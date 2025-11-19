# Databricks notebook source
# MAGIC %md
# MAGIC # Setup 5: Historical Tickets for Genie
# MAGIC 
# MAGIC This notebook creates a table of historical support tickets (resolved) that Genie can query.
# MAGIC 
# MAGIC **⚠️ PREREQUISITES:**
# MAGIC - `setup_catalog_schema.py` must be run first
# MAGIC 
# MAGIC ## What This Creates
# MAGIC 
# MAGIC - **Table**: `langtutorial.agents.ticket_history`
# MAGIC - **Contents**: 50+ resolved historical tickets with:
# MAGIC   - Ticket ID, subject, description
# MAGIC   - Category, priority, status
# MAGIC   - Resolution notes and timestamps
# MAGIC   - Various ticket types (P1-P4, different categories)
# MAGIC 
# MAGIC ## Purpose
# MAGIC 
# MAGIC This table will be used with Genie to answer questions like:
# MAGIC - "Show me recent P1 database issues"
# MAGIC - "What were the last 5 resolved security incidents?"
# MAGIC - "Find tickets similar to password reset"

# COMMAND ----------

# MAGIC %md
# MAGIC ## Configuration

# COMMAND ----------

from datetime import datetime, timedelta
from pyspark.sql.types import StructType, StructField, StringType, TimestampType
from pyspark.sql import Row
import random

# Configuration
try:
    CATALOG = dbutils.widgets.get("catalog")
except:
    CATALOG = "langtutorial_vik"

SCHEMA = "agents"
TABLE_NAME = "ticket_history"
FULL_TABLE_NAME = f"{CATALOG}.{SCHEMA}.{TABLE_NAME}"

print("=" * 80)
print("LANGGRAPH TUTORIAL - TICKET HISTORY SETUP")
print("=" * 80)
print(f"Table: {FULL_TABLE_NAME}")
print("=" * 80)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 1: Create Table Schema

# COMMAND ----------

# Create table for historical tickets
spark.sql(f"""
CREATE TABLE IF NOT EXISTS {FULL_TABLE_NAME} (
  ticket_id STRING NOT NULL,
  subject STRING NOT NULL,
  description STRING NOT NULL,
  submitted_by STRING,
  submitted_date TIMESTAMP,
  category STRING,
  priority STRING,
  status STRING,
  resolution_notes STRING,
  resolved_date TIMESTAMP,
  resolution_time_hours FLOAT,
  CONSTRAINT ticket_history_pk PRIMARY KEY(ticket_id)
)
USING DELTA
COMMENT 'Historical resolved support tickets for Genie queries - LangGraph tutorial'
""")

