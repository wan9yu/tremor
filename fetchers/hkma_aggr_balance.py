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

ON FAILURE, THIS FETCHER RECORDS EVIDENCE, NOT JUST A VERDICT. The endpoint
alternates between reachable and unreachable phases lasting tens of minutes; in
a bad phase the TCP connect and TLS handshake both complete and then no response
body arrives at all. Six weeks of failures were recorded as a bare exception name
or a bare status code, which is why the first diagnosis of them could not say
which layer was at fault, nor even that the ten ReadTimeout days and the five
HTTP 502 days were one fault wearing two labels. Every failure path below now
carries elapsed time, and the HTTP path carries the gateway headers and a body
prefix. This costs no extra request. source_note is prose and no part of a
replayed verdict, so none of it can move a score.
"""
import time

import requests

LINE = "hkma_aggr_balance"
LABEL = "HK aggregate balance (HK$m)"
UNIT = "HK$m"
ANOMALY_DIRECTION = "down"
TIER = 2

_URL = ("https://api.hkma.gov.hk/public/market-data-and-statistics/"
        "daily-monetary-statistics/daily-figures-interbank-liquidity")
_HEADERS = {"User-Agent": "tremor/1.0 (+https://github.com/wan9yu/tremor)"}

# Split so a timeout names WHICH leg ran out. The measured bad-phase signature is
# a completed connect and handshake followed by silence, which raises ReadTimeout;
# a ConnectTimeout would mean something different and has never been observed.
# Connect has never been measured above 3.2s, so the 10s cap does not bind and the
# read budget is unchanged from the single 25s it replaces.
_TIMEOUT = (10, 25)

# The headers that name who answered. api.hkma.gov.hk sits behind an Alibaba Cloud
# edge fronting a Kong gateway, so a non-200 CARRYING these was minted at or behind
# Kong (the gateway reached the origin, or spoke for it), and one lacking them was
# minted by the edge before Kong was ever reached. Those are different faults with
# different owners, and the record has never once been able to tell them apart.
_DIAG_HEADERS = ("Via", "X-Kong-Upstream-Latency", "X-Kong-Proxy-Latency")


def _tidy(text, limit=200):
    """A response body flattened to one bounded line.

    A note is a CSV field that the project reads with grep and tail, so an
    embedded newline would break a record open even though csv would quote it,
    and an unbounded error page would bury the row that carries it.
    """
    return " ".join((text or "").split())[:limit]


def fetch_daily():
    started = time.monotonic()
    try:
        r = requests.get(_URL, params={"pagesize": 1, "sortorder": "desc"},
                         headers=_HEADERS, timeout=_TIMEOUT)
    except requests.RequestException as e:
        return {"raw_value": None,
                "source_note": (f"HKMA request failed: {type(e).__name__} after "
                                f"{time.monotonic() - started:.1f}s")}
    elapsed = time.monotonic() - started
    if r.status_code != 200:
        seen = [f"{h}={r.headers[h]}" for h in _DIAG_HEADERS if h in r.headers]
        origin = "; ".join(seen) if seen else "no gateway headers"
        return {"raw_value": None,
                "source_note": (f"HKMA HTTP {r.status_code} after {elapsed:.1f}s "
                                f"[{origin}] body: {_tidy(r.text)}")}
    try:
        records = (r.json().get("result") or {}).get("records") or []
    except ValueError:
        return {"raw_value": None,
                "source_note": ("HKMA returned a non-JSON body after "
                                f"{elapsed:.1f}s: {_tidy(r.text, 120)}")}
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
