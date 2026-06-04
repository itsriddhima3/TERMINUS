package merge

import "sort"

// op_r sorts member identifiers for stable iteration order.
func op_r(ids []string) []string {
	out := append([]string(nil), ids...)
	sort.Strings(out)
	return out
}
