---
name: audit-security-dependencies
description: "Use when adding packages, bumping versions, or responding to security alerts. Enforces supply chain security and vulnerability remediation."
author: "Claude Code Learning Flywheel Team"
allowed-tools: ["Bash", "Read", "Edit", "Grep", "Glob"]
version: 1.0.0
last_verified: "2026-01-01"
tags: ["security", "dependencies", "supply-chain", "cve"]
related-skills: ["pr-review-standards"]
---

# Skill: Audit Security Dependencies

## Purpose
Prevent supply chain vulnerabilities and dependency bloat. Enforce rigorous security checks before adding or updating packages, preventing the introduction of known CVEs or malicious dependencies.

## 1. Negative Knowledge (Anti-Patterns)

| Failure Pattern | Context | Why It Fails |
| :--- | :--- | :--- |
| Blind Upgrades | `npm update` without checking breaking changes | Production outage, unexpected behavior |
| Vulnerable Versions | Installing packages with known CVEs | Security breach, data exposure |
| Scope Creep | Adding heavy library for single utility function | Bundle bloat, performance degradation |
| Unvetted Packages | Installing packages without checking reputation | Malicious code, supply chain attack |
| Ignoring Peer Warnings | Installing despite peer dependency conflicts | Runtime errors, incompatibilities |
| Outdated Dependencies | Never updating dependencies | Accumulating security debt |
| Dev Deps in Production | Including devDependencies in production builds | Larger bundle, potential vulnerabilities |

## 2. Verified Security Procedure

### Phase 1: Before Adding a New Package

**Research the package first:**

```bash
# Check package metadata
npm view <package-name>

# Check weekly downloads (higher = more trusted)
npm view <package-name> dist.tarball | head -n 1

# Check last publish date (recently maintained?)
npm view <package-name> time

# Check for known vulnerabilities
npm audit --audit-level=moderate
```

**Evaluate the package:**

| Criteria | Good Sign | Red Flag |
| :--- | :--- | :--- |
| Downloads/week | >100k | <1k |
| Last publish | <6 months ago | >2 years ago |
| GitHub stars | >1k | <50 |
| Open issues | <50 | >500 unresolved |
| License | MIT, Apache-2.0, BSD | Unlicensed, Custom |
| Maintainers | >2 active | Single maintainer, inactive |
| Dependencies | <10 | >50 (dependency hell) |

**Run security check:**

```bash
# Use the zero-context script
python .claude/skills/audit-security-dependencies/scripts/check_cves.py \
  --package <package-name> \
  --severity high
```

### Phase 2: Installing a Package

**Install with explicit version:**

```bash
# ❌ BAD: Install latest without pinning
npm install lodash

# ✅ GOOD: Pin to specific version
npm install lodash@4.17.21

# Check what was actually installed
npm list lodash
```

**Verify package contents:**

```bash
# Check package.json for suspicious scripts
cat node_modules/<package-name>/package.json

# Look for postinstall scripts (potential malware vector)
grep -i "postinstall\|preinstall" node_modules/<package-name>/package.json
```

**Run security audit:**

```bash
# Check for vulnerabilities
npm audit

# Fix auto-fixable vulnerabilities
npm audit fix

# Review what will be changed
npm audit fix --dry-run
```

### Phase 3: Updating Dependencies

**Check for breaking changes before updating:**

```bash
# Check outdated packages
npm outdated

# For major version updates, read CHANGELOG
npm view <package-name> versions
# Visit GitHub releases page to read breaking changes
```

**Update process:**

```
1. Update ONE package at a time
2. Read the changelog/migration guide
3. Update the package
4. Run tests
5. Commit
6. Repeat for next package
```

**Example workflow:**

