"""net_outages settle (R23.1): the window is settled to a completed D-1 22:00Z
window so IODA's ~24h detection latency cannot inflate the count (the 2026-08-24
false alarm read 12 live, 4 settled). These stub the one network entry point and
read no committed record, so they are safe in the pre-collect gate.
"""
import datetime
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import collect
from core import normalize
from fetchers import net_outages as no


def _ts(y, m, d, H, M=0):
    return int(datetime.datetime(y, m, d, H, M, tzinfo=datetime.timezone.utc).timestamp())


class TestSettledWindow(unittest.TestCase):
    def test_cron_2226Z_yields_D1_2200Z_window(self):
        f, u, obs = no._settled_window(_ts(2026, 8, 25, 22, 26))
        self.assertEqual(obs, "2026-08-24")
        self.assertEqual(u, _ts(2026, 8, 24, 22, 0))
        self.assertEqual(f, u - 86400)

    def test_exactly_2200Z_is_inclusive(self):
        f, u, obs = no._settled_window(_ts(2026, 8, 25, 22, 0))
        self.assertEqual(obs, "2026-08-24")

    def test_before_2200Z_self_corrects_to_D2(self):
        f, u, obs = no._settled_window(_ts(2026, 8, 25, 21, 59))
        self.assertEqual(obs, "2026-08-23")


class _Resp:
    def __init__(self, payload, status=200):
        self._p, self.status_code = payload, status

    def json(self):
        return self._p


class TestFetchDaily(unittest.TestCase):
    def _run(self, payload, status=200):
        import requests
        real = requests.get
        requests.get = lambda *a, **k: _Resp(payload, status)
        try:
            return no.fetch_daily()
        finally:
            requests.get = real

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
