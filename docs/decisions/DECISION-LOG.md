# Decision log

> Reconstructed 2026-09-06 from `problem-statement.md`, `product-thesis.md`, `product-logic.md` and the code. The working log was not committed; entries below are the decisions those documents cite (D-003, D-005, D-008 by name) plus the ones the code enforces. Status is as of submission.

Format: what we decided · why · what it rules out · where it is enforced.

| ID | Decision | Status |
|---|---|---|
| D-001 | The object is the *unrecorded* classification / mapping-gap decision, not the journal entry | firm |
| D-002 | Sit between source documents and the system of record; never replace the SoR | firm (constraint from admin persona) |
| D-003 | Propose, do not post. A human records every mapping that is not an exact Rule hit | firm |
| D-004 | Exact Rule hit or Case. No confidence score, no soft rule | firm · enforced |
| D-005 | Deployment model and ownership of the rule file | open |
| D-006 | Source excerpt is required on every Line; a Line without one cannot be resolved | firm · enforced |
| D-007 | Override requires a one-paragraph reason and is stored as a Decision on the same Case | firm · enforced |
| D-008 | Autonomy only on classes the admin has explicitly blessed; a precedent becomes a Rule only with dual sign-off | firm (blessing flow not built) |
| D-009 | Demo surface is the reviewer one level up (admin / manager), not the accountant's first pass | firm |
| D-010 | *Unresolved* is a Case state, not a mapping method. LLM output is a list of grounded **candidates**, never a Method | firm · enforced |
| D-011 | Strict provenance: raw bank facts only enter rule evaluation; filed snapshot is comparison-only; older closes are incompatible | firm · enforced |
| D-012 | Decisions are append-only (`decisions.jsonl`); Override requires explicit `supersedes`; event count alone never implies Override | firm · enforced |
| D-013 | Product boundary = validated, system-specific export; Dataset 01/02 are validation cases of one workflow, not two features | firm |

---

## D-001 — The object

**Decided.** The product records the judgment that fills the residue a map does not cover, attached to the source it came from. Not a new GL, not a bank-feed classifier.

**Why.** E7: "50% human experience, 50% mapping"; the admin re-derives the number from the PDF and the formula because the judgment is not written down.

**Rules out.** Any pitch centred on extraction accuracy or on replacing Investran / eFront / QuickBooks.

## D-002 — Position relative to the system of record

**Decided.** The close object lives between source files and the accounting system. Output is a **validated, system-specific export** the reviewer accepts before the operator loads it into the SoR. Not an API write-back.

**Why.** Admin persona: "I'm not going to switch software. What I do need is the ability to verify the data that I'm sticking into that software."

## D-003 — Propose, do not post

**Decided.** The system may propose; a human decides and loads the validated export. `problem-statement.md` §Non-goal cites this as D3.

**Enforced.** `record_decision` is the only write path that changes `Line.mapping`; `/api/suggest` writes `Case.suggestion` only. No SoR client in the product boundary (D-013).

## D-004 — Exact Rule or Case

**Decided.** A Rule either matches or it does not. There is no confidence field on the object or the UI. A guess is a Case.

**Why.** A confidence number is exactly the "soft maybe" the reviewer cannot audit. It also invites the accountant to set a threshold instead of deciding.

**Enforced.** `Rule` dataclass has no `confidence`; `scripts/ci_check.py` fails if one appears in `close.json` or the fixture. A rule that matches the classification but leaves residue (52 counterparty misses on Dataset 01) is a Case with `partial_rule_id`, displayed **Unresolved**.

## D-005 — Deployment and rule-file ownership

**Open.** Who owns the versioned rule file — the administrator (per fund) or the manager — decides where the product deploys and who can bless a class (D-008). Not needed for the weekend demo; named in `problem-statement.md` as out of scope.

## D-006 — Source excerpt required

**Decided.** Every Line carries `bank_ref.excerpt` / `source_ref` and the reviewer can open it on the Case. Resolution is blocked if the string cannot be shown.

