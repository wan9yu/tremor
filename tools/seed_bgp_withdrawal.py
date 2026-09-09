"""Seed net_bgp_withdrawal from IODA's passive-BGP per-country signals.

net_bgp_withdrawal reads a WORST-OF fraction across a 153-country watch-list, and
each country's fraction needs a 28-day rolling-median baseline — so unlike a
single-series line the seed must fetch every watch-list country's whole history,
not one number a day. IODA answers the per-country `bgp` signal for arbitrary
past windows (capped at ~90 days a request), so this pulls each country's history
in <=88-day hourly chunks, reduces each chunk to per-day (daily-min, daily-median),
and caches that reduction per country. The aggregation itself reuses the fetcher's
own pure functions (fetchers/net_bgp_withdrawal.aggregate), so a seeded row is
computed by exactly the code the live line runs.

CONCURRENT-WITH-BACKOFF, RESUMABLE. IODA's TLS resets under a concurrent burst
and the sweep is long, so countries are fetched in a small thread pool, each with
per-chunk retry+backoff, and each country's reduced series is written to its own
cache file the moment it completes. A kill or Ctrl-C stops between countries; a
rerun refetches only the countries not yet cached. The cache
(data/archive/bgp_seed_cache/) is bulky per-country scratch and is gitignored —
the committed record is the scored line CSV, written once every watch-list country
is cached.

Method: ``seedlib.run_seed`` end to end for the merge/re-score/archive — the
history handed to it is the per-day worst-of aggregate, re-scored oldest-first
through the line's own anchored scale-mode (collect.scoring_attrs), so seeded rows
match the live shape and carry the seed-import marker.

    python tools/seed_bgp_withdrawal.py --derive-watchlist   # re-derive + print the 153, fetch nothing
    python tools/seed_bgp_withdrawal.py --dry-run            # report the plan
    python tools/seed_bgp_withdrawal.py --limit 40           # cache 40 more countries, then stop
    python tools/seed_bgp_withdrawal.py                      # fetch all, then write the line
"""
import concurrent.futures as cf
import datetime
import json
import os
import statistics
import sys
import time
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests

import collect
import seedlib
from core import useragent
from fetchers import net_bgp_withdrawal as M

FIRST_DAY = datetime.date(2022, 1, 26)  # IODA's first answered bgp day (probe-bisected)
_CHUNK_DAYS = 88                        # under IODA's ~90-day per-request cap
_CACHE_DIR = os.path.join(collect.DATA, "archive", "bgp_seed_cache")
_WORKERS = 8
_BACKOFF_S = (5, 15, 30, 60)
_ENTITIES = "https://api.ioda.inetintel.cc.gatech.edu/v2/entities/query"


# --- watch-list re-derivation (audit / reproducibility) --------------------

def derive_watchlist(window_days=21, floor=M.SIZE_FLOOR):
    """Re-derive the size-floored watch-list live: the countries whose median
    daily-median visible-/24 over the last ``window_days`` is >= ``floor``. The
    same rule that produced fetchers/net_bgp_withdrawal.WATCHLIST."""
    r = requests.get(_ENTITIES, params={"entityType": "country"},
                     headers=useragent.HEADERS, timeout=45)
    ccs = sorted(e["code"] for e in r.json()["data"] if e.get("code"))
    until = int(time.time())
    frm = until - window_days * 86400
    levels = {}

    def level(cc):
        for i in range(len(_BACKOFF_S) + 1):
            try:
                pts = M.fetch_country_points(cc, frm, until)
                meds = [med for _mn, med in M.daily_stats(pts).values()]
                return cc, (statistics.median(meds) if meds else 0.0)
            except Exception:  # noqa: BLE001
                if i < len(_BACKOFF_S):
                    time.sleep(_BACKOFF_S[i])
        return cc, None
    with cf.ThreadPoolExecutor(max_workers=_WORKERS) as ex:
        for cc, lvl in ex.map(level, ccs):
            levels[cc] = lvl
    watch = sorted(cc for cc, v in levels.items() if v is not None and v >= floor)
    return watch, levels


