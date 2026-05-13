// Widget concepts: floating drop zone (3 states), video sniffer toast, complete moment

// ── Drop Zone — idle (small, dockable orb) ──────────────
function DropIdle() {
  return (
    <div className="nx-dark" style={{
      width: '100%', height: '100%', position: 'relative',
      background: 'linear-gradient(135deg, oklch(0.20 0.04 240), oklch(0.10 0.02 270))',
      display: 'grid', placeItems: 'center',
      borderRadius: 24, overflow: 'hidden',
    }}>
      <Starfield count={28} width={300} height={300}/>
      <div style={{ animation: 'nx-float 4s ease-in-out infinite' }}>
        <div className="glass" style={{
          width: 88, height: 88, borderRadius: '50%',
          display: 'grid', placeItems: 'center',
          background: 'radial-gradient(circle at 30% 30%, oklch(0.55 0.20 210), oklch(0.30 0.18 280))',
          border: '1px solid rgba(255,255,255,0.25)',
          boxShadow: '0 14px 40px oklch(0.40 0.22 240 / 0.5), inset 0 1px 0 rgba(255,255,255,0.4)',
        }}>
          <TideMark size={44}/>
        </div>
      </div>
      <div style={{
        position: 'absolute', bottom: 18, left: 0, right: 0,
        textAlign: 'center', font: '400 11px var(--mono)', color: 'var(--ink-2)',
        letterSpacing: '0.14em', textTransform: 'uppercase',
      }}>idle</div>
    </div>
  );
}

// ── Drop Zone — hovering (portal open) ──────────────────
function DropHover() {
  return (
    <div className="nx-dark" style={{
      width: '100%', height: '100%', position: 'relative',
      background: 'linear-gradient(135deg, oklch(0.20 0.04 240), oklch(0.10 0.02 270))',
      display: 'grid', placeItems: 'center',
      borderRadius: 24, overflow: 'hidden',
    }}>
      <Starfield count={36} width={300} height={300}/>
      {/* Portal rings */}
      <div style={{ position: 'absolute', width: 260, height: 260, borderRadius: '50%',
        border: '1px solid oklch(0.75 0.18 210 / 0.18)', animation: 'nx-orbit 18s linear infinite' }}/>
      <div style={{ position: 'absolute', width: 210, height: 210, borderRadius: '50%',
        border: '1px dashed oklch(0.70 0.20 290 / 0.35)' }}/>
      <div style={{ position: 'absolute', width: 160, height: 160, borderRadius: '50%',
        background: 'radial-gradient(circle, oklch(0.55 0.20 220 / 0.35), transparent 70%)',
        filter: 'blur(6px)' }}/>

      <div className="glass" style={{
        width: 134, height: 134, borderRadius: '50%',
        display: 'grid', placeItems: 'center',
        background: 'radial-gradient(circle at 30% 30%, oklch(0.70 0.22 210), oklch(0.45 0.22 290))',
        border: '1.5px solid rgba(255,255,255,0.4)',
        boxShadow: '0 0 60px oklch(0.55 0.22 240 / 0.7), inset 0 2px 1px rgba(255,255,255,0.5)',
        position: 'relative',
      }}>
        <Icons.Down size={36} stroke="#fff" sw={2}/>
      </div>

      <div style={{
        position: 'absolute', bottom: 24, left: 0, right: 0,
        textAlign: 'center',
      }}>
        <div style={{ font: '400 18px var(--serif)', fontStyle: 'italic', color: 'var(--ink-0)' }}>release to grab</div>
        <div style={{ font: '400 10px var(--mono)', color: 'var(--ink-3)', marginTop: 4, letterSpacing: '0.16em', textTransform: 'uppercase' }}>portal open</div>
      </div>
    </div>
  );
}

