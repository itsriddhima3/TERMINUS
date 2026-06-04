package p4x_test

import (
	"context"
	"testing"

	"local/hub/hub/c3s"
	"local/hub/hub/p4x"
)

func TestStressHandoffCycles(t *testing.T) {
	for i := 0; i < 500; i++ {
		reg := p4x.NewPeerDefault("stress")
		ctx := context.Background()
		done := make(chan int, 1)
		go func() {
			rev, err := c3s.StepOnce(ctx, reg)
			if err != nil {
				t.Errorf("handoff: %v", err)
			}
			done <- rev
		}()
		seq := 1000 + i
		if err := p4x.PhaseLive(ctx, reg, seq, []byte("load")); err != nil {
			t.Fatal(err)
		}
		obs := <-done
		if obs != seq {
			t.Fatalf("iteration %d: got %d want %d", i, obs, seq)
		}
	}
}
