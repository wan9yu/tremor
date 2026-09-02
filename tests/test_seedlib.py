"""The seed merge must never edit the published record. Locked after it did.

The first FRED seed deleted 26 published rows (dark days, stale republishes,
and a date collision). These tests pin the corrected rule in tools/seedlib.py,
plus the small pure functions added in the same repair round.
"""
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tools"))

import seedlib
import support


def _live(date, raw, obs, note="live"):
    return {"date": date, "raw_value": raw, "obs_date": obs, "source_note": note}


def _note(obs, value):
    return f"import {obs}"


class TestMerge(unittest.TestCase):
    def test_every_published_row_survives(self):
        live = [
            _live("2026-07-10", "2.9", "2026-07-09"),
            _live("2026-07-11", "", ""),                    # dark day
            _live("2026-07-12", "2.9", "2026-07-09"),       # stale republish
        ]
        history = [("2026-07-01", 2.5), ("2026-07-09", 2.9)]
        plan, dropped = seedlib.merge(history, live, _note)
        dates = [p[0] for p in plan]
        self.assertIn("2026-07-10", dates)
        self.assertIn("2026-07-11", dates)  # the dark day is published record
        self.assertIn("2026-07-12", dates)  # so is the republish
        self.assertIn("2026-07-01", dates)  # the archive fills the deep past
        self.assertEqual(dropped, [])
        # The observation a live row already carries is not imported again.
        self.assertEqual(dates.count("2026-07-09"), 0)

    def test_collision_with_a_republish_yields_to_the_observation(self):
        live = [
            _live("2026-07-10", "2.9", "2026-07-09"),
            _live("2026-07-11", "2.9", "2026-07-09"),  # republish ON an obs date
        ]
        history = [("2026-07-09", 2.9), ("2026-07-11", 3.1)]
        plan, dropped = seedlib.merge(history, live, _note)
        by_date = {p[0]: p for p in plan}
        # The archive observation for 07-11 wins the date the republish held.
        self.assertEqual(by_date["2026-07-11"][1], 3.1)
        self.assertTrue(dropped)

    def test_collision_with_a_first_occurrence_drops_the_import(self):
        live = [_live("2026-07-11", "2.9", "2026-07-10")]
        history = [("2026-07-11", 3.1)]
        plan, dropped = seedlib.merge(history, live, _note)
        by_date = {p[0]: p for p in plan}
        self.assertEqual(by_date["2026-07-11"][1], 2.9)  # published row wins
        self.assertTrue(dropped)                          # and the drop is loud

    def test_dates_are_unique_and_ordered(self):
        live = [_live("2026-07-10", "2.9", "2026-07-09")]
        history = [("2026-07-0%d" % d, float(d)) for d in range(1, 9)]
        plan, _ = seedlib.merge(history, live, _note)
        dates = [p[0] for p in plan]
        self.assertEqual(dates, sorted(dates))
        self.assertEqual(len(dates), len(set(dates)))

    def test_old_verdict_notes_are_stripped(self):
        self.assertEqual(
            seedlib.strip_verdict_notes(
                "FRED X 2.9 [stale: observation already recorded]"),
            "FRED X 2.9")
        self.assertEqual(
            seedlib.strip_verdict_notes(
                "n=1 [suppressed: within same-weekday range [1, 2] (n=3)]"),
            "n=1")


class TestRerunIsIdempotent(unittest.TestCase):
    """A seeder may be re-run; the record it has already written survives.

    This is what makes hand-restoring a pre-seed archive unnecessary — and the
    hand-restore is what deleted a published live row on 2026-08-04.
    """

    def test_a_second_merge_changes_nothing_and_keeps_later_rows(self):
        history = [("2026-07-01", 1.0), ("2026-07-02", 2.0)]
        first, _ = seedlib.merge(history, [], _note)
        # ...then the daily collector adds a row the archive never had.
        seeded = [{"date": d, "raw_value": "" if raw is None else str(raw),
                   "obs_date": obs, "source_note": note}
                  for d, raw, note, obs in first]
        seeded.append({"date": "2026-07-09", "raw_value": "9",
                       "obs_date": "2026-07-09", "source_note": "live"})
        second, dropped = seedlib.merge(history, seeded, _note)
        self.assertEqual([p[0] for p in second],
                         ["2026-07-01", "2026-07-02", "2026-07-09"])
        self.assertEqual(dropped, [])
        self.assertEqual(second[-1][1], 9.0, "the live row did not survive")


