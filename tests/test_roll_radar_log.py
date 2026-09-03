"""GATE test for tools/roll_radar_log.py — the log-roll tool T16 ships ahead
of the actual roll (radar-log.md crosses its self-set 2,000-line threshold
around R27, at 1,835 lines / 107 lines-per-round today).

Exercises the tool's pure functions against radar-log.md's SOURCE text (the
doc itself, not ``data/`` — reading it is a source-and-docs scan like
tests/lint_registry.py's round-index-parity lint, not a property of the
running instrument) and checks the guarantees the tool exists to make:

  (a) byte-identity — ``verify_write_plan`` reconstructs radar-log.md's
      original text out of the ACTUAL strings the tool would write to each
      file (not out of self-consistent slices of one string, which recombine
      for any input by Python slicing semantics and would prove nothing —
      see roll_radar_log.py's module docstring). ``TestByteIdentityCatchesRealCorruption``
      below hands it a deliberately corrupted write-plan string and checks
      it is refused, which is what makes this property non-tautological.
  (b) round coverage — ``verify_round_coverage`` re-parses ``### Round``
      headers straight out of the write-plan strings and checks the archive
      and the remainder are a clean, non-overlapping, order-preserving
      partition of every header in the original (rounds 1 through 25.1
      today), with the archive holding 1-19 and the remainder holding 20+.
  (c) placement — a partition can be clean and complete yet still land at
      the WRONG boundary (round 20 ending up archived, say); coverage alone
      does not catch that, so ``verify_round_coverage`` also asserts every
      archived round's floor is below ``split_round`` and every remaining
      round's floor is at or above it. ``TestRoundCoverageCatchesRealCorruption``
      proves this with a plan built at the wrong split point.

Nothing here writes a file: every check below is exercised in-memory, and
the one test that drives the CLI does so with ``--check``, which by the
tool's own contract never touches disk — asserted directly rather than
trusted, and against ``main``'s RETURNED message (``main`` itself never
prints — see roll_radar_log.py — so no stdout leaks into the gate console).
Neither radar-log.md nor radar-log-1.md is modified by this module.
"""
import os
import re
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tools"))

import support

import roll_radar_log

LOG_PATH = os.path.join(ROOT, "radar-log.md")

# An independent re-parse of radar-log.md's round headers — deliberately not
# reusing roll_radar_log.ROUND_HEADER, so the coverage checks below test the
# tool against an independently-derived expectation rather than its own
# regex. Matches tests/lint_registry.py's `_ROUND_LOG_HEADER` exactly.
_ROUND_HEADER = re.compile(r'^###\s+Round\s+([0-9]+(?:\.[0-9]+)?)\b', re.M)


def _plan_pieces(original=None):
    """Builds the real write-plan pieces for radar-log.md (read_text(LOG_PATH)
    unless ``original`` is given) without invoking any verification — the one
    place the read -> compute_split -> build_archive_file -> build_remaining_file
    pipeline lives, shared by every TestCase below that needs a real plan to
    corrupt or inspect."""
    if original is None:
        original = support.read_text(LOG_PATH)
    result = roll_radar_log.compute_split(original)
    archive_full, archive_added = roll_radar_log.build_archive_file(result)
    live_full, live_preamble, live_pointer = roll_radar_log.build_remaining_file(result)
    return original, result, archive_full, archive_added, live_full, live_preamble, live_pointer


