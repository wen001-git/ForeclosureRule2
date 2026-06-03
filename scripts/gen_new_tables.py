# -*- coding: utf-8 -*-
"""Generate markdown for foreclosure_data_dictionary.md 表20-表25 from MCP stats JSON.

业务含义/下游 由人工依据 doc 13 + 领域知识 curate（MEAN 字典）；
数据类型/取值范围/填充率/典型取值 全部来自 MCP 实测 JSON（不猜想）。
输出 outputs/new_tables.md。
"""
import json
from decimal import Decimal, InvalidOperation

with open("outputs/table_stats_for_data_dictionary.json", encoding="utf-8") as f:
    DATA = json.load(f)


def money(v):
    try:
        d = Decimal(v)
    except (InvalidOperation, ValueError):
        return v
    if d == d.to_integral_value():
        return f"${d:,.0f}"
    return f"${d:,.2f}"


def clean_num(v):
    try:
        d = Decimal(v)
    except (InvalidOperation, ValueError):
        return v
    if d == d.to_integral_value():
        return str(int(d))
    return f"{d.normalize()}"


def fillpct(s, snap):
    return f"{s['non_null']}/{snap}={round(s['non_null']/snap*100) if snap else 0}%"


def rng(s, money_cols=False, maxv=16):
    t = s["type"]
    d = s["distinct"]
    if d == 0:
        return "实测全为 NULL"
    if "top" in s:
        vals = [x["v"] for x in s["top"] if x["v"] != "None"][:maxv]
        if money_cols and t.startswith("decimal"):
            vals = [money(v) for v in vals]
            return "{" + ", ".join(vals) + f"}}（{d}种）"
        if t.startswith(("int", "bigint", "tinyint", "decimal")):
            vals = [clean_num(v) for v in vals]
            if d <= 12:
                return "{" + ", ".join(vals) + f"}}（{d}种）"
            return f"{clean_num(s['min'])} ~ {clean_num(s['max'])}（{d}种）"
        more = "" if d <= maxv else f" 等{d}种"
        return "{" + ", ".join(vals) + "}" + more
    if t.startswith(("date", "datetime")):
        return f"{s['min']} ~ {s['max']}"
    if t.startswith(("int", "bigint", "tinyint", "decimal")):
        if money_cols and t.startswith("decimal"):
            return f"{money(s['min'])} ~ {money(s['max'])}"
        return f"{clean_num(s['min'])} ~ {clean_num(s['max'])}"
    return f"文本，{d}种（样例 {s['min']} … {s['max']}）"


def typ(s, snap):
    nn = "NOT NULL" if s["nullable"] == "NO" else ""
    return (s["type"] + (" " + nn if nn else "")).strip()


def example(s):
    if s["distinct"] == 0:
        return "—"
    if "top" in s:
        for x in s["top"]:
            if x["v"] != "None":
                v = x["v"]
                if s["type"].startswith("decimal"):
                    return money(v)
                return v
    return s["min"]


def row(tk, col, meaning, src, calc, up, down, note, money_cols=False):
    s = DATA[tk]["columns"][col]
    snap = DATA[tk]["_snapshot_rows"]
    ex = example(s)
    note2 = (note + f"；填充 {fillpct(s, snap)}").lstrip("；")
    return (f"| `{col}` | {meaning} | {src} | {calc} | {typ(s, snap)} | "
            f"{rng(s, money_cols)} | {ex} | {up} | {down} | {note2} |")


HEADER = ("| 字段名 | 字段业务含义 | 来源数据 | 计算/推导逻辑 | 数据类型 | 取值范围 | 典型取值 | 上游字段 | 下游用途 | 备注 |\n"
          "|--------|-----------|--------|-----------|----------|---------|---------|--------|--------|------|")

OUT = []
def emit(*lines):
    OUT.extend(lines)


