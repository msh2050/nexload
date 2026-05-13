use rusqlite::{params, Connection, Result};
use serde::{Deserialize, Serialize};
use std::path::Path;

pub struct Db {
    conn: Connection,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct DownloadRecord {
    pub id: String,
    pub url: String,
    pub title: String,
    pub kind: String,
    pub size_bytes: i64,
    pub path: String,
    pub host: String,
    pub thumbnail_b64: Option<String>,
    pub status: String,
    pub aria2_gid: Option<String>,
    pub created_at: String,
    pub completed_at: Option<String>,
}

impl Db {
    pub fn open<P: AsRef<Path>>(path: P) -> Result<Self> {
        let conn = Connection::open(path)?;
        conn.execute_batch(include_str!("schema.sql"))?;
        Ok(Self { conn })
    }

    pub fn insert(&self, r: &DownloadRecord) -> Result<()> {
        self.conn.execute(
            "INSERT OR IGNORE INTO downloads
             (id,url,title,kind,size_bytes,path,host,thumbnail_b64,status,aria2_gid,created_at)
             VALUES (?1,?2,?3,?4,?5,?6,?7,?8,?9,?10,?11)",
            params![
                r.id, r.url, r.title, r.kind, r.size_bytes, r.path,
                r.host, r.thumbnail_b64, r.status, r.aria2_gid, r.created_at
            ],
        )?;
        Ok(())
    }

    pub fn set_gid(&self, id: &str, gid: &str) -> Result<()> {
        self.conn.execute(
            "UPDATE downloads SET aria2_gid=?1, status='active' WHERE id=?2",
            params![gid, id],
        )?;
        Ok(())
    }

    pub fn set_status(&self, id: &str, status: &str) -> Result<()> {
        self.conn.execute(
            "UPDATE downloads SET status=?1 WHERE id=?2",
            params![status, id],
        )?;
        Ok(())
    }

    pub fn complete(&self, id: &str, size: i64, path: &str, at: &str) -> Result<()> {
        self.conn.execute(
            "UPDATE downloads SET status='completed',size_bytes=?1,path=?2,completed_at=?3 WHERE id=?4",
            params![size, path, at, id],
        )?;
        Ok(())
    }

    pub fn by_gid(&self, gid: &str) -> Result<Option<DownloadRecord>> {
        let mut stmt = self.conn.prepare(
            "SELECT id,url,title,kind,size_bytes,path,host,thumbnail_b64,status,aria2_gid,created_at,completed_at
             FROM downloads WHERE aria2_gid=?1"
        )?;
        let mut rows = stmt.query_map(params![gid], row_map)?;
        Ok(rows.next().transpose()?)
    }

    pub fn list_active(&self) -> Result<Vec<DownloadRecord>> {
        let mut stmt = self.conn.prepare(
            "SELECT id,url,title,kind,size_bytes,path,host,thumbnail_b64,status,aria2_gid,created_at,completed_at
             FROM downloads WHERE status IN ('active','queued','paused')
             ORDER BY created_at DESC"
        )?;
        let rows: Result<Vec<_>> = stmt.query_map([], row_map)?.collect();
        rows
    }

    pub fn list_completed(&self, kind: Option<&str>, limit: u32) -> Result<Vec<DownloadRecord>> {
        if let Some(k) = kind {
            let sql = format!(
                "SELECT id,url,title,kind,size_bytes,path,host,thumbnail_b64,status,aria2_gid,created_at,completed_at
                 FROM downloads WHERE status='completed' AND kind=?1 ORDER BY completed_at DESC LIMIT {}",
                limit
            );
            let mut stmt = self.conn.prepare(&sql)?;
            let rows: Result<Vec<_>> = stmt.query_map(params![k], row_map)?.collect();
            rows
        } else {
            let sql = format!(
                "SELECT id,url,title,kind,size_bytes,path,host,thumbnail_b64,status,aria2_gid,created_at,completed_at
                 FROM downloads WHERE status='completed' ORDER BY completed_at DESC LIMIT {}",
                limit
            );
            let mut stmt = self.conn.prepare(&sql)?;
            let rows: Result<Vec<_>> = stmt.query_map([], row_map)?.collect();
            rows
        }
    }

    pub fn storage_totals(&self) -> Result<(i64, std::collections::HashMap<String, i64>)> {
        let total: i64 = self.conn.query_row(
            "SELECT COALESCE(SUM(size_bytes),0) FROM downloads WHERE status='completed'",
            [],
            |r| r.get(0),
        )?;
        let mut stmt = self.conn.prepare(
            "SELECT kind, COALESCE(SUM(size_bytes),0) FROM downloads WHERE status='completed' GROUP BY kind"
        )?;
        let pairs: Result<Vec<(String, i64)>> = stmt
            .query_map([], |r| Ok((r.get::<_, String>(0)?, r.get::<_, i64>(1)?)))?
            .collect();
        let map = pairs?.into_iter().collect();
        Ok((total, map))
    }
}

fn row_map(r: &rusqlite::Row) -> rusqlite::Result<DownloadRecord> {
    Ok(DownloadRecord {
        id:            r.get(0)?,
        url:           r.get(1)?,
        title:         r.get(2)?,
        kind:          r.get(3)?,
        size_bytes:    r.get(4)?,
        path:          r.get(5)?,
        host:          r.get(6)?,
        thumbnail_b64: r.get(7)?,
        status:        r.get(8)?,
        aria2_gid:     r.get(9)?,
        created_at:    r.get(10)?,
        completed_at:  r.get(11)?,
    })
}
