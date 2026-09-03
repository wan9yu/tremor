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
    setAttribute() {}, removeAttribute() {},
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
(0, eval)(js + "\n;globalThis.__P={LINES,covModal,resoModal,lineModal,levelModal,openTier2Modal,render,load,setDATA:function(v){DATA=v;}};");
const {LINES,covModal,resoModal,lineModal,levelModal,openTier2Modal,render,load,setDATA}=globalThis.__P;

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
// render a "NO DATA" gap chip, and (the boundary case) a tier-2 line dark for
// only ONE collection must NOT. Exercised via setDATA(), bypassing
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
function buildFixtureData() {
  const lines = {};
  // --- tier-1 (all four): one of each of scoring+trembling, scoring+calm,
  // closed, dark -- the tier-1 strip only branches on hasToday/isClosed, so
  // this is what exercises that branch, not the full statusLabel map (that
  // map is read only by the tier-2 watchlist below).
  lines.flights = [fixtureRow({ date: FIXTURE_DATE, raw_value: "1000", z_score: "-3.5",
    trembling: "1", direction: "down", status: "scoring" })];               // alarm=down: fires
  lines.credit_spread = [fixtureRow({ date: FIXTURE_DATE, raw_value: "4.2", z_score: "0.4",
    trembling: "0", direction: "up", status: "scoring" })];                 // calm
  lines.cnh_cny = [fixtureRow({ date: FIXTURE_DATE, status: "closed",
    source_note: "no new observation: FX weekend, both legs frozen" })];
  lines.net_outages = [fixtureRow({ date: FIXTURE_DATE, status: "dark",
    source_note: "IODA request failed: timeout" })];
  // --- tier-2: the remaining statuses, plus the gap-chip run boundary ---
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
    try { covModal(lang); resoModal(lang); levelModal(lang); } catch (e) { errors.push(`modal(${lang}): ${e.stack || e}`); }
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
      } else if (!/NO DATA|无数据/.test(gapItems[0]._html)) {
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
    // exercise the modal builders against the fixture too, tier-1 and tier-2.
    try { covModal(lang); resoModal(lang); levelModal(lang); } catch (e) { errors.push(`fixture modal(${lang}): ${e.stack || e}`); }
    for (const id of Object.keys(fixture.lines)) {
      const L = LINES.find(x => x.id === id);
      if (!L) continue;
      try { lineModal(L, lang); } catch (e) { errors.push(`fixture lineModal(${id},${lang}): ${e.stack || e}`); }
      if ((L.tier || 1) === 2) {
        try { openTier2Modal(L, lang); } catch (e) { errors.push(`fixture openTier2Modal(${id},${lang}): ${e.stack || e}`); }
      }
    }
  }

  await new Promise(r => setTimeout(r, 50));
  if (errors.length) { console.log("FAILURES:\n" + errors.join("\n\n")); process.exit(1); }
  console.log("render OK in both languages; no runtime errors, no undefined/NaN");
  console.log("  headline:", el("count-n").textContent, "/", el("count-of").textContent);
  console.log("  label   :", el("count-label").innerHTML.replace(/<[^>]+>/g, "").trim());
  console.log("  coverage:", el("coverage").innerHTML.replace(/<[^>]+>/g, "").trim().slice(0, 110));
  } catch (e) { console.log("HARNESS FAILURE: " + (e && e.stack || e)); process.exit(1); }
})();
