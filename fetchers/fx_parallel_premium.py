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
"""
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


def fetch_daily():
    try:
        blue, blue_date = _leg(_BLUE)
        oficial, _ = _leg(_OFICIAL)
    except (requests.RequestException, ValueError, KeyError, TypeError) as e:
        return {"raw_value": None, "source_note": f"dolarapi unavailable: {type(e).__name__}"}
    if oficial <= 0:
        return {"raw_value": None, "source_note": "dolarapi official rate not positive"}
    premium = (blue / oficial - 1.0) * 100.0
    return {
        "raw_value": round(premium, 3),
        "source_note": f"dolarapi blue {blue:.0f} / oficial {oficial:.0f} = {premium:+.1f}% premium",
        "obs_date": blue_date,
    }
