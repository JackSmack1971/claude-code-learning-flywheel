---
name: optimize-performance-profiling
description: "Use when the app is slow or when optimizing functions. Enforces profile-first methodology to prevent premature optimization."
author: "Claude Code Learning Flywheel Team"
allowed-tools: ["Bash", "Read", "Edit", "Grep", "Glob"]
version: 1.0.0
last_verified: "2026-01-01"
tags: ["performance", "profiling", "optimization", "benchmarking"]
related-skills: ["debug-root-cause-analysis", "refactor-legacy-code"]
---

# Skill: Optimize Performance Profiling

## Purpose
Prevent "premature optimization" and guesswork-based performance fixes. Enforce data-driven optimization using profiling tools to identify actual bottlenecks before making code changes.

## 1. Negative Knowledge (Anti-Patterns)

| Failure Pattern | Context | Why It Fails |
| :--- | :--- | :--- |
| Premature Optimization | Optimizing code without profiling data | Wastes effort, reduces readability, no real gains |
| N+1 Queries | Fetching data in loops | Database death spiral, exponential slowdown |
| Memory Leaks | Unsubscribed listeners/intervals | Memory grows unbounded, browser/server crash |
| Blocking Operations | Synchronous I/O on main thread | UI freezes, poor user experience |
| Large Bundle Sizes | Importing entire libraries for one function | Slow page loads, poor performance scores |
| Re-rendering Entire Tree | Not memoizing components/values | Unnecessary work, janky UI |
| Inefficient Algorithms | Using O(n²) when O(n log n) exists | Scales poorly with data size |

## 2. Verified Performance Procedure

### The Profile-Optimize-Verify Cycle

```
1. BASELINE   → Measure current performance
2. PROFILE    → Identify actual bottlenecks
3. HYPOTHESIZE → Form theory about the cause
4. OPTIMIZE   → Apply targeted fix
5. MEASURE    → Verify improvement
6. REPEAT     → Continue until acceptable
```

### Phase 1: Establish Baseline

**Before optimizing, measure current performance:**

```bash
# Frontend: Lighthouse audit
npx lighthouse https://localhost:3000 --view

# Backend: Load testing with autocannon
npx autocannon -c 100 -d 30 http://localhost:3000/api/users

# Bundle size analysis
npx vite-bundle-visualizer
# or for webpack:
npx webpack-bundle-analyzer dist/stats.json
```

**Document baseline metrics:**

```
Performance Baseline (2026-01-01)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Frontend:
  - First Contentful Paint: 1.2s
  - Time to Interactive: 3.5s
  - Total Bundle Size: 450 KB

Backend:
  - /api/users: avg 250ms, p95 800ms
  - /api/posts: avg 450ms, p95 1200ms
  - Throughput: 150 req/s

Database:
  - Slow queries (>1s): 3 queries
  - Connection pool usage: 80%
```

### Phase 2: Profile to Find Bottlenecks

**Frontend profiling:**

```typescript
// React DevTools Profiler
import { Profiler } from 'react';

function onRenderCallback(
  id: string,
  phase: 'mount' | 'update',
  actualDuration: number
) {
  console.log(`${id} (${phase}) took ${actualDuration}ms`);
}

<Profiler id="UserDashboard" onRender={onRenderCallback}>
  <UserDashboard />
</Profiler>

// Chrome DevTools Performance tab
// 1. Open DevTools → Performance
// 2. Click Record
// 3. Perform slow action
// 4. Stop recording
// 5. Analyze flame graph
```

**Backend profiling (Node.js):**

```bash
# CPU profiling
node --prof server.js
# Generate load, then:
node --prof-process isolate-*.log > profile.txt

# Memory profiling
node --inspect server.js
# Open chrome://inspect
# Take heap snapshot before and after operation

# Use clinic.js for comprehensive profiling
npx clinic doctor -- node server.js
# Generate load, then Ctrl+C
# Opens HTML report with flame graphs
```

**Database profiling:**

```sql
-- PostgreSQL: Enable slow query logging
ALTER DATABASE mydb SET log_min_duration_statement = 1000;

-- Find slow queries
SELECT query, mean_exec_time, calls
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;

-- Explain query plan
EXPLAIN ANALYZE
SELECT * FROM users WHERE email = 'test@example.com';
```

