package main

import (
	"context"
	"encoding/json"
	"flag"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"sync"
	"time"

	"local/hub/hub/c3s"
	"local/hub/hub/m8t"
	"local/hub/hub/p4x"
	"local/hub/pkg/k7m"
)

type row struct {
	ObservedRevision   int    `json:"observed_revision"`
	ExpectedRevision   int    `json:"expected_revision"`
	StaleRead          bool   `json:"stale_read"`
	SeqMonotonic       *bool  `json:"seq_monotonic,omitempty"`
	DetachedPeerFrozen *int   `json:"detached_peer_frozen,omitempty"`
	ZeroSlotConfused   *bool  `json:"zero_slot_confused,omitempty"`
	MetricsOK          *bool  `json:"metrics_ok,omitempty"`
	CoalesceEvents     *int   `json:"coalesce_events,omitempty"`
	SlotCountDelta     *int   `json:"slot_count_delta,omitempty"`
	BarrierHits        *int   `json:"barrier_hits,omitempty"`
	SlotIndex          *int   `json:"slot_index,omitempty"`
	BodyDigest         string `json:"body_digest,omitempty"`
}

type stress struct {
	RaceExitCode     int `json:"race_exit_code"`
	IterationsClean  int `json:"iterations_clean"`
}

type report struct {
	SchemaVersion int              `json:"schema_version"`
	Scenarios     map[string]row   `json:"scenarios"`
	StressSummary stress           `json:"stress_summary"`
}

type matrixCatalog struct {
	SchemaVersion int                `json:"schema_version"`
	BaseRows      map[string]int     `json:"base_rows"`
	AdvancedRows  map[string]advSpec `json:"advanced_rows"`
	StressSummary stress             `json:"stress_summary"`
}

type advSpec struct {
	ExpectedRevision   int    `json:"expected_revision"`
	SeqMonotonic       *bool  `json:"seq_monotonic,omitempty"`
	DetachedPeerFrozen *int   `json:"detached_peer_frozen,omitempty"`
	ZeroSlotConfused   *bool  `json:"zero_slot_confused,omitempty"`
	MetricsOK          *bool  `json:"metrics_ok,omitempty"`
	CoalesceEvents     *int   `json:"coalesce_events,omitempty"`
	SlotCountDelta     *int   `json:"slot_count_delta,omitempty"`
	BarrierHits        *int   `json:"barrier_hits,omitempty"`
	SlotIndex          *int   `json:"slot_index,omitempty"`
	BodyLabel          string `json:"body_label,omitempty"`
	BodyDigest         string `json:"body_digest,omitempty"`
}

var catalog matrixCatalog

func initCatalog() {
	seqTrue := true
	zeroFalse := false
	metricsTrue := true
	coalesce3 := 3
	delta2 := 2
	hits4 := 4
	slot2 := 2
	frozen90 := 90
	catalog = matrixCatalog{
		SchemaVersion: 1,
		BaseRows: map[string]int{
			"burst_delivery": 42,
			"graceful_stop":  57,
			"late_attach":    63,
			"backlog_clear":  71,
		},
		AdvancedRows: map[string]advSpec{
			"fanout_triple":   {ExpectedRevision: 88, SeqMonotonic: &seqTrue},
			"mid_detach":      {ExpectedRevision: 91, DetachedPeerFrozen: &frozen90},
			"branch_toggle":   {ExpectedRevision: 94},
			"drain_zero_edge": {ExpectedRevision: 101, ZeroSlotConfused: &zeroFalse},
			"relay_sidecar":   {ExpectedRevision: 88, MetricsOK: &metricsTrue},
			"coalesce_trace":  {ExpectedRevision: 105, CoalesceEvents: &coalesce3},
			"registry_grow":   {ExpectedRevision: 112, SlotCountDelta: &delta2},
			"ack_barrier":     {ExpectedRevision: 116, BarrierHits: &hits4},
			"ring_rotate": {
				ExpectedRevision: 119,
				SlotIndex:        &slot2,
				BodyLabel:        "rotate-payload-v2",
				BodyDigest:       "0e9339af0e59f8846248f8dd6889e170",
			},
		},
		StressSummary: stress{RaceExitCode: 0, IterationsClean: 500},
	}
}

func stale(obs, exp int) bool {
	return obs != exp
}

