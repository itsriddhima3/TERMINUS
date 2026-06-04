.PHONY: build run clean test

BINARY := /app/bin/audit
DB     := /app/data/ceremonies.db
OUT    := /app/output/report.json

build:
	go build -o $(BINARY) ./cmd/audit

run: build
	$(BINARY) \
		--db $(DB) \
		--dossier /app/docs/ceremony-policy-v3.md \
		--out $(OUT)

clean:
	rm -f $(BINARY) $(OUT)

test: run
	@echo "Report written to $(OUT)"
	@cat $(OUT)
