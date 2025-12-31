# Project Intelligence & Memory System

This file defines the core behavioral patterns for Claude Code in this repository. It implements the **Continual Learning Flywheel** - a system where AI agents learn from both successes and failures, building institutional memory over time.

## Core Principles

1. **Negative Knowledge First**: Document what failed before documenting what worked
2. **Progressive Disclosure**: Load detailed context only when needed
3. **Zero-Context Scripts**: Move complex logic to scripts that return simple outputs
4. **Tiered Knowledge Layers**: Separate personal, team, and enterprise knowledge

---

## Core Commands

### `/advise`

**Trigger:** Before starting complex tasks.

**Purpose:** Activate relevant skills from memory to avoid repeating past mistakes.

**Procedure:**
1. Read the user's stated goal.
2. Scan `.claude/skills/` and `plugins/` for relevant skills based on description matching.
3. **Critical Step:** Look for "Negative Knowledge" (Failed Attempts tables) in matching skills.
4. Summarize:
   * Recommended approach based on past successes
   * Traps to avoid (previous failures documented in skills)
   * Verified configuration parameters
   * Links to reference docs (loaded only if user requests)

**Example:**
```
User: "I need to deploy a new microservice to production"
Claude: Checking skills registry...

Found: .claude/skills/deploy-microservice-k8s/SKILL.md
- ✅ Use helm chart in /deployments/charts/
- ⚠️ AVOID: Direct kubectl apply (causes config drift - see Failed Attempt #3)
- ✅ Required: Run `./scripts/pre-deploy-check.sh` first
```

---

### `/retrospective`

**Trigger:** After completing a significant task (success OR failure).

**Purpose:** Extract learnings and update the skill registry.

**Procedure:**
1. Analyze the conversation history from task start to completion.
2. Identify:
   * The original goal
   * The final working solution (code snippets, commands, config)
   * **The failures** (errors encountered, wrong approaches tried)
   * Root causes of failures
3. **Action Decision Tree:**

   **If a relevant skill already exists:**
   - Update the "Negative Knowledge" table with new failure modes
   - Refine the "Verified Procedure" section with improvements
   - Update version number in frontmatter

   **If this is a new capability:**
   - Create a new directory: `.claude/skills/[verb-noun-context]/`
   - Generate `SKILL.md` using the standard template
   - Add any supporting scripts to `scripts/` subdirectory

4. **Git Operations:**
   * Create a branch: `memory/update-[topic]`
   * Commit the new/updated `SKILL.md` with message format:
     ```
     memory: [action] [skill-name]

     Learned: [key insight in one sentence]
     ```
   * Draft a PR description summarizing:
     - What was attempted
     - What failed and why
     - What ultimately worked
     - Edge cases discovered

**Example Output:**
```
Task completed. Extracting insights...

Created: .claude/skills/debug-webpack-build-errors/SKILL.md
- Documented: 3 failed attempts (memory-limit, cache-corruption, circular-dep)
- Root cause: Webpack 5 changed default cache behavior
- Solution: Add `cache: {type: 'filesystem', maxAge: 86400000}`

Branch created: memory/update-webpack-debugging
Ready to commit.
```

---

## Skill Discovery & Activation

### Automatic Skill Matching

Claude automatically scans for relevant skills when:
- A task matches keywords in skill `description` fields
- A component mentioned in conversation matches a skill's `name` pattern
- A file path being edited matches a skill's scope

### Manual Skill Invocation

Users can explicitly invoke skills:
```
Use the [skill-name] skill to do this
```

### Skill Composition

Skills can reference other skills:
```markdown
## Prerequisites
Before running this skill, ensure:
- Run skill: `validate-db-connection`
- Run skill: `setup-test-fixtures`
```

---

## Governance Rules

### 1. Negative Knowledge Enforcement
- **All skills MUST document what failed**, not just what worked
- Failed Attempts table is mandatory (validated by CI)
- Each failure entry must include:
  - What was tried
  - What error occurred
  - Root cause (not just symptom)
  - How to avoid it

### 2. Context Budget Management
- SKILL.md files limited to 500 lines (enforced by validator)
- Detailed documentation goes in `reference.md` (loaded on-demand)
- API schemas, examples, edge cases go in separate files
- Use "See `reference.md` for details" pattern

### 3. Zero-Context Scripts
- Complex validation logic (>50 lines) must move to `scripts/`
- Scripts must be executable without conversation context
- Output must be human-readable summary (not raw data dumps)
- Example:
  ```bash
  # Instead of 200 lines in SKILL.md explaining "how to check DB health"
  # Use: python scripts/check_db_health.py
  # Output: "✅ Database ready (latency: 12ms)" or "❌ Connection timeout"
  ```

