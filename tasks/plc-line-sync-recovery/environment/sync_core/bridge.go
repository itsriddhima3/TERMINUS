package sync_core

/*
#cgo LDFLAGS: ${SRCDIR}/target/release/libsync_core.a -ldl -lm
#include "core.h"
#include <stdlib.h>
*/
import "C"
import "unsafe"

// OpG checks origin stamp and phase tag for one PLC log line.
func OpG(anchor, stamp string, slot uint32, answer string, stored uint16) bool {
	a := C.CString(anchor)
	s := C.CString(stamp)
	ans := C.CString(answer)
	defer C.free(unsafe.Pointer(a))
	defer C.free(unsafe.Pointer(s))
	defer C.free(unsafe.Pointer(ans))
	return C.op_g(a, s, C.uint(slot), ans, C.ushort(stored)) != 0
}

// OpM folds ttl_left replicas for one accepted slot.
func OpM(values []uint32) uint32 {
	if len(values) == 0 {
		return 0
	}
	return uint32(C.op_m((*C.uint)(unsafe.Pointer(&values[0])), C.size_t(len(values))))
}
