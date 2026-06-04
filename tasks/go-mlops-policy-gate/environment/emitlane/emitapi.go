package emitlane

import (
	"fmt"

	"gatemod/threshlane"
)

// Emit builds the verdict row for resolved bands.
func Emit(bs threshlane.BandSet, m map[string]float64, fam int) (VerdictRow, error) {
	meta := map[string]string{"fam": fmt.Sprintf("%d", fam)}
	return step_k7(bs, m, meta)
}
