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

---

## 9. Pre-Commit Governance Framework (Behavioral Constraints)

**Problem:** Perfect memory without behavioral constraints creates learned helplessness. The Agent might document "don't use grep" but continues using it because there's no enforcement.

**Solution:** Pre-commit hooks that **reject violations** before they enter the codebase.

### The Enforcement Layer

The Learning Flywheel has three tiers:
1. **Memory Engine** (`auto_retro.py`) - Captures failures
2. **Verification Tests** (`verify_skills.py`) - Proves correctness
3. **Governance Hooks** (`pre_commit_governance.py`) - **Prevents violations**

This completes the loop: **Learn → Verify → Enforce → Learn**

### Architecture

**Pre-Commit Governance Hook** (`scripts/pre_commit_governance.py`):
- Runs automatically on `git commit`
- Scans staged files for policy violations
- Blocks commits that violate architectural principles
- Provides actionable fix suggestions

**Enforced Rules:**

| Rule | Violation | Fix |
|------|-----------|-----|
| **LSP-First Navigation** | SKILL.md mentions `grep` for code navigation without LSP alternatives | Add `cclsp definition <symbol>` examples |
| **Negative Knowledge Required** | SKILL.md lacks "Negative Knowledge" or failure documentation table | Add `\| Attempt \| Failure \| Cost \| Fix \|` table |
| **Zero-Context Scripts** | Code blocks >50 lines in SKILL.md | Move to `scripts/` and reference |
| **Verification Metadata** | Skills without `verification:` frontmatter field | Add test_script path in frontmatter |
| **Conventional Commits** | Commit messages don't follow `type(scope): description` | Use `feat\|fix\|docs\|refactor` prefix |

### Installation

**One-Time Setup:**
```bash
# Install the pre-commit hook
bash scripts/install_hooks.sh

# Output:
# ✅ Pre-commit hook installed at .git/hooks/pre-commit
# ✅ Governance script is executable
```

**Manual Installation:**
```bash
# Make script executable
chmod +x scripts/pre_commit_governance.py

# Create symlink (or copy) to .git/hooks/pre-commit
ln -s ../../scripts/pre_commit_governance.py .git/hooks/pre-commit
```

### Usage

**Automatic (on every commit):**
```bash
# Make changes to a SKILL.md file
git add .claude/skills/example/SKILL.md

# Attempt commit - hook runs automatically
git commit -m "Update skill"

# If violations detected:
# ❌ COMMIT BLOCKED - Governance Violations Detected
#
# ❌ .claude/skills/example/SKILL.md
#    Rule: LSP-First Navigation
#    Issue: Found 5 grep mentions but 0 LSP references...
```

**Manual (test before committing):**
```bash
# Run governance checks on current working directory
python scripts/pre_commit_governance.py

# Exit codes:
#   0 = All checks passed
#   1 = Policy violations found
#   2 = Script error (fail-open for safety)
```

**Bypass Hook (not recommended):**
```bash
# Only use when governance script is broken, not to skip fixes
git commit --no-verify -m "Emergency hotfix"
```

### Example: Violation Detection

**Scenario:** You update a skill with grep-heavy examples.

```markdown
<!-- .claude/skills/code-search/SKILL.md -->
## Usage

Find function definitions:
```bash
grep -r "function myFunc" .
grep -r "class MyClass" src/
```

**Hook Output:**
```
🔍 Governance Check: 1 staged file(s)...

======================================================================
🛡️  GOVERNANCE REPORT
======================================================================

❌ BLOCKING ERRORS (2):

❌ .claude/skills/code-search/SKILL.md
   Rule: LSP-First Navigation
   Issue: Found 5 grep mentions for code navigation but only 0 LSP references.
          Use 'cclsp' for symbol lookup.
          Examples: 'cclsp definition <symbol>', 'cclsp references <symbol>'

❌ .claude/skills/code-search/SKILL.md
   Rule: Negative Knowledge Required
   Issue: SKILL.md must document failure modes. Add a table with:
          | Attempt | Failure | Cost | Fix |
          See CLAUDE.md section 6 for details.

======================================================================
📚 Review: CLAUDE.md § 6 (Core Principles)
🔧 Tools: Use 'cclsp' for navigation, scripts/ for logic
🧠 Memory: Document failures in Negative Knowledge tables
======================================================================

🚫 COMMIT BLOCKED - Fix errors above to proceed
```

**After Fixing:**
```markdown
<!-- .claude/skills/code-search/SKILL.md -->
## Usage

