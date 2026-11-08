"""The replay tool is the record's own auditor; lock what it must detect.

Only the tool's LOGIC is tested here, so this file may gate collection. The
actual replay of the committed record lives in audit_record.py and runs after
the commit: committed rows can fail to replay for reasons no new code caused,
and a gate they can fail would halt collection.
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools"))

import collect
import replay


def _summary_row(date, unusual=None, method=None):
    """A minimal summary row for the re-derivation tests: the three ledger
    counts start at zero, and the two forward-only cells are omitted unless
    asked for."""
    row = {"date": date, "trembling_count": "0", "dark_count": "0", "blind_count": "0"}
    if unusual is not None:
        row["unusual_count"] = unusual
    if method is not None:
        row["count_method"] = method
    return row


class TestSummaryReDerivation(unittest.TestCase):
    """The summary's ledger counts and its forward-only display count both
    re-derive from the replayed rows.

    `unusual_count`/`count_method` are a schema extension: rows before
    `collect.UNUSUAL_SINCE` may leave them empty, while a row at or after it
    must carry them and agree with the replay -- so a collector that stops
    writing the displayed count is red rather than silently tolerated.
    """

    BEFORE = "2026-09-10"      # >= replay.STABLE_SINCE, < collect.UNUSUAL_SINCE
    AFTER = collect.UNUSUAL_SINCE

    def _mismatches(self, rows, unusual_now=None):
        return replay.summary_mismatches(rows, {}, unusual_now or {}, {})

    def test_a_pre_cutover_row_may_leave_the_cells_empty(self):
        self.assertEqual(self._mismatches([_summary_row(self.BEFORE)]), [])

    def test_a_cutover_row_must_carry_both_cells(self):
        found = self._mismatches([_summary_row(self.AFTER)])
        self.assertEqual([sorted(stored) for _, stored, _ in found],
                         [["unusual_count"], ["count_method"]])

    def test_the_displayed_count_must_match_the_replay(self):
        row = _summary_row(self.AFTER, unusual="1", method=collect.COUNT_METHOD)
        self.assertEqual(self._mismatches([row], {self.AFTER: ["flights"]}), [])
        row = _summary_row(self.AFTER, unusual="2", method=collect.COUNT_METHOD)
        self.assertEqual(len(self._mismatches([row], {self.AFTER: ["flights"]})), 1)

    def test_a_pre_cutover_row_with_a_cell_is_still_checked(self):
        row = _summary_row(self.BEFORE, unusual="5", method=collect.COUNT_METHOD)
        self.assertEqual(len(self._mismatches([row])), 1)

    def test_a_corrupt_cell_is_reported_not_raised(self):
        row = _summary_row(self.AFTER, unusual="not-a-number", method=collect.COUNT_METHOD)
        found = self._mismatches([row])
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0][1], {"unusual_count": "not-a-number"})


class TestReplay(unittest.TestCase):
    def test_a_verdict_change_is_detected(self):
        pub = {"z_score": "-2.695", "trembling": "0", "direction": "down", "status": "scoring"}
        same = dict(pub)
        self.assertFalse(replay._differs(pub, same))
        for field, other in (("z_score", "-3.014"), ("trembling", "1"),
                             ("direction", "up"), ("status", "stale")):
            changed = dict(pub, **{field: other})
            self.assertTrue(replay._differs(pub, changed), f"{field} change not detected")

    def test_prose_is_not_part_of_the_verdict(self):
        """source_note is a human note; rewording it must not read as drift."""
        pub = {"z_score": "1.0", "trembling": "0", "direction": "up", "status": "scoring",
               "source_note": "one wording"}
        other = dict(pub, source_note="a different wording")
        self.assertFalse(replay._differs(pub, other))


if __name__ == "__main__":
    unittest.main()
