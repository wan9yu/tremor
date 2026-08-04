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


class TestGateNeverReadsTheCommittedRecord(unittest.TestCase):
    def test_no_gate_test_touches_the_data_directory(self):
        """test_*.py files gate collection, so none may assert committed data.

        A committed-data assertion in the pre-collect gate blocks every later
        run the day an upstream source surprises it — the configuration this
        project forbids. Record assertions belong in audit_*.py, which runs
        after the commit. (Reading docs/data is allowed: those checks catch
        code-caused mirror leaks, which the gate is exactly for.) This rule
        exists because it was broken twice: the component panel test and the
        control-line canary both sat in the gate reading data/.
        """
        # The rule forbids READING THE RECORD, so it names the ways the record
        # is reached rather than the four letters d-a-t-a. Scanning for the bare
        # word was the first attempt and it was wrong: it fires on any stubbed
        # API response whose JSON envelope happens to be {"data": ...}, which is
        # most of them. A guard with false positives gets weakened or deleted,
        # and this one is load-bearing.
        #
        # This file is excluded from its own scan, and the exclusion is the
        # honest version of the alternative: a guard that must not contain the
        # strings it forbids can only be written by spelling every one of them
        # in pieces, which is unreadable and would itself rot. What is lost is
        # small and checkable by eye — the assertions below touch no record.
        quote = '"'
        forbidden = (
            ", " + quote + "data" + quote,   # a path join into the record dir
            "collect.DATA",                  # the constant itself
            "collect.COMPONENTS",
            "seedlib.read_line",             # loads a line's committed rows
        )
        allowed = quote + "docs" + quote + ", " + quote + "data" + quote
        tests_dir = os.path.dirname(os.path.abspath(__file__))
        myself = os.path.basename(__file__)
        for name in sorted(os.listdir(tests_dir)):
            if not (name.startswith("test_") and name.endswith(".py")):
                continue
            if name == myself:
                continue
            with open(os.path.join(tests_dir, name)) as f:
                src = f.read().replace(allowed, "")   # docs/data is a code check
            for needle in forbidden:
                self.assertNotIn(
                    needle, src,
                    f"{name} reaches the committed record via {needle.strip()} — "
                    f"move that assertion to an audit_*.py file, which runs "
                    f"after the commit")


if __name__ == "__main__":
    unittest.main()
