#!/usr/bin/env python3
"""
PR Review Standards - Static Analysis Script

Zero-Context Executor: Analyzes git diff for anti-patterns.
Usage: python analyze_diff.py [--base=main] [--json]
"""

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass, asdict
from typing import List, Dict, Any


@dataclass
class Issue:
    """Represents a single code quality issue."""
    severity: str  # 'blocking', 'warning', 'info'
    category: str
    pattern: str
    file: str
    line: int
    message: str
    suggestion: str


class PRReviewer:
    """Automated PR review analyzer."""

    # Anti-patterns to detect (pattern, severity, category, message, suggestion)
    ANTI_PATTERNS = [
        (r'console\.log\(', 'blocking', 'debug-code',
         'console.log found', 'Use logger.debug() or remove'),
        (r'console\.error\(', 'blocking', 'debug-code',
         'console.error found', 'Use logger.error()'),
        (r'debugger;', 'blocking', 'debug-code',
         'Debugger statement found', 'Remove debugger statement'),
        (r'(password|secret|api_key|apikey|token)\s*=\s*["\'][^"\']+["\']',
         'blocking', 'security', 'Hardcoded secret detected',
         'Use environment variables or secrets manager'),
        (r'TODO:|FIXME:|XXX:', 'warning', 'technical-debt',
         'Task marker comment found', 'Resolve or create issue'),
        (r'^\s*#.*code', 'warning', 'code-smell',
         'Commented code block detected', 'Delete and rely on git history'),
        (r'print\(', 'warning', 'debug-code',
         'Print statement found', 'Use logging framework'),
        (r'\.env\s*$', 'blocking', 'security',
         '.env file in commit', 'Add to .gitignore'),
        (r'credentials\.json', 'blocking', 'security',
         'Credentials file in commit', 'Add to .gitignore'),
    ]

    def __init__(self, base_branch: str = 'main'):
        self.base_branch = base_branch
        self.issues: List[Issue] = []

    def get_diff(self) -> str:
        """Get git diff against base branch."""
        try:
            result = subprocess.run(
                ['git', 'diff', f'{self.base_branch}...HEAD'],
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout
        except subprocess.CalledProcessError as e:
            print(f"Error getting git diff: {e}", file=sys.stderr)
            sys.exit(1)

    def get_diff_stats(self) -> Dict[str, int]:
        """Get diff statistics."""
        try:
            result = subprocess.run(
                ['git', 'diff', '--shortstat', f'{self.base_branch}...HEAD'],
                capture_output=True,
                text=True,
                check=True
            )
            stats_line = result.stdout.strip()

            # Parse: "X files changed, Y insertions(+), Z deletions(-)"
            files_changed = 0
            insertions = 0
            deletions = 0

            if 'file' in stats_line:
                files_match = re.search(r'(\d+)\s+files?\s+changed', stats_line)
                if files_match:
                    files_changed = int(files_match.group(1))

            if 'insertion' in stats_line:
                ins_match = re.search(r'(\d+)\s+insertion', stats_line)
                if ins_match:
                    insertions = int(ins_match.group(1))

            if 'deletion' in stats_line:
                del_match = re.search(r'(\d+)\s+deletion', stats_line)
                if del_match:
                    deletions = int(del_match.group(1))

            return {
                'files_changed': files_changed,
                'insertions': insertions,
                'deletions': deletions,
                'total_lines': insertions + deletions
            }
        except subprocess.CalledProcessError:
            return {'files_changed': 0, 'insertions': 0, 'deletions': 0, 'total_lines': 0}

    def parse_diff_line(self, line: str) -> tuple:
        """Parse diff line to extract file and line number."""
        # Diff format: +++ b/path/to/file
        if line.startswith('+++'):
            file_match = re.match(r'\+\+\+ b/(.+)', line)
            if file_match:
                return file_match.group(1), 0
        # Line number format: @@ -old_start,old_count +new_start,new_count @@
        elif line.startswith('@@'):
            line_match = re.search(r'\+(\d+)', line)
            if line_match:
                return None, int(line_match.group(1))
        return None, 0

    def analyze_diff(self, diff_content: str) -> None:
        """Analyze diff content for anti-patterns."""
        current_file = 'unknown'
        current_line = 0

        for line in diff_content.split('\n'):
            # Track current file and line number
            file_info, line_num = self.parse_diff_line(line)
            if file_info:
                current_file = file_info
            if line_num > 0:
                current_line = line_num

            # Only check added lines (starting with +)
            if not line.startswith('+'):
                continue

            # Remove the leading '+'
            code_line = line[1:]

            # Check against all anti-patterns
            for pattern, severity, category, message, suggestion in self.ANTI_PATTERNS:
                if re.search(pattern, code_line, re.IGNORECASE):
                    issue = Issue(
                        severity=severity,
                        category=category,
                        pattern=pattern,
                        file=current_file,
                        line=current_line,
                        message=message,
                        suggestion=suggestion
                    )
                    self.issues.append(issue)

    def check_pr_size(self, stats: Dict[str, int]) -> None:
        """Check if PR exceeds size limits."""
        max_lines = 500
        if stats['total_lines'] > max_lines:
            issue = Issue(
                severity='warning',
                category='pr-size',
                pattern='N/A',
                file='<entire PR>',
                line=0,
                message=f'PR too large: {stats["total_lines"]} lines changed',
                suggestion=f'Split into smaller PRs (<{max_lines} lines)'
            )
            self.issues.append(issue)

    def generate_report(self, as_json: bool = False) -> str:
        """Generate review report."""
        blocking = [i for i in self.issues if i.severity == 'blocking']
        warnings = [i for i in self.issues if i.severity == 'warning']

        if as_json:
            return json.dumps({
                'blocking_count': len(blocking),
                'warning_count': len(warnings),
                'total_issues': len(self.issues),
                'issues': [asdict(i) for i in self.issues]
            }, indent=2)

        # Markdown report
        report = ["# PR Review Report\n"]

        if not self.issues:
            report.append("✅ **No issues found!** PR is clean.\n")
            return '\n'.join(report)

        if blocking:
            report.append(f"## 🚫 Blocking Issues ({len(blocking)})\n")
            report.append("**These MUST be fixed before merging:**\n")
            for issue in blocking:
                report.append(f"- **{issue.file}:{issue.line}** - {issue.message}")
                report.append(f"  - ❌ Pattern: `{issue.pattern}`")
                report.append(f"  - ✅ Fix: {issue.suggestion}\n")

        if warnings:
            report.append(f"## ⚠️  Warnings ({len(warnings)})\n")
            report.append("**Consider addressing these:**\n")
            for issue in warnings:
                report.append(f"- **{issue.file}:{issue.line}** - {issue.message}")
                report.append(f"  - 💡 Suggestion: {issue.suggestion}\n")

        return '\n'.join(report)

    def run(self, as_json: bool = False) -> int:
        """Execute the review process."""
        # Get diff and stats
        diff_content = self.get_diff()
        stats = self.get_diff_stats()

        # Analyze
        self.analyze_diff(diff_content)
        self.check_pr_size(stats)

        # Report
        report = self.generate_report(as_json)
        print(report)

        # Exit code based on blocking issues
        blocking = [i for i in self.issues if i.severity == 'blocking']
        return 1 if blocking else 0


def main():
    parser = argparse.ArgumentParser(
        description='Analyze PR for code quality issues'
    )
    parser.add_argument(
        '--base',
        default='main',
        help='Base branch to compare against (default: main)'
    )
    parser.add_argument(
        '--json',
        action='store_true',
        help='Output results as JSON'
    )

    args = parser.parse_args()

    reviewer = PRReviewer(base_branch=args.base)
    exit_code = reviewer.run(as_json=args.json)
    sys.exit(exit_code)


if __name__ == '__main__':
    main()
