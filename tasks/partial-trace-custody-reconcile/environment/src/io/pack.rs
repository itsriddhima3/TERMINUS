use std::collections::BTreeMap;
use std::fs;
use std::path::{Path, PathBuf};

use crate::phase_d::ProofBlock;
use crate::step_c::LedgerRow;

#[derive(Debug, Clone)]
pub struct PackMeta {
    pub pack_id: String,
    pub initial_holders: BTreeMap<String, String>,
}

#[derive(Debug, Clone)]
pub struct RawEvent {
    pub kind: String,
    pub tick: i64,
    pub object: String,
    pub holder: Option<String>,
    pub from: Option<String>,
    pub to: Option<String>,
    pub channel: String,
}

pub fn load_ranks(path: &str) -> Result<BTreeMap<String, i64>, String> {
    let text = fs::read_to_string(path).map_err(|e| e.to_string())?;
    let mut ranks = BTreeMap::new();
    for line in text.lines() {
        let line = line.trim();
        if !line.contains(':') || line.starts_with('{') || line.starts_with('}') {
            continue;
        }
        let line = line.trim_matches(|c| c == ',' || c == '"');
        let mut parts = line.splitn(2, ':');
        let key = parts.next().unwrap_or("").trim().trim_matches('"').to_string();
        let val = parts
            .next()
            .unwrap_or("0")
            .trim()
            .trim_matches(',')
            .parse::<i64>()
            .unwrap_or(0);
        if !key.is_empty() && key != "ranks" {
            ranks.insert(key, val);
        }
    }
    Ok(ranks)
}

pub fn load_pack(pack_dir: &Path) -> Result<PackMeta, String> {
    let meta_path = pack_dir.join("meta.json");
    let text = fs::read_to_string(&meta_path).map_err(|e| e.to_string())?;
    let pack_id = extract_string_field(&text, "pack_id").ok_or("pack_id missing")?;
    let initial_holders = extract_holder_map(&text);
    Ok(PackMeta {
        pack_id,
        initial_holders,
    })
}

fn extract_string_field(text: &str, field: &str) -> Option<String> {
    let needle = format!("\"{field}\"");
    let pos = text.find(&needle)?;
    let after = &text[pos + needle.len()..];
    let q1 = after.find('"')? + 1;
    let rest = &after[q1..];
    let q2 = rest.find('"')?;
    Some(rest[..q2].to_string())
}

fn extract_holder_map(text: &str) -> BTreeMap<String, String> {
    let mut out = BTreeMap::new();
    if let Some(start) = text.find("initial_holders") {
        let slice = &text[start..];
        if let Some(open) = slice.find('{') {
            let tail = &slice[open + 1..];
            if let Some(close) = tail.find('}') {
                let body = &tail[..close];
                for line in body.split(',') {
                    let line = line.trim();
                    if !line.contains(':') {
                        continue;
                    }
                    let mut parts = line.splitn(2, ':');
                    let k = parts
                        .next()
                        .unwrap_or("")
                        .trim()
                        .trim_matches('"')
                        .to_string();
                    let v = parts
                        .next()
                        .unwrap_or("")
                        .trim()
                        .trim_matches('"')
                        .to_string();
                    if !k.is_empty() {
                        out.insert(k, v);
                    }
                }
            }
        }
    }
    out
}

pub fn list_channel_files(pack_dir: &Path) -> Result<Vec<PathBuf>, String> {
    let ch = pack_dir.join("channels");
    let mut files: Vec<PathBuf> = fs::read_dir(&ch)
        .map_err(|e| e.to_string())?
        .filter_map(|e| e.ok())
        .map(|e| e.path())
        .filter(|p| p.extension().map(|x| x == "txt").unwrap_or(false))
        .collect();
    files.sort();
    Ok(files)
}

pub fn parse_channel_file(path: &Path, channel: &str) -> Result<Vec<RawEvent>, String> {
    let text = fs::read_to_string(path).map_err(|e| e.to_string())?;
    let mut out = Vec::new();
    for line in text.lines() {
        let line = line.trim();
        if line.is_empty() || line.starts_with('#') {
            continue;
        }
        let parts: Vec<&str> = line.split_whitespace().collect();
        if parts.len() < 3 {
            return Err(format!("bad line in {}: {}", path.display(), line));
        }
        match parts[0] {
            "see" if parts.len() == 4 => {
                let tick: i64 = parts[1].parse().map_err(|_| "tick".to_string())?;
                out.push(RawEvent {
                    kind: "see".into(),
                    tick,
                    object: parts[2].into(),
                    holder: Some(parts[3].into()),
                    from: None,
                    to: None,
                    channel: channel.into(),
                });
            }
            "xfer" if parts.len() == 5 => {
                let tick: i64 = parts[1].parse().map_err(|_| "tick".to_string())?;
                out.push(RawEvent {
                    kind: "xfer".into(),
                    tick,
                    object: parts[2].into(),
                    holder: None,
                    from: Some(parts[3].into()),
                    to: Some(parts[4].into()),
                    channel: channel.into(),
                });
            }
            other => return Err(format!("unknown verb {other} in {}", path.display())),
        }
    }
    Ok(out)
}

fn json_escape(s: &str) -> String {
    s.replace('\\', "\\\\").replace('"', "\\\"")
}

pub fn write_pack_result(
    out_path: &Path,
    pack_id: &str,
    ledger: &[LedgerRow],
    proof: &ProofBlock,
    pack_ok: bool,
) -> Result<(), String> {
    if let Some(parent) = out_path.parent() {
        fs::create_dir_all(parent).map_err(|e| e.to_string())?;
    }
    let mut lines = Vec::new();
    lines.push("{".to_string());
    lines.push(format!("  \"pack_id\": \"{}\",", json_escape(pack_id)));
    lines.push("  \"transition_ledger\": [".to_string());
    for (idx, row) in ledger.iter().enumerate() {
        let comma = if idx + 1 == ledger.len() { "" } else { "," };
        lines.push(format!(
            "    {{\"tick\": {}, \"object\": \"{}\", \"from\": \"{}\", \"to\": \"{}\", \"inferred\": {}}}{}",
            row.tick,
            json_escape(&row.object),
            json_escape(&row.from),
            json_escape(&row.to),
            if row.inferred { "true" } else { "false" },
            comma
        ));
    }
    lines.push("  ],".to_string());
    lines.push("  \"consistency_proof\": {".to_string());
    lines.push(format!(
        "    \"single_holder_ok\": {},",
        proof.single_holder_ok
    ));
    lines.push(format!("    \"acyclic_ok\": {},", proof.acyclic_ok));
    lines.push(format!(
        "    \"gap_fill_count\": {},",
        proof.gap_fill_count
    ));
    lines.push(format!(
        "    \"contradiction_resolved\": {},",
        proof.contradiction_resolved
    ));
    lines.push(format!(
        "    \"ledger_digest\": \"{}\"",
        json_escape(&proof.ledger_digest)
    ));
    lines.push("  },".to_string());
    lines.push(format!("  \"pack_ok\": {}", pack_ok));
    lines.push("}".to_string());
    fs::write(out_path, format!("{}\n", lines.join("\n"))).map_err(|e| e.to_string())?;
    Ok(())
}
