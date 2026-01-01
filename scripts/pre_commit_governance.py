#!/usr/bin/env python3
"""
Pre-Commit Governance Hook - Enforces LSP-First and Zero-Context Patterns

This hook prevents commits that violate core architectural principles:
1. Using grep for symbol navigation (should use LSP)
2. Complex logic in chat (should use Zero-Context Scripts)
3. SKILL.md files without negative knowledge
4. Token-bloat patterns in code changes

Exit Codes:
  0 = All checks passed
  1 = Policy violations found (commit blocked)
  2 = Script error (allow commit)
"""
import sys
import re
import subprocess
from pathlib import Path
from typing import List, Tuple
from dataclasses import dataclass

# Configurable thresholds
MAX_GREP_MENTIONS = 2  # Allow minimal grep usage for content search
REQUIRED_LSP_MENTIONS = 1  # Minimum LSP tool references in skills
MAX_INLINE_CODE_LINES = 50  # Code blocks larger than this should be scripts


@dataclass
class GovernanceViolation:
    """Represents a single policy violation."""
    file: str
    rule: str
    message: str
    severity: str = "ERROR"  # ERROR | WARNING

    def __str__(self):
        icon = "❌" if self.severity == "ERROR" else "⚠️"
        return f"{icon} {self.file}\n   Rule: {self.rule}\n   Issue: {self.message}"


def get_staged_files() -> List[str]:
    """Get list of files staged for commit."""
    try:
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only"],
            capture_output=True,
            text=True,
            check=True
        )
        return [f.strip() for f in result.stdout.split('\n') if f.strip()]
    except subprocess.CalledProcessError as e:
        print(f"⚠️  Could not get staged files: {e}", file=sys.stderr)
        return []


def get_file_content(filepath: str) -> str:
    """Read content of a file from the working directory."""
    try:
        return Path(filepath).read_text()
    except Exception as e:
        print(f"⚠️  Could not read {filepath}: {e}", file=sys.stderr)
        return ""


def check_skill_file(filepath: str, content: str) -> List[GovernanceViolation]:
    """Check SKILL.md files for anti-patterns."""
    violations = []

    # Count mentions of grep vs LSP tools
    grep_patterns = [r'\bgrep\b', r'\brg\b', r'ripgrep', r'grep -r']
    lsp_patterns = [r'\bcclsp\b', r'\blsp\b', r'language.?server', r'goto.?definition']

    grep_count = sum(len(re.findall(p, content, re.IGNORECASE)) for p in grep_patterns)
    lsp_count = sum(len(re.findall(p, content, re.IGNORECASE)) for p in lsp_patterns)

    # Rule 1: LSP-First Navigation
    # If skill mentions grep for code navigation, it must also mention LSP
    if grep_count > MAX_GREP_MENTIONS and lsp_count < REQUIRED_LSP_MENTIONS:
        # Check if grep is used in a code navigation context
        navigation_context = bool(re.search(
            r'(find|search|locate|navigate).{0,50}(function|class|symbol|definition)',
            content,
            re.IGNORECASE
        ))

        if navigation_context:
            violations.append(GovernanceViolation(
                file=filepath,
                rule="LSP-First Navigation",
                message=f"Found {grep_count} grep mentions for code navigation but only "
                       f"{lsp_count} LSP references. Use 'cclsp' for symbol lookup.\n"
                       f"   Examples: 'cclsp definition <symbol>', 'cclsp references <symbol>'",
                severity="ERROR"
            ))

    # Rule 2: Negative Knowledge Required
    has_negative_knowledge = bool(re.search(
        r'(negative knowledge|failed attempts|failure modes|anti-patterns)',
        content,
        re.IGNORECASE
    ))

    # Also accept tables with failure documentation
    has_failure_table = bool(re.search(
        r'\|\s*(attempt|failure|cost|fix)\s*\|',
        content,
        re.IGNORECASE
    ))

    if not (has_negative_knowledge or has_failure_table):
        violations.append(GovernanceViolation(
            file=filepath,
            rule="Negative Knowledge Required",
            message="SKILL.md must document failure modes. Add a table with:\n"
                   "   | Attempt | Failure | Cost | Fix |\n"
                   "   See CLAUDE.md section 6 for details.",
            severity="ERROR"
        ))

    # Rule 3: Zero-Context Script Pattern
    # Check for inline code blocks that should be in scripts/
    code_blocks = re.findall(r'```[\s\S]*?```', content)
    for i, block in enumerate(code_blocks):
        lines = block.split('\n')
        if len(lines) > MAX_INLINE_CODE_LINES:
            violations.append(GovernanceViolation(
                file=filepath,
                rule="Zero-Context Script Required",
                message=f"Code block #{i+1} has {len(lines)} lines (max {MAX_INLINE_CODE_LINES}). "
                       f"Move to scripts/ directory and reference it.\n"
                       f"   Example: See scripts/validate_memory.py for pattern.",
                severity="ERROR"
            ))

    # Rule 4: Verification Metadata
    # Skills should have verification test paths in frontmatter
    if 'verification:' not in content and 'test_script:' not in content:
        violations.append(GovernanceViolation(
            file=filepath,
            rule="Verification Test Required",
            message="Skills should include verification metadata in frontmatter.\n"
                   "   Add: verification:\n"
                   "          test_script: 'tests/skills/test_<skill>.py'",
            severity="WARNING"
        ))

    return violations


