# Foreclosure Data Dictionary — PrefectFlow

> **命名说明（2024-07-05）：** 本文源表前缀现为 `portnewrez*`（此前为 `portshellpoint*`，Shellpoint 时期）；DB 实测 `newrez` schema 仅 `portnewrez*`，现役以此为准，改名史详见 doc 01。

---

## Document Purpose

- **Why this document exists**: PrefectFlow 从多家 Servicer 采集数据，经过归一化后存入 Redshift 数据仓库。Foreclosure 相关数据分散在 12+ 张表中，命名风格各异、字段含义不透明。本文档通过 reverse engineering 将这些表/字段的业务含义、数据来源、计算逻辑系统地记录下来。
- **What problem it solves**: 新加入成员（数据产品经理、数据工程师、验证人员）无法快速理解 foreclosure 数据流和字段语义；系统重构时缺乏可信的字段级规格说明。
- **Scope**: 仅覆盖与 Mortgage Loan Foreclosure / Delinquency / Bankruptcy / Loss Mitigation / REO 直接相关的核心表和字段。不覆盖 ARM、PMI、HELOC 等无关表。
- **System fit**: 本文档是 ForeclosureRule2 项目文档体系的一部分，与 `01_source_data.md`（原始数据源说明）互为补充。

## Target Audience

主要读者：数据产品经理 · 数据工程师 · 业务分析师 · 验证人员 · 未来 AI session  
次要读者：合规/数据治理团队 · 系统重构工程师

## Revision History

| Date | Author | Version | Changes | Related |
|------|--------|---------|---------|---------|
| 2026-06-05 | AI Agent (Claude Opus 4.8) | v14 | 表名改正 `portshellpoint*`→`portnewrez*`（DB 实测 newrez 现役表，2024-07-05 改名）+ 加命名说明 | DB 实测 · doc 01 |
| 2026-06-04 | AI Agent (Claude Opus 4.8) | v13 | 新增**表26 `newrez.portnewrezdatadic`**（Redshift 解码字典）：结构+角色+解码表（小字段 LMDeal/BorrowerIntention/BKStatus/BKStage 全量；大字段 LMProgram/LMStatus/LMDecision/DenialReason 去长尾=prod 最新快照出现的码）；「表19 LM 解码参考」加表26交叉引用。数据经 redshift_prod 只读预取 | doc 19 v3 · redshift_prod |
| 2026-06-03 | AI Agent (Claude Opus 4.8) | v12 | 「表19 LM 编码字段解码参考」补充解码机制溯源：映射数据在 **Redshift 字典表 `newrez.portnewrezdatadic`**（dev MySQL 无），解码 JOIN 在代码 `basic_data_pool_config.py:835-840`（BK :367），非硬编码；LMDeal 字典 13 码（实测 8） | basic_data_pool_config.py · Redshift portnewrezdatadic · doc 13 v33 |
| 2026-06-03 | AI Agent (Claude Opus 4.8) | v11 | 【可读性】把值/枚举取值列表的中点 `·` 分隔符统一改为 `\|`（与 doc 14 一致）：summary_foreclosure_status / fchold1description / fcresults / currentmilestone / lmdeal·lmstatus·lmprogram·lmdecision·denialreason 编码列表 / bk 解码 共 10 处；保留「X 阶段 · 子含义」结构标签、读者行、修订史里的 `·` | doc 14 v24 · doc 13 v32 |
| 2026-05-23 | AI Agent | v1 | Initial draft — reverse engineered from PrefectFlow Python/SQL source | prompt.md |
| 2026-05-25 | AI Agent (Claude Sonnet 4.6) | v2 | 新增表13（port.basic_data_loan_fcl，61列全量）和表14（port.basic_data_loan_foreclosure，62列全量）；包含DB实测类型、真实取值分布、INSERT填充状态标注；修正 fcstage 实际取值说明 | prompt.md |
| 2026-05-25 | AI Agent (Claude Sonnet 4.6) | v3 | 新增表15（port.portmonthbase，120列）和表16（port.portmonth，141列）；含Redshift实测行数/日期范围/delinq分布/关键字段统计；标注 portmonth 相对 portmonthbase 的23个新增字段（★） | prompt.md |
| 2026-05-28 | AI Agent (Claude Sonnet 4.6) | v4 | 新增表17（bpms_dev.sync_loan_foreclosure，72列，MCP实测）；7组字段全量记录（标识符/timeline_*/target_*_days/variance_*/bid_approval_*/summary_*/管理字段）；标注 target_*_days 硬编码DEFAULT值、bid_approval_loan_resolution_holods 列名拼写错误、actual_*_days 字段位于 sync_fcl_stage_info 而非本表 | prompt.md |
| 2026-06-01 | AI Agent (Claude Sonnet 4.6) | v6 | 表18/表19 典型取值 MySQL 实测校正：① currentmilestone 更正（去除不存在的 'First Legal Complete'）；② fchold1description 更正为完整枚举值；③ fcresults 更正（去除不存在的 '3rd Party Sale'/'Redemption'）；④ Hold 2/3 全部 — 字段补充实测值；⑤ hardshiptype/denialreason 更正为实际编码；⑥ pradate2/3、praamount2/3 标注实测始终 NULL | MySQL newrez 实测 |
| 2026-06-01 | AI Agent (Claude Sonnet 4.6) | v8 | 表19 LM 编码字段补全：① borrowerintention、lmdeal 取值范围列内联 BPS 解码文本；② lmprogram/lmstatus/lmdecision/denialreason 取值范围列增加解码参考说明；③ 新增「表19 LM 编码字段解码参考」章节（5 张解码表，共约 60 条 code→text 映射，来自 bpms_dev JOIN newrez 实测） | BPS JOIN 2026-06-01 |
| 2026-06-01 | AI Agent (Claude Sonnet 4.6) | v7 | 表18/表19「典型取值」列拆分为「取值范围」+「典型取值」两列（9列→10列）；取值范围来自 MCP MySQL 实测（min/max、枚举集、格式约束）；典型取值保留单一代表性示例 | MySQL newrez 实测 2026-06-01 |
| 2026-05-29 | AI Agent (Codex) | v5 | 新增表18（newrez.portnewrezfc，63列，MySQL实测）和表19（newrez.portnewrezlm，56列，MySQL实测）；补充 Newrez FCL/LM 原始表字段、行数、dataasof 范围、关键字段最新快照分布、代码下游使用路径 | prompt.md |
| 2026-06-01 | AI Agent (Claude Opus 4.8) | v10 | 依据 PrefectFlow 源码确认/订正表上游下游血缘：① 表17 上游来源由"写入来源不明/推测 BPS 应用层"**订正为代码确认的两步写入**（`sync_to_mysql` staging → `update_to_mysql`→`UPDATE_FORECLOSURE` upsert，df_db_util.py:698/710 + asset_managment_config.py:644）；订正下游（`sync_fcl_stage_info` 非本表下游）；② 表17/20–25 各属性块新增「代码血缘（PrefectFlow）」行（SQL 模板 + file:line）；③ 表23 字段来源按代码订正：`legal_status`←portnewrezgeneral.legalstatus、`status_date`←bkfileddate、`mfr_status`/`claim_status`/`lien_status` 恒 NULL、`mfr_filed_date` 仅 Carrington 分支（推翻 doc 13 §6 二手映射） | PrefectFlow 源码 (basic_data_pool_config.py / asset_managment_config.py / df_db_util.py / sync_asset_management.py / servicer_config.py) |
| 2026-06-01 | AI Agent (Claude Opus 4.8) | v9 | 新增表20–表25（6张，MCP 实测，10列表头含【取值范围】）：表20 `newrez.portnewrezbk`(60) · 表21 `sync_loan_foreclosure_hold`(15) · 表22 `sync_loan_foreclosure_loss_mitigation`(22) · 表23 `sync_loan_foreclosure_bankruptcy`(22) · 表24 `sync_fcl_stage_info`(57) · 表25 `biz_data_view_loan_details_foreclosure`(104, VIEW)。同时为表17 全 7 组补充【取值范围】列并**按 live schema 校正字段清单/类型**（无 `dataasof`、含 `id` 主键、timeline 组成员与多字段类型更正）。取值范围/类型/填充率全部经 MCP 实测（脚本 `scripts/extract_table_stats.py` → `outputs/table_stats_for_data_dictionary.json`；视图溯源用 `SHOW CREATE VIEW`） | MCP 实测 2026-06-01；doc 13 §2/§4/§5/§6/§7 |

## Assumptions

- 字段 Schema 来源于 `statistics_script/sls_daily.sql`、`statistics_script/shellpoint_daily.sql`、`flow/basic_data/transfer_daily_data_config/` 等文件
- MySQL `port` schema 中的表是 Servicer 原始数据（staging 层），Redshift `port` schema 中的表是归一化后的分析层
- SLS 于 2024-07-05 后转移至 Newrez 服务，代码中以 `SLS_TO_NEWREZ_DATE = '2024-07-05'` 为界

## Known Limitations

- `risk_panel_delinq`、`portmrcforeclosure`、`portcarringtonfcl` 等表的 CREATE TABLE 未读到，字段信息来源于 SELECT 语句和 Agent 探索，部分字段标注为 **Strong/Weak Inference**
- 置信度说明：`✅ Confirmed` = 源码直接对应 | `🟡 Strong Inference` = 有充分上下文推断 | `🔶 Weak Inference` = 逻辑推断但未直接验证 | `❓ Unknown`

---

## 1. Foreclosure 业务入门（新人必读）

### 1.1 美国抵押贷款 Foreclosure 生命周期

```
借款人按时还款
     │
     ▼
 逾期 (Delinquent)
     │  nextduedate 过了30/60/90/120天
     ▼
 D30 → D60 → D90 → D120+ (D120P)
     │
     ▼  贷款人发出 NOI（Notice of Intent）或 Demand Letter
     │
     ▼
 Foreclosure Referral（委托律师）
     │  fcl_referred_to_attorney_date / fcreferraldate
     ▼
 First Legal Action（第一次法律行动）
     │  fcl_first_legal_action_date / firstlegaldate
     ▼
 Service Complete（完成送达）
     │  fcl_service_complete_date / servicecompletedate
     ▼
 Judgment Entered（法院裁定）/ Sale Scheduled（拍卖日期确定）
     │  fcl_judgement_entered_date / fcscheduledsaledate
     ▼
 FC Sale Held（拍卖完成）
     │  fcl_sale_held_date / fcsalehelddate
     ▼
 ┌───────────────────────────────────┐
 │ 第三方购买 → 3rd Party Sale       │
 │ 投资人接收 → REO（Real Estate Owned）│
 └───────────────────────────────────┘
```

### 1.2 关键术语速查

| 术语 | 全称 | 含义 |
|------|------|------|
| FCL | Foreclosure | 取消赎回权（法拍）流程 |
| REO | Real Estate Owned | 银行/投资人持有的取回房产 |
| BK | Bankruptcy | 借款人破产 |
| LM | Loss Mitigation | 损失减缓（修改还款、宽限期等） |
| NOI | Notice of Intent | 意向通知书（法拍前预警） |
| MFR | Motion for Relief | 解除自动暂停令申请（BK 期间推进法拍的法律手段） |
| D120P | 120+ Days Past Due | 逾期120天以上（法拍前最严重档位） |
| UPB | Unpaid Principal Balance | 未偿还本金余额 |
| MBA | Mortgage Bankers Association | 美国抵押贷款银行家协会（定义标准化逾期状态码） |
| Servicer | — | 贷款服务商，负责收款、逾期管理、法拍执行 |

### 1.3 系统中的 Servicer

| Servicer | 代码 | MySQL Schema | 备注 |
|----------|------|--------------|------|
| SLS | `SLS` | `sls` | 2024-07-05 前主要服务商，之后转 Newrez |
| Newrez/Shellpoint | `Newrez` | `newrez`, `shellpoint` | 2024-07-05 后接替 SLS |
| Carrington | `Carrington` | `carrington` | — |
| Selene | `Selene` | `selene` | — |
| MRC | `MRC` | `mrc` | — |
| Arvest | `Arvest` | `arvest` | 无 daily 数据，使用月报表 |
| Capecodfive | `Capecodfive` | `capecodfive` | 使用月报表 |

---

## 2. 数据架构概览

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Layer 1: Raw / Servicer-Specific                 │
│         MySQL `port` / `sls` / `shellpoint` / `mrc` etc. schema     │
│                                                                     │
│  sls.portassetdaily    sls.portfcldaily     sls.portbkdaily         │
│  sls.portlmdaily       sls.portreodaily                             │
│  newrez.portnewrezfc   newrez.portnewrezbk          │
│  newrez.portnewrezlm   newrez.portnewrezreo         │
│  mrc.portmrcforeclosure        carrington.portcarringtonfcl         │
│  selene.portselenemain         fci.portfciwebforeclosure            │
└─────────────────────────────────────────────────────────────────────┘
                              │ ETL (PrefectFlow daily flows)
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    Layer 2: Normalized / Staging                    │
│                      Redshift `port` schema                         │
│                                                                     │
│  port.basic_data_daily_loan_common      (86 字段，多 Servicer 汇合)       │
│  port.basic_data_daily_loan_common_clean (标准化 delinq 码，加 deal 维度) │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    Layer 3: Reporting / Analytics                   │
│                      Redshift `czeng` / `port`                      │
│                                                                     │
│  port.basic_data_loan_fcl          (FCL运营数据，61列，3 Servicers)   │
│  port.basic_data_loan_foreclosure  (FCL BI层，62列，BPS下游)           │
│  port.portmonthbase                (基础月度贷款表，120列，78,913行)   │
│  port.portmonth                    (增强月度分析表，141列，129,023行)  │
│  czeng.risk_panel_delinq           (风险面板，FC referral 追踪)      │
│  port.basic_data_monthly_loan_remit     (月度现金流，含逾期状态)           │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 3. 表级说明与字段文档

---

### 表 01：`port.basic_data_daily_loan_common`

| 属性 | 值 |
|------|----|
| **表名** | `port.basic_data_daily_loan_common` |
| **所属 Schema** | Redshift `port`（变量 `REDSHIFT_PORT`） |
| **数据层** | Normalized / Staging |
| **业务作用** | 将所有 Servicer 的日度贷款数据汇合为统一结构，每行为一笔贷款在某个观察日（`asofdate`）的快照 |
| **业务意图** | 消除 Servicer 之间的字段命名差异，形成跨 Servicer 可比的基础数据，供下游 Clean 表使用 |
| **主要用途** | 下游 `port.basic_data_daily_loan_common_clean` 的数据源 |
| **上游来源** | SLS: `sls.portstandarddaily` + `sls.portassetdaily`<br>Newrez: `newrez.portnewrezpmt` + `newrez.portnewrezgeneral` + `newrez.portnewrezlm` + `newrez.portnewrezcontact` 等<br>Carrington: `carrington.portcarrington`<br>Selene: `selene.portselenemain`<br>MRC: `mrc.portmrcloan` + `mrc.portmrcforeclosure` + `mrc.portmrcforbearance` 等 |
| **下游使用** | `port.basic_data_daily_loan_common_clean`（每月 factor date 快照） |
| **Foreclosure 关系** | 包含 `fcl_flag`（简单激活标志）和 `delq_status`（Servicer 原始逾期状态，可含 "Foreclosure"/"REO" 等值） |
| **Servicer-specific** | 否（多 Servicer 合并） |
| **已知问题** | SLS 的 `fcl_flag` 映射为 `null`；Newrez 的 `fcl_flag` 也映射为 `null`（详见 `daily_data_loan_common_config.py`）；Foreclosure 激活状态依赖 Selene 的 `foreclosure_status_code` 和 MRC 的 `fc.fc_flag` |

#### 字段说明（仅 Foreclosure 相关字段）

| 字段名 | 字段业务含义 | 来源数据 | 计算/推导逻辑 | 数据类型 | 典型取值 | 上游字段 | 下游用途 | 备注 |
|--------|------------|---------|--------------|---------|---------|---------|---------|------|
| `asofdate` | 数据观察日期（Servicer 上报数据的截止日） | 各 Servicer | 直接映射 | DATE | `2024-07-04` | `sls.portstandarddaily.dataasofdate`<br>`newrez.portnewrezpmt.dataasof` | 用于与 `basic_data_daily_loan_data_select` join，确定月度快照点 | ✅ Confirmed |
| `loanid` | 投资人贷款ID（跨 Servicer 的统一标识） | 各 Servicer | 直接映射 | VARCHAR(255) | `7727001272` | `sls.portstandarddaily.account_number_investor`<br>`newrez.portnewrezpmt.loanid` | 关联 `port.portfunding`、`d.bid` | ✅ Confirmed |
| `svcloanid` | Servicer 内部贷款号 | 各 Servicer | 直接映射 | VARCHAR(255) | `12345678` | `sls.portstandarddaily.account_number`<br>`newrez.portnewrezpmt.shellpointloanid` | 向 Servicer 查询时的对账字段 | ✅ Confirmed |
| `servicer` | 当前服务商名称（hardcoded） | Hardcoded | `'SLS'` / `'Newrez'` / `'Carrington'` / `'Selene'` / `'MRC'` | VARCHAR(10) | `Newrez` | — | 分组、过滤 | ✅ Confirmed |
| `nextduedate` | 下一个应还款日，即借款人下一笔到期付款的日期 | 各 Servicer | 直接映射 | DATE | `2024-08-01` | `sls.portstandarddaily.payment_due_date_next`<br>`newrez.portnewrezpmt.nextduedate` | 在 Clean 表中用于计算 `delinq` 档位：`days360(nextduedate, fctrdt)` | ✅ Confirmed |
| `delq_status` | Servicer 原始逾期状态描述（未标准化） | 各 Servicer | 直接映射 | VARCHAR(255) | `Foreclosure`, `Bankruptcy`, `REO`, `Current`, `30`, `60` | `sls.portassetdaily.delq_status_mba`<br>`newrez.portnewrezgeneral.delinquency_status_mba`<br>`carrington.portcarrington.loan_status`<br>`selene.portselenemain.loan_status` | Clean 表中转换为标准 `delinq` 码；是识别 FCL/REO 的第一入口 | ✅ Confirmed |
| `fcl_flag` | Foreclosure 激活标志（各 Servicer 含义不一致） | 各 Servicer | 直接映射，未统一 | VARCHAR(50) | `Active`, `null`, 状态码 | `selene.portselenemain.foreclosure_status_code`<br>`mrc.portmrcforeclosure.fc_flag`<br>`carrington.portcarrington.fcl_flag` | Clean 表中结合 `delq_status` 一起推断 FCL 状态 | 🟡 Strong Inference：SLS/Newrez 映射为 `null`，仅 Selene/MRC/Carrington 有值 |
| `lm_flag` | Loss Mitigation 激活标志 | 各 Servicer | CASE-WHEN 逻辑 | VARCHAR(1) | `Y`, `N` | `newrez.portnewrezlm.activelmflag`（`= '1'` → `'Y'`）<br>`carrington.portcarrington.lm_flag`（`= 'Active'` → `'Y'`）<br>`selene.portselenemain.lm_setup_date`（not null → `'Y'`） | 识别在 LM 中的贷款，与 foreclosure 并行追踪 | ✅ Confirmed（各 Servicer 逻辑略有不同） |
| `forbearance` | Forbearance（宽限期）状态 | 各 Servicer | 部分原值，部分 CASE-WHEN 映射 | VARCHAR(255) | `Active`, `Pending`, `Satisfied`, `Delinquent` | `sls.portassetdaily.forbearance_flag`<br>`newrez.portnewrezlm.forbearancestatus`（数字 → 文本：`'1'`→`Active`，`'4'`→`Satisfied`）<br>`carrington.portcarrington.covid_forbearance_flag` | LM 分析；Forbearance 期间通常暂停 FC 推进 | ✅ Confirmed |
| `lastcontactdate` | 服务商最后一次成功联系借款人的日期 | 各 Servicer | 直接映射 | DATE | `2024-06-15` | `newrez.portnewrezcontact.lastcontactdate`<br>`carrington.portcarrington.date_delinq_contact`<br>`mrc.portmrcloan.last_contact_date` | 逾期管理合规监控（30日窗口接触追踪） | ✅ Confirmed |
| `reasonfordefault` | 借款人违约原因描述 | 各 Servicer | 直接映射 | VARCHAR(255) | `Job Loss`, `Medical`, `Divorce` | `newrez.portnewrezgeneral.reasonfordefault`<br>`carrington.portcarrington.reason_for_default1` | 风险面板分析；Loss Mitigation 决策依据 | ✅ Confirmed |
| `modi` | 是否有贷款修改 Y/N | 各 Servicer | CASE-WHEN 推断 | VARCHAR(1) | `Y`, `N` | `sls.portassetdaily.modification_type`（not null → `'Y'`）<br>`newrez.portnewrezmod.modificationflag`（`'1'`→`'Y'`） | 修改后贷款的 FCL 风险通常不同 | ✅ Confirmed |
| `moditype` | 贷款修改类型 | 各 Servicer | 直接映射 | VARCHAR(255) | `HAMP`, `Proprietary`, `FHA` | `sls.portassetdaily.modification_type`<br>`newrez.portnewrezmod.modtype`<br>`carrington.portcarrington.mod_type` | — | ✅ Confirmed |
| `modidate` | 贷款修改生效日 | 各 Servicer | 直接映射 | DATE | `2023-01-01` | `newrez.portnewrezmod.moddate`<br>`carrington.portcarrington.date_modified` | — | ✅ Confirmed |
| `principalbalance` | 当前未偿还本金余额 (UPB) | 各 Servicer | 直接映射 | DOUBLE | `185000.00` | `sls.portstandarddaily.balance_principal_current`<br>`newrez.portnewrezpmt.principalbalance` | FCL 损失率计算；投资人报告 | ✅ Confirmed |
| `deferredprincipalbalance` | 递延本金余额（通常来自 COVID 修改） | 各 Servicer | 直接映射（Newrez 2025-07-01 后含 `deferredescrow` + `deferredotherfees`） | DOUBLE | `15000.00` | `sls.portstandarddaily.balance_principal_deferred`<br>`newrez.portnewrezpmt.deferredprincipalbalance` | 贷款实际负债分析；FCL 前需清算 | ✅ Confirmed |

---

### 表 02：`port.basic_data_daily_loan_common_clean`

| 属性 | 值 |
|------|----|
| **表名** | `port.basic_data_daily_loan_common_clean` |
| **所属 Schema** | Redshift `port` |
| **数据层** | Normalized（标准化 staging） |
| **业务作用** | 在 `port.basic_data_daily_loan_common` 基础上，对每笔贷款按月度 factor date（`fctrdt`）打快照，并将 Servicer 原始逾期状态转换为统一的 `delinq` 状态码 |
| **业务意图** | 为投资人报告、IRR 计算、风险分析提供可信、跨 Servicer 一致的贷款月度快照；`delinq` 字段是全系统 Foreclosure 状态的"事实标准" |
| **主要用途** | IRR 计算、月度风险报告、FCL 率统计、Loss Severity 分析 |
| **上游来源** | `port.basic_data_daily_loan_common`（月度最后快照点）+ `d.bid`（deal 维度）+ `port.portfunding`（投资结构） |
| **下游使用** | `port.basic_data_monthly_loan_remit`、`czeng.risk_panel_delinq`、IRR 流程、投资人报告 |
| **Foreclosure 关系** | `delinq` 字段是核心：值为 `FCL` 表示该贷款处于法拍状态；`D120P` 是法拍的前序状态 |
| **Servicer-specific** | 否 |
| **已知问题** | Arvest、Capecodfive 无 daily 数据，使用月报表聚合，部分字段（`lm_flag`、`lastcontactdate`）为 null |

#### 字段说明（Foreclosure 核心字段）

| 字段名 | 字段业务含义 | 来源数据 | 计算/推导逻辑 | 数据类型 | 典型取值 | 上游字段 | 下游用途 | 备注 |
|--------|------------|---------|--------------|---------|---------|---------|---------|------|
| `fctrdt` | Factor Date，月度报告日期（每月1日，代表上月末数据） | 计算字段 | `trunc(dateadd(day, 1, last_day(asofdate)))` — 即取 asofdate 所在月的最后一天，再加1天 | DATE | `2024-08-01` | `port.basic_data_daily_loan_common.asofdate` | 所有月度分析的时间维度；join key | ✅ Confirmed |
| `dealid` | Deal 编号（投资交易标识） | `port.portfunding` | 直接映射 | VARCHAR(50) | `DEAL001` | `port.portfunding.dealid` | 按 deal 汇总逾期率；投资人报告分组 | ✅ Confirmed |
| `fundingid` | Funding 编号（资金来源标识） | `port.portfunding` | 直接映射 | VARCHAR(50) | `FUND001` | `port.portfunding.fundingid` | — | ✅ Confirmed |
| `loanid` | 投资人贷款ID | 上游表 | 直接映射 | VARCHAR(30) | `7727001272` | `port.basic_data_daily_loan_common.loanid` | 所有下游表的 join key | ✅ Confirmed |
| `servicer` | 服务商名称 | 上游表 | 直接映射 | VARCHAR(20) | `Newrez`, `SLS`, `Carrington` | `port.basic_data_daily_loan_common.servicer` | 按 servicer 分组分析 | ✅ Confirmed |
| `nextduedate` | 下一应还款日 | 上游表 | 直接映射 | DATE | `2024-08-01` | `port.basic_data_daily_loan_common.nextduedate` | 与 `fctrdt` 计算逾期天数 | ✅ Confirmed |
| `svcdelinq` | Servicer 原始逾期状态码（未标准化） | 上游表 | 直接映射（来自 `port.basic_data_daily_loan_common.delq_status`） | VARCHAR(30) | `Foreclosure`, `Current`, `Bankruptcy - Performing` | `port.basic_data_daily_loan_common.delq_status` | 辅助诊断；对比 `delinq` 排查异常 | ✅ Confirmed |
| `delinq` | **标准化逾期状态码（全系统核心字段）** | 计算字段 | 见下方状态机（Section 4）；基于 `svcdelinq` + `days360(nextduedate, fctrdt)` | VARCHAR(10) | `C`, `D30`, `D60`, `D90`, `D120P`, `FCL`, `REO`, `P`, `VASP` | `svcdelinq`, `nextduedate`, `fctrdt`, `fcl_flag` | FCL 率、逾期报告、IRR、风险面板 | ✅ Confirmed |
| `monthindelinq` | 逾期月数（整数） | 计算字段 | `greatest(floor(days360(nextduedate, fctrdt) / 30), 0)` | INT | `0`（Current）, `3`（D90）, `6` | `nextduedate`, `fctrdt` | 逾期深度分析；timeline rule 判断 | ✅ Confirmed |
| `bankruptcy` | 破产标志 Y/N | 计算字段 | SLS: `case when svcdelinq = 'Bankruptcy' then 'Y' else 'N' end`<br>Newrez: `case when svcdelinq like '%Bankruptcy%' then 'Y' else 'N' end`<br>Carrington: `case when svcdelinq = 'Bankruptcy - Performing' then 'Y' else 'N' end` | VARCHAR(10) | `Y`, `N` | `port.basic_data_daily_loan_common.delq_status` | 风险面板；BK 期间 FC 推进暂停 | ✅ Confirmed |
| `lm_flag` | Loss Mitigation 激活标志 Y/N | 上游表 | 直接映射（来自 `port.basic_data_daily_loan_common.lm_flag`） | VARCHAR(10) | `Y`, `N`, `null` | `port.basic_data_daily_loan_common.lm_flag` | LM 追踪；LM 期间 FC 通常暂停 | ✅ Confirmed（Arvest/Capecodfive 为 null） |
| `forbearance` | Forbearance 状态 | 上游表 | 直接映射（Newrez 数字码在 common 中已翻译） | VARCHAR(100) | `Active`, `Satisfied`, `Pending`, `Delinquent` | `port.basic_data_daily_loan_common.forbearance` | LM/forbearance 分析 | ✅ Confirmed |
| `modi` | 是否有贷款修改 | 上游表 | 直接映射或 CASE-WHEN | VARCHAR(100) | `Y`, `N` | `port.basic_data_daily_loan_common.modi` | 修改贷款的 FCL 风险不同 | ✅ Confirmed |
| `balance` | 当前未偿还本金余额 | 上游表 | 直接映射 | FLOAT | `185000.00` | `port.basic_data_daily_loan_common.principalbalance` | FCL Loss Severity 计算基础 | ✅ Confirmed |
| `deferredprin` | 递延本金余额 | 上游表 | 直接映射 | FLOAT | `15000.00` | `port.basic_data_daily_loan_common.deferredprincipalbalance` | 实际负债 = `balance + deferredprin` | ✅ Confirmed |
| `deferredint` | 递延利息余额 | 上游表 | 直接映射 | FLOAT | `2000.00` | `port.basic_data_daily_loan_common.deferredinterestbalance` | — | ✅ Confirmed |
| `pandi` | 月度本利合计（P&I，Scheduled Principal and Interest） | 计算字段 | 若 `schedule_pandi_daily > 0` 则直接用；否则按标准年金公式：`origbal / ((1 - (1 / (1 + rate/1200)^term)) / (rate/1200))` | FLOAT | `1250.00` | `port.basic_data_daily_loan_common.schedule_pandi_daily` | IRR 现金流建模 | ✅ Confirmed |
| `lastcontactdate` | 最后联系日期 | 上游表 | 直接映射 | DATE | `2024-06-15` | `port.basic_data_daily_loan_common.lastcontactdate` | 30日接触合规追踪（risk_panel_delinq） | ✅ Confirmed |
| `reasonfordefault` | 违约原因 | 上游表 | 直接映射 | VARCHAR(5000) | `Job Loss`, `Medical` | `port.basic_data_daily_loan_common.reasonfordefault` | LM 决策支持 | ✅ Confirmed |
| `corpadvrec` | 可回收公司垫付款（Recoverable Corporate Advance） | 上游表 + 计算 | SLS: `reccorpadvance * -1`（符号反转）<br>Newrez: `reccorpadvance * -1`<br>Carrington: `coalesce(reccorpadvance, 0)` | FLOAT | `3500.00` | `port.basic_data_daily_loan_common.reccorpadvance` | FCL 损失分析；垫付款是法拍成本的一部分 | 🟡 Strong Inference（符号逻辑各 Servicer 不同） |
| `origbal` | 原始贷款金额 | `d.bid` 或 `port.basic_data_daily_loan_common.bal_prin_original` | `coalesce(bal_prin_original, bid.origbal)` | FLOAT | `220000.00` | `d.bid.origbal` | LTV 计算；FC 损失率基准 | ✅ Confirmed |
| `loanage` | 贷款已存续月数 | 计算字段 | `datediff(month, firstpaymentdate, fctrdt) + 1` | INT（via FLOAT） | `36` | `firstpaymentdate`, `fctrdt` | 逾期风险模型特征；FCL 预测 | ✅ Confirmed |

---

### 表 03：`sls.portfcldaily` — SLS Foreclosure Legal Timeline

| 属性 | 值 |
|------|----|
| **表名** | `portfcldaily` |
| **所属 Schema** | MySQL `sls`（物理存储在 `port` 数据库）|
| **数据层** | Raw / Servicer-specific |
| **业务作用** | 存储 SLS Servicer 上报的每笔贷款的法拍（Foreclosure）法律流程时间线 |
| **业务意图** | 追踪法拍推进各里程碑节点，支持 FCL timeline compliance（如 FNMA 规定的法拍完成天数） |
| **主要用途** | 法拍时间线分析；FCL days vs FNMA guideline 差异监控（`fcl_days_variance_to_fnma`） |
| **上游来源** | SLS 系统每日上报（通过 SFTP 或 API 抓取，由 PrefectFlow load daily flow 写入） |
| **下游使用** | 目前主要用于 SLS 贷款的 FC timeline 报告；`port.basic_data_daily_loan_common` 的 `fcl_flag` 字段部分来源于此 |
| **Foreclosure 关系** | 直接：记录法拍全流程节点 |
| **Servicer-specific** | 是（仅 SLS） |

#### 字段说明

| 字段名 | 字段业务含义 | 来源数据 | 计算/推导逻辑 | 数据类型 | 典型取值 | 上游字段 | 下游用途 | 备注 |
|--------|------------|---------|--------------|---------|---------|---------|---------|------|
| `account_number` | SLS 内部贷款账号 | SLS 系统 | 直接上报 | INT | `12345678` | — | join key（与 `portstandarddaily.account_number` 关联） | ✅ Confirmed |
| `data_as_of_date` | 数据截止日 | SLS 系统 | 直接上报 | DATE | `2024-07-04` | — | 时间过滤 | ✅ Confirmed |
| `fcl_active_flag` | 法拍是否激活（Y/N） | SLS 系统 | 直接上报 | VARCHAR(255) | `Y`, `N` | — | 识别活跃法拍贷款 | ✅ Confirmed |
| `fcl_approval_date` | 法拍批准日期（投资人/监管批准启动法拍的日期） | SLS 系统 | 直接上报 | DATE | `2023-11-01` | — | FCL 里程碑追踪 | ✅ Confirmed |
| `fcl_referred_to_attorney_date` | **法拍委托律师日期（FCL Referral）** — 法拍流程正式启动的关键节点 | SLS 系统 | 直接上报 | DATE | `2023-11-15` | — | FCL timeline 起点；NOI 后超过X天未 referral 为合规风险 | ✅ Confirmed |
| `fcl_first_legal_action_date` | 第一次法律行动日期（诉状提交或发出法拍通知） | SLS 系统 | 直接上报 | DATE | `2023-12-01` | — | FCL 里程碑；FNMA timeline 合规检查 | ✅ Confirmed |
| `fcl_service_complete_date` | 法律文件送达完成日期 | SLS 系统 | 直接上报 | DATE | `2024-01-15` | — | FCL 里程碑 | ✅ Confirmed |
| `fcl_judgement_entered_date` | 法院裁定法拍成立日期 | SLS 系统 | 直接上报 | DATE | `2024-03-01` | — | FCL 里程碑；judicial foreclosure 州必须有此节点 | ✅ Confirmed |
| `fcl_sale_scheduled_date` | 法拍拍卖预定日期 | SLS 系统 | 直接上报 | DATE | `2024-05-15` | — | 拍卖日期管理 | ✅ Confirmed |
| `fcl_sale_held_date` | 法拍拍卖实际执行日期 | SLS 系统 | 直接上报 | DATE | `2024-05-15` | — | 法拍完成确认；之后进入 REO 或 3rd party sale | ✅ Confirmed |
| `fcl_closed` | 法拍案件关闭日期 | SLS 系统 | 直接上报 | DATE | `2024-06-01` | — | FCL 生命周期终点 | ✅ Confirmed |
| `fcl_days` | 法拍流程历经总天数 | SLS 系统 | 直接上报（或系统计算） | INT | `210` | — | FNMA timeline 合规基准 | ✅ Confirmed |
| `fcl_days_variance_to_fnma` | 实际 FCL 天数与 FNMA 规定标准的差值（正数 = 超期） | SLS 系统 | 直接上报（或系统计算） | INT | `+45`, `-10` | `fcl_days` | FCL 合规监控；超期可能触发 FNMA 处罚 | ✅ Confirmed |
| `fcl_sale_amount` | 法拍拍卖成交价 | SLS 系统 | 直接上报 | DECIMAL(32,16) | `175000.00` | — | Loss Severity = `(UPB - fcl_sale_amount) / UPB` | ✅ Confirmed |
| `fcl_bid_amount` | 投资人出价（通常用于确定底价） | SLS 系统 | 直接上报 | DECIMAL(32,16) | `165000.00` | — | 底价策略分析 | ✅ Confirmed |
| `fcl_3rd_party_sold_flag` | 是否拍卖给第三方（非投资人自持） | SLS 系统 | 直接上报 | DATE（疑 typo，实际应为 VARCHAR） | `Y`, `N` | — | 区分 REO vs 3rd party sale | 🔶 Weak Inference（字段类型为 DATE，疑为数据建模错误） |
| `fcl_current_status_desc` | 当前法拍状态描述 | SLS 系统 | 直接上报 | TEXT | `"Referral Sent"`, `"Sale Scheduled"` | — | 法拍状态监控面板 | ✅ Confirmed |
| `fcl_type_code` | 法拍类型代码（judicial/non-judicial） | SLS 系统 | 直接上报 | VARCHAR(255) | `J`（Judicial）, `NJ`（Non-Judicial） | — | 州级法拍流程判断；judicial 州耗时更长 | 🟡 Strong Inference |
| `fcl_sequence_number` | 同一贷款的第几次法拍（首次/再次） | SLS 系统 | 直接上报 | INT | `1`, `2` | — | 区分再次法拍贷款 | 🟡 Strong Inference |

---

### 表 04：`sls.portbkdaily` — SLS Bankruptcy

| 属性 | 值 |
|------|----|
| **表名** | `portbkdaily` |
| **所属 Schema** | MySQL `sls` |
| **数据层** | Raw / Servicer-specific |
| **业务作用** | 存储 SLS 上报的破产案件详情，包含破产章节、关键日期、MFR（解除暂停令）申请状态 |
| **业务意图** | 破产触发"自动暂停（Automatic Stay）"，法拍必须暂停。本表追踪 BK 的进展，判断何时可恢复法拍 |
| **上游来源** | SLS 系统每日上报 |
| **下游使用** | 逾期风险分析；`czeng.risk_panel_delinq` 中的 `bankruptcy_ind` 字段 |
| **Foreclosure 关系** | 间接：BK 期间法拍自动暂停；MFR 成功后法拍恢复 |
| **Servicer-specific** | 是（仅 SLS） |

#### 字段说明

| 字段名 | 字段业务含义 | 来源数据 | 计算/推导逻辑 | 数据类型 | 典型取值 | 上游字段 | 下游用途 | 备注 |
|--------|------------|---------|--------------|---------|---------|---------|---------|------|
| `account_number` | SLS 内部贷款账号 | SLS 系统 | 直接上报 | INT | `12345678` | — | join key | ✅ Confirmed |
| `bk_active_flag` | 破产案件是否活跃 | SLS 系统 | 直接上报 | VARCHAR(255) | `Y`, `N` | — | 识别活跃 BK；BK 活跃期间 FC 暂停 | ✅ Confirmed |
| `bk_filed_date` | 破产申请日期 | SLS 系统 | 直接上报 | DATE | `2023-10-01` | — | BK 持续时间计算 | ✅ Confirmed |
| `bk_chapter_code` | 破产章节（7/11/13） | SLS 系统 | 直接上报 | VARCHAR(255) | `7`, `13` | — | Chapter 7=清算，Chapter 13=还款计划；影响法拍推进策略 | ✅ Confirmed |
| `bk_mfr_requested_date` | MFR（Motion for Relief from Stay）申请日期 | SLS 系统 | 直接上报 | DATE | `2023-11-15` | — | MFR 是 BK 期间推进法拍的法律手段；申请后法院决定是否解除暂停令 | ✅ Confirmed |
| `bk_mfr_filed_date` | MFR 正式提交法院日期 | SLS 系统 | 直接上报 | DATE | `2023-11-20` | — | — | ✅ Confirmed |
| `bk_mfr_granted_date` | MFR 获批日期（法院同意解除暂停令，法拍可恢复） | SLS 系统 | 直接上报 | DATE | `2023-12-15` | — | **关键节点**：此日期后法拍可恢复推进 | ✅ Confirmed |
| `bk_dismissal_date` | 破产案件被驳回日期 | SLS 系统 | 直接上报 | DATE | `2024-01-01` | — | 驳回后自动暂停令失效，法拍可恢复 | ✅ Confirmed |
| `bk_discharged_date` | 破产免除日期（Chapter 7 债务被免除） | SLS 系统 | 直接上报 | DATE | `2024-02-01` | — | 免除后借款人个人债务消失，但房产担保仍在；法拍仍可继续 | ✅ Confirmed |
| `bk_case_closed_date` | 破产案件关闭日期 | SLS 系统 | 直接上报 | DATE | `2024-03-01` | — | BK 生命周期终点 | ✅ Confirmed |
| `fcl_days_in_bankruptcy` | 法拍流程在 BK 期间被冻结的天数 | SLS 系统 | 直接上报（或计算） | VARCHAR(255) | `45`, `120` | — | FNMA timeline 豁免计算：BK 天数从 FCL 天数中扣除 | 🟡 Strong Inference |
| `bk_poc_filed_date` | Proof of Claim 提交日期（债权申报） | SLS 系统 | 直接上报 | DATE | `2023-10-15` | — | BK Chapter 13 还款计划中投资人的债权申报 | ✅ Confirmed |
| `bk_confirmation_date` | 还款计划确认日期（法院批准 Chapter 13 计划） | SLS 系统 | 直接上报 | DATE | `2024-01-15` | — | 确认后借款人按计划还款；否则 BK 可能被驳回 | ✅ Confirmed |

---

### 表 05：`sls.portlmdaily` — SLS Loss Mitigation

| 属性 | 值 |
|------|----|
| **表名** | `portlmdaily` |
| **所属 Schema** | MySQL `sls` |
| **数据层** | Raw / Servicer-specific |
| **业务作用** | 存储 SLS 上报的损失减缓（Loss Mitigation）评估和修改协议详情，包含 forbearance、trial period、modification terms |
| **业务意图** | LM 是法拍的替代方案。本表追踪 LM 全流程，支持 CFPB/FNMA 合规监控（如评估完成时效要求） |
| **上游来源** | SLS 系统每日上报 |
| **下游使用** | LM 报告；`port.basic_data_daily_loan_common` 的 `lm_flag` | 
| **Foreclosure 关系** | LM 活跃期间，法拍通常暂停或不得启动（CFPB 双轨制规则） |
| **Servicer-specific** | 是（仅 SLS） |

#### 字段说明（核心字段）

| 字段名 | 字段业务含义 | 来源数据 | 计算/推导逻辑 | 数据类型 | 典型取值 | 上游字段 | 下游用途 | 备注 |
|--------|------------|---------|--------------|---------|---------|---------|---------|------|
| `account_number` | SLS 贷款账号 | SLS 系统 | 直接上报 | BIGINT | — | — | join key | ✅ Confirmed |
| `loss_mit_evaluation_status` | 当前 LM 评估状态 | SLS 系统 | 直接上报 | VARCHAR(255) | `Approved`, `Denied`, `Pending`, `Cancelled` | — | LM 追踪；`Pending` 期间通常不得推进法拍 | ✅ Confirmed |
| `loss_mit_workout_type_code_desc` | LM 方案类型描述 | SLS 系统 | 直接上报 | TEXT | `Loan Modification`, `Forbearance`, `Repayment Plan`, `Short Sale`, `Deed-in-Lieu` | — | LM 方案分类统计 | ✅ Confirmed |
| `loss_mit_application_start_date` | LM 申请开始日期 | SLS 系统 | 直接上报 | DATETIME | `2023-09-01` | — | CFPB 合规：收到完整申请后X天内完成评估 | ✅ Confirmed |
| `loss_mit_application_end_date` | LM 申请结束日期 | SLS 系统 | 直接上报 | DATETIME | `2023-11-01` | — | — | ✅ Confirmed |
| `loss_mit_decision_effective_date` | LM 决策生效日期 | SLS 系统 | 直接上报 | DATETIME | `2023-11-15` | — | — | ✅ Confirmed |
| `loss_mit_workout_trial_first_payment_date` | Trial Period 首次还款日期 | SLS 系统 | 直接上报 | DATETIME | `2023-12-01` | — | Trial Period 是正式修改前的试用期（通常3个月） | ✅ Confirmed |
| `workout_completed_date` | LM 方案完成日期 | SLS 系统 | 直接上报 | DATETIME | `2024-02-01` | — | LM 结案；之后贷款状态可能恢复正常或进入法拍 | ✅ Confirmed |
| `loss_mit_decision_passed_flag` | LM 评估是否通过 | SLS 系统 | 直接上报 | VARCHAR(255) | `Y`, `N` | — | — | ✅ Confirmed |
| `loss_mit_mod_unpaid_principal_forbearance_amount` | 递延本金金额（修改条款中的递延部分） | SLS 系统 | 直接上报 | DECIMAL | `20000.00` | — | 贷款修改后实际负债计算 | ✅ Confirmed |
| `loss_mit_mod_terms_modified_interest_rate_percent` | 修改后利率（%） | SLS 系统 | 直接上报 | DECIMAL | `3.50` | — | IRR 重新计算时使用 | ✅ Confirmed |
| `loss_mit_mod_unpaid_principal_forgiveness_amount` | 本金豁免金额（Principal Forgiveness） | SLS 系统 | 直接上报 | DECIMAL | `10000.00` | — | Loss Severity 计算 | ✅ Confirmed |
| `loss_mit_mod_terms_modified_loan_maturity_date` | 修改后到期日 | SLS 系统 | 直接上报 | DATETIME | `2055-01-01` | — | 修改后 IRR 重算 | ✅ Confirmed |
| `loss_mit_mod_terms_modified_scheduled_pi_payment_amount` | 修改后月度 P&I 还款额 | SLS 系统 | 直接上报 | DECIMAL | `950.00` | — | 修改后现金流建模 | ✅ Confirmed |

---

### 表 06：`sls.portassetdaily` — SLS Asset Oversight

| 属性 | 值 |
|------|----|
| **表名** | `portassetdaily` |
| **所属 Schema** | MySQL `sls` |
| **数据层** | Raw / Servicer-specific |
| **业务作用** | SLS 资产监控主表，汇总了每笔贷款的综合状态，包括 FCL/BK/REO 标志、逾期状态、修改信息、联系记录等，是 SLS 数据的综合快照 |
| **业务意图** | 作为 SLS 贷款日度综合状态表，供 `port.basic_data_daily_loan_common` 等 ETL 表 join 使用 |
| **上游来源** | SLS 系统每日上报 |
| **下游使用** | `port.basic_data_daily_loan_common`（通过 `sls.portassetdaily a` join `sls.portstandarddaily s`） |
| **Foreclosure 关系** | 包含 `fcl_active_flag`、`fc_hold_flag`、`bk_active_flag`、`reo_*` 等综合状态标志 |
| **Servicer-specific** | 是（仅 SLS） |

#### 字段说明（Foreclosure 相关）

| 字段名 | 字段业务含义 | 来源数据 | 计算/推导逻辑 | 数据类型 | 典型取值 | 上游字段 | 下游用途 | 备注 |
|--------|------------|---------|--------------|---------|---------|---------|---------|------|
| `account_number_investor` | 投资人贷款号（对应 `loanid`） | SLS 系统 | 直接上报 | VARCHAR(32) | `7727001272` | — | join key | ✅ Confirmed |
| `delq_status_mba` | MBA 标准逾期状态码 | SLS 系统 | 直接上报 | VARCHAR(50) | `Foreclosure`, `Bankruptcy`, `Current`, `30`, `60`, `90`, `120+`, `REO` | — | 映射到 `port.basic_data_daily_loan_common.delq_status` | ✅ Confirmed |
| `fcl_active_flag` | FCL 激活标志 | SLS 系统 | 直接上报 | VARCHAR(1) | `Y`, `N` | — | 识别法拍活跃贷款 | ✅ Confirmed |
| `fc_hold_flag` | FCL Hold 标志（法拍被暂停，等待 LM 评估、BK 解除等） | SLS 系统 | 直接上报 | VARCHAR(4) | `Y`, `N` | — | FCL Hold 管理 | ✅ Confirmed |
| `bk_active_flag` | 破产激活标志 | SLS 系统 | 直接上报 | VARCHAR(1) | `Y`, `N` | — | BK + FCL 并行追踪 | ✅ Confirmed |
| `bk_chapter_code` | 破产章节 | SLS 系统 | 直接上报 | VARCHAR(30) | `7`, `11`, `13` | — | — | ✅ Confirmed |
| `bk_hold_flag` | BK Hold 标志 | SLS 系统 | 直接上报 | VARCHAR(1) | `Y`, `N` | — | — | ✅ Confirmed |
| `reo_start_date` | REO 开始日期（银行接管房产日期） | SLS 系统 | 直接上报 | DATE | `2024-06-01` | — | REO 处置追踪 | ✅ Confirmed |
| `reo_hold_flag` | REO Hold 标志 | SLS 系统 | 直接上报 | VARCHAR(1) | `Y`, `N` | — | REO 暂停出售追踪 | ✅ Confirmed |
| `reo_end_date` | REO 结束日期（房产出售完成） | SLS 系统 | 直接上报 | DATE | `2024-09-01` | — | REO 处置周期 = `reo_end_date - reo_start_date` | ✅ Confirmed |
| `loss_mitigation_status_desc` | LM 状态描述 | SLS 系统 | 直接上报 | TEXT | `Active`, `Completed`, `Denied` | — | LM 综合状态（与 `portlmdaily` 汇总） | ✅ Confirmed |
| `forbearance_flag` | Forbearance 标志 | SLS 系统 | 直接上报 | VARCHAR(255) | `Y`, `N`, `Active` | — | 映射到 `port.basic_data_daily_loan_common.forbearance` | ✅ Confirmed |
| `last_contact_date` | 最后联系日期 | SLS 系统 | 直接上报 | DATE | `2024-06-15` | — | — | ✅ Confirmed |
| `mba_delq_status_paystring` | MBA 逾期状态历史字符串（24月） | SLS 系统 | 直接上报 | VARCHAR(255) | `CCCCCD30D60D90...` | — | 映射到 `port.basic_data_daily_loan_common.paymthist` | ✅ Confirmed |
| `lm_demand_expire_date` | NOI（Demand Letter）到期日 | SLS 系统 | 直接上报 | DATE | `2023-11-30` | — | NOI 到期后若未解决，触发法拍 referral | 🟡 Strong Inference |

---

### 表 07：`sls.portreodaily` — SLS Real Estate Owned

| 属性 | 值 |
|------|----|
| **表名** | `portreodaily` |
| **所属 Schema** | MySQL `sls` |
| **数据层** | Raw / Servicer-specific |
| **业务作用** | 记录法拍后银行/投资人持有的 REO 房产的处置状态和销售信息 |
| **业务意图** | REO 是法拍流程的最后阶段（若无第三方买家），追踪 REO 处置效率和最终回收额 |
| **上游来源** | SLS 系统每日上报 |
| **下游使用** | Loss Severity 分析；REO 销售净收益计算 |
| **Foreclosure 关系** | 直接（FCL 的下游结果之一） |
| **Servicer-specific** | 是（仅 SLS） |

#### 字段说明

| 字段名 | 字段业务含义 | 来源数据 | 计算/推导逻辑 | 数据类型 | 典型取值 | 上游字段 | 下游用途 | 备注 |
|--------|------------|---------|--------------|---------|---------|---------|---------|------|
| `loannumber` | SLS 贷款号 | SLS 系统 | 直接上报 | VARCHAR(255) | — | — | join key | ✅ Confirmed |
| `vacancydate` | 房产空置日期（借款人迁出日） | SLS 系统 | 直接上报 | DATE | `2024-06-15` | — | 占用状态追踪；驱逐程序依据 | ✅ Confirmed |
| `reosalesprice` | REO 实际销售价格 | SLS 系统 | 直接上报 | VARCHAR(255) | `165000` | — | Loss Severity = `(UPB - reonetsalesproceeds) / UPB` | ✅ Confirmed |
| `reonetsalesproceeds` | REO 销售净收益（扣除销售成本后） | SLS 系统 | 直接上报 | VARCHAR(255) | `155000` | — | 实际回收额计算 | ✅ Confirmed |
| `daysinreo` | REO 持有天数（从银行接管到出售） | SLS 系统 | 直接上报或计算 | VARCHAR(255) | `120` | — | REO 处置效率分析 | ✅ Confirmed |
| `actualclosingdate` | REO 实际成交日期 | SLS 系统 | 直接上报 | DATE | `2024-09-01` | — | — | ✅ Confirmed |
| `scheduledclosingdate` | REO 预定成交日 | SLS 系统 | 直接上报 | DATE | `2024-08-15` | — | — | ✅ Confirmed |
| `listdate` | 房产上市日期 | SLS 系统 | 直接上报 | DATE | `2024-07-01` | — | REO 营销周期 = `listdate` 到 `actualclosingdate` | ✅ Confirmed |
| `reovendor` | REO 处置中介/机构 | SLS 系统 | 直接上报 | VARCHAR(255) | `Altisource`, `FirstAm` | — | 供应商绩效分析 | ✅ Confirmed |
| `cashforkeysamount` | Cash for Keys 金额（支付借款人主动迁出的补偿） | SLS 系统 | 直接上报 | VARCHAR(255) | `3000` | — | REO 处置成本 | ✅ Confirmed |
| `evictcompletedate` | 驱逐完成日期 | SLS 系统 | 直接上报 | DATE | `2024-06-30` | — | 若 borrower 不主动迁出则进入驱逐程序 | ✅ Confirmed |

---

### 表 08：`newrez.portnewrezfc` — Shellpoint/Newrez Foreclosure

| 属性 | 值 |
|------|----|
| **表名** | `portnewrezfc` |
| **所属 Schema** | MySQL `newrez`（原 `shellpoint`，2024-07-05 迁移） |
| **数据层** | Raw / Servicer-specific |
| **业务作用** | Shellpoint/Newrez 的法拍流程追踪表，包含法拍阶段（stage）、里程碑节点、Hold 原因和拍卖信息 |
| **业务意图** | 与 SLS 的 `portfcldaily` 类似，但字段名称和结构不同，反映 Shellpoint 的系统设计 |
| **上游来源** | Newrez/Shellpoint 系统每日上报 |
| **下游使用** | FCL timeline 分析（Newrez 贷款）；`port.basic_data_daily_loan_common` 的 `fcl_flag` 目前未从此表读取 |
| **Foreclosure 关系** | 直接 |
| **Servicer-specific** | 是（仅 Shellpoint/Newrez） |

#### 字段说明

| 字段名 | 字段业务含义 | 来源数据 | 计算/推导逻辑 | 数据类型 | 典型取值 | 上游字段 | 下游用途 | 备注 |
|--------|------------|---------|--------------|---------|---------|---------|---------|------|
| `loanid` | 投资人贷款ID | Newrez 系统 | 直接上报 | VARCHAR(255) | `7727001272` | — | join key | ✅ Confirmed |
| `asofdate` | 数据截止日 | Newrez 系统 | 直接上报 | DATE | `2024-07-30` | — | — | ✅ Confirmed |
| `activefcflag` | 法拍激活标志（整数） | Newrez 系统 | 直接上报 | INT | `1`（激活）, `0`（未激活） | — | 识别活跃法拍 | ✅ Confirmed |
| `fcsetupdate` | 法拍案件建立日期 | Newrez 系统 | 直接上报 | DATE | `2023-11-01` | — | 法拍启动时间点 | ✅ Confirmed |
| `fcreferraldate` | **FCL Referral 日期（委托律师）** | Newrez 系统 | 直接上报 | DATE | `2023-11-15` | — | 与 SLS `fcl_referred_to_attorney_date` 对应；FCL timeline 起点 | ✅ Confirmed |
| `smsdaysinfc` | 系统记录的法拍已历天数（SMS系统口径） | Newrez 系统 | 直接上报 | INT | `210` | — | FNMA timeline 合规 | 🟡 Strong Inference（SMS = Shellpoint Management System） |
| `daysinfc` | 法拍已历天数（另一口径） | Newrez 系统 | 直接上报 | INT | `215` | — | — | 🟡 Strong Inference |
| `fcstage` | 法拍当前阶段描述 | Newrez 系统 | 直接上报 | VARCHAR(255) | `Referral`, `First Legal`, `Service`, `Judgment`, `Sale Scheduled` | — | 法拍状态面板 | ✅ Confirmed |
| `lastfcstepcompleted` | 最后完成的法拍步骤 | Newrez 系统 | 直接上报 | VARCHAR(255) | `First Legal`, `Service Complete` | — | 里程碑追踪 | ✅ Confirmed |
| `lastfcstepcompleteddate` | 最后完成步骤的日期 | Newrez 系统 | 直接上报 | DATE | `2024-02-01` | — | — | ✅ Confirmed |
| `fchold1description` | 第1个 Hold 原因描述 | Newrez 系统 | 直接上报 | VARCHAR(255) | `Loss Mitigation`, `Bankruptcy`, `Litigated` | — | FCL Hold 管理；多个 Hold 并发 | ✅ Confirmed |
| `fchold1startdate` | Hold 1 开始日期 | Newrez 系统 | 直接上报 | DATE | `2024-01-01` | — | — | ✅ Confirmed |
| `fchold1enddate` | Hold 1 结束日期 | Newrez 系统 | 直接上报 | DATE | `2024-03-01` | — | Hold 持续时间计算 | ✅ Confirmed |
| `fchold2description` | 第2个 Hold 原因 | Newrez 系统 | 直接上报 | VARCHAR(255) | — | — | — | ✅ Confirmed |
| `firstlegaldate` | 第一次法律行动日期 | Newrez 系统 | 直接上报 | DATE | `2023-12-01` | — | 与 SLS `fcl_first_legal_action_date` 对应 | ✅ Confirmed |
| `servicecompletedate` | 送达完成日期 | Newrez 系统 | 直接上报 | DATE | `2024-01-15` | — | — | ✅ Confirmed |
| `fcjudgmententered` | 法院裁定法拍日期 | Newrez 系统 | 直接上报 | DATE | `2024-03-01` | — | Judicial 州必须 | ✅ Confirmed |
| `fcscheduledsaledate` | 法拍拍卖预定日 | Newrez 系统 | 直接上报 | DATE | `2024-05-15` | — | — | ✅ Confirmed |
| `fcsalehelddate` | 拍卖实际执行日 | Newrez 系统 | 直接上报 | DATE | `2024-05-15` | — | — | ✅ Confirmed |
| `fcsaleamount` | 拍卖成交价 | Newrez 系统 | 直接上报 | DECIMAL(32,16) | `170000.00` | — | Loss Severity | ✅ Confirmed |
| `fcbidamount` | 投资人出价 | Newrez 系统 | 直接上报 | DECIMAL(32,16) | `160000.00` | — | 底价策略 | ✅ Confirmed |
| `fcresults` | 法拍结果描述 | Newrez 系统 | 直接上报 | VARCHAR(255) | `3rd Party Sale`, `REO`, `Redemption` | — | 法拍结果分类 | ✅ Confirmed |
| `fccontestedflag` | 是否有争议的法拍（借款人提出法律挑战） | Newrez 系统 | 直接上报 | INT | `1`（有争议）, `0` | — | 争议法拍通常大幅延期 | ✅ Confirmed |
| `judicial` | 是否为 Judicial 州（法拍需法院程序） | Newrez 系统 | 直接上报 | INT | `1`, `0` | — | 影响法拍耗时 | ✅ Confirmed |
| `titleordereddate` | 产权报告委托日期 | Newrez 系统 | 直接上报 | DATE | `2023-11-20` | — | 产权清晰是法拍成立的前提 | ✅ Confirmed |
| `titlecleardate` | 产权清晰确认日期 | Newrez 系统 | 直接上报 | DATE | `2023-12-15` | — | — | ✅ Confirmed |

---

### 表 09：`newrez.portnewrezbk` — Shellpoint Bankruptcy

| 属性 | 值 |
|------|----|
| **表名** | `portnewrezbk` |
| **所属 Schema** | MySQL `newrez`（原 `shellpoint`） |
| **数据层** | Raw / Servicer-specific |
| **业务作用** | Shellpoint/Newrez 的破产案件追踪表 |
| **业务意图** | 与 SLS `portbkdaily` 对应，但字段名称不同 |
| **上游来源** | Newrez/Shellpoint 系统每日上报 |
| **下游使用** | BK 分析；`port.basic_data_daily_loan_common_clean` 的 `bankruptcy` 字段（通过 `svcdelinq like '%Bankruptcy%'` 推断）|
| **Foreclosure 关系** | 间接（BK 期间法拍暂停） |
| **Servicer-specific** | 是（仅 Shellpoint/Newrez） |

#### 字段说明（关键字段）

| 字段名 | 字段业务含义 | 来源数据 | 计算/推导逻辑 | 数据类型 | 典型取值 | 上游字段 | 下游用途 | 备注 |
|--------|------------|---------|--------------|---------|---------|---------|---------|------|
| `activebkflag` | 破产激活标志 | Newrez 系统 | 直接上报 | INT | `1`, `0` | — | 识别活跃 BK | ✅ Confirmed |
| `bkfileddate` | 破产申请日期 | Newrez 系统 | 直接上报 | DATE | `2023-10-01` | — | — | ✅ Confirmed |
| `bkchapter` | 破产章节 | Newrez 系统 | 直接上报 | INT | `7`, `13` | — | — | ✅ Confirmed |
| `bkcasenumber` | 破产案件号 | Newrez 系统 | 直接上报 | VARCHAR(255) | `23-12345` | — | 法院查询 | ✅ Confirmed |
| `mfrfileddate` | MFR 提交日期 | Newrez 系统 | 直接上报 | DATE | `2023-11-20` | — | — | ✅ Confirmed |
| `mfrgranteddate` | MFR 获批日期 | Newrez 系统 | 直接上报 | DATE | `2023-12-15` | — | 获批后法拍可恢复 | ✅ Confirmed |
| `dischargeddate` | 破产免除日 | Newrez 系统 | 直接上报 | DATE | — | — | — | ✅ Confirmed |
| `dismisseddate` | 破产驳回日 | Newrez 系统 | 直接上报 | DATE | — | — | — | ✅ Confirmed |
| `pocfileddate` | Proof of Claim 提交日 | Newrez 系统 | 直接上报 | DATE | — | — | — | ✅ Confirmed |
| `planconfirmationdate` | 还款计划确认日（Chapter 13） | Newrez 系统 | 直接上报 | DATE | — | — | — | ✅ Confirmed |

---

### 表 10：`newrez.portnewrezlm` — Shellpoint Loss Mitigation

| 属性 | 值 |
|------|----|
| **表名** | `portnewrezlm` |
| **所属 Schema** | MySQL `newrez`（原 `shellpoint`） |
| **数据层** | Raw / Servicer-specific |
| **业务作用** | Shellpoint/Newrez 的 LM 状态追踪表（forbearance、trial period、repayment plan 等） |
| **业务意图** | 与 SLS `portlmdaily` 对应，追踪 LM 流程中的关键时间节点和当前状态 |
| **上游来源** | Newrez/Shellpoint 系统每日上报 |
| **下游使用** | `port.basic_data_daily_loan_common` 的 `lm_flag`（通过 `activelmflag = '1'` 推断）；`port.basic_data_daily_loan_common` 的 `forbearance` 字段 |
| **Foreclosure 关系** | LM 期间法拍暂停（CFPB dual-track 规则） |
| **Servicer-specific** | 是（仅 Shellpoint/Newrez） |

#### 字段说明（关键字段）

| 字段名 | 字段业务含义 | 来源数据 | 计算/推导逻辑 | 数据类型 | 典型取值 | 上游字段 | 下游用途 | 备注 |
|--------|------------|---------|--------------|---------|---------|---------|---------|------|
| `activelmflag` | LM 激活标志 | Newrez 系统 | 直接上报 | INT | `1`（激活）, `0` | — | 映射到 `port.basic_data_daily_loan_common.lm_flag`：`'1'`→`'Y'` | ✅ Confirmed |
| `forbearancestatus` | Forbearance 状态码 | Newrez 系统 | 直接上报 | INT | `0`（Pending）, `1`（Active）, `4`（Satisfied）, `6`（Delinquent）, `9`（Settlement In Full） | — | 在 `port.basic_data_daily_loan_common` 中被翻译为文本 | ✅ Confirmed |
| `forbearancetype` | Forbearance 类型 | Newrez 系统 | 直接上报 | INT | COVID, 常规 | — | — | 🟡 Strong Inference |
| `forbearanceagreementdate` | Forbearance 协议签署日期 | Newrez 系统 | 直接上报 | DATE | — | — | — | ✅ Confirmed |
| `forbearanceendingduedate` | Forbearance 结束应还款日 | Newrez 系统 | 直接上报 | DATE | — | — | Forbearance 到期后需评估 LM 或进入法拍 | ✅ Confirmed |
| `trialagreementdate` | Trial Period 协议签署日 | Newrez 系统 | 直接上报 | DATE | — | — | Trial Period 是正式修改前的3月试用 | ✅ Confirmed |
| `trialstatus` | Trial Period 状态 | Newrez 系统 | 直接上报 | INT | — | — | — | 🟡 Strong Inference |
| `lmdecision` | LM 决策结果 | Newrez 系统 | 直接上报 | INT | — | — | — | 🟡 Strong Inference |

---

### 表 11：`newrez.portnewrezreo` — Shellpoint REO

| 属性 | 值 |
|------|----|
| **表名** | `portnewrezreo` |
| **所属 Schema** | MySQL `newrez`（原 `shellpoint`） |
| **数据层** | Raw / Servicer-specific |
| **业务作用** | Shellpoint/Newrez 的 REO 处置追踪表 |
| **上游来源** | Newrez/Shellpoint 系统每日上报 |
| **下游使用** | REO 处置分析；Loss Severity 计算 |
| **Foreclosure 关系** | 直接（FCL 的结果） |
| **Servicer-specific** | 是（仅 Shellpoint/Newrez） |

#### 字段说明（关键字段）

| 字段名 | 字段业务含义 | 来源数据 | 计算/推导逻辑 | 数据类型 | 典型取值 | 上游字段 | 下游用途 | 备注 |
|--------|------------|---------|--------------|---------|---------|---------|---------|------|
| `activereoflag` | REO 激活标志 | Newrez 系统 | 直接上报 | INT | `1`, `0` | — | — | ✅ Confirmed |
| `reosetupdate` | REO 接管日期 | Newrez 系统 | 直接上报 | DATE | — | — | — | ✅ Confirmed |
| `daysinreo` | REO 持有天数 | Newrez 系统 | 直接上报 | INT | `120` | — | — | ✅ Confirmed |
| `reolistdate` | REO 上市日期 | Newrez 系统 | 直接上报 | DATE | — | — | — | ✅ Confirmed |
| `reolistprice` | REO 挂牌价 | Newrez 系统 | 直接上报 | DECIMAL | — | — | — | ✅ Confirmed |
| `reosalepriceamount` | REO 成交价 | Newrez 系统 | 直接上报 | DECIMAL | — | — | Loss Severity | ✅ Confirmed |
| `reonetsalesprice` | REO 净销售收益 | Newrez 系统 | 直接上报 | DECIMAL | — | — | 实际回收额 | ✅ Confirmed |
| `reoclosedate` | REO 成交日 | Newrez 系统 | 直接上报 | DATE | — | — | — | ✅ Confirmed |
| `reoholdreason` | REO Hold 原因 | Newrez 系统 | 直接上报 | VARCHAR(255) | `Litigation`, `Redemption`, `Eviction` | — | — | ✅ Confirmed |
| `reoredemptionenddate` | 赎回权到期日（借款人有权在此日期前赎回房产） | Newrez 系统 | 直接上报 | DATE | — | — | 部分州有赎回权期 | ✅ Confirmed |
| `reoevictioncompletedate` | 驱逐完成日 | Newrez 系统 | 直接上报 | DATE | — | — | — | ✅ Confirmed |

---

### 表 12：`czeng.risk_panel_delinq` — Delinquency Risk Panel

| 属性 | 值 |
|------|----|
| **表名** | `risk_panel_delinq` |
| **所属 Schema** | Redshift `czeng` |
| **数据层** | Reporting / Analytics |
| **业务作用** | 基于 `port.basic_data_daily_loan_common_clean` 和各 Servicer 的 FCL/BK/LM 数据，生成逾期贷款的综合风险面板，支持资产管理决策 |
| **业务意图** | 为资产管理团队提供每笔逾期贷款（D120P）的动态风险快照，含 FCL referral 状态、LM 追踪、接触记录、风险等级评定 |
| **主要用途** | 资产管理 Dashboard；投资人报告；合规审查；servicer 绩效监控 |
| **上游来源** | `port.basic_data_daily_loan_common_clean`（贷款基础状态）+ Servicer 专属 FC/BK/LM 表 + 接触记录 |
| **下游使用** | 资产管理 Dashboard；Monthly Servicer Review |
| **Foreclosure 关系** | 核心表：直接追踪 FCL referral 日期、NOI 日期、LM 状态 |
| **Servicer-specific** | 否（多 Servicer 汇合） |
| **已知问题** | 表结构来自 `create_risk_panel_delinq.sql`，字段部分为 Strong Inference |

#### 字段说明（关键字段）

| 字段名 | 字段业务含义 | 来源数据 | 计算/推导逻辑 | 数据类型 | 典型取值 | 上游字段 | 下游用途 | 备注 |
|--------|------------|---------|--------------|---------|---------|---------|---------|------|
| `loanid` | 贷款ID | `port.basic_data_daily_loan_common_clean` | 直接映射 | VARCHAR | — | — | join key | ✅ Confirmed |
| `servicer` | 服务商 | `port.basic_data_daily_loan_common_clean` | 直接映射 | VARCHAR | `Newrez`, `Carrington` | — | 按 Servicer 分组分析 | ✅ Confirmed |
| `delinq` | 标准化逾期状态 | `port.basic_data_daily_loan_common_clean` | 直接映射 | VARCHAR | `D120P`, `FCL` | — | 面板过滤主键（通常只看 D120P+） | ✅ Confirmed |
| `fc_referral_date` | FCL Referral 日期（委托律师启动法拍） | Servicer FC 表 | 直接映射 | DATE | `2023-11-15` | `portfcldaily.fcl_referred_to_attorney_date`<br>`portnewrezfc.fcreferraldate` | 核心监控字段：NOI 发出 >60天未 referral = 高风险 | ✅ Confirmed |
| `noi_demand_letter_date` | NOI（Notice of Intent）或 Demand Letter 发出日期 | Servicer 标准日报 | 直接映射 | DATE | `2023-09-15` | `sls.portstandarddaily.lm_demand_expire_date`（推算） | FCL referral 时效检查的起点 | 🟡 Strong Inference |
| `bankruptcy_ind` | 破产标志 | `port.basic_data_daily_loan_common_clean.bankruptcy` | 直接映射 | VARCHAR | `Y`, `N` | `port.basic_data_daily_loan_common_clean.bankruptcy` | BK + FCL 并行分析 | ✅ Confirmed |
| `bk_chapter` | 破产章节 | Servicer BK 表 | 直接映射 | VARCHAR | `7`, `13` | `portbkdaily.bk_chapter_code` | — | ✅ Confirmed |
| `bk_filed_date` | 破产申请日 | Servicer BK 表 | 直接映射 | DATE | — | `portbkdaily.bk_filed_date` | BK 持续时间 | ✅ Confirmed |
| `inlossmit_ind` | LM 激活标志 | `port.basic_data_daily_loan_common_clean.lm_flag` | 直接映射 | VARCHAR | `Y`, `N` | — | LM 追踪 | ✅ Confirmed |
| `lm_plan_active_flag` | LM 计划是否活跃（区别于 LM 评估中） | Servicer LM 表 | 直接映射 | VARCHAR | `Y`, `N` | `portnewrezlm.activelmflag`（推算） | — | 🟡 Strong Inference |
| `contact_attempts_30d` | 过去30天内接触尝试次数 | Servicer 接触记录表 | 聚合计算：30天滚动窗口内 attempt 次数 | INT | `3`, `0` | `portnewrezcontact.mtdoutbound` 等 | CFPB 合规（要求定期接触 D120P 借款人） | 🟡 Strong Inference |
| `risk_tier` | 风险等级（HIGH/LOW） | 计算字段 | 规则推断：如"D120P 且 NOI > 60天且未 referral" → HIGH | VARCHAR | `HIGH`, `LOW` | 多字段组合 | Servicer 管理优先级排序 | 🟡 Strong Inference（规则来自 `create_risk_panel_delinq.sql`） |

---

### 表 13：`port.basic_data_loan_fcl` — FCL 详情运营数据

| 属性 | 值 |
|------|----|
| **表名** | `port.basic_data_loan_fcl` |
| **所属 Schema** | Redshift `port` |
| **数据层** | Layer 2.5 — FCL Detail Staging |
| **业务作用** | 将 Newrez、Carrington、CapeCodFive 三个 Servicer 的 FCL 详情数据 UNION 成统一结构，并 LEFT JOIN Hold 详情表，形成完整的 FCL 运营快照 |
| **业务意图** | 统一多 Servicer 的 FCL 时间线字段，供 `basic_data_loan_foreclosure` 加工消费；保留全历史快照供内部管道使用 |
| **上游来源** | `newrez.portnewrezfc`（UNION）、`carrington.portcarrington`（UNION）、`capecodfive.portcapecodfive_monthly_collections`（UNION）、`port.basic_data_loan_foreclosure_hold_detail`（LEFT JOIN） |
| **下游使用** | `port.basic_data_loan_foreclosure`（INSERT SELECT）、内部快照管道（portmonthbase） |
| **Foreclosure 关系** | 直接：FCL 全阶段时间线和 Hold 详情的综合数据源 |
| **Servicer-specific** | 否（3个Servicer合并），但仅覆盖 Newrez / Carrington / CapeCodFive；其余 7 个 Servicer 不在此表 |
| **数据规模** | 1,836,086 行（全历史追加），最新快照 6,150 行 |
| **更新策略** | 每次重建（DROP + INSERT）；Newrez/Carrington 追加日报，CapeCodFive 月报 |
| **已知限制** | Carrington 和 CapeCodFive 许多时间线字段为 NULL（原始数据缺失）；Hold 详情仅 Newrez 有实质数据；fcstage 含义因 Servicer 不同而异 |

#### 字段说明（共61列，按功能分7组）

**Group 1：基础标识（4列）**

| 字段名 | 字段业务含义 | 来源数据 | 计算/推导逻辑 | 数据类型 | 典型取值 | 上游字段 | 下游用途 | 备注 |
|--------|------------|---------|--------------|---------|---------|---------|---------|------|
| `dataasof` | 数据快照日期 | 3个Servicer | Newrez: 直接取`dataasof`；Carrington: `snap_shot_date`；CapeCodFive: `fctrdt - 1天` | DATE | `2024-11-30` | portnewrezfc.dataasof / portcarrington.snap_shot_date | 时间过滤；join key | ✅ Confirmed |
| `loanid` | Bridger贷款ID | 3个Servicer | 直接映射 | VARCHAR(100) | `7727001272` | portnewrezfc.loanid / portcarrington.loanid / portcapecodfive.bridger_loan_number | 所有下游关联的 join key | ✅ Confirmed |
| `servicer` | 服务商名称（固定字符串） | Hardcoded | 'Newrez' / 'Carrington' / 'Capecodfive' | VARCHAR(11) | `Newrez` | — | 分组过滤；下游 summary_current_step 等 | ✅ Confirmed |
| `svc_loanid` | Servicer 自有贷款号 | 3个Servicer | Newrez: `shellpointloanid`；Carrington: `carrington_ln`；CapeCodFive: `servicer_loan_number` | VARCHAR(255) | `SHP12345678` | portnewrezfc.shellpointloanid 等 | 向 Servicer 对账时使用 | ✅ Confirmed |

**Group 2：FCL 状态与结案（5列）**

| 字段名 | 字段业务含义 | 来源数据 | 计算/推导逻辑 | 数据类型 | 典型取值 | 上游字段 | 下游用途 | 备注 |
|--------|------------|---------|--------------|---------|---------|---------|---------|------|
| `activefcflag` | FCL 激活标志（1=激活，NULL=未激活） | 3个Servicer | Newrez: `CAST(activefcflag AS INT)`；Carrington: `fcl_flag='Active'→1`；CapeCodFive: `foreclosure_flag='Active'→1` | INTEGER | `1` / `NULL` | portnewrezfc.activefcflag | basic_data_loan_foreclosure.summary_foreclosure_status 计算基础 | ✅ Confirmed（Newrez latest: 39/5047 激活，Carrington: 5/718） |
| `fcstage` | FCL 当前阶段描述 | Newrez, Carrington | Newrez: 直接取（Newrez内部流程描述）；Carrington: `fcl_sub_status`；CapeCodFive: NULL | VARCHAR(255) | Newrez: `''`（空串,多数）/ `'Pre-Sale Review 1 (SCRA and PACER Check)'` / `'Service Complete'` / `'Sale Scheduled For'`；Carrington: fcl_sub_status标准码 | portnewrezfc.fcstage / portcarrington.fcl_sub_status | basic_data_loan_foreclosure.summary_current_step | ✅ Confirmed（注意：Newrez 的值是详细内部描述，多数为空串；Carrington 全部非空） |
| `fcresults` | FCL 结案原因描述 | Newrez | Newrez直接取；其他为NULL | VARCHAR(255) | `'REO'` / `'3rd Party'` / `''`（空串） | portnewrezfc.fcresults | 结案原因分析 | ✅ Confirmed（Newrez latest: REO=6, 3rd Party=3，其余4950为空串） |
| `fcremovaldesc` | 退出 FCL 流程的文字说明 | Newrez | 直接取；Carrington/CapeCodFive 为 NULL | VARCHAR(100) | `'Borrower Reinstated'` / `'Loss Mitigation'` / NULL | portnewrezfc.fcremovaldesc | basic_data_loan_foreclosure.summary_foreclosure_status（Closed 状态描述） | ✅ Confirmed |
| `fcremovaldate` | 退出 FCL 流程的日期 | Newrez | 直接取；其他 NULL | DATE | `2024-06-01` / NULL | portnewrezfc.fcremovaldate | 结案时间分析 | ✅ Confirmed |

**Group 3：阶段时间线（17列）**

| 字段名 | 字段业务含义 | 来源数据 | 计算/推导逻辑 | 数据类型 | 典型取值 | 上游字段 | 下游用途 | 备注 |
|--------|------------|---------|--------------|---------|---------|---------|---------|------|
| `noi_date` | 意向通知日（Notice of Intent，正式告知借款人即将进入止赎流程） | CapeCodFive | 直接取；Newrez/Carrington 为 NULL | DATE | `2023-09-01` | portcapecodfive.noi_date | timeline_notice_of_intent_date | ✅ Confirmed（CapeCodFive特有） |
| `fcsetupdate` | FCL 立案/受理日期 | Newrez, Carrington, CapeCodFive | 直接取各Servicer对应字段 | DATE | `2023-08-01` | portnewrezfc.fcreferraldate / portcarrington.fcl_referral_date / portcapecodfive.foreclosure_date_refrd_atty | — | ✅ Confirmed |
| `referral_start_date` | FCL 转交律师日期（止赎时间线正式起点） | Newrez, Carrington, CapeCodFive | 直接取；Newrez latest 97/5047行非空 | DATE | `2023-08-01` | portnewrezfc.fcreferraldate / portcarrington.fcl_referral_date / portcapecodfive.foreclosure_date_refrd_atty | timeline_referred_to_foreclosure_date | ✅ Confirmed（全部3个Servicer均有映射） |
| `demandsentdate` | 催款函（Demand Letter）发出日期 | Newrez | 直接取；Carrington/CapeCodFive 为 NULL | DATE | `2023-06-15` | portnewrezfc.demandsentdate | — | ✅ Confirmed |
| `demandexpirationdate` | 催款函到期日期（到期仍未还款则推进止赎） | Newrez | 直接取；其他 NULL | DATE | `2023-07-15` | portnewrezfc.demandexpirationdate | — | ✅ Confirmed |
| `legal_start_date` | 初次法律行动日期（First Legal Action，司法止赎中为法院立案日） | Newrez, CapeCodFive | 直接取；Carrington 为 NULL；Newrez latest 55/5047行非空 | DATE | `2023-09-15` | portnewrezfc.firstlegaldate / portcapecodfive.foreclosure_first_legal_date | timeline_first_legal_date | ✅ Confirmed |
| `service_start_date` | 法律文件送达完成日期（借款人被正式告知诉状） | Newrez, CapeCodFive | 直接取；Carrington 为 NULL | DATE | `2023-11-01` | portnewrezfc.servicecompletedate / portcapecodfive.foreclosure_service_date | timeline_service_date | ✅ Confirmed |
| `fcjudgment_hearing_scheduled` | 判决听证会计划日期 | Newrez | 直接取；其他 NULL | DATE | `2024-02-15` | portnewrezfc.fcjudgmenthearingscheduled | timeline_judgement_date | ✅ Confirmed |
| `fcjudgment_end_date` | 判决完成日期（法院裁定止赎） | Newrez, CapeCodFive | 直接取；Carrington 为 NULL | DATE | `2024-03-01` | portnewrezfc.fcjudgmententered / portcapecodfive.foreclosure_judgement_date | — | ✅ Confirmed |
| `fcscheduled_sale_date` | 计划拍卖日期（Auction/Sale Date） | Newrez, Carrington, CapeCodFive | 直接取；Newrez latest 16/5047行非空 | DATE | `2024-06-15` | portnewrezfc.fcscheduledsaledate / portcarrington.fcl_scheduled_sale_date / portcapecodfive.foreclosure_date_sale_scheduled | timeline_sale_date_projected_date | ✅ Confirmed |
| `fcsale_held_date` | 实际拍卖执行日期 | Newrez, Carrington, CapeCodFive | 直接取 | DATE | `2024-07-01` | portnewrezfc.fcsalehelddate / portcarrington.fcl_sale_held_date / portcapecodfive.foreclosure_sale_date | timeline_sale_date_held_date | ✅ Confirmed |
| `titleordereddate` | 产权调查委托日期（拍卖前对房产产权进行调查） | Newrez | 直接取；其他 NULL | DATE | `2023-08-15` | portnewrezfc.titleordereddate | — | ✅ Confirmed |
| `titlereceiveddate` | 产权报告收到日期 | Newrez | 直接取；其他 NULL | DATE | `2023-09-01` | portnewrezfc.titlereceiveddate | timeline_title_report_received_date | ✅ Confirmed |
| `titlecleardate` | 产权清理完成日期（产权无争议后可推进拍卖） | Newrez | 直接取；其他 NULL | DATE | `2023-10-01` | portnewrezfc.titlecleardate | timeline_preliminary_title_cleared_date + timeline_final_title_cleared_date（同一字段映射两处） | ✅ Confirmed |
| `dtdeedrecorded` | 产权契约（Deed）登记日期（REO转移后在政府登记） | Newrez | 直接取；其他 NULL | DATE | `2024-08-01` | portnewrezfc.dtdeedrecorded | — | ✅ Confirmed |
| `lastfcstepcompleted` | 最近完成的 FCL 阶段名称（文字描述） | Newrez, CapeCodFive | 直接取；Carrington 为 NULL | VARCHAR(256) | `'Service Complete'` / `'Title Report Received'` / `'Sale Scheduled For'` | portnewrezfc.lastfcstepcompleted / portcapecodfive.most_recent_foreclosure_stage | summary_last_step_completed | ✅ Confirmed |
| `lastfcstepcompleteddate` | 最近完成阶段的日期 | Newrez | 直接取；其他 NULL | DATE | `2024-09-15` | portnewrezfc.lastfcstepcompleteddate | summary_last_step_completed_date | ✅ Confirmed |

**Group 4：耗时计算（2列）**

| 字段名 | 字段业务含义 | 来源数据 | 计算/推导逻辑 | 数据类型 | 典型取值 | 上游字段 | 下游用途 | 备注 |
|--------|------------|---------|--------------|---------|---------|---------|---------|------|
| `svc_days_infc` | Servicer 自报的 FCL 持续天数 | Newrez | Newrez 直接取 `smsdaysinfc`；Carrington/CapeCodFive 为 NULL | DOUBLE PRECISION | `210.0` | portnewrezfc.smsdaysinfc | summary_sms_days_in_fcl | ✅ Confirmed（仅Newrez有值；类型为 double precision） |
| `daysinfc` | 系统计算的 FCL 持续天数 | Newrez, Carrington, CapeCodFive | Newrez: 直接取 `daysinfc`；Carrington/CapeCodFive: `DATEDIFF(day, referral_start_date, dataasof) + 1`（仅 activefcflag=1 时计算，否则 NULL） | DOUBLE PRECISION | `215.0` | portnewrezfc.daysinfc | summary_days_in_fcl | ✅ Confirmed（类型为 double precision，非 integer） |

**Group 5：金额（4列）**

| 字段名 | 字段业务含义 | 来源数据 | 计算/推导逻辑 | 数据类型 | 典型取值 | 上游字段 | 下游用途 | 备注 |
|--------|------------|---------|--------------|---------|---------|---------|---------|------|
| `fcbidamount` | 止赎拍卖出价/底价金额 | Newrez | 直接取；Carrington/CapeCodFive 为 NULL | DOUBLE PRECISION | `165000.00` | portnewrezfc.fcbidamount | bid_approval_bid_amount / summary_foreclosure_bid_amount | ✅ Confirmed（Newrez latest 16/5047行非空） |
| `fcapprbidprice` | 批准的竞价价格 | Newrez | 直接取；其他 NULL | DOUBLE PRECISION | `160000.00` | portnewrezfc.fcapprbidprice | — | ✅ Confirmed |
| `fcsaleamount` | 实际拍卖成交金额 | Newrez | 直接取；其他 NULL | DOUBLE PRECISION | `170000.00` | portnewrezfc.fcsaleamount | summary_foreclosure_sale_amount | ✅ Confirmed |
| `fcl3rdpartyproceedsreceiveddate` | 第三方购买收益到账日期 | Newrez | 直接取；其他 NULL（字段名虽含"amount"语义，实为日期） | DATE | `2024-09-01` | portnewrezfc.fcl3rdpartyproceedsreceiveddate | timeline_third_party_proceeds_received_date | ✅ Confirmed（字段名misleading，实为DATE类型） |

**Group 6：司法属性（5列）**

| 字段名 | 字段业务含义 | 来源数据 | 计算/推导逻辑 | 数据类型 | 典型取值 | 上游字段 | 下游用途 | 备注 |
|--------|------------|---------|--------------|---------|---------|---------|---------|------|
| `judicial` | 是否为司法止赎（需法院程序） | Newrez | 直接取；其他 NULL | VARCHAR(10) | `'1'`=司法，`'0'`=非司法，NULL | portnewrezfc.judicial | summary_judicial_foreclosure（CAST为INTEGER），summary_type（CASE文字转换） | ✅ Confirmed（存为字符串；Newrez 全部 5047 行有值） |
| `fcfirm` | 承办律师事务所名称 | Newrez, Carrington | Newrez: `fcfirm`；Carrington: `fcl_attorney_name`；CapeCodFive: NULL | VARCHAR(255) | `'Smith & Jones Law'` | portnewrezfc.fcfirm / portcarrington.fcl_attorney_name | summary_firm | ✅ Confirmed |
| `fccontestedflag` | 是否有借款人争议诉讼标志 | Newrez | 直接取；其他 NULL | VARCHAR(10) | `'0'`=无，`'1'`=有，NULL | portnewrezfc.fccontestedflag | summary_contested_litigation（CAST为INTEGER） | ✅ Confirmed（存为字符串，下游CAST） |
| `jr_sr_lien_flag` | 初级/高级留置权标志 | Newrez | 直接取；其他 NULL | VARCHAR(10) | — | portnewrezfc.jr_sr_lien_flag | — | ✅ Confirmed |
| `activejnrlienfcflag` | 活跃次级留置权 FCL 标志 | Newrez | 直接取（整数）；其他 NULL | INTEGER | `0`, `1` | portnewrezfc.activejnrlienfcflag | — | ✅ Confirmed |

**Group 7：Hold 详情（24列，4组各6列）**

来源：LEFT JOIN `port.basic_data_loan_foreclosure_hold_detail`（关联条件：`loanid + dataasof`）

> **Hold** 是止赎流程的暂停状态，常见原因包括：破产自动暂停、LM 评估中、法院延期等。一笔贷款同时最多有4个活跃 Hold。Newrez latest 快照 85/5047 行有 Hold 数据。

| 字段名 | 字段业务含义 | 来源数据 | 计算/推导逻辑 | 数据类型 | 典型取值 | 上游字段 | 下游用途 | 备注 |
|--------|------------|---------|--------------|---------|---------|---------|---------|------|
| `fchold1description` | Hold #1 类型名称（止赎暂停的具体原因） | hold_detail | 直接取；Newrez 85/5047行非空 | VARCHAR(256) | `'Loss Mitigation Workout'` / `'Bankruptcy Filed'` / `'Awaiting Funds to Post'` / `'Delinquency Review'` / `'Client Document Execution'` / `'Court Delay'` | hold_detail.fchold1description | FCL Hold管理分析；BPS hold原因上报 | ✅ Confirmed（DB实测Top10：Loss Mitigation Workout居首） |
| `fchold1startdate` | Hold #1 开始日期 | hold_detail | 直接取 | DATE | `2024-01-15` | hold_detail.fchold1startdate | Hold持续时长计算 | ✅ Confirmed |
| `fchold1enddate` | Hold #1 结束日期（NULL = Hold仍活跃） | hold_detail | 直接取；NULL=活跃中 | DATE | `2024-03-01` / NULL | hold_detail.fchold1enddate | Hold完结判断；当前活跃Hold筛选 | ✅ Confirmed |
| `fchold1projectedenddate` | Hold #1 预计结束日期 | hold_detail | 直接取 | DATE | `2024-04-01` | hold_detail.fchold1projectedenddate | Hold预期时间线规划 | ✅ Confirmed |
| `fchold1comment` | Hold #1 备注说明（自由文本） | hold_detail | 直接取 | VARCHAR(1000) | `'BK case 23-12345 auto-stay in effect'` | hold_detail.fchold1comment | Hold详情追踪；审计 | ✅ Confirmed |
| `holdmodified` | Hold #1 记录最后修改日期 | hold_detail | 直接取 | DATE | `2024-02-01` | hold_detail.holdmodified | Hold数据时效性判断 | ✅ Confirmed（类型为 DATE，非 TIMESTAMP） |
| `fchold2description` | Hold #2 类型名称 | hold_detail | 直接取；Hold #2 数据更少 | VARCHAR(256) | `'Loss Mitigation Workout'` / NULL | hold_detail.fchold2description | FCL多重Hold管理 | ✅ Confirmed |
| `fchold2startdate` | Hold #2 开始日期 | hold_detail | 直接取 | DATE | `2024-02-01` / NULL | hold_detail.fchold2startdate | Hold时间线 | ✅ Confirmed |
| `fchold2enddate` | Hold #2 结束日期 | hold_detail | 直接取 | DATE | NULL（多数） | hold_detail.fchold2enddate | Hold完结判断 | ✅ Confirmed |
| `fchold2projectedenddate` | Hold #2 预计结束日期 | hold_detail | 直接取 | DATE | NULL（多数） | hold_detail.fchold2projectedenddate | — | ✅ Confirmed |
| `fchold2comment` | Hold #2 备注 | hold_detail | 直接取 | VARCHAR(1000) | NULL（多数） | hold_detail.fchold2comment | — | ✅ Confirmed |
| `holdmodified2` | Hold #2 记录最后修改日期 | hold_detail | 直接取 | DATE | NULL（多数） | hold_detail.holdmodified2 | — | ✅ Confirmed（DATE类型） |
| `fchold3description` | Hold #3 类型名称 | hold_detail | 直接取；较少出现 | VARCHAR(256) | NULL（多数） | hold_detail.fchold3description | — | ✅ Confirmed |
| `fchold3startdate` | Hold #3 开始日期 | hold_detail | 直接取 | DATE | NULL（多数） | hold_detail.fchold3startdate | — | ✅ Confirmed |
| `fchold3enddate` | Hold #3 结束日期 | hold_detail | 直接取 | DATE | NULL（多数） | hold_detail.fchold3enddate | — | ✅ Confirmed |
| `fchold3projectedenddate` | Hold #3 预计结束日期 | hold_detail | 直接取 | DATE | NULL（多数） | hold_detail.fchold3projectedenddate | — | ✅ Confirmed |
| `fchold3comment` | Hold #3 备注 | hold_detail | 直接取 | VARCHAR(1000) | NULL（多数） | hold_detail.fchold3comment | — | ✅ Confirmed |
| `holdmodified3` | Hold #3 记录最后修改日期 | hold_detail | 直接取 | DATE | NULL（多数） | hold_detail.holdmodified3 | — | ✅ Confirmed（DATE类型） |
| `fchold4description` | Hold #4 类型名称 | hold_detail | 直接取；极少出现 | VARCHAR(256) | NULL（极少有值） | hold_detail.fchold4description | — | ✅ Confirmed |
| `fchold4startdate` | Hold #4 开始日期 | hold_detail | 直接取 | DATE | NULL（极少） | hold_detail.fchold4startdate | — | ✅ Confirmed |
| `fchold4enddate` | Hold #4 结束日期 | hold_detail | 直接取 | DATE | NULL（极少） | hold_detail.fchold4enddate | — | ✅ Confirmed |
| `fchold4projectedenddate` | Hold #4 预计结束日期 | hold_detail | 直接取 | DATE | NULL（极少） | hold_detail.fchold4projectedenddate | — | ✅ Confirmed |
| `fchold4comment` | Hold #4 备注 | hold_detail | 直接取 | VARCHAR(1000) | NULL（极少） | hold_detail.fchold4comment | — | ✅ Confirmed |
| `holdmodified4` | Hold #4 记录最后修改日期 | hold_detail | 直接取 | DATE | NULL（极少） | hold_detail.holdmodified4 | — | ✅ Confirmed（DATE类型） |

---

### 表 14：`port.basic_data_loan_foreclosure` — FCL 业务智能层

| 属性 | 值 |
|------|----|
| **表名** | `port.basic_data_loan_foreclosure` |
| **所属 Schema** | Redshift `port` |
| **数据层** | Layer 3 — FCL Business Intelligence |
| **业务作用** | 从 `basic_data_loan_fcl` 加工而来，统一 FCL 时间线字段命名、加入 SLA 目标字段和状态汇总字段，供 BPS 和下游报告系统消费 |
| **业务意图** | 为 BPS 外部系统和资产管理提供标准化的 FCL 运营数据，支持 SLA 合规监控、竞价审批决策和损失分析 |
| **上游来源** | `port.basic_data_loan_fcl`（INSERT SELECT，只取各 Servicer `MAX(dataasof)` 快照） |
| **下游使用** | BPS 外部系统（`sync_to_bps_config.py` 中 `'5-FORECLOSURE': {'table': 'basic_data_loan_foreclosure'}`）、`asset_management` MySQL |
| **Foreclosure 关系** | 直接：FCL BI 层，BPS 消费的主要 FCL 数据来源 |
| **Servicer-specific** | 否（3个Servicer），同样仅覆盖 Newrez / Carrington / CapeCodFive |
| **数据规模** | 6,150 行（2026-05-25 实测），等于各 Servicer 最新快照贷款数之和 |
| **更新策略** | DROP + INSERT，每次重建，只保留各 Servicer 最新日期快照 |
| **已知限制** | 62列中 30列当前为 NULL（全部 `target_*` 15列 + 全部 `variance_*` 4列 + 5个 `timeline_*` + 3个 `bid_approval_*` + 3个 `summary_*`）；这些是预留的扩展槽位，尚未填充 |

#### 字段说明（共62列，按前缀分组）

> 每行增加**"INSERT状态"**列：✅ = INSERT已填充（可能有实际值）；❌ = 当前为NULL（CREATE TABLE有定义但INSERT未包含）

**基础标识（4列）**

| 字段名 | 字段业务含义 | 来源数据 | 计算/推导逻辑 | 数据类型 | 典型取值 | 上游字段 | INSERT状态 | 备注 |
|--------|------------|---------|--------------|---------|---------|---------|-----------|------|
| `dataasof` | 数据快照日期 | `basic_data_loan_fcl` | `fc.dataasof` | DATE | `2024-11-30` | fcl.dataasof | ✅ | ✅ Confirmed |
| `loanid` | Bridger 贷款 ID | `basic_data_loan_fcl` | `fc.loanid` | VARCHAR(128) | `7727001272` | fcl.loanid | ✅ | ✅ Confirmed |
| `svcloanid` | Servicer 自有贷款号 | `basic_data_loan_fcl` | `fc.svc_loanid` | VARCHAR(64) | `SHP12345678` | fcl.svc_loanid | ✅ | ✅ Confirmed |
| `servicer` | 服务商名称 | `basic_data_loan_fcl` | `fc.servicer` | VARCHAR(128) | `Newrez` | fcl.servicer | ✅ | ✅ Confirmed |

**timeline_*（19列）— FCL 完整阶段时间线**

| 字段名 | 字段业务含义 | 来源（basic_data_loan_fcl字段） | 数据类型 | INSERT状态 | 实际有数据Servicer | 备注 |
|--------|---------|------|------|-----------|---------|------|
| `timeline_notice_of_intent_date` | 意向通知日 | `fc.noi_date` | DATE | ✅ | CapeCodFive | ✅ Confirmed |
| `timeline_notice_of_intent_end_date` | 意向通知截止日 | — | DATE | ❌ NULL | 无 | 预留扩展 |
| `timeline_approved_for_referral_date` | 批准转交日 | — | DATE | ❌ NULL | 无 | 预留扩展 |
| `timeline_referred_to_attorney_date` | 转交律师日 | — | DATE | ❌ NULL | 无 | 预留扩展 |
| `timeline_referred_to_foreclosure_date` | FCL 转交日（Referral 起点） | `fc.referral_start_date` | DATE | ✅ | Newrez, Carrington, CapeCodFive | ✅ Confirmed |
| `timeline_title_report_received_date` | 产权报告收到日 | `fc.titlereceiveddate` | DATE | ✅ | Newrez | ✅ Confirmed |
| `timeline_preliminary_title_cleared_date` | 初步产权清理完成日 | `fc.titlecleardate` | DATE | ✅ | Newrez | ✅ Confirmed |
| `timeline_first_legal_date` | 初次法律行动日 | `fc.legal_start_date` | DATE | ✅ | Newrez, CapeCodFive（Newrez: 55行有值） | ✅ Confirmed |
| `timeline_service_date` | 法律文件送达完成日 | `fc.service_start_date` | DATE | ✅ | Newrez, CapeCodFive | ✅ Confirmed |
| `timeline_publication_date` | 止赎公告发布日 | — | DATE | ❌ NULL | 无 | 预留扩展 |
| `timeline_judgement_hearing_set_date` | 判决听证会设定日 | 计算：`MIN(dataasof) WHERE fcjudgment_hearing_scheduled IS NOT NULL`（LEFT JOIN） | DATE | ✅ | Newrez | ✅ Confirmed |
| `timeline_judgement_date` | 判决日期 | `fc.fcjudgment_hearing_scheduled` | DATE | ✅ | Newrez | ✅ Confirmed |
| `timeline_sale_date_projected_date` | 预计拍卖日 | `fc.fcscheduled_sale_date` | DATE | ✅ | Newrez, Carrington, CapeCodFive | ✅ Confirmed |
| `timeline_sale_date_set_date` | 拍卖日设定日（首次出现日期） | 计算：`MIN(dataasof) WHERE fcscheduled_sale_date IS NOT NULL`（LEFT JOIN） | DATE | ✅ | Newrez, Carrington, CapeCodFive | ✅ Confirmed |
| `timeline_final_title_cleared_date` | 最终产权清理完成日 | `fc.titlecleardate`（与 preliminary 同源） | DATE | ✅ | Newrez | ✅ Confirmed |
| `timeline_sale_date_held_date` | 实际拍卖完成日 | `fc.fcsale_held_date` | DATE | ✅ | Newrez, Carrington, CapeCodFive | ✅ Confirmed |
| `timeline_foreclosure_completed_date` | 止赎完成日 | — | DATE | ❌ NULL | 无 | 预留扩展 |
| `timeline_third_party_sold_date_date` | 第三方购买完成日 | `NULL`（INSERT中显式写入 NULL） | DATE | ✅(NULL) | 无 | INSERT有此列但值为NULL |
| `timeline_third_party_proceeds_received_date` | 第三方收益到账日 | `fc.fcl3rdpartyproceedsreceiveddate` | DATE | ✅ | Newrez | ✅ Confirmed |

**target_*（15列）— SLA 目标天数（全部为 NULL）**

> 当前 INSERT 未填充，DB 实测全部为 NULL（6,150行均为NULL）。字段含义为各 FCL 阶段的 SLA 目标天数，在 CREATE TABLE 的 COMMENT 中标注了预期默认值。

| 字段名 | 字段业务含义 | 数据类型 | 预期默认值 | INSERT状态 |
|--------|---------|---------|----------|-----------|
| `target_notice_of_intent_days` | 意向通知完成目标天数 | INTEGER | 30 | ❌ NULL |
| `target_notice_of_intent_expired_days` | 意向通知有效期目标天数 | INTEGER | 90 | ❌ NULL |
| `target_approved_for_referral_days` | 批准转交目标天数 | INTEGER | 30 | ❌ NULL |
| `target_referred_to_attorney_days` | 转交律师目标天数 | INTEGER | 1 | ❌ NULL |
| `target_referred_to_foreclosure_days` | 转交止赎目标天数 | INTEGER | 1 | ❌ NULL |
| `target_title_report_received_days` | 产权报告收到目标天数 | INTEGER | 30 | ❌ NULL |
| `target_preliminary_title_cleared_days` | 初步产权清理目标天数 | INTEGER | 30 | ❌ NULL |
| `target_first_legal_days` | 初次法律行动目标天数（通常为 FNMA 合规基准） | INTEGER | 120 | ❌ NULL |
| `target_service_days` | 送达完成目标天数 | INTEGER | 90 | ❌ NULL |
| `target_publication_days` | 公告发布目标天数 | INTEGER | 30 | ❌ NULL |
| `target_judgement_hearing_set_days` | 判决听证会设定目标天数 | INTEGER | 120 | ❌ NULL |
| `target_judgement_days` | 判决发布目标天数 | INTEGER | 30 | ❌ NULL |
| `target_sale_date_set_days` | 拍卖日设定目标天数 | INTEGER | 30 | ❌ NULL |
| `target_final_title_cleared_days` | 最终产权清理目标天数 | INTEGER | 5 | ❌ NULL |
| `target_sale_date_held_days` | 实际拍卖目标天数 | INTEGER | 0 | ❌ NULL |

**variance_*（4列）— 破产/Hold 差异指标（全部为 NULL）**

> 当前 INSERT 未填充，DB 实测全部为 NULL。

| 字段名 | 字段业务含义 | 数据类型 | INSERT状态 | 备注 |
|--------|---------|---------|-----------|------|
| `variance_active_bankruptcy` | 当前是否有活跃破产（1=是，0=否） | INTEGER | ❌ NULL | 预留 |
| `variance_completed_bankruptcy` | 是否有已完成破产记录（1=是，0=否） | INTEGER | ❌ NULL | 预留 |
| `variance_estimated_hold_days` | 预计剩余 Hold 天数 | INTEGER | ❌ NULL | 预留 |
| `variance_bankruptcies` | 历史破产申请总次数 | INTEGER | ❌ NULL | 预留 |

**bid_approval_*（4列）— 竞价审批信息（1列已填充）**

| 字段名 | 字段业务含义 | 来源 | 数据类型 | 典型取值 | INSERT状态 | 备注 |
|--------|---------|------|---------|---------|-----------|------|
| `bid_approval_status` | 竞价审批状态 | — | VARCHAR(128) | `Approved` / `Pending` | ❌ NULL | 预留 |
| `bid_approval_sale_date` | 竞价对应的拍卖日期 | — | DATE | — | ❌ NULL | 预留 |
| `bid_approval_bid_amount` | 竞价金额 | `fc.fcbidamount` | NUMERIC(32,16) | `165000.0000000000000000` | ✅ | DB实测 Newrez 16行有值 |
| `bid_approval_loan_resolution_holods` | 贷款处置 Hold 说明（长文本；注意字段名 'holods' 疑为拼写错误，应为 'holds'） | — | VARCHAR(65535) | — | ❌ NULL | 预留 |

**summary_*（16列）— 汇总信息（BPS下游主要消费字段，13列已填充）**

| 字段名 | 字段业务含义 | 来源（计算逻辑） | 数据类型 | 典型取值 | INSERT状态 | 备注 |
|--------|---------|----------------|---------|---------|-----------|------|
| `summary_servicer_number` | 服务商编号标识 | — | VARCHAR(64) | — | ❌ NULL | 预留 |
| `summary_foreclosure_status` | FCL 状态文字描述（BPS 主要消费字段） | `activefcflag=1→'Active Foreclosure'`；`activefcflag=0且fcremovaldesc非空→'Closed Foreclosure:{fcremovaldesc}'`；否则 NULL | VARCHAR(64) | `Active Foreclosure`(44行) / `Closed Foreclosure:Reinstated`(25行) / `Closed Foreclosure:Loss Mitigation`(15行) / `Closed Foreclosure:Paid in Full`(10行) / `Closed Foreclosure:Process Complete`(7行) / `Closed Foreclosure:Deed in Lieu Cmplte`(1行) / NULL(6048行) | ✅ | ✅ Confirmed（DB实测） |
| `summary_completed_foreclosure` | 是否完成止赎标志 | — | INTEGER | — | ❌ NULL | 预留 |
| `summary_foreclosure_bid_amount` | 止赎竞价金额 | `fc.fcbidamount` | NUMERIC(32,16) | `165000.0000000000000000` | ✅ | 仅Newrez 16行有值 |
| `summary_srv_fc_bid_amount` | Servicer 自报竞价金额（与上字段同源） | `fc.fcbidamount` | NUMERIC(32,16) | `165000.0000000000000000` | ✅ | 与 summary_foreclosure_bid_amount 值相同 |
| `summary_foreclosure_sale_amount` | 实际拍卖成交金额 | `fc.fcsaleamount` | NUMERIC(32,16) | `170000.0000000000000000` | ✅ | 仅Newrez |
| `summary_judicial_foreclosure` | 是否司法止赎（0=非司法，1=司法，NULL=未知） | `CAST(CAST(fc.judicial AS float) AS decimal)` | INTEGER | `0` / `1` / NULL | ✅ | Newrez全部5047行有值；DB实测 Judicial=47, Non-Judicial=50（来自 summary_type） |
| `summary_foreclosure_attorney` | 止赎律师姓名 | — | VARCHAR(256) | — | ❌ NULL | 预留 |
| `summary_contested_litigation` | 是否有借款人争议诉讼（0=无，1=有） | `CAST(fc.fccontestedflag AS decimal)` | INTEGER | `0` / `1` | ✅ | 仅Newrez |
| `summary_firm` | 承办律师事务所名称 | `fc.fcfirm` | VARCHAR(256) | `'Smith & Jones Law'` | ✅ | Newrez/Carrington有值 |
| `summary_type` | 司法/非司法止赎类型文字 | `judicial=1→'Judicial'`；`judicial=0→'Non Judicial'`；`judicial=NULL/空→NULL` | VARCHAR(128) | `Judicial`(47行) / `Non Judicial`(50行) / NULL(6053行) | ✅ | DB实测 |
| `summary_sms_days_in_fcl` | Servicer 自报 FCL 持续天数 | `fc.svc_days_infc`（来自 Newrez smsdaysinfc） | INTEGER | `210` | ✅ | 仅Newrez |
| `summary_days_in_fcl` | 系统计算 FCL 持续天数 | `fc.daysinfc` | INTEGER | `215` | ✅ | 全部3个Servicer（activefcflag=1时有值） |
| `summary_current_step` | 当前 FCL 阶段 | `fc.fcstage` | VARCHAR(128) | Newrez: `'Pre-Sale Review 1 (SCRA and PACER Check)'` 等内部描述；Carrington: fcl_sub_status标准码 | ✅ | Newrez/Carrington有值；同 fcstage 的 Servicer 差异 |
| `summary_last_step_completed` | 最近完成的 FCL 阶段名称 | `fc.lastfcstepcompleted` | VARCHAR(256) | `'Service Complete'` / `'Title Report Received'` | ✅ | Newrez/CapeCodFive有值 |
| `summary_last_step_completed_date` | 最近完成阶段的日期 | `fc.lastfcstepcompleteddate` | DATE | `2024-09-15` | ✅ | 仅Newrez |

---

### 表 15：`port.portmonthbase` — 基础月度贷款数据表

| 属性 | 值 |
|------|----|
| **表名** | `port.portmonthbase` |
| **所属 Schema** | Redshift `port`（变量 `REDSHIFT_PORT`） |
| **数据层** | Layer 3 — Monthly Analytics Base |
| **业务作用** | 将 `port.port_daily_clean`（每月 factor date 快照）与 `port.portremit_clean`（月度汇款数据）LEFT JOIN 合并，形成每笔贷款每个月度的综合快照，是 `portmonth` 的直接上游基础表 |
| **业务意图** | 消除日级数据与月级汇款数据的时间粒度差异，为风险分析、收益率计算、服务商对账提供统一月度视图 |
| **上游来源** | `port.port_daily_clean`（主表 a）、`port.portremit_clean`（汇款 b，LEFT JOIN）、`carrington.portcarringtonremit`（Carrington 2023-11-01 特殊补数）、`port.portinterim`（未上 portmonthbase 的过渡 Servicer 贷款） |
| **下游使用** | `port.portmonth`（直接上游）、方向信函报表 (`direction_letter_config.py`)、资金控制基表 (`gen_finacial_control_base_config.py`)、汇款验证流程 |
| **Foreclosure 关系** | 包含 `delinq`、`svcdelinq` 标准化逾期状态；包含 `bankruptcy`、`forbearance`、`lm_flag`；FCL 贷款在此表中 `delinq='FCL'`（实测 279/78,913 行） |
| **Servicer-specific** | 否（6个Servicer合并：Arvest/Newrez/SLS/Carrington/Capecodfive/Interim） |
| **数据规模** | 78,913 行（2023-02-01 ~ 2025-08-01）；最大单 Servicer：Arvest 37,177 行 |
| **更新策略** | 每月 factor date 重建（DROP + CREATE AS SELECT）；生产 flow：`gen_portmonth_v4.py` |
| **源码位置** | `flow/servicer_data/sericer_data_config/portmonth_config_v2.py` Line 6（`GEN_PORTMONTHBASE`） |

#### 字段说明（共120列，按功能分6组）

**Group 1：基础标识（6列）**

| 字段名 | 字段业务含义 | 来源数据 | 计算/推导逻辑 | 数据类型 | 典型取值 | 上游字段 | 下游用途 | 备注 |
|--------|------------|---------|--------------|---------|---------|---------|---------|------|
| `fctrdt` | Factor Date，月度报告截止日（下月1日） | port_daily_clean | 直接取 `a.fctrdt` | DATE | `2025-08-01` | port_daily_clean.fctrdt | 所有时间序列分析的 partition key | ✅ Confirmed；范围 2023-02-01~2025-08-01 |
| `dealid` | 交易/Deal标识符 | port_daily_clean | 直接取 `a.dealid` | VARCHAR(30) | `'WFL001'` | port_daily_clean.dealid | 关联 `d.bid`、`port.portfunding` | ✅ Confirmed |
| `fundingid` | 资金来源标识 | port_daily_clean | 直接取 `a.fundingid` | VARCHAR(50) | `'WFL001'` | port_daily_clean.fundingid | 资金来源分析 | ✅ Confirmed |
| `loanid` | Bridger投资人贷款ID（跨系统主键） | port_daily_clean | 直接取 `a.loanid` | VARCHAR(30) | `'7727001272'` | port_daily_clean.loanid | JOIN key for all downstream tables | ✅ Confirmed |
| `svcloanid` | Servicer内部贷款号 | port_daily_clean | 直接取 `a.svcloanid` | VARCHAR(30) | `'SHP12345678'` | port_daily_clean.svcloanid | 向Servicer对账使用 | ✅ Confirmed |
| `servicer` | 当前服务商名称 | port_daily_clean | 直接取 `a.servicer` | VARCHAR(20) | `'Newrez'` / `'Arvest'` / `'SLS'` / `'Carrington'` / `'Capecodfive'` / `'Interim'` | port_daily_clean.servicer | 分组过滤；Servicer-level分析 | ✅ Confirmed |

**Group 2：逾期/状态（9列）**

| 字段名 | 字段业务含义 | 来源数据 | 计算/推导逻辑 | 数据类型 | 典型取值 | 上游字段 | 下游用途 | 备注 |
|--------|------------|---------|--------------|---------|---------|---------|---------|------|
| `delinq` | **标准化月度逾期状态码（核心字段）** | port_daily_clean | 继承自 `port.basic_data_daily_loan_common_clean.delinq`（5层规则推导） | VARCHAR(10) | `C`(72,796) / `P`(2,288) / `D30`(2,274) / `D60`(480) / `FCL`(279) / `D120P`(403) / `D90`(206) | port_daily_clean.delinq | 所有风险分析、服务费计算的基础状态 | ✅ Confirmed；FCL=279行/78,913行（0.35%） |
| `svcdelinq` | Servicer原始逾期描述（未标准化） | port_daily_clean | 直接取；FCL贷款下主要值：'Foreclosure'(239行) | VARCHAR(30) | `'Foreclosure'`/`'Loss Mitigation'`/`'Current'`/NULL | port_daily_clean.svcdelinq | 逾期原因追溯；Servicer行为分析 | ✅ Confirmed；约49%有值 |
| `monthindelinq` | 连续逾期月数 | port_daily_clean | 直接取；Carrington特殊计算 | INTEGER | `0`~`43` | port_daily_clean.monthindelinq | 逾期深度分析 | ✅ Confirmed |
| `nextduedate` | 下一应还款日 | port_daily_clean | 直接取 `a.nextduedate` | DATE | `2024-08-01` | port_daily_clean.nextduedate | delinq计算（days360基准）；逾期档位判断 | ✅ Confirmed |
| `bankruptcy` | 借款人破产状态 | port_daily_clean | 直接取；Y=破产，N=正常 | VARCHAR(10) | `'N'`(38,842) / `'Y'`(192) | port_daily_clean.bankruptcy | FCL判断（BK中FCL处理差异）；风险分类 | ✅ Confirmed |
| `forbearance` | 宽限协议状态 | port_daily_clean | 直接取；N=无，Y=活跃，Satisfied=完成，Active=活跃 | VARCHAR(100) | `'N'`(47,958) / `'Satisfied'`(151) / `'Y'`(33) / `'Active'`(32) | port_daily_clean.forbearance | LM状态判断；FCL期间hold原因之一 | ✅ Confirmed |
| `modi` | 是否有贷款改期（Y/N） | port_daily_clean | 直接取 | VARCHAR(100) | `'Y'` / `'N'` | port_daily_clean.modi | 修改贷款识别；风险降级分析 | ✅ Confirmed |
| `moditype` | 贷款改期类型 | port_daily_clean | 直接取 | VARCHAR(100) | `'CAP/PERM30-40'` / `'NON-HAMP'` / `'CMSSTRM30-40PD'` | port_daily_clean.moditype | 改期类型分布分析 | ✅ Confirmed（实测top值：CAP/PERM30-40 343行） |
| `modidate` | 贷款改期生效日期 | port_daily_clean | 直接取 | DATE | `2022-05-01` | port_daily_clean.modidate | 改期时间线分析 | ✅ Confirmed |

**Group 3：贷款属性（20列）**

| 字段名 | 字段业务含义 | 来源数据 | 计算/推导逻辑 | 数据类型 | 典型取值 | 上游字段 | 下游用途 | 备注 |
|--------|------------|---------|--------------|---------|---------|---------|---------|------|
| `origdate` | 贷款起始日（签约日） | port_daily_clean | 直接取 | DATE | `2020-03-15` | port_daily_clean.origdate | 贷款年龄计算；队列分析 | ✅ Confirmed |
| `firstpaymtdt` | 首次还款日 | port_daily_clean | 直接取 | DATE | `2020-05-01` | port_daily_clean.firstpaymtdt | loanage计算基准 | ✅ Confirmed |
| `origmaturitydate` | 原始到期日 | port_daily_clean | 直接取；Carrington部分为NULL | DATE | `2050-04-01` / NULL | port_daily_clean.origmaturitydate | 剩余期限计算 | ✅ Confirmed |
| `maturitydate` | 当前到期日（改期后可能调整） | port_daily_clean | 直接取 | DATE | `2050-04-01` | port_daily_clean.maturitydate | remterm计算基准；改期追踪 | ✅ Confirmed |
| `origterm` | 贷款原始期限（月数） | port_daily_clean | 直接取 | INTEGER | `360` / `180` / `240` | port_daily_clean.origterm | 贷款结构分析 | ✅ Confirmed |
| `svcremterm` | Servicer报告的剩余期限（月数） | port_daily_clean | 直接取或计算：`datediff(month, fctrdt, maturitydate)` | INTEGER | `120`~`360` | port_daily_clean.svcremterm | 利率风险分析 | ✅ Confirmed |
| `remterm` | 系统计算剩余期限（月数） | port_daily_clean | 直接取或同svcremterm | INTEGER | `120`~`360` | port_daily_clean.remterm | IRR计算 | ✅ Confirmed |
| `loanage` | 贷款年龄（月数，自firstpaymtdt起） | port_daily_clean | `datediff(month, firstpaymtdt, fctrdt) + 1` | INTEGER | `1`~`100` | port_daily_clean.loanage | 队列分析；prepayment建模 | ✅ Confirmed |
| `origrate` | 原始利率 | port_daily_clean | 直接取 | DOUBLE PRECISION | `3.875` / `4.5` | port_daily_clean.origrate | 利率比较分析 | ✅ Confirmed |
| `intrate` | 当前利率 | port_daily_clean | 直接取；实测范围 0.063~14.75，均值 4.06 | DOUBLE PRECISION | `3.875`~`6.5` | port_daily_clean.intrate | 现金流计算；利率风险 | ✅ Confirmed |
| `amorttype` | 摊还类型（固定/浮动/IO） | port_daily_clean | 直接取 | VARCHAR(50) | `'Fixed'` / `'ARM'` / `'IO'` | port_daily_clean.amorttype | 还款结构分析 | ✅ Confirmed |
| `origamortizeterm` | 原始摊还期（月数） | port_daily_clean | 直接取 | INTEGER | `360` | port_daily_clean.origamortizeterm | 现金流建模 | ✅ Confirmed |
| `amortizeterm` | 当前摊还期（月数） | port_daily_clean | 直接取；改期后可调整 | INTEGER | `360` | port_daily_clean.amortizeterm | 当前现金流建模 | ✅ Confirmed |
| `io` | 是否为只付利息贷款（Y/N） | port_daily_clean | 直接取 | VARCHAR(10) | `'N'` / `'Y'` | port_daily_clean.io | IO期现金流区分 | ✅ Confirmed |
| `iomonth` | IO期剩余月数 | port_daily_clean | 直接取 | INTEGER | `0`~`120` | port_daily_clean.iomonth | IO到期风险分析 | ✅ Confirmed |
| `dscr` | 债务偿还覆盖率（商业贷款） | port_daily_clean | 直接取 | DOUBLE PRECISION | `1.2`~`2.5` | port_daily_clean.dscr | 商业贷款风险评估 | ✅ Confirmed |
| `svcpaymthist` | Servicer提供的还款历史字符串 | port_daily_clean | 直接取 | VARCHAR(255) | `'CCCCCCCCCCCC'` | port_daily_clean.svcpaymthist | 原始还款历史追溯 | ✅ Confirmed（portmonth中加工为paymthist★） |
| `piw` | 免罚款窗口期（Y/N） | port_daily_clean | 直接取 | VARCHAR(10) | `'Y'` / `'N'` | port_daily_clean.piw | 提前还款分析 | ✅ Confirmed |
| `prepaypenalty` | 是否有提前还款罚金（Y/N） | port_daily_clean | 直接取 | VARCHAR(10) | `'Y'` / `'N'` | port_daily_clean.prepaypenalty | 提前还款建模 | ✅ Confirmed |
| `prepaypenaltyterm` | 提前还款罚金期（月数） | port_daily_clean | 直接取 | INTEGER | `36` / `60` | port_daily_clean.prepaypenaltyterm | 提前还款建模 | ✅ Confirmed |

**Group 4：信用与估值（10列）**

| 字段名 | 字段业务含义 | 来源数据 | 计算/推导逻辑 | 数据类型 | 典型取值 | 上游字段 | 下游用途 | 备注 |
|--------|------------|---------|--------------|---------|---------|---------|---------|------|
| `fico` | 原始信用评分 | port_daily_clean | 直接取 | INTEGER | `620`~`800` | port_daily_clean.fico | 信用风险分层；违约概率建模 | ✅ Confirmed |
| `currfico` | 当前信用评分 | port_daily_clean | 直接取 | INTEGER | `600`~`820` | port_daily_clean.currfico | 动态信用风险监控 | ✅ Confirmed |
| `oltv` | 原始LTV（贷款价值比） | port_daily_clean | 直接取；origbal / origbpo | DOUBLE PRECISION | `0.70`~`0.95` | port_daily_clean.oltv | 原始担保覆盖率分析 | ✅ Confirmed |
| `combltv` | 综合LTV（含次级留置权） | port_daily_clean | 直接取 | DOUBLE PRECISION | `0.70`~`1.20` | port_daily_clean.combltv | 综合担保风险 | ✅ Confirmed |
| `dti` | 债务收入比 | port_daily_clean | 直接取 | DOUBLE PRECISION | `0.28`~`0.55` | port_daily_clean.dti | 承保标准验证；违约预测 | ✅ Confirmed |
| `origbpo` | 原始经纪人价值评估 | port_daily_clean | 直接取 | DOUBLE PRECISION | `150000`~`800000` | port_daily_clean.origbpo | portmonth中计算cltv/losssev的基准 | ✅ Confirmed |
| `origbpodate` | 原始BPO评估日期 | port_daily_clean | 直接取 | DATE | `2020-02-01` | port_daily_clean.origbpodate | BPO有效期判断 | ✅ Confirmed |
| `bpo` | 最新BPO（经纪人房产估值） | port_daily_clean | 直接取 | DOUBLE PRECISION | `100000`~`1000000` | port_daily_clean.bpo | 损失估算；FCL回收率计算 | ✅ Confirmed |
| `bpodate` | 最新BPO评估日期 | port_daily_clean | 直接取 | DATE | `2024-06-01` | port_daily_clean.bpodate | BPO时效性判断 | ✅ Confirmed |
| `salesprice` | 原始购买价格 | port_daily_clean | 直接取 | DOUBLE PRECISION | `200000`~`900000` | port_daily_clean.salesprice | HPA基准；资产价值追踪 | ✅ Confirmed |

**Group 5：余额与财务（22列）**

| 字段名 | 字段业务含义 | 来源数据 | 计算/推导逻辑 | 数据类型 | 典型取值 | 上游字段 | 下游用途 | 备注 |
|--------|------------|---------|--------------|---------|---------|---------|---------|------|
| `origbal` | 原始贷款余额 | port_daily_clean | 直接取 `a.origbal` | DOUBLE PRECISION | `200000`~`700000` | port_daily_clean.origbal | 贷款规模基准 | ✅ Confirmed |
| `prevbal` | 上期期末余额 | port_daily_clean | 直接取 `a.prevbal` | DOUBLE PRECISION | `150000`~`680000` | port_daily_clean.prevbal | 月度本金变化计算 | ✅ Confirmed |
| `balance` | 当期期末贷款余额 | port_daily_clean | 直接取 `a.balance`；实测均值 $200,967，范围 $0~$7,200,000 | DOUBLE PRECISION | `0`~`7200000`（avg `200967`） | port_daily_clean.balance | IRR计算；LTV计算；损失估算关键输入 | ✅ Confirmed |
| `invbal` | 投资人账面余额（actual） | port_daily_clean | 直接取 `a.invbal`；Carrington: `balance - principal_payment` | DOUBLE PRECISION | `≈balance` | port_daily_clean.invbal | 投资人回报计算 | ✅ Confirmed |
| `invbalsched` | 投资人应还账面余额（scheduled） | port_daily_clean | 直接取 `a.invbalsched`；Carrington: `balance - current_pmt_amt` | DOUBLE PRECISION | `≈balance` | port_daily_clean.invbalsched | 计划现金流 vs 实际对比 | ✅ Confirmed |
| `deferredprin` | 递延本金（如疫情宽限） | port_daily_clean | 直接取；Carrington: `r.ending_def_prin` | DOUBLE PRECISION | `0`~`30000` | port_daily_clean.deferredprin | 负债还原；FCL回收损失计算 | ✅ Confirmed |
| `deferredint` | 递延利息 | port_daily_clean | 直接取；Carrington: `total_defer_incl_prin - ending_def_prin` | DOUBLE PRECISION | `0`~`5000` | port_daily_clean.deferredint | 递延利息跟踪 | ✅ Confirmed |
| `pandi` | 月度本息应还金额（P&I） | port_daily_clean | 直接取 `a.pandi` | DOUBLE PRECISION | `800`~`3500` | port_daily_clean.pandi | 现金流预期；应付款验证 | ✅ Confirmed |
| `tandi` | 月度本息税险应还（T&I，含税险） | port_daily_clean | 直接取 `a.tandi` | DOUBLE PRECISION | `900`~`4000` | port_daily_clean.tandi | 全额服务费计算 | ✅ Confirmed |
| `piti` | 月度PITI（含本息税险保险） | port_daily_clean | 直接取 `a.piti` | DOUBLE PRECISION | `1000`~`4500` | port_daily_clean.piti | 借款人全额还款能力评估 | ✅ Confirmed |
| `escrowbal` | 托管账户余额 | port_daily_clean | 直接取 `a.escrowbal` | DOUBLE PRECISION | `500`~`8000` | port_daily_clean.escrowbal | 税险代付监控 | ✅ Confirmed |
| `escrowadv` | 累计托管垫付金额 | port_daily_clean | 直接取 `a.escrowadv` | DOUBLE PRECISION | `0`~`50000` | port_daily_clean.escrowadv | 垫付敞口跟踪 | ✅ Confirmed |
| `corpadvrec` | 可追偿企业垫付（Recoverable） | port_daily_clean | 直接取 `a.corpadvrec` | DOUBLE PRECISION | `0`~`100000` | port_daily_clean.corpadvrec | FCL期间垫付成本统计 | ✅ Confirmed |
| `corpadvnonrec` | 不可追偿企业垫付 | port_daily_clean | 直接取 `a.corpadvnonrec` | DOUBLE PRECISION | `0`~`50000` | port_daily_clean.corpadvnonrec | FCL损失计算 | ✅ Confirmed |
| `corpadvtotal` | 企业垫付合计 | port_daily_clean | 直接取 `a.corpadvtotal`；= corpadvrec + corpadvnonrec | DOUBLE PRECISION | `0`~`150000` | port_daily_clean.corpadvtotal | 总垫付风险暴露 | ✅ Confirmed |
| `principalreceived` | 当月实收本金 | portremit_clean | `COALESCE(b.principalreceived, 0)` | DOUBLE PRECISION | `0`~`5000` | portremit_clean.principalreceived | 月度现金流对账 | ✅ Confirmed |
| `interestreceived` | 当月实收利息 | portremit_clean | `COALESCE(b.interestreceived, 0)` | DOUBLE PRECISION | `0`~`3000` | portremit_clean.interestreceived | 月度现金流对账 | ✅ Confirmed |
| `pandireceived` | 当月实收本息合计 | portremit_clean | `COALESCE(b.pandireceived, 0)` | DOUBLE PRECISION | `0`~`5000` | portremit_clean.pandireceived | 还款表现分析 | ✅ Confirmed |
| `escrowadv_chg` | 当月托管垫付变动 | portremit_clean | `COALESCE(b.escrowadv_chg, 0)` | DOUBLE PRECISION | `-500`~`2000` | portremit_clean.escrowadv_chg | 托管垫付月度变动追踪 | ✅ Confirmed |
| `corpadvrec_chg` | 当月可追偿垫付变动 | portremit_clean | `COALESCE(b.corpadvrec_chg, 0)` | DOUBLE PRECISION | `-2000`~`5000` | portremit_clean.corpadvrec_chg | FCL期间垫付变动监控 | ✅ Confirmed |
| `corpadvnonrec_chg` | 当月不可追偿垫付变动 | portremit_clean | `COALESCE(b.corpadvnonrec_chg, 0)` | DOUBLE PRECISION | `-500`~`2000` | portremit_clean.corpadvnonrec_chg | 损失变动追踪 | ✅ Confirmed |
| `corpadvtotal_chg` | 当月垫付总变动 | portremit_clean | `COALESCE(b.corpadvtotal_chg, 0)` | DOUBLE PRECISION | `-2000`~`8000` | portremit_clean.corpadvtotal_chg | 总垫付变动监控 | ✅ Confirmed |

**Group 6：服务费与汇款（11列）**

| 字段名 | 字段业务含义 | 来源数据 | 计算/推导逻辑 | 数据类型 | 典型取值 | 上游字段 | 下游用途 | 备注 |
|--------|------------|---------|--------------|---------|---------|---------|---------|------|
| `servicefee` | 当月服务费 | portremit_clean | `COALESCE(b.servicefee, 0)`；FCL状态下服务费 -110 bps（来自期望值配置） | DOUBLE PRECISION | `50`~`300` | portremit_clean.servicefee | 服务商激励计算；收益率测算 | ✅ Confirmed |
| `otherfees` | 当月其他费用 | portremit_clean | `COALESCE(b.otherfees, 0)` | DOUBLE PRECISION | `0`~`500` | portremit_clean.otherfees | 费用分析 | ✅ Confirmed |
| `subremit` | 次级汇款金额 | portremit_clean | `COALESCE(b.subremit, 0)` | DOUBLE PRECISION | `0`~`2000` | portremit_clean.subremit | 次级现金流分配 | ✅ Confirmed |
| `totremit` | 总汇款金额 | portremit_clean | `COALESCE(totremit, 0)` | DOUBLE PRECISION | `0`~`6000` | portremit_clean.totremit | 月度总汇款对账 | ✅ Confirmed |
| `interimprincipal` | 过渡期本金（Interim Servicer） | port_daily_clean | `COALESCE(interimprincipal, 0)` | DOUBLE PRECISION | `0`（非Interim为0） | port_daily_clean.interimprincipal | Interim Servicer的过渡本金单独跟踪 | ✅ Confirmed |
| `interiminterest` | 过渡期利息 | port_daily_clean | `COALESCE(interiminterest, 0)` | DOUBLE PRECISION | `0` | port_daily_clean.interiminterest | Interim现金流 | ✅ Confirmed |
| `interimcorpadv_chg` | 过渡期可追偿垫付变动 | port_daily_clean | `COALESCE(interimcorpadv_chg, 0)` | DOUBLE PRECISION | `0` | port_daily_clean.interimcorpadv_chg | Interim垫付 | ✅ Confirmed |
| `interimescrowadv_chg` | 过渡期托管垫付变动 | port_daily_clean | `COALESCE(interimescrowadv_chg, 0)` | DOUBLE PRECISION | `0` | port_daily_clean.interimescrowadv_chg | Interim托管 | ✅ Confirmed |
| `interimservicefee` | 过渡期服务费 | port_daily_clean | `COALESCE(interimservicefee, 0)` | DOUBLE PRECISION | `0` | port_daily_clean.interimservicefee | Interim服务费 | ✅ Confirmed |
| `interimotherfees` | 过渡期其他费用 | port_daily_clean | `COALESCE(interimotherfees, 0)` | DOUBLE PRECISION | `0` | port_daily_clean.interimotherfees | Interim其他费 | ✅ Confirmed |
| `interimremit` | 过渡期总汇款 | port_daily_clean | `COALESCE(interimremit, 0)` | DOUBLE PRECISION | `0` | port_daily_clean.interimremit | Interim汇款 | ✅ Confirmed |

**Group 7：其他属性（42列）**

| 字段名 | 字段业务含义 | 来源数据 | 计算/推导逻辑 | 数据类型 | 典型取值 | 上游字段 | 下游用途 | 备注 |
|--------|------------|---------|--------------|---------|---------|---------|---------|------|
| `agency` | 贷款担保机构类型 | port_daily_clean | 直接取 | VARCHAR(30) | `'FNMA'` / `'FHLMC'` / `'GNMA'` / `'Non-Agency'` | port_daily_clean.agency | 机构风险分层；合规报告 | ✅ Confirmed |
| `channel` | 贷款发放渠道 | port_daily_clean | 直接取 | VARCHAR(30) | `'Retail'` / `'Broker'` / `'Correspondent'` | port_daily_clean.channel | 渠道质量分析 | ✅ Confirmed |
| `purpose` | 贷款用途 | port_daily_clean | 直接取 | VARCHAR(50) | `'Purchase'` / `'Refinance'` | port_daily_clean.purpose | 贷款用途分布 | ✅ Confirmed |
| `proptype` | 房产类型 | port_daily_clean | 直接取 | VARCHAR(50) | `'SFR'` / `'Condo'` / `'2-4 Unit'` | port_daily_clean.proptype | 抵押物类型分析 | ✅ Confirmed |
| `occupancy` | 入住状态 | port_daily_clean | 直接取 | VARCHAR(50) | `'Owner Occupied'` / `'Investment'` | port_daily_clean.occupancy | 违约风险分层 | ✅ Confirmed |
| `doctype` | 贷款文件类型 | port_daily_clean | 直接取 | VARCHAR(100) | `'Full Doc'` / `'No Doc'` | port_daily_clean.doctype | 承保质量评估 | ✅ Confirmed |
| `lien` | 留置权顺位 | port_daily_clean | 直接取 | INTEGER | `1` / `2` | port_daily_clean.lien | 担保优先级 | ✅ Confirmed |
| `propaddress` | 房产地址 | port_daily_clean | 直接取 | VARCHAR(255) | `'123 Main St'` | port_daily_clean.propaddress | 资产定位 | ✅ Confirmed |
| `city` | 城市 | port_daily_clean | 直接取 | VARCHAR(50) | `'Los Angeles'` | port_daily_clean.city | 地理分布分析 | ✅ Confirmed |
| `state` | 州代码 | port_daily_clean | 直接取 | VARCHAR(20) | `'CA'` / `'FL'` / `'TX'` | port_daily_clean.state | 地理分布；司法/非司法FCL判断 | ✅ Confirmed |
| `zipcode` | 邮政编码 | port_daily_clean | 直接取 | VARCHAR(20) | `'90001'` | port_daily_clean.zipcode | MSA分析；HPI数据关联 | ✅ Confirmed |
| `msa` | 都市统计区代码 | port_daily_clean | 直接取 | VARCHAR(255) | `'31080'` | port_daily_clean.msa | 区域性房价分析 | ✅ Confirmed |
| `origbpo` | 原始BPO（见Group 4） | — | — | DOUBLE PRECISION | — | — | — | 同Group 4中origbpo |
| `origbpodate` | 原始BPO日期 | — | — | DATE | — | — | — | 同Group 4 |
| `bpo` | 当前BPO | — | — | DOUBLE PRECISION | — | — | — | 同Group 4 |
| `bpodate` | 当前BPO日期 | — | — | DATE | — | — | — | 同Group 4 |
| `salesprice` | 购买价格 | — | — | DOUBLE PRECISION | — | — | — | 同Group 4 |
| `margin` | 浮动利率基差（ARM贷款） | port_daily_clean | 直接取 | DOUBLE PRECISION | `2.25`~`3.5` | port_daily_clean.margin | ARM利率重置计算 | ✅ Confirmed |
| `liferatefloor` | 利率下限 | port_daily_clean | 直接取 | DOUBLE PRECISION | `2.0`~`3.0` | port_daily_clean.liferatefloor | ARM利率区间 | ✅ Confirmed |
| `liferatecap` | 利率上限 | port_daily_clean | 直接取 | DOUBLE PRECISION | `8.0`~`12.0` | port_daily_clean.liferatecap | ARM利率区间 | ✅ Confirmed |
| `lifechgfloor` | 利率变动下限 | port_daily_clean | 直接取 | DOUBLE PRECISION | `-5.0` | port_daily_clean.lifechgfloor | ARM利率调整 | ✅ Confirmed |
| `lifechgcap` | 利率变动上限 | port_daily_clean | 直接取 | DOUBLE PRECISION | `5.0`~`6.0` | port_daily_clean.lifechgcap | ARM利率调整 | ✅ Confirmed |
| `firstcap` | 首次调整上限 | port_daily_clean | 直接取 | DOUBLE PRECISION | `2.0`~`5.0` | port_daily_clean.firstcap | ARM首次重置 | ✅ Confirmed |
| `periodiccap` | 周期调整上限 | port_daily_clean | 直接取 | DOUBLE PRECISION | `1.0`~`2.0` | port_daily_clean.periodiccap | ARM周期重置 | ✅ Confirmed |
| `monthtofirstreset` | 距首次重置月数 | port_daily_clean | 直接取 | INTEGER | `0`~`84` | port_daily_clean.monthtofirstreset | ARM重置时间线 | ✅ Confirmed |
| `firstresetdate` | 首次重置日期 | port_daily_clean | 直接取 | DATE | `2025-03-01` | port_daily_clean.firstresetdate | ARM重置追踪 | ✅ Confirmed |
| `resetfreq` | 重置频率（月） | port_daily_clean | 直接取 | INTEGER | `6` / `12` | port_daily_clean.resetfreq | ARM重置周期 | ✅ Confirmed |
| `prepaypenaltytype` | 提前还款罚金类型 | port_daily_clean | 直接取 | VARCHAR(50) | `'Soft'` / `'Hard'` | port_daily_clean.prepaypenaltytype | 提前还款建模 | ✅ Confirmed |
| `dpa` | 首付援助（Down Payment Assistance） | port_daily_clean | 直接取 | VARCHAR(50) | `'Y'` / `'N'` | port_daily_clean.dpa | 承保质量评估 | ✅ Confirmed |
| `fthb` | 首次购房者（First-Time Home Buyer） | port_daily_clean | 直接取 | VARCHAR(10) | `'Y'` / `'N'` | port_daily_clean.fthb | 借款人风险特征 | ✅ Confirmed |
| `balloon` | 是否气球贷款（Y/N） | port_daily_clean | 直接取 | VARCHAR(10) | `'N'` / `'Y'` | port_daily_clean.balloon | 到期风险识别 | ✅ Confirmed |
| `balloonterm` | 气球贷款期限（月） | port_daily_clean | 直接取 | INTEGER | `60` / `84` | port_daily_clean.balloonterm | 气球期到期分析 | ✅ Confirmed |
| `buydown` | 利率买入点（Y/N） | port_daily_clean | 直接取 | VARCHAR(10) | `'N'` / `'Y'` | port_daily_clean.buydown | 有效利率计算 | ✅ Confirmed |
| `pmiflag` | 是否有私人抵押保险（Y/N） | port_daily_clean | 直接取 | VARCHAR(100) | `'Y'` / `'N'` | port_daily_clean.pmiflag | PMI保费计算 | ✅ Confirmed |
| `pmitype` | PMI类型 | port_daily_clean | 直接取 | VARCHAR(100) | `'Borrower Paid'` / `'Lender Paid'` | port_daily_clean.pmitype | PMI分析 | ✅ Confirmed |
| `pmilevel` | PMI保费率 | port_daily_clean | 直接取 | DOUBLE PRECISION | `0.005`~`0.02` | port_daily_clean.pmilevel | PMI费用计算 | ✅ Confirmed |
| `pmileveladj` | 调整后PMI保费率 | port_daily_clean | 直接取 | DOUBLE PRECISION | `0.005`~`0.02` | port_daily_clean.pmileveladj | PMI调整追踪 | ✅ Confirmed |
| `pmicancel` | PMI是否已取消（Y/N） | port_daily_clean | 直接取 | VARCHAR(10) | `'Y'` / `'N'` | port_daily_clean.pmicancel | PMI状态追踪 | ✅ Confirmed |
| `pmicanceldt` | PMI取消日期 | port_daily_clean | 直接取 | DATE | `2023-05-01` | port_daily_clean.pmicanceldt | PMI生命周期 | ✅ Confirmed |
| `pmiexpirationdt` | PMI到期日期 | port_daily_clean | 直接取 | DATE | `2025-01-01` | port_daily_clean.pmiexpirationdt | PMI到期追踪 | ✅ Confirmed |
| `pminotes` | PMI备注 | port_daily_clean | 直接取 | VARCHAR(255) | — | port_daily_clean.pminotes | PMI说明 | ✅ Confirmed |
| `partialclaim` | 部分求偿金额（HUD部分偿还） | port_daily_clean | 直接取 | DOUBLE PRECISION | `0`~`30000` | port_daily_clean.partialclaim | 政府担保贷款损失计算 | ✅ Confirmed |
| `moreunits` | 房产单元数（多单元住宅） | port_daily_clean | 直接取 | INTEGER | `1`~`4` | port_daily_clean.moreunits | 多单元风险分析 | ✅ Confirmed |
| `indextype` | 利率指数类型（ARM） | port_daily_clean | 直接取 | VARCHAR(100) | `'LIBOR'` / `'SOFR'` / `'Treasury'` | port_daily_clean.indextype | ARM利率基准 | ✅ Confirmed |
| `lm_flag` | 损失缓释激活标志（Y=激活，N=未激活） | port_daily_clean | 直接取 | VARCHAR(10) | `'N'`(27,474) / `'Y'`(565) / NULL(50,874) | port_daily_clean.lm_flag | 损失缓释分析；FCL中LM hold原因 | ✅ Confirmed；portmonth中转换为`inlossmit`★ |
| `lastcontactdate` | 最后联系借款人的日期 | port_daily_clean | 直接取 | DATE | `2024-08-15` | port_daily_clean.lastcontactdate | 客户联系频率合规 | ✅ Confirmed（18,339行非空） |
| `reasonfordefault` | 违约原因描述（自由文本） | port_daily_clean | 直接取 | VARCHAR(5000) | `'Job Loss'` / `'Medical Expense'` | port_daily_clean.reasonfordefault | 违约原因分析；政府报告 | ✅ Confirmed（976行非空）；portmonth中转换为`defaultreason`★ |

---

### 表 16：`port.portmonth` — 增强月度分析表

| 属性 | 值 |
|------|----|
| **表名** | `port.portmonth` |
| **所属 Schema** | Redshift `port`（变量 `REDSHIFT_PORT`） |
| **数据层** | Layer 3 — Monthly Analytics (Enriched) |
| **业务作用** | 在 `portmonthbase`（120列）基础上追加计算型分析字段（HPA、cltv、losssev、paymthist、风险评级、OTS逾期分类等），形成完整月度分析快照，是整个系统最重要的月度宽表，被风险报告/IRR/收益率/BPS/对账流程广泛使用 |
| **业务意图** | 一站式月度贷款分析表，消除下游系统重复计算同类衍生字段的需求；同时承担 portmonthbase 的"加工发布"角色（对外接口为 portmonth，不直接暴露 portmonthbase） |
| **上游来源** | `port.portmonthbase`（经由 `d.portmonthyilin1 → yilin2 → yilin3` 链路加工）、外部 HPI 数据（房价指数）、`port.portmonthlycomment`（批注字段）、`d.portfunding`（trust/risk字段）、`d.bid`（资产信息） |
| **下游使用** | 方向信函报表 `direction_letter_config.py`、财务控制基表 `gen_finacial_control_base_config.py`、IRR分析 `irr.py` / `config_irr.py`、服务商汇款验证 `servicer_validation_*.py`、BPS资产管理 `sync_to_bps_config.py`、MTM贷款摘要 `mtm_loan_summary_risk_data_flow.py`、月度ALIC磁带 `mix_data_monthly_alic_tape_config.py` |
| **Foreclosure 关系** | 包含所有 portmonthbase 的 FCL 字段（delinq、svcdelinq等）+ 额外的：prevdelinq（上月FCL状态变化追踪）、paymthist（FCL轨迹历史字符串）、inlossmit（FCL中LM hold标志）、losssev（FCL损失估算） |
| **Servicer-specific** | 否（6个Servicer合并） |
| **数据规模** | 129,023行（2023-02-01 ~ 2026-06-01）；portmonthbase更新慢于portmonth（portmonthbase截至2025-08） |
| **更新策略** | 每月全量重建（TRUNCATE + INSERT）；生产 flow：`gen_portmonth_v4.py`；中间表 yilin1/yilin2/yilin3 为临时过渡 |
| **源码位置** | `flow/servicer_business/sericer_business_data_config/gen_portmonth_config.py` Line 1405（`GEN_PORTMONTH_DATA`） |
| **与portmonthbase的差异** | 多出23列（★标注），少了 `lm_flag` 和 `reasonfordefault`（已被 `inlossmit`★ 和 `defaultreason`★ 替代） |

#### 字段说明（共141列 = portmonthbase 120列 - 2 + 新增23列★）

> **注**：与 portmonthbase 相同含义的字段（共118列）仅列出差异，详细定义见表15。★标注的字段为 portmonth 独有，portmonthbase 中不存在。

**Group 1：基础标识（6列）** — 与 portmonthbase 完全相同，见表15 Group 1

**Group 2：逾期/状态（12列，portmonth 在 portmonthbase 8列基础上增加4列★）**

| 字段名 | 字段业务含义 | 来源数据 | 计算/推导逻辑 | 数据类型 | 典型取值 | 上游字段 | 下游用途 | 备注 |
|--------|------------|---------|--------------|---------|---------|---------|---------|------|
| `delinq` | 标准化月度逾期状态码 | portmonthbase | 继承 | VARCHAR(10) | C(118,665)/P(5,307)/D30(2,440)/FCL(580) | portmonthbase.delinq | 全系统核心状态字段 | ✅ Confirmed；FCL=580行/129,023行（0.45%） |
| `svcdelinq` | Servicer原始逾期描述 | portmonthbase | 继承（portmonth varchar更宽：100 vs 30） | VARCHAR(100) | `'Foreclosure'`(495行/FCL贷款) | portmonthbase.svcdelinq | 逾期来源追溯 | ✅ Confirmed |
| `★prevdelinq` | **上月逾期状态码（FCL轨迹追踪关键字段）** | portmonthbase(prev月) | JOIN上期portmonth by loanid+prev_fctrdt | VARCHAR(100) | C(120,012)/FCL(550)/P(4,298)/D30(2,355) | portmonth(t-1).delinq | 状态转移分析；FCL进入/退出追踪 | ✅ Confirmed（全量129,023行有值） |
| `★paymthist` | **滚动24个月还款历史字符串（关键合规字段）** | portmonth历史 | 拼接最近24个月delinq代码，如"CCCCCD30D30CCCCCCCCCCCC" | VARCHAR(65535) | `'CCCCCCCCCCCCCCCCCCCCCCCC'`（全当期）/ `'CCCCCCFD30CC...'` | portmonth历史.delinq | MBA/OTS还款历史报告；BPS汇报；对账 | ✅ Confirmed（全量有值） |
| `★ots_delinq` | **OTS口径逾期分类（储贷协会/监管口径）** | portmonthbase | 基于delinq重新分类（OTS标准与MBA标准的差异处理） | VARCHAR(10) | C(121,052)/P(5,307)/FCL(580)/D30(753) | portmonthbase.delinq | OTS/监管报告；多口径一致性分析 | ✅ Confirmed（128,868行有值；与delinq差异3,570行） |
| `★ots_prevdelinq` | 上月OTS口径逾期状态 | portmonthbase(prev月) | 同prevdelinq逻辑，但取OTS口径 | VARCHAR(100) | C(120,012)/FCL(550) | portmonth(t-1).ots_delinq | OTS状态转移分析 | ✅ Confirmed（全量有值） |
| `monthindelinq` | 连续逾期月数 | portmonthbase | 继承（portmonth为DOUBLE PRECISION，portmonthbase为INTEGER） | DOUBLE PRECISION | `0`~`43` | portmonthbase.monthindelinq | 逾期深度分析 | ✅ Confirmed；注意类型差异 |
| `svcpaymthist` | Servicer提供的还款历史 | portmonthbase | 继承（varchar更宽：500 vs 255） | VARCHAR(500) | `'CCCCCCCCCCCC'` | portmonthbase.svcpaymthist | 原始还款历史 | ✅ Confirmed |
| `nextduedate` | 下一应还款日 | portmonthbase | 继承 | DATE | `2024-08-01` | portmonthbase.nextduedate | delinq计算基准 | ✅ Confirmed |
| `bankruptcy` | 破产状态 | portmonthbase | 继承（varchar更宽：20 vs 10） | VARCHAR(20) | `'N'`/`'Y'` | portmonthbase.bankruptcy | FCL处理 | ✅ Confirmed |
| `forbearance` | 宽限协议状态 | portmonthbase | 继承 | VARCHAR(100) | `'N'`/`'Satisfied'`/`'Y'` | portmonthbase.forbearance | LM/FCL hold | ✅ Confirmed |
| `modi` / `moditype` / `modidate` | 改期信息 | portmonthbase | 继承 | VARCHAR/DATE | 同表15 | portmonthbase | 同表15 | ✅ Confirmed |

**Group 3：贷款属性（20列）** — 与 portmonthbase 基本相同，数据类型稍有差异（多为 DOUBLE PRECISION/BIGINT 替代 INTEGER）

> 详见表15 Group 3。主要类型差异：portmonth 中 `origterm`/`origamortizeterm`/`amortizeterm`/`monthtofirstreset`/`resetfreq`/`iomonth`/`prepaypenaltyterm`/`balloonterm`/`moreunits` 等整数字段变为 DOUBLE PRECISION；`loanage`/`svcremterm`/`remterm` 变为 BIGINT。

**Group 4：信用与估值（10列）** — 与 portmonthbase 相同，数据类型稍有差异（`fico`/`currfico` 变为 DOUBLE PRECISION）

> 详见表15 Group 4。

**Group 5：余额与财务（22列）** — 与 portmonthbase 完全相同

> 详见表15 Group 5。

**Group 6：服务费与汇款（14列，portmonth 增加3列★）**

| 字段名 | 字段业务含义 | 来源数据 | 计算/推导逻辑 | 数据类型 | 典型取值 | 上游字段 | 下游用途 | 备注 |
|--------|------------|---------|--------------|---------|---------|---------|---------|------|
| `servicefee`~`interimremit` | 同portmonthbase（11列） | portmonthbase | 继承 | DOUBLE PRECISION | — | portmonthbase | 同表15 | ✅ Confirmed |
| `★loanleveldistribution` | 贷款级别分配金额 | portmonthyilin链路 | 按贷款分配的月度现金流分配金额 | DOUBLE PRECISION | `0`~`5000` | portremit_clean.loanleveldistribution | 现金流分配计算 | ✅ Confirmed |
| `★trust` | 所属信托名称 | portmonthyilin3 | 来自 `d.portfunding` 或 `d.bid` | VARCHAR(100) | `'WFL Trust 2019-1'` | d.portfunding.trust | BPS信托级别报告；信托级现金流分配 | ✅ Confirmed（全量129,023行有值） |
| `★remit_status` | 汇款状态 | portmonthyilin3 | 固定值；全部='cash' | VARCHAR(20) | `'cash'`（129,023行） | — | 汇款类型识别 | ✅ Confirmed（全量='cash'） |

**Group 7：估值/风险指标（11列，portmonth 独有★）**

| 字段名 | 字段业务含义 | 来源数据 | 计算/推导逻辑 | 数据类型 | 典型取值 | 上游字段 | 下游用途 | 备注 |
|--------|------------|---------|--------------|---------|---------|---------|---------|------|
| `★hpa` | **房价涨幅（House Price Appreciation）** | 外部HPI数据 | `current_index / base_index - 1`；基于MSA/ZIP级别的联邦房价指数 | DOUBLE PRECISION | `0.05`~`0.60`（5%~60%涨幅） | 外部HPI数据 | cltv/bpocltv/losssev计算基础；市场风险监控 | ✅ Confirmed（129,000行有值） |
| `★bpo_hpa` | BPO基础的房价涨幅 | BPO + HPI | `bpo / origbpo - 1`（估算） | DOUBLE PRECISION | `0.05`~`0.50` | portmonthbase.bpo / origbpo | BPO精度校验 | ✅ Confirmed |
| `★cltv` | **当前LTV（Current Loan-to-Value）** | portmonthbase + HPI | `balance / (origbpo × (1 + hpa))`；HPA调整后的实时担保覆盖率 | DOUBLE PRECISION | `0.40`~`1.20` | portmonthbase.balance / origbpo / hpa | 损失估算关键输入；FCL回收率预测 | ✅ Confirmed（129,000行有值） |
| `★bpocltv` | BPO基础CLTV | portmonthbase | `balance / bpo`；使用最新BPO而非HPA调整值 | DOUBLE PRECISION | `0.50`~`1.30` | portmonthbase.balance / bpo | 当前担保覆盖率评估（更保守） | ✅ Confirmed |
| `★losssev` | **预估损失率（Loss Severity）** | portmonthbase + HPI | `(balance - bpo × (1-成本率%)) / balance`；FCL回收后的预估损失占比 | DOUBLE PRECISION | `0.10`~`0.60`（10%~60%） | portmonthbase.balance / bpo | IRR计算；FCL损失预测；投资人回报估算 | ✅ Confirmed（仅21行非空；大量NULL） |
| `★nsf` | 净空头寸（Net Shortfall，bpo覆盖不足额） | portmonthbase + HPI | `balance - bpo × (1 - 成本调整系数)` | DOUBLE PRECISION | `-50000`~`100000` | portmonthbase.balance / bpo | 担保覆盖缺口分析；损失敞口监控 | ✅ Confirmed（121,226行非空） |
| `★mainissue` | **风险主因分类（承保/服务风险主要问题）** | d.portfunding / 规则 | 人工标注或规则分类 | CHARACTER(100) | `'Income Miscalculation'`(10,431) / `'Missing Debts'`(5,352) / `'VA Seasoning Issue'`(3,313) / `'ATR Risk'` | d.portfunding.mainissue | 风险归因；合规追踪；诉讼支持 | ✅ Confirmed（51,813行有值） |
| `★secondaryissue` | 风险次因分类 | d.portfunding / 规则 | 同mainissue | CHARACTER(100) | 同mainissue类别 | d.portfunding.secondaryissue | 风险多维归因 | ✅ Confirmed（5,028行有值） |
| `★risktier` | 风险层级评定 | portmonthyilin链路 | 规则引擎或打分卡；综合逾期/BK/LM/信用等因素 | CHARACTER(100) | `'High'` / `'Medium'` / `'Low'` | portmonthbase多字段 | 风险分层管理；服务商绩效评估 | ✅ Confirmed（51,969行有值） |
| `★notes` / `★notes0`~`★notes3` | 批注字段（共5个） | port.portmonthlycomment 或类似 | 直接取；人工/系统生成的月度批注，最多5个 | VARCHAR(5000) | `'BK filed 2024-03-15, FCL on hold'` | port.portmonthlycomment | 操作说明；审计追踪；BPS汇报 | ✅ Confirmed（`notes`为主批注，`notes0`~`notes3`为分层批注） |

**Group 8：损失缓释与其他（6列，包含2个★新字段）**

| 字段名 | 字段业务含义 | 来源数据 | 计算/推导逻辑 | 数据类型 | 典型取值 | 上游字段 | 下游用途 | 备注 |
|--------|------------|---------|--------------|---------|---------|---------|---------|------|
| `★inlossmit` | **是否在损失缓释流程中（Y/N）** | portmonthbase.lm_flag | `CASE WHEN lm_flag = 'Y' THEN 'Y' ELSE 'N' END`（格式化版） | VARCHAR(256) | `'N'`(51,879) / `'Y'`(910) | portmonthbase.lm_flag | FCL中LM hold识别；损失缓释覆盖率报告 | ✅ Confirmed（portmonthbase的`lm_flag`替代字段） |
| `lastcontactdate` | 最后联系借款人日期 | portmonthbase | 继承（portmonthbase中也有） | DATE | `2024-08-15` | portmonthbase.lastcontactdate | 客户联系合规 | ✅ Confirmed（35,917行非空） |
| `★defaultreason` | 违约原因（格式化版） | portmonthbase.reasonfordefault | `reasonfordefault` 格式化/截断版（varchar 256 vs 5000） | VARCHAR(256) | `'Job Loss'` / `'Medical Expense'` | portmonthbase.reasonfordefault | 违约原因简洁展示；BPS报告 | ✅ Confirmed（portmonthbase的`reasonfordefault`替代字段） |
| `agency` ~ `pminotes` | 房产/其他属性（与portmonthbase Group 7 相同，36列） | portmonthbase | 继承 | 同portmonthbase | 同portmonthbase | portmonthbase | 同portmonthbase | ✅ Confirmed |

---

### 表 17：`bpms_dev.sync_loan_foreclosure` — BPS Foreclosure 主应用表

| 属性 | 值 |
|------|----|
| **表名** | `sync_loan_foreclosure` |
| **所属 Schema** | MySQL `bpms_dev`（BPS 应用数据库） |
| **数据层** | Layer 5 — BPS Application Layer（最终展示层） |
| **业务作用** | BPS Foreclosure 管理面板的主数据表，存储每笔贷款的 FCL 全生命周期时间线、SLA 目标天数、差异调整、竞拍审批信息及综合摘要；对应 BPS UI 的5个核心面板：Milestone Timeline / Target Days / Variance / Bid Approval / Summary |
| **业务意图** | 为 BPS Foreclosure 管理界面提供结构化、标准化的数据支撑，供资产经理实时查看贷款 FCL 进展、判断 SLA 合规性、审批竞拍出价 |
| **行数（dev）** | 98 行（95 个 distinct loanid；2家Servicer：Newrez 88行，Carrington 10行） |
| **上游来源** | **由 PrefectFlow 代码写入（已确认，非"来源不明"）**：`sync_asset_management` 的 `5-FORECLOSURE` 分支 → `GEN_FORECLOSURE` 从 Redshift `port.basic_data_loan_foreclosure` 读数 → `sync_to_mysql()` 先 DELETE+INSERT 写 MySQL **staging 表** `port.basic_data_loan_foreclosure` → 随后 `update_to_mysql()` 触发 `UPDATE_FORECLOSURE`：`INSERT INTO sync_loan_foreclosure ... ON DUPLICATE KEY UPDATE`（源 `port.basic_data_loan_foreclosure JOIN port.portfunding WHERE timeline_referred_to_foreclosure_date IS NOT NULL`）。详见「代码血缘」行 |
| **下游使用** | BPS UI 5个面板（Milestone Timeline / Target Days / Variance / Bid Approval / Summary）；视图 `bpms_dev.biz_data_view_loan_details_foreclosure`（表25）以本表为基表实时计算 `actual_*_days`/`var_*_days`。⚠️ 注：`sync_fcl_stage_info`（表24）**不是本表下游**——它是同级 BPS 表，独立由 `12-FCL_STAGE` 从 Redshift `port.fcl_stage_info` 同步 |
| **Foreclosure 关系** | 核心：`timeline_*` 字段驱动时间线面板；`target_*_days` 提供 SLA 基准；`summary_*` 字段驱动综合摘要面板 |
| **已知问题** | ① `actual_*_days`（实际历时天数）**不在本表**——在视图 `biz_data_view_loan_details_foreclosure`（表25）实时计算、阶段口径在 `sync_fcl_stage_info`（表24）；② 列名 `bid_approval_loan_resolution_holods` 含拼写错误（应为 `holds`，已投产无法轻易修改）；③ ~~写入来源未通过 ETL 代码确认~~ **已订正：写入来源已由 PrefectFlow 代码确认**（两步 upsert，见上游来源/代码血缘；推翻 doc 02/12 早期"不在 SYNC_TABLE_MAP/来源不明"的推断）；④ dev 环境多数 `variance_*` / `bid_approval_status` / `summary_servicer_number` / 管理字段（create_*/update_*）实测全为 NULL（未回填） |
| **代码血缘（PrefectFlow）** | 编排 `flow/bps/sync_asset_management.py`（`5-FORECLOSURE`）→ SQL 模板 `flow/bps/bps_config/asset_managment_config.py`：`GEN_FORECLOSURE`(L535)、`UPDATE_FORECLOSURE`(L644，`INSERT INTO sync_loan_foreclosure ... ON DUPLICATE KEY UPDATE`，源 JOIN portfunding + `WHERE timeline_referred_to_foreclosure_date IS NOT NULL` L604-605) → 同步工具 `util/df_db_util.py`：`sync_to_mysql`(L664，staging DELETE+INSERT，`sync_table_name=='basic_data_loan_foreclosure'` 时库为 `port` L675)→`update_to_mysql`(L702，`if sync_table_name=='basic_data_loan_foreclosure'` L710 执行 UPDATE_FORECLOSURE)。Redshift 基表构建 `flow/basic_data/basic_data_config/basic_data_pool_config.py`（CREATE_BASIC_FCL/GEN_FCL_DETAIL）。**写入机制：upsert（ON DUPLICATE KEY UPDATE），区别于子表的 DELETE+INSERT** |
| **MCP验证** | 2026-06-01 重新实测（72列）：INFORMATION_SCHEMA.COLUMNS + 单列 MIN/MAX/COUNT/DISTINCT 全量统计（脚本 `scripts/extract_table_stats.py`，结果 `outputs/table_stats_for_data_dictionary.json`）。⚠️ 本次实测对早期 v4 字段清单做了校正：本表**无 `dataasof` 列**、含自增主键 `id`；timeline 组实际字段为 `judgement_hearing_set_date`/`sale_date_set_date`/`third_party_sold_date_date`（早期误列的 `*_start_date`/`*_completed_date`/`*_proceeds_wired_date` 不存在）；多个字段数据类型已按实测更正。字段清单与 `UPDATE_FORECLOSURE` 的 INSERT 列清单一致（asset_managment_config.py:647+） |

#### Group 1：标识符（6列）

| 字段名 | 字段业务含义 | 来源数据 | 计算/推导逻辑 | 数据类型 | 取值范围 | 典型取值 | 上游字段 | 下游用途 | 备注 |
|--------|------------|---------|--------------|---------|---------|---------|---------|---------|------|
| `id` | 主键，自增 ID | 系统生成 | AUTO_INCREMENT | bigint NOT NULL | `1` ~ `279`（实测98行非连续） | `1` | — | 内部主键（**真正的 PK，非 `bid_id`**） | ✅ Confirmed（MCP 2026-06-01） |
| `bid_id` | Bid/资产业务编号（非自增，文本代码） | BPS 应用层 | 直接写入 | varchar(64) | 实测31种文本码，如 `ACRA005` … `WFL001` | `ACRA005` | — | 竞拍/资产关联键 | 🟡 Strong Inference（类型实测；业务含义待 BPS 确认） |
| `funding_id` | Fund / Funding 编号 | BPS 应用层 | 直接写入 | varchar(256) | 实测34种文本码，如 `2024WS-ARES-4` … `WFL001` | `2024WS-ARES-4` | `port.portfunding.fundingid` | 关联 Funding 维度 | ✅ Confirmed（类型实测为 varchar，非 int） |
| `loanid` | 系统贷款 ID（跨 Servicer 统一标识） | BPS 应用层 | 直接写入 | bigint | `686279936` ~ `700082890000291`（95个distinct） | `7727001272` | `port.basic_data_loan_fcl.loanid` | 全表 join key；关联 FCL 中间表 | ✅ Confirmed（类型实测为 bigint，非 varchar） |
| `svcloanid` | Servicer 内部贷款号 | BPS 应用层 | 直接写入 | varchar(64) | 92种，纯数字字符串如 `0578252925` ~ `9715751096` | `9715751096` | `port.basic_data_loan_fcl.svc_loanid` | Servicer 对账字段 | ✅ Confirmed |
| `servicer` | Servicer 名称 | BPS 应用层 | 直接写入 | varchar(128) | `{Newrez, Carrington}`（2种） | `Newrez` | — | Servicer 分组过滤 | ✅ Confirmed（实测：Newrez 88行 / Carrington 10行） |

#### Group 2：FCL 时间线（`timeline_*`，19列）

> 对应 BPS UI 的 **Milestone Timeline 面板**。日期均为 date 类型，均可为 NULL（事件未发生时为空）。  
> ⚠️ 字段清单按 2026-06-01 实测校正为 19 列（早期误列的 `*_start_date`/`*_completed_date`/`*_proceeds_wired_date` 不存在）。取值范围/填充率来自本表 dev 98 行实测（含历史完结贷款，与 doc 13 活跃-FCL 口径的填充率不同）；上游 Newrez 字段映射见 doc 13 Section 3.1。

| 字段名 | 字段业务含义 | 来源数据 | 计算/推导逻辑 | 数据类型 | 取值范围 | 典型取值 | 上游字段 | 下游用途 | 备注 |
|--------|------------|---------|--------------|---------|---------|---------|---------|---------|------|
| `timeline_notice_of_intent_date` | NOI / Demand 信函发出日 | ETL | 直接映射 `demandsentdate` | date | `2024-05-17` ~ `2025-04-22` | `2025-01-22` | `newrez.portnewrezfc.demandsentdate` | NOI 阶段起始；Milestone 第1步 | ✅ Confirmed（dev填充5%；活跃FCL口径85.9%） |
| `timeline_notice_of_intent_end_date` | NOI 到期日（通常发出+30天） | ETL | 直接映射 `demandexpirationdate` | date | 实测全为 NULL | — | `newrez.portnewrezfc.demandexpirationdate` | NOI 有效期截止 | ✅ Confirmed（dev 0%） |
| `timeline_approved_for_referral_date` | 批准转案/开案日（BPS 建档日） | ETL | 直接映射 `fcsetupdate` | date | 实测全为 NULL | — | `newrez.portnewrezfc.fcsetupdate` | FCL 转案审批节点 | ✅ Confirmed（dev 0%；活跃FCL口径100%） |
| `timeline_referred_to_attorney_date` | 转介律师日 | ETL | 直接映射 `fcreferraldate` | date | 实测全为 NULL | — | `newrez.portnewrezfc.fcreferraldate` | 律师接案确认 | ✅ Confirmed（dev 0%） |
| `timeline_referred_to_foreclosure_date` | 正式转 FCL 日期 | ETL | 直接映射 `fcreferraldate` | date | `2018-08-15` ~ `2026-03-10`（84种） | `2025-05-23` | `newrez.portnewrezfc.fcreferraldate` | **BPS 主表入库过滤字段**（非空才收录） | ✅ Confirmed（100%） |
| `timeline_title_report_received_date` | 产权报告收到日 | ETL | 直接映射 `titlereceiveddate` | date | `2025-03-24` ~ `2025-12-02` | `2025-12-02` | `newrez.portnewrezfc.titlereceiveddate` | 产权追踪 | ✅ Confirmed（dev 3%；Newrez 活跃FCL口径0%） |
| `timeline_preliminary_title_cleared_date` | 初步产权清查日 | ETL | 直接映射 `titlecleardate` | date | `2025-03-24` ~ `2026-02-02` | `2025-03-24` | `newrez.portnewrezfc.titlecleardate` | 产权追踪 | ✅ Confirmed（dev 2%） |
| `timeline_first_legal_date` | 第一次法律行动日（Filing） | ETL | 直接映射 `firstlegaldate` | date | `2018-10-29` ~ `2026-02-25`（42种） | `2025-06-13` | `newrez.portnewrezfc.firstlegaldate` | FCL 法律程序里程碑 | ✅ Confirmed（45%） |
| `timeline_service_date` | 法律文书送达完成日 | ETL | 直接映射 `servicecompletedate` | date | `2018-12-10` ~ `2026-02-16`（19种） | `2025-07-18` | `newrez.portnewrezfc.servicecompletedate` | 法律送达完成节点 | ✅ Confirmed（19%） |
| `timeline_publication_date` | 拍卖公告发布日 | ETL | Newrez 无对应字段 | date | 实测全为 NULL | — | *(Newrez 无对应字段)* | 拍卖公告发布节点 | ✅ Confirmed（恒 NULL，见 doc 13 Q1） |
| `timeline_judgement_hearing_set_date` | 当前听证日首次出现日（ETL 追踪） | ETL | `MIN(dataasof WHERE fcjudgmenthearingscheduled=当前值)` | date | `2023-12-14` ~ `2026-03-06` | `2025-07-15` | `newrez.portnewrezfc.fcjudgmenthearingscheduled` | Judgement 阶段起点（Judicial 州） | ✅ Confirmed（9%） |
| `timeline_judgement_date` | 当前排定的判决听证会日期 | ETL | 直接映射 `fcjudgmenthearingscheduled` | date | `2020-01-22` ~ `2026-07-15` | `2026-01-18` | `newrez.portnewrezfc.fcjudgmenthearingscheduled` | Judgement 听证排期；注：**非** `fcjudgmententered`（法院录入日，见 doc 13 Q12） | ✅ Confirmed（9%） |
| `timeline_sale_date_projected_date` | 最新预计/排定拍卖日 | ETL | 直接映射 `fcscheduledsaledate` | date | `2025-01-23` ~ `2026-06-26`（15种） | `2026-04-07` | `newrez.portnewrezfc.fcscheduledsaledate` | 拍卖安排节点 | ✅ Confirmed（19%） |
| `timeline_sale_date_set_date` | 当前拍卖日首次出现日（ETL 追踪） | ETL | `MIN(dataasof WHERE fcscheduledsaledate=当前值)` | date | `2025-01-23` ~ `2026-03-12`（17种） | `2026-02-25` | `newrez.portnewrezfc.fcscheduledsaledate` | 拍卖确定追踪 | ✅ Confirmed（19%） |
| `timeline_final_title_cleared_date` | 最终产权清查日 | ETL | 直接映射 `titlecleardate`（最终） | date | `2025-03-24` ~ `2026-02-02` | `2026-02-02` | `newrez.portnewrezfc.titlecleardate` | 产权追踪最终节点 | ✅ Confirmed（dev 2%） |
| `timeline_sale_date_held_date` | 实际拍卖举行日 | ETL | 直接映射 `fcsalehelddate` | date | `2025-01-23` ~ `2026-03-11`（7种） | `2026-01-16` | `newrez.portnewrezfc.fcsalehelddate` | 拍卖完成确认 | ✅ Confirmed（7%） |
| `timeline_foreclosure_completed_date` | FCL 流程完结日 | ETL | `COALESCE(dtdeedrecorded, fcremovaldate)` | date | 实测全为 NULL | — | `newrez.portnewrezfc.dtdeedrecorded` / `fcremovaldate` | FCL 关闭里程碑 | ✅ Confirmed（dev 0%） |
| `timeline_third_party_sold_date_date` | 第三方买家成交日 | ETL | 当 `fcresults='3rd Party'` 时取 `fcsalehelddate` | date | 实测全为 NULL | — | `newrez.portnewrezfc.fcsalehelddate` | 第三方拍卖追踪 | ✅ Confirmed（dev 0%） |
| `timeline_third_party_proceeds_received_date` | 第三方拍卖款到账日 | ETL | 直接映射 `fcl3rdpartyproceedsreceiveddate` | date | `2026-03-05`（仅1笔） | `2026-03-05` | `newrez.portnewrezfc.fcl3rdpartyproceedsreceiveddate` | 拍卖款到账追踪 | ✅ Confirmed（1%） |

#### Group 3：SLA 目标天数（`target_*_days`，15列）

> 对应 BPS UI 的 **Target Days 面板**。全部为 `int NOT NULL`，含 **MySQL 硬编码 DEFAULT 值**（静态 SLA 阈值，非动态计算）。  
> ⚠️ `actual_*_days`（实际历时天数）**不在本表**，位于 `bpms_dev.sync_fcl_stage_info`。

> 全部 `int NOT NULL`，含硬编码 DEFAULT；实测每列 distinct=1（98 行全部等于 DEFAULT），故「取值范围」即唯一实测值。

| 字段名 | SLA 含义 | MySQL DEFAULT | 取值范围 | 备注 |
|--------|---------|--------------|---------|------|
| `target_notice_of_intent_days` | NOI 阶段目标天数 | `30` | `{30}`（唯一值, 98/98） | NOI 发出后30天内进入下一阶段 |
| `target_notice_of_intent_expired_days` | NOI 到期等待目标天数 | `90` | `{90}`（唯一值, 98/98） | NOI 等待期90天 |
| `target_approved_for_referral_days` | 批准转案目标天数 | `30` | `{30}`（唯一值, 98/98） | 审批后30天内正式转案 |
| `target_referred_to_attorney_days` | 转案至律师接案目标天数 | `1` | `{1}`（唯一值, 98/98） | 1天内律师确认接案 |
| `target_referred_to_foreclosure_days` | 转案至正式启动FCL目标天数 | `1` | `{1}`（唯一值, 98/98） | 1天内正式进入FCL程序 |
| `target_title_report_received_days` | 产权报告到位目标天数 | `30` | `{30}`（唯一值, 98/98） | 30天内收到产权报告 |
| `target_preliminary_title_cleared_days` | 初步产权确认目标天数 | `30` | `{30}`（唯一值, 98/98） | 初步产权确认30天 |
| `target_first_legal_days` | 第一次法律行动目标天数 | `120` | `{120}`（唯一值, 98/98） | 从正式FCL到First Legal最多120天 |
| `target_service_days` | 送达完成目标天数 | `90` | `{90}`（唯一值, 98/98） | 90天内完成法律送达 |
| `target_publication_days` | 公告发布目标天数 | `30` | `{30}`（唯一值, 98/98） | 30天内完成拍卖公告 |
| `target_judgement_hearing_set_days` | Judgment Hearing 安排目标天数 | `120` | `{120}`（唯一值, 98/98） | 120天内确定判决听证日期 |
| `target_judgement_days` | Judgment 完成目标天数 | `30` | `{30}`（唯一值, 98/98） | 30天内完成判决 |
| `target_sale_date_set_days` | 拍卖日期确定目标天数 | `30` | `{30}`（唯一值, 98/98） | 30天内确定拍卖日 |
| `target_final_title_cleared_days` | 最终产权确认目标天数 | `5` | `{5}`（唯一值, 98/98） | 拍卖后5天内完成最终产权确认 |
| `target_sale_date_held_days` | 拍卖完成目标天数 | `0` | `{0}`（唯一值, 98/98） | 0天（即设定日当天完成） |

#### Group 4：差异/方差调整（`variance_*`，4列）

> 对应 BPS UI 的 **Variance 面板**。记录 FCL 流程中因 BK/LM/Hold 等暂停事件产生的天数调整量。

> ⚠️ dev 环境本组 4 列实测**全为 NULL**（未回填）；下方「取值范围」记录实测状态，业务取值逻辑来自 doc 13 Section 4.4。

| 字段名 | 字段业务含义 | 来源数据 | 计算/推导逻辑 | 数据类型 | 取值范围 | 典型取值 | 上游字段 | 下游用途 | 备注 |
|--------|------------|---------|--------------|---------|---------|---------|---------|---------|------|
| `variance_active_bankruptcy` | 当前是否处于活跃破产保护（1/0） | BPS 应用层 | 直接取 `activebkflag` | int | 实测全为 NULL（dev 未回填） | — | `newrez.portnewrezbk.activebkflag` | 从 Target 中扣除，得到调整后期望天数 | 🟡 类型实测；取值 dev 未回填 |
| `variance_completed_bankruptcy` | 历史上是否曾完结破产（1/0） | BPS 应用层 | `activebkflag=0 AND bkremovaldate IS NOT NULL → 1` | int | 实测全为 NULL（dev 未回填） | — | `newrez.portnewrezbk.activebkflag` / `bkremovaldate` | 历史方差追踪 | 🟡 类型实测；取值 dev 未回填 |
| `variance_estimated_hold_days` | 预计 Hold 调整天数合计 | BPS 应用层 | `MAX(fchold1/2/3projectedenddate) − current_date` | int | 实测全为 NULL（dev 未回填） | — | `newrez.portnewrezfc.fchold*projectedenddate`（**非** Hold 表，见 doc 13 §4.4） | SLA 方差分析 | 🟡 类型实测；取值 dev 未回填 |
| `variance_bankruptcies` | 该贷款历史 BK 申请总次数 | BPS 应用层 | `COUNT(*)` 按 loanid 分组 | int | 实测全为 NULL（dev 未回填） | — | `newrez.portnewrezbk.loanid`（计数） | 风险评估；多次破产=FCL流程更复杂 | 🟡 类型实测；取值 dev 未回填 |

#### Group 5：竞拍审批（`bid_approval_*`，4列）

> 对应 BPS UI 的 **Bid Approval 面板**。

| 字段名 | 字段业务含义 | 来源数据 | 计算/推导逻辑 | 数据类型 | 取值范围 | 典型取值 | 上游字段 | 下游用途 | 备注 |
|--------|------------|---------|--------------|---------|---------|---------|---------|---------|------|
| `bid_approval_status` | 竞拍审批状态 | BPS 应用层 | 直接写入 | varchar(128) | 实测全为 NULL（dev 未回填） | — | — | Bid Approval 面板状态展示 | 🟡 类型实测；取值 dev 未回填 |
| `bid_approval_sale_date` | 竞拍关联的拍卖日期 | BPS 应用层 | 直接写入 | date | 实测全为 NULL（dev 未回填） | — | `port.basic_data_loan_fcl.fcsale_held_date` | 拍卖日确认 | 🟡 类型实测；取值 dev 未回填 |
| `bid_approval_bid_amount` | 竞拍出价金额 | ETL | 映射自 `fcbidamount` / `fcapprbidprice` | decimal(32,16) | `$90,000` ~ `$543,305.96`（9笔有值, 9%） | `136392.44` | `port.basic_data_loan_fcl.fcbidamount` / `fcapprbidprice` | 投资人审批出价 | ✅ Confirmed |
| `bid_approval_loan_resolution_holods` | **贷款处置 Hold 原因** | BPS 应用层 | 直接写入；**⚠️ 列名拼写错误（`holods` 应为 `holds`），已投产，不可轻易修改** | text | 实测全为 NULL（dev 未回填） | — | — | Hold 原因记录 | 🟡 拼写错误已实测确认；取值 dev 未回填 |

#### Group 6：汇总摘要（`summary_*`，16列）

> 对应 BPS UI 的 **Summary 面板**，含 FCL 当前状态、律师信息、关键效率指标等。

| 字段名 | 字段业务含义 | 来源数据 | 计算/推导逻辑 | 数据类型 | 取值范围 | 典型取值 | 上游字段 | 下游用途 | 备注 |
|--------|------------|---------|--------------|---------|---------|---------|---------|---------|------|
| `summary_servicer_number` | Servicer 内部编号 | BPS 应用层 | 直接写入 | varchar(64) | 实测全为 NULL（dev 未回填） | — | — | Servicer 标识辅助字段 | 🟡 类型实测为 varchar（非 int）；取值 dev 未回填 |
| `summary_foreclosure_status` | **FCL 当前状态**（Servicer 状态描述） | ETL | 映射自 `fcremovaldesc` / `activefcflag` / `fcresults` | varchar(64) | 实测9种：`Active Foreclosure`(43) \| `Closed Foreclosure:Reinstated`(21) \| `Closed Foreclosure:Loss Mitigation`(15) \| `Closed Foreclosure:Paid in Full`(10) \| `Closed Foreclosure:Process Complete`(3) \| `Closed Foreclosure:Deed in Lieu Cmplte` \| Carrington `1. First Legal Pending`/`2. First Legal Filed`/`5. Sales Held` | `Active Foreclosure` | `port.basic_data_loan_fcl.fcremovaldesc` | BPS Summary 面板首要展示字段 | ✅ Confirmed（97/98=99%） |
| `summary_completed_foreclosure` | FCL 是否已完结 | ETL | 推断自 `fcresults` / `fcremovaldate` | int | 实测全为 NULL（dev 未回填） | — | `port.basic_data_loan_fcl.fcresults` | 完结 FCL 标志 | 🟡 类型实测为 int（非 varchar）；取值 dev 未回填 |
| `summary_foreclosure_bid_amount` | FCL 出价金额（投资人口径） | ETL | 映射自 `fcbidamount` / `fcapprbidprice` | decimal(32,16) | `$90,000` ~ `$543,305.96`（9笔, 9%） | `136392.44` | `port.basic_data_loan_fcl.fcbidamount` | 投资人出价审批参考 | ✅ Confirmed |
| `summary_srv_fc_bid_amount` | Servicer 上报的 FCL 出价金额 | ETL | 直接映射 | decimal(32,16) | `$90,000` ~ `$543,305.96`（9笔, 9%） | `136392.44` | — | 与投资人出价的差异对比分析 | ✅ Confirmed |
| `summary_foreclosure_sale_amount` | 实际拍卖成交金额 | ETL | 映射自 `fcsaleamount` | decimal(32,16) | `$90,001` ~ `$400,000`（6笔, 6%） | `165900.00` | `port.basic_data_loan_fcl.fcsaleamount` | 拍卖结果记录；Loss Severity 计算 | ✅ Confirmed |
| `summary_judicial_foreclosure` | 是否司法 FCL（1=司法） | ETL | 映射自 `judicial` | int | `{0, 1}`（各44笔, 88/98=90%） | `0` | `port.basic_data_loan_fcl.judicial` | FCL 类型识别（司法/非司法流程差异显著） | ✅ Confirmed（类型实测为 int，非 tinyint） |
| `summary_foreclosure_attorney` | FCL 律师名称 | ETL | 映射自 `fcfirm` | varchar(256) | 实测4种，如 `Brock & Scott PLLC` / `Lender Legal PLLC` / `Vylla Solutions, LLC` | `Brock & Scott PLLC` | `port.basic_data_loan_fcl.fcfirm` | 律师信息展示 | ✅ Confirmed（4%） |
| `summary_contested_litigation` | 是否有争议诉讼（1=有） | ETL | 映射自 `fccontestedflag` | int | `{0(83), 1(4)}`（87/98=89%） | `0` | `port.basic_data_loan_fcl.fccontestedflag` | 争议贷款标识；法律风险追踪 | ✅ Confirmed（类型实测为 int，非 tinyint） |
| `summary_firm` | 律师事务所名称 | ETL | 映射自 `fcfirm` | varchar(256) | 实测46种，如 `Albertelli Law` … `ZBS Law, LLP` | `Albertelli Law` | `port.basic_data_loan_fcl.fcfirm` | BPS 律师事务所展示 | ✅ Confirmed（96%） |
| `summary_type` | FCL 类型文本（与 judicial 配合） | ETL | 映射自 `judicial` 标志 | varchar(128) | `{Judicial, Non Judicial}`（各44笔, 90%） | `Non Judicial` | `port.basic_data_loan_fcl.judicial` | FCL 类型文本展示 | ✅ Confirmed（注：实测文本为 `Non Judicial`，无连字符） |
| `summary_sms_days_in_fcl` | SMS系统统计的 FCL 历时天数（Servicer口径） | ETL | 实时计算自 `svc_days_infc` | int | `5` ~ `531`（73种, 82%） | `128` | `port.basic_data_loan_fcl.svc_days_infc` | Servicer 口径 FCL 历时监控 | ✅ Confirmed |
| `summary_days_in_fcl` | 投资人口径 FCL 历时天数 | ETL | 实时计算自 `daysinfc` | int | `5` ~ `739`（81种, 95%） | `215` | `port.basic_data_loan_fcl.daysinfc` | FCL 效率监控；SLA 评估基础 | ✅ Confirmed |
| `summary_current_step` | 当前 FCL 步骤 | ETL | 次优先：映射自 `fcstage` | varchar(128) | 实测38种，如 `Acceleration Letter Sent` … `TSG Report Received` | `Sale Scheduled For` | `port.basic_data_loan_fcl.fcstage` | BPS 当前进度展示 | ✅ Confirmed（96%） |
| `summary_last_step_completed` | 最近完成的 FCL 步骤 | ETL | 映射自 `lastfcstepcompleted` | varchar(256) | 实测32种，如 `Answer Period Will Expire On` … `TSG Report Received` | `Service Complete` | `port.basic_data_loan_fcl.lastfcstepcompleted` | 历史进度追踪 | ✅ Confirmed（90%；字段曾由 `last_step_completed` 重命名，见 doc 14 v13） |
| `summary_last_step_completed_date` | 最近完成步骤的日期 | ETL | 映射自 `lastfcstepcompleteddate` | date | `2019-10-14` ~ `2026-03-12`（74种, 90%） | `2025-11-01` | `port.basic_data_loan_fcl.lastfcstepcompleteddate` | 进度时间追踪 | ✅ Confirmed |

#### Group 7：管理字段（8列）

| 字段名 | 字段业务含义 | 数据类型 | DEFAULT | 取值范围 | 典型取值 | 备注 |
|--------|------------|---------|---------|---------|---------|------|
| `create_user` | 记录创建用户 | bigint | NULL | 实测全为 NULL（dev 未回填） | — | 审计追踪（类型实测为 bigint，非 varchar） |
| `create_dept` | 记录创建部门 | bigint | NULL | 实测全为 NULL（dev 未回填） | — | 审计追踪（类型实测为 bigint） |
| `create_time` | 记录创建时间 | datetime | NULL | 实测全为 NULL（dev 未回填） | — | 审计追踪 |
| `update_user` | 最后更新用户 | bigint | NULL | 实测全为 NULL（dev 未回填） | — | 审计追踪（类型实测为 bigint） |
| `update_time` | 最后更新时间 | datetime | NULL | 实测全为 NULL（dev 未回填） | — | 审计追踪 |
| `status` | 记录状态（0=正常） | int NOT NULL | `0` | `{0}`（唯一值, 98/98） | `0` | 软停用标志（类型实测为 int） |
| `is_deleted` | 是否软删除（0=未删） | int NOT NULL | `0` | `{0}`（唯一值, 98/98） | `0` | 软删除标志（类型实测为 int） |
| `tenant_id` | 租户 ID（多租户架构） | varchar(12) | NULL | `{000000(86), 984018(12)}`（2种） | `000000` | 多租户支持（类型实测为 varchar(12)，非 bigint） |

---

### 表 18：`newrez.portnewrezfc` — Newrez Foreclosure 原始日报表

| 属性 | 值 |
|------|----|
| **表名** | `portnewrezfc` |
| **所属 Schema** | MySQL `newrez` |
| **数据层** | Raw / Servicer-specific（Newrez/Shellpoint 原始 FCL 日报落地表） |
| **业务作用** | Newrez foreclosure 全流程追踪表，包含 FCL 激活标志、里程碑时间线、Hold 1/2/3、司法/非司法属性、律师、拍卖、结案和高级留置权 sale 信息 |
| **业务意图** | 作为 Newrez FCL 原始事实表，下游统一到 `port.basic_data_loan_fcl`、`port.basic_data_loan_foreclosure_hold_detail`、`port.basic_data_loan_comments`，并被 BPS FCL stage 计算使用 |
| **上游来源** | Newrez/Shellpoint `Foreclosure` / `AresOversight_Foreclosure` 文件；代码映射见 `flow/basic_data/load_servicer_data_config/servicer_config.py` |
| **下游使用** | `port.basic_data_loan_fcl`（FCL timeline 主来源）；`port.basic_data_loan_foreclosure_hold_detail` / `port.basic_data_loan_foreclosure_hold`（Hold 详情）；`port.basic_data_loan_comments`（Hold comment）；BPS `sync_asset_management.get_max_daily_date()` 使用其 `max(dataasof)` |
| **Foreclosure 关系** | 直接：Newrez FCL 判断、timeline、Hold、拍卖和结案事实的核心原始表 |
| **主键 / 索引** | `id` 为自增主键；业务 join key 通常为 `loanid + dataasof` |
| **DB验证** | 2026-05-29 MySQL `information_schema.columns` + 聚合查询：63列；1,556,688行；887个非空 `dataasof`；范围 2023-12-14 至 2026-05-27 |

#### 最新快照分布（`dataasof = 2026-05-27`）

| 指标 | 结果 |
|------|------|
| 行数 | 5,050 |
| `activefcflag` | `0` = 5,012；`1` = 38 |
| `fcstage` Top values | blank/null = 4,951；`Pre-Sale Review 1 (SCRA and PACER Check)` = 16；`Service Complete` = 11；`Post Sale Review (SCRA and PACER Check)` = 9；`Title Report Received` = 8；`Sale Scheduled For` = 8 |
| `fcresults` | blank/null = 5,041；`REO` = 6；`3rd Party` = 3 |
| `judicial` | NULL = 4,951；`0` = 51；`1` = 48 |

#### 字段说明（63列）

| 字段名 | 字段业务含义 | 来源数据 | 计算/推导逻辑 | 数据类型 | 取值范围 | 典型取值 | 上游字段 | 下游用途 | 备注 |
|--------|-----------|--------|-----------|----------|---------|---------|--------|--------|------|
| `id` | MySQL 自增主键 | Newrez 系统 | 直接上报 | bigint | 1~1,556,688 | 1 | — | 技术主键，不作为业务 join key | ✅ Confirmed |
| `loanid` | Bridger/投资人贷款 ID | Newrez 系统 | 直接上报 | varchar(255) | 纯数字字符串 | 7727000088 | — | 与其他 Newrez 表按 `loanid + dataasof` 关联 | ✅ Confirmed |
| `dataasof` | 数据快照日期 | Newrez 系统 | 直接上报 | date | YYYY-MM-DD | 2026-05-27 | — | 每日报表日期；下游 `fctrdt` / `dataasof` 来源 | ✅ Confirmed |
| `shellpointloanid` | Newrez/Shellpoint 服务商贷款号 | Newrez 系统 | 直接上报 | varchar(255) | 格式 NR-YYYY-NNNNNN | NR-2024-001234 | — | 下游 `svc_loanid` / `svcloanid` | ✅ Confirmed |
| `fcsetupdate` | FCL 立案/设置日期 | Newrez 系统 | 直接上报 | date | 2024-02-07~2026-05-26 | 2024-01-10 | — | 下游 `fcsetupdate`，BPS 可用作 Approved for Referral 相关节点 | ✅ Confirmed |
| `fcreferraldate` | FCL Referral / 转交律师日期 | Newrez 系统 | 直接上报 | date | 2024-02-07~2026-05-26 | 2024-01-20 | — | 下游 `referral_start_date`，FCL timeline 起点 | ✅ Confirmed |
| `smsdaysinfc` | Servicer/SMS 口径 FCL 已历天数 | Newrez 系统 | 直接上报 | int | 1~606天 | 128 | — | 下游 `svc_days_infc`、BPS `summary_sms_days_in_fcl` | ✅ Confirmed |
| `daysinfc` | Newrez 自报 FCL 已历天数 | Newrez 系统 | 直接上报 | int | 1~814天 | 215 | — | 下游 `daysinfc`、BPS `summary_days_in_fcl` | ✅ Confirmed |
| `demandsentdate` | Demand / NOI 发出日 | Newrez 系统 | 直接上报 | date | 2021-10-18~2026-04-20 | 2024-02-01 | — | BPS `timeline_notice_of_intent_date` 来源之一 | ✅ Confirmed |
| `demandexpirationdate` | Demand / NOI 到期日 | Newrez 系统 | 直接上报 | date | 2018-03-02~2026-06-22 | 2024-03-02 | — | BPS `timeline_notice_of_intent_end_date` 来源之一 | ✅ Confirmed |
| `fcstage` | 当前 FCL 阶段描述 | Newrez 系统 | 直接上报 | varchar(255) | 自由文本（Newrez系统内部） | Service Complete | — | 下游 `fcstage`、BPS `summary_current_step` | ✅ Confirmed |
| `lastfcstepcompleted` | 最近完成的 FCL 步骤 | Newrez 系统 | 直接上报 | varchar(255) | 自由文本 | First Legal | — | 下游 `lastfcstepcompleted`、BPS `summary_last_step_completed` | ✅ Confirmed |
| `lastfcstepcompleteddate` | 最近完成步骤日期 | Newrez 系统 | 直接上报 | date | 2019-10-14~2026-05-27 | 2024-02-15 | — | 下游 `lastfcstepcompleteddate` | ✅ Confirmed |
| `fchold1description` | Hold 1 原因描述 | Newrez 系统 | 直接上报 | varchar(255) | Loss Mitigation Workout \| Awaiting Funds to Post \| Service Delay \| Court Delay \| Hearing Set \| Bankruptcy Filed 等15+种 | Loss Mitigation Workout | — | 下游 Hold detail 的 `description1` | ✅ Confirmed (MySQL 实测) |
| `fchold1startdate` | Hold 1 开始日期 | Newrez 系统 | 直接上报 | date | 2019-11-20~2026-05-27 | 2024-01-05 | — | 下游 Hold detail 的 `description1_start_date` | ✅ Confirmed |
| `fchold1enddate` | Hold 1 结束日期 | Newrez 系统 | 直接上报 | date | 2019-11-26~2026-05-28（空=仍持续） | 2024-03-15 | — | 下游 Hold detail 的 `description1_end_date` | ✅ Confirmed |
| `fchold2description` | Hold 2 原因描述 | Newrez 系统 | 直接上报 | varchar(255) | 同 fchold1description（69.8%填充） | Loss Mitigation Workout | — | 下游 Hold detail 的 `description2` | ✅ Confirmed (MySQL 实测) |
| `fchold2startdate` | Hold 2 开始日期 | Newrez 系统 | 直接上报 | date | 2019-11-20~2026-05-27 | 2022-11-08 | — | 下游 Hold detail 的 `description2_start_date` | ✅ Confirmed (MySQL 实测) |
| `fchold2enddate` | Hold 2 结束日期 | Newrez 系统 | 直接上报 | date | 2019-11-26~2026-05-28（空=仍持续） | 2022-11-25 | — | 下游 Hold detail 的 `description2_end_date` | ✅ Confirmed (MySQL 实测) |
| `fcjudgmenthearingscheduled` | 判决听证会/出售确认听证会的**排定日期**（未来计划事件；每次改期后此值更新为最新排期日） | Newrez 系统 | 直接上报 | date | 2020-01-22~2026-08-21 | 2026-01-18 | — | → Redshift `port.basic_data_loan_fcl.fcjudgment_hearing_scheduled` → `bpms_dev.sync_loan_foreclosure.timeline_judgement_date`（直接）；同时作为 `timeline_judgement_hearing_set_date` 计算 key（`MIN(dataasof WHERE fcjudgmenthearingscheduled=当前值)`）；→ `bpms_dev.sync_fcl_stage_info.judgement_start_date` | ✅ Confirmed |
| `fcjudgmententered` | 法院**正式录入**判决的日期（已完成的法律事实；与 `fcjudgmenthearingscheduled` 含义不同：前者是排定日/计划事件，后者是录入日/已发生事实） | Newrez 系统 | 直接上报 | date | 2025-01-10~2026-04-09 | 2026-01-07 | — | → Redshift `port.basic_data_loan_fcl.fcjudgment_end_date`；⚠️ 当前未流入任何 `bpms_dev` 字段（ETL 预留；设计意图：未来 `actual_judgement_hearing_set_days` 计算来源；见 doc 13 Q12） | ✅ Confirmed |
| `fcscheduledsaledate` | 计划拍卖日期 | Newrez 系统 | 直接上报 | date | 2025-04-17~2026-08-06 | 2024-05-15 | — | 下游 `fcscheduled_sale_date`、BPS sale projected date | ✅ Confirmed |
| `fcsalehelddate` | 实际拍卖日期 | Newrez 系统 | 直接上报 | date | 2025-05-27~2026-05-22 | 2024-05-15 | — | 下游 `fcsale_held_date` | ✅ Confirmed |
| `fcsaleamount` | 实际拍卖成交金额 | Newrez 系统 | 直接上报 | decimal(32,16) | $90,001~$400,000 | 170000.00 | — | 下游 `fcsaleamount`、BPS sale amount | ✅ Confirmed |
| `fcresults` | FCL 结果 | Newrez 系统 | 直接上报 | varchar(255) | REO \| 3rd Party（活跃FCL为空） | REO | — | 识别 `REO` / `3rd Party` 等结案结果 | ✅ Confirmed (MySQL 实测，仅此2值) |
| `firstlegaldate` | First Legal 日期 | Newrez 系统 | 直接上报 | date | 2018-10-29~2026-05-27 | 2024-02-01 | — | 下游 `legal_start_date`、BPS first legal date | ✅ Confirmed |
| `servicecompletedate` | Service complete 日期 | Newrez 系统 | 直接上报 | date | 2018-12-10~2026-02-15 | 2024-03-10 | — | 下游 `service_start_date`、BPS service date | ✅ Confirmed |
| `titleordereddate` | Title report ordered 日期 | Newrez 系统 | 直接上报 | date | YYYY-MM-DD | 2023-12-20 | — | 产权调查启动 | ✅ Confirmed |
| `titlecleardate` | Title clear 日期 | Newrez 系统 | 直接上报 | date | 2025-03-24~2026-04-26（Newrez少量提供） | 2024-01-15 | — | BPS preliminary/final title cleared 相关来源 | ✅ Confirmed |
| `titlereceiveddate` | Title report received 日期 | Newrez 系统 | 直接上报 | date | 2025-03-24~2026-04-26（Newrez少量提供） | 2024-01-25 | — | BPS title report received date | ✅ Confirmed |
| `fcremovaldesc` | FCL 移除/关闭原因描述 | Newrez 系统 | 直接上报 | varchar(255) | 自由文本 | Foreclosure Complete | — | 下游 summary foreclosure status / closed reason | ✅ Confirmed |
| `fcremovaldate` | FCL 移除/关闭日期 | Newrez 系统 | 直接上报 | date | 2019-11-27~2026-05-28 | 2024-06-01 | — | FCL completed / closed date 相关来源 | ✅ Confirmed |
| `fccontestedflag` | 是否 contested litigation | Newrez 系统 | 直接上报 | int | 0 / 1 | 0 | — | BPS `summary_contested_litigation` | ✅ Confirmed |
| `judicial` | 是否 Judicial Foreclosure | Newrez 系统 | 直接上报 | int | 0（Non-Judicial）/ 1（Judicial） | 1 | — | BPS `summary_judicial_foreclosure` / `summary_type` | ✅ Confirmed |
| `fcfirm` | FCL 律师事务所 | Newrez 系统 | 直接上报 | varchar(255) | 自由文本（律师事务所名称） | Kelley Kronenberg, P.A. | — | BPS `summary_firm` / attorney | ✅ Confirmed |
| `jr_sr_lien_flag` | Junior/Senior lien 标志 | Newrez 系统 | 直接上报 | int | 0 / 1 | 0 | — | 高级/次级留置权辅助字段 | ✅ Confirmed |
| `fcbidamount` | FCL bid amount | Newrez 系统 | 直接上报 | decimal(32,16) | $90,000~$543,305.96 | 160000.00 | — | BPS bid approval / summary bid amount 来源 | ✅ Confirmed |
| `activefcflag` | FCL 活跃标志 | Newrez 系统 | 直接上报 | int | 0（已完结）/ 1（进行中） | 1 | — | Newrez FCL active 判断入口；最新快照 `1`=38 | ✅ Confirmed |
| `fchold1projectedenddate` | Hold 1 预计结束日期 | Newrez 系统 | 直接上报 | date | YYYY-MM-DD | 2024-03-20 | — | Hold 面板 projected end date | ✅ Confirmed |
| `fchold1comment` | Hold 1 备注 | Newrez 系统 | 直接上报 | varchar(1000) | 自由文本 | Awaiting Bankruptcy Resolution | — | 写入 `port.basic_data_loan_comments` | ✅ Confirmed |
| `fchold2projectedenddate` | Hold 2 预计结束日期 | Newrez 系统 | 直接上报 | date | YYYY-MM-DD | 2023-01-07 | — | Hold 面板 projected end date | ✅ Confirmed (MySQL 实测) |
| `fchold2comment` | Hold 2 备注 | Newrez 系统 | 直接上报 | varchar(1000) | 自由文本 | Awaiting Court Scheduling | — | 写入 `port.basic_data_loan_comments` | ✅ Confirmed |
| `holdmodified` | Hold 1 修改日期 | Newrez 系统 | 直接上报 | date | 2019-11-26~2026-05-28 | 2024-02-20 | — | Hold comment 的 `comments_date` | ✅ Confirmed |
| `holdmodified2` | Hold 2 修改日期 | Newrez 系统 | 直接上报 | date | 2019-11-26~2026-05-28 | 2022-11-25 | — | Hold comment 的 `comments_date` | ✅ Confirmed (MySQL 实测) |
| `create_time` | 记录创建时间 | Newrez 系统 | 直接上报 | datetime | 2024-04-09~2026-05-31（datetime） | 2023-12-14 08:30:00 | — | MySQL 管理字段 | ✅ Confirmed |
| `update_time` | 记录更新时间 | Newrez 系统 | 直接上报 | datetime | 2024-04-09~2026-05-31（datetime） | 2026-05-27 10:15:00 | — | MySQL 管理字段 | ✅ Confirmed |
| `dtdeedrecorded` | Deed recorded 日期 | Newrez 系统 | 直接上报 | date | 2025-10-28~2026-05-21 | 2024-06-01 | — | FCL 完成 / REO 转移后登记节点 | ✅ Confirmed |
| `fcapprbidprice` | 批准 bid price | Newrez 系统 | 直接上报 | decimal(32,16) | $90,000~$536,008.42 | 162000.00 | — | Bid approval / summary bid amount 参考 | ✅ Confirmed |
| `fcl3rdpartyproceedsreceiveddate` | 第三方购买款到账日期 | Newrez 系统 | 直接上报 | date | 2026-03-04~2026-05-26 | 2026-03-04 | — | BPS `timeline_third_party_proceeds_received_date` | ✅ Confirmed |
| `investorloanid` | 投资人贷款号 | Newrez 系统 | 直接上报 | varchar(100) | 格式 INV-YYYYMMDD-NNN | INV-20240110-088 | — | Newrez 对账辅助 ID | ✅ Confirmed |
| `fchold3description` | Hold 3 原因描述 | Newrez 系统 | 直接上报 | varchar(1000) | 同 fchold1description（52.6%填充） | Service Delay | — | 下游 Hold detail 的 `description3` | ✅ Confirmed (MySQL 实测) |
| `fchold3startdate` | Hold 3 开始日期 | Newrez 系统 | 直接上报 | date | 2019-10-24~2026-05-25 | 格式 YYYY-MM-DD | — | 下游 Hold detail 的 `description3_start_date` | ✅ Confirmed |
| `fchold3enddate` | Hold 3 结束日期 | Newrez 系统 | 直接上报 | date | YYYY-MM-DD（空=仍持续） | 格式 YYYY-MM-DD | — | 下游 Hold detail 的 `description3_end_date` | ✅ Confirmed |
| `fchold3projectedenddate` | Hold 3 预计结束日期 | Newrez 系统 | 直接上报 | date | YYYY-MM-DD | 格式 YYYY-MM-DD | — | Hold 面板 projected end date | ✅ Confirmed |
| `fchold3comment` | Hold 3 备注 | Newrez 系统 | 直接上报 | varchar(1000) | 自由文本 | 同 fchold1comment 格式 | — | 写入 `port.basic_data_loan_comments` | ✅ Confirmed |
| `holdmodified3` | Hold 3 修改日期 | Newrez 系统 | 直接上报 | date | YYYY-MM-DD | 格式 YYYY-MM-DD | — | Hold comment 的 `comments_date` | ✅ Confirmed |
| `activejnrlienfcflag` | 活跃 junior lien FCL 标志 | Newrez 系统 | 直接上报 | int | 0 / 1 | 0 | — | 下游 `activejnrlienfcflag` | ✅ Confirmed |
| `currentmilestone` | 当前 FCL milestone | Newrez 系统 | 直接上报 | varchar(255) | Closed \| First Legal \| Judgment Entered \| Sale Held \| Sold \| Service Complete \| Sale Scheduled | First Legal | — | Newrez 当前里程碑辅助字段 | ✅ Confirmed (MySQL 实测) |
| `srlienmonitorflag` | Senior lien monitoring 标志 | Newrez 系统 | 直接上报 | int | 0 / 1 | 0 | — | Senior lien 监控 | ✅ Confirmed |
| `srliensalescheduleddate` | Senior lien sale scheduled date | Newrez 系统 | 直接上报 | date | 实测始终为 NULL | — | — | Senior lien sale timeline | ✅ Confirmed |
| `srliensalehelddate` | Senior lien sale held date | Newrez 系统 | 直接上报 | date | 实测始终为 NULL | — | — | Senior lien sale timeline | ✅ Confirmed |
| `srliensaleresult` | Senior lien sale result | Newrez 系统 | 直接上报 | double | 实测始终为 NULL | — | — | Senior lien sale 结果 | ✅ Confirmed |
| `srliensaledate` | Senior lien sale date | Newrez 系统 | 直接上报 | date | YYYY-MM-DD | 2024-06-15 | — | Senior lien sale 日期 | ✅ Confirmed |

---

### 表 19：`newrez.portnewrezlm` — Newrez Loss Mitigation 原始日报表

| 属性 | 值 |
|------|----|
| **表名** | `portnewrezlm` |
| **所属 Schema** | MySQL `newrez` |
| **数据层** | Raw / Servicer-specific（Newrez/Shellpoint 原始 LM 日报落地表） |
| **业务作用** | Newrez Loss Mitigation 周期追踪表，包含 LM deal/program/status/decision、Forbearance、Trial、Repayment、PRA、Deferment、Short Sale 金额和 denial 信息 |
| **业务意图** | 识别贷款是否处于 LM、追踪每轮 LM cycle 的打开/关闭、方案类型和最终处置，并为 FCL Hold / BPS LM Cycle 面板提供业务上下文 |
| **上游来源** | Newrez/Shellpoint `LossMitigation` / `AresOversight_LossMitigation` 文件；代码映射见 `flow/basic_data/load_servicer_data_config/servicer_config.py` |
| **下游使用** | `port.basic_data_daily_loan_common.lm_flag`（`activelmflag = 1` → `Y`）；`port.basic_data_daily_loan_common.forbearance`；`port.basic_data_loan_foreclosure_loss_mitigation`（Deal/Program/Status/Disposition 解码后进入 BPS LM Cycle） |
| **Foreclosure 关系** | 间接但关键：LM 可导致 FCL Hold / Pause；LM 成功可能终止或避免 FCL，LM 失败通常转回 FCL |
| **主键 / 索引** | `id` 为自增主键；`loanid` 有索引；业务 join key 通常为 `loanid + dataasof`，LM cycle 去重常按 `loanid + dealstartdate` |
| **DB验证** | 2026-05-29 MySQL `information_schema.columns` + 聚合查询：56列；1,556,688行；887个非空 `dataasof`；范围 2023-12-14 至 2026-05-27 |

#### 最新快照分布（`dataasof = 2026-05-27`）

| 指标 | 结果 |
|------|------|
| 行数 | 5,050 |
| `activelmflag` | `0` = 5,018；`1` = 32 |
| `lmdeal` Top values | NULL = 4,831；`1` = 71；`2` = 67；`11` = 29；`5` = 25；`4` = 17；`6` = 6；`7` = 3；`9` = 1 |
| `lmprogram` Top values | NULL = 4,831；`21` = 67；`73` = 29；`496` = 23；`12` = 21；`29` = 16；`498` = 11；`419` = 9 |
| `lmstatus` Top values | NULL = 4,831；`166` = 74；`112` = 49；`5` = 20；`20` = 17；`140` = 13；`113` = 12；`25` = 10 |
| `lmdecision` Top values | NULL = 4,806；`99` = 62；`5` = 50；`11` = 34；`10` = 32；`6` = 26；`14` = 21 |
| `forbearancestatus` | NULL = 5,020；`4` = 25；`1` = 5 |

> 注意：`lmdeal` / `lmprogram` / `lmstatus` / `lmdecision` 在原始表中是数值编码。代码在生成 `port.basic_data_loan_foreclosure_loss_mitigation` 时通过 Newrez 数据字典表解码成文本；因此业务文档中应优先展示解码后的 Deal / Program / Status / Final Disposition。

#### 字段说明（56列）

| 字段名 | 字段业务含义 | 来源数据 | 计算/推导逻辑 | 数据类型 | 取值范围 | 典型取值 | 上游字段 | 下游用途 | 备注 |
|--------|-----------|--------|-----------|----------|---------|---------|--------|--------|------|
| `id` | MySQL 自增主键 | Newrez 系统 | 直接上报 | bigint | 1~1,556,688 | 1 | — | 技术主键 | ✅ Confirmed |
| `loanid` | Bridger/投资人贷款 ID | Newrez 系统 | 直接上报 | varchar(255) | 纯数字字符串 | 7727000088 | — | 与其他 Newrez 表按 `loanid + dataasof` 关联 | ✅ Confirmed |
| `dataasof` | 数据快照日期 | Newrez 系统 | 直接上报 | date | YYYY-MM-DD | 2026-05-27 | — | 每日报表日期 | ✅ Confirmed |
| `shellpointloanid` | Newrez/Shellpoint 服务商贷款号 | Newrez 系统 | 直接上报 | varchar(255) | 格式 NR-YYYY-NNNNNN | NR-2024-001234 | — | 下游 `svcloanid` | ✅ Confirmed |
| `hardshiptype` | Hardship 类型编码 | Newrez 系统 | 直接上报 | int | 11 / 12 / 19 / 20 / 7 / 8 / 21 等（整数编码，10+种） | 11 | — | 借款人困难原因；需字典解码 | ✅ Confirmed (MySQL 实测) |
| `borrowerintention` | Borrower intention 编码 | Newrez 系统 | 直接上报 | int | `1`=Unknown / `2`=Retention / `3`=Disposition | `2` | — | 下游解码为 `borrower_intentions` | ✅ Confirmed |
| `lmdeal` | LM Deal 大类编码 | Newrez 系统 | 直接上报 | int | `1`=Modification \| `2`=Evaluation \| `4`=Payment Plan \| `5`=Forbearance \| `6`=Short Sale \| `7`=DIL \| `9`=Payoff \| `11`=Deferment（见下方解码参考表） | `2` | — | 下游解码为 `deal`，如 Evaluation / Modification / Short Sale / DIL | ✅ Confirmed |
| `dealstartdate` | 本轮 LM cycle 打开日期 | Newrez 系统 | 直接上报 | date | 2020-08-17~2026-05-29 | 2024-01-15 | — | 下游 `cycle_opened_date`；LM cycle 去重 key | ✅ Confirmed |
| `daysindeal` | 本轮 Deal 已持续天数 | Newrez 系统 | 直接上报 | int | 0~991天 | 45 | — | LM cycle 时效分析 | ✅ Confirmed |
| `lmstatus` | LM 当前状态编码 | Newrez 系统 | 直接上报 | int | 15+种编码（166=Pending Financials \| 112=Workout Denial \| 5=Document Follow-up 等；**见下方解码参考表**） | `166` | — | 下游解码为 `lmc_status` | ✅ Confirmed |
| `statusstartdate` | 当前 LM status 开始日期 | Newrez 系统 | 直接上报 | date | 2020-08-17~2026-05-29 | 2024-02-01 | — | 状态持续时间分析 | ✅ Confirmed |
| `daysinstatus` | 当前 LM status 已持续天数 | Newrez 系统 | 直接上报 | int | 0~991天 | 30 | — | 状态时效分析 | ✅ Confirmed |
| `lmprogram` | LM Program 编码 | Newrez 系统 | 直接上报 | int | 15+种编码（21=Evaluation \| 73=Deferment \| 10=Deed-in-Lieu \| 8=Short Sale 等；**见下方解码参考表**） | `21` | — | 下游解码为 `program`，并保留原编码为 `improgram` | ✅ Confirmed |
| `lmdecision` | LM 最终决策编码 | Newrez 系统 | 直接上报 | int | 12+种编码（99=Pending \| 6=Referral to FC \| 10=Request Incomplete \| 11=LMS Opened in Error 等；**见下方解码参考表**） | `99` | — | 下游解码为 `final_disposition` | ✅ Confirmed |
| `lmremovaldate` | LM cycle 关闭/移除日期 | Newrez 系统 | 直接上报 | date | 2020-09-22~2026-05-29（空=进行中） | 2024-03-15 | — | 下游 `cycle_closed_date` | ✅ Confirmed |
| `denialreason` | LM 拒绝原因编码 | Newrez 系统 | 直接上报 | int | 18+种编码（109=Loan not due 3+ months \| 4=Withdrawal \| 6=Ineligible 等；**见下方解码参考表**） | `109` | — | 下游解码为 `denialreason` | ✅ Confirmed (MySQL 实测) |
| `forbearanceagreementdate` | Forbearance 协议日期 | Newrez 系统 | 直接上报 | date | 2020-04-01~2026-05-25 | 2024-01-20 | — | Forbearance 子流程 | ✅ Confirmed |
| `forbearancedatecompleted` | Forbearance 完成日期 | Newrez 系统 | 直接上报 | date | 2020-10-15~2026-04-30 | 2024-04-20 | — | Forbearance 子流程 | ✅ Confirmed |
| `forbearancebeginningduedate` | Forbearance 起始 due date | Newrez 系统 | 直接上报 | date | YYYY-MM-DD | 2024-01-01 | — | Forbearance 起始还款期 | ✅ Confirmed |
| `forbearanceendingduedate` | Forbearance 结束 due date | Newrez 系统 | 直接上报 | date | YYYY-MM-DD | 2024-04-01 | — | Forbearance 到期节点 | ✅ Confirmed |
| `forbearancenumberofmonths` | Forbearance 月数 | Newrez 系统 | 直接上报 | int | 1~12个月（常见 3/6/12） | 3 | — | Forbearance 时长 | ✅ Confirmed |
| `forbearancestatus` | Forbearance 状态编码 | Newrez 系统 | 直接上报 | int | 4 / 1 / 6（整数编码） | 4 | — | 下游 `forbearance` 文本映射；最新快照 `4`=25、`1`=5 | ✅ Confirmed |
| `forbearancetype` | Forbearance 类型编码 | Newrez 系统 | 直接上报 | int | 41 / 61 / 40（整数编码） | 41 | — | Forbearance 类型细分 | ✅ Confirmed |
| `trialagreementdate` | Trial Period 协议日期 | Newrez 系统 | 直接上报 | date | 2024-04-01~2026-05-29 | 2024-02-01 | — | Trial plan 子流程 | ✅ Confirmed |
| `trialdatecompleted` | Trial Period 完成日期 | Newrez 系统 | 直接上报 | date | YYYY-MM-DD | 2024-05-01 | — | Trial plan 子流程 | ✅ Confirmed |
| `trialbeginningduedate` | Trial 起始 due date | Newrez 系统 | 直接上报 | date | YYYY-MM-DD | 2024-02-01 | — | Trial plan 起始还款期 | ✅ Confirmed |
| `trialendingduedate` | Trial 结束 due date | Newrez 系统 | 直接上报 | date | YYYY-MM-DD | 2024-05-01 | — | Trial plan 到期节点 | ✅ Confirmed |
| `trialnumberofmonths` | Trial 期数 / 月数 | Newrez 系统 | 直接上报 | int | 3（实测仅此1值） | 3 | — | Trial plan 时长 | ✅ Confirmed |
| `trialstatus` | Trial 状态编码 | Newrez 系统 | 直接上报 | int | 8 / 1 / 4 / 7（整数编码） | 8 | — | Trial plan 状态 | ✅ Confirmed |
| `repaymentagreementdate` | Repayment Plan 协议日期 | Newrez 系统 | 直接上报 | date | 2023-04-20~2026-03-30 | 2024-05-05 | — | Repayment 子流程 | ✅ Confirmed |
| `repaymentstartdate` | Repayment Plan 开始日期 | Newrez 系统 | 直接上报 | date | 2023-04-20~2026-04-30 | 2024-05-15 | — | Repayment 子流程 | ✅ Confirmed |
| `repaymentenddate` | Repayment Plan 结束日期 | Newrez 系统 | 直接上报 | date | 2023-06-20~2027-01-30 | 2025-05-15 | — | Repayment 子流程 | ✅ Confirmed |
| `repaymenttype` | Repayment 类型编码 | Newrez 系统 | 直接上报 | int | 4（实测仅此1值） | 4 | — | Repayment 类型细分 | ✅ Confirmed |
| `repaymentstatus` | Repayment 状态编码 | Newrez 系统 | 直接上报 | int | 5 / 1 / 7 / 4 / 6 / 3（整数编码） | 5 | — | Repayment 状态 | ✅ Confirmed |
| `repaymentplandownpmt` | Repayment Plan down payment 金额 | Newrez 系统 | 直接上报 | decimal(32,16) | $0~$40,000 | 5000.00 | — | 还款计划首付款 | ✅ Confirmed |
| `repaymentplandownpmtdate` | Repayment Plan down payment 日期 | Newrez 系统 | 直接上报 | date | 2023-12-04~2026-04-23 | 2024-05-15 | — | 还款计划首付款日期 | ✅ Confirmed |
| `pradate1` | PRA 日期 1 | Newrez 系统 | 直接上报 | date | 实测始终为 NULL | — | — | Principal Reduction Alternative / PRA 相关字段，需结合 Newrez 字典确认 | ✅ Confirmed |
| `praamount1` | PRA 金额 1 | Newrez 系统 | 直接上报 | int | 实测始终为 0 | 0 | — | PRA 相关金额 | ✅ Confirmed |
| `pradate2` | PRA 日期 2 | Newrez 系统 | 直接上报 | date | 实测始终为 NULL | — | — | PRA 相关字段 | ✅ Confirmed (MySQL 实测) |
| `praamount2` | PRA 金额 2 | Newrez 系统 | 直接上报 | int | 实测始终为 NULL | — | — | PRA 相关金额 | ✅ Confirmed (MySQL 实测) |
| `pradate3` | PRA 日期 3 | Newrez 系统 | 直接上报 | date | 实测始终为 NULL | — | — | PRA 相关字段 | ✅ Confirmed (MySQL 实测) |
| `praamount3` | PRA 金额 3 | Newrez 系统 | 直接上报 | int | 实测始终为 NULL | — | — | PRA 相关金额 | ✅ Confirmed (MySQL 实测) |
| `activelmflag` | LM 活跃标志 | Newrez 系统 | 直接上报 | int | 0（未在LM）/ 1（LM进行中） | 1 | — | 下游 `lm_flag`：`1` → `Y`，否则 `N` | ✅ Confirmed |
| `create_time` | 记录创建时间 | Newrez 系统 | 直接上报 | datetime | 2024-04-09~2026-05-31（datetime） | 2023-12-14 08:30:00 | — | MySQL 管理字段 | ✅ Confirmed |
| `update_time` | 记录更新时间 | Newrez 系统 | 直接上报 | datetime | 2024-04-09~2026-05-31（datetime） | 2026-05-27 10:15:00 | — | MySQL 管理字段 | ✅ Confirmed |
| `lossmitmodtermsmodifiedtermextensionmonths` | Loss Mitigation modification term extension months | Newrez 系统 | 直接上报 | int | 0~181个月 | 6 | — | 贷款修改条款延长期数 | ✅ Confirmed |
| `deferment_flag` | Deferment 标志 | Newrez 系统 | 直接上报 | int | 0 / 1 | 1 | — | 是否存在 deferred payment / deferment | ✅ Confirmed |
| `deferment_amount` | Deferment 金额 | Newrez 系统 | 直接上报 | decimal(32,16) | $1,319~$130,729.62 | 10000.00 | — | 递延金额 | ✅ Confirmed |
| `number_pi_payments_deferred` | 递延的 PI payment 数量 | Newrez 系统 | 直接上报 | int | 1~14期 | 3 | — | 递延本金利息期数 | ✅ Confirmed |
| `shortsalenetproceedsamount` | Short Sale net proceeds 金额 | Newrez 系统 | 直接上报 | decimal(32,16) | 实测始终为 0 | 0 | — | Short Sale 净回收金额 | ✅ Confirmed |
| `shortsalecontractofferamount` | Short Sale contract offer 金额 | Newrez 系统 | 直接上报 | decimal(32,16) | 实测始终为 0 | 0 | — | Short Sale 合同报价 | ✅ Confirmed |
| `appealperiodexpirationdate` | Appeal period expiration date | Newrez 系统 | 直接上报 | date | 2024-09-17~2026-05-12 | 2024-04-15 | — | 拒绝/处置后的申诉期到期日 | ✅ Confirmed |
| `lossmitmodpreviouslydeferredcapitalizedamount` | 贷款修改中以前递延并资本化的金额 | Newrez 系统 | 直接上报 | decimal(32,16) | $0~$4,500 | 8000.00 | — | Modification 资本化金额 | ✅ Confirmed |
| `deferment_date` | Deferment 日期 | Newrez 系统 | 直接上报 | date | 2020-09-11~2026-05-14 | 2024-03-01 | — | Deferment 生效/记录日期 | ✅ Confirmed |
| `denialletterdate` | Denial letter 日期 | Newrez 系统 | 直接上报 | date | 2019-05-07~2026-05-27 | 2024-04-10 | — | LM 拒绝通知函日期 | ✅ Confirmed |
| `investorloanid` | 投资人贷款号 | Newrez 系统 | 直接上报 | varchar(100) | 格式 INV-YYYYMMDD-NNN | INV-20240115-088 | — | Newrez 对账辅助 ID | ✅ Confirmed |


---

#### 表19 LM 编码字段解码参考（BPS JOIN 实测，2026-06-01）

> **权威全量见 [表 26 `newrez.portnewrezdatadic`](#表-26newrezportnewrezdatadic--redshift-解码字典)**（本节为 BPS JOIN 观测子集）。

> 以下解码来自 `newrez.portnewrezlm JOIN bpms_dev.sync_loan_foreclosure_loss_mitigation`，以最高频率映射为准（ETL 可能因版本差异产生少量多对多）。
>
> **解码机制（代码 + DB 验证 2026-06-03）**：映射数据存于 **Redshift 字典表 `newrez.portnewrezdatadic`**（长表 `field_name | code | description`；dev MySQL 无此表），解码逻辑（`LEFT JOIN`）在 ETL 代码 `basic_data_pool_config.py:835-840`（`LMDeal→deal`/`LMProgram→program`/`LMStatus→lmc_status`/`LMDecision→final_disposition`/`BorrowerIntention`/`DenialReason`；BK 在 `:367 BKStatus`），`concat(code,'.0')` 对齐 `lmdeal` 小数串存法 —— 非硬编码 Python 字典。`field_name='LMDeal'` 字典共 **13 码**（实测数据仅出现 8 码）：1 Modification · 2 Evaluation · 3 Reinstatement · 4 Payment Plan · 5 Forbearance · 6 Short Sale · 7 DIL · 8 Loan Sale · 9 Payoff · 10 Settlement · 11 Deferment · 12 CFK · 13 Consent Judgement。

##### lmdeal — LM 交易大类

| 编码 | 解码（BPS deal字段） | 业务含义 |
|---|---|---|
| `1` | Modification | 贷款修改（永久变更利率/期限/本金） |
| `2` | Evaluation | 初始评估阶段 |
| `4` | Payment Plan | 还款计划 |
| `5` | Forbearance | 宽限期（临时暂停还款） |
| `6` | Short Sale | 短售（低于贷款余额出售） |
| `7` | DIL | Deed-in-Lieu（以房抵债） |
| `9` | Payoff | 全额还清 |
| `11` | Deferment | 递延（延期偿还部分本金） |

##### lmprogram — LM 具体方案

| 编码 | 解码（BPS program字段） | 所属大类 |
|---|---|---|
| `21` | Evaluation | Evaluation |
| `73` | Deferment | Deferment |
| `29` | Repayment Plan | Payment Plan |
| `12` | Short-term Forbearance | Forbearance |
| `396` | VA Traditional | Forbearance/Modification |
| `419` | Bridger mod | Modification |
| `240` | SLS Standard Mod | Modification |
| `348` | FHA Recovery SAPC | Modification |
| `8` | Short Sale | Short Sale |
| `10` | Deed-in-Lieu | DIL |
| `14` | Unemployment Forbearance | Forbearance |
| `25` | Payoff | Payoff |
| `151` | Disaster Forbearance | Forbearance |
| `215` | Short-term FB COVID *(RETIRED 2023-11-01)* | Forbearance |
| `273` | Standard Proprietary Modification | Modification |
| `364` | VA 30 Year Modification | Modification |
| `365` | VA 40 Year Modification | Modification |
| `405` | VASP No Trial | Modification |
| `346` | FHA Recovery Mod (40yr) | Modification |
| `358` | SLS Non-Standard Mod | Modification |
| `364` | VA 30 Year Modification | Modification |
| `365` | VA 40 Year Modification | Modification |
| `405` | VASP No Trial | Modification |
| `496` | Evaluation *(CTE实测：映射至 Evaluation，与 lmprogram=21 功能相同)* | Evaluation |
| `498` | *(实测记录极少，含义待确认)* | — |

##### lmstatus — LM 当前工作状态

| 编码 | 解码（BPS lmc_status字段） | 阶段描述 |
|---|---|---|
| `166` | Pending Financials | 等待借款人提交财务材料 |
| `112` | Workout Denial | 本轮 LM 已被拒绝 |
| `5` | Document Follow-up | 跟进补充缺失材料 |
| `20` | Book mod | 贷款修改正式记账中 |
| `113` | Monitor Forbearance | 监控宽限期执行情况 |
| `140` | Deferment Agreement Ordered | 递延协议已下单/签署 |
| `139` | Deferment Plan In Progress | 递延计划进行中 |
| `25` | Monitor for pmts/funds | 监控借款人是否正常还款 |
| `13` | Follow up for 1st Trial Payment | 跟进首期试验期还款 |
| `172` | Liquidation Referral | 清算/处置转介 |
| `116` | Not Assigned | 未分配状态 |
| `45` | Countered by Supervisor | 主管已反驳/调整方案 |
| `135` | DIL Sent for Recording | 以房抵债文件已提交登记 |
| `47` | Book mod | 记账中（另一变体） |
| `48` | Workout Denial | 拒绝（另一代码） |
| `24` | Workout Denial | 拒绝（另一代码） |
| `24` | Awaiting investor approval | 等待投资人审批 |
| `47` | Monitor for Mod Agreement | 监控修改协议执行 |
| `126` | DIL Title Ordered | DIL 产权调查已下单 |
| `127` | Negotiate DIL liens | 与次级留置权方协商 |
| `185` / `186` | Follow up for 1st Trial Payment / Book mod | 跟进首期 Trial 还款 / 记账 |
| `187` | Solicitation Offered | 已发出方案邀约 |

##### lmdecision — LM 最终处置结论

| 编码 | 解码（BPS final_disposition字段） | 对 FCL 的影响 |
|---|---|---|
| `99` | Pending（进行中） | FCL 暂停 |
| `1` | Modification Complete | FCL 撤销/暂停 |
| `3` | DIL Complete | FCL 完成（DIL方式） |
| `4` | Forbearance Complete | 宽限完成，FCL 继续评估 |
| `5` | Reinstated/Current | 借款人已复原还款，FCL 撤销 |
| `6` | Referral to FC | LM 失败，正式转回 FCL |
| `7` | Not Eligible for Loss Mitigation | 不符合 LM 资格 |
| `10` | Request Incomplete/Failed to Provide Information | 申请不完整，FCL 继续 |
| `11` | LMS Opened in Error | 系统错误开立，忽略 |
| `14` | Deferment Completed | 递延完成 |
| `17` | Full Pay Off | 全额还清 |
| `18` | FC Sale Held | 拍卖已执行 |

##### denialreason — LM 拒绝原因

| 编码 | 解码（BPS denialreason字段） |
|---|---|
| `109` | Loan not due for 3 or more monthly payments |
| `76` | HAMP Sunset |
| `4` | Withdrawal of Request/Non-Acceptance |
| `6` | Ineligible Borrower |
| `75` | Declined Mod Review in favor of SS/DIL |
| `21` | Request Incomplete/Failed to Provide Documentation |
| `118` | Loan not 90+ DPD |
| `34` | Ineligible Borrower: Not a Natural Person |
| `30` | Failed Plan |
| `124` | Hardship not resolved |
| `86` | Request Withdrawn |
| `50` | Request Withdrawn Before Offer |
| `108` | Unable to achieve target payment |
| `2` | Trial Plan Default |
| `9` | Investor Not Participating |
| `32` | HDTI out of range |
| `78` | Buyer walked (SS) |
| `11` | Default Not Imminent |


#### 验证 SQL — LM 编码解码实测

> 以下 SQL 在 `mcp__mysql_bpms_dev__mysql_query` 执行（跨库 JOIN）。  
> **JOIN key**：`loanid` + `dealstartdate = cycle_opened_date`（同一 LM 周期开始日，两表命名不同但含义相同）。  
> **⚠️ 快照放大问题**：`portnewrezlm` 是日快照表，同一 `(loanid, dealstartdate)` 存在多行（一天一行，共 887 天）。直接 JOIN 会产生笛卡尔积，导致 1 个 code 出现多个 deal 文本。**修正方法**：用 `ROW_NUMBER()` 每个 LM 周期只取最新快照，再 JOIN（见下方 CTE 模式）。  
> **lmdecision 中残留少量 "Pending" 次级映射**：这是因为 BPS 记录写入时该周期还在进行中，Newrez 后来才更新 decision 码为最终值，属正常历史数据行为，以 cnt 最高的非 Pending 映射为主映射。

```sql
-- 公共 CTE：每个 LM 周期只取最新快照（解决日快照笛卡尔积放大问题）
-- 将 latest_lm 替换到各 SQL 的 FROM 子句中使用

WITH latest_lm AS (
    SELECT loanid, dealstartdate,
           lmdeal, lmprogram, lmstatus, lmdecision, denialreason, borrowerintention,
           ROW_NUMBER() OVER (PARTITION BY loanid, dealstartdate ORDER BY dataasof DESC) AS rn
    FROM newrez.portnewrezlm
)

-- SQL-D1：lmdeal → deal（LM 交易大类）
SELECT l.lmdeal, b.deal, COUNT(*) AS cnt
FROM latest_lm l
JOIN bpms_dev.sync_loan_foreclosure_loss_mitigation b
  ON l.loanid = b.loanid AND l.dealstartdate = b.cycle_opened_date
WHERE l.rn = 1 AND l.lmdeal IS NOT NULL
  AND b.deal IS NOT NULL AND b.deal != '' AND b.deal NOT REGEXP '^[0-9]'
GROUP BY l.lmdeal, b.deal ORDER BY l.lmdeal, cnt DESC;

-- SQL-D2：lmprogram → program（LM 具体方案）
SELECT l.lmprogram, b.program, COUNT(*) AS cnt
FROM latest_lm l
JOIN bpms_dev.sync_loan_foreclosure_loss_mitigation b
  ON l.loanid = b.loanid AND l.dealstartdate = b.cycle_opened_date
WHERE l.rn = 1 AND l.lmprogram IS NOT NULL
  AND b.program IS NOT NULL AND b.program != '' AND b.program NOT REGEXP '^[0-9]'
GROUP BY l.lmprogram, b.program ORDER BY l.lmprogram, cnt DESC;

-- SQL-D3：lmstatus → lmc_status（LM 当前工作状态）
SELECT l.lmstatus, b.lmc_status, COUNT(*) AS cnt
FROM latest_lm l
JOIN bpms_dev.sync_loan_foreclosure_loss_mitigation b
  ON l.loanid = b.loanid AND l.dealstartdate = b.cycle_opened_date
WHERE l.rn = 1 AND l.lmstatus IS NOT NULL
  AND b.lmc_status IS NOT NULL AND b.lmc_status != '' AND b.lmc_status NOT REGEXP '^[0-9]'
GROUP BY l.lmstatus, b.lmc_status ORDER BY l.lmstatus, cnt DESC;

-- SQL-D4：lmdecision → final_disposition（LM 最终处置结论）
SELECT l.lmdecision, b.final_disposition, COUNT(*) AS cnt
FROM latest_lm l
JOIN bpms_dev.sync_loan_foreclosure_loss_mitigation b
  ON l.loanid = b.loanid AND l.dealstartdate = b.cycle_opened_date
WHERE l.rn = 1 AND l.lmdecision IS NOT NULL
  AND b.final_disposition IS NOT NULL AND b.final_disposition != '' AND b.final_disposition NOT REGEXP '^[0-9]'
GROUP BY l.lmdecision, b.final_disposition ORDER BY l.lmdecision, cnt DESC;

-- SQL-D5：denialreason → denialreason text（拒绝原因）
SELECT l.denialreason, b.denialreason AS decoded, COUNT(*) AS cnt
FROM latest_lm l
JOIN bpms_dev.sync_loan_foreclosure_loss_mitigation b
  ON l.loanid = b.loanid AND l.dealstartdate = b.cycle_opened_date
WHERE l.rn = 1 AND l.denialreason IS NOT NULL AND l.denialreason != 0
  AND b.denialreason IS NOT NULL AND b.denialreason != ''
GROUP BY l.denialreason, b.denialreason ORDER BY cnt DESC;

-- SQL-D6：borrowerintention → borrower_intentions（借款人意向）
SELECT l.borrowerintention, b.borrower_intentions, COUNT(*) AS cnt
FROM latest_lm l
JOIN bpms_dev.sync_loan_foreclosure_loss_mitigation b
  ON l.loanid = b.loanid AND l.dealstartdate = b.cycle_opened_date
WHERE l.rn = 1 AND l.borrowerintention IS NOT NULL AND l.borrowerintention != 0
  AND b.borrower_intentions IS NOT NULL AND b.borrower_intentions != ''
GROUP BY l.borrowerintention, b.borrower_intentions ORDER BY l.borrowerintention;
```


### 表 20：`newrez.portnewrezbk` — Newrez Bankruptcy 原始日报表

| 属性 | 值 |
|------|----|
| **表名** | `portnewrezbk` |
| **所属 Schema** | MySQL `newrez` |
| **数据层** | Raw / Servicer-specific（Newrez/Shellpoint 原始 BK 日报落地表） |
| **业务作用** | Newrez 破产全流程追踪表，含破产申请/章节/状态、MFR（解除中止动议）、POC（债权申报）、Cramdown、对抗性诉讼、受托人资产、还款计划确认及暂记款余额等子流程节点 |
| **业务意图** | 作为 Newrez BK 原始事实表，识别贷款是否处于破产保护（破产会暂停 FCL），并为 BPS Bankruptcy 面板提供章节/状态/MFR/POC 等业务上下文 |
| **上游来源** | Newrez/Shellpoint `Bankruptcy` / `AresOversight_Bankruptcy` 文件；映射见 `flow/basic_data/load_servicer_data_config/servicer_config.py` |
| **下游使用** | Redshift 中间表（`WHERE LENGTH(TRIM(bkstatus))>0`，按 `loanid+bkfileddate` 去重最新快照）→ `bpms_dev.sync_loan_foreclosure_bankruptcy`（表23，`bkstatus`/`bkstage` 经 `portnewrezdatadic` 解码）；`activebkflag` 驱动主表 `variance_active_bankruptcy`（表17）；见 doc 13 §2.2 / §6 |
| **Foreclosure 关系** | 间接但关键：活跃破产（`activebkflag=1`）触发 FCL Hold/暂停；破产 Dismiss/MFR Granted 后 FCL 通常恢复 |
| **主键 / 索引** | `id` 自增主键；业务 join key 通常为 `loanid + dataasof`；BK 去重常按 `loanid + bkfileddate` |
| **代码血缘（PrefectFlow）** | 原始落地：`flow/basic_data/load_servicer_data_config/servicer_config.py` `SHELL_POINT_FILE_TABLE_MAP`：文件 `Bankruptcy`/`AresOversight_Bankruptcy` → `newrez.portnewrezbk`(L222,244)。下游消费：`flow/basic_data/basic_data_config/basic_data_pool_config.py` `CREATE_BASIC_DATA_FCL_BANKRUPTCY` Newrez 分支(L349-370)——`JOIN newrez.portnewrezgeneral`(L365-366)、`portnewrezdatadic` 解码 BKStatus(L367)、按 `loanid,bkfileddate` 去重(L364) → Redshift `port.basic_data_loan_foreclosure_bankruptcy` → BPS 表23 |
| **DB验证** | 2026-06-01 MySQL 实测：60列；全表 1,576,896 行；最新快照 `dataasof=2026-05-31` 共 5,052 行。取值范围/填充率取自最新快照（脚本 `scripts/extract_table_stats.py`） |

> ⚠️ `bkstatus`/`bkstage`/`bkremovalcode`/`mfrhearingresults` 等为 **Newrez 内部数值编码**，下游写入 BPS 时经 `newrez.portnewrezdatadic` 解码为文本（见表23 与 doc 13 Q7）。最新快照中仅 32 笔有破产记录（`activebkflag` 等填充约 1%），属正常（多数活跃贷款无破产）。

#### 字段说明（60列）

| 字段名 | 字段业务含义 | 来源数据 | 计算/推导逻辑 | 数据类型 | 取值范围 | 典型取值 | 上游字段 | 下游用途 | 备注 |
|--------|-----------|--------|-----------|----------|---------|---------|--------|--------|------|
| `id` | MySQL 自增主键 | Newrez 系统 | 直接上报 | bigint NOT NULL | 1824745 ~ 1829796 | 1824745 | — | 技术主键 | ✅；填充 5052/5052=100% |
| `loanid` | Bridger/投资人贷款 ID | Newrez 系统 | 直接上报 | varchar(255) | 文本，5052种（样例 0695996231 … 7727006148） | 0695996231 | — | 按 `loanid+dataasof` 关联其他 Newrez 表 | ✅；填充 5052/5052=100% |
| `dataasof` | 数据快照日期 | Newrez 系统 | 直接上报 | date NOT NULL | {2026-05-31} | 2026-05-31 | — | 每日报表日期 | ✅；填充 5052/5052=100% |
| `shellpointloanid` | Newrez/Shellpoint 服务商贷款号 | Newrez 系统 | 直接上报 | varchar(255) | 文本，5052种（样例 0578252925 … 9799754446） | 0578252925 | — | 下游 `svcloanid` | ✅；填充 5052/5052=100% |
| `bkfileddate` | 破产申请日 | Newrez 系统 | 直接上报 | date | {2010-06-03, 2025-04-30, 2024-02-09, 2017-01-18, 2024-01-13, 2008-06-16, 2009-06-01, 2014-12-24, 2026-02-26, 2024-02-01, 2023-11-20, 2022-08-25, 2025-04-18, 2024-03-25, 2026-03-27, 2024-02-06} 等29种 | 2010-06-03 | — | BK 时间线起点 | ✅；填充 32/5052=1% |
| `bkstatus` | 破产状态编码（Newrez 内部数值码） | Newrez 系统 | 直接上报 | int | {2, 1, 3, 5, 4}（5种） | 2 | — | 解码后→ `bankruptcy_status`（表23） | 🟡 数值码，需字典解码；填充 32/5052=1% |
| `bkremovalcode` | 破产终止原因编码（1=Dismissed/2=Discharged 等） | Newrez 系统 | 直接上报 | int | {1, 2, 4, 3}（4种） | 1 | — | 破产结案原因 | 🟡 数值码；填充 20/5052=0% |
| `bkremovaldate` | 破产程序终止日 | Newrez 系统 | 直接上报 | date | {2014-09-24, 2024-06-24, 2022-03-14, 2024-04-11, 2013-08-15, 2009-09-18, 2015-05-08, 2022-09-30, 2026-04-14, 2025-07-29, 2026-03-25, 2023-06-21, 2022-12-30, 2021-06-08, 2023-04-20, 2026-01-08} 等17种 | 2014-09-24 | — | → `variance_completed_bankruptcy` 判定 | ✅；填充 20/5052=0% |
| `bkchapter` | 破产章节（7=清算/11=重组/13=个人还款） | Newrez 系统 | 直接上报 | int | {13, 7, 11}（3种） | 13 | — | → `chapter`（表23） | ✅；填充 32/5052=1% |
| `bkcasenumber` | 破产案件编号 | Newrez 系统 | 直接上报 | varchar(255) | {1033613, 2500228, 2410065, 1701437, 2400439, 881575, 981704, 1482201, 2611401, 2430197, 2331915, 2213209, 2503460, 2421405, 2680351, 2310152} 等29种 | 1033613 | — | 案件追溯 | ✅；填充 32/5052=1% |
| `bkpostpetitionduedate` | 破产申请后贷款应付日 | Newrez 系统 | 直接上报 | date | {2026-05-01, 2026-02-01, 2026-04-01, 2022-04-01, 2024-02-01, 2026-05-06, 2026-07-01, 2022-09-01, 2025-05-01, 2024-04-01, 2023-11-01, 2023-04-01, 2025-12-01, 2025-09-01, 2018-09-01, 2021-04-01} 等18种 | 2026-05-01 | — | → `post_petition_due_date`（表23） | ✅；填充 22/5052=0% |
| `prepetitionduedate` | 破产申请前贷款应付日 | Newrez 系统 | 直接上报 | date | 2022-11-01 ~ 2026-09-01 | 2022-11-01 | — | Pre-petition 欠款基准 | ✅；填充 5052/5052=100% |
| `pocfileddate` | 债权申报（POC）提交日 | Newrez 系统 | 直接上报 | date | {2010-06-17, 2025-08-05, 2022-10-17, 2025-09-22, 2023-11-15, 2023-09-30, 2025-06-27, 2001-01-01, 2024-03-29, 2026-05-04, 2017-03-31, 2024-04-19} | 2010-06-17 | — | → `proof_of_claim_date`（表23） | ✅；填充 13/5052=0% |
| `dischargeddate` | 债务免责（Discharge）日 | Newrez 系统 | 直接上报 | date | {2014-09-24, 2026-01-08, 2021-06-08, 2022-12-30, 2023-06-21, 2025-07-29, 2024-06-24, 2015-04-17, 2009-09-18, 2013-08-15, 2024-04-08, 2022-03-14} | 2014-09-24 | — | BK 完结情形之一 | ✅；填充 15/5052=0% |
| `dismisseddate` | 破产驳回（Dismiss）日 | Newrez 系统 | 直接上报 | date | {2025-12-08, 2026-04-14, 2022-09-30} | 2025-12-08 | — | BK 完结情形之一；驳回后 FCL 可恢复 | ✅；填充 3/5052=0% |
| `mfrfileddate` | 解除自动中止动议（MFR）提交日 | Newrez 系统 | 直接上报 | date | {2025-11-04, 2025-11-21, 2026-04-29, 2026-02-04, 2025-06-10} | 2025-11-04 | — | → `mfr_filed_date`（表23） | ✅；填充 5/5052=0% |
| `mfrhearingdate` | MFR 听证日 | Newrez 系统 | 直接上报 | date | {2025-12-02, 2026-05-15, 2026-03-09, 2025-06-24} | 2025-12-02 | — | MFR 子流程 | ✅；填充 4/5052=0% |
| `mfrgranteddate` | MFR 批准日（批准后可推进 FCL） | Newrez 系统 | 直接上报 | date | {2025-12-05, 2026-03-11, 2025-06-25} | 2025-12-05 | — | MFR 子流程 | ✅；填充 3/5052=0% |
| `trusteeassetflag` | 受托人资产标志（1=有可分配资产） | Newrez 系统 | 直接上报 | int | {0, 1}（2种） | 0 | — | Ch7 资产案件标识 | ✅；填充 32/5052=1% |
| `trusteeassetdate` | 受托人资产认定日 | Newrez 系统 | 直接上报 | date | {2025-11-09, 2023-04-19, 2024-04-16, 2025-06-01, 2024-02-22} | 2025-11-09 | — | Ch7 子流程 | ✅；填充 5/5052=0% |
| `planconfirmationdate` | 还款计划确认日（Ch13 Plan Confirmed） | Newrez 系统 | 直接上报 | date | {2014-03-24, 2023-04-20, 2024-08-15, 2024-07-11, 2024-02-23, 2024-05-07, 2017-03-20, 2024-06-25} | 2014-03-24 | — | Ch13 子流程 | ✅；填充 11/5052=0% |
| `bkstage` | 破产阶段编码（Newrez 内部数值码） | Newrez 系统 | 直接上报 | int | {8, 0, 4, 10, 21, 7, 17}（7种） | 8 | — | 解码后→ `legal_status`（表23） | 🟡 数值码，需字典解码；填充 32/5052=1% |
| `bkfirm` | 破产律师事务所名称 | Newrez 系统 | 直接上报 | varchar(255) | {Padgett Law Group, Aldridge Pite, LLP, Bonial & Associates, P.C., McCalla Raymer Leibert Pierce, LLP, Hill Wallack} | Padgett Law Group | — | 律所信息 | ✅；填充 12/5052=0% |
| `reaffirmationdate` | 重申债务确认（Reaffirmation）日 | Newrez 系统 | 直接上报 | date | {2015-01-14} | 2015-01-14 | — | Ch7 重申子流程 | ✅；填充 1/5052=0% |
| `trusteeabandonmentdate` | 受托人放弃资产日 | Newrez 系统 | 直接上报 | date | 实测全为 NULL | — | — | Ch7 子流程 | ✅；填充 0/5052=0% |
| `pocreferreddate` | POC 转介日 | Newrez 系统 | 直接上报 | date | {2025-07-07, 2025-06-06, 2025-07-17, 2026-05-26, 2026-05-21, 2025-06-04, 2026-04-03, 2024-02-13} | 2025-07-07 | — | POC 子流程 | ✅；填充 8/5052=0% |
| `pocbardate` | POC 申报截止日（Bar Date） | Newrez 系统 | 直接上报 | date | {2010-10-21, 2024-04-16, 2024-04-19, 2017-05-24, 2026-05-07, 2024-04-11, 2024-01-29, 2025-06-27, 2026-06-05, 2024-05-28, 2023-07-24, 2026-06-10, 2024-01-02, 2025-09-22, 2022-10-27, 2025-08-05} | 2010-10-21 | — | POC 截止节点 | ✅；填充 19/5052=0% |
| `mfrreferred` | MFR 转介日 | Newrez 系统 | 直接上报 | date | {2025-10-21, 2025-10-24, 2026-04-08, 2026-01-07, 2025-11-10, 2025-05-15} | 2025-10-21 | — | MFR 子流程 | ✅；填充 6/5052=0% |
| `mfrhearingresults` | MFR 听证结果编码 | Newrez 系统 | 直接上报 | int | {0, 3, 4, 5}（4种） | 0 | — | 解码后→ `mfr_status`（表23） | 🟡 数值码；填充 32/5052=1% |
| `cramdowndatereferred` | Cramdown 转介日 | Newrez 系统 | 直接上报 | date | 实测全为 NULL | — | — | Cramdown 子流程 | ✅；填充 0/5052=0% |
| `cramdownobjectionfileddate` | Cramdown 异议提交日 | Newrez 系统 | 直接上报 | date | 实测全为 NULL | — | — | Cramdown 子流程 | ✅；填充 0/5052=0% |
| `cramdownresultdate` | Cramdown 结果日 | Newrez 系统 | 直接上报 | date | 实测全为 NULL | — | — | Cramdown 子流程 | ✅；填充 0/5052=0% |
| `cramdownhearingresults` | Cramdown 听证结果编码 | Newrez 系统 | 直接上报 | int | {0}（1种） | 0 | — | Cramdown 结果 | 🟡 数值码；填充 32/5052=1% |
| `adversarialactionfileddate` | 对抗性诉讼（Adversary）提交日 | Newrez 系统 | 直接上报 | date | 实测全为 NULL | — | — | Adversary 子流程 | ✅；填充 0/5052=0% |
| `adversarialhearingdate` | 对抗性诉讼听证日 | Newrez 系统 | 直接上报 | date | 实测全为 NULL | — | — | Adversary 子流程 | ✅；填充 0/5052=0% |
| `adversarialresultdate` | 对抗性诉讼结果日 | Newrez 系统 | 直接上报 | date | 实测全为 NULL | — | — | Adversary 子流程 | ✅；填充 0/5052=0% |
| `adversarialresults` | 对抗性诉讼结果编码 | Newrez 系统 | 直接上报 | int | {0}（1种） | 0 | — | Adversary 结果 | 🟡 数值码；填充 32/5052=1% |
| `cramdownflag` | Cramdown 标志（1=存在 cramdown） | Newrez 系统 | 直接上报 | int | {0}（1种） | 0 | — | 本金 cramdown 标识 | ✅；填充 32/5052=1% |
| `bankruptcypaymenttype` | 破产还款类型编码 | Newrez 系统 | 直接上报 | int | {1, 2, 0}（3种） | 1 | — | 还款类型细分 | 🟡 数值码；填充 12/5052=0% |
| `debtorintention` | 债务人意向编码（保留/放弃房产） | Newrez 系统 | 直接上报 | int | {1, 0}（2种） | 1 | — | 债务人意向 | 🟡 数值码；填充 12/5052=0% |
| `jointfilerflag` | 是否共同申请人（1=joint） | Newrez 系统 | 直接上报 | int | {0, 1}（2种） | 0 | — | 共同申请标识 | ✅；填充 12/5052=0% |
| `activebkflag` | 是否在破产保护中（1=是/0=否） | Newrez 系统 | 直接上报 | int | {0, 1}（2种） | 0 | — | → `variance_active_bankruptcy`；BK 活跃判定 | ✅；填充 5052/5052=100% |
| `apocfileddate` | 修订债权申报（APOC）提交日 | Newrez 系统 | 直接上报 | date | {2025-09-23, 2025-08-05} | 2025-09-23 | — | APOC 子流程 | ✅；填充 2/5052=0% |
| `apocreferraldate` | APOC 转介日 | Newrez 系统 | 直接上报 | date | {2025-09-23, 2025-08-29} | 2025-09-23 | — | APOC 子流程 | ✅；填充 2/5052=0% |
| `reasonforapoc` | APOC 原因（文本） | Newrez 系统 | 直接上报 | varchar(255) | {Error with Claim} | Error with Claim | — | APOC 原因说明 | ✅；填充 2/5052=0% |
| `attorney` | 受理律师/律所名称 | Newrez 系统 | 直接上报 | varchar(255) | {Aldridge Pite, LLP} | Aldridge Pite, LLP | — | 律师信息（APOC 相关） | ✅；填充 2/5052=0% |
| `create_time` | 记录创建时间 | Newrez 系统 | 直接上报 | datetime | {2026-06-01 21:37:44} | 2026-06-01 21:37:44 | — | MySQL 管理字段（实测=落库时间） | ✅；填充 5052/5052=100% |
| `update_time` | 记录更新时间 | Newrez 系统 | 直接上报 | datetime | {2026-06-01 21:37:44} | 2026-06-01 21:37:44 | — | MySQL 管理字段 | ✅；填充 5052/5052=100% |
| `bkrepayplanpaymentcount` | 破产还款计划期数 | Newrez 系统 | 直接上报 | int | {0, 60, 36}（3种） | 0 | — | Ch13 计划期数 | ✅；填充 12/5052=0% |
| `bksourceoffundscode` | 资金来源编码 | Newrez 系统 | 直接上报 | int | 实测全为 NULL | — | — | 还款资金来源 | 🟡 数值码；填充 0/5052=0% |
| `bkpoccourtreceiveddate` | POC 法院收到日 | Newrez 系统 | 直接上报 | date | {2025-09-22, 2026-05-04, 2024-04-19} | 2025-09-22 | — | POC 子流程 | ✅；填充 3/5052=0% |
| `bkrcurrentstatusdate` | 当前破产状态生效日期 | Newrez 系统 | 直接上报 | date | {2026-04-27, 2026-04-15, 2025-07-12, 2023-10-24, 2026-04-01, 2026-04-08, 2026-05-26, 2026-03-27, 2023-11-20, 2024-02-01, 2026-02-26, 2024-02-09} | 2026-04-27 | — | → `status_date`（表23） | ✅；填充 12/5052=0% |
| `bkborrowerintent` | 借款人破产意向编码 | Newrez 系统 | 直接上报 | int | {1, 0}（2种） | 1 | — | 借款人意向 | 🟡 数值码；填充 12/5052=0% |
| `bkpostpetitionpaymentcurrent` | 破产后应付款当前额 | Newrez 系统 | 直接上报 | decimal(32,16) | {0, 1805.15, 2437.01, 2192, 1232.3, 805.5, 4103.99, 1427.01}（8种） | $0 | — | Post-petition 还款监控 | ✅；填充 12/5052=0% |
| `bkcramdownpercent` | Cramdown 比例（本金削减%） | Newrez 系统 | 直接上报 | decimal(32,16) | 实测全为 NULL | — | — | Cramdown 金额计算 | ✅；填充 0/5052=0% |
| `bkpostsuspensebalance` | 破产后暂记款（suspense）余额 | Newrez 系统 | 直接上报 | decimal(32,16) | {0}（1种） | $0 | — | 暂记款监控 | ✅；填充 8/5052=0% |
| `bkpresuspensebalance` | 破产前暂记款余额 | Newrez 系统 | 直接上报 | decimal(32,16) | {0}（1种） | $0 | — | 暂记款监控 | ✅；填充 7/5052=0% |
| `investorloanid` | 投资人贷款号 | Newrez 系统 | 直接上报 | varchar(100) | 文本，5051种（样例 1000006548 … 958710） | 1000006548 | — | 投资人对账 ID | ✅；填充 5052/5052=100% |
| `bkfilingstate` | 破产申请州 | Newrez 系统 | 直接上报 | varchar(255) | {OH, IL, FL, CA, TX, AZ, RI, CO, TN, NE, WV, MN, GA, NV, MD, PA} | OH | — | 管辖州 | ✅；填充 32/5052=1% |
| `bkfilingregion` | 破产申请法院辖区（含 Division） | Newrez 系统 | 直接上报 | varchar(255) | {Southern District Of Ohio, Dayton, Central District of Illinois, Peoria Division, (None), Southern District of Ohio, Dayton Division   , Northern District of Illinois, Eastern Division, Eastern District of California, Sacramento Division, District of Rhode Island (Providence), Northern District Of Illinois, Chicago Division, Central District Of California, Riverside Division, Mian District Of Colorado, Denver Division, Main District of Arizona, Phoenix Division, District of Nebraska, Omaha Division                                , Northern District of WV (Martinsburg), Northern District of Florida, Gainesville Division                    , District Of Arizona, Phoenix Division, District of Minnesota, St. Paul Division} 等23种 | Southern District Of Ohio, Dayton | — | 联邦破产法院辖区 | ✅；填充 32/5052=1% |

---

### 表 21：`bpms_dev.sync_loan_foreclosure_hold` — BPS Hold 历史记录表

| 属性 | 值 |
|------|----|
| **表名** | `sync_loan_foreclosure_hold` |
| **所属 Schema** | MySQL `bpms_dev`（BPS 应用数据库） |
| **数据层** | Layer 5 — BPS Application Layer |
| **业务作用** | 贷款 FCL 生命周期内的**完整 Hold 历史**（每次 Hold 变更追加一行），驱动 BPS Loan Foreclosure 详情页 Hold 面板 |
| **业务意图** | Newrez `portnewrezfc` 仅保留 3 个当前 Hold 槽位（fchold1/2/3）；BPS 每日同步将每次变更落为新行，从而累积完整 Hold 历史（单贷款可远多于 3 行） |
| **上游来源** | Redshift `port.basic_data_loan_foreclosure_hold`（源 `portnewrezfc`，`WHERE fchold1startdate IS NOT NULL`，3 槽 UNPIVOT，按 `loanid,description,start_date` 去重）→ `JOIN port.portfunding`；DELETE+INSERT 全量重写（见 doc 13 §4） |
| **下游使用** | BPS Hold 面板（Description/Start/End）；入库链路与主 FCL 表独立（不要求 `fcreferraldate IS NOT NULL`） |
| **Foreclosure 关系** | 直接：Hold（BK/LM/Court Delay 等）暂停 FCL 计时，是 SLA 方差分析的事件来源 |
| **主键 / 索引** | `id` 自增主键；业务键 `loanid + description + description_start_date` |
| **代码血缘（PrefectFlow）** | 编排 `flow/bps/sync_asset_management.py`（`10-FORECLOSURE_HOLD`）→ `flow/bps/bps_config/asset_managment_config.py` `GEN_FORECLOSURE_HOLD`(L847，3 槽 UNPIVOT + `JOIN port.portfunding` L890) → `util/df_db_util.py` `sync_to_mysql`(DELETE+INSERT)。Redshift 基表 `port.basic_data_loan_foreclosure_hold`：`flow/basic_data/basic_data_config/basic_data_pool_config.py`(L466-768，源 `portnewrezfc` L693，按 `loanid,hold1_start_date` 去重 L765) |
| **DB验证** | 2026-06-01 实测：15列；338 行（85 个 distinct svcloanid）；`description` 40 种文本（如 `Loss Mitigation Workout` / `Court Delay`）；脚本 `scripts/extract_table_stats.py` |

> 说明：本表**不存储 Hold 预计结束日**；主表 `sync_loan_foreclosure.variance_estimated_hold_days` 的 projected 来源是 `portnewrezfc` 的 `fchold*projectedenddate`（见表17 与 doc 13 §4.4）。

#### 字段说明（15列）

| 字段名 | 字段业务含义 | 来源数据 | 计算/推导逻辑 | 数据类型 | 取值范围 | 典型取值 | 上游字段 | 下游用途 | 备注 |
|--------|-----------|--------|-----------|----------|---------|---------|--------|--------|------|
| `id` | 自增主键 | BPS ETL | AUTO_INCREMENT | bigint NOT NULL | 10842 ~ 11540 | 10842 | — | 技术主键 | ✅；填充 338/338=100% |
| `loanid` | 系统贷款 ID | BPS ETL | 直接写入 | bigint | 7727000012 ~ 700082870000041 | 7727000012 | `port.basic_data_loan_fcl.loanid` | 贷款 join key | ✅；填充 338/338=100% |
| `svcloanid` | Servicer 内部贷款号 | BPS ETL | 直接写入 | varchar(64) | 文本，85种（样例 0578252925 … 7000329258） | 0578252925 | — | Servicer 对账 | ✅；填充 338/338=100% |
| `fctrdt` | 数据来源批次日期 | BPS ETL | 直接写入 | date | 2023-12-17 ~ 2026-03-13 | 2023-12-17 | — | 快照批次追踪 | ✅；填充 338/338=100% |
| `description` | Hold 原因描述（文本） | BPS ETL | 源 fchold1/2/3description（UNPIVOT） | varchar(256) | 文本，40种（样例 ACT(PA) Letter/Demand Letter/NOI Expiration … Veterans Affairs Servicing Purchase (VASP)） | ACT(PA) Letter/Demand Letter/NOI Expiration | `newrez.portnewrezfc.fchold*description` | BPS Hold 面板 Description 列 | ✅；填充 297/338=88% |
| `description_start_date` | Hold 开始日 | BPS ETL | 源 fchold1/2/3startdate | date | 2019-10-24 ~ 2026-03-13 | 2019-10-24 | `newrez.portnewrezfc.fchold*startdate` | Hold 面板 Start Date | ✅；填充 338/338=100% |
| `description_end_date` | Hold 结束日（NULL=仍持续） | BPS ETL | 源 fchold1/2/3enddate | date | 2019-11-15 ~ 2026-03-12 | 2019-11-15 | `newrez.portnewrezfc.fchold*enddate` | Hold 面板 End Date | ✅；填充 316/338=93% |
| `create_user` | 记录创建用户 | BPS 应用层 | 直接写入 | bigint | 实测全为 NULL | — | — | 审计追踪 | dev 未回填；填充 0/338=0% |
| `create_dept` | 记录创建部门 | BPS 应用层 | 直接写入 | bigint | 实测全为 NULL | — | — | 审计追踪 | dev 未回填；填充 0/338=0% |
| `create_time` | 记录创建时间 | BPS 应用层 | 直接写入 | datetime | 实测全为 NULL | — | — | 审计追踪 | dev 未回填；填充 0/338=0% |
| `update_user` | 最后更新用户 | BPS 应用层 | 直接写入 | bigint | 实测全为 NULL | — | — | 审计追踪 | dev 未回填；填充 0/338=0% |
| `update_time` | 最后更新时间 | BPS 应用层 | 直接写入 | datetime | 实测全为 NULL | — | — | 审计追踪 | dev 未回填；填充 0/338=0% |
| `status` | 记录状态（0=正常） | BPS 应用层 | DEFAULT 0 | int NOT NULL | {0}（1种） | 0 | — | 软停用标志 | ✅；填充 338/338=100% |
| `is_deleted` | 是否软删除（0=未删） | BPS 应用层 | DEFAULT 0 | int NOT NULL | {0}（1种） | 0 | — | 软删除标志 | ✅；填充 338/338=100% |
| `tenant_id` | 租户 ID | BPS 应用层 | 直接写入 | varchar(12) NOT NULL | {000000, 984018} | 000000 | — | 多租户支持 | ✅；填充 338/338=100% |

---

### 表 22：`bpms_dev.sync_loan_foreclosure_loss_mitigation` — BPS Loss Mitigation 周期表

| 属性 | 值 |
|------|----|
| **表名** | `sync_loan_foreclosure_loss_mitigation` |
| **所属 Schema** | MySQL `bpms_dev` |
| **数据层** | Layer 5 — BPS Application Layer |
| **业务作用** | 贷款完整 Loss Mitigation 周期历史（每个 LM 周期一行），驱动 BPS LM Cycle 面板 |
| **业务意图** | 追踪每轮 workout（Evaluation→Modification/Forbearance/Short Sale/DIL）的开/关、方案与最终处置；LM 失败通常转回 FCL，成功则暂停/终止 FCL |
| **上游来源** | Redshift（源 `newrez.portnewrezlm`，`WHERE dealstartdate IS NOT NULL`，按 `loanid,dealstartdate` 去重；6 个整型编码经 `portnewrezdatadic` 解码）→ `JOIN port.portfunding`；合并 Newrez+Carrington+Capecodfive（见 doc 13 §5） |
| **下游使用** | BPS LM Cycle 面板（Deal/Program/Status/Cycle Dates/Final Disposition 等 10 列）；编码↔文本解码对照见表19「LM 编码解码参考」 |
| **Foreclosure 关系** | 直接：LM 周期影响 FCL Hold/恢复；`final_disposition` 决定 FCL 是否继续 |
| **主键 / 索引** | `id` 自增主键；业务键 `loanid + deal + cycle_opened_date` |
| **代码血缘（PrefectFlow）** | 编排 `flow/bps/sync_asset_management.py`（`8-FORECLOSURE_LM`）→ `flow/bps/bps_config/asset_managment_config.py` `GEN_FORECLOSURE_LM`(L799，`JOIN port.portfunding` L814) → `util/df_db_util.py` `sync_to_mysql`(DELETE+INSERT)。Redshift 基表 `port.basic_data_loan_foreclosure_loss_mitigation`：`flow/basic_data/basic_data_config/basic_data_pool_config.py`(L773-1041，源 `portnewrezlm` L833，按 `loanid,dealstartdate` 去重 L832；**编码解码 `LEFT JOIN newrez.portnewrezdatadic`**：LMDeal/LMProgram/LMStatus/LMDecision/BorrowerIntention/DenialReason L835-840) |
| **DB验证** | 2026-06-01 实测：22列；544 行（250 个 distinct svcloanid）；`deal`/`program`/`lmc_status`/`final_disposition` 填充约 87%；脚本 `scripts/extract_table_stats.py` |

> ⚠️ 本表存储**解码后业务文本**（与 Hold 表直接存文本不同；编码解码在 Redshift 层完成）。实测部分值仍为未解码数字（如 `deal='2.0'`、`lmc_status='166.0'`），属 ETL 字典缺失项，应以表19 解码参考为准。

#### 字段说明（22列）

| 字段名 | 字段业务含义 | 来源数据 | 计算/推导逻辑 | 数据类型 | 取值范围 | 典型取值 | 上游字段 | 下游用途 | 备注 |
|--------|-----------|--------|-----------|----------|---------|---------|--------|--------|------|
| `id` | 自增主键 | BPS ETL | AUTO_INCREMENT | bigint NOT NULL | 25061 ~ 26155 | 25061 | — | 技术主键 | ✅；填充 544/544=100% |
| `loanid` | 系统贷款 ID | BPS ETL | 直接写入 | bigint | 7727000010 ~ 700082890000291 | 7727000010 | `newrez.portnewrezlm.loanid` | 贷款 join key | ✅；填充 544/544=100% |
| `svcloanid` | Servicer 内部贷款号 | BPS ETL | 直接写入 | varchar(64) | 文本，250种（样例 0578252925 … 7000359729） | 0578252925 | — | Servicer 对账 | ✅；填充 544/544=100% |
| `fctrdt` | 数据来源批次日期 | BPS ETL | 直接写入 | date | 2023-11-15 ~ 2026-03-13 | 2023-11-15 | — | 快照批次追踪 | ✅；填充 544/544=100% |
| `deal` | LM 大类（解码文本） | BPS ETL | lmdeal(int) 经 portnewrezdatadic 解码 | varchar(256) | {Modification, Evaluation, Forbearance, Deferment, Payment Plan, 2.0, DIL, Short Sale, 4.0, 1.0, Payoff} | Modification | `newrez.portnewrezlm.lmdeal` | LM Cycle 面板 Deal 列 | ✅ 解码存储（如 7→DIL）；填充 475/544=87% |
| `program` | LM 具体方案（解码文本） | BPS ETL | lmprogram(int) 解码 | varchar(256) | {Evaluation, Deferment, 496.0, Short-term Forbearance, Bridger mod, Repayment Plan, VA Traditional, SLS Standard Mod, FHA Recovery SAPC, 498.0, 21.0, Deed-in-Lieu, Standard Proprietary Modification, Short Sale, VASP No Trial, Unemployment Forbearance} 等30种 | Evaluation | `newrez.portnewrezlm.lmprogram` | LM Cycle 面板 Program 列 | ✅ 解码存储（如 10→Deed-in-Lieu）；填充 475/544=87% |
| `lmc_status` | LM 当前状态（解码文本） | BPS ETL | lmstatus(int) 解码 | varchar(256) | {Workout Denial, Pending Financials , Document Follow-up, Monitor Forbearance, Book mod, Deferment Agreement Ordered, 166.0, Deferment Plan In Progress, Monitor for pmts/funds, Liquidation Referral, Follow up for 1st Trial Payment, Solicitation Offered, 5.0, Monitor for Mod Agreement, Follow up for 2nd Trial Payment, 112.0} 等26种 | Workout Denial | `newrez.portnewrezlm.lmstatus` | LM Cycle 面板 Status 列 | ✅ 解码（如 166→Pending Financials）；填充 475/544=87% |
| `cycle_opened_date` | LM 周期开始日 | BPS ETL | 直接映射 dealstartdate | date | 2020-08-17 ~ 2026-03-12 | 2020-08-17 | `newrez.portnewrezlm.dealstartdate` | LM 周期唯一键之一 | ✅；填充 543/544=100% |
| `cycle_closed_date` | LM 周期结束日（NULL=进行中） | BPS ETL | 直接映射 lmremovaldate | date | 2020-09-22 ~ 2026-03-12 | 2020-09-22 | `newrez.portnewrezlm.lmremovaldate` | 周期历时计算 | ✅；填充 489/544=90% |
| `final_disposition` | 最终处置结论（解码文本） | BPS ETL | lmdecision(int) 解码 | varchar(256) | {Referral to FC, Request Incomplete/Failed to Provide Information, Pending, LMS Opened in Error, Reinstated/Current, Deferment Completed, Forbearance Complete, Modification Complete, Not Eligible for Loss Mitigation, Full Pay Off, 10.0, 11.0, 99.0, FC Sale Held, 5.0, 6.0} 等18种 | Referral to FC | `newrez.portnewrezlm.lmdecision` | 决定 FCL 是否恢复（如 Referral to FC） | ✅ 解码存储；填充 475/544=87% |
| `denialreason` | 拒绝原因（解码文本，无则空串） | BPS ETL | denialreason(int) 解码 | varchar(256) | {, Loan not due for 3 or more monthly payments, Request Incomplete/Failed to Provide Documentation, HAMP Sunset, Withdrawal of Request/Non-Acceptance, Unable to achieve target payment, Hardship not resolved, Investor Not Participating, Failed Plan, Loan not 90+ DPD , Post-Mod P&I Payment > Current P&I Payment, Trial Plan Default, HDTI out of range, Request Withdrawn, Default Not Imminent, Ineligible Borrower: Not a Natural Person} 等28种 |  | `newrez.portnewrezlm.denialreason` | LM 拒绝原因 | ✅ 无拒绝=空字符串；填充 475/544=87% |
| `borrower_intentions` | 借款人意向（解码文本） | BPS ETL | borrowerintention(int) 解码 | varchar(256) | {, Retention, Disposition, Unknown} |  | `newrez.portnewrezlm.borrowerintention` | 借款人意向 | ✅ Newrez 多为空；填充 475/544=87% |
| `imminent_default` | 即将违约标识（CFPB Reg X） | BPS ETL | Newrez 无对应字段 | varchar(256) | 实测全为 NULL | — | — | LM Cycle 面板列 | ✅ Newrez 恒 NULL（doc 13 Q6）；填充 0/544=0% |
| `single_point_of_contact` | 专属联系人（CFPB 12 CFR 1024.40） | BPS ETL | Newrez 无对应字段 | varchar(256) | 实测全为 NULL | — | — | LM Cycle 面板列 | ✅ Newrez 恒 NULL（doc 13 Q6）；填充 0/544=0% |
| `create_user` | 记录创建用户 | BPS 应用层 | 直接写入 | bigint | 实测全为 NULL | — | — | 审计追踪 | dev 未回填；填充 0/544=0% |
| `create_dept` | 记录创建部门 | BPS 应用层 | 直接写入 | bigint | 实测全为 NULL | — | — | 审计追踪 | dev 未回填；填充 0/544=0% |
| `create_time` | 记录创建时间 | BPS 应用层 | 直接写入 | datetime | 实测全为 NULL | — | — | 审计追踪 | dev 未回填；填充 0/544=0% |
| `update_user` | 最后更新用户 | BPS 应用层 | 直接写入 | bigint | 实测全为 NULL | — | — | 审计追踪 | dev 未回填；填充 0/544=0% |
| `update_time` | 最后更新时间 | BPS 应用层 | 直接写入 | datetime | 实测全为 NULL | — | — | 审计追踪 | dev 未回填；填充 0/544=0% |
| `status` | 记录状态（0=正常） | BPS 应用层 | DEFAULT 0 | int NOT NULL | {0}（1种） | 0 | — | 软停用标志 | ✅；填充 544/544=100% |
| `is_deleted` | 是否软删除（0=未删） | BPS 应用层 | DEFAULT 0 | int NOT NULL | {0}（1种） | 0 | — | 软删除标志 | ✅；填充 544/544=100% |
| `tenant_id` | 租户 ID | BPS 应用层 | 直接写入 | varchar(12) NOT NULL | {000000, 984018} | 000000 | — | 多租户支持 | ✅；填充 544/544=100% |

---

### 表 23：`bpms_dev.sync_loan_foreclosure_bankruptcy` — BPS Bankruptcy 记录表

| 属性 | 值 |
|------|----|
| **表名** | `sync_loan_foreclosure_bankruptcy` |
| **所属 Schema** | MySQL `bpms_dev` |
| **数据层** | Layer 5 — BPS Application Layer |
| **业务作用** | 贷款破产申请记录，驱动 BPS Bankruptcy 面板（仅有破产记录的贷款才有行） |
| **业务意图** | 向资产经理展示破产章节/状态/MFR/POC 等关键节点；破产保护期间 FCL 暂停 |
| **上游来源** | Redshift（源 `newrez.portnewrezbk`，`WHERE LENGTH(TRIM(bkstatus))>0`，按 `loanid,bkfileddate` 去重；`LEFT JOIN portnewrezgeneral` 取 legalstatus、`portnewrezdatadic` 解码 bkstatus）→ `JOIN port.portfunding`；合并 Newrez+Carrington+Capecodfive（见 doc 13 §6） |
| **下游使用** | BPS Bankruptcy 面板（Status/Legal Status/Chapter/MFR/POC 等 10 列） |
| **Foreclosure 关系** | 直接：上游 `activebkflag`/`bkremovaldate` 还驱动主表 `variance_active_bankruptcy`/`variance_completed_bankruptcy`（表17） |
| **主键 / 索引** | `id` 自增主键；业务键 `loanid + bkfileddate` |
| **代码血缘（PrefectFlow）** | 编排 `flow/bps/sync_asset_management.py`（`9-FORECLOSURE_BK`）→ `flow/bps/bps_config/asset_managment_config.py` `GEN_FORECLOSURE_BK`(L822，原样透传 a.* JOIN portfunding L838) → `util/df_db_util.py` `sync_to_mysql`(DELETE+INSERT)。Redshift 基表 `flow/basic_data/basic_data_config/basic_data_pool_config.py` `CREATE_BASIC_DATA_FCL_BANKRUPTCY`(L308-462)：**三个 servicer 分支** — Newrez(L349-370) `portnewrezbk JOIN portnewrezgeneral`、`portnewrezdatadic` 解码 BKStatus(L367)、按 `loanid,bkfileddate` 去重；Carrington(L391-416) 源 `portcarrington`；Capecodfive(L438-462) 源 `portcapecodfive_monthly_collections`。原始落地见表20 |
| **DB验证** | 2026-06-01 实测：22列；64 行（59 个 distinct svcloanid）；`bankruptcy_status`/`chapter` 100% 填充，`legal_status` 48%；脚本 `scripts/extract_table_stats.py` |

> ⚠️ `bankruptcy_status`/`legal_status` 实测多为已解码文本（Active/Discharged/Dismissed、BK13/BK7/REO 等），但仍混有少量未解码数字（如 `3.0`），属字典缺失项（doc 13 Q7 **已解决 2026-06-02**：`bankruptcy_status` = `bkstatus` int 1~5 解码，1→Active | 2→Discharged | 3→Dismissed | 4→Closed | 5→ReliefGranted；doc 14 v19 同步更正）。
> ⚠️ **字段来源按代码订正（推翻 doc 13 §6 的二手映射）**：`legal_status` 来自 `portnewrezgeneral.legalstatus`（**非** `bkstage`）；`status_date` 来自 `bkfileddate`（**非** `bkrcurrentstatusdate`）；`lien_status`/`mfr_status`/`claim_status` 在 **Newrez 分支硬编码 NULL**（非"待确认"）；`mfr_filed_date` 仅 **Carrington 分支**由 `bk_mfr_filed_date` 填充（Newrez/CC5 分支为 NULL），故 dev 仅 3/64 非空。详见下方字段表「上游字段」列与「代码血缘」行。

#### 字段说明（22列）

| 字段名 | 字段业务含义 | 来源数据 | 计算/推导逻辑 | 数据类型 | 取值范围 | 典型取值 | 上游字段 | 下游用途 | 备注 |
|--------|-----------|--------|-----------|----------|---------|---------|--------|--------|------|
| `id` | 自增主键 | BPS ETL | AUTO_INCREMENT | bigint NOT NULL | 2611 ~ 2739 | 2611 | — | 技术主键 | ✅；填充 64/64=100% |
| `loanid` | 系统贷款 ID | BPS ETL | 直接写入 | bigint | 7727000010 ~ 700082700000050 | 7727000010 | `newrez.portnewrezbk.loanid` | 贷款 join key | ✅；填充 64/64=100% |
| `svcloanid` | Servicer 内部贷款号 | BPS ETL | 直接写入 | varchar(64) | 文本，59种（样例 0578707313 … 7000357268） | 0578707313 | — | Servicer 对账 | ✅；填充 64/64=100% |
| `fctrdt` | 数据来源批次日期 | BPS ETL | 直接写入 | date | {2026-03-10, 2026-03-13, 2026-01-17, 2024-07-24, 2024-09-29, 2025-07-14, 2024-09-05, 2024-11-18, 2026-03-01} | 2026-03-10 | — | 快照批次追踪 | ✅；填充 64/64=100% |
| `bankruptcy_status` | 破产状态（解码文本） | BPS ETL | Newrez: `COALESCE(decode(bkstatus), bkstatus)`（portnewrezdatadic BKStatus，L354/367）；Carrington: `bk_flag`；CC5: `bankruptcy_flag` | varchar(256) | {Completed/Cancelled, Discharged, Active, Dismissed, 3.0, ReliefGranted, Closed} | Completed/Cancelled | Newrez `portnewrezbk.bkstatus`（解码） | BK 面板 Status 列 | ✅ 解码存储；未命中字典则回落原码（如 `3.0`）；填充 64/64=100% |
| `legal_status` | 法律程序状态 | BPS ETL | Newrez: 直接取 `legalstatus`；Carrington/CC5: NULL | varchar(256) | {BK13, , FCBU, BK11, BK11DCH, BK7, BK7DCH, REO, BKD13LM, BKD7LM, BK13DCH, FCSold} | BK13 | **`newrez.portnewrezgeneral.legalstatus`**（**非** bkstage）（L355,365-366） | BK 面板 Legal Status 列 | ✅ 已按代码订正；仅 Newrez 分支非空；填充 31/64=48% |
| `status_date` | 破产申请日（作状态日期用） | BPS ETL | Newrez/Carrington: 破产申请日；CC5: 最近破产申请日 | date | 2003-11-14 ~ 2026-02-26 | 2003-11-14 | **`bkfileddate`**（Newrez，**非** bkrcurrentstatusdate，L356）/ `bk_filed_date`（Carrington）/ `most_recent_bankruptcy_filing_date`（CC5） | BK 面板 Status Date | ✅ 已按代码订正；填充 62/64=97% |
| `chapter` | 破产章节（7/11/13） | BPS ETL | `CAST(bkchapter AS DECIMAL)`（Newrez/Carrington）；CC5 取 `bankruptcy_type` | varchar(256) | {13, 7, 11} | 13 | `newrez.portnewrezbk.bkchapter`(L357) | BK 面板 Chapter | ✅；填充 64/64=100% |
| `lien_status` | 留置权状态 | BPS ETL | 三个 servicer 分支均硬编码 `NULL`（L358/401/449） | varchar(256) | 实测全为 NULL | — | — （未映射） | BK 面板 Lien Status | ✅ 代码确认恒 NULL（非"待确认"）；填充 0/64=0% |
| `mfr_status` | MFR 状态 | BPS ETL | 三个 servicer 分支均硬编码 `NULL`（L359/402/450） | varchar(256) | 实测全为 NULL | — | — （未映射） | BK 面板 MFR Status | ✅ 代码确认恒 NULL（**非** mfrhearingresults）；填充 0/64=0% |
| `mfr_filed_date` | MFR 提交日 | BPS ETL | Newrez/CC5: NULL（L360/451）；Carrington: `bk_mfr_filed_date`（L403） | date | {2022-03-18, 2020-10-19, 2026-03-04} | 2022-03-18 | **`carrington.portcarrington.bk_mfr_filed_date`**（仅 Carrington 分支；Newrez `portnewrezbk.mfrfileddate` **未** 映射） | BK 面板 MFR Filed Date | ✅ 已按代码订正；dev 非空均来自 Carrington；填充 3/64=5% |
| `claim_status` | 债权状态 | BPS ETL | 三个 servicer 分支均硬编码 `NULL`（L361/404/452） | varchar(256) | 实测全为 NULL | — | — （未映射） | BK 面板 Claim Status | ✅ 代码确认恒 NULL（非"待确认"）；填充 0/64=0% |
| `proof_of_claim_date` | 债权申报（POC）日 | BPS ETL | Newrez: `pocfileddate`(L362)；Carrington: `bk_poc_filed_date`(L405)；CC5: NULL | date | {2023-09-30, 2010-06-17, 2001-01-01, 2025-08-05, 2024-03-29, 2025-12-16, 2022-10-17, 2017-03-31, 2024-04-19, 2026-01-26, 2018-04-12, 2016-04-26, 2013-06-13, 2020-02-13, 2024-12-17, 2016-02-15} 等22种 | 2023-09-30 | `newrez.portnewrezbk.pocfileddate` / `carrington.portcarrington.bk_poc_filed_date` | BK 面板 Proof of Claim Date | ✅；填充 24/64=38% |
| `post_petition_due_date` | 破产申请后应付日 | BPS ETL | Newrez: `bkpostpetitionduedate`(L363)；Carrington/CC5: NULL | date | {2026-01-01, 2026-02-01, 2025-06-01, 2026-04-01, 2026-03-06, 2024-02-01, 2026-03-01, 2021-04-01, 2025-11-01, 2025-02-01, 2022-04-01, 2018-09-01, 2025-09-01, 2025-10-01, 2025-05-01, 2022-09-01} 等20种 | 2026-01-01 | `newrez.portnewrezbk.bkpostpetitionduedate`（仅 Newrez 分支） | BK 面板 Post Petition Due Date | ✅；填充 22/64=34% |
| `create_user` | 记录创建用户 | BPS 应用层 | 直接写入 | bigint | 实测全为 NULL | — | — | 审计追踪 | dev 未回填；填充 0/64=0% |
| `create_dept` | 记录创建部门 | BPS 应用层 | 直接写入 | bigint | 实测全为 NULL | — | — | 审计追踪 | dev 未回填；填充 0/64=0% |
| `create_time` | 记录创建时间 | BPS 应用层 | 直接写入 | datetime | 实测全为 NULL | — | — | 审计追踪 | dev 未回填；填充 0/64=0% |
| `update_user` | 最后更新用户 | BPS 应用层 | 直接写入 | bigint | 实测全为 NULL | — | — | 审计追踪 | dev 未回填；填充 0/64=0% |
| `update_time` | 最后更新时间 | BPS 应用层 | 直接写入 | datetime | 实测全为 NULL | — | — | 审计追踪 | dev 未回填；填充 0/64=0% |
| `status` | 记录状态（0=正常） | BPS 应用层 | DEFAULT 0 | int NOT NULL | {0}（1种） | 0 | — | 软停用标志 | ✅；填充 64/64=100% |
| `is_deleted` | 是否软删除（0=未删） | BPS 应用层 | DEFAULT 0 | int NOT NULL | {0}（1种） | 0 | — | 软删除标志 | ✅；填充 64/64=100% |
| `tenant_id` | 租户 ID | BPS 应用层 | 直接写入 | varchar(12) NOT NULL | {000000, 984018} | 000000 | — | 多租户支持 | ✅；填充 64/64=100% |

---

### 表 24：`bpms_dev.sync_fcl_stage_info` — BPS FCL 阶段统计表

| 属性 | 值 |
|------|----|
| **表名** | `sync_fcl_stage_info` |
| **所属 Schema** | MySQL `bpms_dev` |
| **数据层** | Layer 5 — BPS Application Layer（聚合概览页数据源） |
| **业务作用** | 驱动 BPS Foreclosure 聚合概览页（Stage Tab + Time Line Tab）：按当前阶段分组的 Days in Stage / Days in LM / Days on Hold 统计，及各里程碑日期时间线 |
| **业务意图** | 为资产经理提供组合级 FCL 进度与停滞监控；含主表 `sync_loan_foreclosure` 所缺的实际历时天数（`*_stage_days` 等） |
| **上游来源** | Redshift `port.fcl_stage_info`（`GEN_FCL_STAGE`：主筛选 `activefcflag=1 AND fcremovaldate IS NULL`；次筛选 Demand 且 D90/D120P）→ `JOIN port.portfunding`（见 doc 13 §7） |
| **下游使用** | BPS 聚合概览页 Stage Tab（阶段天数）与 Time Line Tab（里程碑日期）；`stage` 代码经前端映射为显示名 |
| **Foreclosure 关系** | 核心：**唯一排除完结贷款**的 FCL 表（仅活跃 FCL），与主表 `sync_loan_foreclosure`（含完结）人口不同，数量不应直接比较 |
| **主键 / 索引** | `id` 自增主键；业务键 `loanid + fctrdt`（每日快照） |
| **代码血缘（PrefectFlow）** | 编排 `flow/bps/sync_asset_management.py`（`12-FCL_STAGE`）→ `flow/bps/bps_config/asset_managment_config.py` `GET_FCL_STAGE_DATA`(L925，`select a.* ... JOIN port.portfunding` L928) → `util/df_db_util.py` `sync_to_mysql`(DELETE+INSERT)。Redshift 基表 `port.fcl_stage_info`：`flow/basic_data/basic_data_config/basic_data_pool_config.py` `GEN_FCL_STAGE`(L1774-2438，INSERT L2344；源 `port.basic_data_loan_fcl` + `port.basic_data_fcl_related` + hold_detail) |
| **DB验证** | 2026-06-01 实测：57列；5,825 行（56 个 distinct loanid × 多快照日）；`stage` 6 种代码；脚本 `scripts/extract_table_stats.py` |

> 阶段字段按前缀分组（`demand_`/`noi_`/`referral_`/`first_legal_`/`service_`/`publication_`/`judgement_`/`sale_`），各组含 `*_start_date`/`*_end_date`/`*_stage_days`/`*_in_lm_days`/`*_on_hold_days`；Upcoming 组用 `to_judgement_days`/`to_sale_days` 替代 stage_days。`noi_*`/`publication_*` 对 Newrez 恒 NULL（见 doc 13 §7）。

#### 字段说明（57列）

| 字段名 | 字段业务含义 | 来源数据 | 计算/推导逻辑 | 数据类型 | 取值范围 | 典型取值 | 上游字段 | 下游用途 | 备注 |
|--------|-----------|--------|-----------|----------|---------|---------|--------|--------|------|
| `id` | 自增主键 | BPS ETL（GEN_FCL_STAGE） | 直接写入 | bigint NOT NULL | 299808 ~ 305632 | 299808 | — | 技术主键 | ✅；填充 5825/5825=100% |
| `stage` | 当前 FCL 阶段代码（全大写） | BPS ETL（GEN_FCL_STAGE） | ETL 计算/派生 | varchar(100) | {REFERRAL, SALE, SERVICE, FIRST_LEGAL, JUDGEMENT, DEMAND} | REFERRAL | — | BPS 聚合页分组键；瀑布优先级判定 | ✅ {SALE,JUDGEMENT,SERVICE,FIRST_LEGAL,REFERRAL,DEMAND}；填充 5825/5825=100% |
| `fctrdt` | 数据快照日（每贷款每天一行） | BPS ETL（GEN_FCL_STAGE） | 直接写入 | date | 2025-06-04 ~ 2026-03-13 | 2025-06-04 | — | 查询当前态需 `fctrdt=MAX(fctrdt)` | ✅；填充 5825/5825=100% |
| `loanid` | 系统贷款 ID | BPS ETL（GEN_FCL_STAGE） | 直接写入 | varchar(100) | 文本，56种（样例 7727000065 … 7727005351） | 7727000065 | — | 贷款 join key | ✅；填充 5825/5825=100% |
| `group` | 派生分类（FCL/REO/D120P/D90） | BPS ETL（GEN_FCL_STAGE） | ETL 计算/派生 | varchar(100) | {FCL, D120P, D90, REO} | FCL | — | 聚合页分组/过滤 | ✅ ETL 写入派生字段；填充 5825/5825=100% |
| `servicer` | Servicer 名称 | BPS ETL（GEN_FCL_STAGE） | 直接写入 | varchar(100) | {Newrez, Carrington} | Newrez | — | 聚合页过滤 | ✅；填充 5825/5825=100% |
| `state` | 物业所在州 | BPS ETL（GEN_FCL_STAGE） | 直接写入 | varchar(100) | {FL, IL, NY, CA, AZ, IN, CO, PA, TX, WA, OR, NC, MT, MD, MA, RI} 等22种 | FL | `newrez.portnewrezfc.*`（经 `port.basic_data_loan_fcl`） | 聚合页过滤 | ✅；填充 5825/5825=100% |
| `judicial` | 是否司法州（Y/N） | BPS ETL（GEN_FCL_STAGE） | 直接写入 | varchar(1) | {Y, N} | Y | `newrez.portnewrezfc.*`（经 `port.basic_data_loan_fcl`） | 司法/非司法流程区分 | ✅；填充 5825/5825=100% |
| `demand_start_date` | NOI/Demand Letter 阶段 · 阶段开始日 | BPS ETL（GEN_FCL_STAGE） | 源 timeline 日期（经 basic_data_loan_fcl） | date | 2021-10-18 ~ 2026-02-04 | 2021-10-18 | `newrez.portnewrezfc` timeline | 聚合页 NOI/Demand Letter 组 | ✅；填充 4858/5825=83% |
| `demand_end_date` | NOI/Demand Letter 阶段 · 阶段结束日 | BPS ETL（GEN_FCL_STAGE） | 源 timeline 日期（经 basic_data_loan_fcl） | date | 2021-11-22 ~ 2026-03-11 | 2021-11-22 | `newrez.portnewrezfc` timeline | 聚合页 NOI/Demand Letter 组 | ✅；填充 4858/5825=83% |
| `demand_stage_days` | NOI/Demand Letter 阶段 · 在该阶段已历天数 | BPS ETL（GEN_FCL_STAGE） | BPS 结合 LM/Hold 状态计算 | int | 3 ~ 1452 | 3 | `portnewrezlm.activelmflag` / Hold 状态 | 聚合页 NOI/Demand Letter 组 | ✅；填充 4858/5825=83% |
| `demand_in_lm_days` | NOI/Demand Letter 阶段 · 该阶段内处于 LM 的天数 | BPS ETL（GEN_FCL_STAGE） | BPS 结合 LM/Hold 状态计算 | int | 3 ~ 283 | 3 | `portnewrezlm.activelmflag` / Hold 状态 | 聚合页 NOI/Demand Letter 组 | ✅；填充 2573/5825=44% |
| `demand_on_hold_days` | NOI/Demand Letter 阶段 · 该阶段内处于 Hold 的天数 | BPS ETL（GEN_FCL_STAGE） | BPS 结合 LM/Hold 状态计算 | int | 1 ~ 250 | 1 | `portnewrezlm.activelmflag` / Hold 状态 | 聚合页 NOI/Demand Letter 组 | ✅；填充 2672/5825=46% |
| `noi_start_date` | NOI(Approved for Referral) 阶段 · 阶段开始日 | BPS ETL（GEN_FCL_STAGE） | 源 timeline 日期（经 basic_data_loan_fcl） | date | 实测全为 NULL | — | `newrez.portnewrezfc` timeline | 聚合页 NOI(Approved for Referral) 组 | ✅；填充 0/5825=0% |
| `noi_end_date` | NOI(Approved for Referral) 阶段 · 阶段结束日 | BPS ETL（GEN_FCL_STAGE） | 源 timeline 日期（经 basic_data_loan_fcl） | date | 实测全为 NULL | — | `newrez.portnewrezfc` timeline | 聚合页 NOI(Approved for Referral) 组 | ✅；填充 0/5825=0% |
| `noi_stage_days` | NOI(Approved for Referral) 阶段 · 在该阶段已历天数 | BPS ETL（GEN_FCL_STAGE） | BPS 结合 LM/Hold 状态计算 | int | 实测全为 NULL | — | `portnewrezlm.activelmflag` / Hold 状态 | 聚合页 NOI(Approved for Referral) 组 | ✅；填充 0/5825=0% |
| `noi_in_lm_days` | NOI(Approved for Referral) 阶段 · 该阶段内处于 LM 的天数 | BPS ETL（GEN_FCL_STAGE） | BPS 结合 LM/Hold 状态计算 | int | 实测全为 NULL | — | `portnewrezlm.activelmflag` / Hold 状态 | 聚合页 NOI(Approved for Referral) 组 | ✅；填充 0/5825=0% |
| `noi_on_hold_days` | NOI(Approved for Referral) 阶段 · 该阶段内处于 Hold 的天数 | BPS ETL（GEN_FCL_STAGE） | BPS 结合 LM/Hold 状态计算 | int | 实测全为 NULL | — | `portnewrezlm.activelmflag` / Hold 状态 | 聚合页 NOI(Approved for Referral) 组 | ✅；填充 0/5825=0% |
| `referral_start_date` | Referral 阶段 · 阶段开始日 | BPS ETL（GEN_FCL_STAGE） | 源 timeline 日期（经 basic_data_loan_fcl） | date | 2024-01-11 ~ 2026-03-10 | 2024-01-11 | `newrez.portnewrezfc` timeline | 聚合页 Referral 组 | ✅；填充 5501/5825=94% |
| `referral_end_date` | Referral 阶段 · 阶段结束日 | BPS ETL（GEN_FCL_STAGE） | 源 timeline 日期（经 basic_data_loan_fcl） | date | {2025-02-12, 2025-04-03, 2025-04-15, 2025-05-19, 2025-01-16, 2025-06-13, 2025-06-11, 2025-07-23, 2025-07-21, 2025-07-28, 2025-08-13, 2025-08-07, 2024-10-29, 2025-03-31, 2025-10-14, 2025-03-27} 等30种 | 2025-02-12 | `newrez.portnewrezfc` timeline | 聚合页 Referral 组 | ✅；填充 3436/5825=59% |
| `referral_stage_days` | Referral 阶段 · 在该阶段已历天数 | BPS ETL（GEN_FCL_STAGE） | BPS 结合 LM/Hold 状态计算 | int | 3 ~ 762 | 3 | `portnewrezlm.activelmflag` / Hold 状态 | 聚合页 Referral 组 | ✅；填充 5501/5825=94% |
| `referral_in_lm_days` | Referral 阶段 · 该阶段内处于 LM 的天数 | BPS ETL（GEN_FCL_STAGE） | BPS 结合 LM/Hold 状态计算 | int | 3 ~ 132 | 3 | `portnewrezlm.activelmflag` / Hold 状态 | 聚合页 Referral 组 | ✅；填充 816/5825=14% |
| `referral_on_hold_days` | Referral 阶段 · 该阶段内处于 Hold 的天数 | BPS ETL（GEN_FCL_STAGE） | BPS 结合 LM/Hold 状态计算 | int | 2 ~ 227 | 2 | `portnewrezlm.activelmflag` / Hold 状态 | 聚合页 Referral 组 | ✅；填充 1300/5825=22% |
| `first_legal_start_date` | First Legal 阶段 · 阶段开始日 | BPS ETL（GEN_FCL_STAGE） | 源 timeline 日期（经 basic_data_loan_fcl） | date | {2025-02-12, 2025-04-03, 2025-04-15, 2025-05-19, 2025-01-16, 2025-06-13, 2025-06-11, 2025-07-23, 2025-07-21, 2025-07-28, 2025-08-13, 2025-08-07, 2024-10-29, 2025-03-31, 2025-10-14, 2025-03-27} 等30种 | 2025-02-12 | `newrez.portnewrezfc` timeline | 聚合页 First Legal 组 | ✅；填充 3436/5825=59% |
| `first_legal_end_date` | First Legal 阶段 · 阶段结束日 | BPS ETL（GEN_FCL_STAGE） | 源 timeline 日期（经 basic_data_loan_fcl） | date | {2025-03-04, 2025-04-24, 2025-06-02, 2025-07-18, 2025-08-14, 2025-08-25, 2025-05-28, 2025-09-02, 2025-05-23, 2025-12-08, 2025-05-03, 2025-12-24, 2025-09-21, 2026-01-13, 2025-12-29, 2025-07-27} 等17种 | 2025-03-04 | `newrez.portnewrezfc` timeline | 聚合页 First Legal 组 | ✅；填充 1993/5825=34% |
| `first_legal_stage_days` | First Legal 阶段 · 在该阶段已历天数 | BPS ETL（GEN_FCL_STAGE） | BPS 结合 LM/Hold 状态计算 | int | 3 ~ 424 | 3 | `portnewrezlm.activelmflag` / Hold 状态 | 聚合页 First Legal 组 | ✅；填充 3436/5825=59% |
| `first_legal_in_lm_days` | First Legal 阶段 · 该阶段内处于 LM 的天数 | BPS ETL（GEN_FCL_STAGE） | BPS 结合 LM/Hold 状态计算 | int | 1 ~ 283 | 1 | `portnewrezlm.activelmflag` / Hold 状态 | 聚合页 First Legal 组 | ✅；填充 828/5825=14% |
| `first_legal_on_hold_days` | First Legal 阶段 · 该阶段内处于 Hold 的天数 | BPS ETL（GEN_FCL_STAGE） | BPS 结合 LM/Hold 状态计算 | int | 3 ~ 250 | 3 | `portnewrezlm.activelmflag` / Hold 状态 | 聚合页 First Legal 组 | ✅；填充 853/5825=15% |
| `first_legal_date_history` | 首次法律行动日变更历史 | BPS ETL（GEN_FCL_STAGE） | ETL 计算/派生 | text | 实测全为 NULL | — | — | First Legal 改期追溯 | 🟡 dev 全 NULL；填充 0/5825=0% |
| `service_start_date` | Service 阶段 · 阶段开始日 | BPS ETL（GEN_FCL_STAGE） | 源 timeline 日期（经 basic_data_loan_fcl） | date | {2025-03-04, 2025-04-24, 2025-06-02, 2025-07-18, 2025-08-14, 2025-08-25, 2025-05-28, 2025-09-02, 2025-05-23, 2025-12-08, 2025-05-03, 2025-12-24, 2025-09-21, 2026-01-13, 2025-12-29, 2025-07-27} 等17种 | 2025-03-04 | `newrez.portnewrezfc` timeline | 聚合页 Service 组 | ✅；填充 1993/5825=34% |
| `service_end_date` | Service 阶段 · 阶段结束日 | BPS ETL（GEN_FCL_STAGE） | 源 timeline 日期（经 basic_data_loan_fcl） | date | {2025-11-17, 2025-07-03, 2025-12-17, 2025-10-27, 2025-06-11, 2025-10-29, 2026-01-26, 2025-08-08, 2025-12-08, 2025-07-15, 2025-07-14, 2025-07-21, 2025-08-06, 2026-02-13, 2025-11-04, 2025-09-12} 等22种 | 2025-11-17 | `newrez.portnewrezfc` timeline | 聚合页 Service 组 | ✅；填充 839/5825=14% |
| `service_stage_days` | Service 阶段 · 在该阶段已历天数 | BPS ETL（GEN_FCL_STAGE） | BPS 结合 LM/Hold 状态计算 | int | 4 ~ 377 | 4 | `portnewrezlm.activelmflag` / Hold 状态 | 聚合页 Service 组 | ✅；填充 1993/5825=34% |
| `service_in_lm_days` | Service 阶段 · 该阶段内处于 LM 的天数 | BPS ETL（GEN_FCL_STAGE） | BPS 结合 LM/Hold 状态计算 | int | 3 ~ 102 | 3 | `portnewrezlm.activelmflag` / Hold 状态 | 聚合页 Service 组 | ✅；填充 832/5825=14% |
| `service_on_hold_days` | Service 阶段 · 该阶段内处于 Hold 的天数 | BPS ETL（GEN_FCL_STAGE） | BPS 结合 LM/Hold 状态计算 | int | 1 ~ 145 | 1 | `portnewrezlm.activelmflag` / Hold 状态 | 聚合页 Service 组 | ✅；填充 834/5825=14% |
| `publication_start_date` | Publication 阶段 · 阶段开始日 | BPS ETL（GEN_FCL_STAGE） | 源 timeline 日期（经 basic_data_loan_fcl） | date | 实测全为 NULL | — | `newrez.portnewrezfc` timeline | 聚合页 Publication 组 | ✅；填充 0/5825=0% |
| `publication_end_date` | Publication 阶段 · 阶段结束日 | BPS ETL（GEN_FCL_STAGE） | 源 timeline 日期（经 basic_data_loan_fcl） | date | 实测全为 NULL | — | `newrez.portnewrezfc` timeline | 聚合页 Publication 组 | ✅；填充 0/5825=0% |
| `publication_stage_days` | Publication 阶段 · 在该阶段已历天数 | BPS ETL（GEN_FCL_STAGE） | BPS 结合 LM/Hold 状态计算 | int | 实测全为 NULL | — | `portnewrezlm.activelmflag` / Hold 状态 | 聚合页 Publication 组 | ✅；填充 0/5825=0% |
| `publication_in_lm_days` | Publication 阶段 · 该阶段内处于 LM 的天数 | BPS ETL（GEN_FCL_STAGE） | BPS 结合 LM/Hold 状态计算 | int | 实测全为 NULL | — | `portnewrezlm.activelmflag` / Hold 状态 | 聚合页 Publication 组 | ✅；填充 0/5825=0% |
| `publication_on_hold_days` | Publication 阶段 · 该阶段内处于 Hold 的天数 | BPS ETL（GEN_FCL_STAGE） | BPS 结合 LM/Hold 状态计算 | int | 实测全为 NULL | — | `portnewrezlm.activelmflag` / Hold 状态 | 聚合页 Publication 组 | ✅；填充 0/5825=0% |
| `judgement_start_date` | Upcoming Judgement 阶段 · 阶段开始日 | BPS ETL（GEN_FCL_STAGE） | 源 timeline 日期（经 basic_data_loan_fcl） | date | {2025-11-29, 2025-09-16, 2026-03-27, 2026-02-04, 2025-09-23, 2026-04-08, 2026-01-18, 2026-01-17, 2026-03-23, 2025-10-15, 2025-10-27, 2025-12-03, 2025-11-14, 2026-04-13, 2026-02-21, 2025-08-07} 等22种 | 2025-11-29 | `newrez.portnewrezfc` timeline | 聚合页 Upcoming Judgement 组 | ✅；填充 839/5825=14% |
| `judgement_end_date` | Upcoming Judgement 阶段 · 阶段结束日 | BPS ETL（GEN_FCL_STAGE） | 源 timeline 日期（经 basic_data_loan_fcl） | date | 实测全为 NULL | — | `newrez.portnewrezfc` timeline | 聚合页 Upcoming Judgement 组 | ✅；填充 0/5825=0% |
| `to_judgement_days` | 距判决日剩余天数 | BPS ETL（GEN_FCL_STAGE） | BPS 计算 | int | 0 ~ 151 | 0 | — | Upcoming Judgement 组 Days to Judgement | ✅；填充 839/5825=14% |
| `judgement_in_lm_days` | Upcoming Judgement 阶段 · 该阶段内处于 LM 的天数 | BPS ETL（GEN_FCL_STAGE） | BPS 结合 LM/Hold 状态计算 | int | 3 ~ 23（21种） | 9 | `portnewrezlm.activelmflag` / Hold 状态 | 聚合页 Upcoming Judgement 组 | ✅；填充 57/5825=1% |
| `judgement_on_hold_days` | Upcoming Judgement 阶段 · 该阶段内处于 Hold 的天数 | BPS ETL（GEN_FCL_STAGE） | BPS 结合 LM/Hold 状态计算 | int | 3 ~ 51 | 3 | `portnewrezlm.activelmflag` / Hold 状态 | 聚合页 Upcoming Judgement 组 | ✅；填充 274/5825=5% |
| `sale_start_date` | Upcoming FC Sales 阶段 · 阶段开始日 | BPS ETL（GEN_FCL_STAGE） | 源 timeline 日期（经 basic_data_loan_fcl） | date | {2025-12-29, 2025-12-30, 2026-03-31, 2025-12-17, 2025-08-15, 2026-01-16, 2026-04-08, 2026-05-15, 2025-08-26, 2026-03-03, 2026-04-07, 2025-10-28, 2026-02-04, 2025-10-14, 2026-03-11, 2026-02-27} 等30种 | 2025-12-29 | `newrez.portnewrezfc` timeline | 聚合页 Upcoming FC Sales 组 | ✅；填充 1197/5825=21% |
| `sale_end_date` | Upcoming FC Sales 阶段 · 阶段结束日 | BPS ETL（GEN_FCL_STAGE） | 源 timeline 日期（经 basic_data_loan_fcl） | date | 实测全为 NULL | — | `newrez.portnewrezfc` timeline | 聚合页 Upcoming FC Sales 组 | ✅；填充 0/5825=0% |
| `to_sale_days` | 距拍卖日剩余天数 | BPS ETL（GEN_FCL_STAGE） | BPS 计算 | int | 0 ~ 129 | 0 | — | Upcoming FC Sales 组 Days to Sale | ✅；填充 1197/5825=21% |
| `sale_in_lm_days` | Upcoming FC Sales 阶段 · 该阶段内处于 LM 的天数 | BPS ETL（GEN_FCL_STAGE） | BPS 结合 LM/Hold 状态计算 | int | 3 ~ 88 | 3 | `portnewrezlm.activelmflag` / Hold 状态 | 聚合页 Upcoming FC Sales 组 | ✅；填充 213/5825=4% |
| `sale_on_hold_days` | Upcoming FC Sales 阶段 · 该阶段内处于 Hold 的天数 | BPS ETL（GEN_FCL_STAGE） | BPS 结合 LM/Hold 状态计算 | int | 3 ~ 109 | 3 | `portnewrezlm.activelmflag` / Hold 状态 | 聚合页 Upcoming FC Sales 组 | ✅；填充 216/5825=4% |
| `create_time` | 记录创建时间 | BPS ETL（GEN_FCL_STAGE） | ETL 计算/派生 | datetime | {2026-03-16 06:54:17} | 2026-03-16 06:54:17 | — | 管理字段 | ✅ 实测=同步批次时间；填充 5825/5825=100% |
| `update_time` | 记录更新时间 | BPS ETL（GEN_FCL_STAGE） | ETL 计算/派生 | datetime | {2026-03-16 06:54:17} | 2026-03-16 06:54:17 | — | 管理字段 | ✅；填充 5825/5825=100% |
| `create_user` | 记录创建用户 | BPS ETL（GEN_FCL_STAGE） | ETL 计算/派生 | bigint | 实测全为 NULL | — | — | 审计追踪 | dev 未回填；填充 0/5825=0% |
| `create_dept` | 记录创建部门 | BPS ETL（GEN_FCL_STAGE） | ETL 计算/派生 | bigint | 实测全为 NULL | — | — | 审计追踪 | dev 未回填；填充 0/5825=0% |
| `update_user` | 最后更新用户 | BPS ETL（GEN_FCL_STAGE） | ETL 计算/派生 | bigint | 实测全为 NULL | — | — | 审计追踪 | dev 未回填；填充 0/5825=0% |
| `status` | 记录状态（0=正常） | BPS ETL（GEN_FCL_STAGE） | ETL 计算/派生 | int NOT NULL | {0}（1种） | 0 | — | 软停用标志 | ✅；填充 5825/5825=100% |
| `is_deleted` | 是否软删除（0=未删） | BPS ETL（GEN_FCL_STAGE） | ETL 计算/派生 | int NOT NULL | {0}（1种） | 0 | — | 软删除标志 | ✅；填充 5825/5825=100% |
| `tenant_id` | 租户 ID | BPS ETL（GEN_FCL_STAGE） | ETL 计算/派生 | varchar(12) NOT NULL | {000000} | 000000 | — | 多租户支持 | ✅；填充 5825/5825=100% |

---

### 表 25：`bpms_dev.biz_data_view_loan_details_foreclosure` — BPS FCL 详情展示视图

| 属性 | 值 |
|------|----|
| **表名** | `biz_data_view_loan_details_foreclosure`（**VIEW，非物理表**） |
| **所属 Schema** | MySQL `bpms_dev` |
| **数据层** | Layer 5 — BPS Application Layer（展示视图，最终展示口径） |
| **业务作用** | BPS Loan Foreclosure 详情页最终数据视图：在主表 `sync_loan_foreclosure` 基础上，按 `nextduedate` 实时计算各阶段 `actual_*_days`、`var_*_days` 偏差及 total 汇总 |
| **业务意图** | 将「目标 vs 实际 vs 偏差」三类天数指标在查询层一次性算出，避免落库；resolved actual/var 字段（如 `actual_judgement_hearing_set_days`）仅存在于本视图 |
| **视图定义** | `sync_portmonth`(monthly) `LEFT JOIN sync_loan_foreclosure`(loan_fcl) ON `loanid+tenant_id`，再 LEFT JOIN 各 loanid 的 `MAX(fctrdt)` 子查询（取最新月度快照）。`actual_*_days = TO_DAYS(timeline_x) − TO_DAYS(nextduedate)`；`var_*_days = actual − 累计 target`（MCP `SHOW CREATE VIEW` 实测） |
| **下游使用** | BPS 详情页 Milestone Timeline / Target / Actual / Variance 面板（含 doc 14 SQL-C3 验证的 `actual_judgement_hearing_set_days`） |
| **Foreclosure 关系** | 核心展示层：FCL 时间线 + SLA 合规（actual vs target）一站式视图 |
| **主键 / 索引** | 视图无主键；按 `loanid + fctrdt` 唯一 |
| **代码血缘（PrefectFlow）** | **本视图不由 PrefectFlow 管理**：全库 grep 无 `biz_data_view_loan_details_foreclosure`、无 `CREATE VIEW`——视图定义在 bpms_dev 库内（`SHOW CREATE VIEW` 实测，见上「视图定义」行）。其基表均由 PrefectFlow 写入：`sync_loan_foreclosure`(表17，两步 upsert) 与 `sync_portmonth`(月度同步)。即 PrefectFlow 负责"喂数据"，视图聚合/计算逻辑在 DB 侧 |
| **DB验证** | 2026-06-01 实测：104列；122,550 行（基于 `sync_portmonth` 全量月度贷款，含非 FCL，故 timeline/summary 等填充率低）；脚本 `scripts/extract_table_stats.py` |

> 列结构（104）：标识与锚点 5 + `timeline_*` 19 + `target_*_days` 15 + `actual_*_days` 15 + `variance_*` 4 + `bid_approval_*` 4 + `summary_*` 16 + 管理字段 8 + `var_*_days` 15 + 汇总 3（`var_total`/`target_total`/`actual_total`）。`target_*` 在视图中为 `bigint`（基表为 `int`）。填充率低因视图人口为全部月度贷款（122,550 行），非仅活跃 FCL。

#### 字段说明（104列）

| 字段名 | 字段业务含义 | 来源数据 | 计算/推导逻辑 | 数据类型 | 取值范围 | 典型取值 | 上游字段 | 下游用途 | 备注 |
|--------|-----------|--------|-----------|----------|---------|---------|--------|--------|------|
| `id` | FCL 记录 ID（来自 loan_fcl） | 视图计算 | `loan_fcl.id` | bigint | 1 ~ 279 | 1 | 表17 `id` | 贷款 FCL 关联 | ✅；填充 2359/122550=2% |
| `loanid` | 系统贷款 ID | 视图计算 | `monthly.loanid` | bigint | 7727000002 ~ 700083320000172 | 7727000002 | `sync_portmonth.loanid` | 视图主键 | ✅；填充 122550/122550=100% |
| `svcloanid` | Servicer 内部贷款号 | 视图计算 | `monthly.svcloanid` | varchar(32) | 文本，9426种（样例 001324995 … HB0075942） | 001324995 | `sync_portmonth` | 对账 | ✅；填充 122550/122550=100% |
| `fctrdt` | 数据快照日（月度） | 视图计算 | `monthly.fctrdt` | date | 2023-02-01 ~ 2026-03-01 | 2023-02-01 | `sync_portmonth` | 时间维度 | ✅；填充 122550/122550=100% |
| `nextduedate` | 下次应还款日（DPD/历时计算锚点） | 视图计算 | `monthly.nextduedate` | date | 2021-09-01 ~ 2027-07-01 | 2021-09-01 | `sync_portmonth` | actual_*_days 计算基准 | ✅ 100%；填充 122037/122550=100% |
| `timeline_notice_of_intent_date` | FCL 里程碑日期（同表17 `timeline_notice_of_intent_date`） | 视图计算 | 取自 `loan_fcl.timeline_notice_of_intent_date` | date | {2025-04-22, 2024-05-17, 2024-10-18, 2025-02-22, 2025-01-22} | 2025-04-22 | 表17 `timeline_notice_of_intent_date` | Milestone Timeline 展示 | ✅；填充 145/122550=0% |
| `timeline_notice_of_intent_end_date` | FCL 里程碑日期（同表17 `timeline_notice_of_intent_end_date`） | 视图计算 | 取自 `loan_fcl.timeline_notice_of_intent_end_date` | date | 实测全为 NULL | — | 表17 `timeline_notice_of_intent_end_date` | Milestone Timeline 展示 | ✅；填充 0/122550=0% |
| `timeline_approved_for_referral_date` | FCL 里程碑日期（同表17 `timeline_approved_for_referral_date`） | 视图计算 | 取自 `loan_fcl.timeline_approved_for_referral_date` | date | 实测全为 NULL | — | 表17 `timeline_approved_for_referral_date` | Milestone Timeline 展示 | ✅；填充 0/122550=0% |
| `timeline_referred_to_attorney_date` | FCL 里程碑日期（同表17 `timeline_referred_to_attorney_date`） | 视图计算 | 取自 `loan_fcl.timeline_referred_to_attorney_date` | date | 实测全为 NULL | — | 表17 `timeline_referred_to_attorney_date` | Milestone Timeline 展示 | ✅；填充 0/122550=0% |
| `timeline_referred_to_foreclosure_date` | FCL 里程碑日期（同表17 `timeline_referred_to_foreclosure_date`） | 视图计算 | 取自 `loan_fcl.timeline_referred_to_foreclosure_date` | date | 2018-08-15 ~ 2026-03-10 | 2018-08-15 | 表17 `timeline_referred_to_foreclosure_date` | Milestone Timeline 展示 | ✅；填充 2359/122550=2% |
| `timeline_title_report_received_date` | FCL 里程碑日期（同表17 `timeline_title_report_received_date`） | 视图计算 | 取自 `loan_fcl.timeline_title_report_received_date` | date | {2025-12-02, 2025-03-24} | 2025-12-02 | 表17 `timeline_title_report_received_date` | Milestone Timeline 展示 | ✅；填充 96/122550=0% |
| `timeline_preliminary_title_cleared_date` | FCL 里程碑日期（同表17 `timeline_preliminary_title_cleared_date`） | 视图计算 | 取自 `loan_fcl.timeline_preliminary_title_cleared_date` | date | {2025-03-24, 2026-02-02} | 2025-03-24 | 表17 `timeline_preliminary_title_cleared_date` | Milestone Timeline 展示 | ✅；填充 59/122550=0% |
| `timeline_first_legal_date` | FCL 里程碑日期（同表17 `timeline_first_legal_date`） | 视图计算 | 取自 `loan_fcl.timeline_first_legal_date` | date | 2018-10-29 ~ 2026-02-25 | 2018-10-29 | 表17 `timeline_first_legal_date` | Milestone Timeline 展示 | ✅；填充 1127/122550=1% |
| `timeline_service_date` | FCL 里程碑日期（同表17 `timeline_service_date`） | 视图计算 | 取自 `loan_fcl.timeline_service_date` | date | {2025-06-02, 2025-09-02, 2025-05-03, 2026-01-13, 2025-07-18, 2025-08-14, 2024-04-01, 2025-11-19, 2025-03-04, 2025-05-23, 2024-11-26, 2025-12-08, 2025-04-24, 2018-12-10, 2025-05-28, 2025-12-29} 等19种 | 2025-06-02 | 表17 `timeline_service_date` | Milestone Timeline 展示 | ✅；填充 559/122550=0% |
| `timeline_publication_date` | FCL 里程碑日期（同表17 `timeline_publication_date`） | 视图计算 | 取自 `loan_fcl.timeline_publication_date` | date | 实测全为 NULL | — | 表17 `timeline_publication_date` | Milestone Timeline 展示 | ✅；填充 0/122550=0% |
| `timeline_judgement_hearing_set_date` | FCL 里程碑日期（同表17 `timeline_judgement_hearing_set_date`） | 视图计算 | 取自 `loan_fcl.timeline_judgement_hearing_set_date` | date | {2025-10-27, 2025-07-15, 2026-03-06, 2026-01-26, 2025-08-06, 2025-11-17, 2023-12-14, 2025-07-03, 2026-02-13} | 2025-10-27 | 表17 `timeline_judgement_hearing_set_date` | Milestone Timeline 展示 | ✅；填充 272/122550=0% |
| `timeline_judgement_date` | FCL 里程碑日期（同表17 `timeline_judgement_date`） | 视图计算 | 取自 `loan_fcl.timeline_judgement_date` | date | {2026-02-04, 2025-10-15, 2026-07-15, 2026-01-18, 2025-11-14, 2025-11-29, 2020-01-22, 2025-09-16, 2026-04-13} | 2026-02-04 | 表17 `timeline_judgement_date` | Milestone Timeline 展示 | ✅；填充 272/122550=0% |
| `timeline_sale_date_projected_date` | FCL 里程碑日期（同表17 `timeline_sale_date_projected_date`） | 视图计算 | 取自 `loan_fcl.timeline_sale_date_projected_date` | date | {2026-04-07, 2026-04-08, 2026-03-31, 2026-04-02, 2025-06-05, 2026-06-26, 2026-05-15, 2025-08-26, 2026-01-16, 2025-01-23, 2025-05-16, 2025-11-04, 2026-03-27, 2026-05-19, 2025-09-09} | 2026-04-07 | 表17 `timeline_sale_date_projected_date` | Milestone Timeline 展示 | ✅；填充 521/122550=0% |
| `timeline_sale_date_set_date` | FCL 里程碑日期（同表17 `timeline_sale_date_set_date`） | 视图计算 | 取自 `loan_fcl.timeline_sale_date_set_date` | date | {2026-02-25, 2026-02-22, 2025-12-23, 2026-01-23, 2025-03-07, 2026-02-15, 2026-01-08, 2025-07-18, 2025-01-23, 2025-11-26, 2025-04-10, 2025-09-25, 2026-02-11, 2026-02-27, 2026-03-12, 2026-02-19} 等17种 | 2026-02-25 | 表17 `timeline_sale_date_set_date` | Milestone Timeline 展示 | ✅；填充 521/122550=0% |
| `timeline_final_title_cleared_date` | FCL 里程碑日期（同表17 `timeline_final_title_cleared_date`） | 视图计算 | 取自 `loan_fcl.timeline_final_title_cleared_date` | date | {2025-03-24, 2026-02-02} | 2025-03-24 | 表17 `timeline_final_title_cleared_date` | Milestone Timeline 展示 | ✅；填充 59/122550=0% |
| `timeline_sale_date_held_date` | FCL 里程碑日期（同表17 `timeline_sale_date_held_date`） | 视图计算 | 取自 `loan_fcl.timeline_sale_date_held_date` | date | {2026-03-11, 2025-10-14, 2026-01-16, 2025-01-23, 2025-12-04, 2025-12-29, 2025-11-04} | 2026-03-11 | 表17 `timeline_sale_date_held_date` | Milestone Timeline 展示 | ✅；填充 204/122550=0% |
| `timeline_foreclosure_completed_date` | FCL 里程碑日期（同表17 `timeline_foreclosure_completed_date`） | 视图计算 | 取自 `loan_fcl.timeline_foreclosure_completed_date` | date | 实测全为 NULL | — | 表17 `timeline_foreclosure_completed_date` | Milestone Timeline 展示 | ✅；填充 0/122550=0% |
| `timeline_third_party_sold_date_date` | FCL 里程碑日期（同表17 `timeline_third_party_sold_date_date`） | 视图计算 | 取自 `loan_fcl.timeline_third_party_sold_date_date` | date | 实测全为 NULL | — | 表17 `timeline_third_party_sold_date_date` | Milestone Timeline 展示 | ✅；填充 0/122550=0% |
| `timeline_third_party_proceeds_received_date` | FCL 里程碑日期（同表17 `timeline_third_party_proceeds_received_date`） | 视图计算 | 取自 `loan_fcl.timeline_third_party_proceeds_received_date` | date | {2026-03-05} | 2026-03-05 | 表17 `timeline_third_party_proceeds_received_date` | Milestone Timeline 展示 | ✅；填充 21/122550=0% |
| `target_notice_of_intent_days` | SLA 目标天数（同表17 `target_notice_of_intent_days`） | 视图计算 | `IFNULL(loan_fcl.target_notice_of_intent_days, 默认值)` | bigint NOT NULL | {30}（1种） | 30 | 表17 `target_notice_of_intent_days` | Target 基准 | ✅ 含 IFNULL 默认；填充 122550/122550=100% |
| `target_notice_of_intent_expired_days` | SLA 目标天数（同表17 `target_notice_of_intent_expired_days`） | 视图计算 | `IFNULL(loan_fcl.target_notice_of_intent_expired_days, 默认值)` | bigint NOT NULL | {90}（1种） | 90 | 表17 `target_notice_of_intent_expired_days` | Target 基准 | ✅ 含 IFNULL 默认；填充 122550/122550=100% |
| `target_approved_for_referral_days` | SLA 目标天数（同表17 `target_approved_for_referral_days`） | 视图计算 | `IFNULL(loan_fcl.target_approved_for_referral_days, 默认值)` | bigint NOT NULL | {30}（1种） | 30 | 表17 `target_approved_for_referral_days` | Target 基准 | ✅ 含 IFNULL 默认；填充 122550/122550=100% |
| `target_referred_to_attorney_days` | SLA 目标天数（同表17 `target_referred_to_attorney_days`） | 视图计算 | `IFNULL(loan_fcl.target_referred_to_attorney_days, 默认值)` | bigint NOT NULL | {1}（1种） | 1 | 表17 `target_referred_to_attorney_days` | Target 基准 | ✅ 含 IFNULL 默认；填充 122550/122550=100% |
| `target_referred_to_foreclosure_days` | SLA 目标天数（同表17 `target_referred_to_foreclosure_days`） | 视图计算 | `IFNULL(loan_fcl.target_referred_to_foreclosure_days, 默认值)` | bigint NOT NULL | {1}（1种） | 1 | 表17 `target_referred_to_foreclosure_days` | Target 基准 | ✅ 含 IFNULL 默认；填充 122550/122550=100% |
| `target_title_report_received_days` | SLA 目标天数（同表17 `target_title_report_received_days`） | 视图计算 | `IFNULL(loan_fcl.target_title_report_received_days, 默认值)` | bigint NOT NULL | {30}（1种） | 30 | 表17 `target_title_report_received_days` | Target 基准 | ✅ 含 IFNULL 默认；填充 122550/122550=100% |
| `target_preliminary_title_cleared_days` | SLA 目标天数（同表17 `target_preliminary_title_cleared_days`） | 视图计算 | `IFNULL(loan_fcl.target_preliminary_title_cleared_days, 默认值)` | bigint NOT NULL | {30}（1种） | 30 | 表17 `target_preliminary_title_cleared_days` | Target 基准 | ✅ 含 IFNULL 默认；填充 122550/122550=100% |
| `target_first_legal_days` | SLA 目标天数（同表17 `target_first_legal_days`） | 视图计算 | `IFNULL(loan_fcl.target_first_legal_days, 默认值)` | bigint NOT NULL | {120}（1种） | 120 | 表17 `target_first_legal_days` | Target 基准 | ✅ 含 IFNULL 默认；填充 122550/122550=100% |
| `target_service_days` | SLA 目标天数（同表17 `target_service_days`） | 视图计算 | `IFNULL(loan_fcl.target_service_days, 默认值)` | bigint NOT NULL | {90}（1种） | 90 | 表17 `target_service_days` | Target 基准 | ✅ 含 IFNULL 默认；填充 122550/122550=100% |
| `target_publication_days` | SLA 目标天数（同表17 `target_publication_days`） | 视图计算 | `IFNULL(loan_fcl.target_publication_days, 默认值)` | bigint NOT NULL | {30}（1种） | 30 | 表17 `target_publication_days` | Target 基准 | ✅ 含 IFNULL 默认；填充 122550/122550=100% |
| `target_judgement_hearing_set_days` | SLA 目标天数（同表17 `target_judgement_hearing_set_days`） | 视图计算 | `IFNULL(loan_fcl.target_judgement_hearing_set_days, 默认值)` | bigint NOT NULL | {120}（1种） | 120 | 表17 `target_judgement_hearing_set_days` | Target 基准 | ✅ 含 IFNULL 默认；填充 122550/122550=100% |
| `target_judgement_days` | SLA 目标天数（同表17 `target_judgement_days`） | 视图计算 | `IFNULL(loan_fcl.target_judgement_days, 默认值)` | bigint NOT NULL | {30}（1种） | 30 | 表17 `target_judgement_days` | Target 基准 | ✅ 含 IFNULL 默认；填充 122550/122550=100% |
| `target_sale_date_set_days` | SLA 目标天数（同表17 `target_sale_date_set_days`） | 视图计算 | `IFNULL(loan_fcl.target_sale_date_set_days, 默认值)` | bigint NOT NULL | {30}（1种） | 30 | 表17 `target_sale_date_set_days` | Target 基准 | ✅ 含 IFNULL 默认；填充 122550/122550=100% |
| `target_final_title_cleared_days` | SLA 目标天数（同表17 `target_final_title_cleared_days`） | 视图计算 | `IFNULL(loan_fcl.target_final_title_cleared_days, 默认值)` | bigint NOT NULL | {5}（1种） | 5 | 表17 `target_final_title_cleared_days` | Target 基准 | ✅ 含 IFNULL 默认；填充 122550/122550=100% |
| `target_sale_date_held_days` | SLA 目标天数（同表17 `target_sale_date_held_days`） | 视图计算 | `IFNULL(loan_fcl.target_sale_date_held_days, 默认值)` | bigint NOT NULL | {0}（1种） | 0 | 表17 `target_sale_date_held_days` | Target 基准 | ✅ 含 IFNULL 默认；填充 122550/122550=100% |
| `actual_notice_of_intent_days` | 实际历时天数（notice_of_intent） | 视图计算 | `TO_DAYS(timeline_notice_of_intent_date) − TO_DAYS(nextduedate)` | int | -594 ~ 811 | -594 | 本视图 timeline + nextduedate | Actual Days 展示 | ✅ 视图实时计算；填充 145/122550=0% |
| `actual_notice_of_intent_expire_days` | 实际历时天数（notice_of_intent_expire） | 视图计算 | `TO_DAYS(timeline_notice_of_intent_expire_date) − TO_DAYS(nextduedate)` | int | 实测全为 NULL | — | 本视图 timeline + nextduedate | Actual Days 展示 | ✅ 视图实时计算；填充 0/122550=0% |
| `actual_approved_for_referral_days` | 实际历时天数（approved_for_referral） | 视图计算 | `TO_DAYS(timeline_approved_for_referral_date) − TO_DAYS(nextduedate)` | int | 实测全为 NULL | — | 本视图 timeline + nextduedate | Actual Days 展示 | ✅ 视图实时计算；填充 0/122550=0% |
| `actual_referred_to_attorney_days` | 实际历时天数（referred_to_attorney） | 视图计算 | `TO_DAYS(timeline_referred_to_attorney_date) − TO_DAYS(nextduedate)` | int | 实测全为 NULL | — | 本视图 timeline + nextduedate | Actual Days 展示 | ✅ 视图实时计算；填充 0/122550=0% |
| `actual_referred_to_foreclosure_days` | 实际历时天数（referred_to_foreclosure） | 视图计算 | `TO_DAYS(timeline_referred_to_foreclosure_date) − TO_DAYS(nextduedate)` | int | -2147 ~ 1274 | -2147 | 本视图 timeline + nextduedate | Actual Days 展示 | ✅ 视图实时计算；填充 2346/122550=2% |
| `actual_title_report_received_days` | 实际历时天数（title_report_received） | 视图计算 | `TO_DAYS(timeline_title_report_received_date) − TO_DAYS(nextduedate)` | int | 215 ~ 1035 | 215 | 本视图 timeline + nextduedate | Actual Days 展示 | ✅ 视图实时计算；填充 95/122550=0% |
| `actual_preliminary_title_cleared_days` | 实际历时天数（preliminary_title_cleared） | 视图计算 | `TO_DAYS(timeline_preliminary_title_cleared_date) − TO_DAYS(nextduedate)` | int | 277 ~ 754（25种） | 357 | 本视图 timeline + nextduedate | Actual Days 展示 | ✅ 视图实时计算；填充 58/122550=0% |
| `actual_first_legal_days` | 实际历时天数（first_legal） | 视图计算 | `TO_DAYS(timeline_first_legal_date) − TO_DAYS(nextduedate)` | int | -2072 ~ 1100 | -2072 | 本视图 timeline + nextduedate | Actual Days 展示 | ✅ 视图实时计算；填充 1121/122550=1% |
| `actual_service_days` | 实际历时天数（service） | 视图计算 | `TO_DAYS(timeline_service_date) − TO_DAYS(nextduedate)` | int | -2030 ~ 1108 | -2030 | 本视图 timeline + nextduedate | Actual Days 展示 | ✅ 视图实时计算；填充 557/122550=0% |
| `actual_publication_days` | 实际历时天数（publication） | 视图计算 | `TO_DAYS(timeline_publication_date) − TO_DAYS(nextduedate)` | int | 实测全为 NULL | — | 本视图 timeline + nextduedate | Actual Days 展示 | ✅ 视图实时计算；填充 0/122550=0% |
| `actual_judgement_hearing_set_days` | 实际历时天数（judgement_hearing_set） | 视图计算 | `TO_DAYS(timeline_judgement_hearing_set_date) − TO_DAYS(nextduedate)` | int | -200 ~ 1129 | -200 | 本视图 timeline + nextduedate | Actual Days 展示 | ✅ 视图实时计算；填充 271/122550=0% |
| `actual_judgement_days` | 实际历时天数（judgement） | 视图计算 | `TO_DAYS(timeline_judgement_date) − TO_DAYS(nextduedate)` | int | -1622 ~ 1260 | -1622 | 本视图 timeline + nextduedate | Actual Days 展示 | ✅ 视图实时计算；填充 271/122550=0% |
| `actual_sale_date_set_days` | 实际历时天数（sale_date_set） | 视图计算 | `TO_DAYS(timeline_sale_date_set_date) − TO_DAYS(nextduedate)` | int | -359 ~ 1148 | -359 | 本视图 timeline + nextduedate | Actual Days 展示 | ✅ 视图实时计算；填充 517/122550=0% |
| `actual_final_title_cleared_days` | 实际历时天数（final_title_cleared） | 视图计算 | `TO_DAYS(timeline_final_title_cleared_date) − TO_DAYS(nextduedate)` | int | 277 ~ 754（25种） | 357 | 本视图 timeline + nextduedate | Actual Days 展示 | ✅ 视图实时计算；填充 58/122550=0% |
| `actual_sale_date_held_days` | 实际历时天数（sale_date_held） | 视图计算 | `TO_DAYS(timeline_sale_date_held_date) − TO_DAYS(nextduedate)` | int | 187 ~ 1075 | 187 | 本视图 timeline + nextduedate | Actual Days 展示 | ✅ 视图实时计算；填充 203/122550=0% |
| `variance_active_bankruptcy` | 同表17 `variance_active_bankruptcy` | 视图计算 | `loan_fcl.variance_active_bankruptcy` | int | 实测全为 NULL | — | 表17 `variance_active_bankruptcy` | BK 方差 | ✅；填充 0/122550=0% |
| `variance_completed_bankruptcy` | 同表17 `variance_completed_bankruptcy` | 视图计算 | `loan_fcl.variance_completed_bankruptcy` | int | 实测全为 NULL | — | 表17 `variance_completed_bankruptcy` | BK 方差 | ✅；填充 0/122550=0% |
| `variance_estimated_hold_days` | 同表17 `variance_estimated_hold_days` | 视图计算 | `loan_fcl.variance_estimated_hold_days` | int | 实测全为 NULL | — | 表17 `variance_estimated_hold_days` | BK 方差 | ✅；填充 0/122550=0% |
| `variance_bankruptcies` | 同表17 `variance_bankruptcies` | 视图计算 | `loan_fcl.variance_bankruptcies` | int | 实测全为 NULL | — | 表17 `variance_bankruptcies` | BK 方差 | ✅；填充 0/122550=0% |
| `bid_approval_status` | 同表17 `bid_approval_status` | 视图计算 | `loan_fcl.bid_approval_status` | varchar(128) | 实测全为 NULL | — | 表17 `bid_approval_status` | Bid Approval 展示 | ✅；填充 0/122550=0% |
| `bid_approval_sale_date` | 同表17 `bid_approval_sale_date` | 视图计算 | `loan_fcl.bid_approval_sale_date` | date | 实测全为 NULL | — | 表17 `bid_approval_sale_date` | Bid Approval 展示 | ✅；填充 0/122550=0% |
| `bid_approval_bid_amount` | 同表17 `bid_approval_bid_amount` | 视图计算 | `loan_fcl.bid_approval_bid_amount` | decimal(32,16) | {$125,366.73, $390,832.50, $231,285.22, $136,392.44, $154,591.01, $543,305.96, $271,278.01, $90,000, $428,971.78}（9种） | $125,366.73 | 表17 `bid_approval_bid_amount` | Bid Approval 展示 | ✅；填充 254/122550=0% |
| `bid_approval_loan_resolution_holods` | 同表17 `bid_approval_loan_resolution_holods` | 视图计算 | `loan_fcl.bid_approval_loan_resolution_holods` | text | 实测全为 NULL | — | 表17 `bid_approval_loan_resolution_holods` | Bid Approval 展示 | ✅；填充 0/122550=0% |
| `summary_servicer_number` | 同表17 `summary_servicer_number` | 视图计算 | `loan_fcl.summary_servicer_number` | varchar(64) | 实测全为 NULL | — | 表17 `summary_servicer_number` | Summary 展示 | ✅；填充 0/122550=0% |
| `summary_foreclosure_status` | 同表17 `summary_foreclosure_status` | 视图计算 | `loan_fcl.summary_foreclosure_status` | varchar(64) | {Active Foreclosure, Closed Foreclosure:Loss Mitigation, Closed Foreclosure:Reinstated, Closed Foreclosure:Paid in Full, Closed Foreclosure:Process Complete, 1. First Legal Pending, Closed Foreclosure:Deed in Lieu Cmplte, 2. First Legal Filed, 5. Sales Held} | Active Foreclosure | 表17 `summary_foreclosure_status` | Summary 展示 | ✅；填充 2330/122550=2% |
| `summary_completed_foreclosure` | 同表17 `summary_completed_foreclosure` | 视图计算 | `loan_fcl.summary_completed_foreclosure` | int | 实测全为 NULL | — | 表17 `summary_completed_foreclosure` | Summary 展示 | ✅；填充 0/122550=0% |
| `summary_foreclosure_bid_amount` | 同表17 `summary_foreclosure_bid_amount` | 视图计算 | `loan_fcl.summary_foreclosure_bid_amount` | decimal(32,16) | {$125,366.73, $390,832.50, $231,285.22, $136,392.44, $154,591.01, $543,305.96, $271,278.01, $90,000, $428,971.78}（9种） | $125,366.73 | 表17 `summary_foreclosure_bid_amount` | Summary 展示 | ✅；填充 254/122550=0% |
| `summary_srv_fc_bid_amount` | 同表17 `summary_srv_fc_bid_amount` | 视图计算 | `loan_fcl.summary_srv_fc_bid_amount` | decimal(32,16) | {$125,366.73, $390,832.50, $231,285.22, $136,392.44, $154,591.01, $543,305.96, $271,278.01, $90,000, $428,971.78}（9种） | $125,366.73 | 表17 `summary_srv_fc_bid_amount` | Summary 展示 | ✅；填充 254/122550=0% |
| `summary_foreclosure_sale_amount` | 同表17 `summary_foreclosure_sale_amount` | 视图计算 | `loan_fcl.summary_foreclosure_sale_amount` | decimal(32,16) | {$203,122.00, $357,200, $274,000, $165,900, $90,001.00, $400,000}（6种） | $203,122.00 | 表17 `summary_foreclosure_sale_amount` | Summary 展示 | ✅；填充 182/122550=0% |
| `summary_judicial_foreclosure` | 同表17 `summary_judicial_foreclosure` | 视图计算 | `loan_fcl.summary_judicial_foreclosure` | int | {0, 1}（2种） | 0 | 表17 `summary_judicial_foreclosure` | Summary 展示 | ✅；填充 2069/122550=2% |
| `summary_foreclosure_attorney` | 同表17 `summary_foreclosure_attorney` | 视图计算 | `loan_fcl.summary_foreclosure_attorney` | varchar(256) | {Lender Legal PLLC, McPhail Sanchez, LLC, Brock & Scott PLLC, Vylla Solutions, LLC} | Lender Legal PLLC | 表17 `summary_foreclosure_attorney` | Summary 展示 | ✅；填充 116/122550=0% |
| `summary_contested_litigation` | 同表17 `summary_contested_litigation` | 视图计算 | `loan_fcl.summary_contested_litigation` | int | {0, 1}（2种） | 0 | 表17 `summary_contested_litigation` | Summary 展示 | ✅；填充 2040/122550=2% |
| `summary_firm` | 同表17 `summary_firm` | 视图计算 | `loan_fcl.summary_firm` | varchar(256) | 文本，45种（样例 Albertelli Law … ZBS Law, LLP） | Albertelli Law | 表17 `summary_firm` | Summary 展示 | ✅；填充 2243/122550=2% |
| `summary_type` | 同表17 `summary_type` | 视图计算 | `loan_fcl.summary_type` | varchar(128) | {Non Judicial, Judicial} | Non Judicial | 表17 `summary_type` | Summary 展示 | ✅；填充 2069/122550=2% |
| `summary_sms_days_in_fcl` | 同表17 `summary_sms_days_in_fcl` | 视图计算 | `loan_fcl.summary_sms_days_in_fcl` | int | 7 ~ 531 | 7 | 表17 `summary_sms_days_in_fcl` | Summary 展示 | ✅；填充 1797/122550=1% |
| `summary_days_in_fcl` | 同表17 `summary_days_in_fcl` | 视图计算 | `loan_fcl.summary_days_in_fcl` | int | 7 ~ 739 | 7 | 表17 `summary_days_in_fcl` | Summary 展示 | ✅；填充 2214/122550=2% |
| `summary_current_step` | 同表17 `summary_current_step` | 视图计算 | `loan_fcl.summary_current_step` | varchar(128) | 文本，37种（样例 Acceleration Letter Sent … TSG Report Received） | Acceleration Letter Sent | 表17 `summary_current_step` | Summary 展示 | ✅；填充 2243/122550=2% |
| `summary_last_step_completed` | 同表17 `summary_last_step_completed` | 视图计算 | `loan_fcl.summary_last_step_completed` | varchar(256) | 文本，32种（样例 Answer Period Will Expire On … TSG Report Received） | Answer Period Will Expire On | 表17 `summary_last_step_completed` | Summary 展示 | ✅；填充 2069/122550=2% |
| `summary_last_step_completed_date` | 同表17 `summary_last_step_completed_date` | 视图计算 | `loan_fcl.summary_last_step_completed_date` | date | 2019-10-14 ~ 2026-03-12 | 2019-10-14 | 表17 `summary_last_step_completed_date` | Summary 展示 | ✅；填充 2069/122550=2% |
| `create_user` | 管理字段（同表17 `create_user`） | 视图计算 | `loan_fcl.create_user` | bigint | 实测全为 NULL | — | 表17 `create_user` | 审计/多租户 | ✅；填充 0/122550=0% |
| `create_dept` | 管理字段（同表17 `create_dept`） | 视图计算 | `loan_fcl.create_dept` | bigint | 实测全为 NULL | — | 表17 `create_dept` | 审计/多租户 | ✅；填充 0/122550=0% |
| `create_time` | 管理字段（同表17 `create_time`） | 视图计算 | `loan_fcl.create_time` | datetime | 实测全为 NULL | — | 表17 `create_time` | 审计/多租户 | ✅；填充 0/122550=0% |
| `update_user` | 管理字段（同表17 `update_user`） | 视图计算 | `loan_fcl.update_user` | bigint | 实测全为 NULL | — | 表17 `update_user` | 审计/多租户 | ✅；填充 0/122550=0% |
| `update_time` | 管理字段（同表17 `update_time`） | 视图计算 | `loan_fcl.update_time` | datetime | 实测全为 NULL | — | 表17 `update_time` | 审计/多租户 | ✅；填充 0/122550=0% |
| `status` | 管理字段（同表17 `status`） | 视图计算 | `loan_fcl.status` | int | {0}（1种） | 0 | 表17 `status` | 审计/多租户 | ✅；填充 2359/122550=2% |
| `is_deleted` | 是否软删除 | 视图计算 | 视图恒置 0 | int NOT NULL | {0}（1种） | 0 | — | 软删除标志 | ✅ 视图硬编码 0；填充 122550/122550=100% |
| `tenant_id` | 管理字段（同表17 `tenant_id`） | 视图计算 | `loan_fcl.tenant_id` | varchar(12) | {000000, 984018} | 000000 | 表17 `tenant_id` | 审计/多租户 | ✅；填充 2359/122550=2% |
| `var_notice_of_intent_days` | SLA 偏差天数（notice_of_intent；正=超期） | 视图计算 | `actual − 累计 target` | bigint | -624 ~ 781 | -624 | 本视图 actual_* − target_* | Variance 展示 | ✅ 视图实时计算；填充 145/122550=0% |
| `var_notice_of_intent_expire_days` | SLA 偏差天数（notice_of_intent_expire；正=超期） | 视图计算 | `actual − 累计 target` | bigint | 实测全为 NULL | — | 本视图 actual_* − target_* | Variance 展示 | ✅ 视图实时计算；填充 0/122550=0% |
| `var_approved_for_referral_days` | SLA 偏差天数（approved_for_referral；正=超期） | 视图计算 | `actual − 累计 target` | bigint | 实测全为 NULL | — | 本视图 actual_* − target_* | Variance 展示 | ✅ 视图实时计算；填充 0/122550=0% |
| `var_referred_to_attorney_days` | SLA 偏差天数（referred_to_attorney；正=超期） | 视图计算 | `actual − 累计 target` | bigint | 实测全为 NULL | — | 本视图 actual_* − target_* | Variance 展示 | ✅ 视图实时计算；填充 0/122550=0% |
| `var_referred_to_foreclosure_days` | SLA 偏差天数（referred_to_foreclosure；正=超期） | 视图计算 | `actual − 累计 target` | bigint | -2299 ~ 1122 | -2299 | 本视图 actual_* − target_* | Variance 展示 | ✅ 视图实时计算；填充 2346/122550=2% |
| `var_title_report_received_days` | SLA 偏差天数（title_report_received；正=超期） | 视图计算 | `actual − 累计 target` | bigint | 33 ~ 853 | 33 | 本视图 actual_* − target_* | Variance 展示 | ✅ 视图实时计算；填充 95/122550=0% |
| `var_preliminary_title_cleared_days` | SLA 偏差天数（preliminary_title_cleared；正=超期） | 视图计算 | `actual − 累计 target` | bigint | 65 ~ 542（25种） | 145 | 本视图 actual_* − target_* | Variance 展示 | ✅ 视图实时计算；填充 58/122550=0% |
| `var_first_legal_days` | SLA 偏差天数（first_legal；正=超期） | 视图计算 | `actual − 累计 target` | bigint | -2404 ~ 768 | -2404 | 本视图 actual_* − target_* | Variance 展示 | ✅ 视图实时计算；填充 1121/122550=1% |
| `var_service_days` | SLA 偏差天数（service；正=超期） | 视图计算 | `actual − 累计 target` | bigint | -2452 ~ 686 | -2452 | 本视图 actual_* − target_* | Variance 展示 | ✅ 视图实时计算；填充 557/122550=0% |
| `var_publication_days` | SLA 偏差天数（publication；正=超期） | 视图计算 | `actual − 累计 target` | bigint | 实测全为 NULL | — | 本视图 actual_* − target_* | Variance 展示 | ✅ 视图实时计算；填充 0/122550=0% |
| `var_judgement_hearing_set_days` | SLA 偏差天数（judgement_hearing_set；正=超期） | 视图计算 | `actual − 累计 target` | bigint | -772 ~ 557 | -772 | 本视图 actual_* − target_* | Variance 展示 | ✅ 视图实时计算；填充 271/122550=0% |
| `var_judgement_days` | SLA 偏差天数（judgement；正=超期） | 视图计算 | `actual − 累计 target` | bigint | -2224 ~ 658 | -2224 | 本视图 actual_* − target_* | Variance 展示 | ✅ 视图实时计算；填充 271/122550=0% |
| `var_sale_date_set_days` | SLA 偏差天数（sale_date_set；正=超期） | 视图计算 | `actual − 累计 target` | bigint | -991 ~ 516 | -991 | 本视图 actual_* − target_* | Variance 展示 | ✅ 视图实时计算；填充 517/122550=0% |
| `var_final_title_cleared_days` | SLA 偏差天数（final_title_cleared；正=超期） | 视图计算 | `actual − 累计 target` | bigint | -360 ~ 117（25种） | -280 | 本视图 actual_* − target_* | Variance 展示 | ✅ 视图实时计算；填充 58/122550=0% |
| `var_sale_date_held_days` | SLA 偏差天数（sale_date_held；正=超期） | 视图计算 | `actual − 累计 target` | bigint | -450 ~ 438 | -450 | 本视图 actual_* − target_* | Variance 展示 | ✅ 视图实时计算；填充 203/122550=0% |
| `var_total` | 总偏差合计 | 视图计算 | Σ(actual_* − target_*) | bigint | 实测全为 NULL | — | 本视图 var_* | 总 SLA 偏差 | ✅ 任一分项 NULL 则为 NULL；填充 0/122550=0% |
| `target_total` | 目标天数合计 | 视图计算 | Σ(target_*_days) | bigint NOT NULL | {637}（1种） | 637 | 本视图 target_* | 总目标=637 | ✅；填充 122550/122550=100% |
| `actual_total` | 实际历时合计 | 视图计算 | Σ(actual_*_days) | bigint | 实测全为 NULL | — | 本视图 actual_* | 总历时 | ✅ 任一分项 NULL 则为 NULL；填充 0/122550=0% |

<!-- DATADIC26 START -->
### 表 26：`newrez.portnewrezdatadic` — Redshift 解码字典

> **角色**：Newrez 数值编码 → 文本 的字典（长表）。FCL ETL 在 Redshift 把 LM/BK 整数码 `LEFT JOIN` 本表解码为文本后写入 BPS（`basic_data_pool_config.py:835-840` LM、`:367` BK；`concat(code,'.0')` 对齐源存法）。**dev MySQL 无此表**，仅 prod Redshift `newrez` schema 有。
>
> **结构（6 列）**：`package` \| `module_name` \| `appendix` \| `field_name` \| `code` \| `description`。FCL 相关 `field_name`：LM 模块 LMDeal/LMProgram/LMStatus/LMDecision/DenialReason/BorrowerIntention；BK 模块 BKStatus/BKStage。
>
> **范围**：小字段（LMDeal/BorrowerIntention/BKStatus/BKStage）列**全量**；大字段（LMProgram/LMStatus/LMDecision/DenialReason）只列 **prod 最新快照实际出现的码**（去长尾；字典总码数见各表标题）。doc 19 `㉑ dict·portnewrezdatadic` 节只列 5 样例贷款用到的码。
>
> **查询 SQL（redshift_prod 只读）**：
```sql
SELECT field_name, code, description FROM newrez.portnewrezdatadic
WHERE (module_name='LossMitigation' AND field_name IN
       ('LMDeal','LMProgram','LMStatus','LMDecision','DenialReason','BorrowerIntention'))
   OR (module_name='Bankruptcy' AND field_name IN ('BKStatus','BKStage'));
```

#### LMDeal ← `newrez.portnewrezlm.lmdeal`（LossMitigation；字典 13 码，本表全量列出）

| 编码 | 解码（description） |
|---|---|
| 1 | Modification |
| 2 | Evaluation |
| 3 | Reinstatement |
| 4 | Payment Plan |
| 5 | Forbearance |
| 6 | Short Sale |
| 7 | DIL |
| 8 | Loan Sale |
| 9 | Payoff |
| 10 | Settlement |
| 11 | Deferment |
| 12 | CFK |
| 13 | Consent Judgement |

#### LMProgram ← `newrez.portnewrezlm.lmprogram`（LossMitigation；字典 388 码 · prod 实际 22 码，本表列 prod 出现的码）

| 编码 | 解码（description） |
|---|---|
| 8 | Short Sale |
| 10 | Deed-in-Lieu |
| 12 | Short-term Forbearance |
| 21 | Evaluation |
| 25 | Payoff |
| 29 | Repayment Plan |
| 73 | Deferment |
| 151 | Disaster Forbearance |
| 215 | Short-term FB COVID (RETIRED 2023-11-01) |
| 240 | SLS Standard Mod |
| 273 | Standard Proprietary Modification |
| 348 | FHA Recovery SAPC |
| 359 | Standard Proprietary Mod - IA Required |
| 365 | VA 40 Year Modification |
| 396 | VA Traditional |
| 419 | Bridger mod |
| 491 | （字典无此码） |
| 496 | （字典无此码） |
| 498 | （字典无此码） |
| 499 | （字典无此码） |
| 527 | （字典无此码） |
| 531 | （字典无此码） |

#### LMStatus ← `newrez.portnewrezlm.lmstatus`（LossMitigation；字典 149 码 · prod 实际 17 码，本表列 prod 出现的码）

| 编码 | 解码（description） |
|---|---|
| 5 | Document Follow-up |
| 13 | Follow up for 1st Trial Payment |
| 20 | Book mod |
| 25 | Monitor for pmts/funds |
| 45 | Countered by Supervisor |
| 48 | Underwriting Follow Up Required |
| 101 | Resubmitted to Underwriting |
| 112 | Workout Denial |
| 113 | Monitor Forbearance |
| 116 | Not Assigned |
| 126 | DIL Title Ordered |
| 135 | DIL Sent for Recording |
| 139 | Deferment Plan In Progress |
| 140 | Deferment Agreement Ordered |
| 166 | Pending Financials  |
| 172 | Liquidation Referral |
| 186 | Monitor for Mod Agreement – Final Trial Payment Due |

#### LMDecision ← `newrez.portnewrezlm.lmdecision`（LossMitigation；字典 23 码 · prod 实际 13 码，本表列 prod 出现的码）

| 编码 | 解码（description） |
|---|---|
| 1 | Modification Complete |
| 3 | DIL Complete |
| 4 | Forbearance Complete |
| 5 | Reinstated/Current |
| 6 | Referral to FC |
| 7 | Not Eligible for Loss Mitigation |
| 10 | Request Incomplete/Failed to Provide Information |
| 11 | LMS Opened in Error |
| 12 | No Change in Circumstance |
| 14 | Deferment Completed |
| 17 | Full Pay Off |
| 18 | FC Sale Held |
| 99 | Pending |

#### DenialReason ← `newrez.portnewrezlm.denialreason`（LossMitigation；字典 130 码 · prod 实际 18 码，本表列 prod 出现的码）

| 编码 | 解码（description） |
|---|---|
| 4 | Withdrawal of Request/Non-Acceptance |
| 6 | Ineligible Borrower |
| 9 | Investor Not Participating |
| 19 | Exceeds Allowable Timeframe |
| 21 | Request Incomplete/Failed to Provide Documentation |
| 30 | Failed Plan |
| 34 | Ineligible Borrower: Not a Natural Person |
| 40 | PMI Company Decline |
| 50 | Request Withdrawn Before Offer |
| 75 | Declined Mod Review in favor of SS/DIL |
| 76 | HAMP Sunset |
| 86 | Request Withdrawn |
| 95 | Loan not eligible for deferment |
| 108 | Unable to achieve target payment |
| 109 | Loan not due for 3 or more monthly payments |
| 112 | No verifiable Hardship |
| 118 | Loan not 90+ DPD  |
| 124 | Hardship not resolved |

#### BorrowerIntention ← `newrez.portnewrezlm.borrowerintention`（LossMitigation；字典 3 码，本表全量列出）

| 编码 | 解码（description） |
|---|---|
| 1 | Unknown |
| 2 | Retention |
| 3 | Disposition |

#### BKStatus ← `newrez.portnewrezbk.bkstatus`（Bankruptcy；字典 5 码，本表全量列出）

| 编码 | 解码（description） |
|---|---|
| 1 | Active |
| 2 | Discharged |
| 3 | Dismissed |
| 4 | Closed |
| 5 | ReliefGranted |

#### BKStage ← `newrez.portnewrezbk.bkstage`（Bankruptcy；字典 22 码，本表全量列出）

| 编码 | 解码（description） |
|---|---|
| 0 | Petition |
| 1 | Received |
| 2 | 341 Meeting |
| 3 | Objection to Plan |
| 4 | Confirmation |
| 5 | Discharge Ability |
| 6 | POC Bar |
| 7 | Proof of Claim |
| 8 | Discharged |
| 9 | Discharged Review |
| 10 | Dismissed |
| 11 | Reaffirmed |
| 12 | Vacated |
| 13 | Transfer of Claim |
| 14 | Final Cure (Chapter 13) |
| 15 | Attorney Consent |
| 16 | Chapter Converted |
| 17 | Termination |
| 18 | Trustee No Asset CH 7 |
| 19 | Trustee Abandonment CH 7  |
| 20 | Plan Review |
| 21 | Motion to Determine Final Cure |

<!-- DATADIC26 END -->

---

---

## 4. Foreclosure 状态机（`delinq` 字段推导逻辑）

`port.basic_data_daily_loan_common_clean.delinq` 字段是全系统的核心状态字段，通过以下逻辑推导：

```sql
-- 通用逻辑（以 SLS 为例，其他 Servicer 同理）
CASE
    -- 优先判断 Servicer 明确声明的终态
    WHEN svcdelinq = 'Foreclosure'       THEN 'FCL'
    WHEN svcdelinq = 'REO'               THEN 'REO'
    WHEN svcdelinq = 'Paid in Full'      THEN 'P'
    WHEN svcdelinq = 'Bankruptcy'        THEN ... -- 仍需计算逾期档位
    -- Newrez 额外情形
    WHEN svcdelinq IN ('Foreclosure / Non-Perf BK',
                       'Foreclosure / Perf BK')  THEN 'FCL'
    WHEN svcdelinq = 'Full Payoff'       THEN 'P'
    -- Carrington 额外情形
    WHEN svcdelinq IN ('Completed Payoff',
                       'Completed Short Sale',
                       'Completed REO Sale')     THEN 'P'
    WHEN svcdelinq IN ('R', 'REO')       THEN 'REO'
    WHEN fcl_flag = 'Active'             THEN 'FCL'  -- Carrington 专用
    -- 通用日期计算（基于 days360 函数）
    ELSE
        CASE
            WHEN days360(nextduedate, fctrdt) <  30  THEN 'C'
            WHEN days360(nextduedate, fctrdt) <  60  THEN 'D30'
            WHEN days360(nextduedate, fctrdt) <  90  THEN 'D60'
            WHEN days360(nextduedate, fctrdt) < 120  THEN 'D90'
            ELSE 'D120P'
        END
END AS delinq
```

**状态转移图：**
```
  C ──→ D30 ──→ D60 ──→ D90 ──→ D120P ──→ FCL ──→ REO
  │                               │           │
  │                               │           └──→ P（3rd party sale 后）
  └───────────────────────────────┴──→ P（还清）
  
  特殊状态：VASP（部分 Newrez 贷款的特殊豁免状态）
```

**days360 函数说明：**
- 使用 360天/年的银行惯例（每月30天）计算日期差
- `days360(nextduedate, fctrdt)` = 从"下一应还款日"到"factor date"的天数
- 正值表示逾期，负值表示提前（通常 = 0 = Current）

---

## 5. 关键字段跨 Servicer 对照

下表展示了同一业务概念在不同 Servicer 中的字段名称差异：

| 业务概念 | `port.basic_data_daily_loan_common` 字段 | SLS 来源字段 | Shellpoint/Newrez 来源字段 | Carrington 来源字段 | Selene 来源字段 |
|---------|-------------------------------------|------------|--------------------------|-------------------|---------------|
| 逾期状态 | `delq_status` | `portassetdaily.delq_status_mba` | `portnewrezgeneral.delinquency_status_mba` | `portcarrington.loan_status` | `portselenemain.loan_status` |
| FCL 激活 | `fcl_flag` | `null`（SLS 未映射） | `null`（未映射） | `portcarrington.fcl_flag` | `portselenemain.foreclosure_status_code` |
| LM 激活 | `lm_flag` | `null` | `portnewrezlm.activelmflag` → `'1'='Y'` | `portcarrington.lm_flag` → `'Active'='Y'` | `portselenemain.lm_setup_date` not null → `'Y'` |
| Forbearance | `forbearance` | `portassetdaily.forbearance_flag` | `portnewrezlm.forbearancestatus`（数字码） | `portcarrington.covid_forbearance_flag` | `null` |
| 最后联系日 | `lastcontactdate` | `null` | `portnewrezcontact.lastcontactdate` | `portcarrington.date_delinq_contact` | `null` |
| FCL Referral 日期 | — | `portfcldaily.fcl_referred_to_attorney_date` | `portnewrezfc.fcreferraldate` | — | — |
| BK 申请日 | — | `portbkdaily.bk_filed_date` | `portnewrezbk.bkfileddate` | — | — |
| MFR 获批日 | — | `portbkdaily.bk_mfr_granted_date` | `portnewrezbk.mfrgranteddate` | — | — |

---

*文档结束 — v4 | 2026-05-28 | AI Agent (Claude Sonnet 4.6)*
