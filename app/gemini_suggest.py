"""Grounded candidate generator (Gemini via Google AI Studio).

What this module is allowed to do: draft 2–4 *candidate* treatments for one
open Case, each citing the evidence refs it relied on.

What it is never allowed to do: set a mapping, a Method, or a status. Its
output lives in ``Case.suggestion`` as candidates and is only ever turned into
a Line mapping by a human Accept / Override, which is recorded as a Decision.

Auth: GOOGLE_API_KEY (or GEMINI_API_KEY) from environment or repo-root .env.
Never expose the key to the browser.
"""
from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MODEL = "gemini-2.0-flash"
API_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "{model}:generateContent"
)
MAX_PRECEDENTS = 5
MIN_CANDIDATES, MAX_CANDIDATES = 2, 4


def load_dotenv(path: Optional[Path] = None) -> None:
    env_path = path or (ROOT / ".env")
    if not env_path.exists():
        return
    for raw in env_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip("'").strip('"')
        if key and key not in os.environ:
            os.environ[key] = value


load_dotenv()


def api_key() -> Optional[str]:
    return os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")


def model_name() -> str:
    return os.environ.get("GEMINI_MODEL") or DEFAULT_MODEL


def llm_status() -> dict[str, Any]:
    key = api_key()
    return {
        "enabled": bool(key),
        "provider": "google_ai_studio",
        "model": model_name() if key else None,
        "auth": "api_key" if key else None,
        "role": "candidate_drafts_only",
    }


# ---------------------------------------------------------------------------
# Grounding
# ---------------------------------------------------------------------------


def build_grounding(canonical: dict[str, Any], case_id: str) -> dict[str, Any]:
    """Collect the evidence a reviewer would have, each item with a ref id.

    Returns {"case", "line", "refs": {ref: description}, "sections": {...}}.
    Only refs present here may be cited by the model.
    """
    cases = {c["case_id"]: c for c in canonical.get("cases") or []}
    lines = {ln["line_id"]: ln for ln in canonical.get("lines") or []}
    rules = {r["rule_id"]: r for r in canonical.get("rules") or []}
    sources = {s["source_id"]: s for s in canonical.get("sources") or []}
    case = cases.get(case_id)
    if not case:
        raise ValueError(f"unknown case_id {case_id}")
    line = lines.get(case["line_id"])
    if not line:
        raise ValueError(f"Case {case_id} references unknown Line {case['line_id']}")

    refs: dict[str, str] = {}
    sections: dict[str, list[str]] = {"source": [], "rules": [], "precedents": [], "vocabulary": []}

    # Source excerpt (bank statement page + staging row)
    bank = line.get("bank_ref") or {}
    if bank.get("source_id"):
        src = sources.get(bank["source_id"]) or {}
        page = (bank.get("location") or {}).get("page")
        ref = bank["source_id"]
        refs[ref] = f"{src.get('filename', '?')} page {page}: {bank.get('excerpt') or line.get('description')}"
        sections["source"].append(f"[{ref}] {refs[ref]}")
    sref = line.get("source_ref") or {}
    if sref.get("source_id"):
        src = sources.get(sref["source_id"]) or {}
        loc = sref.get("location") or {}
        ref = sref["source_id"]
        refs[ref] = f"{src.get('filename', '?')} sheet {loc.get('sheet')} row {loc.get('row')}: {line.get('description')}"
        sections["source"].append(f"[{ref}] {refs[ref]}")

    # Partial rule hit on this Case + account-map rule for the bank account
    mapping = line.get("mapping") or {}
    rule_ids = []
    if case.get("partial_rule_id"):
        rule_ids.append(case["partial_rule_id"])
    if line.get("rule_id"):
        rule_ids.append(line["rule_id"])
    acct = mapping.get("account_number")
    for r in rules.values():
        cond = r.get("condition") or {}
        if acct and cond.get("field") == "account_number" and cond.get("value") == acct:
            rule_ids.append(r["rule_id"])
    for rid in dict.fromkeys(rule_ids):
        r = rules.get(rid)
        if not r:
            continue
        refs[rid] = f"{r.get('name')} · if {r.get('condition')} then {r.get('action')} (v{r.get('version', 'v0').lstrip('v')})"
        sections["rules"].append(f"[{rid}] {refs[rid]}")

    # Precedents: decided cases with the same primary reason
    decisions = [
        d for d in canonical.get("decisions") or []
        if d.get("action") in ("accept", "override") and d.get("case_id")
    ]
    same_reason = []
    for d in decisions:
        pc = cases.get(d["case_id"])
        pl = lines.get(d.get("line_id") or "")
        if not pc or not pl or pc.get("primary_reason") != case.get("primary_reason"):
            continue
        same_reason.append((d, pl))
    for d, pl in sorted(same_reason, key=lambda x: x[0].get("timestamp") or "", reverse=True)[:MAX_PRECEDENTS]:
        ref = d["decision_id"]
        refs[ref] = (
            f"{d.get('action')} by {d.get('decided_by')} ({d.get('role')}) on '{pl.get('description')}' "
            f"{pl.get('amount')} {pl.get('currency')} → {d.get('final_value')} — {d.get('reason')}"
        )
        sections["precedents"].append(f"[{ref}] {refs[ref]}")

    # Allowed classification vocabulary from the rule library
    classes = sorted(
        {
            str((r.get("condition") or {}).get("value"))
            for r in rules.values()
            if (r.get("condition") or {}).get("field") == "classification"
        }
    )
    sections["vocabulary"].append("classification ∈ " + ", ".join(classes))

    return {"case": case, "line": line, "refs": refs, "sections": sections}


