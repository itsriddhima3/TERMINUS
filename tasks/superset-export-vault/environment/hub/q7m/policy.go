package q7m

// WalkerPolicy captures traversal limits from the staging walker policy.
type WalkerPolicy struct {
	RootOnly bool
}

func DefaultWalkerPolicy() WalkerPolicy {
	return WalkerPolicy{RootOnly: true}
}
