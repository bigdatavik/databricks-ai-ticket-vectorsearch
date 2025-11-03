# Databricks notebook source
# MAGIC %md
# MAGIC # Upload Knowledge Base Files to UC Volume

# COMMAND ----------

import os

# Configuration
try:
    CATALOG = dbutils.widgets.get("catalog")
except:
    CATALOG = "classify_tickets_new_dev"  # Default for manual runs
SCHEMA = "support_ai"
VOLUME = "knowledge_docs"
VOLUME_PATH = f"/Volumes/{CATALOG}/{SCHEMA}/{VOLUME}"

print(f"Volume path: {VOLUME_PATH}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Create Volume if it doesn't exist

# COMMAND ----------

# Create volume
try:
    spark.sql(f"""
    CREATE VOLUME IF NOT EXISTS {CATALOG}.{SCHEMA}.{VOLUME}
    COMMENT 'Knowledge base documents for vector search'
    """)
    print(f"✅ Volume created: {CATALOG}.{SCHEMA}.{VOLUME}")
except Exception as e:
    print(f"Volume creation: {e}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Upload Knowledge Base Documents
# MAGIC 
# MAGIC Reads files from the `knowledge_base/` folder in the bundle deployment

# COMMAND ----------

import os
import sys

# Get the bundle root path (where files are deployed)
# Bundle files are deployed to: /Workspace/Users/{user}/.bundle/{bundle_name}/{target}/files/
try:
    # Try to get bundle path from environment or construct it
    username = spark.conf.get("spark.databricks.workspaceUrl", "").split("@")[0] if 'spark' in globals() else None
    bundle_name = "classify_tickets_system"
    target = "dev"
    
    # Try multiple possible paths
    possible_paths = [
        f"/Workspace/Users/{username}/.bundle/{bundle_name}/{target}/files/knowledge_base" if username else None,
        "./knowledge_base",  # Relative to notebook location
        "../knowledge_base",  # One level up
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "knowledge_base") if '__file__' in globals() else None,
    ]
    
    knowledge_base_path = None
    for path in possible_paths:
        if path and os.path.exists(path):
            knowledge_base_path = path
            break
    
    if not knowledge_base_path:
        # Fallback: use dbutils to find files in workspace
        print("⚠️  Could not find knowledge_base folder locally, trying workspace paths...")
        # This will be handled below
        knowledge_base_path = None
except Exception as e:
    print(f"⚠️  Could not determine bundle path: {e}")
    knowledge_base_path = None

print(f"📁 Knowledge base path: {knowledge_base_path}")

# COMMAND ----------

# Read knowledge base files from filesystem
knowledge_files = {}

if knowledge_base_path and os.path.exists(knowledge_base_path):
    # Read from local filesystem (bundle deployment)
    print(f"✅ Reading files from: {knowledge_base_path}")
    for filename in os.listdir(knowledge_base_path):
        if filename.endswith('.txt'):
            file_path = os.path.join(knowledge_base_path, filename)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                knowledge_files[filename] = content
                print(f"  ✅ Loaded: {filename} ({len(content)} chars)")
            except Exception as e:
                print(f"  ❌ Failed to load {filename}: {e}")
else:
    # Fallback: Try reading from workspace using dbutils
    print("⚠️  Using fallback: reading from workspace file system...")
    
    # Try workspace paths
    workspace_paths = [
        f"/Workspace/Users/{dbutils.notebook.entry_point.getDbutils().notebook().getContext().userName().get()}/.bundle/classify_tickets_system/dev/files/knowledge_base",
        "/Workspace/Repos/classify_tickets_system/knowledge_base",
        "/Workspace/knowledge_base",
    ]
    
    files_found = False
    for ws_path in workspace_paths:
        try:
            files = dbutils.fs.ls(ws_path)
            print(f"✅ Found files in workspace: {ws_path}")
            for file_info in files:
                if file_info.name.endswith('.txt'):
                    filename = file_info.name
                    content = dbutils.fs.head(f"{ws_path}/{filename}")
                    knowledge_files[filename] = content
                    print(f"  ✅ Loaded: {filename} ({len(content)} chars)")
            if knowledge_files:
                files_found = True
                break
        except:
            continue
    
    if not files_found:
        raise FileNotFoundError(
            "❌ Could not find knowledge_base files!\n"
            "Please ensure knowledge_base/ folder is accessible in the workspace.\n"
            "Files should be in one of:\n"
            f"  - /Workspace/Users/{{user}}/.bundle/classify_tickets_system/dev/files/knowledge_base\n"
            "  - /Workspace/Repos/classify_tickets_system/knowledge_base\n"
            "  - Or configure bundle to include knowledge_base files"
        )

print(f"\n✅ Loaded {len(knowledge_files)} knowledge base files")
print(f"Files: {list(knowledge_files.keys())}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Upload Files to Volume

# COMMAND ----------

# Upload each file to the volume
for filename, content in knowledge_files.items():
    file_path = f"{VOLUME_PATH}/{filename}"
    
    try:
        # Write content to volume using dbutils
        dbutils.fs.put(file_path, content, overwrite=True)
        print(f"✅ Uploaded: {filename}")
    except Exception as e:
        print(f"❌ Failed to upload {filename}: {e}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Verify Upload

# COMMAND ----------

# List files in volume
print(f"\nFiles in {VOLUME_PATH}:")
files = dbutils.fs.ls(VOLUME_PATH)
for file in files:
    print(f"  - {file.name} ({file.size} bytes)")

print(f"\n✅ Total files: {len(files)}")
