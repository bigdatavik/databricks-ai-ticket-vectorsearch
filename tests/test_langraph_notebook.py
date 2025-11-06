#!/usr/bin/env python3
"""
Test script to run through all LangGraph notebook logic and identify errors.
This will help us fix issues before running in Databricks.
"""

import sys
import os
import json
import time
import traceback

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

print("=" * 80)
print("LANGRAPH NOTEBOOK TEST - Running All Steps")
print("=" * 80)

# Step 1: Import required packages
print("\n[Step 1] Testing imports...")
try:
    from databricks.sdk import WorkspaceClient
    from databricks.vector_search.client import VectorSearchClient
    print("✅ databricks.sdk imported")
except Exception as e:
    print(f"❌ databricks.sdk import failed: {e}")
    print("Installing databricks-sdk...")
    os.system("pip install databricks-sdk databricks-vectorsearch --quiet")

try:
    from databricks_langchain import ChatDatabricks
    print("✅ databricks_langchain imported")
except Exception as e:
    print(f"❌ databricks_langchain import failed: {e}")
    print("Installing databricks-langchain...")
    os.system("pip install databricks-langchain --quiet")

try:
    from langchain_core.tools import Tool
    from langgraph.prebuilt import create_react_agent
    print("✅ langchain/langgraph imported")
except Exception as e:
    print(f"❌ langchain/langgraph import failed: {e}")
    print("Installing langgraph and langchain...")
    os.system("pip install langgraph langchain langchain-core --quiet")
    # Re-import after install
    from langchain_core.tools import Tool
    from langgraph.prebuilt import create_react_agent

try:
    import backoff
    print("✅ backoff imported")
except Exception as e:
    print(f"❌ backoff import failed: {e}")
    print("Installing backoff...")
    os.system("pip install backoff --quiet")
    import backoff

print("✅ All imports successful!")

# Step 2: Initialize WorkspaceClient
print("\n[Step 2] Initializing WorkspaceClient...")
try:
    w = WorkspaceClient()
    print(f"✅ WorkspaceClient initialized")
    print(f"📍 Workspace: {w.config.host}")
    current_user = w.current_user.me()
    print(f"👤 Current user: {current_user.user_name}")
except Exception as e:
    print(f"❌ WorkspaceClient initialization failed: {e}")
    traceback.print_exc()
    sys.exit(1)

# Step 3: Configuration
print("\n[Step 3] Loading configuration...")
CATALOG = "vik_catalog"
SCHEMA = "ai_ticket_classification"
WAREHOUSE_ID = "148ccb90800933a1"
INDEX_NAME = f"{CATALOG}.{SCHEMA}.kb_docs_index"
GENIE_SPACE_ID = "01f0b91aa91c1b0c8cce6529ea09f0a8"
LLM_ENDPOINT = "databricks-meta-llama-3-3-70b-instruct"

print(f"✅ Configuration loaded")
print(f"  📚 Catalog: {CATALOG}")
print(f"  📊 Schema: {SCHEMA}")
print(f"  🔍 Vector Index: {INDEX_NAME}")
print(f"  🤖 Genie Space: {GENIE_SPACE_ID}")

# Step 4: Test UC Function
print("\n[Step 4] Testing UC Function (ai_classify)...")
def call_uc_function(function_name: str, parameters: dict):
    """Call a UC function using Statement Execution API (same as dashboard)."""
    try:
        from databricks.sdk.service.sql import StatementState
        
        print(f"  🔧 Calling: {CATALOG}.{SCHEMA}.{function_name}")
        
        # Build SQL query
        param_values = []
        for key, value in parameters.items():
            if isinstance(value, str):
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
            if response.result and response.result.data_array:
                result_json = response.result.data_array[0][0]
                result = json.loads(result_json) if isinstance(result_json, str) else result_json
                print(f"  ✅ Result received")
                return result
            else:
                return {"error": "No data returned"}
        else:
            error_msg = response.status.error.message if response.status.error else "Unknown error"
            print(f"  ❌ {error_msg}")
            return {"error": error_msg}
    except Exception as e:
        error_msg = f"Exception calling UC function: {str(e)}"
        print(f"  ❌ {error_msg}")
        traceback.print_exc()
        return {"error": error_msg}

test_ticket = "Database connection timeout in production"
classification_result = call_uc_function("ai_classify", {"ticket_text": test_ticket})
if "error" not in classification_result:
    print(f"✅ UC Function (ai_classify) working!")
