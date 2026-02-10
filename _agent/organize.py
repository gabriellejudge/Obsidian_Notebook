#!/usr/bin/env python3
"""
Obsidian Vault Organization Agent

This agent continuously organizes an Obsidian vault by:
- Tagging notes based on themes, topics, and intent
- Detecting and linking related notes
- Grouping notes into higher-level themes
- Generating summaries for context
- Surfacing patterns and recurring ideas

It runs non-destructively: no content is rewritten or deleted.
"""

import os
import re
import json
import hashlib
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from typing import Optional

# Configuration
VAULT_PATH = Path(os.getenv("VAULT_PATH", "/workspace/Obsidian_Notebook"))
META_PATH = VAULT_PATH / "_meta"
CONFIG_PATH = VAULT_PATH / "_agent" / "config.json"
STATE_PATH = META_PATH / "agent_state.json"

# Default theme keywords for classification
DEFAULT_THEMES = {
    "ideas": ["idea", "concept", "thought", "brainstorm", "what if", "could", "might", "explore"],
    "drafts": ["draft", "wip", "work in progress", "rough", "outline", "skeleton"],
    "references": ["reference", "source", "citation", "link", "resource", "article", "paper"],
    "personal": ["journal", "diary", "reflection", "feeling", "today", "personal", "mood"],
    "projects": ["project", "task", "todo", "milestone", "deadline", "sprint", "goal"],
    "research": ["research", "study", "analysis", "findings", "data", "experiment"],
    "learning": ["learn", "note", "lesson", "course", "tutorial", "how to", "guide"],
}

# Intent patterns
INTENT_PATTERNS = {
    "question": [r"\?$", r"^how", r"^what", r"^why", r"^when", r"^where", r"^who"],
    "action": [r"^todo", r"^\[ \]", r"need to", r"should", r"must", r"will"],
    "definition": [r"^##?\s*definition", r"is defined as", r"means that", r":="],
    "comparison": [r"vs\.?", r"versus", r"compared to", r"difference between"],
}


