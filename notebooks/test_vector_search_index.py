# Databricks notebook source
# MAGIC %md
# MAGIC # Vector Search Index Test - Check Guide Documents
# MAGIC 
# MAGIC This notebook tests if the Guide documents are properly indexed in Vector Search.

# COMMAND ----------

# MAGIC %pip install databricks-vectorsearch
# MAGIC dbutils.library.restartPython()

# COMMAND ----------

from databricks.vector_search.client import VectorSearchClient
from databricks.sdk import WorkspaceClient
import json

# Configuration
CATALOG = "classify_tickets_new_dev"
SCHEMA = "support_ai"
INDEX_NAME = f"{CATALOG}.{SCHEMA}.knowledge_base_index"
VECTOR_ENDPOINT = "one-env-shared-endpoint-2"

print("=" * 80)
print("VECTOR SEARCH INDEX TEST")
print("=" * 80)
print(f"Index: {INDEX_NAME}")
print(f"Endpoint: {VECTOR_ENDPOINT}")
print("=" * 80)

# COMMAND ----------

# Initialize clients
vsc = VectorSearchClient(disable_notice=True)
w = WorkspaceClient()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 1: Check Index Status

# COMMAND ----------

try:
    index = vsc.get_index(VECTOR_ENDPOINT, INDEX_NAME)
    desc = index.describe()
    
    print("📊 Index Status:")
    print(f"   Status: {desc.get('status', {}).get('state', 'Unknown')}")
    print(f"   Source Table: {desc.get('source_table', 'Unknown')}")
    
    # Check index stats if available
    stats = desc.get('index_stats', {})
    if stats:
        print(f"   Number of vectors: {stats.get('num_vectors', 'N/A')}")
        print(f"   Total tokens: {stats.get('total_tokens', 'N/A')}")
    
    # Check sync status
    sync_status = desc.get('sync_status', {})
    if sync_status:
        print(f"   Last sync time: {sync_status.get('last_sync_time', 'N/A')}")
        print(f"   Sync status: {sync_status.get('status', 'N/A')}")
    
    print("\n✅ Index is accessible")
    
except Exception as e:
    print(f"❌ Error accessing index: {e}")
    raise

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 2: Test Query for Cloud Resources (Guide documents)

# COMMAND ----------

print("\n" + "=" * 80)
print("TEST QUERY 1: Cloud Resources")
print("=" * 80)

query_text = "How do I scale an EC2 instance or manage cloud resources?"

try:
    response = w.api_client.do(
        'POST',
        f'/api/2.0/vector-search/indexes/{INDEX_NAME}/query',
        body={
            "columns": ["doc_id", "doc_type", "title", "content"],
            "num_results": 5,
            "query_text": query_text
        }
    )
    
    print(f"Query: {query_text}\n")
    
    if 'error_code' in response:
        print(f"❌ Error: {response.get('message', 'Unknown error')}")
    else:
        data_array = response.get('result', {}).get('data_array', [])
        print(f"✅ Found {len(data_array)} results\n")
        
        if data_array:
            print("Results:")
            for i, row in enumerate(data_array, 1):
                doc_id, doc_type, title, content = row
                print(f"\n  Result {i}:")
                print(f"    Doc ID: {doc_id}")
                print(f"    Doc Type: {doc_type}")
                print(f"    Title: {title}")
                print(f"    Content Preview: {content[:150]}...")
                
                # Check if it's a Guide document
                if doc_type == "Guide":
                    print(f"    ✅ GUIDE DOCUMENT FOUND!")
        else:
            print("⚠️  No results returned")
            
except Exception as e:
    print(f"❌ Query error: {e}")
    import traceback
    traceback.print_exc()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 3: Test Query for Email Issues (Guide documents)

# COMMAND ----------

print("\n" + "=" * 80)
print("TEST QUERY 2: Email Issues")
print("=" * 80)

query_text = "Email delivery issues or cannot login to email account"

