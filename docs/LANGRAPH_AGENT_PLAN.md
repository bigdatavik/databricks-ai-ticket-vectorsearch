# LangGraph Agent Learning Implementation Plan

**Branch:** `agent_langraph_trying`  
**Status:** Not Started - Plan Ready for Implementation  
**Created:** November 2025

## Overview
Build a LangGraph ReAct agent that uses LangChain Tools to intelligently decide which operations to perform on support tickets, enabling comparison with the existing sequential pipeline.

---

## Phase 1: Notebook Prototyping

### Step 1: Create LangChain Tool Wrappers
**File:** `notebooks/23_langraph_agent_learning.py`

Create 4 LangChain Tools that wrap existing APIs:

1. **ClassifyTicketTool**
   - Wraps UC Function: `ai_classify`
   - Description: "Classifies a support ticket by category, priority, and team"
   - Uses `WorkspaceClient` to call UC function

2. **ExtractMetadataTool** 
   - Wraps UC Function: `ai_extract`
   - Description: "Extracts structured metadata from ticket (priority score, urgency, systems)"

3. **SearchKnowledgeTool**
   - Wraps Vector Search API
   - Description: "Searches knowledge base for relevant documentation and solutions"
   - Uses existing Vector Search query pattern from dashboard

4. **QueryHistoricalTool**
   - Wraps Genie Conversation API
   - Description: "Queries historical tickets for similar resolved cases"
   - Uses `GenieConversationTool` pattern from dashboard

**Key Implementation:**
```python
from langchain.tools import Tool
from databricks_langchain import ChatDatabricks

# Example structure
classify_tool = Tool(
    name="classify_ticket",
    description="Classifies support ticket by category, priority, and routing team",
    func=lambda ticket: call_uc_function_wrapper("ai_classify", ticket)
)
```

### Step 2: Build ReAct Agent with LangGraph
**File:** `notebooks/23_langraph_agent_learning.py` (continued)

Create a ReAct agent that:
- Receives a ticket as input
- Has access to all 4 tools
- LLM decides which tools to call and in what order
- Shows reasoning trail (Thought → Action → Observation)

**Agent Configuration:**
- Model: `ChatDatabricks(endpoint="databricks-meta-llama-3-3-70b-instruct")`
- Framework: LangGraph `create_react_agent`
- Tools: All 4 tools from Step 1

### Step 3: Add State Management and Conditional Logic
**File:** `notebooks/23_langraph_agent_learning.py` (continued)

Implement LangGraph state machine:
- **State:** Stores ticket, tool results, agent decisions
- **Nodes:** Agent planning, tool execution, result synthesis
- **Edges:** Conditional routing based on agent decisions

**State Schema:**
```python
class AgentState(TypedDict):
    ticket: str
    classification: Optional[dict]
    metadata: Optional[dict]
    knowledge_results: Optional[list]
    historical_results: Optional[dict]
    agent_decisions: list  # Track what agent chose to do
    final_result: Optional[str]
```

### Step 4: Add Comparison Mode
**File:** `notebooks/23_langraph_agent_learning.py` (continued)

Create side-by-side comparison:
1. **Sequential Pipeline:** Run all 4 tools in fixed order (current approach)
2. **Agent Mode:** Let ReAct agent decide which tools to call

Display comparison:
- Which tools were called by agent vs. all tools
- Agent's reasoning for each decision
- Time and cost comparison
- Output quality comparison

### Step 5: Add Debug Visualization
**File:** `notebooks/23_langraph_agent_learning.py` (continued)

Add LangGraph visualization:
- Show agent decision graph
- Display reasoning trail with timestamps
- Highlight which tools were called and why
- Show tool results and how they influenced next decision

---

## Phase 2: Dashboard Integration

### Step 6: Add LangGraph Dependencies
**File:** `dashboard/requirements.txt`

Add required packages:
```
langgraph
langchain
langchain-core
databricks-langchain
```

### Step 7: Create Agent Module
**File:** `dashboard/langraph_agent.py` (new file)

Extract agent logic from notebook into reusable module:
- `TicketAgentTools` class (contains all 4 LangChain Tools)
- `TicketReActAgent` class (manages LangGraph agent)
- `run_agent_analysis()` function (main entry point)

Clean, production-ready code separated from dashboard UI.

### Step 8: Add New Dashboard Tab
**File:** `dashboard/app_databricks.py`

Add 5th tab: **"🧪 LangGraph Agent (Experimental)"**

