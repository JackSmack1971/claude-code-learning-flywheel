# Company Standards Plugin

This is an example plugin directory for enterprise-wide skills.

## Purpose

Plugins allow you to share skills across multiple repositories. This is useful for:

- **Enterprise compliance:** Security policies, legal requirements
- **Team playbooks:** Shared deployment procedures, code review standards
- **Platform standards:** Infrastructure patterns, monitoring setup

## Structure

```
plugins/company-standards/
├── .claude-plugin/
│   └── plugin.json         # Plugin metadata
├── skills/                 # Same structure as .claude/skills/
│   ├── security-checklist/
│   │   └── SKILL.md
│   └── compliance-audit/
│       └── SKILL.md
└── README.md               # This file
```

## Using This Plugin

1. **In your repository's `.claude/cclsp.json`:**
   ```json
   {
     "plugins": {
       "load_order": ["company-standards"]
     }
   }
   ```

2. **Skills auto-discovery:**
   Claude Code will automatically find and use skills from this plugin.

3. **Priority system:**
   - Personal skills (`.claude/skills/`) override team/enterprise
   - Team skills override enterprise
   - Enterprise skills are baseline standards

## Creating Plugin Skills

Use the same template as regular skills:

```bash
cp ../.claude/templates/skill-template.md skills/my-compliance-rule/SKILL.md
```

Follow the same validation rules:
- Document negative knowledge
- Keep under 500 lines
- Use descriptive names

## Distribution

Options for sharing plugins across repositories:

1. **Git submodule:**
   ```bash
   git submodule add https://github.com/yourorg/company-standards.git plugins/company-standards
   ```

2. **Package manager:**
   - NPM: `npm install @yourorg/claude-standards`
   - PyPI: `pip install yourorg-claude-standards`

3. **Direct copy:**
   Copy the entire directory into your project

## Governance

Plugin skills can be marked as **required** and **non-overridable** for compliance.

See `plugin.json` for configuration options.
