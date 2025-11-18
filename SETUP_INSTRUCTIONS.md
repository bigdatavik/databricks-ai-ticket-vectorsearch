# 🚀 LangGraph Tutorial - Complete Setup Instructions

**Comprehensive guide to set up the standalone tutorial environment**

---

## 📋 Overview

This tutorial creates a **completely independent** environment for learning LangGraph on Databricks:
- Separate catalog: `langtutorial`
- Own schema, tables, and functions
- No conflicts with other projects
- Can be torn down safely

**Total Setup Time**: 30-45 minutes

---

## ✅ Prerequisites

Before you begin, ensure you have:

- [ ] Databricks workspace access (Azure, AWS, or GCP)
- [ ] Unity Catalog enabled
- [ ] Cluster running (any size, Runtime 16.4 LTS+)
- [ ] Permissions to:
  - CREATE CATALOG
  - CREATE SCHEMA
  - CREATE FUNCTION
  - CREATE VOLUME
  - Create Vector Search endpoints (or use existing)
- [ ] SQL Warehouse ID (find in SQL Warehouses → click warehouse → copy ID from URL)
- [ ] Cluster ID (find in Compute → click cluster → copy ID from URL)

---

## 🎯 Setup Steps (In Order!)

### Step 0: Upload Setup Notebooks

**Upload these files to your Databricks workspace:**
1. `setup_catalog_schema.py`
2. `setup_uc_functions.py`
3. `setup_knowledge_base.py`
4. `setup_vector_search.py`
5. `setup_ticket_history.py`
6. `tutorial/23_langraph_agent_learning.py`

**Upload `knowledge_base/` folder** to your workspace (needed for Step 3)

---

### Step 1: Create Catalog and Schema ⏱️ 1 minute

**Notebook**: `setup_catalog_schema.py`

**What it does**:
- Creates catalog: `langtutorial`
- Creates schema: `agents`
- Creates volume: `knowledge_docs`

**Run it**:
1. Open `setup_catalog_schema.py` in Databricks
2. Attach to your cluster
3. Click "Run All"
4. Wait for completion (~30 seconds)

**Expected output**:
```
✅ Catalog 'langtutorial' is ready
✅ Schema 'agents' is ready
✅ Volume 'knowledge_docs' is ready
```

**Troubleshooting**:
- ❌ "Permission denied": Ask admin for CREATE CATALOG permission
- ❌ "Catalog already exists": OK, continue to next step

---

### Step 2: Create UC AI Functions ⏱️ 2 minutes

**Notebook**: `setup_uc_functions.py`

**What it does**:
- Creates `ai_classify()` - Classifies tickets by priority/category
- Creates `ai_extract()` - Extracts metadata from text
- Creates `ai_gen()` - Generates helpful responses

**Run it**:
1. Open `setup_uc_functions.py`
2. Attach to your cluster
3. **Verify** CATALOG is set to `langtutorial` (line 34)
4. Click "Run All"
5. Wait for tests to pass

**Expected output**:
```
✅ Created ai_classify() function
✅ Created ai_extract() function
✅ Created ai_gen() function
Test result: priority: "P1", category: "Database"
```

**Troubleshooting**:
- ❌ "Function not found": Re-run Step 1 first
- ❌ "LLM not available": Model may not be enabled in workspace, contact admin

---

### Step 3: Upload Knowledge Base ⏱️ 2-3 minutes

**Notebook**: `setup_knowledge_base.py`

**What it does**:
- Uploads 12 knowledge base documents to UC Volume
- Creates Delta table: `langtutorial.agents.knowledge_base`
- Parses and inserts documents (12 docs)

**Run it**:
1. Open `setup_knowledge_base.py`
2. Attach to your cluster
3. Click "Run All"
4. Monitor upload progress

**Expected output**:
```
✅ Loaded 12 knowledge base files
✅ Uploaded: IT_infrastructure_runbook.txt
✅ Uploaded: database_admin_guide.txt
...
✅ Inserted 12 documents into langtutorial.agents.knowledge_base
```

**Troubleshooting**:
- ❌ "knowledge_base folder not found": Ensure folder is uploaded to workspace
- ❌ "Volume not found": Re-run Step 1 first

---

### Step 4: Create Vector Search Index ⏱️ 10-20 minutes

**Notebook**: `setup_vector_search.py`

**What it does**:
- Checks if endpoint `one-env-shared-endpoint-2` exists
- If not exists: Creates endpoint (takes 10-15 min)
- If exists: Reuses endpoint (instant)
- Creates vector search index: `langtutorial.agents.knowledge_base_index`
- Triggers initial sync to embed documents

**Run it**:
1. Open `setup_vector_search.py`
2. Attach to your cluster
3. Click "Run All"
4. **Be patient**: Endpoint creation can take 10-15 minutes

