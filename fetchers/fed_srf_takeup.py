"""Fed SRF take-up — borrowing from the plumbing's own ceiling (tier 2).

Guarded equilibrium: the Fed's Standing Repo Facility (SRF) is a full-allotment
backstop offered every business day (a morning and an afternoon operation) that
caps the overnight repo rate — the Fed stands ready to lend cash against
Treasuries / Agencies / MBS at a fixed ceiling. When the system is flush with
reserves nobody needs it and take-up sits at exactly $0; when reserves or
collateral turn scarce, dealers borrow from the facility itself, so a rising
take-up is the guard's own hand leaking. The SRF (standing since 2021-07-28) is
the institutionalized answer to the September-2019 repo spike.

Reading: the day's TOTAL amount accepted across all SRF repo operations, in $m.
UP is the alarming move. 60.8% of the 2021-07-28-> record is exactly $0; the
facility only prints under pressure, and the largest days are genuine
reserve-scarcity events — year-end 2025 ($74.6bn, the record), the Oct-2025
month-end ($50.4bn), and a mid-month 2026-02-17 spike ($30.5bn) that no calendar
explains.

Scored in ANCHORED SCALE-MODE (ANCHOR=0, MATERIALITY=$10,000m): normal is the
defended $0, not a rolling window, so a $0 day reads an honest z=0. A rolling Qn
would be zero across the 61% of identical-$0 windows and go blind — or, with a
small floor, cry wolf on ordinary month-end dust. Alarm at 3*10,000 = $30bn, set
deliberately ABOVE the routine post-2025 month/quarter-end friction band
(~$20-26bn -> z 2.0-2.6, a visible bump that does NOT fire), so only genuine
scarcity trembles: replayed over the whole record it fires on exactly the three
>$30bn days and nothing else. The month-end clustering below the alarm is a
calendar structure this line does not yet de-cycle — acceptable for a tier-2 line
banking history, to be handled before any tier-1 promotion.

Source: NY Fed markets API repo operation results (keyless). The live line reads
the most recent operations; the seeder pulls the full range off the same shape, so
history and the live tail are one measure. A lagged/settled read: obs_date is the
latest COMPLETE operation day (< today), so a re-read of the same day — including
weekend / holiday runs when the facility does not operate — is a stale republish,
not a second observation.
"""
import datetime

import requests

LINE = "fed_srf_takeup"
LABEL = "Fed SRF take-up — daily Standing Repo Facility borrowing ($m)"
UNIT = "$m"
ANOMALY_DIRECTION = "up"
TIER = 2
# Anchored scale-mode (round 15 mechanism): normal is the defended $0 facility,
# not a rolling window — see the fetcher contract in collect.py and
# normalize.robust_z. MATERIALITY is set above the post-2025 month/quarter-end
# friction band so routine calendar pressure reads as a bump, not a tremble.
ANCHOR = 0            # a facility nobody draws on, in $m
MATERIALITY = 10000   # $m; alarm at 3*10,000 = $30bn. Dust (<$100m PM ops) -> z<0.01;
                      # elevated month-end ($20-26bn) -> z 2.0-2.6 (visible, no fire);
                      # the three genuine spikes fire: 2025-12-31 $74.6bn -> z=7.5,
                      # 2025-10-31 $50.4bn -> z=5.0, 2026-02-17 $30.5bn -> z=3.05.
                      # The bar is set on the FRICTION BAND (comfortably above the
                      # $26bn month-end cluster), not fitted to a target count; the
                      # count of three is a descriptive replay output, and the
                      # lowest of them (02-17) clears the bar by only ~$0.5bn — if a
                      # re-pull ever revised it under $30bn it would simply read as a
                      # bump, which is honest, not a regression. Declared, so
                      # replay-validate before any promotion; a de-cycling pass (this
                      # repo has none) is the promotion gate.

_SEARCH = "https://markets.newyorkfed.org/api/rp/results/search.json"
_LAST = "https://markets.newyorkfed.org/api/rp/all/all/results/last/{n}.json"
_HEADERS = {"User-Agent": "tremor/1.0 (+https://github.com/wan9yu/tremor)"}


def _get(url, params=None):
    r = requests.get(url, params=params, headers=_HEADERS, timeout=30)
    if r.status_code != 200:
        raise ValueError(f"HTTP {r.status_code}")
    ops = r.json().get("repo", {}).get("operations")
    if not isinstance(ops, list):
        # a 200 with a changed / empty shape is a source problem, not a $0 day —
        # raise so the caller degrades to a stated-empty, never a fabricated read
        raise ValueError("unexpected response shape")
    return ops


def _recent(n):
    """The most recent ``n`` repo/reverse-repo operations (live path)."""
    return _get(_LAST.format(n=n))


def search(start, end):
    """Every SRF repo operation between two dates, inclusive (seeder path)."""
    return _get(_SEARCH, {"startDate": start, "endDate": end, "operationTypes": "Repo"})


def _repo_ops(operations):
    """Only the Standing Repo Facility legs — every ``Repo`` op, both auction
    formats (Full Allotment, Multiple Price) and both overnight and the rare term
    ops; reverse-repo (RRP) is a different facility and is dropped."""
    return [o for o in operations if o.get("operationType") == "Repo"]


def daily_takeup(operations):
    """Sum accepted across each day's SRF repo ops: ``{operationDate: $m}``.

    Shared by the live fetcher and the seeder so both measure take-up the same
    way. The morning and afternoon operations (and any term op) on a day are
    summed; amounts arrive in dollars and are returned in $m.
    """
    by_day = {}
    for o in _repo_ops(operations):
        day = o.get("operationDate")
        if not day:
            continue
        by_day[day] = by_day.get(day, 0.0) + float(o.get("totalAmtAccepted") or 0)
    return {day: amt / 1e6 for day, amt in by_day.items()}


def fetch_daily():
    # The settle boundary is an explicit UTC date, NOT naive date.today(): it must
    # not depend on the runner's timezone. A US-Eastern operation day is fully
    # settled (both the ~08:30 and ~13:45 ET ops closed) well before UTC rolls past
    # it, so "< today (UTC)" never selects a day whose afternoon op has not yet
    # settled — the partial-day trap a local clock ahead of ET would fall into.
    today = datetime.datetime.now(datetime.timezone.utc).date().isoformat()
    try:
        ops = _recent(40)   # ~2 ops/business day -> a comfortable settled window
        takeup = daily_takeup(ops)
    except (requests.RequestException, ValueError, KeyError, TypeError) as e:
        return {"raw_value": None,
                "source_note": f"NY Fed markets API unavailable: {type(e).__name__}"}

    settled = [d for d in takeup if d < today]
    if not settled:
        return {"raw_value": None,
                "source_note": f"NY Fed SRF: no settled operation day before {today}"}
    obs = max(settled)
    val = round(takeup[obs], 1)
    n_ops = sum(1 for o in _repo_ops(ops) if o.get("operationDate") == obs)
    return {
        "raw_value": val,
        "source_note": (f"NY Fed SRF total accepted {val:,.1f}$m across "
                        f"{n_ops} repo op(s) on {obs}"),
        "obs_date": obs,
    }
