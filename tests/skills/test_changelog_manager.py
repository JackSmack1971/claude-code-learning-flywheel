#!/usr/bin/env python3
"""
Verification tests for changelog-manager skill.

This test suite validates the Zero-Context Script (pr_scanner.sh) to ensure:
1. The script is executable
2. The script accepts --help flag
3. The script returns proper exit codes
4. The script outputs valid markdown structure

Run: python3 tests/skills/test_changelog_manager.py
"""

import subprocess
import sys
import os
from pathlib import Path

# Color codes for output
GREEN = '\033[0;32m'
RED = '\033[0;31m'
YELLOW = '\033[1;33m'
BLUE = '\033[0;34m'
NC = '\033[0m'  # No Color


def log_test(test_name: str):
    """Print test name."""
    print(f"\n{BLUE}[TEST]{NC} {test_name}")


def log_pass(message: str):
    """Print success message."""
    print(f"{GREEN}✅ PASS:{NC} {message}")


def log_fail(message: str):
    """Print failure message."""
    print(f"{RED}❌ FAIL:{NC} {message}")


def log_info(message: str):
    """Print info message."""
    print(f"{YELLOW}[INFO]{NC} {message}")


def test_script_exists() -> bool:
    """Verify the pr_scanner.sh script exists."""
    log_test("Script Existence Check")

    script_path = Path(".claude/skills/changelog-manager/scripts/pr_scanner.sh")

    if not script_path.exists():
        log_fail(f"Script not found at: {script_path}")
        return False

    log_pass(f"Script exists at: {script_path}")
    return True


def test_script_is_executable() -> bool:
    """Verify the pr_scanner.sh script is executable."""
    log_test("Script Executable Check")

    script_path = Path(".claude/skills/changelog-manager/scripts/pr_scanner.sh")

    if not os.access(script_path, os.X_OK):
        log_fail(f"Script is not executable: {script_path}")
        log_info("Fix with: chmod +x .claude/skills/changelog-manager/scripts/pr_scanner.sh")
        return False

    log_pass("Script is executable")
    return True


def test_script_help_flag() -> bool:
    """Verify the script accepts --help flag."""
    log_test("Script --help Flag")

    script_path = ".claude/skills/changelog-manager/scripts/pr_scanner.sh"

    try:
        result = subprocess.run(
            ["bash", script_path, "--help"],
            capture_output=True,
            text=True,
            timeout=5
        )

        # --help should return exit code 0
        if result.returncode != 0:
            log_fail(f"Script returned exit code {result.returncode} for --help")
            return False

        # Should output usage information
        if "Usage:" not in result.stdout and "Usage:" not in result.stderr:
            log_fail("Script --help does not display usage information")
            log_info(f"Output: {result.stdout}")
            return False

        log_pass("Script --help displays usage information")
        return True

    except subprocess.TimeoutExpired:
        log_fail("Script --help timed out (5 seconds)")
        return False
    except Exception as e:
        log_fail(f"Script execution failed: {e}")
        return False


def test_script_runs_in_git_repo() -> bool:
    """Verify the script runs without errors in a git repository."""
    log_test("Script Execution in Git Repo")

    script_path = ".claude/skills/changelog-manager/scripts/pr_scanner.sh"

    # Check if we're in a git repo
    try:
        subprocess.run(
            ["git", "rev-parse", "--git-dir"],
            capture_output=True,
            check=True
        )
    except subprocess.CalledProcessError:
        log_info("Not in a git repository - skipping execution test")
        return True  # Skip test gracefully

    try:
        result = subprocess.run(
            ["bash", script_path, "--verbose"],
            capture_output=True,
            text=True,
            timeout=10
        )

        # Exit codes: 0 (success), 2 (no changes found) are both acceptable
        if result.returncode not in [0, 2]:
            log_fail(f"Script returned unexpected exit code: {result.returncode}")
            log_info(f"Stderr: {result.stderr}")
            return False

        log_pass(f"Script executed successfully (exit code {result.returncode})")
        return True

    except subprocess.TimeoutExpired:
        log_fail("Script execution timed out (10 seconds)")
        return False
    except Exception as e:
        log_fail(f"Script execution failed: {e}")
        return False


