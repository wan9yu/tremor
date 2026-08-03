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


def merge(history, live_rows, import_note):
    """Plan a merged series: ``([(date, raw, note, obs)], dropped_reports)``.

    ``history``: [(obs_date, value)] oldest-first, from the source archive.
    ``live_rows``: previously published row dicts, in file order.
    ``import_note``: callable (obs_date, value) -> source_note for an import.
    """
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
        holder = live_by_date.get(obs)
        if holder is None:
            plan[obs] = (float(value), import_note(obs, value), obs)
        elif obs in republish_dates:
            # The stale republish's observation lives elsewhere in the file;
            # the archive observation does not. The observation wins the date.
            dropped.append(f"live republish row {obs} yields its date to the "
                           f"archive observation (its own observation is "
                           f"recorded on an earlier row)")
            plan[obs] = (float(value), import_note(obs, value), obs)
        else:
            dropped.append(f"archive observation {obs} not imported: the date "
                           f"is held by a published "
                           + ("dark" if holder.get("raw_value") in (None, "")
                             else "first-occurrence") + " row")
    ordered = [(d, *plan[d]) for d in sorted(plan)]
    return ordered, dropped


def score_series(plan, weekly_cycle=False):
    """Score a merged plan oldest-first; returns the full row list."""
    out = []
    for date, raw, note, obs in plan:
        out.append(collect.score_row(date, raw, note, obs, out,
                                     weekly_cycle=weekly_cycle))
    return out


def read_line(line):
    """Published rows of ``data/<line>.csv``; [] when the line has none yet."""
    return collect._read_rows(os.path.join(collect.DATA, line + ".csv"))


def run_seed(mod, history, import_note, dry=False):
    """The whole seeder tail: merge, disclose, archive, re-score, write, report.

    Takes the fetcher MODULE, not a line name, so the re-score reads
    ``WEEKLY_CYCLE`` exactly as the live collector does — a parameter a
    hand-rolled seeder has to remember, at a seam that has already bitten
    once. Each seeder is left with only what genuinely differs: acquiring the
    history and wording the import note. Returns the written rows, or None on
    a dry run.
    """
    live = read_line(mod.LINE)
    plan, dropped = merge(history, live, import_note)
    print(f"  {mod.LINE}: {len(history)} archived observations "
          f"{history[0][0]}..{history[-1][0]}; {len(live)} live rows "
          f"-> {len(plan)} merged rows")
    for d in dropped:
        print(f"    note: {d}")
    if dry:
        return None
    archive_current(mod.LINE, "preseed")
    out = score_series(plan, weekly_cycle=getattr(mod, "WEEKLY_CYCLE", False))
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