// ── Drop Zone — receiving ───────────────────────────────
function DropReceiving() {
  return (
    <div className="nx-dark" style={{
      width: '100%', height: '100%', position: 'relative',
      background: 'linear-gradient(135deg, oklch(0.20 0.04 240), oklch(0.10 0.02 270))',
      display: 'grid', placeItems: 'center',
      borderRadius: 24, overflow: 'hidden',
    }}>
      <Starfield count={24} width={300} height={300}/>

      {/* Confetti particles */}
      {Array.from({ length: 12 }).map((_, i) => {
        const a = (i / 12) * Math.PI * 2;
        const r = 80 + (i % 3) * 18;
        return (
          <div key={i} style={{
            position: 'absolute',
            left: '50%', top: '50%',
            width: 4, height: 4, borderRadius: 2,
            background: i % 2 ? 'var(--teal)' : 'var(--violet)',
            transform: `translate(${Math.cos(a) * r}px, ${Math.sin(a) * r - 20}px)`,
            boxShadow: '0 0 6px currentColor',
            opacity: 0.85,
          }}/>
        );
      })}

      <div style={{ position: 'relative' }}>
        <RingProgress size={130} sw={6} value={0.62} from="oklch(0.80 0.18 200)" to="oklch(0.60 0.22 290)">
          <div style={{ textAlign: 'center' }}>
            <Icons.Sparkle size={20} stroke="var(--teal)"/>
            <div style={{ font: '500 11px var(--mono)', color: 'var(--ink-0)', marginTop: 4 }}>62%</div>
          </div>
        </RingProgress>
      </div>

      <div style={{
        position: 'absolute', bottom: 22, left: 0, right: 0,
        textAlign: 'center',
      }}>
        <div style={{ font: '400 14px var(--ui)', color: 'var(--ink-0)' }}>
          Pulling <em style={{ font: '400 14px var(--serif)', fontStyle: 'italic', color: 'var(--teal)' }}>aurora.mp4</em>
        </div>
        <div style={{ font: '400 10px var(--mono)', color: 'var(--ink-3)', marginTop: 4 }}>14.2 MB/s · 12s left</div>
      </div>
    </div>
  );
}

