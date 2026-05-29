# Foreclosure Data Dictionary — PrefectFlow

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
| 2026-05-23 | AI Agent | v1 | Initial draft — reverse engineered from PrefectFlow Python/SQL source | prompt.md |
| 2026-05-25 | AI Agent (Claude Sonnet 4.6) | v2 | 新增表13（port.basic_data_loan_fcl，61列全量）和表14（port.basic_data_loan_foreclosure，62列全量）；包含DB实测类型、真实取值分布、INSERT填充状态标注；修正 fcstage 实际取值说明 | prompt.md |
| 2026-05-25 | AI Agent (Claude Sonnet 4.6) | v3 | 新增表15（port.portmonthbase，120列）和表16（port.portmonth，141列）；含Redshift实测行数/日期范围/delinq分布/关键字段统计；标注 portmonth 相对 portmonthbase 的23个新增字段（★） | prompt.md |
| 2026-05-28 | AI Agent (Claude Sonnet 4.6) | v4 | 新增表17（bpms_dev.sync_loan_foreclosure，72列，MCP实测）；7组字段全量记录（标识符/timeline_*/target_*_days/variance_*/bid_approval_*/summary_*/管理字段）；标注 target_*_days 硬编码DEFAULT值、bid_approval_loan_resolution_holods 列名拼写错误、actual_*_days 字段位于 sync_fcl_stage_info 而非本表 | prompt.md |

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
│  shellpoint.portshellpointfc   shellpoint.portshellpointbk          │
│  shellpoint.portshellpointlm   shellpoint.portshellpointreo         │
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

### 表 08：`shellpoint.portshellpointfc` — Shellpoint/Newrez Foreclosure

| 属性 | 值 |
|------|----|
| **表名** | `portshellpointfc` |
| **所属 Schema** | MySQL `shellpoint`（后迁移到 `newrez`） |
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

### 表 09：`shellpoint.portshellpointbk` — Shellpoint Bankruptcy

| 属性 | 值 |
|------|----|
| **表名** | `portshellpointbk` |
| **所属 Schema** | MySQL `shellpoint` |
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

### 表 10：`shellpoint.portshellpointlm` — Shellpoint Loss Mitigation

| 属性 | 值 |
|------|----|
| **表名** | `portshellpointlm` |
| **所属 Schema** | MySQL `shellpoint` |
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

### 表 11：`shellpoint.portshellpointreo` — Shellpoint REO

