# Canonical model

Contract for one shared close object. Excel is a view, not the book of record.

These are **close-workflow work objects**, not merely engineering tables. Reviewers and operators act on them; three roles share the same chain.

| Work object | Product question |
|---|---|
| **LINE** | What financial item are we processing? |
| **RULE** | How do we normally treat this type of item? |
| **CASE** | What cannot be resolved automatically? |
| **DECISION** | What did the human ultimately decide? |
| **SOURCE** | What evidence supports this? |
| **EXPORT** | What validated result leaves the system? |

On any reviewer surface a Line is in exactly one origin:

**Rule | Decision | Override | Unresolved**

**Contract version:** v1 (strict). Older processed closes without `raw_facts` / `filed_snapshot` are not supported.

## Provenance spine

```
facts        = extract_raw_facts(source_line, source_pages)
evaluation   = evaluate_rules(facts, versioned_rules)   # never reads filed_*
comparison   = compare(evaluation, filed_snapshot)
origin       = derive_origin(evaluation, comparison, decisions)
export       = emit_validated(export_profile)           # after tie-out + decisions
```

`filed_snapshot` is comparison-only. It must never enter rule evaluation.

Match results are not confidence scores:

| `match_result` | Meaning |
|---|---|
| `exact_hit` | Condition matched completely; may establish a Rule when the action is complete |
| `candidates` | Suggestions only; Case stays Unresolved |
| `none` | No match; Case stays Unresolved |

## LINE — What financial item are we processing?

One journal / loader row (Bank→JE or GL→Loader — same object).

```
Line
+-- id
+-- close_id
+-- date
+-- description
+-- amount / currency          # signed Decimal as float JSON; credit +, debit −
+-- raw_facts                  # immutable source facts used by rules
+-- filed_snapshot             # accountant workbook values; comparison only
+-- source_flags[]             # immutable README / workbook residue evidence
+-- source_ref                 # staging row pointer
+-- bank_ref                   # PDF span(s); unique exact/normalized, else ambiguous
+-- rule_evaluation            # result of evaluate_rules
+-- mapping                    # current proposed / accepted treatment
+-- mapping_method             # rule | decision | override | null
+-- rule_id + rule_version     # if mapping_method = rule
+-- case_id
+-- status                     # resolved | unresolved
```

## RULE — How do we normally treat this type of item?

Versioned map entry. Fund account authors cold-start from workbook sheets. Precedent promotion (NEXT) creates new versions under dual control.

```
Rule
+-- id
+-- version
+-- condition       -> narrative / vendor / account / master membership …
+-- action          -> proposed treatment fields
+-- origin          -> workbook sheet + row | promoted_from_decision
+-- status          -> active | stale | retired
+-- kind            -> mapping | comparison_only
+-- health          -> used / accepted / overridden / override_rate   (NEXT)
```

No “confidence” field. A `comparison_only` rule (for example tautological “Classification equals X”) may explain a filed snapshot but **must not** set `mapping_method = rule`.

### Rule health (NEXT — compound the system)

Example surface:

```
RULE R-023
Used: 87
Accepted: 81
Overridden: 6
Override rate: 6.9%
Status: Active
```

If override rate crosses a policy threshold (e.g. 30%):

```
⚠ Potentially stale precedent
```

Stale is a control signal, not automatic retirement. Bad decisions must not accumulate into silent automation.

## CASE — What cannot be resolved automatically?

Opened when there is no complete exact Rule, or the operator would guess.

```
Case
+-- id
+-- line_id
+-- source_flags[]     # copy of Line.source_flags when a Case exists
+-- reasons[]          # current derived blocking / mismatch reasons
+-- primary_reason
+-- status             # unresolved | decided
+-- priority
+-- partial_rule_id    # clue only; never Method
+-- suggestion         # drafted candidates only
+-- decision_id
+-- control fields     # recon category, materiality, preparer/reviewer, …
```

