import json
import shutil
import subprocess
from pathlib import Path

APP = Path("/app")
CASE_ROOT = APP / "captures"
OUT = APP / "output" / "drift_report.json"
BIN = APP / "bin" / "velox_probe"
_BUILT = False

CASE_TEXTS = {
    "c01": """
session no_reload_echo
frames 140
body rook red 0 0 0 0 28 0.500
body pawn blue 5 0 0 0 28 0.500
original
event 60 1 rook push 0.333 0
event 60 2 pawn push -0.111 0
event 110 3 rook strike pawn 2
end
playback
event 60 2 pawn push -0.111 0
event 60 1 rook push 0.333 0
event 110 3 rook strike pawn 2
end
""",
    "c02": """
session twin_push
frames 130
body lane_a red 0 0 0 0 28 0.500
body lane_b blue 5 0 0 0 28 0.500
original
event 55 1 lane_a push 0.180 0
event 90 2 lane_b push -0.140 0
end
playback
event 55 1 lane_a push 0.180 0
event 90 2 lane_b push -0.140 0
end
""",
    "c03": """
session mirror_reload
frames 160
reload 90 mod_x
body east red 0 0 0 0 32 0.600
body west blue 7 0 0 0 32 0.600
original
event 70 1 east push 0.250 0
event 95 2 west push -0.180 0
end
playback
event 70 1 east push 0.250 0
event 95 2 west push -0.180 0
end
""",
    "c04": """
session triple_soft
frames 170
reload 95 mod_d
body one red 0 0 0 0 30 0.500
body two blue 5 0 0 0 30 0.500
body three blue 2 5 0 0 26 0.500
body four red 10 1 0 0 26 0.500
original
event 75 1 one push 0.220 0
event 100 2 two push -0.160 0
event 130 3 three push 0.140 0.090
end
playback
event 75 1 one push 0.220 0
event 100 2 two push -0.160 0
event 130 3 three push 0.140 0.090
end
""",
    "c05": """
session reload_twin
frames 160
reload 90 mod_a
body east red 0 0 0 0 32 0.600
body west blue 7 0 0 0 32 0.600
body north blue 3 4 0 0 24 0.500
original
event 70 1 east push 0.250 0
event 95 2 west push -0.180 0
event 120 3 north push 0.120 0.080
end
playback
event 70 1 east push 0.250 0
event 95 2 west push -0.180 0
event 120 3 north push 0.120 0.080
end
""",
    "c06": """
session reload_press
frames 180
reload 100 mod_b
body helm red 0 0 0 0 30 0.500
body spur blue 4 0 0 0 30 0.500
body arc blue 9 2 0 0 22 0.500
original
event 85 1 helm push 0.400 0
event 105 2 spur push -0.220 0
event 130 3 arc push 0.150 -0.100
end
playback
event 85 1 helm push 0.400 0
event 105 2 spur push -0.220 0
event 130 3 arc push 0.150 -0.100
end
""",
    "c07": """
session late_reload
frames 200
reload 120 mod_c
body kite red 0 0 0 0 35 0.550
body moss blue 8 0 0 0 35 0.550
body reed blue 2 6 0 0 20 0.450
original
event 100 1 kite push 0.300 0
event 125 2 moss push -0.275 0
event 150 3 reed push 0.180 0.120
end
playback
event 100 1 kite push 0.300 0
event 125 2 moss push -0.275 0
event 150 3 reed push 0.180 0.120
end
""",
    "c08": """
session soft_swell
frames 185
reload 88 mod_e
body alpha red 0 0 0 0 30 0.500
body beta blue 4 0 0 0 30 0.500
body gamma blue 2 4 0 0 24 0.500
body delta red 9 1 0 0 24 0.500
original
event 72 1 alpha push 0.180 0
event 98 2 beta push -0.140 0
event 125 3 gamma push 0.110 0.070
event 150 4 delta push -0.090 0.050
end
playback
event 72 1 alpha push 0.180 0
event 98 2 beta push -0.140 0
event 125 3 gamma push 0.110 0.070
event 150 4 delta push -0.090 0.050
end
""",
    "c09": """
session pre_reload_only
frames 150
reload 110 mod_z
body alpha red 0 0 0 0 30 0.500
body beta blue 6 0 0 0 30 0.500
original
event 60 1 alpha push 0.200 0
event 105 2 beta push -0.150 0
end
playback
event 60 1 alpha push 0.200 0
event 105 2 beta push -0.150 0
end
""",
    "c10": """
session shift_after_reload
frames 170
reload 100 mod_y
body helm red 0 0 0 0 30 0.500
body spur blue 4 0 0 0 30 0.500
original
event 85 1 helm push 0.400 0
event 110 2 spur push -0.220 0
end
playback
event 85 1 helm push 0.400 0
event 110 2 spur push -0.320 0
end
""",
    "c11": """
session late_input_mod
frames 195
reload 108 mod_f
body spear red 0 0 0 0 30 0.500
body shield blue 8 0 0 0 30 0.500
original
event 95 1 spear push 0.350 0
event 125 2 shield push -0.200 0
event 155 1 spear push 0.450 0
end
playback
event 95 1 spear push 0.350 0
event 125 2 shield push -0.200 0
event 155 1 spear push 0.750 0
end
""",
    "c12": """
session frac_drift
frames 175
reload 92 mod_g
body amber red 0 0 0 0 28 0.500
body cobalt blue 9 0 0 0 28 0.500
original
event 80 1 amber push 0.200 0
event 118 2 cobalt push -0.450 0
end
playback
event 80 1 amber push 0.200 0
event 118 2 cobalt push -0.750 0
end
""",
    "c13": """
session impact_mod
frames 195
reload 100 mod_h
body blade red 0 0 0 0 30 0.800
body ward blue 2.200 0 0 0 30 0.800
original
event 130 1 blade push 0.100 0
event 162 2 blade strike ward 3
end
playback
event 130 1 blade push 0.100 0
event 162 2 blade strike ward 8
end
""",
    "c14": """
session cross_strike
frames 200
reload 110 mod_i
body glaive red 0 0 0 0 34 0.800
body buckler blue 1.500 0 0 0 34 0.800
body caster blue 3.000 0 0 0 25 0.500
original
event 120 1 glaive push 0.250 0
event 155 2 glaive strike buckler 4
event 170 3 caster push -0.050 0
end
playback
event 120 1 glaive push 0.250 0
event 155 2 glaive strike caster 4
event 170 3 caster push -0.050 0
end
""",
    "c15": """
session scramble_echo
frames 165
reload 87 mod_j
body lance red 0 0 0 0 30 0.500
body helm blue 4 0 0 0 30 0.500
original
event 78 1 lance push 1.500 0
event 78 2 helm push -1.500 0
event 120 3 lance strike helm 4
end
playback
event 78 3 lance strike helm 4
event 78 2 helm push -1.500 0
event 78 1 lance push 1.500 0
end
""",
    "c16": """
session missing_push
frames 205
reload 112 mod_k
body pike red 0 0 0 0 30 0.500
body orb blue 10 0 0 0 30 0.500
original
event 95 1 pike push 0.125 0
event 130 2 orb push -0.450 0
event 175 3 pike strike orb 2
end
playback
event 95 1 pike push 0.125 0
event 175 3 pike strike orb 2
end
""",
    "c17": """
session early_mod
frames 165
reload 55 mod_early
body scout red 0 0 0 0 28 0.500
body flank blue 6 0 0 0 28 0.500
original
event 40 1 scout push 0.220 0
event 90 2 flank push -0.180 0
event 130 1 scout push 0.150 0
end
playback
event 40 1 scout push 0.220 0
event 90 2 flank push -0.180 0
event 130 1 scout push 0.650 0
end
""",
    "c19": """
session guard_drift
frames 185
reload 98 mod_guard
body anvil red 0 0 0 0 18 0.700
body needle blue 2.000 0 0 0 22 0.700
original
event 108 1 anvil guard 0.500 0 0
event 140 2 needle strike anvil 4 0
end
playback
event 108 1 anvil guard 1.250 0 0
event 140 2 needle strike anvil 4 0
end
""",
    "c18": """
session calm_lane
frames 120
body alpha red 0 0 0 0 30 0.500
body beta blue 6 0 0 0 30 0.500
original
event 40 1 alpha push 0.200 0
event 80 2 beta push -0.150 0
end
playback
event 40 1 alpha push 0.200 0
event 80 2 beta push -0.150 0
end
""",
}


