"""One-off: seed net_outages from IODA's own historical outage summaries.

net_outages is a TIER-1 line with twenty-five rows. Its promotion review is
pre-committed at sixty readings, and with a handful of scored days it cannot be
adjudicated — the confidence interval on its tremble rate is wider than any
question anyone would ask of it. IODA answers its summary endpoint for arbitrary
past windows, so the history exists; this fetches it one day at a time.

TWO THINGS THIS SEEDER MUST NOT GET WRONG.

1. AN EMPTY ANSWER IS NOT A CALM WORLD, AND NEITHER IS A BROKEN ONE. IODA's
   summary endpoint returns nothing at all before 2022-01-26 — zero entities
   across every datasource, not zero outages — and seeding those days as
   "0 countries dark" would fabricate the calmest stretch in the record out of
   a service that did not yet exist. Separately, some individual dates make the
   service answer HTTP 500 no matter how patiently they are retried
   (2023-09-19 is the first found): its backend cannot compute that window.
   Three different states, kept three different things: a day is an OBSERVATION
   only if the response carries at least one entity from some datasource; a day
   the service answers but empties is served-nothing; a day it refuses outright
   is UNSERVED, recorded with its reason and skipped. None of the three becomes
   a zero.

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
_WINDOW_HOUR = 22  # display only: the window BOUNDARY math lives in
# net_outages.window_for_day (T1's one settled-window definition); this
# constant only formats the "24h to <obs> {_WINDOW_HOUR}:00Z" source note.
_CACHE = os.path.join(collect.DATA, "archive", "ioda_seed_fetch.csv")


def _load_cache():
    """{obs_date: (hits, entities, names, unserved)} — ONE parse of the file.

    It used to be parsed three times into three projections of the same rows,
    two of them updated in memory during the sweep and one re-read from disk,
    which is how the two representations in the sibling seeder drifted apart
    and cost a 36-minute run.
    """
    return {r["obs_date"]: (_int(r["hits"]), _int(r["entities"]),
                            r.get("countries", ""), r.get("unserved", ""))
            for r in collect._read_rows(_CACHE)}


def _int(cell):
    return int(cell) if cell not in ("", None) else None


_CACHE_HEADER = ["obs_date", "hits", "entities", "countries", "unserved"]


def _append_cache(day, hits, entities, names, unserved=""):
    exists = os.path.exists(_CACHE)
    with open(_CACHE, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=_CACHE_HEADER)
        if not exists:
            w.writeheader()
        w.writerow({"obs_date": day,
                    "hits": "" if hits is None else hits,
                    "entities": "" if entities is None else entities,
                    "countries": names,
                    "unserved": unserved})


# A sweep this long WILL meet a transient network error — the first unattended
# run died on a single SSLError after two tries ten seconds apart, four hours
# from the finish. Blips resolve in seconds; a service that is genuinely down
# stays down. Backing off across a few minutes tells those two apart, and
# ``_BACKOFF_S`` is what an unattended overnight run is worth.
_BACKOFF_S = (5, 15, 30, 60, 120)
# A run of refusals is ambiguous: either those DATES are broken at the source or
# the service (or this network) is down. Counting them cannot tell the two
# apart, so after this many in a row the sweep asks a date it has already
# fetched successfully — a canary. If the canary answers, the service is fine
# and the refusals belong to the dates; if it does not, the sweep stops rather
# than marking months unserved on no evidence.
_UNSERVED_BEFORE_CANARY = 3
# Once the canary has established the service is healthy, the remaining days of
# a broken RUN do not need the full four-minute climb each — the question they
# have to answer is no longer "is the service up" but only "is this date the
# same kind of broken as the last one". The source's gaps are contiguous
# (2023-09-19..10-04 is the first found), so this saves an hour of pure waiting
# on a known hole while keeping one real retry per day.
_RUN_BACKOFF_S = (5, 20)


def day_summary(day, backoff=_BACKOFF_S):
    """``(ping_slash24_count, total_entities, names)`` for one 24h window.

    Raises ``TransportError`` when the service will not answer after backing
    off across several minutes — a served-but-empty day is a legitimate
    ``(0, 0, "")`` and the caller decides what that means.
    """
    frm, until = net_outages.window_for_day(day)
    last = None
    for attempt in range(len(backoff) + 1):
        try:
            r = requests.get(net_outages._URL,
                             params={"from": frm, "until": until,
                                     "entityType": "country", "limit": 400},
                             headers=net_outages._HEADERS, timeout=40)
        except requests.RequestException as e:
            last = type(e).__name__
        else:
            if r.status_code == 200:
                try:
                    data = r.json().get("data") or []
                except ValueError:
                    last = "non-JSON body"
                else:
                    hit = [d for d in data
                           if any(k.startswith(net_outages._DATASOURCE)
                                  for k in (d.get("scores") or {}))]
                    names = sorted((d.get("entity") or {}).get("name")
                                   or (d.get("entity") or {}).get("code") or "?"
                                   for d in hit)
                    return len(hit), len(data), "; ".join(names)
            else:
                last = f"HTTP {r.status_code}"
        if attempt < len(backoff):
            wait = backoff[attempt]
            print(f"  {day}: {last} — retrying in {wait}s "
                  f"({attempt + 1}/{len(backoff)})")
            time.sleep(wait)
    raise TransportError(f"{day}: {last}")


class TransportError(RuntimeError):
    """The service would not answer this day, after backing off."""


def canary_answers(day):
    """Does a date we have ALREADY fetched still answer? One try, no backoff."""
    try:
        day_summary(day, backoff=())
        return True
    except TransportError:
        return False


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
    live = seedlib.read_line(net_outages.LINE)

    # The live rows carry no obs_date (the line reads a rolling 24h window), so
    # the seed stops at the first day the instrument was collecting for itself.
    end = (datetime.date.fromisoformat(min(r["date"] for r in live)) if live
           else datetime.date.today())
    wanted, day = [], FIRST_DAY
    while day < end:
        wanted.append(day.isoformat())
        day += datetime.timedelta(days=1)

    if not wanted:
        # Already seeded: the live record now starts at the seed's own first
        # observation, so there is nothing before it to fetch. Say so instead
        # of indexing an empty list.
        print(f"nothing to seed: {net_outages.LINE} already covers "
              f"{min(r['date'] for r in live)} onward")
        return 0

    todo = [d for d in wanted if d not in cache]
    limit = _limit(argv)
    if limit is not None:
        todo = todo[:limit]
    print(f"seeding {net_outages.LINE}: {len(wanted)} days {wanted[0]}..{wanted[-1]}, "
          f"{len(cache)} cached, {len(todo)} to fetch "
          f"(~{len(todo) * _SECONDS_PER_DAY / 3600:.1f} h)")

    # The canary is the newest date already known to answer, so a "the service
    # is down" verdict is never reached on the strength of broken dates alone.
    good = [d for d, (_, entities, _, _) in sorted(cache.items()) if entities]
    canary_day = datetime.date.fromisoformat(good[-1]) if good else FIRST_DAY

    fetched, stopped, consecutive_unserved = 0, False, 0
    run_confirmed = False   # the canary has vouched for the service mid-run
    try:
        for i, d in enumerate([] if dry else todo):
            try:
                # Full patience on the first refusal of a run; once the canary
                # has vouched for the service, a shorter one for the rest.
                hits, entities, names = day_summary(
                    datetime.date.fromisoformat(d),
                    backoff=_RUN_BACKOFF_S if run_confirmed else _BACKOFF_S)
            except TransportError as e:
                # A date the backend cannot compute is a hole in the SOURCE, not
                # a reason to stop. A run of them might still be the service
                # falling over, so ask the canary before believing the dates.
                consecutive_unserved += 1
                if consecutive_unserved > _UNSERVED_BEFORE_CANARY and not run_confirmed:
                    if not canary_answers(canary_day):
                        raise
                    print(f"  canary {canary_day} still answers — the refusals are "
                          f"these dates, not the service")
                    run_confirmed = True
                print(f"  {d}: unserved ({e}) — recorded and skipped")
                reason = str(e).split(": ", 1)[-1]
                _append_cache(d, None, None, "", unserved=reason)
                cache[d] = (None, None, "", reason)
                continue
            consecutive_unserved, run_confirmed = 0, False
            _append_cache(d, hits, entities, names)
            cache[d] = (hits, entities, names, "")
            fetched += 1
            if i % 100 == 0:
                print(f"  {d} ({i}/{len(todo)}) hits={hits} entities={entities}")
            time.sleep(_PAUSE_S)
    except KeyboardInterrupt:
        stopped = True
        print(f"\n  interrupted after {fetched} day(s); the cache holds every one of "
              f"them and a rerun resumes from there")
    except TransportError as e:
        # Stop the sitting, keep everything fetched, and say so plainly. An
        # unattended sweep must not lose hours of work to one bad minute, and it
        # must not paper over a service that is really down either.
        stopped = True
        print(f"\n  refusals ran on AND the canary {canary_day} stopped answering "
              f"too (last: {e}) — that is the service or this network, not the "
              f"dates. Stopped after {fetched} day(s) this sitting; everything "
              f"fetched is cached and a rerun resumes")

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

    unserved = [d for d in wanted if cache[d][3]]
    history, absent, swept = [], [], []
    for d in wanted:
        hits, entities, _, _ = cache[d]
        if not entities:          # served nothing, or refused: not an observation
            absent.append(d)
            continue
        # The seed must produce exactly what the live fetcher would, including
        # its refusals — otherwise the seeded stretch of the record obeys
        # different integrity rules from the collected stretch.
        if net_outages.monitor_swept(hits, entities):
            swept.append(d)
            history.append((d, None))
            continue
        history.append((d, float(hits)))
    print(f"  {len(swept)} day(s) refused as monitor sweeps: {swept}")
    print(f"fetched: {len(history)} observations, {len(absent)} days without one "
          f"({len(unserved)} the service refused outright, "
          f"{len(absent) - len(unserved)} answered but empty)")
    if unserved:
        print(f"  refused: {unserved[:6]}{'...' if len(unserved) > 6 else ''}")
    spikes = sorted(((v, d) for d, v in history if v is not None), reverse=True)[:5]
    print(f"  largest readings: {[(d, int(v)) for v, d in spikes]}")
    if dry:
        return 0

    def import_note(obs, value):
        hits, entities, names, _ = cache[obs]
        if value is None:
            return (f"no reading: IODA reported {hits} of {entities} watched "
                    f"entities in outage (24h to {obs} {_WINDOW_HOUR}:00Z) — a "
                    f"sweep of essentially everything it can see, which is the "
                    f"monitor losing its own vantage points, not the world going "
                    f"dark" + seedlib.IMPORT_MARK)
        who = f" [{names.replace('; ', ', ')}]" if names else ""
        return (f"IODA {int(value)} countries with {net_outages._DATASOURCE} "
                f"outages (24h to {obs} {_WINDOW_HOUR}:00Z){who}"
                + seedlib.IMPORT_MARK)

    seedlib.run_seed(net_outages, history, import_note)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
