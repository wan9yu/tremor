"""GATE: the common-mode classifier in tools/reconcile_net_outages.py.

Pure logic over synthetic IODA events — never touches the network or the record,
so it belongs in the gate. The classifier is what turns "15 countries trembled,
count is stable" into "this is a synchronized ping-only common-mode artifact,
adjudicate" (the 2026-09-04 case the count-only tripwire missed). These tests pin
the three tests it rests on: a synchronized batch, ping-slash24-only, big enough.
"""
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from tools import reconcile_net_outages as R

BASE = 1_788_300_000  # an arbitrary epoch second; only the deltas matter


def ev(country, datasource, start):
    return {"country": country, "datasource": datasource, "start": start}


def ping_cluster(countries, step_s, start=BASE):
    """One ping-slash24 event per country, onsets ``step_s`` apart."""
    return [ev(c, "ping-slash24", start + i * step_s) for i, c in enumerate(countries)]


EIGHT = ["Australia", "Cambodia", "Fiji", "Indonesia",
         "Japan", "Myanmar", "New Zealand", "Thailand"]


class TestCommonModeClassifier(unittest.TestCase):
    def test_synchronized_ping_only_batch_is_common_mode(self):
        # eight countries onset within ~7 min, ping-slash24 only — the 2026-09-04 shape
        out = R.classify_common_mode(ping_cluster(EIGHT, 60))
        self.assertEqual(out["verdict"], "common-mode")
        self.assertEqual(out["sync_batch"], 8)
        self.assertEqual(out["sync_ping_only"], 8)
        self.assertEqual(out["corroborated"], 0)

    def test_bgp_corroboration_in_the_batch_is_not_common_mode(self):
        # same synchronized batch, but three members also withdraw routes / show
        # telescope traffic — a real event corroborates, so the share drops below 0.8
        events = ping_cluster(EIGHT, 60) + [
            ev("Australia", "bgp", BASE), ev("Japan", "bgp", BASE),
            ev("Indonesia", "merit-nt", BASE)]
        out = R.classify_common_mode(events)
        self.assertEqual(out["verdict"], "ok")
        self.assertEqual(out["corroborated"], 3)
        self.assertEqual(out["sync_ping_only"], 5)  # 8 in batch, 3 corroborated

    def test_staggered_onsets_are_not_common_mode(self):
        # eight ping-only countries but 30 min apart — no window holds >= 5 at once
        out = R.classify_common_mode(ping_cluster(EIGHT, 1800))
        self.assertEqual(out["verdict"], "ok")
        self.assertEqual(out["sync_batch"], 1)

    def test_too_few_countries_is_not_common_mode(self):
        out = R.classify_common_mode(ping_cluster(EIGHT[:4], 60))  # 4 < sync_min (5)
        self.assertEqual(out["verdict"], "ok")

    def test_chronic_background_does_not_trip_it(self):
        # two always-on ping-only outages plus a real corroborated one — no burst
        events = [ev("Cape Verde", "ping-slash24", BASE),
                  ev("Tunisia", "ping-slash24", BASE + 40_000),
                  ev("Iraq", "ping-slash24", BASE + 3_000), ev("Iraq", "bgp", BASE + 3_000)]
        out = R.classify_common_mode(events)
        self.assertEqual(out["verdict"], "ok")

    def test_densest_window_is_chosen_among_scatter(self):
        # a 6-country synchronized burst buried among earlier scattered onsets
        scatter = [ev(f"X{i}", "ping-slash24", BASE + i * 5000) for i in range(3)]
        burst = ping_cluster(["A", "B", "C", "D", "E", "F"], 90, start=BASE + 100_000)
        out = R.classify_common_mode(scatter + burst)
        self.assertEqual(out["verdict"], "common-mode")
        self.assertEqual(out["sync_batch"], 6)

    def test_no_ping_events_is_ok(self):
        out = R.classify_common_mode([ev("Iraq", "bgp", BASE)])
        self.assertEqual(out["verdict"], "ok")
        self.assertEqual(out["ping_countries"], 0)

    def test_empty_is_ok(self):
        self.assertEqual(R.classify_common_mode([])["verdict"], "ok")


if __name__ == "__main__":
    unittest.main()