def fold_m(text: str) -> int:
    dot = text.find(".")
    whole = text if dot == -1 else text[:dot]
    frac = "" if dot == -1 else text[dot + 1 :]
    if not whole:
        whole = "0"
    while len(frac) < 3:
        frac += "0"
    value = int(whole) * 1000 + int(frac[:3])
    if len(frac) > 3 and frac[3] >= "5":
        value += 1
    return value


def parse_cases() -> dict[str, dict]:
    cases: dict[str, dict] = {}
    for text in CASE_TEXTS.values():
        cap = {
            "id": "",
            "frames": 0,
            "reload_frame": -1,
            "reload_tag": "",
            "units": [],
            "original": [],
            "playback": [],
        }
        section = ""
        for raw in text.splitlines():
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            word = parts[0]
            if word == "session":
                cap["id"] = parts[1]
            elif word == "frames":
                cap["frames"] = int(parts[1])
            elif word == "reload":
                cap["reload_frame"] = int(parts[1])
                cap["reload_tag"] = parts[2]
            elif word == "body":
                cap["units"].append(
                    {
                        "id": parts[1],
                        "team": parts[2],
                        "x": fold_m(parts[3]),
                        "y": fold_m(parts[4]),
                        "vx": fold_m(parts[5]),
                        "vy": fold_m(parts[6]),
                        "hp": fold_m(parts[7]),
                        "radius": fold_m(parts[8]),
                    }
                )
            elif word in ("original", "playback"):
                section = word
            elif word == "end":
                section = ""
            elif word == "event":
                cap[section].append(
                    {
                        "frame": int(parts[1]),
                        "seq": int(parts[2]),
                        "unit": parts[3],
                        "op": parts[4],
                        "a": parts[5],
                        "b": parts[6],
                        "c": parts[7] if len(parts) > 7 else "",
                    }
                )
        cases[cap["id"]] = cap
    return cases


