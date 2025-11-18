# ⚡ Quick Start Guide

**Get started with LangGraph on Databricks in 10 minutes!**

---

## 🎯 Choose Your Path

### 🆕 Absolute Beginner?

**Start here**: [`BEGINNER_TUTORIAL.md`](BEGINNER_TUTORIAL.md)

- Complete step-by-step guide
- No prior experience required
- Learn concepts from scratch
- **Time**: 2-3 hours

### 🚀 Experienced Developer?

**Follow this Quick Start** (below) ⬇️

- Assumes you know Databricks basics
- Fast-track to building agents
- **Time**: 10-15 minutes

---

## ⚡ 10-Minute Setup

### 1. Prerequisites Check

- [ ] Databricks workspace access
- [ ] Cluster created (any size)
- [ ] Unity Catalog enabled
- [ ] 10 minutes of time

### 2. Deploy with One Command

```bash
# Install Databricks CLI
curl -fsSL https://raw.githubusercontent.com/databricks/setup-cli/main/install.sh | sh

# Authenticate
databricks configure --token

# Clone and switch to tutorial branch
git clone https://github.com/bigdatavik/databricks-ai-ticket-vectorsearch.git
cd databricks-ai-ticket-vectorsearch
git checkout langgraph-databricks-tutorial

# Deploy everything
databricks bundle deploy --target dev
```

**⚠️ Before deploying**: Edit `databricks.yml` to update:
- `workspace.host` → Your workspace URL
- `variables.cluster_id` → Your cluster ID
- `variables.warehouse_id` → Your warehouse ID

### 3. Set Up Unity Catalog Functions

1. Upload `setup_uc_functions.py` to Databricks
2. Open and run it (creates AI functions)
3. Verify tests pass ✅

### 4. Run the Tutorial

1. Navigate to deployed notebook:
   - Workspace → Users → your-email → .bundle → langraph-tutorial → dev → tutorial
2. Open `23_langraph_agent_learning.py`
3. Update config (Cmd 2):
   ```python
   CATALOG = "langraph_tutorial"
   SCHEMA = "agents"
   CLUSTER_ID = "your-cluster-id"
   WAREHOUSE_ID = "your-warehouse-id"
   ```
4. Run all cells!

---

## 📚 What You'll Learn

By the end, you'll know how to:

✅ Create LangChain Tools from Databricks services  
✅ Build a sequential agent (fixed workflow)  
✅ Build a LangGraph ReAct agent (adaptive)  
✅ Compare approaches and measure savings  
✅ Deploy to production with Asset Bundles  

---

## 🎓 Learning Path

### Level 1: Basics (30 mins)

1. Run setup notebook
2. Test individual tools (Cmd 3-6)
3. Understand tool structure

### Level 2: Agents (60 mins)

4. Build sequential agent (Cmd 7-10)
5. Build ReAct agent (Cmd 11-14)
6. Compare results (Cmd 15)

### Level 3: Advanced (30 mins)

7. Read architecture docs
8. Customize for your use case
9. Deploy to production

---

## 📖 Documentation Index

| Document | Purpose | When to Read |
|----------|---------|--------------|
| [`QUICK_START.md`](QUICK_START.md) | This file - fast setup | First (you're here!) |
| [`BEGINNER_TUTORIAL.md`](BEGINNER_TUTORIAL.md) | Complete guide from scratch | If new to everything |
| [`DEPLOYMENT_GUIDE.md`](DEPLOYMENT_GUIDE.md) | Databricks Asset Bundles | When deploying |
| [`README.md`](README.md) | Project overview | For project details |
| [`docs/LANGRAPH_FOR_FRIENDS.md`](docs/LANGRAPH_FOR_FRIENDS.md) | Simplified concepts | For quick understanding |
| [`docs/LANGRAPH_ARCHITECTURE.md`](docs/LANGRAPH_ARCHITECTURE.md) | Deep technical dive | For production use |
| [`docs/LANGRAPH_BIND_TOOLS_EXPLAINED.md`](docs/LANGRAPH_BIND_TOOLS_EXPLAINED.md) | Critical pattern | If you get errors |

---

## 🐛 Troubleshooting

### "Cluster not found"
→ Update `cluster_id` in databricks.yml and notebook

### "Function ai_classify not found"
→ Run `setup_uc_functions.py` notebook first

### "XML format error"
→ Make sure you're using `llm.bind_tools(tools)` pattern

### "Bundle validation failed"
→ Check YAML syntax and required fields in databricks.yml

**More help**: See [Troubleshooting section](BEGINNER_TUTORIAL.md#troubleshooting) in full tutorial

---

## 🔗 Quick Links

- **Tutorial Notebook**: `tutorial/23_langraph_agent_learning.py`
- **Setup Notebook**: `setup_uc_functions.py`
- **Configuration**: `databricks.yml`
- **GitHub Issues**: [Report problems](https://github.com/bigdatavik/databricks-ai-ticket-vectorsearch/issues)
- **Main Project**: [Full production app](https://github.com/bigdatavik/databricks-ai-ticket-vectorsearch)

---

## 🎯 Next Steps

After completing the tutorial:

1. ⭐ **Star the repo** if helpful!
2. 🔄 **Switch to main branch** to see production app:
   ```bash
   git checkout main
   ```
3. 🛠️ **Build your own agent** for your use case
4. 📝 **Share your experience** - help others learn!

---

## 💬 Need Help?

- **Beginner questions**: Read [`BEGINNER_TUTORIAL.md`](BEGINNER_TUTORIAL.md)
- **Deployment issues**: Read [`DEPLOYMENT_GUIDE.md`](DEPLOYMENT_GUIDE.md)
- **Technical questions**: Check [`docs/`](docs/) folder
- **Bugs/issues**: [Open an issue](https://github.com/bigdatavik/databricks-ai-ticket-vectorsearch/issues)

---

**Ready? Let's build your first LangGraph agent! 🚀**

Start with Step 1 above ⬆️

---

*Updated: November 2024 | Tutorial Version 1.0*

