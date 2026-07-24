### Task 7: Consolidate Dashboard stat cards to canonical StatCard

**Background:** The Dashboard page (`pages/Dashboard.jsx`) has an inline `StatCard` component (lines 75-149) with rich features: animated counter, gradient backgrounds, trend indicators, hover effects, subtitles. The canonical `StatCard` in `styles/components.jsx:479` is simpler. We need to enhance the canonical `StatCard` to support the Dashboard's features, then use it — preserving quality while achieving consistency.

**Files:**
- Modify: `frontend/src/styles/components.jsx` (enhance `StatCard`)
- Modify: `frontend/src/pages/Dashboard.jsx` (use canonical `StatCard`)

**Key constraint:** Quality first. The enhanced `StatCard` must preserve the animated counter, gradient icon containers, trend indicators, subtitles, and hover effects that the Dashboard currently has.

- [ ] **Step 1: Enhance the canonical StatCard in styles/components.jsx**

The current canonical `StatCard` at line 479:
```jsx
export const StatCard = ({
  title,
  value,
  change,
  changeType = "neutral",
  icon,
  className = "",
}) => {
  const changeColors = {
    increase: "text-green-400",
    decrease: "text-red-400",
    neutral: "text-gray-400",
  };

  return (
    <Card className={className}>
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-gray-400">{title}</p>
          <p className="text-2xl font-bold text-white mt-1">{value}</p>
          {change !== undefined && (
            <p className={`text-sm mt-1 ${changeColors[changeType]}`}>
              {changeType === "increase" && "↑"}
              {changeType === "decrease" && "↓"}
              {change}
            </p>
          )}
        </div>
        {icon && (
          <div className="p-3 bg-gray-700/50 rounded-lg text-gray-400">
            {icon}
          </div>
        )}
      </div>
    </Card>
  );
};
```

Enhance it to accept these additional optional props while keeping everything backwards-compatible:
- `trend` (number) — trend percentage
- `trendPositive` (boolean) — whether higher is better
- `subtitle` (string) — secondary description
- `gradient` (string) — Tailwind gradient class for icon container
- `animated` (boolean) — enable animated counter
- `onClick` (function) — click handler
- `iconSize` (string) — size class for icon

Add an `AnimatedCounter` helper component inside the same file (or import it).

Make the enhanced version use `<Card>` as its base wrapper.

- [ ] **Step 2: Update Dashboard.jsx to use the canonical StatCard**

After enhancing `StatCard`, update `Dashboard.jsx`:
- Remove the inline `StatCard` component (lines 75-149)
- Remove the inline `AnimatedCounter` component (lines 38-70) since it's now in components.jsx
- Import `StatCard` from `../styles/components`
- Update the `statsCards` data array to pass props matching the enhanced interface
- Keep all existing functionality (animations, hover effects, click handlers, etc.)

The statsCards array currently at lines 458-495 passes objects with `label`, `value`, `trend`, `trendPositive`, `icon`, `gradient`, `subtitle`. Map these directly to enhanced StatCard props:
- `label` → `title`
- `value` → `value`
- `trend` → `trend`
- `trendPositive` → `trendPositive`
- `icon` → `<stat.icon className="h-5 w-5 text-white" />`
- `gradient` → `gradient`
- `subtitle` → `subtitle`

- [ ] **Step 3: Build check**

Run: `cd frontend; npm run build`
Expected: Build succeeds.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/styles/components.jsx frontend/src/pages/Dashboard.jsx
git commit -m "refactor: consolidate Dashboard stat cards to canonical StatCard"
```
