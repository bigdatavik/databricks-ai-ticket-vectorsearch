# Learning / Experimental Notebooks

This directory contains notebooks used for learning, experimentation, and prototyping new features. These are not part of the production deployment.

## Contents

### LangGraph Agent Learning

- **`23_langraph_agent_learning.py`** - Interactive learning notebook for LangGraph ReAct agents
  - **Purpose:** Learn and test LangGraph patterns before implementing in production
  - **Status:** Experimental (branch: `agent_langraph_trying`)
  - **Features:**
    - Tests all 4 tools individually (UC Functions, Vector Search, Genie)
    - Wraps them as LangChain Tools
    - Creates LangGraph ReAct Agent
    - Compares Sequential vs Agent approaches
  - **Note:** This notebook helped develop the patterns now used in the dashboard's AI Agent Assistant

## Usage

These notebooks are for:
- ✅ Learning new technologies and patterns
- ✅ Prototyping features before production implementation
- ✅ Testing integrations and debugging
- ✅ Educational purposes and documentation

**Not included in:**
- Production deployments (`databricks.yml`)
- Automated test suites
- CI/CD pipelines

## Reference Documentation

For production-ready versions and documentation, see:
- `docs/REFERENCE_23_langraph_agent_learning.py` - Reference implementation
- `docs/LANGRAPH_ARCHITECTURE.md` - Architecture documentation
- `docs/LANGRAPH_BIND_TOOLS_EXPLAINED.md` - Critical patterns explained

