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

Replay of the committed record is NOT here: ``tools/replay.py --check`` is that
audit's single owner (the workflow step before this one), and it checks a
superset of what a duplicate test could — per-row drift AND the summary
re-derivation. One owner, one O(n^2) replay per day.
"""
import csv
import datetime
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import test_control  # the astronomy lives with the control line's logic tests
from fetchers import control_daylength as control

# ONE-OFF short days: {date: {missing components}}. An entry here is a human
# acknowledgement that the shortfall was investigated and found to be the
# source's, not a lost page of ours, and each must have a matching
# annotations.csv row saying what was found. Empty today — the only short day
# the record has seen turned out to be permanent and lives below.
ACKNOWLEDGED_SHORT = {}

# A strait the source has stopped serving ALTOGETHER, from the first date it
# went missing. This is not the same acknowledgement as a one-off short day: it
# says the panel itself has changed and the change has been investigated, so the
# audit stops asking about every subsequent day. Removing an entry from here is
# how the question gets reopened.
#
# Strait of Hormuz, from 2026-07-24: verified against PortWatch directly — obs
# 07-24, 07-25 and 07-26 carry no Hormuz row at all, after 9/12/11/10 transits
# on the four days before. Day ~146 of a closure the level layer has held open
# since April. Whether the source is serving zero-traffic as no-row or has
# dropped the strait cannot be told from the response, and the difference
# matters: under the first reading a FULL closure is invisible to the sum by
# construction. See annotations 2026-08-04.
ONGOING_ABSENT = {
    "Strait of Hormuz": "2026-07-24",
}


def _expected_missing(date, panel):
    """Which components the record accepts as absent on ``date``."""
    missing = set(ACKNOWLEDGED_SHORT.get(date, set()))
    for name, since in ONGOING_ABSENT.items():
        if name in panel and date >= since:
            missing.add(name)
    return missing


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
                missing, _expected_missing(date, panel),
                f"{date}: panel is missing {sorted(missing)} — either the "
                f"source dropped a strait or a page was lost; investigate, "
                f"then fix the capture or acknowledge it in this file")


class TestControlLineRecord(unittest.TestCase):
    """The control line's committed rows, verified against astronomy.

    Moved here from test_control.py: a canary tripping is exactly when
    collection must keep running and the alarm must fire, so these cannot sit
    in the pre-collect gate. The astronomy itself (and the canary's
    sensitivity proofs) stay with the logic tests.
    """

    def _rows(self):
        import collect
        rows = [r for r in collect._read_rows(
                    os.path.join(ROOT, "data", "control_daylength.csv"))
                if r["raw_value"]]
        if not rows:
            self.skipTest("control line has no data yet")
        return rows

    def test_every_row_matches_the_astronomy_for_the_day_it_claims(self):
        """The canary, at a tolerance that can actually catch a one-day slip.

        Rows carrying obs_date are checked to within a minute; rows written
        before obs_date was recorded fall back to the row date at a loose
        tolerance, and are honestly weaker.
        """
        for r in self._rows():
            if r.get("obs_date"):
                day, tol, which = datetime.date.fromisoformat(r["obs_date"]), 0.017, "obs_date"
            else:
                day, tol, which = datetime.date.fromisoformat(r["date"]), 0.25, "row date (no obs_date)"
            expected = test_control.astronomical_day_length_h(control.LAT, day)
            actual = float(r["raw_value"]) / 3600.0
            self.assertLess(
                abs(actual - expected), tol,
                f"{r['date']}: recorded {actual:.4f}h but its {which} {day} implies "
                f"{expected:.4f}h — the pipeline mishandled a date")

    def test_the_row_describes_a_day_close_to_when_it_was_collected(self):
        """obs_date must track the collection date; a drift means a stuck fetch."""
        for r in self._rows():
            if not r.get("obs_date"):
                continue
            gap = (datetime.date.fromisoformat(r["date"])
                   - datetime.date.fromisoformat(r["obs_date"])).days
            self.assertIn(gap, (0, 1),
                          f"{r['date']}: describes {r['obs_date']}, {gap} days adrift")

    def test_consecutive_rows_move_by_a_physically_possible_amount(self):
        """Catches a row overwritten by a run from a different day."""
        rows = self._rows()
        for prev, cur in zip(rows, rows[1:]):
            days = (datetime.date.fromisoformat(cur["date"])
                    - datetime.date.fromisoformat(prev["date"])).days
            jump = abs(float(cur["raw_value"]) - float(prev["raw_value"])) / 3600.0
            # This latitude gains/loses at most ~4.5 min a day, even at equinox.
            self.assertLess(jump, 0.1 * max(days, 1) + 0.05,
                            f"{prev['date']} -> {cur['date']}: {jump:.3f}h in {days} day(s)")


if __name__ == "__main__":
    unittest.main()
