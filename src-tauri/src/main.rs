#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::sync::Arc;
use tauri::Manager;
use tokio::sync::Mutex;

mod commands;
mod engine;
mod settings;
mod sniffer;
mod store;

pub struct AppState {
    pub db: Arc<Mutex<store::Db>>,
    pub settings: Arc<Mutex<settings::Settings>>,
    pub aria2: Arc<engine::direct::Aria2Client>,
}

fn main() {
    env_logger::Builder::from_env(env_logger::Env::default().default_filter_or("warn")).init();

    tauri::Builder::default()
        .plugin(tauri_plugin_opener::init())
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_notification::init())
        .setup(|app| {
            let app_handle = app.handle().clone();

            let data_dir = app.path().app_data_dir().expect("no app data dir");
            std::fs::create_dir_all(&data_dir).ok();

            let db = store::Db::open(data_dir.join("library.db")).expect("db init failed");
            let db = Arc::new(Mutex::new(db));

            let loaded = settings::Settings::load(&data_dir).unwrap_or_default();
            let download_dir = loaded.download_dir.clone();
            std::fs::create_dir_all(&download_dir).ok();
            let settings = Arc::new(Mutex::new(loaded));

            let aria2 = Arc::new(engine::direct::Aria2Client::new());

            // Start aria2c in background
            {
                let a = aria2.clone();
                let h = app_handle.clone();
                let dir = download_dir.clone();
                tauri::async_runtime::spawn(async move {
                    engine::direct::start_aria2(&h, a, &dir).await;
                });
            }

            app.manage(AppState {
                db: db.clone(),
                settings,
                aria2: aria2.clone(),
            });

            // Progress poll → emit loop
            {
                let h = app_handle.clone();
                tauri::async_runtime::spawn(async move {
                    engine::queue::emit_loop(h, aria2, db).await;
                });
            }

            // Sniffer Unix socket
            {
                let h = app_handle.clone();
                tauri::async_runtime::spawn(async move {
                    if let Err(e) = sniffer::start(h).await {
                        log::warn!("sniffer: {}", e);
                    }
                });
            }

            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            commands::probe_url,
            commands::add_download,
            commands::list_active,
            commands::list_completed,
            commands::pause_download,
            commands::resume_download,
            commands::cancel_download,
            commands::reveal_in_folder,
            commands::get_settings,
            commands::update_settings,
            commands::storage_stats,
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
