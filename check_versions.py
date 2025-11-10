# Quick Version Check Script
# Run this in your Databricks notebook to see what versions are installed

print("🔍 Checking LangChain/LangGraph versions...\n")
print("=" * 70)

packages_to_check = [
    'langgraph',
    'langchain', 
    'langchain-core',
    'langchain-community',
    'databricks-langchain',
    'unitycatalog-langchain'
]

for package in packages_to_check:
    try:
        # Import the module
        module_name = package.replace('-', '_')
        module = __import__(module_name)
        
        # Get version
        version = getattr(module, '__version__', 'version not available')
        
        print(f"✅ {package:.<30} {version}")
        
    except ImportError as e:
        print(f"❌ {package:.<30} NOT INSTALLED")
    except Exception as e:
        print(f"⚠️  {package:.<30} ERROR: {str(e)}")

print("=" * 70)

