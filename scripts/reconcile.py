#!/usr/bin/env python3
"""Deterministic reconciliation helpers for the close-control layer.

This module intentionally proposes nothing to the mapping engine.  It groups
evidence before classification: exact reference/amount first, bounded
tolerance matching second, then a small one-to-many search.  Any non-exact
result must become a Case for review; no function here can resolve a Line.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from itertools import combinations
import re
from typing import Iterable


@dataclass(frozen=True)
class Transaction:
    transaction_id: str
    amount: Decimal
    reference: str = ""
    booked_on: str | None = None


@dataclass(frozen=True)
class MatchGroup:
    left_ids: tuple[str, ...]
    right_ids: tuple[str, ...]
    method: str
    difference: Decimal
    review_required: bool


def decimal_amount(value: object) -> Decimal:
    """Parse a financial amount strictly; malformed values never become zero."""
    if isinstance(value, Decimal):
        return value
    text = str(value).strip().replace(",", "")
    if not text:
        raise ValueError("amount is blank")
    try:
        return Decimal(text)
    except InvalidOperation as exc:
        raise ValueError(f"invalid amount {value!r}") from exc


def normalise_reference(value: str) -> str:
    return re.sub(r"[^A-Z0-9]", "", (value or "").upper())


def _date_distance(left: Transaction, right: Transaction) -> int | None:
    if not left.booked_on or not right.booked_on:
        return None
    try:
        return abs((date.fromisoformat(left.booked_on) - date.fromisoformat(right.booked_on)).days)
    except ValueError:
        return None


def exact_matches(left: Iterable[Transaction], right: Iterable[Transaction]) -> list[MatchGroup]:
    """One-to-one, non-reused matches with both reference and amount equal."""
    used_right: set[str] = set()
    output: list[MatchGroup] = []
    for item in sorted(left, key=lambda txn: txn.transaction_id):
        ref = normalise_reference(item.reference)
        if not ref:
            continue
        for candidate in sorted(right, key=lambda txn: txn.transaction_id):
            if candidate.transaction_id in used_right:
                continue
            if candidate.amount == item.amount and normalise_reference(candidate.reference) == ref:
                used_right.add(candidate.transaction_id)
                output.append(MatchGroup((item.transaction_id,), (candidate.transaction_id,), "exact", Decimal("0"), False))
                break
    return output


def tolerance_matches(
    left: Iterable[Transaction],
    right: Iterable[Transaction],
    *,
    tolerance: Decimal = Decimal("0.01"),
    max_days: int = 2,
    already_matched_left: set[str] | None = None,
    already_matched_right: set[str] | None = None,
) -> list[MatchGroup]:
    """Find nearest amount/date candidates. All such matches require review."""
    used_left = set(already_matched_left or ())
    used_right = set(already_matched_right or ())
    output: list[MatchGroup] = []
    for item in sorted(left, key=lambda txn: txn.transaction_id):
        if item.transaction_id in used_left:
            continue
        candidates = []
        for candidate in right:
            if candidate.transaction_id in used_right:
                continue
            difference = abs(item.amount - candidate.amount)
            days = _date_distance(item, candidate)
            if difference <= tolerance and (days is None or days <= max_days):
                candidates.append((difference, days if days is not None else max_days + 1, candidate))
        if candidates:
            difference, _, candidate = min(candidates, key=lambda value: (value[0], value[1], value[2].transaction_id))
            used_left.add(item.transaction_id)
            used_right.add(candidate.transaction_id)
            output.append(MatchGroup((item.transaction_id,), (candidate.transaction_id,), "amount_date_tolerance", difference, True))
    return output


def one_to_many_match(
    target: Transaction,
    candidates: Iterable[Transaction],
    *,
    tolerance: Decimal = Decimal("0.01"),
    max_members: int = 4,
) -> MatchGroup | None:
    """Bounded subset search for batched settlements; always review-required."""
    items = sorted(candidates, key=lambda txn: txn.transaction_id)
    for size in range(2, min(max_members, len(items)) + 1):
        for group in combinations(items, size):
            difference = abs(target.amount - sum((item.amount for item in group), Decimal("0")))
            if difference <= tolerance:
                return MatchGroup(
                    (target.transaction_id,),
                    tuple(item.transaction_id for item in group),
                    "one_to_many",
                    difference,
                    True,
                )
    return None


def _selftest() -> None:
    bank = [
        Transaction("B-1", decimal_amount("100.00"), "INV-42", "2026-03-31"),
        Transaction("B-2", decimal_amount("249.99"), "FEE", "2026-03-31"),
    ]
    ledger = [
        Transaction("L-1", decimal_amount("100.00"), "inv 42", "2026-03-31"),
        Transaction("L-2", decimal_amount("250.00"), "FEE", "2026-04-01"),
    ]
    exact = exact_matches(bank, ledger)
    assert exact == [MatchGroup(("B-1",), ("L-1",), "exact", Decimal("0"), False)]
    tolerant = tolerance_matches(bank, ledger, already_matched_left={"B-1"}, already_matched_right={"L-1"})
    assert tolerant == [MatchGroup(("B-2",), ("L-2",), "amount_date_tolerance", Decimal("0.01"), True)]
    batched = one_to_many_match(Transaction("B-3", Decimal("300")), [Transaction("L-3", Decimal("120")), Transaction("L-4", Decimal("180"))])
    assert batched and batched.right_ids == ("L-3", "L-4") and batched.review_required
    try:
        decimal_amount("TWENTY THOUSAND")
    except ValueError:
        pass
    else:
        raise AssertionError("malformed amount must not become zero")


if __name__ == "__main__":
    _selftest()
    print("reconcile: exact, tolerance, one-to-many, and strict parse checks OK")
