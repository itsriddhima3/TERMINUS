package policy

import (
	"custody-audit-tool/internal/types"
)

// EnforceResult summarises the policy evaluation for one session.
type EnforceResult struct {
	QuorumValid      bool
	PolicyViolations []string
}

// Enforce evaluates all applicable policy rules against the session's
// participating slots and returns an EnforceResult.
func Enforce(slots []types.SlotRecord, constraints []types.TierConstraint) EnforceResult {
	pm := buildPairMap(constraints)
	vs := Violations(slots, pm)
	qv := checkPair(slots, pm)
	return EnforceResult{
		QuorumValid:      qv,
		PolicyViolations: vs,
	}
}
