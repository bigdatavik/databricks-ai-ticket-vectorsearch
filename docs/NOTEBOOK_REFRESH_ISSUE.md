# 🐛 Notebook Not Picking Up Changes After Deploy

## Issue

After deploying notebooks to Databricks with `databricks bundle deploy`, the notebook is still showing errors with **XML-format tool calls**, indicating it's using **Meta Llama** instead of **Claude Sonnet 4**.

**Error seen:**
```
BadRequestError: Error code: 400
Model Output: <function=search_knowledge>{"query": "database connection timeout resolution"}</function>
```

This is the XML format from **Meta Llama models**, but the code clearly shows:
```python
LLM_ENDPOINT = "databricks-claude-sonnet-4"  # Line 140
```

---

## Root Cause

**Databricks notebooks cache code and don't automatically reload after deployment!**

When you run `databricks bundle deploy`:
- ✅ Files ARE uploaded to Databricks workspace
- ❌ Running notebooks DO NOT automatically reload
- ❌ Python kernel keeps old variables in memory
- ❌ Old `LLM_ENDPOINT` value still active

---

## Solution: 3 Options

### **Option 1: Detach & Reattach Notebook (Recommended)** ✅

**In Databricks UI:**

1. Go to your notebook: `notebooks/23_langraph_agent_learning.py`
2. Click the cluster dropdown at top right
3. Click **"Detach"**
4. Wait 5 seconds
5. Click **"Attach"** and select your cluster
6. Run cells from the beginning

**Why this works:**
- Clears Python kernel memory
- Reloads all variables
- Picks up new `LLM_ENDPOINT` value

---

### **Option 2: Restart Cluster** 🔄

**In Databricks UI:**

1. Go to **Compute** in left sidebar
2. Find your cluster
3. Click **"Restart"**
4. Wait for cluster to come back online (~2-3 minutes)
5. Re-run your notebook

**Why this works:**
- Complete cluster restart
- Fresh Python environment
- All notebooks reload

**Downside:**
- Takes longer (cluster startup time)
- Affects all notebooks using that cluster

---

### **Option 3: Clear State & Re-run** 🧹

**In Databricks UI:**

1. In your notebook, click **"Clear"** → **"Clear State & Outputs"**
2. Re-run cells from the beginning (Run All)

**Why this works:**
- Clears all variables in notebook state
- Forces re-execution of all code
- Picks up new configuration