# ============ 表20: newrez.portnewrezbk (60列) ============
TK = "newrez.portnewrezbk"
SRC, CALC, UP = "Newrez 系统", "直接上报", "—"
D_BK = "下游 `sync_loan_foreclosure_bankruptcy`(表23) / BPS BK 面板"
# col: (meaning, down, note)
BK = {
 "id": ("MySQL 自增主键", "技术主键", "✅"),
 "loanid": ("Bridger/投资人贷款 ID", "按 `loanid+dataasof` 关联其他 Newrez 表", "✅"),
 "dataasof": ("数据快照日期", "每日报表日期", "✅"),
 "shellpointloanid": ("Newrez/Shellpoint 服务商贷款号", "下游 `svcloanid`", "✅"),
 "bkfileddate": ("破产申请日", "BK 时间线起点", "✅"),
 "bkstatus": ("破产状态编码（Newrez 内部数值码）", "解码后→ `bankruptcy_status`（表23）", "🟡 数值码，需字典解码"),
 "bkremovalcode": ("破产终止原因编码（1=Dismissed/2=Discharged 等）", "破产结案原因", "🟡 数值码"),
 "bkremovaldate": ("破产程序终止日", "→ `variance_completed_bankruptcy` 判定", "✅"),
 "bkchapter": ("破产章节（7=清算/11=重组/13=个人还款）", "→ `chapter`（表23）", "✅"),
 "bkcasenumber": ("破产案件编号", "案件追溯", "✅"),
 "bkpostpetitionduedate": ("破产申请后贷款应付日", "→ `post_petition_due_date`（表23）", "✅"),
 "prepetitionduedate": ("破产申请前贷款应付日", "Pre-petition 欠款基准", "✅"),
 "pocfileddate": ("债权申报（POC）提交日", "→ `proof_of_claim_date`（表23）", "✅"),
 "dischargeddate": ("债务免责（Discharge）日", "BK 完结情形之一", "✅"),
 "dismisseddate": ("破产驳回（Dismiss）日", "BK 完结情形之一；驳回后 FCL 可恢复", "✅"),
 "mfrfileddate": ("解除自动中止动议（MFR）提交日", "→ `mfr_filed_date`（表23）", "✅"),
 "mfrhearingdate": ("MFR 听证日", "MFR 子流程", "✅"),
 "mfrgranteddate": ("MFR 批准日（批准后可推进 FCL）", "MFR 子流程", "✅"),
 "trusteeassetflag": ("受托人资产标志（1=有可分配资产）", "Ch7 资产案件标识", "✅"),
 "trusteeassetdate": ("受托人资产认定日", "Ch7 子流程", "✅"),
 "planconfirmationdate": ("还款计划确认日（Ch13 Plan Confirmed）", "Ch13 子流程", "✅"),
 "bkstage": ("破产阶段编码（Newrez 内部数值码）", "解码后→ `legal_status`（表23）", "🟡 数值码，需字典解码"),
 "bkfirm": ("破产律师事务所名称", "律所信息", "✅"),
 "reaffirmationdate": ("重申债务确认（Reaffirmation）日", "Ch7 重申子流程", "✅"),
 "trusteeabandonmentdate": ("受托人放弃资产日", "Ch7 子流程", "✅"),
 "pocreferreddate": ("POC 转介日", "POC 子流程", "✅"),
 "pocbardate": ("POC 申报截止日（Bar Date）", "POC 截止节点", "✅"),
 "mfrreferred": ("MFR 转介日", "MFR 子流程", "✅"),
 "mfrhearingresults": ("MFR 听证结果编码", "解码后→ `mfr_status`（表23）", "🟡 数值码"),
 "cramdowndatereferred": ("Cramdown 转介日", "Cramdown 子流程", "✅"),
 "cramdownobjectionfileddate": ("Cramdown 异议提交日", "Cramdown 子流程", "✅"),
 "cramdownresultdate": ("Cramdown 结果日", "Cramdown 子流程", "✅"),
 "cramdownhearingresults": ("Cramdown 听证结果编码", "Cramdown 结果", "🟡 数值码"),
 "adversarialactionfileddate": ("对抗性诉讼（Adversary）提交日", "Adversary 子流程", "✅"),
 "adversarialhearingdate": ("对抗性诉讼听证日", "Adversary 子流程", "✅"),
 "adversarialresultdate": ("对抗性诉讼结果日", "Adversary 子流程", "✅"),
 "adversarialresults": ("对抗性诉讼结果编码", "Adversary 结果", "🟡 数值码"),
 "cramdownflag": ("Cramdown 标志（1=存在 cramdown）", "本金 cramdown 标识", "✅"),
 "bankruptcypaymenttype": ("破产还款类型编码", "还款类型细分", "🟡 数值码"),
 "debtorintention": ("债务人意向编码（保留/放弃房产）", "债务人意向", "🟡 数值码"),
 "jointfilerflag": ("是否共同申请人（1=joint）", "共同申请标识", "✅"),
 "activebkflag": ("是否在破产保护中（1=是/0=否）", "→ `variance_active_bankruptcy`；BK 活跃判定", "✅"),
 "apocfileddate": ("修订债权申报（APOC）提交日", "APOC 子流程", "✅"),
 "apocreferraldate": ("APOC 转介日", "APOC 子流程", "✅"),
 "reasonforapoc": ("APOC 原因（文本）", "APOC 原因说明", "✅"),
 "attorney": ("受理律师/律所名称", "律师信息（APOC 相关）", "✅"),
 "create_time": ("记录创建时间", "MySQL 管理字段（实测=落库时间）", "✅"),
 "update_time": ("记录更新时间", "MySQL 管理字段", "✅"),
 "bkrepayplanpaymentcount": ("破产还款计划期数", "Ch13 计划期数", "✅"),
 "bksourceoffundscode": ("资金来源编码", "还款资金来源", "🟡 数值码"),
 "bkpoccourtreceiveddate": ("POC 法院收到日", "POC 子流程", "✅"),
 "bkrcurrentstatusdate": ("当前破产状态生效日期", "→ `status_date`（表23）", "✅"),
 "bkborrowerintent": ("借款人破产意向编码", "借款人意向", "🟡 数值码"),
 "bkpostpetitionpaymentcurrent": ("破产后应付款当前额", "Post-petition 还款监控", "✅"),
 "bkcramdownpercent": ("Cramdown 比例（本金削减%）", "Cramdown 金额计算", "✅"),
 "bkpostsuspensebalance": ("破产后暂记款（suspense）余额", "暂记款监控", "✅"),
 "bkpresuspensebalance": ("破产前暂记款余额", "暂记款监控", "✅"),
 "investorloanid": ("投资人贷款号", "投资人对账 ID", "✅"),
 "bkfilingstate": ("破产申请州", "管辖州", "✅"),
 "bkfilingregion": ("破产申请法院辖区（含 Division）", "联邦破产法院辖区", "✅"),
}
emit("", "### 表 20：`newrez.portnewrezbk` — Newrez Bankruptcy 原始日报表", "",
     "| 属性 | 值 |", "|------|----|",
     "| **表名** | `portnewrezbk` |",
     "| **所属 Schema** | MySQL `newrez` |",
     "| **数据层** | Raw / Servicer-specific（Newrez/Shellpoint 原始 BK 日报落地表） |",
     "| **业务作用** | Newrez 破产全流程追踪表，含破产申请/章节/状态、MFR（解除中止动议）、POC（债权申报）、Cramdown、对抗性诉讼、受托人资产、还款计划确认及暂记款余额等子流程节点 |",
     "| **业务意图** | 作为 Newrez BK 原始事实表，识别贷款是否处于破产保护（破产会暂停 FCL），并为 BPS Bankruptcy 面板提供章节/状态/MFR/POC 等业务上下文 |",
     "| **上游来源** | Newrez/Shellpoint `Bankruptcy` / `AresOversight_Bankruptcy` 文件；映射见 `flow/basic_data/load_servicer_data_config/servicer_config.py` |",
     "| **下游使用** | Redshift 中间表（`WHERE LENGTH(TRIM(bkstatus))>0`，按 `loanid+bkfileddate` 去重最新快照）→ `bpms_dev.sync_loan_foreclosure_bankruptcy`（表23，`bkstatus`/`bkstage` 经 `portnewrezdatadic` 解码）；`activebkflag` 驱动主表 `variance_active_bankruptcy`（表17）；见 doc 13 §2.2 / §6 |",
     "| **Foreclosure 关系** | 间接但关键：活跃破产（`activebkflag=1`）触发 FCL Hold/暂停；破产 Dismiss/MFR Granted 后 FCL 通常恢复 |",
     "| **主键 / 索引** | `id` 自增主键；业务 join key 通常为 `loanid + dataasof`；BK 去重常按 `loanid + bkfileddate` |",
     "| **DB验证** | 2026-06-01 MySQL 实测：60列；全表 1,576,896 行；最新快照 `dataasof=2026-05-31` 共 5,052 行。取值范围/填充率取自最新快照（脚本 `scripts/extract_table_stats.py`） |", "",
     "> ⚠️ `bkstatus`/`bkstage`/`bkremovalcode`/`mfrhearingresults` 等为 **Newrez 内部数值编码**，下游写入 BPS 时经 `newrez.portnewrezdatadic` 解码为文本（见表23 与 doc 13 Q7）。最新快照中仅 32 笔有破产记录（`activebkflag` 等填充约 1%），属正常（多数活跃贷款无破产）。", "",
     "#### 字段说明（60列）", "", HEADER)
