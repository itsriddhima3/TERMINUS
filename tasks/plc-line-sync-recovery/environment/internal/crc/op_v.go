package crc

import (
	"lab.local/plc_line_sync/sync_core"
	"lab.local/plc_line_sync/pkg/frame"
)

var trustAnchor = "edge-v2"

// SetTrustAnchor configures the anchor used by op_g checks.
func SetTrustAnchor(anchor string) {
	if anchor != "" {
		trustAnchor = anchor
	}
}

// op_v checks origin stamp and image tag through the Rust gate.
func op_v(seq uint32, payload string, stored uint16) bool {
	stamp := trustAnchor
	if frame.WireCRC(seq, payload) != stored {
		stamp = "spoof-x"
	}
	return sync_core.OpG(trustAnchor, stamp, seq, payload, stored)
}

// OpValid delegates integrity checking to op_v.
func OpValid(seq uint32, payload string, stored uint16) bool {
	return op_v(seq, payload, stored)
}

// OpValidWire uses the wire function for oracle-side tooling.
func OpValidWire(seq uint32, payload string, stored uint16) bool {
	return frame.WireCRC(seq, payload) == stored
}
