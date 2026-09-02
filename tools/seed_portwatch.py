"""One-off: rebuild the PortWatch lines from their own published daily archive.

The v1 series asked PortWatch for the newest available day and kept one row, so
it re-recorded the same reading six days out of seven and never accumulated the
distinct observations a z-score needs. v2 reads the observation exactly
``portwatch.LAG_DAYS`` back, which is one new observation per collection day.
Starting v2 cold would leave both lines unable to score for another ten days and
without a real baseline for months, so they are seeded from the source's own
archive — the same thing that was done for ``vix`` on 2026-07-10.

Honest by construction:
  * Only real published observations are written. Nothing is interpolated.
  * Each seeded row is scored by the SAME ``normalize.judge`` the live collector
    uses, replayed strictly in order against only the rows already emitted, so
    no row is ever judged against readings from its own future.
  * Row dates follow the live rule (``clock.china_today()``) while PortWatch is
    current on this line's lag, which is when row date = observation + LAG_DAYS;
    a seeded row and a live row mean the same thing under that rule.
  * Every seeded row says so in ``source_note``. These were computed
    retroactively; they were never live detections.

On 2026-07-22 a re-run of this tool overwrote the archives of both lines
twelve minutes after they were first written, via a hand-rolled file copy
with no never-clobber loop, and rebuilt each line from scratch instead of
merging against what was already published — the true 31-row v1 archives
survive only in git history. This version routes through ``seedlib``, whose
``merge`` preserves every published row and whose ``archive_current`` never
overwrites an existing archive.

Run from the repo root:
    python tools/seed_portwatch.py --dry-run   # report what it would write
    python tools/seed_portwatch.py             # archive, seed, rescore
"""
import datetime
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import seedlib
from core import clock, portwatch
from fetchers import chokepoint, ports

SEED_DAYS = 200  # comfortably past MAX_AGE_DAYS so the first live row has a full window

LINES = [chokepoint, ports]  # each names its own SERVICE / FIELD / NOTE


def _row_date(obs):
    """PortWatch publishes ~10 days late, so an observation lands on the row
    dated when it first became knowable — the same rule the live collector
    uses while the source is current on the lag (the live rule itself is
    ``clock.china_today()``, which this formula matches only then)."""
    return (datetime.date.fromisoformat(obs)
            + datetime.timedelta(days=portwatch.LAG_DAYS)).isoformat()


def seed(mod, today, dry=False):
    rows, reason = portwatch.daily_totals(mod.SERVICE, mod.FIELD, count=SEED_DAYS + 60)
    if rows is None:
        print(f"  {mod.LINE}: FAILED — {reason}")
        return False
    cutoff = datetime.date.fromisoformat(today) - datetime.timedelta(days=portwatch.LAG_DAYS)
    observations = sorted((d, v) for d, v in rows if d <= cutoff)[-SEED_DAYS:]
    if not observations:
        print(f"  {mod.LINE}: FAILED — no observations at or before {cutoff}")
        return False
    history = [(d.isoformat(), v) for d, v in observations]
    seedlib.run_seed(mod, history,
                     lambda obs, value: f"{mod.NOTE} {obs}{seedlib.IMPORT_MARK}",
                     dry=dry, row_date=_row_date)
    return True


def main(argv):
    dry = "--dry-run" in argv
    today = clock.china_today()
    print(f"seeding PortWatch lines as of {today} (lag {portwatch.LAG_DAYS}d)"
          + (" (dry run)" if dry else ""))
    ok = all(seed(mod, today, dry=dry) for mod in LINES)
    print("done" if ok else "FAILED — nothing usable was written for at least one line")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