class VaultOrganizer:
    """Main class for organizing an Obsidian vault."""

    def __init__(self, vault_path: Path = VAULT_PATH):
        self.vault_path = vault_path
        self.meta_path = vault_path / "_meta"
        self.meta_path.mkdir(exist_ok=True)
        self.state = self._load_state()
        self.config = self._load_config()
        self.notes_index = {}
        self.theme_groups = defaultdict(list)
        self.link_graph = defaultdict(set)

    def _load_state(self) -> dict:
        """Load previous agent state."""
        if STATE_PATH.exists():
            with open(STATE_PATH) as f:
                return json.load(f)
        return {
            "last_run": None,
            "processed_notes": {},
            "patterns_detected": [],
            "emerging_themes": [],
        }

    def _save_state(self):
        """Save agent state for next run."""
        self.state["last_run"] = datetime.now().isoformat()
        with open(STATE_PATH, "w") as f:
            json.dump(self.state, f, indent=2)

    def _load_config(self) -> dict:
        """Load agent configuration."""
        if CONFIG_PATH.exists():
            with open(CONFIG_PATH) as f:
                return json.load(f)
        return {
            "themes": DEFAULT_THEMES,
            "min_similarity_threshold": 0.3,
            "auto_link": True,
            "generate_summaries": True,
            "track_patterns": True,
        }

    def _get_note_hash(self, content: str) -> str:
        """Generate hash of note content for change detection."""
        return hashlib.md5(content.encode()).hexdigest()

    def _extract_frontmatter(self, content: str) -> tuple[dict, str]:
        """Extract YAML frontmatter from note content."""
        frontmatter = {}
        body = content

        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                try:
                    # Simple YAML parsing for common frontmatter
                    for line in parts[1].strip().split("\n"):
                        if ":" in line:
                            key, value = line.split(":", 1)
                            key = key.strip()
                            value = value.strip()
                            # Handle lists
                            if value.startswith("[") and value.endswith("]"):
                                value = [v.strip().strip('"\'') for v in value[1:-1].split(",")]
                            frontmatter[key] = value
                    body = parts[2].strip()
                except Exception:
                    pass

        return frontmatter, body

    def _build_frontmatter(self, frontmatter: dict) -> str:
        """Build YAML frontmatter string."""
        if not frontmatter:
            return ""

        lines = ["---"]
        for key, value in frontmatter.items():
            if isinstance(value, list):
                lines.append(f"{key}: [{', '.join(value)}]")
            else:
                lines.append(f"{key}: {value}")
        lines.append("---\n")
        return "\n".join(lines)

    def _extract_keywords(self, text: str) -> list[str]:
        """Extract meaningful keywords from text."""
        # Remove markdown syntax
        text = re.sub(r"[#*`\[\](){}]", " ", text.lower())
        # Remove URLs
        text = re.sub(r"https?://\S+", "", text)
        # Extract words
        words = re.findall(r"\b[a-z]{3,}\b", text)
        # Filter common words
        stopwords = {
            "the", "and", "for", "are", "but", "not", "you", "all", "can",
            "had", "her", "was", "one", "our", "out", "has", "have", "been",
            "were", "they", "this", "that", "with", "from", "will", "would",
            "there", "their", "what", "about", "which", "when", "make", "like",
            "just", "over", "such", "into", "than", "them", "some", "could",
        }
        return [w for w in words if w not in stopwords]

    def _classify_theme(self, content: str, keywords: list[str]) -> list[str]:
        """Classify note into themes based on content."""
        themes = []
        content_lower = content.lower()

        for theme, indicators in self.config.get("themes", DEFAULT_THEMES).items():
            score = sum(1 for indicator in indicators if indicator in content_lower)
            keyword_matches = sum(1 for kw in keywords if kw in indicators)
            if score >= 2 or keyword_matches >= 1:
                themes.append(theme)

        return themes or ["general"]

    def _detect_intent(self, content: str) -> list[str]:
        """Detect the intent/purpose of the note."""
        intents = []
        lines = content.split("\n")

        for intent, patterns in INTENT_PATTERNS.items():
            for line in lines[:10]:  # Check first 10 lines
                for pattern in patterns:
                    if re.search(pattern, line.lower()):
                        intents.append(intent)
                        break

        return list(set(intents)) or ["note"]

    def _calculate_similarity(self, keywords1: list[str], keywords2: list[str]) -> float:
        """Calculate Jaccard similarity between keyword sets."""
        if not keywords1 or not keywords2:
            return 0.0
        set1, set2 = set(keywords1), set(keywords2)
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        return intersection / union if union > 0 else 0.0

    def _find_related_notes(self, note_path: str, keywords: list[str]) -> list[tuple[str, float]]:
        """Find notes related to the given note."""
        related = []
        threshold = self.config.get("min_similarity_threshold", 0.3)

        for other_path, other_data in self.notes_index.items():
            if other_path == note_path:
                continue
            similarity = self._calculate_similarity(keywords, other_data.get("keywords", []))
            if similarity >= threshold:
                related.append((other_path, similarity))

        return sorted(related, key=lambda x: -x[1])[:5]

    def _extract_existing_links(self, content: str) -> list[str]:
        """Extract existing wiki-style links from content."""
        return re.findall(r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]", content)

    def _generate_summary(self, content: str, title: str) -> str:
        """Generate a brief summary/context for the note."""
        lines = [l.strip() for l in content.split("\n") if l.strip() and not l.startswith("#")]

        # Get first meaningful paragraph
        first_para = ""
        for line in lines[:5]:
            if len(line) > 20:
                first_para = line
                break

        if first_para:
            # Truncate to ~100 chars
            if len(first_para) > 100:
                first_para = first_para[:97] + "..."
            return first_para

        return f"Note about {title}"

    def scan_vault(self):
        """Scan all notes in the vault."""
        print(f"Scanning vault: {self.vault_path}")

        for md_file in self.vault_path.rglob("*.md"):
            # Skip agent and meta directories
            if "_agent" in str(md_file) or "_meta" in str(md_file):
                continue
            if md_file.name.startswith("_"):
                continue

            rel_path = str(md_file.relative_to(self.vault_path))

            try:
                with open(md_file, encoding="utf-8") as f:
                    content = f.read()

                content_hash = self._get_note_hash(content)
                frontmatter, body = self._extract_frontmatter(content)
                keywords = self._extract_keywords(body)

                self.notes_index[rel_path] = {
                    "path": rel_path,
                    "title": md_file.stem,
                    "hash": content_hash,
                    "frontmatter": frontmatter,
                    "keywords": keywords,
                    "existing_links": self._extract_existing_links(content),
                    "modified": md_file.stat().st_mtime,
                }

            except Exception as e:
                print(f"Error reading {rel_path}: {e}")

        print(f"Found {len(self.notes_index)} notes")

    def analyze_and_tag(self):
        """Analyze notes and add/update tags in frontmatter."""
        print("Analyzing notes for themes and intent...")
        updates = []

        for rel_path, note_data in self.notes_index.items():
            file_path = self.vault_path / rel_path

            with open(file_path, encoding="utf-8") as f:
                content = f.read()

            frontmatter, body = self._extract_frontmatter(content)

            # Skip if already processed and unchanged
            prev_hash = self.state["processed_notes"].get(rel_path, {}).get("hash")
            if prev_hash == note_data["hash"] and "oz_tags" in frontmatter:
                continue

            # Classify
            themes = self._classify_theme(body, note_data["keywords"])
            intents = self._detect_intent(body)

            # Build agent-managed tags
            oz_tags = themes + [f"intent:{i}" for i in intents]

            # Update frontmatter (preserve user tags)
            frontmatter["oz_tags"] = oz_tags
            if "oz_updated" not in frontmatter:
                frontmatter["oz_created"] = datetime.now().strftime("%Y-%m-%d")
            frontmatter["oz_updated"] = datetime.now().strftime("%Y-%m-%d")

            # Rebuild note
            new_frontmatter = self._build_frontmatter(frontmatter)
            new_content = new_frontmatter + body

            with open(file_path, "w", encoding="utf-8") as f:
                f.write(new_content)

            updates.append(rel_path)

            # Update state
            self.state["processed_notes"][rel_path] = {
                "hash": note_data["hash"],
                "themes": themes,
                "intents": intents,
                "processed": datetime.now().isoformat(),
            }

            # Group by theme
            for theme in themes:
                self.theme_groups[theme].append(rel_path)

        print(f"Tagged {len(updates)} notes")
        return updates

    def link_related_notes(self):
        """Create a suggestions file for related note links."""
        if not self.config.get("auto_link", True):
            return

        print("Finding related notes...")
        suggestions = []

        for rel_path, note_data in self.notes_index.items():
            related = self._find_related_notes(rel_path, note_data["keywords"])

            if related:
                existing_links = set(note_data["existing_links"])
                new_suggestions = []

                for related_path, similarity in related:
                    related_title = self.notes_index[related_path]["title"]
                    if related_title not in existing_links:
                        new_suggestions.append({
                            "target": related_path,
                            "title": related_title,
                            "similarity": round(similarity, 2),
                        })

                if new_suggestions:
                    suggestions.append({
                        "note": rel_path,
                        "title": note_data["title"],
                        "suggested_links": new_suggestions,
                    })

        # Write suggestions file
        suggestions_path = self.meta_path / "link_suggestions.json"
        with open(suggestions_path, "w") as f:
            json.dump(suggestions, f, indent=2)

        # Also create a readable markdown version
        md_path = self.meta_path / "Link Suggestions.md"
        with open(md_path, "w") as f:
            f.write("# Suggested Note Links\n\n")
            f.write(f"_Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}_\n\n")
            f.write("These are AI-suggested links based on content similarity.\n\n")

            for item in suggestions:
                f.write(f"## [[{item['title']}]]\n\n")
                for link in item["suggested_links"]:
                    f.write(f"- [[{link['title']}]] (similarity: {link['similarity']})\n")
                f.write("\n")

        print(f"Generated {len(suggestions)} link suggestions")

    def generate_theme_index(self):
        """Generate an index of notes organized by theme."""
        print("Generating theme index...")

        index_path = self.meta_path / "Theme Index.md"
        with open(index_path, "w") as f:
            f.write("# Vault Theme Index\n\n")
            f.write(f"_Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}_\n\n")

            for theme, notes in sorted(self.theme_groups.items()):
                f.write(f"## {theme.title()}\n\n")
                for note_path in notes:
                    title = self.notes_index[note_path]["title"]
                    f.write(f"- [[{title}]]\n")
                f.write("\n")

        print(f"Theme index updated with {len(self.theme_groups)} themes")

    def generate_summaries(self):
        """Generate context summaries for each note."""
        if not self.config.get("generate_summaries", True):
            return

        print("Generating note summaries...")

        summaries = {}
        for rel_path, note_data in self.notes_index.items():
            file_path = self.vault_path / rel_path

            with open(file_path, encoding="utf-8") as f:
                content = f.read()

            _, body = self._extract_frontmatter(content)
            summary = self._generate_summary(body, note_data["title"])

            summaries[rel_path] = {
                "title": note_data["title"],
                "summary": summary,
                "themes": self.state["processed_notes"].get(rel_path, {}).get("themes", []),
                "keywords": note_data["keywords"][:10],
            }

        # Write summaries
        summaries_path = self.meta_path / "note_summaries.json"
        with open(summaries_path, "w") as f:
            json.dump(summaries, f, indent=2)

        print(f"Generated summaries for {len(summaries)} notes")

    def detect_patterns(self):
        """Detect recurring patterns and emerging themes."""
        if not self.config.get("track_patterns", True):
            return

        print("Detecting patterns...")

        # Keyword frequency analysis
        keyword_freq = defaultdict(int)
        for note_data in self.notes_index.values():
            for kw in note_data["keywords"]:
                keyword_freq[kw] += 1

        # Find recurring keywords (appearing in 3+ notes)
        recurring = [(kw, count) for kw, count in keyword_freq.items() if count >= 3]
        recurring.sort(key=lambda x: -x[1])

        # Theme trends
        theme_counts = {theme: len(notes) for theme, notes in self.theme_groups.items()}

        # Build insights report
        insights_path = self.meta_path / "Insights.md"
        with open(insights_path, "w") as f:
            f.write("# Vault Insights\n\n")
            f.write(f"_Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}_\n\n")

            f.write("## Recurring Concepts\n\n")
            f.write("Keywords that appear across multiple notes:\n\n")
            for kw, count in recurring[:20]:
                f.write(f"- **{kw}** ({count} notes)\n")
            f.write("\n")

            f.write("## Theme Distribution\n\n")
            for theme, count in sorted(theme_counts.items(), key=lambda x: -x[1]):
                f.write(f"- {theme.title()}: {count} notes\n")
            f.write("\n")

            f.write("## Suggested Next Steps\n\n")

            # Generate suggestions based on patterns
            if "ideas" in theme_counts and theme_counts["ideas"] > 3:
                f.write("- 💡 You have several ideas brewing. Consider developing one into a draft.\n")

            if "drafts" in theme_counts and theme_counts["drafts"] > 2:
                f.write("- ✏️ Multiple drafts in progress. Review and prioritize which to complete.\n")

            lonely_notes = [p for p, d in self.notes_index.items()
                          if len(d["existing_links"]) == 0]
            if lonely_notes:
                f.write(f"- 🔗 {len(lonely_notes)} notes have no links. Check link suggestions.\n")

            if recurring:
                top_concept = recurring[0][0]
                f.write(f"- 📚 '{top_concept}' appears frequently. Consider creating a hub note.\n")

        # Update state
        self.state["patterns_detected"] = [{"keyword": kw, "count": c} for kw, c in recurring[:10]]
        self.state["emerging_themes"] = list(theme_counts.keys())

        print("Insights generated")

    def run(self):
        """Run the full organization pipeline."""
        print(f"\n{'='*50}")
        print(f"Obsidian Organization Agent")
        print(f"Run started: {datetime.now().isoformat()}")
        print(f"{'='*50}\n")

        try:
            self.scan_vault()
            self.analyze_and_tag()
            self.link_related_notes()
            self.generate_theme_index()
            self.generate_summaries()
            self.detect_patterns()
            self._save_state()

            print(f"\n{'='*50}")
            print("Organization complete!")
            print(f"{'='*50}\n")

        except Exception as e:
            print(f"Error during organization: {e}")
            raise


def main():
    """Entry point for the organization agent."""
    import argparse

    parser = argparse.ArgumentParser(description="Obsidian Vault Organization Agent")
    parser.add_argument("--vault", "-v", type=str, help="Path to Obsidian vault")
    parser.add_argument("--scan-only", action="store_true", help="Only scan, don't modify")
    args = parser.parse_args()

    vault_path = Path(args.vault) if args.vault else VAULT_PATH

    organizer = VaultOrganizer(vault_path)

    if args.scan_only:
        organizer.scan_vault()
        print(f"\nFound {len(organizer.notes_index)} notes")
        for path in organizer.notes_index:
            print(f"  - {path}")
    else:
        organizer.run()


if __name__ == "__main__":
    main()
