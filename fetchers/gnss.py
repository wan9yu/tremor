"""GPSJam — GPS/GNSS interference (navigation / electronic-warfare watchlist, tier 2).

Guarded equilibrium: aviation, ICAO, and military PNT authorities guard usable,
jam-free GPS as a defended public good — whole air-traffic and timing systems
depend on it. The leaking hand: a rise in the share of aircraft reporting
degraded/implausible GPS over a region leaks deliberate jamming or spoofing —
active electronic warfare, war fronts, border conflict (the Black Sea, Baltic,
and Eastern Mediterranean have run hot for a while).

Reading: share of tracked aircraft reporting bad GPS worldwide, in percent. A
rise is the alarming move. Jamming campaigns persist for days–weeks, so the
day's aggregate is honest at daily cadence.

Source: GPSJam daily CSV (built on ADS-B Exchange). Keyless; the per-day file is
dated, so we take the most recent available day.
"""
from datetime import datetime, timedelta, timezone

import requests

LINE = "gnss_interference"
LABEL = "GPS interference (% aircraft)"
UNIT = "%"
ANOMALY_DIRECTION = "up"
TIER = 1  # primary (the 4th instrument): global, ~1-day lag, fingerprints conflict

_URL = "https://gpsjam.org/data/{date}-h3_4.csv"
_HEADERS = {"User-Agent": "tremor/1.0 (+https://github.com/wan9yu/tremor)"}


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
        good = bad = 0
        for row in r.text.strip().splitlines()[1:]:  # hex,count_good_aircraft,count_bad_aircraft
            cols = row.split(",")
            if len(cols) >= 3:
                try:
                    good += int(cols[1])
                    bad += int(cols[2])
                except ValueError:
                    continue
        total = good + bad
        if total == 0:
            last_status = "empty"
            continue
        return {
            "raw_value": round(bad / total * 100.0, 4),
            "source_note": f"GPSJam {day}: {bad}/{total} aircraft with bad GPS",
            "obs_date": day,
        }
    return {"raw_value": None, "source_note": f"GPSJam unavailable ({last_status})"}
