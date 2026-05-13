// State screens: empty state, completed library, settings panel, progress studies

// ── EMPTY STATE — serene landscape with sleeping mascot ───
function EmptyState() {
  return (
    <div className="nx-dark" style={{
      width: '100%', height: '100%', position: 'relative', overflow: 'hidden',
      background: 'linear-gradient(180deg, oklch(0.20 0.08 270) 0%, oklch(0.10 0.06 250) 60%, oklch(0.18 0.10 220) 100%)',
      borderRadius: 0,
      display: 'flex', flexDirection: 'column',
      color: 'var(--ink-0)',
    }}>
      <ChromeBar/>

      {/* Starfield */}
      <Starfield count={70} width={1280} height={760}/>

      {/* Distant mountains — soft silhouettes */}
      <svg width="100%" height="220" viewBox="0 0 1280 220" preserveAspectRatio="none"
           style={{ position: 'absolute', left: 0, right: 0, bottom: 80, opacity: 0.7 }}>
        <defs>
          <linearGradient id="mtn" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="oklch(0.25 0.10 250)"/>
            <stop offset="100%" stopColor="oklch(0.10 0.04 250)"/>
          </linearGradient>
        </defs>
        <path d="M0 200 L 0 130 L 120 80 L 240 140 L 360 70 L 480 130 L 600 90 L 720 150 L 840 80 L 960 140 L 1080 100 L 1200 160 L 1280 110 L 1280 200 Z" fill="url(#mtn)"/>
      </svg>
      <svg width="100%" height="180" viewBox="0 0 1280 180" preserveAspectRatio="none"
           style={{ position: 'absolute', left: 0, right: 0, bottom: 0 }}>
        <defs>
          <linearGradient id="mtn2" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="oklch(0.16 0.06 230)"/>
            <stop offset="100%" stopColor="oklch(0.06 0.02 250)"/>
          </linearGradient>
        </defs>
        <path d="M0 170 L 0 100 L 80 50 L 200 110 L 320 40 L 480 90 L 640 30 L 800 100 L 960 50 L 1100 110 L 1280 60 L 1280 170 Z" fill="url(#mtn2)"/>
      </svg>

      {/* Soft horizon glow */}
      <div style={{ position: 'absolute', bottom: 60, left: 0, right: 0, height: 120,
        background: 'radial-gradient(ellipse at 50% 100%, oklch(0.55 0.20 220 / 0.35), transparent 70%)',
        filter: 'blur(20px)',
      }}/>

      {/* Content */}
      <div style={{ flex: 1, display: 'grid', placeItems: 'center', position: 'relative', zIndex: 2 }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{ display: 'inline-block' }}>
            <Mascot size={220} mood="sleep"/>
          </div>
          <div style={{ font: '400 38px/1.1 var(--serif)', color: 'var(--ink-0)', marginTop: 8, letterSpacing: '-0.01em' }}>
            <em style={{ color: 'var(--teal)' }}>Tide</em> is resting.
          </div>
          <div style={{ font: '400 14px var(--ui)', color: 'var(--ink-2)', marginTop: 8, maxWidth: 380, marginInline: 'auto' }}>
            No active downloads. Drop a link anywhere on screen, paste it, or wake Tide up.
          </div>

          <div style={{
            display: 'inline-flex', alignItems: 'center', gap: 10, marginTop: 24,
            padding: '12px 14px 12px 16px', borderRadius: 14,
            background: 'rgba(255,255,255,0.05)',
            backdropFilter: 'blur(28px)',
            border: '1px solid var(--line-2)',
          }}>
            <Icons.Link size={14} stroke="var(--ink-2)"/>
            <span style={{ font: '400 13px var(--mono)', color: 'var(--ink-2)' }}>paste a link here…</span>
            <span style={{
              font: '400 10px var(--mono)', color: 'var(--ink-2)',
              padding: '3px 7px', border: '1px solid var(--line-2)', borderRadius: 6,
            }}>⌘V</span>
            <button style={{
              padding: '8px 16px', marginLeft: 6, borderRadius: 10,
              background: 'linear-gradient(135deg, var(--teal), var(--violet))',
              color: '#0a0a0c', font: '600 12px var(--ui)', border: 0, cursor: 'pointer',
              boxShadow: '0 0 18px oklch(0.65 0.20 240 / 0.4)',
            }}>Wake Tide</button>
          </div>
        </div>
      </div>
    </div>
  );
}

