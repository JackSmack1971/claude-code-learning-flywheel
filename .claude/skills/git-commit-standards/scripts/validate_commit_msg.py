#!/usr/bin/env python3
"""
Validate commit messages against conventional commit format.

Usage:
    python validate_commit_msg.py <commit-msg-file>  # Pre-commit hook
    python validate_commit_msg.py HEAD                # Validate last commit
    python validate_commit_msg.py --check-setup       # Verify hooks installed
"""

import re
import sys
import subprocess
from pathlib import Path


CONVENTIONAL_COMMIT_PATTERN = re.compile(
    r'^(feat|fix|docs|style|refactor|test|chore)'
    r'(\([a-z0-9\-]+\))?: '
    r'.{1,72}$',
    re.IGNORECASE
)

# Common secrets patterns (basic check)
SECRET_PATTERNS = [
    re.compile(r'(password|passwd|pwd)\s*=\s*["\'][^"\']+["\']', re.IGNORECASE),
    re.compile(r'(api[_-]?key|apikey)\s*=\s*["\'][^"\']+["\']', re.IGNORECASE),
    re.compile(r'(secret|token)\s*=\s*["\'][^"\']+["\']', re.IGNORECASE),
    re.compile(r'(sk-[a-zA-Z0-9]{32,})'),  # OpenAI API keys
]


def check_hooks_installed():
    """Check if git hooks are properly set up."""
    hook_path = Path('.git/hooks/commit-msg')

    if not hook_path.exists():
        print("⚠️  Git commit-msg hook not found")
        print(f"   Create: {hook_path}")
        print('   Content: #!/bin/bash\\npython scripts/validate_commit_msg.py "$1"')
        return False

    if not hook_path.stat().st_mode & 0o111:
        print(f"⚠️  Hook exists but not executable: chmod +x {hook_path}")
        return False

    print("✅ Git hooks installed correctly")
    return True


def get_commit_message(source):
    """Get commit message from file or git commit reference."""
    if source == '--check-setup':
        return None

    # If it's a file path (from git hook)
    if Path(source).exists():
        with open(source, 'r') as f:
            return f.read().strip()

    # If it's a git reference like HEAD
    try:
        result = subprocess.run(
            ['git', 'log', '-1', '--pretty=%B', source],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        print(f"❌ Invalid commit reference: {source}")
        sys.exit(1)


def validate_commit_message(message):
    """Validate commit message against conventional commit format."""
    lines = message.split('\n')
    subject = lines[0]

    # Check subject line format
    if not CONVENTIONAL_COMMIT_PATTERN.match(subject):
        print("❌ Invalid commit message format")
        print(f"   Got: {subject}")
        print()
        print("   Expected format:")
        print("   <type>(<scope>): <subject>")
        print()
        print("   Valid types: feat, fix, docs, style, refactor, test, chore")
        print("   Example: feat(api): add rate limiting")
        return False

    # Check subject length (already in regex, but explicit check)
    if len(subject) > 72:
        print(f"⚠️  Subject line too long ({len(subject)} chars, max 72)")
        print(f"   {subject}")
        return False

    # Warn if body is missing for complex changes
    if len(lines) == 1 and len(subject) > 50:
        print("⚠️  Consider adding a body to explain this change")
        print("   (Subject is long, might benefit from detailed explanation)")

    print(f"✅ Valid commit message: {subject}")
    return True


def check_for_secrets(message):
    """Basic check for secrets in commit message (shouldn't be there anyway)."""
    for pattern in SECRET_PATTERNS:
        if pattern.search(message):
            print("❌ Possible secret detected in commit message!")
            print("   Remove sensitive data before committing")
            return False
    return True


def main():
    if len(sys.argv) != 2:
        print("Usage: python validate_commit_msg.py <commit-msg-file|commit-ref|--check-setup>")
        sys.exit(1)

    source = sys.argv[1]

    # Special mode: check setup
    if source == '--check-setup':
        success = check_hooks_installed()
        sys.exit(0 if success else 1)

    # Get and validate commit message
    message = get_commit_message(source)
    if not message:
        print("❌ Empty commit message")
        sys.exit(1)

    # Run validations
    format_valid = validate_commit_message(message)
    secrets_clean = check_for_secrets(message)

    if format_valid and secrets_clean:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == '__main__':
    main()
