"""IODA passive-BGP route withdrawal — the global communications slot's
route-WITHDRAWAL detector (tier 2, built R30).

Guarded equilibrium: states, ISPs and transit providers defend a country's
place in the global routing table — a network fights to keep its prefixes
ANNOUNCED, because an unannounced prefix is unreachable and unpaid-for. The
leaking hand: when a country's announced routes fall away, a larger force
withdrew them — a censorship shutdown that pulls the prefixes, a war or cable
cut that severs the backbone, a transit failure. Reading the depth of that
withdrawal, country by country, turns a national routing collapse into a global
signal.

Reading: the day's WORST-OF fractional route visibility across a size-floored
watch-list. For each watch-list country the day's MINIMUM visible-/24 count is
divided by that country's own 28-day rolling-median baseline (fractional
daily-min visibility: 1.0 = normal, → 0 = the country's routes withdrawn); the
worst (smallest) fraction across the list is the day's reading. A DROP is the
alarming move.

PASSIVE BGP, NOT ACTIVE PROBING — why this is not net_outages. IODA's `bgp`
datasource is a passive read of route ANNOUNCEMENTS observed by RIPE RIS +
RouteViews collectors: a withdrawal drops the visible-/24 count, a re-announce
restores it. It carries none of the synchronized active-probing common-mode
that demoted net_outages (that line counted `ping-slash24` active probes; seven
of its eight largest readings were probe-vantage artifacts, not world events).
There is no probe here to lose its vantage point, and worst-of keys on the
single deepest fraction — DEPTH, not COUNT — so a synchronized shallow flap
across many countries barely moves the minimum. This is the exact inversion of
the count form's breadth-spike failure mode.

THE LOAD-BEARING DISCLOSURE — route-WITHDRAWAL only, NOT reachability. BGP
measures route ANNOUNCEMENT, not whether traffic can flow. This line detects
withdrawal events — censorship shutdowns that pull prefixes (Syria's exam
shutdowns, Iraq's curfews), war that severs backbone routing (Sudan 2023-04),
major transit failures — but it SYSTEMATICALLY MISSES access-layer blackouts
where the routes stay announced while no traffic can pass. Gaza is the proof:
through the 2023-10 total blackout (power and fibre cut, the territory dark to
the world) Palestine's BGP visibility never fell below ~96% (a ~4% drop for a
100% human blackout, own z ≈ −0.4, never near the alarm) — the ASes kept
announcing routes into the dark. So this is honest coverage of the WITHDRAWAL
subclass only, the same effective-scope move as gnss_interference's disclosed
"effective reach 1"; it does not close the communications slot's full "is the
country reachable" question, and the severest siege / last-mile humanitarian
blackouts are exactly what it cannot see.

Aggregation (the R29 probe's locked design, evidence at
data/archive/bgp_probe_2026-09-08.csv):
  - WATCH-LIST: the countries whose median daily-median visible-/24 over a
    recent window is at least SIZE_FLOOR (512 /24s) — 153 of IODA's 253
    countries. The floor drops the chronically-tiny/noisy entities where a
    single-prefix flap is a large fraction. Re-derivable with the SAME rule the
    seeder's --derive-watchlist runs; baked here as WATCHLIST so the live path
    reads its 153 countries directly rather than re-snapshotting 253 daily.
  - per-country DAILY-MIN of the hourly visibility captures a sustained
    (hours→days) withdrawal at full depth while averaging away sub-hour flicker;
    the 300 s native step downsampled to hourly preserves the native daily-min
    exactly (probe-verified on Sudan 2023-04).
  - per-country BASELINE: the trailing BASELINE_DAYS (28-day) rolling MEDIAN of
    daily-median visibility, excluding the day itself, requiring at least
    BASELINE_MIN_VALID (14) valid days — each country's own recent normal.
  - fraction = daily-min ÷ baseline; the aggregate is the WORST-OF (minimum
    fraction) across the watch-list, alarming DOWN.

Scored in ANCHORED SCALE-MODE (ANCHOR=1.0 full visibility, MATERIALITY=0.10):
normal is a declared constant (full route visibility), not a rolling window, so
z = (raw − 1.0) / 0.10 and the alarm at 3·MATERIALITY lands at a 30% worst-of
withdrawal (fraction 0.70). The cited events clear it strongly — Syria
2022-05-30 fraction 0.031 → z −9.69, Sudan 2023-04-24 fraction 0.314 → z −6.86 —
while the structural benign floor (a few countries with large diurnal BGP swings
sit near fraction 0.75) reads a visible bump that does not fire, and Gaza's
~0.96 reads z ≈ −0.4. A rolling Qn was rejected by the probe: on very calm days
the worst-of near 1.0 against a tight early-window Qn threw degenerate large
POSITIVE z (a benign-direction artifact), the same corner stablecoin_peg and
fed_srf_takeup hit; the declared anchor removes it and still fires on every
cited event.

Settle: keyed to a COMPLETED UTC day (D-1). IODA's bgp lag is ~0.4 h, so the
most recent whole UTC day is fully present; reading a still-forming current day
would take the daily-min of a partial day. obs_date is that settled day, so a
re-run of the same day is a stale republish, not a second observation.

Source: IODA (Georgia Tech) per-country BGP signals API. Keyless.
"""
import statistics
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone

