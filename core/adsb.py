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
    """Airborne aircraft in one region as (count, provider), or (None, None)."""
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
        return sum(
            1 for a in aircraft if isinstance(a, dict) and a.get("alt_baro") != "ground"
        ), name
    return None, None


def airborne_over(regions, area_word):
    """Sum airborne aircraft over every region in ``regions``.

    ``area_word`` names the region kind for the note (e.g. "regions",
    "China metros"). Returns {"raw_value": float | None, "source_note": str};
    a missing region yields an empty reading so the total stays comparable.
    """
    total = 0
    providers = []
    missing = []
    for name, lat, lon in regions:
        airborne, provider = region_airborne(lat, lon)
        if airborne is None:
            missing.append(name)
        else:
            total += airborne
            providers.append(provider)
    if missing:
        return {
            "raw_value": None,
            "source_note": (
                f"ADS-B over {area_word} incomplete, no data for: "
                + ", ".join(missing)
                + " (count needs every region to stay comparable)"
            ),
        }
    used = ", ".join(sorted(set(providers)))
    return {
        "raw_value": float(total),
        "source_note": f"ADS-B airborne over {len(regions)} {area_word} via {used}",
    }
