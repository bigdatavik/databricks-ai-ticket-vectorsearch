# Quick Start Guide - LangGraph Agent Notebook

**Status:** ✅ Debugged and Ready  
**Date:** November 7, 2025

---

## What Was Fixed

I debugged the `notebooks/23_langraph_agent_learning.py` notebook and fixed **6 critical issues** that were causing errors in Databricks:

1. ✅ **Agent creation with system prompt** - Fixed incorrect `bind()` usage
2. ✅ **Missing package dependencies** - Added databricks-langchain and unitycatalog-langchain
3. ✅ **Missing imports** - Added SystemMessage import
4. ✅ **Message type checking** - Made attribute access safe with getattr()
5. ✅ **Tool call handling** - Handle both dict and object formats
6. ✅ **Tool counting logic** - Made it robust and error-proof

**Full details:** See `docs/NOTEBOOK_DEBUG_FIXES.md`

---

## How to Run the Fixed Notebook

### Step 1: Run Validation (Optional but Recommended)

First, run the validation notebook to check your environment:

```
📓 Open: notebooks/00_validate_environment.py
🚀 Run all cells
✅ Verify all tests pass
```

This will check:
- ✅ All packages installed correctly
- ✅ WorkspaceClient works
- ✅ Configuration is correct
- ✅ LLM endpoint exists
- ✅ Agent creation works

**If validation passes, continue to Step 2.**  
**If validation fails, fix the issues highlighted and re-run.**

---

### Step 2: Update Configuration (If Needed)

Open `notebooks/23_langraph_agent_learning.py` and verify these values in Cell 4:

```python
# Configuration (update to match YOUR environment)
CATALOG = "classify_tickets_new_dev"           # ← Your catalog
SCHEMA = "support_ai"                          # ← Your schema
WAREHOUSE_ID = "148ccb90800933a1"              # ← Your warehouse ID
INDEX_NAME = f"{CATALOG}.{SCHEMA}.knowledge_base_index"
GENIE_SPACE_ID = "01f0b91aa91c1b0c8cce6529ea09f0a8"  # ← Your Genie space
LLM_ENDPOINT = "databricks-dbrx-instruct"      # ← Your LLM endpoint
```

**How to find these values:**

```python
from databricks.sdk import WorkspaceClient
w = WorkspaceClient()

# List catalogs
for c in w.catalogs.list():
    print(f"Catalog: {c.name}")

# List warehouses
for wh in w.warehouses.list():
    print(f"Warehouse: {wh.id} - {wh.name}")

# List LLM endpoints
for e in w.serving_endpoints.list():
    if 'llama' in e.name.lower() or 'dbrx' in e.name.lower():
        print(f"Endpoint: {e.name}")
```

---

### Step 3: Run the Main Notebook

```
📓 Open: notebooks/23_langraph_agent_learning.py
🚀 Run all cells sequentially
```

**What to expect:**

#### Cell 1-2: Setup (2-3 minutes)
```
Installing packages... ✅
Restarting Python... ✅
```

#### Cell 3-4: Configuration (5 seconds)
```
✅ WorkspaceClient initialized
📍 Workspace: https://your-workspace.databricks.com
👤 Current user: your.email@company.com
✅ Configuration loaded
```

#### Cells 5-14: Test Individual Tools (3-5 minutes)
```
TEST 1: UC Function - ai_classify ✅
TEST 2: UC Function - ai_extract ✅
TEST 3: Vector Search ✅
TEST 4: Genie Conversation API ✅ (may take 30-60s)
```

**Note:** First query may take 30-60s if warehouse is cold-starting.

#### Cells 15-17: Create LangChain Tools (5 seconds)
```
✅ Tool 1: classify_ticket
✅ Tool 2: extract_metadata
✅ Tool 3: search_knowledge
✅ Tool 4: query_historical
🎉 All 4 LangChain Tools created successfully!
```

#### Cells 18-19: Create Agent (10 seconds)
```
✅ LLM initialized: databricks-dbrx-instruct
✅ LangGraph ReAct Agent created!
🧰 Agent has 4 tools available:
   1. classify_ticket
   2. extract_metadata
   3. search_knowledge
   4. query_historical
```

**If you see this, the main fix worked! 🎉**

#### Cells 20-24: Test Agent (2-3 minutes per test)
```
🧪 TEST 1: SIMPLE QUESTION
🎫 TICKET: How do I reset my password?
🧠 AGENT REASONING TRAIL:
   🤖 Calling tool: classify_ticket ✅
   🤖 Calling tool: search_knowledge ✅
   🤖 FINAL ANSWER: [Complete response]
📊 SUMMARY: Time: 4.23s, Tools used: 2/4
```

The agent should intelligently choose which tools to use!