Find function definitions using LSP:
```bash
# Semantic search (precise, fast)
cclsp definition myFunc

# Find all references
cclsp references MyClass
```

For content search (non-code), grep is acceptable:
```bash
grep -r "TODO" docs/
```

## Negative Knowledge

| Attempt | Failure | Cost | Fix |
|---------|---------|------|-----|
| Used `grep -r` to find class definitions | 500+ false positives in node_modules | 15k tokens | Use `cclsp definition ClassName` |
```

**Hook Output:**
```
✅ All governance checks passed - commit approved
```

### CI/CD Integration

The governance framework runs in GitHub Actions on every PR:

**Workflow:** `.github/workflows/validate-memory.yml`

**Job:** `governance-enforcement`

**What it does:**
- Runs `pre_commit_governance.py` on all changed files
- Comments on PRs with violation reports
- Fails CI if blocking errors found (prevents merge)
- Allows warnings (soft enforcement)

**PR Comment Example:**
```markdown
### 🛡️ Governance Check Report

❌ **POLICY VIOLATIONS DETECTED**

**Governance Rules:**
- ✅ LSP-First: Use `cclsp` for code navigation, not `grep`
- ✅ Zero-Context: Move code >50 lines to `scripts/`
- ✅ Negative Knowledge: Document failure modes in skills
- ✅ Verification: Add executable tests to skills

See `CLAUDE.md § 6` for architectural principles.
```

### Testing the Framework

**Test Suite:** `tests/test_governance.py`

```bash
# Run all governance tests
python tests/test_governance.py

# Output:
# ✅ PASS: Valid Skill Detection
# ✅ PASS: Invalid Skill Detection
# ✅ PASS: Script Execution
# 3/3 tests passed
```

**Test Fixtures:**
- `tests/fixtures/governance/valid_skill.md` - Passes all checks
- `tests/fixtures/governance/invalid_skill.md` - Violates multiple rules

### Customization

**Adjust Thresholds** (`scripts/pre_commit_governance.py`):
```python
MAX_GREP_MENTIONS = 2        # Allow minimal grep for content search
REQUIRED_LSP_MENTIONS = 1    # Minimum LSP references in skills
MAX_INLINE_CODE_LINES = 50   # Code blocks larger → move to scripts/
```

**Add New Rules:**
1. Define violation in `check_skill_file()` function
2. Add test case in `tests/test_governance.py`
3. Update `CLAUDE.md` documentation
4. Run `python tests/test_governance.py` to verify

### Why This Matters

**Without Governance:**
- Agent reads "don't use grep" in SKILL.md
- Agent uses grep anyway (no cost for violating principle)
- Skill gets updated with more "don't use grep" advice
- Cycle repeats (learned helplessness)

**With Governance:**
- Agent attempts to commit skill with grep examples
- Hook blocks commit with actionable error
- Agent fixes violation (uses LSP examples)
- Correct pattern enters codebase
- **System improves through enforcement**

### Metrics & Success Indicators

**How to measure effectiveness:**

- **Violation Frequency:** Track how often hook blocks commits (should decrease over time)
- **Fix Time:** Measure time from blocked commit to successful commit (should decrease)
- **Pattern Adoption:** Count LSP mentions vs grep mentions in new skills (LSP should dominate)
- **False Positives:** Track bypasses with `--no-verify` (should be rare)

**Dashboard Query (Git History):**
```bash
# Count commits blocked by governance (inferred from retries)
git log --all --oneline | grep -i "governance\|fix.*violation" | wc -l

