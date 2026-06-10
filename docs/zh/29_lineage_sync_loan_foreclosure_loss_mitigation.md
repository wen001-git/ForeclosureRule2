# Doc 29 · 损失缓释（编码→文本解码） — `bpms.sync_loan_foreclosure_loss_mitigation` 字段血缘

> **自动生成** —— 改动请编辑 `outputs/fcl_lineage_source.json` 后重跑 `python - < scripts/gen_fcl_lineage.py`，勿手改本文件。


## 文档目的

逐字段追踪 BPS 表 `bpms.sync_loan_foreclosure_loss_mitigation` 的每个字段：从 Servicer 原始列，经每一张中间表，到最终 BPS 列，并给出每一跳的转换规则与代码出处。

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


`newrez.portnewrezlm` → `port.basic_data_loan_foreclosure_loss_mitigation` → `bpms.sync_loan_foreclosure_loss_mitigation`

| # | layer | db | 表 table | role |
|---|---|---|---|---|
| 1 | L0/L1 | MySQL+Redshift | `newrez.portnewrezlm` | Servicer raw (coded) |
| 2 | L4 | Redshift | `port.basic_data_loan_foreclosure_loss_mitigation` | datadic decode (COALESCE(desc, code)); dedup latest per loan+cycle |
| 3 | L5 | MySQL bpms | `bpms.sync_loan_foreclosure_loss_mitigation` | BPS app table (GEN_FORECLOSURE_LM pass-through) |

> `#` 列是序号，不是层号。FCL 事实表 `port.basic_data_loan_fcl` 直接由 L1 各 servicer 原始表构建（在 `tempfc.temp_basic_data_fcl` 中 UNION；CREATE_BASIC_FCL pool:1531-1654），因此 L2 统一日表（`port.basic_data_daily_loan_common`）与 L3 清洗层（`…_clean` / `…_delinq_clean`）按设计不在本分支——它们承载通用+逾期字段，仅经 `group` 维度（doc 27，`basic_data_fcl_related`）与月度 `portmonth` 路径回流。完整 L0–L5 管道见 doc 02。

> code: `pool` = PrefectFlow/flow/basic_data/basic_data_config/basic_data_pool_config.py · `asset` = PrefectFlow/flow/bps/bps_config/asset_managment_config.py · `view` = bpms.biz_data_view_loan_details_foreclosure (SHOW CREATE VIEW)

> datadic 解码模式（LM deal/program/status/decision/denial/borrower、BK status）：COALESCE((SELECT description FROM newrez.portnewrezdatadic WHERE field_name='<X>' AND code=CONCAT(raw,'.0')), raw)——原始码存为 '5.0' 形式；字典无匹配则回退原始码。


## 标识 / 主键列

> 仅 Newrez 提供该明细（Carrington 等不在此表构建）。

### 1. id 主键  (`bpms.sync_loan_foreclosure_loss_mitigation.id`)

_自增代理主键。_

**来源 / Source (L1)**
- Newrez: `bpms.sync_loan_foreclosure_loss_mitigation.id`  （仅 Newrez 提供此明细）

**流动顺序 / Flow:** ①sync_loan_foreclosure_loss_mitigation
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `bpms.sync_loan_foreclosure_loss_mitigation.id` — auto-increment PK (BPS app) [asset]

**说明 / Note:** BPS 应用插入时生成；非来源数据。

### 2. 投资人贷款 ID  (`bpms.sync_loan_foreclosure_loss_mitigation.loanid`)

_投资人贷款 ID / servicer 贷款 ID。_

**来源 / Source (L1)**
- Newrez: `newrez.portnewrezfc.loanid`  （仅 Newrez 提供此明细）

**流动顺序 / Flow:** ①portnewrezfc → ②basic_data_loan_foreclosure_loss_mitigation → ③sync_loan_foreclosure_loss_mitigation
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `newrez.portnewrezfc.loanid` — servicer raw
- 2. `port.basic_data_loan_foreclosure_loss_mitigation.loanid` — passthrough
- 3. `bpms.sync_loan_foreclosure_loss_mitigation.loanid` — sync passthrough [asset]

### 3. 服务商贷款 ID  (`bpms.sync_loan_foreclosure_loss_mitigation.svcloanid`)

