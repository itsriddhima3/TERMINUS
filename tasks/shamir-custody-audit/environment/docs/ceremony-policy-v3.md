# Distributed Custody Recovery Ceremony Policy
## Reference: DCRC-POL-v3 — Revision 3.2.1

**Classification:** Internal — Restricted Distribution  
**Document Owner:** Key Ceremony Governance Board  
**Effective Date:** 2024-01-15  
**Review Cycle:** Annual  
**Supersedes:** DCRC-POL-v2.4, DCRC-POL-v2.3, DCRC-POL-v1.x series

---

## Table of Contents

1. Scope and Purpose
2. Definitions and Glossary
3. Regulatory and Standards Framework
4. System Architecture Overview
5. Custodian Roles and Responsibilities
6. Pre-Ceremony Requirements and Prerequisites
7. Custodian Eligibility, Verification, and Onboarding
8. Share Distribution Protocol and Key Splitting
9. Recovery Ceremony Procedures
10. Quorum Formation Rules and Validation
11. Policy Enforcement Rules
12. Cryptographic Verification Requirements
13. Database Schema and Approval Linkage Model
14. Exception Handling and Edge Cases
15. Audit, Logging, and Compliance
16. Incident Response and Escalation
17. Appendix A — Authorization Tier Definitions
18. Appendix B — Tier Exclusion Matrix
19. Appendix C — Sample Ceremony Records and Worked Examples
20. Appendix D — Regulatory References and Cross-Mapping
21. Appendix E — Revision History

---

## Chapter 1 — Scope and Purpose

### 1.1 Document Purpose

This document governs the operational procedures, technical requirements, and policy enforcement rules for all distributed custody recovery ceremonies conducted under the authority of the Key Ceremony Governance Board. A recovery ceremony is defined as the formal, witnessed process by which a cryptographic secret previously split into shares under a threshold secret-sharing scheme is reconstituted from a qualifying subset of those shares.

This policy applies to all recovery ceremonies regardless of the sensitivity classification of the secret being recovered, the number of participating custodians, or the authorization tiers represented. Exceptions to this policy require written approval from the Governance Board and must be documented in the ceremony audit record within 48 hours of the ceremony.

### 1.2 Scope of Application

This policy applies to:

(a) All primary root key recovery ceremonies for infrastructure-class secrets managed by the operations teams.

(b) All secondary and contingency key ceremonies where the affected secret has been assigned a Protection Level of 2 or higher under the organizational classification scheme.

(c) Backup recovery operations performed under emergency protocols, subject to the escalated approval requirements defined in Chapter 16.

(d) Test and rehearsal ceremonies when conducted with production-equivalent tooling, even when no actual cryptographic material is involved.

(e) Audit-mode ceremonies in which an approved automated tool replays the ceremony records from a prior physical ceremony to verify correctness and policy compliance.

### 1.3 Objectives

The primary objectives of this policy are to:

1. Ensure that no single custodian, team, or organizational unit can unilaterally reconstitute a secret protected under this policy without the participation of the required quorum of authorized custodians.

2. Establish clear, auditable rules for determining when a recovery ceremony is valid and when it must be rejected.

3. Define the cryptographic verification methods by which the integrity of recovered secrets can be confirmed without re-exposing the full secret to unnecessary parties.

4. Specify the database schema and linkage rules that automated audit tools must use when evaluating ceremony records stored in the operational database.

5. Prevent role conflicts that could compromise the independence requirement of the multi-party scheme.

### 1.4 Relationship to Other Documents

This policy is supplemented by, but takes precedence over, the following documents:

- Key Ceremony Operational Runbook (DCRC-RB-v3)
- Custodian Onboarding Handbook (COH-v2)
- Emergency Recovery Procedures (ERP-v1.5)
- Automated Audit Tool Specification (AATS-v2, incorporated by reference)

In case of conflict between this policy and any of the supplementary documents, this policy prevails.

---

## Chapter 2 — Definitions and Glossary

For the purposes of this document, the following definitions apply. Terms defined here appear in **bold** on first use in the main body of the document.

**Approval Record**: A database entry in the `ceremony_approvals` table that records the formal endorsement of a submitted share. Each approval record is associated with a specific slot by the slot identifier stored in the `approved_slot` field. Approval records must not be confused with submission records; they represent a distinct, independent attestation act performed after share submission.

**Approver**: An individual who endorses a submitted share during the review phase of the ceremony. An approver must hold a different identity from the custodian who submitted the share being approved. The approver's identity is recorded in the `approved_by` field of the approval record.

**Authorization Tier**: A categorical designation assigned to a custodian slot that indicates the organizational level and trust class of the custodian occupying that slot. Tiers are defined in Appendix A. The primary tiers are: `primary`, `secondary`, `backup`, `executive`, and `auditor`. Additional tiers may be defined for specialized ceremonies.

**Ceremony**: See *Recovery Ceremony*.

**Ceremony Session**: A bounded event during which a specific set of custodians assemble to present their shares with the intent of reconstructing a secret. Each session is assigned a unique session identifier and is persisted as a record in the `sessions` database table. A ceremony session has a defined threshold, a set of registered custodian slots, and a collection of submitted shares.

**Concentration Constraint**: A policy rule that limits the number of participating custodians from any single organizational unit to at most a specified fraction of the total quorum. Concentration constraints are distinct from exclusion constraints and are evaluated separately.

**Coord-X**: The x-coordinate of a share point in the finite field. For each custodian slot, the x-coordinate is assigned at share generation time and is stored in the `coord_x` field of the `share_submissions` table. X-coordinates must be non-zero elements of the field.

**Coord-Y**: The y-coordinate of a share point. The y-coordinate is the evaluation of the secret polynomial at the corresponding x-coordinate. It is stored as a hexadecimal string in the `coord_y_hex` field of the `share_submissions` table. The length of the hex string must equal twice the byte length of the protected secret.

**Custodian**: An individual who has been formally onboarded under the custodian onboarding process and has been assigned one or more slots in active ceremony sessions. A custodian holds one share fragment corresponding to their slot.

**Custodian Identity**: The stable identifier assigned to a custodian during onboarding, stored in the `custodian_id` field of the `slot_registry` table. Custodian identities are distinct from approver identities; an individual may hold both, but they are represented as separate identity strings in the database.

**Dossier**: This document in its entirety, including all appendices and embedded parameter specifications. Automated audit tools should parse this document to extract runtime parameters before processing any ceremony records.

**Exclusion Constraint**: A policy rule that prevents two specified authorization tiers from both being represented in a ceremony quorum simultaneously. When an exclusion constraint applies to tiers A and B, a ceremony in which at least one custodian holds a tier-A slot AND at least one custodian holds a tier-B slot is considered invalid. The presence of tier A alone, or tier B alone, does not trigger the constraint. Exclusion constraints are defined in the `tier_constraints` database table and in Appendix B.

**Fingerprint**: A short, fixed-length cryptographic summary derived from the recovered secret bytes. The fingerprint is used to confirm that the same secret has been recovered across multiple ceremony attempts without requiring that the full secret bytes be exchanged or logged. The method for computing the fingerprint is defined in Section 12.3.

**Finite Field**: The algebraic structure over which share arithmetic is performed. This policy mandates the use of the binary extension field GF(2^8) defined by the irreducible polynomial x^8 + x^4 + x^3 + x + 1 (hexadecimal representation 0x11b). All polynomial evaluation, addition, and multiplication operations are performed within this field.

