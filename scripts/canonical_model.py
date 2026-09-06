"""Canonical financial close model for Dataset 01.

Strict provenance contract (D-011 / D-012):
  raw_facts → evaluate_rules → compare(filed_snapshot) → origin
Filed fields never enter rule evaluation. Decisions are append-only.
"""
from __future__ import annotations

import json
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field, fields
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional, Type, TypeVar

MAPPING_METHODS = ("rule", "decision", "override")
MATCH_RESULTS = ("exact_hit", "candidates", "none")
RECON_CATEGORIES = ("timing", "our_error", "external_error", "unidentified", "mapping_gap")
MATERIALITY_TIERS = ("low", "medium", "high")
TASK_STATUSES = ("not_started", "in_progress", "blocked", "complete")
TIEOUT_STATUSES = ("passed", "failed", "not_applicable")
RULE_KINDS = ("mapping", "comparison_only")

# Derived Case reasons (may change as resolvers improve).
CASE_REASONS = (
    "counterparty_miss",
    "project_miss",
    "position_miss",
    "review_flag",
    "rule_mismatch",
    "duplicate_key",
    "first_seen",
    "source_ambiguous",
    "no_matching_rule",
    # Dataset 02 (GL → loader) residue — same Case object, GL row as Source.
    "entity_miss",
    "deal_miss",
    "investor_miss",
)

# Immutable Dataset 01 README residue — counted on Case.source_flags[].
EXPECTED_SOURCE_FLAG_COUNTS = {
    "counterparty_miss": 52,
    "project_miss": 30,
    "position_miss": 4,
    "review_flag": 3,
}

# Back-compat alias used by older callers / tests.
EXPECTED_REASON_COUNTS = EXPECTED_SOURCE_FLAG_COUNTS

REASON_PRIORITY = {
    "tieout_fail": -1,
    "review_flag": 0,
    "rule_mismatch": 1,
    "duplicate_key": 1,
    "source_ambiguous": 1,
    "position_miss": 2,
    "entity_miss": 2,
    "counterparty_miss": 3,
    "deal_miss": 3,
    "investor_miss": 3,
    "project_miss": 4,
    "first_seen": 5,
    "no_matching_rule": 6,
}

T = TypeVar("T")


def _from_known(cls: Type[T], data: dict[str, Any]) -> T:
    known = {f.name for f in fields(cls)}  # type: ignore[arg-type]
    return cls(**{k: v for k, v in data.items() if k in known})


@dataclass
class Close:
    close_id: str
    fund_id: str
    period: str
    workflow: str
    status: str
    contract_version: str = "v1"


@dataclass
class Source:
    source_id: str
    filename: str
    file_type: str
    role: str
    location: dict[str, Any] = field(default_factory=dict)
    text: Optional[str] = None


@dataclass
class Line:
    line_id: str
    close_id: str
    date: Optional[str]
    description: str
    amount: float
    currency: str
    source_ref: dict[str, Any]
    status: str
    raw_facts: dict[str, Any] = field(default_factory=dict)
    filed_snapshot: dict[str, Any] = field(default_factory=dict)
    source_flags: list[str] = field(default_factory=list)
    mapping: dict[str, Any] = field(default_factory=dict)
    rule_evaluation: Optional[dict[str, Any]] = None
    rule_id: Optional[str] = None
    case_id: Optional[str] = None
    bank_ref: Optional[dict[str, Any]] = None
    mapping_method: Optional[str] = None


@dataclass
class Rule:
    rule_id: str
    name: str
    condition: dict[str, Any]
    action: dict[str, Any]
    origin: str
    status: str
    version: str = "v0"
    kind: str = "mapping"  # mapping | comparison_only


