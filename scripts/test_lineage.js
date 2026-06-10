// Comprehensive test harness for the foreclosure field-lineage artifacts (doc 25-30).
// Run: node scripts/test_lineage.js
// Structural tests run inline; it also PRINTS two schema-verify SQL statements to run via MCP.
const fs = require("fs");
const path = require("path");
let PASS = 0, FAIL = 0;
function ok(name, cond, detail) {
  if (cond) { PASS++; console.log("  PASS", name); }
  else { FAIL++; console.log("  FAIL", name, detail ? "->" + detail : ""); }
}
const ROOT = process.cwd();
const J = JSON.parse(fs.readFileSync("outputs/fcl_lineage_source.json", "utf8"));

console.log("== T1. JSON integrity ==");
ok("has fields", Array.isArray(J.fields) && J.fields.length > 0, J.fields.length);
ok("has 5 branches", Object.keys(J.branches).length === 5);
let hopBad = 0, chainMismatch = 0, missKey = 0;
const REQ = ["branch", "bps_table", "family", "label", "hops"];
J.fields.forEach(f => {
  REQ.forEach(k => { if (!(k in f)) missKey++; });
  // cards render hops sequentially; real lineage fields need >=2 hops, but grouped (system/view) and
  // identity/PK entries are legitimately single-hop.
  const exempt = ["system", "view", "identity"].includes(f.family);
  if (!exempt && f.hops.length < 2) chainMismatch++;
  f.hops.forEach(h => { if (!("t" in h && "c" in h && "rule" in h)) hopBad++; });
});
ok("all fields have required keys", missKey === 0, missKey);
ok("every field has a raw→…→BPS path (>=2 hops)", chainMismatch === 0, chainMismatch);
ok("all hops have t/c/rule", hopBad === 0, hopBad);
// every field's bps_table matches its branch bps_table
let btMismatch = 0;
J.fields.forEach(f => { if (J.branches[f.branch].bps_table !== f.bps_table) btMismatch++; });
ok("field bps_table matches branch", btMismatch === 0, btMismatch);
// last hop of each field must be a bpms.* table; main branch ends at view, others at sync
let noBps = 0;
J.fields.forEach(f => { if (!f.hops.some(h => h.t.startsWith("bpms."))) noBps++; });
ok("every field reaches a bpms.* table", noBps === 0, noBps);
// every sql block has a bilingual note + worked example
let sqlMiss = 0;
J.fields.forEach(f => {
  if (f.sql) {
    const n = f.sql_note, e = f.sql_eg;
    if (!(n && n.en && n.zh && e && e.en && e.zh)) sqlMiss++;
  }
});
ok("every sql has bilingual note + example", sqlMiss === 0, sqlMiss);
// completeness: every column of every sync table is covered (entry sync-col == col, or in a system group)
const EXPECT_COLS = { sync_loan_foreclosure: 72, sync_fcl_stage_info: 57, sync_loan_foreclosure_hold: 15, sync_loan_foreclosure_loss_mitigation: 22, sync_loan_foreclosure_bankruptcy: 22 };
let covGaps = [];
if (J.meta.table_columns) {
  for (const [t, cols] of Object.entries(J.meta.table_columns)) {
    const covered = new Set();
    J.fields.filter(f => f.bps_table === t).forEach(f => {
      const h = (f.hops || []).find(x => x.t && x.t.startsWith("bpms."));
      if (f.family === "system") String((f.hops[0] || {}).c || "").split(", ").forEach(c => covered.add(c.trim()));
      else if (h) covered.add(h.c);
    });
    const miss = cols.filter(c => !covered.has(c));
    if (miss.length) covGaps.push(t + ":" + miss.join(","));
    if (cols.length !== EXPECT_COLS[t]) covGaps.push(t + " count " + cols.length + "!=" + EXPECT_COLS[t]);
  }
}
ok("100% column coverage per sync table", covGaps.length === 0, covGaps.join(" | "));
// every business field (not system/view grouping) carries a Chinese name in its label
const cjk = s => /[一-鿿]/.test(s || "");
let noCjk = [];
J.fields.forEach(f => {
  if (["system", "view"].includes(f.family)) return;
  if (!cjk((f.label || {}).zh)) noCjk.push(f.bps_table + "." + (f.label || {}).en);
});
ok("every business/stage/identity field has a Chinese name", noCjk.length === 0, noCjk.join(","));
// revision history is maintained (>=2 versions, each with date/ver/bilingual change)
const revs = (J.meta.revisions || []);
const revBad = revs.length < 2 || revs.some(r => !(r.date && r.ver && r.zh && r.en));
ok("revision history maintained (>=2 versions, bilingual)", !revBad, revs.length + " versions");

console.log("== T2. Doc rendering integrity (12 files) ==");
const DOCS = [["25", "fcl_lineage_overview"], ["26", "lineage_sync_loan_foreclosure"],
  ["27", "lineage_sync_fcl_stage_info"], ["28", "lineage_sync_loan_foreclosure_hold"],
  ["29", "lineage_sync_loan_foreclosure_loss_mitigation"], ["30", "lineage_sync_loan_foreclosure_bankruptcy"]];
