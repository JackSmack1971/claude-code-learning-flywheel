# Claude Code Learning Flywheel

![The AI Athlete: How Continual Learning Builds Smarter Agents](https://img.shields.io/badge/Status-Production%20Ready-brightgreen) ![Language Agnostic](https://img.shields.io/badge/Language-Agnostic-blue) ![License](https://img.shields.io/badge/License-MIT-yellow)

> **An AI that forgets its mistakes is like an athlete without a training log - they'll run the same workouts forever and never improve.**

This is a **language-agnostic architectural scaffold** for implementing the Claude Code Learning Flywheel - a system where AI agents learn from both successes and failures, building institutional memory over time.

## 🎯 What Problem Does This Solve?

**Traditional AI agents** are like amnesiac athletes:
- ❌ Practice tasks but memory wiped afterward
- ❌ Never learn from failures
- ❌ Repeat the same mistakes in every session
- ❌ Static system prompts that don't evolve

**Learning Flywheel agents** are elite athletes with training logs:
- ✅ Document what worked AND what failed
- ✅ Build "muscle memory" through skill registry
- ✅ Compound knowledge over time
- ✅ Perform at peak by avoiding known pitfalls

## 🏗️ Architecture Overview

```
root/
├── CLAUDE.md                    # The "Operating System" - defines agent behavior
├── .claude/
│   ├── skills/                  # Project Skills (collaborative memory)
│   │   ├── git-commit-standards/
│   │   │   ├── SKILL.md         # Main skill definition
│   │   │   ├── reference.md     # Loaded on-demand (Progressive Disclosure)
│   │   │   └── scripts/         # Zero-context validation scripts
│   │   └── [other-skills]/
│   ├── agents/                  # Custom sub-agents (optional)
│   ├── templates/               # Skill templates
│   │   └── skill-template.md
│   └── cclsp.json               # Universal LSP configuration
├── plugins/                     # Enterprise/Shared Plugins
│   └── company-standards/       # Plugin containing cross-project skills
│       ├── .claude-plugin/
│       │   └── plugin.json
│       └── skills/
└── scripts/
    └── validate_memory.py       # CI/CD Governance script
```

## 🚀 Quick Start

### 1. Clone or Use This Template

```bash
# If using as a template for a new project
git clone https://github.com/yourusername/claude-code-learning-flywheel.git
cd claude-code-learning-flywheel

# Or copy the structure into an existing project
cp -r .claude/ your-project/
cp CLAUDE.md your-project/
cp -r scripts/ your-project/
```

### 2. Create Your First Skill

```bash
# Copy the template
cp .claude/templates/skill-template.md .claude/skills/my-first-skill/SKILL.md

# Edit the skill to document a real capability
# IMPORTANT: Add at least one "Failed Attempt" entry
```

### 3. Validate Your Skills

```bash
# Run the validator
python scripts/validate_memory.py

# Expected output:
# ✅ All skills are valid!
```

### 4. Use Skills in Claude Code

When working with Claude Code, reference skills explicitly:

```
User: "I need to set up a new API endpoint"
Claude: [Checks .claude/skills/ for relevant patterns]
Claude: "Found skill: create-rest-endpoint. Key learnings:
         - ✅ Use Blueprint pattern (in /api/blueprints/)
         - ⚠️ AVOID: Direct app.route() decorators (causes circular imports)
         - Required: Add tests in /tests/api/"
```

Or trigger commands:

```
/advise           # Before starting a complex task
/retrospective    # After completing a task (to extract learnings)
```

## 📚 Core Concepts

### 1. The Continual Learning Flywheel

```
┌─────────────────────────────────────────┐
│  1. THE TASK                            │
│     (The Practice Session)              │
│     User assigns a task, Claude         │
│     activates existing skills           │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  2. SKILL ACTIVATION                    │
│     Claude reads relevant SKILL.md      │
│     files, focusing on "Negative        │
│     Knowledge" (what failed before)     │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  3. AUTOMATED RETROSPECTIVE             │
│     After task completion, extract      │
│     insights: successes + failures      │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  4. EXTRACTING INSIGHTS                 │
│     Update existing skills OR create    │
│     new ones with learned patterns      │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  5. SKILL REGISTRY UPDATE               │
│     Commit to git, PR for review,       │
│     knowledge compounds over time       │
└──────────────┬──────────────────────────┘
               │
               └──────► (Next task benefits from this learning)
```

### 2. Negative Knowledge First

The most important principle: **Document what FAILED before documenting what worked.**

Why? Failures teach you what to avoid, which is more valuable than a list of steps that worked once.

**Example:**
```markdown
## Negative Knowledge

| # | Attempted Strategy | Error | Root Cause | Prevention |
|---|-------------------|-------|------------|------------|
| 1 | Used `rm -rf` in script | Deleted production data | No safety check | Always use `rm -i` or check $ENV first |
```

### 3. Progressive Disclosure

Keep SKILL.md files under 500 lines. Move detailed documentation to separate files:

- `SKILL.md` - Core procedure, failures, quick reference (always loaded)
- `reference.md` - API docs, schemas (loaded on-demand)
- `examples.md` - Code examples (loaded on-demand)
- `troubleshooting.md` - Deep debugging guides (loaded on-demand)

### 4. Zero-Context Scripts

Move complex validation logic to scripts that Claude can execute:

**Instead of:**
```markdown
## How to Check Database Health

1. Connect to PostgreSQL on port 5432
2. Run query: SELECT 1
3. Check connection time < 100ms
4. Verify all tables exist...
[200 more lines]
```

**Do this:**
```markdown
## Prerequisites Check

```bash
python scripts/check_db_health.py
```

Expected: "✅ Database ready (latency: 12ms)"
```

The script contains the logic, Claude sees only the result.

### 5. Tiered Knowledge Layers

```
Personal (.claude/skills/)     → Your individual learnings
├─ priority: 1 (overrides team defaults)
├─ scope: This repository only
└─ examples: Experimental approaches, personal preferences

Team (plugins/team-playbook/) → Project-wide conventions
├─ priority: 2 (shared across team)
├─ scope: All team members
└─ examples: Code review standards, deployment procedures

Enterprise (plugins/company-*) → Cross-project compliance
├─ priority: 3 (company-wide rules)
├─ scope: All company projects
└─ examples: Security policies, legal requirements
```

## 🛠️ Usage Guide

### Creating a New Skill

1. **Copy the template:**
   ```bash
   mkdir -p .claude/skills/my-new-skill
   cp .claude/templates/skill-template.md .claude/skills/my-new-skill/SKILL.md
   ```

2. **Fill in the frontmatter:**
   ```yaml
   ---
   name: deploy-lambda-terraform
   description: "Use when deploying AWS Lambda functions via Terraform. Verified on Terraform 1.5+, AWS Provider 5.0+"
   version: 1.0.0
   tags: ["aws", "deployment", "terraform"]
   ---
   ```

3. **Document failures FIRST:**
   Add real failures you encountered to the "Negative Knowledge" table.

4. **Add the working procedure:**
   Document the steps that ultimately worked.

5. **Validate:**
   ```bash
   python scripts/validate_memory.py --skill .claude/skills/my-new-skill/SKILL.md
   ```

6. **Commit:**
   ```bash
   git add .claude/skills/my-new-skill/
   git commit -m "memory: create deploy-lambda-terraform

   Learned: Terraform state locking requires DynamoDB table configured first"
   ```

### Using `/advise` Command

**Before starting a complex task:**

```
User: "I need to deploy a new microservice to production"
Claude: /advise

[Claude scans .claude/skills/ and plugins/]

Found relevant skills:
- .claude/skills/deploy-microservice-k8s/SKILL.md
- plugins/company-standards/skills/security-checklist/SKILL.md

Key learnings:
✅ Use helm chart in /deployments/charts/
⚠️ AVOID: Direct kubectl apply (causes config drift - Failed Attempt #3)
✅ Required: Run ./scripts/pre-deploy-check.sh first
⚠️ SECURITY: Must pass company security checklist (see plugin)

Proceeding with deployment using these guidelines...
```

### Using `/retrospective` Command

**After completing a task:**

```
User: "Great, the deployment worked!"
User: /retrospective

[Claude analyzes the conversation history]

Extracting insights from task: "Deploy new microservice"

Successes:
- Helm chart deployment completed in 3 minutes
- All health checks passed
- Zero downtime achieved

Failures encountered:
- Attempt 1: Image pull failed (wrong registry URL)
- Attempt 2: Pod crashed (missing CONFIG_MAP_NAME env var)

Creating skill update...

Updated: .claude/skills/deploy-microservice-k8s/SKILL.md
Added to Negative Knowledge:
| 4 | Used generic registry URL | ImagePullBackOff | Need region-specific ECR | Use $AWS_REGION in registry URL |

Branch created: memory/update-microservice-deployment
Ready to commit? [y/n]
```

## 📊 Validation & CI/CD

### Pre-commit Hook (Optional)

```bash
# .git/hooks/pre-commit
#!/bin/bash

python scripts/validate_memory.py

if [ $? -ne 0 ]; then
  echo "❌ Skill validation failed. Fix errors or use --no-verify"
  exit 1
fi
```

### GitHub Actions

Create `.github/workflows/validate-memory.yml`:

```yaml
name: Validate Memory

on: [push, pull_request]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Validate all skills
        run: python scripts/validate_memory.py --strict
```

### Validation Rules

The validator enforces:

- ✅ **Negative Knowledge Required:** Every skill must document at least one failure
- ✅ **Context Budget:** Skills limited to 500 lines (prevents context bloat)
- ✅ **Specific Triggers:** Descriptions must include "Use when" phrases
- ✅ **Naming Convention:** Skills use `verb-noun-context` format
- ✅ **Valid YAML:** Frontmatter must be parseable

## 🔬 Advanced Patterns

### Skill Composition

Skills can reference other skills:

```markdown
## Prerequisites

Before running this skill, ensure:
- Run skill: `validate-db-connection`
- Run skill: `setup-test-fixtures`
```

### Environment-Specific Skills

```
.claude/skills/
├── deploy-to-staging/
│   ├── SKILL.md
│   └── config/
│       └── staging.env
└── deploy-to-production/
    ├── SKILL.md
    └── config/
        └── production.env
```

### Cross-Project Plugins

Create reusable skill libraries:

```
plugins/
└── company-security-standards/
    ├── .claude-plugin/
    │   └── plugin.json
    └── skills/
        ├── owasp-checklist/
        ├── secrets-scanning/
        └── dependency-audit/
```

Reference in `.claude/cclsp.json`:

```json
{
  "plugins": {
    "load_order": ["company-security-standards"]
  }
}
```

## 📈 Measuring Success

Track your flywheel's health:

```bash
# How many skills do you have? (Knowledge growth)
find .claude/skills -name "SKILL.md" | wc -l

# How often are they updated? (Active learning)
git log --all --format=%ci .claude/skills/ | sort | uniq | wc -l

# How much failure documentation? (Real learning vs. copy-paste)
grep -r "Negative Knowledge" .claude/skills/ | wc -l
```

**Healthy Flywheel Indicators:**
- ✅ Skills updated monthly (not stale)
- ✅ 3+ failure modes per skill (real learning)
- ✅ Reference docs < 20% of total skills (not bloated)
- ✅ New team members contribute skills within first week

## 🎓 Learning Resources

- **CLAUDE.md** - Read this first for core behaviors
- **.claude/templates/skill-template.md** - Use this for all new skills
- **.claude/skills/git-commit-standards/** - Example skill to study

## 🤝 Contributing

1. **Add your learnings:**
   - Encountered a failure? Add it to the relevant skill's Negative Knowledge
   - Discovered a new capability? Create a new skill
   - Found a better approach? Update the Verified Procedure

2. **Follow the governance:**
   - Run `python scripts/validate_memory.py` before committing
   - Use conventional commit format: `memory: <action> <skill-name>`
   - Create PRs with descriptive retrospectives

3. **Keep it lean:**
   - Skills under 500 lines
   - Move details to reference.md
   - Use zero-context scripts for complex logic

## 📜 License

MIT License - See LICENSE file

## 🙏 Acknowledgments

Based on the Claude Code Learning Flywheel concept, inspired by:
- Progressive Disclosure (cognitive load management)
- Negative Knowledge (learning from failure)
- Zero-Context Optimization (efficient context windows)
- Atomic Skills (composable capabilities)

---

**Remember:** An AI agent that doesn't learn from its mistakes is just an expensive autocomplete. Build the flywheel, compound your knowledge, and watch your agents get smarter every day. 🚀