```bash
# Step 1: Check what's outdated
npm outdated
# Output: react 17.0.2 → 18.2.0 (major update)

# Step 2: Read migration guide
# Visit: https://react.dev/blog/2022/03/08/react-18-upgrade-guide

# Step 3: Update
npm install react@18.2.0 react-dom@18.2.0

# Step 4: Run tests
npm test
# Fix any breaking changes

# Step 5: Run app locally
npm run dev
# Verify app works

# Step 6: Commit
git add package.json package-lock.json
git commit -m "deps: upgrade react 17 → 18"
```

### Phase 4: Responding to Security Alerts

**When you receive a security alert:**

```bash
# 1. Assess severity
npm audit

# 2. Understand the vulnerability
# Read the CVE details in the audit output

# 3. Check if fix is available
npm audit fix --dry-run

# 4. Apply fix if safe
npm audit fix

# 5. If no auto-fix, update manually
npm install <package>@<safe-version>

# 6. If no safe version, consider alternatives
npm uninstall <vulnerable-package>
npm install <alternative-package>
```

**Severity levels:**

| Level | Action Required | Timeline |
| :--- | :--- | :--- |
| Critical | Immediate fix | Same day |
| High | Urgent fix | Within 1 week |
| Moderate | Scheduled fix | Within 1 month |
| Low | Next maintenance window | Opportunistic |

### Phase 5: Dependency Hygiene

**Regular maintenance tasks:**

```bash
# Check for unused dependencies
npx depcheck

# Remove unused dependencies
npm uninstall <unused-package>

# Check for duplicate dependencies (bundle bloat)
npm dedupe

# Verify lockfile integrity
npm ci
```

**Lockfile discipline:**

```
✅ DO:
- Commit package-lock.json / yarn.lock
- Use `npm ci` in CI/CD (not `npm install`)
- Update lockfile with every dependency change

❌ DON'T:
- Delete lockfile to "fix" issues
- Edit lockfile manually
- Use different package managers in same project
```

## 3. Zero-Context Scripts

### check_cves.py

Located at: `.claude/skills/audit-security-dependencies/scripts/check_cves.py`

**Purpose:** Check npm/pip packages for known CVEs with strict thresholds.

**Usage:**
```bash
# Check a specific package
python check_cves.py --package express --severity high

# Check all dependencies
python check_cves.py --check-all --severity moderate

# Get JSON report
python check_cves.py --check-all --format json
```

**Output:**
```
Security Audit Report
═══════════════════════════════════════
Package: express
Version: 4.16.0

⚠️  HIGH SEVERITY VULNERABILITIES FOUND: 2

CVE-2022-24999: Regular Expression Denial of Service
  Severity: High
  Fixed in: 4.17.3
  Description: The qs module before 6.10.3 has a ReDoS vulnerability

CVE-2024-29041: Path Traversal
  Severity: High
  Fixed in: 4.19.2
  Description: Express allows attackers to traverse the filesystem

RECOMMENDATION: Upgrade to express@4.19.2 or later

Exit code: 1 (vulnerabilities found)
```

## 4. Dependency Decision Tree

**When considering adding a dependency:**

```
Is it a trivial utility (<20 lines of code)?
├─ YES → Write it yourself (avoid leftpad syndrome)
└─ NO → Continue

Does it have >100k weekly downloads?
├─ NO → Research thoroughly, consider alternatives
└─ YES → Continue

Has it been updated in the last 6 months?
├─ NO → Consider if maintained, check for forks
└─ YES → Continue

Does it have known HIGH or CRITICAL CVEs?
├─ YES → Find alternative or wait for patch
└─ NO → Continue

Does it add <100KB to bundle size?
├─ NO → Evaluate if worth the bloat
└─ YES → Safe to add (still run audit)
```

## 5. Common Scenarios

### Scenario 1: Security Alert in Production

```bash
# 1. Assess impact
npm audit --production

# 2. Check if vulnerability affects your usage
# Read CVE details carefully

# 3. Test fix in development
git checkout -b fix/security-vulnerability
npm audit fix

# 4. Run full test suite
npm test

# 5. Deploy fix urgently
git commit -m "security: fix CVE-2024-XXXXX in package-name"
git push
# Create PR with "security" label for expedited review
```

