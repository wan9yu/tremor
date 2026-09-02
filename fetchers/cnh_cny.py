"""Offshore vs onshore yuan (CNH − CNY) — China capital-control tension line.

Guarded equilibrium: the PBOC manages the onshore yuan (CNY) inside a tight daily
band, burning FX reserves to defend it. The freely-traded offshore yuan (CNH) has
no such guard. The leaking hand: when CNH trades persistently weaker than CNY, the
market is pricing depreciation the onshore peg won't yet admit — capital-flight
pressure, tightening controls, a managed devaluation building.

Reading: the CNH − CNY spread in pips (1 pip = 0.0001 yuan per USD). A widening
POSITIVE spread (offshore yuan weaker) is the alarming direction.

Source: Yahoo Finance daily quotes for USDCNH=X (offshore) and USDCNY=X (onshore).
Free and keyless. Both legs must be present, or the day is written empty.

A SPREAD IS ONLY MEANINGFUL IF BOTH LEGS ARE QUOTED AT THE SAME MOMENT. The two
legs are two separate requests, and Yahoo's ``regularMarketTime`` for them can
diverge — measured at 6.5 hours apart on 2026-07-25, when the offshore leg still
carried Friday's 20:59 UTC close while the onshore leg had a 03:30 UTC Saturday
print. Subtracting prices captured hours apart injects whatever the yuan did in
between, and this spread is only ~100 pips wide, so the error is the size of the
signal. Two guards follow from that: the day is written EMPTY when the legs are
further apart than ``_MAX_LEG_GAP_S``, and ``obs_date`` is taken from the older
leg's SESSION rather than its raw timestamp. The onshore yuan has no weekend
session, so a Saturday or Sunday stamp names no session at all — Yahoo re-stamps
the frozen legs INTO the weekend, and a naive ``min(stamp)`` would mint a fresh
key every China-Monday instead of dedupping against the Friday close it is a
copy of. Snapping the weekend stamp back to its Friday is what makes the
standard dedup rule give the repeat no new z and no flag.
"""
import datetime

import requests

LINE = "cnh_cny"
LABEL = "Offshore−onshore yuan spread (pips)"
UNIT = "pips"
ANOMALY_DIRECTION = "up"  # offshore yuan weakening past onshore is the alarming move
TIER = 1  # primary indicator
# The onshore yuan (CNY) does not trade on weekends, so there is no simultaneous
# CNH/CNY quote to difference — a Sat/Sun empty is a market CLOSURE, not a fetch
# failure, and is scored ``closed`` rather than ``dark`` (round 18). Weekday
# holidays have no keyless calendar and stay ``dark``, as before.
WEEKEND_MARKET = True

_CHART = "https://query1.finance.yahoo.com/v8/finance/chart/{sym}"
_HEADERS = {"User-Agent": "Mozilla/5.0 (tremor; +https://github.com/wan9yu/tremor)"}
# Both symbols quote nearly around the clock on weekdays, so a simultaneous read
# should differ by minutes. Three hours is generous enough not to blank a normal
# weekday and tight enough to catch the multi-hour desync that motivated it.
_MAX_LEG_GAP_S = 3 * 3600


def _yahoo_quote(symbol):
    """``(price, quote_time_epoch)`` for a Yahoo symbol, or ``(None, None)``."""
    try:
        r = requests.get(
            _CHART.format(sym=symbol),
            headers=_HEADERS,
            timeout=12,
            params={"interval": "1d", "range": "5d"},
        )
    except requests.RequestException:
        return None, None
    if r.status_code != 200:
        return None, None
    try:
        meta = r.json()["chart"]["result"][0]["meta"]
        price = meta.get("regularMarketPrice")
        when = meta.get("regularMarketTime")
        return (float(price) if price is not None else None,
                int(when) if when is not None else None)
    except (ValueError, KeyError, IndexError, TypeError):
        return None, None


def _utc(epoch):
    return datetime.datetime.fromtimestamp(epoch, datetime.timezone.utc)


def _session_date(epoch):
    """The onshore trading session a quote stamp belongs to.

    The onshore yuan has no weekend session, so a Saturday or Sunday stamp names
    no session at all — it is a frozen Friday close that the vendor re-stamped
    forward. Mapping it back to its Friday is what makes the Monday collection
    dedup against Friday instead of minting a fresh observation key every week:
    the daily run fires at 22:30Z, which is 06:30 Beijing, hours before the
    onshore open, so a Monday row can only ever hold Friday's session.
    """
    d = _utc(epoch).date()
    if d.weekday() >= 5:                       # Sat -> -1, Sun -> -2
        return d - datetime.timedelta(days=d.weekday() - 4)
    return d


def _weekend_gap(older_t, newer_t):
    """True when the leg desync is just the FX weekend, not a malfunction.

    Every China-Sunday since the desync guard shipped has gone dark with the
    same signature: CNH frozen at its Friday close while Yahoo restamps the
    idle CNY leg through Saturday. Both fetches succeed; there is simply no
    moment on a weekend at which the two legs can be simultaneous. That is a
    market fact, not a failure, and the note must not describe it as one.
    """
    older, newer = _utc(older_t), _utc(newer_t)
    older_is_friday_close = (older.weekday() == 4 and older.hour >= 20) \
        or older.weekday() >= 5
    return older_is_friday_close and newer.weekday() >= 5


def fetch_daily():
    """Return {"raw_value": float | None, "source_note": str, "obs_date": str}."""
    cnh, cnh_t = _yahoo_quote("USDCNH=X")
    cny, cny_t = _yahoo_quote("USDCNY=X")
    missing = []
    if cnh is None or cnh <= 0:
        missing.append("USDCNH")
    if cny is None or cny <= 0:
        missing.append("USDCNY")
    if missing:
        return {
            "raw_value": None,
            "source_note": "yuan spread unavailable, missing: " + ", ".join(missing),
        }
    if cnh_t is None or cny_t is None:
        return {
            "raw_value": None,
            "source_note": ("yuan spread not comparable: Yahoo gave no quote time, "
                            "so the two legs cannot be shown to be simultaneous"),
        }

    gap = abs(cnh_t - cny_t)
    stamps = (f"CNH {_utc(cnh_t):%Y-%m-%d %H:%MZ}, CNY {_utc(cny_t):%Y-%m-%d %H:%MZ}")
    if gap > _MAX_LEG_GAP_S:
        if _weekend_gap(min(cnh_t, cny_t), max(cnh_t, cny_t)):
            return {
                "raw_value": None,
                "source_note": (f"no new observation: FX weekend, both legs frozen "
                                f"({stamps}) — no simultaneous quote exists until "
                                f"Monday trade; dark by market closure, not failure"),
            }
        return {
            "raw_value": None,
            "source_note": (f"yuan spread not comparable: legs quoted {gap / 3600:.1f}h "
                            f"apart ({stamps}) — a spread this narrow cannot survive "
                            f"subtracting prices captured hours apart"),
        }

    pips = (cnh - cny) * 10000.0
    # The observation belongs to the SESSION of the older leg: that is the
    # moment both prices describe. A weekend stamp is a re-stamped Friday close
    # and snaps back to Friday, so a Monday collection repeats Friday's
    # obs_date and dedups instead of scoring a session that never opened.
    obs = _session_date(min(cnh_t, cny_t)).isoformat()
    return {
        "raw_value": round(pips, 1),
        "source_note": (f"Yahoo USDCNH {cnh:.4f} − USDCNY {cny:.4f} (pips) "
                        f"[{stamps}, {gap / 60:.0f}min apart] [session {obs}]"),
        "obs_date": obs,
    }
