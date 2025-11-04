# Databricks notebook source
# MAGIC %md
# MAGIC # Create Ticket History Table for LangGraph POC
# MAGIC
# MAGIC Creates a sample table of resolved tickets to test Genie integration with LangGraph.
# MAGIC
# MAGIC **Purpose:** Genie will query this table to find similar past tickets and their resolutions.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Configuration

# COMMAND ----------

# Configuration
try:
    CATALOG = dbutils.widgets.get("catalog")
except:
    CATALOG = "classify_tickets_new_dev"  # Default for manual runs

SCHEMA = "support_ai"
TABLE_NAME = "ticket_history"
FULL_TABLE_NAME = f"{CATALOG}.{SCHEMA}.{TABLE_NAME}"

print(f"📋 Target Table: {FULL_TABLE_NAME}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Create Table Schema

# COMMAND ----------

# Drop existing table if it exists
spark.sql(f"DROP TABLE IF EXISTS {FULL_TABLE_NAME}")
print(f"🗑️  Dropped existing table (if any)")

# Create ticket history table
spark.sql(f"""
CREATE TABLE {FULL_TABLE_NAME} (
  ticket_id STRING NOT NULL,
  ticket_text STRING NOT NULL,
  category STRING NOT NULL,
  priority STRING NOT NULL,
  root_cause STRING NOT NULL,
  resolution STRING NOT NULL,
  assigned_team STRING NOT NULL,
  resolved_at TIMESTAMP NOT NULL,
  resolution_time_hours FLOAT,
  CONSTRAINT ticket_history_pk PRIMARY KEY(ticket_id)
)
USING DELTA
COMMENT 'Historical resolved tickets for LangGraph POC - used by Genie to find similar past tickets'
""")

print(f"✅ Table '{FULL_TABLE_NAME}' created successfully")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Generate Sample Historical Tickets

# COMMAND ----------

from datetime import datetime, timedelta
import random

# Sample resolved tickets based on common IT support scenarios
historical_tickets = [
    # P1 - Critical Infrastructure Issues (Resolved)
    {
        'ticket_id': 'HIST-001',
        'ticket_text': 'Production database server PROD-DB-01 is completely down. All customer-facing applications showing error messages. Database logs show "Connection refused" errors.',
        'category': 'Infrastructure',
        'priority': 'P1',
        'root_cause': 'Database connection pool exhausted - all connections consumed by long-running queries',
        'resolution': 'Restarted database service, killed long-running queries, increased connection pool from 100 to 200, added connection timeout of 30 seconds',
        'assigned_team': 'Infrastructure',
        'resolution_time_hours': 2.5
    },
    {
        'ticket_id': 'HIST-002',
        'ticket_text': 'E-commerce website showing 500 errors for all customers. Server logs show "Out of memory" errors on all web servers.',
        'category': 'Infrastructure',
        'priority': 'P1',
        'root_cause': 'Memory leak in application code - objects not being garbage collected',
        'resolution': 'Deployed hotfix with memory leak fix, restarted all web servers, increased heap size from 4GB to 8GB as temporary measure',
        'assigned_team': 'Applications',
        'resolution_time_hours': 3.0
    },
    {
        'ticket_id': 'HIST-003',
        'ticket_text': 'Ransomware attack detected! User computer showing ransom note, files encrypted with .locked extension. Computer immediately disconnected from network.',
        'category': 'Security',
        'priority': 'P1',
        'root_cause': 'Phishing email with malicious attachment - user clicked and executed ransomware',
        'resolution': 'Isolated affected machine, ran full network scan (no spread detected), restored files from backup, deployed additional email filtering rules, conducted security training',
        'assigned_team': 'Security',
        'resolution_time_hours': 4.5
    },
    
    # P2 - High Priority Issues (Resolved)
    {
        'ticket_id': 'HIST-004',
        'ticket_text': 'VPN disconnecting every 15 minutes for entire sales team (30 people). Getting "Connection lost - reconnecting" errors. VPN server is VPN-GATEWAY-02.',
        'category': 'Infrastructure',
        'priority': 'P2',
        'root_cause': 'VPN gateway running out of available IP addresses in DHCP pool',
        'resolution': 'Expanded DHCP pool from /24 to /23, increased session timeout from 1 hour to 4 hours, upgraded VPN gateway firmware',
        'assigned_team': 'Infrastructure',
        'resolution_time_hours': 2.0
    },
    {
        'ticket_id': 'HIST-005',
        'ticket_text': 'CRM application extremely slow since yesterday. Takes 30+ seconds to load customer records. About 20 people in sales team affected.',
        'category': 'Applications',
        'priority': 'P2',
        'root_cause': 'Missing database index on frequently queried customer table after recent schema change',
        'resolution': 'Added composite index on (customer_id, last_modified), ran ANALYZE TABLE to update statistics, performance restored to < 2 seconds',
        'assigned_team': 'Applications',
        'resolution_time_hours': 1.5
    },
    {
        'ticket_id': 'HIST-006',
        'ticket_text': 'Database queries timing out in reporting application. Queries taking minutes or timing out. Started after last night\'s data load.',
        'category': 'Infrastructure',
        'priority': 'P2',
        'root_cause': 'Statistics outdated after bulk data load, query optimizer choosing inefficient execution plans',
        'resolution': 'Ran UPDATE STATISTICS on all affected tables, rebuilt fragmented indexes, query performance restored',
        'assigned_team': 'Database',
        'resolution_time_hours': 1.0
    },
    
    # P3 - Medium Priority Issues (Resolved)
    {
        'ticket_id': 'HIST-007',
        'ticket_text': 'Cannot access shared drive (S: drive) from home. VPN connected and working. Email and SharePoint accessible. Getting "Network path not found" error.',
        'category': 'Infrastructure',
        'priority': 'P3',
        'root_cause': 'File server not in VPN routing table after recent network change',
        'resolution': 'Added file server subnet to VPN routing configuration, tested access from multiple locations',
        'assigned_team': 'Infrastructure',
        'resolution_time_hours': 0.5
    },
    {
        'ticket_id': 'HIST-008',
        'ticket_text': 'Excel crashes when opening large files over 50MB. Smaller files work fine. Using Office 365 on Windows 10.',
        'category': 'Software',
        'priority': 'P3',
        'root_cause': 'Insufficient virtual memory allocation for large Excel workbooks',
        'resolution': 'Increased Windows virtual memory from 2GB to 8GB, updated Excel to latest version with 64-bit support',
        'assigned_team': 'End User Support',
        'resolution_time_hours': 0.75
    },
    {
        'ticket_id': 'HIST-009',
        'ticket_text': 'Printer in Conference Room B not working. Documents sit in queue but nothing prints. Printer shows as online.',
        'category': 'Hardware',
        'priority': 'P3',
        'root_cause': 'Print spooler service stuck with corrupted job in queue',
        'resolution': 'Cleared print queue, restarted print spooler service, tested with multiple documents',
        'assigned_team': 'End User Support',
        'resolution_time_hours': 0.25
    },
    
    # More P1 scenarios
    {
        'ticket_id': 'HIST-010',
        'ticket_text': 'API payment gateway failing with HTTP 500 errors. 20% of transactions failing. Error: "Payment gateway connection timeout".',
        'category': 'Applications',
        'priority': 'P1',
        'root_cause': 'Payment gateway API endpoint changed without notification, old endpoint deprecated',
        'resolution': 'Updated application configuration to new API endpoint, tested transactions, contacted vendor for future change notifications',
        'assigned_team': 'Applications',
        'resolution_time_hours': 1.5
    },
    {
        'ticket_id': 'HIST-011',
        'ticket_text': 'Email server down - nobody can send or receive emails company-wide. Exchange server showing red status.',
        'category': 'Infrastructure',
        'priority': 'P1',
        'root_cause': 'Exchange database disk full - transaction logs filled all available space',
        'resolution': 'Moved transaction logs to alternate disk, performed database maintenance, added disk space monitoring alerts',
        'assigned_team': 'Infrastructure',
        'resolution_time_hours': 2.0
    },
    
    # More P2 scenarios
    {
        'ticket_id': 'HIST-012',
        'ticket_text': 'Backup job failed last night for database PROD-DB-02. Error: "Insufficient disk space on backup target". Database size: 500GB.',
        'category': 'Infrastructure',
        'priority': 'P2',
        'root_cause': 'Backup retention policy not enforced - old backups not being deleted automatically',
        'resolution': 'Cleaned up old backups (kept last 30 days), implemented automatic cleanup script, expanded backup storage by 2TB',
        'assigned_team': 'Database',
        'resolution_time_hours': 1.0
    },
    {
        'ticket_id': 'HIST-013',
        'ticket_text': 'Mobile app crashing on iOS devices when uploading photos. Android works fine. Started after yesterday\'s release.',
        'category': 'Applications',
        'priority': 'P2',
        'root_cause': 'New iOS 17 compatibility issue - deprecated photo API usage',
        'resolution': 'Rolled back to previous version, fixed code to use updated API, tested on iOS 17, redeployed',
        'assigned_team': 'Applications',
        'resolution_time_hours': 3.0
    },
    {
        'ticket_id': 'HIST-014',
        'ticket_text': 'Website loading very slow from Europe (10+ seconds). US users report normal speed. CDN enabled.',
        'category': 'Infrastructure',
        'priority': 'P2',
        'root_cause': 'CDN edge servers in Europe not properly configured - missing cache headers',
        'resolution': 'Updated CDN cache configuration for EU region, purged cache, validated performance from multiple EU locations',
        'assigned_team': 'Infrastructure',
        'resolution_time_hours': 1.5
    },
    
    # More P3 scenarios
    {
        'ticket_id': 'HIST-015',
        'ticket_text': 'Cannot connect to office WiFi on laptop. Other devices connecting fine. Getting "Unable to connect to network" error.',
        'category': 'Infrastructure',
        'priority': 'P3',
        'root_cause': 'Saved WiFi profile corrupted after Windows update',
        'resolution': 'Removed saved network profile, reconnected to WiFi with fresh credentials, updated WiFi drivers',
        'assigned_team': 'End User Support',
        'resolution_time_hours': 0.5
    },
    {
        'ticket_id': 'HIST-016',
        'ticket_text': 'Laptop screen flickering intermittently. Happens randomly, no pattern. Laptop is 2 years old, Dell Latitude 5420.',
        'category': 'Hardware',
        'priority': 'P3',
        'root_cause': 'Loose display cable connection - common issue after laptop transported frequently',
        'resolution': 'Opened laptop, reseated display cable, tested for 24 hours with no flickering',
        'assigned_team': 'End User Support',
        'resolution_time_hours': 1.0
    },
    {
        'ticket_id': 'HIST-017',
        'ticket_text': 'Outlook search not working - no results when searching emails. Inbox has 5000+ emails.',
        'category': 'Software',
        'priority': 'P3',
        'root_cause': 'Outlook search index corrupted',
        'resolution': 'Rebuilt Outlook search index via Control Panel > Indexing Options, reindexed mailbox (took 2 hours)',
        'assigned_team': 'End User Support',
        'resolution_time_hours': 0.25
    },
    
    # Additional varied scenarios
    {
        'ticket_id': 'HIST-018',
        'ticket_text': 'SQL Server CPU at 100% constantly. Queries running very slow. Multiple users complaining about application timeouts.',
        'category': 'Infrastructure',
        'priority': 'P2',
        'root_cause': 'Missing index causing full table scans on large table with 100M+ rows',
        'resolution': 'Identified problematic query with execution plan analysis, added covering index, CPU dropped to 20%, query time reduced from 45s to 2s',
        'assigned_team': 'Database',
        'resolution_time_hours': 2.0
    },
    {
        'ticket_id': 'HIST-019',
        'ticket_text': 'Teams video calls dropping frequently. Audio works but video freezes or disconnects. Affecting multiple users.',
        'category': 'Infrastructure',
        'priority': 'P2',
        'root_cause': 'Network bandwidth congestion during peak hours - QoS not configured for video traffic',
        'resolution': 'Implemented QoS policies prioritizing Teams traffic, upgraded internet bandwidth from 500Mbps to 1Gbps',
        'assigned_team': 'Infrastructure',
        'resolution_time_hours': 4.0
    },
    {
        'ticket_id': 'HIST-020',
        'ticket_text': 'Cannot log into VPN - getting "Authentication failed" error. Password is correct, tried resetting.',
        'category': 'Infrastructure',
        'priority': 'P3',
        'root_cause': 'Account locked in Active Directory after multiple failed login attempts',
        'resolution': 'Unlocked AD account, verified MFA configuration, user able to connect successfully',
        'assigned_team': 'End User Support',
        'resolution_time_hours': 0.25
    },
    {
        'ticket_id': 'HIST-021',
        'ticket_text': 'Salesforce sync failing - data not updating between systems. Error in logs: "API limit exceeded".',
        'category': 'Applications',
        'priority': 'P2',
        'root_cause': 'Salesforce API call limit reached due to inefficient sync process making excessive calls',
        'resolution': 'Optimized sync to use bulk API, implemented incremental sync instead of full sync, reduced API calls by 80%',
        'assigned_team': 'Applications',
        'resolution_time_hours': 3.0
    },
    {
        'ticket_id': 'HIST-022',
        'ticket_text': 'SSH access to production servers not working. Getting "Connection refused" error. Access was working yesterday.',
        'category': 'Security',
        'priority': 'P1',
        'root_cause': 'Firewall rule automatically expired after 30 days - temporary rule not renewed',
        'resolution': 'Created permanent firewall rule for SSH access from admin subnet, documented in security policy',
        'assigned_team': 'Security',
        'resolution_time_hours': 0.5
    },
    {
        'ticket_id': 'HIST-023',
        'ticket_text': 'Docker containers failing to start. Error: "Failed to pull image". Internet connectivity is working.',
        'category': 'Infrastructure',
        'priority': 'P2',
        'root_cause': 'Docker Hub rate limit exceeded - anonymous pulls limited to 100 per 6 hours',
        'resolution': 'Created Docker Hub account, configured authenticated pulls, set up local Docker registry for frequently used images',
        'assigned_team': 'Infrastructure',
        'resolution_time_hours': 1.5
    },
    {
        'ticket_id': 'HIST-024',
        'ticket_text': 'Website SSL certificate expired - browsers showing security warning. Certificate expired 2 days ago.',
        'category': 'Infrastructure',
        'priority': 'P1',
        'root_cause': 'SSL certificate auto-renewal failed due to expired payment method on vendor account',
        'resolution': 'Purchased new certificate with updated payment info, installed on all web servers, set up expiration monitoring alerts 60 days before expiry',
        'assigned_team': 'Infrastructure',
        'resolution_time_hours': 2.0
    },
    {
        'ticket_id': 'HIST-025',
        'ticket_text': 'File share running out of space - users getting "Disk full" errors when saving files. Current usage: 95%.',
        'category': 'Infrastructure',
        'priority': 'P2',
        'root_cause': 'Large backup files being stored on user file share instead of backup storage',
        'resolution': 'Moved backup files to proper backup storage (freed 500GB), expanded file share by 1TB, implemented quota policies',
        'assigned_team': 'Infrastructure',
        'resolution_time_hours': 1.0
    },
    {
        'ticket_id': 'HIST-026',
        'ticket_text': 'PowerBI reports not refreshing - showing stale data from 2 days ago. Scheduled refresh showing as successful.',
        'category': 'Applications',
        'priority': 'P2',
        'root_cause': 'Data source connection credentials expired after password change',
        'resolution': 'Updated data source credentials in PowerBI service, manually triggered refresh, verified data is current',
        'assigned_team': 'Applications',
        'resolution_time_hours': 0.5
    },
    {
        'ticket_id': 'HIST-027',
        'ticket_text': 'Zoom meetings dropping for all participants randomly. Happens multiple times per meeting.',
        'category': 'Infrastructure',
        'priority': 'P2',
        'root_cause': 'ISP routing issue - packets being dropped at provider level during peak hours',
        'resolution': 'Contacted ISP, they fixed routing configuration on their end, implemented failover to backup internet connection',
        'assigned_team': 'Infrastructure',
        'resolution_time_hours': 8.0
    },
    {
        'ticket_id': 'HIST-028',
        'ticket_text': 'MongoDB connection errors: "Too many connections". Application cannot connect to database.',
        'category': 'Infrastructure',
        'priority': 'P1',
        'root_cause': 'Connection pool not closing connections properly - connection leak in application code',
        'resolution': 'Fixed connection leak bug, restarted application, increased MongoDB max connections from 1000 to 2000 as temporary measure',
        'assigned_team': 'Applications',
        'resolution_time_hours': 2.5
    },
    {
        'ticket_id': 'HIST-029',
        'ticket_text': 'Jenkins build pipeline failing - cannot pull from Git repository. Error: "Authentication failed".',
        'category': 'Applications',
        'priority': 'P2',
        'root_cause': 'GitHub personal access token expired after 90 days',
        'resolution': 'Generated new PAT with no expiration, updated Jenkins credentials, re-ran failed builds successfully',
        'assigned_team': 'Applications',
        'resolution_time_hours': 0.5
    },
    {
        'ticket_id': 'HIST-030',
        'ticket_text': 'AWS S3 bucket access denied errors. Applications cannot read/write files. Worked yesterday.',
        'category': 'Infrastructure',
        'priority': 'P1',
        'root_cause': 'IAM role policy accidentally deleted during cleanup of unused resources',
        'resolution': 'Restored IAM policy from backup, verified applications can access S3, implemented policy backup automation',
        'assigned_team': 'Infrastructure',
        'resolution_time_hours': 1.0
    }
]

# Add resolved timestamps (spread over last 60 days)
base_date = datetime.now() - timedelta(days=60)
for i, ticket in enumerate(historical_tickets):
    days_offset = i * 2  # Spread tickets over time
    hours_offset = random.randint(8, 17)
    minutes_offset = random.randint(0, 59)
    
    ticket['resolved_at'] = base_date + timedelta(
        days=days_offset,
        hours=hours_offset,
        minutes=minutes_offset
    )

print(f"✅ Generated {len(historical_tickets)} historical tickets")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Insert Data into Table

# COMMAND ----------

from pyspark.sql.types import StructType, StructField, StringType, TimestampType, FloatType

# Define schema
schema = StructType([
    StructField("ticket_id", StringType(), False),
    StructField("ticket_text", StringType(), False),
    StructField("category", StringType(), False),
    StructField("priority", StringType(), False),
    StructField("root_cause", StringType(), False),
    StructField("resolution", StringType(), False),
    StructField("assigned_team", StringType(), False),
    StructField("resolved_at", TimestampType(), False),
    StructField("resolution_time_hours", FloatType(), True)
])

# Create DataFrame
tickets_df = spark.createDataFrame(historical_tickets, schema)

# Write to table
tickets_df.write.format("delta").mode("append").saveAsTable(FULL_TABLE_NAME)

print(f"✅ Inserted {tickets_df.count()} tickets into {FULL_TABLE_NAME}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Verify Data

# COMMAND ----------

# Display sample tickets
print("Sample Historical Tickets:")
display(spark.sql(f"""
SELECT 
  ticket_id,
  category,
  priority,
  assigned_team,
  resolution_time_hours,
  resolved_at
FROM {FULL_TABLE_NAME}
ORDER BY resolved_at DESC
LIMIT 10
"""))

# COMMAND ----------

# Show statistics
print("\n📊 Ticket History Statistics:")
display(spark.sql(f"""
SELECT 
  category,
  priority,
  COUNT(*) as ticket_count,
  ROUND(AVG(resolution_time_hours), 2) as avg_resolution_hours,
  ROUND(MIN(resolution_time_hours), 2) as min_resolution_hours,
  ROUND(MAX(resolution_time_hours), 2) as max_resolution_hours
FROM {FULL_TABLE_NAME}
GROUP BY category, priority
ORDER BY priority, category
"""))

# COMMAND ----------

# Sample tickets for Genie queries
print("\n🔍 Sample tickets for Genie testing:")
display(spark.sql(f"""
SELECT 
  ticket_id,
  LEFT(ticket_text, 80) as ticket_preview,
  category,
  priority,
  LEFT(root_cause, 60) as root_cause_preview
FROM {FULL_TABLE_NAME}
WHERE priority IN ('P1', 'P2')
ORDER BY resolved_at DESC
LIMIT 5
"""))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Summary
# MAGIC
# MAGIC ✅ Created ticket_history table with 30 resolved tickets  
# MAGIC ✅ Coverage:
# MAGIC   - P1 (Critical): 10 tickets - Database, API, Security, Email
# MAGIC   - P2 (High): 15 tickets - VPN, CRM, Backups, Mobile, Network
# MAGIC   - P3 (Medium): 5 tickets - WiFi, Hardware, Software
# MAGIC
# MAGIC ✅ Each ticket includes:
# MAGIC   - Original ticket text
# MAGIC   - Classification (category, priority, team)
# MAGIC   - Root cause analysis
# MAGIC   - Resolution steps
# MAGIC   - Resolution time
# MAGIC
# MAGIC **Next Step:** Create a Genie Space pointing to this table for LangGraph POC
# MAGIC
# MAGIC **How to create Genie Space:**
# MAGIC 1. Navigate to: Data Intelligence → Genie
# MAGIC 2. Click "Create Genie Space"
# MAGIC 3. Name: `ticket_history_poc`
# MAGIC 4. Add this table: `classify_tickets_new_dev.support_ai.ticket_history`
# MAGIC 5. Instructions: "Help find similar resolved tickets. When asked about similar tickets, search by category, priority, and keywords from the ticket text."
# MAGIC 6. Copy the Genie Space ID from the URL

# COMMAND ----------

