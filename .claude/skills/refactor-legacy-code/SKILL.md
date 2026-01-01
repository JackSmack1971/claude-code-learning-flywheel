---
name: refactor-legacy-code
description: "Use when cleaning up code or moving logic to new files. Enforces Strangler Fig pattern and atomic refactoring to prevent Big Bang rewrites."
author: "Claude Code Learning Flywheel Team"
allowed-tools: ["Read", "Edit", "Bash", "Grep", "Glob"]
version: 1.0.0
last_verified: "2026-01-01"
tags: ["refactoring", "legacy", "strangler-fig", "code-quality"]
related-skills: ["test-driven-workflow", "code-navigation"]
---

# Skill: Refactor Legacy Code

## Purpose
Prevent "Big Bang" rewrites that are impossible to review and inevitably introduce bugs. Enforce the "Strangler Fig" pattern and atomic refactoring steps that preserve behavior while improving code quality.

## 1. Negative Knowledge (Anti-Patterns)

| Failure Pattern | Context | Why It Fails |
| :--- | :--- | :--- |
| Big Bang Rewrite | Changing >200 lines without intermediate tests | PR is unreviewable, high risk of bugs |
| Logic Drift | Changing behavior while refactoring | Violates refactoring definition, breaks existing features |
| Lost Comments | Deleting "why" comments during code moves | Loss of institutional knowledge |
| Premature Abstraction | Creating abstractions before patterns emerge | Over-engineering, complexity without benefit |
| Breaking Tests During Refactor | Tests fail during refactoring process | Violates Red-Green-Refactor cycle |
| No Baseline Tests | Refactoring without existing test coverage | Cannot verify behavior preservation |
| Mixing Refactor and Features | Adding features while refactoring | Can't isolate what caused issues |

## 2. Verified Refactoring Procedure

### The Strangler Fig Pattern

**Concept:** Gradually replace legacy code by growing new code around it, like a strangler fig tree.

```
1. Identify → Target a specific code smell
2. Test → Ensure existing tests cover the area
3. Isolate → Extract the problematic code
4. Replace → Incrementally swap with better implementation
5. Verify → Tests remain green throughout
6. Cleanup → Remove old code only when new code is proven
```

### Phase 1: Establish Safety Net

**Before touching any code, ensure test coverage:**

```bash
# Check current test coverage
npm test -- --coverage

# Target: 80%+ coverage for code you'll refactor
```

If tests are missing, add baseline tests FIRST to document current behavior (even if flawed). See [reference.md](./reference.md) for baseline test examples.

### Phase 2: Identify Code Smells

| Code Smell | Example | Refactoring |
| :--- | :--- | :--- |
| Long Method | Function > 50 lines | Extract Method |
| Large Class | Class > 300 lines | Extract Class |
| Feature Envy | Method uses another class's data heavily | Move Method |
| Duplicate Code | Same logic in multiple places | Extract Function |
| Long Parameter List | Function with >5 parameters | Introduce Parameter Object |
| Primitive Obsession | Using primitives instead of objects | Replace with Value Object |
| Switch Statements | Large switch/case blocks | Replace with Polymorphism |

### Phase 3: Atomic Refactoring Steps

**Rule:** Each refactoring step must keep tests green.

**Workflow for each step:**
1. Apply ONE refactoring technique (e.g., Extract Method)
2. Run tests → Verify all tests PASS
3. Commit with message: `refactor: <specific change>`
4. Repeat for next refactoring

**See [reference.md](./reference.md) for detailed Extract Method example.**

### Phase 4: The Strangler Fig Migration

Use when replacing entire modules or systems:

```
Old System (Legacy)
    ↓
  [Facade Layer] ← New calls go here
    ↓         ↓
  Old Code  New Code
    ↓         ↓
  Gradually migrate traffic (10% → 50% → 100%)
```

**Key steps:**
1. Create facade that routes to old OR new implementation
2. Route all calls through facade
3. Gradually increase percentage to new implementation
4. Remove old code when 100% proven

**See [reference.md](./reference.md) for complete auth migration example.**

### Phase 5: Common Refactoring Techniques

**For detailed code examples, see [reference.md](./reference.md):**

- **Extract Function**: Pull out repeated or complex logic
- **Introduce Parameter Object**: Replace long param lists with object
- **Replace Conditional with Polymorphism**: Replace switch statements with strategy pattern

