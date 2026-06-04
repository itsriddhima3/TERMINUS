# HTTP surface

All routes are rooted at the configured base URL (`http://127.0.0.1:8080` in the shipped profile).

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| GET | /health | no | Liveness JSON |
| POST | /auth/login | no | Issue bearer access token |
| GET | /resource/echo | bearer | Protected echo of subject |
| GET | /.well-known/jwks.json | no | Public keys for active and previous kids |

Login body JSON fields: `username`, `password`.
Successful login returns `access_token`, `token_type` (`Bearer`), `expires_in` (seconds).

Protected routes expect header `Authorization: Bearer <token>`.
