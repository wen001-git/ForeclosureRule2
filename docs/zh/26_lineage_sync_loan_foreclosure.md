# Doc 26 · 主线（里程碑 / 汇总 / 状态） — `bpms.sync_loan_foreclosure` 字段血缘

> <!-- RULEGLOSS_PTR -->📖 **术语解释**：本文 `rule` 列的技术语句 → 易懂中文 + 数学公式，见 [doc 25 · 逐跳转换规则速查（附录）](25_fcl_lineage_overview.md)。
> <!-- CODEGLOSS_PTR -->🔧 **code 列图例**：`pool`=ETL 建表/SQL 代码 `basic_data_pool_config.py` · `asset`=BPS 同步 SQL `asset_managment_config.py` · `view`=BPS 视图定义；冒号后数字=该文件**行号**（链接可点）。

> **数据来源** —— 真源为 `outputs/fcl_lineage_source.json`（逐字段血缘）；本组逐字段文档目前为手工维护（旧生成器 `scripts/gen_fcl_lineage.py` 已废弃删除）。


## 文档目的

逐字段追踪 BPS 表 `bpms.sync_loan_foreclosure` 的每个字段：从 Servicer 原始列，经每一张中间表，到最终 BPS 列，并给出每一跳的转换规则与代码出处。

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


`newrez.portnewrezfc` → `tempfc.temp_basic_data_fcl` → `port.basic_data_loan_fcl` → `port.basic_data_loan_foreclosure` → `bpms.sync_loan_foreclosure` → `bpms.biz_data_view_loan_details_foreclosure`

| # | layer | db | 表 table | role |
|---|---|---|---|---|
| 1 | L0/L1 | MySQL+Redshift | `newrez.portnewrezfc` | Servicer raw |
| 2 | L4·temp | Redshift | `tempfc.temp_basic_data_fcl` | 3-servicer rename-UNION of L1 raw / 三家 servicer 改名 UNION (CREATE_BASIC_FCL, [pool:1531-1654](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L1531-1654)) |
| 3 | L4 | Redshift | `port.basic_data_loan_fcl` | canonical FCL fact |
| 4 | L4 | Redshift→MySQL | `port.basic_data_loan_foreclosure` | timeline+summary build (GEN_FCL_DETAIL) |
| 5 | L5 | MySQL bpms | `bpms.sync_loan_foreclosure` | BPS app table (UPDATE_FORECLOSURE upsert) |
| 6 | L5 | MySQL bpms | `bpms.biz_data_view_loan_details_foreclosure` | display view (Actual/Var days) |

> `#` 列是序号，不是层号。FCL 事实表 `port.basic_data_loan_fcl` 直接由 L1 各 servicer 原始表构建（在 `tempfc.temp_basic_data_fcl` 中 UNION；CREATE_BASIC_FCL [pool:1531-1654](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L1531-1654)），因此 L2 统一日表（`port.basic_data_daily_loan_common`）与 L3 清洗层（`basic_data_daily_loan_common_clean` / `basic_data_loan_delinq_clean`）按设计不在本分支——它们承载通用+逾期字段，仅经 `group` 维度（doc 27，`basic_data_fcl_related`）与月度 `portmonth` 路径回流。完整 L0–L5 管道见 doc 02。

> code: `pool` = [PrefectFlow/flow/basic_data/basic_data_config/basic_data_pool_config.py](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py) · `asset` = [PrefectFlow/flow/bps/bps_config/asset_managment_config.py](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py) · `view` = bpms.biz_data_view_loan_details_foreclosure (SHOW CREATE VIEW)


## 标识 / 主键列

### 1. id 主键  (`bpms.sync_loan_foreclosure.id`)

_自增代理主键。_

**来源 / Source (L1)**
- Newrez: `bpms.sync_loan_foreclosure.id`  （仅 Newrez 提供此明细）

**流动顺序 / Flow:** ①sync_loan_foreclosure
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `bpms.sync_loan_foreclosure.id` — auto-increment PK (BPS app) [asset]

**说明 / Note:** BPS 应用插入时生成；非来源数据。

### 2. bid_id 交易ID  (`bpms.sync_loan_foreclosure.bid_id`)

_Bridger deal id。_

**来源 / Source (L1)**
- Newrez: `port.portfunding.dealid`  （仅 Newrez 提供此明细）

**流动顺序 / Flow:** ①portfunding → ②sync_loan_foreclosure  （视图 `biz_data_view_loan_details_foreclosure` 不暴露此列，故链路终止于 sync 表）
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `port.portfunding.dealid` — join on loanid [asset:541,604](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L541)
- 2. `bpms.sync_loan_foreclosure.bid_id` — dealid → bid_id [asset:541](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L541)

### 3. funding_id 资金ID  (`bpms.sync_loan_foreclosure.funding_id`)

_Bridger funding id。_

**来源 / Source (L1)**
- Newrez: `port.portfunding.fundingid`  （仅 Newrez 提供此明细）

**流动顺序 / Flow:** ①portfunding → ②sync_loan_foreclosure  （视图 `biz_data_view_loan_details_foreclosure` 不暴露此列，故链路终止于 sync 表）
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `port.portfunding.fundingid` — join on loanid [asset:542,604](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L542)
- 2. `bpms.sync_loan_foreclosure.funding_id` — fundingid → funding_id [asset:542](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L542)

### 4. 投资人贷款 ID  (`bpms.sync_loan_foreclosure.loanid`)

_投资人贷款 ID / servicer 贷款 ID。_

**来源 / Source (L1)**
- Newrez: `newrez.portnewrezfc.loanid`  （仅 Newrez 提供此明细）

**流动顺序 / Flow:** ①portnewrezfc → ②basic_data_loan_fcl → ③basic_data_loan_foreclosure → ④sync_loan_foreclosure → ⑤biz_data_view_loan_details_foreclosure
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `newrez.portnewrezfc.loanid` — servicer raw 原始
- 2. `port.basic_data_loan_fcl.loanid` — rename/passthrough 改名直传
- 3. `port.basic_data_loan_foreclosure.loanid` — passthrough 直传
- 4. `bpms.sync_loan_foreclosure.loanid` — GEN_FORECLOSURE join port.portfunding 直传 [asset:543](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L543)
- 5. `bpms.biz_data_view_loan_details_foreclosure.loanid` — passthrough [view]

### 5. 服务商贷款 ID  (`bpms.sync_loan_foreclosure.svcloanid`)

_投资人贷款 ID / servicer 贷款 ID。_

**来源 / Source (L1)**
- Newrez: `newrez.portnewrezfc.shellpointloanid`  （仅 Newrez 提供此明细）

**流动顺序 / Flow:** ①portnewrezfc → ②basic_data_loan_fcl → ③basic_data_loan_foreclosure → ④sync_loan_foreclosure → ⑤biz_data_view_loan_details_foreclosure
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `newrez.portnewrezfc.shellpointloanid` — servicer raw 原始
- 2. `port.basic_data_loan_fcl.svc_loanid` — rename/passthrough 改名直传
- 3. `port.basic_data_loan_foreclosure.svcloanid` — passthrough 直传
- 4. `bpms.sync_loan_foreclosure.svcloanid` — GEN_FORECLOSURE join port.portfunding 直传 [asset:543](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L543)
- 5. `bpms.biz_data_view_loan_details_foreclosure.svcloanid` — passthrough [view]

### 6. servicer 服务商  (`bpms.sync_loan_foreclosure.servicer`)

_服务商名。_

**来源 / Source (L1)**
- Newrez: `(per servicer)` · constant 'Newrez'/'Carrington'/'Capecodfive'  （仅 Newrez 提供此明细）

