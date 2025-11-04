# Databricks notebook source
# MAGIC %md
# MAGIC # LangGraph POC: Multi-Agent Ticket Processing with Tools
# MAGIC
# MAGIC Tests LangGraph with LangChain Tools calling:
# MAGIC - UC Functions (ai_classify, ai_extract)
# MAGIC - Vector Search (knowledge base)
# MAGIC - Genie (historic tickets)
# MAGIC
# MAGIC **Architecture:** Agent with tools (LLM decides which tools to call)
# MAGIC
# MAGIC **Based on:** [Databricks LangGraph Multi-Agent Documentation](https://docs.databricks.com/aws/en/notebooks/source/generative-ai/langgraph-multiagent-genie.html)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Install Dependencies

# COMMAND ----------

# MAGIC %pip install --upgrade langgraph langchain langchain-community databricks-sdk mlflow
# MAGIC dbutils.library.restartPython()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Configuration

# COMMAND ----------

from databricks.sdk import WorkspaceClient
import os

# Configuration
CATALOG = "classify_tickets_new_dev"
SCHEMA = "support_ai"
INDEX_NAME = f"{CATALOG}.{SCHEMA}.knowledge_base_index"

# IMPORTANT: Set this after creating Genie Space
# Get it from Genie Space URL: .../genie/spaces/YOUR_ID_HERE
GENIE_SPACE_ID = "01f0b91aa91c1b0c8cce6529ea09f0a8"  # TODO: Update after creating Genie Space

# LLM Configuration
LLM_ENDPOINT = "databricks-meta-llama-3-1-70b-instruct"

# Initialize Databricks client
w = WorkspaceClient()

