package archive

import (
	"path"
	"strings"
)

func IsMetadataMember(name string) bool {
	clean := path.Clean(name)
	return strings.HasPrefix(clean, "metadata/") &&
		(strings.HasSuffix(clean, ".yaml") || strings.HasSuffix(clean, ".yml") || strings.HasSuffix(clean, ".json"))
}
