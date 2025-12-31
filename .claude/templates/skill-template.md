---
name: [verb]-[noun]-[context]
description: "Specific trigger description. Use when [Action] on [Component]. Verified on [Tech Stack/Version]."
author: "[Your Name or Team]"  # Optional: For ownership and contact
allowed-tools: []  # Optional: ["Read", "Write", "Bash", "Glob", "Grep"]
version: 1.0.0
last_verified: "YYYY-MM-DD"  # Date this skill was last verified to work
tags: []  # Optional: ["database", "deployment", "testing"]
related-skills: []  # Optional: ["other-skill-name"]
---

# [Skill Name]

## 1. Context & Scope

Brief 2-3 sentence description of the architectural context where this skill applies.

**Trigger Conditions:**
- When user asks to [specific action]
- When working with [specific component/file pattern]
- When encountering [specific error pattern]

**Environment:**
- Language/Framework: [e.g., Python 3.11, Node.js 18+]
- Dependencies: [e.g., pytest 7.x, Docker 24+]
- Verified Working On: [Date of last verification]

**Out of Scope:**
- [What this skill does NOT cover]
- [Related but different scenarios]

---

## 2. Negative Knowledge (Read First)

*History of failure is more valuable than instructions. Check this BEFORE executing the procedure.*

### Failed Attempts Table

| # | Attempted Strategy | Error/Symptom | Root Cause | Fix/Prevention |
|---|-------------------|---------------|------------|----------------|
| 1 | [e.g., Used semantic search for codebase] | [OOM error with large repos] | [Vector DB overhead >2GB RAM] | [Use Regex Grep + file patterns instead] |
| 2 | [e.g., Installed package globally] | [Version conflict with other projects] | [Global npm pollutes PATH] | [Use project-local install with npx] |
| 3 | [Example placeholder - delete after adding real failures] | | | |

### Common Pitfalls

- **❌ Don't:** [Anti-pattern observed in practice]
  - **Why it fails:** [Specific reason]
  - **✅ Do instead:** [Alternative approach]

- **❌ Don't:** [Another anti-pattern]
  - **Why it fails:** [Specific reason]
  - **✅ Do instead:** [Alternative approach]

---

## 3. Verified Procedure

Step-by-step instructions that have been validated in practice.

### Prerequisites Check

Run this zero-context validation script:
```bash
# Option 1: Use automated checker
python scripts/check_prerequisites.py

# Option 2: Manual checks
[Command to verify dependency X is installed]
[Command to verify service Y is running]
```

**Expected output:** "✅ All prerequisites met" (or specific actionable error)

### Step 1: [Preparation Phase]

**Description:** [What this step accomplishes]

```bash
# Commands with explanatory comments
[command here]
```

**Validation:**
```bash
# How to verify this step succeeded
[validation command]
# Expected output: [what success looks like]
```

### Step 2: [Execution Phase]

**Description:** [What this step accomplishes]

**Important:** [Critical timing/order considerations]

```bash
# Commands
[command here]
```

**Validation:**
```bash
[validation command]
```

### Step 3: [Verification Phase]

**Description:** [Final checks]

```bash
# Run comprehensive test
[command here]
```

**Success Criteria:**
- [ ] [Observable outcome 1]
- [ ] [Observable outcome 2]
- [ ] [Observable outcome 3]

---

## 4. Configuration Reference

### Required Environment Variables

```bash
# .env.example
VARIABLE_NAME=value  # Purpose: [what this controls]
ANOTHER_VAR=value    # Purpose: [what this controls]
```

### File Locations

| File | Purpose | Critical Settings |
|------|---------|-------------------|
| `path/to/config.yml` | [Description] | `key: value` (see reference.md) |
| `path/to/another.json` | [Description] | `setting: default` |

### Verified Working Configuration

```yaml
# Copy-paste ready configuration that has been validated
setting1: value1
setting2:
  nested: value2
# Comments explain why each value matters
```

---

## 5. Troubleshooting

### Error Pattern Recognition

| Error Message (Regex) | Likely Cause | Quick Fix |
|-----------------------|--------------|-----------|
| `.*ConnectionRefused.*:5432` | PostgreSQL not running | `docker-compose up -d db` |
| `.*ModuleNotFoundError.*` | Missing dependency | `pip install -r requirements.txt` |

### Diagnostic Commands

When things go wrong, run these to gather information:

```bash
# Check system state
[diagnostic command 1]

# Check logs
[diagnostic command 2]

# Check configuration
[diagnostic command 3]
```

Paste output when asking for help.

---

## 6. Reference Links

*Progressive Disclosure: These are loaded only when user explicitly asks for details.*

- **API Documentation:** See `reference.md` for full API schemas
- **Edge Cases:** See `edge-cases.md` for rare scenarios
- **Examples:** See `examples/` directory for working code samples
- **Troubleshooting Deep Dive:** See `troubleshooting.md` for advanced debugging

**External Resources:**
- [Official Docs](https://example.com/docs)
- [GitHub Issue discussing edge case](https://github.com/example/issue)

---

## 7. Maintenance Log

Track when and why this skill was updated:

| Date | Version | Change Summary | Trigger |
|------|---------|----------------|---------|
| 2025-01-XX | 1.0.0 | Initial creation | [Task that created this skill] |
| | | | |

---

## 8. Metrics & Success Indicators

**How to measure if this skill is working:**

- **Time saved:** [e.g., "Deployment now takes 5min vs 30min"]
- **Error rate:** [e.g., "Zero failed deployments since adoption"]
- **Confidence:** [e.g., "Team members can deploy without assistance"]

**When to update this skill:**
- After any failed attempt (add to Negative Knowledge)
- When environment versions change (update Prerequisites)
- When new edge cases discovered (add to Troubleshooting)

---

## Template Usage Instructions

**To create a new skill:**
1. Copy this template to `.claude/skills/[your-skill-name]/SKILL.md`
2. Replace all `[bracketed placeholders]` with actual content
3. Delete the example entries from Failed Attempts table
4. Populate with at least ONE real failure from your experience
5. Run `python scripts/validate_memory.py` to verify format
6. Commit with message: `memory: create [skill-name]`

**Required sections (validator will fail without these):**
- Negative Knowledge / Failed Attempts table (at least 1 entry)
- Verified Procedure (at least 3 steps)
- Description in frontmatter (must contain "Use when")

**Optional sections (delete if unused):**
- Troubleshooting (if no known errors yet)
- Configuration Reference (if no config needed)
- Reference Links (if self-contained)
