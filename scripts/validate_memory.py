#!/usr/bin/env python3
"""
Validate all SKILL.md files in the repository against governance rules.

This script enforces the Learning Flywheel's core principles:
1. Negative Knowledge must be documented
2. Context must be kept within budget
3. Skills must have specific trigger descriptions
4. Format must follow the standard template

Usage:
    python scripts/validate_memory.py                    # Validate all skills
    python scripts/validate_memory.py --skill <path>     # Validate specific skill
    python scripts/validate_memory.py --strict           # Fail on warnings too
    python scripts/validate_memory.py --stats            # Show statistics only
"""

import os
import sys
import re
import argparse
from pathlib import Path
from typing import List, Tuple, Dict
from datetime import datetime, timedelta


# Governance Rules
MAX_SKILL_LINES = 400  # Lowered from 500 to ensure 400-line safety buffer
MIN_DESCRIPTION_LENGTH = 40
REQUIRED_DESCRIPTION_PHRASES = ["Use when", "use when"]
REQUIRED_SECTIONS = [
    "Negative Knowledge",
    "Failed Attempts",
]
VALID_NAME_PATTERN = re.compile(r'^[a-z0-9]+(-[a-z0-9]+)*$')
DETERMINISTIC_LOGIC_THRESHOLD = 50  # Lines of if/else or lists before warning
SKILL_FRESHNESS_DAYS = 180  # Skills not verified in 6 months are flagged as stale


class ValidationResult:
    """Container for validation results."""

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.info: List[str] = []

    def add_error(self, message: str):
        self.errors.append(f"❌ {message}")

    def add_warning(self, message: str):
        self.warnings.append(f"⚠️  {message}")

    def add_info(self, message: str):
        self.info.append(f"ℹ️  {message}")

    def is_valid(self, strict: bool = False) -> bool:
        if strict:
            return len(self.errors) == 0 and len(self.warnings) == 0
        return len(self.errors) == 0

    def print_results(self):
        print(f"\n📄 {self.file_path}")
        for msg in self.errors:
            print(f"  {msg}")
        for msg in self.warnings:
            print(f"  {msg}")
        for msg in self.info:
            print(f"  {msg}")
        if not self.errors and not self.warnings:
            print("  ✅ Valid")


def extract_frontmatter(content: str) -> Tuple[Dict, str]:
    """Extract YAML frontmatter and body from markdown content."""
    if not content.startswith('---'):
        return {}, content

    try:
        parts = content.split('---', 2)
        if len(parts) < 3:
            return {}, content

        frontmatter_text = parts[1].strip()
        body = parts[2].strip()

        # Simple YAML parser (handles basic key: value pairs)
        metadata = {}
        for line in frontmatter_text.split('\n'):
            line = line.strip()
            if ':' in line and not line.startswith('#'):
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")

                # Handle arrays
                if value.startswith('[') and value.endswith(']'):
                    value = [v.strip().strip('"').strip("'") for v in value[1:-1].split(',') if v.strip()]
                # Handle empty arrays
                elif value == '[]':
                    value = []

                metadata[key] = value

        return metadata, body

    except Exception as e:
        return {}, content


