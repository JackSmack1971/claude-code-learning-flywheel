# Skill Verification Tests

This directory contains executable verification tests for skills in `.claude/skills/`.

## Purpose

These tests solve the **"Context Rot"** problem by providing proof that skill procedures
and Zero-Context Scripts are still valid and haven't been broken by:

- Dependency version changes
- Library API changes
- Environment configuration drift
- Tool updates

## Architecture

**Static Validation** (scripts/validate_memory.py):
- Checks formatting, token budgets, negative knowledge presence
- Validates metadata and structure
- **Does NOT prove correctness**

**Dynamic Verification** (this directory):
- Executes skill scripts to prove they work
- Tests validation logic with real inputs
- Auto-updates `last_verified` dates on success
- **Proves correctness through execution**

## Test Structure

Each skill verification test should:

1. **Test Script Executability**: Verify the skill's Zero-Context Script can run
2. **Test Validation Logic**: Verify the script correctly accepts/rejects inputs
3. **Test Integration**: Verify the skill works in the actual environment

Example:
```python
def test_git_commit_validator_rejects_bad_format():
    """Verify validator catches malformed commit messages."""
    result = subprocess.run(
        ["python3", ".claude/skills/git-commit-standards/scripts/validate_commit_msg.py"],
        input="bad commit message",
        capture_output=True,
        text=True
    )
    assert result.returncode != 0, "Should reject invalid format"
```

## Running Tests

```bash
# Verify all skills
python scripts/verify_skills.py

# Verify specific skill
python scripts/verify_skills.py --skill git-commit-standards

# Auto-update last_verified dates on success
python scripts/verify_skills.py --update-dates

# Generate JSON report
python scripts/verify_skills.py --report verification-report.json

# Strict mode (fail if ANY skill lacks verification)
python scripts/verify_skills.py --strict
```

## When Tests Fail

If a verification test fails:

1. **Update Negative Knowledge**: Add the failure to the skill's Failed Attempts table
2. **Fix the Skill**: Update the Verified Procedure or Zero-Context Script
3. **Bump Version**: Increment skill version (following semver)
4. **Re-verify**: Run `python scripts/verify_skills.py --skill [name]` to confirm fix

This creates a learning loop where failures strengthen the collective intelligence.

## Integration with CI

See `.github/workflows/validate-memory.yml` for automated verification:

- Runs on every push to skill files
- Fails PR if verification tests fail
- Comments on PR with verification report
- Prevents broken skills from entering main branch

## Metrics

The verification framework tracks:

- **Verification Coverage**: % of skills with executable tests
- **Success Rate**: % of skills passing verification
- **Staleness**: Days since last verification (auto-updated on test pass)
- **Execution Time**: How long each verification takes

These metrics prove the ROI of "Knowledge as Infrastructure."