**Governance Board**: The Key Ceremony Governance Board, which holds ultimate authority over all policies in this document series. The Governance Board consists of the Chief Security Officer, the Deputy Chief Security Officer, the Head of Operations Security, and two external advisors appointed for fixed terms.

**Interpolation**: The mathematical process of recovering a polynomial's constant term from a set of evaluation points. In the context of this policy, interpolation always means Lagrange interpolation at the zero coordinate of GF(2^8). See Section 12.3 for the detailed specification.

**Interpolation Target**: The field element at which the interpolated polynomial is evaluated to recover the secret. This policy mandates that the interpolation target is the zero element of GF(2^8), denoted 0x00. See Section 12.3. Any tool that evaluates the polynomial at a non-zero target will produce an incorrect reconstruction.

**Lagrange Basis Polynomial**: In the context of Lagrange interpolation over a finite field, the Lagrange basis polynomial L_i(x) for share i is the unique polynomial of degree (k-1) that equals 1 at x_i and 0 at all other x_j (j ≠ i), where {x_1, ..., x_k} are the x-coordinates of the k shares used in reconstruction. The reconstructed secret is the sum (XOR) of y_i * L_i(0) over all i from 1 to k.

**Linked Approval**: An approval record is considered *linked* to a slot when the `approved_slot` field of the approval record exactly matches the `slot_id` field of the slot registry entry. This is the canonical linkage relation. Do not confuse `approved_slot` (a slot identifier) with `approved_by` (an approver identity). These fields serve entirely different purposes: `approved_by` identifies who performed the approval action, while `approved_slot` identifies which slot was approved.

**Policy Violation**: A documented instance in which the composition of a ceremony quorum or the conduct of the ceremony fails to meet one or more requirements of this policy. Policy violations are logged in the audit report and cause the ceremony's verification status to be set to `policy_violation` rather than `verified`.

**Protection Level**: A classification assigned to a protected secret that determines the applicable ceremony requirements. Protection Level 1 (PL1) is the baseline; Protection Level 2 (PL2) and above impose additional requirements such as physical witness requirements and extended retention of ceremony records.

**Quorum**: The subset of registered custodian slots whose submissions are used for secret reconstruction in a given ceremony attempt. The quorum must meet the session's threshold requirement and must satisfy all applicable policy constraints, including exclusion constraints, concentration constraints, and role separation requirements.

**Recovery Ceremony**: The formal event defined in this policy during which a previously split secret is reconstituted from a threshold-qualifying subset of shares. The ceremony produces an audit record regardless of whether reconstruction succeeds.

**Role Separation**: The requirement that the individual who submits a share (the custodian) and the individual who approves that submission (the approver) must be different people. This is enforced by the database design: the `custodian_id` field in `slot_registry` and the `approved_by` field in `ceremony_approvals` must hold distinct identity strings for any linked approval.

**Secret**: The cryptographic material being protected under this scheme. Secrets may include root private keys, master key encryption keys, backup decryption keys, or other high-value material. For the purposes of this policy, the secret is treated as a sequence of bytes without regard to its semantic content.

**Session**: See *Ceremony Session*.

**Share**: A single evaluation point (x, y) of the secret polynomial in GF(2^8). Each custodian holds exactly one share. The share's x-coordinate is fixed at slot creation time; the y-coordinate is the output of the polynomial evaluated at that x-coordinate.

**Slot**: A numbered position within a ceremony session. Each slot is assigned to exactly one custodian and has a fixed authorization tier. Slots are persisted in the `slot_registry` table.

**Slot Identifier**: The unique string assigned to each slot in the `slot_registry` table, stored in the `slot_id` field. Slot identifiers are referenced by approval records through the `approved_slot` field. This is a fundamental design property: approvals are keyed to slots, not to custodians. This distinction matters because a custodian may hold slots in multiple sessions, and approval of a slot in one session must not propagate to other sessions.

**Threshold**: The minimum number of shares required to reconstruct the secret. If the session has N total slots, the threshold K determines how many distinct shares must be presented. A session with threshold K requires at least K submitted shares before reconstruction can be attempted. See Section 10 for threshold determination rules.

**Tier**: See *Authorization Tier*.

**Verification Status**: The final outcome field in an audit report entry for a ceremony session. Valid values are: `verified` (reconstruction succeeded and all policy checks passed), `failed` (reconstruction did not succeed), and `policy_violation` (reconstruction succeeded but one or more policy constraints were violated).

---

## Chapter 3 — Regulatory and Standards Framework

### 3.1 Applicable Standards

All recovery ceremonies governed by this policy must be conducted in compliance with the following standards and guidelines:

**NIST SP 800-57 Part 1 Rev. 5**: Key management recommendations, particularly Part 3 regarding key material handling during transitions and recovery operations.

**FIPS 140-3**: For ceremonies involving hardware security modules, all HSM modules must be FIPS 140-3 Level 3 certified or higher.

**ISO/IEC 27001:2022**: Information security management system requirements, specifically Annex A controls A.8.24 (Use of Cryptography) and A.8.12 (Data Leakage Prevention).

**Common Criteria EAL4+**: For ceremonies where the reconstructed secret will be imported into an evaluated product, the ceremony itself must be documented at a level of assurance consistent with EAL4 operational environment requirements.

### 3.2 Relationship to Organizational Policy

This policy operates under the umbrella of the organizational Information Security Policy (ISP-v7) and the Cryptographic Controls Policy (CCP-v4). In the event of a conflict, the more restrictive policy applies.

### 3.3 Audit Trail Requirements

All ceremony records must be retained for a minimum of seven years from the date of the ceremony. Retention applies to:

- The ceremony session record and all associated slot, submission, and approval records in the operational database.
- Signed witness attestations (physical documents or cryptographic signatures).
- The audit report produced by the automated audit tool, including all fingerprints and policy violation records.
- Any exception or waiver documentation.

---

## Chapter 4 — System Architecture Overview

### 4.1 Operational Database

The ceremony management system uses a relational database (SQLite for single-node deployments, PostgreSQL for distributed deployments) to store all ceremony records. The database schema is documented in full in Chapter 13. The five primary tables are:

- `sessions`: One row per ceremony session, recording the threshold and total slot count.
- `slot_registry`: One row per slot, recording the assigned custodian and authorization tier.
- `share_submissions`: One row per submitted share, recording the field coordinates.
- `ceremony_approvals`: One row per approval action, recording the endorsement of a submitted slot.
- `tier_constraints`: One row per policy constraint between authorization tiers.

### 4.2 Automated Audit Tool

The automated audit tool (referred to as "the tool" in the remainder of this document) is a command-line program that:

1. Connects to the operational database.
2. Parses this dossier to extract runtime parameters (see Section 12.3 and Section 13.4).
3. For each ceremony session in the database, performs the following:
   a. Loads the session, slot, submission, and approval records.
   b. Counts the number of slots with linked approval records.
   c. Attempts secret reconstruction from the submitted shares.
   d. Evaluates policy constraints against the participating slots.
   e. Produces a structured audit report entry.
4. Writes the complete audit report to the designated output path in JSON format.

### 4.3 Output Report Schema

The audit tool produces a JSON file with the following top-level structure:

```json
{
  "audit_results": [
    {
      "session_id": "<string>",
      "slots_loaded": <integer>,
      "approvals_linked": <integer>,
      "reconstruction_status": "<string>",
      "secret_fingerprint": "<string or null>",
      "threshold_met": <boolean>,
      "quorum_valid": <boolean>,
      "policy_violations": ["<string>", ...],
      "verification_status": "<string>"
    }
  ]
}
```

