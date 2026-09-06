# Product logic

The product converts fragmented close evidence into traceable financial Lines, applies reusable Rules, routes unresolved items into Cases, and records human decisions with source lineage and tie-out controls.

It is not a new general ledger. Humans still post. The system proposes; it does not decide unless the admin firm has blessed that class.

## Product logic map

```
SOURCE FILES
PDF / Excel / CSV
        |
        v
    INGESTION          (local; dataset bodies stay off GitHub)
        |
        v
  CANONICAL MODEL
        |
   +----+----+
   v    v    v
 LINE  RULE  SOURCE
   |     |     |
   |     v     |
   |  MATCHING |
   |     |     |
   v     v     v
 +-----------------+
 | RESOLVED / CASE |
 +--------+--------+
          v
    HUMAN REVIEW
    Accept | Reject | Override
          v
       DECISION
          v
        TIE-OUT
          v
   READY FOR POSTING   -> existing SoR (not replaced)
```

## What enters -> what leaves

| Stage | Question |
|---|---|
| Input | PDF statement, workbook maps, staging / journal rows |
| Transform | Each amount becomes a Line with a Source pointer |
| Rules | Exact map hit -> origin **Rule** |
| Automation stops | No map, `Review` flag, or the operator is guessing |
| Human | Accept / reject / override-with-reason |
| Recorded | **Decision** (or **Override**) + who + one paragraph + source excerpt |
| Close complete | Batch **tie-out** passes and no Unresolved material items remain on the slice |

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
 |         (propose, do not auto-post)
 |
 +-- NO  -> open Case -> origin = Unresolved
              |
              v
         Accountant files; Admin decides
              |
              v
         Accept  -> Decision, resolved
         Reject  -> stays Unresolved / re-route
         Override -> Override (a Decision that replaces a Rule or prior Decision)
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
| Tie-out fails | Slice cannot move to admin / manager. Close not complete. |

Surface words only: **Rule / Decision / Override / Unresolved**.
Do not label lines with “AI”, “confidence”, or “pipeline”.

## Why this is better than Excel

Excel holds the number. It does not hold *which PDF string*, *which map version*, or *who changed the class and why*. The six-round review exists because the reviewer one level up has to reconstruct that by hand.

## Where automation helps

Repeatable map hits (Vendor Codes, Account Map, Allocation Rule, CoA). That is the workshop becoming a factory on the 50% that already has a rule.

## Why the resulting number can be trusted

Every Line answers four questions without leaving the reviewer screen:

1. Source excerpt (file + page/sheet + string)
2. Rule or Decision (id + version, or named person)
3. If Decision: candidates, chosen treatment, who, reason
4. Batch tie-out pass / fail
