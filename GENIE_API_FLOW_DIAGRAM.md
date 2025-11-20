# 🤖 Genie Conversation API Flow - Visual Diagram

## Overview
This diagram explains how the `GenieConversationTool` class queries historical ticket data using Databricks Genie API.

---

## 🔄 Complete Workflow Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                    USER / LANGGRAPH AGENT                            │
│                                                                       │
│  Question: "How many P1 tickets were created last month?"           │
└─────────────────────────────┬───────────────────────────────────────┘
                              │
                              │ genie_tool.query(question)
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     GenieConversationTool                            │
│                                                                       │
│  Initialized with:                                                   │
│  • space_id = "011fc5b45ea015bf881b167f7c3de23a"                   │
│  • WorkspaceClient (authenticated)                                   │
└─────────────────────────────┬───────────────────────────────────────┘
                              │
                              │ Step 1: Start Conversation
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    DATABRICKS GENIE API                              │
│                                                                       │
│  POST /api/2.0/genie/spaces/{space_id}/start-conversation           │
│                                                                       │
│  Request Body:                                                       │
│  {                                                                   │
│    "content": "How many P1 tickets were created last month?"       │
│  }                                                                   │
└─────────────────────────────┬───────────────────────────────────────┘
                              │
                              │ Returns conversation_id & message_id
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Response:                                                           │
│  {                                                                   │
│    "conversation_id": "abc-123-def",                                │
│    "message_id": "msg-456-ghi"                                      │
│  }                                                                   │
└─────────────────────────────┬───────────────────────────────────────┘
                              │
                              │ Step 2: Poll for Completion
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    POLLING LOOP (Max 120 seconds)                    │
│                                                                       │
│  Every 2-10 seconds (exponential backoff):                          │
│                                                                       │
│  GET /api/2.0/genie/spaces/{space_id}/conversations/                │
│      {conversation_id}/messages/{message_id}                         │
│                                                                       │
│  ┌────────────────────────────────────────────────────┐            │
│  │  Poll #1 (0.0s):   Status = EXECUTING_QUERY       │            │
│  │  Poll #2 (2.0s):   Status = EXECUTING_QUERY       │            │
│  │  Poll #3 (4.4s):   Status = EXECUTING_QUERY       │            │
│  │  Poll #4 (7.2s):   Status = COMPLETED ✅          │            │
│  └────────────────────────────────────────────────────┘            │
│                                                                       │
│  Status can be:                                                      │
│  • EXECUTING_QUERY → Keep polling                                   │
│  • COMPLETED       → Extract results ✅                             │
│  • FAILED          → Return error ❌                                │
│  • TIMEOUT         → Max wait exceeded ⏱️                          │
└─────────────────────────────┬───────────────────────────────────────┘
                              │
                              │ Step 3: Extract SQL & Attachments
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Completed Response:                                                 │
│  {                                                                   │
│    "status": "COMPLETED",                                           │
│    "content": "Here are the P1 tickets from last month...",        │
│    "attachments": [                                                 │
│      {                                                              │
│        "attachment_id": "attach-789",                              │
│        "query": {                                                  │
│          "query": "SELECT COUNT(*) FROM ticket_history            │
│                    WHERE priority='P1' AND                         │
│                    created_date >= '2024-12-01'"                   │
│        }                                                            │
│      }                                                              │
│    ]                                                                │
│  }                                                                   │
└─────────────────────────────┬───────────────────────────────────────┘
                              │
                              │ Step 4: Fetch Actual Data
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│  GET /api/2.0/genie/spaces/{space_id}/conversations/                │
│      {conversation_id}/messages/{message_id}/                        │
│      query-result/{attachment_id}                                    │
│                                                                       │
│  This endpoint returns the ACTUAL DATA ROWS                         │
└─────────────────────────────┬───────────────────────────────────────┘
                              │
                              │ Returns statement_response
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Query Result Response:                                              │
│  {                                                                   │
│    "statement_response": {                                          │
│      "manifest": {                                                  │
│        "schema": {                                                  │
│          "columns": [                                               │
│            {"name": "count", "type": "bigint"}                     │
│          ]                                                          │
│        }                                                            │
│      },                                                             │
│      "result": {                                                    │
│        "data_array": [                                             │
│          [42]  ← Actual data!                                      │
│        ]                                                            │
│      }                                                              │
│    }                                                                │
│  }                                                                   │
└─────────────────────────────┬───────────────────────────────────────┘
                              │
                              │ Step 5: Format Results
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Structured Result Object:                                           │
│  {                                                                   │
│    "text": "Here are the P1 tickets from last month...",          │
│    "query": "SELECT COUNT(*) FROM ticket_history WHERE...",        │
│    "data": [                                                        │
│      {"count": 42}                                                 │
│    ],                                                               │
│    "conversation_id": "abc-123-def",                               │
│    "message_id": "msg-456-ghi"                                     │
│  }                                                                   │
└─────────────────────────────┬───────────────────────────────────────┘
                              │
                              │ Return to Agent/User
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      FINAL ANSWER                                    │
│                                                                       │
│  "There were 42 P1 (critical) tickets created last month."         │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🔍 Detailed Step Breakdown

