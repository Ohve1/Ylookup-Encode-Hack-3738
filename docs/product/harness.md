# Harness

> Updated 2026-09-06 for the strict provenance contract (canonical-model v1).

The harness is a straight line from the anonymised pack to the reviewer lens. Nothing in the main path is an LLM; the optional candidate step hangs off the side and cannot move a value onto a Line.

```
data/raw/dataset01/            data/raw/dataset02/           (laptop only — not in repo)
   │  extract_pdf · extract_excel    │  normalize_gl.read_gl_groups (openpyxl read-only)
   ▼                                 ▼
data/extracted/{pdf,excel}.json   data/extracted/gl-groups.json
   │  scripts/normalize.py           │  scripts/normalize_gl.py
   │  raw_facts → evaluate_rules → compare(filed_snapshot) → Case / TieOut   (same contract)
   ▼                                 ▼
scripts/canonical_model.validate()                          ← gate 1
   ▼                                 ▼
data/processed/close.json         data/processed/close-dataset02.json
data/processed/decisions.jsonl    data/processed/decisions-dataset02.jsonl   ← append-only journals
   │  app/adapt_close.py  (workflow-aware labels / breakdown)
   ▼
app/server.py  /api/close  /api/decision  /api/assign  /api/suggest  /api/export  /api/metrics
   ▼
app/static/  reviewer lens  (sign-off → Download validated export)

pilot: scripts/run_pilot.py  → data/processed/pilot/<close_id>/{close.json, decisions.jsonl,
                               validated_mapping_<close_id>.csv, export.json, pilot-metrics.json}
       scripts/pilot_metrics.py  (also behind /api/metrics)
side:  app/gemini_suggest.py  → Case.suggestion.candidates[]  (drafts only)
CI:    scripts/ci_check.py  (fixture · both closes · every pilot copy)
       scripts/test_decision_replay.py · test_export.py · test_role_gates.py · test_pilot_metrics.py
```

`./run.sh` serves Dataset 01; `PACK=02 ./run.sh` serves Dataset 02; `CLOSE_FILE=… ./run.sh` serves any canonical close (e.g. a signed-off pilot copy, where the export download is live).

## Stages

| Stage | Entry | Output | Fails when |
|---|---|---|---|
| Extract | `scripts/ingest_dataset.py` | `data/extracted/*.json` | No PDF / xlsx under `--input` |
| Normalize | `normalize_to_canonical_model` | Lines with `raw_facts`, `filed_snapshot`, unique `bank_ref`, Rules, Cases, TieOuts | — |
| Validate | `validate(canonical)` | — | Missing lineage; filed fields used as rule inputs; ambiguous source marked resolved; `source_flags` ≠ 52/30/4/3; hard tie-out fail |
| Adapt | `adapt_close_for_reviewer` | View model with counts + `export_ready` / `export_blockers` | — |
| Decide | `POST /api/decision` | Decision appended to close + `decisions.jsonl` | Override without `supersedes`; empty reason |
| Sign off | `POST /api/decision {action: sign_off}` | Close signed off | Open Cases or hard tie-out fail |
| Export | `GET /api/export?profile=validated_mapping_csv_v1` | `validated_mapping_<close_id>.csv` | Not signed off; open Cases; tie-out fail; unsupported profile |
| Measure | `GET /api/metrics` · `scripts/pilot_metrics.py` | exception / override / review-round / hours-per-close / Rule health, from the record | — (unsupported fields are `null` with a reason) |
| Pilot replay | `scripts/run_pilot.py --close …` | signed-off copy + CSV + `pilot-metrics.json` under `data/processed/pilot/` | Any Case cannot be decided; sign-off gate; export gate |

## Dataset 02 in the same harness

| Object | Dataset 01 | Dataset 02 |
|---|---|---|
| Source | bank statement PDF page · Staging Sheet row | GL extract sheet (34k rows) · loader workbook sheets |
| Line | one statement row (100) | one movement group: Legal Entity × GL Account × Trans Type × currency (1,204) |
| Rule | Vendor Codes / Account Map / narrative patterns | CoA Mapping / LE Mapping / Deal Mapping crosswalk rows, version `v4c` |
| filed_snapshot | Staging Sheet matched columns | verified loader totals at (entity, trans type) |
| Case reasons | counterparty / project / position / review / rule_mismatch … | `no_matching_rule` (incl. Mapping Gaps) / `entity_miss` / `deal_miss` / `rule_mismatch` |
| Hard tie-out | staging_to_lines · DIU batch zero balance | GL abs rollup per currency · GL per-batch zero balance (934) |
| Residue | `source_flags` = 52 / 30 / 4 / 3 (validate) | `readme_residue` tie-outs = 4 / 16 / 198 + Mapping Gaps rows (ingest fails on mismatch) |

## Rule evaluation (cold start)

Rules evaluate **raw bank facts only**:

1. narrative / bank-charge patterns
2. exact counterparty master / Vendor Codes hits
3. deal / position dictionary hits from narrative tokens
4. account map / allocation (supporting fields)

Tautological “Classification equals X” rules are `kind = comparison_only` and never set Method.

A complete exact hit with no blocking reasons and agreement with the filed snapshot → `mapping_method = rule`. Disagreement → Case with `rule_mismatch`. Incomplete → Case with residue reasons.

## What the harness refuses to do

- Post anything to the system of record
- Emit an unverified Investran / eFront loader as if it were a shipped profile
- Let filed counterparty / project / position / classification enter rule evaluation
- Infer a mapping from an LLM
- Hide residue (`source_flags` must stay at README counts)
- Show a confidence score
- Treat an ambiguous PDF span as resolved lineage
- Export before sign-off / with open Cases / with failed hard tie-out

## Running the checks

```bash
python3 scripts/ci_check.py
python3 scripts/test_decision_replay.py
python3 scripts/test_export.py
python3 scripts/test_pilot_metrics.py
.venv/bin/python scripts/ingest_dataset.py --input data/raw/dataset01
.venv/bin/python scripts/ingest_dataset02.py --input data/raw/dataset02
.venv/bin/python scripts/run_pilot.py --close data/processed/close.json --close data/processed/close-dataset02.json --force
```