// ── COMPLETED LIBRARY — grid view ─────────────────────────
const NX_LIB = [
  { id: 1, t: 'Solarpunk City — Walkthrough', sub: '4K · 12:42', kind: 'video', tone: 'teal',  size: '2.1 GB', when: 'Today, 4:18 PM' },
  { id: 2, t: 'Whiteboard Sessions vol. III', sub: '1080p · 38:09', kind: 'video', tone: 'violet', size: '1.4 GB', when: 'Today, 1:02 PM' },
  { id: 3, t: 'Annual report — design final', sub: 'PDF · 84 pages', kind: 'doc',   tone: 'sand',   size: '24 MB', when: 'Today, 11:48 AM' },
  { id: 4, t: 'Brand kit — Q3 refresh',       sub: 'ZIP · 412 files', kind: 'doc',   tone: 'coral',  size: '684 MB', when: 'Yesterday' },
  { id: 5, t: 'Coastal · field recordings',   sub: 'FLAC · 14 tracks', kind: 'music', tone: 'sage',   size: '512 MB', when: 'Yesterday' },
  { id: 6, t: 'Tide test sequence',            sub: '4K · 02:18', kind: 'video', tone: 'ink',    size: '512 MB', when: '2 days ago' },
  { id: 7, t: 'Portrait shoot — studio raws',  sub: 'RAW · 248 files', kind: 'image', tone: 'coral', size: '6.4 GB', when: '2 days ago' },
  { id: 8, t: 'Lo-fi for late drives',         sub: 'MP3 · 24 tracks', kind: 'music', tone: 'violet', size: '188 MB', when: '3 days ago' },
];

