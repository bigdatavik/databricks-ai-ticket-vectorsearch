# Quick Reference Guide

## 🚀 Deployment Commands

### Dev (Fast Iteration)
```bash
./deploy.sh dev
```
- Uses interactive cluster `0304-162117-qgsi1x04`
- Full deployment mode
- Catalog: `classify_tickets_new_dev`

### Staging (Pre-Production)
```bash
./swap_config.sh staging
./deploy.sh staging
```
- Uses job cluster (autoscale 1-20)
- Incremental deployment
- Catalog: `classify_tickets_new_staging`

### Production
```bash
./swap_config.sh staging  # Same config as staging
./deploy.sh prod
```
- Uses job cluster (autoscale 1-20)
- Incremental deployment  
- Catalog: `classify_tickets_new_prod`

## 📁 Project Structure

- `notebooks/` - Deployment notebooks
- `dashboard/` - Streamlit app code
- `knowledge_base/` - Knowledge base documents (auto-discovered)
- `tests/` - Test utilities (not deployed)
- `databricks.yml` - Dev config
- `databricks.staging_prod.yml` - Staging/prod config

### Check Current Config
```bash
./swap_config.sh status
```

### Switch to Dev
```bash
./swap_config.sh dev
```

### Switch to Staging/Prod
```bash
./swap_config.sh staging
```

---

## 📁 File Structure

```
databricks.yml                  # Active config (changes based on swap)
databricks.staging_prod.yml     # Staging/prod backup
swap_config.sh                  # Config switcher
deploy.sh                       # Deployment script
```

---

## 🎯 UC Functions

### Basic Classification
```sql
SELECT ai_classify('Laptop screen flickering');
-- Returns: {category, priority, assigned_team}
```

### Metadata Extraction
```sql
SELECT ai_extract('Cannot access shared drive');
-- Returns: {priority_score, urgency_level, affected_systems, assigned_team}
```

### Summary Generation
```sql
SELECT ai_gen('Printer not working', 'Context from knowledge base');
-- Returns: Summary with recommendations
```

### Quick Classify (All-in-One)
```sql
SELECT quick_classify_ticket('VPN connection keeps dropping');
-- Returns: Complete classification
```

---

## 🔍 Vector Search

### Query Knowledge Base
```python
from databricks.sdk import WorkspaceClient

w = WorkspaceClient()
result = w.api_client.do(
    'POST',
    '/api/2.0/vector-search/indexes/{catalog}.support_ai.knowledge_base_index/query',
    body={
        'columns': ['doc_id', 'doc_type', 'title', 'content'],
        'query_text': 'How to reset password',
        'num_results': 3
    }
)
```

---

## 🐛 Troubleshooting

### Clean Bundle Cache
```bash
rm -rf .databricks/bundle/*
```

### Check App Status
```bash
databricks apps list --profile DEFAULT_azure
databricks apps get classify-tickets-dashboard-dev --profile DEFAULT_azure
```

### Re-grant Permissions
```bash
# Permissions are granted in the infrastructure job
# Re-run the grant_app_permissions task if needed
databricks bundle run setup_infrastructure --profile DEFAULT_azure
```

### View Job Logs
1. Go to Databricks workspace
2. Click **Workflows**
3. Find `[dev] Setup Infrastructure` (or staging/prod)
4. Click on latest run
5. View task logs

---

## 💰 Cost Breakdown

| Phase | Time | Cost |
|-------|------|------|
| ai_classify | 800ms | $0.0004 |
| ai_extract | 1.2s | $0.0005 |
| Vector Search | 200ms | $0.0001 |
| ai_gen | 900ms | $0.0003 |
| Hybrid | 1s | $0.0005 |
| **TOTAL** | **~3s** | **$0.0018** |

---

## 🎨 Dashboard URLs

After deployment, find your app URL:

```bash
databricks apps get classify-tickets-dashboard-dev --profile DEFAULT_azure
```

Or go to: Databricks → **Apps** → Find your app

---

## 📊 Catalogs & Resources

### Dev
- Catalog: `classify_tickets_new_dev`
- Schema: `support_ai`
- Tables: `knowledge_base`, `sample_tickets`, `knowledge_base_index`
- Volume: `knowledge_docs`
- App: `classify-tickets-dashboard-dev`

### Staging
- Catalog: `classify_tickets_new_staging`
- Schema: `support_ai`
- App: `classify-tickets-dashboard-staging`

### Prod
- Catalog: `classify_tickets_new_prod`
- Schema: `support_ai`
- App: `classify-tickets-dashboard-prod`

---

## 🔧 Common Tasks

### Update Knowledge Base
1. Edit files in `knowledge_base/` directory
2. Deploy (will auto-upload and reload)

### Change Cluster ID (Dev)
1. Edit `databricks.yml` line 38
2. Update: `existing_cluster_id: YOUR_CLUSTER_ID`

### Force Full Deployment (Dev)
```bash
# Dev is always full by default
./deploy.sh dev
```

### Force Full Deployment (Staging/Prod)
1. Edit `databricks.staging_prod.yml`
2. Change `deployment_mode: incremental` to `deployment_mode: full`
3. Deploy
4. Change back to `incremental`

---

## 🔐 Permissions Required

The app's service principal needs:
- `USE CATALOG` on catalog
- `USE SCHEMA` on schema
- `SELECT` on tables
- `READ VOLUME` on volume
- `EXECUTE` on UC functions

These are auto-granted by the deployment.

---

## 📞 Support

For issues:
1. Check `./swap_config.sh status`
2. View job logs in Databricks
3. Clean bundle cache: `rm -rf .databricks/bundle/*`
4. Review [DEPLOYMENT_QUICK_START.md](DEPLOYMENT_QUICK_START.md)

---

## ⚡ Quick Tips

- **Dev**: Fast iteration, uses interactive cluster
- **Staging/Prod**: Cost-effective, uses job clusters  
- **Config Swap**: Explicit, no hidden environment variables
- **Cache**: Auto-cleaned by deploy script
- **Permissions**: Auto-granted in infrastructure job
- **Vector Search**: Endpoint shared, never deleted

---

**Need more details?** See [README.md](README.md) or [DEPLOYMENT_QUICK_START.md](DEPLOYMENT_QUICK_START.md)
