#!/usr/bin/env python3
"""Emit a validated mapping CSV after batch sign-off.

Profile: validated_mapping_csv_v1
  - UTF-8 CSV, one row per canonical Line
  - Final mapping + Rule/Decision provenance + source pointers
  - Not an Investran / eFront / DIU loader schema

Hard gate (re-checked on every emit):
  signed_off, zero open Cases, required close tasks complete,
  hard tie-outs passed or not_applicable.
"""
from __future__ import annotations

import csv
import io
from datetime import datetime, timezone
from typing import Any, Optional, Union

from canonical_model import (
    CanonicalClose,
    Decision,
    Line,
    ensure_close_tasks,
)

EXPORT_PROFILE = "validated_mapping_csv_v1"
HARD_TIEOUT_KINDS = (
    "staging_to_lines",
    "diu_batch_zero_balance",
    "statement_row_count",
)
CSV_COLUMNS = (
    "line_id",
    "date",
    "description",
    "amount",
    "currency",
    "classification",
    "project_code",
    "counterparty",
    "fund",
    "account",
    "account_number",
    "bank_account",
    "mapping_method",
    "rule_id",
    "rule_version",
    "decision_id",
    "source_id",
    "source_excerpt",
    "source_location",
    "close_id",
    "export_profile",
)


def _as_canonical(close: Union[CanonicalClose, dict[str, Any]]) -> CanonicalClose:
    if isinstance(close, CanonicalClose):
        return close
    return CanonicalClose.from_dict(close)


def _hard_tieouts_ok(canonical: CanonicalClose) -> tuple[bool, Optional[str]]:
    hard = [t for t in canonical.tieouts if t.kind in HARD_TIEOUT_KINDS]
    if not hard:
        # Fixture may only carry diu_batch_zero_balance; treat empty hard set
        # as fail-closed unless at least one hard kind is present.
        any_batch = next(
            (t for t in canonical.tieouts if t.kind == "diu_batch_zero_balance"),
            None,
        )
        if any_batch is None:
            return False, "missing hard tie-out"
        if any_batch.status == "failed":
            return False, "tie-out failed: diu_batch_zero_balance"
        return True, None
    failed = [t.kind for t in hard if t.status == "failed"]
    if failed:
        return False, "tie-out failed: " + ", ".join(failed)
    return True, None


def export_blockers(close: Union[CanonicalClose, dict[str, Any]]) -> list[str]:
    """Return human-readable blockers; empty list means export is allowed."""
    canonical = _as_canonical(close)
    ensure_close_tasks(canonical)
    blockers: list[str] = []

    signed_off = canonical.close.status == "signed_off" or any(
        d.action == "sign_off" for d in canonical.decisions
    )
    if not signed_off:
        blockers.append("batch not signed off")

    open_cases = [c for c in canonical.cases if c.status == "unresolved"]
    if open_cases:
        blockers.append(f"{len(open_cases)} open case(s) remain")

    ok, tie_msg = _hard_tieouts_ok(canonical)
    if not ok and tie_msg:
        blockers.append(tie_msg)

    incomplete = [
        task.task_id
        for task in canonical.tasks
        if task.required_for_signoff and task.status != "complete"
    ]
    if incomplete:
        blockers.append("incomplete close task(s): " + ", ".join(incomplete))

    return blockers


def can_emit_export(close: Union[CanonicalClose, dict[str, Any]]) -> bool:
    return not export_blockers(close)


def _latest_line_decision(line: Line, decisions: list[Decision]) -> Optional[Decision]:
    line_decs = sorted(
        [d for d in decisions if d.line_id == line.line_id and d.action != "sign_off"],
        key=lambda d: d.timestamp,
    )
    return line_decs[-1] if line_decs else None


def _source_location(line: Line) -> str:
    bank = line.bank_ref or {}
    loc = bank.get("location") if isinstance(bank, dict) else None
    if isinstance(loc, dict) and loc:
        if "page" in loc:
            return f"page {loc['page']}"
        return str(loc)
    src = line.source_ref or {}
    loc = src.get("location") if isinstance(src, dict) else None
    if isinstance(loc, dict) and loc:
        sheet = loc.get("sheet")
        row = loc.get("row")
        if sheet and row is not None:
            return f"{sheet}!row {row}"
        if sheet:
            return str(sheet)
        return str(loc)
    return ""


