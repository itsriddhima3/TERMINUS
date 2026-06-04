-- Candidate filter bundle (2024-09 review). Not applied; kept for diff review.
-- Rewrites ledger/contacts reads to call op_m3_for_session for audit parity.

DROP POLICY IF EXISTS pol_ledger_read ON ledger;
CREATE POLICY pol_ledger_read ON ledger
  FOR SELECT
  USING (
    org_ref = current_setting('app.scope_id', true)::integer
    AND op_m3_for_session('ingest')
  );
