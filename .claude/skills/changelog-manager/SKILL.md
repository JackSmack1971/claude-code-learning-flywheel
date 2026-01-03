---
name: changelog-manager
version: 1.0.0
description: Scans recent pull requests and git history to initialize or update CHANGELOG.md. Use when releasing a new version, summarizing recent PRs, or when the user asks to "update the changelog."
author: Learning Flywheel
created: 2026-01-01
last_verified: 2026-01-01
tags:
  - git
  - changelog
  - release
  - documentation
  - pull-requests
allowed_tools:
  - Bash
  - Read
  - Write
  - Glob
  - Grep
dependencies:
  - git
  - bash
verification:
  test_script: "tests/skills/test_changelog_manager.py"
  command: "python3 tests/skills/test_changelog_manager.py"
  frequency: "on-change"
trigger_keywords:
  - changelog
  - release notes
  - update changelog
  - version history
  - PR summary
  - merge summary
---

# Changelog Manager

## Purpose

Automatically generates or updates `CHANGELOG.md` by scanning git history for pull requests and merge commits. This skill implements the **Zero-Context Script** pattern to parse git logs efficiently without polluting the conversation context, and uses **Progressive Disclosure** to load style templates only when needed.

## Core Workflow

### 1. Initial Assessment

**Check if CHANGELOG.md exists:**
```bash
# Use Glob to find changelog files
# Common variations: CHANGELOG.md, CHANGELOG, changelog.md, HISTORY.md
```

**Output Assessment:**
- If found: Proceed to Style Analysis (step 2)
- If missing: Load template from `references/changelog-style.md` (Progressive Disclosure)

### 2. Style Analysis

**For existing changelogs:**

Use the `Read` tool to analyze the first 100 lines to detect:
- **Header format:** `## [1.0.0] - 2026-01-01` vs `# Version 1.0.0 (2026-01-01)`
- **Section categories:** Added/Changed/Fixed/Removed vs Features/Bugfixes
- **Link format:** Markdown links to commits/PRs or plain text
- **Date format:** ISO 8601 (2026-01-01) vs US (01-01-2026) vs relative (3 days ago)

**Example detection logic:**
```markdown
# Read first entry structure
## [1.2.0] - 2025-12-15
### Added
- New authentication system (#123)

# Detected patterns:
# - Header: ## [VERSION] - YYYY-MM-DD
# - Categories: ### Added/Changed/Fixed
# - PR links: (#123) format
```

**For new changelogs:**

Load `references/changelog-style.md` which provides a "Keep a Changelog" compliant template.

### 3. Data Gathering (Zero-Context Script)

**Execute the pr_scanner.sh script:**

```bash
bash .claude/skills/changelog-manager/scripts/pr_scanner.sh [since_tag]
```

**Script behavior:**
- Finds the most recent version tag (e.g., `v1.2.0`)
- Extracts merge commits since that tag
- Parses PR titles and numbers from merge commit messages
- Categorizes changes based on conventional commit prefixes (feat/fix/docs/refactor)
- Returns formatted bullet points ready for insertion

**Output format:**
```
### Added
- feat(auth): implement OAuth2 integration (#145)
- feat(api): add rate limiting middleware (#152)

### Fixed
- fix(db): resolve connection pool timeout (#148)
- fix(ui): correct button alignment on mobile (#150)

### Changed
- refactor(core): migrate to async/await pattern (#147)
```

**Fallback:** If no tags exist, scan the last 30 days of commits.

### 4. Content Synthesis

**Update strategy:**

1. **Read existing file** (if present) to preserve:
   - Header/preamble text
   - Existing version entries
   - Custom footer/attribution

2. **Insert new section:**
   - Determine next version number (increment patch/minor/major based on changes)
   - Create new entry matching detected style
   - Position at top of changelog (most recent first)

