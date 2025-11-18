# 🚀 Databricks Asset Bundle Deployment Guide

Quick guide for deploying the LangGraph tutorial using Databricks Asset Bundles (DAB).

---

## 📋 Prerequisites

- [ ] Databricks workspace access
- [ ] Databricks CLI installed
- [ ] Git repository cloned
- [ ] Unity Catalog enabled in workspace

---

## ⚡ Quick Start (5 Minutes)

### 1. Install Databricks CLI

**Mac/Linux:**
```bash
curl -fsSL https://raw.githubusercontent.com/databricks/setup-cli/main/install.sh | sh
```

**Windows:**
```powershell
winget install Databricks.DatabricksCLI
```

**Verify:**
```bash
databricks --version
```

### 2. Configure Authentication

```bash
databricks configure --token
```

Enter:
- **Host**: Your workspace URL (e.g., `https://adb-123456789.7.azuredatabricks.net/`)
- **Token**: Generate from User Settings → Developer → Access Tokens

### 3. Clone and Navigate

```bash
git clone https://github.com/bigdatavik/databricks-ai-ticket-vectorsearch.git
cd databricks-ai-ticket-vectorsearch
git checkout langgraph-databricks-tutorial
```

### 4. Customize Configuration

Edit `databricks.yml`:

```yaml
variables:
  catalog:
    default: "your_catalog_name"      # ← Update this
  schema:
    default: "your_schema_name"       # ← Update this
  cluster_id:
    default: "your-cluster-id"        # ← Update this
  warehouse_id:
    default: "your-warehouse-id"      # ← Update this

workspace:
  host: https://your-workspace.cloud.databricks.com  # ← Update this
```

**💡 Finding Your IDs**:
- **Cluster ID**: From cluster URL → `/clusters/[ID]`
- **Warehouse ID**: From SQL Warehouse URL → `/sql/warehouses/[ID]`
- **Workspace URL**: Browser address bar when logged in

### 5. Validate Configuration

```bash
databricks bundle validate
```

**Expected output:**
```
✓ Configuration is valid
```

### 6. Deploy to Dev

```bash
databricks bundle deploy --target dev
```

**What this does:**
- Uploads tutorial notebook
- Uploads documentation
- Creates workspace directories
- Sets up configuration

**Expected output:**
```
✓ Uploaded tutorial/23_langraph_agent_learning.py
✓ Uploaded docs/
✓ Uploaded README.md
✓ Uploaded BEGINNER_TUTORIAL.md
✓ Deployment complete!

Tutorial available at:
/Users/your-email@example.com/.bundle/langraph-tutorial/dev/tutorial/23_langraph_agent_learning
```

---

## 🎯 Deployment Targets

### Development (dev)

**Purpose**: Learning, experimentation, testing

```bash
databricks bundle deploy --target dev
```

**Features**:
- Uses `langraph_tutorial_dev` catalog
- Deploys to `~/.bundle/langraph-tutorial/dev/`
- Safe for breaking changes

### Staging (staging)

**Purpose**: Pre-production testing, validation

```bash
databricks bundle deploy --target staging
```

**Features**:
- Uses `langraph_tutorial_staging` catalog
- Mimics production environment
- Integration testing

### Production (prod)

**Purpose**: Live production system

```bash
databricks bundle deploy --target prod
```

**Features**:
- Uses `langraph_tutorial` catalog (production)
- Strict permissions
- Monitored and validated

---

## 📁 What Gets Deployed

```
Your Workspace
└── Users/
    └── your-email@example.com/
        └── .bundle/
            └── langraph-tutorial/
                └── dev/                    # or staging/prod
                    ├── tutorial/
                    │   └── 23_langraph_agent_learning.py
                    ├── docs/
                    │   ├── REFERENCE_23_langraph_agent_learning.py
                    │   ├── LANGRAPH_ARCHITECTURE.md
                    │   ├── LANGRAPH_BIND_TOOLS_EXPLAINED.md
                    │   ├── LANGRAPH_FOR_FRIENDS.md
                    │   └── QUICK_START_AGENT_NOTEBOOK.md
                    ├── README.md
                    ├── BEGINNER_TUTORIAL.md
                    └── requirements.txt
```

