"""Component capture must stay diagnostic: it records, it never judges.

The scalar a line stores is an aggregate of something richer that was already
fetched. Storing the breakdown is how a future question ("which strait?", "which
region?", "which provider?") stops requiring a time machine. But the moment
anything scored reads it, a diagnostic file becomes an input to a verdict and the
separation that makes it safe is gone.

Only CODE properties live here, so this file may gate collection. Assertions
about the committed component DATA (panel wholeness, sums matching the scored
totals) live in audit_record.py, which runs after the commit — committed data
can be broken by the source, and a gate it can fail would halt collection.
"""
import inspect
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)


class TestComponentsAreDiagnosticOnly(unittest.TestCase):
    def test_no_scoring_code_reads_the_component_files(self):
        """`normalize.py` and `replay.py` must not even NAME a breakdown; the
        scoring modules' only component read is `write_components` merging its
        own file, pinned by the next-but-one test."""
        for rel in (os.path.join("core", "normalize.py"),
                    os.path.join("tools", "replay.py")):
            with open(os.path.join(ROOT, rel)) as f:
                source = f.read()
            self.assertNotIn("components", source,
                             f"{rel} — the scorer must not see the breakdown")

    def test_the_scoring_decision_takes_no_component_input(self):
        """The AGENTS.md seam, machine-bound: a verdict is computed from the
        scalar and its prior rows, never from a breakdown. A `components`
        parameter on either scoring entry point would put a diagnostic file in
        the signature of the function that decides a tremble, so it reds here
        even if the body ignored it."""
        import collect
        from core import normalize
        for fn in (collect.score_row, normalize.judge):
            self.assertNotIn(
                "components", inspect.signature(fn).parameters,
                f"{fn.__module__}.{fn.__name__} accepts a components breakdown")

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


if __name__ == "__main__":
    unittest.main()
