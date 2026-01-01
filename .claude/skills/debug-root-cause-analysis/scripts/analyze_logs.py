#!/usr/bin/env python3
"""
Zero-Context Log Analyzer for Debugging

Parses error logs to identify patterns, frequencies, and temporal correlations.
Helps identify root causes by aggregating error information.

Usage:
    python analyze_logs.py --log-file logs/error.log --error-pattern "TypeError"
    python analyze_logs.py --log-file logs/error.log --time-range "last 24h"
"""

import argparse
import re
import sys
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple


class LogEntry:
    """Represents a single log entry."""

    def __init__(self, timestamp: str, level: str, message: str, stacktrace: List[str]):
        self.timestamp = timestamp
        self.level = level
        self.message = message
        self.stacktrace = stacktrace

    def __repr__(self):
        return f"LogEntry({self.level}: {self.message[:50]}...)"


class LogAnalyzer:
    """Analyzes logs for error patterns and frequencies."""

    def __init__(self, log_file: Path):
        self.log_file = log_file
        self.entries: List[LogEntry] = []
        self.error_counts: Dict[str, int] = defaultdict(int)
        self.error_timestamps: Dict[str, List[datetime]] = defaultdict(list)
        self.error_stacks: Dict[str, List[str]] = defaultdict(list)

    def parse_log_file(self) -> None:
        """Parse log file and extract structured entries."""
        if not self.log_file.exists():
            print(f"Error: Log file not found: {self.log_file}", file=sys.stderr)
            sys.exit(1)

        with open(self.log_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Common log patterns
        # ISO timestamp pattern: 2026-01-01T10:23:45.123Z
        timestamp_pattern = r'\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d{3})?(?:Z|[+-]\d{2}:\d{2})?'
        # Level pattern: ERROR, WARN, INFO, DEBUG
        level_pattern = r'\b(ERROR|WARN|WARNING|INFO|DEBUG|FATAL)\b'

        # Split logs into individual entries (assumes each entry starts with timestamp)
        log_pattern = re.compile(
            rf'({timestamp_pattern})\s*(?:\[|\|)?\s*({level_pattern})\s*(?:\]|\|)?\s*(.*?)(?=\n{timestamp_pattern}|\Z)',
            re.DOTALL
        )

        matches = log_pattern.finditer(content)
        for match in matches:
            timestamp, level, message = match.groups()
            # Extract stack trace if present
            stacktrace = self._extract_stacktrace(message)
            entry = LogEntry(timestamp, level, message, stacktrace)
            self.entries.append(entry)

            # Track errors
            if level in ('ERROR', 'FATAL'):
                error_key = self._get_error_key(message)
                self.error_counts[error_key] += 1
                try:
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    self.error_timestamps[error_key].append(dt)
                except ValueError:
                    pass  # Skip entries with unparseable timestamps

                if stacktrace:
                    self.error_stacks[error_key].extend(stacktrace)

    def _extract_stacktrace(self, message: str) -> List[str]:
        """Extract stack trace lines from error message."""
        stacktrace = []
        lines = message.split('\n')
        for line in lines:
            # Common stack trace patterns
            if re.search(r'\s+at\s+.*\(.*:\d+:\d+\)', line) or \
               re.search(r'\s+at\s+.*:\d+:\d+', line) or \
               re.search(r'File\s+".*",\s+line\s+\d+', line):
                stacktrace.append(line.strip())
        return stacktrace

    def _get_error_key(self, message: str) -> str:
        """Extract a normalized key from error message for grouping."""
        # Extract first line (usually the error type and message)
        first_line = message.split('\n')[0]

        # Remove dynamic parts like IDs, numbers, timestamps
        normalized = re.sub(r'\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b', '<UUID>', first_line)
        normalized = re.sub(r'\b\d{4}-\d{2}-\d{2}', '<DATE>', normalized)
        normalized = re.sub(r'\b\d+\b', '<NUM>', normalized)

        return normalized[:200]  # Limit key length

    def filter_by_pattern(self, pattern: str) -> None:
        """Filter entries by regex pattern."""
        regex = re.compile(pattern, re.IGNORECASE)
        self.entries = [e for e in self.entries if regex.search(e.message)]

    def filter_by_time_range(self, time_range: str) -> None:
        """Filter entries by time range (e.g., 'last 24h', 'last 7d')."""
        now = datetime.now()
        match = re.match(r'last\s+(\d+)\s*(h|d|hours?|days?)', time_range, re.IGNORECASE)
        if not match:
            print(f"Invalid time range format: {time_range}", file=sys.stderr)
            print("Use format like 'last 24h' or 'last 7d'", file=sys.stderr)
            return

        amount, unit = match.groups()
        amount = int(amount)
        unit = unit.lower()

        if unit.startswith('h'):
            delta = timedelta(hours=amount)
        else:
            delta = timedelta(days=amount)

        cutoff = now - delta

        filtered_entries = []
        for entry in self.entries:
            try:
                timestamp = datetime.fromisoformat(entry.timestamp.replace('Z', '+00:00'))
                if timestamp >= cutoff:
                    filtered_entries.append(entry)
            except ValueError:
                continue

        self.entries = filtered_entries

    def generate_report(self) -> str:
        """Generate a formatted analysis report."""
        lines = []
        lines.append("=" * 60)
        lines.append("LOG ANALYSIS REPORT")
        lines.append("=" * 60)
        lines.append(f"Log file: {self.log_file}")
        lines.append(f"Total entries analyzed: {len(self.entries)}")
        lines.append("")

        if not self.error_counts:
            lines.append("No errors found in the analyzed logs.")
            return "\n".join(lines)

        lines.append("ERROR FREQUENCY ANALYSIS:")
        lines.append("-" * 60)

        # Sort errors by frequency
        sorted_errors = sorted(self.error_counts.items(), key=lambda x: x[1], reverse=True)

        for error_key, count in sorted_errors[:10]:  # Top 10 errors
            lines.append(f"\n{error_key}")
            lines.append(f"  Occurrences: {count}")

            # Time information
            if error_key in self.error_timestamps:
                timestamps = sorted(self.error_timestamps[error_key])
                if timestamps:
                    lines.append(f"  First seen: {timestamps[0]}")
                    lines.append(f"  Last seen:  {timestamps[-1]}")

                    # Find peak hour
                    hour_counts = defaultdict(int)
                    for ts in timestamps:
                        hour_counts[ts.hour] += 1
                    if hour_counts:
                        peak_hour, peak_count = max(hour_counts.items(), key=lambda x: x[1])
                        lines.append(f"  Peak hour:  {peak_hour}:00 ({peak_count} errors)")

            # Stack trace information
            if error_key in self.error_stacks:
                stacks = self.error_stacks[error_key]
                if stacks:
                    # Find most common stack trace line
                    stack_counts = defaultdict(int)
                    for stack_line in stacks:
                        stack_counts[stack_line] += 1
                    if stack_counts:
                        most_common_stack = max(stack_counts.items(), key=lambda x: x[1])
                        lines.append(f"  Most common stack trace line:")
                        lines.append(f"    {most_common_stack[0]} ({most_common_stack[1]} times)")

        lines.append("\n" + "=" * 60)
        return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Analyze error logs for debugging",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python analyze_logs.py --log-file logs/error.log
  python analyze_logs.py --log-file logs/error.log --error-pattern "TypeError|null"
  python analyze_logs.py --log-file logs/error.log --time-range "last 24h"
        """
    )

    parser.add_argument(
        '--log-file',
        type=Path,
        required=True,
        help='Path to the log file to analyze'
    )

    parser.add_argument(
        '--error-pattern',
        type=str,
        help='Regex pattern to filter errors (e.g., "TypeError|ReferenceError")'
    )

    parser.add_argument(
        '--time-range',
        type=str,
        help='Time range to analyze (e.g., "last 24h", "last 7d")'
    )

    args = parser.parse_args()

    analyzer = LogAnalyzer(args.log_file)
    analyzer.parse_log_file()

    if args.error_pattern:
        analyzer.filter_by_pattern(args.error_pattern)

    if args.time_range:
        analyzer.filter_by_time_range(args.time_range)

    report = analyzer.generate_report()
    print(report)

    # Exit with error code if errors were found
    sys.exit(0 if not analyzer.error_counts else 1)


if __name__ == '__main__':
    main()
