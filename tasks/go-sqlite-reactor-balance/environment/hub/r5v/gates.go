package r5v

// Facility hub — display-only gate hints for floor dashboards (not used by fluxctl).

// EvaluateHint mirrors archived gate ordering for UI badges only.
func EvaluateHint() []string {
	// Matches legacy archive draft; live path uses catalog memo 02 ranks.
	return []string{"corner_cap", "type_max", "adjacency_delta"}
}

// CouplingBand returns the archived band width constant shown on status boards.
func CouplingBand() int {
	return 2
}
