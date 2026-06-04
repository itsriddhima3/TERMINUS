INSERT INTO org_dim (org_ref, label) VALUES
  (1, 'Acme-Crate'),
  (2, 'Beta-Tote'),
  (3, 'Delta-Bin')
ON CONFLICT (org_ref) DO NOTHING;

INSERT INTO ledger (org_ref, label, amount, active, status) VALUES
  (1, 'acme-freight-01', 1200.00, true, 'open'),
  (1, 'acme-freight-02', 850.50, true, 'open'),
  (1, 'acme-archive', 300.00, false, 'closed'),
  (2, 'beta-lane-a', 440.00, true, 'open'),
  (2, 'beta-lane-b', 990.25, true, 'open'),
  (3, 'delta-slot-1', 150.00, true, 'open'),
  (3, 'delta-slot-2', 275.00, true, 'open'),
  (3, 'delta-slot-3', 610.00, true, 'open'),
  (3, 'delta-slot-4', 88.00, true, 'pending')
;

INSERT INTO contacts (org_ref, name, email) VALUES
  (1, 'Mira Holt', 'mira@acme-crate.test'),
  (1, 'Jon Pike', 'jon@acme-crate.test'),
  (2, 'Ella Voss', 'ella@beta-tote.test'),
  (3, 'Kai Nuru', 'kai@delta-bin.test'),
  (3, 'Tess Om', 'tess@delta-bin.test')
;

INSERT INTO inventory (org_ref, sku, qty) VALUES
  (1, 'CR-100', 42),
  (1, 'CR-200', 17),
  (2, 'BT-11', 9),
  (3, 'DB-7', 31),
  (3, 'DB-8', 5)
;

INSERT INTO audit_log (org_ref, event_code, payload) VALUES
  (1, 'ingest', '{"lane":"north"}'),
  (2, 'ingest', '{"lane":"east"}'),
  (3, 'ingest', '{"lane":"south"}')
;
