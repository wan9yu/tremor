"""Semantics tests for the scoring core.

These lock the rules tremor must never quietly lose: no fabricated magnitudes,
no baseline built from republished observations, no verdict on thin history.
Run with ``python -m unittest discover tests``.
"""
import os
import statistics
import sys
import unittest
from random import Random

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core import normalize as N


class TestScale(unittest.TestCase):
    def test_qn_reference_value(self):
        # Qn of 1..10: the pairwise gaps are nine 1s then eight 2s, so the
        # k-th (k=15) is 2, scaled by 2.2219 * d_10.
        self.assertAlmostEqual(N._qn([float(i) for i in range(1, 11)]), 3.2201, places=3)

    def test_qn_is_unbiased_for_sigma(self):
        """MAD runs narrow on short windows; Qn does not. This is the whole point."""
        rng = Random(20260722)
        for n in (10, 20, 90):
            draws = [[rng.gauss(0, 1) for _ in range(n)] for _ in range(400)]
            qn = statistics.mean(N._qn(d) for d in draws)
            mad = statistics.mean(
                1.4826 * statistics.median([abs(v - statistics.median(d)) for v in d])
                for d in draws
            )
            self.assertLess(abs(qn - 1.0), 0.05, f"Qn biased at n={n}: {qn}")
            self.assertLess(mad, qn, f"MAD should run narrower than Qn at n={n}")

    def test_qn_collapses_where_mad_does(self):
        """No overclaiming: Qn's breakdown is MAD's, at n//2+1 tied readings.

        The gain over MAD is calibration on short windows, not robustness to
        ties. Locked here so the docstring can never drift into claiming more.
        """
        tied = [3.0] * 6 + [10.0, 11.0, 12.0, 13.0]
        median = statistics.median(tied)
        self.assertEqual(statistics.median([abs(v - median) for v in tied]), 0.0)
        self.assertEqual(N._qn(tied), 0.0)
        # One fewer tie and both still resolve.
        resolves = [3.0] * 5 + [10.0, 11.0, 12.0, 13.0, 14.0]
        self.assertGreater(N._qn(resolves), 0.0)

    def test_no_spread_yields_none_not_a_number(self):
        """A window with no dispersion must not produce a magnitude out of nothing.

        The old median-centred RMS fallback had a breakdown point of zero: on a
        window of nine zeros and a one, a reading of 1 scored 3.16 and tremored.
        """
        self.assertIsNone(N._scale_z([5.0] * 10, 9.0))
        flat_ish = [0.0] * 9 + [1.0]
        z = N._scale_z(flat_ish, 1.0)
        self.assertTrue(z is None or abs(z) <= N.THRESHOLD,
                        f"a one-unit move off a flat integer window scored {z}")


