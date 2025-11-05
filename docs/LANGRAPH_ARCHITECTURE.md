# LangGraph Agent Architecture - Visual Guide

## 🎯 Overview: Sequential vs. Agent-Based

### Current Sequential Pipeline (Tab 4: "AI Agent Assistant")
```
┌─────────────────┐
│  User Input     │
│  (Ticket Text)  │
└────────┬────────┘
         │
         ▼
┌────────────────────────────────────────────────────────┐
│  FIXED SEQUENCE - All Steps Always Execute            │
└────────────────────────────────────────────────────────┘
         │
         ├──► Step 1: ai_classify (UC Function)
         │            ↓ Category, Priority, Team
         │
         ├──► Step 2: ai_extract (UC Function)
         │            ↓ Metadata (urgency, systems)
         │
         ├──► Step 3: Vector Search
         │            ↓ Knowledge Base Articles
         │
         └──► Step 4: Genie API
                      ↓ Historical Tickets
         
         ▼
┌─────────────────┐
│  Display All    │
│  Results to     │
│  User           │
└─────────────────┘
```

**Characteristics:**
- ✅ Predictable, always same steps
- ✅ Easy to debug and understand
- ❌ Always runs all 4 tools (time + cost)
- ❌ No flexibility based on context

---

### New LangGraph Agent Approach (Tab 5: "LangGraph Agent")
```
┌─────────────────┐
│  User Input     │
│  (Ticket Text)  │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────┐
│  LLM Agent (Meta-Llama 3.3 70B)                        │
│  - Analyzes ticket                                      │
│  - Decides which tools to use                          │
│  - Makes intelligent choices                           │
└─────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────┐
│  ReAct Loop (Thought → Action → Observation)           │
└─────────────────────────────────────────────────────────┘
         │
         ├──► Thought: "What do I need to know first?"
         │
         ├──► Action: Choose Tool from:
         │            • ClassifyTicketTool
         │            • ExtractMetadataTool
         │            • SearchKnowledgeTool
         │            • QueryHistoricalTool
         │
         ├──► Observation: Process tool result
         │
         ├──► Thought: "Do I need more info?"
         │            ├─► YES: Choose another tool
         │            └─► NO: Finish and return result
         │
         └──► Repeat until agent decides it's done
         
         ▼
┌─────────────────┐
│  Display Agent  │
│  Reasoning +    │
│  Results        │
└─────────────────┘
```

**Characteristics:**
- ✅ Flexible, adaptive to ticket context
- ✅ Potentially faster (only needed tools)
- ✅ Shows reasoning (educational)
- ❌ Less predictable
- ❌ More complex to debug

---

## 🏗️ Architecture Components

### 1. LangChain Tools (Wrappers Around Existing APIs)

```
┌───────────────────────────────────────────────────────────────┐
│                    LangChain Tools Layer                      │
│                                                               │
│  Each tool wraps an existing API with LangChain interface    │
└───────────────────────────────────────────────────────────────┘

┌─────────────────────┐  ┌─────────────────────┐
│ ClassifyTicketTool  │  │ ExtractMetadataTool │
│                     │  │                     │
│ Description:        │  │ Description:        │
│ "Classifies ticket  │  │ "Extracts metadata  │
│  by category,       │  │  like priority,     │
│  priority, team"    │  │  urgency, systems"  │
│                     │  │                     │
│ func():             │  │ func():             │
│  ↓ Call UC Function │  │  ↓ Call UC Function │
│    ai_classify      │  │    ai_extract       │
└─────────────────────┘  └─────────────────────┘

┌─────────────────────┐  ┌─────────────────────┐
│ SearchKnowledgeTool │  │ QueryHistoricalTool │
│                     │  │                     │
│ Description:        │  │ Description:        │
│ "Searches knowledge │  │ "Queries historical │
│  base for relevant  │  │  tickets for        │
│  documentation"     │  │  similar cases"     │
│                     │  │                     │
│ func():             │  │ func():             │
│  ↓ Call Vector      │  │  ↓ Call Genie API   │
│    Search API       │  │                     │
└─────────────────────┘  └─────────────────────┘
```

**Code Example:**
```python
from langchain.tools import Tool

classify_tool = Tool(
    name="classify_ticket",
    description="Classifies a support ticket by category, priority, and routing team. Use this when you need to understand what type of ticket you're dealing with.",
    func=lambda ticket: call_uc_function("ai_classify", {"ticket_text": ticket})
)

# Agent sees tools as:
# - Tool names (classify_ticket, search_knowledge, etc.)
# - Tool descriptions (helps agent decide when to use)
# - Tool functions (what actually gets called)
```