# Measure LSP adoption in skills
grep -r "cclsp" .claude/skills/ | wc -l   # LSP usage
grep -r "grep -r" .claude/skills/ | wc -l  # Anti-pattern usage
```

### Failure Modes & Mitigations

| Failure Mode | Symptom | Mitigation |
|--------------|---------|------------|
| **Hook breaks Git workflow** | All commits blocked | Script has fail-open behavior (exit 0 on exception) |
| **Too strict (false positives)** | Valid commits rejected | Adjust thresholds in script config |
| **Developers bypass with --no-verify** | Rules not enforced | CI job catches bypasses on PR |
| **Script has bugs** | Crashes on edge cases | Test suite validates against fixtures |

### Integration with Learning Flywheel

The governance framework closes the behavioral loop:

1. **Agent encounters failure** (e.g., grep times out on large codebase)
2. **Auto-retrospective captures failure** (`auto_retro.py` updates SKILL.md)
3. **Verification proves fix works** (`verify_skills.py` tests LSP approach)
4. **Governance prevents regression** (hook blocks future grep-heavy commits)
5. **System learns and enforces** (next agent session inherits improved constraints)

This is **Institutional Memory with Enforcement** - not just documenting what went wrong, but preventing it from happening again.

---

## 10. Multi-Agent Architecture (Specialized Execution)

**Problem:** As the Learning Flywheel grows, the main agent's context window gets polluted with thousands of lines from skills, scripts, and negative knowledge. This creates "context bloat" that slows down responses and reduces effectiveness.

**Solution:** Specialized sub-agents that operate with isolated context windows and specific tool permissions, each aligned with institutional memory from `.claude/skills/`.

### Architecture Philosophy

The multi-agent system solves the **"context pollution"** problem through modular AI instances:

```
┌──────────────────────────────────────────────────────────────┐
│                     Main Agent (Orchestrator)                 │
│  - High-level planning and user communication                 │
│  - Delegates specialized tasks to sub-agents                  │
│  - Full tool access (Read, Write, Bash, etc.)                │
└────────────┬──────────────┬──────────────┬───────────────────┘
             │              │              │
             ▼              ▼              ▼
    ┌────────────┐  ┌────────────┐  ┌────────────┐
    │ Knowledge  │  │ Standards  │  │   Infra    │
    │ Explorer   │  │ Enforcer   │  │ Architect  │
    └────────────┘  └────────────┘  └────────────┘
```

**Core Principle:** Each sub-agent is a **"muscle memory specialist"** that:
1. Loads specific skills from `.claude/skills/`
2. Operates with restricted tool permissions (principle of least privilege)
3. Returns concise results (<500 tokens) to avoid polluting main context
4. Compounds expertise through the Learning Flywheel

### The Three Specialists

#### 1. Knowledge Explorer (Flywheel Librarian)

**File:** `.claude/agents/knowledge-explorer.md`

**Purpose:** Research wrapper that prevents context pollution by scanning institutional memory and returning compressed insights.

**When to Use:**
- Before starting any complex task
- When planning implementations
- To check if an approach has failed before
- To find relevant skills and negative knowledge

**Tool Permissions:** `Read`, `Grep`, `Glob` (read-only for safety)

**Model:** `haiku` (fast, cost-effective for research)

**Skills Loaded:** `code-navigation`

**Key Behavior:**
- Scans `.claude/skills/` for relevant failure modes
- Extracts Negative Knowledge tables
- Returns <100 word summaries instead of full files
- Provides file:line references for deeper reading

**Example Invocation:**
```
User: "Before we refactor auth, check for past failures"

Main Agent: "@knowledge-explorer scan for authentication refactor failures"

Knowledge Explorer:
🔍 Knowledge Scan: authentication refactor

📚 Relevant Skills:
- refactor-legacy-code (v1.2.0)

⚠️ Negative Knowledge:
1. ❌ Don't attempt "Big Bang" rewrites
   - Past failure: 3-week rewrite abandoned
   - Fix: Use Strangler Fig pattern

📖 Read: .claude/skills/refactor-legacy-code/SKILL.md:34
```

**Token Savings:** Instead of loading 2000+ lines from skills → 50-100 token summary

#### 2. Standards Enforcer (Strict Reviewer)

**File:** `.claude/agents/standards-enforcer.md`

**Purpose:** Quality gatekeeper that validates implementations against project skills and extracts retrospectives after failures.

**When to Use:**
- After significant code changes (>100 lines)
- Before git commits on critical files
- To extract retrospectives after task failures
- To validate against architectural standards

**Tool Permissions:** `Read`, `Bash`, `Grep`, `Glob` (can execute validation scripts)

**Model:** `sonnet` (balanced for analysis and review)

**Skills Loaded:** `pr-review-standards`, `git-commit-standards`, `test-driven-workflow`

**Key Behavior:**
- Enforces "Negative Knowledge First" principle
- Runs validation scripts (`validate_memory.py`, `pre_commit_governance.py`)
- Rejects implementations that match documented failures
- Generates structured JSON for `auto_retro.py`

**Review Rubric:**
- Security vulnerabilities (auto-reject)
- Negative Knowledge violations (auto-reject)
- Test coverage <70% (auto-reject)
- Governance violations (auto-reject)

**Example Invocation:**
```
User: "Review this API endpoint implementation"

