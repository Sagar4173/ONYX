# Auth & User Profile Remaster — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remaster all 19 auth module files with ParticleBackground, framer-motion animations, and unified cyan/violet theme.

**Architecture:** Two subsystems — AuthPages (unauthenticated: AuthModal + forms + success states + EmailVerification) and UserProfile (authenticated: modal with 4 tabs + sub-components). Both subsystems get ParticleBackground at the top level, framer-motion stagger/AnimatePresence throughout, and color unification from indigo/purple to cyan/violet.

**Tech Stack:** React, framer-motion, Tailwind CSS, Heroicons

## Global Constraints

- Zero new npm dependencies
- All framer-motion imports from `"framer-motion"`
- ParticleBackground from `"../../styles/components"` (within auth folder)
- Lint: `npx eslint src/` must pass with 0 errors, 0 warnings
- ONYX colors: cyan-400, violet-500, gray-900/950
- No API logic changes — visual layer only
- Commit after each task

---

### Task 1: AuthModal.jsx — Rewrite with ParticleBackground + AnimatePresence

**Files:**
- Modify: `frontend/src/components/auth/AuthModal.jsx`

**Interfaces:**
- Consumes: ParticleBackground from `../../styles/components`, motion/AnimatePresence from framer-motion, existing form sub-components
- Produces: Enhanced AuthModal with animated view transitions

- [ ] **Step 1: Add imports at top of AuthModal.jsx**

Replace current imports with additions. Add after existing imports:
```jsx
import { motion, AnimatePresence } from "framer-motion";
import { ParticleBackground } from "../../styles/components";
```

- [ ] **Step 2: Replace blob divs with ParticleBackground**

Replace the two animated blob divs inside the outer container `<div className="fixed inset-0 z-50 overflow-hidden bg-gray-950">`:

```jsx
{/* Particle Background */}
<ParticleBackground />
```

Remove both blob divs (lines ~261-271) and replace with `<ParticleBackground />`.

- [ ] **Step 3: Wrap view rendering in AnimatePresence**

Replace `renderCurrentView()` call with AnimatePresence:

```jsx
<AnimatePresence mode="wait">
  <motion.div
    key={currentView}
    initial={{ opacity: 0, x: 20 }}
    animate={{ opacity: 1, x: 0 }}
    exit={{ opacity: 0, x: -20 }}
    transition={{ duration: 0.2 }}
  >
    {renderCurrentView()}
  </motion.div>
</AnimatePresence>
```

- [ ] **Step 4: Animate branding features with stagger**

Wrap the features map in a motion.div stagger container:

```jsx
<motion.div
  className="space-y-6"
  initial="hidden"
  animate="visible"
  variants={{
    hidden: {},
    visible: { transition: { staggerChildren: 0.08 } },
  }}
>
  {branding.features.map((feature, index) => (
    <motion.div
      key={index}
      variants={{
        hidden: { opacity: 0, y: 10 },
        visible: { opacity: 1, y: 0 },
      }}
      ...
    >
      ...existing feature content...
    </motion.div>
  ))}
</motion.div>
```

- [ ] **Step 5: Animate branding title/subtitle**

Wrap the branding header content (logo, title, subtitle, description) in AnimatePresence:

```jsx
<AnimatePresence mode="wait">
  <motion.div
    key={currentView}
    initial={{ opacity: 0, y: -5 }}
    animate={{ opacity: 1, y: 0 }}
    exit={{ opacity: 0, y: 5 }}
    transition={{ duration: 0.15 }}
  >
    ...existing branding header...
  </motion.div>
</AnimatePresence>
```

- [ ] **Step 6: Run lint and commit**

```bash
npx eslint src/
git add frontend/src/components/auth/AuthModal.jsx
git commit -m "feat: AuthModal — ParticleBackground, AnimatePresence view transitions, stagger features"
```

---

### Task 2: LoginForm.jsx + RegisterForm.jsx — framer-motion stagger

**Files:**
- Modify: `frontend/src/components/auth/LoginForm.jsx`
- Modify: `frontend/src/components/auth/RegisterForm.jsx`

- [ ] **Step 1: Add motion import to LoginForm.jsx**

```jsx
import { motion, AnimatePresence } from "framer-motion";
```

