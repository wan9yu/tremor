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

## Iteration 3 — item 3 (functional): zero readings and every row status in instrument words

**Chosen because** `.ralph/plan.md` ranks copy and structure before style, and items 1 and 2
are now passing. Item 3 finishes the copy item that item 2 partly pre-empted (`calm` /
`tremblingOne` / `tremblingMany` are already gone; the remaining anchors were the six
`statusLabel` entries and the count qualifiers). No item is hard-blocked; the ledger held
iterations 1 and 2 only, both green.

**Entry state measured.** Gate 415 passed; lint 69 OK; forbidden-literal 3 OK; audit 28 OK;
`replay --check` exit 0 (2878 rows seen, 1439 since `STABLE_SINCE`, divergence 0);
`pending --check` 6 tagged / 0 overdue; render smoke OK; annotations mirror identical.

**Test-first, failures recorded.** Three assertions were added or rebound before any copy
changed:

- `tests/render_smoke.js` (new T28 block): `statusLabel` must carry the deck's six labels
  in both languages; `darkNote`, `closedNote`, `blindNote`, `calibNote`, `runNote` and
  the renamed `whichLines` must render the deck's sentences; `whichNote` must be gone; the
  rendered zero-count block must contain neither `calm` nor `平静`; and the count block
  must carry the deck's `countQualifying` line. Run on the unmodified page: 34 failures
  across both languages, including `statusLabel."scoring" is undefined`,
  `statusLabel."dark" is "NO DATA"`, `blindNote(2) renders " · 2 lines cannot score (not
  the same as calm)"`, `whichLines renders undefined`, `the retired whichNote key is still
  declared`, and `the count block's qualifying line is ""`.
- `tests/render_smoke.js` T21 rebound the gap-chip assertion from `/NO DATA|无数据/` to
  `/No reading received|尚未收到读数/` — the one existing test that bound a status label
  this item replaces. Run before the copy change: FAIL in both languages, e.g. `gap chip
  did not carry the "dark" statusLabel text: … <span class="wl-gap">NO DATA</span>`.
- `tests/lint_public_surface.py`: `test_statusLabel_keys_equal_normalizes_non_scoring_statuses`
  became `test_statusLabel_keys_equal_normalizes_status_vocabulary`, asserting the map key
  set equals all six `core/normalize.py` statuses instead of the five non-scoring ones.
  Run before the copy change: FAIL, `core/normalize.py status(es) with no dashboard label
  in docs/index.html's statusLabel maps: ['scoring']`. This strengthens rather than weakens
  the binding: the old assertion encoded the pre-migration state in which `scoring`
  intentionally had no label.

**Decisions (conservative, reversible).**

- `statusLabel` now holds all six statuses. The `scoring` entry has no render site today:
  the tier-2 watchlist reads `statusLabel` only for the blind and gap states, and a
  positive card label would be a card-treatment change owned by item 6. The deck's
  inventory calls the new entry page copy, and the lint binds it.
- The English `{n} line(s)` template is resolved to grammatical number: `1 line has no
  reading` / `2 lines have no reading`, `1 line cannot yet be compared` / `2 lines cannot
  yet be compared`. The deck's `(s)` is a pluralization hint, not literal text.
- `whichNote` is renamed `whichLines` per the deck's migration row; it keeps the existing
  join separators (` + ` EN, ` ＋ ` ZH) because the deck template is ` · {names}` in both
  languages and leaves the join to the substitution.
- `runNote` keeps its `(tag, n)` signature. With an empty tag — the single-firing-line case
  — it renders the deck sentence verbatim (` · outside its recent range for 2 consecutive
  collection days`); on a multiple-firing day the line label prefixes it, the same tag
  mechanism the deck's own `leanNote` template uses. The T22 assertion therefore still
  exercises the real call shape, unchanged.
- `countQualifying` is added as visible page text in a new `#count-qualifying` paragraph
  directly under the count block, with one muted CSS rule (`.count-qualifying`). Item 3's
  step 2 asks for the deck's wording that a reading being absent or inside its recent range
  is not a statement about the world; `countQualifying` (`A statistical comparison, not a
  judgment of conditions.` / `这是统计比较，不替处境下判断。`) is the deck's only string
  that says so, and no other item claims it. Rendering it next to the count also keeps the
  zero case honest, which is item 3's own subject.
- `nodata` (`NO DATA` / `无数据`), the `statusOk`/`warnH`/`warnB`/`alarmDarkH`/`alarmDarkB`/
  `disruptH`/`disruptB` status-banner strings, `feelHint`/`feelGapNote`/`levelBody`, the
  `cov*` block, `notCounted`, `alarmTag`/`alarmingWhen`, `benignShift`/`calibrating`, the
  inline `trembling`/`颤抖` pill text and the `②`/`changeKicker`-adjacent kickers are left
  untouched: they are owned by items 4, 6, 7 and 8, and changing them here would pre-empt
  those items.

**Files changed.**

- `docs/index.html` — `statusLabel` in both locales is the deck's six-state table;
  `darkNote`, `closedNote`, `blindNote`, `calibNote`, `whichNote` → `whichLines` and
  `runNote` carry the deck's sentences; `countQualifying` added to both locales and
  rendered into a new `#count-qualifying` element under the count block; one new
  `.count-qualifying` CSS rule; the render call site uses `whichLines`. No scoring value,
  record column or tier membership moved.
- `tests/render_smoke.js` — new T28 block (six status labels, seven qualifier sentences,
  `whichNote` removal, the calm-word scan over the rendered zero-count block, the
  qualifying copy) and the T21 gap-chip rebound to the new `dark` label.
- `tests/lint_public_surface.py` — the `statusLabel` key set is bound to all six normalize
  statuses; the unused `NON_SCORING_STATUSES` constant is removed; the module docstring's
  status paragraph now describes the six-label contract.

**Verification results (after implementation).** Gates run with
`PATH=/Users/wangyu/.pyenv/shims:$PATH` (pytest 9.0.2), the interpreter iterations 1–2
used.

- gate tier `python -m pytest tests/ -q` — `415 passed, 126 subtests passed in 1.04s`
- lint tier `python -m unittest discover tests -p "lint_*.py"` — `Ran 69 tests … OK`
- forbidden literal `python tests/lint_no_forbidden_literal.py` — `Ran 3 tests … OK`
- audit tier `python -m unittest discover tests -p "audit_*.py"` — `Ran 28 tests … OK`
- replay `python tools/replay.py --check` — exit 0, `TOTAL 1439 0`, divergence 0 since
  `STABLE_SINCE` 2026-09-09
- pending `python tools/pending.py --check` — `OK — 6 tagged pending item(s), 0 overdue, 0 unparseable`
- render smoke `node tests/render_smoke.js` — `render OK in both languages; no runtime errors,
  no undefined/NaN`; label tail `条读数偏离各自近期记录 · 3 条线没有读数 · 4 条线中有 4 条的近期参照仍在积累`
- annotations mirror `cmp data/annotations.csv docs/data/annotations.csv` — `cmp: identical`

The zero-count scan reads the real rendered block (kicker, prefix, numerator, separator,
denominator, label and every qualifier span) for the four-line three-dark fixture in both
languages, not the `T` object in isolation. `docs/index.html` still has exactly one
`innerHTML`, inside `setMarkup` (lint `TestMarkupHasOneAuditedSink` passes), and no new
first-person prose was added.

**Notes for the next iteration.**

- Item 4's step "delete the `changeKicker` key and its DOM assignment" was already done by
  item 2; `#count-kicker` must keep rendering `countTitle`. The `②` `levelKicker` and
  `levelKicker`'s `#level-kicker` assignment are still present and are item 4 material.
