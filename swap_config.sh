#!/bin/bash
# Simple script to swap between dev and staging/prod configurations

set -e

MODE="${1:-status}"

case "$MODE" in
  dev)
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "🔧 Switching to DEV configuration..."
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    # Backup current config if it's not dev
    if [ -f "databricks.yml" ] && ! grep -q "classify_tickets_new_dev" databricks.yml; then
      echo "📦 Backing up current config to databricks.staging_prod.yml"
      cp databricks.yml databricks.staging_prod.yml
    fi
    
    # Check if we have a dev backup
    if [ -f "databricks.dev.backup.yml" ]; then
      echo "✅ Restoring dev config from backup"
      cp databricks.dev.backup.yml databricks.yml
    elif ! grep -q "classify_tickets_new_dev" databricks.yml; then
      echo "❌ Dev config not found!"
      exit 1
    else
      echo "✅ Already on dev config"
    fi
    
    echo ""
    echo "Active config:"
    echo "  • Cluster: Interactive (0304-162117-qgsi1x04)"
    echo "  • Catalog: classify_tickets_new_dev"
    echo "  • Mode: Full deployment"
    echo ""
    ;;
    
  staging|prod)
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "🏭 Switching to STAGING/PROD configuration..."
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    # Backup current config if it's dev
    if [ -f "databricks.yml" ] && grep -q "classify_tickets_new_dev" databricks.yml; then
      echo "📦 Backing up dev config to databricks.dev.backup.yml"
      cp databricks.yml databricks.dev.backup.yml
    fi
    
    # Switch to staging/prod config
    if [ -f "databricks.staging_prod.yml" ]; then
      echo "✅ Activating staging/prod config"
      cp databricks.staging_prod.yml databricks.yml
    else
      echo "❌ Staging/prod config not found!"
      exit 1
    fi
    
    echo ""
    echo "Active config:"
    echo "  • Cluster: Job cluster (16.4 LTS, autoscale 1-20)"
    echo "  • Catalogs: classify_tickets_new_staging, classify_tickets_new_prod"
    echo "  • Mode: Incremental deployment"
    echo ""
    ;;
    
  status)
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "📊 Current Configuration Status"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    if [ -f "databricks.yml" ]; then
      if grep -q "classify_tickets_new_dev" databricks.yml; then
        echo "✅ Currently on: DEV"
        echo "   • Interactive cluster (0304-162117-qgsi1x04)"
        echo "   • Full deployment mode"
      elif grep -q "targets:" databricks.yml; then
        echo "✅ Currently on: STAGING/PROD"
        echo "   • Job clusters"
        echo "   • Incremental deployment mode"
      else
        echo "⚠️  Unknown configuration"
      fi
    else
      echo "❌ No databricks.yml found!"
    fi
    
    echo ""
    echo "Available commands:"
    echo "  ./swap_config.sh dev           - Switch to dev config"
    echo "  ./swap_config.sh staging       - Switch to staging/prod config"
    echo "  ./swap_config.sh status        - Show current config"
    echo ""
    ;;
    
  *)
    echo "Usage: ./swap_config.sh {dev|staging|prod|status}"
    exit 1
    ;;
esac

