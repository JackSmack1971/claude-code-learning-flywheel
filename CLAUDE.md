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

---

## 8. Automated Retrospective System (The Learning Flywheel Engine)

**Problem:** Manual retrospectives create friction in the learning loop. Insights get lost or inconsistently applied.

**Solution:** Automated retrospective merger (`scripts/auto_retro.py`) transforms agent reflections into institutional memory through structured JSON input.

### Architecture

The auto-retrospective system closes the learning loop:

1. **Agent Fails** → Encounters edge case or anti-pattern
2. **Agent Reflects** → Generates structured JSON with failure analysis
3. **Engine Executes** → `auto_retro.py` surgically updates SKILL.md
4. **System Improves** → Next session loads enhanced skill with new negative knowledge

### JSON Schema

When generating retrospective insights, use this exact format:

```json
{
  "target_skill": ".claude/skills/[skill-name]/SKILL.md",
  "version_bump": "patch",
  "negative_knowledge": [
    {
      "attempt": "Description of what was tried",
      "failure": "What went wrong (error message or symptom)",
      "cost": "Impact (tokens/time/production issues)",
      "fix": "Correct approach or prevention strategy"
    }
  ]
}
```

**Field Specifications:**
- `target_skill` (required): Absolute or relative path to SKILL.md file
- `version_bump` (optional): Type of version increment (`major`, `minor`, `patch`). Default: `patch`
- `negative_knowledge` (required): Array of failure entries to append

### Usage

**Basic Usage:**
```bash
# From JSON file
python scripts/auto_retro.py --input insights.json

# From stdin (pipe)
cat insights.json | python scripts/auto_retro.py

# Dry run (preview changes)
python scripts/auto_retro.py --input insights.json --dry-run
```

**What it Does:**
1. Parses skill frontmatter using hardened `yaml_parser.py`
2. Auto-bumps semantic version (e.g., `1.2.0` → `1.2.1`)
3. Updates `last_verified` to current date
4. Locates Negative Knowledge table in skill body
5. Surgically inserts new failure rows (preserves existing content)
6. Reconstructs file with atomic backup/restore on errors

### Integration with Agent Workflow

**Step 1: Detect Failure**
When you encounter an error or discover an anti-pattern:
```bash
# Document the failure context in your working memory
```

**Step 2: Generate Retrospective JSON**
Create structured insights:
```json
{
  "target_skill": ".claude/skills/git-commit-standards/SKILL.md",
  "negative_knowledge": [
    {
      "attempt": "Used grep -r to find commit validation logic",
      "failure": "Returned 500+ false positives from node_modules",
      "cost": "15k tokens wasted",
      "fix": "Use cclsp definition <symbol> for precise lookups"
    }
  ]
}
```

**Step 3: Execute Merge**
```bash
# Save JSON to temporary file
echo '<json>' > /tmp/retro.json

# Merge into skill
python scripts/auto_retro.py --input /tmp/retro.json

# Verify changes
git diff .claude/skills/git-commit-standards/SKILL.md
```

**Step 4: Commit Updates**
```bash
# Commit the enhanced skill
git add .claude/skills/git-commit-standards/SKILL.md
git commit -m "feat(memory): add negative knowledge from retrospective"
```

### Example: Full Workflow

```bash
# 1. Agent discovers that inline Python code is fragile
# 2. Generate retrospective JSON
cat > /tmp/retro.json <<'EOF'
{
  "target_skill": ".claude/skills/test-driven-workflow/SKILL.md",
  "negative_knowledge": [
    {
      "attempt": "Wrote test assertions directly in chat using Python REPL",
      "failure": "Code was lost when session ended, no persistence",
      "cost": "30 minutes of work discarded, had to rewrite tests",
      "fix": "Always write tests to files first (Zero-Context Script pattern)"
    }
  ]
}
EOF

# 3. Merge retrospective
python scripts/auto_retro.py --input /tmp/retro.json

# Output:
# 📈 Version: 2.1.0 → 2.1.1
# 📅 Last verified: 2026-01-01
# ✅ Added 1 failure mode(s) to existing table
# 💾 Saved updates to .claude/skills/test-driven-workflow/SKILL.md

# 4. Verify and commit
git diff .claude/skills/test-driven-workflow/SKILL.md
git add .claude/skills/test-driven-workflow/SKILL.md
git commit -m "feat(tdd): add negative knowledge about REPL fragility"
```

### Safety Features

**Atomic Operations:**
- Creates `.md.bak` backup before writing
- Restores backup automatically if write fails
- Fails fast on YAML parsing errors

**Validation:**
- Uses hardened `yaml_parser.py` (state-machine, handles edge cases)
- Validates JSON schema before processing
- Checks that target skill file exists

**Governance:**
- Auto-bumps semantic version (prevents version conflicts)
- Updates `last_verified` timestamp (proves freshness)
- Preserves frontmatter structure and comments

### When to Use This Tool

**✅ Use auto_retro.py when:**
- You discover a new anti-pattern or failure mode
- A task fails due to incorrect assumptions
- You want to document "what NOT to do"
- Updating negative knowledge in multiple skills

**❌ Don't use for:**
- Adding new features to skills (edit manually)
- Restructuring skill content (use Edit tool)
- Changing frontmatter fields other than version/last_verified

### Metrics & Success Indicators

**How to measure if the flywheel is working:**

- **Failure Reduction:** Same mistake never happens twice (check git history)
- **Knowledge Density:** Negative knowledge tables grow over time
- **Query Success Rate:** `grep` searches in skills find relevant anti-patterns
- **Time to Resolution:** Faster debugging due to documented failure modes

**When to update this system:**
- When YAML frontmatter schema changes (update dumper)
- When table format conventions evolve (update regex patterns)
- When JSON schema needs new fields (document in this section)
