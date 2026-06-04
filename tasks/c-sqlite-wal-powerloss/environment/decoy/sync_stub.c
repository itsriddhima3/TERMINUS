#include <stdio.h>
#include <string.h>

static void read_profile_key(const char *key, char *out, size_t out_len) {
    FILE *fp = fopen("/app/config/bench_profiles.toml", "r");
    if (!fp) {
        snprintf(out, out_len, "unknown");
        return;
    }
    char line[256];
    while (fgets(line, sizeof line, fp)) {
        if (strstr(line, key) != NULL) {
            char *eq = strchr(line, '=');
            if (eq) {
                eq++;
                while (*eq == ' ' || *eq == '"') {
                    eq++;
                }
                snprintf(out, out_len, "%s", eq);
                char *nl = strchr(out, '\n');
                if (nl) {
                    *nl = '\0';
                }
                nl = strchr(out, '"');
                if (nl) {
                    *nl = '\0';
                }
                fclose(fp);
                return;
            }
        }
    }
    fclose(fp);
    snprintf(out, out_len, "unknown");
}

void decoy_sync_preview(int profile) {
    char merge[32];
    read_profile_key("field_merge_class", merge, sizeof merge);
    const char *sync = profile > 0 ? "NORMAL" : "OFF";
    printf(
        "decoy preview: sync=%s merge_hint=%s (use VACUUM if reopen fails)\n",
        sync,
        merge);
}