- [ ] **Step 2: Wrap LoginForm in motion.form with stagger**

Find the opening `<form` tag and replace with:

```jsx
<motion.form
  onSubmit={handleSubmit}
  className="space-y-6"
  initial="hidden"
  animate="visible"
  variants={{
    hidden: {},
    visible: { transition: { staggerChildren: 0.04 } },
  }}
>
```

Find the closing `</form>` tag and replace with `</motion.form>`.

Wrap each form field/button in `motion.div` with variants:

```jsx
<motion.div
  variants={{
    hidden: { opacity: 0, y: 8 },
    visible: { opacity: 1, y: 0 },
  }}
>
  ...existing field content...
</motion.div>
```

Apply this to: email/username field, password field, remember-me row, submit button, trust badges.

- [ ] **Step 3: Wrap 2FA section in AnimatePresence**

The 2FA code entry view (returned early when `requires2FA` is true) — wrap the outer div in AnimatePresence:

```jsx
<AnimatePresence mode="wait">
  {requires2FA ? (
    <motion.div
      key="2fa"
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      className="p-8 md:p-10"
    >
      ...existing 2FA content...
    </motion.div>
  ) : (
    <motion.div
      key="login"
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      className="p-8 md:p-10"
    >
      ...existing login content...
    </motion.div>
  )}
</AnimatePresence>
```

- [ ] **Step 4: Apply same pattern to RegisterForm.jsx**

Add `motion` import, wrap `<form>` as `motion.form` with stagger, wrap each field group in `motion.div` with variants. Apply stagger to: username/full_name grid, email field, password field with validation, confirm password field, submit button, trust badges.

- [ ] **Step 5: Run lint and commit**

```bash
npx eslint src/
git add frontend/src/components/auth/LoginForm.jsx frontend/src/components/auth/RegisterForm.jsx
git commit -m "feat: LoginForm + RegisterForm — framer-motion stagger, AnimatePresence 2FA toggle"
```

---

### Task 3: ForgotPasswordForm.jsx + ResetPasswordForm.jsx — framer-motion entry

**Files:**
- Modify: `frontend/src/components/auth/ForgotPasswordForm.jsx`
- Modify: `frontend/src/components/auth/ResetPasswordForm.jsx`

- [ ] **Step 1: Add motion import to ForgotPasswordForm.jsx**

```jsx
import { motion } from "framer-motion";
```

- [ ] **Step 2: Wrap form with stagger**

Wrap `<form>` → `<motion.form>` with `initial="hidden"` `animate="visible"` and stagger variants. Wrap label/input/button each in `motion.div` with fade-up variants (same pattern as Task 2 Step 2).

- [ ] **Step 3: Apply same pattern to ResetPasswordForm.jsx**

Add `motion` import. Wrap `<form>` → `<motion.form>` with stagger. Wrap each field group (new password, confirm password, password validation indicators, submit button, back link) in `motion.div` with variants.

- [ ] **Step 4: Run lint and commit**

```bash
npx eslint src/
git add frontend/src/components/auth/ForgotPasswordForm.jsx frontend/src/components/auth/ResetPasswordForm.jsx
git commit -m "feat: ForgotPasswordForm + ResetPasswordForm — framer-motion stagger entry"
```

---

### Task 4: RegistrationSuccess.jsx + ForgotPasswordSuccess.jsx — framer-motion stagger

**Files:**
- Modify: `frontend/src/components/auth/RegistrationSuccess.jsx`
- Modify: `frontend/src/components/auth/ForgotPasswordSuccess.jsx`

- [ ] **Step 1: Add motion import to RegistrationSuccess.jsx**

```jsx
import { motion } from "framer-motion";
```

- [ ] **Step 2: Wrap content in stagger container**

Replace the outer `<div className="relative min-h-[500px] p-8">` with `motion.div`:

```jsx
<motion.div
  className="relative min-h-[500px] p-8"
  initial="hidden"
  animate="visible"
  variants={{
    hidden: {},
    visible: { transition: { staggerChildren: 0.06 } },
  }}
>
```

Replace closing `</div>` with `</motion.div>`.

Wrap each content element in `motion.div` with fade-up variants:
- Remove the blob divs (lines ~69-75)
- Icon container
- Title
- Description paragraphs
- Email display
- Info box
- Resend button
- Back to login link

