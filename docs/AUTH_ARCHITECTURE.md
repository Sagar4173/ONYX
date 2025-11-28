# Authentication Component Architecture

## Component Hierarchy

```
frontend/src/components/auth/
│
├── index.js (Central Exports)
│   └── Exports all components & hooks
│
├── Core Authentication
│   ├── AuthContext.jsx
│   │   ├── AuthProvider (Context Provider)
│   │   └── useAuth() hook
│   │
│   └── AuthModal.jsx (Composite Component)
│       ├── View State Management
│       └── Form Routing
│
├── Authentication Forms
│   ├── LoginForm.jsx
│   │   ├── Email/Username Input
│   │   ├── Password Input
│   │   ├── Remember Me
│   │   └── Trust Badges
│   │
│   ├── RegisterForm.jsx
│   │   ├── User Details (username, name, email, org)
│   │   ├── Password with Validation
│   │   └── Confirm Password
│   │
│   ├── ForgotPasswordForm.jsx
│   │   └── Email Input (Reset Request)
│   │
│   └── ResetPasswordForm.jsx
│       ├── New Password
│       ├── Confirm Password
│       └── Token Validation
│
├── Success/Info Screens
│   ├── RegistrationSuccess.jsx
│   │   ├── Email Sent Confirmation
│   │   └── Resend Option
│   │
│   ├── ForgotPasswordSuccess.jsx
│   │   ├── Reset Email Sent
│   │   └── Instructions
│   │
│   └── EmailVerification.jsx
│       ├── Loading State
│       ├── Success State
│       └── Error State
│
└── User Management
    └── UserProfile.jsx
        ├── Profile Display
        ├── Edit Mode
        └── Update Functionality
```

## Data Flow

```
User Action
    ↓
AuthModal (View Router)
    ↓
Specific Form Component
    ↓
useAuth() Hook
    ↓
AuthContext (State Management)
    ↓
authAPI (Backend Communication)
    ↓
Backend Response
    ↓
Update UI State
    ↓
Show Success/Error
```

## View Transitions in AuthModal

```
┌─────────────────────────────────────────────────────────┐
│                      AuthModal                           │
│                                                          │
│  ┌──────────┐    ┌────────────┐    ┌─────────────────┐│
│  │  Login   │───▶│  Register  │───▶│ Reg. Success    ││
│  │  Form    │◀───│    Form    │    │   Screen        ││
│  └──────────┘    └────────────┘    └─────────────────┘│
│       │                                                  │
│       │                                                  │
│       ▼                                                  │
│  ┌──────────┐    ┌────────────┐    ┌─────────────────┐│
│  │  Forgot  │───▶│   Reset    │───▶│     Login       ││
│  │ Password │    │  Password  │    │  (on success)   ││
│  │   Form   │    │    Form    │    │                 ││
│  └──────────┘    └────────────┘    └─────────────────┘│
│       │                                                  │
│       ▼                                                  │
│  ┌──────────┐                                           │
│  │  Forgot  │                                           │
│  │ Password │                                           │
│  │ Success  │                                           │
│  └──────────┘                                           │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

## Component Responsibilities

### AuthContext.jsx

**Purpose**: Global authentication state management

- Manages user session
- Provides authentication methods
- Handles token storage
- Exposes `useAuth()` hook

### AuthModal.jsx

**Purpose**: Authentication flow orchestration

- Routes between different auth views
- Manages form transitions
- Handles success/error callbacks
- Provides modal wrapper

### LoginForm.jsx

**Purpose**: User login interface

- Email/username authentication
- Password input with visibility toggle
- Remember me functionality
- Navigation to register/forgot password

### RegisterForm.jsx

**Purpose**: New user registration

- Collects user information
- Validates password requirements in real-time
- Confirms password match
- Triggers email verification

### ForgotPasswordForm.jsx

**Purpose**: Password reset request

- Accepts email address
- Sends reset link
- Shows success confirmation

### ResetPasswordForm.jsx

**Purpose**: New password creation

- Token-based authentication
- Password requirements validation
- Confirms new password
- Redirects to login on success

### RegistrationSuccess.jsx

**Purpose**: Post-registration guidance

- Confirms account creation
- Shows verification email sent
- Provides resend option
- Directs to login

### ForgotPasswordSuccess.jsx

**Purpose**: Password reset confirmation

- Confirms reset email sent
- Provides clear instructions
- Notes link expiration
- Returns to login

### EmailVerification.jsx

**Purpose**: Email verification handler

- Processes verification token
- Shows verification status
- Handles errors gracefully
- Provides resend option

### UserProfile.jsx

**Purpose**: User account management

- Displays user information
- Allows profile editing
- Shows account status
- Updates user details

## Usage Examples

### Basic Login Modal

```jsx
import { AuthModal } from "./components/auth";

function App() {
  const [showAuth, setShowAuth] = useState(false);

  return (
    <>
      <button onClick={() => setShowAuth(true)}>Login</button>
      <AuthModal
        isOpen={showAuth}
        onClose={() => setShowAuth(false)}
        initialView="login"
      />
    </>
  );
}
```

### Using Auth Hook

```jsx
import { useAuth } from "./components/auth";

function ProtectedComponent() {
  const { user, logout } = useAuth();

  return (
    <div>
      <p>Welcome, {user.username}!</p>
      <button onClick={logout}>Logout</button>
    </div>
  );
}
```

### Password Reset Flow

```jsx
import { AuthModal } from "./components/auth";

function ResetPasswordPage() {
  const { token } = useParams();

  return (
    <AuthModal isOpen={true} initialView="reset-password" resetToken={token} />
  );
}
```

## Styling Patterns

### Common Patterns Used Across Components

1. **Glassmorphism Container**

```jsx
<div className="bg-gray-900/95 backdrop-blur-xl rounded-3xl border border-gray-800/50">
```

2. **Gradient Button**

```jsx
<button className="bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 transform hover:scale-105">
```

3. **Animated Background Blobs**

```jsx
<div className="absolute -top-1/2 -left-1/2 w-full h-full bg-gradient-to-br from-blue-500/20 via-purple-500/20 to-pink-500/20 rounded-full blur-3xl animate-pulse" />
```

4. **Icon-Enhanced Input**

```jsx
<div className="flex items-center gap-3">
  <Icon className="h-5 w-5 text-blue-400" />
  <input className="bg-gray-900/50 border-gray-700 focus:border-blue-500" />
</div>
```

## Accessibility Features

- Proper ARIA labels on forms
- Keyboard navigation support
- Focus states on interactive elements
- Error messages announced to screen readers
- High contrast text for readability
- Descriptive button text
- Semantic HTML structure

## Performance Optimizations

- Lazy loading of heavy components
- Memoized auth context
- Debounced validation checks
- Optimized re-renders with React.memo
- Efficient form state management

## Security Considerations

- JWT tokens stored in localStorage
- Automatic token refresh
- Protected route handling
- Password strength requirements
- Email verification flow
- Token expiration handling
- XSS protection in inputs
- CSRF token support

---

This modular architecture ensures maintainability, scalability, and excellent developer experience! 🎉
