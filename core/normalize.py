"""Robust per-line normalization for tremor.

Each line is normalized ON ITS OWN with a rolling robust z-score (median + MAD,
which shrug off outliers far better than mean + standard deviation). Lines are
NEVER combined into a single doom score — the only composite tremor reports is a
COUNT of how many lines are trembling on a given day.
"""
import math
import statistics
from datetime import datetime

WINDOW = 90        # rolling baseline: the last 90 available readings
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
             window=WINDOW, min_points=MIN_POINTS):
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
