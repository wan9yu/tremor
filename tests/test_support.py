"""Dynamic behavior of tests/support.py: workflow-file parsing (cron_hours,
workflow_run_steps) and the stub_attr context manager's restore guarantee.
support.py's stdlib-only REQUIREMENT — the property that keeps it importable
by every gate test before a single row is collected — is a source scan, not
a property of running code, and is checked separately in
tests/lint_support_stdlib.py."""
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


if __name__ == "__main__":
    unittest.main()
