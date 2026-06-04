package c3s_test

import (
	"context"
	"testing"
	"time"

	"local/hub/hub/c3s"
	"local/hub/hub/p4x"
)

func TestHandoffLivePath(t *testing.T) {
	reg := p4x.NewPeerDefault("live")
	ctx := context.Background()
	go func() {
		_ = p4x.PhaseLive(ctx, reg, 7, []byte("x"))
	}()
	rev, err := c3s.StepOnce(ctx, reg)
	if err != nil {
		t.Fatal(err)
	}
	if rev != 7 {
		t.Fatalf("got %d want 7", rev)
	}
}

func TestHandoffStopPath(t *testing.T) {
	reg := p4x.NewPeerDefault("stop")
	ctx := context.Background()
	done := make(chan int, 1)
	go func() {
		rev, err := c3s.StepOnce(ctx, reg)
		if err != nil {
			t.Errorf("handoff: %v", err)
			return
		}
		done <- rev
	}()
	time.Sleep(10 * time.Millisecond)
	if err := p4x.PhaseStop(ctx, reg, 57, []byte("stop")); err != nil {
		t.Fatal(err)
	}
	select {
	case obs := <-done:
		if obs != 57 {
			t.Fatalf("got %d want 57", obs)
		}
	case <-time.After(2 * time.Second):
		t.Fatal("timed out waiting for handoff")
	}
}
