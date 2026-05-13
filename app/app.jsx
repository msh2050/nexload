// Production app — single screen at a time, wired to Tauri backend.
// No design canvas, no mock data.

function SnifferToastLive({ data, onGrab, onDismiss }) {
  // data: { url, title, formats, host, thumbnail }
  const [selectedFmt, setSelectedFmt] = React.useState(0);
  const fmt = data.formats && data.formats[selectedFmt];

  return (
    <div className="nx-dark glass" style={{
      padding: 14,
      background: 'rgba(15,15,22,0.88)',
      backdropFilter: 'blur(28px) saturate(140%)',
      border: '1px solid rgba(255,255,255,0.10)',
      boxShadow: '0 18px 60px rgba(0,0,0,0.5)',
      borderRadius: 18, position: 'relative', overflow: 'hidden',
    }}>
      {/* Accent line */}
      <div style={{
        position: 'absolute', left: 14, top: -1, height: 2, width: 60,
        background: 'linear-gradient(90deg, var(--teal), var(--violet))',
        borderRadius: 2, boxShadow: '0 0 12px var(--teal)',
      }}/>

      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 12 }}>
        <div style={{
          width: 36, height: 36, borderRadius: 10,
          background: 'linear-gradient(135deg, var(--teal), var(--violet))',
          display: 'grid', placeItems: 'center', color: '#0a0a0c',
          boxShadow: '0 0 16px rgba(0,180,200,0.5)', flex: 'none',
        }}>
          <Icons.Sparkle size={16} stroke="#0a0a0c" sw={2}/>
        </div>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ font: '500 13px var(--ui)', color: 'var(--ink-0)' }}>Video spotted on this page</div>
          <div style={{ font: '400 11px var(--mono)', color: 'var(--ink-3)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
            {data.title} {data.host ? `· ${data.host}` : ''}
          </div>
        </div>
        <button onClick={onDismiss} style={{ background: 'transparent', border: 0, color: 'var(--ink-3)', cursor: 'pointer', display: 'grid', placeItems: 'center', padding: 4 }}>
          <Icons.X size={14}/>
        </button>
      </div>

      {data.formats && data.formats.length > 0 && (
        <div style={{ display: 'flex', gap: 6, marginBottom: 12 }}>
          {data.formats.map((f, i) => (
            <div key={f.formatId} onClick={() => setSelectedFmt(i)} style={{
              flex: 1, padding: '8px 6px', borderRadius: 8, textAlign: 'center', cursor: 'pointer',
              background: i === selectedFmt ? 'linear-gradient(180deg, rgba(120,200,255,0.15), rgba(120,200,255,0.04))' : 'rgba(255,255,255,0.03)',
              border: `1px solid ${i === selectedFmt ? 'rgba(100,200,255,0.5)' : 'var(--line-2)'}`,
              boxShadow: i === selectedFmt ? '0 0 14px rgba(80,180,255,0.25)' : 'none',
              userSelect: 'none',
            }}>
              <div style={{ font: '600 11px var(--ui)', color: i === selectedFmt ? 'var(--teal)' : 'var(--ink-0)' }}>{f.label}</div>
              {f.sizeMb && <div style={{ font: '400 9px var(--mono)', color: 'var(--ink-3)', marginTop: 2 }}>{f.sizeMb.toFixed(0)} MB</div>}
            </div>
          ))}
        </div>
      )}

      <button onClick={() => onGrab(fmt || {})} style={{
        width: '100%', padding: '12px 14px', borderRadius: 12,
        background: 'linear-gradient(135deg, var(--teal), var(--violet))',
        color: '#0a0a0c', font: '600 13px var(--ui)', border: 0, cursor: 'pointer',
        display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
        boxShadow: '0 8px 28px rgba(0,160,200,0.4)',
      }}>
        <Icons.Down size={14} stroke="#0a0a0c" sw={2.2}/>
        Grab it
      </button>

      {data.host && (
        <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 10, font: '400 10px var(--mono)', color: 'var(--ink-3)' }}>
          <span>auto-detected</span>
          <span>{data.host}</span>
        </div>
      )}
    </div>
  );
}

