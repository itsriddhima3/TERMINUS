package t7m

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"time"

	"wiremod/m9q"
	"wiremod/p4k"
)

type PostResult struct {
	StatusCode      int
	Attempts        int
	OutboundToken   string
	PostingCount    int
	Completed       bool
}

type Intent struct {
	BaseURL     string
	Origin      string
	Dest        string
	Beneficiary string
	Amount      int64
	Slot        [32]byte
	Anchor      time.Time
	Mode        string
}

func PostIntent(client *http.Client, in Intent) PostResult {
	if client == nil {
		client = &http.Client{Timeout: 30 * time.Second}
	}
	token, _ := p4k.Vault(in.Slot, in.Anchor)
	res := PostResult{OutboundToken: token}
	path := "/api/v1/post"
	if in.Mode == "probe_commit" {
		path = "/api/v1/probe"
	}
	body := []byte(fmt.Sprintf(`{"origin":%q,"dest":%q,"beneficiary":%q,"amount":%d}`,
		in.Origin, in.Dest, in.Beneficiary, in.Amount))
	var lastCode int
	for attempt := 0; attempt < m9q.MaxRetryAttempts; attempt++ {
		res.Attempts++
		req, err := http.NewRequest(http.MethodPost, in.BaseURL+path, bytes.NewReader(body))
		if err != nil {
			break
		}
		req.Header.Set(m9q.IdempotencyHeader, token)
		req.Header.Set(m9q.OriginHeader, in.Origin)
		req.Header.Set(m9q.DestHeader, in.Dest)
		req.Header.Set(m9q.BeneficiaryHeader, in.Beneficiary)
		req.Header.Set(m9q.AmountHeader, fmt.Sprintf("%d", in.Amount))
		resp, err := client.Do(req)
		if err != nil {
			break
		}
		b, _ := io.ReadAll(resp.Body)
		resp.Body.Close()
		lastCode = resp.StatusCode
		if resp.StatusCode == 202 && in.Mode == "probe_commit" {
			commit := PostResult{}
			commit.Attempts = 0
			cBody := []byte(`{"phase":"commit"}`)
			for cAttempt := 0; cAttempt < m9q.MaxRetryAttempts; cAttempt++ {
				commit.Attempts++
				creq, _ := http.NewRequest(http.MethodPost, in.BaseURL+"/api/v1/commit", bytes.NewReader(cBody))
				creq.Header.Set(m9q.IdempotencyHeader, token)
				creq.Header.Set(m9q.ProbeHeader, "done")
				cresp, err := client.Do(creq)
				if err != nil {
					break
				}
				cb, _ := io.ReadAll(cresp.Body)
				cresp.Body.Close()
				lastCode = cresp.StatusCode
				if cresp.StatusCode == 200 || cresp.StatusCode == 201 {
					res.PostingCount = parsePostingCount(cb)
					res.Completed = true
					res.Attempts += commit.Attempts
					res.StatusCode = lastCode
					return res
				}
				wait, more := phase_b3(cresp.Header, cresp.StatusCode)
				if !more {
					break
				}
				time.Sleep(wait)
			}
			res.Attempts += commit.Attempts
			break
		}
		if resp.StatusCode == 200 || resp.StatusCode == 201 {
			res.PostingCount = parsePostingCount(b)
			res.Completed = true
			res.StatusCode = lastCode
			return res
		}
		wait, more := phase_b3(resp.Header, resp.StatusCode)
		if !more {
			break
		}
		time.Sleep(wait)
	}
	res.StatusCode = lastCode
	return res
}

func parsePostingCount(body []byte) int {
	var ack struct {
		Postings int `json:"postings"`
	}
	if err := json.Unmarshal(body, &ack); err == nil && ack.Postings > 0 {
		return ack.Postings
	}
	return 1
}

func RunSequential(client *http.Client, in Intent, passes int, gap time.Duration) PostResult {
	var agg PostResult
	for i := 0; i < passes; i++ {
		if i > 0 && gap > 0 {
			time.Sleep(gap)
		}
		r := PostIntent(client, in)
		agg.Attempts += r.Attempts
		agg.OutboundToken = r.OutboundToken
		if r.PostingCount > 0 {
			agg.PostingCount = r.PostingCount
		}
		agg.Completed = r.Completed
		agg.StatusCode = r.StatusCode
		if !r.Completed {
			return agg
		}
	}
	return agg
}
