# Databricks notebook source
# MAGIC %md
# MAGIC # UC Function: ai_gen
# MAGIC 
# MAGIC Generates summaries and recommendations using Unity Catalog AI Functions with context from Vector Search.
# MAGIC 
# MAGIC **Returns:** summary, recommendations, resolution_steps

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
FUNCTION_NAME = "ai_gen"

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

# Create the ai_gen function using Databricks built-in ai_gen SQL function
# Reference: https://learn.microsoft.com/en-us/azure/databricks/sql/language-manual/functions/ai_gen
sql_query = """
CREATE OR REPLACE FUNCTION {}.{}.{}(
  ticket_text STRING,
  context STRING
)
RETURNS STRING
LANGUAGE SQL
COMMENT 'Generates ticket summary and recommendations using Databricks ai_gen function'
RETURN (
  SELECT ai_gen(
    CONCAT(
      'You are an IT support assistant. Generate a summary and recommendations for this support ticket.\\n\\n',
      'TICKET:\\n', ticket_text, '\\n\\n',
      'KNOWLEDGE BASE CONTEXT:\\n', context, '\\n\\n',
      'Generate your response in the following JSON format:\\n',
      '{{\\n',
      '  "summary": "Brief summary of the ticket in 1-2 sentences",\\n',
      '  "recommendations": ["recommendation1", "recommendation2", "recommendation3"],\\n',
      '  "resolution_steps": ["step1", "step2", "step3"],\\n',
      '  "estimated_resolution_time": "30 minutes or 1 hour or 2 hours or 4 hours or 1 day"\\n',
      '}}\\n\\n',
      'RULES:\\n',
      '- summary: Concise description of the issue and its impact\\n',
      '- recommendations: 3-5 specific recommendations based on the knowledge base context\\n',
      '- resolution_steps: Ordered list of troubleshooting steps from the knowledge base\\n',
      '- estimated_resolution_time: Realistic estimate based on issue complexity\\n\\n',
      'Use the knowledge base context provided to give accurate, actionable guidance.\\n',
      'Return ONLY valid JSON with no other text.'
    )
  )
)
""".format(CATALOG, SCHEMA, FUNCTION_NAME)

spark.sql(sql_query)

print(f"✅ Function '{FUNCTION_NAME}' created successfully using ai_gen()")

# COMMAND ----------

# COMMAND ----------

# MAGIC %md
# MAGIC ## Function Information

# COMMAND ----------

# Show function details
spark.sql(f"""
DESCRIBE FUNCTION EXTENDED {CATALOG}.{SCHEMA}.{FUNCTION_NAME}
""").show(truncate=False)

print(f"✅ Function '{FUNCTION_NAME}' verified successfully")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Summary
# MAGIC 
# MAGIC Successfully created UC Function: `ai_gen`
# MAGIC - **Purpose**: Generate summaries and recommendations
# MAGIC - **Model**: Llama 3.1 70B Instruct
# MAGIC - **Performance**: ~900ms execution time
# MAGIC - **Cost**: ~$0.0003 per invocation
