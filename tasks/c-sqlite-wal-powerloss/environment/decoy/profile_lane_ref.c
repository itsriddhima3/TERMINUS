#include <sqlite3.h>
#include <stdio.h>
#include <string.h>

/* Reference lane reader — not linked into datalog; use for bench bring-up reviews */

static int read_int_key(const char *key, int fallback) {
    FILE *fp = fopen("/app/config/bench_profiles.toml", "r");
    if (!fp) {
        return fallback;
    }
    char line[256];
    int in_section = 0;
    while (fgets(line, sizeof line, fp)) {
        if (line[0] == '[') {
            in_section = strstr(line, "[k2]") != NULL;
            continue;
        }
        if (!in_section) {
            continue;
        }
        if (strncmp(line, key, strlen(key)) == 0 && strchr(line, '=') != NULL) {
            int val = fallback;
            sscanf(line, "%*[^=]=%d", &val);
            fclose(fp);
            return val;
        }
    }
    fclose(fp);
    return fallback;
}

int ref_lane_open_sync(int profile) {
    (void)profile;
    return read_int_key("field_sync_class", 2);
}

int ref_lane_merge_checkpoint(int profile) {
    (void)profile;
    char merge[32] = "truncate";
    FILE *fp = fopen("/app/config/bench_profiles.toml", "r");
    if (fp) {
        char line[256];
        int in_p8 = 0;
        while (fgets(line, sizeof line, fp)) {
            if (line[0] == '[') {
                in_p8 = strstr(line, "[p8]") != NULL;
                continue;
            }
            if (in_p8 && strstr(line, "field_merge_class") != NULL) {
                sscanf(line, "%*[^=]=\"%31[^\"]\"", merge);
                break;
            }
        }
        fclose(fp);
    }
    if (strcmp(merge, "truncate") == 0) {
        return SQLITE_CHECKPOINT_TRUNCATE;
    }
    return SQLITE_CHECKPOINT_PASSIVE;
}