All fields are mandatory. The `policy_violations` array must be present even when empty (use an empty array `[]`, not `null`). The `secret_fingerprint` field is `null` when reconstruction did not succeed.

### 4.4 Field Descriptions

**`session_id`**: The unique identifier of the ceremony session, taken directly from the `session_id` column of the `sessions` table.

**`slots_loaded`**: The count of slot registry rows loaded for this session. This count should equal `total_slots` from the sessions table when the database is consistent.

**`approvals_linked`**: The count of distinct slots for which at least one linked approval record exists. Linkage is determined by matching the `approved_slot` field of approval records to the `slot_id` field of slot registry rows. See Chapter 13 for the precise linkage specification.

**`reconstruction_status`**: One of `success`, `insufficient_shares`, or `no_shares`. Set to `success` only when the threshold was met and the interpolation produced a result. Set to `insufficient_shares` when the number of submitted shares is less than the session threshold. Set to `no_shares` when no submissions exist for the session.

**`secret_fingerprint`**: The fingerprint string when reconstruction succeeded, `null` otherwise. Computation method defined in Section 12.3.

**`threshold_met`**: Boolean. True when the count of submitted shares is greater than or equal to the session threshold K.

**`quorum_valid`**: Boolean. True when no policy violations were detected among the participating slots.

**`policy_violations`**: List of violation description strings. Each string names the constraint type and the tiers involved, formatted as `<constraint_type>:<tier_a>+<tier_b>`.

**`verification_status`**: One of `verified`, `failed`, or `policy_violation`. See Section 12.4 for the derivation rules.

---

## Chapter 5 — Custodian Roles and Responsibilities

### 5.1 Custodian Classification

Every individual participating as a share holder in a ceremony is classified into exactly one authorization tier. Tiers reflect organizational position, operational responsibility, and accountability level. The classification system is designed so that mixing custodians from different tiers in appropriate proportions provides defense-in-depth against single-party compromise.

### 5.2 Primary Tier Custodians

Primary tier custodians are permanent members of the key custodian roster. They are typically senior technical staff with long tenure and deep familiarity with the ceremony process. Their responsibilities include:

- Maintaining the physical security of their share hardware token.
- Attending all scheduled ceremony rehearsals.
- Responding to emergency mobilization requests within the time window specified in the Emergency Recovery Procedures.
- Reporting any suspected compromise of their share or identity credentials immediately to the Governance Board.

Primary custodians must complete re-certification annually. Re-certification includes a background check refresh, a review of changes to this policy, and a technical assessment of their ceremony operational skills.

### 5.3 Secondary Tier Custodians

Secondary tier custodians serve as alternates for primary tier custodians and may be drawn from a broader pool of qualified technical staff. They carry the same share management responsibilities as primary custodians but are not required to maintain the same level of constant readiness. Secondary custodians are activated when primary custodians are unavailable, particularly in geographically distributed ceremonies.

### 5.4 Backup Tier Custodians

Backup tier custodians hold shares specifically designated for use in disaster recovery scenarios. Their shares are generated at the time of the primary ceremony and stored in secured escrow. Backup custodians are expected to be called upon rarely, but their readiness is verified annually through a sealed-envelope attestation process.

### 5.5 Executive Tier Custodians

Executive tier custodians are senior organizational leadership who hold shares as a governance control. Their participation ensures that high-stakes recovery ceremonies have executive awareness and authorization. Because executive custodians hold authority over the approver function as well, they are subject to the exclusive-pair constraint with auditor tier custodians, as defined in Appendix B and Chapter 11. This constraint exists because combining executive authority with independent audit authority in the same ceremony would undermine the separation of duties principle.

When an executive tier custodian participates in a ceremony, all other participants must be drawn from non-executive, non-auditor authorization tiers, or from tiers not listed in any exclusion pair with the executive tier. The executive tier's exclusion constraints are listed exhaustively in Appendix B; implementers must consult that appendix and not rely on hardcoded assumptions about which tiers conflict.

### 5.6 Auditor Tier Custodians

Auditor tier custodians are independent oversight personnel. Their role in a ceremony is to provide a neutral, accountable witness to the reconstruction process. Because auditor tier custodians are expected to operate independently from all operational command chains, they must never share a quorum with executive tier custodians. This constraint is reciprocal: the presence of an executive in a quorum that also contains an auditor, or an auditor in a quorum that also contains an executive, invalidates the ceremony.

### 5.7 Observer Status

Individuals who attend a ceremony in observer capacity do not submit shares and are not represented in the slot registry. They have no role in the policy enforcement evaluation and are not included in tier checks. The presence of observers does not affect the validity of the ceremony.

---

## Chapter 6 — Pre-Ceremony Requirements and Prerequisites

### 6.1 Scheduling and Notice

A recovery ceremony must be scheduled at least five business days in advance, except in emergency situations covered by Chapter 16. The scheduling notification must include the session identifier, the list of slot assignments, the expected date and time window, and the names of the designated ceremony officers.

For emergency ceremonies, the notice period may be reduced to four hours, but two Governance Board members must provide written authorization.

### 6.2 Facility Requirements

The ceremony facility must meet the following requirements:

(a) Physical access must be restricted to authorized ceremony participants and designated observers. A physical access log must be maintained.

(b) Electronic surveillance equipment (cameras, microphones) must be powered down or physically sealed during the ceremony. The only exception is the authorized ceremony recording system operated under the supervision of the Ceremony Officer.

(c) No network connectivity from the ceremony room to external networks is permitted during the ceremony. Air-gapped operation is required.

(d) The ceremony facility must have an uninterruptible power supply with a minimum 90-minute capacity.

### 6.3 Hardware Requirements

All hardware tokens used in the ceremony must be verified against their enrollment records before the ceremony begins. Verification includes:

1. Visual inspection of the token serial number against the enrollment database.
2. Cryptographic attestation using the token's built-in challenge-response mechanism.
3. Confirmation that the token's last-use timestamp is consistent with the custodian's stated history of access.

Any token that fails verification must be quarantined and the affected slot must be recorded as unavailable. If the resulting available shares fall below the threshold, the ceremony must be postponed.

### 6.4 Documentation Requirements

Before the ceremony begins, the Ceremony Officer must collect the following documents:

- Signed identity attestation from each participating custodian.
- Signed authorization letter from the Governance Board (or designated authority for lower protection-level ceremonies).
- Completed pre-ceremony checklist signed by at least two ceremony witnesses.

---

## Chapter 7 — Custodian Eligibility, Verification, and Onboarding

### 7.1 Eligibility Criteria

To be eligible for inclusion in a ceremony as a custodian, an individual must:

1. Be an active employee or contractor with a current, valid background investigation on file.
2. Have completed the Key Custodian Training Program and hold a valid certification.
3. Have no open disciplinary actions related to information security or data handling.
4. Have passed a biometric verification check within the preceding 12 months.
5. Not be subject to any active investigation by the security team.

### 7.2 Identity Verification at Ceremony Time

On the day of the ceremony, each custodian must present two forms of identity documentation. The Ceremony Officer records the document details and signs the witness attestation form. Identity verification must be completed before any custodian is permitted to access their token.

### 7.3 Custodian Onboarding Process

New custodians must be onboarded through the formal process documented in the Custodian Onboarding Handbook. Key steps include:

1. **Application and Review**: The candidate submits an application to the Governance Board. A three-member panel reviews the application.
2. **Background Investigation**: An enhanced background check is conducted.
3. **Training Completion**: The candidate completes the Key Custodian Training Program.
4. **Token Provisioning**: An enrollment ceremony is conducted to generate the custodian's share token.
5. **Database Registration**: The custodian's identity is registered in the operational database.
6. **First Ceremony Observation**: New custodians must observe one ceremony as a non-participating observer before their first active participation.

