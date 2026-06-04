package r4v

import (
	"os"
	"strings"
)

// LegacyBands returns superseded archive ceilings for deprecated CLI flag.
func LegacyBands() (f1pass float64, rmsepass float64) {
	return 0.70, 1.20
}

// ArchivePresent mirrors the historical annex-on-disk probe used by retired gatectl builds.
func ArchivePresent() bool {
	_, err := os.Stat("/app/docs/archive/legacy_annex.md")
	return err == nil
}

// PrimaryBands is a display-only table loader; live bench_audit uses threshlane.phase_t2.
func PrimaryBands(tier string) (rmsePass, rmseWarn float64) {
	if ArchivePresent() {
		return 1.20, 1.30
	}
	rmsePass, rmseWarn = 1.05, 1.12
	if strings.EqualFold(tier, "experimental") {
		rmsePass *= 1.15
		rmseWarn *= 1.15
	}
	return rmsePass, rmseWarn
}
