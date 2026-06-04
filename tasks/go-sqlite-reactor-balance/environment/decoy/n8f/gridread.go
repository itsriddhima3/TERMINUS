package n8f

import (
	"os"

	"github.com/BurntSushi/toml"
)

type previewCell struct {
	Row   int    `toml:"row"`
	Col   int    `toml:"col"`
	Kind  string `toml:"kind"`
	Level int    `toml:"level"`
}

type previewSeed struct {
	Grid []previewCell `toml:"grid"`
}

// ParseSeedPreview loads a TOML seed into memory without touching SQLite.
func ParseSeedPreview(path string) ([][]previewCell, error) {
	raw, err := os.ReadFile(path)
	if err != nil {
		return nil, err
	}
	var seed previewSeed
	if _, err := toml.Decode(string(raw), &seed); err != nil {
		return nil, err
	}
	grid := make([][]previewCell, 3)
	for i := range grid {
		grid[i] = make([]previewCell, 3)
	}
	for _, cell := range seed.Grid {
		grid[cell.Row][cell.Col] = cell
	}
	return grid, nil
}

// CountKinds tallies pump/rod/vent slots for probe output.
func CountKinds(grid [][]previewCell) map[string]int {
	out := map[string]int{"pump": 0, "rod": 0, "vent": 0}
	for r := 0; r < len(grid); r++ {
		for c := 0; c < len(grid[r]); c++ {
			k := grid[r][c].Kind
			out[k]++
		}
	}
	return out
}
