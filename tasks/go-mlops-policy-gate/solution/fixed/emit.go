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

func step_k7(bs threshlane.BandSet, m map[string]float64, meta map[string]string) (VerdictRow, error) {
	fam := 0
	if v, ok := meta["fam"]; ok {
		fmt.Sscanf(v, "%d", &fam)
	}
	sev, cites := threshlane.Rank_u9(fam, m, bs)
	if cites == nil {
		cites = []string{}
	}
	label := "pass"
	risk := 15
	switch sev {
	case 1:
		label = "warn"
		risk = 45
	case 2:
		label = "fail"
		risk = 88
	}
	if bs.ProdNoWarn && label == "warn" && fam == m5q.FamEmb {
		label = "fail"
		sev = 2
	}
	if fam == m5q.FamCls && label == "warn" {
		if m["baseline_rmse"] > 0 {
			rr := m["rmse"] / m["baseline_rmse"]
			limitPass := bs.RegPassRMSE * bs.RegTierMult
			limitWarn := bs.RegWarnRMSE * bs.RegTierMult
			if rr > limitPass && rr <= limitWarn {
				cites = append(cites, "A3-REG-07")
			}
		}
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
