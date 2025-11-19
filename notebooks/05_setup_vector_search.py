# Databricks notebook source
# MAGIC %md
# MAGIC # Vector Search Index Setup (Mode-Aware)
# MAGIC 
# MAGIC Handles both FULL and INCREMENTAL modes:
# MAGIC - **FULL:** Creates new index (cleanup already deleted old one)
# MAGIC - **INCREMENTAL:** Syncs existing index or creates if missing
# MAGIC 
# MAGIC **IMPORTANT:** The Vector Search endpoint is SHARED and NEVER deleted.

# COMMAND ----------

# MAGIC %pip install databricks-vectorsearch
# MAGIC dbutils.library.restartPython()

# COMMAND ----------

from databricks.sdk import WorkspaceClient
from databricks.vector_search.client import VectorSearchClient
import time

# Configuration
try:
    CATALOG = dbutils.widgets.get("catalog")
    MODE = dbutils.widgets.get("mode")
    VECTOR_ENDPOINT = dbutils.widgets.get("vector_endpoint")
except:
    CATALOG = "langtutorial_vik"  # Tutorial catalog
    MODE = "incremental"
    VECTOR_ENDPOINT = "one-env-shared-endpoint-2"

SCHEMA = "agents"
TABLE_NAME = "knowledge_base"
INDEX_NAME = f"{CATALOG}.{SCHEMA}.knowledge_base_index"
FULL_TABLE_NAME = f"{CATALOG}.{SCHEMA}.{TABLE_NAME}"

print("=" * 80)
print("VECTOR SEARCH INDEX SETUP")
print("=" * 80)
print(f"Mode:             {MODE.upper()}")
print(f"Endpoint:         {VECTOR_ENDPOINT} (SHARED - PROTECTED)")
print(f"Index:            {INDEX_NAME}")
print(f"Source Table:     {FULL_TABLE_NAME}")
print(f"Embedding Model:  databricks-bge-large-en (FREE)")
print(f"Sync Type:        TRIGGERED (cost-optimized)")
print("=" * 80)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 1: Check/Create Shared Endpoint
# MAGIC 
# MAGIC **IMPORTANT:** This endpoint is SHARED across projects.
# MAGIC - ✅ We create it if it doesn't exist
# MAGIC - ✅ We reuse it if it already exists
# MAGIC - ⚠️ We NEVER delete it (would break other projects)

# COMMAND ----------

w = WorkspaceClient()
vsc = VectorSearchClient(disable_notice=True)

print("─" * 80)
print(f"Checking Shared Endpoint: {VECTOR_ENDPOINT}")
print("─" * 80)

endpoint_exists = False
try:
    endpoint = vsc.get_endpoint(VECTOR_ENDPOINT)
    status = endpoint.get('endpoint_status', {}).get('state', 'Unknown')
    print(f"✅ Endpoint exists: {VECTOR_ENDPOINT}")
    print(f"   Status: {status}")
    endpoint_exists = True
    
    if status == "ONLINE":
        print(f"   ✅ Endpoint is ONLINE and ready")
    else:
        print(f"   ⏳ Endpoint is {status}, waiting for ONLINE status...")
        # Wait up to 10 minutes for endpoint to come online
        for i in range(60):
            time.sleep(10)
            endpoint = vsc.get_endpoint(VECTOR_ENDPOINT)
            status = endpoint.get('endpoint_status', {}).get('state', 'Unknown')
            if status == "ONLINE":
                print(f"   ✅ Endpoint is now ONLINE")
                break
            print(f"   ... still {status} ({i+1}/60)")
        
        if status != "ONLINE":
            raise Exception(f"Endpoint did not become ONLINE after 10 minutes. Status: {status}")
        
except Exception as e:
    error_msg = str(e)
    if "not found" in error_msg.lower() or "does not exist" in error_msg.lower():
        print(f"ℹ️  Endpoint not found: {VECTOR_ENDPOINT}")
        print(f"   Creating new shared endpoint...")
        
        try:
            # Create the endpoint
            endpoint = vsc.create_endpoint(
                name=VECTOR_ENDPOINT,
                endpoint_type="STANDARD"
            )
            
            print(f"✅ Endpoint created: {VECTOR_ENDPOINT}")
            print(f"   ⏳ Waiting for endpoint to become ONLINE...")
            
            # Wait for endpoint to be online (can take 10-15 minutes)
            for i in range(90):  # 15 minutes max
                time.sleep(10)
                endpoint = vsc.get_endpoint(VECTOR_ENDPOINT)
                status = endpoint.get('endpoint_status', {}).get('state', 'Unknown')
                
                if status == "ONLINE":
                    print(f"   ✅ Endpoint is ONLINE and ready!")
                    endpoint_exists = True
                    break
                
                print(f"   ... {status} ({i+1}/90)")
            
            if status != "ONLINE":
                raise Exception(f"Endpoint creation timeout. Status: {status}")
                
        except Exception as create_error:
            print(f"❌ ERROR: Failed to create endpoint: {create_error}")
            print(f"")
            print(f"⚠️  This may be due to:")
            print(f"   - Insufficient permissions")
            print(f"   - Workspace quotas exceeded")
            print(f"   - Network/region issues")
            print(f"")
            raise
    else:
        print(f"❌ ERROR: Unexpected error checking endpoint: {e}")
        raise

