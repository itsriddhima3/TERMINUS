package q8n

import "time"

// IntervalStub applies a fixed pause unrelated to response metadata.
func IntervalStub(n int) time.Duration {
	if n <= 0 {
		return 250 * time.Millisecond
	}
	return time.Duration(n) * 200 * time.Millisecond
}
