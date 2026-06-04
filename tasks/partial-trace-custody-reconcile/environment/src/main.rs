mod app;
mod io;

#[path = "../merge-src/merge_a.rs"]
mod merge_a;

#[path = "../resolve-src/resolve_b.rs"]
mod resolve_b;

#[path = "../graph-src/step_c.rs"]
mod step_c;

#[path = "../seal-src/phase_d.rs"]
mod phase_d;

#[path = "../decoy-src/scan_x.rs"]
mod scan_x;

#[path = "../decoy-src/tally_y.rs"]
mod tally_y;

fn main() {
    if let Err(e) = app::run() {
        eprintln!("{e}");
        std::process::exit(2);
    }
}
