"""Push-CI lint over radar.md's Pending block: every ``[opened R.. · owner
R.. · fires: ...]`` tag must fit tools/pending.py's grammar, and neither a
``round`` nor a ``date`` predicate may already be past.

LINT, not gate/audit: a source-and-docs scan (radar.md, never ``data/``), so
it runs on push via ``unittest discover tests -p "lint_*.py"`` (ci.yml's lint
job) and is deliberately NOT part of daily.yml's pre-collect gate — a
mis-tagged pending item must never abort a collection day (see
tests/test_side_channel.py's ``TestGateNeverReadsTheCommittedRecord`` for the
data/-in-the-gate rule this mirrors on the lint side: never read data/ here
either).

Data-dependent predicates (``scored``/``distinct_scored``/``rows_since``) are
NOT evaluated here — they need the committed CSVs, which only
``python tools/pending.py --check`` (tool-side) and tests/audit_registry.py
(post-commit audit) may read. ``round``/``date`` need no data/ at all (the
round index and today's date both come from source/the clock), so this lint
is the right, cheap place to catch those two forms going stale.
"""
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tools"))

from core import clock

import pending


class TestEveryPendingTagParses(unittest.TestCase):
    def test_every_tag_in_the_pending_block_fits_the_grammar(self):
        try:
            items = pending.collect_items()
        except pending.PendingParseError as e:
            self.fail(f"a Pending-block tag does not fit the grammar "
                      f"([opened R<n> · owner R<n> · fires: <predicate>]): {e}")
        # A canary against an over-narrow block scan silently checking nothing.
        self.assertTrue(items, "no tagged pending items were found in "
                         "radar.md's Pending block")


class TestNoRoundOrDateItemIsAlreadyOverdue(unittest.TestCase):
    """Only the two data-independent predicate forms are checked here — see
    the module docstring for why scored/distinct_scored/rows_since belong to
    ``pending.py --check`` and audit_registry.py instead."""

    def test_round_and_date_predicates_have_not_already_fired(self):
        items = pending.collect_items()
        round_now = pending.current_round()
        today = clock.china_today()
        overdue = []
        for item in items:
            if item["kind"] not in ("round", "date"):
                continue  # data-dependent forms are not this lint's job
            pending.evaluate(item, round_now=round_now, today=today)
            if item["fired"]:
                overdue.append((item["label"], item["predicate_text"], item["current"]))
        self.assertEqual(overdue, [],
                          f"pending item(s) already OVERDUE by round/date "
                          f"(close them or re-tag): {overdue}")


if __name__ == "__main__":
    unittest.main()
