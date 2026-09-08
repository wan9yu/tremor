"""GATE test for tools/roll_radar_log.py — the log-roll tool that split
radar-log.md's early rounds into radar-log-1.md at R29, once the live log
crossed its self-set 2,000-line threshold at R28 (2,036 lines, ~107
lines-per-round).

Exercises the tool's pure functions against a SYNTHETIC in-module fixture
(``FIXTURE`` below, split at ``FIXTURE_SPLIT``) rather than the live log, so
the suite reads no radar-log*.md file and stays stable across this roll and
every future one — the tool's guarantees are properties of its own logic, not
of whatever rounds the live log happens to hold today. The fixture is a
6-line preamble followed by rounds 1, 1.1, 2, 3, 3.2, 4, 5, split at round 4:
rounds with an integer floor below 4 archive (1, 1.1, 2, 3, 3.2), rounds at or
above it remain (4, 5). It checks the guarantees the tool exists to make:

  (a) byte-identity — ``verify_write_plan`` reconstructs the split source's
      original text out of the ACTUAL strings the tool would write to each
      file (not out of self-consistent slices of one string, which recombine
      for any input by Python slicing semantics and would prove nothing —
      see roll_radar_log.py's module docstring). ``TestByteIdentityCatchesRealCorruption``
      below hands it a deliberately corrupted write-plan string and checks
      it is refused, which is what makes this property non-tautological.
  (b) round coverage — ``verify_round_coverage`` re-parses ``### Round``
      headers straight out of the write-plan strings and checks the archive
      and the remainder are a clean, non-overlapping, order-preserving
      partition of every header in the original, with the archive holding the
      rounds whose floor is below ``FIXTURE_SPLIT`` and the remainder the rest.
  (c) placement — a partition can be clean and complete yet still land at
      the WRONG boundary (round 4 ending up archived, say); coverage alone
      does not catch that, so ``verify_round_coverage`` also asserts every
      archived round's floor is below ``split_round`` and every remaining
      round's floor is at or above it. ``TestRoundCoverageCatchesRealCorruption``
      proves this with a plan built at the wrong split point.

Nothing here writes to the repo: every check below is exercised in-memory,
and the two tests that drive the CLI seed a ``TemporaryDirectory`` with the
fixture and drive ``main`` against it — one asserts ``--check`` never touches
disk (the tool's dry-run contract), the other that the write path REFUSES to
overwrite an already-existing archive. Both assert against ``main``'s RETURNED
``(message, exit_code)`` (``main`` itself never prints — see roll_radar_log.py
— so no stdout leaks into the gate console). Neither radar-log.md nor
radar-log-1.md is read or modified by this module.
"""
import os
import re
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tools"))

import support

import roll_radar_log

# A synthetic stand-in for radar-log.md, used by every TestCase below so the
# suite never reads the live log. Six preamble lines (mirroring radar-log.md's
# own preamble length), then one `### Round N` section per round. Split at
# FIXTURE_SPLIT: rounds 1, 1.1, 2, 3, 3.2 archive (floor < 4); rounds 4, 5
# remain (floor >= 4).
FIXTURE_SPLIT = 4
FIXTURE = """\
# fixture calibration log — synthetic

A synthetic stand-in for the calibration log, used only by this test module so
the suite reads no live log file and stays stable across every future roll.
Six preamble lines, then one `### Round N` section per round below.

### Round 1 — 2026-01-01 (seed)
- first body line of round one
- second body line of round one

### Round 1.1 — 2026-01-01 (sub-round of one)
- body of round one point one

### Round 2 — 2026-01-02 (second)
- body of round two
- more body of round two

### Round 3 — 2026-01-03 (third)
- body of round three

### Round 3.2 — 2026-01-03 (sub-round of three)
- body of round three point two

### Round 4 — 2026-01-04 (fourth)
- body of round four
- more body of round four

### Round 5 — 2026-01-05 (fifth)
- body of round five
- last body line of round five
"""

