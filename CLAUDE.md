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