print(f"📋 Configuration:")
print(f"  Catalog: {CATALOG}")
print(f"  Schema: {SCHEMA}")
print(f"  Vector Search Index: {INDEX_NAME}")
print(f"  Genie Space ID: {GENIE_SPACE_ID}")
print(f"  LLM Endpoint: {LLM_ENDPOINT}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Define LangChain Tools
# MAGIC
# MAGIC Each tool wraps a direct API call to Databricks services.

# COMMAND ----------

from langchain.tools import tool
from typing import Dict, List
import json

@tool
def classify_ticket(ticket_text: str) -> Dict:
    """
    Classify a support ticket into category, priority, and assigned team.
    
    Args:
        ticket_text: The full text of the support ticket
        
    Returns:
        Dictionary with category, priority, and assigned_team
    """
    try:
        # Direct SQL call to UC Function
        result = spark.sql(f"""
            SELECT {CATALOG}.{SCHEMA}.ai_classify('{ticket_text}') as classification
        """).collect()[0][0]
        
        return {"status": "success", "classification": result}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@tool
def extract_ticket_metadata(ticket_text: str) -> Dict:
    """
    Extract detailed metadata from a support ticket including urgency level,
    affected systems, and priority score.
    
    Args:
        ticket_text: The full text of the support ticket
        
    Returns:
        Dictionary with urgency_level, affected_systems, priority_score, assigned_team
    """
    try:
        # Direct SQL call to UC Function
        result = spark.sql(f"""
            SELECT {CATALOG}.{SCHEMA}.ai_extract('{ticket_text}') as metadata
        """).collect()[0][0]
        
        return {"status": "success", "metadata": result}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@tool
def search_knowledge_base(query: str, num_results: int = 3) -> List[Dict]:
    """
    Search the knowledge base for relevant documentation, runbooks, and guides
    using semantic similarity search.
    
    Args:
        query: Search query (typically the ticket text or a specific question)
        num_results: Number of results to return (default: 3)
        
    Returns:
        List of relevant documents with doc_id, doc_type, title, and content
    """
    try:
        # Direct REST API call to Vector Search
        response = w.api_client.do(
            'POST',
            f'/api/2.0/vector-search/indexes/{INDEX_NAME}/query',
            body={
                'columns': ['doc_id', 'doc_type', 'title', 'content'],
                'query_text': query,
                'num_results': num_results
            }
        )
        
        data_array = response.get('result', {}).get('data_array', [])
        
        # Format results
        documents = []
        for row in data_array:
            if len(row) >= 4:
                documents.append({
                    'doc_id': row[0],
                    'doc_type': row[1],
                    'title': row[2],
                    'content': row[3][:500]  # Truncate for readability
                })
        
        return {"status": "success", "documents": documents, "count": len(documents)}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@tool
def query_ticket_history(question: str) -> str:
    """
    Query historical resolved tickets using natural language via Genie.
    Useful for finding similar past tickets, common root causes, and proven resolutions.
    
    Args:
        question: Natural language question about past tickets
        Example: "Find similar database down tickets from last month"
        
    Returns:
        Natural language response with relevant historical ticket information
    """
    if GENIE_SPACE_ID == "YOUR_GENIE_SPACE_ID":
        return {"status": "error", "error": "Genie Space ID not configured. Please update GENIE_SPACE_ID variable."}
    
    try:
        # Direct Genie API call
        result = w.genie.query(
            space_id=GENIE_SPACE_ID,
            content=question
        )
        
        # Extract text response from Genie result
        # Genie returns a complex object; we want the text response
        response_text = str(result)
        
        return {"status": "success", "response": response_text}
    except Exception as e:
        return {"status": "error", "error": str(e)}

# List all available tools
tools = [classify_ticket, extract_ticket_metadata, search_knowledge_base, query_ticket_history]

print(f"✅ Defined {len(tools)} LangChain tools:")
for tool in tools:
    print(f"  • {tool.name}: {tool.description.split('.')[0]}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Create LangGraph Agent with Tools

# COMMAND ----------

from langchain_community.chat_models import ChatDatabricks
from langgraph.prebuilt import create_react_agent
from langgraph.graph import MessagesState
from typing import Annotated
from langchain_core.messages import HumanMessage, AIMessage

# Initialize LLM
llm = ChatDatabricks(
    endpoint=LLM_ENDPOINT,
    temperature=0.1,  # Low temperature for more consistent responses
    max_tokens=2000
)

print(f"✅ Initialized LLM: {LLM_ENDPOINT}")

# Create agent with tools
# The agent will reason about which tools to call based on the ticket
agent = create_react_agent(
    model=llm,
    tools=tools,
    state_modifier="""You are an AI support ticket assistant that helps classify and analyze support tickets.

Your job is to:
1. Classify the ticket using classify_ticket tool
2. Extract detailed metadata using extract_ticket_metadata tool  
3. Search for relevant documentation using search_knowledge_base tool
4. Find similar past tickets using query_ticket_history tool
5. Provide a comprehensive analysis combining all information

Be thorough and use all available tools to provide the best analysis."""
)

print(f"✅ Created LangGraph ReAct agent with {len(tools)} tools")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Test Agent with Sample Ticket

# COMMAND ----------

# Test ticket - database down scenario
test_ticket = """
Production database server PROD-DB-01 is completely down!
All customer-facing applications are showing connection errors.
This is affecting hundreds of users and we're losing revenue.
Database logs show "Connection refused" errors.
This started 10 minutes ago and needs immediate attention!
"""

print("🎫 Test Ticket:")
print(test_ticket)
print("\n" + "="*80 + "\n")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Run Agent

# COMMAND ----------

# Create input message
messages = [
    HumanMessage(content=f"""Analyze this support ticket and provide a comprehensive analysis:

{test_ticket}

Please:
1. Classify the ticket (category, priority, team)
2. Extract detailed metadata
3. Search for relevant knowledge base documentation
4. Find similar past tickets and their resolutions
5. Provide a summary with recommendations""")
]

# Invoke agent
print("🤖 Agent processing ticket...\n")

try:
    result = agent.invoke({"messages": messages})
    
    print("\n" + "="*80)
    print("📊 AGENT RESULT")
    print("="*80 + "\n")
    
    # Display all messages (shows the reasoning process)
    for msg in result['messages']:
        if isinstance(msg, HumanMessage):
            print(f"👤 USER: {msg.content[:200]}...")
        elif isinstance(msg, AIMessage):
            print(f"🤖 AGENT: {msg.content}")
            print()
        else:
            # Tool calls and results
            if hasattr(msg, 'content'):
                print(f"🔧 TOOL: {msg.content[:300]}...")
                print()
    
except Exception as e:
    print(f"❌ Error running agent: {e}")
    import traceback
    traceback.print_exc()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Test with Another Ticket (VPN Issue)

# COMMAND ----------

test_ticket_2 = """
Our entire sales team is experiencing VPN disconnections every 15 minutes.
About 30 people affected. They need stable VPN to access CRM and databases.
Getting "Connection lost - reconnecting" errors.
VPN server is VPN-GATEWAY-02.
Started this morning around 9 AM EST.
"""

print("🎫 Test Ticket 2:")
print(test_ticket_2)
print("\n" + "="*80 + "\n")

messages_2 = [
    HumanMessage(content=f"""Analyze this support ticket:

{test_ticket_2}

Classify it, search for relevant docs, and find similar past issues.""")
]

print("🤖 Agent processing second ticket...\n")

try:
    result_2 = agent.invoke({"messages": messages_2})
    
    # Display final response
    final_message = result_2['messages'][-1]
    print("\n" + "="*80)
    print("📊 FINAL ANALYSIS")
    print("="*80 + "\n")
    print(final_message.content)
    
except Exception as e:
    print(f"❌ Error: {e}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Manual Tool Testing (Individual Tools)

# COMMAND ----------

print("🧪 Testing individual tools...\n")

# Test 1: Classify Ticket
print("1️⃣ Testing classify_ticket tool:")
classification_result = classify_ticket.invoke({"ticket_text": test_ticket})
print(json.dumps(classification_result, indent=2))
print()

# Test 2: Extract Metadata
print("2️⃣ Testing extract_ticket_metadata tool:")
metadata_result = extract_ticket_metadata.invoke({"ticket_text": test_ticket})
print(json.dumps(metadata_result, indent=2))
print()

# Test 3: Vector Search
print("3️⃣ Testing search_knowledge_base tool:")
search_result = search_knowledge_base.invoke({
    "query": "database connection errors troubleshooting",
    "num_results": 2
})
print(json.dumps(search_result, indent=2))
print()

# Test 4: Genie Query (if configured)
if GENIE_SPACE_ID != "YOUR_GENIE_SPACE_ID":
    print("4️⃣ Testing query_ticket_history tool:")
    genie_result = query_ticket_history.invoke({
        "question": "Find tickets about database connection issues that were resolved"
    })
    print(json.dumps(genie_result, indent=2))
else:
    print("4️⃣ Skipping Genie test - GENIE_SPACE_ID not configured")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Performance Metrics

# COMMAND ----------

import time

def measure_agent_performance(ticket_text, description):
    """Measure agent performance"""
    print(f"\n⏱️ Performance Test: {description}")
    print("="*60)
    
    start_time = time.time()
    
    messages = [HumanMessage(content=f"Analyze this ticket: {ticket_text}")]
    
    try:
        result = agent.invoke({"messages": messages})
        end_time = time.time()
        
        total_time = end_time - start_time
        num_tool_calls = len([m for m in result['messages'] if hasattr(m, 'tool_calls')])
        
        print(f"✅ Success")
        print(f"⏱️  Total Time: {total_time:.2f} seconds")
        print(f"🔧 Tool Calls: {num_tool_calls}")
        print(f"💬 Messages: {len(result['messages'])}")
        
        return {"success": True, "time": total_time, "tool_calls": num_tool_calls}
        
    except Exception as e:
        end_time = time.time()
        print(f"❌ Error: {str(e)}")
        print(f"⏱️  Time until error: {end_time - start_time:.2f} seconds")
        return {"success": False, "error": str(e)}

# Run performance tests
perf_results = []

test_cases = [
    ("Database is down!", "Simple P1 ticket"),
    ("VPN disconnecting frequently for sales team", "P2 network issue"),
    ("Need password reset", "Simple P3 request")
]

for ticket, desc in test_cases:
    result = measure_agent_performance(ticket, desc)
    perf_results.append(result)
    time.sleep(2)  # Avoid rate limits

# COMMAND ----------

# MAGIC %md
# MAGIC ## Summary

# COMMAND ----------

print("="*80)
print("📋 LANGGRAPH POC SUMMARY")
print("="*80)
print()
print("✅ Components Tested:")
print("  1. LangChain Tools - Wrapping direct API calls")
print("  2. UC Functions - ai_classify, ai_extract")
print("  3. Vector Search - Semantic search over knowledge base")
print("  4. Genie - Natural language queries over ticket history")
print("  5. LangGraph ReAct Agent - LLM reasoning about tool usage")
print()
print("🎯 Key Findings:")
print(f"  • Total tools available: {len(tools)}")
print(f"  • LLM model: {LLM_ENDPOINT}")
print(f"  • Agent type: ReAct (Reasoning + Acting)")
print()
print("📊 Performance:")
if perf_results:
    successful = [r for r in perf_results if r.get('success')]
    if successful:
        avg_time = sum(r['time'] for r in successful) / len(successful)
        print(f"  • Average processing time: {avg_time:.2f} seconds")
        print(f"  • Successful tests: {len(successful)}/{len(perf_results)}")
print()
print("🚀 Next Steps:")
print("  1. Create Genie Space (if not done)")
print("  2. Update GENIE_SPACE_ID in notebook")
print("  3. Re-run to test Genie integration")
print("  4. Build full multi-agent system if POC successful")
print()
print("="*80)

# COMMAND ----------

# MAGIC %md
# MAGIC ## How to Create Genie Space
# MAGIC
# MAGIC **Steps:**
# MAGIC 1. Navigate to: **Data Intelligence → Genie**
# MAGIC 2. Click **"Create Genie Space"**
# MAGIC 3. Name: `ticket_history_poc`
# MAGIC 4. Add table: `classify_tickets_new_dev.support_ai.ticket_history`
# MAGIC 5. **Instructions** (paste this):
# MAGIC    ```
# MAGIC    You help find similar resolved support tickets.
# MAGIC    
# MAGIC    When asked about similar tickets:
# MAGIC    - Search by category, priority, and keywords from the ticket description
# MAGIC    - Show the root cause and resolution
# MAGIC    - Focus on tickets resolved in the last 60 days
# MAGIC    - Include resolution time to set expectations
# MAGIC    ```
# MAGIC 6. Copy the **Genie Space ID** from the URL:
# MAGIC    - URL format: `https://...databricks.net/.../genie/spaces/YOUR_ID_HERE`
# MAGIC 7. Update `GENIE_SPACE_ID` variable in Cell 3 above
# MAGIC 8. Re-run the notebook

# COMMAND ----------