`Line.source_flags` preserve the Dataset 01 README residue (`52/30/4/3`). Derived `Case.reasons[]` may differ after a better resolver runs.

Allowed derived reasons include: `counterparty_miss`, `project_miss`, `position_miss`, `review_flag`, `rule_mismatch`, `duplicate_key`, `first_seen`, `source_ambiguous`, `no_matching_rule`, `mapping_gap`.

## DECISION — What did the human ultimately decide?

Append-only human event. Also written to `data/processed/decisions.jsonl`.

```
Decision
+-- id
+-- action            # accept | reject | override | sign_off | promote_request
+-- case_id / line_id # null on sign_off
+-- previous_value / final_value
+-- decided_by / role / reason / timestamp
+-- candidates[] / chosen
+-- supersedes        # required on override; points at prior Decision id
+-- promote_to_rule   # optional; requires dual-control second approval (NEXT)
```

Replay is by action and `supersedes`, never by event count. Reject keeps the Case Unresolved and is not an Override.

### Precedent promotion (NEXT)

```
Case → Human decision → Manager / dual-control approval
     → "Promote as precedent?" → versioned Rule → future close
```

A single accountant Decision never auto-becomes a Rule. Path is always:

```
Decision → Second approval → Rule
```

## SOURCE — What evidence supports this?

Unchanged in role: PDF page/string, workbook cell, GL row, or (later) legal clause. Every Line must show evidence before resolution.

## EXPORT — What validated result leaves the system?

Architecture boundary. The product emits a **validated export file**. It does not call SoR APIs.

**Shipped profile:** `validated_mapping_csv_v1`

```
Export
+-- id
+-- close_id / slice_id
+-- profile            # validated_mapping_csv_v1 (NOW)
+-- file_name          # validated_mapping_<close_id>.csv
+-- line_ids[]         # resolved lines with mapping_method in {rule, decision, override}
+-- tie_out_status     # must be passed (or not_applicable where allowed)
+-- generated_at / generated_by
```

**Gate (re-checked on every download):** batch signed off; zero open Cases; required close tasks complete; hard tie-outs passed / not_applicable.

**CSV columns (stable order):**  
`line_id, date, description, amount, currency, classification, project_code, counterparty, fund, account, account_number, bank_account, mapping_method, rule_id, rule_version, decision_id, source_id, source_excerpt, source_location, close_id, export_profile`

Operator loads the file into the existing accounting system. That hand-off is intentional.

**LATER:** system-specific loader profiles (`investran_loader`, `efront_loader`, DIU dual-leg) only after a verified target schema exists. Do not claim them as shipped.

API: `GET /api/export?profile=validated_mapping_csv_v1` → attachment, or `409` with blockers.

## TieOut / CloseTask

Tie-out statuses are `passed` | `failed` | `not_applicable`.

- GL accounts validate against `CoA`
- Bank account numbers / labels validate against `Account Map`
- Entity-currency footing is `not_applicable` when `Amount (LE)` is blank
- Statement control totals use signed amounts (`closing = opening + Σ signed`)

## Counts (Dataset 01)

| Metric | Meaning |
|---|---|
| `auto_resolved_count` | Lines with no open Case and `mapping_method = rule` |
| `rule_mapping_count` | Lines with `mapping_method = rule` (may still have a review Case) |
| `open_case_count` | Cases with `status = unresolved` |
| `source_flags` totals | Must equal README `52/30/4/3` on Dataset 01 **Lines** |

## As implemented

| Doc field | JSON field |
|---|---|
| origin | derived in `app/adapt_close.py::display_method` |
| Rule.confidence | forbidden (CI fails) |
| Case.candidates[] | `Case.suggestion.candidates[]` |
| Case.audit_history | Decision events + `decisions.jsonl` |
| P&L delta | candidate field `pnl_delta` when journal legs known |
| Export | `scripts/emit_export.py` + `GET /api/export`; overview `export_ready` |
| Rule.health / promote | roadmap NEXT — not claimed as shipped |