@dataclass
class Case:
    case_id: str
    line_id: str
    reasons: list[str]
    primary_reason: str
    status: str
    priority: str
    source_flags: list[str] = field(default_factory=list)
    suggestion: Optional[dict[str, Any]] = None
    assigned_to: Optional[str] = None
    decision_id: Optional[str] = None
    partial_rule_id: Optional[str] = None
    recon_category: Optional[str] = None
    materiality_tier: Optional[str] = None
    opened_at: Optional[str] = None
    due_at: Optional[str] = None
    clearance_target: Optional[str] = None
    preparer: Optional[str] = None
    reviewer: Optional[str] = None


@dataclass
class CloseTask:
    task_id: str
    title: str
    owner: str
    reviewer: str
    due_day: str
    status: str
    dependency_ids: list[str] = field(default_factory=list)
    blocker_case_ids: list[str] = field(default_factory=list)
    required_for_signoff: bool = True
    note: Optional[str] = None


@dataclass
class Decision:
    decision_id: str
    action: str
    previous_value: dict[str, Any]
    final_value: dict[str, Any]
    decided_by: str
    role: str
    reason: str
    timestamp: str
    case_id: Optional[str] = None
    line_id: Optional[str] = None
    candidates: list[Any] = field(default_factory=list)
    chosen: Optional[dict[str, Any]] = None
    supersedes: Optional[str] = None


@dataclass
class TieOut:
    tieout_id: str
    close_id: str
    source_total: float
    line_total: float
    difference: float
    status: str
    currency: Optional[str] = None
    kind: Optional[str] = None
    note: Optional[str] = None
    batch_id: Optional[str] = None
    failed_batches: Optional[list[Any]] = None
    amount_basis: Optional[str] = None  # txn | entity | abs_rollup


@dataclass
class CanonicalClose:
    close: Close
    sources: list[Source]
    lines: list[Line]
    rules: list[Rule]
    cases: list[Case]
    decisions: list[Decision]
    tieouts: list[TieOut]
    tasks: list[CloseTask] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "close": asdict(self.close),
            "sources": [asdict(s) for s in self.sources],
            "lines": [asdict(ln) for ln in self.lines],
            "rules": [asdict(r) for r in self.rules],
            "cases": [asdict(c) for c in self.cases],
            "decisions": [asdict(d) for d in self.decisions],
            "tieouts": [asdict(t) for t in self.tieouts],
            "tasks": [asdict(t) for t in self.tasks],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CanonicalClose":
        close_data = dict(data["close"])
        close_data.setdefault("contract_version", "v0")
        canonical = cls(
            close=_from_known(Close, close_data),
            sources=[_from_known(Source, s) for s in data.get("sources", [])],
            lines=[_from_known(Line, ln) for ln in data.get("lines", [])],
            rules=[_from_known(Rule, r) for r in data.get("rules", [])],
            cases=[_from_known(Case, c) for c in data.get("cases", [])],
            decisions=[_from_known(Decision, d) for d in data.get("decisions", [])],
            tieouts=[_from_known(TieOut, t) for t in data.get("tieouts", [])],
            tasks=[_from_known(CloseTask, t) for t in data.get("tasks", [])],
        )
        ensure_close_tasks(canonical)
        return canonical


