# Databricks notebook source
# MAGIC %md
# MAGIC # Test Genie API - Following Medium Article Approach
# MAGIC
# MAGIC Testing the exact approach from: https://databrickster.medium.com/call-genie-and-build-your-own-data-chat-2dfe6ae4b1a8

# COMMAND ----------

from databricks.sdk import WorkspaceClient
import time
import json

w = WorkspaceClient()

# Configuration
GENIE_SPACE_ID = "01f0b91aa91c1b0c8cce6529ea09f0a8"
WAREHOUSE_ID = "148ccb90800933a1"  # Correct SQL warehouse

print(f"Genie Space ID: {GENIE_SPACE_ID}")
print(f"Warehouse ID: {WAREHOUSE_ID}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 1: Start Conversation

# COMMAND ----------

question = "Show me 3 recent tickets from the Applications team with their resolution details"

print(f"🔹 Starting conversation with question: {question}")

# Start conversation
start_response = w.api_client.do(
    'POST',
    f'/api/2.0/genie/spaces/{GENIE_SPACE_ID}/start-conversation',
    body={'content': question}
)

print(f"\n✅ Start Conversation Response:")
print(json.dumps(start_response, indent=2, default=str))

conversation_id = start_response.get('conversation', {}).get('id')
message_id = start_response.get('message', {}).get('id')

print(f"\n📌 Conversation ID: {conversation_id}")
print(f"📌 Message ID: {message_id}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 2: Poll for Completion

# COMMAND ----------

print(f"🔹 Polling for completion...")

max_wait = 120  # 2 minutes
poll_interval = 5
start_time = time.time()
status = ""

while (time.time() - start_time) < max_wait and status != "COMPLETED":
    time.sleep(poll_interval)
    
    poll_response = w.api_client.do(
        'GET',
        f'/api/2.0/genie/spaces/{GENIE_SPACE_ID}/conversations/{conversation_id}/messages/{message_id}'
    )
    
    status = poll_response.get('status', 'UNKNOWN')
    elapsed = time.time() - start_time
    print(f"  Status: {status}, Elapsed: {elapsed:.1f}s")
    
    if status in ['COMPLETED', 'FAILED', 'CANCELLED']:
        break

print(f"\n✅ Final status: {status}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 3: View Full Message Response

# COMMAND ----------

print(f"📋 Full Message Response:")
print(json.dumps(poll_response, indent=2, default=str))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 4: Extract Attachments

# COMMAND ----------

attachments = poll_response.get('attachments', [])
print(f"📎 Number of attachments: {len(attachments)}")

if attachments:
    for i, attachment in enumerate(attachments):
        print(f"\n{'='*80}")
        print(f"ATTACHMENT {i+1}")
        print(f"{'='*80}")
        print(json.dumps(attachment, indent=2, default=str))
        
        # Extract key information
        attachment_id = attachment.get('id')
        attachment_type = attachment.get('type')
        
        print(f"\n🔑 Attachment ID: {attachment_id}")
        print(f"🔑 Attachment Type: {attachment_type}")
        
        # Extract text
        text_obj = attachment.get('text', {})
        if text_obj:
            text_content = text_obj.get('content', '')
            print(f"\n💬 Text Response:")
            print(text_content)
        
        # Extract query
        query_obj = attachment.get('query', {})
        if query_obj:
            print(f"\n📊 Query Object Keys: {list(query_obj.keys())}")
            sql_query = query_obj.get('query', query_obj.get('content', ''))
            if sql_query:
                print(f"\n💾 SQL Query:")
                print(sql_query)
else:
    print("⚠️ No attachments found!")
    print(f"Response keys: {list(poll_response.keys())}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 5: Try query-result Endpoint (if attachment_id exists)

# COMMAND ----------

if attachments and attachment_id:
    print(f"🔹 Trying query-result endpoint with attachment_id: {attachment_id}")
    
    try:
        query_result_response = w.api_client.do(
            'GET',
            f'/api/2.0/genie/spaces/{GENIE_SPACE_ID}/conversations/{conversation_id}/messages/{message_id}/query-result/{attachment_id}'
        )
        
        print(f"\n✅ Query Result Response:")
        print(json.dumps(query_result_response, indent=2, default=str))
        
        # Try to extract data
        manifest = query_result_response.get('manifest', {})
        if manifest:
            schema = manifest.get('schema', {})
            columns = schema.get('columns', [])
            print(f"\n📊 Columns: {[col.get('name') for col in columns]}")
            
            result_obj = query_result_response.get('result', {})
            data_array = result_obj.get('data_array', [])
            print(f"📊 Number of rows: {len(data_array)}")
            
            if data_array:
                print(f"\n📋 First row: {data_array[0]}")
        
    except Exception as e:
        print(f"\n❌ Error calling query-result endpoint:")
        print(str(e))
        import traceback
        print(traceback.format_exc())
else:
    print("⚠️ No attachment_id found, skipping query-result endpoint")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 6: FALLBACK - Execute SQL Directly

# COMMAND ----------

if sql_query:
    print(f"🔹 FALLBACK: Executing SQL query directly...")
    print(f"SQL: {sql_query}")
    
    try:
        from databricks.sdk.service.sql import StatementState
        
        execute_response = w.statement_execution.execute_statement(
            warehouse_id=WAREHOUSE_ID,
            statement=sql_query,
            wait_timeout='30s'
        )
        
        print(f"\n✅ Execution Status: {execute_response.status.state}")
        
        if execute_response.status.state == StatementState.SUCCEEDED:
            columns = execute_response.manifest.schema.columns if execute_response.manifest and execute_response.manifest.schema else []
            column_names = [col.name for col in columns]
            print(f"📊 Columns: {column_names}")
            
            if execute_response.result and execute_response.result.data_array:
                data_array = execute_response.result.data_array
                print(f"📊 Number of rows: {len(data_array)}")
                
                # Display results
                for i, row in enumerate(data_array):
                    row_dict = dict(zip(column_names, row))
                    print(f"\n🎫 Ticket {i+1}:")
                    print(json.dumps(row_dict, indent=2, default=str))
        else:
            error_msg = execute_response.status.error.message if execute_response.status.error else "Unknown error"
            print(f"❌ Execution failed: {error_msg}")
            
    except Exception as e:
        print(f"\n❌ Error executing SQL:")
        print(str(e))
        import traceback
        print(traceback.format_exc())
else:
    print("⚠️ No SQL query found")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Summary

# COMMAND ----------

print(f"{'='*80}")
print("SUMMARY")
print(f"{'='*80}")
print(f"Question: {question}")
print(f"Status: {status}")
print(f"Conversation ID: {conversation_id}")
print(f"Message ID: {message_id}")
print(f"Number of Attachments: {len(attachments)}")
if attachments:
    print(f"Attachment ID: {attachment_id}")
if sql_query:
    print(f"SQL Query Generated: YES")
    print(f"SQL: {sql_query[:100]}...")
print(f"{'='*80}")