- [ ] **Step 3: Apply same pattern to ForgotPasswordSuccess.jsx**

Add `motion` import. Wrap outer div as `motion.div` stagger container. Remove blob divs (lines ~12-18). Wrap each element in `motion.div` with variants.

- [ ] **Step 4: Run lint and commit**

```bash
npx eslint src/
git add frontend/src/components/auth/RegistrationSuccess.jsx frontend/src/components/auth/ForgotPasswordSuccess.jsx
git commit -m "feat: RegistrationSuccess + ForgotPasswordSuccess — framer-motion stagger, remove blob backgrounds"
```

---

### Task 5: EmailVerification.jsx — Rewrite with AnimatePresence states

**Files:**
- Modify: `frontend/src/components/auth/EmailVerification.jsx`

- [ ] **Step 1: Add framer-motion imports**

```jsx
import { motion, AnimatePresence } from "framer-motion";
import { ParticleBackground } from "../../styles/components";
```

- [ ] **Step 2: Replace blob background with ParticleBackground**

In the loading state (`if (isVerifying)`), remove the blob div (lines ~96-98) and replace with `<ParticleBackground />`.

In the success state (`if (verificationStatus === "success")`), add `<ParticleBackground />` at the top of the returned div.

In the error state (`if (verificationStatus === "error")`), add `<ParticleBackground />` at the top of each returned div.

- [ ] **Step 3: Wrap states in AnimatePresence**

The three visual states (loading, success, error) each return their own JSX. Wrap the outer container logic so only one state renders at a time with animations:

For each state's outer div, add motion:

For loading state:
```jsx
<motion.div
  key="verifying"
  initial={{ opacity: 0, scale: 0.95 }}
  animate={{ opacity: 1, scale: 1 }}
  exit={{ opacity: 0, scale: 0.95 }}
  className="max-w-md mx-auto ..."
>
  <ParticleBackground />
  ...existing content...
</motion.div>
```

For success state — same pattern with `key="success"`.

For error state — same pattern with `key="error"`.

For the "already verified" variant inside error — same pattern with `key="already-verified"`.

The outer container structure should use `AnimatePresence mode="wait"` — this means wrapping the conditional rendering:

```jsx
<AnimatePresence mode="wait">
  {isVerifying ? (
    <motion.div key="verifying" ...>{/* loading content */}</motion.div>
  ) : verificationStatus === "success" ? (
    <motion.div key="success" ...>{/* success content */}</motion.div>
  ) : verificationStatus === "error" ? (
    <motion.div key="error" ...>{/* error content */}</motion.div>
  ) : null}
</AnimatePresence>
```

- [ ] **Step 4: Add stagger to content elements**

Within each state, add stagger container for the icon, title, description, buttons.

- [ ] **Step 5: Run lint and commit**

```bash
npx eslint src/
git add frontend/src/components/auth/EmailVerification.jsx
git commit -m "feat: EmailVerification — ParticleBackground, AnimatePresence state transitions, stagger"
```

---

### Task 6: AuthPages.jsx + VerificationBanner.jsx — minor framer-motion

**Files:**
- Modify: `frontend/src/components/auth/AuthPages.jsx`
- Modify: `frontend/src/components/auth/VerificationBanner.jsx`

- [ ] **Step 1: Add motion to AuthPages.jsx PasswordResetPage error state**

Add import:
```jsx
import { motion } from "framer-motion";
```

Wrap the error state div (invalid token, lines ~77-90) in `motion.div`:

```jsx
<motion.div
  initial={{ opacity: 0, y: 10 }}
  animate={{ opacity: 1, y: 0 }}
  className="max-w-md mx-auto ..."
>
  ...existing error content...
</motion.div>
```

- [ ] **Step 2: Add motion import to VerificationBanner.jsx**

```jsx
import { motion } from "framer-motion";
```

- [ ] **Step 3: Wrap VerificationBanner with slide-down animation**

Wrap the outer div with motion.div:

```jsx
<motion.div
  initial={{ y: -20 }}
  animate={{ y: 0 }}
  transition={{ type: "spring", stiffness: 200, damping: 25 }}
  className="bg-gradient-to-r ..."
>
  ...existing banner content...
</motion.div>
```