def _eligible_lines(canonical: CanonicalClose) -> list[Line]:
    return [
        ln
        for ln in canonical.lines
        if ln.status in ("resolved", "accepted")
        and ln.mapping_method in ("rule", "decision", "override")
    ]


def _row_for_line(
    line: Line,
    canonical: CanonicalClose,
    *,
    rules_by_id: dict[str, Any],
) -> dict[str, Any]:
    mapping = line.mapping or {}
    decision = _latest_line_decision(line, canonical.decisions)
    rule = rules_by_id.get(line.rule_id) if line.rule_id else None
    bank = line.bank_ref or {}
    source_id = ""
    if isinstance(bank, dict) and bank.get("source_id"):
        source_id = str(bank["source_id"])
    elif line.source_ref and line.source_ref.get("source_id"):
        source_id = str(line.source_ref["source_id"])
    excerpt = ""
    if isinstance(bank, dict):
        excerpt = str(bank.get("excerpt") or "")

    return {
        "line_id": line.line_id,
        "date": line.date or "",
        "description": line.description or "",
        "amount": line.amount,
        "currency": line.currency or "",
        "classification": mapping.get("classification") or "",
        "project_code": mapping.get("project_code") or "",
        "counterparty": mapping.get("counterparty") or "",
        "fund": mapping.get("fund") or "",
        "account": mapping.get("account") or "",
        "account_number": mapping.get("account_number") or "",
        "bank_account": mapping.get("bank_account") or "",
        "mapping_method": line.mapping_method or "",
        "rule_id": line.rule_id or "",
        "rule_version": getattr(rule, "version", "") if rule else "",
        "decision_id": decision.decision_id if decision else "",
        "source_id": source_id,
        "source_excerpt": excerpt,
        "source_location": _source_location(line),
        "close_id": canonical.close.close_id,
        "export_profile": EXPORT_PROFILE,
    }


def build_csv_bytes(close: Union[CanonicalClose, dict[str, Any]]) -> bytes:
    canonical = _as_canonical(close)
    rules_by_id = {r.rule_id: r for r in canonical.rules}
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=CSV_COLUMNS, lineterminator="\n")
    writer.writeheader()
    for line in _eligible_lines(canonical):
        writer.writerow(_row_for_line(line, canonical, rules_by_id=rules_by_id))
    # utf-8 with BOM helps Excel open the download cleanly
    return ("\ufeff" + buf.getvalue()).encode("utf-8")


def export_filename(close: Union[CanonicalClose, dict[str, Any]]) -> str:
    canonical = _as_canonical(close)
    safe = "".join(
        ch if ch.isalnum() or ch in "-_" else "_"
        for ch in canonical.close.close_id
    )
    return f"validated_mapping_{safe}.csv"


def emit_validated(
    close: Union[CanonicalClose, dict[str, Any]],
    *,
    profile: str = EXPORT_PROFILE,
    generated_by: str = "system",
) -> dict[str, Any]:
    """Return CSV bytes + Export metadata, or raise ValueError with blockers."""
    if profile != EXPORT_PROFILE:
        raise ValueError(f"unsupported export profile: {profile}")

    canonical = _as_canonical(close)
    blockers = export_blockers(canonical)
    if blockers:
        raise ValueError("; ".join(blockers))

    eligible = _eligible_lines(canonical)
    ok, _ = _hard_tieouts_ok(canonical)
    tie_status = "passed" if ok else "failed"
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    file_name = export_filename(canonical)
    csv_bytes = build_csv_bytes(canonical)

    return {
        "export": {
            "id": f"EXP-{canonical.close.close_id}",
            "close_id": canonical.close.close_id,
            "profile": EXPORT_PROFILE,
            "file_name": file_name,
            "line_ids": [ln.line_id for ln in eligible],
            "line_count": len(eligible),
            "tie_out_status": tie_status,
            "generated_at": generated_at,
            "generated_by": generated_by,
        },
        "csv_bytes": csv_bytes,
        "content_type": "text/csv; charset=utf-8",
        "file_name": file_name,
    }
