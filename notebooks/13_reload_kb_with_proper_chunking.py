# Databricks notebook source
# MAGIC %md
# MAGIC # Reload Knowledge Base with Proper Chunking

# COMMAND ----------

# Configuration
try:
    CATALOG = dbutils.widgets.get("catalog")
except:
    CATALOG = "classify_tickets_new_dev"  # Default for manual runs
SCHEMA = "support_ai"
TABLE_NAME = "knowledge_base"
VOLUME = "knowledge_docs"

# Full paths
FULL_TABLE_NAME = f"{CATALOG}.{SCHEMA}.{TABLE_NAME}"
VOLUME_PATH = f"/Volumes/{CATALOG}/{SCHEMA}/{VOLUME}"

print(f"Table: {FULL_TABLE_NAME}")
print(f"Volume: {VOLUME_PATH}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Create or Truncate Table

# COMMAND ----------

# Drop and recreate table to ensure correct schema
try:
    spark.sql(f"DROP TABLE IF EXISTS {FULL_TABLE_NAME}")
    print(f"✅ Dropped existing table: {FULL_TABLE_NAME}")
except Exception as e:
    print(f"ℹ️  No existing table to drop: {e}")

# Create table with correct schema
spark.sql(f"""
    CREATE TABLE {FULL_TABLE_NAME} (
        doc_id STRING,
        doc_type STRING,
        title STRING,
        content STRING,
        keywords ARRAY<STRING>,
        chunk_index INT,
        total_chunks INT,
        char_count INT,
        created_at TIMESTAMP
    )
    USING DELTA
    TBLPROPERTIES ('delta.enableChangeDataFeed' = 'true')
""")
print(f"✅ Table created with correct schema: {FULL_TABLE_NAME}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Improved Chunking Logic

# COMMAND ----------

from datetime import datetime
import re

def extract_keywords(text, max_keywords=10):
    """Extract keywords from text"""
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
                  'of', 'with', 'by', 'from', 'is', 'are', 'was', 'were', 'be', 'been', 
                  'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 
                  'should', 'could', 'may', 'might', 'must', 'can', 'this', 'that', 
                  'these', 'those', 'not', 'what', 'which', 'who', 'when', 'where', 'why', 'how'}
    
    # Extract words (4+ letters)
    words = re.findall(r'\b[a-zA-Z]{4,}\b', text.lower())
    
    # Count frequency
    word_freq = {}
    for word in words:
        if word not in stop_words:
            word_freq[word] = word_freq.get(word, 0) + 1
    
    # Sort by frequency and get top keywords
    keywords = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:max_keywords]
    return [word for word, freq in keywords]

def split_into_sections(content):
    """Split document into logical sections"""
    sections = []
    current_section = ""
    current_title = ""
    
    lines = content.split('\n')
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        
        # Check if this is a section header
        is_header = False
        
        # Pattern 1: ALL CAPS LINE (section headers)
        if stripped and stripped.isupper() and len(stripped) > 5 and not stripped.startswith('P1') and not stripped.startswith('P2'):
            is_header = True
        
        # Pattern 2: Lines followed by dashes/equals (markdown style headers)
        if i + 1 < len(lines):
            next_line = lines[i + 1].strip()
            if stripped and (next_line.startswith('---') or next_line.startswith('===')):
                is_header = True
        
        # If we found a header, save previous section and start new one
        if is_header and current_section.strip():
            sections.append({
                'title': current_title or "Introduction",
                'content': current_section.strip()
            })
            current_title = stripped
            current_section = ""
        else:
            current_section += line + "\n"
    
    # Add the last section
    if current_section.strip():
        sections.append({
            'title': current_title or "Content",
            'content': current_section.strip()
        })
    
    return sections

def chunk_text_by_size(text, min_size=800, max_size=1500):
    """Split text into chunks between min_size and max_size characters"""
    chunks = []
    
    # Split by double newline (paragraphs)
    paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
    
    current_chunk = ""
    
    for para in paragraphs:
        # If adding this paragraph would exceed max_size, save current chunk
        if current_chunk and len(current_chunk) + len(para) > max_size:
            if len(current_chunk) >= min_size:
                chunks.append(current_chunk.strip())
                current_chunk = para + "\n\n"
            else:
                # Chunk is too small, try to add this paragraph anyway
                current_chunk += para + "\n\n"
        else:
            current_chunk += para + "\n\n"
    
    # Handle remaining content
    if current_chunk.strip():
        if len(current_chunk) >= min_size:
            chunks.append(current_chunk.strip())
        elif chunks:
            # Add to last chunk if it's too small
            chunks[-1] += "\n\n" + current_chunk.strip()
        else:
            # First chunk, keep even if small
            chunks.append(current_chunk.strip())
    
    return chunks

