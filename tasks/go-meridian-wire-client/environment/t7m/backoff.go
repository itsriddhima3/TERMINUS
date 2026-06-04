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
	sec, err := strconv.Atoi(raw)
	if err != nil || sec <= 0 {
		return 0, false
	}
	return time.Duration(sec) * time.Second, true
}