def fold_a(events: list[dict]) -> list[dict]:
    return sorted(
        events,
        key=lambda e: (e["frame"], e["seq"], e["unit"], e["op"], e["a"], e["b"], e["c"]),
    )


def fold_b(values: list[float]) -> float:
    if not values:
        return 0.0
    acc = values[0]
    for v in values[1:]:
        acc += v
    return acc


def fold_d(world: dict[str, dict]) -> str:
    chunks = []
    for uid in sorted(world):
        u = world[uid]
        hp = max(u["hp"], 0)
        chunks.append(
            f"{uid}:{u['team']}:{u['x']},{u['y']}:{u['vx']},{u['vy']}:{hp}"
        )
    return "|".join(chunks)


def step_c(units: list[dict], events: list[dict], frames: int, reload_frame: int) -> dict:
    world = {u["id"]: dict(u) for u in units}
    snapshots = []
    for frame in range(1, frames + 1):
        for e in events:
            if e["frame"] != frame:
                continue
            u = world.get(e["unit"])
            if not u or u["hp"] <= 0:
                continue
            if e["op"] == "push":
                u["vx"] += fold_m(e["a"])
                u["vy"] += fold_m(e["b"])
            elif e["op"] == "guard":
                u["hp"] += fold_m(e["a"])
            elif e["op"] == "strike":
                tgt = world.get(e["a"])
                if not tgt or tgt["hp"] <= 0:
                    continue
                dx = u["x"] - tgt["x"]
                dy = u["y"] - tgt["y"]
                r = u["radius"] + tgt["radius"] + 1500
                if dx * dx + dy * dy <= r * r:
                    tgt["hp"] -= fold_m(e["b"])
                    if tgt["hp"] < 0:
                        tgt["hp"] = 0

        ids = sorted(world)
        for uid in ids:
            u = world[uid]
            if u["hp"] <= 0:
                continue
            parts = []
            for oid in ids:
                if oid == uid:
                    continue
                o = world[oid]
                if o["hp"] <= 0:
                    continue
                dx = float(o["x"] - u["x"])
                dy = float(o["y"] - u["y"])
                dist = (dx * dx + dy * dy) ** 0.5 + 1.0
                parts.append((dx / dist) * 0.001 + (dy / dist) * 0.0007)
            impulse = fold_b(parts)
            u["vx"] += int(impulse * 1000.0)
            u["vy"] += int(impulse * 500.0)

        for uid in ids:
            u = world[uid]
            if u["hp"] > 0:
                u["x"] += u["vx"]
                u["y"] += u["vy"]

        for i, a_id in enumerate(ids):
            for b_id in ids[i + 1 :]:
                a = world[a_id]
                b = world[b_id]
                if a["hp"] <= 0 or b["hp"] <= 0 or a["team"] == b["team"]:
                    continue
                dx = a["x"] - b["x"]
                dy = a["y"] - b["y"]
                r = a["radius"] + b["radius"]
                if dx * dx + dy * dy <= r * r:
                    a["hp"] -= 1000
                    b["hp"] -= 1000
                    a["vx"] = a["vy"] = 0
                    b["vx"] = b["vy"] = 0
                    if a["hp"] < 0:
                        a["hp"] = 0
                    if b["hp"] < 0:
                        b["hp"] = 0

        snapshots.append({"frame": frame, "digest": fold_d(world)})

    final = snapshots[-1]["digest"] if snapshots else fold_d(world)
    return {"final_digest": final, "snapshots": snapshots}


