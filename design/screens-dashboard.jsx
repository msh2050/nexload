// Main Dashboard — dark glass hero + light alt
// Reuses primitives from window scope.

const NX_DOWNLOADS = [
  { id: 'd1', kind: 'video', title: 'Aurora Borealis — 4K timelapse', host: 'youtube.com', size: '1.84 GB', got: '1.21 GB', speed: '12.4 MB/s', eta: '52s', value: 0.66, tone: 'teal' },
  { id: 'd2', kind: 'doc',   title: 'Q3 Pitch Deck — final v7.key',  host: 'dropbox.com', size: '284 MB', got: '198 MB', speed: '8.1 MB/s',  eta: '10s', value: 0.70, tone: 'sand' },
  { id: 'd3', kind: 'video', title: 'Lo-fi Sessions vol. 12',         host: 'vimeo.com',   size: '2.1 GB',  got: '410 MB', speed: '6.7 MB/s',  eta: '4m 12s', value: 0.20, tone: 'violet' },
  { id: 'd4', kind: 'music', title: 'Midnight Drive — full album',    host: 'bandcamp',    size: '78 MB',   got: '74 MB',  speed: '2.4 MB/s',  eta: '2s',  value: 0.95, tone: 'coral' },
  { id: 'd5', kind: 'image', title: 'Studio raw shoot · 248 files',   host: 'wetransfer',  size: '6.4 GB',  got: '512 MB', speed: '14.1 MB/s', eta: '7m 04s', value: 0.08, tone: 'sage' },
];

const NX_SPEED_DATA = [12,18,22,19,26,30,28,34,31,38,42,45,40,48,52,49,55,58,53,60,58,62,67,64,69,72,68,74,71,78];

// ── Window chrome bar ───────────────────────────────────────
function ChromeBar({ light = false }) {
  return (
    <div style={{
      height: 44, padding: '0 16px',
      display: 'flex', alignItems: 'center', gap: 16,
      borderBottom: `1px solid var(--line)`,
      position: 'relative', zIndex: 2,
      flex: 'none',
    }}>
      <TrafficLights />
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginLeft: 6 }}>
        <TideMark size={18}/>
        <span style={{ font: '500 13px var(--ui)', color: 'var(--ink-0)', letterSpacing: '-0.01em' }}>Nexload</span>
        <span style={{ font: '400 11px var(--mono)', color: 'var(--ink-3)', marginLeft: 4 }}>v3.1</span>
      </div>
      <div style={{ flex: 1 }}/>
      <div style={{
        display: 'flex', alignItems: 'center', gap: 8,
        padding: '6px 10px', borderRadius: 999,
        background: 'rgba(255,255,255,0.04)', border: '1px solid var(--line-2)',
        font: '500 11px var(--mono)', color: 'var(--ink-1)',
      }}>
        <span style={{ width: 6, height: 6, borderRadius: '50%', background: 'var(--good)', boxShadow: '0 0 6px var(--good)' }}/>
        43.7 MB/s
        <span style={{ color: 'var(--ink-3)' }}>·</span>
        5 active
      </div>
      <button style={iconBtn}><Icons.Search size={15}/></button>
      <button style={iconBtn}><Icons.Settings size={15}/></button>
    </div>
  );
}

const iconBtn = {
  width: 30, height: 30, borderRadius: 8, border: '1px solid var(--line-2)',
  background: 'rgba(255,255,255,0.03)', color: 'var(--ink-1)',
  display: 'grid', placeItems: 'center', cursor: 'pointer',
};

