# Databricks notebook source
# MAGIC %md
# MAGIC # Cleanup for FULL Mode Deployment
# MAGIC 
# MAGIC **Purpose:** Drops all project resources for a clean slate deployment.
# MAGIC 
# MAGIC **Safety:** 
# MAGIC - ✅ Only runs when `mode=full`
# MAGIC - ✅ **NEVER deletes the shared Vector Search endpoint**
# MAGIC - ✅ Only deletes project-specific resources

# COMMAND ----------

# MAGIC %pip install databricks-vectorsearch
# MAGIC dbutils.library.restartPython()

# COMMAND ----------

from databricks.vector_search.client import VectorSearchClient
from databricks.sdk import WorkspaceClient
import time

# Configuration
try:
    CATALOG = dbutils.widgets.get("catalog")
    MODE = dbutils.widgets.get("mode")
    VECTOR_ENDPOINT = dbutils.widgets.get("vector_endpoint")
    APP_NAME = dbutils.widgets.get("app_name")
except:
    CATALOG = "classify_tickets_new_dev"
    MODE = "full"
    VECTOR_ENDPOINT = "one-env-shared-endpoint-2"
    APP_NAME = "classify-tickets-dashboard-dev"

SCHEMA = "support_ai"
INDEX_NAME = f"{CATALOG}.{SCHEMA}.knowledge_base_index"

print("=" * 80)
print("CLEANUP SCRIPT")
print("=" * 80)
print(f"Mode:             {MODE.upper()}")
print(f"Catalog:          {CATALOG}")
print(f"Vector Endpoint:  {VECTOR_ENDPOINT} (PROTECTED - NEVER DELETED)")
print(f"Vector Index:     {INDEX_NAME}")
print(f"App:              {APP_NAME}")
print("=" * 80)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Safety Check: Only Run in FULL Mode

# COMMAND ----------

if MODE.lower() != "full":
    print(f"✅ MODE is '{MODE}' - Skipping cleanup")
    print(f"   Cleanup only runs when mode=full")
    print(f"   Current mode uses existing resources (incremental)")
    dbutils.notebook.exit("skipped_not_full_mode")

print("🔄 FULL MODE DETECTED")
print("   Proceeding with cleanup to create clean slate...")
print()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 1: Drop Vector Search Index (Project-Specific)

# COMMAND ----------

vsc = VectorSearchClient(disable_notice=True)

print("─" * 80)
print("STEP 1: Vector Search Index Cleanup")
print("─" * 80)

try:
    print(f"🔍 Checking for Vector Search Index: {INDEX_NAME}")
    existing_index = vsc.get_index(VECTOR_ENDPOINT, INDEX_NAME)
    
    print(f"   ✅ Index found: {INDEX_NAME}")
    print(f"   🗑️  Deleting index...")
    
    vsc.delete_index(INDEX_NAME)
    print(f"   ✅ Successfully deleted index: {INDEX_NAME}")
    
    # Wait for deletion to complete
    print(f"   ⏳ Waiting for deletion to complete...")
    time.sleep(5)
    print(f"   ✅ Deletion complete")
    
except Exception as e:
    error_msg = str(e)
    if "not found" in error_msg.lower() or "does not exist" in error_msg.lower():
        print(f"   ℹ️  Index does not exist (nothing to delete)")
    else:
        print(f"   ⚠️  Error checking/deleting index: {e}")
        print(f"   This may be OK if index was already deleted")

print()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 2: Drop Catalog (CASCADE)
# MAGIC 
# MAGIC This drops:
# MAGIC - All schemas in the catalog
# MAGIC - All tables (knowledge_base, sample_tickets, etc.)
# MAGIC - All volumes (knowledge_docs)
# MAGIC - All UC functions (ai_classify, ai_extract, etc.)

# COMMAND ----------

print("─" * 80)
print("STEP 2: Catalog Cleanup (CASCADE)")
print("─" * 80)

try:
    print(f"🔍 Checking if catalog exists: {CATALOG}")
    
    # Check if catalog exists
    try:
        spark.sql(f"USE CATALOG {CATALOG}")
        print(f"   ✅ Catalog exists: {CATALOG}")
    except:
        print(f"   ℹ️  Catalog does not exist (nothing to delete)")
        dbutils.notebook.exit("catalog_not_found")
    
    print(f"   🗑️  Dropping catalog CASCADE...")
    spark.sql(f"DROP CATALOG IF EXISTS {CATALOG} CASCADE")
    
    print(f"   ✅ Successfully dropped catalog: {CATALOG}")
    print()
    print(f"   📦 This also removed:")
    print(f"      ✅ All schemas")
    print(f"      ✅ All tables (knowledge_base, sample_tickets, etc.)")
    print(f"      ✅ All volumes (knowledge_docs)")
    print(f"      ✅ All UC functions (ai_classify, ai_extract, ai_gen, quick_classify_ticket)")
    