Main Agent: "@standards-enforcer review api/routes/payments.py"

Standards Enforcer:
🛡️ Standards Review: api/routes/payments.py

❌ VIOLATIONS (1):
1. ❌ Missing input validation on amount parameter
   - Location: api/routes/payments.py:67
   - Security risk: Negative amounts could bypass logic
   - Fix: Add amount > 0 validation

✅ PASSED (4):
- Layered architecture ✓
- Test coverage 85% ✓

🚫 VERDICT: REJECTED - Fix validation first
```

**Context Isolation:** Review happens in sub-agent context, only verdict returned to main agent

#### 3. Infrastructure Architect (Tool Specialist)

**File:** `.claude/agents/infra-architect.md`

**Purpose:** Operational safety specialist for database migrations, deployments, and cloud infrastructure changes.

**When to Use:**
- Database migrations
- Infrastructure-as-code changes (Terraform, etc.)
- CI/CD pipeline setup
- Dependency security audits
- Production deployments

**Tool Permissions:** `Read`, `Write`, `Bash`, `Grep`, `Glob` (full access for infrastructure)

**Model:** `sonnet` (requires precision for production safety)

**Skills Loaded:** `database-migration-safe`, `audit-security-dependencies`

**Key Behavior:**
- Runs pre-flight safety checks before any infrastructure change
- Validates migrations for data loss, downtime, and rollback capability
- Enforces backup-first policy for destructive operations
- Knows complex CLI tool flags (Terraform, kubectl, Alembic)

**Safety Guardrails:**
```yaml
Critical (Auto-Reject):
  - DROP TABLE without backup
  - terraform destroy on production
  - Dependency updates without tests
  - Deploy on Friday afternoon

Warning (Require Approval):
  - Schema changes on tables >1M rows
  - Multi-region deployments
  - Breaking API changes
```

**Example Invocation:**
```
User: "Add a column to users table"

Main Agent: "@infra-architect analyze database migration for users table"

Infra Architect:
🏗️ Infrastructure Analysis: Database Migration

📊 Current State:
- Table: users (3.2M rows)
- Database: PostgreSQL 14.5

✅ Safety Checks:
1. ✅ Backward compatible (nullable column, no rewrite)
2. ⚠️ Lock duration: <100ms (metadata-only)
3. ✅ Rollback plan: ALTER TABLE users DROP COLUMN

🚦 APPROVED - Safe to execute
```

### Agent Discovery and Invocation

**Automatic Delegation:**
Claude Code evaluates task descriptions and automatically invokes relevant agents based on trigger keywords in the `description` field.

**Trigger Keywords by Agent:**

| Agent | Auto-Invoke Keywords |
|-------|---------------------|
| `knowledge-explorer` | "check skills", "past failures", "negative knowledge", "before we start" |
| `standards-enforcer` | "review code", "validate", "retrospective", "quality check" |
| `infra-architect` | "migration", "deploy", "infrastructure", "database", "terraform" |

**Manual Invocation:**
```bash
# Via @ mention
@knowledge-explorer scan for API design patterns

# Via explicit request
Hey standards-enforcer, review this implementation
```

**Programmatic (from main agent):**
```python
# Main agent delegates to sub-agent
result = invoke_agent("knowledge-explorer", "scan for refactor failures")
```

### Integration with Learning Flywheel

The multi-agent architecture enhances the flywheel loop:

```
┌─────────────────────────────────────────────────────────────┐
│                    LEARNING FLYWHEEL                         │
│                                                              │
│  1. Knowledge Explorer → Surfaces past failures             │
│     ↓                                                        │
│  2. Main Agent → Implements with awareness                  │
│     ↓                                                        │
│  3. Standards Enforcer → Validates against skills           │
│     ↓                                                        │
│  4. If failure → Extract retrospective (auto_retro.py)      │
│     ↓                                                        │
│  5. Skill updated → Next iteration avoids same mistake      │
│     ↓                                                        │
│  6. Governance hooks → Prevent regression                   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

**Before (Single Agent):**
- Main agent loads all skills into context (30k+ tokens)
- Context polluted with irrelevant details
- Slower responses, reduced effectiveness
- No specialized expertise

**After (Multi-Agent):**
- Knowledge Explorer pre-filters relevant skills (100 tokens)
- Main agent focuses on implementation
- Standards Enforcer validates in isolated context
- Specialized expertise per domain

