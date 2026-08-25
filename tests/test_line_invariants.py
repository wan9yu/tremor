"""Per-line module invariants, checked at the pre-collect gate.

Crash isolation in collect() wraps only ``fetch_daily()`` (collect.py); a bad
module ATTRIBUTE is not caught there. In particular ``normalize.judge`` asserts a
line declares QUANTUM or MATERIALITY but never both — an AssertionError raised in
``score_row`` mid-loop aborts the whole day's run and costs every LATER line its
reading, and several are snapshot lines with no archive. Asserting the invariants
here, on pure logic with no network and no committed record, catches a
misdeclared module before any run.
"""
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import collect


class TestLineInvariants(unittest.TestCase):
    def test_no_line_declares_both_quantum_and_materiality(self):
        # ¬(QUANTUM ∧ MATERIALITY) — most lines declare NEITHER, which is fine;
        # only declaring BOTH trips normalize.judge's exclusivity assert.
        for mod in collect.LINES:
            q = getattr(mod, "QUANTUM", None)
            m = getattr(mod, "MATERIALITY", None)
            self.assertFalse(q is not None and m is not None,
                             f"{mod.LINE} declares both QUANTUM and MATERIALITY")

    def test_every_line_has_an_alarm_direction(self):
        for mod in collect.LINES:
            self.assertIn(getattr(mod, "ANOMALY_DIRECTION", None), ("up", "down"),
                          f"{mod.LINE} has no valid ANOMALY_DIRECTION")

    def test_line_names_are_unique(self):
        names = [mod.LINE for mod in collect.LINES]
        self.assertEqual(len(names), len(set(names)), "duplicate LINE name in collect.LINES")


if __name__ == "__main__":
    unittest.main()
