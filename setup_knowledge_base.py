# Databricks notebook source
# MAGIC %md
# MAGIC # Setup 3: Upload Knowledge Base and Create Table
# MAGIC 
# MAGIC This notebook:
# MAGIC 1. Uploads knowledge base documents to UC Volume
# MAGIC 2. Creates a Delta table for vector search
# MAGIC 
# MAGIC **⚠️ PREREQUISITES:**
# MAGIC - `setup_catalog_schema.py` must be run first
# MAGIC - `setup_uc_functions.py` should be run (optional but recommended)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Configuration

# COMMAND ----------

import os
import re
from datetime import datetime

# Configuration
try:
    CATALOG = dbutils.widgets.get("catalog")
except:
    CATALOG = "langtutorial"  # Tutorial catalog

SCHEMA = "agents"
VOLUME = "knowledge_docs"
TABLE_NAME = "knowledge_base"

VOLUME_PATH = f"/Volumes/{CATALOG}/{SCHEMA}/{VOLUME}"
FULL_TABLE_NAME = f"{CATALOG}.{SCHEMA}.{TABLE_NAME}"

print("=" * 80)
print("LANGGRAPH TUTORIAL - KNOWLEDGE BASE SETUP")
print("=" * 80)
print(f"Catalog:    {CATALOG}")
print(f"Schema:     {SCHEMA}")
print(f"Volume:     {VOLUME}")
print(f"Volume Path: {VOLUME_PATH}")
print(f"Table:      {FULL_TABLE_NAME}")
print("=" * 80)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 1: Verify Volume Exists

# COMMAND ----------

# Verify volume exists
try:
    files = dbutils.fs.ls(VOLUME_PATH)
    print(f"✅ Volume exists: {VOLUME_PATH}")
except:
    print(f"❌ Volume not found! Please run setup_catalog_schema.py first.")
    raise

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 2: Read Knowledge Base Files from Repository
# MAGIC 
# MAGIC The knowledge_base/ folder contains IT support documentation:
# MAGIC - Infrastructure runbooks
# MAGIC - Application support guides
# MAGIC - Troubleshooting documentation
# MAGIC - Security incident playbooks
# MAGIC - etc.

# COMMAND ----------

# Try to find knowledge_base folder
# The folder should be in the repository root, deployed with the bundle

knowledge_base_paths = [
    "../knowledge_base",  # If notebook is in root
    "./knowledge_base",   # If run from root
    "knowledge_base",     # Direct path
]

knowledge_files = {}
knowledge_base_path = None

for path in knowledge_base_paths:
    try:
        # Try using dbutils to access workspace files
        full_path = f"/Workspace{os.path.abspath(path)}" if not path.startswith('/') else path
        
        # Try direct filesystem access first (works in Databricks)
        if os.path.exists(path):
            knowledge_base_path = path
            print(f"✅ Found knowledge_base at: {path}")
            break
    except:
        continue

if not knowledge_base_path:
    # Try workspace path from bundle deployment
    try:
        user = dbutils.notebook.entry_point.getDbutils().notebook().getContext().userName().get()
        bundle_path = f"/Workspace/Users/{user}/.bundle/langraph-tutorial/dev/knowledge_base"
        files = dbutils.fs.ls(bundle_path)
        if files:
            knowledge_base_path = bundle_path
            print(f"✅ Found knowledge_base in bundle: {bundle_path}")
    except:
        pass

if not knowledge_base_path:
    raise FileNotFoundError(
        "❌ Could not find knowledge_base folder!\n"
        "Expected locations:\n"
        "  - ../knowledge_base (if notebook uploaded to workspace)\n"
        "  - /Workspace/Users/{user}/.bundle/langraph-tutorial/dev/knowledge_base (if deployed via bundle)\n"
        "\n"
        "Please ensure knowledge_base/ folder is accessible."
    )

# COMMAND ----------

# Read all .txt files from knowledge_base
if knowledge_base_path.startswith('/Workspace'):
    # Read from workspace using dbutils
    print(f"📂 Reading from workspace: {knowledge_base_path}")
    files = dbutils.fs.ls(knowledge_base_path)
    for file_info in files:
        if file_info.name.endswith('.txt'):
            filename = file_info.name
            file_path = f"{knowledge_base_path}/{filename}"
            content = dbutils.fs.head(file_path, maxBytes=1000000)  # Read up to 1MB
            knowledge_files[filename] = content
            print(f"  ✅ Loaded: {filename} ({len(content):,} chars)")
else:
    # Read from local filesystem
    print(f"📂 Reading from filesystem: {knowledge_base_path}")
    for filename in os.listdir(knowledge_base_path):
        if filename.endswith('.txt'):
            file_path = os.path.join(knowledge_base_path, filename)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                knowledge_files[filename] = content
                print(f"  ✅ Loaded: {filename} ({len(content):,} chars)")
            except Exception as e:
                print(f"  ❌ Failed to load {filename}: {e}")

print(f"\n✅ Loaded {len(knowledge_files)} knowledge base files")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 3: Upload Files to UC Volume

# COMMAND ----------

# Upload each file to the volume
print(f"\n📤 Uploading to volume: {VOLUME_PATH}")
for filename, content in knowledge_files.items():
    file_path = f"{VOLUME_PATH}/{filename}"
    
    try:
        # Write content to volume using dbutils
        dbutils.fs.put(file_path, content, overwrite=True)
        print(f"  ✅ Uploaded: {filename}")
    except Exception as e:
        print(f"  ❌ Failed to upload {filename}: {e}")

