package t7m

import (
	"net/http"
	"time"
)

func PhaseB3(h http.Header, code int) (wait time.Duration, more bool) {
	return phase_b3(h, code)
}
