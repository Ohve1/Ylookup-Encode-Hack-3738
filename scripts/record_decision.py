#!/usr/bin/env python3
"""Record a human Decision on a Case in data/processed/close.json."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from canonical_model import CanonicalClose, ValidationError, record_decision  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CLOSE = ROOT / "data" / "processed" / "close.json"


def main() -> None:
    parser = argparse.ArgumentParser(description="Record a Decision on a Case")
    parser.add_argument("--close", type=Path, default=DEFAULT_CLOSE)
    parser.add_argument("--case-id", required=True)
    parser.add_argument("--action", required=True, choices=("accept", "reject", "override"))
    parser.add_argument("--decided-by", required=True)
    parser.add_argument("--role", default="fund_admin")
    parser.add_argument("--reason", required=True)
    parser.add_argument(
        "--final-value",
        required=True,
        help='JSON object, e.g. \'{"account":"7250"}\'',
    )
    parser.add_argument(
        "--candidates",
        default="[]",
        help="JSON array of candidate treatments",
    )
    args = parser.parse_args()

    path = args.close.resolve()
    data = json.loads(path.read_text(encoding="utf-8"))
    canonical = CanonicalClose.from_dict(data)

    try:
        decision = record_decision(
            canonical,
            case_id=args.case_id,
            action=args.action,
            decided_by=args.decided_by,
            role=args.role,
            reason=args.reason,
            final_value=json.loads(args.final_value),
            candidates=json.loads(args.candidates),
        )
    except ValidationError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1) from exc

    path.write_text(
        json.dumps(canonical.to_dict(), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {decision.decision_id} on {decision.case_id} → {path}")


if __name__ == "__main__":
    main()
