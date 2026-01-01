# Learning Flywheel Governance Scripts

This directory contains Zero-Context Scripts that enforce governance rules for the Learning Flywheel architecture.

## Scripts

### `validate_memory.py` - Skill Validation Engine

Validates SKILL.md files against governance rules to prevent context degradation and maintain knowledge quality.

**Features:**
- ✅ Robust YAML frontmatter parsing (handles edge cases, quoted strings, colons in values)
- ✅ Semantic versioning enforcement (requires version bump when Negative Knowledge changes)
- ✅ Context budget enforcement (500-line hard limit, 400-line recommended)
- ✅ Negative Knowledge validation (ensures failures are documented)
- ✅ Skill freshness tracking (flags stale skills not verified in 180 days)

**Usage:**
```bash
# Validate all skills
python scripts/validate_memory.py

# Validate specific skill
python scripts/validate_memory.py --skill .claude/skills/deploy-aws/SKILL.md

# Strict mode (warnings become errors)
python scripts/validate_memory.py --strict

# Show statistics only
python scripts/validate_memory.py --stats
```

**Exit Codes:**
- `0`: All validations passed
- `1`: Validation failed (errors found)

---

### `detect_conflicts.py` - Semantic Conflict Detector

Detects semantic overlap between skills using TF-IDF and Jaccard similarity to prevent the "confused agent" problem.

**Features:**
- ✅ Robust YAML frontmatter parsing (same improvements as validate_memory.py)
- ✅ Improved tokenization that preserves coding symbols (@, -, _, .)
- ✅ TF-IDF + Cosine Similarity for semantic overlap detection
- ✅ Jaccard Similarity for trigger term overlap
- ✅ Tool permission conflict detection
- ✅ Registry generation for disambiguation

**Usage:**
```bash
# Check all skills for conflicts
python scripts/detect_conflicts.py

# Custom similarity threshold (0.0-1.0)
python scripts/detect_conflicts.py --threshold 0.65

# Strict mode (fail build on conflicts)
python scripts/detect_conflicts.py --strict

# Generate registry.yaml for disambiguation
python scripts/detect_conflicts.py --update-registry
```

**Exit Codes:**
- `0`: No conflicts or conflicts found (non-strict mode)
- `1`: Conflicts found (strict mode)

---

## Pre-commit Hook

The `.githooks/pre-commit` hook automatically validates staged SKILL.md files before commit.

**Setup:**
```bash
# Already configured if you cloned this repo
git config core.hooksPath .githooks
```

**What it does:**
1. Detects staged SKILL.md files
2. Runs `validate_memory.py --strict` on each
3. Blocks commit if validation fails
4. Provides clear error messages with fix instructions

**Bypass (NOT recommended):**
```bash
git commit --no-verify
```

---

## Governance Improvements (2026-01-01)

### 1. Robust YAML Parsing
**Problem:** Original parser would crash on edge cases:
- Colons in values (e.g., `description: "Deploy to AWS: Production"`)
- Missing spaces after colons
- Malformed arrays

**Solution:** New parser handles:
- Quoted strings with colons
- Empty/null values
- Robust array parsing
- Per-line error handling (skips malformed lines)

### 2. Semantic Versioning Enforcement
**Problem:** Skills could update Negative Knowledge without bumping version, causing "silent updates" where behavior changes but version doesn't.

**Solution:**
- Compares current vs. previous (git HEAD) Negative Knowledge section
- If changed, REQUIRES version bump
- Fails validation with clear error message

**Example Error:**
```
❌ GOVERNANCE VIOLATION: Negative Knowledge section changed but version not bumped (still 1.0.0).
   Bump version to signal knowledge update.
```

### 3. Improved Tokenization
**Problem:** Naive tokenizer stripped coding symbols, causing false positives:
- `api-endpoint` became `api endpoint`
- `.py` files lost extension
- `@property` decorators lost context

**Solution:** Preserve coding-relevant symbols:
- Hyphens for kebab-case (`api-endpoint`)
- Underscores for snake_case (`user_auth`)
- Periods for extensions (`.py`, `config.json`)
- At-signs for decorators (`@property`)

### 4. Pre-commit Hook
**Problem:** Invalid YAML and oversized skills could enter the repository, poisoning the knowledge base.

**Solution:**
- Automatic validation before commit
- Only validates staged files (efficient)
- Strict mode enabled (warnings = errors)
- Clear error messages with bypass instructions

---

## Design Principles

### Zero-Context Execution
These scripts use **stdlib only** (no dependencies) to run in lightweight CI/CD environments without `pip install` overhead.

**Why?**
- Faster execution (no dependency resolution)
- Fewer security vulnerabilities (no supply chain risk)
- Portable (runs anywhere Python 3.8+ exists)

### Precision Over Generality
The scripts are **surgical** - they solve specific problems with minimal complexity:
- TF-IDF from scratch (avoids 500MB+ sklearn dependency)
- Manual YAML parser (avoids pyyaml dependency)
- Direct git subprocess calls (avoids gitpython dependency)

### Fail-Safe Design
Scripts are designed to **fail gracefully**:
- Invalid YAML lines are skipped (not fatal)
- Git errors don't crash validation (e.g., new files)
- Timeouts on subprocess calls (5 seconds max)
- Clear error messages for debugging

---

## Testing

Run tests manually:

```bash
# Test validation on all skills
python scripts/validate_memory.py

# Test conflict detection
python scripts/detect_conflicts.py

# Test pre-commit hook (stage a SKILL.md file first)
git add .claude/skills/*/SKILL.md
git commit -m "test"
```

---

## Future Improvements

1. **Semantic Skill Retrieval** (`scripts/retrieve_skills.py`)
   - Takes user query
   - Runs TF-IDF against local skill database
   - Returns only relevant SKILL.md files
   - Changes complexity from O(N) context usage to O(1)

2. **Automatic Version Bump**
   - Detect Negative Knowledge changes
   - Auto-increment patch version
   - Update frontmatter automatically

3. **Context Budget Dashboard**
   - Visual dashboard of skill sizes
   - Trend analysis (growing/shrinking)
   - Alert when approaching limits

4. **Conflict Resolution Suggestions**
   - AI-powered merge suggestions
   - Automatic `allowed-tools` differentiation
   - Description refinement prompts

---

## Maintenance

After significant changes to skills:
1. Run `/retrospective` to extract insights
2. Update relevant SKILL.md with Negative Knowledge
3. Bump version in frontmatter
4. Commit (pre-commit hook validates automatically)

**Validation Cadence:**
- Pre-commit: Automatic (staged files only)
- CI/CD: Run on all skills in pipeline
- Manual: Before major refactors or deployments

---

## References

- **Architecture:** `/CLAUDE.md` (Project Memory Tier 2)
- **Governance Rules:** `.claude/rules/*.md` (Auto-loaded)
- **Skills Library:** `.claude/skills/` (Capability Library)