| 属性 | 值 |
|------|----|
| **表名** | `portshellpointreo` |
| **所属 Schema** | MySQL `shellpoint` |
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
| `fc_referral_date` | FCL Referral 日期（委托律师启动法拍） | Servicer FC 表 | 直接映射 | DATE | `2023-11-15` | `portfcldaily.fcl_referred_to_attorney_date`<br>`portshellpointfc.fcreferraldate` | 核心监控字段：NOI 发出 >60天未 referral = 高风险 | ✅ Confirmed |
| `noi_demand_letter_date` | NOI（Notice of Intent）或 Demand Letter 发出日期 | Servicer 标准日报 | 直接映射 | DATE | `2023-09-15` | `sls.portstandarddaily.lm_demand_expire_date`（推算） | FCL referral 时效检查的起点 | 🟡 Strong Inference |
| `bankruptcy_ind` | 破产标志 | `port.basic_data_daily_loan_common_clean.bankruptcy` | 直接映射 | VARCHAR | `Y`, `N` | `port.basic_data_daily_loan_common_clean.bankruptcy` | BK + FCL 并行分析 | ✅ Confirmed |
| `bk_chapter` | 破产章节 | Servicer BK 表 | 直接映射 | VARCHAR | `7`, `13` | `portbkdaily.bk_chapter_code` | — | ✅ Confirmed |
| `bk_filed_date` | 破产申请日 | Servicer BK 表 | 直接映射 | DATE | — | `portbkdaily.bk_filed_date` | BK 持续时间 | ✅ Confirmed |
| `inlossmit_ind` | LM 激活标志 | `port.basic_data_daily_loan_common_clean.lm_flag` | 直接映射 | VARCHAR | `Y`, `N` | — | LM 追踪 | ✅ Confirmed |
| `lm_plan_active_flag` | LM 计划是否活跃（区别于 LM 评估中） | Servicer LM 表 | 直接映射 | VARCHAR | `Y`, `N` | `portshellpointlm.activelmflag`（推算） | — | 🟡 Strong Inference |
| `contact_attempts_30d` | 过去30天内接触尝试次数 | Servicer 接触记录表 | 聚合计算：30天滚动窗口内 attempt 次数 | INT | `3`, `0` | `portshellpointcontact.mtdoutbound` 等 | CFPB 合规（要求定期接触 D120P 借款人） | 🟡 Strong Inference |
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
| **上游来源** | 写入来源不明（**不在 SYNC_TABLE_MAP 中**）；推测由 BPS 应用层（Java/Spring Boot）或专属 ETL 脚本直接写入；见 doc 02 v2 + doc 12 v4 |
| **下游使用** | BPS UI 5个面板（Milestone Timeline / Target Days / Variance / Bid Approval / Summary）；`bpms_dev.sync_fcl_stage_info`（阶段信息及 `actual_*_days` 实际天数字段） |
| **Foreclosure 关系** | 核心：`timeline_*` 字段驱动时间线面板；`target_*_days` 提供 SLA 基准；`summary_*` 字段驱动综合摘要面板 |
| **已知问题** | ① `actual_*_days`（实际历时天数）**不在本表**，而在 `bpms_dev.sync_fcl_stage_info`；② 列名 `bid_approval_loan_resolution_holods` 含拼写错误（应为 `holds`，已投产无法轻易修改）；③ 写入来源未通过 ETL 代码确认（见 doc 12 Section 14 对 SYNC_TABLE_MAP 的分析） |
| **MCP验证** | 2026-05-28 实测；INFORMATION_SCHEMA.COLUMNS + 行统计 SQL |

#### Group 1：标识符（6列）

| 字段名 | 字段业务含义 | 来源数据 | 计算/推导逻辑 | 数据类型 | 典型取值 | 上游字段 | 下游用途 | 备注 |
|--------|------------|---------|--------------|---------|---------|---------|---------|------|
| `bid_id` | 主键，自增 ID | 系统生成 | AUTO_INCREMENT | bigint NOT NULL | `1`, `2`, `3` | — | 内部主键 | ✅ Confirmed |
| `funding_id` | Fund / Funding 编号 | BPS 应用层 | 直接写入 | int NOT NULL | `101`, `202` | `port.portfunding.fundingid` | 关联 Funding 维度 | ✅ Confirmed |
| `loanid` | 系统贷款 ID（跨 Servicer 统一标识） | BPS 应用层 | 直接写入 | varchar(50) NOT NULL | `7727001272` | `port.basic_data_loan_fcl.loanid` | 全表 join key；关联 FCL 中间表 | ✅ Confirmed |
| `svcloanid` | Servicer 内部贷款号 | BPS 应用层 | 直接写入 | varchar(50) NOT NULL | `NR12345678` | `port.basic_data_loan_fcl.svc_loanid` | Servicer 对账字段 | ✅ Confirmed |
| `servicer` | Servicer 名称 | BPS 应用层 | 直接写入 | varchar(50) NOT NULL | `Newrez`, `Carrington` | — | Servicer 分组过滤 | ✅ Confirmed（实测：Newrez 88行 / Carrington 10行） |
| `dataasof` | 数据截止日（Factor Date） | BPS ETL | 直接写入 | date NOT NULL | `2026-05-01` | `port.basic_data_loan_fcl.dataasof` | 时间维度；数据新鲜度追踪 | ✅ Confirmed |

#### Group 2：FCL 时间线（`timeline_*`，19列）

> 对应 BPS UI 的 **Milestone Timeline 面板**。日期均为 date 类型，均可为 NULL（事件未发生时为空）。

