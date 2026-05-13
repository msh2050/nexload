/// yt-dlp wrapper: metadata probe and download.
use serde::{Deserialize, Serialize};
use std::process::Stdio;
use tauri::Manager;
use tokio::io::{AsyncBufReadExt, BufReader};

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct FormatInfo {
    pub label: String,
    pub format_id: String,
    pub size_mb: Option<f64>,
    pub ext: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct ProbeResult {
    pub title: String,
    pub duration: Option<u64>,
    pub thumbnail: Option<String>,
    pub host: String,
    pub is_video: bool,
    pub formats: Vec<FormatInfo>,
    /// true when the URL is a plain file download
    pub direct: bool,
}

#[derive(Debug, Deserialize)]
struct YtFormat {
    format_id: String,
    ext: String,
    #[serde(default)]
    height: Option<u32>,
    #[serde(default)]
    filesize: Option<u64>,
    #[serde(default)]
    filesize_approx: Option<u64>,
    #[serde(default)]
    vcodec: String,
    #[serde(default)]
    acodec: String,
}

#[derive(Debug, Deserialize)]
struct YtMeta {
    title: String,
    #[serde(default)]
    duration: Option<u64>,
    #[serde(default)]
    thumbnail: Option<String>,
    #[serde(default)]
    webpage_url_domain: Option<String>,
    #[serde(default)]
    formats: Vec<YtFormat>,
}

fn ytdlp_path(app: &tauri::AppHandle) -> std::path::PathBuf {
    let triple = std::env::consts::ARCH.to_string() + "-unknown-linux-gnu";
    if let Ok(res) = app.path().resource_dir() {
        let p = res.join("binaries").join(format!("yt-dlp-{}", triple));
        if p.exists() {
            return p;
        }
        let p2 = res
            .join("binaries")
            .join(format!("yt-dlp-{}-pc-windows-msvc.exe", std::env::consts::ARCH));
        if p2.exists() {
            return p2;
        }
    }
    std::path::PathBuf::from("yt-dlp")
}

pub async fn probe(app: &tauri::AppHandle, url: &str) -> Result<ProbeResult, String> {
    // Sanitise URL
    if !url.starts_with("http://") && !url.starts_with("https://") {
        return Err("Only http/https URLs are supported".into());
    }

    let bin = ytdlp_path(app);
    let out = tokio::process::Command::new(&bin)
        .args([
            "-J",
            "--no-playlist",
            "--user-agent",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            url,
        ])
        .output()
        .await
        .map_err(|e| format!("yt-dlp not found: {}", e))?;

    if !out.status.success() {
        return Err(String::from_utf8_lossy(&out.stderr).to_string());
    }

    let meta: YtMeta =
        serde_json::from_slice(&out.stdout).map_err(|e| format!("parse: {}", e))?;

    let host = meta
        .webpage_url_domain
        .clone()
        .unwrap_or_else(|| url_host(url));

    let formats = build_formats(&meta.formats);
    let is_video = !formats.is_empty();

    Ok(ProbeResult {
        title: meta.title,
        duration: meta.duration,
        thumbnail: meta.thumbnail,
        host,
        is_video,
        formats,
        direct: false,
    })
}

fn build_formats(raw: &[YtFormat]) -> Vec<FormatInfo> {
    // Group into quality buckets: 4K, 1080p, 720p, 480p, audio-only (MP3)
    let buckets: &[(&str, Option<u32>, Option<u32>)] = &[
        ("4K", Some(2160), Some(3000)),
        ("1080p", Some(1080), Some(2159)),
        ("720p", Some(720), Some(1079)),
        ("480p", Some(480), Some(719)),
    ];

    let mut result: Vec<FormatInfo> = buckets
        .iter()
        .filter_map(|(label, min_h, max_h)| {
            // Find the best format in this bucket
            let best = raw.iter().filter(|f| {
                let has_video = f.vcodec != "none" && !f.vcodec.is_empty();
                let h = f.height.unwrap_or(0);
                has_video
                    && min_h.map(|m| h >= m).unwrap_or(true)
                    && max_h.map(|m| h <= m).unwrap_or(true)
            }).max_by_key(|f| f.height.unwrap_or(0));
            best.map(|f| FormatInfo {
                label: label.to_string(),
                format_id: format!("bestvideo[height<={}]+bestaudio/best[height<={}]",
                    f.height.unwrap_or(1080), f.height.unwrap_or(1080)),
                size_mb: f.filesize.or(f.filesize_approx).map(|s| s as f64 / 1e6),
                ext: f.ext.clone(),
            })
        })
        .collect();

    // Audio-only bucket
    if let Some(audio) = raw.iter().find(|f| f.vcodec == "none" && f.acodec != "none") {
        result.push(FormatInfo {
            label: "MP3".to_string(),
            format_id: "bestaudio/best".to_string(),
            size_mb: audio.filesize.or(audio.filesize_approx).map(|s| s as f64 / 1e6),
            ext: "mp3".to_string(),
        });
    }

    result
}

/// Progress line emitted by yt-dlp --newline
#[derive(Debug, Serialize, Clone)]
pub struct YtProgress {
    pub downloaded_bytes: u64,
    pub total_bytes: u64,
    pub speed: f64,
    pub eta: u64,
    pub status: String,
}

pub async fn download<F>(
    app: &tauri::AppHandle,
    url: &str,
    format_id: &str,
    dest_dir: &str,
    title: &str,
    mut on_progress: F,
) -> Result<String, String>
where
    F: FnMut(YtProgress) + Send + 'static,
{
    if !url.starts_with("http://") && !url.starts_with("https://") {
        return Err("Only http/https URLs are supported".into());
    }

    let safe_title: String = title
        .chars()
        .map(|c| if c.is_alphanumeric() || " ._-()".contains(c) { c } else { '_' })
        .collect::<String>()
        .trim()
        .chars()
        .take(120)
        .collect();

    let out_tmpl = format!("{}/{}.%(ext)s", dest_dir, safe_title);
    let bin = ytdlp_path(app);

    let mut child = tokio::process::Command::new(&bin)
        .args([
            "-f", format_id,
            "-o", &out_tmpl,
            "--newline",
            "--progress-template",
            "%(progress.status)s %(progress.downloaded_bytes)s %(progress.total_bytes)s %(progress.speed)s %(progress.eta)s",
            "--no-playlist",
            "--user-agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            url,
        ])
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .map_err(|e| e.to_string())?;

    let stdout = child.stdout.take().unwrap();
    let mut lines = BufReader::new(stdout).lines();
    let mut last_path = String::new();

    while let Ok(Some(line)) = lines.next_line().await {
        let parts: Vec<&str> = line.split_whitespace().collect();
        if parts.len() >= 5 {
            let prog = YtProgress {
                status: parts[0].to_string(),
                downloaded_bytes: parts[1].parse().unwrap_or(0),
                total_bytes: parts[2].parse().unwrap_or(0),
                speed: parts[3].parse().unwrap_or(0.0),
                eta: parts[4].parse().unwrap_or(0),
            };
            if prog.status == "finished" {
                // Extract actual output filename from yt-dlp stderr
            }
            on_progress(prog);
        }
    }

    let status = child.wait().await.map_err(|e| e.to_string())?;
    if !status.success() {
        return Err("yt-dlp exited with error".into());
    }

    // Find the downloaded file
    let ext_candidates = ["mp4", "mkv", "webm", "mp3", "m4a", "opus"];
    for ext in &ext_candidates {
        let p = format!("{}/{}.{}", dest_dir, safe_title, ext);
        if std::path::Path::new(&p).exists() {
            return Ok(p);
        }
    }
    Ok(format!("{}/{}", dest_dir, safe_title))
}

fn url_host(url: &str) -> String {
    url.split('/').nth(2).unwrap_or("").to_string()
}
