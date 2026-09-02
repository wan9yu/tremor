"""flights sample-hour guard (R25 follow-up, sleep-to-target scheme).

flights is a concurrent SNAPSHOT scored against a baseline built at a fixed hour;
daily.yml sleeps to 22:30Z so the sample lands there, and on the rare run delayed
PAST the sleep window this guard refuses the off-hour reading rather than score a
diurnal trough as a flight drop. The guard is a COLLECTION-time decision (never a
scoring attr), frozen into the stored raw as dark. These test the pure helpers and
read no committed record, so they are safe in the pre-collect gate.
"""
import datetime
import os
import re
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import collect
import support
from fetchers import cnh_cny
from fetchers import flights


def _dt(H, M=0, S=0):
    return datetime.datetime(2026, 9, 1, H, M, S, tzinfo=datetime.timezone.utc)


class TestHoursFromTarget(unittest.TestCase):
    def test_exact_target_is_zero(self):
        self.assertAlmostEqual(collect._hours_from_target(_dt(22, 30), 22.5), 0.0)

    def test_late_snapshot_positive(self):
        self.assertAlmostEqual(collect._hours_from_target(_dt(23, 24), 22.5), 0.9)

    def test_early_side_negative(self):
        self.assertAlmostEqual(collect._hours_from_target(_dt(18, 0), 22.5), -4.5)

    def test_wraps_across_midnight(self):
        # 05:54Z against a 22:30 target is +7.4h (short way round), not -16.6h.
        self.assertAlmostEqual(collect._hours_from_target(_dt(5, 54), 22.5), 7.4, places=2)

    def test_antipode_is_minus_twelve(self):
        self.assertAlmostEqual(collect._hours_from_target(_dt(10, 30), 22.5), -12.0)


class TestApplySampleGuard(unittest.TestCase):
    def _call(self, H, M, raw=1600.0, target=22.5, tol=1.5):
        return collect.apply_sample_guard(
            raw, "ADS-B regions [W/C Europe=200] via adsb.lol", "",
            _dt(H, M), target, tol)

    def test_no_target_is_noop(self):
        # The 22 lines that do not declare a target must never be guarded.
        r = collect.apply_sample_guard(1600.0, "note", "", _dt(5, 54), None, 1.5)
        self.assertEqual(r, (1600.0, "note", ""))

    def test_failed_fetch_is_noop(self):
        # raw already None (a real fetch failure) keeps its own more-specific note.
        r = collect.apply_sample_guard(None, "IODA request failed", "", _dt(5, 54), 22.5, 1.5)
        self.assertEqual(r, (None, "IODA request failed", ""))

    def test_on_target_passes_unchanged(self):
        raw, note, obs = self._call(22, 30)
        self.assertEqual(raw, 1600.0)
        self.assertTrue(note.startswith("ADS-B"))

    def test_near_target_within_tolerance_passes(self):
        # 23:24Z is +0.9h, inside +/-1.5h -> scored (a near-target trough-day read).
        raw, _, _ = self._call(23, 24)
        self.assertEqual(raw, 1600.0)

    def test_off_hour_refused(self):
        raw, note, obs = self._call(5, 54)          # +7.4h
        self.assertIsNone(raw)
        self.assertEqual(obs, "")
        self.assertIn("not scored", note)
        self.assertIn("22:30Z", note)
        self.assertIn("ADS-B regions", note)        # original breakdown preserved

    def test_just_outside_tolerance_refused(self):
        # 00:06Z is +1.6h, just past +/-1.5h -> dark.
        raw, _, _ = self._call(0, 6)
        self.assertIsNone(raw)

    def test_just_inside_tolerance_passes(self):
        # 00:00Z is +1.5h exactly -> passes (strict >).
        raw, _, _ = self._call(0, 0)
        self.assertEqual(raw, 1600.0)


