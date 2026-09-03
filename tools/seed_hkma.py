"""One-off: give hkma_aggr_balance the baseline it launched without.

The line went live cold on 2026-07-23 and holds 20 unique observations against a
``normalize.WINDOW`` of 90. Its siblings were all seeded; this one never was. The
cost is measured, not stylistic: on 2026-08-09 the cold window put Qn at 32.20
where the seeded window puts it at 112.99, so the same reading scored 19.223
instead of 6.186 — a real move, judged by a scale 3.5x too narrow to know what
this series normally does.

Honest by construction, the same four ways ``seed_portwatch.py`` is:
  * Only real published observations are written. Nothing is interpolated.
  * Each seeded row is judged by the SAME ``normalize.judge`` the live collector
    uses, replayed strictly in order against only the rows already emitted, so
    no row is ever judged against readings from its own future.
  * Row dates follow the live rule. This source publishes one day late, so a
    seeded row is dated ``obs + 1 day`` and means the same thing a live row
    means. Verified against the published record: on all 18 rows where the
    collector actually returned a reading, ``obs + 1`` reproduces the row date
    exactly. Two observations (2026-08-07, 08-21) first appear a day later than
    that, and both times the mapped day is a DARK row — the rule holds; the
    collector was blind. That is the outage in §1.1, not an exception.
  * Every seeded row says so in ``source_note``. These were computed
    retroactively; they were never live detections.

THE RANGE STOPS AT THE DAY BEFORE THE LINE LAUNCHED, and that boundary is the
whole safety argument. ``seedlib.merge`` rule 3 drops an import that lands on a
published first-occurrence or dark row, but an import landing on a published
STALE-REPUBLISH row wins the date and rewrites it. Ending at 2026-07-22 means no
import can reach either branch: every seeded row lands on a date no live row
holds, and the one observation a live row does hold (2026-07-22, carried by row
2026-07-23) is skipped by rule 2. The published record is therefore untouchable
by this tool by construction, not by care.

EVERY observation lost to a dark day since launch is left lost. No count is given
here because the outage is ongoing and any number rots overnight; the rule is
what holds. Recovering them would mean importing onto dates the published record
already occupies. Under the ``obs + 1`` mapping this tool installs they all land
on published DARK rows and are dropped, overwriting nothing — measured, 0 rows
changed. Under seedlib's DEFAULT identity mapping three of them (08-10, 08-17,
08-24) would instead land on stale-republish rows and REWRITE them — measured, 3
rows changed. That is the hazard this tool's ``row_date`` avoids, and it is why
the mapping is a safety control and not a cosmetic one. The record says what it
could see.

The fetched payload is cached under data/archive/, so a re-run costs the source
nothing. The endpoint fails in phases of tens of minutes (see the fetcher), and
this tool is deliberately single-shot: if the fetch fails, run it again later.

Run from the repo root:
    python tools/seed_hkma.py --dry-run   # report what it would write
    python tools/seed_hkma.py             # archive, seed, re-judge
"""
import csv
import datetime
import os
import sys

import requests

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import seedlib
import collect
from fetchers import hkma_aggr_balance as hkma

# The day before the line's first published row. See the module docstring: this
# single number is what keeps the seed off the published record.
SEED_TO = "2026-07-22"
# Far enough back that the first live row sees a full window under
# MAX_AGE_DAYS=180. Deeper would archive observations no verdict can ever reach.
SEED_FROM = "2026-03-01"

_CACHE = os.path.join(collect.DATA, "archive", "hkma_seed_fetch.csv")
_LAG_DAYS = 1


def _row_date(obs):
    """The row an observation would have been collected on.

    HKMA publishes the closing balance the following morning (roughly 06:30-11:30
    HKT), and the collector samples at 22:30Z = 06:30 HKT, so a row dated D
    carries the observation of the previous business day. Reproduces the
    published row date on all 18 rows that carry a live reading; the only two
    observations that surfaced later did so because the intervening row is dark.
    """
    return (datetime.date.fromisoformat(obs)
            + datetime.timedelta(days=_LAG_DAYS)).isoformat()


def _fetch():
    """One request for the whole range, or None with a reason."""
    params = {"choose": "end_of_date", "from": SEED_FROM, "to": SEED_TO,
              "fields": "end_of_date,closing_balance",
              "sortby": "end_of_date", "sortorder": "asc", "pagesize": 500}
    try:
        r = requests.get(hkma._URL, params=params, headers=hkma._HEADERS,
                         timeout=(10, 60))
    except requests.RequestException as e:
        return None, f"request failed: {type(e).__name__}"
    if r.status_code != 200:
        return None, f"HTTP {r.status_code}"
    try:
        records = (r.json().get("result") or {}).get("records") or []
    except ValueError:
        return None, "non-JSON body"
    out = [(rec.get("end_of_date"), rec.get("closing_balance"))
           for rec in records
           if rec.get("end_of_date") and rec.get("closing_balance") is not None]
    return (out, None) if out else (None, "no usable records")


def _cache_write(rows):
    os.makedirs(os.path.dirname(_CACHE), exist_ok=True)
    with open(_CACHE, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["obs_date", "closing_balance"])
        w.writeheader()
        for obs, value in rows:
            w.writerow({"obs_date": obs, "closing_balance": value})


def _cache_read():
    if not os.path.exists(_CACHE):
        return None
    with open(_CACHE, encoding="utf-8") as f:
        return [(r["obs_date"], float(r["closing_balance"]))
                for r in csv.DictReader(f)]


def history():
    """[(obs_date, value)] oldest-first, from the cache or from one request."""
    cached = _cache_read()
    if cached:
        print(f"  using cached payload: {len(cached)} observations "
              f"{cached[0][0]}..{cached[-1][0]}")
        return cached
    rows, reason = _fetch()
    if rows is None:
        print(f"  FAILED — {reason}")
        return None
    rows = [(obs, float(v)) for obs, v in rows]
    _cache_write(rows)
    print(f"  fetched {len(rows)} observations {rows[0][0]}..{rows[-1][0]} "
          f"-> {os.path.relpath(_CACHE)}")
    return rows


def _note(obs, value):
    """The live fetcher's own wording, marked as an import."""
    return f"HKMA aggregate balance {value:.0f} HK$m ({obs}){seedlib.IMPORT_MARK}"


def main(argv):
    dry = "--dry-run" in argv
    print(f"seeding {hkma.LINE} from {SEED_FROM} to {SEED_TO}"
          + (" (dry run)" if dry else ""))
    rows = history()
    if rows is None:
        return 1
    late = [obs for obs, _ in rows if obs > SEED_TO]
    if late:
        print(f"  REFUSED — {len(late)} observations after {SEED_TO}; the boundary "
              f"is what keeps this seed off the published record. "
              f"Delete {os.path.relpath(_CACHE)} and re-fetch.")
        return 1
    seedlib.run_seed(hkma, rows, _note, dry=dry, row_date=_row_date)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