def _prompt(g: dict[str, Any]) -> str:
    case, line, sections = g["case"], g["line"], g["sections"]
    mapping = line.get("mapping") or {}

    def block(title: str, items: list[str]) -> str:
        return f"{title}:\n" + ("\n".join(f"  {i}" for i in items) if items else "  (none)")

    return f"""You draft candidate treatments for one unresolved fund-close line.
You are NOT the decider. A fund administrator will Accept one candidate or Override with their own value.
Rules of evidence:
- Cite only the bracketed refs given below. Never invent a ref, a document, or a policy.
- Prefer null over a guess for account / project_code.
- Candidates must be materially different from each other (e.g. expense vs capitalised, vendor vs related party).
- 2 to 4 candidates.

Return ONLY a JSON object:
{{"candidates":[{{"treatment":string,"classification":string|null,"account":string|null,"project_code":string|null,
  "rationale":string (one paragraph, reviewer-facing),
  "evidence":[{{"type":"source"|"rule"|"precedent","ref":string}}]}}],
 "note":string (one line: what the candidates disagree about)}}

Case {case.get('case_id')} · reasons {case.get('reasons')} · priority {case.get('priority')}
Line {line.get('line_id')}: {line.get('amount')} {line.get('currency')} on {line.get('date')}
Description: {line.get('description')}
Workbook proposal (not a fact): classification={mapping.get('classification')} account={mapping.get('account')} project_code={mapping.get('project_code')} counterparty={mapping.get('counterparty') or mapping.get('pulled_counterparty')}

{block('SOURCE', sections['source'])}
{block('RULES', sections['rules'])}
{block('PRECEDENTS', sections['precedents'])}
{block('VOCABULARY', sections['vocabulary'])}
"""


# ---------------------------------------------------------------------------
# Call + validation
# ---------------------------------------------------------------------------


def _extract_json(text: str) -> dict[str, Any]:
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fence:
        return json.loads(fence.group(1))
    brace = re.search(r"\{.*\}", text, re.DOTALL)
    if brace:
        return json.loads(brace.group(0))
    raise ValueError("model response was not JSON")


def _call_gemini(prompt: str, key: str) -> dict[str, Any]:
    url = API_URL.format(model=model_name()) + f"?key={key}"
    body = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0, "responseMimeType": "application/json"},
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Gemini HTTP {exc.code}: {detail}") from exc
    try:
        text = payload["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError, TypeError) as exc:
        raise RuntimeError(f"Unexpected Gemini payload: {payload!r}") from exc
    return _extract_json(text)


def validate_candidates(parsed: dict[str, Any], refs: dict[str, str]) -> list[dict[str, Any]]:
    """Keep only candidates whose every evidence ref exists in the grounding."""
    kept: list[dict[str, Any]] = []
    for raw in parsed.get("candidates") or []:
        if not isinstance(raw, dict) or not raw.get("treatment"):
            continue
        evidence = []
        ok = True
        for e in raw.get("evidence") or []:
            ref = (e or {}).get("ref")
            if ref not in refs:
                ok = False
                break
            evidence.append({"type": (e or {}).get("type") or "source", "ref": ref})
        if not ok or not evidence:
            continue  # ungrounded candidate is dropped, not shown
        kept.append(
            {
                "treatment": str(raw["treatment"]).strip(),
                "classification": raw.get("classification") or None,
                "account": str(raw["account"]).strip() if raw.get("account") else None,
                "project_code": raw.get("project_code") or None,
                "rationale": (raw.get("rationale") or "").strip(),
                "evidence": evidence,
            }
        )
        if len(kept) == MAX_CANDIDATES:
            break
    return kept


def draft_candidates(canonical: dict[str, Any], case_id: str) -> dict[str, Any]:
    """Return a Case.suggestion payload: {candidates, candidates_note, drafted_by, model, drafted_at}."""
    key = api_key()
    if not key:
        raise RuntimeError("GOOGLE_API_KEY not set. Add it to .env (Google AI Studio API key).")
    grounding = build_grounding(canonical, case_id)
    parsed = _call_gemini(_prompt(grounding), key)
    candidates = validate_candidates(parsed, grounding["refs"])
    if len(candidates) < MIN_CANDIDATES:
        raise RuntimeError(
            f"only {len(candidates)} grounded candidate(s) survived evidence validation; nothing recorded"
        )
    return {
        "candidates": candidates,
        "candidates_note": (parsed.get("note") or "").strip() or None,
        "drafted_by": "assistant",
        "model": model_name(),
        "drafted_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "grounding_refs": sorted(grounding["refs"]),
    }
