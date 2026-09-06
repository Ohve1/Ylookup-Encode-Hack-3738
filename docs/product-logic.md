# Product logic

A fund-close workflow and control layer that turns fragmented source files into traceable financial Lines, surfaces mapping exceptions, and records the decisions behind validated outputs.

It sits between source artifacts and the system of record; it does not replace the accounting platform. Humans still load the validated export. The system proposes; it does not decide unless a class is dual-control blessed as a Rule.

## Fund-close architecture (product boundary)

```
                         FUND CLOSE
                             │
                 PDF / Excel / GL / CSV
                             │
                             ▼
                        INGESTION
                             │
                             ▼
                     CANONICAL LINE
                             │
                    ┌────────┴────────┐
                    ▼                 ▼
                  RULE              NO RULE
                    │                 │
                    ▼                 ▼
                PROPOSED            CASE
                                      │
                         ┌────────────┴───────────┐
                         ▼                        ▼
                    ACCOUNTANT                 MANAGER
                    Resolve                   Approve
                         │                        │
                         └──────────┬─────────────┘
                                    ▼
                                DECISION
                                    │
                              ┌─────┴─────┐
                              ▼           ▼
                    Validated Export   Precedent?
                              │           │
                              ▼           ▼
                      Existing GL     Dual-control
                      (operator load)     │
                              │           ▼
                           TIE-OUT      RULE
                                          │
                                          ▼
                                    Future close
```

**Product stops at Validated Export.**  
Shipped NOW: `validated_mapping_csv_v1` → `validated_mapping_<close_id>.csv` after sign-off.  
Not in scope: Investran / eFront / QuickBooks API write-back. System-specific loader shapes are LATER.

## Same core workflow

```
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

Dataset 01 (Bank → Journal) and Dataset 02 (GL → Loader) are two **validation cases** of this workflow, not two product features. See `dataset-mapping.md`.

## What enters → what leaves

| Stage | Question |
|---|---|
| Input | PDF statement, workbook maps, staging / journal / GL rows |
| Transform | Each amount becomes a Line with a Source pointer |
| Rules | Exact map hit → origin **Rule** |
| Automation stops | No map, `Review` flag, or the operator is guessing |
| Human | Accountant resolves; Admin coordinates; Manager approves |
| Recorded | **Decision** (or **Override**) + who + one paragraph + source excerpt |
| Close complete | Batch **tie-out** passes; **validated export** ready for the existing SoR |
| Compound (NEXT) | Promote approved Decision → Rule under dual control; monitor Rule health |

## Decision logic

```
LINE
 |
 v
Does a Rule match exactly?
 |
 +-- YES -> apply Rule -> origin = Rule
 |              |
 |              v
 |         Reviewer still sees lineage
 |         (propose, do not auto-post / auto-export)
 |
 +-- NO  -> open Case -> origin = Unresolved
              |
              v
         Accountant resolves; Admin coordinates; Manager approves
              |
              v
         Accept  -> Decision, resolved
         Reject  -> stays Unresolved / re-route
         Override -> Override (a Decision that replaces a Rule or prior Decision)
              |
              v
         Dual-control: "Promote as precedent?" -> versioned Rule (NEXT)
```

| Situation | System action |
|---|---|
| Exact rule match | Propose mapped treatment. Origin = **Rule**. |
| No rule / blank map / `Review` | Create **Case**. Origin = **Unresolved**. |
| Operator would be guessing | Must file a Case. Guessing without a Case is a defect. |
| Reviewer accepts | Resolve. Origin = **Decision** (or stays **Rule** if they accepted a rule hit). |
| Reviewer rejects | Stay Unresolved or re-route. |
| Reviewer overrides | Resolve + record **Override** (reason required). |
| Source excerpt unavailable | Block resolution. |
| Tie-out fails | Slice cannot move to export. Close not complete. |
| Export | Emit `validated_mapping_csv_v1` only after sign-off + tie-out + no open Cases. |
| Promote to Rule | Requires second approval (dual control). One accountant Decision alone never becomes a Rule. |

Surface words only: **Rule / Decision / Override / Unresolved**.  
Do not label lines with “AI”, “confidence”, or “pipeline”.

## Why this is better than Excel

Excel holds the number. It does not hold *which PDF string*, *which map version*, or *who changed the class and why*. The six-round review exists because the reviewer one level up has to reconstruct that by hand.

## Where automation helps

Repeatable map hits (Vendor Codes, Account Map, Allocation Rule, CoA). That is the workshop becoming a factory on the 50% that already has a rule.

Automation is not the first question. The first question is:

> Can every financial item’s treatment be seen, validated, reviewed, recorded, and leave as a validated output?

## Why the resulting number can be trusted

Every Line answers four questions without leaving the reviewer screen:

1. Source excerpt (file + page/sheet + string)
2. Rule or Decision (id + version, or named person)
3. If Decision: candidates, chosen treatment, who, reason
4. Batch tie-out pass / fail

Rule health (NEXT) adds: used / accepted / overridden / override rate → flag potentially stale precedent.
