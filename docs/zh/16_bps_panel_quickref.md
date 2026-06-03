# doc 16 — BPS Foreclosure 面板速查

---

## 文档目的

- **为什么存在**：doc 13 是完整的字段逆向映射文档（按字段类型分组，共 22+ 小节）。本文是其"速查入口"——以 BPS 界面面板为单位，每个面板附截图 + 紧凑的三列映射表，让运营/开发人员在 BPS 界面看到异常字段时，无需通读 doc 13 即可立刻定位源数据。
- **解决的问题**：BPS 界面截图 → Newrez 源字段的直接对应；字段名、Mapping Rule 一屏呈现。
- **范围**：BPS Foreclosure 详情页的 6 个面板 + 聚合概览页；仅覆盖 Newrez Servicer；详细逻辑见 doc 13。
- **系统关系**：本文是 doc 13 的精简速查版。发现数据异常时先查本文定位面板/字段，再跳转 doc 13 对应小节深入分析。

## 目标读者

主要：运营分析师 · BPS 系统验收人员 · 数据质量工程师  
次要：新成员快速上手 · 未来 AI Session

## 修订历史

| 日期 | 作者 | 版本 | 变更 | 关联 |
|------|------|------|------|------|
| 2026-06-03 | AI Agent（Claude Opus 4.8） | v2 | SMS Days / Days in Foreclosure 行补起算基准（代码+DB 核实）：SMS Days 自 fcsetupdate(servicer 建案日)、Days 自 fcreferraldate(转介日)，故 SMS Days ≤ Days；同步 doc 13/14/16xlsx/fcl_pipeline.html | doc 13 v34 · doc 14 v31 |
| 2026-05-28 | AI Agent（Claude Sonnet 4.6） | v1 | 初稿：6个面板速查表 + 截图；内容来自 doc 13 MCP 实测数据 | doc 13 |

## 相关文档

| 文档 | 说明 |
|------|------|
| doc 13 | Newrez FCL 字段完整逆向映射（本文数据来源） |
| doc 14 | BPS 驱动的 Servicer 数据接口规范 |

---

## 使用方法

1. 找到 BPS 界面上异常的**面板名称**，跳转到对应 Section
2. 在表格中找到**UI 标签**，查看 Newrez 源字段和 Mapping Rule
3. 如需完整业务含义、填充率、验证 SQL，跳转 doc 13 对应小节

---

## Section 1：Foreclosure Summary 面板

> **BPS 数据库来源**：`bpms_dev.sync_loan_foreclosure`（`summary_*` 字段）  
> **Newrez 来源表**：`newrez.portnewrezfc`  
> **doc 13 对应小节**：Section 3.7

### 界面截图

![Foreclosure Summary 面板（loanid=7727000088）](image/image-20260528-bps-foreclosure-summary-panel.png)

### 字段映射

| UI 标签 | Newrez 源字段 | Mapping Rule |
|---|---|---|
| Foreclosure status | `fcstage` / `fcresults` / `fcremovaldesc` | `activefcflag=1` → 取 `fcstage`（进行中阶段文本）；`activefcflag=0` → 取 `fcresults` 或 `fcremovaldesc` |
| Foreclosure bid amount | `fcbidamount` | 直接取值（活跃 FCL 约 9% 填充） |
| Foreclosure sale amount | `fcsaleamount` | 直接取值（4.7%；⚠️ 高于拍卖完成率 2.1%，见 doc 13 Q9） |
| Contested / Litigation | `fccontestedflag` | 直接取值（1=有争议 / 0=无） |
| Firm | `fcfirm` | 直接取值（律师事务所全名） |
| Type | `judicial` | `judicial=1` → `'Judicial'`；`judicial=0` → `'Non-Judicial'` |
| SMS Days in Foreclosure | `smsdaysinfc`(=svc_days_infc) + `dataasof` | Servicer(SMS=Shellpoint)口径，自**建案日 fcsetupdate** 起算（Newrez 原生透传）；**实时重算**：`smsdaysinfc + DATEDIFF(今日NY, dataasof)`；≤ Days in Foreclosure |
| Days in Foreclosure | `daysinfc` + `dataasof` | 投资人/全程口径，自**转介日 fcreferraldate** 起算；**实时重算**：`daysinfc + DATEDIFF(今日NY, dataasof)`；≥ SMS Days |
| Current Step | `currentmilestone` / `fcstage` | `currentmilestone` 非空则优先取；否则取 `fcstage` |
| Last Step Completed | `lastfcstepcompleted` | 直接取值（99.5% 填充） |
| Last Step Completed Date | `lastfcstepcompleteddate` | 直接取值 |

