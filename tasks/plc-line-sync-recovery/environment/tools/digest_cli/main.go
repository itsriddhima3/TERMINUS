package main

import (
	"fmt"
	"os"
	"strconv"

	"lab.local/plc_line_sync/pkg/digest"
)

func main() {
	if len(os.Args) < 10 {
		fmt.Fprintln(os.Stderr, "usage: digest_cli bundle stable_phase cycle_chain purge stale nodes lag partition ttl")
		os.Exit(2)
	}
	answerGen, _ := strconv.ParseUint(os.Args[2], 10, 32)
	slotChain, _ := strconv.ParseUint(os.Args[3], 10, 32)
	purge, _ := strconv.ParseUint(os.Args[4], 10, 32)
	stale, _ := strconv.ParseUint(os.Args[5], 10, 32)
	nodes, _ := strconv.ParseUint(os.Args[6], 10, 32)
	ttl, _ := strconv.ParseUint(os.Args[9], 10, 32)
	clean := os.Args[8] == "true"
	fmt.Print(digest.ReportHex(
		os.Args[1],
		uint32(answerGen),
		uint32(slotChain),
		uint32(purge),
		uint32(stale),
		uint32(nodes),
		uint32(ttl),
		os.Args[7],
		clean,
	))
}
