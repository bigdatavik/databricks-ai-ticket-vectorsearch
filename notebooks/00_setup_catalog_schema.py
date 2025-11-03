# Databricks notebook source
# MAGIC %md
# MAGIC # Setup: Create Catalog and Schema
# MAGIC 
# MAGIC This notebook creates the Unity Catalog infrastructure for the AI Ticket Classification system.
# MAGIC 
# MAGIC **Run this first before deploying UC Functions**

# COMMAND ----------

# MAGIC %md
# MAGIC ## Configuration

# COMMAND ----------

# Configuration - Get from widgets if available (set by DAB), otherwise use defaults
try:
    CATALOG = dbutils.widgets.get("catalog")
except:
    CATALOG = "classify_tickets_new_dev"  # Default for manual runs

SCHEMA = "support_ai"
VOLUME = "knowledge_docs"

print(f"Using catalog: {CATALOG}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Create Catalog

# COMMAND ----------

# Create catalog if it doesn't exist
spark.sql(f"""
CREATE CATALOG IF NOT EXISTS {CATALOG}
COMMENT 'AI-Powered Support Ticket Classification System'
""")

print(f"✅ Catalog '{CATALOG}' is ready")

# COMMAND ----------

# Use the catalog
spark.sql(f"USE CATALOG {CATALOG}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Create Schema

# COMMAND ----------

# Create schema
spark.sql(f"""
CREATE SCHEMA IF NOT EXISTS {SCHEMA}
COMMENT 'Support AI schema for ticket classification'
""")

print(f"✅ Schema '{SCHEMA}' is ready")

# COMMAND ----------

# Use the schema
spark.sql(f"USE SCHEMA {SCHEMA}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Create Volume for Knowledge Base Documents

# COMMAND ----------

# Create volume for storing knowledge base documents
spark.sql(f"""
CREATE VOLUME IF NOT EXISTS {VOLUME}
COMMENT 'Knowledge base documents for vector search'
""")

print(f"✅ Volume '{VOLUME}' is ready")

# COMMAND ----------

# Show the volume path
volume_path = f"/Volumes/{CATALOG}/{SCHEMA}/{VOLUME}"
print(f"\n📁 Volume path: {volume_path}")
print(f"\nUpload knowledge base documents to: {volume_path}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Verify Setup

# COMMAND ----------

# Show all tables in the schema
print("Current tables in schema:")
display(spark.sql(f"SHOW TABLES IN {CATALOG}.{SCHEMA}"))

# COMMAND ----------

# Show all volumes in the schema
print("Current volumes in schema:")
display(spark.sql(f"SHOW VOLUMES IN {CATALOG}.{SCHEMA}"))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Summary
# MAGIC 
# MAGIC ✅ Catalog: `classify_tickets_new`  
# MAGIC ✅ Schema: `support_ai`  
# MAGIC ✅ Volume: `knowledge_docs`  
# MAGIC 
# MAGIC **Next Steps:**
# MAGIC 1. Upload knowledge base documents to the volume
# MAGIC 2. Run the data preparation notebook
# MAGIC 3. Deploy UC Functions
# MAGIC 4. Create Vector Search index

