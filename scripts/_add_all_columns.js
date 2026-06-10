// One-time transform: enumerate EVERY column of each BPS sync table.
// - preserves curated entries (matched by their bpms.sync_* hop column)
// - expands the {stage}_* templated entries into concrete per-stage columns
// - groups create_*/update_*/status/is_deleted/tenant_id into one system_audit entry per table
// - adds a view_computed entry (sync_loan_foreclosure) for actual_*/var_*/total
// - sets meta.table_columns (full MCP inventory) for the completeness test
// Run: node scripts/_add_all_columns.js   (idempotent)
const fs = require("fs");
const P = "outputs/fcl_lineage_source.json";
const J = JSON.parse(fs.readFileSync(P, "utf8"));

// ---- full MCP column inventories (ordinal order) ----
const TC = {
  sync_loan_foreclosure: ["id","bid_id","funding_id","loanid","svcloanid","servicer","timeline_notice_of_intent_date","timeline_notice_of_intent_end_date","timeline_approved_for_referral_date","timeline_referred_to_attorney_date","timeline_referred_to_foreclosure_date","timeline_title_report_received_date","timeline_preliminary_title_cleared_date","timeline_first_legal_date","timeline_service_date","timeline_publication_date","timeline_judgement_hearing_set_date","timeline_judgement_date","timeline_sale_date_projected_date","timeline_sale_date_set_date","timeline_final_title_cleared_date","timeline_sale_date_held_date","timeline_foreclosure_completed_date","timeline_third_party_sold_date_date","timeline_third_party_proceeds_received_date","target_notice_of_intent_days","target_notice_of_intent_expired_days","target_approved_for_referral_days","target_referred_to_attorney_days","target_referred_to_foreclosure_days","target_title_report_received_days","target_preliminary_title_cleared_days","target_first_legal_days","target_service_days","target_publication_days","target_judgement_hearing_set_days","target_judgement_days","target_sale_date_set_days","target_final_title_cleared_days","target_sale_date_held_days","variance_active_bankruptcy","variance_completed_bankruptcy","variance_estimated_hold_days","variance_bankruptcies","bid_approval_status","bid_approval_sale_date","bid_approval_bid_amount","bid_approval_loan_resolution_holods","summary_servicer_number","summary_foreclosure_status","summary_completed_foreclosure","summary_foreclosure_bid_amount","summary_srv_fc_bid_amount","summary_foreclosure_sale_amount","summary_judicial_foreclosure","summary_foreclosure_attorney","summary_contested_litigation","summary_firm","summary_type","summary_sms_days_in_fcl","summary_days_in_fcl","summary_current_step","summary_last_step_completed","summary_last_step_completed_date","create_user","create_dept","create_time","update_user","update_time","status","is_deleted","tenant_id"],
  sync_fcl_stage_info: ["id","stage","fctrdt","loanid","group","servicer","state","judicial","demand_start_date","demand_end_date","demand_stage_days","demand_in_lm_days","demand_on_hold_days","noi_start_date","noi_end_date","noi_stage_days","noi_in_lm_days","noi_on_hold_days","referral_start_date","referral_end_date","referral_stage_days","referral_in_lm_days","referral_on_hold_days","first_legal_start_date","first_legal_end_date","first_legal_stage_days","first_legal_in_lm_days","first_legal_on_hold_days","first_legal_date_history","service_start_date","service_end_date","service_stage_days","service_in_lm_days","service_on_hold_days","publication_start_date","publication_end_date","publication_stage_days","publication_in_lm_days","publication_on_hold_days","judgement_start_date","judgement_end_date","to_judgement_days","judgement_in_lm_days","judgement_on_hold_days","sale_start_date","sale_end_date","to_sale_days","sale_in_lm_days","sale_on_hold_days","create_time","update_time","create_user","create_dept","update_user","status","is_deleted","tenant_id"],
  sync_loan_foreclosure_hold: ["id","loanid","svcloanid","fctrdt","description","description_start_date","description_end_date","create_user","create_dept","create_time","update_user","update_time","status","is_deleted","tenant_id"],
  sync_loan_foreclosure_loss_mitigation: ["id","loanid","svcloanid","fctrdt","deal","program","lmc_status","cycle_opened_date","cycle_closed_date","final_disposition","denialreason","borrower_intentions","imminent_default","single_point_of_contact","create_user","create_dept","create_time","update_user","update_time","status","is_deleted","tenant_id"],
  sync_loan_foreclosure_bankruptcy: ["id","loanid","svcloanid","fctrdt","bankruptcy_status","legal_status","status_date","chapter","lien_status","mfr_status","mfr_filed_date","claim_status","proof_of_claim_date","post_petition_due_date","create_user","create_dept","create_time","update_user","update_time","status","is_deleted","tenant_id"]
};
J.meta.table_columns = TC;
const SYS = ["create_user","create_dept","create_time","update_user","update_time","status","is_deleted","tenant_id"];
const B = (en, zh) => ({ en, zh });