## 3. Refactoring Workflow for Agents

### When asked to "clean up code" or "refactor":

1. **Read the target code completely**
   - Don't refactor code you haven't read
   - Understand the current behavior
   - Identify dependencies

2. **Check test coverage**
   ```bash
   npm test -- --coverage
   # Must have >80% coverage for target code
   ```

3. **Add missing tests if needed**
   - Document current behavior in tests
   - Tests should pass BEFORE refactoring

4. **Identify ONE code smell to fix**
   - Don't try to fix everything at once
   - Pick the highest-impact smell

5. **Apply ONE atomic refactoring**
   - Extract method, rename variable, etc.
   - ONE change at a time

6. **Run tests**
   ```bash
   npm test
   # Expected: All tests PASS (green)
   ```

7. **Commit**
   ```bash
   git add .
   git commit -m "refactor: <specific change>"
   ```

8. **Repeat steps 4-7**
   - Each commit is a single atomic refactoring
   - Tests stay green throughout

### Example Agent Session

```
User: "Clean up the UserService, it's a mess"

Agent: "I'll refactor UserService using atomic steps."

[READ]
Agent: Reading src/services/UserService.ts...
Found: 350 lines, multiple responsibilities, long methods

[CHECK COVERAGE]
Agent: Running tests with coverage...
Output: UserService has 85% coverage ✓

[IDENTIFY SMELL]
Agent: Identified code smell: Long Method (createUser is 80 lines)
Plan: Extract validation, hashing, and persistence logic

[STEP 1: Extract validation]
Agent: Extracting validateUserInput method...
Running tests... PASS ✓
Committing: "refactor: extract user input validation"

[STEP 2: Extract password hashing]
Agent: Extracting hashPassword method...
Running tests... PASS ✓
Committing: "refactor: extract password hashing logic"

[STEP 3: Extract database save]
Agent: Extracting saveUser method...
Running tests... PASS ✓
Committing: "refactor: extract user persistence logic"

Agent: "Refactoring complete. UserService is now 180 lines with focused methods."
```

## 4. Failed Attempts (Negative Knowledge Evolution)

### ❌ Attempt: Rewrite entire module at once
**Context:** Tried to refactor 500-line file in one go
**Failure:** Introduced 12 new bugs, tests failed, PR rejected
**Learning:** Atomic refactoring only, keep tests green

### ❌ Attempt: Fix bugs while refactoring
**Context:** Found bugs during refactor, fixed them in same commit
**Failure:** Couldn't tell if new test failures were from bugs or refactor
**Learning:** Separate refactoring commits from bug fix commits

### ❌ Attempt: Delete "useless" comments
**Context:** Removed comments that seemed obvious
**Failure:** Lost critical business logic explanations
**Learning:** Preserve "why" comments, only remove "what" comments

### ❌ Attempt: Optimize during refactoring
**Context:** Made code faster while refactoring structure
**Failure:** Couldn't attribute performance gains, risky combination
**Learning:** Refactor for readability first, optimize later

### ❌ Attempt: Skip tests for "trivial" refactorings
**Context:** Renamed variables without running tests
**Failure:** Broke code that depended on variable names (serialization)
**Learning:** ALWAYS run tests, even for "trivial" changes

## 5. Refactoring Checklist

Before marking refactoring as complete, verify:

- [ ] **Behavior Preserved**: All existing tests pass
- [ ] **No Logic Changes**: Only structure changed, not behavior
- [ ] **Tests Still Green**: Run full test suite
- [ ] **Atomic Commits**: Each commit is a single refactoring step
- [ ] **No Feature Additions**: Refactoring-only, no new features
- [ ] **Comments Preserved**: "Why" comments retained
- [ ] **Code Coverage Maintained**: Coverage didn't decrease
- [ ] **Peer Reviewable**: Each commit is small enough to review

## 6. Governance
- **Token Budget:** ~330 lines (within 400 recommended limit)
- **Extended Reference:** See reference.md for detailed code examples and patterns
- **Dependencies:** None (pure refactoring techniques)
- **Pattern Origin:** Martin Fowler's "Refactoring" book, Strangler Fig pattern
- **Maintenance:** Update catalog as new patterns emerge
- **Verification Date:** 2026-01-01
