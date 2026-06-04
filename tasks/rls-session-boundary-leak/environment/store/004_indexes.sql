CREATE INDEX IF NOT EXISTS ledger_org_active_idx ON ledger (org_ref) WHERE active;
CREATE INDEX IF NOT EXISTS contacts_org_idx ON contacts (org_ref);
CREATE INDEX IF NOT EXISTS inventory_org_sku_idx ON inventory (org_ref, sku);
CREATE INDEX IF NOT EXISTS audit_log_org_idx ON audit_log (org_ref, recorded_at DESC);