for c, (m, d, n) in BK.items():
    emit(row(TK, c, m, SRC, CALC, UP, d, n))


B = "BPS ETL"

# ============ 表21: sync_loan_foreclosure_hold (15列) ============
TK = "bpms_dev.sync_loan_foreclosure_hold"
HOLD = {
 "id": ("自增主键", B, "AUTO_INCREMENT", "—", "技术主键", "✅"),
 "loanid": ("系统贷款 ID", B, "直接写入", "`port.basic_data_loan_fcl.loanid`", "贷款 join key", "✅"),
 "svcloanid": ("Servicer 内部贷款号", B, "直接写入", "—", "Servicer 对账", "✅"),
 "fctrdt": ("数据来源批次日期", B, "直接写入", "—", "快照批次追踪", "✅"),
 "description": ("Hold 原因描述（文本）", B, "源 fchold1/2/3description（UNPIVOT）", "`newrez.portnewrezfc.fchold*description`", "BPS Hold 面板 Description 列", "✅"),
 "description_start_date": ("Hold 开始日", B, "源 fchold1/2/3startdate", "`newrez.portnewrezfc.fchold*startdate`", "Hold 面板 Start Date", "✅"),
 "description_end_date": ("Hold 结束日（NULL=仍持续）", B, "源 fchold1/2/3enddate", "`newrez.portnewrezfc.fchold*enddate`", "Hold 面板 End Date", "✅"),
 "create_user": ("记录创建用户", "BPS 应用层", "直接写入", "—", "审计追踪", "dev 未回填"),
 "create_dept": ("记录创建部门", "BPS 应用层", "直接写入", "—", "审计追踪", "dev 未回填"),
 "create_time": ("记录创建时间", "BPS 应用层", "直接写入", "—", "审计追踪", "dev 未回填"),
 "update_user": ("最后更新用户", "BPS 应用层", "直接写入", "—", "审计追踪", "dev 未回填"),
 "update_time": ("最后更新时间", "BPS 应用层", "直接写入", "—", "审计追踪", "dev 未回填"),
 "status": ("记录状态（0=正常）", "BPS 应用层", "DEFAULT 0", "—", "软停用标志", "✅"),
 "is_deleted": ("是否软删除（0=未删）", "BPS 应用层", "DEFAULT 0", "—", "软删除标志", "✅"),
 "tenant_id": ("租户 ID", "BPS 应用层", "直接写入", "—", "多租户支持", "✅"),
}
emit("", "---", "", "### 表 21：`bpms_dev.sync_loan_foreclosure_hold` — BPS Hold 历史记录表", "",
     "| 属性 | 值 |", "|------|----|",
     "| **表名** | `sync_loan_foreclosure_hold` |",
     "| **所属 Schema** | MySQL `bpms_dev`（BPS 应用数据库） |",
     "| **数据层** | Layer 5 — BPS Application Layer |",
     "| **业务作用** | 贷款 FCL 生命周期内的**完整 Hold 历史**（每次 Hold 变更追加一行），驱动 BPS Loan Foreclosure 详情页 Hold 面板 |",
     "| **业务意图** | Newrez `portnewrezfc` 仅保留 3 个当前 Hold 槽位（fchold1/2/3）；BPS 每日同步将每次变更落为新行，从而累积完整 Hold 历史（单贷款可远多于 3 行） |",
     "| **上游来源** | Redshift `port.basic_data_loan_foreclosure_hold`（源 `portnewrezfc`，`WHERE fchold1startdate IS NOT NULL`，3 槽 UNPIVOT，按 `loanid,description,start_date` 去重）→ `JOIN port.portfunding`；DELETE+INSERT 全量重写（见 doc 13 §4） |",
     "| **下游使用** | BPS Hold 面板（Description/Start/End）；入库链路与主 FCL 表独立（不要求 `fcreferraldate IS NOT NULL`） |",
     "| **Foreclosure 关系** | 直接：Hold（BK/LM/Court Delay 等）暂停 FCL 计时，是 SLA 方差分析的事件来源 |",
     "| **主键 / 索引** | `id` 自增主键；业务键 `loanid + description + description_start_date` |",
     "| **DB验证** | 2026-06-01 实测：15列；338 行（85 个 distinct svcloanid）；`description` 40 种文本（如 `Loss Mitigation Workout` / `Court Delay`）；脚本 `scripts/extract_table_stats.py` |", "",
     "> 说明：本表**不存储 Hold 预计结束日**；主表 `sync_loan_foreclosure.variance_estimated_hold_days` 的 projected 来源是 `portnewrezfc` 的 `fchold*projectedenddate`（见表17 与 doc 13 §4.4）。", "",
     "#### 字段说明（15列）", "", HEADER)