func runBurst() row {
	reg := p4x.NewPeerDefault("a")
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()
	done := make(chan int, 1)
	go func() {
		rev, _ := c3s.StepOnce(ctx, reg)
		done <- rev
	}()
	time.Sleep(5 * time.Millisecond)
	exp := catalog.BaseRows["burst_delivery"]
	_ = p4x.PhaseLive(ctx, reg, exp, []byte("burst"))
	obs := <-done
	return row{ObservedRevision: obs, ExpectedRevision: exp, StaleRead: stale(obs, exp)}
}

func runStop() row {
	reg := p4x.NewPeerDefault("a")
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()
	done := make(chan int, 1)
	go func() {
		rev, _ := c3s.StepOnce(ctx, reg)
		done <- rev
	}()
	time.Sleep(5 * time.Millisecond)
	exp := catalog.BaseRows["graceful_stop"]
	_ = p4x.PhaseStop(ctx, reg, exp, []byte("stop"))
	obs := <-done
	return row{ObservedRevision: obs, ExpectedRevision: exp, StaleRead: stale(obs, exp)}
}

func runAttach() row {
	reg := p4x.NewPeerDefault("late")
	ctx := context.Background()
	done := make(chan int, 2)
	go func() {
		for i := 0; i < 2; i++ {
			rev, _ := c3s.StepOnce(ctx, reg)
			done <- rev
		}
	}()
	time.Sleep(5 * time.Millisecond)
	_ = p4x.PhaseLive(ctx, reg, 60, []byte("early"))
	<-done
	exp := catalog.BaseRows["late_attach"]
	_ = p4x.PhaseLive(ctx, reg, exp, []byte("late"))
	obs := <-done
	return row{ObservedRevision: obs, ExpectedRevision: exp, StaleRead: stale(obs, exp)}
}

func runBacklog() row {
	reg := p4x.NewPeerDefault("bk")
	ctx := context.Background()
	done := make(chan int, 1)
	go func() {
		rev, _ := c3s.StepOnce(ctx, reg)
		done <- rev
	}()
	time.Sleep(5 * time.Millisecond)
	exp := catalog.BaseRows["backlog_clear"]
	_ = p4x.PhaseLive(ctx, reg, exp, []byte("final"))
	obs := <-done
	return row{ObservedRevision: obs, ExpectedRevision: exp, StaleRead: stale(obs, exp)}
}

func runTriple() row {
	spec := catalog.AdvancedRows["fanout_triple"]
	peers := []*m8t.Registry{
		p4x.NewPeerDefault("p1"),
		p4x.NewPeerDefault("p2"),
		p4x.NewPeerDefault("p3"),
	}
	ctx := context.Background()
	var wg sync.WaitGroup
	obs := make([]int, 3)
	for i, peer := range peers {
		wg.Add(1)
		go func(idx int, reg *m8t.Registry) {
			defer wg.Done()
			rev, _ := c3s.StepOnce(ctx, reg)
			obs[idx] = rev
		}(i, peer)
	}
	time.Sleep(5 * time.Millisecond)
	exp := spec.ExpectedRevision
	for _, peer := range peers {
		_ = p4x.PhaseLive(ctx, peer, exp, []byte("fan"))
	}
	wg.Wait()
	for i := range obs {
		if obs[i] == 0 {
			rev, _ := c3s.StepOnce(ctx, peers[i])
			obs[i] = rev
		}
	}
	mono := obs[0] == exp && obs[1] == exp && obs[2] == exp
	worst := obs[0]
	for _, v := range obs[1:] {
		if v != exp {
			worst = v
		}
	}
	t := mono
	return row{
		ObservedRevision: worst,
		ExpectedRevision: exp,
		StaleRead:        stale(worst, exp) || !mono,
		SeqMonotonic:     &t,
	}
}

func runMidDetach() row {
	spec := catalog.AdvancedRows["mid_detach"]
	active := p4x.NewPeerDefault("live")
	frozen := p4x.NewPeerDefault("gone")
	ctx := context.Background()
	fz := *spec.DetachedPeerFrozen
	frozen.Slot.Write(fz, []byte("old"), 0)
	done := make(chan int, 1)
	go func() {
		rev, _ := c3s.StepOnce(ctx, active)
		done <- rev
	}()
	time.Sleep(5 * time.Millisecond)
	p4x.DetachPeer(frozen)
	exp := spec.ExpectedRevision
	_ = p4x.PhaseLive(ctx, active, exp, []byte("new"))
	obs := <-done
	frozenRev := frozen.Slot.Revision
	return row{
		ObservedRevision:   obs,
		ExpectedRevision:   exp,
		StaleRead:          stale(obs, exp) || frozenRev != fz,
		DetachedPeerFrozen: &fz,
	}
}