class TestPlanSplitOnTheRealFile(unittest.TestCase):
    """The end-to-end pipeline, uncorrupted, against today's radar-log.md."""

    def test_plan_split_succeeds_and_covers_rounds_1_through_19_vs_20_plus(self):
        text = support.read_text(LOG_PATH)
        result, archive_full, live_full = roll_radar_log.plan_split(text)

        archive_floors = {int(r.split(".")[0]) for r in result.archive_rounds}
        remaining_floors = {int(r.split(".")[0]) for r in result.remaining_rounds}
        self.assertEqual(archive_floors, set(range(1, 20)))
        self.assertGreaterEqual(min(remaining_floors), 20)
        self.assertTrue(archive_full)
        self.assertTrue(live_full)

    def test_archive_and_remaining_rounds_equal_every_header_independently_parsed(self):
        text = support.read_text(LOG_PATH)
        all_rounds = _ROUND_HEADER.findall(text)
        self.assertTrue(all_rounds,
                         "no '### Round' headers found in radar-log.md")

        result, _, _ = roll_radar_log.plan_split(text)

        self.assertEqual(result.archive_rounds + result.remaining_rounds,
                          all_rounds,
                          "archive + remaining rounds must equal every "
                          "'### Round' header, in order")
        self.assertEqual(
            set(result.archive_rounds) & set(result.remaining_rounds), set(),
            "a round must not appear on both sides of the split")


class TestByteIdentityCatchesRealCorruption(unittest.TestCase):
    """Proves verify_write_plan is not a tautology: it is handed a write-plan
    string that has been corrupted the way a REAL bug in
    build_archive_file/build_remaining_file could corrupt it — not a
    corrupted INPUT re-sliced consistently, which the tool's earlier,
    defective version would have let straight through (see roll_radar_log.py's
    module docstring for that proof) — and must raise, refusing to write.
    """

    def setUp(self):
        (self.original, _, self.archive_full, self.archive_added,
         self.live_full, self.live_preamble, self.live_pointer) = _plan_pieces()
        # Sanity: the real, uncorrupted write plan must pass both checks —
        # if this raises, every test below is moot.
        roll_radar_log.verify_write_plan(
            self.original, self.archive_full, self.archive_added,
            self.live_full, self.live_preamble, self.live_pointer)
        roll_radar_log.verify_round_coverage(
            self.original, self.archive_full, self.live_full)

    def test_the_uncorrupted_write_plan_passes_both_checks(self):
        # No exception raised in setUp() already proves this; a named test
        # makes the property visible in the test list on its own, not only
        # as a side effect of every other test's setUp succeeding.
        roll_radar_log.verify_write_plan(
            self.original, self.archive_full, self.archive_added,
            self.live_full, self.live_preamble, self.live_pointer)

    def test_a_line_dropped_from_the_archive_write_plan_is_refused(self):
        # Simulates a bug in build_archive_file that drops a line somewhere
        # in the MIDDLE of what would be written to radar-log-1.md.
        lines = self.archive_full.splitlines(keepends=True)
        mid = len(lines) // 2
        corrupted = "".join(lines[:mid] + lines[mid + 1:])
        self.assertNotEqual(corrupted, self.archive_full)
        with self.assertRaises(AssertionError):
            roll_radar_log.verify_write_plan(
                self.original, corrupted, self.archive_added,
                self.live_full, self.live_preamble, self.live_pointer)

    def test_a_line_duplicated_in_the_live_write_plan_is_refused(self):
        # Simulates a bug in build_remaining_file that duplicates a line
        # somewhere in the MIDDLE of what would be written to radar-log.md.
        lines = self.live_full.splitlines(keepends=True)
        mid = len(lines) // 2
        corrupted = "".join(lines[:mid] + [lines[mid]] + lines[mid:])
        self.assertNotEqual(corrupted, self.live_full)
        with self.assertRaises(AssertionError):
            roll_radar_log.verify_write_plan(
                self.original, self.archive_full, self.archive_added,
                corrupted, self.live_preamble, self.live_pointer)

    def test_a_pointer_leaking_into_the_archive_round_region_is_refused(self):
        # Simulates the live file's pointer sentence leaking into the
        # archive file's round content instead of staying in radar-log.md.
        corrupted = self.archive_full + self.live_pointer
        with self.assertRaises(AssertionError):
            roll_radar_log.verify_write_plan(
                self.original, corrupted, self.archive_added,
                self.live_full, self.live_preamble, self.live_pointer)

    def test_swapping_the_two_bodies_is_refused(self):
        # Simulates the worst-case bug: the archive and live bodies swapped
        # between the two output files.
        with self.assertRaises(AssertionError):
            roll_radar_log.verify_write_plan(
                self.original, self.live_full, self.archive_added,
                self.archive_full, self.live_preamble, self.live_pointer)


