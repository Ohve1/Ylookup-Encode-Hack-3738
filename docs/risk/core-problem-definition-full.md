# Core Problem Definition — Risk Management Scope

**Status:** Draft v1 for review
**Date:** 2026-09-05
**Scope:** Risk management only. Product, commercial and incentive design are referenced only where they create or mitigate risk.
**Evidence base:** Section 7 lists every source used. No factor in this document is introduced without a citation to that section.

---

## 1. Purpose

Define the core risk problem in private-market fund operations (bank statement → journal entry; GL → loader; NAV close) using only evidence already reviewed, so that later design decisions can be traced back to a stated fact, a stated assumption, or a named uncertainty.

## 2. Problem statement (one paragraph)

The residual risk of a private-market close is concentrated in a thin layer of human judgment — counterparty resolution, classification, mapping gaps, policy and period-cutoff calls — that is exercised but not recorded, owned by named people but not by the process, and detected late (at pack review or restatement) rather than at the point the judgment is made. The only detective control currently operating over that layer is the fund manager's own out-of-process re-verification, which is unowned, unaudited, dependent on one person, and evidence that the formal control chain has already failed. **The core problem is the absence of a control that captures, tests and records judgment-based decisions at the moment they occur, with lineage to source, so that residual risk becomes measurable, transferable and defensible.**

## 3. Established facts

Facts are statements directly supported by the evidence in Section 7. Each carries its source tag.

### 3.1 Workflow and roles [E1]
- F1. Three roles operate the close: fund manager (owns the signed number and the risk), fund admin (reviews fund account output, applies more legal factors, works closer to the manager), fund account (third party whose function is precision of output; classifies using experience, mappings and a sample/golden dataset).
- F2. Current process is manual end to end: PDFs received by email → Excel extraction → classification (platform mappings + accountant judgment) → transform to accounting-software format → manual verification of balances, classifications, formulas, source figures → manager review.
- F3. The manager's stated pain is trust: how much error risk to tolerate.

### 3.2 Bank statements dataset [E2]
- F4. One week (six business days), seven accounts, four currencies, 100 staging rows, 15-sheet workbook.
- F5. Of 100 rows: 52 have no counterparty match; 30 project codes do not resolve to the project code report; 4 resolved positions do not resolve to the deal/position master; 3 rows are flagged `Review`.
- F6. These unmatched counts existed in the original production file and were preserved exactly. They are the work, not data defects.
- F7. Every counterparty string in the staging sheet is literally present in the source PDF, in the bank's truncated, capitalised, line-wrapped form. Bridging that to the clean master-list name is described as "most of the work".
- F8. Six stages with review points per stage are documented in the `Process` sheet; the workbook already contains explicit reference artifacts (`Vendor Codes`, `Account Map`, `Allocation Rule`, `CoA`, master lists).

### 3.3 GL-to-loader dataset [E3]
- F9. ~34,000 source GL rows, 43 columns; ~19,000 upload-template rows; 14-sheet output workbook including four crosswalk mappings, a `Mapping Gaps` sheet and a `Movements Rec` sheet.
- F10. Of the output: 4 legal entities not in the entity listing; 16 deal names not in the deals list; 198 investor names in the mapping not in the investors list.
- F11. The `Mapping Gaps` sheet is populated by design: those gaps went back to the administrator for a human decision.
- F12. Amounts, dates and quantities tie to source; cross-file joins resolve. A batch-type override rule exists for batches containing several transaction types.
- F13. A pre-upload reconciliation of movements per entity per account is a documented step.

### 3.4 Call evidence [E4]
- F14. A fund manager reports that a NAV takes six or seven rounds with the administrator.
- F15. Named defect types: subsequent events left in with dates rolled forward; side-letter fee calculations wrong; no one checking that numbers foot.
- F16. That manager now runs the administrator's output through an AI tool before reading it.
- F17. A report-extraction job takes an offshore team two months a year; a prospect is consolidating across fifteen administrators; the vendor's stated approach is replacing outsourced providers service by service.
- F18. Transcripts are partial (roughly the first third to half of each call). Call 4 is internal commercial strategy, not workflow evidence.

### 3.5 Design decisions already taken in this work [E5]
These are established as *decisions*, not as empirical facts about the market.
- D1. Judgment is structured as a case object (exception + source docs + candidate treatments + firm policy/LPA + published precedent + named decision, reviewer, reason).
- D2. Lineage attaches to the case/output object, not to the person; no keystroke or hesitation telemetry.
- D3. Default is propose-not-decide; autonomy only on classes explicitly blessed by the admin firm.
- D4. Precedent is admin-owned; promotion to standing instruction requires dual sign-off, repetition, and no contradiction of policy.
- D5. Fund account authors and edits the versioned first-pass rule file and files a short case whenever guessing.
- D6. Admin override rate is not a performance score; it is the learning signal. Fund account is measured on first-pass accept rate on rule-covered items, exception-file completeness on material items, breaks introduced, and time to clear the first-pass queue.
- D7. Transparency is a *location* decision, not a dial: maximal on objects, minimal on people; and materiality-tiered for the manager.
- D8. Build sequence: automate the solved set with lineage built in from day one; trust is measured (review rounds; whether shadow re-verification stops), not built; risk artifacts are packaged for LPs/auditors last.

