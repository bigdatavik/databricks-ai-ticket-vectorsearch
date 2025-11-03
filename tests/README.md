# Test Files

This directory contains test utilities and scripts for the AI-Powered Support Ticket Classification System.

## Files

- **`test_vector_search.py`** - Local Python script to test Vector Search index via API
  - Tests index status, query functionality, and sync triggers
  - Requires `~/.databrickscfg` for authentication

- **`test_vector_search_index.py`** - Databricks notebook for testing Vector Search index
  - Can be run directly in Databricks workspace
  - Tests index creation, sync, and query operations

- **`rebuild_vector_index.py`** - Utility notebook for rebuilding Vector Search index
  - Full rebuild of Vector Search index
  - Useful for troubleshooting or complete re-indexing

## Usage

### Local Testing
```bash
# Requires databricks-sdk installed
pip install databricks-sdk
python tests/test_vector_search.py
```

### Notebook Testing
Import and run the notebooks in Databricks workspace:
- `tests/test_vector_search_index.py` - For index testing
- `tests/rebuild_vector_index.py` - For full rebuild

## Notes

- These are utility/test files and not part of the main deployment pipeline
- Test files are excluded from normal deployment workflows
- Use these for troubleshooting and validation

