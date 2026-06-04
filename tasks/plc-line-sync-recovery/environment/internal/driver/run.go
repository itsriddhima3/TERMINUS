package driver

import (
	"crypto/sha256"
	"encoding/hex"
	"fmt"

	"lab.local/plc_line_sync/internal/config"
	"lab.local/plc_line_sync/internal/crc"
	"lab.local/plc_line_sync/internal/engine"
)

// Report is the outward JSON envelope.
type Report struct {
	SchemaVersion  string `json:"schema_version"`
	LineID       string `json:"line_id"`
	StablePhase      uint32 `json:"stable_phase"`
	CycleChain      uint32 `json:"cycle_chain"`
	DefectPurges     uint32 `json:"defect_purges"`
	OrphanCycles     uint32 `json:"orphan_cycles"`
	StationsLive      uint32 `json:"stations_live"`
	JitterBand        string `json:"jitter_band"`
	LineSynced bool   `json:"line_synced"`
	SkewDriftMax    uint32 `json:"skew_drift_max"`
	DigestHex      string `json:"digest_hex"`
}

// RunActive loads the active bundle and returns a filled report.
func RunActive(appRoot string) (Report, error) {
	dir, err := config.ActivePaths(appRoot)
	if err != nil {
		return Report{}, err
	}
	pack, profiles, rows, offsets, err := config.LoadPack(dir)
	if err != nil {
		return Report{}, err
	}
	crc.SetTrustAnchor(pack.TrustAnchor)
	out := engine.Replay(pack.ID(), pack.Quorum(), pack.Split(), pack.LagTight(), profiles, rows, offsets)
	ck := "true"
	if !out.LineSynced {
		ck = "false"
	}
	digest := sha256.Sum256([]byte(fmt.Sprintf(
		"%s|%d|%d|%d|%d|%d|%s|%s|%d",
		pack.ID(),
		out.StablePhase,
		out.CycleChain,
		out.DefectPurges,
		out.OrphanCycles,
		out.StationsLive,
		out.JitterBand,
		ck,
		out.SkewDriftMax,
	)))
	return Report{
		SchemaVersion:  "1",
		LineID:       pack.ID(),
		StablePhase:      out.StablePhase,
		CycleChain:      out.CycleChain,
		DefectPurges:     out.DefectPurges,
		OrphanCycles:     out.OrphanCycles,
		StationsLive:      out.StationsLive,
		JitterBand:        out.JitterBand,
		LineSynced: out.LineSynced,
		SkewDriftMax:    out.SkewDriftMax,
		DigestHex:      hex.EncodeToString(digest[:]),
	}, nil
}
