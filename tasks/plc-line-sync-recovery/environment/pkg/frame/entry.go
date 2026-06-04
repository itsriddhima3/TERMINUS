package frame

// Row is one PLC cycle log line from a station segment.
type Row struct {
	Seq     uint32 `json:"seq"`
	Slot    uint32 `json:"slot"`
	Epoch   uint32 `json:"epoch"`
	Gen     uint32 `json:"gen"`
	WallMS  int64  `json:"wall_ms"`
	Ingest  int64  `json:"ingest_ms"`
	Payload string `json:"payload"`
	Answer  string `json:"answer"`
	CRC     uint16 `json:"crc"`
	TTLLeft uint32 `json:"ttl_left"`
	Stamp   string `json:"origin_stamp"`
	Member  string `json:"member"`
}

// SeqKey returns the cache slot index for grouping.
func (r Row) SeqKey() uint32 {
	if r.Seq != 0 {
		return r.Seq
	}
	return r.Slot
}

// AnswerText returns the stored answer body.
func (r Row) AnswerText() string {
	if r.Payload != "" {
		return r.Payload
	}
	return r.Answer
}

// TTL returns ttl_left with a deterministic fallback.
func (r Row) TTL() uint32 {
	if r.TTLLeft != 0 {
		return r.TTLLeft
	}
	return 300 - (r.SeqKey() % 50)
}
