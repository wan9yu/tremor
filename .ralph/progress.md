# Progress ledger

## Iteration 1 — item 1 (functional): pending-reviews block, no untagged promise, no overdue tripwire

**Chosen because** `.ralph/plan.md` prioritizes it first: `python tools/pending.py --check`
is a verification gate and was red on entry (`level-layer → flights`,
`date >= 2026-11-01`, and the clock had reached that date), so every other item would
fail its own verification until this landed. No item was hard-blocked (the ledger was
empty on entry).

**Entry state measured.** `python tools/pending.py --check` exited 1 with exactly one
OVERDUE entry (`level-layer → flights`, date = 2026-11-01 / 2026-11-01). Its table listed
four tagged items. The block held twelve bullets, of which four were closed by the
block's own rule (flights sample-hour SHIPPED, cnh_cny maturity DONE R33, net_outages
CLOSED R28, cnh_cny reachability reference-regime DONE R33) and three carried no tag and
no closure marker at all (cnh_cny maturity, calendar de-cycling, cnh_cny reachability).
`python -m unittest discover tests -p "audit_*.py"` was red on entry with two failures:
the control-line astronomy assertion and `radar-metrics.md` staleness.

**Assumption recorded (ordinary ambiguity, resolved conservatively).** The item's steps
2 and 4 collide on one bullet: step 2 deletes "the flights sample-hour SHIPPED bullet",
step 4 retags "the flights sample-hour bullet". Only one such bullet exists. Resolved as:
the SHIPPED half is closed and removed (its history lives in radar-log.md R25/R25.1), and
the STILL-OPEN re-review that trailed it survives as the retagged bullet, so no open
commitment is silently deleted while the shipped item is closed by the block's own rule.
The surviving bullet keeps the two clauses that are still standing rules (the
anti-loophole demotion disqualifier, and the R34 finding that the 22:30Z baseline is
continuous for the TOTAL only, not for a per-region share).

**Second assumption.** Step 4 says to retag the SOFR deferral sentence. That sentence sat
at the end of the R22 single-credit-slot bullet, so a tag there would generate a pending
row labelled "the single-credit-slot bar" for a predicate about `sofr_iorb_spread`.
Split the deferral into its own bullet, tagged `[opened R29 · owner R40 · fires: date >=
2026-11-30]`, leaving the credit-slot bar as a pure standing rule. Same content, honest
label.