import requests

from core import useragent

LINE = "net_bgp_withdrawal"
LABEL = "Worst-of country BGP route visibility (fraction of normal)"
UNIT = "fraction"
ANOMALY_DIRECTION = "down"  # a DROP in announced routes is the withdrawal
TIER = 2  # built R30 as the communications-slot route-withdrawal candidate; it
# EARNS tier-1 later through the ≥60-scored promotion funnel, not by declaration.
# Anchored scale-mode (round 15 mechanism): normal is full route visibility, a
# declared constant, not a rolling window — see collect.py's fetcher contract and
# normalize.robust_z. z = (raw − 1.0) / 0.10; the alarm at 3·MATERIALITY is a 30%
# worst-of withdrawal (fraction 0.70), set below the structural benign floor
# (~0.75, from countries with large diurnal BGP swings) so ordinary days read a
# bump, not a tremble, and above Gaza's ~0.96 access-layer miss.
ANCHOR = 1.0        # full route visibility (daily-min == the country's own baseline)
MATERIALITY = 0.10  # fraction; alarm at 3×0.10 below the anchor → fraction 0.70.
# Fires: Syria 2022-05-30 frac 0.031 → z −9.69, Sudan 2023-04-24 frac 0.314 →
# z −6.86. Does not fire: the benign worst-of floor ~0.75 → z −2.5, Gaza's
# announced-through-blackout ~0.96 → z −0.4. Declared, so replay-validate before
# any tier-1 promotion.

# The size-floored watch-list: the 153 countries whose median daily-median
# visible-/24 over a recent window is >= SIZE_FLOOR. Re-derivable from IODA's
# entity list with tools/seed_bgp_withdrawal.py --derive-watchlist (which floors
# the same statistic); baked here so the live path reads these 153 directly.
SIZE_FLOOR = 512          # /24s: below this a single-prefix flap is a large fraction
BASELINE_DAYS = 28        # trailing window for each country's own normal
BASELINE_MIN_VALID = 14   # need at least this many valid days in the window
WATCHLIST = (
    "AE", "AF", "AL", "AM", "AO", "AR", "AT", "AU", "AZ", "BA", "BD", "BE",
    "BF", "BG", "BH", "BJ", "BN", "BO", "BR", "BS", "BW", "BY", "CA", "CG",
    "CH", "CI", "CL", "CM", "CN", "CO", "CR", "CU", "CW", "CY", "CZ", "DE",
    "DK", "DO", "DZ", "EC", "EE", "EG", "ES", "ET", "FI", "FJ", "FR", "GA",
    "GB", "GE", "GH", "GM", "GP", "GR", "GT", "GU", "HK", "HN", "HR", "HT",
    "HU", "ID", "IE", "IL", "IN", "IQ", "IR", "IS", "IT", "JM", "JO", "JP",
    "KE", "KG", "KH", "KR", "KW", "KZ", "LB", "LK", "LS", "LT", "LU", "LV",
    "LY", "MA", "MD", "ME", "MG", "MK", "MM", "MN", "MO", "MQ", "MT", "MU",
    "MW", "MX", "MY", "MZ", "NA", "NC", "NG", "NI", "NL", "NO", "NP", "NZ",
    "OM", "PA", "PE", "PH", "PK", "PL", "PR", "PS", "PT", "PY", "QA", "RE",
    "RO", "RS", "RU", "RW", "SA", "SC", "SD", "SE", "SG", "SI", "SK", "SN",
    "SV", "SY", "TG", "TH", "TN", "TR", "TT", "TW", "TZ", "UA", "UG", "US",
    "UY", "UZ", "VE", "VI", "VN", "YE", "ZA", "ZM", "ZW",
)

