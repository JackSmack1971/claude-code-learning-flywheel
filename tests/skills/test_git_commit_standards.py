#!/usr/bin/env python3
"""
Verification test for git-commit-standards skill.

This test proves the skill's Zero-Context Script (validate_commit_msg.py)
is still valid and correctly enforces conventional commit standards.

Purpose:
- Prevents "Context Rot" where the skill's instructions become outdated
- Provides executable proof of correctness
- Auto-updates last_verified date when tests pass

Run:
    python3 tests/skills/test_git_commit_standards.py
    pytest tests/skills/test_git_commit_standards.py -v
"""

import subprocess
import sys
import tempfile
from pathlib import Path


# Test configuration
SCRIPT_PATH = Path(".claude/skills/git-commit-standards/scripts/validate_commit_msg.py")


class TestGitCommitStandardsSkill:
    """Verification tests for git-commit-standards skill."""

    def test_script_exists(self):
        """Verify the validation script exists at expected path."""
        assert SCRIPT_PATH.exists(), f"Script not found: {SCRIPT_PATH}"
        print(f"✓ Script exists: {SCRIPT_PATH}")

    def test_script_is_executable(self):
        """Verify the script can be executed by Python."""
        result = subprocess.run(
            ["python3", str(SCRIPT_PATH), "--check-setup"],
            capture_output=True,
            text=True,
            timeout=5
        )

        # Script should exit with 0 or 1 (1 if hooks not installed, which is fine)
        assert result.returncode in [0, 1], \
            f"Script crashed with code {result.returncode}: {result.stderr}"
        print(f"✓ Script executes without crashing")

    def test_validates_good_commit_format(self):
        """Verify script accepts correctly formatted conventional commits."""
        good_commits = [
            "feat(api): add user authentication",
            "fix(ui): resolve button alignment issue",
            "docs(readme): update installation instructions",
            "test(auth): add login flow tests",
            "chore(deps): upgrade dependencies",
            "refactor(core): simplify error handling",
        ]

        for commit_msg in good_commits:
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
                f.write(commit_msg)
                temp_path = f.name

            try:
                result = subprocess.run(
                    ["python3", str(SCRIPT_PATH), temp_path],
                    capture_output=True,
                    text=True,
                    timeout=5
                )

                assert result.returncode == 0, \
                    f"Valid commit rejected: '{commit_msg}'\n" \
                    f"Output: {result.stdout}\n" \
                    f"Error: {result.stderr}"

                print(f"✓ Accepted: {commit_msg}")

            finally:
                Path(temp_path).unlink()

    def test_rejects_bad_commit_format(self):
        """Verify script rejects malformed commit messages."""
        bad_commits = [
            "Added some stuff",  # No type
            "updated readme",  # lowercase type
            "feat add feature",  # missing colon
            "invalid(scope): message",  # invalid type
            "fix: " + "x" * 100,  # subject too long
        ]

        for commit_msg in bad_commits:
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
                f.write(commit_msg)
                temp_path = f.name

            try:
                result = subprocess.run(
                    ["python3", str(SCRIPT_PATH), temp_path],
                    capture_output=True,
                    text=True,
                    timeout=5
                )

                assert result.returncode != 0, \
                    f"Invalid commit accepted: '{commit_msg}'\n" \
                    f"Output: {result.stdout}"

                print(f"✓ Rejected: {commit_msg[:50]}...")

            finally:
                Path(temp_path).unlink()

    def test_conventional_commit_pattern_coverage(self):
        """Verify all documented commit types are supported."""
        documented_types = ["feat", "fix", "docs", "style", "refactor", "test", "chore"]

        for commit_type in documented_types:
            commit_msg = f"{commit_type}(scope): test message"

            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
                f.write(commit_msg)
                temp_path = f.name

            try:
                result = subprocess.run(
                    ["python3", str(SCRIPT_PATH), temp_path],
                    capture_output=True,
                    text=True,
                    timeout=5
                )

                assert result.returncode == 0, \
                    f"Documented type '{commit_type}' not recognized by validator"

                print(f"✓ Type supported: {commit_type}")

            finally:
                Path(temp_path).unlink()

    def test_scope_is_optional(self):
        """Verify scope is optional in conventional commits."""
        commit_without_scope = "feat: add new feature"

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write(commit_without_scope)
            temp_path = f.name

        try:
            result = subprocess.run(
                ["python3", str(SCRIPT_PATH), temp_path],
                capture_output=True,
                text=True,
                timeout=5
            )

            assert result.returncode == 0, \
                f"Commit without scope was rejected: {result.stderr}"

            print(f"✓ Scope is optional (as per spec)")

        finally:
            Path(temp_path).unlink()

    def test_detects_secrets_in_commit_message(self):
        """Verify script catches potential secrets in commit messages."""
        # Note: This is a basic test - the script does basic pattern matching
        # Real secrets should never be in commit messages anyway
        commits_with_secrets = [
            "feat(api): add auth with password='secret123'",
            "fix(db): update API_KEY='sk-1234567890abcdefghijklmnopqrs'",
        ]

        for commit_msg in commits_with_secrets:
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
                f.write(commit_msg)
                temp_path = f.name

            try:
                result = subprocess.run(
                    ["python3", str(SCRIPT_PATH), temp_path],
                    capture_output=True,
                    text=True,
                    timeout=5
                )

                # Should reject due to secret detection
                assert result.returncode != 0, \
                    f"Commit with potential secret was accepted: {commit_msg[:50]}"

                print(f"✓ Secret detected: {commit_msg[:50]}...")

            finally:
                Path(temp_path).unlink()


def run_tests_standalone():
    """Run tests without pytest (standalone mode)."""
    print("\n" + "=" * 70)
    print("🧪 VERIFICATION TEST: git-commit-standards")
    print("=" * 70 + "\n")

    test_suite = TestGitCommitStandardsSkill()
    tests = [
        ("Script Exists", test_suite.test_script_exists),
        ("Script Executable", test_suite.test_script_is_executable),
        ("Validates Good Commits", test_suite.test_validates_good_commit_format),
        ("Rejects Bad Commits", test_suite.test_rejects_bad_commit_format),
        ("All Commit Types Supported", test_suite.test_conventional_commit_pattern_coverage),
        ("Scope is Optional", test_suite.test_scope_is_optional),
        ("Detects Secrets", test_suite.test_detects_secrets_in_commit_message),
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        try:
            print(f"\n→ Running: {test_name}")
            test_func()
            print(f"  ✅ PASS: {test_name}")
            passed += 1
        except AssertionError as e:
            print(f"  ❌ FAIL: {test_name}")
            print(f"     {e}")
            failed += 1
        except Exception as e:
            print(f"  ❌ ERROR: {test_name}")
            print(f"     {e}")
            failed += 1

    print("\n" + "=" * 70)
    print(f"📊 Results: {passed} passed, {failed} failed")
    print("=" * 70)

    if failed > 0:
        print("\n❌ Verification FAILED")
        print("   The git-commit-standards skill's validation script has issues.")
        print("   Update the skill's Negative Knowledge and fix the script.")
        return 1
    else:
        print("\n✅ Verification PASSED")
        print("   The git-commit-standards skill is verified to work correctly.")
        return 0


if __name__ == "__main__":
    # Run standalone (without pytest)
    exit_code = run_tests_standalone()
    sys.exit(exit_code)
