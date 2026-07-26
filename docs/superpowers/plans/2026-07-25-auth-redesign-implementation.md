# Auth Pages Redesign — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use subagent-driven-development or executing-plans to implement. Steps use `- [ ]` syntax.

**Goal:** Transform all auth pages (Sign In, Sign Up, Forgot/Reset Password) into a premium dark-glass + neon-tech experience with pill-shaped gradient buttons, frosted card containers, consistent spacing, and purposeful micro-interactions.

**Architecture:** Modify the Button component in `styles/components.jsx` first (all forms depend on it), then fix each auth form file. AuthModal is the container; LoginForm/RegisterForm/ForgotPasswordForm/ResetPasswordForm are the inner forms.

**Tech Stack:** React 18, Tailwind CSS 3, Heroicons

## Global Constraints

- No new dependencies
- `npm run build` must pass after every task
- No breaking changes to existing component APIs
- Dark theme only — no light-mode fallbacks
- All interactive elements must have `focus-visible:ring`

---

### Task 1: Button gradientClasses — pill shape, centering, brighter gradient

**Files:**
- Modify: `frontend/src/styles/components.jsx:42-43`

**Interfaces:**
- Consumes: Nothing (self-contained)
- Produces: Fixed `<Button gradient>` with pill shape, centering, proper padding

- [ ] **Step 1: Update gradientClasses**

Replace the gradient class string to include:
- `inline-flex items-center justify-center` for centering
- `gap-2` for icon/text spacing
- `px-8 py-3 text-base` for proper size (replaces missing size classes)
- `rounded-full` for pill shape
- `from-cyan-400 via-violet-500 to-cyan-400` for brighter gradient
- `hover:from-cyan-300 hover:via-violet-400 hover:to-cyan-300` for hover intensify
- `focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-offset-gray-900 focus-visible:ring-cyan-500` for focus
- `disabled:opacity-50 disabled:cursor-not-allowed` for disabled

- [ ] **Step 2: Build check**

Run: `cd frontend; npm run build`
Expected: Build succeeds.

---

### Task 2: AuthModal — remove noise, fix card contrast, trust badges

**Files:**
- Modify: `frontend/src/components/auth/AuthModal.jsx`

**Interfaces:**
- Consumes: Nothing (self-contained layout component)
- Produces: Clean auth container with glass card, no noisy animations

- [ ] **Step 1: Remove all `animate-ping`, `animate-spin`, `animate-bounce` decorations**

Remove the 4 animated particle dots (lines ~268-285) and the 3 floating geometric shapes (lines ~299-311). Keep the two gradient blur orbs.

- [ ] **Step 2: Fix form card contrast**

Change `bg-gray-900/80 backdrop-blur-xl rounded-3xl border border-gray-800/50 shadow-2xl overflow-hidden transform transition-all duration-500 hover:shadow-cyan-500/10` to:
`bg-gray-900/60 backdrop-blur-2xl border border-gray-700/40 rounded-2xl shadow-2xl shadow-cyan-500/5 overflow-hidden`

- [ ] **Step 3: Remove duplicate trust badges**

Remove the trust indicators block from AuthModal (trust badges inside each form already exist).

- [ ] **Step 4: Build check**

Run: `cd frontend; npm run build`
Expected: Build succeeds.

---

### Task 3: LoginForm — pill button, spacing audit, focus rings

**Files:**
- Modify: `frontend/src/components/auth/LoginForm.jsx`

- [ ] **Step 1: Fix Sign In button**

Change `gradient` button to add `focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-offset-gray-900 focus-visible:ring-cyan-500`.
Change `rightIcon` to hide during loading: `rightIcon={isLoading ? undefined : <ArrowRightIcon .../>}`.

- [ ] **Step 2: Fix "Create account" link**

Replace `<Button variant="ghost" ...` hacked link with clean `<button>` with gradient text via `bg-clip-text`.

- [ ] **Step 3: Add focus-visible:ring to forgot-password button and show/hide toggle**

Both buttons need `focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500`.

- [ ] **Step 4: Build check**

Run: `cd frontend; npm run build`
Expected: Build succeeds.

---

### Task 4: RegisterForm — scroll fix, validation UI, icon labels, focus rings

**Files:**
- Modify: `frontend/src/components/auth/RegisterForm.jsx`

- [ ] **Step 1: Remove max-h scroll wrapper**

Change `p-6 md:p-8 max-h-[85vh] overflow-y-auto` to just `p-6 md:p-8`.

- [ ] **Step 2: Replace password validation dots with CheckCircleIcon**

Replace the tiny `h-2 w-2 rounded-full` dots with:
- `CheckCircleIcon w-3.5 h-3.5 text-green-400` (passed)
- `div w-3.5 h-3.5 rounded-full border border-gray-600` (not yet)
- Change grid to inline flex-wrap
- Only show when password has value

- [ ] **Step 3: Add icon labels to all form fields**

Add `AtSymbolIcon` (username), `UserIcon` (full name), `EnvelopeIcon` (email), `LockClosedIcon` (password, confirm).

- [ ] **Step 4: Fix "Sign in" link**

Replace `<Button variant="ghost" ...>` with clean `<button>` with gradient text.

- [ ] **Step 5: Add focus-visible:ring to both show/hide toggles**

Both need `focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500 rounded`.

- [ ] **Step 6: Remove unused `UserCircleSolid` import**

- [ ] **Step 7: Build check**

Run: `cd frontend; npm run build`
Expected: Build succeeds.

---

### Task 5: ForgotPasswordForm + ResetPasswordForm — consistent styling

**Files:**
- Modify: `frontend/src/components/auth/ForgotPasswordForm.jsx`
- Modify: `frontend/src/components/auth/ResetPasswordForm.jsx`

- [ ] **Step 1: ForgotPasswordForm — add focus-visible:ring to submit button**

Add `focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-offset-gray-900 focus-visible:ring-cyan-500` to the gradient submit button.

- [ ] **Step 2: ForgotPasswordForm — fix "Back to sign in" link**

Replace `<Button variant="ghost">` with plain button with gradient text.

- [ ] **Step 3: ResetPasswordForm — add focus-visible:ring to submit button**

Same pattern as step 1.

- [ ] **Step 4: ResetPasswordForm — fix "Back to sign in" link**

Same pattern as step 2.

- [ ] **Step 5: ResetPasswordForm — add focus-visible:ring to show/hide password toggles**

Both password fields need focus rings on their eye buttons.

- [ ] **Step 6: Build check**

Run: `cd frontend; npm run build`
Expected: Build succeeds.

---

### Task 6: Final quality audit

- [ ] **Step 1: Verify all buttons are pill-shaped with gradient**

Check Login, Register, ForgotPassword, ResetPassword submit buttons visually.

- [ ] **Step 2: Verify no layout shift during loading**

Submit buttons should maintain their width when showing spinner (arrow icon hidden).

- [ ] **Step 3: Verify keyboard navigation**

Tab through each form — all focus rings visible.

- [ ] **Step 4: Verify form card has proper contrast**

Card should be visually distinct from background.

- [ ] **Step 5: Build check**

Run: `cd frontend; npm run build`
Expected: Build succeeds with no errors.
