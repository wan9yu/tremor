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
        z, trembling, direction, note, status = N.judge(
            vals, dates, obs, 999.0, "2026-06-05", "2026-06-20")
        self.assertIsNone(z)
        self.assertEqual(trembling, 0)
        self.assertIn("stale", note)

    def test_dedup_keeps_only_the_first_occurrence(self):
        vals = [10.0, 10.0, 10.0, 20.0]
        dates = ["2026-06-01", "2026-06-02", "2026-06-03", "2026-06-04"]
        obs = ["2026-05-30", "2026-05-30", "2026-05-30", "2026-06-03"]
        z, _, _, _, _ = N.judge(vals, dates, obs, 30.0, "2026-06-04", "2026-06-05")
        # Two kept observations is under MIN_POINTS, so the honest answer is None.
        self.assertIsNone(z)

    def test_thin_history_yields_none(self):
        vals, dates, obs = self._hist(n=N.MIN_POINTS - 1)
        z, trembling, _, _, _ = N.judge(vals, dates, obs, 500.0, "", "2026-06-20")
        self.assertIsNone(z)
        self.assertEqual(trembling, 0)

    def test_a_real_outlier_still_trembles(self):
        vals, dates, obs = self._hist(n=20)
        z, trembling, direction, _, _ = N.judge(vals, dates, obs, 5000.0, "", "2026-07-01")
        self.assertIsNotNone(z)
        self.assertEqual(trembling, 1)
        self.assertEqual(direction, "up")

    def test_missing_reading_is_never_scored(self):
        vals, dates, obs = self._hist(n=20)
        z, trembling, _, _, _ = N.judge(vals, dates, obs, None, "", "2026-07-01")
        self.assertIsNone(z)
        self.assertEqual(trembling, 0)

    def test_age_cap_drops_stale_history(self):
        vals = [100.0 + i for i in range(12)]
        dates = [f"2020-01-{i + 1:02d}" for i in range(12)]
        z, _, _, _, _ = N.judge(vals, dates, [""] * 12, 200.0, "", "2026-07-01")
        self.assertIsNone(z, "history older than MAX_AGE_DAYS must not build a baseline")


class TestStatus(unittest.TestCase):
    """"Cannot score" must never again be indistinguishable from "calm"."""

    def _hist(self, n):
        vals = [100.0 + i for i in range(n)]
        return vals, [f"2026-06-{i + 1:02d}" for i in range(n)], [""] * n

    def _status(self, values, today, dates=None, obs=None, today_obs=""):
        dates = dates or [f"2026-06-{i + 1:02d}" for i in range(len(values))]
        return N.judge(values, dates, obs or [""] * len(values),
                       today, today_obs, "2026-07-01")[4]

    def test_enough_clean_history_is_scoring(self):
        self.assertEqual(self._status(self._hist(20)[0], 500.0), N.STATUS_SCORING)

    def test_too_little_history_is_warming_up(self):
        self.assertEqual(self._status(self._hist(4)[0], 500.0), N.STATUS_WARMING)

    def test_a_missing_reading_is_dark(self):
        self.assertEqual(self._status(self._hist(20)[0], None), N.STATUS_DARK)

    def test_a_window_with_no_dispersion_is_no_spread(self):
        self.assertEqual(self._status([5.0] * 14, 9.0), N.STATUS_FLAT)

    def test_a_republished_observation_reports_stale(self):
        vals, dates, _ = self._hist(12)
        obs = [f"2026-06-{i + 1:02d}" for i in range(12)]
        self.assertEqual(N.judge(vals, dates, obs, 9.0, "2026-06-05", "2026-06-20")[4],
                         N.STATUS_STALE)

    def test_blind_means_holding_a_reading_it_cannot_judge(self):
        """Dark is loud already; stale was judged when it first arrived."""
        self.assertIn(N.STATUS_WARMING, N.BLIND_STATUSES)
        self.assertIn(N.STATUS_FLAT, N.BLIND_STATUSES)
        self.assertNotIn(N.STATUS_DARK, N.BLIND_STATUSES)
        self.assertNotIn(N.STATUS_STALE, N.BLIND_STATUSES)
        self.assertNotIn(N.STATUS_SCORING, N.BLIND_STATUSES)


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
        with_obs, _, _, _, _ = N.judge(vals, dates, [""] * 14, 99.0, "", "2026-06-20",
                                    weekly_cycle=True)
        plain, _, _, _, _ = N.judge(vals, dates, [""] * 14, 99.0, "", "2026-06-20",
                                 weekly_cycle=False)
        self.assertIsNotNone(with_obs)
        self.assertAlmostEqual(with_obs, plain)


