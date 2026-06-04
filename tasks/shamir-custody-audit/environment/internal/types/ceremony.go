package types

// CeremonyData bundles all database records for a single session.
type CeremonyData struct {
	Session     SessionRecord
	Slots       []SlotRecord
	Submissions []SubmissionRecord
	Approvals   []ApprovalRecord
}

// PolicyConfig holds parameters extracted from the ceremony policy dossier.
type PolicyConfig struct {
	InterpolationTarget byte
	FingerprintLength   int
	Constraints         []TierConstraint
}
