package m4p

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"os"
	"strings"

	"github.com/example/superset-export-vault/internal/archive"
	"github.com/example/superset-export-vault/pkg/k2n"
	"github.com/example/superset-export-vault/internal/config"
	"github.com/example/superset-export-vault/ledger/h5r"
	"github.com/example/superset-export-vault/internal/types"
	"github.com/example/superset-export-vault/hub/q7m"
	"gopkg.in/yaml.v3"
)

const ManifestMember = "vault/manifest.json"

type Service struct {
	Rules config.RedactionDoc
	Key   []byte
}

func LoadKey(path string) ([]byte, error) {
	raw, err := os.ReadFile(path)
	if err != nil {
		return nil, err
	}
	if len(raw) != 32 {
		return nil, fmt.Errorf("key file must be exactly 32 bytes")
	}
	return raw, nil
}

func (s *Service) Seal(inPath, outPath string) error {
	bundle, err := archive.ReadBundle(inPath)
	if err != nil {
		return err
	}
	delete(bundle.Members, ManifestMember)
	man := types.Manifest{
		Version:   1,
		Files:     map[string]string{},
		Envelopes: map[string]string{},
	}
	for member, payload := range bundle.Members {
		if !archive.IsMetadataMember(member) {
			man.Files[member] = h5r.MemberDigest(member, payload)
			continue
		}
		hits, err := q7m.DiscoverFields(member, payload, s.Rules)
		if err != nil {
			return err
		}
		updated := payload
		for _, hit := range hits {
			token, err := k2n.BindEnvelope(s.Key, hit.MemberPath, hit.FieldPath, []byte(hit.Value))
			if err != nil {
				return err
			}
			replaced := strings.Replace(string(updated), hit.Value, token, 1)
			if replaced == string(updated) {
				return fmt.Errorf("replace failed for %s", hit.FieldPath)
			}
			updated = []byte(replaced)
			man.Envelopes[hit.MemberPath+":"+hit.FieldPath] = token
		}
		bundle.Members[member] = updated
		man.Files[member] = h5r.MemberDigest(member, updated)
	}
	raw, err := json.MarshalIndent(man, "", "  ")
	if err != nil {
		return err
	}
	bundle.Members[ManifestMember] = raw
	return bundle.Write(outPath)
}

func (s *Service) Verify(bundlePath string) error {
	bundle, err := archive.ReadBundle(bundlePath)
	if err != nil {
		return err
	}
	raw, ok := bundle.Members[ManifestMember]
	if !ok {
		return fmt.Errorf("missing manifest")
	}
	var man types.Manifest
	if err := json.Unmarshal(raw, &man); err != nil {
		return err
	}
	for member, expect := range man.Files {
		payload, ok := bundle.Members[member]
		if !ok {
			return fmt.Errorf("missing member %s", member)
		}
		got := h5r.MemberDigest(member, payload)
		if got != expect {
			return fmt.Errorf("digest mismatch for %s", member)
		}
	}
	for id, token := range man.Envelopes {
		parts := strings.SplitN(id, ":", 2)
		if len(parts) != 2 {
			return fmt.Errorf("bad envelope id")
		}
		if _, err := k2n.OpenEnvelope(s.Key, parts[0], parts[1], token); err != nil {
			return fmt.Errorf("envelope open failed for %s: %w", id, err)
		}
	}
	return nil
}

func (s *Service) Decrypt(inPath, outPath string) error {
	bundle, err := archive.ReadBundle(inPath)
	if err != nil {
		return err
	}
	raw, ok := bundle.Members[ManifestMember]
	if !ok {
		return fmt.Errorf("missing manifest")
	}
	var man types.Manifest
	if err := json.Unmarshal(raw, &man); err != nil {
		return err
	}
	delete(bundle.Members, ManifestMember)
	for id, token := range man.Envelopes {
		parts := strings.SplitN(id, ":", 2)
		if len(parts) != 2 {
			return fmt.Errorf("bad envelope id")
		}
		member := parts[0]
		field := parts[1]
		payload := bundle.Members[member]
		plain, err := k2n.OpenEnvelope(s.Key, member, field, token)
		if err != nil {
			return err
		}
		replaced := strings.Replace(string(payload), token, string(plain), 1)
		if replaced == string(payload) {
			return fmt.Errorf("decrypt replace failed for %s", id)
		}
		bundle.Members[member] = []byte(replaced)
	}
	return bundle.Write(outPath)
}

func replaceField(payload []byte, member, fieldPath, value string) ([]byte, error) {
	if strings.HasSuffix(member, ".json") {
		var root map[string]any
		if err := json.Unmarshal(payload, &root); err != nil {
			return nil, err
		}
		if err := setJSONPath(root, fieldPath, value); err != nil {
			return nil, err
		}
		return json.MarshalIndent(root, "", "  ")
	}
	var root yaml.Node
	if err := yaml.Unmarshal(payload, &root); err != nil {
		return nil, err
	}
	if err := setYAMLPath(&root, fieldPath, value); err != nil {
		return nil, err
	}
	var buf strings.Builder
	enc := yaml.NewEncoder(&buf)
	enc.SetIndent(2)
	if err := enc.Encode(&root); err != nil {
		return nil, err
	}
	return []byte(buf.String()), nil
}

func setJSONPath(root map[string]any, fieldPath, value string) error {
	parts := strings.Split(fieldPath, ".")
	cur := any(root)
	for i, part := range parts {
		m, ok := cur.(map[string]any)
		if !ok {
			return fmt.Errorf("bad json path")
		}
		if i == len(parts)-1 {
			m[part] = value
			return nil
		}
		next, ok := m[part]
		if !ok {
			child := map[string]any{}
			m[part] = child
			cur = child
			continue
		}
		cur = next
	}
	return nil
}

func setYAMLPath(root *yaml.Node, fieldPath, value string) error {
	parts := strings.Split(fieldPath, ".")
	if len(root.Content) == 0 {
		return fmt.Errorf("empty yaml")
	}
	node := root.Content[0]
	for i, part := range parts {
		if node.Kind != yaml.MappingNode {
			return fmt.Errorf("bad yaml path")
		}
		idx := -1
		for j := 0; j < len(node.Content); j += 2 {
			if node.Content[j].Value == part {
				idx = j + 1
				break
			}
		}
		if idx < 0 {
			return fmt.Errorf("missing yaml key")
		}
		if i == len(parts)-1 {
			node.Content[idx].Kind = yaml.ScalarNode
			node.Content[idx].Value = value
			return nil
		}
		node = node.Content[idx]
	}
	return nil
}

func PlaintextHits(bundlePath string, needles []string) (int, error) {
	bundle, err := archive.ReadBundle(bundlePath)
	if err != nil {
		return 0, err
	}
	count := 0
	for member, payload := range bundle.Members {
		if member == ManifestMember {
			continue
		}
		text := string(payload)
		for _, needle := range needles {
			if strings.Contains(text, needle) {
				count++
			}
		}
	}
	return count, nil
}

func BundleSHA256(path string) (string, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return "", err
	}
	sum := sha256.Sum256(data)
	return hex.EncodeToString(sum[:]), nil
}