---

## 🔧 Advanced Usage

### Deploy to Specific Environment

```bash
# Deploy to dev
databricks bundle deploy -t dev

# Deploy to staging
databricks bundle deploy -t staging

# Deploy to prod
databricks bundle deploy -t prod
```

### Override Variables

```bash
# Use different catalog
databricks bundle deploy -t dev --var="catalog=my_custom_catalog"

# Use different cluster
databricks bundle deploy -t dev --var="cluster_id=0123-456789-abc123"
```

### Destroy Deployment

```bash
# Remove dev deployment
databricks bundle destroy -t dev

# WARNING: This deletes all deployed resources!
```

### View Deployment Status

```bash
# Show what will be deployed
databricks bundle validate

# Show current deployment
databricks bundle deployment list
```

---

## 📝 Setting Up Unity Catalog

After deploying, you need to create the AI functions.

### Quick Setup Script

Run this in a Databricks notebook:

```python
# Configure
CATALOG = "langraph_tutorial"  # Match your databricks.yml
SCHEMA = "agents"              # Match your databricks.yml

# Create catalog and schema
spark.sql(f"CREATE CATALOG IF NOT EXISTS {CATALOG}")
spark.sql(f"CREATE SCHEMA IF NOT EXISTS {CATALOG}.{SCHEMA}")
spark.sql(f"USE CATALOG {CATALOG}")
spark.sql(f"USE SCHEMA {SCHEMA}")

# Create AI Functions
# 1. Classification
spark.sql("""
CREATE OR REPLACE FUNCTION ai_classify(
  ticket_text STRING COMMENT 'The support ticket text to classify'
)
RETURNS STRUCT<
  priority: STRING COMMENT 'Priority: P1, P2, P3, P4',
  category: STRING COMMENT 'Category: Access, Database, Network, Application, etc.',
  confidence: STRING COMMENT 'Confidence: High, Medium, Low'
>
COMMENT 'Classifies support tickets by priority and category'
RETURN ai_query(
  'databricks-meta-llama-3-1-70b-instruct',
  CONCAT(
    'Classify this support ticket into priority (P1-P4) and category. ',
    'P1=Critical/Outage, P2=High/Degraded, P3=Medium/Issue, P4=Low/Question. ',
    'Categories: Access, Database, Network, Application, Infrastructure, Security, Other. ',
    'Ticket: ', ticket_text
  )
)
""")

# 2. Extraction
spark.sql("""
CREATE OR REPLACE FUNCTION ai_extract(
  ticket_text STRING COMMENT 'The support ticket text to analyze'
)
RETURNS STRUCT<
  user_email: STRING COMMENT 'User email if mentioned',
  system_name: STRING COMMENT 'System or application name',
  error_code: STRING COMMENT 'Error code if mentioned',
  urgency_indicators: STRING COMMENT 'Words indicating urgency'
>
COMMENT 'Extracts key metadata from support tickets'
RETURN ai_query(
  'databricks-meta-llama-3-1-70b-instruct',
  CONCAT(
    'Extract structured information from this support ticket: ',
    'user email, system name, error code, urgency indicators. ',
    'Ticket: ', ticket_text
  )
)
""")

# 3. Response Generation
spark.sql("""
CREATE OR REPLACE FUNCTION ai_gen(
  ticket_text STRING COMMENT 'The support ticket text',
  context STRING COMMENT 'Knowledge base context or solutions'
)
RETURNS STRING
COMMENT 'Generates a helpful response based on ticket and context'
RETURN ai_query(
  'databricks-meta-llama-3-1-70b-instruct',
  CONCAT(
    'Generate a helpful support response based on this ticket and context. ',
    'Ticket: ', ticket_text, ' ',
    'Context: ', context
  )
)
""")

print("✅ All AI Functions created successfully!")

# Test
result = spark.sql("SELECT ai_classify('URGENT: Database is down!') as test").collect()[0]
print(f"Test result: {result.test}")
```

---

