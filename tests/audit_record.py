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
import glob
import os
import re
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
# annotations.csv row saying what was found.
ACKNOWLEDGED_SHORT = {
    # PortWatch served 27 straits on these two days — no Strait of Hormuz row
    # at all, verified by direct query — after 9/12/11/10 transits on the four
    # days before. It resumed on obs 07-26 at 3 transits, the lowest reading in
    # the strait's 214-day record. So the absence was TWO DAYS, not a panel
    # change: most likely the source emitting no row for near-zero traffic,
    # which is the reading that matters, because under it a FULL closure is
    # invisible to a 28-strait sum by construction. See annotations 2026-08-05.
    "2026-07-24": {"Strait of Hormuz"},
    "2026-07-25": {"Strait of Hormuz"},
}

# A component the source has stopped serving ALTOGETHER, from the first date it
# went missing: {name: since}. Different from a one-off short day — it says the
# panel itself changed, so the audit stops asking about every subsequent day.
#
# EMPTY, and the way it emptied is the mechanism working. Hormuz was entered
# here on 2026-08-04 after three consecutive absences looked permanent; on
# 2026-08-05 the audit failed in the OTHER direction — obs 07-26 was missing
# nothing while this dict still expected a gap — which is precisely how a
# standing acknowledgement is supposed to be revoked. It was two days, and they
# are recorded above as what they were.
ONGOING_ABSENT = {}


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


# One underlying observation scored on more than one row — the two families
# reach that from OPPOSITE directions (see each below: cnh_cny repeats no
# obs_date, sofr_iorb repeats one), so neither is the general case. These are
# published rows: forward-only keeps them, and the audit acknowledges them by
# name so a NEW double-score fails loudly instead of hiding in the count.
# See annotations 2026-09-02.
ACKNOWLEDGED_DOUBLE_SCORED = {
    # cnh_cny: the vendor re-stamped Friday's frozen legs into the weekend, so
    # obs_date minted a fresh key on every China-Monday collection. Fixed by
    # _session_date (Round 26); these five rows predate the fix.
    ("cnh_cny", "2026-07-27"), ("cnh_cny", "2026-08-03"), ("cnh_cny", "2026-08-10"),
    ("cnh_cny", "2026-08-17"), ("cnh_cny", "2026-08-24"),
    # sofr_iorb_spread: observation 2026-07-01 republished on three consecutive
    # days (the Independence-Day weekend: Sat 07-04, Sun 07-05, and the
    # holiday-lagged Mon 07-06) before obs-dedup shipped. The 07-04 row minted
    # an alarm-direction tremble (z 5.396) from a republication.
    ("sofr_iorb_spread", "2026-07-04"), ("sofr_iorb_spread", "2026-07-05"),
    ("sofr_iorb_spread", "2026-07-06"),
}


# Pre-``_session_date`` Sunday rows that REPEATED the preceding Saturday row's
# frozen legs verbatim, before obs_date existed to name them by observation —
# the same weekend-repeat family as the five ACKNOWLEDGED_DOUBLE_SCORED cnh_cny
# dates above. 07-05/07-12/07-19 published a z off that repeat; 06-28 was still
# ``warming-up``. Held as a closed list, not a derived property: since the
# leg-desync guard shipped, a weekend row carries no legs at all, so a fifth
# member cannot arise unless that guard is removed — and a property would
# silently absorb exactly that regression, where an enumerated list fails loudly.
# Proven by ``test_leg_repeat_exemptions_are_pre_obs_date_sundays``.
# See annotations 2026-09-02.
LEG_REPEAT_EXEMPT = ("2026-06-28", "2026-07-05", "2026-07-12", "2026-07-19")


class TestNoObservationScoredTwice(unittest.TestCase):
    def test_every_line_scores_each_observation_once(self):
        import collect
        offenders = []
        for mod in collect.LINES:
            seen = {}
            for row in collect._read_rows(os.path.join(collect.DATA, mod.LINE + ".csv")):
                obs = row.get("obs_date") or ""
                if not obs or row.get("status") != "scoring":
                    continue
                if obs in seen and (mod.LINE, row["date"]) not in ACKNOWLEDGED_DOUBLE_SCORED:
                    offenders.append(f"{mod.LINE} {row['date']} re-scores obs {obs} "
                                     f"(first scored {seen[obs]})")
                seen.setdefault(obs, row["date"])
        self.assertEqual(offenders, [], "\n".join(offenders))


