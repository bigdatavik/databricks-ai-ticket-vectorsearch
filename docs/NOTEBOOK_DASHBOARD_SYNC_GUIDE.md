# Notebook ↔ Dashboard Synchronization Guide

This document tracks critical changes that need to be synchronized between notebooks and the dashboard to maintain consistency across the project.

---

## 🎯 Purpose

The project has **two main code paths**:
1. **Notebooks** (`notebooks/`) - For learning, testing, and experimentation in Databricks
2. **Dashboard** (`dashboard/app_databricks.py`) - Production Streamlit application

**CRITICAL:** Changes in one should be reflected in the other to maintain consistency!

---

## 📋 Synchronization Checklist

### ✅ Recently Synchronized (Nov 11, 2025)

| Change | Notebook Status | Dashboard Status | Notes |
|--------|----------------|------------------|-------|
| **LLM Endpoint → Claude Sonnet 4** | ✅ Updated | ✅ Updated | Lines 122-140 (23), 165-168 (00) |
| **Tool Wrapper Error Handling** | ✅ Updated | ✅ Updated | All 4 wrappers now have try/except |
| **Pure Function Documentation** | ✅ Updated | ✅ Updated | Added warnings about Streamlit calls |
| **NoSessionContext Fix** | ✅ Updated | ✅ Updated | Removed all st.* calls from tools |

---

## 🔧 Critical Code Sections to Keep in Sync

### 1. **LLM Endpoint Configuration**

**Why it matters:** Wrong model = BAD_REQUEST errors (XML vs JSON format)

**Notebook Location:**
- `notebooks/23_langraph_agent_learning.py` - Lines 122-140
- `notebooks/00_validate_environment.py` - Lines 165-168

**Dashboard Location:**
- `dashboard/app_databricks.py` - Lines 485-493

**Current Value:**
```python
LLM_ENDPOINT = "databricks-claude-sonnet-4"  # ✅ PRODUCTION CHOICE
```

**When to Update:**
- New models become available
- Current model deprecated
- Testing different models
- Performance/cost optimization

**How to Update:**
1. Test new model endpoint in notebook first
2. Verify tool calling works (no BAD_REQUEST errors)
3. Update all 3 files
4. Commit with clear message
5. Deploy notebooks and dashboard

---

### 2. **Tool Wrapper Functions**

**Why it matters:** Pure functions required for LangGraph (no Streamlit calls)

**Notebook Location:**
- `notebooks/23_langraph_agent_learning.py` - Lines 607-677

**Dashboard Location:**
- `dashboard/app_databricks.py` - Lines 389-447

**Current Pattern:**
```python
def classify_ticket_wrapper(ticket_text: str) -> str:
    """
    IMPORTANT: Pure function - no Streamlit calls!
    ❌ NO st.info(), st.error(), st.warning()
    ✅ Return JSON string only
    """
    result = call_uc_function("ai_classify", ticket_text, show_debug=False)
    return json.dumps(result, indent=2) if result else json.dumps({"error": "..."})
```

**When to Update:**
- Adding new tools
- Changing tool logic
- Improving error handling
- Fixing bugs in tool execution

**How to Update:**
1. Develop/test in notebook first
2. Ensure no Streamlit calls (st.* functions)
3. Add comprehensive error handling
4. Copy exact logic to dashboard
5. Test in both environments

---

### 3. **Tool Descriptions (Prompts)**

**Why it matters:** Affects agent's ability to choose correct tools

**Notebook Location:**
- `notebooks/23_langraph_agent_learning.py` - Lines 621-682

**Dashboard Location:**
- `dashboard/app_databricks.py` - Lines 426-478

**Current Format:**
```python
Tool(
    name="classify_ticket",
    description="Classifies a support ticket into category, priority, and routing team. Use this FIRST to understand the ticket type. Returns JSON with category, priority, team, confidence.",
    func=classify_ticket_wrapper,
    args_schema=ClassifyTicketInput
)
```

**When to Update:**
- Agent not using tools correctly
- Adding strategic guidance
- Clarifying tool purpose
- Improving tool selection

**How to Update:**
1. Test description changes in notebook
2. Observe agent behavior
3. Refine until optimal
4. Copy to dashboard
5. Monitor agent performance

---

### 4. **Pydantic Schemas**

**Why it matters:** Defines tool input structure for LLM

**Notebook Location:**
- `notebooks/23_langraph_agent_learning.py` - Lines 594-604

**Dashboard Location:**
- `dashboard/app_databricks.py` - Lines 376-386

