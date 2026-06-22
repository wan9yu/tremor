"""Robust per-line normalization for tremor.

Each line is normalized ON ITS OWN with a rolling robust z-score (median + MAD,
which shrug off outliers far better than mean + standard deviation). Lines are
NEVER combined into a single doom score — the only composite tremor reports is a
COUNT of how many lines are trembling on a given day.
"""
import math
import statistics

WINDOW = 90        # rolling baseline: the last 90 available readings
THRESHOLD = 3.0    # |z| above this counts as "trembling"
MIN_POINTS = 10    # need at least this much clean history to judge honestly
_MAD_TO_SD = 1.4826  # scales MAD to a standard-deviation equivalent


def robust_z(history, today, window=WINDOW, min_points=MIN_POINTS):
    """Robust z-score of ``today`` against the trailing ``window`` of history.

    ``history`` is the list of prior raw values (oldest..newest) and may contain
    None for gaps; gaps are dropped, so the window is the last ``window``
    *available* readings (which can span more than ``window`` calendar days when
    a source has been down). Returns a float, or None when there is not enough
    clean history — or no spread at all — to judge honestly. Returning None
    there is deliberate: tremor would rather say "I can't tell yet" than fake a
    number.

    The primary scale is MAD (robust). When MAD collapses to zero — which
    happens once more than half the window shares one value — we fall back to a
    median-centered RMS so the centre and the scale share the same reference and
    a move off a near-flat baseline is still seen. A window with no spread at
    all yields None: with nothing to measure against, there is no honest
    magnitude to report.
    """
    if today is None:
        return None
    values = [v for v in history if v is not None][-window:]
    if len(values) < min_points:
        return None
    median = statistics.median(values)
    mad = statistics.median([abs(v - median) for v in values])
    if mad > 0:
        return (today - median) / (_MAD_TO_SD * mad)
    rms = math.sqrt(sum((v - median) ** 2 for v in values) / len(values))
    if rms > 0:
        return (today - median) / rms
    return None


def classify(z, threshold=THRESHOLD):
    """Map a z-score (or None) to ``(trembling: int, direction: str)``."""
    if z is None:
        return 0, ""
    direction = "up" if z > 0 else ("down" if z < 0 else "flat")
    trembling = 1 if abs(z) > threshold else 0
    return trembling, direction
