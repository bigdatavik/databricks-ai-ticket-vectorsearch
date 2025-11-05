# Local Development Files

This folder contains files for **local development only**. These are NOT deployed to Databricks Apps.

## Files

### app_simple.py
- **Purpose:** Local version of the dashboard for laptop development
- **Authentication:** Uses `~/.databrickscfg` profile (not service principal)
- **Usage:** For testing changes locally before deploying to Databricks Apps
- **Note:** Does NOT include the AI Agent Assistant tab (Genie integration)

### run_local.py
- **Purpose:** Helper script to run the local dashboard
- **What it does:**
  - Sets `DATABRICKS_CONFIG_PROFILE` environment variable
  - Runs Streamlit with `app_simple.py`
  - Opens on http://localhost:8501

## How to Use

### Running Locally

```bash
cd dashboard/local_dev
python run_local.py
```

Or directly with Streamlit:

```bash
cd dashboard/local_dev
streamlit run app_simple.py --server.port=8501
```

### Requirements

1. **Databricks config file:** `~/.databrickscfg` with a valid profile (e.g., `DEFAULT_azure`)
2. **Python packages:** Install from `../requirements.txt`

```bash
pip install -r ../requirements.txt
```

3. **Permissions:** Your user account needs access to:
   - Unity Catalog: `classify_tickets_new_dev.support_ai`
   - Vector Search endpoint: `one-env-shared-endpoint-2`
   - SQL Warehouse (for Vector Search queries)

## Production vs Local

| Feature | Production (`app_databricks.py`) | Local (`app_simple.py`) |
|---------|----------------------------------|-------------------------|
| **Authentication** | Service Principal (automatic) | User config (`~/.databrickscfg`) |
| **Location** | Databricks Apps | Your laptop |
| **AI Agent Tab** | ✅ Included (with Genie) | ❌ Not included |
| **Configuration** | `app.yaml` env vars | Environment variables or defaults |
| **Deployment** | `databricks bundle deploy` | `python run_local.py` |

## Why Separated?

- **Production focus:** Keep `dashboard/` clean with only production files
- **Future work:** Local dev version needs updates to match production features
- **Development cycle:** Test locally → Deploy to Databricks Apps
- **Clarity:** Clear separation between what's deployed vs. what's for local testing

## TODO: Update Local Version

The local version (`app_simple.py`) is currently missing:
- 🤖 AI Agent Assistant tab (4-step pipeline with Genie)
- 📊 Latest UI improvements
- 🔧 Recent bug fixes and optimizations

Consider syncing features from `app_databricks.py` when working on local development.

---

**Last Updated:** November 2025
**Status:** For Local Development - Not Deployed