def ensure_close_tasks(canonical: CanonicalClose) -> None:
    if not canonical.tasks:
        canonical.tasks = [
            CloseTask("TASK-INGEST", "Evidence ingested", "Fund Accountant", "Fund Admin", "WD1", "complete"),
            CloseTask("TASK-CASE-REVIEW", "Resolve exception queue", "Fund Accountant", "Fund Admin", "WD3", "blocked", ["TASK-INGEST"]),
            CloseTask("TASK-TIE-OUT", "Complete batch tie-out", "Fund Accountant", "Fund Admin", "WD3", "blocked", ["TASK-INGEST"]),
            CloseTask("TASK-ADMIN-REVIEW", "Admin review of material residue", "Fund Admin", "Fund Manager", "WD4", "blocked", ["TASK-CASE-REVIEW", "TASK-TIE-OUT"]),
            CloseTask("TASK-MANAGER-SIGNOFF", "Manager sign-off", "Fund Manager", "Fund Manager", "WD5", "not_started", ["TASK-ADMIN-REVIEW"], required_for_signoff=False),
        ]

    by_id = {task.task_id: task for task in canonical.tasks}
    open_cases = [case for case in canonical.cases if case.status == "unresolved"]
    high_or_unassigned = [
        case for case in open_cases
        if case.priority == "high" or not case.assigned_to
    ]
    tieouts_pass = all(
        tie.status in ("passed", "not_applicable")
        for tie in canonical.tieouts
        if tie.kind in ("staging_to_lines", "diu_batch_zero_balance", "statement_row_count")
    )

    if task := by_id.get("TASK-CASE-REVIEW"):
        task.blocker_case_ids = [case.case_id for case in open_cases]
        task.status = "complete" if not open_cases else "blocked"
    if task := by_id.get("TASK-TIE-OUT"):
        task.status = "complete" if tieouts_pass else "blocked"
    if task := by_id.get("TASK-ADMIN-REVIEW"):
        task.blocker_case_ids = [case.case_id for case in high_or_unassigned]
        task.status = "complete" if not open_cases and tieouts_pass else "blocked"
    if task := by_id.get("TASK-MANAGER-SIGNOFF"):
        if canonical.close.status == "signed_off":
            task.status = "complete"
        elif not open_cases and tieouts_pass:
            task.status = "in_progress"
        else:
            task.status = "not_started"


class ValidationError(Exception):
    def __init__(self, errors: list[str]):
        self.errors = errors
        super().__init__("INGESTION FAILED\n" + "\n".join(f"  - {e}" for e in errors))


def primary_reason_of(reasons: list[str]) -> str:
    return min(reasons, key=lambda r: REASON_PRIORITY.get(r, 99))


def priority_for_reason(reason: str) -> str:
    if reason in ("review_flag", "position_miss", "rule_mismatch", "duplicate_key", "source_ambiguous", "entity_miss"):
        return "high"
    return "medium"


def derive_line_origin(
    line: Line,
    case: Optional[Case],
    decisions: list[Decision],
) -> str:
    """Pure replay: surface origin from action + supersedes, not event count."""
    line_decisions = sorted(
        [d for d in decisions if d.line_id == line.line_id and d.action != "sign_off"],
        key=lambda d: d.timestamp,
    )
    if line_decisions:
        latest = line_decisions[-1]
        if latest.action == "override":
            return "override"
        if latest.action == "accept":
            return "decision"
        if latest.action == "reject":
            return "unresolved"
    if case and case.status == "unresolved":
        return "unresolved"
    if line.mapping_method == "rule" and line.rule_id:
        return "rule"
    if line.mapping_method in ("decision", "override"):
        return line.mapping_method
    return "unresolved"


def append_decision_journal(
    decision: Decision,
    path: Path | str,
) -> None:
    """Append one Decision event to the append-only journal."""
    journal = Path(path)
    journal.parent.mkdir(parents=True, exist_ok=True)
    with journal.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(asdict(decision), ensure_ascii=False) + "\n")


