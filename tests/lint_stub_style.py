"""Enforces ONE stubbing style across the test suite: a swap must go through
``support.stub_requests`` or ``support.stub_attr``, never a hand-rolled
``<name>.<attr> = ...``. A hand-rolled swap has no guaranteed restore, and one
left in place leaks into whatever test runs next, far from its cause — the
dynamic checks in ``tests/test_zz_stub_hygiene.py``'s ``TestNoStubLeaked``
catch such a leak from the outside; this scans for the hand-rolled shape that
causes it, structurally, from source.

What it actually covers: a line of the form ``<name>.<attr> = ...`` where
``<name>`` is bound by a module-level ``import`` or ``from ... import`` in
that same file — the shape a stubbed module or fetcher object always takes.
A swap through a name that is only a local variable (bound inside a
function, not by a module-level import) is outside what this scan can see.

LINT, not gate: a source scan of tests/test_*.py, not a property of the
running instrument, so it runs on push via ``unittest discover tests -p
"lint_*.py"`` (ci.yml's lint job) and is deliberately NOT part of
daily.yml's pre-collect gate — a convention violation here must never cost
an irreplaceable collection day.
"""
import ast
import os
import re
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import support

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
            if not name.startswith("test_"):
                continue
            src = support.read_text(os.path.join(ROOT, "tests", name))
            if _hand_rolls_a_swap(src):
                offenders.append(name)
        self.assertEqual(offenders, [],
                         "use support.stub_requests / support.stub_attr: " + ", ".join(offenders))


if __name__ == "__main__":
    unittest.main()
