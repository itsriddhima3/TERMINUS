use std::path::Path;
use std::process::Command;

use sha2::{Digest, Sha256};

#[derive(Debug, Clone)]
pub struct StreamFacts {
    pub dur_ms: i64,
    pub stream_hash: String,
}

pub fn read_stream_facts(media_path: &Path) -> Result<StreamFacts, String> {
    let out = Command::new("ffprobe")
        .args([
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            media_path.to_str().ok_or("bad path")?,
        ])
        .output()
        .map_err(|e| format!("ffprobe spawn: {e}"))?;
    if !out.status.success() {
        return Err(format!(
            "ffprobe status {}: {}",
            out.status,
            String::from_utf8_lossy(&out.stderr)
        ));
    }
    let dur_s: f64 = String::from_utf8_lossy(&out.stdout)
        .trim()
        .parse()
        .map_err(|_| "duration parse".to_string())?;
    let dur_ms = (dur_s * 1000.0).round() as i64;
    let bytes = std::fs::read(media_path).map_err(|e| format!("read media: {e}"))?;
    let mut hasher = Sha256::new();
    hasher.update(&bytes);
    let stream_hash = format!("{:x}", hasher.finalize());
    Ok(StreamFacts {
        dur_ms,
        stream_hash,
    })
}
