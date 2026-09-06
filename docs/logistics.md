# Logistics

> Reconstructed 2026-09-06. What a judge or teammate needs to run, demo, and hand over the project.

## Event

- Ylookup × Encode hackathon, Product track, team 3738
- Build window: Friday 5 – Sunday 6 September 2026; submission cut-off Sunday 12:00
- Scoring (brief): problem identification · solution · presentation

## Run it

```bash
./run.sh                      # Python 3.9+, stdlib only for the server
```

Serves `data/processed/close.json` if present (the ingested Dataset 01 close), else `fixtures/sample-close.json` (synthetic, canonical shape). Default `http://127.0.0.1:8378`; `PORT=8391 ./run.sh` to change.

Optional candidate drafting: copy `.env.example` to `.env`, set `GOOGLE_API_KEY` (Google AI Studio). Key stays server-side. Without it the UI shows "candidate drafts off" and everything else works.

## Demo path (≈ 3 minutes)

1. **Overview** (fund admin): 100 lines · auto-resolved Rule count · open Cases · tie-out PASS. Source flags still equal README residue (52 / 30 / 4 / 3) on Lines; derived reasons may differ.
2. Click **Flagged "Review" in workbook** → Queue filtered to 3 high-severity Cases.
3. Open one Case: source page + excerpt, Method **Unresolved**, workbook proposal marked *not a fact*, `Why is this a Case?`.
4. (If key set) **Draft candidates** → 2–4 candidates with evidence chips (`SRC-…`, `RULE-…`, `DEC-…`). Pick one.
5. **Accept** → Decision recorded with chosen candidate; or **Override** with a reason.
6. **History** → Case timeline: opened → workbook proposal → candidates drafted → decision → final state. Batch history shows the same Decision one level up.
7. Switch role to **fund manager**: only high-severity Cases; sign-off disabled until zero open Cases and PASS.

Reset between runs: `git checkout data/processed/close.json`.

## Data handling

- Dataset bodies (PDF / xlsx) stay on the laptop under `data/raw/`; CI fails if any is tracked
- `close.json` contains anonymised narratives and amounts from the pack, per the dataset README's terms; no reversal keys anywhere
- `.env` is git-ignored; `.env.example` is the template

## Hand-over

| Item | Where |
|---|---|
| Entry point | `README.md` → `docs/README.md` |
| Contract | `docs/canonical-model.md` §As implemented · `scripts/canonical_model.py` |
| Decisions | `docs/decisions/DECISION-LOG.md` (D-001 … D-010) |
| Known gaps | `docs/issues/ISSUES.md` |
| Checks | `python3 scripts/ci_check.py` |