// ── Sidebar nav ─────────────────────────────────────────────
function Sidebar({ active = 'active' }) {
  const items = [
    { id: 'active',    label: 'Active',    Icon: Icons.Bolt,     count: 5 },
    { id: 'queue',     label: 'Queued',    Icon: Icons.Down,     count: 12 },
    { id: 'done',      label: 'Completed', Icon: Icons.Check,    count: 184 },
    { id: 'video',     label: 'Video',     Icon: Icons.Video,    count: 47 },
    { id: 'music',     label: 'Music',     Icon: Icons.Music,    count: 92 },
    { id: 'docs',      label: 'Documents', Icon: Icons.Doc,      count: 31 },
    { id: 'images',    label: 'Images',    Icon: Icons.Image,    count: 308 },
  ];
  return (
    <div style={{
      width: 220, flex: 'none',
      borderRight: '1px solid var(--line)',
      padding: '20px 12px',
      display: 'flex', flexDirection: 'column', gap: 2,
      position: 'relative', zIndex: 1,
    }}>
      <div style={{
        font: '500 10px var(--mono)', color: 'var(--ink-3)',
        letterSpacing: '0.14em', textTransform: 'uppercase',
        padding: '6px 10px 10px',
      }}>Library</div>
      {items.map((it) => {
        const sel = it.id === active;
        return (
          <div key={it.id} style={{
            display: 'flex', alignItems: 'center', gap: 10,
            padding: '8px 10px', borderRadius: 10,
            background: sel ? 'linear-gradient(180deg, rgba(255,255,255,0.06), rgba(255,255,255,0.02))' : 'transparent',
            border: sel ? '1px solid var(--line-2)' : '1px solid transparent',
            color: sel ? 'var(--ink-0)' : 'var(--ink-1)',
            font: `${sel ? 500 : 400} 13px var(--ui)`,
            cursor: 'pointer',
            position: 'relative',
          }}>
            {sel && <div style={{ position: 'absolute', left: -1, top: 8, bottom: 8, width: 2, borderRadius: 2, background: 'var(--teal)', boxShadow: '0 0 8px var(--teal)' }}/>}
            <it.Icon size={15} stroke={sel ? 'var(--teal)' : 'currentColor'} />
            <span style={{ flex: 1 }}>{it.label}</span>
            <span style={{ font: '500 10px var(--mono)', color: 'var(--ink-3)' }}>{it.count}</span>
          </div>
        );
      })}

      <div style={{
        font: '500 10px var(--mono)', color: 'var(--ink-3)',
        letterSpacing: '0.14em', textTransform: 'uppercase',
        padding: '20px 10px 10px',
      }}>Tags</div>
      {['Work', 'Inspiration', 'Tutorials'].map((t, i) => (
        <div key={t} style={{
          display: 'flex', alignItems: 'center', gap: 10,
          padding: '7px 10px', borderRadius: 10,
          color: 'var(--ink-1)', font: '400 13px var(--ui)',
        }}>
          <span style={{
            width: 8, height: 8, borderRadius: 2,
            background: ['var(--teal)','var(--violet)','var(--warn)'][i],
            boxShadow: `0 0 5px ${['var(--teal)','var(--violet)','var(--warn)'][i]}`,
          }}/>
          {t}
        </div>
      ))}

      <div style={{ flex: 1 }}/>

      {/* Storage cell */}
      <div style={{
        margin: '0 4px', padding: 12,
        borderRadius: 12, border: '1px solid var(--line-2)',
        background: 'rgba(255,255,255,0.03)',
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', font: '400 11px var(--mono)', color: 'var(--ink-2)' }}>
          <span>Storage</span>
          <span>418 GB</span>
        </div>
        <div style={{ height: 6, marginTop: 8, borderRadius: 999, background: 'rgba(255,255,255,0.06)', overflow: 'hidden', display: 'flex' }}>
          <div style={{ width: '38%', background: 'var(--teal)' }}/>
          <div style={{ width: '22%', background: 'var(--violet)' }}/>
          <div style={{ width: '14%', background: 'var(--warn)' }}/>
        </div>
        <div style={{ font: '400 10px var(--mono)', color: 'var(--ink-3)', marginTop: 6 }}>
          74% of 1 TB used
        </div>
      </div>
    </div>
  );
}

// ── Hero "Now" card — circular ring + featured download ─────
function NowCard({ item = NX_DOWNLOADS[0] }) {
  return (
    <div className="glass" style={{
      padding: 20,
      display: 'grid', gridTemplateColumns: 'auto 1fr auto', gap: 22,
      alignItems: 'center',
      background: 'linear-gradient(135deg, rgba(50,100,140,0.18), rgba(80,40,120,0.18))',
      position: 'relative', overflow: 'hidden',
    }}>
      {/* Big thumb */}
      <div style={{ position: 'relative', flex: 'none' }}>
        <Thumb w={140} h={88} label="4K · 60FPS" tone="teal" r={14}/>
        <div style={{
          position: 'absolute', inset: 0, display: 'grid', placeItems: 'center',
        }}>
          <div style={{
            width: 34, height: 34, borderRadius: '50%',
            background: 'rgba(0,0,0,0.55)', backdropFilter: 'blur(8px)',
            display: 'grid', placeItems: 'center', color: '#fff',
          }}>
            <Icons.Play size={14}/>
          </div>
        </div>
      </div>

      <div style={{ minWidth: 0 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
          <span style={{
            font: '500 10px var(--mono)', color: 'var(--teal)',
            padding: '2px 8px', border: '1px solid var(--teal)',
            borderRadius: 999, textTransform: 'uppercase', letterSpacing: '0.08em',
          }}>Now</span>
          <span style={{ font: '400 11px var(--mono)', color: 'var(--ink-3)' }}>{item.host}</span>
        </div>
        <div style={{ font: '500 18px/1.3 var(--ui)', color: 'var(--ink-0)', letterSpacing: '-0.01em',
                      whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
          {item.title}
        </div>
        <div style={{ marginTop: 10 }}>
          <LiquidBar value={item.value} height={10}/>
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 8,
                      font: '400 11px var(--mono)', color: 'var(--ink-2)' }}>
          <span><span style={{ color: 'var(--ink-0)' }}>{item.got}</span> of {item.size}</span>
          <span style={{ display: 'flex', gap: 12 }}>
            <span><Icons.Bolt size={11} stroke="var(--teal)" style={{ verticalAlign: '-2px', marginRight: 4 }}/>{item.speed}</span>
            <span>{item.eta} left</span>
          </span>
        </div>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 8, alignItems: 'center' }}>
        <RingProgress size={84} sw={6} value={item.value}>
          <div style={{ textAlign: 'center', font: '500 18px var(--ui)', color: 'var(--ink-0)' }}>
            {Math.round(item.value * 100)}
            <span style={{ font: '400 10px var(--mono)', color: 'var(--ink-3)', marginLeft: 1 }}>%</span>
          </div>
        </RingProgress>
        <div style={{ display: 'flex', gap: 6 }}>
          <button style={{ ...iconBtn, width: 28, height: 28 }}><Icons.Pause size={12}/></button>
          <button style={{ ...iconBtn, width: 28, height: 28 }}><Icons.X size={12}/></button>
        </div>
      </div>
    </div>
  );
}

// ── Row: a single download item ─────────────────────────────
function DownloadRow({ item, variant = 'liquid' }) {
  const KindIcon = {
    video: Icons.Video, music: Icons.Music, doc: Icons.Doc, image: Icons.Image,
  }[item.kind];

  return (
    <div style={{
      display: 'grid',
      gridTemplateColumns: '72px 1fr 240px 110px 56px',
      gap: 16, alignItems: 'center',
      padding: '14px 18px',
      borderTop: '1px solid var(--line)',
    }}>
      <Thumb w={72} h={44} label={item.kind} tone={item.tone} r={8}/>

      <div style={{ minWidth: 0 }}>
        <div style={{ font: '500 13px var(--ui)', color: 'var(--ink-0)',
                      whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
          {item.title}
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginTop: 3,
                      font: '400 11px var(--mono)', color: 'var(--ink-3)' }}>
          <KindIcon size={11}/>
          <span>{item.host}</span>
          <span>·</span>
          <span>{item.size}</span>
        </div>
      </div>

      <div>
        {variant === 'liquid' && <LiquidBar value={item.value} height={8}/>}
        {variant === 'spectrum' && <SpectrumBar value={item.value} segments={24} height={8}/>}
        <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 6,
                      font: '400 10px var(--mono)', color: 'var(--ink-2)' }}>
          <span>{Math.round(item.value * 100)}%</span>
          <span>{item.got}</span>
        </div>
      </div>

      <div style={{ font: '400 11px var(--mono)', color: 'var(--ink-1)' }}>
        <div style={{ color: 'var(--ink-0)' }}>{item.speed}</div>
        <div style={{ color: 'var(--ink-3)', marginTop: 2 }}>{item.eta}</div>
      </div>

      <div style={{ display: 'flex', gap: 6, justifyContent: 'flex-end' }}>
        <button style={{ ...iconBtn, width: 26, height: 26 }}><Icons.Pause size={11}/></button>
        <button style={{ ...iconBtn, width: 26, height: 26 }}><Icons.More size={11}/></button>
      </div>
    </div>
  );
}