def sig(e: dict) -> str:
    return f"{e['unit']}:{e['op']}:{e['a']}:{e['b']}:{e['c']}"


def classify(a: list[dict], b: list[dict], frame: int) -> tuple[str, str]:
    left: dict[str, str] = {}
    right: dict[str, str] = {}
    for e in a:
        if e["frame"] == frame:
            left.setdefault(e["unit"], "")
            left[e["unit"]] += sig(e) + ";"
    for e in b:
        if e["frame"] == frame:
            right.setdefault(e["unit"], "")
            right[e["unit"]] += sig(e) + ";"
    for unit, text in left.items():
        if right.get(unit) != text:
            reason = "impact" if ":strike:" in text else "input"
            return reason, unit
    for unit, text in right.items():
        if left.get(unit) != text:
            reason = "impact" if ":strike:" in text else "input"
            return reason, unit
    return "state", ""


def streams_identical(cap: dict) -> bool:
    a = fold_a(cap["original"])
    b = fold_a(cap["playback"])
    if len(a) != len(b):
        return False
    for left, right in zip(a, b):
        if (
            left["frame"] != right["frame"]
            or left["seq"] != right["seq"]
            or left["unit"] != right["unit"]
            or left["op"] != right["op"]
            or left["a"] != right["a"]
            or left["b"] != right["b"]
            or left["c"] != right["c"]
        ):
            return False
    return True


def expected_rows() -> dict[str, dict]:
    rows: dict[str, dict] = {}
    for cap in parse_cases().values():
        a = fold_a(cap["original"])
        b = fold_a(cap["playback"])
        left = step_c(cap["units"], a, cap["frames"], cap["reload_frame"])
        right = step_c(cap["units"], b, cap["frames"], cap["reload_frame"])
        first = -1
        for ls, rs in zip(left["snapshots"], right["snapshots"]):
            if ls["digest"] != rs["digest"]:
                first = ls["frame"]
                break
        if first < 0:
            row = {
                "id": cap["id"],
                "status": "stable",
                "first_bad_frame": None,
                "reason": "none",
                "source": "",
                "original_digest": left["final_digest"],
                "replay_digest": right["final_digest"],
                "frames": cap["frames"],
            }
        else:
            reason, source = classify(a, b, first)
            row = {
                "id": cap["id"],
                "status": "drifted",
                "first_bad_frame": first,
                "reason": reason,
                "source": source,
                "original_digest": left["final_digest"],
                "replay_digest": right["final_digest"],
                "frames": cap["frames"],
            }
        rows[cap["id"]] = row
    return rows


def reload_identical_stable_ids() -> list[str]:
    return [
        cap_id
        for cap_id, cap in parse_cases().items()
        if cap["reload_frame"] >= 0 and streams_identical(cap)
    ]


def build_probe() -> None:
    global _BUILT
    if _BUILT:
        return
    subprocess.run(
        ["cmake", "-S", APP.as_posix(), "-B", (APP / "build").as_posix()],
        check=True,
        cwd=APP,
    )
    subprocess.run(
        [
            "cmake",
            "--build",
            (APP / "build").as_posix(),
            "--target",
            "velox_probe",
            "--parallel",
            "2",
        ],
        check=True,
        cwd=APP,
    )
    _BUILT = True