> **截图验证（loanid=7727000088）**：  
> "Active Foreclosure" ← `fcstage`（activefcflag=1）；"Kelley Kronenberg, P.A." ← `fcfirm`；"Judicial" ← `judicial=1`；"298" ← `smsdaysinfc + DATEDIFF(截图日, dataasof)`；"Judgment Entered" ← `currentmilestone`（优先于 fcstage）；"Motion for Judgment Sent to Court" ← `lastfcstepcompleted`

---

## Section 2：FCL Milestone 时间线面板

> **BPS 数据库来源**：`bpms_dev.sync_loan_foreclosure`（`timeline_*` 字段）  
> **Newrez 来源表**：`newrez.portnewrezfc`  
> **doc 13 对应小节**：Section 3.1

### 字段映射

| UI 标签 | Newrez 源字段 | Mapping Rule |
|---|---|---|
| Notice of Intent Date | `demandsentdate` | 直接取值（NOI/Demand Letter 发出日；85.9% 填充） |
| Notice of Intent End Date | `demandexpirationdate` | 直接取值（NOI 到期日；85.7%） |
| Approved for Referral Date | `fcsetupdate` | 直接取值（BPS 开案日；Newrez 通常与转介日同天） |
| Referred to Attorney Date | `fcreferraldate` | 直接取值 |
| Referred to Foreclosure Date | `fcreferraldate` | 直接取值（**BPS 入库核心条件**；同上字段） |
| Title Report Received Date | `titlereceiveddate` | 直接取值（❌ Newrez 不提供，恒为空） |
| Preliminary Title Cleared Date | `titlecleardate` | 直接取值（❌ Newrez 不提供，恒为空） |
| First Legal Date | `firstlegaldate` | 直接取值（57.6%；Non-Judicial 州通常为空） |
| Service Date | `servicecompletedate` | 直接取值（28.9%） |
| Publication Date | *(无对应字段)* | ❌ Newrez 不提供，始终为空 |
| Judgement Hearing Set Date | `fcjudgmenthearingscheduled` | 直接取值（11.9%；Judicial 州专用；听证会**排定日**） |
| Judgement Date | `fcjudgmententered` | 直接取值（7.9%；法院**正式录入**判决日；≠ 上条） |
| Projected Sale Date | `fcscheduledsaledate` | 直接取值（18.2%；最新预计拍卖日） |
| Sale Date Set | `fcscheduledsaledate` | 直接取值（同上字段，BPS 按状态判断区分） |
| Final Title Cleared Date | `titlecleardate` | 直接取值（❌ Newrez 不提供，恒为空） |
| Sale Date Held | `fcsalehelddate` | 直接取值（2.1%；实际拍卖日） |
| Foreclosure Completed Date | `dtdeedrecorded` / `fcremovaldate` | `COALESCE(dtdeedrecorded, fcremovaldate)`（产权登记日优先；兜底取撤销日） |
| Third Party Sold Date | `fcsalehelddate` | 当 `fcresults='3rd Party'` 时取 `fcsalehelddate` |
| Third Party Proceeds Received Date | `fcl3rdpartyproceedsreceiveddate` | 直接取值（极少填充） |

---

## Section 3：Hold 面板

> **BPS 数据库来源**：`bpms_dev.sync_loan_foreclosure_hold`（15列）  
> **Newrez 来源表**：`newrez.portnewrezfc`（3个 Hold 槽位，每槽 4 字段）  
> **doc 13 对应小节**：Section 4

