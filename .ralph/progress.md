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
