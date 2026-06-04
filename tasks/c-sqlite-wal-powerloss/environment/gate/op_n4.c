#include "datalog.h"
#include "store_iface.h"

#include <stdio.h>
#include <string.h>

int layout_q6(sqlite3 *db) {
    const char *ddl =
        "CREATE TABLE IF NOT EXISTS meta("
        "  key TEXT PRIMARY KEY,"
        "  value INTEGER NOT NULL"
        ");"
        "CREATE TABLE IF NOT EXISTS readings("
        "  id INTEGER PRIMARY KEY AUTOINCREMENT,"
        "  kit TEXT NOT NULL,"
        "  seq INTEGER NOT NULL,"
        "  val REAL NOT NULL"
        ");";
    char *err = NULL;
    if (sqlite3_exec(db, ddl, NULL, NULL, &err) != SQLITE_OK) {
        if (err) {
            fprintf(stderr, "layout: %s\n", err);
            sqlite3_free(err);
        }
        return -1;
    }
    sqlite3_stmt *st = NULL;
    if (sqlite3_prepare_v2(
            db,
            "INSERT OR REPLACE INTO meta(key,value) VALUES('schema_marker',?1);",
            -1,
            &st,
            NULL) != SQLITE_OK) {
        return -1;
    }
    sqlite3_bind_int(st, 1, 2);
    if (sqlite3_step(st) != SQLITE_DONE) {
        sqlite3_finalize(st);
        return -1;
    }
    sqlite3_finalize(st);
    return 0;
}

int datalog_init_db(sqlite3 **db, const char *path, int profile) {
    if (sqlite3_open(path, db) != SQLITE_OK) {
        return -1;
    }
    if (op_k2(*db, profile) != 0) {
        sqlite3_close(*db);
        *db = NULL;
        return -1;
    }
    if (layout_q6(*db) != 0) {
        sqlite3_close(*db);
        *db = NULL;
        return -1;
    }
    return 0;
}
