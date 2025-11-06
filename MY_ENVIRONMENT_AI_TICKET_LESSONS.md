# Complete Guide: AI-Powered Support Ticket Classification System

This guide documents EVERYTHING needed to build this project from scratch, including all lessons learned, patterns, and solutions.

---

## 🎯 Quick Start: The Prompt

Want to recreate this exact project using AI assistance? Use this prompt:

### The Complete Prompt

```
BUILD: AI-Powered Support Ticket Classification System

GOAL:
- 95%+ classification accuracy
- <$0.002 cost per ticket  
- <3 second processing time
- Production-ready with Databricks Asset Bundles

USE:
- Unity Catalog AI Functions (ai_classify, ai_extract, ai_gen)
- Vector Search (Delta Sync + BGE embeddings)
- Streamlit Dashboard (local + Databricks Apps)
- Databricks Asset Bundles (DAB) for deployment

ARCHITECTURE:
6-Phase Classification Workflow:
1. Basic Classification (UC Function: ai_classify)
2. Metadata Extraction (UC Function: ai_extract)
3. Vector Search (semantic retrieval)
4. Summary Generation (UC Function: ai_gen)
5. Hybrid Classification (combine all phases)
6. Quick Classify (single function call)

CRITICAL REQUIREMENTS:

🔴 DEPLOYMENT:
- Use 2 separate config files (NOT multi-target with overrides)
- databricks.yml: Dev (interactive cluster, full mode)
- databricks.staging_prod.yml: Staging/Prod (job clusters, incremental)
- swap_config.sh: Switch between configs
- deploy.sh: Simple deployment script
- Clean bundle cache before each deploy

🔴 UC FUNCTIONS:
- Use SQL language (not Python) for built-in AI functions
- String concatenation (||) for prompts (not f-strings in SQL)
- Safe field access: row.get('key', default)
- Always check for None
- Test after deployment

🔴 VECTOR SEARCH:
- Use w.api_client.do() for queries (OAuth M2M)
- TRIGGERED sync (not CONTINUOUS) for cost savings
- Embedding model: databricks-bge-large-en (free)
- Shared endpoint: one-env-shared-endpoint-2 (never delete!)
- Grant SELECT on index table (Delta Sync indexes are tables)
- Wait for index to be ONLINE before syncing

🔴 DATABRICKS APPS:
- Service principals auto-created by Databricks
- Use app.service_principal_client_id (UUID) for grants
- Grant permissions AFTER app deployment
- Minimal app.yaml (platform manages networking)
- Use WorkspaceClient() for OAuth

🔴 KNOWLEDGE BASE:
- 5 documents: IT runbook, app support, security playbook, access policies, classification rules
- Upload to UC Volume
- Chunk semantically (800-1500 chars, paragraph-based)
- Load into Delta table
- Index with Vector Search

🔴 NOTEBOOKS:
Create these 11 notebooks:
1. 00_cleanup_full_mode.py - Clean slate for full deployments
2. 00_setup_catalog_schema.py - Create catalog/schema/volume
3. 01_deploy_uc_function_ai_classify.py - Basic classification
4. 02_deploy_uc_function_ai_extract.py - Metadata extraction
5. 03_deploy_uc_function_ai_gen.py - Summary generation
6. 04_deploy_uc_function_quick_classify.py - All-in-one
7. 06_prepare_sample_tickets.py - Test data
8. 08_grant_app_permissions.py - Service principal permissions
9. 10_upload_knowledge_docs.py - Upload docs to volume
10. 13_reload_kb_with_proper_chunking.py - Chunk and load docs
11. 14_recreate_vector_search_index.py - Create/sync index

🔴 DASHBOARD:
- app_simple.py: Local dev (uses ~/.databrickscfg)
- app_databricks.py: Production (uses WorkspaceClient)
- app.yaml: Minimal config
- requirements.txt: streamlit, databricks-sdk
- Features: 6-phase classification, cost tracking, Vector Search results

AVOID THESE MISTAKES:
❌ Multi-target DAB with overrides (causes cache conflicts)
❌ Environment variables (DATABRICKS_BUNDLE_CONFIG)
❌ Python SDK VectorSearchClient (403 errors)
❌ curl subprocess (auth issues)
❌ Dot notation in UC functions (use .get())
❌ Granting permissions before app exists
❌ Using service principal display name (use UUID)
❌ CONTINUOUS sync mode (expensive)
❌ Forgetting SELECT on Vector Search index

DEPLOYMENT WORKFLOW:
1. Clean bundle cache
2. Deploy bundle (notebooks + app code)
3. Run infrastructure job (11 tasks sequentially)
4. Deploy Streamlit app (creates service principal)
5. Grant permissions (uses app's UUID)

DELIVERABLES:
- 2 DAB config files
- 2 deployment scripts
- 11 notebooks
- 2 dashboard versions
- 5 knowledge base documents
- Complete documentation

GO! 🚀
```

### How to Use This Prompt

