"""Parse locks for the round-8 fetchers (network fetch not exercised here)."""
import os
import sys
import types
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestFxParallelPremium(unittest.TestCase):
    def test_premium_math_and_obs_date(self):
        import fetchers.fx_parallel_premium as M
        real = M.requests
        payloads = {
            M._BLUE: {"venta": 1560, "fechaActualizacion": "2026-07-22T20:59:00.000Z"},
            M._OFICIAL: {"venta": 1200, "fechaActualizacion": "2026-07-22T18:00:00.000Z"},
        }

        class R:
            def __init__(self, u): self._u = u; self.status_code = 200
            def json(self): return payloads[self._u]
        M.requests = types.SimpleNamespace(
            get=lambda u, **k: R(u), RequestException=Exception)
        try:
            out = M.fetch_daily()
        finally:
            M.requests = real
        self.assertAlmostEqual(out["raw_value"], 30.0, places=2)  # 1560/1200-1 = 30%
        self.assertEqual(out["obs_date"], "2026-07-22")


class TestHkmaAggrBalance(unittest.TestCase):
    def test_reads_closing_balance(self):
        import fetchers.hkma_aggr_balance as M
        real = M.requests
        body = {"result": {"records": [
            {"end_of_date": "2026-07-22", "closing_balance": 53934}]}}

        class R:
            status_code = 200
            def json(self): return body
        M.requests = types.SimpleNamespace(
            get=lambda *a, **k: R(), RequestException=Exception)
        try:
            out = M.fetch_daily()
        finally:
            M.requests = real
        self.assertEqual(out["raw_value"], 53934.0)
        self.assertEqual(out["obs_date"], "2026-07-22")
        self.assertEqual(M.ANOMALY_DIRECTION, "down")


if __name__ == "__main__":
    unittest.main()
