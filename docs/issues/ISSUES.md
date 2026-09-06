# Issues

> Reconstructed 2026-09-06. Open items that a reviewer would trip on, in the order they would trip on them. Closed items are kept so the fix is traceable.

## Open

| # | Issue | Impact | Owner / plan |
|---|---|---|---|
| I-07 | Cold-start rule library previously used tautological "Classification equals X" rules. Those are now `kind=comparison_only` and cannot set Method=Rule (D-011). | Honest Rule coverage is lower than 25/100; judgment remains Cases | Monitor rule-evaluation-report.json; promote only with dual sign-off (D-008) |
| I-16 | Pilot metrics exist only from a scripted replay (`run.kind = scripted_replay`); `hours_per_close` / `review_rounds` are not human numbers yet | VALIDATE cannot claim payback | Run 1 admin × 3 closes through the lens; compare `/api/metrics` against the scripted baseline |
| I-17 | Dataset 02 Lines are movement groups (LE × GL account × trans type); the 198 unmatched investors are preserved as a `readme_residue` tie-out, not per-Line Cases | Investor-level decisions are not yet individually recorded | NEXT: investor grain adapter or a sub-Case per unmatched investor |
| I-18 | Dataset 01 `validated_mapping` rows carry classification but no GL `account` (Line.mapping has none; the DIU holds accounts per batch) | Export is a mapping record, not a loader | LATER: DIU dual-leg profile once schema verified |
| I-09 | Candidate drafting has not been exercised against the live model in this repo state (no API key on the build machine). Evidence validation is unit-tested with synthetic responses. | Feature is off by default; UI shows the off state | Set `GOOGLE_API_KEY` in `.env`, draft on a `review_flag` Case, confirm refs resolve |
| I-10 | ~~`close.json` is rewritten in place; there is no append-only decision journal~~ **Mitigated:** `data/processed/decisions.jsonl` is appended on every Decision; close.json still holds the materialised view | Concurrent reviewers could still clobber close.json | NEXT: rebuild close from journal |
| I-11 | Severity is derived from primary reason; amount is used in queue sort | Large counterparty miss ranks by amount after severity | Tune thresholds per fund |
| I-12 | Reject leaves the Case Unresolved but does not re-route it to anyone | Admin must assign manually | NEXT: reject → assign back to author |
| I-13 | Precedent promotion + Rule health (staleness) are in product logic / roadmap but not built | Compounding story is narrative-only until NEXT | Dual-control promote; override-rate stale flag |

## Closed

| # | Issue | Fix |
|---|---|---|
| I-08 | Dataset 02 had no adapter; generalisation was narrative-only | `scripts/ingest_dataset02.py` + `scripts/normalize_gl.py`: 33,902 GL rows → 1,204 movement-group Lines, 255 crosswalk Rules (exact hit, `v4c`), 103 Cases (`no_matching_rule` 66 / `entity_miss` 30 / `rule_mismatch` 10 / `deal_miss` 8), README2 residue 4 / 16 / 198 as `readme_residue` tie-outs; `PACK=02 ./run.sh`; CI checks the close |
| I-19 | Real close never walked to export (0 Decisions, `in_review`, no CSV) | `scripts/run_pilot.py` decides every Case with a reason on a copy, signs off, emits `validated_mapping_<close_id>.csv` for both packs under `data/processed/pilot/`; CI asserts each pilot copy is signed off with zero open Cases and has an export + metrics |
| I-15 | Docs RACI said Accountant does not Decide Cases but UI/API allowed Accept for all roles | UI + `ROLE_ACTIONS` gate: Accountant prepare-only; Admin Decide; Manager Approve/Override; CI `test_role_gates.py` |
| I-14 | Validated export emit path missing from demo | `validated_mapping_csv_v1` via `scripts/emit_export.py` + `GET /api/export`; Overview download after sign-off; CI `test_export.py` |
| I-01 | `Rule.confidence` existed on the object, contradicting D-004 | Removed; CI fails on the field (D-010) |
| I-02 | UI showed "Method: AI" and "Method: Workbook" — two words outside the surface vocabulary | Method is derived server-side from `mapping_method` + Case status; only Rule / Decision / Override / Unresolved |
| I-03 | Lines with a partial rule hit and an open Case showed **Rule** | `mapping_method = null` + `Case.partial_rule_id`; displayed Unresolved with the partial hit as a clue |
| I-04 | Overview breakdown used three invented buckets (mapping / classification / source) that did not match the dataset residue | Four buckets = the four residue types; sums to open Cases (CI) |
| I-05 | Gemini wrote a single "suggestion" with a label into the Case and the UI treated it as the proposal | Rewritten as 2–4 candidates, each with evidence refs validated against the close; ungrounded candidates dropped |
| I-06 | `docs/README.md` linked six files that did not exist | Reconstructed with real content (this file is one of them) |