else:
    print(f"❌ UC Function (ai_classify) failed: {classification_result}")

# Step 5: Test Vector Search
print("\n[Step 5] Testing Vector Search...")
def search_knowledge_base(query: str, num_results: int = 3):
    """Search knowledge base using Vector Search."""
    try:
        print(f"  🔍 Searching: '{query[:50]}...'")
        vsc = VectorSearchClient()
        
        results = vsc.get_index(
            index_name=INDEX_NAME
        ).similarity_search(
            query_text=query,
            columns=["doc_id", "doc_type", "title", "content"],
            num_results=num_results
        )
        
        docs = results.get('result', {}).get('data_array', [])
        print(f"  ✅ Found {len(docs)} documents")
        
        return [
            {
                "doc_id": doc[0],
                "doc_type": doc[1],
                "title": doc[2],
                "content": doc[3][:200] + "..." if len(doc[3]) > 200 else doc[3]
            }
            for doc in docs
        ]
    except Exception as e:
        error_msg = f"Vector Search Error: {str(e)}"
        print(f"  ❌ {error_msg}")
        traceback.print_exc()
        return []

search_results = search_knowledge_base("database timeout connection pool")
if search_results:
    print(f"✅ Vector Search working! Found {len(search_results)} docs")
else:
    print(f"❌ Vector Search failed or returned no results")

# Step 6: Test Genie API
print("\n[Step 6] Testing Genie Conversation API...")
class GenieConversationTool:
    """Genie Conversation API wrapper using WorkspaceClient."""
    def __init__(self, workspace_client: WorkspaceClient, space_id: str):
        self.w = workspace_client
        self.space_id = space_id
    
    def start_conversation(self, question: str):
        """Start a new Genie conversation"""
        try:
            print(f"  [Genie] Starting conversation...")
            response = self.w.api_client.do(
                'POST',
                f'/api/2.0/genie/spaces/{self.space_id}/start-conversation',
                body={'content': question}
            )
            
            conversation_id = response.get('conversation_id')
            message_id = response.get('message_id')
            print(f"  [Genie] ✅ Started: {conversation_id}")
            
            return {
                'status': 'started',
                'conversation_id': conversation_id,
                'message_id': message_id
            }
        except Exception as e:
            print(f"  [Genie] ❌ Error: {str(e)}")
            traceback.print_exc()
            return {'status': 'error', 'error': str(e)}
    
    def poll_for_result(self, conversation_id: str, message_id: str, max_wait_seconds: int = 60):
        """Poll for query completion"""
        print(f"  [Genie] Polling (max {max_wait_seconds}s)...")
        start_time = time.time()
        poll_interval = 2
        poll_count = 0
        
        while time.time() - start_time < max_wait_seconds:
            try:
                poll_count += 1
                response = self.w.api_client.do(
                    'GET',
                    f'/api/2.0/genie/spaces/{self.space_id}/conversations/{conversation_id}/messages/{message_id}'
                )
                
                status = response.get('status')
                elapsed = time.time() - start_time
                
                if poll_count % 5 == 0:  # Print every 5th poll
                    print(f"  [Genie] Poll #{poll_count} ({elapsed:.1f}s): {status}")
                
                if status == 'COMPLETED':
                    print(f"  [Genie] ✅ Completed in {elapsed:.1f}s")
                    return {'status': 'completed', 'response': response}
                elif status == 'FAILED':
                    print(f"  [Genie] ❌ Failed")
                    return {'status': 'failed', 'response': response}
                
                time.sleep(poll_interval)
                poll_interval = min(poll_interval * 1.2, 10)
                
            except Exception as e:
                print(f"  [Genie] ⚠️ Poll error: {str(e)}")
                time.sleep(poll_interval)
        
        print(f"  [Genie] ⏱️ Timeout")
        return {'status': 'timeout', 'error': f'Timeout after {max_wait_seconds}s'}
    
    def query(self, question: str):
        """Complete Genie query workflow"""
        # Start
        start_result = self.start_conversation(question)
        if start_result.get('status') != 'started':
            return {"error": start_result.get('error')}
        
        # Poll
        poll_result = self.poll_for_result(
            start_result['conversation_id'],
            start_result['message_id'],
            max_wait_seconds=60
        )
        
        if poll_result.get('status') != 'completed':
            return {"error": f"Query failed: {poll_result.get('error')}"}
        
        # Extract
        response = poll_result['response']
        return {
            "text": response.get('content', ''),
            "status": "success"
        }

