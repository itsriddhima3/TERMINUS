#include <stdio.h>

int decoy_wal_frame_total(const char *manifest) {
    FILE *fp = fopen(manifest, "r");
    if (!fp) {
        return -1;
    }
    int lines = 0;
    char buf[256];
    while (fgets(buf, sizeof buf, fp)) {
        lines++;
    }
    fclose(fp);
    return lines;
}
