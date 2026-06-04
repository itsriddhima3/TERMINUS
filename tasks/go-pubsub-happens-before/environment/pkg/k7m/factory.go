package k7m

const (
	KindNotify = 0
	KindStop   = 1
)

func op_n2(kind int, capHint int) chan struct{} {
	if kind == KindStop {
		return make(chan struct{})
	}
	capacity := capHint
	if capacity <= 0 {
		capacity = 4
	}
	return make(chan struct{}, capacity)
}

func NewNotify(capHint int) chan struct{} {
	return op_n2(KindNotify, capHint)
}

func NewStop() chan struct{} {
	return op_n2(KindStop, 0)
}

func WireRegistry(notifyCap int) (chan struct{}, chan struct{}) {
	return NewNotify(notifyCap), NewStop()
}
