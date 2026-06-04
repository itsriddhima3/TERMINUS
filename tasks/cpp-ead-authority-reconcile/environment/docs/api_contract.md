# Authority API (port 3000)

Base URL: `http://127.0.0.1:3000`

| Method | Path | Query | Response |
|--------|------|-------|----------|
| GET | `/health` | — | `{ "ok": true }` |
| GET | `/api/v1/creators/resolve` | `name` | `{ "name", "auth_id" }` |
| GET | `/api/v1/subjects/resolve` | `head`, `tier` | `{ "head", "tier", "subj_id" }` |
| GET | `/api/v1/places/resolve` | `name`, `tier` | `{ "name", "tier", "place_id" }` |
| GET | `/api/v1/accession/validate` | `collection_id`, `candidate` | `{ "collection_id", "candidate", "valid", ... }` |

Subject heads are indexed at tier 1 without subdivision suffixes. Place resolve selects the lookup table named by the `tier` query parameter; approximate geographic headings in EAD require tier 2 for the geographic string after parenthetical stripping. See handbook section 18.2 when client tier and resolved place ids disagree.
