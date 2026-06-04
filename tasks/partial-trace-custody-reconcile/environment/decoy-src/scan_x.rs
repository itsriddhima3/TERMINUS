use std::collections::BTreeMap;
use std::path::Path;

use crate::io::pack::{list_channel_files, RawEvent};

/// Alternate ingest helper retained for channel coverage reports.
pub fn collapse_by_tick(events: &[RawEvent]) -> BTreeMap<(i64, String), RawEvent> {
    let mut out = BTreeMap::new();
    for ev in events {
        out.insert((ev.tick, ev.object.clone()), ev.clone());
    }
    out
}

pub fn count_channel_lines(pack_dir: &Path) -> usize {
    let files = list_channel_files(pack_dir).unwrap_or_default();
    files
        .iter()
        .map(|p| {
            std::fs::read_to_string(p)
                .map(|t| t.lines().filter(|l| !l.trim().is_empty()).count())
                .unwrap_or(0)
        })
        .sum()
}