# Require this share of the watch-list to return a usable fraction before a
# worst-of is trusted. Worst-of is a MINIMUM, so a country that fails to fetch
# can only HIDE a deeper withdrawal, never fabricate one — a thin day would
# understate the reading. Below the floor the day is written EMPTY with the
# reason, never a fabricated calmer number (the net_outages honesty rule).
_COVERAGE_FLOOR = 0.90

_URL = "https://api.ioda.inetintel.cc.gatech.edu/v2/signals/raw/country/{cc}"
_HEADERS = useragent.HEADERS
_DATASOURCE = "bgp"


# --- pure aggregation (no network; unit-tested in tests/test_new_fetchers.py) ---

def daily_stats(points):
    """``{utc_date: (daily_min, daily_median)}`` from ``[(unix_ts, value)]``
    hourly points, grouped by UTC calendar day.

    The daily-MIN is the numerator of a country's fraction (a withdrawal's
    depth); the daily-MEDIAN feeds the rolling baseline (the country's normal).
    Points are the non-null hourly visibility values IODA returns for the
    country; a day with no points simply does not appear.
    """
    by_day = defaultdict(list)
    for ts, value in points:
        day = datetime.fromtimestamp(ts, timezone.utc).date().isoformat()
        by_day[day].append(float(value))
    return {day: (min(vs), statistics.median(vs)) for day, vs in by_day.items()}


def rolling_baseline(daily_medians, day, days=BASELINE_DAYS,
                     min_valid=BASELINE_MIN_VALID):
    """The median of ``daily_medians`` over the ``days`` calendar days strictly
    BEFORE ``day`` (a country's own recent normal), or None when fewer than
    ``min_valid`` of those days are present.

    ``daily_medians`` is ``{utc_date: daily_median}``; ``day`` is an ISO date
    string. Excludes ``day`` itself — a baseline must not be contaminated by the
    withdrawal it is used to judge.
    """
    d0 = date.fromisoformat(day)
    prior = [daily_medians[k] for k in
             ((d0 - timedelta(days=n)).isoformat() for n in range(1, days + 1))
             if k in daily_medians]
    return statistics.median(prior) if len(prior) >= min_valid else None


def country_fraction(day_min, baseline):
    """``day_min / baseline`` (1.0 = normal, → 0 = withdrawn), or None when the
    baseline is missing or non-positive or there is no reading for the day."""
    if day_min is None or baseline is None or baseline <= 0:
        return None
    return day_min / baseline


def worst_of(fractions):
    """``(worst_fraction, worst_country)`` — the MINIMUM fraction across the
    watch-list, ignoring countries with no fraction; ``(None, None)`` when none
    has one. The worst-of keys on the single deepest withdrawal, not a count."""
    valid = {cc: f for cc, f in fractions.items() if f is not None}
    if not valid:
        return None, None
    worst = min(valid, key=valid.get)
    return valid[worst], worst


def aggregate(day, country_points):
    """The day's ``(worst_fraction, worst_country, fractions)`` from raw points.

    ``country_points`` is ``{cc: [(unix_ts, value)]}`` — enough history per
    country to cover ``day`` and its trailing baseline window. The composition
    of the pure functions above: daily stats → per-country fraction → worst-of.
    ``fractions`` is ``{cc: fraction}`` for every country that produced one
    (the diagnostic breakdown).
    """
    fractions = {}
    for cc, points in country_points.items():
        stats = daily_stats(points)
        if day not in stats:
            continue
        medians = {d: med for d, (_mn, med) in stats.items()}
        frac = country_fraction(stats[day][0], rolling_baseline(medians, day))
        if frac is not None:
            fractions[cc] = frac
    worst, cc = worst_of(fractions)
    return worst, cc, fractions


