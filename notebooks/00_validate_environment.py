# Databricks notebook source
# MAGIC %md
# MAGIC # Environment Validation for LangGraph Agent
# MAGIC 
# MAGIC **Purpose:** Quick validation that all dependencies and configurations are correct before running the main agent notebook
# MAGIC 
# MAGIC **Why This Notebook Exists:**
# MAGIC - Catches errors early (before spending time on main notebook)
# MAGIC - Tests each component individually (easier to debug)
# MAGIC - Validates configuration (IDs, endpoints, permissions)
# MAGIC - Tests the critical agent creation pattern (v1.0+ compatibility)
# MAGIC 
# MAGIC **What Gets Validated:**
# MAGIC 1. Package imports (langchain, langgraph, databricks-sdk, etc.)
# MAGIC 2. WorkspaceClient authentication
# MAGIC 3. Configuration (catalog, schema, warehouse, endpoints)
# MAGIC 4. LLM endpoint availability and basic invocation
# MAGIC 5. **Agent creation with LangGraph v1.0+ pattern** (most critical!)
# MAGIC 
# MAGIC Run this notebook first to catch any issues early!

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 1: Install Dependencies
# MAGIC 
# MAGIC **Version Requirements Explained:**
# MAGIC - `langgraph>=1.0.0` - Minimum v1.0 (removed `state_modifier`, changed API)
# MAGIC - `langchain>=0.3.0` - Minimum v0.3 (improved tool calling, agent framework)
# MAGIC - Version pins ensure consistent behavior across environments
# MAGIC 
# MAGIC **Why These Specific Versions Matter:**
# MAGIC - LangGraph v1.0 deprecated `state_modifier` in `create_react_agent()`
# MAGIC - We use manual SystemMessage injection instead (v1.0+ pattern)
# MAGIC - Older versions (<1.0) would work with different code patterns
# MAGIC 
# MAGIC **What Happens If Versions Don't Match:**
# MAGIC - v0.2: Would need `state_modifier` parameter (doesn't exist in our code)
# MAGIC - v1.0+: Our current pattern works (SystemMessage in messages array)

# COMMAND ----------

# MAGIC %pip install langgraph>=1.0.0 langchain>=0.3.0 langchain-core>=0.3.0 langchain-community>=0.3.0 databricks-langchain unitycatalog-langchain[databricks] backoff databricks-sdk mlflow databricks-vectorsearch --quiet

# COMMAND ----------

dbutils.library.restartPython()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 2: Test Imports

# COMMAND ----------

print("Testing imports...")
import_results = []

# Test 1: Databricks SDK
try:
    from databricks.sdk import WorkspaceClient
    import_results.append(("✅", "databricks.sdk", "OK"))
except Exception as e:
    import_results.append(("❌", "databricks.sdk", str(e)))

# Test 2: Databricks LangChain
try:
    from databricks_langchain import ChatDatabricks
    import_results.append(("✅", "databricks_langchain", "OK"))
except Exception as e:
    import_results.append(("❌", "databricks_langchain", str(e)))

# Test 3: Vector Search
try:
    from databricks.vector_search.client import VectorSearchClient
    import_results.append(("✅", "databricks.vector_search", "OK"))
except Exception as e:
    import_results.append(("❌", "databricks.vector_search", str(e)))

# Test 4: LangChain Core
try:
    from langchain_core.tools import Tool
    from langchain_core.messages import SystemMessage
    import_results.append(("✅", "langchain_core", "OK"))
except Exception as e:
    import_results.append(("❌", "langchain_core", str(e)))

# Test 5: LangGraph
try:
    from langgraph.prebuilt import create_react_agent
    import_results.append(("✅", "langgraph.prebuilt", "OK"))
except Exception as e:
    import_results.append(("❌", "langgraph.prebuilt", str(e)))

# Test 6: Pydantic
try:
    from pydantic import BaseModel, Field
    import_results.append(("✅", "pydantic", "OK"))
except Exception as e:
    import_results.append(("❌", "pydantic", str(e)))

# Test 7: Standard libraries
try:
    import os
    import json
    import time
    import backoff
    import_results.append(("✅", "standard libraries", "OK"))
except Exception as e:
    import_results.append(("❌", "standard libraries", str(e)))

# Display results
print("\n" + "=" * 70)
print("IMPORT TEST RESULTS")
print("=" * 70)
for status, package, message in import_results:
    print(f"{status} {package:.<50} {message}")
print("=" * 70)

# Check if all passed
all_passed = all(status == "✅" for status, _, _ in import_results)
if all_passed:
    print("\n✅ ALL IMPORTS SUCCESSFUL! Environment is ready.")
else:
    print("\n❌ SOME IMPORTS FAILED! Check errors above and fix before continuing.")
    print("   Common fix: Restart the Python environment after installing packages")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 3: Test WorkspaceClient