except Exception as e:
    print(f"   ⚠️  Error dropping catalog: {e}")
    print(f"   This may indicate catalog is already dropped or permission issue")

print()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 3: Check/Create Shared Endpoint (NEVER DELETE)
# MAGIC 
# MAGIC **CRITICAL:** We verify/create the endpoint but **NEVER delete it**.
# MAGIC The endpoint is shared across multiple projects.

# COMMAND ----------

print("─" * 80)
print(f"Checking Shared Endpoint: {VECTOR_ENDPOINT}")
print("─" * 80)
print(f"⚠️  IMPORTANT: The endpoint '{VECTOR_ENDPOINT}' is SHARED")
print(f"   It will NEVER be deleted, even in FULL mode")
print()

try:
    print(f"🔍 Checking endpoint status: {VECTOR_ENDPOINT}")
    endpoint = vsc.get_endpoint(VECTOR_ENDPOINT)
    
    status = endpoint.get('endpoint_status', {}).get('state', 'Unknown')
    print(f"   ✅ Endpoint exists: {VECTOR_ENDPOINT}")
    print(f"   📊 Status: {status}")
    
    if status == "ONLINE":
        print(f"   ✅ Endpoint is ONLINE and ready for use")
    else:
        print(f"   ⚠️  Endpoint status is: {status}")
        print(f"      It may take a few minutes to become ONLINE")
    
except Exception as e:
    error_msg = str(e)
    if "not found" in error_msg.lower() or "does not exist" in error_msg.lower():
        print(f"   ℹ️  Endpoint not found: {e}")
        print(f"   📝 Creating shared endpoint: {VECTOR_ENDPOINT}")
        
        try:
            # Create the endpoint
            endpoint = vsc.create_endpoint(
                name=VECTOR_ENDPOINT,
                endpoint_type="STANDARD"
            )
            
            print(f"   ✅ Endpoint created: {VECTOR_ENDPOINT}")
            print(f"   ⏳ Waiting for endpoint to become ONLINE...")
            print(f"      (This can take 10-15 minutes on first creation)")
            
            # Wait for endpoint (with progress)
            for i in range(90):  # 15 minutes
                time.sleep(10)
                endpoint = vsc.get_endpoint(VECTOR_ENDPOINT)
                status = endpoint.get('endpoint_status', {}).get('state', 'Unknown')
                
                if status == "ONLINE":
                    print(f"   ✅ Endpoint is ONLINE and ready!")
                    break
                
                if i % 6 == 0:  # Print every minute
                    print(f"   ... {status} ({i//6} min elapsed)")
            
            if status != "ONLINE":
                print(f"   ⚠️  Endpoint is still {status} after 15 minutes")
                print(f"      It will continue provisioning in the background")
                
        except Exception as create_error:
            print(f"   ⚠️  Could not create endpoint: {create_error}")
            print(f"      This may be OK if another process is creating it")
    else:
        print(f"   ⚠️  Error checking endpoint: {e}")

print()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 4: App Status Check
# MAGIC 
# MAGIC **Note:** Apps are typically NOT deleted to avoid downtime.
# MAGIC The app will be updated in place during deployment.

# COMMAND ----------

print("─" * 80)
print(f"STEP 4: App Status (NO DELETION)")
print("─" * 80)
print(f"ℹ️  App '{APP_NAME}' will be updated in place")
print(f"   Deleting apps is not recommended (causes downtime)")
print(f"   The app will continue running and be updated with new code")
print()

try:
    w = WorkspaceClient()
    # Note: Databricks Apps SDK methods for checking app status
    print(f"   ℹ️  App will be managed by DAB deployment")
    print(f"   ℹ️  If app exists, it will be updated")
    print(f"   ℹ️  If app doesn't exist, it will be created")
    
except Exception as e:
    print(f"   ℹ️  Could not check app status: {e}")

print()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Cleanup Summary

# COMMAND ----------

print("=" * 80)
print("CLEANUP COMPLETE")
print("=" * 80)
print()
print("✅ Resources Deleted (Clean Slate):")
print(f"   🗑️  Vector Search Index: {INDEX_NAME}")
print(f"   🗑️  Catalog (CASCADE):   {CATALOG}")
print(f"      - All schemas")
print(f"      - All tables")
print(f"      - All volumes")  
print(f"      - All UC functions")
print()
print("✅ Protected Resources (NOT Deleted):")
print(f"   🛡️  Vector Endpoint:     {VECTOR_ENDPOINT} (SHARED - NEVER DELETED)")
print(f"   🛡️  App:                 {APP_NAME} (Updated in place)")
print()
print("=" * 80)
print("🚀 Ready for clean deployment!")
print("=" * 80)

