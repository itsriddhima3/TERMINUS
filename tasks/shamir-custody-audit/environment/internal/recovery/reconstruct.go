package recovery

import (
	"encoding/hex"
	"fmt"

	"custody-audit-tool/internal/types"
)

// Result carries the outcome of a reconstruction attempt.
type Result struct {
	Secret []byte
	Status string
}

// StatusSuccess indicates the secret was reconstructed successfully.
const StatusSuccess = "success"

// StatusInsufficient indicates too few shares were submitted.
const StatusInsufficient = "insufficient_shares"

// StatusEmpty indicates no shares were found for this session.
const StatusEmpty = "no_shares"

// Reconstruct attempts to recover the session secret from the submitted shares.
// It uses Lagrange interpolation in GF(2^8) over the per-byte share columns.
func Reconstruct(submissions []types.SubmissionRecord, threshold int) Result {
	if len(submissions) == 0 {
		return Result{Status: StatusEmpty}
	}
	if len(submissions) < threshold {
		return Result{Status: StatusInsufficient}
	}

	pts := make([]fieldPt, 0, len(submissions))
	for _, sub := range submissions {
		raw, err := hex.DecodeString(sub.CoordYHex)
		if err != nil {
			return Result{Status: fmt.Sprintf("decode_error: %v", err)}
		}
		pts = append(pts, fieldPt{X: byte(sub.CoordX), Y: raw})
	}

	secret, err := combinePts(pts, threshold)
	if err != nil {
		return Result{Status: StatusInsufficient}
	}
	return Result{Secret: secret, Status: StatusSuccess}
}