**Current Format:**
```python
class ClassifyTicketInput(BaseModel):
    ticket_text: str = Field(description="The support ticket text to classify")
```

**When to Update:**
- Adding new tool parameters
- Changing required fields
- Improving descriptions
- Adding validation

**How to Update:**
1. Update schema in notebook
2. Test with agent
3. Ensure LLM provides correct args
4. Copy to dashboard
5. Verify no schema errors

---

### 5. **System Prompt**

**Why it matters:** Guides agent's overall strategy and tool usage

**Notebook Location:**
- `notebooks/23_langraph_agent_learning.py` - Lines 746-770

**Dashboard Location:**
- `dashboard/app_databricks.py` - Lines 1432-1449

**Current Pattern:**
```python
system_prompt = """
You are an expert support ticket analyst with access to specialized tools.

YOUR TOOLS:
1. classify_ticket: Determine category, priority, routing team
2. extract_metadata: Extract technical details and impact
3. search_knowledge: Find relevant documentation
4. query_historical: Find similar past tickets

YOUR STRATEGY:
1. ALWAYS start with classify_ticket
2. Then extract_metadata for detailed analysis
3. Use search_knowledge to find solutions
4. Use query_historical for complex issues
5. Provide comprehensive analysis

IMPORTANT:
- Use tools in logical order
- Combine results for holistic view
- Be thorough but efficient
"""
```

**When to Update:**
- Agent using wrong strategy
- Need to emphasize certain behaviors
- Adding new tools
- Improving output quality

**How to Update:**
1. Experiment in notebook
2. Observe agent reasoning
3. Refine prompt iteratively
4. Copy best version to dashboard
5. Monitor production performance

---

### 6. **Agent Creation Pattern (LangGraph v1.0+)**

**Why it matters:** API compatibility and correct usage

**Notebook Location:**
- `notebooks/23_langraph_agent_learning.py` - Lines 700-714

**Dashboard Location:**
- `dashboard/app_databricks.py` - Lines 481-506

**Current Pattern:**
```python
# v1.0+ Pattern - NO state_modifier
agent = create_react_agent(
    model=llm,
    tools=tools_list
    # ✅ No state_modifier parameter!
)

# Inject SystemMessage at invocation time
result = agent.invoke({
    "messages": [
        SystemMessage(content=system_prompt),  # ✅ Manual injection
        ("user", f"Analyze this ticket:\n\n{ticket_text}")
    ]
})
```

**When to Update:**
- LangGraph version upgrade
- API changes
- New features needed
- Bug fixes

**How to Update:**
1. Check LangGraph release notes
2. Update notebook first
3. Test thoroughly
4. Update dashboard
5. Document changes in MY_ENVIRONMENT_AI_TICKET_LESSONS.md

---

## 🚨 Common Pitfalls

### Pitfall #1: Streamlit Calls in Tool Wrappers

**Problem:**
```python
def search_knowledge_wrapper(query: str) -> str:
    st.info(f"Searching: {query}")  # ❌ BREAKS IN NOTEBOOK!
    results = search_knowledge_base(query)
    return json.dumps(results)
```

**Solution:**
```python
def search_knowledge_wrapper(query: str) -> str:
    # No Streamlit calls - pure function
    results = search_knowledge_base(query)
    return json.dumps(results) if results else json.dumps([])
```

**Why:** LangGraph tools run in background threads without Streamlit session context

---

### Pitfall #2: Different Error Handling

**Problem:**
- Dashboard has try/except
- Notebook returns None on error
- Inconsistent agent behavior

**Solution:**
```python
# BOTH should have:
try:
    result = do_something()
    return json.dumps(result) if result else json.dumps({"error": "..."})
except Exception as e:
    return json.dumps({"error": f"Failed: {str(e)}"})
```

---

### Pitfall #3: Model Mismatch

**Problem:**
- Notebook uses Claude Sonnet 4
- Dashboard uses Meta Llama 3.1 8B
- Different success rates!

**Solution:**
- Always use same model endpoint
- Document in both places
- Cross-reference with comments

---

### Pitfall #4: Outdated Reference Docs

**Problem:**
- `docs/REFERENCE_*.py` files become stale
- New developers copy old code

**Solution:**
```bash
# After making changes, update reference docs:
cp notebooks/23_langraph_agent_learning.py docs/REFERENCE_23_langraph_agent_learning.py
cp notebooks/00_validate_environment.py docs/REFERENCE_00_validate_environment.py
git add docs/
git commit -m "📚 Update reference notebooks"
```

---

