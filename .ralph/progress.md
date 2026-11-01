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

## Iteration 6 — item 7 (bug): the control-line offset is a published-model change, dated at the comparison site

**Chosen because** `.ralph/plan.md` orders the record-changing group after the
damage-stopping items and puts the control-line disposition before the five-row FRED
repair. Items 1-5 had landed; item 7 was the next unfinished item and no item was
hard-blocked. Item 8 (the FRED repair) already has its three preconditions (items 2-4).

**Entry state measured.** `python -m unittest discover tests -p "audit_record.py" -k
test_every_row_matches_the_astronomy_for_the_day_it_claims` failed on row 2026-10-22:
recorded 10.3419h against 10.3976h implied by obs_date 2026-10-21 (0.0556 h vs the 0.017 h
bar). The audit tier was 23 tests, 1 failure. The gate tier was 336 passed.

**Step 1 — the offline residual table (recorded in the annotation row).** Ten committed
rows are dated 2026-10-22 or later. Against `astronomical_day_length_h` for the claimed
obs_date they read −200.32, −200.93, −201.39, −201.76, −203.10, −203.47, −203.93, −204.53,
−206.36, −206.47 s; against the FOLLOWING day's model +25.07, +23.61, +22.24, +20.90,
+18.53, +17.07, +15.47, +13.64, +10.53, +9.05 s. The four rows before them sit within
0.9 s of their claimed day. So neither the claimed day nor the next day explains the
values within the 0.4 s fidelity the model has held on every pre-change row.

**Step 2 — the dated source requests.** 2026-11-01, lat 51.4779 lng 0.0, formatted=0:
2026-10-15 (before) returned 38601 s where the 2026-09-08 fetch returned 38799 s (−198 s);
2026-11-03 (after) returned 34376 s against 34586 s pinned from 2026-09-08 (−210 s). The
source recomputed dates before the change as well, so this is a published-model
redefinition, not a per-date slip. The source's current value for each of the ten claimed
obs_dates equals the recorded value exactly, which settles the label question in the same
direction (a slip would have to pick the wrong day consistently for ten days while the
offset drifted monotonically). 19 vendor samples spanning a year (seven around the change
plus one per month 2026-11-15..2027-10-15) fit ONE flat effective solar depression of
−0.84984 deg to within 4.44 s; the first generation's semidiameter double-subtraction is
no longer present, though the residual level sits about 0.017 deg below the plain −50′ that
removing that term alone would leave, so the constant is fitted and not re-derived.

**Step 3 — the branch applied.** Branch one, `source-model change`. The correction is a
dated dispatch at the comparison site for obs_date ≥ 2026-10-21, outside both pinned
models: `source_model_for(obs_date)` returns the generation the source published that day
and `source_day_length_h(lat, day)` applies it to one day. `tests/audit_record.py`'s canary
compares against `source_day_length_h`; `tests/test_control.py::closest_day_margin` takes
the model once per row and applies it to all seven candidate days.

**Step 4 — the archive.** `data/archive/control_daylength_pre_model_change_2026-11-01.csv`,
written by a snippet that refuses to start when the target exists (it did not), 95 data
rows, byte-identical to the live file (`cmp` clean, sha256 match).

**Step 5 — the annotation row.** `data/annotations.csv` line 141: `2026-11-01,
control_daylength, method` with the residual table, the source probe, the branch, the fit,
the rows touched (none) and the artifacts. Mirrored to `docs/data/annotations.csv`;
`cmp` clean, both files 141 rows, 4 columns. The append is one added line: the other 139
rows are byte-identical to `HEAD`, so nothing published was rewritten.

**Assumptions recorded (ordinary ambiguity).**

1. *"Leaving astronomical_day_length_h unchanged"* is read as "its numbers and its pin
   table stay": the body was replaced by a delegate to a new private
   `_day_length_h(lat_deg, day, depression_deg_of_r)` that evaluates the identical
   expression in the identical order, and the delegate was checked offline against the
   committed function over 1,200 dates from 2024-01-01 (bit-identical, no difference at any
   date). The alternative — a second copy of the 30-line solar-position routine — was
   rejected because two copies of an ephemeris drift apart, and the alternative of editing
   the numbers inside `astronomical_day_length_h` is what the item forbids and what the
   2026-09-08 pin table (which includes two post-change dates, 2026-11-03 and 2026-12-21)
   would fail on.
2. *The archive with no row edit.* Branch one edits no committed row, so the archive is a
   pre-disposition snapshot rather than a pre-edit one; it was taken anyway because the
   item's description says "archived" and its step 4 asks for the guard, and the file is
   the record the disposition is about.
