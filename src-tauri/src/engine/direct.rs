/// aria2c JSON-RPC wrapper.
/// Starts aria2c as a subprocess with --enable-rpc; communicates via reqwest.
use reqwest::Client;
use serde::Deserialize;
use serde_json::{json, Value};
use std::sync::Mutex;
use tauri::Manager;

const PORT: u16 = 6824;

pub struct Aria2Client {
    pub secret: String,
    http: Client,
    url: String,
    child: Mutex<Option<std::process::Child>>,
}

impl Aria2Client {
    pub fn new() -> Self {
        let secret = format!("{:016x}", rand::random::<u64>());
        Self {
            url: format!("http://127.0.0.1:{}/jsonrpc", PORT),
            secret,
            http: Client::new(),
            child: Mutex::new(None),
        }
    }

    async fn call(&self, method: &str, params: Value) -> Result<Value, String> {
        let body = json!({
            "jsonrpc": "2.0",
            "id": "nx",
            "method": method,
            "params": params,
        });
        let resp = self
            .http
            .post(&self.url)
            .json(&body)
            .send()
            .await
            .map_err(|e| e.to_string())?;
        let v: Value = resp.json().await.map_err(|e| e.to_string())?;
        if let Some(e) = v.get("error") {
            return Err(e.to_string());
        }
        Ok(v["result"].clone())
    }

    fn tok(&self) -> String {
        format!("token:{}", self.secret)
    }

    pub async fn add_uri(
        &self,
        url: &str,
        filename: &str,
        dest: &str,
        conns: u32,
        max_speed_kbps: u32,
    ) -> Result<String, String> {
        let mut opts = json!({
            "dir": dest,
            "out": filename,
            "split": conns.to_string(),
            "max-connection-per-server": conns.to_string(),
            "continue": "true",
        });
        if max_speed_kbps > 0 {
            opts["max-download-limit"] = json!(format!("{}K", max_speed_kbps));
        }
        let gid = self
            .call("aria2.addUri", json!([self.tok(), [url], opts]))
            .await?;
        Ok(gid.as_str().unwrap_or("").to_string())
    }

    pub async fn pause(&self, gid: &str) -> Result<(), String> {
        self.call("aria2.pause", json!([self.tok(), gid])).await?;
        Ok(())
    }

    pub async fn resume(&self, gid: &str) -> Result<(), String> {
        self.call("aria2.unpause", json!([self.tok(), gid])).await?;
        Ok(())
    }

    pub async fn remove(&self, gid: &str) -> Result<(), String> {
        self.call("aria2.forceRemove", json!([self.tok(), gid]))
            .await?;
        Ok(())
    }

    pub async fn tell_active(&self) -> Result<Vec<Aria2Status>, String> {
        let keys = json!(FIELDS);
        let v = self
            .call("aria2.tellActive", json!([self.tok(), keys]))
            .await?;
        serde_json::from_value(v).map_err(|e| e.to_string())
    }

    pub async fn tell_waiting(&self, offset: i32, num: u32) -> Result<Vec<Aria2Status>, String> {
        let keys = json!(FIELDS);
        let v = self
            .call("aria2.tellWaiting", json!([self.tok(), offset, num, keys]))
            .await?;
        serde_json::from_value(v).map_err(|e| e.to_string())
    }

    pub async fn tell_stopped(&self, offset: i32, num: u32) -> Result<Vec<Aria2Status>, String> {
        let keys = json!(FIELDS);
        let v = self
            .call("aria2.tellStopped", json!([self.tok(), offset, num, keys]))
            .await?;
        serde_json::from_value(v).map_err(|e| e.to_string())
    }

    pub async fn global_stat(&self) -> Result<GlobalStat, String> {
        let v = self
            .call("aria2.getGlobalStat", json!([self.tok()]))
            .await?;
        serde_json::from_value(v).map_err(|e| e.to_string())
    }

    pub fn kill(&self) {
        if let Ok(mut guard) = self.child.lock() {
            if let Some(mut c) = guard.take() {
                c.kill().ok();
            }
        }
    }
}

const FIELDS: &[&str] = &[
    "gid",
    "status",
    "totalLength",
    "completedLength",
    "downloadSpeed",
    "connections",
    "files",
    "errorCode",
    "errorMessage",
];

#[derive(Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct Aria2Status {
    pub gid: String,
    pub status: String,
    pub total_length: String,
    pub completed_length: String,
    pub download_speed: String,
    #[serde(default)]
    pub connections: String,
    #[serde(default)]
    pub files: Vec<Aria2File>,
    pub error_code: Option<String>,
    pub error_message: Option<String>,
}

#[derive(Debug, Deserialize, Default)]
pub struct Aria2File {
    pub path: String,
}

#[derive(Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct GlobalStat {
    pub download_speed: String,
    pub num_active: String,
    pub num_waiting: String,
    pub num_stopped: String,
}

/// Find aria2c: sidecar bundle first, then system PATH.
fn aria2c_path(app: &tauri::AppHandle) -> std::path::PathBuf {
    // Tauri sidecar convention: binaries/{name}-{target_triple}
    let triple = std::env::consts::ARCH.to_string() + "-unknown-linux-gnu";
    if let Ok(res) = app.path().resource_dir() {
        let p = res.join("binaries").join(format!("aria2c-{}", triple));
        if p.exists() {
            return p;
        }
        // Windows
        let p2 = res
            .join("binaries")
            .join(format!("aria2c-{}-pc-windows-msvc.exe", std::env::consts::ARCH));
        if p2.exists() {
            return p2;
        }
    }
    std::path::PathBuf::from("aria2c")
}

pub async fn start_aria2(
    app: &tauri::AppHandle,
    client: std::sync::Arc<Aria2Client>,
    download_dir: &str,
) {
    let bin = aria2c_path(app);
    let session = std::env::temp_dir().join("nexload-aria2.session");

    let mut args = vec![
        "--enable-rpc".to_string(),
        format!("--rpc-listen-port={}", PORT),
        format!("--rpc-secret={}", client.secret),
        "--rpc-listen-all=false".to_string(),
        "--show-console-readout=false".to_string(),
        "--quiet=true".to_string(),
        "--continue=true".to_string(),
        "--max-tries=0".to_string(),
        format!("--dir={}", download_dir),
        format!("--save-session={}", session.display()),
        "--save-session-interval=30".to_string(),
    ];
    if session.exists() {
        args.push(format!("--input-file={}", session.display()));
    }

    match std::process::Command::new(&bin).args(&args).spawn() {
        Ok(child) => {
            *client.child.lock().unwrap() = Some(child);
            log::info!("aria2c started on port {}", PORT);
            // Give it a moment to bind
            tokio::time::sleep(std::time::Duration::from_millis(800)).await;
        }
        Err(e) => {
            log::warn!("aria2c launch failed ({}): {}. Direct downloads unavailable.", bin.display(), e);
        }
    }
}
