"""Shared-date z orthogonality is a diagnostic verdict, not a score.

The dry run of the 2026-09-25 plan showed that reading "alarm direction" as
the sign of z lets one pair be written "orthogonal in this window", while
``collect.counts_as_tremble`` on the same rows allows only "unmeasured under
stress" or "not a measurement". This file locks that predicate. It does not
read ``data/``.
"""
import importlib.util
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

# tools/ is a namespace package. A static ``from tools import pair_verdict``
# is not visible to the checker until the new file is indexed, so load the
# module from its path. The object under test is still the real function.
_spec = importlib.util.spec_from_file_location(
    "pair_verdict", os.path.join(ROOT, "tools", "pair_verdict.py"))
if _spec is None or _spec.loader is None:
    raise ImportError("tools/pair_verdict.py")
pair_verdict = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(pair_verdict)


class _Line:
    def __init__(self, direction):
        self.ANOMALY_DIRECTION = direction


def _row(date, z, trembling="0", direction="up"):
    return {"date": date, "z_score": f"{z:.3f}", "trembling": trembling,
            "direction": direction}


class TestPairVerdict(unittest.TestCase):
    def test_sign_of_z_is_not_an_alarm_day(self):
        # Twenty shared days, z positive on both sides, none trembling.
        # A sign-counter would call this a stress subset of 20 and a small
        # correlation, and the plan's orthogonal clause would fire. Alarm
        # days are zero, so the pair is not a measurement at all.
        left, right = [], []
        for i in range(20):
            day = f"2026-07-{i + 1:02d}"
            left.append(_row(day, 0.4))
            right.append(_row(day, 0.2))
        verdict = pair_verdict.pair_verdict(left, _Line("up"), right, _Line("up"))
        self.assertEqual(verdict["verdict"], "non_measurement")
        self.assertFalse(verdict["countable"])
        self.assertEqual(verdict["alarm_days_left"], 0)
        self.assertEqual(verdict["alarm_days_right"], 0)

    def test_two_alarm_days_are_not_a_stress_window(self):
        # Both sides tremble in the alarm direction on two shared days.
        # Two varying points are always |r|=1, so the left side is flat:
        # correlation is undefined, and a 2-day stress subset is under the
        # floor of 20. The only allowed sentence is unmeasured under stress.
        left = [_row("2026-07-02", 1.0, "1", "up"),
                _row("2026-07-04", 1.0, "1", "up")]
        right = [_row("2026-07-02", 1.5, "1", "down"),
                 _row("2026-07-04", 2.5, "1", "down")]
        verdict = pair_verdict.pair_verdict(left, _Line("up"), right, _Line("down"))
        self.assertEqual(verdict["verdict"], "unmeasured_under_stress")
        self.assertTrue(verdict["countable"])
        self.assertEqual(verdict["stress_n"], 2)

    def test_dust_below_one_hundredth_is_not_a_measurement(self):
        # Alarm days exist, but the larger |z| on the overlap is 0.009.
        # The plan's dust bar is strict: max |z| < 0.01 is not a measurement,
        # and seeing a 0.025 later must not move that bar.
        left = [_row("2026-07-02", 0.009, "1", "up")]
        right = [_row("2026-07-02", 0.005, "1", "down")]
        verdict = pair_verdict.pair_verdict(left, _Line("up"), right, _Line("down"))
        self.assertEqual(verdict["verdict"], "non_measurement")
        self.assertFalse(verdict["countable"])

    def test_high_correlation_is_redundant_even_when_stress_is_short(self):
        # Two shared alarm days, identical z. |r| is 1, above 0.7, and the
        # stress subset has only 2 days. The drop suggestion does not wait
        # for a stress window. A short window must not hide the correlation.
        left = [_row("2026-07-02", 1.0, "1", "up"),
                _row("2026-07-04", 2.0, "1", "up")]
        right = [_row("2026-07-02", 1.0, "1", "down"),
                 _row("2026-07-04", 2.0, "1", "down")]
        verdict = pair_verdict.pair_verdict(left, _Line("up"), right, _Line("down"))
        self.assertEqual(verdict["verdict"], "redundant")
        self.assertTrue(verdict["countable"])
        self.assertEqual(verdict["stress_n"], 2)

    def test_long_stress_window_with_low_correlation_is_orthogonal(self):
        # Twenty shared alarm days. Left rises, right alternates, so |r|
        # stays under 0.7. The stress subset is the right-hand alarm days,
        # and both sides still have an alarm day inside it.
        left, right = [], []
        for i in range(20):
            day = f"2026-08-{i + 1:02d}"
            left.append(_row(day, float(i + 1), "1", "up"))
            right.append(_row(day, 1.0 if i % 2 == 0 else 3.0, "1", "down"))
        verdict = pair_verdict.pair_verdict(left, _Line("up"), right, _Line("down"))
        self.assertEqual(verdict["verdict"], "orthogonal_in_window")
        self.assertTrue(verdict["countable"])
        self.assertEqual(verdict["stress_n"], 20)

    def test_long_stress_window_without_candidate_alarm_days_is_unmeasured(self):
        # The counterpart has 20 alarm days. The candidate's only alarm day
        # is outside that subset, so the stress window is calm-on-stress.
        # A long subset is not enough; the candidate must also have an
        # alarm day inside it.
        left = [_row("2026-08-01", 2.0, "1", "up")]
        right = [_row("2026-08-01", 1.0, "0", "down")]
        for i in range(20):
            day = f"2026-08-{i + 2:02d}"
            left.append(_row(day, 1.0, "0", "up"))
            right.append(_row(day, 1.0 if i % 2 == 0 else 3.0, "1", "down"))
        verdict = pair_verdict.pair_verdict(left, _Line("up"), right, _Line("down"))
        self.assertEqual(verdict["verdict"], "unmeasured_under_stress")
        self.assertTrue(verdict["countable"])
        self.assertEqual(verdict["stress_n"], 20)

    def test_alarm_day_outside_the_overlap_does_not_count(self):
        # The candidate trembles only on a date the counterpart does not
        # share. Shared dates are calm. That outside day must not create an
        # alarm-day count.
        left = [_row("2026-07-02", 1.0, "0", "up"),
                _row("2026-07-03", 4.0, "1", "up")]
        right = [_row("2026-07-02", 1.0, "0", "down")]
        verdict = pair_verdict.pair_verdict(left, _Line("up"), right, _Line("down"))
        self.assertEqual(verdict["alarm_days_left"], 0)
        self.assertEqual(verdict["verdict"], "non_measurement")

    def test_exactly_one_hundredth_is_not_dust(self):
        # The bar is strict less-than. 0.010 is a measurement. A later 0.025
        # must not be used to widen it.
        left = [_row("2026-07-02", 0.010, "1", "up"),
                _row("2026-07-04", 0.010, "1", "up")]
        right = [_row("2026-07-02", 0.010, "1", "down"),
                 _row("2026-07-04", 0.020, "1", "down")]
        verdict = pair_verdict.pair_verdict(left, _Line("up"), right, _Line("down"))
        self.assertNotEqual(verdict["verdict"], "non_measurement")
        self.assertTrue(verdict["countable"])

    def test_scoring_path_does_not_import_the_verdict(self):
        for rel in ("collect.py", os.path.join("core", "normalize.py")):
            with open(os.path.join(ROOT, rel)) as handle:
                source = handle.read()
            self.assertNotIn("pair_verdict", source, rel)
