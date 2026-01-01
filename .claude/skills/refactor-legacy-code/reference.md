# Refactor Legacy Code - Extended Reference

This document contains detailed code examples and patterns referenced in the main SKILL.md file.

## Atomic Refactoring Examples

### Extract Method Refactoring

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

## The Strangler Fig Migration Pattern

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

### Example: Replacing Legacy Authentication

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

## Refactoring Catalog

### Extract Function

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

### Introduce Parameter Object

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

### Replace Conditional with Polymorphism

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

## Baseline Test Examples

If tests are missing, add them FIRST:

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

## Common Code Smells and Refactorings

| Code Smell | Example | Refactoring |
| :--- | :--- | :--- |
| Long Method | Function > 50 lines | Extract Method |
| Large Class | Class > 300 lines | Extract Class |
| Feature Envy | Method uses another class's data heavily | Move Method |
| Duplicate Code | Same logic in multiple places | Extract Function |
| Long Parameter List | Function with >5 parameters | Introduce Parameter Object |
| Primitive Obsession | Using primitives instead of objects | Replace with Value Object |
| Switch Statements | Large switch/case blocks | Replace with Polymorphism |
