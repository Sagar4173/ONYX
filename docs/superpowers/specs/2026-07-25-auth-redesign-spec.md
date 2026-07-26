# ONYX Auth Pages Redesign — Premium Dark Glass + Neon Tech

## Goal

Transform Sign In, Sign Up, Forgot Password, and Reset Password into a cohesive, mind-blowing entry experience that communicates power, security, and futuristic sophistication — without noise.

## Design Language

- **Tone:** Premium command center — not a startup landing page
- **Material:** Dark glass (frosted translucent cards with subtle backdrop blur)
- **Accents:** Cyan + violet neon glow on interactive elements
- **Shapes:** Pill buttons (`rounded-full`), softer card corners (`rounded-2xl`)
- **Motion:** Purposeful micro-interactions only (hover scale, glow intensify, focus rings with shadow bleed)
- **No:** spinning/bouncing/pinging decorations, floating geometric shapes, noisy particles

---

## Layout (AuthModal.jsx)

Full-viewport split screen, kept as-is structurally but refined.

### Left Panel (Branding)

- Darker base: `bg-gray-950` instead of the gradient
- Single animated gradient sweep: one large `bg-gradient-to-br from-cyan-500/10 via-violet-500/10 to-transparent` orb that slowly drifts (15s animation, subtle)
- Remove all `animate-ping`, `animate-spin`, `animate-bounce` decorations
- Keep the feature cards, stats, and platform highlight — refine their spacing
- Logo + title placement unchanged

### Right Panel (Form)

- Initial background: solid `bg-gray-950` (matches left, seamless)
- **Form card:**
  - `bg-gray-900/60 backdrop-blur-2xl` — translucent glass look
  - `border border-gray-700/40` — subtle but visible border
  - `shadow-2xl shadow-cyan-500/5` — faint cyan glow
  - `rounded-2xl` — soft but not extreme
  - No hover glow effect (keeps it clean)
- **Spacing:** `p-10` inside card, consistent 6-8px grid
- **Remove** duplicate trust badges from AuthModal (already in forms)

---

## Button Component Renovation (components.jsx)

### Gradient variant

The current gradient button bypasses `getButtonClasses()` and loses all base styling. Fix by including: `inline-flex items-center justify-center gap-2 px-8 py-3 text-base rounded-full font-semibold transition-all duration-200 transform hover:scale-[1.03] active:scale-[0.98] focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-offset-gray-900 focus-visible:ring-cyan-500 disabled:opacity-50 disabled:cursor-not-allowed`

**Gradient:** `from-cyan-400 via-violet-500 to-cyan-400` (brighter center than before)
**Hover:** intensify to `from-cyan-300 via-violet-400 to-cyan-300`, shadow grows
**Shape:** `rounded-full` — pill shape (non-gradient retains `rounded-lg`)
**Loading state:** spinner centered, same dimensions — no layout shift

### Non-gradient variant

Keep as-is (`rounded-lg` rectangle). This is for secondary/ghost buttons.

---

## LoginForm Renovation

### Form card interior

- **Header:** "Sign In" in `text-3xl font-bold text-white`, subtitle in `text-sm text-gray-400`
- **Spacing:** `space-y-6` between form groups

### Input groups

- Label: `flex items-center gap-2 text-sm font-medium text-gray-300 mb-2` with icon
- Input: Uses `<Input>` component with `leadingIcon`
- Focus: the Input component's built-in ring should be cyan
- Show/hide password button: proper `focus-visible:ring-2`, positioned absolute

### Remember me + Forgot password row

- Same layout but properly spaced
- Checkbox uses `rounded` (already correct)
- Forgot password: `text-sm text-cyan-400 hover:text-cyan-300 font-medium`

### Sign In button

- Pill shape, gradient, centered, full width
- Right arrow icon hidden during loading
- `focus-visible:ring-2 focus-visible:ring-cyan-500 focus-visible:ring-offset-2`

### "Create account" link

