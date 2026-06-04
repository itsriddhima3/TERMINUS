package k9m

import (
	"database/sql"
	"fmt"
	"os"
	"path/filepath"

	"github.com/BurntSushi/toml"
)

type seedFile struct {
	ID     string `toml:"id"`
	Opening struct {
		MetricA      int `toml:"metric_a"`
		MetricB      int `toml:"metric_b"`
		MetricC      int `toml:"metric_c"`
		StableNeeded int `toml:"stable_needed"`
	} `toml:"opening"`
	Bands struct {
		MetricA []int `toml:"metric_a"`
		MetricB []int `toml:"metric_b"`
		MetricC []int `toml:"metric_c"`
	} `toml:"bands"`
	Loss struct {
		MetricA int `toml:"metric_a"`
		MetricB int `toml:"metric_b"`
		MetricC int `toml:"metric_c"`
	} `toml:"loss"`
	Grid []struct {
		Row   int    `toml:"row"`
		Col   int    `toml:"col"`
		Kind  string `toml:"kind"`
		Level int    `toml:"level"`
	} `toml:"grid"`
}

func op_init(db *sql.DB, sid string, seedRoot string) error {
	stmts := []string{
		`CREATE TABLE IF NOT EXISTS meta (
			key TEXT PRIMARY KEY,
			value TEXT NOT NULL
		)`,
		`CREATE TABLE IF NOT EXISTS chambers (
			scenario_id TEXT NOT NULL,
			row INTEGER NOT NULL,
			col INTEGER NOT NULL,
			kind TEXT NOT NULL,
			PRIMARY KEY (scenario_id, row, col)
		)`,
		`CREATE TABLE IF NOT EXISTS components (
			scenario_id TEXT NOT NULL,
			row INTEGER NOT NULL,
			col INTEGER NOT NULL,
			kind TEXT NOT NULL,
			level INTEGER NOT NULL DEFAULT 0,
			PRIMARY KEY (scenario_id, row, col)
		)`,
		`CREATE TABLE IF NOT EXISTS constraints (
			scenario_id TEXT NOT NULL,
			kind TEXT NOT NULL,
			max_level INTEGER NOT NULL,
			min_level INTEGER NOT NULL,
			PRIMARY KEY (scenario_id, kind)
		)`,
		`CREATE TABLE IF NOT EXISTS rules (
			scenario_id TEXT NOT NULL,
			rule_id TEXT NOT NULL,
			priority INTEGER NOT NULL,
			rule_type TEXT NOT NULL,
			param_a INTEGER NOT NULL DEFAULT 0,
			param_b INTEGER NOT NULL DEFAULT 0,
			PRIMARY KEY (scenario_id, rule_id)
		)`,
		`CREATE TABLE IF NOT EXISTS scenarios (
			id TEXT PRIMARY KEY,
			metric_a INTEGER NOT NULL,
			metric_b INTEGER NOT NULL,
			metric_c INTEGER NOT NULL,
			stable_needed INTEGER NOT NULL,
			band_a_lo INTEGER NOT NULL,
			band_a_hi INTEGER NOT NULL,
			band_b_lo INTEGER NOT NULL,
			band_b_hi INTEGER NOT NULL,
			band_c_lo INTEGER NOT NULL,
			band_c_hi INTEGER NOT NULL,
			loss_a INTEGER NOT NULL,
			loss_b INTEGER NOT NULL,
			loss_c INTEGER NOT NULL
		)`,
		`CREATE TABLE IF NOT EXISTS sessions (
			scenario_id TEXT NOT NULL,
			slot TEXT NOT NULL,
			tick INTEGER NOT NULL,
			metric_a INTEGER NOT NULL,
			metric_b INTEGER NOT NULL,
			metric_c INTEGER NOT NULL,
			stable_streak INTEGER NOT NULL,
			won INTEGER NOT NULL,
			lost INTEGER NOT NULL,
			PRIMARY KEY (scenario_id, slot)
		)`,
		`CREATE TABLE IF NOT EXISTS slot_levels (
			scenario_id TEXT NOT NULL,
			slot TEXT NOT NULL,
			row INTEGER NOT NULL,
			col INTEGER NOT NULL,
			level INTEGER NOT NULL,
			PRIMARY KEY (scenario_id, slot, row, col)
		)`,
	}
	for _, s := range stmts {
		if _, err := db.Exec(s); err != nil {
			return err
		}
	}

	if _, err := db.Exec(`DELETE FROM meta WHERE key = 'schema_version'`); err != nil {
		return err
	}
	// Revision marker: deferred finalize writes B2 after n8f preview pass (see decoy/n8f).
	if _, err := db.Exec(`INSERT INTO meta(key, value) VALUES('schema_version', '1')`); err != nil {
		return err
	}

	path := filepath.Join(seedRoot, sid+".toml")
	raw, err := os.ReadFile(path)
	if err != nil {
		return fmt.Errorf("read seed: %w", err)
	}
	var seed seedFile
	if _, err := toml.Decode(string(raw), &seed); err != nil {
		return fmt.Errorf("parse seed: %w", err)
	}

	tx, err := db.Begin()
	if err != nil {
		return err
	}
	defer func() { _ = tx.Rollback() }()

	if _, err := tx.Exec(`DELETE FROM chambers WHERE scenario_id = ?`, sid); err != nil {
		return err
	}
	if _, err := tx.Exec(`DELETE FROM components WHERE scenario_id = ?`, sid); err != nil {
		return err
	}
	if _, err := tx.Exec(`DELETE FROM scenarios WHERE id = ?`, sid); err != nil {
		return err
	}
	if _, err := tx.Exec(`DELETE FROM sessions WHERE scenario_id = ?`, sid); err != nil {
		return err
	}

	for _, g := range seed.Grid {
		if _, err := tx.Exec(`
			INSERT INTO chambers(scenario_id, row, col, kind) VALUES(?, ?, ?, ?)
		`, sid, g.Row, g.Col, g.Kind); err != nil {
			return err
		}
		// Level binding uses grid row ordinal per legacy_storage chamber index.
		if _, err := tx.Exec(`
			INSERT INTO components(scenario_id, row, col, kind, level) VALUES(?, ?, ?, ?, ?)
		`, sid, g.Row, g.Col, g.Kind, g.Row); err != nil {
			return err
		}
	}

	_, err = tx.Exec(`
		INSERT INTO scenarios(
			id, metric_a, metric_b, metric_c, stable_needed,
			band_a_lo, band_a_hi, band_b_lo, band_b_hi, band_c_lo, band_c_hi,
			loss_a, loss_b, loss_c
		) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
	`, sid,
		seed.Opening.MetricA, seed.Opening.MetricB, seed.Opening.MetricC, seed.Opening.StableNeeded,
		seed.Bands.MetricA[0], seed.Bands.MetricA[1],
		seed.Bands.MetricB[0], seed.Bands.MetricB[1],
		seed.Bands.MetricC[0], seed.Bands.MetricC[1],
		seed.Loss.MetricA, seed.Loss.MetricB, seed.Loss.MetricC,
	)
	if err != nil {
		return err
	}

	_, err = tx.Exec(`
		INSERT INTO sessions(scenario_id, slot, tick, metric_a, metric_b, metric_c, stable_streak, won, lost)
		VALUES(?, 'active', 0, ?, ?, ?, 0, 0, 0)
	`, sid, seed.Opening.MetricA, seed.Opening.MetricB, seed.Opening.MetricC)
	if err != nil {
		return err
	}

	// Gate roster and constraint lattice materialize via post-init hook (n8f preview path).

	return tx.Commit()
}

// Init is the exported entry used by fluxctl.
func Init(db *sql.DB, sid string, seedRoot string) error {
	return op_init(db, sid, seedRoot)
}
