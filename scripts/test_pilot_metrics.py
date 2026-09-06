#!/usr/bin/env python3
"""Pilot metrics are derived from the record, never estimated.

Uses an in-memory copy of the public fixture — never mutates demo data.
"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from canonical_model import CanonicalClose, record_batch_sign_off, record_decision  # noqa: E402
from pilot_metrics import compute_pilot_metrics  # noqa: E402

FIXTURE = ROOT / "fixtures" / "sample-close.json"


def _load() -> CanonicalClose:
    return CanonicalClose.from_dict(copy.deepcopy(json.loads(FIXTURE.read_text(encoding="utf-8"))))


def test_open_close_reports_nulls_not_guesses() -> None:
    m = compute_pilot_metrics(_load(), run_kind="unknown")
    assert m["hours_per_close"]["value"] is None
    assert m["error_rate"]["value"] is None
    assert m["sign_off"] is None
    assert m["exception_rate"]["value"] == round(m["volume"]["cases_opened"] / m["volume"]["lines"], 4)
    assert m["volume"]["cases_open"] >= 1


def test_reject_then_accept_counts_as_two_rounds_and_no_override() -> None:
    c = _load()
    base = compute_pilot_metrics(c, run_kind="unknown")
    case = next(x for x in c.cases if x.status == "unresolved")
    line = next(ln for ln in c.lines if ln.line_id == case.line_id)
    record_decision(c, case_id=case.case_id, action="reject", decided_by="A", role="fund_admin",
                    reason="Need the statement page first.", final_value={}, timestamp="2026-09-06T09:00:00Z")
    record_decision(c, case_id=case.case_id, action="accept", decided_by="A", role="fund_admin",
                    reason="Confirmed against the statement.", final_value=dict(line.mapping or {"classification": "Review"}),
                    timestamp="2026-09-06T10:00:00Z")
    m = compute_pilot_metrics(c, run_kind="human")
    assert m["review_rounds"]["max"] >= 2
    assert m["review_rounds"]["cases_with_more_than_one_round"] == base["review_rounds"]["cases_with_more_than_one_round"] + 1
    assert m["override_rate"]["overrides"] == base["override_rate"]["overrides"]
    assert m["override_rate"]["rejects"] == base["override_rate"]["rejects"] + 1
    assert m["volume"]["cases_decided"] == base["volume"]["cases_decided"] + 1


def test_override_flags_rule_health_and_hours_after_sign_off() -> None:
    c = _load()
    base = compute_pilot_metrics(c, run_kind="unknown")
    first = None
    for case in [x for x in c.cases if x.status == "unresolved"]:
        line = next(ln for ln in c.lines if ln.line_id == case.line_id)
        d = record_decision(c, case_id=case.case_id, action="accept", decided_by="A", role="fund_admin",
                            reason="Accept filed treatment for the test.", final_value=dict(line.mapping or {"classification": "Review"}),
                            timestamp="2026-09-06T09:00:00Z")
        first = first or (case, d)
    assert first is not None
    case, d = first
    record_decision(c, case_id=case.case_id, action="override", decided_by="M", role="fund_manager",
                    reason="Reclassify after manager review.", final_value={"classification": "Related Party"},
                    supersedes=d.decision_id, timestamp="2026-09-06T11:00:00Z")
    record_batch_sign_off(c, decided_by="M", role="fund_manager", reason="Test sign-off.", timestamp="2026-09-06T12:00:00Z")
    m = compute_pilot_metrics(c, run_kind="human")
    assert m["close_status"] == "signed_off"
    # Fixture decisions may predate ours; the window still ends at our sign-off.
    assert m["hours_per_close"]["value"] is not None and m["hours_per_close"]["value"] >= 3.0, m["hours_per_close"]
    assert m["hours_per_close"]["signed_off_at"].startswith("2026-09-06T12:00:00")
    assert m["override_rate"]["overrides"] == base["override_rate"]["overrides"] + 1
    assert m["override_rate"]["value"] == round(m["override_rate"]["overrides"] / m["volume"]["cases_decided"], 4)
    assert m["volume"]["cases_open"] == 0
    assert m["tie_out"]["all_passed"] is True
    assert m["sign_off"]["role"] == "fund_manager"


def main() -> None:
    tests = [
        test_open_close_reports_nulls_not_guesses,
        test_reject_then_accept_counts_as_two_rounds_and_no_override,
        test_override_flags_rule_health_and_hours_after_sign_off,
    ]
    for fn in tests:
        fn()
        print(f"OK: {fn.__name__}")
    print(f"OK: {len(tests)} pilot metrics tests passed")


if __name__ == "__main__":
    main()
