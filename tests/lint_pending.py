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
import re
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tools"))

from core import clock

# Imported through the package path, not as a bare ``import pending``: the bare
# form is what the rest of the suite uses, but it only resolves at runtime
# (the sys.path insert above), so a static analyzer reads it as an unresolved
# import. ``tools.pending`` is the same module object either way — pending.py
# takes its own ROOT from ``__file__`` and inserts both paths itself.
from tools import pending  # noqa: E402  (needs the sys.path insert above)

# The three legal ways a bullet can stop being an untracked promise. A CLOSED
# item stays in the block only with a round reference attached (the block's own
# header rule: "Close an item by editing it out with a round reference"), so a
# closure marker that names no round is not legal either.
_TAG_AT_END_RE = re.compile(
    r"\[opened R\d+(?:\.\d+)?\s*·\s*owner R\d+(?:\.\d+)?\s*·\s*"
    r"fires:\s*[^\[\]]+\]\s*$")
_STANDING_RE = re.compile(r"\bstanding\b", re.IGNORECASE)
_CLOSURE_RE = re.compile(r"\b(?:DONE|CLOSED|RESULT)\b[^\n]{0,30}?R\d")


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


class TestEveryBulletIsTrackedOrClosed(unittest.TestCase):
    """Every bullet in the block must END in one of three legal forms.

    The two tests above only see the TAGGED bullets — ``collect_items`` returns
    nothing for an untagged one, so a bare paragraph promising a re-review is
    invisible to them (that is how four closed items and one phantom reference
    outlived their reviews). This asserts the complement over every bullet,
    tagged or not: the bullet ends in a parseable ``[opened R.. · owner R.. ·
    fires: ...]`` tag, OR it carries the word ``standing`` (a rule that never
    fires by construction), OR it is closed with a round reference on its own
    first line. Anything else is an untracked promise: close it, tag it, or
    declare it standing.
    """

    def test_every_pending_bullet_ends_tagged_standing_or_round_closed(self):
        unaccounted = []
        for bullet in pending.block_bullets():
            body = bullet.strip()
            first_line = body.splitlines()[0]
            if (_TAG_AT_END_RE.search(body) or _STANDING_RE.search(body)
                    or _CLOSURE_RE.search(first_line)):
                continue
            unaccounted.append(first_line[:100])
        self.assertEqual(
            unaccounted, [],
            "Pending-block bullet(s) carry no ending tag, no 'standing' marker, "
            "and no round-referenced closure marker — an untracked promise "
            "(tag it, close it with a round reference, or mark it standing): "
            + "; ".join(unaccounted))


if __name__ == "__main__":
    unittest.main()
