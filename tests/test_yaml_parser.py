#!/usr/bin/env python3
"""
Test suite for robust YAML parser.

Tests edge cases that break simple split-on-colon parsing:
- Multiline values with colons
- Nested objects
- Complex quoted strings
- Arrays (inline and multiline)
- Block scalars
- Machine-generated YAML
"""

import sys
import os
from pathlib import Path

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))

from yaml_parser import extract_frontmatter, parse_yaml_subset


def test_simple_key_value():
    """Test basic key:value parsing."""
    yaml = """
name: test-skill
version: 1.0.0
description: A simple test
"""
    result = parse_yaml_subset(yaml)

    assert result['name'] == 'test-skill'
    assert result['version'] == '1.0.0'
    assert result['description'] == 'A simple test'
    print("✅ test_simple_key_value passed")


def test_quoted_strings_with_colons():
    """Test quoted strings containing colons (common edge case)."""
    yaml = """
description: "Use when: deploying to production"
command: "Step 1: Configure. Step 2: Deploy"
"""
    result = parse_yaml_subset(yaml)

    assert result['description'] == 'Use when: deploying to production'
    assert result['command'] == 'Step 1: Configure. Step 2: Deploy'
    print("✅ test_quoted_strings_with_colons passed")


def test_inline_arrays():
    """Test inline array syntax [item1, item2]."""
    yaml = """
tags: [deployment, production, aws]
allowed-tools: ["Bash", "Read", "Write"]
empty: []
"""
    result = parse_yaml_subset(yaml)

    assert result['tags'] == ['deployment', 'production', 'aws']
    assert result['allowed-tools'] == ['Bash', 'Read', 'Write']
    assert result['empty'] == []
    print("✅ test_inline_arrays passed")


def test_multiline_arrays():
    """Test multiline array syntax with dashes."""
    yaml = """
tags:
  - deployment
  - production
  - aws
"""
    result = parse_yaml_subset(yaml)

    assert result['tags'] == ['deployment', 'production', 'aws']
    print("✅ test_multiline_arrays passed")


def test_nested_objects():
    """Test nested object parsing (verification metadata)."""
    yaml = """
verification:
  test_script: "tests/test_foo.py"
  command: "python3 tests/test_foo.py"
  frequency: "on-change"
"""
    result = parse_yaml_subset(yaml)

    assert 'verification' in result
    assert isinstance(result['verification'], dict)
    assert result['verification']['test_script'] == 'tests/test_foo.py'
    assert result['verification']['command'] == 'python3 tests/test_foo.py'
    assert result['verification']['frequency'] == 'on-change'
    print("✅ test_nested_objects passed")


def test_empty_values():
    """Test empty and null values."""
    yaml = """
empty1:
empty2: ""
empty3: null
empty4: ~
"""
    result = parse_yaml_subset(yaml)

    assert result['empty1'] == ''
    assert result['empty2'] == ''
    assert result['empty3'] == ''
    assert result['empty4'] == ''
    print("✅ test_empty_values passed")


def test_comments():
    """Test that comments are ignored."""
    yaml = """
# This is a comment
name: test-skill  # inline comment
# Another comment
version: 1.0.0
"""
    result = parse_yaml_subset(yaml)

    assert result['name'] == 'test-skill'
    assert result['version'] == '1.0.0'
    print("✅ test_comments passed")


def test_block_scalar_literal():
    """Test block scalar with | (literal)."""
    yaml = """
description: |
  This is a multiline
  description with: colons
  and other special chars!
"""
    result = parse_yaml_subset(yaml)

    expected = "This is a multiline\ndescription with: colons\nand other special chars!"
    assert result['description'] == expected
    print("✅ test_block_scalar_literal passed")


def test_block_scalar_folded():
    """Test block scalar with > (folded)."""
    yaml = """
description: >
  This is a long description
  that spans multiple lines
  but will be folded into one
"""
    result = parse_yaml_subset(yaml)

    # Folded scalars join lines with spaces
    assert 'long description' in result['description']
    assert 'multiple lines' in result['description']
    print("✅ test_block_scalar_folded passed")


def test_full_frontmatter_extraction():
    """Test extracting frontmatter from full markdown."""
    markdown = """---
name: test-skill
version: 1.0.0
description: "Deploy to: production"
tags: [aws, deployment]
---

# Test Skill

This is the body.

## Negative Knowledge

| Attempt | Failure | Solution |
|---------|---------|----------|
| Test    | Failed  | Fixed it |
"""
    metadata, body = extract_frontmatter(markdown)

    assert metadata['name'] == 'test-skill'
    assert metadata['version'] == '1.0.0'
    assert metadata['description'] == 'Deploy to: production'
    assert metadata['tags'] == ['aws', 'deployment']
    assert '# Test Skill' in body
    assert 'Negative Knowledge' in body
    print("✅ test_full_frontmatter_extraction passed")