**Third decision (serves the item's description, beyond the enumerated steps).** The
closed `closed-status first live weekend` bullet ended with an open "Follow-up: … decide
whether the guard should also cover Saturday (a fetcher change → needs approval)". That
is an untagged promise inside a closed item, and no later radar entry discharges it. The
follow-up was split into its own bullet tagged `[opened R23 · owner R40 · fires: manual]`
(the grammar's form for a human decision). The obs-dedup half of that follow-up was
dropped: Known limits #6 now states the distinct-observation rule and its 8 cnh_cny rows,
so that question is answered in the registry.

**Files changed.**

- `radar.md` — Pending block: four closed bullets removed (flights sample-hour SHIPPED,
  cnh_cny maturity refresh DONE R33, net_outages CLOSED R28, cnh_cny reachability
  reference-regime DONE R33 including its phantom "n≥250" trailing reference); the
  flights fixed-hour re-review retagged `[opened R26 · owner R40 · fires:
  rows_since(flights, 2026-09-02) >= 90]`; `level-layer → flights` retagged `[opened
  R23.1 · owner R40 · fires: date >= 2027-08-02]` with a closing note saying why the Nov
  2026 target was dropped (it belonged to the per-region component plan R34 killed); the
  SOFR deferral split out and tagged; the weekend-guard follow-up split out and tagged
  `manual`; "standing" added to the calendar de-cycling bullet's opening parenthetical.
- `tools/pending.py` — new public `block_bullets()` (the one block scan, exposed so a
  lint can assert over UNTAGGED bullets too); `collect_items()` now iterates it; the block
  boundary also ends at the section's `---` rule (previously the last bullet swallowed
  that separator, which an end-anchored assertion reads as bullet content); and an
  `ast.List` guard on the `LINES` assignment so a non-list assignment raises the module's
  own `PendingParseError` instead of `AttributeError`.
- `tests/lint_pending.py` — one new assertion (`TestEveryBulletIsTrackedOrClosed`) that
  every bullet in the block ends in a parseable tag, carries "standing", or closes with a
  round-referenced marker on its first line. Import switched to `from tools import
  pending`: the bare `import pending` the rest of the suite uses resolves only at runtime,
  so a static analyzer reports it unresolved; `tools.pending` is the same module object.
  The pre-existing `Module level import not at top of file` note on the file is unchanged
  and shared with `tests/test_pending.py` and `tests/audit_registry.py`.
- `radar-metrics.md` — regenerated (`python tools/episodes.py --markdown` then
  `python tools/pending.py --markdown`), which both refreshes the pending section and
  clears the staleness audit (the committed copy was 10 days of data behind: control rows
  85 → 95, flights 122 → 132).

**Failing test first.** The new lint assertion was added and run before the radar.md edit:
it failed with exactly the three untagged bullets (cnh_cny maturity, calendar de-cycling,
cnh_cny reachability). It went green after the block edit, then stayed green after the
weekend-guard split (the `manual` tag).

**Verification (all commands run at the commit that closed this item).**

- `python -m pytest tests/ -q` — 318 passed, 20 subtests passed (exit 0).
- `python -m unittest discover tests -p "lint_*.py"` — Ran 56 tests, OK (exit 0).
- `python tests/lint_no_forbidden_literal.py` — Ran 3 tests, OK (exit 0).
- `python tools/replay.py --check` — exit 0; TOTAL 1271 rows, 0 divergent.
- `python tools/pending.py --check` — exit 0, "OK — 6 tagged pending item(s), 0 overdue,
  0 unparseable" (was exit 1 on entry).
- `node tests/render_smoke.js` — exit 0, "render OK in both languages".
- `python -m unittest discover tests -p "audit_*.py"` — Ran 23 tests, 1 failure:
  `audit_record.TestControlLineRecord.test_every_row_matches_the_astronomy_for_the_day_it_claims`
  (2026-10-22: recorded 10.3419h vs 10.3976h implied by obs_date 2026-10-21). That is the
  control-line astronomy failure the plan assigns to item 7. The registry freshness
  failure is gone. The audit tier is not a global gate for this bundle.

**Note on step 6's wording.** The step asks to confirm "the registry freshness test is the
only remaining audit failure" after regenerating. Regenerating clears that test, so the
remaining single failure is the astronomy one; recorded here rather than explained away.

**Next iteration should know.** `pending --check` is green and is now a usable gate for
items 2-10. The block's closure convention is enforced by
`tests/lint_pending.py::TestEveryBulletIsTrackedOrClosed`, so any new bullet must be
tagged, marked standing, or round-closed. `radar-metrics.md` was regenerated from the
current committed data and must be regenerated again if a later item changes a line file
or a pending bullet. Item 2 (the `drift_layer.py` derive guard) is next in the plan's
order; item 8 (the five-row FRED repair) explicitly depends on items 2 and 4 landing
first.

## Iteration 2 — item 2 (bug): drift_layer stops crashing on a malformed obs_date

**Chosen because** `.ralph/plan.md` puts it second: item 1 cleared the pending gate, and
this is the first damage-stopping item (the nightly derive step crashed, so the level,
drift, stuck and leans layers were frozen). No item was hard-blocked.

**Entry state measured.** `python tools/drift_layer.py --report` exited 1 with
`ValueError: Invalid isoformat string: '    <link href="https://fonts.googleapis.com/...'`
raised at `walk`'s `ords = [_date.fromisoformat(d) ...]` (drift_layer.py:78), reached from
`main` → `compute` → `walk`. The bad key enters through `series_for`, which keyed on
`r["obs_date"] or r["date"]`. Five committed rows carry an HTML error page in the obs_date
column (credit_spread, em_corp_oas, euro_hy_spread, sofr_iorb_spread, vix, all dated
2026-10-22) — the FRED incident item 8 repairs.

**Fix.** `tools/drift_layer.py`:
- `is_strict_date(value)` — one shared predicate: a `[0-9]{4}-[0-9]{2}-[0-9]{2}` shape
  match (ASCII digits, `\Z` end) plus a real calendar check via `date(y, m, d)`. It is
  deliberately not `date.fromisoformat`, which from 3.11 also accepts the basic form
  `20261022`. It rejects non-strings, empty strings, `2026-02-31`, `2026-13-01`, and a
  timestamp suffix, so `walk`'s own `fromisoformat` cannot still raise on a key it is
  handed.
- `series_from_rows(rows)` — pure row-level helper returning `(series, skipped)`. An empty
  `obs_date` keeps the row's own `date` (flights and capital_premium score rows with no
  observation date; dropping them would delete whole series without a crash). A non-empty
  `obs_date` that fails the predicate drops that observation with no fallback. A dark row
  (empty `raw_value`) is skipped before the date check, so it is not counted as dropped.
