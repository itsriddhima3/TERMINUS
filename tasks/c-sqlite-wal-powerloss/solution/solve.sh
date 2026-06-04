#!/usr/bin/env bash
set -euo pipefail

cd /app

cat > /app/src/util/profile_lane.c <<'EOF'
#include "profile_lane.h"

#include <sqlite3.h>

int lane_open_sync(int profile) {
    (void)profile;
    return 2;
}

int lane_merge_checkpoint(int profile) {
    (void)profile;
    return SQLITE_CHECKPOINT_TRUNCATE;
}
EOF

cat > /app/src/util/fs_sync.c <<'EOF'
#define _DEFAULT_SOURCE
#include <fcntl.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>

#include <sqlite3.h>

int fs_sync_directory(const char *dir_path) {
    if (!dir_path || dir_path[0] == '\0') {
        return -1;
    }
    int fd = open(dir_path, O_RDONLY | O_DIRECTORY);
    if (fd < 0) {
        return -1;
    }
    int rc = fsync(fd);
    close(fd);
    return rc == 0 ? 0 : -1;
}

int fs_sync_db_file(sqlite3 *db) {
    const char *main_file = sqlite3_db_filename(db, "main");
    if (!main_file || main_file[0] == '\0') {
        return -1;
    }
    int fd = open(main_file, O_RDONLY);
    if (fd < 0) {
        return -1;
    }
    int rc = fsync(fd);
    close(fd);
    return rc == 0 ? 0 : -1;
}

int fs_barrier_both(sqlite3 *db, const char *dir_path) {
    if (sqlite3_exec(db, "PRAGMA wal_checkpoint(FULL);", NULL, NULL, NULL) != SQLITE_OK) {
        return -1;
    }
    if (fs_sync_db_file(db) != 0) {
        return -1;
    }
    if (dir_path && dir_path[0] != '\0' && fs_sync_directory(dir_path) != 0) {
        return -1;
    }
    return 0;
}
EOF

sed -i '/^    return 0;$/i\    if (exec_pragma(db, "PRAGMA fullfsync=ON;") != SQLITE_OK) {\n        return -1;\n    }' /app/gate/op_k2.c

cat > /app/src/maint/phase_p8.c <<'EOF'
#define _DEFAULT_SOURCE
#include "maint_iface.h"

#include <stdio.h>
#include <unistd.h>

/* P8 maint cycle merge — catalog part_02 / bench_profiles [p8] */

static int tally_q4(sqlite3 *db) {
    sqlite3_stmt *st = NULL;
    if (sqlite3_prepare_v2(db, "PRAGMA wal_checkpoint;", -1, &st, NULL) != SQLITE_OK) {
        return -1;
    }
    int frames = -1;
    if (sqlite3_step(st) == SQLITE_ROW) {
        frames = sqlite3_column_int(st, 1);
    }
    sqlite3_finalize(st);
    return frames;
}

int phase_p8(sqlite3 *db, int mode_hint, int crash_sim) {
    (void)mode_hint;
    if (crash_sim) {
        const char *marker = "/tmp/datalog_cycle_marker";
        FILE *fp = fopen(marker, "w");
        if (fp) {
            fputc('1', fp);
            fflush(fp);
            fsync(fileno(fp));
            fclose(fp);
        }
        usleep(200000);
    }
    int n_log = 0;
    int n_ckpt = 0;
    int rc = sqlite3_wal_checkpoint_v2(
        db, NULL, SQLITE_CHECKPOINT_TRUNCATE, &n_log, &n_ckpt);
    if (rc != SQLITE_OK && rc != SQLITE_BUSY) {
        fprintf(stderr, "phase_p8 rc=%d log=%d ckpt=%d\n", rc, n_log, n_ckpt);
        return -1;
    }
    if (!crash_sim && tally_q4(db) > 0) {
        rc = sqlite3_wal_checkpoint_v2(
            db, NULL, SQLITE_CHECKPOINT_TRUNCATE, &n_log, &n_ckpt);
        if (rc != SQLITE_OK && rc != SQLITE_BUSY) {
            return -1;
        }
    }
    if (!crash_sim && tally_q4(db) > 0) {
        return -1;
    }
    return 0;
}
EOF

cat > /app/journal/step_q1.c <<'EOF'
#define _DEFAULT_SOURCE
#include "journal_iface.h"
#include "maint_iface.h"

#include <stdio.h>
#include <string.h>
#include <unistd.h>

/* Q1 journal finalize seal — catalog part_03 / bench_profiles [q1] */

extern int fs_barrier_both(sqlite3 *db, const char *dir_path);

int op_r3_preflight(sqlite3 *db) {
    sqlite3_stmt *st = NULL;
    if (sqlite3_prepare_v2(
            db, "SELECT value FROM meta WHERE key='schema_marker';", -1, &st, NULL) !=
        SQLITE_OK) {
        return -1;
    }
    int rc = -1;
    if (sqlite3_step(st) == SQLITE_ROW) {
        rc = sqlite3_column_int(st, 0) == 2 ? 0 : -1;
    }
    sqlite3_finalize(st);
    return rc;
}

static int stamp_q4(const char *dir_path) {
    char marker[512];
    snprintf(marker, sizeof marker, "%s/.cycle_sync_marker", dir_path);
    FILE *fp = fopen(marker, "w");
    if (!fp) {
        return -1;
    }
    fputc('1', fp);
    fflush(fp);
    if (fsync(fileno(fp)) != 0) {
        fclose(fp);
        return -1;
    }
    fclose(fp);
    return 0;
}

int step_q1(sqlite3 *db, const char *dir_path, int crash_sim) {
    if (phase_p8(db, 0, crash_sim) != 0) {
        return -1;
    }
    if (sqlite3_exec(db, "PRAGMA optimize;", NULL, NULL, NULL) != SQLITE_OK) {
        return -1;
    }
    if (!crash_sim && dir_path && dir_path[0] != '\0') {
        for (int attempt = 0; attempt < 3; attempt++) {
            if (fs_barrier_both(db, dir_path) == 0) {
                break;
            }
            if (attempt == 2) {
                return -1;
            }
        }
        if (stamp_q4(dir_path) != 0) {
            return -1;
        }
    }
    return 0;
}
EOF

bash /app/scripts/build.sh
mkdir -p /app/output
/app/bin/datalog audit --output /app/output/recovery_report.json
