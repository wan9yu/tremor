"""Community ADS-B — airspace tension line (flight-volume proxy). The origin line.

Guarded equilibrium: airlines' profit motive keeps planes flying on schedule.
The leaking hand: a sharp drop in airborne volume betrays a larger force that
overwhelmed that motive — closed airspace, severe weather, pandemics, control
lockdowns. Military airspace closures are not announced; they leave a shadow
only in how many aircraft are actually in the air. Flights become a side channel
for the otherwise invisible.

Reading: number of aircraft airborne across a FIXED set of busy, densely-fed
airspaces, sampled at the same time each day. A sudden DROP is the alarming move.

Source: keyless community ADS-B aggregators (airplanes.live / adsb.fi / adsb.lol),
which — unlike OpenSky's anonymous endpoint — respond reliably from shared cloud
IPs and need no key or registration. Each region is tried against the providers
in order, so counts normally come from one provider and stay comparable. Coverage
is volunteer-based, so this is a regional proxy, not a global census; that's fine
because the z-score reacts to a line's deviation from its own baseline, not its
absolute level. The region set is fixed: if any region has no data, the day is
written empty (a partial sum would look like a flight drop).
"""
import requests

LINE = "flights"
LABEL = "Aircraft airborne (major airspaces)"
UNIT = "aircraft"
ANOMALY_DIRECTION = "down"  # a drop in flight volume is the alarming move
WEEKLY_CYCLE = True  # flight volume has a strong weekday rhythm; de-cycle by weekday

_RADIUS_NM = 250
# Fixed, non-overlapping regions with dense community ADS-B coverage.
_REGIONS = [
    ("W/C Europe", 48.5, 9.0),
    ("US East", 39.0, -77.0),
    ("US West", 36.0, -116.0),
    ("E Asia/Japan", 35.0, 137.0),
]
# Keyless providers, tried in this order per region (stable order -> stable counts).
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
    """Airborne aircraft in one region as (count, provider), or (None, None)."""
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
        # alt_baro == "ground" marks a parked/taxiing aircraft; count the rest.
        airborne = sum(
            1 for a in aircraft if isinstance(a, dict) and a.get("alt_baro") != "ground"
        )
        return airborne, name
    return None, None


def fetch_daily():
    """Return {"raw_value": float | None, "source_note": str}."""
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
            "source_note": (
                "ADS-B coverage incomplete, no data for: "
                + ", ".join(missing)
                + " (count needs every region to stay comparable)"
            ),
        }
    used = ", ".join(sorted(set(providers)))
    return {
        "raw_value": float(total),
        "source_note": f"ADS-B airborne over {len(_REGIONS)} regions via {used}",
    }
