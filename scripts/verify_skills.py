#!/usr/bin/env python3
"""
Execute verification tests for skills to ensure "Knowledge as Infrastructure."

This script solves the "Context Rot" problem by running executable verification
tests for each skill. When tests pass, it automatically updates the `last_verified`
field in the skill's frontmatter, providing proof of correctness.

The verification framework transforms skills from static documentation into
dynamically validated, trustworthy infrastructure.

Usage:
    python scripts/verify_skills.py                    # Verify all skills
    python scripts/verify_skills.py --skill <name>     # Verify specific skill
    python scripts/verify_skills.py --update-dates     # Auto-update last_verified on success
    python scripts/verify_skills.py --strict           # Fail if ANY skill lacks verification
    python scripts/verify_skills.py --report           # Generate verification report
"""

import os
import sys
import re
import argparse
import subprocess
from pathlib import Path
from typing import List, Tuple, Dict, Optional
from datetime import datetime, date
import json


# Configuration
SKILLS_BASE_PATH = Path('.claude/skills')
TESTS_BASE_PATH = Path('tests/skills')
VERIFICATION_TIMEOUT = 60  # seconds per test


class VerificationResult:
    """Container for skill verification results."""

    def __init__(self, skill_path: Path, skill_name: str):
        self.skill_path = skill_path
        self.skill_name = skill_name
        self.has_verification = False
        self.test_command: Optional[str] = None
        self.test_script: Optional[str] = None
        self.test_passed: Optional[bool] = None
        self.test_output: str = ""
        self.test_error: str = ""
        self.last_verified: Optional[str] = None
        self.execution_time: float = 0.0

    def mark_no_verification(self):
        """Mark this skill as having no verification defined."""
        self.has_verification = False
        self.test_passed = None

    def mark_test_passed(self, output: str, execution_time: float):
        """Mark the verification test as passed."""
        self.test_passed = True
        self.test_output = output
        self.execution_time = execution_time

    def mark_test_failed(self, error: str, execution_time: float):
        """Mark the verification test as failed."""
        self.test_passed = False
        self.test_error = error
        self.execution_time = execution_time

    def __str__(self):
        status_icon = "✅" if self.test_passed else "❌" if self.test_passed is False else "⚠️"
        status = "PASS" if self.test_passed else "FAIL" if self.test_passed is False else "NO-TEST"
        return f"{status_icon} [{status}] {self.skill_name} ({self.execution_time:.2f}s)"


