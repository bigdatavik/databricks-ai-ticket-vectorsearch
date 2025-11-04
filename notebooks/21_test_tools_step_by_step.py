# Databricks notebook source
# MAGIC %md
# MAGIC # Step-by-Step Tool Testing
# MAGIC
# MAGIC Tests each component individually to isolate any issues:
# MAGIC 1. Package installation
# MAGIC 2. UC Functions (ai_classify, ai_extract)
# MAGIC 3. Vector Search
# MAGIC 4. Genie
# MAGIC 5. LangChain Tools
# MAGIC 6. Simple LangGraph workflow

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 1: Install Packages

# COMMAND ----------

print("📦 Installing packages...")
%pip install --quiet --upgrade langgraph langchain langchain-community databricks-sdk mlflow
print("✅ Packages installed successfully")

# COMMAND ----------

# Restart Python to load new packages
dbutils.library.restartPython()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 2: Configuration

# COMMAND ----------

from databricks.sdk import WorkspaceClient
import json

# Configuration
CATALOG = "classify_tickets_new_dev"
SCHEMA = "support_ai"
INDEX_NAME = f"{CATALOG}.{SCHEMA}.knowledge_base_index"
GENIE_SPACE_ID = "01f0b91aa91c1b0c8cce6529ea09f0a8"

# Initialize Databricks client
w = WorkspaceClient()

print("="*60)
print("📋 CONFIGURATION")
print("="*60)
print(f"Catalog: {CATALOG}")
print(f"Schema: {SCHEMA}")
print(f"Vector Search Index: {INDEX_NAME}")
print(f"Genie Space ID: {GENIE_SPACE_ID}")
print(f"Workspace Client: {w.config.host}")
print("="*60)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 3: Test UC Functions

# COMMAND ----------

print("\n" + "="*60)
print("🧪 TEST 1: UC Function - ai_classify")
print("="*60)

test_ticket = "Production database is completely down! All apps showing connection errors."

try:
    result = spark.sql(f"""
        SELECT {CATALOG}.{SCHEMA}.ai_classify('{test_ticket}') as classification
    """).collect()[0][0]
    
    print("✅ ai_classify SUCCESS")
    print(f"Result type: {type(result)}")
    print(f"Result: {result}")
except Exception as e:
    print(f"❌ ai_classify FAILED: {e}")
    import traceback
    traceback.print_exc()

# COMMAND ----------

print("\n" + "="*60)
print("🧪 TEST 2: UC Function - ai_extract")
print("="*60)

try:
    result = spark.sql(f"""
        SELECT {CATALOG}.{SCHEMA}.ai_extract('{test_ticket}') as metadata
    """).collect()[0][0]
    
    print("✅ ai_extract SUCCESS")
    print(f"Result type: {type(result)}")
    print(f"Result: {result}")
except Exception as e:
    print(f"❌ ai_extract FAILED: {e}")
    import traceback
    traceback.print_exc()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 4: Test Vector Search

# COMMAND ----------

print("\n" + "="*60)
print("🧪 TEST 3: Vector Search")
print("="*60)

try:
    response = w.api_client.do(
        'POST',
        f'/api/2.0/vector-search/indexes/{INDEX_NAME}/query',
        body={
            'columns': ['doc_id', 'doc_type', 'title', 'content'],
            'query_text': 'database connection troubleshooting',
            'num_results': 3
        }
    )
    
    print("✅ Vector Search SUCCESS")
    print(f"Response type: {type(response)}")
    
    data_array = response.get('result', {}).get('data_array', [])
    print(f"Number of results: {len(data_array)}")
    
    if data_array:
        print("\nFirst result:")
        if len(data_array[0]) >= 3:
            print(f"  - doc_id: {data_array[0][0]}")
            print(f"  - doc_type: {data_array[0][1]}")
            print(f"  - title: {data_array[0][2]}")
            print(f"  - content preview: {data_array[0][3][:100]}...")
    
except Exception as e:
    print(f"❌ Vector Search FAILED: {e}")
    import traceback
    traceback.print_exc()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 5: Test Genie

# COMMAND ----------

print("\n" + "="*60)
print("🧪 TEST 4: Genie Query")
print("="*60)

try:
    # Simple query to test Genie
    query = "Show me 3 tickets about database issues"
    
    print(f"Query: {query}")
    
    result = w.genie.query(
        space_id=GENIE_SPACE_ID,
        content=query
    )
    
    print("✅ Genie Query SUCCESS")
    print(f"Result type: {type(result)}")
    print(f"Result attributes: {dir(result)}")
    
    # Try to extract useful info
    if hasattr(result, 'result'):
        print(f"\nGenie Result: {result.result}")
    else:
        print(f"\nGenie Result: {result}")
    
except Exception as e:
    print(f"❌ Genie Query FAILED: {e}")
    import traceback
    traceback.print_exc()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 6: Test LangChain Tool Creation

# COMMAND ----------

print("\n" + "="*60)
print("🧪 TEST 5: LangChain Tool Creation")
print("="*60)

