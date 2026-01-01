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

# Identify gaps in coverage for the target area
# Target: 80%+ coverage for code you'll refactor
```

**If tests are missing, add them FIRST:**

```typescript
// tests/unit/services/LegacyUserService.test.ts
describe('LegacyUserService (baseline tests)', () => {
  it('should create user with existing behavior', async () => {
    // Document current behavior, even if flawed
    const service = new LegacyUserService();
    const user = await service.createUser({
      name: 'Test',
      email: 'test@example.com'
    });

    expect(user).toMatchObject({
      name: 'Test',
      email: 'test@example.com'
    });
  });

  // Test ALL current behaviors, including quirks
  it('should handle empty name (current behavior)', async () => {
    const service = new LegacyUserService();
    const user = await service.createUser({
      name: '',
      email: 'test@example.com'
    });

    // Document that current code allows empty names
    expect(user.name).toBe('');
  });
});
```

### Phase 2: Identify Code Smells

**Common smells to target:**

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

#### Example: Extract Method Refactoring

**BEFORE (Long Method):**
```typescript
// src/services/OrderService.ts
class OrderService {
  async processOrder(orderId: string) {
    // 80 lines of code doing everything...
    const order = await db.orders.findOne({ id: orderId });

    // Validate order (15 lines)
    if (!order) throw new Error('Order not found');
    if (order.status !== 'pending') throw new Error('Invalid status');
    if (order.items.length === 0) throw new Error('Empty order');

    // Calculate total (20 lines)
    let total = 0;
    for (const item of order.items) {
      const price = await this.getItemPrice(item.id);
      const discount = this.calculateDiscount(item, order.customer);
      total += price * item.quantity - discount;
    }

    // Process payment (25 lines)
    const payment = await this.paymentGateway.charge({
      amount: total,
      customerId: order.customerId,
      currency: 'USD'
    });

    // Update inventory (20 lines)
    for (const item of order.items) {
      await db.inventory.decrement(item.id, item.quantity);
    }

    return { orderId, payment, total };
  }
}
```

**STEP 1: Extract validation method**
```typescript
class OrderService {
  async processOrder(orderId: string) {
    const order = await db.orders.findOne({ id: orderId });
    this.validateOrder(order);  // Extracted

    // ... rest of the code unchanged
  }

  private validateOrder(order: Order | null): asserts order is Order {
    if (!order) throw new Error('Order not found');
    if (order.status !== 'pending') throw new Error('Invalid status');
    if (order.items.length === 0) throw new Error('Empty order');
  }
}
```

**Run tests:**
```bash
npm test -- OrderService.test.ts
# Expected: PASS (all green)
```

**Commit:**
```bash
git add src/services/OrderService.ts
git commit -m "refactor: extract order validation to separate method"
```

**STEP 2: Extract total calculation**
```typescript
class OrderService {
  async processOrder(orderId: string) {
    const order = await db.orders.findOne({ id: orderId });
    this.validateOrder(order);

    const total = await this.calculateOrderTotal(order);  // Extracted

    // ... payment and inventory code
  }

  private async calculateOrderTotal(order: Order): Promise<number> {
    let total = 0;
    for (const item of order.items) {
      const price = await this.getItemPrice(item.id);
      const discount = this.calculateDiscount(item, order.customer);
      total += price * item.quantity - discount;
    }
    return total;
  }
}
```

**Run tests → Commit → Continue...**

**AFTER (final state):**
```typescript
class OrderService {
  async processOrder(orderId: string) {
    const order = await this.getAndValidateOrder(orderId);
    const total = await this.calculateOrderTotal(order);
    const payment = await this.processPayment(order, total);
    await this.updateInventory(order);

    return { orderId, payment, total };
  }

