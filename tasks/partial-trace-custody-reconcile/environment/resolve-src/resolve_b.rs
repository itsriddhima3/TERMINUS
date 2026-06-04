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
        let holders: Vec<(String, String)> = group
            .iter()
            .filter_map(|e| e.holder.clone().map(|h| (h, e.channel.clone())))
            .collect();
        let distinct: std::collections::BTreeSet<String> = holders.iter().map(|(h, _)| h.clone()).collect();
        if distinct.len() > 1 {
            contradictions += 1;
            let mut best = group[0];
            for ev in group.iter().skip(1) {
                let r_best = rank_of(&best.channel, ranks);
                let r_cur = rank_of(&ev.channel, ranks);
                if r_cur < r_best || (r_cur == r_best && ev.channel < best.channel) {
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