class TestRoundCoverageCatchesRealCorruption(unittest.TestCase):
    """Same principle as TestByteIdentityCatchesRealCorruption, for
    verify_round_coverage specifically: a round header duplicated across
    both write-plan files, dropped from the write plan, or a boundary that
    is a complete-and-clean partition at the WRONG round, must be refused.
    """

    def setUp(self):
        (self.original, self.result, self.archive_full, _,
         self.live_full, _, _) = _plan_pieces()

    def test_a_round_header_duplicated_across_both_files_is_refused(self):
        # Round 19's header genuinely lives in self.archive_full already;
        # leaking a copy of it into the live write-plan text simulates a
        # boundary bug that put the same round on both sides of the split.
        leaked = "\n### Round 19 — leaked duplicate\n"
        corrupted_live = leaked + self.live_full
        with self.assertRaises(AssertionError):
            roll_radar_log.verify_round_coverage(
                self.original, self.archive_full, corrupted_live)

    def test_a_round_header_dropped_from_the_write_plan_is_refused(self):
        # Simulates a bug that silently drops round 20's header text (and
        # therefore its whole section) while building the live write-plan.
        corrupted_live = self.live_full.replace("### Round 20", "Round 20", 1)
        with self.assertRaises(AssertionError):
            roll_radar_log.verify_round_coverage(
                self.original, self.archive_full, corrupted_live)

    def test_a_split_boundary_off_by_one_round_is_refused(self):
        # Simulates compute_split's `>= split_round` floor comparison
        # landing one round early: round 20 ends up on the ARCHIVE side
        # instead of live. Built with split_round=21, so this plan really
        # is a complete, non-overlapping partition of every round — byte
        # identity and the coverage/overlap checks all pass it — only the
        # placement guard (checked against the tool's own default
        # SPLIT_ROUND=20, not the 21 this plan used) catches the wrong
        # boundary. This is the exact gap a review found: coverage alone is
        # side-agnostic.
        off_by_one_result = roll_radar_log.compute_split(self.original, split_round=21)
        archive_full, _ = roll_radar_log.build_archive_file(off_by_one_result)
        live_full, _, _ = roll_radar_log.build_remaining_file(off_by_one_result)
        self.assertIn("20", off_by_one_result.archive_rounds,
                       "test setup error: round 20 must land in the archive "
                       "side for this to exercise the off-by-one case")
        with self.assertRaises(AssertionError):
            roll_radar_log.verify_round_coverage(self.original, archive_full, live_full)


class TestCheckModeIsADryRun(unittest.TestCase):
    """Drives roll_radar_log.py's own ``--check`` CLI path (in-process, no
    subprocess) against the real radar-log.md and confirms it is provably a
    dry run — the property T16's brief requires be testable. Asserts on
    ``main``'s RETURNED ``(message, exit_code)`` — ``main`` itself never
    prints, so this produces no stdout leak into the gate console."""

    def test_check_mode_leaves_radar_log_untouched_and_writes_no_archive(self):
        before = support.read_text(LOG_PATH)
        self.assertFalse(
            os.path.exists(roll_radar_log.ARCHIVE_PATH),
            "radar-log-1.md must not exist — the roll has not happened yet")

        message, rc = roll_radar_log.main(["--check"])

        self.assertEqual(rc, 0)
        self.assertIn("--check: no file written", message)
        after = support.read_text(LOG_PATH)
        self.assertEqual(before, after, "radar-log.md changed under --check")
        self.assertFalse(os.path.exists(roll_radar_log.ARCHIVE_PATH),
                          "--check must not write radar-log-1.md")


if __name__ == "__main__":
    unittest.main()
