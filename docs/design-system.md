# Design System — Reviewer Lens

**Status:** v1 spec, 2026-09-06 (Sunday, submission day)
**Mode:** extend — no components exist yet; this is the minimum set to build against.
**Scored under:** UI 25% — "Clean and considered. A non-technical fund manager is the user. No AI slop." (F28)
**Derived from:** `problem-statement.md` "What solved looks like" criteria 1–4; F22, F24, F25 (E7).

---

## 1. The one rule

**Every number on screen can be traced to its source in one click, and every classification shows whether a rule or a person produced it.** Anything on screen that violates this is off-scope, however good it looks.

## 2. Vocabulary — four words, used identically everywhere

| Word | Meaning | Never say instead |
|---|---|---|
| **Rule** | Line was produced by a versioned mapping the accountant owns | "auto-classified", "AI", "predicted" |
| **Decision** | A person chose between candidate treatments and wrote a reason | "manual override" (that is the next word), "exception" |
| **Override** | A reviewer changed a Rule or Decision and wrote a reason | "correction", "edit" |
| **Unresolved** | No rule matched and no one has decided yet | "error", "failed", "anomaly" |

Same four words in the badge, the filter, the legend, the README, and the video. Judges will read all four; inconsistency reads as slop.

## 3. Tokens

### Colour — semantic, keyed to provenance; never colour alone
| Token | Use | Hex (light) | Pair with |
|---|---|---|---|
| `prov-rule` | Rule badge | `#2F5F8F` | icon `⚙` / text "Rule" |
| `prov-decision` | Decision badge | `#9A6A00` | icon `✎` / text "Decision" |
| `prov-override` | Override badge | `#6B3FA0` | icon `↺` / text "Override" |
| `prov-unresolved` | Unresolved badge, row tint | `#B42318` | icon `!` / text "Unresolved" |
| `gate-pass` | Tie-out gate pass | `#1B7F4B` | text "Ties to zero" |
| `gate-fail` | Tie-out gate fail | `#B42318` | text "Off by {amount}" |
| `neutral-0..9` | Text, borders, surfaces | greys, min 4.5:1 for text | — |
| `surface`, `surface-raised` | Page, panels | `#FFFFFF`, `#F7F8FA` | — |
| `source-highlight` | Highlighted string in PDF excerpt | `#FFF3B0` background | — |

No gradients. No glows. No brand accent colour beyond `prov-rule`. One dark theme is optional; do not ship two themes half-finished.

### Typography
| Token | Value | Use |
|---|---|---|
| `font-ui` | system-ui stack (Inter if bundled) | Everything except below |
| `font-mono` | ui-monospace stack | Source strings, references, IBAN-shaped IDs, rule IDs |
| `font-num` | `font-variant-numeric: tabular-nums` on `font-ui` | **All amounts. Non-negotiable.** |
| `text-xs/sm/base/lg` | 12 / 13 / 14 / 18 px | Table cells are `sm`; body `base`; one `lg` per screen |
| `weight-regular/medium/semibold` | 400 / 500 / 600 | No bold (700) — it reads as shouting in a finance table |

### Numbers and dates (these are tokens too)
- Amounts: right-aligned, thousands separators, 2 dp, currency code as a separate mono column (`GBP`, `USD`, `EUR`, `SGD` — four currencies in dataset 01). Negatives with a leading minus, not parentheses, not red.
- Dates: `dd MMM yyyy` everywhere. No relative dates ("3 days ago").
- Never round a source figure. If the PDF says 12,345.67 the screen says 12,345.67.

### Spacing / density
- Scale: 4 / 8 / 12 / 16 / 24 / 32.
- Table row height 36 px. This is a reviewer's tool; dense beats airy.
- Panel padding 16. Page gutter 24.

### Borders, radius, shadow, motion
- Radius 4 on inputs and badges; 6 on panels. Nothing pill-shaped except badges.
- Border 1 px `neutral-3`. Shadows: one level, panels only.
- Motion: 120 ms ease-out on panel open; nothing else animates. No skeleton shimmer, no confetti, no typing effect.

## 4. Components — the minimum set (7)

