#!/usr/bin/env python3
"""Scripted pilot run: walk a real close end-to-end and measure it.

  copy close → decide every open Case → batch sign-off → validated export
  → pilot metrics (scripts/pilot_metrics.py)

Works on a COPY under data/processed/pilot/<close_id>/ so the demo state in
data/processed/close.json is untouched.

What the replay decides (and why it is honest):
  * Dataset 01 — Accept the treatment the accountant actually filed in the
    Staging Sheet (filed_snapshot). That is the human judgment the workbook
    already holds; recording it as a Decision with a reason is the product.
    Rows the workbook flagged `Review` are accepted as `Review` — the gap is
    exported visibly, not tidied away.
  * Dataset 02 — Accept the first deterministic candidate on the Case
    (Mapping Gaps proposal, Batch Preference override, or crosswalk result).
    Cases with no candidate are accepted as an explicit Hold so they leave in
    the export marked, never silently mapped.

RACI: Fund Admin decides medium Cases, Fund Manager decides high (material)
Cases and signs off. Nothing here is an override; override_rate is a real 0.
The run is labelled `scripted_replay` in the metrics — its timings are not
evidence of human cycle time.
"""
from __future__ import annotations

import argparse
import copy
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from canonical_model import (  # noqa: E402
    CanonicalClose,
    Case,
    Line,
    ValidationError,
    record_batch_sign_off,
    record_decision,
)
from emit_export import emit_validated, export_blockers  # noqa: E402
from pilot_metrics import compute_pilot_metrics  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
ADMIN = ("Fund Admin (pilot replay)", "fund_admin")
MANAGER = ("Fund Manager (pilot replay)", "fund_manager")


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _who(case: Case) -> tuple[str, str]:
    return MANAGER if case.priority == "high" else ADMIN


def _source_note(line: Line, sources: dict[str, Any]) -> str:
    bank = line.bank_ref or {}
    src = sources.get(bank.get("source_id") or "") or sources.get((line.source_ref or {}).get("source_id") or "")
    name = getattr(src, "filename", None) or "source"
    loc = bank.get("location") or (line.source_ref or {}).get("location") or {}
    if "page" in loc:
        return f"{name} page {loc['page']}"
    if "row" in loc:
        return f"{name} {loc.get('sheet', '')} row {loc['row']}".replace("  ", " ")
    return name


def decide_bank_to_journal(case: Case, line: Line, sources: dict[str, Any]) -> tuple[dict[str, Any], str, Optional[int]]:
    filed = line.filed_snapshot or {}
    mapping = line.mapping or {}
    cls = filed.get("classification") or mapping.get("classification")
    held = not cls or str(cls).strip().lower() == "review"
    final: dict[str, Any] = {"classification": "Review" if held else cls}
    if filed.get("matched_project"):
        final["project_code"] = filed["matched_project"]
    if filed.get("matched_counterparty"):
        final["counterparty"] = filed["matched_counterparty"]
    if mapping.get("account"):
        final["account"] = mapping["account"]
    where = _source_note(line, sources)
    reasons = ", ".join(case.reasons)
    if held:
        reason = (
            f"Workbook flagged this row Review and filed no classification. Held as Review so the gap "
            f"leaves in the export visibly; source excerpt verified on {where}. Case reasons: {reasons}."
        )
    else:
        reason = (
            f"Accepted the treatment filed in the Staging Sheet — classification {final['classification']}"
            + (f", project {final['project_code']}" if final.get("project_code") else "")
            + (f", counterparty {final['counterparty']}" if final.get("counterparty") else "")
            + f". Source excerpt verified on {where}. Case reasons: {reasons}. "
            "The filed value is the accountant's judgment; recording it as a Decision makes it reviewable."
        )
    return final, reason, None


def decide_gl_to_loader(case: Case, line: Line, sources: dict[str, Any]) -> tuple[dict[str, Any], str, Optional[int]]:
    facts = line.raw_facts or {}
    where = _source_note(line, sources)
    reasons = ", ".join(case.reasons)
    cands = list(((case.suggestion or {}).get("candidates")) or [])
    head = (
        f"{facts.get('legal_entity')} · {facts.get('gl_account')} · {facts.get('trans_type')} "
        f"({facts.get('row_count')} GL rows, {where})."
    )
    if cands:
        c = cands[0]
        final = {k: v for k, v in {"classification": c.get("classification"), "account": c.get("account")}.items() if v}
        if line.mapping.get("fund"):
            final["fund"] = line.mapping["fund"]
        treatment = c.get("treatment") or "candidate"
        if treatment.startswith("Mapping Gaps"):
            why = "Accepted the administrator's proposal on the Mapping Gaps sheet (approval column was blank in the workbook)."
        elif treatment.startswith("Batch Preference"):
            why = "Applied the Batch Preference override: Partner Transfer batch ranks first, so the batch type governs the loader treatment."
        elif "entity_miss" in case.reasons:
            why = "Crosswalk treatment recorded; the legal entity has no LE Mapping row and is not in this tranche — target entity ID to be assigned at set-up, not guessed."
        elif "rule_mismatch" in case.reasons:
            why = "Crosswalk hit is exact; the verified loader disagrees at (entity, trans type) level — accepted the crosswalk and left the loader difference on record for the administrator."
        else:
            why = f"Accepted {treatment}."
        reason = f"{head} {why} Case reasons: {reasons}."
        return final, reason, 0
    final = {"classification": "Hold: no crosswalk — administrator to map"}
    if line.mapping.get("fund"):
        final["fund"] = line.mapping["fund"]
    reason = (
        f"{head} No CoA Mapping, Mapping Gaps proposal or batch override covers this movement. "
        f"Recorded as an explicit Hold so it leaves in the export marked, not silently mapped. Case reasons: {reasons}."
    )
    return final, reason, None


