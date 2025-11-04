#!/usr/bin/env python3
"""
Simple test to see if we can execute the SQL query directly
"""
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.sql import StatementState
import json

w = WorkspaceClient(profile="DEFAULT_azure")

# The SQL query that Genie generated
sql_query = """
SELECT `ticket_id`, `ticket_text`, `root_cause`, `resolution`, `resolution_time_hours`, `resolved_at`
FROM `classify_tickets_new_dev`.`support_ai`.`ticket_history`
WHERE `assigned_team` = 'Applications' 
  AND `resolved_at` >= CURRENT_TIMESTAMP() - INTERVAL 60 DAYS
ORDER BY `resolved_at` DESC
LIMIT 3
"""

WAREHOUSE_ID = "148ccb90800933a1"  # Correct warehouse ID

print(f"🔹 Executing SQL query directly...")
print(f"SQL: {sql_query}")
print(f"Warehouse: {WAREHOUSE_ID}")
print()

try:
    execute_response = w.statement_execution.execute_statement(
        warehouse_id=WAREHOUSE_ID,
        statement=sql_query,
        wait_timeout='30s'
    )
    
    print(f"✅ Execution Status: {execute_response.status.state}")
    
    if execute_response.status.state == StatementState.SUCCEEDED:
        columns = execute_response.manifest.schema.columns if execute_response.manifest and execute_response.manifest.schema else []
        column_names = [col.name for col in columns]
        print(f"📊 Columns: {column_names}")
        
        if execute_response.result and execute_response.result.data_array:
            data_array = execute_response.result.data_array
            print(f"📊 Number of rows: {len(data_array)}")
            print()
            
            # Display results
            for i, row in enumerate(data_array):
                row_dict = dict(zip(column_names, row))
                print(f"{'='*80}")
                print(f"🎫 Ticket {i+1}:")
                print(f"{'='*80}")
                print(json.dumps(row_dict, indent=2, default=str))
                print()
        else:
            print("⚠️ No data returned")
    else:
        error_msg = execute_response.status.error.message if execute_response.status.error else "Unknown error"
        print(f"❌ Execution failed: {error_msg}")
        
except Exception as e:
    print(f"❌ Error executing SQL:")
    print(str(e))
    import traceback
    print(traceback.format_exc())

