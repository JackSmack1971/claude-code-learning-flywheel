#!/usr/bin/env python3
"""
Validate all SKILL.md files in the repository against governance rules.

This script enforces the Learning Flywheel's core principles:
1. Negative Knowledge must be documented
2. Versioning must be bumped when knowledge changes
3. Context must be kept within budget
4. Skills must have specific trigger descriptions
5. Format must follow the standard template

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
import subprocess
from pathlib import Path
from typing import List, Tuple, Dict, Optional
from datetime import datetime, timedelta

# Import robust YAML parser
from yaml_parser import extract_frontmatter
from skill_checkers import MetadataChecker, ContentChecker, BudgetChecker


# Governance Rules
MAX_SKILL_LINES = 500  # Hard limit from CLAUDE.md governance framework
RECOMMENDED_SKILL_LINES = 400  # Recommended limit to ensure safety buffer
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


def safe_relative_path(path: Path, base: Optional[Path] = None) -> Path:
    """Safely compute relative path, falling back to resolved path if needed.

    This prevents ValueError when paths don't share a common ancestor
    or when mixing relative and absolute paths.
    """
    try:
        # Resolve both paths to absolute
        abs_path = path.resolve()
        abs_base = (base or Path.cwd()).resolve()

        # Try to compute relative path
        return abs_path.relative_to(abs_base)
    except ValueError:
        # Paths don't share common ancestor - return resolved path
        return path.resolve()


def get_git_file_content(file_path: Path, ref: str = 'HEAD') -> Optional[str]:
    """Get file content from git at a specific ref (commit/branch)."""
    try:
        # Check if we're in a git repo
        result = subprocess.run(
            ['git', 'rev-parse', '--git-dir'],
            capture_output=True,
            text=True,
            cwd=file_path.parent if file_path.is_file() else file_path,
            timeout=5
        )
        if result.returncode != 0:
            return None

        # Get file content from git
        result = subprocess.run(
            ['git', 'show', f'{ref}:{file_path}'],
            capture_output=True,
            text=True,
            cwd=Path.cwd(),
            timeout=5
        )
        if result.returncode == 0:
            return result.stdout
        return None
    except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
        return None


def parse_semver(version: str) -> Optional[Tuple[int, int, int]]:
    """Parse semantic version string (e.g., '1.2.3') into tuple (major, minor, patch)."""
    try:
        # Handle version strings like "1.0.0" or "v1.0.0"
        version = version.strip().lower().lstrip('v')
        parts = version.split('.')
        if len(parts) >= 3:
            major = int(parts[0])
            minor = int(parts[1])
            patch = int(parts[2])
            return (major, minor, patch)
        return None
    except (ValueError, AttributeError):
        return None


def compare_versions(old_ver: str, new_ver: str) -> str:
    """Compare two semantic versions.

    Returns:
        'bumped' if version increased
        'same' if versions are identical
        'invalid' if either version is malformed
    """
    old = parse_semver(old_ver)
    new = parse_semver(new_ver)

    if not old or not new:
        return 'invalid'

    if new > old:
        return 'bumped'
    elif new == old:
        return 'same'
    else:
        return 'invalid'


def extract_negative_knowledge(body: str) -> str:
    """Extract the Negative Knowledge section from skill body."""
    # Match "Negative Knowledge" or "Failed Attempts" section
    pattern = r'#+\s*(Negative Knowledge|Failed Attempts).*?\n(.*?)(?=\n#+|\Z)'
    match = re.search(pattern, body, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(2).strip()
    return ''


def validate_skill_file(file_path: Path) -> ValidationResult:
    """Validate a single SKILL.md file."""
    # Handle both absolute and relative paths safely
    rel_path = safe_relative_path(file_path)
    result = ValidationResult(str(rel_path))

    # Configuration for checkers
    config = {
        'valid_name_pattern': VALID_NAME_PATTERN,
        'min_description_length': MIN_DESCRIPTION_LENGTH,
        'required_description_phrases': REQUIRED_DESCRIPTION_PHRASES,
        'required_sections': REQUIRED_SECTIONS,
        'max_skill_lines': MAX_SKILL_LINES,
        'recommended_skill_lines': RECOMMENDED_SKILL_LINES,
        'deterministic_logic_threshold': DETERMINISTIC_LOGIC_THRESHOLD,
    }

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

    # 2. Run Metadata Validations via modular checker
    metadata_checker = MetadataChecker(result, config)
    metadata_checker.check(metadata, file_path)

    # 3. Handle specific versioning and git logic (kept here for coordination)
    if 'version' in metadata:
        current_version = metadata['version']
        if parse_semver(current_version):
            try:
                # Get relative path for git (safely)
                git_path = safe_relative_path(file_path)

                prev_content = get_git_file_content(git_path)
                if prev_content:
                    # Extract previous version and Negative Knowledge
                    prev_metadata, prev_body = extract_frontmatter(prev_content)
                    prev_version = prev_metadata.get('version', '')

                    if prev_version:
                        # Extract Negative Knowledge sections
                        current_neg_knowledge = extract_negative_knowledge(body)
                        prev_neg_knowledge = extract_negative_knowledge(prev_body)

                        # If Negative Knowledge changed, version MUST be bumped
                        if current_neg_knowledge != prev_neg_knowledge:
                            version_comparison = compare_versions(prev_version, current_version)
                            if version_comparison == 'same':
                                result.add_error(
                                    f"❌ GOVERNANCE VIOLATION: Negative Knowledge section changed "
                                    f"but version not bumped (still {current_version}). "
                                    f"Bump version to signal knowledge update."
                                )
                            elif version_comparison == 'bumped':
                                # Version was bumped - good!
                                result.add_info(
                                    f"✓ Version bumped {prev_version} → {current_version} (Negative Knowledge updated)"
                                )
            except Exception:
                # Don't fail validation if git check fails
                pass

    # 4. Run Content and Structural Validations via modular checker
    content_checker = ContentChecker(result, config)
    content_checker.check(body)

    # 5. Run Budget and Anti-pattern Validations via modular checker
    budget_checker = BudgetChecker(result, config)
    budget_checker.check(body)

    # 6. Validate structure (should have numbered sections)
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
    print(f"Average skill size: {avg_lines:.0f} lines (recommended: {RECOMMENDED_SKILL_LINES}, max: {MAX_SKILL_LINES})")

    # Context efficiency
    if avg_lines > 0:
        efficiency = (1 - (avg_lines / RECOMMENDED_SKILL_LINES)) * 100
        print(f"Context efficiency: {efficiency:.1f}% headroom remaining (against recommended limit)")

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
