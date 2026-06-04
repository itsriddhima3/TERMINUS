package gateway

import (
	"net/http"
	"net/http/httptest"
)

type Server struct {
	HTTP   *httptest.Server
	Handle *Handler
}

func Start(profile string) *Server {
	h := NewHandler(profile)
	mux := http.NewServeMux()
	mux.HandleFunc("/api/v1/post", h.ServePost)
	mux.HandleFunc("/api/v1/probe", h.ServeProbe)
	mux.HandleFunc("/api/v1/commit", h.ServeCommit)
	srv := httptest.NewServer(mux)
	return &Server{HTTP: srv, Handle: h}
}

func (s *Server) Close() {
	if s != nil && s.HTTP != nil {
		s.HTTP.Close()
	}
}

func (s *Server) BaseURL() string {
	if s == nil || s.HTTP == nil {
		return ""
	}
	return s.HTTP.URL
}
