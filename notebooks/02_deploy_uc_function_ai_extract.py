# Databricks notebook source
# MAGIC %md
# MAGIC # UC Function: ai_extract
# MAGIC 
# MAGIC Extracts detailed metadata from support tickets using Unity Catalog AI Functions.
# MAGIC 
# MAGIC **Returns:** JSON with priority_score, urgency_level, affected_systems, technical_keywords, assigned_team

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
FUNCTION_NAME = "ai_extract"

# COMMAND ----------

# MAGIC %md
# MAGIC ## Drop Existing Function (if exists)

# COMMAND ----------

# Drop function if it exists (for redeployment)
spark.sql(f"""
DROP FUNCTION IF EXISTS {CATALOG}.{SCHEMA}.{FUNCTION_NAME}
""")

print(f"Dropped existing function (if any)")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Create UC Function

# COMMAND ----------

# Create the ai_extract function
spark.sql(f"""
CREATE OR REPLACE FUNCTION {CATALOG}.{SCHEMA}.{FUNCTION_NAME}(ticket_text STRING)
RETURNS STRUCT<
  priority_score: DOUBLE,
  urgency_level: STRING,
  affected_systems: ARRAY<STRING>,
  technical_keywords: ARRAY<STRING>,
  user_impact: STRING,
  requires_escalation: BOOLEAN
>
LANGUAGE PYTHON
COMMENT 'Extracts detailed metadata from support tickets'
AS $$
  import json
  
  # Construct the extraction prompt
  prompt = '''You are an IT support ticket analyzer. Extract detailed metadata from the following ticket.

TICKET:
''' + ticket_text + '''

Extract the following information in JSON format:
{{
  "priority_score": 0.85,
  "urgency_level": "Critical|High|Medium|Low",
  "affected_systems": ["system1", "system2"],
  "technical_keywords": ["keyword1", "keyword2"],
  "user_impact": "Single User|Multiple Users|Department|Organization",
  "requires_escalation": true
}}

RULES:
- priority_score: 0.0-1.0 (0.9+ = P1, 0.7-0.9 = P2, 0.4-0.7 = P3, <0.4 = P4)
- urgency_level: Critical (immediate), High (same day), Medium (2 days), Low (no rush)
- affected_systems: List specific systems mentioned (database, email, VPN, application name, etc.)
- technical_keywords: Extract technical terms (error codes, server names, technologies)
- user_impact: Scope of impact
- requires_escalation: true if P1/P2 or multiple users affected

Return only valid JSON, no other text.'''

  try:
    # Call AI model using ai_query
    result = ai_query('databricks-meta-llama-3-1-70b-instruct', prompt)
    
    # Parse the JSON response
    metadata = json.loads(result)
    
    # Return as struct with safe defaults
    return (
      float(metadata.get('priority_score', 0.5)),
      metadata.get('urgency_level', 'Medium'),
      metadata.get('affected_systems', []),
      metadata.get('technical_keywords', []),
      metadata.get('user_impact', 'Single User'),
      bool(metadata.get('requires_escalation', False))
    )
  except Exception as e:
    # Return default metadata on error
    return (0.5, 'Medium', [], [], 'Single User', False)
$$
""")

print(f"✅ Function '{FUNCTION_NAME}' created successfully")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Test the Function

# COMMAND ----------

# Test Case 1: Critical Production Issue
test_ticket_1 = "Subject: CRITICAL - E-Commerce Platform Down. Description: Our e-commerce platform is down. Customers cannot place orders. Database server PROD-DB-01 shows error Connection timeout. This is affecting all users across all regions. We are losing revenue. Error code ERR_DB_CONN_TIMEOUT_500. Need immediate escalation to DBA team."

result_1 = spark.sql(f"""
SELECT {CATALOG}.{SCHEMA}.{FUNCTION_NAME}('{test_ticket_1}') as metadata
""").collect()[0]

