// Execute the dashboard's real render path against the real CSVs, in both
// languages, plus every modal builder — then again against a synthetic
// fixture DATA that exercises every status core/normalize.py can write to a
// row, plus the tier-2 gap-chip run (T21).
//
// The dashboard is a single 40k-character inline script with no build step, so a
// syntax check is all it used to get — and a syntax check cannot see a
// temporal-dead-zone read, a missing i18n key, or a modal that throws on one
// line out of fifteen. Exactly that shipped once: a `const` read four lines
// before its declaration, which threw on every render. The real CSVs are
// whatever the record happens to hold today, so they cannot be relied on to
// cover every status on every run (`stale`, say, is rare) — the fixture pass
// is what guarantees every status is actually exercised, every run.
//
// Usage:  node tests/render_smoke.js
const fs = require("fs"), path = require("path");
const REPO = path.dirname(__dirname);

const html = fs.readFileSync(path.join(REPO, "docs/index.html"), "utf8");
const js = [...html.matchAll(/<script(?![^>]*\bsrc=)[^>]*>([\s\S]*?)<\/script>/g)]
  .map(m => m[1]).join("\n");

const made = {};
// createElement()'d nodes that got appendChild()'d in during the render just
// finished; reset per language below so a language's sweep only sees its own
// appended content, not the previous language's leftovers.
let appendedNodes = [];
function el(id) {
  if (made[id]) return made[id];
  const node = {
    id, _html: "", _text: "", hidden: false, className: "", dataset: {},
    style: { setProperty() {}, removeProperty() {}, getPropertyValue: () => "" }, classList: { add() {}, remove() {}, toggle() {} },
    appendChild(child) { appendedNodes.push(child); return child; },
    setAttribute(k, v) { this["attr:" + k] = String(v); },
    getAttribute(k) { return this["attr:" + k]; }, removeAttribute() {}, scrollIntoView() {},
    addEventListener() {}, getContext: () => ({}),
    set innerHTML(v) { this._html = String(v); }, get innerHTML() { return this._html; },
    set textContent(v) { this._text = String(v); }, get textContent() { return this._text; },
    set onclick(f) { this._onclick = f; }, get onclick() { return this._onclick; },
  };
  return (made[id] = node);
}
// A real cookie jar: `document.cookie = "k=v[;attrs]"` sets ONE cookie (browser
// semantics -- trailing attributes like path=/max-age are parsed off and
// ignored, other cookies are untouched), and the getter returns the
// accumulated "k1=v1; k2=v2" string. The old stub always returned "", so
// getLang()/getRange() (docs/index.html) always fell back to their defaults
// and the zh render path never actually executed.
let cookieJar = {};
global.document = {
  documentElement: {}, body: el("body"),
  getElementById: el, createElement: () => el("tmp-" + Math.random()),
  querySelectorAll: () => [], querySelector: () => null, addEventListener() {},
  get cookie() { return Object.entries(cookieJar).map(([k, v]) => `${k}=${v}`).join("; "); },
  set cookie(v) {
    const kv = String(v).split(";")[0];
    const eq = kv.indexOf("=");
    if (eq > -1) cookieJar[kv.slice(0, eq).trim()] = kv.slice(eq + 1).trim();
  },
};
global.window = { addEventListener() {}, matchMedia: () => ({ matches: false }) };
global.Chart = class { constructor() {} destroy() {} update() {} };
global.Chart.defaults = { font: {}, color: "", plugins: { legend: {} } };
global.fetch = async (url) => {
  const p = path.join(REPO, "docs", url);
  if (!fs.existsSync(p)) return { ok: false, status: 404, text: async () => "" };
  return { ok: true, status: 200, text: async () => fs.readFileSync(p, "utf8") };
};

const errors = [];
process.on("unhandledRejection", e => errors.push("unhandledRejection: " + (e && e.stack || e)));

// docs/index.html has no `setDATA` function -- DATA is a top-level `let`,
// reassigned by load(). Synthesize a setter in this same eval scope (it closes
// over the real `DATA` binding) and export it on globalThis.__P so T21's
// fixtures below can inject DATA directly, bypassing fetch/load().
(0, eval)(js + "\n;globalThis.__P={LINES,T,countModal,lineModal,levelModal,openTier2Modal,render,load,setDATA:function(v){DATA=v;}};");
const {LINES,T,countModal,lineModal,levelModal,openTier2Modal,render,load,setDATA}=globalThis.__P;

// Rendered text lives in two places: nodes looked up by id (`made`, mutated in
// place on every render -- so at sweep time, right after render(), they hold
// only this language's content) and nodes appendChild()'d in during render
// (`appendedNodes`, reset per language above each render() call). Today all
// three appendChild sites in docs/index.html happen to pass createElement()'d
// nodes, which are already registered in `made` too -- so `appendedNodes` is
// redundant with `made` right now. It's kept as defense-in-depth: it also
// catches a node appendChild()'d WITHOUT going through createElement (e.g. a
// clone or a text node), which `made` alone would miss.
function sweepForBadValues(lang) {
  const bits = [];
  for (const n of Object.values(made)) bits.push(n._text, n._html);
  for (const n of appendedNodes) bits.push(n._text, n._html);
  const all = bits.join("\n");
  if (all.includes("undefined")) errors.push(`rendered output (${lang}) contains the literal substring "undefined"`);
  if (all.includes("NaN")) errors.push(`rendered output (${lang}) contains the literal substring "NaN"`);
}

// T21: a synthetic DATA covering every status core/normalize.py can write to
// a row (scoring, warming-up, stale, dark, closed, no-spread) PLUS the new
// tier-2 gap-chip state docs/index.html:GAP_STATUSES/GAP_RUN_LOUD introduces
// -- a tier-2 line dark for >= GAP_RUN_LOUD consecutive collections must
// render the statusLabel.dark gap chip ("No reading received" / "尚未收到读数"
// since the public-surface migration), and (the boundary case) a tier-2 line
// dark for only ONE collection must NOT. Exercised via setDATA(), bypassing
// fetch/load() entirely, so this needs no network and no real CSVs.
//
// Every field a real parseCSV() row would carry is filled in explicitly
// (raw_value, z_score, trembling, direction, source_note, obs_date, status)
// -- a field silently left `undefined` would string-concatenate into the
// rendered HTML as the literal substring "undefined", which is exactly what
// sweepForBadValues() below is built to catch, so leaving one out would be
// invisible right up until it wasn't.
function fixtureRow(overrides) {
  return Object.assign({
    date: "", raw_value: "", z_score: "", trembling: "0", direction: "",
    source_note: "fixture row", obs_date: "", status: "scoring",
  }, overrides);
}
const FIXTURE_DATE = "2026-09-03";
// T25: a payload shaped like what a hostile or merely broken upstream can put in
// a source_note (the record already holds a gateway's HTML error page verbatim).
// Every sink that renders record text must show it as TEXT, never as markup.
const XSS_NOTE = 'gw said <img src=x onerror="alert(1)"> & <script>alert(2)</script> done';
// Markup that must never appear in rendered output: a tag that could execute, or
// any raw angle bracket that survived interpolation.
const XSS_MARKERS = ["<img", "<script", "onerror=\"alert", "& <script"];
function xssScan(label, text) {
  const out = [];
  for (const marker of XSS_MARKERS) {
    if (text.includes(marker)) {
      out.push(`xss(${label}): output contains raw markup ${JSON.stringify(marker)} `
        + `-- a record string reached innerHTML unescaped`);
    }
  }
  return out;
}
function xssErrors(label) {
  const bits = [];
  for (const n of Object.values(made)) bits.push(n._text, n._html);
  for (const n of appendedNodes) bits.push(n._text, n._html);
  return xssScan(label, bits.join("\n"));
}
function buildFixtureData() {
  const lines = {};
  // --- tier-1 (all three since R28 demoted net_outages): scoring+trembling,
  // scoring+calm, closed -- the tier-1 strip only branches on hasToday/isClosed,
  // so this is what exercises that branch, not the full statusLabel map (that
  // map is read only by the tier-2 watchlist below).
  lines.flights = [fixtureRow({ date: FIXTURE_DATE, raw_value: "1000", z_score: "-3.5",
    trembling: "1", direction: "down", status: "scoring" })];               // alarm=down: fires
  lines.credit_spread = [fixtureRow({ date: FIXTURE_DATE, raw_value: "4.2", z_score: "0.4",
    trembling: "0", direction: "up", status: "scoring" })];                 // calm
  lines.cnh_cny = [fixtureRow({ date: FIXTURE_DATE, status: "closed",
    source_note: XSS_NOTE })];
  // --- tier-2: the remaining statuses, plus the gap-chip run boundary ---
  // net_outages is tier-2 since R28; its single dark day exercises a tier-2
  // dark reading below the gap-chip run boundary (like space_weather below).
  lines.net_outages = [fixtureRow({ date: FIXTURE_DATE, status: "dark",
    source_note: "IODA request failed: timeout" })];
  lines.capital_premium = [fixtureRow({ date: FIXTURE_DATE, raw_value: "2.1", status: "warming-up" })];
  lines.grid_frequency = [fixtureRow({ date: FIXTURE_DATE, raw_value: "12", status: "no-spread" })];
  lines.gdelt = [fixtureRow({ date: FIXTURE_DATE, raw_value: "0.18", status: "stale",
    source_note: "[stale: observation already recorded]" })];
  lines.vix = [fixtureRow({ date: FIXTURE_DATE, status: "closed" })];
  lines.em_corp_oas = [fixtureRow({ date: FIXTURE_DATE, raw_value: "1.4", z_score: "0.2", status: "scoring" })];
  // ONE dark day: below GAP_RUN_LOUD (2) -- must render plain, not a gap chip.
  lines.space_weather = [
    fixtureRow({ date: "2026-09-02", raw_value: "3", z_score: "0.1", status: "scoring" }),
    fixtureRow({ date: FIXTURE_DATE, status: "dark", source_note: "NOAA SWPC request failed" }),
  ];
  // A dark run AT GAP_RUN_LOUD -- the hkma_aggr_balance scenario this task is
  // named for (dark 7 of its last 8 real collections as of this writing) --
  // must render the gap chip.
  lines.hkma_aggr_balance = [
    fixtureRow({ date: "2026-09-01", status: "dark", source_note: "HKMA HTTP 502" }),
    fixtureRow({ date: "2026-09-02", status: "dark", source_note: "HKMA request failed: ReadTimeout" }),
    fixtureRow({ date: FIXTURE_DATE, status: "dark", source_note: "HKMA HTTP 502" }),
  ];
  const summary = [{ date: FIXTURE_DATE, trembling_count: "1", dark_count: "1", blind_count: "0" }];
  return { summary, dates: [FIXTURE_DATE], lines, annotations: [], annoMap: new Map(), stuck: [] };
}

