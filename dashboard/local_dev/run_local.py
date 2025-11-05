#!/usr/bin/env python3
"""
Local development runner for Streamlit dashboard.
Sets environment variables and runs app_simple.py.
"""

import os
import sys
import subprocess

# Set environment variable for Databricks config profile
os.environ['DATABRICKS_CONFIG_PROFILE'] = 'DEFAULT_azure'

print("🚀 Starting AI Ticket Classification Dashboard (Local Development)")
print(f"📝 Using config profile: {os.environ['DATABRICKS_CONFIG_PROFILE']}")
print(f"🔧 Config file: ~/.databrickscfg")
print()

# Run streamlit
subprocess.run([
    sys.executable, "-m", "streamlit", "run",
    "app_simple.py",
    "--server.port=8501",
    "--server.enableXsrfProtection=false"
])

