# tremor

> An honest, long-running instrument for one question: is the world actually getting more disordered — or does it only feel that way?

中文：tremor 是一台诚实的、长期运行的仪器，回答"这个世界是不是真的更乱了"。它**不预言**末日——是地震仪，不是先知。

tremor watches a few **tension indicators**: guarded equilibria that something powerful normally holds still. When one moves anyway, a larger — often hidden — force has overpowered its guard. Four lines, each guarding a different domain:

- **Flights airborne** — airspace (community ADS-B)
- **US high-yield credit spread** — financial system (FRED)
- **Offshore−onshore yuan spread** — capital controls (CNH−CNY)
- **Internet outages** — how many countries are dark at once (IODA)

The primary set is chosen and re-chosen by a scored radar process — see `radar.md` for the
current tiers, the metrics, and every calibration decision. Eleven more lines ride a hidden
watchlist, collected daily while they earn (or lose) a place.

Each line is normalized on its own (robust z-score against its own recent history; lines with a known weekly rhythm are de-cycled by weekday so a routine weekend dip doesn't false-trigger); they are never combined into a single doom score. What matters is **resonance** — how many lines are trembling at once. Several independent instruments screaming together is what "actually more disordered" looks like; one moving alone is just a local event.

The dashboard states its own **field of view**: the four primary lines watch EU/US/Japan airspace, US high-yield credit, the onshore/offshore yuan, and worldwide internet reachability. Strain outside that can be entirely real and still read 0 — and because each line is scored against its own recent history, a disorder that has already been running for weeks sits inside its own baseline and reads calm too. Both limits are written down in `radar.md`.

Missing data is never faked or hidden: a source going dark is recorded as a gap, and a prolonged collection blackout is shown as its own "system disruption" — because the instrument itself falling silent is a kind of tremor.

Data is collected daily by a GitHub Actions cron and committed back to the repo (git-scraping). A static dashboard reads the CSVs directly:

**→ https://wan9yu.github.io/tremor/**

## Run it

```bash
pip install -r requirements.txt
python collect.py && python render.py
```

All four primary lines run keyless (flights, yuan spread, internet outages, and the credit spread via a public FRED fallback). Adding a free `FRED_API_KEY` as a repo Secret just gives the credit line its primary, keyed source.