  // Each extracted method is small, focused, testable
  private async getAndValidateOrder(orderId: string): Promise<Order> { ... }
  private async calculateOrderTotal(order: Order): Promise<number> { ... }
  private async processPayment(order: Order, total: number): Promise<Payment> { ... }
  private async updateInventory(order: Order): Promise<void> { ... }
}
```

### Phase 4: The Strangler Fig Migration

**Use when replacing entire modules or systems:**

```
Old System (Legacy)
    ↓
  [Facade Layer] ← New calls go here
    ↓         ↓
  Old Code  New Code
    ↓         ↓
  Gradually migrate traffic →
```

**Example: Replacing legacy authentication**

**STEP 1: Create facade**
```typescript
// src/services/AuthService.ts (new facade)
export class AuthService {
  private legacyAuth = new LegacyAuthService();
  private newAuth = new ModernAuthService();

  async authenticate(credentials: Credentials): Promise<User> {
    // Feature flag to gradually shift traffic
    if (await this.shouldUseNewAuth(credentials.userId)) {
      return this.newAuth.authenticate(credentials);
    }
    return this.legacyAuth.authenticate(credentials);
  }

  private async shouldUseNewAuth(userId: string): Promise<boolean> {
    // Gradual rollout: 10% → 50% → 100%
    const rolloutPercentage = await this.config.get('new_auth_rollout');
    const userHash = hashUserId(userId);
    return userHash % 100 < rolloutPercentage;
  }
}
```

**STEP 2: Route all calls through facade**
```typescript
// Before: Direct legacy calls
const user = await legacyAuth.authenticate(creds);

// After: Through facade
const user = await authService.authenticate(creds);
```

**STEP 3: Increase rollout percentage**
```
Week 1: 10% of users on new system
Week 2: 25% of users
Week 3: 50% of users
Week 4: 100% of users
```

**STEP 4: Remove legacy code**
```typescript
// Once new system is proven at 100%
export class AuthService {
  private auth = new ModernAuthService();

  async authenticate(credentials: Credentials): Promise<User> {
    return this.auth.authenticate(credentials);
  }
}
```

### Phase 5: Refactoring Catalog

**Common refactoring techniques (apply atomically):**

#### Extract Function
```typescript
// Before
function processUser(user) {
  if (user.age < 18 || user.age > 120) throw new Error('Invalid age');
  // ... more code
}

// After
function processUser(user) {
  validateAge(user.age);
  // ... more code
}

function validateAge(age: number) {
  if (age < 18 || age > 120) throw new Error('Invalid age');
}
```

#### Introduce Parameter Object
```typescript
// Before
function createUser(name: string, email: string, age: number, country: string, timezone: string) {
  // ...
}

// After
interface UserParams {
  name: string;
  email: string;
  age: number;
  country: string;
  timezone: string;
}

function createUser(params: UserParams) {
  // ...
}
```

#### Replace Conditional with Polymorphism
```typescript
// Before
class PaymentProcessor {
  process(payment: Payment) {
    switch (payment.type) {
      case 'credit_card':
        return this.processCreditCard(payment);
      case 'paypal':
        return this.processPaypal(payment);
      case 'crypto':
        return this.processCrypto(payment);
    }
  }
}

// After
interface PaymentMethod {
  process(payment: Payment): Promise<Result>;
}

class CreditCardPayment implements PaymentMethod { ... }
class PaypalPayment implements PaymentMethod { ... }
class CryptoPayment implements PaymentMethod { ... }

class PaymentProcessor {
  private methods: Map<string, PaymentMethod> = new Map([
    ['credit_card', new CreditCardPayment()],
    ['paypal', new PaypalPayment()],
    ['crypto', new CryptoPayment()],
  ]);

  process(payment: Payment) {
    const method = this.methods.get(payment.type);
    return method.process(payment);
  }
}
```

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
Plan: Extract validation, extraction, and persistence logic

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
**Failure:** Couldn't tell if new tests failures were from bugs or refactor
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
- **Token Budget:** ~490 lines (within 500 limit)
- **Dependencies:** None (pure refactoring techniques)
- **Pattern Origin:** Martin Fowler's "Refactoring" book, Strangler Fig pattern
- **Maintenance:** Update catalog as new patterns emerge
- **Verification Date:** 2026-01-01