| 字段名 | 字段业务含义 | 来源数据 | 计算/推导逻辑 | 数据类型 | 典型取值 | 上游字段 | 下游用途 | 备注 |
|--------|------------|---------|--------------|---------|---------|---------|---------|------|
| `timeline_notice_of_intent_date` | NOI 发出日期 | ETL | 直接映射 | date | `2025-03-01` | `port.basic_data_loan_fcl.noi_date` / `demandsentdate` | NOI 阶段起始；Milestone 第1步 | ✅ Confirmed |
| `timeline_notice_of_intent_end_date` | NOI 到期日 | ETL | 直接映射 | date | `2025-04-01` | `port.basic_data_loan_fcl.demandexpirationdate` | NOI 有效期截止 | ✅ Confirmed |
| `timeline_notice_of_intent_start_date` | NOI 阶段正式开始日 | ETL | 直接映射 | date | `2025-03-01` | — | NOI 倒计时起点 | ✅ Confirmed |
| `timeline_notice_of_intent_completed_date` | NOI 阶段完成日 | ETL | 直接映射 | date | `2025-04-15` | — | NOI 完结记录 | ✅ Confirmed |
| `timeline_approved_for_referral_date` | 批准转案律师日 | ETL | 直接映射 | date | `2025-04-20` | `port.basic_data_loan_fcl.fcsetupdate` | FCL 转案审批节点 | ✅ Confirmed |
| `timeline_referred_to_attorney_date` | 已转案律师确认日 | ETL | 直接映射 | date | `2025-04-25` | — | 律师接案确认 | ✅ Confirmed |
| `timeline_referred_to_foreclosure_date` | 正式转 FCL 日期 | ETL | 直接映射 | date | `2025-05-01` | `port.basic_data_loan_fcl.referral_start_date` | FCL 流程正式启动节点 | ✅ Confirmed |
| `timeline_title_report_received_date` | 产权报告收到日 | ETL | 直接映射 | date | `2025-06-01` | `port.basic_data_loan_fcl.titlereceiveddate` | 产权追踪第2步 | ✅ Confirmed |
| `timeline_preliminary_title_cleared_date` | 初步产权确认清查日 | ETL | 直接映射 | date | `2025-07-01` | `port.basic_data_loan_fcl.titlecleardate` | 产权追踪第3步 | ✅ Confirmed |
| `timeline_first_legal_date` | 第一次法律行动日 | ETL | 直接映射 | date | `2025-07-15` | `port.basic_data_loan_fcl.legal_start_date` | FCL 法律程序里程碑 | ✅ Confirmed |
| `timeline_service_date` | 完成送达日 | ETL | 直接映射 | date | `2025-09-01` | `port.basic_data_loan_fcl.service_start_date` | 法律送达完成节点 | ✅ Confirmed |
| `timeline_publication_date` | 拍卖公告发布日 | ETL | 直接映射 | date | `2025-10-01` | — | 拍卖公告发布节点 | ✅ Confirmed |
| `timeline_judgement_date` | 判决听证安排日（Judgment Hearing Scheduled） | ETL | 直接映射 | date | `2025-11-01` | `port.basic_data_loan_fcl.fcjudgment_hearing_scheduled` | Judgment 阶段起点；注：法院录入判决日（`fcjudgment_end_date`）为 ETL 预留字段，见 doc 12 Section 15 | ✅ Confirmed |
| `timeline_sale_date_projected_date` | 预计拍卖日期 | ETL | 直接映射 | date | `2025-12-15` | `port.basic_data_loan_fcl.fcscheduled_sale_date` | 拍卖安排节点 | ✅ Confirmed |
| `timeline_sale_date_held_date` | 实际拍卖日期 | ETL | 直接映射 | date | `2026-01-15` | `port.basic_data_loan_fcl.fcsale_held_date` | 拍卖完成确认 | ✅ Confirmed |
| `timeline_final_title_cleared_date` | 最终产权确认清查日 | ETL | 直接映射 | date | `2026-01-20` | `port.basic_data_loan_fcl.titlecleardate`（最终） | 产权追踪最终节点 | ✅ Confirmed |
| `timeline_third_party_proceeds_received_date` | 第三方购买款收到日 | ETL | 直接映射 | date | `2026-02-01` | `port.basic_data_loan_fcl.fcl3rdpartyproceedsreceiveddate` | 拍卖款到账追踪 | ✅ Confirmed |
| `timeline_third_party_proceeds_wired_date` | 第三方购买款转账日 | ETL | 直接映射 | date | `2026-02-05` | — | 资金拨付追踪 | ✅ Confirmed |
| `timeline_foreclosure_completed_date` | FCL 流程完结日 | ETL | 优先取 `dtdeedrecorded`，其次 `fcremovaldate` | date | `2026-02-15` | `port.basic_data_loan_fcl.dtdeedrecorded` / `fcremovaldate` | FCL 关闭里程碑 | ✅ Confirmed |

