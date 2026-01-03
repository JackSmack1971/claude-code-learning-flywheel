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

# Import robust YAML parser
from yaml_parser import extract_frontmatter


# Configuration
SKILLS_BASE_PATH = Path('.claude/skills')
TESTS_BASE_PATH = Path('tests/skills')
VERIFICATION_TIMEOUT = 60  # seconds per test


class VerificationResult:
    """Container for skill verification results.
    
    Stores the outcome of an executable verification test, including output,
    execution time, and whether the test was successful.
    
    Attributes:
        skill_path: Path to the validated skill file.
        skill_name: Name of the skill.
        has_verification: Whether a verification test is defined for this skill.
        test_command: The command executed for verification.
        test_script: The test script file path.
        test_passed: True if the test passed, False if it failed, None if no test.
        test_output: Combined stdout and stderr from the test run.
        test_error: Error message if the test failed.
        last_verified: The date of the last successful verification.
        execution_time: Duration of the test run in seconds.
    """

    def __init__(self, skill_path: Path, skill_name: str):
        """Initializes the verification result container.
        
        Args:
            skill_path: Absolute or relative path to the skill.
            skill_name: Display name for the skill.
        """
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
        """Mark the verification test as passed.
        
        Args:
            output: The combined output string from the test.
            execution_time: Time taken in seconds.
        """
        self.test_passed = True
        self.test_output = output
        self.execution_time = execution_time

    def mark_test_failed(self, error: str, execution_time: float):
        """Mark the verification test as failed.
        
        Args:
            error: The error message or output captured.
            execution_time: Time taken in seconds.
        """
        self.test_passed = False
        self.test_error = error
        self.execution_time = execution_time

    def __str__(self):
        """Returns a formatted status string for console output."""
        status_icon = "✅" if self.test_passed else "❌" if self.test_passed is False else "⚠️"
        status = "PASS" if self.test_passed else "FAIL" if self.test_passed is False else "NO-TEST"
        return f"{status_icon} [{status}] {self.skill_name} ({self.execution_time:.2f}s)"


def safe_relative_path(path: Path, base: Optional[Path] = None) -> str:
    """Safely compute relative path, falling back to absolute if needed.

    Args:
        path: Path to convert to relative.
        base: Base directory. Defaults to current working directory.
        
    Returns:
        str: Relative path if possible, otherwise absolute path.
    """
    try:
        # Resolve both paths to absolute
        abs_path = path.resolve()
        abs_base = (base or Path.cwd()).resolve()

        # Try to compute relative path
        return str(abs_path.relative_to(abs_base))
    except ValueError:
        # Paths don't share common ancestor - use absolute path
        return str(path.resolve())


def update_last_verified_in_frontmatter(file_path: Path, new_date: str) -> bool:
    """Update the last_verified field in the skill's frontmatter.

    Args:
        file_path: Path to the skill file to update.
        new_date: ISO-formatted date string (e.g., "2026-01-01").

    Returns:
        bool: True if successful, False otherwise.
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
    """Find all SKILL.md files in the repository.
    
    Returns:
        List[Path]: A list of paths to all discovered SKILL.md files.
    """
    skills = []

    if not SKILLS_BASE_PATH.exists():
        return skills

    for root, dirs, files in os.walk(SKILLS_BASE_PATH):
        if 'SKILL.md' in files:
            skills.append(Path(root) / 'SKILL.md')

    return skills


def load_skill_verification_config(skill_path: Path) -> Tuple[str, Optional[str], Optional[str], Optional[str]]:
    """Load verification configuration from skill frontmatter.

    Args:
        skill_path: Path to the skill file.

    Returns:
        Tuple[str, Optional[str], Optional[str], Optional[str]]: A tuple containing:
            - skill_name: The name of the skill.
            - test_script: Path to the test script (if defined).
            - test_command: The raw test command (if defined).
            - last_verified: The last verification date.
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

    Args:
        test_command: The shell command to execute.
        timeout: Maximum execution time in seconds. Defaults to 60.

    Returns:
        Tuple[bool, str, float]: A tuple of (success, output, execution_time).
            success: True if exit code is 0.
            output: Combined stdout and stderr.
            execution_time: Duration of the test in seconds.
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
    """Verify a single skill by running its verification test.
    
    Args:
        skill_path: Path to the skill file.
        update_dates: If True, update 'last_verified' in frontmatter on success.
        
    Returns:
        VerificationResult: The outcome of the verification.
    """
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
    """Generate a verification report in JSON format.
    
    Args:
        results: List of verification results.
        output_path: Path to save the JSON report.
        
    Returns:
        Dict: The report data.
    """
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
            "path": safe_relative_path(result.skill_path),
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
    """Print verification results in human-readable format.
    
    Args:
        results: List of verification results.
        verbose: If True, print detailed output for each test.
    """
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
