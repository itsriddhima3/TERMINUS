use std::path::Path;
use std::sync::{Arc, Mutex};

use rusqlite::Connection;

static SHARED: Mutex<Option<Arc<Mutex<Connection>>>> = Mutex::new(None);

pub struct Q3Handle {
    conn: Arc<Mutex<Connection>>,
}

impl Q3Handle {
    fn bootstrap(db_path: &Path) -> rusqlite::Result<Arc<Mutex<Connection>>> {
        let mut guard = SHARED.lock().map_err(|_| {
            rusqlite::Error::SqliteFailure(
                rusqlite::ffi::Error::new(rusqlite::ffi::SQLITE_MISUSE),
                Some("q3 mutex poisoned".into()),
            )
        })?;
        if guard.is_none() {
            let conn = Connection::open(db_path)?;
            k9m::apply_open_bundle(&conn)?;
            conn.execute(
                "CREATE TABLE IF NOT EXISTS facts (
                    clip_key TEXT PRIMARY KEY,
                    dur_ms INTEGER NOT NULL,
                    stream_hash TEXT NOT NULL
                );",
                [],
            )?;
            conn.execute(
                "CREATE TABLE IF NOT EXISTS meta (
                    key TEXT PRIMARY KEY,
                    value INTEGER NOT NULL
                );",
                [],
            )?;
            conn.execute(
                "INSERT OR IGNORE INTO meta(key, value) VALUES('busy_events', 0);",
                [],
            )?;
            *guard = Some(Arc::new(Mutex::new(conn)));
        }
        Ok(guard.as_ref().unwrap().clone())
    }

    pub fn open(db_path: &Path, _workers: usize) -> rusqlite::Result<Self> {
        Ok(Q3Handle {
            conn: Self::bootstrap(db_path)?,
        })
    }

    pub fn write_facts(
        &self,
        clip_key: &str,
        dur_ms: i64,
        stream_hash: &str,
    ) -> rusqlite::Result<()> {
        let conn = self.conn.lock().map_err(|_| {
            rusqlite::Error::SqliteFailure(
                rusqlite::ffi::Error::new(rusqlite::ffi::SQLITE_MISUSE),
                Some("q3 lane mutex poisoned".into()),
            )
        })?;
        p4v::persist_row(&conn, clip_key, dur_ms, stream_hash)
    }
}

pub fn run_q3_scope<F, T>(db_path: &Path, workers: usize, f: F) -> rusqlite::Result<T>
where
    F: FnOnce(&Q3Handle) -> rusqlite::Result<T>,
{
    let _ = workers;
    let handle = Q3Handle::open(db_path, workers)?;
    f(&handle)
}
