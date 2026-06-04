#!/bin/bash
set -euo pipefail

# Terminal-Bench Canary (do not remove): TB3_ORACLE_CANARY

cd /app

cat > /app/merge-src/merge_a.rs <<'EOF'
use std::path::Path;

use crate::io::pack::{list_channel_files, parse_channel_file, RawEvent};

pub struct MergedInput {
    pub events: Vec<RawEvent>,
}

impl MergedInput {
    pub fn from_pack(pack_dir: &Path) -> Result<Self, String> {
        let files = list_channel_files(pack_dir)?;
        let mut events = Vec::new();
        for path in files {
            let channel = path
                .file_stem()
                .and_then(|s| s.to_str())
                .unwrap_or("unknown")
                .to_string();
            events.extend(parse_channel_file(&path, &channel)?);
        }
        Ok(Self { events })
    }
}
EOF

cat > /app/resolve-src/resolve_b.rs <<'EOF'
use std::collections::BTreeMap;

use crate::io::pack::RawEvent;
use crate::merge_a::MergedInput;

#[derive(Debug, Clone)]
pub struct ResolvedEvent {
    pub kind: String,
    pub tick: i64,
    pub object: String,
    pub holder: Option<String>,
    pub from: Option<String>,
    pub to: Option<String>,
}

pub struct ResolvedBatch {
    pub events: Vec<ResolvedEvent>,
    pub contradictions: i64,
}

fn rank_of(channel: &str, ranks: &BTreeMap<String, i64>) -> i64 {
    *ranks.get(channel).unwrap_or(&0)
}

pub fn resolve_events(input: MergedInput, ranks: &BTreeMap<String, i64>) -> Result<ResolvedBatch, String> {
    let mut xfer_keys = BTreeMap::new();
    for ev in &input.events {
        if ev.kind == "xfer" {
            xfer_keys.insert((ev.tick, ev.object.clone()), true);
        }
    }

    let mut by_key: BTreeMap<(i64, String), Vec<&RawEvent>> = BTreeMap::new();
    for ev in &input.events {
        if ev.kind == "see" {
            by_key.entry((ev.tick, ev.object.clone())).or_default().push(ev);
        }
    }

    let mut out = Vec::new();
    let mut contradictions = 0i64;

    for ev in &input.events {
        if ev.kind == "xfer" {
            out.push(ResolvedEvent {
                kind: ev.kind.clone(),
                tick: ev.tick,
                object: ev.object.clone(),
                holder: None,
                from: ev.from.clone(),
                to: ev.to.clone(),
            });
        }
    }

    for ((tick, object), group) in by_key {
        if xfer_keys.contains_key(&(tick, object.clone())) {
            continue;
        }
        let mut holders: Vec<(String, String)> = group
            .iter()
            .filter_map(|e| e.holder.clone().map(|h| (h, e.channel.clone())))
            .collect();
        holders.sort_by(|a, b| a.0.cmp(&b.0));
        let distinct: std::collections::BTreeSet<String> = holders.iter().map(|(h, _)| h.clone()).collect();
        if distinct.len() > 1 {
            contradictions += 1;
            let mut best = group[0];
            for ev in group.iter().skip(1) {
                let r_best = rank_of(&best.channel, ranks);
                let r_cur = rank_of(&ev.channel, ranks);
                if r_cur > r_best || (r_cur == r_best && ev.channel > best.channel) {
                    best = ev;
                }
            }
            out.push(ResolvedEvent {
                kind: "see".into(),
                tick,
                object,
                holder: best.holder.clone(),
                from: None,
                to: None,
            });
        } else if let Some((h, _)) = holders.first() {
            out.push(ResolvedEvent {
                kind: "see".into(),
                tick,
                object,
                holder: Some(h.clone()),
                from: None,
                to: None,
            });
        }
    }

    out.sort_by(|a, b| {
        (a.object.as_str(), a.tick, a.kind.as_str()).cmp(&(b.object.as_str(), b.tick, b.kind.as_str()))
    });
    Ok(ResolvedBatch {
        events: out,
        contradictions,
    })
}
EOF

cat > /app/graph-src/step_c.rs <<'EOF'
use std::collections::BTreeMap;

