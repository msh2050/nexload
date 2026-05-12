/**
 * NexLoad background service worker.
 *
 * - Maintains a WebSocket connection to the NexLoad desktop app
 *   at ws://127.0.0.1:9119
 * - Registers context menus:
 *     "Download link with NexLoad"   (on links)
 *     "Download video with NexLoad"  (on video elements)
 * - Forwards download requests from content.js to the app
 */

"use strict";

const WS_URL = "ws://127.0.0.1:9119";
const RECONNECT_DELAY_MS = 5000;

// ─────────────────────────────────────────── WebSocket management

let ws = null;
let wsReady = false;
let reconnectTimer = null;

function connect() {
  if (ws && ws.readyState <= WebSocket.OPEN) return;
  try {
    ws = new WebSocket(WS_URL);
  } catch (e) {
    scheduleReconnect();
    return;
  }

  ws.onopen = () => {
    wsReady = true;
    clearTimeout(reconnectTimer);
    setIcon(true);
  };

  ws.onclose = () => {
    wsReady = false;
    setIcon(false);
    scheduleReconnect();
  };

  ws.onerror = () => {
    wsReady = false;
  };

  ws.onmessage = (event) => {
    try {
      const msg = JSON.parse(event.data);
      handleServerMessage(msg);
    } catch (_) {}
  };
}

function scheduleReconnect() {
  clearTimeout(reconnectTimer);
  reconnectTimer = setTimeout(connect, RECONNECT_DELAY_MS);
}

function sendToApp(obj) {
  if (wsReady && ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify(obj));
    return true;
  }
  // queue not implemented — just open NexLoad first
  return false;
}

// ─────────────────────────────────────────── icon / badge

function setIcon(connected) {
  chrome.action.setTitle({
    title: connected ? "NexLoad (connected)" : "NexLoad (not connected — open the app)",
  });
  chrome.action.setBadgeText({ text: connected ? "" : "OFF" });
  chrome.action.setBadgeBackgroundColor({ color: connected ? "#1e7e34" : "#c0392b" });
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
  connect();
});

chrome.runtime.onStartup.addListener(() => {
  connect();
});

// ─────────────────────────────────────────── context menu click handler

chrome.contextMenus.onClicked.addListener((info, tab) => {
  const referrer = info.pageUrl || "";

  if (info.menuItemId === "nexload_download_link") {
    const url = info.linkUrl;
    if (!url) return;
    const filename = url.split("/").pop().split("?")[0] || "download";
    sendOrAlert(tab, {
      action: "download",
      url,
      filename,
      referrer,
    });
  } else if (info.menuItemId === "nexload_download_video") {
    // ask content script for the actual video src
    chrome.tabs.sendMessage(
      tab.id,
      { action: "get_link" },
      (resp) => {
        const url = info.srcUrl || (resp && resp.href) || info.pageUrl;
        sendOrAlert(tab, {
          action: "download_video",
          url,
          referrer,
          title: tab.title || "",
        });
      }
    );
  } else if (info.menuItemId === "nexload_download_selection") {
    const url = info.selectionText && info.selectionText.trim();
    if (!url || !url.startsWith("http")) return;
    sendOrAlert(tab, {
      action: "download",
      url,
      filename: url.split("/").pop().split("?")[0] || "download",
      referrer,
    });
  }
});

function sendOrAlert(tab, msg) {
  if (!sendToApp(msg)) {
    chrome.scripting.executeScript({
      target: { tabId: tab.id },
      func: () =>
        alert(
          "NexLoad is not running.\nPlease start NexLoad and try again."
        ),
    });
  }
}

// ─────────────────────────────────────────── messages from content.js

chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg.action === "download" || msg.action === "download_video") {
    const payload = {
      action: msg.action,
      url: msg.url,
      referrer: msg.referrer || sender.url || "",
      title: msg.title || "",
      filename: msg.filename || "",
    };
    if (!sendToApp(payload)) {
      // NexLoad not running — open app install page or show badge
      chrome.action.setBadgeText({ text: "!" });
      chrome.action.setBadgeBackgroundColor({ color: "#e67e22" });
    }
  }
  // no response needed
});

// ─────────────────────────────────────────── server messages

function handleServerMessage(msg) {
  // future: server could ask extension to grab cookies etc.
  if (msg.action === "ping") {
    sendToApp({ action: "pong" });
  }
}

// ─────────────────────────────────────────── keep-alive

setIcon(false);
connect();

// reconnect if the service worker wakes up
chrome.alarms.create("nexload_keepalive", { periodInMinutes: 0.5 });
chrome.alarms.onAlarm.addListener((alarm) => {
  if (alarm.name === "nexload_keepalive") {
    connect();
  }
});