class TestFlightsDeclaration(unittest.TestCase):
    def test_flights_declares_the_target(self):
        self.assertEqual(flights.SAMPLE_TARGET_UTC_H, 22.5)
        self.assertEqual(flights.SAMPLE_TOL_H, 1.5)

    def test_target_is_not_a_scoring_attr(self):
        # It must stay a collection-time input; putting it in scoring_attrs would
        # reach replay/seeders, which have no sample time. STABLE_SINCE depends on this.
        self.assertNotIn("sample_target_utc_h", collect.scoring_attrs(flights))
        self.assertNotIn("SAMPLE_TARGET_UTC_H", collect.scoring_attrs(flights))


class TestScheduleArithmetic(unittest.TestCase):
    """cron hour, sleep target and wait cap are three numbers that must agree.

    They are declared in two files and bound by nothing else: a cron edit alone
    silently pushes every collection outside the guard's tolerance, which darks
    the line daily while the whole suite stays green.
    """

    def setUp(self):
        self.daily = os.path.join(ROOT, ".github/workflows/daily.yml")

    def test_the_wait_cap_equals_the_gap_between_cron_and_target(self):
        (cron_h,) = support.cron_hours(self.daily)
        blob = "\n".join(support.workflow_run_steps(self.daily))
        target_h, target_m = re.search(r"today (\d\d):(\d\d):\d\d", blob).groups()
        cap = int(re.search(r"-le\s+(\d+)", blob).group(1))
        target = int(target_h) + int(target_m) / 60
        self.assertEqual(cap, int(round((target - cron_h) * 3600)),
                         "the sleep cap must equal the cron-to-target gap")

    def test_the_sleep_target_is_the_module_target(self):
        blob = "\n".join(support.workflow_run_steps(self.daily))
        target_h, target_m = re.search(r"today (\d\d):(\d\d):\d\d", blob).groups()
        self.assertEqual(int(target_h) + int(target_m) / 60, flights.SAMPLE_TARGET_UTC_H)

    def test_the_head_start_exceeds_the_tolerance(self):
        (cron_h,) = support.cron_hours(self.daily)
        self.assertGreater(flights.SAMPLE_TARGET_UTC_H - cron_h, flights.SAMPLE_TOL_H,
                           "a head-start inside the tolerance cannot absorb any queue delay")


class TestCnhCnyDeclaresTheGuard(unittest.TestCase):
    """cnh_cny's hour-means run -2 (21Z, n=6), 48 (22Z, n=3), 66 (23Z, n=3) --
    adjacent slopes of 50 pips/h (21Z->22Z) and 18 pips/h (22Z->23Z) against a
    Qn of 44.1. The near-target sample is thin, so the +/-0.5h tolerance is set
    conservatively off the steeper slope: ~25 pips (0.57 Qn) worst case, against
    ~75 pips (1.70 Qn) at flights' +/-1.5h. Its tolerance is therefore tighter
    than the flights line's."""

    def test_it_declares_the_shared_target(self):
        self.assertEqual(cnh_cny.SAMPLE_TARGET_UTC_H, flights.SAMPLE_TARGET_UTC_H)

    def test_its_tolerance_is_tighter_than_flights(self):
        self.assertEqual(cnh_cny.SAMPLE_TOL_H, 0.5)
        self.assertLess(cnh_cny.SAMPLE_TOL_H, flights.SAMPLE_TOL_H)

    def test_an_on_target_run_is_scored(self):
        raw, note, obs = collect.apply_sample_guard(
            80.0, "Yahoo ...", "2026-08-31", _dt(22, 30),
            cnh_cny.SAMPLE_TARGET_UTC_H, cnh_cny.SAMPLE_TOL_H)
        self.assertEqual(raw, 80.0)

    def test_the_2026_08_31_pre_open_run_is_refused(self):
        # sampled 00:09Z, +1.65h off target: Friday's onshore close paired
        # against a Monday offshore quote.
        raw, note, obs = collect.apply_sample_guard(
            80.0, "Yahoo ...", "2026-08-31", _dt(0, 9),
            cnh_cny.SAMPLE_TARGET_UTC_H, cnh_cny.SAMPLE_TOL_H)
        self.assertIsNone(raw)
        self.assertEqual(obs, "")
        self.assertIn("not scored", note)


if __name__ == "__main__":
    unittest.main()