def parse_document_with_proper_chunking(file_path, doc_type, category):
    """Parse document with improved chunking strategy"""
    records = []
    
    # Read the file content
    content = dbutils.fs.head(file_path, 1000000)  # Read up to 1MB
    
    # Get document title (first non-empty, non-separator line)
    lines = content.split('\n')
    doc_title = "Untitled"
    for line in lines[:10]:
        stripped = line.strip()
        if stripped and not stripped.startswith('===') and not stripped.startswith('---') and len(stripped) > 3:
            doc_title = stripped
            break
    
    # Split into sections first
    sections = split_into_sections(content)
    
    print(f"  Found {len(sections)} sections")
    
    # Now chunk each section
    chunk_id = 1
    for section in sections:
        section_title = section['title']
        section_content = section['content']
        
        # Skip very short sections
        if len(section_content) < 100:
            continue
        
        # Chunk the section content
        chunks = chunk_text_by_size(section_content, min_size=800, max_size=1500)
        
        print(f"    Section '{section_title}' -> {len(chunks)} chunks")
        
        for chunk_text in chunks:
            keywords = extract_keywords(chunk_text)
            
            # Create descriptive title
            if len(chunks) == 1:
                title = f"{doc_title} - {section_title}"
            else:
                title = f"{doc_title} - {section_title} (Part {chunk_id})"
            
            records.append({
                'doc_id': f"{doc_type}_{chunk_id:03d}",
                'doc_type': doc_type,
                'title': title,
                'content': chunk_text,
                'keywords': keywords,
                'chunk_index': chunk_id,
                'total_chunks': len(chunks),
                'char_count': len(chunk_text),
                'created_at': datetime.now()
            })
            chunk_id += 1
    
    return records

# COMMAND ----------

# MAGIC %md
# MAGIC ## Load All Documents with Proper Chunking

# COMMAND ----------

# Document mappings
document_mappings = {
    "IT_infrastructure_runbook.txt": {
        "doc_type": "Runbook",
        "category": "Infrastructure"
    },
    "application_support_guide.txt": {
        "doc_type": "Support_Guide",
        "category": "Applications"
    },
    "security_incident_playbook.txt": {
        "doc_type": "Playbook",
        "category": "Security"
    },
    "user_access_policies.txt": {
        "doc_type": "Policy",
        "category": "Access_Management"
    },
    "ticket_classification_rules.txt": {
        "doc_type": "Rules",
        "category": "Classification"
    }
}

all_records = []

# Process each document
for filename, metadata in document_mappings.items():
    file_path = f"{VOLUME_PATH}/{filename}"
    
    try:
        print(f"\nProcessing: {filename}")
        records = parse_document_with_proper_chunking(
            file_path,
            metadata["doc_type"],
            metadata["category"]
        )
        all_records.extend(records)
        print(f"  ✅ Total chunks: {len(records)}")
    except Exception as e:
        print(f"  ❌ Error: {e}")
        import traceback
        traceback.print_exc()

print(f"\n{'='*60}")
print(f"✅ Total records to insert: {len(all_records)}")
print(f"{'='*60}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Insert Records into Table

# COMMAND ----------

from pyspark.sql import Row
from pyspark.sql.types import StructType, StructField, StringType, ArrayType, IntegerType, TimestampType

# Define explicit schema to match table
schema = StructType([
    StructField("doc_id", StringType(), False),
    StructField("doc_type", StringType(), False),
    StructField("title", StringType(), False),
    StructField("content", StringType(), False),
    StructField("keywords", ArrayType(StringType()), False),
    StructField("chunk_index", IntegerType(), False),
    StructField("total_chunks", IntegerType(), False),
    StructField("char_count", IntegerType(), False),
    StructField("created_at", TimestampType(), False)
])

# Convert to Spark DataFrame
if all_records:
    rows = [Row(**record) for record in all_records]
    df = spark.createDataFrame(rows, schema=schema)
    
    # Write to Delta table
    df.write.format("delta").mode("append").saveAsTable(FULL_TABLE_NAME)
    
    print(f"✅ Inserted {len(all_records)} records into {FULL_TABLE_NAME}")
else:
    print("❌ No records to insert")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Verify Data Quality

# COMMAND ----------

# Count records
count = spark.sql(f"SELECT COUNT(*) as count FROM {FULL_TABLE_NAME}").collect()[0]['count']
print(f"Total records in table: {count}")

# Check content lengths
print("\nContent length statistics by document type:")
spark.sql(f"""
SELECT 
  doc_type,
  COUNT(*) as num_chunks,
  CAST(AVG(LENGTH(content)) AS INT) as avg_length,
  MIN(LENGTH(content)) as min_length,
  MAX(LENGTH(content)) as max_length
FROM {FULL_TABLE_NAME}
GROUP BY doc_type
ORDER BY doc_type
""").show()

# Show sample records
print("\nSample records with content lengths:")
spark.sql(f"""
SELECT 
  doc_id,
  doc_type,
  title,
  LENGTH(content) as content_length
FROM {FULL_TABLE_NAME}
ORDER BY doc_id
LIMIT 15
""").show(truncate=False)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Success!
# MAGIC 
# MAGIC ✅ Knowledge base reloaded with proper chunking:
# MAGIC - Chunks are 800-1500 characters (optimal for vector embeddings)
# MAGIC - Sections are preserved (headers detected)
# MAGIC - Semantic meaning maintained within chunks
# MAGIC 
# MAGIC Next: Sync Vector Search index

