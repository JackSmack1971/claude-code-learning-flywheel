#!/usr/bin/env python3
"""
Database Migration Safety Validator

Zero-Context Executor: Validates migration files for dangerous patterns.
Usage: python validate_migration.py <migration_file> [--json]
"""

import argparse
import json
import re
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Dict, Any


@dataclass
class MigrationIssue:
    """Represents a single migration safety issue."""
    severity: str  # 'critical', 'warning', 'info'
    category: str
    pattern: str
    line: int
    message: str
    suggestion: str
    context: str  # The actual line from migration


class MigrationValidator:
    """Validates database migration files for dangerous patterns."""

    # Dangerous patterns (pattern, severity, category, message, suggestion)
    DANGEROUS_PATTERNS = [
        # Critical blockers
        (r'\bRENAME\s+COLUMN\b', 'critical', 'breaking-change',
         'Column rename detected - causes immediate downtime',
         'Use multi-step: Add new column → backfill → switch code → drop old'),

        (r'\bRENAME\s+TABLE\b', 'critical', 'breaking-change',
         'Table rename detected - breaks all running queries',
         'Create view → migrate code → rename later'),

        (r'ADD\s+COLUMN\s+\w+.*NOT\s+NULL(?!\s+DEFAULT)', 'critical', 'data-integrity',
         'Adding NOT NULL column without DEFAULT on existing table',
         'Add as nullable → backfill → add constraint separately'),

        (r'ALTER\s+TABLE\s+.*ADD\s+.*DEFAULT.*NOT\s+NULL', 'critical', 'performance',
         'Adding column with DEFAULT and NOT NULL can lock table',
         'Add without default, backfill in batches, then add constraint'),

        (r'\bDROP\s+COLUMN\b', 'critical', 'breaking-change',
         'Dropping column immediately - may break running code',
         'Multi-step: Stop writes → deploy → stop reads → deploy → drop'),

        (r'ALTER\s+COLUMN\s+.*TYPE\s+', 'critical', 'data-loss-risk',
         'Changing column type - risk of data loss',
         'Add new column → migrate data → verify → drop old'),

        # Warnings
        (r'CREATE\s+INDEX\s+(?!CONCURRENTLY)', 'warning', 'performance',
         'Creating index without CONCURRENTLY - locks table',
         'Use CREATE INDEX CONCURRENTLY (PostgreSQL) or equivalent'),

        (r'CREATE\s+UNIQUE\s+INDEX\s+(?!CONCURRENTLY)', 'warning', 'performance',
         'Creating unique index without CONCURRENTLY',
         'Use CREATE UNIQUE INDEX CONCURRENTLY'),

        (r'\bDROP\s+INDEX\s+(?!CONCURRENTLY)', 'warning', 'performance',
         'Dropping index without CONCURRENTLY',
         'Use DROP INDEX CONCURRENTLY'),

        (r'ADD\s+CONSTRAINT.*FOREIGN\s+KEY', 'warning', 'performance',
         'Adding foreign key constraint - may lock table',
         'Create index first, then add constraint with NOT VALID → validate later'),

        (r'\bTRUNCATE\s+TABLE\b', 'warning', 'data-loss-risk',
         'TRUNCATE TABLE - deletes all data permanently',
         'Ensure this is intentional and backed up'),

        (r'\bDROP\s+TABLE\b', 'critical', 'data-loss-risk',
         'DROP TABLE - permanent data deletion',
         'Ensure table is unused and backed up'),

        # Info
        (r'ALTER\s+TABLE\s+.*ADD\s+COLUMN\s+.*DEFAULT', 'info', 'performance',
         'Adding column with DEFAULT value',
         'For large tables, consider adding without default then backfilling'),
    ]

    # Table size hints (if these tables are mentioned, extra caution)
    LARGE_TABLE_PATTERNS = [
        r'\busers\b', r'\borders\b', r'\btransactions\b',
        r'\bevents\b', r'\blogs\b', r'\banalytics\b'
    ]

    def __init__(self, migration_file: Path):
        self.migration_file = migration_file
        self.issues: List[MigrationIssue] = []

    def read_migration(self) -> str:
        """Read migration file content."""
        try:
            with open(self.migration_file, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            print(f"Error: Migration file not found: {self.migration_file}", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"Error reading migration file: {e}", file=sys.stderr)
            sys.exit(1)

    def check_large_table(self, content: str) -> bool:
        """Check if migration operates on potentially large tables."""
        for pattern in self.LARGE_TABLE_PATTERNS:
            if re.search(pattern, content, re.IGNORECASE):
                return True
        return False

    def validate(self, content: str) -> None:
        """Validate migration content for dangerous patterns."""
        lines = content.split('\n')
        is_large_table = self.check_large_table(content)

        for line_num, line in enumerate(lines, start=1):
            # Skip comments and empty lines
            if line.strip().startswith('--') or not line.strip():
                continue

            # Check against all dangerous patterns
            for pattern, severity, category, message, suggestion in self.DANGEROUS_PATTERNS:
                if re.search(pattern, line, re.IGNORECASE):
                    # Upgrade severity if operating on large table
                    if is_large_table and severity == 'warning':
                        severity = 'critical'
                        message += ' (operating on large table)'

                    issue = MigrationIssue(
                        severity=severity,
                        category=category,
                        pattern=pattern,
                        line=line_num,
                        message=message,
                        suggestion=suggestion,
                        context=line.strip()
                    )
                    self.issues.append(issue)

    def check_migration_structure(self, content: str) -> None:
        """Check for best practices in migration structure."""
        # Check for transaction usage
        has_begin = re.search(r'\bBEGIN\b', content, re.IGNORECASE)
        has_commit = re.search(r'\bCOMMIT\b', content, re.IGNORECASE)

        if not has_begin or not has_commit:
            issue = MigrationIssue(
                severity='info',
                category='best-practice',
                pattern='N/A',
                line=0,
                message='Migration not wrapped in transaction',
                suggestion='Wrap DDL in BEGIN/COMMIT for atomicity (except CONCURRENTLY ops)',
                context='<entire migration>'
            )
            self.issues.append(issue)

        # Check for rollback documentation
        has_rollback_comment = re.search(r'--.*rollback', content, re.IGNORECASE)
        if not has_rollback_comment:
            issue = MigrationIssue(
                severity='info',
                category='best-practice',
                pattern='N/A',
                line=0,
                message='No rollback plan documented',
                suggestion='Add comment with rollback instructions',
                context='<entire migration>'
            )
            self.issues.append(issue)

    def generate_report(self, as_json: bool = False) -> str:
        """Generate validation report."""
        critical = [i for i in self.issues if i.severity == 'critical']
        warnings = [i for i in self.issues if i.severity == 'warning']
        info = [i for i in self.issues if i.severity == 'info']

        if as_json:
            return json.dumps({
                'migration_file': str(self.migration_file),
                'critical_count': len(critical),
                'warning_count': len(warnings),
                'info_count': len(info),
                'total_issues': len(self.issues),
                'safe_to_apply': len(critical) == 0,
                'issues': [asdict(i) for i in self.issues]
            }, indent=2)

        # Markdown report
        report = [f"# Migration Safety Report: {self.migration_file.name}\n"]

        if not self.issues:
            report.append("✅ **No issues found!** Migration appears safe.\n")
            return '\n'.join(report)

        if critical:
            report.append(f"## 🚫 CRITICAL Issues ({len(critical)})\n")
            report.append("**BLOCKING: Do NOT apply this migration without addressing these:**\n")
            for issue in critical:
                report.append(f"### Line {issue.line}: {issue.message}")
                report.append(f"```sql\n{issue.context}\n```")
                report.append(f"**Category:** {issue.category}")
                report.append(f"**Fix:** {issue.suggestion}\n")

        if warnings:
            report.append(f"## ⚠️  Warnings ({len(warnings)})\n")
            report.append("**Review these carefully:**\n")
            for issue in warnings:
                report.append(f"- **Line {issue.line}:** {issue.message}")
                report.append(f"  - SQL: `{issue.context}`")
                report.append(f"  - Suggestion: {issue.suggestion}\n")

        if info:
            report.append(f"## 💡 Info ({len(info)})\n")
            report.append("**Best practices:**\n")
            for issue in info:
                report.append(f"- {issue.message}")
                report.append(f"  - {issue.suggestion}\n")

        # Summary
        report.append("## Summary\n")
        if critical:
            report.append("❌ **Migration is UNSAFE** - Critical issues must be fixed.\n")
        elif warnings:
            report.append("⚠️  **Migration has warnings** - Review carefully before applying.\n")
        else:
            report.append("✅ **Migration is safe** - Only informational items noted.\n")

        return '\n'.join(report)

    def run(self, as_json: bool = False) -> int:
        """Execute validation process."""
        content = self.read_migration()

        # Run validations
        self.validate(content)
        self.check_migration_structure(content)

        # Generate report
        report = self.generate_report(as_json)
        print(report)

        # Exit code based on critical issues
        critical = [i for i in self.issues if i.severity == 'critical']
        return 1 if critical else 0


def main():
    parser = argparse.ArgumentParser(
        description='Validate database migration files for safety'
    )
    parser.add_argument(
        'migration_file',
        type=Path,
        help='Path to migration file to validate'
    )
    parser.add_argument(
        '--json',
        action='store_true',
        help='Output results as JSON'
    )

    args = parser.parse_args()

    if not args.migration_file.exists():
        print(f"Error: Migration file not found: {args.migration_file}", file=sys.stderr)
        sys.exit(1)

    validator = MigrationValidator(args.migration_file)
    exit_code = validator.run(as_json=args.json)
    sys.exit(exit_code)


if __name__ == '__main__':
    main()
