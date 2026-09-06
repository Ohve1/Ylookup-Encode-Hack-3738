#!/usr/bin/env python3
"""Decision replay tests: Accept, Reject, Override, Reject→Accept.

Override is never inferred from event count alone.
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from canonical_model import (  # noqa: E402
    CanonicalClose,
    Case,
    Close,
    Decision,
    Line,
    Rule,
    Source,
    TieOut,
    ValidationError,
    derive_line_origin,
    record_decision,
)


def _minimal_close() -> CanonicalClose:
    return CanonicalClose(
        close=Close("CLOSE-TEST", "FUND", "2026-03", "bank_to_journal", "in_review", "v1"),
        sources=[
            Source("SRC-1", "stmt.pdf", "pdf", "bank_statement", {"page": 1}, "ACME LTD PAYMENT"),
        ],
        lines=[
            Line(
                line_id="L-001",
                close_id="CLOSE-TEST",
                date="2026-03-31",
                description="ACME LTD PAYMENT",
                amount=-100.0,
                currency="EUR",
                source_ref={"source_id": "SRC-1"},
                status="unresolved",
                raw_facts={"narrative": "ACME LTD PAYMENT", "amount": -100.0},
                filed_snapshot={"classification": "Vendor"},
                mapping={"classification": "Vendor"},
                case_id="CASE-001",
                bank_ref={
                    "source_id": "SRC-1",
                    "match_method": "exact",
                    "excerpt": "ACME LTD PAYMENT",
                },
                mapping_method=None,
            )
        ],
        rules=[
            Rule(
                "RULE-001",
                "Vendor family",
                {"field": "counterparty_family", "operator": "equals", "value": "vendor"},
                {"classification": "Vendor"},
                "vendor_master",
                "active",
                "v1",
                "mapping",
            )
        ],
        cases=[
            Case(
                case_id="CASE-001",
                line_id="L-001",
                reasons=["counterparty_miss"],
                primary_reason="counterparty_miss",
                status="unresolved",
                priority="medium",
                source_flags=["counterparty_miss"],
            )
        ],
        decisions=[],
        tieouts=[
            TieOut(
                "TIE-001",
                "CLOSE-TEST",
                0.0,
                0.0,
                0.0,
                "passed",
                kind="diu_batch_zero_balance",
            )
        ],
    )


def test_accept_sets_decision() -> None:
    c = _minimal_close()
    with tempfile.TemporaryDirectory() as tmp:
        journal = Path(tmp) / "decisions.jsonl"
        d = record_decision(
            c,
            case_id="CASE-001",
            action="accept",
            decided_by="Admin",
            role="fund_admin",
            reason="Matches vendor treatment.",
            final_value={"classification": "Vendor", "account": "43000.1"},
            journal_path=journal,
        )
        assert d.action == "accept"
        assert c.lines[0].mapping_method == "decision"
        assert c.cases[0].status == "decided"
        assert derive_line_origin(c.lines[0], c.cases[0], c.decisions) == "decision"
        assert journal.read_text(encoding="utf-8").strip()
        assert json.loads(journal.read_text(encoding="utf-8").splitlines()[0])["action"] == "accept"


def test_reject_stays_unresolved() -> None:
    c = _minimal_close()
    record_decision(
        c,
        case_id="CASE-001",
        action="reject",
        decided_by="Admin",
        role="fund_admin",
        reason="Need more evidence.",
        final_value={},
    )
    assert c.cases[0].status == "unresolved"
    assert c.lines[0].mapping_method is None
    assert derive_line_origin(c.lines[0], c.cases[0], c.decisions) == "unresolved"


def test_reject_then_accept_is_decision_not_override() -> None:
    c = _minimal_close()
    record_decision(
        c,
        case_id="CASE-001",
        action="reject",
        decided_by="Admin",
        role="fund_admin",
        reason="Need more evidence.",
        final_value={},
        timestamp="2026-09-06T10:00:00Z",
    )
    record_decision(
        c,
        case_id="CASE-001",
        action="accept",
        decided_by="Admin",
        role="fund_admin",
        reason="Now confirmed as Vendor.",
        final_value={"classification": "Vendor"},
        timestamp="2026-09-06T11:00:00Z",
    )
    assert len(c.decisions) == 2
    assert derive_line_origin(c.lines[0], c.cases[0], c.decisions) == "decision"
    assert c.lines[0].mapping_method == "decision"


def test_override_requires_supersedes() -> None:
    c = _minimal_close()
    first = record_decision(
        c,
        case_id="CASE-001",
        action="accept",
        decided_by="Admin",
        role="fund_admin",
        reason="Initial accept.",
        final_value={"classification": "Vendor"},
        timestamp="2026-09-06T10:00:00Z",
    )
    second = record_decision(
        c,
        case_id="CASE-001",
        action="override",
        decided_by="Manager",
        role="fund_manager",
        reason="Reclass to Related Party.",
        final_value={"classification": "Related Party"},
        supersedes=first.decision_id,
        timestamp="2026-09-06T12:00:00Z",
    )
    assert second.supersedes == first.decision_id
    assert c.lines[0].mapping_method == "override"
    assert derive_line_origin(c.lines[0], c.cases[0], c.decisions) == "override"

    # Bare override without prior accept must fail.
    c2 = _minimal_close()
    try:
        record_decision(
            c2,
            case_id="CASE-001",
            action="override",
            decided_by="Manager",
            role="fund_manager",
            reason="No prior.",
            final_value={"classification": "Other"},
        )
        raise AssertionError("expected ValidationError")
    except ValidationError:
        pass


def main() -> None:
    test_accept_sets_decision()
    test_reject_stays_unresolved()
    test_reject_then_accept_is_decision_not_override()
    test_override_requires_supersedes()
    print("OK: decision replay tests passed")


if __name__ == "__main__":
    main()