def test_malformed_frontmatter():
    """Test graceful handling of malformed YAML."""
    # Missing closing ---
    markdown1 = """---
name: test
"""
    metadata1, body1 = extract_frontmatter(markdown1)
    assert metadata1 == {}

    # No frontmatter
    markdown2 = """# Just a heading
No frontmatter here
"""
    metadata2, body2 = extract_frontmatter(markdown2)
    assert metadata2 == {}
    assert body2 == markdown2

    print("✅ test_malformed_frontmatter passed")


def test_complex_nested_structure():
    """Test complex nested structure (future-proofing)."""
    yaml = """
metadata:
  author: "John Doe"
  date: "2024-01-01"

verification:
  tests:
    - unit
    - integration
  config:
    timeout: 30
    retry: true
"""
    result = parse_yaml_subset(yaml)

    # Verify nested structure
    assert 'metadata' in result
    assert isinstance(result['metadata'], dict)
    assert result['metadata']['author'] == 'John Doe'

    assert 'verification' in result
    assert isinstance(result['verification'], dict)
    # Note: nested arrays/objects may not be fully supported yet
    # This test documents current behavior

    print("✅ test_complex_nested_structure passed")


def test_edge_case_colons_everywhere():
    """Test the nightmare scenario: colons everywhere."""
    yaml = """
description: "URL: https://example.com:8080/path?key=value"
command: "ssh user@host:port -p 22"
note: "Format: key:value pairs"
"""
    result = parse_yaml_subset(yaml)

    assert result['description'] == 'URL: https://example.com:8080/path?key=value'
    assert result['command'] == 'ssh user@host:port -p 22'
    assert result['note'] == 'Format: key:value pairs'
    print("✅ test_edge_case_colons_everywhere passed")


def test_real_world_skill_metadata():
    """Test parsing real skill metadata structure."""
    yaml = """
name: git-commit-standards
version: 2.1.0
description: "Use when creating git commits or pull requests. Enforces conventional commit format and atomic change principles."
author: claude
last_verified: 2024-01-15
tags: [git, governance, standards]
allowed-tools: [Bash, Read, Grep]
verification:
  test_script: "tests/skills/test_git_commit.py"
  command: "python3 tests/skills/test_git_commit.py"
  frequency: "on-change"
"""
    result = parse_yaml_subset(yaml)

    # Verify all fields parsed correctly
    assert result['name'] == 'git-commit-standards'
    assert result['version'] == '2.1.0'
    assert 'Use when' in result['description']
    assert result['author'] == 'claude'
    assert result['last_verified'] == '2024-01-15'
    assert result['tags'] == ['git', 'governance', 'standards']
    assert result['allowed-tools'] == ['Bash', 'Read', 'Grep']
    assert isinstance(result['verification'], dict)
    assert result['verification']['test_script'] == 'tests/skills/test_git_commit.py'

    print("✅ test_real_world_skill_metadata passed")


def test_backward_compatibility():
    """Ensure new parser handles all formats from existing skills."""
    # This would test against actual skill files
    # For now, we verify the parser doesn't break on simple cases

    simple_yaml = """
name: simple
description: Simple skill
"""
    result = parse_yaml_subset(simple_yaml)
    assert result['name'] == 'simple'

    quoted_yaml = """
name: "quoted-name"
description: 'single quoted'
"""
    result = parse_yaml_subset(quoted_yaml)
    assert result['name'] == 'quoted-name'
    assert result['description'] == 'single quoted'

    print("✅ test_backward_compatibility passed")


def run_all_tests():
    """Run all test functions."""
    print("\n" + "=" * 60)
    print("🧪 Running YAML Parser Test Suite")
    print("=" * 60 + "\n")

    tests = [
        test_simple_key_value,
        test_quoted_strings_with_colons,
        test_inline_arrays,
        test_multiline_arrays,
        test_nested_objects,
        test_empty_values,
        test_comments,
        test_block_scalar_literal,
        test_block_scalar_folded,
        test_full_frontmatter_extraction,
        test_malformed_frontmatter,
        test_complex_nested_structure,
        test_edge_case_colons_everywhere,
        test_real_world_skill_metadata,
        test_backward_compatibility,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"❌ {test.__name__} failed: {e}")
            failed += 1
        except Exception as e:
            print(f"💥 {test.__name__} crashed: {e}")
            failed += 1

    print("\n" + "=" * 60)
    print(f"📊 Results: {passed} passed, {failed} failed out of {len(tests)} tests")
    print("=" * 60 + "\n")

    return failed == 0


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
