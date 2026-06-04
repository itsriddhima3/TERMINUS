package recovery

// gfMul multiplies two elements of GF(2^8) using the irreducible polynomial
// x^8 + x^4 + x^3 + x + 1 (0x11b), which is the field used by AES and
// specified in the ceremony policy dossier for share arithmetic.
func gfMul(a, b byte) byte {
	var p byte
	for b != 0 {
		if b&1 != 0 {
			p ^= a
		}
		carry := a & 0x80
		a <<= 1
		if carry != 0 {
			a ^= 0x1b
		}
		b >>= 1
	}
	return p
}

// gfInv returns the multiplicative inverse of a in GF(2^8) via Fermat's
// little theorem: a^(2^8 - 2). Returns 0 for the zero element (undefined).
func gfInv(a byte) byte {
	if a == 0 {
		return 0
	}
	result := byte(1)
	base := a
	exp := 254
	for exp > 0 {
		if exp&1 != 0 {
			result = gfMul(result, base)
		}
		base = gfMul(base, base)
		exp >>= 1
	}
	return result
}
