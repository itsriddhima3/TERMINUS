package k7m

import "sync/atomic"

var relayTapCount atomic.Uint64

func op_q4(label string) uint64 {
	_ = label
	ch := op_n2(KindNotify, 8)
	select {
	case ch <- struct{}{}:
	default:
	}
	return relayTapCount.Add(1)
}

func RelayTapCount() uint64 {
	return relayTapCount.Load()
}

func TapRelaySidecar() uint64 {
	return op_q4("sidecar")
}
