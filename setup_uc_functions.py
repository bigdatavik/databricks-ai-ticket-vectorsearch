# Databricks notebook source
# MAGIC %md
# MAGIC # Unity Catalog AI Functions Setup
# MAGIC 
# MAGIC This notebook creates the required AI Functions for the LangGraph tutorial.
# MAGIC 
# MAGIC **Run this ONCE before starting the tutorial.**
# MAGIC 
# MAGIC ## What This Creates
# MAGIC 
# MAGIC 1. **ai_classify()** - Classifies tickets by priority and category
# MAGIC 2. **ai_extract()** - Extracts metadata (emails, systems, error codes)
# MAGIC 3. **ai_gen()** - Generates helpful responses
# MAGIC 
# MAGIC ## Prerequisites
# MAGIC 
# MAGIC - Unity Catalog enabled
# MAGIC - Permissions to CREATE FUNCTION
# MAGIC - Databricks Runtime 16.4 LTS or later

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. Configuration
# MAGIC 
# MAGIC **Update these values to match your databricks.yml**

# COMMAND ----------

# ========================================
# CONFIGURATION - Update these values!
# ========================================

CATALOG = "langraph_tutorial"  # Must match databricks.yml
SCHEMA = "agents"              # Must match databricks.yml

# LLM to use for AI functions
LLM_MODEL = "databricks-meta-llama-3-1-70b-instruct"