// ── Paste bar (bottom) ──────────────────────────────────────
function PasteBar() {
  return (
    <div className="glass" style={{
      display: 'flex', alignItems: 'center', gap: 12,
      padding: '10px 12px 10px 18px',
    }}>
      <Icons.Link size={15} stroke="var(--ink-2)"/>
      <span style={{
        flex: 1, font: '400 13px var(--mono)', color: 'var(--ink-3)',
        whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis',
      }}>https://&zwj;<span style={{ color: 'var(--ink-1)' }}>paste a link, or drop one anywhere…</span></span>
      <span style={{
        font: '400 10px var(--mono)', color: 'var(--ink-3)',
        padding: '4px 7px', border: '1px solid var(--line-2)', borderRadius: 6,
      }}>⌘V</span>
      <button style={{
        display: 'flex', alignItems: 'center', gap: 8,
        padding: '8px 14px', borderRadius: 10,
        background: 'linear-gradient(135deg, var(--teal), var(--violet))',
        color: '#0a0a0c', font: '600 12px var(--ui)', border: 0, cursor: 'pointer',
        boxShadow: '0 0 22px oklch(0.70 0.18 250 / 0.45)',
      }}>
        <Icons.Sparkle size={13} stroke="#0a0a0c"/> Grab it
      </button>
    </div>
  );
}

