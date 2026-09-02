"""Parse locks for the round-8 fetchers (network fetch not exercised here)."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from support import stub_requests


class TestFxParallelPremium(unittest.TestCase):
    def test_premium_math_and_obs_date(self):
        import fetchers.fx_parallel_premium as M
        payloads = {
            M._BLUE: {"venta": 1560, "fechaActualizacion": "2026-07-22T20:59:00.000Z"},
            M._OFICIAL: {"venta": 1200, "fechaActualizacion": "2026-07-22T18:00:00.000Z"},
        }

        class R:
            def __init__(self, u): self._u = u; self.status_code = 200
            def json(self): return payloads[self._u]
        with stub_requests(M, get=lambda u, **k: R(u)):
            out = M.fetch_daily()
        self.assertAlmostEqual(out["raw_value"], 30.0, places=2)  # 1560/1200-1 = 30%
        self.assertEqual(out["obs_date"], "2026-07-22")


class TestHkmaAggrBalance(unittest.TestCase):
    def test_reads_closing_balance(self):
        import fetchers.hkma_aggr_balance as M
        body = {"result": {"records": [
            {"end_of_date": "2026-07-22", "closing_balance": 53934}]}}

        class R:
            status_code = 200
            def json(self): return body
        with stub_requests(M, get=lambda *a, **k: R()):
            out = M.fetch_daily()
        self.assertEqual(out["raw_value"], 53934.0)
        self.assertEqual(out["obs_date"], "2026-07-22")
        self.assertEqual(M.ANOMALY_DIRECTION, "down")


class TestCnhCnyLegTimestamps(unittest.TestCase):
    """A spread is only meaningful if both legs are quoted at the same moment."""

    def _fetch(self, cnh_t, cny_t, cnh=6.7705, cny=6.7714):
        import fetchers.cnh_cny as M
        quotes = {"USDCNH=X": (cnh, cnh_t), "USDCNY=X": (cny, cny_t)}

        class R:
            def __init__(self, u): self._u = u; self.status_code = 200
            def json(self):
                sym = self._u.rsplit("/", 1)[-1]
                price, when = quotes[sym]
                return {"chart": {"result": [{"meta": {
                    "regularMarketPrice": price, "regularMarketTime": when}}]}}
        with stub_requests(M, get=lambda u, **k: R(u)):
            return M.fetch_daily()

    def test_legs_hours_apart_are_written_empty(self):
        # The real 2026-07-25 case: offshore still on Friday's close, onshore on
        # a Saturday print 6.5h later. Subtracting them is not a spread.
        out = self._fetch(1774386000 - 6 * 3600 - 1800, 1774386000)
        self.assertIsNone(out["raw_value"])
        self.assertIn("not comparable", out["source_note"])

    def test_simultaneous_legs_score_and_carry_the_older_obs_date(self):
        base = 1774386000  # both legs within minutes of each other
        out = self._fetch(base, base - 600)
        self.assertAlmostEqual(out["raw_value"], -9.0, places=1)
        import datetime
        expected = datetime.datetime.fromtimestamp(
            base - 600, datetime.timezone.utc).strftime("%Y-%m-%d")
        self.assertEqual(out["obs_date"], expected)

    def test_a_missing_quote_time_is_written_empty(self):
        out = self._fetch(None, 1774386000)
        self.assertIsNone(out["raw_value"])


class TestAdsbProviderCorroboration(unittest.TestCase):
    """A coverage failure can only lose aircraft, so the max is the fullest view."""

    def _region(self, counts):
        from core import adsb
        by_host = dict(zip(["airplanes.live", "opendata.adsb.fi", "api.adsb.lol"], counts))

        class R:
            def __init__(self, u):
                self.status_code = 200
                host = next(h for h in by_host if h in u)
                self._n = by_host[host]
            def json(self):
                n = self._n
                return {"ac": ([{"alt_baro": 30000}] * n) + [{"alt_baro": "ground"}]}
        with stub_requests(adsb, get=lambda u, **k: R(u)):
            return adsb.region_airborne(39.0, -77.0)

    def test_one_provider_with_a_coverage_gap_cannot_set_the_reading(self):
        # The defect this fixes: 300 from a degraded provider used to be accepted
        # outright, because it sits far above the absolute floor of 30.
        count, note = self._region([300, 800, 790])
        self.assertEqual(count, 800)
        self.assertIn("disagreed", note)

    def test_agreeing_providers_report_the_agreed_level(self):
        count, note = self._region([297, 288, 291])
        self.assertEqual(count, 297)
        self.assertNotIn("disagreed", note)

    def test_a_real_collapse_is_reported_not_suppressed(self):
        # All providers see an empty sky: that is a measurement, not a fault.
        count, note = self._region([4, 5, 3])
        self.assertEqual(count, 5)
        self.assertIn("under floor", note)


if __name__ == "__main__":
    unittest.main()
