"""IODA — internet outages (communications infrastructure, tier 1).

Guarded equilibrium: ISPs and states defend a country's internet connectivity
(routing, peering, transit) as critical infrastructure. The leaking hand: when a
country goes dark, a larger force overwhelmed that — a censorship shutdown, a war,
a major cable cut, a grid failure. Counting how many countries are in outage at
once turns local incidents into a global breadth-of-disruption signal.

Reading: number of countries with a ping-slash24-detected outage in the trailing
24h. A rise is the alarming move.

Measurement definition (v2, fixed 2026-07-10): count ONLY outages detected by
IODA's ping-slash24 (active probing) datasource. The v1 series counted events
from every datasource, and IODA activating new detectors mid-series (gtr on
2026-07-01, bgp/merit-nt on 2026-07-05) inflated the count against the old
baseline — sensor inflation, exactly the trap this project bans. Pinning the
datasource makes the definition stable and auditable; the v1 series is archived
at data/archive/net_outages_v1.csv and this series starts fresh.

Source: IODA (Georgia Tech) outages summary API. Keyless.
"""
from datetime import datetime, timezone

import requests

LINE = "net_outages"
LABEL = "Countries with internet outages (IODA ping)"
UNIT = "countries"
ANOMALY_DIRECTION = "up"
TIER = 1  # promoted round 7 into the slot gnss_interference vacated. PROVISIONAL:
# it is the only candidate that is global, zero-lag, and a domain no other line
# covers, but v2 has only a handful of scored readings and does NOT meet the
# 60-reading promotion bar. Reviewed at 60; the status column reports its
# blindness on the page meanwhile.

_URL = "https://api.ioda.inetintel.cc.gatech.edu/v2/outages/summary"
_HEADERS = {"User-Agent": "tremor/1.0 (+https://github.com/wan9yu/tremor)"}
_DATASOURCE = "ping-slash24"  # the one stable detector; see module docstring


def fetch_daily():
    now = int(datetime.now(timezone.utc).timestamp())
    try:
        r = requests.get(
            _URL,
            params={"from": now - 86400, "until": now, "entityType": "country", "limit": 300},
            headers=_HEADERS,
            timeout=25,
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
    who = f" [{', '.join(names)}]" if names else ""
    return {
        "raw_value": float(count),
        "source_note": f"IODA {count} countries with {_DATASOURCE} outages (24h){who}",
    }
