// Production Dashboard — receives real data via props, no mock constants.

const iconBtn = {
  width: 30, height: 30, borderRadius: 8, border: '1px solid var(--line-2)',
  background: 'rgba(255,255,255,0.03)', color: 'var(--ink-1)',
  display: 'grid', placeItems: 'center', cursor: 'pointer',
};

// ── Window chrome ─────────────────────────────────────────────
function ChromeBar({ totalSpeed = 0, activeCount = 0, onSettingsClick }) {
  const mbps = (totalSpeed / 1e6).toFixed(1);
  return (
    <div style={{
      height: 44, padding: '0 16px',
      display: 'flex', alignItems: 'center', gap: 16,
      borderBottom: `1px solid var(--line)`,
      position: 'relative', zIndex: 2, flex: 'none',
      WebkitAppRegion: 'drag',
    }}>
      <TrafficLights />
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginLeft: 6, WebkitAppRegion: 'no-drag' }}>
        <TideMark size={18}/>
        <span style={{ font: '500 13px var(--ui)', color: 'var(--ink-0)', letterSpacing: '-0.01em' }}>Nexload</span>
      </div>
      <div style={{ flex: 1 }}/>
      {activeCount > 0 && (
        <div style={{
          display: 'flex', alignItems: 'center', gap: 8, padding: '6px 10px', borderRadius: 999,
          background: 'rgba(255,255,255,0.04)', border: '1px solid var(--line-2)',
          font: '500 11px var(--mono)', color: 'var(--ink-1)',
          WebkitAppRegion: 'no-drag',
        }}>
          <span style={{ width: 6, height: 6, borderRadius: '50%', background: 'var(--good)', boxShadow: '0 0 6px var(--good)' }}/>
          {mbps} MB/s
          <span style={{ color: 'var(--ink-3)' }}>·</span>
          {activeCount} active
        </div>
      )}
      <button style={{ ...iconBtn, WebkitAppRegion: 'no-drag' }} onClick={onSettingsClick}>
        <Icons.Settings size={15}/>
      </button>
    </div>
  );
}

// ── Sidebar ───────────────────────────────────────────────────
function Sidebar({ active = 'active', onNavChange, downloads = [], completed = [], storageStats }) {
  const activeCount   = downloads.filter(d => d.status === 'active').length;
  const queuedCount   = downloads.filter(d => d.status === 'queued').length;
  const completedCount= completed.length;
  const counts = {
    active:  activeCount,
    queue:   queuedCount,
    done:    completedCount,
    video:   completed.filter(d => d.kind === 'video').length,
    music:   completed.filter(d => d.kind === 'music').length,
    docs:    completed.filter(d => d.kind === 'doc').length,
    images:  completed.filter(d => d.kind === 'image').length,
  };
  const items = [
    { id: 'active',    label: 'Active',    Icon: Icons.Bolt     },
    { id: 'queue',     label: 'Queued',    Icon: Icons.Down     },
    { id: 'done',      label: 'Completed', Icon: Icons.Check    },
    { id: 'video',     label: 'Video',     Icon: Icons.Video    },
    { id: 'music',     label: 'Music',     Icon: Icons.Music    },
    { id: 'docs',      label: 'Documents', Icon: Icons.Doc      },
    { id: 'images',    label: 'Images',    Icon: Icons.Image    },
    { id: 'settings',  label: 'Settings',  Icon: Icons.Settings },
  ];
  const usedPct = storageStats ? storageStats.usedPct : 0;
  const freeGb  = storageStats ? (storageStats.freeBytes / 1e9).toFixed(0) : '—';

  return (
    <div style={{
      width: 220, flex: 'none',
      borderRight: '1px solid var(--line)',
      padding: '20px 12px',
      display: 'flex', flexDirection: 'column', gap: 2,
      position: 'relative', zIndex: 1,
    }}>
      <div style={{ font: '500 10px var(--mono)', color: 'var(--ink-3)', letterSpacing: '0.14em', textTransform: 'uppercase', padding: '6px 10px 10px' }}>
        Library
      </div>
      {items.map((it) => {
        const sel = it.id === active;
        const c = counts[it.id] || 0;
        return (
          <div key={it.id} onClick={() => onNavChange(it.id)} style={{
            display: 'flex', alignItems: 'center', gap: 10,
            padding: '8px 10px', borderRadius: 10,
            background: sel ? 'linear-gradient(180deg, rgba(255,255,255,0.06), rgba(255,255,255,0.02))' : 'transparent',
            border: sel ? '1px solid var(--line-2)' : '1px solid transparent',
            color: sel ? 'var(--ink-0)' : 'var(--ink-1)',
            font: `${sel ? 500 : 400} 13px var(--ui)`,
            cursor: 'pointer', position: 'relative', userSelect: 'none',
          }}>
            {sel && <div style={{ position: 'absolute', left: -1, top: 8, bottom: 8, width: 2, borderRadius: 2, background: 'var(--teal)', boxShadow: '0 0 8px var(--teal)' }}/>}
            <it.Icon size={15} stroke={sel ? 'var(--teal)' : 'currentColor'} />
            <span style={{ flex: 1 }}>{it.label}</span>
            {c > 0 && <span style={{ font: '500 10px var(--mono)', color: 'var(--ink-3)' }}>{c}</span>}
          </div>
        );
      })}

      <div style={{ flex: 1 }}/>

      <div style={{ margin: '0 4px', padding: 12, borderRadius: 12, border: '1px solid var(--line-2)', background: 'rgba(255,255,255,0.03)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', font: '400 11px var(--mono)', color: 'var(--ink-2)' }}>
          <span>Storage</span>
          <span>{freeGb} GB free</span>
        </div>
        <div style={{ height: 6, marginTop: 8, borderRadius: 999, background: 'rgba(255,255,255,0.06)', overflow: 'hidden' }}>
          <div style={{ width: `${(usedPct * 100).toFixed(0)}%`, height: '100%', background: 'var(--teal)' }}/>
        </div>
        <div style={{ font: '400 10px var(--mono)', color: 'var(--ink-3)', marginTop: 6 }}>
          {(usedPct * 100).toFixed(0)}% used
        </div>
      </div>
    </div>
  );
}

