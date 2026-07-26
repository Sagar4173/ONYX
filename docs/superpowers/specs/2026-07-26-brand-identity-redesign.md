# ONYX Brand Identity Redesign

## Objective
Elevate ONYX from a functional dark-themed dashboard to a premium security intelligence platform with a cohesive, top-tier brand identity.

## Logo — Primary Wordmark

**Core decision:** The primary logo is a custom wordmark, not an icon.

The wordmark "ONYX" set in bold weight with tight letter-spacing. A faceted ring icon serves as the "O" and as the standalone favicon.

**Icon detail:** A precision circular ring with a single faceted cut on the upper-right edge. Communicates: gemstone (Onyx), seal (security), and lens (intelligence) in one minimal shape. No hexagon, no shield, no lock, no eye.

**Variants:**
| Variant | Description |
|---|---|
| Full color | Icon (faceted ring) + wordmark, cyan-violet gradient |
| Icon only | Faceted ring, used as favicon and sidebar icon |
| Monochrome | White/light, used on dark backgrounds, print |

## Color Palette — Unified

**Problem:** `theme.js` uses blue (`#3b82f6`) as primary, but the brand expression uses cyan (`#06b6d4`) + violet (`#8b5cf6`). This split creates inconsistency.

**Resolution:** Cyan + violet become the unified single source of truth.

| Token | Value | Usage |
|---|---|---|
| Obsidian | `#05080f` | Deepest background |
| Midnight | `#0a0318` | Primary surface |
| Violet Dark | `#0f0520` | Elevated surfaces, card backgrounds |
| Electric Cyan | `#00e5ff` | Primary accent, highlights, CTAs |
| Royal Violet | `#7c3aed` | Secondary accent, gradients |
| Amber | `#f59e0b` | Warning/alert accent (upgrade from yellow) |
| Text Primary | `#f9fafb` | Headings, body |
| Text Secondary | `#d1d5db` | Secondary text |
| Text Muted | `#9ca3af` | Hints, metadata |

**Changes from current:**
- Primary-500: `#3b82f6` (blue) → `#06b6d4` (cyan) or `#00e5ff` (electric cyan)
- Background primary: `#0a0e1a` → `#05080f` (deeper)
- Background secondary: `#111827` → `#0a0318`
- All blue-400/500 accent references → cyan-400/500 or violet-500 equivalents
- Warning: yellow-based → amber-based (`#f59e0b`)

## Files to Modify

| File | Change |
|---|---|
| `public/onyx-logo.svg` | Replace with new wordmark SVG |
| `src/components/common/OnyxLogo.jsx` | Update with faceted ring + wordmark |
| `public/index.html` | Add favicon reference |
| `src/styles/theme.js` | Unify primary → cyan; update bg colors |
| `src/styles/classNames.js` | Replace blue references |
| `src/styles/components.jsx` | Replace blue references |
| `src/constants/brand.js` | Update class tokens |
| `tailwind.config.js` | Update primary color ramp |

## Implementation Order

1. Create production SVG assets (wordmark, icon, favicon)
2. Update OnyxLogo component
3. Unify theme.js color tokens
4. Update classNames.js, brand.js, tailwind.config.js
5. Update logo references in Sidebar, Header, LandingPage
6. Add favicon
7. Verify lint, test, build

## Verification
- `npm run lint` — 0 errors
- `npm test` — 159 tests passing
- `npm run build` — clean build
- `npm run build-storybook` — clean build
- Visual check: sidebar, header, about page, landing page, footer all show new logo