def validate(canonical: CanonicalClose, *, check_residue: bool | None = None) -> None:
    errors: list[str] = []
    if check_residue is None:
        check_residue = canonical.close.close_id == "CLOSE-2026-03-CALDER-WEEK"

    close = canonical.close
    if not close.close_id:
        errors.append("Close missing close_id")
    if not close.fund_id:
        errors.append("Close missing fund_id")
    if not close.period:
        errors.append("Close missing period")
    if not close.workflow:
        errors.append("Close missing workflow")
    if not close.status:
        errors.append("Close missing status")

    if check_residue and close.contract_version != "v1":
        errors.append(
            f"Close.contract_version {close.contract_version!r} != 'v1' "
            "(strict provenance required)"
        )

    source_ids = {s.source_id for s in canonical.sources}
    for s in canonical.sources:
        if not s.source_id:
            errors.append("Source missing source_id")
        if not s.filename:
            errors.append(f"Source {s.source_id} missing filename")
        if not s.file_type:
            errors.append(f"Source {s.source_id} missing file_type")
        if not s.role:
            errors.append(f"Source {s.source_id} missing role")

    line_ids = {ln.line_id for ln in canonical.lines}
    rule_ids = {r.rule_id for r in canonical.rules}
    case_ids = {c.case_id for c in canonical.cases}
    decision_ids = {d.decision_id for d in canonical.decisions}

    for r in canonical.rules:
        if not r.version:
            errors.append(f"Rule {r.rule_id} missing version")
        if r.kind not in RULE_KINDS:
            errors.append(f"Rule {r.rule_id} kind {r.kind!r} invalid")
        if "confidence" in (r.condition or {}) or "confidence" in (r.action or {}):
            errors.append(f"Rule {r.rule_id} must not carry confidence")

    for ln in canonical.lines:
        prefix = f"Line {ln.line_id or '?'}"
        if not ln.line_id:
            errors.append("Line missing line_id")
        if not ln.close_id:
            errors.append(f"{prefix} missing close_id")
        elif ln.close_id != close.close_id:
            errors.append(f"{prefix} close_id mismatch")
        if ln.amount is None:
            errors.append(f"{prefix} missing amount")
        if not ln.source_ref or not ln.source_ref.get("source_id"):
            errors.append(f"{prefix} missing source_ref.source_id")
        else:
            sid = ln.source_ref["source_id"]
            if sid not in source_ids:
                errors.append(f"{prefix} source_ref -> unknown Source {sid}")
        if not ln.status:
            errors.append(f"{prefix} missing status")
        if ln.mapping_method is not None and ln.mapping_method not in MAPPING_METHODS:
            errors.append(f"{prefix} mapping_method {ln.mapping_method!r} invalid")
        if ln.status == "resolved" and ln.mapping_method is None:
            errors.append(f"{prefix} resolved without mapping_method")
        if ln.mapping_method == "rule" and not ln.rule_id:
            errors.append(f"{prefix} mapping_method=rule without rule_id")
        if ln.mapping_method in ("decision", "override") and not ln.case_id:
            errors.append(f"{prefix} mapping_method={ln.mapping_method} without case_id")
        if ln.rule_id and ln.rule_id not in rule_ids:
            errors.append(f"{prefix} rule_id -> unknown Rule {ln.rule_id}")
        if ln.case_id and ln.case_id not in case_ids:
            errors.append(f"{prefix} case_id -> unknown Case {ln.case_id}")

        if check_residue:
            if not ln.raw_facts:
                errors.append(f"{prefix} missing raw_facts")
            if not ln.filed_snapshot:
                errors.append(f"{prefix} missing filed_snapshot")
            # Filed fields must not appear inside raw_facts.
            for forbidden in (
                "matched_counterparty",
                "matched_project",
                "resolved_position",
                "resolved_deal",
                "filed_classification",
            ):
                if forbidden in (ln.raw_facts or {}):
                    errors.append(f"{prefix} raw_facts must not contain {forbidden}")

        if ln.bank_ref:
            if ln.bank_ref.get("source_id") and ln.bank_ref["source_id"] not in source_ids:
                errors.append(f"{prefix} bank_ref -> unknown Source {ln.bank_ref['source_id']}")
            if "match_method" not in ln.bank_ref:
                errors.append(f"{prefix} bank_ref missing match_method")
            if ln.bank_ref.get("match_method") == "ambiguous":
                if ln.mapping_method == "rule" and ln.status == "resolved":
                    errors.append(f"{prefix} ambiguous source cannot be rule-resolved")
            if ln.bank_ref.get("match_method") in ("exact", "exact_ref", "normalized"):
                if ln.bank_ref.get("ambiguous"):
                    errors.append(f"{prefix} unique match marked ambiguous")

        if ln.rule_id:
            rule = next((r for r in canonical.rules if r.rule_id == ln.rule_id), None)
            if rule and rule.kind == "comparison_only" and ln.mapping_method == "rule":
                errors.append(
                    f"{prefix} comparison_only rule {ln.rule_id} cannot set Method=Rule"
                )

    flag_counts: Counter[str] = Counter()
    for ln in canonical.lines:
        flag_counts.update(ln.source_flags or [])

    for c in canonical.cases:
        prefix = f"Case {c.case_id or '?'}"
        if not c.case_id:
            errors.append("Case missing case_id")
        if not c.line_id:
            errors.append(f"{prefix} missing line_id")
        elif c.line_id not in line_ids:
            errors.append(f"{prefix} line_id -> unknown Line {c.line_id}")
        if not c.reasons:
            errors.append(f"{prefix} missing reasons[]")
        else:
            expected_primary = primary_reason_of(c.reasons)
            if c.primary_reason != expected_primary:
                errors.append(
                    f"{prefix} primary_reason {c.primary_reason!r} != {expected_primary!r}"
                )
        if c.status not in ("unresolved", "decided"):
            errors.append(f"{prefix} status {c.status!r} invalid")
        if c.partial_rule_id and c.partial_rule_id not in rule_ids:
            errors.append(f"{prefix} partial_rule_id -> unknown Rule {c.partial_rule_id}")
        if c.decision_id and c.decision_id not in decision_ids:
            errors.append(f"{prefix} decision_id -> unknown Decision {c.decision_id}")
        if c.suggestion is not None:
            for bad in ("mapping_method", "method_label", "source", "label", "confidence"):
                if bad in c.suggestion:
                    errors.append(f"{prefix} suggestion.{bad} is not allowed")
        if c.recon_category is not None and c.recon_category not in RECON_CATEGORIES:
            errors.append(f"{prefix} recon_category {c.recon_category!r} invalid")
        if c.materiality_tier is not None and c.materiality_tier not in MATERIALITY_TIERS:
            errors.append(f"{prefix} materiality_tier {c.materiality_tier!r} invalid")

    if check_residue:
        for reason, expected in EXPECTED_SOURCE_FLAG_COUNTS.items():
            actual = flag_counts.get(reason, 0)
            if actual != expected:
                errors.append(
                    f"README source_flags {reason}: got {actual}, expected {expected}"
                )

    for d in canonical.decisions:
        prefix = f"Decision {d.decision_id or '?'}"
        if not d.decision_id:
            errors.append("Decision missing decision_id")
        if d.action == "sign_off":
            if d.case_id or d.line_id:
                errors.append(f"{prefix} sign_off must not reference case_id/line_id")
        else:
            if not d.case_id:
                errors.append(f"{prefix} missing case_id")
            elif d.case_id not in case_ids:
                errors.append(f"{prefix} case_id -> unknown Case {d.case_id}")
            if not d.line_id:
                errors.append(f"{prefix} missing line_id")
            elif d.line_id not in line_ids:
                errors.append(f"{prefix} line_id -> unknown Line {d.line_id}")
        if d.action == "override" and not d.supersedes:
            errors.append(f"{prefix} override requires supersedes")
        if d.supersedes and d.supersedes not in decision_ids and d.supersedes != d.decision_id:
            # Allow forward validation during append of the same batch.
            if d.supersedes not in {x.decision_id for x in canonical.decisions}:
                errors.append(f"{prefix} supersedes -> unknown Decision {d.supersedes}")

    for t in canonical.tieouts:
        if not t.tieout_id:
            errors.append("TieOut missing tieout_id")
        if t.close_id != close.close_id:
            errors.append(f"TieOut {t.tieout_id} close_id mismatch")
        if t.status not in TIEOUT_STATUSES:
            errors.append(f"TieOut {t.tieout_id} status {t.status!r} invalid")
        if t.kind == "staging_to_lines" and t.status == "failed":
            errors.append(
                f"TieOut {t.tieout_id} staging_to_lines difference={t.difference}"
            )
        if t.kind == "diu_batch_zero_balance" and t.status == "failed":
            errors.append(
                f"TieOut {t.tieout_id} diu_batch_zero_balance failed "
                f"(failed_batches={t.failed_batches})"
            )
        if t.kind == "statement_row_count" and t.status == "failed":
            errors.append(f"TieOut {t.tieout_id} statement_row_count failed")

    task_ids = {t.task_id for t in canonical.tasks}
    for task in canonical.tasks:
        prefix = f"CloseTask {task.task_id or '?'}"
        if not task.task_id:
            errors.append("CloseTask missing task_id")
        if not task.title or not task.owner or not task.reviewer or not task.due_day:
            errors.append(f"{prefix} missing title, owner, reviewer, or due_day")
        if task.status not in TASK_STATUSES:
            errors.append(f"{prefix} status {task.status!r} is invalid")
        for dependency_id in task.dependency_ids:
            if dependency_id not in task_ids:
                errors.append(f"{prefix} dependency -> unknown CloseTask {dependency_id}")
        for blocker_id in task.blocker_case_ids:
            if blocker_id not in case_ids:
                errors.append(f"{prefix} blocker -> unknown Case {blocker_id}")

    if errors:
        raise ValidationError(errors)