# --- per-country fetch + reduce + cache ------------------------------------

def _cache_path(cc):
    return os.path.join(_CACHE_DIR, f"{cc}.json")


def _load_country(cc):
    """Cached ``{day: (min, median)}`` for one country, or None if not cached."""
    path = _cache_path(cc)
    if not os.path.exists(path):
        return None
    with open(path) as f:
        return {day: tuple(mm) for day, mm in json.load(f).items()}


def _chunks(first, last):
    day = first
    while day <= last:
        end = min(day + datetime.timedelta(days=_CHUNK_DAYS - 1), last)
        # window bounds: start of `day` .. end of `end`
        frm = int(datetime.datetime.combine(day, datetime.time(), datetime.timezone.utc).timestamp())
        until = int(datetime.datetime.combine(end + datetime.timedelta(days=1),
                                              datetime.time(), datetime.timezone.utc).timestamp())
        yield frm, until
        day = end + datetime.timedelta(days=1)


def fetch_country(cc, last_day, session):
    """Fetch + reduce one country's whole history to ``{day: (min, median)}``,
    retrying each chunk across a few minutes of backoff."""
    points = []
    for frm, until in _chunks(FIRST_DAY, last_day):
        last = None
        for attempt in range(len(_BACKOFF_S) + 1):
            try:
                points.extend(M.fetch_country_points(cc, frm, until, session=session))
                last = None
                break
            except (requests.RequestException, ValueError, KeyError) as e:
                last = type(e).__name__
                if attempt < len(_BACKOFF_S):
                    time.sleep(_BACKOFF_S[attempt])
        if last is not None:
            raise RuntimeError(f"{cc}: chunk {frm}-{until} failed ({last})")
    return M.daily_stats(points)


def _cache_country(cc, stats):
    os.makedirs(_CACHE_DIR, exist_ok=True)
    tmp = _cache_path(cc) + ".tmp"
    with open(tmp, "w") as f:
        json.dump({day: [mn, med] for day, (mn, med) in stats.items()}, f)
    os.replace(tmp, _cache_path(cc))  # atomic: a kill leaves the file whole or absent


def sweep(todo, last_day):
    """Fetch every country in ``todo`` concurrently, caching each on completion.
    Returns (n_ok, failures)."""
    ok, failures = 0, []
    with requests.Session() as session:
        def one(cc):
            try:
                return cc, fetch_country(cc, last_day, session)
            except Exception as e:  # noqa: BLE001
                return cc, e
        with cf.ThreadPoolExecutor(max_workers=_WORKERS) as ex:
            for cc, res in ex.map(one, todo):
                if isinstance(res, Exception):
                    failures.append(cc)
                    print(f"  {cc}: FAILED {res}")
                else:
                    _cache_country(cc, res)
                    ok += 1
                    print(f"  {cc}: cached {len(res)} days")
    return ok, failures


# --- build the per-day worst-of aggregate from the cache -------------------

def build_history(last_day):
    """The seeded history: ``[(obs_date, worst_fraction)]`` oldest-first, one
    row per day that has a worst-of. Reuses the fetcher's pure aggregation so
    seed and live share one definition."""
    per_country = {cc: _load_country(cc) for cc in M.WATCHLIST}
    per_country = {cc: s for cc, s in per_country.items() if s}
    # union of all days that have at least one country reading
    days = set()
    for stats in per_country.values():
        days.update(stats.keys())
    days = sorted(d for d in days if d <= last_day.isoformat())

    # precompute per-country {day: median} once for the rolling baseline
    medians = {cc: {d: med for d, (_mn, med) in s.items()} for cc, s in per_country.items()}
    history = []
    for day in days:
        fractions = {}
        for cc, stats in per_country.items():
            if day not in stats:
                continue
            frac = M.country_fraction(stats[day][0], M.rolling_baseline(medians[cc], day))
            if frac is not None:
                fractions[cc] = frac
        worst, _driver = M.worst_of(fractions)
        if worst is not None:
            history.append((day, round(worst, 4)))
    return history, per_country


