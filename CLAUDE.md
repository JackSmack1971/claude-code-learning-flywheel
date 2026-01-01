# Project Memory: Claude Code Learning Flywheel

## 1. The WHAT (Architecture Map)
- **Core:** Python-based scaffold for self-improving agentic workflows.
- **Memory Tier:**
  - **Tier 2 (This file):** Onboarding & Map.
  - **Tier 3 (Project Rules):** `.claude/rules/` (Auto-loaded).
  - **Skills:** `.claude/skills/` (Capability Library).
  - **Tools:** `plugins/` & `scripts/` (Zero-Context Executors).

## 2. The WHY (Directives)
- **Prime Directive:** Prioritize **Negative Knowledge**. Before acting, check `.claude/skills/` for past failure modes.
- **Zero-Context Preference:** Do not write complex logic in chat. Write a script in `scripts/`, verify it, and execute it.
- **LSP Over Grep:** Use `cclsp` (Language Server) to navigate symbols and definitions. Do not read full files to find a function definition.

## 3. The HOW (Workflow Standards)
- **Memory Validation:** Run `python scripts/validate_memory.py` before committing new skills.
- **Skill Verification:** Run `python scripts/verify_skills.py` to prove skills work (prevents Context Rot).
- **Retrospectives:** After every significant task, run `/retrospective` to extract insights into `doc/learnings/`.
- **Commits:** Use `git-commit-standards` skill for all commits.

## 4. Agent Commands
> **Trigger:** Use `/advise` before starting significant refactors or deployments.

**Procedure for `/advise`:**
1. **Scan:** Search `.claude/skills/` and `plugins/` for relevant capabilities.
2. **Verify:** Check "Negative Knowledge" (Failed Attempts) in those skills.
3. **Report:** Summarize verified approaches and specific traps to avoid.
4. **Execute:** Proceed only after confirming the plan avoids documented failures.

## 5. Maintenance & Reflexion
- **After every task:** Run `/retrospective` to extract insights.
- **On failure discovery:** Update the relevant `SKILL.md` immediately with negative knowledge.
- **Token Budget:** All skills MUST stay under 500 lines. Refactor complex logic to `scripts/` or `reference.md`.

## 6. Core Principles
- **Negative Knowledge First:** Check for past failures before attempting complex tasks.
- **Precision and Parsimony:** Minimize token usage through LSP and Zero-Context Scripts.
- **Governance Framework:** All complex logic (>500 lines) MUST use "Zero-Context Scripts" in `scripts/`.
- **Knowledge as Infrastructure:** Skills are verified through executable tests, not just documentation.

---

## 7. Verification Framework (NEW)

**Problem:** Skills decay over time ("Context Rot") when dependencies change but documentation doesn't update.

**Solution:** Executable verification tests prove skills still work.

### Architecture

**Two-Tier Validation:**

1. **Static Validation** (`scripts/validate_memory.py`):
   - Checks formatting, token budgets, negative knowledge presence
   - Validates metadata structure and semantic versioning
   - **Does NOT prove correctness**

2. **Dynamic Verification** (`scripts/verify_skills.py`):
   - Executes skill's Zero-Context Scripts with test inputs
   - Proves validation logic works correctly
   - Auto-updates `last_verified` dates on success
   - **Proves correctness through execution**

### Usage

```bash
# Verify all skills
python scripts/verify_skills.py

# Verify specific skill
python scripts/verify_skills.py --skill git-commit-standards

# Auto-update last_verified on success
python scripts/verify_skills.py --update-dates

# Generate JSON report
python scripts/verify_skills.py --report verification-report.json

# Strict mode (fail if any skill lacks verification)
python scripts/verify_skills.py --strict
```

### Adding Verification to a Skill

1. **Update skill frontmatter** (`.claude/skills/[skill-name]/SKILL.md`):
```yaml
verification:
  test_script: "tests/skills/test_[skill-name].py"
  command: "python3 tests/skills/test_[skill-name].py"
  frequency: "on-change"
```

2. **Create verification test** (`tests/skills/test_[skill-name].py`):
```python
def test_skill_script_is_executable():
    """Verify the skill's Zero-Context Script can run."""
    result = subprocess.run(
        ["python3", ".claude/skills/[skill]/scripts/[script].py", "--help"],
        capture_output=True
    )
    assert result.returncode in [0, 1]

def test_validation_logic():
    """Test that validator accepts good input and rejects bad input."""
    # Test with valid input
    # Test with invalid input
    pass
```

3. **Run verification:**
```bash
python scripts/verify_skills.py --skill [skill-name]
```

### CI Integration

The verification framework runs automatically on every push:
- Verifies all skills with tests
- Comments on PRs with verification report
- Fails CI if verification tests fail
- Tracks verification coverage and success rate

See `.github/workflows/validate-memory.yml` job: `verify-skills`

### Metrics

The framework tracks:
- **Verification Coverage:** % of skills with executable tests
- **Success Rate:** % of skills passing verification
- **Staleness:** Auto-updated `last_verified` dates (proof of freshness)
- **Execution Time:** Performance overhead of verification

This transforms skills from static documentation into **trustworthy, verified infrastructure**.