- `series_for(line)` delegates to that helper and returns `(series, skipped)`; `compute()`
  sums the skip tally and returns `(rows, skipped)`; `main` prints it on the existing
  summary line: `... ; 5 observation(s) dropped (unusable obs_date)`. The `--report` path
  unpacks the new tuple and is unchanged otherwise.

**Assumption recorded (ordinary ambiguity).** The item's rule set guards `obs_date` only.
The empty-`obs_date` fallback is the row's own `date`, which is still not validated; that
is what step 2 asks for ("keeps the existing fallback"), and the row date is written by
`collect.py` from its own clock. Left unguarded rather than widening the item.

**Failing test first.** Three gate tests were written in `tests/test_level.py`
(`TestDriftDateGuard`) before the implementation: predicate acceptance/rejection, the
row-level drop/keep/dedup rules with `walk` over the surviving series, and the same rules
through `series_for` with `support.stub_attr(drift_layer.seedlib, "read_line", ...)` (no
`data/` read). Red evidence: with only `tools/drift_layer.py` stashed back to HEAD,
`python -m pytest tests/test_level.py -q` gave `3 failed, 11 passed`, each failing with
`AttributeError: module 'tools.drift_layer' has no attribute 'is_strict_date'` /
`series_from_rows`. Green after the implementation.

**Test-file import change.** `tests/test_level.py` switched from the bare
`import drift_layer` / `import level_layer` (resolvable only through the file's runtime
`sys.path` insertion) to `import support` plus `from tools import drift_layer,
level_layer`, the idiom already used by `tests/lint_pending.py` and
`tests/test_reconcile_common_mode.py`. Same module object graph at runtime; the static
analyzer no longer reports the two imports unresolved. `tools/` is a namespace package
(no `__init__.py`), importable because the test inserts the repo root first.

**Files changed.** `tools/drift_layer.py`, `tests/test_level.py`,
`.ralph/items.json`, `.ralph/progress.md`. `data/drifts.csv` was rewritten by the tool and
re-derived byte-identically (no diff, nothing staged).

**Verification (all commands run at the commit that closed this item).**

- `python tools/drift_layer.py --report` — exit 0 (was exit 1 with the ValueError);
  prints the single historical gnss_interference open/clear pair, no state open now.
- `python tools/drift_layer.py` — exit 0; `drifts: 134 rows (2 open/clear events) -> ...
  ; 5 observation(s) dropped (unusable obs_date)`.
- `python -m pytest tests/ -q` — 321 passed, 20 subtests passed (exit 0; 318 before, the
  three new tests).