### 4. Naming Conventions
- **Skills:** `[verb]-[noun]-[context]`
  - ✅ `deploy-lambda-terraform`
  - ✅ `debug-auth-middleware`
  - ❌ `deployment` (too vague)
  - ❌ `fix-it` (no context)

- **Scripts:** `[action]_[target].py`
  - ✅ `validate_skill_format.py`
  - ✅ `check_api_health.py`

### 5. Tiered Knowledge Layers

```
Personal (.claude/skills/)     → Your individual learnings
Team (plugins/team-standards/) → Project-wide conventions
Enterprise (plugins/company-*) → Cross-project compliance
```

**Resolution Order:** Personal → Team → Enterprise
(Personal skills can override team defaults for experimentation)

---

## Integration with CI/CD

### Pre-commit Hook
```bash
#!/bin/bash
# .git/hooks/pre-commit
python scripts/validate_memory.py
if [ $? -ne 0 ]; then
  echo "❌ Skill validation failed. Fix errors or use --no-verify"
  exit 1
fi
```

### Pull Request Checks
Required status checks:
- `memory-validation`: Ensures skills follow format
- `no-context-bloat`: Checks file sizes
- `negative-knowledge-present`: Validates failure documentation

---

## Migration Guide

### From Static Prompts
If you have `.claude/prompts/` or old system prompts:
1. Convert each prompt to a skill using the template
2. Add "When to Use" triggers to descriptions
3. Document known failure modes
4. Move to `.claude/skills/[name]/SKILL.md`

### From Ad-hoc Notes
If you have `NOTES.md` or `LESSONS_LEARNED.md`:
1. Extract each distinct insight
2. Group by capability (e.g., all DB-related learnings)
3. Create skills for each capability cluster
4. Populate "Negative Knowledge" from your notes

---

## Architecture Decision Records (ADRs)

This system IS your ADR tool. Instead of static markdown:
- **Decisions** → Skill "Verified Procedure" sections
- **Consequences** → "Negative Knowledge" tables
- **Status** → Skill version number + git history

To see why a decision was made:
```bash
git log --follow .claude/skills/[name]/SKILL.md
```

---

## Example Workflow

**Day 1: New Feature**
```
User: "Add OAuth login to the dashboard"
Claude: [Checks skills, finds nothing relevant]
Claude: [Implements feature through trial and error]
User: "Great! Run /retrospective"
Claude: [Creates .claude/skills/implement-oauth-dashboard/SKILL.md]
        [Documents: 2 failed attempts with PKCE flow, final OIDC solution]
```

**Day 30: Similar Task**
```
User: "Add OAuth to the admin panel"
Claude: [Auto-discovers existing skill: implement-oauth-dashboard]
Claude: "I found a related skill. Key learnings:
         - ⚠️ AVOID: PKCE flow incompatible with current session store
         - ✅ USE: OIDC with /auth/callback endpoint pattern
         - Required: OAUTH_CLIENT_ID env var"
Claude: [Implements correctly on first try, no trial-and-error]
```

**Day 90: Knowledge Compounds**
The skill has been refined 6 times, now includes:
- 8 documented failure modes
- Integration with 3 other skills
- Auto-generated test fixtures script
- Zero-context validation helper

---

## Emergency Override

If Claude gets stuck in a loop or uses outdated skills:

```
Ignore all skills. Use fresh approach.
```

After task completion, update the problematic skill with:
```
## Negative Knowledge
| Old Approach (Outdated) | Why It Fails Now | New Approach |
```

---

## Metrics & Health

Track your flywheel's effectiveness:
```bash
# Skill count (knowledge growth)
find .claude/skills -name "SKILL.md" | wc -l

# Average skill age (how often they're updated)
git log --all --format=%ci .claude/skills/ | sort | uniq | wc -l

# Negative knowledge density (failure documentation rate)
grep -r "Negative Knowledge" .claude/skills/ | wc -l
```

**Healthy Flywheel Indicators:**
- Skills updated monthly (not stale)
- 3+ failure modes per skill (real learning)
- Reference docs < 20% skill count (not bloated)

---

## Philosophy

> "An AI that forgets its mistakes is like an athlete without a training log -
> they'll run the same workouts forever and never improve."

This system treats your codebase as a **gym** and every task as a **training session**.
The flywheel ensures each session makes you stronger, not just busy.