class TestLegDiscipline(unittest.TestCase):
    def test_fred_latest_common_pairs_only_shared_dates(self):
        from core import fred
        calls = {"SOFR": [("2026-07-29", 3.65), ("2026-07-30", 3.40)],
                 "IORB": [("2026-07-29", 3.65)]}
        with support.stub_attr(fred, "series", lambda sid: calls[sid]):
            date, a, b = fred.latest_common("SOFR", "IORB")
        # 07-30 has no IORB leg; the honest pair is 07-29, spread zero — not
        # the post-step SOFR against the pre-step IORB.
        self.assertEqual((date, a, b), ("2026-07-29", 3.65, 3.65))

    def test_weekend_stamp_maps_to_friday(self):
        from fetchers import fx_parallel_premium as fx
        self.assertEqual(fx._observation_date("2026-08-01"), "2026-07-31")  # Sat
        self.assertEqual(fx._observation_date("2026-08-02"), "2026-07-31")  # Sun
        self.assertEqual(fx._observation_date("2026-07-31"), "2026-07-31")  # Fri

    def test_weekend_leg_gap_is_recognized(self):
        import datetime
        from fetchers import cnh_cny

        def epoch(s):
            return int(datetime.datetime.fromisoformat(s + "+00:00").timestamp())
        # CNH frozen Friday 20:59Z, CNY restamped Saturday 21:32Z: closure.
        self.assertTrue(cnh_cny._weekend_gap(
            epoch("2026-07-31T20:59:00"), epoch("2026-08-01T21:32:00")))
        # A mid-week 6h desync is a malfunction, not a weekend.
        self.assertFalse(cnh_cny._weekend_gap(
            epoch("2026-07-29T10:00:00"), epoch("2026-07-29T16:00:00")))


class TestRunSeedRefusesLoss(unittest.TestCase):
    def test_a_plan_shorter_than_the_live_record_is_refused(self):
        with self.assertRaises(seedlib.SeedWouldLoseRows) as caught:
            seedlib.check_no_loss("port_throughput", live_rows=241, planned_rows=200)
        self.assertIn("241", str(caught.exception))
        self.assertIn("200", str(caught.exception))

    def test_a_plan_that_keeps_every_row_is_allowed(self):
        seedlib.check_no_loss("port_throughput", live_rows=241, planned_rows=241)
        seedlib.check_no_loss("port_throughput", live_rows=241, planned_rows=300)


class TestMergeDatesRowsThroughRowDate(unittest.TestCase):
    """A lagged source publishes an observation days after it happened, so the
    row it belongs on is not its obs_date. Without this hook a lagged seeder
    cannot use merge at all, and re-dates every row it writes."""

    def test_default_dates_a_row_on_its_observation(self):
        plan, _ = seedlib.merge([("2026-07-10", 4039.0)], [], lambda o, v: "n")
        self.assertEqual(plan[0][0], "2026-07-10")
        self.assertEqual(plan[0][3], "2026-07-10")

    def test_row_date_shifts_the_row_but_not_the_observation(self):
        plan, _ = seedlib.merge([("2026-07-10", 4039.0)], [], lambda o, v: "n",
                                row_date=lambda obs: "2026-07-20")
        self.assertEqual(plan[0][0], "2026-07-20", "the row moves to its publication date")
        self.assertEqual(plan[0][3], "2026-07-10", "the observation date is preserved")

    def test_republish_collision_is_checked_in_row_space_not_observation_space(self):
        """Regression: the republish-collision check once compared the raw
        observation date against republish_dates, which is keyed by row date
        (not observation date). Under a lagged row_date the two values never
        coincide, so a live republish sitting on the row date a lagged import
        maps to was mistaken for a hard first-occurrence collision, and the
        archive observation that should win that date was dropped instead."""
        live = [
            _live("2026-07-11", "2.9", "2026-07-09"),  # first occurrence
            _live("2026-07-12", "2.9", "2026-07-09"),  # republish, row date 2026-07-12
        ]
        # obs 2026-07-10 lags 2 days -> row date 2026-07-12, the republish's date.
        history = [("2026-07-10", 3.1)]
        plan, dropped = seedlib.merge(
            history, live, _note,
            row_date=lambda obs: {"2026-07-10": "2026-07-12"}[obs])
        by_date = {p[0]: p for p in plan}
        self.assertEqual(by_date["2026-07-12"][1], 3.1,
                          "the archive observation should win the republish's row date")
        self.assertTrue(dropped)


if __name__ == "__main__":
    unittest.main()
