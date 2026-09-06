#!/usr/bin/env python3
"""Dataset 02 ingestion entry point (investor-level GL → loader).

raw GL xlsx + verified loader workbook
  → movement groups (Legal Entity × GL Account × Trans Type × currency)
  → crosswalk Rules (CoA / LE / Deal Mapping, exact hit only)
  → compare with the verified loader (filed snapshot)
  → canonical model (same Line / Rule / Case / TieOut objects as Dataset 01)
  → validated JSON (data/processed/close-dataset02.json)

Never modifies files under data/raw. The 34k-row GL body is not copied
under data/extracted; only a grouped summary is written.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from canonical_model import ValidationError, count_metrics, validate  # noqa: E402
from normalize_gl import normalize_gl_to_canonical_model  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]


def write_json(data: object, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def ingest_dataset02(input_dir: Path, output_file: Path, extracted_dir: Path) -> Path:
    if not input_dir.is_dir():
        raise SystemExit(f"input directory not found: {input_dir}")

    try:
        canonical = normalize_gl_to_canonical_model(input_dir)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1) from exc

    try:
        validate(canonical, check_residue=False)
    except ValidationError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1) from exc

    write_json(canonical.to_dict(), output_file)

    summary = getattr(canonical, "gl_summary", {})
    report = getattr(canonical, "evaluation_report", [])
    extracted_dir.mkdir(parents=True, exist_ok=True)
    write_json(
        {
            "summary": summary,
            "groups": [
                {"line_id": ln.line_id, **(ln.raw_facts or {})} for ln in canonical.lines
            ],
        },
        extracted_dir / "gl-groups.json",
    )
    write_json(
        {
            "line_count": len(report),
            "complete": sum(1 for r in report if r.get("complete")),
            "agrees": sum(1 for r in report if r.get("agrees")),
            "rule_method": sum(1 for r in report if r.get("mapping_method") == "rule"),
            "rows": report,
        },
        output_file.parent / "rule-evaluation-report-dataset02.json",
    )
    (output_file.parent / "decisions-dataset02.jsonl").write_text("", encoding="utf-8")

    print("---")
    print(f"close_id     {canonical.close.close_id}")
    print(f"workflow     {canonical.close.workflow}")
    print(f"gl_rows      {summary.get('gl_rows')}")
    print(f"lines        {len(canonical.lines)}  (movement groups)")
    print(f"rules        {len(canonical.rules)}")
    print(f"cases        {len(canonical.cases)}")
    print(f"tieouts      {len(canonical.tieouts)}")
    resolved = sum(1 for ln in canonical.lines if ln.status == "resolved")
    print(f"resolved     {resolved}")
    print(f"unresolved   {len(canonical.lines) - resolved}")
    print(f"reason tags  {summary.get('reason_counts')}")
    print(f"residue      {summary.get('residue')}")
    print(f"source_flags {dict(Counter(f for ln in canonical.lines for f in ln.source_flags))}")
    print(f"metrics      {count_metrics(canonical)}")
    for t in canonical.tieouts:
        mark = {"passed": "PASS", "failed": "FAIL", "not_applicable": "N/A"}.get(t.status, t.status)
        print(f"  tieout [{mark}] {t.tieout_id} {t.kind} {t.currency or '-'}: diff={t.difference}")
    print(f"Wrote {output_file}")
    return output_file


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest Dataset 02 into the canonical close model")
    parser.add_argument("--input", type=Path, default=ROOT / "data" / "raw" / "dataset02")
    parser.add_argument("--output", type=Path, default=ROOT / "data" / "processed" / "close-dataset02.json")
    parser.add_argument("--extracted", type=Path, default=ROOT / "data" / "extracted")
    args = parser.parse_args()
    ingest_dataset02(args.input.resolve(), args.output.resolve(), args.extracted.resolve())


if __name__ == "__main__":
    main()