- `python -m unittest discover tests -p "lint_*.py"` — Ran 56 tests, OK (exit 0).
- `python tests/lint_no_forbidden_literal.py` — Ran 3 tests, OK (exit 0).
- `python tools/replay.py --check` — exit 0; TOTAL 1271 rows, 0 divergent.
- `python tools/pending.py --check` — exit 0; 6 tagged, 0 overdue, 0 unparseable.
- `node tests/render_smoke.js` — exit 0, render OK in both languages.
- `python -m unittest discover tests -p "audit_*.py"` — Ran 23 tests, 1 failure:
  `audit_record.TestControlLineRecord.test_every_row_matches_the_astronomy_for_the_day_it_claims`
  (2026-10-22 recorded 10.3419h vs 10.3976h implied by obs_date 2026-10-21). That is the
  pre-existing failure item 7 owns; no new audit failure. The audit tier is not a global
  gate for this bundle.

**Next iteration should know.** The derive step runs again; `data/drifts.csv` was verified
byte-identical, so no derived-file churn from this item. The guard is at
`series_from_rows`/`series_for`, so any future derive tool that parses `obs_date` from a
line record still needs its own shape check (item 4 adds the collection-time check in
`collect.py`; item 8 repairs the five bad rows and re-derives the tail). Item 3
(`core/fred.py` shape validation) is next in the plan's order, then item 4; item 8 requires
both of them plus this item.

## Iteration 3 — item 3 (bug): core/fred.py refuses a body whose first column is not a date

**Chosen because** `.ralph/plan.md` puts it third: one of the two damage-stopping items left
after the derive guard, and the direct cause of the five contaminated rows item 8 repairs.
No item was hard-blocked.

**Entry state measured.** `python -m pytest tests/ -q` 321 passed. The mechanism was
reproduced offline before any edit: the committed rows carry the fragment
`    <link href="https://fonts.googleapis.com/css?family=Open+Sans:300` as `obs_date` and
`400` as `raw_value`, and feeding a page with that line through `series()` returned
`[('    <link href=…Open+Sans:300', 400.0)]` — the link splits at its comma pair, the old
parse checked only the value column, and `float("400")` succeeded.

**Fix.** `core/fred.py`:
- `_is_iso_date(field)` — `[0-9]{4}-[0-9]{2}-[0-9]{2}\Z` (ASCII digits, absolute end)
  plus a real calendar check via `date(y, m, d)`, and an `isinstance(str)` guard so the
  predicate is total. Deliberately not `date.fromisoformat`, which from 3.11 also accepts
  the basic form `20261022`. Same predicate as `tools/drift_layer.is_strict_date`, with a
  cross-reference in the comment; the duplication is deliberate for now because the two
  live in different layers (item 4 adds the third copy at collection time) and a shared
  module is not this item's change.
- `series()` drops any row whose first field fails that predicate and returns `None` when
  no row survives. Field count is still not asserted (a three-column response reads
  unavailable rather than being parsed), which is what the source-shape plan asked for and
  what keeps a future extra column from darkening all five FRED lines into a parse.
- `common_pair(a, b)` returns `(date, value_a, value_b, missing)`; `latest_common`
  delegates and keeps its `(date, value_a, value_b)` contract (its only caller is
  `tests/test_seedlib.py`).
`fetchers/sofr_iorb.py` uses `common_pair` and separates the two causes: a dark leg reads
`FRED <leg> unavailable`, a shared-date gap still reads `FRED SOFR/IORB share no reported
date` (same string as before, now built from `SERIES` instead of a second literal). The
module docstring states why the two are different failures.

**Assumption recorded (ordinary ambiguity).** The item says "the first comma-separated
field of each row"; the existing parse already skips the first line as a header, and that
was left alone. An HTML body's first line is therefore dropped as a "header" before the
predicate runs, which changes nothing: no HTML page's second line is a dated pair, and a
one-line body still returns `None` through `out or None`.