try:
    response = w.api_client.do(
        'POST',
        f'/api/2.0/vector-search/indexes/{INDEX_NAME}/query',
        body={
            "columns": ["doc_id", "doc_type", "title", "content"],
            "num_results": 5,
            "query_text": query_text
        }
    )
    
    print(f"Query: {query_text}\n")
    
    if 'error_code' in response:
        print(f"❌ Error: {response.get('message', 'Unknown error')}")
    else:
        data_array = response.get('result', {}).get('data_array', [])
        print(f"✅ Found {len(data_array)} results\n")
        
        if data_array:
            print("Results:")
            for i, row in enumerate(data_array, 1):
                doc_id, doc_type, title, content = row
                print(f"\n  Result {i}:")
                print(f"    Doc ID: {doc_id}")
                print(f"    Doc Type: {doc_type}")
                print(f"    Title: {title}")
                print(f"    Content Preview: {content[:150]}...")
                
                # Check if it's a Guide document
                if doc_type == "Guide":
                    print(f"    ✅ GUIDE DOCUMENT FOUND!")
        else:
            print("⚠️  No results returned")
            
except Exception as e:
    print(f"❌ Query error: {e}")
    import traceback
    traceback.print_exc()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 4: Check All Doc Types in Results

# COMMAND ----------

print("\n" + "=" * 80)
print("TEST QUERY 3: Generic Query (Check Doc Types)")
print("=" * 80)

query_text = "troubleshooting IT issues"

try:
    response = w.api_client.do(
        'POST',
        f'/api/2.0/vector-search/indexes/{INDEX_NAME}/query',
        body={
            "columns": ["doc_id", "doc_type", "title"],
            "num_results": 20,  # Get more results to see distribution
            "query_text": query_text
        }
    )
    
    print(f"Query: {query_text}\n")
    
    if 'error_code' in response:
        print(f"❌ Error: {response.get('message', 'Unknown error')}")
    else:
        data_array = response.get('result', {}).get('data_array', [])
        print(f"✅ Found {len(data_array)} results\n")
        
        if data_array:
            # Count doc types
            doc_type_counts = {}
            for row in data_array:
                doc_type = row[1]  # Second column is doc_type
                doc_type_counts[doc_type] = doc_type_counts.get(doc_type, 0) + 1
            
            print("Document Types in Results:")
            for doc_type, count in sorted(doc_type_counts.items()):
                marker = "✅" if doc_type == "Guide" else "  "
                print(f"  {marker} {doc_type}: {count} documents")
            
            print("\nDetailed Results:")
            for i, row in enumerate(data_array, 1):
                doc_id, doc_type, title = row
                marker = "✅" if doc_type == "Guide" else "  "
                print(f"  {marker} {i}. [{doc_type}] {title}")
        else:
            print("⚠️  No results returned")
            
except Exception as e:
    print(f"❌ Query error: {e}")
    import traceback
    traceback.print_exc()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 5: Trigger Manual Sync (if needed)

# COMMAND ----------

print("\n" + "=" * 80)
print("OPTIONAL: Trigger Manual Sync")
print("=" * 80)

# Uncomment the lines below to trigger a manual sync
# This will sync any new records from the source table

try:
    index = vsc.get_index(VECTOR_ENDPOINT, INDEX_NAME)
    print("⏳ Triggering manual sync...")
    index.sync()
    print("✅ Sync triggered!")
    print("   Wait 1-2 minutes for embeddings to generate")
    print("   Then re-run the queries above to check if Guide documents appear")
except Exception as e:
    print(f"⚠️  Sync error: {e}")
    print("   You can manually trigger sync from the Vector Search UI")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Summary
# MAGIC 
# MAGIC **What to look for:**
# MAGIC - ✅ If Guide documents appear in results → Index is working correctly
# MAGIC - ❌ If Guide documents DON'T appear → Index needs to be synced
# MAGIC 
# MAGIC **If Guide documents are missing:**
# MAGIC 1. Click "Sync now" button in Vector Search UI
# MAGIC 2. Or uncomment the sync code above and run it
# MAGIC 3. Wait 1-2 minutes for embeddings
# MAGIC 4. Re-run the queries

