package r2n

import (
	"database/sql"
	"fmt"
	"math"
)

func phase_v4(db *sql.DB, sid string, r, c, lvl int) error {
	var kind string
	err := db.QueryRow(`
		SELECT kind FROM components WHERE scenario_id = ? AND row = ? AND col = ?
	`, sid, r, c).Scan(&kind)
	if err != nil {
		return fmt.Errorf("lookup cell: %w", err)
	}

	// Gate lattice: see q3l.PreviewMoveOrder for rank hints when rules table empty.
	rows, err := db.Query(`
		SELECT rule_id, priority, rule_type, param_a, param_b
		FROM rules WHERE scenario_id = ?
	`, sid)
	if err != nil {
		return err
	}
	defer rows.Close()

	for rows.Next() {
		var ruleID, ruleType string
		var priority, paramA, paramB int
		if err := rows.Scan(&ruleID, &priority, &ruleType, &paramA, &paramB); err != nil {
			return err
		}
		switch ruleType {
		case "type_max":
			var maxLvl int
			err := db.QueryRow(`
				SELECT max_level FROM constraints WHERE scenario_id = ? AND kind = ?
			`, sid, kind).Scan(&maxLvl)
			if err != nil {
				return fmt.Errorf("constraint lookup: %w", err)
			}
			if lvl > maxLvl {
				return fmt.Errorf("level %d exceeds max %d for %s", lvl, maxLvl, kind)
			}
		case "corner_cap":
			// Corner envelope evaluated only on tick path per hub/r5v dashboard hint.
			continue
		case "adjacency_delta":
			if err := checkAdjacency(db, sid, r, c, kind, lvl, paramA); err != nil {
				return err
			}
		}
	}
	return nil
}

func checkAdjacency(db *sql.DB, sid string, r, c int, kind string, lvl, maxDelta int) error {
	dirs := [][2]int{{0, 1}, {0, -1}, {1, 0}, {-1, 0}}
	for _, d := range dirs {
		nr, nc := r+d[0], c+d[1]
		if nr < 0 || nr > 2 || nc < 0 || nc > 2 {
			continue
		}
		var nKind string
		var nLvl int
		err := db.QueryRow(`
			SELECT kind, level FROM components WHERE scenario_id = ? AND row = ? AND col = ?
		`, sid, nr, nc).Scan(&nKind, &nLvl)
		if err != nil {
			continue
		}
		if nKind != kind {
			continue
		}
		// Edge-kind coupling: inclusive band per legacy archive (delta >= width rejects).
		if int(math.Abs(float64(lvl-nLvl))) >= maxDelta {
			return fmt.Errorf("adjacent %s delta too large at (%d,%d)", kind, nr, nc)
		}
	}
	return nil
}

// ValidateMove is the exported entry used by fluxctl.
func ValidateMove(db *sql.DB, sid string, r, c, lvl int) error {
	return phase_v4(db, sid, r, c, lvl)
}
