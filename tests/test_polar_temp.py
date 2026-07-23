"""Locks for the polar_temp context line: the vendored climatology and the
anomaly math. The fetch itself is network and is not exercised here; the parsing
and the fixed baseline are."""
import os
import sys
import types
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core import arctic_clim


class TestClimatology(unittest.TestCase):
    def test_365_daily_normals(self):
        self.assertEqual(len(arctic_clim._NORMAL_K), 365)

    def test_values_are_plausible_arctic_kelvin(self):
        # The high Arctic runs roughly -35C (238K) in deep winter to ~+2C (275K)
        # in the melt season; nothing should fall outside a generous envelope.
        self.assertTrue(all(235.0 <= v <= 278.0 for v in arctic_clim._NORMAL_K))

    def test_seasonal_shape(self):
        # Midsummer (day ~196) must be far warmer than midwinter (day ~15).
        self.assertGreater(arctic_clim.normal_k(196), arctic_clim.normal_k(15) + 20)

    def test_day_of_year_bounds(self):
        self.assertEqual(arctic_clim.normal_k(1), arctic_clim._NORMAL_K[0])
        self.assertEqual(arctic_clim.normal_k(365), arctic_clim._NORMAL_K[364])
        # A leap-year day 366 reuses Dec 31 rather than indexing off the end.
        self.assertEqual(arctic_clim.normal_k(366), arctic_clim._NORMAL_K[364])
        self.assertEqual(arctic_clim.normal_k(0), arctic_clim._NORMAL_K[0])


class TestAnomalyParsing(unittest.TestCase):
    def _fetch_with(self, body):
        import fetchers.polar_temp as M
        real = M.requests

        class R:
            status_code = 200
            text = body
        M.requests = types.SimpleNamespace(get=lambda *a, **k: R(),
                                           RequestException=Exception)
        try:
            return M.fetch_daily()
        finally:
            M.requests = real

    def test_reads_last_row_and_computes_anomaly(self):
        # day 203 normal is ~274.36K; a reading of 275.36K is +1.00C.
        normal = arctic_clim.normal_k(203)
        body = f"Date Day Temp\n20260101 1 250.0\n20260722 203 {normal + 1.0:.3f}\n"
        out = self._fetch_with(body)
        self.assertAlmostEqual(out["raw_value"], 1.0, places=2)
        self.assertEqual(out["obs_date"], "2026-07-22")

    def test_a_headerless_or_empty_file_is_dark(self):
        self.assertIsNone(self._fetch_with("Date Day Temp\n")["raw_value"])


if __name__ == "__main__":
    unittest.main()
