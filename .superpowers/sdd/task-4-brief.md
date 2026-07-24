### Task 4: Add ARIA roles to canonical components

**Files:**
- Modify: `frontend/src/styles/components.jsx`

- [ ] **Step 1: Add ARIA to Tabs component (line 702)**

Edit the `Tabs` component:
- `role="tablist"` and `aria-orientation="horizontal"` on the `<nav>` container
- `role="tab"`, `aria-selected`, `aria-controls` on each tab button

- [ ] **Step 2: Add ARIA to Tooltip component (line 755)**

Add:
- Unique ID generation using `React.useId()`
- `aria-describedby` on the wrapper div
- `role="tooltip"` on the tooltip element

- [ ] **Step 3: Add ARIA to IconButton (line 60)**

Add:
- Warning log if `label` prop is missing
- Keep `aria-label={label}` already present

- [ ] **Step 4: Add ARIA to Modal (line 400)**

Add:
- `role="dialog"` and `aria-modal="true"` on the container
- `aria-labelledby` pointing to the title ID
- Unique title ID using `React.useId()`

- [ ] **Step 5: Add ARIA to ProgressBar (line 521)**

Add:
- `role="progressbar"`, `aria-valuenow`, `aria-valuemin="0"`, `aria-valuemax` on the container

- [ ] **Step 6: Build and lint check**

Run: `cd frontend; npm run build`
Expected: Build succeeds.

- [ ] **Step 7: Commit**

```bash
git add frontend/src/styles/components.jsx
git commit -m "feat: add ARIA roles to Tabs, Tooltip, IconButton, Modal, ProgressBar"
```
