# tremor radar — calibration log

The append-only round-by-round record behind the registry in **[radar.md](radar.md)**.
Each round is dated and states what was measured, decided, and deferred. The living registry
(scoring law, the three gates, tier tables, Backlog, Rejected) is in radar.md; this is the history.

### Round 1 — 2026-06-22 (seed)
- **Scored** the 7 existing indicators on the rubric metrics. Computed metrics
  (Reliability / Responsiveness / Orthogonality) are `—`: only ~1 day of history
  exists, far below the ~20 days needed — honest, not fabricated.
- **Explored** (diverge): reasoned 4 global + guarded + high-leverage candidates and
  web-verified their data. `stablecoin_peg` verified keyless and live; `sofr_stress`
  rests on FRED (already working in CI). `chokepoint_transit` and `net_outages` are
  on-thesis but lack a confirmed free source — kept as ideas pending a data find.
- **Calibrated** (converge): tier-1 is **over capacity (5/4)**. The two clearly-global,
  high-leverage lines (credit_spread, flights) are locked. The demotion contest is
  among the three national/regional lines — capital_premium (Korea), grid_frequency
  (Nordic), cnh_cny (China). The right tie-breaker is **Orthogonality**: Korea premium
  and China CNH/CNY are both "Asian capital-control" lines and may move together, in
  which case one is redundant. That needs history. **No demotion applied this round** —
  deciding now would be 拍脑袋.
- **Moves applied:** none (no evidence yet for any promotion/demotion).
- **Proposed for next rounds:**
  1. Once ~20 days accrue, compute Orthogonality among {Korea, Nordic, China} and demote
     the most-redundant to reach tier-1 = 4.
  2. Build `stablecoin_peg` as a tier-2 fetcher (verified free, high leverage/reach) —
     a strong global candidate to start accumulating history. *(needs approval — new code)*
  3. Build `sofr_stress` as tier-2 (FRED, global dollar-funding stress). *(needs approval)*
  4. Keep exploring toward 16 tier-3 ideas; hunt a free AIS source for chokepoint_transit.

### Round 1.1 — 2026-06-22 (cadence gate added)
- **New gate:** added the **cadence gate** to the methodology — an indicator must persist
  at daily resolution or be aggregated intraday→daily, because collection samples once a
  day. A daily snapshot of an intraday-transient phenomenon is dishonest (aliasing).
- **Rejected `stablecoin_peg`:** depegs recover in minutes–hours, so a daily snapshot
  almost always catches it back at $1 and misses the event. Removed from candidates.
- **Added `ar_blue`** (Argentina blue-dollar premium): web-verified keyless on dolarapi;
  a black-market FX premium persists for weeks, so daily sampling is honest. Capital-control
  domain, national reach.
- **Strongest standing candidate is `sofr_stress`** — global, guarded, high-leverage, daily,
  free. The top build target for tier-2.
- **Moves applied:** none (candidate-list refinement only).

### Round 2 — 2026-06-22 (re-probe + rethink)
- **Explored (diverge):** re-probed data sources live and unblocked two strong candidates:
  - `chokepoint_transit` — found **IMF PortWatch** `Daily_Chokepoints_Data` (free, keyless,
    daily vessel counts per chokepoint; Suez at 26–39/day, already depressed by the Red Sea
    crisis). Upgraded Guard 2→3 and marked data verified. Now a 3/3/3 candidate.
  - `net_outages` — found **IODA** (Georgia Tech) free outage signals (bgp / active-probing /
    Google-transparency). Data verified, replacing the token-gated Cloudflare source.
  - Added `ve_parallel` (Venezuela parallel FX), keyless via dolarapi.
- **Rethink of tier-1 (the deeper ask):** two structural problems surfaced, both pointing the
  same way:
  1. **Domain redundancy** — tier-1 holds TWO capital-control lines (capital_premium/Korea and
     cnh_cny/China). The original thesis wants four DIFFERENT domains; two in one domain is
     likely redundant (an Orthogonality question, pending history).
  2. **Global imbalance** — three of five tier-1 lines are national/regional (Korea, Nordic,
     China); only credit_spread and flights are global. The "tier-1 should be global" principle
     favors demoting a national line.
  Both point to demoting one of the national/regional lines — and the natural replacement is a
  **global 3/3/3** line (chokepoint_transit or sofr_stress), which would also add a genuinely
  new domain (trade) or strengthen financial.
- **Moves applied:** none — chokepoint/sofr have no history yet, so per the gates they can't
  jump to tier-1. The honest path is to BUILD them as tier-2 first.
- **Proposed for next round:**
  1. Build `chokepoint_transit` (IMF PortWatch) and `sofr_stress` (FRED) as **tier-2** fetchers
     so CI starts banking their daily history. *(needs approval — new code)*
  2. After ~20 days, compute Orthogonality of the national tier-1 lines vs each other and vs the
     new global challengers; demote the most-redundant national line to reach tier-1 = 4.
  3. Keep filling tier-3 toward 16 (next hunts: a free daily Baltic Dry / freight source; a
     daily sovereign-spread source).

### Round 3 — 2026-06-22 (tier-1 decided + 6-domain candidate hunt)
- **Tier-1 decision (user):** slot 4 = `cnh_cny` (China). Steady-state tier-1 target is
  **flights · credit_spread · chokepoint_breadth · cnh_cny**. `capital_premium` (Korea, redundant
  capital domain) and `grid_frequency` (Nordic, regional) demote to tier-2 once the trade line is
  built and online (so tier-1 never drops below 4).
- **Hunt (diverge):** ran a parallel 6-domain search (financial, trade, infrastructure, capital,
  geopolitical, wildcard) → 29 candidates; curated tier-3 to 13. Key outcomes:
  - **Discovery:** FRED serves a **keyless** CSV (`fredgraph.csv?id=…`) — live-verified — so SOFR,
    IORB, EM/EU OAS, CP spreads are all free without a key.
  - **Refined two existing candidates into sharper forms:** `sofr_stress` → `sofr_iorb_spread`
    (SOFR minus the defended IORB ceiling = the actual guard deviation, not the rate level);
    `chokepoint_transit` → `chokepoint_breadth` (the full 28-chokepoint panel, each a geopolitical
    tripwire — the live data already shows Hormuz at ~2/day under blockade).
  - **New 3/3/3 global candidates:** `port_throughput` (PortWatch ports), `gnss_interference`
    (GPSJam GPS-jamming — a NEW navigation/PNT domain that fingerprints electronic warfare),
    `em_corp_oas` (EM dollar-funding stress, orthogonal to US HY).
  - **Live-verified keyless sources:** FRED CSV, GPSJam, RIPEstat (BGP), IODA, CriptoYa.
  - **Rejected `tail_risk_market`** (Polymarket): fails the guard gate — a free-floating market read.
- **Moves applied:** none (still thin history). The tier-1 demotions are recorded as decided but
  execute when `chokepoint_breadth` is built and online.
- **Proposed for next round:** build the four global 3/3/3 lines as tier-2 to bank history —
  priority `chokepoint_breadth` + `sofr_iorb_spread`, then `gnss_interference` + `port_throughput`.

### Round 3.2 — 2026-06-22 (build)
- **Built four global tier-2 watchlist lines** (user: keep the dashboard tier-1-only, but collect
  tier-1 AND tier-2 data continuously): `chokepoint_breadth` (IMF PortWatch), `gnss_interference`
  (GPSJam), `sofr_iorb_spread` and `em_corp_oas` (keyless FRED via a new `core/fred.py` helper).
  All four span distinct domains (trade / navigation / financial-plumbing / EM-financial).
- **Live values on build day:** chokepoint ~1810 transits/day; GPS-jam share ~0.43%; SOFR−IORB
  ~−2 bps (calm); EM corp OAS ~1.38pp (calm). Tier 2 is now 6/8; dashboard unchanged (5 tier-1).
- **Moves applied:** tier-3 → tier-2 for the four (built). No tier-1 change.
- **Next:** they bank history; after ~20 days, Orthogonality decides which challenges into tier-1
  (chokepoint_breadth is the slot-3 incumbent-elect, displacing Korea/Nordic).

### Round 3.3 — 2026-06-22 (tier-2 filled to 8/8)
- **Built two more tier-2 lines** to fill the watchlist: `port_throughput` (IMF PortWatch global
  port calls, ~4729/day) and `net_outages` (IODA, ~3 countries currently in outage). Extracted a
  shared `core/portwatch.py` so chokepoint + ports don't duplicate the ArcGIS query.
- **Tier 2 is now full: 8/8.** Funnel snapshot — tier-1 5 (target 4), tier-2 8/8, tier-3 7/16.
- **Moves applied:** tier-3 → tier-2 for the two. No tier-1 change.
- **Tier-2 is full**, so further tier-3 builds wait for a slot to open (a watchlist line graduating
  to tier-1 or washing out on poor Reliability/Responsiveness once history accrues).

### Round 4 — 2026-06-22 (apply the decided tier-1 = 4)
- **Applied the standing decision** (always 4 primary; slot 4 = China). Tier-1 is now
  **flights · credit_spread · cnh_cny · chokepoint_breadth** — four distinct domains (airspace,
  financial, capital, trade). The dashboard and resonance count now read 4/4.
- **Moves:** promoted `chokepoint_breadth` (tier-2 → tier-1); demoted `capital_premium` (Korea)
  and `grid_frequency` (Nordic) (tier-1 → tier-2). All still collected daily.
- **Note on discipline:** this is a user-directed promotion ahead of the orthogonality-history
  gate. Justified on the rubric — chokepoint_breadth is global 3/3/3 vs the two demoted national/
  regional lines (Korea redundant with China; Nordic regional). When ~20 days of history exist,
  Orthogonality/Responsiveness can confirm or revise (e.g. Nordic grid may re-challenge if it
  proves more independent than a tier-1 incumbent).
- **Capacity:** tier-2 candidate slots stay at 8 (Korea + Nordic in, chokepoint out); gdelt is
  counted separately as the contrast line. tier-3 = 7/16.

### Round 5 — 2026-06-22 (freshness rule; swap chokepoint → gnss in tier-1)
- **New rule:** added the **freshness rule** — a tier-1 (displayed) instrument must have low
  publication lag. `chokepoint_breadth` is a strong 3/3/3 signal but IMF PortWatch lags ~8 days,
  so it shows a disruption a week late — too stale to be a live instrument.
- **Swap:** demoted `chokepoint_breadth` back to tier-2 (still collected — the lag washes out in a
  rolling baseline), promoted `gnss_interference` (GPSJam, ~1-day lag, global 3/3/3, a fresh
  navigation/electronic-warfare signal that directly fingerprints conflict) into tier-1.
- **Tier-1 now:** flights · credit_spread · cnh_cny · **gnss_interference** — airspace, financial,
  capital, navigation/EW. All ≤ ~3-day lag.
