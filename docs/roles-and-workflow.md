# Roles and workflow

Three seats, one object. The question is whose judgment remains a job, not whose problem.

```
Fund account (maker)
        |
        v
  first-pass Rules
  file a Case when guessing

Fund admin (checker)
        |
        v
  legal overlay
  decide Cases
  own the precedent library

Fund manager (risk owner)
        |
        v
  material exceptions + batch health
  accept residual risk / send back / override
```

## RACI for this object

| Action | Accountant | Fund admin | Manager |
|---|---|---|---|
| Edit rule file | Yes | | |
| First-pass rule-covered Lines | Yes | | |
| File Case when guessing | Yes | | |
| Decide Case (legal / mapping-gap) | | Yes | |
| Assign / chase Case queue | | Yes | |
| Monitor close / blockers | | Yes | |
| Approve material exception | | | Yes |
| Override with reason | | Yes | Yes |
| View lineage | Yes | Yes | Yes |
| Post to system of record | | Yes (after accept) | |
| Auto-post unblessed class | forbidden | forbidden | forbidden |

Accountant is not scored on admin override rate. Override rate on stable patterns is a learning signal, not a person score.

## Weekend demo surface

The default screen is the **reviewer lens** (admin / manager one level up). That is who cannot see the judgment today.

The accountant rule editor is out of weekend scope. Accountant exists in the demo only as the input that produced the Case.