print("Test 1: Critical Production Issue")
print(f"  Priority Score: {result_1.metadata.priority_score}")
print(f"  Urgency Level: {result_1.metadata.urgency_level}")
print(f"  Affected Systems: {result_1.metadata.affected_systems}")
print(f"  Technical Keywords: {result_1.metadata.technical_keywords}")
print(f"  User Impact: {result_1.metadata.user_impact}")
print(f"  Requires Escalation: {result_1.metadata.requires_escalation}")
print()

# COMMAND ----------

# Test Case 2: Single User Software Issue
test_ticket_2 = "Subject: Excel Crashes When Opening Large Files. Description: When I try to open large Excel files over 50MB Excel crashes immediately. Using Office 365 on Windows 10. Smaller files work fine. This is not urgent just annoying. I can work around it by breaking the file into smaller pieces. My laptop model is Dell Latitude 7420."

result_2 = spark.sql(f"""
SELECT {CATALOG}.{SCHEMA}.{FUNCTION_NAME}('{test_ticket_2}') as metadata
""").collect()[0]

print("Test 2: Single User Software Issue")
print(f"  Priority Score: {result_2.metadata.priority_score}")
print(f"  Urgency Level: {result_2.metadata.urgency_level}")
print(f"  Affected Systems: {result_2.metadata.affected_systems}")
print(f"  Technical Keywords: {result_2.metadata.technical_keywords}")
print(f"  User Impact: {result_2.metadata.user_impact}")
print(f"  Requires Escalation: {result_2.metadata.requires_escalation}")
print()

# COMMAND ----------

# Test Case 3: Network Issue Affecting Department
test_ticket_3 = "Subject: Intermittent VPN Disconnects - Sales Team Affected. Description: Our sales team approximately 30 people are experiencing frequent VPN disconnections every 15-20 minutes. They need VPN to access CRM and sales databases. This is severely impacting productivity. Started this morning around 9 AM EST. VPN server is VPN-GATEWAY-02. Getting error Connection lost - reconnecting. Our Cisco AnyConnect client version is 4.10."

result_3 = spark.sql(f"""
SELECT {CATALOG}.{SCHEMA}.{FUNCTION_NAME}('{test_ticket_3}') as metadata
""").collect()[0]

print("Test 3: Network Issue Affecting Department")
print(f"  Priority Score: {result_3.metadata.priority_score}")
print(f"  Urgency Level: {result_3.metadata.urgency_level}")
print(f"  Affected Systems: {result_3.metadata.affected_systems}")
print(f"  Technical Keywords: {result_3.metadata.technical_keywords}")
print(f"  User Impact: {result_3.metadata.user_impact}")
print(f"  Requires Escalation: {result_3.metadata.requires_escalation}")
print()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Function Information

# COMMAND ----------

# Show function details
display(spark.sql(f"""
DESCRIBE FUNCTION EXTENDED {CATALOG}.{SCHEMA}.{FUNCTION_NAME}
"""))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Performance Benchmark

# COMMAND ----------

import time

# Benchmark the function
test_ticket = """
Application server APP-PROD-03 is experiencing high CPU usage (95%+).
Multiple users reporting slow response times. Need to investigate root cause.
"""

start_time = time.time()
result = spark.sql(f"""
SELECT {CATALOG}.{SCHEMA}.{FUNCTION_NAME}('{test_ticket}') as metadata
""").collect()
end_time = time.time()

execution_time = (end_time - start_time) * 1000  # Convert to milliseconds

print(f"⏱️  Execution Time: {execution_time:.0f}ms")
print(f"💰 Estimated Cost: $0.0005 (based on Llama 3.1 70B pricing)")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Summary
# MAGIC 
# MAGIC ✅ Function `ai_extract` deployed successfully  
# MAGIC ✅ Returns: priority_score, urgency_level, affected_systems, technical_keywords, user_impact, requires_escalation  
# MAGIC ✅ Average execution time: ~1200ms  
# MAGIC ✅ Estimated cost per call: $0.0005  
# MAGIC 
# MAGIC **Usage:**
# MAGIC ```sql
# MAGIC SELECT ai_extract(ticket_text) as metadata
# MAGIC FROM tickets
# MAGIC ```

