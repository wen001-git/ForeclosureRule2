# Doc 30 · 破产（编码→文本解码） — `bpms.sync_loan_foreclosure_bankruptcy` 字段血缘

> <!-- RULEGLOSS_PTR -->📖 **术语解释**：本文 `rule` 列的技术语句 → 易懂中文 + 数学公式，见 [doc 25 · 逐跳转换规则速查（附录）](25_fcl_lineage_overview.md)。

> **自动生成** —— 改动请编辑 `outputs/fcl_lineage_source.json` 后重跑 `python - < scripts/gen_fcl_lineage.py`，勿手改本文件。


## 文档目的

逐字段追踪 BPS 表 `bpms.sync_loan_foreclosure_bankruptcy` 的每个字段：从 Servicer 原始列，经每一张中间表，到最终 BPS 列，并给出每一跳的转换规则与代码出处。

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


`newrez.portnewrezbk (+ portnewrezgeneral.legalstatus)` → `port.basic_data_loan_foreclosure_bankruptcy` → `bpms.sync_loan_foreclosure_bankruptcy`

| # | layer | db | 表 table | role |
|---|---|---|---|---|
| 1 | L0/L1 | MySQL+Redshift | `newrez.portnewrezbk (+ portnewrezgeneral.legalstatus)` | Servicer raw (coded) |
| 2 | L4 | Redshift | `port.basic_data_loan_foreclosure_bankruptcy` | datadic decode; dedup latest per loan+filing |
| 3 | L5 | MySQL bpms | `bpms.sync_loan_foreclosure_bankruptcy` | BPS app table (GEN_FORECLOSURE_BK pass-through) |

> `#` 列是序号，不是层号。FCL 事实表 `port.basic_data_loan_fcl` 直接由 L1 各 servicer 原始表构建（在 `tempfc.temp_basic_data_fcl` 中 UNION；CREATE_BASIC_FCL [pool:1531-1654](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L1531-1654)），因此 L2 统一日表（`port.basic_data_daily_loan_common`）与 L3 清洗层（`basic_data_daily_loan_common_clean` / `basic_data_loan_delinq_clean`）按设计不在本分支——它们承载通用+逾期字段，仅经 `group` 维度（doc 27，`basic_data_fcl_related`）与月度 `portmonth` 路径回流。完整 L0–L5 管道见 doc 02。

> code: `pool` = [PrefectFlow/flow/basic_data/basic_data_config/basic_data_pool_config.py](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py) · `asset` = [PrefectFlow/flow/bps/bps_config/asset_managment_config.py](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py) · `view` = bpms.biz_data_view_loan_details_foreclosure (SHOW CREATE VIEW)

> datadic 解码模式（LM deal/program/status/decision/denial/borrower、BK status）：COALESCE((SELECT description FROM newrez.portnewrezdatadic WHERE field_name='<X>' AND code=CONCAT(raw,'.0')), raw)——原始码存为 '5.0' 形式；字典无匹配则回退原始码。


## 标识 / 主键列

> 仅 Newrez 提供该明细（Carrington 等不在此表构建）。

### 1. id 主键  (`bpms.sync_loan_foreclosure_bankruptcy.id`)

_自增代理主键。_

**来源 / Source (L1)**
- Newrez: `bpms.sync_loan_foreclosure_bankruptcy.id`  （仅 Newrez 提供此明细）

**流动顺序 / Flow:** ①sync_loan_foreclosure_bankruptcy
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `bpms.sync_loan_foreclosure_bankruptcy.id` — auto-increment PK (BPS app) [asset]

**说明 / Note:** BPS 应用插入时生成；非来源数据。

### 2. 投资人贷款 ID  (`bpms.sync_loan_foreclosure_bankruptcy.loanid`)

_投资人贷款 ID / servicer 贷款 ID。_

**来源 / Source (L1)**
- Newrez: `newrez.portnewrezfc.loanid`  （仅 Newrez 提供此明细）