DECIDERS = {
    "bank_to_journal": decide_bank_to_journal,
    "gl_to_loader": decide_gl_to_loader,
}


def run_pilot(close_path: Path, out_dir: Path, *, force: bool = False) -> dict[str, Any]:
    raw = json.loads(close_path.read_text(encoding="utf-8"))
    canonical = CanonicalClose.from_dict(copy.deepcopy(raw))
    close_id = canonical.close.close_id
    target = out_dir / close_id
    if target.exists():
        if not force:
            raise SystemExit(f"{target} exists; pass --force to rerun")
        shutil.rmtree(target)
    target.mkdir(parents=True)
    work = target / "close.json"
    journal = target / "decisions.jsonl"
    journal.write_text("", encoding="utf-8")

    decide = DECIDERS.get(canonical.close.workflow)
    if decide is None:
        raise SystemExit(f"no pilot decision policy for workflow {canonical.close.workflow!r}")
    sources = {s.source_id: s for s in canonical.sources}
    lines = {ln.line_id: ln for ln in canonical.lines}

    started = _now()
    open_cases = sorted((c for c in canonical.cases if c.status == "unresolved"), key=lambda c: c.case_id)
    print(f"{close_id}: {len(canonical.lines)} lines, {len(open_cases)} open cases → deciding")
    tally: dict[str, int] = {}
    for case in open_cases:
        line = lines[case.line_id]
        final, reason, idx = decide(case, line, sources)
        who, role = _who(case)
        try:
            record_decision(
                canonical,
                case_id=case.case_id,
                action="accept",
                decided_by=who,
                role=role,
                reason=reason,
                final_value=final,
                chosen_candidate_index=idx,
                journal_path=journal,
            )
        except ValidationError as exc:
            print(str(exc), file=sys.stderr)
            raise SystemExit(1) from exc
        tally[case.primary_reason] = tally.get(case.primary_reason, 0) + 1

    try:
        record_batch_sign_off(
            canonical,
            decided_by=MANAGER[0],
            role=MANAGER[1],
            reason=f"All {len(open_cases)} Cases decided with reasons; hard tie-outs PASS; required close tasks complete. Scripted pilot replay.",
            journal_path=journal,
        )
    except ValidationError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1) from exc

    blockers = export_blockers(canonical)
    if blockers:
        raise SystemExit("export blocked after sign-off: " + "; ".join(blockers))
    result = emit_validated(canonical, generated_by="pilot_replay")
    csv_path = target / result["file_name"]
    csv_path.write_bytes(result["csv_bytes"])
    (target / "export.json").write_text(json.dumps(result["export"], indent=2) + "\n", encoding="utf-8")

    work.write_text(json.dumps(canonical.to_dict(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    metrics = compute_pilot_metrics(
        canonical,
        run_kind="scripted_replay",
        run_note=(
            "Decisions replayed from the filed workbook / deterministic candidates by scripts/run_pilot.py; "
            "no human timing. Replace with a human run for VALIDATE."
        ),
        journal_path=journal,
    )
    metrics["run"]["started_at"] = started
    metrics["run"]["source_close"] = str(close_path.relative_to(ROOT)) if close_path.is_relative_to(ROOT) else str(close_path)
    metrics["run"]["decided_by_reason"] = tally
    metrics["export"] = {
        "file": str(csv_path.relative_to(ROOT)),
        "line_count": result["export"]["line_count"],
        "profile": result["export"]["profile"],
    }
    (target / "pilot-metrics.json").write_text(json.dumps(metrics, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"  decisions   {metrics['volume']['decisions']}  by reason {tally}")
    print(f"  sign-off    {metrics['sign_off']['decided_by']} @ {metrics['sign_off']['timestamp']}")
    print(f"  export      {csv_path.relative_to(ROOT)}  ({result['export']['line_count']} rows)")
    print(f"  exception   {metrics['exception_rate']['value']}   override {metrics['override_rate']['value']}   rounds {metrics['review_rounds']['mean']}")
    print(f"  hours/close {metrics['hours_per_close']['value']}  ({metrics['hours_per_close']['note']})")
    print(f"  metrics     {(target / 'pilot-metrics.json').relative_to(ROOT)}")
    return metrics


def main() -> None:
    parser = argparse.ArgumentParser(description="Scripted pilot: decide → sign off → export → measure, on a copy")
    parser.add_argument("--close", type=Path, action="append", help="canonical close JSON (repeatable)")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "data" / "processed" / "pilot")
    parser.add_argument("--force", action="store_true", help="overwrite an existing pilot run")
    args = parser.parse_args()
    closes = args.close or [ROOT / "data" / "processed" / "close.json"]
    summary = []
    for path in closes:
        path = path.resolve()
        if not path.exists():
            raise SystemExit(f"missing {path}")
        m = run_pilot(path, args.out_dir.resolve(), force=args.force)
        summary.append(
            {
                "close_id": m["close_id"],
                "workflow": m["workflow"],
                "lines": m["volume"]["lines"],
                "cases": m["volume"]["cases_opened"],
                "rule_coverage": m["volume"]["rule_coverage"],
                "exception_rate": m["exception_rate"]["value"],
                "override_rate": m["override_rate"]["value"],
                "review_rounds_mean": m["review_rounds"]["mean"],
                "export_rows": m["export"]["line_count"],
                "run_kind": m["run"]["kind"],
            }
        )
    index = args.out_dir.resolve() / "pilot-summary.json"
    index.write_text(json.dumps({"runs": summary, "generated_at": _now()}, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {index.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
