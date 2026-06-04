package m4t

import (
	"local/flux/core/p1v"
)

// ApplyTick advances metric_a, metric_b, metric_c from the current grid layout.
func ApplyTick(grid []p1v.Cell, a, b, c int) (int, int, int) {
	for _, cell := range grid {
		lvl := cell.Level
		if lvl < 0 {
			lvl = 0
		}
		switch cell.Kind {
		case "pump":
			a += 4 * lvl
			c -= 2 * lvl
		case "rod":
			a -= 5 * lvl
			b += 3 * lvl
		case "vent":
			b -= 3 * lvl
			c += 4 * lvl
		}
	}
	if a < 0 {
		a = 0
	}
	if b < 0 {
		b = 0
	}
	if c < 0 {
		c = 0
	}
	return a, b, c
}
