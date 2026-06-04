#include "profile_lane.h"

#include <sqlite3.h>

/* Bench lane bindings — reconciled by cycle_diag against bench_profiles.toml */

int lane_open_sync(int profile) {
    (void)profile;
    return 1;
}

int lane_merge_checkpoint(int profile) {
    (void)profile;
    return SQLITE_CHECKPOINT_PASSIVE;
}
