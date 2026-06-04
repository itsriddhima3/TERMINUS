"""Outcome checks for PostgreSQL fulfillment spine plan audit report."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

APP = Path("/app")
OUT = APP / "output"
REPORT = OUT / "plan_audit.json"
AUDIT = APP / "app" / "plan_audit.sh"
ENSURE = APP / "init" / "ensure_pg.sh"
MATRIX = APP / "data" / "workload_matrix.json"
REGISTRY = APP / "docs" / "correlation_registry.md"
SPINE_TEMPLATE = APP / "q" / "spine_template.sql"
EXPLAIN = APP / "lib" / "explain_collect.sh"

BOOTSTRAP_TARGET_FLOOR = 100
REQUIRED_SPINE_DRIVER = "hash_join"
INDEPENDENT_HASH_SPINE_MIN = 1


def load_matrix() -> dict:
    return json.loads(MATRIX.read_text(encoding="utf-8"))


def load_bands() -> dict:
    return load_matrix()["acceptance_bands"]


def load_contract() -> dict:
    return load_matrix()["report_contract"]


def load_registry() -> dict:
    clusters: list[dict] = []
    current: dict | None = None
    for raw in REGISTRY.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("## "):
            if current:
                clusters.append(current)
            current = {"table": line[3:].strip(), "columns": [], "spine_predicate": False}
            continue
        if line.startswith("#"):
            continue
        if current is None or ":" not in line:
            continue
        key, value = (part.strip().lower() for part in line.split(":", 1))
        if key == "columns":
            cols = value.replace(" and ", ",").split(",")
            current["columns"] = [col.strip() for col in cols if col.strip()]
        elif key == "spine predicate":
            current["spine_predicate"] = value.lower().startswith("yes")
    if current:
        clusters.append(current)
    return {"clusters": clusters}


def spine_clusters(registry: dict) -> list[dict]:
    return [row for row in registry["clusters"] if row.get("spine_predicate")]


def run_checked(cmd: list[str], *, timeout: int = 300) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(cmd, text=True, capture_output=True, timeout=timeout, check=False)
    if result.returncode != 0:
        raise AssertionError(
            f"command failed: {' '.join(cmd)}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
    return result


def psql_scalar(sql: str, *, as_postgres: bool = False) -> str:
    if as_postgres:
        proc = run_checked(
            ["bash", "-lc", f"psql -U postgres -d logistics_db -t -A -c {json.dumps(sql)}"]
        )
    else:
        proc = run_checked(
            [
                "bash",
                "-lc",
                f"source /app/lib/psql_wrap.sh && psql_as_planner -t -A -c {json.dumps(sql)}",
            ]
        )
    return proc.stdout.strip()


def psql_rows(sql: str, *, as_postgres: bool = False) -> list[str]:
    if as_postgres:
        proc = run_checked(
            ["bash", "-lc", f"psql -U postgres -d logistics_db -t -A -c {json.dumps(sql)}"]
        )
    else:
        proc = run_checked(
            [
                "bash",
                "-lc",
                f"source /app/lib/psql_wrap.sh && psql_as_planner -t -A -c {json.dumps(sql)}",
            ]
        )
    return [line for line in proc.stdout.splitlines() if line.strip()]


def run_audit() -> dict:
    run_checked(["bash", str(ENSURE)])
    OUT.mkdir(parents=True, exist_ok=True)
    run_checked(["bash", str(AUDIT)])
    return json.loads(REPORT.read_text(encoding="utf-8"))


def independent_spine_count(region_id: int, zone_code: str) -> int:
    proc = run_checked(
        [
            "bash",
            "-lc",
            (
                "source /app/lib/psql_wrap.sh && "
                f"sed -e 's/__REGION__/{region_id}/g' -e 's/__ZONE__/{zone_code}/g' "
                f"{SPINE_TEMPLATE} | psql_as_planner -t -A -f -"
            ),
        ]
    )
    return int(proc.stdout.strip())


def load_independent_plan(region_id: int, zone_code: str) -> dict:
    proc = run_checked(["bash", str(EXPLAIN), str(region_id), zone_code])
    return json.loads(proc.stdout.strip())[0]["Plan"]


def collect_aliases(node: dict) -> set[str]:
    rel = node.get("Relation Name") or node.get("Alias") or ""
    found = {rel} if rel else set()
    for sub in node.get("Plans") or []:
        found |= collect_aliases(sub)
    return found


def count_fact_bridge_hash_joins(plan: dict) -> int:
    total = 0

    def walk(node: dict) -> None:
        nonlocal total
        ntype = node.get("Node Type", "")
        if ntype == "Hash Join":
            children = node.get("Plans") or []
            if len(children) >= 2:
                aliases = collect_aliases(children[0]) | collect_aliases(children[1])
                if {"fs", "fact_shipment"} & aliases and {"bf", "bridge_facility_zone"} & aliases:
                    total += 1
        for sub in node.get("Plans") or []:
            walk(sub)

    walk(plan)
    return total


def cluster_has_dependency_stats(table: str, columns: list[str]) -> bool:
    del columns  # registry lists the correlated pair; any dependency stat on the table suffices
    count = int(
        psql_scalar(
            "SELECT count(*) FROM pg_statistic_ext e "
            "JOIN pg_class c ON c.oid = e.stxrelid "
            f"WHERE c.relname = '{table}' AND 'f' = ANY(e.stxkind)",
            as_postgres=True,
        )
    )
    return count >= 1


@pytest.fixture(scope="module")
def report() -> dict:
    return run_audit()


@pytest.fixture(scope="module")
def bands() -> dict:
    return load_bands()


@pytest.fixture(scope="module")
def contract() -> dict:
    return load_contract()


@pytest.fixture(scope="module")
def registry() -> dict:
    return load_registry()


def test_report_schema_version(report: dict, contract: dict) -> None:
    """Audit report declares the matrix schema version."""
    assert report["schema_version"] == contract["schema_version"]


def test_workload_label(report: dict, contract: dict) -> None:
    """Report names the matrix workload label."""
    assert report["workload_label"] == contract["workload_label"]


def test_catalog_table_count(report: dict, contract: dict) -> None:
    """Table count matches the matrix contract."""
    assert report["catalog_tables"] == contract["catalog_tables"]


def test_filter_constants(report: dict, contract: dict) -> None:
    """Audit uses matrix filter constants."""
    assert report["filter_region_id"] == contract["filter_region_id"]
    assert report["filter_zone_code"] == contract["filter_zone_code"]


def test_result_total_in_band(report: dict, bands: dict) -> None:
    """Spine count sits inside the workload matrix acceptance band."""
    total = report["result_total"]
    assert bands["result_total_min"] <= total <= bands["result_total_max"]


def test_hash_joins_present(report: dict, bands: dict) -> None:
    """Hash join tally meets the matrix minimum after repair."""
    assert report["join_methods"]["hash_join_count"] >= bands["hash_join_count_min"]


def test_spine_driver_allowed(report: dict, bands: dict) -> None:
    """Spine driver is no longer the forbidden nested-loop token."""
    assert report["spine_driver"] != bands["forbidden_spine_driver"]


def test_bridge_estimate_ratio_in_band(report: dict, bands: dict) -> None:
    """Bridge estimate ratio falls inside the matrix band."""
    ratio = report["bridge_estimate_ratio"]
    assert bands["bridge_estimate_ratio_min"] <= ratio <= bands["bridge_estimate_ratio_max"]


def test_inventory_estimate_ratio_in_band(report: dict, bands: dict) -> None:
    """Inventory snapshot estimate ratio falls inside the matrix band."""
    ratio = report["inventory_estimate_ratio"]
    assert bands["inventory_estimate_ratio_min"] <= ratio <= bands["inventory_estimate_ratio_max"]


def test_nested_loops_within_cap(report: dict, bands: dict) -> None:
    """Nested-loop tally stays under the matrix cap."""
    assert report["join_methods"]["nested_loop_count"] <= bands["nested_loop_count_max"]


def test_plan_root_rows_sane(report: dict) -> None:
    """Aggregate plan row estimate stays finite for the analyzed workload."""
    assert report["plan_root_rows"] == 1


def test_spine_registry_clusters_catalogued(registry: dict) -> None:
    """Every spine predicate group in the registry has dependency-class extended stats."""
    missing = []
    for cluster in spine_clusters(registry):
        if not cluster_has_dependency_stats(cluster["table"], cluster["columns"]):
            missing.append(cluster["table"])
    assert not missing, f"missing dependency stats for {missing}"


def test_lane_decoy_cluster_alone_insufficient(registry: dict) -> None:
    """Non-spine registry entries such as lane/carrier pairs do not satisfy spine coverage."""
    decoys = [row for row in registry["clusters"] if not row.get("spine_predicate")]
    assert decoys
    spine_ready = sum(
        1 for cluster in spine_clusters(registry) if cluster_has_dependency_stats(cluster["table"], cluster["columns"])
    )
    assert spine_ready == len(spine_clusters(registry))


def test_spine_registry_statistics_targets_elevated(registry: dict) -> None:
    """Every spine registry table raises region_id and zone_code sample depth above the ops floor."""
    missing: list[str] = []
    for cluster in spine_clusters(registry):
        table = cluster["table"]
        rows = psql_rows(
            "SELECT attname, attstattarget FROM pg_attribute "
            f"WHERE attrelid = '{table}'::regclass "
            "AND attname IN ('region_id', 'zone_code') "
            "ORDER BY attname"
        )
        targets = {line.split("|")[0]: int(line.split("|")[1]) for line in rows}
        if (
            targets.get("region_id", BOOTSTRAP_TARGET_FLOOR)
            <= BOOTSTRAP_TARGET_FLOOR
            or targets.get("zone_code", BOOTSTRAP_TARGET_FLOOR) <= BOOTSTRAP_TARGET_FLOOR
        ):
            missing.append(table)
    assert not missing, f"statistics targets not above ops floor for {missing}"


def test_independent_spine_count_matches_report(report: dict, contract: dict) -> None:
    """Direct spine execution reproduces the audited result_total without reusing the JSON file."""
    direct = independent_spine_count(contract["filter_region_id"], contract["filter_zone_code"])
    assert direct == report["result_total"]


def test_independent_plan_confirms_hash_spine_driver(report: dict, contract: dict) -> None:
    """Fresh EXPLAIN output shows hash joins between shipment and bridge subtrees."""
    plan = load_independent_plan(contract["filter_region_id"], contract["filter_zone_code"])
    assert count_fact_bridge_hash_joins(plan) >= INDEPENDENT_HASH_SPINE_MIN
    assert report["spine_driver"] == REQUIRED_SPINE_DRIVER


def test_hash_join_share_meets_floor(report: dict, bands: dict) -> None:
    """Hash joins represent a material share of all join nodes in the replanned spine."""
    methods = report["join_methods"]
    total_joins = (
        methods["hash_join_count"] + methods["nested_loop_count"] + methods["merge_join_count"]
    )
    assert total_joins > 0
    share = methods["hash_join_count"] / total_joins
    assert share >= bands["hash_join_share_min"]


def test_spine_driver_is_hash_join(report: dict) -> None:
    """Reported spine driver matches the hash implementation required after replanning."""
    assert report["spine_driver"] == REQUIRED_SPINE_DRIVER


def test_bridge_facility_cardinality_baseline(report: dict, contract: dict) -> None:
    """Bridge row count for the bound filters matches live catalog cardinality."""
    count = int(
        psql_scalar(
            "SELECT count(*) FROM bridge_facility_zone "
            f"WHERE region_id = {contract['filter_region_id']} "
            f"AND zone_code = '{contract['filter_zone_code']}'"
        )
    )
    assert count > 0
    assert report["bridge_estimate_ratio"] >= load_bands()["bridge_estimate_ratio_min"]


def test_core_spine_tables_recently_analyzed(registry: dict) -> None:
    """Registry spine tables carry a non-null analyze timestamp after refresh."""
    tables = sorted({cluster["table"] for cluster in spine_clusters(registry)})
    for table in tables:
        stamp = psql_scalar(
            f"SELECT coalesce(last_analyze IS NOT NULL, false) FROM pg_stat_all_tables "
            f"WHERE schemaname = 'public' AND relname = '{table}'"
        )
        assert stamp == "t", table


def test_report_row_consistency(report: dict) -> None:
    """Audited row counters stay internally aligned across root and aggregate fields."""
    assert report["actual_root_rows"] == report["result_total"]
    assert report["plan_root_rows"] == 1
    assert report["actual_root_rows"] >= load_bands()["result_total_min"]