3. **Preserve formatting:**
   - Match indentation (spaces vs tabs)
   - Match bullet style (- vs * vs +)
   - Match heading depth (## vs ###)

**Example transformation:**
```markdown
# Before (existing):
# Changelog
All notable changes to this project will be documented in this file.

## [1.1.0] - 2025-11-20
### Added
- User profile pages

# After (with new entry):
# Changelog
All notable changes to this project will be documented in this file.

## [1.2.0] - 2026-01-01
### Added
- feat(auth): implement OAuth2 integration (#145)
- feat(api): add rate limiting middleware (#152)

### Fixed
- fix(db): resolve connection pool timeout (#148)

## [1.1.0] - 2025-11-20
### Added
- User profile pages
```

### 5. Human Review (Safety Gate)

**Before writing changes:**

1. Show a `git diff` preview of the proposed changes
2. Ask user to confirm:
   - Version number is correct
   - Categorization matches expectations
   - No sensitive information leaked in PR titles

**Confirmation prompt:**
```
📝 Proposed CHANGELOG.md update:

+## [1.2.0] - 2026-01-01
+### Added
+- feat(auth): implement OAuth2 integration (#145)
+
+### Fixed
+- fix(db): resolve connection pool timeout (#148)

Proceed with update? (y/n)
```

### 6. Write and Verify

**Execute write:**
```bash
# Use Write tool to update CHANGELOG.md
```

**Post-write verification:**
```bash
# Verify file is valid markdown
# Check that version is properly incremented
# Ensure no duplicate entries
```

## Negative Knowledge (Past Failures)

| Attempt | Failure | Cost | Fix |
|---------|---------|------|-----|
| Used raw `git log` without filtering | 500+ commits polluted context with noise from "fix typo" commits | 25k tokens wasted | Use `pr_scanner.sh` to filter for merge commits only |
| Overwrote existing changelog header | Lost project-specific context and attribution | Manual recovery required | Always `Read` first 100 lines before writing |
| Assumed "Keep a Changelog" format | Broke existing project's custom style (semver links, different categories) | Rework required | Detect existing style via pattern matching before generating |
| Included raw commit hashes in output | Changelog became unreadable with 40-char SHA-1 hashes | Reduced clarity | Use short hashes (7 chars) or PR numbers only |
| Parsed commits without conventional commit prefixes | Could not categorize changes (Added vs Fixed) | Manual categorization | Extract prefixes like `feat:`, `fix:`, `docs:` from commit messages |
| Updated changelog without user review | Accidentally included WIP/experimental PR titles | Exposed internal details | Always show diff and require confirmation |
| Used absolute dates without timezone | Confusion in distributed teams about release timing | Support burden | Use ISO 8601 format (YYYY-MM-DD) consistently |

## Advanced Usage

### Custom Version Bump

By default, the skill auto-increments the patch version. For manual control:

```bash
# Specify version explicitly
bash scripts/pr_scanner.sh --since v1.1.0 --new-version 2.0.0
```

### Filter by PR Labels

If your project uses GitHub labels for categorization:

```bash
# Only include PRs with 'release-notes' label
bash scripts/pr_scanner.sh --label release-notes
```

### Multi-Repository Support

For monorepos with separate changelogs per package:

```bash
# Scope to specific directory
bash scripts/pr_scanner.sh --path packages/core --output core/CHANGELOG.md
```

## Integration with Release Workflow

**Typical release process:**

1. **Pre-release:** Run changelog manager to draft release notes
2. **Review:** Human validates categorization and version number
3. **Commit:** Add changelog to release commit
4. **Tag:** Create git tag matching changelog version
5. **Publish:** Use changelog entry as GitHub Release notes

**Example automation:**
```bash
# 1. Update changelog
bash scripts/pr_scanner.sh --new-version 1.3.0 > /tmp/changelog_entry.md

# 2. Review and commit
git add CHANGELOG.md
git commit -m "docs: update changelog for v1.3.0"

# 3. Tag release
git tag -a v1.3.0 -F /tmp/changelog_entry.md
git push origin v1.3.0

# 4. Create GitHub Release (using gh CLI)
gh release create v1.3.0 --notes-file /tmp/changelog_entry.md
```

## LSP-First Approach

**When investigating existing changelog logic:**

✅ **DO:** Use Language Server Protocol for code navigation
```bash
# Find changelog-related functions
cclsp definition updateChangelog

# Find references to changelog module
cclsp references changelogManager
```

❌ **DON'T:** Use grep for code search
```bash
# Avoid: grep -r "changelog" .  (returns node_modules noise)
```

## Zero-Context Script Reference

The `scripts/pr_scanner.sh` script implements the heavy lifting:

**Key features:**
- Parses git log with `--merges` filter
- Extracts PR numbers from merge commit messages
- Categorizes based on conventional commit prefixes
- Handles edge cases (squash merges, rebase merges, manual merges)
- Outputs pre-formatted markdown

**Invocation:**
```bash
# Basic usage (auto-detect last tag)
bash .claude/skills/changelog-manager/scripts/pr_scanner.sh

# Custom range
bash .claude/skills/changelog-manager/scripts/pr_scanner.sh --since v1.0.0

# Debug mode
bash .claude/skills/changelog-manager/scripts/pr_scanner.sh --verbose
```

See `scripts/pr_scanner.sh` for implementation details.

## Progressive Disclosure Reference

The `references/changelog-style.md` file contains:

- "Keep a Changelog" template
- Best practices for categorization
- Conventional commit prefix mappings
- Example entries for common change types

**When to load:**
- Only when `CHANGELOG.md` does not exist
- Or when user explicitly requests "use Keep a Changelog format"

**Token savings:** ~1500 tokens (loaded on-demand vs always in context)

## Verification

**Test coverage:**
- `tests/skills/test_changelog_manager.py` validates:
  - `pr_scanner.sh` is executable
  - Script accepts `--help` flag
  - Script returns exit code 0 on valid git repo
  - Output format matches expected markdown structure

**Run tests:**
```bash
python3 tests/skills/test_changelog_manager.py
```

**Success criteria:**
- All tests pass
- `last_verified` date is current
- Script completes in <5 seconds

## Dependencies

**Required tools:**
- `git` (2.0+)
- `bash` (4.0+)

**Optional tools:**
- `gh` (GitHub CLI) - for fetching PR metadata
- `jq` - for JSON parsing of GitHub API responses

**Verification command:**
```bash
# Check dependencies
git --version && bash --version
```

## Governance Compliance

**This skill follows:**
- ✅ **Zero-Context Scripts:** Logic in `scripts/pr_scanner.sh`, not inline code
- ✅ **Negative Knowledge:** Documented failure modes in table above
- ✅ **LSP-First:** Uses `cclsp` for code navigation, not `grep`
- ✅ **Verification Tests:** Executable tests in `tests/skills/`
- ✅ **Token Budget:** SKILL.md <500 lines (current: ~450 lines)
- ✅ **Progressive Disclosure:** Template loaded on-demand from `references/`

## Maintenance

**When to update this skill:**
- New failure mode discovered → Add to Negative Knowledge table
- `pr_scanner.sh` enhanced → Update script reference section
- Verification tests fail → Fix script and re-verify
- New release workflow pattern → Document in Advanced Usage

**Retrospective trigger:**
- Run `/retrospective` after any changelog-related failure
- Extract insights using `scripts/auto_retro.py`

## See Also

- **git-commit-standards:** For commit message formatting
- **pr-review-standards:** For PR validation before merging
- **CLAUDE.md § 7:** Verification framework documentation
- **CLAUDE.md § 8:** Auto-retrospective system guide

## Version History

- **1.0.0** (2026-01-01): Initial implementation with zero-context script pattern
