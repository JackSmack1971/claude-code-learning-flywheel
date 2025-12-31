# Retrospective Template

> **Purpose:** Extract learnings from every significant task to feed the Continual Learning Flywheel.
> **When to Use:** After completing a non-trivial task, encountering failures, or discovering new patterns.

---

## 1. Task Summary

**Task Description:**
<!-- What was the goal? What did you try to accomplish? -->

**Outcome:**
- [ ] Success
- [ ] Partial Success
- [ ] Failure

**Session ID:** <!-- If applicable -->
**Date:** <!-- YYYY-MM-DD -->

---

## 2. What Worked (Verified Procedure)

<!-- Document approaches that SUCCEEDED. Be specific about:
- Exact commands or code patterns that worked
- Why they worked (environmental factors, tool capabilities, etc.)
- When to use this approach again
-->

### Example:
```markdown
✅ **Used LSP for code navigation instead of reading full files**
- Command: `cclsp definition UserAuth`
- Why it worked: Reduced token usage by 90%, got exact answer immediately
- When to use: Anytime you need to find a symbol definition in a codebase
```

---

## 3. What Failed (Negative Knowledge)

<!-- Document approaches that FAILED. This is the MOST IMPORTANT section.
- What did you try that didn't work?
- Why did it fail? (Tool limitation, wrong assumption, environment issue, etc.)
- What was the cost? (Time wasted, tokens used, errors encountered)
- What should you try instead?
-->

### Example:
```markdown
❌ **Attempted to use `grep -r` to find all class references**
- Command: `grep -r "class UserAuth" .`
- Why it failed: Returned 200+ false positives (comments, docs, strings)
- Cost: 15,000 tokens reading irrelevant files, 5 minutes wasted
- Try instead: `cclsp references UserAuth` (semantic search, not text search)
```

| Attempt | Failure Reason | Cost | Correct Approach |
|---------|----------------|------|------------------|
| <!-- Failed approach 1 --> | <!-- Why it failed --> | <!-- Time/tokens wasted --> | <!-- What works --> |
| <!-- Failed approach 2 --> | <!-- Why it failed --> | <!-- Time/tokens wasted --> | <!-- What works --> |

---

## 4. Insights & Patterns

<!-- High-level takeaways. What did you learn about:
- The codebase architecture?
- Tool capabilities and limitations?
- Common pitfalls to avoid?
- Workflow optimizations?
-->

### Example:
```markdown
🔍 **Insight: LSP is 10-100x more efficient than text-based search for semantic queries**
- Pattern: Use LSP first, grep only for literal string search
- Applies to: Any codebase with LSP support
- Exception: When LSP server is unavailable or language not supported
```

---

## 5. Proposed Skill Update (Diff Format)

<!-- If this retrospective reveals a NEW failure mode or verified procedure,
propose an update to the relevant SKILL.md file. Use diff format:

```diff
# In .claude/skills/code-navigation/SKILL.md

## Negative Knowledge

+ ### Failed Attempts
+ | Attempt | Why It Failed | Token Cost |
+ | Using `find` + `cat` to explore codebase | Read 50+ files unnecessarily | 20,000 tokens |
+ | **Lesson:** Always check if `cclsp outline` can provide structure first |
```

If no skill exists yet, propose creating a new one.
-->

**Skill to Update:** <!-- e.g., .claude/skills/code-navigation/SKILL.md -->

**Proposed Changes:**
```diff
<!-- Paste diff here, or write "N/A - no skill update needed" -->
```

---

## 6. Action Items

<!-- What needs to be done as a result of this retrospective? -->

- [ ] Update skill: `.claude/skills/<skill-name>/SKILL.md`
- [ ] Create new skill for: `<new-capability>`
- [ ] Archive outdated skill: `<skill-name>` (moved to `.archive/`)
- [ ] Update `scripts/validate_memory.py` with new governance rule
- [ ] Document in `doc/learnings/` for future reference

---

## 7. Metadata

**Related Skills:**
- <!-- List skills that were used or should be updated -->

**Tools Used:**
- <!-- List tools that were critical to this task -->

**Token Efficiency:**
- Estimated tokens used: <!-- If measurable -->
- Estimated tokens saved (vs. naive approach): <!-- If applicable -->

**Knowledge Tier:**
- [ ] Tier 1 (Conversation Memory) - Temporary
- [ ] Tier 2 (CLAUDE.md) - Update onboarding map
- [ ] Tier 3 (Skills) - Update or create skill
- [ ] Tier 4 (Scripts) - Create zero-context executor
- [ ] Tier 5 (Documentation) - Archive for reference

---

## 8. Retrospective on the Retrospective

<!-- Meta-learning: Was this retrospective useful? Could the template be improved? -->

**Template Effectiveness:**
- [ ] Very useful - captured critical learnings
- [ ] Somewhat useful - some sections were redundant
- [ ] Not useful - didn't extract actionable insights

**Suggested Improvements:**
<!-- How could this template be better? -->

---

*Template Version: 1.0.0*
*Last Updated: 2025-12-31*
*Source: Architectural Diagnosis - Phase 2*
