use serde::{Deserialize, Serialize};
use std::path::Path;

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct Settings {
    pub download_dir: String,
    pub concurrent_downloads: u32,
    pub connections_per_file: u32,
    /// 0 = unlimited
    pub max_speed_kbps: u32,
    pub auto_detect_videos: bool,
    pub pause_on_metered: bool,
    pub resume_on_launch: bool,
    pub verify_checksums: bool,
}

impl Default for Settings {
    fn default() -> Self {
        let dir = dirs::download_dir()
            .map(|p| p.to_string_lossy().to_string())
            .unwrap_or_else(|| "~/Downloads".into());
        Self {
            download_dir: dir,
            concurrent_downloads: 5,
            connections_per_file: 8,
            max_speed_kbps: 0,
            auto_detect_videos: true,
            pause_on_metered: true,
            resume_on_launch: false,
            verify_checksums: true,
        }
    }
}

impl Settings {
    pub fn load(data_dir: &Path) -> Option<Self> {
        let text = std::fs::read_to_string(data_dir.join("settings.json")).ok()?;
        serde_json::from_str(&text).ok()
    }

    pub fn save(&self, data_dir: &Path) -> std::io::Result<()> {
        std::fs::write(
            data_dir.join("settings.json"),
            serde_json::to_string_pretty(self).unwrap(),
        )
    }
}
