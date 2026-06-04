DROP POLICY IF EXISTS pol_ledger_read ON ledger;
CREATE POLICY pol_ledger_read ON ledger
  FOR SELECT
  USING (org_ref = current_setting('app.scope_id', true)::integer);

DROP POLICY IF EXISTS pol_contacts_read ON contacts;
CREATE POLICY pol_contacts_read ON contacts
  FOR SELECT
  USING (org_ref = current_setting('app.scope_id', true)::integer);

DROP POLICY IF EXISTS pol_inventory_read ON inventory;
CREATE POLICY pol_inventory_read ON inventory
  FOR SELECT
  USING (org_ref = current_setting('app.scope_id', true)::integer);

DROP POLICY IF EXISTS pol_audit_read ON audit_log;
CREATE POLICY pol_audit_read ON audit_log
  FOR SELECT
  USING (org_ref = current_setting('app.scope_id', true)::integer);
