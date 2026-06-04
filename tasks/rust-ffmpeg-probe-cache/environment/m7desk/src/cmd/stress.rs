use std::fs;
use std::path::{Path, PathBuf};

use rayon::prelude::*;
use serde::Serialize;
use sha2::{Digest, Sha256};
use r2n::run_q3_scope;

use crate::probe::ff_lane::read_stream_facts;

#[derive(Debug, serde::Deserialize)]
struct Manifest {
    lanes: Vec<LaneSpec>,
    workers: usize,
}

#[derive(Debug, serde::Deserialize)]
struct LaneSpec {
    lane_id: String,
    catalog: String,
    clips: Vec<String>,
    expected_rows: u32,
}

#[derive(Debug, Serialize)]
struct LaneReport {
    lane_id: String,
    expected_rows: u32,
    observed_rows: u32,
    busy_events: u32,
    journal_mode: String,
    integrity_ok: bool,
}

#[derive(Debug, Serialize)]
struct StressLedger {
    lanes: Vec<LaneReport>,
    summary: Summary,
}

#[derive(Debug, Serialize)]
struct Summary {
    all_complete: bool,
    ledger_digest: String,
}

pub fn run_from_args(args: &[String]) -> Result<(), String> {
    let mut manifest_path: Option<PathBuf> = None;
    let mut output_path: Option<PathBuf> = None;
    let mut i = 0;
    while i < args.len() {
        match args[i].as_str() {
            "--manifest" => {
                i += 1;
                manifest_path = Some(PathBuf::from(args.get(i).ok_or("missing manifest")?));
            }
            "--output" => {
                i += 1;
                output_path = Some(PathBuf::from(args.get(i).ok_or("missing output")?));
            }
            flag => return Err(format!("unknown flag: {flag}")),
        }
        i += 1;
    }
    let manifest_path = manifest_path.ok_or("manifest required")?;
    let output_path = output_path.ok_or("output required")?;
    run_stress(&manifest_path, &output_path)
}

pub fn run_stress(manifest_path: &Path, output_path: &Path) -> Result<(), String> {
    let raw = fs::read_to_string(manifest_path).map_err(|e| e.to_string())?;
    let manifest: Manifest = toml::from_str(&raw).map_err(|e| e.to_string())?;
    let work_root = PathBuf::from("/tmp/m7desk_stress");
    if work_root.exists() {
        fs::remove_dir_all(&work_root).map_err(|e| e.to_string())?;
    }
    fs::create_dir_all(&work_root).map_err(|e| e.to_string())?;
    fs::create_dir_all(
        output_path
            .parent()
            .unwrap_or_else(|| Path::new("/app/output")),
    )
    .map_err(|e| e.to_string())?;

    let mut lane_reports = Vec::new();
    let mut all_complete = true;

    for lane in &manifest.lanes {
        let db_path = work_root.join(format!("{}.db", lane.catalog));
        let clip_dir = PathBuf::from("/app/data/clips");
        let clips: Vec<PathBuf> = lane
            .clips
            .iter()
            .map(|c| clip_dir.join(c))
            .collect();

        let ingest_result: Result<(), String> = run_q3_scope(&db_path, manifest.workers, |handle| {
            clips
                .par_iter()
                .try_for_each(|clip_path| {
                    let key = clip_path
                        .file_name()
                        .and_then(|s| s.to_str())
                        .unwrap_or("unknown");
                    let facts = read_stream_facts(clip_path)?;
                    handle
                        .write_facts(key, facts.dur_ms, &facts.stream_hash)
                        .map_err(|e| e.to_string())
                })
                .map_err(|s| {
                    rusqlite::Error::SqliteFailure(
                        rusqlite::ffi::Error::new(rusqlite::ffi::SQLITE_ERROR),
                        Some(s),
                    )
                })
        })
        .map_err(|e| e.to_string());

        if ingest_result.is_err() {
            all_complete = false;
        }

        let observed_rows: u32 = rusqlite::Connection::open(&db_path)
            .ok()
            .and_then(|c| {
                c.query_row("SELECT COUNT(*) FROM facts;", [], |r| r.get(0))
                    .ok()
            })
            .unwrap_or(0);
        let busy_events: u32 = rusqlite::Connection::open(&db_path)
            .ok()
            .and_then(|c| {
                c.query_row(
                    "SELECT value FROM meta WHERE key='busy_events';",
                    [],
                    |r| r.get(0),
                )
                .ok()
            })
            .unwrap_or(0);
        let journal_mode: String = rusqlite::Connection::open(&db_path)
            .ok()
            .and_then(|c| {
                c.query_row("PRAGMA journal_mode;", [], |r| r.get::<_, String>(0))
                    .ok()
            })
            .unwrap_or_else(|| "unknown".into());
        let integrity_ok = rusqlite::Connection::open(&db_path)
            .ok()
            .and_then(|c| {
                c.query_row("PRAGMA integrity_check;", [], |r| r.get::<_, String>(0))
                    .ok()
            })
            .map(|v| v == "ok")
            .unwrap_or(false);

        if observed_rows != lane.expected_rows || busy_events > 0 {
            all_complete = false;
        }

        lane_reports.push(LaneReport {
            lane_id: lane.lane_id.clone(),
            expected_rows: lane.expected_rows,
            observed_rows,
            busy_events,
            journal_mode,
            integrity_ok,
        });
    }

    let mut ledger = StressLedger {
        lanes: lane_reports,
        summary: Summary {
            all_complete,
            ledger_digest: String::new(),
        },
    };
    let mut json = serde_json::to_string_pretty(&ledger).map_err(|e| e.to_string())?;
    let digest = format!("{:x}", Sha256::digest(json.as_bytes()));
    ledger.summary.ledger_digest = digest;
    json = serde_json::to_string_pretty(&ledger).map_err(|e| e.to_string())?;
    fs::write(output_path, json).map_err(|e| e.to_string())?;

    if !ledger.summary.all_complete {
        return Err("stress incomplete".into());
    }
    Ok(())
}