class TestClassify(unittest.TestCase):
    def test_direction_and_threshold(self):
        self.assertEqual(N.classify(None), (0, ""))
        self.assertEqual(N.classify(0.0), (0, "flat"))
        self.assertEqual(N.classify(2.9), (0, "up"))
        self.assertEqual(N.classify(-3.1), (1, "down"))

    def test_the_bar_is_higher_on_a_young_window(self):
        """A ten-reading window must clear more than a ninety-reading one."""
        self.assertEqual(N.threshold_for(N.WINDOW), N.THRESHOLD)
        self.assertGreater(N.threshold_for(10), N.threshold_for(30))
        self.assertGreater(N.threshold_for(30), N.threshold_for(60))
        self.assertEqual(N.classify(3.5, n=N.WINDOW), (1, "up"))
        self.assertEqual(N.classify(3.5, n=10), (0, "up"))

    def test_the_table_never_rises_with_evidence(self):
        thresholds = [N.threshold_for(n) for n in range(N.MIN_POINTS, N.WINDOW + 1)]
        self.assertEqual(thresholds, sorted(thresholds, reverse=True))

    def test_a_window_past_the_cap_uses_the_base_threshold(self):
        self.assertEqual(N.threshold_for(N.WINDOW + 50), N.THRESHOLD)


class TestQuantumFloor(unittest.TestCase):
    """A counted line must not go silent because a calm run tied its scale."""

    FLAT = [1.0] * 20

    def test_a_tied_window_cannot_judge_without_a_quantum(self):
        self.assertIsNone(N._scale_z(self.FLAT, 160.0))

    def test_the_floor_lets_the_spike_be_judged(self):
        z = N._scale_z(self.FLAT, 160.0, quantum=1)
        self.assertIsNotNone(z)
        self.assertGreater(z, 100)

    def test_the_floor_never_widens_a_resolvable_scale(self):
        spread = [float(v) for v in range(20)]
        self.assertAlmostEqual(N._scale_z(spread, 40.0),
                               N._scale_z(spread, 40.0, quantum=1))

    def test_a_quantized_line_goes_scoring_not_flat(self):
        dates = [f"2026-06-{i + 1:02d}" for i in range(20)]
        _, _, _, _, without = N.judge(self.FLAT, dates, [""] * 20, 9.0, "", "2026-06-25")
        _, _, _, _, with_q = N.judge(self.FLAT, dates, [""] * 20, 9.0, "", "2026-06-25",
                                     quantum=1)
        self.assertEqual(without, N.STATUS_FLAT)
        self.assertEqual(with_q, N.STATUS_SCORING)


class TestDecycling(unittest.TestCase):
    """The weekly rhythm is removed from the window, not carved out of it."""

    def _weekly_series(self, weeks=12, dip=-40.0):
        """A flat line except every Sunday, which dips."""
        import datetime
        start = datetime.date(2026, 1, 5)  # a Monday
        values, dates = [], []
        for i in range(weeks * 7):
            day = start + datetime.timedelta(days=i)
            values.append(100.0 + (dip if day.weekday() == 6 else 0.0)
                          + (i % 5) * 0.5)   # a little ordinary noise
            dates.append(day.isoformat())
        return values, dates

    def test_a_routine_sunday_dip_is_not_a_tremble(self):
        values, dates = self._weekly_series()
        obs = [""] * len(values)
        z, trembling, _, _, status = N.judge(values, dates, obs, 60.0, "", "2026-03-29",
                                             weekly_cycle=True)
        self.assertEqual(status, N.STATUS_SCORING)
        self.assertEqual(trembling, 0, f"a normal Sunday trembled at z={z}")

    def test_a_real_collapse_on_a_sunday_still_fires(self):
        values, dates = self._weekly_series()
        obs = [""] * len(values)
        _, trembling, direction, _, _ = N.judge(values, dates, obs, 5.0, "", "2026-03-29",
                                                weekly_cycle=True)
        self.assertEqual((trembling, direction), (1, "down"))

    def test_the_rhythm_is_not_removed_before_the_gate(self):
        """Below DECYCLE_MIN the window is judged pooled, with the veto."""
        values, dates = self._weekly_series(weeks=6)
        self.assertLess(len(values), N.DECYCLE_MIN)
        residuals, _ = N._decycled(values, dates, 60.0, "2026-02-15")
        self.assertIsNotNone(residuals)          # the machinery works...
        _, trembling, _, note, _ = N.judge(values, dates, [""] * len(values), 60.0, "",
                                           "2026-02-15", weekly_cycle=True)
        self.assertEqual(trembling, 0)           # ...but the veto is what guards here
        self.assertIn("suppressed", note)

    def test_offsets_are_measured_from_the_window(self):
        values, dates = self._weekly_series()
        residuals, today = N._decycled(values, dates, 60.0, "2026-03-29")
        # Sundays sit 40 below; after de-cycling the window has no weekday step.
        import statistics
        self.assertLess(statistics.pstdev(residuals), 5.0)
        self.assertAlmostEqual(today, 100.0, delta=3.0)


