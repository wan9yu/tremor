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
  * Row dates follow the live rule exactly (row date = observation + LAG_DAYS),
    so a seeded row and a live row mean the same thing.
  * Every seeded row says so in ``source_note``. These were computed
    retroactively; they were never live detections.

Run from the repo root:  python tools/seed_portwatch.py
"""
import datetime
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import collect
from core import clock, portwatch
from fetchers import chokepoint, ports

SEED_DAYS = 200  # comfortably past MAX_AGE_DAYS so the first live row has a full window
IMPORT_MARK = " [archive import: scored retroactively, not a live reading]"

LINES = [chokepoint, ports]  # each names its own SERVICE / FIELD / NOTE


def seed(mod, today):
    rows, reason = portwatch.daily_totals(mod.SERVICE, mod.FIELD, count=SEED_DAYS + 60)
    if rows is None:
        print(f"  {mod.LINE}: FAILED — {reason}")
        return False
    cutoff = datetime.date.fromisoformat(today) - datetime.timedelta(days=portwatch.LAG_DAYS)
    observations = sorted((d, v) for d, v in rows if d <= cutoff)[-SEED_DAYS:]
    if not observations:
        print(f"  {mod.LINE}: FAILED — no observations at or before {cutoff}")
        return False

    src = os.path.join(collect.DATA, mod.LINE + ".csv")
    archive = os.path.join(collect.DATA, "archive")
    os.makedirs(archive, exist_ok=True)
    if os.path.exists(src):
        shutil.copy2(src, os.path.join(archive, f"{mod.LINE}_v1.csv"))

    out = []
    for obs_date, value in observations:
        row_date = (obs_date + datetime.timedelta(days=portwatch.LAG_DAYS)).isoformat()
        # score_row replays against only the rows already emitted, so no row is
        # ever judged against readings from its own future.
        out.append(collect.score_row(
            row_date, value, f"{mod.NOTE} {obs_date}{IMPORT_MARK}",
            obs_date.isoformat(), out,
            weekly_cycle=getattr(mod, "WEEKLY_CYCLE", False)))
    collect.write_line(mod.LINE, out)

    scored = sum(1 for r in out if r["z_score"])
    trembles = sum(int(r["trembling"]) for r in out)
    print(f"  {mod.LINE}: {len(out)} rows {out[0]['date']}..{out[-1]['date']}, "
          f"{scored} scored, {trembles} trembles, last status={out[-1]['status']}")
    return True


def main():
    today = clock.china_today()
    print(f"seeding PortWatch lines as of {today} (lag {portwatch.LAG_DAYS}d)")
    ok = all(seed(mod, today) for mod in LINES)
    print("done" if ok else "FAILED — nothing usable was written for at least one line")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
