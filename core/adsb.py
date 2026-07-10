"""Shared community-ADS-B helper for the airspace lines.

Counts airborne aircraft over a set of regions using keyless aggregators
(airplanes.live / adsb.fi / adsb.lol), tried in order per region so a count
normally comes from one provider and stays comparable. The region set is fixed
and ALL regions are required: a partial sum would look like a flight drop, so a
missing region yields an empty reading instead.

Both flights lines (global and the China watchlist) share this so the provider
list, headers, parsing, and the require-all-regions rule live in exactly one
place.
"""
import requests

RADIUS_NM = 250
# Sanity floor: a busy region snapshot below this is either a degraded feed
# (HTTP 200 with a thin aircraft list) or a genuine collapse. One provider
# reporting under-floor is treated as suspect and the next provider is tried;
# TWO independent providers agreeing under-floor is accepted as a real reading
# — corroboration converts "degraded sensor" into "measured collapse", so the
# instrument cannot blind itself at exactly the moment it matters.
REGION_FLOOR = 30
PROVIDERS = [
    ("airplanes.live", "https://api.airplanes.live/v2/point/{lat}/{lon}/{r}"),
    ("adsb.fi", "https://opendata.adsb.fi/api/v2/lat/{lat}/lon/{lon}/dist/{r}"),
    ("adsb.lol", "https://api.adsb.lol/v2/lat/{lat}/lon/{lon}/dist/{r}"),
]
HEADERS = {
    "User-Agent": "tremor/1.0 (+https://github.com/wan9yu/tremor)",
    "Accept": "application/json",
}


def region_airborne(lat, lon):
    """Airborne aircraft in one region as (count, provider), or (None, reason)."""
    thin = []  # under-floor readings seen so far: (count, provider)
    for name, template in PROVIDERS:
        url = template.format(lat=lat, lon=lon, r=RADIUS_NM)
        try:
            r = requests.get(url, headers=HEADERS, timeout=15)
        except requests.RequestException:
            continue
        if r.status_code != 200:
            continue
        try:
            payload = r.json()
        except ValueError:
            continue
        aircraft = payload.get("ac") or payload.get("aircraft") or []
        # alt_baro == "ground" marks a parked/taxiing aircraft; count the rest.
        count = sum(
            1 for a in aircraft if isinstance(a, dict) and a.get("alt_baro") != "ground"
        )
        if count >= REGION_FLOOR:
            return count, name
        if thin:  # a second provider agrees it's thin -> a real reading
            return thin[0][0], f"{thin[0][1]} (low, corroborated by {name})"
        thin.append((count, name))
    if thin:
        return None, f"suspected degraded feed ({thin[0][0]} via {thin[0][1]}, uncorroborated)"
    return None, "no provider responded"


def airborne_over(regions, area_word):
    """Sum airborne aircraft over every region in ``regions``.

    ``area_word`` names the region kind for the note (e.g. "regions",
    "China metros"). Returns {"raw_value": float | None, "source_note": str};
    a missing region yields an empty reading so the total stays comparable.
    Per-region counts are recorded in the note so a degraded provider or a
    one-region anomaly stays diagnosable after the fact.
    """
    total = 0
    parts = []
    providers = []
    missing = []
    for name, lat, lon in regions:
        airborne, provider = region_airborne(lat, lon)
        if airborne is None:
            missing.append(f"{name} ({provider})")
        else:
            total += airborne
            parts.append(f"{name}={airborne}")
            providers.append(provider)
    if missing:
        return {
            "raw_value": None,
            "source_note": (
                f"ADS-B over {area_word} incomplete: "
                + "; ".join(missing)
                + " (count needs every region to stay comparable)"
            ),
        }
    used = ", ".join(sorted(set(providers)))
    return {
        "raw_value": float(total),
        "source_note": f"ADS-B {area_word} [{', '.join(parts)}] via {used}",
    }
