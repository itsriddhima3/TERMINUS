package main

import (
	"flag"
	"fmt"
	"log"
	"os"

	"custody-audit-tool/internal/ledger"
	"custody-audit-tool/internal/policy"
	"custody-audit-tool/internal/recovery"
	"custody-audit-tool/internal/report"
)

func main() {
	dbPath := flag.String("db", "", "path to ceremonies SQLite database")
	dossierPath := flag.String("dossier", "", "path to ceremony policy dossier")
	outPath := flag.String("out", "/app/output/report.json", "output report path")
	flag.Parse()

	if *dbPath == "" || *dossierPath == "" {
		fmt.Fprintln(os.Stderr, "usage: audit -db <path> -dossier <path> [-out <path>]")
		os.Exit(1)
	}

	db, err := ledger.Open(*dbPath)
	if err != nil {
		log.Fatalf("open db: %v", err)
	}
	defer db.Close()

	constraints, err := ledger.LoadConstraints(db)
	if err != nil {
		log.Fatalf("load constraints: %v", err)
	}

	cfg, err := policy.LoadDossierConfig(*dossierPath, constraints)
	if err != nil {
		log.Fatalf("load dossier: %v", err)
	}

	sessions, err := ledger.LoadSessions(db)
	if err != nil {
		log.Fatalf("load sessions: %v", err)
	}

	var entries []report.AuditEntry

	for _, sess := range sessions {
		slots, err := ledger.LoadSlots(db, sess.SessionID)
		if err != nil {
			log.Fatalf("load slots for %s: %v", sess.SessionID, err)
		}

		submissions, err := ledger.LoadSubmissions(db, sess.SessionID)
		if err != nil {
			log.Fatalf("load submissions for %s: %v", sess.SessionID, err)
		}

		approvalCount, err := ledger.CountLinkedApprovals(db, sess.SessionID)
		if err != nil {
			log.Fatalf("count approvals for %s: %v", sess.SessionID, err)
		}

		recvResult := recovery.Reconstruct(submissions, sess.ThresholdK)
		thresholdMet := len(submissions) >= sess.ThresholdK

		enf := policy.Enforce(slots, cfg.Constraints)

		violations := enf.PolicyViolations
		if violations == nil {
			violations = []string{}
		}

		fp := report.Fingerprint(recvResult.Secret, cfg.FingerprintLength)

		vs := report.VerificationStatus(
			recvResult.Status == recovery.StatusSuccess,
			enf.QuorumValid,
			violations,
		)

		entries = append(entries, report.AuditEntry{
			SessionID:         sess.SessionID,
			SlotsLoaded:       len(slots),
			ApprovalsLinked:   approvalCount,
			ReconstructStatus: recvResult.Status,
			SecretFingerprint: fp,
			ThresholdMet:      thresholdMet,
			QuorumValid:       enf.QuorumValid,
			PolicyViolations:  violations,
			VerificationStatus: vs,
		})
	}

	r := report.Report{AuditResults: entries}
	if err := report.Write(*outPath, r); err != nil {
		log.Fatalf("write report: %v", err)
	}
	fmt.Printf("audit complete: %d sessions written to %s\n", len(entries), *outPath)
}
