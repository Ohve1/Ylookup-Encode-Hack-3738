# Dataset → product mapping

The Discord pack is **evidence of one close**. It is not the product. Dataset bodies (PDFs, workbooks) stay on the operator laptop and are not in this repository.

The public repo ships a synthetic fixture with the same *shape* so a reviewer can run `./run.sh` without the pack.

## Same core workflow — two validation cases

Do **not** pitch:

| Wrong framing | |
|---|---|
| Feature 1 | Bank → Journal |
| Feature 2 | GL → Loader |

Do pitch:

```
                    SAME CORE WORKFLOW
Any Source
   ↓
Canonical Line
   ↓
Mapping
   ↓
Mapping Gap
   ↓
Case
   ↓
Human Decision
   ↓
Validated Output
```

| Pack | Path | Role |
|---|---|---|
| **Dataset 01** | Bank → Journal | Validation case: proves source → Line → Case → Decision on statements |
| **Dataset 02** | GL → Loader | Validation case: proves the same source → target abstraction generalises |

They are not two product features. They are two packs exercising one control layer.

## Artifact → object

| Dataset artifact | Product object | Product behavior |
|---|---|---|
| Bank PDF / GL extract | Source | Evidence. Line must quote a string that exists in the file. |
| Excel staging / transaction / GL row | Line | The financial work item. |
| Vendor Codes / Account Map / Allocation Rule / CoA | Rule | Reusable treatment. Exact hit only. |
| Blank / unmatched counterparty (52) | Case | Unresolved exception. Do not delete. |
| Project miss (30) / position miss (4) | Case | Same. |
| `Review` row (3) | Case | Explicit human review. |
| Dataset 02 GL movement group (LE × GL account × trans type) | Line | 33,902 GL rows → 1,204 Lines; every Line quotes its GL rows (first / last / sample) and Dr / Cr totals. |
| Dataset 02 CoA / LE / Deal Mapping rows | Rule (`v4c`) | Crosswalk row = reusable treatment. Exact hit only. 1,101 of 1,204 Lines. |
| Dataset 02 Mapping Gaps / unmapped entity / unmapped deal / loader disagreement | Case (same type) | 103 Cases: `no_matching_rule` 66 · `entity_miss` 30 · `rule_mismatch` 10 · `deal_miss` 8. Source = GL rows. |
| Dataset 02 README residue (4 entities / 16 deals / 198 investors) | TieOut `readme_residue` | Ingest fails if the counts move. Not deleted, not cleaned. |
| Journal / DIU / loader shape | Export target (LATER profiles) | Dataset 01 ships `validated_mapping_csv_v1` first — not a claimed Investran schema. |
| Journal / movements totals | Batch tie-out | Control. Fail blocks export. |
| Reviewer accept / override | Decision / Override | Audit trail. |
| Dual-control promote | Rule (new version) | NEXT — precedent library. |
| Batch sign-off + download | Export | `validated_mapping_<close_id>.csv` after gate. |

## Flow

```
Dataset 01                         Dataset 02
Bank PDF → journal workbook        Investor GL → loader + Mapping Gaps
        |                                    |
        +----------------+-------------------+
                         v
                  Canonical model   (this repo)
                         |
                         v
              Lines / Rules / Cases / Decisions
                         |
                         v
                  Reviewer lenses     (./run.sh)
                         |
                         v
         Sign-off → GET /api/export
         validated_mapping_<close_id>.csv
                         |
                         v
              Existing accounting system (operator load)
```

First shipped profile is **`validated_mapping_csv_v1`** (one row per Line). DIU dual-leg / Investran / eFront loader profiles stay LATER until schemas are verified.

## Local vs public

| On your computer | On GitHub |
|---|---|
| Discord zip (`statements/`, `workbook/`, `02-investor-level-gl-to-loader/`) | Never |
| `data/raw/dataset01`, `data/raw/dataset02` (symlinks to the packs) | gitignored |
| `fixtures/sample-close.json` | Public stand-in |
| `docs/data/*.md` contracts + unmatched **counts** | Public |

Unmatched rows are the work. Cleaning them so the demo looks tidy is a product defect.
