"""tests/support.py must stay stdlib-only: every gate test imports it, and a
non-stdlib import at module scope would raise ImportError before a single row
is collected.

LINT, not gate: checking this is itself a source scan (parsing support.py's
own imports and checking each root against the interpreter's stdlib
manifest), not a property of the running instrument, so it runs on push via
``unittest discover tests -p "lint_*.py"`` (ci.yml's lint job) rather than
inside daily.yml's pre-collect gate — a convention violation here must never
cost an irreplaceable collection day. (The REQUIREMENT is still enforced
structurally regardless: every gate test imports support.py directly, so a
non-stdlib import there still fails the gate immediately via ImportError —
this lint only gives that failure a clear, dedicated reason on push, before
it can ever reach daily.yml.)
"""
import ast
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import support


class TestStdlibOnly(unittest.TestCase):
    def test_support_imports_nothing_outside_the_stdlib(self):
        # A denylist of banned names (the previous form of this check) can
        # only ever catch imports someone thought to list — `import pandas`
        # or `from yaml import safe_load` both passed it silently. Parsing
        # the actual imports and checking each root against the interpreter's
        # own stdlib manifest catches any non-stdlib import, named or not.
        src = support.read_text(os.path.join(ROOT, "tests/support.py"))
        tree = ast.parse(src)
        roots = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    roots.add(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom):
                if node.level == 0 and node.module:
                    roots.add(node.module.split(".")[0])
        non_stdlib = sorted(roots - sys.stdlib_module_names)
        self.assertEqual(non_stdlib, [], "support.py must stay stdlib-only")


if __name__ == "__main__":
    unittest.main()
