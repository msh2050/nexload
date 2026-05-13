'use strict';

const HOST = 'com.nexload.sniffer';

const VIDEO_TYPES = [
  'video/mp4', 'video/webm', 'video/ogg', 'video/x-matroska',
  'application/vnd.apple.mpegurl', 'application/x-mpegurl',
  'application/dash+xml', 'audio/mpeg', 'audio/ogg', 'audio/flac',
];

const MIN_SIZE = 1024 * 1024; // ignore responses < 1 MB

chrome.webRequest.onResponseStarted.addListener(
  (details) => {
    const ct = details.responseHeaders
      ?.find(h => h.name.toLowerCase() === 'content-type')
      ?.value?.split(';')[0]
      .trim() || '';

    const cl = parseInt(
      details.responseHeaders
        ?.find(h => h.name.toLowerCase() === 'content-length')
        ?.value || '0',
      10
    );

    const isVideo = VIDEO_TYPES.some(t => ct.startsWith(t)) ||
      /\.(mp4|mkv|webm|m3u8|mpd|mp3|flac|m4a)($|\?)/i.test(details.url);

    if (!isVideo) return;
    if (cl > 0 && cl < MIN_SIZE) return; // skip tiny files (ads, thumbnails)
    if (details.url.includes('googlevideo.com/videoplayback')) return; // YouTube internal

    const payload = JSON.stringify({
      url: details.url,
      contentType: ct,
      tabId: details.tabId,
    });

    // Send to native messaging host
    try {
      const port = chrome.runtime.connectNative(HOST);
      port.postMessage({ url: details.url, contentType: ct });
      port.onDisconnect.addListener(() => {
        if (chrome.runtime.lastError) {
          console.debug('Nexload NM host not available:', chrome.runtime.lastError.message);
        }
      });
    } catch (e) {
      console.debug('Nexload sniffer: native host unavailable', e);
    }
  },
  { urls: ['<all_urls>'] },
  ['responseHeaders']
);