use crate::io::pack::PackMeta;
use crate::resolve_b::ResolvedBatch;

pub struct LedgerRow {
    pub tick: i64,
    pub object: String,
    pub from: String,
    pub to: String,
    pub inferred: bool,
}

#[derive(Clone)]
struct Point {
    tick: i64,
    holder: String,
    is_xfer: bool,
}

pub fn build_ledger(meta: &PackMeta, batch: &ResolvedBatch) -> Result<Vec<LedgerRow>, String> {
    let mut ledger = Vec::new();
    let mut xfer_at: BTreeMap<String, BTreeMap<i64, (String, String)>> = BTreeMap::new();

    for ev in &batch.events {
        if ev.kind == "xfer" {
            let from = ev.from.clone().unwrap_or_default();
            let to = ev.to.clone().unwrap_or_default();
            xfer_at
                .entry(ev.object.clone())
                .or_default()
                .insert(ev.tick, (from.clone(), to.clone()));
            ledger.push(LedgerRow {
                tick: ev.tick,
                object: ev.object.clone(),
                from,
                to,
                inferred: false,
            });
        }
    }

    let mut objects: BTreeMap<String, String> = BTreeMap::new();
    for (obj, holder) in &meta.initial_holders {
        objects.insert(obj.clone(), holder.clone());
    }
    for ev in &batch.events {
        objects.entry(ev.object.clone()).or_insert_with(String::new);
    }

    for (object, start) in objects {
        let mut points: Vec<Point> = Vec::new();
        for ev in &batch.events {
            if ev.object != object {
                continue;
            }
            if ev.kind == "xfer" {
                if let Some(to) = &ev.to {
                    points.push(Point {
                        tick: ev.tick,
                        holder: to.clone(),
                        is_xfer: true,
                    });
                }
            } else if ev.kind == "see" {
                if let Some(h) = &ev.holder {
                    points.push(Point {
                        tick: ev.tick,
                        holder: h.clone(),
                        is_xfer: false,
                    });
                }
            }
        }
        points.sort_by_key(|p| (p.tick, p.is_xfer));

        let mut cur = start;
        for pt in points {
            if pt.is_xfer {
                cur = pt.holder;
                continue;
            }
            if pt.holder != cur {
                let explicit = xfer_at
                    .get(&object)
                    .and_then(|m| m.get(&pt.tick))
                    .is_some();
                if !explicit {
                    ledger.push(LedgerRow {
                        tick: pt.tick,
                        object: object.clone(),
                        from: cur.clone(),
                        to: pt.holder.clone(),
                        inferred: true,
                    });
                }
                cur = pt.holder;
            }
        }
    }

    ledger.sort_by(|a, b| {
        (a.object.as_str(), a.tick, a.from.as_str(), a.to.as_str())
            .cmp(&(b.object.as_str(), b.tick, b.from.as_str(), b.to.as_str()))
    });
    Ok(ledger)
}
EOF

cat > /app/seal-src/phase_d.rs <<'EOF'
use std::collections::BTreeMap;

use crate::step_c::LedgerRow;

#[derive(Debug, Clone)]
pub struct ProofBlock {
    pub single_holder_ok: bool,
    pub acyclic_ok: bool,
    pub gap_fill_count: i64,
    pub contradiction_resolved: i64,
    pub ledger_digest: String,
}

pub fn build_proof(ledger: &[LedgerRow], contradictions: i64) -> ProofBlock {
    let gap_fill_count = ledger.iter().filter(|r| r.inferred).count() as i64;
    let acyclic_ok = check_acyclic(ledger);
    let single_holder_ok = acyclic_ok && !ledger.is_empty();
    let ledger_digest = digest_ledger(ledger);
    ProofBlock {
        single_holder_ok,
        acyclic_ok,
        gap_fill_count,
        contradiction_resolved: contradictions,
        ledger_digest,
    }
}

fn check_acyclic(ledger: &[LedgerRow]) -> bool {
    let mut by_obj: BTreeMap<String, Vec<&LedgerRow>> = BTreeMap::new();
    for row in ledger {
        by_obj.entry(row.object.clone()).or_default().push(row);
    }
    for rows in by_obj.values_mut() {
        rows.sort_by_key(|r| (r.tick, r.from.as_str(), r.to.as_str()));
        for w in rows.windows(2) {
            if w[0].to != w[1].from || w[1].tick < w[0].tick {
                return false;
            }
        }
    }
    true
}

