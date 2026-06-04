#ifndef MAINT_IFACE_H
#define MAINT_IFACE_H

#include <sqlite3.h>

int phase_p8(sqlite3 *db, int mode_hint, int crash_sim);

#endif
