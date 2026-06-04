package c3s

import "context"

func CoalesceTrace(ctx context.Context, windows []int) int {
	total := 0
	for range windows {
		total++
		_ = ctx
	}
	return total
}
