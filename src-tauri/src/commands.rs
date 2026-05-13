use crate::{
    engine::video,
    settings::Settings,
    store::DownloadRecord,
    AppState,
};
use chrono::Utc;
use serde::{Deserialize, Serialize};
use std::{collections::HashMap, sync::Arc};
use tauri::{AppHandle, Manager, State};
use uuid::Uuid;

// ── Types ──────────────────────────────────────────────────────────────────

#[derive(Debug, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct AddOpts {
    pub title: Option<String>,
    pub format: Option<String>,
    pub dest_dir: Option<String>,
    pub kind: Option<String>,
}

#[derive(Debug, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct StorageStats {
    pub total_bytes: u64,
    pub free_bytes: u64,
    pub used_pct: f64,
    pub by_kind: HashMap<String, i64>,
}

// ── Helpers ────────────────────────────────────────────────────────────────

fn url_host(url: &str) -> String {
    url.split('/').nth(2).unwrap_or("").to_string()
}

fn kind_from_url(url: &str) -> &'static str {
    let u = url.to_lowercase();
    if u.ends_with(".mp4") || u.ends_with(".mkv") || u.ends_with(".webm") || u.contains("youtube") || u.contains("vimeo") {
        "video"
    } else if u.ends_with(".mp3") || u.ends_with(".flac") || u.ends_with(".m4a") {
        "music"
    } else if u.ends_with(".png") || u.ends_with(".jpg") || u.ends_with(".jpeg") || u.ends_with(".gif") || u.ends_with(".webp") {
        "image"
    } else if u.ends_with(".pdf") || u.ends_with(".doc") || u.ends_with(".docx") || u.ends_with(".key") || u.ends_with(".zip") {
        "doc"
    } else {
        "other"
    }
}

fn filename_from_url(url: &str) -> String {
    url.split('/')
        .last()
        .and_then(|s| s.split('?').next())
        .filter(|s| !s.is_empty())
        .unwrap_or("download")
        .to_string()
}

// ── Commands ────────────────────────────────────────────────────────────────

#[tauri::command]
pub async fn probe_url(
    app: AppHandle,
    url: String,
) -> Result<video::ProbeResult, String> {
    // Sanitise
    if !url.starts_with("http://") && !url.starts_with("https://") {
        return Err("Only http/https URLs supported".into());
    }

    match video::probe(&app, &url).await {
        Ok(r) => Ok(r),
        Err(_) => {
            // Not a video / yt-dlp doesn't know it — treat as direct download
            Ok(video::ProbeResult {
                title: filename_from_url(&url),
                duration: None,
                thumbnail: None,
                host: url_host(&url),
                is_video: false,
                formats: vec![],
                direct: true,
            })
        }
    }
}

#[tauri::command]
pub async fn add_download(
    app: AppHandle,
    state: State<'_, AppState>,
    url: String,
    opts: AddOpts,
) -> Result<DownloadRecord, String> {
    if !url.starts_with("http://") && !url.starts_with("https://") {
        return Err("Only http/https URLs supported".into());
    }

    let settings = state.settings.lock().await.clone();
    let dest = opts
        .dest_dir
        .clone()
        .unwrap_or_else(|| settings.download_dir.clone());

    let id = Uuid::new_v4().to_string();
    let title = opts.title.clone().unwrap_or_else(|| filename_from_url(&url));
    let kind = opts
        .kind
        .clone()
        .unwrap_or_else(|| kind_from_url(&url).to_string());

    let rec = DownloadRecord {
        id: id.clone(),
        url: url.clone(),
        title: title.clone(),
        kind,
        size_bytes: 0,
        path: String::new(),
        host: url_host(&url),
        thumbnail_b64: None,
        status: "queued".to_string(),
        aria2_gid: None,
        created_at: Utc::now().to_rfc3339(),
        completed_at: None,
    };

    // Insert into DB
    {
        let db = state.db.lock().await;
        db.insert(&rec).map_err(|e| e.to_string())?;
    }

    // If it's a video with a format, use yt-dlp; otherwise use aria2c
    if let Some(ref fmt) = opts.format {
        // yt-dlp download (async, doesn't block command)
        let app2 = app.clone();
        let url2 = url.clone();
        let fmt2 = fmt.clone();
        let dest2 = dest.clone();
        let title2 = title.clone();
        let id2 = id.clone();
        let db2 = Arc::clone(&state.db);
        let db3 = Arc::clone(&state.db);
        tokio::spawn(async move {
            let result = video::download(&app2, &url2, &fmt2, &dest2, &title2, move |p| {
                // Progress is emitted separately via download://update if we track it
                let _ = p;
            })
            .await;
            match result {
                Ok(path) => {
                    let db = db2.lock().await;
                    db.complete(&id2, 0, &path, &Utc::now().to_rfc3339()).ok();
                }
                Err(e) => {
                    log::error!("yt-dlp download failed: {}", e);
                    let db = db3.lock().await;
                    db.set_status(&id2, "failed").ok();
                }
            }
        });
    } else {
        // aria2c direct download
        let filename = opts
            .title
            .clone()
            .map(|t| t + &extension_for_url(&url))
            .unwrap_or_else(|| filename_from_url(&url));
        let gid = state
            .aria2
            .add_uri(&url, &filename, &dest, settings.connections_per_file, settings.max_speed_kbps)
            .await
            .map_err(|e| format!("aria2: {}", e))?;
        let db = state.db.lock().await;
        db.set_gid(&id, &gid).map_err(|e| e.to_string())?;

        return Ok(DownloadRecord {
            aria2_gid: Some(gid),
            status: "active".to_string(),
            ..rec
        });
    }

    Ok(rec)
}

