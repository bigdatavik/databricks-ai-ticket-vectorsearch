# Databricks notebook source
# MAGIC %md
# MAGIC # Debug Genie API Response Structure
# MAGIC
# MAGIC This notebook tests the Genie API to see the exact response structure

# COMMAND ----------

from databricks.sdk import WorkspaceClient
import time
import json

w = WorkspaceClient()

GENIE_SPACE_ID = "01f0b91aa91c1b0c8cce6529ea09f0a8"

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 1: Start Conversation

# COMMAND ----------

question = "Show me 3 recent tickets from the Applications team with their resolution details"

response = w.api_client.do(
    'POST',
    f'/api/2.0/genie/spaces/{GENIE_SPACE_ID}/start-conversation',
    body={'content': question}
)

print("Start Conversation Response:")
print(json.dumps(response, indent=2, default=str))

conversation_id = response.get('conversation', {}).get('id')
message_id = response.get('message', {}).get('id')

print(f"\nConversation ID: {conversation_id}")
print(f"Message ID: {message_id}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 2: Poll for Completion

# COMMAND ----------

max_wait = 60
poll_interval = 5
start_time = time.time()

while (time.time() - start_time) < max_wait:
    response = w.api_client.do(
        'GET',
        f'/api/2.0/genie/spaces/{GENIE_SPACE_ID}/conversations/{conversation_id}/messages/{message_id}'
    )
    
    status = response.get('status', 'UNKNOWN')
    print(f"Status: {status}")
    
    if status in ['COMPLETED', 'FAILED', 'CANCELLED']:
        print(f"\nFinal status: {status}")
        break
    
    time.sleep(poll_interval)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 3: View Full Message Response

# COMMAND ----------

print("Full Message Response:")
print(json.dumps(response, indent=2, default=str))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 4: Extract Attachment ID and Try query-result API

# COMMAND ----------

attachments = response.get('attachments', [])
print(f"Number of attachments: {len(attachments)}")

if attachments:
    attachment = attachments[0]
    attachment_id = attachment.get('id')
    print(f"\nAttachment ID: {attachment_id}")
    print(f"\nAttachment keys: {list(attachment.keys())}")
    print(f"\nFull Attachment:")
    print(json.dumps(attachment, indent=2, default=str))
    
    # COMMAND ----------
    
    # Try to get query results
    if attachment_id:
        try:
            print(f"\n{'='*80}")
            print(f"Calling query-result API...")
            print(f"{'='*80}")
            
            query_results = w.api_client.do(
                'GET',
                f'/api/2.0/genie/spaces/{GENIE_SPACE_ID}/conversations/{conversation_id}/messages/{message_id}/query-result/{attachment_id}'
            )
            
            print(f"\nQuery Results Response:")
            print(json.dumps(query_results, indent=2, default=str))
            
        except Exception as e:
            print(f"\nERROR calling query-result API: {str(e)}")
            print(f"This endpoint may not be available or may require different permissions")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 5: Check if Data is Already in Attachment

# COMMAND ----------

if attachments:
    attachment = attachments[0]
    
    # Check query object
    query_obj = attachment.get('query', {})
    if query_obj:
        print("Query object keys:", list(query_obj.keys()))
        print("\nQuery SQL:", query_obj.get('query', 'N/A'))
        
        # Check if result is already here
        if 'result' in query_obj:
            print("\n🎯 FOUND 'result' in query object!")
            print("Result keys:", list(query_obj['result'].keys()))
            print("\nFull result:")
            print(json.dumps(query_obj['result'], indent=2, default=str)[:2000])

