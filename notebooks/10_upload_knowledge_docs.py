# Databricks notebook source
# MAGIC %md
# MAGIC # Upload Knowledge Base Files to UC Volume

# COMMAND ----------

import os

# Configuration
try:
    CATALOG = dbutils.widgets.get("catalog")
except:
    CATALOG = "classify_tickets_new_dev"  # Default for manual runs
SCHEMA = "support_ai"
VOLUME = "knowledge_docs"
VOLUME_PATH = f"/Volumes/{CATALOG}/{SCHEMA}/{VOLUME}"

print(f"Volume path: {VOLUME_PATH}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Create Volume if it doesn't exist

# COMMAND ----------

# Create volume
try:
    spark.sql(f"""
    CREATE VOLUME IF NOT EXISTS {CATALOG}.{SCHEMA}.{VOLUME}
    COMMENT 'Knowledge base documents for vector search'
    """)
    print(f"✅ Volume created: {CATALOG}.{SCHEMA}.{VOLUME}")
except Exception as e:
    print(f"Volume creation: {e}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Upload Knowledge Base Documents

# COMMAND ----------

# Knowledge base files content
knowledge_files = {
    "IT_infrastructure_runbook.txt": """IT INFRASTRUCTURE RUNBOOK
=========================

This document provides troubleshooting procedures and best practices for IT infrastructure issues.

SERVER TROUBLESHOOTING
---------------------

High CPU Usage (Priority P1):
- Check running processes with top/htop command
- Identify resource-intensive applications
- Review application logs for errors
- Consider scaling up resources if sustained
- Escalate to Infrastructure team if above 90% for 10+ minutes

Database Connection Issues (Priority P1):
- Verify database server status
- Check connection pool settings
- Review firewall rules
- Test connectivity from application server
- Check for connection leaks in application
- Escalate to Database team immediately

Server Downtime (Priority P1):
- Check server status in monitoring dashboard
- Attempt ping and SSH connectivity
- Review system logs for crash indicators
- Check hardware health indicators
- Initiate failover procedures if available
- Escalate to Infrastructure team immediately

Network Connectivity Problems (Priority P2):
- Test connectivity with ping and traceroute
- Check switch and router status
- Verify VLAN configuration
- Review firewall logs
- Check DNS resolution
- Escalate to Network team if unresolved in 15 minutes

Storage Space Issues (Priority P2):
- Check disk usage with df -h command
- Identify large files and directories
- Review log rotation settings
- Clean up temporary files
- Archive old data if necessary
- Escalate if >90% capacity

Application Deployment Issues (Priority P2):
- Review deployment logs
- Check application configuration
- Verify dependencies are installed
- Test connectivity to required services
- Rollback if necessary
- Escalate to Development team

Performance Degradation (Priority P3):
- Review system resource utilization
- Check application response times
- Analyze recent changes
- Review caching effectiveness
- Consider performance tuning
- Schedule maintenance window if needed""",

    "application_support_guide.txt": """APPLICATION SUPPORT GUIDE
========================

Common application issues and their resolutions.

CRM APPLICATION ISSUES
---------------------

Slow Performance (Priority P2):
- Clear browser cache and cookies
- Check internet connection speed
- Verify no other bandwidth-intensive applications running
- Review recent CRM updates or changes
- Check CRM server status in monitoring
- Escalate to Applications team if persists >30 minutes

Login Failures (Priority P2):
- Verify username and password
- Check if account is locked or disabled
- Verify user has appropriate licenses
- Clear browser cache
- Try different browser
- Reset password if necessary
- Escalate to Identity & Access team

Data Synchronization Issues (Priority P2):
- Force manual sync if available
- Check network connectivity
- Verify sync service is running
- Review sync logs for errors
- Check for data conflicts
- Escalate to Applications team

Email Integration Not Working (Priority P2):
- Verify email credentials
- Check OAuth authorization status
- Test email connectivity separately
- Review email client settings
- Re-authorize integration if needed
- Escalate to Applications team

Missing Data or Records (Priority P1):
- Check if user has proper permissions
- Verify data filters are not hiding records
- Check if records were accidentally deleted
- Review audit logs
- Attempt data recovery if deleted recently
- Escalate to Applications team immediately

Custom Reports Not Loading (Priority P3):
- Refresh the report
- Check if underlying data source is available
- Verify report permissions
- Try running report with different parameters
- Clear report cache
- Contact Applications team

Mobile App Crashes (Priority P2):
- Update app to latest version
- Clear app cache and data
- Uninstall and reinstall app
- Check device OS compatibility
- Review app error logs if available
- Escalate to Applications team""",

    "security_incident_playbook.txt": """SECURITY INCIDENT RESPONSE PLAYBOOK
===================================

Procedures for handling security incidents and threats.

RANSOMWARE / MALWARE DETECTION
------------------------------

Immediate Actions (Priority P1):
1. DISCONNECT affected device from network immediately
2. Do NOT turn off the device (preserves evidence)
3. Document what the user observed (error messages, ransom notes)
4. Take photos of screens if ransom note is displayed
5. Notify Security team immediately
6. Isolate potentially affected network segments
7. Begin checking other devices for similar infections
8. Review backup status and integrity
9. Escalate to Security team - DO NOT ATTEMPT REMEDIATION YOURSELF

Prevention Measures:
- Keep antivirus definitions updated
- Enable real-time protection
- Block suspicious file types in email
- Implement application whitelisting
- Regular security awareness training
- Maintain offline backups

PHISHING EMAIL REPORTS
----------------------

Response Procedure (Priority P2):
1. Thank user for reporting
2. Do NOT click any links or open attachments
3. Document sender address and email content
4. Check if other users received similar emails
5. Report to Security team
6. Block sender if confirmed phishing
7. Send security alert to all users if widespread
8. Update email filters

Indicators of Phishing:
- Suspicious sender address
- Urgency or threats
- Requests for credentials
- Poor grammar/spelling
- Mismatched URLs
- Unexpected attachments
- Too good to be true offers

SUSPICIOUS USER ACTIVITY
------------------------

Investigation Steps (Priority P2):
1. Document the suspicious activity
2. Check user account activity logs
3. Review recent access patterns
4. Verify if account may be compromised
5. Check for data exfiltration attempts
6. Disable account if compromise suspected
7. Reset password and revoke active sessions
8. Escalate to Security team
9. Preserve evidence for investigation

UNAUTHORIZED ACCESS ATTEMPTS
----------------------------

Response (Priority P1):
1. Document the attempt (IP, timestamp, method)
2. Check if account was compromised
3. Enable additional authentication if available
4. Review firewall and access logs
5. Block attacking IP addresses
6. Reset affected user credentials
7. Notify Security team immediately
8. Monitor for continued attempts

DATA BREACH SUSPECTED
--------------------

Critical Steps (Priority P1):
1. DO NOT NOTIFY THE USER YET
2. Immediately contact Security team
3. Document all known facts
4. Preserve all evidence
5. Do not modify any systems
6. Follow Security team instructions exactly
7. Prepare for potential legal requirements
8. Begin incident response documentation""",

    "user_access_policies.txt": """USER ACCESS & IDENTITY MANAGEMENT POLICIES
==========================================

Procedures for user account management and access requests.

NEW USER PROVISIONING
--------------------

Standard Process (Priority P3):
1. Verify request from manager or HR
2. Determine user role and department
3. Select appropriate access template
4. Create AD/Azure AD account
5. Assign email mailbox
6. Grant application access based on role:
   - CRM access for Sales team
   - HR systems for HR department
   - Development tools for Engineering
   - Financial systems with additional approval
7. Set up VPN access if remote worker
8. Enable MFA (required for all users)
9. Send welcome email with credentials
10. Schedule follow-up for access verification

Timeline: Complete within 24 hours of request

PASSWORD RESETS
--------------

Self-Service (Priority P3):
- Users should use self-service portal first
- Requires security questions or MFA
- Available 24/7 online

Help Desk Reset (Priority P3):
1. Verify user identity (employee ID, personal info)
2. Generate temporary password
3. Require password change on next login
4. Enable MFA if not already enabled
5. Document in ticketing system

Timeline: Resolve within 2 hours

ACCOUNT LOCKOUTS
---------------

Unlocking Accounts (Priority P2):
1. Verify user identity
2. Check reason for lockout (failed attempts, expired password)
3. Unlock account in AD/Azure AD
4. If suspicious, verify with user before unlocking
5. Reset password if security concern
6. Review recent login attempts
7. Enable additional security if needed

Timeline: Resolve within 1 hour

ACCESS MODIFICATIONS
-------------------

Adding Access (Priority P3):
1. Verify manager approval
2. Check business justification
3. Assign additional permissions
4. Document changes
5. Set expiration date if temporary
6. Notify user of new access

Removing Access (Priority P2):
1. Verify authorization
2. Remove permissions immediately
3. Document removal
4. Verify removal was successful
5. Notify requestor

OFFBOARDING
----------

User Termination (Priority P1):
1. Receive notification from HR
2. IMMEDIATELY disable AD/Azure AD account
3. Revoke all application access
4. Disable VPN access
5. Forward email to manager (if requested)
6. Wipe mobile devices remotely
7. Disable badge access
8. Archive user data per retention policy
9. Document all actions taken

Timeline: Complete within 1 hour of notification

VPN ACCESS REQUESTS
------------------

Setup Process (Priority P2):
1. Verify remote work approval
2. Install VPN client if needed
3. Create VPN credentials
4. Test connectivity
5. Provide user documentation
6. Enable MFA for VPN
7. Set up split tunneling if required

Troubleshooting (Priority P2):
- Verify credentials
- Check VPN client version
- Review firewall settings
- Test internet connectivity
- Check VPN server capacity
- Review VPN logs
- Escalate to Network team if needed""",

    "ticket_classification_rules.txt": """TICKET CLASSIFICATION RULES
===========================

Guidelines for prioritizing and routing support tickets.

PRIORITY DEFINITIONS
-------------------

P1 - Critical (Response: Immediate, Resolution: 4 hours):
- Production systems completely down
- Security breaches or active attacks
- Data loss or corruption
- Ransomware or malware infection
- Complete loss of critical functionality
- Affecting multiple users (>50)
- Revenue-impacting issues
- Executive-level escalations

Examples:
- "Production database is down"
- "Ransomware detected on server"
- "Customer-facing website is down"
- "Email system not working for entire company"

P2 - High (Response: 1 hour, Resolution: 8 hours):
- Degraded performance of critical systems
- Partial functionality loss
- Affecting multiple users (10-50)
- Security concerns (phishing, suspicious activity)
- VPN access issues for remote workers
- Important integrations failing
- Workaround available but not ideal

Examples:
- "CRM running very slow"
- "VPN disconnecting frequently"
- "Phishing email received"
- "Cannot access file share"

P3 - Medium (Response: 4 hours, Resolution: 24 hours):
- Single user issues
- Non-critical functionality
- Access requests
- Password resets
- Minor bugs or glitches
- Feature requests
- Questions about system usage
- Workaround exists and is acceptable

Examples:
- "Forgot my password"
- "Need access to new application"
- "Printer not working"
- "How do I do X in the system?"

P4 - Low (Response: 8 hours, Resolution: 48 hours):
- Informational requests
- Enhancement requests
- Cosmetic issues
- Documentation requests
- Training requests
- General inquiries

Examples:
- "Can we add this feature?"
- "Documentation is outdated"
- "Suggestion for improvement"

CATEGORY ASSIGNMENT
------------------

Hardware:
- Physical device issues
- Printer problems
- Monitor/keyboard/mouse issues
- Laptop/desktop problems
- Server hardware failures
- Network equipment issues

Software:
- Application errors
- Software installation requests
- License issues
- Application performance
- Software updates
- Bug reports

Security:
- Malware/ransomware
- Phishing attempts
- Suspicious activity
- Security policy violations
- Vulnerability reports
- Data breach concerns

Infrastructure:
- Server issues
- Network connectivity
- Database problems
- Storage issues
- Backup problems
- System performance

Service Request:
- Access requests
- New user setup
- Termination requests
- Permission changes
- VPN setup
- Equipment requests

TEAM ROUTING
-----------

Infrastructure Team:
- Server administration
- Database issues
- Backup and recovery
- Storage management
- System monitoring
- Performance optimization

Applications Team:
- Business application support
- CRM, ERP, HR systems
- Application troubleshooting
- Integration issues
- Application deployment
- Custom development

Security Team:
- Security incidents
- Malware removal
- Access violations
- Security assessments
- Compliance issues
- Security awareness

End User Support:
- Desktop/laptop support
- Password resets
- Basic troubleshooting
- User training
- Hardware issues
- Printer support

Identity & Access Management:
- User provisioning
- Access requests
- Permission changes
- Password policies
- MFA setup
- Account management

Database Team:
- Database administration
- Query optimization
- Backup/restore
- Database performance
- Schema changes
- Database security

Cloud Team:
- Cloud infrastructure
- Azure/AWS issues
- Cloud migrations
- Cost optimization
- Cloud security
- Scalability

Network Team:
- Network connectivity
- VPN issues
- Firewall rules
- Bandwidth problems
- Network security
- Network design

URGENCY INDICATORS
-----------------

Critical Urgency:
- "DOWN", "CRASHED", "NOT WORKING AT ALL"
- "EMERGENCY", "URGENT", "CRITICAL"
- "AFFECTING EVERYONE", "COMPANY-WIDE"
- "LOSING MONEY", "REVENUE IMPACT"
- "SECURITY BREACH", "HACKED"
- "RANSOMWARE", "MALWARE"

High Urgency:
- "SLOW", "DEGRADED PERFORMANCE"
- "MULTIPLE USERS AFFECTED"
- "WORKAROUND NEEDED"
- "SUSPICIOUS", "PHISHING"
- "DISCONNECTING", "INTERMITTENT"

Medium Urgency:
- "CANNOT", "UNABLE TO"
- "ERROR MESSAGE"
- "NOT SURE HOW"
- "LOCKED OUT"
- "FORGOT PASSWORD"

Low Urgency:
- "WHEN POSSIBLE"
- "NOT URGENT"
- "SUGGESTION"
- "QUESTION ABOUT"
- "WOULD LIKE TO"""
}

# COMMAND ----------

# Upload each file to the volume
for filename, content in knowledge_files.items():
    file_path = f"{VOLUME_PATH}/{filename}"
    
    try:
        # Write content to volume using dbutils
        dbutils.fs.put(file_path, content, overwrite=True)
        print(f"✅ Uploaded: {filename}")
    except Exception as e:
        print(f"❌ Failed to upload {filename}: {e}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Verify Upload

# COMMAND ----------

# List files in volume
print(f"\nFiles in {VOLUME_PATH}:")
files = dbutils.fs.ls(VOLUME_PATH)
for file in files:
    print(f"  - {file.name} ({file.size} bytes)")

print(f"\n✅ Total files: {len(files)}")

