// Shared visual primitives for Nexload concepts
// Icons, progress visualizations, mascot, mini placeholder thumbnails.

const NX_COLORS = {
  teal: 'oklch(0.82 0.14 200)',
  tealDeep: 'oklch(0.65 0.18 210)',
  violet: 'oklch(0.72 0.18 295)',
  violetDeep: 'oklch(0.55 0.22 290)',
  warn: 'oklch(0.78 0.14 60)',
  good: 'oklch(0.78 0.16 150)',
  coral: 'oklch(0.75 0.16 30)',
};

// ── Icons (stroked, 1.5px) ────────────────────────────────────
const Icon = ({ d, size = 18, stroke = 'currentColor', sw = 1.5, fill = 'none', children, style }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill={fill} stroke={stroke}
       strokeWidth={sw} strokeLinecap="round" strokeLinejoin="round" style={style}>
    {d ? <path d={d}/> : children}
  </svg>
);

const Icons = {
  Download: (p) => <Icon {...p}><path d="M12 4v12"/><path d="m7 11 5 5 5-5"/><path d="M5 20h14"/></Icon>,
  Play:     (p) => <Icon {...p} fill="currentColor" sw={0}><path d="M8 5v14l11-7z"/></Icon>,
  Pause:    (p) => <Icon {...p}><rect x="6" y="5" width="4" height="14" rx="1"/><rect x="14" y="5" width="4" height="14" rx="1"/></Icon>,
  X:        (p) => <Icon {...p}><path d="M6 6l12 12M18 6 6 18"/></Icon>,
  Check:    (p) => <Icon {...p}><path d="m5 12 5 5L20 7"/></Icon>,
  Plus:     (p) => <Icon {...p}><path d="M12 5v14M5 12h14"/></Icon>,
  Search:   (p) => <Icon {...p}><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></Icon>,
  Folder:   (p) => <Icon {...p}><path d="M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/></Icon>,
  Video:    (p) => <Icon {...p}><rect x="3" y="6" width="13" height="12" rx="2"/><path d="m22 8-6 4 6 4z"/></Icon>,
  Doc:      (p) => <Icon {...p}><path d="M7 3h7l5 5v13a1 1 0 0 1-1 1H7a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1z"/><path d="M14 3v5h5"/></Icon>,
  Music:    (p) => <Icon {...p}><path d="M9 18V5l12-2v13"/><circle cx="6" cy="18" r="3"/><circle cx="18" cy="16" r="3"/></Icon>,
  Image:    (p) => <Icon {...p}><rect x="3" y="4" width="18" height="16" rx="2"/><circle cx="9" cy="10" r="2"/><path d="m4 19 5-5 4 4 3-3 4 4"/></Icon>,
  Settings: (p) => <Icon {...p}><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.7 1.7 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-1.8-.3 1.7 1.7 0 0 0-1 1.5V21a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 0-1.1-1.5 1.7 1.7 0 0 0-1.8.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0 .3-1.8 1.7 1.7 0 0 0-1.5-1H3a2 2 0 1 1 0-4h.1a1.7 1.7 0 0 0 1.5-1.1 1.7 1.7 0 0 0-.3-1.8l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 1.8.3H9a1.7 1.7 0 0 0 1-1.5V3a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.8-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0-.3 1.8V9a1.7 1.7 0 0 0 1.5 1H21a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1.5 1z"/></Icon>,
  Sparkle:  (p) => <Icon {...p}><path d="M12 3v4M12 17v4M3 12h4M17 12h4M5.6 5.6l2.8 2.8M15.6 15.6l2.8 2.8M5.6 18.4l2.8-2.8M15.6 8.4l2.8-2.8"/></Icon>,
  Bolt:     (p) => <Icon {...p}><path d="M13 2 4 14h7l-1 8 9-12h-7z"/></Icon>,
  Pin:      (p) => <Icon {...p}><path d="M12 17v5M9 3h6l-1 7 4 3v2H6v-2l4-3z"/></Icon>,
  More:     (p) => <Icon {...p}><circle cx="5" cy="12" r="1.4"/><circle cx="12" cy="12" r="1.4"/><circle cx="19" cy="12" r="1.4"/></Icon>,
  Up:       (p) => <Icon {...p}><path d="M7 14l5-5 5 5"/></Icon>,
  Down:     (p) => <Icon {...p}><path d="M7 10l5 5 5-5"/></Icon>,
  Globe:    (p) => <Icon {...p}><circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3a14 14 0 0 1 0 18M12 3a14 14 0 0 0 0 18"/></Icon>,
  Link:     (p) => <Icon {...p}><path d="M10 14a5 5 0 0 0 7 0l3-3a5 5 0 0 0-7-7l-1 1"/><path d="M14 10a5 5 0 0 0-7 0l-3 3a5 5 0 0 0 7 7l1-1"/></Icon>,
  Stars:    (p) => <Icon {...p}><path d="M12 3v3M12 18v3M3 12h3M18 12h3"/><path d="M12 8l1.5 2.5L16 12l-2.5 1.5L12 16l-1.5-2.5L8 12l2.5-1.5z" fill="currentColor" stroke="none"/></Icon>,
  Wifi:     (p) => <Icon {...p}><path d="M2 9a16 16 0 0 1 20 0M5 13a11 11 0 0 1 14 0M8.5 16.5a6 6 0 0 1 7 0"/><circle cx="12" cy="20" r="1" fill="currentColor"/></Icon>,
};

