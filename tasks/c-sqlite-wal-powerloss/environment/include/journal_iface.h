#ifndef JOURNAL_IFACE_H
#define JOURNAL_IFACE_H

#include <sqlite3.h>

int op_r3_preflight(sqlite3 *db);
int step_q1(sqlite3 *db, const char *dir_path, int crash_sim);

#endif