// ---- index curated entries by (bps_table, sync-hop column) ----
function syncCol(f) {
  const h = (f.hops || []).find(x => x.t && x.t.startsWith("bpms.sync"));
  return h ? h.c : null;
}
// index curated entries by EACH concrete sync column (split multi-col); rebuild other/system/view fresh
const curatedByCol = {};
const pushed = new Set();
for (const f of J.fields) {
  if (["other", "system", "view", "stage_date", "stage_days", "identity"].includes(f.family)) continue;  // re-synthesize stage/identity columns deterministically
  const c = syncCol(f);
  if (!c) continue;
  c.split(/[\/,]/).map(s => s.trim()).filter(s => s && !s.includes("{") && !s.includes(" "))
    .forEach(cc => { curatedByCol[f.bps_table + "|" + cc] = f; });
}
// stash stage metric templates (sql/sql_note/sql_eg) from the templated entries
const stageTpl = {};
for (const f of J.fields) {
  if (f.bps_table !== "sync_fcl_stage_info" || !f.sql) continue;
  const c = syncCol(f) || "";
  if (!stageTpl.stage_days && /_stage_days$/.test(c)) stageTpl.stage_days = f;       // templated {stage}_stage_days or concrete X_stage_days
  else if (!stageTpl.to_days && /to_(sale|judgement)_days$/.test(c)) stageTpl.to_days = f;
  else if (!stageTpl.in_lm && /_in_lm_days$/.test(c)) stageTpl.in_lm = f;
  else if (!stageTpl.on_hold && /_on_hold_days$/.test(c)) stageTpl.on_hold = f;
}

// ---- helpers to synthesize entries ----
const branchOf = { sync_loan_foreclosure: "main", sync_fcl_stage_info: "stage", sync_loan_foreclosure_hold: "hold", sync_loan_foreclosure_loss_mitigation: "lm", sync_loan_foreclosure_bankruptcy: "bk" };
const PORT = { sync_loan_foreclosure: "basic_data_loan_foreclosure", sync_fcl_stage_info: "fcl_stage_info", sync_loan_foreclosure_hold: "basic_data_loan_foreclosure_hold", sync_loan_foreclosure_loss_mitigation: "basic_data_loan_foreclosure_loss_mitigation", sync_loan_foreclosure_bankruptcy: "basic_data_loan_foreclosure_bankruptcy" };
function entry(tbl, fam, col, label, biz, hops, extra) {
  return Object.assign({ branch: branchOf[tbl], bps_table: tbl, family: fam, label, biz, hops }, extra || {});
}
// main-branch identity hops
function mainIdentityHops(col, rawcol, factcol) {
  return [
    { t: "newrez.portnewrezfc", c: rawcol || col, rule: "servicer raw 原始" },
    { t: "port.basic_data_loan_fcl", c: factcol || rawcol || col, rule: "rename/passthrough 改名直传" },
    { t: "port.basic_data_loan_foreclosure", c: col, rule: "passthrough 直传" },
    { t: "bpms.sync_loan_foreclosure", c: col, rule: "GEN_FORECLOSURE join port.portfunding 直传", code: "asset:543" },
    { t: "bpms.biz_data_view_loan_details_foreclosure", c: col, rule: "passthrough", code: "view" }
  ];
}
function mainNullHops(col, note) {
  return [
    { t: "port.basic_data_loan_foreclosure", c: col, rule: note, code: "pool:148-305" },
    { t: "bpms.sync_loan_foreclosure", c: col, rule: "GEN_FORECLOSURE 直传（值=NULL）", code: "asset:540-605" },
    { t: "bpms.biz_data_view_loan_details_foreclosure", c: col, rule: "passthrough", code: "view" }
  ];
}

