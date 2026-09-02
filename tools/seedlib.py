"""Shared machinery for the archive seeders.

THE MERGE RULE, learned the hard way. The first FRED seed keyed the live rows
by observation date and kept only rows that had one — which silently deleted 26
published rows across three lines: every dark day (no observation to key by),
every stale republish after the first (last-one-wins in a dict), and it let an
archive observation collide with a published row on the same date, leaving two
rows dated 2026-07-14. A seed exists to DEEPEN a line's history, and the one
thing it must never do is edit the part of the record that was already
published. So the rule, in order:

  1. Every live row keeps its own date — dark days, stale republishes, all of
     them. They are published record.
  2. An archive observation already carried by a live row is not imported;
     the live row IS that observation's record.
  3. An uncovered archive observation is imported at its own observation date.
     If a live row occupies that date, whichever carries information the other
     lacks wins: a live stale-republish (its observation lives elsewhere in the
     file) yields to the import; a live first-occurrence or dark row keeps the
     date and the import is dropped. Either way the seeder must say so.

Rows are then re-scored strictly oldest-first through ``collect.score_row``,
so no row is ever judged against readings from its own future, and any verdict
notes the old rows carried are stripped first — the judge appends fresh ones.
"""
import os
import re
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import collect

IMPORT_MARK = " [archive import: scored retroactively, not a live reading]"

# Notes appended by normalize.judge; they describe the OLD verdict and must not
# survive a re-score, or a row can end up saying "stale" while its status says
# scoring — seven rows did exactly that after the first seed. The suppressed
# detail contains one nested bracket pair ("range [lo, hi] (n=..)"), so the
# pattern allows a level of nesting rather than stopping at the first "]".
_VERDICT_NOTES = re.compile(
    r" \[(?:stale: observation already recorded"
    r"|suppressed: (?:[^\[\]]|\[[^\]]*\])*)\]")


def strip_verdict_notes(note):
    return _VERDICT_NOTES.sub("", note or "")


def merge(history, live_rows, import_note, row_date=None):
    """Plan a merged series: ``([(date, raw, note, obs)], dropped_reports)``.

    ``history``: [(obs_date, value)] oldest-first, from the source archive.
    ``live_rows``: previously published row dicts, in file order.
    ``import_note``: callable (obs_date, value) -> source_note for an import.
    ``row_date``: callable obs_date -> row_date, for a source that publishes
        an observation days after it happened (default: the row is dated on
        its own observation). The observation itself is never altered.
    """
    at = row_date or (lambda obs: obs)
    live_by_date = {}
    covered = set()          # observations some live row already records
    republish_dates = set()  # live rows that repeat an observation seen earlier
    for row in live_rows:
        live_by_date[row["date"]] = row
        obs = row.get("obs_date") or ""
        if row.get("raw_value") and obs:
            if obs in covered:
                republish_dates.add(row["date"])
            covered.add(obs)

    dropped = []
    plan = {}
    for date, row in live_by_date.items():
        raw = row.get("raw_value")
        plan[date] = (float(raw) if raw not in (None, "") else None,
                      strip_verdict_notes(row.get("source_note", "")),
                      row.get("obs_date") or "")
    for obs, value in history:
        if obs in covered:
            continue  # a live row is that observation's record
        # A seeded day may be DARK: the source answered, and the fetcher's own
        # integrity rules refuse to read a world number out of that answer. The
        # seed must be able to say so, or it would either fabricate a value the
        # live fetcher would never write, or drop a day it can explain.
        raw = None if value is None else float(value)
        holder = live_by_date.get(at(obs))
        if holder is None:
            plan[at(obs)] = (raw, import_note(obs, value), obs)
        elif at(obs) in republish_dates:
            # The stale republish's observation lives elsewhere in the file;
            # the archive observation does not. The observation wins the date.
            dropped.append(f"live republish row {at(obs)} yields to archive "
                           f"observation {obs} (the republish's own "
                           f"observation is recorded on an earlier row)")
            plan[at(obs)] = (raw, import_note(obs, value), obs)
        else:
            dropped.append(f"archive observation {obs} not imported: row "
                           f"{at(obs)} is held by a published "
                           + ("dark" if holder.get("raw_value") in (None, "")
                             else "first-occurrence") + " row")
    ordered = [(d, *plan[d]) for d in sorted(plan)]
    return ordered, dropped


