"""Parse locks for the round-8 fetchers (network fetch not exercised here)."""
import datetime
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


class TestNetBgpWithdrawalAggregation(unittest.TestCase):
    """The worst-of route-withdrawal aggregation, PURE (no network).

    Builds hourly points for a few countries so daily_stats yields controlled
    daily-min / daily-median, then checks the whole chain — per-country
    fraction against a 28-day rolling-median baseline, worst-of across the
    watch-list — reproduces the probe's Syria (0.031) and Sudan (0.314)
    fractions and picks the deepest withdrawal as the driver.
    """
    _DAY0 = datetime.datetime(2022, 1, 1, tzinfo=datetime.timezone.utc)

    def _country_points(self, level, event_frac, event_day_index=28, days=29):
        """Hourly points where every prior day sits flat at ``level`` (so its
        daily-min == daily-median == level), and the event day dips to
        ``level*event_frac`` for one hour (daily-min == that dip, daily-median
        stays ``level``)."""
        base = int(self._DAY0.timestamp())
        pts = []
        for d in range(days):
            for h in range(24):
                pts.append((base + d * 86400 + h * 3600, float(level)))
        # overwrite one hour of the event day with the withdrawal depth
        ev = event_day_index
        pts[ev * 24 + 12] = (base + ev * 86400 + 12 * 3600, float(level) * event_frac)
        return pts

    def _event_day(self, index=28):
        return (self._DAY0 + datetime.timedelta(days=index)).date().isoformat()

    def test_daily_stats_min_and_median(self):
        import fetchers.net_bgp_withdrawal as M
        pts = self._country_points(1000, 0.1, event_day_index=0, days=1)  # one day, one hour at 100
        stats = M.daily_stats(pts)
        day = self._event_day(0)
        self.assertEqual(stats[day], (100.0, 1000.0))  # min=100, median=1000

    def test_rolling_baseline_needs_min_valid_days(self):
        import fetchers.net_bgp_withdrawal as M
        medians = {(datetime.date(2022, 2, 1) + datetime.timedelta(days=n)).isoformat(): 500.0
                   for n in range(13)}  # only 13 prior days
        day = (datetime.date(2022, 2, 1) + datetime.timedelta(days=13)).isoformat()
        self.assertIsNone(M.rolling_baseline(medians, day))  # 13 < 14 → no baseline
        medians[(datetime.date(2022, 2, 1) + datetime.timedelta(days=13)).isoformat()] = 500.0
        day = (datetime.date(2022, 2, 1) + datetime.timedelta(days=14)).isoformat()
        self.assertEqual(M.rolling_baseline(medians, day), 500.0)  # 14 valid → median

    def test_worst_of_picks_the_deepest_fraction(self):
        import fetchers.net_bgp_withdrawal as M
        frac, cc = M.worst_of({"SY": 0.031, "SD": 0.314, "ID": 0.758, "NG": 0.99})
        self.assertEqual((round(frac, 3), cc), (0.031, "SY"))
        self.assertEqual(M.worst_of({}), (None, None))
        self.assertEqual(M.worst_of({"XX": None}), (None, None))

    def test_aggregate_reproduces_probe_fractions_and_driver(self):
        import fetchers.net_bgp_withdrawal as M
        day = self._event_day(28)
        country_points = {
            "SY": self._country_points(4734.4, 148.0 / 4734.4),  # → 0.031
            "SD": self._country_points(7333.5, 2303.0 / 7333.5),  # → 0.314
            "NG": self._country_points(5000.0, 0.99),             # benign
        }
        worst, driver, fractions = M.aggregate(day, country_points)
        self.assertEqual(driver, "SY")
        self.assertAlmostEqual(fractions["SY"], 0.0313, places=3)
        self.assertAlmostEqual(fractions["SD"], 0.314, places=3)
        self.assertAlmostEqual(worst, 0.0313, places=3)

    def test_country_with_too_little_baseline_is_excluded(self):
        import fetchers.net_bgp_withdrawal as M
        day = self._event_day(28)
        # only 10 days of history for the deep-withdrawal country → no baseline,
        # so it cannot drive the worst-of even though its dip is deepest
        short = self._country_points(4000.0, 0.02, event_day_index=10, days=11)
        deep_day = self._event_day(10)
        good = self._country_points(5000.0, 0.5, event_day_index=28, days=29)
        w_short, drv_short, fr_short = M.aggregate(deep_day, {"SY": short})
        self.assertEqual((w_short, drv_short), (None, None))  # no baseline yet
        w, drv, fr = M.aggregate(day, {"SY": short, "GB": good})
        self.assertEqual(drv, "GB")  # SY has no reading for `day`; GB drives it
        self.assertNotIn("SY", fr)

    def test_anchored_scoring_fires_on_withdrawal_not_on_benign(self):
        import collect
        import fetchers.net_bgp_withdrawal as M
        opts = collect.scoring_attrs(M)
        fires = collect.score_row("2026-01-01", 0.031, "n", "2026-01-01", [], **opts)
        self.assertEqual((fires["trembling"], fires["direction"]), ("1", "down"))
        self.assertAlmostEqual(float(fires["z_score"]), -9.69, places=2)
        benign = collect.score_row("2026-01-01", 0.96, "n", "2026-01-01", [], **opts)
        self.assertEqual(benign["trembling"], "0")  # Gaza-like ~0.96 never fires


class TestAdsbProviderCorroboration(unittest.TestCase):
    """A coverage failure can only lose aircraft, so the max is the fullest view."""

    def _region(self, counts):
        import urllib.parse
        from core import adsb
        # Hosts come from adsb.PROVIDERS itself rather than a hardcoded list, so
        # this test tracks whichever providers are actually configured instead
        # of silently assuming a fixed roster size.
        self.assertEqual(len(counts), len(adsb.PROVIDERS),
                          "one count per currently configured provider")
        by_host = {urllib.parse.urlparse(template).netloc: count
                   for (_, template), count in zip(adsb.PROVIDERS, counts)}

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
        count, note = self._region([300, 800])
        self.assertEqual(count, 800)
        self.assertIn("disagreed", note)

    def test_agreeing_providers_report_the_agreed_level(self):
        count, note = self._region([297, 288])
        self.assertEqual(count, 297)
        self.assertNotIn("disagreed", note)

    def test_a_real_collapse_is_reported_not_suppressed(self):
        # All providers see an empty sky: that is a measurement, not a fault.
        count, note = self._region([4, 5])
        self.assertEqual(count, 5)
        self.assertIn("under floor", note)


if __name__ == "__main__":
    unittest.main()
