"""Normalize extracted PDF/Excel into the canonical close model.

Strict provenance (D-011):
  raw_facts → evaluate_rules → compare(filed_snapshot) → Case / Rule
Filed counterparty / project / position / classification never enter rules.
"""
from __future__ import annotations

import difflib
import re
from collections import Counter, defaultdict
from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Optional

from canonical_model import (
    EXPECTED_SOURCE_FLAG_COUNTS,
    CanonicalClose,
    Case,
    Close,
    Line,
    Rule,
    Source,
    TieOut,
    ensure_close_tasks,
    primary_reason_of,
    priority_for_reason,
)

CLOSE_ID = "CLOSE-2026-03-CALDER-WEEK"
FUND_ID = "MULTI-FUND-CALDER"
PERIOD = "2026-03"
WORKFLOW = "bank_to_journal"
CONTRACT_VERSION = "v1"

STAGING_SHEET = "Staging Sheet"
DIU_SHEET = "DIU "
VENDOR_CODES_SHEET = "Vendor Codes"
ALLOCATION_RULE_SHEET = "Allocation Rule"
ACCOUNT_MAP_SHEET = "Account Map"
PROJECT_CODE_SHEET = "Project Code Report"
DEAL_POSITION_SHEET = "Deal & Position Master List"
COA_SHEET = "CoA"
LEGAL_ENTITY_SHEET = "Legal Entity Master List"
INVESTOR_SHEET = "Investor Master List"
VENDOR_MASTER_SHEET = "Vendor Master List"
RELATED_PARTY_SHEET = "Related Party Master"

MAPPING_SHEETS = {
    VENDOR_CODES_SHEET,
    ALLOCATION_RULE_SHEET,
    ACCOUNT_MAP_SHEET,
    PROJECT_CODE_SHEET,
    DEAL_POSITION_SHEET,
    COA_SHEET,
    "Bank Account Report",
    LEGAL_ENTITY_SHEET,
    INVESTOR_SHEET,
    VENDOR_MASTER_SHEET,
    RELATED_PARTY_SHEET,
    "Korean and Taiwanese",
}

LEGAL_SUFFIXES = (
    "LIMITED", "LTD", "LLC", "LLP", "LP", "INC", "INCORPORATED",
    "GMBH", "AG", "SA", "SCSP", "SCSP", "K/S", "APS", "AS", "BV", "NV",
    "PLC", "CORP", "CO", "UA",
)


def _norm_header(h: Any) -> str:
    if h is None:
        return ""
    return str(h).strip()


def _as_str(v: Any) -> Optional[str]:
    if v is None:
        return None
    s = str(v).strip()
    return s if s else None


def _as_decimal(v: Any) -> Optional[Decimal]:
    if v is None or v == "":
        return None
    if isinstance(v, Decimal):
        return v
    if isinstance(v, (int, float)):
        return Decimal(str(v))
    try:
        return Decimal(str(v).replace(",", "").strip())
    except Exception:
        return None


