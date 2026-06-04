#ifndef DATALOG_H
#define DATALOG_H

#include <sqlite3.h>

#define DATALOG_SCHEMA_MARKER 2

int datalog_init_db(sqlite3 **db, const char *path, int profile);
int datalog_load_seed(sqlite3 *db, const char *csv_path, const char *kit_label);
int datalog_run_audit(const char *manifest_path, const char *output_path);
int datalog_maintain_once(sqlite3 *db, const char *dir_path, int crash_sim);

#endif
