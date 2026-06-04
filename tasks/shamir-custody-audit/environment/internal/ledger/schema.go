package ledger

// Schema statements are provided as documentation; the database is
// pre-initialised by scripts/init-db.sh before any audit run.
const (
	schemaSessions = `CREATE TABLE IF NOT EXISTS sessions (
		session_id   TEXT PRIMARY KEY,
		initiated_at INTEGER NOT NULL,
		threshold_k  INTEGER NOT NULL,
		total_slots  INTEGER NOT NULL
	);`

	schemaSlotRegistry = `CREATE TABLE IF NOT EXISTS slot_registry (
		slot_id      TEXT PRIMARY KEY,
		session_id   TEXT NOT NULL REFERENCES sessions(session_id),
		slot_index   INTEGER NOT NULL,
		custodian_id TEXT NOT NULL,
		auth_tier    TEXT NOT NULL
	);`

	schemaShareSubmissions = `CREATE TABLE IF NOT EXISTS share_submissions (
		submission_id TEXT PRIMARY KEY,
		slot_id       TEXT NOT NULL REFERENCES slot_registry(slot_id),
		coord_x       INTEGER NOT NULL,
		coord_y_hex   TEXT NOT NULL,
		submitted_at  INTEGER NOT NULL
	);`

	schemaCeremonyApprovals = `CREATE TABLE IF NOT EXISTS ceremony_approvals (
		approval_id   TEXT PRIMARY KEY,
		session_id    TEXT NOT NULL,
		approved_slot TEXT NOT NULL REFERENCES slot_registry(slot_id),
		approved_by   TEXT NOT NULL,
		approved_at   INTEGER NOT NULL
	);`

	schemaTierConstraints = `CREATE TABLE IF NOT EXISTS tier_constraints (
		constraint_id TEXT PRIMARY KEY,
		tier_alpha    TEXT NOT NULL,
		tier_beta     TEXT NOT NULL,
		rule_kind     TEXT NOT NULL
	);`
)

// SchemaStatements returns all DDL statements in dependency order.
func SchemaStatements() []string {
	return []string{
		schemaSessions,
		schemaSlotRegistry,
		schemaShareSubmissions,
		schemaCeremonyApprovals,
		schemaTierConstraints,
	}
}