## 4. Assumptions

Statements the work currently relies on that are not directly evidenced. Each is tagged with the fact it extends and what would falsify it.

- A1. **The premise for this document: the fund manager takes direct accountability for the fee.** Stated as an instruction in this work, not observed in the evidence. Consequence relied on: manager tolerance for defects falls and demand for defensibility rises. Falsified if fee accountability stays with the administrator relationship.
- A2. **Unmatched rows are predominantly judgment work, not extraction/matching failure.** Extends F5–F7. F7 shows the strings are recoverable from the PDFs, so an unknown share of the 52 may be solvable by better matching rather than by judgment. Falsified if a matching improvement clears most of the 52 with no human decision.
- A3. **Fund admin's decisions are reliable enough to be worth capturing.** Extends D4–D5. The compounding precedent library is an asset only if what enters it is correct. Not tested. Falsified if manager override rate on admin decisions is systematically high.
- A4. **The dual-control promotion gate is a sufficient quality control on precedent.** Extends D4. Untested; no evidence on how often two roles agree on wrong treatments.
- A5. **Team stability and internal agreement are high enough for a shared precedent library to stay coherent.** No turnover or disagreement data exists in the evidence.
- A6. **The anonymised datasets are representative of production distribution.** F6 preserves counts, but one week (E2) and one quarter (E3) are single samples; base rates across closes are unknown.
- A7. **Call-1's defects are at least partly visibility failures rather than purely quality failures.** F15 lists defects; F16 shows the manager compensating by re-verification. Whether recorded reasoning would have prevented those defects is not established (explicitly asked in this work; not answered because transcripts are partial, F18).
- A8. **Override rate on stable patterns is observable.** Extends D6. Requires instrumentation that does not exist in the current Excel workflow (F2).

## 5. Uncertainties

Open questions where the evidence does not support a position either way.

- U1. Root cause split of call-1 defects: judgment error, arithmetic/tie-out omission, or period-cutoff control failure. F15 contains all three types; proportions unknown.
- U2. Deployment model (SaaS to administrators / insourcing tooling for GPs / vendor delivery platform). F17 points toward provider replacement, but who paid in the underlying engagements is not in the evidence. This determines rule-file ownership.
- U3. Whether LPs and auditors will accept case-file lineage ("independence in evidence") as a substitute for a third-party administrator's name ("independence in name"). No evidence either way.
- U4. Materiality thresholds that define which cases reach the manager (D7). Undefined.
- U5. Current baseline error rate and cost of error. Only qualitative evidence (F14–F16); no measured defect rate, no restatement history.
- U6. Turnover and disagreement rates among fund account and fund admin staff (bears on A5).
- U7. What share of the 52 unmatched counterparties, 30 project codes and 198 investor names are genuinely new versus recurring-but-unrecorded (bears on A2 and on the value of capture).

## 6. Unresolved risks

Risk register. Each entry: description → evidence → why unresolved → current mitigation status.

