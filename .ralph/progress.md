# Progress ledger

The working copy of this file is reset to empty by the runtime bundle at launch; the
previous bundle's ledger (round-40 pending reviews) remains in git history. Entries below
are appended per iteration of the public-surface migration.

## Iteration 1 — item 1 (functional): line detail states what a line measures, not why it moved

**Chosen because** `.ralph/plan.md` orders the copy-and-structure items first and names
the `measures` field as the first of the three fields later items reference. It also
removes the largest single block of unsupported claim in the bundle: 24 causal
`explain` paragraphs (each one asserting that a reading proves a hidden force
overpowered a guard). No item was marked hard-blocked; the ledger was empty on entry, so
the branch `public-surface/migration` was created from `main` at `313bfd0`.

**Entry state measured.** `python -m pytest tests/ -q` 415 passed; lint tier 66 OK;
forbidden-literal 3 OK; audit 28 OK; `tools/replay.py --check` exit 0, rows 2878,
divergence 0; `tools/pending.py --check` 6 tagged / 0 overdue; render smoke OK;
`data/annotations.csv` byte-identical to its `docs/data/` mirror. Baseline was green, so
the new assertions below are the only source of the recorded failures.

**Test-first, failures recorded.** Two assertions were added before any copy changed:

- `tests/render_smoke.js` (new T26 block): `lineModal` must not contain three sampled
  sentences from the retired causal payloads — `Airlines fight to keep planes on
  schedule` (flights EN), `fear has overpowered greed` (credit_spread EN), and
  `说明有更大的力量压垮了这股动机` (flights ZH) — and must render its own
  `measures.<lang>` string. Run on the unmodified page: FAIL, 48 lines of
  `measures(<lang>): LINES entry <id> declares no measures.<lang>` plus the two
  `still renders retired causal wording` hits.
- `tests/lint_public_surface.py` (new `TestLineDetailStatesWhatIsMeasured`): every
  `const LINES` entry carries a non-empty EN and ZH `measures` block, the `explain`
  field is gone, and no definition carries one of the eight causal connectives. Run on
  the unmodified page: `test_every_line_declares_a_bilingual_measures_definition` FAIL
  (24 ids incomplete), `test_the_causal_explain_field_is_gone` FAIL. The connectives test
  passed vacuously there and is bound by the first test, which fails loudly when no
  definition parses at all.

**Decision (conservative, reversible).** The deck's `measuresLabel` (`Measures` /
`测量内容`) is added as a `T` key in both locales and used as a small heading above the
definition in both detail builders (lineModal and openTier2Modal), reusing the existing
`.modal-card .annoh` class — no CSS change. The deck lists the key, no later item claims
it, and the modal otherwise gives a bare paragraph of prose no label. The existing
`alarmTag` direction string is left untouched in the modal: renaming it to the deck's
`directionLabel` is item 7's work, and doing it here would pre-empt that item's field
rename. `verdictLabel` and the annotation list are also untouched — dated record text, not
instrument explanation.

**Files changed.**

- `docs/index.html` — all 24 `LINES[].explain` blocks replaced with `measures:{en,zh}`
  using the design deck §4 definitions verbatim (quantity, population or region, sampling
  cadence, unit; no causal connective); `measuresLabel` added to both `T` locales;
  `lineModal` and `openTier2Modal` now interpolate `L.measures[lang]` under that heading
  between the tags and the annotations. Nothing else in the page moved.
- `tests/render_smoke.js` — new T26 assertion block (sampled retired sentences in two
  languages, plus the positive `measures.<lang>` render check for all 24 lines and both
  languages).
- `tests/lint_public_surface.py` — new `CAUSAL_CONNECTIVES`, `_docs_measures()` (regex
  over the `const LINES` block, entries split on their own `{ id:"…"` starts, keyed by
  line id) and `TestLineDetailStatesWhatIsMeasured`; module docstring now says three
  things are checked and describes the new one.

**Verification results (after implementation).**

