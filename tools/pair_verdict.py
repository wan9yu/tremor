"""Diagnostic verdict for one shared-date z pair. Not a scoring input.

Alarm days are ``collect.counts_as_tremble`` only. The sign of z is not an
alarm day, and a tremble in the other direction is not one either.
"""
import collect

DUST = 0.01
SPAN = 0.7
STRESS_MIN = 20


def pair_verdict(left_rows, left_mod, right_rows, right_mod):
    """Return whether this pair may be counted, and the only sentence it allows.

    The right-hand line is the counterpart. Its alarm days on the shared
    dates are the stress subset.
    """
    left, right, dates = _overlap(left_rows, right_rows)
    shared_left = [left[day] for day in dates]
    shared_right = [right[day] for day in dates]
    alarm_days_left = _alarm_days(shared_left, left_mod)
    alarm_days_right = _alarm_days(shared_right, right_mod)
    stress_n = alarm_days_right
    # Dust is a hard bar, not a number to retune after seeing a 0.025.
    if (_not_measured(shared_left, left_mod)
            or _not_measured(shared_right, right_mod)):
        return _report("non_measurement", False, alarm_days_left,
                        alarm_days_right, stress_n)
    # A high correlation is the drop suggestion even when the stress
    # window is too short to confirm orthogonality.
    coefficient = _pearson([_z(row) for row in shared_left],
                           [_z(row) for row in shared_right])
    if coefficient is not None and abs(coefficient) >= SPAN:
        return _report("redundant", True, alarm_days_left,
                        alarm_days_right, stress_n)
    if stress_n < STRESS_MIN or _stress_subset_unmeasured(
            shared_left, left_mod, shared_right, right_mod):
        return _report("unmeasured_under_stress", True, alarm_days_left,
                        alarm_days_right, stress_n)
    return _report("orthogonal_in_window", True, alarm_days_left,
                    alarm_days_right, stress_n)


def _report(verdict, countable, alarm_days_left, alarm_days_right, stress_n):
    return {
        "verdict": verdict,
        "countable": countable,
        "alarm_days_left": alarm_days_left,
        "alarm_days_right": alarm_days_right,
        "stress_n": stress_n,
    }


def _alarm_days(rows, mod):
    return sum(1 for row in rows if collect.counts_as_tremble(row, mod))


def _not_measured(rows, mod):
    """No alarm day on these rows, or every |z| is under the dust bar."""
    return _alarm_days(rows, mod) == 0 or _max_abs_z(rows) < DUST


def _stress_subset_unmeasured(left_rows, left_mod, right_rows, right_mod):
    """True when the counterpart's alarm days are not a measurement for both."""
    stress_left = []
    stress_right = []
    for left_row, right_row in zip(left_rows, right_rows, strict=True):
        if collect.counts_as_tremble(right_row, right_mod):
            stress_left.append(left_row)
            stress_right.append(right_row)
    # Every kept right-hand row is already an alarm day, so that side fails
    # this check only on dust. The left side fails when those dates are calm.
    return (_not_measured(stress_left, left_mod)
            or _not_measured(stress_right, right_mod))


def _max_abs_z(rows):
    values = [abs(z) for row in rows if (z := _z(row)) is not None]
    return max(values) if values else 0.0


def _z(row):
    raw = row.get("z_score")
    if raw is None or raw == "":
        return None
    try:
        return float(raw)
    except (TypeError, ValueError):
        return None


def _overlap(left_rows, right_rows):
    left = {row["date"]: row for row in left_rows if _z(row) is not None}
    right = {row["date"]: row for row in right_rows if _z(row) is not None}
    return left, right, sorted(set(left) & set(right))


def _pearson(xs, ys):
    pairs = [(x, y) for x, y in zip(xs, ys, strict=True)
             if x is not None and y is not None]
    n = len(pairs)
    if n < 2:
        return None
    mean_x = sum(x for x, _ in pairs) / n
    mean_y = sum(y for _, y in pairs) / n
    var_x = sum((x - mean_x) ** 2 for x, _ in pairs)
    var_y = sum((y - mean_y) ** 2 for _, y in pairs)
    if var_x <= 0 or var_y <= 0:
        return None
    cov = sum((x - mean_x) * (y - mean_y) for x, y in pairs)
    return cov / (var_x ** 0.5 * var_y ** 0.5)