class TestAnchoredScaleMode(unittest.TestCase):
    """A line whose normal is a DECLARED constant scores against anchor+materiality,
    not a rolling window — fixing both the tiny-Qn hypersensitivity and the Qn=0
    blindness that a near-constant series hits. Opt-in only."""

    def test_scores_from_declared_constants(self):
        # 3*materiality is by construction the trembling bar; no history needed.
        z, status, n = N.robust_z([], 75.0, anchor=0, materiality=25)
        self.assertAlmostEqual(z, 3.0)
        self.assertEqual(status, N.STATUS_SCORING)
        self.assertEqual(n, N.WINDOW)                       # flat 3.0 bar
        z2, _, _ = N.robust_z([], 314.7, anchor=0, materiality=25)
        self.assertAlmostEqual(z2, 12.588, places=3)        # USDC's SVB close fires

    def test_needs_no_warmup(self):
        # declared constants, so a depeg in the first days is caught, not hidden.
        z, status, n = N.robust_z([10.0, 11.0], 90.0, anchor=0, materiality=25)
        self.assertEqual(status, N.STATUS_SCORING)
        self.assertGreater(z, 3.0)

    def test_perfect_value_is_a_scoreable_zero_not_blind(self):
        # a $0/perfect-peg day is an honest 0, never STATUS_FLAT — the structural
        # -zero blindness (Qn=0 -> "cannot score" looking like "calm") is gone.
        z, status, n = N.robust_z([], 0.0, anchor=0, materiality=25)
        self.assertEqual(z, 0.0)
        self.assertEqual(status, N.STATUS_SCORING)
        self.assertEqual(N.classify(0.0, n), (0, "flat"))

    def test_a_gap_stays_dark_never_forward_filled(self):
        # the branch reads only `today`; a missing reading hits the DARK guard.
        z, status, n = N.robust_z([10.0] * 90, None, anchor=0, materiality=25)
        self.assertIsNone(z)
        self.assertEqual(status, N.STATUS_DARK)

    def test_absent_materiality_is_byte_identical(self):
        # the opt-in guarantee: without MATERIALITY the rolling path is untouched.
        rng = Random(7)
        hist = [rng.gauss(100, 5) for _ in range(90)]
        base = N.robust_z(list(hist), 130.0)
        self.assertEqual(N.robust_z(list(hist), 130.0, anchor=None, materiality=None), base)
        # a QUANTUM line is likewise unchanged
        q = N.robust_z([1.0] * 20, 5.0, quantum=1)
        self.assertEqual(N.robust_z([1.0] * 20, 5.0, quantum=1, materiality=None), q)

    def test_quantum_and_materiality_are_exclusive(self):
        with self.assertRaises(AssertionError):
            N.robust_z([], 50.0, quantum=1, materiality=25)


class TestClosedStatus(unittest.TestCase):
    """A weekend with no reading on a WEEKEND_MARKET line is a market closure, not a
    failure — deterministic from the date, so replay reproduces it. Opt-in only; a
    weekday empty (a holiday, an outage) stays dark."""

    def test_a_weekend_empty_is_closed(self):
        # 2026-08-16 is a Sunday, 2026-08-15 a Saturday
        self.assertEqual(N.robust_z([], None, today_date="2026-08-16", weekend_market=True),
                         (None, N.STATUS_CLOSED, 0))
        self.assertEqual(N.robust_z([], None, today_date="2026-08-15",
                                    weekend_market=True)[1], N.STATUS_CLOSED)

    def test_a_weekday_empty_stays_dark(self):
        # 2026-08-13 is a Thursday — a weekday empty is not a market closure
        self.assertEqual(N.robust_z([], None, today_date="2026-08-13",
                                    weekend_market=True)[1], N.STATUS_DARK)

    def test_absent_weekend_market_is_byte_identical(self):
        # a line that does not opt in scores a weekend empty as dark, exactly as before
        base = N.robust_z([], None, today_date="2026-08-16")
        self.assertEqual(base, (None, N.STATUS_DARK, 0))
        self.assertEqual(N.robust_z([], None, today_date="2026-08-16",
                                    weekend_market=False), base)

    def test_closure_only_on_an_empty_a_weekend_reading_still_scores(self):
        rng = Random(3)
        hist = [rng.gauss(100, 5) for _ in range(90)]
        _, status, _ = N.robust_z(hist, 130.0, today_date="2026-08-15", weekend_market=True)
        self.assertEqual(status, N.STATUS_SCORING)   # a present Saturday quote is judged

    def test_cnh_cny_declares_it_and_the_scorer_reads_it(self):
        import collect
        from fetchers import cnh_cny
        self.assertTrue(cnh_cny.WEEKEND_MARKET)
        self.assertTrue(collect.scoring_attrs(cnh_cny)["weekend_market"])


if __name__ == "__main__":
    unittest.main()