### Scenario 2: No Safe Version Available

```bash
# Option 1: Find alternative package
npm uninstall vulnerable-package
npm install safe-alternative

# Option 2: Vendor the code (if small enough)
mkdir -p vendor/package-name
cp -r node_modules/package-name/src vendor/package-name
# Update imports to use vendored version

# Option 3: Fork and patch
git clone https://github.com/author/package-name
cd package-name
# Apply security fix
# Publish to npm under @your-org/package-name
```

### Scenario 3: Dependency Conflict

```bash
# Check dependency tree
npm ls <package-name>

# If peer dependency conflict:
npm install --legacy-peer-deps  # temporary workaround

# Better solution: Update packages to compatible versions
npm install package-a@latest package-b@latest
```

## 6. Approved Package Lists

**Utility libraries (prefer these over adding new ones):**

- **Date/Time:** `date-fns` (not moment.js - unmaintained)
- **HTTP Client:** `axios` or native `fetch`
- **Validation:** `zod` or `yup`
- **Testing:** `vitest` or `jest`
- **Logging:** `pino` or `winston`

**Red flags (avoid these):**

- Packages with `eval()` or `Function()` in their code
- Packages requesting unnecessary permissions
- Typosquatting variations of popular packages
- Packages with obfuscated code
- Newly created packages with high version numbers (v10.0.0 on day 1)

## 7. Failed Attempts (Negative Knowledge Evolution)

### ❌ Attempt: Auto-update all dependencies weekly
**Context:** Set up automated PRs to update all deps
**Failure:** Breaking changes broke production 3 times
**Learning:** Update dependencies deliberately, read changelogs

### ❌ Attempt: Ignore low severity CVEs
**Context:** Only fixed high/critical vulnerabilities
**Failure:** Low severity CVEs were chained for exploit
**Learning:** Fix all CVEs, not just high severity

### ❌ Attempt: Add packages for single functions
**Context:** Installed `is-even` for a single check
**Failure:** Added 5 dependencies for 1 line of code
**Learning:** Write simple utilities yourself

### ❌ Attempt: Use wildcard versions
**Context:** Set `"express": "*"` in package.json
**Failure:** Got major version update, broke app
**Learning:** Always pin versions, use exact or ~tilde

## 8. Security Checklist

Before committing dependency changes:

- [ ] **Audit Clean**: `npm audit` shows no high/critical vulnerabilities
- [ ] **Tests Pass**: Full test suite passes
- [ ] **Bundle Size**: Check bundle size didn't increase unreasonably
- [ ] **Lockfile Updated**: package-lock.json is committed
- [ ] **Changelog Read**: For major updates, read migration guide
- [ ] **Alternatives Considered**: Evaluated if package is necessary
- [ ] **License Compatible**: Package license is compatible with project
- [ ] **Maintainer Vetted**: Package is actively maintained

## 9. Tools & Commands Reference

```bash
# Check for vulnerabilities
npm audit
npm audit --production  # Only production deps

# Fix vulnerabilities
npm audit fix
npm audit fix --force  # Apply breaking changes (risky)

# Check outdated packages
npm outdated

# Check package info
npm view <package> versions
npm view <package> repository
npm view <package> license

# Analyze bundle size
npx bundlephobia <package>@<version>

# Check for unused dependencies
npx depcheck

# Verify lockfile integrity
npm ci  # Clean install from lockfile

# List dependency tree
npm ls
npm ls --depth=0  # Top-level only
npm ls <package>  # Where is this package used?
```

## 10. Governance
- **Token Budget:** ~490 lines (within 500 limit)
- **Dependencies:** Python 3.8+ for CVE checking script, npm/pip
- **Pattern Origin:** OWASP Top 10, Supply Chain Security Best Practices
- **Maintenance:** Update vulnerability patterns monthly
- **Verification Date:** 2026-01-01
