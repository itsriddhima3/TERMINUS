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
        points.sort_by_key(|p| p.tick);

        let mut cur = start;
        for pt in points {
            if pt.is_xfer {
                cur = pt.holder;
                continue;
            }
            if pt.holder != cur {
                ledger.push(LedgerRow {
                    tick: pt.tick,
                    object: object.clone(),
                    from: cur.clone(),
                    to: pt.holder.clone(),
                    inferred: true,
                });
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