// ── Circular ring progress (with optional inner content) ─────
function RingProgress({ size = 56, sw = 4, value = 0.5, track = 'rgba(255,255,255,0.08)', from = NX_COLORS.teal, to = NX_COLORS.violet, children, glow = true, id }) {
  const r = (size - sw) / 2;
  const c = 2 * Math.PI * r;
  const off = c * (1 - value);
  const uid = id || `r${Math.random().toString(36).slice(2, 7)}`;
  return (
    <div style={{ position: 'relative', width: size, height: size }}>
      <svg width={size} height={size} style={{ transform: 'rotate(-90deg)', filter: glow ? `drop-shadow(0 0 8px ${from})` : 'none' }}>
        <defs>
          <linearGradient id={uid} x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor={from} />
            <stop offset="100%" stopColor={to} />
          </linearGradient>
        </defs>
        <circle cx={size/2} cy={size/2} r={r} fill="none" stroke={track} strokeWidth={sw} />
        <circle cx={size/2} cy={size/2} r={r} fill="none" stroke={`url(#${uid})`} strokeWidth={sw}
                strokeDasharray={c} strokeDashoffset={off} strokeLinecap="round" />
      </svg>
      {children && (
        <div style={{ position: 'absolute', inset: 0, display: 'grid', placeItems: 'center' }}>
          {children}
        </div>
      )}
    </div>
  );
}

// ── Liquid fill bar — animated wave inside a pill ───────────
function LiquidBar({ value = 0.55, height = 14, from = NX_COLORS.teal, to = NX_COLORS.violet, track = 'rgba(255,255,255,0.06)' }) {
  return (
    <div style={{
      position: 'relative', width: '100%', height, background: track, borderRadius: 999, overflow: 'hidden',
      border: '1px solid rgba(255,255,255,0.05)'
    }}>
      <div style={{
        position: 'absolute', left: 0, top: 0, bottom: 0, width: `${value * 100}%`,
        background: `linear-gradient(90deg, ${from}, ${to})`,
        borderRadius: 999,
        overflow: 'hidden',
        boxShadow: `0 0 14px ${from}`,
        transition: 'width .4s ease',
      }}>
        <svg viewBox="0 0 200 30" preserveAspectRatio="none" style={{
          position: 'absolute', inset: 0, width: '200%', height: '100%',
          opacity: 0.45,
          animation: 'nx-wave 3.5s linear infinite',
        }}>
          <path d="M0 15 Q 25 5, 50 15 T 100 15 T 150 15 T 200 15 V30 H0 Z" fill="rgba(255,255,255,0.6)"/>
        </svg>
      </div>
    </div>
  );
}

// ── Spectrum bar (segmented LED-style) ──────────────────────
function SpectrumBar({ value = 0.6, segments = 28, height = 10, gap = 2 }) {
  const filled = Math.round(segments * value);
  return (
    <div style={{ display: 'flex', gap, alignItems: 'center', width: '100%', height }}>
      {Array.from({ length: segments }).map((_, i) => {
        const active = i < filled;
        const hue = 200 + (i / segments) * 95;
        return (
          <div key={i} style={{
            flex: 1, height: '100%',
            borderRadius: 2,
            background: active ? `oklch(0.78 0.16 ${hue})` : 'rgba(255,255,255,0.06)',
            boxShadow: active ? `0 0 6px oklch(0.78 0.16 ${hue} / 0.7)` : 'none',
          }}/>
        );
      })}
    </div>
  );
}

