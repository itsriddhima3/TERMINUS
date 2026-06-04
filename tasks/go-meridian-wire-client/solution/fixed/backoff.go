package t7m

import (
	"net/http"
	"strconv"
	"time"
)

func phase_b3(h http.Header, code int) (wait time.Duration, more bool) {
	if code != 429 && code != 503 {
		return 0, false
	}
	raw := h.Get("Retry-After")
	if raw == "" {
		return time.Second, true
	}
	if sec, err := strconv.Atoi(raw); err == nil && sec > 0 {
		return time.Duration(sec) * time.Second, true
	}
	if when, err := http.ParseTime(raw); err == nil {
		d := time.Until(when)
		if d < 0 {
			d = 0
		}
		if d == 0 {
			d = time.Millisecond
		}
		return d, true
	}
	return 0, false
}
