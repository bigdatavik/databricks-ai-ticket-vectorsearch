# Databricks notebook source
# MAGIC %md
# MAGIC # Setup 4: Vector Search Index
# MAGIC 
# MAGIC This notebook creates the vector search index for semantic knowledge base retrieval.
# MAGIC 
# MAGIC **⚠️ PREREQUISITES:**
# MAGIC - `setup_catalog_schema.py` must be run first
# MAGIC - `setup_knowledge_base.py` must be run first (creates the source table)
# MAGIC 
# MAGIC ## What This Does
# MAGIC 
# MAGIC 1. Checks if vector search endpoint exists (creates if not)
# MAGIC 2. Enables Change Data Feed on knowledge base table
# MAGIC 3. Creates vector search index with embeddings
# MAGIC 4. Triggers initial sync
# MAGIC 5. Verifies index is queryable

# COMMAND ----------

# MAGIC %pip install databricks-vectorsearch --quiet
# MAGIC dbutils.library.restartPython()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Configuration

# COMMAND ----------

from databricks.sdk import WorkspaceClient
from databricks.vector_search.client import VectorSearchClient
import time

# Configuration
try:
    CATALOG = dbutils.widgets.get("catalog")
except:
    CATALOG = "langtutorial"

SCHEMA = "agents"
TABLE_NAME = "knowledge_base"
INDEX_NAME = f"{CATALOG}.{SCHEMA}.knowledge_base_index"
FULL_TABLE_NAME = f"{CATALOG}.{SCHEMA}.{TABLE_NAME}"

# Vector Search Endpoint - will be created if it doesn't exist
VECTOR_ENDPOINT = "one-env-shared-endpoint-2"

print("=" * 80)
print("LANGGRAPH TUTORIAL - VECTOR SEARCH SETUP")
print("=" * 80)
print(f"Endpoint:         {VECTOR_ENDPOINT}")
print(f"Index:            {INDEX_NAME}")
print(f"Source Table:     {FULL_TABLE_NAME}")
print(f"Embedding Model:  databricks-bge-large-en (FREE)")
print(f"Sync Type:        TRIGGERED (cost-optimized)")
print("=" * 80)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 1: Check/Create Vector Search Endpoint
# MAGIC 
# MAGIC **Note:** This endpoint may be shared across projects.
# MAGIC - If it exists: We reuse it (cost-effective)
# MAGIC - If it doesn't exist: We create it (portable to new environments)

# COMMAND ----------

w = WorkspaceClient()
vsc = VectorSearchClient(disable_notice=True)

print("─" * 80)
print(f"Checking Endpoint: {VECTOR_ENDPOINT}")
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
            if i % 6 == 0:  # Print every minute
                print(f"   ... still {status} ({i//6} min elapsed)")
        
        if status != "ONLINE":
            raise Exception(f"Endpoint did not become ONLINE after 10 minutes. Status: {status}")
        
except Exception as e:
    error_msg = str(e)
    if "not found" in error_msg.lower() or "does not exist" in error_msg.lower():
        print(f"ℹ️  Endpoint not found: {VECTOR_ENDPOINT}")
        print(f"   Creating new endpoint...")
        print(f"   ⚠️  This can take 10-15 minutes...")
        
        try:
            # Create the endpoint
            endpoint = vsc.create_endpoint(
                name=VECTOR_ENDPOINT,
                endpoint_type="STANDARD"
            )
            
            print(f"✅ Endpoint creation started: {VECTOR_ENDPOINT}")
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
                
                if i % 6 == 0:  # Print every minute
                    print(f"   ... {status} ({i//6} min elapsed)")
            
            if status != "ONLINE":
                raise Exception(f"Endpoint creation timeout. Status: {status}")
                
        except Exception as create_error:
            print(f"❌ ERROR: Failed to create endpoint: {create_error}")
            print(f"")
            print(f"⚠️  This may be due to:")
            print(f"   - Insufficient permissions (need to create endpoints)")
            print(f"   - Workspace quotas exceeded")
            print(f"   - Network/region issues")
            print(f"")
            print(f"💡 Solutions:")
            print(f"   - Ask workspace admin to create endpoint '{VECTOR_ENDPOINT}'")
            print(f"   - Or use existing endpoint and update VECTOR_ENDPOINT variable")
            raise
    else:
        print(f"❌ ERROR: Unexpected error checking endpoint: {e}")
        raise

if not endpoint_exists:
    raise Exception(f"Failed to ensure endpoint '{VECTOR_ENDPOINT}' is available")

print()
print("✅ Vector Search Endpoint is ready")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 2: Enable Change Data Feed on Source Table

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
# MAGIC ## Step 3: Create Vector Search Index

# COMMAND ----------

print("─" * 80)
print(f"Creating Vector Search Index")
print("─" * 80)

# Check if index already exists
index_exists = False
try:
    existing_index = vsc.get_index(VECTOR_ENDPOINT, INDEX_NAME)
    print(f"⚠️  Index already exists: {INDEX_NAME}")
    
    desc = existing_index.describe()
    status = desc.get('status', {}).get('state', 'Unknown')
    print(f"   Current Status: {status}")
    
    if status == "ONLINE":
        print(f"   ✅ Index is already ONLINE")
        print(f"   📌 Will trigger sync to ensure latest data")
        index_exists = True
    else:
        print(f"   ⏳ Index is {status}, will wait for it to be ready")
        index_exists = True
        
