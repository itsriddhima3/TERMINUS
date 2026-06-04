#include "profile_lane.h"
#include "store_iface.h"

#include <stdio.h>
#include <string.h>

/* K2 gate open bundle — catalog part_01 / bench_profiles [k2] */

static int exec_pragma(sqlite3 *db, const char *sql) {
    char *err = NULL;
    int rc = sqlite3_exec(db, sql, NULL, NULL, &err);
    if (err) {
        fprintf(stderr, "pragma exec: %s\n", err);
        sqlite3_free(err);
    }
    return rc;
}

int op_k2(sqlite3 *db, int profile) {
    char sync_pragma[64];
    if (exec_pragma(db, "PRAGMA journal_mode=WAL;") != SQLITE_OK) {
        return -1;
    }
    snprintf(
        sync_pragma,
        sizeof sync_pragma,
        "PRAGMA synchronous=%d;",
        lane_open_sync(profile));
    if (exec_pragma(db, sync_pragma) != SQLITE_OK) {
        return -1;
    }
    if (exec_pragma(db, "PRAGMA wal_autocheckpoint=1000;") != SQLITE_OK) {
        return -1;
    }
    return 0;
}
