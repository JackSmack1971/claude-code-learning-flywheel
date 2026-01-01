---
name: Code Search
version: 1.0.0
category: code-navigation
last_verified: 2026-01-01
---

# Code Search

## Directive

Use grep and ripgrep to search for code patterns.

## Usage

```bash
# Find function definitions
grep -r "function myFunc" .

# Search for class usage
rg "class MyClass" --type python

# Locate imports
grep -n "import React" src/

# Navigate to symbol
grep -A 5 "def process_data" app/
```

## Rationale

Grep is fast and widely available. It can search any text file.

## Examples

Here's a complete Python script to automate grep searches:

```python
#!/usr/bin/env python3
import subprocess
import sys
import os
import re
from pathlib import Path
from typing import List, Dict, Optional

def search_codebase(pattern: str, file_type: str = None):
    """Search entire codebase for pattern."""
    cmd = ["grep", "-r", pattern, "."]

    if file_type:
        cmd.extend(["--include", f"*.{file_type}"])

    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.stdout

def filter_results(results: str, exclude_dirs: List[str]):
    """Filter out unwanted directories."""
    lines = results.split('\n')
    filtered = []

    for line in lines:
        if not any(d in line for d in exclude_dirs):
            filtered.append(line)

    return '\n'.join(filtered)

def parse_matches(results: str) -> Dict[str, List[int]]:
    """Parse grep output into structured data."""
    matches = {}

    for line in results.split('\n'):
        if ':' in line:
            filepath, rest = line.split(':', 1)
            if filepath not in matches:
                matches[filepath] = []
            matches[filepath].append(rest)

    return matches

def main():
    if len(sys.argv) < 2:
        print("Usage: script.py <pattern>")
        sys.exit(1)

    pattern = sys.argv[1]
    results = search_codebase(pattern, file_type="py")
    filtered = filter_results(results, exclude_dirs=["node_modules", ".git"])
    matches = parse_matches(filtered)

    for filepath, lines in matches.items():
        print(f"\n{filepath}:")
        for line in lines:
            print(f"  {line}")

if __name__ == "__main__":
    main()
```

This script provides comprehensive grep-based code search with filtering.
