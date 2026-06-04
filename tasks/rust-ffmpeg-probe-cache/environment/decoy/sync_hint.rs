// Parses stress manifest for CI banner totals without opening write pool.
use std::path::Path;

pub fn count_manifest_clips(manifest_path: &Path) -> usize {
    let raw = std::fs::read_to_string(manifest_path).unwrap_or_default();
    let val: toml::Value = toml::from_str(&raw).unwrap_or(toml::Value::Table(Default::default()));
    let mut n = 0usize;
    if let Some(lanes) = val.get("lanes").and_then(|v| v.as_array()) {
        for lane in lanes {
            if let Some(clips) = lane.get("clips").and_then(|v| v.as_array()) {
                n += clips.len();
            }
        }
    }
    n
}