---

### 2. LangGraph ReAct Agent Flow

```
┌──────────────────────────────────────────────────────────────┐
│                    LangGraph State Graph                     │
└──────────────────────────────────────────────────────────────┘

        START
          │
          ▼
    ┌─────────┐
    │  Agent  │◄──────────┐
    │  Node   │            │
    └────┬────┘            │
         │                 │
         │ Decision:       │
         │                 │
    ┌────▼────┐           │
    │ Should  │           │
    │Continue?│           │
    └────┬────┘           │
         │                │
    ┌────┴─────┬──────────┘
    │          │
   YES        NO
    │          │
    ▼          ▼
┌────────┐  ┌────────┐
│ Tools  │  │  END   │
│ Node   │  │ (Return│
└───┬────┘  │Result) │
    │       └────────┘
    │
    │ Execute
    │ Selected
    │ Tool
    │
    └─────────┘
    (Loop back to Agent)
```

**State Object:**
```python
class AgentState(TypedDict):
    """State that flows through the graph"""
    
    # Input
    ticket: str  # Original ticket text
    
    # Tool Results (populated as agent calls tools)
    classification: Optional[dict]    # From ClassifyTicketTool
    metadata: Optional[dict]          # From ExtractMetadataTool
    knowledge_results: Optional[list] # From SearchKnowledgeTool
    historical_results: Optional[dict] # From QueryHistoricalTool
    
    # Agent's Decision Trail
    messages: list  # Chat history with agent's thoughts
    
    # Output
    final_result: Optional[str]  # Agent's final answer
```

---

### 3. ReAct Decision Loop (How the Agent Thinks)

```
┌─────────────────────────────────────────────────────────────┐
│  ReAct = Reasoning + Acting (Thought → Action → Observation)│
└─────────────────────────────────────────────────────────────┘

Example Ticket: "Database connection timeout in production"

ITERATION 1:
┌──────────────────────────────────────────────────────────┐
│ 🧠 Thought:                                              │
│   "I need to classify this ticket to understand          │
│    the urgency and which team should handle it"          │
└──────────────────────────────────────────────────────────┘
           ↓
┌──────────────────────────────────────────────────────────┐
│ 🔧 Action:                                               │
│   Tool: classify_ticket                                  │
│   Input: "Database connection timeout in production"     │
└──────────────────────────────────────────────────────────┘
           ↓
┌──────────────────────────────────────────────────────────┐
│ 👁️ Observation:                                          │
│   Result: {                                              │
│     "category": "Technical",                             │
│     "priority": "Critical",                              │
│     "team": "Database Team"                              │
│   }                                                      │
└──────────────────────────────────────────────────────────┘

ITERATION 2:
┌──────────────────────────────────────────────────────────┐
│ 🧠 Thought:                                              │
│   "This is critical and production-related. I should     │
│    search the knowledge base for timeout solutions"      │
└──────────────────────────────────────────────────────────┘
           ↓
┌──────────────────────────────────────────────────────────┐
│ 🔧 Action:                                               │
│   Tool: search_knowledge                                 │
│   Input: "database connection timeout production"        │
└──────────────────────────────────────────────────────────┘
           ↓
┌──────────────────────────────────────────────────────────┐
│ 👁️ Observation:                                          │
│   Found 3 articles:                                      │
│   1. "DB Timeout Troubleshooting Guide"                  │
│   2. "Connection Pool Configuration"                     │
│   3. "Network Latency Issues"                            │
└──────────────────────────────────────────────────────────┘

ITERATION 3:
┌──────────────────────────────────────────────────────────┐
│ 🧠 Thought:                                              │
│   "I have classification and knowledge articles.         │
│    For critical issues, I should check historical        │
│    tickets to see how similar cases were resolved"       │
└──────────────────────────────────────────────────────────┘
           ↓
┌──────────────────────────────────────────────────────────┐
│ 🔧 Action:                                               │
│   Tool: query_historical                                 │
│   Input: "database timeout critical resolved"            │
└──────────────────────────────────────────────────────────┘
           ↓
┌──────────────────────────────────────────────────────────┐
│ 👁️ Observation:                                          │
│   Found 5 similar tickets, average resolution: 2.5 hrs  │
│   Common resolution: "Increase connection pool size"     │
└──────────────────────────────────────────────────────────┘

ITERATION 4:
┌──────────────────────────────────────────────────────────┐
│ 🧠 Thought:                                              │
│   "I have enough information now:                        │
│    - Critical technical issue for DB team                │
│    - Knowledge base articles available                   │
│    - Historical pattern shows common fix                 │
│    I can provide a comprehensive response"               │
└──────────────────────────────────────────────────────────┘
           ↓
┌──────────────────────────────────────────────────────────┐
│ 🏁 Action: FINISH                                        │
│   Final Answer: [Synthesized recommendation]             │
└──────────────────────────────────────────────────────────┘
```