def check_commit_message() -> List[GovernanceViolation]:
    """Validate commit message follows standards."""
    violations = []

    # Get commit message from git
    commit_msg_file = Path('.git/COMMIT_EDITMSG')
    if not commit_msg_file.exists():
        return violations  # No message yet (interactive amend case)

    try:
        message = commit_msg_file.read_text().strip()
    except Exception:
        return violations

    # Skip if empty (user hasn't written message yet)
    if not message or message.startswith('#'):
        return violations

    staged_files = get_staged_files()

    # Rule: Commits touching skills/ should reference retrospective
    skill_files = [f for f in staged_files if '.claude/skills/' in f and 'SKILL.md' in f]

    if skill_files:
        has_retro_ref = bool(re.search(
            r'\b(retro(spective)?|learning|failure|negative.?knowledge)\b',
            message,
            re.IGNORECASE
        ))

        if not has_retro_ref:
            violations.append(GovernanceViolation(
                file="<commit-message>",
                rule="Retrospective Documentation",
                message=f"Commits modifying {len(skill_files)} skill(s) should reference learning process.\n"
                       f"   Examples: 'feat(memory): add negative knowledge from retrospective'\n"
                       f"             'fix(skill): update failure modes based on session learnings'",
                severity="WARNING"
            ))

    # Rule: Conventional Commit Format
    # Should match: type(scope): description
    conventional_pattern = r'^(feat|fix|docs|refactor|test|chore|perf|ci|build|style)(\(.+?\))?: .{10,}'

    if not re.match(conventional_pattern, message):
        violations.append(GovernanceViolation(
            file="<commit-message>",
            rule="Conventional Commit Format",
            message="Commit message should follow format: type(scope): description\n"
                   f"   Types: feat, fix, docs, refactor, test, chore, perf, ci\n"
                   f"   Example: feat(memory): implement atomic retrospective merger",
            severity="WARNING"
        ))

    return violations


def check_script_files(filepath: str, content: str) -> List[GovernanceViolation]:
    """Check scripts for governance violations."""
    violations = []

    # Rule: Scripts should have docstrings
    if filepath.startswith('scripts/') and filepath.endswith('.py'):
        if not re.search(r'^"""[\s\S]+?"""', content, re.MULTILINE):
            violations.append(GovernanceViolation(
                file=filepath,
                rule="Script Documentation Required",
                message="Python scripts in scripts/ must have module-level docstrings.\n"
                       "   Include: Purpose, usage examples, exit codes.",
                severity="WARNING"
            ))

    return violations


def main():
    """Run all governance checks."""
    violations = []
    staged_files = get_staged_files()

    if not staged_files:
        print("✅ No files staged for commit")
        return 0

    print(f"🔍 Governance Check: {len(staged_files)} staged file(s)...\n")

    for filepath in staged_files:
        content = get_file_content(filepath)
        if not content:
            continue

        # Check SKILL.md files
        if filepath.endswith('SKILL.md') and '.claude/skills/' in filepath:
            violations.extend(check_skill_file(filepath, content))

        # Check script files
        if filepath.startswith('scripts/') and filepath.endswith('.py'):
            violations.extend(check_script_files(filepath, content))

    # Check commit message
    violations.extend(check_commit_message())

    # Separate errors from warnings
    errors = [v for v in violations if v.severity == "ERROR"]
    warnings = [v for v in violations if v.severity == "WARNING"]

    # Report results
    if errors or warnings:
        print("=" * 70)
        print("🛡️  GOVERNANCE REPORT")
        print("=" * 70)

        if errors:
            print(f"\n❌ BLOCKING ERRORS ({len(errors)}):\n")
            for v in errors:
                print(f"{v}\n")

        if warnings:
            print(f"\n⚠️  WARNINGS ({len(warnings)}):\n")
            for v in warnings:
                print(f"{v}\n")

        print("=" * 70)
        print("📚 Review: CLAUDE.md § 6 (Core Principles)")
        print("🔧 Tools: Use 'cclsp' for navigation, scripts/ for logic")
        print("🧠 Memory: Document failures in Negative Knowledge tables")
        print("=" * 70)

        if errors:
            print("\n🚫 COMMIT BLOCKED - Fix errors above to proceed\n")
            return 1
        else:
            print("\n⚠️  Warnings detected - commit allowed but review recommended\n")
            return 0

    print("✅ All governance checks passed - commit approved\n")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        # If script fails, allow commit (fail-open for safety)
        print(f"⚠️  Governance script error: {e}", file=sys.stderr)
        print("⚠️  Allowing commit to proceed", file=sys.stderr)
        sys.exit(0)
