#!/usr/bin/env python3
"""
Integration tests for multi-agent architecture.

Tests agent definition files for:
- Valid YAML frontmatter
- Required fields (name, description)
- Tool permissions are valid
- Model selection is valid
- Skills references exist
"""

import os
import re
import sys
import yaml
from pathlib import Path


class AgentValidator:
    """Validates agent definition files."""

    VALID_TOOLS = {'Read', 'Write', 'Bash', 'Grep', 'Glob', 'Edit', 'WebFetch', 'WebSearch'}
    VALID_MODELS = {'sonnet', 'opus', 'haiku', 'inherit'}
    REQUIRED_FIELDS = {'name', 'description'}

    def __init__(self, repo_root):
        self.repo_root = Path(repo_root)
        self.agents_dir = self.repo_root / '.claude' / 'agents'
        self.skills_dir = self.repo_root / '.claude' / 'skills'

    def find_agent_files(self):
        """Find all agent definition files."""
        if not self.agents_dir.exists():
            return []
        return list(self.agents_dir.glob('*.md'))

    def extract_frontmatter(self, content):
        """Extract YAML frontmatter from markdown file."""
        # Match YAML frontmatter between --- delimiters
        pattern = r'^---\s*\n(.*?)\n---\s*\n'
        match = re.match(pattern, content, re.DOTALL)

        if not match:
            return None

        try:
            frontmatter = yaml.safe_load(match.group(1))
            return frontmatter
        except yaml.YAMLError as e:
            return None

    def validate_agent(self, agent_path):
        """Validate a single agent definition file."""
        errors = []
        warnings = []

        # Read file
        try:
            with open(agent_path, 'r') as f:
                content = f.read()
        except Exception as e:
            return [f"Failed to read file: {e}"], []

        # Extract frontmatter
        frontmatter = self.extract_frontmatter(content)
        if frontmatter is None:
            return [f"Invalid or missing YAML frontmatter"], []

        # Check required fields
        for field in self.REQUIRED_FIELDS:
            if field not in frontmatter:
                errors.append(f"Missing required field: {field}")

        # Validate name (should be kebab-case)
        if 'name' in frontmatter:
            name = frontmatter['name']
            if not re.match(r'^[a-z0-9]+(-[a-z0-9]+)*$', name):
                warnings.append(f"Name '{name}' should be kebab-case (e.g., 'knowledge-explorer')")

        # Validate description (should mention "Use when" or "MUST BE USED")
        if 'description' in frontmatter:
            desc = frontmatter['description']
            if 'use when' not in desc.lower() and 'must be used' not in desc.lower():
                warnings.append("Description should include trigger language ('Use when...' or 'MUST BE USED')")

        # Validate tools (if present)
        if 'tools' in frontmatter:
            tools = frontmatter['tools']

            # Handle both string and list formats
            if isinstance(tools, str):
                tool_list = [t.strip() for t in tools.split(',')]
            elif isinstance(tools, list):
                tool_list = tools
            else:
                errors.append(f"Tools field must be string or list, got {type(tools)}")
                tool_list = []

            # Check each tool is valid
            for tool in tool_list:
                if tool not in self.VALID_TOOLS:
                    warnings.append(f"Unknown tool '{tool}' (valid: {', '.join(sorted(self.VALID_TOOLS))})")

        # Validate model (if present)
        if 'model' in frontmatter:
            model = frontmatter['model']
            if model not in self.VALID_MODELS:
                errors.append(f"Invalid model '{model}' (valid: {', '.join(sorted(self.VALID_MODELS))})")

        # Validate skills (if present)
        if 'skills' in frontmatter:
            skills = frontmatter['skills']

            # Handle both string and list formats
            if isinstance(skills, str):
                skill_list = [s.strip() for s in skills.split(',')]
            elif isinstance(skills, list):
                skill_list = skills
            else:
                errors.append(f"Skills field must be string or list, got {type(skills)}")
                skill_list = []

            # Check each skill exists
            for skill in skill_list:
                skill_path = self.skills_dir / skill / 'SKILL.md'
                if not skill_path.exists():
                    warnings.append(f"Referenced skill '{skill}' not found at {skill_path}")

        # Check body has content
        body = content.split('---', 2)[-1].strip()
        if len(body) < 100:
            warnings.append("Agent body seems too short (<100 chars). Add detailed instructions.")

        # Check for negative knowledge section
        if '## Negative Knowledge' not in content:
            warnings.append("Consider adding a 'Negative Knowledge' section for self-improvement")

        return errors, warnings

    def validate_all_agents(self):
        """Validate all agent files and return report."""
        agent_files = self.find_agent_files()

        if not agent_files:
            return {
                'total': 0,
                'passed': 0,
                'failed': 0,
                'agents': []
            }

        results = []
        passed = 0
        failed = 0

        for agent_path in agent_files:
            errors, warnings = self.validate_agent(agent_path)

            result = {
                'name': agent_path.name,
                'path': str(agent_path.relative_to(self.repo_root)),
                'errors': errors,
                'warnings': warnings,
                'passed': len(errors) == 0
            }

            results.append(result)

            if result['passed']:
                passed += 1
            else:
                failed += 1

        return {
            'total': len(agent_files),
            'passed': passed,
            'failed': failed,
            'agents': results
        }


def print_report(report):
    """Print validation report to console."""
    print(f"\n{'='*70}")
    print(f"  MULTI-AGENT VALIDATION REPORT")
    print(f"{'='*70}\n")

    print(f"📊 Summary:")
    print(f"   Total agents: {report['total']}")
    print(f"   ✅ Passed: {report['passed']}")
    print(f"   ❌ Failed: {report['failed']}")
    print()

    if report['total'] == 0:
        print("⚠️  No agent files found in .claude/agents/")
        print("   Create agent definitions to enable multi-agent architecture.")
        return

    # Print details for each agent
    for agent in report['agents']:
        status_icon = '✅' if agent['passed'] else '❌'
        print(f"{status_icon} {agent['name']}")
        print(f"   Path: {agent['path']}")

        if agent['errors']:
            print(f"   ❌ ERRORS ({len(agent['errors'])}):")
            for error in agent['errors']:
                print(f"      - {error}")

        if agent['warnings']:
            print(f"   ⚠️  WARNINGS ({len(agent['warnings'])}):")
            for warning in agent['warnings']:
                print(f"      - {warning}")

        if agent['passed'] and not agent['warnings']:
            print(f"   ✅ All checks passed")

        print()

    # Final verdict
    print(f"{'='*70}")
    if report['failed'] == 0:
        print(f"✅ ALL AGENTS VALID")
        print(f"{'='*70}\n")
        return 0
    else:
        print(f"❌ {report['failed']} AGENT(S) FAILED VALIDATION")
        print(f"{'='*70}\n")
        return 1


def main():
    """Main entry point."""
    # Find repository root (assuming script is in tests/agents/)
    script_dir = Path(__file__).parent
    repo_root = script_dir.parent.parent

    # Validate agents
    validator = AgentValidator(repo_root)
    report = validator.validate_all_agents()

    # Print report
    exit_code = print_report(report)

    sys.exit(exit_code)


if __name__ == '__main__':
    main()
