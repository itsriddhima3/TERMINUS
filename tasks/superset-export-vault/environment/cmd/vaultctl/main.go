package main

import (
	"flag"
	"fmt"
	"os"

	"github.com/example/superset-export-vault/internal/config"
	"github.com/example/superset-export-vault/svc/m4p"
)

func main() {
	if len(os.Args) < 2 {
		usage()
		os.Exit(2)
	}
	switch os.Args[1] {
	case "seal":
		runSeal(os.Args[2:])
	case "verify":
		runVerify(os.Args[2:])
	case "decrypt":
		runDecrypt(os.Args[2:])
	default:
		usage()
		os.Exit(2)
	}
}

func usage() {
	fmt.Fprintf(os.Stderr, "usage: vaultctl seal|verify|decrypt [flags]\n")
}

func runSeal(args []string) {
	fs := flag.NewFlagSet("seal", flag.ExitOnError)
	keyFile := fs.String("key-file", "", "path to 32-byte key")
	inPath := fs.String("in", "", "input export archive")
	outPath := fs.String("out", "", "sealed output archive")
	_ = fs.Parse(args)
	if *keyFile == "" || *inPath == "" || *outPath == "" {
		fmt.Fprintln(os.Stderr, "seal requires --key-file --in --out")
		os.Exit(2)
	}
	svc, err := newService(*keyFile)
	if err != nil {
		die(err)
	}
	if err := svc.Seal(*inPath, *outPath); err != nil {
		die(err)
	}
}

func runVerify(args []string) {
	fs := flag.NewFlagSet("verify", flag.ExitOnError)
	keyFile := fs.String("key-file", "", "path to 32-byte key")
	bundle := fs.String("bundle", "", "sealed archive")
	_ = fs.Parse(args)
	if *keyFile == "" || *bundle == "" {
		fmt.Fprintln(os.Stderr, "verify requires --key-file --bundle")
		os.Exit(2)
	}
	svc, err := newService(*keyFile)
	if err != nil {
		die(err)
	}
	if err := svc.Verify(*bundle); err != nil {
		die(err)
	}
}

func runDecrypt(args []string) {
	fs := flag.NewFlagSet("decrypt", flag.ExitOnError)
	keyFile := fs.String("key-file", "", "path to 32-byte key")
	bundle := fs.String("bundle", "", "sealed archive")
	outPath := fs.String("out", "", "restored archive")
	_ = fs.Parse(args)
	if *keyFile == "" || *bundle == "" || *outPath == "" {
		fmt.Fprintln(os.Stderr, "decrypt requires --key-file --bundle --out")
		os.Exit(2)
	}
	svc, err := newService(*keyFile)
	if err != nil {
		die(err)
	}
	if err := svc.Decrypt(*bundle, *outPath); err != nil {
		die(err)
	}
}

func newService(keyFile string) (*m4p.Service, error) {
	key, err := m4p.LoadKey(keyFile)
	if err != nil {
		return nil, err
	}
	rules, err := config.LoadRedaction("/app/config/redaction.toml")
	if err != nil {
		return nil, err
	}
	return &m4p.Service{Rules: rules, Key: key}, nil
}

func die(err error) {
	fmt.Fprintln(os.Stderr, err)
	os.Exit(1)
}
