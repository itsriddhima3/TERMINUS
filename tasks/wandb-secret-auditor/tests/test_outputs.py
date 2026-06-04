"""Verifier for wandb-secret-auditor outputs."""

import hashlib
import json
import pathlib
import re
import subprocess
import tempfile

import pytest

RUNS_DIR = pathlib.Path("/app/fixtures")
TRANSCRIPT_DIR = pathlib.Path("/app/docs/review")
OUT = pathlib.Path("/app/output/report.json")


def _sha256_file(p: pathlib.Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _sha256_concat_sorted_txt(dir_path: pathlib.Path) -> str:
    h = hashlib.sha256()
    parts = sorted([p for p in dir_path.iterdir() if p.is_file() and p.name.endswith(".txt")])
    for i, p in enumerate(parts):
        if i:
            h.update(b"\n")
        h.update(p.read_bytes())
    return h.hexdigest()


def _run() -> subprocess.CompletedProcess:
    return subprocess.run(
        ["/app/bin/wbaudit", str(RUNS_DIR), str(TRANSCRIPT_DIR), str(OUT)],
        capture_output=True,
        timeout=60,
    )


def _run_custom(runs_dir: pathlib.Path, transcript_dir: pathlib.Path, out: pathlib.Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["/app/bin/wbaudit", str(runs_dir), str(transcript_dir), str(out)],
        capture_output=True,
        timeout=60,
    )


def _load() -> dict:
    assert OUT.exists(), f"missing {OUT}"
    raw = OUT.read_text(encoding="utf-8")
    assert raw.endswith("\n")
    return json.loads(raw)


def _transcript_text(dir_path: pathlib.Path) -> str:
    parts = sorted([p for p in dir_path.iterdir() if p.is_file() and p.name.endswith(".txt")])
    return "\n".join(p.read_text(encoding="utf-8") for p in parts)


def _extract_active_policy(text: str) -> tuple[str | None, list[str], list[str]]:
    current_tag: str | None = None
    active_tag: str | None = None
    blocks: dict[str, list[str]] = {}

    for line in text.splitlines():
        m_tag = re.search(r"POLICY_TAG\s*:\s*([A-Z]{2}-\d{4}-\d{2})", line)
        if m_tag:
            current_tag = m_tag.group(1)
            blocks.setdefault(current_tag, [])
            continue

        if current_tag is not None:
            blocks[current_tag].append(line)

        if re.search(r"\bSTATUS\s*:\s*ACTIVE\b", line) and current_tag:
            active_tag = current_tag

    chosen = active_tag or (list(blocks.keys())[-1] if blocks else None)
    chosen_lines = blocks.get(chosen or "", [])

    allow_prefixes: list[str] = []
    redact_rules: list[str] = []
    for line in chosen_lines:
        m_allow = re.search(r"ALLOW_REF_PREFIX\s*:\s*(.+)\s*$", line)
        if m_allow:
            allow_prefixes.append(m_allow.group(1).strip())
        m_redact = re.search(r"REDACT\s*:\s*(.+)\s*$", line)
        if m_redact:
            redact_rules.append(m_redact.group(1).strip())

    return (chosen, allow_prefixes, redact_rules)


def _fixture_exposure_substrings() -> list[str]:
    """Collect literal secret-like substrings present in fixture logs for leak checks."""
    found: list[str] = []
    for p in RUNS_DIR.rglob("*"):
        if not p.is_file():
            continue
        txt = p.read_text(encoding="utf-8")
        for m in re.finditer(r"api_key=([A-Z0-9\-]{8,64})", txt):
            found.append(m.group(0).split("=", 1)[1])
        for m in re.finditer(r"token:\s*([a-zA-Z0-9_]{8,64})", txt):
            found.append(m.group(1))
    return sorted(set(found))


def _snapshot_tree(root: pathlib.Path) -> dict[str, tuple[int, str, int]]:
    snap: dict[str, tuple[int, str, int]] = {}
    for p in sorted([x for x in root.rglob("*") if x.is_file()]):
        rel = str(p.relative_to(root))
        st = p.stat()
        snap[rel] = (st.st_size, _sha256_file(p), st.st_mtime_ns)
    return snap


@pytest.fixture(scope="session", autouse=True)
def _build_cli():
    subprocess.run(["bash", "/app/scripts/build-cli.sh"], check=True, timeout=120)


def test_alpha_schema_types_and_ordering():
    """Report exists, schema matches instruction, and run order is stable."""
    if OUT.exists():
        OUT.unlink()
    proc = _run()
    assert proc.returncode == 0, proc.stderr.decode()
    data = _load()
    assert set(data.keys()) == {"policy_ref", "transcript_hash", "runs", "totals"}
    assert isinstance(data["policy_ref"], str)
    assert isinstance(data["transcript_hash"], str)
    assert isinstance(data["runs"], list)
    assert isinstance(data["totals"], dict)
    assert set(data["totals"].keys()) == {"run_count", "alert_count", "invalid_approval_count"}
    assert all(isinstance(data["totals"][k], int) for k in data["totals"].keys())

    runs = data["runs"]
    run_ids = [r["id"] for r in runs]
    assert run_ids == sorted(run_ids)
    for r in runs:
        assert set(r.keys()) == {"id", "alerts", "approvals", "artifacts", "links"}
        assert isinstance(r["alerts"], list)
        assert isinstance(r["approvals"], list)
        assert isinstance(r["artifacts"], list)
        assert isinstance(r["links"], list)


def test_alpha_nested_lists_are_sorted_and_stable():
    """Nested lists are sorted so output is deterministic and comparable."""
    _run()
    data = _load()
    for r in data["runs"]:
        assert [a["name"] for a in r["artifacts"]] == sorted(a["name"] for a in r["artifacts"])
        assert [link["ref"] for link in r["links"]] == sorted(link["ref"] for link in r["links"])
        assert [a["id"] for a in r["approvals"]] == sorted(a["id"] for a in r["approvals"])
        # alerts should be stable in file order + path order
        assert [a["path"] for a in r["alerts"]] == sorted(a["path"] for a in r["alerts"])


def test_beta_transcript_hash_covers_all_meetings():
    """Transcript hash is bound to all meeting files."""
    _run()
    data = _load()
    got = data["transcript_hash"]
    assert re.fullmatch(r"[0-9a-f]{64}", got)
    exp = _sha256_concat_sorted_txt(TRANSCRIPT_DIR)
    assert got == exp


def test_gamma_idempotent_bytes():
    """Byte-for-byte determinism across repeated runs."""
    if OUT.exists():
        OUT.unlink()
    assert _run().returncode == 0
    a = OUT.read_bytes()
    assert _run().returncode == 0
    b = OUT.read_bytes()
    assert a == b


def test_delta_runs_and_totals_are_consistent():
    """Totals must match the per-run aggregates."""
    _run()
    data = _load()
    runs = data["runs"]
    assert data["totals"]["run_count"] == len(runs)
    alert_count = sum(len(r["alerts"]) for r in runs)
    invalid_approvals = sum(1 for r in runs for ap in r["approvals"] if ap["ok"] is False)
    assert data["totals"]["alert_count"] == alert_count
    assert data["totals"]["invalid_approval_count"] == invalid_approvals


def test_epsilon_artifact_hashes_match_bytes():
    """Artifact hashes must match the raw bytes on disk."""
    _run()
    data = _load()
    by_run = {r["id"]: r for r in data["runs"]}
    for run_id, run in by_run.items():
        art_dir = RUNS_DIR / f"run_{run_id}" / "artifacts"
        if not art_dir.exists():
            continue
        expected = {p.name: (_sha256_file(p), p.stat().st_size) for p in art_dir.iterdir() if p.is_file()}
        got = {a["name"]: (a["hash_hex"], a["bytes"]) for a in run["artifacts"]}
        assert got == expected


def test_foxtrot_no_raw_secret_substrings_leak():
    """Redaction must prevent known raw secrets from appearing in output."""
    _run()
    raw = OUT.read_text(encoding="utf-8")
    for secret in _fixture_exposure_substrings():
        assert secret not in raw

    data = json.loads(raw)
    for run in data["runs"]:
        for a in run["alerts"]:
            assert a["code"] == "EXPOSED"
            snip = a["snippet"]
            assert isinstance(snip, str)
            # snippets should keep context, not collapse to a fixed token
            assert "api_key=" in snip or "token:" in snip
            assert "<redacted>" in snip


def test_golf_link_validation_matrix():
    """Link validation must reject traversal/absolute refs and respect allowed prefixes."""
    _run()
    data = _load()
    by_run = {r["id"]: r for r in data["runs"]}
    alpha = {x["ref"]: x["ok"] for x in by_run["alpha"]["links"]}
    assert alpha["artifact://public/model-A@v1"] is True
    assert alpha["file:./artifacts/model.bin"] is True
    assert alpha["file:../../etc/passwd"] is False

    bravo = {x["ref"]: x["ok"] for x in by_run["bravo"]["links"]}
    assert bravo["artifact://public/model-B@v1"] is True
    assert bravo["artifact://private/model-B@v1"] is False
    assert bravo["file:./artifacts/data.txt"] is True

    charlie = {x["ref"]: x["ok"] for x in by_run["charlie"]["links"]}
    assert charlie["artifact://public/model-C@v2"] is True
    assert charlie["file:/absolute/outside"] is False


def test_hotel_approval_validation_is_policy_bound():
    """Approval validation must accept and reject the fixture matrix."""
    _run()
    data = _load()
    by_run = {r["id"]: r for r in data["runs"]}

    alpha = {x["id"]: (x["ok"], x["reason"]) for x in by_run["alpha"]["approvals"]}
    assert alpha["ap-alpha-1"][0] is True
    assert alpha["ap-alpha-2"][0] is False
    assert alpha["ap-alpha-2"][1] == "invalid-proof"

    bravo = {x["id"]: (x["ok"], x["reason"]) for x in by_run["bravo"]["approvals"]}
    assert bravo["ap-bravo-1"][0] is True

    charlie = {x["id"]: (x["ok"], x["reason"]) for x in by_run["charlie"]["approvals"]}
    assert charlie["ap-charlie-1"][0] is True
    assert charlie["ap-charlie-2"][0] is False

    delta = {x["id"]: (x["ok"], x["reason"]) for x in by_run["delta"]["approvals"]}
    assert delta["ap-delta-3"][0] is False
    assert delta["ap-delta-3"][1] == "invalid-proof"


def test_india_policy_ref_is_one_of_transcript_tags():
    """Policy ref should be derived from transcript tags."""
    _run()
    data = _load()
    tags = set(
        re.findall(
            r"POLICY_TAG\s*:\s*([A-Z]{2}-\d{4}-\d{2})",
            "\n".join(p.read_text(encoding="utf-8") for p in sorted(TRANSCRIPT_DIR.glob("*.txt"))),
        )
    )
    assert tags
    assert data["policy_ref"] in tags


def test_juliet_policy_ref_matches_active_tag():
    """Policy ref should select the ACTIVE tag (not just any transcript tag)."""
    _run()
    data = _load()
    active_tag, _, _ = _extract_active_policy(_transcript_text(TRANSCRIPT_DIR))
    assert active_tag
    assert data["policy_ref"] == active_tag


def test_kilo_allowed_prefixes_never_marked_invalid():
    """If a ref matches an allowed prefix, it should not be marked invalid."""
    _run()
    data = _load()
    _, prefixes, _ = _extract_active_policy(_transcript_text(TRANSCRIPT_DIR))
    assert prefixes
    for run in data["runs"]:
        for link in run["links"]:
            ref = link["ref"]
            ok = link["ok"]
            if any(ref.startswith(p) for p in prefixes):
                assert ok is True


def test_lima_tool_does_not_modify_fixture_runs():
    """Audit must not mutate input run directories (bytes or mtimes)."""
    before = _snapshot_tree(RUNS_DIR)
    proc = _run()
    assert proc.returncode == 0, proc.stderr.decode()
    after = _snapshot_tree(RUNS_DIR)
    assert before == after


def test_mike_alert_paths_point_to_real_files():
    """Every alert path must correspond to an existing file under its run directory."""
    _run()
    data = _load()
    for run in data["runs"]:
        run_id = run["id"]
        root = RUNS_DIR / f"run_{run_id}"
        for alert in run["alerts"]:
            path = alert["path"]
            assert path.startswith("/")
            assert ".." not in path
            on_disk = root / path.lstrip("/")
            assert on_disk.is_file()


def test_november_links_unique_per_run():
    """Links should not contain duplicates within a run (prevents double-counting)."""
    _run()
    data = _load()
    for run in data["runs"]:
        refs = [x["ref"] for x in run["links"]]
        assert refs == sorted(refs)
        assert len(refs) == len(set(refs))


def test_oscar_approval_rows_have_unique_ids_and_nonempty_reason():
    """Approval rows must be stable, uniquely identified, and explain verdicts."""
    _run()
    data = _load()
    for run in data["runs"]:
        ids = [x["id"] for x in run["approvals"]]
        assert ids == sorted(ids)
        assert len(ids) == len(set(ids))
        for row in run["approvals"]:
            assert isinstance(row["reason"], str)
            assert row["reason"].strip()


def test_papa_artifact_hash_hex_format_and_bytes_consistency():
    """Artifact rows must use lowercase hex digests and consistent byte sizes."""
    _run()
    data = _load()
    for run in data["runs"]:
        for art in run["artifacts"]:
            assert re.fullmatch(r"[0-9a-f]{64}", art["hash_hex"])
            assert isinstance(art["bytes"], int) and art["bytes"] >= 0
            p = RUNS_DIR / f"run_{run['id']}" / "artifacts" / art["name"]
            assert p.is_file()
            assert art["bytes"] == p.stat().st_size


def test_quebec_transcript_hash_changes_with_one_byte_edit():
    """Transcript hash must change when the transcript corpus changes."""
    with tempfile.TemporaryDirectory() as td:
        tdir = pathlib.Path(td)
        # Use a policy tag that already exists on solver-visible surfaces.
        (tdir / "meeting_01.txt").write_text(
            "\n".join(
                [
                    "POLICY_TAG: SR-2026-04",
                    "STATUS: ACTIVE",
                    "APPROVAL_KEY: alpha-review-key-seed",
                    "NONCE_FMT: NNC-v2:<run>:<8hex>",
                    "REDACT: token:\\s*[a-zA-Z0-9_]{8,64}",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        (tdir / "meeting_02.txt").write_text("ALLOW_REF_PREFIX: artifact://public/\n", encoding="utf-8")
        out1 = tdir / "report.json"
        out2 = tdir / "report2.json"

        proc1 = _run_custom(RUNS_DIR, tdir, out1)
        assert proc1.returncode == 0, proc1.stderr.decode()
        h1 = json.loads(out1.read_text(encoding="utf-8"))["transcript_hash"]

        # one-byte edit
        (tdir / "meeting_02.txt").write_text("ALLOW_REF_PREFIX: artifact://public/ \n", encoding="utf-8")
        proc2 = _run_custom(RUNS_DIR, tdir, out2)
        assert proc2.returncode == 0, proc2.stderr.decode()
        h2 = json.loads(out2.read_text(encoding="utf-8"))["transcript_hash"]

        assert h1 != h2


def test_romeo_synthetic_active_tag_beats_late_draft_tag():
    """When an ACTIVE tag exists earlier, later draft tags must not override it."""
    with tempfile.TemporaryDirectory() as td:
        tdir = pathlib.Path(td)
        (tdir / "meeting_01.txt").write_text(
            "\n".join(
                [
                    "POLICY_TAG: SR-2026-04",
                    "STATUS: ACTIVE",
                    "APPROVAL_KEY: alpha-review-key-seed",
                    "NONCE_FMT: NNC-v2:<run>:<8hex>",
                    "ALLOW_REF_PREFIX: artifact://public/",
                    "REDACT: token:\\s*[a-zA-Z0-9_]{8,64}",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        (tdir / "meeting_02.txt").write_text(
            "\n".join(
                [
                    "POLICY_TAG: SR-2026-05",
                    "STATUS: DRAFT",
                    "ALLOW_REF_PREFIX: artifact://private/",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        out = tdir / "report.json"
        proc = _run_custom(RUNS_DIR, tdir, out)
        assert proc.returncode == 0, proc.stderr.decode()
        data = json.loads(out.read_text(encoding="utf-8"))
        assert data["policy_ref"] == "SR-2026-04"


def test_uniform_alpha_per_line_exposure_alerts():
    """Each exposure log line must become its own alert (not one alert per file)."""
    _run()
    data = _load()
    alpha = next(r for r in data["runs"] if r["id"] == "alpha")
    assert len(alpha["alerts"]) == 2
    paths = {a["path"] for a in alpha["alerts"]}
    assert paths == {"/logs/stdout.txt"}


def test_uniform_delta_nested_log_line_alerts():
    """Nested log paths must still produce per-line alerts."""
    _run()
    data = _load()
    delta = next(r for r in data["runs"] if r["id"] == "delta")
    assert len(delta["alerts"]) == 2
    paths = {a["path"] for a in delta["alerts"]}
    assert "/logs/stdout.txt" in paths
    assert "/logs/nested/trace.log" in paths


def test_uniform_charlie_legacy_nonce_reason_code():
    """Legacy nonce versions must surface invalid-nonce, not invalid-proof."""
    _run()
    data = _load()
    charlie = next(r for r in data["runs"] if r["id"] == "charlie")
    reasons = {x["id"]: (x["ok"], x["reason"]) for x in charlie["approvals"]}
    assert reasons["ap-charlie-2"][0] is False
    assert reasons["ap-charlie-2"][1] == "invalid-nonce"


def test_uniform_delta_legacy_nonce_reason_code():
    """Delta run rejects NNC-v1 nonces under the active v2 format."""
    _run()
    data = _load()
    delta = next(r for r in data["runs"] if r["id"] == "delta")
    row = next(x for x in delta["approvals"] if x["id"] == "ap-delta-2")
    assert row["ok"] is False
    assert row["reason"] == "invalid-nonce"


def test_uniform_run_order_by_meta_id():
    """Runs must be ordered by meta id, not fixture directory name."""
    _run()
    data = _load()
    assert [r["id"] for r in data["runs"]] == ["alpha", "bravo", "charlie", "delta"]


def test_uniform_snippet_redaction_marker_shape():
    """Redaction must use angle-bracket token from the lexicon, not square brackets."""
    _run()
    raw = OUT.read_text(encoding="utf-8")
    assert "[REDACTED]" not in raw
    data = _load()
    for run in data["runs"]:
        for alert in run["alerts"]:
            assert "<redacted>" in alert["snippet"]


def test_uniform_draft_private_prefix_does_not_apply():
    """Draft-only private artifact prefixes in the transcript must not validate bravo private refs."""
    _run()
    data = _load()
    bravo = next(r for r in data["runs"] if r["id"] == "bravo")
    by_ref = {x["ref"]: x["ok"] for x in bravo["links"]}
    assert by_ref["artifact://private/model-B@v1"] is False


def test_uniform_totals_include_delta_run():
    """Fixture corpus includes four runs; totals must reflect all of them."""
    _run()
    data = _load()
    assert data["totals"]["run_count"] == 4
    assert len(data["runs"]) == 4


def test_tango_exposed_log_files_are_covered_by_alerts():
    """If a run log file contains exposure markers, there must be an alert for that file path."""
    _run()
    data = _load()
    by_id = {r["id"]: r for r in data["runs"]}

    for run_dir in sorted([p for p in RUNS_DIR.iterdir() if p.is_dir() and p.name.startswith("run_")]):
        run_id = run_dir.name.removeprefix("run_")
        log_dir = run_dir / "logs"
        if not log_dir.exists():
            continue
        expected_paths: set[str] = set()
        for p in log_dir.rglob("*"):
            if not p.is_file():
                continue
            txt = p.read_text(encoding="utf-8")
            if "api_key=" in txt or "token:" in txt:
                expected_paths.add("/" + str(p.relative_to(run_dir)).replace("\\", "/"))

        got_paths = {a["path"] for a in by_id[run_id]["alerts"]}
        assert expected_paths.issubset(got_paths)