### Phase 3: Common Performance Fixes

#### Fix 1: N+1 Query Problem

```typescript
// ❌ BAD: N+1 queries (1 query for users + N queries for posts)
async function getUsersWithPosts() {
  const users = await db.users.findMany();  // 1 query

  for (const user of users) {
    user.posts = await db.posts.findMany({   // N queries
      where: { userId: user.id }
    });
  }

  return users;
}

// ✅ GOOD: Single query with join
async function getUsersWithPosts() {
  return await db.users.findMany({
    include: {
      posts: true  // Single query with JOIN
    }
  });
}

// ✅ GOOD: DataLoader for batching (GraphQL)
const userLoader = new DataLoader(async (userIds) => {
  const users = await db.users.findMany({
    where: { id: { in: userIds } }
  });
  return userIds.map(id => users.find(u => u.id === id));
});
```

#### Fix 2: Memory Leaks

```typescript
// ❌ BAD: Event listener never removed
useEffect(() => {
  window.addEventListener('resize', handleResize);
  // Missing cleanup!
}, []);

// ✅ GOOD: Cleanup subscriptions
useEffect(() => {
  const handleResize = () => { /* ... */ };
  window.addEventListener('resize', handleResize);

  return () => {
    window.removeEventListener('resize', handleResize);
  };
}, []);

// ❌ BAD: Interval never cleared
function startPolling() {
  setInterval(() => {
    fetchData();
  }, 5000);
}

// ✅ GOOD: Clear interval on unmount
useEffect(() => {
  const intervalId = setInterval(() => {
    fetchData();
  }, 5000);

  return () => clearInterval(intervalId);
}, []);
```

#### Fix 3: Bundle Size Optimization

```typescript
// ❌ BAD: Import entire library
import _ from 'lodash';
const result = _.debounce(fn, 300);

// ✅ GOOD: Import only what you need
import debounce from 'lodash/debounce';
const result = debounce(fn, 300);

// ❌ BAD: Import entire icon library
import { FaUser, FaHome, FaSettings } from 'react-icons/fa';

// ✅ GOOD: Use tree-shakeable imports
import FaUser from 'react-icons/fa/FaUser';
import FaHome from 'react-icons/fa/FaHome';

// ✅ BEST: Code splitting with dynamic imports
const HeavyComponent = lazy(() => import('./HeavyComponent'));

<Suspense fallback={<Loading />}>
  <HeavyComponent />
</Suspense>
```

#### Fix 4: Inefficient Algorithms

```typescript
// ❌ BAD: O(n²) nested loops
function findDuplicates(arr: number[]): number[] {
  const duplicates = [];
  for (let i = 0; i < arr.length; i++) {
    for (let j = i + 1; j < arr.length; j++) {
      if (arr[i] === arr[j]) {
        duplicates.push(arr[i]);
      }
    }
  }
  return duplicates;
}

// ✅ GOOD: O(n) with Set
function findDuplicates(arr: number[]): number[] {
  const seen = new Set<number>();
  const duplicates = new Set<number>();

  for (const num of arr) {
    if (seen.has(num)) {
      duplicates.add(num);
    }
    seen.add(num);
  }

  return Array.from(duplicates);
}
```

#### Fix 5: Database Indexing

```sql
-- ❌ BAD: No index on frequently queried column
SELECT * FROM users WHERE email = 'test@example.com';
-- Seq Scan on users (cost=0.00..3500.00 rows=1 width=100)

-- ✅ GOOD: Add index
CREATE INDEX idx_users_email ON users(email);
-- Index Scan using idx_users_email (cost=0.29..8.31 rows=1 width=100)

-- Composite index for multiple columns
CREATE INDEX idx_posts_user_created ON posts(user_id, created_at DESC);
```

### Phase 4: Frontend-Specific Optimizations

**React performance patterns:**