// ── Sparkline (for speed graph) ─────────────────────────────
function Sparkline({ data, width = 240, height = 48, stroke = NX_COLORS.teal, fill = true, glow = true }) {
  const max = Math.max(...data, 1);
  const step = width / (data.length - 1);
  const pts = data.map((v, i) => `${i * step},${height - (v / max) * (height - 6) - 3}`);
  const linePath = `M ${pts.join(' L ')}`;
  const fillPath = `${linePath} L ${width},${height} L 0,${height} Z`;
  const uid = `sp${Math.random().toString(36).slice(2, 7)}`;
  return (
    <svg width={width} height={height} style={{ display: 'block', filter: glow ? `drop-shadow(0 0 6px ${stroke})` : 'none' }}>
      <defs>
        <linearGradient id={uid} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={stroke} stopOpacity="0.4" />
          <stop offset="100%" stopColor={stroke} stopOpacity="0" />
        </linearGradient>
      </defs>
      {fill && <path d={fillPath} fill={`url(#${uid})`} />}
      <path d={linePath} fill="none" stroke={stroke} strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

// ── Placeholder thumbnail with subtle stripes + monospace label
function Thumb({ w = 96, h = 56, label = 'video', r = 10, tone = 'teal' }) {
  const palettes = {
    teal:   ['oklch(0.45 0.10 205)', 'oklch(0.30 0.08 220)'],
    violet: ['oklch(0.40 0.14 295)', 'oklch(0.28 0.10 300)'],
    coral:  ['oklch(0.55 0.14 30)',  'oklch(0.35 0.10 20)'],
    sand:   ['oklch(0.55 0.06 80)',  'oklch(0.40 0.05 70)'],
    sage:   ['oklch(0.50 0.08 150)', 'oklch(0.35 0.06 155)'],
    ink:    ['oklch(0.28 0.02 260)', 'oklch(0.18 0.02 260)'],
  };
  const [a, b] = palettes[tone] || palettes.teal;
  return (
    <div style={{
      width: w, height: h, borderRadius: r, position: 'relative', overflow: 'hidden',
      background: `linear-gradient(135deg, ${a}, ${b})`,
      border: '1px solid rgba(255,255,255,0.08)',
      flex: 'none',
    }}>
      <div style={{
        position: 'absolute', inset: 0,
        backgroundImage: 'repeating-linear-gradient(135deg, rgba(255,255,255,0.06) 0 2px, transparent 2px 14px)',
      }}/>
      <div style={{
        position: 'absolute', left: 6, bottom: 5,
        font: '500 8px/1 var(--mono, monospace)', color: 'rgba(255,255,255,0.7)',
        letterSpacing: '0.04em', textTransform: 'uppercase',
      }}>{label}</div>
    </div>
  );
}

// ── Mascot: "Tide" — a serene sleeping crescent character ───
function Mascot({ size = 200, mood = 'sleep' }) {
  // Sleeping: closed eye (curve), z's floating. Awake: eyes open + sparkle.
  const sleeping = mood === 'sleep';
  return (
    <svg width={size} height={size} viewBox="0 0 200 200" style={{ overflow: 'visible' }}>
      <defs>
        <radialGradient id="mg-body" cx="0.3" cy="0.3" r="0.9">
          <stop offset="0%" stopColor="oklch(0.85 0.10 205)"/>
          <stop offset="55%" stopColor="oklch(0.65 0.16 215)"/>
          <stop offset="100%" stopColor="oklch(0.40 0.18 270)"/>
        </radialGradient>
        <radialGradient id="mg-glow" cx="0.5" cy="0.5" r="0.5">
          <stop offset="0%" stopColor="oklch(0.75 0.20 210 / 0.5)"/>
          <stop offset="100%" stopColor="oklch(0.75 0.20 210 / 0)"/>
        </radialGradient>
      </defs>

      {/* Soft glow halo */}
      <circle cx="100" cy="105" r="92" fill="url(#mg-glow)"/>

      {/* Body — soft pebble shape */}
      <g style={{ transformOrigin: '100px 105px', animation: 'nx-float 4.5s ease-in-out infinite' }}>
        <path d="M 100 30 C 145 30 170 65 170 110 C 170 150 142 175 100 175 C 60 175 30 150 30 110 C 30 65 55 30 100 30 Z"
              fill="url(#mg-body)" />
        {/* Highlight */}
        <ellipse cx="78" cy="68" rx="22" ry="10" fill="rgba(255,255,255,0.16)" />

        {/* Eyes */}
        {sleeping ? (
          <>
            <path d="M 70 105 Q 80 112 90 105" stroke="rgba(255,255,255,0.85)" strokeWidth="3" fill="none" strokeLinecap="round"/>
            <path d="M 110 105 Q 120 112 130 105" stroke="rgba(255,255,255,0.85)" strokeWidth="3" fill="none" strokeLinecap="round"/>
          </>
        ) : (
          <>
            <circle cx="80" cy="105" r="4.5" fill="#fff"/>
            <circle cx="120" cy="105" r="4.5" fill="#fff"/>
          </>
        )}

        {/* Cheek blush */}
        <ellipse cx="68" cy="122" rx="9" ry="4" fill="oklch(0.75 0.16 25 / 0.6)"/>
        <ellipse cx="132" cy="122" rx="9" ry="4" fill="oklch(0.75 0.16 25 / 0.6)"/>

        {/* Smile */}
        <path d="M 92 138 Q 100 144 108 138" stroke="rgba(255,255,255,0.85)" strokeWidth="2.5" fill="none" strokeLinecap="round"/>
      </g>

      {/* Floating Z's when sleeping */}
      {sleeping && (
        <g style={{ fill: 'rgba(255,255,255,0.7)', fontFamily: 'var(--serif, serif)', fontStyle: 'italic' }}>
          <text x="155" y="55" fontSize="22" style={{ animation: 'nx-float 3.2s ease-in-out infinite' }}>z</text>
          <text x="170" y="38" fontSize="16" style={{ opacity: 0.7, animation: 'nx-float 3.2s ease-in-out infinite .4s' }}>z</text>
          <text x="180" y="22" fontSize="12" style={{ opacity: 0.4, animation: 'nx-float 3.2s ease-in-out infinite .8s' }}>z</text>
        </g>
      )}
    </svg>
  );
}

// ── Tiny mascot for chrome (16-32px logo) ──────────────────
function TideMark({ size = 24 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 32 32">
      <defs>
        <linearGradient id="tm" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="oklch(0.85 0.12 200)"/>
          <stop offset="100%" stopColor="oklch(0.50 0.22 290)"/>
        </linearGradient>
      </defs>
      <path d="M 16 3 C 23 3 28 8.5 28 16.5 C 28 24 23 29 16 29 C 9 29 4 24 4 16.5 C 4 8.5 9 3 16 3 Z" fill="url(#tm)"/>
      <path d="M 11 19 Q 14 22 17 19 Q 20 16 23 19" stroke="rgba(255,255,255,0.85)" strokeWidth="2" fill="none" strokeLinecap="round"/>
      <circle cx="12" cy="13" r="1.4" fill="#fff"/>
      <circle cx="20" cy="13" r="1.4" fill="#fff"/>
    </svg>
  );
}

// ── Traffic lights (macOS chrome) ────────────────────────
function TrafficLights() {
  return (
    <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
      <div style={{ width: 12, height: 12, borderRadius: '50%', background: '#ff5f57' }}/>
      <div style={{ width: 12, height: 12, borderRadius: '50%', background: '#febc2e' }}/>
      <div style={{ width: 12, height: 12, borderRadius: '50%', background: '#28c840' }}/>
    </div>
  );
}

// ── Tiny starfield (for empty state / dark moments) ─────
function Starfield({ count = 40, width = 600, height = 320 }) {
  const stars = React.useMemo(() =>
    Array.from({ length: count }).map(() => ({
      x: Math.random() * width,
      y: Math.random() * height,
      r: Math.random() * 1.4 + 0.3,
      d: Math.random() * 4,
    })), [count, width, height]);
  return (
    <svg width={width} height={height} style={{ position: 'absolute', inset: 0, pointerEvents: 'none' }}>
      {stars.map((s, i) => (
        <circle key={i} cx={s.x} cy={s.y} r={s.r} fill="white"
                style={{ animation: `nx-twinkle 3s ease-in-out ${s.d}s infinite` }}/>
      ))}
    </svg>
  );
}

Object.assign(window, {
  NX_COLORS, Icon, Icons,
  RingProgress, LiquidBar, SpectrumBar, Sparkline,
  Thumb, Mascot, TideMark, TrafficLights, Starfield,
});
