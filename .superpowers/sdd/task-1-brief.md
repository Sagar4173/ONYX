### Task 1: ParticleBackground.jsx

**Files:**
- Create: `src/components/projects/ParticleBackground.jsx`

**Interface:**
- Consumes: `isScanActive: boolean`
- Produces: A CSS-only particle layer rendered as a fixed-position div behind all content

- [ ] **Step 1: Create the component**

```jsx
const ParticleBackground = ({ isScanActive = false }) => {
  const particleCount = 60;
  const particles = useMemo(() => {
    const p = [];
    const isFast = isScanActive;
    for (let i = 0; i < particleCount; i++) {
      const x = Math.random() * 100;
      const y = Math.random() * 100;
      const size = 1 + Math.random() * 2;
      const drift = 8 + Math.random() * 12;
      const sway = 12 + Math.random() * 8;
      const delay = Math.random() * 10;
      const isViolet = Math.random() > 0.6;
      const color = isViolet ? 'rgba(139,92,246,0.12)' : 'rgba(6,182,212,0.15)';
      p.push({ x, y, size, drift, sway, delay, color, isViolet });
    }
    return p;
  }, [isScanActive]);

  return (
    <div className="fixed inset-0 pointer-events-none overflow-hidden z-0" aria-hidden="true">
      {particles.map((p, i) => (
        <div
          key={i}
          className={`absolute rounded-full ${isScanActive ? 'animate-particle-fast' : 'animate-particle-slow'}`}
          style={{
            left: `${p.x}%`, top: `${p.y}%`,
            width: `${p.size}px`, height: `${p.size}px`,
            backgroundColor: p.color,
            animationDelay: `${p.delay}s`,
            animationDuration: `${isScanActive ? p.drift * 0.5 : p.drift}s, ${isScanActive ? p.sway * 0.5 : p.sway}s`,
            boxShadow: `0 0 ${p.size * 2}px ${p.color}`,
          }}
        />
      ))}
    </div>
  );
};
```

- [ ] **Step 2: Add keyframe animations to index.css**

```css
/* In src/index.css */
@keyframes particle-float-slow {
  0%, 100% { transform: translateY(0) translateX(0); opacity: 0.4; }
  25% { transform: translateY(-30px) translateX(15px); opacity: 0.8; }
  50% { transform: translateY(-10px) translateX(-10px); opacity: 0.5; }
  75% { transform: translateY(-40px) translateX(5px); opacity: 0.7; }
}
@keyframes particle-float-fast {
  0%, 100% { transform: translateY(0) translateX(0); opacity: 0.6; }
  25% { transform: translateY(-60px) translateX(30px); opacity: 1; }
  50% { transform: translateY(-20px) translateX(-20px); opacity: 0.8; }
  75% { transform: translateY(-80px) translateX(10px); opacity: 0.9; }
}
```

```css
.animate-particle-slow { animation: particle-float-slow var(--drift, 12s) ease-in-out infinite, particle-sway var(--sway, 15s) ease-in-out infinite; }
.animate-particle-fast { animation: particle-float-fast calc(var(--drift, 12s) * 0.5) ease-in-out infinite, particle-sway calc(var(--sway, 15s) * 0.5) ease-in-out infinite; }
```

- [ ] **Step 3: Verify with lint**

Run: `npx eslint src/components/projects/ParticleBackground.jsx`
Expected: 0 errors, 0 warnings

---

