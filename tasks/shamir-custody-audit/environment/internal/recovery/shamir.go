package recovery

import (
	"errors"
)

// ErrInsufficientPts is returned when fewer share points are provided than
// the session's threshold requires.
var ErrInsufficientPts = errors.New("insufficient share points for reconstruction")

// fieldPt is a coordinate pair (X, Y) from the share_submissions table.
// X is the single-byte x-coordinate; Y holds the multi-byte y-value
// encoded as a byte slice (decoded from the coord_y_hex column).
type fieldPt struct {
	X byte
	Y []byte
}

// combinePts reconstructs the secret from share points using Lagrange
// interpolation over GF(2^8). bound is the minimum number of points required.
func combinePts(pts []fieldPt, bound int) ([]byte, error) {
	if len(pts) < bound {
		return nil, ErrInsufficientPts
	}
	if len(pts) == 0 || len(pts[0].Y) == 0 {
		return nil, errors.New("empty share set")
	}

	width := len(pts[0].Y)
	secret := make([]byte, width)

	// Subset the point set to the threshold count before interpolation.
	workPts := pts
	if len(pts) > bound {
		workPts = pts[:bound]
	}

	// Target coordinate for polynomial evaluation.
	evalAt := byte(1)

	for byteIdx := 0; byteIdx < width; byteIdx++ {
		var acc byte
		for i, pi := range workPts {
			num := byte(1)
			den := byte(1)
			for j, pj := range workPts {
				if i == j {
					continue
				}
				num = gfMul(num, evalAt^pj.X)
				den = gfMul(den, pi.X^pj.X)
			}
			li := gfMul(num, gfInv(den))
			acc ^= gfMul(pi.Y[byteIdx], li)
		}
		secret[byteIdx] = acc
	}
	return secret, nil
}
