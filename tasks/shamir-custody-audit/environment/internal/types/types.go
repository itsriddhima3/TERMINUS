package types

// SessionRecord represents a recovery ceremony session row from the database.
type SessionRecord struct {
	SessionID   string
	InitiatedAt int64
	ThresholdK  int
	TotalSlots  int
}

// SlotRecord represents a custodian slot registration within a session.
type SlotRecord struct {
	SlotID      string
	SessionID   string
	SlotIndex   int
	CustodianID string
	AuthTier    string
}

// SubmissionRecord represents one share submitted by a custodian.
type SubmissionRecord struct {
	SubmissionID string
	SlotID       string
	CoordX       int
	CoordYHex    string
	SubmittedAt  int64
}

// ApprovalRecord records the endorsement of a submitted share.
type ApprovalRecord struct {
	ApprovalID   string
	SessionID    string
	ApprovedSlot string
	ApprovedBy   string
	ApprovedAt   int64
}

// TierConstraint describes a policy relationship between two authorization tiers.
type TierConstraint struct {
	ConstraintID string
	TierAlpha    string
	TierBeta     string
	RuleKind     string
}
