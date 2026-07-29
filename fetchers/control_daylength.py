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
a value inconsistent with the date on its own row means the pipeline mishandled a
date — a same-day overwrite from a different run, a timezone boundary, a dedup
misfire, a row written under the wrong label. That class of bug is not
hypothetical here: this project has already been bitten by a +1 date-label
offset and by manual re-runs overwriting a day. `tests/test_control.py` asserts
every committed row against the astronomy for its own date, so the canary is
checked offline on every CI run, independent of any z-score.

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
import requests

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
_HEADERS = {"User-Agent": "tremor/1.0 (+https://github.com/wan9yu/tremor)"}


def fetch_daily():
    """Return {"raw_value": float | None, "source_note": str}."""
    try:
        r = requests.get(_URL, params={"lat": LAT, "lng": LON, "formatted": 0},
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
        "source_note": (f"day length {seconds / 3600:.4f}h at {LAT}N,{LON}E "
                        f"(sunrise {sunrise}Z, sunset {sunset}Z) — CONTROL LINE, "
                        f"no guard, never counted; a tremble here outside "
                        f"Feb-Mar is the instrument, not the world"),
    }