try:
    from langchain.tools import tool
    
    @tool
    def test_classify_ticket(ticket_text: str) -> dict:
        """Test classification tool"""
        result = spark.sql(f"""
            SELECT {CATALOG}.{SCHEMA}.ai_classify('{ticket_text}') as classification
        """).collect()[0][0]
        return {"status": "success", "result": result}
    
    print("✅ Tool creation SUCCESS")
    print(f"Tool name: {test_classify_ticket.name}")
    print(f"Tool description: {test_classify_ticket.description}")
    
    # Test invoke
    print("\nTesting tool invocation...")
    result = test_classify_ticket.invoke({"ticket_text": test_ticket})
    print(f"✅ Tool invoke SUCCESS")
    print(f"Result: {result}")
    
except Exception as e:
    print(f"❌ LangChain Tool FAILED: {e}")
    import traceback
    traceback.print_exc()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 7: Test LLM Endpoint

# COMMAND ----------

print("\n" + "="*60)
print("🧪 TEST 6: LLM Endpoint")
print("="*60)

LLM_ENDPOINT = "databricks-meta-llama-3-1-70b-instruct"

try:
    from langchain_community.chat_models import ChatDatabricks
    
    llm = ChatDatabricks(
        endpoint=LLM_ENDPOINT,
        temperature=0.1,
        max_tokens=100
    )
    
    print("✅ LLM initialization SUCCESS")
    print(f"Endpoint: {LLM_ENDPOINT}")
    
    # Test simple invocation
    print("\nTesting LLM invocation...")
    response = llm.invoke("Say 'Hello World' and nothing else.")
    print(f"✅ LLM invoke SUCCESS")
    print(f"Response: {response.content}")
    
except Exception as e:
    print(f"❌ LLM Endpoint FAILED: {e}")
    import traceback
    traceback.print_exc()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 8: Test Simple LangGraph Workflow

# COMMAND ----------

print("\n" + "="*60)
print("🧪 TEST 7: Simple LangGraph Workflow")
print("="*60)

try:
    from langgraph.graph import StateGraph, END
    from typing import TypedDict
    
    # Simple state
    class SimpleState(TypedDict):
        input_text: str
        output_text: str
    
    # Simple node
    def process_node(state: SimpleState) -> SimpleState:
        state['output_text'] = f"Processed: {state['input_text']}"
        return state
    
    # Build graph
    graph = StateGraph(SimpleState)
    graph.add_node("process", process_node)
    graph.set_entry_point("process")
    graph.add_edge("process", END)
    
    workflow = graph.compile()
    
    print("✅ LangGraph creation SUCCESS")
    
    # Test invocation
    print("\nTesting workflow invocation...")
    result = workflow.invoke({"input_text": "test ticket"})
    print(f"✅ LangGraph invoke SUCCESS")
    print(f"Result: {result}")
    
except Exception as e:
    print(f"❌ LangGraph Workflow FAILED: {e}")
    import traceback
    traceback.print_exc()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 9: Test Full Integration (Tools + Agent)

# COMMAND ----------

print("\n" + "="*60)
print("🧪 TEST 8: Full Integration - Tools + Agent")
print("="*60)

try:
    from langchain.tools import tool
    from langchain_community.chat_models import ChatDatabricks
    from langgraph.prebuilt import create_react_agent
    from langchain_core.messages import HumanMessage
    
    # Define a simple tool
    @tool
    def classify_ticket_tool(ticket_text: str) -> dict:
        """Classify a support ticket"""
        result = spark.sql(f"""
            SELECT {CATALOG}.{SCHEMA}.ai_classify('{ticket_text}') as classification
        """).collect()[0][0]
        return {"classification": result}
    
    # Create LLM
    llm = ChatDatabricks(
        endpoint="databricks-meta-llama-3-1-70b-instruct",
        temperature=0.1,
        max_tokens=200
    )
    
    # Create agent
    tools = [classify_ticket_tool]
    agent = create_react_agent(llm, tools)
    
    print("✅ Agent creation SUCCESS")
    print(f"Tools: {[t.name for t in tools]}")
    
    # Test agent
    print("\nTesting agent invocation...")
    test_message = HumanMessage(content=f"Classify this ticket: {test_ticket}")
    result = agent.invoke({"messages": [test_message]})
    
    print(f"✅ Agent invoke SUCCESS")
    print(f"Number of messages: {len(result['messages'])}")
    print(f"\nFinal response:")
    print(result['messages'][-1].content)
    
except Exception as e:
    print(f"❌ Full Integration FAILED: {e}")
    import traceback
    traceback.print_exc()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Summary

# COMMAND ----------

print("\n" + "="*80)
print("📊 TEST SUMMARY")
print("="*80)
print()
print("Tests completed. Review results above:")
print()
print("1. ✅/❌ Package Installation")
print("2. ✅/❌ UC Function - ai_classify")
print("3. ✅/❌ UC Function - ai_extract")
print("4. ✅/❌ Vector Search")
print("5. ✅/❌ Genie Query")
print("6. ✅/❌ LangChain Tool Creation")
print("7. ✅/❌ LLM Endpoint")
print("8. ✅/❌ LangGraph Workflow")
print("9. ✅/❌ Full Integration (Tools + Agent)")
print()
print("="*80)
print()
print("Next Steps:")
print("- If all tests pass: The full LangGraph POC should work")
print("- If any test fails: Fix that component before proceeding")
print()
print("="*80)

# COMMAND ----------