// ── Video Sniffer toast (in-browser detection) ─────────
function SnifferToast() {
  return (
    <div className="nx-dark" style={{
      width: '100%', height: '100%', position: 'relative',
      background: 'linear-gradient(180deg, oklch(0.18 0.02 250), oklch(0.10 0.02 260))',
      borderRadius: 18, padding: 24,
      display: 'flex', flexDirection: 'column', justifyContent: 'flex-end',
      overflow: 'hidden',
    }}>
      {/* Faux browser content */}
      <div style={{ position: 'absolute', top: 14, left: 16, right: 16 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, font: '400 11px var(--mono)', color: 'var(--ink-3)' }}>
          <Icons.Globe size={12}/> vimeo.com/showcase
        </div>
        <div style={{
          marginTop: 14, height: 154, borderRadius: 12, overflow: 'hidden',
          background: 'linear-gradient(135deg, oklch(0.32 0.08 220), oklch(0.20 0.10 280))',
          border: '1px solid rgba(255,255,255,0.06)',
          position: 'relative',
        }}>
          <div style={{
            position: 'absolute', inset: 0,
            backgroundImage: 'repeating-linear-gradient(135deg, rgba(255,255,255,0.05) 0 2px, transparent 2px 18px)',
          }}/>
          <div style={{
            position: 'absolute', left: '50%', top: '50%', transform: 'translate(-50%,-50%)',
            width: 48, height: 48, borderRadius: '50%',
            background: 'rgba(0,0,0,0.5)', backdropFilter: 'blur(6px)',
            display: 'grid', placeItems: 'center',
          }}>
            <Icons.Play size={18}/>
          </div>
          <div style={{ position: 'absolute', left: 12, bottom: 10, font: '500 8px var(--mono)', color: 'rgba(255,255,255,0.6)', textTransform: 'uppercase', letterSpacing: '0.08em' }}>
            featured video
          </div>
        </div>
      </div>

      {/* Toast */}
      <div className="glass" style={{
        padding: 14,
        background: 'rgba(15,15,22,0.85)',
        backdropFilter: 'blur(28px) saturate(140%)',
        border: '1px solid rgba(255,255,255,0.10)',
        boxShadow: '0 18px 60px rgba(0,0,0,0.5)',
        position: 'relative',
      }}>
        <div style={{
          position: 'absolute', left: 14, top: -1, height: 2, width: 60,
          background: 'linear-gradient(90deg, var(--teal), var(--violet))',
          borderRadius: 2,
          boxShadow: '0 0 12px var(--teal)',
        }}/>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 12 }}>
          <div style={{
            width: 36, height: 36, borderRadius: 10,
            background: 'linear-gradient(135deg, var(--teal), var(--violet))',
            display: 'grid', placeItems: 'center', color: '#0a0a0c',
            boxShadow: '0 0 16px oklch(0.65 0.20 240 / 0.6)',
          }}>
            <Icons.Sparkle size={16} stroke="#0a0a0c" sw={2}/>
          </div>
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ font: '500 13px var(--ui)', color: 'var(--ink-0)' }}>
              Video spotted on this page
            </div>
            <div style={{ font: '400 11px var(--mono)', color: 'var(--ink-3)',
                          whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
              The Wave Forms — Audio Visuals · 04:18
            </div>
          </div>
          <button style={{
            background: 'transparent', border: 0, color: 'var(--ink-3)', cursor: 'pointer',
            display: 'grid', placeItems: 'center', padding: 4,
          }}><Icons.X size={14}/></button>
        </div>

        <div style={{ display: 'flex', gap: 6, marginBottom: 12 }}>
          {[
            { l: '4K', s: '512 MB', hot: true },
            { l: '1080p', s: '184 MB' },
            { l: '720p', s: '92 MB' },
            { l: 'MP3', s: '6 MB' },
          ].map((q) => (
            <div key={q.l} style={{
              flex: 1, padding: '8px 6px', borderRadius: 8,
              background: q.hot ? 'linear-gradient(180deg, rgba(120,200,255,0.15), rgba(120,200,255,0.04))' : 'rgba(255,255,255,0.03)',
              border: `1px solid ${q.hot ? 'oklch(0.75 0.18 210 / 0.5)' : 'var(--line-2)'}`,
              textAlign: 'center',
              boxShadow: q.hot ? '0 0 14px oklch(0.55 0.20 210 / 0.3)' : 'none',
            }}>
              <div style={{ font: '600 11px var(--ui)', color: q.hot ? 'var(--teal)' : 'var(--ink-0)' }}>{q.l}</div>
              <div style={{ font: '400 9px var(--mono)', color: 'var(--ink-3)', marginTop: 2 }}>{q.s}</div>
            </div>
          ))}
        </div>

        <button style={{
          width: '100%', padding: '12px 14px', borderRadius: 12,
          background: 'linear-gradient(135deg, var(--teal), var(--violet))',
          color: '#0a0a0c', font: '600 13px var(--ui)', border: 0, cursor: 'pointer',
          display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
          boxShadow: '0 8px 28px oklch(0.55 0.20 240 / 0.45)',
          letterSpacing: '-0.01em',
        }}>
          <Icons.Down size={14} stroke="#0a0a0c" sw={2.2}/>
          Grab it
          <span style={{ font: '500 10px var(--mono)', opacity: 0.7, marginLeft: 6 }}>⌘⇧D</span>
        </button>

        <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 10,
                      font: '400 10px var(--mono)', color: 'var(--ink-3)' }}>
          <span>auto-detected · m3u8</span>
          <span>save to ~/Movies</span>
        </div>
      </div>
    </div>
  );
}