def _driver_for(day, per_country):
    fractions = {}
    for cc, stats in per_country.items():
        if day not in stats:
            continue
        meds = {d: med for d, (_mn, med) in stats.items()}
        frac = M.country_fraction(stats[day][0], M.rolling_baseline(meds, day))
        if frac is not None:
            fractions[cc] = frac
    _worst, driver = M.worst_of(fractions)
    return driver, len(fractions)


def main(argv):
    if "--derive-watchlist" in argv:
        watch, _levels = derive_watchlist()
        print(f"watch-list size: {len(watch)}")
        print(json.dumps(watch))
        same = list(watch) == list(M.WATCHLIST)
        print(f"matches fetchers/net_bgp_withdrawal.WATCHLIST: {same}")
        if not same:
            print("  added:", sorted(set(watch) - set(M.WATCHLIST)))
            print("  dropped:", sorted(set(M.WATCHLIST) - set(watch)))
        return 0

    dry = "--dry-run" in argv
    limit = None
    if "--limit" in argv:
        try:
            limit = max(0, int(argv[argv.index("--limit") + 1]))
        except (IndexError, ValueError):
            raise SystemExit("--limit needs a number of countries")

    live = seedlib.read_line(M.LINE)
    # stop the seed before the first live-collected obs (obs_date == its date for
    # seeded rows); with no live rows yet, seed through the settled UTC day.
    last_day = datetime.date.fromisoformat(M.settled_day(datetime.datetime.now(datetime.timezone.utc)))
    if live:
        last_day = min(last_day,
                       datetime.date.fromisoformat(min(r["date"] for r in live))
                       - datetime.timedelta(days=1))

    cached = [cc for cc in M.WATCHLIST if os.path.exists(_cache_path(cc))]
    todo = [cc for cc in M.WATCHLIST if cc not in cached]
    if limit is not None:
        todo = todo[:limit]
    print(f"seeding {M.LINE}: {len(M.WATCHLIST)} watch-list countries, "
          f"{len(cached)} cached, {len(todo)} to fetch this sitting "
          f"({FIRST_DAY}..{last_day})")

    if todo and not dry:
        ok, failures = sweep(todo, last_day)
        print(f"  fetched {ok} country(ies), {len(failures)} failed: {failures}")
        cached = [cc for cc in M.WATCHLIST if os.path.exists(_cache_path(cc))]

    remaining = [cc for cc in M.WATCHLIST if not os.path.exists(_cache_path(cc))]
    if remaining or dry:
        print(f"  {len(cached)}/{len(M.WATCHLIST)} countries cached, "
              f"{len(remaining)} to go")
        if remaining:
            print("  nothing written to the line yet — rerun to continue; the seed "
                  "lands when every watch-list country is cached")
        if dry:
            history, _ = build_history(last_day) if cached else ([], {})
            print(f"  (dry) partial history from {len(cached)} cached countries: "
                  f"{len(history)} days"
                  + (f" {history[0][0]}..{history[-1][0]}" if history else ""))
        return 0

    history, per_country = build_history(last_day)
    if not history:
        print("  no worst-of days built — nothing to seed")
        return 0
    spikes = sorted(history, key=lambda dv: dv[1])[:5]
    print(f"built {len(history)} worst-of days {history[0][0]}..{history[-1][0]}; "
          f"deepest: {[(d, v) for d, v in spikes]}")

    def import_note(obs, value):
        driver, n = _driver_for(obs, per_country)
        return (f"IODA bgp worst-of route visibility {value:.4f} of normal, "
                f"driven by {driver} (daily-min ÷ {M.BASELINE_DAYS}d median), "
                f"across {n}/{len(M.WATCHLIST)} countries (settled UTC day {obs})"
                + seedlib.IMPORT_MARK)

    seedlib.run_seed(M, history, import_note)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
