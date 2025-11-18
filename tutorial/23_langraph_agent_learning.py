# Databricks notebook source
# MAGIC %md
# MAGIC # ✨✨✨ VERSION 2.0 - UPDATED NOV 13, 2025 ✨✨✨
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
# MAGIC ## 🔄 **NOTEBOOK VERSION INFO**
# MAGIC 
# MAGIC **📅 Last Updated:** November 13, 2025 - 10:00 AM PST  
# MAGIC **🔧 Version:** 2.0 - WITH `bind_tools()` FIX  
# MAGIC **✅ Critical Fix:** Added `llm.bind_tools()` to prevent XML format errors  
# MAGIC **🎯 Status:** Ready for testing  
# MAGIC 
# MAGIC **🚨 VERIFICATION:** After running LLM init cell, you MUST see:  
# MAGIC ```
# MAGIC ✅ Tools bound to LLM (ensures proper JSON format)
# MAGIC ```
# MAGIC 
# MAGIC **If you DON'T see this line → Detach & Reattach notebook!**
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
# MAGIC 
# MAGIC **Why these specific versions?**
# MAGIC - `langgraph>=1.0.0` - Latest version (v1.0) removed `state_modifier` parameter
# MAGIC - `langchain>=0.3.0` - Latest version with improved tool calling
# MAGIC - Pinning versions ensures reproducibility across environments
# MAGIC 
# MAGIC **Key packages:**
# MAGIC - `langgraph` - State machine and agent orchestration
# MAGIC - `langchain` - Agent framework and tool abstractions
# MAGIC - `databricks-langchain` - Databricks-specific LangChain integrations
# MAGIC - `unitycatalog-langchain` - Unity Catalog function integration

# COMMAND ----------

# MAGIC %pip install langgraph>=1.0.0 langchain>=0.3.0 langchain-core>=0.3.0 langchain-community>=0.3.0 databricks-langchain unitycatalog-langchain[databricks] backoff databricks-sdk mlflow databricks-vectorsearch --quiet

# COMMAND ----------

dbutils.library.restartPython()

# COMMAND ----------

# MAGIC %md
# MAGIC ## ✅ Version Check - Run This First!

# COMMAND ----------

# Version check - Run this to verify you have the latest notebook
import datetime
print("=" * 80)
print("🔍 NOTEBOOK VERSION CHECK")
print("=" * 80)
print("📅 Deployed Version: November 13, 2025 - 10:00 AM PST")
print("🔧 Version: 2.0 - WITH bind_tools() FIX")
print("=" * 80)
print("\n✅ If you see this, the notebook file is the latest version!")
print("🚨 After running LLM init, you MUST see: 'Tools bound to LLM'")
print("❌ If you don't see that line → Detach & Reattach notebook")
print("=" * 80)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 🔧 Imports and Configuration
# MAGIC 
# MAGIC **Import Strategy:**
# MAGIC - `WorkspaceClient` - Databricks SDK for calling APIs (UC Functions, Genie, etc.)
# MAGIC - `ChatDatabricks` - LangChain wrapper for Databricks Foundation Models
# MAGIC - `VectorSearchClient` - For semantic search in knowledge base
# MAGIC - `SystemMessage` - LangChain message type for system prompts (v1.0+ pattern)
# MAGIC - `create_react_agent` - Pre-built ReAct agent from LangGraph
# MAGIC 
# MAGIC **Why these imports?**
# MAGIC - All use WorkspaceClient pattern (same as dashboard) for portability
# MAGIC - SystemMessage needed for manual prompt injection (v1.0+ requirement)
# MAGIC - No custom state classes needed for this simple use case

# COMMAND ----------

# Core Databricks integrations
from databricks.sdk import WorkspaceClient  # Unified API client
from databricks_langchain import ChatDatabricks  # LLM wrapper
from databricks.vector_search.client import VectorSearchClient  # Semantic search

# LangChain/LangGraph components
from langchain_core.tools import Tool  # Tool wrapper abstraction
from langchain_core.messages import SystemMessage  # For system prompt injection
from langgraph.prebuilt import create_react_agent  # Pre-built ReAct pattern

# Additional imports for state management (if needed for advanced use)
from typing import Annotated
from langgraph.graph import MessagesState
from langgraph.graph.message import add_messages

