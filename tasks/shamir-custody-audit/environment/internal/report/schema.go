package report

// AuditEntry is the per-session record in the output report.
type AuditEntry struct {
	SessionID          string   `json:"session_id"`
	SlotsLoaded        int      `json:"slots_loaded"`
	ApprovalsLinked    int      `json:"approvals_linked"`
	ReconstructStatus  string   `json:"reconstruction_status"`
	SecretFingerprint  *string  `json:"secret_fingerprint"`
	ThresholdMet       bool     `json:"threshold_met"`
	QuorumValid        bool     `json:"quorum_valid"`
	PolicyViolations   []string `json:"policy_violations"`
	VerificationStatus string   `json:"verification_status"`
}

// Report is the root object written to the output file.
type Report struct {
	AuditResults []AuditEntry `json:"audit_results"`
}
