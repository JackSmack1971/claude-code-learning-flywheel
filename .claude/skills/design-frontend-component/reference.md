# Frontend Component Design - Extended Reference

This document contains detailed code examples, patterns, and best practices referenced in the main SKILL.md file.

## Component Design Patterns

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

## Styling Best Practices

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

## Testing Frontend Components

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

## Additional Composition Patterns

### Higher-Order Components (HOC)

```typescript
// ✅ HOC for adding loading state
function withLoading<P extends object>(
  Component: React.ComponentType<P>
) {
  return function WithLoadingComponent(
    props: P & { isLoading: boolean }
  ) {
    const { isLoading, ...rest } = props;

    if (isLoading) {
      return <Spinner />;
    }

    return <Component {...(rest as P)} />;
  };
}

// Usage
const UserListWithLoading = withLoading(UserList);

<UserListWithLoading isLoading={loading} users={users} />
```

### Slots Pattern

```typescript
// ✅ Flexible component with named slots
interface CardProps {
  header?: ReactNode;
  footer?: ReactNode;
  children: ReactNode;
}

function Card({ header, footer, children }: CardProps) {
  return (
    <div className="card">
      {header && <div className="card-header">{header}</div>}
      <div className="card-body">{children}</div>
      {footer && <div className="card-footer">{footer}</div>}
    </div>
  );
}

// Usage
<Card
  header={<h2>User Profile</h2>}
  footer={<Button>Save Changes</Button>}
>
  <UserProfileForm />
</Card>
```

## Advanced State Management Patterns

### Reducer Pattern for Complex State

```typescript
type State = {
  items: Item[];
  filter: string;
  sortBy: 'name' | 'date';
  isLoading: boolean;
};

type Action =
  | { type: 'ADD_ITEM'; payload: Item }
  | { type: 'REMOVE_ITEM'; payload: string }
  | { type: 'SET_FILTER'; payload: string }
  | { type: 'SET_SORT'; payload: 'name' | 'date' }
  | { type: 'SET_LOADING'; payload: boolean };

function reducer(state: State, action: Action): State {
  switch (action.type) {
    case 'ADD_ITEM':
      return { ...state, items: [...state.items, action.payload] };
    case 'REMOVE_ITEM':
      return {
        ...state,
        items: state.items.filter(i => i.id !== action.payload)
      };
    case 'SET_FILTER':
      return { ...state, filter: action.payload };
    case 'SET_SORT':
      return { ...state, sortBy: action.payload };
    case 'SET_LOADING':
      return { ...state, isLoading: action.payload };
    default:
      return state;
  }
}

function ItemManager() {
  const [state, dispatch] = useReducer(reducer, {
    items: [],
    filter: '',
    sortBy: 'name',
    isLoading: false,
  });

  // ... use dispatch for actions
}
```

## Accessibility Patterns

### Keyboard Navigation

```typescript
function Dropdown({ items, onSelect }: DropdownProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(0);

  const handleKeyDown = (e: KeyboardEvent) => {
    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        setSelectedIndex(i => Math.min(i + 1, items.length - 1));
        break;
      case 'ArrowUp':
        e.preventDefault();
        setSelectedIndex(i => Math.max(i - 1, 0));
        break;
      case 'Enter':
        e.preventDefault();
        onSelect(items[selectedIndex]);
        setIsOpen(false);
        break;
      case 'Escape':
        setIsOpen(false);
        break;
    }
  };

  return (
    <div
      role="combobox"
      aria-expanded={isOpen}
      aria-controls="dropdown-list"
      onKeyDown={handleKeyDown}
      tabIndex={0}
    >
      {/* ... dropdown content */}
    </div>
  );
}
```

### ARIA Labels

```typescript
function SearchInput() {
  const [query, setQuery] = useState('');

  return (
    <div role="search">
      <label htmlFor="search-input" className="sr-only">
        Search users
      </label>
      <input
        id="search-input"
        type="search"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        aria-label="Search users"
        aria-describedby="search-hint"
      />
      <span id="search-hint" className="sr-only">
        Enter at least 3 characters to search
      </span>
    </div>
  );
}
```

## Performance Optimization Patterns

### Windowing/Virtualization

```typescript
import { FixedSizeList as List } from 'react-window';

function VirtualizedUserList({ users }: { users: User[] }) {
  const Row = ({ index, style }: { index: number; style: CSSProperties }) => (
    <div style={style}>
      <UserCard user={users[index]} />
    </div>
  );

  return (
    <List
      height={600}
      itemCount={users.length}
      itemSize={80}
      width="100%"
    >
      {Row}
    </List>
  );
}
```

### Intersection Observer for Lazy Loading

```typescript
function LazyImage({ src, alt }: { src: string; alt: string }) {
  const [isVisible, setIsVisible] = useState(false);
  const imgRef = useRef<HTMLImageElement>(null);

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsVisible(true);
          observer.disconnect();
        }
      },
      { rootMargin: '50px' }
    );

    if (imgRef.current) {
      observer.observe(imgRef.current);
    }

    return () => observer.disconnect();
  }, []);

  return (
    <img
      ref={imgRef}
      src={isVisible ? src : '/placeholder.png'}
      alt={alt}
      loading="lazy"
    />
  );
}
```
