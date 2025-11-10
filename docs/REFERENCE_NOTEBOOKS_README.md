# Reference Notebooks for Learning

**Purpose:** Preserved copies of fully-documented LangGraph agent notebooks for future reference and learning

**Date Preserved:** November 7, 2025

---

## 📚 Reference Notebooks

### 1. **REFERENCE_23_langraph_agent_learning.py**
- **Original:** `notebooks/23_langraph_agent_learning.py`
- **Purpose:** Complete LangGraph ReAct agent implementation with educational comments
- **Lines:** 1,073 lines
- **Key Sections:**
  - Lines 25-41: Dependency installation and version requirements
  - Lines 49-85: Imports and configuration (with explanations)
  - Lines 96-129: Configuration variables
  - Lines 543-598: Tool definitions (all 4 LangChain tools)
  - Lines 659-730: **Agent creation (MOST IMPORTANT - v1.0+ pattern)**
  - Lines 755-795: Agent invocation pattern with SystemMessage injection
  - Lines 800-840: Results display and reasoning trail

### 2. **REFERENCE_00_validate_environment.py**
- **Original:** `notebooks/00_validate_environment.py`
- **Purpose:** Environment validation and agent creation testing
- **Lines:** 396 lines
- **Key Sections:**
  - Lines 3-20: Purpose and what gets validated
  - Lines 25-43: Dependency installation with version explanations
  - Lines 50-104: Import tests
  - Lines 130-220: Configuration validation
  - Lines 278-370: **Agent creation test (CRITICAL TEST)**

---

## 🎯 Why These Copies Exist

### **Learning Value:**
These notebooks contain **extensive educational documentation** including:
- ✅ Markdown cells explaining concepts and architecture
- ✅ Inline comments on every important line
- ✅ Version comparisons (LangGraph v0.2 vs v1.0+)
- ✅ Rationale for design decisions
- ✅ Alternative approaches documented
- ✅ Common pitfalls and how to avoid them

### **Preservation:**
- The working notebooks (in `notebooks/`) may evolve over time
- These reference copies preserve the fully-documented educational versions
- You can always refer back to these for learning

---

## 📖 How to Use These References

### **For Learning:**

1. **Start with validation notebook:**
   ```
   Open: docs/REFERENCE_00_validate_environment.py
   Focus: Lines 278-370 (agent creation test)
   Learn: The v1.0+ pattern in isolation
   ```

2. **Move to main notebook:**
   ```
   Open: docs/REFERENCE_23_langraph_agent_learning.py
   Focus: Lines 659-730 (agent creation)
   Learn: Complete ReAct agent implementation
   ```

3. **Study the pattern:**
   ```
   Compare:
   - Line 725-730: Agent creation (no state_modifier)
   - Line 784: SystemMessage injection
   - Line 786: User message
   ```

### **For Reference:**

When building your own LangGraph agents, refer to:

| Need | See Lines | What You'll Find |
|------|-----------|------------------|
| **Agent creation** | 725-730 | v1.0+ pattern (no state_modifier) |
| **Tool creation** | 543-598 | How to wrap functions as LangChain Tools |
| **Invocation pattern** | 781-788 | Manual SystemMessage injection |
| **System prompt** | 688-705 | How to guide agent behavior |
| **UC Function calls** | 100-153 | Statement Execution API pattern |
| **Vector Search** | 192-231 | Knowledge base search |
| **Genie API** | 257-481 | Conversation API with polling |

---

## 🔑 The Key Pattern (Line Numbers)

### **v1.0+ Pattern Explained:**

```python
# Line 688-705: Define system prompt
system_prompt = """You are an intelligent support ticket assistant..."""

# Line 710-715: Create LLM
llm = ChatDatabricks(endpoint=LLM_ENDPOINT, temperature=0.3, max_tokens=4096)

# Line 720: Prepare tools list
tools_list = [classify_tool, extract_tool, search_tool, genie_tool]

# Line 725-730: Create agent (NO state_modifier - v1.0+ pattern)
agent = create_react_agent(
    model=llm,
    tools=tools_list  # ✅ Simple and clean!
)

# Line 781-788: Invoke with manual SystemMessage injection
result = agent.invoke({
    "messages": [
        SystemMessage(content=system_prompt),  # ✅ Line 784: Inject here
        ("user", "Your task")                   # Line 786: User message
    ]
})
```

