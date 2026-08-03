"""One-off: seed net_outages from IODA's own historical outage summaries.

net_outages is a TIER-1 line with twenty-five rows. Its promotion review is
pre-committed at sixty readings, and with a handful of scored days it cannot be
adjudicated — the confidence interval on its tremble rate is wider than any
question anyone would ask of it. IODA answers its summary endpoint for arbitrary
past windows, so the history exists; this fetches it one day at a time.

TWO THINGS THIS SEEDER MUST NOT GET WRONG.

1. AN EMPTY ANSWER IS NOT A CALM WORLD. IODA's summary endpoint returns nothing
   at all before 2022-01-26 — zero entities across every datasource, not zero
   outages — and seeding those days as "0 countries dark" would fabricate the
   calmest stretch in the record out of a service that did not yet exist. A day
   counts as an OBSERVATION only if the response carries at least one entity
   from some datasource; then the ping-slash24 count, zero or not, is real.
   Days before the floor are not fetched at all, and any later empty day is
   recorded as served-nothing rather than as a reading.

2. IODA HAS TWICE GONE DOWN AND REPORTED ITSELF AS THE WORLD GOING DOWN. The
   known artifact days show 160 and 191 countries against a median of 3 — a
   monitoring failure wearing the costume of a global blackout. They are NOT
   filtered out here: the instrument cannot know at capture which is which, and
   a seeder that silently deletes the days it dislikes is worse than one that
   records them. They are seeded, they will score, and each is annotated. The
   robust scale is built for exactly this: at 2 contaminated days in a 90-day
   window the median and Qn barely move, so those two days cost the line
   nothing except two trembles that the record explains.

Method: ``seedlib.run_seed`` end to end — published rows keep their dates,
everything re-scored oldest-first, the pre-seed file archived.

INTERRUPTIBLE BY DESIGN. The sweep is an overnight job against someone else's
research service, so stopping it must never cost anything. Each day is appended
to the cache the moment it arrives, so the file on disk is always complete up to
wherever it got to; Ctrl-C (or a kill) stops between days and prints how to
resume; a rerun refetches nothing it already holds. ``--limit N`` runs a bounded
chunk and stops cleanly, which is the polite way to spread the sweep over
several sittings. The write is one row per fetch, so even a hard kill leaves the
last row either whole or absent — never half.

    python tools/seed_ioda.py --dry-run     # report the plan, fetch nothing new
    python tools/seed_ioda.py --limit 200   # fetch 200 more days, then stop
    python tools/seed_ioda.py               # fetch to the end
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
from fetchers import net_outages

# Bisected against the source, not assumed: 2022-01-25 and everything before it
# answers with zero entities across all datasources; 2022-01-26 is the first day
# that answers at all.
FIRST_DAY = datetime.date(2022, 1, 26)
_PAUSE_S = 1.5
# IODA answers a one-day summary in about 6.5 seconds and more slowly on busy
# days, so the real cost is the SERVICE's, not the pause: measured end to end at
# ~15s per day, which makes the full sweep an overnight job. The estimate below
# uses the measurement rather than the pause, because a progress line that lies
# by an order of magnitude is worse than no progress line.
_SECONDS_PER_DAY = 15.0
_WINDOW_HOUR = 22  # the daily run's own collection hour, so windows are comparable
_CACHE = os.path.join(collect.DATA, "archive", "ioda_seed_fetch.csv")


def _load_cache():
    if not os.path.exists(_CACHE):
        return {}
    return {r["obs_date"]: (_int(r["hits"]), _int(r["entities"]))
            for r in collect._read_rows(_CACHE)}


def _int(cell):
    return int(cell) if cell not in ("", None) else None


def _append_cache(day, hits, entities, names):
    exists = os.path.exists(_CACHE)
    with open(_CACHE, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["obs_date", "hits", "entities", "countries"])
        if not exists:
            w.writeheader()
        w.writerow({"obs_date": day,
                    "hits": "" if hits is None else hits,
                    "entities": "" if entities is None else entities,
                    "countries": names})


def day_summary(day):
    """``(ping_slash24_count, total_entities, names)`` for one 24h window.

    ``(None, None, "")`` when the request fails outright; a served-but-empty day
    comes back as ``(0, 0, "")`` and the caller decides what that means.
    """
    end = datetime.datetime.combine(day, datetime.time(_WINDOW_HOUR, 0),
                                    datetime.timezone.utc)
    stamp = int(end.timestamp())
    last = None
    for attempt in (1, 2):
        try:
            r = requests.get(net_outages._URL,
                             params={"from": stamp - 86400, "until": stamp,
                                     "entityType": "country", "limit": 400},
                             headers=net_outages._HEADERS, timeout=40)
        except requests.RequestException as e:
            last = type(e).__name__
        else:
            if r.status_code == 200:
                data = r.json().get("data") or []
                hit = [d for d in data
                       if any(k.startswith(net_outages._DATASOURCE)
                              for k in (d.get("scores") or {}))]
                names = sorted((d.get("entity") or {}).get("name")
                               or (d.get("entity") or {}).get("code") or "?"
                               for d in hit)
                return len(hit), len(data), "; ".join(names)
            last = f"HTTP {r.status_code}"
        if attempt == 1:
            time.sleep(10)
    raise RuntimeError(f"{day}: {last}")


def _limit(argv):
    """``--limit N`` — fetch at most N more days this sitting, then stop cleanly."""
    if "--limit" not in argv:
        return None
    try:
        return max(0, int(argv[argv.index("--limit") + 1]))
    except (IndexError, ValueError):
        raise SystemExit("--limit needs a number of days")


def main(argv):
    dry = "--dry-run" in argv
    cache = _load_cache()
    names_by_day = {r["obs_date"]: r.get("countries", "")
                    for r in collect._read_rows(_CACHE)}
    live = seedlib.read_line(net_outages.LINE)

    # The live rows carry no obs_date (the line reads a rolling 24h window), so
    # the seed stops at the first day the instrument was collecting for itself.
    end = (datetime.date.fromisoformat(min(r["date"] for r in live)) if live
           else datetime.date.today())
    wanted, day = [], FIRST_DAY
    while day < end:
        wanted.append(day.isoformat())
        day += datetime.timedelta(days=1)

    todo = [d for d in wanted if d not in cache]
    limit = _limit(argv)
    if limit is not None:
        todo = todo[:limit]
    print(f"seeding {net_outages.LINE}: {len(wanted)} days {wanted[0]}..{wanted[-1]}, "
          f"{len(cache)} cached, {len(todo)} to fetch "
          f"(~{len(todo) * _SECONDS_PER_DAY / 3600:.1f} h)")

    fetched, stopped = 0, False
    try:
        for i, d in enumerate([] if dry else todo):
            hits, entities, names = day_summary(datetime.date.fromisoformat(d))
            _append_cache(d, hits, entities, names)
            cache[d] = (hits, entities)
            names_by_day[d] = names
            fetched += 1
            if i % 100 == 0:
                print(f"  {d} ({i}/{len(todo)}) hits={hits} entities={entities}")
            time.sleep(_PAUSE_S)
    except KeyboardInterrupt:
        stopped = True
        print(f"\n  interrupted after {fetched} day(s); the cache holds every one of "
              f"them and a rerun resumes from there")

    # A partial sweep must not write a line CSV with a hole where the rest of
    # history goes: the merge would treat the unfetched days as observations
    # that never existed. Report and stop instead.
    remaining = [d for d in wanted if d not in cache]
    if stopped or remaining or dry:
        print(f"  {len(cache)} of {len(wanted)} days cached, {len(remaining)} to go "
              f"(~{len(remaining) * _SECONDS_PER_DAY / 3600:.1f} h)")
        if remaining:
            print("  nothing written to the line yet — rerun to continue, and the "
                  "seed lands when the sweep is complete")
        return 0

    history, absent = [], []
    for d in wanted:
        hits, entities = cache[d]
        if not entities:          # served nothing at all: not an observation
            absent.append(d)
            continue
        history.append((d, float(hits)))
    print(f"fetched: {len(history)} observations, {len(absent)} days served nothing"
          + (f" ({absent[:5]}{'...' if len(absent) > 5 else ''})" if absent else ""))
    spikes = sorted(((v, d) for d, v in history), reverse=True)[:5]
    print(f"  largest readings: {[(d, int(v)) for v, d in spikes]}")
    if dry:
        return 0

    def import_note(obs, value):
        who = names_by_day.get(obs, "")
        who = f" [{who.replace('; ', ', ')}]" if who else ""
        return (f"IODA {int(value)} countries with {net_outages._DATASOURCE} "
                f"outages (24h to {obs} {_WINDOW_HOUR}:00Z){who}"
                + seedlib.IMPORT_MARK)

    seedlib.run_seed(net_outages, history, import_note)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
