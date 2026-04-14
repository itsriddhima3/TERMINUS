#!/usr/bin/env python3
"""
Mechanical collapse and discoverability checks for Terminal-Bench 3 tasks.

Organized around 4 root causes of task triviality:

  RC1 — Oracle simplification: Does the fix mostly REMOVE code rather than ADD logic?
  RC2 — Oracle predictability: Can you find the oracle-targeted files from instruction + file tree alone?
  RC3 — Verifier shallowness: Do tests check format/schema/existence or domain-correct computed values?
  RC4 — Tamper surface: Can the agent modify what the tests depend on to bypass domain reasoning?

Usage:
    python collapse_check.py tasks/<task-name>
    python collapse_check.py tasks/<task-name> --json

Exit codes: 0 = PASS, 1 = FAIL, 2 = WARN
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


def load_instruction(task_dir: Path) -> str:
    p = task_dir / "instruction.md"
    return p.read_text(encoding="utf-8") if p.exists() else ""

def load_oracle(task_dir: Path) -> str:
    p = task_dir / "solution" / "solve.sh"
    return p.read_text(encoding="utf-8") if p.exists() else ""

def load_tests(task_dir: Path) -> str:
    """Load all test files recursively: Python, JS, TS under tests/."""
    tests_dir = task_dir / "tests"
    if not tests_dir.is_dir():
        return ""
    parts = []
    # Python tests (recursive)
    for f in sorted(tests_dir.rglob("*.py")):
        if f.name.startswith("test") or f.name == "conftest.py":
            parts.append(f.read_text(encoding="utf-8", errors="replace"))
    # JS/TS tests (recursive — covers tests/unit/, tests/e2e/)
    for pattern in ("**/*.test.js", "**/*.test.ts", "**/*.spec.js", "**/*.spec.ts",
                     "**/*.test.jsx", "**/*.test.tsx"):
        for f in sorted(tests_dir.glob(pattern)):
            parts.append(f.read_text(encoding="utf-8", errors="replace"))
    return "\n".join(parts)

def env_files(task_dir: Path) -> list[Path]:
    env = task_dir / "environment"
    if not env.is_dir():
        return []
    return [f for f in env.rglob("*") if f.is_file()
            and f.name.lower() not in ("dockerfile", "docker-compose.yaml", "docker-compose.yml")]

def extract_keywords(text: str, min_len: int = 4) -> set[str]:
    text = re.sub(r'[`*#\[\](){}]', ' ', text)
    tokens = re.findall(r'[a-zA-Z][a-zA-Z0-9_-]{3,}', text)
    stop = {
        'must','should','that','this','with','from','your','have','will','when',
        'each','they','them','than','been','also','into','only','does','make',
        'after','before','under','over','about','between','through','during',
        'without','within','every','where','which','their','there','these',
        'those','other','some','same','such','more','most','keep','limit',
        'write','read','file','files','path','string','integer','boolean',
        'array','object','value','required','allowed','correctly','exactly',
        'properly','ascending','descending','rebuild','needed','changes',
        'implementation','fixed','include','source','main','test','tests',
        'data','config','default','common','util','utils','helper','base',
        'core','model','models','build','output','input','result','error',
        'format','type','types','state','status','info','context','driver',
        'runtime','internal','private','public','const','version','programs',
        'tools','cases','harness','code','module','modules','component',
        'system','process','report','level','entry','entries','binary',
        'library','container','environment','application','service',
    }
    return {t.lower() for t in tokens if t.lower() not in stop and len(t) >= min_len}

def oracle_touched_files(oracle: str) -> set[str]:
    targets = set()
    for pat in [
        r'cat\s*>\s*(\S+)',
        r"sed\s+-i\s+(?:'[^']*'|\"[^\"]*\"|\S+)\s+(\S+\.(?:cpp|c|h|hpp|py|rs|go|java|js|ts|toml|yaml|yml|json|conf|cfg|sh|S))",
        r'cp\s+\S+\s+(\S+)', r'install\s+.*?"?(\S+\.\w+)"?',
        r'copy_fixed\s+(\S+)', r'tee\s+(\S+)', r'patch\s+(?:-p\d\s+)?(\S+)',
    ]:
        targets.update(re.findall(pat, oracle))
    return targets

def oracle_heredoc_content(oracle: str) -> list[tuple[str, str]]:
    return [(m.group(1), m.group(2))
            for m in re.finditer(r"cat\s*>\s*(\S+)\s*<<['\"]?EOF['\"]?\n(.*?)\nEOF", oracle, re.DOTALL)]


# ═══════════════════════════════════════════════════════════════════════════
# RC1: Oracle Simplification
# ═══════════════════════════════════════════════════════════════════════════

def rc1_oracle_simplification(task_dir: Path) -> dict:
    """Does the fix mostly REMOVE code rather than ADD logic?"""
    oracle = load_oracle(task_dir)
    if not oracle:
        return {"check": "rc1_oracle_simplification", "severity": "WARN", "detail": "No oracle found"}

    heredocs = oracle_heredoc_content(oracle)
    env_dir = task_dir / "environment"

    if heredocs:
        net_delta = 0; files_simplified = 0; files_expanded = 0; neutralized = 0; comparisons = []
        for target, content in heredocs:
            rel = re.sub(r'^/app/', '', target)
            env_file = env_dir / rel
            if not env_file.exists():
                continue
            env_c = env_file.read_text(encoding="utf-8", errors="replace")
            el = len([l for l in env_c.splitlines() if l.strip()])
            ol = len([l for l in content.splitlines() if l.strip()])
            d = ol - el
            if d < 0: files_simplified += 1
            elif d > 0: files_expanded += 1
            net_delta += d
            comparisons.append({"file": rel, "env_lines": el, "oracle_lines": ol, "delta": d})
            neutralized += len(re.findall(
                r'\{[^{}]*(?:\(void\)|return\s+(?:0|true|false|nullptr)\s*;)[^{}]*\}', content, re.DOTALL))

        total = len(comparisons)
        if total == 0:
            return {"check": "rc1_oracle_simplification", "severity": "WARN", "detail": "No comparable files"}
        sr = files_simplified / total
        severity = "FAIL" if (sr > 0.6 and net_delta < -5) else "WARN" if (sr > 0.4 or neutralized >= 2) else "PASS"
        return {
            "check": "rc1_oracle_simplification", "severity": severity,
            "net_delta": net_delta, "files_simplified": files_simplified,
            "files_expanded": files_expanded, "total_files": total,
            "neutralized_functions": neutralized, "comparisons": comparisons[:10],
            "detail": f"Net delta: {net_delta:+d} lines across {total} files "
                      f"({files_simplified} simplified, {files_expanded} expanded, {neutralized} neutralized fns)",
        }
    else:
        lines = [l.strip() for l in oracle.splitlines()
                 if l.strip() and not l.strip().startswith("#")
                 and l.strip() not in ("#!/bin/bash","#!/usr/bin/env bash","set -euo pipefail")]
        dels = sum(1 for l in lines if re.match(r"sed\s+-i\s+'[^']*d'|sed\s+-i\s+.*\bd\b", l))
        edits = sum(1 for l in lines if re.match(r'sed |cp |copy_fixed|install |patch ', l))
        if edits == 0:
            return {"check": "rc1_oracle_simplification", "severity": "PASS", "detail": "No edit commands"}
        dr = dels / edits
        severity = "WARN" if dr > 0.5 else "PASS"
        return {
            "check": "rc1_oracle_simplification", "severity": severity,
            "deletions": dels, "total_edits": edits, "delete_ratio": round(dr, 2),
            "detail": f"{dels}/{edits} edit commands are deletions ({dr:.0%})",
        }


# ═══════════════════════════════════════════════════════════════════════════
# RC2: Oracle Predictability
# ═══════════════════════════════════════════════════════════════════════════

def rc2_oracle_predictability(task_dir: Path) -> dict:
    """Can instruction + file tree predict which files the oracle touches?"""
    oracle = load_oracle(task_dir)
    instruction = load_instruction(task_dir)
    if not oracle or not instruction:
        return {"check": "rc2_oracle_predictability", "severity": "WARN", "detail": "Missing oracle or instruction"}

    targets = oracle_touched_files(oracle)
    if not targets:
        return {"check": "rc2_oracle_predictability", "severity": "WARN", "detail": "Could not detect oracle targets"}

    keywords = extract_keywords(instruction)
    predictable = []; unpredictable = []
    for t in targets:
        rel = re.sub(r'^/app/', '', t)
        pts = set()
        for part in Path(rel).parts:
            stem = Path(part).stem.lower()
            pts.add(stem); pts.update(re.split(r'[_\-.]', stem))
        overlap = keywords & pts
        if overlap:
            predictable.append({"file": rel, "keywords": sorted(overlap)})
        else:
            unpredictable.append(rel)

    total = len(predictable) + len(unpredictable)
    pr = len(predictable) / max(total, 1)

    target_dirs = set()
    for t in targets:
        rel = re.sub(r'^/app/', '', t)
        parts = Path(rel).parts
        if len(parts) >= 2:
            target_dirs.add(parts[0] if len(parts) == 2 else "/".join(parts[:2]))
    dir_kw = set()
    for d in target_dirs:
        dir_kw.update(re.split(r'[_\-/]', d.lower()))
    dir_overlap = keywords & dir_kw

    severity = "FAIL" if pr > 0.7 and dir_overlap else "WARN" if pr > 0.5 or dir_overlap else "PASS"
    return {
        "check": "rc2_oracle_predictability", "severity": severity,
        "predictable_files": len(predictable), "unpredictable_files": len(unpredictable),
        "predict_ratio": round(pr, 2), "target_dirs": sorted(target_dirs),
        "dir_keyword_overlap": sorted(dir_overlap),
        "predictable": predictable[:10], "unpredictable": unpredictable[:10],
        "detail": f"{len(predictable)}/{total} oracle targets predictable from instruction ({pr:.0%}). "
                  f"Dirs: {', '.join(sorted(target_dirs))}. "
                  f"Dir-keyword overlap: {', '.join(sorted(dir_overlap)) or 'none'}",
    }


# ═══════════════════════════════════════════════════════════════════════════
# RC3: Verifier Shallowness
# ═══════════════════════════════════════════════════════════════════════════

def rc3_verifier_shallowness(task_dir: Path) -> dict:
    """Do test assertions validate domain correctness or just format?"""
    test_code = load_tests(task_dir)
    if not test_code:
        return {"check": "rc3_verifier_shallowness", "severity": "WARN", "detail": "No test file"}

    assertions = re.findall(r'assert\s+(.+?)(?:\n|$)', test_code)
    if not assertions:
        return {"check": "rc3_verifier_shallowness", "severity": "WARN", "detail": "No assertions found"}

    fmt = 0; val = 0; struct = 0; exitc = 0
    for a in assertions:
        s = a.strip()
        if re.search(r'isinstance\(|\.is_file\(\)|\.exists\(\)|\.is_dir\(', s):
            fmt += 1
        elif re.search(r'returncode\s*==\s*0', s):
            exitc += 1
        elif re.search(r'[><=]=?\s*\d|math\.|relclose|isclose|abs\(|round\(|fnv|checksum|hash', s):
            val += 1
        elif re.search(r'==\s*\w+\(|==\s*\w+\[|==\s*gold|==\s*expected|==\s*ref|==\s*summary', s):
            val += 1
        elif re.search(r'in\s+[\(\{\[]|\.keys\(\)|set\(.*\)\s*==', s):
            struct += 1
        elif re.search(r'len\(|\.strip\(\)\s*!=\s*""', s):
            struct += 1
        elif re.search(r'is\s+True|is\s+False|is\s+None|==\s*True|==\s*False', s):
            if re.search(r'\[.*\]\s*(?:is|==)', s): val += 1
            else: fmt += 1
        elif '==' in s or '!=' in s:
            val += 1
        elif re.search(r'>\s*0|>=\s*1', s):
            fmt += 1
        else:
            struct += 1

    total = fmt + val + struct + exitc
    shallow = fmt + exitc + struct
    sr = shallow / max(total, 1)
    severity = "FAIL" if (sr > 0.75 and val < 3) else "WARN" if (sr > 0.6 or exitc > total // 3) else "PASS"
    return {
        "check": "rc3_verifier_shallowness", "severity": severity,
        "value_checks": val, "format_checks": fmt, "structure_checks": struct,
        "exitcode_checks": exitc, "total": total, "shallow_ratio": round(sr, 2),
        "detail": f"{val} value, {fmt} format, {struct} structure, {exitc} exit-code ({sr:.0%} shallow)",
    }


# ═══════════════════════════════════════════════════════════════════════════
# RC4: Tamper Surface
# ═══════════════════════════════════════════════════════════════════════════

def rc4_tamper_surface(task_dir: Path) -> dict:
    """Can the agent modify what the tests depend on to bypass domain reasoning?"""
    test_code = load_tests(task_dir)
    if not test_code:
        return {"check": "rc4_tamper_surface", "severity": "WARN", "detail": "No test file"}

    issues = []

    # 1. Agent-editable binaries + exit-code-only
    base_vars = {}
    for m in re.finditer(r'(\w+)\s*=\s*Path\(\s*["\'](/app[^"\']*)["\']', test_code):
        base_vars[m.group(1)] = m.group(2)
    for m in re.finditer(r'(\w+)\s*=\s*(\w+)\s*/\s*["\']([^"\']+)["\']', test_code):
        if m.group(2) in base_vars:
            full = base_vars[m.group(2)].rstrip("/") + "/" + m.group(3)
            base_vars[m.group(1)] = full

    agent_bins = set()
    for v, p in base_vars.items():
        if not p.endswith(('.py','.sh','.json','.txt','.toml','.yaml','.yml')):
            agent_bins.add(p)
    agent_bins.update(
        p for p in re.findall(r'["\'](/app/[a-zA-Z0-9_/.-]+)["\']', test_code)
        if not p.endswith(('.py','.sh','.json','.txt','.toml','.yaml','.yml'))
        and '/app/' in p and '.' not in p.split('/')[-1]  # likely binary
    )

    if agent_bins:
        has_output_val = bool(re.search(r'assert.*(?:stdout|stderr|json\.loads|\.read_text|fnv|checksum|hash)', test_code))
        ec_only = bool(re.search(r'returncode\s*==\s*0', test_code)) and not has_output_val
        if ec_only:
            issues.append({"type": "exit_code_only_binary", "binaries": sorted(agent_bins),
                           "detail": "Tests run agent-editable binaries and only check exit code"})

    # 2. Baseline derived from agent-editable binary
    for m in re.finditer(r'subprocess\.\w+\(\s*\[.*?str\((\w+)\)', test_code):
        var = m.group(1)
        if var in base_vars and not base_vars[var].endswith('.py'):
            issues.append({"type": "editable_baseline", "path": base_vars[var],
                           "detail": f"Gold values derived from agent-editable binary {base_vars[var]}"})

    # 3. Agent-editable test inputs without integrity
    editable_inputs = re.findall(r'Path\(\s*["\'](/app/(?:programs|data|inputs?|fixtures?)[^"\']*)["\']', test_code)
    if editable_inputs and not re.search(r'hash|checksum|digest|hmac|sha|md5', test_code, re.IGNORECASE):
        issues.append({"type": "editable_inputs", "paths": editable_inputs,
                       "detail": f"Tests use {len(editable_inputs)} agent-editable input paths without integrity checks"})

    severity = "FAIL" if any(i["type"] in ("exit_code_only_binary", "editable_baseline") for i in issues) else \
               "WARN" if issues else "PASS"
    return {
        "check": "rc4_tamper_surface", "severity": severity,
        "issue_count": len(issues), "issues": issues[:10],
        "detail": f"{len(issues)} tamper surface(s)" if issues else "No tamper surfaces detected",
    }


# ═══════════════════════════════════════════════════════════════════════════
# RC5: Agent-Visible Reference Artifacts
# ═══════════════════════════════════════════════════════════════════════════

def rc5_reference_artifacts(task_dir: Path) -> dict:
    """Are golden/reference outputs visible to the agent in the environment?"""
    env = task_dir / "environment"
    if not env.is_dir():
        return {"check": "rc5_reference_artifacts", "severity": "PASS", "detail": "No environment dir"}

    issues = []

    # 1. Golden/reference directories or files
    golden_patterns = ["golden", "reference", "expected", "baseline", "ground_truth", "gold"]
    for f in env.rglob("*"):
        if not f.is_file():
            continue
        rel = str(f.relative_to(env)).lower()
        for pat in golden_patterns:
            if pat in rel:
                issues.append({"type": "golden_file", "path": str(f.relative_to(env)),
                               "detail": f"Agent-visible file matching '{pat}' pattern"})
                break

    # 2. Compile-time golden/debug code paths in source
    for f in env.rglob("*"):
        if not f.is_file() or f.suffix.lower() not in (".c", ".cpp", ".cc", ".h", ".hpp", ".rs", ".go", ".java", ".cmake"):
            continue
        if f.name.lower() == "cmakelists.txt" or f.suffix.lower() == ".cmake":
            try:
                content = f.read_text(encoding="utf-8", errors="replace")
                for m in re.finditer(r'option\(\s*(\w*(?:GOLDEN|REFERENCE|DEBUG_DUMP|INTERNAL)\w*)', content, re.IGNORECASE):
                    issues.append({"type": "compile_flag", "path": str(f.relative_to(env)),
                                   "flag": m.group(1),
                                   "detail": f"Compile-time flag '{m.group(1)}' may enable golden/debug mode"})
            except Exception:
                pass
        elif f.suffix.lower() in (".c", ".cpp", ".cc", ".h", ".hpp"):
            try:
                content = f.read_text(encoding="utf-8", errors="replace")
                for m in re.finditer(r'#ifdef\s+(\w*(?:GOLDEN|REFERENCE|DUMP_EXPECTED)\w*)', content, re.IGNORECASE):
                    issues.append({"type": "ifdef_golden", "path": str(f.relative_to(env)),
                                   "flag": m.group(1),
                                   "detail": f"#ifdef '{m.group(1)}' enables agent-visible golden code path"})
            except Exception:
                pass

    severity = "FAIL" if issues else "PASS"
    return {
        "check": "rc5_reference_artifacts", "severity": severity,
        "issue_count": len(issues), "issues": issues[:10],
        "detail": f"{len(issues)} agent-visible reference artifact(s)" if issues else "No reference artifacts found",
    }


# ─── Main ────────────────────────────────────────────────────────────────────

ALL_CHECKS = [rc1_oracle_simplification, rc2_oracle_predictability, rc3_verifier_shallowness, rc4_tamper_surface, rc5_reference_artifacts]

LABELS = {
    "rc1_oracle_simplification": "RC1 Oracle Simplification — does the fix mostly REMOVE code?",
    "rc2_oracle_predictability": "RC2 Oracle Predictability — can instruction + tree predict oracle targets?",
    "rc3_verifier_shallowness":  "RC3 Verifier Shallowness — do tests check format or domain values?",
    "rc4_tamper_surface":        "RC4 Tamper Surface — can the agent modify what tests depend on?",
    "rc5_reference_artifacts":   "RC5 Reference Artifacts — are golden/expected outputs visible to the agent?",
}

def main():
    parser = argparse.ArgumentParser(description="Mechanical collapse checks (root-cause based)")
    parser.add_argument("task_dir", type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    if not args.task_dir.is_dir():
        print(f"ERROR: {args.task_dir} is not a directory", file=sys.stderr); sys.exit(1)

    results = [c(args.task_dir) for c in ALL_CHECKS]
    fails = [r for r in results if r["severity"] == "FAIL"]
    warns = [r for r in results if r["severity"] == "WARN"]

    if args.json:
        print(json.dumps({"results": results, "fails": len(fails), "warns": len(warns)}, indent=2))
    else:
        print(f"\n{'='*70}\n  Collapse Check: {args.task_dir}\n{'='*70}\n")
        for r in results:
            icon = {"PASS":"\u2705","WARN":"\u26a0\ufe0f ","FAIL":"\u274c"}[r["severity"]]
            print(f"  {icon} {r['severity']:4s}  {LABELS.get(r['check'], r['check'])}")
            print(f"         {r['detail']}")
            if r["severity"] != "PASS":
                for key in ("comparisons","predictable","issues"):
                    for item in (r.get(key) or [])[:4]:
                        if isinstance(item, dict):
                            s = item.get("detail") or item.get("file","")
                            e = ""
                            if "keywords" in item: e = f" (keywords: {', '.join(item['keywords'])})"
                            elif "delta" in item: e = f" ({item['delta']:+d} lines)"
                            print(f"           \u2192 {s}{e}")
            print()
        print(f"{'─'*70}\n  RESULT: {len(fails)} FAIL, {len(warns)} WARN, {len(results)-len(fails)-len(warns)} PASS")
        if fails:
            print(f"\n  \u274c VERDICT: FAIL — {len(fails)} root-cause signal(s).\n")
        elif warns:
            print(f"\n  \u26a0\ufe0f  VERDICT: WARN — {len(warns)} signal(s) need justification.\n")
        else:
            print(f"\n  \u2705 VERDICT: PASS\n")

    sys.exit(1 if fails else 2 if warns else 0)

if __name__ == "__main__":
    main()
