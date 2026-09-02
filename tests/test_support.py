"""tests/support.py must stay stdlib-only: every gate test imports it, and a
non-stdlib import at module scope would raise ImportError in daily.yml's gate
step, before any row is collected."""
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import support


class TestWorkflowParsing(unittest.TestCase):
    def test_cron_hours_reads_the_daily_schedule(self):
        hours = support.cron_hours(os.path.join(ROOT, ".github/workflows/daily.yml"))
        self.assertEqual(hours, [18])

    def test_run_steps_include_the_sleep_block(self):
        steps = support.workflow_run_steps(os.path.join(ROOT, ".github/workflows/daily.yml"))
        self.assertTrue(any("22:30:00" in s for s in steps))


class TestStubAttr(unittest.TestCase):
    def test_restores_the_original_value(self):
        ns = type("N", (), {})()
        ns.x = 1
        with support.stub_attr(ns, "x", 2):
            self.assertEqual(ns.x, 2)
        self.assertEqual(ns.x, 1)

    def test_restores_even_when_the_block_raises(self):
        ns = type("N", (), {})()
        ns.x = 1
        with self.assertRaises(ValueError):
            with support.stub_attr(ns, "x", 2):
                raise ValueError("boom")
        self.assertEqual(ns.x, 1)


class TestStdlibOnly(unittest.TestCase):
    def test_support_imports_nothing_outside_the_stdlib(self):
        src = open(os.path.join(ROOT, "tests/support.py")).read()
        for banned in ("import yaml", "import requests", "import numpy", "import scipy"):
            self.assertNotIn(banned, src, "support.py must stay stdlib-only")


if __name__ == "__main__":
    unittest.main()
