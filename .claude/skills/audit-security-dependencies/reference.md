# Audit Security Dependencies - Extended Reference

This document contains detailed scenarios, package lists, and command references for the main SKILL.md file.

## Common Scenarios

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

## Approved Package Lists

**Utility libraries (prefer these over adding new ones):**

- **Date/Time:** `date-fns` (not moment.js - unmaintained)
- **HTTP Client:** `axios` or native `fetch`
- **Validation:** `zod` or `yup`
- **Testing:** `vitest` or `jest`
- **Logging:** `pino` or `winston`
- **UUID Generation:** `uuid`
- **Deep Copy:** `structuredClone` (native) or `lodash/cloneDeep`
- **Debounce/Throttle:** `lodash/debounce`, `lodash/throttle`

**Red flags (avoid these):**

- Packages with `eval()` or `Function()` in their code
- Packages requesting unnecessary permissions
- Typosquatting variations of popular packages
- Packages with obfuscated code
- Newly created packages with high version numbers (v10.0.0 on day 1)
- Packages with no TypeScript definitions
- Packages with >100 dependencies
- Packages not updated in >2 years (unless extremely stable like lodash)

## Tools & Commands Reference

### NPM Security Commands

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
npm view <package> dist.tarball  # Check download stats

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

# View package details
npm view <package>
npm info <package>

# Check package download stats
npm view <package> dist.tarball
```

### Yarn Security Commands

```bash
# Check for vulnerabilities
yarn audit

# Fix vulnerabilities
yarn audit --fix

# Check outdated packages
yarn outdated

# Upgrade interactive
yarn upgrade-interactive

# Check why a package is installed
yarn why <package>

# Verify lockfile integrity
yarn install --frozen-lockfile
```

### pnpm Security Commands

```bash
# Check for vulnerabilities
pnpm audit

# Fix vulnerabilities
pnpm audit --fix

# Check outdated packages
pnpm outdated

# Update packages
pnpm update

# Check dependency tree
pnpm list
pnpm why <package>
```

### Python (pip) Security Commands

```bash
# Check for vulnerabilities (requires pip-audit)
pip install pip-audit
pip-audit

# Check outdated packages
pip list --outdated

# Update a package
pip install --upgrade <package>

# Check package info
pip show <package>

# Generate requirements with versions
pip freeze > requirements.txt

# Verify package checksums
pip install --require-hashes -r requirements.txt
```

### Security Scanning Tools

```bash
# Snyk (comprehensive security scanner)
npm install -g snyk
snyk test
snyk monitor

# Socket.dev (supply chain security)
npx socket npm <package>

# npm-check (interactive updater)
npx npm-check -u

# lighthouse (for frontend bundles)
npx lighthouse <url> --only-categories=performance

# webpack-bundle-analyzer
npx webpack-bundle-analyzer dist/stats.json

# source-map-explorer (for bundle analysis)
npx source-map-explorer 'dist/**/*.js'
```

## Package Evaluation Checklist

Before installing a new package, check:

| Criteria | How to Check | Good Sign | Red Flag |
| :--- | :--- | :--- | :--- |
| Downloads | `npm view <pkg> dist.tarball` | >100k/week | <1k/week |
| Last Update | `npm view <pkg> time` | <6 months ago | >2 years |
| GitHub Stars | Visit repo | >1k stars | <50 stars |
| Open Issues | Visit repo | <50 open | >500 open |
| License | `npm view <pkg> license` | MIT, Apache | Unlicensed |
| Maintainers | `npm view <pkg> maintainers` | >2 active | Single, inactive |
| Dependencies | `npm view <pkg> dependencies` | <10 deps | >50 deps |
| Bundle Size | `npx bundlephobia <pkg>` | <50KB | >500KB |
| Has Types | Check package | .d.ts files | No types |
| Security Audits | `npm audit` after install | No vulns | High/Critical vulns |

## Dependency Update Strategy

### Semantic Versioning Quick Reference

```
Version: MAJOR.MINOR.PATCH (e.g., 2.4.1)

MAJOR: Breaking changes
MINOR: New features (backwards compatible)
PATCH: Bug fixes (backwards compatible)

^ (caret): Allow MINOR and PATCH updates
  ^2.4.1 → Allows 2.x.x (but not 3.0.0)

~ (tilde): Allow PATCH updates only
  ~2.4.1 → Allows 2.4.x (but not 2.5.0)

Exact: No automatic updates
  2.4.1 → Only 2.4.1
```

### Update Frequency Recommendations

| Dependency Type | Update Frequency | Strategy |
| :--- | :--- | :--- |
| Security patches | Immediately | Auto-apply patches |
| Framework core (React, Vue) | Every 3-6 months | Read migration guides |
| Utilities (lodash, date-fns) | Every 6-12 months | Low risk, update in batches |
| Build tools (webpack, vite) | Every 6 months | Test thoroughly |
| Testing libraries | Every 3-6 months | Update with framework |
| Dev dependencies | Every 6-12 months | Lower priority |

## License Compatibility

**Compatible with most projects:**
- MIT
- Apache 2.0
- BSD (2-clause, 3-clause)
- ISC

**Requires attribution:**
- Apache 2.0 (requires NOTICE file)
- BSD-3-Clause (requires attribution)

**Copyleft (may require source disclosure):**
- GPL (v2, v3)
- LGPL
- AGPL

**Avoid in proprietary projects:**
- GPL (without permission)
- AGPL (especially for web services)

Check license compatibility:
```bash
npx license-checker --summary
```
