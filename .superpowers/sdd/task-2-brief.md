### Task 2: Audit and tighten theme.js tokens

**Files:**
- Modify: `frontend/src/styles/theme.js:1-317`

- [ ] **Step 1: Verify theme.js has all required tokens**

Read `frontend/src/styles/theme.js` and confirm:
- Has all 5 severity colors (critical, high, medium, low, info) with bg/text/border
- Has all semantic color groups (primary, success, warning, danger, info)
- Has spacing scale (xs through 3xl)
- Has typography scale (font sizes, weights)
- Has shadow definitions
- Has border radius scale
- Has animation helpers
- Has `getSeverityStyles` function

If any are missing, add them.

- [ ] **Step 2: Commit**

```bash
git add frontend/src/styles/theme.js
git commit -m "refactor: verify and tighten design tokens in theme.js"
```