for c, (m, s, ca, u, d, n) in HOLD.items():
    emit(row(TK, c, m, s, ca, u, d, n))


# ============ 表22: sync_loan_foreclosure_loss_mitigation (22列) ============
TK = "bpms_dev.sync_loan_foreclosure_loss_mitigation"
LM = {
 "id": ("自增主键", B, "AUTO_INCREMENT", "—", "技术主键", "✅"),
 "loanid": ("系统贷款 ID", B, "直接写入", "`newrez.portnewrezlm.loanid`", "贷款 join key", "✅"),
 "svcloanid": ("Servicer 内部贷款号", B, "直接写入", "—", "Servicer 对账", "✅"),
 "fctrdt": ("数据来源批次日期", B, "直接写入", "—", "快照批次追踪", "✅"),
 "deal": ("LM 大类（解码文本）", B, "lmdeal(int) 经 portnewrezdatadic 解码", "`newrez.portnewrezlm.lmdeal`", "LM Cycle 面板 Deal 列", "✅ 解码存储（如 7→DIL）"),
 "program": ("LM 具体方案（解码文本）", B, "lmprogram(int) 解码", "`newrez.portnewrezlm.lmprogram`", "LM Cycle 面板 Program 列", "✅ 解码存储（如 10→Deed-in-Lieu）"),
 "lmc_status": ("LM 当前状态（解码文本）", B, "lmstatus(int) 解码", "`newrez.portnewrezlm.lmstatus`", "LM Cycle 面板 Status 列", "✅ 解码（如 166→Pending Financials）"),
 "cycle_opened_date": ("LM 周期开始日", B, "直接映射 dealstartdate", "`newrez.portnewrezlm.dealstartdate`", "LM 周期唯一键之一", "✅"),
 "cycle_closed_date": ("LM 周期结束日（NULL=进行中）", B, "直接映射 lmremovaldate", "`newrez.portnewrezlm.lmremovaldate`", "周期历时计算", "✅"),
 "final_disposition": ("最终处置结论（解码文本）", B, "lmdecision(int) 解码", "`newrez.portnewrezlm.lmdecision`", "决定 FCL 是否恢复（如 Referral to FC）", "✅ 解码存储"),
 "denialreason": ("拒绝原因（解码文本，无则空串）", B, "denialreason(int) 解码", "`newrez.portnewrezlm.denialreason`", "LM 拒绝原因", "✅ 无拒绝=空字符串"),
 "borrower_intentions": ("借款人意向（解码文本）", B, "borrowerintention(int) 解码", "`newrez.portnewrezlm.borrowerintention`", "借款人意向", "✅ Newrez 多为空"),
 "imminent_default": ("即将违约标识（CFPB Reg X）", B, "Newrez 无对应字段", "—", "LM Cycle 面板列", "✅ Newrez 恒 NULL（doc 13 Q6）"),
 "single_point_of_contact": ("专属联系人（CFPB 12 CFR 1024.40）", B, "Newrez 无对应字段", "—", "LM Cycle 面板列", "✅ Newrez 恒 NULL（doc 13 Q6）"),
 "create_user": ("记录创建用户", "BPS 应用层", "直接写入", "—", "审计追踪", "dev 未回填"),
 "create_dept": ("记录创建部门", "BPS 应用层", "直接写入", "—", "审计追踪", "dev 未回填"),
 "create_time": ("记录创建时间", "BPS 应用层", "直接写入", "—", "审计追踪", "dev 未回填"),
 "update_user": ("最后更新用户", "BPS 应用层", "直接写入", "—", "审计追踪", "dev 未回填"),
 "update_time": ("最后更新时间", "BPS 应用层", "直接写入", "—", "审计追踪", "dev 未回填"),
 "status": ("记录状态（0=正常）", "BPS 应用层", "DEFAULT 0", "—", "软停用标志", "✅"),
 "is_deleted": ("是否软删除（0=未删）", "BPS 应用层", "DEFAULT 0", "—", "软删除标志", "✅"),
 "tenant_id": ("租户 ID", "BPS 应用层", "直接写入", "—", "多租户支持", "✅"),
}
emit("", "---", "", "### 表 22：`bpms_dev.sync_loan_foreclosure_loss_mitigation` — BPS Loss Mitigation 周期表", "",
     "| 属性 | 值 |", "|------|----|",
     "| **表名** | `sync_loan_foreclosure_loss_mitigation` |",
     "| **所属 Schema** | MySQL `bpms_dev` |",
     "| **数据层** | Layer 5 — BPS Application Layer |",
     "| **业务作用** | 贷款完整 Loss Mitigation 周期历史（每个 LM 周期一行），驱动 BPS LM Cycle 面板 |",
     "| **业务意图** | 追踪每轮 workout（Evaluation→Modification/Forbearance/Short Sale/DIL）的开/关、方案与最终处置；LM 失败通常转回 FCL，成功则暂停/终止 FCL |",
     "| **上游来源** | Redshift（源 `newrez.portnewrezlm`，`WHERE dealstartdate IS NOT NULL`，按 `loanid,dealstartdate` 去重；6 个整型编码经 `portnewrezdatadic` 解码）→ `JOIN port.portfunding`；合并 Newrez+Carrington+Capecodfive（见 doc 13 §5） |",
     "| **下游使用** | BPS LM Cycle 面板（Deal/Program/Status/Cycle Dates/Final Disposition 等 10 列）；编码↔文本解码对照见表19「LM 编码解码参考」 |",
     "| **Foreclosure 关系** | 直接：LM 周期影响 FCL Hold/恢复；`final_disposition` 决定 FCL 是否继续 |",
     "| **主键 / 索引** | `id` 自增主键；业务键 `loanid + deal + cycle_opened_date` |",
     "| **DB验证** | 2026-06-01 实测：22列；544 行（250 个 distinct svcloanid）；`deal`/`program`/`lmc_status`/`final_disposition` 填充约 87%；脚本 `scripts/extract_table_stats.py` |", "",
     "> ⚠️ 本表存储**解码后业务文本**（与 Hold 表直接存文本不同；编码解码在 Redshift 层完成）。实测部分值仍为未解码数字（如 `deal='2.0'`、`lmc_status='166.0'`），属 ETL 字典缺失项，应以表19 解码参考为准。", "",
     "#### 字段说明（22列）", "", HEADER)
