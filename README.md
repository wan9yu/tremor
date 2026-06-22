# tremor

> An honest, long-running instrument that answers one question: **is the world actually getting more disordered — or does it only feel that way?**

`tremor` is three things at once: the **micro-shaking before an earthquake** (a leading signal), the **shiver of fear or cold** (a stress signal), and an earthquake itself (where this project began). Civilizations tremble before they break; tremor listens for that trembling.

It does **not** predict the end — nobody can. It only makes *now* readable: it's a seismograph, not a prophet. It is blind to instantaneous, global catastrophe (a nuclear flash, an overnight black swan). What it listens for is the **slow, systemic, trace-leaving** kind of disorder.

中文一句话：tremor 是一台诚实的、长期运行的仪器，回答"这个世界是不是真的更乱了"。它**不预言**末日，只让此刻变得可读——是地震仪，不是先知。

---

## How it works — tension indicators

You can't measure "how close the world is to collapse." But you *can* find a few deeply-coupled proxies that are continuously, publicly recorded and that swing hard the moment systemic stress appears. tremor only admits a proxy if it's a **tension indicator** — a guarded equilibrium with three parts:

| part | meaning |
|---|---|
| **the guard** | a powerful, self-interested force pins this number to its normal value |
| **the leaking hand** | when it moves anyway, a larger — often hidden — force has overpowered the guard. You aren't measuring the number; you're measuring *that hand* |
| **the source** | public, stable, fetchable automatically every day |

Free-floating noise (raw news-event counts, VIX, seismic energy) is **excluded** on purpose: nothing guards it, so a spike is cheap. Tension indicators are naturally resistant to "more sensors = more disorder" inflation, because they only yield to a real force.

## The four lines

Each line guards a **different domain**, so on a normal day they're unrelated. Several trembling *at once* is the signal.

| line | domain | guard → leaking hand | source (free) |
|---|---|---|---|
| **Flights airborne** | Airspace | airlines defend on-time profit → closed airspace, weather, pandemic, lockdown | OpenSky `/states/all` (anonymous, OAuth optional) |
| **Credit spread** | Financial system | banks/central banks press spreads down → fear overpowering greed (the 2008 fuse) | FRED `BAMLH0A0HYM2` |
| **Korea BTC premium** | Capital controls | arbitrage should erase price gaps → capital trapped, controls tightening | Upbit + Coinbase + open.er-api |
| **Grid frequency** | Infrastructure | operators defend 50 Hz by the second → supply/demand overwhelmed | Fingrid Open Data, dataset 177 |

## Reading the instrument

Each line is normalized **on its own** with a rolling robust z-score (median + MAD over the last 90 available readings; gap days are skipped, never filled). A line is **trembling** when `|z| > 3`. When a baseline has no spread to measure against, the z-score is left blank rather than guessed.

The lines are **never** multiplied or weighted into a single doom score. The only composite is a **count**: how many lines are trembling today (0–4). Several independent instruments screaming together is what "the world is actually more disordered" looks like; one moving alone is a local event.

## Architecture — git scraping

A GitHub Actions cron runs `collect.py` daily → each fetcher pulls today's value → values are appended to `data/*.csv` with their z-score and trembling flag → `render.py` redraws the charts → everything is committed back to the repo. Free, fully automatic, and the data carries its own version history. A static [GitHub Pages dashboard](docs/index.html) (Chart.js) reads the CSVs directly — no backend.

```
data/<line>.csv   date,raw_value,z_score,trembling,direction,source_note
data/summary.csv  date,flights_z,credit_z,capital_z,grid_z,trembling_count
charts/*.png      one per line + a resonance overview
docs/             the Pages dashboard (reads docs/data/*.csv)
```

## Guardrails / discipline

1. **Calm, not panic.** tremor reports "N instruments are trembling," never "run." Measured language only.
2. **Every tremble must be attributable.** Each spike should get a note: what happened that day. Unattributed spikes are suspect by default.
3. **Missing data is honest.** If a source fails, the day is written **empty with a reason** — never forward-filled or faked.
4. **No inflation.** We measure the *deviation* of a guarded indicator, not raw counts — so "more records" never masquerades as "more disorder."
5. **"Still running" ≠ "safe forever."** A line being normal describes only this moment, never the future.

## Running it

```bash
pip install -r requirements.txt
python collect.py      # appends today's readings
python render.py       # redraws charts/
```

Flights work anonymously and the Korea premium needs no key, so the pipeline runs out of the box. To light up every line, add these **free** API keys as repo Secrets (used by the daily workflow):

| secret | source | needed for |
|---|---|---|
| `FRED_API_KEY` | https://fred.stlouisfed.org/docs/api/api_key.html | credit spread |
| `FINGRID_API_KEY` | https://data.fingrid.fi | grid frequency |
| `OPENSKY_CLIENT_ID` / `OPENSKY_CLIENT_SECRET` | https://opensky-network.org (Account → API client) | higher flight quota (optional) |

Never hardcode keys — they live only in repo Secrets.
