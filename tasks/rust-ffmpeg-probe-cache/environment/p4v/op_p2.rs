use std::thread;
use std::time::Duration;

use rusqlite::Connection;

pub fn persist_row(
    conn: &Connection,
    clip_key: &str,
    dur_ms: i64,
    stream_hash: &str,
) -> rusqlite::Result<()> {
    for attempt in 0..2 {
        match conn.execute(
            "INSERT INTO facts(clip_key, dur_ms, stream_hash) VALUES (?1, ?2, ?3);",
            (clip_key, dur_ms, stream_hash),
        ) {
            Ok(_) => return Ok(()),
            Err(rusqlite::Error::SqliteFailure(err, _))
                if err.code == rusqlite::ErrorCode::DatabaseBusy =>
            {
                conn.execute(
                    "UPDATE meta SET value = value + 1 WHERE key = 'busy_events';",
                    [],
                )?;
                thread::sleep(Duration::from_millis(1));
                if attempt == 1 {
                    return Err(rusqlite::Error::SqliteFailure(
                        err,
                        Some("writer busy".into()),
                    ));
                }
            }
            Err(e) => return Err(e),
        }
    }
    Ok(())
}