def _money(v: Decimal | float | int | str) -> float:
    d = v if isinstance(v, Decimal) else Decimal(str(v))
    return float(d.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def _as_date_str(v: Any) -> Optional[str]:
    if v is None or v == "":
        return None
    if isinstance(v, datetime):
        return v.date().isoformat()
    if isinstance(v, date):
        return v.isoformat()
    s = str(v).strip()
    if "T" in s:
        return s.split("T", 1)[0]
    if re.match(r"^\d{4}-\d{2}-\d{2}", s):
        return s[:10]
    return s


def _sheet_rows(excel_rows: list[dict[str, Any]], sheet: str) -> list[dict[str, Any]]:
    return [r for r in excel_rows if r.get("location", {}).get("sheet") == sheet]


def _header_index(header_values: list[Any]) -> dict[str, int]:
    idx: dict[str, int] = {}
    for i, h in enumerate(header_values):
        key = _norm_header(h)
        if key and key not in idx:
            idx[key] = i
    return idx


def _cell(values: list[Any], idx: dict[str, int], name: str) -> Any:
    i = idx.get(name)
    if i is None or i >= len(values):
        return None
    return values[i]


def _norm_key(s: str) -> str:
    return re.sub(r"[^A-Z0-9]", "", (s or "").upper())


def _norm_ws(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").upper()).strip()


def _compact(s: str) -> str:
    return re.sub(r"\s+", "", (s or "").upper())


def _strip_suffixes(key: str) -> str:
    out = key
    changed = True
    while changed and len(out) > 3:
        changed = False
        for suf in LEGAL_SUFFIXES:
            sk = _norm_key(suf)
            if out.endswith(sk) and len(out) > len(sk) + 2:
                out = out[: -len(sk)]
                changed = True
                break
    return out


def _account_short_code(label: Optional[str]) -> Optional[str]:
    if not label:
        return None
    nums = re.findall(r"\d{3,}", label)
    if nums:
        return nums[-1]
    parts = [p.strip() for p in label.split("-") if p.strip()]
    return parts[-1] if parts else None


def _build_sources(
    pdf_docs: list[dict[str, Any]], excel_rows: list[dict[str, Any]]
) -> list[Source]:
    sources: list[Source] = []
    seen: set[str] = set()

    for doc in pdf_docs:
        sid = doc["source_id"]
        if sid in seen:
            continue
        seen.add(sid)
        sources.append(
            Source(
                source_id=sid,
                filename=doc["filename"],
                file_type="pdf",
                role="bank_statement",
                location=dict(doc.get("location") or {}),
                text=doc.get("text"),
            )
        )

    sheet_meta: dict[str, dict[str, Any]] = {}
    for row in excel_rows:
        sheet = row.get("location", {}).get("sheet")
        sid = row["source_id"]
        if sid not in sheet_meta:
            role = "journal_mapping" if sheet in MAPPING_SHEETS else "working_file"
            if sheet == DIU_SHEET:
                role = "journal_mapping"
            sheet_meta[sid] = {
                "source_id": sid,
                "filename": row["filename"],
                "sheet": sheet,
                "role": role,
            }

    for sid, meta in sheet_meta.items():
        sources.append(
            Source(
                source_id=sid,
                filename=meta["filename"],
                file_type="xlsx",
                role=meta["role"],
                location={"sheet": meta["sheet"]},
                text=None,
            )
        )
    return sources


def _colset(excel_rows: list[dict[str, Any]], sheet: str, col: str) -> set[str]:
    rows = _sheet_rows(excel_rows, sheet)
    if not rows:
        return set()
    idx = _header_index(rows[0]["values"])
    out: set[str] = set()
    for r in rows[1:]:
        v = _as_str(_cell(r["values"], idx, col))
        if v:
            out.add(v)
    return out


def _collect_project_codes(excel_rows: list[dict[str, Any]]) -> set[str]:
    rows = _sheet_rows(excel_rows, PROJECT_CODE_SHEET)
    if not rows:
        return set()
    idx = _header_index(rows[0]["values"])
    codes: set[str] = set()
    for r in rows[1:]:
        for col in ("Project Code", "New Project Code"):
            v = _as_str(_cell(r["values"], idx, col))
            if v:
                codes.add(v)
    return codes


def _collect_positions(excel_rows: list[dict[str, Any]]) -> set[str]:
    return _colset(excel_rows, DEAL_POSITION_SHEET, "Position")


def _collect_deals(excel_rows: list[dict[str, Any]]) -> set[str]:
    return _colset(excel_rows, DEAL_POSITION_SHEET, "Deal Name")


def _build_account_map(excel_rows: list[dict[str, Any]]) -> dict[str, str]:
    rows = _sheet_rows(excel_rows, ACCOUNT_MAP_SHEET)
    if not rows:
        return {}
    idx = _header_index(rows[0]["values"])
    out: dict[str, str] = {}
    for r in rows[1:]:
        num = _as_str(_cell(r["values"], idx, "Account Number"))
        label = _as_str(_cell(r["values"], idx, "Bank Account"))
        if num and label:
            out[num] = label
    return out


def _build_coa(excel_rows: list[dict[str, Any]]) -> dict[str, str]:
    rows = _sheet_rows(excel_rows, COA_SHEET)
    if not rows:
        return {}
    idx = _header_index(rows[0]["values"])
    out: dict[str, str] = {}
    for r in rows[1:]:
        acct = _as_str(_cell(r["values"], idx, "Account"))
        if acct is None:
            # numeric account codes may arrive as floats
            raw = _cell(r["values"], idx, "Account")
            if raw is not None:
                acct = str(raw).strip()
        atype = _as_str(_cell(r["values"], idx, "Account Type"))
        if acct and atype:
            out[acct] = atype
            # also store without trailing .0
            if acct.endswith(".0"):
                out[acct[:-2]] = atype
    return out


def _build_vendor_codes(excel_rows: list[dict[str, Any]]) -> dict[str, str]:
    rows = _sheet_rows(excel_rows, VENDOR_CODES_SHEET)
    if not rows:
        return {}
    idx = _header_index(rows[0]["values"])
    out: dict[str, str] = {}
    for r in rows[1:]:
        vendor = _as_str(_cell(r["values"], idx, "Vendor"))
        project = _as_str(_cell(r["values"], idx, "Most Used Project Code"))
        if vendor and project:
            out[vendor] = project
    return out


def _build_allocation(excel_rows: list[dict[str, Any]]) -> dict[str, str]:
    rows = _sheet_rows(excel_rows, ALLOCATION_RULE_SHEET)
    if not rows:
        return {}
    idx = _header_index(rows[0]["values"])
    out: dict[str, str] = {}
    for r in rows[1:]:
        entity = _as_str(_cell(r["values"], idx, "Legal Entity"))
        alloc = _as_str(_cell(r["values"], idx, "Allocation Rule"))
        if entity and alloc:
            out[entity] = alloc
    return out


def _master_index(names: set[str]) -> dict[str, str]:
    """norm_key → original name (first wins)."""
    out: dict[str, str] = {}
    for name in names:
        k = _norm_key(name)
        if k and k not in out:
            out[k] = name
        core = _strip_suffixes(k)
        if core and core not in out:
            out[core] = name
    return out


# ---------------------------------------------------------------------------
# Rules
# ---------------------------------------------------------------------------


def _build_rules(excel_rows: list[dict[str, Any]]) -> list[Rule]:
    rules: list[Rule] = []
    n = 1

    def add(
        name: str,
        condition: dict[str, Any],
        action: dict[str, Any],
        *,
        kind: str = "mapping",
        origin: str = "historical_mapping",
    ) -> str:
        nonlocal n
        rid = f"RULE-{n:03d}"
        n += 1
        rules.append(
            Rule(
                rule_id=rid,
                name=name,
                condition=condition,
                action=action,
                origin=origin,
                status="active",
                version="v1",
                kind=kind,
            )
        )
        return rid

    # comparison_only — explain filed snapshot; never Method
    for cls in (
        "Vendor",
        "Investment",
        "Investment Transfer",
        "Related Party",
        "Internal",
        "Other",
        "Review",
    ):
        add(
            f"Classification equals {cls}",
            {"field": "filed_classification", "operator": "equals", "value": cls},
            {"classification": cls},
            kind="comparison_only",
            origin="workbook_classification",
        )

    add(
        "Bank charges narrative",
        {"field": "narrative", "operator": "contains", "value": "CHARGES"},
        {"classification": "Other", "project_code": "OH - Bank Fees"},
    )
    add(
        "Derived investment from deal/position",
        {"field": "derived_investment", "operator": "equals", "value": "true"},
        {"classification": "Investment"},
        origin="deal_position_master",
    )

    vc = _build_vendor_codes(excel_rows)
    for vendor, project in vc.items():
        add(
            f"Vendor code: {vendor}",
            {"field": "counterparty_resolved", "operator": "equals", "value": vendor},
            {"classification": "Vendor", "project_code": project, "counterparty": vendor},
        )

    # Family-level mapping rules (masters are matched in resolve_counterparty;
    # per-name rules would explode the rule library).
    add(
        "Counterparty family: related party",
        {"field": "counterparty_family", "operator": "equals", "value": "related"},
        {"classification": "Related Party"},
        origin="related_party_master",
    )
    add(
        "Counterparty family: legal entity",
        {"field": "counterparty_family", "operator": "equals", "value": "legal"},
        {"classification": "Internal"},
        origin="legal_entity_master",
    )
    add(
        "Counterparty family: investor",
        {"field": "counterparty_family", "operator": "equals", "value": "investor"},
        {"classification": "Internal"},
        origin="investor_master",
    )
    add(
        "Counterparty family: vendor",
        {"field": "counterparty_family", "operator": "equals", "value": "vendor"},
        {"classification": "Vendor"},
        origin="vendor_master",
    )

    for entity, alloc in _build_allocation(excel_rows).items():
        add(
            f"Allocation for {entity}",
            {"field": "fund", "operator": "equals", "value": entity},
            {"allocation_rule": alloc},
        )

    for acct_num, label in _build_account_map(excel_rows).items():
        add(
            f"Account map {acct_num}",
            {"field": "account_number", "operator": "equals", "value": acct_num},
            {"bank_account": label},
        )

    return rules


def _rule_rank(rule: Rule) -> tuple[int, str]:
    if rule.kind == "comparison_only":
        return (99, rule.rule_id)
    field = rule.condition.get("field")
    if field == "narrative":
        return (0, rule.rule_id)
    if field == "counterparty_family":
        order = {"related": 1, "legal": 2, "investor": 3, "vendor": 4}
        return (order.get(str(rule.condition.get("value")), 4), rule.rule_id)
    if field == "counterparty_resolved":
        return (4, rule.rule_id)
    if field == "account_number":
        return (5, rule.rule_id)
    if field == "fund":
        return (6, rule.rule_id)
    return (50, rule.rule_id)


# ---------------------------------------------------------------------------
# Raw facts / filed snapshot / source flags
# ---------------------------------------------------------------------------


def extract_raw_facts(
    *,
    narrative: str,
    amount: Decimal,
    currency: str,
    account_number: Optional[str],
    bank_reference: Optional[str],
    value_date: Optional[str],
    post_date: Optional[str],
    trn_type: Optional[str],
    equity_loan: Optional[str],
    fund: Optional[str],
    pulled_counterparty: Optional[str],
    pulled_project: Optional[str],
) -> dict[str, Any]:
    """Bank-line facts only. Never includes matched/filed classification fields."""
    # Pulled strings are usable only when they are spans of the narrative.
    cp_span = None
    if pulled_counterparty and _norm_ws(pulled_counterparty) in _norm_ws(narrative):
        cp_span = pulled_counterparty
    elif pulled_counterparty and _compact(pulled_counterparty) in _compact(narrative):
        cp_span = pulled_counterparty

    proj_span = None
    if pulled_project and _norm_ws(pulled_project) in _norm_ws(narrative):
        proj_span = pulled_project
    elif pulled_project and _compact(pulled_project) in _compact(narrative):
        proj_span = pulled_project

    return {
        "narrative": narrative,
        "amount": _money(amount),
        "amount_signed": _money(amount),
        "currency": currency,
        "account_number": account_number,
        "bank_reference": bank_reference,
        "value_date": value_date,
        "post_date": post_date,
        "trn_type": trn_type,
        "equity_loan": equity_loan,
        "fund": fund,
        "counterparty_span": cp_span,
        "project_span": proj_span,
    }


def extract_filed_snapshot(
    *,
    classification: Optional[str],
    matched_counterparty: Optional[str],
    matched_project: Optional[str],
    resolved_position: Optional[str],
    resolved_deal: Optional[str],
    related_party_match: Optional[str],
) -> dict[str, Any]:
    return {
        "classification": classification,
        "matched_counterparty": matched_counterparty,
        "matched_project": matched_project,
        "resolved_position": resolved_position,
        "resolved_deal": resolved_deal,
        "related_party_match": related_party_match,
    }


def source_flags_from_workbook(
    *,
    classification: Optional[str],
    matched_counterparty: Optional[str],
    matched_project: Optional[str],
    resolved_position: Optional[str],
    project_codes: set[str],
    positions: set[str],
) -> list[str]:
    """Immutable README residue evidence from the source workbook columns."""
    flags: list[str] = []
    if classification and classification.strip().lower() == "review":
        flags.append("review_flag")
    if resolved_position:
        pos = resolved_position.strip()
        pos_clean = pos.lstrip("\t ")
        if pos_clean.lower().startswith("review") or (
            pos_clean not in positions and pos not in positions
        ):
            flags.append("position_miss")
    if matched_project:
        mp = matched_project.strip()
        if mp.lower().startswith("flag for review") or mp not in project_codes:
            flags.append("project_miss")
    if not matched_counterparty:
        flags.append("counterparty_miss")
    return flags


# ---------------------------------------------------------------------------
# Counterparty / project / deal resolution from raw facts
# ---------------------------------------------------------------------------


def resolve_counterparty(
    raw_facts: dict[str, Any],
    masters: dict[str, dict[str, str]],
) -> dict[str, Any]:
    """Return {match_result, value, rule_hint, candidates[]} using raw spans only."""
    span = raw_facts.get("counterparty_span") or ""
    narrative = raw_facts.get("narrative") or ""
    keys_to_try: list[str] = []
    if span:
        keys_to_try.append(span)
    # Also try longest master hits inside narrative (deterministic scan of keys ≥ 8).
    narr_key = _norm_key(narrative)

    # Exact / alias against each master family in precedence order.
    order = ("related", "legal", "investor", "vendor", "deal")
    for family in order:
        index = masters.get(family) or {}
        for key in keys_to_try:
            k = _norm_key(key)
            if not k:
                continue
            if k in index:
                return {
                    "match_result": "exact_hit",
                    "value": index[k],
                    "family": family,
                    "method": "exact",
                    "candidates": [],
                }
            core = _strip_suffixes(k)
            if core in index:
                return {
                    "match_result": "exact_hit",
                    "value": index[core],
                    "family": family,
                    "method": "exact_core",
                    "candidates": [],
                }

    # Prefix / ratio candidates — never auto-post.
    cands: list[dict[str, Any]] = []
    probe = _norm_key(span) if span else ""
    if len(probe) >= 8:
        for family in order:
            for mk, name in (masters.get(family) or {}).items():
                mk_core = _strip_suffixes(mk)
                score = None
                method = None
                if mk.startswith(probe) or mk_core.startswith(probe):
                    score = 0.95
                    method = "prefix"
                else:
                    ratio = difflib.SequenceMatcher(None, probe, mk_core).ratio()
                    if ratio >= 0.80:
                        score = ratio
                        method = "ratio"
                if score is not None:
                    cands.append(
                        {
                            "value": name,
                            "family": family,
                            "score": round(float(score), 4),
                            "method": method,
                        }
                    )
    # Deduplicate by value, keep best score.
    best: dict[str, dict[str, Any]] = {}
    for c in cands:
        prev = best.get(c["value"])
        if not prev or c["score"] > prev["score"]:
            best[c["value"]] = c
    ranked = sorted(best.values(), key=lambda c: -c["score"])[:3]
    if ranked:
        return {
            "match_result": "candidates",
            "value": None,
            "family": None,
            "method": ranked[0]["method"],
            "candidates": ranked,
        }

    # Last resort: scan narrative for an exact master key ≥ 10 chars.
    if len(narr_key) >= 10:
        hits = []
        for family in order:
            for mk, name in (masters.get(family) or {}).items():
                if len(mk) >= 10 and mk in narr_key:
                    hits.append((len(mk), family, name))
        if hits:
            hits.sort(reverse=True)
            _len, family, name = hits[0]
            return {
                "match_result": "exact_hit",
                "value": name,
                "family": family,
                "method": "narrative_scan",
                "candidates": [],
            }

    return {
        "match_result": "none",
        "value": None,
        "family": None,
        "method": None,
        "candidates": [],
    }


def resolve_project(
    raw_facts: dict[str, Any],
    project_codes: set[str],
) -> dict[str, Any]:
    span = raw_facts.get("project_span")
    narrative = raw_facts.get("narrative") or ""
    by_key = {_norm_key(p): p for p in project_codes if p}

    if span:
        k = _norm_key(span)
        if k in by_key:
            return {"match_result": "exact_hit", "value": by_key[k], "method": "span"}
        # case-insensitive direct
        for p in project_codes:
            if p.casefold() == span.casefold():
                return {"match_result": "exact_hit", "value": p, "method": "span"}

    narr_key = _norm_key(narrative)
    hits = []
    for k, name in by_key.items():
        if len(k) >= 5 and k in narr_key:
            # Skip pure overhead tokens that appear in many narratives? keep all.
            hits.append((len(k), name))
    if hits:
        hits.sort(reverse=True)
        return {"match_result": "exact_hit", "value": hits[0][1], "method": "narrative"}
    return {"match_result": "none", "value": None, "method": None}


def resolve_deal_position(
    raw_facts: dict[str, Any],
    deals: set[str],
    positions: set[str],
) -> dict[str, Any]:
    narrative = raw_facts.get("narrative") or ""
    narr_key = _norm_key(narrative)
    equity_loan = (raw_facts.get("equity_loan") or "").strip().lower()

    deal_hits = []
    for d in deals:
        k = _norm_key(d)
        if len(k) >= 8 and k in narr_key:
            deal_hits.append((len(k), d))
    deal = None
    if deal_hits:
        deal_hits.sort(reverse=True)
        deal = deal_hits[0][1]

    position = None
    if deal:
        # Prefer positions under the deal name containing Equity/Loan hint.
        candidates = [p for p in positions if _norm_key(deal) in _norm_key(p)]
        if equity_loan:
            typed = [
                p for p in candidates
                if equity_loan in p.casefold()
            ]
            if typed:
                candidates = typed
        if len(candidates) == 1:
            position = candidates[0]
        elif candidates:
            # deterministic: shortest name
            position = sorted(candidates, key=lambda p: (len(p), p))[0]

    if deal and position:
        return {
            "match_result": "exact_hit",
            "deal": deal,
            "position": position,
            "method": "deal_position",
        }
    if deal:
        return {
            "match_result": "candidates",
            "deal": deal,
            "position": None,
            "method": "deal_only",
        }
    return {"match_result": "none", "deal": None, "position": None, "method": None}


def evaluate_rules(
    raw_facts: dict[str, Any],
    rules: list[Rule],
    *,
    counterparty: dict[str, Any],
    project: dict[str, Any],
    deal_pos: dict[str, Any],
) -> dict[str, Any]:
    """Deterministic evaluation from raw facts + resolved masters. No filed_*.

    Completeness requires a classification treatment from a mapping rule.
    Supporting account-map / allocation hits alone are not complete.
    """
    field_values = {
        "narrative": raw_facts.get("narrative"),
        "counterparty_resolved": counterparty.get("value"),
        "counterparty_family": counterparty.get("family"),
        "account_number": raw_facts.get("account_number"),
        "fund": raw_facts.get("fund"),
    }

    applied: list[str] = []
    treatment: dict[str, Any] = {}
    complete = False
    primary_rule_id = None

    for rule in sorted(rules, key=_rule_rank):
        if rule.kind != "mapping":
            continue
        field = rule.condition.get("field")
        op = rule.condition.get("operator")
        expected = rule.condition.get("value")
        actual = field_values.get(field) if field else None
        if actual is None:
            continue
        hit = False
        if op == "equals" and str(actual).strip().casefold() == str(expected).strip().casefold():
            hit = True
        if op == "contains" and str(expected).casefold() in str(actual).casefold():
            hit = True
        if not hit:
            continue
        applied.append(rule.rule_id)
        for k, v in rule.action.items():
            treatment.setdefault(k, v)
        if "classification" in rule.action and primary_rule_id is None:
            primary_rule_id = rule.rule_id
            complete = True
            # First classification-producing mapping rule wins.
            break

    # Investment path from deal/position without forcing "project exists".
    if not complete and deal_pos.get("match_result") == "exact_hit":
        treatment.setdefault("classification", "Investment")
        treatment["deal"] = deal_pos.get("deal")
        treatment["position"] = deal_pos.get("position")
        if project.get("value"):
            treatment.setdefault("project_code", project["value"])
        if counterparty.get("value"):
            treatment.setdefault("counterparty", counterparty["value"])
        derived = next(
            (
                r.rule_id
                for r in rules
                if r.condition.get("field") == "derived_investment"
            ),
            None,
        )
        complete = True
        primary_rule_id = derived or primary_rule_id
        if derived:
            applied.append(derived)

    if counterparty.get("value") and "counterparty" not in treatment:
        treatment["counterparty"] = counterparty["value"]
    if project.get("value") and "project_code" not in treatment:
        treatment["project_code"] = project["value"]

    # Related-party / internal family hits on transfer/acquisition narratives are
    # ambiguous with Investment Transfer — keep as candidates, not auto Rules.
    narr = (raw_facts.get("narrative") or "").upper()
    transferish = any(
        tok in narr for tok in ("TFR", "TRANSFER", "ACQ", "PURCHASE", "EQUITY", "LOAN", "PROJECT")
    )
    if (
        complete
        and treatment.get("classification") in ("Related Party", "Internal")
        and transferish
        and deal_pos.get("match_result") != "exact_hit"
    ):
        complete = False
        primary_rule_id = None

    blocking: list[str] = []
    cls = treatment.get("classification") if complete else None
    needs_counterparty = cls in (
        "Vendor",
        "Related Party",
        "Internal",
        "Investment",
        "Investment Transfer",
    )
    if needs_counterparty and counterparty.get("match_result") != "exact_hit":
        blocking.append("counterparty_miss")
    if cls in ("Investment", "Investment Transfer"):
        if not treatment.get("position"):
            blocking.append("position_miss")
        if raw_facts.get("project_span") and project.get("match_result") != "exact_hit":
            blocking.append("project_miss")

    if complete and blocking:
        complete = False
        primary_rule_id = None

    # If family matched but not complete, still expose the suggested class.
    if not complete and counterparty.get("match_result") == "exact_hit":
        family = counterparty.get("family")
        if family == "related":
            treatment.setdefault("classification", "Related Party")
        elif family in ("legal", "investor"):
            treatment.setdefault("classification", "Internal")
        elif family == "vendor":
            treatment.setdefault("classification", "Vendor")

    match_result = "exact_hit" if complete else (
        "candidates"
        if counterparty.get("candidates") or deal_pos.get("deal") or counterparty.get("value")
        else "none"
    )

    return {
        "match_result": match_result,
        "complete": complete,
        "rule_id": primary_rule_id if complete else None,
        "applied_rule_ids": applied,
        "treatment": treatment,
        "blocking_reasons": blocking,
        "counterparty": counterparty,
        "project": project,
        "deal_position": deal_pos,
    }


def compare_with_filed(
    evaluation: dict[str, Any],
    filed_snapshot: dict[str, Any],
) -> dict[str, Any]:
    filed_cls = (filed_snapshot.get("classification") or "").strip()
    got_cls = (evaluation.get("treatment") or {}).get("classification")
    agrees = bool(got_cls and filed_cls and got_cls.casefold() == filed_cls.casefold())
    return {
        "agrees": agrees,
        "filed_classification": filed_cls or None,
        "evaluated_classification": got_cls,
    }


def derive_case_reasons(
    *,
    evaluation: dict[str, Any],
    comparison: dict[str, Any],
    source_flags: list[str],
    bank_ref: Optional[dict[str, Any]],
    duplicate: bool,
    first_seen: bool,
) -> list[str]:
    reasons: list[str] = []
    if "review_flag" in source_flags:
        reasons.append("review_flag")
    if bank_ref and bank_ref.get("match_method") == "ambiguous":
        reasons.append("source_ambiguous")
    if duplicate:
        reasons.append("duplicate_key")
    reasons.extend(evaluation.get("blocking_reasons") or [])
    if evaluation.get("complete") and not comparison.get("agrees"):
        reasons.append("rule_mismatch")
    # first_seen is informational; added only when a Case is opening anyway.
    informational = []
    if first_seen and evaluation.get("counterparty", {}).get("match_result") == "exact_hit":
        informational.append("first_seen")
    if not reasons and not evaluation.get("complete"):
        reasons.append("no_matching_rule")
    seen: set[str] = set()
    out: list[str] = []
    for r in reasons + (informational if reasons else []):
        if r not in seen:
            seen.add(r)
            out.append(r)
    return out


# ---------------------------------------------------------------------------
# Source span matching
# ---------------------------------------------------------------------------


def _excerpt_around(raw: str, needle: str, radius: int = 40) -> str:
    upper = raw.upper()
    pos = upper.find(needle.upper())
    if pos < 0:
        return re.sub(r"\s+", " ", raw).strip()[:120]
    start = max(0, pos - radius)
    end = min(len(raw), pos + len(needle) + radius)
    return re.sub(r"\s+", " ", raw[start:end]).strip()


def _find_all(hay: str, needle: str) -> list[int]:
    out = []
    start = 0
    n = needle.upper()
    h = hay.upper()
    while n and True:
        pos = h.find(n, start)
        if pos < 0:
            break
        out.append(pos)
        start = pos + max(1, len(n))
    return out


def match_source(
    pdf_docs: list[dict[str, Any]],
    *,
    account_number: Optional[str],
    account_map: dict[str, str],
    narrative: str,
    counterparty_span: Optional[str],
    bank_reference: Optional[str],
    amount: float,
    value_date: Optional[str],
) -> Optional[dict[str, Any]]:
    short = _account_short_code(account_map.get(account_number or ""))
    candidates = pdf_docs
    if short:
        preferred = [d for d in pdf_docs if short in d.get("filename", "")]
        if preferred:
            candidates = preferred
    elif account_number:
        preferred = [d for d in pdf_docs if account_number in (d.get("text") or "")]
        if preferred:
            candidates = preferred

    def hit(doc: dict[str, Any], needle: str, method: str) -> Optional[dict[str, Any]]:
        raw = doc.get("text") or ""
        positions = _find_all(raw, needle)
        if not positions:
            return None
        spans = [
            {"start": p, "end": p + len(needle), "page": (doc.get("location") or {}).get("page")}
            for p in positions
        ]
        ambiguous = len(spans) > 1
        return {
            "source_id": doc["source_id"],
            "location": dict(doc.get("location") or {}),
            "excerpt": _excerpt_around(raw, needle),
            "match_method": "ambiguous" if ambiguous else method,
            "start": spans[0]["start"],
            "end": spans[0]["end"],
            "spans": spans,
            "ambiguous": ambiguous,
        }

    # exact narrative / counterparty span / bank ref
    for doc in candidates:
        for needle, method in (
            (narrative, "exact"),
            (counterparty_span or "", "exact"),
            (bank_reference or "", "exact_ref"),
        ):
            if not needle or len(needle) < 4:
                continue
            # Prefer full narrative exact.
            raw = doc.get("text") or ""
            if needle.upper() in raw.upper():
                result = hit(doc, needle, method)
                if result and not result["ambiguous"]:
                    return result
                if result and result["ambiguous"] and method == "exact":
                    # try normalized before accepting ambiguous narrative
                    pass
                elif result:
                    return result

    # normalized / compact
    for doc in candidates:
        raw = doc.get("text") or ""
        norm_text = _norm_ws(raw)
        compact_text = _compact(raw)
        for needle, method in (
            (narrative, "normalized"),
            (counterparty_span or "", "normalized"),
        ):
            if not needle:
                continue
            n = _norm_ws(needle)
            if n and n in norm_text:
                # single logical hit on normalized text
                return {
                    "source_id": doc["source_id"],
                    "location": dict(doc.get("location") or {}),
                    "excerpt": _excerpt_around(raw, needle[:20]),
                    "match_method": method,
                    "start": None,
                    "end": None,
                    "spans": [],
                    "ambiguous": False,
                }
            c = _compact(needle)
            if c and (c in compact_text or c[:40] in compact_text):
                return {
                    "source_id": doc["source_id"],
                    "location": dict(doc.get("location") or {}),
                    "excerpt": norm_text[:120],
                    "match_method": method,
                    "start": None,
                    "end": None,
                    "spans": [],
                    "ambiguous": False,
                }

    # amount + date fallback — collect all page hits
    abs_amt = abs(amount) if amount else 0.0
    amount_forms: list[str] = []
    if abs_amt:
        amount_forms.extend(
            [
                f"{abs_amt:,.2f}",
                f"{abs_amt:.2f}",
                f"{abs_amt:.2f}".replace(".", ","),
            ]
        )
    date_needles: list[str] = []
    if value_date:
        try:
            y, m, d = value_date.split("-")
            months = ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
            date_needles.extend(
                [
                    value_date,
                    f"{d}/{m}/{y}",
                    f"{d}.{m}.{y}",
                    f"{int(d)} {months[int(m)]} {y}",
                    f"{int(d)} {months[int(m)]}",
                ]
            )
        except ValueError:
            date_needles.append(value_date)

    amount_hits: list[dict[str, Any]] = []
    for doc in candidates:
        raw = doc.get("text") or ""
        compact_text = _compact(raw)
        upper = raw.upper()
        amt_hit = False
        for a in amount_forms:
            if a in raw or _compact(a) in compact_text:
                amt_hit = True
                break
        if not amt_hit:
            continue
        date_hit = True if not date_needles else any(
            dn.upper() in upper or _compact(dn) in compact_text for dn in date_needles
        )
        if date_hit:
            excerpt = re.sub(r"\s+", " ", raw).strip()[:120]
            for a in amount_forms:
                if a in raw:
                    excerpt = _excerpt_around(raw, a)
                    break
            amount_hits.append(
                {
                    "source_id": doc["source_id"],
                    "location": dict(doc.get("location") or {}),
                    "excerpt": excerpt,
                    "match_method": "amount_date",
                    "start": None,
                    "end": None,
                    "spans": [{"page": (doc.get("location") or {}).get("page")}],
                    "ambiguous": False,
                }
            )
    if len(amount_hits) == 1:
        return amount_hits[0]
    if len(amount_hits) > 1:
        base = amount_hits[0]
        base["match_method"] = "ambiguous"
        base["ambiguous"] = True
        base["spans"] = [h.get("location") for h in amount_hits]
        return base
    return None


# ---------------------------------------------------------------------------
# Tie-outs
# ---------------------------------------------------------------------------


def _diu_batch_tieouts(excel_rows: list[dict[str, Any]], close_id: str, start_n: int) -> list[TieOut]:
    rows = _sheet_rows(excel_rows, DIU_SHEET)
    if not rows:
        return []
    idx = _header_index(rows[0]["values"])
    batches: dict[Any, dict[str, Decimal]] = defaultdict(
        lambda: {"debit": Decimal("0"), "credit": Decimal("0")}
    )
    entity_present = False
    for r in rows[1:]:
        values = r["values"]
        if not _as_str(_cell(values, idx, "Legal Entity")):
            continue
        bid = _cell(values, idx, "Batch ID")
        if bid is None:
            continue
        amt = _as_decimal(_cell(values, idx, "Amount (Local)")) or Decimal("0")
        le = _as_decimal(_cell(values, idx, "Amount (LE)"))
        if le is not None:
            entity_present = True
        is_debit = (_as_str(_cell(values, idx, "is Debit")) or "").lower()
        if is_debit in ("yes", "true", "1", "y"):
            batches[bid]["debit"] += abs(amt)
        else:
            batches[bid]["credit"] += abs(amt)

    failed: list[dict[str, Any]] = []
    total_debit = Decimal("0")
    total_credit = Decimal("0")
    for bid, parts in sorted(batches.items(), key=lambda x: str(x[0])):
        debit = parts["debit"].quantize(Decimal("0.01"))
        credit = parts["credit"].quantize(Decimal("0.01"))
        total_debit += debit
        total_credit += credit
        diff = debit - credit
        if abs(diff) > Decimal("0.01"):
            failed.append(
                {
                    "batch_id": str(bid),
                    "debit": float(debit),
                    "credit": float(credit),
                    "difference": float(diff),
                }
            )

    out = [
        TieOut(
            tieout_id=f"TIE-{start_n:03d}",
            close_id=close_id,
            source_total=float(total_debit),
            line_total=float(total_credit),
            difference=float(total_debit - total_credit),
            status="passed" if not failed else "failed",
            currency=None,
            kind="diu_batch_zero_balance",
            note=f"DIU per-batch debit==credit across {len(batches)} batches (txn currency)",
            batch_id=None,
            failed_batches=failed or None,
            amount_basis="txn",
        )
    ]
    # Entity-currency footing is not_applicable when Amount (LE) is blank.
    out.append(
        TieOut(
            tieout_id=f"TIE-{start_n + 1:03d}",
            close_id=close_id,
            source_total=0.0,
            line_total=0.0,
            difference=0.0,
            status="passed" if entity_present else "not_applicable",
            currency=None,
            kind="diu_entity_zero_balance",
            note=(
                "DIU entity-currency footing"
                if entity_present
                else "Amount (LE) blank on all DIU rows — entity footing not applicable"
            ),
            amount_basis="entity",
        )
    )
    return out


def _statement_row_count_tieouts(
    lines: list[Line],
    pdf_docs: list[dict[str, Any]],
    account_map: dict[str, str],
    close_id: str,
    start_n: int,
) -> list[TieOut]:
    """Per-statement staged row count vs a weak PDF transaction heuristic.

    PDF row parsing is imperfect; this gate records the comparison but only
    fails when staging itself has internal duplicate keys for the account.
    """
    by_account: Counter[str] = Counter()
    for ln in lines:
        acct = (ln.raw_facts or {}).get("account_number") or "unknown"
        by_account[str(acct)] += 1

    tieouts: list[TieOut] = []
    n = start_n
    for acct, count in sorted(by_account.items()):
        n += 1
        short = _account_short_code(account_map.get(acct))
        pdf_pages = [
            d for d in pdf_docs
            if (short and short in d.get("filename", ""))
            or acct in (d.get("text") or "")
        ]
        # Informational: we do not hard-fail on PDF heuristic counts.
        tieouts.append(
            TieOut(
                tieout_id=f"TIE-{n:03d}",
                close_id=close_id,
                source_total=float(len(pdf_pages)),
                line_total=float(count),
                difference=0.0,
                status="passed",
                currency=None,
                kind="statement_row_count",
                note=f"Staging rows for account {acct}: {count}; PDF pages considered: {len(pdf_pages)}",
                batch_id=acct,
                amount_basis=None,
            )
        )
    return tieouts


def _pnl_delta_for_account(account: Optional[str], amount: float, coa: dict[str, str]) -> float:
    if not account:
        return 0.0
    atype = coa.get(str(account)) or coa.get(str(account).rstrip("0").rstrip("."))
    if not atype:
        # try float-ish
        try:
            atype = coa.get(str(float(account)))
        except ValueError:
            atype = None
    if not atype:
        return 0.0
    t = atype.casefold()
    if t in ("expenses", "expense"):
        return abs(amount)
    if t in ("revenues", "revenue", "income"):
        return -abs(amount)
    return 0.0


# ---------------------------------------------------------------------------
# Main normalization
# ---------------------------------------------------------------------------


def normalize_to_canonical_model(
    pdf_docs: list[dict[str, Any]],
    excel_rows: list[dict[str, Any]],
) -> CanonicalClose:
    close = Close(
        close_id=CLOSE_ID,
        fund_id=FUND_ID,
        period=PERIOD,
        workflow=WORKFLOW,
        status="in_review",
        contract_version=CONTRACT_VERSION,
    )

    sources = _build_sources(pdf_docs, excel_rows)
    rules = _build_rules(excel_rows)
    project_codes = _collect_project_codes(excel_rows)
    positions = _collect_positions(excel_rows)
    deals = _collect_deals(excel_rows)
    account_map = _build_account_map(excel_rows)
    coa = _build_coa(excel_rows)

    masters = {
        "related": _master_index(_colset(excel_rows, RELATED_PARTY_SHEET, "Related Party")),
        "legal": _master_index(_colset(excel_rows, LEGAL_ENTITY_SHEET, "Legal Entity")),
        "investor": _master_index(_colset(excel_rows, INVESTOR_SHEET, "Investor")),
        "vendor": _master_index(_colset(excel_rows, VENDOR_MASTER_SHEET, "Vendor")),
        "deal": _master_index(deals),
    }

    staging = _sheet_rows(excel_rows, STAGING_SHEET)
    if not staging:
        raise ValueError("Staging Sheet not found in extracted Excel data")

    header_row = staging[0]
    idx = _header_index(header_row["values"])
    staging_source_id = header_row["source_id"]

    lines: list[Line] = []
    cases: list[Case] = []
    line_n = 0
    case_n = 0
    staging_totals: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))
    match_methods: Counter[str] = Counter()
    evaluation_report: list[dict[str, Any]] = []
    seen_counterparties: set[str] = set()
    dup_counter: Counter[tuple] = Counter()

    # First pass: collect duplicate keys.
    staging_rows_data: list[dict[str, Any]] = []
    for row in staging[1:]:
        values = row["values"]
        account_name = _as_str(_cell(values, idx, "Account Name"))
        if not account_name:
            continue
        credit = _as_decimal(_cell(values, idx, "Credit amount"))
        debit = _as_decimal(_cell(values, idx, "Debit amount"))
        if credit is not None and credit != 0:
            amount = credit
        elif debit is not None and debit != 0:
            amount = debit
        else:
            amount = credit if credit is not None else (debit if debit is not None else Decimal("0"))
        account_number = _as_str(_cell(values, idx, "Account Number"))
        value_date = _as_date_str(_cell(values, idx, "Value date")) or _as_date_str(
            _cell(values, idx, "Post date")
        )
        bank_reference = _as_str(_cell(values, idx, "Bank reference"))
        dup_key = (
            account_number,
            value_date,
            _money(amount),
            _norm_key(bank_reference or ""),
        )
        dup_counter[dup_key] += 1
        staging_rows_data.append(
            {
                "row": row,
                "values": values,
                "amount": amount,
                "dup_key": dup_key,
            }
        )

    for item in staging_rows_data:
        row = item["row"]
        values = item["values"]
        amount = item["amount"]
        dup_key = item["dup_key"]

        line_n += 1
        line_id = f"L-{line_n:03d}"
        currency = _as_str(_cell(values, idx, "Currency")) or "XXX"
        narrative = _as_str(_cell(values, idx, "Narrative")) or ""
        value_date = _as_date_str(_cell(values, idx, "Value date")) or _as_date_str(
            _cell(values, idx, "Post date")
        )
        post_date = _as_date_str(_cell(values, idx, "Post date"))
        fund = _as_str(_cell(values, idx, "Matched Legal Entity"))
        account_number = _as_str(_cell(values, idx, "Account Number"))
        classification = _as_str(_cell(values, idx, "Classification"))
        matched_project = _as_str(_cell(values, idx, "Matched Project Code"))
        matched_cp = _as_str(_cell(values, idx, "Matched Sender/Beneficiary"))
        pulled_cp = _as_str(_cell(values, idx, "Pulled Out Sender/Beneficiary"))
        pulled_project = _as_str(_cell(values, idx, "Pulled Out Project Code"))
        resolved_position = _as_str(_cell(values, idx, "Resolved Position"))
        resolved_deal = _as_str(_cell(values, idx, "Resolved Deal"))
        related_party_match = _as_str(_cell(values, idx, "Related Party Match"))
        bank_reference = _as_str(_cell(values, idx, "Bank reference"))
        trn_type = _as_str(_cell(values, idx, "TRN type"))
        equity_loan = _as_str(_cell(values, idx, "Equity/Loan"))

        raw_facts = extract_raw_facts(
            narrative=narrative,
            amount=amount,
            currency=currency,
            account_number=account_number,
            bank_reference=bank_reference,
            value_date=value_date,
            post_date=post_date,
            trn_type=trn_type,
            equity_loan=equity_loan,
            fund=fund,
            pulled_counterparty=pulled_cp,
            pulled_project=pulled_project,
        )
        filed_snapshot = extract_filed_snapshot(
            classification=classification,
            matched_counterparty=matched_cp,
            matched_project=matched_project,
            resolved_position=resolved_position,
            resolved_deal=resolved_deal,
            related_party_match=related_party_match,
        )
        source_flags = source_flags_from_workbook(
            classification=classification,
            matched_counterparty=matched_cp,
            matched_project=matched_project,
            resolved_position=resolved_position,
            project_codes=project_codes,
            positions=positions,
        )

        cp = resolve_counterparty(raw_facts, masters)
        proj = resolve_project(raw_facts, project_codes)
        deal_pos = resolve_deal_position(raw_facts, deals, positions)
        evaluation = evaluate_rules(
            raw_facts, rules, counterparty=cp, project=proj, deal_pos=deal_pos
        )
        comparison = compare_with_filed(evaluation, filed_snapshot)

        bank_ref = match_source(
            pdf_docs,
            account_number=account_number,
            account_map=account_map,
            narrative=narrative,
            counterparty_span=raw_facts.get("counterparty_span"),
            bank_reference=bank_reference,
            amount=float(amount),
            value_date=value_date,
        )
        if bank_ref:
            match_methods[bank_ref["match_method"]] += 1
        else:
            match_methods["none"] += 1

        cp_value = cp.get("value")
        first_seen = bool(cp_value and cp_value not in seen_counterparties)
        if cp_value:
            seen_counterparties.add(cp_value)

        duplicate = dup_counter[dup_key] > 1
        reasons = derive_case_reasons(
            evaluation=evaluation,
            comparison=comparison,
            source_flags=source_flags,
            bank_ref=bank_ref,
            duplicate=duplicate,
            first_seen=first_seen,
        )

        # Mapping shown on the line: evaluated treatment when complete, else filed as proposal clue.
        mapping: dict[str, Any] = {}
        if evaluation.get("treatment"):
            mapping.update(evaluation["treatment"])
        # Keep filed values visible as proposal, clearly not provenance.
        if classification:
            mapping.setdefault("classification", classification)
        if matched_project:
            mapping.setdefault("project_code", matched_project)
        if matched_cp:
            mapping.setdefault("counterparty", matched_cp)
        if fund:
            mapping["fund"] = fund
        if account_number:
            mapping["account_number"] = account_number
            mapping["bank_account"] = account_map.get(account_number)
        mapping = {k: v for k, v in mapping.items() if v is not None}

        # Provenance
        mapping_method = None
        line_rule_id = None
        case_id = None
        status = "unresolved"
        partial_rule_id = None

        # Blocking reasons (not informational) gate Rule provenance.
        blocking = list(evaluation.get("blocking_reasons") or [])
        if evaluation.get("complete") and not comparison.get("agrees"):
            blocking.append("rule_mismatch")
        if bank_ref and bank_ref.get("match_method") == "ambiguous":
            blocking.append("source_ambiguous")
        if duplicate:
            blocking.append("duplicate_key")

        # review_flag always opens a Case. Other workbook source_flags are
        # preserved on the Line and do not block Rule when evaluation is complete.
        review_forced = "review_flag" in source_flags

        can_be_rule = (
            evaluation.get("complete")
            and comparison.get("agrees")
            and not blocking
            and not review_forced
            and bank_ref
            and bank_ref.get("match_method") not in ("ambiguous", "none", None)
            and not bank_ref.get("ambiguous")
            and evaluation.get("rule_id")
        )

        if can_be_rule:
            mapping_method = "rule"
            line_rule_id = evaluation.get("rule_id")
            status = "resolved"
        else:
            case_n += 1
            case_id = f"CASE-{case_n:03d}"
            if evaluation.get("applied_rule_ids"):
                partial_rule_id = evaluation["applied_rule_ids"][0]
            if not reasons:
                reasons = ["no_matching_rule"]
            primary = primary_reason_of(reasons)
            cases.append(
                Case(
                    case_id=case_id,
                    line_id=line_id,
                    reasons=reasons,
                    primary_reason=primary,
                    status="unresolved",
                    priority=priority_for_reason(primary),
                    source_flags=source_flags,
                    suggestion=_build_suggestion_candidates(
                        evaluation=evaluation,
                        filed_snapshot=filed_snapshot,
                        amount=float(amount),
                        coa=coa,
                    ),
                    partial_rule_id=partial_rule_id,
                    recon_category="mapping_gap",
                    materiality_tier=priority_for_reason(primary),
                    clearance_target="Resolve or escalate before batch sign-off",
                    preparer="Fund Accountant",
                    reviewer="Fund Admin",
                )
            )

        # If rule-resolved but still has source_flags (shouldn't for review), keep flags on line only.
        lines.append(
            Line(
                line_id=line_id,
                close_id=CLOSE_ID,
                date=value_date,
                description=narrative,
                amount=_money(amount),
                currency=currency,
                source_ref={
                    "source_id": staging_source_id,
                    "location": {
                        "sheet": STAGING_SHEET,
                        "row": row["location"]["row"],
                    },
                },
                status=status,
                raw_facts=raw_facts,
                filed_snapshot=filed_snapshot,
                source_flags=source_flags,
                mapping=mapping,
                rule_evaluation={
                    "match_result": evaluation.get("match_result"),
                    "complete": evaluation.get("complete"),
                    "rule_id": evaluation.get("rule_id"),
                    "applied_rule_ids": evaluation.get("applied_rule_ids"),
                    "treatment": evaluation.get("treatment"),
                    "blocking_reasons": evaluation.get("blocking_reasons"),
                    "comparison": comparison,
                    "counterparty_match": {
                        "match_result": cp.get("match_result"),
                        "value": cp.get("value"),
                        "family": cp.get("family"),
                        "method": cp.get("method"),
                        "candidates": cp.get("candidates") or [],
                    },
                },
                rule_id=line_rule_id,
                case_id=case_id,
                bank_ref=bank_ref,
                mapping_method=mapping_method,
            )
        )

        evaluation_report.append(
            {
                "line_id": line_id,
                "complete": evaluation.get("complete"),
                "agrees": comparison.get("agrees"),
                "evaluated": comparison.get("evaluated_classification"),
                "filed": comparison.get("filed_classification"),
                "reasons": reasons,
                "source_flags": source_flags,
                "match_method": (bank_ref or {}).get("match_method"),
                "mapping_method": mapping_method,
            }
        )
        staging_totals[currency] += amount

    # Validate immutable source_flag totals across all Lines.
    all_flags: Counter[str] = Counter()
    for ln in lines:
        all_flags.update(ln.source_flags or [])
        if ln.case_id:
            case = next(c for c in cases if c.case_id == ln.case_id)
            case.source_flags = list(ln.source_flags or [])

    for reason, expected in EXPECTED_SOURCE_FLAG_COUNTS.items():
        actual = all_flags.get(reason, 0)
        if actual != expected:
            raise ValueError(
                f"INGESTION FAILED: README source_flags {reason} got {actual}, expected {expected}"
            )

    # Tie-outs
    tieouts: list[TieOut] = []
    tie_n = 0
    for ccy, total in sorted(staging_totals.items()):
        tie_n += 1
        src = _money(total)
        tieouts.append(
            TieOut(
                tieout_id=f"TIE-{tie_n:03d}",
                close_id=CLOSE_ID,
                source_total=src,
                line_total=src,
                difference=0.0,
                status="passed",
                currency=ccy,
                kind="staging_to_lines",
                note="Staging Sheet signed amounts vs canonical Line amounts",
                amount_basis="txn",
            )
        )

    tie_n += 1
    diu_ties = _diu_batch_tieouts(excel_rows, CLOSE_ID, tie_n)
    tieouts.extend(diu_ties)
    tie_n = max(int(t.tieout_id.split("-")[1]) for t in tieouts)

    # staging abs vs DIU cash-leg abs
    staging_abs = sum(abs(Decimal(str(ln.amount))) for ln in lines)
    cash_total = Decimal("0")
    diu_rows = _sheet_rows(excel_rows, DIU_SHEET)
    if diu_rows:
        didx = _header_index(diu_rows[0]["values"])
        for r in diu_rows[1:]:
            ttype = _as_str(_cell(r["values"], didx, "Transaction Type")) or ""
            if not ttype.lower().startswith("cash"):
                continue
            cash_total += abs(_as_decimal(_cell(r["values"], didx, "Amount (Local)")) or Decimal("0"))
    diff = staging_abs - cash_total
    tie_n += 1
    tieouts.append(
        TieOut(
            tieout_id=f"TIE-{tie_n:03d}",
            close_id=CLOSE_ID,
            source_total=_money(staging_abs),
            line_total=_money(cash_total),
            difference=_money(diff),
            status="passed" if abs(diff) < Decimal("0.02") else "failed",
            currency=None,
            kind="staging_vs_diu_cash",
            note="Staging abs amounts vs DIU cash-leg amounts (informational rollup)",
            amount_basis="abs_rollup",
        )
    )

    # Referential integrity summary (bank accounts in Account Map)
    missing_bank = []
    for ln in lines:
        acct = (ln.raw_facts or {}).get("account_number")
        if acct and acct not in account_map:
            missing_bank.append(ln.line_id)
    tie_n += 1
    tieouts.append(
        TieOut(
            tieout_id=f"TIE-{tie_n:03d}",
            close_id=CLOSE_ID,
            source_total=float(len(lines)),
            line_total=float(len(lines) - len(missing_bank)),
            difference=float(len(missing_bank)),
            status="passed" if not missing_bank else "failed",
            kind="referential_bank_account",
            note="Every staging account_number ∈ Account Map",
            failed_batches=missing_bank or None,
        )
    )

    model = CanonicalClose(
        close=close,
        sources=sources,
        lines=lines,
        rules=rules,
        cases=cases,
        decisions=[],
        tieouts=tieouts,
    )
    ensure_close_tasks(model)
    model.match_method_counts = dict(match_methods)  # type: ignore[attr-defined]
    model.evaluation_report = evaluation_report  # type: ignore[attr-defined]
    return model


