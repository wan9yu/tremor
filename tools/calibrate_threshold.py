"""Generate the per-window-size tremble threshold table in core/normalize.py.

WHY THE THRESHOLD CANNOT BE ONE NUMBER. A robust z is today's distance from the
window's median in units of the window's Qn — and both of those are ESTIMATED
from the window. At ninety observations they are steady; at ten they are not,
so a calm day fakes a |z| above 3 far more often on a young line than on an old
one. Measured on this repo's own arithmetic, the same |z| > 3 rule delivers a
false-tremble probability of 2.62% per calm day at n=10 and 0.391% at n=90 —
a 6.7x spread, with both regimes live on the record simultaneously.

So the rule is stated the other way round: every line, whatever its age, gets
the SAME odds of a false tremble on a calm day, and the bar moves to deliver
that. The target is the rate the instrument already had at a full window
(0.391%, i.e. exactly c=3.0 at n=90), so nothing about a mature line changes
and only young lines are held to the higher bar their thin evidence deserves.

METHOD. For iid Gaussian data the new observation is independent of the window,
so conditional on a window's median m and scale s the exceedance probability is
exact: P(|x-m| > c*s) = Phi(m - c*s) + 1 - Phi(m + c*s). Only the WINDOW is
simulated; the observation is integrated out. That is both far cheaper and far
less noisy than drawing an observation per window, which is what makes an
81-entry table practical to a few thousandths.

The Qn here is a vectorized mirror of ``normalize._qn`` and is asserted equal
to it before any table is produced — the calibration must be of the estimator
the instrument actually uses, not of a lookalike.

NUMPY AND SCIPY ARE DEV-ONLY. They are deliberately NOT in requirements.txt —
the daily run must not depend on them, and nothing else in the repo imports
them — so this tool needs requirements-dev.txt installed. The table it produces
is vendored into core/normalize.py precisely so that collection never has to
simulate anything.

    pip install -r requirements-dev.txt
    python tools/calibrate_threshold.py            # print the table
    python tools/calibrate_threshold.py --check    # verify the shipped table
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from scipy.stats import norm

from core import normalize

SEED = 20260803          # fixed: the table must be re-derivable exactly
WINDOWS = 120_000        # simulated windows per n
N_MIN, N_MAX = normalize.MIN_POINTS, normalize.WINDOW
TARGET_N = normalize.WINDOW      # the window size whose rate everything matches
TARGET_C = 3.0                   # ...at the threshold the instrument always had


def qn_batch(samples):
    """Qn of every row of ``samples`` (m x n), matching normalize._qn exactly."""
    n = samples.shape[1]
    # Index the pairs directly rather than building the full n x n cube and
    # discarding half of it: measured 212ms against 274ms per 3000-window batch
    # at n=90, and half the peak memory.
    i, j = np.triu_indices(n, k=1)
    diffs = np.abs(samples[:, i] - samples[:, j])
    h = n // 2 + 1
    k = h * (h - 1) // 2 - 1
    kth = np.partition(diffs, k, axis=1)[:, k]
    return normalize._QN_C * normalize._qn_factor(n) * kth


def _assert_mirror():
    rng = np.random.default_rng(1)
    for n in (10, 11, 25, 40, 89, 90):
        sample = rng.normal(size=(3, n))
        mine = qn_batch(sample)
        theirs = [normalize._qn(list(row)) for row in sample]
        assert np.allclose(mine, theirs, atol=1e-9), f"Qn mirror differs at n={n}"


def window_stats(n, rng, batch=3000):
    """(median, Qn) of ``WINDOWS`` iid standard-normal windows of size n."""
    meds, scales = [], []
    done = 0
    while done < WINDOWS:
        size = min(batch, WINDOWS - done)
        sample = rng.normal(size=(size, n))
        meds.append(np.median(sample, axis=1))
        scales.append(qn_batch(sample))
        done += size
    return np.concatenate(meds), np.concatenate(scales)


def exceedance(meds, scales, c):
    """P(|z| > c) averaged over the simulated windows, observation integrated out."""
    lo, hi = meds - c * scales, meds + c * scales
    return float(np.mean(norm.cdf(lo) + norm.sf(hi)))


def solve_c(meds, scales, target):
    # 25 halvings of [2, 12] resolve 3e-7 — three orders below the rounding the
    # table ships at, and far below the 0.02 tolerance --check allows. Sixty
    # steps resolved float64 itself and cost ~40 wasted evaluations per entry.
    lo, hi = 2.0, 12.0
    for _ in range(25):
        mid = (lo + hi) / 2
        if exceedance(meds, scales, mid) > target:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def monotone(values):
    """Enforce non-increasing c(n) by pooling adjacent violators.

    The true bar can only fall as evidence accumulates — more readings never
    make a calm day fake a tremble more easily. Simulation noise does not know
    that, and leaves the raw table wobbling by ~0.01 between neighbours, which
    would put a visibly higher bar at 70 readings than at 69 and invite a reader
    to look for a meaning that is not there. Pooling adjacent violators (the
    standard isotonic fit) imposes the constraint and changes nothing else: it
    is the closest non-increasing sequence to what was measured.
    """
    blocks = [[v, 1] for v in values]
    i = 1
    while i < len(blocks):
        if blocks[i - 1][0] < blocks[i][0]:      # a rise: pool the two blocks
            total = blocks[i - 1][0] * blocks[i - 1][1] + blocks[i][0] * blocks[i][1]
            weight = blocks[i - 1][1] + blocks[i][1]
            blocks[i - 1:i + 1] = [[total / weight, weight]]
            i = max(1, i - 1)
        else:
            i += 1
    return [value for value, weight in blocks for _ in range(weight)]


def build():
    _assert_mirror()
    rng = np.random.default_rng(SEED)
    anchor_meds, anchor_scales = window_stats(TARGET_N, rng)
    target = exceedance(anchor_meds, anchor_scales, TARGET_C)
    print(f"target rate = P(|z|>{TARGET_C}) at n={TARGET_N} = {target * 100:.4f}%/calm day",
          file=sys.stderr)
    sizes = list(range(N_MIN, N_MAX + 1))
    raw = []
    for n in sizes:
        # The anchor window was already simulated to fix the target rate; the
        # largest size is the most expensive one and does not need it twice.
        meds, scales = ((anchor_meds, anchor_scales) if n == TARGET_N
                        else window_stats(n, rng))
        raw.append(solve_c(meds, scales, target))
        print(f"  n={n:3d}  c={raw[-1]:.3f}", file=sys.stderr)
    # Two constraints the simulation does not know, applied after the fit.
    # The bar falls with evidence (monotone, above) and it never falls BELOW
    # the full-window bar, because a full window is all the evidence there is —
    # ``WINDOW`` caps it. Near n=90 the measured curve wobbles a few
    # thousandths across 3.0; clamping keeps the anchor exact, so a mature line
    # is governed by precisely the rule it always was.
    table = {n: round(max(c, TARGET_C), 3) for n, c in zip(sizes, monotone(raw))}
    return target, table


def main(argv):
    target, table = build()
    if "--check" in argv:
        bad = [(n, c, shipped) for n, c in table.items()
               if abs((shipped := normalize.threshold_for(n)) - c) > 0.02]
        if bad:
            print(f"FAIL: {len(bad)} entries differ by more than 0.02: {bad[:5]}")
            return 1
        print(f"OK: shipped table matches a fresh calibration within 0.02 "
              f"(target {target * 100:.4f}%)")
        return 0
    print(f"# target null tremble rate {target * 100:.4f}% per calm day "
          f"(= |z|>{TARGET_C} at n={TARGET_N})")
    print("_C_N = {")
    for n in sorted(table):
        print(f"    {n}: {table[n]:.3f},")
    print("}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
