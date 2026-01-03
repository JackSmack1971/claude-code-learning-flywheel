# Changelog Style Guide

## Purpose

This reference provides a **"Keep a Changelog"** compliant template for generating new `CHANGELOG.md` files. It is loaded via **Progressive Disclosure** only when no existing changelog is detected, saving ~1500 tokens in normal operation.

## Template

```markdown
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- New features go here

### Changed
- Changes to existing functionality

### Deprecated
- Soon-to-be removed features

### Removed
- Removed features

### Fixed
- Bug fixes

### Security
- Security vulnerability fixes

## [1.0.0] - 2026-01-01

### Added
- Initial release

[Unreleased]: https://github.com/user/repo/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/user/repo/releases/tag/v1.0.0
```

## Category Definitions

### Added
For new features or functionality.

**Examples:**
- feat(auth): implement OAuth2 integration (#145)
- feat(api): add GraphQL endpoint for user queries (#152)
- feat(ui): create dark mode toggle (#158)

**Conventional Commit Prefixes:** `feat:`

### Changed
For changes in existing functionality (not bug fixes).

**Examples:**
- refactor(core): migrate from callbacks to async/await (#147)
- perf(db): optimize query performance with indexes (#153)
- style(ui): update button styles to match design system (#160)

**Conventional Commit Prefixes:** `refactor:`, `perf:`, `style:`, `chore:` (when user-facing)

### Deprecated
For soon-to-be removed features (with migration path).

**Examples:**
- deprecate(api): mark `/v1/users` endpoint for removal in v2.0 (#149)
- deprecate(config): old YAML config format (use JSON) (#155)

**Conventional Commit Prefixes:** `deprecate:` (or note in commit message)

### Removed
For removed features (breaking changes).

**Examples:**
- remove(api): delete deprecated `/v1/auth` endpoint (#151)
- remove(deps): drop support for Node.js 12 (#156)

**Conventional Commit Prefixes:** `remove:`, `feat!:` (breaking), `chore!:`

### Fixed
For bug fixes.

**Examples:**
- fix(db): resolve connection pool timeout issue (#148)
- fix(ui): correct button alignment on mobile devices (#150)
- fix(auth): handle expired tokens gracefully (#154)

**Conventional Commit Prefixes:** `fix:`

### Security
For security vulnerability fixes (should be highlighted).

**Examples:**
- security(auth): patch XSS vulnerability in login form (#157)
- security(deps): upgrade lodash to fix prototype pollution (CVE-2020-8203)

**Conventional Commit Prefixes:** `security:`, `fix:` (with CVE reference)

## Conventional Commit Mapping

| Prefix | Category | Notes |
|--------|----------|-------|
| `feat:` | Added | New features |
| `fix:` | Fixed | Bug fixes |
| `docs:` | (omit) | Documentation changes (not user-facing) |
| `style:` | Changed | UI/UX changes (if user-facing) |
| `refactor:` | Changed | Code restructuring (if user-facing) |
| `perf:` | Changed | Performance improvements |
| `test:` | (omit) | Test changes (not user-facing) |
| `chore:` | (omit) | Maintenance tasks (not user-facing) |
| `security:` | Security | Vulnerability fixes |
| `deprecate:` | Deprecated | Feature deprecation |
| `remove:` | Removed | Feature removal |
| `feat!:` | Removed | Breaking changes (new feature) |
| `fix!:` | Removed | Breaking changes (bug fix) |

**Note:** The `!` suffix indicates a breaking change (MAJOR version bump).

## Version Numbering

Follow **Semantic Versioning** (SemVer):

```
MAJOR.MINOR.PATCH

MAJOR: Breaking changes (API changes, removed features)
MINOR: New features (backward-compatible additions)
PATCH: Bug fixes (backward-compatible fixes)
```

**Examples:**
- `1.0.0` → `1.0.1` (bug fix)
- `1.0.1` → `1.1.0` (new feature)
- `1.1.0` → `2.0.0` (breaking change)

## Date Format

Use **ISO 8601** format: `YYYY-MM-DD`

**Examples:**
- ✅ `2026-01-01`
- ✅ `2025-12-15`
- ❌ `01-01-2026` (US format, ambiguous)
- ❌ `1st January 2026` (verbose, inconsistent)

## Link Format

**Semantic diff links:**

```markdown
[Unreleased]: https://github.com/user/repo/compare/v1.2.0...HEAD
[1.2.0]: https://github.com/user/repo/compare/v1.1.0...v1.2.0
[1.1.0]: https://github.com/user/repo/releases/tag/v1.1.0
```

**PR reference format:**

```markdown
- feat(auth): implement OAuth2 (#145)
  ^           ^                   ^
  |           |                   PR number (links to GitHub)
  |           Description
  Conventional commit prefix
```

**Rendering:**
- On GitHub: `(#145)` auto-links to PR
- Elsewhere: Add explicit link: `([#145](https://github.com/user/repo/pull/145))`

## Best Practices

### 1. Write for Humans, Not Machines

**Bad:**
```markdown
- fix(db): update query.js line 47 to use parameterized statement
```

**Good:**
```markdown
- fix(db): prevent SQL injection in user search (#148)
```

### 2. Group Related Changes

**Bad:**
```markdown
### Added
- feat(ui): add button (#1)
- feat(api): add endpoint (#2)
- feat(ui): add modal (#3)
```

**Good:**
```markdown
### Added
- feat(ui): add button and modal components (#1, #3)
- feat(api): add user authentication endpoint (#2)
```

### 3. Highlight Breaking Changes

**Use bold or special formatting:**

```markdown
### Removed
- **BREAKING:** remove deprecated `/v1/auth` endpoint (#151)
  - Migration: Use `/v2/oauth` instead
```

### 4. Include Migration Paths

**For breaking changes:**

```markdown
### Changed
- **BREAKING:** rename `getUser()` to `fetchUser()` (#159)
  - **Migration:** Find-replace `getUser(` → `fetchUser(` in your codebase
```

### 5. Link to Documentation

**For complex features:**

```markdown
### Added
- feat(api): add GraphQL support (#152)
  - See [GraphQL Migration Guide](docs/graphql.md) for details
```

## Anti-Patterns to Avoid

### ❌ Overly Technical Language

**Bad:**
```markdown
- refactor(core): replace EventEmitter with RxJS Subject
```

**Good:**
```markdown
- improve(core): enhance event handling performance (#147)
```

### ❌ Commit Hashes Instead of PR Numbers

**Bad:**
```markdown
- fix(db): resolve timeout (a3f5c21)
```

**Good:**
```markdown
- fix(db): resolve connection timeout (#148)
```

**Why:** PR numbers link to discussions, commits are just code.

### ❌ Duplicate Information

**Bad:**
```markdown
### Added
- Added new authentication system
- New authentication system added
```

**Good:**
```markdown
### Added
- Implement OAuth2 authentication (#145)
```

### ❌ Missing Context

**Bad:**
```markdown
- fix(ui): fix bug
```

**Good:**
```markdown
- fix(ui): correct button alignment on mobile devices (#150)
```

## Example: Full Changelog Entry

```markdown
## [1.3.0] - 2026-01-15

### Added
- feat(auth): implement OAuth2 with Google and GitHub providers (#145)
- feat(api): add rate limiting middleware (100 req/min) (#152)
- feat(ui): create dark mode with persistent preferences (#158)

### Changed
- refactor(core): migrate to async/await pattern for better readability (#147)
- perf(db): optimize user queries with composite indexes (3x faster) (#153)

### Fixed
- fix(db): resolve connection pool timeout on high traffic (#148)
- fix(ui): correct button alignment on mobile devices (#150)
- fix(auth): handle expired tokens gracefully without crashes (#154)

### Security
- security(auth): patch XSS vulnerability in login form (#157)

[1.3.0]: https://github.com/user/repo/compare/v1.2.0...v1.3.0
```

## When to Deviate from This Template

**It's acceptable to use a different format if:**

1. **Project has existing conventions:**
   - Detect and match the existing style
   - Consistency within a project > global standards

2. **Team preferences:**
   - Some teams prefer Features/Bugfixes over Added/Fixed
   - Some use release dates in headers, others don't

3. **Tool integration:**
   - GitHub Releases may require specific formatting
   - Automated changelog generators (conventional-changelog, etc.)

**Rule:** Always analyze existing `CHANGELOG.md` first (if present) before applying this template.

## Token Budget

**This file:**
- ~1500 tokens (loaded only when needed)

**Savings:**
- Not loaded when existing changelog detected
- Progressive Disclosure reduces average context usage

## See Also

- [Keep a Changelog](https://keepachangelog.com/) - Original specification
- [Semantic Versioning](https://semver.org/) - Version numbering rules
- [Conventional Commits](https://www.conventionalcommits.org/) - Commit message format
- **git-commit-standards** skill - For commit message validation
- **pr-review-standards** skill - For PR title formatting
