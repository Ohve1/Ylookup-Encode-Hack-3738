#!/usr/bin/env python3
"""Serve the reviewer lens from data/processed/close.json (or the fixture).

Gemini (optional): set GOOGLE_API_KEY in .env for Google AI Studio. It only
drafts candidates on a Case; it never sets a mapping or a Method.
Key stays server-side only. No LLM required for the core workflow.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed" / "close.json"
FIXTURE = ROOT / "fixtures" / "sample-close.json"
DECISIONS_JOURNAL = ROOT / "data" / "processed" / "decisions.jsonl"
STATIC = Path(__file__).resolve().parent / "static"
SCRIPTS = ROOT / "scripts"

# Optional explicit close to serve (CLOSE_FILE env or --close). Lets the same
# reviewer lens open Dataset 02 (close-dataset02.json) or a pilot copy.
CLOSE_OVERRIDE: Path | None = None

if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
if str(ROOT / "app") not in sys.path:
    sys.path.insert(0, str(ROOT / "app"))

from adapt_close import adapt_close_for_reviewer  # noqa: E402
from canonical_model import (  # noqa: E402
    CanonicalClose,
    ValidationError,
    assign_case,
    record_batch_sign_off,
    record_decision,
)
from emit_export import (  # noqa: E402
    EXPORT_PROFILE,
    emit_validated,
    export_blockers,
)
from gemini_suggest import draft_candidates, llm_status  # noqa: E402
from pilot_metrics import compute_pilot_metrics  # noqa: E402

# Minimal RACI for Decision actions (D-009 / roles-and-workflow).
# Accountant prepares / files Cases; Admin decides; Manager approves material.
ROLE_ACTIONS = {
    "accountant": set(),  # no Accept / Override / Reject / sign_off
    "fund_admin": {"accept", "reject", "override", "sign_off"},
    "fund_manager": {"accept", "override", "sign_off"},
}


def close_path() -> Path:
    """Canonical close to serve: explicit override, else the ingested pack, else the fixture."""
    if CLOSE_OVERRIDE is not None:
        if CLOSE_OVERRIDE.exists():
            return CLOSE_OVERRIDE
        raise FileNotFoundError(f"missing {CLOSE_OVERRIDE}")
    if PROCESSED.exists():
        return PROCESSED
    if FIXTURE.exists():
        return FIXTURE
    raise FileNotFoundError(f"missing {PROCESSED} and {FIXTURE}")


def journal_path() -> Path | None:
    """Append-only Decision journal next to the served close (none for the fixture)."""
    path = close_path()
    if path == FIXTURE:
        return None
    if path == PROCESSED:
        return DECISIONS_JOURNAL
    return path.with_name(path.stem.replace("close", "decisions") + ".jsonl")


def load_canonical_dict() -> dict:
    return json.loads(close_path().read_text(encoding="utf-8"))


def load_adapted() -> dict:
    return adapt_close_for_reviewer(load_canonical_dict())


def write_canonical(canonical: CanonicalClose) -> None:
    close_path().write_text(
        json.dumps(canonical.to_dict(), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def load_reviewer_payload() -> bytes:
    adapted = load_adapted()
    adapted["llm"] = llm_status()
    return json.dumps(adapted, ensure_ascii=False).encode("utf-8")


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(STATIC), **kwargs)

    def _send_json(self, code: int, payload: dict) -> None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        if path in ("/api/close", "/api/close.json"):
            try:
                data = load_reviewer_payload()
            except Exception as exc:  # noqa: BLE001
                self._send_json(500, {"error": str(exc)})
                return
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return
        if path == "/api/export":
            qs = parse_qs(parsed.query or "")
            profile = (qs.get("profile") or [EXPORT_PROFILE])[0]
            try:
                raw = load_canonical_dict()
                blockers = export_blockers(raw)
                if blockers:
                    self._send_json(
                        409,
                        {
                            "error": "export not ready",
                            "blockers": blockers,
                            "profile": profile,
                        },
                    )
                    return
                result = emit_validated(raw, profile=profile, generated_by="reviewer")
            except ValueError as exc:
                self._send_json(
                    409,
                    {
                        "error": str(exc),
                        "blockers": str(exc).split("; "),
                        "profile": profile,
                    },
                )
                return
            except Exception as exc:  # noqa: BLE001
                self._send_json(500, {"error": str(exc)})
                return
            payload = result["csv_bytes"]
            self.send_response(200)
            self.send_header("Content-Type", result["content_type"])
            self.send_header(
                "Content-Disposition",
                f'attachment; filename="{result["file_name"]}"',
            )
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(payload)))
            self.send_header("X-Export-Profile", result["export"]["profile"])
            self.send_header("X-Export-Line-Count", str(result["export"]["line_count"]))
            self.end_headers()
            self.wfile.write(payload)
            return
        if path == "/api/llm":
            self._send_json(200, llm_status())
            return
        if path == "/api/metrics":
            # Pilot instrumentation, derived from the served close record only.
            try:
                canonical = CanonicalClose.from_dict(load_canonical_dict())
                metrics = compute_pilot_metrics(
                    canonical,
                    run_kind="live",
                    run_note=f"Served close record: {close_path().name}. Decisions as recorded in the close / journal.",
                    journal_path=journal_path(),
                )
            except Exception as exc:  # noqa: BLE001
                self._send_json(500, {"error": str(exc)})
                return
            self._send_json(200, metrics)
            return
        if path == "/":
            self.path = "/index.html"
        return super().do_GET()

    def do_POST(self):
        path = urlparse(self.path).path
        if path not in ("/api/decision", "/api/assign", "/api/suggest"):
            self.send_error(404)
            return
        length = int(self.headers.get("Content-Length") or 0)
        try:
            body = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
        except json.JSONDecodeError:
            self._send_json(400, {"error": "invalid JSON"})
            return

        if path == "/api/suggest":
            if "case_id" not in body:
                self._send_json(400, {"error": "missing fields: ['case_id']"})
                return
            try:
                raw = load_canonical_dict()
                canonical = CanonicalClose.from_dict(raw)
                case = next(
                    (c for c in canonical.cases if c.case_id == body["case_id"]),
                    None,
                )
                if case is None:
                    self._send_json(400, {"error": f"unknown case_id {body['case_id']}"})
                    return
                if case.status == "decided":
                    self._send_json(400, {"error": f"{case.case_id} is already decided"})
                    return

                # Candidates only. Line.mapping, mapping_method and Case.status
                # are untouched — a human Accept / Override is the only way in.
                draft = draft_candidates(raw, body["case_id"])
                case.suggestion = draft
                write_canonical(canonical)
            except ValueError as exc:
                self._send_json(400, {"error": str(exc)})
                return
            except Exception as exc:  # noqa: BLE001
                self._send_json(500, {"error": str(exc)})
                return
            self._send_json(200, {"ok": True, "candidates": draft})
            return

        if path == "/api/assign":
            if "case_id" not in body:
                self._send_json(400, {"error": "missing fields: ['case_id']"})
                return
            try:
                canonical = CanonicalClose.from_dict(load_canonical_dict())
                case = assign_case(
                    canonical,
                    case_id=body["case_id"],
                    assigned_to=body.get("assigned_to"),
                )
                write_canonical(canonical)
            except ValidationError as exc:
                self._send_json(400, {"error": str(exc), "details": exc.errors})
                return
            except Exception as exc:  # noqa: BLE001
                self._send_json(500, {"error": str(exc)})
                return
            self._send_json(
                200,
                {
                    "ok": True,
                    "case": {
                        "case_id": case.case_id,
                        "assigned_to": case.assigned_to,
                    },
                },
            )
            return

        action = body.get("action")
        role = body.get("role") or "fund_admin"
        allowed = ROLE_ACTIONS.get(role)
        if allowed is None:
            self._send_json(400, {"error": f"unknown role {role!r}"})
            return
        if action not in allowed:
            self._send_json(
                403,
                {
                    "error": f"role {role} cannot {action}",
                    "hint": "Accountant prepares Cases; Fund Admin decides; Fund Manager approves.",
                },
            )
            return
        if action == "sign_off":
            required = ("action", "decided_by", "reason")
        elif action == "reject":
            required = ("case_id", "action", "decided_by", "reason")
        else:
            required = ("case_id", "action", "decided_by", "reason", "final_value")
        missing = [k for k in required if k not in body]
        if missing:
            self._send_json(400, {"error": f"missing fields: {missing}"})
            return

        try:
            canonical = CanonicalClose.from_dict(load_canonical_dict())
            if action == "sign_off":
                decision = record_batch_sign_off(
                    canonical,
                    decided_by=body["decided_by"],
                    role=role,
                    reason=body["reason"],
                    journal_path=journal_path(),
                )
            else:
                idx = body.get("chosen_candidate_index")
                # Candidates are snapshotted server-side from the Case; the
                # browser only says which index (if any) it accepted.
                decision = record_decision(
                    canonical,
                    case_id=body["case_id"],
                    action=body["action"],
                    decided_by=body["decided_by"],
                    role=role,
                    reason=body["reason"],
                    final_value=body.get("final_value") or {},
                    chosen_candidate_index=int(idx) if idx is not None else None,
                    previous_value=body.get("previous_value"),
                    supersedes=body.get("supersedes"),
                    journal_path=journal_path(),
                )
            write_canonical(canonical)
        except ValidationError as exc:
            self._send_json(400, {"error": str(exc), "details": exc.errors})
            return
        except Exception as exc:  # noqa: BLE001
            self._send_json(500, {"error": str(exc)})
            return

        self._send_json(
            200,
            {
                "ok": True,
                "decision": {
                    "decision_id": decision.decision_id,
                    "case_id": decision.case_id,
                    "line_id": decision.line_id,
                    "action": decision.action,
                    "role": decision.role,
                    "chosen": decision.chosen,
                    "candidate_count": len(decision.candidates),
                },
            },
        )

    def log_message(self, fmt, *args):
        print("[reviewer]", fmt % args)


def main():
    global CLOSE_OVERRIDE
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8378)
    parser.add_argument(
        "--close",
        type=Path,
        default=Path(os.environ["CLOSE_FILE"]) if os.environ.get("CLOSE_FILE") else None,
        help="canonical close JSON to serve (default: data/processed/close.json, else fixture)",
    )
    args = parser.parse_args()
    if args.close is not None:
        CLOSE_OVERRIDE = args.close.resolve()
    try:
        source = close_path()
    except FileNotFoundError as exc:
        raise SystemExit(str(exc)) from exc
    status = llm_status()
    httpd = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    print(f"Reviewer lens → http://127.0.0.1:{args.port}")
    print(f"Close data    → {source}")
    print(f"Metrics       → http://127.0.0.1:{args.port}/api/metrics")
    if status["enabled"]:
        print(f"Candidates    → Gemini {status['model']} (drafts only; never a Method)")
    else:
        print("Candidates    → off (set GOOGLE_API_KEY in .env to enable Draft candidates)")
    print("Ctrl+C to stop.")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped")


if __name__ == "__main__":
    main()
