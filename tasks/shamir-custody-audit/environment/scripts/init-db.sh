#!/bin/bash
# Initialises the ceremony SQLite database at /app/data/ceremonies.db.
# Share byte vectors are computed over GF(2^8) with irreducible poly 0x11b.
# Reconstruction uses Lagrange interpolation at x=0 (the zero coordinate).
set -euo pipefail

DB=/app/data/ceremonies.db
mkdir -p /app/data
rm -f "$DB"

sqlite3 "$DB" <<'SQL'
CREATE TABLE sessions (
    session_id   TEXT PRIMARY KEY,
    initiated_at INTEGER NOT NULL,
    threshold_k  INTEGER NOT NULL,
    total_slots  INTEGER NOT NULL
);

CREATE TABLE slot_registry (
    slot_id      TEXT PRIMARY KEY,
    session_id   TEXT NOT NULL REFERENCES sessions(session_id),
    slot_index   INTEGER NOT NULL,
    custodian_id TEXT NOT NULL,
    auth_tier    TEXT NOT NULL
);

CREATE TABLE share_submissions (
    submission_id TEXT PRIMARY KEY,
    slot_id       TEXT NOT NULL REFERENCES slot_registry(slot_id),
    coord_x       INTEGER NOT NULL,
    coord_y_hex   TEXT NOT NULL,
    submitted_at  INTEGER NOT NULL
);

CREATE TABLE ceremony_approvals (
    approval_id   TEXT PRIMARY KEY,
    session_id    TEXT NOT NULL,
    approved_slot TEXT NOT NULL REFERENCES slot_registry(slot_id),
    approved_by   TEXT NOT NULL,
    approved_at   INTEGER NOT NULL
);

CREATE TABLE tier_constraints (
    constraint_id TEXT PRIMARY KEY,
    tier_alpha    TEXT NOT NULL,
    tier_beta     TEXT NOT NULL,
    rule_kind     TEXT NOT NULL
);

-- Tier constraint: executive and auditor tiers cannot coexist in a quorum.
INSERT INTO tier_constraints VALUES ('tc-001','executive','auditor','cannot_coexist');

-- -----------------------------------------------------------------------
-- sess-alpha: 5 slots, threshold=3, 3 submissions, valid approvals.
-- Secret (8 bytes): 41 42 43 44 45 46 47 48  ("ABCDEFGH")
-- Polynomial per byte i: f(x) = s_i XOR gfMul(03,x) XOR gfMul(05,x^2)
-- Share at x=1 (each byte s XOR 06): 47 44 45 42 43 40 41 4e
-- Share at x=2 (each byte s XOR 12 XOR 14 = s XOR 06): wait...
--   gfMul(03,2)=06; gfMul(05,gfMul(2,2))=gfMul(05,04)=14(0x14)
--   so x=2: s XOR 06 XOR 14 = s XOR 12 ... XOR gives:
--     06 = 00000110, 14=00010100: 06 XOR 14 = 00010010 = 0x12
--   x=2: s XOR 0x12 → byte seq: 53 50 51 56 57 54 55 5a
-- Share at x=3:
--   gfMul(03,3)=05; gfMul(05,gfMul(3,3))=gfMul(05,05)=11(0x11)
--   x=3: s XOR 05 XOR 11 = s XOR 14 → byte seq: 55 56 57 50 51 52 53 5c
-- -----------------------------------------------------------------------
INSERT INTO sessions VALUES ('sess-alpha',1700000000,3,5);
INSERT INTO slot_registry VALUES
    ('slt-a1','sess-alpha',1,'cust-01','primary'),
    ('slt-a2','sess-alpha',2,'cust-02','primary'),
    ('slt-a3','sess-alpha',3,'cust-03','secondary'),
    ('slt-a4','sess-alpha',4,'cust-04','secondary'),
    ('slt-a5','sess-alpha',5,'cust-05','backup');
INSERT INTO share_submissions VALUES
    ('sub-a1','slt-a1',1,'474445424340414e',1700000100),
    ('sub-a2','slt-a2',2,'535051565754555a',1700000200),
    ('sub-a3','slt-a3',3,'555657505152535c',1700000300);
-- Approvals reference slots by slot_id (approved_slot = slot_id).
-- Approver identities differ from custodian identities (role separation).
INSERT INTO ceremony_approvals VALUES
    ('apv-a1','sess-alpha','slt-a1','apvr-01',1700000150),
    ('apv-a2','sess-alpha','slt-a2','apvr-02',1700000250),
    ('apv-a3','sess-alpha','slt-a3','apvr-03',1700000350);