#### Cells 25-27: Comparison (5-7 minutes)
```
🆚 COMPARISON TEST: Sequential vs Agent
   Sequential: 4 tools, 8.2s
   Agent: 2 tools, 4.1s
   💡 Agent was 50% more efficient!
```

---

## What the Notebook Does

This notebook demonstrates LangGraph ReAct agents by:

1. **Testing 4 tools individually:**
   - UC Function: `ai_classify` (category, priority, team)
   - UC Function: `ai_extract` (metadata, urgency, systems)
   - Vector Search: knowledge base articles
   - Genie API: historical tickets

2. **Wrapping tools as LangChain Tools:**
   - Each tool gets a description
   - LLM uses descriptions to decide when to call tools

3. **Creating a ReAct agent:**
   - Agent receives a ticket
   - Agent decides which tools to call
   - Agent synthesizes results
   - Shows reasoning trail

4. **Comparing approaches:**
   - Sequential: Always calls all 4 tools
   - Agent: Only calls needed tools
   - Measures time, cost, quality

---

## Expected Output Examples

### Simple Question (Agent uses 2 tools):
```
Ticket: "How do I reset my password?"

Agent reasoning:
  1. Classify first → Category: Account, Priority: Low
  2. This is simple, search KB → Found "Password Reset Guide"
  3. Don't need historical tickets or metadata → FINISH

Result: 2 tools used, complete answer
```

### Critical Issue (Agent uses 3-4 tools):
```
Ticket: "Production database timeout affecting all users!"

Agent reasoning:
  1. Classify first → Category: Technical, Priority: Critical
  2. Critical issue, search KB → Found troubleshooting guides
  3. Check historical for patterns → Found similar resolved cases
  4. Synthesize urgent recommendations → FINISH

Result: 3 tools used, comprehensive response
```

---

## Troubleshooting

### Error: "No module named 'databricks_langchain'"

**Fix:**
- Re-run Cell 1 (pip install)
- Re-run Cell 2 (restart Python)
- Re-run Cell 3 (imports)

### Error: "Warehouse not found"

**Fix:**
- Get correct warehouse ID:
  ```python
  from databricks.sdk import WorkspaceClient
  w = WorkspaceClient()
  for wh in w.warehouses.list():
      print(f"{wh.id} - {wh.name}")
  ```
- Update `WAREHOUSE_ID` in Cell 4

### Error: "LLM endpoint not found"

**Fix:**
- List available endpoints:
  ```python
  for e in w.serving_endpoints.list():
      print(e.name)
  ```
- Update `LLM_ENDPOINT` in Cell 4 to a valid endpoint

### Error: "UC Function not found"

**Fix:**
- Verify functions exist:
  ```python
  for f in w.functions.list(catalog_name=CATALOG, schema_name=SCHEMA):
      print(f.name)
  ```
- Should see: `ai_classify`, `ai_extract`
- If missing, run the function creation notebook first

### Agent creates but fails to invoke

**Fix:** This should be fixed now! But if it happens:
- Check `docs/NOTEBOOK_DEBUG_FIXES.md` section on agent creation
- Verify you have the latest notebook version
- Check LangGraph version: `%pip show langgraph`

---

## Success Criteria

You'll know it worked when you see:

✅ All 4 tools test successfully individually  
✅ Agent creation completes without errors  
✅ Agent makes intelligent tool choices (doesn't always use all 4)  
✅ Agent shows reasoning trail  
✅ Comparison shows agent is more efficient than sequential

---

## Next Steps After Success

Once the notebook runs successfully:

1. **Extract to dashboard module:**
   - Move agent logic to `dashboard/langraph_agent.py`
   
2. **Add dashboard tab:**
   - Create new tab: "🧪 LangGraph Agent (Experimental)"
   
3. **Test in production:**
   - Compare with existing sequential pipeline
   
4. **Document learnings:**
   - Update `MY_ENVIRONMENT_AI_TICKET_LESSONS.md`

---

## Files Reference

| File | Purpose |
|------|---------|
| `notebooks/00_validate_environment.py` | Validate setup before running agent |
| `notebooks/23_langraph_agent_learning.py` | Main agent learning notebook (FIXED) |
| `docs/NOTEBOOK_DEBUG_FIXES.md` | Detailed list of all fixes |
| `docs/LANGRAPH_AGENT_PLAN.md` | Original implementation plan |
| `docs/LANGRAPH_ARCHITECTURE.md` | Architecture explanation |

---

## Questions?

If you encounter any issues not covered here:

1. Check `docs/NOTEBOOK_DEBUG_FIXES.md` for detailed fixes
2. Run `notebooks/00_validate_environment.py` to diagnose
3. Verify configuration values match your environment
4. Check error messages against troubleshooting section above

---

**Ready to run!** 🚀

Start with the validation notebook, then run the main agent notebook. The fixes are in place and it should work now.