_投资人贷款 ID / servicer 贷款 ID。_

**来源 / Source (L1)**
- Newrez: `newrez.portnewrezfc.shellpointloanid`  （仅 Newrez 提供此明细）

**流动顺序 / Flow:** ①portnewrezfc → ②basic_data_loan_foreclosure_loss_mitigation → ③sync_loan_foreclosure_loss_mitigation
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `newrez.portnewrezfc.shellpointloanid` — servicer raw
- 2. `port.basic_data_loan_foreclosure_loss_mitigation.svcloanid` — passthrough
- 3. `bpms.sync_loan_foreclosure_loss_mitigation.svcloanid` — sync passthrough [asset]

### 4. fctrdt 报告快照日  (`bpms.sync_loan_foreclosure_loss_mitigation.fctrdt`)

_每日快照/报告日（=dataasof）。_

**来源 / Source (L1)**
- Newrez: `port.basic_data_loan_fcl.dataasof`  （仅 Newrez 提供此明细）

**流动顺序 / Flow:** ①basic_data_loan_fcl → ②sync_loan_foreclosure_loss_mitigation
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `port.basic_data_loan_fcl.dataasof` — dataasof → fctrdt
- 2. `bpms.sync_loan_foreclosure_loss_mitigation.fctrdt` — sync passthrough [asset]


## 损失缓释周期

> 仅 Newrez 提供该明细（Carrington 等不在此表构建）。

### 5. Deal 交易类型  (`bpms.sync_loan_foreclosure_loss_mitigation.deal`)

_LM 交易类型（解码）。_

**来源 / Source (L1)**
- Newrez: `newrez.portnewrezlm` · lmdeal (code)  （仅 Newrez 提供此明细）

**流动顺序 / Flow:** ①portnewrezlm → ②basic_data_loan_foreclosure_loss_mitigation → ③sync_loan_foreclosure_loss_mitigation
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `newrez.portnewrezlm` · lmdeal (code) — servicer raw 编码
- 2. `port.basic_data_loan_foreclosure_loss_mitigation.deal` — datadic decode 解码 见 sql [pool:821,835]
- 3. `bpms.sync_loan_foreclosure_loss_mitigation.deal` — GEN_FORECLOSURE_LM pass-through [asset:804]

```sql
COALESCE(datadic[field_name='LMDeal', code=lmdeal||'.0'].description, lmdeal)
```
🔎 **说明** 整数码经 newrez.portnewrezdatadic（field_name='LMDeal'）解码为文本。码以 'N.0' 存储，故连接键为 concat(code,'.0')；字典无匹配时 COALESCE 回退原始码。
▶ **示例** 7727004408：lmdeal=2 ⇒ deal='Evaluation'。

### 6. Program 方案  (`bpms.sync_loan_foreclosure_loss_mitigation.program`)

_LM 方案（解码）。_

**来源 / Source (L1)**
- Newrez: `newrez.portnewrezlm` · lmprogram (code)  （仅 Newrez 提供此明细）

**流动顺序 / Flow:** ①portnewrezlm → ②basic_data_loan_foreclosure_loss_mitigation → ③sync_loan_foreclosure_loss_mitigation
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `newrez.portnewrezlm` · lmprogram (code) — servicer raw 编码
- 2. `port.basic_data_loan_foreclosure_loss_mitigation.program` — datadic decode 解码 [pool:822,836]
- 3. `bpms.sync_loan_foreclosure_loss_mitigation.program` — pass-through [asset:805]

```sql
COALESCE(datadic['LMProgram', lmprogram||'.0'], lmprogram)
```
🔎 **说明** 同 datadic 解码模式，field_name='LMProgram'（连接 concat(code,'.0')；回退原始码）。
▶ **示例** 7727004408：lmprogram=21 ⇒ program='Evaluation'。

### 7. Status 状态  (`bpms.sync_loan_foreclosure_loss_mitigation.lmc_status`)

_LM 周期状态（解码）。_

**来源 / Source (L1)**
- Newrez: `newrez.portnewrezlm` · lmstatus (code)  （仅 Newrez 提供此明细）