def score_series(plan, mod):
    """Score a merged plan oldest-first through ``mod``'s own scoring options."""
    opts = collect.scoring_attrs(mod)
    out = []
    for date, raw, note, obs in plan:
        out.append(collect.score_row(date, raw, note, obs, out, **opts))
    return out


def read_line(line):
    """Published rows of ``data/<line>.csv``; [] when the line has none yet."""
    return collect._read_rows(os.path.join(collect.DATA, line + ".csv"))


def rerun_is_safe():
    """Why a seeder can simply be RE-RUN, and must never be hand-restored.

    ``merge`` preserves every published row and imports only observations no
    row already carries, so running a seeder twice is idempotent: the second
    run finds every observation covered, changes nothing, and keeps whatever
    the daily collector has added since.

    RESTORING THE PRE-SEED ARCHIVE FIRST IS NOT. That archive was captured at
    the moment of the FIRST seed, so anything collected since — a live row the
    daily run wrote yesterday — is not in it, and copying it back deletes that
    row before the merge ever sees it. It happened on 2026-08-04: the
    net_outages re-seed silently dropped the 08-04 live reading, recovered
    from git. The seeders never ask for a restore; nothing in this module does
    one; do not do it by hand.
    """
    return True


class SeedWouldLoseRows(RuntimeError):
    """Raised when a seed plan holds fewer rows than the published record.

    A seeder rewrites a whole line file. The record is forward-only, so a plan
    that is shorter than what is already published is not a re-seed, it is data
    loss — and it has happened: a PortWatch re-run once truncated two lines and
    overwrote their archives twelve minutes after they were created.
    """


def check_no_loss(line, live_rows, planned_rows):
    if planned_rows < live_rows:
        raise SeedWouldLoseRows(
            f"{line}: the plan holds {planned_rows} rows but {live_rows} are already "
            f"published; a seed may never drop a published row")


def run_seed(mod, history, import_note, dry=False, row_date=None):
    """The whole seeder tail: merge, disclose, archive, re-score, write, report.

    Takes the fetcher MODULE, not a line name, so the re-score reads the same
    per-line options the live collector does — via ``collect.scoring_attrs``,
    which is the single place that knows which module attributes affect a
    verdict. This function used to forward one of them by hand and the seam bit
    twice: once when a seeder forgot ``WEEKLY_CYCLE``, and again when
    ``QUANTUM`` was added to two callers and not this one, costing the
    net_outages seed 34 unscoreable rows. Each seeder is left with only what
    genuinely differs: acquiring the history and wording the import note.
    Returns the written rows, or None on a dry run.
    """
    live = read_line(mod.LINE)
    plan, dropped = merge(history, live, import_note, row_date=row_date)
    check_no_loss(mod.LINE, len(live), len(plan))
    print(f"  {mod.LINE}: {len(history)} archived observations "
          f"{history[0][0]}..{history[-1][0]}; {len(live)} live rows "
          f"-> {len(plan)} merged rows")
    for d in dropped:
        print(f"    note: {d}")
    if dry:
        return None
    archive_current(mod.LINE, "preseed")
    out = score_series(plan, mod)
    collect.write_line(mod.LINE, out)
    print(f"    -> {len(out)} rows, {sum(1 for r in out if r['z_score'])} scored, "
          f"{sum(int(r['trembling']) for r in out)} trembles, "
          f"last status={out[-1]['status']}")
    return out


def archive_current(line, suffix):
    """Copy ``data/<line>.csv`` to ``data/archive/<line>_<suffix>.csv``."""
    src = os.path.join(collect.DATA, line + ".csv")
    if not os.path.exists(src):
        return None
    archive = os.path.join(collect.DATA, "archive")
    os.makedirs(archive, exist_ok=True)
    dst = os.path.join(archive, f"{line}_{suffix}.csv")
    n = 2
    while os.path.exists(dst):  # an archive is a record; never clobber one
        dst = os.path.join(archive, f"{line}_{suffix}{n}.csv")
        n += 1
    shutil.copy2(src, dst)
    return dst
