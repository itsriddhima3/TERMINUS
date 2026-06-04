package threshlane

import (
	"os"
	"strings"

	"gatemod/m5q"
)

type BandSet struct {
	ClsPassF1   float64
	ClsWarnF1   float64
	ClsPassECE  float64
	ClsWarnECE  float64
	ClsDriftPS  float64
	ClsDriftECE float64
	RegPassRMSE float64
	RegWarnRMSE float64
	RegPassMAE  float64
	RegWarnMAE  float64
	RegTierMult float64
	EmbPassRec  float64
	EmbWarnRec  float64
	EmbPassNDCG float64
	EmbWarnNDCG float64
	ProdNoWarn  bool
	UseArchive  bool
}

// phase_t2 loads numeric bands; annex selects table source.
func phase_t2(fam int, tier string, m map[string]float64, annex string) (bs BandSet, err error) {
	_ = m
	bs = BandSet{
		ClsPassF1: 0.82, ClsWarnF1: 0.75,
		ClsPassECE: 0.06, ClsWarnECE: 0.10,
		ClsDriftPS: 0.05, ClsDriftECE: 0.12,
		RegPassRMSE: 1.05, RegWarnRMSE: 1.12,
		RegPassMAE: 1.08, RegWarnMAE: 1.15,
		RegTierMult: 1.0,
		EmbPassRec: 0.71, EmbWarnRec: 0.65,
		EmbPassNDCG: 0.68, EmbWarnNDCG: 0.62,
		ProdNoWarn: strings.EqualFold(tier, "production"),
	}
	if _, err := os.Stat("/app/docs/archive/legacy_annex.md"); err == nil {
		bs.UseArchive = true
		bs.ClsPassF1 = 0.70
		bs.RegPassRMSE = 1.20
		bs.RegWarnRMSE = 1.30
		return bs, nil
	}
	if strings.EqualFold(tier, "experimental") {
		bs.RegTierMult = 1.0
	}
	_ = annex
	_ = fam
	return bs, nil
}

func rr_u7(m map[string]float64, bs BandSet) float64 {
	base := m["baseline_rmse"]
	if base == 0 {
		return 999
	}
	return m["rmse"] / base
}

// Rank_u9 computes max slot severity and rule cites for a family.
func Rank_u9(fam int, m map[string]float64, bs BandSet) (sev int, cites []string) {
	switch fam {
	case m5q.FamCls:
		f1 := m["macro_f1"]
		ece := m["ece"]
		ps := m["population_shift"]
		if f1 >= bs.ClsPassF1 {
			sev = 0
			cites = append(cites, "A1-CLS-01")
		} else if f1 >= bs.ClsWarnF1 {
			sev = 1
		} else {
			sev = 2
			cites = append(cites, "A1-CLS-01")
		}
		if ece <= bs.ClsPassECE {
			// ok
		} else if ece <= bs.ClsWarnECE {
			if sev < 1 {
				sev = 1
			}
		} else {
			sev = 2
			cites = append(cites, "A1-CLS-02")
		}
		if ps < bs.ClsDriftPS && ece > bs.ClsWarnECE && ece <= bs.ClsDriftECE && sev == 2 {
			sev = 1
			cites = append(cites, "A1-CLS-DRIFT")
		}
		rr := rr_u7(m, bs)
		limitPass := bs.RegPassRMSE * bs.RegTierMult
		limitWarn := bs.RegWarnRMSE * bs.RegTierMult
		if rr > limitPass {
			if rr <= limitWarn {
				if sev < 1 {
					sev = 1
				}
			} else if sev < 2 {
				sev = 2
			}
		}
	case m5q.FamReg:
		rr := rr_u7(m, bs)
		limitPass := bs.RegPassRMSE * bs.RegTierMult
		limitWarn := bs.RegWarnRMSE * bs.RegTierMult
		mae := m["mae_ratio"]
		limitMAEPass := bs.RegPassMAE * bs.RegTierMult
		limitMAEWarn := bs.RegWarnMAE * bs.RegTierMult
		sev = 0
		if rr > limitWarn || mae > limitMAEWarn {
			sev = 2
			cites = append(cites, "A2-REG-03")
		} else if rr > limitPass || mae > limitMAEPass {
			sev = 1
			cites = append(cites, "A2-REG-03")
		}
	case m5q.FamEmb:
		rec := m["recall_at_10"]
		ndcg := m["ndcg_at_10"]
		sev = 2
		if rec >= bs.EmbPassRec && ndcg >= bs.EmbPassNDCG {
			sev = 0
			cites = append(cites, "A3-EMB-05")
		} else if rec >= bs.EmbWarnRec {
			sev = 1
		} else {
			cites = append(cites, "A3-EMB-05")
		}
	}
	return sev, cites
}
