package m9q

const (
	SchemaVersion     = 1
	ReuseWindowHours  = 24
	MaxRetryAttempts  = 12
	ProbeHeader       = "X-Probe-Phase"
	CommitHeader      = "X-Commit-Phase"
	IdempotencyHeader = "Idempotency-Key"
	OriginHeader      = "X-Origin-Account"
	DestHeader        = "X-Dest-Account"
	BeneficiaryHeader = "X-Beneficiary"
	AmountHeader      = "X-Amount-Cents"
)
