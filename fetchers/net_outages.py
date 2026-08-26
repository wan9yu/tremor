"""IODA — internet outages (communications infrastructure, tier 1).

Guarded equilibrium: ISPs and states defend a country's internet connectivity
(routing, peering, transit) as critical infrastructure. The leaking hand: when a
country goes dark, a larger force overwhelmed that — a censorship shutdown, a war,
a major cable cut, a grid failure. Counting how many countries are in outage at
once turns local incidents into a global breadth-of-disruption signal.

Reading: number of countries with a ping-slash24-detected outage in the day's
completed 24h window (settled, see v3). A rise is the alarming move.

Measurement definition (v2, fixed 2026-07-10): count ONLY outages detected by
IODA's ping-slash24 (active probing) datasource. The v1 series counted events
from every datasource, and IODA activating new detectors mid-series (gtr on
2026-07-01, bgp/merit-nt on 2026-07-05) inflated the count against the old
baseline — sensor inflation, exactly the trap this project bans. Pinning the
datasource makes the definition stable and auditable; the v1 series is archived
at data/archive/net_outages_v1.csv and this series starts fresh.

Window definition (v3, R23.1, 2026-08-25): count a COMPLETED window ending at the
most recent 22:00:00Z at least a day old, not a trailing window ending at
collection time. The trailing window's last hours were inside IODA's ~24h
detection latency, which retimes and inflates the count: on 2026-08-24 it read 12
countries (z=4.69, a tier-1 FALSE ALARM) where the completed window settles to 4.
Settling makes the count STABLE (reproducible, no longer query-time-dependent)
and aligned with the seed, which already fetched each day at 22:00Z. CORRECTED
2026-08-26: the earlier "removes the whole latency-injection class" was overstated.
Settle does NOT filter the artifact — a synchronized-onset common-mode cluster is a
stable set of IODA events at a real timestamp, so it lives in one settled window and
would tremble there. The 08-24 cluster's true home is the 08-23 settled window (the
same twelve countries, stably), so a future artifact of this shape WOULD alarm on
its own date; it is a DETECT-AND-ADJUDICATE class (the reconciliation tripwire flags
it, the R23 five-agent playbook attributes it), not one settle closes. Rows
2026-07-10 -> 2026-08-25 are the unsettled trailing-window stretch (and hold the
adjudicated 08-24 artifact, kept forward-only); the switch day carries a one-time
~24h window overlap with the last unsettled row. Cost: a ~1-day lag (was zero-lag),
inside the tier-1 freshness bar. See annotations.csv for the method + correction rows.

Source: IODA (Georgia Tech) outages summary API. Keyless.
"""
from datetime import datetime, timedelta, timezone

import requests

LINE = "net_outages"
LABEL = "Countries with internet outages (IODA ping)"
UNIT = "countries"
ANOMALY_DIRECTION = "up"
TIER = 1  # promoted round 7 into the slot gnss_interference vacated. PROVISIONAL:
# it is the only candidate that is global and a domain no other line covers
# (settled to a completed D-1 22:00Z window since R23.1 — ~1-day lagged, was
# zero-lag before then), but v2 has only a handful of scored readings and does NOT meet the
# 60-reading promotion bar. Reviewed at 60; the status column reports its
# blindness on the page meanwhile.
QUANTUM = 1  # countries: a count, and the resolution of the reading is one of them.
# Without this floor the line goes SILENT exactly when it matters. Its readings
# are small integers (the record holds 0..6, median 3), and the robust scale
# collapses to zero once about a quarter of the window's pairs tie — measured,
# twelve consecutive days of "1 country" is enough. The day after such a run, a
# 160-country mass outage scores z=None: no verdict, no flag, on a tier-1 line.
# Flooring the scale at one country says the honest thing — a window of
# identical counts has spread finer than the instrument can see, not zero
# spread. It has never bound on the real record (smallest Qn used: 1.610).

_URL = "https://api.ioda.inetintel.cc.gatech.edu/v2/outages/summary"
_HEADERS = {"User-Agent": "tremor/1.0 (+https://github.com/wan9yu/tremor)"}
_DATASOURCE = "ping-slash24"  # the one stable detector; see module docstring

