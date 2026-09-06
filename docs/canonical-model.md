# Canonical model

Contract for one shared close object. Excel is a view, not the book of record.

On any reviewer surface a Line is in exactly one origin:

**Rule | Decision | Override | Unresolved**

## Line

One journal / loader row.

```
Line
+-- id
+-- batch_id
+-- fund / entity
+-- date
+-- description
+-- amount / currency
+-- source          -> Source
+-- origin          -> Rule | Decision | Override | Unresolved
+-- rule_id + rule_version     (if Rule)
+-- case_id                    (if Decision, Override, or Unresolved)
+-- status          -> drafted | accepted | rejected | overridden
```

## Rule

Versioned map entry. Fund account authors it. Cold start = workbook sheets that already exist.

```
Rule
+-- id
+-- version
+-- condition       -> vendor code / narrative / account / jurisdiction …
+-- proposed_account / treatment
+-- origin          -> workbook sheet + row (Vendor Codes, Account Map, …)
+-- owner           -> fund account
```

No “confidence” field on the object or the UI. Either the condition matches or it does not. A guess is a Case, not a soft Rule.

## Case

Opened when there is no exact Rule, or the operator would guess.

```
Case
+-- id
+-- line_id
+-- type            -> counterparty_miss | project_miss | position_miss
|                      | mapping_gap | review_flag | classification | legal_figure
+-- reason
+-- status          -> Unresolved | decided
+-- author          -> fund account
+-- owner / decider -> fund admin (manager if material)
+-- candidates[]    -> proposed treatments (P&L delta when known)
+-- chosen
+-- policy_ref      -> LPA / side letter / firm policy
+-- precedent_ids[]
+-- decision        -> Decision | Override
+-- audit_history   -> who, when, reason (no keystroke telemetry)
```

## Source

```
Source
+-- file            -> PDF name or workbook name
+-- page / sheet
+-- row
+-- extracted_text  -> string that exists in that file
```

Resolution is blocked if `extracted_text` cannot be shown.

## Batch

```
Batch
+-- id
+-- counts          -> rule / decision / unresolved
+-- tie_out         -> pass | fail  (debits vs credits / movements rec)
```

Fail => the slice does not advance.

## Precedent

A decided Case becomes a standing Rule only with dual sign-off, repetition, and no policy clash. Until then it is a comparable, not an unattended Rule.
