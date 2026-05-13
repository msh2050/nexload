// State screens: empty state, completed library, settings panel.
// All accept real data via props.

// ── EMPTY STATE ───────────────────────────────────────────────
function EmptyState({ onGrab, pasteUrl, onPasteChange }) {
  const [input, setInput] = React.useState(pasteUrl || '');
  React.useEffect(() => { setInput(pasteUrl || ''); }, [pasteUrl]);
  const commit = () => { if (onGrab && input) onGrab(input); };
  const onKey  = (e) => { if (e.key === 'Enter') commit(); };

  return (
    <div className="nx-dark" style={{
      width: '100%', height: '100%', position: 'relative', overflow: 'hidden',
      background: 'linear-gradient(180deg, #1a1540 0%, #0a0a14 60%, #0f1a2a 100%)',
      display: 'flex', flexDirection: 'column', color: 'var(--ink-0)',
    }}>
      <ChromeBar/>
      <Starfield count={70} width={1280} height={760}/>

      {/* Mountains */}
      <svg width="100%" height="220" viewBox="0 0 1280 220" preserveAspectRatio="none"
           style={{ position: 'absolute', left: 0, right: 0, bottom: 80, opacity: 0.7 }}>
        <defs>
          <linearGradient id="mtn" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#1e2545"/><stop offset="100%" stopColor="#0a0c1e"/>
          </linearGradient>
        </defs>
        <path d="M0 200 L0 130 L120 80 L240 140 L360 70 L480 130 L600 90 L720 150 L840 80 L960 140 L1080 100 L1200 160 L1280 110 L1280 200 Z" fill="url(#mtn)"/>
      </svg>
      <svg width="100%" height="180" viewBox="0 0 1280 180" preserveAspectRatio="none"
           style={{ position: 'absolute', left: 0, right: 0, bottom: 0 }}>
        <defs>
          <linearGradient id="mtn2" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#111828"/><stop offset="100%" stopColor="#050810"/>
          </linearGradient>
        </defs>
        <path d="M0 170 L0 100 L80 50 L200 110 L320 40 L480 90 L640 30 L800 100 L960 50 L1100 110 L1280 60 L1280 170 Z" fill="url(#mtn2)"/>
      </svg>

      <div style={{ position: 'absolute', bottom: 60, left: 0, right: 0, height: 120,
        background: 'radial-gradient(ellipse at 50% 100%, rgba(0,170,160,0.25), transparent 70%)',
        filter: 'blur(20px)', pointerEvents: 'none' }}/>

      <div style={{ flex: 1, display: 'grid', placeItems: 'center', position: 'relative', zIndex: 2 }}>
        <div style={{ textAlign: 'center' }}>
          <Mascot size={220} mood="sleep"/>
          <div style={{ font: '400 38px/1.1 var(--serif)', color: 'var(--ink-0)', marginTop: 8, letterSpacing: '-0.01em' }}>
            <em style={{ color: 'var(--teal)' }}>Tide</em> is resting.
          </div>
          <div style={{ font: '400 14px var(--ui)', color: 'var(--ink-2)', marginTop: 8, maxWidth: 380, marginInline: 'auto' }}>
            No active downloads. Drop a link anywhere on screen, paste it, or wake Tide up.
          </div>

          <div style={{
            display: 'inline-flex', alignItems: 'center', gap: 10, marginTop: 24,
            padding: '12px 14px 12px 16px', borderRadius: 14,
            background: 'rgba(255,255,255,0.05)', backdropFilter: 'blur(28px)',
            border: '1px solid rgba(255,255,255,0.12)',
          }}>
            <Icons.Link size={14} stroke="var(--ink-2)"/>
            <input
              value={input}
              onChange={e => { setInput(e.target.value); if (onPasteChange) onPasteChange(e.target.value); }}
              onKeyDown={onKey}
              placeholder="paste a link here…"
              style={{ background: 'transparent', border: 0, outline: 'none', font: '400 13px var(--mono)', color: 'var(--ink-2)', width: 240 }}
            />
            <span style={{ font: '400 10px var(--mono)', color: 'var(--ink-2)', padding: '3px 7px', border: '1px solid rgba(255,255,255,0.12)', borderRadius: 6 }}>⌘V</span>
            <button onClick={commit} style={{
              padding: '8px 16px', marginLeft: 6, borderRadius: 10,
              background: 'linear-gradient(135deg, var(--teal), var(--violet))',
              color: '#0a0a0c', font: '600 12px var(--ui)', border: 0, cursor: 'pointer',
              boxShadow: '0 0 18px rgba(0,170,200,0.35)',
            }}>Wake Tide</button>
          </div>
        </div>
      </div>
    </div>
  );
}

