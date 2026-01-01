#!/usr/bin/env python3
"""
Automated Retrospective Merger (The Flywheel Engine)

Merges structured insights (JSON) into existing SKILL.md files.
Enforces governance by auto-bumping versions and updating verification dates.

Usage:
    cat insights.json | python scripts/auto_retro.py
    python scripts/auto_retro.py --input insights.json

JSON Schema:
    {
      "target_skill": ".claude/skills/skill-name/SKILL.md",
      "negative_knowledge": [
        {
          "attempt": "Description of what was tried",
          "failure": "What went wrong",
          "cost": "Impact (tokens/time)",
          "fix": "Correct approach"
        }
      ]
    }

Design Principles:
- Uses the hardened yaml_parser for robust frontmatter parsing
- Surgically appends to Negative Knowledge table without disrupting structure
- Auto-governs metadata (version bump, last_verified update)
- Atomic operations (fail fast on errors)
"""

import argparse
import json
import sys
import re
from pathlib import Path
from datetime import date
from typing import Dict, List, Tuple, Optional, Any

# Import the hardened parser
sys.path.insert(0, str(Path(__file__).parent))
from yaml_parser import extract_frontmatter


def parse_semver(version: str) -> List[int]:
    """Parse semver string into [major, minor, patch]."""
    try:
        # Handle both "v1.2.3" and "1.2.3" formats
        clean = version.lstrip('v').split('.')
        return [int(x) for x in clean[:3]]
    except (ValueError, IndexError):
        # Default to 1.0.0 if parsing fails
        return [1, 0, 0]


def bump_version(version: str, bump_type: str = 'patch') -> str:
    """Bump semantic version.

    Args:
        version: Current version string (e.g., "1.2.3" or "v1.2.3")
        bump_type: Type of bump ('major', 'minor', 'patch')

    Returns:
        New version string (without 'v' prefix)
    """
    major, minor, patch = parse_semver(version)

    if bump_type == 'major':
        major += 1
        minor = 0
        patch = 0
    elif bump_type == 'minor':
        minor += 1
        patch = 0
    else:  # patch
        patch += 1

    return f"{major}.{minor}.{patch}"


def dump_yaml_frontmatter(metadata: Dict[str, Any]) -> str:
    """Convert metadata dict to YAML frontmatter string.

    This is a simple YAML dumper for the subset we use in skills.
    Handles: strings, numbers, booleans, lists, nested dicts.
    """
    lines = ['---']

    for key, value in metadata.items():
        lines.append(dump_yaml_value(key, value, indent=0))

    lines.append('---')
    return '\n'.join(lines)


def dump_yaml_value(key: str, value: Any, indent: int = 0) -> str:
    """Dump a single YAML key-value pair with proper indentation."""
    prefix = '  ' * indent

    if value is None or value == '':
        return f"{prefix}{key}: \"\""

    elif isinstance(value, bool):
        return f"{prefix}{key}: {str(value).lower()}"

    elif isinstance(value, (int, float)):
        return f"{prefix}{key}: {value}"

    elif isinstance(value, list):
        if not value:
            return f"{prefix}{key}: []"
        # Inline array for simple values
        if all(isinstance(x, str) and '\n' not in x for x in value):
            items = ', '.join(f'"{x}"' if ' ' in x or ':' in x else x for x in value)
            return f"{prefix}{key}: [{items}]"
        # Multiline array for complex values
        lines = [f"{prefix}{key}:"]
        for item in value:
            if isinstance(item, dict):
                lines.append(f"{prefix}  -")
                for k, v in item.items():
                    lines.append(dump_yaml_value(k, v, indent=indent+2))
            else:
                lines.append(f"{prefix}  - {item}")
        return '\n'.join(lines)

    elif isinstance(value, dict):
        # Nested object
        lines = [f"{prefix}{key}:"]
        for k, v in value.items():
            lines.append(dump_yaml_value(k, v, indent=indent+1))
        return '\n'.join(lines)

    else:  # String
        value_str = str(value)
        # Quote strings with special characters
        if any(char in value_str for char in [':', '#', '[', ']', '{', '}']) or \
           value_str.strip() != value_str:
            # Escape quotes in the string
            escaped = value_str.replace('"', '\\"')
            return f"{prefix}{key}: \"{escaped}\""
        else:
            return f"{prefix}{key}: {value_str}"


def locate_negative_knowledge_table(body: str) -> Tuple[Optional[int], Optional[int]]:
    """Find the insertion point for the Negative Knowledge table.

    Returns:
        Tuple of (insert_line_index, end_line_index)
        insert_line_index: Where to insert new rows (after table header)
        end_line_index: Last line of table (for future use)
    """
    lines = body.split('\n')

    # Search for "Negative Knowledge" or "Failed Attempts" section
    for i, line in enumerate(lines):
        if 'negative knowledge' in line.lower() or 'failed attempts' in line.lower():
            # Look ahead for markdown table separator (|---|---|)
            for j in range(i, min(i + 10, len(lines))):
                if re.match(r'^\s*\|[\s\-:|]+\|', lines[j]):
                    # Found table separator - insert after this line
                    return j + 1, None

    # Table not found
    return None, None