def extract_frontmatter(content: str) -> Tuple[Dict, str]:
    """Extract YAML frontmatter and body from markdown content.

    Reuses the same robust parser from validate_memory.py.
    """
    if not content.startswith('---'):
        return {}, content

    try:
        parts = content.split('---', 2)
        if len(parts) < 3:
            return {}, content

        frontmatter_text = parts[1].strip()
        body = parts[2].strip()

        # Robust YAML parser
        metadata = {}
        for line_num, line in enumerate(frontmatter_text.split('\n'), 1):
            original_line = line
            line = line.strip()

            # Skip empty lines and comments
            if not line or line.startswith('#'):
                continue

            # Must contain colon for key:value
            if ':' not in line:
                continue

            try:
                # Split on first colon only
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip()

                # Validate key (must be non-empty and valid YAML key)
                if not key or key.startswith('-'):
                    continue

                # Handle quoted strings (preserve colons inside quotes)
                if value:
                    # Remove quotes if present
                    if (value.startswith('"') and value.endswith('"')) or \
                       (value.startswith("'") and value.endswith("'")):
                        value = value[1:-1]
                    # Handle arrays
                    elif value.startswith('[') and value.endswith(']'):
                        # Parse inline array
                        array_content = value[1:-1].strip()
                        if not array_content:
                            value = []
                        else:
                            # Split by comma and clean each item
                            items = []
                            for item in array_content.split(','):
                                item = item.strip()
                                # Remove quotes from array items
                                if (item.startswith('"') and item.endswith('"')) or \
                                   (item.startswith("'") and item.endswith("'")):
                                    item = item[1:-1]
                                if item:
                                    items.append(item)
                            value = items
                    # Handle nested objects (for verification field)
                    elif value == '':
                        # This might be a parent key for nested fields
                        # We'll handle this below by looking for indented lines
                        value = {}
                    # Handle empty/null values
                    elif value.lower() in ('null', '~', ''):
                        value = ''
                else:
                    value = ''

                metadata[key] = value

            except ValueError:
                # Line doesn't follow key:value format, skip it
                continue
            except Exception as parse_error:
                # Log but don't fail on individual line parse errors
                print(f"Warning: Failed to parse frontmatter line {line_num}: {original_line}", file=sys.stderr)
                continue

        # Handle nested 'verification' object (simplified nested parser)
        # Look for patterns like:
        # verification:
        #   test_script: "path/to/test.py"
        #   command: "pytest ..."
        if 'verification' in metadata and isinstance(metadata['verification'], dict):
            # Already parsed as dict (shouldn't happen with our current parser)
            pass
        else:
            # Try to extract verification sub-fields
            verification_data = {}
            lines = frontmatter_text.split('\n')
            in_verification = False

            for i, line in enumerate(lines):
                stripped = line.strip()
                if stripped.startswith('verification:'):
                    in_verification = True
                    continue

                if in_verification:
                    # Check if still indented (part of verification block)
                    if line.startswith('  ') or line.startswith('\t'):
                        # Parse sub-field
                        if ':' in stripped:
                            sub_key, sub_value = stripped.split(':', 1)
                            sub_key = sub_key.strip()
                            sub_value = sub_value.strip()
                            # Remove quotes
                            if (sub_value.startswith('"') and sub_value.endswith('"')) or \
                               (sub_value.startswith("'") and sub_value.endswith("'")):
                                sub_value = sub_value[1:-1]
                            verification_data[sub_key] = sub_value
                    else:
                        # No longer indented, end of verification block
                        in_verification = False

            if verification_data:
                metadata['verification'] = verification_data

        return metadata, body

    except Exception as e:
        # Catastrophic failure - return empty metadata
        print(f"Warning: Failed to extract frontmatter: {e}", file=sys.stderr)
        return {}, content