1. **With AI Assistant**: Copy the prompt above and paste it into Claude, ChatGPT, or your AI tool
2. **Follow Along**: Use this document as a reference for detailed implementation
3. **Customize**: Replace cluster IDs, warehouse IDs, host URLs with your values
4. **Deploy**: Run `./deploy.sh dev` when ready

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Prerequisites](#prerequisites)
3. [Architecture](#architecture)
4. [Deployment Strategy](#deployment-strategy)
5. [File Structure](#file-structure)
6. [Step-by-Step Build Guide](#step-by-step-build-guide)
7. [Unity Catalog Functions](#unity-catalog-functions)
8. [Vector Search Implementation](#vector-search-implementation)
9. [Dashboard Development](#dashboard-development)
10. [Databricks Asset Bundles](#databricks-asset-bundles)
11. [Common Issues & Solutions](#common-issues--solutions)
12. [Testing & Validation](#testing--validation)

---

## Project Overview

**Goal**: Build an AI-powered support ticket classification system that achieves:
- 95%+ classification accuracy
- <$0.002 cost per ticket
- <3 second processing time
- Production-ready deployment

**Key Technologies**:
- Unity Catalog AI Functions (`ai_classify`, `ai_extract`, `ai_gen`)
- Vector Search (Delta Sync + BGE embeddings)
- Streamlit Dashboard (local + Databricks Apps)
- Databricks Asset Bundles (DAB)

---

## Prerequisites

### Required Access
- Databricks workspace (Azure, AWS, or GCP)
- Unity Catalog enabled
- Ability to create:
  - Catalogs and schemas
  - Unity Catalog functions
  - Vector Search endpoints and indexes
  - Databricks Apps
  - Interactive or job clusters

### Local Setup
```bash
# Install Databricks CLI
pip install databricks-cli

# Configure authentication
databricks configure --token

# Verify connection
databricks workspace ls /
```

### Required Databricks CLI Profile
Create `~/.databrickscfg`:
```ini
[DEFAULT_azure]
host = https://adb-XXXXXXXXX.azuredatabricks.net
token = dapi...
```

### Infrastructure Values to Customize

**Replace these values throughout the project with your own:**

| What | Example Value | Where to Find | Where to Update |
|------|---------------|---------------|-----------------|
| **Workspace Host** | `adb-984752964297111.11.azuredatabricks.net` | Databricks workspace URL | `databricks.yml`, `databricks.staging_prod.yml`, `dashboard/app.yaml` |
| **Cluster ID** (for dev) | `0304-162117-qgsi1x04` | Compute → Clusters → Your cluster | `databricks.yml` line 38 |
| **SQL Warehouse ID** | `148ccb90800933a1` | SQL → Warehouses → Your warehouse | `dashboard/app_databricks.py`, `dashboard/app.yaml` |
| **Catalog Name** | `classify_tickets_new_dev` | Choose your own | `databricks.yml` line 7 (default) |
| **Vector Endpoint** | `one-env-shared-endpoint-2` | Compute → Vector Search → Endpoints | `databricks.yml` line 18 (default), can keep or change |

**How to find your values:**

1. **Workspace Host**: Look at your browser URL when logged into Databricks
   - Example: `https://adb-984752964297111.11.azuredatabricks.net`
   - Use everything after `https://`

2. **Cluster ID**: Go to Compute → Clusters → Click your cluster → Copy from URL
   - URL format: `.../compute/clusters/0304-162117-qgsi1x04`

3. **SQL Warehouse ID**: Go to SQL → Warehouses → Click warehouse → Copy from URL
   - URL format: `.../sql/1.0/warehouses/148ccb90800933a1`

4. **Catalog Name**: Choose any name (must be unique in your workspace)
   - Pattern: `{project}_{environment}` (e.g., `classify_tickets_new_dev`)

5. **Vector Endpoint**: Use existing or create new
   - Compute → Vector Search → Endpoints
   - Recommended: Share one endpoint across projects (cost-effective)

**Quick Find & Replace Commands:**

```bash
# Replace workspace host
find . -type f \( -name "*.yml" -o -name "*.yaml" -o -name "*.py" \) -exec sed -i '' 's/adb-984752964297111.11.azuredatabricks.net/YOUR_HOST/g' {} +

# Replace cluster ID (dev only)
sed -i '' 's/0304-162117-qgsi1x04/YOUR_CLUSTER_ID/g' databricks.yml

# Replace SQL Warehouse ID
find ./dashboard -type f -name "*.py" -exec sed -i '' 's/148ccb90800933a1/YOUR_WAREHOUSE_ID/g' {} +
```

**Validation Checklist:**
- [ ] Can connect to cluster from Databricks CLI
- [ ] Can query SQL Warehouse from local Streamlit
- [ ] Vector Search endpoint exists (or will be created)
- [ ] Catalog name is available (not in use)

---

## Architecture

### 6-Phase Classification Workflow

```
Input Ticket
    ↓
Phase 1: Basic Classification (ai_classify)
    → Returns: {category, priority, assigned_team}
    ↓
Phase 2: Metadata Extraction (ai_extract)
    → Returns: {priority_score, urgency_level, affected_systems}
    ↓
Phase 3: Vector Search
    → Returns: Top 3 relevant knowledge base documents
    ↓
Phase 4: Summary Generation (ai_gen)
    → Returns: Context-aware recommendations
    ↓
Phase 5: Hybrid Classification
    → Combines all phases for best accuracy
    ↓
Phase 6: Quick Classify
    → Single function call for simple tickets
```

### Components

1. **Data Layer**
   - Unity Catalog (catalog + schema)
   - Delta tables (knowledge base, sample tickets)
   - UC Volume (raw document storage)

2. **AI Layer**
   - 4 UC Functions (classification, extraction, generation, quick classify)
   - Vector Search index (semantic retrieval)

3. **Application Layer**
   - Streamlit dashboard (local + production)
   - Service principal (auto-created)

4. **Deployment Layer**
   - Databricks Asset Bundles
   - 2 config files (dev, staging/prod)
   - 2 scripts (deploy, swap)

---

## Deployment Strategy

### The Simplified 2-Config Approach

**CRITICAL LESSON**: Multi-target DAB configs with overrides cause:
- Environment variable confusion
- Bundle cache conflicts
- Path mismatch errors
- Complexity that's hard to debug

**SOLUTION**: Use 2 separate config files that you swap between.

#### Config Files

**1. `databricks.yml` (Dev)**
- Interactive cluster for fast iteration
- Full deployment mode (clean slate)
- Catalog: `classify_tickets_new_dev`

**2. `databricks.staging_prod.yml` (Staging/Prod)**
- Job clusters for cost-effectiveness
- Incremental deployment mode
- Catalogs: `classify_tickets_new_staging`, `classify_tickets_new_prod`

#### Scripts

**1. `swap_config.sh`**
- Switches between configs
- Backs up current config automatically
- Shows current status

**2. `deploy.sh`**
- Cleans bundle cache
- Deploys bundle
- Runs infrastructure job
- Deploys app

---

## File Structure

Create this exact structure:

```
project_root/
├── databricks.yml                    # Dev config
├── databricks.staging_prod.yml       # Staging/prod config
├── deploy.sh                         # Deployment script
├── swap_config.sh                    # Config switcher
│
├── notebooks/                        # DAB tasks
│   ├── 00_cleanup_full_mode.py
│   ├── 00_setup_catalog_schema.py
│   ├── 01_deploy_uc_function_ai_classify.py
│   ├── 02_deploy_uc_function_ai_extract.py
│   ├── 03_deploy_uc_function_ai_gen.py
│   ├── 04_deploy_uc_function_quick_classify.py
│   ├── 06_prepare_sample_tickets.py
│   ├── 08_grant_app_permissions.py
│   ├── 10_upload_knowledge_docs.py
│   ├── 13_reload_kb_with_proper_chunking.py
│   └── 14_recreate_vector_search_index.py
│
├── dashboard/                        # Streamlit apps
│   ├── app_simple.py                # Local dev
│   ├── app_databricks.py            # Production
│   ├── app.yaml                     # App config
│   └── requirements.txt
│
└── knowledge_base/                   # Knowledge base docs
    ├── IT_infrastructure_runbook.txt
    ├── application_support_guide.txt
    ├── security_incident_playbook.txt
    ├── user_access_policies.txt
    └── ticket_classification_rules.txt
```

---

## Step-by-Step Build Guide

### Phase 1: Setup Databricks Asset Bundle

#### 1.1 Create `databricks.yml` (Dev Config)

```yaml
bundle:
  name: classify_tickets_system

variables:
  catalog:
    description: Unity Catalog name
    default: classify_tickets_new_dev
  
  schema:
    description: Schema name
    default: support_ai
  
  deployment_mode:
    description: "Deployment mode: full (clean slate) or incremental (update only changes)"
    default: full
  
  vector_endpoint:
    description: "Shared Vector Search endpoint name (NEVER DELETED - shared across projects)"
    default: one-env-shared-endpoint-2

workspace:
  host: https://adb-XXXXXXXXX.azuredatabricks.net
  root_path: /Workspace/Users/${workspace.current_user.userName}/.bundle/${bundle.name}/dev

resources:
  jobs:
    setup_infrastructure:
      name: "[dev] Setup Infrastructure"
      
      # NO job_clusters section for dev - uses existing cluster
      
      tasks:
        - task_key: cleanup_full_mode
          existing_cluster_id: YOUR_CLUSTER_ID  # Replace with your cluster
          notebook_task:
            notebook_path: ./notebooks/00_cleanup_full_mode.py
            base_parameters:
              catalog: ${var.catalog}
              mode: ${var.deployment_mode}
              vector_endpoint: ${var.vector_endpoint}
              app_name: classify-tickets-dashboard-dev
            source: WORKSPACE
        
        - task_key: create_catalog_schema
          depends_on:
            - task_key: cleanup_full_mode
          existing_cluster_id: YOUR_CLUSTER_ID
          notebook_task:
            notebook_path: ./notebooks/00_setup_catalog_schema.py
            base_parameters:
              catalog: ${var.catalog}
            source: WORKSPACE
        
        # ... (add remaining 9 tasks - see full example in repo)

  apps:
    ticket_classification_dashboard:
      name: classify-tickets-dashboard-dev
      description: "AI-Powered Support Ticket Classification Dashboard (dev)"
      source_code_path: ./dashboard
```

**Key Points**:
- Use `existing_cluster_id` for all tasks in dev
- NO `job_clusters` section (avoids job cluster creation)
- Pass parameters via `base_parameters`
- `source: WORKSPACE` (not GIT)

#### 1.2 Create `databricks.staging_prod.yml`

```yaml
bundle:
  name: classify_tickets_system

variables:
  catalog:
    description: Unity Catalog name
    # NO default - set in targets
  
  schema:
    description: Schema name
    default: support_ai
  
  deployment_mode:
    description: "Deployment mode: full (clean slate) or incremental (update only changes)"
    default: incremental
  
  vector_endpoint:
    description: "Shared Vector Search endpoint name"
    default: one-env-shared-endpoint-2

workspace:
  host: https://adb-XXXXXXXXX.azuredatabricks.net

resources:
  jobs:
    setup_infrastructure:
      name: "[${bundle.target}] Setup Infrastructure"
      
      # Job cluster configuration
      job_clusters:
        - job_cluster_key: setup_cluster
          new_cluster:
            spark_version: 16.4.x-scala2.12
            node_type_id: Standard_D4ds_v5
            driver_node_type_id: Standard_D8ds_v5
            autoscale:
              min_workers: 1
              max_workers: 20
            azure_attributes:
              availability: SPOT_WITH_FALLBACK_AZURE
              first_on_demand: 1
              spot_bid_max_price: -1
            runtime_engine: PHOTON
            data_security_mode: USER_ISOLATION
      
      tasks:
        - task_key: cleanup_full_mode
          job_cluster_key: setup_cluster  # Use job cluster
          notebook_task:
            notebook_path: ./notebooks/00_cleanup_full_mode.py
            base_parameters:
              catalog: ${var.catalog}
              mode: ${var.deployment_mode}
              vector_endpoint: ${var.vector_endpoint}
              app_name: classify-tickets-dashboard-${bundle.target}
            source: WORKSPACE
        
        # ... (add remaining tasks)

  apps:
    ticket_classification_dashboard:
      name: classify-tickets-dashboard-${bundle.target}
      description: "AI-Powered Support Ticket Classification Dashboard (${bundle.target})"
      source_code_path: ./dashboard

targets:
  staging:
    default: true
    mode: development
    variables:
      catalog: classify_tickets_new_staging
      deployment_mode: incremental
      vector_endpoint: one-env-shared-endpoint-2
    workspace:
      host: https://adb-XXXXXXXXX.azuredatabricks.net
      root_path: /Workspace/Users/${workspace.current_user.userName}/.bundle/${bundle.name}/${bundle.target}
  
  prod:
    mode: production
    variables:
      catalog: classify_tickets_new_prod
      deployment_mode: incremental
      vector_endpoint: one-env-shared-endpoint-2
    workspace:
      host: https://adb-XXXXXXXXX.azuredatabricks.net
      root_path: /Workspace/Users/${workspace.current_user.userName}/.bundle/${bundle.name}/${bundle.target}
    permissions:
      - user_name: ${workspace.current_user.userName}
        level: CAN_MANAGE
```

**Key Points**:
- Use `job_cluster_key` for all tasks
- Define `job_clusters` with cost-effective config
- Catalog name set in targets (not variables default)
- `mode: development` for staging, `mode: production` for prod

#### 1.3 Create Deployment Scripts

**`deploy.sh`**:
```bash
#!/bin/bash
set -e

TARGET="${1:-dev}"
PROFILE="${2:-DEFAULT_azure}"

echo "🚀 Deploying: $TARGET"

# Clean bundle cache
rm -rf .databricks/bundle/*

# Deploy bundle
if [ "$TARGET" == "dev" ]; then
  databricks bundle deploy --profile "$PROFILE"
else
  databricks bundle deploy -t "$TARGET" --profile "$PROFILE"
fi

# Run infrastructure
if [ "$TARGET" == "dev" ]; then
  databricks bundle run setup_infrastructure --profile "$PROFILE"
else
  databricks bundle run setup_infrastructure -t "$TARGET" --profile "$PROFILE"
fi

# Deploy app
if [ "$TARGET" == "dev" ]; then
  databricks bundle run ticket_classification_dashboard --profile "$PROFILE"
else
  databricks bundle run ticket_classification_dashboard -t "$TARGET" --profile "$PROFILE"
fi

echo "✅ Deployment complete!"
```

**`swap_config.sh`**:
```bash
#!/bin/bash
set -e

MODE="${1:-status}"

case "$MODE" in
  dev)
    if [ -f "databricks.yml" ] && ! grep -q "classify_tickets_new_dev" databricks.yml; then
      cp databricks.yml databricks.staging_prod.yml
    fi
    if [ -f "databricks.dev.backup.yml" ]; then
      cp databricks.dev.backup.yml databricks.yml
    fi
    echo "✅ Switched to DEV"
    ;;
    
  staging|prod)
    if [ -f "databricks.yml" ] && grep -q "classify_tickets_new_dev" databricks.yml; then
      cp databricks.yml databricks.dev.backup.yml
    fi
    if [ -f "databricks.staging_prod.yml" ]; then
      cp databricks.staging_prod.yml databricks.yml
    fi
    echo "✅ Switched to STAGING/PROD"
    ;;
    
  status)
    if grep -q "classify_tickets_new_dev" databricks.yml 2>/dev/null; then
      echo "✅ Currently on: DEV"
    elif grep -q "targets:" databricks.yml 2>/dev/null; then
      echo "✅ Currently on: STAGING/PROD"
    else
      echo "⚠️  Unknown configuration"
    fi
    ;;
    
  *)
    echo "Usage: ./swap_config.sh {dev|staging|prod|status}"
    exit 1
    ;;
esac
```

Make scripts executable:
```bash
chmod +x deploy.sh swap_config.sh
```

### Phase 2: Create Notebooks

#### 2.1 Cleanup Notebook (`00_cleanup_full_mode.py`)

```python
# Databricks notebook source
import sys
from databricks.sdk import WorkspaceClient

# Get parameters
try:
    CATALOG = dbutils.widgets.get("catalog")
    MODE = dbutils.widgets.get("mode")
    VECTOR_ENDPOINT = dbutils.widgets.get("vector_endpoint")
    APP_NAME = dbutils.widgets.get("app_name")
except:
    CATALOG = "classify_tickets_new_dev"
    MODE = "full"
    VECTOR_ENDPOINT = "one-env-shared-endpoint-2"
    APP_NAME = "classify-tickets-dashboard-dev"

SCHEMA = "support_ai"

print(f"Cleanup Mode: {MODE}")
print(f"Catalog: {CATALOG}")

if MODE.lower() != "full":
    print("Skipping cleanup - not in FULL mode")
    dbutils.notebook.exit("skipped")

print("=" * 60)
print("FULL MODE: Cleaning everything...")
print("=" * 60)

w = WorkspaceClient()

# 1. Ensure Vector Search endpoint exists (never delete it!)
print(f"\n1. Checking Vector Search endpoint: {VECTOR_ENDPOINT}")
try:
    endpoint = w.vector_search_endpoints.get_endpoint(VECTOR_ENDPOINT)
    print(f"   ✅ Endpoint exists: {endpoint.endpoint_status.state}")
except Exception as e:
    print(f"   Creating endpoint {VECTOR_ENDPOINT}...")
    try:
        w.vector_search_endpoints.create_endpoint(VECTOR_ENDPOINT, endpoint_type="STANDARD")
        print(f"   ✅ Endpoint created")
    except Exception as create_error:
        print(f"   ⚠️  Could not create endpoint: {create_error}")

# 2. Drop Vector Search index
print(f"\n2. Dropping Vector Search index...")
index_name = f"{CATALOG}.{SCHEMA}.knowledge_base_index"
try:
    w.vector_search_indexes.delete_index(index_name)
    print(f"   ✅ Deleted index: {index_name}")
except Exception as e:
    print(f"   ⚠️  Index not found or already deleted: {e}")

# 3. Drop catalog (CASCADE removes everything)
print(f"\n3. Dropping catalog: {CATALOG}")
try:
    spark.sql(f"DROP CATALOG IF EXISTS {CATALOG} CASCADE")
    print(f"   ✅ Dropped catalog: {CATALOG}")
except Exception as e:
    print(f"   ⚠️  Error dropping catalog: {e}")

print("\n" + "=" * 60)
print("✅ Cleanup complete!")
print("=" * 60)

dbutils.notebook.exit("success")
```

**Key Pattern**: Always check for shared resources (like endpoints) and create if missing, but NEVER delete them.

#### 2.2 Setup Catalog/Schema (`00_setup_catalog_schema.py`)

```python
# Databricks notebook source

# Get parameters
try:
    CATALOG = dbutils.widgets.get("catalog")
except:
    CATALOG = "classify_tickets_new_dev"

SCHEMA = "support_ai"

print(f"Setting up catalog: {CATALOG}")
print(f"Setting up schema: {SCHEMA}")

# Create catalog
spark.sql(f"CREATE CATALOG IF NOT EXISTS {CATALOG}")
print(f"✅ Catalog created/verified: {CATALOG}")

# Create schema
spark.sql(f"CREATE SCHEMA IF NOT EXISTS {CATALOG}.{SCHEMA}")
print(f"✅ Schema created/verified: {SCHEMA}")

# Create volume for knowledge docs
spark.sql(f"""
    CREATE VOLUME IF NOT EXISTS {CATALOG}.{SCHEMA}.knowledge_docs
""")
print(f"✅ Volume created/verified: knowledge_docs")

print("\n✅ Setup complete!")
dbutils.notebook.exit("success")
```

**Key Pattern**: Use `IF NOT EXISTS` for idempotent operations.

#### 2.3 UC Function: ai_classify (`01_deploy_uc_function_ai_classify.py`)

```python
# Databricks notebook source

try:
    CATALOG = dbutils.widgets.get("catalog")
except:
    CATALOG = "classify_tickets_new_dev"

SCHEMA = "support_ai"
FUNCTION_NAME = "ai_classify"

print(f"Deploying UC Function: {CATALOG}.{SCHEMA}.{FUNCTION_NAME}")

# Drop existing function
try:
    spark.sql(f"DROP FUNCTION IF EXISTS {CATALOG}.{SCHEMA}.{FUNCTION_NAME}")
    print("✅ Dropped existing function")
except:
    pass

# Create function
function_sql = f"""
CREATE OR REPLACE FUNCTION {CATALOG}.{SCHEMA}.{FUNCTION_NAME}(ticket_text STRING)
RETURNS STRUCT<
  category STRING,
  priority STRING,
  assigned_team STRING
>
LANGUAGE SQL
RETURN (
  SELECT
    ai_classify(
      'You are an IT support ticket classifier. Classify this ticket:' || ticket_text ||
      '\n\nReturn JSON with these exact fields:\n' ||
      '{{\n' ||
      '  "category": "Hardware|Software|Network|Security|Access|Other",\n' ||
      '  "priority": "Critical|High|Medium|Low",\n' ||
      '  "assigned_team": "Desktop Support|Network Team|Security Team|Application Team|Help Desk"\n' ||
      '}}'
    )
)
"""

spark.sql(function_sql)
print(f"✅ Created function: {FUNCTION_NAME}")

# Test function
print("\nTesting function...")
result = spark.sql(f"""
  SELECT {CATALOG}.{SCHEMA}.{FUNCTION_NAME}(
    'My laptop screen is flickering'
  ) as result
""").collect()[0]

print(f"Test result: {result.result}")
print("\n✅ Function deployed and tested successfully!")

dbutils.notebook.exit("success")
```

**CRITICAL LESSONS for UC Functions**:
1. Use string concatenation (`||`) instead of Python f-strings inside SQL
2. Escape curly braces in JSON examples: `{{` and `}}`
3. Always test after deployment
4. Use `LANGUAGE SQL` for built-in AI functions (simpler than PYTHON)

#### 2.4 UC Function: ai_extract (`02_deploy_uc_function_ai_extract.py`)

```python
# Databricks notebook source

try:
    CATALOG = dbutils.widgets.get("catalog")
except:
    CATALOG = "classify_tickets_new_dev"

SCHEMA = "support_ai"
FUNCTION_NAME = "ai_extract"

# Drop existing
spark.sql(f"DROP FUNCTION IF EXISTS {CATALOG}.{SCHEMA}.{FUNCTION_NAME}")

# Create function
function_sql = f"""
CREATE OR REPLACE FUNCTION {CATALOG}.{SCHEMA}.{FUNCTION_NAME}(ticket_text STRING)
RETURNS STRUCT<
  priority_score DOUBLE,
  urgency_level STRING,
  affected_systems ARRAY<STRING>,
  assigned_team STRING
>
LANGUAGE SQL
RETURN (
  SELECT
    ai_extract(
      ticket_text,
      ARRAY(
        'priority_score:double',
        'urgency_level:string',
        'affected_systems:array<string>',
        'assigned_team:string'
      )
    )
)
"""

spark.sql(function_sql)
print(f"✅ Created function: {FUNCTION_NAME}")

dbutils.notebook.exit("success")
```

**Key Pattern**: Use `ai_extract()` built-in function with explicit field types.

#### 2.5 UC Function: ai_gen (`03_deploy_uc_function_ai_gen.py`)

```python
# Databricks notebook source

try:
    CATALOG = dbutils.widgets.get("catalog")
except:
    CATALOG = "classify_tickets_new_dev"

SCHEMA = "support_ai"
FUNCTION_NAME = "ai_gen"

# Drop existing
spark.sql(f"DROP FUNCTION IF EXISTS {CATALOG}.{SCHEMA}.{FUNCTION_NAME}")

# Create function  
function_sql = f"""
CREATE OR REPLACE FUNCTION {CATALOG}.{SCHEMA}.{FUNCTION_NAME}(
  ticket_text STRING,
  context STRING
)
RETURNS STRING
LANGUAGE SQL
RETURN (
  SELECT ai_gen(
    'Ticket: ' || ticket_text || '\n\nKnowledge Base Context:\n' || context ||
    '\n\nProvide a summary and actionable recommendations.'
  )
)
"""

spark.sql(function_sql)
print(f"✅ Created function: {FUNCTION_NAME}")

dbutils.notebook.exit("success")
```

**Key Pattern**: Use built-in `ai_gen()` SQL function (NOT Python implementation).

#### 2.6 UC Function: quick_classify_ticket (`04_deploy_uc_function_quick_classify.py`)

```python
# Databricks notebook source

try:
    CATALOG = dbutils.widgets.get("catalog")
except:
    CATALOG = "classify_tickets_new_dev"

SCHEMA = "support_ai"
FUNCTION_NAME = "quick_classify_ticket"

# Drop existing
spark.sql(f"DROP FUNCTION IF EXISTS {CATALOG}.{SCHEMA}.{FUNCTION_NAME}")

# Create orchestration function
function_sql = f"""
CREATE OR REPLACE FUNCTION {CATALOG}.{SCHEMA}.{FUNCTION_NAME}(ticket_text STRING)
RETURNS STRUCT<
  category STRING,
  priority STRING,
  assigned_team STRING,
  priority_score DOUBLE,
  urgency_level STRING,
  affected_systems ARRAY<STRING>,
  summary STRING
>
LANGUAGE SQL
RETURN (
  WITH classification AS (
    SELECT {CATALOG}.{SCHEMA}.ai_classify(ticket_text) as class_result
  ),
  extraction AS (
    SELECT {CATALOG}.{SCHEMA}.ai_extract(ticket_text) as extract_result
  )
  SELECT
    struct(
      classification.class_result.category as category,
      classification.class_result.priority as priority,
      classification.class_result.assigned_team as assigned_team,
      extraction.extract_result.priority_score as priority_score,
      extraction.extract_result.urgency_level as urgency_level,
      extraction.extract_result.affected_systems as affected_systems,
      'Quick classification without knowledge base context' as summary
    )
  FROM classification, extraction
)
"""

spark.sql(function_sql)
print(f"✅ Created function: {FUNCTION_NAME}")

dbutils.notebook.exit("success")
```

**Key Pattern**: SQL functions can orchestrate multiple UC function calls using CTEs.

#### 2.7 Upload Knowledge Docs (`10_upload_knowledge_docs.py`)

```python
# Databricks notebook source
import os
from pathlib import Path

try:
    CATALOG = dbutils.widgets.get("catalog")
except:
    CATALOG = "classify_tickets_new_dev"

SCHEMA = "support_ai"
VOLUME = "knowledge_docs"

# Local knowledge base path
KB_PATH = Path("../knowledge_base")

# Upload each file to volume
volume_path = f"/Volumes/{CATALOG}/{SCHEMA}/{VOLUME}"

print(f"Uploading knowledge base documents to: {volume_path}")

files = [
    "IT_infrastructure_runbook.txt",
    "application_support_guide.txt",
    "security_incident_playbook.txt",
    "user_access_policies.txt",
    "ticket_classification_rules.txt"
]

for filename in files:
    local_path = KB_PATH / filename
    
    if local_path.exists():
        with open(local_path, 'r') as f:
            content = f.read()
        
        # Write to volume using dbutils
        volume_file_path = f"{volume_path}/{filename}"
        dbutils.fs.put(volume_file_path, content, overwrite=True)
        
        print(f"✅ Uploaded: {filename}")
    else:
        print(f"⚠️  File not found: {filename}")

print("\n✅ All documents uploaded!")
dbutils.notebook.exit("success")
```

**Key Pattern**: Use `dbutils.fs.put()` to write to UC Volumes.

#### 2.8 Load & Chunk Knowledge Base (`13_reload_kb_with_proper_chunking.py`)

```python
# Databricks notebook source
from pyspark.sql.types import *
from pyspark.sql.functions import *
from datetime import datetime
import re

try:
    CATALOG = dbutils.widgets.get("catalog")
except:
    CATALOG = "classify_tickets_new_dev"

SCHEMA = "support_ai"
TABLE = "knowledge_base"
VOLUME = "knowledge_docs"

# Define table schema
schema = StructType([
    StructField("doc_id", StringType(), False),
    StructField("doc_type", StringType(), False),
    StructField("title", StringType(), False),
    StructField("content", StringType(), False),
    StructField("keywords", ArrayType(StringType()), False),
    StructField("chunk_index", IntegerType(), False),
    StructField("total_chunks", IntegerType(), False),
    StructField("char_count", IntegerType(), False),
    StructField("created_at", TimestampType(), False)
])

# Drop and recreate table
spark.sql(f"DROP TABLE IF EXISTS {CATALOG}.{SCHEMA}.{TABLE}")

create_table_sql = f"""
CREATE TABLE {CATALOG}.{SCHEMA}.{TABLE} (
    doc_id STRING NOT NULL,
    doc_type STRING NOT NULL,
    title STRING NOT NULL,
    content STRING NOT NULL,
    keywords ARRAY<STRING> NOT NULL,
    chunk_index INT NOT NULL,
    total_chunks INT NOT NULL,
    char_count INT NOT NULL,
    created_at TIMESTAMP NOT NULL
)
USING DELTA
"""
spark.sql(create_table_sql)

# Chunking function
def chunk_text(text, min_size=800, max_size=1500):
    """Split text into semantic chunks"""
    chunks = []
    
    # Split on double newlines (paragraphs)
    paragraphs = text.split('\n\n')
    
    current_chunk = ""
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        
        # If adding this paragraph exceeds max_size, save current chunk
        if len(current_chunk) + len(para) > max_size and len(current_chunk) >= min_size:
            chunks.append(current_chunk.strip())
            current_chunk = para + "\n\n"
        else:
            current_chunk += para + "\n\n"
    
    # Add remaining content
    if current_chunk.strip():
        chunks.append(current_chunk.strip())
    
    return chunks

# Process documents
volume_path = f"/Volumes/{CATALOG}/{SCHEMA}/{VOLUME}"
files = dbutils.fs.ls(volume_path)

records = []
for file_info in files:
    if file_info.name.endswith('.txt'):
        # Read file
        content = dbutils.fs.head(file_info.path, 1000000)  # Read up to 1MB
        
        # Extract doc type from filename
        doc_type = file_info.name.replace('.txt', '').replace('_', ' ').title()
        
        # Chunk content
        chunks = chunk_text(content)
        
        # Create records
        for i, chunk in enumerate(chunks):
            # Extract keywords (simple approach)
            keywords = list(set([
                word.lower() for word in re.findall(r'\b[A-Z][a-z]+\b', chunk)
                if len(word) > 3
            ]))[:10]  # Top 10 keywords
            
            record = (
                f"{file_info.name}_{i}",      # doc_id
                doc_type,                      # doc_type
                doc_type,                      # title
                chunk,                         # content
                keywords,                      # keywords
                i,                             # chunk_index
                len(chunks),                   # total_chunks
                len(chunk),                    # char_count
                datetime.now()                 # created_at
            )
            records.append(record)

# Create DataFrame with explicit schema
df = spark.createDataFrame(records, schema)

# Write to table
df.write.mode("append").saveAsTable(f"{CATALOG}.{SCHEMA}.{TABLE}")

print(f"✅ Loaded {len(records)} chunks from {len(files)} documents")

dbutils.notebook.exit("success")
```

**Key Patterns**:
1. Drop and recreate table to ensure schema correctness
2. Define explicit DataFrame schema matching table
3. Chunk text semantically (paragraphs, not arbitrary splits)
4. Extract keywords for better retrieval

#### 2.9 Create Vector Search Index (`14_recreate_vector_search_index.py`)

```python
# Databricks notebook source
from databricks.sdk import WorkspaceClient
import time

try:
    CATALOG = dbutils.widgets.get("catalog")
    MODE = dbutils.widgets.get("mode")
    VECTOR_ENDPOINT = dbutils.widgets.get("vector_endpoint")
except:
    CATALOG = "classify_tickets_new_dev"
    MODE = "full"
    VECTOR_ENDPOINT = "one-env-shared-endpoint-2"

SCHEMA = "support_ai"
INDEX_NAME = f"{CATALOG}.{SCHEMA}.knowledge_base_index"
SOURCE_TABLE = f"{CATALOG}.{SCHEMA}.knowledge_base"

w = WorkspaceClient()

# Ensure endpoint exists
print(f"Checking endpoint: {VECTOR_ENDPOINT}")
try:
    endpoint = w.vector_search_endpoints.get_endpoint(VECTOR_ENDPOINT)
    print(f"✅ Endpoint exists: {endpoint.endpoint_status.state}")
except:
    print(f"Creating endpoint: {VECTOR_ENDPOINT}")
    w.vector_search_endpoints.create_endpoint(VECTOR_ENDPOINT, endpoint_type="STANDARD")
    
    # Wait for endpoint to be ready
    for _ in range(60):
        try:
            endpoint = w.vector_search_endpoints.get_endpoint(VECTOR_ENDPOINT)
            if endpoint.endpoint_status.state == "ONLINE":
                break
        except:
            pass
        time.sleep(10)
    print("✅ Endpoint created and online")

# Create or sync index
if MODE.lower() == "full":
    print(f"\nFULL MODE: Creating new index...")
    
    # Create index using SQL
    spark.sql(f"""
        CREATE TABLE IF NOT EXISTS {INDEX_NAME}
        USING VECTORSEARCH
        TBLPROPERTIES (
            'vectorsearch.endpoint' = '{VECTOR_ENDPOINT}',
            'vectorsearch.index_type' = 'DELTA_SYNC',
            'vectorsearch.source_table' = '{SOURCE_TABLE}',
            'vectorsearch.primary_key' = 'doc_id',
            'vectorsearch.embedding_source_column' = 'content',
            'vectorsearch.embedding_model' = 'databricks-bge-large-en',
            'vectorsearch.sync_mode' = 'TRIGGERED'
        )
    """)
    
    # Wait for index to be ONLINE
    print("Waiting for index to be ONLINE...")
    for i in range(60):
        try:
            index = w.vector_search_indexes.get_index(INDEX_NAME)
            if index.status.state == "ONLINE":
                print("✅ Index is ONLINE")
                break
        except:
            pass
        time.sleep(10)
    
    # Trigger sync
    print("Triggering initial sync...")
    w.vector_search_indexes.sync_index(INDEX_NAME)
    
else:
    print(f"\nINCREMENTAL MODE: Syncing existing index...")
    
    try:
        index = w.vector_search_indexes.get_index(INDEX_NAME)
        
        # Wait for ONLINE
        for i in range(30):
            index = w.vector_search_indexes.get_index(INDEX_NAME)
            if index.status.state == "ONLINE":
                break
            time.sleep(10)
        
        # Trigger sync
        w.vector_search_indexes.sync_index(INDEX_NAME)
        print("✅ Index synced")
        
    except:
        print("Index doesn't exist, creating...")
        # Same as full mode
        spark.sql(f"""
            CREATE TABLE IF NOT EXISTS {INDEX_NAME}
            USING VECTORSEARCH
            ...
        """)

print("\n✅ Vector Search index ready!")
dbutils.notebook.exit("success")
```

**CRITICAL LESSONS for Vector Search**:
1. Always wait for index to be ONLINE before syncing
2. Use TRIGGERED sync (not CONTINUOUS) for cost savings
3. Check/create shared endpoint (never delete it)
4. Use `databricks-bge-large-en` embedding model (free)
5. Sync mode is set via TBLPROPERTIES (not API parameter)

#### 2.10 Grant App Permissions (`08_grant_app_permissions.py`)

```python
# Databricks notebook source
from databricks.sdk import WorkspaceClient

try:
    APP_NAME = dbutils.widgets.get("app_name")
    CATALOG = dbutils.widgets.get("catalog")
except:
    APP_NAME = "classify-tickets-dashboard-dev"
    CATALOG = "classify_tickets_new_dev"

SCHEMA = "support_ai"

w = WorkspaceClient()

# Get app details
print(f"Getting app: {APP_NAME}")
try:
    app = w.apps.get(APP_NAME)
    service_principal_id = app.service_principal_client_id  # UUID format
    service_principal_name = app.service_principal_name
    
    print(f"✅ App found")
    print(f"   Service Principal ID: {service_principal_id}")
    print(f"   Service Principal Name: {service_principal_name}")
except Exception as e:
    print(f"❌ App not found: {e}")
    print("Make sure the app is deployed first!")
    dbutils.notebook.exit("ERROR: App not found")

# Grant permissions using UUID (not display name!)
print(f"\nGranting permissions...")

permissions_sql = f"""
-- Grant catalog access
GRANT USE CATALOG ON CATALOG {CATALOG} TO `{service_principal_id}`;
GRANT USE SCHEMA ON SCHEMA {CATALOG}.{SCHEMA} TO `{service_principal_id}`;

-- Grant table access
GRANT SELECT ON TABLE {CATALOG}.{SCHEMA}.knowledge_base TO `{service_principal_id}`;
GRANT SELECT ON TABLE {CATALOG}.{SCHEMA}.sample_tickets TO `{service_principal_id}`;

-- Grant volume access
GRANT READ VOLUME ON VOLUME {CATALOG}.{SCHEMA}.knowledge_docs TO `{service_principal_id}`;

-- Grant Vector Search Index access (Delta Sync indexes are tables!)
GRANT SELECT ON TABLE {CATALOG}.{SCHEMA}.knowledge_base_index TO `{service_principal_id}`;

-- Grant function access
GRANT EXECUTE ON FUNCTION {CATALOG}.{SCHEMA}.ai_classify TO `{service_principal_id}`;
GRANT EXECUTE ON FUNCTION {CATALOG}.{SCHEMA}.ai_extract TO `{service_principal_id}`;
GRANT EXECUTE ON FUNCTION {CATALOG}.{SCHEMA}.ai_gen TO `{service_principal_id}`;
GRANT EXECUTE ON FUNCTION {CATALOG}.{SCHEMA}.quick_classify_ticket TO `{service_principal_id}`;
"""

# Execute grants
for statement in permissions_sql.split(';'):
    statement = statement.strip()
    if statement and not statement.startswith('--'):
        try:
            spark.sql(statement)
            print(f"✅ {statement[:50]}...")
        except Exception as e:
            print(f"⚠️  Error: {e}")

print("\n✅ Permissions granted!")
dbutils.notebook.exit("success")
```

**CRITICAL LESSONS for Permissions**:
1. Use `app.service_principal_client_id` (UUID), NOT `service_principal_name`
2. Grant permissions AFTER app is deployed
3. Vector Search Delta Sync indexes are tables - need SELECT permission
4. Use backticks around UUID: \`{uuid}\`

### Phase 3: Create Dashboard

#### 3.1 Production Dashboard (`dashboard/app_databricks.py`)

```python
import streamlit as st
from databricks.sdk import WorkspaceClient
import json

# Configuration
CATALOG = "classify_tickets_new_dev"  # Replace with your catalog
SCHEMA = "support_ai"

# Initialize Databricks client (OAuth M2M for apps)
w = WorkspaceClient()

def call_uc_function(function_name, *args):
    """Call UC function using Statement Execution API"""
    # Build SQL
    args_str = ', '.join([f"'{arg}'" for arg in args])
    sql = f"SELECT {CATALOG}.{SCHEMA}.{function_name}({args_str})"
    
    # Execute
    response = w.statement_execution.execute_statement(
        warehouse_id="YOUR_WAREHOUSE_ID",  # Replace
        statement=sql,
        wait_timeout="30s"
    )
    
    # Parse result
    if response.result and response.result.data_array:
        return response.result.data_array[0][0]
    return None

def query_vector_search(query_text, num_results=3):
    """Query Vector Search using WorkspaceClient API"""
    index_name = f"{CATALOG}.{SCHEMA}.knowledge_base_index"
    
    try:
        # Use w.api_client.do() for OAuth M2M
        result = w.api_client.do(
            'POST',
            f'/api/2.0/vector-search/indexes/{index_name}/query',
            body={
                'columns': ['doc_id', 'doc_type', 'title', 'content'],
                'query_text': query_text,
                'num_results': num_results
            }
        )
        
        if 'result' in result and 'data_array' in result['result']:
            return result['result']['data_array']
        return []
    except Exception as e:
        st.error(f"Vector Search error: {e}")
        return []

# Streamlit UI
st.title("🎫 AI-Powered Ticket Classification")

ticket_text = st.text_area("Enter ticket description:", height=150)

if st.button("Classify Ticket"):
    if ticket_text:
        with st.spinner("Classifying..."):
            # Phase 1: Basic classification
            result1 = call_uc_function("ai_classify", ticket_text)
            st.subheader("Phase 1: Basic Classification")
            st.json(result1)
            
            # Phase 2: Metadata extraction
            result2 = call_uc_function("ai_extract", ticket_text)
            st.subheader("Phase 2: Metadata Extraction")
            st.json(result2)
            
            # Phase 3: Vector search
            docs = query_vector_search(ticket_text)
            st.subheader("Phase 3: Vector Search")
            for doc in docs:
                st.write(f"**{doc[2]}** ({doc[1]})")
                st.write(doc[3][:200] + "...")
            
            # Phase 4: Generate summary
            context = "\n".join([doc[3] for doc in docs])
            summary = call_uc_function("ai_gen", ticket_text, context)
            st.subheader("Phase 4: Summary")
            st.write(summary)
```

**Key Pattern**: Use `w.api_client.do()` for Vector Search (handles OAuth automatically).

#### 3.2 Dashboard Config (`dashboard/app.yaml`)

```yaml
command:
  - streamlit
  - run
  - app_databricks.py
  - --server.port
  - "8080"
```

**Key Pattern**: Minimal config, let Databricks manage networking.

#### 3.3 Dependencies (`dashboard/requirements.txt`)

```
streamlit==1.29.0
databricks-sdk>=0.20.0
```

#### 3.4 Alternative: SQL-Based Dashboard Pattern

**For dashboards using SQL queries instead of UC Functions:**

```python
# Alternative dashboard using Databricks SQL Connector
from databricks import sql
from databricks.sdk.core import Config
import streamlit as st
import os

# Configuration
CATALOG = os.getenv("CATALOG_NAME", "classify_tickets_new_dev")
SCHEMA = os.getenv("SCHEMA_NAME", "support_ai")
SQL_WAREHOUSE_ID = os.getenv("DATABRICKS_WAREHOUSE_ID", "148ccb90800933a1")

@st.cache_resource
def get_databricks_connection():
    """Create Databricks SQL connection using official pattern"""
    try:
        # Config() reads from DATABRICKS_HOST env var (set in app.yaml)
        # For local: reads from ~/.databrickscfg DEFAULT profile
        cfg = Config()
        
        return sql.connect(
            server_hostname=cfg.host,
            http_path=f"/sql/1.0/warehouses/{SQL_WAREHOUSE_ID}",
            credentials_provider=lambda: cfg.authenticate,
        )
    except Exception as e:
        st.error(f"Connection error: {e}")
        return None

def query_table(sql_query: str):
    """Execute SQL query and return results"""
    conn = get_databricks_connection()
    if conn is None:
        return None
    
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql_query)
            return cursor.fetchall_arrow().to_pandas()
    except Exception as e:
        st.error(f"Query error: {e}")
        return None

# Example: Query sample tickets
st.title("Sample Tickets")
df = query_table(f"SELECT * FROM {CATALOG}.{SCHEMA}.sample_tickets LIMIT 10")
if df is not None:
    st.dataframe(df)
```

**When to use this pattern:**
- ✅ Simple SQL queries (SELECT, aggregations)
- ✅ Reading tables directly
- ✅ SQL Warehouse preferred over clusters

**When to use WorkspaceClient pattern (main guide):**
- ✅ UC Function calls
- ✅ Vector Search queries
- ✅ Complex API operations

**Required dependencies for SQL pattern:**
```
streamlit==1.29.0
databricks-sql-connector>=2.9.0
databricks-sdk>=0.20.0
```

**app.yaml for SQL pattern:**
```yaml
command:
  - streamlit
  - run
  - app_databricks.py
  - --server.port
  - "8080"

env:
  - name: 'DATABRICKS_HOST'
    value: 'adb-984752964297111.11.azuredatabricks.net'
  - name: 'DATABRICKS_WAREHOUSE_ID'
    value: '148ccb90800933a1'
  - name: 'CATALOG_NAME'
    value: 'classify_tickets_new_dev'
  - name: 'SCHEMA_NAME'
    value: 'support_ai'
```

**Key Differences:**
| Feature | WorkspaceClient | SQL Connector |
|---------|----------------|---------------|
| UC Functions | ✅ Statement Execution API | ❌ Not supported |
| Vector Search | ✅ w.api_client.do() | ❌ Not supported |
| SQL Queries | ✅ Statement Execution | ✅ cursor.execute() |
| Performance | Slower (compute) | Faster (SQL Warehouse) |
| Use Case | AI/ML operations | Analytics queries |

**Recommendation**: Use **WorkspaceClient** for this project (UC Functions + Vector Search). Use SQL Connector for traditional BI dashboards.

### Phase 4: Deploy

```bash
# Deploy to dev
./deploy.sh dev

# Check status
./swap_config.sh status

# Deploy to staging
./swap_config.sh staging
./deploy.sh staging

# Deploy to prod
./deploy.sh prod
```

---

## Common Issues & Solutions

### Issue 1: Bundle Cache Conflicts

**Symptom**: Path mismatch errors, staging paths appearing in dev deployments

**Solution**:
```bash
rm -rf .databricks/bundle/*
```

### Issue 2: Vector Search 403 Errors

**Symptom**: Permission denied when querying Vector Search

**Solution**:
1. Use `w.api_client.do()` (not Python SDK's VectorSearchClient)
2. Grant SELECT on index table:
   ```sql
   GRANT SELECT ON TABLE {catalog}.{schema}.knowledge_base_index TO `{sp_uuid}`;
   ```

### Issue 3: UC Function Returns None

**Symptom**: Functions return None or empty results

**Solution**: Use `.get()` for safe field access:
```python
result.get('category', 'Unknown')
```

### Issue 4: App Permissions Not Working

**Symptom**: App can't access catalog/tables

**Solution**:
1. Deploy app FIRST
2. Get service principal UUID: `app.service_principal_client_id`
3. Grant permissions using UUID (not display name)

### Issue 5: Vector Search Index Not Syncing

**Symptom**: Index shows 0 vectors after creation

**Solution**:
1. Wait for index to be ONLINE
2. Then trigger sync
3. Use TRIGGERED mode (not CONTINUOUS)

---

## Testing & Validation

### 1. Test UC Functions

```sql
-- Test ai_classify
SELECT ai_classify('My laptop screen is flickering');

-- Test ai_extract  
SELECT ai_extract('Cannot access shared drive');

-- Test ai_gen
SELECT ai_gen('Printer not working', 'Check printer settings and network connectivity');

-- Test quick_classify
SELECT quick_classify_ticket('VPN connection keeps dropping');
```

### 2. Test Vector Search

```python
from databricks.sdk import WorkspaceClient

w = WorkspaceClient()
result = w.api_client.do(
    'POST',
    '/api/2.0/vector-search/indexes/classify_tickets_new_dev.support_ai.knowledge_base_index/query',
    body={
        'columns': ['doc_id', 'title', 'content'],
        'query_text': 'How to reset password',
        'num_results': 3
    }
)
print(result)
```

### 3. Test Dashboard

1. Deploy: `./deploy.sh dev`
2. Get app URL: `databricks apps get classify-tickets-dashboard-dev`
3. Open in browser
4. Test sample tickets

---

## Performance Optimization

### Cost Optimization

1. **Use TRIGGERED Sync** - $0.0001 per query vs CONTINUOUS
2. **Share Endpoints** - Reuse `one-env-shared-endpoint-2`
3. **Free Embeddings** - Use `databricks-bge-large-en`
4. **Job Clusters** - Autoscale + spot instances
5. **Incremental Deployment** - Update only changes

### Speed Optimization

1. **Interactive Cluster for Dev** - Fast startup
2. **Parallel UC Function Calls** - Where possible
3. **Vector Search Indexing** - Pre-compute embeddings
4. **Batch Processing** - Process multiple tickets

---

## Production Checklist

- [ ] Replace cluster IDs in `databricks.yml`
- [ ] Replace warehouse IDs in dashboard
- [ ] Update host URLs in configs
- [ ] Test all 4 UC functions
- [ ] Verify Vector Search returns results
- [ ] Test dashboard locally
- [ ] Deploy to dev and verify end-to-end
- [ ] Deploy to staging and test
- [ ] Review costs in Databricks console
- [ ] Deploy to prod with monitoring

---

## Key Takeaways

### What Works

✅ **Simplified 2-Config Approach**
- Separate configs for dev and staging/prod
- Explicit swapping (no environment variables)
- No bundle cache conflicts

✅ **UC Functions with SQL**
- Use built-in AI functions (`ai_classify`, `ai_extract`, `ai_gen`)
- String concatenation for prompts
- Safe field access with `.get()`

✅ **Vector Search with OAuth**
- Use `w.api_client.do()` for queries
- TRIGGERED sync for cost savings
- Grant SELECT on index table

✅ **Databricks Apps**
- Service principals auto-created
- Use client_id (UUID) for grants
- Grant permissions AFTER deployment

### What Doesn't Work

❌ **Multi-Target DAB with Overrides**
- Complex, error-prone
- Bundle cache conflicts
- Hard to debug

❌ **Python SDK for Vector Search**
- 403 errors with service principals
- OAuth issues

❌ **Dot Notation in UC Functions**
- `row.field` fails
- Use `row.get('field')` instead

❌ **Granting Permissions Before App Exists**
- Service principal doesn't exist yet
- Must deploy app first

---

## Next Steps

1. **Clone this repository**
2. **Update configuration** (cluster IDs, warehouse IDs, host URLs)
3. **Deploy to dev**: `./deploy.sh dev`
4. **Test everything**
5. **Deploy to staging**: `./swap_config.sh staging && ./deploy.sh staging`
6. **Deploy to prod**: `./deploy.sh prod`

---

## 🔮 Genie API Integration (Multi-Agent Enhancement)

### Overview

Integrated Genie API for natural language querying of historical tickets, completing the multi-agent system with real-time classification, knowledge base search, and historical ticket retrieval.

### Architecture

**4-Agent Sequential Workflow:**
1. **Agent 1:** Classification (UC Function: `ai_classify`)
2. **Agent 2:** Metadata Extraction (UC Function: `ai_extract`)
3. **Agent 3:** Knowledge Base Search (Vector Search)
4. **Agent 4:** Historical Tickets (Genie Conversation API)

### Critical Genie API Bugs & Fixes

#### Bug #1: Wrong Warehouse ID
**Problem:** Used `os.environ.get('WAREHOUSE_ID')` but variable is `DATABRICKS_WAREHOUSE_ID`
```python
# ❌ Wrong
warehouse_id=os.environ.get('WAREHOUSE_ID')

# ✅ Correct
warehouse_id=os.getenv("DATABRICKS_WAREHOUSE_ID", "148ccb90800933a1")
```

**Impact:** All query executions failed silently

#### Bug #2: Wrong Attachment Field Name
**Problem:** Genie returns `attachment_id`, not `id`
```python
# ❌ Wrong
attachment_id = attachment.get('id')  # Returns None!

# ✅ Correct  
attachment_id = attachment.get('attachment_id')
```

**Discovery:** Found by running test notebook and inspecting actual API response
**Impact:** Could not retrieve query results from Genie

#### Bug #3: Missing Response Wrapper
**Problem:** Query-result response wrapped in `statement_response`
```python
# ❌ Wrong
manifest = response.get('manifest', {})

# ✅ Correct
statement_response = response.get('statement_response', {})
manifest = statement_response.get('manifest', {})
```

**Discovery:** Test notebook showed actual response structure
**Impact:** Could not parse data from Genie API

### Genie API Implementation Pattern

#### 3-Step Conversation Pattern

```python
class GenieConversationTool:
    def query(self, question: str):
        # Step 1: Start conversation
        response = self.w.api_client.do(
            'POST',
            f'/api/2.0/genie/spaces/{space_id}/start-conversation',
            body={'content': question}
        )
        conversation_id = response['conversation']['id']
        message_id = response['message']['id']
        
        # Step 2: Poll for completion
        while status != 'COMPLETED':
            response = self.w.api_client.do(
                'GET',
                f'/api/2.0/genie/spaces/{space_id}/conversations/{conversation_id}/messages/{message_id}'
            )
            status = response.get('status')
            time.sleep(poll_interval)
        
        # Step 3: Retrieve query results
        attachment_id = response['attachments'][0]['attachment_id']
        result = self.w.api_client.do(
            'GET',
            f'/api/2.0/genie/spaces/{space_id}/conversations/{conversation_id}/messages/{message_id}/query-result/{attachment_id}'
        )
        
        # Extract data from statement_response wrapper
        statement_response = result['statement_response']
        data_array = statement_response['result']['data_array']
        columns = statement_response['manifest']['schema']['columns']
        
        return data_array, columns
```

### Hybrid Approach: Genie + Fallback

**Best Practice:** Try Genie API, fallback to direct SQL execution

```python
# Try Genie query-result endpoint
if attachment_id:
    result = get_query_results(attachment_id)
    if result.get('data'):
        return result  # Success!

# Fallback: Execute SQL directly
if result.get('query') and not result.get('data'):
    execute_response = w.statement_execution.execute_statement(
        warehouse_id=WAREHOUSE_ID,
        statement=result['query']
    )
    return parse_statement_response(execute_response)
```

**Why:** Genie generates perfect SQL, but API availability varies by environment

### Permissions Required

1. **Genie Space Access:**
   - Service principal needs "Can Use" permission on Genie space
   - Grant via UI: Genie → Space Settings → Share
   - Notebook: `notebooks/09_grant_genie_permissions.py`

2. **Table Access:**
   ```sql
   GRANT SELECT ON TABLE catalog.schema.ticket_history TO `service_principal_id`;
   ```

3. **Warehouse Access:**
   ```sql
   GRANT CAN_USE ON WAREHOUSE warehouse_id TO `service_principal_id`;
   ```

### Testing Strategy

**Create Test Notebook** (`tests/test_genie_api.py`):
1. Test each API step independently
2. Print full response structures
3. Verify data extraction
4. Compare Genie API vs direct SQL execution

**Key Insight:** Test notebooks reveal actual API response structures, not what documentation assumes!

### Dashboard Integration

**Display Method Indicator:**
```python
if result.get('used_fallback'):
    st.caption("📡 Data Source: Direct SQL Execution (Fallback)")
else:
    st.caption("📡 Data Source: Genie query-result API")
```

**Display Historical Tickets:**
```python
for ticket in tickets:
    with st.expander(f"🎫 {ticket['ticket_id']}"):
        st.write(f"**Issue:** {ticket['ticket_text']}")
        st.warning(f"**Root Cause:** {ticket['root_cause']}")
        st.success(f"**Resolution:** {ticket['resolution']}")
        st.info(f"**Time:** {ticket['resolution_time_hours']} hours")
```

### Key Lessons Learned

1. **API Response Structure ≠ Documentation**
   - Always test with actual API calls
   - Print full responses to understand structure
   - Don't trust documentation alone

2. **Field Names Matter**
   - `attachment_id` vs `id`
   - `statement_response` wrapper exists
   - Test notebooks reveal truth

3. **Hybrid Approach is Best**
   - Use Genie for SQL generation (intelligence)
   - Use direct execution for reliability
   - Both approaches use same data format

4. **Environment Variables Are Critical**
   - `DATABRICKS_WAREHOUSE_ID` not `WAREHOUSE_ID`
   - Wrong warehouse = silent failures
   - Always use defaults: `os.getenv("VAR", "default")`

5. **Incremental Debugging Wins**
   - Fix one bug at a time
   - Test each fix independently  
   - Commit working state before next fix

### Files Created

- `notebooks/19_create_ticket_history_poc.py` - Sample historical tickets table
- `notebooks/09_grant_genie_permissions.py` - Grant service principal access
- `tests/test_genie_api.py` - Comprehensive API testing notebook
- `dashboard/app_databricks.py` - Full multi-agent integration

### Monitoring & Debugging

**Server Logs (print statements):**
```python
print(f"[Genie] Starting conversation...")
print(f"[Genie] Poll status: {status}")
print(f"[Genie] Found {len(attachments)} attachments")
print(f"[Genie] Attachment ID: {attachment_id}")
print(f"[Genie] Method used: {'GENIE API' if not fallback else 'FALLBACK SQL'}")
```

**UI Debug Info:**
```python
st.info(f"Debug: Genie returned data type: {type(data)}, length: {len(data)}")
with st.expander("🔍 Debug: Genie Response Keys"):
    st.json(genie_response)
```

### Performance Metrics

- **Genie SQL Generation:** ~10-15 seconds
- **Query Execution:** ~2-3 seconds
- **Data Display:** Instant
- **Total Time:** ~15-20 seconds for historical ticket retrieval

### Cost Optimization

- **Genie API:** Included in Databricks platform
- **SQL Warehouse:** Serverless (pay per query)
- **Caching:** Results cached in session state
- **Estimated Cost:** <$0.001 per query

---

## 🤖 LangGraph Agent Implementation (Learning & Prototyping)

### Overview

Built a LangGraph ReAct agent to learn agent-based architectures and compare with the sequential pipeline approach. The agent intelligently decides which tools to call based on ticket complexity, potentially reducing API calls by 25-50% on simple tickets.

**Learning Objective:** Understand when agent-based systems add value vs. when sequential pipelines are better.

### Architecture Comparison

**Sequential Pipeline (Production):**
```
Ticket → Classify → Extract → Vector Search → Genie → Display
        (Always all 4 steps, every time)
```

**LangGraph Agent (Experimental):**
```
Ticket → Agent → Think → Pick Tool → Observe → Think Again
                  ↓         ↓          ↓         ↓
                 "What    Which     Process   Need
                  do I     tool?    result    more?"
                  know?"                       
```

**Key Difference:** Agent makes intelligent decisions about which tools are needed based on context.

### Critical Errors Found & Fixed

#### Error #1: Wrong Tool Import Path
**Problem:** `langchain.tools.Tool` moved to `langchain_core.tools.Tool`
```python
# ❌ Wrong (old path)
from langchain.tools import Tool

# ✅ Correct (new path)
from langchain_core.tools import Tool
```

**Impact:** ImportError on notebook startup
**Discovery:** LangChain refactored in v1.0+ to separate core components

#### Error #2: UC Functions API Method Not Available
**Problem:** Used `w.functions.execute()` which doesn't exist in Python SDK
```python
# ❌ Wrong (non-existent API)
response = w.functions.execute(
    name=function_full_name,
    arguments=[{"name": k, "value": json.dumps(v)} for k, v in parameters.items()]
)

# ✅ Correct (Statement Execution API - same as dashboard)
from databricks.sdk.service.sql import StatementState

query = f"SELECT {CATALOG}.{SCHEMA}.{function_name}({args_str}) as result"
response = w.statement_execution.execute_statement(
    warehouse_id=WAREHOUSE_ID,
    statement=query,
    wait_timeout='30s'
)

if response.status.state == StatementState.SUCCEEDED:
    result = json.loads(response.result.data_array[0][0])
```

**Impact:** All UC Function calls failed
**Lesson:** Use Statement Execution API for UC Functions (more reliable, matches dashboard pattern)

#### Error #3: Vector Search Client Initialization
**Problem:** Passing `workspace_client` parameter no longer supported
```python
# ❌ Wrong (deprecated parameter)
vsc = VectorSearchClient(workspace_client=w)

# ✅ Correct (auto-detects from environment)
vsc = VectorSearchClient()
```

**Impact:** TypeError on Vector Search initialization
**Lesson:** VectorSearchClient auto-detects auth from environment (WorkspaceClient context)

#### Error #4: LangGraph Agent API Changed
**Problem:** `create_react_agent()` signature changed, no longer accepts `state_modifier`
```python
# ❌ Wrong (deprecated API)
agent = create_react_agent(
    llm,
    tools=[...],
    state_modifier=system_prompt  # No longer supported!
)

# ✅ Correct (bind system prompt to LLM)
llm = ChatDatabricks(
    endpoint=LLM_ENDPOINT,
    temperature=0.1
).bind(system=system_prompt)

agent = create_react_agent(
    model=llm,  # Note: parameter renamed to 'model'
    tools=[...]
)
```

**Impact:** TypeError on agent creation
**Lesson:** LangGraph v1.0 changed API - system prompts now bound to LLM, not agent

#### Error #5: Incorrect Catalog/Schema Names
**Problem:** Notebook configured with wrong catalog/schema names (copied from old config)
```python
# ❌ Wrong (old values)
CATALOG = "vik_catalog"
SCHEMA = "ai_ticket_classification"

# ✅ Correct (matches databricks.yml)
CATALOG = "classify_tickets_new_dev"
SCHEMA = "support_ai"
```

**Impact:** All UC Functions failed with `[UNRESOLVED_ROUTINE]` errors
**Lesson:** Always verify catalog/schema match `databricks.yml` configuration

#### Error #6: Vector Search Column Mismatch
**Problem:** Requested columns didn't match actual index schema
```python
# ❌ Wrong (old schema)
results = vsc.get_index(index_name).similarity_search(
    query_text=query,
    columns=["title", "content", "category"],  # 'category' doesn't exist!
    num_results=3
)

# ✅ Correct (actual schema)
results = vsc.get_index(index_name).similarity_search(
    query_text=query,
    columns=["doc_id", "doc_type", "title", "content"],
    num_results=3
)
```

**Impact:** Vector Search failed with "Requested columns not present in index"
**Lesson:** Verify index schema before querying (use `w.vector_search_indexes.get_index()` to inspect)

#### Error #7: Genie Not Fetching Data (attachment_id extraction)
**Problem:** Same issue as dashboard - `attachment_id` field name confusion
```python
# ❌ Wrong (looking for 'id')
attachment_id = attachment.get('id')

# ✅ Correct (field is 'attachment_id', not 'id')
attachment_id = attachment.get('attachment_id') or attachment.get('id')
```

**Impact:** Genie generated SQL but didn't fetch actual data rows
**Lesson:** Microsoft Genie API uses `attachment_id` field (not `id`), AND response is wrapped in `statement_response`

#### Error #8: Agent Test Runner None-Safety
**Problem:** `message.content` and `m.name` could be `None`, causing `TypeError`
```python
# ❌ Wrong (no None checks)
content_preview = message.content[:200]
tools_used = [m.name for m in result['messages'] if hasattr(m, 'name')]

# ✅ Correct (None-safe)
content = message.content or ""
content_preview = content[:200] if len(content) > 200 else content
tools_used = [m.name for m in result['messages'] if hasattr(m, 'name') and m.name]
```

**Impact:** Test runner crashed with "TypeError: sequence item 0: expected str instance, NoneType found"
**Lesson:** Always handle `None` values when processing LLM messages

#### Error #9: LLM Generating Generic `__arg1` Parameters
**Problem:** LLM used generic parameter names instead of actual tool parameter names
```
# Error message:
BadRequestError: 400 - Model response did not respect the required format.
Model Output: <function=search_knowledge>{"__arg1": "database connection timeout"}</function>

Expected: {"query": "database connection timeout"}
Actual:   {"__arg1": "database connection timeout"}
```

**Root Cause:** Tools didn't have explicit argument schemas, so LLM couldn't determine correct parameter names

**Solution:** Add Pydantic `args_schema` to each tool:
```python
from pydantic import BaseModel, Field

# Define explicit schemas
class SearchKnowledgeInput(BaseModel):
    query: str = Field(description="The search query to find relevant documentation")

# Bind schema to tool
search_tool = Tool(
    name="search_knowledge",
    description="Searches the knowledge base...",
    func=search_knowledge_wrapper,
    args_schema=SearchKnowledgeInput  # ← This guides the LLM!
)
```

**Impact:** All tool calls failed after first two tools (classification worked by luck before validation)
**Lesson:** **ALWAYS define `args_schema` for LangChain Tools** - it's the LLM's schema reference

#### Error #10: LLM Generating Malformed JSON (Wrong Closing Bracket)
**Problem:** Even with Pydantic schemas, LLM generated malformed JSON
```
# Error message:
BadRequestError: 400 - Model response did not respect the required format.
Model Output: <function=search_knowledge>{"query": "database connection timeout")</function>
                                                                                ^
                                                                                Wrong! Should be }
```

**Root Cause #1:** Temperature too low (0.1) caused deterministic formatting errors

**Root Cause #2:** `databricks-meta-llama-3-3-70b-instruct` doesn't have strong function calling support

**Solution:**
```python
# 1. Increase temperature
llm = ChatDatabricks(
    endpoint=LLM_ENDPOINT,
    temperature=0.3,  # Up from 0.1
    max_tokens=4096
)

# 2. Use explicit tool binding
tools_list = [classify_tool, extract_tool, search_tool, genie_tool]
llm_with_tools = llm.bind_tools(tools_list).bind(system=system_prompt)

agent = create_react_agent(
    model=llm_with_tools,
    tools=tools_list
)

# 3. Switch to DBRX model (better function calling support)
LLM_ENDPOINT = "databricks-dbrx-instruct"  # Databricks' own model
```

**Why DBRX?**
- Native Databricks model, optimized for function calling
- Extensively tested with LangChain patterns
- Better JSON formatting reliability than Llama 3.3

**Impact:** All tool calls after classification failed with JSON parse errors
**Lesson:** 
  - **Model selection matters for function calling** - not all LLMs handle it well
  - **Use `.bind_tools()`** explicitly for better formatting
  - **Temperature 0.1-0.3** is the sweet spot (too low = deterministic errors)

### Implementation Pattern

#### LangChain Tool Wrapper Structure

```python
from langchain_core.tools import Tool
from pydantic import BaseModel, Field

# IMPORTANT: Define Pydantic schema for tool inputs (guides LLM parameter naming)
class ClassifyTicketInput(BaseModel):
    ticket_text: str = Field(description="The support ticket text to classify")

# Pattern: Wrap existing APIs as Tools
def classify_ticket_wrapper(ticket_text: str) -> str:
    """Wrapper returns string (required by Tool interface)"""
    result = call_uc_function("ai_classify", {"ticket_text": ticket_text})
    return json.dumps(result, indent=2)  # Serialize to string

classify_tool = Tool(
    name="classify_ticket",
    description="Classifies a support ticket into category, priority, and routing team. Use this FIRST to understand the ticket type. Returns JSON with category, priority, team, confidence.",
    func=classify_ticket_wrapper,
    args_schema=ClassifyTicketInput  # ← CRITICAL: Tells LLM exact parameter names!
)
```

**Key Lessons:** 
- **Tool descriptions guide agent decisions** - be specific and directive
- **`args_schema` is mandatory** - without it, LLM generates generic `__arg1` parameters
- **Keep descriptions single-line** - reduces LLM confusion with JSON formatting

#### LangGraph Agent Creation

```python
from databricks_langchain import ChatDatabricks
from langgraph.prebuilt import create_react_agent

# System prompt embedded in LLM
system_prompt = """You are an intelligent support ticket analysis assistant.
Guidelines:
1. ALWAYS classify the ticket first
2. For simple questions, knowledge base is usually sufficient
3. For critical issues, check historical tickets
4. Be efficient but thorough - only use tools that add value"""

llm = ChatDatabricks(
    endpoint="databricks-dbrx-instruct",  # Better function calling than Llama
    temperature=0.3,  # Higher than 0.1 to avoid deterministic errors
    max_tokens=4096
)

# Bind tools explicitly for better function calling
tools_list = [classify_tool, extract_tool, search_tool, genie_tool]
llm_with_tools = llm.bind_tools(tools_list).bind(system=system_prompt)

# Create agent with all tools
agent = create_react_agent(
    model=llm_with_tools,
    tools=tools_list
)

# Invoke agent
result = agent.invoke({
    "messages": [("user", f"Analyze this ticket: {ticket_text}")]
})
```

**Key Lesson:** System prompt shapes agent behavior - clear guidelines = better decisions

### Testing Strategy

Created comprehensive test script to validate all components:

1. **Test Individual APIs First**
   - UC Functions (using Statement Execution API)
   - Vector Search (using VectorSearchClient)
   - Genie API (using WorkspaceClient)

2. **Then Wrap as LangChain Tools**
   - Verify each tool works independently
   - Check return format (must be string)

3. **Finally Test Agent**
   - Simple tickets (expect 2/4 tools)
   - Complex tickets (expect 3-4/4 tools)
   - Compare with sequential pipeline

**Test Script:** `tests/test_langraph_notebook.py`

### Agent Decision Examples

**Example 1: Simple Question**
```
Ticket: "How do I reset my password?"

Agent Thought: "Simple account question"
✓ Called: classify_ticket → Low priority, Account
✓ Called: search_knowledge → Found password reset guide
✗ Skipped: extract_metadata (not needed for simple question)
✗ Skipped: query_historical (KB article sufficient)

Result: 2/4 tools used, 50% reduction
```

**Example 2: Critical Production Issue**
```
Ticket: "Production database timeout affecting all users"

Agent Thought: "Critical production issue, need comprehensive analysis"
✓ Called: classify_ticket → Critical, Database Team
✓ Called: search_knowledge → Found timeout troubleshooting
✓ Called: extract_metadata → Priority score: 9.5, Systems: [Database, API]
✓ Called: query_historical → Found 5 similar resolved cases

Result: 4/4 tools used, full analysis
```

### Key Learnings

#### 1. API Compatibility is Critical
- **Databricks SDK APIs change** - test actual execution, not just imports
- **LangChain/LangGraph evolving** - check version compatibility
- **Statement Execution API** is the reliable pattern for UC Functions

#### 2. Tool Descriptions Drive Behavior
```python
# ❌ Bad description (too vague)
description="Classifies tickets"

# ✅ Good description (specific, directive)
description="""Classifies a support ticket by category, priority, team.
Use this FIRST to understand ticket type.
Returns: JSON with category, priority, team, confidence."""
```

#### 3. System Prompts Shape Intelligence
- **Clear guidelines** → Better tool selection
- **Explicit priorities** → Efficient decisions
- **Contextual examples** → Improved reasoning

#### 4. Testing in Isolation is Essential
- Test each API independently before wrapping
- Verify tool wrappers work standalone
- Then test agent orchestration
- Iterative debugging beats big-bang testing

#### 5. Authentication Patterns Differ by Context
```python
# Local testing
w = WorkspaceClient()  # Uses ~/.databrickscfg

# Notebook (Databricks runtime)
w = WorkspaceClient()  # Uses notebook execution context

# Dashboard (Databricks App)
w = WorkspaceClient()  # Uses service principal OAuth
```

**Same code, different auth context!**

### Files Created

**Notebooks:**
- `notebooks/23_langraph_agent_learning.py` - Full LangGraph agent implementation
  - Part 1: Test individual tools
  - Part 2: Create LangChain tool wrappers
  - Part 3: Build LangGraph ReAct agent
  - Part 4: Test with different ticket types
  - Part 5: Sequential vs Agent comparison

**Tests:**
- `tests/test_langraph_notebook.py` - Comprehensive validation script

**Documentation:**
- `docs/LANGRAPH_AGENT_PLAN.md` - Implementation plan (3 phases, 12 steps)
- `docs/LANGRAPH_ARCHITECTURE.md` - Visual architecture guide with ASCII diagrams

**Git Branch:**
- `agent_langraph_trying` - All experimental agent work isolated from main

### When to Use Each Approach

| Scenario | Sequential | Agent | Winner |
|----------|-----------|-------|--------|
| **Simple, uniform tickets** | ✅ Predictable | ⚠️ Overhead | Sequential |
| **Varied complexity** | ⚠️ Over-processes | ✅ Adaptive | Agent |
| **Cost-sensitive** | ⚠️ Always 4 calls | ✅ 2-4 calls | Agent |
| **Need consistency** | ✅ Always same | ⚠️ Varies | Sequential |
| **Learning/Research** | ⚠️ Static | ✅ Insightful | Agent |
| **Production reliability** | ✅ Battle-tested | ⚠️ Experimental | Sequential |

### Performance Comparison

**Test Case: "How do I export a report to PDF?"**

| Metric | Sequential | Agent | Improvement |
|--------|-----------|-------|-------------|
| Tools Called | 4/4 (100%) | 2/4 (50%) | 50% reduction |
| API Calls | 4 | 2 | 50% fewer |
| Time | ~8s | ~4s | 50% faster |
| Cost | ~$0.008 | ~$0.004 | 50% cheaper |
| Quality | Complete | Complete | Equal |

**Agent Reasoning:**
```
"This is a simple how-to question. I classified it as low priority.
The knowledge base should have a guide - no need to query historical
tickets or extract detailed metadata."
```

### Future Enhancements (Phase 2)

**Dashboard Integration:**
1. Add 5th tab: "🧪 LangGraph Agent (Experimental)"
2. Display agent reasoning trail
3. Side-by-side comparison mode
4. Tool usage metrics
5. Cost tracking (agent vs sequential)

**Module Structure:**
```python
# dashboard/langraph_agent.py
class TicketAgentTools:
    """Container for all 4 LangChain tools"""
    def __init__(self, workspace_client, config):
        self.classify_tool = self._create_classify_tool()
        self.extract_tool = self._create_extract_tool()
        # ...

class TicketReActAgent:
    """LangGraph agent manager"""
    def __init__(self, tools, llm_endpoint):
        self.agent = create_react_agent(...)
    
    def analyze(self, ticket_text):
        """Run agent and return results with reasoning"""
        result = self.agent.invoke(...)
        return self._parse_result(result)
```

### Dependencies

**Added to `dashboard/requirements.txt`:**
```
langgraph>=0.1.0
langchain>=0.1.0
langchain-core>=0.1.0
databricks-langchain>=0.1.0
backoff>=2.0.0
```

### Monitoring & Debugging

**Agent Trace Format:**
```
🧠 Agent Thought:
   "I need to classify this ticket first to understand its nature"

🔧 Action:
   Tool: classify_ticket
   Input: "Database connection timeout in production"

📤 Observation:
   Result: {"category": "Technical", "priority": "Critical", "team": "Database Team"}

🤔 Decision:
   "Critical technical issue - I should check knowledge base and historical tickets"
```

### Notebook Execution Tips

1. **Cell-by-Cell Execution:**
   - Run imports first
   - Test each tool independently
   - Create agent last
   - Test agent with multiple tickets

2. **Debug Mode:**
   ```python
   # Enable verbose logging
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```

3. **Cluster Requirements:**
   - Runtime: 14.3 LTS ML or newer
   - Node: Standard_DS3_v2 or similar
   - Workers: 1-2 (single node sufficient)

### Cost Analysis

**Per Ticket Costs:**
- **LLM Calls (Llama 3.3 70B):**
  - Agent thinking: ~$0.001
  - Tool calls: $0.001-0.004 (varies by tools used)
  
- **Total Cost:**
  - Simple ticket: ~$0.002 (agent) vs $0.008 (sequential)
  - Complex ticket: ~$0.006 (agent) vs $0.008 (sequential)
  
- **Potential Savings:** 25-75% depending on ticket distribution

### Lessons Learned Summary

1. ✅ **Statement Execution API is the Way**
   - More reliable than w.functions.execute()
   - Matches dashboard pattern
   - Works consistently

2. ✅ **LangChain Core for Tools**
   - Import from `langchain_core.tools`
   - Not from `langchain.tools` (deprecated)

3. ✅ **System Prompts Bind to LLM**
   - Not passed to create_react_agent()
   - Use `llm.bind(system=prompt)`

4. ✅ **Tool Descriptions are Critical**
   - Agent's only guidance
   - Be specific and directive
   - Include use cases

5. ✅ **Test in Isolation First**
   - Individual APIs
   - Then tools
   - Finally agent
   - Saves debugging time

6. ✅ **Agent-Based is Not Always Better**
   - Great for varied workloads
   - Overkill for uniform tasks
   - Learn when to use each

### Success Criteria Met

- ✅ All 4 tools working with WorkspaceClient
- ✅ LangChain tool wrappers created
- ✅ LangGraph ReAct agent functioning
- ✅ Agent makes intelligent decisions
- ✅ Sequential vs Agent comparison working
- ✅ Code portable to dashboard
- ✅ Comprehensive documentation created

### Next Phase

**Dashboard Integration Plan:**
- Extract working code to `dashboard/langraph_agent.py`
- Add new experimental tab to dashboard
- Display agent reasoning trail
- Add comparison mode
- Deploy and test in production

**Branch:** `agent_langraph_trying` (ready for merge when testing complete)

---

**You now have everything needed to build this system from scratch AND understand agent-based architectures! 🎉**

For questions or issues, review the lessons learned sections and common issues above.
