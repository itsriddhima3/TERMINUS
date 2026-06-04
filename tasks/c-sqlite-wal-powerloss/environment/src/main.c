#include "datalog.h"

#include <stdio.h>
#include <string.h>

static void usage(const char *argv0) {
    fprintf(
        stderr,
        "usage: %s audit --output <path>\n"
        "       %s init --kit <label> --db <path>\n",
        argv0,
        argv0);
}

int main(int argc, char **argv) {
    if (argc < 2) {
        usage(argv[0]);
        return 1;
    }
    if (strcmp(argv[1], "audit") == 0) {
        const char *out = "/app/output/recovery_report.json";
        for (int i = 2; i + 1 < argc; i++) {
            if (strcmp(argv[i], "--output") == 0) {
                out = argv[i + 1];
            }
        }
        return datalog_run_audit("/app/data/crash_manifest.toml", out) == 0 ? 0 : 1;
    }
    if (strcmp(argv[1], "init") == 0) {
        const char *kit = "KIT-A";
        const char *db_path = "/tmp/test.db";
        for (int i = 2; i + 1 < argc; i++) {
            if (strcmp(argv[i], "--kit") == 0) {
                kit = argv[i + 1];
            } else if (strcmp(argv[i], "--db") == 0) {
                db_path = argv[i + 1];
            }
        }
        sqlite3 *db = NULL;
        if (datalog_init_db(&db, db_path, 1) != 0) {
            return 1;
        }
        char seed_path[256];
        snprintf(seed_path, sizeof seed_path, "/app/data/seeds/%s.csv", kit);
        if (datalog_load_seed(db, seed_path, kit) != 0) {
            sqlite3_close(db);
            return 1;
        }
        sqlite3_close(db);
        return 0;
    }
    usage(argv[0]);
    return 1;
}
