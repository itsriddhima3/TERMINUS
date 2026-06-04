package q7m

import (
	"encoding/json"
	"strings"

	"github.com/example/superset-export-vault/internal/config"
	"github.com/example/superset-export-vault/internal/types"
	"gopkg.in/yaml.v3"
)

func DiscoverFields(member string, payload []byte, rules config.RedactionDoc) ([]types.FieldHit, error) {
	_ = DefaultWalkerPolicy()
	return walk_q3(member, payload, rules)
}

func walk_q3(member string, payload []byte, rules config.RedactionDoc) ([]types.FieldHit, error) {
	if strings.HasSuffix(member, ".json") {
		return op_j8(member, payload, rules)
	}
	if strings.HasSuffix(member, ".yaml") || strings.HasSuffix(member, ".yml") {
		return op_y8(member, payload, rules)
	}
	return nil, nil
}

func op_j8(member string, payload []byte, rules config.RedactionDoc) ([]types.FieldHit, error) {
	var root map[string]any
	if err := json.Unmarshal(payload, &root); err != nil {
		return nil, err
	}
	var hits []types.FieldHit
	for key, val := range root {
		if str, ok := val.(string); ok && tokenMatch(key, rules, member) {
			hits = append(hits, types.FieldHit{
				MemberPath: member,
				FieldPath:  key,
				Value:      str,
			})
		}
	}
	return hits, nil
}

func op_y8(member string, payload []byte, rules config.RedactionDoc) ([]types.FieldHit, error) {
	var root yaml.Node
	if err := yaml.Unmarshal(payload, &root); err != nil {
		return nil, err
	}
	if len(root.Content) == 0 {
		return nil, nil
	}
	doc := root.Content[0]
	if doc.Kind != yaml.MappingNode {
		return nil, nil
	}
	var hits []types.FieldHit
	for i := 0; i < len(doc.Content); i += 2 {
		keyNode := doc.Content[i]
		valNode := doc.Content[i+1]
		key := keyNode.Value
		if valNode.Kind == yaml.ScalarNode && tokenMatch(key, rules, member) {
			hits = append(hits, types.FieldHit{
				MemberPath: member,
				FieldPath:  key,
				Value:      valNode.Value,
			})
		}
	}
	return hits, nil
}

func tokenMatch(key string, rules config.RedactionDoc, member string) bool {
	lower := strings.ToLower(key)
	for _, rule := range rules.Rules {
		if rule.MemberSuffix != "" && !strings.HasSuffix(member, rule.MemberSuffix) {
			continue
		}
		for _, tok := range rule.KeyTokens {
			if strings.Contains(lower, strings.ToLower(tok)) {
				return true
			}
		}
	}
	return false
}

// LegacyPathScan counts legacy sqlite dump password markers only.
func legacy_n0(member string, payload []byte) int {
	if !strings.Contains(member, "legacy") {
		return 0
	}
	return strings.Count(string(payload), "password")
}