def run_report() -> dict:
    build_probe()
    if CASE_ROOT.exists():
        shutil.rmtree(CASE_ROOT)
    CASE_ROOT.mkdir(parents=True)
    for name, text in CASE_TEXTS.items():
        (CASE_ROOT / f"{name}.vcap").write_text(text.strip() + "\n", encoding="utf-8")
    subprocess.run([BIN.as_posix(), CASE_ROOT.as_posix(), OUT.as_posix()], check=True, cwd=APP)
    raw = OUT.read_text(encoding="utf-8")
    assert raw.endswith("\n")
    assert raw.count("\n") == 1
    return json.loads(raw.strip())


def rows_by_id(report: dict) -> dict[str, dict]:
    return {row["id"]: row for row in report["sessions"]}


def test_alpha_contract():
    """Report envelope, exact summary counts, sorted ids, and complete row keys."""
    report = run_report()
    expected = expected_rows()
    rows = report["sessions"]
    assert [row["id"] for row in rows] == sorted(expected)
    assert report["summary"] == {
        "checked": len(expected),
        "stable": sum(row["status"] == "stable" for row in expected.values()),
        "drifted": sum(row["status"] == "drifted" for row in expected.values()),
    }
    for row in rows:
        assert set(row) == {
            "id",
            "status",
            "first_bad_frame",
            "reason",
            "source",
            "original_digest",
            "replay_digest",
            "frames",
        }


def test_beta_stable_corpus():
    """Stable captures stay stable with matching digests across the full corpus."""
    report = rows_by_id(run_report())
    expected = expected_rows()
    stable_ids = [
        cap_id
        for cap_id, row in expected.items()
        if row["status"] == "stable"
    ]
    assert len(stable_ids) >= 10
    for cap_id in stable_ids:
        assert report[cap_id] == expected[cap_id]
        assert report[cap_id]["original_digest"] == report[cap_id]["replay_digest"]


def test_gamma_reload_identical_stable():
    """Identical streams across a script boundary must remain stable end-to-end."""
    report = rows_by_id(run_report())
    expected = expected_rows()
    targets = reload_identical_stable_ids()
    assert len(targets) >= 7
    for cap_id in targets:
        assert report[cap_id] == expected[cap_id]
        assert report[cap_id]["status"] == "stable"
        assert report[cap_id]["first_bad_frame"] is None


def test_delta_input_drift():
    """Input-value drift rows match the reference model exactly."""
    report = rows_by_id(run_report())
    expected = expected_rows()
    targets = [cap_id for cap_id, row in expected.items() if row["reason"] == "input"]
    assert len(targets) >= 4
    for cap_id in targets:
        assert report[cap_id] == expected[cap_id]
        cap = parse_cases()[cap_id]
        assert report[cap_id]["first_bad_frame"] > cap["reload_frame"]


def test_epsilon_extended_drift():
    """Every drifted session in the corpus matches the reference model."""
    report = rows_by_id(run_report())
    expected = expected_rows()
    targets = [cap_id for cap_id, row in expected.items() if row["status"] == "drifted"]
    assert len(targets) >= 5
    for cap_id in targets:
        assert report[cap_id] == expected[cap_id]
        cap = parse_cases()[cap_id]
        assert report[cap_id]["first_bad_frame"] > cap["reload_frame"]


def test_zeta_late_mismatch_frames():
    """Drifted sessions mismatch only on late frames, not in the opening segment."""
    report = rows_by_id(run_report())
    expected = expected_rows()
    drift_reasons: set[str] = set()
    for cap_id, row in expected.items():
        if row["status"] != "drifted":
            continue
        drift_reasons.add(row["reason"])
        cap = parse_cases()[cap_id]
        got = report[cap_id]
        assert got["first_bad_frame"] == row["first_bad_frame"]
        assert got["first_bad_frame"] > 85
        if cap["reload_frame"] >= 0:
            assert got["first_bad_frame"] > cap["reload_frame"]
        assert got["original_digest"] != got["replay_digest"]
    assert "input" in drift_reasons
    assert drift_reasons & {"input", "impact", "state"}


def test_theta_full_corpus_parity():
    """Every session row matches the independent reference model."""
    report = rows_by_id(run_report())
    expected = expected_rows()
    assert set(report) == set(expected)
    for cap_id, exp in expected.items():
        assert report[cap_id] == exp