#### Group 3：SLA 目标天数（`target_*_days`，15列）

> 对应 BPS UI 的 **Target Days 面板**。全部为 `int NOT NULL`，含 **MySQL 硬编码 DEFAULT 值**（静态 SLA 阈值，非动态计算）。  
> ⚠️ `actual_*_days`（实际历时天数）**不在本表**，位于 `bpms_dev.sync_fcl_stage_info`。

| 字段名 | SLA 含义 | MySQL DEFAULT | 备注 |
|--------|---------|--------------|------|
| `target_notice_of_intent_days` | NOI 阶段目标天数 | `30` | NOI 发出后30天内进入下一阶段 |
| `target_notice_of_intent_expired_days` | NOI 到期等待目标天数 | `90` | NOI 等待期90天 |
| `target_approved_for_referral_days` | 批准转案目标天数 | `30` | 审批后30天内正式转案 |
| `target_referred_to_attorney_days` | 转案至律师接案目标天数 | `1` | 1天内律师确认接案 |
| `target_referred_to_foreclosure_days` | 转案至正式启动FCL目标天数 | `1` | 1天内正式进入FCL程序 |
| `target_title_report_received_days` | 产权报告到位目标天数 | `30` | 30天内收到产权报告 |
| `target_preliminary_title_cleared_days` | 初步产权确认目标天数 | `30` | 初步产权确认30天 |
| `target_first_legal_days` | 第一次法律行动目标天数 | `120` | 从正式FCL到First Legal最多120天 |
| `target_service_days` | 送达完成目标天数 | `90` | 90天内完成法律送达 |
| `target_publication_days` | 公告发布目标天数 | `30` | 30天内完成拍卖公告 |
| `target_judgement_hearing_set_days` | Judgment Hearing 安排目标天数 | `120` | 120天内确定判决听证日期 |
| `target_judgement_days` | Judgment 完成目标天数 | `30` | 30天内完成判决 |
| `target_sale_date_set_days` | 拍卖日期确定目标天数 | `30` | 30天内确定拍卖日 |
| `target_final_title_cleared_days` | 最终产权确认目标天数 | `5` | 拍卖后5天内完成最终产权确认 |
| `target_sale_date_held_days` | 拍卖完成目标天数 | `0` | 0天（即设定日当天完成） |

#### Group 4：差异/方差调整（`variance_*`，4列）

> 对应 BPS UI 的 **Variance 面板**。记录 FCL 流程中因 BK/LM/Hold 等暂停事件产生的天数调整量。

| 字段名 | 字段业务含义 | 来源数据 | 计算/推导逻辑 | 数据类型 | 典型取值 | 上游字段 | 下游用途 | 备注 |
|--------|------------|---------|--------------|---------|---------|---------|---------|------|
| `variance_active_bankruptcy` | 活跃破产期间的方差调整天数 | BPS 应用层 | 破产期间 FCL 暂停总天数 | int | `30`, `60`, `0` | — | 从 Target 中扣除，得到调整后期望天数 | ✅ Confirmed |
| `variance_completed_bankruptcy` | 已完结破产的方差天数 | BPS 应用层 | 历史破产事件累计暂停天数 | int | `0`, `90` | — | 历史方差追踪 | ✅ Confirmed |
| `variance_estimated_hold_days` | 预计 Hold 调整天数合计 | BPS 应用层 | 各类 Hold（BK/LM/AOM等）预计延误天数合计 | int | `0`, `30`, `60` | `bpms_dev.sync_loan_foreclosure_hold` | SLA 方差分析 | ✅ Confirmed |
| `variance_bankruptcies` | 该贷款历史破产次数 | BPS 应用层 | 直接写入 | int | `0`, `1`, `2` | — | 风险评估；多次破产=FCL流程更复杂 | ✅ Confirmed |