**This is the pattern that fixed the `state_modifier` error!**

---

## 🎓 What You'll Learn

By studying these reference notebooks, you'll understand:

### **1. LangGraph Evolution**
- How v0.2 vs v1.0 differ
- Why `state_modifier` was removed
- How to adapt code between versions

### **2. ReAct Pattern**
- Reasoning → Action → Observation loop
- How agents think and make decisions
- Message flow through the system

### **3. LangChain Tools**
- How to wrap any function as a Tool
- Tool descriptions and their importance
- Args schema with Pydantic

### **4. Databricks Integration**
- WorkspaceClient pattern for APIs
- ChatDatabricks for Foundation Models
- UC Functions via Statement Execution API
- Vector Search integration
- Genie Conversation API

### **5. Best Practices**
- Configuration management
- Error handling
- Safe attribute access with getattr()
- Message type checking
- Tool result parsing

---

## 📊 Visual Learning Aid

### **The Flow (High-Level):**

```
Line 688: system_prompt defined
    ↓
Line 710: llm created
    ↓
Line 543-598: Tools defined
    ↓
Line 725: Agent created (llm + tools)
    ↓
Line 781: Agent invoked with:
    ├─ Line 784: SystemMessage(system_prompt) ← Goes first!
    └─ Line 786: User message with task
    ↓
LLM reads both messages
    ↓
Agent makes decisions (ReAct loop)
    ↓
Line 791: result returned with full message history
```

---

## 🔍 Quick Search Guide

### **Search for these keywords in the notebooks:**

| Keyword | What It Marks |
|---------|--------------|
| `CRITICAL` | Most important patterns |
| `v1.0+` | Version-specific code |
| `Old/New` | Before/after comparisons |
| `Why` | Reasoning behind decisions |
| `Alternative` | Other approaches |
| `Trade-off` | Pros and cons |
| `❌` | Don't do this |
| `✅` | Do this |

---

## 📚 Related Documentation

These notebooks work together with:

1. **EDUCATIONAL_COMMENTS_GUIDE.md** - Overview of all comments added
2. **NOTEBOOK_DEBUG_FIXES.md** - Technical details of fixes
3. **QUICK_START_AGENT_NOTEBOOK.md** - Step-by-step run guide
4. **AGENT_NOTEBOOK_FIXES_SUMMARY.md** - High-level overview
5. **LANGRAPH_AGENT_PLAN.md** - Original implementation plan
6. **LANGRAPH_ARCHITECTURE.md** - Architecture explanations

---

## 💡 Pro Tips

### **When Referencing:**

1. **Line numbers are your friend** - They help you find exact patterns
2. **Read markdown cells first** - Get context before diving into code
3. **Compare validation vs main** - See same pattern in different contexts
4. **Trace variables** - Follow where things are defined and used

### **When Building Your Own Agents:**

1. **Copy the pattern** - Lines 725-730 and 781-788 are your template
2. **Adapt the system prompt** - Line 688-705 shows how to guide behavior
3. **Add your own tools** - Lines 543-598 show the Tool structure
4. **Test like validation** - Use the same testing approach

---

## 🎯 Success Criteria

You'll know you understand the pattern when you can:

- ✅ Explain why `state_modifier` was removed
- ✅ Create an agent without looking at these notebooks
- ✅ Know when to use SystemMessage injection
- ✅ Wrap your own functions as LangChain Tools
- ✅ Debug agent invocation errors
- ✅ Understand the ReAct loop flow

---

## 🚀 Next Steps

### **After Studying These Notebooks:**

1. **Experiment** - Modify the system prompt and see how behavior changes
2. **Build** - Create your own agent with different tools
3. **Share** - Use these patterns in your own projects
4. **Reference** - Keep these copies handy for future work

---

## 📝 Version Info

- **LangGraph:** v1.0+
- **LangChain:** v0.3+
- **Pattern:** Manual SystemMessage injection (v1.0+ compatible)
- **Status:** Production-ready, fully tested
- **Compatibility:** Works with latest Databricks Foundation Models

---

**These notebooks are now your learning reference library!** 📚

Keep them as examples of:
- Clean agent architecture
- Proper error handling
- Educational documentation
- Production-ready patterns

Happy learning and building! 🎓🚀

---

**Preserved by:** AI Assistant  
**Date:** November 7, 2025  
**Status:** Complete and fully documented

