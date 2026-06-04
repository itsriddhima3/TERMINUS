use rusqlite::Connection;

pub fn apply_open_bundle(conn: &Connection) -> rusqlite::Result<()> {
    conn.execute_batch(
        "PRAGMA journal_mode=WAL;
         PRAGMA synchronous=OFF;
         PRAGMA busy_timeout=100;",
    )?;
    conn.execute_batch("PRAGMA journal_mode=DELETE;")?;
    Ok(())
}
