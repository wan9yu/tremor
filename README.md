# tremor

> An honest, long-running instrument for one question: is the world actually getting more disordered — or does it only feel that way?

中文：tremor 是一台诚实的、长期运行的仪器，回答"这个世界是不是真的更乱了"。它**不预言**末日——是地震仪，不是先知。

tremor watches a few **tension indicators**: guarded equilibria that something powerful normally holds still. When one moves anyway, a larger — often hidden — force has overpowered its guard. Four lines, each guarding a different domain:

- **Flights airborne** — airspace (community ADS-B)
- **US high-yield credit spread** — financial system (FRED)
- **Korea BTC premium** — capital controls (Upbit + Coinbase)
- **Grid frequency** — infrastructure (Nordic grid: Fingrid / Statnett)

Each line is normalized on its own (robust z-score, de-cycled so routine daily/weekly rhythms don't false-trigger); they are never combined into a single doom score. What matters is **resonance** — how many lines are trembling at once. Several independent instruments screaming together is what "actually more disordered" looks like; one moving alone is just a local event.

Missing data is never faked or hidden: a source going dark is recorded as a gap, and a prolonged collection blackout is shown as its own "system disruption" — because the instrument itself falling silent is a kind of tremor.

Data is collected daily by a GitHub Actions cron and committed back to the repo (git-scraping). A static dashboard reads the CSVs directly:

**→ https://wan9yu.github.io/tremor/**

## Run it

```bash
pip install -r requirements.txt
python collect.py && python render.py
```

Three lines need no keys (flights, Korea premium, grid frequency). Add a free `FRED_API_KEY` as a repo Secret to light up the credit-spread line too.
