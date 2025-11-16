# Scripts Directory

This directory contains utility scripts for project management and deployment.

## Available Scripts

### Deployment Scripts

- **`deploy.sh`** - Main deployment script for Databricks Asset Bundles
  - Validates bundle configuration
  - Deploys to dev environment
  - Runs infrastructure setup job
  - Deploys Streamlit dashboard app
  - Usage: `./scripts/deploy.sh`

- **`swap_config.sh`** - Swap between dev and staging/prod configurations
  - Backs up current `databricks.yml`
  - Swaps to `databricks.staging_prod.yml` or back to dev
  - Usage: `./scripts/swap_config.sh`

### Utility Scripts

- **`check_versions.py`** - Verify notebook versions after deployment
  - Checks if deployed notebooks match local versions
  - Helps debug caching issues
  - Usage: `python scripts/check_versions.py`

- **`git-commit.sh`** - Git commit helper (removes environment files from tracking)
  - Ensures `MY_ENVIRONMENT*.md` files are not committed
  - Commits all other changes
  - Usage: `./scripts/git-commit.sh "commit message"`

## Usage Notes

- Make scripts executable: `chmod +x scripts/*.sh`
- Run from project root: `./scripts/script-name.sh`
- For Python scripts: `python scripts/script-name.py`