class TestJudge(unittest.TestCase):
    def _hist(self, n=12, start=100.0, step=1.0):
        vals = [start + i * step for i in range(n)]
        dates = [f"2026-06-{i + 1:02d}" for i in range(n)]
        return vals, dates, [""] * n

    def test_republished_observation_scores_nothing(self):
        vals, dates, _ = self._hist()
        obs = [f"2026-06-{i + 1:02d}" for i in range(len(vals))]
        z, trembling, direction, note = N.judge(
            vals, dates, obs, 999.0, "2026-06-05", "2026-06-20")
        self.assertIsNone(z)
        self.assertEqual(trembling, 0)
        self.assertIn("stale", note)

    def test_dedup_keeps_only_the_first_occurrence(self):
        vals = [10.0, 10.0, 10.0, 20.0]
        dates = ["2026-06-01", "2026-06-02", "2026-06-03", "2026-06-04"]
        obs = ["2026-05-30", "2026-05-30", "2026-05-30", "2026-06-03"]
        z, _, _, _ = N.judge(vals, dates, obs, 30.0, "2026-06-04", "2026-06-05")
        # Two kept observations is under MIN_POINTS, so the honest answer is None.
        self.assertIsNone(z)

    def test_thin_history_yields_none(self):
        vals, dates, obs = self._hist(n=N.MIN_POINTS - 1)
        z, trembling, _, _ = N.judge(vals, dates, obs, 500.0, "", "2026-06-20")
        self.assertIsNone(z)
        self.assertEqual(trembling, 0)

    def test_a_real_outlier_still_trembles(self):
        vals, dates, obs = self._hist(n=20)
        z, trembling, direction, _ = N.judge(vals, dates, obs, 5000.0, "", "2026-07-01")
        self.assertIsNotNone(z)
        self.assertEqual(trembling, 1)
        self.assertEqual(direction, "up")

    def test_missing_reading_is_never_scored(self):
        vals, dates, obs = self._hist(n=20)
        z, trembling, _, _ = N.judge(vals, dates, obs, None, "", "2026-07-01")
        self.assertIsNone(z)
        self.assertEqual(trembling, 0)

    def test_age_cap_drops_stale_history(self):
        vals = [100.0 + i for i in range(12)]
        dates = [f"2020-01-{i + 1:02d}" for i in range(12)]
        z, _, _, _ = N.judge(vals, dates, [""] * 12, 200.0, "", "2026-07-01")
        self.assertIsNone(z, "history older than MAX_AGE_DAYS must not build a baseline")


class TestWeekdayVeto(unittest.TestCase):
    def test_veto_suppresses_a_routine_same_weekday_level(self):
        # Four prior Sundays spanning 100-140; today at 120 is routine for a Sunday.
        dates = ["2026-06-07", "2026-06-14", "2026-06-21", "2026-06-28"]
        vals = [100.0, 140.0, 110.0, 130.0]
        vetoed, detail = N.weekday_range_veto(vals, dates, 120.0, "2026-07-05")
        self.assertTrue(vetoed)
        self.assertIn("same-weekday", detail)

    def test_a_crisis_value_can_never_be_vetoed(self):
        dates = ["2026-06-07", "2026-06-14", "2026-06-21", "2026-06-28"]
        vals = [100.0, 140.0, 110.0, 130.0]
        vetoed, _ = N.weekday_range_veto(vals, dates, 5.0, "2026-07-05")
        self.assertFalse(vetoed)


class TestCycleKeying(unittest.TestCase):
    """De-cycling must key off the OBSERVATION date, not the row date."""

    def test_same_weekday_uses_the_cycle_date(self):
        # Rows written Mon/Tue/Wed, but each is ABOUT the preceding Sunday.
        vals = [10.0, 20.0, 30.0]
        rows = ["2026-06-01", "2026-06-09", "2026-06-16"]
        obs = ["2026-05-31", "2026-06-07", "2026-06-14"]  # all Sundays
        self.assertEqual(N._same_weekday(vals, obs, "2026-06-21"), vals)
        # Keyed on the row dates instead, the same call finds nothing in common.
        self.assertNotEqual(N._same_weekday(vals, rows, "2026-06-21"), vals)

    def test_cycle_dates_default_to_row_dates(self):
        """A live snapshot line has no obs_date; behaviour must be unchanged."""
        vals = [float(i) for i in range(14)]
        dates = [f"2026-06-{i + 1:02d}" for i in range(14)]
        with_obs, _, _, _ = N.judge(vals, dates, [""] * 14, 99.0, "", "2026-06-20",
                                    weekly_cycle=True)
        plain, _, _, _ = N.judge(vals, dates, [""] * 14, 99.0, "", "2026-06-20",
                                 weekly_cycle=False)
        self.assertIsNotNone(with_obs)
        self.assertAlmostEqual(with_obs, plain)


class TestClassify(unittest.TestCase):
    def test_direction_and_threshold(self):
        self.assertEqual(N.classify(None), (0, ""))
        self.assertEqual(N.classify(0.0), (0, "flat"))
        self.assertEqual(N.classify(2.9), (0, "up"))
        self.assertEqual(N.classify(-3.1), (1, "down"))


if __name__ == "__main__":
    unittest.main()
