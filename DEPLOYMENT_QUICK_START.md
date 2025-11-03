# Deployment Quick Start

## Simple 2-Config Approach

This project uses **TWO separate config files** that you swap between:

### Files

- **`databricks.yml`** - Dev config (interactive cluster)
- **`databricks.staging_prod.yml`** - Staging/Prod config (job clusters)

### Scripts

- **`swap_config.sh`** - Switch between configs
- **`deploy.sh`** - Deploy to any environment

---

## Quick Commands

### Deploy to Dev (Fast iteration)

```bash
# Check current config
./swap_config.sh status

# Make sure you're on dev config
./swap_config.sh dev

# Deploy
./deploy.sh dev
```

**Dev uses:**
- Interactive cluster `0304-162117-qgsi1x04` (fast!)
- Full deployment mode (clean slate)
- Catalog: `classify_tickets_new_dev`

---

### Deploy to Staging

```bash
# Switch to staging/prod config
./swap_config.sh staging

# Deploy to staging
./deploy.sh staging
```

**Staging uses:**
- Job cluster (cost-effective, autoscales 1-20)
- Incremental deployment mode
- Catalog: `classify_tickets_new_staging`

---

### Deploy to Prod

```bash
# Make sure you're on staging/prod config
./swap_config.sh status

# Switch if needed
./swap_config.sh staging

# Deploy to prod
./deploy.sh prod
```

**Prod uses:**
- Job cluster (cost-effective, autoscales 1-20)
- Incremental deployment mode
- Catalog: `classify_tickets_new_prod`

---

## How It Works

### 1. Config Swap (`swap_config.sh`)

When you run `./swap_config.sh dev`:
- Backs up current `databricks.yml` to `databricks.staging_prod.yml`
- Restores dev config from backup (or keeps it if already on dev)

When you run `./swap_config.sh staging`:
- Backs up current `databricks.yml` to `databricks.dev.backup.yml`
- Copies `databricks.staging_prod.yml` to `databricks.yml`

### 2. Deployment (`deploy.sh`)

The deploy script:
1. Cleans bundle cache (prevents conflicts)
2. Deploys bundle (uploads notebooks, app code)
3. Runs infrastructure job (sets up catalog, tables, functions, Vector Search)
4. Deploys Streamlit app (creates service principal)
5. Grants permissions (runs in infrastructure job)

---

## Why This Approach?

**Previous approach:** Multi-target YAML with complex overrides
- ❌ Environment variable confusion
- ❌ Bundle cache conflicts
- ❌ Path mismatch errors
- ❌ Hard to debug

**New approach:** Simple config swap
- ✅ Only ONE `databricks.yml` at a time
- ✅ No environment variables
- ✅ No cache conflicts
- ✅ Clear and explicit

---

## Troubleshooting

### Check which config is active
```bash
./swap_config.sh status
```

### Switch back to dev
```bash
./swap_config.sh dev
```

### Clean bundle cache manually
```bash
rm -rf .databricks/bundle/*
```

### Verify databricks.yml content
```bash
head -20 databricks.yml
```

---

## File Locations

### Config Files
- `databricks.yml` - Active config (changes based on swap)
- `databricks.staging_prod.yml` - Staging/prod backup
- `databricks.dev.backup.yml` - Dev backup (created when switching)
- `databricks.yml.old` - Original multi-target config (backup)

### Scripts
- `swap_config.sh` - Config switcher
- `deploy.sh` - Deployment script

---

## Next Steps After Deployment

1. **Check app status** in Databricks Apps UI
2. **Test the dashboard** - click the app URL
3. **Verify permissions** - app should have access to catalog
4. **Test classification** - try sample tickets in the dashboard

---

## Need Help?

Run status check:
```bash
./swap_config.sh status
```

View deployment logs in Databricks:
- Go to **Workflows** → Find your job → View run details

