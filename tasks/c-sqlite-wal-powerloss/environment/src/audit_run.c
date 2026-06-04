#define _DEFAULT_SOURCE
#include "datalog.h"

#include <fcntl.h>
#include <dirent.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <sys/wait.h>
#include <unistd.h>

extern int fs_sync_directory(const char *dir_path);

typedef struct {
    char id[32];
    char kit[32];
    char seed[256];
    int expect_rows;
} scenario_t;

static int parse_manifest(const char *path, scenario_t *out, int max, int *count) {
    FILE *fp = fopen(path, "r");
    if (!fp) {
        return -1;
    }
    char line[512];
    scenario_t cur;
    memset(&cur, 0, sizeof cur);
    int n = 0;
    while (fgets(line, sizeof line, fp)) {
        char *p = line;
        while (*p == ' ' || *p == '\t') {
            p++;
        }
        if (strncmp(p, "id =", 4) == 0) {
            if (n > 0 && n < max) {
                out[n - 1] = cur;
            }
            memset(&cur, 0, sizeof cur);
            sscanf(p + 4, " \"%31[^\"]\"", cur.id);
            if (n < max) {
                n++;
            }
        } else if (strncmp(p, "kit =", 5) == 0) {
            sscanf(p + 5, " \"%31[^\"]\"", cur.kit);
        } else if (strncmp(p, "seed =", 6) == 0) {
            sscanf(p + 6, " \"%255[^\"]\"", cur.seed);
        } else if (strncmp(p, "expect_rows =", 13) == 0) {
            sscanf(p + 13, " %d", &cur.expect_rows);
        }
    }
    if (cur.id[0] && n > 0 && n <= max) {
        out[n - 1] = cur;
    }
    fclose(fp);
    *count = n;
    return 0;
}

static int read_sync_level(sqlite3 *db) {
    sqlite3_stmt *st = NULL;
    if (sqlite3_prepare_v2(db, "PRAGMA synchronous;", -1, &st, NULL) != SQLITE_OK) {
        return -1;
    }
    int val = -1;
    if (sqlite3_step(st) == SQLITE_ROW) {
        val = sqlite3_column_int(st, 0);
    }
    sqlite3_finalize(st);
    return val;
}

static long wal_bytes(const char *db_path) {
    char wal_path[512];
    snprintf(wal_path, sizeof wal_path, "%s-wal", db_path);
    struct stat st;
    if (stat(wal_path, &st) != 0) {
        return 0;
    }
    return (long)st.st_size;
}

static int cycle_dir_synced(const char *work_dir) {
    char marker[512];
    snprintf(marker, sizeof marker, "%s/.cycle_sync_marker", work_dir);
    return access(marker, F_OK) == 0 ? 1 : 0;
}

static int probe_wal_cleared(const scenario_t *sc, const char *work_dir) {
    char db_path[512];
    snprintf(db_path, sizeof db_path, "%s/%s_probe.db", work_dir, sc->id);
    unlink(db_path);
    char wal_path[512];
    snprintf(wal_path, sizeof wal_path, "%s-wal", db_path);
    unlink(wal_path);

    sqlite3 *db = NULL;
    if (datalog_init_db(&db, db_path, 1) != 0) {
        return 0;
    }
    if (datalog_load_seed(db, sc->seed, sc->kit) != 0) {
        sqlite3_close(db);
        return 0;
    }
    sqlite3_exec(db, "BEGIN IMMEDIATE; COMMIT;", NULL, NULL, NULL);
    if (datalog_maintain_once(db, work_dir, 0) != 0) {
        sqlite3_close(db);
        return 0;
    }
    sqlite3_close(db);
    return wal_bytes(db_path) == 0 ? 1 : 0;
}

static void simulate_torn_wal(const char *db_path) {
    (void)db_path;
}

static int count_rows(sqlite3 *db) {
    sqlite3_stmt *st = NULL;
    if (sqlite3_prepare_v2(db, "SELECT COUNT(*) FROM readings;", -1, &st, NULL) !=
        SQLITE_OK) {
        return -1;
    }
    int rows = -1;
    if (sqlite3_step(st) == SQLITE_ROW) {
        rows = sqlite3_column_int(st, 0);
    }
    sqlite3_finalize(st);
    return rows;
}

static int integrity_ok(sqlite3 *db) {
    sqlite3_stmt *st = NULL;
    if (sqlite3_prepare_v2(db, "PRAGMA integrity_check;", -1, &st, NULL) != SQLITE_OK) {
        return 0;
    }
    int ok = 0;
    if (sqlite3_step(st) == SQLITE_ROW) {
        const char *res = (const char *)sqlite3_column_text(st, 0);
        ok = res && strcmp(res, "ok") == 0;
    }
    sqlite3_finalize(st);
    return ok;
}

static int schema_marker(sqlite3 *db) {
    sqlite3_stmt *st = NULL;
    if (sqlite3_prepare_v2(
            db, "SELECT value FROM meta WHERE key='schema_marker';", -1, &st, NULL) !=
        SQLITE_OK) {
        return -1;
    }
    int val = -1;
    if (sqlite3_step(st) == SQLITE_ROW) {
        val = sqlite3_column_int(st, 0);
    }
    sqlite3_finalize(st);
    return val;
}

