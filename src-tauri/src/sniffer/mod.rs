pub mod browser_ext;

use tauri::{AppHandle, Emitter};

/// Unix socket (or named pipe on Windows) that the browser extension
/// native-messaging host forwards detected video URLs to.
pub async fn start(app: AppHandle) -> Result<(), String> {
    #[cfg(unix)]
    {
        use tokio::io::{AsyncBufReadExt, BufReader};
        use tokio::net::UnixListener;

        let socket_path = socket_path();

        // Remove stale socket
        std::fs::remove_file(&socket_path).ok();

        let listener = UnixListener::bind(&socket_path).map_err(|e| e.to_string())?;
        log::info!("sniffer socket: {}", socket_path);

        loop {
            let (stream, _) = listener.accept().await.map_err(|e| e.to_string())?;
            let app2 = app.clone();
            tokio::spawn(async move {
                let mut lines = BufReader::new(stream).lines();
                while let Ok(Some(line)) = lines.next_line().await {
                    if let Ok(payload) = serde_json::from_str::<serde_json::Value>(&line) {
                        app2.emit("sniffer://detected", &payload).ok();
                    }
                }
            });
        }
    }

    #[cfg(windows)]
    {
        // Named pipe implementation for Windows
        log::warn!("sniffer not yet implemented for Windows");
        Ok(())
    }
}

pub fn socket_path() -> String {
    let runtime_dir = std::env::var("XDG_RUNTIME_DIR").unwrap_or_else(|_| "/tmp".into());
    format!("{}/nexload.sock", runtime_dir)
}
