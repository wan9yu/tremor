"""net_outages settle (R23.1): the window is settled to a completed D-1 22:00Z
window so IODA's ~24h detection latency cannot inflate the count (the 2026-08-24
false alarm read 12 live, 4 settled). ``window_for``/``window_for_day`` are the
ONE settled-window definition (T1) — the live path, the reconciliation tool and
the seeder all resolve to this same arithmetic; see tests/lint_ssot.py for the
source-scan guard that keeps it in this one place. These stub the one network
entry point and read no committed record, so they are safe in the pre-collect
gate.
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
from fetchers import net_outages as no


def _ts(y, m, d, H, M=0):
    return int(datetime.datetime(y, m, d, H, M, tzinfo=datetime.timezone.utc).timestamp())


class TestWindowFor(unittest.TestCase):
    """The timestamp-anchored form: ``window_for(now_ts) -> (from, until, obs)``."""

    def test_cron_2226Z_yields_D1_2200Z_window(self):
        f, u, obs = no.window_for(_ts(2026, 8, 25, 22, 26))
        self.assertEqual(obs, "2026-08-24")
        self.assertEqual(u, _ts(2026, 8, 24, 22, 0))
        self.assertEqual(f, u - 86400)

    def test_exactly_2200Z_is_inclusive(self):
        f, u, obs = no.window_for(_ts(2026, 8, 25, 22, 0))
        self.assertEqual(obs, "2026-08-24")

    def test_before_2200Z_self_corrects_to_D2(self):
        f, u, obs = no.window_for(_ts(2026, 8, 25, 21, 59))
        self.assertEqual(obs, "2026-08-23")

    def test_mid_day_monday(self):
        # 2026-08-24 is a Monday. now=noon settles to the 22Z window that
        # closed on the Saturday two days earlier.
        f, u, obs = no.window_for(_ts(2026, 8, 24, 12, 0))
        self.assertEqual(obs, "2026-08-22")
        self.assertEqual(u, _ts(2026, 8, 22, 22, 0))
        self.assertEqual(f, _ts(2026, 8, 21, 22, 0))

    def test_monday_midnight(self):
        f, u, obs = no.window_for(_ts(2026, 8, 24, 0, 0))
        self.assertEqual(obs, "2026-08-22")
        self.assertEqual(u, _ts(2026, 8, 22, 22, 0))
        self.assertEqual(f, _ts(2026, 8, 21, 22, 0))

    def test_sunday_afternoon(self):
        # 2026-08-30 is a Sunday.
        f, u, obs = no.window_for(_ts(2026, 8, 30, 15, 0))
        self.assertEqual(obs, "2026-08-28")
        self.assertEqual(u, _ts(2026, 8, 28, 22, 0))
        self.assertEqual(f, _ts(2026, 8, 27, 22, 0))


class TestWindowForDay(unittest.TestCase):
    """The day-anchored form: ``window_for_day(day) -> (from, until)``, used by
    the reconciliation tool and the seeder (which already know the target day
    rather than "now")."""

    def test_weekday(self):
        # 2026-08-24 is a Monday.
        f, u = no.window_for_day(datetime.date(2026, 8, 24))
        self.assertEqual(u, _ts(2026, 8, 24, 22, 0))
        self.assertEqual(f, _ts(2026, 8, 23, 22, 0))

    def test_saturday(self):
        f, u = no.window_for_day(datetime.date(2026, 8, 29))
        self.assertEqual(u, _ts(2026, 8, 29, 22, 0))
        self.assertEqual(f, _ts(2026, 8, 28, 22, 0))

    def test_sunday(self):
        f, u = no.window_for_day(datetime.date(2026, 8, 30))
        self.assertEqual(u, _ts(2026, 8, 30, 22, 0))
        self.assertEqual(f, _ts(2026, 8, 29, 22, 0))

    def test_agrees_with_window_for_on_its_own_obs_date(self):
        # The two entry points describe the same boundary: window_for's obs_date
        # fed back into window_for_day must reproduce the same (from, until).
        f1, u1, obs = no.window_for(_ts(2026, 8, 25, 22, 26))
        f2, u2 = no.window_for_day(datetime.date.fromisoformat(obs))
        self.assertEqual((f1, u1), (f2, u2))


class _Resp:
    def __init__(self, payload, status=200):
        self._p, self.status_code = payload, status

    def json(self):
        return self._p


class TestFetchDaily(unittest.TestCase):
    def _run(self, payload, status=200):
        with support.stub_requests(no, get=lambda *a, **k: _Resp(payload, status)):
            return no.fetch_daily()

    def test_success_carries_obs_and_settled_note(self):
        out = self._run({"data": [{"entity": {"name": "Tunisia"},
                                   "scores": {"ping-slash24.x": 1}}]})
        self.assertEqual(out["raw_value"], 1.0)
        self.assertIn("obs_date", out)
        self.assertIn("22:00Z", out["source_note"])

    def test_error_omits_obs_date(self):
        self.assertNotIn("obs_date", self._run({}, status=503))

    def test_sweep_still_refused_and_omits_obs_date(self):
        sweep = {"data": [{"entity": {"name": str(i)}, "scores": {"ping-slash24.x": 1}}
                          for i in range(120)]}
        out = self._run(sweep)
        self.assertIsNone(out["raw_value"])
        self.assertNotIn("obs_date", out)

    def test_later_row_date_dedups_to_stale(self):
        opts = collect.scoring_attrs(no)
        rows = [collect.score_row("2026-08-25", 3.0, "n", "2026-08-24", [], **opts)]
        r2 = collect.score_row("2026-08-26", 3.0, "n", "2026-08-24", rows, **opts)
        self.assertEqual(r2["status"], normalize.STATUS_STALE)


if __name__ == "__main__":
    unittest.main()
