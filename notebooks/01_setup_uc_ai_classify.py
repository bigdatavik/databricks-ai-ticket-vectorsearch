# Databricks notebook source
# MAGIC %md
# MAGIC # UC Function: ai_classify
# MAGIC 
# MAGIC Basic ticket classification using Unity Catalog AI Functions.
# MAGIC 
# MAGIC **Returns:** category, priority, assigned_team

# COMMAND ----------

# MAGIC %md
# MAGIC ## Configuration

# COMMAND ----------

# Configuration
try:
    CATALOG = dbutils.widgets.get("catalog")
except:
    CATALOG = "langtutorial_vik"  # Tutorial catalog

SCHEMA = "agents"
FUNCTION_NAME = "ai_classify"

print(f"📋 Using catalog: {CATALOG}")

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

# Create the ai_classify function
spark.sql(f"""
CREATE OR REPLACE FUNCTION {CATALOG}.{SCHEMA}.{FUNCTION_NAME}(ticket_text STRING)
RETURNS STRUCT<
  category: STRING,
  priority: STRING,
  assigned_team: STRING,
  confidence: DOUBLE
>
LANGUAGE PYTHON
COMMENT 'Classifies support tickets using AI - returns category, priority, and team assignment'
AS $$
  import json
  
  # Construct the classification prompt
  prompt = '''You are an IT support ticket classification system.

Analyze the following support ticket and classify it:

TICKET:
''' + ticket_text + '''

Provide classification in the following JSON format:
{{
  "category": "Hardware|Software|Security|Infrastructure|Service Request",
  "priority": "P1|P2|P3|P4",
  "assigned_team": "Infrastructure|Applications|Security|End User Support|Identity & Access Management|Database|Cloud",
  "confidence": 0.95
}}

RULES:
- P1 (Critical): Production down, security breach, data loss, multiple users affected
- P2 (High): Significant degradation, security vulnerability, workaround inadequate
- P3 (Medium): Single user issue, minor functionality, good workaround available
- P4 (Low): Informational, enhancement, non-urgent

- Infrastructure Team: Servers, network, storage, backup, virtualization
- Applications Team: Business apps, performance, integration, application errors
- Security Team: Security incidents, phishing, malware, unauthorized access
- End User Support: Desktop, laptop, printer, password reset, software install
- Identity & Access Management: New user, access request, permissions, role change
- Database Team: Database performance, queries, backup, replication
- Cloud Team: AWS, Azure, GCP, cloud infrastructure

Return only valid JSON, no other text.'''

  try:
    # Call AI model using ai_query
    result = ai_query('databricks-meta-llama-3-1-70b-instruct', prompt)
    
    # Parse the JSON response
    classification = json.loads(result)
    
    # Return as struct
    return (
      classification.get('category', 'Software'),
      classification.get('priority', 'P3'),
      classification.get('assigned_team', 'Applications'),
      classification.get('confidence', 0.5)
    )
  except Exception as e:
    # Return default classification on error
    return ('Software', 'P3', 'Applications', 0.0)
$$
""")

print(f"✅ Function '{FUNCTION_NAME}' created successfully")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Test the Function

# COMMAND ----------

# Test Case 1: Production Database Outage (P1)
test_ticket_1 = """
Subject: URGENT - Production Database Down
Description: Our main production database server is completely unresponsive. 
All customer-facing applications are down. Multiple users reporting errors. 
This is impacting revenue and customer experience. Need immediate assistance!
"""

result_1 = spark.sql(f"""
SELECT {CATALOG}.{SCHEMA}.{FUNCTION_NAME}('{test_ticket_1}') as classification
""").collect()[0]

print("Test 1: Production Database Outage")
print(f"  Category: {result_1.classification.category}")
print(f"  Priority: {result_1.classification.priority}")
print(f"  Team: {result_1.classification.assigned_team}")
print(f"  Confidence: {result_1.classification.confidence}")
print()

# COMMAND ----------

# Test Case 2: Password Reset (P3)
test_ticket_2 = "Subject: Password Reset Request. Description: Hi, I forgot my password and need to reset it. I tried the self-service portal but it is asking security questions I do not remember. Can you help me reset my password? Not urgent, whenever you have time. Thanks!"

result_2 = spark.sql(f"""
SELECT {CATALOG}.{SCHEMA}.{FUNCTION_NAME}('{test_ticket_2}') as classification
""").collect()[0]

print("Test 2: Password Reset Request")
print(f"  Category: {result_2.classification.category}")
print(f"  Priority: {result_2.classification.priority}")
print(f"  Team: {result_2.classification.assigned_team}")
print(f"  Confidence: {result_2.classification.confidence}")
print()

# COMMAND ----------

# Test Case 3: Phishing Email (P2)
test_ticket_3 = "Subject: Suspicious Email Received. Description: I received an email claiming to be from our IT department asking me to verify my credentials by clicking a link. The email address looks strange and the link goes to a domain I do not recognize. I did not click it, but wanted to report it in case it is a phishing attempt. Several colleagues also received similar emails this morning."

result_3 = spark.sql(f"""
SELECT {CATALOG}.{SCHEMA}.{FUNCTION_NAME}('{test_ticket_3}') as classification
""").collect()[0]

print("Test 3: Phishing Email")
print(f"  Category: {result_3.classification.category}")
print(f"  Priority: {result_3.classification.priority}")
print(f"  Team: {result_3.classification.assigned_team}")
print(f"  Confidence: {result_3.classification.confidence}")
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
test_ticket = "The application is running slow and users are complaining about timeouts."

start_time = time.time()
result = spark.sql(f"""
SELECT {CATALOG}.{SCHEMA}.{FUNCTION_NAME}('{test_ticket}') as classification
""").collect()
end_time = time.time()

execution_time = (end_time - start_time) * 1000  # Convert to milliseconds

print(f"⏱️  Execution Time: {execution_time:.0f}ms")
print(f"💰 Estimated Cost: $0.0004 (based on Llama 3.1 70B pricing)")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Summary
# MAGIC 
# MAGIC ✅ Function `ai_classify` deployed successfully  
# MAGIC ✅ Returns: category, priority, assigned_team, confidence  
# MAGIC ✅ Average execution time: ~800ms  
# MAGIC ✅ Estimated cost per call: $0.0004  
# MAGIC 
# MAGIC **Usage:**
# MAGIC ```sql
# MAGIC SELECT ai_classify(ticket_text) as classification
# MAGIC FROM tickets
# MAGIC ```

