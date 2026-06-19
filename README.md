---
oz_tags: [ideas, references, personal, projects, research, learning, creative, intent:note]
oz_created: 2026-02-10
oz_updated: 2026-06-19
---
# Obsidian Vault with AI Organization Agent

This Obsidian vault includes an AI-powered background agent that automatically organizes your notes.

## What the Agent Does

The organization agent runs periodically and performs these tasks **without modifying your note content**:

### 1. **Tag Notes by Theme**
Analyzes note content and adds `oz_tags` to frontmatter:
- Ideas, drafts, references, personal reflections
- Projects, research, learning, meetings, creative writing
- Intent detection (questions, actions, definitions, comparisons)

### 2. **Detect Related Notes**
Finds notes with similar content and generates link suggestions in `_meta/Link Suggestions.md`.

### 3. **Group by Themes**
Creates a theme index at `_meta/Theme Index.md` showing all notes organized by topic.

### 4. **Generate Summaries**
Produces brief context summaries for each note, stored in `_meta/note_summaries.json`.

### 5. **Surface Patterns**
Identifies recurring concepts and emerging themes, with actionable insights in `_meta/Insights.md`.

## Folder Structure

```
Obsidian_Notebook/
├── notes/              # Your notes go here
├── _agent/             # Agent scripts and config
│   ├── organize.py     # Main organization script
│   ├── config.json     # Customizable settings
│   └── schedule_agent.sh
├── _meta/              # Agent-generated metadata
│   ├── Theme Index.md
│   ├── Link Suggestions.md
│   ├── Insights.md
│   └── agent_state.json
└── .obsidian/          # Obsidian configuration
```

## Running the Agent

### Manually (Local)

```bash
python3 _agent/organize.py
```

### Scan Only (No Changes)

```bash
python3 _agent/organize.py --scan-only
```

### Schedule via Oz (Recommended)

1. Create an Oz environment with this repository
2. Set your environment ID:
   ```bash
   export OZ_ENVIRONMENT_ID=<your-environment-id>
   ```
3. Schedule the agent:
   ```bash
   bash _agent/schedule_agent.sh
   ```

The agent will run every 6 hours by default. Customize with:
```bash
CRON_SCHEDULE="0 */2 * * *" bash _agent/schedule_agent.sh  # Every 2 hours
```

### One-Time Cloud Run

```bash
oz-preview agent run-cloud \
  --prompt "Run python3 _agent/organize.py and report insights" \
  --environment <ENV_ID>
```

## Configuration

Edit `_agent/config.json` to customize:

```json
{
  "themes": {
    "ideas": ["idea", "concept", "brainstorm", ...],
    "custom_theme": ["keyword1", "keyword2", ...]
  },
  "min_similarity_threshold": 0.25,
  "auto_link": true,
  "generate_summaries": true,
  "track_patterns": true
}
```

## What Gets Modified

The agent **only** modifies:
- Note frontmatter (adds `oz_tags`, `oz_created`, `oz_updated`)
- Files in `_meta/` folder

The agent **never**:
- Rewrites note content
- Deletes notes or content
- Modifies your existing tags or frontmatter fields

## Viewing Agent Output

After running, check these files in Obsidian:
- `_meta/Theme Index.md` - Notes organized by theme
- `_meta/Link Suggestions.md` - Suggested connections
- `_meta/Insights.md` - Patterns and next steps

## Troubleshooting

**Agent not detecting themes correctly?**
- Add custom keywords to `config.json`
- Ensure notes have enough content for classification

**Too many/few link suggestions?**
- Adjust `min_similarity_threshold` (0.0-1.0)
- Lower = more suggestions, higher = stricter matching

**Want to reset agent state?**
```bash
rm _meta/agent_state.json
```

## Summary

This note serves as the documentation hub for the Obsidian vault, explaining how the AI-powered organization agent works. The author's intent is to provide users with a clear guide on installation, configuration, and usage of the automated note organization system, including folder structure, agent capabilities, and troubleshooting tips.

## Tags

#documentation #obsidian #automation #ai-agent #knowledge-management #organization #vault-setup

## Related Notes

- [[Personal Knowledge Management]] - Core PKM principles that this vault and agent system implement
- [[AI Writing Assistant Idea]] - Context-aware AI concept closely aligned with this agent's approach
- [[Research - Note-Taking Studies]] - Research evidence supporting the automated organization this agent provides
- [[2024-02-10 Morning Reflection]] - Personal motivation behind building this AI-powered organization system
- [[Palantir Products]] - Data integration and analysis platforms that parallel the agent's note organization capabilities
- [[Palantir Origin Story]] - Founding narrative demonstrating the interconnected research this vault organizes
- [[LinkedIn]] - Example of a data aggregation platform discussed in this vault
- [[All Kings]] - Central hub note demonstrating interconnected knowledge networks
- [[Corporate Cabal]] - Explores institutional power networks, exemplifying the connected research this agent helps organize
- [[Flock Camera Investors]] - Surveillance startup investment patterns tracked across vault notes