**Key Insight:** Agent called 3 tools (classify, search, historical) but skipped `extract_metadata` because it wasn't needed for this ticket!

---

### 4. Comparison Example: Same Ticket, Different Approaches

**Ticket:** "How do I reset my password?"

#### Sequential Pipeline (Always 4 steps):
```
Step 1: Classify        → Category: Account, Priority: Low
Step 2: Extract         → Systems: ["Auth Service"]
Step 3: Vector Search   → 5 password reset articles
Step 4: Genie Query     → 20 similar historical tickets

Total: 4 API calls, ~8 seconds, 4 tools
```

#### LangGraph Agent (Adaptive):
```
Iteration 1:
  Thought: "Simple password question, classify first"
  Action: classify_ticket
  Result: Category: Account, Priority: Low

Iteration 2:
  Thought: "This is a common account question. Knowledge
           base should have the answer. No need for
           historical tickets or metadata extraction."
  Action: search_knowledge
  Result: Found "Password Reset Guide" article

Iteration 3:
  Thought: "I have the answer - found a complete guide.
           No need to query historical tickets since
           the KB article has step-by-step instructions."
  Action: FINISH

Total: 2 API calls, ~4 seconds, 2 tools
Result: 50% faster, 50% cheaper, still complete answer
```

**Why the difference?**
- Agent recognized it was a simple, common question
- KB article was sufficient
- Historical tickets wouldn't add value
- Metadata extraction not needed for low-priority account issue

---

## 🔄 Complete Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                         Dashboard UI                        │
│  Tab 5: "🧪 LangGraph Agent (Experimental)"                │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ User enters ticket
                            ▼
┌─────────────────────────────────────────────────────────────┐
│            dashboard/langraph_agent.py Module               │
│                                                             │
│  TicketReActAgent class:                                    │
│  - Initialize LangGraph agent                               │
│  - Load 4 LangChain Tools                                   │
│  - Configure ChatDatabricks LLM                             │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                  LangGraph ReAct Agent                      │
│                                                             │
│  [Agent Node]                                               │
│   ↓                                                         │
│  LLM decides: What tool to use?                             │
│   ↓                                                         │
│  [Tool Node]                                                │
│   ↓                                                         │
│  Execute selected tool (one of 4)                           │
│   ↓                                                         │
│  [Agent Node] - Evaluate result                             │
│   ↓                                                         │
│  Continue? → YES: Loop back | NO: Return result             │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ Tool calls go to:
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ UC Functions │  │ Vector Search│  │  Genie API   │
│              │  │              │  │              │
│ ai_classify  │  │ Query with   │  │ Natural      │
│ ai_extract   │  │ embeddings   │  │ language SQL │
└──────────────┘  └──────────────┘  └──────────────┘
        │                   │                   │
        └───────────────────┼───────────────────┘
                            │
                            ▼
                    Results flow back
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                      Dashboard Display                      │
│                                                             │
│  📊 Show:                                                   │
│  - Agent's reasoning trail                                  │
│  - Which tools were called                                  │
│  - Results from each tool                                   │
│  - Final synthesized answer                                 │
│  - Comparison metrics (time, cost, tools used)              │
└─────────────────────────────────────────────────────────────┘
```

---

## 📊 Side-by-Side Comparison in Dashboard

```
┌─────────────────────────────────────────────────────────────┐
│  Comparison Mode: Sequential vs. LangGraph Agent           │
└─────────────────────────────────────────────────────────────┘

┌──────────────────────────┬──────────────────────────────────┐
│  Sequential Pipeline     │  LangGraph Agent                 │
├──────────────────────────┼──────────────────────────────────┤
│ ✓ ai_classify            │ ✓ classify_ticket (decided)      │
│ ✓ ai_extract             │ ✗ extract_metadata (skipped)     │
│ ✓ vector_search          │ ✓ search_knowledge (decided)     │
│ ✓ genie_query            │ ✗ query_historical (skipped)     │
├──────────────────────────┼──────────────────────────────────┤
│ Tools Used: 4/4          │ Tools Used: 2/4                  │
│ Time: 8.2s               │ Time: 4.1s                       │
│ Cost: ~$0.008            │ Cost: ~$0.005                    │
├──────────────────────────┼──────────────────────────────────┤
│ Result: Complete         │ Result: Complete                 │
│ Quality: ⭐⭐⭐⭐⭐     │ Quality: ⭐⭐⭐⭐⭐           │
└──────────────────────────┴──────────────────────────────────┘