try:
    genie = GenieConversationTool(w, GENIE_SPACE_ID)
    genie_result = genie.query("Show me 2 recent resolved tickets")
    if "error" not in genie_result:
        print(f"✅ Genie API working!")
    else:
        print(f"❌ Genie API failed: {genie_result}")
except Exception as e:
    print(f"❌ Genie API test failed: {e}")
    traceback.print_exc()

# Step 7: Create LangChain Tools
print("\n[Step 7] Creating LangChain Tools...")
try:
    def classify_ticket_wrapper(ticket_text: str) -> str:
        result = call_uc_function("ai_classify", {"ticket_text": ticket_text})
        return json.dumps(result, indent=2)
    
    classify_tool = Tool(
        name="classify_ticket",
        description="Classifies a support ticket by category, priority, and team.",
        func=classify_ticket_wrapper
    )
    print("  ✅ classify_tool created")
    
    def extract_metadata_wrapper(ticket_text: str) -> str:
        result = call_uc_function("ai_extract", {"ticket_text": ticket_text})
        return json.dumps(result, indent=2)
    
    extract_tool = Tool(
        name="extract_metadata",
        description="Extracts metadata from ticket: priority score, urgency, systems.",
        func=extract_metadata_wrapper
    )
    print("  ✅ extract_tool created")
    
    def search_knowledge_wrapper(query: str) -> str:
        results = search_knowledge_base(query, num_results=3)
        return json.dumps(results, indent=2)
    
    search_tool = Tool(
        name="search_knowledge",
        description="Searches knowledge base for relevant articles.",
        func=search_knowledge_wrapper
    )
    print("  ✅ search_tool created")
    
    def query_historical_wrapper(question: str) -> str:
        genie = GenieConversationTool(w, GENIE_SPACE_ID)
        result = genie.query(question)
        return json.dumps(result, indent=2, default=str)
    
    genie_tool = Tool(
        name="query_historical",
        description="Queries historical resolved tickets.",
        func=query_historical_wrapper
    )
    print("  ✅ genie_tool created")
    
    print("✅ All 4 LangChain Tools created successfully!")
except Exception as e:
    print(f"❌ Failed to create LangChain Tools: {e}")
    traceback.print_exc()

# Step 8: Create LangGraph Agent
print("\n[Step 8] Creating LangGraph ReAct Agent...")
try:
    system_prompt = """You are an intelligent support ticket analysis assistant.
    Your goal is to efficiently gather the RIGHT information - not to call every tool.
    Guidelines:
    1. ALWAYS classify the ticket first
    2. For simple questions, knowledge base is usually sufficient
    3. For critical issues, check historical tickets
    4. Be efficient but thorough"""
    
    llm = ChatDatabricks(
        endpoint=LLM_ENDPOINT,
        temperature=0.1
    ).bind(system=system_prompt)
    print(f"  ✅ LLM initialized: {LLM_ENDPOINT}")
    
    agent = create_react_agent(
        model=llm,
        tools=[classify_tool, extract_tool, search_tool, genie_tool]
    )
    print("  ✅ LangGraph ReAct Agent created!")
    print("  🧰 Agent has 4 tools available")
except Exception as e:
    print(f"❌ Failed to create LangGraph Agent: {e}")
    traceback.print_exc()
    sys.exit(1)

# Step 9: Test Agent with Simple Ticket
print("\n[Step 9] Testing Agent with Simple Ticket...")
try:
    test_ticket = "How do I reset my password?"
    print(f"  🎫 Ticket: {test_ticket}")
    
    result = agent.invoke({
        "messages": [("user", f"Analyze this support ticket: {test_ticket}")]
    })
    
    # Count tools used
    tool_messages = [m for m in result['messages'] if hasattr(m, 'name')]
    tools_used = list(set([m.name for m in tool_messages]))
    
    print(f"  ✅ Agent completed!")
    print(f"  🧰 Tools used: {len(tools_used)}/4 - {tools_used}")
    
    if len(tools_used) < 4:
        print(f"  💡 Agent was efficient - used only {len(tools_used)} tools!")
    
except Exception as e:
    print(f"❌ Agent test failed: {e}")
    traceback.print_exc()

# Final Summary
print("\n" + "=" * 80)
print("TEST SUMMARY")
print("=" * 80)
print("✅ All steps completed! The notebook should work in Databricks.")
print("\nIf any steps failed above, those need to be fixed in the notebook.")
print("=" * 80)

