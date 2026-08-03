"""Audits of the COMMITTED record — run after the day is committed, never before.

Everything in this file asserts a property of data already in the repository,
which means an upstream surprise — a source shrinking its panel, a seam left by
a seeder — can fail these at any time through no fault of today's code. The
daily workflow therefore runs them AFTER the commit step: a failure raises the
alarm issue, it never blocks collection. Putting any of these into the
pre-collect gate is the configuration this project forbids: one bad committed
day would then abort every subsequent run before it collected anything, and the
snapshot lines have no archive to recover those days from. That is not
hypothetical — the panel test below failed exactly that way the day PortWatch
first served 27 straits, and only the gate/audit split kept the instrument
collecting.

The filename deliberately does not match test_*.py, so the pre-collect gate
(``python -m unittest discover tests``) skips this file; CI runs it explicitly
with ``python -m unittest discover tests -p "audit_*.py"``.
"""
import csv
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tools"))

import replay

# Dates on which the source itself served an incomplete panel, with the missing
# straits named. An entry here is a human acknowledgement: the shortfall was
# investigated and found to be the source's, not a lost page of ours. A NEW
# short date fails the audit until someone looks and either fixes the capture
# or acknowledges it here.
#
# 2026-07-24: PortWatch served 27 straits — no Strait of Hormuz row at all
# (verified by direct single-date query). Absence, not zero: day ~146 of the
# Hormuz closure, and the source stopped saying anything about the strait. The
# fetcher now discloses short panels in source_note.
ACKNOWLEDGED_SHORT = {
    "2026-07-24": {"Strait of Hormuz"},
}


class TestReplayOfTheLiveRecord(unittest.TestCase):
    def test_the_live_record_replays_since_the_declared_stable_date(self):
        """No drift between the collector and the scorer on any committed row."""
        import collect
        drifted = []
        for mod in collect.LINES:
            for date, published, replayed in replay.replay_line(mod):
                if date >= replay.STABLE_SINCE and replay._differs(published, replayed):
                    drifted.append((mod.LINE, date))
        self.assertEqual(drifted, [], f"rows since {replay.STABLE_SINCE} do not replay")


class TestChokepointComponents(unittest.TestCase):
    PATH = os.path.join(ROOT, "data", "components", "chokepoint_breadth.csv")

    def _by_date(self):
        if not os.path.exists(self.PATH):
            self.skipTest("no components recovered yet")
        with open(self.PATH, newline="") as f:
            rows = list(csv.DictReader(f))
        by_date = {}
        for r in rows:
            by_date.setdefault(r["date"], {})[r["component"]] = float(r["value"])
        return by_date

    def test_components_sum_to_something_near_the_scored_total(self):
        """The breakdown must be OF the reading, not of some other quantity."""
        by_date = self._by_date()
        line = os.path.join(ROOT, "data", "chokepoint_breadth.csv")
        with open(line, newline="") as f:
            scored = {r["obs_date"]: float(r["raw_value"])
                      for r in csv.DictReader(f) if r["raw_value"] and r.get("obs_date")}
        checked = 0
        for obs, total in scored.items():
            if obs not in by_date:
                continue
            checked += 1
            self.assertAlmostEqual(
                sum(by_date[obs].values()), total, delta=1.0,
                msg=f"{obs}: components sum to {sum(by_date[obs].values())} "
                    f"but the line recorded {total}")
        self.assertGreater(checked, 100, "too few observations cross-checked")

    def test_every_observation_carries_the_full_panel(self):
        """A short panel and a lost page look identical; both must be loud.

        The panel is the union of every strait ever seen, so a strait the
        source quietly drops keeps being demanded until a human acknowledges
        the absence above with a reason.
        """
        by_date = self._by_date()
        panel = set().union(*(set(v) for v in by_date.values()))
        for date, values in sorted(by_date.items()):
            missing = panel - set(values)
            self.assertEqual(
                missing, ACKNOWLEDGED_SHORT.get(date, set()),
                f"{date}: panel is missing {sorted(missing)} — either the "
                f"source dropped a strait or a page was lost; investigate, "
                f"then fix the capture or acknowledge it in this file")


if __name__ == "__main__":
    unittest.main()
