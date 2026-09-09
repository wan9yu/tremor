# tremor radar — calibration log

The append-only round-by-round record behind the registry in **[radar.md](radar.md)**.
Each round is dated and states what was measured, decided, and deferred. The living registry
(scoring law, the three gates, tier tables, Backlog, Rejected) is in radar.md; this is the history.

Rounds 1–19 are archived in **[radar-log-1.md](radar-log-1.md)**.

### Round 20 — 2026-08-19 (the possibilities sweep: six probes, and what is actually reachable)

The prompt was "看一下我们的可能性" — survey what is reachable. So this round is mostly the DIVERGE
step, run as six parallel source-probes across domains, each required to actually FETCH its endpoint
and return the real number, not assert plausibility. The score step first, because it decides
whether any diverge even matters.

**No tier-1 move is due — measured, same verdict as R13.** The orthogonality of every tier-2 line's
z-history against the live four: the only MATURE lines that clear the ≥60-reading bar are all
credit-correlated and would duplicate an existing slot — `em_corp_oas` +0.80, `euro_hy_spread`
+0.74, `vix` +0.75 against the credit family. Every line that is genuinely ORTHOGONAL and FRESH is
still too young to adjudicate: `sofr_iorb_spread` 36 scored (−/+0.34), `stablecoin_peg` 2129 rows but
only ~4 days LIVE (seeded rows are not live detections; −0.13), `tga_days_cash` n=1, `fx_parallel`
n=14, `hkma` n=6. The two strong-and-orthogonal mature ones — `port_throughput` (−0.34) and
`chokepoint_breadth` (−0.19), both 214/218 scored — are frozen out of tier-1 by the freshness rule
(PortWatch obs lag 10 days). Nothing to promote; the value of the round is the survey.

**The six probes (each fetched live, 2026-08-19):**

1. **`fed_srf_takeup` — BUILD-READY, CONFIRMED.** The registry has carried this as build-ready since
   R15; this round proves the source is live+keyless+daily+zero-lag TODAY. NY Fed markets API,
   `https://markets.newyorkfed.org/api/rp/all/all/results/last/N.json` (HTTP 200, no key), returns
   `repo.operations[]` with `operationDate` / `operationType` / `totalAmtAccepted`. Today's rows:
   2026-08-18 Repo $0 and a $1,000,000 Repo; Reverse Repo $155m. Guard passes cleanly (SRF is a
   full-allotment ceiling the Fed defends at a ~$0 equilibrium — nonzero take-up is a bank borrowing
   from the guard itself, the leaking hand); cadence passes (daily-settled); reachability passes (a
   Sept-2019-style squeeze draws tens of billions against ANCHOR=0/MATERIALITY≈$5000m → |z|≫3). Two
   corrections vs the registry's carried plan: the URL needs the `/all/all/` method segment (the
   `/rp/all/results/` form 400s), and there are TWO "Repo" ops per day — the recurring **$1m is the
   Fed's standing small-value exercise (SVE)** and must be filtered from the genuine SRF take-up. Both
   are build-time detail, not blockers. This is the one actionable "possibility" of the round.

2. **`onrrp_takeup` — REJECTED on the guard gate (new).** A new idea, and a clean kill. The source is
   live/keyless/daily/fresh (FRED `RRPONTSYD`, 2026-08-18 = $0.155B, drained from a $2.55T Dec-2022
   peak), so it fails nothing on plumbing. It fails on the FOUNDING QUESTION: the Fed defends the RRP
   offering RATE (the corridor floor), not the take-up QUANTITY. Take-up is a market-determined
   residual — the cash money funds park when private rates sink to the floor — with no guardian
   holding it at any equilibrium, so nothing "leaks" when it moves. It is a scarcity LEVEL, not a
   defended-equilibrium leak. The genuinely-guarded number in this exact plumbing is the rate spread,
   which the registry already collects as `sofr_iorb_spread`. Recorded in Rejected so it is not
   re-probed. (This is the guard gate doing precisely its job — screening out an interesting number
   that has no guardian.)