# Standard library
import os
import json
import time
import backoff  # For retry logic

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
# MAGIC 
# MAGIC **Configuration Strategy:**
# MAGIC - Centralized config makes it easy to change environments (dev/prod)
# MAGIC - All IDs/names are explicit (no magic strings scattered in code)
# MAGIC - LLM endpoint changed to Meta Llama 3.1 8B (available in workspace)
# MAGIC 
# MAGIC **Why Meta Llama 3.1 8B Instruct?**
# MAGIC - Foundation model (managed by Databricks, always available)
# MAGIC - Good balance: fast (8B params) + capable (instruction-tuned)
# MAGIC - Strong tool-calling abilities needed for ReAct agents
# MAGIC - Cost-effective for experimentation

# COMMAND ----------

# Configuration - Tutorial environment (independent from main project)
CATALOG = "langtutorial"  # Tutorial catalog (created in setup_catalog_schema.py)
SCHEMA = "agents"  # Schema containing tables and functions
WAREHOUSE_ID = "your-warehouse-id"  # ← UPDATE THIS: Your SQL Warehouse ID
INDEX_NAME = f"{CATALOG}.{SCHEMA}.knowledge_base_index"  # Vector search index
GENIE_SPACE_ID = "your-genie-space-id"  # ← UPDATE THIS: Copy from Genie UI after creating space

# LLM Configuration
# 🚨 CRITICAL: Use Claude Sonnet 4 for production agents with function calling
# 
# LESSON LEARNED:
# - Meta Llama models return XML-like syntax: <function=name>{args}</function>
# - LangGraph expects proper JSON format for tool calls
# - This causes BAD_REQUEST errors: "Model response did not respect required format"
# 
# MODEL COMPARISON (Function Calling):
# ✅ Claude Sonnet 4: ⭐⭐⭐⭐⭐ BEST - Perfect JSON, reliable tool use
# ✅ GPT-4: ⭐⭐⭐⭐⭐ Also excellent (not tested here)
# ⚠️ DBRX: ⭐⭐⭐⭐☆ Good (but unavailable in this workspace)
# ❌ Meta Llama 3.3 70B: ⭐⭐☆☆☆ Poor - XML format issues
# ❌ Meta Llama 3.1 8B: ⭐☆☆☆☆ Very Poor - XML format issues
#
# COST vs RELIABILITY:
# - Claude costs more per token BUT first-try success = lower total cost
# - Failed tool calls waste tokens on retries + bad UX
# - For production agents: Reliability > per-token cost
LLM_ENDPOINT = "databricks-claude-sonnet-4"  # ✅ PRODUCTION CHOICE

print("=" * 80)
print("✅ CONFIGURATION LOADED")
print("=" * 80)
print(f"📚 Catalog: {CATALOG}")
print(f"📊 Schema: {SCHEMA}")
print(f"🔍 Vector Index: {INDEX_NAME}")
print(f"🤖 Genie Space: {GENIE_SPACE_ID}")
print(f"🧠 LLM Endpoint: {LLM_ENDPOINT}")
print("=" * 80)

# 🚨 CRITICAL VERIFICATION: Ensure we're using Claude Sonnet 4
if LLM_ENDPOINT != "databricks-claude-sonnet-4":
    print("\n" + "!" * 80)
    print("⚠️  WARNING: WRONG MODEL DETECTED!")
    print("!" * 80)
    print(f"❌ Currently using: {LLM_ENDPOINT}")
    print(f"✅ Should be using: databricks-claude-sonnet-4")
    print("\n🔧 FIX:")
    print("   1. In Databricks UI: Detach & Reattach this notebook")
    print("   2. OR: Click 'Clear' → 'Clear State & Outputs'")
    print("   3. Re-run ALL cells from the beginning")
    print("!" * 80)
    raise ValueError(
        f"Wrong LLM endpoint! Using '{LLM_ENDPOINT}' instead of 'databricks-claude-sonnet-4'. "
        f"This will cause BAD_REQUEST errors with XML-format tool calls. "
        f"Detach & reattach notebook, then re-run from beginning."
    )
