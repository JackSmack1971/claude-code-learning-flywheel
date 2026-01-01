# Multi-Agent Architecture

This directory contains specialized sub-agent definitions for the Claude Code Learning Flywheel. Each agent operates with isolated context windows and specific tool permissions to prevent context pollution while compounding expertise through institutional memory.

## Available Agents

### 🔍 Knowledge Explorer (`knowledge-explorer.md`)

**Purpose:** Research wrapper that scans `.claude/skills/` for past failures and returns compressed insights.

**When to use:**
- Before starting complex tasks
- To check if an approach has failed before
- When planning implementations

**Invocation:**
```
@knowledge-explorer scan for [topic] failures
```

**Example:**
```
@knowledge-explorer check for API design patterns
```

---

### 🛡️ Standards Enforcer (`standards-enforcer.md`)

**Purpose:** Quality gatekeeper that validates implementations against project skills and extracts retrospectives.

**When to use:**
- After significant code changes (>100 lines)
- Before git commits on critical files
- To extract retrospectives after failures

**Invocation:**
```
@standards-enforcer review [file/module]
```

**Example:**
```
@standards-enforcer validate this implementation
```

---

### 🏗️ Infrastructure Architect (`infra-architect.md`)

**Purpose:** Operational safety specialist for database migrations, deployments, and infrastructure changes.

**When to use:**
- Database schema changes
- Infrastructure-as-code deployments
- Dependency security audits

**Invocation:**
```
@infra-architect analyze [infrastructure change]
```

**Example:**
```
@infra-architect review this database migration
```

---

## Architecture Overview

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
       (Haiku)        (Sonnet)        (Sonnet)
     Read-only     + Validation    Full Access
```

## Key Benefits

1. **Context Efficiency:** Sub-agents return <500 token summaries instead of loading full skills
2. **Specialized Expertise:** Each agent has deep knowledge of specific domains
3. **Tool Scoping:** Principle of least privilege (agents only get tools they need)
4. **Parallel Execution:** Multiple agents can work simultaneously (future)
5. **Institutional Memory:** Agents load relevant skills automatically

## Testing

Validate all agent definitions:

```bash
python tests/agents/test_agent_definitions.py
```

This checks:
- Valid YAML frontmatter
- Required fields (name, description)
- Tool permissions are valid
- Referenced skills exist
- Agent body has sufficient content

## Adding New Agents

1. Create new file: `.claude/agents/[agent-name].md`

2. Add YAML frontmatter:
```yaml
---
name: agent-name
description: "Use when [trigger condition]. Expert in [expertise]."
tools: Read, Grep, Bash  # Only tools needed
model: sonnet  # or haiku, opus
skills: skill-name, other-skill  # Auto-load skills
---
```

3. Write agent instructions (see existing agents for examples)

4. Test with validation script:
```bash
python tests/agents/test_agent_definitions.py
```

5. Update `CLAUDE.md` section 10 with agent details

6. Test manual invocation:
```
@agent-name test task
```

## Best Practices

### 1. Flat Hierarchy
Only the main agent invokes sub-agents. Sub-agents CANNOT invoke other sub-agents (prevents recursion).

### 2. Concise Responses
Sub-agents MUST return <500 token summaries to avoid re-polluting main context.

### 3. Tool Scoping
Grant minimum necessary permissions:
- **Research agents:** Read, Grep, Glob (read-only)
- **Validation agents:** + Bash (for running scripts)
- **Infrastructure agents:** Full access (needs to modify files)

### 4. Model Selection
- **Haiku:** Fast, cheap for research/scanning
- **Sonnet:** Balanced for code review and analysis
- **Opus:** Reserved for complex reasoning (use sparingly)

### 5. Skill Integration
Always specify relevant skills in frontmatter to load institutional memory automatically.

## Integration with Learning Flywheel

```
1. Knowledge Explorer → Surfaces past failures
   ↓
2. Main Agent → Implements with awareness
   ↓
3. Standards Enforcer → Validates against skills
   ↓
4. If failure → Extract retrospective (auto_retro.py)
   ↓
5. Skill updated → Next iteration avoids same mistake
   ↓
6. Governance hooks → Prevent regression
```

## Metrics

Track effectiveness:
```bash
# Count agent invocations in git history
git log --all --oneline | grep -E "@knowledge-explorer|@standards-enforcer|@infra-architect" | wc -l

# Validate all agents
python tests/agents/test_agent_definitions.py
```

## Documentation

Full documentation: `CLAUDE.md` § 10 (Multi-Agent Architecture)

- Architecture philosophy
- Detailed agent specifications
- Workflow examples
- Metrics and success indicators
- Extension opportunities
- Limitations and tradeoffs
