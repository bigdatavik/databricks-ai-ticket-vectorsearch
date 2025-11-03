# Databricks notebook source
# MAGIC %md
# MAGIC # Rebuild Vector Search Index - Full Sync
# MAGIC 
# MAGIC This will delete and recreate the index to pick up all documents including Guide documents.

# COMMAND ----------

# MAGIC %pip install databricks-vectorsearch
# MAGIC dbutils.library.restartPython()

# COMMAND ----------

from databricks.vector_search.client import VectorSearchClient
from databricks.sdk import WorkspaceClient
import time

# Configuration
CATALOG = "classify_tickets_new_dev"
SCHEMA = "support_ai"
INDEX_NAME = f"{CATALOG}.{SCHEMA}.knowledge_base_index"
FULL_TABLE_NAME = f"{CATALOG}.{SCHEMA}.knowledge_base"
VECTOR_ENDPOINT = "one-env-shared-endpoint-2"

print("=" * 80)
print("REBUILD VECTOR SEARCH INDEX")
print("=" * 80)
print(f"Index: {INDEX_NAME}")
print(f"Source Table: {FULL_TABLE_NAME}")
print(f"Endpoint: {VECTOR_ENDPOINT}")
print("=" * 80)

# COMMAND ----------

vsc = VectorSearchClient(disable_notice=True)
w = WorkspaceClient()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 1: Check Current Index Status

# COMMAND ----------

try:
    index = vsc.get_index(VECTOR_ENDPOINT, INDEX_NAME)
    desc = index.describe()
    
    print("📊 Current Index Status:")
    print(f"   Status: {desc.get('status', {}).get('state', 'Unknown')}")
    
    stats = desc.get('index_stats', {})
    if stats:
        print(f"   Current vectors: {stats.get('num_vectors', 'N/A')}")
    
    print("\n⚠️  Current index has only 21 documents")
    print("   Source table has 31 documents (missing 10 Guide documents)")
    
except Exception as e:
    print(f"⚠️  Error accessing index: {e}")
    print("   Index might not exist - will create new one")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 2: Delete Existing Index

# COMMAND ----------

print("\n" + "=" * 80)
print("STEP 2: Deleting Existing Index")
print("=" * 80)

try:
    print(f"🗑️  Deleting index: {INDEX_NAME}")
    vsc.delete_index(INDEX_NAME)
    print(f"✅ Index deleted successfully")
    
    # Wait for deletion to complete
    print("⏳ Waiting for deletion to complete...")
    time.sleep(10)
    
except Exception as e:
    error_msg = str(e)
    if "not found" in error_msg.lower() or "does not exist" in error_msg.lower():
        print(f"ℹ️  Index does not exist (nothing to delete)")
    else:
        print(f"⚠️  Error deleting index: {e}")
        raise

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 3: Create New Index (Full Sync)

# COMMAND ----------

print("\n" + "=" * 80)
print("STEP 3: Creating New Index")
print("=" * 80)

try:
    print(f"📝 Creating Vector Search Index: {INDEX_NAME}")
    print(f"   Endpoint: {VECTOR_ENDPOINT}")
    print(f"   Source: {FULL_TABLE_NAME}")
    print(f"   Primary Key: doc_id")
    print(f"   Embedding Column: content")
    print(f"   Model: databricks-bge-large-en")
    
    index = vsc.create_delta_sync_index(
        endpoint_name=VECTOR_ENDPOINT,
        index_name=INDEX_NAME,
        source_table_name=FULL_TABLE_NAME,
        pipeline_type="TRIGGERED",
        primary_key="doc_id",
        embedding_source_column="content",
        embedding_model_endpoint_name="databricks-bge-large-en"
    )
    
    print(f"   ✅ Index created successfully")
    print()
    print(f"   ⏳ Waiting for index to be ONLINE...")
    
    # Wait for index to be ONLINE (can take a few minutes)
    for i in range(60):  # Wait up to 10 minutes
        time.sleep(10)
        try:
            desc = index.describe()
            status = desc.get('status', {}).get('state', 'Unknown')
            
            if status == "ONLINE":
                print(f"   ✅ Index is ONLINE and ready")
                break
                
            if i % 6 == 0:  # Print every minute
                print(f"   ... Index status: {status} ({i//6} min elapsed)")
                
        except Exception as check_error:
            if i % 6 == 0:
                print(f"   ... Waiting for index to be queryable ({i//6} min elapsed)")
    
    # Trigger initial sync
    print(f"   ⏳ Triggering initial full sync...")
    try:
        index.sync()
        print(f"   ✅ Sync triggered")
        print(f"      All 31 documents will be embedded (including 10 Guide documents)")
        print(f"      This may take 5-10 minutes")
    except Exception as sync_error:
        print(f"   ⚠️  Sync trigger: {sync_error}")
        print(f"      Index will sync automatically in the background")
        
except Exception as e:
    print(f"   ❌ Error creating index: {e}")
    raise

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 4: Verify Index Status

# COMMAND ----------

print("\n" + "=" * 80)
print("STEP 4: Verify Index Status")
print("=" * 80)

try:
    index = vsc.get_index(VECTOR_ENDPOINT, INDEX_NAME)
    desc = index.describe()
    
    print(f"Index Name:       {INDEX_NAME}")
    print(f"Status:           {desc.get('status', {}).get('state', 'Unknown')}")
    print(f"Source Table:     {FULL_TABLE_NAME}")
    
    stats = desc.get('index_stats', {})
    if stats:
        num_vectors = stats.get('num_vectors', 'N/A')
        print(f"Number of vectors: {num_vectors}")
        
        if num_vectors == 31:
            print("\n✅ SUCCESS! All 31 documents are indexed (including Guide documents)")
        elif num_vectors > 21:
            print(f"\n⚠️  Index has {num_vectors} vectors (expected 31)")
            print("   Sync may still be in progress - wait a few minutes")
        else:
            print(f"\n⚠️  Index has {num_vectors} vectors (expected 31)")
            print("   Sync may need more time or manual trigger")
    
    print("=" * 80)
    print("✅ Index rebuild complete!")
    print("\nNext steps:")
    print("  1. Wait 5-10 minutes for embeddings to complete")
    print("  2. Re-run your test queries")
    print("  3. Guide documents should now appear in search results")
    
except Exception as e:
    print(f"❌ Error checking index: {e}")
    raise