### 7.4 Custodian Offboarding

When a custodian leaves the program, their slot must be revoked and a key regeneration ceremony must be conducted within 30 days to generate new shares for all active sessions that included the departing custodian's slot. This ensures that the departing custodian cannot participate in future ceremonies.

---

## Chapter 8 — Share Distribution Protocol and Key Splitting

### 8.1 Mathematical Foundation

Share generation for secrets governed by this policy uses a (k, n) threshold secret sharing scheme based on polynomial interpolation over the finite field GF(2^8). The scheme was first described by Adi Shamir in "How to Share a Secret" (Communications of the ACM, 1979) and has been adapted here for use with the binary extension field defined in Section 2.

For a secret S of length L bytes, the scheme generates shares as follows:

1. A random polynomial f of degree (k-1) is selected for each byte position. For byte position i (0-indexed), the polynomial is f_i(x) = S[i] + a_{1,i}*x + a_{2,i}*x^2 + ... + a_{k-1,i}*x^(k-1), where all arithmetic is in GF(2^8). The constant term equals S[i].

2. For each of the n custodian slots, a distinct non-zero x-coordinate x_j (j = 1 to n) is assigned.

3. The share for slot j is the vector of evaluations: (x_j, (f_0(x_j), f_1(x_j), ..., f_{L-1}(x_j))).

4. The x-coordinate is stored in the `coord_x` column; the vector of y-values is stored as a hexadecimal string in the `coord_y_hex` column.

### 8.2 Field Specification

All polynomial arithmetic uses the binary extension field GF(2^8) with the irreducible polynomial:

```
m(x) = x^8 + x^4 + x^3 + x + 1
```

In hexadecimal, the full polynomial representation is 0x11b. The reduction polynomial for multiplication overflow is 0x1b (representing the lower 8 bits). Addition in GF(2^8) is bitwise XOR. Multiplication follows the standard shift-and-XOR algorithm with reduction when the degree of the intermediate result reaches 8.

### 8.3 Threshold Parameter

The threshold K for a session is specified in the `threshold_k` column of the `sessions` table at session creation time. The threshold is not automatically derived from the total slot count; it is set by the ceremony officer based on the protection level of the secret and the quorum policy in effect at the time.

The general guidance for threshold selection is:

- For sessions with N = 3 slots: K should be 2.
- For sessions with N = 4 or 5 slots: K should be 3.
- For sessions with N = 7 slots (recommended for PL3+): K should be 4.

These are recommendations; the actual K stored in the database is authoritative.

### 8.4 X-Coordinate Assignment

X-coordinates for slots are assigned sequentially starting at 1. Slot index 1 receives x-coordinate 1, slot index 2 receives x-coordinate 2, and so on. X-coordinates must be non-zero; the zero x-coordinate is reserved exclusively as the interpolation target for secret recovery (see Section 12.3).

This reservation of x=0 is a structural property of the scheme: the constant term of the polynomial — which is the secret byte — is the value at x=0. The shares at x=1, x=2, ..., x=n are evaluations of the polynomial at non-zero points. Recovery requires interpolating back to x=0.

### 8.5 Share Storage Security

Share y-coordinate vectors must be encrypted at rest on the hardware token using the token's built-in encryption engine. The cleartext y-value must never be written to any persistent storage other than the token itself. During a ceremony, the y-value is decrypted in-token and transmitted over a secure local channel to the ceremony management workstation for submission to the database. Once submitted, the raw y-values are retained only in the `share_submissions` table and are subject to the retention policy in Section 3.3.

---

## Chapter 9 — Recovery Ceremony Procedures

### 9.1 Pre-Ceremony Setup (Phase 0)

The Ceremony Officer performs the following setup tasks before the ceremony begins:

(a) Verify that the ceremony session record has been created in the operational database and that the `session_id`, `threshold_k`, and `total_slots` values are correct.

(b) Confirm that the slot registry contains exactly `total_slots` rows for the session, each with a valid `custodian_id` and `auth_tier`.

(c) Verify that no submissions exist for this session in the `share_submissions` table (a clean slate before the ceremony).

(d) Confirm that all required physical materials are present: hardware tokens, identity documentation, witness attestation forms.

(e) Brief all participants on the ceremony procedure and policy requirements.

### 9.2 Identity and Token Verification Phase (Phase 1)

For each participating custodian:

1. The Ceremony Officer verifies identity documentation against the enrollment record.
2. The custodian's hardware token is verified against the enrollment record using the challenge-response mechanism.
3. The Ceremony Officer records the outcome of identity and token verification in the ceremony log.
4. The custodian is assigned to their designated slot and the slot is marked as active.

Custodians who fail identity or token verification must not proceed to the submission phase. Their slot is recorded as unverified in the ceremony log. If the number of successfully verified custodians falls below the threshold, the ceremony must be suspended.

### 9.3 Share Submission Phase (Phase 2)

For each successfully verified custodian, in sequential order by slot index:

1. The custodian activates their hardware token using their personal authentication credential.
2. The token decrypts and presents the y-coordinate vector of the share.
3. The ceremony workstation reads the (x, y) share and submits it to the database:
   - A row is inserted into `share_submissions` with the appropriate `slot_id`, `coord_x`, `coord_y_hex`, and `submitted_at` values.
4. The submission is confirmed by reading it back from the database.
5. The custodian witnesses the confirmation and signs the submission attestation form.

Submissions must be made in slot order. If a submission fails (database error, token read error), the Ceremony Officer halts the ceremony, logs the failure, and consults the escalation procedures in Chapter 16.

### 9.4 Approval Phase (Phase 3)

After all available submissions are complete, the approval phase begins. During this phase, designated approvers review and endorse the submissions.

For each submitted slot:

1. A designated approver (who is NOT the custodian who submitted the share) reviews the submission record.
2. The approver verifies that the `coord_y_hex` in the database matches the value they received from the custodian through a separate secure channel (out-of-band confirmation).
3. If verified, the approver submits an approval record:
   - A row is inserted into `ceremony_approvals` with:
     - `approval_id`: A unique identifier for this approval act.
     - `session_id`: The identifier of the current session.
     - **`approved_slot`**: The `slot_id` of the slot being approved. This field establishes the linkage between the approval record and the specific slot.
     - `approved_by`: The identity string of the approver. This is the approver's identity, NOT the custodian's identity. The `approved_by` field must differ from the `custodian_id` of the slot being approved.
     - `approved_at`: The timestamp of the approval action.
4. The approver signs the approval attestation form.

### 9.5 Reconstruction and Verification Phase (Phase 4)

After sufficient approvals have been obtained, the reconstruction phase begins:

1. The audit tool (or ceremony workstation) loads the submission records and verifies that the count of submissions with linked approvals meets the threshold.

2. The Lagrange interpolation is performed at the zero coordinate of GF(2^8) to recover the secret. See Chapter 12 for the precise computation specification.

3. The fingerprint is computed from the recovered secret bytes (see Section 12.3) and compared against the pre-registered fingerprint on file.

4. If the fingerprints match, reconstruction is confirmed successful.

5. The recovered secret is handled according to the purpose of the ceremony:
   - For a key restore: the secret is imported into the target HSM.
   - For a verification ceremony: the secret is confirmed and immediately destroyed in memory.
   - For an audit ceremony: the audit tool records the fingerprint in the output report without retaining the full secret.

### 9.6 Post-Ceremony Procedures (Phase 5)

After reconstruction:

1. All hardware tokens are re-sealed and returned to their respective custodians.
2. The ceremony log is signed by all participants and the Ceremony Officer.
3. The audit report is generated by the automated audit tool and submitted to the ceremony record archive.
4. Any policy violations identified are reported to the Governance Board within 24 hours.

---

## Chapter 10 — Quorum Formation Rules and Validation

### 10.1 Basic Quorum Requirement

A valid quorum consists of at least K participating custodians, where K is the `threshold_k` value stored in the `sessions` table for the relevant session. The threshold is set at session creation time and is immutable for the life of the session. The threshold represents the minimum number of submitted and approved shares required for reconstruction.

For the purposes of the audit tool, the threshold check is performed as follows:

```
threshold_met = (count of submitted shares) >= threshold_k
```

A session that does not meet the threshold cannot be reconstructed and must be marked as `insufficient_shares` in the audit report.

### 10.2 Quorum Diversity Requirements

In addition to the numerical threshold, a valid quorum must satisfy the following diversity requirements:

(a) **No duplicate custodians**: A single custodian may not contribute more than one share to a quorum, even if they hold slots in multiple sessions.

(b) **Tier composition**: Depending on the protection level of the secret being recovered, specific minimum representation from certain tier categories may be required. Refer to the ceremony-level authorization letter for tier composition requirements specific to any individual ceremony.

(c) **Exclusion constraints**: The quorum must not include custodians from two or more tiers that are listed as mutually exclusive in the `tier_constraints` table. This check is the most mechanically complex of the quorum validation rules; it is specified in detail in Chapter 11.

### 10.3 Quorum Validation Process

The automated audit tool performs quorum validation as follows:

Step 1. Load the slot records for the session.
Step 2. Identify the slots for which submissions exist and for which linked approvals exist.
Step 3. Count the qualifying submissions and compare against the threshold.
Step 4. Extract the `auth_tier` values from all submitted slots.
Step 5. Evaluate each constraint in the `tier_constraints` table against the set of tiers present.
Step 6. If any constraint is violated, record the violation and mark `quorum_valid = false`.
Step 7. If no constraints are violated, mark `quorum_valid = true`.

### 10.4 Threshold and Quorum Relationship

The `threshold_met` and `quorum_valid` fields in the audit report are independent. A session can have `threshold_met = true` and `quorum_valid = false` (sufficient shares were submitted but they violated a policy constraint). A session can also have `threshold_met = false` and `quorum_valid = true` (the submitted shares meet all policy constraints, but there are not enough of them for reconstruction).

---

## Chapter 11 — Policy Enforcement Rules

### 11.1 Overview

Policy enforcement is the process by which the automated audit tool determines whether a ceremony session meets all applicable policy requirements. This chapter specifies the complete set of policy rules that the tool must evaluate.

### 11.2 Constraint Categories

Policy constraints fall into two broad categories:

**Exclusion Constraints** (`rule_kind = 'cannot_coexist'`): These constraints specify pairs of authorization tiers that must not both be present in a ceremony quorum. The check is bilateral: if tiers A and B are listed as a cannot_coexist pair, then a quorum containing at least one custodian with tier A AND at least one custodian with tier B is invalid.

The critical aspect of the `cannot_coexist` rule is the AND condition. A quorum is invalid under this rule only when BOTH tiers of the specified pair are simultaneously represented. If only one of the two tiers is present, the quorum is not in violation of this constraint, regardless of which tier it is.

To state this precisely:

- Quorum contains tier A, does not contain tier B → NO VIOLATION of the A-B cannot_coexist constraint.
- Quorum contains tier B, does not contain tier A → NO VIOLATION of the A-B cannot_coexist constraint.
- Quorum contains neither tier A nor tier B → NO VIOLATION.
- Quorum contains BOTH tier A AND tier B → VIOLATION. The ceremony is invalid.

**Concentration Constraints** (`rule_kind = 'concentration_limit'`): These constraints limit the fraction of quorum slots that may be held by custodians from a single tier. They are not currently used in this deployment but are reserved for future policy expansion. Audit tools must skip constraint rows with `rule_kind = 'concentration_limit'` without generating violations.

### 11.3 Evaluation of Cannot-Coexist Constraints

For each row in the `tier_constraints` table where `rule_kind = 'cannot_coexist'`:

1. Let tier_A = the `tier_alpha` value from that row.
2. Let tier_B = the `tier_beta` value from that row.
3. Let set_A = true if any slot in the quorum has `auth_tier = tier_A`, false otherwise.
4. Let set_B = true if any slot in the quorum has `auth_tier = tier_B`, false otherwise.
5. **The constraint is violated if and only if (set_A AND set_B) is true.**

If the constraint is violated, a violation record is appended to the `policy_violations` list in the form: `cannot_coexist:<tier_A>+<tier_B>`.

If set_A is true but set_B is false, or set_B is true but set_A is false, the constraint is NOT violated and no violation record is generated.

### 11.4 Worked Example: Cannot-Coexist Evaluation

Suppose the `tier_constraints` table contains the single row:

```
constraint_id = 'tc-001', tier_alpha = 'executive', tier_beta = 'auditor', rule_kind = 'cannot_coexist'
```

**Case 1**: Quorum tiers = {primary, primary, secondary}
- set_A (executive): false
- set_B (auditor): false
- set_A AND set_B: false → NO VIOLATION, quorum_valid = true

**Case 2**: Quorum tiers = {executive, primary, secondary}
- set_A (executive): true
- set_B (auditor): false
- set_A AND set_B: false → NO VIOLATION, quorum_valid = true

**Case 3**: Quorum tiers = {auditor, primary, secondary}
- set_A (executive): false
- set_B (auditor): true
- set_A AND set_B: false → NO VIOLATION, quorum_valid = true

**Case 4**: Quorum tiers = {executive, auditor, backup}
- set_A (executive): true
- set_B (auditor): true
- set_A AND set_B: true → VIOLATION. quorum_valid = false.
  violation record: "cannot_coexist:executive+auditor"

This example illustrates that only Case 4 triggers the constraint. Cases 2 and 3 must NOT generate violations; they are valid ceremony configurations. Any enforcement implementation that flags Cases 2 or 3 as violations is defective.

### 11.5 Role Separation Check

The audit tool must also verify that the approval records exhibit role separation: for each linked approval, the `approved_by` identity must differ from the `custodian_id` of the slot referenced by `approved_slot`. When role separation is violated, the tool records a violation of type `role_separation:<slot_id>`.

Role separation is a separate check from the quorum constraint evaluation and uses different data relationships. The quorum check uses tier information from `slot_registry`. The role separation check uses the `custodian_id` from `slot_registry` cross-referenced with `approved_by` and `approved_slot` from `ceremony_approvals`.

### 11.6 Verification Status Derivation

After completing all checks, the tool derives `verification_status` as follows:

- If `reconstruction_status` is not `success`: set `verification_status = 'failed'`.
- Else if `quorum_valid = false` OR `policy_violations` is non-empty: set `verification_status = 'policy_violation'`.
- Else: set `verification_status = 'verified'`.

---

## Chapter 12 — Cryptographic Verification Requirements

### 12.1 Purpose of Cryptographic Verification

Cryptographic verification serves to confirm that the output of the reconstruction process is the correct secret without requiring full secret disclosure to audit personnel. The verification mechanism uses a fingerprint — a short, collision-resistant summary — that can be compared against a pre-registered expected fingerprint to confirm correctness.

### 12.2 Field Arithmetic Review

Before specifying the reconstruction algorithm, this section reviews the field arithmetic used.

