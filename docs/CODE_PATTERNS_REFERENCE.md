# Code Patterns Reference: UC Functions, Vector Search, Genie as Tools

**Purpose:** Quick reference for implementing UC Functions, Vector Search, and Genie API as both standalone functions and LangChain Tools

**Last Updated:** November 7, 2025

---

## 📍 Where All Patterns Are Saved

### **Complete Implementation:**
- **File:** `docs/REFERENCE_23_langraph_agent_learning.py`
- **Lines:** 1,073 lines of fully-commented code
- **Contains:** All patterns below with educational comments

### **This Guide:**
- Quick reference with line numbers
- Copy-paste ready code snippets
- Best practices and gotchas

---

## 🔧 **Pattern 1: UC Function Calls (Statement Execution API)**

### **Location:** Lines 100-153 in REFERENCE_23_langraph_agent_learning.py

### **Code Pattern:**

```python
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.sql import StatementState
import json

def call_uc_function(function_name: str, parameters: dict):
    """
    Call a UC function using Statement Execution API.
    More reliable than w.functions.execute() for Databricks Apps.
    
    Args:
        function_name: Name of UC function (e.g., "ai_classify")
        parameters: Dict of parameter name → value
        
    Returns:
        Dict: Result from UC function (already parsed from JSON)
    """
    try:
        w = WorkspaceClient()
        
        # Build SQL query with parameters
        param_values = []
        for key, value in parameters.items():
            if isinstance(value, str):
                # IMPORTANT: Escape single quotes for SQL
                escaped = value.replace("'", "''")
                param_values.append(f"'{escaped}'")
            else:
                param_values.append(str(value))
        
        args_str = ', '.join(param_values)
        query = f"SELECT {CATALOG}.{SCHEMA}.{function_name}({args_str}) as result"
        
        # Execute via Statement Execution API
        response = w.statement_execution.execute_statement(
            warehouse_id=WAREHOUSE_ID,
            statement=query,
            wait_timeout='30s'
        )
        
        if response.status.state == StatementState.SUCCEEDED:
            # Extract result from response
            if response.result and response.result.data_array:
                result_json = response.result.data_array[0][0]
                result = json.loads(result_json) if isinstance(result_json, str) else result_json
                return result
            else:
                return {"error": "No data returned"}
        else:
            error_msg = response.status.error.message if response.status.error else "Unknown error"
            return {"error": error_msg}
        
    except Exception as e:
        return {"error": str(e)}
```

### **Usage:**

```python
# Example 1: Classify ticket
result = call_uc_function(
    "ai_classify",
    {"ticket_text": "Database connection timeout"}
)
# Returns: {"category": "Technical", "priority": "High", "team": "Database Team"}

# Example 2: Extract metadata
result = call_uc_function(
    "ai_extract",
    {"ticket_text": "Urgent production issue"}
)
# Returns: {"priority_score": 9, "urgency": "High", "systems": ["Production"]}
```

### **Key Points:**
- ✅ Use Statement Execution API (not `w.functions.execute()`)
- ✅ Escape single quotes in string parameters
- ✅ Wait timeout of 30s is usually sufficient
- ✅ Always check `response.status.state`
- ✅ Parse JSON result from `data_array[0][0]`

### **Gotchas:**
- ❌ Warehouse cold start can take 30-60s on first call
- ❌ Don't forget to escape quotes in SQL strings
- ❌ Result is nested: `data_array[0][0]`, not just `data_array`

---

## 🔍 **Pattern 2: Vector Search**

### **Location:** Lines 192-231 in REFERENCE_23_langraph_agent_learning.py

### **Code Pattern:**

```python
from databricks.vector_search.client import VectorSearchClient

def search_knowledge_base(query: str, num_results: int = 3):
    """
    Search knowledge base using Vector Search with Delta Sync.
    Uses workspace credentials automatically.
    
    Args:
        query: Natural language search query
        num_results: Number of results to return (default 3)
        
    Returns:
        List of dicts with doc_id, doc_type, title, content, score
    """
    try:
        # Initialize VectorSearchClient
        # Uses workspace authentication from environment
        vsc = VectorSearchClient()
        
        # Get the index and perform similarity search
        results = vsc.get_index(
            index_name=INDEX_NAME  # e.g., "catalog.schema.index_name"
        ).similarity_search(
            query_text=query,
            columns=["doc_id", "doc_type", "title", "content"],  # Specify columns to return
            num_results=num_results
        )
        
        # Extract and format results
        docs = results.get('result', {}).get('data_array', [])
        
        formatted_results = [
            {
                "doc_id": doc[0],
                "doc_type": doc[1],
                "title": doc[2],
                "content": doc[3][:200] + "..." if len(doc[3]) > 200 else doc[3],  # Truncate long content
                "score": doc[4] if len(doc) > 4 else None  # Similarity score
            }
            for doc in docs
        ]
        
        return formatted_results
        
    except Exception as e:
        print(f"Vector Search Error: {str(e)}")
        return []
```