Agent's Reasoning:
  "This is a simple account question. The knowledge base
   article provides complete step-by-step instructions.
   No need to query historical tickets or extract metadata
   for such a common, well-documented issue."
```

---

## 🎓 Learning Objectives

After implementing this, you'll understand:

### 1. **LangChain Tools Pattern**
- How to wrap any API/function as a LangChain Tool
- How tool descriptions guide agent decisions
- How to pass parameters and handle results

### 2. **ReAct Agent Architecture**
- Thought → Action → Observation loop
- How LLMs make autonomous decisions
- When agents add value vs. overhead

### 3. **LangGraph State Management**
- How to define state schemas
- How state flows through graph nodes
- Conditional routing based on agent decisions

### 4. **Trade-offs Analysis**
- **Predictability** vs. **Flexibility**
- **Simplicity** vs. **Intelligence**
- **Fixed Cost** vs. **Variable Cost**
- **Easy Debug** vs. **Adaptive Behavior**

### 5. **Real-World Application**
- When to use agents (complex, varied scenarios)
- When to use sequential (predictable, uniform tasks)
- How to measure and compare approaches
- Production considerations (reliability, cost, latency)

---

## 🚀 Quick Start Guide

Once you implement following the plan:

### 1. **Run Notebook**
```bash
# Open notebook in Databricks
notebooks/23_langraph_agent_learning.py

# Test with sample tickets
# Compare Sequential vs. Agent mode
```

### 2. **Try in Dashboard**
```python
# Navigate to new tab: 🧪 LangGraph Agent (Experimental)
# Enter ticket
# Toggle "Show Agent Reasoning" ON
# Click "Run LangGraph Agent"
# Watch the agent think!
```

### 3. **Compare Approaches**
```python
# Click "Compare with Sequential Pipeline"
# See side-by-side results
# Analyze which approach worked better for your ticket type
```

---

## 🔍 Example Agent Decision Trees

### Scenario 1: Critical Production Issue
```
Ticket: "Production database down"
├─ Thought: Critical word detected, classify first
├─ Action: classify_ticket → Critical, Database Team
├─ Thought: Need immediate solutions
├─ Action: search_knowledge → Emergency procedures
├─ Thought: Check if this happened before
├─ Action: query_historical → Found 3 similar incidents
└─ Result: 3 tools, comprehensive response
```

### Scenario 2: Simple How-To Question
```
Ticket: "How do I export a report?"
├─ Thought: Simple question, classify first
├─ Action: classify_ticket → Low priority, Documentation
├─ Thought: Knowledge base should have this
├─ Action: search_knowledge → Found "Report Export Guide"
└─ Result: 2 tools, sufficient answer (no need for historical)
```

### Scenario 3: Complex Feature Request
```
Ticket: "Need new API integration with Salesforce"
├─ Thought: Complex request, classify first
├─ Action: classify_ticket → Feature Request, Engineering
├─ Thought: Extract technical details
├─ Action: extract_metadata → Systems, integrations, timeline
├─ Thought: Check if similar features exist
├─ Action: search_knowledge → Found integration docs
├─ Thought: Check historical feature requests
├─ Action: query_historical → Found similar past requests
└─ Result: 4 tools, comprehensive analysis
```

---

## 💡 Key Insights

1. **Agent adapts to ticket complexity**
   - Simple questions → fewer tools
   - Complex issues → more thorough analysis

2. **Cost efficiency potential**
   - Can reduce API calls by 25-50% on simple tickets
   - Still maintains quality

3. **Transparency gain**
   - You see *why* agent made each decision
   - Educational: learn what information is actually needed

4. **Flexibility for future**
   - Easy to add new tools (e.g., "Create JIRA ticket")
   - Agent automatically incorporates them

5. **Trade-off awareness**
   - Adds LLM inference overhead (agent thinking)
   - Saves on unnecessary tool calls
   - Net benefit depends on ticket distribution

---

## 📚 References

- **LangGraph Docs:** https://python.langchain.com/docs/langgraph
- **LangChain Tools:** https://python.langchain.com/docs/modules/agents/tools/
- **ReAct Paper:** https://arxiv.org/abs/2210.03629
- **Databricks LangGraph Example:** https://docs.databricks.com/aws/en/notebooks/source/generative-ai/langgraph-multiagent-genie.html

---

**Ready to implement?** Follow the plan in `docs/LANGRAPH_AGENT_PLAN.md`! 🎯