# An independent re-parse of the fixture's round headers — deliberately not
# reusing roll_radar_log.ROUND_HEADER, so the coverage checks below test the
# tool against an independently-derived expectation rather than its own
# regex. Matches tests/lint_registry.py's `_ROUND_LOG_HEADER` exactly.
_ROUND_HEADER = re.compile(r'^###\s+Round\s+([0-9]+(?:\.[0-9]+)?)\b', re.M)


def _plan_pieces(original=None):
    """Builds the real write-plan pieces for the fixture (``FIXTURE`` unless
    ``original`` is given) without invoking any verification — the one place
    the compute_split -> build_archive_file -> build_remaining_file pipeline
    lives, shared by every TestCase below that needs a real plan to corrupt or
    inspect. Passes ``FIXTURE_SPLIT`` explicitly — the tool has no default
    split round."""
    if original is None:
        original = FIXTURE
    result = roll_radar_log.compute_split(original, FIXTURE_SPLIT)
    archive_full, archive_added = roll_radar_log.build_archive_file(result)
    live_full, live_preamble, live_pointer = roll_radar_log.build_remaining_file(result)
    return original, result, archive_full, archive_added, live_full, live_preamble, live_pointer


class TestPlanSplitOnTheFixture(unittest.TestCase):
    """The end-to-end pipeline, uncorrupted, against the synthetic fixture."""

    def test_plan_split_succeeds_and_covers_the_archive_floors_vs_the_remainder(self):
        result, archive_full, live_full = roll_radar_log.plan_split(FIXTURE, FIXTURE_SPLIT)

        archive_floors = {int(r.split(".")[0]) for r in result.archive_rounds}
        remaining_floors = {int(r.split(".")[0]) for r in result.remaining_rounds}
        self.assertEqual(archive_floors, {1, 2, 3})
        self.assertGreaterEqual(min(remaining_floors), FIXTURE_SPLIT)
        self.assertTrue(archive_full)
        self.assertTrue(live_full)

    def test_archive_and_remaining_rounds_equal_every_header_independently_parsed(self):
        all_rounds = _ROUND_HEADER.findall(FIXTURE)
        self.assertTrue(all_rounds,
                         "no '### Round' headers found in the fixture")

        result, _, _ = roll_radar_log.plan_split(FIXTURE, FIXTURE_SPLIT)

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
            self.original, self.archive_full, self.live_full, FIXTURE_SPLIT)

    def test_the_uncorrupted_write_plan_passes_both_checks(self):
        # No exception raised in setUp() already proves this; a named test
        # makes the property visible in the test list on its own, not only
        # as a side effect of every other test's setUp succeeding.
        roll_radar_log.verify_write_plan(
            self.original, self.archive_full, self.archive_added,
            self.live_full, self.live_preamble, self.live_pointer)

    def test_a_line_dropped_from_the_archive_write_plan_is_refused(self):
        # Simulates a bug in build_archive_file that drops a line somewhere
        # in the MIDDLE of what would be written to the archive file.
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
        # Round 3's header genuinely lives in self.archive_full already;
        # leaking a copy of it into the live write-plan text simulates a
        # boundary bug that put the same round on both sides of the split.
        leaked = "\n### Round 3 — leaked duplicate\n"
        corrupted_live = leaked + self.live_full
        with self.assertRaises(AssertionError):
            roll_radar_log.verify_round_coverage(
                self.original, self.archive_full, corrupted_live, FIXTURE_SPLIT)

    def test_a_round_header_dropped_from_the_write_plan_is_refused(self):
        # Simulates a bug that silently drops round 4's header text (and
        # therefore its whole section) while building the live write-plan.
        corrupted_live = self.live_full.replace("### Round 4", "Round 4", 1)
        with self.assertRaises(AssertionError):
            roll_radar_log.verify_round_coverage(
                self.original, self.archive_full, corrupted_live, FIXTURE_SPLIT)

    def test_a_split_boundary_off_by_one_round_is_refused(self):
        # Simulates compute_split's `>= split_round` floor comparison
        # landing one round early: round 4 ends up on the ARCHIVE side
        # instead of live. Built with split_round=FIXTURE_SPLIT+1, so this
        # plan really is a complete, non-overlapping partition of every round
        # — byte identity and the coverage/overlap checks all pass it — only
        # the placement guard (checked against FIXTURE_SPLIT, not the +1 this
        # plan used) catches the wrong boundary. This is the exact gap a
        # review found: coverage alone is side-agnostic.
        off_by_one_result = roll_radar_log.compute_split(
            self.original, split_round=FIXTURE_SPLIT + 1)
        archive_full, _ = roll_radar_log.build_archive_file(off_by_one_result)
        live_full, _, _ = roll_radar_log.build_remaining_file(off_by_one_result)
        self.assertIn(str(FIXTURE_SPLIT), off_by_one_result.archive_rounds,
                       "test setup error: round 4 must land in the archive "
                       "side for this to exercise the off-by-one case")
        with self.assertRaises(AssertionError):
            roll_radar_log.verify_round_coverage(
                self.original, archive_full, live_full, FIXTURE_SPLIT)


