CC ?= gcc
CFLAGS ?= -O2 -Wall -Wextra -std=c11 -Iinclude -Isqlite
LDFLAGS ?= -pthread -ldl -lm

SQLITE_SRC = sqlite/sqlite3.c

OBJS = \
	build/sqlite3.o \
	build/main.o \
	build/audit_run.o \
	build/gate_op_k2.o \
	build/gate_op_n4.o \
	build/maint_phase_p8.o \
	build/journal_step_q1.o \
	build/maint_op_r3.o \
	build/ingest_load_seed.o \
	build/util_fs_sync.o \
	build/util_profile_lane.o \
	build/util_log_x1.o \
	build/decoy_sync_stub.o \
	build/decoy_wal_reader.o \
	build/decoy_checkpoint_ui.o

.PHONY: all clean

all: bin/datalog

bin/datalog: $(OBJS)
	@mkdir -p bin
	$(CC) $(CFLAGS) -o $@ $^ $(LDFLAGS)

build/sqlite3.o: $(SQLITE_SRC)
	@mkdir -p build
	$(CC) $(CFLAGS) -DSQLITE_THREADSAFE=1 -DSQLITE_ENABLE_FTS5 -c -o $@ $<

build/main.o: src/main.c
	@mkdir -p build
	$(CC) $(CFLAGS) -c -o $@ $<

build/audit_run.o: src/audit_run.c
	@mkdir -p build
	$(CC) $(CFLAGS) -c -o $@ $<

build/gate_op_k2.o: gate/op_k2.c
	@mkdir -p build
	$(CC) $(CFLAGS) -c -o $@ $<

build/gate_op_n4.o: gate/op_n4.c
	@mkdir -p build
	$(CC) $(CFLAGS) -c -o $@ $<

build/maint_phase_p8.o: src/maint/phase_p8.c
	@mkdir -p build
	$(CC) $(CFLAGS) -c -o $@ $<

build/journal_step_q1.o: journal/step_q1.c
	@mkdir -p build
	$(CC) $(CFLAGS) -c -o $@ $<

build/maint_op_r3.o: src/maint/op_r3.c
	@mkdir -p build
	$(CC) $(CFLAGS) -c -o $@ $<

build/ingest_load_seed.o: src/ingest/load_seed.c
	@mkdir -p build
	$(CC) $(CFLAGS) -c -o $@ $<

build/util_fs_sync.o: src/util/fs_sync.c
	@mkdir -p build
	$(CC) $(CFLAGS) -c -o $@ $<

build/util_profile_lane.o: src/util/profile_lane.c
	@mkdir -p build
	$(CC) $(CFLAGS) -c -o $@ $<

build/util_log_x1.o: src/util/log_x1.c
	@mkdir -p build
	$(CC) $(CFLAGS) -c -o $@ $<

build/decoy_sync_stub.o: decoy/sync_stub.c
	@mkdir -p build
	$(CC) $(CFLAGS) -c -o $@ $<

build/decoy_wal_reader.o: decoy/wal_reader.c
	@mkdir -p build
	$(CC) $(CFLAGS) -c -o $@ $<

build/decoy_checkpoint_ui.o: decoy/checkpoint_ui.c
	@mkdir -p build
	$(CC) $(CFLAGS) -c -o $@ $<

clean:
	rm -rf build bin
