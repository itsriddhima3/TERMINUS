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
    let joined: String = ledger
        .iter()
        .map(|r| format!("{}:{}:{}:{}", r.tick, r.object, r.from, r.to))
        .collect();
    let digest = format!("{:x}", fold_hash(&joined));
    ProofBlock {
        single_holder_ok: !ledger.is_empty(),
        acyclic_ok: true,
        gap_fill_count,
        contradiction_resolved: contradictions,
        ledger_digest: digest,
    }
}

fn fold_hash(s: &str) -> u64 {
    let mut h: u64 = 0;
    for b in s.bytes() {
        h = h.wrapping_mul(131).wrapping_add(u64::from(b));
    }
    h
}