# --- settle window + live fetch (network) ---------------------------------

def settled_day(now):
    """The most recent COMPLETE UTC calendar day before ``now`` (a datetime):
    D-1. BGP's ~0.4 h lag means that whole day is present; today is still
    forming and its daily-min would be a partial-day reading."""
    return (now.astimezone(timezone.utc).date() - timedelta(days=1)).isoformat()


def _window_bounds(day):
    """``(from, until)`` unix timestamps spanning ``day`` and its baseline
    window — from the start of ``day − BASELINE_DAYS`` to the end of ``day``."""
    d0 = date.fromisoformat(day)
    start = datetime.combine(d0 - timedelta(days=BASELINE_DAYS + 1),
                             datetime.min.time(), timezone.utc)
    end = datetime.combine(d0 + timedelta(days=1),
                           datetime.min.time(), timezone.utc)
    return int(start.timestamp()), int(end.timestamp())


def fetch_country_points(cc, frm, until, session=None):
    """Non-null hourly ``[(unix_ts, visible_/24)]`` for one country over
    ``[frm, until]``. maxPoints = hours in the window downsamples the 300 s
    native step to hourly, which preserves the native daily-min exactly. Raises
    on a transport/shape failure so the caller can retry or count a miss."""
    get = (session or requests).get
    hours = max(1, (until - frm) // 3600)
    r = get(_URL.format(cc=cc),
            params={"datasource": _DATASOURCE, "from": frm, "until": until,
                    "maxPoints": hours},
            headers=_HEADERS, timeout=45)
    if r.status_code != 200:
        raise ValueError(f"HTTP {r.status_code}")
    data = r.json().get("data")
    if not data:
        return []
    s = data[0]
    while isinstance(s, list):  # IODA nests the series one list deep
        s = s[0]
    start, step = s["from"], s["step"]
    return [(start + i * step, float(v))
            for i, v in enumerate(s.get("values") or []) if v is not None]


def fetch_daily():
    import concurrent.futures as cf

    now = datetime.now(timezone.utc)
    obs = settled_day(now)
    frm, until = _window_bounds(obs)

    points, failed = {}, []
    with requests.Session() as session:
        def one(cc):
            # A country that flakes is retried a few times; IODA's TLS resets
            # under a concurrent burst, so the retry is what makes coverage hold.
            last = None
            for _attempt in range(4):
                try:
                    return cc, fetch_country_points(cc, frm, until, session=session)
                except (requests.RequestException, ValueError, KeyError) as e:
                    last = type(e).__name__
            return cc, last  # a str marks a country that would not answer
        with cf.ThreadPoolExecutor(max_workers=6) as ex:
            for cc, res in ex.map(one, WATCHLIST):
                if isinstance(res, str):
                    failed.append(cc)
                else:
                    points[cc] = res

    covered = len(points) / len(WATCHLIST)
    if covered < _COVERAGE_FLOOR:
        return {"raw_value": None,
                "source_note": (f"no reading: only {len(points)}/{len(WATCHLIST)} "
                                f"watch-list countries answered IODA bgp "
                                f"({covered:.0%} < {_COVERAGE_FLOOR:.0%}); a thin "
                                f"day would understate the worst-of withdrawal")}

    worst, driver, fractions = aggregate(obs, points)
    if worst is None:
        return {"raw_value": None,
                "source_note": (f"no reading: no watch-list country had both a {obs} "
                                f"daily-min and a {BASELINE_DAYS}d baseline")}

    miss = f", {len(failed)} unreachable" if failed else ""
    return {
        "raw_value": round(worst, 4),
        "source_note": (f"IODA bgp worst-of route visibility {worst:.4f} of normal, "
                        f"driven by {driver} (daily-min ÷ {BASELINE_DAYS}d median), "
                        f"across {len(fractions)}/{len(WATCHLIST)} countries{miss} "
                        f"(settled UTC day {obs})"),
        "obs_date": obs,
        "components": fractions,
    }
