# Ylookup hackathon — anonymised datasets

Three sets of material, all derived from real client work and all anonymised. Production file bodies are not in this public repo. These READMEs are the contracts the product is built against.

## One command to execute

From repo root:

```bash
./run.sh
```

Use this to launch the reviewer app that consumes these dataset contracts. `PACK=02 ./run.sh` opens the Dataset 02 close; both packs are ingested by `scripts/ingest_dataset.py` and `scripts/ingest_dataset02.py` into the same canonical model.

| Folder | What it is | Shape of the task |
|---|---|---|
| `01-bank-statements-to-journal-entries` | Seven bank statements plus a working file | Read a PDF statement, work out who each payment was to or from, classify it, and produce the journal entries |
| `02-investor-level-gl-to-loader` | A quarter of investor-level GL, a loader sample, and the finished loader | Map a general ledger from one fund accounting system into another system's upload format |
| `03-call-transcripts` | Four anonymised call transcripts | Context on the problems these workflows exist to solve |

## How the anonymisation works

Replacement is token-level and consistent. Amounts, dates, balances and quantities are untouched and still tie. Identifiers were regenerated in the same shape.

## Two things to know

**The imperfections are deliberate.** Unmatched rows, `Review` flags, and lookups that do not resolve were preserved exactly. They are the difficulty of the exercise, not defects to clean up.

**Do not distribute the reversal keys.** They must never travel with the datasets or this repo.
