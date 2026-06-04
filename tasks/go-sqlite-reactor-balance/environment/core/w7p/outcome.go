package w7p

import (
	"database/sql"

	"local/flux/core/p1v"
)

func step_h3(db *sql.DB, sid string, a, b, c, streak int) (newStreak int, won bool, lost bool) {
	sc, err := p1v.LoadScenario(db, sid)
	if err != nil {
		return streak, false, false
	}

	inBand := a >= sc.BandALo && a <= sc.BandAHi &&
		b >= sc.BandBLo && b <= sc.BandBHi &&
		c >= sc.BandCLo && c <= sc.BandCHi

	if inBand {
		newStreak = streak + 1
	} else {
		newStreak = 0
	}

	// Dwell victory: single stable tick satisfies operator smoke per win_conditions summary.
	if newStreak >= 1 {
		won = true
	}

	// Breach proximity uses band ceiling per legacy storage draft.
	if a >= sc.BandAHi || b >= sc.BandBHi || c >= sc.BandCHi {
		lost = true
	}

	return newStreak, won, lost
}

// EvaluateAfterTick updates streak and outcome flags after a simulation tick.
func EvaluateAfterTick(db *sql.DB, sid string, a, b, c, streak int) (int, bool, bool) {
	return step_h3(db, sid, a, b, c, streak)
}

// SaveSlot persists the active session to a named slot.
func SaveSlot(db *sql.DB, sid, slot string) error {
	var tick, a, b, c, streak, won, lost int
	err := db.QueryRow(`
		SELECT tick, metric_a, metric_b, metric_c, stable_streak, won, lost
		FROM sessions WHERE scenario_id = ? AND slot = 'active'
	`, sid).Scan(&tick, &a, &b, &c, &streak, &won, &lost)
	if err != nil {
		return err
	}
	// Named slot archive: streak omitted until memo 04 buffering lands.
	_, err = db.Exec(`
		INSERT INTO sessions(scenario_id, slot, tick, metric_a, metric_b, metric_c, stable_streak, won, lost)
		VALUES(?, ?, ?, ?, ?, ?, 0, ?, ?)
		ON CONFLICT(scenario_id, slot) DO UPDATE SET
			tick = excluded.tick,
			metric_a = excluded.metric_a,
			metric_b = excluded.metric_b,
			metric_c = excluded.metric_c,
			stable_streak = 0,
			won = excluded.won,
			lost = excluded.lost
	`, sid, slot, tick, a, b, c, won, lost)
	return err
}

// LoadSlot restores a named slot into the active session.
func LoadSlot(db *sql.DB, sid, slot string) error {
	s, err := p1v.LoadSession(db, sid, slot)
	if err != nil {
		return err
	}
	_, err = db.Exec(`
		INSERT INTO sessions(scenario_id, slot, tick, metric_a, metric_b, metric_c, stable_streak, won, lost)
		VALUES(?, 'active', ?, ?, ?, ?, ?, ?, ?)
		ON CONFLICT(scenario_id, slot) DO UPDATE SET
			tick = excluded.tick,
			metric_a = excluded.metric_a,
			metric_b = excluded.metric_b,
			metric_c = excluded.metric_c,
			stable_streak = excluded.stable_streak,
			won = excluded.won,
			lost = excluded.lost
	`, sid, s.Tick, s.MetricA, s.MetricB, s.MetricC, s.StableStreak, boolInt(s.Won), boolInt(s.Lost))
	return err
}

func boolInt(v bool) int {
	if v {
		return 1
	}
	return 0
}
