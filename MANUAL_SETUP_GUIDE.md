# 🚀 Manual Setup Guide - Run Notebooks in Databricks UI

## ⚠️ Important: CLI Execution Has Issues

The notebooks have path dependencies that don't work well with CLI automation.
**SOLUTION**: Run them manually in the Databricks UI where relative paths work correctly.

---

## ✅ What's Already Done:

1. ✅ **Bundle Deployed** to workspace
2. ✅ **Catalog Created**: `langtutorial_vik`
3. ✅ **Permissions Verified**: You can create functions and use AI models
4. ✅ **Knowledge Base Files**: All 12 docs uploaded to workspace

---

## 📍 Where Are Your Files?

**Workspace Location**:
```
/Workspace/Users/vik.malhotra@databricks.com/.bundle/langraph-tutorial/dev/files/
```

**Direct Link**:
https://adb-984752964297111.11.azuredatabricks.net/workspace/984752964297111/folders/2640373444649934

---

## 🎯 Step-by-Step: Run Setup Notebooks

### 1. Open Databricks Workspace

Go to: https://adb-984752964297111.11.azuredatabricks.net

### 2. Navigate to Notebooks

Click: **Workspace** → **Users** → **vik.malhotra@databricks.com** → **.bundle** → **langraph-tutorial** → **dev** → **files** → **notebooks**

### 3. Attach Cluster to All Notebooks

- Cluster ID: `0304-162117-qgsi1x04`
- For each notebook, click the cluster dropdown at top and select this cluster

### 4. Run Notebooks in This Order

#### ✅ Notebook 1: setup_catalog_schema
**Status**: Already completed via CLI ✅

**What it created**:
- Catalog: `langtutorial_vik`
- Schema: `agents`
- Volume: `knowledge_docs`

**Skip this one** - already done!

---

#### 🔧 Notebook 2: setup_uc_functions

**What it does**: Creates 3 AI functions
- `ai_classify()` - Classifies tickets
- `ai_extract()` - Extracts metadata
- `ai_gen()` - Generates responses

**How to run**:
1. Open the notebook
2. Click **"Run All"** at the top
3. Wait ~2 minutes for all cells to complete
4. Verify you see: "✅ All functions created and tested successfully!"

**If it fails**:
- Check the error message in the last cell
- Common issue: Model access (should be fixed now)
- Try running cell-by-cell to see which one fails

---

#### 📚 Notebook 3: setup_knowledge_base

**What it does**: 
- Reads 12 IT support docs from `knowledge_base/` folder
- Uploads them to UC Volume
- Creates Delta table `langtutorial_vik.agents.knowledge_base`

**How to run**:
1. Open the notebook
2. Click **"Run All"**
3. Wait ~2-3 minutes
4. Verify you see: "✅ Uploaded 12 documents"

**Expected output**:
- Table with 12 rows
- Each row has: title, content, doc_id, category

---

#### 🔍 Notebook 4: setup_vector_search

**What it does**:
- Creates or reuses vector endpoint: `one-env-shared-endpoint-2`
- Creates vector index: `langtutorial_vik.agents.knowledge_base_index`
- Embeds all knowledge base documents

**How to run**:
1. Open the notebook
2. Click **"Run All"**
3. **BE PATIENT**: Endpoint creation takes 10-15 minutes if new
4. Verify you see: "✅ Vector search index created and syncing"

**Note**: If endpoint already exists, this will be much faster (~2 min)

---

#### 🎫 Notebook 5: setup_ticket_history

**What it does**:
- Creates table: `langtutorial_vik.agents.ticket_history`
- Inserts 50+ sample support tickets
- Used for Genie queries

**How to run**:
1. Open the notebook
2. Click **"Run All"**
3. Wait ~1 minute
4. Verify you see: "✅ Created 50+ sample tickets"

---

### 5. Create Genie Space (Manual - Cannot Automate)

**After notebook 5 completes**:

1. **Go to Genie** (click Genie in left sidebar)
2. **Click** "Create Genie Space"
3. **Name**: "LangGraph Tutorial - Ticket History"
4. **Data Source**: Select `langtutorial_vik.agents.ticket_history`
5. **Click** "Create"
6. **IMPORTANT**: Copy the Space ID from the URL
   - URL will look like: `.../#genie/spaces/01abc123-...`
   - Copy the ID part: `01abc123-...`

