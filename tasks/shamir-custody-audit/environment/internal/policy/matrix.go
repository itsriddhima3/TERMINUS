package policy

import "custody-audit-tool/internal/types"

// pairMap indexes tier constraints by their rule kind for fast lookups.
type pairMap struct {
	cannotCoexist []tierPair
}

// tierPair is a two-element entry from the tier_constraints table.
type tierPair struct {
	Alpha string
	Beta  string
}

// buildPairMap constructs a pairMap from the given constraint slice.
func buildPairMap(constraints []types.TierConstraint) pairMap {
	pm := pairMap{}
	for _, c := range constraints {
		switch c.RuleKind {
		case "cannot_coexist":
			pm.cannotCoexist = append(pm.cannotCoexist, tierPair{Alpha: c.TierAlpha, Beta: c.TierBeta})
		}
	}
	return pm
}

// tierPresent returns true if any entry in slots has the given auth_tier.
func tierPresent(slots []types.SlotRecord, tier string) bool {
	for _, s := range slots {
		if s.AuthTier == tier {
			return true
		}
	}
	return false
}
