"""GPSJam — GPS/GNSS interference (navigation / electronic warfare, tier 2).

Guarded equilibrium: aviation, ICAO, and military PNT authorities guard usable,
jam-free GPS as a defended public good — whole air-traffic and timing systems
depend on it. The leaking hand: a rise in the share of aircraft reporting
degraded/implausible GPS over a region leaks deliberate jamming or spoofing —
active electronic warfare, war fronts, border conflict (the Black Sea, Baltic,
and Eastern Mediterranean have run hot for a while).

Reading: share of tracked aircraft reporting bad GPS worldwide, in percent. A
rise is the alarming move. Jamming campaigns persist for days–weeks, so the
day's aggregate is honest at daily cadence.

KNOWN LIMIT — this is one WORLDWIDE ratio and has no regional sensitivity. A
jamming campaign confined to one theatre is diluted by global traffic: through
the July 2026 Gulf escalation the bad-GPS share inside the Iran/Hormuz airspace
ran near 16% while this line read only 0.47%. Regionalizing it was investigated
in radar round 7 and deferred on two grounds: every candidate box that detected
the episode lost the detection when its edge moved one degree, and the 39-
observation baseline then in hand made the sampling frame look like it had
grown by an order of magnitude.

CORRECTED round 9 (2026-08-03), once the line was seeded to four years of real
history (radar-log.md:499-511): the July 2026 window re-scores to z = +2.87
(49 alarm-direction trembles record-wide across 1,452 scored days) — the line
DID register the escalation, it just fell short of the |z|>3 bar; the flat
0.47% reading above was an artifact of the thin baseline it was first judged
against, not evidence the line never moves. The sampling-frame growth was
overstated too: measured by yearly median across the seeded record it is
about 1.23x, not the order-of-magnitude the round-7 estimate implied (9
broken partial files out of 1,423). What survives: +2.87 is still under the
alarm bar, so a worldwide ratio still cannot be trusted to catch a regional
campaign — treat the reading as a global floor, not as a conflict detector.

Source: GPSJam daily CSV (built on ADS-B Exchange). Keyless; the per-day file is
dated, so we take the most recent available day.
"""
from datetime import datetime, timedelta, timezone

import requests

from core import useragent

LINE = "gnss_interference"
LABEL = "GPS interference (% aircraft)"
UNIT = "%"
ANOMALY_DIRECTION = "up"
TIER = 2  # demoted round 7: one worldwide ratio cannot see a regional campaign

_URL = "https://gpsjam.org/data/{date}-h3_4.csv"
_HEADERS = useragent.HEADERS


def counts_from_csv(text):
    """``(bad, total)`` aircraft summed over every h3 cell of one day's file.

    Rows are ``hex,count_good_aircraft,count_bad_aircraft``. The seeder
    aggregates whole archive days through this same function, which is what
    makes its "identical to the live fetcher" claim true by construction.
    """
    good = bad = 0
    for row in text.strip().splitlines()[1:]:
        cols = row.split(",")
        if len(cols) >= 3:
            try:
                good += int(cols[1])
                bad += int(cols[2])
            except ValueError:
                continue
    return bad, good + bad


def fetch_daily():
    last_status = None
    for back in range(0, 4):  # today may not be published yet; walk back a few days
        day = (datetime.now(timezone.utc) - timedelta(days=back)).strftime("%Y-%m-%d")
        try:
            r = requests.get(_URL.format(date=day), headers=_HEADERS, timeout=20)
        except requests.RequestException as e:
            last_status = type(e).__name__
            continue
        if r.status_code != 200 or len(r.text) < 100:
            last_status = f"HTTP {r.status_code}"
            continue
        bad, total = counts_from_csv(r.text)
        if total == 0:
            last_status = "empty"
            continue
        return {
            "raw_value": round(bad / total * 100.0, 4),
            "source_note": f"GPSJam {day}: {bad}/{total} aircraft with bad GPS",
            "obs_date": day,
        }
    return {"raw_value": None, "source_note": f"GPSJam unavailable ({last_status})"}
