#ifndef STORE_IFACE_H
#define STORE_IFACE_H

#include <sqlite3.h>

int op_k2(sqlite3 *db, int profile);
int layout_q6(sqlite3 *db);

#endif
