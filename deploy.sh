#!/bin/bash
# Simple Deployment Script for Databricks Classify Tickets System

set -e  # Exit on error

# Configuration
TARGET="${1:-}"
PROFILE="${2:-DEFAULT_azure}"

# Detect target from databricks.yml if not specified
if [ -z "$TARGET" ]; then
  if grep -q "classify_tickets_new_dev" databricks.yml 2>/dev/null; then
    TARGET="dev"
  elif grep -q "targets:" databricks.yml 2>/dev/null; then
    TARGET="staging"  # default for staging/prod config
  else
    echo "❌ Cannot detect environment. Please specify: dev, staging, or prod"
    exit 1
  fi
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🚀 Deploying: Classify Tickets System"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Target:  $TARGET"
echo "Profile: $PROFILE"
echo "Time:    $(date)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Clean bundle cache
echo "🧹 Cleaning bundle cache..."
rm -rf .databricks/bundle/*
echo ""

# Step 1: Deploy Bundle
echo "📦 Step 1/4: Deploying bundle..."
if [ "$TARGET" == "dev" ]; then
  databricks bundle deploy --profile "$PROFILE"
else
  databricks bundle deploy -t "$TARGET" --profile "$PROFILE"
fi
echo "   ✅ Bundle deployed"
echo ""

# Step 2: Run Infrastructure Setup
echo "🏗️  Step 2/4: Setting up infrastructure..."
if [ "$TARGET" == "dev" ]; then
  databricks bundle run setup_infrastructure --profile "$PROFILE"
else
  databricks bundle run setup_infrastructure -t "$TARGET" --profile "$PROFILE"
fi
echo "   ✅ Infrastructure ready"
echo ""

# Step 3: Deploy App
echo "📱 Step 3/4: Deploying Streamlit app..."
if [ "$TARGET" == "dev" ]; then
  databricks bundle run ticket_classification_dashboard --profile "$PROFILE"
else
  databricks bundle run ticket_classification_dashboard -t "$TARGET" --profile "$PROFILE"
fi
echo "   ✅ App deployed"
echo ""

# Step 4: Grant Permissions (re-run grant task from infrastructure job)
echo "🔐 Step 4/4: Granting app permissions..."
echo "   NOTE: Permissions are granted in the infrastructure job's last task"
echo "   If needed, you can re-run just that task from Databricks UI"
echo "   ✅ Permissions should be set"
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ DEPLOYMENT COMPLETE!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🎯 Next Steps:"
echo "   1. Check app status in Databricks Apps UI"
echo "   2. Test the dashboard"
echo ""