// ── DASHBOARD — DARK ───────────────────────────────────────
function DashboardDark() {
  return (
    <div className="nx-dark nx-grain" style={{
      width: '100%', height: '100%', background: 'var(--bg-0)',
      display: 'flex', flexDirection: 'column',
      position: 'relative', overflow: 'hidden',
      color: 'var(--ink-0)',
    }}>
      <div className="nx-aurora"/>
      <ChromeBar/>
      <div style={{ flex: 1, display: 'flex', minHeight: 0, position: 'relative', zIndex: 1 }}>
        <Sidebar active="active"/>

        <div style={{ flex: 1, padding: '20px 24px', display: 'flex', flexDirection: 'column', gap: 16, minWidth: 0, overflow: 'hidden' }}>

          {/* Header row */}
          <div style={{ display: 'flex', alignItems: 'flex-end', justifyContent: 'space-between' }}>
            <div>
              <div style={{ font: '400 11px var(--mono)', color: 'var(--ink-3)', letterSpacing: '0.16em', textTransform: 'uppercase' }}>
                Active · 5 downloads
              </div>
              <div style={{ font: '400 28px/1.05 var(--serif)', color: 'var(--ink-0)', letterSpacing: '-0.01em', marginTop: 4, whiteSpace: 'nowrap' }}>
                Good evening, <em style={{ color: 'var(--teal)' }}>fetching</em> in flow.
              </div>
            </div>
            <div className="glass" style={{ padding: '10px 14px', display: 'flex', alignItems: 'center', gap: 18 }}>
              <div>
                <div style={{ font: '400 10px var(--mono)', color: 'var(--ink-3)', textTransform: 'uppercase', letterSpacing: '0.1em' }}>Net</div>
                <div style={{ font: '500 16px var(--ui)', color: 'var(--ink-0)' }}>43.7 <span style={{ font: '400 11px var(--mono)', color: 'var(--ink-2)' }}>MB/s</span></div>
              </div>
              <div style={{ width: 1, alignSelf: 'stretch', background: 'var(--line)' }}/>
              <Sparkline data={NX_SPEED_DATA} width={180} height={42}/>
            </div>
          </div>

          {/* Hero NOW card */}
          <NowCard/>

          {/* List */}
          <div className="glass" style={{ overflow: 'hidden', padding: 0, flex: 1, display: 'flex', flexDirection: 'column' }}>
            <div style={{
              display: 'grid', gridTemplateColumns: '72px 1fr 240px 110px 56px',
              gap: 16, padding: '12px 18px',
              font: '500 10px var(--mono)', color: 'var(--ink-3)',
              textTransform: 'uppercase', letterSpacing: '0.14em',
            }}>
              <span/>
              <span>File</span>
              <span>Progress</span>
              <span>Speed / ETA</span>
              <span/>
            </div>
            {NX_DOWNLOADS.slice(1).map((d, i) => (
              <DownloadRow key={d.id} item={d} variant={i % 2 ? 'spectrum' : 'liquid'}/>
            ))}
          </div>

          <PasteBar/>
        </div>
      </div>
    </div>
  );
}

