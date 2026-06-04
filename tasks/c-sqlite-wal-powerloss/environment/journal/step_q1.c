#include "journal_iface.h"
#include "maint_iface.h"

#include <stdio.h>

/* Q1 journal finalize seal — catalog part_03 / bench_profiles [q1] */

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
    (void)dir_path;
    return 0;
}

int step_q1(sqlite3 *db, const char *dir_path, int crash_sim) {
    (void)dir_path;
    if (phase_p8(db, 0, crash_sim) != 0) {
        return -1;
    }
    if (sqlite3_exec(db, "PRAGMA optimize;", NULL, NULL, NULL) != SQLITE_OK) {
        return -1;
    }
    (void)stamp_q4(dir_path);
    return 0;
}