**Failing test first.** `tests/test_fred_shape.py` (new) and two tests in
`tests/test_seedlib.py::TestLegDiscipline`. Red evidence: with `core/fred.py` and
`fetchers/sofr_iorb.py` copied back from `HEAD`, `python -m pytest tests/test_fred_shape.py
tests/test_seedlib.py -q` gave `5 failed, 17 passed`; green after the fix. The cases pin
behaviour, not the implementation: the incident page returns `None` end to end through
`reading()`, a dated CSV still parses, and a mixed body keeps only the dated row. The
mixed body deliberately includes `20261022` (basic format), Arabic-Indic `٢٠٢٦-10-22` and
full-width `２０２６-10-23` (both match `\d` and both are valid inputs to `int()`), and
`2026-02-31` (right shape, impossible day) — so a `[0-9]`→`\d` mutation or a dropped
calendar check fails the test. The non-200 case now serves a well-formed body, so only the
status branch can reject it.

**Independent review.** `reviewer` (opencode-go/deepseek-v4.1-flash) reviewed the diff:
verdict "OK with notes", no P0/P1, and six P2 notes on test robustness and doc accuracy.
Five were taken in this iteration: the shared-predicate cross-reference, the `isinstance`
guard, the corrected claim about what downstream readers accept, the Unicode-digit and
faithful-link rows, the non-200 body, and the both-legs-dark note test. The sixth (extract
the predicate to one home) is deferred: it spans `tools/drift_layer.py`, `core/fred.py` and
the not-yet-written `collect.py` check, and the review itself recommends doing it when the
third copy lands.

**Files changed.** `core/fred.py`, `fetchers/sofr_iorb.py`, `tests/test_seedlib.py`,
`tests/test_fred_shape.py` (new), `.ralph/items.json`, `.ralph/progress.md`. No `data/`
file changed; no derived layer re-ran; `radar-metrics.md` untouched (no line, pending item
or round changed).

**Why the record does not change here.** `tools/replay.py` re-scores the STORED
`raw_value`, so it cannot see a bad response; the five committed rows stay exactly as they
are until item 8 archives and darkens them. This item only makes the recurrence impossible.

**Verification (all commands run at the commit that closed this item).**

- `python -m pytest tests/ -q` — 329 passed, 20 subtests passed (exit 0; 321 before, the
  eight new tests).
- `python -m unittest discover tests -p "lint_*.py"` — Ran 56 tests, OK (exit 0).
- `python tests/lint_no_forbidden_literal.py` — Ran 3 tests, OK (exit 0).
- `python tools/replay.py --check` — exit 0; TOTAL 1271 rows, 0 divergent.
- `python tools/pending.py --check` — exit 0; 6 tagged, 0 overdue, 0 unparseable.
- `node tests/render_smoke.js` — exit 0, "render OK in both languages; no runtime errors,
  no undefined/NaN".
- `python -m unittest discover tests -p "audit_*.py"` — Ran 23 tests, 1 failure:
  `audit_record.TestControlLineRecord.test_every_row_matches_the_astronomy_for_the_day_it_claims`
  (2026-10-22: recorded 10.3419h vs 10.3976h implied by obs_date 2026-10-21). That is the
  pre-existing failure item 7 owns; no new audit failure. The audit tier is not a global
  gate for this bundle.

**Note on the test-file import change.** `tests/test_seedlib.py` switched `import seedlib`
to `from tools import seedlib` to clear the static analyzer's unresolved-import note; same
module object graph at runtime (`tools/` is a namespace package, and no test patches
`seedlib` attributes). The file's two remaining analyzer notes (import block order, module
level import not at top of file) were already present at `L15`/`L16` before this iteration
and come from the file's `sys.path.insert` idiom, which `tests/test_pending.py` and
`tests/audit_registry.py` share.

**Next iteration should know.** `core/fred.py` is now the third place a strict date
predicate is spelled (`tools/drift_layer.is_strict_date` is the first); item 4 adds one in
`collect.py`, and the reviewer's recommendation is to extract the predicate to one home at
that point rather than ship three copies. The `missing` list from `common_pair` is the
supported way to describe a two-leg failure without a second fetch, so a future fetcher
that wants a cause-distinguishing note should use it instead of `latest_common`. Item 4
(the collection-time `obs_date` check) is next in the plan's order; item 8 still requires
items 2 and 4 plus this one.