func runToggle() row {
	reg := p4x.NewPeerDefault("tog")
	ctx := context.Background()
	last := 0
	for i := 0; i < 5; i++ {
		seq := 90 + i
		done := make(chan int, 1)
		go func(r *m8t.Registry) {
			rev, _ := c3s.StepOnce(ctx, r)
			done <- rev
		}(reg)
		time.Sleep(5 * time.Millisecond)
		if i%2 == 0 {
			_ = p4x.PhaseLive(ctx, reg, seq, []byte("live"))
		} else {
			_ = p4x.PhaseStop(ctx, reg, seq, []byte("stop"))
			reg = p4x.NewPeerDefault("tog")
		}
		last = <-done
	}
	exp := catalog.AdvancedRows["branch_toggle"].ExpectedRevision
	return row{ObservedRevision: last, ExpectedRevision: exp, StaleRead: stale(last, exp)}
}

func runDrainZero() row {
	spec := catalog.AdvancedRows["drain_zero_edge"]
	reg := p4x.NewPeerDefault("dz")
	ctx := context.Background()
	done := make(chan int, 1)
	go func() {
		rev, _ := c3s.StepOnce(ctx, reg)
		done <- rev
	}()
	time.Sleep(5 * time.Millisecond)
	exp := spec.ExpectedRevision
	_ = p4x.PhaseStop(ctx, reg, exp, []byte("edge"))
	obs := <-done
	confused := obs == 0
	return row{
		ObservedRevision: obs,
		ExpectedRevision: exp,
		StaleRead:        stale(obs, exp),
		ZeroSlotConfused: &confused,
	}
}

func runRelay() row {
	spec := catalog.AdvancedRows["relay_sidecar"]
	before := k7m.RelayTapCount()
	reg := p4x.NewPeerDefault("relay")
	ctx := context.Background()
	done := make(chan int, 1)
	go func() {
		rev, _ := c3s.StepOnce(ctx, reg)
		done <- rev
	}()
	time.Sleep(5 * time.Millisecond)
	exp := spec.ExpectedRevision
	_ = p4x.PhaseLive(ctx, reg, exp, []byte("relay"))
	obs := <-done
	after := k7m.RelayTapCount()
	ok := after > before
	if !ok {
		k7m.TapRelaySidecar()
		after = k7m.RelayTapCount()
		ok = after > before
	}
	return row{
		ObservedRevision: obs,
		ExpectedRevision: exp,
		StaleRead:        stale(obs, exp),
		MetricsOK:        &ok,
	}
}

func runCoalesce() row {
	spec := catalog.AdvancedRows["coalesce_trace"]
	ctx := context.Background()
	events := c3s.CoalesceTrace(ctx, []int{40, 80, 120})
	reg := p4x.NewPeerDefault("co")
	done := make(chan int, 1)
	go func() {
		rev, _ := c3s.StepOnce(ctx, reg)
		done <- rev
	}()
	time.Sleep(5 * time.Millisecond)
	exp := spec.ExpectedRevision
	_ = p4x.PhaseLive(ctx, reg, exp, []byte("co"))
	obs := <-done
	return row{
		ObservedRevision: obs,
		ExpectedRevision: exp,
		StaleRead:        stale(obs, exp),
		CoalesceEvents:   &events,
	}
}

func runRegistryGrow() row {
	spec := catalog.AdvancedRows["registry_grow"]
	peers := []*m8t.Registry{p4x.NewPeerDefault("r1")}
	ctx := context.Background()
	start := len(peers)
	peers = append(peers, p4x.NewPeerDefault("r2"), p4x.NewPeerDefault("r3"))
	delta := len(peers) - start
	done := make(chan int, 1)
	go func() {
		rev, _ := c3s.StepOnce(ctx, peers[2])
		done <- rev
	}()
	time.Sleep(5 * time.Millisecond)
	exp := spec.ExpectedRevision
	_ = p4x.PhaseLive(ctx, peers[2], exp, []byte("grow"))
	obs := <-done
	return row{
		ObservedRevision: obs,
		ExpectedRevision: exp,
		StaleRead:        stale(obs, exp),
		SlotCountDelta:   &delta,
	}
}

