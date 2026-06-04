#define _DEFAULT_SOURCE
#include "journal_iface.h"
#include "maint_iface.h"

#include <stdio.h>

int datalog_maintain_once(sqlite3 *db, const char *dir_path, int crash_sim) {
    if (op_r3_preflight(db) != 0) {
        return -1;
    }
    return step_q1(db, dir_path, crash_sim);
}