print(f"✅ Configuration:")
print(f"   Catalog: {CATALOG}")
print(f"   Schema: {SCHEMA}")
print(f"   LLM Model: {LLM_MODEL}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. Create Catalog and Schema

# COMMAND ----------

# Create catalog (if it doesn't exist)
spark.sql(f"CREATE CATALOG IF NOT EXISTS {CATALOG}")
print(f"✅ Catalog '{CATALOG}' ready")

# Create schema (if it doesn't exist)
spark.sql(f"CREATE SCHEMA IF NOT EXISTS {CATALOG}.{SCHEMA}")
print(f"✅ Schema '{CATALOG}.{SCHEMA}' ready")

# Set as current
spark.sql(f"USE CATALOG {CATALOG}")
spark.sql(f"USE SCHEMA {SCHEMA}")
print(f"✅ Using {CATALOG}.{SCHEMA}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. Create AI Classification Function
# MAGIC 
# MAGIC Classifies support tickets into:
# MAGIC - **Priority**: P1 (Critical) → P4 (Low)
# MAGIC - **Category**: Access, Database, Network, Application, etc.
# MAGIC - **Confidence**: High, Medium, Low

# COMMAND ----------

spark.sql(f"""
CREATE OR REPLACE FUNCTION ai_classify(
  ticket_text STRING COMMENT 'The support ticket text to classify'
)
RETURNS STRUCT<
  priority: STRING COMMENT 'Priority: P1 (Critical), P2 (High), P3 (Medium), P4 (Low)',
  category: STRING COMMENT 'Category: Access, Database, Network, Application, Infrastructure, Security, Other',
  confidence: STRING COMMENT 'Confidence level: High, Medium, Low'
>
COMMENT 'Classifies support tickets by priority and category using LLM'
RETURN ai_query(
  '{LLM_MODEL}',
  CONCAT(
    'You are a support ticket classifier. Analyze this ticket and classify it.\\n\\n',
    'Priority Levels:\\n',
    '- P1: Critical/Outage - System down, data loss, security breach\\n',
    '- P2: High/Degraded - Performance issues, multiple users affected\\n',
    '- P3: Medium/Issue - Single user affected, workaround available\\n',
    '- P4: Low/Question - General inquiry, feature request\\n\\n',
    'Categories: Access, Database, Network, Application, Infrastructure, Security, Other\\n\\n',
    'Return ONLY a JSON object with: priority, category, confidence\\n\\n',
    'Ticket: ', ticket_text
  )
)
""")

print("✅ Created ai_classify() function")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4. Create AI Extraction Function
# MAGIC 
# MAGIC Extracts structured metadata from tickets:
# MAGIC - User emails
# MAGIC - System/application names
# MAGIC - Error codes
# MAGIC - Urgency indicators

# COMMAND ----------

spark.sql(f"""
CREATE OR REPLACE FUNCTION ai_extract(
  ticket_text STRING COMMENT 'The support ticket text to analyze'
)
RETURNS STRUCT<
  user_email: STRING COMMENT 'User email address if mentioned',
  system_name: STRING COMMENT 'System or application name affected',
  error_code: STRING COMMENT 'Error code or reference number',
  urgency_indicators: STRING COMMENT 'Words/phrases indicating urgency'
>
COMMENT 'Extracts key metadata from support tickets using LLM'
RETURN ai_query(
  '{LLM_MODEL}',
  CONCAT(
    'You are a support ticket analyzer. Extract structured information from this ticket.\\n\\n',
    'Extract:\\n',
    '- user_email: Email address mentioned (null if none)\\n',
    '- system_name: Name of affected system/application\\n',
    '- error_code: Any error codes, ticket IDs, or reference numbers\\n',
    '- urgency_indicators: Words indicating urgency (URGENT, ASAP, CRITICAL, etc.)\\n\\n',
    'Return ONLY a JSON object with these fields.\\n\\n',
    'Ticket: ', ticket_text
  )
)
""")

print("✅ Created ai_extract() function")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 5. Create AI Response Generation Function
# MAGIC 
# MAGIC Generates helpful support responses based on:
# MAGIC - Original ticket
# MAGIC - Knowledge base context
# MAGIC - Similar historical tickets

# COMMAND ----------

spark.sql(f"""
CREATE OR REPLACE FUNCTION ai_gen(
  ticket_text STRING COMMENT 'The support ticket text',
  context STRING COMMENT 'Knowledge base context, solutions, or similar tickets'
)
RETURNS STRING
COMMENT 'Generates a helpful support response based on ticket and context'
RETURN ai_query(
  '{LLM_MODEL}',
  CONCAT(
    'You are a helpful IT support assistant. Generate a clear, professional response to this support ticket.\\n\\n',
    'Guidelines:\\n',
    '- Be specific and actionable\\n',
    '- Reference knowledge base articles when available\\n',
    '- Include steps to resolve the issue\\n',
    '- Be empathetic and professional\\n',
    '- Keep response concise (2-4 paragraphs)\\n\\n',
    'Context/Knowledge Base:\\n', context, '\\n\\n',
    'Support Ticket:\\n', ticket_text, '\\n\\n',
    'Your Response:'
  )
)
""")

print("✅ Created ai_gen() function")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 6. Verify Functions Created

# COMMAND ----------

# List all AI functions
print("📋 All AI Functions in this schema:")
functions = spark.sql(f"SHOW FUNCTIONS IN {CATALOG}.{SCHEMA} LIKE 'ai_%'")
display(functions)

# Count functions
function_count = functions.count()
expected_count = 3

if function_count == expected_count:
    print(f"\n✅ All {expected_count} functions created successfully!")
else:
    print(f"\n⚠️ Warning: Expected {expected_count} functions, found {function_count}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 7. Test Functions
# MAGIC 
# MAGIC Let's verify each function works correctly.

# COMMAND ----------

# Test 1: Classification
print("🧪 Test 1: ai_classify()")
print("-" * 60)

test_ticket = "URGENT: Production database server is down! All users cannot access the system. Error: Connection timeout."

result = spark.sql(f"""
    SELECT ai_classify('{test_ticket}') as classification
""").collect()[0]

print(f"Ticket: {test_ticket}")
print(f"\nResult:")
print(f"  Priority: {result.classification.priority}")
print(f"  Category: {result.classification.category}")
print(f"  Confidence: {result.classification.confidence}")

assert result.classification.priority in ["P1", "P2", "P3", "P4"], "Invalid priority"
print("\n✅ Classification test passed!")

# COMMAND ----------

# Test 2: Extraction
print("🧪 Test 2: ai_extract()")
print("-" * 60)

test_ticket = "User john.doe@company.com reports error ERR-503 in the PayrollApp system. This is urgent!"

result = spark.sql(f"""
    SELECT ai_extract('{test_ticket}') as metadata
""").collect()[0]

print(f"Ticket: {test_ticket}")
print(f"\nResult:")
print(f"  User Email: {result.metadata.user_email}")
print(f"  System Name: {result.metadata.system_name}")
print(f"  Error Code: {result.metadata.error_code}")
print(f"  Urgency: {result.metadata.urgency_indicators}")

print("\n✅ Extraction test passed!")

# COMMAND ----------

# Test 3: Response Generation
print("🧪 Test 3: ai_gen()")
print("-" * 60)

test_ticket = "I need to reset my password for the corporate portal"
test_context = """
Knowledge Base Article KB-001: Password Reset
- Go to https://portal.company.com/reset
- Enter your email address
- Click 'Send Reset Link'
- Check your email and follow the link
- Create a new password (min 12 characters)
"""

result = spark.sql(f"""
    SELECT ai_gen(
        '{test_ticket}',
        '{test_context}'
    ) as response
""").collect()[0]

print(f"Ticket: {test_ticket}")
print(f"\nContext: {test_context}")
print(f"\nGenerated Response:")
print(result.response)

assert len(result.response) > 50, "Response too short"
print("\n✅ Generation test passed!")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 8. Grant Permissions (Optional)
# MAGIC 
# MAGIC If you need to grant EXECUTE permissions to specific users or groups, uncomment and run:

# COMMAND ----------

# # Grant EXECUTE to specific user
# USER_EMAIL = "user@company.com"  # Update this
# 
# for function in ["ai_classify", "ai_extract", "ai_gen"]:
#     spark.sql(f"""
#         GRANT EXECUTE ON FUNCTION {CATALOG}.{SCHEMA}.{function}
#         TO `{USER_EMAIL}`
#     """)
#     print(f"✅ Granted EXECUTE on {function} to {USER_EMAIL}")

# COMMAND ----------

# # Grant EXECUTE to a group
# GROUP_NAME = "data_scientists"  # Update this
# 
# for function in ["ai_classify", "ai_extract", "ai_gen"]:
#     spark.sql(f"""
#         GRANT EXECUTE ON FUNCTION {CATALOG}.{SCHEMA}.{function}
#         TO `{GROUP_NAME}`
#     """)
#     print(f"✅ Granted EXECUTE on {function} to group {GROUP_NAME}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## ✅ Setup Complete!
# MAGIC 
# MAGIC You're now ready to run the LangGraph tutorial!
# MAGIC 
# MAGIC ### Next Steps:
# MAGIC 
# MAGIC 1. **Open the tutorial notebook**: `tutorial/23_langraph_agent_learning.py`
# MAGIC 2. **Update configuration** in the notebook (Cmd 2):
# MAGIC    - Set CATALOG = "`langraph_tutorial`"
# MAGIC    - Set SCHEMA = "`agents`"
# MAGIC    - Set your CLUSTER_ID and WAREHOUSE_ID
# MAGIC 3. **Run the tutorial** step-by-step
# MAGIC 
# MAGIC ### Functions Created:
# MAGIC 
# MAGIC ```python
# MAGIC # You can now use these in any notebook:
# MAGIC 
# MAGIC # Classify a ticket
# MAGIC SELECT ai_classify('Database is down!')
# MAGIC 
# MAGIC # Extract metadata
# MAGIC SELECT ai_extract('User john@company.com reports ERR-500')
# MAGIC 
# MAGIC # Generate response
# MAGIC SELECT ai_gen('Password reset needed', 'KB-001: Use self-service portal')
# MAGIC ```
# MAGIC 
# MAGIC ### Troubleshooting:
# MAGIC 
# MAGIC - **Function not found**: Make sure you ran ALL cells above
# MAGIC - **Permission denied**: Ask your admin for CREATE FUNCTION permission
# MAGIC - **LLM errors**: Verify the model name is correct and accessible
# MAGIC 
# MAGIC **Happy Learning! 🎉**

# COMMAND ----------

# MAGIC %md
# MAGIC ## Summary
# MAGIC 
# MAGIC ### ✅ What Was Created:
# MAGIC 
# MAGIC | Function | Purpose | Returns |
# MAGIC |----------|---------|---------|
# MAGIC | `ai_classify()` | Classify tickets by priority & category | STRUCT (priority, category, confidence) |
# MAGIC | `ai_extract()` | Extract structured metadata | STRUCT (user_email, system_name, error_code, urgency) |
# MAGIC | `ai_gen()` | Generate helpful responses | STRING (response text) |
# MAGIC 
# MAGIC ### 📁 Location:
# MAGIC 
# MAGIC - **Catalog**: `{CATALOG}`
# MAGIC - **Schema**: `{SCHEMA}`
# MAGIC - **Full Path**: `{CATALOG}.{SCHEMA}.ai_classify`, etc.
# MAGIC 
# MAGIC ### 🔗 Resources:
# MAGIC 
# MAGIC - [Unity Catalog AI Functions Docs](https://docs.databricks.com/large-language-models/ai-functions.html)
# MAGIC - [Tutorial Notebook](tutorial/23_langraph_agent_learning.py)
# MAGIC - [Beginner Guide](BEGINNER_TUTORIAL.md)

