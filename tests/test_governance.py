#!/usr/bin/env python3
"""
Test Pre-Commit Governance Script

Verifies that pre_commit_governance.py correctly identifies violations.
"""
import sys
import subprocess
from pathlib import Path

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from pre_commit_governance import (
    check_skill_file,
    GovernanceViolation
)


def test_valid_skill():
    """Test that valid skill file passes all checks."""
    fixture_path = Path(__file__).parent / "fixtures/governance/valid_skill.md"
    content = fixture_path.read_text()

    violations = check_skill_file(str(fixture_path), content)

    # Should have no ERROR violations
    errors = [v for v in violations if v.severity == "ERROR"]

    if errors:
        print("❌ Valid skill should not have errors:")
        for v in errors:
            print(f"  - {v.rule}: {v.message}")
        return False

    print("✅ Valid skill passed all checks")
    return True


def test_invalid_skill():
    """Test that invalid skill file is caught."""
    fixture_path = Path(__file__).parent / "fixtures/governance/invalid_skill.md"
    content = fixture_path.read_text()

    violations = check_skill_file(str(fixture_path), content)

    expected_violations = {
        "LSP-First Navigation",  # Too much grep, no LSP
        "Negative Knowledge Required",  # No failure documentation
        "Zero-Context Script Required"  # Code block >50 lines
    }

    found_rules = {v.rule for v in violations if v.severity == "ERROR"}

    missing = expected_violations - found_rules
    if missing:
        print(f"❌ Invalid skill should trigger: {missing}")
        print(f"   Found violations: {found_rules}")
        return False

    print(f"✅ Invalid skill caught {len(violations)} violation(s):")
    for v in violations:
        print(f"  - {v.rule}")
    return True


def test_script_execution():
    """Test that governance script runs without errors."""
    script_path = Path(__file__).parent.parent / "scripts/pre_commit_governance.py"

    # Test with --help (should exit 0)
    result = subprocess.run(
        ["python3", str(script_path)],
        capture_output=True,
        text=True
    )

    # Script should run without crashing (exit 0 or 1, not 2)
    if result.returncode == 2:
        print(f"❌ Script crashed: {result.stderr}")
        return False

    print(f"✅ Script executed successfully (exit {result.returncode})")
    return True


def main():
    """Run all tests."""
    print("🧪 Testing Pre-Commit Governance\n")

    tests = [
        ("Valid Skill Detection", test_valid_skill),
        ("Invalid Skill Detection", test_invalid_skill),
        ("Script Execution", test_script_execution)
    ]

    results = []
    for name, test_func in tests:
        print(f"\n{'='*60}")
        print(f"Test: {name}")
        print('='*60)
        try:
            passed = test_func()
            results.append((name, passed))
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            results.append((name, False))

    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print('='*60)

    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)

    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {name}")

    print(f"\n{passed_count}/{total_count} tests passed")

    return 0 if passed_count == total_count else 1


if __name__ == "__main__":
    sys.exit(main())