for c, (m, s, ca, u, d, n) in LM.items():
    emit(row(TK, c, m, s, ca, u, d, n))


# ============ 表23: sync_loan_foreclosure_bankruptcy (22列) ============
TK = "bpms_dev.sync_loan_foreclosure_bankruptcy"
BKC = {
 "id": ("自增主键", B, "AUTO_INCREMENT", "—", "技术主键", "✅"),
 "loanid": ("系统贷款 ID", B, "直接写入", "`newrez.portnewrezbk.loanid`", "贷款 join key", "✅"),
 "svcloanid": ("Servicer 内部贷款号", B, "直接写入", "—", "Servicer 对账", "✅"),
 "fctrdt": ("数据来源批次日期", B, "直接写入", "—", "快照批次追踪", "✅"),
 "bankruptcy_status": ("破产状态（解码文本）", B, "bkstatus(int) 经 portnewrezdatadic 解码", "`newrez.portnewrezbk.bkstatus`", "BK 面板 Status 列", "✅ 解码存储"),
 "legal_status": ("法律程序状态（解码文本）", B, "bkstage(int) 解码", "`newrez.portnewrezbk.bkstage`", "BK 面板 Legal Status 列", "✅ 解码（如 BK13/FCBU/REO）"),
 "status_date": ("当前状态生效日期", B, "直接映射 bkrcurrentstatusdate", "`newrez.portnewrezbk.bkrcurrentstatusdate`", "BK 面板 Status Date", "✅"),
 "chapter": ("破产章节（7/11/13）", B, "直接映射 bkchapter", "`newrez.portnewrezbk.bkchapter`", "BK 面板 Chapter", "✅"),
 "lien_status": ("留置权状态", B, "源待确认", "`newrez.portnewrezbk.*`", "BK 面板 Lien Status", "🟡 来源待确认；dev 全 NULL"),
 "mfr_status": ("MFR 状态（解码文本）", B, "mfrhearingresults(int) 解码", "`newrez.portnewrezbk.mfrhearingresults`", "BK 面板 MFR Status", "🟡 dev 全 NULL"),
 "mfr_filed_date": ("MFR 提交日", B, "直接映射 mfrfileddate", "`newrez.portnewrezbk.mfrfileddate`", "BK 面板 MFR Filed Date", "✅"),
 "claim_status": ("债权状态", B, "源待确认", "`newrez.portnewrezbk.*`", "BK 面板 Claim Status", "🟡 来源待确认；dev 全 NULL"),
 "proof_of_claim_date": ("债权申报（POC）日", B, "直接映射 pocfileddate", "`newrez.portnewrezbk.pocfileddate`", "BK 面板 Proof of Claim Date", "✅"),
 "post_petition_due_date": ("破产申请后应付日", B, "直接映射 bkpostpetitionduedate", "`newrez.portnewrezbk.bkpostpetitionduedate`", "BK 面板 Post Petition Due Date", "✅"),
 "create_user": ("记录创建用户", "BPS 应用层", "直接写入", "—", "审计追踪", "dev 未回填"),
 "create_dept": ("记录创建部门", "BPS 应用层", "直接写入", "—", "审计追踪", "dev 未回填"),
 "create_time": ("记录创建时间", "BPS 应用层", "直接写入", "—", "审计追踪", "dev 未回填"),
 "update_user": ("最后更新用户", "BPS 应用层", "直接写入", "—", "审计追踪", "dev 未回填"),
 "update_time": ("最后更新时间", "BPS 应用层", "直接写入", "—", "审计追踪", "dev 未回填"),
 "status": ("记录状态（0=正常）", "BPS 应用层", "DEFAULT 0", "—", "软停用标志", "✅"),
 "is_deleted": ("是否软删除（0=未删）", "BPS 应用层", "DEFAULT 0", "—", "软删除标志", "✅"),
 "tenant_id": ("租户 ID", "BPS 应用层", "直接写入", "—", "多租户支持", "✅"),
}
emit("", "---", "", "### 表 23：`bpms_dev.sync_loan_foreclosure_bankruptcy` — BPS Bankruptcy 记录表", "",
     "| 属性 | 值 |", "|------|----|",
     "| **表名** | `sync_loan_foreclosure_bankruptcy` |",
     "| **所属 Schema** | MySQL `bpms_dev` |",
     "| **数据层** | Layer 5 — BPS Application Layer |",
     "| **业务作用** | 贷款破产申请记录，驱动 BPS Bankruptcy 面板（仅有破产记录的贷款才有行） |",
     "| **业务意图** | 向资产经理展示破产章节/状态/MFR/POC 等关键节点；破产保护期间 FCL 暂停 |",
     "| **上游来源** | Redshift（源 `newrez.portnewrezbk`，`WHERE LENGTH(TRIM(bkstatus))>0`，按 `loanid,bkfileddate` 去重；`LEFT JOIN portnewrezgeneral` 取 legalstatus、`portnewrezdatadic` 解码 bkstatus）→ `JOIN port.portfunding`；合并 Newrez+Carrington+Capecodfive（见 doc 13 §6） |",
     "| **下游使用** | BPS Bankruptcy 面板（Status/Legal Status/Chapter/MFR/POC 等 10 列） |",
     "| **Foreclosure 关系** | 直接：上游 `activebkflag`/`bkremovaldate` 还驱动主表 `variance_active_bankruptcy`/`variance_completed_bankruptcy`（表17） |",
     "| **主键 / 索引** | `id` 自增主键；业务键 `loanid + bkfileddate` |",
     "| **DB验证** | 2026-06-01 实测：22列；64 行（59 个 distinct svcloanid）；`bankruptcy_status`/`chapter` 100% 填充，`legal_status` 48%；脚本 `scripts/extract_table_stats.py` |", "",
     "> ⚠️ `bankruptcy_status`/`legal_status` 实测多为已解码文本（Active/Discharged/Dismissed、BK13/BK7/REO 等），但仍混有少量未解码数字（如 `3.0`），属字典缺失项（doc 13 Q7）。`lien_status`/`mfr_status`/`claim_status` dev 全为 NULL，源字段待确认。", "",
     "#### 字段说明（22列）", "", HEADER)
