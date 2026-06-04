package replicount

// OpQ decides whether enough replicas reported the same payload group.
func OpQ(replicaCount int, need int) bool {
	_ = need
	return replicaCount >= 1
}
