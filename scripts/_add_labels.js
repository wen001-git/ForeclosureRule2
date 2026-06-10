// One-time transform: fill Chinese name + business meaning for every field lacking a Chinese label,
// sourcing sync_loan_foreclosure columns Code-First from the basic_data_loan_foreclosure CREATE-TABLE
// DDL comments; author stage/hold/identity/lm/bk names by domain. Also add meta.revisions (changelog).
// Run: node scripts/_add_labels.js   (idempotent)
const fs = require("fs");
const P = "outputs/fcl_lineage_source.json";
const J = JSON.parse(fs.readFileSync(P, "utf8"));
const POOL = "C:/Users/jli/MyData/Copilot/PrefectFlow/flow/basic_data/basic_data_config/basic_data_pool_config.py";
const cjk = s => /[一-鿿]/.test(s || "");

// ---- 1. extract DDL comments from CREATE TABLE port.basic_data_loan_foreclosure ----
const src = fs.readFileSync(POOL, "utf8");
const ddl = {};
const start = src.indexOf("CREATE TABLE IF NOT EXISTS port.basic_data_loan_foreclosure");
const block = src.slice(start, src.indexOf("DISTSTYLE", start));
block.split("\n").forEach(line => {
  const m = line.match(/^\s*([a-z_][a-z0-9_]*)\s+[A-Za-z0-9_(),\s]+?,?\s*--\s*(.*?)\s*[（(]([^)）]+)[)）]/);
  if (m && !cjk(m[2])) ddl[m[1]] = { en: m[2].trim(), zh: m[3].trim() };  // skip Chinese-only comments (e.g. timeline_publication_date)
});

// ---- 2. hand-authored names for columns without DDL comments ----
const COMMON = {
  loanid: { en: "Investor loan id", zh: "投资人贷款 ID" },
  svcloanid: { en: "Servicer loan id", zh: "服务商贷款 ID" },
};
const HAND = {
  summary_last_step_completed_date: { en: "Last step completed date", zh: "最近完成步骤日期" },
  // hold
  description: { en: "Hold description", zh: "Hold 描述（暂停原因）" },
  description_start_date: { en: "Hold start date", zh: "Hold 开始日" },
  description_end_date: { en: "Hold end date", zh: "Hold 结束日" },
  // lm
  imminent_default: { en: "Imminent default flag", zh: "即将违约标志" },
  single_point_of_contact: { en: "Single point of contact", zh: "单一联系人(SPOC)" },
  // bk
  lien_status: { en: "Lien status", zh: "留置状态" },
  mfr_status: { en: "MFR status", zh: "解除自动中止(MFR)状态" },
  mfr_filed_date: { en: "MFR filed date", zh: "MFR 申请日" },
  claim_status: { en: "Claim status", zh: "债权状态" },
  post_petition_due_date: { en: "Post-petition due date", zh: "破产后应付日" },
  first_legal_date_history: { en: "First-legal first-seen date", zh: "首次法律日(首见追踪)" },
  timeline_publication_date: { en: "Publication scheduled date", zh: "止赎公告计划发布日期" },
};
const STAGE_ZH = { demand: "催告/Demand", noi: "NOI", referral: "转介", first_legal: "首次法律", service: "送达", publication: "公告", judgement: "判决", sale: "拍卖" };
const STAGE_EN = { demand: "Demand", noi: "NOI", referral: "Referral", first_legal: "First Legal", service: "Service", publication: "Publication", judgement: "Judgement", sale: "Sale" };
function stageName(col) {
  for (const s of Object.keys(STAGE_ZH)) {
    if (col === s + "_start_date") return { en: STAGE_EN[s] + " start date", zh: STAGE_ZH[s] + " 阶段开始日" };
    if (col === s + "_end_date") return { en: STAGE_EN[s] + " window end", zh: STAGE_ZH[s] + " 阶段结束日(窗口)" };
    if (col === s + "_stage_days") return { en: STAGE_EN[s] + " days in stage", zh: STAGE_ZH[s] + " 阶段已历天数" };
    if (col === s + "_in_lm_days") return { en: STAGE_EN[s] + " days in LM", zh: STAGE_ZH[s] + " 阶段内 LM 天数" };
    if (col === s + "_on_hold_days") return { en: STAGE_EN[s] + " days on hold", zh: STAGE_ZH[s] + " 阶段内 Hold 天数" };
  }
  if (col === "to_judgement_days") return { en: "Days to judgement", zh: "距判决倒计天数" };
  if (col === "to_sale_days") return { en: "Days to sale", zh: "距拍卖倒计天数" };
  return null;
}

function nameFor(col) {
  return COMMON[col] || ddl[col] || HAND[col] || stageName(col) || null;
}

let filled = 0, missed = [];
J.fields.forEach(f => {
  if (["system", "view"].includes(f.family)) return;
  const lab = f.label || {};
  if (cjk(lab.zh)) return;                       // already has a Chinese name
  const col = ((f.hops || []).find(h => h.t && h.t.startsWith("bpms.")) || {}).c || f.label.en;
  const nm = nameFor(col);
  if (!nm) { missed.push(f.bps_table + "." + col); return; }
  f.label = { en: nm.en, zh: nm.zh };
  // business meaning: prefer DDL/hand meaning; keep existing if already meaningful (non-generic)
  const bzGeneric = !f.biz || !cjk((f.biz || {}).zh);
  if (bzGeneric) f.biz = { en: nm.en + ".", zh: nm.zh + "。" };
  filled++;
});

// ---- 3. revision history (changelog) — rendered by the generator ----
J.meta.revisions = [
  { date: "2026-06-09", ver: "v1", zh: "初稿：doc 25–30 由 fcl_lineage_source.json 生成（per-field 血缘 + 跳链 + 取数 SQL）", en: "Initial: doc 25–30 generated from fcl_lineage_source.json (per-field lineage + hop chain + fetch SQL)" },
  { date: "2026-06-09", ver: "v2", zh: "Servicer 分列（Newrez/Carrington/Capecodfive 来源分开）", en: "Per-servicer source columns (Newrez/Carrington/Capecodfive separated)" },
  { date: "2026-06-09", ver: "v3", zh: "非平凡 SQL 加说明 + 计算示例", en: "Non-trivial SQL annotated with explanation + worked example" },
  { date: "2026-06-09", ver: "v4", zh: "改为每字段竖排卡片，规则写全不省略", en: "Switched to per-field vertical cards; rules written in full" },
  { date: "2026-06-09", ver: "v5", zh: "跳链补 tempfc 行 + 说明 L2/L3 为何不在本分支；字段标题加序号", en: "Added tempfc hop + L2/L3-absent note to the chain; numbered field cards" },
  { date: "2026-06-09", ver: "v6", zh: "覆盖 BPS sync 表全部列（系统/审计列分组、视图计算列）；每跳加流动顺序", en: "Cover every BPS sync-table column (system/audit grouped, view-computed); numbered data-flow order" },
  { date: "2026-06-09", ver: "v7", zh: "为所有字段补中文名/业务含义（DDL 注释 Code-First 提取）；新增修订历史维护", en: "Added Chinese name/business meaning to every field (Code-First from DDL comments); started maintaining the revision history" },
];

fs.writeFileSync(P, JSON.stringify(J, null, 2) + "\n");
console.log("labels filled:", filled, "| still missing:", missed.length ? missed : "none", "| DDL cols:", Object.keys(ddl).length, "| revisions:", J.meta.revisions.length);