function CompletedLibrary() {
  return (
    <div className="nx-dark nx-grain" style={{
      width: '100%', height: '100%', background: 'var(--bg-0)',
      display: 'flex', flexDirection: 'column', overflow: 'hidden',
      position: 'relative', color: 'var(--ink-0)',
    }}>
      <div className="nx-aurora"/>
      <ChromeBar/>
      <div style={{ flex: 1, display: 'flex', minHeight: 0, position: 'relative', zIndex: 1 }}>
        <Sidebar active="done"/>
        <div style={{ flex: 1, padding: '20px 24px', display: 'flex', flexDirection: 'column', gap: 16, overflow: 'hidden' }}>
          <div style={{ display: 'flex', alignItems: 'flex-end', justifyContent: 'space-between' }}>
            <div>
              <div style={{ font: '400 11px var(--mono)', color: 'var(--ink-3)', letterSpacing: '0.16em', textTransform: 'uppercase' }}>
                Completed · 184 items · 47.2 GB
              </div>
              <div style={{ font: '400 28px/1.05 var(--serif)', color: 'var(--ink-0)', letterSpacing: '-0.01em', marginTop: 4, whiteSpace: 'nowrap' }}>
                Your <em style={{ color: 'var(--teal)' }}>catch</em> this week.
              </div>
            </div>
            <div style={{ display: 'flex', gap: 8 }}>
              {['All', 'Video', 'Music', 'Docs', 'Images'].map((t, i) => (
                <div key={t} style={{
                  padding: '6px 12px', borderRadius: 999,
                  background: i === 0 ? 'rgba(255,255,255,0.08)' : 'transparent',
                  border: `1px solid ${i === 0 ? 'var(--line-2)' : 'var(--line)'}`,
                  font: `${i === 0 ? 500 : 400} 12px var(--ui)`,
                  color: i === 0 ? 'var(--ink-0)' : 'var(--ink-2)', cursor: 'pointer',
                }}>{t}</div>
              ))}
            </div>
          </div>

          <div style={{
            display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 14, overflow: 'auto', flex: 1,
            paddingBottom: 8,
          }}>
            {NX_LIB.map((it) => {
              const KindIcon = { video: Icons.Video, doc: Icons.Doc, music: Icons.Music, image: Icons.Image }[it.kind];
              return (
                <div key={it.id} className="glass" style={{
                  padding: 12, display: 'flex', flexDirection: 'column', gap: 10,
                }}>
                  <div style={{ position: 'relative' }}>
                    <Thumb w="100%" h={120} label={it.kind} tone={it.tone} r={10}/>
                    {it.kind === 'video' && (
                      <div style={{
                        position: 'absolute', left: 8, bottom: 8,
                        padding: '3px 7px', borderRadius: 6,
                        background: 'rgba(0,0,0,0.55)', backdropFilter: 'blur(8px)',
                        font: '500 10px var(--mono)', color: '#fff',
                      }}>{it.sub.split(' · ')[1]}</div>
                    )}
                    <div style={{
                      position: 'absolute', right: 8, top: 8,
                      width: 24, height: 24, borderRadius: 8,
                      background: 'rgba(0,0,0,0.4)', backdropFilter: 'blur(8px)',
                      display: 'grid', placeItems: 'center',
                      color: 'var(--good)',
                      border: '1px solid rgba(255,255,255,0.12)',
                    }}>
                      <Icons.Check size={11} sw={2.5}/>
                    </div>
                  </div>
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 2 }}>
                      <KindIcon size={10} stroke="var(--ink-2)"/>
                      <span style={{ font: '400 10px var(--mono)', color: 'var(--ink-3)' }}>{it.sub}</span>
                    </div>
                    <div style={{ font: '500 13px/1.3 var(--ui)', color: 'var(--ink-0)',
                                  display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
                      {it.t}
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 6,
                                  font: '400 10px var(--mono)', color: 'var(--ink-3)' }}>
                      <span>{it.size}</span>
                      <span>{it.when}</span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}

// ── SETTINGS PANEL ───────────────────────────────────────
function SettingsPanel() {
  return (
    <div className="nx-dark nx-grain" style={{
      width: '100%', height: '100%', background: 'var(--bg-0)',
      display: 'flex', flexDirection: 'column', overflow: 'hidden',
      position: 'relative', color: 'var(--ink-0)',
    }}>
      <div className="nx-aurora"/>
      <ChromeBar/>
      <div style={{ flex: 1, display: 'flex', minHeight: 0, position: 'relative', zIndex: 1 }}>
        {/* Settings sub-nav */}
        <div style={{
          width: 200, flex: 'none', borderRight: '1px solid var(--line)',
          padding: '20px 12px', display: 'flex', flexDirection: 'column', gap: 2,
        }}>
          <div style={{ font: '500 10px var(--mono)', color: 'var(--ink-3)', letterSpacing: '0.14em', textTransform: 'uppercase', padding: '6px 10px 10px' }}>Settings</div>
          {[
            ['General', Icons.Settings, false],
            ['Connection', Icons.Wifi, true],
            ['Schedule', Icons.Bolt, false],
            ['Browser', Icons.Globe, false],
            ['Library', Icons.Folder, false],
            ['Appearance', Icons.Sparkle, false],
            ['Advanced', Icons.Stars, false],
          ].map(([label, IconC, sel]) => (
            <div key={label} style={{
              display: 'flex', alignItems: 'center', gap: 10,
              padding: '8px 10px', borderRadius: 10,
              background: sel ? 'linear-gradient(180deg, rgba(255,255,255,0.06), rgba(255,255,255,0.02))' : 'transparent',
              border: sel ? '1px solid var(--line-2)' : '1px solid transparent',
              color: sel ? 'var(--ink-0)' : 'var(--ink-1)',
              font: `${sel ? 500 : 400} 13px var(--ui)`, cursor: 'pointer',
            }}>
              <IconC size={14} stroke={sel ? 'var(--teal)' : 'currentColor'}/>
              {label}
            </div>
          ))}
        </div>

        <div style={{ flex: 1, padding: '24px 32px', overflow: 'auto' }}>
          <div style={{ font: '400 11px var(--mono)', color: 'var(--ink-3)', letterSpacing: '0.16em', textTransform: 'uppercase' }}>
            Settings · Connection
          </div>
          <div style={{ font: '400 28px var(--serif)', color: 'var(--ink-0)', letterSpacing: '-0.01em', marginTop: 4, marginBottom: 22 }}>
            Tune the <em style={{ color: 'var(--teal)' }}>pipes</em>.
          </div>

          {/* Speed control card */}
          <div className="glass" style={{ padding: 20, marginBottom: 14 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <div>
                <div style={{ font: '500 14px var(--ui)', color: 'var(--ink-0)' }}>Maximum download speed</div>
                <div style={{ font: '400 12px var(--ui)', color: 'var(--ink-2)', marginTop: 2 }}>
                  Cap your total throughput. Set to <span style={{ font: '400 11px var(--mono)' }}>0</span> for unlimited.
                </div>
              </div>
              <div style={{ font: '500 24px var(--mono)', color: 'var(--ink-0)' }}>
                72<span style={{ font: '400 11px var(--mono)', color: 'var(--ink-3)' }}> MB/s</span>
              </div>
            </div>
            {/* Slider track */}
            <div style={{ marginTop: 18, position: 'relative', height: 22 }}>
              <div style={{ position: 'absolute', left: 0, right: 0, top: 9, height: 4, borderRadius: 999, background: 'rgba(255,255,255,0.06)' }}/>
              <div style={{ position: 'absolute', left: 0, top: 9, width: '60%', height: 4, borderRadius: 999, background: 'linear-gradient(90deg, var(--teal), var(--violet))', boxShadow: '0 0 12px var(--teal)' }}/>
              <div style={{ position: 'absolute', left: '60%', top: 0, transform: 'translate(-50%, 0)',
                width: 22, height: 22, borderRadius: '50%',
                background: '#fff', border: '4px solid oklch(0.65 0.18 240)',
                boxShadow: '0 4px 14px rgba(0,0,0,0.5)' }}/>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 6, font: '400 10px var(--mono)', color: 'var(--ink-3)' }}>
              <span>0 MB/s</span><span>50</span><span>100</span><span>∞</span>
            </div>
          </div>

          {/* Concurrent + connections */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14, marginBottom: 14 }}>
            <div className="glass" style={{ padding: 18 }}>
              <div style={{ font: '500 13px var(--ui)' }}>Concurrent downloads</div>
              <div style={{ font: '400 12px var(--ui)', color: 'var(--ink-2)', marginTop: 2, marginBottom: 12 }}>How many run at once</div>
              <div style={{ display: 'flex', gap: 6 }}>
                {[1,2,3,4,5,6,8,'∞'].map((n, i) => (
                  <div key={n} style={{
                    flex: 1, padding: '8px 0', borderRadius: 8, textAlign: 'center',
                    background: i === 4 ? 'linear-gradient(180deg, rgba(120,200,255,0.18), rgba(120,200,255,0.05))' : 'rgba(255,255,255,0.03)',
                    border: `1px solid ${i === 4 ? 'oklch(0.75 0.16 210 / 0.5)' : 'var(--line)'}`,
                    font: '500 13px var(--ui)', color: i === 4 ? 'var(--teal)' : 'var(--ink-1)',
                    boxShadow: i === 4 ? '0 0 12px oklch(0.55 0.18 210 / 0.3)' : 'none',
                  }}>{n}</div>
                ))}
              </div>
            </div>
            <div className="glass" style={{ padding: 18 }}>
              <div style={{ font: '500 13px var(--ui)' }}>Connections per file</div>
              <div style={{ font: '400 12px var(--ui)', color: 'var(--ink-2)', marginTop: 2, marginBottom: 12 }}>Multi-thread chunks</div>
              <div style={{ display: 'flex', gap: 6 }}>
                {['1','2','4','8','16','32'].map((n, i) => (
                  <div key={n} style={{
                    flex: 1, padding: '8px 0', borderRadius: 8, textAlign: 'center',
                    background: i === 3 ? 'linear-gradient(180deg, rgba(180,140,255,0.18), rgba(180,140,255,0.05))' : 'rgba(255,255,255,0.03)',
                    border: `1px solid ${i === 3 ? 'oklch(0.70 0.18 295 / 0.5)' : 'var(--line)'}`,
                    font: '500 13px var(--ui)', color: i === 3 ? 'var(--violet)' : 'var(--ink-1)',
                  }}>{n}</div>
                ))}
              </div>
            </div>
          </div>

          {/* Toggles */}
          {[
            { t: 'Auto-detect videos on visited pages',  s: 'Show the sniffer toast when a downloadable stream is found.', on: true },
            { t: 'Pause on metered connections',          s: 'Hold downloads on hotspots & limited networks.', on: true },
            { t: 'Resume on app launch',                  s: 'Pick up where you left off.', on: false },
            { t: 'Verify checksums when available',       s: 'Re-check files match their declared hash.', on: true },
          ].map((r) => (
            <div key={r.t} className="glass" style={{
              padding: 16, display: 'flex', alignItems: 'center', gap: 16, marginBottom: 8,
            }}>
              <div style={{ flex: 1 }}>
                <div style={{ font: '500 13px var(--ui)' }}>{r.t}</div>
                <div style={{ font: '400 12px var(--ui)', color: 'var(--ink-2)', marginTop: 2 }}>{r.s}</div>
              </div>
              <div style={{
                width: 42, height: 24, borderRadius: 999,
                background: r.on ? 'linear-gradient(135deg, var(--teal), var(--violet))' : 'rgba(255,255,255,0.08)',
                position: 'relative', flex: 'none',
                boxShadow: r.on ? '0 0 12px oklch(0.65 0.18 240 / 0.5)' : 'none',
              }}>
                <div style={{
                  position: 'absolute', top: 2, left: r.on ? 20 : 2,
                  width: 20, height: 20, borderRadius: '50%',
                  background: '#fff',
                  boxShadow: '0 2px 6px rgba(0,0,0,0.4)',
                  transition: 'left .2s',
                }}/>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// ── Progress visual studies (compact, for the canvas) ────
function ProgressStudies() {
  return (
    <div className="nx-dark" style={{
      width: '100%', height: '100%', background: 'var(--bg-0)',
      padding: 32, display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 20,
      position: 'relative', overflow: 'hidden',
    }}>
      <div className="nx-aurora"/>
      <div style={{ gridColumn: '1 / -1' }}>
        <div style={{ font: '400 11px var(--mono)', color: 'var(--ink-3)', letterSpacing: '0.16em', textTransform: 'uppercase' }}>Studies</div>
        <div style={{ font: '400 26px var(--serif)', color: 'var(--ink-0)', letterSpacing: '-0.01em' }}>
          Six ways to <em style={{ color: 'var(--teal)' }}>show progress</em>.
        </div>
      </div>

      {[
        { name: 'Liquid pill', body: <LiquidBar value={0.62} height={18}/> },
        { name: 'Spectrum', body: <SpectrumBar value={0.72} segments={28} height={14}/> },
        { name: 'Ring + speed', body: (
            <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
              <RingProgress size={56} sw={5} value={0.66}>
                <div style={{ font: '500 11px var(--mono)', color: 'var(--ink-0)' }}>66%</div>
              </RingProgress>
              <Sparkline data={NX_SPEED_DATA.slice(8)} width={140} height={36}/>
            </div>
        )},
        { name: 'Particle dots', body: (
            <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
              {Array.from({ length: 30 }).map((_, i) => (
                <div key={i} style={{
                  width: 8, height: i < 18 ? 18 : Math.max(4, 18 - (i - 18) * 1.5),
                  borderRadius: 2,
                  background: i < 18 ? `oklch(0.78 0.16 ${200 + i*4})` : 'rgba(255,255,255,0.08)',
                  boxShadow: i < 18 ? `0 0 6px oklch(0.78 0.16 ${200 + i*4} / 0.6)` : 'none',
                }}/>
              ))}
            </div>
        )},
        { name: 'Tide gradient', body: (
            <div style={{ height: 18, borderRadius: 999, overflow: 'hidden', background: 'rgba(255,255,255,0.06)' }}>
              <div style={{
                width: '78%', height: '100%', borderRadius: 999,
                background: 'linear-gradient(90deg, oklch(0.45 0.22 295) 0%, oklch(0.55 0.22 240) 50%, oklch(0.85 0.16 195) 100%)',
                boxShadow: '0 0 14px oklch(0.65 0.18 230 / 0.6)',
              }}/>
            </div>
        )},
        { name: 'Shimmer ghost', body: (
          <div style={{ height: 18, borderRadius: 999, overflow: 'hidden', position: 'relative',
            background: 'linear-gradient(90deg, rgba(255,255,255,0.06), rgba(180,140,255,0.18), rgba(120,200,255,0.18), rgba(255,255,255,0.06))',
            backgroundSize: '200% 100%',
            animation: 'nx-shimmer 2s linear infinite',
          }}/>
        )},
      ].map((s) => (
        <div key={s.name} className="glass" style={{ padding: 18 }}>
          <div style={{ font: '400 10px var(--mono)', color: 'var(--ink-3)', letterSpacing: '0.14em', textTransform: 'uppercase', marginBottom: 14 }}>
            {s.name}
          </div>
          {s.body}
        </div>
      ))}
    </div>
  );
}

Object.assign(window, { EmptyState, CompletedLibrary, SettingsPanel, ProgressStudies, NX_LIB });
