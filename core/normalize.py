"""Robust per-line normalization for tremor.

Each line is normalized ON ITS OWN with a rolling robust z-score (median for the
centre, Rousseeuw-Croux Qn for the scale — both shrug off outliers far better
than mean + standard deviation). Lines are NEVER combined into a single doom
score — the only composite tremor reports is a COUNT of how many lines are
trembling on a given day.
"""
import statistics
from datetime import datetime, timedelta
from itertools import combinations

WINDOW = 90        # rolling baseline: the last 90 available readings
MAX_AGE_DAYS = 180  # calendar cap: slow sources must not build baselines across seasons
THRESHOLD = 3.0    # |z| above this counts as "trembling"
MIN_POINTS = 10    # need at least this much clean history to judge honestly

_QN_C = 2.2219  # scales the Qn order statistic to a Gaussian standard deviation
# Rousseeuw-Croux finite-sample corrections; past n=9 the closed form takes over.
_QN_D = {2: 0.399, 3: 0.994, 4: 0.512, 5: 0.844,
         6: 0.611, 7: 0.857, 8: 0.669, 9: 0.872}


def _qn_factor(n):
    if n in _QN_D:
        return _QN_D[n]
    return n / (n + 1.4) if n % 2 else n / (n + 3.8)


def _qn(values):
    """Rousseeuw-Croux Qn: the k-th smallest pairwise absolute difference.

    Same 50% breakdown point as MAD, and it collapses to zero on the same
    windows (once n//2+1 readings are tied). What it buys is calibration on
    SHORT windows, which is what tremor actually runs on: MAD is biased narrow
    there — about 0.91 sigma at n=10, measured — and a narrow denominator
    inflates every z. Qn measures ~1.00 sigma at every n and carries roughly
    half MAD's sampling variance, so a |z|>3 rule means much closer to what it
    claims. Measured null exceedance of |z|>3 on iid Gaussian data:
    n=10 5.3% -> 2.7%, n=20 2.1% -> 1.2%, n=90 0.56% -> 0.36%. Still not the
    0.3% of a true 3-sigma rule at short n — no scale estimator can deliver
    that from ten points — but roughly half the false alarms for the same
    threshold, and better power at the same false-alarm rate.
    """
    n = len(values)
    if n < 2:
        return 0.0
    pairs = sorted(abs(a - b) for a, b in combinations(values, 2))
    h = n // 2 + 1
    return _QN_C * _qn_factor(n) * pairs[h * (h - 1) // 2 - 1]


def _scale_z(values, today):
    """z of ``today`` against a clean value list, or None if there's no spread.

    A window with no resolvable dispersion yields None: there is genuinely
    nothing to measure against, and saying so is the honest answer. This used to
    fall through to a median-centered RMS, which has a breakdown point of zero —
    on a near-flat integer window a single-unit move scored above 3 and raised a
    tremble out of one quantum of resolution.
    """
    scale = _qn(values)
    if scale <= 0:
        return None
    return (today - statistics.median(values)) / scale


def _weekday(date_str):
    return datetime.strptime(date_str, "%Y-%m-%d").weekday()


def _age_capped(history, dates, today_date, max_age_days):
    """Drop (value, date) pairs older than ``max_age_days`` before ``today_date``.

    For slow/deduplicated sources, "the last 90 observations" could otherwise
    span seasons or regimes. Shared by the z baseline and the weekday veto so
    both always judge against the same sample set.
    """
    if not (dates is not None and today_date and max_age_days):
        return history, dates
    try:
        cutoff = (datetime.strptime(today_date, "%Y-%m-%d")
                  - timedelta(days=max_age_days)).strftime("%Y-%m-%d")
    except (ValueError, TypeError):
        return history, dates
    pairs = [(v, d) for v, d in zip(history, dates) if not d or d >= cutoff]
    return [v for v, _ in pairs], [d for _, d in pairs]


def _same_weekday(history, dates, today_date):
    """Values from ``history`` whose date falls on ``today_date``'s weekday."""
    try:
        target = _weekday(today_date)
        return [v for v, d in zip(history, dates)
                if v is not None and d and _weekday(d) == target]
    except (ValueError, TypeError):
        return []


def robust_z(history, today, dates=None, today_date=None, weekday_cycle=False,
             window=WINDOW, min_points=MIN_POINTS, max_age_days=MAX_AGE_DAYS):
    """Robust z-score of ``today`` against the trailing ``window`` of history.

    ``history`` is the list of prior raw values (oldest..newest) and may contain
    None for gaps; gaps are dropped, so the window is the last ``window``
    *available* readings (which can span more than ``window`` calendar days when
    a source has been down). Returns a float, or None when there is not enough
    clean history — or no spread at all — to judge honestly. Returning None
    there is deliberate: tremor would rather say "I can't tell yet" than fake a
    number.

    De-cycling: sampling at a fixed time of day already removes the diurnal
    cycle. For a line with a strong WEEKLY rhythm (e.g. flights, which dip every
    weekend), pass ``weekday_cycle=True`` with aligned ``dates`` and
    ``today_date`` so the baseline is built only from the SAME weekday — its
    normal weekend dip then is not mistaken for a deviation. This falls back to
    the full window until enough same-weekday history exists. (The slow seasonal
    cycle is absorbed by the trailing window; true year-over-year
    de-seasonalization waits on a full year of history.)
    """
    if today is None:
        return None
    history, dates = _age_capped(history, dates, today_date, max_age_days)
    if weekday_cycle and dates is not None and today_date is not None:
        same = _same_weekday(history, dates, today_date)[-window:]
        if len(same) >= min_points:
            return _scale_z(same, today)
    values = [v for v in history if v is not None][-window:]
    if len(values) < min_points:
        return None
    return _scale_z(values, today)


def classify(z, threshold=THRESHOLD):
    """Map a z-score (or None) to ``(trembling: int, direction: str)``."""
    if z is None:
        return 0, ""
    direction = "up" if z > 0 else ("down" if z < 0 else "flat")
    trembling = 1 if abs(z) > threshold else 0
    return trembling, direction


def weekday_range_veto(history, dates, today, today_date,
                       min_samples=3, max_samples=MIN_POINTS, margin=0.05):
    """Warm-up veto for weekly-cycle lines, nonparametric by design.

    Until a line has ``max_samples`` same-weekday readings (when the proper
    weekday baseline engages in ``robust_z``), a full-window tremble can be a
    routine weekend dip read against a weekday-heavy window. With as few as
    ``min_samples`` same-weekday readings we can still ask a scale-free
    question: has this LEVEL been seen on this weekday before? If today lies
    inside the same-weekday [min, max] envelope (widened by ``margin`` of the
    span), the tremble is suppressed. No dispersion estimate is used — a
    genuine crisis value falls outside every previously seen same-weekday
    value and can never be vetoed.

    Returns ``(vetoed: bool, detail: str)``; detail is auditable and should be
    recorded wherever the suppression is applied.
    """
    if today is None or not dates or today_date is None:
        return False, ""
    # Same age cap as robust_z, so the veto judges against the same sample set
    # the z-score was computed from.
    history, dates = _age_capped(history, dates, today_date, MAX_AGE_DAYS)
    same = _same_weekday(history, dates, today_date)
    n = len(same)
    if not (min_samples <= n < max_samples):
        return False, ""
    lo, hi = min(same), max(same)
    pad = (hi - lo) * margin
    if lo - pad <= today <= hi + pad:
        return True, (f"suppressed: within same-weekday range "
                      f"[{lo:g}, {hi:g}] (n={n})")
    return False, ""


def judge(history, dates, obs_dates, today, today_obs, today_date,
          weekly_cycle=False):
    """The full verdict for today's reading: ``(z, trembling, direction, note)``.

    Owns the whole scoring sequence in one place — observation dedup (lagged
    sources republish a reading until they update; only the first occurrence
    counts), the stale check (a republished observation scores no new z and
    raises no flag), the calendar cap, the weekday baseline, classification,
    and the weekly-cycle warm-up veto. ``note`` carries any verdict detail
    (stale marker, veto reason) for the row's source_note.

    ``history``/``dates``/``obs_dates`` are aligned per prior row; ``today_obs``
    is today's observation date ("" for real-time lines).
    """
    values, kept_dates = [], []
    seen_obs = set()
    for v, d, o in zip(history, dates, obs_dates):
        if o:
            if o in seen_obs:
                continue
            seen_obs.add(o)
        values.append(v)
        kept_dates.append(d)
    if today_obs and today_obs in seen_obs:
        return None, 0, "", "[stale: observation already recorded]"
    z = robust_z(values, today, dates=kept_dates, today_date=today_date,
                 weekday_cycle=weekly_cycle)
    trembling, direction = classify(z)
    if trembling and weekly_cycle:
        vetoed, detail = weekday_range_veto(values, kept_dates, today, today_date)
        if vetoed:
            return z, 0, direction, f"[{detail}]"
    return z, trembling, direction, ""