// ── Now card (featured / first download) ─────────────────────
function NowCard({ item, onPause, onResume, onCancel }) {
  if (!item) return null;
  const value = item.value || 0;
  return (
    <div className="glass" style={{
      padding: 20, display: 'grid', gridTemplateColumns: 'auto 1fr auto', gap: 22,
      alignItems: 'center',
      background: 'linear-gradient(135deg, rgba(50,100,140,0.18), rgba(80,40,120,0.18))',
      position: 'relative', overflow: 'hidden',
    }}>
      <div style={{ position: 'relative', flex: 'none' }}>
        {item.thumbnailB64 ? (
          <img src={`data:image/jpeg;base64,${item.thumbnailB64}`}
               style={{ width: 140, height: 88, objectFit: 'cover', borderRadius: 14, border: '1px solid rgba(255,255,255,0.08)' }}/>
        ) : (
          <Thumb w={140} h={88} label={item.kind || 'file'} tone="teal" r={14}/>
        )}
        <div style={{ position: 'absolute', inset: 0, display: 'grid', placeItems: 'center' }}>
          <div style={{ width: 34, height: 34, borderRadius: '50%', background: 'rgba(0,0,0,0.55)', backdropFilter: 'blur(8px)', display: 'grid', placeItems: 'center', color: '#fff' }}>
            <Icons.Play size={14}/>
          </div>
        </div>
      </div>

      <div style={{ minWidth: 0 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
          <span style={{ font: '500 10px var(--mono)', color: 'var(--teal)', padding: '2px 8px', border: '1px solid var(--teal)', borderRadius: 999, textTransform: 'uppercase', letterSpacing: '0.08em' }}>
            Now
          </span>
          <span style={{ font: '400 11px var(--mono)', color: 'var(--ink-3)' }}>{item.host}</span>
        </div>
        <div style={{ font: '500 18px/1.3 var(--ui)', color: 'var(--ink-0)', letterSpacing: '-0.01em', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
          {item.title}
        </div>
        <div style={{ marginTop: 10 }}>
          <LiquidBar value={value} height={10}/>
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 8, font: '400 11px var(--mono)', color: 'var(--ink-2)' }}>
          <span>
            <span style={{ color: 'var(--ink-0)' }}>{fmtBytes(item.got || 0)}</span> of {fmtBytes(item.total || item.sizeBytes || 0)}
          </span>
          <span style={{ display: 'flex', gap: 12 }}>
            <span><Icons.Bolt size={11} stroke="var(--teal)" style={{ verticalAlign: '-2px', marginRight: 4 }}/>{fmtSpeed(item.speedBytes || 0)}</span>
            {item.eta && <span>{item.eta} left</span>}
          </span>
        </div>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 8, alignItems: 'center' }}>
        <RingProgress size={84} sw={6} value={value}>
          <div style={{ textAlign: 'center', font: '500 18px var(--ui)', color: 'var(--ink-0)' }}>
            {Math.round(value * 100)}<span style={{ font: '400 10px var(--mono)', color: 'var(--ink-3)', marginLeft: 1 }}>%</span>
          </div>
        </RingProgress>
        <div style={{ display: 'flex', gap: 6 }}>
          {item.status === 'active'
            ? <button style={{ ...iconBtn, width: 28, height: 28 }} onClick={() => onPause && onPause(item.id, item.aria2Gid)}><Icons.Pause size={12}/></button>
            : <button style={{ ...iconBtn, width: 28, height: 28 }} onClick={() => onResume && onResume(item.id, item.aria2Gid)}><Icons.Play size={12}/></button>
          }
          <button style={{ ...iconBtn, width: 28, height: 28 }} onClick={() => onCancel && onCancel(item.id, item.aria2Gid)}>
            <Icons.X size={12}/>
          </button>
        </div>
      </div>
    </div>
  );
}

