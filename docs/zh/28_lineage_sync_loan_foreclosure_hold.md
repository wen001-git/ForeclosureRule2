# Doc 28 · Hold（宽表→长表 unpivot） — `bpms.sync_loan_foreclosure_hold` 字段血缘

> <!-- RULEGLOSS_PTR -->📖 **术语解释**：本文 `rule` 列的技术语句 → 易懂中文 + 数学公式，见 [doc 25 · 逐跳转换规则速查（附录）](25_fcl_lineage_overview.md)。
> <!-- CODEGLOSS_PTR -->🔧 **code 列图例**：`pool`=ETL 建表/SQL 代码 `basic_data_pool_config.py` · `asset`=BPS 同步 SQL `asset_managment_config.py` · `view`=BPS 视图定义；冒号后数字=该文件**行号**（链接可点）。

> **数据来源** —— 真源为 `outputs/fcl_lineage_source.json`（逐字段血缘）；本组逐字段文档目前为手工维护（旧生成器 `scripts/gen_fcl_lineage.py` 已废弃删除）。


## 文档目的

逐字段追踪 BPS 表 `bpms.sync_loan_foreclosure_hold` 的每个字段：从 Servicer 原始列，经每一张中间表，到最终 BPS 列，并给出每一跳的转换规则与代码出处。

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
| 2026-06-09 | AI Agent | v8 | 为 stage 计算字段补完整逻辑说明+举例（多分支多例）；按 SQL 投影 Code-First 校正 end_date/countdown 跳规则（demand_end=催告到期、referral/first_legal/service_end=下一阶段开始、judgement/sale/noi/publication=NULL）；修正 to_judgement/to_sale 错误示例 | doc 02 · doc 13 · doc 14 |
| 2026-06-09 | AI Agent | v9 | 代码引用 [pool:]/[asset:] 做成可点击 GitLab 链接（fork jli/prefectflow，钉到提交 32a750a3，行号精确稳定）；code legend 文件路径亦可点击；view 视图保留纯文字 | doc 02 · doc 13 · doc 14 |
| 2026-06-10 | AI Agent | v10 | hub 新增「FCL 事实中枢 vs BPS 投影」说明：basic_data_loan_fcl=事实中枢/全历史，**直接派生 foreclosure + fcl_stage_info 两张**；_hold/_bankruptcy/_loss_mitigation/fcl_related 各自从原始 servicer 表并行构建（非 fcl 子表） | doc 02 · doc 13 · doc 14 |

## 相关文档

doc 02（ETL 管道，表级）· doc 13/14（字段映射）· doc 25（血缘总览）· 源码 PrefectFlow（见各跳 code）


---

**规范跳链 / canonical hop chain**


`newrez.portnewrezfc (fchold1..4 slots)` → `port.basic_data_loan_foreclosure_hold` → `bpms.sync_loan_foreclosure_hold`

| # | layer | db | 表 table | role |
|---|---|---|---|---|
| 1 | L0/L1 | MySQL+Redshift | `newrez.portnewrezfc (fchold1..4 slots)` | Servicer raw |
| 2 | L4 | Redshift | `port.basic_data_loan_foreclosure_hold` | wide description1..3 (+ Carrington slot4); deduped roll-up of *_hold_detail |
| 3 | L5 | MySQL bpms | `bpms.sync_loan_foreclosure_hold` | long rows via UNION ALL unpivot (GEN_FORECLOSURE_HOLD) |

> `#` 列是序号，不是层号。FCL 事实表 `port.basic_data_loan_fcl` 直接由 L1 各 servicer 原始表构建（在 `tempfc.temp_basic_data_fcl` 中 UNION；CREATE_BASIC_FCL [pool:1531-1654](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L1531-1654)），因此 L2 统一日表（`port.basic_data_daily_loan_common`）与 L3 清洗层（`basic_data_daily_loan_common_clean` / `basic_data_loan_delinq_clean`）按设计不在本分支——它们承载通用+逾期字段，仅经 `group` 维度（doc 27，`basic_data_fcl_related`）与月度 `portmonth` 路径回流。完整 L0–L5 管道见 doc 02。

> code: `pool` = [PrefectFlow/flow/basic_data/basic_data_config/basic_data_pool_config.py](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py) · `asset` = [PrefectFlow/flow/bps/bps_config/asset_managment_config.py](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py) · `view` = bpms.biz_data_view_loan_details_foreclosure (SHOW CREATE VIEW)


## 标识 / 主键列

### 1. id 主键  (`bpms.sync_loan_foreclosure_hold.id`)

_自增代理主键。_

**来源 / Source (L1)**
- Newrez: `bpms.sync_loan_foreclosure_hold.id`  （仅 Newrez 提供此明细）

**流动顺序 / Flow:** ①sync_loan_foreclosure_hold
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `bpms.sync_loan_foreclosure_hold.id` — auto-increment PK (BPS app) [asset]

**说明 / Note:** BPS 应用插入时生成；非来源数据。

### 2. 投资人贷款 ID  (`bpms.sync_loan_foreclosure_hold.loanid`)

_投资人贷款 ID / servicer 贷款 ID。_

**来源 / Source (L1)**
- Newrez: `newrez.portnewrezfc.loanid`  （仅 Newrez 提供此明细）

