package emitlane

import (
	"fmt"

	"gatemod/m5q"
	"gatemod/threshlane"
)

type VerdictRow struct {
	Verdict    string   `json:"verdict"`
	RiskScore  int      `json:"risk_score"`
	CitedRules []string `json:"cited_rules"`
	Reasons    []string `json:"reasons"`
}

// step_k7 turns resolved bands and metrics into an output row.
func step_k7(bs threshlane.BandSet, m map[string]float64, meta map[string]string) (VerdictRow, error) {
	fam := 0
	if v, ok := meta["fam"]; ok {
		fmt.Sscanf(v, "%d", &fam)
	}
	sev, cites := threshlane.Rank_u9(fam, m, bs)
	label := "pass"
	risk := 10
	switch sev {
	case 1:
		label = "warn"
		risk = 30
	case 2:
		label = "fail"
		risk = 70
	}
	if bs.ProdNoWarn && label == "warn" && fam == m5q.FamEmb {
		label = "warn"
	}
	if fam == m5q.FamCls && label == "warn" {
		rr := m["rmse"] / m["baseline_rmse"]
		if m["baseline_rmse"] > 0 && rr > bs.RegPassRMSE && rr <= bs.RegWarnRMSE {
			_ = rr
		}
	}
	if label != "fail" && len(cites) > 0 && sev > 0 {
		cites = nil
	}
	if sev == 2 {
		risk += 12 * len(cites)
	}
	if risk > 100 {
		risk = 100
	}
	reasons := []string{fmt.Sprintf("severity=%d fam=%d", sev, fam)}
	return VerdictRow{
		Verdict:    label,
		RiskScore:  risk,
		CitedRules: cites,
		Reasons:    reasons,
	}, nil
}
