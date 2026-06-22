"""Render tremor's PNG "temperature charts": one per line + a resonance overview.

These are committed alongside the data so the repository itself is readable at a
glance, with no dashboard required.
"""
import csv
import os
from datetime import datetime

import matplotlib

matplotlib.use("Agg")  # headless: no display needed in CI
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.dates import DateFormatter  # noqa: E402

from fetchers import capital_premium, credit_spread, flights, grid_frequency  # noqa: E402

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, "data")
CHARTS = os.path.join(ROOT, "charts")
LINES = [flights, credit_spread, capital_premium, grid_frequency]


def _load(path):
    if not os.path.exists(path):
        return []
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def _dates(rows):
    return [datetime.strptime(r["date"], "%Y-%m-%d") for r in rows]


def render_line(mod):
    rows = [r for r in _load(os.path.join(DATA, mod.LINE + ".csv"))
            if r.get("raw_value") not in (None, "")]
    if not rows:
        return
    xs = _dates(rows)
    ys = [float(r["raw_value"]) for r in rows]
    trembling = [r.get("trembling") == "1" for r in rows]

    fig, ax = plt.subplots(figsize=(9, 3.2))
    ax.plot(xs, ys, color="#444444", lw=1.2, zorder=1)
    tx = [x for x, t in zip(xs, trembling) if t]
    ty = [y for y, t in zip(ys, trembling) if t]
    if tx:
        ax.scatter(tx, ty, color="#d62728", s=36, zorder=3, label="trembling")
        ax.legend(loc="best", fontsize=8)
    ax.set_title(f"{mod.LABEL}  ·  alarming when {mod.ANOMALY_DIRECTION}", fontsize=11)
    ax.set_ylabel(mod.UNIT, fontsize=9)
    ax.grid(True, alpha=0.25)
    ax.xaxis.set_major_formatter(DateFormatter("%b %d"))
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(os.path.join(CHARTS, mod.LINE + ".png"), dpi=120)
    plt.close(fig)


def render_overview():
    rows = _load(os.path.join(DATA, "summary.csv"))
    if not rows:
        return
    xs = _dates(rows)
    counts = [int(r["trembling_count"]) if r.get("trembling_count") not in (None, "") else 0
              for r in rows]

    fig, ax = plt.subplots(figsize=(9, 3.2))
    ax.bar(xs, counts, color="#d62728", alpha=0.85)
    ax.set_title("Resonance — lines trembling per day (0-4)", fontsize=11)
    ax.set_ylim(0, 4)
    ax.set_yticks([0, 1, 2, 3, 4])
    ax.grid(True, axis="y", alpha=0.25)
    ax.xaxis.set_major_formatter(DateFormatter("%b %d"))
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(os.path.join(CHARTS, "overview.png"), dpi=120)
    plt.close(fig)


def render():
    os.makedirs(CHARTS, exist_ok=True)
    for mod in LINES:
        render_line(mod)
    render_overview()
    print("charts written to", CHARTS)


if __name__ == "__main__":
    render()
