# Dashboard Polish — Design Spec

## Overview

Tighten the Dashboard's visual details to match the auth + navigation design language. The component already uses `GlassCard`, `StatCard`, `SectionHeader`, `PageContainer` — this spec covers the remaining gaps.

## Changes

| Element | Line | Current | After |
|---|---|---|---|
| "New Project" CTA button | 434-441 | Raw `<Link>` with `rounded-xl from-blue-500 to-purple-600` | `<Button gradient>` from design system — pill `rounded-full`, `px-8 py-3`, `from-cyan-400 via-violet-500 to-cyan-400` |
| QuickAction button hover | 198 | `hover:scale-[1.03] hover:border-gray-600/50` | `hover:-translate-y-1 hover:shadow-lg hover:shadow-cyan-500/10 hover:border-cyan-500/30` |
| "View all" reports link | 518 | `text-blue-400 hover:text-blue-300` | `text-cyan-400 hover:text-cyan-300` |
| Recent scans loading spinner | 527 | `border-blue-500` | `border-cyan-500` |
| Live activity notification icon | 574-575 | `bg-blue-500/10 text-blue-400` | `bg-cyan-500/10 text-cyan-400` |

## File

- Modify: `pages/Dashboard.jsx`

## Verification

- `npm run build` passes
- "New Project" button is pill-shaped with auth design gradient
- QuickAction buttons lift on hover with cyan shadow glow
- "View all" link is cyan
- Loading spinner is cyan
- Live activity icons are cyan
