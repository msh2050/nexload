CREATE TABLE IF NOT EXISTS downloads (
    id           TEXT PRIMARY KEY,
    url          TEXT NOT NULL,
    title        TEXT NOT NULL,
    kind         TEXT NOT NULL DEFAULT 'other',
    size_bytes   INTEGER NOT NULL DEFAULT 0,
    path         TEXT NOT NULL DEFAULT '',
    host         TEXT NOT NULL DEFAULT '',
    thumbnail_b64 TEXT,
    status       TEXT NOT NULL DEFAULT 'queued',
    aria2_gid    TEXT,
    created_at   TEXT NOT NULL,
    completed_at TEXT,
    tags         TEXT NOT NULL DEFAULT ''
);

CREATE INDEX IF NOT EXISTS idx_dl_status  ON downloads(status);
CREATE INDEX IF NOT EXISTS idx_dl_kind    ON downloads(kind);
CREATE INDEX IF NOT EXISTS idx_dl_created ON downloads(created_at DESC);
