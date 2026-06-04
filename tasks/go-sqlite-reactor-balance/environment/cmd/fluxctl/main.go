package main

import (
	"database/sql"
	"encoding/json"
	"flag"
	"fmt"
	"os"
	"path/filepath"

	"local/flux/core/k9m"
	"local/flux/core/m4t"
	"local/flux/core/p1v"
	"local/flux/core/r2n"
	"local/flux/core/t2x"
	"local/flux/core/w7p"
)

const (
	seedRoot = "/app/data/seeds"
	dbPath   = p1v.DefaultDBPath
)

var activeScenario = "SCN-Alpha"

type statusDoc struct {
	Scenario      string       `json:"scenario"`
	Tick          int          `json:"tick"`
	MetricA       int          `json:"metric_a"`
	MetricB       int          `json:"metric_b"`
	MetricC       int          `json:"metric_c"`
	StableStreak  int          `json:"stable_streak"`
	Won           bool         `json:"won"`
	Lost          bool         `json:"lost"`
	SchemaVersion int          `json:"schema_version"`
	Grid          [][]gridCell `json:"grid"`
}

type gridCell struct {
	Kind  string `json:"kind"`
	Level int    `json:"level"`
}

func main() {
	if len(os.Args) < 2 {
		usage()
		os.Exit(2)
	}
	cmd := os.Args[1]
	switch cmd {
	case "init":
		runInit(os.Args[2:])
	case "status":
		runStatus(os.Args[2:])
	case "set":
		runSet(os.Args[2:])
	case "tick":
		runTick()
	case "save":
		runSave(os.Args[2:])
	case "load":
		runLoad(os.Args[2:])
	case "run":
		runScript(os.Args[2:])
	default:
		fmt.Fprintf(os.Stderr, "unknown command %q\n", cmd)
		usage()
		os.Exit(2)
	}
}

func usage() {
	fmt.Fprintf(os.Stderr, "usage: fluxctl init --scenario <id>\n")
	fmt.Fprintf(os.Stderr, "       fluxctl status [--json]\n")
	fmt.Fprintf(os.Stderr, "       fluxctl set <row> <col> <level>\n")
	fmt.Fprintf(os.Stderr, "       fluxctl tick\n")
	fmt.Fprintf(os.Stderr, "       fluxctl save <slot>\n")
	fmt.Fprintf(os.Stderr, "       fluxctl load <slot>\n")
	fmt.Fprintf(os.Stderr, "       fluxctl run <script>\n")
}

func runInit(args []string) {
	fs := flag.NewFlagSet("init", flag.ExitOnError)
	scenario := fs.String("scenario", "", "scenario identifier")
	_ = fs.Parse(args)
	if *scenario == "" {
		fmt.Fprintln(os.Stderr, "init requires --scenario")
		os.Exit(2)
	}
	activeScenario = *scenario
	db, err := p1v.Open(dbPath)
	if err != nil {
		fail(err)
	}
	defer db.Close()
	if err := k9m.Init(db, *scenario, seedRoot); err != nil {
		fail(err)
	}
}

func runStatus(args []string) {
	fs := flag.NewFlagSet("status", flag.ExitOnError)
	asJSON := fs.Bool("json", false, "emit JSON")
	_ = fs.Parse(args)

	db, err := p1v.Open(dbPath)
	if err != nil {
		fail(err)
	}
	defer db.Close()

	doc, err := buildStatus(db, activeScenario)
	if err != nil {
		fail(err)
	}
	if !*asJSON {
		fmt.Printf("scenario=%s tick=%d a=%d b=%d c=%d streak=%d won=%v lost=%v\n",
			doc.Scenario, doc.Tick, doc.MetricA, doc.MetricB, doc.MetricC,
			doc.StableStreak, doc.Won, doc.Lost)
		return
	}
	enc := json.NewEncoder(os.Stdout)
	enc.SetIndent("", "  ")
	if err := enc.Encode(doc); err != nil {
		fail(err)
	}
}

func buildStatus(db *sql.DB, sid string) (*statusDoc, error) {
	var tick, a, b, c, streak int
	var won, lost int
	err := db.QueryRow(`
		SELECT tick, metric_a, metric_b, metric_c, stable_streak, won, lost
		FROM sessions WHERE scenario_id = ? AND slot = 'active'
	`, sid).Scan(&tick, &a, &b, &c, &streak, &won, &lost)
	if err != nil {
		return nil, err
	}

	verStr, _ := p1v.MetaGet(db, "schema_version")
	schemaVer := 0
	if verStr != "" {
		fmt.Sscanf(verStr, "%d", &schemaVer)
	}

	cells, err := p1v.LoadGrid(db, sid)
	if err != nil {
		return nil, err
	}
	grid := make([][]gridCell, 3)
	for i := range grid {
		grid[i] = make([]gridCell, 3)
	}
	for _, cell := range cells {
		grid[cell.Row][cell.Col] = gridCell{Kind: cell.Kind, Level: cell.Level}
	}

	return &statusDoc{
		Scenario:      sid,
		Tick:          tick,
		MetricA:       a,
		MetricB:       b,
		MetricC:       c,
		StableStreak:  streak,
		Won:           won == 1,
		Lost:          lost == 1,
		SchemaVersion: schemaVer,
		Grid:          grid,
	}, nil
}