| ID | Risk | Evidence | Why unresolved | Mitigation status |
|---|---|---|---|---|
| R1 | **Late detection.** Judgment defects surface at pack review (round 6–7) or restatement, not when made. | F14, F15, F1–F2 | No in-process detective control exists; the design (D1–D3) proposes one but it is unbuilt and untested. | Design only |
| R2 | **Unowned compensating control.** The manager's shadow AI re-verification (F16) is the de facto final control; it is outside the process, unaudited, and single-person dependent. | F16, F3 | Nothing in the current process replaces it; the design measures its disappearance (D8) but cannot force it. | Metric defined; no control |
| R3 | **Period-cutoff / subsequent-event errors are outside the classification model.** | F15 ("subsequent events left in with dates rolled forward") | The case/precedent model (D1–D5) addresses classification and mapping. It contains no cutoff control. This is a scope gap, not a design flaw. | Unaddressed |
| R4 | **Tie-out omission.** "No one checking that numbers foot" is a reconciliation failure, not a judgment failure. | F15; F13 shows a rec step exists in E3 but F15 shows it is not reliably performed in E4's case | Not covered by judgment capture; requires a deterministic tie-out gate. | Unaddressed in design; partially present in E3 workbook |
| R5 | **Precedent pollution.** Wrong or guessed treatments enter the standing-instruction library and compound. | F11 (gaps required human decisions), F15, A3, A4 | Quality of captured judgment is assumed, not measured. | Gate designed (D4); untested |
| R6 | **Defensive escalation.** If recorded decisions are read as a scorecard, admins escalate rather than decide; queue volume rises, speed falls. | D6 rationale; F1 | Depends on metric discipline the firm must hold; product cannot enforce it. | Metric design only |
| R7 | **Lineage retrofit impossibility.** If speed is built before provenance, source-to-number lineage cannot be reconstructed later. | F2 (current process discards provenance at Excel stage), D8 | Architectural; must be a day-one constraint. | Stated as constraint; not yet built |
| R8 | **Independence dilution.** Under GP-insourced or vendor-delivered deployment (U2), fund account is no longer a third party in name (F1). | F1, F17, U2, U3 | Acceptance by LPs/auditors unknown. | Unresolved; depends on U2/U3 |
| R9 | **Rule-file ownership conflict.** The adoption promise (D5: fund account owns the file) conflicts with a provider-replacement go-to-market (F17). | D5, F17 | Deployment model not chosen (U2). | Unresolved |
| R10 | **Transparency overload.** Exposing all cases to the manager recreates the multi-round review in a new form. | F14, D7 | Materiality tiering undefined (U4). | Principle stated; thresholds undefined |
| R11 | **Extraction failure misread as judgment.** Truncated/wrapped PDF strings (F7) may be mis-attributed to "needs human decision", inflating the judgment queue and the precedent library with matching artefacts. | F5, F7, A2 | Share unknown (U7). | Unmeasured |
| R12 | **Sample and evidence limits.** One week, one quarter, anonymised, partial transcripts. Any base-rate claim rests on thin evidence. | F4, F9, F18, A6 | Cannot be resolved without production volume. | Acknowledged |
| R13 | **Key-person dependency.** Classification knowledge lives in heads and side files; loss of a fund accountant or admin removes uncaptured precedent. | F1, F7, F11 | Capture mechanism (D5) unbuilt. | Design only |

## 7. Evidence register

| Tag | Source | Type | Notes |
|---|---|---|---|
| E1 | User-stated scenario (fund manager / fund admin / fund account workflow and pain points) | Stated scenario | Treated as fact about the target operation |
| E2 | `01-bank-statements-to-journal-entries/README.md` | Dataset documentation | Anonymised, counts preserved |
| E3 | `02-investor-level-gl-to-loader/README.md` | Dataset documentation | Anonymised, amounts tie |
| E4 | `03-call-transcripts/README.md` | Summary of four partial transcripts | Transcript bodies not reviewed; only README summaries |
| E5 | Three design memos produced in this work (subject-user / case object; fund account role; priority and sequence discussion) | Design decisions | Establish decisions, not market facts |
| E6 | Top-level `README.md` (anonymisation method; imperfections deliberate) | Dataset documentation | Supports F6, A6 |

## 8. Key decisions and the evidence behind them

- **Decision: the core problem is control absence over the judgment layer, not automation of extraction.**
  Evidence: F5–F7 and F10–F11 show the unmatched residue is where human decisions are made; F14–F16 show that residue is where defects surface; F2 shows no record of those decisions exists. Alternative rejected: "the problem is manual PDF-to-Excel effort" — rejected because F17's cost is real but F15's defect types are not extraction defects.
- **Decision: the manager's shadow re-verification is classified as a failed-control signal, not a user habit.**
  Evidence: F16 in combination with F14. A functioning control chain would not require the risk owner to re-perform the work.
- **Decision: period-cutoff and tie-out are recorded as scope gaps (R3, R4) rather than folded into the judgment model.**
  Evidence: F15 names them explicitly; D1–D5 do not cover them. Folding them in would introduce a factor without design support.
- **Decision: A1 (fee accountability) is held as an assumption, not a fact.**
  Evidence: it was supplied as a working premise; no source in E1–E6 states it.

## 9. Consistency and completeness review

- Every fact (F1–F18) cites a source in Section 7. Checked.
- Every assumption (A1–A8) names the fact it extends and a falsifier. Checked.
- Every risk (R1–R13) cites at least one fact or assumption. Checked.
- No factor appears in Section 6 that is absent from Sections 3–5. Checked.
- Known limitation: E4 is used through README summaries only; if transcript bodies are later reviewed, F14–F17, A7 and U1 should be re-examined first.
- Known limitation: E1 is the operator's own description of the workflow and is not independently verified.

## 10. Next actions (risk scope only)

1. Resolve U1 by reading the call-1 transcript body and tagging each defect as judgment / arithmetic / cutoff. This directly sizes R3 and R4 against R1.
2. Resolve U7 by running a matching pass over the 52 unmatched counterparties and recording how many clear without a decision. This sizes R11 and tests A2.
3. Decide U2 before any build that touches rule-file ownership, because R8 and R9 cannot be mitigated until it is decided.
