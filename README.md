# Claude Code Learning Flywheel

![The AI Athlete](https://img.shields.io/badge/Status-Production%20Ready-brightgreen) ![Language Agnostic](https://img.shields.io/badge/Language-Agnostic-blue) ![License](https://img.shields.io/badge/License-MIT-yellow)

> **An AI that forgets its mistakes is like an athlete without a training log - they'll run the same workouts forever and never improve.**

This is a **language-agnostic architectural scaffold** for implementing the Claude Code Learning Flywheel. It transforms AI agents from session-based "amnesiacs" into elite performers with institutional memory.

## 🎯 The Core Problem: Context Rot

In traditional AI workflows:

- ❌ **Vanishing Knowledge:** Learnings are trapped in chat history and forgotten.
- ❌ **Repetitive Failures:** The same logic errors recur across different sessions.
- ❌ **Stale Documentation:** Procedures drift from actual code reality.
- ❌ **Feedback Gap:** Agents lack a mechanism to "study" their own mistakes.

**The Flywheel Solution:** Knowledge as Infrastructure. Every success and failure is codified, versioned, and automatically verified.

## 🏗️ Technical Architecture

The repository is organized into three distinct layers: Governance, Learning, and Verification.

```
root/
├── CLAUDE.md                    # The OS - defines core agent protocols
├── .claude/
│   ├── skills/                  # Institutional Memory (The Registry)
│   │   ├── git-commit-standards/
│   │   │   ├── SKILL.md         # Procedural knowledge & Negative Knowledge
│   │   │   └── reference.md     # On-demand deep context
│   │   └── [skill-name]/
│   └── templates/               # Governance blueprints
├── scripts/                     # The Flywheel Engine
│   ├── validate_memory.py       # Governance: Enforces semver & Negative Knowledge
│   ├── skill_checkers.py        # Validation Logic: Modular rule engine
│   ├── verify_skills.py         # Verification: Runs executable proofs (CI/CD)
│   ├── auto_retro.py            # Learning: Merges JSON insights into skills
│   └── yaml_parser.py           # Robust stdlib frontmatter parser
└── tests/                       # Verification Artifacts
    └── skills/                  # Executable tests for each skill
```

## 🚀 The Flywheel Lifecycle

### 1. Planning (`/advise`)

Before a task, Claude scans the Registry for relevant skills, prioritizing **Negative Knowledge** (what failed before) to avoid known traps.

### 2. Execution & Discovery

As Claude works, it encounters new failure modes. These are captured as "Shadow Knowledge" during the session.

### 3. Automated Retrospective (`auto_retro.py`)

Insights are serialized to JSON and merged back into the Skill Registry.

- ✅ **Version Bumps:** Updates to Negative Knowledge trigger mandatory version changes.
- ✅ **Table Injection:** Failure rows are surgically appended to MD tables.

### 4. Continuous Verification (`verify_skills.py`)

Skills are not just text; they are **Verified Infrastructure**.

- ✅ **Executable Proofs:** Skills point to test scripts that validate the procedure.
- ✅ **Proof of Correctness:** Successful tests update the `last_verified` field.

### 5. Governance (`validate_memory.py`)

A strict rule engine ensures the Registry remains healthy.

- ✅ **Mandatory Failures:** Skills without Negative Knowledge are rejected.
- ✅ **Context Budgeting:** Prevents "Token Bloat" by enforcing line limits.

## 🛠️ Getting Started

### Installation

```bash
# Clone the flywheel
git clone https://github.com/yourusername/claude-code-learning-flywheel.git

# Initialize your project
cp -r .claude/ your-project/
cp -r scripts/ your-project/
```

### The Verification Loop

```bash
# 1. Run full verification suite
python scripts/verify_skills.py --report verify-report.json

# 2. Add a new failure mode safely
python scripts/auto_retro.py --input insights.json

# 3. Secure the registry before commit
python scripts/validate_memory.py --strict
```

## 📜 Governance Standards

| Protocol | Constraint | Rationale |
| :--- | :--- | :--- |
| **Negative Knowledge** | Mandatory | You learn more from 1 failure than 10 successes. |
| **Semver Enforcement** | P0 | Negative Knowledge changes MUST bump version. |
| **Context Budget** | < 500 lines | Prevents context window saturation. |
| **Verification First** | `last_verified` | Documentation without tests is just a wish. |

## 🤝 Contributing to the Flywheel

1. **Codify Failures Early:** Document the "How NOT to" before the "How to."
2. **Use Zero-Context Scripts:** Move complex logic from MD to executable scripts.
3. **Follow the Versioning Rule:** Bump the version to signal a knowledge update to the agent.

---

**Remember:** An AI agent that doesn't learn from its mistakes is just an expensive autocomplete. Build the flywheel, watch your knowledge compound, and reach peak performance. 🚀
