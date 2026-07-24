# Task 4: Add ARIA roles to canonical components

## Changes implemented

### IconButton (line 60)
- Added `console.warn("IconButton requires a \`label\` prop for accessibility")` when `label` prop is falsy
- Existing `aria-label={label}` and `title={label}` remain unchanged

### Modal (line 400)
- Added `const titleId = React.useId()` for unique title reference
- Added `role="dialog"` and `aria-modal="true"` to the container div
- Added `aria-labelledby={title ? titleId : undefined}` to link dialog to title
- Added `id={titleId}` to the `<h2>` title element

### ProgressBar (line 521)
- Added `role="progressbar"`, `aria-valuenow={value}`, `aria-valuemin={0}`, `aria-valuemax={max}` to the inner container div (the one with `className={container}`)

### Tabs (line 702)
- Added `role="tablist"` and `aria-orientation="horizontal"` to the `<nav>` element
- Added `role="tab"`, `aria-selected={activeTab === tab.id}`, and `aria-controls={tabpanel-${tab.id}}` to each tab button

### Tooltip (line 755)
- Added `const tooltipId = React.useId()` for unique tooltip reference
- Added `aria-describedby={isVisible ? tooltipId : undefined}` on the wrapper div
- Added `id={tooltipId}` and `role="tooltip"` on the tooltip element

## Files changed
- `frontend/src/styles/components.jsx` (all 5 components in one file)

## Testing
- Ran `npm run build` from `frontend/` — build succeeds
- No lint or type errors

## Self-review
- All `useId()` calls use `React.useId()` (React already imported at line 5), so no additional import needed
- `aria-labelledby` conditionally set to `undefined` when no title exists (so the attribute is omitted, not pointing to nothing)
- `aria-describedby` conditionally set to `undefined` when tooltip not visible (avoids pointing to a non-existent element)
- All changes are backward-compatible — no prop signatures changed
- No regressions in existing behavior

## Concerns
None.
