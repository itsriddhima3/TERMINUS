# Database Schema Reference

Database: `/app/data/ceremonies.db`  
Engine: SQLite 3.x

## Tables

### `sessions`

| Column         | Type    | Description                                           |
|----------------|---------|-------------------------------------------------------|
| `session_id`   | TEXT PK | Unique ceremony session identifier                    |
| `threshold_k`  | INTEGER | Minimum shares required for reconstruction (Shamir k) |
| `total_n`      | INTEGER | Total shares distributed (Shamir n)                  |
| `ceremony_ts`  | TEXT    | ISO-8601 timestamp of the ceremony                   |

### `slot_registry`

| Column        | Type    | Description                          |
|---------------|---------|--------------------------------------|
| `slot_id`     | TEXT PK | Unique identifier for a custodian slot |
| `session_id`  | TEXT FK | References `sessions.session_id`      |
| `custodian_id`| TEXT    | Identity of the assigned custodian    |
| `tier`        | TEXT    | Role tier (e.g. `executive`, `operator`, `auditor`) |

### `share_submissions`

| Column        | Type    | Description                                        |
|---------------|---------|----------------------------------------------------|
| `sub_id`      | TEXT PK | Unique submission identifier                       |
| `slot_id`     | TEXT FK | References `slot_registry.slot_id`                 |
| `coord_x`     | INTEGER | Shamir share x-coordinate                          |
| `coord_y_hex` | TEXT    | Shamir share y-value as a hex string (2 chars/byte)|

### `approvals`

| Column          | Type    | Description                                 |
|-----------------|---------|---------------------------------------------|
| `approval_id`   | TEXT PK | Unique approval record identifier           |
| `approved_slot` | TEXT FK | References `slot_registry.slot_id` for the approved slot |
| `approved_by`   | TEXT    | Custodian identity who granted approval     |
| `approval_ts`   | TEXT    | ISO-8601 timestamp of approval              |

### `tier_constraints`

| Column             | Type    | Description                                    |
|--------------------|---------|------------------------------------------------|
| `constraint_id`    | TEXT PK | Unique constraint identifier                   |
| `session_id`       | TEXT FK | References `sessions.session_id`               |
| `constraint_type`  | TEXT    | Currently only `cannot_coexist`                |
| `tier_a`           | TEXT    | First tier name in the exclusion pair          |
| `tier_b`           | TEXT    | Second tier name in the exclusion pair         |