def validate_skill_file(file_path: Path) -> ValidationResult:
    """Validate a single SKILL.md file."""
    # Handle both absolute and relative paths
    try:
        rel_path = file_path.relative_to(Path.cwd())
    except ValueError:
        # Already relative or different base
        rel_path = file_path
    result = ValidationResult(str(rel_path))

    # Read file
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        result.add_error(f"Failed to read file: {e}")
        return result

    # Check if file is empty
    if not content.strip():
        result.add_error("File is empty")
        return result

    # Extract frontmatter and body
    metadata, body = extract_frontmatter(content)

    # 1. Validate frontmatter exists
    if not metadata:
        result.add_error("Missing or invalid YAML frontmatter (must start with ---)")
        return result

    # 2. Validate required frontmatter fields
    if 'name' not in metadata:
        result.add_error("Frontmatter missing required field: 'name'")
    else:
        # Validate name format (kebab-case)
        name = metadata['name']
        if not VALID_NAME_PATTERN.match(name):
            result.add_error(f"Invalid name format: '{name}'. Use kebab-case: verb-noun-context")

    if 'description' not in metadata:
        result.add_error("Frontmatter missing required field: 'description'")
    else:
        # Validate description quality
        desc = metadata['description']
        if len(desc) < MIN_DESCRIPTION_LENGTH:
            result.add_warning(
                f"Description too vague ({len(desc)} chars, min {MIN_DESCRIPTION_LENGTH}). "
                "Add specific trigger conditions."
            )

        # Check for trigger phrase
        has_trigger = any(phrase in desc for phrase in REQUIRED_DESCRIPTION_PHRASES)
        if not has_trigger:
            result.add_warning(
                "Description should include 'Use when' to define trigger conditions"
            )

    if 'version' not in metadata:
        result.add_warning("Frontmatter missing recommended field: 'version'")

    if 'last_verified' not in metadata:
        result.add_warning("Frontmatter missing recommended field: 'last_verified' (tracks skill freshness)")
    else:
        # Validate date format (YYYY-MM-DD)
        last_verified = metadata['last_verified']
        date_pattern = re.compile(r'^\d{4}-\d{2}-\d{2}$')
        if not date_pattern.match(str(last_verified)):
            result.add_warning(
                f"Invalid 'last_verified' format: '{last_verified}'. Use YYYY-MM-DD format"
            )
        else:
            # Check for staleness (Context Rot)
            try:
                verified_date = datetime.strptime(str(last_verified), '%Y-%m-%d')
                days_since_verified = (datetime.now() - verified_date).days
                if days_since_verified > SKILL_FRESHNESS_DAYS:
                    result.add_warning(
                        f"⏰ STALE: Last verified {days_since_verified} days ago (>{SKILL_FRESHNESS_DAYS} days). "
                        "Verify skill still works or archive it to prevent 'Context Rot'"
                    )
            except ValueError:
                pass  # Date format already checked above

    if 'author' not in metadata:
        result.add_warning("Frontmatter missing recommended field: 'author' (for ownership tracking)")

    if 'tags' in metadata:
        tags = metadata['tags']
        if isinstance(tags, list) and len(tags) == 0:
            result.add_info("Consider adding tags for better skill organization and discovery")

    # Check for enterprise skills (in plugins/company-* directories) - allowed-tools is MANDATORY
    is_enterprise_skill = 'plugins/company-' in str(file_path) or 'plugins/enterprise-' in str(file_path)

    if 'allowed-tools' in metadata:
        allowed_tools = metadata['allowed-tools']
        if isinstance(allowed_tools, list) and len(allowed_tools) == 0:
            if is_enterprise_skill:
                result.add_error("Enterprise skills MUST specify 'allowed-tools' for governance and security")
            else:
                result.add_info("Consider specifying allowed-tools to restrict skill tool usage")
    else:
        if is_enterprise_skill:
            result.add_error("Enterprise skills MUST include 'allowed-tools' field in frontmatter")

    # 3. Validate Negative Knowledge section
    has_negative_knowledge = any(
        section in body for section in REQUIRED_SECTIONS
    )

    if not has_negative_knowledge:
        result.add_error(
            "Missing required section: 'Negative Knowledge' or 'Failed Attempts'. "
            "Document what FAILED, not just what worked."
        )
    else:
        # Check if it actually has content (not just the header)
        neg_knowledge_match = re.search(
            r'#+\s*(Negative Knowledge|Failed Attempts).*?\n(.*?)(?=\n#+|\Z)',
            body,
            re.DOTALL | re.IGNORECASE
        )
        if neg_knowledge_match:
            section_content = neg_knowledge_match.group(2).strip()
            # Check if it has a table or substantial content
            if len(section_content) < 100 and '|' not in section_content:
                result.add_warning(
                    "Negative Knowledge section exists but appears empty or minimal. "
                    "Add at least one documented failure."
                )

    # 4. Validate context budget (file size)
    line_count = len(body.split('\n'))
    if line_count > MAX_SKILL_LINES:
        result.add_error(
            f"❌ FAIL: Exceeds token budget: {line_count} lines (max {MAX_SKILL_LINES}). "
            f"Skills > {MAX_SKILL_LINES} lines degrade model performance.\n"
            f"   -> ACTION: Extract logic to a 'Zero-Context Script' in scripts/\n"
            f"   -> OR: Move detailed documentation to reference.md"
        )
    elif line_count > MAX_SKILL_LINES * 0.8:
        result.add_warning(
            f"Approaching context limit: {line_count}/{MAX_SKILL_LINES} lines. "
            "Consider splitting or moving details to reference.md to preserve 'Instruction Budget'"
        )

    # 5. Check for deterministic logic that should be in scripts
    # Detect if/else patterns and list declarations
    if_else_pattern = re.compile(r'^\s*(if|elif|else|switch|case)\s', re.MULTILINE)
    list_pattern = re.compile(r'^\s*[-*]\s+\w+:\s*["\']', re.MULTILINE)  # Detect config-like lists

    if_else_matches = if_else_pattern.findall(body)
    list_matches = list_pattern.findall(body)

    deterministic_lines = len(if_else_matches) + (len(list_matches) // 2)  # Rough estimate

    if deterministic_lines > DETERMINISTIC_LOGIC_THRESHOLD:
        result.add_warning(
            f"Detected {deterministic_lines} lines of deterministic logic (if/else, hardcoded lists). "
            "Move complex logic to scripts/ for zero-context execution"
        )

    # 6. Check for common anti-patterns
    if 'TODO' in body or 'FIXME' in body:
        result.add_warning("Contains TODO/FIXME markers - complete before committing")

    # 7. Validate structure (should have numbered sections)
    section_pattern = re.compile(r'^#+\s+\d+\.\s+', re.MULTILINE)
    sections = section_pattern.findall(body)
    if len(sections) < 3:
        result.add_info(
            "Consider organizing content with numbered sections (## 1. Context, ## 2. Negative Knowledge, etc.)"
        )

    return result


def find_all_skills(base_path: Path = Path('.claude/skills')) -> List[Path]:
    """Find all SKILL.md files in the repository."""
    skills = []

    if not base_path.exists():
        return skills

    for root, dirs, files in os.walk(base_path):
        if 'SKILL.md' in files:
            skills.append(Path(root) / 'SKILL.md')

    return skills


def print_statistics(results: List[ValidationResult]):
    """Print summary statistics."""
    total = len(results)
    valid = sum(1 for r in results if r.is_valid())
    with_warnings = sum(1 for r in results if r.warnings and not r.errors)
    with_errors = sum(1 for r in results if r.errors)

    print("\n" + "=" * 60)
    print("📊 VALIDATION STATISTICS")
    print("=" * 60)
    print(f"Total skills validated: {total}")
    print(f"✅ Valid (no errors):   {valid}")
    print(f"⚠️  With warnings:       {with_warnings}")
    print(f"❌ With errors:         {with_errors}")

    if total > 0:
        success_rate = (valid / total) * 100
        print(f"\nSuccess rate: {success_rate:.1f}%")

    # Calculate total lines across all skills
    total_lines = 0
    for skill_path in find_all_skills():
        try:
            with open(skill_path, 'r') as f:
                total_lines += len(f.readlines())
        except:
            pass

    avg_lines = total_lines / total if total > 0 else 0
    print(f"Average skill size: {avg_lines:.0f} lines (max {MAX_SKILL_LINES})")

    # Context efficiency
    if avg_lines > 0:
        efficiency = (1 - (avg_lines / MAX_SKILL_LINES)) * 100
        print(f"Context efficiency: {efficiency:.1f}% headroom remaining")

    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description='Validate SKILL.md files against governance rules'
    )
    parser.add_argument(
        '--skill',
        type=str,
        help='Validate specific skill file instead of all skills'
    )
    parser.add_argument(
        '--strict',
        action='store_true',
        help='Fail on warnings as well as errors'
    )
    parser.add_argument(
        '--stats',
        action='store_true',
        help='Show statistics only'
    )

    args = parser.parse_args()

    # Find skills to validate
    if args.skill:
        skill_path = Path(args.skill)
        if not skill_path.exists():
            print(f"❌ Skill file not found: {args.skill}")
            sys.exit(1)
        skills = [skill_path]
    else:
        skills = find_all_skills()

    if not skills:
        print("⚠️  No SKILL.md files found in .claude/skills/")
        print("   Create your first skill using the template in .claude/templates/")
        sys.exit(0)

    # Validate all skills
    results = []
    for skill_path in skills:
        result = validate_skill_file(skill_path)
        results.append(result)
        if not args.stats:
            result.print_results()

    # Print statistics
    print_statistics(results)

    # Determine exit code
    if args.strict:
        has_issues = any(not r.is_valid(strict=True) for r in results)
    else:
        has_issues = any(not r.is_valid(strict=False) for r in results)

    if has_issues:
        print("\n❌ Validation failed. Fix errors above.")
        sys.exit(1)
    else:
        print("\n✅ All skills are valid!")
        sys.exit(0)


if __name__ == '__main__':
    main()
