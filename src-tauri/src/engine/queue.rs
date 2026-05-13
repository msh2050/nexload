/// Download progress emit loop: polls aria2c every 500 ms, emits download://update event.
use crate::{engine::direct::Aria2Client, store::Db};
use chrono::Utc;
use serde::Serialize;
use std::sync::Arc;
use tauri::Emitter;
use tokio::sync::Mutex;

#[derive(Debug, Clone, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct DownloadUpdate {
    pub id: String,
    pub aria2_gid: String,
    pub value: f64,
    pub speed: f64,
    pub eta: String,
    pub state: String,
    pub got: u64,
    pub total: u64,
    pub speed_bytes: u64,
}

#[derive(Debug, Clone, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct GlobalUpdate {
    pub total_speed: u64,
    pub active_count: u32,
}

pub async fn emit_loop(
    app: tauri::AppHandle,
    aria2: Arc<Aria2Client>,
    db: Arc<Mutex<Db>>,
) {
    let mut interval = tokio::time::interval(std::time::Duration::from_millis(500));
    loop {
        interval.tick().await;

        // Fetch active + waiting from aria2
        let active = aria2.tell_active().await.unwrap_or_default();
        let waiting = aria2.tell_waiting(-1, 50).await.unwrap_or_default();

        let mut updates: Vec<DownloadUpdate> = Vec::new();
        let mut total_speed: u64 = 0;

        for status in active.iter().chain(waiting.iter()) {
            let total: u64 = status.total_length.parse().unwrap_or(0);
            let got: u64 = status.completed_length.parse().unwrap_or(0);
            let speed: u64 = status.download_speed.parse().unwrap_or(0);
            let value = if total > 0 { got as f64 / total as f64 } else { 0.0 };

            let eta = if speed > 0 && total > got {
                format_eta((total - got) / speed)
            } else {
                String::new()
            };

            total_speed += speed;

            // Look up our internal ID from the GID
            let db_guard = db.lock().await;
            let id = db_guard
                .by_gid(&status.gid)
                .ok()
                .flatten()
                .map(|r| r.id)
                .unwrap_or_else(|| status.gid.clone());
            drop(db_guard);

            // Mark completed in DB
            if status.status == "complete" {
                let path = status.files.first().map(|f| f.path.as_str()).unwrap_or("");
                let db_guard = db.lock().await;
                db_guard
                    .complete(&id, total as i64, path, &Utc::now().to_rfc3339())
                    .ok();
            }

            updates.push(DownloadUpdate {
                id,
                aria2_gid: status.gid.clone(),
                value,
                speed: speed as f64,
                eta,
                state: map_aria2_state(&status.status),
                got,
                total,
                speed_bytes: speed,
            });
        }

        if !updates.is_empty() {
            app.emit("download://update", &updates).ok();
        }

        app.emit(
            "global://stat",
            &GlobalUpdate {
                total_speed,
                active_count: active.len() as u32,
            },
        ).ok();
    }
}

fn map_aria2_state(s: &str) -> String {
    match s {
        "active" => "active",
        "waiting" | "paused" => "paused",
        "complete" => "completed",
        "error" | "removed" => "failed",
        _ => s,
    }
    .to_string()
}

fn format_eta(secs: u64) -> String {
    if secs < 60 {
        format!("{}s", secs)
    } else if secs < 3600 {
        format!("{}m {}s", secs / 60, secs % 60)
    } else {
        format!("{}h {}m", secs / 3600, (secs % 3600) / 60)
    }
}
