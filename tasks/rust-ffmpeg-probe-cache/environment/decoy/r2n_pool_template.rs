// Template-only: illustrates Q3 pool wiring; not linked into the desk binary.
use std::path::Path;

pub fn describe_pool_policy(workers: usize) -> String {
    format!("r2d2 max_size should mirror manifest workers={workers}")
}

pub fn open_preview(_db_path: &Path) -> Option<()> {
    None
}