### **Usage:**

```python
# Search for database-related documentation
results = search_knowledge_base(
    query="database timeout connection pool configuration",
    num_results=3
)

# Results structure:
# [
#   {
#     "doc_id": "KB-001",
#     "doc_type": "troubleshooting",
#     "title": "Database Timeout Issues",
#     "content": "Common causes of database timeouts...",
#     "score": 0.8523
#   },
#   ...
# ]
```

### **Key Points:**
- ✅ VectorSearchClient uses workspace auth automatically
- ✅ Specify columns to return (saves bandwidth)
- ✅ Truncate long content for display
- ✅ Score is similarity metric (0-1, higher = more relevant)

### **Gotchas:**
- ❌ Index must be synced and online
- ❌ Results come as nested arrays (doc values in order of columns)
- ❌ Empty results return `[]`, not error

---

## 🤖 **Pattern 3: Genie Conversation API**

### **Location:** Lines 257-481 in REFERENCE_23_langraph_agent_learning.py

### **Code Pattern:**

```python
from databricks.sdk import WorkspaceClient
import time

class GenieConversationTool:
    """
    Genie Conversation API wrapper using WorkspaceClient.
    Handles: start conversation → poll → fetch data
    """
    
    def __init__(self, workspace_client: WorkspaceClient, space_id: str):
        self.w = workspace_client
        self.space_id = space_id
    
    def start_conversation(self, question: str):
        """Start a new Genie conversation"""
        try:
            response = self.w.api_client.do(
                'POST',
                f'/api/2.0/genie/spaces/{self.space_id}/start-conversation',
                body={'content': question}
            )
            
            return {
                'status': 'started',
                'conversation_id': response.get('conversation_id'),
                'message_id': response.get('message_id')
            }
        except Exception as e:
            return {'status': 'error', 'error': str(e)}
    
    def poll_for_result(self, conversation_id: str, message_id: str, max_wait_seconds: int = 120):
        """Poll for query completion with exponential backoff"""
        start_time = time.time()
        poll_interval = 2
        
        while time.time() - start_time < max_wait_seconds:
            try:
                response = self.w.api_client.do(
                    'GET',
                    f'/api/2.0/genie/spaces/{self.space_id}/conversations/{conversation_id}/messages/{message_id}'
                )
                
                status = response.get('status')
                
                if status == 'COMPLETED':
                    return {'status': 'completed', 'response': response}
                elif status == 'FAILED':
                    return {'status': 'failed', 'response': response}
                
                time.sleep(poll_interval)
                poll_interval = min(poll_interval * 1.2, 10)  # Exponential backoff
                
            except Exception as e:
                time.sleep(poll_interval)
        
        return {'status': 'timeout'}
    
    def query(self, question: str):
        """
        Complete Genie query workflow: start → poll → fetch data
        
        Returns:
            Dict with 'text', 'query' (SQL), 'data' (rows), 'method'
        """
        # Step 1: Start conversation
        start_result = self.start_conversation(question)
        if start_result.get('status') != 'started':
            return {"error": start_result.get('error')}
        
        conversation_id = start_result['conversation_id']
        message_id = start_result['message_id']
        
        # Step 2: Poll for completion
        poll_result = self.poll_for_result(conversation_id, message_id)
        
        if poll_result.get('status') != 'completed':
            return {"error": "Query did not complete"}
        
        # Step 3: Extract results
        response = poll_result['response']
        attachments = response.get('attachments', [])
        
        result = {
            "text": response.get('content', ''),
            "query": None,
            "data": None
        }
        
        if attachments:
            attachment = attachments[0]
            attachment_id = attachment.get('attachment_id')
            
            # Extract SQL query
            query_obj = attachment.get('query', {})
            if isinstance(query_obj, dict):
                result['query'] = query_obj.get('query')
            
            # Step 4: Fetch actual data
            if attachment_id:
                try:
                    query_result = self.w.api_client.do(
                        'GET',
                        f'/api/2.0/genie/spaces/{self.space_id}/conversations/{conversation_id}/messages/{message_id}/query-result/{attachment_id}'
                    )
                    
                    # Parse data from statement_response
                    statement_response = query_result.get('statement_response', {})
                    manifest = statement_response.get('manifest', {})
                    columns = manifest.get('schema', {}).get('columns', [])
                    column_names = [col.get('name') for col in columns]
                    
                    data_array = statement_response.get('result', {}).get('data_array', [])
                    
                    # Convert to list of dicts
                    result['data'] = [
                        dict(zip(column_names, row))
                        for row in data_array
                    ]
                    result['method'] = 'Genie query-result API'
                    
                except Exception as e:
                    print(f"Error fetching data: {e}")
        
        # FALLBACK: Execute SQL directly if Genie API fails
        if result.get('query') and not result.get('data'):
            result['used_fallback'] = True
            try:
                from databricks.sdk.service.sql import StatementState
                
                execute_response = self.w.statement_execution.execute_statement(
                    warehouse_id=WAREHOUSE_ID,
                    statement=result['query'],
                    wait_timeout='30s'
                )
                
                if execute_response.status.state == StatementState.SUCCEEDED:
                    columns = execute_response.manifest.schema.columns
                    column_names = [col.name for col in columns]
                    data_array = execute_response.result.data_array
                    
                    result['data'] = [
                        dict(zip(column_names, row))
                        for row in data_array
                    ]
                    result['method'] = 'Direct SQL Execution (Fallback)'
            except Exception as e:
                print(f"Fallback execution error: {e}")
        
        return result
```