// T22 (Task 2): headline discloses adjudication + machine leans + episode-age.
// Three firing tier-1 lines, each exercising one new state, PLUS the
// precedence rule (a human annotation wins over a same-day machine lean) --
// flights carries BOTH an `artifact` annotation and a common-mode lean on the
// same day, and only the annotation's qualifier may surface. (net_outages was
// the common-mode-lean line here until R28 demoted it to tier-2; the lean
// disclosure is generic over any firing tier-1 line, so cnh_cny now stands in
// as the synthetic lean-carrier -- the render path under test is unchanged.)
const ADJ_DATE = "2026-09-10";
const ADJ_PREV_DATE = "2026-09-09";
function buildAdjFixtureData() {
  const lines = {
    // (a) adjudicated artifact -- AND a same-day common-mode lean that must
    // be suppressed by precedence (the lean's own evidence string is the
    // canary: it must never appear in the rendered output).
    flights: [fixtureRow({ date: ADJ_DATE, raw_value: "500", z_score: "-4.1",
      trembling: "1", direction: "down", status: "scoring" })],
    // (c) a 2-day trembling run, no annotation, and an "ok" lean (must render
    // nothing -- only common-mode does).
    credit_spread: [
      fixtureRow({ date: ADJ_PREV_DATE, raw_value: "4.0", z_score: "3.2",
        trembling: "1", direction: "up", status: "scoring" }),
      fixtureRow({ date: ADJ_DATE, raw_value: "4.1", z_score: "3.4",
        trembling: "1", direction: "up", status: "scoring" }),
    ],
    // (b) common-mode lean, no annotation at all -- the lean qualifier fires.
    cnh_cny: [fixtureRow({ date: ADJ_DATE, raw_value: "10", z_score: "5.0",
      trembling: "1", direction: "up", status: "scoring" })],
  };
  const annotations = [
    { date: ADJ_DATE, line: "flights", verdict: "artifact", note: "fixture: instrument artifact" },
    // verdict must not be "method": annosFor() filters those out of the modal
    { date: ADJ_PREV_DATE, line: "flights", verdict: "correction", note: XSS_NOTE },
  ];
  const leans = [
    { date: ADJ_DATE, line: "flights", lean: "common-mode", evidence: "MUST NOT RENDER: annotation wins" },
    { date: ADJ_DATE, line: "cnh_cny", lean: "common-mode", evidence: "7/7 synchronized" },
    { date: ADJ_DATE, line: "credit_spread", lean: "ok", evidence: "0/4 corroborated" },
  ];
  const summary = [{ date: ADJ_DATE, trembling_count: "3", dark_count: "0", blind_count: "0" }];
  return {
    summary, dates: [ADJ_PREV_DATE, ADJ_DATE], lines,
    annotations, annoMap: new Map(annotations.map(a => [a.line + "|" + a.date, a])),
    leans, leanMap: new Map(leans.map(r => [r.line + "|" + r.date, r])),
    stuck: [],
  };
}

// T23 (review fix): data/annotations.csv keys plenty of method/correction/
// retraction rows to the SAME (line,date) as a genuine verdict -- none of
// those three actually adjudicates a tremble, and 2026-09-04 net_outages
// carries both a retraction AND an artifact row for the same day. Two cases
// the T22 fixture above did not cover:
//   (d) a firing line with ONLY a same-day `method` annotation must still
//       disclose its common-mode lean and hatch its pill -- method is not an
//       adjudication, so this must read exactly like "no annotation at all".
//   (e) a (line,date) carrying BOTH a non-adjudicating row and an `artifact`
//       row, with the artifact row written FIRST and a later, non-adjudicating
//       `correction` row LAST -- a last-row-wins lookup (over ALL rows,
//       adjudicating or not) would wrongly return the correction and silently
//       drop the artifact qualifier; the fix must return the artifact row
//       regardless of position.
const ADJ2_DATE = "2026-09-11";
function buildAdjPrecedenceFixtureData() {
  const lines = {
    // (e): the artifact row is written BEFORE the correction row below.
    flights: [fixtureRow({ date: ADJ2_DATE, raw_value: "480", z_score: "-4.3",
      trembling: "1", direction: "down", status: "scoring" })],
    // (d): method only -- no adjudication. (cnh_cny stands in for net_outages,
    // demoted to tier-2 R28; the disclosure path is line-agnostic.)
    cnh_cny: [fixtureRow({ date: ADJ2_DATE, raw_value: "12", z_score: "5.5",
      trembling: "1", direction: "up", status: "scoring" })],
    // bystander: calm, present so all three tier-1 lines have a today row.
    credit_spread: [fixtureRow({ date: ADJ2_DATE, raw_value: "3.0", z_score: "0.2",
      trembling: "0", direction: "up", status: "scoring" })],
  };
  const annotations = [
    { date: ADJ2_DATE, line: "flights", verdict: "artifact", note: "fixture: artifact, written FIRST" },
    { date: ADJ2_DATE, line: "cnh_cny", verdict: "method", note: "fixture: methodology note -- not a verdict on today's tremble" },
    { date: ADJ2_DATE, line: "flights", verdict: "correction", note: "fixture: a later, non-adjudicating row -- must NOT shadow the artifact row above" },
  ];
  const leans = [
    { date: ADJ2_DATE, line: "cnh_cny", lean: "common-mode", evidence: "12/12 synchronized" },
    { date: ADJ2_DATE, line: "flights", lean: "common-mode",
      evidence: "MUST NOT RENDER: later correction must not un-adjudicate" },
  ];
  const summary = [{ date: ADJ2_DATE, trembling_count: "2", dark_count: "0", blind_count: "0" }];
  return {
    summary, dates: [ADJ2_DATE], lines,
    annotations, annoMap: new Map(annotations.map(a => [a.line + "|" + a.date, a])),
    leans, leanMap: new Map(leans.map(r => [r.line + "|" + r.date, r])),
    stuck: [],
  };
}

// T24 (R29 C1): the sysstatus banner's alarm branch (docs/index.html:903) is a
// TIER1.length-derived MAJORITY rule (`darkCount*2 > TIER1.length`), not the
// old hard-coded `darkCount>=3` -- at today's TIER1.length=4 (R30 promoted
// fed_srf_takeup) that is 3-of-4, not 4-of-4. The date must be RUNTIME
// China-today (not a fixed fixture date) -- gapDays is computed from
// `nowChinaMidnight()`, which reads the real clock, so a stale date would make
// gapDays>=2 true and the EARLIER disrupt branch (:902) fire first, and the
// assertion below would then check disruptH/disruptB and never actually reach
// :903 at all. darkNames is built from each TIER1 line's own today-row
// (hasToday/isClosed), not from the summary row, so making darkCount*summary
// agree with reality means marking 3 of the 4 tier-1 lines actually dark
// (raw_value:"", status:"dark"), not just setting a summary count.
const RUNTIME_TODAY = new Date(Date.now() + 8 * 3600 * 1000).toISOString().slice(0, 10);
function buildDarkAlarmFixtureData() {
  const lines = {
    // 3 of 4 tier-1 lines dark today (same shape as the net_outages dark
    // fixture row above: raw_value:"" via the fixtureRow default, status:"dark").
    flights: [fixtureRow({ date: RUNTIME_TODAY, status: "dark",
      source_note: "fixture: dark (ADS-B feed down)" })],
    credit_spread: [fixtureRow({ date: RUNTIME_TODAY, status: "dark",
      source_note: "fixture: dark (FRED feed down)" })],
    fed_srf_takeup: [fixtureRow({ date: RUNTIME_TODAY, status: "dark",
      source_note: "fixture: dark (NY Fed markets API down)" })],
    // the fourth tier-1 line has a real reading today -- NOT dark -- so this
    // is genuinely 3-of-4, not 4-of-4.
    cnh_cny: [fixtureRow({ date: RUNTIME_TODAY, raw_value: "10", z_score: "0.3",
      trembling: "0", direction: "up", status: "scoring" })],
  };
  const summary = [{ date: RUNTIME_TODAY, trembling_count: "0", dark_count: "3", blind_count: "0" }];
  return { summary, dates: [RUNTIME_TODAY], lines, annotations: [], annoMap: new Map(), stuck: [] };
}

// R1.2 fixtures: every sysstatus branch. `GAP_DATE` is China-today minus 3
// days, so gapDays>=2 fires the collection-gap branch before any dark branch.
const GAP_DATE = new Date(Date.parse(RUNTIME_TODAY) - 3 * 86400000).toISOString().slice(0, 10);
function buildOneDarkFixtureData() {
  const lines = {
    flights: [fixtureRow({ date: RUNTIME_TODAY, status: "dark" })],
    credit_spread: [fixtureRow({ date: RUNTIME_TODAY, raw_value: "3.0", z_score: "0.2", direction: "up" })],
    cnh_cny: [fixtureRow({ date: RUNTIME_TODAY, raw_value: "10", z_score: "0.1", direction: "up" })],
    fed_srf_takeup: [fixtureRow({ date: RUNTIME_TODAY, raw_value: "0", z_score: "0.1", direction: "up" })],
  };
  const summary = [{ date: RUNTIME_TODAY, trembling_count: "0", dark_count: "1", blind_count: "0" }];
  return { summary, dates: [RUNTIME_TODAY], lines, annotations: [], annoMap: new Map(), stuck: [] };
}
function buildGapFixtureData() {
  const lines = {};
  for (const id of ["flights", "credit_spread", "cnh_cny", "fed_srf_takeup"]) {
    lines[id] = [fixtureRow({ date: GAP_DATE, raw_value: "1", z_score: "0.5", direction: "up" })];
  }
  const summary = [{ date: GAP_DATE, trembling_count: "0", dark_count: "0", blind_count: "0" }];
  return { summary, dates: [GAP_DATE], lines, annotations: [], annoMap: new Map(), stuck: [] };
}
function buildNoRecordFixtureData() {
  return { summary: [], dates: [], lines: {}, annotations: [], annoMap: new Map(), stuck: [] };
}

