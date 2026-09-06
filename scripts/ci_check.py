#!/usr/bin/env python3
"""Control-language contract checks. Does not read the Discord pack.

Runs against the public fixture and, when present, data/processed/close.json.

  1. No Rule carries a `confidence` field (exact hit or Case — D-004).
  2. Reviewer surface never says "Method: AI" / "Ask Gemini".
  3. Every open Case is displayed as Unresolved; every resolved line has
     provenance (Rule / Decision / Override) and a source excerpt.
  4. The four-way residue breakdown sums to the open-case count.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "app"))

from adapt_close import adapt_close_for_reviewer  # noqa: E402
from canonical_model import CanonicalClose, ValidationError, validate  # noqa: E402

FIXTURE = ROOT / "fixtures" / "sample-close.json"
PROCESSED = ROOT / "data" / "processed" / "close.json"
PROCESSED_02 = ROOT / "data" / "processed" / "close-dataset02.json"
PILOT_DIR = ROOT / "data" / "processed" / "pilot"
SURFACE_DIRS = (ROOT / "app" / "static", ROOT / "fixtures")
FORBIDDEN_SURFACE = ("Method: AI", "Ask Gemini", "Low-confidence", "method_label\": \"AI")
ALLOWED_ORIGIN = {"rule", "decision", "override", "unresolved"}
ALLOWED_DISPLAY = {"Rule", "Decision", "Override", "Unresolved"}


def fail(msg: str) -> None:
    print(f"FAIL: {msg}", file=sys.stderr)
    sys.exit(1)


def check_surface_words() -> None:
    for d in SURFACE_DIRS:
        for p in d.rglob("*"):
            if not p.is_file():
                continue
            text = p.read_text(encoding="utf-8", errors="replace")
            for bad in FORBIDDEN_SURFACE:
                if bad in text:
                    fail(f"{p.relative_to(ROOT)} contains forbidden surface text {bad!r}")


def check_close(path: Path, *, check_residue: bool) -> str:
    raw = json.loads(path.read_text(encoding="utf-8"))
    rel = path.relative_to(ROOT)

    for r in raw.get("rules") or []:
        if "confidence" in r:
            fail(f"{rel}: Rule {r.get('rule_id')} carries a confidence field")

    try:
        validate(CanonicalClose.from_dict(raw), check_residue=check_residue)
    except ValidationError as exc:
        fail(f"{rel}: canonical validation failed\n{exc}")

    adapted = adapt_close_for_reviewer(raw)
    lines = adapted.get("lines") or []
    if not lines:
        fail(f"{rel}: no lines")

    open_cases = 0
    for ln in lines:
        origin = ln.get("origin")
        if origin not in ALLOWED_ORIGIN:
            fail(f"{rel} {ln.get('id')}: origin {origin!r} not in {sorted(ALLOWED_ORIGIN)}")
        if ln.get("display_method") not in ALLOWED_DISPLAY:
            fail(f"{rel} {ln.get('id')}: display_method {ln.get('display_method')!r}")
        if not (ln.get("source") or {}).get("excerpt", "").strip():
            fail(f"{rel} {ln.get('id')}: source excerpt required")
        if origin in {"decision", "override", "unresolved"} and not ln.get("case"):
            fail(f"{rel} {ln.get('id')}: {origin} requires a case")
        if origin == "unresolved":
            open_cases += 1

    for c in adapted.get("cases") or []:
        if c["status"] in ("needs_review", "rejected") and c["display_method"] != "Unresolved":
            fail(f"{rel} {c['case_id']}: open case shows {c['display_method']!r}, not Unresolved")
        if c["status"] == "resolved" and c["display_method"] not in ("Decision", "Override"):
            fail(f"{rel} {c['case_id']}: resolved case shows {c['display_method']!r}")

    ov = adapted["overview"]
    breakdown_total = sum(r["count"] for r in ov["reason_breakdown"])
    if breakdown_total != ov["needs_review"]:
        fail(f"{rel}: breakdown sums to {breakdown_total}, needs_review is {ov['needs_review']}")
    if open_cases != ov["needs_review"]:
        fail(f"{rel}: {open_cases} unresolved lines vs needs_review {ov['needs_review']}")
    if ov["tie_out"]["status"] not in {"PASS", "FAIL"}:
        fail(f"{rel}: tie_out.status must be PASS or FAIL")

    return (
        f"{rel}: {len(lines)} lines, tie-out={ov['tie_out']['status']}, "
        f"unresolved={ov['needs_review']}, breakdown="
        + "/".join(str(r["count"]) for r in ov["reason_breakdown"])
    )


def main() -> None:
    check_surface_words()
    if not FIXTURE.exists():
        fail(f"missing {FIXTURE.relative_to(ROOT)}")
    reports = [check_close(FIXTURE, check_residue=False)]
    fixture_open = adapt_close_for_reviewer(json.loads(FIXTURE.read_text()))["overview"]["needs_review"]
    if fixture_open < 1:
        fail("fixture must keep at least one unresolved case (do not tidy the residue)")
    if PROCESSED.exists():
        reports.append(check_close(PROCESSED, check_residue=True))
    if PROCESSED_02.exists():
        # Dataset 02: same objects, same surface words; README2 residue is a tie-out.
        reports.append(check_close(PROCESSED_02, check_residue=False))
        raw02 = json.loads(PROCESSED_02.read_text(encoding="utf-8"))
        residue = [t for t in raw02.get("tieouts") or [] if t.get("kind") == "readme_residue"]
        if len(residue) < 3 or any(t.get("status") != "passed" for t in residue):
            fail("close-dataset02.json: README2 residue tie-outs must be present and passed")
    if PILOT_DIR.exists():
        # Every pilot copy that claims an export must be signed off with zero open Cases.
        for pilot_close in sorted(PILOT_DIR.glob("*/close.json")):
            rawp = json.loads(pilot_close.read_text(encoding="utf-8"))
            rel = pilot_close.relative_to(ROOT)
            if rawp["close"].get("status") != "signed_off":
                fail(f"{rel}: pilot copy not signed off")
            if any(c.get("status") == "unresolved" for c in rawp.get("cases") or []):
                fail(f"{rel}: pilot copy has open cases")
            if not list(pilot_close.parent.glob("validated_mapping_*.csv")):
                fail(f"{rel}: pilot copy has no validated export")
            if not (pilot_close.parent / "pilot-metrics.json").exists():
                fail(f"{rel}: pilot copy has no pilot-metrics.json")
            reports.append(check_close(pilot_close, check_residue=False) + " (pilot copy, signed off)")
    reconcile = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "reconcile.py")],
        check=False,
        capture_output=True,
        text=True,
    )
    if reconcile.returncode:
        fail("reconciliation control self-test failed\n" + reconcile.stderr)
    replay = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "test_decision_replay.py")],
        check=False,
        capture_output=True,
        text=True,
    )
    if replay.returncode:
        fail("decision replay tests failed\n" + replay.stderr + replay.stdout)
    export = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "test_export.py")],
        check=False,
        capture_output=True,
        text=True,
    )
    if export.returncode:
        fail("export tests failed\n" + export.stderr + export.stdout)
    roles = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "test_role_gates.py")],
        check=False,
        capture_output=True,
        text=True,
    )
    if roles.returncode:
        fail("role gate tests failed\n" + roles.stderr + roles.stdout)
    metrics = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "test_pilot_metrics.py")],
        check=False,
        capture_output=True,
        text=True,
    )
    if metrics.returncode:
        fail("pilot metrics tests failed\n" + metrics.stderr + metrics.stdout)
    for r in reports:
        print("OK:", r)
    print("OK:", reconcile.stdout.strip())
    print("OK:", replay.stdout.strip())
    print("OK:", export.stdout.strip().splitlines()[-1])
    print("OK:", roles.stdout.strip())
    print("OK:", metrics.stdout.strip().splitlines()[-1])


if __name__ == "__main__":
    main()
