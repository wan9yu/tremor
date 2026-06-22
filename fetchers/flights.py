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
from core import adsb

LINE = "flights"
LABEL = "Aircraft airborne (major airspaces)"
UNIT = "aircraft"
ANOMALY_DIRECTION = "down"  # a drop in flight volume is the alarming move
WEEKLY_CYCLE = True  # flight volume has a strong weekday rhythm; de-cycle by weekday

# Fixed, non-overlapping regions with dense community ADS-B coverage.
_REGIONS = [
    ("W/C Europe", 48.5, 9.0),
    ("US East", 39.0, -77.0),
    ("US West", 36.0, -116.0),
    ("E Asia/Japan", 35.0, 137.0),
]


def fetch_daily():
    """Return {"raw_value": float | None, "source_note": str}."""
    return adsb.airborne_over(_REGIONS, "regions")