3. *The 10 s pin for the second generation* rather than the 5 s the first generation uses:
   the fitted depression leaves a ±4.4 s annual sinusoid, so a 5 s pin would trip on the
   fit's own residual rather than on a source shift. The record check keeps its own
   0.017 h (1.02 min) bar untouched.
4. *Per-row, not per-candidate-day, generation selection in `closest_day_margin`.* The
   distinction is unobservable on today's record (both readings give every row the same
   verdict), but per-row is the coherent one: a row was collected at one moment, when the
   source published one generation for all dates. A test pins it by feeding a boundary row
   a value from the other generation, where a per-candidate dispatch finds an exact
   neighbour (best = 0.0) and a per-row one does not (best = 26.5 s).
5. *obs_date as the dispatch key.* The physical selector is when the row was fetched, and
   obs_date is a 0-or-1-day proxy for it (the audit allows that gap, and the record has
   gap-0 rows sampled at 00:xxZ). Both rows bracketing the change are 22:30Z collections,
   so the proxy is exact here; a future shift landing between an early-UTC run and the next
   22:30Z run could mis-dispatch one row. Recorded, not fixed, because tightening the gap
   rule is out of scope for this bundle.

**Files changed.** `tests/test_control.py` (shared `_day_length_h`; `SOURCE_MODEL_CHANGE_OBS_DATE`;
`_V2_DEPRESSION_DEG = -0.84984`; `astronomical_day_length_h_v2`; `source_model_for`;
`source_day_length_h`; `closest_day_margin` on the per-row model; six new tests;
`TestClosestDayMarginLogic` synthesizes with `source_day_length_h`; one behaviour-neutral
type narrowing in `test_it_is_a_control_and_can_never_be_counted` — the pre-existing
`control.__doc__.upper()` on a `str | None` blocked the edit, and `control.fetch_daily.__module__ and`
was a no-op in the same expression), `tests/audit_record.py` (canary on
`source_day_length_h` plus its docstring; one behaviour-neutral narrowing at the
`LEG_REPEAT_EXEMPT` lookup that cleared the same class of pre-existing analyzer blocker,
same assertion and same failure message), `data/annotations.csv`,
`docs/data/annotations.csv`, `data/archive/control_daylength_pre_model_change_2026-11-01.csv`
(new), `.ralph/items.json`, `.ralph/progress.md`. `data/control_daylength.csv` is NOT in the
diff: no row was touched. No `radar.md` or `radar-metrics.md` edit: this is not a round, no
line, tier, pending bullet or round index changed, and the audit's registry freshness test
stays green.

**Failing tests first.** Six tests were added to `tests/test_control.py` before the
implementation and run red (`6 failed, 6 passed`, each new one failing with `NameError` on
`astronomical_day_length_h_v2` / `source_day_length_h`); they went green after. The
margin-helper test was additionally run against the pre-fix per-candidate-day dispatch
restored in-process: `FAIL ... AssertionError: 0.0 not greater than 1.0`.

**Independent review.** `reviewer` (opencode-go/deepseek-v4.1-flash, thinking high) read the
diff plus the record: verdict BLOCK on two P1s, both fixed before the commit. P1-1 —
`closest_day_margin` dispatched per candidate day, contradicting its own docstring and the
annotation that ships with the change (no verdict changes today, but the code did not do
what the record said); fixed with `source_model_for` and the pinning test above. P1-2 — the
archive was untracked, so the annotation's citation would dangle; it is staged with the
commit. Four P2 notes were taken into the annotation row: the double-subtraction clause no
longer equates the removal with the fitted level, the bit-identity claim is stated as the
offline check it was, and the sunrise/sunset pair-sum is relabelled as internal consistency
rather than independent evidence. Two P2s were left as recorded notes: obs_date is a proxy
for fetch time (assumption 5) and the weakest new test (`test_the_generation_switches_…`)
is a boundary pin only, which is its correct shape.

**Verification (all commands run at the commit that closed this item).**

- `python -m pytest tests/ -q` — 342 passed, 34 subtests passed (exit 0; 336 before, the six
  new tests).
- `python -m unittest discover tests -p "lint_*.py"` — Ran 61 tests, OK (exit 0).
- `python tests/lint_no_forbidden_literal.py` — Ran 3 tests, OK (exit 0).
- `python tools/replay.py --check` — exit 0; TOTAL 1271 rows, 0 divergent.
- `python tools/pending.py --check` — exit 0; 6 tagged, 0 overdue, 0 unparseable.
- `node tests/render_smoke.js` — exit 0, "render OK in both languages; no runtime errors,
  no undefined/NaN".
- `python -m unittest discover tests -p "audit_*.py"` — Ran 23 tests, OK (exit 0). The
  astronomy assertion that was red on entry passes; the audit tier is now green, not just
  free of new failures.
