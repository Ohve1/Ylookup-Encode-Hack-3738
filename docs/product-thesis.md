# Product thesis

## Positioning

A fund-close workflow and control layer that turns fragmented source files into traceable financial lines, surfaces mapping exceptions, and records the decisions behind validated outputs.

It sits between source artifacts and the system of record; it does not replace the accounting platform.

## 1. Problem

Fund close currently spans PDFs, Excel mappings, staging journals, and accounting systems.

The main problem is not data entry. It is the unmanaged space between:

**source evidence → mapping → exception → decision → validated output.**

That space is exercised by named people, not recorded, and detected late. The reviewer one level up re-does the work to reconstruct what the person below was thinking.

## 2. Existing workflow

Receive PDFs by email → extract to Excel → classify with platform maps plus judgment → reshape for downstream software → check balances by hand → send the workbook up a chain (accountant → admin → manager).

## 3. Failure points

- Maps never cover the residue (unmatched counterparties, project/position misses, `Review`, Mapping Gaps).
- The judgment that fills the residue does not travel with the number.
- Manager shadow-checks the pack because the formal chain has no lineage.
- Spreadsheets cannot be the control environment LPs and regulators will accept, but replacing the partnership with a new GL kills the judgment that justified staying private.

## 4. Design principles

1. Preserve source evidence.
2. Make every financial item traceable.
3. Automate repeatable mappings.
4. Surface exceptions rather than hiding them.
5. Keep humans responsible for judgement.
6. Never allow unresolved differences to disappear.
7. Stop at a **validated, system-specific export** — do not write back to the SoR.
8. Promote precedent only under dual control; watch rules for staleness when they are frequently overridden.

## 5. Product abstraction

A **shared close workflow object** between source files and the existing system of record.

Not bank-statement automation. Not a new GL. Not an administrator replacement. Not an API integration into Investran / eFront.

The product records, validates, and reuses mapping decisions made during close. Output is a validated export the operator loads into the system they already use.

## 6. Canonical model (work objects)

Line · Rule · Case · Decision · Source · Export — plus batch tie-out.

These are close-workflow work objects, not “just database tables.” See `canonical-model.md`.

## 7. Decision logic

Exact Rule or Case. No soft “maybe.” See `product-logic.md`.

Approved Decision may become a Rule only after dual-control promotion. High override rate marks a Rule potentially stale.

## 8. Role model

| Seat | Verb | Question |
|---|---|---|
| Accountant | Prepare | What needs preparation? (cannot Decide) |
| Admin | Decide | What's blocking the close? |
| Manager | Approve | What decisions require my judgement? |

Three seats operate the same underlying chain: Line → Source → Rule/Mapping → Case → Decision → Export. See `roles-and-workflow.md`.

## 9. Trust / control

Trust is measured, not shipped:

- hours per close
- review rounds to signed NAV
- exception rate
- override rate on stable patterns (not a person score)
- error rate after export / load

Control on the object: source excerpt required; override requires a reason; tie-out fail blocks the slice; export only after validation; Rule health surfaces stale precedent.

## 10. Scope

**Validation cases (same workflow, not two features):**

- Dataset 01 — Bank → Journal (proves source → canonical Line → Case → Decision → Export)
- Dataset 02 — GL → Loader (proves the same abstraction generalises)

**Product boundary:** validated export file after tie-out + sign-off — not SoR API write-back.

**Export contract (v1):** profile `validated_mapping_csv_v1` → `validated_mapping_<close_id>.csv`. One row per canonical Line with final mapping and provenance. System-specific loader profiles (Investran / eFront / DIU dual-leg) are LATER, only after a verified schema exists.

## 11. Must Have / Must Not Have

Review and cut features against this table.

| Must Have | Must Not Have |
|---|---|
| Source → Line → Rule / Exception → Case → Review → Decision → Tie-out → Validated Export | SoR API write-back |
| Source excerpt + Rule or Decision + reason on every Line | Autonomous / unattended posting |
| Exact Rule or Case (no soft maybe) | Confidence scores as Method |
| Tie-out fail blocks export | Unverified “Investran loader” claims |
| Sign-off then downloadable validated mapping CSV | Finance chatbot, portfolio / investor dashboards |
| One workflow; Dataset 01 / 02 as validation cases | Second product pipeline for Dataset 02 |
| Dual-control before Decision → Rule (NEXT) | Auto-promote a single accountant Decision to Rule |

**Out this weekend / NOW:** period-cutoff engine, keystroke telemetry, claiming LP/auditor acceptance before pilot metrics exist.
