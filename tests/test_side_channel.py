"""The intraday sampler must stay inert: it measures the instrument, not the world.

If anything in the scoring path ever starts reading it, a diagnostic file becomes
an input to a verdict, and the separation that makes it safe is gone.
"""
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)


class TestSideChannelIsInert(unittest.TestCase):
    SCORING_PATH = ["collect.py", os.path.join("core", "normalize.py"),
                    os.path.join("core", "clock.py")]

    def test_no_scoring_code_reads_the_intraday_file(self):
        for rel in self.SCORING_PATH:
            with open(os.path.join(ROOT, rel)) as f:
                source = f.read()
            # collect.py may NAME the file to exclude it from the mirror; what it
            # must never do is read it or import the sampler.
            self.assertNotIn("read_intraday", source, f"{rel} reads the side channel")
            self.assertNotIn("sample_intraday", source, f"{rel} imports the sampler")

    def test_it_is_excluded_from_the_dashboard_mirror(self):
        """The mirror is an ALLOW-list: a new diagnostic file under data/ stays
        off the dashboard unless someone deliberately serves it."""
        import collect
        self.assertNotIn("intraday.csv", collect.MIRRORED)
        self.assertNotIn("levels.csv", collect.MIRRORED)
        for name in collect.MIRRORED:
            self.assertTrue(name.endswith(".csv"))
        self.assertFalse(
            os.path.exists(os.path.join(ROOT, "docs", "data", "intraday.csv")),
            "the side channel was mirrored into the served data directory")

    def test_the_sampler_writes_only_its_own_file(self):
        with open(os.path.join(ROOT, "tools", "sample_intraday.py")) as f:
            source = f.read()
        self.assertNotIn("write_line", source, "the sampler writes a scored line CSV")
        self.assertNotIn("summary.csv", source, "the sampler touches the summary")
        self.assertNotIn("score_row", source, "the sampler produces a verdict")

    def test_it_samples_only_instantaneous_lines(self):
        """A line whose reading is already a daily aggregate has no intraday spread."""
        sys.path.insert(0, os.path.join(ROOT, "tools"))
        import sample_intraday
        names = {m.LINE for m in sample_intraday.SNAPSHOT_LINES}
        self.assertEqual(names, {"flights", "cnh_cny", "capital_premium"})


if __name__ == "__main__":
    unittest.main()
