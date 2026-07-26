# Task 1 Report: ParticleBackground.jsx

## Implemented
- `frontend/src/components/projects/ParticleBackground.jsx` — CSS-only ambient particle effect with 60 particles
- Added `@keyframes particle-float-slow`, `@keyframes particle-float-fast`, `@keyframes particle-sway` to `src/index.css`
- Added `.animate-particle-slow` and `.animate-particle-fast` utility classes

**Files changed:**
- Created: `frontend/src/components/projects/ParticleBackground.jsx` (56 lines)
- Modified: `frontend/src/index.css` (added 34 lines)

## Tested
- ESLint: 0 errors, 0 warnings (1 informational useMemo warning)
- Prettier: clean

## Self-Review
- `useMemo` with `[isScanActive]` dependency stabilizes particle positions across renders
- 60 particles with random positions, sizes (1-3px), colors (60% cyan / 40% violet), drift/sway timing, box-shadow glow
- CSS variables for per-particle duration control