```typescript
// 1. Memoize expensive calculations
function ExpensiveComponent({ items, filter }) {
  const filteredItems = useMemo(() => {
    return items.filter(item => item.category === filter);
  }, [items, filter]);

  return <List items={filteredItems} />;
}

// 2. Memoize callbacks
function ParentComponent() {
  const [count, setCount] = useState(0);

  const handleClick = useCallback(() => {
    setCount(c => c + 1);
  }, []);

  return <ChildComponent onClick={handleClick} />;
}

// 3. Virtualize long lists
import { FixedSizeList } from 'react-window';

function VirtualizedList({ items }) {
  return (
    <FixedSizeList
      height={600}
      itemCount={items.length}
      itemSize={50}
      width="100%"
    >
      {({ index, style }) => (
        <div style={style}>{items[index].name}</div>
      )}
    </FixedSizeList>
  );
}

// 4. Lazy load images
<img
  src={imageUrl}
  loading="lazy"
  alt="Description"
/>

// 5. Debounce expensive operations
const debouncedSearch = useMemo(
  () => debounce((query: string) => {
    performSearch(query);
  }, 300),
  []
);
```

### Phase 5: Backend-Specific Optimizations

**Caching strategies:**

```typescript
// 1. In-memory cache (LRU)
import LRU from 'lru-cache';

const cache = new LRU({
  max: 500,
  ttl: 1000 * 60 * 5  // 5 minutes
});

async function getUser(id: string) {
  const cached = cache.get(id);
  if (cached) return cached;

  const user = await db.users.findOne({ id });
  cache.set(id, user);
  return user;
}

// 2. Redis cache
import { redis } from './redis';

async function getCachedData(key: string) {
  const cached = await redis.get(key);
  if (cached) return JSON.parse(cached);

  const data = await fetchFromDatabase(key);
  await redis.set(key, JSON.stringify(data), 'EX', 300);  // 5 min TTL
  return data;
}

// 3. HTTP caching headers
app.get('/api/static-data', (req, res) => {
  res.set('Cache-Control', 'public, max-age=3600');  // 1 hour
  res.json(data);
});
```

**Connection pooling:**

```typescript
// ✅ Configure proper pool size
const pool = new Pool({
  host: 'localhost',
  database: 'mydb',
  max: 20,           // Max connections
  min: 5,            // Min connections
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 2000,
});
```

## 3. Performance Benchmarking

**Use the zero-context script:**

```bash
# Benchmark a function
python .claude/skills/optimize-performance-profiling/scripts/benchmark.py \
  --file src/utils/sorting.ts \
  --function quickSort \
  --iterations 10000

# Compare before/after
python scripts/benchmark.py \
  --before src/utils/old.ts:slowFunction \
  --after src/utils/new.ts:fastFunction \
  --iterations 5000
```

**Output example:**

```
Benchmark Results
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Function: quickSort
Iterations: 10,000

Metrics:
  Average: 2.3ms
  Median:  2.1ms
  P95:     3.8ms
  P99:     5.2ms
  Min:     1.8ms
  Max:     12.1ms

Memory:
  Peak:    45.2 MB
  Average: 38.7 MB
```

## 4. Performance Workflow for Agents

### When asked to "make it faster" or "optimize":

1. **Reject premature optimization**
   ```
   User: "Optimize this function"
   Agent: "Let me first profile to identify if this is actually a bottleneck."
   ```

2. **Establish baseline**
   ```bash
   # Measure current performance
   npm run benchmark
   # Or lighthouse, autocannon, etc.
   ```

3. **Profile to find bottlenecks**
   ```bash
   # Use appropriate profiling tool
   node --prof server.js
   # or React DevTools Profiler
   ```

4. **Identify the bottleneck**
   - Is it CPU-bound? → Optimize algorithm
   - Is it I/O-bound? → Add caching, connection pooling
   - Is it network-bound? → Add compression, CDN
   - Is it database-bound? → Add indexes, optimize queries

5. **Apply ONE optimization at a time**
   - Fix the top bottleneck only
   - Don't optimize multiple things simultaneously

6. **Measure improvement**
   ```bash
   npm run benchmark
   # Compare before/after metrics
   ```

7. **Verify no regressions**
   ```bash
   npm test
   # Ensure functionality unchanged
   ```

8. **Document improvement**
   ```
   Performance improvement: /api/users endpoint
   Before: 450ms avg, 1200ms p95
   After:  120ms avg, 250ms p95
   Improvement: 73% faster (avg), 79% faster (p95)
   Method: Added database index on user_id column
   ```