**Expected output**:
```
✅ Endpoint exists: one-env-shared-endpoint-2
   Status: ONLINE
✅ Change Data Feed enabled
✅ Index created successfully
✅ Sync triggered successfully
✅ Index is queryable! Found 3 results
```

**Troubleshooting**:
- ❌ "Permission denied creating endpoint": Ask admin to create endpoint OR use existing endpoint
- ❌ "Table not found": Re-run Step 3 first
- ⏳ "Endpoint creating...": This is normal, wait 10-15 minutes
- ⚠️ "No results yet": Embeddings still processing, wait 5 more minutes

---

### Step 5: Create Historical Tickets ⏱️ 1 minute

**Notebook**: `setup_ticket_history.py`

**What it does**:
- Creates table: `langtutorial.agents.ticket_history`
- Inserts 50+ resolved historical tickets
- Different categories: Database, Network, Access, Security, etc.
- Different priorities: P1 (Critical) to P4 (Low)

**Run it**:
1. Open `setup_ticket_history.py`
2. Attach to your cluster
3. Click "Run All"

**Expected output**:
```
✅ Table created: langtutorial.agents.ticket_history
✅ Generated 50 sample tickets
✅ Inserted 50 records into langtutorial.agents.ticket_history
```

**Troubleshooting**:
- ❌ "Schema not found": Re-run Step 1 first

---

### Step 6: Create Genie Space (Manual) ⏱️ 2 minutes

**This step is MANUAL** (cannot be automated via notebook)

**Instructions**:

1. **Open Genie in Databricks**:
   - Click **Genie** in left sidebar (or search "Genie" in command palette)

2. **Create New Space**:
   - Click **"Create Genie Space"** button
   - If you don't see this, ask admin for Genie access

3. **Configure Space**:
   - **Name**: `LangGraph Tutorial - Ticket History`
   - **Description**: `Historical support tickets for LangGraph tutorial queries`
   - **Data Source**: Click "Select tables"
     - Navigate to: `langtutorial` → `agents` → `ticket_history`
     - Select the table
     - Click "Add"

4. **Create and Copy ID**:
   - Click **"Create"**
   - Wait for space to be created (30 seconds)
   - **IMPORTANT**: Copy the **Space ID** from the URL
   - URL looks like: `.../genie/spaces/01abc123def456...`
   - Space ID is the part after `/spaces/`: `01abc123def456...`

5. **Save Space ID**:
   - Write it down or paste into a text file
   - You'll need it for Step 7

**Expected result**:
```
Space created: LangGraph Tutorial - Ticket History
Space ID: 01abc123def456... (32 character hex string)
```

**Troubleshooting**:
- ❌ "Genie not available": Your workspace may not have Genie enabled, contact admin
- ❌ "Table not found": Re-run Step 5 first
- ❌ "Permission denied": Ask admin for Genie space creation permission

**Alternative**: If Genie is not available, you can skip this and test the tutorial with only 3 tools (classify, extract, search) instead of 4.

---

### Step 7: Update Tutorial Notebook Configuration ⏱️ 1 minute

**Notebook**: `tutorial/23_langraph_agent_learning.py`

**What to do**:
1. Open `tutorial/23_langraph_agent_learning.py`
2. Find the configuration cell (Cmd 2, around line 150)
3. Update these values:

```python
# Configuration - Tutorial environment
CATALOG = "langtutorial"  # Already set
SCHEMA = "agents"  # Already set
WAREHOUSE_ID = "your-warehouse-id"  # ← PASTE YOUR WAREHOUSE ID HERE
INDEX_NAME = f"{CATALOG}.{SCHEMA}.knowledge_base_index"  # Already set
GENIE_SPACE_ID = "your-genie-space-id"  # ← PASTE SPACE ID FROM STEP 6 HERE
```

**How to find Warehouse ID**:
- Go to **SQL Warehouses** in Databricks
- Click on your warehouse
- Copy ID from URL: `.../sql/warehouses/abc123...`
- Warehouse ID = `abc123...`

**Save the notebook** (Ctrl+S or Cmd+S)

---

### Step 8: Run Tutorial Notebook! 🎉 ⏱️ 10-15 minutes

**Notebook**: `tutorial/23_langraph_agent_learning.py`

**You're ready to learn!**

1. Open `tutorial/23_langraph_agent_learning.py`
2. Attach to your cluster
3. Start from **Cmd 1** (top)
4. Run cells one by one (or "Run All")
5. Follow along with the tutorial

**What you'll learn**:
- How to create LangChain Tools
- How to wrap Databricks services (UC Functions, Vector Search, Genie)
- How to build a sequential agent
- How to build a LangGraph ReAct agent
- How to compare approaches
- Best practices and patterns

---

## 📊 Verification Checklist

After completing all steps, verify your setup:

### Resources Created

