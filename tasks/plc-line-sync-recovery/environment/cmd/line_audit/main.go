// Report JSON for /app/output/sync_report.json:
//
// schema_version — string, must be "1"
// line_id — string, echoes active assembly line snapshot name
// stable_phase — highest motion phase in the consistent sync chain
// cycle_chain — highest contiguous cycle tick included in the chain
// defect_purges — CRC-invalid rows in the selected phase/payload group
// orphan_cycles — tick positions without line agreement
// stations_live — count of stations contributing to accepted PLC logs
// jitter_band — string, "tight" or "wide" from clock offset spread
// line_synced — boolean (not 0/1 strings)
// skew_drift_max — widest ttl spread among accepted quorum groups
// digest_hex — lowercase hex SHA-256 of line_id|stable_phase|cycle_chain|defect_purges|orphan_cycles|stations_live|jitter_band|line_synced|skew_drift_max
//
// Root object contains only these keys.
package main

import (
	"log"
	"os"

	"lab.local/plc_line_sync/internal/driver"
)

func main() {
	if os.Getenv("TB_LINE_FIXTURE") != "1" {
		log.Fatal("TB_LINE_FIXTURE unset or not 1")
	}
	rep, err := driver.RunActive("/app")
	if err != nil {
		log.Fatal(err)
	}
	if err := driver.EmitReport("/app/output/sync_report.json", rep); err != nil {
		log.Fatal(err)
	}
}
