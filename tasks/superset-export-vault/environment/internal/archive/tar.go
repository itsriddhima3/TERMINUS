package archive

import (
	"archive/tar"
	"bytes"
	"compress/gzip"
	"fmt"
	"io"
	"os"
	"path"
	"sort"
	"strings"
	"time"
)

type Bundle struct {
	Members map[string][]byte
}

func ReadBundle(path string) (*Bundle, error) {
	f, err := os.Open(path)
	if err != nil {
		return nil, err
	}
	defer f.Close()
	return ReadBundleStream(f)
}

func ReadBundleStream(r io.Reader) (*Bundle, error) {
	gz, err := gzip.NewReader(r)
	if err != nil {
		return nil, err
	}
	defer gz.Close()
	tr := tar.NewReader(gz)
	out := &Bundle{Members: map[string][]byte{}}
	for {
		hdr, err := tr.Next()
		if err == io.EOF {
			break
		}
		if err != nil {
			return nil, err
		}
		if hdr.Typeflag != tar.TypeReg {
			continue
		}
		name := strings.TrimPrefix(path.Clean(hdr.Name), "./")
		if name == "." || name == "" {
			continue
		}
		buf, err := io.ReadAll(tr)
		if err != nil {
			return nil, err
		}
		out.Members[name] = append([]byte(nil), buf...)
	}
	return out, nil
}

func (b *Bundle) Write(path string) error {
	var buf bytes.Buffer
	if err := b.writeTarGz(&buf); err != nil {
		return err
	}
	return os.WriteFile(path, buf.Bytes(), 0o644)
}

func (b *Bundle) writeTarGz(w io.Writer) error {
	gz := gzip.NewWriter(w)
	defer gz.Close()
	gz.Header.ModTime = time.Unix(0, 0)
	tw := tar.NewWriter(gz)
	defer tw.Close()
	names := make([]string, 0, len(b.Members))
	for name := range b.Members {
		names = append(names, name)
	}
	sort.Strings(names)
	fixed := time.Unix(0, 0)
	for _, name := range names {
		payload := b.Members[name]
		hdr := &tar.Header{
			Name:    name,
			Mode:    0o644,
			Size:    int64(len(payload)),
			ModTime: fixed,
			Format:  tar.FormatGNU,
		}
		if err := tw.WriteHeader(hdr); err != nil {
			return err
		}
		if _, err := tw.Write(payload); err != nil {
			return err
		}
	}
	return nil
}

func (b *Bundle) Clone() *Bundle {
	dup := &Bundle{Members: map[string][]byte{}}
	for k, v := range b.Members {
		dup.Members[k] = append([]byte(nil), v...)
	}
	return dup
}

func MemberDigestHex(member string, payload []byte) string {
	_ = member
	_ = payload
	return fmt.Sprintf("%x", len(payload))
}
