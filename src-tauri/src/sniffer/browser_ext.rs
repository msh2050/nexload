/// Native-messaging host manifest installer.
/// Call `install_nm_manifests()` on first launch to register the host with
/// Chrome and Firefox, so the bundled WebExtension can talk to Nexload.

use std::path::PathBuf;

const HOST_NAME: &str = "com.nexload.sniffer";
const NM_BIN_DESCRIPTION: &str = "Nexload native messaging host";

/// Write native-messaging manifests for Chrome and Firefox.
pub fn install_nm_manifests(host_binary: &str) -> std::io::Result<()> {
    let manifest = serde_json::json!({
        "name": HOST_NAME,
        "description": NM_BIN_DESCRIPTION,
        "path": host_binary,
        "type": "stdio",
        "allowed_origins": [
            "chrome-extension://nexload-sniffer-id/"
        ]
    });
    let ff_manifest = serde_json::json!({
        "name": HOST_NAME,
        "description": NM_BIN_DESCRIPTION,
        "path": host_binary,
        "type": "stdio",
        "allowed_extensions": ["sniffer@nexload.app"]
    });

    for dir in chrome_nm_dirs() {
        std::fs::create_dir_all(&dir)?;
        let path = dir.join(format!("{}.json", HOST_NAME));
        std::fs::write(&path, serde_json::to_string_pretty(&manifest).unwrap())?;
        log::info!("wrote Chrome NM manifest: {}", path.display());
    }

    for dir in firefox_nm_dirs() {
        std::fs::create_dir_all(&dir)?;
        let path = dir.join(format!("{}.json", HOST_NAME));
        std::fs::write(&path, serde_json::to_string_pretty(&ff_manifest).unwrap())?;
        log::info!("wrote Firefox NM manifest: {}", path.display());
    }

    Ok(())
}

fn chrome_nm_dirs() -> Vec<PathBuf> {
    let mut dirs = vec![];
    #[cfg(target_os = "linux")]
    {
        if let Some(home) = dirs_macro() {
            dirs.push(home.join(".config/google-chrome/NativeMessagingHosts"));
            dirs.push(home.join(".config/chromium/NativeMessagingHosts"));
        }
    }
    #[cfg(target_os = "macos")]
    {
        if let Some(home) = dirs_macro() {
            dirs.push(home.join("Library/Application Support/Google/Chrome/NativeMessagingHosts"));
        }
    }
    #[cfg(target_os = "windows")]
    {} // Windows uses registry keys; out of scope here
    dirs
}

fn firefox_nm_dirs() -> Vec<PathBuf> {
    let mut dirs = vec![];
    #[cfg(target_os = "linux")]
    {
        if let Some(home) = dirs_macro() {
            dirs.push(home.join(".mozilla/native-messaging-hosts"));
        }
    }
    #[cfg(target_os = "macos")]
    {
        if let Some(home) = dirs_macro() {
            dirs.push(home.join("Library/Application Support/Mozilla/NativeMessagingHosts"));
        }
    }
    dirs
}

fn dirs_macro() -> Option<PathBuf> {
    dirs::home_dir()
}

/// Native-messaging host binary: reads a 4-byte length-prefixed JSON message
/// from stdin, connects to the Nexload Unix socket, and forwards it.
/// This is compiled as a separate tiny binary in a real deployment; here we
/// describe the protocol so the extension builder can implement it.
///
/// Message format (Chrome NM): [u32 LE length][JSON bytes]
/// We forward the JSON line to the Nexload socket.
pub fn nm_host_forward(msg: &[u8]) -> std::io::Result<()> {
    use std::io::Write;
    use std::os::unix::net::UnixStream;

    let socket_path = super::socket_path();
    let mut stream = UnixStream::connect(&socket_path)?;
    stream.write_all(msg)?;
    stream.write_all(b"\n")?;
    Ok(())
}
