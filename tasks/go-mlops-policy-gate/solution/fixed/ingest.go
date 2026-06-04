package bindlane

import (
	"strings"

	"gatemod/m5q"
)

func op_bind(hdr map[string]string) (fam int, err error) {
	k := strings.ToLower(strings.TrimSpace(hdr["kind"]))
	switch k {
	case "classification_report":
		return m5q.FamCls, nil
	case "regression_report":
		return m5q.FamReg, nil
	case "embedding_report":
		return m5q.FamEmb, nil
	default:
		return m5q.FamUnknown, nil
	}
}
