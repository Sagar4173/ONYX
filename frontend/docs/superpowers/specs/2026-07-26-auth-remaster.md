# Auth & User Profile Remaster — Design Spec

## Objective

Remaster the ONYX auth module (auth pages + UserProfile modal) with premium visual upgrades consistent with the 7 previously remastered areas: ParticleBackground, framer-motion animations, unified cyan/violet theme, glassmorphism enhancements. All 19 existing files enhanced in-place; no new files.

## Zero Dependencies

Zero new npm dependencies. All animations via framer-motion (already in project). ParticleBackground from `../../styles/components`. Canvas/SVG/CSS only.

## Design Language

- Particles: `ParticleBackground` component (cyan/violet dots)
- Animations: framer-motion `motion.div`, `AnimatePresence`, `layoutId` spring, staggerChildren
- Colors: cyan-400/violet-500 gradients, gray-900/950 backgrounds
- Glassmorphism: `backdrop-blur-xl`, `bg-gray-900/60`, `border border-gray-700/40`
- Typography: Inter font (existing), gradient text for headings

---

## Part 1: Auth Pages (Unauthenticated)

### AuthModal.jsx — Rewrite

**Current**: 429 lines, split-screen layout (branding left + form right), blob div animations.

**Changes**:
- Import `ParticleBackground` from `"../../styles/components"`
- Import `motion`, `AnimatePresence` from `"framer-motion"`
- Replace absolute-positioned blob divs with `<ParticleBackground />`
- Wrap `renderCurrentView()` with `<AnimatePresence mode="wait">` — each form is a `motion.div` keyed on `currentView`
- Transition: `initial={{ opacity: 0, x: 20 }}` `animate={{ opacity: 1, x: 0 }}` `exit={{ opacity: 0, x: -20 }}` with `duration: 0.2`
- Feature cards: `motion.div` with `staggerChildren: 0.08` — each card gets `initial={{ opacity: 0, y: 10 }}` `animate={{ opacity: 1, y: 0 }}`
- Branding title/subtitle: `motion.div` with fade transition on view change using `AnimatePresence mode="wait"`
- Stats row (99.9% / 10K+ / 500+): add `whileInView` with fade-up
- Close button: subtle rotate-90 on hover (already exists, keep)

### LoginForm.jsx — Enhance

**Current**: 278 lines, two modes (standard login + 2FA code entry), remember-me checkbox, trust badges.

**Changes**:
- Import `motion` from `"framer-motion"`
- Wrap form in `motion.form` with `initial={{ opacity: 0, y: 10 }}` `animate={{ opacity: 1, y: 0 }}`
- Wrap the 2FA code section in `AnimatePresence` with fade/slide-up for smooth toggle
- Form fields use stagger container — `variants={{ hidden: {}, visible: { transition: { staggerChildren: 0.04 } } }}` — each field/button gets `initial={{ opacity: 0, y: 8 }}` `animate={{ opacity: 1, y: 0 }}`
- Keep existing 2FA, security badges, and visual structure

### RegisterForm.jsx — Enhance

**Current**: 287 lines, 2-column grid, password validation indicators, trust badges.

**Changes**:
- Import `motion` from `"framer-motion"`
- Same stagger pattern as LoginForm for form fields
- Password validation indicators get `motion.div` with stagger for the 5 criteria badges
- Keep existing structure, 2-column grid, trust badges

### ForgotPasswordForm.jsx — Enhance

**Current**: 72 lines, single email input + submit button.

**Changes**:
- Import `motion` from `"framer-motion"`
- `motion.form` with fade-up entry
- Stagger for label, input, button (2 items)

### ResetPasswordForm.jsx — Enhance

**Current**: 194 lines, password/new/confirm with validation, strength meter.

**Changes**:
- Import `motion` from `"framer-motion"`
- `motion.form` with fade-up entry
- Stagger for fields + strength meter + button
- Password validation badges get stagger animation

### RegistrationSuccess.jsx — Enhance

**Current**: 157 lines, blob backgrounds, animated bounce icon, resend with cooldown.

**Changes**:
- Wrap content in `motion.div` with stagger container (particles from AuthModal)
- Icon: `motion.div` with bounce spring animation (keep existing bounce, add motion wrapper)
- Email box, info box, buttons: stagger-fade in

### ForgotPasswordSuccess.jsx — Enhance

**Current**: 77 lines, blob backgrounds, next-steps list, back-to-login button.

**Changes**:
- Wrap content in `motion.div` stagger container (particles from AuthModal)
- Next-steps list items: `motion.li` with stagger

### EmailVerification.jsx — Rewrite

**Current**: 258 lines, three states (loading/success/error), manual state management. Rendered standalone on `/verify-email` so needs its own ParticleBackground.

**Changes**:
- Import `motion`, `AnimatePresence` from `"framer-motion"`
- Add `<ParticleBackground />` (standalone page)
- Wrap the three visual states in `<AnimatePresence mode="wait">` — each state is a `motion.div` keyed on the status string
- Transition: `initial={{ opacity: 0, scale: 0.95 }}` `animate={{ opacity: 1, scale: 1 }}` `exit={{ opacity: 0, scale: 0.95 }}`
- Content within each state: stagger-fade for icon, title, description, button

### VerificationBanner.jsx — Enhance

**Current**: 93 lines, amber gradient banner, resend button, dismiss.

**Changes**:
- Import `motion` from `"framer-motion"`
- Wrap banner in `motion.div` with `initial={{ y: -20 }}` `animate={{ y: 0 }}` slide-down entrance

### AuthPages.jsx — Enhance

**Current**: 201 lines, route handler for /login, /register, /verify-email, /reset-password, etc.