### C1 · Batch header
**Purpose.** Tells the reviewer in one glance whether the batch is safe to read.
**Props.** `entity`, `account`, `currency`, `period`, `counts: {rule, decision, override, unresolved}`, `gate: {status: pass|fail, delta}`.
**States.** default · gate-fail (header border `gate-fail`, delta shown) · loading (counts as `—`, not spinners).
**A11y.** `role="region"`, `aria-label="Batch summary"`; gate status is text, not just colour.
**Don't.** Don't add a chart. Don't add a percentage "confidence".

### C2 · Line table
**Purpose.** One row per journal line (or loader row). The queue.
**Columns (fixed order).** Date · Source ref (mono) · Counterparty (as matched) · Amount (num) · CCY · Classification · Provenance badge (C3) · Reviewer status.
**Props.** `rows[]`, `selectedId`, `filter: all|rule|decision|override|unresolved`, `sort`.
**States.** default · row-selected (left border 3 px `prov-*` of that row) · row-unresolved (tint `prov-unresolved` at 6 % opacity) · empty (see C7).
**Keyboard.** `↑/↓` move, `Enter` opens trace (C4), `Esc` closes. `A` / `R` / `O` for accept / reject / override — optional; if shipped, show them in a footer legend.
**A11y.** Real `<table>`; `aria-sort` on sorted column; row `aria-selected`.
**Don't.** No inline editing of amounts. No colour-coded amounts. No hover tooltips carrying required information.

### C3 · Provenance badge
**Purpose.** The one glance that answers "rule or person?"
**Props.** `kind: rule|decision|override|unresolved`, `ref` (rule id + version, or decision id), `compact?`.
**Visual.** Icon + word + ref in mono, e.g. `⚙ Rule  VND-alias v7` · `✎ Decision  D-0142` · `↺ Override  D-0142→D-0158` · `! Unresolved`.
**States.** default · hover shows full ref (still readable without hover).
**A11y.** `aria-label="Provenance: Rule, vendor alias rule version 7"`.
**Don't.** Never a percentage. Never the word "AI".

### C4 · Trace panel
**Purpose.** Solved-criteria 1–3 in one place. Opens to the right of C2, never as a modal over it.
**Sections, in order (do not reorder).**
1. **Source** — PDF excerpt (C5) or GL row or legal clause, with the matched string highlighted, page number, file name.
2. **How it was produced** — Rule card (rule id, version, the rule text itself, who owns it) **or** Decision card (C6).
3. **Chain** — if overridden: prior decision → override, each with author and reason.
4. **Review actions** — C7 bar.
**States.** loading (section headers render, content as `—`) · rule · decision · override · unresolved (sections 2–3 read "No rule matched. No decision recorded." and C7 offers Decide instead of Accept).
**A11y.** `role="complementary"`, focus moves into panel on open and returns to the row on close; `Esc` closes.
**Don't.** No tabs. No accordion. The reviewer must not have to click to see the source.

### C5 · Source excerpt
**Purpose.** The literal bank text, in the bank's truncated uppercase line-wrapped form (F7), with the matched span highlighted.
**Props.** `text`, `highlight: [start,end]`, `page`, `file`, `openFullHref?`.
**Visual.** `font-mono`, preserved line breaks, `source-highlight` on the span, page/file in `text-xs` beneath.
**States.** default · no-highlight (unresolved: whole excerpt shown, nothing highlighted, caption "No match in master lists").
**Don't.** Don't clean the text. Don't title-case it. The mess is the evidence.

### C6 · Decision card
**Purpose.** Solved-criterion 3: candidates, chosen, who, reason.
**Props.** `candidates[{treatment, account, pnlDelta}]`, `chosenIndex`, `author`, `role: accountant|admin|manager`, `date`, `reason` (≤ 1 paragraph), `precedentRef?`.
**Visual.** Candidates as a 2–3 row list; chosen row marked with a check and `weight-medium`; P&L delta in `font-num`; reason as plain prose beneath; author line `Name · Role · dd MMM yyyy`.
**States.** default · draft (proposed by system, no author yet — label "Proposed", author "—") · superseded (struck-through, linked to the override).
**A11y.** `role="group"`, `aria-labelledby` the card title.
**Don't.** No star ratings, no thumbs, no "confidence".

