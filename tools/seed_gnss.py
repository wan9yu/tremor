"""One-off: seed gnss_interference from GPSJam's published daily files.

GPSJam publishes one static CSV per day back to 2022-07-27 — the same files
the daily fetcher reads, aggregated by exactly the same arithmetic (sum the
good and bad aircraft counts over every h3 cell, take the bad share), so the
seeded values are bit-identical to what the live fetcher would have recorded
on those days.

The sampling frame is not constant — tracked-aircraft counts grew severalfold
over the period — but the RATIO is what the line scores, and re-deriving the
line's own live rows from a fixed common-cell frame was measured to move the
value by under 0.3% relative: the share is robust to the frame growing under
it. That measurement is what makes this seed honest; a count would not have
survived it.

POLITENESS: ~1,470 requests of ~190KB against a personal static site, paced
1.5s apart (~40 minutes). Parsed ratios are cached incrementally, so a rerun
resumes instead of refetching. A 404 is recorded as a day the source does not
serve; any other failure retries once and then ABORTS the run — a seed must
not quietly write a series with a transport-shaped hole in it.

    python tools/seed_gnss.py            # fetch (resumable), merge, write
    python tools/seed_gnss.py --dry-run  # fetch/cache only, write nothing
"""
import csv
import datetime
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests

import collect
import seedlib
from fetchers import gnss

FIRST_DAY = datetime.date(2022, 7, 27)
_PAUSE_S = 1.5
_CACHE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..",
                      "data", "archive", "gnss_seed_fetch.csv")


def _load_cache():
    if not os.path.exists(_CACHE):
        return {}
    with open(_CACHE, newline="") as f:
        return {r["obs_date"]: r for r in csv.DictReader(f)}


def _append_cache(row):
    exists = os.path.exists(_CACHE)
    with open(_CACHE, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["obs_date", "bad", "total"])
        if not exists:
            w.writeheader()
        w.writerow(row)


def day_counts(day):
    """(bad, total) for one GPSJam day; (None, None) if the day is not served.

    Raises RuntimeError after a retry on any transport-level failure.
    """
    url = gnss._URL.format(date=day)
    for attempt in (1, 2):
        try:
            r = requests.get(url, headers=gnss._HEADERS, timeout=30)
        except requests.RequestException as e:
            if attempt == 2:
                raise RuntimeError(f"{day}: {type(e).__name__}")
            time.sleep(10)
            continue
        if r.status_code == 404:
            return None, None
        if r.status_code != 200:
            if attempt == 2:
                raise RuntimeError(f"{day}: HTTP {r.status_code}")
            time.sleep(10)
            continue
        good = bad = 0
        for row in r.text.strip().splitlines()[1:]:
            cols = row.split(",")
            if len(cols) >= 3:
                try:
                    good += int(cols[1])
                    bad += int(cols[2])
                except ValueError:
                    continue
        return bad, good + bad
    return None, None


def main(argv):
    dry = "--dry-run" in argv
    cache = _load_cache()
    last_live_obs = None
    path = os.path.join(collect.DATA, gnss.LINE + ".csv")
    live = []
    if os.path.exists(path):
        with open(path, newline="") as f:
            live = list(csv.DictReader(f))
        obs_seen = [r["obs_date"] for r in live if r.get("obs_date")]
        last_live_obs = max(obs_seen) if obs_seen else None

    # Fetch up to the day before the live record began observing; the live rows
    # carry everything after that.
    end = datetime.date.fromisoformat(min(r["obs_date"] for r in live
                                          if r.get("obs_date"))) if last_live_obs \
        else datetime.date.today()
    wanted = []
    day = FIRST_DAY
    while day < end:
        wanted.append(day.isoformat())
        day += datetime.timedelta(days=1)

    todo = [d for d in wanted if d not in cache]
    print(f"seeding {gnss.LINE}: {len(wanted)} days {wanted[0]}..{wanted[-1]}, "
          f"{len(cache)} cached, {len(todo)} to fetch "
          f"(~{len(todo) * _PAUSE_S / 60:.0f} min)")
    for i, d in enumerate(todo):
        bad, total = day_counts(d)
        row = {"obs_date": d, "bad": "" if bad is None else bad,
               "total": "" if total is None else total}
        _append_cache(row)
        cache[d] = row
        if i % 100 == 0:
            print(f"  {d} ({i}/{len(todo)})")
        time.sleep(_PAUSE_S)

    history, absent = [], []
    for d in wanted:
        r = cache[d]
        if r["total"] in ("", "0"):
            absent.append(d)
            continue
        bad, total = int(r["bad"]), int(r["total"])
        history.append((d, round(bad / total * 100.0, 4)))
    print(f"fetched: {len(history)} observations, {len(absent)} days not served"
          + (f" ({absent[:5]}{'...' if len(absent) > 5 else ''})" if absent else ""))
    if dry:
        return 0

    counts = {d: (int(cache[d]["bad"]), int(cache[d]["total"])) for d, _ in history}

    def import_note(obs, value):
        bad, total = counts[obs]
        return (f"GPSJam {obs}: {bad}/{total} aircraft with bad GPS"
                + seedlib.IMPORT_MARK)

    plan, dropped = seedlib.merge(history, live, import_note)
    for d in dropped:
        print(f"  note: {d}")
    seedlib.archive_current(gnss.LINE, "preseed")
    out = seedlib.score_series(plan)
    collect.write_line(gnss.LINE, out)
    print(f"-> {len(out)} rows, {sum(1 for r in out if r['z_score'])} scored, "
          f"{sum(int(r['trembling']) for r in out)} trembles, "
          f"last status={out[-1]['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