- Item 4 still owns `title`/`tag`, `promise`, `asOf`/`asof`, `nodata`, `more`, `dirUp`/
  `dirDown`, `last`, `noCollect`, `source`, the `range_*` keys, `covTitle`/`covLead`/
  `covLead2`/`covTail`/`covMore`/`covBlind`, `notCounted` and the whole limits section.
- Item 6 owns `countColor`, the four-way status/marker colouring, and the inline
  `trembling`/`颤抖` pill text; item 7 owns the `alarm:` field plus `alarmTag`/
  `alarmingWhen` and `render.py`'s chart title; item 8's guard will still find `alarm`,
  `共振`, `平静` and layer wording in `feelHint`, `feelGapNote`, `levelTitle`/`levelBody`,
  `covLead`/`covBlind`, `notCounted`, `footer`'s neighbours and the `②` kickers.
- `statusLabel.scoring` will render nowhere until a card treatment claims it (item 6 or
  later); the lint binding is what keeps it from silently disappearing.

## Iteration 4 — item 4 (functional): the numbered two-probe framing is deleted and the structural copy describes a record

**Chosen because** `.ralph/plan.md` ranks copy and structure before style, names the
`declared_dir` field as the third field later items reference, and this item is the last
unfinished copy item that other items do not depend on for field names. It also clears the
probe vocabulary out of the blocks items 5–8 must edit. No item is hard-blocked; the
ledger held iterations 1–3, all green.

**Entry state measured.** Gate 415 passed; lint 69 OK; forbidden-literal 3 OK; audit 28 OK;
`replay --check` exit 0 (1439 rows since `STABLE_SINCE`, divergence 0); `pending --check`
6 tagged / 0 overdue; render smoke OK; annotations mirror identical.

**Test-first, failure recorded.** `tests/render_smoke.js` gained a T29 block before any
copy changed: it binds the deck's structural strings in both languages (title, promise,
as-of line, gap word, detail link, direction words, four range labels, coverage sentence,
limits title/body/flights, fixed-reference title/body/as-of, not-counted line, watchlist
heading and day counts), requires the retired keys `tag`, `changeKicker`, `levelKicker` and
`asof` to be absent, and scans the rendered page plus every detail panel for the circled
kickers `①`/`②`/`③` and the words `probe`/`探针`. Run on the unmodified page: exit 1 with
71 `structure(...)` failures, including `structure(en): the retired key "tag" is still
declared`, `structure(en): direction words are ["up","down"], expected the deck's
["rising","falling"]`, `structure(en): document title is undefined, expected the deck's
"tremor — readings, kept in view"`, `structure(en): the fixed-reference heading is "② the
level probe · what is stuck broken now"`, `structure(en): the coverage panel does not carry
the deck's limitsTitle "Limits of this record"`, and `structure(en): the reader surface
still carries probe wording "②"` / `"probe"` plus the ZH `"探针"` counterpart.

**Test rebind (same commit, not weakened).** `tests/audit_record.py`'s flights-reach audit
bound twelve phrases from the retired `covBlind` paragraph (`"about 44% and 34%"`,
`"~1.2z"`, `"44% 与 34%"`, …). Those are three shares and three z figures that the new
`limitsFlights` copy still states, so the phrase list was rebound to the deck's wording with
each of the four shares and each of the three z figures bound separately in both languages
(`"US East about 44%"`, `"US West 34%"`, `"W/C Europe 13%"`, `"Japan/E Asia 9%"`,
`"about 1.2z"`, `"about 0.8z"`, `"about 2.0z"`, and the ZH equivalents). The two
`covBlind` docstring/message references were renamed to `limitsFlights`. The binding is
stricter than the old combined phrases, not looser.

**Decisions (conservative, reversible).**

- `title` and `promise` replace `tag`. The static `<title>` is the deck's EN title; `render()`
  sets `document.title` per language and `#tag` renders `promise`. The `#tag` element id
  keeps its spelling (internal identifier).
- The `②` kicker string is deleted and `#level-kicker` now renders `referenceTitle`, exactly
  as `#count-kicker` renders `countTitle` since item 2. The deck deletes `levelKicker`
  outright; the block still needs a heading, and the deck supplies one.
- `levelTitle`/`levelBody`/`levelAsof` become `referenceTitle`/`referenceBody`/
  `referenceAsOf` (deck text verbatim). The deck's `referenceItem` is NOT rendered: it needs
  `latest {value} / reference {reference} / {days}`, while `docs/data/stuck.csv` carries only
  `pct` and `since`. Inventing a reference value or a days template would state figures the
  served record does not contain, so the block keeps its count label, reworded to
  `reading(s) below its/their fixed reference(s)` / `N 条读数长期低于既定参照`. The deck's
  demotion of this block below the history chart is a DOM move that no item in this bundle
  claims; the block stays where it is.
- `covTitle`/`covLead`/`covLead2`/`covTail`/`covBlind` are replaced by `coverage` (a
  function of the `watches`-derived region list), `covMore`, `limitsTitle`, `limitsBody` and
  `limitsFlights`. The limits copy renders in the coverage panel for now; item 5 owns
  putting it inline as visible body text below the collected records. `covBlind`'s
  cadence-gap prose (`cnh_cny` weekend session) is not in the deck and is dropped with the
  rest of that paragraph; `limitsFlights` carries the measured sampling-weight facts.
- `watchTitle` and `watchDays` were migrated although item 4 lists only `notCounted`: the
  watchlist heading is where a reader learns which collected lines never enter the count,
  and the old heading claimed those lines are "not displayed", which contradicted the list
  directly below it. `watchDays` keeps the deck's `{n} recorded days` template with the
  English `(s)` hint resolved to grammatical number, the same treatment item 3 used.
- The deck supplies no replacement string for `noCollect` (`no collection this day` /
  `当天未采集`), so it is unchanged; `last` keeps its shape with the label word aligned to
  the deck's `latest`. `source` (`Source` / `数据来源`) and `countQ` → `countQuestion` were
  already deck strings.
- `panelTitle`/`panelHint`, `statusOk`/`awaiting`/`warn*`/`alarmDark*`/`disrupt*`,
  `annoTitle`/`annoBody`, `feel*`, `alarmTag`/`alarmingWhen`, `benignShift`/`calibrating`,
  `verdictLabel`, `leanNote` and `footer` were left untouched: items 6, 7 and 8 own them.
  The `<title>` element now carries no world-question framing, and the two probe-kicker
  comments in the render path were reworded to describe the reference block.

**Files changed.**

- `docs/index.html` — `<title>`; both `T` locales: `tag` → `title` + `promise`,
  `levelKicker` deleted, `asof` → `asOf`, `nodata`/`more`/`dirUp`/`dirDown`/`range_*`/
  `notCounted`/`watchTitle`/`watchDays`/`last` migrated, `levelHead` reworded,
  `levelTitle`/`levelBody`/`levelAsof` → `referenceTitle`/`referenceBody`/`referenceAsOf`,
  `cov*` → `coverage`/`covMore`/`limitsTitle`/`limitsBody`/`limitsFlights`; `render()` sets
  `document.title` and the promise, uses `asOf`, renders the reference heading and the
  deck's coverage sentence; `covModal` renders the limits block; `levelModal` renders the
  reference rule. No scoring value, record column or tier membership moved.
- `tests/render_smoke.js` — new T29 block (structural copy, retired keys, circled-kicker
  and probe-word scan over the rendered page and every detail panel, gap word, detail
  link, limits panel, reference panel, watchlist not-counted line).
- `tests/audit_record.py` — flights-reach phrase list rebound to `limitsFlights` copy; two
  `covBlind` docstring/message references renamed.

**Verification results (after implementation).** Gates run with
`PATH=/Users/wangyu/.pyenv/shims:$PATH` (pytest 9.0.2), the interpreter iterations 1–3 used.

