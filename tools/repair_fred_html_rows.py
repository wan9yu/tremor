"""One-off: repair the five 2026-10-22 rows that scored a FRED HTML error page.

On 2026-10-22 every FRED-sourced line asked the API for an observation and was
handed an HTML page — the keyless fallback and the keyed endpoint alike. The
reader of the day took the first comma-separated field of the page as the
observation date and the number it found in the body as the reading, so five
rows were PUBLISHED as scored measurements of a value the source never
reported:

    line              raw   z           what the page actually was
    credit_spread     400   4658.842    an error page, no observation
    em_corp_oas       400   6231.881    an error page, no observation
    euro_hy_spread    400   3727.871    an error page, no observation
    sofr_iorb_spread    0      0.915    400.0 - 400.0, two error pages
    vix               400    285.834    an error page, no observation

``core/fred.py`` now refuses a body whose first column is not a date and
``collect.py`` refuses an unusable observation date at collection time, so the
class cannot recur (the same close-out landed both guards). This tool repairs
the rows the old reader wrote and re-derives the tail those rows contaminated:
the rolling baseline behind every later row counted 400 as a reading.

ENTIRELY OFFLINE, forward-only, and one-shot:

  * the five line files are archived first as
    ``data/archive/<line>_pre_html_repair_2026-11-01.csv``; the tool REFUSES to
    start when any of those archives already exists, because a second run is a
    new decision, not a rerun. It also refuses when the 2026-10-22 row no
    longer carries an unusable obs_date, so a deleted archive cannot lead to a
    silent second repair;
  * the 2026-10-22 row is rebuilt through ``collect.score_row`` with
    ``raw_value`` None, its obs_date cleared, and a note that states why;
  * only rows dated 2026-10-22 or later are re-scored, oldest first, against
    the published rows that preceded them — their stored verdict prose is
    stripped with ``seedlib.strip_verdict_notes`` before re-scoring so nothing
    is duplicated. Earlier rows keep the verdict the instrument of their day
    produced: that is the forward-only rule;
  * ``data/summary.csv`` is re-derived for the same dates from the repaired
    tier-1 rows, because the 2026-10-22 headline counted the phantom reading
    (and the tail counts rest on the repaired verdicts);
  * every file in ``collect.MIRRORED`` is synced to ``docs/data/`` in the same
    run, since the record is served from there.

The annotation row in ``data/annotations.csv`` is written by hand, not here: a
rewritten verdict without a written reason is the thing the protocol forbids.
The derive layer (levels, drifts, panels, charts, radar-metrics) is regenerated
afterwards by running the daily workflow's derive block.

IF A RUN ABORTS AFTER ARCHIVING AND BEFORE THE LAST WRITE, restore the affected
line files from ``data/archive/`` before doing anything else: the guard below
will refuse a second run by design, so this tool cannot resume a half-finished
repair and recovery is manual.

    python tools/repair_fred_html_rows.py --dry-run
    python tools/repair_fred_html_rows.py
"""
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import seedlib

import collect
from core import normalize
from fetchers import credit_spread, em_oas, euro_hy_spread, sofr_iorb, vix

REPAIRED = [credit_spread, em_oas, euro_hy_spread, sofr_iorb, vix]
REPAIR_DATE = "2026-10-22"
ARCHIVE_SUFFIX = "pre_html_repair_2026-11-01"
NOTE_PREFIX = "no reading: source returned an HTML page, not a CSV - not scored :: "


def archive_path(mod):
    return os.path.join(collect.DATA, "archive",
                        f"{mod.LINE}_{ARCHIVE_SUFFIX}.csv")


def check_preconditions():
    """Refuse before writing anything: one shot, and only on the broken rows."""
    existing = [archive_path(mod) for mod in REPAIRED if os.path.exists(archive_path(mod))]
    if existing:
        raise SystemExit(
            "refusing to start: an archive from this repair already exists:\n  "
            + "\n  ".join(os.path.basename(p) for p in existing)
            + "\n(a second run is a new decision with a new annotation row, "
              "not a rerun of this one)")
    for mod in REPAIRED:
        rows = seedlib.read_line(mod.LINE)
        holders = [r for r in rows if r["date"] == REPAIR_DATE]
        if len(holders) != 1:
            raise SystemExit(f"{mod.LINE}: expected one row dated {REPAIR_DATE}, "
                             f"found {len(holders)}")
        row = holders[0]
        if not row["obs_date"] or collect.is_strict_date(row["obs_date"]):
            raise SystemExit(f"{mod.LINE}: the {REPAIR_DATE} row carries obs_date "
                             f"{row['obs_date']!r}, which is not the unusable "
                             f"value this repair exists to remove — refusing to "
                             f"re-score a row that may already be repaired")