- Plain `<button>` (not hacked `Button`), gradient text via `bg-clip-text`
- `font-semibold text-transparent bg-gradient-to-r from-cyan-400 to-violet-400 bg-clip-text`
- `focus-visible:ring` on keyboard focus

### Trust badges

- Inside the form footer: `mt-8 pt-6 border-t border-gray-700/50`
- Three items: "256-bit SSL", "SOC 2 Certified", "GDPR Compliant"
- Keep as-is, already clean

---

## RegisterForm Renovation

### Form card interior

- **Header:** "Create Account" with subtitle
- **No scroll container** — form expands naturally
- `space-y-5` between groups (slightly tighter than login due to more fields)

### Input groups

- Consistent with LoginForm — icons in labels
- Username + Full Name in 2-column grid: `grid-cols-2 gap-4`
- Email: full width
- Password + Confirm: full width

### Password validation

- Only appears when user starts typing in password field
- Inline flex-wrap row with `CheckCircleIcon` (green) for passed, outlined circle (`border border-gray-600 w-3.5 h-3.5 rounded-full`) for not-yet
- Labels: "8+ chars", "Uppercase", "Lowercase", "Number", "Special char" — concise
- Green text for passed, `text-gray-500` for not-yet

### Confirm password

- Match validator: red text "Passwords don't match" inline
- Present only when confirm differs from password

### Create Account button

- Same pill gradient style as Sign In
- Right arrow hidden during loading

### "Sign in" link

- Same pattern as LoginForm's "Create account" — plain button with gradient text

---

## ForgotPasswordForm + ResetPasswordForm

These are simpler (fewer fields). Apply the same card styling:
- Consistent header pattern (`text-2xl font-bold` title + `text-sm` subtitle)
- Same input styling with icons
- Same pill gradient submit button
- Same "Back to sign in" plain button

---

## Margin / Padding Audit

| Element | Current | New |
|---------|---------|-----|
| Form card outer padding | `p-8 md:p-10` | `p-10` |
| Space between form groups | `space-y-5` | `space-y-6` (login), `space-y-5` (register) |
| Button padding | `px-4 py-2` (from `md` size) | `px-8 py-3` (custom via gradientClasses) |
| Between label and input | `mb-2` | `mb-2` (keep) |
| Between form and footer link | `mt-6` | `mt-8` |
| Trust badges top border | `mt-8 pt-6` | `mt-10 pt-6` |
| Input height | default | default (keep) |

---

## Gradient Color Refinement

| Element | Current | New |
|---------|---------|-----|
| Button gradient | `from-cyan-500 via-violet-500 to-cyan-500` | `from-cyan-400 via-violet-500 to-cyan-400` |
| Button hover | `from-cyan-600 via-violet-600 to-cyan-600` | `from-cyan-300 via-violet-400 to-cyan-300` |
| Title gradient | `from-cyan-400 via-violet-400 to-cyan-400` | same (keep) |
| Link gradient text | `from-cyan-400 to-violet-400` | same (keep) |
| Form card glow | `hover:shadow-cyan-500/10` | `shadow-cyan-500/5` (static, no hover) |

---

## Files to Modify

| File | Changes |
|------|---------|
| `frontend/src/styles/components.jsx` | Button `gradientClasses` — add padding, pill shape, centering, focus ring, brighter gradient |
| `frontend/src/components/auth/AuthModal.jsx` | Remove animated decorations, fix form card styling, remove duplicate trust badges |
| `frontend/src/components/auth/LoginForm.jsx` | Pill button, spacing audit, consistent link style, focus rings |
| `frontend/src/components/auth/RegisterForm.jsx` | Pill button, validation UI, icon labels, scroll fix, focus rings |
| `frontend/src/components/auth/ForgotPasswordForm.jsx` | Consistent styling with login |
| `frontend/src/components/auth/ResetPasswordForm.jsx` | Consistent styling with login |

---

## Verification

- `npm run build` passes
- All 4 auth forms render with consistent styling
- Buttons are pill-shaped with gradient
- No layout shift during loading
- Keyboard navigation works (Tab through all fields)
- Focus rings visible on all interactive elements
