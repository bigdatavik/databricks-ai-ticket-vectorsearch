#!/usr/bin/env python3
"""
Test Vector Search Index - Check if Guide documents are indexed
Can be run locally with databricks CLI configured
"""

import json
import sys
from databricks.sdk import WorkspaceClient
from databricks.vector_search.client import VectorSearchClient

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

try:
    # Initialize clients
    w = WorkspaceClient()
    vsc = VectorSearchClient(disable_notice=True)
    
    # Step 1: Check Index Status
    print("\n📊 Step 1: Checking Index Status...")
    print("-" * 80)
    
    index = vsc.get_index(VECTOR_ENDPOINT, INDEX_NAME)
    desc = index.describe()
    
    print(f"Status: {desc.get('status', {}).get('state', 'Unknown')}")
    print(f"Source Table: {desc.get('source_table', 'Unknown')}")
    
    stats = desc.get('index_stats', {})
    if stats:
        print(f"Number of vectors: {stats.get('num_vectors', 'N/A')}")
        print(f"Total tokens: {stats.get('total_tokens', 'N/A')}")
    
    sync_status = desc.get('sync_status', {})
    if sync_status:
        print(f"Last sync time: {sync_status.get('last_sync_time', 'N/A')}")
        print(f"Sync status: {sync_status.get('status', 'N/A')}")
    
    print("\n✅ Index is accessible")
    
    # Step 2: Test Query for Cloud Resources
    print("\n" + "=" * 80)
    print("📊 Step 2: Testing Query - Cloud Resources")
    print("=" * 80)
    
    query_text = "How do I scale an EC2 instance or manage cloud resources?"
    print(f"Query: {query_text}\n")
    
    response = w.api_client.do(
        'POST',
        f'/api/2.0/vector-search/indexes/{INDEX_NAME}/query',
        body={
            "columns": ["doc_id", "doc_type", "title", "content"],
            "num_results": 5,
            "query_text": query_text
        }
    )
    
    if 'error_code' in response:
        print(f"❌ Error: {response.get('message', 'Unknown error')}")
    else:
        data_array = response.get('result', {}).get('data_array', [])
        print(f"✅ Found {len(data_array)} results\n")
        
        guide_found = False
        if data_array:
            print("Results:")
            for i, row in enumerate(data_array, 1):
                doc_id, doc_type, title, content = row
                print(f"\n  Result {i}:")
                print(f"    Doc ID: {doc_id}")
                print(f"    Doc Type: {doc_type}")
                print(f"    Title: {title}")
                print(f"    Content Preview: {content[:150]}...")
                
                if doc_type == "Guide":
                    print(f"    ✅ GUIDE DOCUMENT FOUND!")
                    guide_found = True
        else:
            print("⚠️  No results returned")
        
        if not guide_found:
            print("\n⚠️  WARNING: No Guide documents found in results!")
    
    # Step 3: Test Query for Email Issues
    print("\n" + "=" * 80)
    print("📊 Step 3: Testing Query - Email Issues")
    print("=" * 80)
    
    query_text = "Email delivery issues or cannot login to email account"
    print(f"Query: {query_text}\n")
    
    response = w.api_client.do(
        'POST',
        f'/api/2.0/vector-search/indexes/{INDEX_NAME}/query',
        body={
            "columns": ["doc_id", "doc_type", "title", "content"],
            "num_results": 5,
            "query_text": query_text
        }
    )
    
    if 'error_code' in response:
        print(f"❌ Error: {response.get('message', 'Unknown error')}")
    else:
        data_array = response.get('result', {}).get('data_array', [])
        print(f"✅ Found {len(data_array)} results\n")
        
        guide_found = False
        if data_array:
            print("Results:")
            for i, row in enumerate(data_array, 1):
                doc_id, doc_type, title, content = row
                print(f"\n  Result {i}:")
                print(f"    Doc ID: {doc_id}")
                print(f"    Doc Type: {doc_type}")
                print(f"    Title: {title}")
                print(f"    Content Preview: {content[:150]}...")
                
                if doc_type == "Guide":
                    print(f"    ✅ GUIDE DOCUMENT FOUND!")
                    guide_found = True
        else:
            print("⚠️  No results returned")
        
        if not guide_found:
            print("\n⚠️  WARNING: No Guide documents found in results!")
    
    # Step 4: Check All Doc Types
    print("\n" + "=" * 80)
    print("📊 Step 4: Checking Doc Type Distribution")
    print("=" * 80)
    
    query_text = "troubleshooting IT issues"
    print(f"Query: {query_text}\n")
    
    response = w.api_client.do(
        'POST',
        f'/api/2.0/vector-search/indexes/{INDEX_NAME}/query',
        body={
            "columns": ["doc_id", "doc_type", "title"],
            "num_results": 20,
            "query_text": query_text
        }
    )
    
    if 'error_code' in response:
        print(f"❌ Error: {response.get('message', 'Unknown error')}")
    else:
        data_array = response.get('result', {}).get('data_array', [])
        print(f"✅ Found {len(data_array)} results\n")
        
        if data_array:
            doc_type_counts = {}
            for row in data_array:
                doc_type = row[1]
                doc_type_counts[doc_type] = doc_type_counts.get(doc_type, 0) + 1
            
            print("Document Types in Results:")
            guide_count = 0
            for doc_type, count in sorted(doc_type_counts.items()):
                marker = "✅" if doc_type == "Guide" else "  "
                print(f"  {marker} {doc_type}: {count} documents")
                if doc_type == "Guide":
                    guide_count = count
            
            print("\nDetailed Results (first 10):")
            for i, row in enumerate(data_array[:10], 1):
                doc_id, doc_type, title = row
                marker = "✅" if doc_type == "Guide" else "  "
                print(f"  {marker} {i}. [{doc_type}] {title}")
            
            if guide_count == 0:
                print("\n⚠️  WARNING: Guide documents are NOT in the index!")
                print("   Solution: Trigger a manual sync from Vector Search UI")
        else:
            print("⚠️  No results returned")
    
    # Summary
    print("\n" + "=" * 80)
    print("📋 SUMMARY")
    print("=" * 80)
    print("If Guide documents appeared in any results:")
    print("  ✅ Index is working correctly")
    print("  ✅ Guide documents are searchable")
    print("\nIf Guide documents did NOT appear:")
    print("  ⚠️  Index needs to be synced")
    print("  💡 Go to Vector Search UI and click 'Sync now'")
    print("  💡 Or run: index.sync() in a notebook")
    print("=" * 80)
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

