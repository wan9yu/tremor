"""Named test_zz_* so it runs last: it proves no earlier test leaked a stub.

A swap that is not restored surfaces as a failure in whatever test runs next,
far from its cause. Two dynamic checks below catch the two distinct ways a
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

Neither dynamic check can see a leak in an attribute that is not `requests`
(for example `srf._recent`); `test_no_test_file_swaps_an_attribute_by_hand`
below guards that structurally instead. What it actually covers: a line of the
form `<name>.<attr> = ...` where `<name>` is bound by a module-level `import`
or `from ... import` in that same file — the shape a stubbed module or fetcher
object always takes. It requires that swap to route through
`support.stub_attr` instead, whose own `try`/`finally` is what actually
guarantees the restore. A swap through a name that is only a local variable
(bound inside a function, not by a module-level import) is outside what this
scan can see.
"""
import ast
import os
import re
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


# A hand-rolled swap of `<name>.<attr>` — `requests.get = ...`, `sw.settled =
# ...`, `srf._recent = ...`. Anchored to the start of the line so it does not
# match inside a string or a mid-line expression.
_ATTR_SWAP = re.compile(r'^\s*([A-Za-z_]\w*)\.\w+\s*=(?!=)')


def _module_level_import_names(src):
    """Names bound by a module-level ``import``/``from ... import`` in ``src``.

    Only these can be the stubbed module or fetcher object a swap targets;
    a same-named local (a function parameter, a loop variable, an ordinary
    instance via ``self``) is never one of them, so restricting to these
    names is what keeps the scan below from matching locals like
    `m.fetch_daily = ...` or `ns.x = 1`.
    """
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return set()
    names = set()
    for node in tree.body:  # module level only, not inside a function/class
        if isinstance(node, ast.Import):
            for alias in node.names:
                names.add((alias.asname or alias.name).split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                names.add(alias.asname or alias.name)
    return names


def _hand_rolls_a_swap(src):
    imported = _module_level_import_names(src)
    return any(m.group(1) in imported
              for m in (_ATTR_SWAP.match(line) for line in src.splitlines())
              if m)


class TestOneStubbingStyle(unittest.TestCase):
    def test_no_test_file_swaps_an_attribute_by_hand(self):
        offenders = []
        for name in sorted(os.listdir(os.path.join(ROOT, "tests"))):
            if not name.startswith("test_") or name == "test_zz_stub_hygiene.py":
                continue
            with open(os.path.join(ROOT, "tests", name), encoding="utf-8") as fh:
                src = fh.read()
            if _hand_rolls_a_swap(src):
                offenders.append(name)
        self.assertEqual(offenders, [],
                         "use support.stub_requests / support.stub_attr: " + ", ".join(offenders))


if __name__ == "__main__":
    unittest.main()
