// Thin wrapper around window.__TAURI__.core.invoke so components stay testable.
// Falls back to mock data when running outside Tauri (e.g. plain browser).

const _invoke = (window.__TAURI__ && window.__TAURI__.core)
  ? (cmd, args) => window.__TAURI__.core.invoke(cmd, args)
  : (cmd, args) => Promise.resolve(_mock(cmd, args));

const _listen = (window.__TAURI__ && window.__TAURI__.event)
  ? (ev, fn) => window.__TAURI__.event.listen(ev, fn)
  : () => Promise.resolve(() => {});

function _mock(cmd, args) {
  console.debug('[API mock]', cmd, args);
  switch (cmd) {
    case 'list_active':    return [];
    case 'list_completed': return [];
    case 'get_settings':   return _defaultSettings();
    case 'update_settings': return Object.assign(_defaultSettings(), args?.patch || {});
    case 'storage_stats':  return { totalBytes: 0, freeBytes: 500*1e9, usedPct: 0.0, byKind: {} };
    case 'probe_url':
      return { title: 'Sample Video', duration: 120, thumbnail: null, host: 'example.com',
               isVideo: true, formats: [
                 { label: '1080p', formatId: 'bv[height<=1080]+ba', sizeMb: 180, ext: 'mp4' },
                 { label: '720p',  formatId: 'bv[height<=720]+ba',  sizeMb: 92,  ext: 'mp4' },
                 { label: 'MP3',   formatId: 'bestaudio',           sizeMb: 6,   ext: 'mp3' },
               ], direct: false };
    case 'add_download':
      return { id: 'mock-' + Date.now(), url: args?.url, title: args?.opts?.title || 'Download',
               kind: 'other', sizeBytes: 0, path: '', host: '',
               thumbnailB64: null, status: 'active', aria2Gid: 'mock',
               createdAt: new Date().toISOString(), completedAt: null };
    default: return null;
  }
}

function _defaultSettings() {
  return {
    downloadDir: '~/Downloads',
    concurrentDownloads: 5,
    connectionsPerFile: 8,
    maxSpeedKbps: 0,
    autoDetectVideos: true,
    pauseOnMetered: true,
    resumeOnLaunch: false,
    verifyChecksums: true,
  };
}

const API = {
  probeUrl: (url)            => _invoke('probe_url', { url }),
  addDownload: (url, opts)   => _invoke('add_download', { url, opts: opts || {} }),
  listActive:  ()            => _invoke('list_active', {}),
  listCompleted: (kind, lim) => _invoke('list_completed', { kind: kind || null, limit: lim || 100 }),
  pauseDownload: (id, gid)   => _invoke('pause_download', { id, gid }),
  resumeDownload:(id, gid)   => _invoke('resume_download', { id, gid }),
  cancelDownload:(id, gid)   => _invoke('cancel_download', { id, gid }),
  revealInFolder:(id)        => _invoke('reveal_in_folder', { id }),
  getSettings:  ()           => _invoke('get_settings', {}),
  updateSettings:(patch)     => _invoke('update_settings', { patch }),
  storageStats: ()           => _invoke('storage_stats', {}),

  // Event subscriptions — returns a Promise<unsubscribe fn>
  onDownloadUpdate: (fn) => _listen('download://update', ev => fn(ev.payload)),
  onGlobalStat:     (fn) => _listen('global://stat',    ev => fn(ev.payload)),
  onSnifferDetected:(fn) => _listen('sniffer://detected', ev => fn(ev.payload)),
};

// Make globally available (Babel-in-browser, no imports)
window.API = API;
