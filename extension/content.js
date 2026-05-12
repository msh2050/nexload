/**
 * NexLoad content script.
 *
 * Responsibilities:
 *  1. Detect <video> elements on any page
 *  2. Inject a floating "⬇ Download with NexLoad" button above each video
 *  3. Keep the button positioned correctly as the page scrolls/resizes
 *  4. On button click: resolve the best video URL and send to background.js
 *  5. Pass right-click download-link selection to background.js
 */

(function () {
  "use strict";
  if (window.__nexload_injected__) return;
  window.__nexload_injected__ = true;

  // ─────────────────────────────────────────── constants

  const BTN_ID_PREFIX = "__nexload_btn_";
  const BTN_Z = "2147483640";
  const BTN_CSS = `
    .nexload-btn {
      position: fixed;
      z-index: ${BTN_Z};
      background: rgba(20,20,20,0.88);
      color: #fff;
      border: none;
      border-radius: 6px;
      padding: 5px 12px;
      font-size: 13px;
      font-family: sans-serif;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 6px;
      box-shadow: 0 2px 8px rgba(0,0,0,.5);
      transition: background 0.15s;
      white-space: nowrap;
      pointer-events: auto;
      user-select: none;
    }
    .nexload-btn:hover { background: rgba(0,120,215,0.92); }
    .nexload-btn svg { flex-shrink: 0; }
  `;

  // ─────────────────────────────────────────── style injection

  const style = document.createElement("style");
  style.textContent = BTN_CSS;
  (document.head || document.documentElement).appendChild(style);

  // ─────────────────────────────────────────── state

  const tracked = new Map(); // video element → { btn, rafId }

  // ─────────────────────────────────────────── helpers

  function makeButton(video) {
    const btn = document.createElement("button");
    btn.className = "nexload-btn";
    btn.innerHTML =
      `<svg width="14" height="14" viewBox="0 0 16 16" fill="currentColor">
        <path d="M8 12l-5-5h3V2h4v5h3z"/>
        <rect x="2" y="13" width="12" height="2" rx="1"/>
       </svg>Download with NexLoad`;
    btn.title = "Download this video with NexLoad";
    btn.addEventListener("click", (e) => {
      e.stopPropagation();
      e.preventDefault();
      downloadVideo(video);
    });
    document.documentElement.appendChild(btn);
    return btn;
  }

  function positionButton(video, btn) {
    const rect = video.getBoundingClientRect();
    if (
      rect.width < 80 ||
      rect.height < 50 ||
      rect.bottom < 0 ||
      rect.top > window.innerHeight
    ) {
      btn.style.display = "none";
      return;
    }

    const MARGIN = 8;
    const top = Math.max(rect.top + MARGIN, MARGIN);
    const left = Math.max(rect.left + MARGIN, MARGIN);

    btn.style.display = "flex";
    btn.style.top = `${top}px`;
    btn.style.left = `${left}px`;
  }

  function trackVideo(video) {
    if (tracked.has(video)) return;
    const btn = makeButton(video);

    function loop() {
      if (!document.contains(video)) {
        btn.remove();
        tracked.delete(video);
        return;
      }
      positionButton(video, btn);
      const id = requestAnimationFrame(loop);
      tracked.get(video).rafId = id;
    }

    const entry = { btn, rafId: null };
    tracked.set(video, entry);
    entry.rafId = requestAnimationFrame(loop);
  }

  function scanForVideos() {
    document.querySelectorAll("video").forEach((v) => {
      // skip tiny/hidden videos (thumbnails, ads etc.)
      if (v.offsetWidth >= 200 && v.offsetHeight >= 120) {
        trackVideo(v);
      }
    });
  }

  // ─────────────────────────────────────────── video URL resolution

  function resolveVideoUrl(video) {
    // 1. src attribute
    if (video.src && !video.src.startsWith("blob:")) return video.src;

    // 2. <source> children
    for (const src of video.querySelectorAll("source")) {
      if (src.src && !src.src.startsWith("blob:")) return src.src;
    }

    // 3. current page URL (the page IS the video e.g. YouTube)
    return window.location.href;
  }

  function downloadVideo(video) {
    const url = resolveVideoUrl(video);
    const referrer = window.location.href;
    const title = document.title || "";

    chrome.runtime.sendMessage({
      action: "download_video",
      url,
      referrer,
      title,
    });
  }

  // ─────────────────────────────────────────── observe DOM

  const observer = new MutationObserver(() => scanForVideos());
  observer.observe(document.documentElement, {
    childList: true,
    subtree: true,
  });

  // initial scan + re-scan after full page load
  scanForVideos();
  window.addEventListener("load", scanForVideos);

  // re-scan after SPA navigations
  let lastHref = location.href;
  setInterval(() => {
    if (location.href !== lastHref) {
      lastHref = location.href;
      // give the new page a moment to render
      setTimeout(scanForVideos, 1500);
    }
  }, 500);

  // ─────────────────────────────────────────── right-click link helper

  let lastContextTarget = null;
  document.addEventListener(
    "contextmenu",
    (e) => {
      lastContextTarget = e.target;
    },
    true
  );

  // background.js will ask for the last right-clicked element's href
  chrome.runtime.onMessage.addListener((msg, _sender, sendResponse) => {
    if (msg.action === "get_link") {
      const el = lastContextTarget;
      const anchor = el && el.closest("a[href]");
      sendResponse({
        href: anchor ? anchor.href : null,
        referrer: window.location.href,
        text: anchor ? (anchor.textContent || "").trim().slice(0, 80) : "",
      });
      return true;
    }
  });
})();
