# LangGraph + Databricks Tutorial

**Learn to build adaptive AI agents using LangGraph's ReAct pattern on Databricks**

This tutorial demonstrates how to build intelligent agents that can reason and act adaptively using LangGraph, LangChain, and Databricks Unity Catalog.

🔗 **Main Project**: [databricks-ai-ticket-vectorsearch](https://github.com/bigdatavik/databricks-ai-ticket-vectorsearch)

---

## 🎯 What You'll Learn

By completing this tutorial, you will learn how to:

1. **Create LangChain Tools** that wrap Databricks services:
   - Unity Catalog AI Functions
   - Vector Search for semantic retrieval
   - Genie API for natural language queries

2. **Build a LangGraph ReAct Agent** that:
   - Reasons about which tools to use
   - Adapts to task complexity
   - Provides transparent decision-making

3. **Master Critical Patterns**:
   - `bind_tools()` for reliable tool calling
   - Pydantic input schemas for type safety
   - WorkspaceClient authentication
   - Error handling and retries

4. **Compare Approaches**:
   - Sequential agent orchestration
   - Adaptive ReAct agent
   - When to use each pattern

---

## 📋 Prerequisites

### Required Access

- **Databricks Workspace** (Azure, AWS, or GCP)
- **Unity Catalog** enabled
- **Cluster** with Databricks Runtime 16.4 LTS or later
- **Permissions**:
  - Execute UC AI Functions
  - Query Vector Search indexes
  - Access Genie spaces (optional)

### Required Knowledge

- Python programming
- Basic understanding of LLMs
- Familiarity with Databricks notebooks

---

## 🚀 Quick Start

### For Complete Beginners

**📖 NEW: [Complete Beginner's Tutorial](BEGINNER_TUTORIAL.md)**

Step-by-step guide that assumes NO prior experience with:
- Databricks
- LangChain
- LangGraph
- AI Agents

**Start here if you're new!** → [`BEGINNER_TUTORIAL.md`](BEGINNER_TUTORIAL.md)

### For Experienced Users

**1. Deploy with Databricks Asset Bundles (Recommended)**

```bash
# Install Databricks CLI
curl -fsSL https://raw.githubusercontent.com/databricks/setup-cli/main/install.sh | sh

# Configure authentication
databricks configure --token

# Clone and deploy
git clone https://github.com/bigdatavik/databricks-ai-ticket-vectorsearch.git
cd databricks-ai-ticket-vectorsearch
git checkout langgraph-databricks-tutorial

# Update databricks.yml with your config
# Then deploy
databricks bundle deploy --target dev
```

**📋 Full deployment guide**: [`DEPLOYMENT_GUIDE.md`](DEPLOYMENT_GUIDE.md)

**2. Manual Setup**

```bash
# Clone repository
git clone https://github.com/bigdatavik/databricks-ai-ticket-vectorsearch.git
cd databricks-ai-ticket-vectorsearch
git checkout langgraph-databricks-tutorial

# Install dependencies
pip install -r requirements.txt

# Upload tutorial/23_langraph_agent_learning.py to Databricks
# Upload setup_uc_functions.py to Databricks

# Run setup_uc_functions.py to create AI Functions
# Then run the tutorial notebook
```

**3. Quick Configuration**

Update these in the tutorial notebook:
- `CATALOG` - Your Unity Catalog name
- `SCHEMA` - Your schema name  
- `WAREHOUSE_ID` - Your SQL Warehouse ID
- `CLUSTER_ID` - Your cluster ID

---

## 📚 Tutorial Structure

### Main Tutorial Notebook

**`tutorial/23_langraph_agent_learning.py`**

An interactive Databricks notebook that walks you through:

1. **Setup & Dependencies** - Install LangGraph and configure environment
2. **Test Individual Tools** - Verify each Databricks service works
3. **Wrap Tools for LangChain** - Create tool wrappers with proper schemas
4. **Build Sequential Agent** - Fixed 4-step orchestration
5. **Build ReAct Agent** - Adaptive tool selection with LangGraph
6. **Compare Approaches** - See the difference in action
7. **Best Practices** - Critical patterns and gotchas

### Supporting Documentation

**`docs/`**

- **`REFERENCE_23_langraph_agent_learning.py`** - Complete reference implementation
- **`LANGRAPH_ARCHITECTURE.md`** - Deep dive into the architecture
- **`LANGRAPH_BIND_TOOLS_EXPLAINED.md`** - Why `bind_tools()` is critical
- **`LANGRAPH_FOR_FRIENDS.md`** - Simplified explanation for beginners
- **`QUICK_START_AGENT_NOTEBOOK.md`** - Quick reference guide

---

## 🔑 Key Concepts

### 1. The ReAct Pattern (Reasoning + Acting)

```
1. Think: Analyze the problem
2. Act: Choose and use tools
3. Observe: Review tool results
4. Decide: Continue or finish
5. Respond: Provide final answer
```

### 2. The bind_tools() Pattern (Critical!)

```python
# ❌ BAD: Tools not bound to LLM
agent = create_react_agent(llm, tools)

# ✅ GOOD: Explicitly bind tools
llm_with_tools = llm.bind_tools(tools)
agent = create_react_agent(llm_with_tools, tools)
```

**Why?** Ensures consistent JSON formatting, eliminates XML parse errors.

### 3. Tool Input Schemas (Type Safety)

```python
from pydantic import BaseModel, Field

class ClassifyInput(BaseModel):
    ticket_text: str = Field(description="The text to classify")
```

### 4. Adaptive vs Sequential

**Sequential**:
- Always runs all tools
- Predictable execution
- Higher cost for simple tasks

**Adaptive (ReAct)**:
- Chooses tools based on need
- 40-60% cost savings on simple tasks
- More intelligent behavior

---

## 🛠️ Technology Stack

- **LangGraph**: 1.0+ (state machine for agents)
- **LangChain**: 0.3+ (tool abstractions)
- **Databricks SDK**: WorkspaceClient for API calls
- **Unity Catalog**: Serverless AI Functions
- **Vector Search**: Semantic retrieval
- **Genie API**: Natural language SQL queries
- **Claude Sonnet 4**: Recommended LLM (via Databricks FMAPI)

---

## 📖 Learning Path

### Beginner (1-2 hours)

1. Read `LANGRAPH_FOR_FRIENDS.md`
2. Run notebook cells 1-5 (Setup & Individual Tools)
3. Understand tool wrappers

### Intermediate (2-3 hours)

1. Complete full notebook
2. Build sequential agent
3. Build ReAct agent
4. Compare results

### Advanced (3-4 hours)

1. Read `LANGRAPH_ARCHITECTURE.md`
2. Study `REFERENCE_23_langraph_agent_learning.py`
3. Customize for your use case
4. Implement in production

---

## 🎨 Real-World Example

### Simple Task (Password Reset)

```
🧠 Agent Thought: "Standard password reset"
🔧 Tool 1: classify_ticket() → P3, Access
🔧 Tool 2: search_knowledge() → KB-001 solution
💡 Response: "Follow KB-001 for password reset"
Cost: $0.0005 | Time: 1.2s
```

### Complex Task (Database Outage)

```
🧠 Agent Thought: "Critical database issue"
🔧 Tool 1: classify_ticket() → P1, Database
🔧 Tool 2: extract_metadata() → Multiple systems affected
🔧 Tool 3: search_knowledge() → No exact match
🔧 Tool 4: query_historical() → 3 similar P1 tickets
💡 Response: "Critical outage. Similar incidents resolved by restarting replica (avg 15min)"
Cost: $0.0018 | Time: 4.1s
```

---

## 🐛 Common Issues & Solutions

### 1. XML Format Errors

**Problem**: Agent returns XML instead of JSON

**Solution**: Use `llm.bind_tools(tools)` pattern

### 2. Tool Not Found

**Problem**: "Tool 'classify_ticket' not found"

**Solution**: Verify tool name matches exactly in schema and tool list

### 3. Authentication Errors

**Problem**: 403/401 errors calling Databricks APIs

**Solution**: Ensure WorkspaceClient() is initialized correctly and cluster has permissions

### 4. Timeout Errors (Genie)

**Problem**: Genie queries timeout

**Solution**: Implement polling with exponential backoff (shown in notebook)

---

## 🔗 Additional Resources

### From This Project

- **Main Project**: [Full AI Support Ticket System](https://github.com/bigdatavik/databricks-ai-ticket-vectorsearch)
- **LinkedIn Article**: [Reference Architecture Blog Post](#) (detailed writeup)

### Databricks Documentation

- [Unity Catalog AI Functions](https://docs.databricks.com/en/large-language-models/ai-functions.html)
- [Vector Search](https://docs.databricks.com/en/generative-ai/vector-search.html)
- [Genie API](https://docs.databricks.com/en/genie/genie-api.html)

### LangChain & LangGraph

- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [ReAct Pattern Paper](https://arxiv.org/abs/2210.03629)
- [LangChain Tools](https://python.langchain.com/docs/modules/agents/tools/)

---

## 🤝 Contributing

Found an issue or have improvements? 

1. Open an issue on the [main repository](https://github.com/bigdatavik/databricks-ai-ticket-vectorsearch/issues)
2. Submit a pull request
3. Share your feedback!

---

## 📝 License

This tutorial is part of the databricks-ai-ticket-vectorsearch project.

[Add your license here]

---

## 🙏 Acknowledgments

This tutorial is extracted from a production reference architecture built for AI-powered support ticket classification. The patterns demonstrated here are battle-tested and production-ready.

**Main Project Contributors**: [Your Name and Co-Authors]

---

## 💬 Questions?

- **Issues**: [GitHub Issues](https://github.com/bigdatavik/databricks-ai-ticket-vectorsearch/issues)
- **Discussions**: [GitHub Discussions](#)
- **LinkedIn**: [Connect for questions](#)

---

**Built with ❤️ using Databricks, LangChain, and LangGraph**

---

## 🚀 Next Steps

After completing this tutorial:

1. ⭐ **Star the repository** if you found it useful!
2. 📖 **Explore the full project** for production deployment patterns
3. 🔧 **Adapt for your use case** (customer service, email classification, etc.)
4. 🎓 **Share your learnings** - help others discover these patterns!

**Happy Learning!** 🎉