def format_table_row(entry: Dict[str, str]) -> str:
    """Format a failure entry as a markdown table row.

    Args:
        entry: Dict with keys: attempt, failure, cost, fix

    Returns:
        Formatted markdown table row
    """
    # Escape pipe characters in cell content
    attempt = entry.get('attempt', 'N/A').replace('|', '\\|')
    failure = entry.get('failure', 'Unknown Error').replace('|', '\\|')
    cost = entry.get('cost', 'Unknown').replace('|', '\\|')
    fix = entry.get('fix', 'See detailed analysis').replace('|', '\\|')

    return f"| {attempt} | {failure} | {cost} | {fix} |"


def create_negative_knowledge_section(entries: List[Dict[str, str]]) -> str:
    """Create a complete Negative Knowledge section from scratch."""
    lines = [
        "",
        "## Negative Knowledge (Auto-Generated)",
        "",
        "| Attempt | Failure | Cost | Correction |",
        "|---------|---------|------|------------|"
    ]

    for entry in entries:
        lines.append(format_table_row(entry))

    lines.append("")
    return '\n'.join(lines)


def merge_retrospective(retro_data: Dict) -> bool:
    """Merge retrospective data into target skill.

    Args:
        retro_data: JSON structure with target_skill and negative_knowledge

    Returns:
        True on success, False on failure
    """
    # Validate input
    skill_path = Path(retro_data.get('target_skill', ''))
    if not skill_path.exists():
        print(f"❌ Skill not found: {skill_path}", file=sys.stderr)
        return False

    # Read current file
    with open(skill_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Parse using hardened parser
    try:
        metadata, body = extract_frontmatter(content)
    except Exception as e:
        print(f"❌ Failed to parse frontmatter: {e}", file=sys.stderr)
        return False

    if not metadata:
        print(f"❌ No frontmatter found in {skill_path}", file=sys.stderr)
        return False

    # Step 1: Update Metadata (Governance)
    current_ver = str(metadata.get('version', '1.0.0'))
    bump_type = retro_data.get('version_bump', 'patch')
    new_ver = bump_version(current_ver, bump_type)

    metadata['version'] = new_ver
    metadata['last_verified'] = date.today().isoformat()

    print(f"📈 Version: {current_ver} → {new_ver}")
    print(f"📅 Last verified: {metadata['last_verified']}")

    # Step 2: Inject Negative Knowledge
    new_knowledge = retro_data.get('negative_knowledge', [])

    if new_knowledge:
        insert_idx, _ = locate_negative_knowledge_table(body)

        if insert_idx is not None:
            # Table exists - insert new rows
            body_lines = body.split('\n')

            # Insert in reverse order to maintain indices
            for entry in reversed(new_knowledge):
                row = format_table_row(entry)
                body_lines.insert(insert_idx, row)

            body = '\n'.join(body_lines)
            print(f"✅ Added {len(new_knowledge)} failure mode(s) to existing table")
        else:
            # Table doesn't exist - append new section
            new_section = create_negative_knowledge_section(new_knowledge)
            body += new_section
            print(f"✅ Created Negative Knowledge section with {len(new_knowledge)} entry(ies)")

    # Step 3: Reconstruct File
    new_frontmatter = dump_yaml_frontmatter(metadata)
    new_content = new_frontmatter + '\n' + body

    # Step 4: Write atomically (backup first)
    backup_path = skill_path.with_suffix('.md.bak')
    skill_path.rename(backup_path)

    try:
        with open(skill_path, 'w', encoding='utf-8') as f:
            f.write(new_content)

        # Remove backup on success
        backup_path.unlink()
        print(f"💾 Saved updates to {skill_path}")
        return True

    except Exception as e:
        # Restore backup on failure
        backup_path.rename(skill_path)
        print(f"❌ Write failed, restored backup: {e}", file=sys.stderr)
        return False


def main():
    """Entry point for CLI usage."""
    parser = argparse.ArgumentParser(
        description='Automated Retrospective Merger - The Flywheel Engine',
        epilog='Example: python scripts/auto_retro.py --input insights.json'
    )
    parser.add_argument(
        '--input',
        help='JSON file containing retrospective insights'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview changes without writing to disk'
    )

    args = parser.parse_args()

    # Read JSON input
    try:
        if args.input:
            with open(args.input, 'r', encoding='utf-8') as f:
                data = json.load(f)
        else:
            # Read from stdin
            if sys.stdin.isatty():
                parser.print_help()
                print("\n❌ Error: No input provided. Use --input or pipe JSON to stdin.",
                      file=sys.stderr)
                sys.exit(1)
            data = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON: {e}", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError:
        print(f"❌ Input file not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    # Validate JSON schema
    if 'target_skill' not in data:
        print("❌ JSON missing required field: 'target_skill'", file=sys.stderr)
        sys.exit(1)

    if args.dry_run:
        print("🔍 DRY RUN - No changes will be written")
        print(f"Target: {data.get('target_skill')}")
        print(f"Entries: {len(data.get('negative_knowledge', []))}")
        sys.exit(0)

    # Execute merge
    success = merge_retrospective(data)
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
