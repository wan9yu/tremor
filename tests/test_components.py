"""Component capture must stay diagnostic: it records, it never judges.

The scalar a line stores is an aggregate of something richer that was already
fetched. Storing the breakdown is how a future question ("which strait?", "which
region?", "which provider?") stops requiring a time machine. But the moment
anything scored reads it, a diagnostic file becomes an input to a verdict and the
separation that makes it safe is gone.
"""
import csv
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import collect


class TestComponentsAreDiagnosticOnly(unittest.TestCase):
    def test_no_scoring_code_reads_the_component_files(self):
        for rel in (os.path.join("core", "normalize.py"),):
            with open(os.path.join(ROOT, rel)) as f:
                source = f.read()
            self.assertNotIn("components", source,
                             f"{rel} — the scorer must not see the breakdown")

    def test_components_never_reach_the_dashboard(self):
        served = os.path.join(ROOT, "docs", "data")
        self.assertFalse(os.path.exists(os.path.join(served, "components")),
                         "the breakdown was mirrored into the served directory")

    def test_a_component_write_does_not_touch_the_scored_row(self):
        """write_components must be incapable of altering a line CSV."""
        with open(os.path.join(ROOT, "collect.py")) as f:
            source = f.read()
        body = source.split("def write_components")[1].split("\ndef ")[0]
        self.assertNotIn("score_row", body)
        self.assertNotIn("LINE_HEADER", body)
        self.assertIn("COMPONENT_HEADER", body)


class TestRecoveredComponents(unittest.TestCase):
    PATH = os.path.join(ROOT, "data", "components", "chokepoint_breadth.csv")

    def _rows(self):
        if not os.path.exists(self.PATH):
            self.skipTest("no components recovered yet")
        with open(self.PATH, newline="") as f:
            return list(csv.DictReader(f))

    def test_components_sum_to_something_near_the_scored_total(self):
        """The breakdown must be OF the reading, not of some other quantity."""
        rows = self._rows()
        by_date = {}
        for r in rows:
            by_date.setdefault(r["date"], {})[r["component"]] = float(r["value"])
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
        rows = self._rows()
        by_date = {}
        for r in rows:
            by_date.setdefault(r["date"], set()).add(r["component"])
        sizes = {len(v) for v in by_date.values()}
        self.assertEqual(sizes, {28},
                         f"observations carry differing panel sizes: {sorted(sizes)}")


if __name__ == "__main__":
    unittest.main()
