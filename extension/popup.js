"use strict";

const dot = document.getElementById("dot");
const statusEl = document.getElementById("status");
const addBtn = document.getElementById("addBtn");
const openBtn = document.getElementById("openBtn");

async function checkConnection() {
  try {
    const r = await fetch("http://127.0.0.1:9119/ping", { method: "GET" });
    return r.ok;
  } catch (_) {
    return false;
  }
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
