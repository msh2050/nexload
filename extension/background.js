"use strict";

const SERVER_URL = "http://127.0.0.1:9119";

// ─────────────────────────────────────────── icon / badge

function setIcon(connected) {
  chrome.action.setTitle({
    title: connected ? "NexLoad (connected)" : "NexLoad (not connected — open the app)",
  });
  chrome.action.setBadgeText({ text: connected ? "" : "OFF" });
  chrome.action.setBadgeBackgroundColor({ color: connected ? "#1e7e34" : "#c0392b" });
}

// ─────────────────────────────────────────── HTTP communication

async function pingServer() {
  try {
    const r = await fetch(`${SERVER_URL}/ping`, { method: "GET" });
    if (r.ok) { setIcon(true); return true; }
  } catch (_) {}
  setIcon(false);
  return false;
}

async function sendToApp(obj) {
  try {
    const r = await fetch(SERVER_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(obj),
    });
    if (r.ok) { setIcon(true); return true; }
  } catch (_) {}
  setIcon(false);
  return false;
}

// ─────────────────────────────────────────── video URL capture (like IDM / DownloadHelper)

// tabId → [{url, type, size, ts}]
const capturedVideos = new Map();

// Match video/audio MIME types and playlist types
const VIDEO_MIME_RE = /^(video|audio)\/|application\/(x-mpegurl|vnd\.apple\.mpegurl|dash\+xml)/i;
// Match video file extensions in the URL
const VIDEO_EXT_RE  = /\.(mp4|webm|mkv|m3u8|mpd|flv|avi|mov|m4v|m4a|mp3|ogg|opus)(\?|#|$)/i;
// Skip tiny HLS/DASH segment files — we want the playlist, not chunks
const SKIP_EXT_RE   = /\.(ts|m4s|cmfa|cmfv)(\?|#|$)/i;

chrome.webRequest.onResponseStarted.addListener(
  (details) => {
    if (details.tabId < 0) return;
    const url = details.url;
    if (SKIP_EXT_RE.test(url)) return;

    const hdrs = details.responseHeaders || [];
    const ct = (hdrs.find(h => h.name.toLowerCase() === "content-type") || {}).value || "";
    const cl = parseInt((hdrs.find(h => h.name.toLowerCase() === "content-length") || {}).value || "0");

    if (!VIDEO_MIME_RE.test(ct) && !VIDEO_EXT_RE.test(url)) return;

    const list = capturedVideos.get(details.tabId) || [];
    if (!list.find(v => v.url === url)) {
      list.push({ url, type: ct, size: cl, ts: Date.now() });
      if (list.length > 30) list.splice(0, list.length - 30);
    }
    capturedVideos.set(details.tabId, list);
  },
  { urls: ["<all_urls>"], types: ["media", "xmlhttprequest", "other"] },
  ["responseHeaders"]
);

// Clear captured URLs when tab navigates or closes
chrome.tabs.onRemoved.addListener(tabId => capturedVideos.delete(tabId));
chrome.tabs.onUpdated.addListener((tabId, info) => {
  if (info.status === "loading") capturedVideos.delete(tabId);
});

function getBestCapturedUrl(tabId) {
  const list = capturedVideos.get(tabId) || [];
  if (!list.length) return null;
  // Prefer M3U8 playlists (HLS master/index), then largest MP4, then most recent
  const m3u8 = list.filter(v => /m3u8/i.test(v.url) || /mpegurl/i.test(v.type));
  if (m3u8.length) return m3u8[m3u8.length - 1].url;
  const sorted = [...list].sort((a, b) => (b.size || 0) - (a.size || 0));
  return sorted[0].url;
}

// ─────────────────────────────────────────── URL resolution

const KNOWN_VIDEO_HOSTS = [
  "youtube.com", "youtu.be", "dailymotion.com", "vimeo.com",
  "twitch.tv", "tiktok.com", "twitter.com", "x.com",
  "facebook.com", "instagram.com", "reddit.com",
];

function resolveVideoUrl(msg, sender) {
  if (msg.action !== "download_video") return msg.url;

  const tabId = sender.tab?.id;
  const tabUrl = sender.tab?.url || "";
  const frameUrl = sender.url || "";

  // 1. Best: use a URL we actually saw the browser request (like IDM does)
  if (tabId != null) {
    const captured = getBestCapturedUrl(tabId);
    if (captured) return captured;
  }

  // 2. For known platforms (YouTube, Dailymotion…) yt-dlp needs the page URL
  if (frameUrl && frameUrl !== tabUrl) {
    try {
      const tabHost = new URL(tabUrl).hostname;
      if (KNOWN_VIDEO_HOSTS.some(h => tabHost === h || tabHost.endsWith("." + h))) {
        return tabUrl;
      }
    } catch (_) {}
    // Unknown aggregator site: use the embed/player iframe URL
    return frameUrl;
  }

  return tabUrl || msg.url;
}

// ─────────────────────────────────────────── context menus

chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.removeAll(() => {
    chrome.contextMenus.create({
      id: "nexload_download_link",
      title: "⬇ Download link with NexLoad",
      contexts: ["link"],
    });
    chrome.contextMenus.create({
      id: "nexload_download_video",
      title: "⬇ Download video with NexLoad",
      contexts: ["video", "audio"],
    });
    chrome.contextMenus.create({
      id: "nexload_download_selection",
      title: "⬇ Download with NexLoad",
      contexts: ["selection"],
    });
  });
});

