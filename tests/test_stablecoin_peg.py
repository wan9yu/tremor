"""stablecoin_peg fetcher: the depeg aggregation and the settle-lag are pure logic.

These stub the one network entry point (``candles``) and read no committed record,
so they are safe in the pre-collect gate.
"""
import datetime
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from fetchers import stablecoin_peg as sp


class TestDevBp(unittest.TestCase):
    def test_deviation_in_basis_points(self):
        self.assertEqual(round(sp.dev_bp(1.0), 1), 0.0)
        self.assertEqual(round(sp.dev_bp(0.9685), 1), 315.0)   # USDC on the SVB close
        self.assertEqual(round(sp.dev_bp(1.001), 1), 10.0)     # a premium counts the same


class TestFetchDaily(unittest.TestCase):
    def setUp(self):
        self._real = sp.candles
        # today is fixed via the module's datetime; stub the network instead
        self.today = datetime.date.today().isoformat()
        self.yesterday = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()

    def tearDown(self):
        sp.candles = self._real

    def _stub(self, mapping):
        # mapping: pair -> [(date, close, low)] oldest-first
        sp.candles = lambda pair, limit, start=None, end=None: mapping[pair]

    def test_worst_coin_wins_and_settles_to_yesterday(self):
        self._stub({
            "usdcusd": [(self.yesterday, 0.9685, 0.80), (self.today, 0.99, 0.98)],   # SVB-like close
            "usdtusd": [(self.yesterday, 0.999, 0.999), (self.today, 0.9991, 0.999)],
        })
        r = sp.fetch_daily()
        self.assertEqual(r["raw_value"], 315.0)          # USDC 315bp beats USDT 10bp
        self.assertEqual(r["obs_date"], self.yesterday)  # today's forming candle is skipped
        self.assertEqual(r["components"], {"USDC": 315.0, "USDT": 10.0})

    def test_missing_leg_is_empty_not_half_computed(self):
        self._stub({
            "usdcusd": [(self.yesterday, 0.9685, 0.80)],
            "usdtusd": [(self.today, 0.9991, 0.999)],   # only a forming candle -> no settled row
        })
        r = sp.fetch_daily()
        self.assertIsNone(r["raw_value"])
        self.assertIn("no settled candle", r["source_note"])

    def test_source_failure_is_empty(self):
        def boom(*a, **k):
            raise sp.requests.RequestException("down")
        sp.candles = boom
        r = sp.fetch_daily()
        self.assertIsNone(r["raw_value"])
        self.assertIn("unavailable", r["source_note"])


class TestScaleModeWiring(unittest.TestCase):
    """The line opts into anchored scale-mode; the declaration must reach the scorer
    so a real depeg fires while USDT's ordinary venue discount does not."""

    def test_declares_anchor_and_materiality_not_quantum(self):
        self.assertEqual(sp.ANCHOR, 0)
        self.assertEqual(sp.MATERIALITY, 25)
        self.assertFalse(hasattr(sp, "QUANTUM"))   # the two are mutually exclusive

    def test_scoring_attrs_carries_the_declaration(self):
        import collect
        attrs = collect.scoring_attrs(sp)
        self.assertEqual(attrs["anchor"], 0)
        self.assertEqual(attrs["materiality"], 25)

    def test_score_row_fires_on_a_depeg_not_on_venue_fuzz(self):
        import collect
        attrs = collect.scoring_attrs(sp)
        # an anchored line needs no history to score
        depeg = collect.score_row("2023-03-11", 314.7, "", "2023-03-11", [], **attrs)
        self.assertEqual(depeg["trembling"], "1")
        self.assertEqual(depeg["direction"], "up")
        fuzz = collect.score_row("2026-06-01", 12.7, "", "2026-06-01", [], **attrs)
        self.assertEqual(fuzz["trembling"], "0")     # 12.7bp -> z=0.5, calm


if __name__ == "__main__":
    unittest.main()