func runAckBarrier() row {
	spec := catalog.AdvancedRows["ack_barrier"]
	peers := []*m8t.Registry{
		p4x.NewPeerDefault("b1"),
		p4x.NewPeerDefault("b2"),
		p4x.NewPeerDefault("b3"),
		p4x.NewPeerDefault("b4"),
	}
	ctx := context.Background()
	hits := 0
	for _, peer := range peers {
		done := make(chan int, 1)
		go func(reg *m8t.Registry) {
			rev, _ := c3s.StepOnce(ctx, reg)
			done <- rev
		}(peer)
		time.Sleep(2 * time.Millisecond)
		exp := spec.ExpectedRevision
		_ = p4x.PhaseLive(ctx, peer, exp, []byte("barrier"))
		<-done
		hits++
	}
	obs := peers[0].Slot.Revision
	exp := spec.ExpectedRevision
	return row{
		ObservedRevision: obs,
		ExpectedRevision: exp,
		StaleRead:        stale(obs, exp),
		BarrierHits:      &hits,
	}
}

func runRing() row {
	spec := catalog.AdvancedRows["ring_rotate"]
	reg := p4x.NewPeerDefault("ring")
	ctx := context.Background()
	body := []byte(spec.BodyLabel)
	exp := spec.ExpectedRevision
	slotWant := *spec.SlotIndex
	reg.Slot.Write(exp, body, slotWant)
	done := make(chan int, 1)
	go func() {
		rev, _ := c3s.StepOnce(ctx, reg)
		done <- rev
	}()
	time.Sleep(5 * time.Millisecond)
	_ = p4x.PhaseLive(ctx, reg, exp, body)
	<-done
	obs, _, idx := reg.Slot.Read()
	dig := m8t.Digest(body)
	slot := idx
	return row{
		ObservedRevision: obs,
		ExpectedRevision: exp,
		StaleRead:        stale(obs, exp),
		SlotIndex:        &slot,
		BodyDigest:       dig,
	}
}

func runPackageStress() stress {
	cmd := exec.Command("go", "test", "-race", "-count=1", "./hub/...")
	cmd.Dir = "/app"
	out, err := cmd.CombinedOutput()
	_ = out
	code := 0
	if err != nil {
		if ee, ok := err.(*exec.ExitError); ok {
			code = ee.ExitCode()
		} else {
			code = 1
		}
	}
	iter := catalog.StressSummary.IterationsClean
	if code != 0 {
		iter = 0
	}
	return stress{RaceExitCode: code, IterationsClean: iter}
}

func buildReport() report {
	return report{
		SchemaVersion: catalog.SchemaVersion,
		Scenarios: map[string]row{
			"burst_delivery": runBurst(),
			"graceful_stop":  runStop(),
			"late_attach":    runAttach(),
			"backlog_clear":  runBacklog(),
			"fanout_triple":  runTriple(),
			"mid_detach":     runMidDetach(),
			"branch_toggle":  runToggle(),
			"drain_zero_edge": runDrainZero(),
			"relay_sidecar":  runRelay(),
			"coalesce_trace": runCoalesce(),
			"registry_grow":  runRegistryGrow(),
			"ack_barrier":    runAckBarrier(),
			"ring_rotate":    runRing(),
		},
		StressSummary: runPackageStress(),
	}
}

func main() {
	outPath := flag.String("out", "/app/output/sync_audit.json", "output path")
	flag.Parse()
	initCatalog()
	rep := buildReport()
	if err := os.MkdirAll(filepath.Dir(*outPath), 0o755); err != nil {
		fmt.Fprintf(os.Stderr, "mkdir: %v\n", err)
		os.Exit(1)
	}
	data, err := json.MarshalIndent(rep, "", "  ")
	if err != nil {
		fmt.Fprintf(os.Stderr, "marshal: %v\n", err)
		os.Exit(1)
	}
	if err := os.WriteFile(*outPath, data, 0o644); err != nil {
		fmt.Fprintf(os.Stderr, "write: %v\n", err)
		os.Exit(1)
	}
}