### **Usage:**

```python
w = WorkspaceClient()
genie = GenieConversationTool(w, GENIE_SPACE_ID)

# Query historical tickets
result = genie.query("Show me 3 recent resolved tickets about database issues")

# Result structure:
# {
#   "text": "Here are 3 recent resolved database tickets...",
#   "query": "SELECT * FROM tickets WHERE category='database' AND status='resolved' LIMIT 3",
#   "data": [
#     {"ticket_id": "T001", "description": "...", "resolution": "..."},
#     ...
#   ],
#   "method": "Genie query-result API" or "Direct SQL Execution (Fallback)"
# }
```

### **Key Points:**
- ✅ Three-step process: start → poll → fetch
- ✅ Exponential backoff for polling
- ✅ Fallback to direct SQL execution if Genie API fails
- ✅ Returns both text summary and actual data rows

### **Gotchas:**
- ❌ Can take 15-30 seconds to complete
- ❌ Polling is required (no webhooks/callbacks)
- ❌ Field name is `attachment_id`, not `id`
- ❌ Data parsing is complex (nested structure)

---

## 🧰 **Pattern 4: Wrapping as LangChain Tools**

### **Location:** Lines 543-598 in REFERENCE_23_langraph_agent_learning.py

### **Code Pattern:**

```python
from langchain_core.tools import Tool
from pydantic import BaseModel, Field

# Step 1: Define Pydantic schema for input validation
class ClassifyTicketInput(BaseModel):
    ticket_text: str = Field(description="The support ticket text to classify")

# Step 2: Create wrapper function
def classify_ticket_wrapper(ticket_text: str) -> str:
    """Wrapper that returns JSON string"""
    result = call_uc_function("ai_classify", {"ticket_text": ticket_text})
    return json.dumps(result, indent=2)

# Step 3: Create LangChain Tool
classify_tool = Tool(
    name="classify_ticket",
    description="""Classifies a support ticket into category, priority, and routing team. 
    Use this FIRST to understand the ticket type. 
    Returns JSON with category, priority, team, confidence.""",
    func=classify_ticket_wrapper,
    args_schema=ClassifyTicketInput
)
```

### **Complete Tool Set:**

```python
# Tool 1: Classification
classify_tool = Tool(
    name="classify_ticket",
    description="Classifies ticket by category, priority, team. Use FIRST.",
    func=classify_ticket_wrapper,
    args_schema=ClassifyTicketInput
)

# Tool 2: Metadata Extraction
extract_tool = Tool(
    name="extract_metadata",
    description="Extracts metadata (urgency, systems, details). Use for complex technical issues.",
    func=extract_metadata_wrapper,
    args_schema=ExtractMetadataInput
)

# Tool 3: Knowledge Base Search
search_tool = Tool(
    name="search_knowledge",
    description="Searches KB for articles and solutions. Use for how-to guides, troubleshooting.",
    func=search_knowledge_wrapper,
    args_schema=SearchKnowledgeInput
)

# Tool 4: Historical Tickets (Genie)
genie_tool = Tool(
    name="query_historical",
    description="Queries historical tickets for similar cases. Use for complex issues where past patterns matter.",
    func=query_historical_wrapper,
    args_schema=QueryHistoricalInput
)
```

