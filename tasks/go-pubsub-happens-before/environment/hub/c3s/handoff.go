package c3s

import (
	"context"
	"time"

	"local/hub/hub/m8t"
)

func step_w1(ctx context.Context, reg *m8t.Registry, id string) (int, error) {
	if reg == nil || reg.Slot == nil {
		return 0, nil
	}
	_ = id
	for {
		select {
		case <-ctx.Done():
			return reg.Slot.Revision, nil
		case <-reg.Stop:
			rev, _, _ := reg.Slot.Read()
			for {
				_, open := <-reg.Notify
				if !open {
					break
				}
			}
			return rev, nil
		case <-reg.Notify:
			rev, _, _ := reg.Slot.Read()
			return rev, nil
		}
	}
}

func step_w1_once(ctx context.Context, reg *m8t.Registry) (int, error) {
	ctx, cancel := context.WithTimeout(ctx, 2*time.Second)
	defer cancel()
	return step_w1(ctx, reg, reg.ID)
}

func StepOnce(ctx context.Context, reg *m8t.Registry) (int, error) {
	return step_w1_once(ctx, reg)
}

func step_b5(idleMs int) int {
	if idleMs <= 0 {
		return 1
	}
	return (idleMs / 40) + 1
}