**Note:** This only works if the notebook file itself was refreshed (see Option 1 if this doesn't work)

---

## How to Verify It's Fixed

### **Step 1: Check Configuration Loading**

Run the configuration cell and verify output shows:
```
✅ Configuration loaded
  📚 Catalog: classify_tickets_new_dev
  📊 Schema: support_ai
  🔍 Vector Index: classify_tickets_new_dev.support_ai.knowledge_base_index
  💬 Genie Space: 01f0b91aa91c1b0c8cce6529ea09f0a8
  🤖 LLM: databricks-claude-sonnet-4  ← CHECK THIS!
```

**If you see:**
- ✅ `databricks-claude-sonnet-4` → Correct!
- ❌ `databricks-meta-llama-3-1-8b-instruct` → Still using old version

---

### **Step 2: Check LLM Initialization**

After running the LLM initialization cell, verify:
```
✅ LLM initialized: databricks-claude-sonnet-4  ← CHECK THIS!
```

---

### **Step 3: Run Test 2 Again**

The critical production issue test should now:
- ✅ Use proper JSON format for tool calls
- ✅ No BAD_REQUEST errors
- ✅ Successfully complete with 3-4 tool calls

**Before (Broken):**
```
BadRequestError: Error code: 400
Model Output: <function=search_knowledge>{...}</function>
```

**After (Fixed):**
```
🔧 Tool call 1: classify_ticket
✅ Tool result received
🔧 Tool call 2: search_knowledge
✅ Tool result received
🧠 Agent reasoning: Based on the classification...
```

---

## Why This Happens

### **Databricks Notebook Execution Model:**

1. **File Upload (Deploy):**
   - `databricks bundle deploy` uploads new file versions
   - Files stored in workspace filesystem

2. **Notebook Runtime:**
   - When notebook is attached to cluster, it loads file into memory
   - Python kernel caches variables and imports
   - **Running notebooks don't auto-reload when files change**

3. **Variable Persistence:**
   - Once `LLM_ENDPOINT = "..."` is executed, it stays in memory
   - Subsequent file changes don't update existing variable
   - Need to detach/reattach or restart to clear memory

**This is BY DESIGN** - prevents running notebooks from suddenly changing behavior mid-execution!

---

## Best Practice: Deployment Workflow

### **Correct Workflow:**

```bash
# 1. Make changes locally
vim notebooks/23_langraph_agent_learning.py

# 2. Commit changes
git add notebooks/
git commit -m "Update LLM endpoint"

# 3. Deploy to Databricks
databricks bundle deploy --profile DEFAULT

# 4. In Databricks UI:
#    - Detach & reattach notebook
#    OR
#    - Clear state & re-run
#    OR  
#    - Restart cluster

# 5. Run from beginning
#    - Execute cells in order
#    - Verify configuration output
#    - Test functionality
```

### **Common Mistakes:**

❌ **Deploy but don't refresh:**
```bash
databricks bundle deploy  # ✅ Files uploaded
# Run notebook cells      # ❌ Still using old code!
```

❌ **Only re-run test cells:**
```bash
databricks bundle deploy
# Run only test cells     # ❌ Old LLM_ENDPOINT still in memory!
```

✅ **Correct approach:**
```bash
databricks bundle deploy
# Detach & reattach OR Clear state & re-run
# Run ALL cells from beginning
```

---

## Dashboard vs Notebook Difference

### **Why Dashboard Works:**

**Dashboard (Streamlit on Databricks Apps):**
- App fully restarts when redeployed
- New process with fresh Python environment
- Immediately picks up new code
- No caching issues

**Workflow:**
```bash
databricks bundle deploy
databricks apps restart classify-tickets-dashboard-dev
# ✅ New code active immediately!
```

### **Why Notebook Needs Manual Refresh:**

**Notebook (Running on Cluster):**
- Maintains persistent Python kernel
- Variables cached in memory
- File changes don't auto-reload
- Need manual refresh

**Workflow:**
```bash
databricks bundle deploy
# ❌ Notebook still using old code!
# ✅ Must detach/reattach or clear state
```

---

## Quick Reference

### **Symptoms of This Issue:**

🔴 **XML format errors** (Llama) when code shows Claude:
```
Model Output: <function=search_knowledge>...
```

🔴 **Wrong model in error messages:**
- Error mentions Llama behavior
- Code clearly shows Claude Sonnet 4

🔴 **Dashboard works, notebook doesn't:**
- Same code
- Different behavior

### **Quick Fix:**

1. **Detach & Reattach** notebook (30 seconds)
2. **Re-run ALL cells** from beginning
3. **Verify** configuration output shows Claude

### **When to Use Each Solution:**

| Issue | Solution |
|-------|----------|
| Just deployed, notebook running | Detach & reattach |
| Multiple notebooks affected | Restart cluster |
| Single notebook, quick fix | Clear state & re-run |
| Persistent cache issues | Restart cluster |

---

## Prevention for Future

### **Add Verification Cell at Top:**

Add this as the **first code cell** after configuration:

```python
# VERIFICATION: Check we're using correct configuration
print("=" * 80)
print("🔍 CONFIGURATION VERIFICATION")
print("=" * 80)
print(f"✅ LLM Endpoint: {LLM_ENDPOINT}")
print(f"✅ Expected: databricks-claude-sonnet-4")
print(f"✅ Match: {LLM_ENDPOINT == 'databricks-claude-sonnet-4'}")
print("=" * 80)

if LLM_ENDPOINT != "databricks-claude-sonnet-4":
    raise ValueError(
        f"❌ WRONG MODEL! Using {LLM_ENDPOINT} instead of Claude Sonnet 4!\n"
        f"   → Detach & reattach notebook, then re-run from beginning"
    )
```

This will **immediately fail** if the old configuration is still in memory!

---

## Summary

**Problem:** Notebook cache showing XML errors (Llama) despite code showing Claude

**Root Cause:** Databricks notebooks don't auto-reload after deployment

**Solution:** Detach & reattach notebook (or restart cluster)

**Verification:** 
- Configuration output shows `databricks-claude-sonnet-4`
- Tests complete without BAD_REQUEST errors
- No XML-format tool calls in errors

**Prevention:** Add verification cell to catch this early

---

**Status:** 🔧 **Awaiting notebook refresh in Databricks**

Once you detach & reattach, the notebook will work exactly like the dashboard! ✅

