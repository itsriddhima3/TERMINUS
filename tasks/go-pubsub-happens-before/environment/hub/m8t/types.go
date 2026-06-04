package m8t

type Registry struct {
	ID     string
	Notify chan struct{}
	Stop   chan struct{}
	Slot   *PayloadSlot
	Active bool
}
