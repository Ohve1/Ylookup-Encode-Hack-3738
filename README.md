# Close Control Layer

**Ylookup × Encode hackathon · Product track · team 3738**

A fund-close workflow and control layer that turns fragmented source files into traceable financial lines, surfaces mapping exceptions, and records the decisions behind validated outputs.

It sits between source artifacts and the system of record; it does not replace the accounting platform.

> "The only way for me to currently check that is manually by looking at the number, finding it in PDF, and then to verify the transform I need to understand what he was thinking."
> — fund admin persona, live Q&A

## 30 seconds for a reviewer

| Question | Answer |
|---|---|
| What is this? | A control layer for close mapping decisions — not bank automation, not a new GL. |
| Why better than Excel? | Excel holds the number, not the PDF string, the map version, or who changed the class. |
| Where does the product stop? | At a **validated mapping export** (`validated_mapping_csv_v1`). No SoR API write-back. |
| Where does automation stop? | Exact Rule hit only. No map / `Review` / a guess → Case. |
| Why trust the number? | Every Line shows source excerpt, Rule or Decision, reason, and batch tie-out. |

Full logic: [`docs/product-logic.md`](docs/product-logic.md) · dataset → object: [`docs/dataset-mapping.md`](docs/dataset-mapping.md) · why: [`docs/product-thesis.md`](docs/product-thesis.md)

## Same core workflow (two validation cases)

```
Any Source → Canonical Line → Mapping → Mapping Gap → Case → Human Decision → Validated Export
```

| Pack | Path | What it proves |
|---|---|---|
| Dataset 01 | Bank → Journal | Source → Line → Case → Decision works on statements (100 lines, 90 Cases) |
| Dataset 02 | GL → Loader | The same abstraction generalises; not a second product feature (1,204 lines, 103 Cases, README residue 4 / 16 / 198 preserved as tie-outs) |

Constraint: they will not switch the system of record.  
Non-goal: replacing the administrator, autonomous posting, or SoR API integration.

## Must Have / Must Not Have

| Must Have | Must Not Have |
|---|---|
| Source → Line → Rule / Exception → Case → Review → Decision → Tie-out → **Validated Export** | SoR API write-back (Investran / eFront / QuickBooks clients) |
| Every Line shows source excerpt + Rule or Decision + reason | Autonomous posting or unattended close |
| Exact Rule hit only; otherwise Case | Soft confidence / “maybe” mappings |
| Batch tie-out gate before export | Claiming unverified system-specific loaders as shipped |
| Downloadable `validated_mapping_<close_id>.csv` after sign-off | Finance chatbot, portfolio / investor dashboards, generic analytics |
| Dataset 01 + Dataset 02 as **one** workflow, two validation cases | Two separate product features (Bank→JE vs GL→Loader) |

**Export contract (v1):** profile `validated_mapping_csv_v1` — UTF-8 CSV, one row per canonical Line, after batch sign-off. Not an Investran/eFront loader schema until that schema is verified.

## Quick start (one command)

```bash
./run.sh
```

Run this from the repository root.  
It serves the ingested Dataset 01 close (`data/processed/close.json`: 100 lines, 10 Rule, 90 Unresolved, tie-out PASS) or, if that file is absent, the synthetic fixture. Python 3 only; no API key needed.

Then open the URL printed in the terminal (default http://127.0.0.1:8378).

Same lens, second validation case: `PACK=02 ./run.sh` serves the Dataset 02 close (`data/processed/close-dataset02.json`: 33,902 GL rows → 1,204 movement-group lines, 1,101 Rule, 103 Unresolved, tie-out PASS). Any canonical close: `CLOSE_FILE=path ./run.sh`.

### End-to-end on the real packs (scripted pilot)

```bash
python3 scripts/run_pilot.py --close data/processed/close.json --close data/processed/close-dataset02.json --force
```

Works on a **copy** under `data/processed/pilot/<close_id>/` — decides every open Case with a reason (Dataset 01: the treatment the accountant filed; Dataset 02: the Mapping Gaps proposal / batch override / crosswalk result), signs off, emits `validated_mapping_<close_id>.csv`, and writes `pilot-metrics.json`. The demo state in `close.json` is untouched. Open a finished run with `CLOSE_FILE=data/processed/pilot/CLOSE-2026-03-CALDER-WEEK/close.json ./run.sh` and the download button is live.

Pilot metrics (roadmap VALIDATE) are also served live at `GET /api/metrics`: exception rate, override rate, review rounds, hours per close, decisions by role, Rule health (override rate per Rule → potentially stale). Anything the record cannot support is `null` with a reason; a scripted run is labelled `scripted_replay` and its timings are not evidence of human cycle time.

Re-ingest from the packs (laptop only): `python3 scripts/ingest_dataset.py` (Dataset 01), `python3 scripts/ingest_dataset02.py` (Dataset 02). Checks: `python3 scripts/ci_check.py`.

Optional: set `GOOGLE_API_KEY` in `.env` (see `.env.example`) to enable **Draft candidates** on a Case. Candidates are grounded on the source excerpt, matching rules and prior decisions, cite their evidence, and are never a Method — only Accept / Override records anything.

For any line you can see, without leaving the screen:

1. source excerpt (statement narrative / page)
2. whether it was produced by a **Rule** (id + version) or a **Decision**
3. if a decision: candidates, chosen treatment, who, one-paragraph reason
4. batch **tie-out** pass/fail

Accept / reject / override-with-reason. An override is stored as another decision on the line.

Surface words only: **Rule / Decision / Override / Unresolved**.

## What this repo contains

```
README.md                      ← you are here
run.sh                         ← one command (PACK=02 for Dataset 02)
app/                           ← reviewer lens (+ GET /api/metrics)
scripts/ingest_dataset.py      ← Dataset 01 → canonical close
scripts/ingest_dataset02.py    ← Dataset 02 → the same canonical close
scripts/run_pilot.py           ← decide → sign off → export → measure, on a copy
scripts/pilot_metrics.py       ← VALIDATE instrumentation from the record
fixtures/sample-close.json     ← public stand-in (not the Discord pack)
docs/product-logic.md          ← fund-close map + export boundary
docs/canonical-model.md        ← Line / Rule / Case / Decision / Source / Export
docs/roles-and-workflow.md     ← Accountant resolve · Admin coordinate · Manager approve
docs/dataset-mapping.md        ← two packs, one workflow
docs/product-thesis.md         ← positioning + trust metrics
docs/roadmap.md                ← NOW / NEXT / VALIDATE / LATER
docs/problem-statement.md      ← scored problem identification
```

Production dataset *bodies* (PDFs, workbooks) are not in this repo. Keep them on the laptop. Contracts and unmatched counts: `docs/data/`.

## Three lenses, one object

| Seat | Verb | Job in the product |
|---|---|---|
| Accountant | Prepare | My Cases — lineage + prepare; cannot Decide |
| Fund admin | Decide | Close Overview — blockers, Decide Cases, export |
| Fund manager | Approve | Review — material exceptions only |

Every page traces the same chain: Line → Source → Rule / Mapping → Case → Decision → Export.

## Do not look for

- A replacement for Investran / eFront / QuickBooks
- SoR API write-back (boundary = validated export)
- Dataset PDFs or xlsx in this repository
- Keystroke telemetry / autonomous posting / finance chatbot
- Two separate products (Bank→JE vs GL→Loader) — same workflow, two validation cases
- Period-cutoff / subsequent-event controls (named in Call-1, out of this object)
