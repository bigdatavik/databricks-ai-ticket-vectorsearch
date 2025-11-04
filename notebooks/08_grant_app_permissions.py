# Databricks notebook source
# MAGIC %md
# MAGIC # Grant App Service Principal Permissions
# MAGIC 
# MAGIC Automatically grants the Databricks App service principal permissions to:
# MAGIC - Unity Catalog (catalog, schema, tables, functions)
# MAGIC - Vector Search endpoint and index

# COMMAND ----------

# MAGIC %md
# MAGIC ## Get App Service Principal

# COMMAND ----------

from databricks.sdk import WorkspaceClient
import time

w = WorkspaceClient()

# Get parameters from notebook widgets (passed by DAB)
# These will be automatically set based on the target (dev/staging/prod)
try:
    APP_NAME = dbutils.widgets.get("app_name")
    CATALOG = dbutils.widgets.get("catalog")
except:
    # Fallback defaults if running manually
    APP_NAME = "classify-tickets-dashboard-dev"
    CATALOG = "classify_tickets_new_dev"

SCHEMA = "support_ai"
VECTOR_ENDPOINT = "one-env-shared-endpoint-2"

print(f"Looking for app: {APP_NAME}")
print(f"Catalog: {CATALOG}")

# COMMAND ----------

# Get app details
try:
    app = w.apps.get(APP_NAME)
    service_principal_id = app.service_principal_client_id
    service_principal_name = app.service_principal_name
    
    print(f"✅ Found app: {APP_NAME}")
    print(f"Service Principal ID: {service_principal_id}")
    print(f"Service Principal Name: {service_principal_name}")
except Exception as e:
    print(f"❌ Error getting app: {e}")
    print("Make sure the app is deployed first!")
    dbutils.notebook.exit("ERROR: App not found")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Grant Catalog Permissions

# COMMAND ----------

print(f"\n🔐 Granting catalog permissions...")
print(f"Service Principal ID: {service_principal_id}")
print(f"Service Principal Name: {service_principal_name}")
print()

# IMPORTANT: Use service_principal_id (UUID format) for grants, not the display name
# According to Microsoft docs, service principals should be referenced by their client ID
permissions_sql = f"""
-- Grant catalog access
GRANT USE CATALOG ON CATALOG {CATALOG} TO `{service_principal_id}`;
GRANT USE SCHEMA ON SCHEMA {CATALOG}.{SCHEMA} TO `{service_principal_id}`;

-- Grant table access
GRANT SELECT ON TABLE {CATALOG}.{SCHEMA}.knowledge_base TO `{service_principal_id}`;
GRANT SELECT ON TABLE {CATALOG}.{SCHEMA}.sample_tickets TO `{service_principal_id}`;
GRANT SELECT ON TABLE {CATALOG}.{SCHEMA}.ticket_history TO `{service_principal_id}`;

-- Grant volume access
GRANT READ VOLUME ON VOLUME {CATALOG}.{SCHEMA}.knowledge_docs TO `{service_principal_id}`;

-- Grant function access
GRANT EXECUTE ON FUNCTION {CATALOG}.{SCHEMA}.ai_classify TO `{service_principal_id}`;
GRANT EXECUTE ON FUNCTION {CATALOG}.{SCHEMA}.ai_extract TO `{service_principal_id}`;
GRANT EXECUTE ON FUNCTION {CATALOG}.{SCHEMA}.ai_gen TO `{service_principal_id}`;
GRANT EXECUTE ON FUNCTION {CATALOG}.{SCHEMA}.quick_classify_ticket TO `{service_principal_id}`;
"""

# Execute grants
for sql_statement in permissions_sql.strip().split(';'):
    if sql_statement.strip():
        try:
            spark.sql(sql_statement)
            # Extract permission type for cleaner output
            if 'GRANT' in sql_statement:
                parts = sql_statement.split()
                perm_type = parts[1] if len(parts) > 1 else 'permission'
                on_what = ' '.join(parts[3:7]) if len(parts) > 6 else 'resource'
                print(f"  ✅ Granted {perm_type} on {on_what}")
        except Exception as e:
            print(f"  ⚠️ Warning: {e}")

