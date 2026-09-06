# Product thesis

## 1. Problem

Fund close currently spans PDFs, Excel mappings, staging journals, and accounting systems.

The main problem is not data entry. It is the unmanaged space between:

**source evidence → mapping → exception → decision.**

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

## 5. Product abstraction

A **shared close object** between source files and the existing system of record.

Not a new GL. Not an administrator replacement. Propose, do not post, unless a class is explicitly blessed.

## 6. Canonical model

Line + Rule + Case + Source + Batch tie-out. See `canonical-model.md`.

## 7. Decision logic

Exact Rule or Case. No soft “maybe”. See `product-logic.md`.

## 8. Role model

Accountant makes and files. Admin decides and overlays legal. Manager sees material residue only. See `roles-and-workflow.md`.

## 9. Trust / control

Trust is measured, not shipped: review rounds to signed NAV; whether manager shadow re-verification stops; override rate on *stable* patterns (not a person score).

Control on the object: source excerpt required; override requires a reason; tie-out fail blocks the slice.

## 10. Scope

**In this weekend:** Dataset 01 bank-to-JE as Lines/Cases; Dataset 02 Mapping Gaps as the same Case type; reviewer lens; tie-out badge.

**Out:** new SoR, period-cutoff engine, keystroke telemetry, unattended posting, publishing dataset bodies, claiming LP/auditor acceptance.