3. **`ais_dark_activity` — NON-FIND (sourcing) and guard-questionable.** The idea: vessels going dark
   (disabling AIS) leak sanctions evasion / pre-conflict staging, orthogonal to PortWatch transit
   counts. Two walls. Sourcing: every real dark-ship feed is key-gated or commercial — Global Fishing
   Watch Events (the canonical one) returns HTTP 401 without a mandatory free-registration token;
   SkyTruth/Skylight is a platform not a feed; Datalastic/VesselFinder/MarineTraffic/UN Global
   Platform all require keys. Guard: an AIS-gap is an INFERRED detection (someone's smuggling model),
   closer to a sentiment read than a number a guardian defends. Recorded in Rejected in the
   `marine_war_risk` / `sovereign_cds` lineage — the guarded quantity is real, no keyless daily source
   exists — so the search is not repeated.

4. **`bgp_instability` — re-probe, STILL BLOCKED.** The backlog blocker holds. RIPEstat is keyless
   but every routing endpoint (`routing-status`, `bgp-updates`, `bgp-update-activity`) makes
   `resource=` mandatory → SINGLE-AS only (e.g. AS3333: 6 IPv4 prefixes, 325/325 RIS peers), which is
   dominated by low-count-integer and sensor-inflation noise, not a global instability measure. The
   one true global aggregate — Cloudflare Radar BGP timeseries — requires an `Authorization: Bearer`
   token even on the free tier. No keyless GLOBAL daily aggregate exists; note updated with the
   concrete endpoints tried.

5. **`entsog_gas_flow` — BACKLOG, but the source is now PROBED keyless-live (real progress).** The one
   backlog item that moved forward. The ENTSOG operational-data API is KEYLESS and returns real daily
   per-point physical flows: `.../api/v1/operationaldata?indicator=Physical%20Flow&periodType=day` →
   Fos LNG (FR) entry 129,088,330 kWh/d for 2026-08-16 (updated 08-18), Blaregnies L (BE/FR) 51.6
   GWh/d, ~2-day lag. Guard passes (cross-border physical flow is a real defended quantity — Nord
   Stream 2022 went to zero), cadence passes (kWh/**d**), reachability passes (a cutoff drives flow to
   0). The blocker was never sourcing — it is the AGGREGATION DESIGN the registry already named:
   choosing a non-diluting, non-frame-churning set of import points. Backlog note upgraded from
   "source uncertain" to "source confirmed keyless-live; only point-selection design remains." (AGSI+
   storage, the separate `eu_gas_storage` item, was re-checked and STILL returns "invalid/missing API
   key" — unchanged, still needs a free registered key.)

6. **`usd_xccy_basis` — re-probe, STILL EXHAUSTED.** The cleanest guard in the whole registry (USD
   swap lines literally defend this exact number) remains unbuildable for lack of a feed. Re-verified
   by fetching: OFR STFM exposes only {FNYR, MMF, NYPD, REPO, TYLD} — zero FX/swap series; FRED
   `XCCYBASIS3M` 403/absent; cbonds and CME paywalled/keyed. No keyless daily basis number obtainable.
   Note stamped with the re-probe date so the exhaustion is dated, not perpetual.

**Decisions.** No tier move. `fed_srf_takeup` is RECOMMENDED to build (financial-plumbing, the
structural-zero wall already solved by the R15 anchored scale-mode) — building a fetcher needs the
user's go, so it is proposed, not shipped, this round. Mechanical registry writes applied: `onrrp_takeup`
and `ais_dark_activity` → Rejected with their reasons; `entsog_gas_flow` source confirmed keyless;
`bgp_instability` and `usd_xccy_basis` re-probe notes dated; `fed_srf_takeup` backlog note corrected
(URL `/all/all/`, SVE filter). The survey's shape: the registry's plumbing corner is well-mapped —
the reachable next line is `fed_srf_takeup`, and beyond it the frontier is not more sources but the
DESIGN work already named (entsog point-selection) or a key we've chosen not to ship (AGSI+, xccy).

**Build follow-through (same round, approved): `fed_srf_takeup` ships as tier 2.** Files:
`fetchers/fed_srf_takeup.py`, `tools/seed_fed_srf.py`, `tests/test_fed_srf_takeup.py`, registered in
`collect.py`. The reading is the day's TOTAL amount accepted across all SRF repo operations, in $m,
scored in anchored scale-mode (ANCHOR=0, MATERIALITY=$10,000m). One correction to the pre-build
recommendation: the "$1m SVE to filter" turned out NOT to be a fixed exercise — the small afternoon
amounts vary ($0/$1m/$2m/$3m/$100m) and are indistinguishable in the API's fields (same `Full
Allotment` method, empty note), so they are not filtered but SUMMED IN; at <$100m they are z<0.01
against the $10bn materiality, immaterial by construction. Take-up = every `Repo` op that day (both
auction formats — Full Allotment and Multiple Price — and the three rare term ops); reverse-repo (RRP,
a different facility) is excluded by the `operationType=="Repo"` filter.

**MATERIALITY set on the friction band, not fitted to a count.** The full 2021-07-28-> record pulls in
one keyless request: 1262 operation days, 60.8% exactly $0 (the registry's 61.4% claim, confirmed on
live data), 767 zero-days scoring an honest z=0. The post-2025 regime brought genuine month/quarter-end
reserve scarcity — the friction band now sits at ~$20-26bn — so MATERIALITY=$10bn puts the alarm at
$30bn, comfortably above it. Replayed, the line fires on exactly three days, all genuine: year-end
2025 $74.6bn (z=7.5, the record SRF print), the Oct-2025 month-end $50.4bn (z=5.0), and a mid-month
2026-02-17 $30.5bn (z=3.05) that no calendar explains. The sub-alarm month-end cluster ($20-26bn → z
2.0-2.6) reads as a visible bump, not a tremble — a calendar structure this line does not yet
de-cycle, which is the named gate on any future tier-1 promotion (this repo still has no de-cycling).

**Verified before commit.** An adversarial four-lens review (contract/registration, financial
semantics, settle-timezone-dedup, robustness) ran over the built files. Two lenses clean; it surfaced
two worth-fixing items, both applied: (1) the settle boundary now uses an explicit UTC date, not naive
`date.today()`, so a manual re-seed from a machine ahead of US-Eastern can never record a partial
AM-only day as the full total (the concrete hazard: 2025-12-31 would have posted $60bn instead of
$74.6bn); (2) `_get` now validates the response shape and `daily_takeup` moved inside the try, so a
malformed HTTP-200 degrades to the module's own stated-empty instead of a generic crash-dark row. The
2026-02-17 print clears the $30bn bar by only ~$0.5bn — documented as a descriptive fact, deliberately
NOT tuned away, since the tremble count is a replay output, not an invariant to defend. Final state:
126 tests pass, `replay --check` re-derives the post-STABLE_SINCE rows with zero divergence, no
forbidden string. The line collects daily from the next CI run forward.

### Round 21 — 2026-08-20 (the 5S round: an audit sweeps the whole shop, and the port slide gets its attribution)

Two things happened at once this round: a full three-mode audit (waste / drift / strategic — nine
parallel evidence-first lanes over the whole repo) ran as the round's calibration event, and the
instrument's strongest sustained tier-2 signal to date demanded an attribution ruling. No tier
moves; no new candidates (the frontier was mapped one day ago in R20 — the R9/R16/R19 precedent
for a bookkeeping-weighted round applies).

**The port slide is REAL, and the revision-artifact hypothesis is refuted by measurement.**
`port_throughput` fired four alarm-direction trembles in five business days (08-16 z=-4.4,
08-17 z=-6.8, 08-19 z=-5.2, 08-20 z=-7.3; obs 08-06..08-10) — global port calls fell from July's
~4,800-5,250 band to a 4,055 trough. The obvious suspect was a PortWatch trailing-revision
artifact (newest days provisionally undercounted). Tested directly: re-querying today the same
obs days recorded a week ago shows revisions of **+0 to +34 calls (<1%)** — nowhere near the
10-15% dip. So the slide is real in the source: a broad-based fall across ordinary ports, NOT
chokepoint-concentrated (same-source `chokepoint_breadth`, 28 straits, read z=-0.28 flat through
it), already recovering by obs 08-13/14 (4,648). Cause not identifiable from this data; what the
record can say is measured and now says it. The z will keep firing while the rolling baseline
still remembers July — correct behavior for a change detector.

**fed_srf_takeup's first live contact worked exactly as designed.** The first CI pass after the
R20 build read obs 2026-08-18 — already carried by the seed — and wrote an honest `stale`
republish rather than a duplicate observation. The line runs T+1 by its strict UTC settle rule.
Watch note, not signal: `capital_premium` swung -0.61 → -3.23% in a day (Upbit discount
deepening, z=-2.9) — the benign direction (alarm is premium UP = capital flight), below its bar,
but the sharpest one-day move in its record.

**The audit, in one paragraph each.** WASTE: two completed one-off tools with zero consumers
(`tools/repair_fred_seed.py`, `tools/backfill_components.py`), one abstraction whose second
consumer died (`core/adsb.py`, extracted for cn_flights which R8 retired), two unused imports,
and one explicit keep (`tools/rescore.py`, a twice-used standing repair) — all surfaced for the
user, none deleted (waste is report-only by protocol). DRIFT: the R20 build had left the
dashboard's JS registry without fed_srf_takeup — the third registry (collect.py LINES /
index.html / radar.md) misses a build ~50% of the time historically; fixed, along with the
dashboard's four-domain list still naming navigation (demoted R7), a stablecoin explainer still
describing the pre-R15 rolling-z world, README's hand-copied counts, and this registry's own
drift (the 9-cell stablecoin row, ~8-day PortWatch claims vs the measured 10, the R9 "currently"
paragraph, R11-stamped tier-1 cells — all corrected in this round's edit). STRATEGIC, the three
findings that matter: (1) `charts/*.png` is ~94% of all pack growth (353 blob versions, 12.8MB of
a 13.6MB pack, ~160KB/cycle — the CSVs delta to almost nothing); (2) the dashboard ships every
line's full seeded history on every page load (2.3MB and step-growing with each deep seed);
(3) registry membership is triple-maintained with no sync test. All three are decision points
surfaced to the user, not unilateral changes.

**Standardize: promises now live in a list, not in prose.** The audit found six standing
commitments floating in narrative (the flights 08-31 review, cnh_cny's maturity refresh, the R15
anchored-scale promotion gates, the de-cycling debt, xccy's unfireable "ever" condition) — a
pattern, not an accident. radar.md now carries a **"Pending reviews & tripwires"** block: every
open commitment in one place, each with its trigger, closed only by editing it out with a round
reference. Two new tripwires were declared while formalizing: roll radar-log.md to an archive at
2,000 lines (~R32-35 at the measured ~57 lines/round), and re-probe xccy sourcing every ~10
rounds with a downgrade decision at R30. One timing seam recorded: the 08-16 cnh_cny dark ran
hours before R18's closed-status landed — the first live weekend for `closed` is 08-22/23, and
its verification is on the list.

---

### Round 22 — 2026-08-21 (the credit-redundancy + space sweep)

Three questions, all data-backed: is the credit family redundant, does a space-weather line
belong, and is there other usable NOAA data. No tier moves — but two standing registry claims
were measured FALSE and corrected, one new bar was registered, and one context candidate was
live-probed to build-ready.

**The credit family is ONE factor, and the registry said otherwise.** Two tier-2 credit
challengers carried a note claiming orthogonality to the US HY tier-1 line — em_corp_oas
"orthogonal to US HY", euro_hy_spread "orthogonal to US HY (different central bank)". Measured
against the live tier-1 set on shared z-history, both claims are false:

| challenger | \|max corr\| vs tier-1 | vs which | n |
|---|---|---|---|
| em_corp_oas | **+0.80** | credit_spread | 789 |
| euro_hy_spread | **+0.74** | credit_spread | 783 |
| (em ~ euro) | **+0.86** | — | 783 |
| vix | +0.75 | credit_spread | 194 |
| sofr_iorb_spread | **+0.34** | credit_spread | 35 |

US HY, EM corp and Euro HY move together as a single global credit factor at daily z — the
"different central bank" intuition does not survive contact with the data. Both notes corrected.
This is not a demotion (they were never tier-1) and not a deletion (they earn their tier-2 keep
as breadth/confirmation — the March-2026 x5 resonance day fired on all three agreeing). It is a
**promotion bar**: a new **"single-credit-slot bar"** now lives in Pending reviews — no second
credit-family line may reach tier-1, because it would fail the orthogonality gate AND break the
headline's iid null (Known limits #3 warned of exactly this; R22 measures the number behind the
warning). The genuinely-orthogonal financial challenger is `sofr_iorb_spread` at +0.34 — but
n=35, under the 60-reading bar, so it defers.

**Space weather belongs — as a confounder, not a counted line.** NOAA SWPC's planetary Kp index
is keyless JSON, live-probed R22 (HTTP 200; Kp 2.67 on 2026-08-14; 3-hourly, aggregate to daily
MAX like grid_frequency; reachability wide — quiet ~2 to a G5 storm's Kp 9). But the sun defends
no equilibrium; it IS the exogenous force. So space_weather **fails the guard gate** and can
never be tier-1 or counted — the polar_temp/vix disposition. Its real value is as a
**confounder-subtractor**: two lines already in the registry (gnss_interference, grid_frequency)
have a space-weather failure mode baked in. When GNSS interference spikes, is it geopolitical
jamming or a geomagnetic storm? A Kp line disambiguates — GNSS tremble + calm Kp = real human
interference; both up = the sun. That materially sharpens two existing lines rather than adding
a decorative one. Registered in a NEW radar.md subsection, "Context / confounder candidates (no
guard by design)", separate from the guard-based Backlog because forcing a no-guard line into a
guard-required table is exactly the kind of category error the guard gate exists to prevent.
Disposition: BUILD-READY, pending approval (per the standing rule that building a fetcher needs
a green light; the user asked to evaluate first).

**NOAA is otherwise a guard-gate desert for this instrument.** Swept for other daily keyless
feeds: NOAA's are physical/natural (weather, Mauna Loa CO2, river gauges, seismic). Nature
defends no equilibrium a hidden hand overpowers, so these are context at best and mostly
redundant with polar_temp's planetary-level role. Space weather (SWPC) is the single NOAA feed
that adds orthogonal value, and only as the confounder line above. Recorded so the NOAA search
is not repeated (the marine_war_risk / sovereign_cds non-find pattern).

**Net:** no tier moves; two measured corrections (em_corp_oas, euro_hy_spread orthogonality
claims); one standing bar (single credit slot); one build-ready context candidate (space_weather)
awaiting approval; one sweep closed (NOAA). The instrument's honesty held: a note that claimed
independence was checked against the data and found wanting, and the record now says so.

**Build follow-through (R22, same day).** space_weather shipped end-to-end the moment the
evaluation cleared it, the fed_srf pattern reused wholesale: a live fetcher (NOAA SWPC planetary-K
JSON, 3-hourly → daily MAX, settled to the last complete UTC day so the still-forming nowcast is
never recorded), a seeder off a SEPARATE keyless archive (GFZ Potsdam definitive Kp since 1932,
CC BY 4.0) that emits the same (date, Kp) pairs into the fetcher's OWN daily_max/settled — so the
1932-source history and the SWPC live tail are one measure by construction, not by matching
docstrings. Seed start pinned to 2022-07-27 to align with gnss_interference, the line it most
disambiguates, so the confounder comparison is day-for-day from row one. Scored on the ordinary
rolling z (WINDOW=90) with QUANTUM=1/3 (Kp's reporting resolution) as the scale floor — NOT
anchored: Kp is not a near-constant defended level, it genuinely varies day to day, so "storm"
means unusual-vs-recent, which is exactly the confounder question. Seeded 1,486 days, 1,476
scored, 0 dark, 39 trembles. Validated against ground truth rather than asserted: every up-tremble
is a real G1-G5 storm, and the May-2024 Gannon superstorm (Kp 9, the strongest geomagnetic storm
in two decades) trembles on BOTH peak days (05-10 Kp 8.667 z=4.23, 05-11 Kp 9 z=4.34), as do the
Oct-2024, Mar-2024, and Apr-2023 storms. A handful of DOWN trembles (Kp≈0.3-1 after a
storm-elevated window) are recorded but uncounted — an honest "unusually calm" read, and this line
is uncounted anyway. 9 new tests (aggregation/settle/fetch-degradation/context-wiring), full suite
136 green, replay --check 0 divergence since STABLE_SINCE, registered on the dashboard as a
"space weather (confounder)" context line. The confounder is now live: the next time
gnss_interference or grid_frequency trembles, there is a Kp column beside it to say whether the
Sun or a hand did it.

**The context-line admission bar (formalized R22).** Building space_weather exposed a gap in the
method: tier-2 candidate lines have a stated three-part admission bar, but CONTEXT lines had none —
they were added case by case (vix/gdelt as "felt vs real", polar_temp as a "level" read, now
space_weather as a "confounder"), with no written rule for what earns a context slot. A context
line is exempt from the guard gate by design, but NOT from the survivability liability every
collected source carries, so the bar is now explicit: a context line must NAME the specific
ambiguity it resolves in an existing line, and fall into one of three established roles —
felt-vs-real contrast (gdelt/gdelt_tone/vix), slow-level read (polar_temp), or
confounder-subtractor (space_weather). "It's free to collect" is refused by name; that is the
liability the bar exists to stop. Written into radar.md's tier-2 section. This is why the tropical
cyclone idea is being evaluated against a real test rather than a shrug: it must show it resolves a
NAMED ambiguity (weather-vs-tension in port_throughput/flights) with payoff worth the liability.

**The tropical cyclone probe — a build-ready source, rejected on measured payoff (R22).** The
weather-confounder idea (disambiguate weather- vs tension-driven dips in port_throughput / flights)
got a full exploration: a 10-agent workflow scouted six source families with live web verification,
and the SOURCE question came back solved — two independent keyless, all-basin feeds, both fetched
and verified 2026-08-20: GDACS `EVENTS4APP` GeoJSON (live, ~hourly, every active global TC with
km/h intensity, CORS-open) and IBTrACS v04r01 `since1980.list` CSV at NCEI (seed, dense 6-hourly
best-track 1980→present; `last3years.csv` as the 90-day window; `ALL` to 1842). Both close the
West-Pacific gap that killed NHC/CPHC (SAUDEL-26, a live WP typhoon, is in the feed). The design
question came back solved too: a port/hub-**gated worst-of** (strongest storm within ~500 km of a
fixed top-20 hub list) is a MAX-form that kills the dilution and frame-churn that block a global
count or ACE sum. The workflow returned **BUILD-READY, clears the admission bar**.

Then the load-bearing claim was MEASURED, and it failed. The workflow's case rested on "a typhoon
over East-Asian airspace dips flights — full real-time payoff" (flights being near-real-time and,
crucially, COUNTED). But it never measured the magnitude. Measured: E-Asia/Japan is ~8% of the
flights line (~126 of ~1496 aircraft), and flights' own robust scale is Qn ≈ 199 aircraft — so the
ENTIRE Japanese airspace going dark moves flights only **z=0.63**, nowhere near the |z|>3 alarm.
port_throughput is worse: a global sum of 2065 ports, Qn ≈ 245 calls, so a full Shanghai+Ningbo
closure (~120 calls) moves it **z=0.49**. Both lines are diluted below their own alarm by the same
mechanism — the storm's footprint is a small slice of a global aggregate whose intrinsic daily
noise is larger than the whole slice. So a cyclone essentially never creates a weather-tremble in
either line, and a confounder-subtractor with nothing to subtract is decoration. It fails the
admission bar's PAYOFF half even though it passes the "names an ambiguity" half.

This is the precise opposite of space_weather, and the contrast is the lesson: a geomagnetic storm
degrades the WHOLE global GNSS ratio at once (gnss_interference is globally sensitive to its
confounder — undiluted), which is why Kp cleared the same bar the same round. A confounder only
earns its keep when the line it serves is GLOBALLY sensitive to the confounding force, not locally.
Recorded in Rejected with the sources banked and a revival precondition (a globally-cyclone-
sensitive line, or per-hub sub-lines — a Shanghai-only port line, a Japan-only flights line — where
the storm isn't diluted). And a method note for the log: a scouting workflow returned BUILD-READY on
qualitative reasoning; the discipline that caught it was refusing to build until the one number that
mattered was on the table. Adversarial measurement over plausible narrative, every time.

---

### Round 23 — 2026-08-25 (the false-alarm round)

A metrics refresh that turned into an adjudication. On 2026-08-24 the tier-1 line net_outages spiked
to 12 countries dark (z=4.69, its 58th alarm day) — the first tier-1 tremble since the 07-05 flights
artifact, breaking a 45-day calm. The cluster (Cambodia, Cape Verde, Indonesia, Japan, Maldives,
Mexico, Myanmar, New Zealand, Singapore, Thailand, Tunisia, Viet Nam) LOOKED like a regional
submarine-cable disruption — heavy in SE Asia + Indian Ocean + Pacific. A 5-agent probe (re-query
IODA / web-attribute / cable-infrastructure / tremor-internal cross-check / adversarial synthesis)
refuted that hypothesis three independent ways and returned **likely-IODA-artifact, high confidence**.
The cable story was mine; the data killed it. That is the round.

**The evidence that it was a FALSE ALARM (a real IODA reading of a non-real-world event):**
- **Timing (the smoking gun).** Re-querying IODA's own per-event data: 10 of the 12 (Indonesia,
  Maldives, Cambodia, Singapore, Thailand, Myanmar, Mexico, Japan, Vietnam, New Zealand) are each a
  SINGLE brief ping-slash24 event with onsets synchronized into a 20-minute window (01:00–01:20 UTC,
  23 Aug), all 30–60 min long, all recovered by ~02:00Z, low tightly-banded magnitudes (692–1517),
  no BGP corroboration. A 40-minute blip-and-recover that simultaneously hits the E. Pacific (Mexico),
  NW Pacific (Japan), SW Pacific (NZ), Indian Ocean (Maldives) and SE Asia cannot be one cable — no
  system spans those basins, and cuts cause sustained (hours–weeks) coherent outages, not synchronized
  global blips. Cross-basin 20-minute onset synchrony is the common-mode signature of IODA's own
  active-probing vantage.
- **Windowing instability.** The trailing-24h count is latency-driven: re-querying the exact window
  that produced the reading returns only 4 (Tunisia, Cape Verde, Syria, Gabon); the 12 came in via
  IODA's ~24h detection latency and settled out. The 08-25 recorded row (4 countries: Cape Verde,
  Gabon, Syria, Tunisia) equals that settled set — the two genuine survivors are the sustained
  multi-day AFRICAN outages (Cape Verde 13 events to 13.3h; Tunisia 14 events), which merely co-occurred.
- **Infrastructure.** The SE-Asia core six (SG/TH/VN/KH/MM/ID) do share systems (AAE-1 etc.), but Japan,
  NZ and the Maldives are on non-overlapping cable families; reproducing the exact set needs 4+
  simultaneous independent cuts, which do not heal in an hour.
- **Web.** No dated report of any cable cut or regional outage on 2026-08-24; a live outage tracker
  affirmatively denies any submarine-cable incident Aug 23–25 (the date is not a coverage gap — cloud
  incidents that day are documented).
- **Cross-check.** net_outages moved essentially ALONE: gnss (z1.6, but 2-day-lagged and global),
  grid_frequency (z1.0, Nordic), flights (z0.6, Japan component in-range) do not corroborate a physical
  event, and space_weather was quiet (Kp 2), ruling out a solar common cause. A single line moving
  alone is a LOCAL event by the thesis — and here "local" resolves to the sensor, not the world.

**The guard gap this exposed.** Annotation 97 (2026-08-04) already documented twelve IODA "monitor
swept" self-outage days and installed a guard: `monitor_swept` fires only at hits≥100 AND
hits/entities≥0.8 — deliberately a conjunction, so it would never refuse a genuine catastrophe, and its
nearest non-selected day was 45 countries at ratio 0.45. The 08-24 event is a NEW, smaller sibling:
a 12-country (~5% share) synchronized-onset common-mode blip that sails cleanly under both thresholds
yet is just as much an artifact. Verified in-repo: `_SWEEP_MIN_COUNTRIES=100`, `_SWEEP_MIN_SHARE=0.8`.
So a Pending-review item is queued — a finer filter keyed on onset-synchrony + BGP-corroboration +
single-window transience, before a spike of this shape counts as world-signal. Building it is a fetcher
change and needs approval; net_outages is NOT demoted (its 37 real episodes stand, and the artifact is
now caught and documented), but a second such artifact before the fix reopens its tier-1 status.

**The rest of the refresh.** cnh_cny is the most active tier-1 line today (z−2.49, raw −4, benign DOWN)
but is still n=48<60 — maturity refresh keeps waiting; record range is −45..143, all 4 trembles benign
DOWN. The closed-status first-live-weekend tripwire: 08-23 (Sun) correctly read `closed`; 08-22 (Sat)
re-scored Friday's close (raw 83, z−0.24) because the weekend guard keys on the newer leg being Sat/Sun
and Saturday morning still holds two Friday timestamps — follow-up queued. flights' pre-committed review
holds to 08-31 (n=55 now, no new alarm since the 07-05 artifact). No tier moves.

**Method note.** This is the second round running where a scouting workflow proposed the exciting story
(R22 cyclone BUILD-READY; R23 subsea-cable event) and the discipline that held was refusing to write it
until the load-bearing claim was measured. Here the measurement was IODA's own per-event onset timing,
and it turned a 12-country "regional cable cut" into a 40-minute measurement hiccup. Attribution is a
claim about evidence, not about how good the story is — the same lesson annotation 102 recorded when it
withdrew the 2022-03-02 Ukraine attribution.

---

### Round 23.1 — 2026-08-25 (settle + last-mile tightening)

An implementation round, not an adjudication: R23 diagnosed the 08-24 tier-1 false alarm as an IODA
latency artifact; R23.1 fixes it at the source, and folds in the low-risk hygiene items a holistic
review surfaced. Brainstormed, plan-reviewed by a fresh pass that caught eight bugs before any code was
written (a gate that would have bricked every collection, a docs/data test that would self-brick, a
wrong stale-claim in a test, and more) — the discipline that made this round cheap was refusing to
implement until the plan was adversarially read.

**The settle fix.** `net_outages` counted a trailing 24h window ending at collection time; its last hours
sat inside IODA's ~24h detection latency, which retimes and inflates the count. The live fetcher now
counts a COMPLETED window ending at the most recent 22:00:00Z at least a day old (`_settled_window`),
`obs_date` = that day — the exact convention the seed already used (`_WINDOW_HOUR=22`), so history and the
live tail are one measure. This is the GENERAL fix — it removes the whole latency-injection class — and it
was chosen over the R23-queued onset-synchrony/BGP/transience filter precisely because that filter was
fitted to the 08-24 signature (the "tuned to the last crisis" failure the ethos names). `monitor_swept`
is untouched (it catches ≥100-country vantage-loss sweeps, a different class; the two are complementary).

**Validated against the record before shipping** (live IODA re-queries, 2026-08-25): the 08-24 settled
window returns 4 (Cape Verde, Gabon, Syria, Tunisia) vs the live 12 → the false alarm is dropped; and
7 historical single-day alarms reproduce BYTE-EXACT (2022-03-02=45, 2023-06-18=40, 2024-10-03=44,
2025-04-30=41, 2026-04-08=15, 2026-03-06=11, 2025-06-19=9) — big and small alike, so settle refuses no
real episode. The record's 43 episodes are 37 isolated single-days + 6 multi-day runs; the seed (97% of
rows) was already settled, so the only unsettled stretch is 2026-07-10 → 2026-08-25, which held exactly
one alarm — the 08-24 artifact. The decisive argument is regime consistency, not the n=1 adjudication:
the live fetcher had been measuring a different quantity (latency-inflated) than the settled baseline it
was judged against. STABLE_SINCE untouched, `replay --check` stays 0-divergence (settle changes only the
live fetcher forward; obs_date is data replayed from the CSV). The 08-24 row STAYS forward-only (the raw
12 is the v2 instrument's true reading, not a bug — not rescore-eligible), annotated as the artifact.
The residual risk (IODA's "~24h" is typical, not a bound; the fresh-settled-vs-archive bridge is n=1) is
held by a standing reconciliation tripwire in Pending-reviews, which also carries R23's clause forward.
Cost: net_outages goes from zero-lag to ~1-day-lagged, inside the tier-1 ≤2-day freshness bar (gnss
already runs 2-day-lagged at tier-1); the TIER comment is updated to say so.

**The reachability gate, amended.** A young line whose own calm record is too shallow to contain its
alarm now passes if the alarm is reachable under a documented REFERENCE REGIME — real historical episodes
of the guarded quantity — the same baseline-relativity the gate already declared, made explicit. cnh_cny
passes on it (its UP alarm needs +227 pips vs a 52-obs high of 143, but real capital-flight episodes have
run hundreds of pips); re-checked at n≥60. This closes the R23 open fork.

**eu_gas_storage — probed and off eternal parking.** AGSI+ answered HTTP 200 with a registered key (EU
aggregate daily fill 62.99% on 2026-08-23, injection/withdrawal/full% fields, ~2-day lag), key set locally
and as a CI Secret. Marked BUILD-READY, and named the registry's FIRST LOAD-BEARING key (no keyless
fallback, unlike the optional FRED/FINGRID keys); the "keyless daily fetcher" build criterion is amended
to allow a declared load-bearing key as a stated exception. Building the line (fetcher + a vendored
365-entry seasonal-normal table for the de-cycling) is its own next round.

**Two integrity tests.** A docs/data SUBSET gate (`docs/data ⊆ MIRRORED ∪ {stuck.csv}`) closes the hole
that `stuck_panel.py` writes around the allow-list by design, without the equality version that would brick
the first collect after any new fetcher. A pre-collect LINES-invariant gate asserts ¬(QUANTUM ∧
MATERIALITY), a present ANOMALY_DIRECTION, and unique LINE names — catching a misdeclared module before its
AssertionError in `score_row` can abort a whole day's run. Plus: the covBlind field-of-view sentence drops
"Latin America" (fx_parallel_premium is a scored Argentina line), and the round index's R22/R23 ordering
glitch is corrected. No tier moves.

---

### Round 23.2 — 2026-08-26 (the settle claim, corrected by its own tripwire)

The reconciliation tripwire, built and first-run the same day, corrected R23.1's overstated claim
before CI ever exercised it. R23.1 said settling to a completed window "removes the whole
latency-injection class." The first-run seam audit re-queried the 2026-07-10 → 08-25 unsettled
stretch against IODA's now-settled windows and found the load-bearing counterexample: the 08-24
twelve-country synchronized-onset cluster is a stable set of ping-slash24 events at ~08-23 01:00Z,
so it lives in the SETTLED window ending 08-23 22:00Z — the exact same twelve countries (Cambodia,
Indonesia, Japan, Maldives, Myanmar, New Zealand, Singapore, Thailand, Viet Nam, plus Cape Verde,
Mexico, Tunisia) — while the window ending 08-24 22:00Z holds only the four genuine survivors.
Settle relocates the cluster to its true date and makes the count stable and reproducible; it does
NOT recognize it as an artifact. A future synchronized-onset common-mode cluster would alarm on its
own date under settle — the same tremble the trailing window produced, now stably timed rather than
eliminated.

Corrected: settle's benefit is count-stability and seed-alignment, not artifact-elimination; the
synchronized-onset class stays DETECT-AND-ADJUDICATE (the reconciliation tripwire flags a settled
tremble, the R23 five-agent playbook attributes it). Settle is kept — the trailing window was
genuinely unstable, the seam audit showing old rows and settled windows disagreeing day to day —
and net_outages is not demoted (its 37 real episodes stand). The lesson is the tool's, not the
claim's: insisting on a reconciliation tripwire, over the objection that settle had "closed" the
class, is exactly what caught the class still open. No tier moves.

---

### Round 24 — 2026-08-26 (park eu_gas, and a state check)

**eu_gas_storage, parked on the reachability gate.** The AGSI+ source is confirmed and keyed
(HTTP 200, EU daily fill, ~2-day lag; key banked locally + as a CI Secret), so sourcing is no
longer the blocker. The metric is. The natural line — fill DEVIATION from the seasonal-normal
full% (day-of-year median over 3,889 daily points, 2016-2026) — fails reachability: the deviation's
own normal spread is ±14pp (p5 −14.4, p95 +22.2) while the worst downside in ten years is only
~−16pp. No MATERIALITY threads that needle: an alarm reachable at ≤ −16pp fires on ordinary ±14pp
variation, and a clean −3z alarm lands near −33pp, which has never occurred. The cause is
structural: EU storage LEVEL is a defended-holds quantity. The 2022 war-onset crisis — the worst
gas shock on the record — dented fill by only −9pp in March and refilled to ~95% by November via
record prices and demand destruction; the stress showed in PRICE, not in the level, because the
guard held. The seasonal baseline is additionally regime-confounded: the post-2022 90%-by-November
mandate lifted 2023-25 fill structurally, dragging the ten-year median up. This is the
tropical_cyclone shape again — an excellent source whose natural metric does not clear a gate.
Un-parking needs a cleaner guard: deviation from the EU regulatory TARGET PATH (the actual defended
trajectory of intermediate fill mandates), not a blended seasonal median — more work, uncertain
payoff, deferred. One live fact is worth carrying regardless: EU storage in 2026 sits at −15pp
(63.3% against a 78.4% seasonal normal), the ten-year deviation low — genuinely running behind,
a candidate line for the dashboard's field-of-view or a briefing note even though it is not scored.

**State check after the R23.1/R23.2 settle work.** The headline is calm: resonance 0 on 2026-08-26,
a two-day zero streak; flights (z 0.72), credit_spread (2.69%, z −0.94) and net_outages (2 countries,
z 0) all quiet; the felt layer calm too (VIX z −0.74, GDELT conflict z −0.90, tone z +0.90). The one
mover is cnh_cny at −43 pips, z −3.24 — its FIFTH benign DOWN tremble (offshore yuan stronger than
onshore, the opposite of the capital-flight direction the line guards), so uncounted, consistent
with the reachability-gate amendment that kept it tier-1 on a cited reference regime. Its scored n
is climbing toward the 60-reading maturity review, where the reference-regime evidence and the
benign-tremble recount both come due. net_outages runs on its settled window now, its artifact class
documented as detect-and-adjudicate; the reconciliation tripwire is a standing round-time check. No
tier moves.

---

### Round 25 — 2026-09-01 (the flights pre-committed review — retained, its two alarms share one clock)

The R11 pre-commitment came due: **flights** review "due 2026-08-31 (de-cycling engages, n≥60):
demote if the replayed episode-rate Wilson lower bound exceeds 2%, or immediately on the next
unadjudicable alarm." A tremble had fired on 2026-08-28 (z=−3.05, DOWN) — the "next alarm" — so the
review had a live case to adjudicate. It was run this round and **externally audited** (an external
model, GO-WITH-CHANGES; its three must-fixes are folded into what follows — the audit corrected a
factual error in the first draft, supplied the decisive evidence, and reframed an overstated claim).

**Condition (a) — the replayed episode-rate. NOT met.** flights has 62 scored readings; the
current-rule replay (`tools/replay.py`) returns exactly two alarm-direction trembles — 2026-07-05
(−5.73, the long-adjudicated artifact) and 2026-08-28 (−3.05) — two isolated episodes. Point rate
3.23%, **Wilson 95% lower bound 0.89%** (one-sided LB 1.07%), both under the 2% bar. Stated as
replayed, per the clause's wording.

**Condition (b) — an unadjudicable alarm. NOT met; the 08-28 alarm is ADJUDICATED.** flights reads a
CONCURRENT SNAPSHOT of aircraft over four fixed airspaces, and its baseline assumes the snapshot is
taken at the same time each day (the fetcher docstring says so). It is not: the CI cron is fixed at
`0 22 * * *`, but GitHub-Actions queue latency drifts the actual sample hour, and on 2026-08-27/28/29
it slipped to **02.8 / 5.9 / 3.4 Z** — four to seven hours off the ~22.5Z baseline median, into the
diurnal trough (US East asleep, Europe pre-peak). The three off-hour samples ARE the three lowest
recent counts (1095 / 1035 / 1019); all 31 near-baseline (21–01.5Z) samples read 1230–1908 with a
minimum z of −2.31 and never alarmed. Sample hour separates the trembling regime from calm perfectly.

The decisive proof is the **intraday sampler** — the very instrument clause (b) named. On the alarm
day, 2026-08-28T23:22Z (baseline hour) read **1660**, normal; 08-27T23:28Z read 1398 and
08-29T22:11Z read 1562. The airspaces were measurably normal at the baseline hour on all three low
days — the alarm is the clock, proven, not inferred. The 08-28 daily snapshot's regional mix
(Europe 546 UP, Asia 221 UP, US East 86) is a ~06Z dawn signature, and two regions rising is
impossible under any real flight-suppressing event. Adjudicated as a sample-hour artifact.

**Verdict: RETAINED.** Neither pre-committed demotion condition fired, and "a line is never demoted
without evidence" — the evidence indicts the CI schedule, not the guard. flights is not inert:
07-22 (FAA ground stops, replays −3.01) and 07-19 (−3.41) are real events read correctly just under
the bar. But the honest record is that BOTH of flights' |z|>3 alarms are now artifacts, and the
08-28 mechanism is structural.

**One factual correction folded in.** The first draft claimed weekday de-cycling had not yet
engaged (reasoning from scored n=62 vs `DECYCLE_MIN=70`). Wrong: the gate counts WINDOW readings
(including the ten warming-up rows), so window depth reached 70 on 2026-08-31 and de-cycling engaged
exactly as R11 foretold ("row 71, verified through the scoring path"). The 08-28 alarm was scored at
window-depth 67, before de-cycling; 08-31 and 09-01 were scored WITH it and still read hour-depressed
— because weekday de-cycling removes the WEEKDAY rhythm, which is orthogonal to an HOUR-of-day
confound. De-cycling was never going to fix this.

**The fix (queued, needs approval).** Pinning the CI sample hour is not achievable — the delay is
the platform's. The smallest honest fix is a **sample-hour guard**: a reading sampled more than ~Nh
from the 22:00Z target is written dark-with-reason rather than scored, consistent with the
side-channel firewall (the scorer must NOT read intraday.csv) and with flights' own "a partial sum
would look like a flight drop → write empty" precedent. Recorded with an **anti-loophole clause**: a
repeat of this same adjudicated artifact class after the fix ships is itself demotion-disqualifying —
an adjudicable-but-recurring artifact must not shield the line forever. The drift is ONGOING (the
08-30/31 daily samples still ran 1.8–3h late and hour-depressed, recovering only in intraday —
08-30T22:18Z read 1731), so the fix is urgent, not leisurely. Also worth recording: the 07-05
artifact (945, a Sunday) sits in the weekday-range envelope and suppressed the replayed 07-19 real
event (−3.41 vs bar 3.34) — a measured instance of one artifact contaminating a real detection.

**The rest of the round.** The net_outages reconciliation tripwire ran (live, a round-time check):

    row          win-end      stored settled
    2026-07-09   2026-07-09        2       2
    2026-08-27   2026-08-25        2       2
    2026-08-28   2026-08-26        8       8
    2026-08-29   2026-08-27        4       4
    2026-08-30   2026-08-28        3       3
    2026-08-31   2026-08-29        3       3
    2026-09-01   2026-08-30        4       4
    7 rows checked, 0 mismatch(es) >= 3 countries.

Zero mismatches — the settle holds, and the 08-26 window's 8 countries (z=2.81, sub-threshold, did
not tremble) is a STABLE real reading, not a trailing-window inflation. cnh_cny is at n=52 scored
(<60), still short of the maturity review. No new candidate is due — the round was the review. No
tier moves.

---

### Round 25.1 — 2026-09-01 (the flights sample-hour fix, shipped — sleep-to-target)

R25 retained flights and queued a fix for the sample-hour artifact. This ships it, after two
external-model review rounds that killed two earlier designs. The problem, restated at its root:
flights is a concurrent SNAPSHOT scored against a baseline built at a fixed hour, so a mistimed
sample measures the diurnal cycle (aircraft aloft swing ~150/hour ≈ 0.9z around the target), not
the world — the 2026-08-28 z=−3.05 tremble was a run delayed by GitHub-Actions queue latency into
the 05:54Z trough.

The load-bearing fact, measured over 34 days: **the delay is one-sided — always late, never early
(+0.44h to +7.91h).** So the fix does not detect, discard, or correct a mistimed sample; it makes
the sample LAND on target. The daily workflow now schedules early (`0 18 * * *`) and SLEEPS until
22:30:00Z before collecting (only when 22:30Z is 0–4.5h ahead, so an overnight-wrapped delay never
sleeps ~20h). Whenever the queue delay is inside the 4.5h head-start — all 31 non-trough days of the
record — the sample lands exactly at 22:30Z. 22:30Z is the historical effective sample hour (the
record's samples cluster there, minimum 22:26; flights was never once sampled at 22:00), so the
baseline is continuous — no reseed. A declarative backstop guard (`collect.py::apply_sample_guard`,
read via `flights.SAMPLE_TARGET_UTC_H=22.5` / `SAMPLE_TOL_H=1.5`) darks any reading still sampled
more than 1.5h off on a run delayed past the sleep window (~1/34). The guard decision is frozen into
the stored raw as a dark row, never a scoring attribute, so replay stays 0-divergence and
STABLE_SINCE is untouched; a test binds the CI sleep target to the module constant so the two cannot
silently diverge.

Two designs were rejected on the way here, both correctly. A **discard-guard** (dark every off-hour
day) throws away coverage that already exists — on 08-28 a good 23:22Z reading of 1660 sits in the
intraday record — and leaves the +2–3.5h regime bias scored. A **settle-from-intraday** design
(compose the daily value from the intraday samples) looked elegant but the data broke it: at the
specified ±1h tolerance only 11 of 34 days have a usable sample (68% dark), its settle-day formula
lost observations under the exact delays it fought, it froze the components bank (colliding with the
level-layer→flights pending item), it made the "deliberately inert" intraday sampler load-bearing,
and it cost flights its zero-lag. Sleep-to-target fixes the same root cause with none of that: no
firewall change, no lag, no seam, no sampler dependency, one workflow edit plus a declarative guard.

Validated: 15 new tests (green); full suite 162 tests; `replay.py --check` flights 0-divergence
since 2026-08-17; the sleep shell logic correct on GitHub GNU-date including the overnight wrap; a
34-day timing simulation — 31/34 days land exactly at 22:30Z, the 08-28 false tremble darks, the
other two troughs (08-27/29) sample near-target and score without trembling, and no clean day newly
darkens. Orphaned comments in daily.yml and core/clock.py corrected. STILL OPEN (Pending reviews): a
re-review after an observation window, since the 18Z cron's OWN delay distribution is unmeasured (2pm
ET may differ) — the failure mode is benign (delays ≤4.5h still land on target, >6h dark). The R25
anti-loophole clause stands: a repeat of this adjudicated artifact class after the fix is itself
demotion-disqualifying. No tier moves.

### Round 26 — 2026-09-04 (the P2–P6 zero-debt remainder: guards, generators, and the customer surface)

The zero-debt plan's safety phases (P0/P1) shipped earlier; this round is the mechanical
remainder — P2 through P6 — executed across 2026-09-03 and 2026-09-04 as some two dozen
reviewed commits, each task landed and reviewed on its own. Nothing here is a reading. No line trembled,
no tier moved, no scoring rule changed: this is instrument hygiene — single sources of truth,
mechanical guards for every hand-maintained fact, and two corrections to what the dashboard
told a reader. Replay stays 0-divergence and STABLE_SINCE is untouched throughout, because
none of it touches how a row is scored.

**Single sources of truth.** The alarm predicate (trembling in the line's own alarming
direction) now has ONE home in `collect.py`, consumed by both `episodes.py` and — as its
deliberately independent re-derivation — `replay.py`; the third hand-copy is gone. Scoring
constants are read from `core/normalize.py` rather than re-typed. `net_outages` gained one
settled-window definition (`window_for`), proven against an exhaustive hourly sweep. The FRED
series ids are declared once and read by the seeders; the collector speaks with one
User-Agent (cnh_cny's browser variant preserved as `COMPAT_HEADERS`). The `STABLE_SINCE`
ledger comment, which had stopped at the 2026-08-04 mark while the value moved to 2026-08-17,
now records the Round 18 closed/dark split and its two grandfathered weekend rows.

**A lint layer that never costs a collection day.** Five source-vs-source checks, all
stdlib-only so they run on push CI (which installs nothing) and never in the pre-collect gate:
`lint_ssot` keeps the alarm predicate and the scoring constants in their owning module only;
`lint_registry` binds `radar.md`'s registry table to `collect.LINES` and the round index;
`lint_workflows` parses and shell-checks every workflow file; `lint_pending` (kept stdlib-only
by deferring the collect/seedlib imports) enforces the pending-item grammar; `lint_public_surface`
binds the dashboard's status vocabulary to `normalize`.

**Generators and tools.** `episodes.py --markdown` now emits `radar-metrics.md` and the
unread `data/episodes.json` is retired. `pending.py` gives every pre-committed review a
machine-parseable tag (`[opened R<n> · owner R<n> · fires: <predicate>]`) with an overdue
lint, so a lapsed review fails loudly instead of sitting in prose. `roll_radar_log.py` is
built with a byte-identity guarantee against the held original — not yet fired (this log is
1835 lines, under its 2000-line threshold, expected ~R27). A `calibration.yml` workflow now
schedules the check that regenerates the vendored tremble-threshold table, the one place the
dev-only numpy/scipy deps are exercised.

**Audits (post-commit, an alarm not a gate).** `audit_registry` adds a retracted-phrase scan
(a phrase the record has retracted must not reappear live), the QUANTUM-floor invariant, and a
no-overdue-pending check. `audit_charts` caps each committed chart PNG at a fixed per-file byte
budget. `audit_public_surface` asserts the dashboard's mirrored files are byte-identical to
their `data/` sources and that every `GAP_STATUSES` status carries no reading in the record.

**Retracted claims, corrected at the source.** The retracted-phrase scan landed beside the
corrections it exists to enforce: two live surfaces still carried claims the record had
already retracted. The `gnss_interference` line's "never moved" copy — on the dashboard and
in the fetcher's own docstring — is corrected to the z=+2.87 its July window reaches on the
four-year baseline (a global ratio diluted by regional jamming, not a line that stayed flat),
and `radar.md`'s stale `net_outages` settle claim is fixed. Each retraction is recorded as an
annotation row carrying the exact phrase, which the scan now guards against silently
reappearing anywhere live.

**The customer surface — two things the dashboard was getting wrong.** First, a tier-2
watchlist line that goes dark now says so. A line dark for two or more consecutive collections
renders a "NO DATA" gap chip instead of the same calm as a scoring line — the live
`hkma_aggr_balance` line, dark five straight days (2026-08-30 to 09-03 on HTTP 502 and read
timeouts), had been rendering calm, indistinguishable from a quiet reading. Second, the
credit-independence copy is corrected to what Round 22 measured. The old text called
`em_corp_oas` "a distinct guard, a distinct signal" and said `euro_hy_spread` fires "while the
US line sleeps"; the record measures the opposite — |max corr| **+0.80** for EM corp vs
`credit_spread` (n=789), **+0.74** for Euro HY vs `credit_spread` (n=783) and **+0.86** Euro
HY vs EM corp: US high-yield, EM corp and Euro HY are ONE global credit factor at daily z, so
both stay tier-2 for breadth and confirmation and neither is a tier-1 promotion candidate
(promoting a redundant credit line would break the headline count's independence assumption).
A cadence note now warns that `cnh_cny` posts no weekend session, so a reader expecting ~7
points a week from that line typically sees closer to 5. The render-smoke harness gained a real
cookie slot so the Chinese-language render path actually executes under test, plus the modal
exports it was missing.

**Smaller charts.** `render.py` now quantizes each chart to a 64-colour palette (MEDIANCUT)
after writing it, dropping the largest from 61,594 to 24,886 bytes (the overview from 19,930 to
6,776); `audit_charts`'s per-file cap tightens from 70,000 to 40,000. `pillow` is pinned to
`12.3.0` — the version `matplotlib==3.9.0` already resolves transitively on the CI runner, so
the pin freezes what is installed without changing it.

Validated: the full suite is green — 260 gate tests, 49 lint tests (stdlib-only, confirmed in a
bare virtualenv), 17 audit tests; `replay.py --check` reports 412 rows, 0 diverged, 0 diverged
since STABLE_SINCE=2026-08-17; `render_smoke.js` passes in both languages with the zh path now
genuinely exercised. This entry itself writes no annotation row; the round's three annotation
rows — the retraction markers above — landed earlier, in the commit that made the live
corrections they describe. Still open: `roll_radar_log` awaits the
2000-line threshold (~R27); the flights cron-delay re-review carried from R25.1 stands; the
cnh_cny maturity review fires at n≥60. No tier moves.

### Round 27 — 2026-09-08 (the corroboration probe: net_outages kept under a tightened, named-weaker standard)

The 2026-09-04 net_outages spike (15 countries, z=6.098) and its 2026-09-05 recurrence (13, z=5.160)
were IODA active-probing common-mode artifacts — synchronized ping-slash24-only batches, no BGP or
network-telescope corroboration — and cleared on 2026-09-06, a two-day transient. Round 26's served
synchrony lean flagged both the day they fired.

The open question: could a CORROBORATED sibling line — counting only countries where ping-slash24 AND
bgp/merit-nt agree — tell a real event from this artifact class, and so serve as an exit path from
net_outages' repeated adjudications? tools/probe_ioda_corroboration.py re-queried every one of the ~60
historical alarm windows live and labeled each with its raw ping count, corroborated count, and
common-mode lean. The answer is NO. Corroboration is sparse on every band and its count cannot be told
from calm: calm days corroborate a median of 0 (max 4), alarm days a median of 2 (common-mode-lean) to
4 (ok-lean); requiring corroboration deflates both bands into the background and zeroes artifact-shaped
days whether or not they are real. So the corroborated line is CUT — measured dead, not deferred.
Banking per-country datasource components on the tier-1 line remains worthwhile as ADJUDICATION
EVIDENCE, not as a filter. No exit path is named.

With no fix (R23.2 established that settle cannot close the class) and no exit (this probe),
net_outages is RETAINED under a named weaker standard — it is the only global-communications
candidate, and its evidence is rate-confirmed but unattributed — with the demotion clause tightened to
three disqualifying conditions, each alone sending it to tier-2 with the slot left empty and disclosed:
(a) an UNADJUDICABLE instance the R23 playbook cannot attribute after a genuine attempt; (b) any alarm
day left UNADJUDICATED 14 days after it is served; (c) REACH — by 2026-10-15 adjudicate the 8 largest
readings, and if none survives as a real world event the line demotes on the reachability standard
cnh_cny was held to at R13/R23.1 (a cited reference regime counts; a rate does not). Per recurrence the
round now reports the class's adjudicated-artifact rate on the live settled series (2 episodes in 58
days), not the seed-diluted whole record.

Three annotations landed. 2026-09-05 net_outages `artifact` adjudicates the recurrence, so clause (b)
opens with no standing debt. 2026-09-06 `method` records that corroboration was measured and is not a
filter, with the evidence base: 24 of 60 alarm days, and 7 of the 8 largest readings, lean
common-mode. 2026-09-06 `correction` withdraws Round 11's "2025 Iberian blackout" attribution — that
alarm (2025-04-30, z=18.3) re-queries 0/41 corroborated and 32/32 synchronized ping-only, an artifact;
the real blackout day (2025-04-28) read 7 countries, sub-alarm. It is the same calendar-adjacency error
as the withdrawn 2022-03-02 Ukraine attribution.

Validated: the probe was a concurrent re-fetch replayed through the unmodified reconcile classifier,
not one sequential invocation, and its read was independently confirmed. Full suite green (gate, lint
stdlib-only in a bare venv, replay 0-divergence, annotations mirror byte-identical). No tier moves.
Still open and SEPARATE: the control_daylength canary is raising a false positive as the autumn equinox
approaches — the audit's CBM day-length approximation disagrees with the source by more than its
one-minute tolerance (issue #3), a check flaw, not a pipeline date bug; a fix is designed, not applied.

### Round 28 — 2026-09-08 (the reach adjudication: net_outages demoted to tier-2, plus two spine fixes)

Three items, recorded here in one entry, the demotion last and longest.

① The control_daylength canary (issue #3, closed). The daily audit that guards the pipeline canary was
raising a false positive as the autumn equinox approached: its day-length check disagreed with the source
(sunrise-sunset.org) by more than its one-minute tolerance. The cause was a check flaw, not a pipeline date
bug. The audit reconstructed day length from astronomical truth (geometric sunrise/sunset at the horizon),
while the SOURCE computes it from Schlyter's sunriset model with an ≈1.10° effective depression (refraction
plus the sun's radius); near an equinox, where day length changes fastest, that definitional gap exceeds a
minute. The check now reproduces the source's own model, so it measures the pipeline rather than the gap
between two day-length definitions. A second flaw rode with it: the closest-day lookup used a strict argmin,
which near a solstice — where day length is flat — can jump to the wrong day; a margin closest-day check
replaces it (solstice-safe). No reading changes; the control line's forward-only record stands.

② A1 spine hardening. A fetcher that returned a non-numeric or non-finite value (a None coerced to a
string, a NaN, an inf) could either abort the whole collection run or be stored verbatim as 'nan'/'inf'
into the forward-only record — a value no later reader could score and no re-derivation could reproduce.
The collect() boundary now coerces a non-finite fetcher value to a darkened reading (no raw_value, a stated
reason): one bad line darks itself for the day, the run completes, and the record never ingests a
non-finite number. Guarded by finiteness tests on the collect path and an audit over every stored
raw_value and z_score.

③ The reach adjudication, and the demotion it forced. R27 put net_outages under a named weaker standard
with a reach deadline (condition (c)): by 2026-10-15, adjudicate the 8 largest readings under the R23
playbook, and if none survives as a cited real world event, demote to tier-2. R28 discharged that deadline
early. The evidence is a live IODA re-query through the reconcile classifier (per-country datasource, onset,
corroboration) plus a multi-source attribution search (NetBlocks, Cloudflare Radar quarterly disruption
summaries, ThousandEyes/Network World, Kentik, ISOC Pulse, Access Now, Wikipedia), both completed
2026-09-08 and archived at data/archive/ioda_8largest_requery_2026-09-08.csv.

None of the eight is a cited world event. Seven (2022-03-02, 2022-03-11, 2023-06-18, 2023-09-06, 2025-03-27,
2025-04-30, 2025-11-29) are common-mode active-probing artifacts — large synchronized ping-slash24-only
batches with sparse corroboration, the signature the R23 playbook names. The 2025-04-30 (41) and 2022-03-02
(45) readings were the withdrawn Iberian and Ukraine calendar-adjacency attributions; the search re-confirmed
the real events fall on other days. The 2023-09-06 reading is the sharpest test: a real Cogent Communications
backbone outage (~57 min, ~17 countries, ThousandEyes via Network World) did fall on that date, but the IODA
reading does not correspond to it — 2 of 30 corroborated, a 22-country synchronized ping-only batch bracketed
by baseline; a backbone/transit withdrawal would corroborate on BGP, and this did not. Citing Cogent would
repeat the calendar-adjacency error. The Cogent linchpin is on the record, not just asserted by mechanism:
the 22-country synchronized batch (archived in batch_countries) is predominantly Caribbean/Pacific/South-Asian island and
small-state probes — Dominica, Fiji, Grenada, Jamaica, Saint Lucia, Vanuatu, US Virgin Islands, Sri Lanka,
Nepal, Yemen among them — with no coherent Cogent transit footprint (medium confidence: the ThousandEyes
primary is paywalled, so the citation rests on the Network World syndication). And the governing reading holds
regardless — a single shared-transit-provider fan-out is not the world reaching the alarm bar, so 2023-09-06
fails condition (c) on the standard's meaning even if a paywalled source names 17 Cogent-downstream countries.
The one reading the classifier does not lean common-mode, 2024-10-03 (44 countries, a 38-country synchronized
batch 29 of it ping-only — 76%, just under the classifier's 80% share bar, a near-miss of the common-mode
class rather than a different shape — 13/44 corroborated), is the closest the line ever came to a real event
and still does not survive: the search found no cited world event, the 13 corroborated countries are
geographically incoherent (West/East/Southern Africa plus Myanmar) with three chronic (present 10-02/03/04),
and the day is an isolated single-day spike (10-02: 7, 10-04: 5). Corroboration is a measurement, not a cited
reference regime.

None reaches its own alarm bar on the world from a cited reference — the reachability standard cnh_cny was
held to at R13/R23.1, where a cited reference regime counts and a rate does not. Condition (c) fired, and
net_outages is DEMOTED to tier-2: the consequence pre-committed at its R7 promotion and R11 retention. The
line keeps collecting — history and z-score accumulate as a watchlist candidate — but is no longer counted in
the trembling/dark/blind headline, and the tier-1 global-communications slot is left empty and disclosed.
Nine annotations landed: one `artifact` per reading (dated to the reading, inserted in date order), and a
2026-09-08 `method` row recording the demotion. The demotion clause's two pending tags are closed — the reach
deadline fired, and the per-recurrence tripwire is no longer a tier-1 duty. Code: TIER=2 in
fetchers/net_outages.py, the line moved to the tier-2 grouping in collect.py, tier:2 in docs/index.html, the
Tier 2 table and Known limit 7 in radar.md, and docs/data/leans.csv regenerated to the new tier-1 set. The
dashboard's resonance note now enumerates the three counted domains (airspace, finance, capital) rather than
four — communications drops out to match the emptied slot the coverage note already discloses.

STABLE_SINCE bumped to 2026-09-08: a TIER change alters the summary re-derivation, which counts tier-1 lines
only. net_outages did not tremble on 2026-09-08, so the 2026-09-08 summary row re-derives byte-exact and
replay --check stays 0-divergence. Full suite green (gate, lint stdlib-only in a bare venv, replay
0-divergence, annotations mirror byte-identical). radar-log.md crosses 2,000 lines with this entry; the roll
(tool shipped R26) is deferred to R29.

### Round 29 — 2026-09-08 (the discipline-holding round: roll the log, cite cnh_cny's regime, probe one forward path)

A discipline-holding round, not a tier-move round. No line clears count + orthogonal + fresh + real-guard + its own
gates at once, so nothing is promoted and the communications slot stays disclosed-empty. The work is three honest
things — tell the registry's own truth, open one credible forward path, consolidate dead-ends — with every structural
fix parked to ~Nov, when its banked window matures. Eleven items ship in one round; A/C1/C2 are code, the rest is record.

**A — the log roll.** radar-log.md crossed its self-set 2,000-line threshold at R28 (2,036 lines).
`tools/roll_radar_log.py --split-round 20` archived rounds 1-19 into radar-log-1.md and left 20+ here, verified
byte-identical and round-complete. The tool gained a required `--split-round` CLI, injectable path/round kwargs, a
6-line archive preamble (so every archived round keeps its exact line number), and a guard against overwriting an
existing archive; its tests moved to a synthetic fixture, so no test reads the live log now. `lint_registry`'s
round-index parity globs `radar-log*.md`, so both files are swept in and the 1-28 index matches with no lint change.

**C1 — the dark-count banner.** docs/index.html's alarm banner fired at a hard-coded `darkCount >= 3` — a majority at
four tier-1 lines, but all-dark at three, a bar that silently shifted when net_outages left. It now reads
`darkCount*2 > TIER1.length`, a majority rule off the live count (2-of-3 today, reproducing the historical 3-of-5 /
3-of-4), asserted in both languages by a render_smoke fixture with runtime-current dates and two of three lines dark.

**C2 — the tier-1-count lint.** A new lint in lint_public_surface.py scans the `const T` block and the README's claims
prose and binds every "three primary lines"/"三条主线"-shape literal to `_docs_tier1_line_count()` — green today (5
matches, each 3), red when a literal is planted to four — so a hard-coded count can no longer drift off `TIER1`.

**S1 — cnh_cny, retained on a cited regime.** cnh_cny sits at n=57 scored, a short week from its n≥60 maturity review,
so neither pending review closes (Known limit 4: below 60, defer). The stale cells are refreshed: orthogonality
|max Pearson| +0.076 vs credit_spread (n=42), −0.036 vs flights — the most orthogonal tier-1 line; the UP alarm bar is
≈223 pips, +80 above the all-time record high of 143, unreachable within this young calm record; all five |z|>3 events
are benign DOWN trembles (07-02/07-07/07-25/08-10/08-26), zero UP-trembles in 57 days. Retention therefore rests
entirely on a WEAKER external-reference-regime standard than credit_spread or flights, and R23.1's rule is that the
regime be cited, not assumed. The citation is now written into the reachability gate: the 2015-16 RMB devaluation /
capital-flight episode — the PBOC's surprise onshore devaluation of 2015-08-11 (its first since 1994) and the offshore
squeeze of 2016-01-12, when overnight CNH HIBOR spiked to a record ~66-67% and the CNH-CNY spread ran to the hundreds
of pips, multiples of the ~223-pip alarm bar (BIS Working Paper No. 446, CNBC 2016-01-12). This is the SAME
reachability standard net_outages FAILED at R28: cnh_cny passes only because its regime is a documented, sourced world
event, where net_outages' 8 largest readings adjudicated to no cited event. Banked for the n≥60 review: is the zero
alarm-direction reach a young-calm-record artifact, or a sign the bar or statistic needs revisiting?

**S2 — the passive-BGP comms-slot probe (probe-only).** A probe, not a build: no fetcher, no scored line, no tier
change. It tests whether IODA's pre-aggregated passive-BGP signal (RIPE RIS + RouteViews) can pass the reachability
standard net_outages could not. The keyless endpoint `/v2/signals/raw/country/{CC}?datasource=bgp` returns per-country
visible-/24 counts at ~0.4h lag; a flicker-beating aggregation — a size-floored 153-country watch-list (≥512 /24s),
each country's daily-min over its 28-day rolling-median baseline, worst-of across the list — plausibly passes every
gate: reachable (alarm bar frac 0.583, observed min 0.409, max down-|z| 15.25, the up-side a larger benign rolling-Qn artifact), firing on Syria 2022-05-30 −96.9%
(z−24.6) and Sudan 2023-04-24 −68.6% (z−9.1); orthogonal (max Pearson 0.167 vs flights, .154 credit, .082 cnh); fresh
(~0.4h); and structurally immune to the active-probing common-mode that demoted net_outages, because BGP is a passive
read of route announcements. The load-bearing disclosure: BGP measures route ANNOUNCEMENT, not reachability, so it
misses the Gaza 2023-10 total blackout (~3.7% BGP drop, z≈−0.4, routes stayed announced). A built line must therefore
be disclosed as route-WITHDRAWAL detection — the gnss "effective reach 1" precedent — in anchored scale-mode (anchor
1.0, materiality ≈0.10). Evidence: data/archive/bgp_probe_2026-09-08.csv (committed this round, diagnostic, not
mirrored). The empty communications slot now has a credible candidate, net_bgp_withdrawal, that would enter at tier-2
under the ≥60 funnel — but it is NOT built this round; the build is a separate operator decision, and no line is ever
seated in tier-1 on a reference regime alone.

**S3-S7 — registry bookkeeping.** S3: the Backlog bgp_instability entry is rewritten to the measured finding above
(IODA is the correct global formulation; RIPEstat single-AS and keyed Cloudflare Radar BGP are not; a DIY collector is
rejected). S4: flights structural work stays deferred to the two ~Nov reviews (the level-layer extension and the
fixed-hour re-review, ~7/60); the planned fix is a per-region worst-of-region z (restoring Europe −7.84z / Japan −7.33z
at the existing 22:30Z hour), and a second sample hour is rejected; the two ADS-B survivors (adsb.fi 900 / adsb.lol
897, <1% apart) are accepted, the gated hosts and OpenSky recorded so the mirror search is not repeated. S5:
fed_srf_takeup is named the lead tier-1 challenger on raw merit (1274 scored, |max corr| 0.0998 vs flights, fresh
NY-Fed T+1, guard 3, three clean >$30bn alarms), the R20 de-cycling debt and R15 anchored-scale gates pointed at it
and deferred — though it, like any BGP line, is dollar/plumbing, and preserving the empty slot for a comms line is the
deliberate choice S2 serves. S6: hkma_aggr_balance is flagged before it can count as a promotion candidate — 16
scattered dark days, worst-in-set reliability (0.871 = 108/124, or 0.888 = 127/143 by the read/rows definition), and a
|z|>3 on 14/108 days (10 flagged trembles, all benign up) from discrete step-jumps argue for anchored scoring; it is disqualified now. S7: the
single-credit-slot bar note is refreshed — sofr_iorb_spread is now n=49 with |max corr| 0.231 vs cnh_cny, still
deferred to n≥60.

**C3 — the per-line STABLE_SINCE map, deferred (no code).** Banked as prose: per-line replay is already
tier-independent (scoring_attrs omits TIER; 527 rows, 0 divergence since 08-17), and only the summary re-derivation
loop is tier-sensitive; the lighter fix is a separate TIER_CHANGED_SINCE used only at the summary guard; deferred
because the restored ~504-row per-line window is daily-checked-while-recent, tier-independent, and frozen — zero
detection benefit at ~22× the daily --check cost.

Full suite green (gate, audit including radar-metrics freshness, lint stdlib-only in a bare venv, replay 0-divergence,
pending 0 overdue); radar-metrics.md regenerated; the bgp probe CSV committed as evidence. No served or scored line
changed this round.

### Round 30 — 2026-09-09 (the promote-one round: fed_srf_takeup fills the open primary slot at 4/4)

A tier-move round. The board was scored whole, one line cleared count + orthogonality + freshness + real-guard + its
own standing gates at once, and it was promoted — the first tier-1 addition since the net_outages demotion at R28 left
the roster at 3/4. fed_srf_takeup goes tier-2 → tier-1, filling the open primary slot back to 4/4. The round also
records the domain decision that filling it made, and the tier-2 BGP line built to carry communications forward.

**The pick — fed_srf, on the data.** The R29 board had already named fed_srf_takeup the lead tier-1 challenger on raw
merit; the whole-board re-score confirmed it as the most orthogonal candidate for the open slot: |max Pearson| 0.008 vs
credit_spread (shared-date n=750), 0.10 vs flights (n=45), 0.10 vs cnh_cny (n=40) — a distinct dollar-plumbing domain,
not a second reading of one already covered, on 1,274 scored days overall. Fresh (NY-Fed T+1), guard 3, reach 3, three
clean >$30bn scarcity alarms on a 1,283-row
seed back to SRF inception (2021-07-28). Nothing else on the board cleared every gate at once.

**The gate-work — both standing gates cleared.** Promotion pointed at the two gates the registry had parked against this
exact line; both were worked and both cleared on the data (full analysis in the R30 gate-work report; the figures below
are cited from it).

- **R20 calendar de-cycling debt — CLEARS, on two independent grounds.** First, it is structurally MOOT for an anchored
  line: normalize.robust_z's materiality branch returns (today − anchor) / materiality and reads only `today`, never the
  rolling window — no median centre, no Qn scale, no weekday de-cycling term on that path — so month/quarter-end
  baseline-warping cannot move fed_srf's z at all. Second, even ignoring mootness, the month-turn friction band tops at
  $26.0bn (z 2.60), $4.0bn (0.40 z) below the $30bn / 3×MATERIALITY alarm; no routine reading anywhere lands in the
  z 2.60 → 3.05 gap. Routine month/quarter-end reserve-friction ops do not approach the alarm.

- **R15 anchored-scale gates — CLEAR.** MATERIALITY is validated: the routine (non-alarm) take-up distribution is
  median $0, p90 $10m, p95 $100m, max-routine z 2.60, with a clean 0.45 z empty gap between the z-2.60 friction ceiling
  and the z-3.05 lowest fire — no reading falls inside it. 85.4% of nonzero routine days are <$100m dust at z<0.01,
  exactly the docstring's claim. The episode / serial-dependence overlay: the 3 alarms (2025-10-31 z 5.04, 2025-12-31
  z 7.46 the record, 2026-02-17 z 3.05) are 3 DISTINCT single-day episodes 61 and 48 days apart, each a solitary spike
  (its neighbours sit below the alarm), full-series lag-1 autocorr 0.406 — no two trembling days adjacent, so 3
  trembling days = 3 episodes, 1:1. Unlike a second credit-family line (lag-1 0.986-0.993, day-counts ~8× episode
  counts), this does not threaten the headline's iid null.

**The promotion.** fed_srf_takeup.TIER 2 → 1, applied across every surface that reads it: the fetcher module,
docs/index.html's `const LINES` (tier:1, plus the `watches` field the coverage line and covModal need for a tier-1
line), collect.py's LINES grouping, and radar.md's tier tables (the row moved into Tier 1; the counts 3→4 primary; tier-2
candidates net 14→14 this round — one out via this promotion, one in via the BGP build). The customer copy's
tier-1-count claims move with it — "three primary lines" → "four" and "三条主线"
→ "四条主线" in the `const T` block, and the README prose ("Three lines"/"three primary lines") plus its
machine-checked-claims table (primary lines 3→4, keyless 3→4, fed_srf being keyless) — all kept green under the R29 C2
parity lint. The C1 darkCount majority banner now spans 4 lines by its own `darkCount*2 > TIER1.length` rule; the
render_smoke fixture that exercised it was updated from a 2-of-3 to a genuine 3-of-4 majority.

**STABLE_SINCE.** A tier change alters the summary re-derivation (replay reconstructs the headline counts from each
line's CURRENT tier), so STABLE_SINCE is bumped 2026-09-08 → 2026-09-09 — the first collection the new tiering governs
— with a dated ledger entry (kept in order for the lint_ssot T6 constraint). fed_srf did not tremble/dark/blind on
2026-09-09: its row is stale (obs_date 2026-09-04 already recorded), counting toward none of the three tallies, so the
2026-09-09 summary row (0/0/0) re-derives byte-exact with fed_srf added to the tier-1 set. `replay.py --check` is
0-divergence.

**The domain decision.** The open slot had been reserved, in intent, for a communications line to replace the demoted
net_outages. But the sole comms candidate — a passive-BGP route-withdrawal line — was still unbuilt when the promotion
came due, and an empty disclosed slot with a data-backed financial line waiting is worse than a fourth financial line
filling it. So the slot takes fed_srf: the tier-1 domains are now airspace + credit + capital-controls + dollar-plumbing
(three financial, one airspace). Communications is not abandoned — it now rides tier-2 as net_bgp_withdrawal, the
standing candidate for a future slot, to earn tier-1 over the ≥60-scored funnel like any other line, not by
declaration. The mild cost (three of four primary lines now financial) is recorded openly against the benefit of a
proven, orthogonal, fresh instrument over an empty slot.

**The BGP build.** net_bgp_withdrawal is BUILT at tier-2 — the route-WITHDRAWAL candidate the R29 probe validated.
Passive-BGP worst-of route visibility over a size-floored 153-country watch-list (median daily-median visible-/24 ≥
512), each country's daily-min ÷ its 28-day rolling-median baseline, worst-of across the list, scored DOWN in anchored
scale-mode (ANCHOR 1.0, MATERIALITY 0.10 → alarm at fraction 0.70, below the ~0.75 structural benign floor). It fires
strongly on the cited events (Syria 2022-05-30 z −9.69, Sudan 2023-04-24 z −6.86) and is structurally immune to the
active-probing common-mode that demoted net_outages — BGP is a passive read of route announcements, with no probe
vantage to lose. BASE-RATE CALIBRATION, recorded pre-promotion: the anchored bar (frac<0.70) fires ~21% of the full
seed (352/1673 days) — NOT a bump-only line — because it flags CHRONIC route-withdrawal states each day (Sudan 61 /
Iraq 58 / Syria 51 ≈ 48% of runs, Cameroon 40; by year 6%/25%/34%/25%/10%), versus the probe's rolling-Qn ~5% on the
recent calm 2026 window (the anchored bar itself reads ~6.4% on 2026-03..09). So "ordinary days read a bump, not a
tremble" holds only on a calm window; before any tier-1 promotion the line needs a calibration pass — a
sustained-duration variant, or a re-set materiality / explicit chronic-state handling — so the count reflects new
withdrawals, not standing ones. DISCLOSURE (the gnss "effective reach 1" precedent): it measures route ANNOUNCEMENT,
not reachability, so it catches shutdowns/cable-cuts/transit failures that WITHDRAW prefixes but MISSES access-layer
blackouts where routes stay announced (Gaza 2023-10's total blackout read only ~−4%, the ASes announcing into the
dark). It closes the withdrawal subclass of the communications question, not the whole of it.

**Pending.** fed_srf's two gate items are closed as cleared: the R15 anchored-scale gate still stands for stablecoin_peg
(tier-2, unpromoted) and any future anchored line, and the R20 de-cycling item's tga_days_cash warp remains noted (tga
is not a promotion candidate). The usd_xccy_basis parking review's R30 sourcing re-probe fell inside this focused
promote-one round and was not run; its standing keyless-exhausted finding holds and the cadence is rolled to R40. Every
other pending item stands.

Full suite green (gate, audit including radar-metrics freshness + round-index parity + no-overdue + retracted-phrase,
lint stdlib-only in a bare venv including the lint_registry TIER parity and the C2 tier-1-count lint, replay
0-divergence, pending 0 overdue); render_smoke passes both languages, the headline reading "of 4"; radar-metrics.md
regenerated to reflect the tier change and the closed pending items.
