# Doc 27 · 阶段 / 天数 — `bpms.sync_fcl_stage_info` 字段血缘

> **自动生成** —— 改动请编辑 `outputs/fcl_lineage_source.json` 后重跑 `python - < scripts/gen_fcl_lineage.py`，勿手改本文件。


## 文档目的

逐字段追踪 BPS 表 `bpms.sync_fcl_stage_info` 的每个字段：从 Servicer 原始列，经每一张中间表，到最终 BPS 列，并给出每一跳的转换规则与代码出处。

## 目标读者

数据工程师 · 分析师 · 校验人员 · 未来 AI 会话

## 修订历史

| 日期 | 作者 | 版本 | 变更 | 关联 |
|---|---|---|---|---|
| 2026-06-09 | AI Agent | v1 | 初稿：doc 25–30 由 fcl_lineage_source.json 生成（per-field 血缘 + 跳链 + 取数 SQL） | doc 02 · doc 13 · doc 14 |
| 2026-06-09 | AI Agent | v2 | Servicer 分列（Newrez/Carrington/Capecodfive 来源分开） | doc 02 · doc 13 · doc 14 |
| 2026-06-09 | AI Agent | v3 | 非平凡 SQL 加说明 + 计算示例 | doc 02 · doc 13 · doc 14 |
| 2026-06-09 | AI Agent | v4 | 改为每字段竖排卡片，规则写全不省略 | doc 02 · doc 13 · doc 14 |
| 2026-06-09 | AI Agent | v5 | 跳链补 tempfc 行 + 说明 L2/L3 为何不在本分支；字段标题加序号 | doc 02 · doc 13 · doc 14 |
| 2026-06-09 | AI Agent | v6 | 覆盖 BPS sync 表全部列（系统/审计列分组、视图计算列）；每跳加流动顺序 | doc 02 · doc 13 · doc 14 |
| 2026-06-09 | AI Agent | v7 | 为所有字段补中文名/业务含义（DDL 注释 Code-First 提取）；新增修订历史维护 | doc 02 · doc 13 · doc 14 |

## 相关文档

doc 02（ETL 管道，表级）· doc 13/14（字段映射）· doc 25（血缘总览）· 源码 PrefectFlow（见各跳 code）


---

**规范跳链 / canonical hop chain**


`newrez.portnewrezfc` → `tempfc.temp_basic_data_fcl` → `port.basic_data_loan_fcl` → `port.fcl_stage_info` → `bpms.sync_fcl_stage_info`

| # | layer | db | 表 table | role |
|---|---|---|---|---|
| 1 | L0/L1 | MySQL+Redshift | `newrez.portnewrezfc` | Servicer raw |
| 2 | L4·temp | Redshift | `tempfc.temp_basic_data_fcl` | 3-servicer rename-UNION of L1 raw / 三家 servicer 改名 UNION (CREATE_BASIC_FCL, pool:1531-1654) |
| 3 | L4 | Redshift | `port.basic_data_loan_fcl` | canonical FCL fact |
| 4 | L4 | Redshift | `port.fcl_stage_info` | stage classification + day-math (GEN_FCL_STAGE); group/state from port.basic_data_fcl_related |
| 5 | L5 | MySQL bpms | `bpms.sync_fcl_stage_info` | BPS app table (12-FCL_STAGE sync, keeps fctrdt history) |

> `#` 列是序号，不是层号。FCL 事实表 `port.basic_data_loan_fcl` 直接由 L1 各 servicer 原始表构建（在 `tempfc.temp_basic_data_fcl` 中 UNION；CREATE_BASIC_FCL pool:1531-1654），因此 L2 统一日表（`port.basic_data_daily_loan_common`）与 L3 清洗层（`…_clean` / `…_delinq_clean`）按设计不在本分支——它们承载通用+逾期字段，仅经 `group` 维度（doc 27，`basic_data_fcl_related`）与月度 `portmonth` 路径回流。完整 L0–L5 管道见 doc 02。

> code: `pool` = PrefectFlow/flow/basic_data/basic_data_config/basic_data_pool_config.py · `asset` = PrefectFlow/flow/bps/bps_config/asset_managment_config.py · `view` = bpms.biz_data_view_loan_details_foreclosure (SHOW CREATE VIEW)


## 标识 / 主键列

### 1. id 主键  (`bpms.sync_fcl_stage_info.id`)

_自增代理主键。_

**来源 / Source (L1)**
- Newrez: `bpms.sync_fcl_stage_info.id`  （仅 Newrez 提供此明细）

**流动顺序 / Flow:** ①sync_fcl_stage_info
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `bpms.sync_fcl_stage_info.id` — auto-increment PK (BPS app) [asset]

**说明 / Note:** BPS 应用插入时生成；非来源数据。

### 2. fctrdt 报告快照日  (`bpms.sync_fcl_stage_info.fctrdt`)

_每日快照/报告日（=dataasof）。_

**来源 / Source (L1)**
- Newrez: `port.basic_data_loan_fcl.dataasof`  （仅 Newrez 提供此明细）

**流动顺序 / Flow:** ①basic_data_loan_fcl → ②sync_fcl_stage_info
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `port.basic_data_loan_fcl.dataasof` — dataasof → fctrdt
- 2. `bpms.sync_fcl_stage_info.fctrdt` — sync passthrough [asset]

### 3. 投资人贷款 ID  (`bpms.sync_fcl_stage_info.loanid`)

_投资人贷款 ID / servicer 贷款 ID。_

**来源 / Source (L1)**
- Newrez: `newrez.portnewrezfc.loanid`  （仅 Newrez 提供此明细）

**流动顺序 / Flow:** ①portnewrezfc → ②fcl_stage_info → ③sync_fcl_stage_info
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `newrez.portnewrezfc.loanid` — servicer raw
- 2. `port.fcl_stage_info.loanid` — passthrough
- 3. `bpms.sync_fcl_stage_info.loanid` — sync passthrough [asset]

### 4. servicer 服务商  (`bpms.sync_fcl_stage_info.servicer`)

_服务商名。_

**来源 / Source (L1)**
- Newrez: `(per servicer)` · constant 'Newrez'/'Carrington'/'Capecodfive'  （仅 Newrez 提供此明细）

