"""Milestone 1 — EAD parse (nested names, date spans, CSV layout)."""

import csv
import json
import subprocess
from pathlib import Path

JSONL = Path("/app/var/records.jsonl")
CSV = Path("/app/var/records.csv")
BATCH = "ARC-2024-Q2"


def _run_parse() -> None:
    subprocess.run(["/app/bin/arcctl", "parse", BATCH], check=True, capture_output=True)


class TestMilestone1:
    def test_m1_jsonl_exists_three_records(self) -> None:
        """JSONL holds one object per finding aid in ARC-2024-Q2."""
        _run_parse()
        lines = [ln for ln in JSONL.read_text(encoding="utf-8").splitlines() if ln.strip()]
        assert len(lines) == 3

    def test_m1_ua_date_span_century(self) -> None:
        """UA-0012 unitdate span keeps century digits."""
        _run_parse()
        rows = [json.loads(ln) for ln in JSONL.read_text(encoding="utf-8").splitlines() if ln.strip()]
        ua = next(r for r in rows if r["collection_id"] == "UA.12.003")
        assert ua["date_span"] == "1950-1975"

    def test_m1_ua_nested_persname_present(self) -> None:
        """UA-0012 retains John Smith from controlaccess."""
        _run_parse()
        rows = [json.loads(ln) for ln in JSONL.read_text(encoding="utf-8").splitlines() if ln.strip()]
        ua = next(r for r in rows if r["collection_id"] == "UA.12.003")
        names = {c["name"] for c in ua["creators"]}
        assert "John Smith" in names

    def test_m1_csv_header_layout(self) -> None:
        """CSV header matches csv_layout column order."""
        _run_parse()
        header = CSV.read_text(encoding="utf-8").splitlines()[0]
        assert header == "collection_id,title,date_span,creator_primary,subject_headings,place_names"

    def test_m1_csv_first_column_collection_id(self) -> None:
        """First CSV data column is collection_id for UA-0012 row."""
        _run_parse()
        with CSV.open(encoding="utf-8") as fh:
            rows = list(csv.reader(fh))
        ua_row = next(r for r in rows[1:] if "UA.12.003" in r)
        assert ua_row[0] == "UA.12.003"

    def test_m1_ms_collection_id(self) -> None:
        """MS-0456 collection id preserved in JSONL."""
        _run_parse()
        rows = [json.loads(ln) for ln in JSONL.read_text(encoding="utf-8").splitlines() if ln.strip()]
        ms = next(r for r in rows if r["collection_id"] == "MS-0456")
        assert ms["title"] == "Edith Wilson Papers"

    def test_m1_ph_collection_id(self) -> None:
        """PH.0789 collection id preserved in JSONL."""
        _run_parse()
        rows = [json.loads(ln) for ln in JSONL.read_text(encoding="utf-8").splitlines() if ln.strip()]
        ph = next(r for r in rows if r["collection_id"] == "PH.0789")
        assert ph["title"] == "Bentley Library Photo Series"

    def test_m1_ms_date_span(self) -> None:
        """MS-0456 date span keeps century digits."""
        _run_parse()
        rows = [json.loads(ln) for ln in JSONL.read_text(encoding="utf-8").splitlines() if ln.strip()]
        ms = next(r for r in rows if r["collection_id"] == "MS-0456")
        assert ms["date_span"] == "1880-1895"

    def test_m1_ph_date_span(self) -> None:
        """PH.0789 date span keeps century digits."""
        _run_parse()
        rows = [json.loads(ln) for ln in JSONL.read_text(encoding="utf-8").splitlines() if ln.strip()]
        ph = next(r for r in rows if r["collection_id"] == "PH.0789")
        assert ph["date_span"] == "1920-1930"

    def test_m1_ua_jsonl_dual_creators_corp_before_pers(self) -> None:
        """UA-0012 JSONL creators preserve corp then pers with typed entries."""
        _run_parse()
        rows = [json.loads(ln) for ln in JSONL.read_text(encoding="utf-8").splitlines() if ln.strip()]
        ua = next(r for r in rows if r["collection_id"] == "UA.12.003")
        creators = ua["creators"]
        assert len(creators) == 2
        assert creators[0] == {"type": "corp", "name": "University Archives"}
        assert creators[1] == {"type": "pers", "name": "John Smith"}

    def test_m1_ua_csv_title_second_column(self) -> None:
        """UA-0012 CSV keeps title in the second column after collection_id."""
        _run_parse()
        with CSV.open(encoding="utf-8") as fh:
            rows = list(csv.reader(fh))
        ua_row = next(r for r in rows[1:] if r[0] == "UA.12.003")
        assert ua_row[1] == "Campus Views Photograph Collection"
        assert ua_row[2] == "1950-1975"
