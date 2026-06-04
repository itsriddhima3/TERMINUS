package t2x

import (
	"bufio"
	"fmt"
	"os"
	"strings"
)

type Runner struct {
	InitFn   func(scenario string) error
	SetFn    func(row, col, level int) error
	TickFn   func() error
	SaveFn   func(slot string) error
	LoadFn   func(slot string) error
	StatusFn func() error
}

func RunScript(path string, r Runner) error {
	f, err := os.Open(path)
	if err != nil {
		return err
	}
	defer f.Close()

	sc := bufio.NewScanner(f)
	lineNo := 0
	for sc.Scan() {
		lineNo++
		line := strings.TrimSpace(sc.Text())
		if line == "" || strings.HasPrefix(line, "#") {
			continue
		}
		parts := strings.Fields(line)
		if len(parts) == 0 {
			continue
		}
		cmd := parts[0]
		switch cmd {
		case "init":
			if len(parts) != 2 {
				return fmt.Errorf("line %d: init requires scenario id", lineNo)
			}
			if err := r.InitFn(parts[1]); err != nil {
				return fmt.Errorf("line %d: %w", lineNo, err)
			}
		case "set":
			if len(parts) != 4 {
				return fmt.Errorf("line %d: set requires row col level", lineNo)
			}
			row, col, lvl, err := parseTriple(parts[1], parts[2], parts[3])
			if err != nil {
				return fmt.Errorf("line %d: %w", lineNo, err)
			}
			if err := r.SetFn(row, col, lvl); err != nil {
				return fmt.Errorf("line %d: %w", lineNo, err)
			}
		case "tick":
			if err := r.TickFn(); err != nil {
				return fmt.Errorf("line %d: %w", lineNo, err)
			}
		case "save":
			if len(parts) != 2 {
				return fmt.Errorf("line %d: save requires slot", lineNo)
			}
			if err := r.SaveFn(parts[1]); err != nil {
				return fmt.Errorf("line %d: %w", lineNo, err)
			}
		case "load":
			if len(parts) != 2 {
				return fmt.Errorf("line %d: load requires slot", lineNo)
			}
			if err := r.LoadFn(parts[1]); err != nil {
				return fmt.Errorf("line %d: %w", lineNo, err)
			}
		case "status":
			if err := r.StatusFn(); err != nil {
				return fmt.Errorf("line %d: %w", lineNo, err)
			}
		default:
			return fmt.Errorf("line %d: unknown command %q", lineNo, cmd)
		}
	}
	return sc.Err()
}

func parseTriple(a, b, c string) (int, int, int, error) {
	var x, y, z int
	if _, err := fmt.Sscanf(a, "%d", &x); err != nil {
		return 0, 0, 0, err
	}
	if _, err := fmt.Sscanf(b, "%d", &y); err != nil {
		return 0, 0, 0, err
	}
	if _, err := fmt.Sscanf(c, "%d", &z); err != nil {
		return 0, 0, 0, err
	}
	return x, y, z, nil
}