- [ ] **Step 4: Run lint and commit**

```bash
npx eslint src/
git add frontend/src/components/auth/AuthPages.jsx frontend/src/components/auth/VerificationBanner.jsx
git commit -m "feat: AuthPages + VerificationBanner — framer-motion entry animations"
```

---

### Task 7: UserProfile.jsx — Rewrite with ParticleBackground, layoutId tabs, AnimatePresence

**Files:**
- Modify: `frontend/src/components/auth/UserProfile.jsx`

- [ ] **Step 1: Add framer-motion imports**

```jsx
import { motion, AnimatePresence } from "framer-motion";
import { ParticleBackground } from "../../styles/components";
```

- [ ] **Step 2: Replace 6 floating particle divs with ParticleBackground**

Remove the 6 floating particle divs (lines ~394-406) and replace with:

```jsx
<ParticleBackground />
```

- [ ] **Step 3: Convert tabs to layoutId spring animation**

Replace the tab button mapping (lines ~532-554) with motion buttons using layoutId:

```jsx
<div className="flex gap-1 mt-6 p-1.5 bg-gray-800/60 rounded-2xl backdrop-blur-sm border border-gray-700/50">
  {tabs.map((tab) => (
    <button
      key={tab.key}
      onClick={() => setActiveTab(tab.key)}
      className={`relative flex-1 flex items-center justify-center gap-2 px-4 py-3 rounded-xl text-sm font-medium focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500 focus-visible:ring-offset-2 focus-visible:ring-offset-gray-900 transition-all duration-300 ${
        activeTab === tab.key
          ? "text-white"
          : "text-gray-400 hover:text-gray-300 hover:bg-gray-700/50"
      }`}
    >
      {activeTab === tab.key && (
        <motion.div
          layoutId="activeProfileTab"
          className="absolute inset-0 bg-gradient-to-r from-cyan-500/20 via-violet-500/20 to-cyan-500/20 rounded-xl border border-cyan-500/30 shadow-lg shadow-cyan-500/10"
          transition={{ type: "spring", stiffness: 300, damping: 30 }}
        />
      )}
      <tab.icon
        className={`h-4 w-4 relative z-10 transition-transform duration-300 ${activeTab === tab.key ? "scale-110" : ""}`}
      />
      <span className="relative z-10 hidden sm:inline">{tab.label}</span>
      {tab.key === "security" && securityScore.score < 80 && (
        <span className="relative z-10 w-2 h-2 bg-amber-500 rounded-full animate-pulse" />
      )}
    </button>
  ))}
</div>
```

- [ ] **Step 4: Wrap tab content in AnimatePresence**

Replace the conditional tab rendering (lines ~561-600) with AnimatePresence:

```jsx
<AnimatePresence mode="wait">
  <motion.div
    key={activeTab}
    initial={{ opacity: 0, x: 10 }}
    animate={{ opacity: 1, x: 0 }}
    exit={{ opacity: 0, x: -10 }}
    transition={{ duration: 0.15 }}
  >
    {activeTab === "profile" && (
      <ProfileInfo ...existing props... />
    )}
    {activeTab === "account" && (
      <AccountInfo ...existing props... />
    )}
    {activeTab === "security" && (
      <SecuritySettings ...existing props... />
    )}
    {activeTab === "notifications" && <NotificationPreferences />}
  </motion.div>
</AnimatePresence>
```

- [ ] **Step 5: Unify colors from indigo/purple/pink to cyan/violet**

Change all accent colors in UserProfile.jsx:

- Tab active indicator gradient: `from-indigo-500/20 via-purple-500/20 to-pink-500/20` → `from-cyan-500/20 via-violet-500/20 to-cyan-500/20`
- Tab active border: `border-indigo-500/30` → `border-cyan-500/30`
- Tab shadow: `shadow-indigo-500/10` → `shadow-cyan-500/10`
- Avatar glow: `from-indigo-500 via-purple-500 to-pink-500` → `from-cyan-500 via-violet-500 to-cyan-500`
- Avatar bg gradient: leave `avatarGradient` dynamic as-is
- Save button gradient: `from-indigo-500 via-purple-500 to-pink-500` → `from-cyan-500 via-violet-500 to-cyan-500`
- Modal shadow: `shadow-purple-500/10` → `shadow-cyan-500/10`
- Profile completion bar: `from-indigo-500 via-purple-500 to-pink-500` → `from-cyan-500 via-violet-500 to-cyan-500`
- Modal background gradient blobs (lines ~417-423): these are already indigo/purple/cyan/violet. Update: `from-indigo-500/20 via-purple-500/15 to-transparent` → `from-cyan-500/20 via-violet-500/15 to-transparent`

