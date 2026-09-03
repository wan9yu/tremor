"""Push-CI lint over every GitHub Actions workflow file: a stdlib structural
sanity scan, a shellcheck of every ``run:`` block, and source-vs-source shape
assertions the workflows must hold (concurrency groups distinct where
present, daily.yml's gate-then-commit-then-audit step order, ci.yml's
gate/lint split, which requirements file each schedule installs). Asserts
T7's calibration.yml shape and the P0 ci.yml gate/lint split.

STDLIB ONLY, deliberately no ``import yaml``: ci.yml's lint job (the job
this file itself runs under) installs NOTHING, so a non-stdlib import here
would ImportError before a single check ran. tests/support.py's
``workflow_run_steps`` already established the pattern this file extends —
see its own docstring ("Deliberately a regex and not a YAML parse..."). So
"the YAML parses" below is a pragmatic structural sanity scan (no tabs,
consistent indentation, required top-level keys present via text scan), not
a real parse — strict parse-validation is delegated to GitHub Actions itself
and the dev env.

LINT, not gate: a source scan of .github/workflows (never data/), not a
property of the running instrument, so it runs on push via ``unittest
discover tests -p "lint_*.py"`` (ci.yml's lint job) and is deliberately NOT
part of daily.yml's pre-collect gate — a workflow-file typo here must never
cost an irreplaceable collection day.
"""
import os
import re
import subprocess
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import support

WORKFLOWS_DIR = os.path.join(ROOT, ".github", "workflows")


def _workflow_files():
    """Every workflow file's basename under .github/workflows, sorted."""
    return sorted(f for f in os.listdir(WORKFLOWS_DIR)
                  if f.endswith((".yml", ".yaml")))


def _path(name):
    return os.path.join(WORKFLOWS_DIR, name)


_REQUIRED_TOP_LEVEL_KEYS = ("on:", "jobs:")


