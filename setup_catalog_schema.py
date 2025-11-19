# Databricks notebook source
# MAGIC %md
# MAGIC # Setup 1: Create Catalog and Schema
# MAGIC 
# MAGIC This notebook creates the Unity Catalog infrastructure for the LangGraph Tutorial.
# MAGIC 
# MAGIC **⚠️ RUN THIS FIRST** before any other setup notebooks!
# MAGIC 
# MAGIC ## What This Creates
# MAGIC 
# MAGIC 1. **Catalog**: `langtutorial` - Top-level namespace for tutorial resources
# MAGIC 2. **Schema**: `agents` - Schema containing tables, functions, and volumes
# MAGIC 3. **Volume**: `knowledge_docs` - Storage for knowledge base documents
# MAGIC 
# MAGIC ## Prerequisites
# MAGIC 
# MAGIC - Unity Catalog enabled in workspace
# MAGIC - Permission to CREATE CATALOG (workspace admin or granted permission)
# MAGIC - Databricks Runtime 16.4 LTS or later

# COMMAND ----------

# MAGIC %md
# MAGIC ## Configuration

# COMMAND ----------

# Configuration - Tutorial-specific defaults
try:
    CATALOG = dbutils.widgets.get("catalog")
except:
    CATALOG = "langtutorial_vik"  # Tutorial catalog

SCHEMA = "agents"
VOLUME = "knowledge_docs"

print("=" * 80)
print("LANGGRAPH TUTORIAL - CATALOG SETUP")
print("=" * 80)
print(f"Catalog: {CATALOG}")
print(f"Schema:  {SCHEMA}")
print(f"Volume:  {VOLUME}")
print("=" * 80)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 1: Create Catalog

# COMMAND ----------

# Create catalog if it doesn't exist
spark.sql(f"""
CREATE CATALOG IF NOT EXISTS {CATALOG}
COMMENT 'LangGraph + Databricks Tutorial - Independent tutorial environment'
""")

print(f"✅ Catalog '{CATALOG}' is ready")

# COMMAND ----------

# Use the catalog
spark.sql(f"USE CATALOG {CATALOG}")
print(f"✅ Using catalog: {CATALOG}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 2: Create Schema

# COMMAND ----------

# Create schema
spark.sql(f"""
CREATE SCHEMA IF NOT EXISTS {SCHEMA}
COMMENT 'Schema for LangGraph agent tutorial - contains AI functions, knowledge base, and sample data'
""")

print(f"✅ Schema '{SCHEMA}' is ready")

# COMMAND ----------

# Use the schema
spark.sql(f"USE SCHEMA {SCHEMA}")
print(f"✅ Using schema: {CATALOG}.{SCHEMA}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 3: Create Volume for Knowledge Base Documents

# COMMAND ----------

# Create volume for storing knowledge base documents
spark.sql(f"""
CREATE VOLUME IF NOT EXISTS {VOLUME}
COMMENT 'Knowledge base documents for vector search - tutorial resources'
""")

print(f"✅ Volume '{VOLUME}' is ready")

# COMMAND ----------

# Show the volume path
volume_path = f"/Volumes/{CATALOG}/{SCHEMA}/{VOLUME}"
print("\n" + "=" * 80)
print("VOLUME INFORMATION")
print("=" * 80)
print(f"📁 Volume path: {volume_path}")
print(f"\nKnowledge base documents will be uploaded here in the next setup step.")
print("=" * 80)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 4: Verify Setup

# COMMAND ----------

# Show all tables in the schema (should be empty initially)
print("📋 Current tables in schema:")
display(spark.sql(f"SHOW TABLES IN {CATALOG}.{SCHEMA}"))

# COMMAND ----------

# Show all volumes in the schema
print("📁 Current volumes in schema:")
display(spark.sql(f"SHOW VOLUMES IN {CATALOG}.{SCHEMA}"))

# COMMAND ----------

# Show all functions in the schema (should be empty initially)
print("🔧 Current functions in schema:")
display(spark.sql(f"SHOW FUNCTIONS IN {CATALOG}.{SCHEMA}"))

# COMMAND ----------

# MAGIC %md
# MAGIC ## ✅ Summary
# MAGIC 
# MAGIC **Created Resources:**
# MAGIC - ✅ Catalog: `langtutorial`
# MAGIC - ✅ Schema: `agents`
# MAGIC - ✅ Volume: `knowledge_docs`
# MAGIC 
# MAGIC **Full Names:**
# MAGIC - Catalog: `langtutorial`
# MAGIC - Schema: `langtutorial.agents`
# MAGIC - Volume: `langtutorial.agents.knowledge_docs`
# MAGIC - Volume Path: `/Volumes/langtutorial/agents/knowledge_docs`
# MAGIC 
# MAGIC **Next Steps (in order):**
# MAGIC 
# MAGIC 1. ✅ **COMPLETED** - Catalog and schema created
# MAGIC 2. 📝 **NEXT** - Run `setup_uc_functions.py` to create AI Functions
# MAGIC 3. 📚 Run `setup_knowledge_base.py` to upload knowledge base documents
# MAGIC 4. 🔍 Run `setup_vector_search.py` to create vector search index
# MAGIC 5. 🎫 Run `setup_ticket_history.py` to create sample historical tickets
# MAGIC 6. 🤖 Create Genie Space manually in Databricks UI
# MAGIC 7. 📓 Update tutorial notebook with Genie Space ID
# MAGIC 8. 🚀 Run the tutorial notebook!
# MAGIC 
# MAGIC ---
# MAGIC 
# MAGIC **📖 For detailed instructions, see:** `SETUP_INSTRUCTIONS.md`

# COMMAND ----------

# Final verification
print("\n" + "=" * 80)
print("✅ SETUP COMPLETE!")
print("=" * 80)
print(f"Catalog: {CATALOG}")
print(f"Schema:  {CATALOG}.{SCHEMA}")
print(f"Volume:  {CATALOG}.{SCHEMA}.{VOLUME}")
print("=" * 80)
print("\n🎯 You can now proceed to setup_uc_functions.py")
print("=" * 80)

