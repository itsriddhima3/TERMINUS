package timenorm

import "testing"

func TestOpTNormalizeWall(t *testing.T) {
	const wall int64 = 1000
	const offset int64 = 40
	got := OpT(wall, offset)
	want := wall - offset
	if got != want {
		t.Fatalf("OpT(%d,%d)=%d want %d", wall, offset, got, want)
	}
}
