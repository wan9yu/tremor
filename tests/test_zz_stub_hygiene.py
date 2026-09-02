"""Named test_zz_* so it runs last: it proves no earlier test leaked a stub.

A swap that is not restored surfaces as a failure in whatever test runs next,
far from its cause. One helper with a guaranteed restore, and this sentinel,
make that class of bug impossible to ship.
"""
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import requests


class TestNoStubLeaked(unittest.TestCase):
    def test_requests_get_is_the_real_one(self):
        self.assertEqual(requests.get.__module__.split(".")[0], "requests")

    def test_fetcher_modules_hold_the_real_requests(self):
        import collect
        for mod in collect.LINES:
            real = getattr(mod, "requests", None)
            if real is None:
                continue
            with self.subTest(line=mod.LINE):
                self.assertTrue(hasattr(real, "Session"),
                                f"{mod.LINE} still holds a stubbed requests module")


class TestOneStubbingStyle(unittest.TestCase):
    def test_no_test_file_swaps_an_attribute_by_hand(self):
        offenders = []
        for name in sorted(os.listdir(os.path.join(ROOT, "tests"))):
            if not name.startswith("test_") or name == "test_zz_stub_hygiene.py":
                continue
            src = open(os.path.join(ROOT, "tests", name)).read()
            if "requests = types.SimpleNamespace" in src or ".requests = " in src:
                if "import support" not in src:
                    offenders.append(name)
        self.assertEqual(offenders, [],
                         "use support.stub_requests / support.stub_attr: " + ", ".join(offenders))


if __name__ == "__main__":
    unittest.main()