def record_decision(
    canonical: CanonicalClose,
    *,
    case_id: str,
    action: str,
    decided_by: str,
    role: str,
    reason: str,
    final_value: dict[str, Any],
    candidates: Optional[list[Any]] = None,
    chosen_candidate_index: Optional[int] = None,
    previous_value: Optional[dict[str, Any]] = None,
    decision_id: Optional[str] = None,
    timestamp: Optional[str] = None,
    supersedes: Optional[str] = None,
    journal_path: Optional[Path | str] = None,
) -> Decision:
    case = next((c for c in canonical.cases if c.case_id == case_id), None)
    if case is None:
        raise ValidationError([f"unknown case_id {case_id}"])

    line = next((ln for ln in canonical.lines if ln.line_id == case.line_id), None)
    if line is None:
        raise ValidationError([f"Case {case_id} references unknown Line {case.line_id}"])

    if action not in ("accept", "reject", "override"):
        raise ValidationError([f"invalid action {action!r}"])

    prior = [
        d for d in canonical.decisions
        if d.line_id == line.line_id and d.action in ("accept", "override")
    ]
    if action == "override":
        if not supersedes and prior:
            supersedes = prior[-1].decision_id
        if not supersedes:
            raise ValidationError(["override requires supersedes"])
        if case.status != "decided" and not prior:
            # First resolution on an open case should be accept, not override,
            # unless a prior accept exists.
            raise ValidationError(
                ["override requires a prior accept/override Decision to supersede"]
            )
    elif action in ("accept", "reject") and case.status == "decided":
        raise ValidationError(
            [f"Case {case_id} is already decided; use override to replace"]
        )

    n = len(canonical.decisions) + 1
    did = decision_id or f"DEC-{n:03d}"
    ts = timestamp or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    prev = previous_value
    if prev is None:
        prev = {}
        for key in ("account", "classification", "project_code", "counterparty"):
            if line.mapping.get(key) is not None:
                prev[key] = line.mapping.get(key)

    drafted = list(((case.suggestion or {}).get("candidates")) or [])
    snapshot = list(candidates) if candidates is not None else drafted

    chosen: Optional[dict[str, Any]] = None
    if action == "accept":
        if chosen_candidate_index is not None:
            if not (0 <= chosen_candidate_index < len(snapshot)):
                raise ValidationError(
                    [f"chosen_candidate_index {chosen_candidate_index} out of range"]
                )
            chosen = dict(snapshot[chosen_candidate_index])
        else:
            chosen = {"treatment": "Workbook proposal", **final_value}

    decision = Decision(
        decision_id=did,
        case_id=case_id,
        line_id=line.line_id,
        action=action,
        previous_value=prev,
        final_value=final_value,
        decided_by=decided_by,
        role=role,
        reason=reason,
        timestamp=ts,
        candidates=snapshot,
        chosen=chosen,
        supersedes=supersedes,
    )
    canonical.decisions.append(decision)
    case.decision_id = did
    if action in ("accept", "override"):
        case.status = "decided"
        line.status = "resolved"
        line.mapping_method = "decision" if action == "accept" else "override"
        for key, value in final_value.items():
            if key in ("account", "classification", "project_code", "counterparty", "fund"):
                line.mapping[key] = value
    elif action == "reject":
        case.status = "unresolved"
        line.status = "unresolved"
        line.mapping_method = None

    ensure_close_tasks(canonical)
    validate(
        canonical,
        check_residue=canonical.close.close_id == "CLOSE-2026-03-CALDER-WEEK",
    )
    if journal_path is not None:
        append_decision_journal(decision, journal_path)
    return decision


