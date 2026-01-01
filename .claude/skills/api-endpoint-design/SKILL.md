---
name: api-endpoint-design
description: "Use when designing API endpoints. Enforces layered architecture, separation of concerns, and type safety. Supports Express.js and similar frameworks."
author: "Claude Code Learning Flywheel Team"
allowed-tools: ["Read", "Write", "Edit", "Grep", "Glob"]
version: 1.0.0
last_verified: "2026-01-01"
tags: ["api", "architecture", "backend", "best-practices"]
related-skills: ["test-driven-workflow"]
---

# Skill: API Endpoint Design

## Purpose
Ensure consistency in backend service construction. Prevent "Context Rot" by keeping the agent aligned with established architectural patterns.

## 1. Negative Knowledge (Anti-Patterns)

| Approach | Failure Mode | Why It Fails |
| :--- | :--- | :--- |
| Putting logic in controllers | Hard to test, violates SoC | Business logic becomes coupled to HTTP layer |
| Returning raw DB objects | Exposes internal schema | Security risk, tight coupling to DB structure |
| Direct DB queries in routes | Untestable, non-reusable | Cannot mock for tests, duplicated queries |
| Missing input validation | Runtime errors, security holes | Invalid data reaches business logic |
| Generic error responses | Poor developer experience | Clients can't distinguish error types |
| No request/response types | Type safety lost | Runtime errors, maintenance burden |
| Mixing authentication in business logic | Tight coupling | Auth changes require business logic updates |

## 2. Verified Architecture Pattern

### Layer Separation
```
Request → Route → Middleware → Controller → Service → Repository → Database
                     ↓            ↓           ↓
                  Auth/Validation  DTOs    Business Logic
```

### Responsibilities
- **Routes** (`src/routes/v1/`): Define endpoints and HTTP methods only
- **Middleware**: Handle cross-cutting concerns (auth, logging, validation)
- **Controllers**: Orchestrate request/response flow, call services
- **Services** (`src/services/`): Implement business logic
- **Repositories** (`src/repositories/`): Database access layer
- **DTOs** (`src/dtos/`): Request/Response data transfer objects

## 3. Verified Procedure

### Step 1: Define Route
```typescript
// src/routes/v1/users.ts
import { Router } from 'express';
import { validateRequest } from '@/middleware/validation';
import { UserController } from '@/controllers/UserController';
import { CreateUserDto } from '@/dtos/user.dto';

const router = Router();
const controller = new UserController();

router.post(
  '/',
  validateRequest(CreateUserDto),
  controller.createUser
);

export default router;
```

### Step 2: Define DTOs
```typescript
// src/dtos/user.dto.ts
import { z } from 'zod';

export const CreateUserDto = z.object({
  email: z.string().email(),
  name: z.string().min(1).max(100),
  role: z.enum(['admin', 'user']).default('user')
});

export const UserResponseDto = z.object({
  id: z.string(),
  email: z.string(),
  name: z.string(),
  role: z.string(),
  createdAt: z.date()
});

export type CreateUserInput = z.infer<typeof CreateUserDto>;
export type UserResponse = z.infer<typeof UserResponseDto>;
```

### Step 3: Implement Service Layer
```typescript
// src/services/UserService.ts
import { UserRepository } from '@/repositories/UserRepository';
import type { CreateUserInput, UserResponse } from '@/dtos/user.dto';

export class UserService {
  constructor(private userRepo: UserRepository) {}

  async createUser(input: CreateUserInput): Promise<UserResponse> {
    // Business logic here
    const existingUser = await this.userRepo.findByEmail(input.email);
    if (existingUser) {
      throw new Error('User already exists');
    }

    const user = await this.userRepo.create(input);

    // Return DTO, not raw DB object
    return {
      id: user.id,
      email: user.email,
      name: user.name,
      role: user.role,
      createdAt: user.createdAt
    };
  }
}
```

### Step 4: Implement Controller
```typescript
// src/controllers/UserController.ts
import { Request, Response, NextFunction } from 'express';
import { UserService } from '@/services/UserService';

export class UserController {
  constructor(private userService: UserService) {}

  createUser = async (req: Request, res: Response, next: NextFunction) => {
    try {
      // Input already validated by middleware
      const user = await this.userService.createUser(req.body);
      res.status(201).json(user);
    } catch (error) {
      next(error); // Let error handler middleware deal with it
    }
  };
}
```

## 4. Validation Requirements

### MUST Have
- ✅ Input validation using schema library (zod, joi, yup)
- ✅ DTO types for all request/response payloads
- ✅ Service layer for business logic
- ✅ Error handling middleware
- ✅ Authentication middleware (where required)

### MUST NOT Have
- ❌ Business logic in route handlers
- ❌ Direct DB access in controllers
- ❌ Raw DB objects in responses
- ❌ Hardcoded connection strings
- ❌ Inline validation logic (use schemas)

## 5. Failed Attempts (Negative Knowledge Evolution)

### ❌ Attempt: Shared service instances
**Context:** Created singleton services to "optimize" memory
**Failure:** State leakage between requests, race conditions
**Learning:** Use dependency injection, instantiate per-request or use stateless services

### ❌ Attempt: Generic CRUD endpoints
**Context:** Built generic "resource" endpoints to reduce boilerplate
**Failure:** Lost type safety, complex special cases, security issues
**Learning:** Explicit endpoints are better than "clever" generic ones

### ❌ Attempt: Validation in service layer
**Context:** Put validation logic inside services
**Failure:** Services harder to test, validation bypassed in some paths
**Learning:** Validate at the boundary (middleware) before data enters system

## 6. Checklist for New Endpoints

Before marking an endpoint "done," verify:

- [ ] Route defined in appropriate `src/routes/v1/<resource>.ts`
- [ ] DTOs defined with schema validation (zod/joi)
- [ ] Business logic in service layer, not controller
- [ ] Controller only orchestrates, no business logic
- [ ] Error handling uses centralized error middleware
- [ ] Authentication/authorization middleware applied (if needed)
- [ ] Response uses DTO types, not raw DB objects
- [ ] Tests written for service layer
- [ ] API documentation updated (OpenAPI/Swagger)

## 7. Governance
- **Token Budget:** ~400 lines (within 500 limit)
- **Dependencies:** Express.js (adaptable to Fastify, Koa, etc.)
- **Pattern Origin:** Clean Architecture + Layered Architecture
- **Maintenance:** Update pattern if new architectural decisions are made
- **Verification Date:** 2026-01-01