**流动顺序 / Flow:** ①portnewrezfc → ②basic_data_loan_foreclosure_hold → ③sync_loan_foreclosure_hold
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `newrez.portnewrezfc.loanid` — servicer raw
- 2. `port.basic_data_loan_foreclosure_hold.loanid` — passthrough
- 3. `bpms.sync_loan_foreclosure_hold.loanid` — sync passthrough [asset]

### 3. 服务商贷款 ID  (`bpms.sync_loan_foreclosure_hold.svcloanid`)

_投资人贷款 ID / servicer 贷款 ID。_

**来源 / Source (L1)**
- Newrez: `newrez.portnewrezfc.shellpointloanid`  （仅 Newrez 提供此明细）

**流动顺序 / Flow:** ①portnewrezfc → ②basic_data_loan_foreclosure_hold → ③sync_loan_foreclosure_hold
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `newrez.portnewrezfc.shellpointloanid` — servicer raw
- 2. `port.basic_data_loan_foreclosure_hold.svcloanid` — passthrough
- 3. `bpms.sync_loan_foreclosure_hold.svcloanid` — sync passthrough [asset]

### 4. fctrdt 报告快照日  (`bpms.sync_loan_foreclosure_hold.fctrdt`)

_每日快照/报告日（=dataasof）。_

**来源 / Source (L1)**
- Newrez: `port.basic_data_loan_fcl.dataasof`  （仅 Newrez 提供此明细）

**流动顺序 / Flow:** ①basic_data_loan_fcl → ②sync_loan_foreclosure_hold
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `port.basic_data_loan_fcl.dataasof` — dataasof → fctrdt
- 2. `bpms.sync_loan_foreclosure_hold.fctrdt` — sync passthrough [asset]


## Hold 时段

### 5. Hold 描述（暂停原因）  (`bpms.sync_loan_foreclosure_hold.description`)

_Hold 时段 description（Newrez 宽槽 → 长表行）。_

**来源 / Source (L1)**
- Newrez: `newrez.portnewrezfc.fchold1..3`
- Carrington: `carrington.portcarrington fchold4 slot`
- Capecodfive: —

**流动顺序 / Flow:** ①basic_data_loan_foreclosure_hold → ②sync_loan_foreclosure_hold
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `port.basic_data_loan_foreclosure_hold.description1..3` — slot assembly + dedup roll-up [pool:744-768](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L744-768)
- 2. `bpms.sync_loan_foreclosure_hold.description` — UNION ALL wide→long unpivot [asset:847-892](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L847-892)

```sql
WITH hold_unpivot AS (
  SELECT loanid, description1 AS description, description1_start_date AS s, description1_end_date AS e FROM ...hold WHERE description1<>''
  UNION ALL SELECT loanid, description2, description2_start_date, description2_end_date ...
  UNION ALL SELECT loanid, description3, description3_start_date, description3_end_date ...)
SELECT loanid, description, s AS description_start_date, MAX(e) AS description_end_date GROUP BY loanid, description, s
```
🔎 **说明** Newrez 把最多 3 个 Hold 槽宽存；同步时把非空槽 UNION ALL 成长表行，按 loanid+description+start_date 分组取 MAX(end_date)。
▶ **示例** 7727004408：fchold1=('Court Delay',2026-03-24,2026-04-10)、fchold2=('Mediation Hearing',2026-04-28,2026-05-14) ⇒ 2 行。

### 6. Hold 开始日  (`bpms.sync_loan_foreclosure_hold.description_start_date`)

_Hold 时段 description_start_date（Newrez 宽槽 → 长表行）。_

**来源 / Source (L1)**
- Newrez: `newrez.portnewrezfc.fchold1..3`
- Carrington: `carrington.portcarrington fchold4 slot`
- Capecodfive: —

**流动顺序 / Flow:** ①basic_data_loan_foreclosure_hold → ②sync_loan_foreclosure_hold
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `port.basic_data_loan_foreclosure_hold.description1..3_start_date` — slot assembly + dedup roll-up [pool:744-768](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L744-768)
- 2. `bpms.sync_loan_foreclosure_hold.description_start_date` — UNION ALL wide→long unpivot [asset:847-892](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L847-892)

### 7. Hold 结束日  (`bpms.sync_loan_foreclosure_hold.description_end_date`)

_Hold 时段 description_end_date（Newrez 宽槽 → 长表行）。_

**来源 / Source (L1)**
- Newrez: `newrez.portnewrezfc.fchold1..3`
- Carrington: `carrington.portcarrington fchold4 slot`
- Capecodfive: —

**流动顺序 / Flow:** ①basic_data_loan_foreclosure_hold → ②sync_loan_foreclosure_hold
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `port.basic_data_loan_foreclosure_hold.description1..3_end_date` — slot assembly + dedup roll-up [pool:744-768](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L744-768)
- 2. `bpms.sync_loan_foreclosure_hold.description_end_date` — UNION ALL wide→long unpivot [asset:847-892](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L847-892)


## 系统 / 审计列

### 8. 系统 / 审计列

_应用/ETL 管理列（非 servicer 来源）。_

**列 / Columns:** `create_user, create_dept, create_time, update_user, update_time, status, is_deleted, tenant_id`

**说明 / Note:** 列：create_user, create_dept, create_time, update_user, update_time, status, is_deleted, tenant_id。tenant_id ← GET_LOAN_TENANT_ID(portfunding ⋈ basic_data_trust_funding，[asset:932-936](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L932-936))；create_*/update_* 由 BPS 应用写；is_deleted 视图恒 0；status 应用标志。非 servicer 数据。


> 本文档共 8 个字段。
