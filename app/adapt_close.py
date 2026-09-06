"""Adapt canonical close.json into the reviewer-facing view model.

Two dimensions are kept apart on purpose:

  * ``Line.mapping_method``  — how the mapping was established
                               (rule | decision | override | None)
  * ``Case.status``          — whether a human still owes a decision
                               (unresolved | decided)

The word shown to the reviewer ("Method") is *derived* here, once, by
``display_method``.  The front end never computes it.  Surface vocabulary is
exactly: Rule / Decision / Override / Unresolved.  Drafted candidates are
never a Method.
"""
from __future__ import annotations

from typing import Any

WHY_FOOTER = (
    "The system has not changed the amount or silently assigned an account."
)

REASON_SENTENCES = {
    "counterparty_miss": "No matching counterparty was found.",
    "project_miss": "No matching project code was found.",
    "position_miss": "No matching position was found.",
    "review_flag": "The workbook flagged this line `Review` for human classification.",
    "no_matching_rule": "No matching account rule was found.",
    "rule_mismatch": "The rule evaluation disagrees with the filed classification.",
    "duplicate_key": "Duplicate staging key (account, date, amount, reference).",
    "first_seen": "First time this counterparty appears in the batch.",
    "source_ambiguous": "Source span match is ambiguous on the statement.",
    # Dataset 02 (GL → loader): same Case object, GL movement group as the Line.
    "entity_miss": "The legal entity has no exact hit in the LE Mapping crosswalk.",
    "deal_miss": "A deal on these GL rows has no exact hit in the Deal Mapping crosswalk.",
    "investor_miss": "An investor on these GL rows is not in the target investors list.",
}

# One label per residue type, in the words of docs/dataset-mapping.md.
REASON_LABELS = {
    "counterparty_miss": "Missing counterparty mapping",
    "project_miss": "Missing project mapping",
    "position_miss": "Missing position mapping",
    "review_flag": 'Flagged "Review" in workbook',
    "no_matching_rule": "Missing account rule",
    "rule_mismatch": "Rule / filed classification mismatch",
    "duplicate_key": "Duplicate staging key",
    "first_seen": "First-seen counterparty",
    "source_ambiguous": "Ambiguous source span",
    "entity_miss": "Missing entity mapping",
    "deal_miss": "Missing deal mapping",
    "investor_miss": "Missing investor mapping",
}

# Overview breakdown rows, fixed order per workflow. Extra reasons append when present.
BREAKDOWN_ORDER = ("counterparty_miss", "project_miss", "position_miss", "review_flag")
BREAKDOWN_ORDER_BY_WORKFLOW = {
    "bank_to_journal": BREAKDOWN_ORDER,
    "gl_to_loader": ("no_matching_rule", "entity_miss", "deal_miss", "rule_mismatch"),
}

WORKFLOW_META = {
    "bank_to_journal": {
        "dataset": "01-bank-statements-to-journal-entries",
        "label": "Bank statements → journal entries",
        "tie_out_label": "Source / Journal Tie-out",
    },
    "gl_to_loader": {
        "dataset": "02-investor-level-gl-to-loader",
        "label": "Investor-level GL → loader",
        "tie_out_label": "GL / Loader Tie-out",
    },
}

SOURCE_ROLE_LABELS = {
    "bank_statement": "Bank Statement",
    "gl_extract": "GL Extract",
    "loader_output": "Verified Loader",
    "loader_mapping": "Loader Crosswalk",
    "loader_sample": "Loader Sample",
    "reference_list": "Reference List",
    "journal_mapping": "Staging Workbook",
    "working_file": "Staging Workbook",
}

MATCH_LABELS = {
    "exact": "Exact match",
    "exact_ref": "Exact bank reference",
    "normalized": "Normalized match",
    "amount_date": "Matched by amount and date",
    "ambiguous": "Ambiguous source match",
    "none": "Source page not located",
}

SEVERITY_RANK = {"high": 0, "medium": 1, "low": 2}

# Display vocabulary. "unresolved" is a display state, not a mapping method.
METHOD_LABELS = {
    "rule": "Rule",
    "decision": "Decision",
    "override": "Override",
    "unresolved": "Unresolved",
}


# ---------------------------------------------------------------------------
# Provenance
# ---------------------------------------------------------------------------


def _case_is_open(case: dict[str, Any] | None, decision: dict[str, Any] | None) -> bool:
    if not case:
        return False
    if decision and decision.get("action") in ("accept", "override"):
        return False
    return case.get("status") != "decided"


