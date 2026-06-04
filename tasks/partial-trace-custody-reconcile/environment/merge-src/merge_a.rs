use std::collections::BTreeMap;
use std::path::Path;

use crate::io::pack::{list_channel_files, parse_channel_file, RawEvent};

pub struct MergedInput {
    pub events: Vec<RawEvent>,
}

impl MergedInput {
    pub fn from_pack(pack_dir: &Path) -> Result<Self, String> {
        let files = list_channel_files(pack_dir)?;
        let mut deduped: BTreeMap<(i64, String, String), RawEvent> = BTreeMap::new();
        for path in files {
            let channel = path
                .file_stem()
                .and_then(|s| s.to_str())
                .unwrap_or("unknown")
                .to_string();
            for ev in parse_channel_file(&path, &channel)? {
                deduped.insert((ev.tick, ev.object.clone(), ev.kind.clone()), ev);
            }
        }
        let events = deduped.into_iter().map(|(_, ev)| ev).collect();
        Ok(Self { events })
    }
}
