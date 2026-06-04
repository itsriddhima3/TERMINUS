package policy

import "custody-audit-tool/internal/types"

// checkPair returns true if the slot set satisfies all cannot_coexist
// tier constraints defined in the pair map.
func checkPair(slots []types.SlotRecord, pm pairMap) bool {
	for _, pair := range pm.cannotCoexist {
		if tierPresent(slots, pair.Alpha) || tierPresent(slots, pair.Beta) {
			return false
		}
	}
	return true
}

// Violations returns a list of policy violation descriptions for the session.
// An empty slice indicates no violations were detected.
func Violations(slots []types.SlotRecord, pm pairMap) []string {
	var vs []string
	for _, pair := range pm.cannotCoexist {
		if tierPresent(slots, pair.Alpha) || tierPresent(slots, pair.Beta) {
			vs = append(vs, "cannot_coexist:"+pair.Alpha+"+"+pair.Beta)
		}
	}
	return vs
}

// QuorumValid returns true when the participating slots pass all policy
// constraints defined in the pair map.
func QuorumValid(slots []types.SlotRecord, constraints []types.TierConstraint) bool {
	pm := buildPairMap(constraints)
	return checkPair(slots, pm)
}