for c, (m, s, ca, u, d, n) in BKC.items():
    emit(row(TK, c, m, s, ca, u, d, n))


# ============ 表24: sync_fcl_stage_info (57列) ============
TK = "bpms_dev.sync_fcl_stage_info"
SB = "BPS ETL（GEN_FCL_STAGE）"
PFX = {"demand": "NOI/Demand Letter", "noi": "NOI(Approved for Referral)", "referral": "Referral",
       "first_legal": "First Legal", "service": "Service", "publication": "Publication",
       "judgement": "Upcoming Judgement", "sale": "Upcoming FC Sales"}
def stage_meaning(col):
    for p, lab in PFX.items():
        if col.startswith(p + "_") or col == "to_" + ("judgement_days" if p == "judgement" else "sale_days") and p in ("judgement", "sale"):
            pass
    return None
STG = {
 "id": ("自增主键", "技术主键", "✅"),
 "stage": ("当前 FCL 阶段代码（全大写）", "BPS 聚合页分组键；瀑布优先级判定", "✅ {SALE,JUDGEMENT,SERVICE,FIRST_LEGAL,REFERRAL,DEMAND}"),
 "fctrdt": ("数据快照日（每贷款每天一行）", "查询当前态需 `fctrdt=MAX(fctrdt)`", "✅"),
 "loanid": ("系统贷款 ID", "贷款 join key", "✅"),
 "group": ("派生分类（FCL/REO/D120P/D90）", "聚合页分组/过滤", "✅ ETL 写入派生字段"),
 "servicer": ("Servicer 名称", "聚合页过滤", "✅"),
 "state": ("物业所在州", "聚合页过滤", "✅"),
 "judicial": ("是否司法州（Y/N）", "司法/非司法流程区分", "✅"),
 "first_legal_date_history": ("首次法律行动日变更历史", "First Legal 改期追溯", "🟡 dev 全 NULL"),
 "create_time": ("记录创建时间", "管理字段", "✅ 实测=同步批次时间"),
 "update_time": ("记录更新时间", "管理字段", "✅"),
 "create_user": ("记录创建用户", "审计追踪", "dev 未回填"),
 "create_dept": ("记录创建部门", "审计追踪", "dev 未回填"),
 "update_user": ("最后更新用户", "审计追踪", "dev 未回填"),
 "status": ("记录状态（0=正常）", "软停用标志", "✅"),
 "is_deleted": ("是否软删除（0=未删）", "软删除标志", "✅"),
 "tenant_id": ("租户 ID", "多租户支持", "✅"),
}
SUF = {"start_date": "阶段开始日", "end_date": "阶段结束日", "stage_days": "在该阶段已历天数",
       "in_lm_days": "该阶段内处于 LM 的天数", "on_hold_days": "该阶段内处于 Hold 的天数"}