def rederive(mod, rows):
    """``rows`` with every row dated REPAIR_DATE or later re-scored.

    The published prior rows are the history, exactly as ``tools/replay.py``
    builds it, so the rewritten tail is what the current scorer says about the
    record with the phantom reading removed. Nothing before REPAIR_DATE moves.
    """
    first = next(i for i, r in enumerate(rows) if r["date"] >= REPAIR_DATE)
    out = list(rows[:first])
    opts = collect.scoring_attrs(mod)
    for row in rows[first:]:
        note = seedlib.strip_verdict_notes(row["source_note"])
        raw = row["raw_value"]
        if raw not in (None, ""):
            try:
                raw = float(raw)
            except ValueError:
                raise SystemExit(
                    f"{mod.LINE} {row['date']}: stored raw_value {raw!r} is not a "
                    f"number — refusing to re-score a corrupt record") from None
        obs = row["obs_date"] or ""
        if row["date"] == REPAIR_DATE:
            raw = None
            obs = ""
            note = NOTE_PREFIX + note
        out.append(collect.score_row(row["date"], raw, note, obs, out, **opts))
    return out


def verdict(row):
    return (row["z_score"], row["trembling"], row["direction"], row["status"])


def rebuild_summary(since):
    """Re-derived summary rows on/after ``since``; ``(rows, changes)``.

    The headline counts tier-1 rows only, and their statuses are the repaired
    verdicts just written. Same reconstruction ``tools/replay.py`` audits, so
    ``--check`` stays at zero divergence instead of reporting the stale counts.
    """
    summary = collect._read_rows(os.path.join(collect.DATA, "summary.csv"))
    by_date = {}
    for mod in collect.LINES:
        if getattr(mod, "TIER", 1) != 1:
            continue
        for row in collect._read_rows(os.path.join(collect.DATA, mod.LINE + ".csv")):
            by_date.setdefault(row["date"], []).append((mod, row))
    changes = []
    for srow in summary:
        if srow["date"] < since:
            continue
        entries = by_date.get(srow["date"], [])
        derived = {
            "trembling_count": str(sum(
                1 for mod, row in entries if collect.counts_as_tremble(row, mod))),
            "dark_count": str(sum(
                1 for _, row in entries if row["status"] == normalize.STATUS_DARK)),
            "blind_count": str(sum(
                1 for _, row in entries if row["status"] in normalize.BLIND_STATUSES)),
        }
        stored = {k: (srow.get(k) or "0") for k in derived}
        if stored != derived:
            changes.append((srow["date"], stored, derived))
            srow.update(derived)
    return summary, changes


def mirror():
    for name in sorted(collect.MIRRORED):
        src = os.path.join(collect.DATA, name)
        if os.path.exists(src):
            shutil.copy2(src, os.path.join(collect.DOCS_DATA, name))
    return sorted(collect.MIRRORED)


def main(argv):
    dry = "--dry-run" in argv
    check_preconditions()

    planned = {}
    for mod in REPAIRED:
        before = seedlib.read_line(mod.LINE)
        after = rederive(mod, before)
        changed = [(b["date"], verdict(b), verdict(a))
                   for b, a in zip(before, after, strict=True)
                   if verdict(b) != verdict(a)]
        planned[mod.LINE] = (before, after, changed)
        print(f"{mod.LINE}: {len(before)} rows, {len(changed)} verdict(s) change")
        for date, was, now in changed:
            print(f"  {date}  z {was[0] or '—':>9} {was[3]:<11} -> "
                  f"z {now[0] or '—':>9} {now[3]}")
    if dry:
        print("\n(dry run — nothing written)")
        return 0

    for mod in REPAIRED:
        dst = archive_path(mod)
        shutil.copy2(os.path.join(collect.DATA, mod.LINE + ".csv"), dst)
        print(f"archived {os.path.basename(dst)}")
    for mod in REPAIRED:
        _, after, _ = planned[mod.LINE]
        collect.write_line(mod.LINE, after)

    summary, changes = rebuild_summary(REPAIR_DATE)
    if changes:
        collect._write_rows(os.path.join(collect.DATA, "summary.csv"),
                            collect.SUMMARY_HEADER, summary)
        for date, was, now in changes:
            print(f"summary {date}: {was} -> {now}")
    mirrored = mirror()
    print(f"mirrored {len(mirrored)} file(s) to docs/data/")

    print("\nNOW: add a method row to data/annotations.csv (and its docs/ mirror) "
          "saying what was wrong, what changed, and which archives hold the "
          "pre-repair files; then run the daily derive block and "
          "tools/replay.py --check.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