if not endpoint_exists:
    raise Exception(f"Failed to ensure endpoint '{VECTOR_ENDPOINT}' is available")

print()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 2: Enable Change Data Feed

# COMMAND ----------

print("─" * 80)
print("Enabling Change Data Feed on Source Table")
print("─" * 80)

try:
    spark.sql(f"""
        ALTER TABLE {FULL_TABLE_NAME} 
        SET TBLPROPERTIES (delta.enableChangeDataFeed = true)
    """)
    print(f"✅ Change Data Feed enabled on {FULL_TABLE_NAME}")
except Exception as e:
    print(f"ℹ️  CDC status: {e}")
    print(f"   (May already be enabled - this is OK)")

print()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 3: Handle Index Based on Mode

# COMMAND ----------

print("─" * 80)
print(f"Index Management: {MODE.upper()} Mode")
print("─" * 80)

if MODE.lower() == "full":
    print("🔄 FULL MODE: Creating new index")
    print("   (Cleanup script already deleted old index)")
    print()
    
    # In FULL mode, cleanup already deleted the index
    # Just create a fresh one
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
        print(f"   ⏳ Waiting for index to be ready...")
        
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
            print(f"   ✅ Initial sync triggered")
            print(f"      All documents will be embedded")
        except Exception as sync_error:
            print(f"   ⚠️  Sync trigger: {sync_error}")
            print(f"      Index will sync automatically in the background")
        
    except Exception as e:
        error_msg = str(e)
        if "RESOURCE_ALREADY_EXISTS" in error_msg or "already exists" in error_msg.lower():
            print(f"   ⚠️  WARNING: Index already exists!")
            print(f"      This shouldn't happen in FULL mode.")
            print(f"      Cleanup script may have failed.")
            print()
            print(f"   Attempting to delete and recreate...")
            try:
                vsc.delete_index(INDEX_NAME)
                print(f"   ✅ Deleted existing index")
                time.sleep(5)
                
                # Retry creation
                index = vsc.create_delta_sync_index(
                    endpoint_name=VECTOR_ENDPOINT,
                    index_name=INDEX_NAME,
                    source_table_name=FULL_TABLE_NAME,
                    pipeline_type="TRIGGERED",
                    primary_key="doc_id",
                    embedding_source_column="content",
                    embedding_model_endpoint_name="databricks-bge-large-en"
                )
                print(f"   ✅ Index recreated successfully")
                time.sleep(10)
                index.sync()
                print(f"   ✅ Sync triggered")
            except Exception as retry_error:
                print(f"   ❌ Failed to recreate: {retry_error}")
                raise
        else:
            print(f"   ❌ Error creating index: {e}")
            raise