### 字段映射

| UI 标签 | Newrez 源字段 | Mapping Rule |
|---|---|---|
| Description | `fchold1/2/3description` | 直接取值（Hold 原因文本，如"Court Delay"） |
| Start Date | `fchold1/2/3startdate` | 直接取值 |
| End Date | `fchold1/2/3enddate` | 直接取值（NULL = 仍在持续） |

> **架构说明**：Newrez 3 个槽位是**当前快照**。BPS 每日检测变更并追加新行，积累完整历史（如 loanid=7727000088 有 7 条历史记录，而 Newrez 仅显示 1 个活跃槽位）。  
> **BPS 入库筛选**：`fchold1startdate IS NOT NULL`（槽位 1 有开始日才提取）；各槽展开后取 description/dates 有一非空即入。

---

## Section 4：Loss Mitigation Cycle 面板

> **BPS 数据库来源**：`bpms_dev.sync_loan_foreclosure_loss_mitigation`（22列）  
> **Newrez 来源表**：`newrez.portnewrezlm`  
> **doc 13 对应小节**：Section 5

### 字段映射

| UI 标签 | Newrez 源字段 | Mapping Rule |
|---|---|---|
| Deal | `lmdeal`（int） | ETL 解码为文本（如 `7`→`"DIL"`；`1`→`"Evaluation"`） |
| Program | `lmprogram`（int） | ETL 解码（如 `10`→`"Deed-in-Lieu"`；`"Bridger mod"` 等） |
| Status | `lmstatus`（int） | ETL 解码（如 `"Pending Financials"`/`"Workout Denial"`） |
| Cycle Opened Date | `dealstartdate` | 直接取值（LM 周期开始日） |
| Cycle Closed Date | `lmremovaldate` | 直接取值（NULL = 进行中） |
| Final Disposition | `lmdecision`（int） | ETL 解码（如 `"Referral to FC"`/`"Pending"`） |
| Denial / Reason | `denialreason`（int） | ETL 解码；无拒绝时为空字符串 |
| Borrower Intentions | `borrowerintention`（int） | ETL 解码；Newrez 恒为 NULL（不提供） |
| Imminent Default | *(无)* | Newrez 不提供；恒为 NULL |
| Single Point of Contact | *(无)* | Newrez 不提供；恒为 NULL |

> **BPS 入库筛选**：`dealstartdate IS NOT NULL`；去重：`PARTITION BY (loanid, dealstartdate) ORDER BY dataasof DESC`（每 LM 周期保留最新快照一行）。

---

## Section 5：Bankruptcy 面板

> **BPS 数据库来源**：`bpms_dev.sync_loan_foreclosure_bankruptcy`（22列）  
> **Newrez 来源表**：`newrez.portnewrezbk` + `newrez.portnewrezgeneral`（legal_status）  
> **doc 13 对应小节**：Section 6

### 字段映射

| UI 标签 | Newrez 源字段 | Mapping Rule |
|---|---|---|
| Status | `bkstatus`（int） | 编码解码行为待确认（见 doc 13 Q7） |
| Legal Status | `bkstage`（int） | 同上 |
| Status Date | `bkrcurrentstatusdate` | 直接取值 |
| Chapter | `bkchapter` | 直接取值（7 / 11 / 13） |
| Lien Status | *(待确认)* | 可能来自 `portnewrezgeneral.legalstatus` |
| MFR Status | `mfrhearingresults`（int） | 数字编码（解码行为待确认） |
| MFR Filed Date | `mfrfileddate` | 直接取值 |
| Claim Status | *(待确认)* | 可能来自 POC 相关字段 |
| Proof of Claim Date | `pocfileddate` | 直接取值 |
| Post Petition Due Date | `bkpostpetitionduedate` | 直接取值 |

> **BPS 入库筛选**：`LENGTH(TRIM(bkstatus)) > 0`；去重：`PARTITION BY (loanid, bkfileddate) ORDER BY dataasof DESC`。  
> loanid=7727000088 无破产记录，面板显示"No Rows To Show"（MCP 实测确认）。

