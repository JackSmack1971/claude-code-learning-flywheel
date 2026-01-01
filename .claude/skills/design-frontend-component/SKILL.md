---
name: design-frontend-component
description: "Use when creating React/Vue components or adding UI features. Enforces composition patterns and state management best practices."
author: "Claude Code Learning Flywheel Team"
allowed-tools: ["Read", "Write", "Edit", "Bash", "Grep", "Glob"]
version: 1.0.0
last_verified: "2026-01-01"
tags: ["frontend", "react", "vue", "components", "ui", "composition"]
related-skills: ["test-driven-workflow", "refactor-legacy-code"]
---

# Skill: Design Frontend Component

## Purpose
Prevent "Prop Drilling Hell" and monolithic components. Enforce composition patterns, proper state management, and the Atomic Design methodology to create maintainable, testable UI components.

## 1. Negative Knowledge (Anti-Patterns)

| Failure Pattern | Context | Why It Fails |
| :--- | :--- | :--- |
| Prop Drilling | Passing data through 5+ layers | Tight coupling, hard to refactor |
| God Components | Files >300 lines with mixed concerns | Untestable, unmaintainable |
| Inline Styles | Hardcoded hex values and dimensions | Inconsistent design, no theming |
| Direct DOM Manipulation | `document.getElementById` in React/Vue | Breaks framework reactivity |
| Business Logic in Components | API calls and validation in render | Hard to test, violates SRP |
| Missing Key Props | List items without unique keys | Performance issues, bugs |
| Mutating Props | Changing props directly | Breaks one-way data flow |
| Excessive State | Everything in component state | Performance issues, complex logic |

## 2. Verified Component Design Procedure

### The Atomic Design Hierarchy

```
ATOMS       → Smallest units (Button, Input, Label)
  ↓
MOLECULES   → Simple groups (SearchBar = Input + Button)
  ↓
ORGANISMS   → Complex sections (Header = Logo + Nav + SearchBar)
  ↓
TEMPLATES   → Page layouts (wireframes)
  ↓
PAGES       → Actual instances with real data
```

### Phase 1: Component Planning

**Before writing code, answer these questions:**

1. **What is the single responsibility of this component?**
   - ❌ "It handles the user profile, settings, and notifications"
   - ✅ "It displays user profile information"

2. **What category is it? (Atom, Molecule, Organism)**
   - Atom: Basic building block (Button, Input, Icon)
   - Molecule: Combination of atoms (Form field with label and error)
   - Organism: Complex UI section (Navigation bar, Product card)

3. **What data does it need?**
   - Props (from parent)
   - Local state (UI-only)
   - Global state (context/store)

4. **What actions can users take?**
   - Events to emit/handle
   - Side effects (API calls, navigation)

### Phase 2: Component Structure

**File organization:**

```
components/
├── atoms/
│   ├── Button/
│   │   ├── Button.tsx
│   │   ├── Button.test.tsx
│   │   ├── Button.stories.tsx  (Storybook)
│   │   └── index.ts
│   └── Input/
│       ├── Input.tsx
│       └── ...
├── molecules/
│   └── SearchBar/
│       ├── SearchBar.tsx
│       └── ...
└── organisms/
    └── Header/
        ├── Header.tsx
        └── ...
```

**Component template:**

```typescript
// components/atoms/Button/Button.tsx
import { ReactNode } from 'react';
import styles from './Button.module.css';

export interface ButtonProps {
  /** The button's content */
  children: ReactNode;
  /** Visual variant */
  variant?: 'primary' | 'secondary' | 'danger';
  /** Size of the button */
  size?: 'small' | 'medium' | 'large';
  /** Disabled state */
  disabled?: boolean;
  /** Click handler */
  onClick?: () => void;
  /** Additional CSS classes */
  className?: string;
}

export function Button({
  children,
  variant = 'primary',
  size = 'medium',
  disabled = false,
  onClick,
  className = '',
}: ButtonProps) {
  return (
    <button
      className={`${styles.button} ${styles[variant]} ${styles[size]} ${className}`}
      disabled={disabled}
      onClick={onClick}
      type="button"
    >
      {children}
    </button>
  );
}
```

