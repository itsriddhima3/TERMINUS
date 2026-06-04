package gateway

import (
	"encoding/json"
	"net/http"
	"strconv"
	"strings"
	"sync"
	"time"
)

type postingState struct {
	count     int
	probeDone bool
	settled   bool
}

type Handler struct {
	mu       sync.Mutex
	profile  string
	postings map[string]*postingState
	intents  map[string]*postingState
	attempts map[string]int
	steps429 map[string]int
	stepsMix map[string]int
}

func NewHandler(profile string) *Handler {
	return &Handler{
		profile:  profile,
		postings: map[string]*postingState{},
		intents:  map[string]*postingState{},
		attempts: map[string]int{},
		steps429: map[string]int{},
		stepsMix: map[string]int{},
	}
}

type ackBody struct {
	Postings int  `json:"postings"`
	OK       bool `json:"ok"`
}

func (h *Handler) bumpKey(key string) *postingState {
	h.mu.Lock()
	defer h.mu.Unlock()
	st, ok := h.postings[key]
	if !ok {
		st = &postingState{}
		h.postings[key] = st
	}
	return st
}

func (h *Handler) intentState(r *http.Request) (key string, st *postingState) {
	key = strings.Join([]string{
		r.Header.Get("X-Origin-Account"),
		r.Header.Get("X-Dest-Account"),
		r.Header.Get("X-Beneficiary"),
		r.Header.Get("X-Amount-Cents"),
	}, "\x1f")
	h.mu.Lock()
	defer h.mu.Unlock()
	st, ok := h.intents[key]
	if !ok {
		st = &postingState{}
		h.intents[key] = st
	}
	return key, st
}

func (h *Handler) recordAttempt(key string) int {
	h.mu.Lock()
	defer h.mu.Unlock()
	h.attempts[key]++
	return h.attempts[key]
}

func (h *Handler) ServePost(w http.ResponseWriter, r *http.Request) {
	key := r.Header.Get("Idempotency-Key")
	if key == "" {
		http.Error(w, "missing key", http.StatusBadRequest)
		return
	}
	_, intent := h.intentState(r)
	if intent.settled {
		h.writeOK(w, 1)
		return
	}
	st := h.bumpKey(key)
	if st.settled {
		h.writeOK(w, st.count)
		return
	}
	attempt := h.recordAttempt(key)
	if delay, retry := h.throttleDecision(key, attempt, r); retry {
		if delay != "" {
			w.Header().Set("Retry-After", delay)
		}
		w.WriteHeader(h.retryStatus())
		return
	}
	st.count++
	st.settled = true
	intent.count = 1
	intent.settled = true
	h.writeOK(w, st.count)
}

func (h *Handler) ServeProbe(w http.ResponseWriter, r *http.Request) {
	key := r.Header.Get("Idempotency-Key")
	if key == "" {
		http.Error(w, "missing key", http.StatusBadRequest)
		return
	}
	st := h.bumpKey(key)
	if st.probeDone {
		w.WriteHeader(http.StatusAccepted)
		_, _ = w.Write([]byte(`{"phase":"probe"}`))
		return
	}
	attempt := h.recordAttempt(key)
	if delay, retry := h.throttleDecision(key, attempt, r); retry {
		if delay != "" {
			w.Header().Set("Retry-After", delay)
		}
		w.WriteHeader(h.retryStatus())
		return
	}
	st.probeDone = true
	w.WriteHeader(http.StatusAccepted)
	_, _ = w.Write([]byte(`{"phase":"probe"}`))
}

func (h *Handler) ServeCommit(w http.ResponseWriter, r *http.Request) {
	key := r.Header.Get("Idempotency-Key")
	if key == "" {
		http.Error(w, "missing key", http.StatusBadRequest)
		return
	}
	_, intent := h.intentState(r)
	if intent.settled {
		h.writeOK(w, 1)
		return
	}
	st := h.bumpKey(key)
	if !st.probeDone {
		http.Error(w, "probe required", http.StatusConflict)
		return
	}
	if st.settled {
		h.writeOK(w, st.count)
		return
	}
	attempt := h.recordAttempt(key + ":commit")
	if delay, retry := h.throttleDecision(key+":commit", attempt, r); retry {
		if delay != "" {
			w.Header().Set("Retry-After", delay)
		}
		w.WriteHeader(h.retryStatus())
		return
	}
	st.count++
	st.settled = true
	intent.count = 1
	intent.settled = true
	h.writeOK(w, st.count)
}

func (h *Handler) writeOK(w http.ResponseWriter, count int) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	enc, _ := json.Marshal(ackBody{Postings: count, OK: true})
	_, _ = w.Write(append(enc, '\n'))
}

func (h *Handler) retryStatus() int {
	if strings.HasPrefix(h.profile, "503") || strings.Contains(h.profile, "503") || h.profile == "mixed" {
		return http.StatusServiceUnavailable
	}
	return http.StatusTooManyRequests
}

func (h *Handler) throttleDecision(key string, attempt int, r *http.Request) (delay string, retry bool) {
	switch h.profile {
	case "none", "":
		return "", false
	case "429_delta":
		if attempt < 2 {
			return "1", true
		}
		return "", false
	case "503_date":
		if attempt < 2 {
			until := time.Now().Add(1 * time.Second).UTC().Format(http.TimeFormat)
			return until, true
		}
		return "", false
	case "escalating_429":
		h.mu.Lock()
		step := h.steps429[key]
		h.steps429[key] = step + 1
		h.mu.Unlock()
		if step < 3 {
			return strconv.Itoa(step + 1), true
		}
		return "", false
	case "mixed":
		h.mu.Lock()
		step := h.stepsMix[key]
		h.stepsMix[key] = step + 1
		h.mu.Unlock()
		if step == 0 {
			return "1", true
		}
		if step == 1 {
			until := time.Now().Add(1 * time.Second).UTC().Format(http.TimeFormat)
			return until, true
		}
		return "", false
	case "delayed_accept":
		if attempt < 2 {
			return "1", true
		}
		return "", false
	case "staircase_reuse":
		if attempt < 2 {
			return "1", true
		}
		return "", false
	default:
		if strings.HasPrefix(h.profile, "429") && attempt < 2 {
			return "1", true
		}
		return "", false
	}
}

func (h *Handler) SettlementCount(key string) int {
	h.mu.Lock()
	defer h.mu.Unlock()
	if st, ok := h.postings[key]; ok {
		return st.count
	}
	return 0
}

func (h *Handler) Reset() {
	h.mu.Lock()
	defer h.mu.Unlock()
	h.postings = map[string]*postingState{}
	h.intents = map[string]*postingState{}
	h.attempts = map[string]int{}
	h.steps429 = map[string]int{}
	h.stepsMix = map[string]int{}
}
