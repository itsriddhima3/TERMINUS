#define _DEFAULT_SOURCE
#include "maint_iface.h"
#include "profile_lane.h"

#include <stdio.h>
#include <unistd.h>

/* P8 maint cycle merge — catalog part_02 / bench_profiles [p8] */

static int tally_q4(sqlite3 *db) {
    (void)db;
    return 0;
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
        db, NULL, lane_merge_checkpoint(mode_hint), &n_log, &n_ckpt);
    if (rc != SQLITE_OK && rc != SQLITE_BUSY) {
        fprintf(stderr, "phase_p8 rc=%d log=%d ckpt=%d\n", rc, n_log, n_ckpt);
        return -1;
    }
    (void)tally_q4(db);
    return 0;
}
