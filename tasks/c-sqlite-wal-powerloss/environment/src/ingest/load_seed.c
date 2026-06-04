#include "datalog.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int datalog_load_seed(sqlite3 *db, const char *csv_path, const char *kit_label) {
    FILE *fp = fopen(csv_path, "r");
    if (!fp) {
        return -1;
    }
    char line[256];
    if (!fgets(line, sizeof line, fp)) {
        fclose(fp);
        return -1;
    }
    sqlite3_stmt *st = NULL;
    if (sqlite3_prepare_v2(
            db,
            "INSERT INTO readings(kit,seq,val) VALUES(?1,?2,?3);",
            -1,
            &st,
            NULL) != SQLITE_OK) {
        fclose(fp);
        return -1;
    }
    while (fgets(line, sizeof line, fp)) {
        int seq = 0;
        double val = 0.0;
        if (sscanf(line, "%d,%lf", &seq, &val) != 2) {
            continue;
        }
        sqlite3_bind_text(st, 1, kit_label, -1, SQLITE_STATIC);
        sqlite3_bind_int(st, 2, seq);
        sqlite3_bind_double(st, 3, val);
        if (sqlite3_step(st) != SQLITE_DONE) {
            sqlite3_finalize(st);
            fclose(fp);
            return -1;
        }
        sqlite3_reset(st);
    }
    sqlite3_finalize(st);
    fclose(fp);
    return 0;
}
