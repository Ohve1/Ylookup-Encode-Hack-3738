# Core problem definition — F / A / U / R / E

> Reconstructed 2026-09-06. `problem-statement.md` cites tags from this file (E2, E3, E4, E7, R3, R8, U3, A1, §11). The tags below carry those ids so the citations resolve. Anything not traceable to a transcript, the dataset READMEs, or the brief is marked A (assumption) or U (unknown), not F.

Tags: **F** fact we can show · **A** assumption we are making · **U** unknown that could change the answer · **R** risk to the product or the claim · **E** evidence source.

## §1 Evidence sources (E)

| Id | Source | What it gives us |
|---|---|---|
| E1 | Hackathon brief (`YlookupEncodeHackathon.pdf`) | Industry framing, three tracks, scoring: problem identification, solution, presentation |
| E2 | Dataset 01 README + workbook (`docs/data/`) | 100 staging rows; 52 blank counterparty, 30 unresolved project code, 4 position miss, 3 `Review` — preserved from production |
| E3 | Dataset 02 README (`docs/data/`) | `Mapping Gaps` sheet is populated by design and sent back for human decision; 198 investor names unmatched |
| E4 | Call transcript 1 (manager) | NAV takes "six or seven rounds"; manager re-runs administrator output through his own tool |
| E5 | Call transcripts 2–3 (administrator side) | Chain is accountant → admin → manager → investors, workbook by email at each step |
| E6 | Call transcript 4 | Platform maps differ (Revolut, QuickBooks, Investran, eFront) |
| E7 | Live Q&A with accountant and admin personas, 5 Sept | Quotes in `problem-statement.md`: "50% mapping, 50% judgment"; "find it in the PDF … understand what he was thinking"; "not going to switch software" |

## §2 Facts (F)

| Id | Fact | E |
|---|---|---|
| F1 | Classification is a mix of a written map and unwritten judgment | E7 |
| F2 | The residue the map does not cover is large and recurring: 89 raw residue tags on 100 rows in Dataset 01 | E2 |
| F3 | The reviewer above cannot see the judgment without re-deriving the number from the PDF and the formula | E7 |
| F4 | Review chain is three deep and passes a workbook by email | E5, E7 |
| F5 | The administrator will not change the system of record | E7 |
| F6 | Maps are per platform; one fixed map cannot be the answer | E6, E7 |
| F7 | The reviewer's stated checks: balances to zero, categorised correctly, matches the legal document | E7 |
| F8 | The manager shadow-checks the pack because the formal chain has no lineage | E4 |

## §3 Assumptions (A)

| Id | Assumption | Why we hold it | If wrong |
|---|---|---|---|
| A1 | The fund manager takes direct accountability for the administration fee | Sharpens the manager's demand for defensibility | Nothing in the object depends on it (`problem-statement.md`) |
| A2 | The judgment residue is stable enough that decided Cases become useful precedents | Vendor codes and project codes repeat across statements | Candidate drafting loses its precedent evidence; the record is still valuable |
| A3 | Reviewers will accept a reason paragraph plus source excerpt as sufficient to stop re-deriving | E7 admin describes exactly this as the missing thing | Lineage becomes a compliance artefact rather than a time saver |
| A4 | Anonymised datasets behave like production for classification residue | Dataset README: amounts, dates and unmatched rows preserved | Counts change; the shape of the problem does not |

## §4 Unknowns (U)

| Id | Unknown | How to close it |
|---|---|---|
| U1 | How much of the six-to-seven-round NAV problem is classification vs period-cutoff and footing | Full call-1 transcript coding |
| U2 | Whether the admin or the manager owns the rule file (feeds D-005) | One question to each persona |
| U3 | Whether LPs / auditors accept Case-file lineage as an independence signal | Not answerable this weekend; do not claim it |
| U4 | Real-world ratio of exact Rule hits once vendor codes are maintained (Dataset 01 cold start: 25 / 100) | Second close on the same fund |

## §5–§10 Risks (R)

| Id | Risk | Mitigation in this build |
|---|---|---|
| R1 | Product drifts into "AI classifier" and loses the reviewer's trust | D-004, D-010: no confidence, no AI method word; candidates cite evidence |
| R2 | Residue is cleaned up to make the demo look better | `validate()` hard-fails if Dataset 01 residue counts ≠ 52 / 30 / 4 / 3 |
| R3 | Period-cutoff / subsequent-event errors dominate the real review loop | Out of this object (§11); stated openly |
| R4 | Reviewer accepts everything to clear the queue | Accept records who / role / timestamp and the candidates shown; override rate on stable patterns is the trust metric (`product-thesis.md` §9) |
| R5 | Source excerpt cannot be located for some lines | Resolution blocked; Dataset 01 located 100 / 100 exactly |
| R6 | Tie-out passes while lines are mis-mapped | Tie-out is a gate, not a proof; Cases still need decisions before sign-off |
| R7 | Dataset bodies or reversal keys leak into the repo | CI guard on tracked paths; bodies stay on the laptop |
| R8 | Claiming LP / auditor acceptance without evidence | Not claimed (U3) |

## §11 Out of scope (appendix cited by `problem-statement.md`)

- Period-cutoff / subsequent-event controls (R3)
- LP and auditor acceptance of Case-file lineage (R8, U3)
- Deployment model and rule-file ownership (D-005, U2)
- Fee accountability (A1)
- Replacing the administrator, autonomous posting, keystroke telemetry (`product-thesis.md` §10)