// ── DASHBOARD — LIGHT ──────────────────────────────────────
function DashboardLight() {
  return (
    <div className="nx-light nx-grain" style={{
      width: '100%', height: '100%', background: 'var(--bg-0)',
      display: 'flex', flexDirection: 'column',
      position: 'relative', overflow: 'hidden',
      color: 'var(--ink-0)',
    }}>
      <div className="nx-aurora"/>
      <ChromeBar light/>
      <div style={{ flex: 1, display: 'flex', minHeight: 0, position: 'relative', zIndex: 1 }}>
        <Sidebar active="active"/>

        <div style={{ flex: 1, padding: '20px 24px', display: 'flex', flexDirection: 'column', gap: 16, minWidth: 0, overflow: 'hidden' }}>
          <div style={{ display: 'flex', alignItems: 'flex-end', justifyContent: 'space-between' }}>
            <div>
              <div style={{ font: '400 11px var(--mono)', color: 'var(--ink-2)', letterSpacing: '0.16em', textTransform: 'uppercase' }}>
                Active · 5 downloads
              </div>
              <div style={{ font: '400 28px/1.05 var(--serif)', color: 'var(--ink-0)', letterSpacing: '-0.01em', marginTop: 4, whiteSpace: 'nowrap' }}>
                A calm afternoon, <em style={{ color: 'var(--violet)' }}>quietly</em> fetching.
              </div>
            </div>
            <div className="glass" style={{ padding: '10px 14px', display: 'flex', alignItems: 'center', gap: 18, background: 'var(--glass-strong)' }}>
              <div>
                <div style={{ font: '400 10px var(--mono)', color: 'var(--ink-2)', textTransform: 'uppercase', letterSpacing: '0.1em' }}>Net</div>
                <div style={{ font: '500 16px var(--ui)' }}>43.7 <span style={{ font: '400 11px var(--mono)', color: 'var(--ink-2)' }}>MB/s</span></div>
              </div>
              <div style={{ width: 1, alignSelf: 'stretch', background: 'var(--line)' }}/>
              <Sparkline data={NX_SPEED_DATA} width={180} height={42} stroke="oklch(0.50 0.18 290)" glow={false}/>
            </div>
          </div>

          <NowCard/>

          <div className="glass" style={{ overflow: 'hidden', padding: 0, flex: 1, display: 'flex', flexDirection: 'column', background: 'var(--glass-strong)' }}>
            <div style={{
              display: 'grid', gridTemplateColumns: '72px 1fr 240px 110px 56px',
              gap: 16, padding: '12px 18px',
              font: '500 10px var(--mono)', color: 'var(--ink-2)',
              textTransform: 'uppercase', letterSpacing: '0.14em',
            }}>
              <span/>
              <span>File</span>
              <span>Progress</span>
              <span>Speed / ETA</span>
              <span/>
            </div>
            {NX_DOWNLOADS.slice(1).map((d, i) => (
              <DownloadRow key={d.id} item={d} variant={i % 2 ? 'spectrum' : 'liquid'}/>
            ))}
          </div>

          <PasteBar/>
        </div>
      </div>
    </div>
  );
}

Object.assign(window, { DashboardDark, DashboardLight, NX_DOWNLOADS, NX_SPEED_DATA, ChromeBar, Sidebar, NowCard, DownloadRow, PasteBar });