// R3 fixtures: two open level states with the reporter's new carried fields.
function buildLevelFixtureData() {
  const data = buildFixtureData();
  data.stuck = [
    { date: RUNTIME_TODAY, component: "Strait of Hormuz", since: "2026-04-06",
      pct: "5", stale: "", trail_median: "3.5", reference: "72", open_days: "207" },
    { date: RUNTIME_TODAY, component: "Kerch Strait", since: "2026-07-26",
      pct: "0", stale: "1", trail_median: "0", reference: "12", open_days: "96" },
  ];
  return data;
}

// R2 fixtures: two tier-1 lines tremble through the same two days. flights
// trembles in its recorded direction; credit_spread trembles AGAINST its own.
// The ledger's trembling_count is therefore 1, while the displayed
// direction-free count is 2.
const PREV_DAY = new Date(Date.parse(RUNTIME_TODAY) - 86400000).toISOString().slice(0, 10);
function buildEitherDirectionFixtureData() {
  const lines = {
    flights: [
      fixtureRow({ date: PREV_DAY, raw_value: "900", z_score: "-3.4", trembling: "1", direction: "down" }),
      fixtureRow({ date: RUNTIME_TODAY, raw_value: "1000", z_score: "-3.5", trembling: "1", direction: "down" }),
    ],
    credit_spread: [
      fixtureRow({ date: PREV_DAY, raw_value: "4.0", z_score: "-3.2", trembling: "1", direction: "down" }),
      fixtureRow({ date: RUNTIME_TODAY, raw_value: "4.2", z_score: "-3.1", trembling: "1", direction: "down" }),
    ],
    cnh_cny: [fixtureRow({ date: RUNTIME_TODAY, raw_value: "10", z_score: "0.2", trembling: "0", direction: "up" })],
    fed_srf_takeup: [fixtureRow({ date: RUNTIME_TODAY, raw_value: "0", z_score: "0.1", trembling: "0", direction: "up" })],
  };
  const summary = [{ date: RUNTIME_TODAY, trembling_count: "1", unusual_count: "2",
    count_method: "either-direction-tier1-v1", dark_count: "0", blind_count: "0" }];
  return { summary, dates: [PREV_DAY, RUNTIME_TODAY], lines,
    annotations: [], annoMap: new Map(), stuck: [] };
}

// T27 (public-surface migration, item 2): the headline states a fraction of
// comparable readings with a denominator, in one canonical template per
// language, and the retired resonance framing is gone from the count block and
// the explanation modal it opens. A headline fixture with a non-zero count and
// one with the zero case: the deck says the zero case uses the SAME label
// template rather than a separate zero phrase, so both must render it.
function buildHeadlineFixtureData() {
  const lines = {};
  for (const id of ["flights", "credit_spread", "cnh_cny", "fed_srf_takeup"]) {
    const L = LINES.find(x => x.id === id);
    lines[id] = [fixtureRow({ date: RUNTIME_TODAY, raw_value: "1", z_score: "0.5",
      trembling: id === "flights" || id === "credit_spread" ? "1" : "0",
      direction: L.declared_dir, status: "scoring" })];
  }
  const summary = [{ date: RUNTIME_TODAY, trembling_count: "2", dark_count: "0", blind_count: "0" }];
  return { summary, dates: [RUNTIME_TODAY], lines, annotations: [], annoMap: new Map(), stuck: [] };
}

