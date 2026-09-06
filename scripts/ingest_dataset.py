#!/usr/bin/env python3
"""Dataset 01 ingestion entry point.

raw PDF / Excel
  → extraction (location-preserving)
  → raw structured representation (data/extracted/)
  → normalization
  → canonical model
  → validated JSON (data/processed/close.json)

Never modifies files under data/raw.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Allow `python scripts/ingest_dataset.py` without installing as a package
SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from canonical_model import ValidationError, validate  # noqa: E402
from extract_excel import extract_excels  # noqa: E402
from extract_pdf import extract_pdfs  # noqa: E402
from normalize import normalize_to_canonical_model  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]


def find_pdfs(input_dir: Path) -> list[Path]:
    return sorted(input_dir.rglob("*.pdf"))


def find_excels(input_dir: Path) -> list[Path]:
    files = list(input_dir.rglob("*.xlsx")) + list(input_dir.rglob("*.xlsm"))
    # Skip Excel temp lock files
    return sorted(p for p in files if not p.name.startswith("~$"))


def write_json(data: object, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def ingest_dataset(input_dir: Path, output_file: Path, extracted_dir: Path) -> Path:
    if not input_dir.is_dir():
        raise SystemExit(f"input directory not found: {input_dir}")

    pdf_files = find_pdfs(input_dir)
    excel_files = find_excels(input_dir)
    if not pdf_files and not excel_files:
        raise SystemExit(f"no PDF or Excel files under {input_dir}")

    print(f"Found {len(pdf_files)} PDF(s), {len(excel_files)} Excel file(s)")

    pdf_docs = extract_pdfs(pdf_files)
    excel_rows = extract_excels(excel_files)

    extracted_dir.mkdir(parents=True, exist_ok=True)
    write_json({"documents": pdf_docs}, extracted_dir / "pdf.json")
    write_json({"rows": excel_rows}, extracted_dir / "excel.json")
    print(f"Wrote {extracted_dir / 'pdf.json'} ({len(pdf_docs)} pages)")
    print(f"Wrote {extracted_dir / 'excel.json'} ({len(excel_rows)} rows)")

    canonical = normalize_to_canonical_model(pdf_docs, excel_rows)

    try:
        validate(canonical)
    except ValidationError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1) from exc

    payload = canonical.to_dict()
    write_json(payload, output_file)

    # Evaluation report (100-row rule applicability / agreement)
    report = getattr(canonical, "evaluation_report", None)
    if report is not None:
        report_path = output_file.parent / "rule-evaluation-report.json"
        summary = {
            "line_count": len(report),
            "complete": sum(1 for r in report if r.get("complete")),
            "agrees": sum(1 for r in report if r.get("agrees")),
            "rule_method": sum(1 for r in report if r.get("mapping_method") == "rule"),
            "disagreements": [
                r for r in report
                if r.get("complete") and not r.get("agrees")
            ],
            "rows": report,
        }
        write_json(summary, report_path)
        print(f"Wrote {report_path}")

    # Fresh decision journal for a new ingest
    journal = output_file.parent / "decisions.jsonl"
    journal.write_text("", encoding="utf-8")

    # Summary
    print("---")
    print(f"close_id     {canonical.close.close_id}")
    print(f"contract     {canonical.close.contract_version}")
    print(f"sources      {len(canonical.sources)}")
    print(f"lines        {len(canonical.lines)}")
    print(f"rules        {len(canonical.rules)}")
    print(f"cases        {len(canonical.cases)}")
    print(f"decisions    {len(canonical.decisions)}")
    print(f"tieouts      {len(canonical.tieouts)}")
    resolved = sum(1 for ln in canonical.lines if ln.status == "resolved")
    print(f"resolved     {resolved}")
    print(f"unresolved   {len(canonical.lines) - resolved}")
    bank_linked = sum(
        1
        for ln in canonical.lines
        if ln.bank_ref and ln.bank_ref.get("match_method") not in (None, "none", "ambiguous")
    )
    print(f"bank_ref hit {bank_linked}/{len(canonical.lines)}")
    methods = getattr(canonical, "match_method_counts", None)
    if methods:
        print(f"match_method {methods}")
    from collections import Counter

    reason_counts = Counter()
    flag_counts = Counter()
    for c in canonical.cases:
        reason_counts.update(c.reasons)
    for ln in canonical.lines:
        flag_counts.update(ln.source_flags or [])
    print(f"reason tags  {dict(reason_counts)}")
    print(f"source_flags {dict(flag_counts)}")
    from canonical_model import count_metrics

    print(f"metrics      {count_metrics(canonical)}")
    for t in canonical.tieouts:
        mark = {"passed": "PASS", "failed": "FAIL", "not_applicable": "N/A"}.get(
            t.status, t.status
        )
        extra = f" batch_id={t.batch_id}" if t.batch_id else ""
        print(
            f"  tieout [{mark}] {t.tieout_id} {t.kind} {t.currency or '-'}: "
            f"diff={t.difference}{extra}"
        )
    print(f"Wrote {output_file}")
    return output_file


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Ingest Dataset 01 into the canonical close model"
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=ROOT / "data" / "raw" / "dataset01",
        help="Directory containing PDF and Excel source files",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "data" / "processed" / "close.json",
        help="Canonical close JSON output path",
    )
    parser.add_argument(
        "--extracted",
        type=Path,
        default=ROOT / "data" / "extracted",
        help="Directory for intermediate extraction JSON",
    )
    args = parser.parse_args()
    ingest_dataset(args.input.resolve(), args.output.resolve(), args.extracted.resolve())


if __name__ == "__main__":
    main()
