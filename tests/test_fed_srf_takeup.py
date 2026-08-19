"""fed_srf_takeup fetcher: the per-day take-up aggregation and the settle-lag are
pure logic. These stub the one network entry point (``_recent``) and read no
committed record, so they are safe in the pre-collect gate.
"""
import datetime
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from fetchers import fed_srf_takeup as srf


def _op(date, otype, amt, method="Full Allotment", term="Overnight"):
    return {"operationDate": date, "operationType": otype,
            "operationMethod": method, "term": term, "totalAmtAccepted": amt}


class TestDailyTakeup(unittest.TestCase):
    def test_sums_am_pm_and_term_repo_drops_reverse_repo(self):
        ops = [
            _op("2025-12-31", "Repo", 60_000_000_000),                       # AM
            _op("2025-12-31", "Repo", 14_600_000_000),                       # PM
            _op("2025-12-31", "Repo", 61_000_000, term="Term"),             # a term SRF op
            _op("2025-12-31", "Reverse Repo", 300_000_000_000,             # RRP — different facility
                method="Fixed Rate"),
            _op("2025-12-30", "Repo", 0),
        ]
        t = srf.daily_takeup(ops)
        self.assertAlmostEqual(t["2025-12-31"], 74661.0, places=0)   # $m, RRP excluded
        self.assertEqual(t["2025-12-30"], 0.0)                       # a real $0 observation

    def test_zero_day_is_present_not_dropped(self):
        t = srf.daily_takeup([_op("2026-08-14", "Repo", 0), _op("2026-08-14", "Repo", 0)])
        self.assertEqual(t["2026-08-14"], 0.0)


class TestSettledTakeup(unittest.TestCase):
    """The shared settle rule: only days strictly before `today` are complete."""

    def test_drops_the_forming_day(self):
        ops = [_op("2026-01-01", "Repo", 5_000_000_000),
               _op("2026-01-02", "Repo", 9_000_000_000)]   # the forming day
        t = srf.settled_takeup(ops, today="2026-01-02")
        self.assertEqual(sorted(t), ["2026-01-01"])         # 01-02 not yet settled
        self.assertEqual(t["2026-01-01"], 5000.0)


class TestFetchDaily(unittest.TestCase):
    def setUp(self):
        self._real = srf._recent
        # UTC, matching the fetcher's settle clock, so these assertions do not
        # depend on the timezone of the machine running the tests
        utc_today = datetime.datetime.now(datetime.timezone.utc).date()
        self.today = utc_today.isoformat()
        self.yesterday = (utc_today - datetime.timedelta(days=1)).isoformat()

    def tearDown(self):
        srf._recent = self._real

    def test_settles_to_latest_complete_day_and_sums(self):
        srf._recent = lambda n: [
            _op(self.yesterday, "Repo", 20_000_000_000),   # AM
            _op(self.yesterday, "Repo", 500_000_000),      # PM
            _op(self.today, "Repo", 999_000_000_000),      # today's forming ops — skipped
        ]
        r = srf.fetch_daily()
        self.assertEqual(r["raw_value"], 20500.0)          # $m, AM+PM of the settled day
        self.assertEqual(r["obs_date"], self.yesterday)    # today is not yet settled

    def test_zero_takeup_day_scores_not_dark(self):
        srf._recent = lambda n: [_op(self.yesterday, "Repo", 0), _op(self.yesterday, "Repo", 0)]
        r = srf.fetch_daily()
        self.assertEqual(r["raw_value"], 0.0)              # a real reading, not None
        self.assertEqual(r["obs_date"], self.yesterday)

    def test_no_settled_day_is_empty(self):
        srf._recent = lambda n: [_op(self.today, "Repo", 1_000_000_000)]  # only a forming day
        r = srf.fetch_daily()
        self.assertIsNone(r["raw_value"])
        self.assertIn("no settled operation day", r["source_note"])

    def test_source_failure_is_empty(self):
        def boom(n):
            raise srf.requests.RequestException("down")
        srf._recent = boom
        r = srf.fetch_daily()
        self.assertIsNone(r["raw_value"])
        self.assertIn("unavailable", r["source_note"])

    def test_malformed_200_shape_degrades_cleanly(self):
        # a 200 whose body lacks a well-formed operations list must yield the
        # module's own stated-empty, not crash out to collect's generic dark row
        srf._recent = lambda n: None
        r = srf.fetch_daily()
        self.assertIsNone(r["raw_value"])
        self.assertIn("unavailable", r["source_note"])


class TestScaleModeWiring(unittest.TestCase):
    """The line opts into anchored scale-mode; the declaration must reach the scorer
    so a genuine scarcity spike fires while routine month-end friction does not."""

    def test_declares_anchor_and_materiality_not_quantum(self):
        self.assertEqual(srf.ANCHOR, 0)
        self.assertEqual(srf.MATERIALITY, 10000)
        self.assertFalse(hasattr(srf, "QUANTUM"))   # the two are mutually exclusive

    def test_scoring_attrs_carries_the_declaration(self):
        import collect
        attrs = collect.scoring_attrs(srf)
        self.assertEqual(attrs["anchor"], 0)
        self.assertEqual(attrs["materiality"], 10000)

    def test_fires_on_scarcity_spike_not_on_month_end_or_zero(self):
        import collect
        attrs = collect.scoring_attrs(srf)
        # anchored: no history needed to score
        spike = collect.score_row("2026-02-17", 30500.0, "", "2026-02-17", [], **attrs)
        self.assertEqual(spike["trembling"], "1")            # $30.5bn -> z=3.05 fires
        self.assertEqual(spike["direction"], "up")
        month_end = collect.score_row("2025-11-28", 24400.0, "", "2025-11-28", [], **attrs)
        self.assertEqual(month_end["trembling"], "0")        # $24.4bn -> z=2.44, a bump
        calm = collect.score_row("2026-08-14", 0.0, "", "2026-08-14", [], **attrs)
        self.assertEqual(calm["trembling"], "0")             # $0 -> z=0, honest calm
        self.assertTrue(calm["z_score"])                     # scored, not blind


if __name__ == "__main__":
    unittest.main()