// ── App root ──────────────────────────────────────────────────
function App() {
  const [nav, setNav]               = React.useState('active');
  const [downloads, setDownloads]   = React.useState([]);
  const [completed, setCompleted]   = React.useState([]);
  const [sniffer, setSniffer]       = React.useState(null);
  const [appSettings, setSettings]  = React.useState(null);
  const [storageStats, setStorage]  = React.useState(null);
  const [speedHistory, setSpeedHist]= React.useState(Array(30).fill(0));
  const [totalSpeed, setTotalSpeed] = React.useState(0);
  const [pasteUrl, setPasteUrl]     = React.useState('');

  // ── Initialise ─────────────────────────────────────────────
  React.useEffect(() => {
    API.listActive().then(setDownloads).catch(console.warn);
    API.listCompleted().then(setCompleted).catch(console.warn);
    API.getSettings().then(setSettings).catch(console.warn);
    API.storageStats().then(setStorage).catch(console.warn);

    const unsubs = [];

    API.onDownloadUpdate(updates => {
      setDownloads(prev => {
        const map = new Map(prev.map(d => [d.id, d]));
        updates.forEach(u => map.set(u.id, { ...(map.get(u.id) || {}), ...u }));
        return Array.from(map.values());
      });
      const speed = updates.reduce((s, u) => s + (u.speedBytes || 0), 0);
      setTotalSpeed(speed);
      setSpeedHist(h => [...h.slice(1), speed / 1e6]);
    }).then(fn => unsubs.push(fn));

    API.onGlobalStat(stat => {
      setTotalSpeed(stat.totalSpeed || 0);
    }).then(fn => unsubs.push(fn));

    API.onSnifferDetected(payload => {
      setSniffer(payload);
    }).then(fn => unsubs.push(fn));

    // Global paste listener
    const onPaste = e => {
      const text = (e.clipboardData || window.clipboardData)?.getData('text') || '';
      if (/^https?:\/\//.test(text)) {
        setPasteUrl(text);
        handleGrab(text);
      }
    };
    document.addEventListener('paste', onPaste);

    // Global drag-and-drop listener
    const onDrop = e => {
      e.preventDefault();
      const url = e.dataTransfer?.getData('text/uri-list') || e.dataTransfer?.getData('text/plain') || '';
      if (/^https?:\/\//.test(url)) {
        setPasteUrl(url);
        handleGrab(url);
      }
    };
    const onDragOver = e => e.preventDefault();
    document.addEventListener('drop', onDrop);
    document.addEventListener('dragover', onDragOver);

    return () => {
      unsubs.forEach(fn => typeof fn === 'function' && fn());
      document.removeEventListener('paste', onPaste);
      document.removeEventListener('drop', onDrop);
      document.removeEventListener('dragover', onDragOver);
    };
  }, []);

  // ── When a completed download comes in, refresh library ────
  React.useEffect(() => {
    const justCompleted = downloads.filter(d => d.state === 'completed' || d.status === 'completed');
    if (justCompleted.length > 0) {
      API.listCompleted().then(setCompleted).catch(console.warn);
      API.storageStats().then(setStorage).catch(console.warn);
    }
  }, [downloads]);

  // ── Handlers ───────────────────────────────────────────────
  const handleGrab = React.useCallback(async url => {
    if (!url) return;
    try {
      const result = await API.probeUrl(url);
      if (result.isVideo && result.formats && result.formats.length > 0) {
        setSniffer({ url, ...result });
      } else {
        const dl = await API.addDownload(url, {});
        setDownloads(prev => {
          const map = new Map(prev.map(d => [d.id, d]));
          map.set(dl.id, dl);
          return Array.from(map.values());
        });
        setNav('active');
        setPasteUrl('');
      }
    } catch (e) {
      console.warn('probe/add failed:', e);
    }
  }, []);

  const handleSnifferGrab = React.useCallback(async fmt => {
    if (!sniffer) return;
    try {
      const dl = await API.addDownload(sniffer.url, {
        format: fmt.formatId,
        title: sniffer.title,
        kind: 'video',
      });
      setDownloads(prev => {
        const map = new Map(prev.map(d => [d.id, d]));
        map.set(dl.id, dl);
        return Array.from(map.values());
      });
      setSniffer(null);
      setNav('active');
    } catch (e) {
      console.warn('sniffer grab failed:', e);
    }
  }, [sniffer]);

  const handlePause  = (id, gid) => API.pauseDownload(id, gid).then(() =>
    setDownloads(prev => prev.map(d => d.id === id ? { ...d, status: 'paused' } : d))
  ).catch(console.warn);

  const handleResume = (id, gid) => API.resumeDownload(id, gid).then(() =>
    setDownloads(prev => prev.map(d => d.id === id ? { ...d, status: 'active' } : d))
  ).catch(console.warn);

  const handleCancel = (id, gid) => API.cancelDownload(id, gid).then(() =>
    setDownloads(prev => prev.filter(d => d.id !== id))
  ).catch(console.warn);

  const handleReveal = (id) => API.revealInFolder(id).catch(console.warn);

  const handleSaveSettings = async (patch) => {
    try {
      const s = await API.updateSettings(patch);
      setSettings(s);
      setNav('active');
    } catch (e) { console.warn('save settings failed:', e); }
  };

  // ── Route to correct screen ────────────────────────────────
  const activeDownloads = downloads.filter(d =>
    d.status === 'active' || d.status === 'queued' || d.status === 'paused'
  );

  let screen;
  if (nav === 'settings') {
    screen = <SettingsPanel settings={appSettings} onSave={handleSaveSettings} onNavChange={setNav}/>;
  } else if (nav === 'done' || nav === 'video' || nav === 'music' || nav === 'docs' || nav === 'images') {
    const kindFilter = { video: 'video', music: 'music', docs: 'doc', images: 'image' }[nav];
    const items = kindFilter ? completed.filter(d => d.kind === kindFilter) : completed;
    screen = <CompletedLibrary items={items} onNavChange={setNav} onSettingsClick={() => setNav('settings')}/>;
  } else if (activeDownloads.length === 0 && nav === 'active') {
    screen = <EmptyState onGrab={handleGrab} pasteUrl={pasteUrl} onPasteChange={setPasteUrl} onSettingsClick={() => setNav('settings')}/>;
  } else {
    screen = (
      <DashboardDark
        downloads={downloads}
        completed={completed}
        nav={nav}
        onNavChange={setNav}
        totalSpeed={totalSpeed}
        speedHistory={speedHistory}
        storageStats={storageStats}
        onGrab={handleGrab}
        pasteUrl={pasteUrl}
        onPasteChange={setPasteUrl}
        onPause={handlePause}
        onResume={handleResume}
        onCancel={handleCancel}
        onReveal={handleReveal}
        onSettingsClick={() => setNav('settings')}
      />
    );
  }

  return (
    <div style={{ width: '100vw', height: '100vh', overflow: 'hidden', position: 'relative' }}>
      {screen}

      {/* Sniffer toast — fixed overlay bottom-right */}
      {sniffer && (
        <div style={{ position: 'fixed', bottom: 24, right: 24, width: 340, zIndex: 9999 }}>
          <SnifferToastLive
            data={sniffer}
            onGrab={handleSnifferGrab}
            onDismiss={() => setSniffer(null)}
          />
        </div>
      )}
    </div>
  );
}

// Mount
const _root = ReactDOM.createRoot(document.getElementById('app'));
_root.render(<App/>);