**流动顺序 / Flow:** ①(per → ②sync_fcl_stage_info
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `(per servicer)` · constant 'Newrez'/'Carrington'/'Capecodfive' — constant per UNION branch [pool:1536/1577/1618]
- 2. `bpms.sync_fcl_stage_info.servicer` — sync passthrough [asset]


## 维度（group / judicial / state）

### 5. stage 当前阶段分类  (`bpms.sync_fcl_stage_info.stage`)

_贷款当前阶段分类（waterfall 结果）。_

**来源 / Source (L1)**
- Newrez: `port.basic_data_loan_fcl` · (stage dates)  （仅 Newrez 提供此明细）

**流动顺序 / Flow:** ①basic_data_loan_fcl → ②fcl_stage_info → ③sync_fcl_stage_info
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `port.basic_data_loan_fcl` · (stage dates) — waterfall by first non-null date
- 2. `port.fcl_stage_info.stage` — CASE waterfall: SALE→JUDGEMENT→PUBLICATION→SERVICE→FIRST_LEGAL→REFERRAL→DEMAND [pool:2095-2102]
- 3. `bpms.sync_fcl_stage_info.stage` — sync passthrough [asset:925]

**说明 / Note:** 取值：SALE / JUDGEMENT / PUBLICATION / SERVICE / FIRST_LEGAL / REFERRAL / DEMAND（7 个；prod 快照当前为 REFERRAL/SALE/FIRST_LEGAL/SERVICE/JUDGEMENT）。

### 6. Group 分组（FCL/D120P/D90/REO/P…）  (`bpms.sync_fcl_stage_info.group`)

_用于分桶的逾期/法律分组。_

**来源 / Source (L1)**
- Newrez: `newrez.portnewrezgeneral.delinquency_status_mba`
- Carrington: `carrington.portcarrington.loan_status / fcl_flag`
- Capecodfive: —

**流动顺序 / Flow:** ①basic_data_fcl_related → ②fcl_stage_info → ③sync_fcl_stage_info
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `port.basic_data_fcl_related.delq_status` — CASE mba then days360 fallback 见 sql [pool:1702-1711]
- 2. `port.fcl_stage_info.group` — = r.delq_status (join loanid+dataasof) [pool:2348,2400]
- 3. `bpms.sync_fcl_stage_info.group` — 12-FCL_STAGE sync pass-through [asset:925]

**规则（完整）/ Rule (full):** `fcl_stage_info.group = basic_data_fcl_related.delq_status`。**Newrez**（pool:1702-1711）：`delinquency_status_mba='Full Payoff'`→P、`'REO'`→REO、任意 `'Foreclosure*'`→FCL；否则按 `days360(portnewrezpmt.nextduedate, dataasof)` 分桶：`<30`→C、`<60`→D30、`<90`→D60、`<120`→D90、否则→D120P。**Carrington**（pool:1749-1758）：`loan_status='Foreclosure' 或 fcl_flag='Active'`→FCL、`loan_status IN ('R','REO')`→REO、`IN ('Completed Payoff','Completed Short Sale')`→P；否则对 `date_payment_due` 用同样的 `days360` 分桶。**Capecodfive** 不在 `basic_data_fcl_related` → group 为 `—`。

```sql
group = port.basic_data_fcl_related.delq_status; CASE delinquency_status_mba: 'Full Payoff'→P, 'REO'→REO, Foreclosure*→FCL, ELSE days360(nextduedate,dataasof): <30→C,<60→D30,<90→D60,<120→D90,else→D120P
```
🔎 **说明** delq_status（带入 fcl_stage_info.group）：delinquency_status_mba 为 'Full Payoff'→P、'REO'→REO、任意 'Foreclosure*'→FCL；否则按 days360(nextduedate, dataasof) 分桶：<30→C、<60→D30、<90→D60、<120→D90、否则→D120P。
▶ **示例** 7727004408：delinquency_status_mba='Foreclosure' ⇒ FCL。（逾期路径，示意：nextduedate 距 dataasof 约 100 天 ⇒ days360≈100 ⇒ D90。）

### 7. State 州  (`bpms.sync_fcl_stage_info.state`)

_房产州。_

**来源 / Source (L1)**
- Newrez: `newrez.portnewrezprop.propertystate`
- Carrington: `carrington.portcarrington.property_state`
- Capecodfive: —

**流动顺序 / Flow:** ①basic_data_fcl_related → ②fcl_stage_info → ③sync_fcl_stage_info
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `port.basic_data_fcl_related.propertystate` — direct 直传 [pool:1721]
- 2. `port.fcl_stage_info.state` — = r.propertystate (join) [pool:2350,2401]
- 3. `bpms.sync_fcl_stage_info.state` — sync pass-through [asset:925]

### 8. Judicial 司法(Y/N)  (`bpms.sync_fcl_stage_info.judicial`)

_司法标志（带州级回退）。_

**来源 / Source (L1)**
- Newrez: `newrez.portnewrezfc.judicial`
- Carrington: —
- Capecodfive: —

**流动顺序 / Flow:** ①basic_data_loan_fcl → ②fcl_stage_info → ③sync_fcl_stage_info
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `port.basic_data_loan_fcl.judicial` — normalize cast(int) [pool:2034]
- 2. `port.fcl_stage_info.judicial` — Y/N else state-config fallback 见 sql [pool:2351-2353,2432]
- 3. `bpms.sync_fcl_stage_info.judicial` — sync pass-through [asset:925]

**规则（完整）/ Rule (full):** `fcl_stage_info.judicial = CASE judicial=1→'Y'、0→'N'`。**Newrez** 提供贷款级 `judicial` 标志（pool:1565）。**Carrington / Capecodfive** 事实表中 `judicial=NULL`（pool:1606 / 1647）→ **州级回退**：按房产州关联 `basic_data_judicial_config`，取其 judicial 值（pool:2351-2353，关联 pool:2432）。

```sql
CASE judicial=1→'Y', 0→'N', ELSE config_judicial (port.basic_data_judicial_config keyed by propertystate)
```
🔎 **说明** 由归一化的贷款级 judicial：1→'Y'、0→'N'。若 NULL/空，则回退到州级司法配置（basic_data_judicial_config 按房产州关联）。
▶ **示例** judicial=1 ⇒ 'Y'。无标志的贷款在司法州（如 FL）⇒ 配置 'Y'；在非司法州（如 TX）⇒ 'N'。


## 阶段开始日期

### 9. 催告/Demand 阶段开始日  (`bpms.sync_fcl_stage_info.demand_start_date`)

_阶段开始日期。_

**来源 / Source (L1)**
- Newrez: `newrez.portnewrezfc.demandsentdate`
- Carrington: —
- Capecodfive: —

**流动顺序 / Flow:** ①basic_data_loan_fcl → ②fcl_stage_info → ③sync_fcl_stage_info
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `port.basic_data_loan_fcl.demandsentdate` — source 源
- 2. `port.fcl_stage_info.demand_start_date` — passthrough start date 见 sql [pool:2354-2391]
- 3. `bpms.sync_fcl_stage_info.demand_start_date` — sync passthrough [asset:925]

### 10. 催告/Demand 阶段结束日(窗口)  (`bpms.sync_fcl_stage_info.demand_end_date`)

_阶段窗口结束（= 下一阶段开始日，否则今天）。_

**来源 / Source (L1)**
- Newrez: `newrez.portnewrezfc`  （仅 Newrez 提供此明细）

**流动顺序 / Flow:** ①portnewrezfc → ②basic_data_loan_fcl → ③fcl_stage_info → ④sync_fcl_stage_info
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `newrez.portnewrezfc` — —
- 2. `port.basic_data_loan_fcl` · (stage end) — source 源
- 3. `port.fcl_stage_info.demand_end_date` — stage window end = next stage start / curr_date 见 sql [pool:2049-2076]
- 4. `bpms.sync_fcl_stage_info.demand_end_date` — sync passthrough [asset:925]

### 11. NOI 阶段开始日  (`bpms.sync_fcl_stage_info.noi_start_date`)

_NOI 桶未单独填充（由 DEMAND 覆盖）。_

> ⚠ null_in_build

**来源 / Source (L1)**
- Newrez: `port.fcl_stage_info.noi_start_date`  （仅 Newrez 提供此明细）

**流动顺序 / Flow:** ①fcl_stage_info → ②sync_fcl_stage_info
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `port.fcl_stage_info.noi_start_date` — hardcoded NULL in business_1 [pool:2078-2102]
- 2. `bpms.sync_fcl_stage_info.noi_start_date` — sync passthrough (NULL) [asset:925]

### 12. NOI 阶段结束日(窗口)  (`bpms.sync_fcl_stage_info.noi_end_date`)

_阶段窗口结束（= 下一阶段开始日，否则今天）。_

> ⚠ null_in_build

**来源 / Source (L1)**
- Newrez: `newrez.portnewrezfc`  （仅 Newrez 提供此明细）

**流动顺序 / Flow:** ①portnewrezfc → ②basic_data_loan_fcl → ③fcl_stage_info → ④sync_fcl_stage_info
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `newrez.portnewrezfc` — —
- 2. `port.basic_data_loan_fcl` · (stage end) — source 源
- 3. `port.fcl_stage_info.noi_end_date` — stage window end = next stage start / curr_date 见 sql [pool:2049-2076]
- 4. `bpms.sync_fcl_stage_info.noi_end_date` — sync passthrough [asset:925]

### 13. NOI 阶段已历天数  (`bpms.sync_fcl_stage_info.noi_stage_days`)

_NOI 桶未单独填充（由 DEMAND 覆盖）。_

> ⚠ null_in_build

**来源 / Source (L1)**
- Newrez: `port.fcl_stage_info.noi_stage_days`  （仅 Newrez 提供此明细）

**流动顺序 / Flow:** ①fcl_stage_info → ②sync_fcl_stage_info
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `port.fcl_stage_info.noi_stage_days` — hardcoded NULL in business_1 [pool:2078-2102]
- 2. `bpms.sync_fcl_stage_info.noi_stage_days` — sync passthrough (NULL) [asset:925]

### 14. 转介 阶段开始日  (`bpms.sync_fcl_stage_info.referral_start_date`)

_阶段开始日期。_

**来源 / Source (L1)**
- Newrez: `newrez.portnewrezfc.fcreferraldate`
- Carrington: `carrington.portcarrington.fcl_referral_date`
- Capecodfive: `capecodfive.portcapecodfive_monthly_collections.foreclosure_date_refrd_atty`

**流动顺序 / Flow:** ①basic_data_loan_fcl → ②fcl_stage_info → ③sync_fcl_stage_info
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `port.basic_data_loan_fcl.referral_start_date` — source 源
- 2. `port.fcl_stage_info.referral_start_date` — passthrough start date 见 sql [pool:2354-2391]
- 3. `bpms.sync_fcl_stage_info.referral_start_date` — sync passthrough [asset:925]

### 15. 转介 阶段结束日(窗口)  (`bpms.sync_fcl_stage_info.referral_end_date`)

_阶段窗口结束（= 下一阶段开始日，否则今天）。_

**来源 / Source (L1)**
- Newrez: `newrez.portnewrezfc`  （仅 Newrez 提供此明细）

**流动顺序 / Flow:** ①portnewrezfc → ②basic_data_loan_fcl → ③fcl_stage_info → ④sync_fcl_stage_info
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `newrez.portnewrezfc` — —
- 2. `port.basic_data_loan_fcl` · (stage end) — source 源
- 3. `port.fcl_stage_info.referral_end_date` — stage window end = next stage start / curr_date 见 sql [pool:2049-2076]
- 4. `bpms.sync_fcl_stage_info.referral_end_date` — sync passthrough [asset:925]

### 16. 首次法律 阶段开始日  (`bpms.sync_fcl_stage_info.first_legal_start_date`)

_阶段开始日期。_

**来源 / Source (L1)**
- Newrez: `newrez.portnewrezfc.firstlegaldate`
- Carrington: —
- Capecodfive: `capecodfive.portcapecodfive_monthly_collections.foreclosure_first_legal_date`

**流动顺序 / Flow:** ①basic_data_loan_fcl → ②fcl_stage_info → ③sync_fcl_stage_info
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `port.basic_data_loan_fcl.legal_start_date` — source 源
- 2. `port.fcl_stage_info.first_legal_start_date` — passthrough start date 见 sql [pool:2354-2391]
- 3. `bpms.sync_fcl_stage_info.first_legal_start_date` — sync passthrough [asset:925]

### 17. 首次法律 阶段结束日(窗口)  (`bpms.sync_fcl_stage_info.first_legal_end_date`)

_阶段窗口结束（= 下一阶段开始日，否则今天）。_

**来源 / Source (L1)**
- Newrez: `newrez.portnewrezfc`  （仅 Newrez 提供此明细）

**流动顺序 / Flow:** ①portnewrezfc → ②basic_data_loan_fcl → ③fcl_stage_info → ④sync_fcl_stage_info
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `newrez.portnewrezfc` — —
- 2. `port.basic_data_loan_fcl` · (stage end) — source 源
- 3. `port.fcl_stage_info.first_legal_end_date` — stage window end = next stage start / curr_date 见 sql [pool:2049-2076]
- 4. `bpms.sync_fcl_stage_info.first_legal_end_date` — sync passthrough [asset:925]

### 18. 首次法律日(首见追踪)  (`bpms.sync_fcl_stage_info.first_legal_date_history`)

_首次法律日的 ETL 首见追踪。_

**来源 / Source (L1)**
- Newrez: `newrez.portnewrezfc.firstlegaldate`  （仅 Newrez 提供此明细）

**流动顺序 / Flow:** ①portnewrezfc → ②basic_data_loan_fcl → ③fcl_stage_info → ④sync_fcl_stage_info
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `newrez.portnewrezfc.firstlegaldate` — servicer raw 原始
- 2. `port.basic_data_loan_fcl.legal_start_date` — source 源
- 3. `port.fcl_stage_info.first_legal_date_history` — ETL tracking (first-seen) 见 sql [pool:2058-2066]
- 4. `bpms.sync_fcl_stage_info.first_legal_date_history` — sync passthrough [asset:925]

### 19. 送达 阶段开始日  (`bpms.sync_fcl_stage_info.service_start_date`)

_阶段开始日期。_

**来源 / Source (L1)**
- Newrez: `newrez.portnewrezfc.servicecompletedate`
- Carrington: —
- Capecodfive: `capecodfive.portcapecodfive_monthly_collections.foreclosure_service_date`

**流动顺序 / Flow:** ①basic_data_loan_fcl → ②fcl_stage_info → ③sync_fcl_stage_info
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `port.basic_data_loan_fcl.service_start_date` — source 源
- 2. `port.fcl_stage_info.service_start_date` — passthrough start date 见 sql [pool:2354-2391]
- 3. `bpms.sync_fcl_stage_info.service_start_date` — sync passthrough [asset:925]

### 20. 送达 阶段结束日(窗口)  (`bpms.sync_fcl_stage_info.service_end_date`)

_阶段窗口结束（= 下一阶段开始日，否则今天）。_

**来源 / Source (L1)**
- Newrez: `newrez.portnewrezfc`  （仅 Newrez 提供此明细）

**流动顺序 / Flow:** ①portnewrezfc → ②basic_data_loan_fcl → ③fcl_stage_info → ④sync_fcl_stage_info
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `newrez.portnewrezfc` — —
- 2. `port.basic_data_loan_fcl` · (stage end) — source 源
- 3. `port.fcl_stage_info.service_end_date` — stage window end = next stage start / curr_date 见 sql [pool:2049-2076]
- 4. `bpms.sync_fcl_stage_info.service_end_date` — sync passthrough [asset:925]

### 21. 公告 阶段开始日  (`bpms.sync_fcl_stage_info.publication_start_date`)

_Publication 对这些 servicer 未填充。_

> ⚠ null_in_build

**来源 / Source (L1)**
- Newrez: `port.fcl_stage_info.publication_start_date`  （仅 Newrez 提供此明细）

**流动顺序 / Flow:** ①fcl_stage_info → ②sync_fcl_stage_info
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `port.fcl_stage_info.publication_start_date` — hardcoded NULL in business_1 [pool:2078-2102]
- 2. `bpms.sync_fcl_stage_info.publication_start_date` — sync passthrough (NULL) [asset:925]

### 22. 公告 阶段结束日(窗口)  (`bpms.sync_fcl_stage_info.publication_end_date`)

_阶段窗口结束（= 下一阶段开始日，否则今天）。_

> ⚠ null_in_build

**来源 / Source (L1)**
- Newrez: `newrez.portnewrezfc`  （仅 Newrez 提供此明细）

**流动顺序 / Flow:** ①portnewrezfc → ②basic_data_loan_fcl → ③fcl_stage_info → ④sync_fcl_stage_info
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `newrez.portnewrezfc` — —
- 2. `port.basic_data_loan_fcl` · (stage end) — source 源
- 3. `port.fcl_stage_info.publication_end_date` — stage window end = next stage start / curr_date 见 sql [pool:2049-2076]
- 4. `bpms.sync_fcl_stage_info.publication_end_date` — sync passthrough [asset:925]

### 23. 公告 阶段已历天数  (`bpms.sync_fcl_stage_info.publication_stage_days`)

_Publication 对这些 servicer 未填充。_

> ⚠ null_in_build

**来源 / Source (L1)**
- Newrez: `port.fcl_stage_info.publication_stage_days`  （仅 Newrez 提供此明细）

**流动顺序 / Flow:** ①fcl_stage_info → ②sync_fcl_stage_info
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `port.fcl_stage_info.publication_stage_days` — hardcoded NULL in business_1 [pool:2078-2102]
- 2. `bpms.sync_fcl_stage_info.publication_stage_days` — sync passthrough (NULL) [asset:925]

### 24. 判决 阶段开始日  (`bpms.sync_fcl_stage_info.judgement_start_date`)

_阶段开始日期。_

**来源 / Source (L1)**
- Newrez: `newrez.portnewrezfc.fcjudgmenthearingscheduled`
- Carrington: —
- Capecodfive: —

**流动顺序 / Flow:** ①basic_data_loan_fcl → ②fcl_stage_info → ③sync_fcl_stage_info
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `port.basic_data_loan_fcl.fcjudgment_hearing_scheduled` — source 源
- 2. `port.fcl_stage_info.judgement_start_date` — passthrough start date 见 sql [pool:2354-2391]
- 3. `bpms.sync_fcl_stage_info.judgement_start_date` — sync passthrough [asset:925]

### 25. 判决 阶段结束日(窗口)  (`bpms.sync_fcl_stage_info.judgement_end_date`)

_阶段窗口结束（= 下一阶段开始日，否则今天）。_

**来源 / Source (L1)**
- Newrez: `newrez.portnewrezfc`  （仅 Newrez 提供此明细）

**流动顺序 / Flow:** ①portnewrezfc → ②basic_data_loan_fcl → ③fcl_stage_info → ④sync_fcl_stage_info
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `newrez.portnewrezfc` — —
- 2. `port.basic_data_loan_fcl` · (stage end) — source 源
- 3. `port.fcl_stage_info.judgement_end_date` — stage window end = next stage start / curr_date 见 sql [pool:2049-2076]
- 4. `bpms.sync_fcl_stage_info.judgement_end_date` — sync passthrough [asset:925]

### 26. 拍卖 阶段开始日  (`bpms.sync_fcl_stage_info.sale_start_date`)

_阶段开始日期。_

**来源 / Source (L1)**
- Newrez: `newrez.portnewrezfc.fcscheduledsaledate`
- Carrington: `carrington.portcarrington.fcl_scheduled_sale_date`
- Capecodfive: `capecodfive.portcapecodfive_monthly_collections.foreclosure_date_sale_scheduled`

**流动顺序 / Flow:** ①basic_data_loan_fcl → ②fcl_stage_info → ③sync_fcl_stage_info
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `port.basic_data_loan_fcl.fcscheduled_sale_date` — source 源
- 2. `port.fcl_stage_info.sale_start_date` — passthrough start date 见 sql [pool:2354-2391]
- 3. `bpms.sync_fcl_stage_info.sale_start_date` — sync passthrough [asset:925]

### 27. 拍卖 阶段结束日(窗口)  (`bpms.sync_fcl_stage_info.sale_end_date`)

_阶段窗口结束（= 下一阶段开始日，否则今天）。_

**来源 / Source (L1)**
- Newrez: `newrez.portnewrezfc`  （仅 Newrez 提供此明细）

**流动顺序 / Flow:** ①portnewrezfc → ②basic_data_loan_fcl → ③fcl_stage_info → ④sync_fcl_stage_info
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `newrez.portnewrezfc` — —
- 2. `port.basic_data_loan_fcl` · (stage end) — source 源
- 3. `port.fcl_stage_info.sale_end_date` — stage window end = next stage start / curr_date 见 sql [pool:2049-2076]
- 4. `bpms.sync_fcl_stage_info.sale_end_date` — sync passthrough [asset:925]


## 阶段天数

### 28. 催告/Demand 阶段已历天数  (`bpms.sync_fcl_stage_info.demand_stage_days`)

_阶段内含端点已历天数。_

**来源 / Source (L1)**
- Newrez: `newrez.portnewrezfc`  （仅 Newrez 提供此明细）

**流动顺序 / Flow:** ①portnewrezfc → ②basic_data_loan_fcl → ③fcl_stage_info → ④sync_fcl_stage_info
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `newrez.portnewrezfc` — —
- 2. `port.basic_data_loan_fcl` · (stage dates) — source 源
- 3. `port.fcl_stage_info.demand_stage_days` — datediff+1 (inclusive) 见 sql [pool:2040-2076]
- 4. `bpms.sync_fcl_stage_info.demand_stage_days` — sync passthrough [asset:925]

```sql
datediff(day, {stage}_start, {next_stage}_start or curr_date) + 1; e.g. referral_end=legal_start_date, first_legal_end=service_start_date, service_end=judgment_available_date
```
🔎 **说明** 阶段内含端点天数：datediff(day, {stage}_start, end)+1，其中 end = 下一阶段开始日（referral_end=首次法律日；first_legal_end=送达日；service_end=判决可得日），若未结束则取今天 curr_date。
▶ **示例** 7727004408：referral_start 2024-03-08，下一阶段（首次法律）2025-07-28 ⇒ referral_stage_days = datediff+1 = 508（与 prod 一致）。

### 29. 催告/Demand 阶段内 LM 天数  (`bpms.sync_fcl_stage_info.demand_in_lm_days`)

_阶段内与开启 LM 周期重叠天数。_

**来源 / Source (L1)**
- Newrez: `newrez.portnewrezfc`  （仅 Newrez 提供此明细）

**流动顺序 / Flow:** ①portnewrezfc → ②basic_data_loan_fcl → ③fcl_stage_info → ④sync_fcl_stage_info
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `newrez.portnewrezfc` — —
- 2. `port.basic_data_loan_fcl` · (LM cycle) — source 源
- 3. `port.fcl_stage_info.demand_in_lm_days` — interval overlap (LM) 见 sql [pool:2246-2330]
- 4. `bpms.sync_fcl_stage_info.demand_in_lm_days` — sync passthrough [asset:925]

```sql
in_lm = datediff(greatest(stage_start, cycle_opened_date), least(stage_end, coalesce(cycle_closed_date,curr_date))) + 1; only open cycles; pivoted per stage with max()
```
🔎 **说明** 阶段窗口与「进行中」LM 周期的重叠天数：datediff(greatest(stage_start, cycle_opened), least(stage_end, coalesce(cycle_closed, 今天)))+1；仅开启周期；按阶段计算后取 max()。
▶ **示例** 7727000569：Service 阶段与开启 LM 周期重叠 ⇒ service_in_lm_days = 185（prod）。

### 30. 催告/Demand 阶段内 Hold 天数  (`bpms.sync_fcl_stage_info.demand_on_hold_days`)

_阶段内与开启 Hold 重叠天数。_

**来源 / Source (L1)**
- Newrez: `newrez.portnewrezfc`  （仅 Newrez 提供此明细）

**流动顺序 / Flow:** ①portnewrezfc → ②basic_data_loan_fcl → ③fcl_stage_info → ④sync_fcl_stage_info
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `newrez.portnewrezfc` — —
- 2. `port.basic_data_loan_fcl.fchold1..3` — source 源
- 3. `port.fcl_stage_info.demand_on_hold_days` — interval overlap (Hold) 见 sql [pool:2215-2297]
- 4. `bpms.sync_fcl_stage_info.demand_on_hold_days` — sync passthrough [asset:925]

```sql
on_hold = datediff(greatest(stage_start, hold_start), least(stage_end, coalesce(hold_end,curr_date))) + 1; only open holds (fchold1..3 of basic_data_loan_fcl); pivoted per stage
```
🔎 **说明** 阶段窗口与「进行中」Hold（basic_data_loan_fcl 的 fchold1..3）的重叠天数：datediff(greatest(stage_start, hold_start), least(stage_end, coalesce(hold_end, 今天)))+1；按阶段后取 max()。
▶ **示例** 7727000569：Service 阶段 ∩ 开启 Hold ⇒ service_on_hold_days = 87（prod）。

### 31. NOI 阶段内 LM 天数  (`bpms.sync_fcl_stage_info.noi_in_lm_days`)

_阶段内与开启 LM 周期重叠天数。_

**来源 / Source (L1)**
- Newrez: `newrez.portnewrezfc`  （仅 Newrez 提供此明细）

**流动顺序 / Flow:** ①portnewrezfc → ②basic_data_loan_fcl → ③fcl_stage_info → ④sync_fcl_stage_info
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `newrez.portnewrezfc` — —
- 2. `port.basic_data_loan_fcl` · (LM cycle) — source 源
- 3. `port.fcl_stage_info.noi_in_lm_days` — interval overlap (LM) 见 sql [pool:2246-2330]
- 4. `bpms.sync_fcl_stage_info.noi_in_lm_days` — sync passthrough [asset:925]

```sql
in_lm = datediff(greatest(stage_start, cycle_opened_date), least(stage_end, coalesce(cycle_closed_date,curr_date))) + 1; only open cycles; pivoted per stage with max()
```
🔎 **说明** 阶段窗口与「进行中」LM 周期的重叠天数：datediff(greatest(stage_start, cycle_opened), least(stage_end, coalesce(cycle_closed, 今天)))+1；仅开启周期；按阶段计算后取 max()。
▶ **示例** 7727000569：Service 阶段与开启 LM 周期重叠 ⇒ service_in_lm_days = 185（prod）。

### 32. NOI 阶段内 Hold 天数  (`bpms.sync_fcl_stage_info.noi_on_hold_days`)

_阶段内与开启 Hold 重叠天数。_

**来源 / Source (L1)**
- Newrez: `newrez.portnewrezfc`  （仅 Newrez 提供此明细）

**流动顺序 / Flow:** ①portnewrezfc → ②basic_data_loan_fcl → ③fcl_stage_info → ④sync_fcl_stage_info
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `newrez.portnewrezfc` — —
- 2. `port.basic_data_loan_fcl.fchold1..3` — source 源
- 3. `port.fcl_stage_info.noi_on_hold_days` — interval overlap (Hold) 见 sql [pool:2215-2297]
- 4. `bpms.sync_fcl_stage_info.noi_on_hold_days` — sync passthrough [asset:925]

```sql
on_hold = datediff(greatest(stage_start, hold_start), least(stage_end, coalesce(hold_end,curr_date))) + 1; only open holds (fchold1..3 of basic_data_loan_fcl); pivoted per stage
```
🔎 **说明** 阶段窗口与「进行中」Hold（basic_data_loan_fcl 的 fchold1..3）的重叠天数：datediff(greatest(stage_start, hold_start), least(stage_end, coalesce(hold_end, 今天)))+1；按阶段后取 max()。
▶ **示例** 7727000569：Service 阶段 ∩ 开启 Hold ⇒ service_on_hold_days = 87（prod）。

### 33. 转介 阶段已历天数  (`bpms.sync_fcl_stage_info.referral_stage_days`)

_阶段内含端点已历天数。_

**来源 / Source (L1)**
- Newrez: `newrez.portnewrezfc`  （仅 Newrez 提供此明细）

**流动顺序 / Flow:** ①portnewrezfc → ②basic_data_loan_fcl → ③fcl_stage_info → ④sync_fcl_stage_info
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `newrez.portnewrezfc` — —
- 2. `port.basic_data_loan_fcl` · (stage dates) — source 源
- 3. `port.fcl_stage_info.referral_stage_days` — datediff+1 (inclusive) 见 sql [pool:2040-2076]
- 4. `bpms.sync_fcl_stage_info.referral_stage_days` — sync passthrough [asset:925]

```sql
datediff(day, {stage}_start, {next_stage}_start or curr_date) + 1; e.g. referral_end=legal_start_date, first_legal_end=service_start_date, service_end=judgment_available_date
```
🔎 **说明** 阶段内含端点天数：datediff(day, {stage}_start, end)+1，其中 end = 下一阶段开始日（referral_end=首次法律日；first_legal_end=送达日；service_end=判决可得日），若未结束则取今天 curr_date。
▶ **示例** 7727004408：referral_start 2024-03-08，下一阶段（首次法律）2025-07-28 ⇒ referral_stage_days = datediff+1 = 508（与 prod 一致）。

### 34. 转介 阶段内 LM 天数  (`bpms.sync_fcl_stage_info.referral_in_lm_days`)

_阶段内与开启 LM 周期重叠天数。_

**来源 / Source (L1)**
- Newrez: `newrez.portnewrezfc`  （仅 Newrez 提供此明细）

**流动顺序 / Flow:** ①portnewrezfc → ②basic_data_loan_fcl → ③fcl_stage_info → ④sync_fcl_stage_info
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `newrez.portnewrezfc` — —
- 2. `port.basic_data_loan_fcl` · (LM cycle) — source 源
- 3. `port.fcl_stage_info.referral_in_lm_days` — interval overlap (LM) 见 sql [pool:2246-2330]
- 4. `bpms.sync_fcl_stage_info.referral_in_lm_days` — sync passthrough [asset:925]

```sql
in_lm = datediff(greatest(stage_start, cycle_opened_date), least(stage_end, coalesce(cycle_closed_date,curr_date))) + 1; only open cycles; pivoted per stage with max()
```
🔎 **说明** 阶段窗口与「进行中」LM 周期的重叠天数：datediff(greatest(stage_start, cycle_opened), least(stage_end, coalesce(cycle_closed, 今天)))+1；仅开启周期；按阶段计算后取 max()。
▶ **示例** 7727000569：Service 阶段与开启 LM 周期重叠 ⇒ service_in_lm_days = 185（prod）。

### 35. 转介 阶段内 Hold 天数  (`bpms.sync_fcl_stage_info.referral_on_hold_days`)

_阶段内与开启 Hold 重叠天数。_

**来源 / Source (L1)**
- Newrez: `newrez.portnewrezfc`  （仅 Newrez 提供此明细）

**流动顺序 / Flow:** ①portnewrezfc → ②basic_data_loan_fcl → ③fcl_stage_info → ④sync_fcl_stage_info
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `newrez.portnewrezfc` — —
- 2. `port.basic_data_loan_fcl.fchold1..3` — source 源
- 3. `port.fcl_stage_info.referral_on_hold_days` — interval overlap (Hold) 见 sql [pool:2215-2297]
- 4. `bpms.sync_fcl_stage_info.referral_on_hold_days` — sync passthrough [asset:925]

```sql
on_hold = datediff(greatest(stage_start, hold_start), least(stage_end, coalesce(hold_end,curr_date))) + 1; only open holds (fchold1..3 of basic_data_loan_fcl); pivoted per stage
```
🔎 **说明** 阶段窗口与「进行中」Hold（basic_data_loan_fcl 的 fchold1..3）的重叠天数：datediff(greatest(stage_start, hold_start), least(stage_end, coalesce(hold_end, 今天)))+1；按阶段后取 max()。
▶ **示例** 7727000569：Service 阶段 ∩ 开启 Hold ⇒ service_on_hold_days = 87（prod）。

### 36. 首次法律 阶段已历天数  (`bpms.sync_fcl_stage_info.first_legal_stage_days`)

_阶段内含端点已历天数。_

**来源 / Source (L1)**
- Newrez: `newrez.portnewrezfc`  （仅 Newrez 提供此明细）

**流动顺序 / Flow:** ①portnewrezfc → ②basic_data_loan_fcl → ③fcl_stage_info → ④sync_fcl_stage_info
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `newrez.portnewrezfc` — —
- 2. `port.basic_data_loan_fcl` · (stage dates) — source 源
- 3. `port.fcl_stage_info.first_legal_stage_days` — datediff+1 (inclusive) 见 sql [pool:2040-2076]
- 4. `bpms.sync_fcl_stage_info.first_legal_stage_days` — sync passthrough [asset:925]

```sql
datediff(day, {stage}_start, {next_stage}_start or curr_date) + 1; e.g. referral_end=legal_start_date, first_legal_end=service_start_date, service_end=judgment_available_date
```
🔎 **说明** 阶段内含端点天数：datediff(day, {stage}_start, end)+1，其中 end = 下一阶段开始日（referral_end=首次法律日；first_legal_end=送达日；service_end=判决可得日），若未结束则取今天 curr_date。
▶ **示例** 7727004408：referral_start 2024-03-08，下一阶段（首次法律）2025-07-28 ⇒ referral_stage_days = datediff+1 = 508（与 prod 一致）。

### 37. 首次法律 阶段内 LM 天数  (`bpms.sync_fcl_stage_info.first_legal_in_lm_days`)

_阶段内与开启 LM 周期重叠天数。_

**来源 / Source (L1)**
- Newrez: `newrez.portnewrezfc`  （仅 Newrez 提供此明细）

**流动顺序 / Flow:** ①portnewrezfc → ②basic_data_loan_fcl → ③fcl_stage_info → ④sync_fcl_stage_info
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `newrez.portnewrezfc` — —
- 2. `port.basic_data_loan_fcl` · (LM cycle) — source 源
- 3. `port.fcl_stage_info.first_legal_in_lm_days` — interval overlap (LM) 见 sql [pool:2246-2330]
- 4. `bpms.sync_fcl_stage_info.first_legal_in_lm_days` — sync passthrough [asset:925]

```sql
in_lm = datediff(greatest(stage_start, cycle_opened_date), least(stage_end, coalesce(cycle_closed_date,curr_date))) + 1; only open cycles; pivoted per stage with max()
```
🔎 **说明** 阶段窗口与「进行中」LM 周期的重叠天数：datediff(greatest(stage_start, cycle_opened), least(stage_end, coalesce(cycle_closed, 今天)))+1；仅开启周期；按阶段计算后取 max()。
▶ **示例** 7727000569：Service 阶段与开启 LM 周期重叠 ⇒ service_in_lm_days = 185（prod）。

### 38. 首次法律 阶段内 Hold 天数  (`bpms.sync_fcl_stage_info.first_legal_on_hold_days`)

_阶段内与开启 Hold 重叠天数。_

**来源 / Source (L1)**
- Newrez: `newrez.portnewrezfc`  （仅 Newrez 提供此明细）

**流动顺序 / Flow:** ①portnewrezfc → ②basic_data_loan_fcl → ③fcl_stage_info → ④sync_fcl_stage_info
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `newrez.portnewrezfc` — —
- 2. `port.basic_data_loan_fcl.fchold1..3` — source 源
- 3. `port.fcl_stage_info.first_legal_on_hold_days` — interval overlap (Hold) 见 sql [pool:2215-2297]
- 4. `bpms.sync_fcl_stage_info.first_legal_on_hold_days` — sync passthrough [asset:925]

```sql
on_hold = datediff(greatest(stage_start, hold_start), least(stage_end, coalesce(hold_end,curr_date))) + 1; only open holds (fchold1..3 of basic_data_loan_fcl); pivoted per stage
```
🔎 **说明** 阶段窗口与「进行中」Hold（basic_data_loan_fcl 的 fchold1..3）的重叠天数：datediff(greatest(stage_start, hold_start), least(stage_end, coalesce(hold_end, 今天)))+1；按阶段后取 max()。
▶ **示例** 7727000569：Service 阶段 ∩ 开启 Hold ⇒ service_on_hold_days = 87（prod）。

### 39. 送达 阶段已历天数  (`bpms.sync_fcl_stage_info.service_stage_days`)

_阶段内含端点已历天数。_

**来源 / Source (L1)**
- Newrez: `newrez.portnewrezfc`  （仅 Newrez 提供此明细）

**流动顺序 / Flow:** ①portnewrezfc → ②basic_data_loan_fcl → ③fcl_stage_info → ④sync_fcl_stage_info
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `newrez.portnewrezfc` — —
- 2. `port.basic_data_loan_fcl` · (stage dates) — source 源
- 3. `port.fcl_stage_info.service_stage_days` — datediff+1 (inclusive) 见 sql [pool:2040-2076]
- 4. `bpms.sync_fcl_stage_info.service_stage_days` — sync passthrough [asset:925]

```sql
datediff(day, {stage}_start, {next_stage}_start or curr_date) + 1; e.g. referral_end=legal_start_date, first_legal_end=service_start_date, service_end=judgment_available_date
```
🔎 **说明** 阶段内含端点天数：datediff(day, {stage}_start, end)+1，其中 end = 下一阶段开始日（referral_end=首次法律日；first_legal_end=送达日；service_end=判决可得日），若未结束则取今天 curr_date。
▶ **示例** 7727004408：referral_start 2024-03-08，下一阶段（首次法律）2025-07-28 ⇒ referral_stage_days = datediff+1 = 508（与 prod 一致）。

### 40. 送达 阶段内 LM 天数  (`bpms.sync_fcl_stage_info.service_in_lm_days`)

_阶段内与开启 LM 周期重叠天数。_

**来源 / Source (L1)**
- Newrez: `newrez.portnewrezfc`  （仅 Newrez 提供此明细）

**流动顺序 / Flow:** ①portnewrezfc → ②basic_data_loan_fcl → ③fcl_stage_info → ④sync_fcl_stage_info
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `newrez.portnewrezfc` — —
- 2. `port.basic_data_loan_fcl` · (LM cycle) — source 源
- 3. `port.fcl_stage_info.service_in_lm_days` — interval overlap (LM) 见 sql [pool:2246-2330]
- 4. `bpms.sync_fcl_stage_info.service_in_lm_days` — sync passthrough [asset:925]

```sql
in_lm = datediff(greatest(stage_start, cycle_opened_date), least(stage_end, coalesce(cycle_closed_date,curr_date))) + 1; only open cycles; pivoted per stage with max()
```
🔎 **说明** 阶段窗口与「进行中」LM 周期的重叠天数：datediff(greatest(stage_start, cycle_opened), least(stage_end, coalesce(cycle_closed, 今天)))+1；仅开启周期；按阶段计算后取 max()。
▶ **示例** 7727000569：Service 阶段与开启 LM 周期重叠 ⇒ service_in_lm_days = 185（prod）。

### 41. 送达 阶段内 Hold 天数  (`bpms.sync_fcl_stage_info.service_on_hold_days`)

_阶段内与开启 Hold 重叠天数。_

**来源 / Source (L1)**
- Newrez: `newrez.portnewrezfc`  （仅 Newrez 提供此明细）

**流动顺序 / Flow:** ①portnewrezfc → ②basic_data_loan_fcl → ③fcl_stage_info → ④sync_fcl_stage_info
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `newrez.portnewrezfc` — —
- 2. `port.basic_data_loan_fcl.fchold1..3` — source 源
- 3. `port.fcl_stage_info.service_on_hold_days` — interval overlap (Hold) 见 sql [pool:2215-2297]
- 4. `bpms.sync_fcl_stage_info.service_on_hold_days` — sync passthrough [asset:925]

```sql
on_hold = datediff(greatest(stage_start, hold_start), least(stage_end, coalesce(hold_end,curr_date))) + 1; only open holds (fchold1..3 of basic_data_loan_fcl); pivoted per stage
```
🔎 **说明** 阶段窗口与「进行中」Hold（basic_data_loan_fcl 的 fchold1..3）的重叠天数：datediff(greatest(stage_start, hold_start), least(stage_end, coalesce(hold_end, 今天)))+1；按阶段后取 max()。
▶ **示例** 7727000569：Service 阶段 ∩ 开启 Hold ⇒ service_on_hold_days = 87（prod）。

### 42. 公告 阶段内 LM 天数  (`bpms.sync_fcl_stage_info.publication_in_lm_days`)

_阶段内与开启 LM 周期重叠天数。_

**来源 / Source (L1)**
- Newrez: `newrez.portnewrezfc`  （仅 Newrez 提供此明细）

**流动顺序 / Flow:** ①portnewrezfc → ②basic_data_loan_fcl → ③fcl_stage_info → ④sync_fcl_stage_info
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `newrez.portnewrezfc` — —
- 2. `port.basic_data_loan_fcl` · (LM cycle) — source 源
- 3. `port.fcl_stage_info.publication_in_lm_days` — interval overlap (LM) 见 sql [pool:2246-2330]
- 4. `bpms.sync_fcl_stage_info.publication_in_lm_days` — sync passthrough [asset:925]

```sql
in_lm = datediff(greatest(stage_start, cycle_opened_date), least(stage_end, coalesce(cycle_closed_date,curr_date))) + 1; only open cycles; pivoted per stage with max()
```
🔎 **说明** 阶段窗口与「进行中」LM 周期的重叠天数：datediff(greatest(stage_start, cycle_opened), least(stage_end, coalesce(cycle_closed, 今天)))+1；仅开启周期；按阶段计算后取 max()。
▶ **示例** 7727000569：Service 阶段与开启 LM 周期重叠 ⇒ service_in_lm_days = 185（prod）。

### 43. 公告 阶段内 Hold 天数  (`bpms.sync_fcl_stage_info.publication_on_hold_days`)

_阶段内与开启 Hold 重叠天数。_

**来源 / Source (L1)**
- Newrez: `newrez.portnewrezfc`  （仅 Newrez 提供此明细）

**流动顺序 / Flow:** ①portnewrezfc → ②basic_data_loan_fcl → ③fcl_stage_info → ④sync_fcl_stage_info
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `newrez.portnewrezfc` — —
- 2. `port.basic_data_loan_fcl.fchold1..3` — source 源
- 3. `port.fcl_stage_info.publication_on_hold_days` — interval overlap (Hold) 见 sql [pool:2215-2297]
- 4. `bpms.sync_fcl_stage_info.publication_on_hold_days` — sync passthrough [asset:925]

```sql
on_hold = datediff(greatest(stage_start, hold_start), least(stage_end, coalesce(hold_end,curr_date))) + 1; only open holds (fchold1..3 of basic_data_loan_fcl); pivoted per stage
```
🔎 **说明** 阶段窗口与「进行中」Hold（basic_data_loan_fcl 的 fchold1..3）的重叠天数：datediff(greatest(stage_start, hold_start), least(stage_end, coalesce(hold_end, 今天)))+1；按阶段后取 max()。
▶ **示例** 7727000569：Service 阶段 ∩ 开启 Hold ⇒ service_on_hold_days = 87（prod）。

### 44. 距判决倒计天数  (`bpms.sync_fcl_stage_info.to_judgement_days`)

_距排定判决/拍卖的倒计天数。_

**来源 / Source (L1)**
- Newrez: `newrez.portnewrezfc.fcjudgmenthearingscheduled`  （仅 Newrez 提供此明细）

**流动顺序 / Flow:** ①portnewrezfc → ②basic_data_loan_fcl → ③fcl_stage_info → ④sync_fcl_stage_info
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `newrez.portnewrezfc.fcjudgmenthearingscheduled` — servicer raw 原始
- 2. `port.basic_data_loan_fcl.fcjudgment_hearing_scheduled` — source 源
- 3. `port.fcl_stage_info.to_judgement_days` — countdown (no +1, floored 0) 见 sql [pool:2085-2093]
- 4. `bpms.sync_fcl_stage_info.to_judgement_days` — sync passthrough [asset:925]

```sql
CASE WHEN date IS NULL THEN null WHEN date>=curr_date THEN datediff(day,curr_date,date) ELSE 0 END  (no +1; floored at 0 once past)
```
🔎 **说明** 距排定日的倒计天数：日期为 NULL→NULL；日期 ≥ 今天 → datediff(今天, 日期)（不 +1）；已过期 → 0。
▶ **示例** 7727001179：排定拍卖 2026-06-23 ⇒ to_sale_days = 15（自快照日倒计）。

### 45. 判决 阶段内 LM 天数  (`bpms.sync_fcl_stage_info.judgement_in_lm_days`)

_阶段内与开启 LM 周期重叠天数。_

**来源 / Source (L1)**
- Newrez: `newrez.portnewrezfc`  （仅 Newrez 提供此明细）

**流动顺序 / Flow:** ①portnewrezfc → ②basic_data_loan_fcl → ③fcl_stage_info → ④sync_fcl_stage_info
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `newrez.portnewrezfc` — —
- 2. `port.basic_data_loan_fcl` · (LM cycle) — source 源
- 3. `port.fcl_stage_info.judgement_in_lm_days` — interval overlap (LM) 见 sql [pool:2246-2330]
- 4. `bpms.sync_fcl_stage_info.judgement_in_lm_days` — sync passthrough [asset:925]

```sql
in_lm = datediff(greatest(stage_start, cycle_opened_date), least(stage_end, coalesce(cycle_closed_date,curr_date))) + 1; only open cycles; pivoted per stage with max()
```
🔎 **说明** 阶段窗口与「进行中」LM 周期的重叠天数：datediff(greatest(stage_start, cycle_opened), least(stage_end, coalesce(cycle_closed, 今天)))+1；仅开启周期；按阶段计算后取 max()。
▶ **示例** 7727000569：Service 阶段与开启 LM 周期重叠 ⇒ service_in_lm_days = 185（prod）。

### 46. 判决 阶段内 Hold 天数  (`bpms.sync_fcl_stage_info.judgement_on_hold_days`)

_阶段内与开启 Hold 重叠天数。_

**来源 / Source (L1)**
- Newrez: `newrez.portnewrezfc`  （仅 Newrez 提供此明细）

**流动顺序 / Flow:** ①portnewrezfc → ②basic_data_loan_fcl → ③fcl_stage_info → ④sync_fcl_stage_info
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `newrez.portnewrezfc` — —
- 2. `port.basic_data_loan_fcl.fchold1..3` — source 源
- 3. `port.fcl_stage_info.judgement_on_hold_days` — interval overlap (Hold) 见 sql [pool:2215-2297]
- 4. `bpms.sync_fcl_stage_info.judgement_on_hold_days` — sync passthrough [asset:925]

```sql
on_hold = datediff(greatest(stage_start, hold_start), least(stage_end, coalesce(hold_end,curr_date))) + 1; only open holds (fchold1..3 of basic_data_loan_fcl); pivoted per stage
```
🔎 **说明** 阶段窗口与「进行中」Hold（basic_data_loan_fcl 的 fchold1..3）的重叠天数：datediff(greatest(stage_start, hold_start), least(stage_end, coalesce(hold_end, 今天)))+1；按阶段后取 max()。
▶ **示例** 7727000569：Service 阶段 ∩ 开启 Hold ⇒ service_on_hold_days = 87（prod）。

### 47. 距拍卖倒计天数  (`bpms.sync_fcl_stage_info.to_sale_days`)

_距排定判决/拍卖的倒计天数。_

**来源 / Source (L1)**
- Newrez: `newrez.portnewrezfc.fcscheduledsaledate`  （仅 Newrez 提供此明细）

**流动顺序 / Flow:** ①portnewrezfc → ②basic_data_loan_fcl → ③fcl_stage_info → ④sync_fcl_stage_info
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `newrez.portnewrezfc.fcscheduledsaledate` — servicer raw 原始
- 2. `port.basic_data_loan_fcl.fcscheduled_sale_date` — source 源
- 3. `port.fcl_stage_info.to_sale_days` — countdown (no +1, floored 0) 见 sql [pool:2085-2093]
- 4. `bpms.sync_fcl_stage_info.to_sale_days` — sync passthrough [asset:925]

```sql
CASE WHEN date IS NULL THEN null WHEN date>=curr_date THEN datediff(day,curr_date,date) ELSE 0 END  (no +1; floored at 0 once past)
```
🔎 **说明** 距排定日的倒计天数：日期为 NULL→NULL；日期 ≥ 今天 → datediff(今天, 日期)（不 +1）；已过期 → 0。
▶ **示例** 7727001179：排定拍卖 2026-06-23 ⇒ to_sale_days = 15（自快照日倒计）。

### 48. 拍卖 阶段内 LM 天数  (`bpms.sync_fcl_stage_info.sale_in_lm_days`)

_阶段内与开启 LM 周期重叠天数。_

**来源 / Source (L1)**
- Newrez: `newrez.portnewrezfc`  （仅 Newrez 提供此明细）

**流动顺序 / Flow:** ①portnewrezfc → ②basic_data_loan_fcl → ③fcl_stage_info → ④sync_fcl_stage_info
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `newrez.portnewrezfc` — —
- 2. `port.basic_data_loan_fcl` · (LM cycle) — source 源
- 3. `port.fcl_stage_info.sale_in_lm_days` — interval overlap (LM) 见 sql [pool:2246-2330]
- 4. `bpms.sync_fcl_stage_info.sale_in_lm_days` — sync passthrough [asset:925]

```sql
in_lm = datediff(greatest(stage_start, cycle_opened_date), least(stage_end, coalesce(cycle_closed_date,curr_date))) + 1; only open cycles; pivoted per stage with max()
```
🔎 **说明** 阶段窗口与「进行中」LM 周期的重叠天数：datediff(greatest(stage_start, cycle_opened), least(stage_end, coalesce(cycle_closed, 今天)))+1；仅开启周期；按阶段计算后取 max()。
▶ **示例** 7727000569：Service 阶段与开启 LM 周期重叠 ⇒ service_in_lm_days = 185（prod）。

### 49. 拍卖 阶段内 Hold 天数  (`bpms.sync_fcl_stage_info.sale_on_hold_days`)

_阶段内与开启 Hold 重叠天数。_

**来源 / Source (L1)**
- Newrez: `newrez.portnewrezfc`  （仅 Newrez 提供此明细）

**流动顺序 / Flow:** ①portnewrezfc → ②basic_data_loan_fcl → ③fcl_stage_info → ④sync_fcl_stage_info
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `newrez.portnewrezfc` — —
- 2. `port.basic_data_loan_fcl.fchold1..3` — source 源
- 3. `port.fcl_stage_info.sale_on_hold_days` — interval overlap (Hold) 见 sql [pool:2215-2297]
- 4. `bpms.sync_fcl_stage_info.sale_on_hold_days` — sync passthrough [asset:925]

```sql
on_hold = datediff(greatest(stage_start, hold_start), least(stage_end, coalesce(hold_end,curr_date))) + 1; only open holds (fchold1..3 of basic_data_loan_fcl); pivoted per stage
```
🔎 **说明** 阶段窗口与「进行中」Hold（basic_data_loan_fcl 的 fchold1..3）的重叠天数：datediff(greatest(stage_start, hold_start), least(stage_end, coalesce(hold_end, 今天)))+1；按阶段后取 max()。
▶ **示例** 7727000569：Service 阶段 ∩ 开启 Hold ⇒ service_on_hold_days = 87（prod）。


## 系统 / 审计列

### 50. 系统 / 审计列

_应用/ETL 管理列（非 servicer 来源）。_

**列 / Columns:** `create_time, update_time, create_user, create_dept, update_user, status, is_deleted, tenant_id`

**说明 / Note:** 列：create_time, update_time, create_user, create_dept, update_user, status, is_deleted, tenant_id。tenant_id ← GET_LOAN_TENANT_ID(portfunding ⋈ basic_data_trust_funding，asset:932-936)；create_*/update_* 由 BPS 应用写；is_deleted 视图恒 0；status 应用标志。非 servicer 数据。


> 本文档共 50 个字段。
