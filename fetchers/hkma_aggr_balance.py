"""Hong Kong aggregate balance — currency-board stress watchlist (tier 2).

Guarded equilibrium: the HKMA runs a currency board that defends the HKD peg
inside 7.75-7.85 per USD. When the HKD hits the weak side, the HKMA buys HKD
(sells USD) to defend it, and doing so DRAINS the banking system's aggregate
balance — the pool of settlement money. The leaking hand: a collapse in the
aggregate balance is the peg being defended under capital-outflow pressure; a
sustained drain toward near-zero is the board spending its room to hold the line.

Reading: the closing aggregate balance in HK$ millions. A fall is the alarming
move (the guard is being forced to spend). Note the balance also moves on benign
monetary operations, which is why this is a watchlist line, not counted.

Source: HKMA Open API, daily interbank-liquidity figures (keyless JSON).
"""
import requests

LINE = "hkma_aggr_balance"
LABEL = "HK aggregate balance (HK$m)"
UNIT = "HK$m"
ANOMALY_DIRECTION = "down"
TIER = 2

_URL = ("https://api.hkma.gov.hk/public/market-data-and-statistics/"
        "daily-monetary-statistics/daily-figures-interbank-liquidity")
_HEADERS = {"User-Agent": "tremor/1.0 (+https://github.com/wan9yu/tremor)"}


def fetch_daily():
    try:
        r = requests.get(_URL, params={"pagesize": 1, "sortorder": "desc"},
                         headers=_HEADERS, timeout=25)
    except requests.RequestException as e:
        return {"raw_value": None, "source_note": f"HKMA request failed: {type(e).__name__}"}
    if r.status_code != 200:
        return {"raw_value": None, "source_note": f"HKMA HTTP {r.status_code}"}
    try:
        records = (r.json().get("result") or {}).get("records") or []
    except ValueError:
        return {"raw_value": None, "source_note": "HKMA returned a non-JSON body"}
    if not records:
        return {"raw_value": None, "source_note": "HKMA returned no records"}
    rec = records[0]
    try:
        bal = float(rec.get("closing_balance"))  # float(None) raises TypeError
    except (ValueError, TypeError):
        return {"raw_value": None,
                "source_note": "HKMA closing_balance missing or unparseable"}
    return {
        "raw_value": bal,
        "source_note": f"HKMA aggregate balance {bal:.0f} HK$m ({rec.get('end_of_date')})",
        "obs_date": rec.get("end_of_date") or "",
    }