// ── Download row ──────────────────────────────────────────────
function DownloadRow({ item, variant = 'liquid', onPause, onResume, onCancel, onReveal }) {
  const KindIcon = ({ video: Icons.Video, music: Icons.Music, doc: Icons.Doc, image: Icons.Image }[item.kind]) || Icons.Download;
  const value = item.value || 0;
  const isPaused = item.status === 'paused';
  const isCompleted = item.status === 'completed';
  const isFailed = item.status === 'failed';

  return (
    <div style={{
      display: 'grid', gridTemplateColumns: '72px 1fr 240px 110px 56px',
      gap: 16, alignItems: 'center', padding: '14px 18px',
      borderTop: '1px solid var(--line)',
    }}>
      {item.thumbnailB64 ? (
        <img src={`data:image/jpeg;base64,${item.thumbnailB64}`}
             style={{ width: 72, height: 44, objectFit: 'cover', borderRadius: 8, border: '1px solid rgba(255,255,255,0.08)' }}/>
      ) : (
        <Thumb w={72} h={44} label={item.kind || 'file'} tone="teal" r={8}/>
      )}

      <div style={{ minWidth: 0 }}>
        <div style={{ font: '500 13px var(--ui)', color: 'var(--ink-0)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
          {item.title}
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginTop: 3, font: '400 11px var(--mono)', color: 'var(--ink-3)' }}>
          <KindIcon size={11}/>
          <span>{item.host}</span>
          {item.sizeBytes > 0 && <><span>·</span><span>{fmtBytes(item.sizeBytes)}</span></>}
          {isFailed && <span style={{ color: 'var(--warn)' }}>· failed</span>}
        </div>
      </div>

      <div>
        {!isCompleted && !isFailed && (
          variant === 'spectrum'
            ? <SpectrumBar value={value} segments={24} height={8}/>
            : <LiquidBar value={value} height={8}/>
        )}
        {isCompleted && (
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, color: 'var(--good)', font: '400 11px var(--mono)' }}>
            <Icons.Check size={13} sw={2.5}/> Done
          </div>
        )}
        {!isCompleted && !isFailed && (
          <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 6, font: '400 10px var(--mono)', color: 'var(--ink-2)' }}>
            <span>{Math.round(value * 100)}%</span>
            <span>{fmtBytes(item.got || 0)}</span>
          </div>
        )}
      </div>

      <div style={{ font: '400 11px var(--mono)', color: 'var(--ink-1)' }}>
        {!isCompleted && !isFailed && (
          <>
            <div style={{ color: 'var(--ink-0)' }}>{fmtSpeed(item.speedBytes || 0)}</div>
            {item.eta && <div style={{ color: 'var(--ink-3)', marginTop: 2 }}>{item.eta}</div>}
          </>
        )}
        {isCompleted && item.completedAt && (
          <div style={{ color: 'var(--ink-3)', fontSize: 10 }}>{fmtRelTime(item.completedAt)}</div>
        )}
      </div>

      <div style={{ display: 'flex', gap: 6, justifyContent: 'flex-end' }}>
        {!isCompleted && !isFailed && (
          isPaused
            ? <button style={{ ...iconBtn, width: 26, height: 26 }} onClick={() => onResume && onResume(item.id, item.aria2Gid)}><Icons.Play size={11}/></button>
            : <button style={{ ...iconBtn, width: 26, height: 26 }} onClick={() => onPause && onPause(item.id, item.aria2Gid)}><Icons.Pause size={11}/></button>
        )}
        {isCompleted && (
          <button style={{ ...iconBtn, width: 26, height: 26 }} onClick={() => onReveal && onReveal(item.id)}>
            <Icons.Folder size={11}/>
          </button>
        )}
        {!isCompleted && (
          <button style={{ ...iconBtn, width: 26, height: 26 }} onClick={() => onCancel && onCancel(item.id, item.aria2Gid)}>
            <Icons.X size={11}/>
          </button>
        )}
      </div>
    </div>
  );
}

