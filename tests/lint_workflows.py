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


class TestNoStaleTwentyTwoZeroDailyRunPhrasing(unittest.TestCase):
    """Guard against the stale "22:00 daily run" comment class: daily.yml
    fires at 18:00Z and sleeps to the 22:30Z collection target (see
    daily.yml's own "Sleep until the 22:30Z sample target" step) — there has
    never been a 22:00 daily run. A comment naming one names a schedule that
    does not exist."""

    def test_no_workflow_names_a_22_00_daily_run(self):
        for name in _workflow_files():
            with self.subTest(workflow=name):
                text = support.read_text(_path(name))
                self.assertNotIn("22:00 daily run", text)


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

        def first(msg, predicate):
            found = next((i for i, s in enumerate(steps) if predicate(s)), None)
            if found is None:
                self.fail(msg)
            return found

        # The pre-collect gate — plain `unittest discover tests`, not the
        # audit_*.py suite that reuses the same "unittest discover tests"
        # words with a `-p` filter appended.
        gate = first("no pre-collect gate step (`unittest discover tests`) found",
                     lambda s: "unittest discover tests" in s and "-p" not in s)
        commit = first("no commit step (`ci_push.sh`) found",
                       lambda s: "ci_push.sh" in s)
        replay = first("no replay --check audit step found",
                       lambda s: "replay.py --check" in s)
        audit = first("no audit_*.py audit step found",
                      lambda s: 'discover tests -p "audit_*.py"' in s)
        render = first("no render-smoke audit step found",
                       lambda s: "render_smoke.js" in s)

        self.assertLess(gate, commit, "the gate must run before the first commit")
        self.assertLess(commit, replay, "the commit must run before the replay audit")
        self.assertLess(commit, audit, "the commit must run before the audit_*.py suite")
        self.assertLess(commit, render, "the commit must run before the render-smoke audit")


class TestFailureAlarmBodyMatchesTheStepOrder(unittest.TestCase):
    """The failure alarm fires from ANY failed step, including the audits that
    run AFTER the day is committed (see daily.yml's own "VERIFY AFTER
    COMMITTING, NEVER BEFORE" comment). So its body may not claim that a failed
    run wrote no row: a run that falls over in a derive tool or an audit has
    already pushed the day. The body must say which failures cost the day and
    which do not, and must keep the schedule-expiry sentence, which is true
    either way. Pinned through ``support.workflow_run_steps`` so the assertion
    reads the shell the workflow actually runs, not a comment beside it."""

    _TITLE = 'TITLE="tremor: the daily collection is failing"'

    def _alarm_block(self):
        blocks = [s for s in support.workflow_run_steps(_path("daily.yml"))
                  if self._TITLE in s]
        self.assertEqual(len(blocks), 1,
                          f"expected exactly one failure-alarm run block carrying {self._TITLE}")
        return blocks[0]

    def _alarm_body(self):
        """The alarm block with runs of whitespace collapsed, so a sentence
        wrapped across YAML lines compares as one string."""
        return " ".join(self._alarm_block().split())

    def test_body_says_a_pre_commit_failure_costs_the_day(self):
        self.assertIn(
            "A run that fails before the commit step leaves the day unrecorded.",
            self._alarm_body())

    def test_body_says_a_post_commit_failure_does_not_cost_the_day(self):
        self.assertIn(
            "run that fails after it has already pushed the day has not lost the day",
            self._alarm_body())

    def test_body_keeps_the_schedule_expiry_sentence(self):
        self.assertIn(
            "The schedule itself expires after 60 days without a commit.",
            self._alarm_body())

    def test_body_no_longer_claims_a_failed_run_writes_no_row(self):
        body = self._alarm_body()
        self.assertNotIn("The instrument writes no row for a failed run", body)
        self.assertNotIn("writes no row for a failed run", body)

    def test_body_adds_no_command_substitution_or_backtick(self):
        block = self._alarm_block()
        self.assertNotIn("`", block)
        # The two substitutions the body already had, and no third: an issue
        # body is prose, so anything it interpolates must be able to fail
        # silently inside a shell double-quoted string.
        self.assertIn("$(date -u +%F)", block)
        self.assertEqual(block.count("$("), 2)


class TestCiHasTheGateLintSplit(unittest.TestCase):
    """ci.yml's ``gate`` job reproduces the daily pre-collect gate's
    environment (installs requirements.txt); its ``lint`` job installs
    nothing at all — a coding-convention scan must never depend on whether a
    dependency happens to install on the runner (see ci.yml's own lint-job
    comment)."""

    def _job(self, name):
        """The one job block named `name` in ci.yml; fails loudly when absent."""
        block = _job_block(support.read_text(_path("ci.yml")), name)
        if block is None:
            self.fail(f"ci.yml has no `{name}` job")
        return block

    def test_gate_job_installs_requirements(self):
        self.assertIn("pip install -r requirements.txt", self._job("gate"))

    def test_lint_job_installs_nothing(self):
        self.assertNotIn("pip install", self._job("lint"))


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