### C7 · Review action bar
**Purpose.** Accept / Reject / Override-with-reason. The override is itself a Decision.
**Props.** `lineId`, `currentKind`, `onAccept`, `onReject`, `onOverride(reason, treatment)`.
**Visual.** Three buttons, one primary (Accept), two secondary. Override expands an inline form: treatment select + reason textarea + confirm. **Reason is required; confirm is disabled until ≥ 20 characters.**
**States.** default · override-open · submitting (button text "Saving…", disabled) · done (bar collapses to a one-line status "Accepted by {name}, {date}").
**A11y.** Buttons are `<button>`; the form has labels; error text tied by `aria-describedby`.
**Don't.** No swipe gestures. No "Accept all" on this bar — batch accept lives in C1 only for rule-covered lines and only after the gate passes.

### Empty and error states (shared)
| Situation | Copy | Visual |
|---|---|---|
| All lines rule-covered, gate passed | "100 lines. All rule-covered. Ties to zero." | Plain text in C1; table renders normally |
| Zero lines | "No lines in this batch." | Centered `text-sm` |
| PDF failed to parse | "Statement {file} could not be read. {n} lines unresolved." | Banner above C2, `prov-unresolved` border |
| Gate fails | "Off by {amount} {ccy}." | C1 border + first-row banner |

No illustrations, no mascots, no exclamation marks in copy.

## 5. Pre-submission UI checklist

Tick every line before recording the video. Each maps to the UI criterion or to a solved-criterion in `problem-statement.md`.

**Traceability (the product)**
- [ ] Click any amount → source excerpt with highlighted string, page, file (criterion 1)
- [ ] Every row shows Rule / Decision / Override / Unresolved — no fifth state, no blank (criterion 2)
- [ ] Every Decision shows candidates, chosen, author, role, date, reason (criterion 3)
- [ ] Batch header shows tie-out gate result and delta (criterion 4)
- [ ] Override requires a reason and creates a new Decision visible in the chain

**"Non-technical fund manager is the user"**
- [ ] Zero jargon from the build: no "pipeline", "LLM", "embedding", "confidence", "inference"
- [ ] Domain words only: journal line, counterparty, batch, ties to zero, statement, rule, decision
- [ ] One primary action per screen
- [ ] Nothing required is hidden behind hover
- [ ] Amounts: right-aligned, tabular numerals, currency code column, 2 dp, no rounding of source figures
- [ ] Dates: `dd MMM yyyy`, consistent

**"No AI slop"**
- [ ] No chat interface anywhere on the primary screen
- [ ] No gradients, glows, emoji, illustrations, confetti, typing effects
- [ ] No vanity charts or KPI tiles; the only numbers on the header are counts and the gate delta
- [ ] No placeholder or lorem text; data is the anonymised dataset, mess intact
- [ ] Copy has no exclamation marks and no adjectives about the product
- [ ] Bold (700) not used; headings are `weight-semibold`

**"Clean and considered"**
- [ ] Four provenance words identical across badge, filter, legend, README, video script
- [ ] Colour never carries meaning alone (icon + word on every badge; gate status is text)
- [ ] Text contrast ≥ 4.5:1; focus ring visible on every interactive element
- [ ] Keyboard: arrow through rows, Enter opens trace, Esc closes, focus returns
- [ ] Table is a real `<table>`; buttons are real `<button>`
- [ ] Trace panel opens beside the table, not over it

**Video-specific**
- [ ] First screen shown is C2 with C1 above it — not a landing page, not a login
- [ ] The first click in the video is an amount → source (criterion 1 on camera within 30 s)
- [ ] One Unresolved line is decided on camera, then one Decision is overridden, showing the chain

## 6. Explicitly not in this system (this weekend)

- Accountant rule editor (X-01 — post-hackathon; the accountant side in the demo is the seed rule file loaded from the workbook sheets)
- Materiality tiering (X-06)
- Precedent library browser (L-01)
- Any dashboard, chart, or trend view
- Dark theme, responsive breakpoints below 1024 px (reviewers use laptops; the judging panel will too)

## 7. Open questions (only if time allows — otherwise default as stated)

- Does the trace panel need a "open full PDF" link? **Default: yes if the PDF is served locally; omit otherwise.**
- Filter as segmented control or dropdown? **Default: segmented, five segments (All + four words).**
- Show P&L delta for candidates when the treatment doesn't change P&L (e.g. balance-sheet reclass)? **Default: show `0.00`, not blank.**
