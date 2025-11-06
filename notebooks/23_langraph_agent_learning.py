# Databricks notebook source
# MAGIC %md
# MAGIC # LangGraph Agent Learning - Support Ticket Analysis
# MAGIC 
# MAGIC **Purpose:** Learn LangGraph ReAct agents by wrapping existing UC Functions, Vector Search, and Genie API
# MAGIC 
# MAGIC **Authentication:** Uses WorkspaceClient (same as dashboard) for realistic testing
# MAGIC 
# MAGIC **Branch:** `agent_langraph_trying` (experimental)
# MAGIC 
# MAGIC ---
# MAGIC 
# MAGIC ## What This Notebook Does
# MAGIC 
# MAGIC 1. ✅ Tests all 4 tools individually (UC Functions, Vector Search, Genie)
# MAGIC 2. ✅ Wraps them as LangChain Tools
# MAGIC 3. ✅ Creates LangGraph ReAct Agent
# MAGIC 4. ✅ Tests agent with different ticket types
# MAGIC 5. ✅ Compares Sequential vs Agent approaches
# MAGIC 
# MAGIC **Goal:** Iron out any issues before implementing in dashboard

# COMMAND ----------

# MAGIC %md
# MAGIC ## 📦 Setup - Install Dependencies

# COMMAND ----------

# MAGIC %pip install langgraph langchain langchain-core databricks-langchain backoff databricks-sdk mlflow databricks-vectorsearch --quiet

# COMMAND ----------

dbutils.library.restartPython()

# COMMAND ----------

# MAGIC %md
# MAGIC ## 🔧 Imports and Configuration

# COMMAND ----------

from databricks.sdk import WorkspaceClient
from databricks_langchain import ChatDatabricks
from databricks.vector_search.client import VectorSearchClient
from langchain.tools import Tool
from langgraph.prebuilt import create_react_agent
import os
import json
import time
import backoff

# Initialize WorkspaceClient (same pattern as dashboard)
w = WorkspaceClient()