## 🔍 Verification Steps

### 1. Check Deployment

```bash
# In terminal
databricks bundle deployment list -t dev
```

### 2. Open Notebook

1. Go to your Databricks workspace
2. Navigate to: **Workspace** → **Users** → **your-email@example.com** → **.bundle** → **langraph-tutorial** → **dev** → **tutorial**
3. Click `23_langraph_agent_learning.py`

### 3. Verify AI Functions

In a notebook:
```python
# Check functions exist
spark.sql("SHOW FUNCTIONS IN langraph_tutorial.agents LIKE 'ai_%'").show()

# Should show:
# ai_classify
# ai_extract
# ai_gen
```

### 4. Run Tutorial

1. Attach notebook to your cluster
2. Update configuration in Cmd 2
3. Run all cells
4. Verify all tests pass

---

## 🐛 Troubleshooting

### Issue: "Bundle validation failed"

**Cause**: Invalid YAML syntax or missing required fields

**Solution**:
```bash
# Check YAML syntax
databricks bundle validate

# Common fixes:
# - Ensure proper indentation (use spaces, not tabs)
# - Check all required fields are filled
# - Verify cluster_id and warehouse_id are correct
```

### Issue: "Cluster not found"

**Cause**: Invalid cluster ID in configuration

**Solution**:
1. Go to **Compute** in Databricks
2. Click your cluster
3. Copy ID from URL: `/clusters/[CLUSTER_ID]`
4. Update `databricks.yml`:
   ```yaml
   variables:
     cluster_id:
       default: "your-correct-cluster-id"
   ```
5. Redeploy: `databricks bundle deploy -t dev`

### Issue: "Catalog does not exist"

**Cause**: Unity Catalog not set up

**Solution**:
```python
# In a notebook
spark.sql("CREATE CATALOG IF NOT EXISTS langraph_tutorial")
spark.sql("CREATE SCHEMA IF NOT EXISTS langraph_tutorial.agents")
```

### Issue: "Function ai_classify not found"

**Cause**: AI Functions not created

**Solution**:
Run the setup script from "Setting Up Unity Catalog" section above.

### Issue: "Permission denied"

**Cause**: Insufficient permissions

**Solution**:
Ask your workspace admin to grant:
- `USE CATALOG` permission
- `CREATE SCHEMA` permission
- `CREATE FUNCTION` permission
- `EXECUTE` permission on AI functions

---

## 📚 Additional Resources

### Documentation
- [Databricks Asset Bundles Docs](https://docs.databricks.com/dev-tools/bundles/index.html)
- [Databricks CLI Reference](https://docs.databricks.com/dev-tools/cli/index.html)
- [Unity Catalog AI Functions](https://docs.databricks.com/large-language-models/ai-functions.html)

### Tutorial Resources
- **Beginner Guide**: [`BEGINNER_TUTORIAL.md`](BEGINNER_TUTORIAL.md)
- **Quick Start**: [`README.md`](README.md)
- **Architecture**: [`docs/LANGRAPH_ARCHITECTURE.md`](docs/LANGRAPH_ARCHITECTURE.md)

### Getting Help
- [GitHub Issues](https://github.com/bigdatavik/databricks-ai-ticket-vectorsearch/issues)
- [Databricks Community](https://community.databricks.com)

---

## 🎉 Success Checklist

After deployment, you should have:

- [ ] Databricks CLI installed and configured
- [ ] Bundle deployed to dev environment
- [ ] Tutorial notebook accessible in workspace
- [ ] Unity Catalog and schema created
- [ ] AI Functions created (ai_classify, ai_extract, ai_gen)
- [ ] AI Functions tested and working
- [ ] Notebook attached to cluster
- [ ] Configuration updated with your IDs
- [ ] First test cell runs successfully

**🎊 Congratulations! You're ready to start learning LangGraph!**

Next step: Open [`BEGINNER_TUTORIAL.md`](BEGINNER_TUTORIAL.md) and follow Step 4 onwards.

---

*Last Updated: November 2024*  
*Bundle Version: 1.0*  
*Databricks CLI: v0.217+*