const LANGS = ["zh", "en"];
let allExist = true;
const text = {};
for (const [n, s] of DOCS) for (const lg of LANGS) {
  const p = path.join("docs", lg, `${n}_${s}.md`);
  const ex = fs.existsSync(p);
  if (!ex) allExist = false;
  if (ex) text[`${lg}/${n}`] = fs.readFileSync(p, "utf8");
}
ok("all 12 docs exist", allExist);
// markdown table column consistency + leakage scan
function checkTables(md) {
  const lines = md.split("\n");
  let issues = 0;
  for (let i = 0; i < lines.length; i++) {
    const l = lines[i];
    if (/^\s*\|/.test(l) && /\|\s*$/.test(l)) {
      // a table row; if next line is a separator, this is a header
      const cnt = (l.match(/\|/g) || []).length;
      // find contiguous block
      if (/^\s*\|[\s\-:|]+\|\s*$/.test(lines[i + 1] || "")) {
        const sep = (lines[i + 1].match(/\|/g) || []).length;
        if (sep !== cnt) issues++;
        // rows below
        let j = i + 2;
        while (j < lines.length && /^\s*\|/.test(lines[j])) {
          const rc = (lines[j].match(/\|/g) || []).length;
          if (rc !== cnt) issues++;
          j++;
        }
      }
    }
  }
  return issues;
}
let tblIssues = 0, leak = 0;
const LEAKS = ["undefined", "None", "PLACEHOLDER", "[object Object]", "NaN"];
for (const k in text) {
  tblIssues += checkTables(text[k]);
  for (const w of LEAKS) if (text[k].includes(w)) { leak++; }
}
ok("no markdown table column mismatches", tblIssues === 0, tblIssues);
ok("no placeholder/undefined leakage", leak === 0, leak);
// zh/en parity: same number of field rows (lines starting with '| **') per doc
let parity = 0;
for (const [n] of DOCS) {
  const zc = (text[`zh/${n}`].match(/^### /gm) || []).length;
  const ec = (text[`en/${n}`].match(/^### /gm) || []).length;
  if (zc !== ec) parity++;
}
ok("zh/en card-count parity per doc", parity === 0, parity);
// per-servicer source rendered as cards (Capecodfive line present in main & stage docs)
let svcRendered = 0;
for (const lg of LANGS) for (const n of ["26", "27"]) {
  if (text[`${lg}/${n}`].includes("Capecodfive:")) svcRendered++;
}
ok("per-servicer source rendered in cards (26/27)", svcRendered === 4, svcRendered);
// hub links to 26-30
let linkMiss = 0;
for (const lg of LANGS) for (const d of ["26", "27", "28", "29", "30"]) {
  if (!text[`${lg}/25`].includes("doc " + d) && !text[`${lg}/25`].includes(d + "_lineage")) linkMiss++;
}
ok("hub links to all per-table docs", linkMiss === 0, linkMiss);
// every code ref like pool:NNN / asset:NNN present in at least the matrices
let codeRefs = 0;
for (const k in text) codeRefs += (text[k].match(/\b(pool|asset):\d/g) || []).length;
ok("code refs present in docs", codeRefs > 50, codeRefs);

console.log("== T3. Build schema-verify SQL (run via MCP) ==");
// collect clean single-identifier columns from hops
const ident = s => /^[a-z][a-z0-9_]+$/.test(s);
function parseTbl(t) { // 'newrez.portnewrezfc (..)' -> {schema,table}
  const base = t.split(" ")[0];
  const dot = base.indexOf(".");
  return { schema: base.slice(0, dot), table: base.slice(dot + 1) };
}
const refs = new Set(); // "schema|table|col"
J.fields.forEach(f => f.hops.forEach(h => {
  if (!h.t.includes(".")) return;
  const { schema, table } = parseTbl(h.t);
  if (!schema || !table.match(/^[a-z_]+$/)) return;
  if (ident(h.c)) refs.add(`${schema}|${table}|${h.c}`);
}));
// also collect per-servicer source columns (table.col), mapping table -> schema
function schemaOf(tbl) {
  if (tbl === "portcarrington") return "carrington";
  if (tbl === "portcapecodfive_monthly_collections") return "capecodfive";
  if (tbl.startsWith("portnewrez")) return "newrez";
  if (tbl.startsWith("basic_data") || tbl === "fcl_stage_info") return "port";
  if (tbl.startsWith("sync")) return "bpms";
  return null;
}
J.fields.forEach(f => {
  const sv = f.servicers || {};
  Object.values(sv).forEach(v => {
    if (!/^[a-z][a-z0-9_]*\.[a-z0-9_]+$/.test(v)) return; // single clean table.col only
    const dot = v.indexOf(".");
    const tbl = v.slice(0, dot), col = v.slice(dot + 1);
    const sc = schemaOf(tbl);
    if (sc) refs.add(`${sc}|${tbl}|${col}`);
  });
});
// EXTRA expanded concrete columns for templated/composite rows
const STAGES = ["demand", "noi", "referral", "first_legal", "service", "publication", "judgement", "sale"];
function add(schema, table, cols) { cols.forEach(c => refs.add(`${schema}|${table}|${c}`)); }
const stageCols = [];
STAGES.forEach(s => { stageCols.push(s + "_start_date", s + "_in_lm_days", s + "_on_hold_days"); });
["demand", "noi", "referral", "first_legal", "service", "publication"].forEach(s => stageCols.push(s + "_stage_days"));
stageCols.push("to_sale_days", "to_judgement_days", "group", "judicial", "state", "fctrdt", "loanid");
add("port", "fcl_stage_info", stageCols);
add("bpms", "sync_fcl_stage_info", stageCols);
add("port", "basic_data_loan_fcl", ["referral_start_date", "legal_start_date", "service_start_date", "fcjudgment_hearing_scheduled", "fcscheduled_sale_date", "demandsentdate", "fchold1startdate", "fchold1enddate", "fchold1description", "fchold2startdate", "fchold2enddate", "fchold2description", "fchold3startdate", "fchold3enddate", "fchold3description"]);
add("port", "basic_data_loan_foreclosure_hold", ["description1", "description1_start_date", "description1_end_date", "description2", "description2_start_date", "description2_end_date", "description3", "description3_start_date", "description3_end_date", "description4", "description4_start_date", "description4_end_date"]);
add("bpms", "sync_loan_foreclosure_hold", ["description", "description_start_date", "description_end_date"]);
add("newrez", "portnewrezfc", ["fchold1description", "fchold1startdate", "fchold1enddate", "fchold2description", "fchold2startdate", "fchold2enddate", "fchold3description", "fchold3startdate", "fchold3enddate"]);
add("newrez", "portnewrezpmt", ["nextduedate"]);
add("newrez", "portnewrezprop", ["propertystate"]);
add("newrez", "portnewrezgeneral", ["delinquency_status_mba", "legalstatus"]);
add("port", "basic_data_fcl_related", ["delq_status", "propertystate"]);
add("port", "basic_data_loan_foreclosure_bankruptcy", ["lien_status", "mfr_status", "mfr_filed_date", "claim_status"]);
add("bpms", "sync_loan_foreclosure_bankruptcy", ["lien_status", "mfr_status", "mfr_filed_date", "claim_status"]);

const mysqlRefs = [], rsRefs = [];
[...refs].sort().forEach(r => {
  const [schema, table, col] = r.split("|");
  if (schema === "newrez" || schema === "bpms") mysqlRefs.push([schema, table, col]);
  else if (schema === "port" || schema === "tempfc" || schema === "carrington" || schema === "capecodfive") rsRefs.push([schema, table, col]);
});
function valSql(rows) { return rows.map(([s, t, c]) => `('${s}','${t}','${c}')`).join(","); }
const mysqlSql = `SELECT r.s,r.t,r.c FROM (SELECT * FROM (VALUES ${"ROW".length ? "" : ""}${valSql(mysqlRefs)}) AS x(s,t,c)) r LEFT JOIN information_schema.columns ic ON ic.table_schema=r.s AND ic.table_name=r.t AND ic.column_name=r.c WHERE ic.column_name IS NULL;`;
// MySQL 8 VALUES ROW() syntax: use UNION approach for safety
const mysqlSql2 = `WITH refs(s,t,c) AS (${mysqlRefs.map(([s, t, c]) => `SELECT '${s}','${t}','${c}'`).join(" UNION ALL ")}) SELECT r.s,r.t,r.c FROM refs r LEFT JOIN information_schema.columns ic ON ic.table_schema=r.s AND ic.table_name=r.t AND ic.column_name=r.c WHERE ic.column_name IS NULL;`;
const rsSql = `WITH refs(s,t,c) AS (${rsRefs.map(([s, t, c]) => `SELECT '${s}'::varchar,'${t}'::varchar,'${c}'::varchar`).join(" UNION ALL ")}) SELECT r.s,r.t,r.c FROM refs r LEFT JOIN information_schema.columns ic ON ic.table_schema=r.s AND ic.table_name=r.t AND ic.column_name=r.c WHERE ic.column_name IS NULL;`;
ok("mysql refs collected", mysqlRefs.length > 30, mysqlRefs.length);
ok("redshift refs collected", rsRefs.length > 30, rsRefs.length);
fs.writeFileSync("outputs/_verify_mysql.sql", mysqlSql2);
fs.writeFileSync("outputs/_verify_redshift.sql", rsSql);
console.log("  wrote outputs/_verify_mysql.sql (" + mysqlRefs.length + " refs), outputs/_verify_redshift.sql (" + rsRefs.length + " refs)");

console.log(`\n== SUMMARY: ${PASS} passed, ${FAIL} failed ==`);
process.exit(FAIL ? 1 : 0);
