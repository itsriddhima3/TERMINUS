#define _DEFAULT_SOURCE
#include <fcntl.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>

#include <sqlite3.h>

int fs_sync_directory(const char *dir_path) {
    if (!dir_path || dir_path[0] == '\0') {
        return -1;
    }
    int fd = open(dir_path, O_RDONLY | O_DIRECTORY);
    if (fd < 0) {
        return -1;
    }
    int rc = fsync(fd);
    close(fd);
    return rc == 0 ? 0 : -1;
}

int fs_sync_db_file(sqlite3 *db) {
    const char *main_file = sqlite3_db_filename(db, "main");
    if (!main_file || main_file[0] == '\0') {
        return -1;
    }
    int fd = open(main_file, O_RDONLY);
    if (fd < 0) {
        return -1;
    }
    int rc = fsync(fd);
    close(fd);
    return rc == 0 ? 0 : -1;
}

int fs_barrier_both(sqlite3 *db, const char *dir_path) {
    if (sqlite3_exec(db, "PRAGMA wal_checkpoint(FULL);", NULL, NULL, NULL) != SQLITE_OK) {
        return -1;
    }
    if (fs_sync_db_file(db) != 0) {
        return -1;
    }
    (void)dir_path;
    return 0;
}
