"""Outcome checks for PostgreSQL scope isolation audit report."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

APP = Path("/app")
OUT = APP / "output"
REPORT = OUT / "boundary_audit.json"
AUDIT = APP / "app" / "audit_runner.sh"
ENSURE = APP / "init" / "ensure_pg.sh"

CATALOG = ["Acme-Crate", "Beta-Tote", "Delta-Bin"]
SCENARIOS = (
    "adhoc_single",
    "reuse_stmt",
    "pool_rotate",
    "join_path",
    "view_path",
    "batch_fetch",
    "triple_hop",
    "savepoint_cycle",
    "nested_subquery",
    "aggregate_reuse",
    "cte_chain",
    "inventory_lane",
    "audit_log_chain",
    "union_rotate",
    "window_rank",
    "reader_lane",
    "warm_cache_first",
    "dual_stmt_interleave",
    "lateral_correlation",
)

ACTIVE_COUNTS = {
    "Acme-Crate": 2,
    "Beta-Tote": 2,
    "Delta-Bin": 4,
}

CONTACT_COUNTS = {
    "Acme-Crate": 2,
    "Beta-Tote": 1,
    "Delta-Bin": 2,
}


def run_checked(cmd: list[str], *, timeout: int = 180) -> None:
    result = subprocess.run(cmd, text=True, capture_output=True, timeout=timeout, check=False)
    if result.returncode != 0:
        raise AssertionError(
            f"command failed: {' '.join(cmd)}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )


def run_audit() -> dict:
    run_checked(["bash", str(ENSURE)])
    OUT.mkdir(parents=True, exist_ok=True)
    run_checked(["bash", str(AUDIT)])
    return json.loads(REPORT.read_text(encoding="utf-8"))


def pg_scalar(query: str) -> str:
    result = subprocess.run(
        ["psql", "-U", "postgres", "-d", "saas_db", "-At", "-c", query],
        text=True,
        capture_output=True,
        timeout=60,
        check=False,
    )
    if result.returncode != 0:
        raise AssertionError(
            "postgres query failed\n"
            f"query: {query}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
    return result.stdout.strip()


def tenant_policy_exprs() -> dict[str, str]:
    rows = pg_scalar(
        """
        SELECT c.relname, pg_get_expr(p.polqual, p.polrelid)
        FROM pg_policy p
        JOIN pg_class c ON c.oid = p.polrelid
        WHERE c.relname IN ('ledger', 'contacts', 'inventory', 'audit_log')
        ORDER BY c.relname;
        """
    )
    exprs: dict[str, str] = {}
    for line in rows.splitlines():
        if not line.strip():
            continue
        table, expr = line.split("|", 1)
        exprs[table] = expr
    return exprs


def assert_isolated(row: dict) -> None:
    assert row["foreign_labels_seen"] == []


@pytest.fixture(scope="module")
def report() -> dict:
    return run_audit()


def test_report_schema_version(report: dict) -> None:
    """Audit report declares schema version 1."""
    assert report["schema_version"] == 1


def test_catalog_labels_present(report: dict) -> None:
    """Catalog labels list the three customer organizations from the prompt."""
    assert report["catalog_labels"] == CATALOG


def test_all_scenarios_present(report: dict) -> None:
    """Every access pattern named in the contract appears in the scenarios map."""
    for name in SCENARIOS:
        assert name in report["scenarios"]


def test_no_scenario_leaks(report: dict) -> None:
    """No scenario surfaces foreign catalog labels after context switches."""
    for name in SCENARIOS:
        row = report["scenarios"][name]
        assert row["cross_scope_visible"] is False, name
        assert_isolated(row)


def test_tenant_policies_avoid_inlined_session_reads() -> None:
    """Core tenant row filters do not inline app.scope_id reads inside policy quals."""
    for table, qual in tenant_policy_exprs().items():
        assert "current_setting('app.scope_id'" not in qual, table
        assert 'current_setting("app.scope_id"' not in qual, table


def test_scope_accessor_rebinds_each_statement() -> None:
    """The shared session scope accessor stays volatile so reused plans rebind filters."""
    assert pg_scalar("SELECT provolatile FROM pg_proc WHERE proname = 'fn_k7';") == "v"


def test_adhoc_single_row_count(report: dict) -> None:
    """Ad-hoc reads return the expected owned row volume for the active catalog entry."""
    row = report["scenarios"]["adhoc_single"]
    assert row["owned_row_count"] == max(ACTIVE_COUNTS.values())


def test_reuse_stmt_row_count(report: dict) -> None:
    """Reused statement handles return Beta-Tote owned row volume after the switch."""
    row = report["scenarios"]["reuse_stmt"]
    assert row["owned_row_count"] == ACTIVE_COUNTS["Beta-Tote"]


def test_pool_rotate_row_count(report: dict) -> None:
    """Pooled rotation returns Delta-Bin owned row volume after the switch."""
    row = report["scenarios"]["pool_rotate"]
    assert row["owned_row_count"] == ACTIVE_COUNTS["Delta-Bin"]


def test_join_path_row_count(report: dict) -> None:
    """Joined reads return at least the Delta-Bin active ledger volume after the switch."""
    row = report["scenarios"]["join_path"]
    assert row["owned_row_count"] >= ACTIVE_COUNTS["Delta-Bin"]


def test_view_path_row_count(report: dict) -> None:
    """View-backed reads return at least the Acme-Crate active ledger volume after the switch."""
    row = report["scenarios"]["view_path"]
    assert row["owned_row_count"] >= ACTIVE_COUNTS["Acme-Crate"]


def test_batch_fetch_row_count(report: dict) -> None:
    """Batch fetch returns Beta-Tote owned row volume after the switch."""
    row = report["scenarios"]["batch_fetch"]
    assert row["owned_row_count"] == ACTIVE_COUNTS["Beta-Tote"]


def test_triple_hop_isolated(report: dict) -> None:
    """Three consecutive context hops on one prepared handle stay within Delta-Bin."""
    row = report["scenarios"]["triple_hop"]
    assert row["owned_row_count"] == ACTIVE_COUNTS["Delta-Bin"]


def test_savepoint_cycle_isolated(report: dict) -> None:
    """Savepoint rollback on a reused handle still honors Beta-Tote after the switch."""
    row = report["scenarios"]["savepoint_cycle"]
    assert row["owned_row_count"] == ACTIVE_COUNTS["Beta-Tote"]


def test_nested_subquery_isolated(report: dict) -> None:
    """Prepared nested subqueries rebind filters when the context moves to Beta-Tote."""
    row = report["scenarios"]["nested_subquery"]
    assert row["owned_row_count"] == ACTIVE_COUNTS["Beta-Tote"]


def test_aggregate_reuse_isolated(report: dict) -> None:
    """Prepared aggregate counts track Beta-Tote row volume after the switch."""
    row = report["scenarios"]["aggregate_reuse"]
    assert row["owned_row_count"] == ACTIVE_COUNTS["Beta-Tote"]


def test_cte_chain_isolated(report: dict) -> None:
    """CTE-backed prepared reads stay within Delta-Bin after the switch."""
    row = report["scenarios"]["cte_chain"]
    assert row["owned_row_count"] == ACTIVE_COUNTS["Delta-Bin"]


def test_inventory_lane_isolated(report: dict) -> None:
    """Inventory SKU reads expose only Acme-Crate CR- prefixed rows after the switch."""
    row = report["scenarios"]["inventory_lane"]
    assert row["owned_row_count"] == ACTIVE_COUNTS["Acme-Crate"]


def test_audit_log_chain_isolated(report: dict) -> None:
    """Audit-log probes return a single Beta-Tote event marker after the switch."""
    row = report["scenarios"]["audit_log_chain"]
    assert row["owned_row_count"] == 1


def test_union_rotate_isolated(report: dict) -> None:
    """Union reads across ledger and contacts stay within Beta-Tote membership."""
    row = report["scenarios"]["union_rotate"]
    expected = ACTIVE_COUNTS["Beta-Tote"] + CONTACT_COUNTS["Beta-Tote"]
    assert row["owned_row_count"] == expected


def test_window_rank_isolated(report: dict) -> None:
    """Window-ranked prepared reads stay within Acme-Crate after the switch."""
    row = report["scenarios"]["window_rank"]
    assert row["owned_row_count"] == ACTIVE_COUNTS["Acme-Crate"]


def test_reader_lane_isolated(report: dict) -> None:
    """Read-only role lanes honor Acme-Crate boundaries on prepared reuse."""
    row = report["scenarios"]["reader_lane"]
    assert row["owned_row_count"] == ACTIVE_COUNTS["Acme-Crate"]


def test_warm_cache_first_isolated(report: dict) -> None:
    """Warm-cache handle reuse stays within Delta-Bin after startup preparation."""
    row = report["scenarios"]["warm_cache_first"]
    assert row["owned_row_count"] == ACTIVE_COUNTS["Delta-Bin"]


def test_dual_stmt_interleave_isolated(report: dict) -> None:
    """Interleaved prepared handles on one connection honor Beta-Tote after the switch."""
    row = report["scenarios"]["dual_stmt_interleave"]
    assert row["owned_row_count"] == ACTIVE_COUNTS["Beta-Tote"]


def test_lateral_correlation_isolated(report: dict) -> None:
    """Lateral correlated prepared reads stay within Acme-Crate after the switch."""
    row = report["scenarios"]["lateral_correlation"]
    assert row["owned_row_count"] == ACTIVE_COUNTS["Acme-Crate"]


def test_foreign_labels_are_strings(report: dict) -> None:
    """Foreign label arrays remain string lists even when empty."""
    for name in SCENARIOS:
        labels = report["scenarios"][name]["foreign_labels_seen"]
        assert isinstance(labels, list)
        assert all(isinstance(item, str) for item in labels)


# ---------------------------------------------------------------------------
# Hard structural tests — all fail in the broken environment, pass after fix
# ---------------------------------------------------------------------------


def test_svc_runner_plan_cache_mode() -> None:
    """svc_runner enforces custom plan cache to prevent generic-plan scope freeze."""
    config = pg_scalar(
        "SELECT array_to_string(rolconfig, ',') FROM pg_roles WHERE rolname='svc_runner';"
    )
    assert "plan_cache_mode=force_custom_plan" in config, (
        "svc_runner is missing plan_cache_mode=force_custom_plan; "
        "generic plans will cache a stale scope_id into the filter."
    )


def test_fn_k7_guard_is_volatile() -> None:
    """Scope guard helper fn_k7_guard() is VOLATILE so RLS quals re-evaluate each statement."""
    vol = pg_scalar("SELECT provolatile FROM pg_proc WHERE proname='fn_k7_guard';")
    assert vol == "v", (
        f"fn_k7_guard() has volatility '{vol}' — expected 'v' (VOLATILE); "
        "a non-volatile guard lets the planner cache scope checks across context switches."
    )


def test_fn_k7_refresh_is_volatile() -> None:
    """Long-session scope refresh helper fn_k7_refresh() is VOLATILE so GUC rebinds are never frozen."""
    vol = pg_scalar("SELECT provolatile FROM pg_proc WHERE proname='fn_k7_refresh';")
    assert vol == "v", (
        f"fn_k7_refresh() has volatility '{vol}' — expected 'v' (VOLATILE); "
        "a non-volatile refresh helper allows the session GUC to be optimised away."
    )


def test_org_dim_refresh_trigger_installed() -> None:
    """The scope-rebind trigger n4w_touch_trg fires on org_dim row updates."""
    count = pg_scalar(
        "SELECT count(*) FROM pg_trigger t "
        "JOIN pg_class c ON c.oid = t.tgrelid "
        "WHERE t.tgname = 'n4w_touch_trg' AND c.relname = 'org_dim';"
    )
    assert count == "1", (
        f"Expected 1 row for trigger n4w_touch_trg on org_dim, got {count!r}; "
        "without the trigger, org dimension updates cannot rebind long-lived sessions."
    )


def test_svc_reader_read_only_mode() -> None:
    """svc_reader role enforces read-only transaction mode by default."""
    config = pg_scalar(
        "SELECT array_to_string(rolconfig, ',') FROM pg_roles WHERE rolname='svc_reader';"
    )
    assert "default_transaction_read_only=on" in config, (
        "svc_reader is missing default_transaction_read_only=on; "
        "the role can execute writes, violating the read-only lane contract."
    )


def test_catalog_compliance_accessor_flag_true(report: dict) -> None:
    """Audit report's catalog_compliance confirms row-filter expressions use the scope accessor."""
    flag = report["catalog_compliance"]["tenant_policies_use_accessor"]
    assert flag is True, (
        "catalog_compliance.tenant_policies_use_accessor is False; "
        "at least one core-table policy still inlines the session GUC read directly."
    )


