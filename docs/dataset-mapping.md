# Dataset -> product mapping

The Discord pack is **evidence of one close**. It is not the product. Dataset bodies (PDFs, workbooks) stay on the operator laptop and are not in this repository.

The public repo ships a synthetic fixture with the same *shape* so a reviewer can run `./run.sh` without the pack.

## Artifact -> object

| Dataset artifact | Product object | Product behavior |
|---|---|---|
| Bank PDF | Source | Evidence. Line must quote a string that exists in the file. |
| Excel staging / transaction row | Line | The financial work item. |
| Vendor Codes / Account Map / Allocation Rule / CoA | Rule | Reusable treatment. Exact hit only. |
| Blank / unmatched counterparty (52) | Case | Unresolved exception. Do not delete. |
| Project miss (30) / position miss (4) | Case | Same. |
| `Review` row (3) | Case | Explicit human review. |
| Journal / DIU output | Line (accepted shape) | What posting looks like. Not a new GL. |
| Journal / movements totals | Batch tie-out | Control. Fail blocks the slice. |
| Reviewer accept / override | Decision / Override | Audit trail. |
| Dataset 02 Mapping Gaps | Case (same type) | Shown on one screen. No second pipeline this weekend. |

## Flow

```
Dataset 01
Bank PDF -> journal workbook
        |
        v
Canonical model   (this repo)
        |
        v
Lines / Rules / Cases
        |
        v
Reviewer lens     (./run.sh)
        |
        v
Ready for posting into the existing SoR
```

```
Dataset 02
Investor GL -> loader + Mapping Gaps
        |
        v
Same Case type
        |
        v
One extra view — not a second product
```

## Local vs public

| On your computer | On GitHub |
|---|---|
| Discord zip (`statements/`, `workbook/`) | Never |
| `fixtures/local-*.json` generated from the zip | gitignored |
| `fixtures/sample-close.json` | Public stand-in |
| `docs/data/*.md` contracts + unmatched **counts** | Public |

Unmatched rows are the work. Cleaning them so the demo looks tidy is a product defect.