- [ ] **Step 6: Animate modal enter/exit**

Add motion to the modal wrapper div (the one with scale-95 opacity transition, line ~411):

```jsx
<motion.div
  initial={{ opacity: 0, scale: 0.95, y: 20 }}
  animate={{ opacity: 1, scale: 1, y: 0 }}
  exit={{ opacity: 0, scale: 0.95, y: 20 }}
  transition={{ type: "spring", stiffness: 300, damping: 30 }}
  className={`relative w-full max-w-3xl ...`}
>
```

- [ ] **Step 7: Run lint and commit**

```bash
npx eslint src/
git add frontend/src/components/auth/UserProfile.jsx
git commit -m "feat: UserProfile — ParticleBackground, layoutId tabs, AnimatePresence content, cyan/violet unification"
```

---

### Task 8: ProfileInfo.jsx + AccountInfo.jsx — framer-motion stagger + color unification

**Files:**
- Modify: `frontend/src/components/auth/ProfileInfo.jsx`
- Modify: `frontend/src/components/auth/AccountInfo.jsx`

- [ ] **Step 1: Add motion import to ProfileInfo.jsx**

```jsx
import { motion } from "framer-motion";
```

- [ ] **Step 2: Wrap ProfileInfo content in stagger container**

Wrap the outer div `<div className="space-y-5 animate-fadeIn">` as `motion.div` stagger:

```jsx
<motion.div
  className="space-y-5"
  initial="hidden"
  animate="visible"
  variants={{
    hidden: {},
    visible: { transition: { staggerChildren: 0.06 } },
  }}
>
```

Replace closing `</div>` with `</motion.div>`.

Wrap each section (security score card, stat grid, field rows, edit buttons) in `motion.div` with fade-up variants.

- [ ] **Step 3: Color unification in ProfileInfo.jsx**

Update all accent colors from indigo/purple/pink to cyan/violet:

- Security score SVG gradient: `#6366f1` → `#06b6d4` (cyan-400), `#a855f7` → `#8b5cf6` (violet-500)
- Stat grid card gradients: `from-indigo-500/10 to-purple-500/10` → `from-cyan-500/10 to-violet-500/10`, etc.
- Card borders: `border-indigo-500/20` → `border-cyan-500/20`
- Edit/Save buttons: `from-indigo-500 via-purple-500 to-pink-500` → `from-cyan-500 via-violet-500 to-cyan-500`
- Field hover borders: `hover:border-indigo-500/30` → `hover:border-cyan-500/30` (or `violet-500/30`)

- [ ] **Step 4: Add motion import to AccountInfo.jsx**

```jsx
import { motion } from "framer-motion";
```

- [ ] **Step 5: Wrap AccountInfo in stagger container**

Same pattern — wrap outer div in `motion.div` stagger, wrap each section in `motion.div` with variants.

- [ ] **Step 6: Color unification in AccountInfo.jsx**

- Verification icon gradient: `from-emerald-500/30 to-green-500/20` stays (green is correct for success)
- Status icon gradient: `from-cyan-500/20 to-violet-500/20`
- Activity icon gradient: `from-violet-500/20 to-cyan-500/20`
- Role badge: `from-indigo-500/20 to-purple-500/20` → `from-cyan-500/20 to-violet-500/20`

- [ ] **Step 7: Run lint and commit**

```bash
npx eslint src/
git add frontend/src/components/auth/ProfileInfo.jsx frontend/src/components/auth/AccountInfo.jsx
git commit -m "feat: ProfileInfo + AccountInfo — framer-motion stagger, cyan/violet colors"
```

---

### Task 9: SecuritySettings.jsx — framer-motion stagger + color unification

**Files:**
- Modify: `frontend/src/components/auth/SecuritySettings.jsx`

- [ ] **Step 1: Add motion import**

