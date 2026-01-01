# Performance Optimization - Extended Reference

This document contains detailed code examples, optimization patterns, and tooling references for the main SKILL.md file.

## Common Performance Fixes

### Fix 1: N+1 Query Problem

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

### Fix 2: Memory Leaks

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

### Fix 3: Bundle Size Optimization

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

### Fix 4: Inefficient Algorithms

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

### Fix 5: Database Indexing

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

## Frontend-Specific Optimizations

### React Performance Patterns

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

## Backend-Specific Optimizations

### Caching Strategies

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

### Connection Pooling

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

## Performance Budget

Set performance budgets to maintain gains:

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

Fail CI if budgets exceeded:

```bash
# In CI/CD pipeline
npx lighthouse-ci assert \
  --budgets-file=budgets.json \
  --preset=lighthouse:recommended
```

## Tools Reference

### Frontend Tools

- **Chrome DevTools Performance tab**: Record and analyze runtime performance
- **React DevTools Profiler**: Identify slow-rendering components
- **Lighthouse CI**: Automated performance audits
- **webpack-bundle-analyzer**: Visualize bundle composition
- **vite-bundle-visualizer**: Vite bundle analysis

### Backend Tools

- **Node.js --prof / --inspect**: Built-in CPU and memory profiling
- **clinic.js doctor**: Comprehensive performance diagnostics
- **clinic.js flame**: CPU flame graphs
- **clinic.js bubbleprof**: Async operations analysis
- **autocannon**: HTTP load testing
- **0x**: Flamegraph profiler for Node.js

### Database Tools

- **EXPLAIN ANALYZE** (PostgreSQL): Query execution plan analysis
- **EXPLAIN** (MySQL): Query optimization insights
- **pg_stat_statements**: PostgreSQL query statistics
- **Slow query logs**: Database-specific slow query logging

### General Tools

- **Benchmark.js / tinybench**: JavaScript benchmarking
- **Apache Bench (ab)**: HTTP server benchmarking
- **Artillery.io**: Modern load testing toolkit

## Advanced Optimization Patterns

### Web Workers for CPU-Intensive Tasks

```typescript
// main.ts
const worker = new Worker(new URL('./worker.ts', import.meta.url));

worker.postMessage({ data: largeDataset });

worker.onmessage = (event) => {
  console.log('Result:', event.data);
};

// worker.ts
self.onmessage = (event) => {
  const result = performHeavyCalculation(event.data);
  self.postMessage(result);
};
```

### Request Coalescing

```typescript
// Prevent duplicate requests for same resource
const pendingRequests = new Map();

async function fetchWithCoalescing(url: string) {
  if (pendingRequests.has(url)) {
    return pendingRequests.get(url);
  }

  const promise = fetch(url).then(r => r.json());
  pendingRequests.set(url, promise);

  try {
    const result = await promise;
    pendingRequests.delete(url);
    return result;
  } catch (error) {
    pendingRequests.delete(url);
    throw error;
  }
}
```

### Progressive Enhancement

```typescript
// Load critical CSS inline, defer non-critical
function App() {
  useEffect(() => {
    // Load non-critical CSS after initial render
    const link = document.createElement('link');
    link.rel = 'stylesheet';
    link.href = '/non-critical.css';
    document.head.appendChild(link);
  }, []);

  return <div>App content</div>;
}
```

### Service Workers for Offline Performance

```typescript
// sw.ts
const CACHE_NAME = 'v1';
const urlsToCache = [
  '/',
  '/styles/main.css',
  '/script/main.js',
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => cache.addAll(urlsToCache))
  );
});

self.addEventListener('fetch', (event) => {
  event.respondWith(
    caches.match(event.request)
      .then((response) => response || fetch(event.request))
  );
});
```

## Performance Monitoring

### Core Web Vitals

```typescript
import { getCLS, getFID, getFCP, getLCP, getTTFB } from 'web-vitals';

function sendToAnalytics(metric) {
  const body = JSON.stringify(metric);
  // Use `navigator.sendBeacon()` if available, falling back to `fetch()`
  (navigator.sendBeacon && navigator.sendBeacon('/analytics', body)) ||
    fetch('/analytics', { body, method: 'POST', keepalive: true });
}

getCLS(sendToAnalytics);
getFID(sendToAnalytics);
getFCP(sendToAnalytics);
getLCP(sendToAnalytics);
getTTFB(sendToAnalytics);
```

### Custom Performance Marks

```typescript
// Mark start of operation
performance.mark('data-fetch-start');

await fetchData();

// Mark end and measure
performance.mark('data-fetch-end');
performance.measure('data-fetch', 'data-fetch-start', 'data-fetch-end');

// Get measurements
const measures = performance.getEntriesByType('measure');
console.log('Data fetch took:', measures[0].duration, 'ms');
```
