#!/usr/bin/env python3
"""Validated export gate + CSV contract tests.

Uses in-memory copies of the public fixture — never mutates demo data.
"""
from __future__ import annotations

import copy
import csv
import io
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "app"))

from adapt_close import adapt_close_for_reviewer  # noqa: E402
from canonical_model import CanonicalClose, record_batch_sign_off, record_decision  # noqa: E402
from emit_export import (  # noqa: E402
    CSV_COLUMNS,
    EXPORT_PROFILE,
    can_emit_export,
    emit_validated,
    export_blockers,
    export_filename,
)

FIXTURE = ROOT / "fixtures" / "sample-close.json"


def _load_raw() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def _resolve_open_and_sign_off(raw: dict) -> CanonicalClose:
    """Make a close export-ready without touching disk."""
    canonical = CanonicalClose.from_dict(copy.deepcopy(raw))
    open_cases = [c for c in canonical.cases if c.status == "unresolved"]
    for case in open_cases:
        line = next(ln for ln in canonical.lines if ln.line_id == case.line_id)
        record_decision(
            canonical,
            case_id=case.case_id,
            action="accept",
            decided_by="T. Tester",
            role="fund_admin",
            reason="Fixture resolve for export test.",
            final_value=dict(line.mapping or {"classification": "Review"}),
            timestamp="2026-09-06T12:00:00Z",
        )
    record_batch_sign_off(
        canonical,
        decided_by="T. Tester",
        role="fund_admin",
        reason="All cases resolved; tie-out PASS.",
        timestamp="2026-09-06T12:01:00Z",
    )
    return canonical


def test_not_signed_off_blocked() -> None:
    raw = _load_raw()
    blockers = export_blockers(raw)
    assert "batch not signed off" in blockers, blockers
    assert not can_emit_export(raw)


def test_open_case_blocked() -> None:
    raw = _load_raw()
    # Force signed_off while leaving the open case — should still block.
    raw["close"]["status"] = "signed_off"
    raw["decisions"].append(
        {
            "decision_id": "DEC-SIGNOFF",
            "action": "sign_off",
            "previous_value": {"close_status": "in_review"},
            "final_value": {"close_status": "signed_off"},
            "decided_by": "T",
            "role": "fund_admin",
            "reason": "forced",
            "timestamp": "2026-09-06T12:00:00Z",
            "case_id": None,
            "line_id": None,
            "candidates": [],
            "chosen": None,
        }
    )
    blockers = export_blockers(raw)
    assert any("open case" in b for b in blockers), blockers
    assert not can_emit_export(raw)


def test_tieout_failed_blocked() -> None:
    canonical = _resolve_open_and_sign_off(_load_raw())
    for tie in canonical.tieouts:
        if tie.kind == "diu_batch_zero_balance":
            tie.status = "failed"
            tie.difference = 1.0
    blockers = export_blockers(canonical)
    assert any("tie-out failed" in b for b in blockers), blockers
    assert not can_emit_export(canonical)


def test_successful_export_shape() -> None:
    canonical = _resolve_open_and_sign_off(_load_raw())
    assert can_emit_export(canonical)
    result = emit_validated(canonical, generated_by="test")
    assert result["export"]["profile"] == EXPORT_PROFILE
    assert result["file_name"] == export_filename(canonical)
    assert result["file_name"].startswith("validated_mapping_")
    assert result["file_name"].endswith(".csv")
    assert result["export"]["line_count"] == len(result["export"]["line_ids"])
    assert result["export"]["line_count"] >= 1

    text = result["csv_bytes"].decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))
    assert reader.fieldnames == list(CSV_COLUMNS)
    rows = list(reader)
    assert len(rows) == result["export"]["line_count"]
    for row in rows:
        assert row["export_profile"] == EXPORT_PROFILE
        assert row["close_id"] == canonical.close.close_id
        assert row["mapping_method"] in ("rule", "decision", "override")
        assert row["line_id"]


def test_csv_escaping() -> None:
    canonical = _resolve_open_and_sign_off(_load_raw())
    line = canonical.lines[0]
    line.description = 'ACME, "SPECIAL" FEE\nLINE'
    result = emit_validated(canonical)
    text = result["csv_bytes"].decode("utf-8-sig")
    rows = list(csv.DictReader(io.StringIO(text)))
    match = next(r for r in rows if r["line_id"] == line.line_id)
    assert match["description"] == 'ACME, "SPECIAL" FEE\nLINE'


def test_adapt_overview_export_flags() -> None:
    raw = _load_raw()
    ov = adapt_close_for_reviewer(raw)["overview"]
    assert ov["export_ready"] is False
    assert ov["export_profile"] == EXPORT_PROFILE
    assert "batch not signed off" in ov["export_blockers"]

    ready = _resolve_open_and_sign_off(raw)
    ov2 = adapt_close_for_reviewer(ready.to_dict())["overview"]
    assert ov2["signed_off"] is True
    assert ov2["export_ready"] is True
    assert ov2["export_blockers"] == []


def test_unsupported_profile() -> None:
    canonical = _resolve_open_and_sign_off(_load_raw())
    try:
        emit_validated(canonical, profile="investran_loader")
        raise AssertionError("expected ValueError")
    except ValueError as exc:
        assert "unsupported" in str(exc)


def main() -> None:
    tests = [
        test_not_signed_off_blocked,
        test_open_case_blocked,
        test_tieout_failed_blocked,
        test_successful_export_shape,
        test_csv_escaping,
        test_adapt_overview_export_flags,
        test_unsupported_profile,
    ]
    for fn in tests:
        fn()
        print(f"OK: {fn.__name__}")
    print(f"OK: {len(tests)} export tests passed")


if __name__ == "__main__":
    main()
