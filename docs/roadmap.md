# Roadmap

Sequenced by control-layer maturity, not by “more AI” or feature size.

Product boundary stays fixed: **validated export**, not SoR API write-back.  
Dataset 01 and Dataset 02 remain **two validation cases** of one workflow.

---

## NOW — Complete the workflow

Ship and demo the end-to-end control object:

- ✓ Lines
- ✓ Rules
- ✓ Cases
- ✓ Source lineage
- ✓ Review
- ✓ Decision
- ✓ Tie-out
- ✓ Three user layers (Resolve / Coordinate / Approve)
- ✓ Validated export (`validated_mapping_csv_v1` download after sign-off — not SoR API)
- ✓ Dataset 02 adapter (`scripts/ingest_dataset02.py`): GL movement groups → the same Line / Rule / Case / TieOut objects; README2 residue (4 / 16 / 198) preserved as tie-outs
- ✓ End-to-end on both real packs, scripted (`scripts/run_pilot.py`): every Case decided with a reason → sign-off → `validated_mapping_<close_id>.csv` → `pilot-metrics.json`, on a copy under `data/processed/pilot/`

Dataset 02 is framed as the same Case type proving generalisation — not “Feature 2.”

**First question for demo:**  
Can every financial item’s treatment be seen, validated, reviewed, recorded, and leave as a validated output?

---

## NEXT — Make the system compound

Stop adding surface features. Compound the record:

| Item | Why |
|---|---|
| Precedent promotion | Case → Decision → dual-control → Rule → future close |
| Dual-control approval | One accountant Decision must never auto-become a Rule |
| Rule versioning | Every Line cites rule id + version; re-run shows what would move |
| Staleness detection | High override rate → ⚠ potentially stale precedent |
| Better mapping / extraction | Only where it reduces Cases without hiding judgment |
| Dataset 02 investor grain | Adapter maps at movement-group grain; the 198 unmatched investors are a residue tie-out, not yet per-Line Cases |

UI affordance example (NEXT, not claimed shipped):

```
Case #237
Final decision: Account 7100
[Approve]  [Override]  [Promote to Rule]
```

Promote requires a second approval.

---

## VALIDATE — Prove business value

Pilot shape (do not invent LP acceptance before this):

- 1 administrator
- 1 fund
- 3 closes

**Instrumentation — built (`scripts/pilot_metrics.py`, `GET /api/metrics`); human measurement pending:**

| Metric | Intent | How it is derived | Status |
|---|---|---|---|
| Hours per close | Does the control layer shorten the cycle? | first Case opened / first Decision → sign-off | instrumented; scripted runs report the value but label it not-evidence |
| Review rounds | Does manager shadow re-verification drop? | Decisions per decided Case (reject → re-decide) | instrumented |
| Exception rate | Residue size over time | Cases / Lines, by primary reason | instrumented — D01 0.90, D02 0.0855 |
| Override rate | On stable patterns / Rules — learning, not person score | Overrides / decided Cases; per-Rule override rate → `potentially_stale` at ≥ 25% | instrumented — 0.0 in scripted runs (no overrides synthesised) |
| Error rate | After validated export is loaded | requires the system of record | `null` with reason |

Scripted baseline exists for both packs (`data/processed/pilot/*/pilot-metrics.json`, `run.kind = scripted_replay`). What VALIDATE still needs: the same run with one administrator making the Decisions through the lens, on three closes, so `hours_per_close` and `review_rounds` become human numbers.

Trust thesis: automation that monitors whether its own precedent remains reliable.

---

## LATER — Scale the boundary

Only after VALIDATE shows payback:

- More target export formats (verified Investran / eFront / DIU dual-leg loaders) — beyond shipped `validated_mapping_csv_v1`
- More source types
- Enterprise integrations
- APIs **around the control layer** (not replacing the SoR write path as the product)

---

## Explicitly cut (do not build)

- Generic finance chatbot
- Investment analytics / portfolio management / investor dashboard
- Autonomous accounting agent
- Complex SoR API write-back “to look complete”
- Large AI feature stacks ahead of lineage + export
- Hardcoded Dataset-01-only logic that cannot generalise to Dataset 02
- Analytics that do not change Resolve / Coordinate / Approve behaviour
- Replacing the system of record
- Unattended posting
- Keystroke telemetry
- Claiming LP / auditor acceptance before pilot metrics exist