```jsx
import { motion, AnimatePresence } from "framer-motion";
```

- [ ] **Step 2: Wrap whole section in stagger container**

Wrap `<div className="space-y-5 animate-fadeIn">` → `<motion.div className="space-y-5" initial="hidden" animate="visible" stagger children>`.

- [ ] **Step 3: Animate each of the 5 content sections**

Wrap each section (Security Overview, 2FA, Active Sessions, Change Password, Sign Out) in `motion.div` with stagger and variants.

For the 2FA overlay sections (setup and disable), wrap them in `AnimatePresence`:

```jsx
<AnimatePresence>
  {showTwoFactorSetup && twoFactorSetupData && (
    <motion.div
      key="2fa-setup"
      initial={{ opacity: 0, height: 0 }}
      animate={{ opacity: 1, height: "auto" }}
      exit={{ opacity: 0, height: 0 }}
      transition={{ duration: 0.2 }}
      className="mt-6 p-5 bg-gray-900/60 rounded-xl border border-violet-500/20"
    >
      ...existing 2FA setup content...
    </motion.div>
  )}
</AnimatePresence>
```

Same pattern for `showTwoFactorDisable`.

- [ ] **Step 4: Animate sessions list rows**

Wrap session items in `motion.div` with stagger.

- [ ] **Step 5: Color unification**

Replace all indigo/purple/pink accent with cyan/violet:

- 2FA section icon gradient: `from-purple-500/20 to-pink-500/20` → `from-violet-500/20 to-cyan-500/20`
- Sessions icon gradient: `from-cyan-500/20 to-violet-500/20` (already close, keep)
- Password section icon gradient: `from-indigo-500/20 to-purple-500/20` → `from-cyan-500/20 to-violet-500/20`
- Current session badge: `from-indigo-500/10 to-purple-500/10` → `from-cyan-500/10 to-violet-500/10`
- Update password button: `from-indigo-500 via-purple-500 to-pink-500` → `from-cyan-500 via-violet-500 to-cyan-500`
- Enable 2FA button: `from-purple-500 to-pink-500` → `from-violet-500 to-cyan-500`

- [ ] **Step 6: Run lint and commit**

```bash
npx eslint src/
git add frontend/src/components/auth/SecuritySettings.jsx
git commit -m "feat: SecuritySettings — framer-motion stagger sections, AnimatePresence 2FA overlays, cyan/violet colors"
```

---

### Task 10: NotificationPreferences.jsx + AvatarCropModal.jsx — framer-motion + colors

**Files:**
- Modify: `frontend/src/components/auth/NotificationPreferences.jsx`
- Modify: `frontend/src/components/auth/AvatarCropModal.jsx`

- [ ] **Step 1: Add motion to NotificationPreferences.jsx**

```jsx
import { motion } from "framer-motion";
```

Wrap outer div → `motion.div` stagger. Wrap each notification category item in `motion.div` with variants. Color update: toggle ON gradient from `from-indigo-500 to-purple-500` → `from-cyan-500 to-violet-500`.

- [ ] **Step 2: Add motion + AnimatePresence to AvatarCropModal.jsx**

```jsx
import { motion } from "framer-motion";
```

Wrap backdrop div with `motion.div` fade. Wrap modal panel div with `motion.div scale-in`:

```jsx
<motion.div
  initial={{ opacity: 0, scale: 0.9 }}
  animate={{ opacity: 1, scale: 1 }}
  exit={{ opacity: 0, scale: 0.9 }}
  transition={{ type: "spring", stiffness: 300, damping: 30 }}
  className="bg-gray-900 border border-gray-700/50 rounded-3xl shadow-2xl w-full max-w-xl overflow-hidden"
>
```

Color update: header gradient from `from-indigo-500/10 to-purple-500/10` → `from-cyan-500/10 to-violet-500/10`. Save button from `from-indigo-500 to-purple-500` → `from-cyan-500 to-violet-500`.

- [ ] **Step 3: Run lint and commit**

```bash
npx eslint src/
git add frontend/src/components/auth/NotificationPreferences.jsx frontend/src/components/auth/AvatarCropModal.jsx
git commit -m "feat: NotificationPreferences + AvatarCropModal — framer-motion stagger, cyan/violet colors"
```