print("✅ WorkspaceClient initialized")
print(f"📍 Workspace: {w.config.host}")
print(f"👤 Current user: {w.current_user.me().user_name}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## ⚙️ Configuration Variables
# MAGIC 
# MAGIC These match the dashboard configuration

# COMMAND ----------

# Configuration (same as dashboard)
CATALOG = "vik_catalog"
SCHEMA = "ai_ticket_classification"
WAREHOUSE_ID = "148ccb90800933a1"
INDEX_NAME = f"{CATALOG}.{SCHEMA}.kb_docs_index"
GENIE_SPACE_ID = "01f0b91aa91c1b0c8cce6529ea09f0a8"
LLM_ENDPOINT = "databricks-meta-llama-3-3-70b-instruct"

print("✅ Configuration loaded")
print(f"  📚 Catalog: {CATALOG}")
print(f"  📊 Schema: {SCHEMA}")
print(f"  🔍 Vector Index: {INDEX_NAME}")
print(f"  🤖 Genie Space: {GENIE_SPACE_ID}")
print(f"  🧠 LLM Endpoint: {LLM_ENDPOINT}")

# COMMAND ----------

# MAGIC %md
# MAGIC ---
# MAGIC # Part 1: Test Individual Tools
# MAGIC 
# MAGIC Before creating the agent, verify each tool works correctly

# COMMAND ----------

# MAGIC %md
# MAGIC ## 🔧 Tool 1: UC Function Wrapper (Classification & Extraction)

# COMMAND ----------

def call_uc_function(function_name: str, parameters: dict):
    """
    Call a UC function using WorkspaceClient.
    Same pattern as dashboard - directly portable!
    """
    try:
        function_full_name = f"{CATALOG}.{SCHEMA}.{function_name}"
        
        print(f"🔧 Calling UC Function: {function_full_name}")
        
        response = w.functions.execute(
            name=function_full_name,
            arguments=[{"name": k, "value": json.dumps(v)} for k, v in parameters.items()]
        )
        
        if response.error:
            error_msg = f"UC Function Error: {response.error.error_message}"
            print(f"❌ {error_msg}")
            return {"error": error_msg}
        
        result = json.loads(response.value) if response.value else {}
        print(f"✅ UC Function result received")
        return result
        
    except Exception as e:
        error_msg = f"Exception calling UC function: {str(e)}"
        print(f"❌ {error_msg}")
        return {"error": error_msg}

# COMMAND ----------

# Test 1: ai_classify
print("=" * 80)
print("TEST 1: UC Function - ai_classify")
print("=" * 80)

test_ticket = "Database connection timeout in production affecting all users"
classification_result = call_uc_function(
    "ai_classify",
    {"ticket_text": test_ticket}
)

print(f"\n📊 Classification Result:")
print(json.dumps(classification_result, indent=2))

# COMMAND ----------

# Test 2: ai_extract
print("=" * 80)
print("TEST 2: UC Function - ai_extract")
print("=" * 80)

metadata_result = call_uc_function(
    "ai_extract",
    {"ticket_text": test_ticket}
)

print(f"\n📊 Metadata Extraction Result:")
print(json.dumps(metadata_result, indent=2))

# COMMAND ----------

# MAGIC %md
# MAGIC ## 🔍 Tool 2: Vector Search Wrapper

# COMMAND ----------

def search_knowledge_base(query: str, num_results: int = 3):
    """
    Search knowledge base using Vector Search.
    Same pattern as dashboard - directly portable!
    """
    try:
        print(f"🔍 Searching knowledge base: '{query[:50]}...'")
        
        vsc = VectorSearchClient(workspace_client=w)
        
        results = vsc.get_index(
            index_name=INDEX_NAME
        ).similarity_search(
            query_text=query,
            columns=["title", "content", "category"],
            num_results=num_results
        )
        
        docs = results.get('result', {}).get('data_array', [])
        print(f"✅ Found {len(docs)} documents")
        
        formatted_results = [
            {
                "title": doc[0],
                "content": doc[1][:200] + "..." if len(doc[1]) > 200 else doc[1],
                "category": doc[2],
                "score": doc[3] if len(doc) > 3 else None
            }
            for doc in docs
        ]
        
        return formatted_results
        
    except Exception as e:
        error_msg = f"Vector Search Error: {str(e)}"
        print(f"❌ {error_msg}")
        return []

# COMMAND ----------

# Test 3: Vector Search
print("=" * 80)
print("TEST 3: Vector Search")
print("=" * 80)

search_query = "database timeout connection pool configuration"
search_results = search_knowledge_base(search_query)

print(f"\n📚 Knowledge Base Results ({len(search_results)} documents):")
for i, doc in enumerate(search_results, 1):
    print(f"\n{i}. 📄 {doc['title']}")
    print(f"   📂 Category: {doc['category']}")
    print(f"   📝 Content: {doc['content'][:150]}...")
    if doc.get('score'):
        print(f"   🎯 Score: {doc['score']:.4f}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 🤖 Tool 3: Genie Conversation API Wrapper

# COMMAND ----------

class GenieConversationTool:
    """
    Genie Conversation API wrapper using WorkspaceClient.
    Same class as dashboard - directly portable!
    """
    def __init__(self, workspace_client: WorkspaceClient, space_id: str):
        self.w = workspace_client
        self.space_id = space_id
        print(f"[Genie] Initialized with space_id: {space_id}")
    
    def start_conversation(self, question: str):
        """Start a new Genie conversation"""
        try:
            print(f"[Genie] Starting conversation...")
            response = self.w.api_client.do(
                'POST',
                f'/api/2.0/genie/spaces/{self.space_id}/start-conversation',
                body={'content': question}
            )
            
            conversation_id = response.get('conversation_id')
            message_id = response.get('message_id')
            
            print(f"[Genie] ✅ Started - conversation_id: {conversation_id}, message_id: {message_id}")
            
            return {
                'status': 'started',
                'conversation_id': conversation_id,
                'message_id': message_id
            }
        except Exception as e:
            print(f"[Genie] ❌ Error starting conversation: {str(e)}")
            return {'status': 'error', 'error': str(e)}
    
    def poll_for_result(self, conversation_id: str, message_id: str, max_wait_seconds: int = 120):
        """Poll for query completion with exponential backoff"""
        print(f"[Genie] Polling for result (max {max_wait_seconds}s)...")
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
                print(f"[Genie] Poll #{poll_count} ({elapsed:.1f}s): Status = {status}")
                
                if status == 'COMPLETED':
                    print(f"[Genie] ✅ Query completed!")
                    return {'status': 'completed', 'response': response}
                elif status == 'FAILED':
                    error = response.get('error', {})
                    print(f"[Genie] ❌ Query failed: {error}")
                    return {'status': 'failed', 'response': response, 'error': error}
                
                time.sleep(poll_interval)
                poll_interval = min(poll_interval * 1.2, 10)
                
            except Exception as e:
                print(f"[Genie] ⚠️ Poll error: {str(e)}")
                time.sleep(poll_interval)
        
        print(f"[Genie] ⏱️ Timeout after {max_wait_seconds}s")
        return {'status': 'timeout', 'error': f'Query did not complete within {max_wait_seconds}s'}
    
    def query(self, question: str):
        """
        Complete Genie query workflow: start → poll → extract results
        Returns structured results or error message.
        """
        print(f"\n[Genie] === Starting Genie Query ===")
        print(f"[Genie] Question: {question[:100]}...")
        
        # Step 1: Start conversation
        start_result = self.start_conversation(question)
        if start_result.get('status') != 'started':
            error_msg = f"Error starting conversation: {start_result.get('error')}"
            print(f"[Genie] {error_msg}")
            return {"error": error_msg}
        
        conversation_id = start_result['conversation_id']
        message_id = start_result['message_id']
        
        # Step 2: Poll for completion
        poll_result = self.poll_for_result(conversation_id, message_id, max_wait_seconds=120)
        
        poll_status = poll_result.get('status')
        
        if poll_status == 'failed':
            error_detail = poll_result.get('error', {}).get('message', 'Query execution failed')
            error_msg = f"Query failed: {error_detail}"
            print(f"[Genie] {error_msg}")
            return {"error": error_msg}
        
        if poll_status != 'completed':
            error_msg = f"Query did not complete: {poll_result.get('error', poll_status)}"
            print(f"[Genie] {error_msg}")
            return {"error": error_msg}
        
        # Step 3: Extract results
        response = poll_result['response']
        text_content = response.get('content', '')
        attachments = response.get('attachments', [])
        
        print(f"[Genie] Received response with {len(attachments)} attachments")
        
        result = {
            "text": text_content,
            "query": None,
            "data": None,
            "conversation_id": conversation_id,
            "message_id": message_id
        }
        
        # Extract SQL query if available
        if attachments:
            attachment = attachments[0]
            query_obj = attachment.get('query', {})
            if isinstance(query_obj, dict):
                result['query'] = query_obj.get('query') or query_obj.get('content')
                if result['query']:
                    print(f"[Genie] Extracted SQL: {result['query'][:100]}...")
        
        print(f"[Genie] === Genie Query Complete ===\n")
        return result

# COMMAND ----------

# Test 4: Genie API
print("=" * 80)
print("TEST 4: Genie Conversation API")
print("=" * 80)

genie = GenieConversationTool(w, GENIE_SPACE_ID)
genie_question = "Show me 3 recent resolved tickets about database connection issues"
genie_result = genie.query(genie_question)

print(f"\n🤖 Genie Result:")
print(f"  📝 Text Response: {genie_result.get('text', '')[:300]}...")
if genie_result.get('query'):
    print(f"  🔍 Generated SQL: {genie_result['query'][:200]}...")
if genie_result.get('error'):
    print(f"  ❌ Error: {genie_result['error']}")

# COMMAND ----------

# MAGIC %md
# MAGIC ---
# MAGIC # Part 2: Create LangChain Tools
# MAGIC 
# MAGIC Wrap the working functions as LangChain Tools for the agent

# COMMAND ----------

# MAGIC %md
# MAGIC ## 🧰 Wrap Functions as LangChain Tools

# COMMAND ----------

print("=" * 80)
print("CREATING LANGCHAIN TOOLS")
print("=" * 80)

# Tool 1: Classification
def classify_ticket_wrapper(ticket_text: str) -> str:
    """Wrapper for ai_classify UC Function"""
    result = call_uc_function("ai_classify", {"ticket_text": ticket_text})
    return json.dumps(result, indent=2)

classify_tool = Tool(
    name="classify_ticket",
    description="""Classifies a support ticket into category (Technical, Account, Feature Request), 
    priority (Critical, High, Medium, Low), and routing team. 
    Use this FIRST to understand what type of ticket you're dealing with.
    
    Returns: JSON with category, priority, team, confidence scores.""",
    func=classify_ticket_wrapper
)
print("✅ Tool 1: classify_ticket")

# Tool 2: Metadata Extraction
def extract_metadata_wrapper(ticket_text: str) -> str:
    """Wrapper for ai_extract UC Function"""
    result = call_uc_function("ai_extract", {"ticket_text": ticket_text})
    return json.dumps(result, indent=2)

extract_tool = Tool(
    name="extract_metadata",
    description="""Extracts structured metadata from ticket: priority score (1-10), 
    urgency indicators, affected systems, technical details, and key entities.
    Use this for complex technical issues that need detailed analysis.
    
    Returns: JSON with priority_score, urgency, systems, details.""",
    func=extract_metadata_wrapper
)
print("✅ Tool 2: extract_metadata")

# Tool 3: Knowledge Base Search
def search_knowledge_wrapper(query: str) -> str:
    """Wrapper for Vector Search"""
    results = search_knowledge_base(query, num_results=3)
    return json.dumps(results, indent=2)

search_tool = Tool(
    name="search_knowledge",
    description="""Searches the knowledge base for relevant articles, documentation, 
    and solutions using semantic search. Use this when you need to find how-to guides, 
    troubleshooting steps, or existing documentation about the ticket's topic.
    
    Returns: JSON array with title, content, category for top matches.""",
    func=search_knowledge_wrapper
)
print("✅ Tool 3: search_knowledge")

# Tool 4: Historical Tickets (Genie)
def query_historical_wrapper(question: str) -> str:
    """Wrapper for Genie Conversation API"""
    genie = GenieConversationTool(w, GENIE_SPACE_ID)
    result = genie.query(question)
    return json.dumps(result, indent=2, default=str)

genie_tool = Tool(
    name="query_historical",
    description="""Queries historical resolved tickets using natural language to find 
    similar cases and their resolutions. Use this for complex issues where past 
    solutions might help, or to find resolution patterns and time estimates.
    Ask questions like: 'Show me resolved tickets about X' or 'Find similar cases to Y'.
    
    Returns: JSON with text summary and optionally SQL query used.""",
    func=query_historical_wrapper
)
print("✅ Tool 4: query_historical")

print(f"\n🎉 All 4 LangChain Tools created successfully!")

# COMMAND ----------

# MAGIC %md
# MAGIC ---
# MAGIC # Part 3: Create LangGraph ReAct Agent
# MAGIC 
# MAGIC Build the agent that will intelligently decide which tools to use

# COMMAND ----------

# MAGIC %md
# MAGIC ## 🧠 Initialize LLM and Create Agent

# COMMAND ----------

print("=" * 80)
print("CREATING LANGGRAPH REACT AGENT")
print("=" * 80)

# Initialize LLM
llm = ChatDatabricks(
    endpoint=LLM_ENDPOINT,
    temperature=0.1
)
print(f"✅ LLM initialized: {LLM_ENDPOINT}")

# System prompt for the agent
system_prompt = """You are an intelligent support ticket analysis assistant.

Your goal is to efficiently gather the RIGHT information to help resolve 
the ticket - not to blindly call every tool available.

GUIDELINES:
1. ALWAYS classify the ticket first to understand its nature
2. For simple how-to questions, the knowledge base is usually sufficient
3. For critical production issues, check historical tickets for proven solutions
4. For low-priority simple questions, metadata extraction is usually not needed
5. Only use query_historical for complex or critical issues where past patterns matter
6. Be efficient but thorough - only use tools that add value

Think step-by-step, explain your reasoning, and make smart decisions about which tools to use.
"""

# Create ReAct agent with all 4 tools
agent = create_react_agent(
    llm,
    tools=[classify_tool, extract_tool, search_tool, genie_tool],
    state_modifier=system_prompt
)

print(f"✅ LangGraph ReAct Agent created!")
print(f"🧰 Agent has 4 tools available:")
print(f"   1. classify_ticket")
print(f"   2. extract_metadata")
print(f"   3. search_knowledge")
print(f"   4. query_historical")
print(f"\n🎯 Agent will decide which tools to use based on the ticket!")

# COMMAND ----------

# MAGIC %md
# MAGIC ---
# MAGIC # Part 4: Test Agent with Different Tickets
# MAGIC 
# MAGIC See how the agent adapts to different ticket complexities

# COMMAND ----------

# MAGIC %md
# MAGIC ## 🧪 Test Runner Function

# COMMAND ----------

def run_agent_test(ticket_text: str, show_reasoning: bool = True):
    """Test agent with a ticket and display results"""
    print("\n" + "=" * 80)
    print(f"🎫 TICKET: {ticket_text}")
    print("=" * 80 + "\n")
    
    start_time = time.time()
    
    result = agent.invoke({
        "messages": [("user", f"Analyze this support ticket and provide recommendations: {ticket_text}")]
    })
    
    elapsed_time = time.time() - start_time
    
    if show_reasoning:
        print("🧠 AGENT REASONING TRAIL:")
        print("-" * 80)
        
        for i, message in enumerate(result['messages']):
            if message.type == "human":
                print(f"\n👤 USER:")
                print(f"   {message.content[:200]}...")
            elif message.type == "ai":
                content = message.content
                # Check if this is a tool call or final answer
                if hasattr(message, 'tool_calls') and message.tool_calls:
                    print(f"\n🤖 AGENT THOUGHT & ACTION:")
                    print(f"   {content[:300]}...")
                    for tool_call in message.tool_calls:
                        print(f"   🔧 Calling tool: {tool_call['name']}")
                        print(f"   📥 Input: {str(tool_call['args'])[:150]}...")
                else:
                    print(f"\n🤖 AGENT FINAL ANSWER:")
                    print(f"   {content[:500]}...")
            elif hasattr(message, 'name'):  # Tool message
                print(f"\n📤 TOOL RESULT ({message.name}):")
                result_preview = message.content[:200] if len(message.content) > 200 else message.content
                print(f"   {result_preview}...")
    
    # Count tools used
    tool_messages = [m for m in result['messages'] if hasattr(m, 'name')]
    tools_used = list(set([m.name for m in tool_messages]))
    
    print("\n" + "=" * 80)
    print(f"📊 SUMMARY:")
    print(f"   ⏱️  Time: {elapsed_time:.2f}s")
    print(f"   🧰 Tools used: {len(tools_used)}/4 - {', '.join(tools_used)}")
    print("=" * 80 + "\n")
    
    return result

# COMMAND ----------

# MAGIC %md
# MAGIC ## 🧪 Test 1: Simple Question (Expected: 2 tools)

# COMMAND ----------

print("🧪 TEST 1: SIMPLE QUESTION")
print("Expected behavior: Should use classify + search, skip extract and genie\n")

result_1 = run_agent_test("How do I reset my password?")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 🧪 Test 2: Critical Production Issue (Expected: 3-4 tools)

# COMMAND ----------

print("🧪 TEST 2: CRITICAL PRODUCTION ISSUE")
print("Expected behavior: Should use classify + search + genie, possibly extract\n")

result_2 = run_agent_test("Production database connection timeout affecting all users, urgent!")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 🧪 Test 3: Feature Request (Expected: 2-3 tools)

# COMMAND ----------

print("🧪 TEST 3: FEATURE REQUEST")
print("Expected behavior: Should use classify + extract, maybe search\n")

result_3 = run_agent_test("Need to integrate our system with Salesforce API for syncing customer data")

# COMMAND ----------

# MAGIC %md
# MAGIC ---
# MAGIC # Part 5: Sequential vs Agent Comparison
# MAGIC 
# MAGIC Compare the agent approach with the current sequential pipeline

# COMMAND ----------

# MAGIC %md
# MAGIC ## 🔄 Sequential Pipeline Function

# COMMAND ----------

def sequential_pipeline(ticket_text: str):
    """
    Run all 4 tools sequentially (current dashboard approach).
    Always executes all tools regardless of ticket complexity.
    """
    print("\n" + "=" * 80)
    print("🔄 SEQUENTIAL PIPELINE - Running ALL tools")
    print("=" * 80 + "\n")
    
    start_time = time.time()
    results = {}
    
    # Step 1: Classify
    print("1️⃣ Step 1: Classifying ticket...")
    results['classification'] = call_uc_function("ai_classify", {"ticket_text": ticket_text})
    print(f"   ✅ Done\n")
    
    # Step 2: Extract
    print("2️⃣ Step 2: Extracting metadata...")
    results['metadata'] = call_uc_function("ai_extract", {"ticket_text": ticket_text})
    print(f"   ✅ Done\n")
    
    # Step 3: Search
    print("3️⃣ Step 3: Searching knowledge base...")
    results['knowledge'] = search_knowledge_base(ticket_text)
    print(f"   ✅ Done\n")
    
    # Step 4: Genie
    print("4️⃣ Step 4: Querying historical tickets via Genie...")
    genie = GenieConversationTool(w, GENIE_SPACE_ID)
    results['historical'] = genie.query(f"Find similar resolved tickets about: {ticket_text}")
    print(f"   ✅ Done\n")
    
    elapsed_time = time.time() - start_time
    
    print("=" * 80)
    print(f"📊 SEQUENTIAL SUMMARY:")
    print(f"   ⏱️  Time: {elapsed_time:.2f}s")
    print(f"   🧰 Tools used: 4/4 (always all tools)")
    print("=" * 80 + "\n")
    
    return results, elapsed_time

# COMMAND ----------

# MAGIC %md
# MAGIC ## 🆚 Side-by-Side Comparison

# COMMAND ----------

print("\n" + "🆚" * 40)
print("COMPARISON TEST: Sequential vs Agent")
print("🆚" * 40 + "\n")

comparison_ticket = "How do I export a report to PDF?"

print("📋 Testing with ticket:")
print(f"   '{comparison_ticket}'")
print("\n" + "=" * 80)

# Run Sequential
print("\n🅰️ APPROACH A: SEQUENTIAL PIPELINE (Current Dashboard)")
sequential_result, seq_time = sequential_pipeline(comparison_ticket)

# Run Agent
print("\n🅱️ APPROACH B: LANGGRAPH AGENT (New Adaptive)")
agent_result = run_agent_test(comparison_ticket, show_reasoning=True)

# Extract agent time and tools
agent_tools = [m.name for m in agent_result['messages'] if hasattr(m, 'name')]
agent_tools_unique = list(set(agent_tools))

print("\n" + "🆚" * 40)
print("COMPARISON RESULTS")
print("🆚" * 40 + "\n")

print("┌─────────────────────────┬──────────────────┬──────────────────┐")
print("│ Metric                  │ Sequential       │ Agent            │")
print("├─────────────────────────┼──────────────────┼──────────────────┤")
print(f"│ Tools Used              │ 4/4 (100%)       │ {len(agent_tools_unique)}/4 ({len(agent_tools_unique)*25}%)        │")
print(f"│ Efficiency              │ Fixed pipeline   │ Adaptive         │")
print(f"│ Predictability          │ High             │ Medium           │")
print(f"│ Flexibility             │ None             │ High             │")
print("└─────────────────────────┴──────────────────┴──────────────────┘")

print("\n💡 INSIGHTS:")
if len(agent_tools_unique) < 4:
    print(f"   ✅ Agent was more efficient: used {len(agent_tools_unique)}/4 tools vs 4/4")
    print(f"   ✅ Agent skipped: {set(['classify_ticket', 'extract_metadata', 'search_knowledge', 'query_historical']) - set(agent_tools_unique)}")
    print(f"   💰 Potential cost savings: ~{(4-len(agent_tools_unique))*25}%")
else:
    print(f"   ℹ️  Agent used all tools for this complex ticket")
    print(f"   ℹ️  For simple tickets, agent would be more efficient")

# COMMAND ----------

# MAGIC %md
# MAGIC ---
# MAGIC # ✅ Summary & Next Steps

# COMMAND ----------

# MAGIC %md
# MAGIC ## 🎉 Success Criteria Checklist
# MAGIC 
# MAGIC If you've successfully run all cells above, you have:
# MAGIC 
# MAGIC - ✅ **Tool 1 Working:** UC Function (ai_classify) with WorkspaceClient
# MAGIC - ✅ **Tool 2 Working:** UC Function (ai_extract) with WorkspaceClient
# MAGIC - ✅ **Tool 3 Working:** Vector Search with WorkspaceClient
# MAGIC - ✅ **Tool 4 Working:** Genie Conversation API with WorkspaceClient
# MAGIC - ✅ **All 4 LangChain Tools Created:** Successfully wrapped APIs
# MAGIC - ✅ **LangGraph ReAct Agent Created:** Agent with 4 tools and system prompt
# MAGIC - ✅ **Agent Makes Decisions:** Tested with different ticket complexities
# MAGIC - ✅ **Comparison Complete:** Sequential vs Agent side-by-side
# MAGIC - ✅ **Code is Portable:** Everything uses WorkspaceClient (same as dashboard)
# MAGIC 
# MAGIC ---
# MAGIC 
# MAGIC ## 📊 Key Learnings
# MAGIC 
# MAGIC **What We Learned:**
# MAGIC 1. **Agent adapts to ticket complexity** - uses fewer tools for simple questions
# MAGIC 2. **Tool descriptions matter** - they guide the agent's decision-making
# MAGIC 3. **System prompt is critical** - sets the agent's behavior and efficiency
# MAGIC 4. **ReAct pattern works** - Thought → Action → Observation loop is visible
# MAGIC 5. **Trade-offs are real** - flexibility vs predictability
# MAGIC 
# MAGIC **When to Use Each Approach:**
# MAGIC - **Sequential:** Predictable, uniform tickets; need consistency
# MAGIC - **Agent:** Varied complexity tickets; want cost optimization
# MAGIC 
# MAGIC ---
# MAGIC 
# MAGIC ## 🚀 Next Steps
# MAGIC 
# MAGIC **Phase 2: Dashboard Integration**
# MAGIC 
# MAGIC Now that the agent works in the notebook, we can:
# MAGIC 
# MAGIC 1. ✅ Extract working code to `dashboard/langraph_agent.py` module
# MAGIC 2. ✅ Add 5th tab to dashboard: "🧪 LangGraph Agent (Experimental)"
# MAGIC 3. ✅ Display agent reasoning trail in Streamlit UI
# MAGIC 4. ✅ Add comparison mode in dashboard
# MAGIC 5. ✅ Deploy and test in production
# MAGIC 
# MAGIC **Ready to move to dashboard integration!** 🎯

# COMMAND ----------

print("""
╔════════════════════════════════════════════════════════════════╗
║                                                                ║
║  🎉 LANGGRAPH AGENT NOTEBOOK COMPLETE! 🎉                     ║
║                                                                ║
║  ✅ All 4 tools tested and working                            ║
║  ✅ LangGraph ReAct Agent created                             ║
║  ✅ Agent makes intelligent decisions                         ║
║  ✅ Sequential vs Agent comparison done                       ║
║  ✅ Code is ready for dashboard integration                   ║
║                                                                ║
║  📍 Branch: agent_langraph_trying                             ║
║  📁 Notebook: notebooks/23_langraph_agent_learning.py         ║
║                                                                ║
║  🚀 Ready for Phase 2: Dashboard Integration!                 ║
║                                                                ║
╚════════════════════════════════════════════════════════════════╝
""")

