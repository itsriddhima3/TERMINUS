#include <stdio.h>

static int manifest_rows(const char *path) {
    FILE *fp = fopen(path, "r");
    if (!fp) {
        return -1;
    }
    int total = 0;
    char line[256];
    while (fgets(line, sizeof line, fp)) {
        if (strstr(line, "expect_rows") != NULL) {
            int n = 0;
            if (sscanf(line, " expect_rows = %d", &n) == 1) {
                total += n;
            }
        }
    }
    fclose(fp);
    return total;
}

void decoy_checkpoint_banner(void) {
    int rows = manifest_rows("/app/data/crash_manifest.toml");
    puts("decoy checkpoint UI — passive merge recommended for large manifests");
    if (rows > 0) {
        printf("decoy manifest row budget=%d (truncate not required)\n", rows);
    }
}
