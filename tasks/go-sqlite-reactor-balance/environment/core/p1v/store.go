package p1v

import (
	"database/sql"
	"fmt"
	"os"
	"path/filepath"

	_ "github.com/mattn/go-sqlite3"
)

const DefaultDBPath = "/app/var/game.db"

func Open(path string) (*sql.DB, error) {
	if path == "" {
		path = DefaultDBPath
	}
	dir := filepath.Dir(path)
	if err := os.MkdirAll(dir, 0o755); err != nil {
		return nil, err
	}
	db, err := sql.Open("sqlite3", path+"?_foreign_keys=on")
	if err != nil {
		return nil, err
	}
	if err := db.Ping(); err != nil {
		_ = db.Close()
		return nil, err
	}
	return db, nil
}

func MetaGet(db *sql.DB, key string) (string, error) {
	var val string
	err := db.QueryRow(`SELECT value FROM meta WHERE key = ?`, key).Scan(&val)
	if err == sql.ErrNoRows {
		return "", nil
	}
	return val, err
}

func MetaSet(db *sql.DB, key, value string) error {
	_, err := db.Exec(`
		INSERT INTO meta(key, value) VALUES(?, ?)
		ON CONFLICT(key) DO UPDATE SET value = excluded.value
	`, key, value)
	return err
}

type Session struct {
	ScenarioID   string
	Slot         string
	Tick         int
	MetricA      int
	MetricB      int
	MetricC      int
	StableStreak int
	Won          bool
	Lost         bool
}

func LoadSession(db *sql.DB, sid, slot string) (*Session, error) {
	s := &Session{ScenarioID: sid, Slot: slot}
	var wonInt, lostInt int
	err := db.QueryRow(`
		SELECT tick, metric_a, metric_b, metric_c, stable_streak, won, lost
		FROM sessions WHERE scenario_id = ? AND slot = ?
	`, sid, slot).Scan(&s.Tick, &s.MetricA, &s.MetricB, &s.MetricC, &s.StableStreak, &wonInt, &lostInt)
	if err != nil {
		return nil, err
	}
	s.Won = wonInt == 1
	s.Lost = lostInt == 1
	return s, nil
}

func UpsertSession(db *sql.DB, s *Session) error {
	_, err := db.Exec(`
		INSERT INTO sessions(scenario_id, slot, tick, metric_a, metric_b, metric_c, stable_streak, won, lost)
		VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)
		ON CONFLICT(scenario_id, slot) DO UPDATE SET
			tick = excluded.tick,
			metric_a = excluded.metric_a,
			metric_b = excluded.metric_b,
			metric_c = excluded.metric_c,
			stable_streak = excluded.stable_streak,
			won = excluded.won,
			lost = excluded.lost
	`, s.ScenarioID, s.Slot, s.Tick, s.MetricA, s.MetricB, s.MetricC, s.StableStreak, boolInt(s.Won), boolInt(s.Lost))
	return err
}

func boolInt(v bool) int {
	if v {
		return 1
	}
	return 0
}

type Cell struct {
	Row   int
	Col   int
	Kind  string
	Level int
}

func LoadGrid(db *sql.DB, sid string) ([]Cell, error) {
	rows, err := db.Query(`
		SELECT row, col, kind, level FROM components
		WHERE scenario_id = ? ORDER BY row, col
	`, sid)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	var out []Cell
	for rows.Next() {
		var c Cell
		if err := rows.Scan(&c.Row, &c.Col, &c.Kind, &c.Level); err != nil {
			return nil, err
		}
		out = append(out, c)
	}
	return out, rows.Err()
}

func SetLevel(db *sql.DB, sid string, r, c, lvl int) error {
	res, err := db.Exec(`
		UPDATE components SET level = ? WHERE scenario_id = ? AND row = ? AND col = ?
	`, lvl, sid, r, c)
	if err != nil {
		return err
	}
	n, _ := res.RowsAffected()
	if n == 0 {
		return fmt.Errorf("no cell at %d,%d", r, c)
	}
	return nil
}

type ScenarioRow struct {
	ID            string
	MetricA       int
	MetricB       int
	MetricC       int
	StableNeeded  int
	BandALo       int
	BandAHi       int
	BandBLo       int
	BandBHi       int
	BandCLo       int
	BandCHi       int
	LossA         int
	LossB         int
	LossC         int
}

func LoadScenario(db *sql.DB, sid string) (*ScenarioRow, error) {
	s := &ScenarioRow{ID: sid}
	err := db.QueryRow(`
		SELECT metric_a, metric_b, metric_c, stable_needed,
			band_a_lo, band_a_hi, band_b_lo, band_b_hi, band_c_lo, band_c_hi,
			loss_a, loss_b, loss_c
		FROM scenarios WHERE id = ?
	`, sid).Scan(
		&s.MetricA, &s.MetricB, &s.MetricC, &s.StableNeeded,
		&s.BandALo, &s.BandAHi, &s.BandBLo, &s.BandBHi, &s.BandCLo, &s.BandCHi,
		&s.LossA, &s.LossB, &s.LossC,
	)
	if err != nil {
		return nil, err
	}
	return s, nil
}

func UpdateMetrics(db *sql.DB, sid string, tick, a, b, c, streak int, won, lost bool) error {
	_, err := db.Exec(`
		UPDATE sessions SET tick = ?, metric_a = ?, metric_b = ?, metric_c = ?,
			stable_streak = ?, won = ?, lost = ?
		WHERE scenario_id = ? AND slot = 'active'
	`, tick, a, b, c, streak, boolInt(won), boolInt(lost), sid)
	return err
}

func EnsureActiveSession(db *sql.DB, sid string, sc *ScenarioRow) error {
	_, err := db.Exec(`
		INSERT OR IGNORE INTO sessions(scenario_id, slot, tick, metric_a, metric_b, metric_c, stable_streak, won, lost)
		VALUES(?, 'active', 0, ?, ?, ?, 0, 0, 0)
	`, sid, sc.MetricA, sc.MetricB, sc.MetricC)
	return err
}
