"""Robust per-line normalization for tremor.

Each line is normalized ON ITS OWN with a rolling robust z-score (median + MAD,
which shrug off outliers far better than mean + standard deviation). Lines are
NEVER combined into a single doom score — the only composite tremor reports is a
COUNT of how many lines are trembling on a given day.
"""
import math
import statistics
from datetime import datetime, timedelta

WINDOW = 90        # rolling baseline: the last 90 available readings
MAX_AGE_DAYS = 180  # calendar cap: slow sources must not build baselines across seasons
THRESHOLD = 3.0    # |z| above this counts as "trembling"
MIN_POINTS = 10    # need at least this much clean history to judge honestly
_MAD_TO_SD = 1.4826  # scales MAD to a standard-deviation equivalent


def _scale_z(values, today):
    """z of ``today`` against a clean value list, or None if there's no spread.

    Primary scale is MAD (robust). When MAD collapses to zero — once more than
    half the window shares one value — fall back to a median-centered RMS so the
    centre and scale share a reference and a move off a near-flat baseline is
    still seen. No spread at all yields None: nothing to measure against.
    """
    median = statistics.median(values)
    mad = statistics.median([abs(v - median) for v in values])
    if mad > 0:
        return (today - median) / (_MAD_TO_SD * mad)
    rms = math.sqrt(sum((v - median) ** 2 for v in values) / len(values))
    if rms > 0:
        return (today - median) / rms
    return None


def _weekday(date_str):
    return datetime.strptime(date_str, "%Y-%m-%d").weekday()


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
    # Calendar cap: for slow/deduped sources, "the last 90 observations" could
    # otherwise span seasons or regimes; drop anything older than max_age_days.
    if dates is not None and today_date is not None and max_age_days:
        try:
            cutoff = (datetime.strptime(today_date, "%Y-%m-%d")
                      - timedelta(days=max_age_days)).strftime("%Y-%m-%d")
            pairs = [(v, d) for v, d in zip(history, dates) if not d or d >= cutoff]
            history = [v for v, _ in pairs]
            dates = [d for _, d in pairs]
        except (ValueError, TypeError):
            pass
    if weekday_cycle and dates is not None and today_date is not None:
        try:
            target = _weekday(today_date)
            same = [v for v, d in zip(history, dates)
                    if v is not None and d and _weekday(d) == target]
        except (ValueError, TypeError):
            same = []
        same = same[-window:]
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
    try:
        target = _weekday(today_date)
        same = [v for v, d in zip(history, dates)
                if v is not None and d and _weekday(d) == target]
    except (ValueError, TypeError):
        return False, ""
    n = len(same)
    if not (min_samples <= n < max_samples):
        return False, ""
    lo, hi = min(same), max(same)
    pad = (hi - lo) * margin
    if lo - pad <= today <= hi + pad:
        return True, (f"suppressed: within same-weekday range "
                      f"[{lo:g}, {hi:g}] (n={n})")
    return False, ""