### Phase 3: Props Design

**Principles:**

1. **Keep props flat and simple**
   ```typescript
   // ❌ BAD: Nested props
   interface BadProps {
     user: {
       profile: {
         personal: {
           name: string;
         }
       }
     }
   }

   // ✅ GOOD: Flat props
   interface GoodProps {
     userName: string;
     userEmail: string;
     userAvatar: string;
   }
   ```

2. **Use discriminated unions for variants**
   ```typescript
   // ✅ Type-safe variants
   type ButtonProps =
     | { variant: 'link'; href: string }
     | { variant: 'button'; onClick: () => void };
   ```

3. **Provide sensible defaults**
   ```typescript
   function Card({
     variant = 'outlined',  // Default value
     elevation = 1,
     padding = 'medium'
   }: CardProps) {
     // ...
   }
   ```

### Phase 4: State Management

**Decision tree for state location:**

```
Is it server data (API)?
├─ YES → Use React Query / SWR / TanStack Query
└─ NO → Continue

Does more than one component need it?
├─ YES → Use Context / Redux / Zustand
└─ NO → Continue

Is it just UI state (open/closed, hover)?
├─ YES → Use local useState
└─ NO → Reconsider if state is needed
```

**Example: Proper state management**

```typescript
// ❌ BAD: Everything in component state
function UserProfile() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [isEditing, setIsEditing] = useState(false);  // UI state
  const [theme, setTheme] = useState('light');         // Global state

  useEffect(() => {
    setLoading(true);
    fetch('/api/user')
      .then(res => res.json())
      .then(setUser)
      .catch(setError)
      .finally(() => setLoading(false));
  }, []);

  // ... rest of component
}

// ✅ GOOD: Separate concerns
function UserProfile() {
  // Server state (React Query)
  const { data: user, isLoading, error } = useQuery({
    queryKey: ['user'],
    queryFn: fetchUser
  });

  // Global state (Context)
  const { theme } = useTheme();

  // Local UI state
  const [isEditing, setIsEditing] = useState(false);

  // ... rest of component
}
```

### Phase 5: Composition Over Prop Drilling

**Avoid prop drilling:**

```typescript
// ❌ BAD: Prop drilling
function App() {
  const user = useUser();
  return <Dashboard user={user} />;
}

function Dashboard({ user }) {
  return <Sidebar user={user} />;
}

function Sidebar({ user }) {
  return <UserMenu user={user} />;
}

function UserMenu({ user }) {
  return <div>{user.name}</div>;
}

// ✅ GOOD: Use context for deeply nested data
const UserContext = createContext<User | null>(null);

function App() {
  const user = useUser();
  return (
    <UserContext.Provider value={user}>
      <Dashboard />
    </UserContext.Provider>
  );
}

function UserMenu() {
  const user = useContext(UserContext);
  return <div>{user.name}</div>;
}
```

**Composition patterns:**

```typescript
// ✅ Render props pattern
function DataFetcher({ url, children }) {
  const { data, loading } = useFetch(url);
  return children({ data, loading });
}

<DataFetcher url="/api/users">
  {({ data, loading }) => loading ? <Spinner /> : <UserList users={data} />}
</DataFetcher>

// ✅ Compound components pattern
function Tabs({ children }) {
  const [activeTab, setActiveTab] = useState(0);
  return (
    <TabsContext.Provider value={{ activeTab, setActiveTab }}>
      {children}
    </TabsContext.Provider>
  );
}

Tabs.List = function TabsList({ children }) { /* ... */ };
Tabs.Tab = function Tab({ children, index }) { /* ... */ };
Tabs.Panel = function TabPanel({ children, index }) { /* ... */ };

// Usage
<Tabs>
  <Tabs.List>
    <Tabs.Tab index={0}>Profile</Tabs.Tab>
    <Tabs.Tab index={1}>Settings</Tabs.Tab>
  </Tabs.List>
  <Tabs.Panel index={0}><ProfileContent /></Tabs.Panel>
  <Tabs.Panel index={1}><SettingsContent /></Tabs.Panel>
</Tabs>
```