def _structural_sanity_errors(text):
    """A pragmatic stdlib structural scan — NOT a real YAML parse (see the
    module docstring). Flags a tab anywhere (YAML forbids tabs for
    indentation), any non-blank/non-comment line whose leading-space count
    is odd (every workflow in this repo is 2-space indented, so an odd
    indent is a strong corruption signal), and a missing required top-level
    ``on:``/``jobs:`` key. Good enough to catch a stray tab or a mis-pasted
    block before it reaches GitHub Actions' own real parser."""
    errors = []
    if "\t" in text:
        errors.append("contains a tab character (YAML forbids tabs for indentation)")
    for i, line in enumerate(text.splitlines(), 1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        indent = len(line) - len(line.lstrip(" "))
        if indent % 2 != 0:
            errors.append(f"line {i}: odd indentation ({indent} spaces): {line.strip()[:40]!r}")
    for key in _REQUIRED_TOP_LEVEL_KEYS:
        if not re.search(rf"(?m)^{re.escape(key)}", text):
            errors.append(f"missing required top-level key {key!r}")
    return errors


_BLOCK_SCALAR_INDICATORS = ("|", "|-", "|+", ">", ">-", ">+")


def _shell_text(step):
    """The actual shell text of one ``support.workflow_run_steps`` block,
    with the YAML block-scalar indicator line stripped off. A multi-line
    ``run: |`` step's first extracted line is a bare ``|`` (the remainder of
    the ``run:`` line) — that indicator is YAML syntax, not shell, and would
    fail ``sh -n`` on every multi-line step even though the script itself is
    fine. A single-line step (``run: pip install ...``) has no such line and
    passes through unchanged."""
    lines = step.splitlines()
    if lines and lines[0].strip() in _BLOCK_SCALAR_INDICATORS:
        return "\n".join(lines[1:])
    return step


def _job_block(text, job_name):
    """The raw text of one job definition inside a workflow's ``jobs:``
    section — from its own 2-space-indented ``<name>:`` line up to (but not
    including) the next sibling job at the same indent, or EOF. A text scan,
    not a real YAML parse (see the module docstring); good enough to tell
    ci.yml's ``gate`` and ``lint`` jobs apart when checking which one
    installs what."""
    lines = text.splitlines()
    start = next((i for i, line in enumerate(lines)
                  if re.match(rf"^  {re.escape(job_name)}:\s*$", line)), None)
    if start is None:
        return None
    end = next((j for j in range(start + 1, len(lines))
                if re.match(r"^  \S", lines[j])), len(lines))
    return "\n".join(lines[start:end])


class TestWorkflowsAreDiscovered(unittest.TestCase):
    def test_all_known_workflows_are_found(self):
        # A canary against an over-narrow directory listing silently
        # checking nothing.
        self.assertEqual(_workflow_files(),
                          ["calibration.yml", "ci.yml", "daily.yml", "intraday.yml"])


class TestWorkflowsPassAStructuralSanityScan(unittest.TestCase):
    """Every workflow passes the pragmatic stdlib scan of
    ``_structural_sanity_errors`` — deliberately not a real YAML parse (see
    the module docstring)."""

    def test_every_workflow_is_structurally_sane(self):
        for name in _workflow_files():
            with self.subTest(workflow=name):
                text = support.read_text(_path(name))
                errors = _structural_sanity_errors(text)
                self.assertEqual(errors, [], f"{name}: {errors}")


class TestRunBlocksAreShellClean(unittest.TestCase):
    """``sh -n`` every ``run:`` block ``support.workflow_run_steps``
    extracts — a syntax-only check; nothing in any block actually runs."""

    def test_every_run_block_parses_as_shell(self):
        checked = 0
        for name in _workflow_files():
            steps = support.workflow_run_steps(_path(name))
            for i, step in enumerate(steps):
                text = _shell_text(step)
                proc = subprocess.run(["sh", "-n", "-c", text],
                                       capture_output=True, text=True)
                checked += 1
                with self.subTest(workflow=name, step=i):
                    self.assertEqual(proc.returncode, 0,
                                      f"{name} run-block {i} failed `sh -n`: {proc.stderr}")
        # A canary against workflow_run_steps silently finding nothing to check.
        self.assertGreaterEqual(checked, 20)


class TestConcurrencyGroupsAreDistinctWherePresent(unittest.TestCase):
    """Every workflow that declares a ``concurrency:`` group must not share
    that group's name with another workflow's — a shared group would queue
    two unrelated workflows behind each other. ci.yml legitimately declares
    none (its push and pull_request runs are meant to overlap), so this only
    checks the workflows that DO declare one."""

    def test_groups_are_pairwise_distinct(self):
        groups = {}
        for name in _workflow_files():
            text = support.read_text(_path(name))
            m = re.search(r"^\s*group:\s*(\S+)", text, re.M)
            if m:
                groups[name] = m.group(1)
        # A canary: calibration/daily/intraday must all be found with a group.
        expected = {"calibration.yml", "daily.yml", "intraday.yml"}
        self.assertEqual(set(groups) & expected, expected)
        names = list(groups.values())
        self.assertEqual(len(names), len(set(names)),
                          f"duplicate concurrency group name(s) across workflows: {groups}")

    def test_ci_yml_declares_no_concurrency_group(self):
        text = support.read_text(_path("ci.yml"))
        self.assertIsNone(re.search(r"^concurrency:", text, re.M),
                           "ci.yml legitimately has no concurrency group — "
                           "its push and pull_request runs are meant to overlap")


class TestDailyStepOrderIsGateCommitAudit(unittest.TestCase):
    """daily.yml must run the pre-collect gate, THEN commit the day, THEN
    audit the committed record — verified AFTER committing, never before
    (see daily.yml's own "VERIFY AFTER COMMITTING, NEVER BEFORE" comment): a
    gate failure aborts before any row is written, but an audit failure must
    never be able to cost the day."""

    def test_gate_precedes_commit_precedes_audits(self):
        steps = support.workflow_run_steps(_path("daily.yml"))

        def first(predicate):
            return next((i for i, s in enumerate(steps) if predicate(s)), None)

        # The pre-collect gate — plain `unittest discover tests`, not the
        # audit_*.py suite that reuses the same "unittest discover tests"
        # words with a `-p` filter appended.
        gate = first(lambda s: "unittest discover tests" in s and "-p" not in s)
        commit = first(lambda s: "ci_push.sh" in s)
        replay = first(lambda s: "replay.py --check" in s)
        audit = first(lambda s: 'discover tests -p "audit_*.py"' in s)
        render = first(lambda s: "render_smoke.js" in s)

        self.assertIsNotNone(gate, "no pre-collect gate step (`unittest discover tests`) found")
        self.assertIsNotNone(commit, "no commit step (`ci_push.sh`) found")
        self.assertIsNotNone(replay, "no replay --check audit step found")
        self.assertIsNotNone(audit, "no audit_*.py audit step found")
        self.assertIsNotNone(render, "no render-smoke audit step found")

        self.assertLess(gate, commit, "the gate must run before the first commit")
        self.assertLess(commit, replay, "the commit must run before the replay audit")
        self.assertLess(commit, audit, "the commit must run before the audit_*.py suite")
        self.assertLess(commit, render, "the commit must run before the render-smoke audit")


class TestCiHasTheGateLintSplit(unittest.TestCase):
    """ci.yml's ``gate`` job reproduces the daily pre-collect gate's
    environment (installs requirements.txt); its ``lint`` job installs
    nothing at all — a coding-convention scan must never depend on whether a
    dependency happens to install on the runner (see ci.yml's own lint-job
    comment)."""

    def test_gate_job_installs_requirements(self):
        text = support.read_text(_path("ci.yml"))
        block = _job_block(text, "gate")
        self.assertIsNotNone(block, "ci.yml has no `gate` job")
        self.assertIn("pip install -r requirements.txt", block)

    def test_lint_job_installs_nothing(self):
        text = support.read_text(_path("ci.yml"))
        block = _job_block(text, "lint")
        self.assertIsNotNone(block, "ci.yml has no `lint` job")
        self.assertNotIn("pip install", block)


class TestRequirementsFileMatchesEachWorkflowsTier(unittest.TestCase):
    """daily.yml and intraday.yml — the schedules that run every day — must
    install only the pinned runtime deps (requirements.txt), never the dev
    extras those never need; calibration.yml is the one workflow that needs
    the dev extras (numpy/scipy) and must install requirements-dev.txt. This
    checks WHICH file gets installed, not that file's contents, so a later
    addition to requirements.txt itself does not affect it."""

    _EXPECTED = {
        "daily.yml": "requirements.txt",
        "intraday.yml": "requirements.txt",
        "calibration.yml": "requirements-dev.txt",
    }

    def test_each_workflow_installs_its_mapped_requirements_file(self):
        for name, req_file in self._EXPECTED.items():
            with self.subTest(workflow=name):
                text = support.read_text(_path(name))
                self.assertIn(f"pip install -r {req_file}", text)
                if req_file == "requirements.txt":
                    # Guard the runtime-only tier: it must not sneak in the
                    # dev extras just because "requirements.txt" is also a
                    # substring-adjacent prefix of "requirements-dev.txt".
                    self.assertNotIn("requirements-dev.txt", text)


if __name__ == "__main__":
    unittest.main()