**流动顺序 / Flow:** ①portnewrezlm → ②basic_data_loan_foreclosure_loss_mitigation → ③sync_loan_foreclosure_loss_mitigation
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `newrez.portnewrezlm` · lmstatus (code) — servicer raw 编码
- 2. `port.basic_data_loan_foreclosure_loss_mitigation.lmc_status` — datadic decode 解码 [pool:823,837]
- 3. `bpms.sync_loan_foreclosure_loss_mitigation.lmc_status` — pass-through [asset:806]

```sql
COALESCE(datadic['LMStatus', lmstatus||'.0'], lmstatus)
```
🔎 **说明** 同 datadic 解码模式，field_name='LMStatus'（连接 concat(code,'.0')；回退原始码）。
▶ **示例** 7727004408：lmstatus=166 ⇒ lmc_status='Pending Financials'。

### 8. Cycle Opened Date 周期开启日  (`bpms.sync_loan_foreclosure_loss_mitigation.cycle_opened_date`)

_LM 周期开始日。_

**来源 / Source (L1)**
- Newrez: `newrez.portnewrezlm.dealstartdate`  （仅 Newrez 提供此明细）

**流动顺序 / Flow:** ①portnewrezlm → ②basic_data_loan_foreclosure_loss_mitigation → ③sync_loan_foreclosure_loss_mitigation
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `newrez.portnewrezlm.dealstartdate` — servicer raw
- 2. `port.basic_data_loan_foreclosure_loss_mitigation.cycle_opened_date` — rename 改名 (dedup key) [pool:824]
- 3. `bpms.sync_loan_foreclosure_loss_mitigation.cycle_opened_date` — pass-through [asset:807]

### 9. Cycle Closed Date 周期关闭日  (`bpms.sync_loan_foreclosure_loss_mitigation.cycle_closed_date`)

_LM 周期结束日（NULL=进行中）。_

**来源 / Source (L1)**
- Newrez: `newrez.portnewrezlm.lmremovaldate`  （仅 Newrez 提供此明细）

**流动顺序 / Flow:** ①portnewrezlm → ②basic_data_loan_foreclosure_loss_mitigation → ③sync_loan_foreclosure_loss_mitigation
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `newrez.portnewrezlm.lmremovaldate` — servicer raw
- 2. `port.basic_data_loan_foreclosure_loss_mitigation.cycle_closed_date` — rename 改名 [pool:825]
- 3. `bpms.sync_loan_foreclosure_loss_mitigation.cycle_closed_date` — pass-through [asset:808]

### 10. Final Disposition 最终处置  (`bpms.sync_loan_foreclosure_loss_mitigation.final_disposition`)

_LM 最终结论（解码）。_

**来源 / Source (L1)**
- Newrez: `newrez.portnewrezlm` · lmdecision (code)  （仅 Newrez 提供此明细）

**流动顺序 / Flow:** ①portnewrezlm → ②basic_data_loan_foreclosure_loss_mitigation → ③sync_loan_foreclosure_loss_mitigation
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `newrez.portnewrezlm` · lmdecision (code) — servicer raw 编码
- 2. `port.basic_data_loan_foreclosure_loss_mitigation.final_disposition` — datadic decode 解码 [pool:826,838]
- 3. `bpms.sync_loan_foreclosure_loss_mitigation.final_disposition` — pass-through [asset:809]

```sql
COALESCE(datadic['LMDecision', lmdecision||'.0'], lmdecision)
```
🔎 **说明** 同 datadic 解码模式，field_name='LMDecision'（连接 concat(code,'.0')；回退原始码）。
▶ **示例** 7727004408：lmdecision=99 ⇒ final_disposition='Pending'。

### 11. Denial / Reason 拒绝原因  (`bpms.sync_loan_foreclosure_loss_mitigation.denialreason`)

_拒绝原因（解码）。_

**来源 / Source (L1)**
- Newrez: `newrez.portnewrezlm` · denialreason (code)  （仅 Newrez 提供此明细）

**流动顺序 / Flow:** ①portnewrezlm → ②basic_data_loan_foreclosure_loss_mitigation → ③sync_loan_foreclosure_loss_mitigation
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `newrez.portnewrezlm` · denialreason (code) — servicer raw 编码
- 2. `port.basic_data_loan_foreclosure_loss_mitigation.denialreason` — datadic decode 解码 [pool:828,840]
- 3. `bpms.sync_loan_foreclosure_loss_mitigation.denialreason` — pass-through [asset:810]