- gate tier `python -m pytest tests/ -q` — `415 passed, 126 subtests passed in 0.94s`
- lint tier `python -m unittest discover tests -p "lint_*.py"` — `Ran 69 tests … OK`
- forbidden literal `python tests/lint_no_forbidden_literal.py` — `Ran 3 tests … OK`
- audit tier `python -m unittest discover tests -p "audit_*.py"` — `Ran 28 tests … OK`
- replay `python tools/replay.py --check` — exit 0, `TOTAL 1439 0 0`, divergence 0 since
  `STABLE_SINCE` 2026-09-09
- pending `python tools/pending.py --check` — `OK — 6 tagged pending item(s), 0 overdue, 0 unparseable`
- render smoke `node tests/render_smoke.js` — `render OK in both languages; no runtime errors,
  no undefined/NaN`; coverage `当前记录范围：… 。本页展示的是这些记录。范围与限度 ↓`
- annotations mirror `cmp data/annotations.csv docs/data/annotations.csv` — `cmp: identical`

`grep` over `docs/index.html` finds no `①`/`②`/`③` and no `probe`/`探针` anywhere in the
file, source comments included. `docs/index.html` still has exactly one `innerHTML`, inside
`setMarkup` (lint `TestMarkupHasOneAuditedSink` passes), and no first-person prose was
added.

**Notes for the next iteration.**

- Item 5 owns making `limitsTitle`/`limitsBody`/`limitsFlights` visible inline below the
  collected records. All three render today only in the panel opened by `covMore`; the
  copy itself is already the deck's, so item 5 is placement plus the visibility assertion.
  `covMore`'s `↓` should then scroll to that section rather than open the panel.
- Item 6 owns `countColor`, the four-way status/marker colouring and the inline
  `trembling`/`颤抖` pill text.
- Item 7 owns the `alarm:` field, `alarmTag`/`alarmingWhen` and `render.py`'s chart title.
  `dirUp`/`dirDown` now read `rising`/`falling`, so `alarmTag` renders
  `alarming when rising` until item 7 renames it.
- Item 8's guard will still find `alarm` in `alarmTag`/`alarmingWhen`/`statusLabel`'s
  neighbours, `calm`/`平静` in `feelHint`/`feelGapNote`, `共振` nowhere (the last copy use
  went with `notCounted`), and the layer wording in nothing migrated here; `footer` and
  `panelTitle`/`panelHint` remain the unclaimed deck keys.
- The reference count head uses `levelHead` with the number kept in `#level-n`, matching the
  daily count block; the deck has no head template for that block.

## Iteration 5 — item 5 (functional): the four limitations are visible page text

**Chosen because** item 5 is the last unfinished copy-and-structure item, and
`.ralph/plan.md` ranks copy and structure before style (item 6) and the guard (item 8).
It also finishes the placement that item 4 left open: `limitsTitle`/`limitsBody`/
`limitsFlights` existed only inside the panel opened by `covMore`, so the four
limitations were not visible page text. No item is hard-blocked; the ledger held
iterations 1–4, all green.

**Entry state measured.** Gate 415 passed; lint 69 OK; forbidden-literal 3 OK; audit 28 OK;
`replay --check` exit 0 (1439 rows since `STABLE_SINCE`, divergence 0); `pending --check`
6 tagged / 0 overdue; render smoke OK; annotations mirror identical.

**Test-first, failures recorded.** Two existing surfaces were rebound and one block was
added before any page copy moved:

- `tests/render_smoke.js` (new T30 block): the inline limits section must sit in the page
  body between `#watchlist` and `#footer` (and before the modal markup), must not be
  hidden after a plain `render()`, and its rendered text must carry the deck's title, one
  marker sentence per limitation (rolling reference absorbs long-running change; roster
  selected under written assumptions; other daily records never counted; no communications
  domain so worldwide connectivity reads zero) and the measured flights sampling fact, in
  both languages, with no panel opened. Run on the unmodified page: 20 failures, including
  `limits: the inline section is not in the page body between the collected records (9660)
  and the footer (9698), before the modal (9728): -1`, `limits(en): limitation 1 is not
  visible page text ("The rolling comparison looks to recent history; …")` through
  limitation 4, `limits(en): the inline section does not carry the measured flights sampling
  fact …`, and the ZH counterparts.
- `tests/render_smoke.js` T29 rebound: its `#covmore` assertion previously clicked the link
  and read the limits copy out of `#modal-body`. It now sets `#modal.hidden = true`, clicks
  the link, requires the modal to stay closed, and reads the copy out of `#limits`. Run
  before the page change: `structure(en): the scope link opened a panel instead of scrolling
  to the inline limits section` plus the three missing inline copies, repeated in ZH (8
  failures).
- `tests/render_smoke.js` harness: `covModal` was removed from the eval export, the
  destructure, the two modal exercise loops and T29's reader-surface scan, because the
  builder is deleted below; the fake node gained a `scrollIntoView() {}` stub so the real
  scroll call the page makes is legal in the harness.

**Decisions (conservative, reversible).**

- The limits copy is rendered by `render()` into a static `<section class="panel limits"
  id="limits">` placed after `#watchlist` and before `#footer`, matching the deck's reading
  order (scope and limits after the other records) and item 5's "below the collected
  records". `hidden` is cleared unconditionally, so the section does not depend on the
  watchlist existing.
- The section renders the deck's `limitsBody` verbatim as one paragraph — it already
  carries the four limitations as four sentences, which is how the deck specifies them —
  and `limitsFlights` as its own paragraph in the same section. No copy was reworded or
  split, so `tests/audit_record.py`'s per-region share and z bindings still match.
- The region list that used to live only in the panel is kept, in the same section,
  derived from each tier-1 line's `watches` field. Without it the "Scope" half of the
  `covMore` label would name nothing; it is derived, so a tier swap cannot make it stale
  (the comment above `LINES` was updated to say so).
- `covModal` and its `openModal` wiring are deleted. The deck's architecture says the scope
  link scrolls to the always-visible section, so keeping a second, hidden copy of the same
  prose would be dead code. `#covmore` now calls `scrollIntoView` on the section and opens
  no panel; T29 asserts the modal stays closed.
- The section reuses the existing `.panel` card style with four small `.limits` rules, so
  it reads as body content, not a modal. No colour was introduced.

**Files changed.**

- `docs/index.html` — new `<section class="panel limits" id="limits">` between `#watchlist`
  and `#footer`; `.limits` CSS rules (margins, list and paragraph treatment); `covModal`
  deleted; `#covmore` handler scrolls to the section; `render()` fills the section with
  the watches-derived region list, `limitsTitle`, `limitsBody` and `limitsFlights`; the
  comment above `LINES` now names the section. One `innerHTML` remains, inside `setMarkup`.
- `tests/render_smoke.js` — new T30 block (placement, visibility, title, four limitation
  markers, flights fact, no-panel); T29's `#covmore` assertion rebound to the inline section
  and the closed-modal check; `covModal` removed from the export/loops/surface scan; a
  `scrollIntoView()` stub added to the fake node.

**Verification results (after implementation).** Gates run with
`PATH=/Users/wangyu/.pyenv/shims:$PATH` (pytest 9.0.2), the interpreter iterations 1–4 used.

- gate tier `python -m pytest tests/ -q` — `415 passed, 126 subtests passed in 0.98s`
- lint tier `python -m unittest discover tests -p "lint_*.py"` — `Ran 69 tests … OK`
- forbidden literal `python tests/lint_no_forbidden_literal.py` — `Ran 3 tests … OK`
- audit tier `python -m unittest discover tests -p "audit_*.py"` — `Ran 28 tests … OK`
- replay `python tools/replay.py --check` — exit 0, `TOTAL 1439 0 0`, divergence 0 since
  `STABLE_SINCE` 2026-09-09
