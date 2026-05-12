"use strict";

const dot = document.getElementById("dot");
const statusEl = document.getElementById("status");
const addBtn = document.getElementById("addBtn");
const openBtn = document.getElementById("openBtn");

// probe connection by attempting a WebSocket
function checkConnection() {
  return new Promise((resolve) => {
    const ws = new WebSocket("ws://127.0.0.1:9119");
    const timer = setTimeout(() => { ws.close(); resolve(false); }, 2000);
    ws.onopen = () => { clearTimeout(timer); ws.close(); resolve(true); };
    ws.onerror = () => { clearTimeout(timer); resolve(false); };
  });
}

checkConnection().then((connected) => {
  if (connected) {
    dot.classList.add("on");
    statusEl.textContent = "NexLoad is running and ready.";
  } else {
    statusEl.textContent = "NexLoad is not running. Start the app first.";
  }
});

addBtn.addEventListener("click", () => {
  chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
    const tab = tabs[0];
    const url = tab ? tab.url : "";
    chrome.runtime.sendMessage({
      action: "download",
      url,
      referrer: "",
      title: tab ? tab.title : "",
      filename: url.split("/").pop().split("?")[0] || "download",
    });
    window.close();
  });
});

openBtn.addEventListener("click", () => {
  // NexLoad registers a custom protocol handler `nexload:` for this
  window.open("nexload://open", "_blank");
  window.close();
});