def stg_meta(col):
    if col in STG:
        m, d, n = STG[col]
        calc = "直接写入" if col in ("id", "loanid", "fctrdt", "servicer", "state", "judicial") else "ETL 计算/派生"
        up = "`newrez.portnewrezfc.*`（经 `port.basic_data_loan_fcl`）" if col in ("state", "judicial") else "—"
        return m, SB, calc, up, d, n
    for p, lab in PFX.items():
        if col == "to_judgement_days":
            return "距判决日剩余天数", SB, "BPS 计算", "—", "Upcoming Judgement 组 Days to Judgement", "✅"
        if col == "to_sale_days":
            return "距拍卖日剩余天数", SB, "BPS 计算", "—", "Upcoming FC Sales 组 Days to Sale", "✅"
        if col.startswith(p + "_"):
            suf = col[len(p) + 1:]
            mean = f"{lab} 阶段 · {SUF.get(suf, suf)}"
            calc = "源 timeline 日期（经 basic_data_loan_fcl）" if suf in ("start_date", "end_date") else "BPS 结合 LM/Hold 状态计算"
            up = "`newrez.portnewrezfc` timeline" if suf in ("start_date", "end_date") else "`portnewrezlm.activelmflag` / Hold 状态"
            return mean, SB, calc, up, f"聚合页 {lab} 组", "✅"
    return col, SB, "ETL", "—", "—", "🟡"
emit("", "---", "", "### 表 24：`bpms_dev.sync_fcl_stage_info` — BPS FCL 阶段统计表", "",
     "| 属性 | 值 |", "|------|----|",
     "| **表名** | `sync_fcl_stage_info` |",
     "| **所属 Schema** | MySQL `bpms_dev` |",
     "| **数据层** | Layer 5 — BPS Application Layer（聚合概览页数据源） |",
     "| **业务作用** | 驱动 BPS Foreclosure 聚合概览页（Stage Tab + Time Line Tab）：按当前阶段分组的 Days in Stage / Days in LM / Days on Hold 统计，及各里程碑日期时间线 |",
     "| **业务意图** | 为资产经理提供组合级 FCL 进度与停滞监控；含主表 `sync_loan_foreclosure` 所缺的实际历时天数（`*_stage_days` 等） |",
     "| **上游来源** | Redshift `port.fcl_stage_info`（`GEN_FCL_STAGE`：主筛选 `activefcflag=1 AND fcremovaldate IS NULL`；次筛选 Demand 且 D90/D120P）→ `JOIN port.portfunding`（见 doc 13 §7） |",
     "| **下游使用** | BPS 聚合概览页 Stage Tab（阶段天数）与 Time Line Tab（里程碑日期）；`stage` 代码经前端映射为显示名 |",
     "| **Foreclosure 关系** | 核心：**唯一排除完结贷款**的 FCL 表（仅活跃 FCL），与主表 `sync_loan_foreclosure`（含完结）人口不同，数量不应直接比较 |",
     "| **主键 / 索引** | `id` 自增主键；业务键 `loanid + fctrdt`（每日快照） |",
     "| **DB验证** | 2026-06-01 实测：57列；5,825 行（56 个 distinct loanid × 多快照日）；`stage` 6 种代码；脚本 `scripts/extract_table_stats.py` |", "",
     "> 阶段字段按前缀分组（`demand_`/`noi_`/`referral_`/`first_legal_`/`service_`/`publication_`/`judgement_`/`sale_`），各组含 `*_start_date`/`*_end_date`/`*_stage_days`/`*_in_lm_days`/`*_on_hold_days`；Upcoming 组用 `to_judgement_days`/`to_sale_days` 替代 stage_days。`noi_*`/`publication_*` 对 Newrez 恒 NULL（见 doc 13 §7）。", "",
     "#### 字段说明（57列）", "", HEADER)
for c in DATA[TK]["columns"]:
    m, s, ca, u, d, n = stg_meta(c)
    emit(row(TK, c, m, s, ca, u, d, n))