#[tauri::command]
pub async fn list_active(state: State<'_, AppState>) -> Result<Vec<DownloadRecord>, String> {
    let db = state.db.lock().await;
    db.list_active().map_err(|e| e.to_string())
}

#[tauri::command]
pub async fn list_completed(
    state: State<'_, AppState>,
    kind: Option<String>,
    limit: Option<u32>,
) -> Result<Vec<DownloadRecord>, String> {
    let db = state.db.lock().await;
    db.list_completed(kind.as_deref(), limit.unwrap_or(100))
        .map_err(|e| e.to_string())
}

#[tauri::command]
pub async fn pause_download(
    state: State<'_, AppState>,
    id: String,
    gid: String,
) -> Result<(), String> {
    state.aria2.pause(&gid).await?;
    let db = state.db.lock().await;
    db.set_status(&id, "paused").map_err(|e| e.to_string())
}

#[tauri::command]
pub async fn resume_download(
    state: State<'_, AppState>,
    id: String,
    gid: String,
) -> Result<(), String> {
    state.aria2.resume(&gid).await?;
    let db = state.db.lock().await;
    db.set_status(&id, "active").map_err(|e| e.to_string())
}

#[tauri::command]
pub async fn cancel_download(
    state: State<'_, AppState>,
    id: String,
    gid: String,
) -> Result<(), String> {
    state.aria2.remove(&gid).await.ok(); // ignore if already gone
    let db = state.db.lock().await;
    db.set_status(&id, "cancelled").map_err(|e| e.to_string())
}

#[tauri::command]
pub async fn reveal_in_folder(
    app: AppHandle,
    state: State<'_, AppState>,
    id: String,
) -> Result<(), String> {
    use tauri_plugin_opener::OpenerExt;
    let db = state.db.lock().await;
    if let Ok(recs) = db.list_completed(None, 500) {
        if let Some(r) = recs.iter().find(|r| r.id == id) {
            if !r.path.is_empty() {
                let p = std::path::Path::new(&r.path);
                let dir = p.parent().unwrap_or(p);
                app.opener()
                    .open_path(dir.to_string_lossy().as_ref(), None::<&str>)
                    .map_err(|e| e.to_string())?;
            }
        }
    }
    Ok(())
}

#[tauri::command]
pub async fn get_settings(state: State<'_, AppState>) -> Result<Settings, String> {
    Ok(state.settings.lock().await.clone())
}

#[tauri::command]
pub async fn update_settings(
    app: AppHandle,
    state: State<'_, AppState>,
    patch: serde_json::Value,
) -> Result<Settings, String> {
    let mut settings = state.settings.lock().await;
    // Merge patch into current settings
    let mut current = serde_json::to_value(&*settings).unwrap();
    if let (Some(c), Some(p)) = (current.as_object_mut(), patch.as_object()) {
        for (k, v) in p {
            c.insert(k.clone(), v.clone());
        }
    }
    *settings = serde_json::from_value(current).map_err(|e| e.to_string())?;
    let data_dir = app.path().app_data_dir().map_err(|e| e.to_string())?;
    settings.save(&data_dir).map_err(|e| e.to_string())?;
    Ok(settings.clone())
}

#[tauri::command]
pub async fn storage_stats(
    _app: AppHandle,
    state: State<'_, AppState>,
) -> Result<StorageStats, String> {
    let db = state.db.lock().await;
    let (total_bytes, by_kind) = db.storage_totals().map_err(|e| e.to_string())?;

    let settings = state.settings.lock().await;
    let download_dir = std::path::Path::new(&settings.download_dir);

    // statvfs on the download dir
    let (free_bytes, disk_total) = disk_free(download_dir);
    let used_pct = if disk_total > 0 {
        (disk_total - free_bytes) as f64 / disk_total as f64
    } else {
        0.0
    };

    Ok(StorageStats {
        total_bytes: total_bytes as u64,
        free_bytes,
        used_pct,
        by_kind,
    })
}

fn disk_free(path: &std::path::Path) -> (u64, u64) {
    #[cfg(unix)]
    {
        use std::mem::MaybeUninit;
        unsafe {
            let path_c = std::ffi::CString::new(path.to_string_lossy().as_bytes()).unwrap();
            let mut stat: MaybeUninit<libc::statvfs> = MaybeUninit::uninit();
            if libc::statvfs(path_c.as_ptr(), stat.as_mut_ptr()) == 0 {
                let s = stat.assume_init();
                let free = s.f_bavail as u64 * s.f_frsize as u64;
                let total = s.f_blocks as u64 * s.f_frsize as u64;
                return (free, total);
            }
        }
    }
    (0, 0)
}

fn extension_for_url(url: &str) -> String {
    let u = url.split('?').next().unwrap_or(url);
    let ext = u.rsplit('.').next().unwrap_or("");
    if ext.len() <= 5 && ext.chars().all(|c| c.is_alphanumeric()) {
        format!(".{}", ext)
    } else {
        String::new()
    }
}
