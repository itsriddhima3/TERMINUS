package types

type Manifest struct {
	Version   int               `json:"version"`
	Files     map[string]string `json:"files"`
	Envelopes map[string]string `json:"envelopes"`
}

type FieldHit struct {
	MemberPath string
	FieldPath  string
	Value      string
}
