// One-time transform: add bilingual `sql_note` (explanation) + `sql_eg` (worked example) to every
// field that has a `sql` block; fix the Type CASE sql. Examples are MCP-grounded (prod).
// Run: node scripts/_add_sql_docs.js   (idempotent)
const fs = require("fs");
const P = "outputs/fcl_lineage_source.json";
const J = JSON.parse(fs.readFileSync(P, "utf8"));

// fix Type CASE (dropped cast in transcription)
const FIX_SQL = {
  "Type (Judicial / Non Judicial)": "CASE WHEN judicial IS NULL OR judicial='' THEN null WHEN cast(cast(judicial AS float) as int)=0 THEN 'Non Judicial' WHEN cast(cast(judicial AS float) as int)=1 THEN 'Judicial' ELSE null END"
};

// keyed by label.en: [note_en, note_zh, eg_en, eg_zh]
const M = {
  "Judgement Hearing Set": [
    "Tracks WHEN the current scheduled-hearing value first appeared: group the loan's daily snapshots by (loanid, fcjudgment_hearing_scheduled) and take MIN(dataasof). So it is the date that hearing date was first set — not the hearing date itself.",
    "追踪「当前听证日期值」首次出现的日期：按 (loanid, fcjudgment_hearing_scheduled) 分组取 MIN(dataasof)。即该听证日被首次设定之日，而非听证日本身。",
    "Loan 7727004408: the hearing date 2026-08-21 first appears in the 2026-05-14 snapshot ⇒ timeline_judgement_hearing_set_date = 2026-05-14 (while Judgement = 2026-08-21).",
    "贷款 7727004408：听证日 2026-08-21 在 2026-05-14 的快照首次出现 ⇒ timeline_judgement_hearing_set_date = 2026-05-14（而 Judgement = 2026-08-21）。"],
  "Sale Date Set": [
    "Same first-seen logic as Hearing Set, for the scheduled-sale date: MIN(dataasof) over (loanid, fcscheduled_sale_date). The date the current sale date was first scheduled.",
    "与 Hearing Set 同理，针对排定拍卖日：按 (loanid, fcscheduled_sale_date) 取 MIN(dataasof)。即当前拍卖日被首次排定之日。",
    "e.g. if a loan's scheduled sale 2026-06-23 first appears on the 2026-03-10 snapshot ⇒ timeline_sale_date_set_date = 2026-03-10 (Sale Date Projected stays 2026-06-23).",
    "例：某贷款排定拍卖日 2026-06-23 在 2026-03-10 快照首次出现 ⇒ timeline_sale_date_set_date = 2026-03-10（Sale Date Projected 仍为 2026-06-23）。"],
  "Foreclosure Status": [
    "activefcflag=1 ⇒ fixed text 'Active Foreclosure'. activefcflag=0 AND fcremovaldesc non-empty ⇒ 'Closed Foreclosure:'+fcremovaldesc (the exit reason). Otherwise NULL. (Note: the closed text uses fcremovaldesc, NOT fcstage.)",
    "activefcflag=1 ⇒ 固定文本 'Active Foreclosure'。activefcflag=0 且 fcremovaldesc 非空 ⇒ 'Closed Foreclosure:'+fcremovaldesc（退出原因）。否则 NULL。（注意：关闭文本取 fcremovaldesc，非 fcstage。）",
    "7727004408: activefcflag=1 ⇒ 'Active Foreclosure'. A closed loan with activefcflag=0, fcremovaldesc='Paid in Full' ⇒ 'Closed Foreclosure:Paid in Full'.",
    "7727004408：activefcflag=1 ⇒ 'Active Foreclosure'。已关闭贷款 activefcflag=0、fcremovaldesc='Paid in Full' ⇒ 'Closed Foreclosure:Paid in Full'。"],
  "Type (Judicial / Non Judicial)": [
    "Normalize the judicial flag: NULL/blank ⇒ NULL; otherwise cast text→float→int, then 0 ⇒ 'Non Judicial', 1 ⇒ 'Judicial'.",
    "归一化 judicial 标志：NULL/空 ⇒ NULL；否则 文本→float→int，0 ⇒ 'Non Judicial'，1 ⇒ 'Judicial'。",
    "judicial='1' ⇒ 'Judicial' (7727004408); '0' ⇒ 'Non Judicial'; '' ⇒ NULL.",
    "judicial='1' ⇒ 'Judicial'（7727004408）；'0' ⇒ 'Non Judicial'；'' ⇒ NULL。"],
  "Group (FCL/D120P/D90/REO/P…)": [
    "delq_status (carried into fcl_stage_info.group): if delinquency_status_mba is 'Full Payoff'→P, 'REO'→REO, any 'Foreclosure*'→FCL; otherwise bucket by days360(nextduedate, dataasof): <30→C, <60→D30, <90→D60, <120→D90, else→D120P.",
    "delq_status（带入 fcl_stage_info.group）：delinquency_status_mba 为 'Full Payoff'→P、'REO'→REO、任意 'Foreclosure*'→FCL；否则按 days360(nextduedate, dataasof) 分桶：<30→C、<60→D30、<90→D60、<120→D90、否则→D120P。",
    "7727004408: delinquency_status_mba='Foreclosure' ⇒ FCL. (Delinquency path, illustrative: nextduedate ~100 days before dataasof ⇒ days360≈100 ⇒ D90.)",
    "7727004408：delinquency_status_mba='Foreclosure' ⇒ FCL。（逾期路径，示意：nextduedate 距 dataasof 约 100 天 ⇒ days360≈100 ⇒ D90。）"],
  "Judicial (Y/N)": [
    "From the normalized loan-level judicial: 1→'Y', 0→'N'. If NULL/blank, fall back to the state-level judicial config (basic_data_judicial_config keyed by property state).",
    "由归一化的贷款级 judicial：1→'Y'、0→'N'。若 NULL/空，则回退到州级司法配置（basic_data_judicial_config 按房产州关联）。",
    "judicial=1 ⇒ 'Y'. A loan with no flag in a judicial state (e.g. FL) ⇒ config 'Y'; in a non-judicial state (e.g. TX) ⇒ 'N'.",
    "judicial=1 ⇒ 'Y'。无标志的贷款在司法州（如 FL）⇒ 配置 'Y'；在非司法州（如 TX）⇒ 'N'。"],
  "{stage}_stage_days (elapsed in stage)": [
    "Inclusive days in the stage: datediff(day, {stage}_start, end)+1, where end = the next stage's start (referral_end=first-legal start; first_legal_end=service start; service_end=judgement-available), or today (curr_date) if the stage hasn't ended.",
    "阶段内含端点天数：datediff(day, {stage}_start, end)+1，其中 end = 下一阶段开始日（referral_end=首次法律日；first_legal_end=送达日；service_end=判决可得日），若未结束则取今天 curr_date。",
    "7727004408: referral_start 2024-03-08, next stage (first legal) 2025-07-28 ⇒ referral_stage_days = datediff+1 = 508 (matches prod).",
    "7727004408：referral_start 2024-03-08，下一阶段（首次法律）2025-07-28 ⇒ referral_stage_days = datediff+1 = 508（与 prod 一致）。"],
  "to_sale_days / to_judgement_days (countdown)": [
    "Forward countdown to the scheduled date: NULL date→NULL; if date ≥ today → datediff(today, date) (NO +1); if already past → 0.",
    "距排定日的倒计天数：日期为 NULL→NULL；日期 ≥ 今天 → datediff(今天, 日期)（不 +1）；已过期 → 0。",
    "7727001179: scheduled sale 2026-06-23 ⇒ to_sale_days = 15 (countdown from the snapshot date).",
    "7727001179：排定拍卖 2026-06-23 ⇒ to_sale_days = 15（自快照日倒计）。"],
  "{stage}_in_lm_days": [
    "Days of the stage window overlapping an OPEN loss-mitigation cycle: datediff(greatest(stage_start, cycle_opened), least(stage_end, coalesce(cycle_closed, today)))+1; only open cycles; computed per stage then max().",
    "阶段窗口与「进行中」LM 周期的重叠天数：datediff(greatest(stage_start, cycle_opened), least(stage_end, coalesce(cycle_closed, 今天)))+1；仅开启周期；按阶段计算后取 max()。",
    "7727000569: the Service stage overlaps an open LM cycle ⇒ service_in_lm_days = 185 (prod).",
    "7727000569：Service 阶段与开启 LM 周期重叠 ⇒ service_in_lm_days = 185（prod）。"],
  "{stage}_on_hold_days": [
    "Days of the stage window overlapping an OPEN hold (fchold1..3 of basic_data_loan_fcl): datediff(greatest(stage_start, hold_start), least(stage_end, coalesce(hold_end, today)))+1; per stage then max().",
    "阶段窗口与「进行中」Hold（basic_data_loan_fcl 的 fchold1..3）的重叠天数：datediff(greatest(stage_start, hold_start), least(stage_end, coalesce(hold_end, 今天)))+1；按阶段后取 max()。",
    "7727000569: the Service stage ∩ an open hold ⇒ service_on_hold_days = 87 (prod).",
    "7727000569：Service 阶段 ∩ 开启 Hold ⇒ service_on_hold_days = 87（prod）。"],
  "Description / Start / End (unpivot)": [
    "Newrez stores up to 3 hold slots wide (fchold1..3 description/start/end). The sync UNION ALLs the non-empty slots into long rows (description, description_start_date, description_end_date), grouping by loanid+description+start_date and taking MAX(end_date).",
    "Newrez 把最多 3 个 Hold 槽宽存（fchold1..3 description/start/end）。同步时把非空槽 UNION ALL 成长表行（description, description_start_date, description_end_date），按 loanid+description+start_date 分组取 MAX(end_date)。",
    "7727004408 wide → long: fchold1=('Court Delay',2026-03-24,2026-04-10) and fchold2=('Mediation Hearing',2026-04-28,2026-05-14) ⇒ 2 separate rows in sync_loan_foreclosure_hold.",
    "7727004408 宽转长：fchold1=('Court Delay',2026-03-24,2026-04-10)、fchold2=('Mediation Hearing',2026-04-28,2026-05-14) ⇒ sync_loan_foreclosure_hold 中 2 行。"],
  // --- LM / BK datadic decode (shared pattern, field-specific field_name + example) ---
  "Deal": [
    "Integer code → text via newrez.portnewrezdatadic (field_name='LMDeal'). Codes are stored as 'N.0', so the join key is concat(code,'.0'); COALESCE falls back to the raw code if no dictionary match.",
    "整数码经 newrez.portnewrezdatadic（field_name='LMDeal'）解码为文本。码以 'N.0' 存储，故连接键为 concat(code,'.0')；字典无匹配时 COALESCE 回退原始码。",
    "7727004408: lmdeal=2 ⇒ deal='Evaluation'.",
    "7727004408：lmdeal=2 ⇒ deal='Evaluation'。"],
  "Program": [
    "Same datadic decode pattern, field_name='LMProgram' (join concat(code,'.0'); fallback to raw).",
    "同 datadic 解码模式，field_name='LMProgram'（连接 concat(code,'.0')；回退原始码）。",
    "7727004408: lmprogram=21 ⇒ program='Evaluation'.",
    "7727004408：lmprogram=21 ⇒ program='Evaluation'。"],
  "Status": [
    "Same datadic decode pattern, field_name='LMStatus' (join concat(code,'.0'); fallback to raw).",
    "同 datadic 解码模式，field_name='LMStatus'（连接 concat(code,'.0')；回退原始码）。",
    "7727004408: lmstatus=166 ⇒ lmc_status='Pending Financials'.",
    "7727004408：lmstatus=166 ⇒ lmc_status='Pending Financials'。"],
  "Final Disposition": [
    "Same datadic decode pattern, field_name='LMDecision' (join concat(code,'.0'); fallback to raw).",
    "同 datadic 解码模式，field_name='LMDecision'（连接 concat(code,'.0')；回退原始码）。",
    "7727004408: lmdecision=99 ⇒ final_disposition='Pending'.",
    "7727004408：lmdecision=99 ⇒ final_disposition='Pending'。"],
  "Denial / Reason": [
    "Same datadic decode pattern, field_name='DenialReason' (join concat(code,'.0'); fallback to raw).",
    "同 datadic 解码模式，field_name='DenialReason'（连接 concat(code,'.0')；回退原始码）。",
    "7727004408 (Short Sale cycle): denialreason=78 ⇒ 'Buyer walked (SS)'.",
    "7727004408（Short Sale 周期）：denialreason=78 ⇒ 'Buyer walked (SS)'。"],
  "Borrower Intentions": [
    "Same datadic decode pattern, field_name='BorrowerIntention' (join concat(code,'.0'); fallback to raw). Note raw col is borrowerintention (singular) → output borrower_intentions (plural).",
    "同 datadic 解码模式，field_name='BorrowerIntention'（连接 concat(code,'.0')；回退原始码）。注意原始列 borrowerintention（单数）→ 输出 borrower_intentions（复数）。",
    "7727004408 (Short Sale cycle): borrowerintention=3 ⇒ 'Disposition'.",
    "7727004408（Short Sale 周期）：borrowerintention=3 ⇒ 'Disposition'。"],
  "Bankruptcy Status": [
    "Integer code → text via datadic (field_name='BKStatus'; join concat(code,'.0'); fallback to raw). Decode map: 1→Active, 2→Discharged, 3→Dismissed, 4→Closed, 5→ReliefGranted.",
    "整数码经 datadic（field_name='BKStatus'；连接 concat(code,'.0')；回退原始码）解码。解码表：1→Active、2→Discharged、3→Dismissed、4→Closed、5→ReliefGranted。",
    "Loan 7727000010: bkstatus=1 ⇒ bankruptcy_status='Active'.",
    "贷款 7727000010：bkstatus=1 ⇒ bankruptcy_status='Active'。"]
};

let fixed = 0, annotated = 0, miss = [];
J.fields.forEach(f => {
  const lab = f.label && f.label.en;
  if (FIX_SQL[lab]) { f.sql = FIX_SQL[lab]; fixed++; }
  if (f.sql && M[lab]) {
    const [ne, nz, ee, ez] = M[lab];
    f.sql_note = { en: ne, zh: nz };
    f.sql_eg = { en: ee, zh: ez };
    annotated++;
  }
});
J.fields.forEach(f => { if (f.sql && !f.sql_note) miss.push(f.label.en); });
Object.keys(M).forEach(k => { if (!J.fields.some(f => f.label && f.label.en === k && f.sql)) miss.push("UNMATCHED:" + k); });
fs.writeFileSync(P, JSON.stringify(J, null, 2) + "\n");
console.log("type-case fixed:", fixed, "| annotated:", annotated, "| sql w/o note OR unmatched:", miss.length ? miss : "none");