def test_catalog_compliance_volatile_flag_true(report: dict) -> None:
    """Audit report's catalog_compliance confirms the scope accessor is classified VOLATILE."""
    flag = report["catalog_compliance"]["scope_accessor_volatile"]
    assert flag is True, (
        "catalog_compliance.scope_accessor_volatile is False; "
        "fn_k7() remains STABLE or IMMUTABLE, allowing plan caching to freeze the scope."
    )


def test_policy_quals_call_fn_k7_guard() -> None:
    """Core-table row-filter USING clauses call fn_k7_guard() to validate scope context."""
    for table, qual in tenant_policy_exprs().items():
        assert "fn_k7_guard()" in qual, (
            f"Table '{table}' policy USING clause does not call fn_k7_guard(); "
            "unguarded policies can dereference a null scope handle and expose all rows."
        )


def test_svc_runner_statement_timeout_configured() -> None:
    """svc_runner role carries a statement_timeout to bound long-running catalog scans."""
    config = pg_scalar(
        "SELECT array_to_string(rolconfig, ',') FROM pg_roles WHERE rolname='svc_runner';"
    )
    assert "statement_timeout=" in config, (
        "svc_runner has no statement_timeout; unbounded scans under the service role "
        "can exhaust connections and mask scope-leak symptoms."
    )


def test_scope_touch_trigger_fn_is_volatile() -> None:
    """Scope-rebind trigger function n4w_touch() is VOLATILE to allow session-state mutations."""
    vol = pg_scalar("SELECT provolatile FROM pg_proc WHERE proname='n4w_touch';")
    assert vol == "v", (
        f"n4w_touch() has volatility '{vol}' — expected 'v' (VOLATILE); "
        "a non-volatile trigger body cannot safely call set_config() or fn_k7_refresh()."
    )