#### Group 5：竞拍审批（`bid_approval_*`，4列）

> 对应 BPS UI 的 **Bid Approval 面板**。

| 字段名 | 字段业务含义 | 来源数据 | 计算/推导逻辑 | 数据类型 | 典型取值 | 上游字段 | 下游用途 | 备注 |
|--------|------------|---------|--------------|---------|---------|---------|---------|------|
| `bid_approval_status` | 竞拍审批状态 | BPS 应用层 | 直接写入 | varchar | `Approved`, `Pending`, `Rejected` | — | Bid Approval 面板状态展示 | ✅ Confirmed |
| `bid_approval_sale_date` | 竞拍关联的拍卖日期 | BPS 应用层 | 直接写入 | date | `2026-01-15` | `port.basic_data_loan_fcl.fcsale_held_date` | 拍卖日确认 | ✅ Confirmed |
| `bid_approval_bid_amount` | 竞拍出价金额 | ETL | 映射自 `fcbidamount` 或 `fcapprbidprice` | decimal | `180000.00` | `port.basic_data_loan_fcl.fcbidamount` / `fcapprbidprice` | 投资人审批出价 | ✅ Confirmed |
| `bid_approval_loan_resolution_holods` | **贷款处置 Hold 原因** | BPS 应用层 | 直接写入；**⚠️ 列名拼写错误（`holods` 应为 `holds`），已投产，不可轻易修改** | varchar | `BK Hold`, `LM Hold` | — | Hold 原因记录 | 🟡 Strong Inference（拼写错误已MCP实测确认） |

#### Group 6：汇总摘要（`summary_*`，16列）

> 对应 BPS UI 的 **Summary 面板**，含 FCL 当前状态、律师信息、关键效率指标等。