## Iteration 4 — item 4 (bug): collect.py refuses an unusable obs_date at collection time

**Chosen because** `.ralph/plan.md` puts it fourth: after the derive guard (item 2) and the
FRED shape check (item 3) it is the last damage-stopping item, and item 8 (the five-row
repair) lists it as a precondition. No item was hard-blocked.

**Entry state measured.** `python -m pytest tests/ -q` 336 passed after the change, 329
before it; `python tools/pending.py --check` exit 0. The hole was reproduced offline before
any edit: a stub fetcher returning `{"raw_value": 400.0, "obs_date": "<the incident's HTML
first comma-field>"}` through the real `collect()` was SCORED — status warm, raw stored,
the phantom observation date written into the row. That is the same shape that produced the
five 2026-10-22 rows.

**Fix.** `collect.py`:
- `is_strict_date(value)` — `[0-9]{4}-[0-9]{2}-[0-9]{2}\Z` (ASCII digits, absolute end) plus
  a real calendar check via `datetime.strptime`. Not `date.fromisoformat`, which from 3.11
  also accepts the basic form `20261022`. Same predicate as `tools/drift_layer.is_strict_date`
  and `core.fred._is_iso_date`, cross-referenced in the docstring.
- `obs_date_problem(obs_date, date)` — `None` for an empty `obs_date` (a snapshot line keeps
  the collection date) or a strict date on/before the row date; otherwise the reason string.
  Both operands of the `>` comparison are strict-shaped when it is reached, so lexicographic
  order is calendar order.
- `collect()` — the check sits between `coerce_finite` and `apply_sample_guard`. On a
  violation it sets `raw = None`, clears `obs_date`, and prefixes the note with exactly
  `no reading: source returned an unusable observation date - not scored :: `, then appends
  the reason and the original note. Collection-time only, like `apply_sample_guard`: the
  refusal is frozen into the stored row as dark, so it replays deterministically and no
  scoring rule or `STABLE_SINCE` is touched.
- The module docstring sentence declaring `obs_date` shape validation out of scope is
  replaced by the actual contract (non-empty must be a real YYYY-MM-DD and not later than
  the row; empty is legitimate).

**Assumptions recorded (ordinary ambiguity).**

1. Ordering: `coerce_finite` → obs_date check → `apply_sample_guard`. A darkened raw has
   already cleared `obs_date`, so the two guards never double-report, and the sample guard
   returns unchanged on a `None` raw. `write_components` then keys the darkened row by the
   collection date, which is what every other dark row already does.
2. "Not later than the row's own date" is compared against `clock.china_today()`, the same
   memoized date the row is stamped with, so the guard cannot disagree with the record's own
   dating.
3. The strict predicate is now spelled in three places (`tools/drift_layer.py`,
   `core/fred.py`, `collect.py`). Item 3's review recommended extracting it when the third
   copy landed; this item's steps do not ask for that refactor, so it is deferred and the
   three docstrings cross-reference each other. Extraction would touch the fetch parser and
   the derive tool, which item 8 depends on, for no behaviour change.

**Failing test first.** `tests/test_collect_loop.py`: `_mod` gained an optional `obs_date`
kwarg and its `raw` parameter is annotated `object` (the stub deliberately hands the
collector shapes a real fetcher must never return); two new classes were added,
`TestUnusableObsDateIsDarkened` (malformed shapes including the incident HTML field,
`20261022`, `2026-02-31`, `2026-13-01`, a timestamp suffix and `22/10/2026`; a future
`obs_date`; and a usable one stored verbatim) and `TestObsDateProblemDirectly` (the pure
predicate, each branch its own assertion). Red evidence: with only `collect.py` stashed back
to HEAD, `python -m pytest tests/test_collect_loop.py -k "UnusableObsDate or ObsDateProblem"`
gave `16 failed, 3 passed, 2 subtests passed`; green after.