// ── Complete moment ─────────────────────────────────
function CompleteMoment() {
  return (
    <div className="nx-dark" style={{
      width: '100%', height: '100%', position: 'relative', overflow: 'hidden',
      background: 'radial-gradient(circle at 50% 60%, oklch(0.25 0.15 195) 0%, oklch(0.08 0.04 250) 65%)',
      borderRadius: 18,
      display: 'grid', placeItems: 'center',
    }}>
      <Starfield count={40} width={600} height={500}/>

      {/* Confetti */}
      {Array.from({ length: 28 }).map((_, i) => {
        const a = ((i * 360) / 28) * (Math.PI / 180);
        const dist = 120 + (i % 4) * 22;
        const colors = ['oklch(0.80 0.18 200)', 'oklch(0.75 0.18 290)', 'oklch(0.80 0.16 60)', 'oklch(0.85 0.16 150)'];
        const c = colors[i % 4];
        return (
          <div key={i} style={{
            position: 'absolute', left: '50%', top: '52%',
            width: i % 3 ? 4 : 6, height: i % 3 ? 4 : 10,
            borderRadius: i % 3 ? 2 : 3,
            background: c,
            transform: `translate(${Math.cos(a) * dist}px, ${Math.sin(a) * dist}px) rotate(${i * 23}deg)`,
            boxShadow: `0 0 8px ${c}`,
            opacity: 0.9,
          }}/>
        );
      })}

      {/* Halo rings */}
      <div style={{ position: 'absolute', width: 280, height: 280, borderRadius: '50%',
        border: '1px solid oklch(0.75 0.20 200 / 0.18)' }}/>
      <div style={{ position: 'absolute', width: 200, height: 200, borderRadius: '50%',
        border: '1px solid oklch(0.75 0.20 200 / 0.30)' }}/>

      {/* Checkmark medallion */}
      <div style={{ position: 'relative', textAlign: 'center' }}>
        <div style={{
          width: 110, height: 110, borderRadius: '50%',
          background: 'linear-gradient(135deg, oklch(0.78 0.18 195), oklch(0.55 0.22 250))',
          display: 'grid', placeItems: 'center',
          boxShadow: '0 0 60px oklch(0.65 0.22 220 / 0.7), inset 0 2px 2px rgba(255,255,255,0.4)',
          margin: '0 auto',
        }}>
          <Icons.Check size={50} stroke="#fff" sw={3}/>
        </div>
        <div style={{ font: '400 30px/1.1 var(--serif)', color: 'var(--ink-0)', marginTop: 24, letterSpacing: '-0.01em' }}>
          all <em style={{ color: 'var(--teal)' }}>yours</em>.
        </div>
        <div style={{ font: '400 13px var(--ui)', color: 'var(--ink-2)', marginTop: 6 }}>
          aurora.mp4 saved to <span style={{ font: '400 12px var(--mono)', color: 'var(--ink-1)' }}>~/Movies</span>
        </div>

        <div style={{
          display: 'inline-flex', alignItems: 'center', gap: 14, marginTop: 22,
          padding: '8px 14px', borderRadius: 999,
          background: 'rgba(255,255,255,0.04)', border: '1px solid var(--line-2)',
          backdropFilter: 'blur(20px)',
          font: '400 11px var(--mono)', color: 'var(--ink-1)',
        }}>
          <span><span style={{ color: 'var(--teal)' }}>1.84 GB</span> · 2m 31s</span>
          <span style={{ color: 'var(--ink-3)' }}>·</span>
          <button style={{
            background: 'transparent', border: 0, color: 'var(--ink-0)',
            font: '500 11px var(--ui)', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 4, padding: 0,
          }}>
            <Icons.Folder size={11}/> Reveal
          </button>
          <button style={{
            background: 'transparent', border: 0, color: 'var(--ink-0)',
            font: '500 11px var(--ui)', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 4, padding: 0,
          }}>
            <Icons.Play size={11}/> Play
          </button>
        </div>
      </div>
    </div>
  );
}

Object.assign(window, { DropIdle, DropHover, DropReceiving, SnifferToast, CompleteMoment });
