"""AUDIT: every committed chart PNG stays under a fixed per-file byte cap.

A rendering change in ``render.py`` (a new series, a denser legend, a colour
regression away from quantization) can silently bloat every chart it writes.
Nothing upstream of ``git`` catches that — the PNGs are binary, so a normal
diff review shows only "file changed", not "file grew". This audit is the
mechanical guard: it caps each file's raw size in bytes.

AUDIT, not gate, not lint. Charts do not exist until ``render.py`` runs, and
daily.yml's derive step runs ``render.py`` (writing ``charts/``) and commits
it BEFORE the audit step (``python -m unittest discover tests -p
"audit_*.py"``) — see daily.yml's "Derive levels and drifts, render charts,
commit" step followed by "Audit the committed record". So this cannot be a
``test_*.py`` gate file (the pre-collect gate runs before any chart exists
for today, and — per tests/audit_record.py's docstring and
tests/test_side_channel.py's ``TestGateNeverReadsTheCommittedRecord`` — the
gate may never read committed artifacts at all, so a stale chart could never
abort a collection day even if one existed). Nor may it be a
``lint_*.py`` push-CI check: push CI has no render step, so a lint would only
ever see whatever charts happen to already be sitting in the tree — on an
ordinary push that is yesterday's committed PNGs, unrelated to today's diff,
so it would either pass vacuously (nothing in the diff touched the charts)
or flag a size with no connection to the change under review, missing a
render.py-induced regression until the NEXT daily run. Only the audit runs
in the same job, after that run's own ``render.py`` invocation, checking the
charts that invocation just produced.

Not a ``git rev-list``/repo-growth test: no workflow in this repo sets
``fetch-depth`` on ``actions/checkout``, so every job — this one included —
runs on a shallow clone. A history-growth check would either error on the
missing history or silently see only the single fetched commit, making it
vacuous here. A per-PNG byte cap needs none of that history; ``os.path
.getsize`` on the file as committed is enough.

Measured post-quantization sizes (2026-09-04, render.py's 64-colour
MEDIANCUT quantize): overview 6,776 B, credit_spread 22,259 B, cnh_cny
23,381 B, net_outages 24,325 B, flights 24,886 B (the largest).
``PER_CHART_BYTE_CAP`` below comes from that largest quantized file plus
generous headroom — the daily render happens on an ubuntu CI runner (these
were measured on macOS) and ordinary day-to-day variation (more data
points, a wider legend on a bad day) can shift a file's size, so the cap
absorbs cross-platform and cross-day variance without chasing every render.
"""
import glob
import os
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHARTS = os.path.join(ROOT, "charts")

# From the quantized sizes above (largest measured: flights at 24,886 B),
# times roughly 1.6 for cross-platform (ubuntu daily vs. macOS measurement)
# and day-to-day headroom, rounded to a clean number. Still a single-file
# bound, never a cross-chart sum.
PER_CHART_BYTE_CAP = 40000


class TestChartByteBudget(unittest.TestCase):
    def test_every_chart_png_is_under_the_cap(self):
        paths = sorted(glob.glob(os.path.join(CHARTS, "*.png")))
        self.assertTrue(
            paths, f"no PNGs found under {CHARTS} — glob matched nothing, "
                   f"which would make this audit vacuously pass")
        offenders = []
        for path in paths:
            size = os.path.getsize(path)
            if size > PER_CHART_BYTE_CAP:
                offenders.append(
                    f"{os.path.basename(path)}: {size} B exceeds the "
                    f"{PER_CHART_BYTE_CAP} B per-chart cap")
        self.assertEqual(offenders, [], "\n".join(offenders))


if __name__ == "__main__":
    unittest.main()
