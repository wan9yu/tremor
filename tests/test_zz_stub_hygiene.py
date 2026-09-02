"""Named test_zz_* so it runs last: it proves no earlier test leaked a stub.

A swap that is not restored surfaces as a failure in whatever test runs next,
far from its cause. The two DYNAMIC checks below catch the two distinct ways a
`requests` stub can leak, because neither sees the other's failure mode:

- `test_requests_get_is_the_real_one` catches an in-place mutation of the
  shared `requests` module (`requests.get = ...`). Python caches one module
  object per process, so every fetcher's own `requests` name refers to that
  same object; mutating its `.get` in place leaks into all of them at once,
  and this is the only check that can see it — a fetcher module's `requests`
  attribute still `is` the real module, so the other check's `hasattr(...,
  "Session")` stays true regardless.
- `test_fetcher_modules_hold_the_real_requests` catches a fetcher module's
  own `requests` name being replaced outright (`module.requests =
  types.SimpleNamespace(...)`), which never touches the real `requests`
  module and so is invisible to the first check.

Both checks here observe actual leaked STATE after the suite has run, which
is why they stay in the pre-collect gate. The complementary STATIC check —
scanning test source for the hand-rolled swap that would cause such a leak —
is a lint, not a gate check, and lives in tests/lint_stub_style.py instead.
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


if __name__ == "__main__":
    unittest.main()