- gate tier `python -m pytest tests/ -q` — `415 passed, 126 subtests passed in 0.95s`
- lint tier `python -m unittest discover tests -p "lint_*.py"` — `Ran 69 tests … OK`
- forbidden literal `python tests/lint_no_forbidden_literal.py` — `Ran 3 tests … OK`
- audit tier `python -m unittest discover tests -p "audit_*.py"` — `Ran 28 tests … OK`
- replay `python tools/replay.py --check` — exit 0, `rows=2878 divergence=0`
- pending `python tools/pending.py --check` — `OK — 6 tagged pending item(s), 0 overdue, 0 unparseable`
- render smoke `node tests/render_smoke.js` — `render OK in both languages; no runtime errors, no undefined/NaN`
- annotations mirror `cmp data/annotations.csv docs/data/annotations.csv` — `cmp: identical`

Rendered detail checked by hand for `flights` and `stablecoin_peg` in both languages:
domain, label, `alarming when …` tag, `Source: …` tag, `Measures` heading, definition.
No causal sentence survives, and `grep` finds no remaining `explain` reference in the page.

**Notes for the next iteration.** Item 1 leaves the vocabulary guard red by design:
`alarmTag`/`alarmingWhen`, `resoTitle`/`resoBody`, `calm`/`trembling`, the two probe
kickers and the layer wording are all still user-visible and are owned by items 2–8.
Untouched and still present (not claimed by any item in this bundle): the `verdictLabel`
map, the feel chart block (`feelTitle`/`feelHint`/`feelBars`/`feelchart`), and
`data/leans.csv` consumption — the design deck deletes the feel chart, but no item lists
it, so it was left alone rather than half-removed. `docs/index.html` still has exactly one
`innerHTML`, inside `setMarkup` (lint `TestMarkupHasOneAuditedSink` passes).

## Iteration 2 — item 2 (functional): headline states a fraction with its denominator

**Chosen because** `.ralph/plan.md` ranks copy and structure first, and names the
headline label as the second of the three fields later items reference (`measures` was
item 1). It also removes the last block of `resonance` prose from the page: the
`resoTitle`/`resoBody` modal behind the headline. No item is hard-blocked; the ledger
held only iteration 1.

**Test-first, failures recorded.** `tests/render_smoke.js` gained a fixture with a
non-zero count (2 of 4 comparable) and one with the zero case, plus a T27 block that
assembles the rendered headline from the count block's own fragments (prefix, numerator,
separator, denominator, label tail) and matches it against the deck's pattern, asserts
the block title, question, modal title and a `countModalBody` marker, and bans
`Resonance` / `共振` / `only number that matters` / `唯一重要的数字` from the block and the
modal that opens from it. Run on the unmodified page: 14 failures, one per language and
case, including `the rendered count block is "2lines trembling today …" which does not
match the deck's countLabel pattern`, `count title is "① the change probe · what
suddenly moved today"`, `the count modal does not carry the title "How the count is
made"`, and both retired phrasing hits in each language. A first version of the
assembly read a static `#count-of-wrap` node; the smoke harness has no HTML parser, so
that fragment came back empty and the same four pattern failures reappeared after the
implementation. The assertion now assembles from the three nodes `render()` actually
writes (`#count-prefix`, `#count-sep`, `#count-of`), which is the same sentence and not
a weaker check.

**Decisions (conservative, reversible).**

- The deck's `countLabel` is kept as one template string per language with `{n}` and
  `{m}`; `render()` splits it around the placeholders into a prefix, a separator and a
  tail, so `#count-n` and `#count-of` remain the separate numeric display elements
  (item 6 also names `#count-n`). A `#count-prefix` span carries the ZH leading
  `今天有` and is `hidden` when empty (EN); `#count-sep` carries the exact separator
  (` / ` EN, `/` ZH). The rendered sentence is therefore the deck template verbatim.
- `countTitle` occupies the block-heading slot (`#count-kicker`), which previously held
  `changeKicker`. This is earlier than item 3's step list, which still lists deleting
  `changeKicker` and its DOM assignment; that deletion is now already done. **Item 3
  must keep the `#count-kicker` → `countTitle` assignment** rather than removing the
  kicker element's text assignment.