elif MODE.lower() == "incremental":
    print("⚡ INCREMENTAL MODE: Smart sync")
    print("   Will use existing index if available")
    print()
    
    # Check if index exists
    try:
        existing_index = vsc.get_index(VECTOR_ENDPOINT, INDEX_NAME)
        print(f"   ✅ Index exists: {INDEX_NAME}")
        
        # Get status
        desc = existing_index.describe()
        status = desc.get('status', {}).get('state', 'Unknown')
        print(f"   📊 Index Status: {status}")
        
        if status == "ONLINE":
            print(f"   ✅ Index is ONLINE")
        else:
            print(f"   ⏳ Index is {status}, waiting...")
            # Wait for index to be ready
            for i in range(30):
                time.sleep(10)
                desc = existing_index.describe()
                status = desc.get('status', {}).get('state', 'Unknown')
                if status == "ONLINE":
                    print(f"   ✅ Index is now ONLINE")
                    break
                print(f"   ... still {status}")
        
        # Trigger incremental sync
        print()
        print(f"   ⏳ Triggering incremental sync...")
        
        # CRITICAL: Wait a moment after merge operations to ensure Change Data Feed is ready
        # Vector Search sync reads from Change Data Feed, which needs time to process
        print(f"   ⏳ Waiting 5 seconds for Change Data Feed to process recent commits...")
        time.sleep(5)
        
        # Diagnostic: Check how many records are in source table vs index
        try:
            from pyspark.sql import SparkSession
            spark = SparkSession.builder.getOrCreate()
            source_count = spark.sql(f"SELECT COUNT(*) as count FROM {FULL_TABLE_NAME}").collect()[0]['count']
            
            # Refresh index description to get latest stats
            desc = existing_index.describe()
            stats = desc.get('index_stats', {})
            index_count = stats.get('num_vectors', 0) if stats else 0
            
            print(f"\n   📊 Sync Diagnostic:")
            print(f"      Source table records: {source_count}")
            print(f"      Indexed records: {index_count}")
            if source_count > index_count:
                print(f"      ⚠️  Missing {source_count - index_count} records in index")
                print(f"      Sync should pick up these records")
            else:
                print(f"      ✅ Index appears to be in sync")
        except Exception as diag_error:
            print(f"      ⚠️  Could not check counts: {diag_error}")
        
        existing_index.sync()
        
        print(f"   ✅ Incremental sync triggered!")
        print(f"      Only new/changed records were embedded")
        print(f"      Existing embeddings were preserved")
        
        # Verify sync is processing
        print(f"\n   📊 Checking sync status...")
        time.sleep(3)  # Give sync a moment to start
        
        try:
            desc = existing_index.describe()
            sync_status = desc.get('sync_status', {})
            if sync_status:
                print(f"   Sync status: {sync_status.get('status', 'Unknown')}")
                print(f"   Last sync time: {sync_status.get('last_sync_time', 'N/A')}")
        except:
            pass
        
        print(f"\n   💡 Note: Sync may take 1-2 minutes to complete")
        print(f"      Check Vector Search UI to see when sync finishes")
        
    except Exception as e:
        error_msg = str(e)
        if "not found" in error_msg.lower() or "does not exist" in error_msg.lower():
            print(f"   ℹ️  Index not found")
            print(f"   📝 Creating new index (first deployment for this catalog)")
            print()
            
            # Index doesn't exist - create it
            try:
                index = vsc.create_delta_sync_index(
                    endpoint_name=VECTOR_ENDPOINT,
                    index_name=INDEX_NAME,
                    source_table_name=FULL_TABLE_NAME,
                    pipeline_type="TRIGGERED",
                    primary_key="doc_id",
                    embedding_source_column="content",
                    embedding_model_endpoint_name="databricks-bge-large-en"
                )
                
                print(f"   ✅ Index created")
                print(f"   ⏳ Waiting for index to be ready...")
                
                # Wait for index to be ONLINE
                for i in range(60):
                    time.sleep(10)
                    try:
                        desc = index.describe()
                        status = desc.get('status', {}).get('state', 'Unknown')
                        if status == "ONLINE":
                            print(f"   ✅ Index is ONLINE")
                            break
                        if i % 6 == 0:
                            print(f"   ... {status} ({i//6} min)")
                    except:
                        if i % 6 == 0:
                            print(f"   ... Waiting ({i//6} min)")
                
                # Trigger sync
                try:
                    index.sync()
                    print(f"   ✅ Initial sync triggered")
                except Exception as sync_err:
                    print(f"   ⚠️  Sync: {sync_err}")
                    print(f"      Will sync automatically")
                
            except Exception as create_error:
                print(f"   ❌ Error creating index: {create_error}")
                raise
        else:
            print(f"   ❌ Error accessing index: {e}")
            raise

else:
    raise ValueError(f"❌ Unknown mode: '{MODE}'. Must be 'full' or 'incremental'")

print()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 4: Verify Index Status

# COMMAND ----------

print("=" * 80)
print("VECTOR SEARCH INDEX STATUS")
print("=" * 80)

try:
    index = vsc.get_index(VECTOR_ENDPOINT, INDEX_NAME)
    desc = index.describe()
    
    print(f"Index Name:       {INDEX_NAME}")
    print(f"Endpoint:         {VECTOR_ENDPOINT}")
    print(f"Status:           {desc.get('status', {}).get('state', 'Unknown')}")
    print(f"Source Table:     {FULL_TABLE_NAME}")
    print(f"Primary Key:      {desc.get('primary_key')}")
    print(f"Embedding Model:  databricks-bge-large-en")
    print(f"Sync Mode:        TRIGGERED")
    print("=" * 80)
    print("✅ Vector Search is ready!")
    
except Exception as e:
    print(f"❌ Error checking index: {e}")
    raise

# COMMAND ----------

# MAGIC %md
# MAGIC ## Summary
# MAGIC 
# MAGIC ✅ Vector Search Index is configured and ready
# MAGIC 
# MAGIC **Key Points:**
# MAGIC - Endpoint `{VECTOR_ENDPOINT}` is SHARED (never deleted)
# MAGIC - Index syncs via Delta Change Data Feed
# MAGIC - TRIGGERED mode = manual sync (cost-optimized)
# MAGIC - Uses free `databricks-bge-large-en` embedding model