**流动顺序 / Flow:** ①portnewrezfc → ②basic_data_loan_foreclosure_bankruptcy → ③sync_loan_foreclosure_bankruptcy
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `newrez.portnewrezfc.loanid` — servicer raw
- 2. `port.basic_data_loan_foreclosure_bankruptcy.loanid` — passthrough
- 3. `bpms.sync_loan_foreclosure_bankruptcy.loanid` — sync passthrough [asset]

### 3. 服务商贷款 ID  (`bpms.sync_loan_foreclosure_bankruptcy.svcloanid`)

_投资人贷款 ID / servicer 贷款 ID。_

**来源 / Source (L1)**
- Newrez: `newrez.portnewrezfc.shellpointloanid`  （仅 Newrez 提供此明细）

**流动顺序 / Flow:** ①portnewrezfc → ②basic_data_loan_foreclosure_bankruptcy → ③sync_loan_foreclosure_bankruptcy
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `newrez.portnewrezfc.shellpointloanid` — servicer raw
- 2. `port.basic_data_loan_foreclosure_bankruptcy.svcloanid` — passthrough
- 3. `bpms.sync_loan_foreclosure_bankruptcy.svcloanid` — sync passthrough [asset]

### 4. fctrdt 报告快照日  (`bpms.sync_loan_foreclosure_bankruptcy.fctrdt`)

_每日快照/报告日（=dataasof）。_

**来源 / Source (L1)**
- Newrez: `port.basic_data_loan_fcl.dataasof`  （仅 Newrez 提供此明细）

**流动顺序 / Flow:** ①basic_data_loan_fcl → ②sync_loan_foreclosure_bankruptcy
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `port.basic_data_loan_fcl.dataasof` — dataasof → fctrdt
- 2. `bpms.sync_loan_foreclosure_bankruptcy.fctrdt` — sync passthrough [asset]


## 破产记录

> 仅 Newrez 提供该明细（Carrington 等不在此表构建）。

### 5. Bankruptcy Status 破产状态  (`bpms.sync_loan_foreclosure_bankruptcy.bankruptcy_status`)

_破产状态（解码：1→Active,2→Discharged,3→Dismissed,4→Closed,5→ReliefGranted）。_

**来源 / Source (L1)**
- Newrez: `newrez.portnewrezbk` · bkstatus (code)  （仅 Newrez 提供此明细）

**流动顺序 / Flow:** ①portnewrezbk → ②basic_data_loan_foreclosure_bankruptcy → ③sync_loan_foreclosure_bankruptcy
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `newrez.portnewrezbk` · bkstatus (code) — servicer raw 编码
- 2. `port.basic_data_loan_foreclosure_bankruptcy.bankruptcy_status` — datadic decode 解码 [pool:354,367](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L354)
- 3. `bpms.sync_loan_foreclosure_bankruptcy.bankruptcy_status` — GEN_FORECLOSURE_BK pass-through [asset:828](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L828)

```sql
COALESCE(datadic[field_name='BKStatus', code=bkstatus||'.0'].description, bkstatus)
```
🔎 **说明** 整数码经 datadic（field_name='BKStatus'；连接 concat(code,'.0')；回退原始码）解码。解码表：1→Active、2→Discharged、3→Dismissed、4→Closed、5→ReliefGranted。
▶ **示例** 贷款 7727000010：bkstatus=1 ⇒ bankruptcy_status='Active'。

### 6. Legal Status 法律状态  (`bpms.sync_loan_foreclosure_bankruptcy.legal_status`)

_法律状态（BK13/BK7）。_

**来源 / Source (L1)**
- Newrez: `newrez.portnewrezgeneral.legalstatus`  （仅 Newrez 提供此明细）

**流动顺序 / Flow:** ①portnewrezgeneral → ②basic_data_loan_foreclosure_bankruptcy → ③sync_loan_foreclosure_bankruptcy
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `newrez.portnewrezgeneral.legalstatus` — servicer raw
- 2. `port.basic_data_loan_foreclosure_bankruptcy.legal_status` — direct 直传 (join) [pool:355,365](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L355)
- 3. `bpms.sync_loan_foreclosure_bankruptcy.legal_status` — pass-through [asset:829](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L829)