fn digest_ledger(ledger: &[LedgerRow]) -> String {
    let mut parts = Vec::new();
    for row in ledger {
        parts.push(format!(
            "{{\"from\":\"{}\",\"inferred\":{},\"object\":\"{}\",\"tick\":{},\"to\":\"{}\"}}",
            escape(&row.from),
            if row.inferred { "true" } else { "false" },
            escape(&row.object),
            row.tick,
            escape(&row.to)
        ));
    }
    let body = format!("[{}]", parts.join(","));
    hex_sha256(body.as_bytes())
}

fn escape(s: &str) -> String {
    s.replace('\\', "\\\\").replace('"', "\\\"")
}

fn hex_sha256(data: &[u8]) -> String {
    let hash = sha256(data);
    hash.iter().map(|b| format!("{:02x}", b)).collect()
}

fn sha256(data: &[u8]) -> [u8; 32] {
    let mut h = [0u32; 8];
    h.copy_from_slice(&[
        0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a, 0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19,
    ]);
    let mut padded = data.to_vec();
    let bit_len = (data.len() as u64) * 8;
    padded.push(0x80);
    while (padded.len() % 64) != 56 {
        padded.push(0);
    }
    padded.extend_from_slice(&bit_len.to_be_bytes());
    for chunk in padded.chunks(64) {
        let mut w = [0u32; 64];
        for (i, word) in chunk.chunks(4).enumerate().take(16) {
            w[i] = u32::from_be_bytes([word[0], word.get(1).copied().unwrap_or(0), word.get(2).copied().unwrap_or(0), word.get(3).copied().unwrap_or(0)]);
        }
        for i in 16..64 {
            let s0 = w[i - 15].rotate_right(7) ^ w[i - 15].rotate_right(18) ^ (w[i - 15] >> 3);
            let s1 = w[i - 2].rotate_right(17) ^ w[i - 2].rotate_right(19) ^ (w[i - 2] >> 10);
            w[i] = w[i - 16]
                .wrapping_add(s0)
                .wrapping_add(w[i - 7])
                .wrapping_add(s1);
        }
        let mut a = h[0];
        let mut b = h[1];
        let mut c = h[2];
        let mut d = h[3];
        let mut e = h[4];
        let mut f = h[5];
        let mut g = h[6];
        let mut hh = h[7];
        let k = [
            0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5,
            0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3, 0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174,
            0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc, 0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
            0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7, 0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967,
            0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13, 0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
            0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
            0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
            0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208, 0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2,
        ];
        for i in 0..64 {
            let s1 = e.rotate_right(6) ^ e.rotate_right(11) ^ e.rotate_right(25);
            let ch = (e & f) ^ ((!e) & g);
            let temp1 = hh
                .wrapping_add(s1)
                .wrapping_add(ch)
                .wrapping_add(k[i])
                .wrapping_add(w[i]);
            let s0 = a.rotate_right(2) ^ a.rotate_right(13) ^ a.rotate_right(22);
            let maj = (a & b) ^ (a & c) ^ (b & c);
            let temp2 = s0.wrapping_add(maj);
            hh = g;
            g = f;
            f = e;
            e = d.wrapping_add(temp1);
            d = c;
            c = b;
            b = a;
            a = temp1.wrapping_add(temp2);
        }
        h[0] = h[0].wrapping_add(a);
        h[1] = h[1].wrapping_add(b);
        h[2] = h[2].wrapping_add(c);
        h[3] = h[3].wrapping_add(d);
        h[4] = h[4].wrapping_add(e);
        h[5] = h[5].wrapping_add(f);
        h[6] = h[6].wrapping_add(g);
        h[7] = h[7].wrapping_add(hh);
    }
    let mut out = [0u8; 32];
    for (i, v) in h.iter().enumerate() {
        out[i * 4..i * 4 + 4].copy_from_slice(&v.to_be_bytes());
    }
    out
}
EOF

bash /app/scripts/build.sh
bash /app/platform/run_scenarios.sh
