"""The machine-lean panel serves the same-day classifier verdict to the
dashboard, from OUTSIDE the scoring path.

A firing tier-1 line (trembling, in its own alarm direction) is a bare
resonance=1 on the dashboard today; for net_outages, tools/reconcile_net_outages.py
already knows how to tell a real event from a synchronized ping-only
common-mode artifact (R23/R27), but only as a human-run, round-time tool. This
reporter is the served version -- and, like tools/stuck_panel.py, it must stay
outside the scoring path (tests/test_side_channel.py) and never touch the
network in its pure half. These tests exercise only build_panel with synthetic
rows and a stub classify -- no network, no data/ read -- so they are safe in
the pre-collect gate.
"""
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tools"))

import lean_panel


class _Mod:
    """A synthetic stand-in for a tier-1 fetcher module -- build_panel needs
    only ``.LINE`` and ``.ANOMALY_DIRECTION`` off it."""

    def __init__(self, line, direction):
        self.LINE = line
        self.ANOMALY_DIRECTION = direction


NET = _Mod("net_outages", "up")
FLIGHTS = _Mod("flights", "down")
TIER1 = [NET, FLIGHTS]


def _row(date, trembling, direction, obs_date=""):
    return {"date": date, "trembling": trembling, "direction": direction, "obs_date": obs_date}


def _stub_classify(calls):
    """Records every (line_id, obs_date) it is called with and hands back a
    fixed, recognizable lean/evidence pair -- proves build_panel passes the
    classifier's output straight through without touching it."""
    def classify(line_id, obs_date):
        calls.append((line_id, obs_date))
        return "STUB-LEAN", f"STUB-EVIDENCE for {line_id}@{obs_date}"
    return classify


class TestBuildPanel(unittest.TestCase):
    def test_firing_tier1_rows_emit_oldest_first(self):
        summary_rows = [{"date": d} for d in ("2026-08-24", "2026-09-04", "2026-09-05")]
        line_rows_by_id = {
            "net_outages": [
                _row("2026-08-24", "1", "up", obs_date="2026-08-22"),
                _row("2026-09-04", "1", "up", obs_date="2026-09-02"),
                _row("2026-09-05", "0", "up"),        # calm today -- does not fire
            ],
            "flights": [
                _row("2026-08-24", "0", "down"),
                _row("2026-09-04", "0", "down"),
                _row("2026-09-05", "1", "down"),      # fires today, no obs_date on the row
            ],
        }
        calls = []
        out = lean_panel.build_panel(summary_rows, line_rows_by_id, TIER1, _stub_classify(calls))
        self.assertEqual(
            [(r["date"], r["line"]) for r in out],
            [("2026-08-24", "net_outages"),
             ("2026-09-04", "net_outages"),
             ("2026-09-05", "flights")])
        # obs_date (the settled-window date), not the collection date, reaches classify()
        self.assertIn(("net_outages", "2026-08-22"), calls)
        self.assertIn(("net_outages", "2026-09-02"), calls)
        # no obs_date on the flights row -> falls back to the collection date
        self.assertIn(("flights", "2026-09-05"), calls)
        # the stub's lean/evidence pass straight through
        self.assertTrue(all(r["lean"] == "STUB-LEAN" for r in out))
        self.assertEqual(out[0]["evidence"], "STUB-EVIDENCE for net_outages@2026-08-22")

    def test_same_day_multiple_firing_lines_preserve_tier1_order(self):
        summary_rows = [{"date": "2026-09-05"}]
        line_rows_by_id = {
            "net_outages": [_row("2026-09-05", "1", "up")],
            "flights": [_row("2026-09-05", "1", "down")],
        }
        out = lean_panel.build_panel(summary_rows, line_rows_by_id, TIER1, _stub_classify([]))
        self.assertEqual([r["line"] for r in out], ["net_outages", "flights"])

    def test_other_direction_does_not_fire(self):
        # trembling, but the "wrong" way for this line's declared alarm
        # direction, must not be mistaken for the alarm
        summary_rows = [{"date": "2026-09-05"}]
        line_rows_by_id = {"net_outages": [_row("2026-09-05", "1", "down")]}
        out = lean_panel.build_panel(summary_rows, line_rows_by_id, [NET], _stub_classify([]))
        self.assertEqual(out, [])

    def test_calm_row_does_not_fire(self):
        summary_rows = [{"date": "2026-09-05"}]
        line_rows_by_id = {"net_outages": [_row("2026-09-05", "0", "up")]}
        out = lean_panel.build_panel(summary_rows, line_rows_by_id, [NET], _stub_classify([]))
        self.assertEqual(out, [])

    def test_a_line_outside_tier1_is_never_consulted(self):
        # a firing, direction-matched row on a line the caller left out of
        # tier1 (main() feeds it only tier-1 modules; a tier-2 line would
        # never appear there) must not fire -- the builder trusts its caller
        # for tier, it does not re-derive it
        summary_rows = [{"date": "2026-09-05"}]
        line_rows_by_id = {
            "net_outages": [_row("2026-09-05", "0", "up")],
            "chokepoint": [_row("2026-09-05", "1", "down")],
        }
        out = lean_panel.build_panel(summary_rows, line_rows_by_id, [NET], _stub_classify([]))
        self.assertEqual(out, [])

    def test_a_line_row_outside_the_committed_record_does_not_fire(self):
        # net_outages fires the day after the latest date summary.csv has
        # committed -- a line's own CSV can run ahead of the summary; only
        # committed days are walked, so this row is never looked up
        summary_rows = [{"date": "2026-09-04"}]
        line_rows_by_id = {"net_outages": [
            _row("2026-09-04", "0", "up"),
            _row("2026-09-05", "1", "up"),
        ]}
        out = lean_panel.build_panel(summary_rows, line_rows_by_id, [NET], _stub_classify([]))
        self.assertEqual(out, [])

    def test_empty(self):
        self.assertEqual(lean_panel.build_panel([], {}, TIER1, _stub_classify([])), [])


if __name__ == "__main__":
    unittest.main()
