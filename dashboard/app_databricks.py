"""
AI-Powered Support Ticket Classification Dashboard
PRODUCTION VERSION - For Databricks Apps deployment

This version uses WorkspaceClient() for authentication (no manual config needed).
For local development, use app_simple.py instead.
"""

import streamlit as st
import json
import time
import os
from databricks.sdk import WorkspaceClient
import backoff

# Page configuration
st.set_page_config(
    page_title="AI Ticket Classification",
    page_icon="🎫",
    layout="wide"
)

# Configuration (read from environment variables with defaults for backward compatibility)
CATALOG = os.getenv("CATALOG_NAME", "classify_tickets_new_dev")
SCHEMA = os.getenv("SCHEMA_NAME", "support_ai")
WAREHOUSE_ID = os.getenv("DATABRICKS_WAREHOUSE_ID", "148ccb90800933a1")
INDEX_NAME = f"{CATALOG}.{SCHEMA}.knowledge_base_index"
GENIE_SPACE_ID = os.getenv("GENIE_SPACE_ID", "01f0b91aa91c1b0c8cce6529ea09f0a8")
LLM_ENDPOINT = os.getenv("LLM_ENDPOINT", "databricks-meta-llama-3-3-70b-instruct")

# Initialize Databricks client (uses Databricks Apps authentication)
@st.cache_resource
def get_workspace_client():
    """Initialize Databricks WorkspaceClient (automatically authenticated in Databricks Apps)"""
    try:
        return WorkspaceClient()
    except Exception as e:
        st.error(f"Failed to initialize Databricks client: {e}")
        return None

w = get_workspace_client()