- `cmp data/annotations.csv docs/data/annotations.csv` — exit 0.
- `python tools/drift_layer.py` was not re-run: this item changes no line record.

**Next iteration should know.** The comparison site is `source_model_for` /
`source_day_length_h`, so a THIRD published source shift needs its own dated generation
pinned from fresh vendor samples — never an edit to either existing table, and never a
loosened `closest_day_margin` margin. Item 6 (prose) now has its evidence: the measured
offset is NEGATIVE — the recorded day is 3.34-3.44 min SHORTER than the first-generation
model (200.3 s at 2026-10-22 widening to 206.5 s at 2026-10-31), so the
"source-redefinition identification band" in `tests/test_control.py` currently states the
wrong sign and a magnitude band the record contradicts; that band was deliberately left for
item 6. The remaining unfinished items are 6 (prose), 8 (five-row FRED repair, all
preconditions in), 9 (derived-recency audit assertions) and 10 (`AGENTS.md` components
claim); item 8 should run before item 9.

## Iteration 7 — item 8 (bug): the five FRED HTML rows are darkened, archived and the tail re-derived

**Chosen because** `.ralph/plan.md` orders the record-changing group after the damage-stopping
items: "control-line disposition, then the five-row repair". Item 7 (the control line) landed,
item 8 was the next unfinished item, its three preconditions (items 2, 3, 4) were in, and no item
was hard-blocked. Items 6 and 10 are prose-only and allowed "any time after the first item"; item 9
asserts properties this repair produces, so it follows.

**Entry state measured.** All six gates green at HEAD (pytest 342 passed; lint 61 OK; forbidden
literal 3 OK; replay 1271 rows 0 divergent; pending 6 tagged 0 overdue; render smoke exit 0) and the
audit tier 23 tests OK. The two preconditions named by step 1 pass: `python -m pytest tests/test_level.py
-k DriftDateGuard tests/test_collect_loop.py -k "UnusableObsDate or ObsDateProblem"` gave 7 passed.

**Failing test first.** `tests/audit_record.py::TestObservationDatesAreWellFormed` was added and run
before the repair: `python -m unittest discover tests -p "audit_record.py" -k
TestObservationDatesAreWellFormed` failed on exactly five rows — credit_spread, em_corp_oas,
euro_hy_spread, sofr_iorb_spread and vix, all dated 2026-10-22 — each carrying
`'    <link href="https://fonts.googleapis.com/css?family=Open+Sans:300'` in obs_date. Green after
the repair. A second assertion, added after review, pins that every `collect.LINES` file still
declares the obs_date column.

**The repair.** New one-off `tools/repair_fred_html_rows.py` (entirely offline). It refuses to start
when any archive from this repair exists, and also when the 2026-10-22 row no longer carries an
unusable obs_date, so neither a deleted archive nor a re-broken row can lead to a silent second
repair. It archived the five line files byte-identically as
`data/archive/<line>_pre_html_repair_2026-11-01.csv` (`cmp` clean against `git show
HEAD:data/<line>.csv` for all five), rebuilt each 2026-10-22 row through `collect.score_row` with
`raw_value` None, obs_date cleared and the note prefixed
`no reading: source returned an HTML page, not a CSV - not scored :: `, then re-derived every row
dated 2026-10-22 or later oldest-first against the published prior rows, stripping stored verdict
prose through `seedlib.strip_verdict_notes` first. 25 of the 50 tail rows change: the five darkened
rows, plus 20 z-only moves (credit_spread 10-28 6.801 -> 6.860, 10-29 5.336 -> 5.394, 10-30 4.808 ->
4.867; em_corp_oas 10-28 3.635 -> 4.847, 10-30 3.108 -> 3.166, 10-31 3.401 -> 3.459; euro_hy_spread
10-23 6.989 -> 7.036, 10-28 7.740 -> 9.334, 10-29 7.622 -> 7.661, 10-30 6.567 -> 6.606;
sofr_iorb_spread 10-24 0.915 -> 0.941, 10-27 1.880 -> 1.830, 10-28 2.287 -> 2.350, 10-29 3.052 ->
3.201, 10-30 2.286 -> 2.582, 10-31 2.345 -> 2.286; vix 10-27 2.534 -> 2.576, 10-28 1.705 -> 1.733,
10-29 1.041 -> 1.057, 10-31 0.794 -> 0.819). No scored row's trembling or direction flips; the other
25 tail rows re-derive byte-identically.

**Assumptions recorded (ordinary ambiguity).**