const newFields = [];
for (const tbl of Object.keys(TC)) {
  const cols = TC[tbl];
  const sysPresent = [];
  for (const col of cols) {
    if (SYS.includes(col)) { sysPresent.push(col); continue; }
    const cf = curatedByCol[tbl + "|" + col];
    if (cf) { if (!pushed.has(cf)) { newFields.push(cf); pushed.add(cf); } continue; }
    // synthesize by category
    const e = synth(tbl, col);
    if (e) newFields.push(e);
  }
  // one grouped system/audit card per table
  if (sysPresent.length) {
    newFields.push(entry(tbl, "system", sysPresent.join(", "),
      B("System / audit columns", "系统 / 审计列"),
      B("App/ETL-managed columns (not servicer-sourced).", "应用/ETL 管理列（非 servicer 来源）。"),
      [{ t: "bpms." + tbl, c: sysPresent.join(", "), rule: "BPS app/ETL managed", code: "asset" }],
      { servicer_audit: true,
        note: B("Columns: " + sysPresent.join(", ") + ". tenant_id ← GET_LOAN_TENANT_ID(portfunding ⋈ basic_data_trust_funding, asset:932-936); create_*/update_* set by the BPS app; is_deleted constant 0 (view); status app flag. Not servicer data.",
                "列：" + sysPresent.join(", ") + "。tenant_id ← GET_LOAN_TENANT_ID(portfunding ⋈ basic_data_trust_funding，asset:932-936)；create_*/update_* 由 BPS 应用写；is_deleted 视图恒 0；status 应用标志。非 servicer 数据。") }));
  }
}
// view_computed entry (doc 26)
newFields.push(entry("sync_loan_foreclosure", "view", "actual_* / var_* / target_total / actual_total",
  B("View-computed columns (Actual / Variance / Totals)", "视图计算列（Actual / Variance / 合计）"),
  B("The display view derives ~45 day-variance columns from the timeline dates + targets + nextduedate.", "展示视图基于 timeline 日期 + target + nextduedate 派生约 45 个天数差异列。"),
  [{ t: "bpms.biz_data_view_loan_details_foreclosure", c: "actual_<stage>_days / var_<stage>_days / target_total / actual_total / var_total", rule: "view-computed", code: "view" }],
  { sql: "actual_<stage>_days = to_days(timeline_<stage>_date) - to_days(nextduedate);\nvar_<stage>_days   = actual_<stage>_days - (cumulative target days up to that stage);\ntarget_total = Σ target_*; actual_total = Σ actual_*; var_total = Σ var_*",
    sql_note: B("Per milestone the view computes actual days (from next-due date) and variance vs the cumulative target; plus row totals. Targets use ifnull(target_X, <default>).",
                "视图对每个里程碑计算 actual 天数（自 next-due 日）与相对累计 target 的偏差；并给出行合计。target 用 ifnull(target_X, <默认>)。"),
    sql_eg: B("e.g. actual_first_legal_days = to_days(timeline_first_legal_date) - to_days(nextduedate); var_first_legal_days = that - (Σ targets through first legal).",
              "例：actual_first_legal_days = to_days(timeline_first_legal_date) - to_days(nextduedate)；var_first_legal_days = 该值 - (截至 first legal 的累计 target)。") }));

