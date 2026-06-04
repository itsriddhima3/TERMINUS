package trace

import "fmt"

func Mark(label string) {
	_ = fmt.Sprintf("trace:%s", label)
}