**Enforced.** `validate()` requires `source_ref.source_id`; `ci_check` requires a non-empty excerpt on every adapted line. Dataset 01: 100 / 100 lines located exactly on the statement page.

## D-007 — Override is a Decision with a reason

**Decided.** Override stores `previous_value`, `final_value`, `reason`, `decided_by`, `role`, `timestamp` on the same Case. Reject also needs a reason and keeps the Case Unresolved.

**Enforced.** UI refuses an empty reason; `record_decision` records the Decision and sets `mapping_method = override`.

## D-008 — Autonomy only on blessed classes

**Decided.** A decided Case is a comparable, not a Rule, until dual sign-off, repetition, and no policy clash. `problem-statement.md` cites this as D8.

**Not built.** Promotion flow is roadmap **NEXT** (compound the system). Precedents are, however, already fed to candidate drafting as evidence refs (`DEC-xxx`).

## D-009 — Reviewer lens first

**Decided.** The demo surface is the admin / manager one level up. That is the person who today cannot see the judgment and re-does the work.

**Consequence.** Three role views over one object (`roles-and-workflow.md`); the accountant view is a table, not a workflow.

## D-010 — Unresolved is a state; LLM output is candidates

**Decided 2026-09-06**, after review found the surface saying "Method: AI" and "Method: Workbook" and the object carrying `Rule.confidence`.

1. `Line.mapping_method ∈ {rule, decision, override, null}`. *Unresolved* is derived from an open Case, never stored as a method.
2. The optional Gemini step drafts 2–4 **candidates**, each citing refs that exist in the close (source page, rule, precedent decision). Ungrounded candidates are dropped server-side. Accepting a candidate is a Decision with `chosen`; the model is named in `drafted_by` / `model`, not in Method.
3. Surface vocabulary is exactly Rule / Decision / Override / Unresolved. `ci_check` greps the UI and fixture for the forbidden phrases.

**Why.** The thesis says "no soft maybe" and "keep humans responsible for judgement". A fifth method word — AI or Workbook — would have been a silent fact. This also fixes the scoring risk that reviewers see the docs and the demo disagree.

## D-011 — Strict provenance inputs

**Decided 2026-09-06.** Rule evaluation may read only raw bank facts, independently verified spans, and versioned reference tables. Filed counterparty, project, position and classification are stored as `filed_snapshot` for comparison and must not enter `evaluate_rules`.

**Why.** Using filed fields to reproduce filed classification is circular and cannot honestly label a line `Rule`.

**Rules out.** Soft confidence levels; “project exists → Investment”; tautological classification rules as Method.

**Enforced.** `scripts/normalize.py` evaluation path; `validate()` requires `raw_facts` and `filed_snapshot` on Dataset 01 lines; CI fails on `confidence`.

## D-012 — Append-only decisions with explicit supersedes

**Decided 2026-09-06.** Every Accept / Reject / Override / sign-off is appended to `data/processed/decisions.jsonl` as well as the close object. Override requires `supersedes` pointing at the prior Decision. Reject keeps the Case Unresolved and is never inferred as Override from event count.

**Why.** `len(decisions) > 1` falsely treats Reject→Accept as Override.

**Enforced.** `record_decision` / `append_decision_journal` / `derive_line_origin`.

## D-013 — Validated export boundary; one workflow, two packs

**Decided 2026-09-06** (feedback alignment). Product positioning is a fund-close workflow / mapping-decision control layer. Dataset 01 (Bank→Journal) and Dataset 02 (GL→Loader) are validation cases of the same Source → Line → Mapping → Case → Decision → Export chain — not Feature 1 / Feature 2.

**Boundary.** The product stops at a validated, system-specific export file (e.g. `validated_investran_loader.csv`). SoR API write-back is out of scope.

**Rules out.** Pitch as bank automation; Investran API as the architecture end-state; second product pipeline for Dataset 02; auto-promoting a single Decision to a Rule without dual control.

**Where.** `product-thesis.md`, `product-logic.md`, `dataset-mapping.md`, `roadmap.md` (NOW / NEXT / VALIDATE / LATER).