# ===== GENIE CONVERSATION TOOL =====
class GenieConversationTool:
    """
    Tool for querying Genie using the proper Conversation API pattern.
    Reference: https://learn.microsoft.com/en-us/azure/databricks/genie/conversation-api
    """
    
    def __init__(self, workspace_client: WorkspaceClient, space_id: str):
        self.w = workspace_client
        self.space_id = space_id
        self.conversations = {}
        
    def start_conversation(self, question: str):
        """Start a new Genie conversation"""
        try:
            response = self.w.api_client.do(
                'POST',
                f'/api/2.0/genie/spaces/{self.space_id}/start-conversation',
                body={'content': question}
            )
            
            conversation_id = response.get('conversation', {}).get('id')
            message_id = response.get('message', {}).get('id')
            
            return {
                'status': 'started',
                'conversation_id': conversation_id,
                'message_id': message_id,
                'response': response
            }
        except Exception as e:
            return {'status': 'error', 'error': str(e)}
    
    def poll_for_result(self, conversation_id: str, message_id: str, max_wait_seconds: int = 180):
        """Poll for Genie query completion"""
        start_time = time.time()
        poll_interval = 3  # Start with 3 seconds
        
        while (time.time() - start_time) < max_wait_seconds:
            try:
                response = self.w.api_client.do(
                    'GET',
                    f'/api/2.0/genie/spaces/{self.space_id}/conversations/{conversation_id}/messages/{message_id}'
                )
                
                status = response.get('status', 'UNKNOWN')
                
                # Log status for debugging
                print(f"[Genie Poll] Status: {status}, Elapsed: {time.time() - start_time:.1f}s")
                
                if status in ['COMPLETED', 'FAILED', 'CANCELLED']:
                    return {
                        'status': status.lower(),
                        'response': response
                    }
                
                # Wait before next poll
                time.sleep(poll_interval)
                
                # Gradually increase poll interval
                poll_interval = min(poll_interval * 1.2, 10)
                    
            except Exception as e:
                print(f"[Genie Poll Error] {str(e)}")
                # Don't fail immediately on single poll error, keep trying
                time.sleep(poll_interval)
        
        return {'status': 'timeout', 'error': f'Query did not complete within {max_wait_seconds}s'}
    
    def get_query_results(self, conversation_id: str, message_id: str, attachment_id: str):
        """
        Retrieve query results from a completed Genie query.
        This makes an additional API call to get the actual data.
        """
        try:
            print(f"[Genie] Fetching query results for attachment {attachment_id}")
            response = self.w.api_client.do(
                'GET',
                f'/api/2.0/genie/spaces/{self.space_id}/conversations/{conversation_id}/messages/{message_id}/query-result/{attachment_id}'
            )
            print(f"[Genie] Query results fetched successfully")
            return {
                'status': 'success',
                'results': response
            }
        except Exception as e:
            print(f"[Genie] Error fetching query results: {str(e)}")
            return {'status': 'error', 'error': str(e)}
    
    def query(self, question: str):
        """Complete Genie query workflow: start → poll → retrieve results"""
        # Step 1: Start conversation
        print(f"[Genie] Starting conversation with question: {question[:100]}...")
        start_result = self.start_conversation(question)
        
        if start_result.get('status') != 'started':
            error_msg = f"Error starting conversation: {start_result.get('error', 'Unknown error')}"
            print(f"[Genie Error] {error_msg}")
            return error_msg
        
        conversation_id = start_result['conversation_id']
        message_id = start_result['message_id']
        print(f"[Genie] Started conversation {conversation_id}, message {message_id}")
        
        # Step 2: Poll for completion
        poll_result = self.poll_for_result(conversation_id, message_id, max_wait_seconds=180)
        
        poll_status = poll_result.get('status')
        print(f"[Genie] Poll result status: {poll_status}")
        
        if poll_status == 'failed':
            # Get more details about the failure
            response = poll_result.get('response', {})
            error_detail = response.get('error', {}).get('message', 'Query execution failed')
            return f"Query failed: {error_detail}"
        
        if poll_status != 'completed':
            return f"Query did not complete: {poll_result.get('error', poll_result.get('status'))}"
        
        # Step 3: Extract results
        response = poll_result['response']
        
        # Debug: Log the response structure
        print(f"[Genie] Response keys: {list(response.keys())}")
        print(f"[Genie] Content: {response.get('content', '')[:200]}")
        
        # Get main content (always present)
        text_content = response.get('content', '')
        
        # Try to get attachments
        attachments = response.get('attachments', [])
        print(f"[Genie] Found {len(attachments)} attachments")
        print(f"[Genie] Attachments type: {type(attachments)}")
        
        # Debug: Check if attachments is actually populated
        if attachments is None:
            print(f"[Genie] WARNING: attachments is None!")
            attachments = []
        elif not attachments:
            print(f"[Genie] WARNING: attachments is empty!")
            print(f"[Genie] Full response keys: {list(response.keys())}")
            # Check if there's query_result field directly in response
            if 'query_result' in response:
                print(f"[Genie] Found query_result directly in response!")
        
        # Initialize result
        result = {
            "text": text_content,
            "query": None,
            "data": None,
            "conversation_id": conversation_id,
            "message_id": message_id,
            "raw_response": response  # Keep full response for debugging
        }
        
        # If we have attachments, extract additional details AND FETCH ACTUAL DATA
        if attachments:
            attachment = attachments[0]
            # Note: The field is 'attachment_id', not 'id'!
            attachment_id = attachment.get('attachment_id') or attachment.get('id')
            print(f"[Genie] Found {len(attachments)} attachments")
            print(f"[Genie] Attachment ID: {attachment_id}")
            print(f"[Genie] Attachment keys: {list(attachment.keys())}")
            print(f"[Genie] Attachment type: {attachment.get('type', 'unknown')}")
            
            # Debug: print full attachment to see structure
            import json
            try:
                att_json = json.dumps(attachment, indent=2, default=str)
                print(f"[Genie] Full attachment (first 1500 chars):\n{att_json[:1500]}")
            except:
                print(f"[Genie] Could not serialize attachment")
            
            if not attachment_id:
                print(f"[Genie] WARNING: No attachment_id found! Cannot retrieve query results.")
            
            # Extract text from attachment (might be more detailed than main content)
            text_obj = attachment.get('text', {})
            if isinstance(text_obj, dict):
                attachment_text = text_obj.get('content', '')
                if attachment_text:
                    result['text'] = attachment_text
            
            # Extract query SQL - try multiple possible structures
            query_obj = attachment.get('query', {})
            if isinstance(query_obj, dict):
                # Try structure 1: query.query
                result['query'] = query_obj.get('query', '')
                
                # Try structure 2: query.content (from the article example)
                if not result['query']:
                    result['query'] = query_obj.get('content', '')
                
                print(f"[Genie] Extracted SQL query: {result['query'][:100] if result['query'] else 'None'}...")
                print(f"[Genie] query_obj keys: {list(query_obj.keys())}")
                print(f"[Genie] query_obj type: {type(query_obj)}")
                
                # Debug: print full query object
                import json
                try:
                    query_json = json.dumps(query_obj, indent=2, default=str)
                    print(f"[Genie] Full query_obj (first 1000 chars):\n{query_json[:1000]}")
                except:
                    print(f"[Genie] Could not serialize query_obj")
            
            # *** STEP 6: Retrieve query results using attachment_id (per Microsoft documentation) ***
            # https://learn.microsoft.com/en-us/azure/databricks/genie/conversation-api#-step-6-retrieve-query-results
            if attachment_id:
                print(f"[Genie] Calling query-result endpoint with attachment_id: {attachment_id}")
                try:
                    # Use the official endpoint from Microsoft docs
                    query_result_response = self.w.api_client.do(
                        'GET',
                        f'/api/2.0/genie/spaces/{self.space_id}/conversations/{conversation_id}/messages/{message_id}/query-result/{attachment_id}'
                    )
                    
                    print(f"[Genie] Query result response keys: {list(query_result_response.keys())}")
                    
                    # Debug: Print full response structure
                    import json
                    try:
                        result_json = json.dumps(query_result_response, indent=2, default=str)
                        print(f"[Genie] Full query result response (first 2000 chars):\n{result_json[:2000]}")
                    except:
                        print(f"[Genie] Could not serialize query result response")
                    
                    # Parse the response - data is wrapped in 'statement_response'
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
                                print(f"[Genie] Successfully converted {len(result['data'])} rows to dicts from Genie API")
                            else:
                                print(f"[Genie] No data_array in result")
                        else:
                            print(f"[Genie] No manifest in statement_response")
                    else:
                        print(f"[Genie] No statement_response in query result response")
                        
                except Exception as e:
                    print(f"[Genie] Error calling query-result endpoint: {str(e)}")
                    import traceback
                    print(f"[Genie] Traceback: {traceback.format_exc()}")
        
        # FALLBACK: If we have the SQL query but no data, execute it ourselves
        if result.get('query') and not result.get('data'):
            print(f"[Genie] FALLBACK: No data from Genie API, executing SQL query directly...")
            result['used_fallback'] = True  # Mark that we're using fallback
            try:
                from databricks.sdk.service.sql import StatementState
                
                execute_response = self.w.statement_execution.execute_statement(
                    warehouse_id=os.getenv("DATABRICKS_WAREHOUSE_ID", "148ccb90800933a1"),
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
                        print(f"[Genie] Fallback successfully converted {len(result['data'])} rows")
                else:
                    error_msg = execute_response.status.error.message if execute_response.status.error else "Unknown error"
                    print(f"[Genie] Fallback execution failed: {error_msg}")
            except Exception as e:
                print(f"[Genie] Fallback execution error: {str(e)}")
                import traceback
                print(f"[Genie] Traceback: {traceback.format_exc()}")
        
        print(f"[Genie] Final result text length: {len(result.get('text') or '')}")
        print(f"[Genie] Data rows extracted: {len(result.get('data') or [])}")
        
        # Determine which method was used
        if result.get('data'):
            if result.get('used_fallback'):
                result['method'] = 'Direct SQL Execution (Fallback)'
                print(f"[Genie] Method used: FALLBACK SQL")
            else:
                result['method'] = 'Genie query-result API'
                print(f"[Genie] Method used: GENIE API")
        
        return result

# Initialize Genie tool
@st.cache_resource
def get_genie_tool():
    """Initialize Genie tool"""
    if w:
        return GenieConversationTool(w, GENIE_SPACE_ID)
    return None

genie_tool = get_genie_tool()

# ===== LANGCHAIN TOOLS FOR LANGRAPH AGENT =====
try:
    from langchain_core.tools import Tool
    from pydantic import BaseModel, Field
    from langgraph.prebuilt import create_react_agent
    from langchain_core.messages import SystemMessage
    from databricks_langchain import ChatDatabricks
    
    LANGCHAIN_AVAILABLE = True
    
    # Tool input schemas
    class ClassifyTicketInput(BaseModel):
        ticket_text: str = Field(description="The support ticket text to classify")
    
    class ExtractMetadataInput(BaseModel):
        ticket_text: str = Field(description="The support ticket text to extract metadata from")
    
    class SearchKnowledgeInput(BaseModel):
        query: str = Field(description="The search query to find relevant documentation")
    
    class QueryHistoricalInput(BaseModel):
        question: str = Field(description="Natural language question about historical tickets")
    
    # Tool wrapper functions
    def classify_ticket_wrapper(ticket_text: str) -> str:
        """Classifies a support ticket into category, priority, and routing team"""
        result = call_uc_function("ai_classify", ticket_text, show_debug=False)
        import json
        return json.dumps(result, indent=2) if result else json.dumps({"error": "Classification failed"})
    
    def extract_metadata_wrapper(ticket_text: str) -> str:
        """Extracts detailed metadata from a support ticket"""
        result = call_uc_function("ai_extract", ticket_text, show_debug=False)
        import json
        return json.dumps(result, indent=2) if result else json.dumps({"error": "Extraction failed"})
    
    def search_knowledge_wrapper(query: str) -> str:
        """Searches the knowledge base for relevant articles and documentation"""
        import json
        # Call vector search WITHOUT Streamlit UI (for tool execution)
        try:
            if not w:
                return json.dumps({"error": "WorkspaceClient not initialized"})
            
            body = {
                "columns": ["doc_id", "doc_type", "title", "content"],
                "num_results": 3,
                "query_text": query
            }
            
            response = w.api_client.do(
                'POST',
                f'/api/2.0/vector-search/indexes/{INDEX_NAME}/query',
                body=body
            )
            
            # Check for error
            if isinstance(response, dict) and 'error_code' in response:
                error_msg = response.get('message', 'Unknown error')
                return json.dumps({"error": f"Vector Search error: {error_msg}"})
            
            # Extract results
            data_array = response.get('result', {}).get('data_array', [])
            
            if data_array:
                formatted = []
                for row in data_array:
                    formatted.append({
                        "doc_id": row[0],
                        "doc_type": row[1],
                        "title": row[2],
                        "content": row[3][:500]  # Truncate for agent
                    })
                return json.dumps(formatted, indent=2)
            return json.dumps([])
        except Exception as e:
            return json.dumps({"error": f"Search failed: {str(e)}"})
    
    def query_historical_wrapper(question: str) -> str:
        """Queries historical resolved tickets using natural language"""
        if not genie_tool:
            return json.dumps({"error": "Genie tool not available"})
        result = genie_tool.query(question)
        import json
        return json.dumps(result, indent=2, default=str)
    
    # Create LangChain Tools
    classify_tool = Tool(
        name="classify_ticket",
        description="Classifies a support ticket into category, priority, and routing team. Use this FIRST to understand the ticket type. Returns JSON with category, priority, team, confidence.",
        func=classify_ticket_wrapper,
        args_schema=ClassifyTicketInput
    )
    
    extract_tool = Tool(
        name="extract_metadata",
        description="Extracts detailed metadata from ticket including priority score, urgency level, affected systems, technical keywords, and user impact. Use after classification to get deeper insights. Returns JSON with structured metadata.",
        func=extract_metadata_wrapper,
        args_schema=ExtractMetadataInput
    )
    
    search_tool = Tool(
        name="search_knowledge",
        description="Searches the knowledge base for relevant articles, documentation, and solutions using semantic search. Use to find how-to guides, troubleshooting steps, or existing documentation. Returns JSON array with title, content, category for top matches.",
        func=search_knowledge_wrapper,
        args_schema=SearchKnowledgeInput
    )
    
    genie_tool_langchain = Tool(
        name="query_historical",
        description="Queries historical resolved tickets using natural language to find similar cases and their resolutions. Use for complex issues where past solutions might help. Returns JSON with text summary and optionally SQL query used.",
        func=query_historical_wrapper,
        args_schema=QueryHistoricalInput
    )
    
    # LangGraph Agent creation
    @st.cache_resource
    def create_langraph_agent():
        """Create the LangGraph ReAct agent with all tools"""
        try:
            # Use Meta Llama 3.3 70B for function calling support
            # This is the best available model in the workspace for tool calling
            agent_endpoint = "databricks-meta-llama-3-3-70b-instruct"
            
            # Initialize LLM with Llama 3.3 70B (good function calling support)
            llm = ChatDatabricks(
                endpoint=agent_endpoint,
                temperature=0.1,  # Small temp for more reliable tool calls
                max_tokens=2000
            )
            
            # Create agent with all tools
            tools_list = [classify_tool, extract_tool, search_tool, genie_tool_langchain]
            agent = create_react_agent(
                model=llm,
                tools=tools_list
            )
            
            return agent
        except Exception as e:
            st.error(f"Error creating agent: {e}")
            import traceback
            st.error(traceback.format_exc())
            return None
    
except ImportError as e:
    LANGCHAIN_AVAILABLE = False
    st.warning(f"LangChain/LangGraph not available: {e}")

def query_vector_search(query_text, num_results=3):
    """
    Query Vector Search using WorkspaceClient's API client (handles OAuth automatically).
    Reference: https://learn.microsoft.com/en-us/azure/databricks/generative-ai/create-query-vector-search#query
    """
    try:
        if not w:
            st.error("WorkspaceClient not initialized")
            return []
        
        st.info(f"🔍 Querying Vector Search: {INDEX_NAME}")
        
        # Build payload according to REST API spec
        # The API expects the body as a dict with specific fields
        body = {
            "columns": ["doc_id", "doc_type", "title", "content"],
            "num_results": num_results,
            "query_text": query_text
        }
        
        # Use WorkspaceClient's API client - it handles OAuth authentication automatically
        # Use 'body' parameter instead of 'data' for proper JSON serialization
        response = w.api_client.do(
            'POST',
            f'/api/2.0/vector-search/indexes/{INDEX_NAME}/query',
            body=body
        )
        
        # Check for error in response
        if isinstance(response, dict) and 'error_code' in response:
            error_msg = response.get('message', 'Unknown error')
            st.error(f"Vector Search error: {error_msg}")
            
            # Check if index is still syncing
            if 'not ready' in error_msg.lower() or 'syncing' in error_msg.lower() or 'offline' in error_msg.lower():
                st.warning("⏳ The Vector Search index is still syncing.")
                st.info("The index was recently created and may take 5-10 minutes to be ready. Please try again in a few minutes.")
            
            return []
        
        # Extract results according to API response format
        # Response format: {"manifest": {...}, "result": {"row_count": N, "data_array": [[...]]}}
        data_array = response.get('result', {}).get('data_array', [])
        
        if not data_array:
            st.warning("No results found in Vector Search")
        else:
            st.success(f"✅ Found {len(data_array)} relevant knowledge base articles")
            
        return data_array
    
    except Exception as e:
        error_msg = str(e)
        st.error(f"Vector Search error: {error_msg}")
        
        # Check for common error patterns
        if '404' in error_msg or 'not found' in error_msg.lower():
            st.warning(f"Index not found: {INDEX_NAME}")
            st.info("The index may still be creating. Please wait a few minutes.")
        elif '403' in error_msg or 'forbidden' in error_msg.lower():
            st.error("Permission denied. The app may not have access to the Vector Search index.")
            st.info("Make sure the app's service principal has SELECT privilege on the index.")
        elif '400' in error_msg or 'invalid' in error_msg.lower() or 'json' in error_msg.lower():
            st.error("Bad request - the API rejected the query format")
            st.info("This may indicate the index is not fully initialized yet.")
        
        import traceback
        with st.expander("🔍 Debug Details"):
            st.code(traceback.format_exc())
        
        return []

def call_uc_function(function_name, *args, timeout=50, show_debug=True):
    """Call a Unity Catalog function using Statement Execution API (more reliable for Databricks Apps)"""
    try:
        # Escape single quotes in string arguments
        escaped_args = []
        for arg in args:
            if isinstance(arg, str):
                # Escape single quotes by doubling them for SQL
                escaped_arg = arg.replace("'", "''")
                escaped_args.append(f"'{escaped_arg}'")
            else:
                escaped_args.append(str(arg))
        
        args_str = ', '.join(escaped_args)
        query = f"SELECT {CATALOG}.{SCHEMA}.{function_name}({args_str}) as result"
        
        if show_debug:
            st.info(f"🔍 Executing: {function_name}(...) on warehouse {WAREHOUSE_ID}")
        
        # Use Statement Execution API (more reliable for Databricks Apps)
        # Note: wait_timeout must be between 5s and 50s (API limit)
        try:
            result = w.statement_execution.execute_statement(
                warehouse_id=WAREHOUSE_ID,
                statement=query,
                wait_timeout="50s"  # Maximum allowed by API
            )
            
            # Check if execution was successful
            if result.status.state.value == "SUCCEEDED":
                # Extract result from data_array
                if result.result and result.result.data_array:
                    data = result.result.data_array[0][0]
                    
                    # Debug: Show what we received
                    if show_debug:
                        with st.expander(f"🔍 Debug: {function_name} raw response"):
                            st.write("Type:", type(data))
                            st.write("Data:", data)
                    
                    # Handle different response types
                    if isinstance(data, str):
                        # Try to parse as JSON (for string-encoded structs)
                        import json
                        try:
                            parsed = json.loads(data)
                            if show_debug:
                                st.success(f"✅ Parsed {function_name} as JSON")
                            return parsed
                        except:
                            # Not JSON, return as-is
                            if show_debug:
                                st.info(f"ℹ️ {function_name} returned string (not JSON)")
                            return data
                    
                    elif isinstance(data, dict):
                        # Already a dict - return as-is
                        if show_debug:
                            st.success(f"✅ {function_name} returned dict")
                        return data
                    
                    elif isinstance(data, (list, tuple)):
                        # For STRUCT types, Statement Execution API might return as array
                        # Need to map to field names based on function
                        if function_name == "ai_gen":
                            # ai_gen returns: summary, recommendations, resolution_steps, estimated_resolution_time
                            if show_debug:
                                st.info(f"🔍 ai_gen returned array with {len(data)} elements")
                                with st.expander("🔍 Debug: Raw ai_gen response"):
                                    st.write("Type:", type(data))
                                    st.write("Length:", len(data))
                                    st.write("Data:", data)
                            
                            if len(data) >= 4:
                                result = {
                                    'summary': data[0],
                                    'recommendations': data[1] if data[1] else [],
                                    'resolution_steps': data[2] if data[2] else [],
                                    'estimated_resolution_time': data[3]
                                }
                                if show_debug:
                                    st.success("✅ Parsed ai_gen response successfully")
                                return result
                            else:
                                st.error(f"ai_gen returned unexpected array length: {len(data)}")
                                if show_debug:
                                    with st.expander("🔍 Debug: Array contents"):
                                        for i, item in enumerate(data):
                                            st.write(f"Index {i}: {item}")
                                return None
                        else:
                            # For other functions, return as-is
                            return data
                    
                    else:
                        # Unknown type - return as-is
                        return data
                else:
                    if show_debug:
                        st.warning("Function returned no data")
                    return None
            else:
                if show_debug:
                    st.error(f"Query failed with state: {result.status.state.value}")
                    if result.status.error:
                        st.error(f"Error: {result.status.error.message}")
                return None
        
        except Exception as api_error:
            if show_debug:
                st.error(f"Statement Execution API error: {api_error}")
                import traceback
                with st.expander("🔍 Debug Details"):
                    st.code(traceback.format_exc())
            return None
    
    except Exception as e:
        if show_debug:
            st.error(f"Error calling UC function {function_name}: {e}")
            import traceback
            with st.expander("🔍 Debug Details"):
                st.code(traceback.format_exc())
        return None

# Sample tickets for testing
SAMPLE_TICKETS = {
    "Production Database Down (P1)": "URGENT: Production database server PROD-DB-01 is completely down. All customer-facing applications are showing error messages. This is affecting hundreds of users and we are losing revenue. Database logs show Connection refused errors. Need immediate attention!",
    
    "Ransomware Attack (P1)": "EMERGENCY! User in Finance department clicked on a suspicious email attachment. Now their computer is showing a ransom note and files are encrypted with .locked extension. We immediately disconnected the computer from the network. Need security team NOW!",
    
    "VPN Issues - Sales Team (P2)": "Our entire sales team (about 30 people) is experiencing VPN disconnections every 15-20 minutes. They need stable VPN to access CRM and sales databases. This started this morning around 9 AM EST. Getting Connection lost - reconnecting errors.",
    
    "CRM Application Slow (P2)": "The CRM application has been very slow since yesterday afternoon. Takes 30+ seconds to load customer records, normally it is instant. About 20 people in sales team are affected. We can still work but it is very frustrating.",
    
    "Phishing Email (P2)": "Everyone in our marketing department (about 15 people) received a suspicious email this morning claiming to be from IT. The email asks us to verify our credentials by clicking a link. Nobody has clicked it yet but wanted to report this immediately.",
    
    "Password Reset (P3)": "Hi IT, I forgot my password and need to reset it. I tried the self-service portal but cannot remember the answers to my security questions. This is not urgent, I can use my personal laptop today if needed.",
    
    "New User Access (P3)": "We have a new employee starting next Monday, Sarah Thompson. She will need access to email, CRM system, file shares for Sales department, and VPN access. Her manager is Mike Chen. Please set this up before her start date.",
    
    "Printer Not Working (P3)": "The printer in Conference Room B is not working. When I try to print, nothing happens. The printer shows as online in the system but documents just sit in the queue. Not urgent as we can use the printer in the next room.",
}

# Main UI
st.title("🎫 AI-Powered Support Ticket Classification")
st.markdown("Real-time ticket classification using Unity Catalog AI Functions and Vector Search")

# Sidebar
with st.sidebar:
    st.header("⚙️ Configuration")
    st.info(f"**Catalog:** {CATALOG}\n\n**Schema:** {SCHEMA}\n\n**Warehouse:** {WAREHOUSE_ID}\n\n**Environment:** Databricks Apps")
    
    st.markdown("---")
    
    st.header("📊 System Status")
    if w:
        st.success("✅ Databricks Connected")
    else:
        st.error("❌ Databricks Not Connected")
    
    st.markdown("---")
    
    st.header("🎯 Classification Phases")
    st.markdown("""
    1. **Basic Classification** (ai_classify)
    2. **Metadata Extraction** (ai_extract)
    3. **Vector Search** (semantic retrieval)
    4. **Summary Generation** (ai_gen)
    5. **Hybrid Classification** (combined)
    6. **Quick Classify** (single call)
    """)
    
    st.markdown("---")
    st.caption("💰 Cost per ticket: <$0.002\n⏱️ Processing time: <3s")

# Tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs(["🚀 Quick Classify", "📋 6-Phase Classification", "📊 Batch Processing", "🤖 AI Agent Assistant", "🧠 LangGraph Agent"])

with tab1:
    st.header("Quick Classification (Single Function Call)")
    st.markdown("**Fastest method:** All analysis in one UC function call (~1 second)")
    
    # Ticket input
    col1, col2 = st.columns([3, 1])
    
    with col1:
        sample_choice = st.selectbox("Select a sample ticket or write your own:", ["Custom"] + list(SAMPLE_TICKETS.keys()))
    
    if sample_choice == "Custom":
        ticket_text = st.text_area("Enter support ticket:", height=150, value="")
    else:
        ticket_text = st.text_area("Enter support ticket:", height=150, value=SAMPLE_TICKETS[sample_choice])
    
    if st.button("🚀 Classify Ticket", key="quick_classify_btn", type="primary"):
        if not ticket_text.strip():
            st.warning("Please enter a ticket description")
        else:
            status_placeholder = st.empty()
            status_placeholder.info("⏳ Connecting to SQL warehouse... (may take 30-60s if warehouse is starting)")
            
            with st.spinner("Classifying ticket..."):
                start_time = time.time()
                
                # Call quick_classify_ticket function with max allowed timeout
                result = call_uc_function("quick_classify_ticket", ticket_text, timeout=50)
                
                status_placeholder.empty()  # Clear status message
                elapsed_time = (time.time() - start_time) * 1000
                
                if result:
                    st.success(f"✅ Classification complete in {elapsed_time:.0f}ms")
                    
                    # Display results in columns
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("Category", result.get('category', 'Unknown'))
                        st.metric("Priority", result.get('priority', 'Unknown'))
                    
                    with col2:
                        st.metric("Assigned Team", result.get('assigned_team', 'Unknown'))
                        st.metric("Urgency Level", result.get('urgency_level', 'Unknown'))
                    
                    with col3:
                        # Handle priority_score - might be string or float
                        priority_score = result.get('priority_score', 0.0)
                        try:
                            priority_val = float(priority_score) if priority_score else 0.0
                            st.metric("Priority Score", f"{priority_val:.2f}")
                        except (ValueError, TypeError):
                            st.metric("Priority Score", str(priority_score))
                        st.metric("Cost", "$0.0005")
                    
                    # Summary
                    st.markdown("### 📝 Summary")
                    st.info(result.get('summary', 'No summary available'))
                    
                    # Affected Systems
                    if result.get('affected_systems'):
                        st.markdown("### 🖥️ Affected Systems")
                        systems = result.get('affected_systems', [])
                        if systems:
                            st.write(", ".join(systems))
                        else:
                            st.write("No specific systems identified")
                    
                    # Recommendations
                    st.markdown("### 💡 Recommendations")
                    recommendations = result.get('recommendations', [])
                    if recommendations:
                        for i, rec in enumerate(recommendations, 1):
                            st.write(f"{i}. {rec}")
                    else:
                        st.write("No recommendations available")
                    
                    # Performance metrics
                    st.markdown("---")
                    st.caption(f"⏱️ Execution time: {elapsed_time:.0f}ms | 💰 Estimated cost: $0.0005")

with tab2:
    st.header("6-Phase Classification Pipeline")
    st.markdown("**Complete analysis:** Step-by-step classification with Vector Search (~3-5 seconds)")
    
    # Ticket input
    sample_choice_6phase = st.selectbox("Select a sample ticket:", ["Custom"] + list(SAMPLE_TICKETS.keys()), key="6phase_sample")
    
    if sample_choice_6phase == "Custom":
        ticket_text_6phase = st.text_area("Enter support ticket:", height=150, value="", key="6phase_text")
    else:
        ticket_text_6phase = st.text_area("Enter support ticket:", height=150, value=SAMPLE_TICKETS[sample_choice_6phase], key="6phase_text_filled")
    
    if st.button("🔍 Run 6-Phase Classification", key="6phase_btn", type="primary"):
        if not ticket_text_6phase.strip():
            st.warning("Please enter a ticket description")
        else:
            total_start = time.time()
            total_cost = 0.0
            
            # Phase 1: Basic Classification
            st.markdown("### Phase 1: Basic Classification")
            with st.spinner("Running ai_classify..."):
                start = time.time()
                classify_result = call_uc_function("ai_classify", ticket_text_6phase)
                elapsed = (time.time() - start) * 1000
                cost = 0.0004
                total_cost += cost
                
                if classify_result:
                    col1, col2, col3, col4 = st.columns(4)
                    col1.metric("Category", classify_result.get('category', 'N/A'))
                    col2.metric("Priority", classify_result.get('priority', 'N/A'))
                    col3.metric("Team", classify_result.get('assigned_team', 'N/A'))
                    
                    # Handle confidence - might be string or float
                    confidence = classify_result.get('confidence', 0)
                    try:
                        confidence_val = float(confidence) if confidence else 0.0
                        col4.metric("Confidence", f"{confidence_val:.2f}")
                    except (ValueError, TypeError):
                        col4.metric("Confidence", str(confidence))
                    
                    st.caption(f"⏱️ {elapsed:.0f}ms | 💰 ${cost:.4f}")
            
            st.markdown("---")
            
            # Phase 2: Metadata Extraction
            st.markdown("### Phase 2: Metadata Extraction")
            with st.spinner("Running ai_extract..."):
                start = time.time()
                extract_result = call_uc_function("ai_extract", ticket_text_6phase)
                elapsed = (time.time() - start) * 1000
                cost = 0.0005
                total_cost += cost
                
                if extract_result:
                    col1, col2, col3 = st.columns(3)
                    
                    # Handle priority_score - might be string or float
                    priority_score = extract_result.get('priority_score', 0)
                    try:
                        priority_val = float(priority_score) if priority_score else 0.0
                        col1.metric("Priority Score", f"{priority_val:.2f}")
                    except (ValueError, TypeError):
                        col1.metric("Priority Score", str(priority_score))
                    
                    col2.metric("Urgency", extract_result.get('urgency_level', 'N/A'))
                    col3.metric("User Impact", extract_result.get('user_impact', 'N/A'))
                    
                    if extract_result.get('affected_systems'):
                        st.write("**Affected Systems:**", ", ".join(extract_result.get('affected_systems', [])))
                    
                    if extract_result.get('technical_keywords'):
                        st.write("**Keywords:**", ", ".join(extract_result.get('technical_keywords', [])))
                    
                    st.caption(f"⏱️ {elapsed:.0f}ms | 💰 ${cost:.4f}")
            
            st.markdown("---")
            
            # Phase 3: Vector Search
            st.markdown("### Phase 3: Vector Search (Knowledge Base Retrieval)")
            with st.spinner("Searching knowledge base..."):
                start = time.time()
                vs_results = query_vector_search(ticket_text_6phase, num_results=3)
                elapsed = (time.time() - start) * 1000
                cost = 0.0001
                total_cost += cost
                
                if vs_results:
                    st.success(f"Found {len(vs_results)} relevant knowledge base articles")
                    
                    for i, row in enumerate(vs_results, 1):
                        with st.expander(f"📄 Result {i}: {row[2]}", expanded=(i == 1)):
                            st.write(f"**Doc ID:** {row[0]}")
                            st.write(f"**Type:** {row[1]}")
                            st.write(f"**Content:** {row[3][:500]}...")
                    
                    # Combine context for ai_gen
                    context = "\n\n".join([f"{row[2]}\n{row[3][:1000]}" for row in vs_results])
                else:
                    st.warning("No relevant knowledge base articles found")
                    context = "No relevant context found."
                
                st.caption(f"⏱️ {elapsed:.0f}ms | 💰 ${cost:.4f}")
            
            st.markdown("---")
            
            # Phase 4: Summary Generation
            st.markdown("### Phase 4: Summary and Recommendations")
            with st.spinner("Generating summary with AI..."):
                start = time.time()
                gen_result = call_uc_function("ai_gen", ticket_text_6phase, context)
                elapsed = (time.time() - start) * 1000
                cost = 0.0003
                total_cost += cost
                
                if gen_result:
                    st.info(f"**Summary:** {gen_result.get('summary', 'N/A')}")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write("**Recommendations:**")
                        for rec in gen_result.get('recommendations', []):
                            st.write(f"• {rec}")
                    
                    with col2:
                        st.write("**Resolution Steps:**")
                        for i, step in enumerate(gen_result.get('resolution_steps', []), 1):
                            st.write(f"{i}. {step}")
                    
                    st.metric("Estimated Resolution Time", gen_result.get('estimated_resolution_time', 'Unknown'))
                    st.caption(f"⏱️ {elapsed:.0f}ms | 💰 ${cost:.4f}")
            
            # Total metrics
            total_elapsed = (time.time() - total_start) * 1000
            st.markdown("---")
            st.success(f"✅ 6-Phase Classification Complete")
            
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Time", f"{total_elapsed:.0f}ms")
            col2.metric("Total Cost", f"${total_cost:.4f}")
            col3.metric("Phases", "4 of 6")

with tab3:
    st.header("Batch Processing")
    st.markdown("**Process multiple tickets at once**")
    
    st.info("Upload a CSV file with tickets or paste multiple tickets (one per line)")
    
    # File upload
    uploaded_file = st.file_uploader("Upload CSV file (must have 'ticket_text' column)", type=['csv'])
    
    if uploaded_file:
        import pandas as pd
        df = pd.read_csv(uploaded_file)
        
        if 'ticket_text' not in df.columns:
            st.error("CSV must have a 'ticket_text' column")
        else:
            st.write(f"Loaded {len(df)} tickets")
            st.dataframe(df.head())
            
            if st.button("Process All Tickets", key="batch_process_btn"):
                with st.spinner(f"Processing {len(df)} tickets..."):
                    results = []
                    progress_bar = st.progress(0)
                    
                    for i, row in df.iterrows():
                        ticket = row['ticket_text']
                        result = call_uc_function("quick_classify_ticket", ticket)
                        
                        if result:
                            results.append({
                                'ticket_text': ticket[:100] + '...',
                                'category': result.get('category', ''),
                                'priority': result.get('priority', ''),
                                'team': result.get('assigned_team', ''),
                                'urgency': result.get('urgency_level', '')
                            })
                        
                        progress_bar.progress((i + 1) / len(df))
                    
                    # Display results
                    st.success(f"✅ Processed {len(results)} tickets")
                    results_df = pd.DataFrame(results)
                    st.dataframe(results_df)
                    
                    # Download results
                    csv = results_df.to_csv(index=False)
                    st.download_button(
                        label="📥 Download Results",
                        data=csv,
                        file_name="classified_tickets.csv",
                        mime="text/csv"
                    )

with tab4:
    st.header("🤖 Multi-Agent Ticket Assistant")
    st.markdown("""
    **Comprehensive AI Analysis:** Get intelligent ticket analysis using multiple AI agents that coordinate to:
    - 🎯 Classify the ticket automatically
    - 📊 Extract detailed metadata  
    - 📚 Search knowledge base for solutions
    - 🔍 Find similar resolved tickets (via Genie)
    - 💡 Generate comprehensive recommendations
    """)
    
    # Ticket input
    st.markdown("---")
    st.subheader("Enter Support Ticket")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        sample_choice_agent = st.selectbox(
            "Select a sample ticket or write your own:", 
            ["Custom"] + list(SAMPLE_TICKETS.keys()), 
            key="agent_sample"
        )
    
    if sample_choice_agent == "Custom":
        ticket_text_agent = st.text_area(
            "Ticket Description:", 
            height=200, 
            value="",
            key="agent_text",
            placeholder="Describe the issue in detail..."
        )
    else:
        ticket_text_agent = st.text_area(
            "Ticket Description:", 
            height=200, 
            value=SAMPLE_TICKETS[sample_choice_agent],
            key="agent_text_filled"
        )
    
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        analyze_button = st.button("🤖 Analyze with AI Agent", type="primary", key="agent_analyze_btn")
    with col2:
        use_genie = st.checkbox("Include Historical Tickets (Genie)", value=True, key="agent_use_genie")
    
    if analyze_button:
        if not ticket_text_agent.strip():
            st.warning("⚠️ Please enter a ticket description")
        else:
            st.markdown("---")
            st.markdown("### 🔄 Agent Processing")
            
            total_start = time.time()
            results = {}
            
            # Container for agent status
            status_container = st.container()
            
            with status_container:
                # Phase 1: Classification
                with st.status("🎯 Agent 1: Classifying ticket...", expanded=True) as status_classify:
                    start = time.time()
                    classify_result = call_uc_function("ai_classify", ticket_text_agent, show_debug=False)
                    elapsed = (time.time() - start) * 1000
                    
                    if classify_result:
                        results['classification'] = classify_result
                        st.write(f"✅ Category: **{classify_result.get('category', 'N/A')}**")
                        st.write(f"✅ Priority: **{classify_result.get('priority', 'N/A')}**")
                        st.write(f"✅ Team: **{classify_result.get('assigned_team', 'N/A')}**")
                        status_classify.update(label=f"✅ Classification Complete ({elapsed:.0f}ms)", state="complete")
                    else:
                        status_classify.update(label="❌ Classification Failed", state="error")
                
                # Phase 2: Metadata Extraction
                with st.status("📊 Agent 2: Extracting metadata...", expanded=True) as status_extract:
                    start = time.time()
                    extract_result = call_uc_function("ai_extract", ticket_text_agent, show_debug=False)
                    elapsed = (time.time() - start) * 1000
                    
                    if extract_result:
                        results['metadata'] = extract_result
                        priority_score = extract_result.get('priority_score', 0)
                        try:
                            priority_val = float(priority_score) if priority_score else 0.0
                            st.write(f"✅ Priority Score: **{priority_val:.2f}**")
                        except:
                            st.write(f"✅ Priority Score: **{priority_score}**")
                        st.write(f"✅ Urgency: **{extract_result.get('urgency_level', 'N/A')}**")
                        if extract_result.get('affected_systems'):
                            st.write(f"✅ Affected Systems: {', '.join(extract_result.get('affected_systems', []))}")
                        status_extract.update(label=f"✅ Metadata Extracted ({elapsed:.0f}ms)", state="complete")
                    else:
                        status_extract.update(label="❌ Extraction Failed", state="error")
                
                # Phase 3: Vector Search
                with st.status("📚 Agent 3: Searching knowledge base...", expanded=True) as status_search:
                    start = time.time()
                    vs_results = query_vector_search(ticket_text_agent, num_results=3)
                    elapsed = (time.time() - start) * 1000
                    
                    if vs_results:
                        results['knowledge_base'] = vs_results
                        st.write(f"✅ Found {len(vs_results)} relevant documentation articles")
                        for i, row in enumerate(vs_results[:2], 1):
                            st.write(f"  {i}. {row[2]}")
                        status_search.update(label=f"✅ Knowledge Base Searched ({elapsed:.0f}ms)", state="complete")
                    else:
                        st.write("⚠️ No relevant articles found")
                        results['knowledge_base'] = []
                        status_search.update(label=f"⚠️ No Results ({elapsed:.0f}ms)", state="complete")
                
                # Phase 4: Genie Query (if enabled)
                if use_genie and genie_tool:
                    with st.status("🔍 Agent 4: Querying historical tickets (Genie)...", expanded=True) as status_genie:
                        start = time.time()
                        
                        # Build intelligent query based on classification
                        category = results.get('classification', {}).get('category', 'issue')
                        team = results.get('classification', {}).get('assigned_team', 'team')
                        
                        # Simplified query that's more likely to work
                        genie_question = f"Show me 3 recent tickets from the {team} team with their resolution details"
                        
                        st.write(f"📝 Query: _{genie_question}_")
                        
                        genie_result = genie_tool.query(genie_question)
                        elapsed = (time.time() - start) * 1000
                        
                        # If first query fails, try a simpler fallback
                        if isinstance(genie_result, str) and 'did not complete' in genie_result.lower():
                            st.write(f"⚠️ First query failed, trying simpler query...")
                            genie_question = "Show me 3 tickets with their resolution details"
                            genie_result = genie_tool.query(genie_question)
                            elapsed = (time.time() - start) * 1000
                        
                        # Check if we got a result (dict with text, or string response)
                        if isinstance(genie_result, dict):
                            text_result = genie_result.get('text', '')
                            if text_result and len(text_result.strip()) > 0:
                                results['genie'] = genie_result
                                st.write(f"✅ Found similar historical tickets")
                                # Show first 200 chars as preview
                                preview = text_result[:200]
                                if len(text_result) > 200:
                                    preview += "..."
                                st.write(f"📊 {preview}")
                                status_genie.update(label=f"✅ Historical Tickets Retrieved ({elapsed:.0f}ms)", state="complete")
                            else:
                                st.write(f"⚠️ Genie query completed but returned no text content")
                                st.write(f"📝 Response keys: {list(genie_result.keys())}")
                                results['genie'] = None
                                status_genie.update(label=f"⚠️ No Data Returned ({elapsed:.0f}ms)", state="complete")
                        elif isinstance(genie_result, str):
                            # String response indicates an error
                            st.write(f"⚠️ {genie_result}")
                            st.write(f"ℹ️ Genie may need a few minutes to index the ticket_history table")
                            results['genie'] = None
                            status_genie.update(label=f"⚠️ Query Incomplete ({elapsed:.0f}ms)", state="complete")
                        else:
                            st.write(f"⚠️ Unexpected response type: {type(genie_result)}")
                            results['genie'] = None
                            status_genie.update(label=f"⚠️ Query Incomplete ({elapsed:.0f}ms)", state="complete")
                elif use_genie:
                    st.warning("⚠️ Genie tool not initialized")
            
            # Summary and Recommendations
            st.markdown("---")
            st.markdown("### 📋 Comprehensive Analysis")
            
            total_elapsed = (time.time() - total_start) * 1000
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Category", results.get('classification', {}).get('category', 'N/A'))
            with col2:
                st.metric("Priority", results.get('classification', {}).get('priority', 'N/A'))
            with col3:
                st.metric("Team", results.get('classification', {}).get('assigned_team', 'N/A'))
            with col4:
                st.metric("Processing Time", f"{total_elapsed:.0f}ms")
            
            # Detailed Analysis
            st.markdown("#### 🎯 Classification Details")
            if results.get('metadata'):
                metadata = results['metadata']
                col1, col2 = st.columns(2)
                
                with col1:
                    priority_score = metadata.get('priority_score', 0)
                    try:
                        priority_val = float(priority_score) if priority_score else 0.0
                        st.write(f"**Priority Score:** {priority_val:.2f}")
                    except:
                        st.write(f"**Priority Score:** {priority_score}")
                    st.write(f"**Urgency Level:** {metadata.get('urgency_level', 'N/A')}")
                    st.write(f"**User Impact:** {metadata.get('user_impact', 'N/A')}")
                
                with col2:
                    if metadata.get('affected_systems'):
                        st.write("**Affected Systems:**")
                        for system in metadata.get('affected_systems', []):
                            st.write(f"  • {system}")
                    
                    if metadata.get('technical_keywords'):
                        st.write("**Technical Keywords:**")
                        st.write(", ".join(metadata.get('technical_keywords', [])))
            
            # Knowledge Base Results
            if results.get('knowledge_base'):
                st.markdown("#### 📚 Relevant Documentation")
                for i, row in enumerate(results['knowledge_base'], 1):
                    with st.expander(f"📄 {row[2]}", expanded=(i == 1)):
                        st.write(f"**Type:** {row[1]}")
                        st.write(f"**Content:** {row[3][:500]}...")
            
            # Genie Results
            if results.get('genie'):
                st.markdown("#### 🔍 Similar Historical Tickets")
                genie_data = results['genie']
                
                # Debug: Show what we received
                st.info(f"Debug: Genie returned data type: {type(genie_data.get('data'))}, length: {len(genie_data.get('data') or [])}")
                
                # Display the actual ticket data
                if genie_data.get('data'):
                    tickets = genie_data['data']
                    method = genie_data.get('method', 'Unknown')
                    st.success(f"Found {len(tickets)} similar historical tickets")
                    st.caption(f"📡 Data Source: {method}")
                    
                    for i, ticket in enumerate(tickets, 1):
                        # ticket_history schema: ticket_id, ticket_text, root_cause, resolution, resolution_time_hours, resolved_at
                        ticket_id = ticket.get('ticket_id', 'Unknown')
                        ticket_summary = ticket.get('ticket_text', '')[:60] + "..." if len(ticket.get('ticket_text', '')) > 60 else ticket.get('ticket_text', 'Unknown')
                        
                        with st.expander(f"🎫 Ticket #{i}: {ticket_id} - {ticket_summary}", expanded=(i == 1)):
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.write(f"**Ticket ID:** {ticket_id}")
                                resolution_time = ticket.get('resolution_time_hours', 'N/A')
                                if resolution_time != 'N/A':
                                    st.write(f"**Resolution Time:** {resolution_time} hours")
                                resolved_at = ticket.get('resolved_at', 'N/A')
                                if resolved_at != 'N/A':
                                    # Format the timestamp nicely
                                    st.write(f"**Resolved At:** {str(resolved_at)[:19]}")
                            
                            with col2:
                                st.write(f"**Status:** ✅ Resolved")
                            
                            # Show ticket description
                            if ticket.get('ticket_text'):
                                st.markdown("**📝 Issue Description:**")
                                st.info(ticket['ticket_text'])
                            
                            # Show root cause if available
                            if ticket.get('root_cause'):
                                st.markdown("**🔍 Root Cause:**")
                                st.warning(ticket['root_cause'])
                            
                            # Show resolution
                            if ticket.get('resolution'):
                                st.markdown("**✅ Resolution:**")
                                st.success(ticket['resolution'])
                else:
                    # Fallback: show text summary if no data
                    st.warning("⚠️ No structured ticket data extracted from Genie")
                    if genie_data.get('text'):
                        st.info(f"Genie response text:\n\n{genie_data['text']}")
                    else:
                        st.error("No text content either - check server logs for debug info")
                    
                    # Show raw genie_data keys for debugging
                    with st.expander("🔍 Debug: Genie Response Keys"):
                        st.json({
                            "keys": list(genie_data.keys()),
                            "conversation_id": genie_data.get('conversation_id'),
                            "message_id": genie_data.get('message_id'),
                            "has_text": bool(genie_data.get('text')),
                            "has_query": bool(genie_data.get('query')),
                            "has_data": bool(genie_data.get('data'))
                        })
                        st.markdown("**Full Genie Response (for debugging):**")
                        st.json(genie_data)
                
                # Show SQL query in expander
                if genie_data.get('query'):
                    with st.expander("📊 View SQL Query"):
                        st.code(genie_data['query'], language='sql')
            
            # Action Recommendations
            st.markdown("#### 💡 Recommended Actions")
            
            # Generate context-aware recommendations
            category = results.get('classification', {}).get('category', '')
            priority = results.get('classification', {}).get('priority', '')
            team = results.get('classification', {}).get('assigned_team', '')
            
            recommendations = []
            
            if priority == 'P1':
                recommendations.append("🚨 **URGENT:** Escalate immediately to on-call team")
                recommendations.append("📞 Initiate incident response protocol")
            elif priority == 'P2':
                recommendations.append("⚡ Assign to next available team member")
                recommendations.append("📊 Monitor for similar issues")
            else:
                recommendations.append("📝 Add to team queue")
                recommendations.append("📅 Schedule within SLA timeframe")
            
            if results.get('knowledge_base'):
                recommendations.append(f"📚 Review {len(results['knowledge_base'])} relevant documentation articles")
            
            if results.get('genie') and isinstance(results.get('genie'), dict):
                recommendations.append("🔍 Check historical resolution patterns")
            
            recommendations.append(f"👥 Route to **{team}** team")
            
            for rec in recommendations:
                st.write(rec)
            
            # Export Results
            st.markdown("---")
            
            export_data = {
                "ticket": ticket_text_agent[:200],
                "classification": results.get('classification', {}),
                "metadata": results.get('metadata', {}),
                "knowledge_articles": len(results.get('knowledge_base', [])),
                "processing_time_ms": total_elapsed,
                "recommendations": recommendations
            }
            
            col1, col2 = st.columns([1, 3])
            with col1:
                st.download_button(
                    label="📥 Export Analysis",
                    data=json.dumps(export_data, indent=2),
                    file_name="ticket_analysis.json",
                    mime="application/json",
                    key="agent_export_btn"
                )
            
            with col2:
                st.caption(f"💰 Estimated cost: $0.002 | ⏱️ Total time: {total_elapsed:.0f}ms | 🤖 4 AI agents coordinated")

with tab5:
    st.header("🧠 LangGraph ReAct Agent")
    st.markdown("""
    **Intelligent Agent:** Uses LangGraph's ReAct (Reasoning + Acting) pattern to:
    - 🧠 **Think** about which tools to use
    - 🔧 **Act** by calling the right tools
    - 🔄 **Observe** the results and decide next steps
    - 🎯 **Adapt** its strategy based on ticket complexity
    
    **Key Difference:** Unlike the multi-agent tab which runs all tools sequentially, 
    this agent intelligently chooses which tools to use and in what order.
    """)
    
    if not LANGCHAIN_AVAILABLE:
        st.error("❌ LangChain/LangGraph not available. Please install required packages.")
        st.code("pip install langgraph>=1.0.0 langchain>=0.3.0 langchain-core>=0.3.0 databricks-langchain")
    else:
        # Ticket input
        st.markdown("---")
        st.subheader("Enter Support Ticket")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            sample_choice_langraph = st.selectbox(
                "Select a sample ticket or write your own:", 
                ["Custom"] + list(SAMPLE_TICKETS.keys()), 
                key="langraph_sample"
            )
        
        if sample_choice_langraph == "Custom":
            ticket_text_langraph = st.text_area(
                "Ticket Description:", 
                height=200, 
                value="",
                key="langraph_text",
                placeholder="Describe the issue in detail..."
            )
        else:
            ticket_text_langraph = st.text_area(
                "Ticket Description:", 
                height=200, 
                value=SAMPLE_TICKETS[sample_choice_langraph],
                key="langraph_text_filled"
            )
        
        col1, col2 = st.columns([1, 3])
        with col1:
            analyze_button_langraph = st.button("🧠 Analyze with LangGraph Agent", type="primary", key="langraph_analyze_btn")
        
        if analyze_button_langraph:
            if not ticket_text_langraph.strip():
                st.warning("⚠️ Please enter a ticket description")
            else:
                st.markdown("---")
                st.markdown("### 🤖 Agent Execution")
                
                total_start = time.time()
                
                # Create agent
                agent = create_langraph_agent()
                
                if not agent:
                    st.error("Failed to create LangGraph agent")
                else:
                    # System prompt
                    system_prompt = """You are an expert IT support ticket analyst. Your job is to analyze support tickets and provide comprehensive recommendations.

You have access to these tools:
1. classify_ticket - Classifies tickets into category/priority/team. Use this FIRST.
2. extract_metadata - Extracts detailed metadata. Use after classification.
3. search_knowledge - Searches knowledge base for solutions. Use for most tickets.
4. query_historical - Finds similar historical tickets. Use for complex P1/P2 issues.

IMPORTANT: You MUST use the tools by calling them properly. After using tools, provide a final text summary.

Analysis strategy:
- Start with classify_ticket
- Then use extract_metadata
- Use search_knowledge to find solutions
- For P1/P2 tickets, also use query_historical
- After gathering information, provide your final analysis

Be thorough but efficient."""
                    
                    # Container for agent reasoning
                    reasoning_container = st.container()
                    
                    with reasoning_container:
                        st.markdown("#### 🧠 Agent Reasoning Process")
                        
                        # Show agent thinking
                        with st.spinner("🤔 Agent is analyzing the ticket..."):
                            try:
                                # Invoke agent with system message
                                result = agent.invoke({
                                    "messages": [
                                        SystemMessage(content=system_prompt),
                                        ("user", f"Analyze this support ticket and provide recommendations: {ticket_text_langraph}")
                                    ]
                                })
                                
                                elapsed_time = (time.time() - total_start) * 1000
                                
                                # Parse messages to show reasoning
                                messages = result.get('messages', [])
                                
                                st.success(f"✅ Analysis complete in {elapsed_time:.0f}ms")
                                st.markdown("---")
                                
                                # Show tool calls and reasoning
                                tool_calls = []
                                agent_thoughts = []
                                agent_response = None
                                
                                for msg in messages:
                                    msg_type = getattr(msg, 'type', None) or type(msg).__name__.lower()
                                    
                                    if 'ai' in msg_type:
                                        # AI message (thought or final response)
                                        content = getattr(msg, 'content', '')
                                        tool_calls_in_msg = getattr(msg, 'tool_calls', [])
                                        
                                        if tool_calls_in_msg:
                                            # This is a thought with tool calls
                                            for tc in tool_calls_in_msg:
                                                tool_name = tc.get('name', 'unknown')
                                                tool_args = tc.get('args', {})
                                                tool_calls.append({
                                                    'name': tool_name,
                                                    'args': tool_args
                                                })
                                        elif content:
                                            # This is reasoning or final answer
                                            if not agent_response:  # First AI message with content is likely the final answer
                                                agent_response = content
                                            else:
                                                agent_thoughts.append(content)
                                    
                                    elif 'tool' in msg_type:
                                        # Tool response
                                        tool_name = getattr(msg, 'name', 'unknown')
                                        tool_content = getattr(msg, 'content', '')
                                        
                                        # Find matching tool call
                                        for tc in tool_calls:
                                            if tc['name'] == tool_name and 'result' not in tc:
                                                tc['result'] = tool_content
                                                break
                                
                                # Display tool calls in expandable sections
                                if tool_calls:
                                    st.markdown("#### 🔧 Tools Used by Agent")
                                    st.info(f"Agent used **{len(tool_calls)} tools** out of 4 available")
                                    
                                    for i, tc in enumerate(tool_calls, 1):
                                        tool_name = tc['name']
                                        tool_args = tc.get('args', {})
                                        tool_result = tc.get('result', 'No result')
                                        
                                        # Icon based on tool
                                        icon = "🎯" if "classify" in tool_name else "📊" if "extract" in tool_name else "📚" if "search" in tool_name else "🔍"
                                        
                                        with st.expander(f"{icon} **Tool {i}: {tool_name}**", expanded=(i <= 2)):
                                            st.write("**Input:**")
                                            st.json(tool_args)
                                            
                                            st.write("**Output:**")
                                            try:
                                                result_json = json.loads(tool_result)
                                                st.json(result_json)
                                            except:
                                                st.text(tool_result[:500] + "..." if len(tool_result) > 500 else tool_result)
                                else:
                                    st.warning("No tool calls detected in agent execution")
                                
                                # Display final response
                                st.markdown("---")
                                st.markdown("#### 💡 Agent's Final Analysis")
                                
                                if agent_response:
                                    st.markdown(agent_response)
                                else:
                                    st.info("Agent completed analysis. Check tool outputs above for details.")
                                
                                # Performance metrics
                                st.markdown("---")
                                col1, col2, col3 = st.columns(3)
                                
                                with col1:
                                    st.metric("Tools Used", f"{len(tool_calls)}/4")
                                with col2:
                                    st.metric("Total Time", f"{elapsed_time:.0f}ms")
                                with col3:
                                    # Estimate cost based on tools used
                                    cost_per_tool = 0.0005
                                    total_cost = len(tool_calls) * cost_per_tool
                                    st.metric("Estimated Cost", f"${total_cost:.4f}")
                                
                                # Show raw messages for debugging
                                with st.expander("🔍 Debug: Raw Agent Messages"):
                                    for i, msg in enumerate(messages):
                                        st.write(f"**Message {i+1}:** {type(msg).__name__}")
                                        st.write(f"Content: {getattr(msg, 'content', 'N/A')[:200]}")
                                        if hasattr(msg, 'tool_calls') and msg.tool_calls:
                                            st.write(f"Tool calls: {len(msg.tool_calls)}")
                                        st.markdown("---")
                                
                            except Exception as e:
                                st.error(f"Error running agent: {e}")
                                import traceback
                                with st.expander("🔍 Error Details"):
                                    st.code(traceback.format_exc())
        
        # Comparison with other approaches
        st.markdown("---")
        st.markdown("### 🔄 LangGraph Agent vs Other Approaches")
        
        comparison_data = {
            "Approach": ["Quick Classify", "6-Phase Pipeline", "Multi-Agent", "LangGraph Agent"],
            "Speed": ["⚡ Fastest (~1s)", "🐌 Slower (~3-5s)", "🐌 Slower (~3-5s)", "⚡ Adaptive (1-5s)"],
            "Cost": ["💰 Lowest ($0.0005)", "💰💰 Higher ($0.002)", "💰💰 Higher ($0.002)", "💰 Adaptive ($0.0005-$0.002)"],
            "Intelligence": ["🤖 Fixed", "🤖 Fixed", "🤖🤖 Coordinated", "🤖🤖🤖 Adaptive"],
            "Tools Used": ["1 (combined)", "4 (always)", "4 (always)", "1-4 (adaptive)"],
            "Best For": ["Simple tickets", "Comprehensive analysis", "All tickets", "All tickets (smart)"]
        }
        
        import pandas as pd
        comparison_df = pd.DataFrame(comparison_data)
        st.table(comparison_df)
        
        st.markdown("""
        **Why Use LangGraph Agent?**
        - 🧠 **Intelligent**: Decides which tools to use based on ticket complexity
        - ⚡ **Efficient**: Skips unnecessary tools for simple tickets (saves time & money)
        - 🎯 **Comprehensive**: Uses all tools when needed for complex issues
        - 🔍 **Transparent**: Shows reasoning process and tool selection
        
        **Example:**
        - **P3 ticket** (password reset): Agent uses 2 tools → $0.001, ~1-2s
        - **P1 ticket** (database down): Agent uses 4 tools → $0.002, ~3-5s
        """)

# Footer
st.markdown("---")
st.caption("🏗️ Built with Unity Catalog AI Functions, Vector Search, Genie, LangGraph, and Streamlit | ☁️ Running on Databricks Apps")