| 字段名 | 字段业务含义 | 来源数据 | 计算/推导逻辑 | 数据类型 | 典型取值 | 上游字段 | 下游用途 | 备注 |
|--------|------------|---------|--------------|---------|---------|---------|---------|------|
| `summary_servicer_number` | Servicer 内部编号 | BPS 应用层 | 直接写入 | int | `1`, `2` | — | Servicer 标识辅助字段 | ✅ Confirmed |
| `summary_foreclosure_status` | **FCL 当前状态**（Servicer 状态描述） | ETL | 映射自 `fcremovaldesc` / `activefcflag` / `fcresults` | varchar | Newrez: `Active Foreclosure` / `Closed Foreclosure:Process Complete`；Carrington: `1. First Legal Pending` / `5. Sales Held` | `port.basic_data_loan_fcl.fcremovaldesc` | BPS Summary 面板首要展示字段 | ✅ Confirmed（实测取值已确认） |
| `summary_completed_foreclosure` | FCL 是否已完结 | ETL | 推断自 `fcresults` / `fcremovaldate` | varchar | `Foreclosure Complete`, `null` | `port.basic_data_loan_fcl.fcresults` | 完结 FCL 标志 | ✅ Confirmed |
| `summary_foreclosure_bid_amount` | FCL 出价金额（投资人口径） | ETL | 映射自 `fcbidamount` / `fcapprbidprice` | decimal | `180000.00` | `port.basic_data_loan_fcl.fcbidamount` | 投资人出价审批参考 | ✅ Confirmed |
| `summary_srv_fc_bid_amount` | Servicer 上报的 FCL 出价金额 | ETL | 直接映射 | decimal | `178000.00` | — | 与投资人出价的差异对比分析 | ✅ Confirmed |
| `summary_foreclosure_sale_amount` | 实际拍卖成交金额 | ETL | 映射自 `fcsaleamount` | decimal | `175000.00` | `port.basic_data_loan_fcl.fcsaleamount` | 拍卖结果记录；Loss Severity 计算 | ✅ Confirmed |
| `summary_judicial_foreclosure` | 是否司法 FCL（1=司法） | ETL | 映射自 `judicial` | tinyint | `0`（非司法）, `1`（司法） | `port.basic_data_loan_fcl.judicial` | FCL 类型识别（司法/非司法流程差异显著） | ✅ Confirmed |
| `summary_foreclosure_attorney` | FCL 律师名称 | ETL | 映射自 `fcfirm` | varchar | `'ABC Law Firm'` | `port.basic_data_loan_fcl.fcfirm` | 律师信息展示 | ✅ Confirmed |
| `summary_contested_litigation` | 是否有争议诉讼（1=有） | ETL | 映射自 `fccontestedflag` | tinyint | `0`, `1` | `port.basic_data_loan_fcl.fccontestedflag` | 争议贷款标识；法律风险追踪 | ✅ Confirmed |
| `summary_firm` | 律师事务所名称 | ETL | 映射自 `fcfirm` | varchar | `'Smith & Jones LLP'` | `port.basic_data_loan_fcl.fcfirm` | BPS 律师事务所展示 | ✅ Confirmed |
| `summary_type` | FCL 类型文本（与 judicial 配合） | ETL | 映射自 `judicial` 标志 | varchar | `'Judicial'`, `'Non-Judicial'` | `port.basic_data_loan_fcl.judicial` | FCL 类型文本展示 | ✅ Confirmed |
| `summary_sms_days_in_fcl` | SMS系统统计的 FCL 历时天数（Servicer口径） | ETL | 实时计算自 `svc_days_infc` | int | `180`, `365` | `port.basic_data_loan_fcl.svc_days_infc` | Servicer 口径 FCL 历时监控 | ✅ Confirmed |
| `summary_days_in_fcl` | 投资人口径 FCL 历时天数 | ETL | 实时计算自 `daysinfc` | int | `200`, `400` | `port.basic_data_loan_fcl.daysinfc` | FCL 效率监控；SLA 评估基础 | ✅ Confirmed |
| `summary_current_step` | 当前 FCL 步骤 | ETL | 次优先：映射自 `fcstage` | varchar | `'Judgment'`, `'Sale Scheduled'`, `'First Legal'` | `port.basic_data_loan_fcl.fcstage` | BPS 当前进度展示 | ✅ Confirmed |
| `summary_last_step_completed` | 最近完成的 FCL 步骤 | ETL | 映射自 `lastfcstepcompleted` | varchar | `'Service Complete'` | `port.basic_data_loan_fcl.lastfcstepcompleted` | 历史进度追踪 | ✅ Confirmed |
| `summary_last_step_completed_date` | 最近完成步骤的日期 | ETL | 映射自 `lastfcstepcompleteddate` | date | `2025-11-01` | `port.basic_data_loan_fcl.lastfcstepcompleteddate` | 进度时间追踪 | ✅ Confirmed |

#### Group 7：管理字段（8列）

| 字段名 | 字段业务含义 | 数据类型 | DEFAULT | 典型取值 | 备注 |
|--------|------------|---------|---------|---------|------|
| `create_user` | 记录创建用户 | varchar | NULL | `'ETL'`, `'admin'` | 审计追踪 |
| `create_dept` | 记录创建部门 | varchar | NULL | `'Engineering'` | 审计追踪 |
| `create_time` | 记录创建时间 | datetime | NULL | `2026-01-15 10:00:00` | 审计追踪 |
| `update_user` | 最后更新用户 | varchar | NULL | `'ETL'` | 审计追踪 |
| `update_time` | 最后更新时间 | datetime | NULL | `2026-05-28 08:00:00` | 审计追踪 |
| `status` | 记录状态（0=正常） | tinyint NOT NULL | `0` | `0` | 软停用标志 |
| `is_deleted` | 是否软删除（0=未删） | tinyint NOT NULL | `0` | `0` | 软删除标志 |
| `tenant_id` | 租户 ID（多租户架构预留） | bigint | NULL | `1` | 多租户支持 |

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
| FCL Referral 日期 | — | `portfcldaily.fcl_referred_to_attorney_date` | `portshellpointfc.fcreferraldate` | — | — |
| BK 申请日 | — | `portbkdaily.bk_filed_date` | `portshellpointbk.bkfileddate` | — | — |
| MFR 获批日 | — | `portbkdaily.bk_mfr_granted_date` | `portshellpointbk.mfrgranteddate` | — | — |

---

*文档结束 — v4 | 2026-05-28 | AI Agent (Claude Sonnet 4.6)*