- pending `python tools/pending.py --check` — `OK — 6 tagged pending item(s), 0 overdue, 0 unparseable`
- render smoke `node tests/render_smoke.js` — `render OK in both languages; no runtime
  errors, no undefined/NaN`; coverage line unchanged and still ends with `范围与限度 ↓`
- annotations mirror `cmp data/annotations.csv docs/data/annotations.csv` — `cmp: identical`

`grep` over `docs/index.html` finds no `covModal` left, one `innerHTML` (the `setMarkup`
line), and no `①`/`②`/`③` or `probe`/`探针`. The section's four limitation sentences are
the deck's `limitsBody` verbatim in both languages, and T30 reads them from the rendered
`#limits` node after a plain `render()` with no modal click.

**Notes for the next iteration.**

- Item 6 owns `countColor`, the four-way status/marker colouring and the inline
  `trembling`/`颤抖` pill text; the new `.limits` block introduces no colour, so nothing
  there is left for it.
- Item 7 owns the `alarm:` field, `alarmTag`/`alarmingWhen` and `render.py`'s chart title.
- Item 8's guard will still find `alarm` in `alarmTag`/`alarmingWhen` and the status
  banner keys, `calm`/`平静` in `feelHint`/`feelGapNote`, and layer wording in nothing
  migrated here. The `footer` and `panelTitle`/`panelHint` deck keys remain unclaimed by
  any item in this bundle.
- The smoke harness now depends on `scrollIntoView` existing on a node; any future handler
  that calls another real-DOM method needs the stub extended the same way.

## Iteration 6 — item 7 (functional): the per-line direction is a recorded hypothesis under a neutral field

**Chosen because** `.ralph/plan.md` ranks copy and structure that other items reference
first, and names the `declared_dir` field as the third of the three fields later items
reference (`measures` was item 1, the headline label item 2). Items 1–5 are passing; item 6
(style and colour) depends on markers rather than on this field, while item 8's vocabulary
guard is the last-ranked class and needs the field name settled first. No item is
hard-blocked; the ledger held iterations 1–5, all green.

**Entry state measured.** Gate 415 passed; lint 69 OK; forbidden-literal 3 OK; audit 28 OK;
`replay --check` exit 0 (1439 rows since `STABLE_SINCE`, divergence 0); `pending --check`
6 tagged / 0 overdue; render smoke OK; annotations mirror identical.

**Test-first, failures recorded.** Three assertions were added before any page copy moved:

- `tests/lint_registry.py` (new `_docs_lines_block()` helper plus two tests):
  `test_every_docs_line_declares_a_direction_under_the_neutral_field_name` requires a
  `declared_dir:"up"|"down"` field on every `const LINES` entry, and
  `test_docs_lines_carry_no_alarm_field` requires the block to declare no `alarm:` field.
  Run on the unmodified page: 8 lint failures, including
  `Lists differ: ['capital_premium', 'chokepoint_breadth', … 'vix'] != [] : docs/index.html
  const LINES line(s) declare no declared_dir field: [24 ids]`,
  `Lists differ: ['alarm:', 'alarm:', …] != []`, and the parse-dependent tests reporting
  `docs/index.html's const LINES parsed to 0 entries but collect.LINES resolves to 24`.
- `tests/lint_public_surface.py` (new `TestChartTitlesStateTheRecordedDirection`): no
  `alarming when` anywhere in `render.py`, and the `ax.set_title(...)` call that
  interpolates `ANOMALY_DIRECTION` must state the recorded comparison direction. Run before
  the change: `AssertionError: 'alarming when' unexpectedly found in … render.py still
  titles a per-line chart 'alarming when …'`.
- `tests/render_smoke.js` (new T31 block): every line's detail and every reading card must
  carry the deck's direction sentence in both languages, the `alarm` field must be gone, and
  `alarmTag`/`alarmingWhen` must not be declared. Run on the unmodified page: `exit 1` with
  108 `direction(...)` failures, e.g. `direction(en): LINES entry flights still declares an
  'alarm' field; the recorded direction belongs under declared_dir` and
  `direction(en): LINES entry flights declares declared_dir undefined, expected "up" or
  "down"` (two per line per language).

**Decisions (conservative, reversible).**

- One `directionLabel` key per locale carries the deck's full sentence
  (`Comparison direction noted when this series was selected: {direction}` /
  `比较方向（建线时记下）：{direction}`), replacing both `alarmingWhen` and `alarmTag`. The
  deck's migration row maps both retired keys to that one key, and the page has three render
  sites for a direction: the line detail's tag row (the "legend" of the detail), the tier-2
  detail's tag row, and the reading card's subtitle (what a reader sees on the card). All
  three render the same sentence, so no shorter, invented copy was introduced. The card
  subtitle now wraps on narrow screens; no CSS changed.
