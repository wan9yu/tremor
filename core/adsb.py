"""Shared community-ADS-B helper for the airspace lines.

Counts airborne aircraft over a set of regions using keyless aggregators
(airplanes.live / adsb.fi / adsb.lol). EVERY provider is asked for EVERY region
and the maximum is taken — see ``region_airborne`` for why that is the right
rule and what it costs. The region set is fixed and ALL regions are required: a
partial sum would look like a flight drop, so a missing region yields an empty
reading instead.

The provider list, headers, parsing, and the require-all-regions rule live here
in one place for whichever airspace lines use them.
"""
import requests

from core import useragent

RADIUS_NM = 250
# A busy region reading below this is remarkable enough to say so in the note.
# It is a DISCLOSURE, not a veto: every provider is consulted anyway, so if they
# all agree the sky is that empty, the sky is that empty — the instrument must
# not refuse to report a collapse at exactly the moment it matters.
REGION_FLOOR = 30
# Report the provider spread in the note once it exceeds this fraction — a
# widening gap between aggregators is how a degrading feeder network announces
# itself, and it should be visible in the record rather than silently absorbed.
PROVIDER_SPREAD_NOTE = 0.10
PROVIDERS = [
    ("airplanes.live", "https://api.airplanes.live/v2/point/{lat}/{lon}/{r}"),
    ("adsb.fi", "https://opendata.adsb.fi/api/v2/lat/{lat}/lon/{lon}/dist/{r}"),
    ("adsb.lol", "https://api.adsb.lol/v2/lat/{lat}/lon/{lon}/dist/{r}"),
]
HEADERS = {**useragent.HEADERS, "Accept": "application/json"}


def _provider_count(template, lat, lon):
    """Airborne aircraft one provider reports for a region, or None if it can't say."""
    try:
        r = requests.get(template.format(lat=lat, lon=lon, r=RADIUS_NM),
                         headers=HEADERS, timeout=15)
    except requests.RequestException:
        return None
    if r.status_code != 200:
        return None
    try:
        payload = r.json()
    except ValueError:
        return None
    aircraft = payload.get("ac") or payload.get("aircraft") or []
    # alt_baro == "ground" marks a parked/taxiing aircraft; count the rest.
    return sum(1 for a in aircraft
               if isinstance(a, dict) and a.get("alt_baro") != "ground")


def region_airborne(lat, lon, per_provider=None):
    """Airborne aircraft in one region as (count, note), or (None, reason).

    ``per_provider``, if given a dict, is filled with every provider's own
    count. All three are already fetched to take the maximum; discarding the
    other two throws away the only evidence that would show a provider
    degrading, and it cannot be recovered afterwards.

    EVERY provider is asked, every day, and the MAXIMUM is taken. The asymmetry
    that makes this the right rule: a coverage failure can only LOSE aircraft —
    a dead receiver or a thinned feeder network means fewer planes seen, and
    nothing makes an aggregator invent one. So when providers disagree, the
    highest count is the most complete view of the sky, and a single provider
    having a bad day can no longer set the reading.

    This replaces asking one provider and only consulting a second when the
    count fell under an absolute floor of 30. That floor never engaged at the
    magnitude that matters: a region normally carrying 700-1000 aircraft could
    lose two thirds of its coverage and still be accepted from the first
    provider without a second opinion. Corroboration now happens on every
    region every day rather than only in the extreme.

    Measured cost of the change: taking the max instead of the first responder
    raises the four-region total by about 0.5%, against a robust scale of ~11%
    of the median — inside the line's own daily noise. The spread between
    providers is recorded in the note whenever it is wide, so a degrading
    provider becomes visible in the record instead of silently setting the level.
    """
    seen = []
    for name, template in PROVIDERS:
        count = _provider_count(template, lat, lon)
        if count is not None:
            seen.append((count, name))
            if per_provider is not None:
                per_provider[name] = count
    if not seen:
        return None, "no provider responded"

    best, best_name = max(seen)
    if len(seen) == 1:
        note = f"{best_name} (sole responder)"
    else:
        low = min(c for c, _ in seen)
        spread = (best - low) / best if best else 0.0
        note = best_name if spread <= PROVIDER_SPREAD_NOTE else (
            f"{best_name} (providers disagreed {low}-{best}, "
            f"{spread * 100:.0f}% apart — max taken)")
    # An absolute floor is still worth keeping as a last sanity check, but it is
    # now a DISCLOSURE and not a veto: if every provider sees almost nothing, the
    # sky really is that empty and the instrument must not refuse to say so.
    if best < REGION_FLOOR:
        note += f" [under floor {REGION_FLOOR}: all {len(seen)} providers agree]"
    return best, note


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
    components = {}
    for name, lat, lon in regions:
        per_provider = {}
        airborne, provider = region_airborne(lat, lon, per_provider=per_provider)
        if airborne is not None:
            components[name] = float(airborne)
        for pname, pcount in per_provider.items():
            components[f"{name}/{pname}"] = float(pcount)
        if airborne is None:
            missing.append(f"{name} ({provider})")
        else:
            total += airborne
            parts.append(f"{name}={airborne}")
            providers.append(provider)
    if missing:
        # Components are recorded even on a failed reading: a dark day is exactly
        # when knowing WHICH region went missing is worth most, and it is the one
        # day the scalar cannot tell you.
        return {
            "raw_value": None,
            "source_note": (
                f"ADS-B over {area_word} incomplete: "
                + "; ".join(missing)
                + " (count needs every region to stay comparable)"
            ),
            "components": components,
        }
    used = ", ".join(sorted(set(providers)))
    return {
        "raw_value": float(total),
        "source_note": f"ADS-B {area_word} [{', '.join(parts)}] via {used}",
        "components": components,
    }