(async () => {
  try {
  await load();
  for (const lang of ["en", "zh"]) {
    global.document.cookie = "tremor_lang=" + lang;
    appendedNodes = [];
    try { render(); sweepForBadValues(lang); } catch (e) { errors.push(`render(${lang}): ${e.stack || e}`); }
  }
  // exercise every modal builder, in both languages
  for (const lang of ["en", "zh"]) {
    try { countModal(lang); levelModal(lang); } catch (e) { errors.push(`modal(${lang}): ${e.stack || e}`); }
    for (const L of LINES) {
      try { lineModal(L, lang); } catch (e) { errors.push(`lineModal(${L.id},${lang}): ${e.stack || e}`); }
      // openTier2Modal is only ever invoked (in docs/index.html) for tier-2
      // lines, and it side-effects through openModal() rather than returning
      // html, so it needs DATA (already loaded above) and a real tier-2 row.
      if ((L.tier || 1) === 2) {
        try { openTier2Modal(L, lang); } catch (e) { errors.push(`openTier2Modal(${L.id},${lang}): ${e.stack || e}`); }
      }
    }
  }
  // T21: drive the fixture DATA through the real render path, both languages
  // -- every normalize status plus the tier-2 gap-chip run, and no crash / no
  // undefined / no NaN for any of them.
  const fixture = buildFixtureData();
  const fixtureSummary = fixture.summary[fixture.summary.length - 1];
  for (const lang of ["en", "zh"]) {
    global.document.cookie = "tremor_lang=" + lang;
    setDATA(fixture);
    appendedNodes = [];
    try {
      render();
      sweepForBadValues("fixture-" + lang);
      // summary <-> page firing-count binding: the headline "N" the page
      // shows is read straight off summary.csv's own trembling_count column
      // (count-n's textContent), so a fixture summary row and a fresh count
      // over its own tier-1 rows must imply the SAME N -- this asserts the
      // page actually reads that column rather than silently drifting from it.
      const shownN = el("count-n").textContent;
      if (shownN !== fixtureSummary.trembling_count) {
        errors.push(`fixture(${lang}): headline shows ${shownN}, but the fixture's `
          + `summary row implies trembling_count=${fixtureSummary.trembling_count}`);
      }
      // gap chip: exactly the GAP_RUN_LOUD+ dark line (hkma_aggr_balance)
      // renders one -- the single-dark-day line (space_weather) must not.
      const gapItems = appendedNodes.filter(n => (n.className || "").includes("wl-gap"));
      if (gapItems.length !== 1) {
        errors.push(`fixture(${lang}): expected exactly 1 tier-2 gap chip `
          + `(hkma_aggr_balance's dark run), found ${gapItems.length}`);
      } else if (!/No reading received|尚未收到读数/.test(gapItems[0]._html)) {
        errors.push(`fixture(${lang}): gap chip did not carry the "dark" statusLabel text: ${gapItems[0]._html}`);
      }
      // blind chip: warming-up (capital_premium) and no-spread (grid_frequency).
      // wl-blind is an inline <span> INSIDE the item's innerHTML (unlike
      // wl-gap, which also marks the outer wl-item node's own className), so
      // this greps the rendered markup rather than filtering by className.
      const blindItems = appendedNodes.filter(n => (n._html || "").includes('class="wl-blind"'));
      if (blindItems.length !== 2) {
        errors.push(`fixture(${lang}): expected exactly 2 BLIND watchlist items `
          + `(warming-up + no-spread), found ${blindItems.length}`);
      }
    } catch (e) { errors.push(`fixture render(${lang}): ${e.stack || e}`); }
    errors.push(...xssErrors("fixture-" + lang));
    // exercise the modal builders against the fixture too, tier-1 and tier-2.
    try { countModal(lang); levelModal(lang); } catch (e) { errors.push(`fixture modal(${lang}): ${e.stack || e}`); }
    for (const id of Object.keys(fixture.lines)) {
      const L = LINES.find(x => x.id === id);
      if (!L) continue;
      try { lineModal(L, lang); } catch (e) { errors.push(`fixture lineModal(${id},${lang}): ${e.stack || e}`); }
      if ((L.tier || 1) === 2) {
        try { openTier2Modal(L, lang); } catch (e) { errors.push(`fixture openTier2Modal(${id},${lang}): ${e.stack || e}`); }
      }
    }
  }

  // T22: adjudication/lean/run disclosure (Task 2), both languages -- the
  // headline integer must not move, precedence must hold (flights' lean
  // evidence must never surface once it is annotated), and all three new
  // qualifiers must actually render. The reading cards carry ONE neutral
  // unusual marker either way (T32 binds the both-directions case); no card
  // hatches or discloses an adjudication of its own.
  const adjFixture = buildAdjFixtureData();
  for (const lang of ["en", "zh"]) {
    global.document.cookie = "tremor_lang=" + lang;
    setDATA(adjFixture);
    appendedNodes = [];
    try {
      render();
      sweepForBadValues("adj-" + lang);
      const Tl = T[lang];
      const shownN = el("count-n").textContent;
      if (shownN !== "3") {
        errors.push(`adj(${lang}): headline shows ${shownN}, expected 3 -- `
          + `the integer must never move for a disclosure qualifier`);
      }
      const labelHtml = el("count-label").innerHTML;
      // The deck deletes the adjudication paraphrase from the headline: the
      // dated note stays in the record detail, never as generated headline text.
      if (labelHtml.includes("fixture: instrument artifact")) {
        errors.push(`adj(${lang}): the raw annotation note rendered in the headline; `
          + `dated notes belong to the record detail`);
      }
      if (!lineModal(LINES.find(l => l.id === "flights"), lang)
            .includes("fixture: instrument artifact")) {
        errors.push(`adj(${lang}): the line detail does not carry the dated annotation note`);
      }
      const leanCore = Tl.leanNote("", "7/7 synchronized").replace(" · ", "");
      if (!labelHtml.includes(leanCore)) {
        errors.push(`adj(${lang}): missing the common-mode machine-lean qualifier for cnh_cny`);
      }
      const suppressedLeanCore = Tl.leanNote("", "MUST NOT RENDER: annotation wins").replace(" · ", "");
      if (labelHtml.includes(suppressedLeanCore)) {
        errors.push(`adj(${lang}): precedence violated -- flights' machine lean rendered `
          + `even though it carries a human annotation`);
      }
      const runCore = Tl.runNote("", 2).replace(" · ", "");
      if (!labelHtml.includes(runCore)) {
        errors.push(`adj(${lang}): missing the 2-day trembling-run qualifier for credit_spread`);
      }
      // one neutral marker: every firing card carries the SAME unusual pill --
      // the card never hatches or distinguishes an adjudication, and the
      // headline qualifier above is where a recorded adjudication is disclosed.
      const instNodes = appendedNodes.filter(n => n.className === "inst");
      if (instNodes.length !== 3) {
        errors.push(`adj(${lang}): expected 3 tier-1 strip chips, found ${instNodes.length}`);
      } else {
        for (const [i, id] of [[0, "flights"], [1, "credit_spread"], [2, "cnh_cny"]]) {
          const chipHtml = instNodes[i]._html || "";
          if (!chipHtml.includes(`class="pill trembling">${Tl.unusualPill}</span>`)) {
            errors.push(`adj(${lang}): ${id}'s card does not carry the one neutral `
              + `unusual marker ${JSON.stringify(Tl.unusualPill)}: ${chipHtml}`);
          }
          if (/adjudicated/.test(chipHtml)) {
            errors.push(`adj(${lang}): ${id}'s card still carries an adjudication-specific `
              + `marker class: ${chipHtml}`);
          }
        }
      }
    } catch (e) { errors.push(`adj render(${lang}): ${e.stack || e}`); }
  }

  // T23 (review fix): method-only annotation must not suppress the lean (case
  // d), and an adjudicating row must win regardless of row order among
  // duplicates for the same (line,date) (case e). The cards' one neutral marker
  // is bound here too: a firing card renders it without an adjudication class.
  const adj2Fixture = buildAdjPrecedenceFixtureData();
  for (const lang of ["en", "zh"]) {
    global.document.cookie = "tremor_lang=" + lang;
    setDATA(adj2Fixture);
    appendedNodes = [];
    try {
      render();
      sweepForBadValues("adj2-" + lang);
      const Tl = T[lang];
      const shownN = el("count-n").textContent;
      if (shownN !== "2") {
        errors.push(`adj2(${lang}): headline shows ${shownN}, expected 2 -- `
          + `the integer must never move for a disclosure qualifier`);
      }
      const labelHtml = el("count-label").innerHTML;
      // (d) cnh_cny carries only a `method` annotation -- not an
      // adjudication -- so its common-mode lean must still surface.
      const leanCore = Tl.leanNote("", "12/12 synchronized").replace(" · ", "");
      if (!labelHtml.includes(leanCore)) {
        errors.push(`adj2(${lang}): a same-day METHOD annotation wrongly suppressed `
          + `cnh_cny's common-mode lean qualifier (method must not act as an adjudication)`);
      }
      // (e) flights carries an `artifact` row written FIRST and a `correction`
      // row written LAST for the same (line,date). The correction does not
      // adjudicate, so adjudication() must still return the artifact row --
      // observable through the lean it suppresses: flights' fixture lean
      // evidence is a canary that must never reach the headline.
      if (labelHtml.includes("MUST NOT RENDER: later correction must not un-adjudicate")) {
        errors.push(`adj2(${lang}): flights' machine lean rendered, so a later `
          + `non-adjudicating (correction) row shadowed the adjudicating row`);
      }
      const flightsHtml = lineModal(LINES.find(l => l.id === "flights"), lang);
      if (!flightsHtml.includes("fixture: artifact, written FIRST")) {
        errors.push(`adj2(${lang}): the line detail does not carry the dated artifact note`);
      }
      // one neutral marker: flights (artifact, order-independent) and cnh_cny
      // (method-only + common-mode lean) both render the same unusual pill;
      // the calm bystander renders no pill at all.
      const instNodes = appendedNodes.filter(n => n.className === "inst");
      if (instNodes.length !== 3) {
        errors.push(`adj2(${lang}): expected 3 tier-1 strip chips, found ${instNodes.length}`);
      } else {
        for (const [i, id] of [[0, "flights"], [2, "cnh_cny"]]) {
          const chipHtml = instNodes[i]._html || "";
          if (!chipHtml.includes(`class="pill trembling">${Tl.unusualPill}</span>`)) {
            errors.push(`adj2(${lang}): ${id}'s card does not carry the one neutral `
              + `unusual marker: ${chipHtml}`);
          }
        }
        if (/class="pill trembling|class="pill benign/.test(instNodes[1]._html || "")) {
          errors.push(`adj2(${lang}): the calm credit_spread card carries an unusual marker`);
        }
      }
    } catch (e) { errors.push(`adj2 render(${lang}): ${e.stack || e}`); }
  }

  // T26 (public-surface migration, item 1): the line detail states what a line
  // MEASURES - quantity, population, sampling, unit - and no longer explains
  // why a value moved. These are opening sentences of the retired causal
  // `explain` payloads (two EN, one ZH); none may survive in any line's detail
  // in any language, and every detail must render its own `measures`
  // definition in its place.
  const RETIRED_CAUSAL = [
    "Airlines fight to keep planes on schedule",
    "fear has overpowered greed",
    "说明有更大的力量压垮了这股动机",
  ];
  for (const lang of ["en", "zh"]) {
    for (const L of LINES) {
      const detail = lineModal(L, lang);
      for (const phrase of RETIRED_CAUSAL) {
        if (detail.includes(phrase)) {
          errors.push(`measures(${lang}): lineModal(${L.id}) still renders retired causal `
            + `wording ${JSON.stringify(phrase)} -- the detail must state what the line `
            + `measures, not why its value moved`);
        }
      }
      const measure = L.measures && L.measures[lang];
      if (!measure) {
        errors.push(`measures(${lang}): LINES entry ${L.id} declares no measures.${lang}`);
      } else if (!detail.includes(measure)) {
        errors.push(`measures(${lang}): lineModal(${L.id}) does not render its own `
          + `measures.${lang} definition`);
      }
    }
  }

  // T27 (public-surface migration, item 2): the headline is one canonical
  // fraction - {n} over {m}, where {m} is the day's comparable-line count - in
  // both languages, and the retired resonance framing is gone from the count
  // block and from the explanation modal that block opens. The rendered
  // headline is assembled from the count block's own fragments (prefix,
  // numerator, separator + denominator, label tail), because the numerator
  // keeps its own display element; the ASSEMBLED sentence is what must match
  // the deck's countLabel template.
  const COUNT_LABEL_PATTERN = {
    en: /^(\d+) \/ (\d+) readings unusual today/,
    zh: /^今天有 (\d+)\/(\d+) 条读数偏离各自近期记录/,
  };
  const COUNT_TITLE = { en: "Readings unusual today", zh: "今日偏离近期记录的读数" };
  const COUNT_QUESTION = { en: "How is this count made? ›", zh: "这个计数如何得出？›" };
  const COUNT_MODAL_TITLE = { en: "How the count is made", zh: "这个计数如何得出" };
  const COUNT_MODAL_MARKER = {
    en: "A line contributes when its scored value crosses its own threshold in either direction.",
    zh: "一条线的分数向任一方向越过自身阈值时，便计入其中。",
  };
  const RETIRED_HEADLINE = ["Resonance", "共振", "only number that matters", "唯一重要的数字"];
  const plainText = s => String(s == null ? "" : s).replace(/<[^>]+>/g, "");
  const headlineCases = [
    { name: "nonzero", data: buildHeadlineFixtureData() },
    { name: "zero", data: buildDarkAlarmFixtureData() },
  ];
  for (const { name, data } of headlineCases) {
    for (const lang of ["en", "zh"]) {
      global.document.cookie = "tremor_lang=" + lang;
      setDATA(data);
      appendedNodes = [];
      try {
        render();
        sweepForBadValues("headline-" + name + "-" + lang);
        const headline = plainText(el("count-prefix").textContent)
          + plainText(el("count-n").textContent)
          + plainText(el("count-sep").textContent)
          + plainText(el("count-of").textContent)
          + plainText(el("count-label").innerHTML);
        const match = COUNT_LABEL_PATTERN[lang].exec(headline);
        if (!match) {
          errors.push(`headline(${name}-${lang}): the rendered count block is `
            + `${JSON.stringify(headline)}, which does not match the deck's `
            + `countLabel pattern ${COUNT_LABEL_PATTERN[lang]}`);
        } else {
          if (match[1] !== el("count-n").textContent) {
            errors.push(`headline(${name}-${lang}): the label's numerator is `
              + `${JSON.stringify(match[1])} but the count shows ${JSON.stringify(el("count-n").textContent)}`);
          }
          if (match[2] !== el("count-of").textContent) {
            errors.push(`headline(${name}-${lang}): the label's denominator is `
              + `${JSON.stringify(match[2])} but the count shows ${JSON.stringify(el("count-of").textContent)}`);
          }
        }
        if (el("count-kicker").textContent !== COUNT_TITLE[lang]) {
          errors.push(`headline(${name}-${lang}): count title is `
            + `${JSON.stringify(el("count-kicker").textContent)}, expected ${JSON.stringify(COUNT_TITLE[lang])}`);
        }
        if (el("count-q").textContent !== COUNT_QUESTION[lang]) {
          errors.push(`headline(${name}-${lang}): count question is `
            + `${JSON.stringify(el("count-q").textContent)}, expected ${JSON.stringify(COUNT_QUESTION[lang])}`);
        }
        // The explanation modal is opened by clicking the count block itself,
        // so scan what a reader actually gets rather than a builder called in
        // isolation (the old resonance payload lived in exactly this modal).
        el("count").onclick();
        const modal = plainText(el("modal-body").innerHTML);
        if (!modal.includes(COUNT_MODAL_TITLE[lang])) {
          errors.push(`headline(${name}-${lang}): the count modal does not carry `
            + `the title ${JSON.stringify(COUNT_MODAL_TITLE[lang])}`);
        }
        if (!modal.includes(COUNT_MODAL_MARKER[lang])) {
          errors.push(`headline(${name}-${lang}): the count modal does not carry `
            + `the countModalBody marker ${JSON.stringify(COUNT_MODAL_MARKER[lang])}`);
        }
        const surface = headline + "\n" + modal;
        for (const phrase of RETIRED_HEADLINE) {
          if (surface.includes(phrase)) {
            errors.push(`headline(${name}-${lang}): the count block or its modal `
              + `still renders the retired framing ${JSON.stringify(phrase)}`);
          }
        }
      } catch (e) { errors.push(`headline render(${name}-${lang}): ${e.stack || e}`); }
    }
  }

  // T28 (public-surface migration, item 3): a zero reading and every row
  // status are described without a calm/平静 word, and statusLabel carries the
  // deck's copy for all six statuses core/normalize.py can emit -- including
  // `scoring`, which the page had no label for at all. The count block's new
  // qualifying line states that the count is a statistical comparison, not a
  // judgment of conditions, and the migrated count qualifiers read as the
  // deck's sentences in both languages.
  const DECK_STATUS_LABEL = {
    en: {
      "scoring": "Compared with recent record",
      "warming-up": "Comparison history still forming",
      "no-spread": "Too little variation to compare",
      "stale": "Repeated observation; prior record retained",
      "dark": "No reading received",
      "closed": "Market closed",
    },
    zh: {
      "scoring": "已与近期记录比较",
      "warming-up": "近期参照仍在积累",
      "no-spread": "变化太少，暂无法比较",
      "stale": "重复观测；沿用此前记录",
      "dark": "尚未收到读数",
      "closed": "市场休市",
    },
  };
  const DECK_COUNT_QUALIFYING = {
    en: "A statistical comparison, not a judgment of conditions.",
    zh: "这是统计比较，不替处境下判断。",
  };
  const CALM_WORDS = ["calm", "平静"];
  const DECK_QUALIFIERS = {
    en: [
      ["darkNote(2)", Tl2 => Tl2.darkNote(2), " · 2 lines have no reading"],
      ["darkNote(1)", Tl2 => Tl2.darkNote(1), " · 1 line has no reading"],
      ["closedNote", Tl2 => Tl2.closedNote(["cnh_cny"]), " · market closed: cnh_cny"],
      ["blindNote(2)", Tl2 => Tl2.blindNote(2), " · 2 lines cannot yet be compared"],
      ["blindNote(1)", Tl2 => Tl2.blindNote(1), " · 1 line cannot yet be compared"],
      ["calibNote(1,4)", Tl2 => Tl2.calibNote(1, 4),
        " · comparison history is still forming for 1 of 4 lines"],
      ["runNote(_,2)", Tl2 => Tl2.runNote("", 2),
        " · outside its recent range for 2 consecutive collection days"],
      ["whichLines", Tl2 => (typeof Tl2.whichLines === "function" ? Tl2.whichLines(["a", "b"]) : undefined),
        " · a + b"],
    ],
    zh: [
      ["darkNote(2)", Tl2 => Tl2.darkNote(2), " · 2 条线没有读数"],
      ["darkNote(1)", Tl2 => Tl2.darkNote(1), " · 1 条线没有读数"],
      ["closedNote", Tl2 => Tl2.closedNote(["cnh_cny"]), " · 市场休市：cnh_cny"],
      ["blindNote(2)", Tl2 => Tl2.blindNote(2), " · 2 条线暂不可比较"],
      ["blindNote(1)", Tl2 => Tl2.blindNote(1), " · 1 条线暂不可比较"],
      ["calibNote(1,4)", Tl2 => Tl2.calibNote(1, 4), " · 4 条线中有 1 条的近期参照仍在积累"],
      ["runNote(_,2)", Tl2 => Tl2.runNote("", 2), " · 已连续 2 个采集日偏离近期范围"],
      ["whichLines", Tl2 => (typeof Tl2.whichLines === "function" ? Tl2.whichLines(["a", "b"]) : undefined),
        " · a ＋ b"],
    ],
  };
  for (const lang of ["en", "zh"]) {
    const Tl = T[lang] || {};
    const labels = Tl.statusLabel || {};
    for (const code of Object.keys(DECK_STATUS_LABEL[lang])) {
      const got = labels[code];
      if (got !== DECK_STATUS_LABEL[lang][code]) {
        errors.push(`status(${lang}): statusLabel.${JSON.stringify(code)} is `
          + `${JSON.stringify(got)}, expected the deck copy `
          + `${JSON.stringify(DECK_STATUS_LABEL[lang][code])}`);
      }
    }
    if (typeof Tl.whichNote === "function") {
      errors.push(`status(${lang}): the retired whichNote key is still declared -- `
        + `the deck renames it to whichLines`);
    }
    for (const [name, call, expected] of DECK_QUALIFIERS[lang]) {
      const got = call(Tl);
      if (got !== expected) {
        errors.push(`status(${lang}): ${name} renders ${JSON.stringify(got)}, `
          + `expected the deck's copy ${JSON.stringify(expected)}`);
      }
    }
    // The zero case is described in the count block: a day with no unusual
    // readings (three of four lines dark) must carry no calm word there.
    global.document.cookie = "tremor_lang=" + lang;
    setDATA(buildDarkAlarmFixtureData());
    appendedNodes = [];
    try {
      render();
      sweepForBadValues("zero-" + lang);
      const zeroBlock = plainText(el("count-kicker").textContent)
        + " " + plainText(el("count-prefix").textContent)
        + " " + plainText(el("count-n").textContent)
        + " " + plainText(el("count-sep").textContent)
        + " " + plainText(el("count-of").textContent)
        + " " + plainText(el("count-label").innerHTML)
        + " " + plainText(el("count-qualifying").textContent);
      for (const word of CALM_WORDS) {
        if (zeroBlock.toLowerCase().includes(word.toLowerCase())) {
          errors.push(`zero(${lang}): the zero-reading count block still uses the `
            + `calm word ${JSON.stringify(word)}: ${JSON.stringify(zeroBlock)}`);
        }
      }
      const qualifying = plainText(el("count-qualifying").textContent);
      if (qualifying !== DECK_COUNT_QUALIFYING[lang]) {
        errors.push(`zero(${lang}): the count block's qualifying line is `
          + `${JSON.stringify(qualifying)}, expected the deck's copy `
          + `${JSON.stringify(DECK_COUNT_QUALIFYING[lang])}`);
      }
    } catch (e) { errors.push(`zero render(${lang}): ${e.stack || e}`); }
  }

  // T25: record text is escaped at every sink, including the builders that
  // RETURN markup (lineModal / openTier2Modal reach the DOM only through
  // openModal, so a DOM-only sweep would miss them entirely).
  for (const lang of ["en", "zh"]) {
    global.document.cookie = "tremor_lang=" + lang;
    setDATA(adjFixture);
    const flightsLine = LINES.find(x => x.id === "flights");
    errors.push(...xssScan("lineModal-" + lang, lineModal(flightsLine, lang)));
  }

  // T24 (R29 C1): sysstatus alarm banner fires on a TIER1.length-derived
  // MAJORITY (2-of-3 today), not the old hard-coded 3-of-3. Assert the
  // manyDark-SPECIFIC text in both languages -- a className-only check
  // ("alarm") cannot distinguish this branch from the collection-gap branch
  // just above it (:922), which also sets className "sysstatus alarm".
  const darkAlarmFixture = buildDarkAlarmFixtureData();
  for (const lang of ["en", "zh"]) {
    global.document.cookie = "tremor_lang=" + lang;
    setDATA(darkAlarmFixture);
    appendedNodes = [];
    try {
      render();
      sweepForBadValues("darkalarm-" + lang);
      const Tl = T[lang];
      const st = el("sysstatus");
      const darkDomains = ["flights", "credit_spread", "fed_srf_takeup"]
        .map(id => LINES.find(l => l.id === id).domain[lang]).join(", ");
      const expectH = Tl.manyDark(3, 4, darkDomains);
      if (st.className !== "sysstatus alarm") {
        errors.push(`darkalarm(${lang}): expected className "sysstatus alarm", got "${st.className}"`);
      }
      if (!st.innerHTML.includes(expectH)) {
        errors.push(`darkalarm(${lang}): expected the manyDark(3,4) text "${expectH}" in the `
          + `sysstatus banner, got: ${st.innerHTML}`);
      }
    } catch (e) { errors.push(`darkalarm render(${lang}): ${e.stack || e}`); }
  }

  // T29 (public-surface migration, item 4): the numbered two-probe framing is
  // deleted and the structural copy describes a record. No circled-probe
  // kicker (①/②/③) and no probe wording (probe / 探针) may reach a reader in
  // either language, and the deck's structural strings are what renders:
  // title, promise, as-of line, gap word, detail link, direction words, range
  // labels, the coverage sentence, the limits block, the fixed-reference block
  // and the watchlist's collected-never-counted line.
  const DECK_STRUCT = {
    en: {
      title: "tremor — readings, kept in view",
      promise: "A daily record of what each series measures and how today’s readings differ from their own recent records; the meaning stays open.",
      nodata: "NO READING",
      more: "Open reading details ›",
      dirUp: "rising",
      dirDown: "falling",
      ranges: { "30": "30 days", "90": "90 days", "365": "1 year", "all": "All" },
      coveragePrefix: "In view: ",
      coverageSuffix: ". This is the set of records shown here.",
      covMore: "Scope and limits ↓",
      limitsTitle: "Limits of this record",
      limitsBody: "The rolling comparison looks to recent history; a change that lasts can become part of a series' reference.",
      limitsFlights: "Flights samples four regions at 22:30 UTC, with uneven shares:",
      referenceTitle: "Long-running readings below fixed references",
      referenceBody: "A named strait is listed after its recorded daily traffic stays at or below half of its fixed reference for 14 days.",
      referenceAsOf: /(^| · )Latest source observation: \d{4}-\d{2}-\d{2} \(about 10 days behind publication\)$/,
      notCounted: "Collected daily; never included in this count.",
      watchTitle: "Other daily records",
      watchDays: ["1 recorded day", "2 recorded days"],
      asOf: /^Record through \d{4}-\d{2}-\d{2} \(China time\)$/,
    },
    zh: {
      title: "tremor——把读数留在眼前",
      promise: "每日记录各条序列测量什么，以及今天的读数与各自近期记录相差多远；如何理解，仍由读者决定。",
      nodata: "无读数",
      more: "查看读数详情 ›",
      dirUp: "升高",
      dirDown: "下降",
      ranges: { "30": "30 天", "90": "90 天", "365": "1 年", "all": "全部" },
      coveragePrefix: "当前记录范围：",
      coverageSuffix: "。本页展示的是这些记录。",
      covMore: "范围与限度 ↓",
      limitsTitle: "这份记录的限度",
      limitsBody: "滚动比较照见近期记录；延续很久的变化，可能渐渐进入一条序列的参照。",
      limitsFlights: "Flights 每日 22:30 UTC 采样四个区域，各自占比并不相同：",
      referenceTitle: "长期低于既定参照的条目",
      referenceBody: "具名海峡的每日记录流量连续 14 天处于固定参照值的一半或以下时，页面列出该项。",
      referenceAsOf: /(^| · )来源最新观测：\d{4}-\d{2}-\d{2}（发布约滞后 10 天）$/,
      notCounted: "每日采集，但从不进入这个计数。",
      watchTitle: "其他每日记录",
      watchDays: ["已有 1 天记录", "已有 2 天记录"],
      asOf: /^记录截至 \d{4}-\d{2}-\d{2}（北京时间）$/,
    },
  };
  const PROBE_WORDS = ["①", "②", "③", "probe", "探针"];
  const structFixture = buildFixtureData();
  structFixture.stuck = [{ date: FIXTURE_DATE, component: "Strait of Hormuz",
    since: "2026-04-06", pct: "4", stale: "",
    trail_median: "3", reference: "72", open_days: "151" }];
  for (const lang of ["en", "zh"]) {
    const d = DECK_STRUCT[lang];
    const Tl = T[lang] || {};
    global.document.cookie = "tremor_lang=" + lang;
    // Retired keys: the deck deletes changeKicker and levelKicker outright,
    // renames asof to asOf, and replaces the two-probe `tag` with `promise`.
    for (const retired of ["tag", "changeKicker", "levelKicker", "asof"]) {
      if (typeof Tl[retired] !== "undefined") {
        errors.push(`structure(${lang}): the retired key ${JSON.stringify(retired)} is still declared`);
      }
    }
    if (Tl.dirUp !== d.dirUp || Tl.dirDown !== d.dirDown) {
      errors.push(`structure(${lang}): direction words are ${JSON.stringify([Tl.dirUp, Tl.dirDown])}, `
        + `expected the deck's ${JSON.stringify([d.dirUp, d.dirDown])}`);
    }
    for (const r of ["30", "90", "365", "all"]) {
      if (Tl["range_" + r] !== d.ranges[r]) {
        errors.push(`structure(${lang}): range_${r} is ${JSON.stringify(Tl["range_" + r])}, `
          + `expected the deck's ${JSON.stringify(d.ranges[r])}`);
      }
    }
    for (const [name, got, want] of [
      ["nodata", Tl.nodata, d.nodata],
      ["more", Tl.more, d.more],
      ["notCounted", Tl.notCounted, d.notCounted],
      ["watchTitle", Tl.watchTitle, d.watchTitle],
      ["watchDays(1)", Tl.watchDays(1), d.watchDays[0]],
      ["watchDays(2)", Tl.watchDays(2), d.watchDays[1]],
    ]) {
      if (got !== want) {
        errors.push(`structure(${lang}): ${name} is ${JSON.stringify(got)}, `
          + `expected the deck's ${JSON.stringify(want)}`);
      }
    }
    setDATA(structFixture);
    appendedNodes = [];
    try {
      render();
      sweepForBadValues("structure-" + lang);
      if (document.title !== d.title) {
        errors.push(`structure(${lang}): document title is ${JSON.stringify(document.title)}, `
          + `expected the deck's ${JSON.stringify(d.title)}`);
      }
      if (el("tag").textContent !== d.promise) {
        errors.push(`structure(${lang}): the promise line is ${JSON.stringify(el("tag").textContent)}, `
          + `expected the deck's ${JSON.stringify(d.promise)}`);
      }
      if (!d.asOf.test(el("asof").textContent)) {
        errors.push(`structure(${lang}): the as-of line is ${JSON.stringify(el("asof").textContent)}, `
          + `which does not match the deck's asOf pattern ${d.asOf}`);
      }
      const cov = plainText(el("coverage").innerHTML);
      if (!cov.startsWith(d.coveragePrefix) || !cov.includes(d.coverageSuffix)
          || !cov.includes(d.covMore)) {
        errors.push(`structure(${lang}): the coverage line is ${JSON.stringify(cov)}, `
          + `expected the deck's coverage sentence plus ${JSON.stringify(d.covMore)}`);
      }
      if (el("level-kicker").textContent !== d.referenceTitle) {
        errors.push(`structure(${lang}): the fixed-reference heading is `
          + `${JSON.stringify(el("level-kicker").textContent)}, expected the deck's `
          + `${JSON.stringify(d.referenceTitle)}`);
      }
      if (!d.referenceAsOf.test(plainText(el("level-label").innerHTML))) {
        errors.push(`structure(${lang}): the fixed-reference label is `
          + `${JSON.stringify(plainText(el("level-label").innerHTML))}, which does not carry the `
          + `deck's referenceAsOf pattern ${d.referenceAsOf}`);
      }
      const chips = appendedNodes.filter(n => (n.className || "").startsWith("inst"));
      const tier1Count = LINES.filter(L => (L.tier || 1) === 1).length;
      if (chips.length !== tier1Count) {
        errors.push(`structure(${lang}): expected ${tier1Count} tier-1 chips, found ${chips.length}`);
      }
      for (const n of chips) {
        if (!(n._html || "").includes(`<div class="more">${d.more}</div>`)) {
          errors.push(`structure(${lang}): a reading chip does not carry the deck's detail link `
            + `${JSON.stringify(d.more)}`);
        }
      }
      // The scope link scrolls to the always-visible limits section and opens no
      // panel; T30 binds the four limitations and the measured flights fact.
      el("modal").hidden = true;
      el("covmore").onclick();
      if (el("modal").hidden !== true) {
        errors.push(`structure(${lang}): the scope link opened a panel instead of scrolling `
          + `to the inline limits section`);
      }
      const limits = plainText(el("limits").innerHTML);
      for (const [name, want] of [["limitsTitle", d.limitsTitle],
                                  ["limitsBody", d.limitsBody],
                                  ["limitsFlights", d.limitsFlights]]) {
        if (!limits.includes(want)) {
          errors.push(`structure(${lang}): the inline limits section does not carry the deck's `
            + `${name} ${JSON.stringify(want)}`);
        }
      }
      // The fixed-reference number opens its own rule, not a probe explanation.
      el("level-count").onclick();
      const refModal = plainText(el("modal-body").innerHTML);
      for (const [name, want] of [["referenceTitle", d.referenceTitle],
                                  ["referenceBody", d.referenceBody]]) {
        if (!refModal.includes(want)) {
          errors.push(`structure(${lang}): the fixed-reference panel does not carry the deck's `
            + `${name} ${JSON.stringify(want)}`);
        }
      }
      // A collected-but-never-counted line says so in its own detail.
      const tier2 = LINES.find(L => (L.tier || 1) === 2);
      openTier2Modal(tier2, lang);
      if (!plainText(el("modal-body").innerHTML).includes(d.notCounted)) {
        errors.push(`structure(${lang}): a watchlist detail does not carry the deck's `
          + `not-counted line ${JSON.stringify(d.notCounted)}`);
      }
      const watchHeading = appendedNodes.find(n => n._text === d.watchTitle);
      if (!watchHeading) {
        errors.push(`structure(${lang}): the watchlist heading is not the deck's `
          + `${JSON.stringify(d.watchTitle)}`);
      }
      // The reader surface -- rendered page plus every detail panel -- must not
      // carry a numbered kicker or any probe wording.
      const surface = [
        document.title, el("tag").textContent, el("asof").textContent, el("coverage").innerHTML,
        el("count-kicker").textContent, el("count-label").innerHTML,
        el("level-kicker").textContent, el("level-label").innerHTML,
        el("panel-title").textContent, el("panel-hint").textContent, el("footer").innerHTML,
        ...Object.values(made).flatMap(n => [n._text, n._html]),
        ...appendedNodes.flatMap(n => [n._text, n._html]),
        countModal(lang), levelModal(lang),
        ...LINES.map(L => lineModal(L, lang)),
      ].join("\n");
      for (const word of PROBE_WORDS) {
        if (surface.includes(word)) {
          errors.push(`structure(${lang}): the reader surface still carries probe wording `
            + `${JSON.stringify(word)}`);
        }
      }
    } catch (e) { errors.push(`structure render(${lang}): ${e.stack || e}`); }
    // A line with no reading shows the deck's gap word, not a bare "no data".
    setDATA(buildDarkAlarmFixtureData());
    appendedNodes = [];
    try {
      render();
      const darkChips = appendedNodes.filter(n => (n.className || "").includes("inst dark"));
      if (darkChips.length !== 3) {
        errors.push(`structure(${lang}): expected 3 dark reading chips, found ${darkChips.length}`);
      }
      for (const n of darkChips) {
        if (!(n._html || "").includes(`<span class="nodata">${d.nodata}</span>`)) {
          errors.push(`structure(${lang}): a dark reading chip does not carry the deck's gap word `
            + `${JSON.stringify(d.nodata)}: ${n._html}`);
        }
      }
    } catch (e) { errors.push(`structure dark render(${lang}): ${e.stack || e}`); }
  }

  // T30 (public-surface migration, item 5): the page states its four
  // limitations as visible body text, plus the measured flights sampling
  // weight, in an inline section below the collected records. Each marker is
  // one deck sentence; all four must be readable on the rendered page in both
  // languages, with no panel opened.
  const DECK_LIMITS = {
    en: {
      title: "Limits of this record",
      points: [
        "The rolling comparison looks to recent history; a change that lasts can become part of a series' reference.",
        "The displayed roster is selected under written measurement assumptions",
        "Other daily records are collected but never enter this count.",
        "No communications-domain reading is included, so a worldwide connectivity event reads zero in this count.",
      ],
      flights: "Flights samples four regions at 22:30 UTC, with uneven shares:",
    },
    zh: {
      title: "这份记录的限度",
      points: [
        "滚动比较照见近期记录；延续很久的变化，可能渐渐进入一条序列的参照。",
        "页面展示哪些线，依据书面观测假设选定",
        "其他每日记录会继续采集，却永不进入这个计数。",
        "这里没有通信域的读数，所以全球性的连通事件在这个计数里读作零。",
      ],
      flights: "Flights 每日 22:30 UTC 采样四个区域",
    },
  };
  // Placement is part of the requirement: the section sits in the page body
  // below the collected records, before the footer, and never inside the modal.
  {
    const wl = html.indexOf('id="watchlist"');
    const lim = html.indexOf('id="limits"');
    const foot = html.indexOf('id="footer"');
    const modal = html.indexOf('<div class="modal"');
    if (!(wl > -1 && lim > wl && foot > lim && modal > lim)) {
      errors.push(`limits: the inline section is not in the page body between the collected `
        + `records (${wl}) and the footer (${foot}), before the modal (${modal}): ${lim}`);
    }
  }
  for (const lang of ["en", "zh"]) {
    const d = DECK_LIMITS[lang];
    global.document.cookie = "tremor_lang=" + lang;
    setDATA(buildFixtureData());
    appendedNodes = [];
    el("modal").hidden = true;
    try {
      render();
      if (el("limits").hidden) {
        errors.push(`limits(${lang}): the restrictions section is hidden on the rendered page`);
      }
      const text = plainText(el("limits").innerHTML);
      if (!text.includes(d.title)) {
        errors.push(`limits(${lang}): the inline section does not carry the deck's title `
          + `${JSON.stringify(d.title)}`);
      }
      d.points.forEach((want, i) => {
        if (!text.includes(want)) {
          errors.push(`limits(${lang}): limitation ${i + 1} is not visible page text `
            + `(${JSON.stringify(want)})`);
        }
      });
      if (!text.includes(d.flights)) {
        errors.push(`limits(${lang}): the inline section does not carry the measured flights `
          + `sampling fact ${JSON.stringify(d.flights)}`);
      }
      // Visible means visible: none of it was read out of an opened panel.
      if (el("modal").hidden !== true) {
        errors.push(`limits(${lang}): reading the limitations required opening a panel`);
      }
    } catch (e) { errors.push(`limits render(${lang}): ${e.stack || e}`); }
  }

  // T31 (public-surface migration, item 7): the per-line direction is the
  // comparison direction recorded when the line was built -- a selection note,
  // not a verdict on a reading. Every detail and every card states it in the
  // deck's own words, in both languages; the retired `alarm` field and the
  // `alarming when …` phrasing are gone.
  const DIRECTION_LABEL = {
    en: "Comparison direction noted when this series was selected: ",
    zh: "比较方向（建线时记下）：",
  };
  for (const lang of ["en", "zh"]) {
    for (const L of LINES) {
      if (L.alarm !== undefined) {
        errors.push(`direction(${lang}): LINES entry ${L.id} still declares an \`alarm\` `
          + `field; the recorded direction belongs under declared_dir`);
      }
      if (L.declared_dir !== "up" && L.declared_dir !== "down") {
        errors.push(`direction(${lang}): LINES entry ${L.id} declares declared_dir `
          + `${JSON.stringify(L.declared_dir)}, expected "up" or "down"`);
        continue;
      }
      const dir = L.declared_dir === "down" ? T[lang].dirDown : T[lang].dirUp;
      const want = DIRECTION_LABEL[lang] + dir;
      const detail = plainText(lineModal(L, lang));
      if (!detail.includes(want)) {
        errors.push(`direction(${lang}): lineModal(${L.id}) does not state `
          + `${JSON.stringify(want)}`);
      }
      if (detail.includes("alarming when")) {
        errors.push(`direction(${lang}): lineModal(${L.id}) still renders the retired `
          + `\`alarming when …\` framing`);
      }
    }
    for (const retired of ["alarmTag", "alarmingWhen"]) {
      if (T[lang][retired] !== undefined) {
        errors.push(`direction(${lang}): the retired key ${JSON.stringify(retired)} is `
          + `still declared; one directionLabel states the recorded comparison direction`);
      }
    }
    // The cards carry the same note, so a reader does not have to open a line
    // to see what direction was recorded when it was built.
    global.document.cookie = "tremor_lang=" + lang;
    setDATA(buildHeadlineFixtureData());
    appendedNodes = [];
    try {
      render();
      const chips = appendedNodes.filter(n => (n.className || "").startsWith("inst"));
      for (const L of LINES.filter(x => (x.tier || 1) === 1)) {
        const dir = L.declared_dir === "down" ? T[lang].dirDown : T[lang].dirUp;
        const want = L.label[lang] + " · " + DIRECTION_LABEL[lang] + dir;
        const chip = chips.find(c => (c._html || "").includes(L.label[lang] + " · "));
        if (!chip) {
          errors.push(`direction(${lang}): no reading card rendered for ${L.id}`);
        } else if (!chip._html.includes(want)) {
          errors.push(`direction(${lang}): the ${L.id} card does not carry `
            + `${JSON.stringify(want)}`);
        }
      }
    } catch (e) { errors.push(`direction cards(${lang}): ${e.stack || e}`); }
  }

  // T32 (public-surface migration, item 6): one neutral treatment. A departure
  // in the recorded direction and a departure AGAINST it render the same
  // marker text (no favourable/unfavourable split), the marker never hatches,
  // and neither number is painted in JS -- both take the stylesheet's one
  // neutral reading mark. The retired `benign shift` wording is gone from both
  // languages. The stylesheet side of the rule (no severity hue anywhere) is
  // bound by tests/lint_public_surface.py::TestNeutralReadingTreatment, which
  // reads the CSS this harness cannot.
  const RETIRED_MARKER_TEXTS = { en: "benign shift", zh: "良性异动" };
  const neutralFixture = buildFixtureData();
  neutralFixture.summary = [{ date: FIXTURE_DATE, trembling_count: "2",
    dark_count: "0", blind_count: "0" }];
  // TIER1 order is [flights, credit_spread, cnh_cny]. flights (declared down)
  // trembles in its recorded direction; credit_spread (declared up) trembles
  // against it -- the case the old code painted green and called "benign shift".
  neutralFixture.lines.flights = [fixtureRow({ date: FIXTURE_DATE, raw_value: "1000",
    z_score: "-3.5", trembling: "1", direction: "down", status: "scoring" })];
  neutralFixture.lines.credit_spread = [fixtureRow({ date: FIXTURE_DATE, raw_value: "4.2",
    z_score: "-3.1", trembling: "1", direction: "down", status: "scoring" })];
  neutralFixture.lines.cnh_cny = [fixtureRow({ date: FIXTURE_DATE, raw_value: "10",
    z_score: "0.2", trembling: "0", direction: "up", status: "scoring" })];
  neutralFixture.lines.fed_srf_takeup = [fixtureRow({ date: FIXTURE_DATE,
    raw_value: "0", z_score: "0.1", trembling: "0", direction: "up", status: "scoring" })];
  neutralFixture.stuck = [{ date: FIXTURE_DATE, component: "Strait of Hormuz",
    since: "2026-04-06", pct: "4", stale: "",
    trail_median: "3", reference: "72", open_days: "151" }];
  for (const lang of ["en", "zh"]) {
    global.document.cookie = "tremor_lang=" + lang;
    setDATA(neutralFixture);
    appendedNodes = [];
    try {
      render();
      sweepForBadValues("neutral-" + lang);
      const Tl = T[lang];
      if (Tl.benignShift !== undefined) {
        errors.push(`neutral(${lang}): the retired benignShift key is still declared -- `
          + `a departure gets one marker in either direction`);
      }
      const chips = appendedNodes.filter(n => (n.className || "").startsWith("inst"));
      if (chips.length !== 4) {
        errors.push(`neutral(${lang}): expected 4 tier-1 chips, found ${chips.length}`);
      } else {
        const want = `class="pill trembling">${Tl.unusualPill}</span>`;
        for (const [i, id] of [[0, "flights (recorded direction)"],
                               [1, "credit_spread (against its recorded direction)"]]) {
          const chipHtml = chips[i]._html || "";
          if (!chipHtml.includes(want)) {
            errors.push(`neutral(${lang}): ${id} does not carry the one neutral marker `
              + `${JSON.stringify(Tl.unusualPill)}: ${chipHtml}`);
          }
          if (/class="pill benign/.test(chipHtml) || /adjudicated/.test(chipHtml)) {
            errors.push(`neutral(${lang}): ${id} still carries a direction- or `
              + `adjudication-specific marker: ${chipHtml}`);
          }
        }
        if (/class="pill trembling|class="pill benign/.test(chips[2]._html || "")) {
          errors.push(`neutral(${lang}): the calm cnh_cny card carries an unusual marker`);
        }
      }
      const surface = [el("count-label").innerHTML, el("count-n").textContent,
        el("sysstatus").innerHTML,
        ...appendedNodes.flatMap(n => [n._text, n._html])].join("\n");
      if (surface.toLowerCase().includes(RETIRED_MARKER_TEXTS[lang].toLowerCase())) {
        errors.push(`neutral(${lang}): the rendered page still carries the retired marker `
          + `wording ${JSON.stringify(RETIRED_MARKER_TEXTS[lang])}`);
      }
      for (const id of ["count-n", "level-n"]) {
        if (el(id).style.color !== undefined) {
          errors.push(`neutral(${lang}): #${id} is painted with `
            + `${JSON.stringify(el(id).style.color)} in JS instead of the one neutral `
            + `reading mark`);
        }
      }
    } catch (e) { errors.push(`neutral render(${lang}): ${e.stack || e}`); }
  }

  // T33 (completion R1.1): the real-vs-felt chart is deleted, not renamed. The
  // deck removes the chart, its explanation and its render path; the summary
  // chart title follows in render.py (bound by TestRealVsFeltChartIsGone and
  // TestChartTitlesStateTheRecordedDirection in tests/lint_public_surface.py).
  for (const token of ["feelchart", "feel-title", "feel-hint", "FEEL_IDS",
                       "isDivergent", "FEEL_HOT", "feelChart"]) {
    if (html.includes(token)) {
      errors.push(`feel: docs/index.html still carries the retired chart token ${JSON.stringify(token)}`);
    }
  }
  for (const lang of ["en", "zh"]) {
    const Tl = T[lang];
    for (const retired of ["feelTitle", "feelHint", "feelGapNote", "feelBars"]) {
      if (Tl[retired] !== undefined) {
        errors.push(`feel(${lang}): the retired copy key ${JSON.stringify(retired)} is still declared`);
      }
    }
    global.document.cookie = "tremor_lang=" + lang;
    setDATA(buildFixtureData());
    appendedNodes = [];
    try {
      render();
      for (const id of ["feel-title", "feel-hint", "feelchart"]) {
        if (made[id] !== undefined) {
          errors.push(`feel(${lang}): render still looks up the retired element #${id}`);
        }
      }
      const surface = [el("count-label").innerHTML, el("coverage").innerHTML,
        el("sysstatus").innerHTML,
        ...appendedNodes.flatMap(n => [n._text, n._html])].join("\n");
      if (/Real vs felt|真实 vs 感觉/.test(surface)) {
        errors.push(`feel(${lang}): the rendered page still carries the retired chart heading`);
      }
    } catch (e) { errors.push(`feel render(${lang}): ${e.stack || e}`); }
  }

  // T34 (completion R1.2): the status banner, panel headings, dated-notes
  // copy, footer, chart axis label and modal close label are the deck's. All
  // five banner branches are driven: no record, collection gap, majority dark
  // (T24), one dark, and the normal branch.
  const DECK_R12 = {
    en: {
      panel: ["Readings over time",
        "Each score compares one line with its own recent record. Dashed guides mark the statistical threshold; gaps are not filled."],
      footer: "A measuring instrument, not a forecast.",
      about: ["About this record", "This static page reads the published CSV files directly."],
      anno: ["Dated notes in the record",
        "They are attached text, not output from the scoring rule."],
    },
    zh: {
      panel: ["读数随时间的变化",
        "每条分数都与本线近期记录比较。虚线标出统计阈值；空缺不作填补。"],
      footer: "一件测量仪器，不作预言。",
      about: ["关于这份记录", "本静态页面直接读取已发布的 CSV 文件。"],
      anno: ["记录中的日期注记", "它们是附上的文字，不由计分规则生成。"],
    },
  };
  for (const lang of ["en", "zh"]) {
    global.document.cookie = "tremor_lang=" + lang;
    const Tl = T[lang];
    const deck = DECK_R12[lang];
    try {
      setDATA(buildFixtureData()); render();
      if (el("panel-title").textContent !== deck.panel[0]) {
        errors.push(`r12(${lang}): panel title is ${JSON.stringify(el("panel-title").textContent)}, `
          + `expected the deck's ${JSON.stringify(deck.panel[0])}`);
      }
      if (el("panel-hint").textContent !== deck.panel[1]) {
        errors.push(`r12(${lang}): panel hint is ${JSON.stringify(el("panel-hint").textContent)}, `
          + `expected the deck's ${JSON.stringify(deck.panel[1])}`);
      }
      if (!el("footer").innerHTML.includes(deck.footer)) {
        errors.push(`r12(${lang}): the footer does not carry the deck's sentence `
          + `${JSON.stringify(deck.footer)}`);
      }
      if (el("modal-x").getAttribute("aria-label") !== Tl.close) {
        errors.push(`r12(${lang}): the close control's aria-label is `
          + `${JSON.stringify(el("modal-x").getAttribute("aria-label"))}, expected `
          + `${JSON.stringify(Tl.close)}`);
      }
      if (!Tl.zAxis) errors.push(`r12(${lang}): the deck's zAxis key is not declared`);
      // About block: visible body text in the reading order (limits -> about -> footer).
      const limAt = html.indexOf('id="limits"'), aboutAt = html.indexOf('id="about"'),
        footAt = html.indexOf('id="footer"');
      if (!(limAt !== -1 && limAt < aboutAt && aboutAt < footAt)) {
        errors.push(`r12(${lang}): the About section is not in the page body between `
          + `the limits section (${limAt}) and the footer (${footAt}): ${aboutAt}`);
      }
      const aboutHtml = el("about").innerHTML;
      if (aboutHtml.includes("undefined")) {
        errors.push(`r12(${lang}): the About section rendered an undefined value: ${aboutHtml}`);
      }
      if (el("about").hidden) {
        errors.push(`r12(${lang}): the About section is hidden after a plain render`);
      }
      if (!aboutHtml.includes(deck.about[0]) || !aboutHtml.includes(deck.about[1])) {
        errors.push(`r12(${lang}): the About section does not carry the deck's heading and body: ${aboutHtml}`);
      }

      const banner = () => el("sysstatus").innerHTML;
      setDATA(buildNoRecordFixtureData()); render();
      if (!banner().includes(Tl.noRecord)) {
        errors.push(`r12(${lang}): the no-record banner does not state ${JSON.stringify(Tl.noRecord)}: ${banner()}`);
      }
      setDATA(buildGapFixtureData()); render();
      const gapCopy = Tl.disruption(GAP_DATE, 3);
      if (!banner().includes(gapCopy)) {
        errors.push(`r12(${lang}): the collection-gap banner does not state `
          + `${JSON.stringify(gapCopy)}: ${banner()}`);
      }
      setDATA(buildOneDarkFixtureData()); render();
      const oneDarkName = LINES.find(l => l.id === "flights").domain[lang];
      if (!banner().includes(Tl.warnH(1)) || !banner().includes(Tl.warnB(oneDarkName))) {
        errors.push(`r12(${lang}): the one-dark banner does not state `
          + `${JSON.stringify(Tl.warnH(1))} + ${JSON.stringify(Tl.warnB(oneDarkName))}: ${banner()}`);
      }
      setDATA(buildHeadlineFixtureData()); render();
      if (!banner().includes(Tl.statusOk)) {
        errors.push(`r12(${lang}): the normal banner does not state ${JSON.stringify(Tl.statusOk)}: ${banner()}`);
      }

      // Dated notes: heading + body in both detail builders.
      const noteFixture = buildFixtureData();
      const flightsLine = LINES.find(l => l.id === "flights");
      const vixLine = LINES.find(l => l.id === "vix");
      const flightNote = { date: FIXTURE_DATE, line: flightsLine.id, verdict: "artifact", note: "fixture dated note" };
      const vixNote = { date: FIXTURE_DATE, line: vixLine.id, verdict: "artifact", note: "fixture tier-2 note" };
      noteFixture.annotations = [flightNote, vixNote];
      noteFixture.annoMap = new Map([[flightsLine.id + "|" + FIXTURE_DATE, flightNote],
        [vixLine.id + "|" + FIXTURE_DATE, vixNote]]);
      setDATA(noteFixture);
      const lineHtml = lineModal(flightsLine, lang);
      if (!lineHtml.includes(deck.anno[0]) || !lineHtml.includes(deck.anno[1])) {
        errors.push(`r12(${lang}): the line detail does not carry the deck's dated-notes `
          + `heading and body: ${lineHtml}`);
      }
      openTier2Modal(vixLine, lang);
      const tier2Html = el("modal-body").innerHTML;
      if (!tier2Html.includes(deck.anno[0]) || !tier2Html.includes(deck.anno[1])) {
        errors.push(`r12(${lang}): the watchlist detail does not carry the deck's dated-notes `
          + `heading and body: ${tier2Html}`);
      }
    } catch (e) { errors.push(`r12 render(${lang}): ${e.stack || e}`); }
  }

  // T35 (completion R2): the displayed count is direction-free. Two tier-1
  // lines tremble for two consecutive days -- one in its recorded direction,
  // one against it -- so the ledger's trembling_count is 1 while the headline
  // must show 2 and name both lines, with a two-day run for each. A legacy
  // summary row (no unusual_count) derives the SAME rule from the per-line
  // rows; it must never fall back to trembling_count.
  for (const lang of ["en", "zh"]) {
    global.document.cookie = "tremor_lang=" + lang;
    const Tl = T[lang];
    try {
      setDATA(buildEitherDirectionFixtureData());
      render();
      if (el("count-n").textContent !== "2") {
        errors.push(`r2(${lang}): the headline shows ${JSON.stringify(el("count-n").textContent)}, `
          + `expected the stored direction-free count 2`);
      }
      const labelHtml = el("count-label").innerHTML;
      for (const id of ["flights", "credit_spread"]) {
        const label = LINES.find(l => l.id === id).label[lang];
        if (!labelHtml.includes(label)) {
          errors.push(`r2(${lang}): ${id} is not named in the count qualifier`);
        }
      }
      const runCore = Tl.runNote("", 2).replace(" · ", "");
      const runCount = labelHtml.split(runCore).length - 1;
      if (runCount !== 2) {
        errors.push(`r2(${lang}): expected the 2-day run for both firing lines, `
          + `found ${runCount}`);
      }

      const legacy = buildEitherDirectionFixtureData();
      delete legacy.summary[0].unusual_count;
      delete legacy.summary[0].count_method;
      setDATA(legacy);
      render();
      if (el("count-n").textContent !== "2") {
        errors.push(`r2(${lang}): a legacy row shows ${JSON.stringify(el("count-n").textContent)}, `
          + `expected the derived direction-free 2 (the ledger's trembling_count is 1)`);
      }
    } catch (e) { errors.push(`r2 render(${lang}): ${e.stack || e}`); }
  }

  // T36 (completion R3): the fixed-reference block states, per open state, the
  // pinned reference and the trailing median it is compared with, plus how
  // long the state has been open. The values come from the reporter's own
  // carried fields (trail_median/reference/open_days), never from the rounded
  // percentage. `levelWhich` (a bare name list without the reference) is gone.
  const LEVEL_NAMES = { en: ["Strait of Hormuz", "Kerch Strait"],
                        zh: ["霍尔木兹海峡", "刻赤海峡"] };
  const LEVEL_ROWS = [["3.5", "72", "207", "2026-04-06"], ["0", "12", "96", "2026-07-26"]];
  for (const lang of ["en", "zh"]) {
    global.document.cookie = "tremor_lang=" + lang;
    const Tl = T[lang];
    try {
      setDATA(buildLevelFixtureData());
      render();
      if (Tl.levelWhich !== undefined) {
        errors.push(`r3(${lang}): the retired levelWhich key is still declared`);
      }
      if (el("level-items").hidden) {
        errors.push(`r3(${lang}): the fixed-reference item list is hidden`);
      }
      const items = el("level-items").innerHTML;
      LEVEL_NAMES[lang].forEach((name, i) => {
        const [median, ref, days, since] = LEVEL_ROWS[i];
        const want = Tl.referenceItem(name, median, ref, days, since);
        if (!items.includes(want)) {
          errors.push(`r3(${lang}): the item list does not carry ${JSON.stringify(want)}: ${items}`);
        }
      });
      const label = el("level-label").innerHTML;
      if (!label.includes(Tl.referenceAsOf(RUNTIME_TODAY))) {
        errors.push(`r3(${lang}): the level label lost its source-as-of line: ${label}`);
      }
      if (LEVEL_NAMES[lang].some(name => label.includes(name))) {
        errors.push(`r3(${lang}): the level label still lists names without their reference: ${label}`);
      }
    } catch (e) { errors.push(`r3 render(${lang}): ${e.stack || e}`); }
  }

  // T37 (P1 security): the fixed-reference block renders a component name and
  // four CSV cells through the one markup sink. A hostile upstream component
  // name must arrive escaped, like every other record-derived string.
  for (const lang of ["en", "zh"]) {
    global.document.cookie = "tremor_lang=" + lang;
    const hostile = buildLevelFixtureData();
    hostile.stuck = [{ date: RUNTIME_TODAY, component: XSS_NOTE, since: "2026-04-06",
      pct: "4", stale: "", trail_median: "3", reference: "72", open_days: "151" }];
    setDATA(hostile);
    appendedNodes = [];
    try {
      render();
      errors.push(...xssErrors("level-" + lang));
    } catch (e) { errors.push(`level xss(${lang}): ${e.stack || e}`); }
  }

  await new Promise(r => setTimeout(r, 50));
  if (errors.length) { console.log("FAILURES:\n" + errors.join("\n\n")); process.exit(1); }
  console.log("render OK in both languages; no runtime errors, no undefined/NaN");
  console.log("  headline:", el("count-n").textContent, "/", el("count-of").textContent);
  console.log("  label   :", el("count-label").innerHTML.replace(/<[^>]+>/g, "").trim());
  console.log("  coverage:", el("coverage").innerHTML.replace(/<[^>]+>/g, "").trim().slice(0, 110));
  } catch (e) { console.log("HARNESS FAILURE: " + (e && e.stack || e)); process.exit(1); }
})();
