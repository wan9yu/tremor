"""Side-channel: sample the snapshot lines several times a day, score nothing.

Some lines are INSTANTANEOUS. `flights` counts the aircraft in the air right
now; `cnh_cny` reads two prices as they stand; `capital_premium` compares two
order books at one moment. For those the daily row is one draw from a
distribution the instrument has never measured — and it matters. Reconstructing
every committed revision of `cnh_cny` from git showed the same calendar date
written at values 131 pips apart by runs at different times, which is 3.6x that
line's robust scale, larger than the 3.0 its own alarm requires. A tier-1 alarm
reachable by the clock alone is not measuring the world.

The question that cannot be answered from the daily record is simple: **how wide
is a day, and where in it does the 22:00 reading fall?** This tool answers it by
sampling the same quantities at several hours and writing them somewhere the
scorer never looks.

Deliberately inert:
  * it writes ONLY to ``data/intraday.csv`` — no line CSV, no summary, no z, no
    verdict, nothing the dashboard counts;
  * ``collect.py`` and ``core/normalize.py`` do not read it and must never;
  * it runs from its own workflow, so a failure here cannot cost a daily row.

It is measurement about the instrument, gathered before deciding anything. After
~30 days it will settle, with data rather than argument, whether cnh_cny's
problem is that it should be demoted or that its daily value should be a median
of several samples instead of one instant — and the same file answers the same
question for flights, whose four regions are sampled at 18:00, 15:00, 07:00 and
MIDNIGHT local respectively by a single global cron.
"""
import csv
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core import normalize
from fetchers import capital_premium, cnh_cny, flights

# Only the truly instantaneous lines. Lines whose reading is already an
# aggregate over a window (grid_frequency's 24h maximum, net_outages' trailing
# day) or a published daily file (gnss_interference, the FRED and PortWatch
# lines) do not have this problem and are not sampled.
SNAPSHOT_LINES = [flights, cnh_cny, capital_premium]

PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    "data", "intraday.csv")
HEADER = ["sampled_utc", "line", "raw_value", "source_note"]


def sample():
    now = datetime.now(timezone.utc)
    rows = []
    for mod in SNAPSHOT_LINES:
        try:
            result = mod.fetch_daily()
        except Exception as e:  # a side channel must never be able to fail loudly
            result = {"raw_value": None,
                      "source_note": f"fetcher crashed: {type(e).__name__}"}
        value = result.get("raw_value")
        rows.append({
            "sampled_utc": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "line": mod.LINE,
            "raw_value": "" if value is None else f"{float(value):.4f}".rstrip("0").rstrip("."),
            "source_note": result.get("source_note", ""),
        })
        print(f"  {mod.LINE:18} {rows[-1]['raw_value'] or 'NA':>10}")

    existing = []
    if os.path.exists(PATH):
        with open(PATH, newline="") as f:
            existing = list(csv.DictReader(f))
    os.makedirs(os.path.dirname(PATH), exist_ok=True)
    with open(PATH, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=HEADER, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(existing + rows)
    print(f"\n{len(existing) + len(rows)} rows in data/intraday.csv")


def report():
    """What the file says so far: how wide is a day, per line."""
    import statistics
    from collections import defaultdict
    if not os.path.exists(PATH):
        print("no samples yet")
        return
    with open(PATH, newline="") as f:
        rows = [r for r in csv.DictReader(f) if r["raw_value"]]
    by_day = defaultdict(lambda: defaultdict(list))
    for r in rows:
        by_day[r["line"]][r["sampled_utc"][:10]].append(float(r["raw_value"]))
    print(f"{'line':18} {'days':>5} {'samples':>8} {'median day range':>18} {'in Qn':>8}")
    for line, days in sorted(by_day.items()):
        spans = [max(v) - min(v) for v in days.values() if len(v) > 1]
        if not spans:
            print(f"{line:18} {len(days):>5} {sum(len(v) for v in days.values()):>8}"
                  f"{'(need 2+ per day)':>18}")
            continue
        path = os.path.join(os.path.dirname(PATH), line + ".csv")
        qn = None
        if os.path.exists(path):
            with open(path, newline="") as f:
                hist = [float(x["raw_value"]) for x in csv.DictReader(f) if x["raw_value"]]
            qn = (normalize._qn(hist[-normalize.WINDOW:])
                  if len(hist) >= normalize.MIN_POINTS else None)
        span = statistics.median(spans)
        ratio = f"{span / qn:.2f}" if qn else "—"
        print(f"{line:18} {len(days):>5} {sum(len(v) for v in days.values()):>8} "
              f"{span:>18.4g} {ratio:>8}")
    print("\n'in Qn' is the day's spread measured in the line's own robust scale.")
    print(f"Above {normalize.THRESHOLD:.1f} means the clock alone can move it further "
          "than its alarm requires.")


if __name__ == "__main__":
    if "--report" in sys.argv:
        report()
    else:
        sample()