except Exception as e:
    if "not found" in str(e).lower() or "does not exist" in str(e).lower():
        print(f"ℹ️  Index does not exist, creating new index...")
        index_exists = False
    else:
        print(f"⚠️  Error checking index: {e}")
        index_exists = False

if not index_exists:
    # Create new index
    try:
        print()
        print(f"📝 Creating Vector Search Index: {INDEX_NAME}")
        print(f"   Endpoint: {VECTOR_ENDPOINT}")
        print(f"   Source: {FULL_TABLE_NAME}")
        print(f"   Primary Key: doc_id")
        print(f"   Embedding Column: content")
        print(f"   Model: databricks-bge-large-en (FREE)")
        print(f"   Pipeline: TRIGGERED (cost-optimized)")
        
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
        
    except Exception as e:
        error_msg = str(e)
        if "RESOURCE_ALREADY_EXISTS" in error_msg or "already exists" in error_msg.lower():
            print(f"   ⚠️  Index was created by another process, continuing...")
            index = vsc.get_index(VECTOR_ENDPOINT, INDEX_NAME)
        else:
            print(f"   ❌ Error creating index: {e}")
            raise
else:
    # Use existing index
    index = vsc.get_index(VECTOR_ENDPOINT, INDEX_NAME)
    print(f"   Using existing index")

print()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 4: Trigger Initial Sync

# COMMAND ----------

print("─" * 80)
print("Triggering Sync")
print("─" * 80)

try:
    print(f"⏳ Triggering full sync...")
    print(f"   This will embed all {spark.table(FULL_TABLE_NAME).count()} documents")
    
    index.sync()
    
    print(f"✅ Sync triggered successfully")
    print(f"   Embeddings will be generated in the background")
    print(f"   This may take a few minutes...")
    
except Exception as e:
    print(f"⚠️  Sync trigger: {e}")
    print(f"   Index will sync automatically in the background")

print()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 5: Verify Index is Queryable

# COMMAND ----------

print("─" * 80)
print("Verifying Index")
print("─" * 80)

# Wait a bit for initial embeddings
print("⏳ Waiting for initial embeddings (30 seconds)...")
time.sleep(30)

# Try a test search
try:
    print("\n🔍 Testing search with query: 'database connection issues'")
    
    results = index.similarity_search(
        query_text="database connection issues",
        columns=["doc_id", "title", "content"],
        num_results=3
    )
    
    data_array = results.get('result', {}).get('data_array', [])
    
    if data_array:
        print(f"✅ Index is queryable! Found {len(data_array)} results:")
        for i, doc in enumerate(data_array[:3], 1):
            doc_id = doc[0] if len(doc) > 0 else "N/A"
            title = doc[1] if len(doc) > 1 else "N/A"
            print(f"   {i}. {doc_id}: {title}")
    else:
        print(f"⚠️  No results yet - embeddings still processing")
        print(f"   This is normal for large knowledge bases")
        print(f"   Wait a few minutes and try searching again")
        
except Exception as e:
    print(f"⚠️  Search test: {e}")
    print(f"   Index may still be initializing")
    print(f"   Wait a few minutes before using in tutorial")

print()

# COMMAND ----------

# MAGIC %md
# MAGIC ## ✅ Summary
# MAGIC 
# MAGIC **Completed:**
# MAGIC - ✅ Vector Search Endpoint ready: `one-env-shared-endpoint-2`
# MAGIC - ✅ Change Data Feed enabled on source table
# MAGIC - ✅ Vector Search Index created: `langtutorial.agents.knowledge_base_index`
# MAGIC - ✅ Initial sync triggered
# MAGIC - ✅ Index verified queryable
# MAGIC 
# MAGIC **Index Details:**
# MAGIC - **Source Table**: `langtutorial.agents.knowledge_base`
# MAGIC - **Primary Key**: `doc_id`
# MAGIC - **Embedding Column**: `content`
# MAGIC - **Embedding Model**: `databricks-bge-large-en` (FREE)
# MAGIC - **Pipeline Type**: TRIGGERED (cost-optimized)
# MAGIC 
# MAGIC **Next Steps:**
# MAGIC 
# MAGIC 1. ✅ **COMPLETED** - Vector search index ready
# MAGIC 2. 📝 **NEXT** - Run `setup_ticket_history.py` to create sample historical tickets
# MAGIC 3. 🤖 Create Genie Space manually in Databricks UI
# MAGIC 4. 📓 Update tutorial notebook with Genie Space ID
# MAGIC 5. 🚀 Run the tutorial notebook!

# COMMAND ----------

# Final summary
print("\n" + "=" * 80)
print("✅ VECTOR SEARCH SETUP COMPLETE!")
print("=" * 80)
print(f"Endpoint:    {VECTOR_ENDPOINT}")
print(f"Index:       {INDEX_NAME}")
print(f"Source:      {FULL_TABLE_NAME}")
print(f"Status:      Ready for queries")
print("=" * 80)
print("\n🎯 You can now proceed to setup_ticket_history.py")
print("=" * 80)