---

### 6. Update Tutorial Notebook

1. **Open**: `notebooks/23_langraph_agent_learning`
2. **Find** the configuration cell (around line 150)
3. **Update** this line:
   ```python
   GENIE_SPACE_ID = "PASTE-YOUR-GENIE-SPACE-ID-HERE"
   ```
4. **Paste** the Genie Space ID you copied
5. **Save** the notebook (Cmd+S or Ctrl+S)

---

### 7. Run the Tutorial! 🎓

1. **Open**: `notebooks/23_langraph_agent_learning`
2. **Attach** cluster: `0304-162117-qgsi1x04`
3. **Option A**: Click **"Run All"** to run everything
4. **Option B**: Run cell-by-cell to learn as you go (recommended!)

**What you'll learn**:
- Creating LangChain tools from Databricks services
- Building sequential agents
- Building LangGraph ReAct agents
- Using `bind_tools()` (critical pattern!)
- Comparing approaches and cost savings

---

## 📊 Summary of Resources Created

| # | Notebook | Resource | Full Name |
|---|----------|----------|-----------|
| 1 | setup_catalog_schema | Catalog | `langtutorial_vik` |
| 1 | setup_catalog_schema | Schema | `langtutorial_vik.agents` |
| 1 | setup_catalog_schema | Volume | `langtutorial_vik.agents.knowledge_docs` |
| 2 | setup_uc_functions | Function | `langtutorial_vik.agents.ai_classify()` |
| 2 | setup_uc_functions | Function | `langtutorial_vik.agents.ai_extract()` |
| 2 | setup_uc_functions | Function | `langtutorial_vik.agents.ai_gen()` |
| 3 | setup_knowledge_base | Table | `langtutorial_vik.agents.knowledge_base` |
| 4 | setup_vector_search | Endpoint | `one-env-shared-endpoint-2` |
| 4 | setup_vector_search | Index | `langtutorial_vik.agents.knowledge_base_index` |
| 5 | setup_ticket_history | Table | `langtutorial_vik.agents.ticket_history` |
| Manual | Genie UI | Genie Space | (You'll create this) |

---

## ⏱️ Estimated Time

- **Notebook 2-5**: 20-30 minutes total
- **Genie Space**: 2 minutes
- **Tutorial notebook**: 2-3 hours (learning experience)

**Total**: ~3-4 hours for complete setup + learning

---

## 🐛 Troubleshooting

### If a notebook fails:

1. **Read the error message** carefully
2. **Check the cell** that failed
3. **Common issues**:
   - Model not accessible → Check serving endpoints
   - Permission denied → Check catalog ownership
   - Path not found → Make sure previous notebooks completed
   - Timeout → Increase timeout or run cell-by-cell

### To start over:

```sql
-- Drop everything and start fresh
DROP CATALOG IF EXISTS langtutorial_vik CASCADE;
```

Then run notebooks 1-5 again.

---

## ✅ Verification Queries

After running all notebooks, verify in SQL:

```sql
-- Check catalog
SHOW CATALOGS LIKE 'langtutorial_vik';

-- Check functions
SHOW FUNCTIONS IN langtutorial_vik.agents;

-- Check tables
SHOW TABLES IN langtutorial_vik.agents;

-- Check knowledge base
SELECT COUNT(*) FROM langtutorial_vik.agents.knowledge_base;
-- Should return: 12

-- Check ticket history
SELECT COUNT(*) FROM langtutorial_vik.agents.ticket_history;
-- Should return: 50+

-- Test a function
SELECT langtutorial_vik.agents.ai_classify('User cannot access database');
```

---

## 🎯 Next Action

**START HERE**: 

1. Open Databricks: https://adb-984752964297111.11.azuredatabricks.net
2. Navigate to: Workspace → Users → vik.malhotra@databricks.com → .bundle → langraph-tutorial → dev → files → **notebooks**
3. Open **setup_uc_functions** (skip #1, it's done)
4. Click **"Run All"**

---

**Good luck! 🚀**