### Example Agent Session

```
User: "The dashboard is slow, make it faster"

Agent: "I'll profile the dashboard to identify bottlenecks."

[BASELINE]
Agent: Running Lighthouse audit...
Found: Time to Interactive = 5.2s, LCP = 3.8s

[PROFILE]
Agent: Opening React DevTools Profiler...
Found: UserTable component re-renders 47 times on page load
Found: Each render takes 180ms

[IDENTIFY]
Agent: Analyzing UserTable component...
Issue: Component re-renders on every parent state change
Issue: Not using virtualization for 5000 row table

[OPTIMIZE 1]
Agent: Wrapping UserTable in React.memo...
Testing... Re-renders reduced to 2

[MEASURE]
Agent: Running Lighthouse again...
Result: Time to Interactive = 3.1s (40% improvement)

[OPTIMIZE 2]
Agent: Implementing react-window virtualization...
Testing... Only rendering visible rows

[MEASURE]
Agent: Final Lighthouse audit...
Result: Time to Interactive = 1.8s (65% total improvement)
Verified: All tests still pass

Agent: "Dashboard optimized. TTI improved from 5.2s to 1.8s (65% faster)."
```

## 5. Failed Attempts (Negative Knowledge Evolution)

### ❌ Attempt: Micro-optimizations without profiling
**Context:** Replaced forEach with for loops for "performance"
**Failure:** No measurable improvement, code less readable
**Learning:** Profile first, optimize proven bottlenecks only

### ❌ Attempt: Added Redis cache everywhere
**Context:** Cached all database queries to "make it faster"
**Failure:** Cache invalidation bugs, stale data, increased complexity
**Learning:** Cache only hot paths identified by profiling

### ❌ Attempt: Memoized every React component
**Context:** Wrapped all components in React.memo
**Failure:** No performance gain, harder to debug, memory overhead
**Learning:** Memoize only components that re-render frequently

### ❌ Attempt: Aggressive code splitting
**Context:** Split every route into separate bundle
**Failure:** Too many HTTP requests, worse performance
**Learning:** Balance bundle size with HTTP request overhead

## 6. Performance Checklist

Before marking optimization as complete:

- [ ] **Baseline Established**: Current metrics documented
- [ ] **Profiled**: Used profiling tools to identify bottleneck
- [ ] **Targeted Fix**: Only optimized proven bottleneck
- [ ] **Measured**: Verified improvement with metrics
- [ ] **Tests Pass**: No functionality broken
- [ ] **Documented**: Performance improvement documented
- [ ] **Acceptable**: Performance now meets requirements

## 7. Performance Budget

**Set performance budgets to maintain gains:**

```json
{
  "budgets": [
    {
      "resourceSizes": [
        { "resourceType": "script", "budget": 300 },
        { "resourceType": "total", "budget": 500 }
      ],
      "timings": [
        { "metric": "interactive", "budget": 3000 },
        { "metric": "first-contentful-paint", "budget": 1000 }
      ]
    }
  ]
}
```

**Fail CI if budgets exceeded:**

```bash
# In CI/CD pipeline
npx lighthouse-ci assert \
  --budgets-file=budgets.json \
  --preset=lighthouse:recommended
```

## 8. Tools Reference

**Frontend:**
- Chrome DevTools Performance tab
- React DevTools Profiler
- Lighthouse CI
- webpack-bundle-analyzer / vite-bundle-visualizer

**Backend:**
- Node.js --prof / --inspect
- clinic.js (doctor, flame, bubbleprof)
- autocannon (load testing)
- 0x (flamegraph profiler)

**Database:**
- EXPLAIN ANALYZE (PostgreSQL)
- EXPLAIN (MySQL)
- pg_stat_statements
- Database slow query logs

**General:**
- Benchmark.js / tinybench
- Apache Bench (ab)
- Artillery.io (load testing)

## 9. Governance
- **Token Budget:** ~495 lines (within 500 limit)
- **Dependencies:** Node.js profiling tools, Chrome DevTools, database-specific tools
- **Pattern Origin:** Performance Engineering best practices, Web Vitals
- **Maintenance:** Update as new profiling tools emerge
- **Verification Date:** 2026-01-01