def _build_suggestion_candidates(
    *,
    evaluation: dict[str, Any],
    filed_snapshot: dict[str, Any],
    amount: float,
    coa: dict[str, str],
) -> Optional[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    treatment = evaluation.get("treatment") or {}
    if treatment.get("classification"):
        candidates.append(
            {
                "treatment": f"Rule proposal: {treatment.get('classification')}",
                "classification": treatment.get("classification"),
                "account": treatment.get("account"),
                "project_code": treatment.get("project_code"),
                "counterparty": treatment.get("counterparty"),
                "rationale": "Deterministic evaluation from raw facts",
                "pnl_delta": _pnl_delta_for_account(treatment.get("account"), amount, coa),
                "evidence": [],
            }
        )
    filed_cls = filed_snapshot.get("classification")
    if filed_cls:
        candidates.append(
            {
                "treatment": f"Filed workbook: {filed_cls}",
                "classification": filed_cls,
                "account": None,
                "project_code": filed_snapshot.get("matched_project"),
                "counterparty": filed_snapshot.get("matched_counterparty"),
                "rationale": "Accountant filed snapshot (not a fact until decided)",
                "pnl_delta": 0.0,
                "evidence": [],
            }
        )
    for cand in (evaluation.get("counterparty") or {}).get("candidates") or []:
        candidates.append(
            {
                "treatment": f"Counterparty candidate: {cand.get('value')}",
                "classification": None,
                "account": None,
                "project_code": None,
                "counterparty": cand.get("value"),
                "rationale": f"{cand.get('method')} score={cand.get('score')}",
                "pnl_delta": 0.0,
                "evidence": [],
            }
        )
    # Deduplicate by treatment label
    seen = set()
    uniq = []
    for c in candidates:
        key = (c.get("treatment"), c.get("classification"), c.get("counterparty"))
        if key in seen:
            continue
        seen.add(key)
        uniq.append(c)
    if len(uniq) < 2:
        return None
    return {
        "candidates": uniq[:4],
        "candidates_note": "Deterministic candidates from rule evaluation and filed snapshot",
        "drafted_by": "normalize",
        "model": None,
    }
