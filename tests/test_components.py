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
import os
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


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


if __name__ == "__main__":
    unittest.main()
