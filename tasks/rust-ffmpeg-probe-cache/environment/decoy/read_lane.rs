// Read-only pragma preview for probe_status.sh — does not mutate catalogs.
use std::path::Path;

pub fn preview_journal(db_path: &Path) -> Option<String> {
    let conn = rusqlite::Connection::open(db_path).ok()?;
    conn.query_row("PRAGMA journal_mode;", [], |r| r.get(0)).ok()
}