def test_output_format() -> bool:
    """Verify the script outputs valid markdown structure."""
    log_test("Output Format Validation")

    script_path = ".claude/skills/changelog-manager/scripts/pr_scanner.sh"

    # Check if we're in a git repo with commits
    try:
        subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            check=True
        )
    except subprocess.CalledProcessError:
        log_info("No git commits - skipping output format test")
        return True  # Skip test gracefully

    try:
        result = subprocess.run(
            ["bash", script_path],
            capture_output=True,
            text=True,
            timeout=10
        )

        # Exit code 2 (no changes) is acceptable - skip format check
        if result.returncode == 2:
            log_info("No changes found - skipping format validation")
            return True

        if result.returncode != 0:
            log_fail(f"Script failed with exit code {result.returncode}")
            return False

        output = result.stdout

        # Validate markdown structure
        validation_checks = [
            ("##" in output, "Has version header (##)"),
            ("###" in output or "No changes" in output, "Has category sections (###) or no changes message"),
        ]

        all_passed = True
        for check, description in validation_checks:
            if check:
                log_pass(description)
            else:
                log_fail(description)
                all_passed = False

        if all_passed:
            log_pass("Output format is valid markdown")
        else:
            log_info(f"Output preview:\n{output[:200]}...")

        return all_passed

    except subprocess.TimeoutExpired:
        log_fail("Script timed out during output validation")
        return False
    except Exception as e:
        log_fail(f"Output validation failed: {e}")
        return False


def test_skill_metadata() -> bool:
    """Verify SKILL.md has required metadata."""
    log_test("Skill Metadata Validation")

    skill_path = Path(".claude/skills/changelog-manager/SKILL.md")

    if not skill_path.exists():
        log_fail(f"SKILL.md not found at: {skill_path}")
        return False

    content = skill_path.read_text()

    # Check for required frontmatter fields
    required_fields = [
        "name:",
        "version:",
        "description:",
        "verification:",
        "allowed_tools:",
    ]

    missing_fields = []
    for field in required_fields:
        if field not in content:
            missing_fields.append(field)

    if missing_fields:
        log_fail(f"Missing required frontmatter fields: {', '.join(missing_fields)}")
        return False

    # Check for Negative Knowledge section
    if "Negative Knowledge" not in content:
        log_fail("Missing 'Negative Knowledge' section")
        return False

    log_pass("SKILL.md has required metadata and sections")
    return True


def main():
    """Run all verification tests."""
    print(f"\n{BLUE}{'='*60}{NC}")
    print(f"{BLUE}Changelog Manager Skill Verification Tests{NC}")
    print(f"{BLUE}{'='*60}{NC}")

    tests = [
        ("Script Existence", test_script_exists),
        ("Script Executable", test_script_is_executable),
        ("Script Help Flag", test_script_help_flag),
        ("Script Execution", test_script_runs_in_git_repo),
        ("Output Format", test_output_format),
        ("Skill Metadata", test_skill_metadata),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            passed = test_func()
            results.append((test_name, passed))
        except Exception as e:
            log_fail(f"Test crashed: {e}")
            results.append((test_name, False))

    # Summary
    print(f"\n{BLUE}{'='*60}{NC}")
    print(f"{BLUE}Test Summary{NC}")
    print(f"{BLUE}{'='*60}{NC}")

    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)

    for test_name, passed in results:
        status = f"{GREEN}✅ PASS{NC}" if passed else f"{RED}❌ FAIL{NC}"
        print(f"{status}: {test_name}")

    print(f"\n{BLUE}Results:{NC} {passed_count}/{total_count} tests passed")

    if passed_count == total_count:
        print(f"{GREEN}✅ ALL TESTS PASSED{NC}")
        return 0
    else:
        print(f"{RED}❌ SOME TESTS FAILED{NC}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
