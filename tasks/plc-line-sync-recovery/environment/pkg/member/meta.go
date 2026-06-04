package member

// Profile holds per-station radio lag and commit watermark metadata.
type Profile struct {
	MemberID       string `json:"member_id"`
	ClockOffsetMS  int64  `json:"clock_offset_ms"`
	FreezeSeq      uint32 `json:"freeze_seq"`
}