### Phase 6: Performance Optimization

**Only optimize when needed, but follow these patterns:**

```typescript
// ✅ Memoize expensive calculations
function ProductList({ products, filters }) {
  const filteredProducts = useMemo(() => {
    return products.filter(p => matchesFilters(p, filters));
  }, [products, filters]);

  return <div>{filteredProducts.map(p => <ProductCard key={p.id} {...p} />)}</div>;
}

// ✅ Memoize callbacks passed to children
function ParentComponent() {
  const handleClick = useCallback(() => {
    console.log('Clicked');
  }, []);

  return <ChildComponent onClick={handleClick} />;
}

// ✅ Memoize components that render often
const ExpensiveComponent = memo(function ExpensiveComponent({ data }) {
  // Complex rendering logic
  return <div>{/* ... */}</div>;
});

// ❌ DON'T memoize everything (premature optimization)
const SimpleComponent = memo(function SimpleComponent({ text }) {
  return <div>{text}</div>;  // Too simple to benefit from memo
});
```

## 3. Component Design Patterns

### Pattern 1: Container/Presenter (Smart/Dumb)

```typescript
// Container (Smart): Handles logic, data fetching
function UserProfileContainer() {
  const { data: user, isLoading } = useQuery(['user'], fetchUser);
  const mutation = useMutation(updateUser);

  const handleSave = (updates: Partial<User>) => {
    mutation.mutate(updates);
  };

  if (isLoading) return <Spinner />;

  return <UserProfilePresenter user={user} onSave={handleSave} />;
}

// Presenter (Dumb): Pure display logic
interface UserProfilePresenterProps {
  user: User;
  onSave: (updates: Partial<User>) => void;
}

function UserProfilePresenter({ user, onSave }: UserProfilePresenterProps) {
  const [formData, setFormData] = useState(user);

  return (
    <form onSubmit={() => onSave(formData)}>
      <Input value={formData.name} onChange={/* ... */} />
      <Button type="submit">Save</Button>
    </form>
  );
}
```

### Pattern 2: Custom Hooks for Logic Extraction

```typescript
// ✅ Extract complex logic to custom hooks
function useFormValidation(initialValues: FormData) {
  const [values, setValues] = useState(initialValues);
  const [errors, setErrors] = useState({});

  const validate = useCallback(() => {
    const newErrors = {};
    if (!values.email) newErrors.email = 'Required';
    if (!values.password || values.password.length < 8) {
      newErrors.password = 'Must be 8+ characters';
    }
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  }, [values]);

  return { values, setValues, errors, validate };
}

// Usage in component
function LoginForm() {
  const { values, setValues, errors, validate } = useFormValidation({
    email: '',
    password: ''
  });

  const handleSubmit = () => {
    if (validate()) {
      // Submit form
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <Input
        value={values.email}
        onChange={(e) => setValues({ ...values, email: e.target.value })}
        error={errors.email}
      />
      {/* ... */}
    </form>
  );
}
```

### Pattern 3: Error Boundaries

```typescript
// Error boundary for graceful error handling
class ErrorBoundary extends React.Component<
  { children: ReactNode; fallback: ReactNode },
  { hasError: boolean }
> {
  state = { hasError: false };

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Component error:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return this.props.fallback;
    }
    return this.props.children;
  }
}

// Usage
<ErrorBoundary fallback={<ErrorMessage />}>
  <UserDashboard />
</ErrorBoundary>
```

## 4. Styling Best Practices

**Use CSS modules or styled-components, not inline styles:**

