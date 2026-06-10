// One-time transform: clean `servicers` values to pure table.col / —, and add full `servicer_rule`.
// Run: node scripts/_clean_servicers.js   (idempotent)
const fs = require("fs");
const P = "outputs/fcl_lineage_source.json";
const J = JSON.parse(fs.readFileSync(P, "utf8"));

// 1) clean servicers values: "(computed…)"/"—(…)"/"x (…)" -> strip the parenthetical; pure source or —
function clean(v) {
  if (v == null) return v;
  v = v.trim();
  if (v.startsWith("(")) return "—";            // e.g. "(computed: …)"
  v = v.replace(/\s*\(.*\)\s*$/, "").trim();     // strip trailing " (…)"
  return v === "" ? "—" : v;
}
let cleaned = 0;
J.fields.forEach(f => {
  if (f.servicers) {
    ["Newrez", "Carrington", "Capecodfive"].forEach(k => {
      if (k in f.servicers) {
        const nv = clean(f.servicers[k]);
        if (nv !== f.servicers[k]) cleaned++;
        f.servicers[k] = nv;
      }
    });
  }
});

// 2) add full servicer_rule (bilingual) where Carrington/Capecodfive build differs from a plain rename
const RULE = {
  "Foreclosure Status": {
    en: "Inputs are built per servicer, then a shared CASE produces the text. **Newrez**: `activefcflag` (0/1) and `fcremovaldesc` taken directly. **Carrington**: no `activefcflag` column → `activefcflag = CASE WHEN fcl_flag='Active' THEN 1 ELSE NULL` (pool:1579); `fcremovaldesc` is NULL. **Capecodfive**: `activefcflag = CASE WHEN foreclosure_flag='Active' THEN 1 ELSE NULL` (pool:1620). **Shared rule**: `CASE WHEN activefcflag=1 THEN 'Active Foreclosure' WHEN activefcflag=0 AND fcremovaldesc<>'' THEN CONCAT('Closed Foreclosure:',fcremovaldesc) ELSE NULL` (pool:273).",
    zh: "各 servicer 先各自构建输入，再走同一个 CASE 生成文本。**Newrez**：直接取 `activefcflag`(0/1) 与 `fcremovaldesc`。**Carrington**：无 `activefcflag` 列 → `activefcflag = CASE WHEN fcl_flag='Active' THEN 1 ELSE NULL`（pool:1579）；`fcremovaldesc` 为 NULL。**Capecodfive**：`activefcflag = CASE WHEN foreclosure_flag='Active' THEN 1 ELSE NULL`（pool:1620）。**共用规则**：`CASE WHEN activefcflag=1 THEN 'Active Foreclosure' WHEN activefcflag=0 AND fcremovaldesc<>'' THEN CONCAT('Closed Foreclosure:',fcremovaldesc) ELSE NULL`（pool:273）。"
  },
  "Days in Foreclosure": {
    en: "**Newrez**: raw `daysinfc` passed through (pool:1546). **Carrington / Capecodfive**: no raw `daysinfc` → computed `CASE WHEN <active> THEN datediff(day, referral_start_date, <snapshot>)+1 ELSE NULL` (Carrington uses snap_shot_date, pool:1587; Capecodfive uses dataasof, pool:1628). Downstream the view shows the lag-corrected value; see the per-hop rule.",
    zh: "**Newrez**：原始 `daysinfc` 直传（pool:1546）。**Carrington / Capecodfive**：无原始 `daysinfc` → 计算 `CASE WHEN <active> THEN datediff(day, referral_start_date, <快照日>)+1 ELSE NULL`（Carrington 用 snap_shot_date，pool:1587；Capecodfive 用 dataasof，pool:1628）。下游视图显示延迟校正值，详见逐跳规则。"
  },
  "Judicial (Y/N)": {
    en: "`fcl_stage_info.judicial = CASE judicial=1→'Y', 0→'N'`. **Newrez** supplies the loan-level `judicial` flag (pool:1565). **Carrington / Capecodfive** have `judicial=NULL` in the fact (pool:1606 / 1647) → **state fallback**: join `basic_data_judicial_config` on the property state and use its judicial value (pool:2351-2353, join pool:2432).",
    zh: "`fcl_stage_info.judicial = CASE judicial=1→'Y'、0→'N'`。**Newrez** 提供贷款级 `judicial` 标志（pool:1565）。**Carrington / Capecodfive** 事实表中 `judicial=NULL`（pool:1606 / 1647）→ **州级回退**：按房产州关联 `basic_data_judicial_config`，取其 judicial 值（pool:2351-2353，关联 pool:2432）。"
  },
  "Group (FCL/D120P/D90/REO/P…)": {
    en: "`fcl_stage_info.group = basic_data_fcl_related.delq_status`. **Newrez** (pool:1702-1711): if `delinquency_status_mba='Full Payoff'`→P, `'REO'`→REO, any `'Foreclosure*'`→FCL; otherwise bucket by `days360(portnewrezpmt.nextduedate, dataasof)`: `<30`→C, `<60`→D30, `<90`→D60, `<120`→D90, else→D120P. **Carrington** (pool:1749-1758): if `loan_status='Foreclosure' OR fcl_flag='Active'`→FCL, `loan_status IN ('R','REO')`→REO, `IN ('Completed Payoff','Completed Short Sale')`→P; otherwise the same `days360` buckets on `date_payment_due`. **Capecodfive** is not in `basic_data_fcl_related` → group is `—`.",
    zh: "`fcl_stage_info.group = basic_data_fcl_related.delq_status`。**Newrez**（pool:1702-1711）：`delinquency_status_mba='Full Payoff'`→P、`'REO'`→REO、任意 `'Foreclosure*'`→FCL；否则按 `days360(portnewrezpmt.nextduedate, dataasof)` 分桶：`<30`→C、`<60`→D30、`<90`→D60、`<120`→D90、否则→D120P。**Carrington**（pool:1749-1758）：`loan_status='Foreclosure' 或 fcl_flag='Active'`→FCL、`loan_status IN ('R','REO')`→REO、`IN ('Completed Payoff','Completed Short Sale')`→P；否则对 `date_payment_due` 用同样的 `days360` 分桶。**Capecodfive** 不在 `basic_data_fcl_related` → group 为 `—`。"
  }
};
let ruled = 0;
J.fields.forEach(f => {
  const lab = f.label && f.label.en;
  if (RULE[lab]) { f.servicer_rule = RULE[lab]; ruled++; }
});
Object.keys(RULE).forEach(k => { if (!J.fields.some(f => f.label && f.label.en === k)) console.log("WARN unmatched RULE key:", k); });
fs.writeFileSync(P, JSON.stringify(J, null, 2) + "\n");
console.log("servicers cells cleaned:", cleaned, "| servicer_rule added:", ruled);