# COMMAND ----------

print("Testing WorkspaceClient...")
try:
    from databricks.sdk import WorkspaceClient
    w = WorkspaceClient()
    
    current_user = w.current_user.me()
    print(f"✅ WorkspaceClient initialized successfully")
    print(f"   📍 Workspace: {w.config.host}")
    print(f"   👤 Current user: {current_user.user_name}")
    
except Exception as e:
    print(f"❌ WorkspaceClient failed: {str(e)}")
    print("   Check your authentication settings")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 4: Validate Configuration

# COMMAND ----------

print("Validating configuration...")

# Configuration (update these to match your environment)
CATALOG = "classify_tickets_new_dev"
SCHEMA = "support_ai"
WAREHOUSE_ID = "148ccb90800933a1"
INDEX_NAME = f"{CATALOG}.{SCHEMA}.knowledge_base_index"
GENIE_SPACE_ID = "01f0b91aa91c1b0c8cce6529ea09f0a8"
LLM_ENDPOINT = "databricks-meta-llama-3-1-8b-instruct"

config_checks = []

# Check 1: Catalog exists
try:
    from databricks.sdk import WorkspaceClient
    w = WorkspaceClient()
    catalogs = [c.name for c in w.catalogs.list()]
    if CATALOG in catalogs:
        config_checks.append(("✅", "Catalog", CATALOG, "Exists"))
    else:
        config_checks.append(("⚠️", "Catalog", CATALOG, f"Not found. Available: {catalogs[:3]}..."))
except Exception as e:
    config_checks.append(("❌", "Catalog", CATALOG, str(e)))

# Check 2: Schema exists
try:
    schemas = [s.name for s in w.schemas.list(catalog_name=CATALOG)]
    if SCHEMA in schemas:
        config_checks.append(("✅", "Schema", SCHEMA, "Exists"))
    else:
        config_checks.append(("⚠️", "Schema", SCHEMA, f"Not found. Available: {schemas}"))
except Exception as e:
    config_checks.append(("❌", "Schema", SCHEMA, str(e)))

# Check 3: Warehouse exists
try:
    warehouse = w.warehouses.get(WAREHOUSE_ID)
    config_checks.append(("✅", "Warehouse", WAREHOUSE_ID, f"Found: {warehouse.name}"))
except Exception as e:
    config_checks.append(("⚠️", "Warehouse", WAREHOUSE_ID, "Not found or no access"))

# Check 4: UC Functions exist
try:
    from databricks.sdk.service.catalog import FunctionsAPI
    functions = []
    for func in w.functions.list(catalog_name=CATALOG, schema_name=SCHEMA):
        functions.append(func.name)
    
    required_functions = ["ai_classify", "ai_extract"]
    missing = [f for f in required_functions if f not in functions]
    
    if not missing:
        config_checks.append(("✅", "UC Functions", "ai_classify, ai_extract", "Both found"))
    else:
        config_checks.append(("⚠️", "UC Functions", f"Missing: {missing}", f"Available: {functions}"))
except Exception as e:
    config_checks.append(("❌", "UC Functions", "Check failed", str(e)))

# Check 5: LLM Endpoint exists
try:
    endpoints = [e.name for e in w.serving_endpoints.list()]
    if LLM_ENDPOINT in endpoints:
        config_checks.append(("✅", "LLM Endpoint", LLM_ENDPOINT, "Found"))
    else:
        # Try to find similar endpoints
        llm_endpoints = [e for e in endpoints if 'llama' in e.lower() or 'dbrx' in e.lower()]
        config_checks.append(("⚠️", "LLM Endpoint", LLM_ENDPOINT, f"Not found. Try: {llm_endpoints[:3]}"))
except Exception as e:
    config_checks.append(("❌", "LLM Endpoint", "Check failed", str(e)))

# Display results
print("\n" + "=" * 100)
print("CONFIGURATION VALIDATION")
print("=" * 100)
for status, check, value, message in config_checks:
    print(f"{status} {check:.<20} {value:.<40} {message}")
print("=" * 100)

# Summary
success = sum(1 for s, _, _, _ in config_checks if s == "✅")
warning = sum(1 for s, _, _, _ in config_checks if s == "⚠️")
error = sum(1 for s, _, _, _ in config_checks if s == "❌")

print(f"\n📊 Summary: {success} passed, {warning} warnings, {error} errors")

if error == 0 and warning == 0:
    print("✅ Configuration is perfect! Ready to run the agent notebook.")
elif error == 0:
    print("⚠️ Configuration has warnings. The notebook might work but verify the warnings.")
else:
    print("❌ Configuration has errors. Fix these before running the agent notebook.")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 5: Quick LLM Test

# COMMAND ----------