**Changes**:
- Import `motion` from `"framer-motion"`
- Wrap `PasswordResetPage` error state (invalid token) in `motion.div` with fade-up entry
- Keep routing logic intact

### AdminRoute.jsx — No changes (68 lines, fine as-is)

---

## Part 2: User Profile (Authenticated)

### UserProfile.jsx — Rewrite

**Current**: 624 lines, centered modal with 4 tabs, 6 floating particles using CSS animation, indigo/purple/pink theme.

**Changes**:
- Import `ParticleBackground`, `motion`, `AnimatePresence`, `layoutId`
- Replace 6 floating particle divs with `<ParticleBackground />`
- **Tab indicator**: use `layoutId="activeTab"` spring animation (same pattern as Settings.jsx and Analytics.jsx)
  - Each tab button wraps the active indicator in a `motion.div layoutId="activeTab"` with `type="spring" stiffness={300} damping={30}`
  - Tabs gradient background from `from-indigo-500/20 via-purple-500/20 to-pink-500/20` → changed to `from-cyan-500/20 via-violet-500/20 to-cyan-500/20`
- **Tab content**: wrap in `<AnimatePresence mode="wait">` with `motion.div` keyed on `activeTab`
  - `initial={{ opacity: 0, x: 10 }}` `animate={{ opacity: 1, x: 0 }}` `exit={{ opacity: 0, x: -10 }}`
- **Profile header** (avatar, name, completion bar): add `whileInView` fade-up animation
- **Avatar glow**: keep existing gradient border, update from indigo to cyan/violet if needed
- **Modal enter/exit**: keep existing scale-95/opacity transition (already framer-motion-like via CSS, but convert to motion.div `AnimatePresence` if straightforward)
- Unify all accent colors from indigo/purple/pink to cyan/violet gradient:
  - Tab active indicator: `from-cyan-500/20 via-violet-500/20 to-cyan-500/20`
  - Security score SVG gradient: `#06b6d4` (cyan) → `#8b5cf6` (violet)
  - Edit/Save buttons: `from-cyan-500 via-violet-500 to-cyan-500`
  - Header background: `from-cyan-500/10 via-violet-500/10 to-cyan-500/10`

### ProfileInfo.jsx — Enhance

**Current**: 390 lines, security score ring, stat grid, editable fields, save/cancel buttons. Rendered inside UserProfile (gets particles from parent).

**Changes**:
- Import `motion` from `"framer-motion"`
- Wrap the whole section in `motion.div` stagger container
- Security score card: `motion.div` with `whileInView`
- Stat grid (Member Since / Role / Verified): each gets `motion.div` with stagger
- Editable fields: `motion.div` per field row with stagger
- Save/Cancel/Edit buttons: `motion.button`
- Color unification: indigo/purple/pink → cyan/violet/cyan

### AccountInfo.jsx — Enhance

**Current**: 123 lines, email verification section, status cards, activity timeline. Rendered inside UserProfile (gets particles from parent).

**Changes**:
- Import `motion` from `"framer-motion"`
- Stagger fade for verification section and the two cards
- Color unification: indigo/purple → cyan/violet

### SecuritySettings.jsx — Enhance

**Current**: 816 lines, 5 sections (overview, 2FA, sessions, password change, sign out). Heaviest file. Rendered inside UserProfile (gets particles from parent).

**Changes**:
- Import `motion` from `"framer-motion"`
- Wrap each of the 5 sections in `motion.div` with staggering between sections
- Each section's internal content: staggerChildren for cards/inputs/buttons
- 2FA setup/disable overlays: wrap in `AnimatePresence` with fade
- Password strength meter: animate bar width transitions
- Sessions list: stagger rows
- Color unification: indigo/purple → cyan/violet throughout
- Section border hover: from indigo-500/30 → cyan-500/30 or violet-500/30
- Buttons: `from-cyan-500 via-violet-500 to-cyan-500` gradient

### NotificationPreferences.jsx — Enhance

**Current**: 252 lines, 5 category toggles, loading skeleton, quick action buttons. Rendered inside UserProfile (gets particles from parent).

**Changes**:
- Import `motion` from `"framer-motion"`
- Stagger for the 5 notification items (each item gets `motion.div` with stagger-fade)
- Loading skeletons: keep existing pulse animation (already fine)
- Quick action buttons: `motion.button` with whileHover scale
- Color: toggle ON gradient from `indigo-500/purple-500` → `cyan-500/violet-500`
- Section borders/icons: update to cyan/violet

### AvatarCropModal.jsx — Enhance

**Current**: 183 lines, modal overlay, Cropper integration, zoom slider, save/remove/cancel.

**Changes**:
- Import `motion`, `AnimatePresence` from `"framer-motion"`
- Backdrop: `motion.div` with fade
- Modal panel: `motion.div` with `initial={{ scale: 0.9, opacity: 0 }}` `animate={{ scale: 1, opacity: 1 }}`
- Title gradient: `from-cyan-500/10 via-violet-500/10 to-cyan-500/10`
- Buttons: Save Avatar uses `from-cyan-500 to-violet-500` gradient

---

## Error Handling & Edge Cases

- All forms already have error handling via toast (existing AuthContext error handling)
- No API logic changes — only visual layer
- Loading states in EmailVerification and SecuritySettings already exist, enhanced with AnimatePresence
- Dismissed VerificationBanner: no animation on re-appearance (component remounts naturally with slide-down)
- All color changes are purely visual — no functional impact

## Verification

- `npx eslint src/` — 0 errors, 0 warnings
- Manual checks: login flow, register flow, forgot/reset password flow, UserProfile tabs, 2FA setup/disable, session management, email verification flow

## Out of Scope

- AuthContext.jsx — no changes (business logic left intact)
- AdminRoute.jsx — no changes
- index.js — no changes
- API layer — no changes