- [ ] Catalog: `langtutorial` exists
- [ ] Schema: `langtutorial.agents` exists
- [ ] Volume: `langtutorial.agents.knowledge_docs` exists (with 12 files)
- [ ] Function: `langtutorial.agents.ai_classify()` exists
- [ ] Function: `langtutorial.agents.ai_extract()` exists
- [ ] Function: `langtutorial.agents.ai_gen()` exists
- [ ] Table: `langtutorial.agents.knowledge_base` exists (12 rows)
- [ ] Table: `langtutorial.agents.ticket_history` exists (50+ rows)
- [ ] Vector Index: `langtutorial.agents.knowledge_base_index` exists (ONLINE status)
- [ ] Vector Endpoint: `one-env-shared-endpoint-2` exists (ONLINE status)
- [ ] Genie Space: Created and Space ID copied

### Test Queries

Run these in a SQL notebook to verify:

```sql
-- Test catalog
USE CATALOG langtutorial;
USE SCHEMA agents;

-- Test AI Functions
SELECT ai_classify('URGENT: Database server down!');
SELECT ai_extract('User john@company.com reports error ERR-500');

-- Test knowledge base table
SELECT COUNT(*) FROM knowledge_base;  -- Should return 12

-- Test ticket history table
SELECT COUNT(*) FROM ticket_history;  -- Should return 50+

-- Test vector search index
-- (Run from Python in tutorial notebook)
```

---

## 🐛 Common Issues

### Issue 1: "Permission denied" errors

**Cause**: Insufficient permissions

**Solution**:
1. Contact your Databricks workspace admin
2. Request these permissions:
   - CREATE CATALOG on workspace
   - USE CATALOG on `langtutorial`
   - CREATE SCHEMA on `langtutorial`
   - CREATE FUNCTION on `langtutorial.agents`
   - CREATE VOLUME on `langtutorial.agents`

### Issue 2: Vector endpoint creation stuck

**Cause**: Endpoint creation can take 10-15 minutes

**Solution**:
- Wait patiently, this is normal
- Monitor progress in notebook output
- After 15 minutes, check Vector Search UI in Databricks

**Alternative**:
- Ask admin to create endpoint `one-env-shared-endpoint-2` beforehand

### Issue 3: Knowledge base files not found

**Cause**: `knowledge_base/` folder not uploaded to workspace

**Solution**:
1. Download `knowledge_base/` folder from repository
2. Upload to Databricks workspace (next to the notebook)
3. Or: Deploy using Databricks Asset Bundles (DAB)

### Issue 4: Genie not available

**Cause**: Genie may not be enabled in your workspace

**Solution**:
- Contact admin to enable Genie
- Or: Skip Genie and use tutorial with 3 tools only
- Tutorial will still work, just without historical ticket queries

### Issue 5: "Catalog already exists" on re-run

**Cause**: Setup was run before

**Solution**:
- This is OK! Continue to next step
- Or: Delete and recreate if you want fresh start:
  ```sql
  DROP CATALOG IF EXISTS langtutorial CASCADE;
  ```
  Then re-run all setup notebooks

---

## 🔄 Starting Over (Clean Slate)

If you want to reset and start fresh:

```sql
-- ⚠️ WARNING: This deletes EVERYTHING in the tutorial catalog!

DROP CATALOG IF EXISTS langtutorial CASCADE;
```

Then:
1. Re-run Step 1 through Step 7
2. Vector search endpoint will be reused (not deleted)

---

## 📚 Additional Resources

- **Tutorial Notebook**: `tutorial/23_langraph_agent_learning.py`
- **Beginner Guide**: `BEGINNER_TUTORIAL.md`
- **Quick Start**: `QUICK_START.md`
- **Architecture Docs**: `docs/LANGRAPH_ARCHITECTURE.md`
- **Troubleshooting**: `docs/LANGRAPH_BIND_TOOLS_EXPLAINED.md`

---

## 💬 Getting Help

- **GitHub Issues**: [Report problems](https://github.com/bigdatavik/databricks-ai-ticket-vectorsearch/issues)
- **Databricks Community**: [community.databricks.com](https://community.databricks.com)

---

## ✅ Setup Complete!

If all steps succeeded, you should see:

```
✅ Catalog and schema created
✅ 3 UC Functions created and tested
✅ 12 Knowledge base documents uploaded
✅ Vector search index created and syncing
✅ 50+ Historical tickets created
✅ Genie Space created with Space ID
✅ Tutorial notebook configured
```

**🚀 You're ready to learn LangGraph on Databricks!**

**Next**: Open `tutorial/23_langraph_agent_learning.py` and start the tutorial!

---

*Setup Time: ~30-45 minutes total*  
*Tutorial Time: ~2-3 hours*  
*Total Learning Experience: ~3-4 hours*