**Record scan (offline, no network).** Every committed `data/*.csv` obs_date was run through
`collect.obs_date_problem` against its own row date: exactly five rows are refused, the five
known 2026-10-22 FRED rows (`credit_spread`, `em_corp_oas`, `euro_hy_spread`,
`sofr_iorb_spread`, `vix`). No other committed row is affected, so the guard is invisible to
the good record and item 8 owns the repair of those five.

**Analyzer note.** The lens ast-grep rule `unchecked-throwing-call-python` reports five
findings on `_read_rows`, `_write_rows` and the `docs/` mirror loop. Those lines are
pre-existing at HEAD (`git show HEAD:collect.py` has the same calls; this diff's hunks are
the docstring, `import re`, the new helpers, and the `collect()` check). Not changed
deliberately: a failed write to the forward-only record must abort the run loudly, and
wrapping it would either swallow the failure or re-raise for no gain. Not a project gate.

**Files changed.** `collect.py`, `tests/test_collect_loop.py`, `.ralph/items.json`,
`.ralph/progress.md`. No `data/` file changed; no derived layer re-ran; `radar-metrics.md`
untouched (no line, pending item or round changed).

**Verification (all commands run at the commit that closed this item).**

- `python -m pytest tests/ -q` — 336 passed, 34 subtests passed (exit 0; 329 before, the
  seven new tests).
- `python -m unittest discover tests -p "lint_*.py"` — Ran 56 tests, OK (exit 0).
- `python tests/lint_no_forbidden_literal.py` — Ran 3 tests, OK (exit 0).
- `python tools/replay.py --check` — exit 0; TOTAL 1271 rows, 0 divergent.
- `python tools/pending.py --check` — exit 0; 6 tagged, 0 overdue, 0 unparseable.
- `node tests/render_smoke.js` — exit 0, render OK in both languages.
- `python -m unittest discover tests -p "audit_*.py"` — Ran 23 tests, 1 failure:
  `audit_record.TestControlLineRecord.test_every_row_matches_the_astronomy_for_the_day_it_claims`
  (2026-10-22: recorded 10.3419h vs 10.3976h implied by obs_date 2026-10-21). That is the
  pre-existing failure item 7 owns; no new audit failure. The audit tier is not a global
  gate for this bundle.

**Next iteration should know.** Item 5 (the failure-alarm body) is next in the plan's order;
item 8 now has all three of its preconditions (items 2, 3, 4). The guard lives in `collect()`
only: `tools/replay.py` re-scores the stored `raw_value` and never parses a source
`obs_date`, and the derive tools parse committed rows (guarded by item 2), so no other path
needs this check. A future fetcher whose `obs_date` is stamped in a timezone ahead of China
(UTC+8) would now be darkened; none of the 25 live fetchers does today, and a snapshot line
that leaves `obs_date` empty is unaffected.

## Iteration 5 — item 5 (bug): the failure alarm body states the step order, not a falsehood

**Chosen because** `.ralph/plan.md` puts it fifth: item 1 cleared the pending gate and items
2-4 landed the three damage-stopping guards, so this is the next unfinished item in the
plan's order (the "items that stop further damage next" group). No item was hard-blocked.

**Entry state measured.** The alarm step in `.github/workflows/daily.yml` opened with
`The instrument writes no row for a failed run, and the schedule itself expires after 60
days without a commit.` The first clause is false for the step order the same file
declares: `Commit the day` (line 87) runs BEFORE the derive layer, `replay.py --check`, the
`audit_*.py` tier and the render smoke, so every one of those failures fires the alarm on a
run that already wrote and pushed the day. The alarm is `if: failure()`, so it covers all
of them.

**Failing test first.** `tests/lint_workflows.py::TestFailureAlarmBodyMatchesTheStepOrder`
(new, five tests) was added and run before the workflow edit: `python -m unittest discover
tests -p "lint_workflows.py" -k TestFailureAlarmBodyMatchesTheStepOrder -v` gave
`Ran 5 tests ... FAILED (failures=5)`, each assertion quoting the old body. Green after the
body edit (15/15 in that file).