// ── COMPLETED LIBRARY ─────────────────────────────────────────
function CompletedLibrary({ items = [], onNavChange }) {
  const [filter, setFilter] = React.useState('All');
  const filters = ['All', 'Video', 'Music', 'Docs', 'Images'];
  const kindMap = { Video: 'video', Music: 'music', Docs: 'doc', Images: 'image' };

  const visible = filter === 'All'
    ? items
    : items.filter(it => it.kind === (kindMap[filter] || filter.toLowerCase()));

  const totalGb = (items.reduce((s, i) => s + (i.sizeBytes || 0), 0) / 1e9).toFixed(1);

  return (
    <div className="nx-dark nx-grain" style={{
      width: '100%', height: '100%', background: 'var(--bg-0)',
      display: 'flex', flexDirection: 'column', overflow: 'hidden',
      position: 'relative', color: 'var(--ink-0)',
    }}>
      <div className="nx-aurora"/>
      <ChromeBar/>
      <div style={{ flex: 1, display: 'flex', minHeight: 0, position: 'relative', zIndex: 1 }}>
        <Sidebar active="done" onNavChange={onNavChange} completed={items}/>
        <div style={{ flex: 1, padding: '20px 24px', display: 'flex', flexDirection: 'column', gap: 16, overflow: 'hidden' }}>
          <div style={{ display: 'flex', alignItems: 'flex-end', justifyContent: 'space-between' }}>
            <div>
              <div style={{ font: '400 11px var(--mono)', color: 'var(--ink-3)', letterSpacing: '0.16em', textTransform: 'uppercase' }}>
                Completed · {items.length} items · {totalGb} GB
              </div>
              <div style={{ font: '400 28px/1.05 var(--serif)', color: 'var(--ink-0)', letterSpacing: '-0.01em', marginTop: 4 }}>
                Your <em style={{ color: 'var(--teal)' }}>catch</em> this week.
              </div>
            </div>
            <div style={{ display: 'flex', gap: 8 }}>
              {filters.map((t, i) => (
                <div key={t} onClick={() => setFilter(t)} style={{
                  padding: '6px 12px', borderRadius: 999, cursor: 'pointer',
                  background: filter === t ? 'rgba(255,255,255,0.08)' : 'transparent',
                  border: `1px solid ${filter === t ? 'var(--line-2)' : 'var(--line)'}`,
                  font: `${filter === t ? 500 : 400} 12px var(--ui)`,
                  color: filter === t ? 'var(--ink-0)' : 'var(--ink-2)', userSelect: 'none',
                }}>{t}</div>
              ))}
            </div>
          </div>

          {visible.length === 0 ? (
            <div style={{ flex: 1, display: 'grid', placeItems: 'center' }}>
              <div style={{ textAlign: 'center', color: 'var(--ink-3)' }}>
                <Icons.Folder size={40} stroke="var(--ink-3)"/>
                <div style={{ marginTop: 12, font: '400 15px var(--ui)' }}>No completed downloads yet.</div>
              </div>
            </div>
          ) : (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: 14, overflow: 'auto', flex: 1, paddingBottom: 8 }}>
              {visible.map((it) => {
                const KindIcon = ({ video: Icons.Video, doc: Icons.Doc, music: Icons.Music, image: Icons.Image }[it.kind]) || Icons.Download;
                const tone = ({ video: 'teal', doc: 'sand', music: 'coral', image: 'sage' }[it.kind]) || 'ink';
                return (
                  <div key={it.id} className="glass" style={{ padding: 12, display: 'flex', flexDirection: 'column', gap: 10 }}>
                    <div style={{ position: 'relative' }}>
                      {it.thumbnailB64 ? (
                        <img src={`data:image/jpeg;base64,${it.thumbnailB64}`}
                             style={{ width: '100%', height: 120, objectFit: 'cover', borderRadius: 10 }}/>
                      ) : (
                        <Thumb w="100%" h={120} label={it.kind} tone={tone} r={10}/>
                      )}
                      <div style={{
                        position: 'absolute', right: 8, top: 8,
                        width: 24, height: 24, borderRadius: 8,
                        background: 'rgba(0,0,0,0.4)', backdropFilter: 'blur(8px)',
                        display: 'grid', placeItems: 'center', color: 'var(--good)',
                        border: '1px solid rgba(255,255,255,0.12)',
                      }}>
                        <Icons.Check size={11} sw={2.5}/>
                      </div>
                    </div>
                    <div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 2 }}>
                        <KindIcon size={10} stroke="var(--ink-2)"/>
                        <span style={{ font: '400 10px var(--mono)', color: 'var(--ink-3)' }}>{it.kind}</span>
                      </div>
                      <div style={{ font: '500 13px/1.3 var(--ui)', color: 'var(--ink-0)', display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
                        {it.title}
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 6, font: '400 10px var(--mono)', color: 'var(--ink-3)' }}>
                        <span>{it.sizeBytes > 0 ? fmtBytes(it.sizeBytes) : '—'}</span>
                        <span>{it.completedAt ? fmtRelTime(it.completedAt) : ''}</span>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// ── SETTINGS PANEL ────────────────────────────────────────────
function SettingsPanel({ settings, onSave, onNavChange }) {
  const [local, setLocal] = React.useState(settings || {
    downloadDir: '~/Downloads', concurrentDownloads: 5, connectionsPerFile: 8,
    maxSpeedKbps: 0, autoDetectVideos: true, pauseOnMetered: true,
    resumeOnLaunch: false, verifyChecksums: true,
  });
  React.useEffect(() => { if (settings) setLocal(settings); }, [settings]);

  const set = (key, val) => setLocal(prev => ({ ...prev, [key]: val }));
  const save = () => onSave && onSave(local);

  const subnavItems = [
    ['General',    Icons.Settings, false],
    ['Connection', Icons.Wifi,     true],
    ['Library',    Icons.Folder,   false],
    ['Appearance', Icons.Sparkle,  false],
  ];

  const concurrencyOpts = [1,2,3,4,5,6,8,'∞'];
  const connOpts = ['1','2','4','8','16','32'];

  return (
    <div className="nx-dark nx-grain" style={{
      width: '100%', height: '100%', background: 'var(--bg-0)',
      display: 'flex', flexDirection: 'column', overflow: 'hidden',
      position: 'relative', color: 'var(--ink-0)',
    }}>
      <div className="nx-aurora"/>
      <ChromeBar onSettingsClick={() => onNavChange && onNavChange('active')}/>
      <div style={{ flex: 1, display: 'flex', minHeight: 0, position: 'relative', zIndex: 1 }}>
        <div style={{ width: 200, flex: 'none', borderRight: '1px solid var(--line)', padding: '20px 12px', display: 'flex', flexDirection: 'column', gap: 2 }}>
          <div style={{ font: '500 10px var(--mono)', color: 'var(--ink-3)', letterSpacing: '0.14em', textTransform: 'uppercase', padding: '6px 10px 10px' }}>Settings</div>
          {subnavItems.map(([label, IconC, sel]) => (
            <div key={label} style={{
              display: 'flex', alignItems: 'center', gap: 10,
              padding: '8px 10px', borderRadius: 10,
              background: sel ? 'linear-gradient(180deg, rgba(255,255,255,0.06), rgba(255,255,255,0.02))' : 'transparent',
              border: sel ? '1px solid var(--line-2)' : '1px solid transparent',
              color: sel ? 'var(--ink-0)' : 'var(--ink-1)',
              font: `${sel ? 500 : 400} 13px var(--ui)`, cursor: 'pointer',
            }}>
              <IconC size={14} stroke={sel ? 'var(--teal)' : 'currentColor'}/>{label}
            </div>
          ))}
        </div>

        <div style={{ flex: 1, padding: '24px 32px', overflow: 'auto' }}>
          <div style={{ font: '400 11px var(--mono)', color: 'var(--ink-3)', letterSpacing: '0.16em', textTransform: 'uppercase' }}>Settings · Connection</div>
          <div style={{ font: '400 28px var(--serif)', color: 'var(--ink-0)', letterSpacing: '-0.01em', marginTop: 4, marginBottom: 22 }}>
            Tune the <em style={{ color: 'var(--teal)' }}>pipes</em>.
          </div>

          {/* Download dir */}
          <div className="glass" style={{ padding: 20, marginBottom: 14 }}>
            <div style={{ font: '500 14px var(--ui)' }}>Download folder</div>
            <div style={{ marginTop: 10, display: 'flex', gap: 8 }}>
              <input value={local.downloadDir || ''}
                     onChange={e => set('downloadDir', e.target.value)}
                     style={{ flex: 1, background: 'rgba(255,255,255,0.04)', border: '1px solid var(--line-2)', borderRadius: 8, padding: '8px 12px', color: 'var(--ink-0)', font: '400 13px var(--mono)', outline: 'none' }}/>
            </div>
          </div>

          {/* Concurrent + connections */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14, marginBottom: 14 }}>
            <div className="glass" style={{ padding: 18 }}>
              <div style={{ font: '500 13px var(--ui)' }}>Concurrent downloads</div>
              <div style={{ font: '400 12px var(--ui)', color: 'var(--ink-2)', marginTop: 2, marginBottom: 12 }}>How many run at once</div>
              <div style={{ display: 'flex', gap: 4 }}>
                {concurrencyOpts.map((n, i) => {
                  const sel = n === local.concurrentDownloads || (n === '∞' && local.concurrentDownloads === 0);
                  return (
                    <div key={n} onClick={() => set('concurrentDownloads', n === '∞' ? 0 : n)} style={{
                      flex: 1, padding: '8px 0', borderRadius: 8, textAlign: 'center', cursor: 'pointer',
                      background: sel ? 'linear-gradient(180deg, rgba(120,200,255,0.18), rgba(120,200,255,0.05))' : 'rgba(255,255,255,0.03)',
                      border: `1px solid ${sel ? 'rgba(100,200,255,0.5)' : 'var(--line)'}`,
                      font: '500 13px var(--ui)', color: sel ? 'var(--teal)' : 'var(--ink-1)',
                      userSelect: 'none',
                    }}>{n}</div>
                  );
                })}
              </div>
            </div>
            <div className="glass" style={{ padding: 18 }}>
              <div style={{ font: '500 13px var(--ui)' }}>Connections per file</div>
              <div style={{ font: '400 12px var(--ui)', color: 'var(--ink-2)', marginTop: 2, marginBottom: 12 }}>Multi-thread chunks</div>
              <div style={{ display: 'flex', gap: 4 }}>
                {connOpts.map((n) => {
                  const val = parseInt(n);
                  const sel = val === local.connectionsPerFile;
                  return (
                    <div key={n} onClick={() => set('connectionsPerFile', val)} style={{
                      flex: 1, padding: '8px 0', borderRadius: 8, textAlign: 'center', cursor: 'pointer',
                      background: sel ? 'linear-gradient(180deg, rgba(180,140,255,0.18), rgba(180,140,255,0.05))' : 'rgba(255,255,255,0.03)',
                      border: `1px solid ${sel ? 'rgba(160,120,255,0.5)' : 'var(--line)'}`,
                      font: '500 13px var(--ui)', color: sel ? 'var(--violet)' : 'var(--ink-1)',
                      userSelect: 'none',
                    }}>{n}</div>
                  );
                })}
              </div>
            </div>
          </div>

          {/* Toggles */}
          {[
            { key: 'autoDetectVideos', t: 'Auto-detect videos on visited pages', s: 'Show the sniffer toast when a stream is found.' },
            { key: 'pauseOnMetered',   t: 'Pause on metered connections',         s: 'Hold downloads on hotspots & limited networks.' },
            { key: 'resumeOnLaunch',   t: 'Resume on app launch',                  s: 'Pick up where you left off.' },
            { key: 'verifyChecksums',  t: 'Verify checksums when available',       s: 'Re-check files match their declared hash.' },
          ].map((r) => (
            <div key={r.key} className="glass" style={{ padding: 16, display: 'flex', alignItems: 'center', gap: 16, marginBottom: 8 }}>
              <div style={{ flex: 1 }}>
                <div style={{ font: '500 13px var(--ui)' }}>{r.t}</div>
                <div style={{ font: '400 12px var(--ui)', color: 'var(--ink-2)', marginTop: 2 }}>{r.s}</div>
              </div>
              <div onClick={() => set(r.key, !local[r.key])} style={{
                width: 42, height: 24, borderRadius: 999, cursor: 'pointer', flex: 'none',
                background: local[r.key] ? 'linear-gradient(135deg, var(--teal), var(--violet))' : 'rgba(255,255,255,0.08)',
                position: 'relative',
                boxShadow: local[r.key] ? '0 0 12px rgba(0,180,200,0.4)' : 'none',
                transition: 'background .2s',
              }}>
                <div style={{
                  position: 'absolute', top: 2, left: local[r.key] ? 20 : 2,
                  width: 20, height: 20, borderRadius: '50%', background: '#fff',
                  boxShadow: '0 2px 6px rgba(0,0,0,0.4)', transition: 'left .2s',
                }}/>
              </div>
            </div>
          ))}

          <div style={{ marginTop: 20, display: 'flex', justifyContent: 'flex-end', gap: 10 }}>
            <button onClick={() => onNavChange && onNavChange('active')} style={{
              padding: '10px 20px', borderRadius: 10, border: '1px solid var(--line-2)',
              background: 'transparent', color: 'var(--ink-1)', font: '500 13px var(--ui)', cursor: 'pointer',
            }}>Cancel</button>
            <button onClick={save} style={{
              padding: '10px 20px', borderRadius: 10, border: 0,
              background: 'linear-gradient(135deg, var(--teal), var(--violet))',
              color: '#0a0a0c', font: '600 13px var(--ui)', cursor: 'pointer',
              boxShadow: '0 0 18px rgba(0,180,200,0.35)',
            }}>Save changes</button>
          </div>
        </div>
      </div>
    </div>
  );
}

Object.assign(window, { EmptyState, CompletedLibrary, SettingsPanel });
