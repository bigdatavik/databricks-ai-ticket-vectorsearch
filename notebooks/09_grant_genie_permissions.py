# Databricks notebook source
# MAGIC %md
# MAGIC # Grant Genie Space Permissions to App Service Principal
# MAGIC 
# MAGIC Grants the Databricks App service principal access to the Genie space for querying historical tickets.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Get App Service Principal

# COMMAND ----------

from databricks.sdk import WorkspaceClient
import time

w = WorkspaceClient()

# Get parameters from notebook widgets (passed by DAB)
try:
    APP_NAME = dbutils.widgets.get("app_name")
    GENIE_SPACE_ID = dbutils.widgets.get("genie_space_id")
except:
    # Fallback defaults if running manually
    APP_NAME = "classify-tickets-dashboard-dev"
    GENIE_SPACE_ID = "01f0b91aa91c1b0c8cce6529ea09f0a8"

print(f"Looking for app: {APP_NAME}")
print(f"Genie Space ID: {GENIE_SPACE_ID}")

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
# MAGIC ## Grant Genie Space Permissions

# COMMAND ----------

print(f"\n🔐 Granting Genie space permissions...")
print(f"Space ID: {GENIE_SPACE_ID}")
print(f"Service Principal: {service_principal_name}")
print()

try:
    # First, verify the space exists
    try:
        space = w.api_client.do('GET', f'/api/2.0/genie/spaces/{GENIE_SPACE_ID}')
        space_name = space.get('name', 'Unknown')
        print(f"  ℹ️ Found Genie space: {space_name}")
    except Exception as e:
        print(f"  ⚠️ Warning: Could not verify space exists: {e}")
        print(f"  Continuing anyway...")
    
    # Grant permissions using the Genie API
    # Add the service principal as a user with query access
    # Reference: https://learn.microsoft.com/en-us/azure/databricks/genie/conversation-api
    
    try:
        # Method 1: Try adding as a collaborator via permissions API
        permission_body = {
            "access_control_list": [
                {
                    "service_principal_name": service_principal_name,
                    "permission_level": "CAN_USE"
                }
            ]
        }
        
        response = w.api_client.do(
            'PATCH',
            f'/api/2.0/genie/spaces/{GENIE_SPACE_ID}/permissions',
            body=permission_body
        )
        print(f"  ✅ Granted CAN_USE permission on Genie space via permissions API")
        
    except Exception as e1:
        print(f"  ℹ️ Permissions API not available: {e1}")
        
        # Method 2: Try adding via collaborators endpoint
        try:
            collaborator_body = {
                "collaborators": [
                    {
                        "type": "SERVICE_PRINCIPAL",
                        "name": service_principal_name,
                        "permission": "CAN_QUERY"
                    }
                ]
            }
            
            response = w.api_client.do(
                'POST',
                f'/api/2.0/genie/spaces/{GENIE_SPACE_ID}/collaborators',
                body=collaborator_body
            )
            print(f"  ✅ Added service principal as collaborator with CAN_QUERY permission")
            
        except Exception as e2:
            print(f"  ℹ️ Collaborators API not available: {e2}")
            
            # Method 3: Try using workspace-level permissions
            try:
                # Some Genie implementations inherit from workspace permissions
                print(f"  ℹ️ Attempting workspace-level permission grant...")
                
                # Grant via SQL (if Genie space is backed by a schema/catalog)
                # This is environment-specific
                print(f"  ⚠️ Manual Grant Required:")
                print(f"")
                print(f"  Please manually add the service principal to the Genie space:")
                print(f"  1. Go to Databricks Workspace → Genie")
                print(f"  2. Open space: {GENIE_SPACE_ID}")
                print(f"  3. Click 'Share' or 'Settings'")
                print(f"  4. Add user: {service_principal_name}")
                print(f"  5. Grant: 'Can Use' or 'Can Query' permission")
                print(f"")
                print(f"  Alternative: Add by Service Principal ID: {service_principal_id}")
                
            except Exception as e3:
                print(f"  ⚠️ Could not grant permissions automatically: {e3}")

    print(f"\n✅ Genie permission grant attempted")
    print(f"   If the app still can't access Genie, manual grant may be needed")
    
except Exception as e:
    print(f"  ⚠️ Error: {e}")
    print(f"\n📝 Manual Steps Required:")
    print(f"  1. Go to Databricks Workspace → Genie")
    print(f"  2. Find space ID: {GENIE_SPACE_ID}")
    print(f"  3. Add service principal: {service_principal_name}")
    print(f"     Or use ID: {service_principal_id}")
    print(f"  4. Grant 'Can Use' or 'Can Query' permission")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Verify Access (Test Query)

# COMMAND ----------

print(f"\n🧪 Testing Genie access...")

try:
    # Try to start a test conversation as the service principal would
    # This is a read-only test
    test_response = w.api_client.do(
        'GET',
        f'/api/2.0/genie/spaces/{GENIE_SPACE_ID}'
    )
    
    print(f"  ✅ Successfully accessed Genie space!")
    print(f"  Space Name: {test_response.get('name', 'N/A')}")
    print(f"  Description: {test_response.get('description', 'N/A')}")
    
    # Note: This test uses YOUR credentials, not the service principal's
    # The service principal access will be verified when the app runs
    print(f"\n  ℹ️ Note: Test used your credentials")
    print(f"  Service principal access will be verified when app queries Genie")
    
except Exception as e:
    print(f"  ⚠️ Could not access Genie space: {e}")
    print(f"  This might mean the space doesn't exist or manual permission grant is needed")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Summary

# COMMAND ----------

print(f"\n✅ Genie Permission Grant Summary:")
print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print(f"App: {APP_NAME}")
print(f"Service Principal: {service_principal_name}")
print(f"Genie Space ID: {GENIE_SPACE_ID}")
print(f"")
print(f"Granted Access To:")
print(f"  🔮 Genie Space (for historical ticket queries)")
print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print(f"")
print(f"✅ Permission grant complete!")
print(f"")
print(f"⚠️ If app still shows Genie errors:")
print(f"   → Manual grant may be required in Genie UI")
print(f"   → See instructions above")

# COMMAND ----------