The field GF(2^8) is constructed as the quotient ring GF(2)[x] / m(x) where m(x) = x^8 + x^4 + x^3 + x + 1. Elements of this field are 8-bit values (0x00 through 0xff). The field has 256 elements.

**Addition**: a ⊕ b (bitwise XOR). Subtraction is identical to addition in characteristic-2 fields.

**Multiplication**: The product a * b is computed by the standard shift-and-XOR algorithm: multiply bit by bit, shifting and reducing modulo m(x) whenever the degree reaches 8. The reduction step XORs with 0x1b (the low 8 bits of m(x)) when a carry occurs. The zero element (0x00) is the additive identity. The unit element (0x01) is the multiplicative identity.

**Multiplicative Inverse**: The inverse of a non-zero element a can be computed using Fermat's little theorem: a^(-1) = a^(254) in GF(2^8), since the multiplicative group has order 255 and 2^8 - 2 = 254.

### 12.3 Secret Reconstruction Algorithm

The secret is reconstructed from k submitted shares using Lagrange interpolation over GF(2^8). The procedure is as follows:

**Input**: A set of k share points {(x_1, Y_1), (x_2, Y_2), ..., (x_k, Y_k)} where each x_i is a non-zero byte (the `coord_x` value) and each Y_i is an L-byte vector (decoded from the `coord_y_hex` column).

**Interpolation target**: The zero element of GF(2^8), i.e., x = 0x00.

The choice of interpolation target is a fundamental property of the scheme: the secret S is defined as the constant term of the polynomial f, which means S = f(0). Interpolating at x = 0x00 recovers S. Interpolating at any other coordinate would recover f(target), which is a share point of the polynomial, not the secret.

AUDIT_PARAM: INTERPOLATION_TARGET = 0

**Procedure** (repeated independently for each byte position j from 0 to L-1):

```
secret[j] = XOR over i from 1 to k of ( Y_i[j] * L_i(0x00) )
```

where the Lagrange basis coefficient L_i(0x00) is:

```
L_i(0x00) = product over all m ≠ i of ( (0x00 ⊕ x_m) / (x_i ⊕ x_m) )
           = product over all m ≠ i of ( x_m * gfInv(x_i ⊕ x_m) )
```

Here ⊕ denotes bitwise XOR (GF addition), and all multiplication and inversion are in GF(2^8).

**Note on the evaluation point**: The expression `0x00 ⊕ x_m` simplifies to `x_m` because XOR with zero is the identity. The evaluation target 0x00 is therefore not explicitly present in the arithmetic formula; it manifests as the simplification that the numerator product is just the product of all x_m for m ≠ i.

### 12.4 Fingerprint Computation

The cryptographic fingerprint of the recovered secret is computed as follows:

1. Let raw_secret be the byte slice resulting from successful reconstruction (one byte per secret byte position).

2. Compute the SHA-256 digest of raw_secret:
   ```
   digest = SHA-256(raw_secret)
   ```

3. Encode the full 32-byte digest as a lowercase hexadecimal string (64 characters).

4. Take the first 16 characters of the hexadecimal string as the fingerprint:
   ```
   fingerprint = hex_encode(digest)[0:16]
   ```

AUDIT_PARAM: FINGERPRINT_LENGTH = 16

The fingerprint is therefore exactly 16 lowercase hexadecimal characters.

### 12.5 Fingerprint Verification

To verify a reconstructed secret against a pre-registered fingerprint:

1. Compute the fingerprint from the reconstructed secret bytes as specified in Section 12.4.
2. Compare the computed fingerprint against the expected fingerprint using a constant-time comparison function.
3. If the fingerprints match, the verification passes.
4. If they do not match, the verification fails and the discrepancy must be logged as a critical event.

### 12.6 Entropy and Collision Resistance

The 16-character (8-byte effective) fingerprint provides 64 bits of output from a 256-bit hash function. This is sufficient for verification purposes where the comparison is between a computed value and a small number of pre-registered expected values. It is not intended for use as a general-purpose collision-resistant identifier. Applications that require stronger collision resistance should use the full 64-character hex digest.

---

## Chapter 13 — Database Schema and Approval Linkage Model

### 13.1 Schema Overview

The operational database stores all records required for ceremony audit. The five tables and their relationships are described in this chapter. The schema is designed so that each entity type is clearly separated and relationships between entities are expressed through stable identifier references.

### 13.2 Sessions Table

```sql
CREATE TABLE sessions (
    session_id   TEXT PRIMARY KEY,
    initiated_at INTEGER NOT NULL,
    threshold_k  INTEGER NOT NULL,
    total_slots  INTEGER NOT NULL
);
```

The `session_id` is the primary business identifier for a ceremony event. It is referenced by all other tables. `threshold_k` is the minimum number of shares required for reconstruction. `total_slots` is the number of custodian positions registered for the session.

### 13.3 Slot Registry Table

```sql
CREATE TABLE slot_registry (
    slot_id      TEXT PRIMARY KEY,
    session_id   TEXT NOT NULL REFERENCES sessions(session_id),
    slot_index   INTEGER NOT NULL,
    custodian_id TEXT NOT NULL,
    auth_tier    TEXT NOT NULL
);
```

Each row represents one custodian position in a session. `slot_id` is the stable identifier for this position; it does not change if a custodian is replaced. `custodian_id` is the identity of the individual occupying the slot. `auth_tier` is the authorization tier as described in Chapter 5.

### 13.4 Approval Linkage Specification

The linkage between approval records and slot records is one of the most critical relationships in the schema. It is also the most frequently misimplemented in automated tools.

**Canonical Linkage Definition**: An approval record in the `ceremony_approvals` table is linked to a slot in the `slot_registry` table when and only when:

```
ceremony_approvals.approved_slot = slot_registry.slot_id
```

This is the authoritative linkage condition. It links the approval to the specific custodian slot that was approved, not to the identity of the custodian who holds that slot.

### 13.5 Share Submissions Table

```sql
CREATE TABLE share_submissions (
    submission_id TEXT PRIMARY KEY,
    slot_id       TEXT NOT NULL REFERENCES slot_registry(slot_id),
    coord_x       INTEGER NOT NULL,
    coord_y_hex   TEXT NOT NULL,
    submitted_at  INTEGER NOT NULL
);
```

The `coord_x` value is the x-coordinate of the share point in GF(2^8), stored as an integer. `coord_y_hex` is the y-coordinate vector encoded as a lowercase hexadecimal string with length equal to twice the byte length of the secret.

### 13.6 Ceremony Approvals Table

```sql
CREATE TABLE ceremony_approvals (
    approval_id   TEXT PRIMARY KEY,
    session_id    TEXT NOT NULL,
    approved_slot TEXT NOT NULL REFERENCES slot_registry(slot_id),
    approved_by   TEXT NOT NULL,
    approved_at   INTEGER NOT NULL
);
```

The distinction between `approved_slot` and `approved_by` is critical and is documented again here for clarity:

- `approved_slot`: The `slot_id` of the slot being approved. This is a foreign key to `slot_registry.slot_id`. This field establishes the linkage between the approval and the slot.
- `approved_by`: The identity string of the approver. This is NOT a foreign key; approver identities are stored as plain strings. Approver identities must differ from the `custodian_id` of the slot referenced by `approved_slot`.

**Note**: The `approved_slot` and `approved_by` fields serve different purposes in this table. `approved_slot` is a foreign key to `slot_registry.slot_id` and establishes which slot was approved. `approved_by` is a plain string holding the approver's identity; it is not a foreign key to any other table.