**说明 / Note:** 来自 portnewrezgeneral.legalstatus（非 portnewrezbk），按 loanid+dataasof 关联。

### 7. Status Date 状态日(申请日)  (`bpms.sync_loan_foreclosure_bankruptcy.status_date`)

_破产申请日。_

**来源 / Source (L1)**
- Newrez: `newrez.portnewrezbk.bkfileddate`  （仅 Newrez 提供此明细）

**流动顺序 / Flow:** ①portnewrezbk → ②basic_data_loan_foreclosure_bankruptcy → ③sync_loan_foreclosure_bankruptcy
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `newrez.portnewrezbk.bkfileddate` — servicer raw
- 2. `port.basic_data_loan_foreclosure_bankruptcy.status_date` — rename (dedup key) [pool:356](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L356)
- 3. `bpms.sync_loan_foreclosure_bankruptcy.status_date` — pass-through [asset:830](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L830)

**说明 / Note:** status_date 来源 bkfileddate（申请日），非当前状态日。

### 8. Chapter 章节  (`bpms.sync_loan_foreclosure_bankruptcy.chapter`)

_破产章节（7/11/13）。_

**来源 / Source (L1)**
- Newrez: `newrez.portnewrezbk.bkchapter`  （仅 Newrez 提供此明细）

**流动顺序 / Flow:** ①portnewrezbk → ②basic_data_loan_foreclosure_bankruptcy → ③sync_loan_foreclosure_bankruptcy
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `newrez.portnewrezbk.bkchapter` — servicer raw
- 2. `port.basic_data_loan_foreclosure_bankruptcy.chapter` — cast(decimal) 数值化 [pool:357](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L357)
- 3. `bpms.sync_loan_foreclosure_bankruptcy.chapter` — pass-through [asset:831](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L831)

### 9. 留置状态  (`bpms.sync_loan_foreclosure_bankruptcy.lien_status`)

_Newrez 未填充（NULL）。MFR 字段仅 Carrington 有。_

> ⚠ newrez_null

**来源 / Source (L1)**
- Newrez: `newrez.portnewrezbk` · (none for Newrez)  （仅 Newrez 提供此明细）

**流动顺序 / Flow:** ①portnewrezbk → ②basic_data_loan_foreclosure_bankruptcy → ③sync_loan_foreclosure_bankruptcy
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `newrez.portnewrezbk` · (none for Newrez) — —
- 2. `port.basic_data_loan_foreclosure_bankruptcy.lien_status` — null (Newrez) 常量空 [pool:358-361](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L358-361)
- 3. `bpms.sync_loan_foreclosure_bankruptcy.lien_status` — GEN_FORECLOSURE_BK passthrough [asset:832-835](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L832-835)

### 10. 解除自动中止(MFR)状态  (`bpms.sync_loan_foreclosure_bankruptcy.mfr_status`)

_Newrez 未填充（NULL）。MFR 字段仅 Carrington 有。_

> ⚠ newrez_null

**来源 / Source (L1)**
- Newrez: `newrez.portnewrezbk` · (none for Newrez)  （仅 Newrez 提供此明细）

**流动顺序 / Flow:** ①portnewrezbk → ②basic_data_loan_foreclosure_bankruptcy → ③sync_loan_foreclosure_bankruptcy
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `newrez.portnewrezbk` · (none for Newrez) — —
- 2. `port.basic_data_loan_foreclosure_bankruptcy.mfr_status` — null (Newrez) 常量空 [pool:358-361](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L358-361)
- 3. `bpms.sync_loan_foreclosure_bankruptcy.mfr_status` — GEN_FORECLOSURE_BK passthrough [asset:832-835](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L832-835)

### 11. MFR 申请日  (`bpms.sync_loan_foreclosure_bankruptcy.mfr_filed_date`)

_Newrez 未填充（NULL）。MFR 字段仅 Carrington 有。_

> ⚠ newrez_null

