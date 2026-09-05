# The problem we picked

**Ylookup × Encode hackathon · Product track · 5–6 September 2026**
**Status:** provisional — see "What would change this" at the end.

---

## In their words

> "There is like a mapping that we internally use, but it's not like exactly fixed. You can go here and there a bit. So it's like more of a human judgment while you're doing it."
> — fund accountant persona [E7]. A participant summarised it as "50% human experience, 50% mapping"; the persona confirmed: "Exactly."

> "The only way for me to currently check that is manually by looking at the number, finding it in PDF, and then to verify the transform I need to understand what he was thinking… the only way for me to do that is looking at the formula that he made."
> — fund admin persona [E7]

> "If I'm doing an import from PDF, I need to be able to trace it back to where the PDF is. If I'm doing a transformation in Excel, I need to know where these numbers are coming from."
> — fund admin persona [E7]

> "As a fund administrator, I can tell you that I'm not going to switch software. What I do need is the ability to verify the data that I'm sticking into that software."
> — fund admin persona [E7]

**The product is not a new general ledger. It is a record of the 50% that never lands in the mapping file, attached to the source it came from.**

---

## The one object

**Unrecorded classification and mapping-gap decisions — on bank-statement-to-journal-entry and GL-to-loader — with no source lineage for the reviewer one level up.**

That is the whole problem. Everything below is evidence for it, the constraint on solving it, or what we are deliberately not solving this weekend.

## Where it came from

| Claim | Evidence |
|---|---|
| Classification is part mapping, part judgment, and the judgment part is not written down anywhere | E7: accountant persona on the internal mapping being "not exactly fixed"; "sometimes it's a bit dangerous" |
| The judgment residue is large and recurring | E2: 52 of 100 statement rows with no counterparty match, 30 unresolved project codes, 3 flagged `Review` — preserved from production. E3: `Mapping Gaps` sheet populated by design and sent back for human decision; 198 investor names unmatched |
| The reviewer cannot see the judgment or the source without re-doing the work | E7: admin persona finds the number in the PDF and reads the formula to infer intent; "takes me like weeks" |
| The review chain is three deep and each level passes an Excel workbook by email | E7: accountant → admin → fund manager → investors; "there's not much difference" between levels except volume |
| Mappings differ by platform, so a single fixed mapping cannot be the answer | E7: Revolut, QuickBooks, and admin systems (Investran, eFront) each carry their own |
| The reviewer's checks are: does it balance to zero, is it categorised correctly, does the figure match the legal document | E7: admin persona's stated criteria, including checking "the 2% that is here" against the legal document |
| Managers stop trusting the output and re-verify it themselves | E4: call-1 manager runs administrator output through his own AI tool; NAV takes six or seven rounds |

## The constraint

**They will not change the system of record.** The admin persona said it directly. The product sits between the source documents and the accounting system; it never replaces the accounting system, and its output has to be something the reviewer can accept or reject before it goes in.

## Non-goal this weekend

**Replacing the administrator.** The product drafts; a human still posts. Autonomy only on classes the admin has explicitly blessed. This is consistent with decisions D3 and D8 in the decision log and with what the room said.

## What "solved" looks like by Sunday 12:00

For any journal line or loader row the reviewer opens, they can see, without leaving the screen:

1. the source excerpt it came from (statement PDF page and string, or GL row, or legal-document clause);
2. whether it was produced by a rule (which rule, which version) or by a decision;
3. if by a decision: the candidate treatments, the one chosen, who chose it, and the reason in one paragraph;
4. a zero-balance / tie-out gate result for the batch it belongs to.

The reviewer's job changes from "re-derive it" to "accept, reject, or override with a reason" — and the override is itself recorded as a decision with lineage.

## Working premise, stated so it is not mistaken for evidence

We assume the fund manager takes direct accountability for the administration fee. No interview says this. It sharpens the manager's demand for defensibility but nothing in the problem statement depends on it.

## Out of scope this weekend (appendix in `risk/core-problem-definition.md` §11)

- Period-cutoff / subsequent-event controls (R3) — named in call-1, not in the live Q&A, not addressed by this object
- LP and auditor acceptance of case-file lineage as an independence signal (R8, U3)
- Deployment model and who owns the rule file (D-005)
- Fee accountability (A1)

## What would change this

If the full call-1 transcript shows the six-to-seven-round problem is mostly period-cutoff and footing errors rather than classification, this problem is still real but it is partial — the reviewer would need cutoff controls the object above does not provide. The live Q&A lists footing, categorisation and legal-figure checks and does not mention cutoff, which supports the object as chosen but does not settle it.