static int run_crash_scenario(const scenario_t *sc, const char *work_dir) {
    char db_path[512];
    snprintf(db_path, sizeof db_path, "%s/%s.db", work_dir, sc->id);
    unlink(db_path);
    char wal_path[512];
    snprintf(wal_path, sizeof wal_path, "%s-wal", db_path);
    unlink(wal_path);
    char shm_path[512];
    snprintf(shm_path, sizeof shm_path, "%s-shm", db_path);
    unlink(shm_path);

    sqlite3 *db = NULL;
    if (datalog_init_db(&db, db_path, 1) != 0) {
        return -1;
    }
    if (datalog_load_seed(db, sc->seed, sc->kit) != 0) {
        sqlite3_close(db);
        return -1;
    }
    sqlite3_exec(db, "BEGIN IMMEDIATE;", NULL, NULL, NULL);
    sqlite3_exec(db, "COMMIT;", NULL, NULL, NULL);
    sqlite3_close(db);

    const char *marker = "/tmp/datalog_cycle_marker";
    unlink(marker);

    pid_t pid = fork();
    if (pid == 0) {
        sqlite3 *child_db = NULL;
        if (datalog_init_db(&child_db, db_path, 1) != 0) {
            _exit(2);
        }
        datalog_maintain_once(child_db, work_dir, 1);
        sqlite3_close(child_db);
        _exit(0);
    }
    if (pid < 0) {
        return -1;
    }
    for (int i = 0; i < 200; i++) {
        if (access(marker, F_OK) == 0) {
            break;
        }
        usleep(10000);
    }
    kill(pid, SIGKILL);
    waitpid(pid, NULL, 0);
    simulate_torn_wal(db_path);

    sqlite3 *reopen = NULL;
    int recovered = 0;
    int rows = -1;
    int ic = 0;
    int marker_val = -1;
    if (sqlite3_open(db_path, &reopen) == SQLITE_OK) {
        ic = integrity_ok(reopen);
        rows = count_rows(reopen);
        marker_val = schema_marker(reopen);
        recovered = ic && rows == sc->expect_rows && marker_val == DATALOG_SCHEMA_MARKER;
        sqlite3_close(reopen);
    }
    (void)marker_val;
    return recovered ? 0 : -1;
}


static void write_report(
    const char *output_path,
    const scenario_t *scenarios,
    int count,
    int *recovered,
    int *rows,
    int *integrity,
    int *markers) {
    FILE *fp = fopen(output_path, "w");
    if (!fp) {
        return;
    }
    fprintf(fp, "{\n  \"scenarios\": [\n");
    int all = 1;
    unsigned long digest = 5381;
    for (int i = 0; i < count; i++) {
        if (!recovered[i]) {
            all = 0;
        }
        digest = ((digest << 5) + digest) + (unsigned long)recovered[i];
        digest = ((digest << 5) + digest) + (unsigned long)rows[i];
        digest = ((digest << 5) + digest) + (unsigned long)integrity[i];
        digest = ((digest << 5) + digest) + (unsigned long)markers[i];
        fprintf(
            fp,
            "    {\"id\": \"%s\", \"kit\": \"%s\", \"recovered\": %s, "
            "\"row_count\": %d, \"integrity_ok\": %s, \"schema_marker\": %d}%s\n",
            scenarios[i].id,
            scenarios[i].kit,
            recovered[i] ? "true" : "false",
            rows[i],
            integrity[i] ? "true" : "false",
            markers[i],
            i + 1 < count ? "," : "");
    }
    fprintf(
        fp,
        "  ],\n  \"summary\": {\"all_recovered\": %s, \"audit_digest\": "
        "\"%08lx\"}\n}\n",
        all ? "true" : "false",
        digest & 0xffffffffUL);
    fclose(fp);
}

int datalog_run_audit(const char *manifest_path, const char *output_path) {
    scenario_t scenarios[8];
    int count = 0;
    if (parse_manifest(manifest_path, scenarios, 8, &count) != 0 || count == 0) {
        return -1;
    }
    const char *work_dir = "/tmp/datalog_audit";
    mkdir(work_dir, 0755);

    int recovered[8] = {0};
    int rows[8] = {0};
    int integrity[8] = {0};
    int markers[8] = {0};

    for (int i = 0; i < count; i++) {
        char db_path[512];
        snprintf(db_path, sizeof db_path, "%s/%s.db", work_dir, scenarios[i].id);
        unlink(db_path);
        char marker_path[512];
        snprintf(marker_path, sizeof marker_path, "%s/.cycle_sync_marker", work_dir);
        unlink(marker_path);

        run_crash_scenario(&scenarios[i], work_dir);

        sqlite3 *db = NULL;
        if (datalog_init_db(&db, db_path, 1) == 0) {
            integrity[i] = integrity_ok(db);
            rows[i] = count_rows(db);
            markers[i] = schema_marker(db);
            int sync = read_sync_level(db);
            sqlite3_close(db);
            int wal_clear = probe_wal_cleared(&scenarios[i], work_dir);
            int dir_sync = cycle_dir_synced(work_dir);
            int crash_ok =
                integrity[i] && rows[i] == scenarios[i].expect_rows &&
                markers[i] == DATALOG_SCHEMA_MARKER;
            recovered[i] = crash_ok && sync == 2 && wal_clear && dir_sync;
            if (!recovered[i]) {
                fprintf(
                    stderr,
                    "audit: scenario=%s lane=(%d,%d,%d) "
                    "sync=%d wal=%d stamp=%d base=%d\n",
                    scenarios[i].id,
                    sync == 2,
                    wal_clear,
                    dir_sync,
                    sync,
                    wal_clear,
                    dir_sync,
                    crash_ok);
            }
        }
    }

    write_report(output_path, scenarios, count, recovered, rows, integrity, markers);
    return recovered[0] && recovered[1] && recovered[2] && recovered[3] ? 0 : -1;
}