### **Key Points:**
- ✅ Always define Pydantic schema for inputs
- ✅ Wrapper function must return string (JSON string for complex data)
- ✅ Description guides agent when to use tool
- ✅ Be directive in descriptions ("Use FIRST", "Use for...")

### **Gotchas:**
- ❌ Function must return string, not dict
- ❌ Args schema must be Pydantic BaseModel
- ❌ Tool name should be snake_case

---

## 🤖 **Pattern 5: Using Tools in ReAct Agent**

### **Location:** Lines 725-788 in REFERENCE_23_langraph_agent_learning.py

### **Code Pattern:**

```python
from langgraph.prebuilt import create_react_agent
from databricks_langchain import ChatDatabricks
from langchain_core.messages import SystemMessage

# Step 1: Create LLM
llm = ChatDatabricks(
    endpoint="databricks-meta-llama-3-1-8b-instruct",
    temperature=0.3,
    max_tokens=4096
)

# Step 2: List all tools
tools_list = [classify_tool, extract_tool, search_tool, genie_tool]

# Step 3: Create agent (NO state_modifier in v1.0+)
agent = create_react_agent(
    model=llm,
    tools=tools_list
)

# Step 4: Invoke with system prompt
system_prompt = """You are an intelligent support ticket assistant.
Be efficient - only use tools that add value."""

result = agent.invoke({
    "messages": [
        SystemMessage(content=system_prompt),  # Goes FIRST
        ("user", "Analyze this ticket: Database timeout")
    ]
})
```

### **Key Points:**
- ✅ LangGraph v1.0+ pattern (no state_modifier)
- ✅ System message injected at invocation time
- ✅ Agent decides which tools to call
- ✅ All tools use WorkspaceClient (portable)

---

## 📊 **Pattern Comparison Table**

| Pattern | Standalone Use | As LangChain Tool | Best For |
|---------|---------------|-------------------|----------|
| **UC Functions** | Direct SQL execution | Wrap with Tool() | Classification, extraction |
| **Vector Search** | Direct client call | Wrap with Tool() | Semantic search |
| **Genie API** | Multi-step (start/poll/fetch) | Wrap with Tool() | Natural language SQL |
| **WorkspaceClient** | Required for all | Same client reused | Authentication |

---

## 📁 **Where Everything Lives**

### **Complete Code:**
- `docs/REFERENCE_23_langraph_agent_learning.py` (1,073 lines)
  - Lines 100-153: UC Functions
  - Lines 192-231: Vector Search
  - Lines 257-481: Genie API
  - Lines 543-598: LangChain Tool wrappers
  - Lines 725-788: ReAct Agent creation

### **Working Example:**
- `notebooks/23_langraph_agent_learning.py` (deployed in Databricks)
  - Same code as reference, ready to run

### **Validation:**
- `docs/REFERENCE_00_validate_environment.py` (396 lines)
  - Test each pattern individually

---

## 🎓 **Learning Path**

1. **Study standalone patterns first:**
   - UC Functions (Lines 100-153)
   - Vector Search (Lines 192-231)
   - Genie API (Lines 257-481)

2. **Learn tool wrapping:**
   - Tool creation (Lines 543-598)
   - Input schemas with Pydantic

3. **Build agent:**
   - Agent creation (Lines 725-730)
   - Invocation pattern (Lines 781-788)

4. **Test in notebook:**
   - Run `notebooks/23_langraph_agent_learning.py`
   - See patterns in action

---

## ✅ **Quick Checklist**

Before using these patterns:
- [ ] Have WorkspaceClient credentials
- [ ] Know your CATALOG, SCHEMA, WAREHOUSE_ID
- [ ] UC Functions deployed and working
- [ ] Vector Search index created and synced
- [ ] Genie Space ID available
- [ ] LLM endpoint accessible
- [ ] LangGraph v1.0+ installed

---

**All patterns saved, documented, and ready to use!** 🎉

Use `docs/REFERENCE_23_langraph_agent_learning.py` as your copy-paste source!