1. *`data/summary.csv` is a derived file, not a record file.* The item's steps do not name it, but
   `tools/replay.py --check` audits the summary re-derivation (`summary_bad`) and the phantom reading
   had changed the day's headline. Recomputed from the repaired tier-1 rows and stated in the
   annotation row: 2026-10-22 `1/0/0 -> 0/1/0` (the phantom had been the day's only counted tremble;
   credit_spread is tier-1). No later summary row changes.
2. *History semantics.* "using published prior rows as history" read as: rows before 2026-10-22 are
   untouched and are the history for that row, and each re-derived row is then history for the next —
   the same oldest-first construction `tools/replay.py` uses, which is why `--check` stays at zero.
3. *The captured note is kept, not replaced.* The required prefix is prepended to the stripped
   original note, so what the source actually returned survives as evidence.
4. *A tracked one-off tool is the mechanism*, in the house style of `tools/repair_fred_seed.py`; the
   annotation row is written separately because that is the protocol.

**Derive layer.** The daily derive block was re-run verbatim (`tools/level_layer.py`,
`tools/drift_layer.py`, `tools/stuck_panel.py`, `tools/lean_panel.py`, `tools/episodes.py --markdown >
radar-metrics.md`, `tools/pending.py --markdown >> radar-metrics.md`, `python render.py`) and every
file in `collect.MIRRORED` was re-synced (26 files) plus the annotations row. That also caught the
frozen layers up to their inputs: `data/levels.csv` and `docs/data/stuck.csv` 2026-10-11 ->
2026-10-17, `docs/data/leans.csv` to 2026-10-31. The chokepoint component capture
(`data/components/chokepoint_breadth.csv`, unchanged by this item) has no row after 2026-10-17, so
levels and stuck stop there. That component freeze predates this item, was not caused by it, and is
outside its scope (Scope Out: PortWatch probe results beyond recording them); it is a known open
defect — item 9's assertion (levels newest equals components newest) holds with both at 2026-10-17,
but the served stuck panel stays behind the record until the capture is restored. The annotation row
states this so the regenerated layer is not read as current-through-end-of-record.

**Files changed.** `tools/repair_fred_html_rows.py` (new),
`tests/audit_record.py` (new `TestObservationDatesAreWellFormed`),
`data/{credit_spread,em_corp_oas,euro_hy_spread,sofr_iorb_spread,vix}.csv`,
`data/summary.csv`, `data/annotations.csv`, `data/levels.csv`,
`data/archive/{credit_spread,em_corp_oas,euro_hy_spread,sofr_iorb_spread,vix}_pre_html_repair_2026-11-01.csv`
(new), the matching `docs/data/` mirrors, `docs/data/stuck.csv`, `docs/data/leans.csv`,
`radar-metrics.md`, `charts/{overview,flights,credit_spread,cnh_cny,fed_srf_takeup}.png`,
`.ralph/items.json`, `.ralph/progress.md`. `data/drifts.csv` re-derived byte-identically (the five
dark rows are skipped by the derive guard, so the drop tally fell from 5 to 0 with no row change) and
is not in the diff. No scoring rule or `STABLE_SINCE` change.

**Verification (all commands run at the commit that closed this item).**

- `python -m pytest tests/ -q` — 342 passed, 34 subtests passed (exit 0).
- `python -m unittest discover tests -p "lint_*.py"` — Ran 61 tests, OK (exit 0).
- `python tests/lint_no_forbidden_literal.py` — Ran 3 tests, OK (exit 0).
- `python tools/replay.py --check` — exit 0; TOTAL 1271 rows, 0 divergent, 0 summary days bad.
- `python tools/pending.py --check` — exit 0; "OK — 6 tagged pending item(s), 0 overdue, 0
  unparseable".
- `node tests/render_smoke.js` — exit 0.
- `python -m unittest discover tests -p "audit_*.py"` — Ran 25 tests, OK (exit 0; 23 before, the
  obs_date shape test and its header check).
- `cmp data/annotations.csv docs/data/annotations.csv` — exit 0.
- `python tools/repair_fred_html_rows.py --dry-run` after the repair — exit 1 with the archive
  refusal, proving the one-shot guard.

**Independent review.** `reviewer` (opencode-go/deepseek-v4.1-flash, thinking high) returned OK with
notes, no P0/P1. All six P2s were addressed before the commit: the annotation sentence that called all
25 changed rows "z-only" (false for the five darkened rows) was split into 20 z-only later rows plus
the five darkened rows; the obs_date audit gained the column-declaration assertion so a header loss
cannot make a file skip silently; the non-recursive `data/*.csv` glob and the deliberate
`data/archive/` exclusion are documented in the test docstring; the annotation now states that levels
and stuck stop at 2026-10-17 because of the component capture; the six untracked artifacts the
annotation cites are staged with the record change; and the tool docstring states that recovery from
an aborted run is manual because the guard will not resume. The reviewer's suggestion to give the
component freeze a `radar.md` pending tripwire was not taken: that is registry/round work outside
this item's scope, recorded above instead. One note left as-is: the repair note prefix ("source
returned an HTML page, not a CSV") differs from what `collect.py` now writes for the same class
("unusable observation date") — both are accurate and the annotation quotes the prefix verbatim.