## 📝 Update Workflow

### When You Change the Notebooks:

1. **Make changes** in notebook
2. **Test thoroughly** in Databricks
3. **Identify sync points** (use checklist above)
4. **Update dashboard** (`dashboard/app_databricks.py`)
5. **Update reference docs** (copy to `docs/`)
6. **Update this guide** if new sync point
7. **Commit all changes** together
8. **Deploy both** notebooks and dashboard

### When You Change the Dashboard:

1. **Make changes** in dashboard
2. **Test in Streamlit** (local or Databricks Apps)
3. **Identify sync points** (use checklist above)
4. **Update notebooks** (both 00 and 23)
5. **Update reference docs** (copy to `docs/`)
6. **Update this guide** if new sync point
7. **Commit all changes** together
8. **Deploy both** notebooks and dashboard

---

## 🔍 How to Check for Drift

Run these commands periodically to check for differences:

```bash
# Compare LLM endpoint
grep "LLM_ENDPOINT.*=" notebooks/23_langraph_agent_learning.py
grep "agent_endpoint.*=" dashboard/app_databricks.py

# Compare tool wrapper signatures
grep "def.*_wrapper(" notebooks/23_langraph_agent_learning.py
grep "def.*_wrapper(" dashboard/app_databricks.py

# Compare tool descriptions
grep "description=" notebooks/23_langraph_agent_learning.py | head -4
grep "description=" dashboard/app_databricks.py | grep -A1 "Tool("
```

---

## 📊 Synchronization History

| Date | Change | Reason | Files Updated |
|------|--------|--------|---------------|
| 2025-11-11 | Claude Sonnet 4 | BAD_REQUEST errors with Llama | All 3 files + docs |
| 2025-11-11 | Tool error handling | NoSessionContext fix | All wrappers |
| 2025-11-11 | Pure function docs | Prevent future errors | All tool wrappers |

---

## 🎓 Key Lessons

### Lesson 1: Test in Notebooks First
- Notebooks are faster to iterate
- Easier to debug
- Less deployment overhead
- Then promote to dashboard

### Lesson 2: Document Sync Points
- Not everything needs sync
- Focus on critical sections
- Document WHY things must match
- Update this guide when patterns change

### Lesson 3: Automate Where Possible
- Copy reference docs automatically
- Use grep/diff to check drift
- Consider pre-commit hooks
- CI/CD checks for consistency

### Lesson 4: Version Control Everything
- Commit notebooks + dashboard together
- Clear commit messages
- Reference both in commit
- Tag major sync updates

---

## 🚀 Quick Reference

### Files to Keep in Sync:

1. ✅ `notebooks/23_langraph_agent_learning.py`
2. ✅ `notebooks/00_validate_environment.py`
3. ✅ `dashboard/app_databricks.py`
4. ✅ `docs/REFERENCE_23_langraph_agent_learning.py`
5. ✅ `docs/REFERENCE_00_validate_environment.py`

### Key Sections:

- **LLM Endpoint** (Model selection)
- **Tool Wrappers** (Pure functions)
- **Tool Descriptions** (Agent prompts)
- **Pydantic Schemas** (Input validation)
- **System Prompt** (Agent strategy)
- **Agent Creation** (LangGraph v1.0+ pattern)

### Deployment Commands:

```bash
# Update reference docs
cp notebooks/*.py docs/REFERENCE_*.py

# Deploy notebooks
databricks bundle deploy --profile DEFAULT

# Deploy dashboard
databricks apps stop classify-tickets-dashboard-dev --profile DEFAULT
databricks apps start classify-tickets-dashboard-dev --profile DEFAULT
```

---

## ❓ FAQ

**Q: Do I always need to sync notebooks and dashboard?**
A: No, only the critical sections listed above. UI-specific code doesn't need sync.

**Q: What if I want to experiment with different models?**
A: Use notebook for experiments, but document in dashboard why production model was chosen.

**Q: How do I know if something needs sync?**
A: Ask: "If this changed in one place but not the other, would behavior differ?" If yes, sync it.

**Q: Can I have different tool wrappers?**
A: Logic should be identical, but dashboard version might need additional Streamlit-specific code OUTSIDE the wrapper.

**Q: What about dependencies?**
A: Notebook uses `%pip install`, dashboard uses `requirements.txt`. Keep versions aligned!

---

**Last Updated:** November 11, 2025  
**Maintainer:** See git history  
**Status:** ✅ Notebooks and dashboard currently in sync

---

**Need to update this guide? Follow the same sync workflow!** 📚

