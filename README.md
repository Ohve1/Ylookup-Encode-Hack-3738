# Close Control Layer

**Ylookup × Encode hackathon · Product track · team 3738**

The product is not a new general ledger. It is a record of the 50% that never lands in the mapping file, attached to the source it came from.

> "The only way for me to currently check that is manually by looking at the number, finding it in PDF, and then to verify the transform I need to understand what he was thinking."
> — fund admin persona, live Q&A

## The one object

Unrecorded classification and mapping-gap decisions — on bank-statement-to-journal-entry and GL-to-loader — with no source lineage for the reviewer one level up.

Constraint: they will not switch the system of record.  
Non-goal this weekend: replacing the administrator.

## Run

```bash
./run.sh
```

Opens a reviewer lens on a fixture close (Dataset 01 shape). No API key. Python 3 only.

Then open the URL printed in the terminal (default http://127.0.0.1:8378).

For any line you can see, without leaving the screen:

1. source excerpt (statement narrative / page)
2. whether it was produced by a **rule** (id + version) or a **decision**
3. if a decision: candidates, chosen treatment, who, one-paragraph reason
4. batch **tie-out** pass/fail

Accept / reject / override-with-reason. An override is stored as another decision on the line.

## What this repo contains

```
README.md                 ← you are here
run.sh                    ← one command
app/                      ← reviewer lens
fixtures/                 ← anonymised-shape fixture (not production files)
docs/problem-statement.md ← scored problem identification
docs/                     ← decisions, risk register, roadmap, harness
```

Production dataset *bodies* (PDFs, 34k-row GL) are not in this repo. Dataset contracts and unmatched counts are in `docs/data/`. Do not treat unmatched rows as bugs — they are the work.

## Three lenses, one object

| Seat | Job in the product |
|---|---|
| Fund account | First-pass the rule file; file a case when guessing |
| Fund admin | Decide cases; legal overlay; promote precedent |
| Fund manager | Material cases + batch health only; accept residual risk |

The demo surface is the **reviewer** (admin / manager one level up). That is who cannot see the judgment today.

## Do not look for

- A replacement for Investran / eFront / QuickBooks
- Keystroke telemetry
- Autonomous posting
- Period-cutoff / subsequent-event controls (named in Call-1, out of this object)

Full problem statement, evidence tags, and harness: [`docs/problem-statement.md`](docs/problem-statement.md).
