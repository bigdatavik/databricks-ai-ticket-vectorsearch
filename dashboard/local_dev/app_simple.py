"""
AI-Powered Support Ticket Classification Dashboard
LOCAL VERSION - Uses ~/.databrickscfg for authentication

This is the local development version that runs on your laptop.
For production deployment to Databricks Apps, use app_databricks.py
"""

import streamlit as st
import subprocess
import json
import os
import configparser
import time
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.catalog import FunctionInfo

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

# Set environment variable for config profile
os.environ['DATABRICKS_CONFIG_PROFILE'] = 'DEFAULT_azure'

# Initialize Databricks client
@st.cache_resource
def get_workspace_client():
    """Initialize Databricks WorkspaceClient using ~/.databrickscfg"""
    try:
        # This will read from ~/.databrickscfg using the profile from env var
        return WorkspaceClient()
    except Exception as e:
        st.error(f"Failed to initialize Databricks client: {e}")
        st.info("Make sure ~/.databrickscfg exists with DEFAULT_azure profile")
        return None

w = get_workspace_client()

def get_databricks_credentials():
    """Read credentials from ~/.databrickscfg"""
    config = configparser.ConfigParser()
    config_path = os.path.expanduser('~/.databrickscfg')
    config.read(config_path)
    
    profile = os.getenv('DATABRICKS_CONFIG_PROFILE', 'DEFAULT_azure')
    
    if profile not in config:
        raise ValueError(f"Profile '{profile}' not found in {config_path}")
    
    token = config[profile].get('token', '')
    host = config[profile].get('host', '').replace('https://', '')
    
    if not token or not host:
        raise ValueError(f"Missing token or host in profile '{profile}'")
    
    return token, host

def query_vector_search(query_text, num_results=3):
    """
    Query Vector Search using curl subprocess (production pattern).
    Avoids 403 errors from Python SDK.
    """
    try:
        token, host = get_databricks_credentials()
        
        url = f"https://{host}/api/2.0/vector-search/indexes/{INDEX_NAME}/query"
        
        payload = {
            "columns": ["doc_id", "doc_type", "title", "content"],
            "num_results": num_results,
            "query_text": query_text
        }
        
        curl_cmd = [
            'curl', '-s', '-X', 'POST',
            '-H', 'Content-Type: application/json',
            '-H', f'Authorization: Bearer {token}',
            url,
            '-d', json.dumps(payload)
        ]
        
        result = subprocess.run(
            curl_cmd,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode != 0:
            raise Exception(f"curl failed: {result.stderr}")
        
        response = json.loads(result.stdout)
        
        if 'error_code' in response:
            raise Exception(f"API error: {response.get('message', 'Unknown error')}")
        
        return response.get('result', {}).get('data_array', [])
    
    except Exception as e:
        st.error(f"Vector Search error: {e}")
        return []

def call_uc_function(function_name, *args):
    """Call a Unity Catalog function and return the result"""
    try:
        # Build SQL query
        args_str = ', '.join([f"'{arg}'" if isinstance(arg, str) else str(arg) for arg in args])
        query = f"SELECT {CATALOG}.{SCHEMA}.{function_name}({args_str}) as result"
        
        # Execute using Databricks SQL
        from databricks import sql
        
        token, host = get_databricks_credentials()
        
        # Get SQL warehouse (use first available)
        warehouses = list(w.warehouses.list())
        if not warehouses:
            raise Exception("No SQL warehouses available")
        
        warehouse_id = warehouses[0].id
        
        # Connect and execute
        with sql.connect(
            server_hostname=host,
            http_path=f"/sql/1.0/warehouses/{warehouse_id}",
            access_token=token
        ) as connection:
            with connection.cursor() as cursor:
                cursor.execute(query)
                row = cursor.fetchone()
                if row:
                    result = row[0]
                    # Convert Row object to dict if needed
                    if hasattr(result, 'asDict'):
                        return result.asDict()
                    return result
                return None
    
    except Exception as e:
        st.error(f"Error calling UC function {function_name}: {e}")
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

# Sidebar for configuration
with st.sidebar:
    st.header("⚙️ Configuration")
    st.info(f"**Catalog:** {CATALOG}\n\n**Schema:** {SCHEMA}\n\n**Environment:** Local Development")
    
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

# Tabs for different classification methods
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
            with st.spinner("Classifying ticket..."):
                start_time = time.time()
                
                # Call quick_classify_ticket function
                result = call_uc_function("quick_classify_ticket", ticket_text)
                
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
                        priority_score = result.get('priority_score', 0.0)
                        st.metric("Priority Score", f"{priority_score:.2f}")
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
                    col4.metric("Confidence", f"{classify_result.get('confidence', 0):.2f}")
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
                    col1.metric("Priority Score", f"{extract_result.get('priority_score', 0):.2f}")
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
            
            st.caption("Note: Phases 5 (Hybrid) and 6 (Quick) are alternative approaches shown in other tabs")

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
    else:
        # Text area for manual batch entry
        batch_text = st.text_area("Or paste multiple tickets (one per line):", height=200)
        
        if st.button("Process Tickets", key="batch_text_btn") and batch_text:
            tickets = [t.strip() for t in batch_text.split('\n') if t.strip()]
            
            with st.spinner(f"Processing {len(tickets)} tickets..."):
                results = []
                progress_bar = st.progress(0)
                
                for i, ticket in enumerate(tickets):
                    result = call_uc_function("quick_classify_ticket", ticket)
                    
                    if result:
                        results.append({
                            'ticket': ticket[:80] + '...' if len(ticket) > 80 else ticket,
                            'category': result.get('category', ''),
                            'priority': result.get('priority', ''),
                            'team': result.get('assigned_team', '')
                        })
                    
                    progress_bar.progress((i + 1) / len(tickets))
                
                st.success(f"✅ Processed {len(results)} tickets")
                
                import pandas as pd
                results_df = pd.DataFrame(results)
                st.dataframe(results_df)

# Footer
st.markdown("---")
st.caption("🏗️ Built with Unity Catalog AI Functions, Vector Search, and Streamlit | 💻 Running locally with ~/.databrickscfg")

