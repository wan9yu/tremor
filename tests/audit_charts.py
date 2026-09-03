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

PROVISIONAL cap. Measured pre-quantization sizes (2026-09-04): overview
19,930 B, cnh_cny 57,872 B, net_outages 58,408 B, credit_spread 59,435 B,
flights 61,594 B (the largest). ``PER_CHART_BYTE_CAP`` below is set a little
above that largest measured file, with headroom for ordinary day-to-day
variation (more data points, a wider legend on a bad day) without chasing
every render. It is meant to be TIGHTENED in T22, once ``render.py``
quantizes each chart to a 64-colour palette (measured there to drop each
chart to roughly 20 KB) — at that point the cap should come from the
per-file quantized sizes, not this pre-quantization number, and NOT from any
summed total across all charts (a sum bounds nothing about a single
oversized file).
"""
import glob
import os
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHARTS = os.path.join(ROOT, "charts")

# PROVISIONAL, from the pre-quantization sizes above (largest measured:
# flights at 61,594 B) — TIGHTEN in T22 once render.py's 64-colour quantize
# lands, using each chart's own quantized size, not this number and not a
# cross-chart sum.
PER_CHART_BYTE_CAP = 70000


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