---

## Section 6：聚合概览页（Foreclosure Summary Tab）

> **BPS 数据库来源**：`bpms_dev.sync_fcl_stage_info`（57列）  
> **Newrez 来源表**：`newrez.portnewrezfc`  
> **doc 13 对应小节**：Section 7  
> **⚠️ 仅含活跃 FCL**：`activefcflag=1 AND fcremovaldate IS NULL`（完结贷款不在此表）

### Stage Tab — 阶段天数字段

| UI 列 | BPS 字段 | Newrez 触发条件 |
|---|---|---|
| Days in Stage | `{stage}_stage_days` | 当前阶段开始日 → 今日 |
| Days in LM | `{stage}_in_lm_days` | 当前阶段期间与 LM 周期重叠天数 |
| Days on Hold | `{stage}_on_hold_days` | 当前阶段期间与 Hold 重叠天数 |
| Days to Sale | `to_sale_days` | SALE 阶段专用：`fcscheduledsaledate − 今日` |
| Days to Judgement | `to_judgement_days` | JUDGEMENT 阶段专用 |

### 阶段划分规则（瀑布优先级）

| 优先级 | Stage | Newrez 触发条件 |
|---|---|---|
| 1 | `SALE` | `fcscheduledsaledate IS NOT NULL` |
| 2 | `JUDGEMENT` | `fcjudgmenthearingscheduled IS NOT NULL` AND SALE 未触发 |
| 3 | `PUBLICATION` | `publication_date IS NOT NULL`（Newrez 恒为空） |
| 4 | `SERVICE` | `servicecompletedate IS NOT NULL` |
| 5 | `FIRST_LEGAL` | `firstlegaldate IS NOT NULL` AND SERVICE 未触发 |
| 6 | `REFERRAL` | `fcreferraldate IS NOT NULL` AND FIRST_LEGAL 未触发 |
| 7 | `DEMAND` | `demandsentdate IS NOT NULL` AND REFERRAL 未触发 |

### Time Line Tab — 里程碑日期字段

| UI 列（序号） | BPS 字段 | Newrez 源字段 | 说明 |
|---|---|---|---|
| NOI Date 1 | `noi_start_date` | *(无)* | Newrez 恒为 NULL（见 doc 13 Q11） |
| Referral Date 2 | `referral_start_date` | `fcreferraldate` | 100%（入库前提） |
| First Legal Date 3 | `first_legal_start_date` | `firstlegaldate` | — |
| Service Date 4 | `service_start_date` | `servicecompletedate` | 28.9% |
| Publication Date 5 | `publication_start_date` | *(无)* | Newrez 恒为 NULL |
| Judgement Date 6 | `judgement_start_date` | `fcjudgmenthearingscheduled` | 听证会**排定日**（非法院录入日） |
| Sale Date 7 | `sale_start_date` | `fcscheduledsaledate` | 18.2% |

---

## 附录：快速错误排查路径

| 症状 | 先查 | 再查 |
|---|---|---|
| Foreclosure Summary 字段显示异常 | Section 1 找到 UI 标签 → 确认 Newrez 源字段 | doc 13 Section 3.7 + 附录 B SQL-4 |
| Timeline 日期显示异常 | Section 2 找到 UI 标签 | doc 13 Section 3.1 |
| Hold 面板数据缺失或重复 | Section 3 架构说明 | doc 13 Section 4 + 附录 B SQL-5 |
| LM 面板显示数字编码而非文本 | Section 4 Mapping Rule（ETL 解码） | doc 13 Section 5 + Section 3.2 ETL 解码说明 |
| BK 面板字段确认 | Section 5 | doc 13 Section 6 + Q7 |
| 聚合页 Stage 分类错误 | Section 6 阶段划分规则 | doc 13 Section 7 + 附录 B SQL-9/10 |
| Days in Stage / LM / Hold 计算异常 | Section 6 Stage Tab 字段说明 | doc 13 Section 7 |
