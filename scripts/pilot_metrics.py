#!/usr/bin/env python3
"""Pilot instrumentation (roadmap VALIDATE) computed from the close record only.

Every number here is derived from Lines / Cases / Decisions / TieOuts already
in the canonical close and its append-only journal. Nothing is estimated.

  hours_per_close     first Case opened (or first Decision) → sign-off, wall clock
  review_rounds       Decisions per decided Case (reject → re-decide cycles)
  exception_rate      Cases / Lines
  override_rate       Overrides / decided Cases, plus per-Rule override rate
  error_rate          after validated export is loaded — not measurable here
  rule_health         override rate on Rule-mapped Lines → potentially stale

Fields the record cannot support are reported as null with a reason, never
as a guess. `run.kind` says whether the Decisions came from people or a
scripted replay; scripted timings are not evidence of cycle time.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from canonical_model import CanonicalClose  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
STALE_OVERRIDE_RATE = 0.25  # ≥ 25% of a Rule's lines overridden → flag the Rule, not the person
METRICS_VERSION = "pilot_metrics_v1"


def _parse_ts(ts: Optional[str]) -> Optional[datetime]:
    if not ts:
        return None
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except ValueError:
        return None


def _rate(num: int, den: int) -> Optional[float]:
    return round(num / den, 4) if den else None


def compute_pilot_metrics(
    canonical: CanonicalClose,
    *,
    run_kind: str = "unknown",
    run_note: Optional[str] = None,
    journal_path: Optional[Path] = None,
) -> dict[str, Any]:
    lines = canonical.lines
    cases = canonical.cases
    decisions = sorted(canonical.decisions, key=lambda d: d.timestamp or "")
    line_by_id = {ln.line_id: ln for ln in lines}
    case_by_id = {c.case_id: c for c in cases}

    case_decisions = [d for d in decisions if d.action != "sign_off"]
    sign_off = next((d for d in decisions if d.action == "sign_off"), None)
    actions = Counter(d.action for d in case_decisions)
    by_role = Counter(d.role for d in case_decisions)
    by_person = Counter(d.decided_by for d in case_decisions)

    decided_cases = [c for c in cases if c.status == "decided"]
    open_cases = [c for c in cases if c.status == "unresolved"]
    decisions_per_case: dict[str, int] = Counter(d.case_id for d in case_decisions if d.case_id)
    rounds = list(decisions_per_case.values())
    multi_round_cases = sum(1 for n in rounds if n > 1)

    # Per-reason: how many Cases, how many decided, by which action.
    per_reason: dict[str, dict[str, Any]] = {}
    for c in cases:
        slot = per_reason.setdefault(
            c.primary_reason, {"cases": 0, "decided": 0, "accept": 0, "override": 0, "reject": 0}
        )
        slot["cases"] += 1
        if c.status == "decided":
            slot["decided"] += 1
    for d in case_decisions:
        c = case_by_id.get(d.case_id or "")
        if c and d.action in ("accept", "override", "reject"):
            per_reason[c.primary_reason][d.action] += 1

    # Rule health: lines that a Rule mapped (or partially hit) and were later overridden.
    rule_lines: dict[str, set[str]] = defaultdict(set)
    rule_overrides: dict[str, set[str]] = defaultdict(set)
    for ln in lines:
        if ln.rule_id:
            rule_lines[ln.rule_id].add(ln.line_id)
        elif ln.case_id and case_by_id.get(ln.case_id) and case_by_id[ln.case_id].partial_rule_id:
            rule_lines[case_by_id[ln.case_id].partial_rule_id].add(ln.line_id)
    for d in case_decisions:
        if d.action != "override" or not d.line_id:
            continue
        ln = line_by_id.get(d.line_id)
        if not ln:
            continue
        case = case_by_id.get(ln.case_id or "")
        rid = ln.rule_id or (case.partial_rule_id if case else None)
        if rid:
            rule_overrides[rid].add(d.line_id)
    rule_health = []
    for rid, line_ids in sorted(rule_lines.items()):
        overridden = len(rule_overrides.get(rid, set()))
        rate = _rate(overridden, len(line_ids))
        rule_health.append(
            {
                "rule_id": rid,
                "lines": len(line_ids),
                "overridden": overridden,
                "override_rate": rate,
                "status": "potentially_stale" if rate is not None and rate >= STALE_OVERRIDE_RATE and overridden else "stable",
            }
        )
    stale_rules = [r["rule_id"] for r in rule_health if r["status"] == "potentially_stale"]

    # Cycle time: first opened_at (if recorded) or first Decision → sign-off.
    opened = [t for t in (_parse_ts(c.opened_at) for c in cases) if t]
    first_decision = _parse_ts(case_decisions[0].timestamp) if case_decisions else None
    start = min(opened) if opened else first_decision
    end = _parse_ts(sign_off.timestamp) if sign_off else None
    hours: Optional[float] = None
    hours_note = "not signed off yet"
    if start and end:
        hours = round((end - start).total_seconds() / 3600, 4)
        hours_note = (
            "first Case opened → sign-off"
            if opened
            else "first Decision → sign-off (Case opened_at not recorded)"
        )
        if run_kind == "scripted_replay":
            hours_note += "; scripted replay — not evidence of human cycle time"

    # Time-to-decide per Case (only where opened_at exists).
    ttd = []
    for c in decided_cases:
        o = _parse_ts(c.opened_at)
        d = next((x for x in reversed(case_decisions) if x.case_id == c.case_id), None)
        if o and d and _parse_ts(d.timestamp):
            ttd.append((_parse_ts(d.timestamp) - o).total_seconds() / 3600)  # type: ignore[operator]

    hard_ties = [t for t in canonical.tieouts if t.kind in ("staging_to_lines", "diu_batch_zero_balance", "statement_row_count")]
    rule_lines_count = sum(1 for ln in lines if ln.mapping_method == "rule")
    journal_events: Optional[int] = None
    if journal_path and Path(journal_path).exists():
        journal_events = sum(1 for _ in Path(journal_path).read_text(encoding="utf-8").splitlines() if _.strip())

    return {
        "metrics_version": METRICS_VERSION,
        "close_id": canonical.close.close_id,
        "workflow": canonical.close.workflow,
        "period": canonical.close.period,
        "close_status": canonical.close.status,
        "run": {
            "kind": run_kind,
            "note": run_note,
            "computed_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        },
        "volume": {
            "lines": len(lines),
            "rule_mapped_lines": rule_lines_count,
            "rule_coverage": _rate(rule_lines_count, len(lines)),
            "cases_opened": len(cases),
            "cases_decided": len(decided_cases),
            "cases_open": len(open_cases),
            "decisions": len(case_decisions),
            "journal_events": journal_events,
        },
        "exception_rate": {
            "value": _rate(len(cases), len(lines)),
            "definition": "Cases opened / Lines",
            "by_reason": per_reason,
        },
        "override_rate": {
            "value": _rate(actions.get("override", 0), len(decided_cases)),
            "definition": "Override Decisions / decided Cases",
            "overrides": actions.get("override", 0),
            "accepts": actions.get("accept", 0),
            "rejects": actions.get("reject", 0),
        },
        "review_rounds": {
            "mean": round(sum(rounds) / len(rounds), 4) if rounds else None,
            "max": max(rounds) if rounds else None,
            "cases_with_more_than_one_round": multi_round_cases,
            "definition": "Decisions per decided Case; > 1 means reject → re-decide",
        },
        "hours_per_close": {
            "value": hours,
            "note": hours_note,
            "started_at": start.isoformat() if start else None,
            "signed_off_at": end.isoformat() if end else None,
            "time_to_decide_hours": {
                "mean": round(sum(ttd) / len(ttd), 4) if ttd else None,
                "max": round(max(ttd), 4) if ttd else None,
                "sample": len(ttd),
            },
        },
        "error_rate": {
            "value": None,
            "note": "Measured after the validated export is loaded into the system of record; no SoR in this repo.",
        },
        "decisions_by_role": dict(by_role),
        "decisions_by_person": dict(by_person),
        "rule_health": {
            "stale_threshold": STALE_OVERRIDE_RATE,
            "potentially_stale_rules": stale_rules,
            "rules_evaluated": len(rule_health),
            "rules": rule_health,
        },
        "tie_out": {
            "hard_gates": [{"kind": t.kind, "status": t.status, "difference": t.difference} for t in hard_ties],
            "all_passed": all(t.status in ("passed", "not_applicable") for t in hard_ties),
        },
        "sign_off": (
            {
                "decision_id": sign_off.decision_id,
                "decided_by": sign_off.decided_by,
                "role": sign_off.role,
                "timestamp": sign_off.timestamp,
            }
            if sign_off
            else None
        ),
    }


def metrics_for_close_file(path: Path, *, run_kind: str = "unknown", run_note: Optional[str] = None) -> dict[str, Any]:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    canonical = CanonicalClose.from_dict(raw)
    journal = Path(path).with_name(Path(path).stem.replace("close", "decisions") + ".jsonl")
    return compute_pilot_metrics(canonical, run_kind=run_kind, run_note=run_note, journal_path=journal)


def main() -> None:
    parser = argparse.ArgumentParser(description="Compute pilot metrics from a canonical close")
    parser.add_argument("--close", type=Path, default=ROOT / "data" / "processed" / "close.json")
    parser.add_argument("--out", type=Path, default=None, help="Write JSON here (default: print)")
    parser.add_argument("--run-kind", default="unknown", choices=("unknown", "live", "human", "scripted_replay"))
    parser.add_argument("--note", default=None)
    args = parser.parse_args()
    metrics = metrics_for_close_file(args.close.resolve(), run_kind=args.run_kind, run_note=args.note)
    text = json.dumps(metrics, indent=2, ensure_ascii=False)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text + "\n", encoding="utf-8")
        print(f"Wrote {args.out}")
    else:
        print(text)


if __name__ == "__main__":
    main()