```sql
COALESCE(datadic['DenialReason', denialreason||'.0'], denialreason)
```
🔎 **说明** 同 datadic 解码模式，field_name='DenialReason'（连接 concat(code,'.0')；回退原始码）。
▶ **示例** 7727004408（Short Sale 周期）：denialreason=78 ⇒ 'Buyer walked (SS)'。

### 12. Borrower Intentions 借款人意向  (`bpms.sync_loan_foreclosure_loss_mitigation.borrower_intentions`)

_借款人意向（解码）。_

**来源 / Source (L1)**
- Newrez: `newrez.portnewrezlm` · borrowerintention (code)  （仅 Newrez 提供此明细）

**流动顺序 / Flow:** ①portnewrezlm → ②basic_data_loan_foreclosure_loss_mitigation → ③sync_loan_foreclosure_loss_mitigation
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `newrez.portnewrezlm` · borrowerintention (code) — servicer raw 编码
- 2. `port.basic_data_loan_foreclosure_loss_mitigation.borrower_intentions` — datadic decode 解码 [pool:829,839]
- 3. `bpms.sync_loan_foreclosure_loss_mitigation.borrower_intentions` — pass-through [asset:811]

**说明 / Note:** 原始列 borrowerintention（单数）→ 输出 borrower_intentions（复数）。

```sql
COALESCE(datadic['BorrowerIntention', borrowerintention||'.0'], borrowerintention)
```
🔎 **说明** 同 datadic 解码模式，field_name='BorrowerIntention'（连接 concat(code,'.0')；回退原始码）。注意原始列 borrowerintention（单数）→ 输出 borrower_intentions（复数）。
▶ **示例** 7727004408（Short Sale 周期）：borrowerintention=3 ⇒ 'Disposition'。

### 13. 即将违约标志  (`bpms.sync_loan_foreclosure_loss_mitigation.imminent_default`)

_即将违约标志。_

> ⚠ newrez_null

**来源 / Source (L1)**
- Newrez: `newrez.portnewrezlm`  （仅 Newrez 提供此明细）

**流动顺序 / Flow:** ①portnewrezlm → ②basic_data_loan_foreclosure_loss_mitigation → ③sync_loan_foreclosure_loss_mitigation
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `newrez.portnewrezlm` — 无源
- 2. `port.basic_data_loan_foreclosure_loss_mitigation.imminent_default` — null [pool:830]
- 3. `bpms.sync_loan_foreclosure_loss_mitigation.imminent_default` — pass-through [asset:812]

**说明 / Note:** Newrez 硬编码 NULL。

### 14. 单一联系人(SPOC)  (`bpms.sync_loan_foreclosure_loss_mitigation.single_point_of_contact`)

_单一联系人。_

> ⚠ newrez_null

**来源 / Source (L1)**
- Newrez: `newrez.portnewrezlm`  （仅 Newrez 提供此明细）

**流动顺序 / Flow:** ①portnewrezlm → ②basic_data_loan_foreclosure_loss_mitigation → ③sync_loan_foreclosure_loss_mitigation
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `newrez.portnewrezlm` — 无源
- 2. `port.basic_data_loan_foreclosure_loss_mitigation.single_point_of_contact` — null [pool:831]
- 3. `bpms.sync_loan_foreclosure_loss_mitigation.single_point_of_contact` — pass-through [asset:813]

**说明 / Note:** Newrez 硬编码 NULL。


## 系统 / 审计列

> 仅 Newrez 提供该明细（Carrington 等不在此表构建）。

### 15. 系统 / 审计列

_应用/ETL 管理列（非 servicer 来源）。_

**列 / Columns:** `create_user, create_dept, create_time, update_user, update_time, status, is_deleted, tenant_id`

**说明 / Note:** 列：create_user, create_dept, create_time, update_user, update_time, status, is_deleted, tenant_id。tenant_id ← GET_LOAN_TENANT_ID(portfunding ⋈ basic_data_trust_funding，asset:932-936)；create_*/update_* 由 BPS 应用写；is_deleted 视图恒 0；status 应用标志。非 servicer 数据。


> 本文档共 15 个字段。