```typescript
// ❌ BAD: Inline styles (no theming, no reusability)
function Button() {
  return (
    <button style={{
      backgroundColor: '#007bff',
      padding: '10px 20px',
      borderRadius: '4px'
    }}>
      Click me
    </button>
  );
}

// ✅ GOOD: CSS modules
import styles from './Button.module.css';

function Button() {
  return <button className={styles.button}>Click me</button>;
}

// ✅ GOOD: Styled-components with theme
import styled from 'styled-components';

const StyledButton = styled.button`
  background-color: ${props => props.theme.colors.primary};
  padding: ${props => props.theme.spacing.medium};
  border-radius: ${props => props.theme.borderRadius.small};
`;
```

**Design tokens for consistency:**

```typescript
// theme.ts
export const theme = {
  colors: {
    primary: '#007bff',
    secondary: '#6c757d',
    danger: '#dc3545',
    success: '#28a745',
  },
  spacing: {
    small: '0.5rem',
    medium: '1rem',
    large: '2rem',
  },
  borderRadius: {
    small: '4px',
    medium: '8px',
    large: '12px',
  },
  typography: {
    fontFamily: 'Inter, sans-serif',
    fontSize: {
      small: '0.875rem',
      medium: '1rem',
      large: '1.25rem',
    },
  },
};
```

## 5. Testing Frontend Components

**Test user behavior, not implementation:**

```typescript
// ✅ GOOD: Test behavior
import { render, screen, fireEvent } from '@testing-library/react';

describe('LoginForm', () => {
  it('should show error when email is invalid', async () => {
    render(<LoginForm />);

    const emailInput = screen.getByLabelText('Email');
    const submitButton = screen.getByRole('button', { name: 'Login' });

    fireEvent.change(emailInput, { target: { value: 'invalid' } });
    fireEvent.click(submitButton);

    expect(await screen.findByText('Invalid email')).toBeInTheDocument();
  });

  it('should call onSubmit when form is valid', async () => {
    const onSubmit = vi.fn();
    render(<LoginForm onSubmit={onSubmit} />);

    fireEvent.change(screen.getByLabelText('Email'), {
      target: { value: 'test@example.com' }
    });
    fireEvent.change(screen.getByLabelText('Password'), {
      target: { value: 'password123' }
    });
    fireEvent.click(screen.getByRole('button', { name: 'Login' }));

    expect(onSubmit).toHaveBeenCalledWith({
      email: 'test@example.com',
      password: 'password123',
    });
  });
});
```

## 6. Failed Attempts (Negative Knowledge Evolution)

### ❌ Attempt: Premature abstraction
**Context:** Created reusable component after first use
**Failure:** Over-engineered, didn't fit other use cases
**Learning:** Wait for 3 instances before abstracting

### ❌ Attempt: Global state for everything
**Context:** Put all state in Redux store
**Failure:** Boilerplate explosion, slow development
**Learning:** Use local state by default, global only when needed

### ❌ Attempt: Index as key in lists
**Context:** Used array index as React key: `key={index}`
**Failure:** Bugs when list items reordered or filtered
**Learning:** Always use unique, stable IDs as keys

### ❌ Attempt: Fetching data in components
**Context:** Used useEffect for API calls in multiple components
**Failure:** No caching, duplicate requests, complex loading states
**Learning:** Use React Query/SWR for server state

## 7. Component Design Checklist

Before committing a component:

- [ ] **Single Responsibility**: Component has one clear purpose
- [ ] **Size Limit**: File is <300 lines (extract if larger)
- [ ] **Props Typed**: All props have TypeScript interfaces
- [ ] **No Prop Drilling**: Props don't pass through >2 layers
- [ ] **Accessible**: Has proper ARIA labels and keyboard navigation
- [ ] **Tested**: Has tests for main user interactions
- [ ] **Documented**: Props are documented with JSDoc comments
- [ ] **Styled**: Uses design system tokens, no magic numbers
- [ ] **Keys in Lists**: List items have unique, stable keys

## 8. Governance
- **Token Budget:** ~495 lines (within 500 limit)
- **Dependencies:** React 18+, TypeScript 5+, Testing Library
- **Pattern Origin:** Atomic Design (Brad Frost), React Best Practices
- **Maintenance:** Update as React/framework patterns evolve
- **Verification Date:** 2026-01-01