func runSet(args []string) {
	if len(args) != 3 {
		fmt.Fprintln(os.Stderr, "set requires row col level")
		os.Exit(2)
	}
	var r, c, lvl int
	if _, err := fmt.Sscanf(args[0], "%d", &r); err != nil {
		fail(err)
	}
	if _, err := fmt.Sscanf(args[1], "%d", &c); err != nil {
		fail(err)
	}
	if _, err := fmt.Sscanf(args[2], "%d", &lvl); err != nil {
		fail(err)
	}

	db, err := p1v.Open(dbPath)
	if err != nil {
		fail(err)
	}
	defer db.Close()

	if err := r2n.ValidateMove(db, activeScenario, r, c, lvl); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	if err := p1v.SetLevel(db, activeScenario, r, c, lvl); err != nil {
		fail(err)
	}
}

func runTick() {
	db, err := p1v.Open(dbPath)
	if err != nil {
		fail(err)
	}
	defer db.Close()

	var tick, a, b, c, streak int
	var won, lost int
	err = db.QueryRow(`
		SELECT tick, metric_a, metric_b, metric_c, stable_streak, won, lost
		FROM sessions WHERE scenario_id = ? AND slot = 'active'
	`, activeScenario).Scan(&tick, &a, &b, &c, &streak, &won, &lost)
	if err != nil {
		fail(err)
	}
	if won == 1 || lost == 1 {
		return
	}

	grid, err := p1v.LoadGrid(db, activeScenario)
	if err != nil {
		fail(err)
	}
	a, b, c = m4t.ApplyTick(grid, a, b, c)
	tick++

	newStreak, nowWon, nowLost := w7p.EvaluateAfterTick(db, activeScenario, a, b, c, streak)
	if err := p1v.UpdateMetrics(db, activeScenario, tick, a, b, c, newStreak, nowWon, nowLost); err != nil {
		fail(err)
	}
}

func runSave(args []string) {
	if len(args) != 1 {
		fmt.Fprintln(os.Stderr, "save requires slot name")
		os.Exit(2)
	}
	db, err := p1v.Open(dbPath)
	if err != nil {
		fail(err)
	}
	defer db.Close()
	if err := w7p.SaveSlot(db, activeScenario, args[0]); err != nil {
		fail(err)
	}
}

func runLoad(args []string) {
	if len(args) != 1 {
		fmt.Fprintln(os.Stderr, "load requires slot name")
		os.Exit(2)
	}
	db, err := p1v.Open(dbPath)
	if err != nil {
		fail(err)
	}
	defer db.Close()
	if err := w7p.LoadSlot(db, activeScenario, args[0]); err != nil {
		fail(err)
	}
}

func runScript(args []string) {
	if len(args) != 1 {
		fmt.Fprintln(os.Stderr, "run requires script path")
		os.Exit(2)
	}
	path := args[0]
	if !filepath.IsAbs(path) {
		path = filepath.Join("/app/data/transcripts", path)
	}

	runner := t2x.Runner{
		InitFn: func(scenario string) error {
			activeScenario = scenario
			db, err := p1v.Open(dbPath)
			if err != nil {
				return err
			}
			defer db.Close()
			return k9m.Init(db, scenario, seedRoot)
		},
		SetFn: func(row, col, level int) error {
			db, err := p1v.Open(dbPath)
			if err != nil {
				return err
			}
			defer db.Close()
			if err := r2n.ValidateMove(db, activeScenario, row, col, level); err != nil {
				return err
			}
			return p1v.SetLevel(db, activeScenario, row, col, level)
		},
		TickFn: func() error {
			runTick()
			return nil
		},
		SaveFn: func(slot string) error {
			db, err := p1v.Open(dbPath)
			if err != nil {
				return err
			}
			defer db.Close()
			return w7p.SaveSlot(db, activeScenario, slot)
		},
		LoadFn: func(slot string) error {
			db, err := p1v.Open(dbPath)
			if err != nil {
				return err
			}
			defer db.Close()
			return w7p.LoadSlot(db, activeScenario, slot)
		},
		StatusFn: func() error {
			runStatus([]string{"--json"})
			return nil
		},
	}
	if err := t2x.RunScript(path, runner); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}

func fail(err error) {
	fmt.Fprintln(os.Stderr, err)
	os.Exit(1)
}