**Next iteration should know.** The five rows are now dark with a stated reason, the archives hold the
pre-repair files, and `replay --check` is at zero. `data/summary.csv` 2026-10-22 reads 0/1/0 and the
served `docs/data/` copies are byte-equal again. The remaining unfinished items are 6 (prose), 9
(derived-recency assertions) and 10 (the `AGENTS.md` components claim). Item 9 should be checked
against the regenerated layer: its levels-vs-components assertion holds at 2026-10-17, and the
chokepoint component freeze after that date is the open defect recorded above, not a derived-layer
bug.

## Iteration 8 — item 9 (functional): the derived layers are checked against their own inputs

**Chosen because** `.ralph/plan.md` puts the derived-recency assertions fourth, after the
record-changing items: item 8 regenerated the layers, so the properties to assert now exist.
Items 1-5, 7 and 8 had landed; item 9 was the next unfinished item and no item was
hard-blocked. Items 6 and 10 are prose-only and remain.

**Entry state measured.** All six gates green at HEAD (pytest 342 passed; lint 61 OK;
forbidden literal 3 OK; replay 1271 rows, 0 divergent; pending 6 tagged, 0 overdue; render
smoke exit 0); audit tier 25 tests OK. The three inputs and outputs on the committed record:
components newest 2026-10-17, levels newest 2026-10-17 (hold rows for Kerch and Hormuz),
stuck newest 2026-10-17, summary newest 2026-10-31, leans newest 2026-10-31.

**Red evidence before the assertions were accepted (scratch script, not committed).** The
pre-repair freeze is committed at `0b12b49`: levels 2026-10-11 against components 2026-10-17,
leans 2026-10-21 against summary 2026-10-31, stuck 2026-10-11 against levels 2026-10-11.
Running the new class with its class-attribute paths pointed at that tree: levels red
(`'2026-10-11' != '2026-10-17'`), leans red (`'2026-10-21' != '2026-10-31'`), stuck green
because stuck did match its own (frozen) input — the correct division of responsibility, the
levels check is what catches that freeze. Running against live copies with the newest day
removed, one file at a time: levels red (`2026-10-16` vs the replayed `2026-10-17`), stuck red
(`2026-10-16` vs `2026-10-17`), leans red (`2026-10-30` vs `2026-10-31`).

**Implementation.** New audit-tier class `TestDerivedLayersAreCurrent` in
`tests/audit_record.py`, three tests, one per layer. The level check replays
`level_layer.walk` over `data/components/chokepoint_breadth.csv` and asserts that
`data/levels.csv`'s newest date equals the last date that replay emits; the stuck check
asserts `docs/data/stuck.csv`'s newest date equals the last `open`/`hold` date in
`data/levels.csv` (`build_panel` drops only the `clear` row); the lean check asserts
`docs/data/leans.csv`'s newest date equals the newest `data/summary.csv` day on which a
tier-1 line (`TIER` absent = 1) trembles in its own alarm direction, through the shared
`collect.counts_as_tremble`. No production code changed.

**Assumption recorded (ordinary ambiguity, review-driven).** The item's step 1 says the
levels equality is "evaluated only when an open state exists on that newest component date".
The delivered check compares against the layer's own last emitted event date instead, with no
open-state gate. The gate exists to avoid a false red when the layer legitimately stops
early (level_layer writes nothing after a state closes), and the exact last-emitted date has
that same protection without two blind spots the independent review identified: when every
open strait has gone stale-unserved, and when the newest input day closes the only state, the
gate would skip exactly where a freeze could hide. A divergence under the exact form can only
mean the file was not regenerated from the code and record in the tree. The trade-off is
recorded in the class docstring: a retune of `level_layer`'s thresholds without regenerating
`data/levels.csv` reds the audit, which is the honest signal.

**Second decision.** The leans expectation restates the reporter's row rule
(`lean_panel.build_panel`) rather than calling it, so a deliberate rule change in the
reporter cannot silently move the audit's own definition of "current". The docstring states
the two are one invariant and the assertion message names both causes (a stale file, or a
rule that moved without this check). The reviewer's alternative (bind to `build_panel` with a
stub classifier) was considered and not taken, for that reason.