### Step 1: Start Conversation
```python
start_result = self.start_conversation(question)
# Returns: {'status': 'started', 'conversation_id': '...', 'message_id': '...'}
```

**API Call:**
```http
POST /api/2.0/genie/spaces/{space_id}/start-conversation
Content-Type: application/json

{
  "content": "How many P1 tickets were created last month?"
}
```

**What Genie Does:**
1. Receives natural language question
2. Analyzes table schema (`sample_tickets`)
3. Generates SQL query
4. Starts executing the query
5. Returns IDs to track progress

---

### Step 2: Poll for Completion
```python
poll_result = self.poll_for_result(conversation_id, message_id, max_wait_seconds=120)
```

**Polling Strategy:**
- Initial interval: 2 seconds
- Exponential backoff: `interval * 1.2` (max 10 seconds)
- Max total wait: 120 seconds

**Status Flow:**
```
EXECUTING_QUERY → EXECUTING_QUERY → EXECUTING_QUERY → COMPLETED ✅
                                                     ↘ FAILED ❌
```

**API Call (repeated):**
```http
GET /api/2.0/genie/spaces/{space_id}/conversations/{conversation_id}/messages/{message_id}
```

**Response Evolution:**
```javascript
// Poll #1 (2s)
{ "status": "EXECUTING_QUERY", "content": "", "attachments": [] }

// Poll #2 (4s)
{ "status": "EXECUTING_QUERY", "content": "", "attachments": [] }

// Poll #3 (7s)
{ 
  "status": "COMPLETED", 
  "content": "Here are the results...",
  "attachments": [...]  // ✅ Results ready!
}
```

---

### Step 3: Extract SQL & Attachments
```python
attachments = response.get('attachments', [])
attachment_id = attachments[0].get('attachment_id')
sql_query = attachments[0].get('query', {}).get('query')
```

**Attachment Structure:**
```json
{
  "attachment_id": "attach-789-xyz",
  "query": {
    "query": "SELECT COUNT(*) FROM langtutorial_vik.agents.sample_tickets WHERE priority='P1' AND created_date >= '2024-12-01'",
    "warehouse_id": "148ccb90800933a1"
  },
  "text": {
    "content": "Query returned 1 row"
  }
}
```

**Key Fields:**
- `attachment_id`: Needed to fetch actual data (Step 4)
- `query.query`: The SQL that Genie generated
- Text response is NOT the data - need Step 4!

---

### Step 4: Fetch Actual Data
```python
query_result_response = self.w.api_client.do(
    'GET',
    f'/api/2.0/genie/spaces/{space_id}/conversations/{conversation_id}/messages/{message_id}/query-result/{attachment_id}'
)
```

**⚠️ CRITICAL:** The previous response doesn't include data rows! You must call this endpoint!

**API Call:**
```http
GET /api/2.0/genie/spaces/{space_id}/conversations/{conversation_id}/
    messages/{message_id}/query-result/{attachment_id}
```

**Response Structure:**
```json
{
  "statement_response": {
    "manifest": {
      "schema": {
        "columns": [
          {"name": "priority", "type": "string"},
          {"name": "count", "type": "bigint"}
        ]
      }
    },
    "result": {
      "data_array": [
        ["P1", 42],
        ["P2", 156],
        ["P3", 301],
        ["P4", 89]
      ]
    }
  }
}
```

---

### Step 5: Format Results
```python
# Extract columns
columns = schema.get('columns', [])
column_names = [col.get('name') for col in columns]
# ['priority', 'count']

# Extract data
data_array = result_obj.get('data_array', [])
# [['P1', 42], ['P2', 156], ...]

# Convert to list of dicts
result['data'] = []
for row in data_array:
    row_dict = dict(zip(column_names, row))
    result['data'].append(row_dict)
# [{'priority': 'P1', 'count': 42}, {'priority': 'P2', 'count': 156}, ...]
```

**Final Structured Result:**
```python
{
    "text": "Here are the ticket counts by priority...",
    "query": "SELECT priority, COUNT(*) as count FROM sample_tickets GROUP BY priority",
    "data": [
        {"priority": "P1", "count": 42},
        {"priority": "P2", "count": 156},
        {"priority": "P3", "count": 301},
        {"priority": "P4", "count": 89}
    ],
    "conversation_id": "abc-123-def",
    "message_id": "msg-456-ghi"
}
```

