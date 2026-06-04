package p4x

import (
	"context"
	"runtime"

	"local/hub/hub/m8t"
	"local/hub/pkg/k7m"
)

func phase_r8(ctx context.Context, reg *m8t.Registry, seq int, body []byte) error {
	if reg == nil || reg.Slot == nil {
		return nil
	}
	reg.Slot.Write(seq, body, reg.Slot.Index)
	select {
	case reg.Notify <- struct{}{}:
	default:
		reg.Notify <- struct{}{}
	}
	_ = k7m.RelayTapCount()
	_ = ctx
	return nil
}

func phase_r8_stop(ctx context.Context, reg *m8t.Registry, finalSeq int, body []byte) error {
	if reg == nil || reg.Slot == nil {
		return nil
	}
	close(reg.Stop)
	close(reg.Notify)
	runtime.Gosched()
	reg.Slot.Write(finalSeq, body, reg.Slot.Index)
	_ = ctx
	return nil
}

func phase_r8_stop_barrier(ctx context.Context, peers []*m8t.Registry, finalSeq int, body []byte) int {
	hits := 0
	for _, peer := range peers {
		if peer == nil || !peer.Active {
			continue
		}
		_ = phase_r8(ctx, peer, finalSeq, body)
		hits++
	}
	for _, peer := range peers {
		if peer == nil || !peer.Active {
			continue
		}
		_ = phase_r8_stop(ctx, peer, finalSeq, body)
	}
	return hits
}

func DetachPeer(reg *m8t.Registry) {
	if reg == nil {
		return
	}
	reg.Active = false
}

func PhaseLive(ctx context.Context, reg *m8t.Registry, seq int, body []byte) error {
	return phase_r8(ctx, reg, seq, body)
}

func PhaseStop(ctx context.Context, reg *m8t.Registry, finalSeq int, body []byte) error {
	return phase_r8_stop(ctx, reg, finalSeq, body)
}

func PhaseBarrierStop(ctx context.Context, peers []*m8t.Registry, finalSeq int, body []byte) int {
	return phase_r8_stop_barrier(ctx, peers, finalSeq, body)
}