// ─────────────────────────────────────────── context menu handler

chrome.contextMenus.onClicked.addListener((info, tab) => {
  const referrer = info.pageUrl || "";

  if (info.menuItemId === "nexload_download_link") {
    const url = info.linkUrl;
    if (!url) return;
    sendOrAlert(tab, {
      action: "download",
      url,
      filename: url.split("/").pop().split("?")[0] || "download",
      referrer,
    });

  } else if (info.menuItemId === "nexload_download_video") {
    // Try captured network URLs first; fall back to frame/tab URL
    const captured = getBestCapturedUrl(tab.id);
    const frameUrl = info.pageUrl || tab.url;
    const tabHost = (() => { try { return new URL(tab.url).hostname; } catch (_) { return ""; } })();
    const useTabUrl = KNOWN_VIDEO_HOSTS.some(h => tabHost === h || tabHost.endsWith("." + h));
    sendOrAlert(tab, {
      action: "download_video",
      url: captured || (useTabUrl ? tab.url : frameUrl),
      referrer,
      title: tab.title || "",
    });

  } else if (info.menuItemId === "nexload_download_selection") {
    const url = (info.selectionText || "").trim();
    if (!url.startsWith("http")) return;
    sendOrAlert(tab, {
      action: "download",
      url,
      filename: url.split("/").pop().split("?")[0] || "download",
      referrer,
    });
  }
});

async function sendOrAlert(tab, msg) {
  const ok = await sendToApp(msg);
  if (!ok) {
    chrome.scripting.executeScript({
      target: { tabId: tab.id },
      func: () => alert("NexLoad is not running.\nPlease start NexLoad and try again."),
    });
  }
}

// ─────────────────────────────────────────── messages from content.js

chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg.action === "download" || msg.action === "download_video") {
    const url = resolveVideoUrl(msg, sender);
    const payload = {
      action: msg.action,
      url,
      referrer: msg.referrer || sender.url || "",
      title: msg.title || sender.tab?.title || "",
      filename: msg.filename || "",
    };
    sendToApp(payload).then((ok) => {
      if (!ok && sender.tab) sendOrAlert(sender.tab, payload);
    });
  }
});

// ─────────────────────────────────────────── keepalive

setIcon(false);
pingServer();

chrome.alarms.create("nexload_keepalive", { periodInMinutes: 0.5 });
chrome.alarms.onAlarm.addListener((alarm) => {
  if (alarm.name === "nexload_keepalive") pingServer();
});