# ============ 表25: biz_data_view_loan_details_foreclosure (104列, VIEW) ============
TK = "bpms_dev.biz_data_view_loan_details_foreclosure"
SV = "视图计算"
def view_meta(col):
    if col == "id":
        return "FCL 记录 ID（来自 loan_fcl）", SV, "`loan_fcl.id`", "表17 `id`", "贷款 FCL 关联", "✅"
    if col == "loanid":
        return "系统贷款 ID", SV, "`monthly.loanid`", "`sync_portmonth.loanid`", "视图主键", "✅"
    if col == "svcloanid":
        return "Servicer 内部贷款号", SV, "`monthly.svcloanid`", "`sync_portmonth`", "对账", "✅"
    if col == "fctrdt":
        return "数据快照日（月度）", SV, "`monthly.fctrdt`", "`sync_portmonth`", "时间维度", "✅"
    if col == "nextduedate":
        return "下次应还款日（DPD/历时计算锚点）", SV, "`monthly.nextduedate`", "`sync_portmonth`", "actual_*_days 计算基准", "✅ 100%"
    if col.startswith("timeline_"):
        return f"FCL 里程碑日期（同表17 `{col}`）", SV, f"取自 `loan_fcl.{col}`", f"表17 `{col}`", "Milestone Timeline 展示", "✅"
    if col.startswith("target_") and col.endswith("_days"):
        return f"SLA 目标天数（同表17 `{col}`）", SV, f"`IFNULL(loan_fcl.{col}, 默认值)`", f"表17 `{col}`", "Target 基准", "✅ 含 IFNULL 默认"
    if col == "actual_total":
        return "实际历时合计", SV, "Σ(actual_*_days)", "本视图 actual_*", "总历时", "✅ 任一分项 NULL 则为 NULL"
    if col == "target_total":
        return "目标天数合计", SV, "Σ(target_*_days)", "本视图 target_*", "总目标=637", "✅"
    if col == "var_total":
        return "总偏差合计", SV, "Σ(actual_* − target_*)", "本视图 var_*", "总 SLA 偏差", "✅ 任一分项 NULL 则为 NULL"
    if col.startswith("actual_") and col.endswith("_days"):
        base = col[len("actual_"):-len("_days")]
        return f"实际历时天数（{base}）", SV, f"`TO_DAYS(timeline_{base}_date) − TO_DAYS(nextduedate)`", "本视图 timeline + nextduedate", "Actual Days 展示", "✅ 视图实时计算"
    if col.startswith("var_") and col.endswith("_days"):
        base = col[len("var_"):-len("_days")]
        return f"SLA 偏差天数（{base}；正=超期）", SV, "`actual − 累计 target`", "本视图 actual_* − target_*", "Variance 展示", "✅ 视图实时计算"
    if col.startswith("variance_"):
        return f"同表17 `{col}`", SV, f"`loan_fcl.{col}`", f"表17 `{col}`", "BK 方差", "✅"
    if col.startswith("bid_approval_"):
        return f"同表17 `{col}`", SV, f"`loan_fcl.{col}`", f"表17 `{col}`", "Bid Approval 展示", "✅"
    if col.startswith("summary_"):
        return f"同表17 `{col}`", SV, f"`loan_fcl.{col}`", f"表17 `{col}`", "Summary 展示", "✅"
    if col in ("create_user", "create_dept", "create_time", "update_user", "update_time", "status", "tenant_id"):
        return f"管理字段（同表17 `{col}`）", SV, f"`loan_fcl.{col}`", f"表17 `{col}`", "审计/多租户", "✅"
    if col == "is_deleted":
        return "是否软删除", SV, "视图恒置 0", "—", "软删除标志", "✅ 视图硬编码 0"
    return col, SV, "视图字段", "—", "—", "🟡"
emit("", "---", "", "### 表 25：`bpms_dev.biz_data_view_loan_details_foreclosure` — BPS FCL 详情展示视图", "",
     "| 属性 | 值 |", "|------|----|",
     "| **表名** | `biz_data_view_loan_details_foreclosure`（**VIEW，非物理表**） |",
     "| **所属 Schema** | MySQL `bpms_dev` |",
     "| **数据层** | Layer 5 — BPS Application Layer（展示视图，最终展示口径） |",
     "| **业务作用** | BPS Loan Foreclosure 详情页最终数据视图：在主表 `sync_loan_foreclosure` 基础上，按 `nextduedate` 实时计算各阶段 `actual_*_days`、`var_*_days` 偏差及 total 汇总 |",
     "| **业务意图** | 将「目标 vs 实际 vs 偏差」三类天数指标在查询层一次性算出，避免落库；resolved actual/var 字段（如 `actual_judgement_hearing_set_days`）仅存在于本视图 |",
     "| **视图定义** | `sync_portmonth`(monthly) `LEFT JOIN sync_loan_foreclosure`(loan_fcl) ON `loanid+tenant_id`，再 LEFT JOIN 各 loanid 的 `MAX(fctrdt)` 子查询（取最新月度快照）。`actual_*_days = TO_DAYS(timeline_x) − TO_DAYS(nextduedate)`；`var_*_days = actual − 累计 target`（MCP `SHOW CREATE VIEW` 实测） |",
     "| **下游使用** | BPS 详情页 Milestone Timeline / Target / Actual / Variance 面板（含 doc 14 SQL-C3 验证的 `actual_judgement_hearing_set_days`） |",
     "| **Foreclosure 关系** | 核心展示层：FCL 时间线 + SLA 合规（actual vs target）一站式视图 |",
     "| **主键 / 索引** | 视图无主键；按 `loanid + fctrdt` 唯一 |",
     "| **DB验证** | 2026-06-01 实测：104列；122,550 行（基于 `sync_portmonth` 全量月度贷款，含非 FCL，故 timeline/summary 等填充率低）；脚本 `scripts/extract_table_stats.py` |", "",
     "> 列结构（104）：标识与锚点 5 + `timeline_*` 19 + `target_*_days` 15 + `actual_*_days` 15 + `variance_*` 4 + `bid_approval_*` 4 + `summary_*` 16 + 管理字段 8 + `var_*_days` 15 + 汇总 3（`var_total`/`target_total`/`actual_total`）。`target_*` 在视图中为 `bigint`（基表为 `int`）。填充率低因视图人口为全部月度贷款（122,550 行），非仅活跃 FCL。", "",
     "#### 字段说明（104列）", "", HEADER)
for c in DATA[TK]["columns"]:
    m, s, ca, u, d, n = view_meta(c)
    money_cols = "amount" in c
    emit(row(TK, c, m, s, ca, u, d, n, money_cols=money_cols))


with open("outputs/new_tables.md", "w", encoding="utf-8") as f:
    f.write("\n".join(OUT) + "\n")
print(f"wrote outputs/new_tables.md  ({len(OUT)} lines)")