**来源 / Source (L1)**
- Newrez: `newrez.portnewrezbk` · (none for Newrez)  （仅 Newrez 提供此明细）

**流动顺序 / Flow:** ①portnewrezbk → ②basic_data_loan_foreclosure_bankruptcy → ③sync_loan_foreclosure_bankruptcy
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `newrez.portnewrezbk` · (none for Newrez) — —
- 2. `port.basic_data_loan_foreclosure_bankruptcy.mfr_filed_date` — null (Newrez) 常量空 [pool:358-361](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L358-361)
- 3. `bpms.sync_loan_foreclosure_bankruptcy.mfr_filed_date` — GEN_FORECLOSURE_BK passthrough [asset:832-835](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L832-835)

### 12. 债权状态  (`bpms.sync_loan_foreclosure_bankruptcy.claim_status`)

_Newrez 未填充（NULL）。MFR 字段仅 Carrington 有。_

> ⚠ newrez_null

**来源 / Source (L1)**
- Newrez: `newrez.portnewrezbk` · (none for Newrez)  （仅 Newrez 提供此明细）

**流动顺序 / Flow:** ①portnewrezbk → ②basic_data_loan_foreclosure_bankruptcy → ③sync_loan_foreclosure_bankruptcy
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `newrez.portnewrezbk` · (none for Newrez) — —
- 2. `port.basic_data_loan_foreclosure_bankruptcy.claim_status` — null (Newrez) 常量空 [pool:358-361](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L358-361)
- 3. `bpms.sync_loan_foreclosure_bankruptcy.claim_status` — GEN_FORECLOSURE_BK passthrough [asset:832-835](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L832-835)

### 13. Proof of Claim Date 债权申报日  (`bpms.sync_loan_foreclosure_bankruptcy.proof_of_claim_date`)

_债权证明申报日。_

**来源 / Source (L1)**
- Newrez: `newrez.portnewrezbk.pocfileddate`  （仅 Newrez 提供此明细）

**流动顺序 / Flow:** ①portnewrezbk → ②basic_data_loan_foreclosure_bankruptcy → ③sync_loan_foreclosure_bankruptcy
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `newrez.portnewrezbk.pocfileddate` — servicer raw
- 2. `port.basic_data_loan_foreclosure_bankruptcy.proof_of_claim_date` — rename 改名 [pool:362](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L362)
- 3. `bpms.sync_loan_foreclosure_bankruptcy.proof_of_claim_date` — pass-through [asset:836](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L836)

### 14. 破产后应付日  (`bpms.sync_loan_foreclosure_bankruptcy.post_petition_due_date`)

_破产后应付日。_

**来源 / Source (L1)**
- Newrez: `newrez.portnewrezbk.bkpostpetitionduedate`  （仅 Newrez 提供此明细）

**流动顺序 / Flow:** ①portnewrezbk → ②basic_data_loan_foreclosure_bankruptcy → ③sync_loan_foreclosure_bankruptcy
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `newrez.portnewrezbk.bkpostpetitionduedate` — servicer raw
- 2. `port.basic_data_loan_foreclosure_bankruptcy.post_petition_due_date` — rename 改名 [pool:363](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L363)
- 3. `bpms.sync_loan_foreclosure_bankruptcy.post_petition_due_date` — pass-through [asset:837](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L837)


## 系统 / 审计列

> 仅 Newrez 提供该明细（Carrington 等不在此表构建）。

### 15. 系统 / 审计列

_应用/ETL 管理列（非 servicer 来源）。_

**列 / Columns:** `create_user, create_dept, create_time, update_user, update_time, status, is_deleted, tenant_id`

**说明 / Note:** 列：create_user, create_dept, create_time, update_user, update_time, status, is_deleted, tenant_id。tenant_id ← GET_LOAN_TENANT_ID(portfunding ⋈ basic_data_trust_funding，[asset:932-936](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L932-936))；create_*/update_* 由 BPS 应用写；is_deleted 视图恒 0；status 应用标志。非 servicer 数据。


> 本文档共 15 个字段。