# COMMAND ----------

# Verify upload
print(f"\n📋 Files in volume:")
files = dbutils.fs.ls(VOLUME_PATH)
for file in files:
    size_kb = file.size / 1024
    print(f"  - {file.name} ({size_kb:.1f} KB)")

print(f"\n✅ Total files in volume: {len(files)}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 4: Create Knowledge Base Delta Table
# MAGIC 
# MAGIC This table will be used for vector search.

# COMMAND ----------

# Create knowledge base table schema
spark.sql(f"""
CREATE TABLE IF NOT EXISTS {FULL_TABLE_NAME} (
  doc_id STRING NOT NULL,
  doc_type STRING,
  title STRING,
  content STRING,
  source_file STRING,
  char_count INT,
  created_at TIMESTAMP,
  CONSTRAINT knowledge_base_pk PRIMARY KEY(doc_id)
)
USING DELTA
COMMENT 'Knowledge base documents for vector search - LangGraph tutorial'
""")

print(f"✅ Table created: {FULL_TABLE_NAME}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 5: Parse and Insert Documents

# COMMAND ----------

from pyspark.sql.types import StructType, StructField, StringType, IntegerType, TimestampType
from pyspark.sql import Row

# Parse documents and create records
documents = []

for filename, content in knowledge_files.items():
    # Extract title from filename (remove extension, replace underscores)
    title = filename.replace('.txt', '').replace('_', ' ').title()
    
    # Determine document type from filename
    if 'runbook' in filename.lower() or 'guide' in filename.lower():
        doc_type = 'Guide'
    elif 'playbook' in filename.lower():
        doc_type = 'Playbook'
    elif 'troubleshooting' in filename.lower():
        doc_type = 'Troubleshooting'
    elif 'policy' in filename.lower() or 'policies' in filename.lower():
        doc_type = 'Policy'
    elif 'rules' in filename.lower():
        doc_type = 'Rules'
    else:
        doc_type = 'Documentation'
    
    # Create document ID from filename
    doc_id = filename.replace('.txt', '').upper().replace('_', '-')
    
    # Create document record
    doc = Row(
        doc_id=doc_id,
        doc_type=doc_type,
        title=title,
        content=content.strip(),
        source_file=filename,
        char_count=len(content),
        created_at=datetime.now()
    )
    
    documents.append(doc)
    print(f"  📄 Parsed: {title} ({doc_type}, {len(content):,} chars)")

print(f"\n✅ Parsed {len(documents)} documents")

# COMMAND ----------

# Create DataFrame and write to Delta table
df = spark.createDataFrame(documents)

# Write to table (overwrite if exists)
df.write.format("delta").mode("overwrite").saveAsTable(FULL_TABLE_NAME)

print(f"✅ Inserted {df.count()} documents into {FULL_TABLE_NAME}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 6: Verify Table Contents

# COMMAND ----------

# Show table statistics
print("📊 Table Statistics:")
stats_df = spark.sql(f"""
SELECT 
  COUNT(*) as total_docs,
  COUNT(DISTINCT doc_type) as doc_types,
  SUM(char_count) as total_chars,
  AVG(char_count) as avg_chars_per_doc
FROM {FULL_TABLE_NAME}
""")
display(stats_df)

# COMMAND ----------

# Show document types breakdown
print("📁 Documents by Type:")
types_df = spark.sql(f"""
SELECT 
  doc_type,
  COUNT(*) as count,
  SUM(char_count) as total_chars
FROM {FULL_TABLE_NAME}
GROUP BY doc_type
ORDER BY count DESC
""")
display(types_df)

# COMMAND ----------

# Show sample documents
print("📄 Sample Documents:")
sample_df = spark.sql(f"""
SELECT 
  doc_id,
  doc_type,
  title,
  char_count,
  SUBSTRING(content, 1, 100) as content_preview
FROM {FULL_TABLE_NAME}
ORDER BY doc_id
LIMIT 5
""")
display(sample_df)

# COMMAND ----------

# MAGIC %md
# MAGIC ## ✅ Summary
# MAGIC 
# MAGIC **Completed:**
# MAGIC - ✅ Uploaded knowledge base files to UC Volume
# MAGIC - ✅ Created Delta table: `langtutorial.agents.knowledge_base`
# MAGIC - ✅ Inserted and parsed documents
# MAGIC 
# MAGIC **Next Steps:**
# MAGIC 
# MAGIC 1. ✅ **COMPLETED** - Knowledge base table ready
# MAGIC 2. 📝 **NEXT** - Run `setup_vector_search.py` to create vector search index
# MAGIC 3. 🎫 Run `setup_ticket_history.py` to create sample historical tickets
# MAGIC 4. 🤖 Create Genie Space manually in Databricks UI
# MAGIC 5. 📓 Update tutorial notebook with Genie Space ID
# MAGIC 6. 🚀 Run the tutorial notebook!

# COMMAND ----------

# Final summary
print("\n" + "=" * 80)
print("✅ KNOWLEDGE BASE SETUP COMPLETE!")
print("=" * 80)
print(f"Volume:      {VOLUME_PATH}")
print(f"Table:       {FULL_TABLE_NAME}")
print(f"Documents:   {len(documents)}")
print("=" * 80)
print("\n🎯 You can now proceed to setup_vector_search.py")
print("=" * 80)