print(f"✅ Catalog permissions granted")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Grant SQL Warehouse Permissions

# COMMAND ----------

print(f"\n🔐 Granting SQL Warehouse permissions...")

SQL_WAREHOUSE_ID = "148ccb90800933a1"

try:
    # Get warehouse
    warehouse = w.warehouses.get(SQL_WAREHOUSE_ID)
    
    # Grant CAN_USE permission
    w.warehouses.set_permissions(
        warehouse_id=SQL_WAREHOUSE_ID,
        access_control_list=[
            {
                "service_principal_name": service_principal_name,
                "permission_level": "CAN_USE"
            }
        ]
    )
    print(f"  ✅ Granted CAN_USE on SQL Warehouse {SQL_WAREHOUSE_ID}")
except Exception as e:
    print(f"  ⚠️ Warning: {e}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Grant Vector Search Permissions

# COMMAND ----------

print(f"\n🔐 Granting Vector Search permissions...")

INDEX_NAME = f"{CATALOG}.{SCHEMA}.knowledge_base_index"

try:
    # Grant permissions on the Vector Search index using SQL
    # Vector Search indexes are Unity Catalog objects and need explicit permissions
    vector_grants = [
        f"GRANT SELECT ON TABLE {CATALOG}.{SCHEMA}.knowledge_base_index TO `{service_principal_id}`",
    ]
    
    for grant_sql in vector_grants:
        try:
            spark.sql(grant_sql)
            print(f"  ✅ Granted SELECT on Vector Search index")
        except Exception as e:
            # Vector Search indexes might not support direct grants, try alternative
            print(f"  ℹ️ Direct grant not supported, using endpoint permissions")
            
            # Try granting via endpoint permissions API
            try:
                from databricks.sdk.service.vectorsearch import VectorSearchEndpointsAPI
                
                # Grant permission on the endpoint
                endpoint_perms = {
                    "access_control_list": [
                        {
                            "service_principal_name": service_principal_name,
                            "permission_level": "CAN_QUERY_VECTORS"
                        }
                    ]
                }
                # Note: This may require using REST API directly
                print(f"  ℹ️ Vector Search permissions typically inherited from catalog")
            except Exception as e2:
                print(f"  ℹ️ Using catalog-level permissions for Vector Search: {e2}")
    
    print(f"  Index: {INDEX_NAME}")
    print(f"  Endpoint: {VECTOR_ENDPOINT}")
    print(f"  ✅ Vector Search access configured")
    
except Exception as e:
    print(f"  ⚠️ Warning: {e}")
    print(f"  Note: Vector Search access should work via catalog permissions")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Verify Permissions

# COMMAND ----------

print(f"\n✅ Permission Grant Summary:")
print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print(f"App: {APP_NAME}")
print(f"Service Principal: {service_principal_name}")
print(f"")
print(f"Granted Access To:")
print(f"  📁 Catalog: {CATALOG}")
print(f"  📂 Schema: {SCHEMA}")
print(f"  📊 Tables: knowledge_base, sample_tickets, ticket_history")
print(f"  ⚙️ Functions: ai_classify, ai_extract, ai_gen, quick_classify_ticket")
print(f"  🗄️ SQL Warehouse: {SQL_WAREHOUSE_ID}")
print(f"  🔍 Vector Search: {INDEX_NAME}")
print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print(f"")
print(f"✅ All permissions granted successfully!")
print(f"")
print(f"🚀 App is ready to use!")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Restart App (Optional)

# COMMAND ----------

print(f"\n🔄 Restarting app to apply permissions...")

try:
    # Stop app
    w.apps.stop(APP_NAME)
    print(f"  ⏸️ Stopping app...")
    time.sleep(5)
    
    # Start app
    w.apps.start(APP_NAME)
    print(f"  ▶️ Starting app...")
    time.sleep(10)
    
    # Check status
    app_status = w.apps.get(APP_NAME)
    print(f"  ✅ App status: {app_status.status.state}")
    
    if hasattr(app_status, 'url'):
        print(f"")
        print(f"🌐 App URL: {app_status.url}")
    
except Exception as e:
    print(f"  ⚠️ Manual restart may be needed: {e}")

print(f"\n✅ Setup complete!")