class TestCnhCnyLegIdentity(unittest.TestCase):
    """A weekday onshore HOLIDAY re-stamp carries a weekday stamp and so slips
    past the session snap. Identical consecutive leg pairs are the only
    signature that catches it; on this line the check has no false positives."""

    def test_no_unacknowledged_identical_leg_pair(self):
        import collect
        rows = collect._read_rows(os.path.join(collect.DATA, "cnh_cny.csv"))
        legs = re.compile(r"USDCNH ([\d.]+) − USDCNY ([\d.]+)")
        offenders, prev = [], None
        for row in rows:
            m = legs.search(row.get("source_note") or "")
            if not m:
                prev = None
                continue
            pair = m.groups()
            if pair == prev and ("cnh_cny", row["date"]) not in ACKNOWLEDGED_DOUBLE_SCORED \
                    and row["date"] not in LEG_REPEAT_EXEMPT:
                offenders.append(f"cnh_cny {row['date']} repeats the previous row's legs {pair}")
            prev = pair
        self.assertEqual(offenders, [], "\n".join(offenders))

    def test_leg_repeat_exemptions_are_pre_obs_date_sundays(self):
        """Every exempted date must really have the property that exempts it.

        An exemption list with no prover is a place a REAL future defect can be
        parked silently. The sibling check does this for ACKNOWLEDGED_DOUBLE_SCORED;
        this does it for LEG_REPEAT_EXEMPT. It also makes a whole class of comment
        error impossible: the justification beside the constant once said "Saturday
        rows" for four Sunday dates, and prose cannot catch that — an assertion can.
        """
        import collect
        rows = {r["date"]: r for r
                in collect._read_rows(os.path.join(collect.DATA, "cnh_cny.csv"))}
        for date in LEG_REPEAT_EXEMPT:
            with self.subTest(date=date):
                row = rows.get(date)
                self.assertIsNotNone(row, f"{date} is exempted but not in the record")
                self.assertEqual(datetime.date.fromisoformat(date).weekday(), 6,
                                 f"{date} is exempted as a Sunday repeat but is not a Sunday")
                self.assertEqual((row.get("obs_date") or "").strip(), "",
                                 f"{date} is exempted as predating obs_date, but carries one")

    def test_no_unacknowledged_weekend_obs_date(self):
        """The direct signature of the pre-fix bug this class is named for.

        ``_session_date`` (Round 26) always snaps a Saturday/Sunday leg stamp
        back to its Friday session, so a SCORED row whose obs_date itself
        falls on a weekend is impossible after the fix — it is exactly what
        the un-snapped vendor re-stamp used to write. Checked directly against
        the real record: this signature names the five acknowledged rows and
        nothing else, so it is what actually makes the acknowledgement above
        provable rather than a documentation-only list.
        """
        import collect
        rows = collect._read_rows(os.path.join(collect.DATA, "cnh_cny.csv"))
        offenders = []
        for row in rows:
            obs = row.get("obs_date") or ""
            if not obs or row.get("status") != "scoring":
                continue
            if datetime.date.fromisoformat(obs).weekday() >= 5 \
                    and ("cnh_cny", row["date"]) not in ACKNOWLEDGED_DOUBLE_SCORED:
                offenders.append(f"cnh_cny {row['date']} scores obs {obs}, a weekend date "
                                 f"— _session_date should have snapped this to Friday")
        self.assertEqual(offenders, [], "\n".join(offenders))


class TestArchivesAreNotSeededOutput(unittest.TestCase):
    """An archive is the OLD series. A file that is a byte-prefix of its live
    line is the seeded output written over the archive it was meant to preserve
    — which is how two v1 archives were lost twelve minutes after creation.

    A *_preseed archive legitimately equals the live file when the seed appended
    nothing, so only *_v1 archives are held to this.
    """

    def test_no_v1_archive_is_a_prefix_of_its_live_line(self):
        import collect
        offenders = []
        for path in glob.glob(os.path.join(collect.DATA, "archive", "*_v1.csv")):
            line = os.path.basename(path)[: -len("_v1.csv")]
            live = os.path.join(collect.DATA, line + ".csv")
            if not os.path.exists(live):
                continue
            with open(path) as f:
                archived = f.read().splitlines()
            with open(live) as f:
                head = f.read().splitlines()[: len(archived)]
            if archived == head:
                offenders.append(f"{os.path.basename(path)} is a byte-prefix of {line}.csv")
        self.assertEqual(offenders, [], "\n".join(offenders))


if __name__ == "__main__":
    unittest.main()
