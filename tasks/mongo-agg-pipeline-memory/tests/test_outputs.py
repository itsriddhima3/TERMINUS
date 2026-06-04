"""Outcome checks for MongoDB spine pipeline audit report."""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

APP = Path("/app")
OUT = APP / "output"
REPORT = OUT / "pipeline_audit.json"
AUDIT = APP / "app" / "pipeline_audit.sh"
SPINE_RUN = APP / "runners" / "k7_execute.sh"
ENSURE = APP / "init" / "ensure_mongo.sh"
MATRIX = APP / "data" / "workload_matrix.json"
REGISTRY = APP / "docs" / "spine_predicate_registry.md"
INVOKE_POLICY = APP / "config" / "invoke_policy.json"
MONGOSH = APP / "lib" / "mongosh_wrap.sh"
STAGE_DIGEST = APP / "app" / "stage_digest.js"
INDEPENDENT_TOTAL = APP / "app" / "independent_total.js"

LABEL = "WK-SPINE-EMEA"
LAB_EVENTS = 120_000
METRICS_SNAP_ROWS = 120


def load_matrix() -> dict:
    return json.loads(MATRIX.read_text(encoding="utf-8"))


def load_bands() -> dict:
    return load_matrix()["workloads"][LABEL]["acceptance_bands"]


def load_workload() -> dict:
    return load_matrix()["workloads"][LABEL]


def load_contract() -> dict:
    return load_matrix()["report_contract"]