def record_batch_sign_off(
    canonical: CanonicalClose,
    *,
    decided_by: str,
    role: str,
    reason: str,
    decision_id: Optional[str] = None,
    timestamp: Optional[str] = None,
    journal_path: Optional[Path | str] = None,
) -> Decision:
    ensure_close_tasks(canonical)
    if any(d.action == "sign_off" for d in canonical.decisions):
        raise ValidationError(["batch already signed off"])
    if canonical.close.status == "signed_off":
        raise ValidationError(["batch already signed off"])

    open_cases = [c for c in canonical.cases if c.status == "unresolved"]
    if open_cases:
        raise ValidationError(
            [f"cannot sign off: {len(open_cases)} open case(s) remain"]
        )

    batch_tie = next(
        (t for t in canonical.tieouts if t.kind == "diu_batch_zero_balance"),
        None,
    )
    if batch_tie is not None and batch_tie.status == "failed":
        raise ValidationError(["cannot sign off: tie-out is not PASS"])

    incomplete_tasks = [
        task.task_id
        for task in canonical.tasks
        if task.required_for_signoff and task.status != "complete"
    ]
    if incomplete_tasks:
        raise ValidationError(
            ["cannot sign off: incomplete close task(s): " + ", ".join(incomplete_tasks)]
        )

    n = len(canonical.decisions) + 1
    did = decision_id or f"DEC-{n:03d}"
    ts = timestamp or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    decision = Decision(
        decision_id=did,
        case_id=None,
        line_id=None,
        action="sign_off",
        previous_value={"close_status": canonical.close.status},
        final_value={"close_status": "signed_off"},
        decided_by=decided_by,
        role=role,
        reason=reason,
        timestamp=ts,
        candidates=[],
        chosen=None,
    )
    canonical.decisions.append(decision)
    canonical.close.status = "signed_off"
    ensure_close_tasks(canonical)
    validate(
        canonical,
        check_residue=canonical.close.close_id == "CLOSE-2026-03-CALDER-WEEK",
    )
    if journal_path is not None:
        append_decision_journal(decision, journal_path)
    return decision


def assign_case(
    canonical: CanonicalClose,
    *,
    case_id: str,
    assigned_to: Optional[str],
) -> Case:
    case = next((c for c in canonical.cases if c.case_id == case_id), None)
    if case is None:
        raise ValidationError([f"unknown case_id {case_id}"])
    case.assigned_to = (assigned_to or "").strip() or None
    ensure_close_tasks(canonical)
    validate(canonical, check_residue=False)
    return case


def count_metrics(canonical: CanonicalClose) -> dict[str, int]:
    open_cases = {c.line_id for c in canonical.cases if c.status == "unresolved"}
    rule_mapping = sum(1 for ln in canonical.lines if ln.mapping_method == "rule")
    auto_resolved = sum(
        1
        for ln in canonical.lines
        if ln.mapping_method == "rule" and ln.line_id not in open_cases
    )
    return {
        "auto_resolved_count": auto_resolved,
        "rule_mapping_count": rule_mapping,
        "open_case_count": len(open_cases),
        "line_count": len(canonical.lines),
    }