**Fix.** `.github/workflows/daily.yml`, alarm body only:
`A run that fails before the commit step leaves the day unrecorded. A run that fails after
it has already pushed the day has not lost the day; the failure lies in a later step. The
schedule itself expires after 60 days without a commit. Fix or disable deliberately.`
The schedule-expiry sentence is kept with its content unchanged (now its own sentence);
the `Run failed on $(date -u +%F) — $run_url` line, `TITLE`, `NUM`, the `if [ -n "$NUM" ]`
branch and both `gh` calls are untouched. No command substitution or backtick was added:
the block still carries exactly `$(date -u +%F)` and the pre-existing `$(gh issue list ...)`,
asserted by count.

**Assumption recorded (ordinary ambiguity).** The item says "replace only the false clause
… keeping the schedule-expiry sentence". The false clause is the row-less-run claim; the
replacement says which failures cost the day and which do not, and deliberately does not
enumerate the post-commit steps (the derived-layer commit, `replay`, the audit tier, the
render smoke, the sample-hour notice) because that list would drift the moment a step is
added. "The failure lies in a later step" is true for every one of them without naming any.

**Behaviour-neutral analyzer pass in the same file (recorded, not scope creep).** Editing
`tests/lint_workflows.py` surfaced 10 analyzer diagnostics on code that is byte-identical
to `HEAD` (`git show HEAD:tests/lint_workflows.py`): four `assertLess` calls fed an
`int | None` from the local `first()` helper, and two `assertIn`/`assertNotIn` calls fed a
`str | None` from `_job_block()`. Both files are covered by no type-check gate in this repo
(no pyright/mypy config, no type step in `ci.yml`), but the diagnostics block the edit, so
they were cleared without changing any assertion: `first(msg, predicate)` now calls
`self.fail(msg)` and returns `int` (the five `assertIsNotNone` lines are removed and their
message strings move into the call sites verbatim), and `_job(name)` does the same for the
two `ci.yml` job-block lookups. Same assertions, same failure messages, same passing set.

**Files changed.** `.github/workflows/daily.yml`, `tests/lint_workflows.py`,
`.ralph/items.json`, `.ralph/progress.md`. No `data/` file, no derived layer and no
`radar-metrics.md` change: this item touches neither a line file nor a pending bullet.

**Verification (all commands run at the commit that closed this item).**

- `python -m pytest tests/ -q` — 336 passed, 34 subtests passed (exit 0).
- `python -m unittest discover tests -p "lint_*.py"` — Ran 61 tests, OK (exit 0; 56 before,
  the five new alarm-body tests).
- `python tests/lint_no_forbidden_literal.py` — Ran 3 tests, OK (exit 0).
- `python tools/replay.py --check` — exit 0; TOTAL 1271 rows, 0 divergent.
- `python tools/pending.py --check` — exit 0; "OK — 6 tagged pending item(s), 0 overdue,
  0 unparseable".
- `node tests/render_smoke.js` — exit 0, render OK in both languages.
- `python -m unittest discover tests -p "audit_*.py"` — Ran 23 tests, 1 failure:
  `audit_record.TestControlLineRecord.test_every_row_matches_the_astronomy_for_the_day_it_claims`
  (2026-10-22: recorded 10.3419h but its obs_date 2026-10-21 implies 10.3976h). That is the
  pre-existing control-line failure item 7 owns; no new audit failure. The audit tier is not
  a global gate for this bundle.

**Next iteration should know.** All six gates are green and the alarm body now matches the
step order; `tests/lint_workflows.py` pins it through `support.workflow_run_steps`, so a
future edit that re-introduces the row-less claim fails the lint tier. The remaining
unfinished items are 6 (prose statements in `tests/test_control.py` and `radar.md`), 7 (the
control-line offset), 8 (the five-row FRED repair, whose preconditions items 2-4 are all in),
9 (derived-recency audit assertions) and 10 (the `AGENTS.md` components claim). Items 6, 7,
9 and 10 are independent; item 8 should run before item 9, which asserts properties the
repair and regeneration produce.