### Best Practices

**1. Flat Hierarchy (Prevent Recursion)**

Only the main agent can invoke sub-agents. Sub-agents CANNOT invoke other sub-agents.

```
✅ CORRECT:
Main Agent → Knowledge Explorer → Returns result
Main Agent → Standards Enforcer → Returns result

❌ WRONG:
Main Agent → Standards Enforcer → Knowledge Explorer (infinite loop risk)
```

**2. Concise Responses**

Sub-agents MUST return <500 token summaries to avoid re-polluting main context.

**Format:**
```
🎯 [Agent Icon] [Task Summary]

✅ Key Findings (3 max):
- Finding 1
- Finding 2
- Finding 3

📖 References:
- file.md:line
```

**3. Tool Scoping (Principle of Least Privilege)**

Grant sub-agents only the tools they need:

```yaml
knowledge-explorer:
  tools: Read, Grep, Glob  # Read-only

standards-enforcer:
  tools: Read, Bash, Grep, Glob  # + Bash for validation scripts

infra-architect:
  tools: Read, Write, Bash, Grep, Glob  # Full access (needs to modify infra)
```

**4. Model Selection**

Choose the right model for the task:

```yaml
knowledge-explorer:
  model: haiku  # Fast, cheap for research

standards-enforcer:
  model: sonnet  # Balanced for code review

infra-architect:
  model: sonnet  # Precision for production safety
```

**5. Skill Integration**

Load relevant skills automatically via the `skills` field:

```yaml
---
name: standards-enforcer
skills: pr-review-standards, git-commit-standards, test-driven-workflow
---
```

This ensures the sub-agent has access to institutional memory without manual context loading.

### Workflow Examples

#### Example 1: Refactoring with Knowledge Scan

```
User: "Refactor the authentication system"

Main Agent:
"This is a complex task. Let me consult our institutional memory first."
→ Invokes @knowledge-explorer

Knowledge Explorer:
"🔍 Found 2 relevant failures in refactor-legacy-code skill:
1. Don't attempt Big Bang rewrites (use Strangler Fig)
2. Don't refactor without tests (write characterization tests first)"

Main Agent:
"Based on negative knowledge, I'll use Strangler Fig pattern:
1. Write tests for current auth behavior
2. Create new auth module alongside old one
3. Migrate routes incrementally"
→ Implements refactor

Main Agent:
"Implementation complete. Let me validate against standards."
→ Invokes @standards-enforcer

Standards Enforcer:
"🛡️ APPROVED: Test coverage 87%, follows Strangler Fig pattern"

Main Agent: "Refactor complete and validated ✓"
```