- The comparable-line denominator rule in `render()` is unchanged (primary roster minus
  dark, blind, closed). The computed value is stored in `headlineDenominator` so
  `countModalBody`'s `{m}` states the same number the headline shows.
- `calm`, `tremblingOne` and `tremblingMany` are deleted: the deck has no zero phrase,
  and the zero case uses the same `countLabel`. This pre-empts the zero-state part of
  item 3, whose remaining anchors are `statusLabel.scoring`, the qualifiers, `nodata`
  and `more`.
- `#level-q` still renders `countQuestion`; the fixed-reference section is outside item
  2's steps and its copy is item 3/5 material. `countColor`, the level headline and
  their style hooks are untouched (item 6).

**Files changed.**

- `docs/index.html` — count block markup (added `#count-prefix`, `#count-sep`, wrapped
  `#count-of`); both `T` locales: `changeKicker` → `countTitle`, `calm` /
  `tremblingOne` / `tremblingMany` → `countLabel`, `countQ` → `countQuestion`,
  `resoTitle` / `resoBody` → `countModalTitle` / `countModalBody(m)`; `resoModal` →
  `countModal` (same `#count` click); `render()` splits the label template, sets
  prefix/separator, stores `headlineDenominator` and renders the tail before the
  existing qualifiers; `#level-q` now reads `countQuestion`.
- `tests/render_smoke.js` — new `buildHeadlineFixtureData` (2 of 4 comparable) and T27
  block (both fixtures × both languages); `resoModal` export/destructure/calls renamed
  to `countModal`, same coverage.

**Verification results (after implementation).** The shell's default `python` resolves
to the pi-lens pip-tools interpreter, which has no pytest; gates were run with
`PATH=/Users/wangyu/.pyenv/shims:$PATH` (pytest 9.0.2), which is the interpreter
iteration 1's 415-passed baseline used.

- gate tier `python -m pytest tests/ -q` — `415 passed, 126 subtests passed in 1.14s`
- lint tier `python -m unittest discover tests -p "lint_*.py"` — `Ran 69 tests … OK`
- forbidden literal `python tests/lint_no_forbidden_literal.py` — `Ran 3 tests … OK`
- audit tier `python -m unittest discover tests -p "audit_*.py"` — `Ran 28 tests … OK`
- replay `python tools/replay.py --check` — exit 0, `TOTAL 1439 0`, divergence 0
  since `STABLE_SINCE` 2026-09-09
- pending `python tools/pending.py --check` — `OK — 6 tagged pending item(s), 0 overdue, 0 unparseable`
- render smoke `node tests/render_smoke.js` — `render OK in both languages; no runtime errors, no undefined/NaN`; headline `0 / 1`; label tail `条读数偏离各自近期记录 · 3 根线无数据（4/4 根线校准中）`
- annotations mirror `cmp data/annotations.csv docs/data/annotations.csv` — `cmp: identical`

The count modal was opened by clicking the real `#count` handler in both languages, so
the asserted title, marker and retired-phrase scan cover the rendered reader surface,
not a builder left unconnected. `grep` finds no remaining `reso`, `countQ`, `calm`,
`tremblingOne` or `tremblingMany` reference in the page.

**Notes for the next iteration.**

- Item 3's step "delete the `changeKicker` key and its DOM assignment" is already
  satisfied; the `#count-kicker` assignment must stay (it renders `countTitle`). Its
  zero-state assertion is also partly satisfied — no `calm`/`平静` key remains in `T` —
  so its failing anchor is `statusLabel.scoring`.
- The reviewer role in the global contract has no installed agent here (only
  `final-review` and `vision-check` are defined, and this bundle never merges or
  releases), so the diff was checked against the item's steps and the gates.
- `render.py`'s overview chart title still reads `Resonance — lines trembling per day`
  and its per-line title still reads `alarming when …`. Item 7 claims only the per-line
  title; the overview title is claimed by no item in this bundle and was left alone.
- `tag`, `<title>`, `levelKicker`, `nodata`, `more`, the `verdictLabel` map and the feel
  chart remain untouched (items 3–8).
