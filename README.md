# Close Control Layer

**Ylookup × Encode hackathon · Product track · team 3738**

The product converts fragmented close evidence into traceable financial Lines, applies reusable Rules, routes unresolved items into Cases, and records human decisions with source lineage and tie-out controls.

It is not a new general ledger. It is a record of the 50% that never lands in the mapping file, attached to the source it came from.

> "The only way for me to currently check that is manually by looking at the number, finding it in PDF, and then to verify the transform I need to understand what he was thinking."
> — fund admin persona, live Q&A

## 30 seconds for a reviewer

| Question | Answer |
|---|---|
| Why is this better than Excel? | Excel holds the number, not the PDF string, the map version, or who changed the class. |
| Where does automation stop? | Exact Rule hit only. No map / `Review` / a guess → Case. |
| Why trust the number? | Every Line shows source excerpt, Rule or Decision, reason, and batch tie-out. |

Full logic: [`docs/product-logic.md`](docs/product-logic.md) · dataset → object: [`docs/dataset-mapping.md`](docs/dataset-mapping.md) · why: [`docs/product-thesis.md`](docs/product-thesis.md)

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
2. whether it was produced by a **Rule** (id + version) or a **Decision**
3. if a decision: candidates, chosen treatment, who, one-paragraph reason
4. batch **tie-out** pass/fail

Accept / reject / override-with-reason. An override is stored as another decision on the line.

Surface words only: **Rule / Decision / Override / Unresolved**.

## What this repo contains

```
README.md                      ← you are here
run.sh                         ← one command
app/                           ← reviewer lens
fixtures/sample-close.json     ← public stand-in (not the Discord pack)
docs/product-logic.md          ← map + decision table
docs/canonical-model.md        ← Line / Rule / Case / Source
docs/roles-and-workflow.md     ← who does what
docs/dataset-mapping.md        ← pack artifact → product object
docs/product-thesis.md         ← why it is shaped this way
docs/problem-statement.md      ← scored problem identification
```

Production dataset *bodies* (PDFs, workbooks) are not in this repo. Keep them on the laptop. Contracts and unmatched counts: `docs/data/`.

## Three lenses, one object

| Seat | Job in the product |
|---|---|
| Fund account | First-pass the rule file; file a case when guessing |
| Fund admin | Decide cases; legal overlay; promote precedent |
| Fund manager | Material cases + batch health only; accept residual risk |

The demo surface is the **reviewer** (admin / manager one level up). That is who cannot see the judgment today.

## Do not look for

- A replacement for Investran / eFront / QuickBooks
- Dataset PDFs or xlsx in this repository
- Keystroke telemetry
- Autonomous posting
- Period-cutoff / subsequent-event controls (named in Call-1, out of this object)