// ── Paste bar ─────────────────────────────────────────────────
function PasteBar({ url, onChange, onGrab }) {
  const [input, setInput] = React.useState(url || '');
  React.useEffect(() => { setInput(url || ''); }, [url]);

  const commit = () => { if (onGrab) onGrab(input); };
  const onKey  = (e) => { if (e.key === 'Enter') commit(); };

  return (
    <div className="glass" style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '10px 12px 10px 18px' }}>
      <Icons.Link size={15} stroke="var(--ink-2)"/>
      <input
        value={input}
        onChange={e => { setInput(e.target.value); if (onChange) onChange(e.target.value); }}
        onKeyDown={onKey}
        placeholder="paste a link, or drop one anywhere…"
        style={{
          flex: 1, background: 'transparent', border: 0, outline: 'none',
          font: '400 13px var(--mono)', color: 'var(--ink-1)',
          '::placeholder': { color: 'var(--ink-3)' },
        }}
      />
      <span style={{ font: '400 10px var(--mono)', color: 'var(--ink-3)', padding: '4px 7px', border: '1px solid var(--line-2)', borderRadius: 6 }}>⌘V</span>
      <button onClick={commit} style={{
        display: 'flex', alignItems: 'center', gap: 8,
        padding: '8px 14px', borderRadius: 10,
        background: 'linear-gradient(135deg, var(--teal), var(--violet))',
        color: '#0a0a0c', font: '600 12px var(--ui)', border: 0, cursor: 'pointer',
        boxShadow: '0 0 22px rgba(100,160,255,0.35)',
      }}>
        <Icons.Sparkle size={13} stroke="#0a0a0c"/> Grab it
      </button>
    </div>
  );
}

