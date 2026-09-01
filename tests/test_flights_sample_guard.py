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

    def test_ci_sleep_target_matches_the_module(self):
        # daily.yml sleeps to a hardcoded 'today HH:MM:SS'; it MUST equal the module's
        # SAMPLE_TARGET_UTC_H, or the sleep parks the sample at one hour while the guard
        # darks anything off a different one — a silent daily-dark divergence.
        yml = open(os.path.join(ROOT, ".github", "workflows", "daily.yml")).read()
        m = re.search(r"date -d 'today (\d\d):(\d\d):\d\d'", yml)
        self.assertIsNotNone(m, "no 'today HH:MM:SS' sleep target found in daily.yml")
        sleep_h = int(m.group(1)) + int(m.group(2)) / 60
        self.assertEqual(sleep_h, flights.SAMPLE_TARGET_UTC_H)


if __name__ == "__main__":
    unittest.main()
