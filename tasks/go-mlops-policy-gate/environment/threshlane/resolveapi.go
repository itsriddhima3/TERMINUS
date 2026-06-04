package threshlane

// Resolve loads annex bands for a bound family.
func Resolve(fam int, tier string, m map[string]float64) (BandSet, error) {
	return phase_t2(fam, tier, m, "primary")
}
