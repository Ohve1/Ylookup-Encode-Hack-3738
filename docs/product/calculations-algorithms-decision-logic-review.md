# Calculations, Algorithms and Decision Logic — Product Review

**Status:** Implemented (strict contract v1), 2026-09-06  
**Scope:** Dataset 01  
**Verdict:** The blocking findings below were accepted and implemented. The processed close is regenerated under `contract_version: v1` and is not compatible with earlier closes.

## What changed

### Provenance spine

```
facts        = extract_raw_facts(bank_line, source_pages)
evaluation   = evaluate_rules(facts, versioned_rules)   # never reads filed_*
comparison   = compare(evaluation, filed_snapshot)
origin       = derive_origin(evaluation, comparison, decisions)
```

- `Line.raw_facts` and `Line.filed_snapshot` are separated.
- Filed counterparty / project / position / classification never enter rule evaluation.
- `match_result` is `exact_hit | candidates | none` — not a confidence score.
- Tautological `Classification equals X` rules are `kind = comparison_only` and cannot set Method=Rule.

### Source residue vs derived reasons

- `Line.source_flags` preserve the README residue (`52/30/4/3`).
- `Case.reasons[]` are current derived blockers and may differ.
- Validation asserts source-flag totals, not derived-reason totals.

### Amounts, spans, tie-outs

- Staging amounts are signed (`credit +`, `debit −`) via `Decimal`.
- Source matching returns spans; ambiguous amount/date collisions are `ambiguous` and cannot resolve as Rule.
- DIU entity-currency footing is `not_applicable` when `Amount (LE)` is blank.
- Bank accounts validate against Account Map; GL accounts against CoA when present.

### Decisions

- Append-only journal: `data/processed/decisions.jsonl`
- Override requires explicit `supersedes`
- Reject stays Unresolved; Reject→Accept is Decision, not Override
- Covered by `scripts/test_decision_replay.py`

## Current Dataset 01 outcome (after re-ingest)

Honest rule coverage is intentionally lower than the previous tautological 25/100:

- Rules establish Method only when raw-fact evaluation is complete, agrees with the filed snapshot, and has unique source lineage.
- Transfer / acquisition narratives that only hit Related Party / Legal Entity masters remain Unresolved candidates (they are ambiguous with Investment Transfer).
- Overview now reports `auto_resolved_count`, `rule_mapping_count`, and `open_case_count` separately.

See `data/processed/rule-evaluation-report.json` for the 100-row applicability / agreement report.

## References

- `docs/canonical-model.md`
- `docs/product/harness.md`
- `docs/decisions/DECISION-LOG.md` (D-011, D-012)
- `scripts/normalize.py`
- `scripts/canonical_model.py`