-- -----------------------------------------------------------------------
-- sess-beta: 4 slots, threshold=3, only 2 submissions (insufficient).
-- -----------------------------------------------------------------------
INSERT INTO sessions VALUES ('sess-beta',1700001000,3,4);
INSERT INTO slot_registry VALUES
    ('slt-b1','sess-beta',1,'cust-11','primary'),
    ('slt-b2','sess-beta',2,'cust-12','secondary'),
    ('slt-b3','sess-beta',3,'cust-13','backup'),
    ('slt-b4','sess-beta',4,'cust-14','primary');
INSERT INTO share_submissions VALUES
    ('sub-b1','slt-b1',1,'aabbccdd11223344',1700001100),
    ('sub-b2','slt-b2',2,'eeff001122334455',1700001200);
INSERT INTO ceremony_approvals VALUES
    ('apv-b1','sess-beta','slt-b1','apvr-11',1700001150),
    ('apv-b2','sess-beta','slt-b2','apvr-12',1700001250);

-- -----------------------------------------------------------------------
-- sess-gamma: 5 slots, threshold=3, 3 submissions.
-- BOTH 'executive' and 'auditor' tiers present -> cannot_coexist violation.
-- Secret (8 bytes): 61 62 63 64 65 66 67 68  ("abcdefgh")
-- Polynomial per byte i: f(x) = s_i XOR gfMul(09,x) XOR gfMul(0b,x^2)
--   x=1: s XOR 09 XOR 0b = s XOR 02 → 63 60 61 66 67 64 65 6a
--   x=2: s XOR 12 XOR 2c = s XOR 3e → 5f 5c 5d 5a 5b 58 59 56
--   x=3: s XOR 1b XOR 27 = s XOR 3c → 5d 5e 5f 58 59 5a 5b 54
-- -----------------------------------------------------------------------
INSERT INTO sessions VALUES ('sess-gamma',1700002000,3,5);
INSERT INTO slot_registry VALUES
    ('slt-g1','sess-gamma',1,'cust-21','executive'),
    ('slt-g2','sess-gamma',2,'cust-22','auditor'),
    ('slt-g3','sess-gamma',3,'cust-23','backup'),
    ('slt-g4','sess-gamma',4,'cust-24','primary'),
    ('slt-g5','sess-gamma',5,'cust-25','secondary');
INSERT INTO share_submissions VALUES
    ('sub-g1','slt-g1',1,'636061666764656a',1700002100),
    ('sub-g2','slt-g2',2,'5f5c5d5a5b585956',1700002200),
    ('sub-g3','slt-g3',3,'5d5e5f58595a5b54',1700002300);
INSERT INTO ceremony_approvals VALUES
    ('apv-g1','sess-gamma','slt-g1','apvr-21',1700002150),
    ('apv-g2','sess-gamma','slt-g2','apvr-22',1700002250),
    ('apv-g3','sess-gamma','slt-g3','apvr-23',1700002350);

-- -----------------------------------------------------------------------
-- sess-delta: 3 slots, threshold=2, 2 submissions.
-- Only 'executive' tier present (no 'auditor') -> quorum_valid=true.
-- Secret (8 bytes): 70 71 72 73 74 75 76 77  ("pqrstuvw")
-- Polynomial per byte i: f(x) = s_i XOR gfMul(0d,x)  [degree-1, threshold=2]
--   gfMul(0d,1)=0d; gfMul(0d,2)=1a
--   x=1: s XOR 0d → 7d 7c 7f 7e 79 78 7b 7a
--   x=2: s XOR 1a → 6a 6b 68 69 6e 6f 6c 6d
-- -----------------------------------------------------------------------
INSERT INTO sessions VALUES ('sess-delta',1700003000,2,3);
INSERT INTO slot_registry VALUES
    ('slt-d1','sess-delta',1,'cust-31','executive'),
    ('slt-d2','sess-delta',2,'cust-32','primary'),
    ('slt-d3','sess-delta',3,'cust-33','secondary');
INSERT INTO share_submissions VALUES
    ('sub-d1','slt-d1',1,'7d7c7f7e79787b7a',1700003100),
    ('sub-d2','slt-d2',2,'6a6b68696e6f6c6d',1700003200);
INSERT INTO ceremony_approvals VALUES
    ('apv-d1','sess-delta','slt-d1','apvr-31',1700003150),
    ('apv-d2','sess-delta','slt-d2','apvr-32',1700003250);

SQL

echo "Database initialised at $DB"
sqlite3 "$DB" "SELECT COUNT(*) || ' sessions' FROM sessions;"
sqlite3 "$DB" "SELECT COUNT(*) || ' slot_registry rows' FROM slot_registry;"
sqlite3 "$DB" "SELECT COUNT(*) || ' share_submissions rows' FROM share_submissions;"
sqlite3 "$DB" "SELECT COUNT(*) || ' ceremony_approvals rows' FROM ceremony_approvals;"
