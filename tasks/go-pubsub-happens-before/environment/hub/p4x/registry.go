package p4x

import (
	"local/hub/hub/m8t"
	"local/hub/pkg/k7m"
)

func NewPeer(id string, notifyCap int) *m8t.Registry {
	notify, stop := k7m.WireRegistry(notifyCap)
	return &m8t.Registry{
		ID:     id,
		Notify: notify,
		Stop:   stop,
		Slot:   m8t.NewPayloadSlot(),
		Active: true,
	}
}

func NewPeerDefault(id string) *m8t.Registry {
	return NewPeer(id, 0)
}