// ---- synthesizer ----
function synth(tbl, col) {
  // identity (all tables)
  if (col === "id") return entry(tbl, "identity", col, B("id (PK)", "id 主键"), B("Auto surrogate primary key.", "自增代理主键。"),
    [{ t: "bpms." + tbl, c: col, rule: "auto-increment PK (BPS app)", code: "asset" }], { note: B("Generated by the BPS app on insert; not from source.", "BPS 应用插入时生成；非来源数据。") });
  if (col === "loanid" || col === "svcloanid") {
    const raw = col === "loanid" ? "loanid" : "shellpointloanid";
    if (tbl === "sync_loan_foreclosure") return entry(tbl, "identity", col, B(col, col), B("Investor loan id / servicer loan id.", "投资人贷款 ID / servicer 贷款 ID。"), mainIdentityHops(col, raw, col === "loanid" ? "loanid" : "svc_loanid"));
    return entry(tbl, "identity", col, B(col, col), B("Investor loan id / servicer loan id.", "投资人贷款 ID / servicer 贷款 ID。"),
      [{ t: "newrez.portnewrezfc", c: raw, rule: "servicer raw" }, { t: "port." + PORT[tbl], c: col, rule: "passthrough" }, { t: "bpms." + tbl, c: col, rule: "sync passthrough", code: "asset" }]);
  }
  if (col === "servicer") return entry(tbl, "identity", col, B("servicer", "servicer 服务商"), B("Servicer name.", "服务商名。"),
    [{ t: "(per servicer)", c: "constant 'Newrez'/'Carrington'/'Capecodfive'", rule: "constant per UNION branch", code: "pool:1536/1577/1618" }, { t: "bpms." + tbl, c: col, rule: "sync passthrough", code: "asset" }]);
  if (col === "fctrdt") return entry(tbl, "identity", col, B("fctrdt", "fctrdt 报告快照日"), B("Daily snapshot/report date (=dataasof).", "每日快照/报告日（=dataasof）。"),
    [{ t: "port.basic_data_loan_fcl", c: "dataasof", rule: "dataasof → fctrdt" }, { t: "bpms." + tbl, c: col, rule: "sync passthrough", code: "asset" }]);
  if (col === "bid_id") return entry(tbl, "identity", col, B("bid_id (deal id)", "bid_id 交易ID"), B("Bridger deal id.", "Bridger deal id。"),
    [{ t: "port.portfunding", c: "dealid", rule: "join on loanid", code: "asset:541,604" }, { t: "bpms." + tbl, c: col, rule: "dealid → bid_id", code: "asset:541" }, { t: "bpms.biz_data_view_loan_details_foreclosure", c: col, rule: "passthrough", code: "view" }]);
  if (col === "funding_id") return entry(tbl, "identity", col, B("funding_id", "funding_id 资金ID"), B("Bridger funding id.", "Bridger funding id。"),
    [{ t: "port.portfunding", c: "fundingid", rule: "join on loanid", code: "asset:542,604" }, { t: "bpms." + tbl, c: col, rule: "fundingid → funding_id", code: "asset:542" }, { t: "bpms.biz_data_view_loan_details_foreclosure", c: col, rule: "passthrough", code: "view" }]);

  // sync_loan_foreclosure non-core business
  if (tbl === "sync_loan_foreclosure") {
    if (["timeline_notice_of_intent_end_date","timeline_approved_for_referral_date","timeline_referred_to_attorney_date","timeline_publication_date","timeline_foreclosure_completed_date"].includes(col))
      return entry(tbl, "milestone", col, B(col.replace(/_/g, " "), col), B("Reserved milestone; not populated by the FCL ETL.", "保留里程碑；FCL ETL 未填充。"),
        mainNullHops(col, "not in GEN_FCL_DETAIL INSERT → NULL 未填充"), { status: "null_in_build" });
    if (col.startsWith("target_"))
      return entry(tbl, "target", col, B(col, col), B("Target days for the milestone (config constant).", "该里程碑的目标天数（配置常量）。"),
        [{ t: "port.basic_data_loan_foreclosure", c: col, rule: "NULL (not populated)", code: "pool:174-188" }, { t: "bpms.sync_loan_foreclosure", c: col, rule: "GEN_FORECLOSURE: target_* commented out → NULL", code: "asset:564-577" }, { t: "bpms.biz_data_view_loan_details_foreclosure", c: col, rule: "ifnull(" + col + ", <default>) — view default constant", code: "view" }],
        { status: "view_default", note: B("Stored NULL in sync; the view supplies the default target (e.g. first_legal 120, service 90, judgement 30).", "sync 中存 NULL；视图给默认 target（如 first_legal 120、service 90、judgement 30）。") });
    if (["variance_active_bankruptcy","variance_completed_bankruptcy","variance_estimated_hold_days","variance_bankruptcies","bid_approval_status","bid_approval_sale_date","bid_approval_loan_resolution_holods","summary_servicer_number","summary_completed_foreclosure","summary_foreclosure_attorney"].includes(col))
      return entry(tbl, col.startsWith("variance") ? "variance" : col.startsWith("bid") ? "bid" : "summary", col, B(col, col), B("Defined in schema but not populated by the FCL ETL.", "Schema 中有，但 FCL ETL 未填充。"),
        mainNullHops(col, "not in GEN_FCL_DETAIL INSERT → NULL 未填充"), { status: "null_in_build" });
    if (col === "bid_approval_bid_amount" || col === "summary_srv_fc_bid_amount")
      return entry(tbl, col.startsWith("bid") ? "bid" : "summary", col, B(col, col), B("Foreclosure bid amount (same raw as summary_foreclosure_bid_amount).", "止赎竞价金额（与 summary_foreclosure_bid_amount 同源）。"),
        [{ t: "newrez.portnewrezfc", c: "fcbidamount", rule: "servicer raw" }, { t: "port.basic_data_loan_fcl", c: "fcbidamount", rule: "rename" }, { t: "port.basic_data_loan_foreclosure", c: col, rule: "= fcbidamount", code: col === "bid_approval_bid_amount" ? "pool:272" : "pool:275" }, { t: "bpms.sync_loan_foreclosure", c: col, rule: "passthrough", code: "asset" }, { t: "bpms.biz_data_view_loan_details_foreclosure", c: col, rule: "passthrough", code: "view" }]);
  }

  // sync_fcl_stage_info
  if (tbl === "sync_fcl_stage_info") {
    if (col === "stage") return entry(tbl, "stage_dim", col, B("stage (current bucket)", "stage 当前阶段分类"), B("The loan's current stage classification (waterfall outcome).", "贷款当前阶段分类（waterfall 结果）。"),
      [{ t: "port.basic_data_loan_fcl", c: "(stage dates)", rule: "waterfall by first non-null date" }, { t: "port.fcl_stage_info", c: "stage", rule: "CASE waterfall: SALE→JUDGEMENT→PUBLICATION→SERVICE→FIRST_LEGAL→REFERRAL→DEMAND", code: "pool:2095-2102" }, { t: "bpms.sync_fcl_stage_info", c: "stage", rule: "sync passthrough", code: "asset:925" }],
      { note: B("Values: SALE / JUDGEMENT / PUBLICATION / SERVICE / FIRST_LEGAL / REFERRAL / DEMAND (7; prod snapshot currently REFERRAL/SALE/FIRST_LEGAL/SERVICE/JUDGEMENT).", "取值：SALE / JUDGEMENT / PUBLICATION / SERVICE / FIRST_LEGAL / REFERRAL / DEMAND（7 个；prod 快照当前为 REFERRAL/SALE/FIRST_LEGAL/SERVICE/JUDGEMENT）。") });
    // stage prefix parsing
    const stages = ["demand","noi","referral","first_legal","service","publication","judgement","sale"];
    const rawByStage = { demand: "demandsentdate", referral: "fcreferraldate", first_legal: "firstlegaldate", service: "servicecompletedate", judgement: "fcjudgmenthearingscheduled", sale: "fcscheduledsaledate" };
    const factByStage = { demand: "demandsentdate", referral: "referral_start_date", first_legal: "legal_start_date", service: "service_start_date", judgement: "fcjudgment_hearing_scheduled", sale: "fcscheduled_sale_date" };
    for (const s of stages) {
      if (col === s + "_start_date") {
        if (s === "noi" || s === "publication") return stageNull(col, s);
        return entry(tbl, "stage_date", col, B(col, col), B("Stage start date.", "阶段开始日期。"),
          stageHops(col, rawByStage[s], factByStage[s], "passthrough start date", "pool:2354-2391"),
          { servicers: startServicers(s) });
      }
      if (col === s + "_end_date") return entry(tbl, "stage_date", col, B(col, col), B("Stage window end (= next stage start, else today).", "阶段窗口结束（= 下一阶段开始日，否则今天）。"),
        stageHops(col, "—", "(stage end)", "stage window end = next stage start / curr_date", "pool:2049-2076"), { status: (s==="noi"||s==="publication")?"null_in_build":undefined });
      if (col === s + "_stage_days") { if (s==="noi"||s==="publication") return stageNull(col, s);
        return withTpl(entry(tbl, "stage_days", col, B(col, col), B("Inclusive days elapsed in the stage.", "阶段内含端点已历天数。"), stageHops(col, "—", "(stage dates)", "datediff+1 (inclusive)", "pool:2040-2076")), stageTpl.stage_days, "stage_days"); }
      if (col === s + "_in_lm_days") return withTpl(entry(tbl, "stage_days", col, B(col, col), B("Days in the stage overlapping an open LM cycle.", "阶段内与开启 LM 周期重叠天数。"), stageHops(col, "—", "(LM cycle)", "interval overlap (LM)", "pool:2246-2330")), stageTpl.in_lm, "in_lm");
      if (col === s + "_on_hold_days") return withTpl(entry(tbl, "stage_days", col, B(col, col), B("Days in the stage overlapping an open hold.", "阶段内与开启 Hold 重叠天数。"), stageHops(col, "—", "fchold1..3", "interval overlap (Hold)", "pool:2215-2297")), stageTpl.on_hold, "on_hold");
    }
    if (col === "to_judgement_days" || col === "to_sale_days") return withTpl(entry(tbl, "stage_days", col, B(col, col), B("Forward countdown to the scheduled judgement/sale.", "距排定判决/拍卖的倒计天数。"), stageHops(col, col === "to_sale_days" ? "fcscheduledsaledate" : "fcjudgmenthearingscheduled", col === "to_sale_days" ? "fcscheduled_sale_date" : "fcjudgment_hearing_scheduled", "countdown (no +1, floored 0)", "pool:2085-2093")), stageTpl.to_days, "to_days");
    if (col === "first_legal_date_history") return entry(tbl, "stage_date", col, B(col, col), B("ETL first-seen tracking of the first-legal date.", "首次法律日的 ETL 首见追踪。"),
      stageHops(col, "firstlegaldate", "legal_start_date", "ETL tracking (first-seen)", "pool:2058-2066"));
  }
  // hold concrete columns (wide→long unpivot)
  if (tbl === "sync_loan_foreclosure_hold" && ["description", "description_start_date", "description_end_date"].includes(col)) {
    const slot = col === "description" ? "description" : col === "description_start_date" ? "startdate" : "enddate";
    const portc = col === "description" ? "description1..3" : "description1..3" + (col === "description_start_date" ? "_start_date" : "_end_date");
    const e = entry(tbl, "hold", col, B(col, col), B("Hold span " + col + " (Newrez wide slots → long rows).", "Hold 时段 " + col + "（Newrez 宽槽 → 长表行）。"),
      [{ t: "newrez.portnewrezfc", c: "fchold1..3 " + slot, rule: "servicer raw (wide slots) 原始" },
       { t: "port.basic_data_loan_foreclosure_hold", c: portc, rule: "slot assembly + dedup roll-up", code: "pool:744-768" },
       { t: "bpms.sync_loan_foreclosure_hold", c: col, rule: "UNION ALL wide→long unpivot", code: "asset:847-892" }],
      { servicers: { Newrez: "portnewrezfc.fchold1..3", Carrington: "portcarrington fchold4 slot", Capecodfive: "—" } });
    if (col === "description") {
      e.sql = "WITH hold_unpivot AS (\n  SELECT loanid, description1 AS description, description1_start_date AS s, description1_end_date AS e FROM ...hold WHERE description1<>''\n  UNION ALL SELECT loanid, description2, description2_start_date, description2_end_date ...\n  UNION ALL SELECT loanid, description3, description3_start_date, description3_end_date ...)\nSELECT loanid, description, s AS description_start_date, MAX(e) AS description_end_date GROUP BY loanid, description, s";
      e.sql_note = B("Newrez stores up to 3 hold slots wide; the sync UNION ALLs the non-empty slots into long rows, grouping by loanid+description+start_date and taking MAX(end_date).",
                     "Newrez 把最多 3 个 Hold 槽宽存；同步时把非空槽 UNION ALL 成长表行，按 loanid+description+start_date 分组取 MAX(end_date)。");
      e.sql_eg = B("7727004408: fchold1=('Court Delay',2026-03-24,2026-04-10) & fchold2=('Mediation Hearing',2026-04-28,2026-05-14) ⇒ 2 separate rows.",
                   "7727004408：fchold1=('Court Delay',2026-03-24,2026-04-10)、fchold2=('Mediation Hearing',2026-04-28,2026-05-14) ⇒ 2 行。");
    }
    return e;
  }
  // bankruptcy NULL-for-Newrez columns
  if (tbl === "sync_loan_foreclosure_bankruptcy" && ["lien_status", "mfr_status", "mfr_filed_date", "claim_status"].includes(col)) {
    return entry(tbl, "bk", col, B(col, col), B("Newrez: not populated (NULL). MFR fields are Carrington-only.", "Newrez 未填充（NULL）。MFR 字段仅 Carrington 有。"),
      [{ t: "newrez.portnewrezbk", c: "(none for Newrez)", rule: "—" },
       { t: "port.basic_data_loan_foreclosure_bankruptcy", c: col, rule: "null (Newrez) 常量空", code: "pool:358-361" },
       { t: "bpms.sync_loan_foreclosure_bankruptcy", c: col, rule: "GEN_FORECLOSURE_BK passthrough", code: "asset:832-835" }],
      { status: "newrez_null" });
  }
  // fallback: shouldn't happen
  return entry(tbl, "other", col, B(col, col), B("", ""), [{ t: "bpms." + tbl, c: col, rule: "(see code)", code: "" }]);
}
function stageHops(col, rawcol, factcol, rule, code) {
  const computed = !rawcol || rawcol === "—";
  return [
    { t: "newrez.portnewrezfc", c: computed ? "—" : rawcol, rule: computed ? "—" : "servicer raw 原始" },
    { t: "port.basic_data_loan_fcl", c: factcol, rule: "source 源" },
    { t: "port.fcl_stage_info", c: col, rule: rule + " 见 sql", code: code },
    { t: "bpms.sync_fcl_stage_info", c: col, rule: "sync passthrough", code: "asset:925" }
  ];
}
function stageNull(col, s) {
  return entry("sync_fcl_stage_info", "stage_date", col, B(col, col), B(s === "noi" ? "NOI bucket not populated separately (covered by DEMAND)." : "Publication not populated for these servicers.", s === "noi" ? "NOI 桶未单独填充（由 DEMAND 覆盖）。" : "Publication 对这些 servicer 未填充。"),
    [{ t: "port.fcl_stage_info", c: col, rule: "hardcoded NULL in business_1", code: "pool:2078-2102" }, { t: "bpms.sync_fcl_stage_info", c: col, rule: "sync passthrough (NULL)", code: "asset:925" }], { status: "null_in_build" });
}
function startServicers(s) {
  const m = {
    demand: { Newrez: "portnewrezfc.demandsentdate", Carrington: "—", Capecodfive: "—" },
    referral: { Newrez: "portnewrezfc.fcreferraldate", Carrington: "portcarrington.fcl_referral_date", Capecodfive: "portcapecodfive_monthly_collections.foreclosure_date_refrd_atty" },
    first_legal: { Newrez: "portnewrezfc.firstlegaldate", Carrington: "—", Capecodfive: "portcapecodfive_monthly_collections.foreclosure_first_legal_date" },
    service: { Newrez: "portnewrezfc.servicecompletedate", Carrington: "—", Capecodfive: "portcapecodfive_monthly_collections.foreclosure_service_date" },
    judgement: { Newrez: "portnewrezfc.fcjudgmenthearingscheduled", Carrington: "—", Capecodfive: "—" },
    sale: { Newrez: "portnewrezfc.fcscheduledsaledate", Carrington: "portcarrington.fcl_scheduled_sale_date", Capecodfive: "portcapecodfive_monthly_collections.foreclosure_date_sale_scheduled" }
  };
  return m[s];
}
function withTpl(e, tpl, kind) {
  if (tpl) { if (tpl.sql) e.sql = tpl.sql; if (tpl.sql_note) e.sql_note = tpl.sql_note; if (tpl.sql_eg) e.sql_eg = tpl.sql_eg; }
  return e;
}

J.fields = newFields;
fs.writeFileSync(P, JSON.stringify(J, null, 2) + "\n");
const by = {}; newFields.forEach(f => by[f.bps_table] = (by[f.bps_table] || 0) + 1);
console.log("total entries:", newFields.length, JSON.stringify(by));