### 13.7 Tier Constraints Table

```sql
CREATE TABLE tier_constraints (
    constraint_id TEXT PRIMARY KEY,
    tier_alpha    TEXT NOT NULL,
    tier_beta     TEXT NOT NULL,
    rule_kind     TEXT NOT NULL
);
```

Each row defines a policy constraint between two authorization tiers. The `rule_kind` determines how the constraint is evaluated (see Chapter 11). The `tier_alpha` and `tier_beta` values are the authorization tier strings that the constraint governs.

---

## Chapter 14 — Exception Handling and Edge Cases

### 14.1 Insufficient Shares

When the number of submitted shares for a session is less than the session threshold, reconstruction cannot proceed. The tool must:

1. Set `reconstruction_status = 'insufficient_shares'`.
2. Set `threshold_met = false`.
3. Set `secret_fingerprint = null`.
4. Proceed with quorum validation using only the available slots.
5. Set `verification_status = 'failed'`.

The tool must not attempt reconstruction when shares are insufficient. Attempting to apply Lagrange interpolation with fewer points than the polynomial degree plus one will produce an incorrect result without signaling an error, which would be worse than reporting the true failure mode.

### 14.2 Decoding Errors

If the `coord_y_hex` value for any submission cannot be decoded as a valid hexadecimal string, the tool must:

1. Set `reconstruction_status = 'decode_error:<slot_id>'`.
2. Treat the affected submission as missing for the purposes of the threshold check.
3. Log the error with the specific slot identifier.

### 14.3 Zero Coordinate Error

If any submission has `coord_x = 0`, this is a fatal error: the x-coordinate zero is reserved for the interpolation target and must never appear in the shares. The tool must:

1. Reject the submission.
2. Set `reconstruction_status = 'invalid_coordinate'`.
3. Log a critical error.

This restriction flows from the fundamental property that x=0 is the secret recovery point. If a share existed at x=0, its y-value would equal the secret, completely defeating the purpose of the sharing scheme.

### 14.4 Duplicate X-Coordinates

If two submissions for the same session have the same `coord_x` value, the Lagrange interpolation formula becomes undefined (division by zero in the denominator). The tool must detect this condition and:

1. Reject the duplicate.
2. Use only the first submission with each unique x-coordinate.
3. Log a warning.

### 14.5 Missing Session Records

If a session referenced by a slot or submission does not exist in the `sessions` table, the tool must log an orphan record warning and skip the orphaned records.

### 14.6 Empty Sessions

A session with zero slots loaded is marked as `no_shares` with all boolean fields set to `false`.

---

## Chapter 15 — Audit, Logging, and Compliance

### 15.1 Audit Trail Integrity

The audit trail produced by the automated tool must be signed using the tool's deployment key. The signature covers the entire JSON output file. Consumers of the audit report must verify this signature before relying on the report's contents.

For environments where deployment key signing is not yet implemented, the tool must at minimum log the SHA-256 hash of the output file to the system audit log, providing a tamper-evidence baseline.

### 15.2 Logging Requirements

The tool must emit structured log entries to standard output for the following events:

- Session loading: one entry per session loaded.
- Approval count: one entry per session, logging the `approvals_linked` value.
- Reconstruction attempt: one entry per session, logging the status.
- Policy evaluation: one entry per constraint evaluated, logging the tier values and outcome.
- Report write: one entry confirming the output path and session count.

### 15.3 Compliance Reporting

Quarterly compliance reports must be produced by aggregating the ceremony audit records for the preceding 90 days. The compliance report must include:

- Total ceremonies conducted.
- Total ceremonies with policy violations.
- Total ceremonies with reconstruction failures.
- Distribution of participating tiers across all ceremonies.
- Any patterns indicating unusual ceremony behavior.

---

## Chapter 16 — Incident Response and Escalation

### 16.1 Ceremony Failure Escalation

If a ceremony fails due to insufficient shares, the Ceremony Officer must:

1. Suspend the ceremony immediately.
2. Notify the Governance Board within one hour.
3. Document the number of available shares versus the threshold.
4. Initiate the emergency mobilization process to locate additional custodians if needed.

### 16.2 Policy Violation Escalation

If the automated audit tool reports a policy violation for a ceremony:

1. The recovery action that depends on the ceremony must be suspended pending review.
2. The Governance Board must convene a review within 48 hours.
3. If the violation was genuine (e.g., conflicting tiers participated), the ceremony is void and must be repeated with a compliant quorum.
4. If the violation was due to a tool error (e.g., the audit tool has a bug in its policy evaluation logic), the tool must be corrected, the output regenerated, and the remediation documented.

### 16.3 Suspected Compromise

If any custodian suspects that their share has been compromised:

1. They must notify the Governance Board immediately.
2. All ceremonies pending that custodian's slot must be suspended.
3. A share regeneration ceremony must be initiated within 24 hours.

---

## Appendix A — Authorization Tier Definitions

### A.1 Tier Catalog

The following authorization tiers are defined for use in the `auth_tier` field of the `slot_registry` table:

| Tier Name   | Description                                                              | Required Background Check | Re-cert Cycle |
|-------------|--------------------------------------------------------------------------|---------------------------|---------------|
| `primary`   | Senior technical staff, permanent custodian roster                       | Enhanced, 5-year refresh  | Annual        |
| `secondary` | Alternate technical staff, activated as needed                           | Standard, 3-year refresh  | Annual        |
| `backup`    | Escrow-only custodians for disaster recovery scenarios                   | Enhanced, 5-year refresh  | Biennial      |
| `executive` | Senior organizational leadership for governance control                  | Executive, 2-year refresh | Annual        |
| `auditor`   | Independent oversight personnel for neutral witness function             | Enhanced, 3-year refresh  | Annual        |

### A.2 Tier Hierarchy

The tiers above do not form a strict hierarchy in which higher tiers include all permissions of lower tiers. Each tier is orthogonal in terms of operational role. For the purposes of threshold counting and quorum validity, all tiers are equal: one slot of any tier contributes one share.

### A.3 Mixed-Tier Quorums

Mixed-tier quorums are permitted and are the default for most ceremonies. The policy imposes no minimum or maximum representation from any tier (other than zero minimum), except through exclusion constraints. A quorum consisting entirely of primary tier custodians is valid. A quorum mixing primary, secondary, and backup is valid. A quorum mixing executive and auditor is invalid under the exclusion constraint defined in Appendix B.

---

## Appendix B — Tier Exclusion Matrix

### B.1 Purpose

This appendix defines all exclusion constraints that must be enforced during quorum validation. Each entry specifies a pair of tiers that may not coexist in the same ceremony quorum. The enforcement rule is the bilateral AND condition described in Section 11.2: both tiers must be present for a violation to occur.

### B.2 Active Exclusion Constraints

| Constraint ID | Tier Alpha  | Tier Beta | Rule Kind       | Rationale                                                   |
|---------------|-------------|-----------|-----------------|-------------------------------------------------------------|
| `tc-001`      | `executive` | `auditor` | `cannot_coexist`| Separation of governance and independent oversight functions |

### B.3 Interpretation Notes

The single active constraint in this deployment (`tc-001`) prevents executive and auditor tiers from coexisting in the same quorum. The practical effect is:

- A ceremony with only executive tier participants (and other non-auditor tiers) is valid.
- A ceremony with only auditor tier participants (and other non-executive tiers) is valid.
- A ceremony with BOTH executive and auditor participants is invalid.

Future policy revisions may add additional constraints to this matrix. Automated tools must read the `tier_constraints` table at runtime rather than hardcoding the constraints.

---

