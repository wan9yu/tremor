"""OpenSky Network — airspace tension line (flight-volume proxy).

Guarded equilibrium: airlines' profit motive keeps planes flying on schedule.
The leaking hand: a sharp drop in airborne volume betrays a larger force that
overwhelmed that motive — closed airspace, severe weather, pandemics, control
lockdowns. Military airspace closures are not announced; they leave a shadow
only in how many aircraft are actually in the air. Flights become a side
channel for the otherwise invisible.

Reading: number of aircraft currently airborne worldwide (a daily snapshot).
A sudden DROP is the alarming direction.

Source: OpenSky REST API /states/all.
  - Works anonymously (rate-limited). With OAuth2 client credentials
    (OPENSKY_CLIENT_ID / OPENSKY_CLIENT_SECRET) it draws on a higher daily
    credit budget. Basic auth was retired in 2026-03; this uses the
    client_credentials grant.
"""
import os
import time

import requests

LINE = "flights"
LABEL = "Aircraft airborne (OpenSky)"
UNIT = "aircraft"
ANOMALY_DIRECTION = "down"  # a drop in flight volume is the alarming move

_STATES_URL = "https://opensky-network.org/api/states/all"
_TOKEN_URL = (
    "https://auth.opensky-network.org/auth/realms/"
    "opensky-network/protocol/openid-connect/token"
)


def _bearer_token():
    """Exchange client credentials for a short-lived bearer token, or None."""
    cid = os.environ.get("OPENSKY_CLIENT_ID")
    secret = os.environ.get("OPENSKY_CLIENT_SECRET")
    if not (cid and secret):
        return None
    try:
        r = requests.post(
            _TOKEN_URL,
            timeout=10,
            data={
                "grant_type": "client_credentials",
                "client_id": cid,
                "client_secret": secret,
            },
        )
    except requests.RequestException:
        return None
    if r.status_code == 200:
        try:
            return r.json().get("access_token")
        except ValueError:
            return None
    return None


def fetch_daily():
    """Return {"raw_value": float | None, "source_note": str}."""
    headers = {}
    auth_mode = "anonymous"
    token = _bearer_token()
    if token:
        headers["Authorization"] = "Bearer " + token
        auth_mode = "oauth"
    # OpenSky's public endpoint is occasionally slow to connect from shared cloud
    # IPs; retry a couple of times so one cold timeout doesn't blank the line.
    r = None
    last_err = None
    for attempt in range(3):
        try:
            r = requests.get(_STATES_URL, headers=headers, timeout=30)
            break
        except requests.RequestException as e:
            last_err = type(e).__name__
            if attempt < 2:
                time.sleep(3)
    if r is None:
        return {
            "raw_value": None,
            "source_note": f"OpenSky /states/all request failed after retries: {last_err}",
        }
    if r.status_code != 200:
        return {
            "raw_value": None,
            "source_note": f"OpenSky /states/all HTTP {r.status_code} ({auth_mode})",
        }
    try:
        states = r.json().get("states") or []
    except ValueError:
        return {"raw_value": None, "source_note": "OpenSky returned a non-JSON body"}
    # In a state vector, index 8 is on_ground (bool). Count those explicitly
    # flying; guard the index so a short/malformed vector is skipped, not raised,
    # and so an unknown (None) ground status is not miscounted as airborne.
    airborne = sum(1 for s in states if s and len(s) > 8 and s[8] is False)
    return {
        "raw_value": float(airborne),
        "source_note": f"OpenSky /states/all airborne count ({auth_mode}); {len(states)} states total",
    }
