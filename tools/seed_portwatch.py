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
import csv
import datetime
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from collect import LINE_HEADER, _fmt
from core import clock, normalize, portwatch

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
ARCHIVE = os.path.join(DATA, "archive")

SEED_DAYS = 200  # comfortably past MAX_AGE_DAYS so the first live row has a full window

LINES = [
    ("chokepoint_breadth", "Daily_Chokepoints_Data", "n_total",
     "IMF PortWatch 28 chokepoints, total transits"),
    ("port_throughput", "Daily_Ports_Data", "portcalls",
     "IMF PortWatch global port calls"),
]


def seed(line, service, field, label, today):
    rows, reason = portwatch.daily_totals(service, field, count=SEED_DAYS + 60)
    if rows is None:
        print(f"  {line}: FAILED — {reason}")
        return False
    cutoff = datetime.date.fromisoformat(today) - datetime.timedelta(days=portwatch.LAG_DAYS)
    observations = sorted((d, v) for d, v in rows if d <= cutoff)[-SEED_DAYS:]
    if not observations:
        print(f"  {line}: FAILED — no observations at or before {cutoff}")
        return False

    src = os.path.join(DATA, line + ".csv")
    os.makedirs(ARCHIVE, exist_ok=True)
    if os.path.exists(src):
        shutil.copy2(src, os.path.join(ARCHIVE, f"{line}_v1.csv"))

    out = []
    for obs_date, value in observations:
        row_date = (obs_date + datetime.timedelta(days=portwatch.LAG_DAYS)).isoformat()
        history = [float(r["raw_value"]) for r in out]
        dates = [r["date"] for r in out]
        obs_dates = [r["obs_date"] for r in out]
        z, trembling, direction, verdict, status = normalize.judge(
            history, dates, obs_dates, value, obs_date.isoformat(), row_date)
        out.append({
            "date": row_date,
            "raw_value": _fmt(value),
            "z_score": "" if z is None else f"{z:.3f}",
            "trembling": str(trembling),
            "direction": direction,
            "source_note": (f"{label} {obs_date}{(' ' + verdict) if verdict else ''}"
                            " [archive import: scored retroactively, not a live reading]"),
            "obs_date": obs_date.isoformat(),
            "status": status,
        })

    with open(src, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=LINE_HEADER, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(out)

    scored = sum(1 for r in out if r["z_score"])
    trembles = sum(int(r["trembling"]) for r in out)
    print(f"  {line}: {len(out)} rows {out[0]['date']}..{out[-1]['date']}, "
          f"{scored} scored, {trembles} trembles, last status={out[-1]['status']}")
    return True


def main():
    today = clock.china_today()
    print(f"seeding PortWatch lines as of {today} (lag {portwatch.LAG_DAYS}d)")
    ok = all(seed(line, svc, fld, label, today) for line, svc, fld, label in LINES)
    print("done" if ok else "FAILED — nothing usable was written for at least one line")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
