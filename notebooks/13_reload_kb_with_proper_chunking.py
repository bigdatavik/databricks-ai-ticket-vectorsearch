# Databricks notebook source
# MAGIC %md
# MAGIC # Reload Knowledge Base with Proper Chunking

# COMMAND ----------

# Configuration
try:
    CATALOG = dbutils.widgets.get("catalog")
    MODE = dbutils.widgets.get("mode")
except:
    CATALOG = "classify_tickets_new_dev"  # Default for manual runs
    MODE = "incremental"  # Default to incremental for safety

SCHEMA = "support_ai"
TABLE_NAME = "knowledge_base"
VOLUME = "knowledge_docs"

# Full paths
FULL_TABLE_NAME = f"{CATALOG}.{SCHEMA}.{TABLE_NAME}"
VOLUME_PATH = f"/Volumes/{CATALOG}/{SCHEMA}/{VOLUME}"

print(f"Table: {FULL_TABLE_NAME}")
print(f"Volume: {VOLUME_PATH}")
print(f"Mode: {MODE.upper()}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Create Table (Mode-Aware)
# MAGIC 
# MAGIC - **FULL mode**: Drops and recreates table (clean slate)
# MAGIC - **INCREMENTAL mode**: Creates table if not exists (preserves existing data)

# COMMAND ----------

# Check mode and handle accordingly
if MODE.lower() == "full":
    # FULL mode: Drop and recreate for clean slate
    print(f"🔄 FULL MODE: Dropping and recreating table for clean slate")
    try:
        spark.sql(f"DROP TABLE IF EXISTS {FULL_TABLE_NAME}")
        print(f"✅ Dropped existing table: {FULL_TABLE_NAME}")
    except Exception as e:
        print(f"ℹ️  No existing table to drop: {e}")
    
    # Create fresh table
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
    print(f"✅ Table created: {FULL_TABLE_NAME}")
    table_exists = False
    existing_count = 0
else:
    # INCREMENTAL mode: Create if not exists (preserves existing data)
    print(f"⚡ INCREMENTAL MODE: Preserving existing table data")
    spark.sql(f"""
        CREATE TABLE IF NOT EXISTS {FULL_TABLE_NAME} (
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
    
    # Check if table exists and has data
    table_exists = spark.catalog.tableExists(FULL_TABLE_NAME)
    existing_count = 0
    if table_exists:
        existing_count = spark.sql(f"SELECT COUNT(*) as count FROM {FULL_TABLE_NAME}").collect()[0]['count']
        print(f"✅ Table exists: {FULL_TABLE_NAME}")
        print(f"   Existing records: {existing_count}")
        
        # Show existing doc_types
        existing_doc_types = spark.sql(f"""
            SELECT DISTINCT doc_type 
            FROM {FULL_TABLE_NAME} 
            ORDER BY doc_type
        """).collect()
        if existing_doc_types:
            print(f"   Existing document types: {[row['doc_type'] for row in existing_doc_types]}")
    else:
        print(f"✅ Table created: {FULL_TABLE_NAME}")

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

def parse_document_with_proper_chunking(file_path, doc_type, category, filename):
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
    
    # Create a unique file identifier from filename (remove .txt extension)
    file_id = filename.replace('.txt', '').replace(' ', '_').upper()
    
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
            
            # Use file_id in doc_id to make it unique per file
            records.append({
                'doc_id': f"{doc_type}_{file_id}_{chunk_id:03d}",
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

# Dynamically discover files from volume and infer metadata
print("📁 Discovering files in volume...")
volume_files = []
try:
    files = dbutils.fs.ls(VOLUME_PATH)
    for f in files:
        if f.name.endswith('.txt'):
            volume_files.append(f.name)
    print(f"✅ Found {len(volume_files)} .txt files in volume")
except Exception as e:
    print(f"⚠️  Error listing volume files: {e}")
    volume_files = []

# Helper function to infer doc_type and category from filename
def infer_metadata(filename):
    """Infer doc_type and category from filename patterns"""
    filename_lower = filename.lower()
    
    # Infer doc_type from filename patterns
    if 'runbook' in filename_lower:
        doc_type = "Runbook"
    elif 'playbook' in filename_lower:
        doc_type = "Playbook"
    elif 'policy' in filename_lower or 'policies' in filename_lower:
        doc_type = "Policy"
    elif 'rules' in filename_lower or 'classification' in filename_lower:
        doc_type = "Rules"
    elif 'guide' in filename_lower or 'troubleshooting' in filename_lower:
        doc_type = "Guide"
    elif 'support' in filename_lower:
        doc_type = "Support_Guide"
    else:
        doc_type = "Guide"  # Default
    
    # Infer category from filename patterns
    if 'infrastructure' in filename_lower or 'server' in filename_lower:
        category = "Infrastructure"
    elif 'application' in filename_lower or 'app' in filename_lower:
        category = "Applications"
    elif 'security' in filename_lower:
        category = "Security"
    elif 'access' in filename_lower or 'user' in filename_lower or 'identity' in filename_lower:
        category = "Access_Management"
    elif 'classification' in filename_lower or 'ticket' in filename_lower:
        category = "Classification"
    elif 'cloud' in filename_lower or 'aws' in filename_lower or 'azure' in filename_lower or 'ec2' in filename_lower:
        category = "Cloud_Resources"
    elif 'email' in filename_lower or 'mail' in filename_lower:
        category = "Email_Systems"
    elif 'database' in filename_lower or 'db' in filename_lower or 'sql' in filename_lower:
        category = "Database_Administration"
    elif 'network' in filename_lower or 'vpn' in filename_lower or 'dns' in filename_lower:
        category = "Network_Troubleshooting"
    else:
        category = "General"  # Default
    
    return {"doc_type": doc_type, "category": category}

# Build document_mappings dynamically from discovered files
document_mappings = {}
for filename in volume_files:
    metadata = infer_metadata(filename)
    document_mappings[filename] = metadata
    print(f"  📄 {filename} → {metadata['doc_type']} / {metadata['category']}")

print(f"\n✅ Discovered {len(document_mappings)} documents")

# Check which files already exist in the table
existing_files = set()
if table_exists and existing_count > 0:
    # Get list of files that have already been processed
    # Check for new format first (doc_type_FILENAME_NNN), then fall back to old format check
    for filename, metadata in document_mappings.items():
        doc_type = metadata["doc_type"]
        # Create file_id pattern from filename (new format)
        file_id = filename.replace('.txt', '').replace(' ', '_').upper()
        new_format_pattern = f"{doc_type}_{file_id}_%"
        
        # Check for new format first
        existing_docs_new = spark.sql(f"""
            SELECT COUNT(*) as count 
            FROM {FULL_TABLE_NAME} 
            WHERE doc_id LIKE '{new_format_pattern}'
        """).collect()[0]['count']
        
        # If not found in new format, check old format (doc_type_NNN - exactly 3 digits)
        existing_docs_old = 0
        if existing_docs_new == 0:
            existing_docs_old = spark.sql(f"""
                SELECT COUNT(*) as count 
                FROM {FULL_TABLE_NAME} 
                WHERE doc_id RLIKE '^{doc_type}_[0-9]{{3}}$'
            """).collect()[0]['count']
        
        total_existing = existing_docs_new + existing_docs_old
        
        if total_existing > 0:
            existing_files.add(filename)
            format_type = "new format" if existing_docs_new > 0 else "old format"
            print(f"  ℹ️  {filename} already processed ({total_existing} chunks, {format_type})")

print(f"\n{'='*60}")
print(f"Files to process: {len(document_mappings) - len(existing_files)} new")
print(f"Files already processed: {len(existing_files)}")
print(f"{'='*60}\n")

all_records = []

# Process each document (only new ones)
for filename, metadata in document_mappings.items():
    file_path = f"{VOLUME_PATH}/{filename}"
    
    # Skip if already processed
    if filename in existing_files:
        print(f"⏭️  Skipping {filename} (already in table)")
        continue
    
    # Check if file exists in volume
    try:
        file_exists = False
        volume_files = dbutils.fs.ls(VOLUME_PATH)
        for f in volume_files:
            if f.name == filename:
                file_exists = True
                break
        
        if not file_exists:
            print(f"⚠️  {filename} not found in volume, skipping")
            continue
            
    except Exception as e:
        print(f"⚠️  Could not check volume for {filename}: {e}")
        continue
    
    try:
        print(f"\n📄 Processing NEW file: {filename}")
        records = parse_document_with_proper_chunking(
            file_path,
            metadata["doc_type"],
            metadata["category"],
            filename  # Pass filename for unique doc_id generation
        )
        all_records.extend(records)
        print(f"  ✅ Total chunks: {len(records)}")
    except Exception as e:
        print(f"  ❌ Error processing {filename}: {e}")
        import traceback
        traceback.print_exc()

print(f"\n{'='*60}")
print(f"✅ Total NEW records to insert: {len(all_records)}")
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

# Convert to Spark DataFrame and insert only new records
if all_records:
    rows = [Row(**record) for record in all_records]
    df = spark.createDataFrame(rows, schema=schema)
    
    # Ensure Change Data Feed is enabled BEFORE merge (critical for Vector Search sync)
    if table_exists:
        print("📋 Ensuring Change Data Feed is enabled...")
        try:
            spark.sql(f"""
                ALTER TABLE {FULL_TABLE_NAME} 
                SET TBLPROPERTIES (delta.enableChangeDataFeed = true)
            """)
            print(f"   ✅ Change Data Feed enabled")
        except Exception as e:
            print(f"   ℹ️  Change Data Feed status: {e}")
    
    # Use MERGE to handle duplicates (if doc_id already exists, update; otherwise insert)
    # This handles the case where a file was updated
    from delta.tables import DeltaTable
    
    if table_exists:
        delta_table = DeltaTable.forName(spark, FULL_TABLE_NAME)
        
        print(f"📝 Merging {len(all_records)} records...")
        # Merge: if doc_id exists, update; otherwise insert
        delta_table.alias("target").merge(
            df.alias("source"),
            "target.doc_id = source.doc_id"
        ).whenMatchedUpdateAll().whenNotMatchedInsertAll().execute()
        
        print(f"✅ Merged {len(all_records)} records into {FULL_TABLE_NAME} (updated existing, inserted new)")
        
        # Verify merge completed and get commit info
        print("📊 Verifying merge completed...")
        import time
        time.sleep(2)  # Small delay to ensure transaction commits
        
        # Check Delta table history to confirm merge
        history = spark.sql(f"DESCRIBE HISTORY {FULL_TABLE_NAME} LIMIT 1").collect()
        if history:
            latest_commit = history[0]
            # PySpark Row objects don't have .get() method - access fields directly using bracket notation
            try:
                operation = latest_commit['operation']
                version = latest_commit['version']
            except (KeyError, AttributeError):
                # Fallback: try attribute access
                operation = getattr(latest_commit, 'operation', 'Unknown')
                version = getattr(latest_commit, 'version', 'Unknown')
            print(f"   Latest operation: {operation}")
            print(f"   Latest commit: {version}")
        
    else:
        # First time - just insert
        df.write.format("delta").mode("append").saveAsTable(FULL_TABLE_NAME)
        print(f"✅ Inserted {len(all_records)} records into {FULL_TABLE_NAME}")
else:
    print("✅ No new records to insert - all files already processed")

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
# MAGIC ✅ Knowledge base updated with proper chunking:
# MAGIC - **Incremental mode**: Only processes NEW files from volume
# MAGIC - Preserves existing documents (no table drop/recreate)
# MAGIC - Chunks are 800-1500 characters (optimal for vector embeddings)
# MAGIC - Sections are preserved (headers detected)
# MAGIC - Semantic meaning maintained within chunks
# MAGIC 
# MAGIC **Next:** Vector Search index will sync incrementally (only new records)