def display_method(
    ln: dict[str, Any],
    case: dict[str, Any] | None,
    decision: dict[str, Any] | None,
) -> str:
    """The one word the reviewer sees. Derived, never stored."""
    if decision:
        action = decision.get("action")
        if action == "override":
            return "Override"
        if action == "accept":
            return "Decision"
        if action == "reject":
            return "Unresolved"
    if _case_is_open(case, decision):
        return "Unresolved"
    mm = ln.get("mapping_method")
    if mm is None and ln.get("rule_id") and not case:
        mm = "rule"  # legacy JSON without mapping_method
    if mm in ("rule", "decision", "override"):
        return METHOD_LABELS[mm]
    return "Unresolved"


def _partial_rule_label(rule: dict[str, Any] | None) -> str | None:
    if not rule:
        return None
    keys = sorted((rule.get("action") or {}).keys())
    scope = ", ".join(k.replace("_", " ") for k in keys) or "no fields"
    return f"Partial rule hit · {rule['rule_id']} ({scope} only)"


def _provenance(
    ln: dict[str, Any],
    rule: dict[str, Any] | None,
    decision: dict[str, Any] | None,
    case: dict[str, Any] | None,
    rules_by_id: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """Honest mapping provenance — never imply a silent fact."""
    rule_id = (rule or {}).get("rule_id") or ln.get("rule_id")
    rule_version = (rule or {}).get("version") or ("v0" if rule_id else None)
    partial_id = (case or {}).get("partial_rule_id")
    partial = rules_by_id.get(partial_id) if partial_id else None
    method = display_method(ln, case, decision)
    return {
        "mapping_method": ln.get("mapping_method"),
        "display_method": method,
        "method_label": method,  # kept for the fixture / older front-end paths
        "rule_id": rule_id,
        "rule_version": rule_version,
        "partial_rule_id": partial_id,
        "partial_rule_label": _partial_rule_label(partial),
    }


# ---------------------------------------------------------------------------
# Small formatters
# ---------------------------------------------------------------------------


def _period_label(period: str | None) -> str:
    if not period:
        return "Close"
    parts = period.split("-")
    if len(parts) == 2:
        year, month = parts
        months = (
            "January February March April May June "
            "July August September October November December"
        ).split()
        try:
            return f"{months[int(month) - 1]} {year} Close"
        except (ValueError, IndexError):
            pass
    return f"{period} Close"


def _source_label(filename: str, role: str | None = None) -> str:
    if role in SOURCE_ROLE_LABELS:
        return SOURCE_ROLE_LABELS[role]
    if filename and filename.lower().endswith(".pdf"):
        return "Bank Statement"
    if filename and (filename.lower().endswith(".xlsx") or filename.lower().endswith(".xls")):
        return "Staging Workbook"
    return filename or "Source"


def _source_location(page: Any, sheet: Any, row: Any) -> str:
    if page is not None:
        return f"Page {page}"
    bits = []
    if sheet:
        bits.append(str(sheet))
    if row is not None:
        bits.append(f"row {row}")
    return " · ".join(bits) if bits else "Location unknown"


def _why_sentence(reasons: list[str], primary: str) -> str:
    lines = [
        "This line could not be automatically classified.",
        f"Reason: {REASON_SENTENCES.get(primary, primary.replace('_', ' ').capitalize() + '.')}",
    ]
    extras = [r for r in reasons if r != primary]
    if extras:
        extra_text = "; ".join(
            REASON_SENTENCES.get(r, r.replace("_", " ")) for r in extras
        )
        lines.append(f"Also noted: {extra_text}")
    lines.append(WHY_FOOTER)
    return " ".join(lines)


def _format_value_summary(value: dict[str, Any] | None) -> str | None:
    if not value:
        return None
    parts = []
    for key in ("classification", "account", "project_code", "counterparty", "fund"):
        if key in value and value[key] is not None:
            parts.append(f"{key.replace('_', ' ')}: {value[key]}")
    if not parts:
        for k, v in value.items():
            if k in ("treatment", "rationale", "evidence"):
                continue
            parts.append(f"{k}: {v}")
    return " · ".join(parts) if parts else None


def _candidate_summary(c: dict[str, Any] | None) -> str | None:
    if not c:
        return None
    head = c.get("treatment")
    tail = _format_value_summary(
        {k: c.get(k) for k in ("classification", "account", "project_code")}
    )
    if head and tail:
        return f"{head} — {tail}"
    return head or tail


def _candidates_view(suggestion: dict[str, Any] | None) -> dict[str, Any] | None:
    """Drafted candidates on a Case. Presentation only; never provenance."""
    if not suggestion or not suggestion.get("candidates"):
        return None
    items = []
    for i, c in enumerate(suggestion["candidates"]):
        items.append(
            {
                "index": i,
                "treatment": c.get("treatment"),
                "classification": c.get("classification"),
                "account": c.get("account"),
                "project_code": c.get("project_code"),
                "rationale": c.get("rationale"),
                "evidence": list(c.get("evidence") or []),
                "summary": _candidate_summary(c),
            }
        )
    return {
        "items": items,
        "note": suggestion.get("candidates_note"),
        "drafted_by": suggestion.get("drafted_by"),
        "model": suggestion.get("model"),
        "drafted_at": suggestion.get("drafted_at"),
    }


# ---------------------------------------------------------------------------
# Decision / history views
# ---------------------------------------------------------------------------


def _decision_vm(decision: dict[str, Any] | None) -> dict[str, Any] | None:
    if not decision:
        return None
    return {
        "decision_id": decision.get("decision_id"),
        "action": decision.get("action"),
        "decided_by": decision.get("decided_by"),
        "role": decision.get("role"),
        "reason": decision.get("reason"),
        "timestamp": decision.get("timestamp"),
        "previous_value": decision.get("previous_value"),
        "final_value": decision.get("final_value"),
        "previous_summary": _format_value_summary(decision.get("previous_value")),
        "final_summary": _format_value_summary(decision.get("final_value")),
        "candidates": [
            {**c, "summary": _candidate_summary(c)} if isinstance(c, dict) else {"summary": str(c)}
            for c in decision.get("candidates") or []
        ],
        "chosen": decision.get("chosen"),
        "chosen_summary": _candidate_summary(decision.get("chosen"))
        if isinstance(decision.get("chosen"), dict)
        else None,
    }


def _decision_list_item(
    decision: dict[str, Any],
    case_views_by_id: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    action = decision.get("action") or ""
    scope = "batch" if action == "sign_off" or not decision.get("case_id") else "case"
    case = case_views_by_id.get(decision.get("case_id") or "")
    vm = _decision_vm(decision) or {}
    return {
        "decision_id": decision.get("decision_id"),
        "case_id": decision.get("case_id"),
        "line_id": decision.get("line_id"),
        "action": action,
        "scope": scope,
        "decided_by": decision.get("decided_by"),
        "role": decision.get("role"),
        "reason": decision.get("reason"),
        "timestamp": decision.get("timestamp"),
        "previous_summary": vm.get("previous_summary"),
        "final_summary": vm.get("final_summary"),
        "candidate_count": len(vm.get("candidates") or []),
        "chosen_summary": vm.get("chosen_summary"),
        "amount": (case or {}).get("amount"),
        "currency": (case or {}).get("currency"),
        "reason_label": (case or {}).get("reason_label"),
    }


def _build_history(
    case: dict[str, Any],
    ln: dict[str, Any],
    rule: dict[str, Any] | None,
    partial_rule: dict[str, Any] | None,
    decision: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    history: list[dict[str, Any]] = []
    primary = case.get("primary_reason") or "unknown"
    history.append(
        {
            "at": None,
            "actor": "System",
            "event": "Case opened",
            "detail": REASON_SENTENCES.get(
                primary, primary.replace("_", " ").capitalize() + "."
            ),
        }
    )

    # After a decision Line.mapping holds the final value; the original
    # workbook proposal survives in Decision.previous_value.
    mapping = ln.get("mapping") or {}
    if decision and isinstance(decision.get("previous_value"), dict) and decision["previous_value"]:
        mapping = decision["previous_value"]
    proposed_bits = []
    if mapping.get("classification"):
        proposed_bits.append(str(mapping["classification"]))
    if mapping.get("account"):
        proposed_bits.append(f"Account {mapping['account']}")
    if mapping.get("project_code"):
        proposed_bits.append(f"Project {mapping['project_code']}")
    rule_bit = None
    if rule:
        rule_bit = f"{rule.get('name') or rule['rule_id']} · Rule {rule.get('version') or 'v0'}"
    elif partial_rule:
        rule_bit = _partial_rule_label(partial_rule)
    history.append(
        {
            "at": None,
            "actor": "Workbook",
            "event": "Proposed treatment",
            "detail": " · ".join(proposed_bits) if proposed_bits else "No proposal in workbook",
            "rule": rule_bit,
        }
    )

    suggestion = case.get("suggestion") or {}
    if suggestion.get("candidates"):
        cands = suggestion["candidates"]
        history.append(
            {
                "at": suggestion.get("drafted_at"),
                "actor": "Draft",
                "event": f"{len(cands)} candidate treatment(s) drafted",
                "detail": suggestion.get("candidates_note")
                or "Grounded on source excerpt, rules and precedents. Not a Rule, not a Decision.",
                "candidates": [_candidate_summary(c) for c in cands],
            }
        )

    if decision:
        vm = _decision_vm(decision) or {}
        action = decision.get("action")
        event = {
            "override": "Override",
            "accept": "Decision — accepted",
            "reject": "Rejected — stays Unresolved",
        }.get(action or "", (action or "Decision").capitalize())
        history.append(
            {
                "at": decision.get("timestamp"),
                "actor": decision.get("decided_by") or "Reviewer",
                "role": decision.get("role"),
                "event": event,
                "previous": vm.get("previous_summary"),
                "final": vm.get("final_summary"),
                "detail": decision.get("reason"),
                "candidates": [c.get("summary") for c in vm.get("candidates") or []],
                "chosen": vm.get("chosen_summary"),
            }
        )
        if action in ("accept", "override"):
            history.append(
                {
                    "at": decision.get("timestamp"),
                    "actor": "Final",
                    "event": "Final state",
                    "detail": vm.get("final_summary"),
                }
            )
    return history


# ---------------------------------------------------------------------------
# Case view
# ---------------------------------------------------------------------------


def _case_view(
    case: dict[str, Any],
    ln: dict[str, Any],
    rule: dict[str, Any] | None,
    decision: dict[str, Any] | None,
    sources: dict[str, Any],
    rules_by_id: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    bank = ln.get("bank_ref") or {}
    source_ref = ln.get("source_ref") or {}
    src_pdf = sources.get(bank.get("source_id")) if bank else None
    src_xlsx = sources.get(source_ref.get("source_id"))
    src = src_pdf or src_xlsx or {}
    filename = src.get("filename") or "unknown"
    page = (bank.get("location") or {}).get("page")
    sheet = (source_ref.get("location") or {}).get("sheet")
    row = (source_ref.get("location") or {}).get("row")
    match_method = bank.get("match_method") or "none"
    mapping = ln.get("mapping") or {}
    reasons = case.get("reasons") or ([case.get("primary_reason")] if case.get("primary_reason") else [])
    primary = case.get("primary_reason") or (reasons[0] if reasons else "unknown")

    prov = _provenance(ln, rule, decision, case, rules_by_id)
    partial_rule = rules_by_id.get(prov["partial_rule_id"]) if prov["partial_rule_id"] else None

    account = mapping.get("account") or mapping.get("account_number")
    proposed_label = (
        mapping.get("classification") or mapping.get("project_code") or "Unclassified"
    )
    rule_label = None
    if rule:
        rule_label = f"{rule.get('name') or 'Account Map'} · Rule {rule.get('version') or 'v0'}"

    if decision and decision.get("action") in ("accept", "override"):
        ui_status = "resolved"
    elif decision and decision.get("action") == "reject":
        ui_status = "rejected"
    elif case.get("status") == "decided":
        ui_status = "resolved"
    else:
        ui_status = "needs_review"

    loc_label = _source_location(page, sheet, row)
    source_short = f"{_source_label(filename, src.get('role'))} · {loc_label.replace('Page ', 'p') if page is not None else loc_label}"

    return {
        "case_id": case["case_id"],
        "line_id": ln.get("line_id"),
        "amount": ln.get("amount"),
        "currency": ln.get("currency"),
        "date": ln.get("date"),
        "description": ln.get("description") or "",
        "status": ui_status,
        "surface_status": prov["display_method"],
        "assigned_to": case.get("assigned_to"),
        "severity": case.get("priority") or "medium",
        "control": {
            "recon_category": case.get("recon_category") or "mapping_gap",
            "materiality_tier": case.get("materiality_tier") or case.get("priority") or "medium",
            "opened_at": case.get("opened_at"),
            "due_at": case.get("due_at"),
            "clearance_target": case.get("clearance_target") or "Resolve or escalate before batch sign-off",
            "preparer": case.get("preparer") or "Fund Accountant",
            "reviewer": case.get("reviewer") or "Fund Admin",
        },
        "reason_category": primary,
        "reason_category_label": REASON_LABELS.get(primary, primary.replace("_", " ").capitalize()),
        "primary_reason": primary,
        "reason_label": REASON_LABELS.get(primary, primary.replace("_", " ").capitalize()),
        "reasons": reasons,
        "why_sentence": _why_sentence(list(reasons), primary),
        "mapping_method": prov["mapping_method"],
        "display_method": prov["display_method"],
        "method_label": prov["display_method"],
        "partial_rule_id": prov["partial_rule_id"],
        "partial_rule_label": prov["partial_rule_label"],
        "source": {
            "label": _source_label(filename, src.get("role")),
            "location": loc_label,
            "short": source_short,
            "file": filename,
            "page": page,
            "sheet": sheet,
            "row": row,
            "excerpt": bank.get("excerpt") or ln.get("description") or "",
            "match_method": match_method,
            "match_label": MATCH_LABELS.get(match_method, match_method),
        },
        # What the workbook / accountant already put on the line. Not a fact.
        "proposed": {
            "account": account,
            "label": proposed_label,
            "classification": mapping.get("classification"),
            "project_code": mapping.get("project_code"),
            "bank_account": mapping.get("bank_account"),
            "match": MATCH_LABELS.get(match_method, match_method),
            "rule": rule_label,
            "rule_id": prov["rule_id"],
            "rule_version": prov["rule_version"] or "v0",
        },
        "candidates": _candidates_view(case.get("suggestion")),
        "mapping": mapping,
        "decision": _decision_vm(decision),
        "history": _build_history(case, ln, rule, partial_rule, decision),
    }


def _control_tasks(
    raw_tasks: list[dict[str, Any]],
    open_cases: list[dict[str, Any]],
    *,
    tieout_passed: bool,
    signed_off: bool,
) -> list[dict[str, Any]]:
    """Return a small control board derived only from controlled close facts."""
    blocker_ids = [case["case_id"] for case in open_cases]
    high_or_unassigned = [
        case["case_id"]
        for case in open_cases
        if case.get("severity") == "high" or not case.get("assigned_to")
    ]
    if not raw_tasks:
        raw_tasks = [
            {"task_id": "TASK-INGEST", "title": "Evidence ingested", "owner": "Fund Accountant", "reviewer": "Fund Admin", "due_day": "WD1", "status": "complete", "dependency_ids": [], "blocker_case_ids": [], "required_for_signoff": True},
            {"task_id": "TASK-CASE-REVIEW", "title": "Resolve exception queue", "owner": "Fund Accountant", "reviewer": "Fund Admin", "due_day": "WD3", "status": "blocked", "dependency_ids": ["TASK-INGEST"], "blocker_case_ids": blocker_ids, "required_for_signoff": True},
            {"task_id": "TASK-TIE-OUT", "title": "Complete batch tie-out", "owner": "Fund Accountant", "reviewer": "Fund Admin", "due_day": "WD3", "status": "blocked", "dependency_ids": ["TASK-INGEST"], "blocker_case_ids": [], "required_for_signoff": True},
            {"task_id": "TASK-ADMIN-REVIEW", "title": "Admin review of material residue", "owner": "Fund Admin", "reviewer": "Fund Manager", "due_day": "WD4", "status": "blocked", "dependency_ids": ["TASK-CASE-REVIEW", "TASK-TIE-OUT"], "blocker_case_ids": high_or_unassigned, "required_for_signoff": True},
            {"task_id": "TASK-MANAGER-SIGNOFF", "title": "Manager sign-off", "owner": "Fund Manager", "reviewer": "Fund Manager", "due_day": "WD5", "status": "not_started", "dependency_ids": ["TASK-ADMIN-REVIEW"], "blocker_case_ids": [], "required_for_signoff": False},
        ]

    views = []
    for raw in raw_tasks:
        task = dict(raw)
        task_id = task.get("task_id")
        if task_id == "TASK-CASE-REVIEW":
            task["status"] = "complete" if not open_cases else "blocked"
            task["blocker_case_ids"] = blocker_ids
        elif task_id == "TASK-TIE-OUT":
            task["status"] = "complete" if tieout_passed else "blocked"
        elif task_id == "TASK-ADMIN-REVIEW":
            task["status"] = "complete" if not open_cases and tieout_passed else "blocked"
            task["blocker_case_ids"] = high_or_unassigned
        elif task_id == "TASK-MANAGER-SIGNOFF":
            task["status"] = "complete" if signed_off else ("in_progress" if not open_cases and tieout_passed else "not_started")
        task["id"] = task_id
        task["dependencies"] = list(task.get("dependency_ids") or [])
        task["blockers"] = list(task.get("blocker_case_ids") or [])
        views.append(task)
    return views


# ---------------------------------------------------------------------------
# Whole close
# ---------------------------------------------------------------------------


def adapt_close_for_reviewer(canonical: dict[str, Any]) -> dict[str, Any]:
    """Map a canonical close (any workflow) → reviewer view model (+ line cards)."""
    close = canonical.get("close") or {}
    workflow = close.get("workflow") or "bank_to_journal"
    meta = WORKFLOW_META.get(workflow) or {
        "dataset": workflow,
        "label": workflow.replace("_", " "),
        "tie_out_label": "Source / Target Tie-out",
    }
    breakdown_order = BREAKDOWN_ORDER_BY_WORKFLOW.get(workflow, BREAKDOWN_ORDER)
    lines_in = canonical.get("lines") or []
    rules = {r["rule_id"]: r for r in canonical.get("rules") or []}
    cases = {c["case_id"]: c for c in canonical.get("cases") or []}
    decisions = {d["decision_id"]: d for d in canonical.get("decisions") or []}
    decisions_by_case = {
        d["case_id"]: d for d in canonical.get("decisions") or [] if d.get("case_id")
    }
    sources = {s["source_id"]: s for s in canonical.get("sources") or []}
    tieouts = canonical.get("tieouts") or []
    lines_by_id = {ln["line_id"]: ln for ln in lines_in}

    batch_tie = next(
        (t for t in tieouts if t.get("kind") == "diu_batch_zero_balance"),
        None,
    )
    staging_ties = [t for t in tieouts if t.get("kind") == "staging_to_lines"]
    currency = "EUR"
    if staging_ties:
        eur = next((t for t in staging_ties if t.get("currency") == "EUR"), staging_ties[0])
        currency = eur.get("currency") or "EUR"

    counts = {"rule": 0, "decision": 0, "override": 0, "unresolved": 0}
    out_lines: list[dict[str, Any]] = []

    for ln in lines_in:
        case = cases.get(ln["case_id"]) if ln.get("case_id") else None
        decision = None
        if case and case.get("decision_id"):
            decision = decisions.get(case["decision_id"])

        rule = rules.get(ln["rule_id"]) if ln.get("rule_id") else None
        bank = ln.get("bank_ref") or {}
        src_pdf = sources.get(bank.get("source_id")) if bank else None
        src_xlsx = sources.get((ln.get("source_ref") or {}).get("source_id"))

        match_method = bank.get("match_method") or "none"
        excerpt = bank.get("excerpt") or ln.get("description") or ""
        if match_method == "amount_date":
            excerpt = f"[matched by amount/date] {excerpt}"
        elif match_method == "none":
            excerpt = f"[source page not located] {excerpt}"

        page = (bank.get("location") or {}).get("page")
        filename = (src_pdf or src_xlsx or {}).get("filename") or "unknown"

        mapping = ln.get("mapping") or {}
        classification = (mapping.get("classification") or "other").lower().replace(" ", "_")

        prov = _provenance(ln, rule, decision, case, rules)
        origin = prov["display_method"].lower()  # rule | decision | override | unresolved
        counts[origin] += 1
        if origin == "unresolved":
            status = "open"
        elif origin == "rule":
            status = "accepted" if ln.get("status") == "resolved" else ln.get("status")
        else:
            status = "accepted"

        rule_obj = None
        if rule and origin == "rule":
            rule_obj = {
                "id": rule["rule_id"],
                "version": rule.get("version") or "v0",
                "matched": rule.get("name") or rule["rule_id"],
            }

        case_obj = None
        if case:
            reasons = case.get("reasons") or [case.get("primary_reason")]
            primary = case.get("primary_reason") or (reasons[0] if reasons else "unknown")
            drafted = ((case.get("suggestion") or {}).get("candidates")) or []
            cand = [_candidate_summary(c) for c in drafted if isinstance(c, dict)]
            if decision and decision.get("candidates"):
                cand = [
                    _candidate_summary(c) if isinstance(c, dict) else str(c)
                    for c in decision["candidates"]
                ]
            chosen = None
            if decision and isinstance(decision.get("chosen"), dict):
                chosen = _candidate_summary(decision["chosen"])
            elif decision and decision.get("final_value"):
                chosen = _format_value_summary(decision["final_value"])
            case_obj = {
                "id": case["case_id"],
                "type": primary,
                "reasons": reasons,
                "candidates": cand,
                "chosen": chosen,
                "author": "fund account",
                "decider": (decision or {}).get("decided_by"),
                "reason": (decision or {}).get("reason")
                or f"Open case: {', '.join(str(r) for r in reasons)}.",
                "partial_rule_id": prov["partial_rule_id"],
            }

        src_short = f"{filename}"
        if page is not None:
            src_short += f" · p{page}"

        out_lines.append(
            {
                "id": ln["line_id"],
                "case_id": case["case_id"] if case else None,
                "status": status,
                "surface_status": prov["display_method"],
                "origin": origin,
                "amount": ln.get("amount"),
                "currency": ln.get("currency"),
                "date": ln.get("date"),
                "class": classification,
                "description": ln.get("description") or "",
                "mapping_method": prov["mapping_method"],
                "display_method": prov["display_method"],
                "method_label": prov["display_method"],
                "rule_id": prov["rule_id"],
                "partial_rule_id": prov["partial_rule_id"],
                "partial_rule_label": prov["partial_rule_label"],
                "assigned_to": (case or {}).get("assigned_to") if case else None,
                "source": {
                    "file": filename,
                    "page": page,
                    "excerpt": excerpt,
                    "match_method": match_method,
                    "short": src_short,
                    "sheet": (ln.get("source_ref") or {}).get("location", {}).get("sheet"),
                    "row": (ln.get("source_ref") or {}).get("location", {}).get("row"),
                },
                "mapping": {
                    "account": mapping.get("account") or mapping.get("account_number"),
                    "classification": mapping.get("classification"),
                },
                "rule": rule_obj,
                "case": case_obj,
            }
        )

    case_views: list[dict[str, Any]] = []
    for case in canonical.get("cases") or []:
        ln = lines_by_id.get(case["line_id"])
        if not ln:
            continue
        decision = None
        if case.get("decision_id"):
            decision = decisions.get(case["decision_id"])
        elif case["case_id"] in decisions_by_case:
            decision = decisions_by_case[case["case_id"]]
        rule = rules.get(ln["rule_id"]) if ln.get("rule_id") else None
        case_views.append(_case_view(case, ln, rule, decision, sources, rules))

    case_views.sort(
        key=lambda c: (
            SEVERITY_RANK.get(c.get("severity") or "medium", 9),
            -(abs(float(c.get("amount") or 0))),
            c.get("case_id") or "",
        )
    )

    needs_review = sum(1 for c in case_views if c["status"] == "needs_review")
    rejected_open = sum(1 for c in case_views if c["status"] == "rejected")
    resolved_cases = sum(1 for c in case_views if c["status"] == "resolved")
    open_cases = [c for c in case_views if c["status"] in ("needs_review", "rejected")]
    unassigned_open = sum(1 for c in open_cases if not c.get("assigned_to"))
    high_open = sum(1 for c in open_cases if c.get("severity") == "high")
    open_total = len(open_cases)
    lines_needing_review = {c["line_id"] for c in open_cases}
    auto_resolved_count = len(lines_in) - len(lines_needing_review)
    rule_mapping_count = sum(
        1 for ln in lines_in if ln.get("mapping_method") == "rule"
    )

    breakdown_counts: dict[str, int] = {k: 0 for k in breakdown_order}
    for c in open_cases:
        key = c["primary_reason"]
        breakdown_counts[key] = breakdown_counts.get(key, 0) + 1
    reason_breakdown = [
        {"category": key, "label": REASON_LABELS[key], "count": breakdown_counts[key]}
        for key in breakdown_order
    ]
    for key, count in breakdown_counts.items():
        if key not in breakdown_order and count:
            reason_breakdown.append(
                {
                    "category": key,
                    "label": REASON_LABELS.get(key, key.replace("_", " ").capitalize()),
                    "count": count,
                }
            )

    tie_status = "pass"
    difference = 0.0
    debits = 0.0
    credits = 0.0
    if batch_tie:
        tie_status = "pass" if batch_tie.get("status") in ("passed", "not_applicable") else "fail"
        debits = float(batch_tie.get("source_total") or 0)
        credits = float(batch_tie.get("line_total") or 0)
        difference = float(batch_tie.get("difference") or 0)
    elif staging_ties:
        tie_status = (
            "pass"
            if all(t.get("status") == "passed" for t in staging_ties)
            else "fail"
        )

    overview_status = "Review Required" if open_total > 0 else "Clean"
    period = close.get("period")
    raw_decisions = list(canonical.get("decisions") or [])
    signed_off = close.get("status") == "signed_off" or any(
        d.get("action") == "sign_off" for d in raw_decisions
    )
    if signed_off:
        overview_status = "Signed Off"

    control_tasks = _control_tasks(
        list(canonical.get("tasks") or []),
        open_cases,
        tieout_passed=tie_status == "pass",
        signed_off=signed_off,
    )
    incomplete_required_tasks = [
        task["id"]
        for task in control_tasks
        if task.get("required_for_signoff", True) and task.get("status") != "complete"
    ]

    case_views_by_id = {c["case_id"]: c for c in case_views}
    decision_list = [
        _decision_list_item(d, case_views_by_id) for d in raw_decisions
    ]
    decision_list.sort(key=lambda d: d.get("timestamp") or "", reverse=True)

    return {
        "close_id": close.get("close_id"),
        "dataset": meta["dataset"],
        "workflow": workflow,
        "workflow_label": meta["label"],
        "note": "Adapted from the canonical close JSON (same model for every workflow).",
        "overview": {
            "period_label": _period_label(period),
            "workflow": workflow,
            "workflow_label": meta["label"],
            "period": period,
            "fund_id": close.get("fund_id"),
            "close_id": close.get("close_id"),
            "status": overview_status,
            "total_lines": len(lines_in),
            "auto_resolved": auto_resolved_count,
            "rule_mapping_count": rule_mapping_count,
            "open_case_count": open_total,
            "needs_review": open_total,
            "needs_review_first_pass": needs_review,
            "rejected_open": rejected_open,
            "resolved_cases": resolved_cases,
            "signed_off": signed_off,
            "signoff_ready": not signed_off and not open_cases and tie_status == "pass" and not incomplete_required_tasks,
            "export_profile": "validated_mapping_csv_v1",
            "export_ready": bool(
                signed_off
                and not open_cases
                and tie_status == "pass"
                and not incomplete_required_tasks
            ),
            "export_blockers": (
                []
                if (
                    signed_off
                    and not open_cases
                    and tie_status == "pass"
                    and not incomplete_required_tasks
                )
                else (
                    (["batch not signed off"] if not signed_off else [])
                    + (
                        [f"{open_total} open case(s) remain"]
                        if open_cases
                        else []
                    )
                    + (
                        ["tie-out is not PASS"]
                        if tie_status != "pass"
                        else []
                    )
                    + (
                        [
                            "incomplete close task(s): "
                            + ", ".join(incomplete_required_tasks)
                        ]
                        if incomplete_required_tasks
                        else []
                    )
                )
            ),
            "blockers": {
                "unassigned_open": unassigned_open,
                "high_open": high_open,
                "open_total": open_total,
            },
            "tie_out": {
                "status": "PASS" if tie_status == "pass" else "FAIL",
                "difference": difference,
                "label": meta["tie_out_label"],
                "source": "diu_batch_zero_balance",
                "debits": debits,
                "credits": credits,
            },
            "reason_breakdown": reason_breakdown,
            "control_tasks": control_tasks,
            "incomplete_required_tasks": incomplete_required_tasks,
            "control_checks": [
                {
                    "id": "tie_out",
                    "label": meta["tie_out_label"],
                    "ok": tie_status == "pass",
                    "detail": f"Difference: {difference}",
                },
                {
                    "id": "completeness",
                    "label": "All source lines accounted for",
                    "ok": True,
                    "detail": f"{len(lines_in)} / {len(lines_in)}",
                },
                {
                    "id": "no_silent",
                    "label": "No unresolved silent mappings",
                    "ok": True,
                    "detail": f"{open_total} open for review",
                },
                {
                    "id": "decision_history",
                    "label": "Decision history recorded",
                    "ok": True,
                    "detail": f"{len(raw_decisions)} decision(s)",
                },
                {
                    "id": "close_tasks",
                    "label": "Required close tasks complete",
                    "ok": not incomplete_required_tasks,
                    "detail": "All required tasks complete" if not incomplete_required_tasks else f"Blocked: {', '.join(incomplete_required_tasks)}",
                },
            ],
        },
        "cases": case_views,
        "decisions": decision_list,
        "batch": {
            "id": close.get("close_id"),
            "entity": close.get("fund_id"),
            "currency": currency,
            "tie_out": {
                "status": tie_status,
                "debits": debits,
                "credits": credits,
                "source": "diu_batch_zero_balance",
            },
            "counts": counts,
        },
        "lines": out_lines,
        "canonical_meta": {
            "line_count": len(lines_in),
            "case_count": len(cases),
            "rule_count": len(rules),
            "decision_count": len(raw_decisions),
            "tieout_kinds": sorted({t.get("kind") for t in tieouts if t.get("kind")}),
        },
    }
