package walk

import (
	"encoding/json"
	"fmt"
	"strings"

	"github.com/example/superset-export-vault/internal/config"
	"github.com/example/superset-export-vault/internal/types"
	"gopkg.in/yaml.v3"
)

func DiscoverFields(member string, payload []byte, rules config.RedactionDoc) ([]types.FieldHit, error) {
	return walk_q3(member, payload, rules)
}

func walk_q3(member string, payload []byte, rules config.RedactionDoc) ([]types.FieldHit, error) {
	if strings.HasSuffix(member, ".json") {
		var root any
		if err := json.Unmarshal(payload, &root); err != nil {
			return nil, err
		}
		return collectJSON(member, "", root, rules), nil
	}
	if strings.HasSuffix(member, ".yaml") || strings.HasSuffix(member, ".yml") {
		var root yaml.Node
		if err := yaml.Unmarshal(payload, &root); err != nil {
			return nil, err
		}
		if len(root.Content) == 0 {
			return nil, nil
		}
		return collectYAML(member, "", root.Content[0], rules), nil
	}
	return nil, nil
}

func collectJSON(member, prefix string, val any, rules config.RedactionDoc) []types.FieldHit {
	var hits []types.FieldHit
	switch typed := val.(type) {
	case map[string]any:
		for key, child := range typed {
			path := key
			if prefix != "" {
				path = prefix + "." + key
			}
			if str, ok := child.(string); ok && tokenMatch(key, rules, member) {
				hits = append(hits, types.FieldHit{MemberPath: member, FieldPath: path, Value: str})
				continue
			}
			hits = append(hits, collectJSON(member, path, child, rules)...)
		}
	case []any:
		for idx, child := range typed {
			path := fmt.Sprintf("%d", idx)
			if prefix != "" {
				path = fmt.Sprintf("%s.%d", prefix, idx)
			}
			hits = append(hits, collectJSON(member, path, child, rules)...)
		}
	}
	return hits
}

func collectYAML(member, prefix string, node *yaml.Node, rules config.RedactionDoc) []types.FieldHit {
	var hits []types.FieldHit
	switch node.Kind {
	case yaml.MappingNode:
		for i := 0; i < len(node.Content); i += 2 {
			keyNode := node.Content[i]
			valNode := node.Content[i+1]
			path := keyNode.Value
			if prefix != "" {
				path = prefix + "." + keyNode.Value
			}
			if valNode.Kind == yaml.ScalarNode && tokenMatch(keyNode.Value, rules, member) {
				hits = append(hits, types.FieldHit{MemberPath: member, FieldPath: path, Value: valNode.Value})
				continue
			}
			hits = append(hits, collectYAML(member, path, valNode, rules)...)
		}
	case yaml.SequenceNode:
		for idx, child := range node.Content {
			path := fmt.Sprintf("%d", idx)
			if prefix != "" {
				path = fmt.Sprintf("%s.%d", prefix, idx)
			}
			hits = append(hits, collectYAML(member, path, child, rules)...)
		}
	}
	return hits
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

func LegacyPathScan(member string, payload []byte) int {
	if !strings.Contains(member, "legacy") {
		return 0
	}
	return strings.Count(string(payload), "password")
}
