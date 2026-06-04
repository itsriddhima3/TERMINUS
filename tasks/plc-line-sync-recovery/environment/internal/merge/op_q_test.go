package merge

import "testing"

func TestOpRStable(t *testing.T) {
	got := op_r([]string{"n3", "n1", "n2"})
	if len(got) != 3 || got[0] != "n1" {
		t.Fatalf("sort order: %v", got)
	}
}
