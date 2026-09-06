#!/usr/bin/env python3
"""Public fixture contract. Does not read the Discord pack."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "fixtures" / "sample-close.json"
ALLOWED_ORIGIN = {"rule", "decision", "override", "unresolved"}


def fail(msg: str) -> None:
    print(f"FAIL: {msg}", file=sys.stderr)
    sys.exit(1)


def main() -> None:
    if not FIXTURE.exists():
        fail(f"missing {FIXTURE.relative_to(ROOT)}")
    data = json.loads(FIXTURE.read_text())
    lines = data.get("lines") or []
    if not lines:
        fail("fixture has no lines")

    tie = (data.get("batch") or {}).get("tie_out") or {}
    if tie.get("status") not in {"pass", "fail"}:
        fail("batch.tie_out.status must be pass or fail")

    open_cases = 0
    for line in lines:
        origin = str(line.get("origin") or "").lower()
        if origin not in ALLOWED_ORIGIN:
            fail(f"{line.get('id')}: origin {origin!r} not in {sorted(ALLOWED_ORIGIN)}")
        source = line.get("source") or {}
        excerpt = (source.get("excerpt") or "").strip()
        if not excerpt:
            fail(f"{line.get('id')}: source excerpt required")
        if origin in {"decision", "override", "unresolved"} and not line.get("case"):
            fail(f"{line.get('id')}: {origin} requires a case")
        case = line.get("case") or {}
        if case and case.get("chosen") is None:
            open_cases += 1

    if open_cases < 1:
        fail("fixture must keep at least one unresolved case (do not tidy the residue)")

    print(
        f"OK: {len(lines)} lines, tie-out={tie.get('status')}, "
        f"unresolved_cases={open_cases}"
    )


if __name__ == "__main__":
    main()
