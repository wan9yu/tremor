"""Every seeder must route through seedlib: it is the one place that merges
against the published record, refuses to drop a row, and archives without
clobbering. Reads source text only, so it is safe in the pre-collect gate."""
import glob
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

SEEDERS = sorted(glob.glob(os.path.join(ROOT, "tools", "seed_*.py")))


class TestSeedersRouteThroughSeedlib(unittest.TestCase):
    def test_there_are_seeders_to_check(self):
        self.assertGreaterEqual(len(SEEDERS), 8)

    def test_every_seeder_calls_run_seed(self):
        for path in SEEDERS:
            with self.subTest(seeder=os.path.basename(path)):
                with open(path) as fh:
                    src = fh.read()
                # The call itself, not a docstring mention: seed_polar.py,
                # seed_fred.py and seed_ioda.py all name "seedlib.run_seed" in
                # prose, which a bare substring check on "run_seed" cannot
                # distinguish from the real call.
                self.assertIn("seedlib.run_seed(", src)

    def test_no_seeder_writes_a_line_directly(self):
        for path in SEEDERS:
            with open(path) as fh:
                src = fh.read()
            with self.subTest(seeder=os.path.basename(path)):
                self.assertNotIn("collect.write_line", src)
                self.assertNotIn("score_row", src)
                self.assertNotIn("shutil.copy2", src)


if __name__ == "__main__":
    unittest.main()
