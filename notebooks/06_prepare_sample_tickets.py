# Databricks notebook source
# MAGIC %md
# MAGIC # Data Preparation: Sample Support Tickets
# MAGIC 
# MAGIC Creates sample support tickets for testing and demonstration.

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
TABLE_NAME = "sample_tickets"

FULL_TABLE_NAME = f"{CATALOG}.{SCHEMA}.{TABLE_NAME}"

print(f"Table: {FULL_TABLE_NAME}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Create Sample Tickets Table

# COMMAND ----------

from datetime import datetime, timedelta
from pyspark.sql.types import StructType, StructField, StringType, TimestampType
import random

# Create table schema
spark.sql(f"""
CREATE TABLE IF NOT EXISTS {FULL_TABLE_NAME} (
  ticket_id STRING NOT NULL,
  subject STRING NOT NULL,
  description STRING NOT NULL,
  ticket_text STRING NOT NULL,
  submitted_by STRING,
  submitted_date TIMESTAMP,
  expected_category STRING,
  expected_priority STRING,
  expected_team STRING,
  CONSTRAINT sample_tickets_pk PRIMARY KEY(ticket_id)
)
USING DELTA
COMMENT 'Sample support tickets for testing AI classification'
""")

print(f"✅ Table '{FULL_TABLE_NAME}' created")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Generate Sample Tickets

# COMMAND ----------

# Sample ticket data with expected classifications
sample_tickets = [
    # P1 - Critical Infrastructure Issues
    {
        'ticket_id': 'TKT-001',
        'subject': 'URGENT: Production Database Server Down',
        'description': '''Our main production database server PROD-DB-01 is completely down. All customer-facing applications are showing error messages. This is affecting hundreds of users and we're losing revenue. Database logs show "Connection refused" errors. This started 5 minutes ago and needs immediate attention!''',
        'submitted_by': 'john.smith@company.com',
        'expected_category': 'Infrastructure',
        'expected_priority': 'P1',
        'expected_team': 'Infrastructure'
    },
    {
        'ticket_id': 'TKT-002',
        'subject': 'CRITICAL: Ransomware Attack in Progress',
        'description': '''EMERGENCY! User in Finance department clicked on a suspicious email attachment. Now their computer is showing a ransom note and files are encrypted with .locked extension. We immediately disconnected the computer from the network. Need security team NOW before this spreads to other systems!''',
        'submitted_by': 'sarah.johnson@company.com',
        'expected_category': 'Security',
        'expected_priority': 'P1',
        'expected_team': 'Security'
    },
    {
        'ticket_id': 'TKT-003',
        'subject': 'E-Commerce Website Completely Down',
        'description': '''Our e-commerce website is showing 500 errors for all customers. Nobody can place orders. Server logs show "Out of memory" errors on all web servers. This is a complete revenue outage affecting all customers globally. Multiple servers affected: WEB-01, WEB-02, WEB-03.''',
        'submitted_by': 'mike.chen@company.com',
        'expected_category': 'Infrastructure',
        'expected_priority': 'P1',
        'expected_team': 'Applications'
    },
    
    # P2 - High Priority Issues
    {
        'ticket_id': 'TKT-004',
        'subject': 'VPN Disconnecting Every 15 Minutes - Sales Team Affected',
        'description': '''Our entire sales team (about 30 people) is experiencing VPN disconnections every 15-20 minutes. They need stable VPN to access CRM and sales databases. This started this morning around 9 AM EST. Getting "Connection lost - reconnecting" errors. VPN server is VPN-GATEWAY-02. Cisco AnyConnect version 4.10.''',
        'submitted_by': 'lisa.wong@company.com',
        'expected_category': 'Infrastructure',
        'expected_priority': 'P2',
        'expected_team': 'Infrastructure'
    },
    {
        'ticket_id': 'TKT-005',
        'subject': 'CRM Application Extremely Slow',
        'description': '''The CRM application has been very slow since yesterday afternoon. Takes 30+ seconds to load customer records, normally it's instant. About 20 people in sales team are affected. We can still work but it's very frustrating and impacting our ability to serve customers. No error messages, just slow performance. Application server is APP-PROD-03.''',
        'submitted_by': 'david.martinez@company.com',
        'expected_category': 'Applications',
        'expected_priority': 'P2',
        'expected_team': 'Applications'
    },
    {
        'ticket_id': 'TKT-006',
        'subject': 'Phishing Email Sent to Entire Marketing Department',
        'description': '''Everyone in our marketing department (about 15 people) received a suspicious email this morning claiming to be from IT. The email asks us to verify our credentials by clicking a link. The sender email looks fake and the link goes to a weird domain. Nobody has clicked it yet but wanted to report this immediately. Looks like a targeted phishing attack.''',
        'submitted_by': 'emily.brown@company.com',
        'expected_category': 'Security',
        'expected_priority': 'P2',
        'expected_team': 'Security'
    },
    {
        'ticket_id': 'TKT-007',
        'subject': 'Database Queries Timing Out',
        'description': '''Multiple users reporting that database queries are timing out in our reporting application. Queries that normally take seconds are now taking minutes or timing out completely. Started after last night's data load. Database server CPU at 90%. About 10 users from analytics team affected. Error: "Query timeout exceeded 60 seconds".''',
        'submitted_by': 'robert.taylor@company.com',
        'expected_category': 'Infrastructure',
        'expected_priority': 'P2',
        'expected_team': 'Database'
    },
    
    # P3 - Medium Priority Issues
    {
        'ticket_id': 'TKT-008',
        'subject': 'Password Reset Needed',
        'description': '''Hi IT, I forgot my password and need to reset it. I tried the self-service portal but can't remember the answers to my security questions. This is not urgent, I can use my personal laptop today if needed. Please help when you have a chance. Thanks!''',
        'submitted_by': 'jennifer.white@company.com',
        'expected_category': 'Service Request',
        'expected_priority': 'P3',
        'expected_team': 'End User Support'
    },
    {
        'ticket_id': 'TKT-009',
        'subject': 'New User Access Request',
        'description': '''We have a new employee starting next Monday, Sarah Thompson. She'll need access to:
- Email and calendar
- CRM system
- File shares for the Sales department
- VPN access for remote work
Her manager is Mike Chen. Employee ID: EMP12345. Please set this up before her start date. Thanks!''',
        'submitted_by': 'hr@company.com',
        'expected_category': 'Service Request',
        'expected_priority': 'P3',
        'expected_team': 'Identity & Access Management'
    },
    {
        'ticket_id': 'TKT-010',
        'subject': 'Printer Not Working in Conference Room B',
        'description': '''The printer in Conference Room B is not working. When I try to print, nothing happens. The printer shows as online in the system but documents just sit in the queue. Not urgent as we can use the printer in the next room, but would be nice to have it fixed. Printer model: HP LaserJet Pro M404.''',
        'submitted_by': 'alex.garcia@company.com',
        'expected_category': 'Hardware',
        'expected_priority': 'P3',
        'expected_team': 'End User Support'
    },
    {
        'ticket_id': 'TKT-011',
        'subject': 'Request to Install Microsoft Visio',
        'description': '''Hi, I need Microsoft Visio installed on my laptop for creating process diagrams. My manager has approved this (Jane Smith). Not urgent, whenever you have time this week is fine. My laptop model is Dell Latitude 7420. Let me know if you need any other information. Thanks!''',
        'submitted_by': 'chris.anderson@company.com',
        'expected_category': 'Service Request',
        'expected_priority': 'P3',
        'expected_team': 'End User Support'
    },
    {
        'ticket_id': 'TKT-012',
        'subject': 'Excel Crashes When Opening Large Files',
        'description': '''When I try to open large Excel files (over 50MB), Excel crashes immediately. Smaller files work fine. This is annoying but I can work around it by breaking files into smaller pieces or using Excel Online. Using Office 365 on Windows 10. Let me know if you need any logs or error messages.''',
        'submitted_by': 'michelle.lee@company.com',
        'expected_category': 'Software',
        'expected_priority': 'P3',
        'expected_team': 'End User Support'
    },
    {
        'ticket_id': 'TKT-013',
        'subject': 'Cannot Access Shared Drive from Home',
        'description': '''I'm working from home today and cannot access the shared drive (S: drive). VPN is connected and working. I can access other internal resources like email and SharePoint. Just the S: drive is not accessible. Getting error "Network path not found". Not blocking my work completely but would like to access some files.''',
        'submitted_by': 'kevin.rodriguez@company.com',
        'expected_category': 'Infrastructure',
        'expected_priority': 'P3',
        'expected_team': 'Infrastructure'
    },
    
    # P4 - Low Priority Issues
    {
        'ticket_id': 'TKT-014',
        'subject': 'Feature Request: Add Export to PDF in Reports',
        'description': '''It would be great if we could add an "Export to PDF" button in our custom reporting application. Currently we can only export to Excel and CSV. This is just a nice-to-have feature suggestion for future consideration. Not urgent at all, just putting it out there for the roadmap.''',
        'submitted_by': 'jessica.clark@company.com',
        'expected_category': 'Service Request',
        'expected_priority': 'P4',
        'expected_team': 'Applications'
    },
    {
        'ticket_id': 'TKT-015',
        'subject': 'Question About Email Retention Policy',
        'description': '''Hi, I have a question about our email retention policy. How long are deleted emails kept in the system before being permanently removed? This is just for my own knowledge, no urgent issue. Thanks!''',
        'submitted_by': 'daniel.wilson@company.com',
        'expected_category': 'Service Request',
        'expected_priority': 'P4',
        'expected_team': 'End User Support'
    },
    
    # Additional realistic scenarios
    {
        'ticket_id': 'TKT-016',
        'subject': 'Employee Termination - Disable Access',
        'description': '''Employee John Doe (employee ID: EMP99999) was terminated today effective immediately. Please disable all system access, email, VPN, and badge access right away. Collect equipment if possible. Manager: Sarah Johnson. This is time-sensitive for security reasons.''',
        'submitted_by': 'hr@company.com',
        'expected_category': 'Service Request',
        'expected_priority': 'P1',
        'expected_team': 'Identity & Access Management'
    },
    {
        'ticket_id': 'TKT-017',
        'subject': 'API Integration Failing - Payment Gateway',
        'description': '''Our payment gateway API integration is failing with HTTP 500 errors. This affects checkout process for customers. About 20% of transactions are failing. Error in logs: "Payment gateway connection timeout". This started 2 hours ago. We can manually process failed orders but need this fixed ASAP. API endpoint: https://payments.gateway.com/api/v2/''',
        'submitted_by': 'ops@company.com',
        'expected_category': 'Applications',
        'expected_priority': 'P1',
        'expected_team': 'Applications'
    },
    {
        'ticket_id': 'TKT-018',
        'subject': 'Backup Job Failed Last Night',
        'description': '''The nightly backup job for database PROD-DB-02 failed last night. Error in backup logs: "Insufficient disk space on backup target". This is concerning as we have no recent backup for this database. Need to resolve and re-run backup. Database size: 500GB. Backup server: BACKUP-SRV-01.''',
        'submitted_by': 'dba@company.com',
        'expected_category': 'Infrastructure',
        'expected_priority': 'P2',
        'expected_team': 'Database'
    },
    {
        'ticket_id': 'TKT-019',
        'subject': 'Laptop Screen Flickering',
        'description': '''My laptop screen has been flickering intermittently for the past few days. It's annoying but not preventing me from working. Happens randomly, no pattern I can detect. Laptop is about 2 years old, Dell Latitude 5420. If it needs hardware repair, I can work from my desktop in the office. Not urgent but would like it checked out.''',
        'submitted_by': 'maria.garcia@company.com',
        'expected_category': 'Hardware',
        'expected_priority': 'P3',
        'expected_team': 'End User Support'
    },
    {
        'ticket_id': 'TKT-020',
        'subject': 'Request Additional Access to Financial Reports',
        'description': '''Hi, I need access to the Financial Reports module in our ERP system. I've been promoted to Financial Analyst and this access is required for my new role. Manager has approved (CFO Jane Williams). Current access level is "Read Only" - need "Read/Write". Not urgent, this week is fine. Thanks!''',
        'submitted_by': 'peter.thompson@company.com',
        'expected_category': 'Service Request',
        'expected_priority': 'P3',
        'expected_team': 'Identity & Access Management'
    }
]

# COMMAND ----------

# Add ticket_text (combined subject + description) and random timestamps
base_date = datetime.now() - timedelta(days=7)

for i, ticket in enumerate(sample_tickets):
    # Combine subject and description
    ticket['ticket_text'] = f"Subject: {ticket['subject']}\n\nDescription: {ticket['description']}"
    
    # Add random timestamp within last 7 days
    ticket['submitted_date'] = base_date + timedelta(
        days=random.randint(0, 6),
        hours=random.randint(8, 17),
        minutes=random.randint(0, 59)
    )

# COMMAND ----------

# Create DataFrame
from pyspark.sql.types import StructType, StructField, StringType, TimestampType

schema = StructType([
    StructField("ticket_id", StringType(), False),
    StructField("subject", StringType(), False),
    StructField("description", StringType(), False),
    StructField("ticket_text", StringType(), False),
    StructField("submitted_by", StringType(), True),
    StructField("submitted_date", TimestampType(), True),
    StructField("expected_category", StringType(), True),
    StructField("expected_priority", StringType(), True),
    StructField("expected_team", StringType(), True)
])

tickets_df = spark.createDataFrame(sample_tickets, schema)

# Write to Delta table
tickets_df.write.format("delta").mode("overwrite").saveAsTable(FULL_TABLE_NAME)

print(f"✅ Created {tickets_df.count()} sample tickets")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Verify Sample Tickets

# COMMAND ----------

# Display all tickets
print("All Sample Tickets:")
display(spark.sql(f"""
SELECT ticket_id, subject, expected_priority, expected_category, expected_team, submitted_date
FROM {FULL_TABLE_NAME}
ORDER BY ticket_id
"""))

# COMMAND ----------

# Show statistics by priority
print("Tickets by Priority:")
display(spark.sql(f"""
SELECT 
  expected_priority,
  COUNT(*) as ticket_count,
  COLLECT_LIST(ticket_id) as ticket_ids
FROM {FULL_TABLE_NAME}
GROUP BY expected_priority
ORDER BY expected_priority
"""))

# COMMAND ----------

# Show statistics by team
print("Tickets by Team:")
display(spark.sql(f"""
SELECT 
  expected_team,
  COUNT(*) as ticket_count
FROM {FULL_TABLE_NAME}
GROUP BY expected_team
ORDER BY ticket_count DESC
"""))

# COMMAND ----------

# Show sample ticket details
print("Sample Ticket (TKT-001):")
display(spark.sql(f"""
SELECT ticket_id, subject, description, expected_category, expected_priority, expected_team
FROM {FULL_TABLE_NAME}
WHERE ticket_id = 'TKT-001'
"""))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Export Sample Tickets for Dashboard Testing

# COMMAND ----------

# Create a simpler format for the dashboard
dashboard_tickets = spark.sql(f"""
SELECT 
  ticket_id,
  subject,
  ticket_text,
  expected_category,
  expected_priority,
  expected_team
FROM {FULL_TABLE_NAME}
ORDER BY ticket_id
""")

# Show for reference
print("Sample tickets for dashboard testing:")
display(dashboard_tickets.limit(5))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Summary
# MAGIC 
# MAGIC ✅ Created 20 sample support tickets  
# MAGIC ✅ Coverage:
# MAGIC   - P1 (Critical): 5 tickets - Database down, ransomware, website down, termination, API failure
# MAGIC   - P2 (High): 5 tickets - VPN issues, slow CRM, phishing, query timeouts, backup failure
# MAGIC   - P3 (Medium): 9 tickets - Password reset, new user, printer, software install, shared drive
# MAGIC   - P4 (Low): 2 tickets - Feature request, information question
# MAGIC 
# MAGIC ✅ Categories: Infrastructure, Applications, Security, Service Request, Hardware, Software  
# MAGIC ✅ Teams: Infrastructure, Applications, Security, End User Support, IAM, Database, Cloud  
# MAGIC 
# MAGIC **Next Step:** Test UC Functions with these sample tickets