// ── Dashboard (dark) ──────────────────────────────────────────
function DashboardDark({
  downloads = [], nav = 'active', onNavChange,
  totalSpeed = 0, speedHistory = [],
  onGrab, pasteUrl, onPasteChange,
  onPause, onResume, onCancel, onReveal,
  completed = [], storageStats,
  onSettingsClick,
}) {
  const activeItems = downloads.filter(d => d.status === 'active' || d.status === 'queued' || d.status === 'paused');
  const nowItem = activeItems[0];
  const listItems = activeItems.slice(1);
  const mbps = (totalSpeed / 1e6).toFixed(1);
  const greetings = ['Good morning', 'Good afternoon', 'Good evening'];
  const hour = new Date().getHours();
  const greeting = hour < 12 ? greetings[0] : hour < 18 ? greetings[1] : greetings[2];

  return (
    <div className="nx-dark nx-grain" style={{
      width: '100%', height: '100%', background: 'var(--bg-0)',
      display: 'flex', flexDirection: 'column',
      position: 'relative', overflow: 'hidden', color: 'var(--ink-0)',
    }}>
      <div className="nx-aurora"/>
      <ChromeBar totalSpeed={totalSpeed} activeCount={activeItems.length} onSettingsClick={onSettingsClick}/>

      <div style={{ flex: 1, display: 'flex', minHeight: 0, position: 'relative', zIndex: 1 }}>
        <Sidebar active={nav} onNavChange={onNavChange} downloads={downloads} completed={completed} storageStats={storageStats}/>

        <div style={{ flex: 1, padding: '20px 24px', display: 'flex', flexDirection: 'column', gap: 16, minWidth: 0, overflow: 'hidden' }}>

          {/* Header */}
          <div style={{ display: 'flex', alignItems: 'flex-end', justifyContent: 'space-between' }}>
            <div>
              <div style={{ font: '400 11px var(--mono)', color: 'var(--ink-3)', letterSpacing: '0.16em', textTransform: 'uppercase' }}>
                Active · {activeItems.length} download{activeItems.length !== 1 ? 's' : ''}
              </div>
              <div style={{ font: '400 28px/1.05 var(--serif)', color: 'var(--ink-0)', letterSpacing: '-0.01em', marginTop: 4, whiteSpace: 'nowrap' }}>
                {greeting}, <em style={{ color: 'var(--teal)' }}>fetching</em> in flow.
              </div>
            </div>
            {speedHistory.length > 1 && (
              <div className="glass" style={{ padding: '10px 14px', display: 'flex', alignItems: 'center', gap: 18 }}>
                <div>
                  <div style={{ font: '400 10px var(--mono)', color: 'var(--ink-3)', textTransform: 'uppercase', letterSpacing: '0.1em' }}>Net</div>
                  <div style={{ font: '500 16px var(--ui)', color: 'var(--ink-0)' }}>{mbps} <span style={{ font: '400 11px var(--mono)', color: 'var(--ink-2)' }}>MB/s</span></div>
                </div>
                <div style={{ width: 1, alignSelf: 'stretch', background: 'var(--line)' }}/>
                <Sparkline data={speedHistory} width={180} height={42}/>
              </div>
            )}
          </div>

          {/* Now card */}
          {nowItem && (
            <NowCard item={nowItem} onPause={onPause} onResume={onResume} onCancel={onCancel}/>
          )}

          {/* Download list */}
          {listItems.length > 0 && (
            <div className="glass" style={{ overflow: 'hidden auto', padding: 0, flex: 1, display: 'flex', flexDirection: 'column' }}>
              <div style={{
                display: 'grid', gridTemplateColumns: '72px 1fr 240px 110px 56px',
                gap: 16, padding: '12px 18px',
                font: '500 10px var(--mono)', color: 'var(--ink-3)',
                textTransform: 'uppercase', letterSpacing: '0.14em',
              }}>
                <span/><span>File</span><span>Progress</span><span>Speed / ETA</span><span/>
              </div>
              {listItems.map((d, i) => (
                <DownloadRow key={d.id} item={d} variant={i % 2 ? 'spectrum' : 'liquid'}
                  onPause={onPause} onResume={onResume} onCancel={onCancel} onReveal={onReveal}/>
              ))}
            </div>
          )}

          <PasteBar url={pasteUrl} onChange={onPasteChange} onGrab={onGrab}/>
        </div>
      </div>
    </div>
  );
}

// ── Formatting helpers ────────────────────────────────────────
function fmtBytes(b) {
  if (b <= 0) return '—';
  if (b < 1e3) return b + ' B';
  if (b < 1e6) return (b/1e3).toFixed(1) + ' KB';
  if (b < 1e9) return (b/1e6).toFixed(1) + ' MB';
  return (b/1e9).toFixed(2) + ' GB';
}
function fmtSpeed(b) {
  if (b <= 0) return '—';
  return fmtBytes(b) + '/s';
}
function fmtRelTime(iso) {
  const d = new Date(iso);
  const now = Date.now();
  const diff = Math.floor((now - d.getTime()) / 1000);
  if (diff < 60)  return 'just now';
  if (diff < 3600) return Math.floor(diff/60) + 'm ago';
  if (diff < 86400) return Math.floor(diff/3600) + 'h ago';
  return d.toLocaleDateString();
}

Object.assign(window, { DashboardDark, ChromeBar, Sidebar, NowCard, DownloadRow, PasteBar, fmtBytes, fmtSpeed });