- **Moves:** gnss tier-2 → tier-1; chokepoint tier-1 → tier-2. No other change.

### Round 6 — 2026-07-10 (first live-signal review, 19 days of history)
- **System:** 17 consecutive scheduled runs, zero failures, zero dark days across all 13 lines.
  z-scores active since ~07-01. First trembles observed; every one was attributed (see
  `data/annotations.csv`) — none was a resonance (never more than 1 tier-1 line on a day).
- **Signals attributed:** quarter-end repo turn caught by `sofr_iorb_spread` exactly on 06-30
  (mild, benign — the line's first validation); `cnh_cny` flipped negative twice on offshore-yuan
  strength (07-07 coincided to the day with the PBOC's Hong Kong offshore-yuan package); `flights`
  dipped on the July-4 Sunday (holiday + US storms + Italy ATC strike); Hormuz REOPENED (~2/day
  → 22-42/day), driving chokepoint's benign up-tremble; Super Typhoon Bavi took out Guam's grid.
- **Calibration findings for next rounds:**
  1. `net_outages` z≈10 was mostly a MONITORING ARTIFACT — IODA activated new datasources
     (gtr 07-01, bgp/merit-nt 07-05), inflating the country count against a quiet baseline
     (52/89 spike events were merit-nt micro-events in North Macedonia alone). Consider filtering
     by outage score or datasource for a stabler count before this line can be trusted.
  2. `flights` weekday de-cycling cannot engage until ~10 same-weekday samples (~10 weeks);
     until then weekend/holiday dips can soft-false-positive. Self-heals by ~Sep 2026.
  3. ADS-B provider flakiness (fallbacks fired on 07-04/07-07): a provider returning HTTP 200
     with a degraded aircraft list passes the require-all-regions guard silently. Consider a
     per-region sanity floor.
  4. Trembles in the benign direction (chokepoint up, outages down) count toward the flag; the
     `direction` column disambiguates. Open question: should tier-1 resonance count only
     alarm-direction trembles?
- **Moves applied:** none — no evidence against any tier placement yet; Orthogonality unlocks
  around ~20 days of z history (mid-July).

### Round 6.1 — 2026-07-10 (methodology batch from the live-signal review)
Adjustments approved after a three-lens panel review (statistician / thesis-guardian /
minimalist); all recorded as `method` rows in `data/annotations.csv`, applied FORWARD ONLY
(no committed z/trembling value was rewritten).
- **Observation dedup:** rows gained an `obs_date` column; the z baseline uses only the first
  occurrence of each observation, a republished observation scores no new z and raises no flag,
  and baselines cap at 180 calendar days. Backtest over the 19-day history: the six
  publication-step trembles (chokepoint ×3, port ×1, sofr ×2) would not have fired.
- **Direction-aware resonance:** `trembling_count` now counts only alarm-direction trembles;
  benign-direction moves (a guard reasserting itself, e.g. Hormuz reopening) are recorded and
  shown as "benign shift", not disorder. Under the new rule the July history would have counted
  1 tremble (flights 07-05), not 3.
- **Weekly-cycle warm-up veto:** with 3–9 same-weekday samples, a full-window tremble whose
  level lies inside the same-weekday min–max envelope is suppressed, auditable in source_note.
  Nonparametric by design — a genuine crisis value cannot be vetoed.
- **net_outages v2:** count restricted to IODA's ping-slash24 datasource (v1 counted every
  datasource and measured IODA's sensor rollout, not disorder — live check: v2 reads 3
  countries where v1 read 17). v1 archived at `data/archive/net_outages_v1.csv`; v2 restarts
  under warm-up.
- **ADS-B region floor:** under-floor (<30 aircraft) from one provider = suspected degraded
  feed, try the next; two providers agreeing under-floor = accepted as a real reading
  (corroboration keeps the instrument from blinding itself during a genuine collapse).
  Per-region counts now recorded in source_note.
- **Dashboard:** trembled points now carry their attribution notes from annotations.csv
  (tooltip + per-line modal); alarm-direction trembles read red, benign shifts read calm green;
  lines with <30 unique observations show a "calibrating" badge.
- **CHANGE FREEZE:** methodology is now frozen until the next radar round (~30 days of clean
  history), barring a correctness-critical failure. Open items parked for that round: MAD is
  ill-suited to low-count integer lines (net_outages); a small holiday calendar as annotation;
  a false-positive budget review of the |z|>3 threshold at ~90 days.

### Round 6.2 — 2026-07-10 (the "feels" half, rendered)
The mission audit scored the second clause of the founding question ("或只是感觉更乱了")
3/10: the feel side was collected but 0% displayed. This round builds it out:
- **gdelt v2:** conflict share now aggregates the entire previous UTC day (~96 files,
  ~100k events) instead of one 15-minute sample that swung 8→23% in a week; obs_date set;
  v1 archived. **gdelt_tone** added from the same download pass (news valence vs event mix).
- **vix** added as the priced-fear channel (keyless FRED VIXCLS), seeded with 180 days of
  archive scored through the standard pipeline — feel z is live immediately (13 archive
  trembles, incl. the Mar-2026 VIX-31 episode). Contrast lines are exempt from the guard
  gate by design and can never be counted or promoted.
- **Dashboard:** a "Real vs felt — the anxiety premium" panel now renders trembling_count
  history as bars (the real side — also the first trend view of the headline number)
  against the feel lines' z toward their alarm direction, with amber columns marking days
  when feeling runs hot (feel z ≥ 2) while every instrument reads calm — the anxiety
  premium, visible. Earlier same-day fixes: stale tier-1 lists in README/resonance modal
  corrected, comparator disclosed, calibrating qualifier added to the headline.
- The founding question's two halves are now both on the page.

### Round 7 — 2026-07-22 (the scale estimator; a miss, and a correction)

Triggered by a 15-day miss, reviewed against 31 days of history. The instrument read
**0 / 4 every day from 07-07 to 07-22** while the US–Iran ceasefire collapsed, the IRGC
closed the Strait of Hormuz, the Houthis declared a naval blockade of Saudi Arabia and
Brent reached $91. The miss is logged in `annotations.csv` as a permanent record.

**Diagnosis — mostly coverage, partly calibration, and the premise was wrong.**
The working premise going in was "the |z|>3 rule over-fires 26x" (7.8% observed against
0.3% nominal). That is wrong: 0.3% is the tail of a *standard normal*, but a z built from a
finite window has its own, much fatter null distribution that depends on window size.
Measured by simulation against the shipped code: **|z|>3 under MAD occurs 5.3% of the time
at n=10 and 0.56% at n=90 with nothing happening.** True over-firing was ~1.5–3x, not 26x —
and the threshold could not be raised anyway, because two adjudicated REAL events (the FAA
nine-airport ground stop of 07-21, and the 07-18 Northeast storms) had already scored
−2.70 and −2.80 and been missed *at* 3.0.

**Shipped: MAD → Rousseeuw-Croux Qn** in `core/normalize.py`. Same 50% breakdown point and
the same collapse condition, but unbiased on short windows (MAD measures ~0.91 sigma at
n=10; Qn ~1.00) with about half the sampling variance. Null exceedance at |z|>3 falls to
2.7% / 1.2% / 0.36% at n=10 / 20 / 90. Replayed over all 341 scored rows the tremble rate
goes 7.3% → 6.5%; `em_corp_oas` 9.1% → 0%; the adjudicated `grid_frequency` artifact of
07-12 is suppressed while 07-17 survives; and **the adjudicated real `flights` event of
07-22 is recovered, −2.695 → −3.014.** Forward only; every series carries a seam here.

**Shipped: the RMS fallback is gone.** When the robust scale collapsed, scoring fell
through to a median-centred RMS with breakdown point 0 — on the real `sofr_iorb_spread`
window of 07-02 it manufactured z = 5.262 from a 3bp integer move. No spread now returns
None, as the stated rule always said it should. Costs zero z-scores on the existing record.

**Shipped: a test suite** (`tests/test_normalize.py`, run in CI before any row is written)
and a **CI failure alarm** — a persistently failing run stopped the daily commit, and
GitHub disables a cron workflow after 60 days without repository activity, so the
instrument could have switched itself off with nobody told.

**Corrected:** the `gdelt_tone` annotation of 07-21 defended a tremble with a weekday
control computed on a *different row*. The trembling row scored a Sunday observation whose
own-weekday z is ≈ −1.05; the genuine weekday signal was the next row, at −4.31 sd, which
did not tremble. The instrument trembled on the artifact and stayed silent on the real day.

**Reliability, first data-backed reading** (tremble rate over scored rows, MAD basis, and
see limit 4 above — none of these n are large enough to adjudicate, they are recorded to
accumulate): `sofr_iorb_spread` 30% (n=10), `grid_frequency` 9.5% (21), `cnh_cny` 9.5% (21),
`em_corp_oas` 9.1% (11), `vix` 7.3% (178), `capital_premium` 4.8% (21), `cn_flights` 4.8%
(21), `flights` 4.8% (21), `credit_spread` 0% (11), `gnss_interference` 0% (19).
No promotions. `grid_frequency` is **blocked from tier-1** pending re-measurement under Qn.

**Investigated and deliberately NOT built** (each rejected on evidence, recorded so it is
not silently re-litigated):
- *A Gulf region for `flights`* — probed all three keyless ADS-B aggregators at seven Gulf
  points: 6–15 airborne over Dubai, 14–28 Doha, 10–21 Hormuz; the deduplicated union of
  eight 250nm circles covering the whole peninsula is **35 aircraft**, against ~950 in the
  single W/C Europe circle. Dubai swung 14→15→11→6→13 within fourteen minutes. A sensor
  with ±50% snapshot noise cannot see the −14% move the Hormuz closure actually produced.
  Free community ADS-B does not instrument the Gulf. Recorded as a permanent limitation.
- *Regionalizing `gnss_interference` onto a Hormuz box* — backtested on 95 days of real
  GPSJam files. A box at 25–38N/44–62E does fire (z ≈ +3.2/+3.8/+3.3 across the episode),
  but **moving its southern edge by one degree destroys the detection entirely** (24–38N
  gives 2.0/2.1/1.8), and its 90-day baseline spans a ~10x growth in the sampling frame
  (139 active cells / 3,570 aircraft in April against 555 / 36,416 in July) — the same
  sensor-inflation artifact that forced the `net_outages` v2 break. A tier-1 reading that
  depends on where a human drew a rectangle is worse than an honestly empty slot. Deferred.

**Still open, carried to round 8:** the level-vs-change limit (1 above) — the deepest
finding of the review and unaddressed; harvesting the full DAILY PortWatch series (the
fetcher currently discards 6 of every 7 observations it already downloads, which is the
real reason `chokepoint_breadth` could not score through the Hormuz closure); a per-line
`status` so "cannot score" stops reading identically to "calm"; the weekly cycle on the
GDELT feel lines; `grid_frequency`'s daily-maximum statistic; vendoring Chart.js.

### Round 7.1 — 2026-07-22 (tier-1 swap; the status column; PortWatch rebuilt)

**Tier-1 swap: `gnss_interference` → tier 2, `net_outages` → tier 1.**
The GPS line kept a primary slot while being structurally unable to do its job:
it sums every h3 cell on earth into one ratio, so a regional jamming campaign is
diluted by global traffic. Through the July Gulf escalation it read 0.47% and
z = −0.12 while the airspace over Iran and the Hormuz approaches ran near 16%.
Its Reach was scored 3 (global) — the honest score for a *global average* is 1,
because it responds to nowhere in particular. Regionalizing it was investigated
and deferred this round (see 7.0), so the slot is better spent.

Candidates were ranked on the data, not on preference. The freshness rule (≤ ~2
days) eliminated `chokepoint_breadth` (10d), `port_throughput` (10d) and
`sofr_iorb_spread` (2.5d) outright. Of the five survivors, first-difference
correlation against the three remaining tier-1 lines eliminated `em_corp_oas`
as **redundant** (r = +0.74 against credit_spread — it is another credit
spread); `capital_premium` and `cn_flights` duplicate the domains cnh_cny and
flights already cover, at Reach 1; `grid_frequency` is orthogonal (max |r| =
0.22) but is Nordic-only and was blocked from tier-1 this round on its
statistic. `net_outages` is the only candidate that is GLOBAL, zero-lag, and a
domain no other line watches — and it is the only change available that widens
an instrument whose other three lines are EU/US/China-specific. A country going
dark leaks either a deliberate shutdown or an infrastructure collapse; both are
disorder, and both are invisible to every other line here.

**This promotion is PROVISIONAL and breaks the round-7 bar, deliberately and on
the record.** The v2 series has ~13 observations, far short of the 60 scored
readings this same round set as the promotion standard. It is taken because the
alternative — leaving a slot occupied by a line proven unable to see its own
domain — is worse, and because the status column now makes the weakness legible
on the page rather than hidden. **Pre-committed review at 60 scored readings
(~late September 2026):** if the tremble rate's Wilson lower bound exceeds 2%,
or the line proves to track IODA's detector coverage rather than the world, it
goes back to tier-2 and the slot runs empty and disclosed.
> **REVIEW HELD IN ROUND 11 (2026-08-04)** — early, because the IODA seed
> delivered 1,590 scored days at once. Outcome: CONFIRMED, with the tremble
> clause amended to episode terms at the moment its day-count letter fired.
> The full adjudication and the reason the letter was miscalibrated (applied
> evenhandedly it demotes credit_spread first) are in round 11. Also fixed as a
precondition: the fetcher now records WHICH countries are dark, because a count
alone makes a tremble unattributable and every tremble here must be answerable.

**The `status` column.** Every row now carries one of `scoring` / `warming-up` /
`stale` / `dark` / `no-spread`, and `summary.csv` gains `blind_count` and
`scoring_count`. A line reporting nothing was previously in one of six very
different states, all rendered as an empty z-score — which is exactly how a
strait closing went unnoticed for fifteen days: the only line watching it COULD
NOT SCORE, and that looked identical to calm. The dashboard's denominator is now
the number of instruments that could actually answer, so "0 of 4" can become
"0 of 3 · 1 line cannot score (not the same as calm)". Historical rows were
migrated by DERIVING status from what each row already said — dark from an empty
value, stale from its own note, scoring from a present z — never by re-scoring.

**PortWatch rebuilt (series v2, both trade lines).** The fetcher asked for the
newest available day and kept one row, so on six days out of seven it
re-recorded a reading it already held. PortWatch is a COMPLETE DAILY series
published weekly in seven-day batches: the fetcher was downloading the whole
week and discarding six sevenths of it. That, not the publication lag, is why
these lines held 6 distinct observations in 31 days and could not score at all.
v2 reads the observation exactly 10 days back — one new observation per
collection day — and both lines were seeded from the source's own archive
(`tools/seed_portwatch.py`, the `vix` precedent, replayed strictly in order so
no row is judged against its own future). Result: 6 distinct observations → 190
scored, with tremble rates of 2.1% and 1.1%. Every seeded row says in its note
that it was computed retroactively and was never a live detection.

**What this does NOT fix, stated plainly:** it does not close the Hormuz gap.
The reading is a 28-strait TOTAL and Hormuz is one or two percent of it — on the
day the strait closed this line moved UP. The alarm-direction tremble it does
record (observation 07-10, z = −4.63) comes from elsewhere in the basket. Seeing
a single strait needs a per-strait breadth COUNT, which is opened as a tier-3
candidate rather than built this round: it would be a second series break on a
line already broken today. Also noted: PortWatch REVISES history — the service
now serves 2,133 transits for observation 07-12 where the v1 record captured
2,137.

### Round 8 — 2026-07-23 (tier-2 red/blue divergence; cn_flights retired)

A diverge-then-adversarial round: six blue-team domain sweeps proposed candidates
(each required to probe a real free source), then every candidate ran through a
red-team attack and a neutral judge. Outcome: **16 rejected, 1 adjustment, zero
added.** A harsh screen is the honest one — the failure to fund is the finding.

**Acted on — RETIRE `cn_flights`** (structurally confounded, not underperforming;
do not re-litigate as "needs more readings"). Its alarm direction is *down*, and
its dominant confound — a community ADS-B feeder dropping offline — pushes the
count *down too*, so the sensor is collinear with its own failure and can never
separate "China grounded its metros" from "a Beijing receiver rebooted." Verified
live on the 32-row history: 2026-07-20 read Beijing=0 (physically impossible for a
metro), total 33, z=−2.41 in the alarm direction — a feeder outage wearing the
costume of an airspace collapse; Beijing then sat at 0/3/1/2 aircraft for four
straight days. The only tremble ever recorded (07-10, z=+6.07) was benign-direction
(coverage coming *on*). More data cannot cure a collinearity, and a normalization
cannot either (the dropout is per-metro and no keyless same-frame denominator is
exposed). A broken sensor pointed in the alarm direction is worse than an empty
slot — it manufactures the exact false "China air-traffic collapse" the instrument
exists to suppress. CSV archived to `data/archive/cn_flights_retired.csv`; the 8th
watchlist slot is now **open and disclosed** (the screen found nothing worth
filling it with).

**Why nothing was added — the pattern.** Almost every "new domain" candidate was
plumbing-clean (keyless, daily, fresh, real numbers) and died on the GUARD GATE:
they were free-floating physical or market-clearing reads dressed as guarded
equilibria. River gauges (`rhine_kaub`, a Mississippi stage), a Brazilian
reservoir level (`br_hydro_reserve`), French power net-exchange and nuclear
availability (`fr_net_exchange`, `fr_nuclear`), GB interconnector flows — in each,
nothing self-interested defends the level and pushes it back when it drifts;
scarcity or market coupling moving the number is arbitrage/weather succeeding, not
a guard being overpowered. That is the VIX/GDELT signature, and it fails the gate
categorically — no accumulation of readings converts a weather gauge into a
tension indicator. Two candidates passed the guard gate and still died on the
project's own statistics: `sofr99_dispersion` (SOFR99−SOFR is quantized to integer
basis points, so Qn=0 and the row is STATUS_FLAT on ~23% of windows — it literally
cannot score in the calm regime, failure mode #5 in terminal form) and
`taiwan_strait_transits` (an AIS gap-then-backfill artifact fires a false −7 to −11
"blockade" z on calm days, and it re-taps the weekly PortWatch pipeline).

**Adjustments screened and REJECTED (kept as-is, with the reason on record):**
- `grid_frequency` daily-max → minutes-outside-band: the duration statistic reads
  structurally zero on 41% of days at the honest ±100 mHz limit (failure mode #5),
  destroys the keyless Statnett fallback (a 60s snapshot can't compute a daily
  duration), and forces a baseline reset. The mild right-skew of the max (2 up-
  trembles in 32 rows) is the lesser evil. A skew-aware one-sided z on the existing
  max is the better idea, but it is a different, unbuilt change.
- `gnss_interference` regional-breadth: the ratio (hot/eligible) form does NOT
  divide out coverage growth — ADS-B feeders densify preferentially in already-hot
  theatres, so the breadth statistic drifts +43% over 24 months from the sampling
  frame alone (failure mode #1, the exact reason it was demoted in r7). Stays a
  global line.
- `chokepoint_per_strait_breadth`: the proposed volume gate (median ≥ 40) deletes
  Bab el-Mandeb, Panama, and Hormuz — the very straits the line exists to watch —
  from the panel. Rejected; `chokepoint_breadth` stays the 28-strait total.
- `capital_premium` keep-as-orthogonal: a label-only rebuttal that answered only
  one of the two demotion grounds; no change.

**Biggest gap still unaddressed** (unchanged from r7): the LEVEL-vs-CHANGE limit.
A rolling z is a change detector, so a sustained crisis reads calm once it sits
inside its own baseline — and notably, most of the rejected candidates fail *worse*
on exactly this axis (a heatwave-driven nuclear depression, a multi-week drought,
a year-long net-importer flip all go blind mid-crisis). Widening coverage does not
address it; only a level reference would, and that remains a deliberate open
question rather than a build.

**Added (provisional-watch): `polar_temp` — Arctic 80N temperature anomaly.** Not a
tension indicator: nobody guards the temperature of the Arctic, so it fails the guard
gate exactly as the river-gauge and reservoir candidates did, and it can never be
counted or promoted. It is admitted as a never-counted CONTEXT line — the first brick of
the long-horizon LEVEL layer that is this project's largest gap. Source verified live:
DMI (Danish Meteorological Institute) daily mean temperature north of 80N, keyless, ~1-day
lag, back to 1958. The reading is the anomaly vs the fixed 1958-2002 climate normal (that
normal is extracted once and vendored in `core/arctic_clim.py`, so the long baseline lives
in the repo and each daily row is self-contained — no decades of seed rows needed). The
huge seasonal cycle is removed by the anomaly; note the high-Arctic summer normal sits near
freezing (ice-melt pinned), so summer anomalies run small while the real warming shows in
winter — today's read is -1.04C, slightly below the historical summer normal. Collected
now to build history; how it is PRESENTED to aid interpretation is deferred until it has a
run of history and a designed readout (it is deliberately NOT on the dashboard yet). This
is the provisional-watch disposition working as intended: verified source, undecided role,
zero commitment to the counted instrument.

**Structure change — collapsed 4-8-16 into two tiers.** Tier 1 (counted) and tier 2
(collected, uncapped). The old "candidate ideas, not built" tier is gone: it produced no
data, so a candidate parked there could only ever be judged from n=0 — which contradicts
the project's own data-backed rule. Now, anything with a real guard and a PROBED working
fetcher is built and collected immediately; the only remaining funnel is tier-1 promotion
(≥60 readings). Unbuilt ideas move to a plain Backlog list. The bar to enter tier-2 stays
real because each collected line is a survivability liability — a verified fetcher and a
named failure mode, not just a plausible source.

**Built three ex-tier-3 lines** (their sources were re-probed live and returned real
numbers): `euro_hy_spread` (ICE BofA Euro HY OAS, keyless FRED — European credit fear,
orthogonal to US HY), `fx_parallel_premium` (Argentina blue-vs-official premium, keyless
dolarapi — a hard capital-control regime, distinct from cnh_cny and the Korea kimchi
premium), `hkma_aggr_balance` (HK currency-board aggregate balance, keyless HKMA API —
falls as the peg is defended under outflow). Four ex-tier-3 ideas stay on the Backlog
because they are not yet buildable as probed: `euro_fragmentation` (the probed ECB series
was monthly, not daily), `entsog_gas_flow` (needs point-selection design to avoid
aggregation dilution), `bgp_instability` (RIPEstat single-AS routing is not a global
instability measure), `cp_funding_spread` (a single FRED CPFF series is not a verified
CP-minus-funds spread).

### Round 9 — 2026-08-03 (bookkeeping: the registry catches up with the instrument)

Not a scoring round: **no tier moves, no threshold changes.** Everything below had
already happened in code and data over 2026-07-29..08-03; this entry makes the registry
stop lying about it. The one genuine scoring question that surfaced is queued at the end,
with the evidence bar it must clear.

**Registered.** The reachability gate (standing since 2026-07-30, now a third absolute
gate above); the `control_daylength` control line (added 2026-07-30, now in the tier-2
table); the empirical false-alarm rate on real credit data (5.5–8.5%/day, clustered
inside four real episodes — appended to Known limit 2).

**The FRED seeds, what they found, and what they cost.** `credit_spread`,
`em_corp_oas`, `euro_hy_spread` seeded to 787 observations each (back to 2023-08-01).
Found: ~20 three-line resonance days the live record was too young to contain (peak
2025-04-07: z=12.2 / 11.3 / 8.9), and credit_spread's "approach to threshold" of
2026-07-29 (z=+2.376) was a short-baseline artifact — the same observation reads
**z=+0.704** against the full record. Cost: the first seeder's merge silently deleted 26
published rows across the three lines, including a counted tier-1 dark day. Repaired
2026-08-03 from the preseed archives via the corrected merge (`tools/seedlib.py`, which
every future seeder now goes through); annotations 08-02/08-03 carry the correction.
**Consequence for this table: every reachability figure computed on 2026-07-29/30 for
the FRED lines is void** — em_corp_oas's alarm now sits INSIDE its observed range (the
2025-04 episode reached z=11), not beyond its record. Reachability must be recomputed
against seeded baselines before it is cited again.

**Seeded.** `polar_temp` to 2019-01-01 (2,740 rows; DMI's directory serves 2019+ only —
an earlier probe's "2017" claim did not survive contact with the source; DMI's 2023 file
is comma-separated where every other year is whitespace-separated, and the parser now
reads both). `gnss_interference` to 2022-07-27 (1,466 rows from 1,423 GPSJam daily files;
the raw bad/total counts are archived alongside, so the ratio no longer destroys its own
numerator at capture).

**What the gnss seed overturned, and what it did not.** Two of round 7's findings do not
survive four years of the line's own data. (1) The "tenfold growth in the sampling frame"
is 9 broken partial files out of 1,423 — by yearly median the frame grew 1.23x, not 10x —
so that half of the reason regionalization was deferred is void. (2) "It read 0.47% through
a Gulf air war and never moved" was a statement about a 39-observation baseline: re-scored
against the seeded record the July 2026 window peaks at **z = +2.87**, an approach to the
alarm, and across 1,452 scored days the line fires 49 alarm-direction trembles (3.4%)
clustered in real episodes. The line was under-powered, not motionless. What SURVIVES is
the demotion itself: 2.87 is still not 3, a worldwide ratio still cannot be trusted to
catch a regional campaign, and the other half of the deferral reason — candidate boxes
losing the detection when their edge moves one degree — is untouched. Regionalization
returns to the table with one of its two objections removed; it is not thereby approved.

**A level shift in a context line, found the same way.** gnss's monthly medians step from
0.19-0.25% (2022 through mid-2023) to ~0.44% after 2023-08 and never return: first-year
median 0.236%, last-year 0.388%, **1.64x**, with no single day ever unusual against its own
trailing 90. That is Known limit 1 in its purest form, in a second domain — and together
with polar_temp's 384-warm-to-4-cold asymmetry it is the argument that the level layer is
not a chokepoint-specific convenience but a missing organ.

**The level layer** (`tools/level_layer.py`, derived, unscored, uncounted, unmirrored):
pinned-reference state detection over the per-strait component record — open at 14
consecutive days of a 14-day trailing median ≤0.5× a pre-event reference (median of
t-365..t-60, ≥30 obs, ≥5/day), reference pinned at open, clear at 0.8× pinned. Replayed
over the full record it opens exactly two states: **Hormuz 2026-04-06, still open at
~14% of its pinned 72/day**, and Kerch 2026-05-14, self-cleared 05-19. Zero breach days
across the other 26 straits, including Taiwan through its July AIS artifact. This is the
first written answer to Known limit 1.

**Leg discipline for the spread family.** `sofr_iorb_spread` now differences same-date
legs only (an FOMC step can no longer manufacture a ~12-Qn jump out of misaligned
publication schedules). `fx_parallel_premium` maps weekend republish stamps to their
Friday, so obs-dedup finally fires for it (it had never fired once: frozen weekend
quotes were scored three times each). `cnh_cny`'s weekend darkness is now labeled as
market closure, which it is — the line goes dark every China-Sunday by construction,
and a Sunday dark_count=1 is a market fact, not a reliability failure.
`grid_frequency`'s Statnett fallback is disclosure-only now: a ~60-second max is not
comparable to the line's 24-hour max and is no longer scored into the same series.

**Pipeline honesty, after the audit.** Record audits (replay, component panel) moved
BEHIND the daily commit — the pre-collect gate runs pure logic only, because a
committed 27-strait day had made the old gate fail ahead of collection, which would
have silently cost every snapshot line every day until someone noticed. The daily push
rebases and retries instead of losing the day to a race with the intraday sampler.
Charts render only after the data is pushed. The docs mirror is an allow-list. Keyless
FRED requests are spaced 5s apart (the daily run was bursting five unspaced requests at
an endpoint with a measured 10-in-20s lockout). Components are keyed by observation
date. PortWatch short panels are disclosed in the note and acknowledged per-date in the
audit — obs 2026-07-24 arrived with NO Hormuz row (absence, not zero) on day ~146 of
the closure, the first short panel in 212 observations.

**Queued with data, deliberately NOT decided here: the resonance ceiling.** Under
current tier-1 baselines the headline count cannot structurally exceed ~2 of 4 —
cnh_cny's alarm needs +211 pips against a record max of 143, net_outages needs 8.3
countries against a record max of 6 — and a full replay of three years of real crises
never produced a headline above 1. Whether that means a tier-1 swap, a per-line
threshold review, or acceptance (a headline that is HARD to reach is not automatically
wrong) is the next radar round's question, and it must be answered against the
≥60-reading bar, not in a bookkeeping entry. `net_outages`' Qn-collapse exposure (47%
of the tied pairs needed for a zero scale, on a line whose real spike would then score
z=None) belongs to the same review.

> **RETRACTED IN ROUND 10.** The ceiling claim above is false, and it repeated the
> tiny-sample error this round had just caught elsewhere: +211 pips and 8.3 countries
> were computed against 41 and 25 observations. Measured properly, the headline reaches
> 2 about **1.9 days a year** at the lines' own replayed alarm rates, and the record
> shows no 2 because ≥2 tier-1 lines were simultaneously SCORING on only 33 of 800
> replayed days. The Qn-collapse exposure was real and is now fixed (`QUANTUM`). See
> round 10.


### Round 10 — 2026-08-04 (the calibration round: the bar, the floor, the rhythm, the drift)

A statistical audit of the scoring machinery against the seeded records — the first time
these questions could be MEASURED rather than argued. Four scoring changes ship together
under one **STABLE_SINCE = 2026-08-04**; two reporting changes and one new derived layer
ship alongside without touching a verdict. Full replay: **631 trembles become 619**, the
headline changes on no day, both adjudicated artifacts in the record are suppressed, and
every real credit episode survives.

**The bar now depends on the evidence.** See Known limit 2 — `_C_N`, calibrated so a calm
day has the same 0.3916% odds of a false tremble at any window size. The one thing it must
not be sold as fixing is the excess tremble rate on the slow lines: that is ~two-thirds
serial dependence (an AR(1) null at credit's own lag-1 of 0.987 already gives ~4.7%), and
c(n) removes exactly 1 of credit_spread's 66 trembles.

**A counted line gets a scale floor.** Qn collapses to zero once about a quarter of a
window's pairs tie — on a small-integer line the certain outcome of any calm stretch.
Verified against the real file: twelve consecutive days of "1 country" is enough, after
which a **160-country mass outage on tier-1 `net_outages` scores z=None**. `QUANTUM=1`
(one country, one basis point) floors the scale for `net_outages` and `sofr_iorb_spread`.
It has never bound on the record (smallest Qn used: 1.610), so it flips no published
verdict — it only prevents the future silence.

**The weekly rhythm is removed from the window, not carved out of it.** Same-weekday
baselining left ~26 readings permanently, the instrument's highest false-alarm regime,
locked in on a headline line. Above `DECYCLE_MIN = 70` observations each weekday's own
level is measured from the window and subtracted, and the day is judged against the whole
de-cycled window: measured false-alarm rate over flights' coming year 2.30-2.67% → 1.10-
1.20%, with 5-9 points more power on a real four-sigma collapse and the same weekend-dip
suppression the mechanism exists for. The gate is 70 because de-cycling a thin window eats
the spread it should preserve (18% false-alarm rate at three readings per weekday).

**Two weekly flags corrected.** `port_throughput` gains one — Sundays 8.0% light, Mondays
7.2% heavy, span 2.50x its own scale at permutation p=0.0001 over 211 observations, and
the rhythm was MASKING alarm-direction days inside the July 2026 Hormuz window (it reads
one tremble pooled, four de-cycled). `gdelt_tone` loses one: the volume rhythm is real but
the TONE does not follow it (span 1.61x, p=0.58), and claiming a rhythm that is not there
costs sensitivity.

**Episodes, not days** (`tools/episodes.py`) — Known limit 3. No rule changes; the
vocabulary does.

**The drift layer** (`tools/drift_layer.py` → `data/drifts.csv`): a two-sided clone of the
level layer for the third shape — a whole line's level moving and staying moved. A line is
DRIFTED when its two-week median has run ≥1.5x above (or ≤2/3 below) its own year-ago
median for 28 straight days, reference pinned at the open, clearing within 20% of the pin.
Over 3,882 judged line-days the entire record opens **exactly one state**: gnss 2023-07-09
to 2023-11-19, the real jamming escalation, at +38 days. Zero false states. Robust CUSUM
was tested and disqualified (21-216 alarms per line). Declared blind: undefined on a
series crossing zero, and blind to a ratchet slow enough for the trailing reference to
absorb.

**Yearly medians**, the one view that sees the drifts a ratio rule provably cannot (the
Arctic anomaly is an interval scale; gnss's post-2023 creep is absorbed by any trailing
reference):

| line | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
|---|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|
| credit_spread | — | — | — | — | 3.905 | 3.17 | 2.94 | 2.8 |
| em_corp_oas | — | — | — | — | 2.595 | 1.9 | 1.64 | 1.49 |
| euro_hy_spread | — | — | — | — | 4.41 | 3.45 | 2.96 | 2.65 |
| vix | — | — | — | — | — | — | 16.92 | 17.965 |
| gnss_interference | — | — | — | 0.2289 | 0.2937 | 0.3892 | 0.36875 | 0.4185 |
| polar_temp | 2.233 | 3.205 | 2.213 | 2.478 | 2.3265 | 2.5115 | 3.276 | 2.6655 |
| chokepoint_breadth | — | — | — | — | — | — | — | 1897 |
| port_throughput | — | — | — | — | — | — | — | 4862 |

Read the gnss row: 0.229 → 0.294 → 0.389 → 0.369 → 0.419. The credit rows show the mirror
image — a four-year compression from 3.905 to 2.8 with no episode to point at. Neither
motion is visible to any single day's z.

**The resonance ceiling claim of round 9 is retracted** — see the note inline above. The
headline reaches 2 about 1.9 days a year at the lines' own measured rates; the record has
none because ≥2 tier-1 lines were simultaneously scoring on only 33 of 800 replayed days.
> **CORRECTED R16.** Both figures in that last sentence are wrong. Re-measured from the
> replay: ≥2 tier-1 lines were simultaneously SCORING on **~778 of 796 days (97.7%)**, not 33 —
> the "33" was the ≥3-scoring count (~32), mislabelled and paired with the wrong denominator.
> So the record's lack of a 2 is NOT a co-scoring problem; the lines co-score almost always.
> The real reasons: the alarms are rare and near-independent (credit 8.3%, net 3.5%, flights
> 2.2%, cnh_cny 0.0% of scoring days), so a same-day double is intrinsically ~1/year (the
> "1.9/yr" is the iid MODEL; the realized rate over 3.04y is 3 doubles ≈ 0.99/yr), and the
> live 4-line record is only 56 days old with cnh_cny never once trembling in alarm. See round 16.
What survives is that the PAIR matters more than the count: `cnh_cny` and `net_outages`
sit at their calm nulls, so a double involving either is near-certainly signal (all-null
P(count≥2) = 0.0076%/day, once in 36 years), while `flights` is the headline's dominant
noise source. The dashboard now names which lines are firing whenever the count exceeds 1.

**The `flights` feed-dropout guard was examined and NOT built** — see the annotation of
2026-08-04. It cannot live in a stateless fetcher without coupling it to the record, and
more importantly the evidence does not support the diagnosis: on 2026-07-22 at least two
of the three aggregators independently agreed the US East sky was that empty, so a
shared-upstream failure and a real ground-stop are indistinguishable in what was recorded.
The capability to tell them apart next time already exists (the intraday sampler from
2026-07-29, per-provider components from 2026-08-02); it merely postdates the event. A
rule that darkened such days would make the instrument assert a cause it cannot know.

**`net_outages` is seeded** (2022-01-26 onward, 1,646 rows, 1,590 scoring, 4.52 years) and
the seed changed what we know about it in two directions. It is far MORE reachable than
recorded — the 2026-07-29 note said its alarm needed 8.3 countries against a record max of
6, but that max was 25 observations deep; the real distribution reaches 45 and the line
fires 55 times in four years, 3.5% of scored days across 35 episodes at lag-1 0.363. And
it is dirtier than recorded: the two known IODA self-outage days are actually **twelve**,
each a day the monitor reported essentially every entity it watches as dark (220 of 222 on
2025-03-25, Antarctica and Andorra included, recovered the next day). Those are now refused
at the fetcher on a measured conjunction — count ≥100 AND ≥80% of everything watched,
which selects exactly those 12 of 1,621 with the nearest non-selected day at 45 countries
and 45%. The line's promotion review can now actually be held.

**Still open after this round:** the tier-1 composition question itself — a promotion
review at the ≥60-reading bar, which `net_outages` now clears by a factor of twenty-six;
and whether `MAX_AGE_DAYS = 180` still binds correctly now that de-cycling shortens the
effective baseline span.
### Round 11 — 2026-08-04 (the tier-1 composition review: held, and the set survives it)

The review the registry has owed since round 7.1 — held early because the IODA seed
delivered `net_outages` 1,590 scored days at once. Every number below is replayed under
STABLE_SINCE=2026-08-04 rules and the six that drive decisions were adversarially
re-derived by independent verifiers. **No tier moves.** The composition survives its
first full review, with one pre-commitment adjudicated and amended, one new
pre-commitment issued, and two candidates entering the Backlog.

**`net_outages`: CONFIRMED, and the pre-commitment is amended at the moment it fired —
on the record, with the reason measured.** The round-7.1 clause said: demote if the
tremble rate's Wilson lower bound exceeds 2%, or if the line tracks IODA's detector
coverage rather than the world. Adjudication: the SECOND clause does not fire —
corr(hits, coverage) = 0.184 excluding sweeps, and the median count stayed 2-4 while
IODA's watched-entity count halved, which is what "measures the world, not the sensor"
looks like. The FIRST clause fires on its day-count letter (57/1,625 = 3.51%, Wilson LB
2.72%) and clears on episodes (37 episodes, rate 2.28%, LB 1.66%). The letter is
provably miscalibrated: applied evenhandedly, a 2% day-rate bar demotes `credit_spread`
FIRST (its replayed day-rate Wilson LB is 6.63% — 8 episodes, all four real events),
and round 10's Known limit 3 already established that day counts overstate independent
alarms on autocorrelated lines. The clause was written in round 7.1 before episodes
existed as a vocabulary; its intent — "demote a line that cries wolf" — is what the
episode reading measures. AMENDED: the demotion bar for any pre-committed rate review is
the EPISODE-rate Wilson lower bound against 2%. Everything else about the line passed
outright: all three gates (alarm at ≥9 countries today, the 93.6th percentile of its
record, max observed z=20.2; 24h cadence, longest real run 7 days), zero-lag freshness,
orthogonality ≤0.141 against every tier-1 line, 26/26 live reliability with 12/1,626
source-integrity refusals (the guarded IODA sweeps) disclosed separately. Its largest
attributable episodes: the November 2022 Ukraine grid-strike runs and the 2025 Iberian
blackout.

**A correction inside the confirmation:** the 2026-08-04 seed annotation called the
45-country day of 2022-03-02 "the week of the Ukraine invasion." Its own country list
contains neither Ukraine nor Russia; it is the sweep guard's nearest non-selected day
(ratio 0.45) and its cause is unattributed. The attribution is withdrawn in
annotations.csv. Also recorded: the seed's STORED verdicts differ from current-rule
replay on 34 scored days / 2 trembles (pre-STABLE_SINCE seam, expected and legal) — any
future arithmetic on this line must replay, not read stored cells.

**`flights`: RETAINED WITH CONDITIONS — the honest middle of a genuinely split case.**
Against: under current rules its entire alarm record is one fire, the adjudicated
2026-07-05 artifact (replayed z=-5.726, a Sunday scored against a weekday-mixed window
at same-weekday n=6), making it the only tier-1 line whose current-rule record contains
zero real detections. For: the c(n) table has ALREADY retired its second artifact
(07-22 replays at z=-3.014 against threshold_for(30)=3.291 — under today's rules it
never fires); its rate at n=34 carries a Wilson interval of [0.5%, 15%], and Known
limit 4 reads symmetrically — below 60 readings, rate evidence can neither promote nor
demote; it was seated in round 1 with zero readings, a month before the bar existed —
grandfathered, never promoted past it; it is the registry's only airspace line, with no
tier-2 successor and a measured non-find where one was sought; and the instrumentation
that would have adjudicated 07-22 (the intraday sampler, per-provider components) now
exists but postdates the event. CONDITIONS, both pre-committed and both measurable:
(a) review on **2026-08-31**, the day weekday de-cycling engages (row 71, verified
through the scoring path) and the record passes 60 scored days — demote if the replayed
episode-rate Wilson lower bound exceeds 2%, the same amended bar as everyone else;
(b) demote immediately on the next alarm-direction tremble the new instrumentation
cannot adjudicate — the ability to settle such a day now exists, so an unsettleable day
is henceforth itself disqualifying.

**Orthogonality, measured for the whole registry** (replayed z, obs-date keyed, Pearson
with Spearman cross-check): the tier-1 set is clean where measurable — the one pair
with ≥40 shared dates, credit_spread × net_outages, reads **+0.035** (n=766); the five
thin pairs all sit ≤|0.103| but stay formally open until the young lines mature
(~mid-September). The credit-fear family is the only correlated block anywhere
(credit_spread / em_corp_oas / euro_hy_spread / vix, six pairs at 0.548-0.863), which
**decisively bars em_corp_oas (+0.805) and euro_hy_spread (+0.737)** from tier-1 —
depth was never their problem; independence is. Every non-credit candidate is
orthogonal to tier-1 (max |r| 0.195) and barred by a different gate instead: reach
(gnss — its alarm is reachable by exactly 1 observed day in 1,463; grid_frequency;
capital_premium) or freshness (the PortWatch pair). The largest cross-family
correlation in the registry is gnss × polar_temp at −0.325, plausibly seasonal, worth
an eye and nothing more.

**Diverge:** three candidates, all of which changed shape when probed properly in
R11.1 — see that entry. Two of this paragraph's original claims did not survive
(`fed_srf_takeup`'s "calm ~$0-2B" was off by three orders of magnitude and its
"needs a QUANTUM floor" was the opposite of what the data says), and `tga_balance`
turned out to be buildable after all once the reading was changed from the balance
to the balance divided by the burn rate. The two most orthogonal guarded domains —
marine war-risk premia and sovereign CDS — have **no free daily source**; recorded
as non-finds so the search is not repeated.

**What this round says about the instrument:** the first full composition review found
the set defensible but young — one line confirmed on four years of evidence, one
retained on grandfather rights with its exit conditions now written down, two slots
(cnh_cny's reach cell, five of six orthogonality pairs) formally open until September.
The review mechanism itself worked the way the project wants: a pre-commitment fired,
was adjudicated against measurement rather than kept or waived by taste, and the
amendment is recorded next to the clause it amends.

### Round 11.1 — 2026-08-04 (the three candidates, probed properly; one built, two blocked)

Round 11 named three candidates on a single reconnaissance pass. Probed properly — every
claim below comes from a response actually received — **one is built, two are blocked,
and two of round 11's own numbers were wrong.** The corrections are made in place above.

**BUILT: `tga_days_cash`** (tier 2). Round 11 filed the Treasury General Account as
drift-shaped and unscoreable, and on the BALANCE it is: routine single-day swings run to
$121bn, the level regime moved by trillions after 2020, and tax dates impose a calendar
rhythm this repo cannot remove. The reading was changed instead of the verdict — closing
balance divided by the trailing 20-business-day mean withdrawal, giving **days of its own
outflows**. That normalizes the level, the regime and most of the calendar at once, and it
is not a statistical trick: a buffer is only large or small relative to what is being
spent, so when outflows spike the buffer really is shorter and the line falls without the
balance moving. The guard becomes VISIBLE rather than asserted — Treasury says it targets
about a week of outflows, and the median of the served history is **5.3 business days**.
The leak is sharp: **the June-2023 X-date reads 0.21 days**, and 72 days of 2023 sit below
3.0. Keyless, business-daily, T+1. One field trap is recorded in the fetcher because a
module written from the schema alone ships broken: `close_today_bal` is the literal string
"null" on every modern row and the value lives in `open_today_bal`. Both sides of the ratio
are captured as components, because a ratio destroys its own inputs and this project has
paid for that lesson once already.

**BLOCKED: `fed_srf_takeup`** — and round 11's entry for it was wrong twice. The guard is
excellent (the Fed posts the SRF as a defended ceiling and allots in full twice every
business day; take-up IS the guard being borrowed from) and both gates pass cleanly. The
source is keyless and one request rebuilds the whole SRF era. What kills it is the scale:
**61.4% of SRF-era days are exactly zero**. Replaying this repo's own `normalize` over
1,251 days measures the two available options and neither is honest — with no floor, Qn is
exactly zero on **79.4% of windows** and the line is blind four days in five (the
`sofr99_dispersion` rejection was made at 23%); with `QUANTUM=1` at the source's true $1m
resolution it fires **174 times in 1,241 days, twenty-one of them on $4 million** of
take-up against a facility with a $500bn limit. Round 11 recorded "calm ~$0-2B" — the calm
median is **$1 million**, three orders of magnitude out — and "needs a QUANTUM floor",
which is precisely the fix the measurement disproves. It stays on the Backlog until there
is a materiality floor with its own semantics, or an episode layer for structurally-zero
series. Two traps are recorded there for whoever builds it: filtering on `method=allotment`
returns HTTP 200 and silently truncates the history to 2025-12-11 (the Fed relabelled the
operations mid-series), and seeding from the endpoint's full range splices in the 2019-20
emergency repos and the 2000-08 daily OMOs — a different facility at $100-150bn scale that
would make the real 2025 episode look unremarkable.

**BLOCKED: `eu_gas_storage`**, designed and then declined on sourcing ethics. The design is
right and worth keeping: the raw fill percentage is dominated by the seasonal injection
cycle, so the honest reading is the **weekly fill change minus the seasonal-normal weekly
change** — "did the EU lose ground against its own refill path this week". AGSI+ carries
it cleanly (daily since 2011-01-01, 5,693 rows, zero missing days) and today reads −0.61
pp/week against a level that is 15.5 points behind its same-day-of-year normal — which is
exactly the split the design predicts, a line that correctly says "not getting worse this
week" about a situation that is already bad. But AGSI+ **requires a free registered key**,
and the only keyless path that works is a spoofed browser User-Agent. This project does not
ship that: the service asked for a registration, and evading it with a fake identity is not
a sourcing practice an instrument about honesty can hold. ACTIONABLE and one step: register
at agsi.gie.eu, add `AGSI_KEY` to repo Secrets, vendor the 365-entry seasonal-normal table,
and it is build-ready.

**The pattern worth naming.** All three round-11 entries were written from one
reconnaissance pass each, and all three were wrong in some load-bearing way — one verdict
inverted, one line's calm regime off by 1000x, one design missing entirely. A candidate is
not characterised until something has replayed the repo's own scoring over its actual
history. That is now the bar for a Backlog entry claiming "build-ready".

### Round 12 — 2026-08-14 (the chokepoint blind spot: measured, sourced, and its fix located outside the scoring path)

Triggered by the 2026-08-04 Hormuz correction (commit 6455f2a): two straits stuck quiet at
once — Hormuz and Kerch — while the scored `chokepoint_breadth` z sat at ±0.3. The question
was whether that is a coverage gap, a detector gap, or a reporting gap. Answer, every
decision-driving number independently re-derived through the repo's own `normalize`: a
**reporting gap in an organ that already exists and already fired**. No tier moves, no new
fetcher; one honesty fix to the level layer's docstring, and one design recorded as
recommended-but-approval-gated.

**The SUM cannot reach its own alarm on a small-strait closure — measured, not argued.**
Against the line's own machinery (`core/normalize`: Qn scale, `threshold_for(n)`) over the
trailing WINDOW=90 of the 28-strait total: Qn ≈ **81 transits per z**, centre 1914, so the
−3z alarm sits **243 transits below centre**. Hormuz's pinned reference is 72/day and
Kerch's 12/day; a **full simultaneous closure of both** removes 84 transits = **1.04 z**,
only **35%** of the way to the alarm — you would need **3.4 Hormuz-sized straits to close at
once** for the sum to fire. This is the reachability gate (a standing absolute gate) failing
not for the line but for a whole event class: "one or two small straits go silent" is
unreachable for a 28-strait sum by construction. And because a closure ramps gradually the
rolling baseline absorbs it (Known limit 1), so the sum reads calm on the way down as well
as at the bottom. (Qn is 78.9 or 81.0 depending on whether today's just-written row sits in
the window; the estimator-faithful history window — the one `robust_z` actually uses to
score the newest reading — gives 81.0, and reproduces 1.04z / 35% / 3.4 exactly.)

**Not a coverage gap.** A sweep for a free, ~daily, per-strait maritime source with a
shorter lag than PortWatch's ~5–10 days returned a **non-find**, recorded so the search is
not repeated. The nearest technical match, TankerMap (`/api/analytics/chokepoints`: keyless
JSON, ~0 lag, and it emits explicit 0s — a better closure shape than PortWatch's missing
row), is disqualified on data quality: tanker-only, self-declared `confidence=unknown`, and
it undercounts Hormuz by ~90% (avg ~1.3/day vs the real ~25–30), so a genuine closure is
indistinguishable from its everyday noise. Every free real-time AIS feed (AISstream, AISHub,
StraitScope) needs a key, serves raw positions not per-strait counts, or covers one strait —
i.e. re-implementing PortWatch against a worse terrestrial, coverage-gapped sensor.
Kpler/MarineTraffic/Vortexa/EMSA are paywalled or access-restricted (the war-risk-premia /
CDS pattern again). PortWatch stays the source; the fault is the aggregation, not the sensing.

**Not a detector gap either — the level layer already fired.** `tools/level_layer.py` holds
two states OPEN right now: Hormuz since 2026-04-06 (7% of its pinned 72) and Kerch since
2026-07-26 (0% of its pinned 12) — the second a re-closure after the 05-14→05-19 self-clear.
A COUNT over those states (a state/episode count, never a rolling z — a count-of-stuck-straits
is structurally zero and would drive Qn=0 exactly as `fed_srf_takeup` does, R11.1) reads
**2** on the day the sum reads calm. The organ exists and works.

**The gap is that the count is not SERVED — and it must not be served through the summary.**
The tempting move, a `stuck_count` column in `data/summary.csv`, was probed against the code
and **rejected**: it breaks three load-bearing guards at once. (1) `tests/test_level.py`
(`test_scoring_code_never_reads_the_level_file`) forbids the scoring path from containing
even the string `"levels"` — the firewall whose stated why (`tests/test_side_channel.py`) is
that "a diagnostic file becomes an input to a verdict, and the separation that makes it safe
is gone". (2) `tools/replay.py` re-derives all three summary counts from the **replayed
tier-1 rows** and fails `--check` on any mismatch; a count sourced from the tier-2 component
record, recomputed from scratch over a growing union panel with backfillable values, is not
forward-only and cannot be re-derived that way. (3) `collect.py` declares the summary holds
"only the tier-1 aggregates" (and would not double-count — chokepoint is TIER=2, so it adds
nothing to trembling/dark/blind today — but disjointness is bought by breaking the other two
guards). The correct home is a **separately-served diagnostic**: mirror `levels.csv` (or a
derived open-state count) into its own dashboard panel, read by `render.py` or a new `tools/`
reporter that lives OUTSIDE the scoring path — which honors the mirror allow-list as a named
serve and is legitimately exempt from forward-only because it is recomputed each run.
**RECOMMENDED, approval-gated (touches the dashboard, not the scoring path); not built here.**

**absence-as-breach: rejected.** The deeper worry the 08-04 commit named — PortWatch emits
no row for near-zero traffic, so the most alarming state arrives as a missing row — cannot be
promoted to a scored or counted breach. Two of this round's own working premises were wrong
and are corrected here: no obs day ever served 4 straits (the component panel histogram is
{27: 2, 28: 221}); the only short panels are obs 07-24/07-25 at 27 straits with the Hormuz
row absent. And the Taiwan July artifact such a rule would have to survive was never an
absence — Taiwan was present at low-then-backfilled values (277→28→401) — so a "require the
rest of the panel complete" guard defends against the wrong artifact class while coupling
each strait's alarm to every other strait's completeness (a real no-row closure coinciding
with any unrelated single-strait drop would be silently suppressed). The one genuinely
uncovered case — an instantaneous full closure served as no-row with no 14-day ramp — is,
without a human, indistinguishable from a pipeline drop, which is exactly why it already
lives correctly as a post-commit ALARM (`audit_record.py` ACKNOWLEDGED_SHORT / ONGOING_ABSENT):
on 07-24/25 that alarm took three days of direct queries to classify, was briefly entered as
ONGOING_ABSENT on 08-04, and self-revoked on 08-05 when obs 07-26 returned non-missing at 3
transits (commit 6455f2a). An automated persistence threshold cannot beat that — short fires
on transient hiccups, long adds nothing, because once the strait resumes at a low value the
level layer's value-based OPEN already sees it.

**Honesty fix applied:** `tools/level_layer.py`'s docstring said the record "opens exactly
two states: Hormuz … and Kerch (2026-05-14, self-cleared 05-19)" at "~14%". It now opens
three across two straits (Kerch re-closed 07-26, still open) and Hormuz runs at 7%. Docstring
corrected to the live state; no logic touched.

**Method note.** The reachability arithmetic, the source sweep, and the firewall analysis
were each run as an independent agent and cross-checked against the raw CSVs and the actual
tests — the R11 discipline ("a claim is not characterised until something has replayed the
repo's own scoring / read the real code"), which this round twice needed: it caught the
non-existent 4-strait day and the misspecified Taiwan guard before they reached this page.

### Round 13 — 2026-08-15 (metrics refresh + three candidates probed live; no tier move is due)

A general calibration round with no forced decision: the two tier-1 lines carrying open
questions are both under the ≥60-reading bar — **flights** at 55 scored (review pre-committed
2026-08-31) and **cnh_cny** at 52 — so the discipline says refresh the numbers and defer the
rulings, which is what this round does. **No tier moves.** Every figure below is computed
against the repo's own `core/normalize` (Qn, `threshold_for(n)`) or a hand Pearson, on the
committed CSVs; the three candidates were each live-probed (an endpoint actually hit).

**Reliability, refreshed.** Tier-1 is near-perfect: flights 55/55, credit_spread 0.999,
net_outages 0.993 (12 IODA all-dark days), cnh_cny 0.945 — and cnh_cny's 3 dark rows are all
yuan-spread rejections (legs quoted ~24 h apart / weekend freeze), a market fact the line
discloses, not a fetch failure. The one weak line anywhere is `hkma_aggr_balance` at 0.833
(4 dark of 24) — young and thin; watch, do not rule (n=24).

**Reachability, recomputed for the three maturing lines.** flights (n=55) REACHABLE with room
(alarm 566 flights off the median vs an observed 683 move, 0.83×); sofr_iorb_spread (n=54)
comfortable (0.58×). **cnh_cny (n=52) is the finding:** its threshold is symmetric, but its
guard is not — the ALARMING direction is UP (offshore yuan weaker = capital flight), and a +3z
up-alarm needs **+227 pips against a 52-obs record high of 143**, so within this young calm
record the alarm side is a decoration. Two things keep that from being a demotion. First it is
**baseline-relative** (the standing caution since R7/R9): the record is 52 days of calm, and
real capital-flight episodes have blown CNH−CNY hundreds of pips wide, so a world-resembling
stress day *does* reach the alarm — the young record simply has not sampled the tail. Second,
the line is not motionless: it fired four |z|>3 trembles (to −45 pips), but **all four are
DOWN** — the benign direction (offshore yuan *stronger*, the guard comfortable), which do not
feed the alarm count, so R11's "0 alarms" stands exactly. Queued for the maturity review:
recompute this at n≥60 and decide whether the alarm-direction reach is a young-record artifact
(expected) or a real ceiling.

**Orthogonality — the R11 open question largely closes.** R11 could measure only one tier-1
pair at ≥40 shared dates (credit_spread × net_outages, +0.035). Now **four of six pairs cross
≥40**: credit × net_outages +0.036 (n=775, the anchor, unchanged), flights × net_outages
+0.013 (45), flights × cnh_cny +0.088 (40), cnh_cny × net_outages +0.017 (40). Every measured
pair sits **below |0.09|** — the tier-1 set is confirmed orthogonal where it can be measured,
the largest coupling being the young, bare-40 flights × cnh_cny at 0.088. Two pairs remain thin
(flights × credit_spread n=29, credit_spread × cnh_cny n=27) and should cross ≥40 around
mid-September; nothing about them looks non-orthogonal.

**Explore — three candidates, each live-probed; two added to the Backlog, one advanced.**
- **border_wait (ADDED).** A genuinely new domain — land chokepoints, orthogonal to the
  maritime (PortWatch) and air (ADS-B) lines. `bwt.cbp.gov/api/waittimes` is live, keyless, real
  JSON (85 land ports). Guard real; but the raw feed fails the cadence gate until an aggregation
  design removes the commuter intraday cycle (fixed-hour daily scrape of COMMERCIAL lanes) and
  separates UNSCHEDULED closures from the nightly scheduled ones. National reach, no historical
  backfill (build forward). Strongest new find of the round; parked on the aggregation design.
- **usd_xccy_basis (ADDED).** The cleanest guard in the whole registry — a deeply negative
  cross-currency basis is *literally* what the central-bank USD swap lines defend, cadence and
  reachability both pass (−150 to −200 bp in 2008, −80 to −140 bp in Mar-2020). But keyless daily
  sourcing is **EXHAUSTED**: FRED is spot-only (no forwards), OFR STFM has no FX series, ECB
  spot-only, forward points paywalled, CME's index needs a key. Recorded as a non-find so the
  keyless search is not repeated; parked on sourcing like `eu_gas_storage`.
- **cp_funding_spread (ADVANCED, still blocked).** The open construction doubt is resolved:
  FRED's `CPFF` IS exactly (3M AA-financial CP − fed funds), verified to the cent. But the probe
  moved the blocker from construction to **cadence** — the term-CP leg is blank on a
  ~50%-and-rising, stress-clustered share of business days, with the entire 2023-03 SVB window
  missing, so a daily differenced z would have to fill across exactly the gap that carries the
  signal. It needs a denser term-CP source or the same gap-tolerant / episode cadence layer that
  `fed_srf_takeup` is waiting on — a second Backlog line now pointing at the same missing organ.

**What the round says about the instrument.** The two structural gaps the Backlog keeps
re-deriving are now named twice each: a **sourcing** wall (guarded quantities with no free daily
feed — marine war-risk, sovereign CDS, the xccy basis) and a **cadence** wall (guarded quantities
that are keyless and daily-shaped but structurally sparse — `fed_srf_takeup`, `cp_funding_spread`).
Neither is closed by more coverage; the first needs a key the project will accept, the second an
episode/gap-tolerant scoring layer this repo does not yet have. Both are the honest next frontiers,
recorded so the next round starts from them rather than rediscovering them.

### Round 14 — 2026-08-15 (crypto, probed and built: one line ships, and its own replay names the wall)

Three crypto candidates were live-probed (an endpoint actually hit each time), and the
strongest was BUILT — then its own replay against this repo's scoring told the honest story.

**BTC/ETH price — contrast-only, not a candidate.** A free-floating asset with no defended
anchor fails the guard gate, exactly as `tail_risk_market` did. It could only ever be a
felt-vs-real contrast read like `vix`, never a counted tension line; recorded so it is not
re-proposed as an indicator.

**`stablecoin_peg` — BUILT (tier 2), and moved out of Rejected.** Its old rejection
("depegs are intraday-transient, a daily snapshot aliases past them") does not survive the
SVB counter-example: USDC held below peg for ~3 days over the March-2023 weekend, a
**close-visible, multi-day** event, not a flash-wick. The line scores the worst-of-{USDC,USDT}
deviation-from-$1 in bp, off the **settled daily close** (so a sustained depeg counts and a
recover-by-close wick does not — the cadence objection answered by design), from keyless
Bitstamp OHLC, one source for both the live feed and a **seed back to 2020-10 (2127 obs)**.
The guard is clean and the reachability is not arithmetic but **demonstrated**: USDC's SVB
close $0.9685 scores **z=122**, and the FTX (Nov-2022) and UST (May-2022) episodes are in
the record. Guard 3 / Reach 3 (global) / source keyless + deep.

**But the build's own replay found the wall, and it is the Round-13 wall.** Scored through
the current rolling z the line fires **214 trembles ≈ 10% of days** (15% across 2026) — not
on stress, but on USDT's ordinary ~10bp Bitstamp venue discount, because a folded
near-constant series has a Qn of ~3bp and z=3 arrives at ~19bp. It cannot be fixed by a hard
floor to zero: that recreates the **structural-zero** failure that blocks `fed_srf_takeup`
(Qn→0). So `stablecoin_peg` ships **collected + PROVISIONAL** — the data is real and the
crises are in it, it is tier-2 and therefore uncounted, and it is **not promotable until a
materiality-floor / episode layer exists**. That is now the SECOND line (with `fed_srf_takeup`,
and adjacent to `cp_funding_spread`) waiting on the same missing organ — the cadence wall
Round 13 named, now with a shipped, replayable line sitting against it rather than a Backlog note.

**`crypto_capital_flight_premium` — Backlog.** Guard real (the cnh_cny / fx_parallel_premium
capital-controls guard) and it PASSES the cadence gate a depeg fails (a controls premium is
structural, persisting for weeks). Binance P2P adv/search is keyless and live. But the set
reachable ∩ orthogonal ∩ strong-guard ∩ clean-keyless-official-leg is nearly empty: ARS and
CNY are redundant with existing lines, NGN/RUB return zero ads (Binance banned/exited),
TRY/EGP are weak-guard floats, and the one orthogonal hard-controlled case (Venezuela VES)
has no keyless TRUE-official leg — the easy source tracks a near-parallel rate and collapses a
real 85% gap to 14%. Parked on official-leg sourcing, the `usd_xccy_basis` shape.

**What the round adds to the instrument.** A candidate was not just characterised on paper but
BUILT and run against the repo's own scoring — and the scoring, not an argument, is what set
its disposition: guard and source clean, cadence-reject overturned, yet provisional because the
rolling z is the wrong organ for a pegged instrument. The materiality-floor / episode layer is
no longer a Backlog footnote; it is the thing standing between three real, sourced, guarded
candidates (`fed_srf_takeup`, `stablecoin_peg`, `cp_funding_spread`) and a countable reading.

### Round 15 — 2026-08-16 (the materiality wall, answered: anchored scale-mode, built into the scorer)

Round 14 ended with three real candidates jammed against one wall. Rather than bolt a fourth
fix on, this round stepped back to the whole scoring structure and asked what that wall actually
is. It is one wrong assumption: the change layer's rolling z assumes **normal = the recent
window**. For an anchored series that is false — normal is a DECLARED constant (a $1 peg, a $0
facility take-up), and the rolling window is a broken estimator of it (tiny Qn → cries wolf; zero
Qn → goes blind). This is the same realization `level_layer` (pinned reference) and `drift_layer`
(year-ago reference) already made about the CENTRE; scale-mode makes it about the SCALE.

**The design was adjudicated, not guessed.** Three independent architectures were proposed and
adversarially scored: a minimal scale-mode, a new diagnostic episode/breach layer, and a full
per-line reference+scale abstraction. The **minimal scale-mode won**: it is the smallest change
that is still fully general, and the only one that keeps these lines COUNTED (a depeg is a genuine
onset the resonance should count, not a slow level state) — for an anchored series the CHANGE
question and the LEVEL question coincide, because the recent past IS the anchor. The episode
layer's best idea (a multi-day crisis is one episode, not N independent alarms) is grafted as a
FUTURE diagnostic overlay via `episodes.py`, gating promotion; it is not a reason to exile these
lines to an unscored layer.

**What shipped (opt-in, provably additive).** A line may declare `ANCHOR` + `MATERIALITY`
(module attrs, exactly like `WEEKLY_CYCLE` / `QUANTUM`). When `MATERIALITY` is set, `robust_z`
short-circuits immediately after the `today is None → DARK` guard: `z = (today − ANCHOR) /
MATERIALITY`, status SCORING, n = window → the flat 3.0 bar, so **3·MATERIALITY IS the smallest
material move**. Four small edits carry it — the one branch in `normalize.robust_z`, the forward
in `normalize.judge`, and two keys in `collect.scoring_attrs` (the single place three callers read,
so replay and the seeders inherit it for free, the seam the net_outages QUANTUM bug taught). It
**reads only `today`, never `history`**, so it structurally cannot forward-fill a gap (a missing
reading still returns DARK); a declared constant has no sampling wobble, so it needs no warm-up
and takes the flat bar honestly; `_scale_z`, `classify`, `threshold_for`, `_qn` are byte-for-byte
untouched. `QUANTUM` and `MATERIALITY` are asserted mutually exclusive. **Proof of no blast
radius: 111 tests green, and `replay.py --check` shows 0 post-STABLE_SINCE divergence on every
existing line** — a line that does not opt in scores identically, so no STABLE_SINCE bump.

**`stablecoin_peg` retrofit, replayed.** `QUANTUM=1` removed; `ANCHOR=0`, `MATERIALITY=25bp`
(alarm at 75bp). Over the 2127-obs seed the rolling z fired **214 trembles ≈10%/day** on USDT's
ordinary ~10bp Bitstamp venue discount; scale-mode drops that to **3 (SVB 2023-03-11 z=12.6,
03-12 z=3.4, a 2021-01-07 wobble), 0 blind**, and 2026-06-01 falls from z=5.3 to z=0.51. The
close-based measure keeps FTX (~31bp) and UST (~48bp) as visible ~z=1.3 bumps, not trembles —
disclosed, not hidden; drop MATERIALITY toward ~12–15bp if that class is later judged material.

**What it unblocks.** `fed_srf_takeup` is now BUILD-READY — its structural-zero wall is exactly
what an anchored z with a declared materiality dissolves ($0 → honest z=0, a $20bn scramble →
z=4). `cp_funding_spread`'s scoring is unblocked too (each present day honest, no
differencing-across-a-gap), but it stays parked on SOURCING — scale-mode cannot conjure its
missing stress days. The wall Round 13 named now has a mechanism; two of the three candidates
behind it are cleared of the scoring blocker, and the third is down to a data-coverage problem.

**Still gated.** Scale-mode makes these lines SCORE honestly; it does not promote them. `MATERIALITY`
is a declared judgment and must be replay-validated to the R11 bar per line, and the episode /
serial-dependence overlay is the second gate before any of the three becomes a counted tier-1
instrument. None is promoted this round; `stablecoin_peg` stays TIER=2, now honestly scored.

### Round 16 — 2026-08-16 (the registry corrects its own arithmetic, and the counts get a source)

A holistic audit replayed the whole record and found this log had drifted from its own data in
three places — so this round is bookkeeping, no tier moves, no scoring change: the registry stops
lying about numbers it hand-copied, and the numbers most prone to it are given a computed source.

**Three corrections, all replay-measured.** (1) The round-10 retraction says "≥2 tier-1 lines were
simultaneously scoring on only 33 of 800 replayed days" — **both figures are wrong** and the causal
claim built on them is too. Re-measured: ≥2 lines co-score on **~778 of 796 days (97.7%)**; the "33"
was the ≥3-scoring count (~32), mislabelled and paired with the full-replay denominator. The record's
lack of a "2" is therefore NOT a co-scoring failure — the lines co-score almost always — but the
compound of near-independent rare alarms (credit 8.3%, net 3.5%, flights 2.2%, **cnh_cny 0.0%** of
scoring days → an intrinsic ~1 double/year) and a 56-day-young 4-line record. The correction is
inline at the round-10 claim. (2) The round-10 "1.9 days a year" is the iid MODEL (1.94/yr); the
REALIZED rate is 3 doubles over 3.04y ≈ 0.99/yr — the model runs ~2×. Labelled as such. (3) The
tier-1 table read `credit_spread 65 alarm days` while the body two paragraphs up and `episodes.py`
both say **66**; fixed to 66. README's "Fifteen more lines ride the watchlist" was stale at Round 9;
tier-2 is now 17, corrected.

**The counts now have a computed source (止漂).** `tools/episodes.py` — which the same audit flagged
as orphaned: named in the scorer's own docstring as THE remedy for serial-dependence over-counting,
yet not in the pipeline and producing no artifact — is now run in the daily derived step and writes
`data/episodes.json` (alarm days, episode count, longest run, lag-1 per line), regenerated from the
committed record every run. The alarm/episode numbers this log quotes (credit's 66=8 episodes,
net's 57=37, and the rest) are hand-transcribed from exactly this tool; giving it a committed,
CI-refreshed output means the next drift is a diff, not a discovery. What SURVIVED the audit
unblemished is worth recording too: the `_C_N` calibrated-threshold table and every completed-year
yearly-median reproduce from the data to <1e-6 — the discipline holds wherever a number was treated
as load-bearing rather than prose.

**Why this mattered enough to spend a round on.** The audit's larger finding — that the counted
change-resonance is near-mute by construction (0 on 92.8% of 1664 replayed days, never above 2)
while the uncounted layers held ~273 state-days of real broken/drifted conditions the headline read
0 on — is the subject of the next round's structural work (a second, level-based headline). This
round only clears the ground: an instrument whose whole thesis is honesty cannot carry three wrong
numbers in its own ledger while arguing about what to build next.

### Round 17 — 2026-08-16 (the second headline: the level layer becomes a counted probe)

The deep dive that drove round 16 also settled a structural question: the counted change-resonance
is near-mute by construction (0 on 92.8% of 1,664 replayed days, never above 2, ~1 double/year by
its lines' own independent alarm rates), and it is mute not from a broken pipeline but because a
count of sudden, near-independent alarms across four lines simply IS rare — while the diagnostic
layers held **~273 state-days** of real broken/drifted conditions the headline read 0 on (Hormuz
121 days at ~6% of pinned, Kerch twice, a 134-day GNSS drift, four multi-year median regimes).
The signal had migrated to the uncounted layers; the headline had not followed. This round it does.

**A second headline, a second probe.** The dashboard now shows two simple numbers side by side.
The founding one — "N / 4 lines trembling" — is the CHANGE probe: what suddenly moved today, which
by design falls quiet once a disruption has been running a while (Known limit 1). Beside it now sits
the LEVEL probe — "**N guarded states broken now**" — the count of chokepoint states currently OPEN
in the level layer (today: 2, Hormuz + Kerch), each a strait held at or below half a PINNED
pre-event normal for 14+ days so a closure cannot quiet itself by becoming its own baseline. Two
questions the founding thesis always asked and only one of which was ever counted: the sudden onset,
and the stuck state.

**Firewall-clean by construction.** The level headline is fed by `docs/data/stuck.csv` — the file
`tools/stuck_panel.py` already serves from the derived level record, OUTSIDE the scoring path (the
round-12 finding: a level count must never enter `summary.csv`, or the side-channel firewall, the
replay re-derivation, and the tier-1-only summary contract all break). So this is a presentation
elevation of an organ that already existed, not a new scored line: it emits no z, feeds no
trembling_count, and the dashboard reads it with the same `getCSV` the stuck panel uses. It carries
its own as-of date and names the ~10-day PortWatch lag, because a level read is only as fresh as the
panel it derives from. What it does NOT yet count is deliberate and recorded: drift states
(`drift_layer`) and anchored materiality breaches (stablecoin/SRF/CP, once the episode overlay
lands) are the natural next members of a "broken now" count — this round seats the chokepoint
straits, the one level detector with a live consumer and a proven event, and leaves the rest to
earn their place the way every probe here does.

**Why this is the right shape for the instrument.** Tremor is a set of simple numbers, each a probe
of the world, re-chosen over time so that accumulation becomes insight. For fifteen rounds the only
counted probe was "what changed," and the record shows that probe is honest but narrow. Adding "what
is stuck broken" does not complicate the headline — it keeps it a simple integer — but it lets the
front page finally say what the instrument has known for months: the world can be calm in the change
probe and have two straits shut at once. Neither number is a doom score; together they are a
truer reading than either alone.

### Round 18 — 2026-08-16 (a status the dark column always owed: market closure, split from failure)

One scoring-core change the record has owed since the status column was invented, plus two
dashboard changes that follow from round 17.

**`dark` splits, and `closed` is the first piece.** The status column's own comment has said for
months that "no reading at all" hides two different facts — the source FAILED, or the source
answered and the fetcher DECLINED what came back — and that separating them "changes a verdict
field and so bumps STABLE_SINCE." This round takes the cleanest piece: a MARKET CLOSURE.
`cnh_cny` measures offshore−onshore yuan, and the onshore leg does not trade on weekends, so a
Saturday/Sunday has no simultaneous quote to difference — an empty by the calendar, not by
failure. A line that declares `WEEKEND_MARKET` now scores such a day **`closed`**, decided
deterministically from the date (so replay reproduces it with no signal from the long-gone
fetch), and it counts toward NEITHER the dark nor the blind tally. Weekday holidays — this repo
has no keyless holiday calendar — stay `dark`, honestly. The change bumps **STABLE_SINCE to
2026-08-17**, grandfathering the two existing weekend dark rows (08-09, 08-16); every non-opting
line scores byte-identical, and it rides the same `scoring_attrs` seam as WEEKLY_CYCLE / QUANTUM /
MATERIALITY (116 tests green, `replay.py --check` clean).

Why it is more than tidiness: R9 already ruled that "a Sunday dark_count=1 is a market fact, not a
reliability failure," but the dashboard still rendered it as an outage — "0/3 · 1 line dark" every
weekend, an alarm shape for a calendar fact. The front page now reads "0/4 · yuan spread closed
(weekend market)," neutral, and a real `dark` again means what it says: the source is down.

**The level layer is a headline now, so its panel is redundant.** Round 17 promoted the
stuck-strait count to a second headline number; the standalone stuck PANEL below it (a chart plus
a strait list) said the same thing twice, so it is removed — the headline number plus its
click-through modal carry it, and `stuck_panel.py` / `stuck.csv` stay as that number's source.
The two headlines are now framed as an explicit PAIR: a kicker over each names the probe and its
question — "① the change probe · what suddenly moved today" and "② the level probe · what is stuck
broken now" — and the tag says the instrument reads with two probes. Simple numbers, two of them,
each a probe of the world; the accumulation the level probe needs (a pinned pre-event normal over
a year) is exactly why it could only be built now. No tier moves.