class TestCheckModeIsADryRun(unittest.TestCase):
    """Drives roll_radar_log.py's own ``--check`` CLI path (in-process, no
    subprocess) against a ``TemporaryDirectory`` seeded with the fixture and
    confirms it is provably a dry run — the property the tool's brief requires
    be testable. Asserts on ``main``'s RETURNED ``(message, exit_code)`` —
    ``main`` itself never prints, so this produces no stdout leak into the
    gate console, and nothing in the repo tree is read or written."""

    def test_check_mode_leaves_the_log_untouched_and_writes_no_archive(self):
        with tempfile.TemporaryDirectory() as tmp:
            log_path = os.path.join(tmp, "radar-log.md")
            archive_path = os.path.join(tmp, "radar-log-1.md")
            with open(log_path, "w", encoding="utf-8") as fh:
                fh.write(FIXTURE)
            before = support.read_text(log_path)
            self.assertFalse(os.path.exists(archive_path),
                             "the archive must not exist before the roll")

            message, rc = roll_radar_log.main(
                ["--check", "--split-round", str(FIXTURE_SPLIT)],
                log_path=log_path, archive_path=archive_path)

            self.assertEqual(rc, 0)
            self.assertIn("--check: no file written", message)
            after = support.read_text(log_path)
            self.assertEqual(before, after, "the log changed under --check")
            self.assertFalse(os.path.exists(archive_path),
                              "--check must not write the archive")


class TestOverwriteGuardRefusesAnExistingArchive(unittest.TestCase):
    """The write path must never silently clobber a previous roll's archive.
    Drives ``main`` (no ``--check``) against a ``TemporaryDirectory`` where the
    archive file ALREADY exists, and confirms it refuses (rc==1) and leaves
    BOTH the log and the pre-existing archive byte-for-byte untouched — the one
    genuinely-new safety behavior this tool gained at R29."""

    def test_write_is_refused_when_the_archive_already_exists(self):
        with tempfile.TemporaryDirectory() as tmp:
            log_path = os.path.join(tmp, "radar-log.md")
            archive_path = os.path.join(tmp, "radar-log-1.md")
            with open(log_path, "w", encoding="utf-8") as fh:
                fh.write(FIXTURE)
            sentinel = "# a previous roll's archive — must NOT be overwritten\n"
            with open(archive_path, "w", encoding="utf-8") as fh:
                fh.write(sentinel)

            log_before = support.read_text(log_path)
            archive_before = support.read_text(archive_path)

            message, rc = roll_radar_log.main(
                ["--split-round", str(FIXTURE_SPLIT)],
                log_path=log_path, archive_path=archive_path)

            self.assertEqual(rc, 1, "an existing archive must make the roll refuse")
            self.assertIn("already exists", message)
            self.assertEqual(support.read_text(log_path), log_before,
                              "the log must be untouched when the roll is refused")
            self.assertEqual(support.read_text(archive_path), archive_before,
                              "the pre-existing archive must not be overwritten")
            self.assertEqual(support.read_text(archive_path), sentinel,
                              "the archive must still hold its original bytes")


if __name__ == "__main__":
    unittest.main()
