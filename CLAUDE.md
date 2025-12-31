# Project Memory & Governance

## 1. Project Context (The WHAT & WHY)
- **Goal:** Implement a self-improving "Continual Learning Flywheel" for AI agent capabilities.
- **Architecture:** Python-based scaffolding leveraging Claude Code's memory hierarchy (Tier 1-5).
- **Core Principle:** Negative Knowledge First. Check for past failures before attempting complex tasks.

## 2. Operational Directives (The HOW)
- **Constraint:** Do not rely on internal training data for project specifics; use `file_search` or `ls`.
- **Style:** Adhere to existing patterns in `src/`. Run linters via `scripts/lint.sh` (if available).
- **Governance:** All complex logic (>500 lines) MUST use "Zero-Context Scripts" [Source: Governance Framework].

## 3. Agent Commands
> **Trigger:** Use `/advise` before starting significant refactors or deployments.

**Procedure for `/advise`:**
1.  **Scan:** Search `.claude/skills/` and `plugins/` for relevant capabilities.
2.  **Verify:** Check "Negative Knowledge" (Failed Attempts) in those skills.
3.  **Report:** Summarize verified approaches and specific traps to avoid.
4.  **Execute:** Proceed only after confirming the plan avoids documented failures.

## 4. Maintenance
- **Reflexion:** After every task, run `/retrospective` to extract insights.
- **Updates:** If a new failure mode is discovered, update the relevant `SKILL.md` immediately.