**流动顺序 / Flow:** ①(per → ②sync_loan_foreclosure
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `(per servicer)` · constant 'Newrez'/'Carrington'/'Capecodfive' — constant per UNION branch [pool:1536/1577/1618](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L1536)
- 2. `bpms.sync_loan_foreclosure.servicer` — sync passthrough [asset]


## 时间线里程碑

### 7. Notice of Intent 通知意向日  (`bpms.sync_loan_foreclosure.timeline_notice_of_intent_date`)

_NOI/Demand 催告函日期。_

> ⚠ newrez_null

**来源 / Source (L1)**
- Newrez: —
- Carrington: —
- Capecodfive: `capecodfive.portcapecodfive_monthly_collections.noi_date`

**流动顺序 / Flow:** ①basic_data_loan_fcl → ②basic_data_loan_foreclosure → ③sync_loan_foreclosure → ④biz_data_view_loan_details_foreclosure
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `port.basic_data_loan_fcl.noi_date` — null for Newrez（常量空） [pool:1542](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L1542)
- 2. `port.basic_data_loan_foreclosure.timeline_notice_of_intent_date` — direct copy 直传 [pool:258](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L258)
- 3. `bpms.sync_loan_foreclosure.timeline_notice_of_intent_date` — upsert pass-through 直传 [asset:703/753](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L703)
- 4. `bpms.biz_data_view_loan_details_foreclosure` · timeline_notice_of_intent_date (+actual/var) — view: actual=to_days(x)-to_days(nextduedate); var=actual-target [view]

**说明 / Note:** Newrez 无 NOI 源 → 恒空；仅 Capecodfive 填充。

### 8. 通知意向结束日期  (`bpms.sync_loan_foreclosure.timeline_notice_of_intent_end_date`)

_保留里程碑；FCL ETL 未填充。_

> ⚠ null_in_build

**来源 / Source (L1)**
- Newrez: `port.basic_data_loan_foreclosure.timeline_notice_of_intent_end_date`  （仅 Newrez 提供此明细）

**流动顺序 / Flow:** ①basic_data_loan_foreclosure → ②sync_loan_foreclosure → ③biz_data_view_loan_details_foreclosure
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `port.basic_data_loan_foreclosure.timeline_notice_of_intent_end_date` — not in GEN_FCL_DETAIL INSERT → NULL 未填充 [pool:148-305](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L148-305)
- 2. `bpms.sync_loan_foreclosure.timeline_notice_of_intent_end_date` — GEN_FORECLOSURE 直传（值=NULL） [asset:540-605](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L540-605)
- 3. `bpms.biz_data_view_loan_details_foreclosure.timeline_notice_of_intent_end_date` — passthrough [view]

### 9. 批准转交日期  (`bpms.sync_loan_foreclosure.timeline_approved_for_referral_date`)

_保留里程碑；FCL ETL 未填充。_

> ⚠ null_in_build

**来源 / Source (L1)**
- Newrez: `port.basic_data_loan_foreclosure.timeline_approved_for_referral_date`  （仅 Newrez 提供此明细）

**流动顺序 / Flow:** ①basic_data_loan_foreclosure → ②sync_loan_foreclosure → ③biz_data_view_loan_details_foreclosure
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `port.basic_data_loan_foreclosure.timeline_approved_for_referral_date` — not in GEN_FCL_DETAIL INSERT → NULL 未填充 [pool:148-305](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L148-305)
- 2. `bpms.sync_loan_foreclosure.timeline_approved_for_referral_date` — GEN_FORECLOSURE 直传（值=NULL） [asset:540-605](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L540-605)
- 3. `bpms.biz_data_view_loan_details_foreclosure.timeline_approved_for_referral_date` — passthrough [view]

### 10. 转交律师日期  (`bpms.sync_loan_foreclosure.timeline_referred_to_attorney_date`)

_保留里程碑；FCL ETL 未填充。_

> ⚠ null_in_build

**来源 / Source (L1)**
- Newrez: `port.basic_data_loan_foreclosure.timeline_referred_to_attorney_date`  （仅 Newrez 提供此明细）

**流动顺序 / Flow:** ①basic_data_loan_foreclosure → ②sync_loan_foreclosure → ③biz_data_view_loan_details_foreclosure
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `port.basic_data_loan_foreclosure.timeline_referred_to_attorney_date` — not in GEN_FCL_DETAIL INSERT → NULL 未填充 [pool:148-305](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L148-305)
- 2. `bpms.sync_loan_foreclosure.timeline_referred_to_attorney_date` — GEN_FORECLOSURE 直传（值=NULL） [asset:540-605](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L540-605)
- 3. `bpms.biz_data_view_loan_details_foreclosure.timeline_referred_to_attorney_date` — passthrough [view]

### 11. Referred to Foreclosure 转介止赎  (`bpms.sync_loan_foreclosure.timeline_referred_to_foreclosure_date`)

_正式 FCL 转介日；BPS 入库过滤（须非空）。_

**来源 / Source (L1)**
- Newrez: `newrez.portnewrezfc.fcreferraldate`
- Carrington: `carrington.portcarrington.fcl_referral_date`
- Capecodfive: `capecodfive.portcapecodfive_monthly_collections.foreclosure_date_refrd_atty`

**流动顺序 / Flow:** ①basic_data_loan_fcl → ②basic_data_loan_foreclosure → ③sync_loan_foreclosure → ④biz_data_view_loan_details_foreclosure
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `port.basic_data_loan_fcl.referral_start_date` — rename 改名 [pool:1544](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L1544)
- 2. `port.basic_data_loan_foreclosure.timeline_referred_to_foreclosure_date` — direct copy 直传 [pool:259](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L259)
- 3. `bpms.sync_loan_foreclosure.timeline_referred_to_foreclosure_date` — upsert pass-through 直传 [asset:707/757](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L707)
- 4. `bpms.biz_data_view_loan_details_foreclosure` · timeline_referred_to_foreclosure_date (+actual/var) — view: actual=to_days(x)-to_days(nextduedate); var=actual-Σtarget [view]

### 12. Title Report Received 收到产权报告  (`bpms.sync_loan_foreclosure.timeline_title_report_received_date`)

_产权报告收到日。_

> ⚠ newrez_empty

**来源 / Source (L1)**
- Newrez: `newrez.portnewrezfc.titlereceiveddate`
- Carrington: —
- Capecodfive: —

**流动顺序 / Flow:** ①basic_data_loan_fcl → ②basic_data_loan_foreclosure → ③sync_loan_foreclosure → ④biz_data_view_loan_details_foreclosure
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `port.basic_data_loan_fcl.titlereceiveddate` — rename 改名 [pool:1540](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L1540)
- 2. `port.basic_data_loan_foreclosure.timeline_title_report_received_date` — direct copy 直传 [pool:260](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L260)
- 3. `bpms.sync_loan_foreclosure.timeline_title_report_received_date` — upsert pass-through [asset:758](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L758)
- 4. `bpms.biz_data_view_loan_details_foreclosure` · timeline_title_report_received_date (+actual/var) — view actual/var [view]

**说明 / Note:** Newrez 实测不填充（活跃 FCL ~0%）。

### 13. Preliminary Title Cleared 初步产权清查  (`bpms.sync_loan_foreclosure.timeline_preliminary_title_cleared_date`)

_初步产权清查日。_

> ⚠ newrez_empty

**来源 / Source (L1)**
- Newrez: `newrez.portnewrezfc.titlecleardate`
- Carrington: —
- Capecodfive: —

**流动顺序 / Flow:** ①basic_data_loan_fcl → ②basic_data_loan_foreclosure → ③sync_loan_foreclosure → ④biz_data_view_loan_details_foreclosure
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `port.basic_data_loan_fcl.titlecleardate` — rename 改名 [pool:1541](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L1541)
- 2. `port.basic_data_loan_foreclosure.timeline_preliminary_title_cleared_date` — direct copy 直传 [pool:261](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L261)
- 3. `bpms.sync_loan_foreclosure.timeline_preliminary_title_cleared_date` — upsert pass-through [asset:759](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L759)
- 4. `bpms.biz_data_view_loan_details_foreclosure` · timeline_preliminary_title_cleared_date (+actual/var) — view actual/var [view]

**说明 / Note:** 与 Final Title Cleared 共用 titlecleardate；Newrez 不填充。

### 14. 1st Legal 首次法律行动  (`bpms.sync_loan_foreclosure.timeline_first_legal_date`)

_首次法律行动（Filing）日。_

**来源 / Source (L1)**
- Newrez: `newrez.portnewrezfc.firstlegaldate`
- Carrington: —
- Capecodfive: `capecodfive.portcapecodfive_monthly_collections.foreclosure_first_legal_date`

**流动顺序 / Flow:** ①basic_data_loan_fcl → ②basic_data_loan_foreclosure → ③sync_loan_foreclosure → ④biz_data_view_loan_details_foreclosure
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `port.basic_data_loan_fcl.legal_start_date` — rename 改名 [pool:1549](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L1549)
- 2. `port.basic_data_loan_foreclosure.timeline_first_legal_date` — direct copy 直传 [pool:262](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L262)
- 3. `bpms.sync_loan_foreclosure.timeline_first_legal_date` — upsert pass-through [asset:760](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L760)
- 4. `bpms.biz_data_view_loan_details_foreclosure` · timeline_first_legal_date (+actual/var) — view actual/var [view]

**说明 / Note:** Non-Judicial 州通常为空。

### 15. Service Complete 送达完成  (`bpms.sync_loan_foreclosure.timeline_service_date`)

_法律文书送达完成日。_

**来源 / Source (L1)**
- Newrez: `newrez.portnewrezfc.servicecompletedate`
- Carrington: —
- Capecodfive: `capecodfive.portcapecodfive_monthly_collections.foreclosure_service_date`

**流动顺序 / Flow:** ①basic_data_loan_fcl → ②basic_data_loan_foreclosure → ③sync_loan_foreclosure → ④biz_data_view_loan_details_foreclosure
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `port.basic_data_loan_fcl.service_start_date` — rename 改名 [pool:1550](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L1550)
- 2. `port.basic_data_loan_foreclosure.timeline_service_date` — direct copy 直传 [pool:263](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L263)
- 3. `bpms.sync_loan_foreclosure.timeline_service_date` — upsert pass-through [asset:761](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L761)
- 4. `bpms.biz_data_view_loan_details_foreclosure` · timeline_service_date (+actual/var) — view actual/var [view]

### 16. 止赎公告计划发布日期  (`bpms.sync_loan_foreclosure.timeline_publication_date`)

_保留里程碑；FCL ETL 未填充。_

> ⚠ null_in_build

**来源 / Source (L1)**
- Newrez: `port.basic_data_loan_foreclosure.timeline_publication_date`  （仅 Newrez 提供此明细）

**流动顺序 / Flow:** ①basic_data_loan_foreclosure → ②sync_loan_foreclosure → ③biz_data_view_loan_details_foreclosure
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `port.basic_data_loan_foreclosure.timeline_publication_date` — not in GEN_FCL_DETAIL INSERT → NULL 未填充 [pool:148-305](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L148-305)
- 2. `bpms.sync_loan_foreclosure.timeline_publication_date` — GEN_FORECLOSURE 直传（值=NULL） [asset:540-605](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L540-605)
- 3. `bpms.biz_data_view_loan_details_foreclosure.timeline_publication_date` — passthrough [view]

### 17. Judgement Hearing Set 听证排定(首见)  (`bpms.sync_loan_foreclosure.timeline_judgement_hearing_set_date`)

_当前排定听证日期值在快照中首次出现日（ETL 追踪）。仅司法州。_

**来源 / Source (L1)**
- Newrez: `newrez.portnewrezfc.fcjudgmenthearingscheduled`
- Carrington: —
- Capecodfive: —

**流动顺序 / Flow:** ①basic_data_loan_fcl → ②basic_data_loan_foreclosure → ③sync_loan_foreclosure → ④biz_data_view_loan_details_foreclosure
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `port.basic_data_loan_fcl.fcjudgment_hearing_scheduled` — rename 改名 [pool:1551](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L1551)
- 2. `port.basic_data_loan_foreclosure.timeline_judgement_hearing_set_date` — ETL tracking: min(dataasof) of current value 首见日 [pool:264,295](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L264)
- 3. `bpms.sync_loan_foreclosure.timeline_judgement_hearing_set_date` — upsert pass-through [asset:762](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L762)
- 4. `bpms.biz_data_view_loan_details_foreclosure` · timeline_judgement_hearing_set_date (+actual/var) — view actual/var [view]

```sql
ju.jd_set_date = min(dataasof) FROM port.basic_data_loan_fcl WHERE fcjudgment_hearing_scheduled IS NOT NULL GROUP BY loanid, fcjudgment_hearing_scheduled
```
🔎 **说明** 追踪「当前听证日期值」首次出现的日期：按 (loanid, fcjudgment_hearing_scheduled) 分组取 MIN(dataasof)。即该听证日被首次设定之日，而非听证日本身。属规则 **b 首见追踪**——详 [doc 33 §2.5.1](33_fcl_table_erd.md) 详解 a 取最新 / b 首见追踪 / c 直接透传 三套规则。
▶ **示例** 贷款 7727004408：听证日 2026-08-21 在 2026-05-14 的快照首次出现 ⇒ timeline_judgement_hearing_set_date = 2026-05-14（而 Judgement = 2026-08-21）。

### 18. Judgement 判决(当前排定听证日)  (`bpms.sync_loan_foreclosure.timeline_judgement_date`)

_当前排定的判决听证日（当前值），非 fcjudgmententered（法院录入日）。_

**来源 / Source (L1)**
- Newrez: `newrez.portnewrezfc.fcjudgmenthearingscheduled`
- Carrington: —
- Capecodfive: —

**流动顺序 / Flow:** ①basic_data_loan_fcl → ②basic_data_loan_foreclosure → ③sync_loan_foreclosure → ④biz_data_view_loan_details_foreclosure
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `port.basic_data_loan_fcl.fcjudgment_hearing_scheduled` — rename 改名 [pool:1551](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L1551)
- 2. `port.basic_data_loan_foreclosure.timeline_judgement_date` — direct copy (current value) 直传 [pool:265](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L265)
- 3. `bpms.sync_loan_foreclosure.timeline_judgement_date` — upsert pass-through [asset:763](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L763)
- 4. `bpms.biz_data_view_loan_details_foreclosure` · timeline_judgement_date (+actual/var) — view actual/var [view]

**说明 / Note:** 与 Hearing Set 同源，但取当前值（非首见）。

### 19. Sale Date Projected 预计拍卖日  (`bpms.sync_loan_foreclosure.timeline_sale_date_projected_date`)

_最新预计/排定拍卖日（动态）。_

**来源 / Source (L1)**
- Newrez: `newrez.portnewrezfc.fcscheduledsaledate`
- Carrington: `carrington.portcarrington.fcl_scheduled_sale_date`
- Capecodfive: `capecodfive.portcapecodfive_monthly_collections.foreclosure_date_sale_scheduled`

**流动顺序 / Flow:** ①basic_data_loan_fcl → ②basic_data_loan_foreclosure → ③sync_loan_foreclosure → ④biz_data_view_loan_details_foreclosure
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `port.basic_data_loan_fcl.fcscheduled_sale_date` — rename 改名 [pool:1553](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L1553)
- 2. `port.basic_data_loan_foreclosure.timeline_sale_date_projected_date` — direct copy 直传 [pool:266](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L266)
- 3. `bpms.sync_loan_foreclosure.timeline_sale_date_projected_date` — upsert pass-through [asset:764](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L764)
- 4. `bpms.biz_data_view_loan_details_foreclosure.timeline_sale_date_projected_date` — passthrough (no actual/var) [view]

### 20. Sale Date Set 拍卖排定(首见)  (`bpms.sync_loan_foreclosure.timeline_sale_date_set_date`)

_当前排定拍卖值在快照中首次出现日（ETL 追踪）。_

**来源 / Source (L1)**
- Newrez: `newrez.portnewrezfc.fcscheduledsaledate`
- Carrington: `carrington.portcarrington.fcl_scheduled_sale_date`
- Capecodfive: `capecodfive.portcapecodfive_monthly_collections.foreclosure_date_sale_scheduled`

**流动顺序 / Flow:** ①basic_data_loan_fcl → ②basic_data_loan_foreclosure → ③sync_loan_foreclosure → ④biz_data_view_loan_details_foreclosure
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `port.basic_data_loan_fcl.fcscheduled_sale_date` — rename 改名 [pool:1553](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L1553)
- 2. `port.basic_data_loan_foreclosure.timeline_sale_date_set_date` — ETL tracking: min(dataasof) of current value 首见日（按 (loanid, fcscheduled_sale_date) 分组取 MIN(dataasof)，再 join 当前值）[pool:266-303](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L266-L303)
- 3. `bpms.sync_loan_foreclosure.timeline_sale_date_set_date` — upsert pass-through [asset:765](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L765)
- 4. `bpms.biz_data_view_loan_details_foreclosure` · timeline_sale_date_set_date (+actual/var) — view actual/var [view]

```sql
-- Redshift GEN_FCL_DETAIL 投影 [basic_data_pool_config.py pool:266-303]
fc.fcscheduled_sale_date AS timeline_sale_date_projected_date,  -- pool:266  projected = 排定日「值」(当前)
sa.sa_set_date           AS timeline_sale_date_set_date         -- pool:267  set_date  = 该值「首见」dataasof
LEFT JOIN (
  SELECT loanid, fcscheduled_sale_date, MIN(dataasof) AS sa_set_date   -- pool:300
  FROM port.basic_data_loan_fcl
  WHERE fcscheduled_sale_date IS NOT NULL
  GROUP BY loanid, fcscheduled_sale_date                              -- pool:301
) sa ON fc.loanid = sa.loanid AND fc.fcscheduled_sale_date = sa.fcscheduled_sale_date  -- pool:303
```
🔎 **说明** 与 Hearing Set 同理，针对排定拍卖日：按 (loanid, fcscheduled_sale_date) 取 MIN(dataasof)。即当前拍卖日被首次排定之日。属规则 **b 首见追踪**——详 [doc 33 §2.5.1](33_fcl_table_erd.md)（3 套规则 + 7727003984 真例含 12 次改期）。
▶ **示例** MCP 实证 Loan 7727003984（改期 12 次，prod 2026-06-11）：当前 fcscheduled_sale_date = 2026-06-30，该值在 2026-05-22 快照首次出现 ⇒ timeline_sale_date_set_date = 2026-05-22（Sale Date Projected 仍为 2026-06-30）。BPS UI Sale Date Projected = 2026-06-30 / Sale Date Set = 2026-05-22——一字不差。

### 21. Final Title Cleared 最终产权清查  (`bpms.sync_loan_foreclosure.timeline_final_title_cleared_date`)

_最终产权清查日。_

> ⚠ newrez_empty

**来源 / Source (L1)**
- Newrez: `newrez.portnewrezfc.titlecleardate`
- Carrington: —
- Capecodfive: —

**流动顺序 / Flow:** ①basic_data_loan_fcl → ②basic_data_loan_foreclosure → ③sync_loan_foreclosure → ④biz_data_view_loan_details_foreclosure
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `port.basic_data_loan_fcl.titlecleardate` — rename 改名 [pool:1541](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L1541)
- 2. `port.basic_data_loan_foreclosure.timeline_final_title_cleared_date` — direct copy 直传 [pool:268](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L268)
- 3. `bpms.sync_loan_foreclosure.timeline_final_title_cleared_date` — upsert pass-through [asset:766](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L766)
- 4. `bpms.biz_data_view_loan_details_foreclosure` · timeline_final_title_cleared_date (+actual/var) — view actual/var [view]

**说明 / Note:** 与 Preliminary 共用 titlecleardate；Newrez 不填充。

### 22. Sale Held 实际拍卖  (`bpms.sync_loan_foreclosure.timeline_sale_date_held_date`)

_实际拍卖举行日。_

**来源 / Source (L1)**
- Newrez: `newrez.portnewrezfc.fcsalehelddate`
- Carrington: `carrington.portcarrington.fcl_sale_held_date`
- Capecodfive: `capecodfive.portcapecodfive_monthly_collections.foreclosure_sale_date`

**流动顺序 / Flow:** ①basic_data_loan_fcl → ②basic_data_loan_foreclosure → ③sync_loan_foreclosure → ④biz_data_view_loan_details_foreclosure
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `port.basic_data_loan_fcl.fcsale_held_date` — rename 改名 [pool:1554](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L1554)
- 2. `port.basic_data_loan_foreclosure.timeline_sale_date_held_date` — direct copy 直传 [pool:269](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L269)
- 3. `bpms.sync_loan_foreclosure.timeline_sale_date_held_date` — upsert pass-through [asset:767](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L767)
- 4. `bpms.biz_data_view_loan_details_foreclosure` · timeline_sale_date_held_date (+actual/var) — view actual/var [view]

### 23. 止赎完成日期  (`bpms.sync_loan_foreclosure.timeline_foreclosure_completed_date`)

_保留里程碑；FCL ETL 未填充。_

> ⚠ null_in_build

**来源 / Source (L1)**
- Newrez: `port.basic_data_loan_foreclosure.timeline_foreclosure_completed_date`  （仅 Newrez 提供此明细）

**流动顺序 / Flow:** ①basic_data_loan_foreclosure → ②sync_loan_foreclosure → ③biz_data_view_loan_details_foreclosure
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `port.basic_data_loan_foreclosure.timeline_foreclosure_completed_date` — not in GEN_FCL_DETAIL INSERT → NULL 未填充 [pool:148-305](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L148-305)
- 2. `bpms.sync_loan_foreclosure.timeline_foreclosure_completed_date` — GEN_FORECLOSURE 直传（值=NULL） [asset:540-605](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L540-605)
- 3. `bpms.biz_data_view_loan_details_foreclosure.timeline_foreclosure_completed_date` — passthrough [view]

### 24. 第三方成交日  (`bpms.sync_loan_foreclosure.timeline_third_party_sold_date_date`)

_第三方买家成交日。_

> ⚠ null_in_build

**来源 / Source (L1)**
- Newrez: —
- Carrington: —
- Capecodfive: —

**流动顺序 / Flow:** ①basic_data_loan_fcl → ②basic_data_loan_foreclosure → ③sync_loan_foreclosure → ④biz_data_view_loan_details_foreclosure
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `port.basic_data_loan_fcl` — —
- 2. `port.basic_data_loan_foreclosure.timeline_third_party_sold_date_date` — null 常量空 [pool:270](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L270)
- 3. `bpms.sync_loan_foreclosure.timeline_third_party_sold_date_date` — upsert pass-through [asset:769](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L769)
- 4. `bpms.biz_data_view_loan_details_foreclosure.timeline_third_party_sold_date_date` — passthrough [view]

**说明 / Note:** GEN_FCL_DETAIL 中硬编码 NULL（此处未从 raw 映射）。

### 25. 第三方拍卖款到账日  (`bpms.sync_loan_foreclosure.timeline_third_party_proceeds_received_date`)

_第三方拍卖款到账日。_

> ⚠ newrez_empty

**来源 / Source (L1)**
- Newrez: `newrez.portnewrezfc.fcl3rdpartyproceedsreceiveddate`
- Carrington: —
- Capecodfive: —

**流动顺序 / Flow:** ①basic_data_loan_fcl → ②basic_data_loan_foreclosure → ③sync_loan_foreclosure → ④biz_data_view_loan_details_foreclosure
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `port.basic_data_loan_fcl.fcl3rdpartyproceedsreceiveddate` — rename 改名 [pool:1558](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L1558)
- 2. `port.basic_data_loan_foreclosure.timeline_third_party_proceeds_received_date` — direct copy 直传 [pool:271](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L271)
- 3. `bpms.sync_loan_foreclosure.timeline_third_party_proceeds_received_date` — upsert pass-through [asset:770](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L770)
- 4. `bpms.biz_data_view_loan_details_foreclosure.timeline_third_party_proceeds_received_date` — passthrough [view]


## 目标天数（配置；视图默认）

### 26. 通知意向目标天数，默认值：30  (`bpms.sync_loan_foreclosure.target_notice_of_intent_days`)

_该里程碑的目标天数（配置常量）。_

> ⚠ view_default

**来源 / Source (L1)**
- Newrez: `port.basic_data_loan_foreclosure.target_notice_of_intent_days`  （仅 Newrez 提供此明细）

**流动顺序 / Flow:** ①basic_data_loan_foreclosure → ②sync_loan_foreclosure → ③biz_data_view_loan_details_foreclosure
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `port.basic_data_loan_foreclosure.target_notice_of_intent_days` — NULL (not populated) [pool:174-188](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L174-188)
- 2. `bpms.sync_loan_foreclosure.target_notice_of_intent_days` — GEN_FORECLOSURE: target_* commented out → NULL [asset:564-577](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L564-577)
- 3. `bpms.biz_data_view_loan_details_foreclosure.target_notice_of_intent_days` — ifnull(target_notice_of_intent_days, <default>) — view default constant [view]

**说明 / Note:** sync 中存 NULL；视图给默认 target（如 first_legal 120、service 90、judgement 30）。

### 27. 通知意向过期目标天数，默认值：90  (`bpms.sync_loan_foreclosure.target_notice_of_intent_expired_days`)

_该里程碑的目标天数（配置常量）。_

> ⚠ view_default

**来源 / Source (L1)**
- Newrez: `port.basic_data_loan_foreclosure.target_notice_of_intent_expired_days`  （仅 Newrez 提供此明细）

**流动顺序 / Flow:** ①basic_data_loan_foreclosure → ②sync_loan_foreclosure → ③biz_data_view_loan_details_foreclosure
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `port.basic_data_loan_foreclosure.target_notice_of_intent_expired_days` — NULL (not populated) [pool:174-188](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L174-188)
- 2. `bpms.sync_loan_foreclosure.target_notice_of_intent_expired_days` — GEN_FORECLOSURE: target_* commented out → NULL [asset:564-577](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L564-577)
- 3. `bpms.biz_data_view_loan_details_foreclosure.target_notice_of_intent_expired_days` — ifnull(target_notice_of_intent_expired_days, <default>) — view default constant [view]

**说明 / Note:** sync 中存 NULL；视图给默认 target（如 first_legal 120、service 90、judgement 30）。

### 28. 批准转交目标天数，默认值：30  (`bpms.sync_loan_foreclosure.target_approved_for_referral_days`)

_该里程碑的目标天数（配置常量）。_

> ⚠ view_default

**来源 / Source (L1)**
- Newrez: `port.basic_data_loan_foreclosure.target_approved_for_referral_days`  （仅 Newrez 提供此明细）

**流动顺序 / Flow:** ①basic_data_loan_foreclosure → ②sync_loan_foreclosure → ③biz_data_view_loan_details_foreclosure
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `port.basic_data_loan_foreclosure.target_approved_for_referral_days` — NULL (not populated) [pool:174-188](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L174-188)
- 2. `bpms.sync_loan_foreclosure.target_approved_for_referral_days` — GEN_FORECLOSURE: target_* commented out → NULL [asset:564-577](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L564-577)
- 3. `bpms.biz_data_view_loan_details_foreclosure.target_approved_for_referral_days` — ifnull(target_approved_for_referral_days, <default>) — view default constant [view]

**说明 / Note:** sync 中存 NULL；视图给默认 target（如 first_legal 120、service 90、judgement 30）。

### 29. 转交律师目标天数，默认值：1  (`bpms.sync_loan_foreclosure.target_referred_to_attorney_days`)

_该里程碑的目标天数（配置常量）。_

> ⚠ view_default

**来源 / Source (L1)**
- Newrez: `port.basic_data_loan_foreclosure.target_referred_to_attorney_days`  （仅 Newrez 提供此明细）

**流动顺序 / Flow:** ①basic_data_loan_foreclosure → ②sync_loan_foreclosure → ③biz_data_view_loan_details_foreclosure
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `port.basic_data_loan_foreclosure.target_referred_to_attorney_days` — NULL (not populated) [pool:174-188](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L174-188)
- 2. `bpms.sync_loan_foreclosure.target_referred_to_attorney_days` — GEN_FORECLOSURE: target_* commented out → NULL [asset:564-577](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L564-577)
- 3. `bpms.biz_data_view_loan_details_foreclosure.target_referred_to_attorney_days` — ifnull(target_referred_to_attorney_days, <default>) — view default constant [view]

**说明 / Note:** sync 中存 NULL；视图给默认 target（如 first_legal 120、service 90、judgement 30）。

### 30. 转交止赎目标天数，默认值：1  (`bpms.sync_loan_foreclosure.target_referred_to_foreclosure_days`)

_该里程碑的目标天数（配置常量）。_

> ⚠ view_default

**来源 / Source (L1)**
- Newrez: `port.basic_data_loan_foreclosure.target_referred_to_foreclosure_days`  （仅 Newrez 提供此明细）

**流动顺序 / Flow:** ①basic_data_loan_foreclosure → ②sync_loan_foreclosure → ③biz_data_view_loan_details_foreclosure
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `port.basic_data_loan_foreclosure.target_referred_to_foreclosure_days` — NULL (not populated) [pool:174-188](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L174-188)
- 2. `bpms.sync_loan_foreclosure.target_referred_to_foreclosure_days` — GEN_FORECLOSURE: target_* commented out → NULL [asset:564-577](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L564-577)
- 3. `bpms.biz_data_view_loan_details_foreclosure.target_referred_to_foreclosure_days` — ifnull(target_referred_to_foreclosure_days, <default>) — view default constant [view]

**说明 / Note:** sync 中存 NULL；视图给默认 target（如 first_legal 120、service 90、judgement 30）。

### 31. 收到产权报告目标天数，默认值：30  (`bpms.sync_loan_foreclosure.target_title_report_received_days`)

_该里程碑的目标天数（配置常量）。_

> ⚠ view_default

**来源 / Source (L1)**
- Newrez: `port.basic_data_loan_foreclosure.target_title_report_received_days`  （仅 Newrez 提供此明细）

**流动顺序 / Flow:** ①basic_data_loan_foreclosure → ②sync_loan_foreclosure → ③biz_data_view_loan_details_foreclosure
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `port.basic_data_loan_foreclosure.target_title_report_received_days` — NULL (not populated) [pool:174-188](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L174-188)
- 2. `bpms.sync_loan_foreclosure.target_title_report_received_days` — GEN_FORECLOSURE: target_* commented out → NULL [asset:564-577](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L564-577)
- 3. `bpms.biz_data_view_loan_details_foreclosure.target_title_report_received_days` — ifnull(target_title_report_received_days, <default>) — view default constant [view]

**说明 / Note:** sync 中存 NULL；视图给默认 target（如 first_legal 120、service 90、judgement 30）。

### 32. 初步产权清理完成目标天数，默认值：30  (`bpms.sync_loan_foreclosure.target_preliminary_title_cleared_days`)

_该里程碑的目标天数（配置常量）。_

> ⚠ view_default

**来源 / Source (L1)**
- Newrez: `port.basic_data_loan_foreclosure.target_preliminary_title_cleared_days`  （仅 Newrez 提供此明细）

**流动顺序 / Flow:** ①basic_data_loan_foreclosure → ②sync_loan_foreclosure → ③biz_data_view_loan_details_foreclosure
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `port.basic_data_loan_foreclosure.target_preliminary_title_cleared_days` — NULL (not populated) [pool:174-188](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L174-188)
- 2. `bpms.sync_loan_foreclosure.target_preliminary_title_cleared_days` — GEN_FORECLOSURE: target_* commented out → NULL [asset:564-577](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L564-577)
- 3. `bpms.biz_data_view_loan_details_foreclosure.target_preliminary_title_cleared_days` — ifnull(target_preliminary_title_cleared_days, <default>) — view default constant [view]

**说明 / Note:** sync 中存 NULL；视图给默认 target（如 first_legal 120、service 90、judgement 30）。

### 33. 初次法律行动目标天数，默认值：120  (`bpms.sync_loan_foreclosure.target_first_legal_days`)

_该里程碑的目标天数（配置常量）。_

> ⚠ view_default

**来源 / Source (L1)**
- Newrez: `port.basic_data_loan_foreclosure.target_first_legal_days`  （仅 Newrez 提供此明细）

**流动顺序 / Flow:** ①basic_data_loan_foreclosure → ②sync_loan_foreclosure → ③biz_data_view_loan_details_foreclosure
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `port.basic_data_loan_foreclosure.target_first_legal_days` — NULL (not populated) [pool:174-188](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L174-188)
- 2. `bpms.sync_loan_foreclosure.target_first_legal_days` — GEN_FORECLOSURE: target_* commented out → NULL [asset:564-577](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L564-577)
- 3. `bpms.biz_data_view_loan_details_foreclosure.target_first_legal_days` — ifnull(target_first_legal_days, <default>) — view default constant [view]

**说明 / Note:** sync 中存 NULL；视图给默认 target（如 first_legal 120、service 90、judgement 30）。

### 34. 服务完成目标天数，默认值：90  (`bpms.sync_loan_foreclosure.target_service_days`)

_该里程碑的目标天数（配置常量）。_

> ⚠ view_default

**来源 / Source (L1)**
- Newrez: `port.basic_data_loan_foreclosure.target_service_days`  （仅 Newrez 提供此明细）

**流动顺序 / Flow:** ①basic_data_loan_foreclosure → ②sync_loan_foreclosure → ③biz_data_view_loan_details_foreclosure
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `port.basic_data_loan_foreclosure.target_service_days` — NULL (not populated) [pool:174-188](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L174-188)
- 2. `bpms.sync_loan_foreclosure.target_service_days` — GEN_FORECLOSURE: target_* commented out → NULL [asset:564-577](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L564-577)
- 3. `bpms.biz_data_view_loan_details_foreclosure.target_service_days` — ifnull(target_service_days, <default>) — view default constant [view]

**说明 / Note:** sync 中存 NULL；视图给默认 target（如 first_legal 120、service 90、judgement 30）。

### 35. publication目标天数，默认值：30  (`bpms.sync_loan_foreclosure.target_publication_days`)

_该里程碑的目标天数（配置常量）。_

> ⚠ view_default

**来源 / Source (L1)**
- Newrez: `port.basic_data_loan_foreclosure.target_publication_days`  （仅 Newrez 提供此明细）

**流动顺序 / Flow:** ①basic_data_loan_foreclosure → ②sync_loan_foreclosure → ③biz_data_view_loan_details_foreclosure
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `port.basic_data_loan_foreclosure.target_publication_days` — NULL (not populated) [pool:174-188](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L174-188)
- 2. `bpms.sync_loan_foreclosure.target_publication_days` — GEN_FORECLOSURE: target_* commented out → NULL [asset:564-577](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L564-577)
- 3. `bpms.biz_data_view_loan_details_foreclosure.target_publication_days` — ifnull(target_publication_days, <default>) — view default constant [view]

**说明 / Note:** sync 中存 NULL；视图给默认 target（如 first_legal 120、service 90、judgement 30）。

### 36. 判决听证会设置目标天数，默认值：120  (`bpms.sync_loan_foreclosure.target_judgement_hearing_set_days`)

_该里程碑的目标天数（配置常量）。_

> ⚠ view_default

**来源 / Source (L1)**
- Newrez: `port.basic_data_loan_foreclosure.target_judgement_hearing_set_days`  （仅 Newrez 提供此明细）

**流动顺序 / Flow:** ①basic_data_loan_foreclosure → ②sync_loan_foreclosure → ③biz_data_view_loan_details_foreclosure
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `port.basic_data_loan_foreclosure.target_judgement_hearing_set_days` — NULL (not populated) [pool:174-188](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L174-188)
- 2. `bpms.sync_loan_foreclosure.target_judgement_hearing_set_days` — GEN_FORECLOSURE: target_* commented out → NULL [asset:564-577](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L564-577)
- 3. `bpms.biz_data_view_loan_details_foreclosure.target_judgement_hearing_set_days` — ifnull(target_judgement_hearing_set_days, <default>) — view default constant [view]

**说明 / Note:** sync 中存 NULL；视图给默认 target（如 first_legal 120、service 90、judgement 30）。

### 37. 判决发布目标天数，默认值：30  (`bpms.sync_loan_foreclosure.target_judgement_days`)

_该里程碑的目标天数（配置常量）。_

> ⚠ view_default

**来源 / Source (L1)**
- Newrez: `port.basic_data_loan_foreclosure.target_judgement_days`  （仅 Newrez 提供此明细）

**流动顺序 / Flow:** ①basic_data_loan_foreclosure → ②sync_loan_foreclosure → ③biz_data_view_loan_details_foreclosure
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `port.basic_data_loan_foreclosure.target_judgement_days` — NULL (not populated) [pool:174-188](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L174-188)
- 2. `bpms.sync_loan_foreclosure.target_judgement_days` — GEN_FORECLOSURE: target_* commented out → NULL [asset:564-577](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L564-577)
- 3. `bpms.biz_data_view_loan_details_foreclosure.target_judgement_days` — ifnull(target_judgement_days, <default>) — view default constant [view]

**说明 / Note:** sync 中存 NULL；视图给默认 target（如 first_legal 120、service 90、judgement 30）。

### 38. 实际设定出售目标天数，默认值：30  (`bpms.sync_loan_foreclosure.target_sale_date_set_days`)

_该里程碑的目标天数（配置常量）。_

> ⚠ view_default

**来源 / Source (L1)**
- Newrez: `port.basic_data_loan_foreclosure.target_sale_date_set_days`  （仅 Newrez 提供此明细）

**流动顺序 / Flow:** ①basic_data_loan_foreclosure → ②sync_loan_foreclosure → ③biz_data_view_loan_details_foreclosure
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `port.basic_data_loan_foreclosure.target_sale_date_set_days` — NULL (not populated) [pool:174-188](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L174-188)
- 2. `bpms.sync_loan_foreclosure.target_sale_date_set_days` — GEN_FORECLOSURE: target_* commented out → NULL [asset:564-577](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L564-577)
- 3. `bpms.biz_data_view_loan_details_foreclosure.target_sale_date_set_days` — ifnull(target_sale_date_set_days, <default>) — view default constant [view]

**说明 / Note:** sync 中存 NULL；视图给默认 target（如 first_legal 120、service 90、judgement 30）。

### 39. 最终产权清理完成目标天数，默认值：5  (`bpms.sync_loan_foreclosure.target_final_title_cleared_days`)

_该里程碑的目标天数（配置常量）。_

> ⚠ view_default

**来源 / Source (L1)**
- Newrez: `port.basic_data_loan_foreclosure.target_final_title_cleared_days`  （仅 Newrez 提供此明细）

**流动顺序 / Flow:** ①basic_data_loan_foreclosure → ②sync_loan_foreclosure → ③biz_data_view_loan_details_foreclosure
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `port.basic_data_loan_foreclosure.target_final_title_cleared_days` — NULL (not populated) [pool:174-188](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L174-188)
- 2. `bpms.sync_loan_foreclosure.target_final_title_cleared_days` — GEN_FORECLOSURE: target_* commented out → NULL [asset:564-577](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L564-577)
- 3. `bpms.biz_data_view_loan_details_foreclosure.target_final_title_cleared_days` — ifnull(target_final_title_cleared_days, <default>) — view default constant [view]

**说明 / Note:** sync 中存 NULL；视图给默认 target（如 first_legal 120、service 90、judgement 30）。

### 40. 实际出售目标天数，默认值：0  (`bpms.sync_loan_foreclosure.target_sale_date_held_days`)

_该里程碑的目标天数（配置常量）。_

> ⚠ view_default

**来源 / Source (L1)**
- Newrez: `port.basic_data_loan_foreclosure.target_sale_date_held_days`  （仅 Newrez 提供此明细）

**流动顺序 / Flow:** ①basic_data_loan_foreclosure → ②sync_loan_foreclosure → ③biz_data_view_loan_details_foreclosure
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `port.basic_data_loan_foreclosure.target_sale_date_held_days` — NULL (not populated) [pool:174-188](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L174-188)
- 2. `bpms.sync_loan_foreclosure.target_sale_date_held_days` — GEN_FORECLOSURE: target_* commented out → NULL [asset:564-577](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L564-577)
- 3. `bpms.biz_data_view_loan_details_foreclosure.target_sale_date_held_days` — ifnull(target_sale_date_held_days, <default>) — view default constant [view]

**说明 / Note:** sync 中存 NULL；视图给默认 target（如 first_legal 120、service 90、judgement 30）。


## Variance 列

### 41. 当前破产标志，1 表示是，0 表示否  (`bpms.sync_loan_foreclosure.variance_active_bankruptcy`)

_Schema 中有，但 FCL ETL 未填充。_

> ⚠ null_in_build

**来源 / Source (L1)**
- Newrez: `port.basic_data_loan_foreclosure.variance_active_bankruptcy`  （仅 Newrez 提供此明细）

**流动顺序 / Flow:** ①basic_data_loan_foreclosure → ②sync_loan_foreclosure → ③biz_data_view_loan_details_foreclosure
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `port.basic_data_loan_foreclosure.variance_active_bankruptcy` — not in GEN_FCL_DETAIL INSERT → NULL 未填充 [pool:148-305](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L148-305)
- 2. `bpms.sync_loan_foreclosure.variance_active_bankruptcy` — GEN_FORECLOSURE 直传（值=NULL） [asset:540-605](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L540-605)
- 3. `bpms.biz_data_view_loan_details_foreclosure.variance_active_bankruptcy` — passthrough [view]

### 42. 完成破产标志，1 表示是，0 表示否  (`bpms.sync_loan_foreclosure.variance_completed_bankruptcy`)

_Schema 中有，但 FCL ETL 未填充。_

> ⚠ null_in_build

**来源 / Source (L1)**
- Newrez: `port.basic_data_loan_foreclosure.variance_completed_bankruptcy`  （仅 Newrez 提供此明细）

**流动顺序 / Flow:** ①basic_data_loan_foreclosure → ②sync_loan_foreclosure → ③biz_data_view_loan_details_foreclosure
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `port.basic_data_loan_foreclosure.variance_completed_bankruptcy` — not in GEN_FCL_DETAIL INSERT → NULL 未填充 [pool:148-305](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L148-305)
- 2. `bpms.sync_loan_foreclosure.variance_completed_bankruptcy` — GEN_FORECLOSURE 直传（值=NULL） [asset:540-605](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L540-605)
- 3. `bpms.biz_data_view_loan_details_foreclosure.variance_completed_bankruptcy` — passthrough [view]

### 43. 预计持有天数  (`bpms.sync_loan_foreclosure.variance_estimated_hold_days`)

_Schema 中有，但 FCL ETL 未填充。_

> ⚠ null_in_build

**来源 / Source (L1)**
- Newrez: `port.basic_data_loan_foreclosure.variance_estimated_hold_days`  （仅 Newrez 提供此明细）

**流动顺序 / Flow:** ①basic_data_loan_foreclosure → ②sync_loan_foreclosure → ③biz_data_view_loan_details_foreclosure
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `port.basic_data_loan_foreclosure.variance_estimated_hold_days` — not in GEN_FCL_DETAIL INSERT → NULL 未填充 [pool:148-305](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L148-305)
- 2. `bpms.sync_loan_foreclosure.variance_estimated_hold_days` — GEN_FORECLOSURE 直传（值=NULL） [asset:540-605](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L540-605)
- 3. `bpms.biz_data_view_loan_details_foreclosure.variance_estimated_hold_days` — passthrough [view]

### 44. 破产总数  (`bpms.sync_loan_foreclosure.variance_bankruptcies`)

_Schema 中有，但 FCL ETL 未填充。_

> ⚠ null_in_build

**来源 / Source (L1)**
- Newrez: `port.basic_data_loan_foreclosure.variance_bankruptcies`  （仅 Newrez 提供此明细）

**流动顺序 / Flow:** ①basic_data_loan_foreclosure → ②sync_loan_foreclosure → ③biz_data_view_loan_details_foreclosure
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `port.basic_data_loan_foreclosure.variance_bankruptcies` — not in GEN_FCL_DETAIL INSERT → NULL 未填充 [pool:148-305](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L148-305)
- 2. `bpms.sync_loan_foreclosure.variance_bankruptcies` — GEN_FORECLOSURE 直传（值=NULL） [asset:540-605](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L540-605)
- 3. `bpms.biz_data_view_loan_details_foreclosure.variance_bankruptcies` — passthrough [view]


## Bid Approval 列

### 45. 审批状态  (`bpms.sync_loan_foreclosure.bid_approval_status`)

_Schema 中有，但 FCL ETL 未填充。_

> ⚠ null_in_build

**来源 / Source (L1)**
- Newrez: `port.basic_data_loan_foreclosure.bid_approval_status`  （仅 Newrez 提供此明细）

**流动顺序 / Flow:** ①basic_data_loan_foreclosure → ②sync_loan_foreclosure → ③biz_data_view_loan_details_foreclosure
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `port.basic_data_loan_foreclosure.bid_approval_status` — not in GEN_FCL_DETAIL INSERT → NULL 未填充 [pool:148-305](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L148-305)
- 2. `bpms.sync_loan_foreclosure.bid_approval_status` — GEN_FORECLOSURE 直传（值=NULL） [asset:540-605](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L540-605)
- 3. `bpms.biz_data_view_loan_details_foreclosure.bid_approval_status` — passthrough [view]

### 46. 销售日期  (`bpms.sync_loan_foreclosure.bid_approval_sale_date`)

_Schema 中有，但 FCL ETL 未填充。_

> ⚠ null_in_build

**来源 / Source (L1)**
- Newrez: `port.basic_data_loan_foreclosure.bid_approval_sale_date`  （仅 Newrez 提供此明细）

**流动顺序 / Flow:** ①basic_data_loan_foreclosure → ②sync_loan_foreclosure → ③biz_data_view_loan_details_foreclosure
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `port.basic_data_loan_foreclosure.bid_approval_sale_date` — not in GEN_FCL_DETAIL INSERT → NULL 未填充 [pool:148-305](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L148-305)
- 2. `bpms.sync_loan_foreclosure.bid_approval_sale_date` — GEN_FORECLOSURE 直传（值=NULL） [asset:540-605](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L540-605)
- 3. `bpms.biz_data_view_loan_details_foreclosure.bid_approval_sale_date` — passthrough [view]

### 47. 投标金额  (`bpms.sync_loan_foreclosure.bid_approval_bid_amount`)

_止赎竞价金额（与 summary_foreclosure_bid_amount 同源）。_

**来源 / Source (L1)**
- Newrez: `newrez.portnewrezfc.fcbidamount`  （仅 Newrez 提供此明细）

**流动顺序 / Flow:** ①portnewrezfc → ②basic_data_loan_fcl → ③basic_data_loan_foreclosure → ④sync_loan_foreclosure → ⑤biz_data_view_loan_details_foreclosure
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `newrez.portnewrezfc.fcbidamount` — servicer raw
- 2. `port.basic_data_loan_fcl.fcbidamount` — rename
- 3. `port.basic_data_loan_foreclosure.bid_approval_bid_amount` — = fcbidamount [pool:272](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L272)
- 4. `bpms.sync_loan_foreclosure.bid_approval_bid_amount` — passthrough [asset]
- 5. `bpms.biz_data_view_loan_details_foreclosure.bid_approval_bid_amount` — passthrough [view]

### 48. 贷款决议阻滞说明  (`bpms.sync_loan_foreclosure.bid_approval_loan_resolution_holods`)

_Schema 中有，但 FCL ETL 未填充。_

> ⚠ null_in_build

**来源 / Source (L1)**
- Newrez: `port.basic_data_loan_foreclosure.bid_approval_loan_resolution_holods`  （仅 Newrez 提供此明细）

**流动顺序 / Flow:** ①basic_data_loan_foreclosure → ②sync_loan_foreclosure → ③biz_data_view_loan_details_foreclosure
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `port.basic_data_loan_foreclosure.bid_approval_loan_resolution_holods` — not in GEN_FCL_DETAIL INSERT → NULL 未填充 [pool:148-305](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L148-305)
- 2. `bpms.sync_loan_foreclosure.bid_approval_loan_resolution_holods` — GEN_FORECLOSURE 直传（值=NULL） [asset:540-605](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L540-605)
- 3. `bpms.biz_data_view_loan_details_foreclosure.bid_approval_loan_resolution_holods` — passthrough [view]


## 汇总 / 状态

### 49. 服务商编号标识  (`bpms.sync_loan_foreclosure.summary_servicer_number`)

_Schema 中有，但 FCL ETL 未填充。_

> ⚠ null_in_build

**来源 / Source (L1)**
- Newrez: `port.basic_data_loan_foreclosure.summary_servicer_number`  （仅 Newrez 提供此明细）

**流动顺序 / Flow:** ①basic_data_loan_foreclosure → ②sync_loan_foreclosure → ③biz_data_view_loan_details_foreclosure
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `port.basic_data_loan_foreclosure.summary_servicer_number` — not in GEN_FCL_DETAIL INSERT → NULL 未填充 [pool:148-305](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L148-305)
- 2. `bpms.sync_loan_foreclosure.summary_servicer_number` — GEN_FORECLOSURE 直传（值=NULL） [asset:540-605](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L540-605)
- 3. `bpms.biz_data_view_loan_details_foreclosure.summary_servicer_number` — passthrough [view]

### 50. Foreclosure Status 止赎状态  (`bpms.sync_loan_foreclosure.summary_foreclosure_status`)

_进行中 vs 已关闭（+原因）。_

**来源 / Source (L1)**
- Newrez: `newrez.portnewrezfc.activefcflag + fcremovaldesc`
- Carrington: `carrington.portcarrington.fcl_flag`
- Capecodfive: `capecodfive.portcapecodfive_monthly_collections.foreclosure_flag`

**流动顺序 / Flow:** ①basic_data_loan_fcl → ②basic_data_loan_foreclosure → ③sync_loan_foreclosure → ④biz_data_view_loan_details_foreclosure
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `port.basic_data_loan_fcl` · activefcflag, fcremovaldesc — activefcflag=cast(int); fcremovaldesc rename [pool:1538,1563](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L1538)
- 2. `port.basic_data_loan_foreclosure.summary_foreclosure_status` — CASE active/closed 见 sql [pool:273](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L273)
- 3. `bpms.sync_loan_foreclosure.summary_foreclosure_status` — upsert pass-through [asset:730/780](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L730)
- 4. `bpms.biz_data_view_loan_details_foreclosure.summary_foreclosure_status` — passthrough [view]

**规则（完整）/ Rule (full):** 各 servicer 先各自构建输入，再走同一个 CASE 生成文本。**Newrez**：直接取 `activefcflag`(0/1) 与 `fcremovaldesc`。**Carrington**：无 `activefcflag` 列 → `activefcflag = CASE WHEN fcl_flag='Active' THEN 1 ELSE NULL`（[pool:1579](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L1579)）；`fcremovaldesc` 为 NULL。**Capecodfive**：`activefcflag = CASE WHEN foreclosure_flag='Active' THEN 1 ELSE NULL`（[pool:1620](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L1620)）。**共用规则**：`CASE WHEN activefcflag=1 THEN 'Active Foreclosure' WHEN activefcflag=0 AND fcremovaldesc<>'' THEN CONCAT('Closed Foreclosure:',fcremovaldesc) ELSE NULL`（[pool:273](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L273)）。

```sql
CASE WHEN activefcflag=1 THEN 'Active Foreclosure' WHEN activefcflag=0 AND fcremovaldesc IS NOT NULL AND fcremovaldesc!='' THEN CONCAT('Closed Foreclosure:', fcremovaldesc) ELSE null END
```
🔎 **说明** activefcflag=1 ⇒ 固定文本 'Active Foreclosure'。activefcflag=0 且 fcremovaldesc 非空 ⇒ 'Closed Foreclosure:'+fcremovaldesc（退出原因）。否则 NULL。（注意：关闭文本取 fcremovaldesc，非 fcstage。）
▶ **示例** 7727004408：activefcflag=1 ⇒ 'Active Foreclosure'。已关闭贷款 activefcflag=0、fcremovaldesc='Paid in Full' ⇒ 'Closed Foreclosure:Paid in Full'。

### 51. 完成止赎标志  (`bpms.sync_loan_foreclosure.summary_completed_foreclosure`)

_Schema 中有，但 FCL ETL 未填充。_

> ⚠ null_in_build

**来源 / Source (L1)**
- Newrez: `port.basic_data_loan_foreclosure.summary_completed_foreclosure`  （仅 Newrez 提供此明细）

**流动顺序 / Flow:** ①basic_data_loan_foreclosure → ②sync_loan_foreclosure → ③biz_data_view_loan_details_foreclosure
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `port.basic_data_loan_foreclosure.summary_completed_foreclosure` — not in GEN_FCL_DETAIL INSERT → NULL 未填充 [pool:148-305](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L148-305)
- 2. `bpms.sync_loan_foreclosure.summary_completed_foreclosure` — GEN_FORECLOSURE 直传（值=NULL） [asset:540-605](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L540-605)
- 3. `bpms.biz_data_view_loan_details_foreclosure.summary_completed_foreclosure` — passthrough [view]

### 52. 止赎竞价金额  (`bpms.sync_loan_foreclosure.summary_foreclosure_bid_amount`)

_止赎竞价金额。_

**来源 / Source (L1)**
- Newrez: `newrez.portnewrezfc.fcbidamount`
- Carrington: —
- Capecodfive: —

**流动顺序 / Flow:** ①basic_data_loan_fcl → ②basic_data_loan_foreclosure → ③sync_loan_foreclosure → ④biz_data_view_loan_details_foreclosure
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `port.basic_data_loan_fcl.fcbidamount` — rename 改名 [pool:1555](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L1555)
- 2. `port.basic_data_loan_foreclosure.summary_foreclosure_bid_amount` — direct copy 直传 [pool:274](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L274)
- 3. `bpms.sync_loan_foreclosure.summary_foreclosure_bid_amount` — upsert pass-through [asset:733/782](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L733)
- 4. `bpms.biz_data_view_loan_details_foreclosure.summary_foreclosure_bid_amount` — passthrough [view]

**说明 / Note:** 同源 fcbidamount 同时供 bid_approval_bid_amount 与 summary_srv_fc_bid_amount。

### 53. 服务商止赎竞价金额  (`bpms.sync_loan_foreclosure.summary_srv_fc_bid_amount`)

_止赎竞价金额（与 summary_foreclosure_bid_amount 同源）。_

**来源 / Source (L1)**
- Newrez: `newrez.portnewrezfc.fcbidamount`  （仅 Newrez 提供此明细）

**流动顺序 / Flow:** ①portnewrezfc → ②basic_data_loan_fcl → ③basic_data_loan_foreclosure → ④sync_loan_foreclosure → ⑤biz_data_view_loan_details_foreclosure
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `newrez.portnewrezfc.fcbidamount` — servicer raw
- 2. `port.basic_data_loan_fcl.fcbidamount` — rename
- 3. `port.basic_data_loan_foreclosure.summary_srv_fc_bid_amount` — = fcbidamount [pool:275](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L275)
- 4. `bpms.sync_loan_foreclosure.summary_srv_fc_bid_amount` — passthrough [asset]
- 5. `bpms.biz_data_view_loan_details_foreclosure.summary_srv_fc_bid_amount` — passthrough [view]

### 54. 止赎成交金额  (`bpms.sync_loan_foreclosure.summary_foreclosure_sale_amount`)

_止赎成交金额。_

**来源 / Source (L1)**
- Newrez: `newrez.portnewrezfc.fcsaleamount`
- Carrington: —
- Capecodfive: —

**流动顺序 / Flow:** ①basic_data_loan_fcl → ②basic_data_loan_foreclosure → ③sync_loan_foreclosure → ④biz_data_view_loan_details_foreclosure
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `port.basic_data_loan_fcl.fcsaleamount` — rename 改名 [pool:1557](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L1557)
- 2. `port.basic_data_loan_foreclosure.summary_foreclosure_sale_amount` — direct copy 直传 [pool:276](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L276)
- 3. `bpms.sync_loan_foreclosure.summary_foreclosure_sale_amount` — upsert pass-through [asset:734/784](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L734)
- 4. `bpms.biz_data_view_loan_details_foreclosure.summary_foreclosure_sale_amount` — passthrough [view]

### 55. Judicial Foreclosure 司法标志  (`bpms.sync_loan_foreclosure.summary_judicial_foreclosure`)

_数值司法标志。_

**来源 / Source (L1)**
- Newrez: `newrez.portnewrezfc.judicial`
- Carrington: —
- Capecodfive: —

**流动顺序 / Flow:** ①basic_data_loan_fcl → ②basic_data_loan_foreclosure → ③sync_loan_foreclosure → ④biz_data_view_loan_details_foreclosure
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `port.basic_data_loan_fcl.judicial` — rename 改名 [pool:1565](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L1565)
- 2. `port.basic_data_loan_foreclosure.summary_judicial_foreclosure` — cast(empty→null else decimal) [pool:277](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L277)
- 3. `bpms.sync_loan_foreclosure.summary_judicial_foreclosure` — upsert pass-through [asset:735/785](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L735)
- 4. `bpms.biz_data_view_loan_details_foreclosure.summary_judicial_foreclosure` — passthrough [view]

### 56. 止赎律师姓名  (`bpms.sync_loan_foreclosure.summary_foreclosure_attorney`)

_Schema 中有，但 FCL ETL 未填充。_

> ⚠ null_in_build

**来源 / Source (L1)**
- Newrez: `port.basic_data_loan_foreclosure.summary_foreclosure_attorney`  （仅 Newrez 提供此明细）

**流动顺序 / Flow:** ①basic_data_loan_foreclosure → ②sync_loan_foreclosure → ③biz_data_view_loan_details_foreclosure
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `port.basic_data_loan_foreclosure.summary_foreclosure_attorney` — not in GEN_FCL_DETAIL INSERT → NULL 未填充 [pool:148-305](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L148-305)
- 2. `bpms.sync_loan_foreclosure.summary_foreclosure_attorney` — GEN_FORECLOSURE 直传（值=NULL） [asset:540-605](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L540-605)
- 3. `bpms.biz_data_view_loan_details_foreclosure.summary_foreclosure_attorney` — passthrough [view]

### 57. Contested / Litigation 争议诉讼  (`bpms.sync_loan_foreclosure.summary_contested_litigation`)

_争议诉讼标志。_

**来源 / Source (L1)**
- Newrez: `newrez.portnewrezfc.fccontestedflag`
- Carrington: —
- Capecodfive: —

**流动顺序 / Flow:** ①basic_data_loan_fcl → ②basic_data_loan_foreclosure → ③sync_loan_foreclosure → ④biz_data_view_loan_details_foreclosure
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `port.basic_data_loan_fcl.fccontestedflag` — rename 改名 [pool:1567](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L1567)
- 2. `port.basic_data_loan_foreclosure.summary_contested_litigation` — cast(empty→null else decimal) [pool:285](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L285)
- 3. `bpms.sync_loan_foreclosure.summary_contested_litigation` — upsert pass-through [asset:737/787](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L737)
- 4. `bpms.biz_data_view_loan_details_foreclosure.summary_contested_litigation` — passthrough [view]

### 58. Firm 律所  (`bpms.sync_loan_foreclosure.summary_firm`)

_止赎律所名。_

**来源 / Source (L1)**
- Newrez: `newrez.portnewrezfc.fcfirm`
- Carrington: `carrington.portcarrington.fcl_attorney_name`
- Capecodfive: —

**流动顺序 / Flow:** ①basic_data_loan_fcl → ②basic_data_loan_foreclosure → ③sync_loan_foreclosure → ④biz_data_view_loan_details_foreclosure
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `port.basic_data_loan_fcl.fcfirm` — rename 改名 [pool:1566](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L1566)
- 2. `port.basic_data_loan_foreclosure.summary_firm` — direct copy 直传 [pool:278](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L278)
- 3. `bpms.sync_loan_foreclosure.summary_firm` — upsert pass-through [asset:738/789](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L738)
- 4. `bpms.biz_data_view_loan_details_foreclosure.summary_firm` — passthrough [view]

### 59. Type 司法/非司法  (`bpms.sync_loan_foreclosure.summary_type`)

_司法/非司法 文本。_

**来源 / Source (L1)**
- Newrez: `newrez.portnewrezfc.judicial`
- Carrington: —
- Capecodfive: —

**流动顺序 / Flow:** ①basic_data_loan_fcl → ②basic_data_loan_foreclosure → ③sync_loan_foreclosure → ④biz_data_view_loan_details_foreclosure
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `port.basic_data_loan_fcl.judicial` — rename 改名 [pool:1565](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L1565)
- 2. `port.basic_data_loan_foreclosure.summary_type` — CASE 0→Non Judicial / 1→Judicial [pool:279](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L279)
- 3. `bpms.sync_loan_foreclosure.summary_type` — upsert pass-through [asset:739/790](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L739)
- 4. `bpms.biz_data_view_loan_details_foreclosure.summary_type` — passthrough [view]

```sql
CASE WHEN judicial IS NULL OR judicial='' THEN null WHEN cast(cast(judicial AS float) as int)=0 THEN 'Non Judicial' WHEN cast(cast(judicial AS float) as int)=1 THEN 'Judicial' ELSE null END
```
🔎 **说明** 归一化 judicial 标志：NULL/空 ⇒ NULL；否则 文本→float→int，0 ⇒ 'Non Judicial'，1 ⇒ 'Judicial'。
▶ **示例** judicial='1' ⇒ 'Judicial'（7727004408）；'0' ⇒ 'Non Judicial'；'' ⇒ NULL。

### 60. SMS Days in FCL (servicer 口径)  (`bpms.sync_loan_foreclosure.summary_sms_days_in_fcl`)

_Servicer 自报 FCL 天数（自建案日起）。_

**来源 / Source (L1)**
- Newrez: `newrez.portnewrezfc.smsdaysinfc`
- Carrington: —
- Capecodfive: —

**流动顺序 / Flow:** ①basic_data_loan_fcl → ②basic_data_loan_foreclosure → ③sync_loan_foreclosure → ④biz_data_view_loan_details_foreclosure
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `port.basic_data_loan_fcl.svc_days_infc` — rename (smsdaysinfc→svc_days_infc) [pool:1545](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L1545)
- 2. `port.basic_data_loan_foreclosure.summary_sms_days_in_fcl` — direct copy 直传 [pool:280](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L280)
- 3. `bpms.sync_loan_foreclosure.summary_sms_days_in_fcl` — upsert pass-through [asset:740/791](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L740)
- 4. `bpms.biz_data_view_loan_details_foreclosure.summary_sms_days_in_fcl` — passthrough [view]

### 61. Days in FCL (投资人口径)  (`bpms.sync_loan_foreclosure.summary_days_in_fcl`)

_自转介起算的 FCL 天数（投资人口径）。_

**来源 / Source (L1)**
- Newrez: `newrez.portnewrezfc.daysinfc`
- Carrington: —
- Capecodfive: —

**流动顺序 / Flow:** ①basic_data_loan_fcl → ②basic_data_loan_foreclosure → ③sync_loan_foreclosure → ④biz_data_view_loan_details_foreclosure
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `port.basic_data_loan_fcl.daysinfc` — Newrez 直传同名列 daysinfc（servicer 自报值，不重算）；Carrington/Capecodfive 计算 = FCL 活跃 ? datediff(referral_start_date, 快照日)+1 : NULL [pool:1546(NZ直传),1587(Carr),1628(CC5)](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L1546)
- 2. `port.basic_data_loan_foreclosure.summary_days_in_fcl` — direct copy 直传 [pool:281](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L281)
- 3. `bpms.sync_loan_foreclosure.summary_days_in_fcl` — upsert pass-through [asset:741/792](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L741)
- 4. `bpms.biz_data_view_loan_details_foreclosure.summary_days_in_fcl` — passthrough [view]

**规则（完整）/ Rule (full):** **Newrez**：原始 `daysinfc` 直传（[pool:1546](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L1546)）。**Carrington / Capecodfive**：无原始 `daysinfc` → 计算 `CASE WHEN <active> THEN datediff(day, referral_start_date, <快照日>)+1 ELSE NULL`（Carrington 用 snap_shot_date，[pool:1587](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L1587)；Capecodfive 用 dataasof，[pool:1628](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L1628)）。下游视图显示延迟校正值，详见逐跳规则。

**说明 / Note:** Newrez=raw daysinfc 直传；Carrington/Capecodfive 为计算值。

### 62. Current Step 当前阶段  (`bpms.sync_loan_foreclosure.summary_current_step`)

_当前 FCL 阶段文本。_

**来源 / Source (L1)**
- Newrez: `newrez.portnewrezfc.fcstage`
- Carrington: `carrington.portcarrington.fcl_sub_status`
- Capecodfive: —

**流动顺序 / Flow:** ①basic_data_loan_fcl → ②basic_data_loan_foreclosure → ③sync_loan_foreclosure → ④biz_data_view_loan_details_foreclosure
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `port.basic_data_loan_fcl.fcstage` — rename 改名 [pool:1560](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L1560)
- 2. `port.basic_data_loan_foreclosure.summary_current_step` — direct copy 直传 [pool:282](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L282)
- 3. `bpms.sync_loan_foreclosure.summary_current_step` — upsert pass-through [asset:742/793](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L742)
- 4. `bpms.biz_data_view_loan_details_foreclosure.summary_current_step` — passthrough [view]

### 63. Last Step Completed 最近完成步骤  (`bpms.sync_loan_foreclosure.summary_last_step_completed`)

_最近完成的 FCL 步骤。_

**来源 / Source (L1)**
- Newrez: `newrez.portnewrezfc.lastfcstepcompleted`
- Carrington: —
- Capecodfive: `capecodfive.portcapecodfive_monthly_collections.most_recent_foreclosure_stage`

**流动顺序 / Flow:** ①basic_data_loan_fcl → ②basic_data_loan_foreclosure → ③sync_loan_foreclosure → ④biz_data_view_loan_details_foreclosure
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `port.basic_data_loan_fcl.lastfcstepcompleted` — rename 改名 [pool:1561](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L1561)
- 2. `port.basic_data_loan_foreclosure.summary_last_step_completed` — direct copy 直传 [pool:283](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L283)
- 3. `bpms.sync_loan_foreclosure.summary_last_step_completed` — upsert pass-through [asset:743/794](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L743)
- 4. `bpms.biz_data_view_loan_details_foreclosure.summary_last_step_completed` — passthrough [view]

### 64. 最近完成步骤日期  (`bpms.sync_loan_foreclosure.summary_last_step_completed_date`)

_最近完成的 FCL **子步骤事件**完成日（配对字段 `lastfcstepcompleted` 携带子步骤文本，Newrez 21+ 种自定义值，粒度远细于 BPS 6-stage）。_

**来源 / Source (L1)**
- Newrez: `newrez.portnewrezfc.lastfcstepcompleteddate`
- Carrington: —
- Capecodfive: —

**流动顺序 / Flow:** ①basic_data_loan_fcl → ②basic_data_loan_foreclosure → ③sync_loan_foreclosure → ④biz_data_view_loan_details_foreclosure
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `port.basic_data_loan_fcl.lastfcstepcompleteddate` — rename 改名 [pool:1562](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L1562)
- 2. `port.basic_data_loan_foreclosure.summary_last_step_completed_date` — direct copy 直传 (rule c) [pool:284](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L284)
- 3. `bpms.sync_loan_foreclosure.summary_last_step_completed_date` — upsert pass-through [asset:744/795](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L744)
- 4. `bpms.biz_data_view_loan_details_foreclosure.summary_last_step_completed_date` — passthrough [view]

🔎 **说明** 纯透传——pool:284 `fc.lastfcstepcompleteddate AS summary_last_step_completed_date`，无聚合/计算。Newrez 自报 `lastfcstepcompleted`（子步骤名，21+ distinct 值如 'NOS Recorded' / 'Complaint Sent for Filing' / 'Motion for Judgment Sent to Court' 等）+ `lastfcstepcompleteddate`（该子步骤完成日）。**与 BPS 6-stage 模型（DEMAND/REFERRAL/FIRST_LEGAL/SERVICE/JUDGEMENT/SALE）正交**——一个 stage 内可能演化多个 sub-step。属规则 **c 直接透传**——详 [doc 33 §2.5.1](33_fcl_table_erd.md)（3 套规则 + 7 笔 loan 实测分布 + 21+ 种子步骤值）。Carrington/Capecodfive 设 null（pool:1602-1644）。
▶ **实测样例（MCP 实测 prod 2026-06-11）** — 3 笔 loan 展示「子步骤名 + 完成日 + 当前 fcstage」。

**字段对照（中文标签 → BPS sync 列 ← Newrez 源列）**：

| 中文标签 | BPS sync 列 | ← Newrez 源列 |
|---|---|---|
| 子步骤名 | `bpms.sync_loan_foreclosure.summary_last_step_completed` | `newrez.portnewrezfc.lastfcstepcompleted` |
| **完成日（本字段）** | **`bpms.sync_loan_foreclosure.summary_last_step_completed_date`** | `newrez.portnewrezfc.lastfcstepcompleteddate` |
| 当前 fcstage | `bpms.sync_loan_foreclosure.summary_current_step` | `newrez.portnewrezfc.fcstage` |

**3 笔实测**：

- **Loan 7727004408**
  - 子步骤名 = `Motion for Judgment Sent to Court`
  - 完成日 = **2026-05-13**
  - 当前 fcstage = `Judgment Hearing Scheduled For`
- **Loan 7727003984**
  - 子步骤名 = `NOS Sent for Recording`
  - 完成日 = **2025-07-16**
  - 当前 fcstage = `Pre-Sale Review 1 (SCRA and PACER Check)`
  - **注**：该日期碰巧与首次排定拍卖日同日，但两个字段语义独立——详 [doc 33 §2.5.1](33_fcl_table_erd.md)
- **Loan 7727000088**
  - 子步骤名 = `Post Sale Review (SCRA and PACER Check)`
  - 完成日 = **2026-05-26**
  - 当前 fcstage = `Post Sale Review (SCRA and PACER Check)`


## 系统 / 审计列

### 65. 系统 / 审计列

_应用/ETL 管理列（非 servicer 来源）。_

**列 / Columns:** `create_user, create_dept, create_time, update_user, update_time, status, is_deleted, tenant_id`

**说明 / Note:** 列：create_user, create_dept, create_time, update_user, update_time, status, is_deleted, tenant_id。tenant_id ← GET_LOAN_TENANT_ID(portfunding ⋈ basic_data_trust_funding，[asset:932-936](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L932-936))；create_*/update_* 由 BPS 应用写；is_deleted 视图恒 0；status 应用标志。非 servicer 数据。


## 视图计算列

### 66. 视图计算列（Actual / Variance / 合计）

_展示视图基于 timeline 日期 + target + nextduedate 派生约 45 个天数差异列。_

**列 / Columns:** `actual_<stage>_days / var_<stage>_days / target_total / actual_total / var_total`

```sql
actual_<stage>_days = to_days(timeline_<stage>_date) - to_days(nextduedate);
var_<stage>_days   = actual_<stage>_days - (cumulative target days up to that stage);
target_total = Σ target_*; actual_total = Σ actual_*; var_total = Σ var_*
```
🔎 **说明** 视图对每个里程碑计算 actual 天数（自 next-due 日）与相对累计 target 的偏差；并给出行合计。target 用 ifnull(target_X, <默认>)。
▶ **示例** 例：actual_first_legal_days = to_days(timeline_first_legal_date) - to_days(nextduedate)；var_first_legal_days = 该值 - (截至 first legal 的累计 target)。


> 本文档共 66 个字段。