**Token Savings:** ~20k tokens (didn't load full skills into main context)

#### Example 2: Database Migration with Safety Checks

```
User: "Add indexes to improve query performance"

Main Agent:
"This is an infrastructure change. Delegating to specialist."
→ Invokes @infra-architect

Infra Architect:
"🏗️ Safety Analysis:
- Table: orders (8M rows)
- Index creation will lock table
- Estimated duration: 15 minutes
- ⚠️ RECOMMENDATION: Use CONCURRENTLY flag (PostgreSQL)

Proposed migration:
CREATE INDEX CONCURRENTLY idx_orders_user_id ON orders(user_id);

✅ APPROVED with CONCURRENTLY flag"

Main Agent: "Migration plan approved. Creating migration file..."
→ Writes migration
→ Invokes @standards-enforcer for final review

Standards Enforcer:
"✅ PASSED: Migration has rollback (DROP INDEX), uses CONCURRENTLY"

Main Agent: "Migration ready to apply ✓"
```

**Safety Achieved:** Infrastructure specialist caught lock issue, suggested fix

#### Example 3: Failed Task + Retrospective

```
User: "Implement feature X"

Main Agent: [Attempts implementation, encounters error]

Main Agent:
"Implementation failed. Extracting retrospective."
→ Invokes @standards-enforcer in retrospective mode

Standards Enforcer:
"Generating retrospective JSON:
{
  'target_skill': '.claude/skills/test-driven-workflow/SKILL.md',
  'negative_knowledge': [{
    'attempt': 'Wrote implementation before tests',
    'failure': 'Integration broke, no way to verify fix',
    'cost': '2 hours debugging',
    'fix': 'Follow TDD: Red-Green-Refactor cycle'
  }]
}

Merging into skill..."
→ Executes: python scripts/auto_retro.py --input /tmp/retro.json

Main Agent: "Retrospective extracted. Skill updated with new failure mode."
```

**Learning Loop Closed:** Next session will load updated skill, avoid same mistake

### Metrics & Success Indicators

**How to measure multi-agent effectiveness:**

| Metric | Measurement | Target |
|--------|-------------|--------|
| **Context Efficiency** | Tokens used per task | 30% reduction vs single agent |
| **Task Delegation Rate** | % of tasks using sub-agents | >50% for complex tasks |
| **Failure Prevention** | Tasks that avoid documented failures | >90% (knowledge-explorer effectiveness) |
| **Review Coverage** | % of commits validated by standards-enforcer | 100% for critical paths |
| **Production Incidents** | Infra changes causing downtime | 0 (infra-architect safety) |

**Dashboard Queries:**

```bash
# Count agent invocations (look for agent mentions in git history)
git log --all --oneline | grep -E "@knowledge-explorer|@standards-enforcer|@infra-architect" | wc -l

# Measure context savings (compare token usage before/after multi-agent)
# (Requires instrumentation in Claude Code)

# Track failure prevention (negative knowledge matches)
grep -r "Negative Knowledge" .claude/skills/ | wc -l
```

### Extension Opportunities

**Future Agents to Consider:**

1. **Test Automation Specialist**
   - Skills: `test-driven-workflow`
   - Tools: `Read`, `Write`, `Bash`
   - Purpose: Generate and execute test suites

2. **Security Auditor**
   - Skills: `audit-security-dependencies`
   - Tools: `Read`, `Bash`
   - Purpose: Scan for vulnerabilities, OWASP compliance

3. **Performance Optimizer**
   - Skills: `optimize-performance-profiling`
   - Tools: `Read`, `Bash`
   - Purpose: Profile-first optimization workflow

4. **Documentation Writer**
   - Skills: Custom documentation standards
   - Tools: `Read`, `Write`
   - Purpose: Generate and maintain technical docs

**Adding a New Agent:**

1. Create agent definition: `.claude/agents/[agent-name].md`
2. Define frontmatter (name, description, tools, skills)
3. Write agent instructions (expertise, patterns, negative knowledge)
4. Update `CLAUDE.md` section 10 with agent details
5. Test with manual invocation: `@agent-name task description`
6. Monitor effectiveness and refine

### Limitations and Tradeoffs

**Limitations:**

1. **Communication Overhead:** Sub-agent invocation adds latency (network roundtrip)
2. **Context Boundaries:** Sub-agents can't access main agent's working memory
3. **No Cross-Agent Communication:** Agents can't collaborate directly (only via main agent)
4. **Token Budget:** Each agent invocation counts against session limit

**Tradeoffs:**

| Benefit | Cost |
|---------|------|
| Reduced context pollution | Invocation latency |
| Specialized expertise | More complex orchestration |
| Parallel execution (future) | Harder to debug |
| Scoped tool permissions | Potential bottlenecks |

**When NOT to Use Sub-Agents:**

- Simple tasks (<50 lines of code)
- Tasks already well-understood by main agent
- Tight latency requirements
- Low token budget remaining

**Decision Matrix:**

```
┌─────────────────────────┬──────────────┬──────────────┐
│ Task Complexity         │ Context Size │ Use Agent?   │
├─────────────────────────┼──────────────┼──────────────┤
│ Simple (<50 lines)      │ Small        │ ❌ No        │
│ Simple (<50 lines)      │ Large        │ ✅ Yes       │
│ Complex (>100 lines)    │ Small        │ ⚠️ Maybe     │
│ Complex (>100 lines)    │ Large        │ ✅ Yes       │
└─────────────────────────┴──────────────┴──────────────┘
```

### Conclusion

The multi-agent architecture transforms the Claude Code Learning Flywheel from a single "amnesiac athlete" into a **specialized team with institutional memory**:

- **Knowledge Explorer** prevents repeating past failures
- **Standards Enforcer** ensures quality through validation
- **Infrastructure Architect** prevents production incidents

Each agent compounds expertise through the flywheel loop, creating a system where AI "muscle memory" improves over time without polluting the main context window.

**Next Steps:**

1. Test agents with manual invocations: `@agent-name task`
2. Monitor token usage and context efficiency
3. Extract retrospectives when agents fail (feed back into skills)
4. Extend with additional specialists as patterns emerge
