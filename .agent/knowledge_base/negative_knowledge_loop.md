# Pattern: Negative Knowledge Feedback Loop

## Context

In autonomous coding environments where agents must learn from failures to prevent regressions across disparate sessions.

## Problem

Agents often "know" how to do something but "forget" what failed in previous attempts by other agents or in past sessions, leading to a "Knowledge Treadmill" where the same bugs are introduced repeatedly.

## Solution

Treat **Failure as Infrastructure**. Document failed attempts in a structured format and enforce its update through automated governance.

### The Feedback Recipe

1. **Failed Attempt Table**: Every skill or module must have a markdown table documenting specific failure modes.
2. **Governance Hook**: A script (e.g., `validate_memory.py`) that checks for the presence of this table.
3. **Immune System Signal**: Mandate a **Version Bump** whenever the "Negative Knowledge" section is updated. This signals to other agents that the "Immune System" of the codebase has evolved.

### Structural Skeleton (SKILL.md)

```markdown
## Negative Knowledge (Failed Attempts)

| Date | Strategy | Failure Mode | Prevention | Version |
|------|----------|--------------|------------|---------|
| YYYY-MM-DD | Attempted X | Error Y occurred | Added check Z to script | 1.0.1 |
```

## Gotchas

- **Semantic Drift**: Not updating the version. If the version stays the same, other agents may assume the failure knowledge is stale.
- **Vague Failure Modes**: Using "it didn't work" instead of specific error messages.
- **Verification Gap**: Not linking the failure to a regression test.
