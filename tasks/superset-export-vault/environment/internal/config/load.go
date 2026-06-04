package config

import (
	"os"

	"gopkg.in/yaml.v3"
)

type RedactionRule struct {
	MemberSuffix string   `yaml:"member_suffix"`
	KeyTokens    []string `yaml:"key_tokens"`
}

type RedactionDoc struct {
	Rules []RedactionRule `yaml:"rules"`
}

func LoadRedaction(path string) (RedactionDoc, error) {
	raw, err := os.ReadFile(path)
	if err != nil {
		return RedactionDoc{}, err
	}
	var doc RedactionDoc
	if err := yaml.Unmarshal(raw, &doc); err != nil {
		return RedactionDoc{}, err
	}
	return doc, nil
}
