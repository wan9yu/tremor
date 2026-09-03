"""CONTROL LINE — day length at a fixed point. Nothing happens here, on purpose.

This is not an indicator. It has no guard, it measures no tension, and it can
never be counted or promoted. It exists to answer a question no real line can:
**what does this instrument do when the world is definitionally boring?**

Every other line mixes two things — what the world did, and what the apparatus
did. When `grid_frequency` trembled we had to go and read Nordic grid reports to
find out which. A control removes that ambiguity by measuring a quantity with no
world in it: the length of the day at a fixed point on the globe is settled by
orbital mechanics alone. It cannot be disordered. So every tremble it raises is
the instrument, and every tremble it does NOT raise on a day the pipeline was
healthy is a small piece of evidence that the pipeline is healthy.

It earns its slot twice.

**As a pipeline canary.** Day length is an exact function of (date, latitude), so
a value inconsistent with the day the row claims to describe means the pipeline
mishandled a date — a same-day overwrite from a different run, a timezone
boundary, a dedup misfire, a row written under the wrong label. That class of bug
is not hypothetical here: this project has been bitten by a +1 date-label offset
and by manual re-runs overwriting a day.

The canary earned its keep on day four. Rows are dated by COLLECTION in China
time, so the 23:0x UTC run lands on the next China day, and a row dated D carries
the UTC day D−1 — the project's existing convention, previously invisible because
no other line could be checked against ground truth. The fetcher now asks for an
explicit UTC date and records it as ``obs_date``, so the row states which day it
describes instead of leaving it to be inferred. That matters because a one-day
offset moves day length by only about three minutes; `tests/test_control.py`
checks every row against the astronomy for its own ``obs_date`` to within one
minute, which a one-day slip cannot survive. Near the solstices, where
consecutive days differ by seconds, no value check can detect an offset — which
is precisely why the date is recorded rather than inferred.

**As a standing measurement of the estimator.** Replaying 400 days of pure day
length through the unmodified scoring rules produces **30 trembles (7.5%), every
one of them in February and March** — the steep run-up to the spring equinox.
That is the ground truth we could not otherwise obtain: a rolling median lags a
sustained trend, so a trend alone reads as an anomaly, with no disorder present
anywhere. It is the change-versus-level limit seen from the other side, and it
means the expected behaviour of this line is KNOWN IN ADVANCE: it should be quiet
most of the year and noisy approaching the equinoxes. **A tremble here in, say,
August is not the trend — it is us.**

Reading: day length in seconds at 51.4779N, 0.0E (Greenwich — arbitrary, fixed,
and documented so it is never quietly moved). Source: sunrise-sunset.org, free
and keyless. ANOMALY_DIRECTION is nominal; nothing here is ever counted.
"""
import datetime

import requests

from core import useragent

LINE = "control_daylength"
LABEL = "Control: day length at Greenwich (s)"
UNIT = "s"
ANOMALY_DIRECTION = "up"  # nominal only — a control line is never counted
TIER = 2  # context/control: fails the guard gate by construction, never promotable

# Fixed and documented. Moving these would silently redefine the series, so they
# live here as constants rather than inline, and the test asserts against them.
LAT = 51.4779
LON = 0.0

_URL = "https://api.sunrise-sunset.org/json"
_HEADERS = useragent.HEADERS


def fetch_daily():
    """Return {"raw_value": float | None, "source_note": str}."""
    # Ask for an EXPLICIT UTC date rather than letting the server decide what
    # "today" is, and record it as obs_date. Rows here are dated by collection
    # (China time, so a 23:0x UTC run lands on the next China day) while the
    # value describes a UTC day — without obs_date the row cannot say which, and
    # the offset is only ~3 minutes of day length, far too small to infer back
    # from the value. Making it explicit is what lets the canary be tight.
    day = datetime.datetime.now(datetime.timezone.utc).date()
    try:
        r = requests.get(_URL, params={"lat": LAT, "lng": LON, "date": day.isoformat(),
                                       "formatted": 0},
                         headers=_HEADERS, timeout=20)
    except requests.RequestException as e:
        return {"raw_value": None,
                "source_note": f"sunrise-sunset request failed: {type(e).__name__}"}
    if r.status_code != 200:
        return {"raw_value": None, "source_note": f"sunrise-sunset HTTP {r.status_code}"}
    try:
        payload = r.json()
    except ValueError:
        return {"raw_value": None, "source_note": "sunrise-sunset returned a non-JSON body"}
    if payload.get("status") != "OK":
        return {"raw_value": None,
                "source_note": f"sunrise-sunset status {payload.get('status')}"}
    results = payload.get("results") or {}
    try:
        seconds = float(results["day_length"])
    except (KeyError, TypeError, ValueError):
        return {"raw_value": None, "source_note": "sunrise-sunset gave no usable day_length"}
    sunrise = (results.get("sunrise") or "")[11:19]
    sunset = (results.get("sunset") or "")[11:19]
    return {
        "raw_value": seconds,
        "source_note": (f"day length {seconds / 3600:.4f}h at {LAT}N,{LON}E on {day} "
                        f"(sunrise {sunrise}Z, sunset {sunset}Z) — CONTROL LINE, "
                        f"no guard, never counted; a tremble here outside "
                        f"Feb-Mar is the instrument, not the world"),
        "obs_date": day.isoformat(),
    }
