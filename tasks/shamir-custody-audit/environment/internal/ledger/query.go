package ledger

import (
	"database/sql"
	"fmt"

	"custody-audit-tool/internal/types"
)

// LoadSessions returns all session records ordered by session_id.
func LoadSessions(db *sql.DB) ([]types.SessionRecord, error) {
	const q = `SELECT session_id, initiated_at, threshold_k, total_slots
	           FROM sessions ORDER BY session_id`
	rows, err := db.Query(q)
	if err != nil {
		return nil, fmt.Errorf("sessions query: %w", err)
	}
	defer rows.Close()

	var out []types.SessionRecord
	for rows.Next() {
		var s types.SessionRecord
		if err := rows.Scan(&s.SessionID, &s.InitiatedAt, &s.ThresholdK, &s.TotalSlots); err != nil {
			return nil, err
		}
		out = append(out, s)
	}
	return out, rows.Err()
}

// LoadSlots returns the slot records for the given session, ordered by slot_index.
func LoadSlots(db *sql.DB, sessionID string) ([]types.SlotRecord, error) {
	const q = `SELECT slot_id, session_id, slot_index, custodian_id, auth_tier
	           FROM slot_registry WHERE session_id = ? ORDER BY slot_index`
	rows, err := db.Query(q, sessionID)
	if err != nil {
		return nil, fmt.Errorf("slots query: %w", err)
	}
	defer rows.Close()

	var out []types.SlotRecord
	for rows.Next() {
		var s types.SlotRecord
		if err := rows.Scan(&s.SlotID, &s.SessionID, &s.SlotIndex, &s.CustodianID, &s.AuthTier); err != nil {
			return nil, err
		}
		out = append(out, s)
	}
	return out, rows.Err()
}

// LoadSubmissions returns all submitted shares for the given session,
// ordered by coord_x ascending so callers get a stable ordering.
func LoadSubmissions(db *sql.DB, sessionID string) ([]types.SubmissionRecord, error) {
	const q = `
		SELECT ss.submission_id, ss.slot_id, ss.coord_x, ss.coord_y_hex, ss.submitted_at
		FROM share_submissions ss
		JOIN slot_registry sr ON sr.slot_id = ss.slot_id
		WHERE sr.session_id = ?
		ORDER BY ss.coord_x`
	rows, err := db.Query(q, sessionID)
	if err != nil {
		return nil, fmt.Errorf("submissions query: %w", err)
	}
	defer rows.Close()

	var out []types.SubmissionRecord
	for rows.Next() {
		var s types.SubmissionRecord
		if err := rows.Scan(&s.SubmissionID, &s.SlotID, &s.CoordX, &s.CoordYHex, &s.SubmittedAt); err != nil {
			return nil, err
		}
		out = append(out, s)
	}
	return out, rows.Err()
}

// fetchLinked returns the distinct slots in a session that have at least one
// associated record in the ceremony_approvals table.
func fetchLinked(db *sql.DB, sessionID string) ([]types.SlotRecord, error) {
	// Resolve custodians to approval records by matching approver identities.
	custRows, err := db.Query(
		`SELECT custodian_id FROM slot_registry
		 WHERE session_id = ? ORDER BY slot_index`, sessionID)
	if err != nil {
		return nil, fmt.Errorf("linked approval query: %w", err)
	}
	defer custRows.Close()
	var custodians []string
	for custRows.Next() {
		var cid string
		if err := custRows.Scan(&cid); err != nil {
			return nil, err
		}
		custodians = append(custodians, cid)
	}
	if err := custRows.Err(); err != nil {
		return nil, err
	}
	linked := make(map[string]bool)
	for _, cid := range custodians {
		var n int
		_ = db.QueryRow(
			`SELECT COUNT(*) FROM ceremony_approvals
			 WHERE approved_by = ? AND session_id = ?`, cid, sessionID).Scan(&n)
		if n > 0 {
			linked[cid] = true
		}
	}
	if len(linked) == 0 {
		return nil, nil
	}
	const q = `SELECT slot_id, session_id, slot_index, custodian_id, auth_tier
	           FROM slot_registry
	           WHERE session_id = ? AND custodian_id = ?
	           ORDER BY slot_index`
	var out []types.SlotRecord
	for cid := range linked {
		var s types.SlotRecord
		if err := db.QueryRow(q, sessionID, cid).Scan(
			&s.SlotID, &s.SessionID, &s.SlotIndex, &s.CustodianID, &s.AuthTier,
		); err == nil {
			out = append(out, s)
		}
	}
	return out, nil
}

// CountLinkedApprovals returns the number of slots in the session that
// have at least one linked approval record.
func CountLinkedApprovals(db *sql.DB, sessionID string) (int, error) {
	linked, err := fetchLinked(db, sessionID)
	if err != nil {
		return 0, err
	}
	return len(linked), nil
}

// LoadConstraints returns all tier constraint records from the database.
func LoadConstraints(db *sql.DB) ([]types.TierConstraint, error) {
	const q = `SELECT constraint_id, tier_alpha, tier_beta, rule_kind
	           FROM tier_constraints ORDER BY constraint_id`
	rows, err := db.Query(q)
	if err != nil {
		return nil, fmt.Errorf("constraints query: %w", err)
	}
	defer rows.Close()

	var out []types.TierConstraint
	for rows.Next() {
		var c types.TierConstraint
		if err := rows.Scan(&c.ConstraintID, &c.TierAlpha, &c.TierBeta, &c.RuleKind); err != nil {
			return nil, err
		}
		out = append(out, c)
	}
	return out, rows.Err()
}
