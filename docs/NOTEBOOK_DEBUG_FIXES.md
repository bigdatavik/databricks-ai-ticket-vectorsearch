# Notebook Debug Fixes - 23_langraph_agent_learning.py

**Date:** November 7, 2025  
**Notebook:** `notebooks/23_langraph_agent_learning.py`  
**Status:** Fixed and Ready for Testing

---

## Summary

Fixed multiple compatibility issues in the LangGraph agent learning notebook that were causing errors when running in Databricks. The main issues were related to incorrect agent creation patterns, missing imports, and incomplete package dependencies.

---

## Issues Fixed

### 1. ✅ Agent Creation with System Prompt (CRITICAL FIX)

**Problem:**
```python
# WRONG: bind(system=...) is not a valid method
llm_with_tools = llm.bind_tools(tools_list).bind(system=system_prompt)

agent = create_react_agent(
    model=llm_with_tools,
    tools=tools_list
)
```

**Fix:**
```python
# CORRECT: Use state_modifier parameter to inject system message
from langchain_core.messages import SystemMessage

def add_system_message(state):
    """Add system message to the state"""
    return [SystemMessage(content=system_prompt)] + state["messages"]

agent = create_react_agent(
    model=llm,
    tools=tools_list,
    state_modifier=add_system_message
)
```

**Why it failed:** 
- `bind(system=...)` is not a standard LangChain method
- The `create_react_agent` expects either no system prompt or uses `state_modifier` to inject system messages
- This was causing the agent to fail at initialization or during invocation

---

### 2. ✅ Missing Package Dependencies

**Problem:**
```python
# Missing required packages
%pip install langgraph langchain langchain-core databricks-langchain ...
```

**Fix:**
```python
# Added all required packages including databricks-langchain and unitycatalog-langchain
%pip install langgraph langchain langchain-core langchain-community databricks-langchain unitycatalog-langchain[databricks] backoff databricks-sdk mlflow databricks-vectorsearch --quiet
```

**Why it failed:**
- `databricks-langchain` was initially missing from the pip install
- `unitycatalog-langchain[databricks]` is needed for proper Unity Catalog integration
- `langchain-community` is required for additional tool support

---

### 3. ✅ Missing Import Statement

**Problem:**
```python
# SystemMessage was used but not imported
def add_system_message(state):
    return [SystemMessage(content=system_prompt)] + state["messages"]
```

**Fix:**
```python
# Added import at the top of the file
from langchain_core.messages import SystemMessage
```

**Why it failed:**
- NameError would occur when trying to use SystemMessage without importing it

---

### 4. ✅ Message Type Checking in run_agent_test()

**Problem:**
```python
# Direct attribute access could fail
for message in result['messages']:
    if message.type == "human":  # Could raise AttributeError
        print(message.content)  # Could be None
    if hasattr(message, 'name') and message.name:  # Fragile check
```

**Fix:**
```python
# Use getattr() with defaults for safe attribute access
for message in result['messages']:
    msg_type = getattr(message, 'type', None)
    
    if msg_type == "human":
        content = getattr(message, 'content', '')
        print(f"   {str(content)[:200]}...")
    elif msg_type == "tool":
        tool_name = getattr(message, 'name', 'unknown')
        content = getattr(message, 'content', None)
```

**Why it failed:**
- Direct attribute access could raise AttributeError if attributes don't exist
- Tool calls might be dicts or objects, needed flexible handling
- Content could be None, causing slicing errors

---

### 5. ✅ Tool Call Attribute Access

**Problem:**
```python
# Assuming tool_call is always a dict
for tool_call in message.tool_calls:
    print(f"Tool: {tool_call['name']}")  # Could fail if tool_call is object
```

**Fix:**
```python
# Handle both dict and object representations
for tool_call in tool_calls:
    tool_name = tool_call.get('name') if isinstance(tool_call, dict) else getattr(tool_call, 'name', 'unknown')
    tool_args = tool_call.get('args') if isinstance(tool_call, dict) else getattr(tool_call, 'args', {})
    print(f"   🔧 Calling tool: {tool_name}")
    print(f"   📥 Input: {str(tool_args)[:150]}...")
```

**Why it failed:**
- LangChain can represent tool calls as either dicts or objects
- Accessing with dict notation on objects would raise TypeError
- Needs to handle both formats dynamically

---

### 6. ✅ Tool Counting Logic

**Problem:**
```python
# Fragile tool counting
tool_messages = [m for m in result['messages'] if hasattr(m, 'name') and m.name]
tools_used = list(set([m.name for m in tool_messages if m.name]))
```

**Fix:**
```python
# Robust tool counting using type checking
tool_messages = [m for m in result['messages'] if getattr(m, 'type', None) == 'tool']
tools_used = list(set([getattr(m, 'name', None) for m in tool_messages if getattr(m, 'name', None)]))
```

**Why it failed:**
- Checking only for 'name' attribute could match non-tool messages
- Better to explicitly check for 'tool' message type
- Safe attribute access prevents AttributeErrors

---

## Testing Checklist

Before running the notebook in Databricks, verify:

- [ ] **Cell 1:** Package installation completes without errors
- [ ] **Cell 2:** Python restart completes
- [ ] **Cell 3:** All imports succeed (WorkspaceClient, ChatDatabricks, etc.)
- [ ] **Cell 4:** Configuration variables are correct for your environment:
  - `CATALOG` = your catalog name
  - `SCHEMA` = your schema name
  - `WAREHOUSE_ID` = valid warehouse ID
  - `INDEX_NAME` = existing vector search index
  - `GENIE_SPACE_ID` = valid Genie space ID
  - `LLM_ENDPOINT` = valid model endpoint
- [ ] **Cells 5-14:** Individual tool tests pass (UC Functions, Vector Search, Genie)
- [ ] **Cells 15-17:** LangChain tools creation succeeds
- [ ] **Cells 18-19:** Agent creation completes without errors
- [ ] **Cells 20-24:** Agent tests run successfully
- [ ] **Cells 25-27:** Comparison tests complete

---

## Configuration Notes

### Model Endpoint

The notebook uses:
```python
LLM_ENDPOINT = "databricks-dbrx-instruct"
```

If this endpoint doesn't exist in your workspace, consider alternatives:
- `databricks-meta-llama-3-1-70b-instruct`
- `databricks-meta-llama-3-3-70b-instruct`
- `databricks-dbrx-instruct` (if available)

Check available endpoints in your workspace:
```python
from databricks.sdk import WorkspaceClient
w = WorkspaceClient()
endpoints = w.serving_endpoints.list()
for e in endpoints:
    print(e.name)
```

### Warehouse Startup

Note: The first query may take 30-60 seconds if the SQL warehouse is cold-starting. This is normal and will only happen on the first execution.

---

## Expected Behavior

### Successful Agent Creation Output:
```
✅ LLM initialized: databricks-dbrx-instruct
✅ LangGraph ReAct Agent created!
🧰 Agent has 4 tools available:
   1. classify_ticket
   2. extract_metadata
   3. search_knowledge
   4. query_historical

🎯 Agent will decide which tools to use based on the ticket!
```

### Successful Agent Test Output:
```
🎫 TICKET: How do I reset my password?
================================================================================

🧠 AGENT REASONING TRAIL:
--------------------------------------------------------------------------------

👤 USER:
   Analyze this support ticket and provide recommendations: How do I reset my password?

🤖 AGENT THOUGHT & ACTION:
   I need to understand the ticket category first
   🔧 Calling tool: classify_ticket
   📥 Input: {'ticket_text': 'How do I reset my password?'}

📤 TOOL RESULT (classify_ticket):
   {"category": "Account", "priority": "Low", ...}

🤖 AGENT THOUGHT & ACTION:
   This is a simple account question. Let me search the knowledge base
   🔧 Calling tool: search_knowledge
   📥 Input: {'query': 'password reset guide'}

📤 TOOL RESULT (search_knowledge):
   [{"title": "Password Reset Guide", ...}]

🤖 AGENT FINAL ANSWER:
   Based on the classification and knowledge base search...

================================================================================
📊 SUMMARY:
   ⏱️  Time: 4.23s
   🧰 Tools used: 2/4 - classify_ticket, search_knowledge
================================================================================
```

---

## Common Errors and Solutions

### Error: "No module named 'databricks_langchain'"
**Solution:** Make sure Cell 1 (pip install) ran successfully and Cell 2 (restart Python) completed

### Error: "ImportError: cannot import name 'SystemMessage'"
**Solution:** This should be fixed now - SystemMessage is imported at the top

### Error: "'NoneType' object has no attribute 'bind_tools'"
**Solution:** This should be fixed now - we're not using bind() incorrectly anymore

### Error: "create_react_agent() got an unexpected keyword argument 'state_modifier'"
**Solution:** If this occurs, your langgraph version might be too old or too new. Try:
```python
%pip install langgraph==0.2.0 --upgrade
```

### Error: Tool calls failing with AttributeError
**Solution:** This should be fixed now - we use getattr() for safe attribute access

---

## Architecture Verification

To verify the agent is working correctly, check that:

1. **Agent makes intelligent decisions** - doesn't always call all 4 tools
2. **System prompt is active** - agent explains its reasoning
3. **Tools execute successfully** - each tool returns valid JSON
4. **Messages flow correctly** - agent → tool → agent → finish
5. **Comparison works** - can compare sequential vs agent approaches

---

## Next Steps

After verifying the notebook works:

1. **Phase 2:** Extract agent logic to `dashboard/langraph_agent.py`
2. **Phase 3:** Add 5th tab to dashboard for agent interface
3. **Phase 4:** Compare agent vs sequential approaches in production
4. **Phase 5:** Document learnings and update architecture docs

---

## Files Modified

- `notebooks/23_langraph_agent_learning.py` - Main notebook with all fixes

---

## References

- **LangGraph Documentation:** https://python.langchain.com/docs/langgraph
- **Databricks LangChain Integration:** https://docs.databricks.com/generative-ai/agent-framework/langchain-uc-integration.html
- **Create ReAct Agent:** https://python.langchain.com/docs/langgraph/prebuilt/create_react_agent
- **Original Plan:** `docs/LANGRAPH_AGENT_PLAN.md`

---

**Status:** ✅ Ready for testing in Databricks

**Last Updated:** November 7, 2025

