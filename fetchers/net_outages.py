"""IODA — internet outages (infrastructure tension watchlist, tier 2).

Guarded equilibrium: ISPs and states defend a country's internet connectivity
(routing, peering, transit) as critical infrastructure. The leaking hand: when a
country goes dark, a larger force overwhelmed that — a censorship shutdown, a war,
a major cable cut, a grid failure. Counting how many countries are in outage at
once turns local incidents into a global breadth-of-disruption signal.

Reading: number of countries with a detected internet outage in the trailing 24h.
A rise is the alarming move. Outages persist hours–days, so daily sampling is
honest.

Source: IODA (Georgia Tech) outages summary API. Keyless.
"""
from datetime import datetime, timezone

import requests

LINE = "net_outages"
LABEL = "Countries with internet outages (IODA)"
UNIT = "countries"
ANOMALY_DIRECTION = "up"
TIER = 2

_URL = "https://api.ioda.inetintel.cc.gatech.edu/v2/outages/summary"
_HEADERS = {"User-Agent": "tremor/1.0 (+https://github.com/wan9yu/tremor)"}


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
    # The summary lists only entities that had an outage event in the window.
    return {
        "raw_value": float(len(data)),
        "source_note": f"IODA {len(data)} countries with outage events (24h)",
    }