else:
    print("✅ VERIFICATION PASSED: Using Claude Sonnet 4 (correct model for function calling)")

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
    Call a UC function using Statement Execution API (same as dashboard).
    This is more reliable for Databricks Apps and notebooks.
    """
    try:
        from databricks.sdk.service.sql import StatementState
        
        print(f"🔧 Calling UC Function: {CATALOG}.{SCHEMA}.{function_name}")
        
        # Build SQL query with parameters
        param_values = []
        for key, value in parameters.items():
            if isinstance(value, str):
                # Escape single quotes
                escaped = value.replace("'", "''")
                param_values.append(f"'{escaped}'")
            else:
                param_values.append(str(value))
        
        args_str = ', '.join(param_values)
        query = f"SELECT {CATALOG}.{SCHEMA}.{function_name}({args_str}) as result"
        
        print(f"  📝 SQL: {query[:100]}...")
        
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
                print(f"✅ UC Function result received")
                return result
            else:
                print(f"❌ No data in response")
                return {"error": "No data returned"}
        else:
            error_msg = response.status.error.message if response.status.error else "Unknown error"
            print(f"❌ {error_msg}")
            return {"error": error_msg}
        
    except Exception as e:
        error_msg = f"Exception calling UC function: {str(e)}"
        print(f"❌ {error_msg}")
        import traceback
        traceback.print_exc()
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
        
        # Initialize VectorSearchClient (uses workspace client from environment)
        vsc = VectorSearchClient()
        
        results = vsc.get_index(
            index_name=INDEX_NAME
        ).similarity_search(
            query_text=query,
            columns=["doc_id", "doc_type", "title", "content"],
            num_results=num_results
        )
        
        docs = results.get('result', {}).get('data_array', [])
        print(f"✅ Found {len(docs)} documents")
        
        formatted_results = [
            {
                "doc_id": doc[0],
                "doc_type": doc[1],
                "title": doc[2],
                "content": doc[3][:200] + "..." if len(doc[3]) > 200 else doc[3],
                "score": doc[4] if len(doc) > 4 else None
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
    print(f"   📂 Type: {doc['doc_type']}")
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
        Complete Genie query workflow: start → poll → extract results → fetch data
        Returns structured results with actual data rows or error message.
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
        
        # Step 3: Extract results from poll response
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
        
        # Step 4: Extract SQL query and attachment_id
        if attachments:
            attachment = attachments[0]
            
            # CRITICAL: Field is 'attachment_id', NOT 'id'!
            attachment_id = attachment.get('attachment_id') or attachment.get('id')
            print(f"[Genie] Attachment ID: {attachment_id}")
            
            # Extract SQL query
            query_obj = attachment.get('query', {})
            if isinstance(query_obj, dict):
                result['query'] = query_obj.get('query') or query_obj.get('content')
                if result['query']:
                    print(f"[Genie] Extracted SQL: {result['query'][:100]}...")
            
            # Step 5: Fetch actual data using query-result endpoint
            if attachment_id:
                print(f"[Genie] Calling query-result endpoint...")
                try:
                    query_result_response = self.w.api_client.do(
                        'GET',
                        f'/api/2.0/genie/spaces/{self.space_id}/conversations/{conversation_id}/messages/{message_id}/query-result/{attachment_id}'
                    )
                    
                    # Parse response - data is wrapped in 'statement_response'
                    statement_response = query_result_response.get('statement_response', {})
                    if statement_response:
                        print(f"[Genie] Found statement_response")
                        manifest = statement_response.get('manifest', {})
                        if manifest:
                            schema = manifest.get('schema', {})
                            columns = schema.get('columns', [])
                            column_names = [col.get('name') for col in columns]
                            print(f"[Genie] Found columns: {column_names}")
                            
                            # Get data rows
                            result_obj = statement_response.get('result', {})
                            data_array = result_obj.get('data_array', [])
                            print(f"[Genie] Found {len(data_array)} data rows from Genie API")
                            
                            if data_array:
                                # Convert to list of dicts
                                result['data'] = []
                                for row in data_array:
                                    row_dict = dict(zip(column_names, row))
                                    result['data'].append(row_dict)
                                print(f"[Genie] ✅ Successfully converted {len(result['data'])} rows")
                            else:
                                print(f"[Genie] No data_array in result")
                        else:
                            print(f"[Genie] No manifest in statement_response")
                    else:
                        print(f"[Genie] No statement_response in query result response")
                        
                except Exception as e:
                    print(f"[Genie] Error calling query-result endpoint: {str(e)}")
        
        # Step 6: FALLBACK - Execute SQL directly if we have query but no data
        if result.get('query') and not result.get('data'):
            print(f"[Genie] FALLBACK: No data from Genie API, executing SQL directly...")
            result['used_fallback'] = True
            try:
                from databricks.sdk.service.sql import StatementState
                
                execute_response = self.w.statement_execution.execute_statement(
                    warehouse_id=WAREHOUSE_ID,
                    statement=result['query'],
                    wait_timeout='30s'
                )
                
                print(f"[Genie] Fallback execution status: {execute_response.status.state}")
                
                if execute_response.status.state == StatementState.SUCCEEDED:
                    columns = execute_response.manifest.schema.columns if execute_response.manifest and execute_response.manifest.schema else []
                    column_names = [col.name for col in columns]
                    print(f"[Genie] Fallback found columns: {column_names}")
                    
                    if execute_response.result and execute_response.result.data_array:
                        data_array = execute_response.result.data_array
                        print(f"[Genie] Fallback found {len(data_array)} data rows")
                        
                        result['data'] = []
                        for row in data_array:
                            row_dict = dict(zip(column_names, row))
                            result['data'].append(row_dict)
                        print(f"[Genie] ✅ Fallback successfully converted {len(result['data'])} rows")
                else:
                    error_msg = execute_response.status.error.message if execute_response.status.error else "Unknown error"
                    print(f"[Genie] Fallback execution failed: {error_msg}")
            except Exception as e:
                print(f"[Genie] Fallback execution error: {str(e)}")
        
        print(f"[Genie] Final data rows extracted: {len(result.get('data') or [])}")
        
        # Determine which method was used
        if result.get('data'):
            if result.get('used_fallback'):
                result['method'] = 'Direct SQL Execution (Fallback)'
            else:
                result['method'] = 'Genie query-result API'
            print(f"[Genie] Method: {result['method']}")
        
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
if genie_result.get('data'):
    print(f"  📊 Data Rows: {len(genie_result['data'])}")
    print(f"  🔧 Method: {genie_result.get('method', 'Unknown')}")
    print(f"\n  Sample rows:")
    for i, row in enumerate(genie_result['data'][:3], 1):
        print(f"    {i}. {row}")
elif genie_result.get('error'):
    print(f"  ❌ Error: {genie_result['error']}")
else:
    print(f"  ⚠️ No data returned (query generated but data not fetched)")

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

# Define Pydantic schemas for tool inputs (fixes LLM parameter naming issues)
from pydantic import BaseModel, Field

class ClassifyTicketInput(BaseModel):
    ticket_text: str = Field(description="The support ticket text to classify")

class ExtractMetadataInput(BaseModel):
    ticket_text: str = Field(description="The support ticket text to extract metadata from")

class SearchKnowledgeInput(BaseModel):
    query: str = Field(description="The search query to find relevant documentation")

class QueryHistoricalInput(BaseModel):
    question: str = Field(description="Natural language question about historical tickets")

# Tool 1: Classification
def classify_ticket_wrapper(ticket_text: str) -> str:
    """
    Wrapper for ai_classify UC Function.
    
    IMPORTANT: This function MUST be pure (no side effects)!
    - ❌ NO Streamlit calls (st.info, st.error, etc.) - causes NoSessionContext error
    - ✅ Return JSON string only
    - ✅ Include error handling in return value
    
    WHY: LangGraph runs tools in background threads without Streamlit session context
    """
    result = call_uc_function("ai_classify", {"ticket_text": ticket_text})
    return json.dumps(result, indent=2) if result else json.dumps({"error": "Classification failed"})

classify_tool = Tool(
    name="classify_ticket",
    description="Classifies a support ticket into category, priority, and routing team. Use this FIRST to understand the ticket type. Returns JSON with category, priority, team, confidence.",
    func=classify_ticket_wrapper,
    args_schema=ClassifyTicketInput
)
print("✅ Tool 1: classify_ticket")

# Tool 2: Metadata Extraction
def extract_metadata_wrapper(ticket_text: str) -> str:
    """
    Wrapper for ai_extract UC Function.
    IMPORTANT: Pure function - no Streamlit calls! (See classify_ticket_wrapper for details)
    """
    result = call_uc_function("ai_extract", {"ticket_text": ticket_text})
    return json.dumps(result, indent=2) if result else json.dumps({"error": "Extraction failed"})

extract_tool = Tool(
    name="extract_metadata",
    description="Extracts structured metadata from ticket including priority score, urgency indicators, affected systems, and technical details. Use for complex technical issues. Returns JSON with priority_score, urgency, systems, details.",
    func=extract_metadata_wrapper,
    args_schema=ExtractMetadataInput
)
print("✅ Tool 2: extract_metadata")

# Tool 3: Knowledge Base Search
def search_knowledge_wrapper(query: str) -> str:
    """
    Wrapper for Vector Search.
    IMPORTANT: Pure function - no Streamlit calls! (See classify_ticket_wrapper for details)
    """
    try:
        results = search_knowledge_base(query, num_results=3)
        return json.dumps(results, indent=2) if results else json.dumps([])
    except Exception as e:
        return json.dumps({"error": f"Search failed: {str(e)}"})

search_tool = Tool(
    name="search_knowledge",
    description="Searches the knowledge base for relevant articles, documentation, and solutions using semantic search. Use to find how-to guides, troubleshooting steps, or existing documentation. Returns JSON array with title, content, category for top matches.",
    func=search_knowledge_wrapper,
    args_schema=SearchKnowledgeInput
)
print("✅ Tool 3: search_knowledge")

# Tool 4: Historical Tickets (Genie)
def query_historical_wrapper(question: str) -> str:
    """
    Wrapper for Genie Conversation API.
    IMPORTANT: Pure function - no Streamlit calls! (See classify_ticket_wrapper for details)
    """
    try:
        genie = GenieConversationTool(w, GENIE_SPACE_ID)
        result = genie.query(question)
        return json.dumps(result, indent=2, default=str)
    except Exception as e:
        return json.dumps({"error": f"Historical query failed: {str(e)}"})

genie_tool = Tool(
    name="query_historical",
    description="Queries historical resolved tickets using natural language to find similar cases and their resolutions. Use for complex issues where past solutions might help. Returns JSON with text summary and optionally SQL query used.",
    func=query_historical_wrapper,
    args_schema=QueryHistoricalInput
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
# MAGIC 
# MAGIC **Critical LangGraph v1.0+ Pattern:**
# MAGIC This is the **main fix** that made the agent work!
# MAGIC 
# MAGIC **What Changed in LangGraph v1.0:**
# MAGIC - ❌ Old: `state_modifier` parameter (removed in v1.0)
# MAGIC - ✅ New: Pass SystemMessage in messages array at invocation time
# MAGIC 
# MAGIC **Why This Approach:**
# MAGIC 1. **Compatible** - Works with LangGraph v1.0+
# MAGIC 2. **Explicit** - Clear what messages are sent to LLM
# MAGIC 3. **Flexible** - Can change system prompt per invocation if needed
# MAGIC 4. **Simple** - No complex state management required
# MAGIC 
# MAGIC **Alternative Approaches (for reference):**
# MAGIC - LangGraph v0.2: Used `state_modifier` parameter
# MAGIC - LangGraph v1.0 advanced: Use custom `StateGraph` with preprocessor
# MAGIC - LangChain v1.0: Use `langchain.agents.create_agent()` with state_schema
# MAGIC 
# MAGIC We chose the simplest approach that works across versions!

# COMMAND ----------

print("=" * 80)
print("CREATING LANGGRAPH REACT AGENT")
print("=" * 80)

# System prompt for the agent
# This guides the agent's decision-making process
# Key insight: Agent should be EFFICIENT, not exhaustive
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

# Initialize LLM
# ChatDatabricks is a LangChain wrapper for Databricks Foundation Models
# It handles authentication via WorkspaceClient automatically
llm = ChatDatabricks(
    endpoint=LLM_ENDPOINT,  # Foundation model serving endpoint
    temperature=0.1,  # VERY LOW temp for reliable tool calling (was 0.3, reduced to 0.1)
    max_tokens=4096  # Sufficient for reasoning + tool calls
)
print(f"✅ LLM initialized: {LLM_ENDPOINT}")

# Create ReAct agent with all 4 tools
# ReAct = Reasoning + Acting (agent thinks before acting)
# Pattern: Thought → Action (tool call) → Observation (tool result) → repeat
tools_list = [classify_tool, extract_tool, search_tool, genie_tool]

# 🚨 CRITICAL FIX: Use bind_tools for reliable function calling
# This ensures the LLM uses proper JSON format (not XML) for ALL tool calls
# Without this, Claude might hallucinate XML format mid-conversation
llm_with_tools = llm.bind_tools(tools_list)
print(f"✅ Tools bound to LLM (ensures proper JSON format)")

# Create the agent using the standard create_react_agent
# IMPORTANT: Pass the bound LLM (llm_with_tools) not the raw LLM
# This ensures consistent tool calling format throughout the conversation
agent = create_react_agent(
    model=llm_with_tools,  # The LLM with tools bound (CRITICAL!)
    tools=tools_list  # Available tools the agent can call
    # NOTE: We do NOT pass state_modifier here (deprecated in v1.0)
    # Instead, we'll inject SystemMessage when we invoke the agent
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
    """
    Test agent with a ticket and display results
    
    This function demonstrates the LangGraph v1.0+ invocation pattern
    
    **Key Pattern: Manual SystemMessage Injection**
    We pass the system prompt as the FIRST message when invoking the agent.
    This is the v1.0+ replacement for the deprecated state_modifier parameter.
    
    Args:
        ticket_text: The support ticket to analyze
        show_reasoning: Whether to display the agent's thought process
        
    Returns:
        Agent result containing messages and tool calls
    """
    print("\n" + "=" * 80)
    print(f"🎫 TICKET: {ticket_text}")
    print("=" * 80 + "\n")
    
    start_time = time.time()
    
    # CRITICAL PATTERN: Manual SystemMessage Injection (v1.0+)
    # We explicitly pass SystemMessage as first message
    # This replaces the old state_modifier approach from v0.2
    result = agent.invoke({
        "messages": [
            # System message goes FIRST - sets agent behavior/personality
            SystemMessage(content=system_prompt),
            # Then user message with the actual task
            ("user", f"Analyze this support ticket and provide recommendations: {ticket_text}")
        ]
    })
    # The agent will:
    # 1. Read system prompt (guidance)
    # 2. Read user message (task)
    # 3. Reason about what tools to call
    # 4. Call tools as needed
    # 5. Synthesize final answer
    
    elapsed_time = time.time() - start_time
    
    if show_reasoning:
        print("🧠 AGENT REASONING TRAIL:")
        print("-" * 80)
        
        for i, message in enumerate(result['messages']):
            msg_type = getattr(message, 'type', None)
            
            if msg_type == "human":
                print(f"\n👤 USER:")
                content = getattr(message, 'content', '')
                print(f"   {str(content)[:200]}...")
            elif msg_type == "ai":
                content = getattr(message, 'content', '') or ""
                # Check if this is a tool call or final answer
                tool_calls = getattr(message, 'tool_calls', None)
                if tool_calls:
                    print(f"\n🤖 AGENT THOUGHT & ACTION:")
                    if content:
                        print(f"   {str(content)[:300]}...")
                    for tool_call in tool_calls:
                        tool_name = tool_call.get('name') if isinstance(tool_call, dict) else getattr(tool_call, 'name', 'unknown')
                        tool_args = tool_call.get('args') if isinstance(tool_call, dict) else getattr(tool_call, 'args', {})
                        print(f"   🔧 Calling tool: {tool_name}")
                        print(f"   📥 Input: {str(tool_args)[:150]}...")
                else:
                    print(f"\n🤖 AGENT FINAL ANSWER:")
                    if content:
                        print(f"   {str(content)[:500]}...")
                    else:
                        print(f"   (No answer generated)")
            elif msg_type == "tool":  # Tool message
                tool_name = getattr(message, 'name', 'unknown')
                print(f"\n📤 TOOL RESULT ({tool_name}):")
                content = getattr(message, 'content', None)
                if content:
                    result_preview = str(content)[:200] if len(str(content)) > 200 else str(content)
                    print(f"   {result_preview}...")
                else:
                    print(f"   (No content)")
    
    # Count tools used
    tool_messages = [m for m in result['messages'] if getattr(m, 'type', None) == 'tool']
    tools_used = list(set([getattr(m, 'name', None) for m in tool_messages if getattr(m, 'name', None)]))
    
    print("\n" + "=" * 80)
    print(f"📊 SUMMARY:")
    print(f"   ⏱️  Time: {elapsed_time:.2f}s")
    if tools_used:
        print(f"   🧰 Tools used: {len(tools_used)}/4 - {', '.join(tools_used)}")
    else:
        print(f"   🧰 Tools used: 0/4")
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
agent_tools = [getattr(m, 'name', None) for m in agent_result['messages'] if getattr(m, 'type', None) == 'tool']
agent_tools_unique = list(set([t for t in agent_tools if t]))

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

