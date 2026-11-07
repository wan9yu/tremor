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