print("Testing LLM endpoint...")
try:
    from databricks_langchain import ChatDatabricks
    
    llm = ChatDatabricks(
        endpoint=LLM_ENDPOINT,
        temperature=0.3,
        max_tokens=100
    )
    
    # Simple test
    from langchain_core.messages import HumanMessage
    response = llm.invoke([HumanMessage(content="Say 'hello' if you can hear me")])
    
    print(f"✅ LLM endpoint working!")
    print(f"   Response: {response.content[:100]}")
    
except Exception as e:
    print(f"❌ LLM test failed: {str(e)}")
    print("   Try a different endpoint name or check permissions")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 6: Test Agent Creation
# MAGIC 
# MAGIC **This is the CRITICAL TEST!**
# MAGIC 
# MAGIC **What We're Testing:**
# MAGIC - Agent creation with LangGraph v1.0+ pattern (NO state_modifier)
# MAGIC - Manual SystemMessage injection at invocation time
# MAGIC - Tool registration and basic agent execution
# MAGIC 
# MAGIC **Why This Test Matters:**
# MAGIC - If this fails, the main notebook won't work
# MAGIC - Tests the exact pattern used in `23_langraph_agent_learning.py`
# MAGIC - Validates LangGraph v1.0+ compatibility
# MAGIC 
# MAGIC **What Changed from LangGraph v0.2:**
# MAGIC - v0.2: Used `state_modifier=function` parameter
# MAGIC - v1.0+: Pass SystemMessage in messages array (our approach)
# MAGIC 
# MAGIC **Expected Output:**
# MAGIC - ✅ Agent creation successful
# MAGIC - ✅ Agent invoked successfully
# MAGIC - ❌ NO TypeError about unexpected keyword argument 'state_modifier'

# COMMAND ----------

print("Testing ReAct agent creation...")
try:
    # Import required components
    from databricks_langchain import ChatDatabricks
    from langchain_core.tools import Tool
    from langchain_core.messages import SystemMessage  # Critical for v1.0+
    from langgraph.prebuilt import create_react_agent
    from pydantic import BaseModel, Field
    
    # Create a simple test tool
    # Tools need: name, description, function, args_schema
    class TestInput(BaseModel):
        text: str = Field(description="Test input")
    
    def test_tool(text: str) -> str:
        return f"Received: {text}"
    
    test_tool_obj = Tool(
        name="test_tool",
        description="A simple test tool",
        func=test_tool,
        args_schema=TestInput
    )
    
    # Create LLM - same as main notebook
    llm = ChatDatabricks(
        endpoint=LLM_ENDPOINT,
        temperature=0.3,
        max_tokens=100
    )
    
    # CRITICAL: Create agent WITHOUT state_modifier (v1.0+ pattern)
    # This is the main fix that made the agent work!
    # Old way (v0.2): agent = create_react_agent(model, tools, state_modifier=func)
    # New way (v1.0+): agent = create_react_agent(model, tools) - no state_modifier!
    agent = create_react_agent(
        model=llm,
        tools=[test_tool_obj]
        # NO state_modifier parameter! That's the key difference.
    )
    
    print("✅ Agent creation successful!")
    print("   Agent type:", type(agent).__name__)
    print("   Tools count: 1")
    
    # Try a simple invocation
    # CRITICAL: Pass SystemMessage as FIRST message
    # This is how we inject system prompt in v1.0+ (replaces state_modifier)
    print("\n   Testing agent invocation...")
    result = agent.invoke({
        "messages": [
            # System message goes first - sets agent behavior
            SystemMessage(content="You are a test assistant"),
            # Then user message - the actual task
            ("user", "Just say hello")
        ]
    })
    
    print(f"   ✅ Agent invoked successfully!")
    print(f"   Messages in response: {len(result['messages'])}")
    
except Exception as e:
    print(f"❌ Agent test failed: {str(e)}")
    import traceback
    traceback.print_exc()
    print("\n   This is the critical test - if this fails, the main notebook won't work")
    print("   Common issue: state_modifier error = Need LangGraph v1.0+ pattern")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Final Summary

# COMMAND ----------

print("""
╔════════════════════════════════════════════════════════════════╗
║                                                                ║
║  ENVIRONMENT VALIDATION COMPLETE                               ║
║                                                                ║
║  If all tests passed above, you are ready to run:             ║
║  📓 notebooks/23_langraph_agent_learning.py                    ║
║                                                                ║
║  If any tests failed:                                          ║
║  1. Review the error messages above                            ║
║  2. Fix configuration in Step 4                                ║
║  3. Check docs/NOTEBOOK_DEBUG_FIXES.md for solutions           ║
║  4. Re-run this validation notebook                            ║
║                                                                ║
╚════════════════════════════════════════════════════════════════╝
""")