def run_checked(cmd: list[str], *, timeout: int = 600) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(cmd, text=True, capture_output=True, timeout=timeout, check=False)
    if result.returncode != 0:
        raise AssertionError(
            f"command failed: {' '.join(cmd)}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
    return result


def run_audit() -> dict:
    run_checked(["bash", str(ENSURE)])
    OUT.mkdir(parents=True, exist_ok=True)
    run_checked(["bash", str(AUDIT)])
    return json.loads(REPORT.read_text(encoding="utf-8"))


def mongosh_json(script: Path) -> dict:
    run_checked(["bash", str(ENSURE)])
    proc = run_checked(
        ["bash", "-lc", f"{MONGOSH} --quiet --file {script}"]
    )
    line = proc.stdout.strip().splitlines()[-1]
    return json.loads(line)


def expected_emea_purchase_total() -> int:
    regions = ("EMEA", "APAC", "AMER")
    events = ("purchase", "click", "view")
    total = 0
    for i in range(LAB_EVENTS):
        if regions[i % 3] == "EMEA" and events[(i // 3) % 3] == "purchase":
            total += (i % 100) + 1
    return total


def expected_emea_purchase_count() -> int:
    regions = ("EMEA", "APAC", "AMER")
    events = ("purchase", "click", "view")
    count = 0
    for i in range(LAB_EVENTS):
        if regions[i % 3] == "EMEA" and events[(i // 3) % 3] == "purchase":
            count += 1
    return count


def expected_apac_purchase_total() -> int:
    regions = ("EMEA", "APAC", "AMER")
    events = ("purchase", "click", "view")
    total = 0
    for i in range(LAB_EVENTS):
        if regions[i % 3] == "APAC" and events[(i // 3) % 3] == "purchase":
            total += (i % 100) + 1
    return total


def live_pipeline_hash() -> str:
    script = (
        'const crypto=require("crypto");'
        'const {phase_bundle}=require("/app/x9/p9a_bundle.js");'
        'const stages=phase_bundle({region:"EMEA",eventType:"purchase"});'
        'print(crypto.createHash("sha256").update(JSON.stringify(stages)).digest("hex"));'
    )
    proc = run_checked(["bash", str(MONGOSH), "--quiet", "--eval", script])
    return proc.stdout.strip().splitlines()[-1]


def spine_runner_total() -> int:
    run_checked(["bash", str(ENSURE)])
    proc = run_checked(["bash", str(SPINE_RUN)])
    for line in proc.stdout.splitlines():
        match = re.fullmatch(r"SPINE_OK total=(\d+)", line.strip())
        if match:
            return int(match.group(1))
    raise AssertionError(
        f"spine runner missing SPINE_OK line\nstdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
    )


def events_count_documents(region: str, event_type: str) -> int:
    run_checked(["bash", str(ENSURE)])
    proc = run_checked(
        [
            "bash",
            "-lc",
            (
                f"{MONGOSH} --quiet --eval "
                f"'print(db.events.countDocuments({{region:\"{region}\","
                f'event_type:"{event_type}"}}))\''
            ),
        ]
    )
    return int(proc.stdout.strip().splitlines()[-1])


def live_bundle_tail_sort() -> dict:
    script = (
        'const {phase_bundle}=require("/app/x9/p9a_bundle.js");'
        'const stages=phase_bundle({region:"EMEA",eventType:"purchase"});'
        "const last=stages[stages.length-1]||{};"
        "const sortStage=last['$sort'];"
        "print(JSON.stringify({"
        "stage_count:stages.length,"
        "last_kind:sortStage?'sort':'other',"
        "sort_total_desc:!!(sortStage&&sortStage.total===-1)"
        "}));"
    )
    proc = run_checked(["bash", str(MONGOSH), "--quiet", "--eval", script])
    return json.loads(proc.stdout.strip().splitlines()[-1])


def test_audit_report_exists_and_schema() -> None:
    """Audit JSON exists and includes every field from the workload report contract."""
    report = run_audit()
    required = load_contract()["required_fields"]
    for field in required:
        assert field in report, f"missing field {field}"


def test_lane_job_exit_zero() -> None:
    """Lane runner completes without aggregation abort."""
    run_checked(["bash", str(ENSURE)])
    run_checked(["bash", str(SPINE_RUN)])


def test_memory_limit_not_exceeded() -> None:
    """Audit reports no aggregation RAM cap abort for the spine workload."""
    report = run_audit()
    bands = load_bands()
    assert report["memory_limit_exceeded"] is bands["require_memory_limit_exceeded"]


def test_allow_disk_enabled() -> None:
    """Runner enables disk spill for batch analytics per workload matrix."""
    report = run_audit()
    bands = load_bands()
    assert report["allow_disk_enabled"] is bands["require_allow_disk_enabled"]


def test_first_stage_is_match() -> None:
    """First pipeline stage is a selective predicate on raw document fields."""
    report = run_audit()
    bands = load_bands()
    assert report["first_stage_kind"] == bands["require_first_stage_kind"]


def test_match_stage_index_zero() -> None:
    """Selective predicate stage index is zero in the spine bundle."""
    report = run_audit()
    bands = load_bands()
    assert report["match_stage_index"] == bands["require_match_stage_index"]


def test_result_total_in_band() -> None:
    """Grouped value sum for WK-SPINE-EMEA sits inside matrix acceptance band."""
    report = run_audit()
    bands = load_bands()
    total = report["result_total"]
    assert bands["result_total_min"] <= total <= bands["result_total_max"]
    assert total == expected_emea_purchase_total()


def test_grouped_keys_in_band() -> None:
    """Grouped key count sits inside matrix acceptance band."""
    report = run_audit()
    bands = load_bands()
    keys = report["grouped_keys"]
    assert bands["grouped_keys_min"] <= keys <= bands["grouped_keys_max"]
    assert keys == 1


def test_examined_ratio_below_cap() -> None:
    """Explain examined-to-returned ratio stays below matrix cap after early filtering."""
    report = run_audit()
    bands = load_bands()
    assert report["examined_to_returned_ratio"] <= bands["examined_to_returned_ratio_max"]


def test_pipeline_hash_stable() -> None:
    """Pipeline hash is stable across consecutive audit runs."""
    first = run_audit()
    second = run_audit()
    assert first["pipeline_hash"] == second["pipeline_hash"]
    assert len(first["pipeline_hash"]) == 64


def test_rerun_idempotent() -> None:
    """Key audit metrics match across consecutive audit runs."""
    first = run_audit()
    second = run_audit()
    for key in (
        "result_total",
        "grouped_keys",
        "memory_limit_exceeded",
        "allow_disk_enabled",
        "first_stage_kind",
        "match_stage_index",
    ):
        assert first[key] == second[key]


def test_decoy_rollup_untouched() -> None:
    """Hourly beta rollup on metrics_snap still returns totals inside decoy band."""
    run_checked(["bash", str(ENSURE)])
    proc = run_checked(
        ["bash", "-lc", f"{MONGOSH} --quiet --file /app/decoy/beta_probe.js"]
    )
    payload = json.loads(proc.stdout.strip().splitlines()[-1])
    decoy = load_matrix()["decoy"]
    assert decoy["result_total_min"] <= payload["total"] <= decoy["result_total_max"]


def test_registry_names_spine_filters() -> None:
    """Spine predicate registry documents WK-SPINE-EMEA filter tokens."""
    text = REGISTRY.read_text(encoding="utf-8")
    workload = load_workload()
    assert workload["filter_region"] in text
    assert workload["filter_event_type"] in text


def test_report_schema_version_matches_matrix() -> None:
    """Audit schema_version matches the workload matrix schema_version field."""
    report = run_audit()
    matrix = load_matrix()
    assert report["schema_version"] == matrix["schema_version"]


def test_workload_label_and_spine_collection_contract() -> None:
    """Audit names WK-SPINE-EMEA against the events spine collection."""
    report = run_audit()
    workload = load_workload()
    assert report["workload_label"] == LABEL
    assert report["spine_collection"] == workload["spine_collection"]


def test_filter_fields_match_workload_matrix() -> None:
    """Audit filter_region and filter_event_type mirror the workload matrix."""
    report = run_audit()
    workload = load_workload()
    assert report["filter_region"] == workload["filter_region"]
    assert report["filter_event_type"] == workload["filter_event_type"]


def test_examined_ratio_reflects_selective_scan() -> None:
    """Examined-to-returned ratio tracks selective scan volume, not full store size."""
    report = run_audit()
    selective = expected_emea_purchase_count()
    ratio = report["examined_to_returned_ratio"]
    assert selective * 0.5 < ratio < selective * 2.0
    assert ratio < LAB_EVENTS * 0.5


def test_live_bundle_stage_count_three() -> None:
    """Live spine bundle exposes exactly three stages after tail attachment is fixed."""
    digest = mongosh_json(STAGE_DIGEST)
    assert digest["stage_count"] == 3


def test_live_bundle_opens_with_raw_field_match() -> None:
    """First live bundle stage matches on region and event_type document fields."""
    digest = mongosh_json(STAGE_DIGEST)
    assert digest["first_stage_kind"] == "match"
    assert digest["first_has_region"] is True
    assert digest["first_has_event_type"] is True


def test_live_bundle_no_document_level_tail_match() -> None:
    """No post-group stage re-applies a document-level region predicate."""
    digest = mongosh_json(STAGE_DIGEST)
    assert digest["tail_document_match"] is False


def test_independent_aggregate_matches_audit() -> None:
    """Independent allowDiskUse rollup on events matches audit result_total."""
    report = run_audit()
    independent = mongosh_json(INDEPENDENT_TOTAL)
    assert independent["total"] == report["result_total"]
    assert independent["total"] == expected_emea_purchase_total()


def test_events_store_lab_scale_populated() -> None:
    """Events store document count matches the lab replica size."""
    run_checked(["bash", str(ENSURE)])
    proc = run_checked(
        [
            "bash",
            "-lc",
            f'{MONGOSH} --quiet --eval \'print(db.events.estimatedDocumentCount())\'',
        ]
    )
    count = int(proc.stdout.strip().splitlines()[-1])
    assert count == LAB_EVENTS


def test_metrics_snap_seed_row_count() -> None:
    """Metrics snap collection retains the seeded hourly beta row count."""
    run_checked(["bash", str(ENSURE)])
    proc = run_checked(
        [
            "bash",
            "-lc",
            f'{MONGOSH} --quiet --eval \'print(db.metrics_snap.estimatedDocumentCount())\'',
        ]
    )
    count = int(proc.stdout.strip().splitlines()[-1])
    assert count == METRICS_SNAP_ROWS


def test_triple_audit_hash_and_total_stable() -> None:
    """Three consecutive audits share one pipeline_hash and one result_total."""
    reports = [run_audit() for _ in range(3)]
    totals = {row["result_total"] for row in reports}
    hashes = {row["pipeline_hash"] for row in reports}
    assert len(totals) == 1
    assert len(hashes) == 1
    assert reports[0]["result_total"] == expected_emea_purchase_total()


def test_invoke_policy_allows_spill() -> None:
    """WK-SPINE invoke policy JSON enables batch spill for spine_defaults."""
    policy = json.loads(INVOKE_POLICY.read_text(encoding="utf-8"))
    assert policy["spine_defaults"]["allow_disk_use"] is True


def test_examined_ratio_decomposes_to_selective_count() -> None:
    """Examined-to-returned ratio times grouped row count equals selective document count."""
    report = run_audit()
    selective = expected_emea_purchase_count()
    keys = report["grouped_keys"]
    assert keys >= 1
    reconstructed = report["examined_to_returned_ratio"] * keys
    assert abs(reconstructed - selective) < 0.01
    assert selective == events_count_documents("EMEA", "purchase")


def test_spine_runner_emits_total_matching_audit() -> None:
    """Spine lane runner stdout total matches audit result_total after repair."""
    report = run_audit()
    runner_total = spine_runner_total()
    assert runner_total == report["result_total"]
    assert runner_total == expected_emea_purchase_total()


def test_pipeline_hash_matches_live_bundle_sha256() -> None:
    """Audit pipeline_hash equals SHA-256 of the wired live phase_bundle stages."""
    report = run_audit()
    digest = report["pipeline_hash"]
    assert digest == live_pipeline_hash()
    assert len(digest) == 64
    int(digest, 16)


def test_apac_purchase_total_differs_from_spine_result() -> None:
    """EMEA spine total is distinct from the APAC purchase rollup on the same seed."""
    report = run_audit()
    apac_total = expected_apac_purchase_total()
    assert apac_total > 0
    assert apac_total != report["result_total"]
    assert report["result_total"] == expected_emea_purchase_total()


def test_audit_boolean_fields_are_json_booleans() -> None:
    """Spill and memory-cap flags in the audit report are JSON booleans, not strings."""
    report = run_audit()
    assert isinstance(report["memory_limit_exceeded"], bool)
    assert isinstance(report["allow_disk_enabled"], bool)
    bands = load_bands()
    assert report["memory_limit_exceeded"] is bands["require_memory_limit_exceeded"]
    assert report["allow_disk_enabled"] is bands["require_allow_disk_enabled"]


def test_live_bundle_closes_with_sort_on_total() -> None:
    """Repaired spine bundle ends with a descending sort on grouped total."""
    tail = live_bundle_tail_sort()
    assert tail["stage_count"] == 3
    assert tail["last_kind"] == "sort"
    assert tail["sort_total_desc"] is True


def test_emea_purchase_mean_value_consistent_with_total_and_count() -> None:
    """EMEA purchase average value implied by audit total and selective count is stable."""
    report = run_audit()
    count = expected_emea_purchase_count()
    total = report["result_total"]
    assert count > 0
    mean = total / count
    assert 50.0 < mean < 51.0
    assert abs(total - count * mean) < 0.01


def test_count_documents_emea_purchase_matches_ratio_numerator() -> None:
    """countDocuments for EMEA purchase equals examined_to_returned_ratio numerator."""
    report = run_audit()
    counted = events_count_documents("EMEA", "purchase")
    assert counted == expected_emea_purchase_count()
    if report["grouped_keys"] > 0:
        assert report["examined_to_returned_ratio"] == counted / report["grouped_keys"]


def test_quintuple_audit_all_contract_fields_stable() -> None:
    """Five consecutive audits keep every report-contract field identical."""
    fields = load_contract()["required_fields"]
    reports = [run_audit() for _ in range(5)]
    for field in fields:
        values = {json.dumps(row[field], sort_keys=True) for row in reports}
        assert len(values) == 1, f"field {field} drifted across quintuple audit"


def test_runner_profile_and_matrix_filters_triangulate_with_report() -> None:
    """Runner profile, workload matrix, and audit agree on spine collection and filters."""
    report = run_audit()
    profile = json.loads(
        (APP / "config" / "w9_profile.json").read_text(encoding="utf-8")
    )
    workload = load_workload()
    prof = profile["workloads"][LABEL]
    assert prof["spine_collection"] == workload["spine_collection"] == report["spine_collection"]
    assert prof["filter_region"] == workload["filter_region"] == report["filter_region"]
    assert (
        prof["filter_event_type"]
        == workload["filter_event_type"]
        == report["filter_event_type"]
    )
    assert report["filter_region"] == workload["filter_region"]
    assert report["filter_event_type"] == workload["filter_event_type"]