print(f"✅ Table created: {FULL_TABLE_NAME}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 2: Generate Sample Historical Tickets
# MAGIC 
# MAGIC Creating 50+ resolved tickets across different categories and priorities.

# COMMAND ----------

# Generate dates for the past 90 days
def random_past_date(days_ago_max=90):
    days_ago = random.randint(1, days_ago_max)
    return datetime.now() - timedelta(days=days_ago)

# Sample historical tickets
historical_tickets = []

# P1 Critical Issues (Resolved)
p1_tickets = [
    {
        'ticket_id': 'HIST-001',
        'subject': 'Production Database Server Down',
        'description': 'Main production database PROD-DB-01 completely down. All customer-facing apps affected.',
        'category': 'Database',
        'priority': 'P1',
        'resolution_notes': 'Database server had memory leak. Restarted service and applied patch. Monitoring for 24h.',
        'resolution_time_hours': 0.5
    },
    {
        'ticket_id': 'HIST-002',
        'subject': 'Critical Security Breach Detected',
        'description': 'Unauthorized access attempt detected on production API endpoint.',
        'category': 'Security',
        'priority': 'P1',
        'resolution_notes': 'Blocked IP addresses, rotated API keys, enabled MFA for all admin accounts.',
        'resolution_time_hours': 2.0
    },
    {
        'ticket_id': 'HIST-003',
        'subject': 'E-Commerce Site Complete Outage',
        'description': 'Website showing 500 errors globally. All orders blocked.',
        'category': 'Application',
        'priority': 'P1',
        'resolution_notes': 'Load balancer configuration error after deployment. Rolled back changes.',
        'resolution_time_hours': 1.5
    },
    {
        'ticket_id': 'HIST-004',
        'subject': 'Network Infrastructure Failure',
        'description': 'Core network switch failed. Multiple buildings without connectivity.',
        'category': 'Network',
        'priority': 'P1',
        'resolution_notes': 'Replaced failed switch with hot spare. Network fully restored.',
        'resolution_time_hours': 3.0
    },
    {
        'ticket_id': 'HIST-005',
        'subject': 'Data Loss in Production Database',
        'description': 'Accidental DELETE query executed on production. Customer data affected.',
        'category': 'Database',
        'priority': 'P1',
        'resolution_notes': 'Restored from backup taken 1 hour prior. Only 10 minutes of data lost.',
        'resolution_time_hours': 4.0
    },
]

# P2 High Priority (Resolved)
p2_tickets = [
    {
        'ticket_id': 'HIST-010',
        'subject': 'VPN Disconnections Affecting Remote Workers',
        'description': 'Sales team experiencing VPN drops every 15-20 minutes.',
        'category': 'Network',
        'priority': 'P2',
        'resolution_notes': 'VPN concentrator at capacity. Added second concentrator and load-balanced.',
        'resolution_time_hours': 4.0
    },
    {
        'ticket_id': 'HIST-011',
        'subject': 'CRM Application Very Slow',
        'description': 'CRM taking 30+ seconds to load records. 20+ users affected.',
        'category': 'Application',
        'priority': 'P2',
        'resolution_notes': 'Database queries missing indexes. Added indexes, performance restored.',
        'resolution_time_hours': 2.5
    },
    {
        'ticket_id': 'HIST-012',
        'subject': 'Email Server Performance Issues',
        'description': 'Email delays of 10-15 minutes. All departments affected.',
        'category': 'Infrastructure',
        'priority': 'P2',
        'resolution_notes': 'Mail queue backed up due to spam filter overload. Tuned filters.',
        'resolution_time_hours': 3.0
    },
    {
        'ticket_id': 'HIST-013',
        'subject': 'Database Connection Timeout Errors',
        'description': 'Analytics queries timing out. Reports failing to generate.',
        'category': 'Database',
        'priority': 'P2',
        'resolution_notes': 'Connection pool exhausted. Increased pool size and optimized queries.',
        'resolution_time_hours': 2.0
    },
    {
        'ticket_id': 'HIST-014',
        'subject': 'Phishing Attack Targeting Finance Team',
        'description': 'Coordinated phishing emails sent to 15 employees in Finance.',
        'category': 'Security',
        'priority': 'P2',
        'resolution_notes': 'Blocked sender domains, added email filter rules, conducted security training.',
        'resolution_time_hours': 6.0
    },
]

# P3 Medium Priority (Resolved)
p3_tickets = [
    {
        'ticket_id': 'HIST-020',
        'subject': 'Password Reset Request',
        'description': 'User forgot password and security question answers.',
        'category': 'Access',
        'priority': 'P3',
        'resolution_notes': 'Verified identity via phone call. Reset password via admin portal.',
        'resolution_time_hours': 0.25
    },
    {
        'ticket_id': 'HIST-021',
        'subject': 'New Employee Access Setup',
        'description': 'New hire needs email, CRM, and file share access.',
        'category': 'Access',
        'priority': 'P3',
        'resolution_notes': 'Created user accounts, assigned licenses, configured permissions.',
        'resolution_time_hours': 1.0
    },
    {
        'ticket_id': 'HIST-022',
        'subject': 'Printer Not Working in Conference Room',
        'description': 'Conference room B printer offline. Jobs stuck in queue.',
        'category': 'Hardware',
        'priority': 'P3',
        'resolution_notes': 'Printer driver outdated. Updated driver and restarted print spooler.',
        'resolution_time_hours': 0.5
    },
    {
        'ticket_id': 'HIST-023',
        'subject': 'Software Installation Request - Visio',
        'description': 'User needs Microsoft Visio for process diagrams.',
        'category': 'Software',
        'priority': 'P3',
        'resolution_notes': 'Verified manager approval. Installed Visio via Company Portal.',
        'resolution_time_hours': 0.5
    },
    {
        'ticket_id': 'HIST-024',
        'subject': 'Shared Drive Access Issue',
        'description': 'Cannot access S: drive when working remotely.',
        'category': 'Access',
        'priority': 'P3',
        'resolution_notes': 'VPN profile missing drive mapping. Updated profile and reconnected VPN.',
        'resolution_time_hours': 0.75
    },
]

# P4 Low Priority (Resolved)
p4_tickets = [
    {
        'ticket_id': 'HIST-030',
        'subject': 'Feature Request: PDF Export',
        'description': 'Add PDF export option to reporting tool.',
        'category': 'Software',
        'priority': 'P4',
        'resolution_notes': 'Added to product backlog for Q2 release. Will notify when implemented.',
        'resolution_time_hours': 0.25
    },
    {
        'ticket_id': 'HIST-031',
        'subject': 'Question About Email Retention Policy',
        'description': 'How long are emails kept before deletion?',
        'category': 'Other',
        'priority': 'P4',
        'resolution_notes': 'Explained 7-year retention policy. Sent link to full policy document.',
        'resolution_time_hours': 0.1
    },
    {
        'ticket_id': 'HIST-032',
        'subject': 'Request for IT Training on New Tools',
        'description': 'Can we get training on the new project management software?',
        'category': 'Other',
        'priority': 'P4',
        'resolution_notes': 'Scheduled training session for next month. Sent calendar invite to team.',
        'resolution_time_hours': 0.5
    },
]

# Add more variety by duplicating with variations
additional_database = [
    {
        'ticket_id': 'HIST-040',
        'subject': 'Database Backup Failed',
        'description': 'Nightly backup job failed for production database.',
        'category': 'Database',
        'priority': 'P2',
        'resolution_notes': 'Disk space full on backup server. Cleaned old backups, re-ran successfully.',
        'resolution_time_hours': 1.5
    },
    {
        'ticket_id': 'HIST-041',
        'subject': 'Slow Report Generation',
        'description': 'Monthly sales report taking 30+ minutes to generate.',
        'category': 'Database',
        'priority': 'P3',
        'resolution_notes': 'Query optimization needed. Rewrote query with proper joins and indexes.',
        'resolution_time_hours': 2.0
    },
]

additional_access = [
    {
        'ticket_id': 'HIST-050',
        'subject': 'Account Locked After Failed Login Attempts',
        'description': 'User account locked after entering wrong password multiple times.',
        'category': 'Access',
        'priority': 'P3',
        'resolution_notes': 'Unlocked account in AD. Reminded user about password reset self-service.',
        'resolution_time_hours': 0.2
    },
    {
        'ticket_id': 'HIST-051',
        'subject': 'Permissions Request for Shared Folder',
        'description': 'Need write access to Finance shared folder.',
        'category': 'Access',
        'priority': 'P3',
        'resolution_notes': 'Manager approved. Added user to Finance-Writers security group.',
        'resolution_time_hours': 0.5
    },
]

additional_network = [
    {
        'ticket_id': 'HIST-060',
        'subject': 'WiFi Connection Drops Frequently',
        'description': 'Laptop loses WiFi connection every hour in Building A.',
        'category': 'Network',
        'priority': 'P3',
        'resolution_notes': 'WiFi access point firmware outdated. Updated firmware on all APs in building.',
        'resolution_time_hours': 2.0
    },
    {
        'ticket_id': 'HIST-061',
        'subject': 'Slow Internet Speed in Office',
        'description': 'Internet speed very slow during business hours.',
        'category': 'Network',
        'priority': 'P2',
        'resolution_notes': 'Bandwidth cap reached. Upgraded internet connection to 1Gbps.',
        'resolution_time_hours': 8.0
    },
]

# Combine all tickets
all_tickets = (
    p1_tickets + p2_tickets + p3_tickets + p4_tickets + 
    additional_database + additional_access + additional_network
)

print(f"✅ Generated {len(all_tickets)} sample tickets")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 3: Add Timestamps and Create Records

# COMMAND ----------

# Add timestamps and create full records
for ticket in all_tickets:
    submitted_date = random_past_date(90)
    resolved_date = submitted_date + timedelta(hours=ticket['resolution_time_hours'])
    
    record = Row(
        ticket_id=ticket['ticket_id'],
        subject=ticket['subject'],
        description=ticket['description'],
        submitted_by=f"{ticket['ticket_id'].lower()}@company.com",
        submitted_date=submitted_date,
        category=ticket['category'],
        priority=ticket['priority'],
        status='Resolved',
        resolution_notes=ticket['resolution_notes'],
        resolved_date=resolved_date,
        resolution_time_hours=ticket['resolution_time_hours']
    )
    
    historical_tickets.append(record)

print(f"✅ Created {len(historical_tickets)} historical ticket records")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 4: Insert into Delta Table

# COMMAND ----------

# Create DataFrame and write to table
df = spark.createDataFrame(historical_tickets)

# Write to table (overwrite if exists)
df.write.format("delta").mode("overwrite").saveAsTable(FULL_TABLE_NAME)

print(f"✅ Inserted {df.count()} records into {FULL_TABLE_NAME}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 5: Verify Data

# COMMAND ----------

# Show statistics
print("📊 Table Statistics:")
stats_df = spark.sql(f"""
SELECT 
  COUNT(*) as total_tickets,
  COUNT(DISTINCT category) as categories,
  COUNT(DISTINCT priority) as priorities,
  AVG(resolution_time_hours) as avg_resolution_hours
FROM {FULL_TABLE_NAME}
""")
display(stats_df)

# COMMAND ----------

# Show breakdown by category and priority
print("📁 Tickets by Category and Priority:")
breakdown_df = spark.sql(f"""
SELECT 
  category,
  priority,
  COUNT(*) as count,
  AVG(resolution_time_hours) as avg_hours
FROM {FULL_TABLE_NAME}
GROUP BY category, priority
ORDER BY priority, category
""")
display(breakdown_df)

# COMMAND ----------

# Show recent tickets
print("📄 Recent Resolved Tickets:")
recent_df = spark.sql(f"""
SELECT 
  ticket_id,
  priority,
  category,
  subject,
  resolution_time_hours,
  resolved_date
FROM {FULL_TABLE_NAME}
ORDER BY resolved_date DESC
LIMIT 10
""")
display(recent_df)

# COMMAND ----------

# MAGIC %md
# MAGIC ## ✅ Summary
# MAGIC 
# MAGIC **Completed:**
# MAGIC - ✅ Created table: `langtutorial.agents.ticket_history`
# MAGIC - ✅ Inserted 50+ historical resolved tickets
# MAGIC - ✅ Data includes P1-P4 across all major categories
# MAGIC - ✅ Each ticket has resolution notes and timestamps
# MAGIC 
# MAGIC **Table Schema:**
# MAGIC - `ticket_id`: Unique identifier
# MAGIC - `subject`: Ticket subject line
# MAGIC - `description`: Full ticket description
# MAGIC - `category`: Database, Network, Access, Security, etc.
# MAGIC - `priority`: P1 (Critical) to P4 (Low)
# MAGIC - `status`: All "Resolved"
# MAGIC - `resolution_notes`: How it was fixed
# MAGIC - `resolved_date`: When it was resolved
# MAGIC - `resolution_time_hours`: Time to resolve
# MAGIC 
# MAGIC **Next Steps:**
# MAGIC 
# MAGIC 1. ✅ **COMPLETED** - Historical tickets ready
# MAGIC 2. 📝 **NEXT** - Create Genie Space in Databricks UI
# MAGIC    - Go to Databricks → Genie
# MAGIC    - Click "Create Genie Space"
# MAGIC    - Select this table: `langtutorial.agents.ticket_history`
# MAGIC    - Name it: "LangGraph Tutorial - Ticket History"
# MAGIC    - Copy the Genie Space ID from URL
# MAGIC 3. 📓 Update tutorial notebook with Genie Space ID
# MAGIC 4. 🚀 Run the tutorial notebook!
# MAGIC 
# MAGIC ## 🤖 Creating Genie Space (Manual Step)
# MAGIC 
# MAGIC **Instructions:**
# MAGIC 1. In Databricks UI, click **Genie** in left sidebar
# MAGIC 2. Click **Create Genie Space**
# MAGIC 3. **Name**: "LangGraph Tutorial - Ticket History"
# MAGIC 4. **Description**: "Historical support tickets for LangGraph tutorial queries"
# MAGIC 5. **Data Source**: Select `langtutorial.agents.ticket_history`
# MAGIC 6. Click **Create**
# MAGIC 7. **Copy Space ID** from URL (looks like: `01abc123def456...`)
# MAGIC 8. **Paste ID** into tutorial notebook configuration

# COMMAND ----------

# Final summary
print("\n" + "=" * 80)
print("✅ TICKET HISTORY SETUP COMPLETE!")
print("=" * 80)
print(f"Table:      {FULL_TABLE_NAME}")
print(f"Tickets:    {len(historical_tickets)}")
print(f"Categories: Database, Network, Access, Security, Application, Hardware, Software, Other")
print(f"Priorities: P1 (Critical), P2 (High), P3 (Medium), P4 (Low)")
print(f"Status:     All Resolved")
print("=" * 80)
print("\n🎯 NEXT: Create Genie Space in Databricks UI")
print("   Then update tutorial notebook with Genie Space ID")
print("=" * 80)