**Out of scope by decision.** `data/drifts.csv` is not checked: it records open/clear events
and has carried none since 2023-11-19, so a recency check there would skip unconditionally
today, and `tools/drift_layer.py` exits non-zero on a crash, so a freeze in that tool already
reds the derive step. The class docstring says so.

**Absence contract.** `tests/audit_record.py` treats a missing tracked derived file as a
defect; `tests/audit_public_surface.py` keeps its historical skip when
`docs/data/leans.csv` is absent. That asymmetry is deliberate (one owns recency and the file
is tracked, the other owns row shape and keeps its old tolerance) and is now stated in both
docstrings; the stale "so nothing else checks it" sentence in `audit_public_surface.py` was
corrected.

**Files changed.** `tests/audit_record.py` (new class plus its local-import helpers),
`tests/audit_public_surface.py` (two docstring corrections and a behaviour-neutral import
cleanup: the bare `import lean_panel` became a test-local `from tools import lean_panel`,
clearing its unresolved-import diagnostic, and ruff's single blank line was added to the
import block in both files), `.ralph/items.json`, `.ralph/progress.md`. No `data/` file, no
derived file, no `radar-metrics.md` change: this item asserts properties, it does not
regenerate.

**Independent review.** `reviewer` (opencode-go/deepseek-v4.1-flash, thinking high) returned
OK with notes, no P0/P1, and five P2s. Taken: the docstring overclaim ("every served derived
layer"; levels is not served and drifts is a fourth layer) reworded with the out-of-scope
reason; the two skip holes replaced by the exact last-emitted date; the leans message widened
to name rule drift; the `audit_public_surface.py` staleness corrected; the garbled
local-import comment and the imprecise "day before the last clear" prose fixed. The fifth
(restate vs bind) is the deliberate choice recorded above.

**Verification (all commands run at the commit that closed this item).**

- `python -m pytest tests/ -q` — 342 passed, 34 subtests passed (exit 0).
- `python -m unittest discover tests -p "lint_*.py"` — Ran 61 tests, OK (exit 0).
- `python tests/lint_no_forbidden_literal.py` — Ran 3 tests, OK (exit 0).
- `python tools/replay.py --check` — exit 0; TOTAL 1271 rows, 0 divergent, 0 summary days bad.
- `python tools/pending.py --check` — exit 0; "OK — 6 tagged pending item(s), 0 overdue,
  0 unparseable".
- `node tests/render_smoke.js` — exit 0.
- `python -m unittest discover tests -p "audit_*.py"` — Ran 28 tests, OK (exit 0; 25 before,
  the three new tests). Run verbosely for the new class, all three report `ok`, none `skipped`,
  on the committed record.
- `cmp data/annotations.csv docs/data/annotations.csv` — exit 0 (unchanged by this item).

**Next iteration should know.** Items 6 (two prose statements in `tests/test_control.py` and
`radar.md`) and 10 (the `AGENTS.md` components claim) remain; both are prose-only. Item 6's
evidence is already in the ledger (iteration 6: the measured offset is negative, 200.3-206.5 s,
so the "source-redefinition identification band" states the wrong sign and a band the record
contradicts). The new audit class is coupled on purpose to `level_layer.walk`'s parameters and
`lean_panel.build_panel`'s row rule: a change to either must move this check or regenerate the
derived file in the same commit, or the audit reds.

## Iteration 9 — item 6 (docs): the redefinition band states no sign, and the equinox item points at R28

**Chosen because** `.ralph/plan.md` allows prose-only items "at any time after the first item"
and item 6 is the next unfinished item in `.ralph/items.json` (items 1-5 and 7-9 landed; only 6
and 10 remain). Its evidence was already in the ledger from iteration 6, and no item was
hard-blocked.

**Entry state measured.** All six gates green at HEAD (pytest 342 passed; lint 61 OK; forbidden
literal 3 OK; replay 1271 rows, 0 divergent; pending 6 tagged, 0 overdue; render smoke exit 0)
and the audit tier 28 tests OK.

**Correction 1 — the identification band (`tests/test_control.py`).** The
`astronomical_day_length_h` docstring carried "The source-redefinition tell: a UNIFORM
+3.5-4.5 minute offset appearing on every row from one date onward ...". Iteration 6 measured
the actual shift: every row from 2026-10-22 records a day 200.3-206.5 s (3.34-3.44 min)
SHORTER than the first-generation model for its claimed obs_date. So the quoted band has the
wrong sign and a magnitude range the record falls outside. The paragraph now names only the
shape (a uniform offset — the same direction and size on every row from one date onward) and
states that the direction and size belong to that particular shift and are measured from the
record, so no band is quoted. The consecutive-jump sentence (0.15 h/day will not fire on a
uniform shift) and the recovery rule (annotation plus a forward-only bump, never a rewrite) are
unchanged. The following paragraph, which correctly records that the source published a shorter
day from obs_date 2026-10-21, was left alone: it describes the measured second generation, not
the identification band.

**Correction 2 — the equinox item's reference (radar.md and tests/test_control.py).** The
equinox false positive was tied to "issue #3" in three places: radar.md's Round 27 trailing
separator, radar.md's Round 28 item 1, and
`tests/test_control.py::TestReproducesTheSourcesPublishedModel`'s docstring. `gh issue view 3`
confirms GitHub issue #3 is `tremor: the daily collection is failing`, state OPEN — the failure
alarm issue, not a canary item. All three now point at the R28 canary fix instead of the issue
number:
- Round 27: `(Separate/open at this round: control_daylength canary false positive near the
  equinox — CLOSED by the R28 canary fix below.)`
- Round 28: `the equinox false positive (the R27 separate item) is CLOSED`
- the test docstring: `This is the test the R28 canary fix added: ...`

**Assumption recorded (ordinary ambiguity).** `radar-log.md` still carries "issue #3" in its
Round 27 narrative (line 740) and Round 28 item 1 heading (line 746). The item names only
`radar.md` and `tests/test_control.py`, and `radar-log.md` is the published per-round ledger, so
the correction was NOT extended to it: rewriting published history was judged worse than the
remaining stale identifier, which is now wrong in one place and right (round-referenced)
everywhere the registry itself routes a reader. Recorded here so a later round can decide
whether to supersede it in a new log entry rather than edit the old one.

**No failing test first, and why.** The item is prose only: no code path, no data row, no
assertion changes, so no behaviour change exists to pin with a failing test, and the item's
steps ask for none. The step-3 requirement (test gate tier plus lint tier) is the verification,
and every gate in the runtime contract was run in addition.

**Files changed.** `tests/test_control.py` (the band paragraph rewritten; one docstring
reference retargeted), `radar.md` (Round 27 trailer and Round 28 item 1 retargeted),
`.ralph/items.json`, `.ralph/progress.md`. No `data/` file, no derived layer, no annotation row
and no `radar-metrics.md` change: this item changes no line, tier, pending bullet or round
count, so the generated metrics are unchanged and the freshness audit stays green.

**Verification (all commands run at the commit that closed this item).**

- `python -m pytest tests/ -q` — 342 passed, 34 subtests passed (exit 0).
- `python -m unittest discover tests -p "lint_*.py"` — Ran 61 tests, OK (exit 0).
- `python tests/lint_no_forbidden_literal.py` — Ran 3 tests, OK (exit 0).
- `python tools/replay.py --check` — exit 0; TOTAL 1271 rows, 0 divergent.
- `python tools/pending.py --check` — exit 0; "OK — 6 tagged pending item(s), 0 overdue,
  0 unparseable".
- `node tests/render_smoke.js` — exit 0, "render OK in both languages".
- `python -m unittest discover tests -p "audit_*.py"` — Ran 28 tests, OK (exit 0). Not a gate
  for this bundle; run as evidence that the prose edits touched no audited surface.
- `cmp data/annotations.csv docs/data/annotations.csv` — exit 0 (files unchanged).
- `grep -rn "3\.5-4\.5\|+3\.5" tests/test_control.py radar.md radar-log.md
  fetchers/control_daylength.py tests/audit_record.py` — no match, so the band is gone from
  every file that could restate it.
- `grep -rn "issue #3"` outside `internal/` and `.ralph/` — only `radar-log.md` lines 740/746
  remain, the recorded deliberate exclusion above.

**Next iteration should know.** Only item 10 remains: the `AGENTS.md` section 4 sentence that
claims the scoring path must never read `data/components/`, to be replaced by the actual seam
(`score_row`, `normalize.judge`, replay never read them; `tests/test_side_channel.py` binds it).
It is prose-only like this one and its steps ask for the lint tier plus the public-surface and
side-channel tests. `radar-metrics.md` was not regenerated here and does not need to be unless a
later item changes a line file, pending bullet or round entry.

## Iteration 10 — item 10 (docs): AGENTS.md names the seam the scoring decision actually has

**Chosen because** `.ralph/plan.md` allows prose-only items "at any time after the first item";
item 10 is the last unfinished item (items 1-9 landed, no item was hard-blocked).

**Entry state measured.** All six gates green at HEAD (pytest 342 passed; lint 61 OK; forbidden
literal 3 OK; replay 1271 rows 0 divergent; pending 6 tagged 0 overdue; render smoke exit 0),
audit tier 28 tests OK, and the item-named tests green: `test_side_channel` 6 OK,
`audit_public_surface` 3 OK, `test_components` 3 OK.

**The false claim, measured.**

- `collect.py:452` reads `data/components/<line>.csv` inside `write_components` (merging the rows
  it is about to append). `grep -n "_read_rows(" collect.py` shows exactly three call sites: that
  component read at `:452`, a line CSV at `:468` and the summary at `:558`. So "the scoring path
  (`collect.py`, `core/normalize.py`) must never read them" was literally false about
  `collect.py`.
- `tests/test_side_channel.py` asserts only `read_intraday`/`sample_intraday` and the served
  allow-list; it binds the intraday channel and the gate/audit tier boundary, not the components
  rule. The components seam is bound by `tests/test_components.py`: `core/normalize.py` must not
  name `components` at all, and `write_components`' body must not name `score_row`/`LINE_HEADER`.

**The replacement (`AGENTS.md` section 4, third bullet).** The scoring DECISION — `score_row`,
`normalize.judge`, `tools/replay.py` — never reads either channel. Verified before writing:
`score_row` takes no `components` argument, and `grep -c "components"` is 0 in
`core/normalize.py` and `tools/replay.py`. The paragraph states that the one component-file read
in `collect.py` is `write_components` merging the rows it is about to append, that no component
value reaches `score_row`, and that the derived level layer (`tools/level_layer.py`, whose
`SOURCE` is `data/components/chokepoint_breadth.csv`) is the intended consumer. It closes by
naming which test binds which half: `tests/test_components.py` the components side (the
normalizer never names a breakdown; a component write cannot touch a scored row), and
`tests/test_side_channel.py` the intraday side plus the gate/audit tier boundary.

**Assumption recorded (ordinary ambiguity, deviation from the step's letter).** Step 1 says the
replacement should state "that `tests/test_side_channel.py` binds that seam". That is false for
components — the very class of false statement the item exists to remove, and the sentence the
equivalent plan row marks as "must not drop which part the test binds". Resolved conservatively:
`tests/test_side_channel.py` is named, but for the intraday side and the tier boundary it
actually binds, and `tests/test_components.py` is named for the components side. Naming only
`test_side_channel.py` would have replaced one literally false sentence with another.

**No failing test first, and why.** Prose only: no code path, no data row, no assertion changes,
so no behaviour change exists to pin, and the item's steps ask for none (`python
-m unittest discover tests -p "lint_*.py"` plus the public-surface and side-channel tests are the
step-2 verification). Every runtime-contract gate was run in addition.

**Files changed.** `AGENTS.md` (section 4, third bullet: 2 lines replaced by 8),
`.ralph/items.json`, `.ralph/progress.md`. No `data/` file, no derived layer, no annotation row
and no `radar-metrics.md` change: no line, tier, pending bullet or round changed.

**Verification (all commands run at the commit that closed this item).**

- `python -m pytest tests/ -q` — 342 passed, 34 subtests passed (exit 0).
- `python -m unittest discover tests -p "lint_*.py"` — Ran 61 tests, OK (exit 0).
- `python tests/lint_no_forbidden_literal.py` — Ran 3 tests, OK (exit 0).
- `python tools/replay.py --check` — exit 0; TOTAL 1271 rows, 0 divergent.
- `python tools/pending.py --check` — exit 0; "OK — 6 tagged pending item(s), 0 overdue,
  0 unparseable".
- `node tests/render_smoke.js` — exit 0.
- `python -m unittest discover tests -p "test_side_channel.py"` — Ran 6 tests, OK (exit 0).
- `python -m unittest discover tests -p "test_components.py"` — Ran 3 tests, OK (exit 0).
- `python -m unittest discover tests -p "audit_public_surface.py"` — Ran 3 tests, OK (exit 0).
- `python -m unittest discover tests -p "audit_*.py"` — Ran 28 tests, OK (exit 0). Not a gate for
  this bundle; run as evidence that a prose edit touched no audited surface.
- `cmp data/annotations.csv docs/data/annotations.csv` — exit 0 (files unchanged).
- `grep -rn "\bI\b\|\bwe\b\|\bour\b\|\bmy\b" AGENTS.md` — the only match is the rule statement
  in section 0.2 itself, so the new prose is impersonal.

**Next iteration should know.** All ten items in `.ralph/items.json` are `passes: true` and every
runtime-contract gate is green. The components rule as written is now checkable against two
tests: `tests/test_components.py` owns the components half and `tests/test_side_channel.py` owns
the intraday half, so an edit to either invariant must move the named test with it. The
`write_components` docstring in `collect.py` still says "no scoring code may read it" while that
function reads the file it appends to; the sentence is defensible as a rule about the verdict
(and is outside this item's file scope), but a later round may want the same precision applied
there.
