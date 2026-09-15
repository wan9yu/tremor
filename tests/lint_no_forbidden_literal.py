"""Enforce hard invariant AGENTS.md §0.1: the forbidden six-letter author-tool
literal (spelled c-l-a-u-d-e, any case) must not appear in any tracked file's
CONTENT, in any tracked FILENAME, or in the tip commit's message / author — the
three vectors the harness can inject it through (a session-URL commit trailer, a
default file name, pasted text).

Lint tier: STDLIB-ONLY. Shells out to `git` (a system binary, not a dependency).
The check pattern is a regex with a bracket break, so this file itself never
spells the contiguous literal — the invariant must not force its own violation.

History is not scanned: a literal already in an old commit cannot be removed
without rewriting history (forbidden by AGENTS.md §0.4), so this guards what is
forward-fixable — the current tree and the commit at HEAD.
"""
import os
import re
import subprocess
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_GREP_RE = "cl[a]ude"                       # regex for `git grep -iE`
_PY_RE = re.compile("cl[a]ude", re.IGNORECASE)   # same, for python-side matching


def _git(*args):
    return subprocess.run(["git", *args], cwd=ROOT,
                          capture_output=True, text=True)


class TestNoForbiddenLiteral(unittest.TestCase):
    def test_no_tracked_file_contains_it(self):
        r = _git("grep", "-iEl", _GREP_RE)
        # git grep: exit 0 = matches found, 1 = clean, >1 = git error.
        self.assertNotEqual(
            r.returncode, 0,
            "forbidden author-tool literal in tracked file content:\n" + r.stdout)

    def test_no_tracked_filename_contains_it(self):
        r = _git("ls-files")
        hits = [p for p in r.stdout.splitlines() if _PY_RE.search(p)]
        self.assertEqual(
            hits, [], "forbidden author-tool literal in tracked filename(s): "
            + ", ".join(hits))

    def test_tip_commit_message_and_author_are_clean(self):
        r = _git("log", "-1", "--format=%B%n%an%n%ae")
        self.assertIsNone(
            _PY_RE.search(r.stdout),
            "forbidden author-tool literal in the HEAD commit message or author "
            "(check for an injected commit trailer)")


if __name__ == "__main__":
    unittest.main()
