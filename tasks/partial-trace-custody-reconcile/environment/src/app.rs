use std::env;
use std::path::PathBuf;

use crate::io::pack::{load_pack, write_pack_result, PackMeta};
use crate::merge_a::MergedInput;
use crate::phase_d::build_proof;
use crate::resolve_b::resolve_events;
use crate::step_c::build_ledger;

pub fn run() -> Result<(), String> {
    let args: Vec<String> = env::args().collect();
    if args.len() != 3 {
        return Err("usage: route_pack <pack_dir> <out_json>".into());
    }
    let pack_dir = PathBuf::from(&args[1]);
    let out_path = PathBuf::from(&args[2]);

    let ranks = crate::io::pack::load_ranks("/app/config/channel_ranks.json")?;
    let meta: PackMeta = load_pack(&pack_dir)?;
    if crate::scan_x::count_channel_lines(&pack_dir) == 0 {
        return Err("pack has no channel lines".into());
    }
    let merged = MergedInput::from_pack(&pack_dir)?;
    let resolved = resolve_events(merged, &ranks)?;
    let ledger = build_ledger(&meta, &resolved)?;
    let proof = build_proof(&ledger, resolved.contradictions);
    let pack_ok = proof.single_holder_ok && proof.acyclic_ok && !ledger.is_empty();

    write_pack_result(
        &out_path,
        &meta.pack_id,
        &ledger,
        &proof,
        pack_ok,
    )?;
    Ok(())
}
