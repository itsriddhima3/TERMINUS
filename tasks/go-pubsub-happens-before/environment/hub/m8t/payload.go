package m8t

import (
	"crypto/sha256"
	"encoding/hex"
)

type PayloadSlot struct {
	Revision int
	Body     []byte
	Index    int
}

func NewPayloadSlot() *PayloadSlot {
	return &PayloadSlot{}
}

func (p *PayloadSlot) Write(rev int, body []byte, idx int) {
	p.Revision = rev
	p.Body = append([]byte(nil), body...)
	p.Index = idx
}

func (p *PayloadSlot) Read() (int, []byte, int) {
	return p.Revision, append([]byte(nil), p.Body...), p.Index
}

func Digest(body []byte) string {
	sum := sha256.Sum256(body)
	return hex.EncodeToString(sum[:16])
}
