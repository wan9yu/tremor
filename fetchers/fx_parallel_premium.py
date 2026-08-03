"""Argentina parallel-FX premium — capital-control tension watchlist (tier 2).

Guarded equilibrium: Argentina's central bank defends an official USD/ARS rate
(reserves, capital controls, the "cepo"). The leaking hand: when the black-market
("blue") rate trades far above the official one, capital is trapped and controls
are straining — the parallel premium is what people will actually pay to get
dollars out, the same mechanism as the Korea kimchi premium but for a chronically
controlled currency. A blowout in the premium leaks accelerating flight or a
devaluation the official rate has not admitted yet.

Reading: (blue sell rate / official sell rate − 1), in percent. A rise is the
alarming move. Distinct from cnh_cny (a managed-float spread of a few pips) and
from capital_premium (Korea, a convertible currency): this is a hard-controlled
regime where the premium runs in the tens of percent.

Source: dolarapi.com (keyless JSON, updated intraday). Both legs are read in one
pass; if either is missing the reading is empty rather than half-computed.

THE SOURCE'S TIMESTAMP IS A REPUBLISH STAMP, NOT AN OBSERVATION DATE. dolarapi's
fechaActualizacion advances every day even while both markets are closed: the
identical frozen quotes (banks do not trade the oficial on weekends, and the
premium cannot move without that leg) arrived under three distinct dates every
weekend, so the dedup rule structurally never fired and each frozen quote was
scored three times — the exact pseudo-replication obs_date exists to kill. A
weekend stamp is therefore mapped back to its Friday, which is the day the
quotes actually describe. (A weekday holiday still slips through — there is no
keyless calendar of Argentine bank holidays — so the guard is honest for the
52 weekends a year and silent on the handful of holidays.)
"""
import datetime

import requests

LINE = "fx_parallel_premium"
LABEL = "Argentina blue-vs-official FX premium (%)"
UNIT = "%"
ANOMALY_DIRECTION = "up"
TIER = 2

_BLUE = "https://dolarapi.com/v1/dolares/blue"
_OFICIAL = "https://dolarapi.com/v1/dolares/oficial"
_HEADERS = {"User-Agent": "tremor/1.0 (+https://github.com/wan9yu/tremor)"}


def _leg(url):
    r = requests.get(url, headers=_HEADERS, timeout=20)
    if r.status_code != 200:
        raise ValueError(f"HTTP {r.status_code}")
    d = r.json()
    return float(d["venta"]), (d.get("fechaActualizacion") or "")[:10]


def _observation_date(stamp):
    """The trading day a quote describes: a weekend stamp maps to its Friday."""
    try:
        day = datetime.date.fromisoformat(stamp)
    except ValueError:
        return stamp
    friday_shift = max(0, day.weekday() - 4)  # Sat -> 1, Sun -> 2
    return (day - datetime.timedelta(days=friday_shift)).isoformat()


def fetch_daily():
    try:
        blue, blue_date = _leg(_BLUE)
        oficial, _ = _leg(_OFICIAL)
    except (requests.RequestException, ValueError, KeyError, TypeError) as e:
        return {"raw_value": None, "source_note": f"dolarapi unavailable: {type(e).__name__}"}
    if oficial <= 0:
        return {"raw_value": None, "source_note": "dolarapi official rate not positive"}
    premium = (blue / oficial - 1.0) * 100.0
    obs = _observation_date(blue_date)
    mapped = f" [weekend stamp {blue_date} -> {obs}]" if obs != blue_date else ""
    return {
        "raw_value": round(premium, 3),
        "source_note": (f"dolarapi blue {blue:.0f} / oficial {oficial:.0f} "
                        f"= {premium:+.1f}% premium{mapped}"),
        "obs_date": obs,
    }
