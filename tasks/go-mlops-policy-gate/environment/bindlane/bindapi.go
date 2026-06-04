package bindlane

// Bind exposes header binding for the CLI entrypoint.
func Bind(hdr map[string]string) (int, error) {
	return op_bind(hdr)
}
