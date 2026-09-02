"""space_weather fetcher: the 3-hourly -> daily-max aggregation, the settle-lag,
and the context-line scoring wiring. These stub the one network entry point
(``requests.get``) and read no committed record, so they are safe in the
pre-collect gate.
"""
import datetime
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import collect
import support
from core import normalize
from fetchers import space_weather as sw


def _rec(tag, kp):
    return {"time_tag": tag, "Kp": kp, "a_running": 0, "station_count": 8}


class TestDailyMax(unittest.TestCase):
    def test_takes_the_days_maximum_not_the_average(self):
        pairs = sw.parse_live([
            _rec("2026-08-14T00:00:00", 2.0),
            _rec("2026-08-14T03:00:00", 5.667),   # the storm hour
            _rec("2026-08-14T06:00:00", 3.0),
            _rec("2026-08-15T00:00:00", 1.0),
        ])
        d = sw.daily_max(pairs)
        self.assertEqual(d["2026-08-14"], 5.667)  # max, not the ~3.56 mean
        self.assertEqual(d["2026-08-15"], 1.0)

    def test_skips_unparseable_kp_without_fabricating(self):
        pairs = sw.parse_live([
            _rec("2026-08-14T00:00:00", None),
            _rec("2026-08-14T03:00:00", 4.0),
        ])
        self.assertEqual(sw.daily_max(pairs), {"2026-08-14": 4.0})

    def test_rejects_a_changed_shape_rather_than_reading_zero(self):
        with self.assertRaises(ValueError):
            sw.parse_live({"repo": "not a list"})


class TestSettled(unittest.TestCase):
    """Only UTC days strictly before ``today`` are complete; the forming day's
    nowcast Kp must never be recorded."""

    def test_drops_the_forming_day(self):
        daily = {"2026-08-13": 4.0, "2026-08-14": 2.0}
        self.assertEqual(sw.settled(daily, today="2026-08-14"),
                         {"2026-08-13": 4.0})


class TestFetchDaily(unittest.TestCase):
    def _run(self, payload, status=200, today="2026-08-15"):
        class _Resp:
            status_code = status
            def json(self_inner):
                return payload

        # pin the settle boundary without a network or a clock
        orig_settled = sw.settled
        with support.stub_requests(sw, get=lambda *a, **k: _Resp()), \
             support.stub_attr(sw, "settled",
                               lambda daily, today=today: orig_settled(daily, today)):
            return sw.fetch_daily()

    def test_reports_the_latest_settled_daily_max(self):
        out = self._run([
            _rec("2026-08-13T00:00:00", 3.0),
            _rec("2026-08-14T00:00:00", 2.0),
            _rec("2026-08-14T21:00:00", 6.333),   # a storm on the latest settled day
            _rec("2026-08-15T00:00:00", 9.0),      # today (forming) — must be dropped
        ])
        self.assertEqual(out["raw_value"], 6.333)      # 08-14's daily MAX, not its 2.0
        self.assertEqual(out["obs_date"], "2026-08-14")  # latest complete day
        self.assertNotIn("2026-08-15", out["source_note"])

    def test_source_failure_degrades_to_stated_empty(self):
        out = self._run([], status=503)
        self.assertIsNone(out["raw_value"])
        self.assertNotIn("obs_date", out)

    def test_malformed_200_degrades_cleanly(self):
        out = self._run({"unexpected": "shape"}, status=200)
        self.assertIsNone(out["raw_value"])


class TestContextScoringWiring(unittest.TestCase):
    """A quiet-then-storm run: the line is a plain rolling-z context line with a
    QUANTUM floor — not anchored — and the storm trembles UP."""

    def test_quantum_floor_carried_not_anchored(self):
        attrs = collect.scoring_attrs(sw)
        self.assertAlmostEqual(attrs["quantum"], 1.0 / 3.0)
        self.assertIsNone(attrs["materiality"])   # rolling z, not scale-mode
        self.assertIsNone(attrs["anchor"])

    def test_a_storm_against_a_quiet_baseline_trembles_up(self):
        # 80 quiet days near Kp 2-3, then a G3 storm at Kp 7 the next day.
        rows = []
        base = datetime.date(2026, 1, 1)
        opts = collect.scoring_attrs(sw)
        for i in range(80):
            d = (base + datetime.timedelta(days=i)).isoformat()
            kp = 2.667 if i % 2 else 2.333
            rows = collect._upsert(rows, collect.score_row(
                d, kp, "seed", d, rows, **opts), d)
        storm_day = (base + datetime.timedelta(days=80)).isoformat()
        storm = collect.score_row(storm_day, 7.0, "storm", storm_day, rows, **opts)
        self.assertEqual(storm["trembling"], "1")
        self.assertEqual(storm["direction"], "up")
        self.assertEqual(storm["status"], normalize.STATUS_SCORING)


if __name__ == "__main__":
    unittest.main()
