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
