#!/bin/bash
# Schedule the Obsidian Organization Agent to run periodically via Oz

# Configuration - update these values
ENVIRONMENT_ID="${OZ_ENVIRONMENT_ID:-}"
CRON_SCHEDULE="${CRON_SCHEDULE:-0 */6 * * *}"  # Default: every 6 hours

# Agent prompt for the Oz cloud agent
AGENT_PROMPT='You are an Obsidian vault organization agent. Your task is to organize notes without rewriting or deleting content.

Run the organization script:
```bash
cd /workspace/Obsidian_Notebook
python3 _agent/organize.py
```

After running, commit any changes to the _meta folder and note frontmatter updates:
```bash
git add -A
git commit -m "chore: auto-organize vault

- Updated note tags and themes
- Generated link suggestions  
- Updated insights and patterns

Co-Authored-By: Warp <agent@warp.dev>" || echo "No changes to commit"
git push || echo "Push skipped"
```

Report what was organized and any insights discovered.'

if [ -z "$ENVIRONMENT_ID" ]; then
    echo "Error: OZ_ENVIRONMENT_ID environment variable not set"
    echo ""
    echo "To schedule this agent:"
    echo "1. Create an Oz environment with your vault repository"
    echo "2. Export OZ_ENVIRONMENT_ID=<your-environment-id>"
    echo "3. Run this script again"
    echo ""
    echo "Or run manually:"
    echo "  oz-preview agent run-cloud --prompt \"$AGENT_PROMPT\" --environment <ENV_ID>"
    exit 1
fi

echo "Scheduling Obsidian Organization Agent..."
echo "Environment: $ENVIRONMENT_ID"
echo "Schedule: $CRON_SCHEDULE"
echo ""

# Create the scheduled task
oz-preview schedule create \
    --cron "$CRON_SCHEDULE" \
    --prompt "$AGENT_PROMPT" \
    --environment "$ENVIRONMENT_ID" \
    --output-format text

echo ""
echo "Agent scheduled! Use 'oz-preview schedule list' to view scheduled tasks."
