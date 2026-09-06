# Roles and workflow

Three seats, one underlying object. Every seat operates the same chain:

```
Line → Source → Rule / Mapping → Case → Decision → Export
```

```
Accountant          Admin               Manager
 Prepare             Decide               Approve
     │                   │                    │
     v                   v                    v
 My Cases          Close Overview          Review
 What needs        What's blocking       What decisions
 preparation?      the close?            require my judgement?
```

## Verbs (minimal path)

| Seat | Verb | Can record Decision? | Owns |
|---|---|---|---|
| Fund accountant | **Prepare** | No | First-pass Rules; file Case when guessing; attach lineage; draft candidates |
| Fund admin | **Decide** | Yes (Accept / Reject / Override) | Queue; legal overlay; blockers; emit validated export |
| Fund manager | **Approve** | Yes (Approve / Override; no Reject) | Material exceptions; residual risk; dual-control on promote |

UI and `POST /api/decision` both enforce this. Accountant clicking Accept is blocked.

## RACI for this object

| Action | Accountant | Fund admin | Manager |
|---|---|---|---|
| Edit rule file | Yes | | |
| First-pass rule-covered Lines | Yes | | |
| File Case when guessing | Yes | | |
| Prepare / draft candidates on Case | Yes | Yes | |
| Coordinate Case queue / blockers | | Yes | |
| Decide Case (Accept / Reject / Override) | | Yes | |
| Approve material exception | | | Yes |
| Override with reason (≥ 20 chars) | | Yes | Yes |
| Promote Decision → Rule (dual control) | propose | Yes (1st) | Yes (2nd) |
| View lineage (Line→…→Export) | Yes | Yes | Yes |
| Emit validated export | | Yes (after accept + tie-out + sign-off) | Yes (sign-off) |
| Load export into SoR | | Yes (outside product) | |
| SoR API write-back | forbidden | forbidden | forbidden |
| Auto-post / auto-promote unblessed class | forbidden | forbidden | forbidden |

Accountant is not scored on admin override rate. Override rate on stable patterns is a **Rule health** learning signal, not a person score.

## UI information hierarchy

| Page | Seat | Primary question | Must still show |
|---|---|---|---|
| My Cases / Lines | Accountant | What needs preparation? | Line, Source, How produced chain, Case |
| Close Overview | Admin | What's blocking the close? | Open Cases, tie-out, export readiness |
| Review | Manager | What decisions require my judgement? | Material Cases, prior Decisions |

Every Case page shows **How produced**: Source → Line → Rule/Mapping gap → Case → Decision → Export.

## Demo surface

Default screen is the **reviewer lens** (admin / manager). Accountant prepares; Admin decides on camera; Manager approves material residue.