- `render.py` has no locale: the per-line chart title uses the deck's EN sentence with
  `{mod.ANOMALY_DIRECTION}` interpolated. The overview PNG title
  (`Resonance — lines trembling per day`) is untouched — no item in this bundle claims it,
  and changing the source without regenerating `charts/` is out of scope (that directory is
  the nightly job's output).
- `_collect_registry()` and `_docs_registry()` now both key the comparison on
  `declared_dir`, so the agreement test still compares the dashboard field to each fetcher's
  unchanged `ANOMALY_DIRECTION`, and the test is named
  `test_docs_and_collect_agree_on_declared_direction_and_tier`.
- `tremblingRunLength`'s parameter is renamed `declaredDir` (a pure internal rename). Its
  direction-sensitive semantics are unchanged: the direction-free run is part of the
  separate scoring phase that `.ralph/plan.md` scopes out.
- Two pre-existing type-narrowing defects in `tests/lint_registry.py` were fixed while the
  file was open (an `ast.List` guard in `_collect_lines_aliases`, and an
  `assert header is not None` after `assertIsNotNone`). Neither changes an assertion.
- The retired `alarmTag` notion survives nowhere as a T key; `T.en`/`T.zh` stay key-for-key
  identical (both lose two keys, both gain one).
- Residual `alarm` spelling in `docs/index.html` is exactly the encumbrance the plan
  permits or assigns elsewhere: the `--alarm` CSS variable and `.sysstatus.alarm` class,
  the `alarmDarkH`/`alarmDarkB` status-banner T keys (deck row: `manyDark`/`disruption`,
  item 8's vocabulary work), `countColor` and the `trembleState` state name (item 6), and the
  feel-chart block (`feelHint`, the `feel z` axis title) that no item claims.

**Files changed.**

- `docs/index.html` — 24 `alarm:` fields renamed `declared_dir:`; all 8 `L.alarm` reads
  renamed; `alarmingWhen` and `alarmTag` deleted from both locales and `directionLabel`
  added; `lineModal`, `openTier2Modal` and the card subtitle render it; `tremblingRunLength`
  parameter and its comment reworded. No scoring value, record column or tier membership
  moved.
- `render.py` — per-line chart title states the recorded comparison direction.
- `tests/lint_registry.py` — `_docs_lines_block()` helper, `declared_dir` regex group, both
  registry dicts keyed `declared_dir`, agreement test renamed, two new field tests, and the
  two type narrowings.
- `tests/lint_public_surface.py` — `RENDER` path, `TestChartTitlesStateTheRecordedDirection`,
  and the module docstring's fourth checked surface.
- `tests/render_smoke.js` — T31 block; the headline fixture's direction read rebound from
  `L.alarm` to `L.declared_dir` (the only existing fixture that bound the renamed field).

**Verification results (after implementation).** Gates run with
`PATH=/Users/wangyu/.pyenv/shims:$PATH` (pytest 9.0.2), the interpreter iterations 1–5 used.

- gate tier `python -m pytest tests/ -q` — `415 passed, 126 subtests passed in 1.00s`
- lint tier `python -m unittest discover tests -p "lint_*.py"` — `Ran 72 tests … OK`
- forbidden literal `python tests/lint_no_forbidden_literal.py` — `Ran 3 tests … OK`
- audit tier `python -m unittest discover tests -p "audit_*.py"` — `Ran 28 tests … OK`
- replay `python tools/replay.py --check` — exit 0, `TOTAL 1439 0 0`, divergence 0 since
  `STABLE_SINCE` 2026-09-09
- pending `python tools/pending.py --check` — `OK — 6 tagged pending item(s), 0 overdue, 0 unparseable`
- render smoke `node tests/render_smoke.js` — `render OK in both languages; no runtime errors,
  no undefined/NaN`; headline `2 / 4`
- annotations mirror `cmp data/annotations.csv docs/data/annotations.csv` — `cmp: identical`

Rendered detail checked by hand for `flights` in both languages: `EN: Airspace · Aircraft
airborne · Comparison direction noted when this series was selected: falling · Source:
Community ADS-B, 4 busy regions · Measures Aircraft reported airborne across …`; the ZH
counterpart reads `比较方向（建线时记下）：下降`. All 24 entries carry `declared_dir`, no entry
carries `alarm`, and neither locale declares `alarmTag` or `alarmingWhen`. `docs/index.html`
still has exactly one `innerHTML`, inside `setMarkup`, and the chart title change is a source
change only: `charts/` was not regenerated or touched (nightly output).

**Notes for the next iteration.**

- Item 6 (style and colour) now has the field name it needs: `countColor`, the four-way
  status/marker colouring, the `trembleState` "alarm"/"benign" split, `.pill.trembling`
  and the adjudicated hatch are untouched here.
- Item 8's guard should treat `alarmDarkH`/`alarmDarkB` (deck row: `manyDark`/`disruption`),
  `feelHint`/`feelGapNote`, `notCounted`'s neighbours, `panelTitle`/`panelHint` and `footer`
  as residual strings to migrate; the `alarm` CSS variable and `.sysstatus.alarm` class must
  stay out of the scan (the plan exempts CSS class names and internal identifiers).
- The feel chart (`feelTitle`/`feelHint`/`feelGapNote`/`feelBars`/`feelchart`) and its
  `feel z (toward alarm)` / `感觉 z（报警方向）` axis title remain, with `data/leans.csv`
  consumption, because no item in this bundle claims their deletion. They are the largest
  remaining source of alarm vocabulary on the public page.
- `render.py`'s overview title still says `Resonance`, and the two per-line titles will only
  change in the committed PNGs at the next nightly render; nothing in the gate tier renders
  charts.

**Analyzer note.** The editor-side analyzer reports four unresolved imports in `render.py`
(`matplotlib`, `matplotlib.pyplot`, `matplotlib.dates`, `PIL`, lines 10–15). Verified and
left unchanged: those imports predate this iteration (`git diff render.py` changes only the
title call), `python -c "import render"` succeeds under the gate interpreter
(`matplotlib 3.9.0`, `pillow 12.2.0`), and removing them to silence the finding would break
the module's only job. The report is a package-resolution mismatch in the analyzer's own
interpreter, not a defect in the file.

## Iteration 7 — item 6 (functional): one neutral reading treatment

**Chosen because** item 6 is the only unfinished style item and `.ralph/plan.md` ranks style
after copy and structure (items 1–5 and 7 pass) and before the vocabulary guard (item 8).
No item is hard-blocked; the ledger held iterations 1–6, all green.

**Entry state measured.** Gate 415 passed; lint 72 OK; forbidden-literal 3 OK; audit 28 OK;
`replay --check` exit 0 (1439 rows since `STABLE_SINCE`, divergence 0); `pending --check`
6 tagged / 0 overdue; render smoke OK; annotations mirror identical.

**Test-first, failures recorded.** `tests/lint_public_surface.py` gained
`TestNeutralReadingTreatment` (four tests) before any page change. Run on the unmodified
page: `Ran 76 tests in 0.753s` / `FAILED (failures=4)`:

- `test_count_color_is_gone` — `countColor` is still defined at `docs/index.html:593`.
- `test_no_severity_hue_remains_in_the_stylesheet` — the stylesheet still carries
  `--calm/--amber/--orange/--alarm`, `#3fb27f`, `#e0a83d`, `#ff6b6b` and the matching
  `rgba(...)` triples.
- `test_the_count_and_reference_numbers_use_the_neutral_reading_mark` — `.count .n` has no
  `color:var(--reading-mark)`, and `#count-n` / `#level-n` are painted from JS with
  `el.style.color=countColor(...)`.
- `test_the_unusual_marker_does_not_hatch` — `.pill.trembling.adjudicated`, the emitted
  `" adjudicated"` class, `ptColor`, and the red `rgba(214,69,69,.45)` threshold remain.

The smoke rebinds and the new T32 were then run against the pre-change page
(`git show HEAD:docs/index.html` swapped in, then restored): exit 1 with 26 failures. Each
language reported `adj`/`adj2` failures on both firing cards ("does not carry the one
neutral unusual marker undefined", "still carries an adjudication-specific marker class")
and seven `neutral(...)` failures: the retired `benignShift` key is still declared, neither
direction carries the neutral marker, the against-direction card still carries the
direction-specific marker, the rendered page still carries "benign shift" / "良性异动",
and `#count-n` / `#level-n` are painted `var(--orange)` / `var(--amber)`.

**Decisions (conservative, reversible).**

- One tone: `--reading-mark:#c7ccd6` (the deck's value) replaces the four severity
  variables, which are deleted from `:root` (unused after the change; the plan permits
  keeping their spelling, not requiring it). `.count .n` applies the tone to both
  `#count-n` and `#level-n`; size (54px / 44px) and weight (700 / 600) carry emphasis, and
  neither element is painted from JS.
- CSS class NAMES kept: `sysstatus.ok/.warn/.alarm`, `inst dark` and `pill trembling` stay
  in markup as internal state names, per the plan's "do not rename CSS class names in this
  bundle". Their colour rules are deleted (`.sysstatus` variants, `.inst.dark`), so every
  banner and card renders the base neutral panel and a status is read from its sentence.
- Reading cards: the `--dot` series accent and its JS `setProperty` are removed;
  `.inst .nodata`, `.wl-blind`, `.wl-gap`, `.count .darknote` and `.count .pairnote` move to
  the neutral tone. `L.color` now reaches only chart datasets.
- Unusual marker: `.pill.trembling.adjudicated` and its hatch are deleted together with the
  card-level adjudication/lean lookup; the marker is one `<span class="pill trembling">`
  in either direction. The deck's `unusualPill` (`Unusual` / `偏离近期记录`) replaces the
  inline `trembling` / `颤抖` literal and `benignShift` / `良性异动` is deleted, because the
  deck's migration row for these exact surfaces is "one neutral `unusual` marker in both
  directions" and keeping "benign shift" would leave a favourable/unfavourable copy split
  inside that one treatment. This is the item's one copy change; no other item in the
  bundle names the key. The class spelling stays `trembling` (renaming a CSS class is out
  of scope).
- Chart: `trembleState` returns one `unusual` state; `ptColor` is deleted and the tremble
  point uses the series' own `L.color` with the existing larger radius. The ±3 threshold
  guide moves from alarm red to neutral ink, and the tier-2 mini chart drops its red/green
  point map for the series colour with the same radius emphasis.
- The feel chart (`feelTitle`, `feelHint`, `feelGapNote`, `feelBars`, red bars, amber
  divergence columns, both axis titles) is untouched: no item in this bundle claims it, and
  its colours are chart-trace colours rather than the count/card/status/marker surfaces
  item 6 names. It remains the one place whose copy still carries `alarm` / `报警` and
  `calm` / `平静` (item 8's subject).

**Files changed.**

- `docs/index.html` — `:root` (`--reading-mark`, four severity variables removed);
  `.count .n` / `.darknote` / `.pairnote`, `.sysstatus` colour variants, `.inst` accent and
  `.inst.dark`, `.inst .nodata`, `.pill.trembling` plus hatch rule and `.pill.benign`,
  `.wl-blind` / `.wl-gap`; `unusualPill` added and `benignShift` deleted in both locales;
  `countColor` and its two call sites deleted; `chip.style.setProperty("--dot",…)` deleted;
  `trembleState` reduced to one state and `ptColor` deleted; card pill one neutral marker;
  chart point colours, threshold colour and tier-2 mini-chart point colours; the
  `adjudication()` reader comment.
- `tests/lint_public_surface.py` — `SEVERITY_TOKENS`, `_STYLE_BLOCK`,
  `_COUNT_NUMBER_RULE`, `_docs_style_block()`, `TestNeutralReadingTreatment`; the module
  docstring now lists five checks and states the style-vs-vocabulary scope.
- `tests/render_smoke.js` — T22/T23 rebound from the retired hatch class to the neutral
  marker (both firing cards render `class="pill trembling">unusualPill` and no card carries
  `adjudicated`; the calm card carries no unusual marker); new T32 (one marker in both
  directions, retired `benignShift`, neither number painted in JS).

**Verification results (after implementation).** Gates run with
`PATH=/Users/wangyu/.pyenv/shims:$PATH` (pytest 9.0.2), the interpreter iterations 1–6 used.

- gate tier `python -m pytest tests/ -q` — `415 passed, 126 subtests passed in 0.90s`
- lint tier `python -m unittest discover tests -p "lint_*.py"` — `Ran 76 tests in 0.752s … OK`
  (was 72)
- forbidden literal `python tests/lint_no_forbidden_literal.py` — `Ran 3 tests … OK`
- audit tier `python -m unittest discover tests -p "audit_*.py"` — `Ran 28 tests … OK`
- replay `python tools/replay.py --check` — exit 0, `TOTAL 1439 0 0`, divergence 0 since
  `STABLE_SINCE` 2026-09-09
- pending `python tools/pending.py --check` — `OK — 6 tagged pending item(s), 0 overdue, 0 unparseable`
- render smoke `node tests/render_smoke.js` — `render OK in both languages; no runtime
  errors, no undefined/NaN`; headline `2 / 4`
- annotations mirror `cmp data/annotations.csv docs/data/annotations.csv` — `cmp: identical`

`grep` over `docs/index.html` finds no `countColor`, no `ptColor`, no `--dot`, no
`--calm`/`--amber`/`--orange`/`--alarm`, no `.pill.trembling.adjudicated` and no emitted
`" adjudicated"` class. One `innerHTML` code line remains, inside `setMarkup` (lint
`TestMarkupHasOneAuditedSink` passes), and both record-derived sinks still call `esc()`.
The rendered marker was checked by hand in both languages: a card trembling in its
recorded direction and a card trembling against it both read `Unusual` / `偏离近期记录`
in the same neutral outline.

**Notes for the next iteration.**

- Item 8 is the only item left: rewrite the README opening and add the vocabulary guard.
  The guard must scan user-visible VALUES, not keys: `alarmDarkH` / `alarmDarkB` are
  internal key names whose values carry no banned word, so a whole-`const T`-block
  substring scan would trip on them and must not be written that way.
- Residual banned words in user-visible values today, all in the unclaimed feel chart: EN
  `feelHint` ("alarming direction", "read calm"), EN `feelGapNote` ("measured calm"), ZH
  `feelHint` ("报警方向", "读数平静"), ZH `feelGapNote` ("测量平静"). No `resonance` / `共振`
  and no layer vocabulary remain in the T locale values or in `LINES`.
- README still carries the world-disorder question plus alarm and resonance prose; item 8
  rewrites it. The deck's replacement copy for the feel chart is deletion, which no item
  claims, so item 8 has to either reword those two strings or drop the chart's hint copy
  under the guard.
- The feel chart's red bars `rgba(214,69,69,.55)` and amber gap columns
  `rgba(224,168,61,.28)` remain in JS, outside the stylesheet scope the new lint binds.
- Still unmigrated and unclaimed after this bundle's items: `statusLabel.scoring`,
  `verdictLabel`, `panelTitle` ("Tension lines"), `panelHint` ("trembling threshold"),
  `statusOk` / `awaiting` / `warnH` / `warnB` / `alarmDarkH` / `alarmDarkB` / `disruptH` /
  `disruptB`, `annoTitle`, `feelBars`, `footer`.

**Analyzer note.** No new analyzer findings: the four `render.py` import findings recorded
in iteration 6 are unchanged and still a package-resolution mismatch in the analyzer's own
interpreter (the gate interpreter imports `render` cleanly).

## Iteration 8 — item 8 (docs): README and public copy pass the vocabulary guard

**Chosen because** item 8 is the only item left with `passes: false`, and
`.ralph/plan.md` ranks the guard last: it can only pass once the copy is clean, and items
1–7 (the `measures` field, the headline label, the status vocabulary, the structural copy,
the inline limits, the neutral treatment, `declared_dir`) are all passing. No item is
hard-blocked; the ledger held iterations 1–7, all green.

**Entry state measured.** Gate 415 passed / 126 subtests; lint 76 OK; forbidden-literal 3
OK; audit 28 OK; `replay --check` exit 0 (1439 rows since `STABLE_SINCE`, divergence 0);
`pending --check` 6 tagged / 0 overdue; render smoke OK; annotations mirror identical.

**Test-first, failures recorded.** `tests/lint_public_surface.py` gained the
`TestPublicCopyVocabulary` section before any copy changed (four tests, plus the
`BANNED_COPY_WORDS` / `_LAYER_VOCABULARY` constants, `_visible_copy`, `_line_of` and
`_banned_copy_hits`). Run on the unmodified page and README: `Ran 27 tests … FAILED
(failures=2)`:

- `test_locale_strings_carry_no_banned_vocabulary` — four offenders, exactly the feel
  chart's copy: `docs/index.html:460: ['alarm', 'calm']` (EN `feelHint`),
  `:461: ['calm']` (EN `feelGapNote`), `:525: ['报警', '平静']` (ZH `feelHint`),
  `:526: ['平静']` (ZH `feelGapNote`).
- `test_readme_prose_carries_no_banned_vocabulary` — `README.md: ['alarm', 'resonance',
  'calm']`.
- `test_line_metadata_carries_no_banned_vocabulary` and
  `test_the_guard_scans_visible_copy_only` passed on entry: `const LINES`' copy fields
  were already clean, and the corpus was already copy-only. They are the non-vacuity and
  scope bindings, not the failing evidence.

**Decisions (conservative, reversible).**

- The guard's corpus is exactly the item's enumeration: every double-quoted string VALUE
  in the `const T` block, each `const LINES` entry's `label`, `source`, `measures`,
  `watches` and `domain` values in both languages, and the whole README. `_visible_copy`
  skips a quoted literal immediately followed by `:` so `statusLabel`/`verdictLabel` keys
  are not read as copy; `unit` is left out because it is a measure word ("aircraft", "架").
- The corpus excludes CSS and code by construction, and
  `test_the_guard_scans_visible_copy_only` binds that: it asserts every surface is
  represented, then asserts `--reading-mark`, `.sysstatus`, `alarmDarkH`, `const LINES`
  and `<style>` are absent from the corpus, so a whole-file (or stylesheet) scan would go
  red. The section comment states the same scope, including why an unquoted key name such
  as `alarmDarkH` is an internal identifier while its VALUE is copy.
- `calm` / `平静` are banned outright rather than only in a narrow zero-state sense: on
  this page every use of the word read the absence of a departure as a state of the world,
  which is the claim the migration removed. The choice is stated on the constant.
- Backtick strings are deliberately not read: the only backtick spans inside the `const T`
  block are code comments naming internal values (`real`, `benign`), so a backtick scan
  would pull internal identifiers into the corpus and contradict the stated scope.
- Residual copy fixed in place: the four feel-chart strings above (`feelHint`,
  `feelGapNote` in both locales) keep their structure and their factual content, with the
  banned phrases replaced by the deck's vocabulary — "the comparison direction recorded
  when each feel line was selected" instead of "each line's alarming direction", "sat
  inside its own recent range" instead of "read calm", and the dropped "how disordered the
  world FEELS" clause replaced by the two series it named.
- The feel chart's hardcoded y2 axis title (`感觉 z（报警方向）` / `feel z (toward alarm)`)
  is visible page text outside the locale objects, so the guard does not cover it. It was
  reworded in place to `感觉 z（建线时记下的比较方向）` / `feel z (recorded comparison
  direction)` to satisfy the bundle's completion definition ("no alarm … vocabulary in
  visible strings"), and left out of the corpus rather than adding an invented T key: the
  deck deletes the feel chart and supplies no key for its axis. `render.py`'s overview PNG
  title still reads `Resonance — lines trembling per day`; no item claims it and `charts/`
  is the nightly job's output, so it was not touched.
- README rewrite: the deck's `promise` (EN, plus its ZH line in place of the old ZH
  sentence), `readmeCount` for the count description and `limitsBody` verbatim for the
  scope paragraph. The four-line list, the R28/R30 history parenthetical and the
  machine-checked claims table are unchanged; the table's `primary (tier-1) lines | 4` row
  still binds through `_tier1_line_count_claims`, and the new prose keeps one matching
  claim ("Four lines are primary today"). Removed: the one-question blockquote, the
  "guarded equilibria … a larger force has overpowered its guard" causal framing, the
  resonance/doom-score paragraph, the field-of-view paragraph with its "reads calm too"
  and "second headline / level layer" claims, and the metaphor clause at the end of the
  missing-data sentence. The fixed-reference list is described as a distinct measure with
  its own rule and lag, not as a second answer to the count.

**Files changed.**

- `README.md` — opening, count description, registry paragraph and scope paragraph
  rewritten to the deck's copy; Run it and Machine-checked claims sections unchanged.
- `docs/index.html` — `feelHint` and `feelGapNote` in both locales reworded; the feel
  chart's y2 axis title reworded. No scoring value, record column, tier membership or
  layout moved.
- `tests/lint_public_surface.py` — the `TestPublicCopyVocabulary` block (constants,
  `_JS_STRING`, `_JS_LINE_COPY_FIELD`, `_line_of`, `_visible_copy`, `_banned_copy_hits`,
  four tests) and the module docstring's sixth checked surface.

**Verification results (after implementation).** Gates run with
`PATH=/Users/wangyu/.pyenv/shims:$PATH` (pytest 9.0.2), the interpreter iterations 1–7 used.

- gate tier `python -m pytest tests/ -q` — `415 passed, 126 subtests passed in 0.94s`
- lint tier `python -m unittest discover tests -p "lint_*.py"` — `Ran 80 tests in 0.774s …
  OK` (was 76)
- forbidden literal `python tests/lint_no_forbidden_literal.py` — `Ran 3 tests … OK`
- audit tier `python -m unittest discover tests -p "audit_*.py"` — `Ran 28 tests in 2.473s
  … OK`
- replay `python tools/replay.py --check` — exit 0, `TOTAL 1439 0 0`, divergence 0 since
  `STABLE_SINCE` 2026-09-09
- pending `python tools/pending.py --check` — `OK — 6 tagged pending item(s), 0 overdue, 0
  unparseable`
- render smoke `node tests/render_smoke.js` — `render OK in both languages; no runtime
  errors, no undefined/NaN`; headline `2 / 4`
- annotations mirror `cmp data/annotations.csv docs/data/annotations.csv` — `cmp: identical`

`grep` over `docs/index.html` finds `alarm`/`calm` only in the exempt internals: the CSS
names (`--alarm` removed already; `.sysstatus.alarm` and its comment), the unquoted T keys
`alarmDarkH`/`alarmDarkB` (values clean), and code comments. `grep` over `README.md` finds
none of the banned tokens. `docs/index.html` still has exactly one `innerHTML` code line,
inside `setMarkup` (lint `TestMarkupHasOneAuditedSink` passes), and no first-person prose
was added.

**Notes for the next iteration.** Every item in `.ralph/items.json` now has `passes: true`
and every gate is green, so the bundle's completion definition is met on branch
`public-surface/migration` (nine commits, one per item; nothing pushed, nothing merged).
Deliberately still outside this bundle, all unclaimed by any item: the feel chart itself
(deleted by the deck but not by any item — it keeps `data/leans.csv`, its red bars, amber
gap columns and `feelBars` legend), `panelTitle`/`panelHint` ("Tension lines, normalized"),
the status-banner keys `statusOk`/`awaiting`/`warnH`/`warnB`/`alarmDarkH`/`alarmDarkB`/
`disruptH`/`disruptB`, `verdictLabel`, `annoTitle`, `footer`, and `render.py`'s overview
chart title. Removing the feel chart would also retire the guard's only reworded
T strings, so it belongs to a later phase that owns the chart and `leans.csv` together.

## Iteration 9 — post-bundle completion, phase R1 (human-directed)

**Why this exists.** After the bundle's eight items passed and the branch was pushed, the
operator asked for the remaining deck work. `.ralph/items.json` stays the bundle record (all
eight still pass); this phase is tracked here. A forward plan was written to
`internal/plans/2026-11-08-public-surface-completion-plan.md` (local, gitignored) and
reviewed read-only by two other opencode-go models (`glm-5.3-flash`, `kimi-k3.1-pro`); their
findings and dispositions are the plan's §7.

**R1.1 — the real-vs-felt chart is deleted (`f7311fb`).** Tests first: `TestRealVsFeltChartIsGone`
(no `feelchart`/`feelChart`/`FEEL_IDS`/`isDivergent`/`FEEL_HOT`; no `feelTitle`/`feelHint`/
`feelGapNote`/`feelBars`), a summary-title test, and render-smoke T33 (no retired key, no
render lookup, no retired heading). Removed the panel markup, the render block, the four
copy keys in both locales, `FEEL_IDS`, `FEEL_HOT`, `isDivergent`, `feelChart`; kept the
`data/leans.csv` fetch and `leanMap` (the headline's machine lean, a different consumer).
`render.py`'s summary title is now "Lines trembling in their recorded direction per day
(0-{n})" (what the bars count), and its docstring/comment no longer call the summary a
resonance — the reviewers caught that the old title would regenerate forever.

**R1.2 — status, panel, notes and footer copy to the deck (`367e9fd`).** Tests first:
`TestDeckStatusAndPanelCopy` (retired `alarmDarkH`/`alarmDarkB`/`disruptH`/`disruptB` gone;
`manyDark`/`disruption`/`noRecord`/`annoBody`/`zAxis`/`close` declared twice) and
render-smoke T34 (all five banner branches, panel headings, footer, `zAxis`, modal close
label, dated-notes heading and body in both detail builders). The banner's five branches
now render `noRecord` / `disruption` / `manyDark` / `warnH`+`warnB` / `statusOk`; the
`alarmDarkB` claim that a source failure "is itself a signal" is gone; the chart's vertical
axis reads the `zAxis` key; the close control's aria-label is localized. T24 was rebound
from `alarmDarkH` to `manyDark` with the same 3-of-4 majority rule.

**R1.3 — no adjudication paraphrase in the headline (landed in `5f79e62` together with R1.4).** Tests first: T22 now
asserts the raw annotation note never renders in the headline while the line detail keeps
it, and T23's order-precedence case is re-expressed as a machine-lean canary (the fixture
gained a flights lean; a later non-adjudicating `correction` must not un-adjudicate the
earlier `artifact` row). Removed the `verdictLabel` maps and their render site; `leanNote`
is the deck's sentence ("this line's own inputs moved together (…); no review note is
attached"), with the line tag's colon localized. `tests/lint_public_surface.py` drops the
map's parity test (the surface no longer exists) and asserts the map is gone; the module
docstring records why.

**R1.4 — an About block in the reading order (`5f79e62`).** Tests first: the declared-key
lint gains `aboutTitle`/`aboutBody`, and T34 asserts the section sits between `#limits` and
`#footer`, is visible after a plain render, and carries the deck's heading and body in both
languages. Rendered by `render()` into a new `#about` panel with one small CSS rule.

**Verification (all green after R1.4).** gate `415 passed / 126 subtests`; lint `Ran 85
tests … OK`; forbidden literal `OK`; audit `Ran 28 tests … OK`; replay exit 0
(`TOTAL 1439 0 0`); pending `6 tagged / 0 overdue`; render smoke `OK`; annotations mirror
identical. `docs/index.html` still has exactly one `innerHTML`, inside `setMarkup`.

**Not started: R2 (the count's number semantics).** The page's copy already says the count
crosses "in either direction" while `collect.counts_as_tremble` still counts the declared
direction only — a live mismatch. The reviewed design (plan §3 + §7): add forward-only
`unusual_count`/`count_method` cells, leave `counts_as_tremble` and the ledger's
`trembling_count` untouched, cut over with an `UNUSUAL_SINCE` marker that replay enforces,
derive the same rule in the page when the cell is absent (never fall back to
`trembling_count`), do not render `count_method`, and teach `tools/repair_fred_html_rows.py`
to maintain the new cells. Needs its own commit series and a data-owner window.

**R2 — the displayed count is direction-free (`collect: record a direction-free count beside the ledger's`).** The page's copy has said
"either direction" since item 2 while `collect.counts_as_tremble` counted the declared
direction only: a live mismatch between the published sentence and the published number.
Both reviewers put this first. Implemented as a forward-only schema extension, not a
rescoring:

- `collect.py`: `SUMMARY_HEADER` gains `unusual_count` and `count_method`; the collector
  counts every tier-1 row with `trembling == "1"` (either direction) into the new cell and
  stamps `COUNT_METHOD = "either-direction-tier1-v1"`. `trembling_count`, `counts_as_tremble`,
  episodes, lean panel, pair verdict and the repair predicate are untouched — the ledger
  keeps its declared-direction meaning and its SSOT.
- `tools/replay.py`: `summary_mismatches()` is now a pure function and also re-derives
  `unusual_count` from the replayed tier-1 rows. Rows before `collect.UNUSUAL_SINCE`
  (`2026-11-08`) may leave both cells empty; a row at or after it must carry them, the
  count must agree, and the method token must match. A corrupt cell is reported, not raised.
  `tests/test_replay.py` gains five gate tests for those rules.
- `tools/repair_fred_html_rows.py`: a summary rebuild maintains the two new cells.
- `docs/index.html`: the numerator reads `last.unusual_count`; when the cell is absent (a
  legacy row) it derives the same rule from the per-line rows already loaded — never from
  `trembling_count`. `firingLines` names every trembling tier-1 line either way, and
  `tremblingRunLength(rows, declaredDir)` became `unusualRunLength(rows)`.
- `tests/test_collect_loop.py`: the asymmetric fixture now also asserts `unusual_count == "3"`
  (two in-direction + one against-direction, never the tier-2 member) and the method token.
- `tests/render_smoke.js` T35: a two-day fixture where one line trembles in its recorded
  direction and one against it — headline 2 while `trembling_count` is 1, both lines named,
  a two-day run for each, and a legacy row still deriving 2 rather than falling back to 1.
  The assertion was proven load-bearing by running it against the pre-R2 page
  (`r2(en): the headline shows "1", expected the stored direction-free count 2`, plus the
  names/run/legacy failures, in both languages).
- `tests/lint_public_surface.py`: no `tremblingRunLength`, and a direction-free run helper.

`data/summary.csv` is untouched: the next collection writes the two cells for its own day,
the older rows keep empty cells, and the dashboard's derivation covers the transition. No
scoring rule, threshold, tier, `STABLE_SINCE` or historical value changed (both reviewers
confirmed no bump is required).

**Verification (R2).** gate `420 passed / 126 subtests`; lint `Ran 86 tests … OK`; audit
`Ran 28 tests … OK`; forbidden literal `OK`; replay exit 0 (`TOTAL 1439 0 0`, summary
re-derivation clean); pending `6 tagged / 0 overdue`; render smoke `OK`; annotations mirror
identical.

## Iteration 10 — post-bundle completion, phase R3 (human-directed)

Two decisions from the operator: render `referenceItem` with corrected labels, and drop
`reviewNote`.

**`referenceItem` (corrected labels).** The deck's template says `latest {value}`, but the
level layer carries a 14-day trailing median, not a latest single-day observation, and
`{days} consecutive days` would overclaim for a held-open state (the state persists after
the trailing median recovers). The rendered line therefore states what the record holds:

- `tools/stuck_panel.py` now carries `trail_median`, `reference` and `open_days` through
  from `data/levels.csv` (it already carried `pct`), with `open_days` = inclusive calendar
  days since the state opened. The reporter is derived-from-scratch, so this is a
  projection change, not a record rewrite: the old columns are byte-identical in all 290
  rows (checked), and `docs/data/stuck.csv` was regenerated by the reporter.
- `docs/index.html`: `levelWhich` (a bare name list) is gone; `referenceItem` renders one
  line per open state under the count — `{name} · open since {date} · 14-day median {n} vs
  pinned reference {n} transits/day · {days} days`, in both languages. The count label
  keeps `referenceAsOf`; the values are the reporter's cells, never recomputed from `pct`.
- `reviewNote` is not implemented: the record has no field for it, the negative half is
  already `leanNote`'s "no review note is attached", and a positive tag would paraphrase
  an adjudication the date-stamped note already carries.
- Tests: `test_stuck_panel` binds the carried values and `open_days` (113 for Hormuz
  04-06→07-27, 2 for Kerch 07-26→07-27); render-smoke T36 binds both languages and asserts
  the label no longer lists bare names; lint binds `referenceItem` and the absence of
  `levelWhich`. The T29/T32 fixtures gained the carried fields so the undefined sweep stays
  meaningful.

**Verification (R3).** gate `420 passed / 126 subtests`; lint `Ran 86 tests … OK`; audit
`Ran 28 tests … OK`; forbidden literal `OK`; replay exit 0 (`TOTAL 1463 0 0`); pending
`6 tagged / 0 overdue`; render smoke `OK`; annotations mirror identical. `charts/*.png`
and `radar-metrics.md` remain the nightly job's output.

## Iteration 11 — P0/P1 sweep after the reference-item merge (human-directed)

One P1 found and fixed: the new fixed-reference block interpolated the component name and
four carried CSV cells straight into the page's single markup sink, against the page's own
`esc()` contract and the record's threat model (an upstream component name can carry
markup, as the FRED HTML incident showed). Fixed by escaping `straitLabel(r.component,lang)`,
`r.trail_median`, `r.reference`, `r.open_days`, `r.since` and `lLatest`, with a render-smoke
T37 hostile-component case and two lint bindings. No P0 found: gates, replay (0 divergence
over 1463 rows), audit, mirrors (all 26 MIRRORED files byte-equal), CI on the prior pushes
and the Pages build were green; the 2026-11-08 headline derives to 0 and agrees with the
per-line rows.