# WHEN THE MONITOR FAILS, IT REPORTS THE WORLD AS FAILING. Twelve days in the
# 2022-2026 record show IODA returning essentially every entity it watches as
# being in outage — 220 of 222 on 2025-03-25, 191 of 191 on 2026-06-20 —
# alphabetically complete, Antarctica and Andorra and Australia together, and
# fully recovered the next day. No cause makes those countries dark at once and
# well again in twenty-four hours; what went dark was IODA's own view.
#
# The signature is a CONJUNCTION and both halves are needed: a large absolute
# count, and a count that is essentially everything the service could see. The
# ratio alone flags 74 days (on a quiet day three outages out of six watched
# entities is half of them, and perfectly real); the count alone would one day
# refuse a genuine catastrophe. Together they select exactly those twelve days
# across 1,621, and the nearest day they do NOT select is 45 countries at a
# ratio of 0.45 — a wide margin on both axes.
#
# Such a reading is not a small number or a big number: it is not a reading of
# the world at all, the same verdict cnh_cny reaches when its two legs are
# quoted hours apart. So the day is written EMPTY with the reason stated, and
# the raw counts stay in the note so the judgement can be re-examined.
_SWEEP_MIN_COUNTRIES = 100
_SWEEP_MIN_SHARE = 0.8


def monitor_swept(hits, entities):
    """True when the response describes IODA's own blindness, not the world."""
    return (entities and hits >= _SWEEP_MIN_COUNTRIES
            and hits / entities >= _SWEEP_MIN_SHARE)


def _settled_window(now_ts):
    """``(from, until, obs_date)`` for the latest COMPLETE 24h window ending at the
    most recent 22:00:00Z that is at least a full day before ``now_ts``.

    THE SETTLE RULE (R23.1). The live line used to count a trailing 24h window
    ending at collection time; that window's last hours sit inside IODA's ~24h
    detection latency, which retimes and inflates the count — on 2026-08-24 it
    read 12 countries (z=4.69, a tier-1 false alarm) where the completed window
    settles to 4. Counting a COMPLETED window makes the count STABLE (reproducible,
    not query-time-dependent) and aligns the live tail with the seed, which already
    fetched each day's window at ``_WINDOW_HOUR=22`` (97% of the record). It does NOT
    filter the artifact itself (a synchronized-onset cluster lives, stably, in its
    own settled window and would tremble there — see the module docstring's 2026-08-26
    correction and the reconciliation tripwire). A run firing before 22:00Z
    self-corrects one day earlier rather than reading a still-forming edge. The cost is
    a ~1-day lag, inside the tier-1 freshness bar.
    """
    cutoff = now_ts - 86400
    end = datetime.fromtimestamp(cutoff, timezone.utc).replace(
        hour=22, minute=0, second=0, microsecond=0)
    if end.timestamp() > cutoff:
        end -= timedelta(days=1)
    start = end - timedelta(days=1)
    return int(start.timestamp()), int(end.timestamp()), end.date().isoformat()


def fetch_daily():
    frm, until, obs = _settled_window(int(datetime.now(timezone.utc).timestamp()))
    try:
        r = requests.get(
            _URL,
            params={"from": frm, "until": until, "entityType": "country", "limit": 400},
            headers=_HEADERS,
            timeout=40,
        )
    except requests.RequestException as e:
        return {"raw_value": None, "source_note": f"IODA request failed: {type(e).__name__}"}
    if r.status_code != 200:
        return {"raw_value": None, "source_note": f"IODA HTTP {r.status_code}"}
    try:
        data = r.json().get("data")
    except ValueError:
        return {"raw_value": None, "source_note": "IODA returned a non-JSON body"}
    if data is None:
        return {"raw_value": None, "source_note": "IODA returned no data field"}
    # Count only countries whose outage was seen by the pinned datasource, and
    # record WHICH ones: a count alone makes a tremble unattributable, and every
    # tremble in this instrument has to be answerable with "caused by what?".
    hit = [d for d in data
           if any(k.startswith(_DATASOURCE) for k in (d.get("scores") or {}))]
    names = sorted(
        (d.get("entity") or {}).get("name") or (d.get("entity") or {}).get("code") or "?"
        for d in hit
    )
    count = len(hit)
    # A sweep / error / dark return carries NO obs_date: a refused window's date
    # must not stale-block a later genuine read of that same settled window.
    if monitor_swept(count, len(data)):
        return {
            "raw_value": None,
            "source_note": (f"no reading: IODA reported {count} of {len(data)} watched "
                            f"entities in outage — a sweep of essentially everything "
                            f"it can see, which is the monitor losing its own vantage "
                            f"points, not the world going dark"),
        }
    who = f" [{', '.join(names)}]" if names else ""
    return {
        "raw_value": float(count),
        "source_note": f"IODA {count} countries with {_DATASOURCE} outages (24h to {obs} 22:00Z){who}",
        "obs_date": obs,
    }