UI Components:
1. **Header:** Explain this is experimental/learning mode
2. **Input:** Same ticket input as other tabs
3. **Toggle:** "Show Agent Reasoning" (display thought process)
4. **Run Button:** "🤖 Run LangGraph Agent"
5. **Results Display:**
   - Agent's decision trail (which tools it called and why)
   - Results from each tool call
   - Final synthesized response
   - Comparison metrics (time, cost, tools used)

### Step 9: Add Agent Reasoning Display
**File:** `dashboard/app_databricks.py` (continued)

Show agent's thinking process:
```
🧠 Agent Thinking:
  1. Thought: "I need to understand the ticket category first"
     Action: classify_ticket
     Result: Category=Technical, Priority=High
  
  2. Thought: "This is technical and high priority, I should search knowledge base"
     Action: search_knowledge
     Result: Found 3 relevant articles
  
  3. Thought: "I have enough information to provide recommendation"
     Action: FINISH
```

### Step 10: Add Comparison View
**File:** `dashboard/app_databricks.py` (continued)

Optional feature: Side-by-side comparison
- Button: "Compare with Sequential Pipeline"
- Shows both results
- Highlights differences in tool usage, time, cost

---

## Phase 3: Documentation

### Step 11: Update Documentation
**Files:** `MY_ENVIRONMENT_AI_TICKET_LESSONS.md`, `README.md`

Add new section: "LangGraph Agent Learning"
- Architecture comparison: Sequential vs. Agent-based
- When to use each approach
- Key learnings from implementation
- Performance and cost analysis
- Future considerations

### Step 12: Create Agent README
**File:** `notebooks/poc_archive/AGENT_LEARNING.md` (or similar)

Document the learning journey:
- Why we implemented both approaches
- How ReAct agents work
- LangChain Tools pattern
- LangGraph state management
- Pros/cons of each approach for this use case

---

## Key Files Modified/Created

### New Files
- `notebooks/23_langraph_agent_learning.py` - Learning notebook
- `dashboard/langraph_agent.py` - Agent module
- Documentation updates

### Modified Files
- `dashboard/app_databricks.py` - Add new tab
- `dashboard/requirements.txt` - Add LangGraph dependencies

---

## Implementation Checklist

- [ ] Create 4 LangChain Tool wrappers (Classify, Extract, Search, Genie) in notebook
- [ ] Build ReAct agent with LangGraph using ChatDatabricks LLM
- [ ] Implement LangGraph state machine with conditional routing
- [ ] Create side-by-side comparison: Sequential vs Agent approach
- [ ] Add agent decision graph and reasoning trail visualization
- [ ] Add langgraph, langchain, databricks-langchain to dashboard/requirements.txt
- [ ] Extract agent logic into dashboard/langraph_agent.py module
- [ ] Add new 'LangGraph Agent (Experimental)' tab to dashboard
- [ ] Implement agent reasoning trail display in dashboard UI
- [ ] Add optional comparison view in dashboard (Sequential vs Agent)
- [ ] Update MY_ENVIRONMENT_AI_TICKET_LESSONS.md and README.md with agent learnings

---

## Learning Outcomes

After implementation, you'll understand:
1. How to wrap APIs as LangChain Tools
2. How ReAct agents make autonomous decisions
3. How LangGraph manages state and routing
4. Trade-offs: flexibility vs. predictability
5. When agent-based approaches add value vs. overhead

---

## Success Criteria

- ✅ Notebook runs successfully with ReAct agent
- ✅ Agent makes intelligent tool selection decisions
- ✅ Dashboard tab displays agent reasoning clearly
- ✅ Can compare sequential vs. agent approaches
- ✅ Documentation captures learnings

---

## References

- **Existing POC Notebooks:** `notebooks/poc_archive/20_langgraph_poc_with_tools.py`, `22_fixed_agent_with_genie.py`
- **Current Dashboard:** `dashboard/app_databricks.py` - "🤖 AI Agent Assistant" tab (sequential pipeline)
- **LangGraph Docs:** https://docs.databricks.com/aws/en/notebooks/source/generative-ai/langgraph-multiagent-genie.html
- **LangChain Tools:** https://python.langchain.com/docs/modules/agents/tools/

---

## Notes

- This is for **learning purposes** - to understand agent-based architectures
- The existing sequential pipeline in production will remain untouched
- Implementation is on the `agent_langraph_trying` branch
- Can merge to main later if the approach proves valuable
- Focus on understanding trade-offs rather than replacing current system

