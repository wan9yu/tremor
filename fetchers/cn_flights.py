"""China airborne aircraft — airspace WATCHLIST line (tier 2).

Same idea as the main flights line, scoped to China's three busiest metros
(Beijing, Shanghai, Guangzhou). This is a TIER-2 / watchlist indicator: scraped
every day so history and z-score accumulate, but NOT displayed and NOT counted
toward the trembling resonance — a candidate being observed for promotion.

Why watchlist, not primary: free community ADS-B coverage over mainland China is
sparse and feeder-dependent (measured ~30-60 aircraft over each metro vs ~800
over Europe), so the count partly reflects receiver availability, not real air
traffic. Keeping it tier-2 lets us watch whether it becomes a usable signal
without letting that noise into the live instrument. Promote by setting TIER = 1.
"""
import requests

LINE = "cn_flights"
LABEL = "China aircraft airborne (watchlist)"
UNIT = "aircraft"
ANOMALY_DIRECTION = "down"
TIER = 2  # watchlist — collected daily, not displayed, not counted
WEEKLY_CYCLE = True

_RADIUS_NM = 250
_REGIONS = [("Beijing", 39.9, 116.4), ("Shanghai", 31.2, 121.5), ("Guangzhou", 23.0, 113.5)]
_PROVIDERS = [
    ("airplanes.live", "https://api.airplanes.live/v2/point/{lat}/{lon}/{r}"),
    ("adsb.fi", "https://opendata.adsb.fi/api/v2/lat/{lat}/lon/{lon}/dist/{r}"),
    ("adsb.lol", "https://api.adsb.lol/v2/lat/{lat}/lon/{lon}/dist/{r}"),
]
_HEADERS = {
    "User-Agent": "tremor/1.0 (+https://github.com/wan9yu/tremor)",
    "Accept": "application/json",
}


def _region_airborne(lat, lon):
    for name, template in _PROVIDERS:
        url = template.format(lat=lat, lon=lon, r=_RADIUS_NM)
        try:
            r = requests.get(url, headers=_HEADERS, timeout=15)
        except requests.RequestException:
            continue
        if r.status_code != 200:
            continue
        try:
            payload = r.json()
        except ValueError:
            continue
        aircraft = payload.get("ac") or payload.get("aircraft") or []
        return sum(1 for a in aircraft if isinstance(a, dict) and a.get("alt_baro") != "ground"), name
    return None, None


def fetch_daily():
    total = 0
    providers = []
    missing = []
    for name, lat, lon in _REGIONS:
        airborne, provider = _region_airborne(lat, lon)
        if airborne is None:
            missing.append(name)
        else:
            total += airborne
            providers.append(provider)
    if missing:
        return {
            "raw_value": None,
            "source_note": "China ADS-B incomplete, no data for: " + ", ".join(missing),
        }
    used = ", ".join(sorted(set(providers)))
    return {
        "raw_value": float(total),
        "source_note": f"ADS-B airborne over {len(_REGIONS)} China metros via {used}",
    }