## Appendix C — Sample Ceremony Records and Worked Examples

### C.1 Example: Standard Recovery, Valid Quorum (sess-alpha Equivalent)

This example illustrates a ceremony session with five registered slots, a threshold of three, three submitted shares, three linked approvals, and a valid quorum composition.

**Session Record**:
- `session_id`: "sess-alpha-example"
- `initiated_at`: 1700000000
- `threshold_k`: 3
- `total_slots`: 5

**Slot Registry** (5 rows):
- Slot 1: primary tier, custodian cust-01
- Slot 2: primary tier, custodian cust-02
- Slot 3: secondary tier, custodian cust-03
- Slot 4: secondary tier, custodian cust-04
- Slot 5: backup tier, custodian cust-05

**Submitted Shares** (3 rows):
- Slot 1 submitted: coord_x=1, coord_y_hex=(8-byte hex value)
- Slot 2 submitted: coord_x=2, coord_y_hex=(8-byte hex value)
- Slot 3 submitted: coord_x=3, coord_y_hex=(8-byte hex value)

**Approval Records** (3 rows):
- approved_slot="slt-1", approved_by="apvr-01" (distinct from cust-01)
- approved_slot="slt-2", approved_by="apvr-02" (distinct from cust-02)
- approved_slot="slt-3", approved_by="apvr-03" (distinct from cust-03)

Note that the approvals reference the `slot_id` values ("slt-1", "slt-2", "slt-3"), not the custodian identity strings. The `approved_by` values are approver identities that differ from the custodian identities.

**Expected Audit Output**:
```json
{
  "session_id": "sess-alpha-example",
  "slots_loaded": 5,
  "approvals_linked": 3,
  "reconstruction_status": "success",
  "secret_fingerprint": "<16-char hex>",
  "threshold_met": true,
  "quorum_valid": true,
  "policy_violations": [],
  "verification_status": "verified"
}
```

### C.2 Example: Insufficient Shares (sess-beta Equivalent)

A session with threshold=3 where only 2 shares were submitted.

**Expected Audit Output**:
```json
{
  "session_id": "sess-beta-example",
  "slots_loaded": 4,
  "approvals_linked": 2,
  "reconstruction_status": "insufficient_shares",
  "secret_fingerprint": null,
  "threshold_met": false,
  "quorum_valid": true,
  "policy_violations": [],
  "verification_status": "failed"
}
```

Note: `quorum_valid` may still be `true` even when `threshold_met` is `false`, because the quorum check evaluates the composition of the participating slots, not whether they are sufficient in number.

### C.3 Example: Policy Violation — Conflicting Tiers (sess-gamma Equivalent)

A session where both executive and auditor tier custodians participated.

**Slot Composition**: executive, auditor, backup, primary, secondary

**Tier Check for tc-001 (executive / auditor, cannot_coexist)**:
- set_A (executive): true (slot 1 is executive)
- set_B (auditor): true (slot 2 is auditor)
- Condition: set_A AND set_B = true → VIOLATION

**Expected Audit Output**:
```json
{
  "session_id": "sess-gamma-example",
  "slots_loaded": 5,
  "approvals_linked": 3,
  "reconstruction_status": "success",
  "secret_fingerprint": "<16-char hex>",
  "threshold_met": true,
  "quorum_valid": false,
  "policy_violations": ["cannot_coexist:executive+auditor"],
  "verification_status": "policy_violation"
}
```

Note that reconstruction succeeds (the shares are valid) but the ceremony is flagged due to the tier conflict.

### C.4 Example: Valid Executive-Only Participation (sess-delta Equivalent)

A session where executive tier is present but auditor tier is absent.

**Slot Composition**: executive, primary, secondary

**Tier Check for tc-001 (executive / auditor, cannot_coexist)**:
- set_A (executive): true
- set_B (auditor): false
- Condition: set_A AND set_B = false → NO VIOLATION

**Expected Audit Output**:
```json
{
  "session_id": "sess-delta-example",
  "slots_loaded": 3,
  "approvals_linked": 2,
  "reconstruction_status": "success",
  "secret_fingerprint": "<16-char hex>",
  "threshold_met": true,
  "quorum_valid": true,
  "policy_violations": [],
  "verification_status": "verified"
}
```

This example is particularly important for verifying that the enforcement implementation does not generate false positives for sessions where only one tier of an exclusion pair is present.

---

## Appendix D — Regulatory References and Cross-Mapping

### D.1 Cross-Mapping to Standards

The following table maps the key policy requirements in this document to their normative counterparts in applicable standards:

| Policy Section | Requirement Description                        | NIST SP 800-57 | ISO/IEC 27001    | FIPS 140-3 |
|----------------|------------------------------------------------|----------------|------------------|------------|
| Section 8.1    | Threshold secret sharing scheme                | Section 5.3    | A.8.24           | —          |
| Section 12.3   | Lagrange interpolation at zero coordinate      | —              | —                | Section 5  |
| Section 11.2   | Cannot-coexist enforcement (AND condition)     | —              | A.5.3 (SoD)      | —          |
| Section 13.4   | Approval linkage by slot_id                    | —              | A.8.22           | —          |
| Section 12.4   | SHA-256 fingerprint (16 hex chars)             | Section 5.1    | A.8.24           | —          |

### D.2 Deviations from Standard Recommendations

This policy intentionally deviates from certain standard recommendations as follows:

**Deviation 1**: NIST SP 800-57 recommends that threshold values be determined by a formal risk analysis for each key type. This policy provides general guidance (Section 8.3) but allows ceremony officers to set thresholds based on operational context. This deviation is accepted because the operational database stores the authoritative threshold value and tools must use that value.

**Deviation 2**: Some standards recommend using a prime-field implementation of Shamir Secret Sharing (over a large prime such as 2^127-1). This policy mandates GF(2^8) for implementation simplicity and consistency with widely deployed HSM firmware. The security level is equivalent for the share sizes used in this deployment.

---

## Appendix E — Revision History

| Version | Date       | Author             | Summary of Changes                                            |
|---------|------------|--------------------|---------------------------------------------------------------|
| 1.0     | 2020-03-01 | Governance Board   | Initial release                                               |
| 1.1     | 2020-09-15 | Ops Security       | Clarified phase 2 submission procedure                        |
| 1.2     | 2021-02-28 | Governance Board   | Added concentration constraint category (not yet active)     |
| 2.0     | 2022-06-01 | Governance Board   | Major revision: added automated audit tool specification      |
| 2.1     | 2022-10-15 | Ops Security       | Clarified fingerprint computation (SHA-256 requirement)       |
| 2.2     | 2023-01-20 | Governance Board   | Added executive and auditor tier definitions                  |
| 2.3     | 2023-05-10 | Ops Security       | Added Appendix C worked examples                              |
| 2.4     | 2023-09-30 | Governance Board   | Strengthened role separation requirements                     |
| 3.0     | 2024-01-15 | Governance Board   | Version 3.0: complete rewrite for clarity and automation      |
| 3.1     | 2024-04-01 | Ops Security       | Added AUDIT_PARAM machine-readable markers                   |
| 3.2     | 2024-07-15 | Governance Board   | Clarified AND condition for cannot_coexist in Section 11.3   |
| 3.2.1   | 2024-10-01 | Ops Security       | Fixed typographical errors in SQL examples in Chapter 13     |

---

*End of Document — DCRC-POL-v3 Revision 3.2.1*

*This document contains confidential operational procedures. Distribution is restricted to authorized ceremony personnel and Governance Board members. Do not copy, transmit, or store outside of approved secure repositories.*
