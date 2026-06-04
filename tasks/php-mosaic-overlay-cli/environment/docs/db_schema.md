# Database schema reference

The SQLite database at `/app/state/challenges.db` is created at image
build time from `/app/assets/seed/seed_pack.sql`. The schema is shared
across the play loop, the verifier, and the developer subcommands.

## packs

| column     | type    | notes                              |
|------------|---------|------------------------------------|
| pack_id    | TEXT PK | seeded with one row (starter_pack) |
| pack_label | TEXT    | human-readable label               |
| created_at | INTEGER | epoch milliseconds                 |

## challenges

| column        | type    | notes                                                  |
|---------------|---------|--------------------------------------------------------|
| challenge_id  | TEXT PK | seeded: ch_alpha, ch_bravo                             |
| pack_id       | TEXT FK | references packs.pack_id                               |
| source_width  | INTEGER | width in source pixels                                 |
| source_height | INTEGER | height in source pixels                                |
| scene_a_path  | TEXT    | relative path to first scene PNG                       |
| scene_b_path  | TEXT    | relative path to second scene PNG                      |
| regions_path  | TEXT    | relative path to JSON polygon definitions              |
| base_units    | INTEGER | base value used by the score composer (default 1000)   |

## region_defs

| column         | type    | notes                                          |
|----------------|---------|------------------------------------------------|
| challenge_id   | TEXT FK | references challenges.challenge_id             |
| region_id      | TEXT    | per-challenge unique id (e.g. alpha_region_top)|
| region_label   | TEXT    | human label                                    |
| polygon_json   | TEXT    | JSON array of `[u, v]` source-pixel vertices   |

## sessions

| column              | type     | notes                                                      |
|---------------------|----------|------------------------------------------------------------|
| session_row_id      | INTEGER  | AUTOINCREMENT primary key                                  |
| challenge_id        | TEXT FK  | references challenges.challenge_id                         |
| opened_at_ms        | INTEGER  | epoch milliseconds when session was opened                 |
| closed_at_ms        | INTEGER  | epoch milliseconds when session was closed (null while open) |
| closed_reason       | TEXT     | one of: paused, quit, NULL while open                      |
| score               | INTEGER  | final composed value, written by Sink::commit              |
| component_breakdown | TEXT     | JSON payload describing the per-component arithmetic       |

## marks

| column            | type     | notes                                          |
|-------------------|----------|------------------------------------------------|
| mark_row_id       | INTEGER  | AUTOINCREMENT primary key                      |
| session_row_id    | INTEGER  | references sessions.session_row_id             |
| sequence_no       | INTEGER  | per-session rolling sequence number            |
| raised_at_ms      | INTEGER  | engine clock timestamp                         |
| input_col         | INTEGER  | rendered-cell column the player supplied       |
| input_row         | INTEGER  | rendered-cell row the player supplied          |
| matched_region_id | TEXT     | id of the region polygon matched (or NULL)     |
| matched           | INTEGER  | 1 if the cell resolved inside a polygon, 0 not |

## hints

| column            | type     | notes                                          |
|-------------------|----------|------------------------------------------------|
| hint_row_id       | INTEGER  | AUTOINCREMENT primary key                      |
| session_row_id    | INTEGER  | references sessions.session_row_id             |
| sequence_no       | INTEGER  | per-session rolling sequence number            |
| raised_at_ms      | INTEGER  | engine clock timestamp                         |
| incurred_penalty  | INTEGER  | per-draw penalty assessed by the rate gate     |
| bucket_start_ms   | INTEGER  | start-of-bucket timestamp at admission time    |

## audit_log

| column         | type    | notes                                  |
|----------------|---------|----------------------------------------|
| audit_row_id   | INTEGER | AUTOINCREMENT primary key              |
| occurred_at_ms | INTEGER | epoch milliseconds                     |
| action         | TEXT    | one of: open_session, resume_session, reset |
| detail         | TEXT    | optional JSON payload                  |
