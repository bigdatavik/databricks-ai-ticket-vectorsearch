# POC Archive - Exploratory Notebooks

This folder contains proof-of-concept and exploratory notebooks that were used during development but are **NOT part of the production deployment**.

## Archived Notebooks

### 19_create_ticket_history_poc.py
- **Purpose:** One-time setup to create sample `ticket_history` table with 30 resolved tickets
- **Status:** Already executed, data exists in `classify_tickets_new_dev.support_ai.ticket_history`
- **Used for:** Genie POC testing
- **Note:** This was a one-time data load, not part of regular deployment

### 20_langgraph_poc_with_tools.py
- **Purpose:** LangGraph POC with LangChain Tools (UC Functions, Vector Search, Genie)
- **Status:** Exploration completed, NOT integrated into production
- **Key Finding:** LangGraph adds complexity and latency for our use case
- **Decision:** Implemented direct API approach in dashboard instead

### 21_test_tools_step_by_step.py
- **Purpose:** Step-by-step testing of individual components
- **Status:** Used for debugging during development
- **Tests:** Package installation, UC Functions, Vector Search, Genie, LangChain Tools
- **Note:** Useful reference for troubleshooting

### 22_fixed_agent_with_genie.py
- **Purpose:** Final POC validation with proper Genie Conversation API integration
- **Status:** Concept successfully integrated into production dashboard
- **Key Learnings:** Documented critical bugs and fixes (warehouse ID, attachment_id field, response wrapper)
- **Production Code:** See `dashboard/app_databricks.py` - AI Agent Assistant tab

## Why These Were Archived

1. **LangGraph exploration:** Decided against framework-based approach for current use case
   - Simpler direct API approach is faster and more maintainable
   - May revisit for future enhancements (conditional routing, conversational interface)

2. **POC/Testing nature:** These notebooks served their purpose during R&D phase
   - Valuable learnings were extracted and documented
   - Core concepts integrated into production dashboard
   - Keeping for reference but not part of deployment pipeline

3. **One-time setup:** Notebook 19 was a data load script, not needed for regular operations

## Production Notebooks

For active notebooks used in deployment, see parent `notebooks/` folder. The deployment pipeline is defined in `databricks.yml`.

## Reference Documentation

- **Architecture & Decisions:** `MY_ENVIRONMENT_AI_TICKET_LESSONS.md`
- **Production Dashboard:** `dashboard/app_databricks.py`
- **Genie Integration Details:** `MY_ENVIRONMENT_AI_TICKET_LESSONS.md` - Section "Genie API Integration"

---

**Last Updated:** November 2025
**Status:** Archive - Reference Only

