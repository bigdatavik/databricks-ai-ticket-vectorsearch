"""
AI-Powered Support Ticket Classification Dashboard
PRODUCTION VERSION - For Databricks Apps deployment

This version uses WorkspaceClient() for authentication (no manual config needed).
For local development, use app_simple.py instead.
"""

import streamlit as st
import json
import time
from databricks.sdk import WorkspaceClient

# Page configuration
st.set_page_config(
    page_title="AI Ticket Classification",
    page_icon="🎫",
    layout="wide"
)

# Configuration
CATALOG = "classify_tickets_new_dev"
SCHEMA = "support_ai"
INDEX_NAME = f"{CATALOG}.{SCHEMA}.knowledge_base_index"

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

def call_uc_function(function_name, *args, timeout=50):
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
        
        # Use specific warehouse from MY_ENVIRONMENT.md
        warehouse_id = "148ccb90800933a1"
        
        st.info(f"🔍 Executing: {function_name}(...) on warehouse {warehouse_id}")
        
        # Use Statement Execution API (more reliable for Databricks Apps)
        # Note: wait_timeout must be between 5s and 50s (API limit)
        try:
            result = w.statement_execution.execute_statement(
                warehouse_id=warehouse_id,
                statement=query,
                wait_timeout="50s"  # Maximum allowed by API
            )
            
            # Check if execution was successful
            if result.status.state.value == "SUCCEEDED":
                # Extract result from data_array
                if result.result and result.result.data_array:
                    data = result.result.data_array[0][0]
                    
                    # Debug: Show what we received
                    with st.expander(f"🔍 Debug: {function_name} raw response"):
                        st.write("Type:", type(data))
                        st.write("Data:", data)
                    
                    # Handle different response types
                    if isinstance(data, str):
                        # Try to parse as JSON (for string-encoded structs)
                        import json
                        try:
                            parsed = json.loads(data)
                            st.success(f"✅ Parsed {function_name} as JSON")
                            return parsed
                        except:
                            # Not JSON, return as-is
                            st.info(f"ℹ️ {function_name} returned string (not JSON)")
                            return data
                    
                    elif isinstance(data, dict):
                        # Already a dict - return as-is
                        st.success(f"✅ {function_name} returned dict")
                        return data
                    
                    elif isinstance(data, (list, tuple)):
                        # For STRUCT types, Statement Execution API might return as array
                        # Need to map to field names based on function
                        if function_name == "ai_gen":
                            # ai_gen returns: summary, recommendations, resolution_steps, estimated_resolution_time
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
                                st.success("✅ Parsed ai_gen response successfully")
                                return result
                            else:
                                st.error(f"ai_gen returned unexpected array length: {len(data)}")
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
                    st.warning("Function returned no data")
                    return None
            else:
                st.error(f"Query failed with state: {result.status.state.value}")
                if result.status.error:
                    st.error(f"Error: {result.status.error.message}")
                return None
        
        except Exception as api_error:
            st.error(f"Statement Execution API error: {api_error}")
            import traceback
            with st.expander("🔍 Debug Details"):
                st.code(traceback.format_exc())
            return None
    
    except Exception as e:
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
    st.info(f"**Catalog:** {CATALOG}\n\n**Schema:** {SCHEMA}\n\n**Environment:** Databricks Apps")
    
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
tab1, tab2, tab3 = st.tabs(["🚀 Quick Classify", "📋 6-Phase Classification", "📊 Batch Processing"])

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

# Footer
st.markdown("---")
st.caption("🏗️ Built with Unity Catalog AI Functions, Vector Search, and Streamlit | ☁️ Running on Databricks Apps")

