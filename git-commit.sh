#!/bin/bash
# Git cleanup and commit script
# Run this from: ~/databricks-ai-ticket-vectorsearch/

cd ~/databricks-ai-ticket-vectorsearch || exit 1

echo "📋 Step 1: Removing files from Git tracking (keeping local copies)..."
git rm --cached MY_ENVIRONMENT.md MY_ENVIRONMENT_AI_TICKET_LESSONS.md

echo ""
echo "📋 Step 2: Staging all changes..."
git add .

echo ""
echo "📋 Step 3: Checking what will be committed..."
git status

echo ""
echo "📋 Step 4: Committing changes..."
git commit -m "feat: Extract LangGraph patterns to central standards

- Add MY_ENVIRONMENT_AI_TICKET_LESSONS.md to .gitignore
- Remove MY_ENVIRONMENT.md and MY_ENVIRONMENT_AI_TICKET_LESSONS.md from repo
- These files now managed via central ~/.cursor-standards/templates/
- Updated cross-references between files
- Core LangGraph patterns extracted to MY_ENVIRONMENT.md

Files remain locally but won't be tracked in Git."

echo ""
echo "📋 Step 5: Pushing to remote..."
git push

echo ""
echo "✅ Done! Check the output above for any errors."