def update_last_verified_in_frontmatter(file_path: Path, new_date: str) -> bool:
    """Update the last_verified field in the skill's frontmatter.

    This provides automatic proof-of-correctness updates when tests pass.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Parse frontmatter
        if not content.startswith('---'):
            print(f"⚠️  No frontmatter in {file_path}")
            return False

        parts = content.split('---', 2)
        if len(parts) < 3:
            return False

        frontmatter_text = parts[1]
        body = parts[2]

        # Update last_verified field
        # Match: last_verified: "2025-12-31" or last_verified: 2025-12-31
        pattern = r'(last_verified:\s*)["\']?\d{4}-\d{2}-\d{2}["\']?'
        replacement = f'\\1"{new_date}"'

        updated_frontmatter = re.sub(pattern, replacement, frontmatter_text)

        # If field didn't exist, add it after version field
        if 'last_verified:' not in frontmatter_text:
            # Find version field and add last_verified after it
            version_pattern = r'(version:\s*[^\n]+\n)'
            if re.search(version_pattern, updated_frontmatter):
                updated_frontmatter = re.sub(
                    version_pattern,
                    f'\\1last_verified: "{new_date}"\n',
                    updated_frontmatter
                )
            else:
                # Just append to end of frontmatter
                updated_frontmatter += f'\nlast_verified: "{new_date}"\n'

        # Reconstruct file
        new_content = f"---{updated_frontmatter}---{body}"

        # Write back
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)

        return True

    except Exception as e:
        print(f"❌ Failed to update {file_path}: {e}", file=sys.stderr)
        return False


def find_all_skills() -> List[Path]:
    """Find all SKILL.md files in the repository."""
    skills = []

    if not SKILLS_BASE_PATH.exists():
        return skills

    for root, dirs, files in os.walk(SKILLS_BASE_PATH):
        if 'SKILL.md' in files:
            skills.append(Path(root) / 'SKILL.md')

    return skills


def load_skill_verification_config(skill_path: Path) -> Tuple[str, Optional[str], Optional[str], Optional[str]]:
    """Load verification configuration from skill frontmatter.

    Returns:
        (skill_name, test_script, test_command, last_verified)
    """
    try:
        with open(skill_path, 'r', encoding='utf-8') as f:
            content = f.read()

        metadata, _ = extract_frontmatter(content)

        skill_name = metadata.get('name', skill_path.parent.name)
        last_verified = metadata.get('last_verified', None)

        # Extract verification config
        verification = metadata.get('verification', {})
        if isinstance(verification, dict):
            test_script = verification.get('test_script', None)
            test_command = verification.get('command', None)
        else:
            test_script = None
            test_command = None

        return skill_name, test_script, test_command, last_verified

    except Exception as e:
        print(f"⚠️  Failed to load {skill_path}: {e}", file=sys.stderr)
        return skill_path.parent.name, None, None, None


def run_verification_test(test_command: str, timeout: int = VERIFICATION_TIMEOUT) -> Tuple[bool, str, float]:
    """Run a verification test command.

    Returns:
        (success, output, execution_time)
    """
    import time

    start_time = time.time()

    try:
        result = subprocess.run(
            test_command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=Path.cwd()
        )

        execution_time = time.time() - start_time

        # Test passes if exit code is 0
        success = result.returncode == 0
        output = result.stdout + result.stderr

        return success, output, execution_time

    except subprocess.TimeoutExpired:
        execution_time = time.time() - start_time
        return False, f"Test timed out after {timeout}s", execution_time
    except Exception as e:
        execution_time = time.time() - start_time
        return False, f"Test execution failed: {e}", execution_time


def verify_skill(skill_path: Path, update_dates: bool = False) -> VerificationResult:
    """Verify a single skill by running its verification test."""
    skill_name, test_script, test_command, last_verified = load_skill_verification_config(skill_path)

    result = VerificationResult(skill_path, skill_name)
    result.last_verified = last_verified

    # Check if verification is defined
    if not test_command and not test_script:
        result.mark_no_verification()
        return result

    result.has_verification = True
    result.test_command = test_command
    result.test_script = test_script

    # Determine command to run
    if test_command:
        cmd = test_command
    elif test_script:
        # Infer command from script extension
        if test_script.endswith('.py'):
            cmd = f"python3 {test_script}"
        elif test_script.endswith('.sh'):
            cmd = f"bash {test_script}"
        else:
            cmd = test_script
    else:
        result.mark_test_failed("No test command or script defined", 0.0)
        return result

    # Run the test
    success, output, execution_time = run_verification_test(cmd)

    if success:
        result.mark_test_passed(output, execution_time)

        # Auto-update last_verified if requested
        if update_dates:
            today = date.today().isoformat()
            if update_last_verified_in_frontmatter(skill_path, today):
                result.last_verified = today
    else:
        result.mark_test_failed(output, execution_time)

    return result


def generate_verification_report(results: List[VerificationResult], output_path: Optional[Path] = None):
    """Generate a verification report in JSON format."""
    report = {
        "timestamp": datetime.now().isoformat(),
        "summary": {
            "total_skills": len(results),
            "verified": sum(1 for r in results if r.test_passed),
            "failed": sum(1 for r in results if r.test_passed is False),
            "no_verification": sum(1 for r in results if not r.has_verification),
        },
        "skills": []
    }

    for result in results:
        skill_data = {
            "name": result.skill_name,
            "path": str(result.skill_path.relative_to(Path.cwd())),
            "has_verification": result.has_verification,
            "test_passed": result.test_passed,
            "last_verified": result.last_verified,
            "execution_time": result.execution_time,
        }

        if result.has_verification:
            skill_data["test_command"] = result.test_command
            if result.test_passed:
                skill_data["output"] = result.test_output
            else:
                skill_data["error"] = result.test_error

        report["skills"].append(skill_data)

    # Write report
    if output_path:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
        print(f"\n📊 Report saved to {output_path}")

    return report


def print_results(results: List[VerificationResult], verbose: bool = False):
    """Print verification results in human-readable format."""
    print("\n" + "=" * 80)
    print("🧪 SKILL VERIFICATION RESULTS")
    print("=" * 80)

    # Group by status
    passed = [r for r in results if r.test_passed]
    failed = [r for r in results if r.test_passed is False]
    no_test = [r for r in results if not r.has_verification]

    # Print passed skills
    if passed:
        print(f"\n✅ VERIFIED ({len(passed)} skills):")
        for result in passed:
            print(f"  {result}")
            if verbose and result.test_output:
                print(f"     Output: {result.test_output[:100]}...")

    # Print failed skills
    if failed:
        print(f"\n❌ FAILED ({len(failed)} skills):")
        for result in failed:
            print(f"  {result}")
            if result.test_error:
                print(f"     Error: {result.test_error[:200]}...")

    # Print skills without verification
    if no_test:
        print(f"\n⚠️  NO VERIFICATION ({len(no_test)} skills):")
        for result in no_test:
            print(f"  ⚠️  [{result.skill_name}] No verification test defined")

    # Summary statistics
    print("\n" + "=" * 80)
    print("📊 SUMMARY")
    print("=" * 80)
    total = len(results)
    print(f"Total skills:        {total}")
    print(f"✅ Verified:          {len(passed)}")
    print(f"❌ Failed:            {len(failed)}")
    print(f"⚠️  No verification:  {len(no_test)}")

    if total > 0:
        verification_rate = ((len(passed) + len(failed)) / total) * 100
        success_rate = (len(passed) / total) * 100 if total > 0 else 0
        print(f"\nVerification coverage: {verification_rate:.1f}%")
        print(f"Success rate:          {success_rate:.1f}%")

    print("=" * 80)


def main():
    parser = argparse.ArgumentParser(
        description='Execute verification tests for skills to prevent Context Rot'
    )
    parser.add_argument(
        '--skill',
        type=str,
        help='Verify specific skill by name (e.g., "git-commit-standards")'
    )
    parser.add_argument(
        '--update-dates',
        action='store_true',
        help='Auto-update last_verified dates when tests pass'
    )
    parser.add_argument(
        '--strict',
        action='store_true',
        help='Fail if ANY skill lacks verification or fails test'
    )
    parser.add_argument(
        '--report',
        type=str,
        help='Generate JSON report at specified path (e.g., "verification-report.json")'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Show detailed test output'
    )

    args = parser.parse_args()

    # Find skills to verify
    if args.skill:
        skill_path = SKILLS_BASE_PATH / args.skill / 'SKILL.md'
        if not skill_path.exists():
            print(f"❌ Skill not found: {args.skill}")
            print(f"   Expected path: {skill_path}")
            sys.exit(1)
        skills = [skill_path]
    else:
        skills = find_all_skills()

    if not skills:
        print("⚠️  No SKILL.md files found in .claude/skills/")
        sys.exit(0)

    print(f"🧪 Verifying {len(skills)} skill(s)...")
    if args.update_dates:
        print("   Auto-update mode: Will update last_verified on success")

    # Verify all skills
    results = []
    for skill_path in skills:
        result = verify_skill(skill_path, update_dates=args.update_dates)
        results.append(result)

    # Print results
    print_results(results, verbose=args.verbose)

    # Generate report if requested
    if args.report:
        generate_verification_report(results, Path(args.report))

    # Determine exit code
    has_failures = any(r.test_passed is False for r in results)
    has_missing = any(not r.has_verification for r in results)

    if args.strict and (has_failures or has_missing):
        print("\n❌ Verification failed in strict mode")
        if has_failures:
            print("   Some tests failed")
        if has_missing:
            print("   Some skills lack verification tests")
        sys.exit(1)
    elif has_failures:
        print("\n⚠️  Some verifications failed. Review errors above.")
        sys.exit(1)
    else:
        print("\n✅ All skill verifications passed!")
        sys.exit(0)


if __name__ == '__main__':
    main()
