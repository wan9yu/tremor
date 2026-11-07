# tremor

> A daily record of what each series measures and how today’s readings differ from their own recent records; the meaning stays open.

中文：每日记录各条序列测量什么，以及今天的读数与各自近期记录相差多远；如何理解，仍由读者决定。

tremor collects a small set of daily readings from public sources and compares each one with its own recent record: a robust z-score against a trailing window, or — for a pegged or near-constant series, where "normal" is a declared value rather than a rolling history — a declared anchor and materiality. Lines with a known weekly rhythm are de-cycled by weekday, so a routine weekend does not read as a departure. Readings are never combined into one score.

Four lines are primary today; their readings are the ones the headline counts:

- **Flights airborne** — airspace (community ADS-B)
- **US high-yield credit spread** — financial system (FRED)
- **Offshore−onshore yuan spread** — capital controls (CNH−CNY)
- **Fed SRF take-up** — financial plumbing / US dollar funding (NY Fed markets API)

(The communications slot ran **Internet outages** — a daily count of countries with an IODA outage detection — until R28 moved that line to tier 2 after its eight largest readings were adjudicated as artifacts. R30 filled the open primary slot with **Fed SRF take-up** — a fourth financial line whose two standing gates cleared — rather than a communications line, because the sole comms candidate was still unbuilt; communications now rides the collected set as a passive-BGP route-withdrawal line, the standing candidate for a future slot.)

The primary set is chosen and re-chosen by a scored radar process — see `radar.md` for the current tiers, the metrics, and every calibration decision. The rest of the registry is collected daily and shown beside the count: other daily records, contrast lines (VIX, global news tone), context lines (a planetary slow-level read and a space-weather confounder-subtractor), and one control line with no world in it at all. None of them enters the count.

The headline states how many scored primary lines crossed their own threshold in either direction, out of those comparable that day. It counts lines, not events; repeated observations do not add another score. A separate list records long-running readings that stay below a fixed reference — the named straits whose daily traffic holds at or below half of the reference for 14 days — with its own rule and publication lag. It is a distinct measure, not a second answer to the count.

The rolling comparison looks to recent history; a change that lasts can become part of a series' own reference. The displayed roster is selected under written measurement assumptions, and the count does not undo that selection. Other daily records are collected but never enter this count. No communications-domain reading is included, so a worldwide connectivity event reads zero in this count. Some sources arrive late or skip dates; missing values remain gaps.

Missing data is never faked or hidden: a source going dark is recorded as a gap, and a prolonged collection blackout is shown as its own system disruption.

Data is collected daily by a GitHub Actions cron and committed back to the repo (git-scraping). A static dashboard reads the CSVs directly:

**→ https://wan9yu.github.io/tremor/**

## Run it

```bash
pip install -r requirements.txt
python collect.py && python render.py
```

All four primary lines run keyless (flights, yuan spread, Fed SRF take-up via the NY Fed markets API, and the credit spread via a public FRED fallback). Adding a free `FRED_API_KEY` as a repo Secret just gives the credit line its primary, keyed source.

## Machine-checked claims

A few numbers in this document are checked against the code by `tests/lint_public_surface.py`, which runs on every push — if the code moves and this table doesn't, the lint goes red rather than the claim quietly going stale.

| claim | value |
|---|---|
| primary (tier-1) lines | 4 |
| status values `core/normalize.py` can emit | 6 |
| primary lines that run keyless | 4 |