---

## 🎯 Key Points to Remember

### 1. **Two-Phase Data Retrieval**
```
Phase 1: Poll endpoint    → Get SQL query + attachment_id
Phase 2: Query-result     → Get actual data rows
```

### 2. **Field Names Matter**
```python
# ✅ CORRECT
attachment_id = attachment.get('attachment_id')

# ❌ WRONG (common mistake)
attachment_id = attachment.get('id')
```

### 3. **Data is Nested**
```
response
  └─ statement_response
      ├─ manifest
      │   └─ schema
      │       └─ columns[]
      └─ result
          └─ data_array[]  ← Actual data here!
```

### 4. **Polling is Essential**
- Queries take 2-10 seconds typically
- Always use exponential backoff
- Handle TIMEOUT gracefully

### 5. **Error Handling**
```python
# Check at every step:
if start_result.get('status') != 'started':
    return {"error": "Failed to start"}

if poll_status == 'failed':
    return {"error": poll_result.get('error')}

if not data_array:
    return {"error": "No data returned"}
```

---

## 🔧 How It's Used in LangGraph Agent

### As a LangChain Tool:
```python
genie_tool = Tool(
    name="query_historical_tickets",
    description="Query historical ticket data using natural language",
    func=lambda q: genie_conversation.query(q)
)
```

### Agent Decides When to Use:
```
User: "What were the most common issues last week?"

Agent Reasoning:
1. This needs historical data → Use Genie tool ✅
2. Not about classification → Don't use ai_classify ❌
3. Not about knowledge base → Don't use vector search ❌

Action: query_historical_tickets("Show top 5 ticket categories from last 7 days")
```

### Example Flow:
```
┌──────────────────────┐
│  LangGraph Agent     │
│  "Need historical    │
│   ticket stats"      │
└──────┬───────────────┘
       │
       │ Calls query_historical_tickets()
       ▼
┌──────────────────────┐
│  GenieConversation   │
│  Tool                │
└──────┬───────────────┘
       │
       │ Executes 5-step flow
       ▼
┌──────────────────────┐
│  Returns:            │
│  {                   │
│    "data": [...],   │
│    "query": "..."   │
│  }                   │
└──────┬───────────────┘
       │
       │ Agent formats response
       ▼
┌──────────────────────┐
│  "Last week had:     │
│  - 42 access issues  │
│  - 38 VPN problems   │
│  - 25 DB timeouts"   │
└──────────────────────┘
```

---

## 📊 Performance Characteristics

| Metric | Typical Value |
|--------|--------------|
| Start Conversation | 0.5-1s |
| Query Execution | 2-8s |
| Poll Interval | 2-10s (exponential) |
| Total Time | 5-15s |
| Max Timeout | 120s |

**Cost:**
- API calls: 4-6 per query (1 start + 3-5 polls)
- Data transfer: Minimal (JSON)
- Warehouse compute: Charged per query

---

## 🚨 Common Pitfalls

### ❌ Pitfall #1: Not calling query-result endpoint
```python
# ❌ WRONG - This doesn't have data!
data = response.get('attachments', [])
```

```python
# ✅ CORRECT - Call query-result endpoint
query_result_response = self.w.api_client.do('GET', query_result_url)
data = query_result_response['statement_response']['result']['data_array']
```

### ❌ Pitfall #2: Wrong field name
```python
# ❌ WRONG
attachment_id = attachment.get('id')  # Returns None!
```

```python
# ✅ CORRECT
attachment_id = attachment.get('attachment_id')
```

### ❌ Pitfall #3: Not handling nested structure
```python
# ❌ WRONG
data = response.get('data_array')  # Returns None!
```

```python
# ✅ CORRECT
data = response['statement_response']['result']['data_array']
```

### ❌ Pitfall #4: Not polling long enough
```python
# ❌ WRONG - Too short!
poll_result = self.poll_for_result(conv_id, msg_id, max_wait_seconds=5)
```

```python
# ✅ CORRECT - Give it time
poll_result = self.poll_for_result(conv_id, msg_id, max_wait_seconds=120)
```

---

## 🎓 Learning Takeaways

1. **Genie API is Async**: Start → Poll → Fetch pattern
2. **Two Endpoints for Data**: Poll for status, query-result for data
3. **Field Names are Specific**: `attachment_id`, not `id`
4. **Data is Deeply Nested**: `statement_response.result.data_array`
5. **Always Handle Errors**: Each step can fail independently
6. **Exponential Backoff**: Don't hammer the API
7. **Natural Language → SQL**: Genie does the translation automatically

---

**This flow enables the LangGraph agent to query historical ticket data using plain English!** 🚀

