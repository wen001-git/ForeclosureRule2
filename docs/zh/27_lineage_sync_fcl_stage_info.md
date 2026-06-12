# Doc 27 · 阶段 / 天数 — `bpms.sync_fcl_stage_info` 字段血缘

> <!-- RULEGLOSS_PTR -->📖 **术语解释**：本文 `rule` 列的技术语句 → 易懂中文 + 数学公式，见 [doc 25 · 逐跳转换规则速查（附录）](25_fcl_lineage_overview.md)。
> <!-- CODEGLOSS_PTR -->🔧 **code 列图例**：`pool`=ETL 建表/SQL 代码 `basic_data_pool_config.py` · `asset`=BPS 同步 SQL `asset_managment_config.py` · `view`=BPS 视图定义；冒号后数字=该文件**行号**（链接可点）。

> **数据来源** —— 真源为 `outputs/fcl_lineage_source.json`（逐字段血缘）；本组逐字段文档目前为手工维护（旧生成器 `scripts/gen_fcl_lineage.py` 已废弃删除）。


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
| 2026-06-09 | AI Agent | v8 | 为 stage 计算字段补完整逻辑说明+举例（多分支多例）；按 SQL 投影 Code-First 校正 end_date/countdown 跳规则（demand_end=催告到期、referral/first_legal/service_end=下一阶段开始、judgement/sale/noi/publication=NULL）；修正 to_judgement/to_sale 错误示例 | doc 02 · doc 13 · doc 14 |
| 2026-06-09 | AI Agent | v9 | 代码引用 [pool:]/[asset:] 做成可点击 GitLab 链接（fork jli/prefectflow，钉到提交 32a750a3，行号精确稳定）；code legend 文件路径亦可点击；view 视图保留纯文字 | doc 02 · doc 13 · doc 14 |
| 2026-06-10 | AI Agent | v10 | hub 新增「FCL 事实中枢 vs BPS 投影」说明：basic_data_loan_fcl=事实中枢/全历史，**直接派生 foreclosure + fcl_stage_info 两张**；_hold/_bankruptcy/_loss_mitigation/fcl_related 各自从原始 servicer 表并行构建（非 fcl 子表） | doc 02 · doc 13 · doc 14 |

## 相关文档

doc 02（ETL 管道，表级）· doc 13/14（字段映射）· doc 25（血缘总览）· 源码 PrefectFlow（见各跳 code）


---

**规范跳链 / canonical hop chain**


`newrez.portnewrezfc` → `tempfc.temp_basic_data_fcl` → `port.basic_data_loan_fcl` → `port.fcl_stage_info` → `bpms.sync_fcl_stage_info`

| # | layer | db | 表 table | role |
|---|---|---|---|---|
| 1 | L0/L1 | MySQL+Redshift | `newrez.portnewrezfc` | Servicer raw |
| 2 | L4·temp | Redshift | `tempfc.temp_basic_data_fcl` | 3-servicer rename-UNION of L1 raw / 三家 servicer 改名 UNION (CREATE_BASIC_FCL, [pool:1531-1654](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L1531-1654)) |
| 3 | L4 | Redshift | `port.basic_data_loan_fcl` | canonical FCL fact |
| 4 | L4 | Redshift | `port.fcl_stage_info` | stage classification + day-math (GEN_FCL_STAGE); group/state from port.basic_data_fcl_related |
| 5 | L5 | MySQL bpms | `bpms.sync_fcl_stage_info` | BPS app table (12-FCL_STAGE sync, keeps fctrdt history) |

> `#` 列是序号，不是层号。FCL 事实表 `port.basic_data_loan_fcl` 直接由 L1 各 servicer 原始表构建（在 `tempfc.temp_basic_data_fcl` 中 UNION；CREATE_BASIC_FCL [pool:1531-1654](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L1531-1654)），因此 L2 统一日表（`port.basic_data_daily_loan_common`）与 L3 清洗层（`basic_data_daily_loan_common_clean` / `basic_data_loan_delinq_clean`）按设计不在本分支——它们承载通用+逾期字段，仅经 `group` 维度（doc 27，`basic_data_fcl_related`）与月度 `portmonth` 路径回流。完整 L0–L5 管道见 doc 02。

> code: `pool` = [PrefectFlow/flow/basic_data/basic_data_config/basic_data_pool_config.py](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py) · `asset` = [PrefectFlow/flow/bps/bps_config/asset_managment_config.py](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py) · `view` = bpms.biz_data_view_loan_details_foreclosure (SHOW CREATE VIEW)


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
- 1. `(per servicer)` · constant 'Newrez'/'Carrington'/'Capecodfive' — constant per UNION branch [pool:1536/1577/1618](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L1536)
- 2. `bpms.sync_fcl_stage_info.servicer` — sync passthrough [asset]


## 维度（group / judicial / state）

### 5. stage 当前阶段分类  (`bpms.sync_fcl_stage_info.stage`)

_贷款当前阶段分类（waterfall 结果）。_

**来源 / Source (L1)**
- Newrez: `port.basic_data_loan_fcl` · (stage dates)  （仅 Newrez 提供此明细）

**流动顺序 / Flow:** ①basic_data_loan_fcl → ②fcl_stage_info → ③sync_fcl_stage_info
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `port.basic_data_loan_fcl` · (stage dates) — waterfall by first non-null date
- 2. `port.fcl_stage_info.stage` — CASE waterfall: SALE→JUDGEMENT→PUBLICATION→SERVICE→FIRST_LEGAL→REFERRAL→DEMAND [pool:2095-2102](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L2095-2102)
- 3. `bpms.sync_fcl_stage_info.stage` — sync passthrough [asset:925](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L925)

**说明 / Note:** 取值：SALE / JUDGEMENT / PUBLICATION / SERVICE / FIRST_LEGAL / REFERRAL / DEMAND（7 个；prod 快照当前为 REFERRAL/SALE/FIRST_LEGAL/SERVICE/JUDGEMENT）。

```sql
CASE: sale_start⇒SALE; elif fcjudgment_start⇒JUDGEMENT; elif publication_start⇒PUBLICATION; elif service_start⇒SERVICE; elif legal_start⇒FIRST_LEGAL; elif referral_start⇒REFERRAL; elif demand_sent_start⇒DEMAND; else NULL
```
🔎 **说明** 当前阶段取贷款已到达的最靠后里程碑：7 分支 CASE，按 SALE → JUDGEMENT → PUBLICATION → SERVICE → FIRST_LEGAL → REFERRAL → DEMAND 的优先级判断——第一个开始日非空的阶段即为结果。
▶ **示例** ① 7727001179：sale_start 有值 ⇒ stage = SALE。② 7727000357：无 sale 但 fcjudgment_start 有值 ⇒ JUDGEMENT。③ 700082880000091：仅到 service_start ⇒ SERVICE。④ 700082700000033：仅 referral_start ⇒ REFERRAL。

### 6. Group 分组（FCL/D120P/D90/REO/P）  (`bpms.sync_fcl_stage_info.group`)

_用于分桶的逾期/法律分组。_

**来源 / Source (L1)**
- Newrez: `newrez.portnewrezgeneral.delinquency_status_mba`
- Carrington: `carrington.portcarrington.loan_status / fcl_flag`
- Capecodfive: —

**流动顺序 / Flow:** ①basic_data_fcl_related → ②fcl_stage_info → ③sync_fcl_stage_info
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `port.basic_data_fcl_related.delq_status` — CASE mba then days360 fallback 见 sql [pool:1702-1711](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L1702-1711)
- 2. `port.fcl_stage_info.group` — = r.delq_status (join loanid+dataasof) [pool:2348,2400](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L2348)
- 3. `bpms.sync_fcl_stage_info.group` — 12-FCL_STAGE sync pass-through [asset:925](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L925)

**规则（完整）/ Rule (full):** `fcl_stage_info.group = basic_data_fcl_related.delq_status`。**Newrez**（[pool:1702-1711](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L1702-1711)）：`delinquency_status_mba='Full Payoff'`→P、`'REO'`→REO、任意 `'Foreclosure*'`→FCL；否则按 `days360(portnewrezpmt.nextduedate, dataasof)` 分桶：`<30`→C、`<60`→D30、`<90`→D60、`<120`→D90、否则→D120P。**Carrington**（[pool:1749-1758](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L1749-1758)）：`loan_status='Foreclosure' 或 fcl_flag='Active'`→FCL、`loan_status IN ('R','REO')`→REO、`IN ('Completed Payoff','Completed Short Sale')`→P；否则对 `date_payment_due` 用同样的 `days360` 分桶。**Capecodfive** 不在 `basic_data_fcl_related` → group 为 `—`。

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
- 1. `port.basic_data_fcl_related.propertystate` — direct 直传 [pool:1721](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L1721)
- 2. `port.fcl_stage_info.state` — = property state (r.propertystate), joined in [pool:2401](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L2401)
- 3. `bpms.sync_fcl_stage_info.state` — sync pass-through [asset:925](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L925)

**说明 / Note:** 房产所在美国州，由止赎关系属性 r.propertystate 关联带入。直取，无转换。

### 8. Judicial 司法(Y/N)  (`bpms.sync_fcl_stage_info.judicial`)

_司法标志（带州级回退）。_

**来源 / Source (L1)**
- Newrez: `newrez.portnewrezfc.judicial`
- Carrington: —
- Capecodfive: —

**流动顺序 / Flow:** ①basic_data_loan_fcl → ②fcl_stage_info → ③sync_fcl_stage_info
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `port.basic_data_loan_fcl.judicial` — normalize cast(int) [pool:2034](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L2034)
- 2. `port.fcl_stage_info.judicial` — Y/N else state-config fallback 见 sql [pool:2351-2353,2432](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L2351-2353)
- 3. `bpms.sync_fcl_stage_info.judicial` — sync pass-through [asset:925](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L925)

**规则（完整）/ Rule (full):** `fcl_stage_info.judicial = CASE judicial=1→'Y'、0→'N'`。**Newrez** 提供贷款级 `judicial` 标志（[pool:1565](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L1565)）。**Carrington / Capecodfive** 事实表中 `judicial=NULL`（[pool:1606](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L1606) / 1647）→ **州级回退**：按房产州关联 `basic_data_judicial_config`，取其 judicial 值（[pool:2351-2353](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L2351-2353)，关联 [pool:2432](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L2432)）。

```sql
CASE judicial=1→'Y', 0→'N', ELSE config_judicial (port.basic_data_judicial_config keyed by propertystate)
```
🔎 **说明** 由归一化的贷款级 judicial：1→'Y'、0→'N'。若 NULL/空，则回退到州级司法配置（basic_data_judicial_config 按房产州关联）。
▶ **示例** judicial=1 ⇒ 'Y'。无标志的贷款在司法州（如 FL）⇒ 配置 'Y'；在非司法州（如 TX）⇒ 'N'。


## 阶段开始日期

### 9. 催告/Demand 阶段开始日  (`bpms.sync_fcl_stage_info.demand_start_date`)

_阶段开始日期。_

> ℹ️ **透传**自 `newrez.portnewrezfc.demandsentdate`（催告函发出日 = DEMAND 阶段左端）。完整规则见 [doc 31 §2](31_fcl_stage_window_rules.md#2-stage_start_date-来源总表)。

**来源 / Source (L1)**
- Newrez: `newrez.portnewrezfc.demandsentdate`
- Carrington: —
- Capecodfive: —

**流动顺序 / Flow:** ①basic_data_loan_fcl → ②fcl_stage_info → ③sync_fcl_stage_info
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `port.basic_data_loan_fcl.demandsentdate` — source 源
- 2. `port.fcl_stage_info.demand_start_date` — passthrough of source demandsentdate [pool:2037](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L2037)
- 3. `bpms.sync_fcl_stage_info.demand_start_date` — sync passthrough [asset:925](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L925)

```sql
demand_start_date = passthrough of business_1.demandsentdate (no transform)
```
🔎 **说明** 直接透传来源里程碑日期 `demandsentdate`，无转换；贷款未进入该阶段则为 NULL。
▶ **示例** 700082880000091：demandsentdate 2025-12-29 ⇒ demand_start_date = 2025-12-29。

### 10. 催告/Demand 阶段结束日(窗口)  (`bpms.sync_fcl_stage_info.demand_end_date`)

_催告窗口结束日（= 催告到期日 demandexpirationdate）。_

> ℹ️ **透传**自 `newrez.portnewrezfc.demandexpirationdate`（窗口右端展示）。⚠️ **不参与 demand_stage_days 计算**——demand 一律数到 curr_date。完整规则见 [doc 31 §3 + §5](31_fcl_stage_window_rules.md#3-stage_end_date-派生规则总表)。

**来源 / Source (L1)**
- Newrez: `newrez.portnewrezfc`  （仅 Newrez 提供此明细）

**流动顺序 / Flow:** ①portnewrezfc → ②basic_data_loan_fcl → ③fcl_stage_info → ④sync_fcl_stage_info
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `newrez.portnewrezfc.demandexpirationdate` — servicer raw 原始（DB 实测列存在）
- 2. `port.basic_data_loan_fcl.demandexpirationdate` — passthrough 直传（DB 实测列存在）
- 3. `port.fcl_stage_info.demand_end_date` — = source demandexpirationdate (passthrough; NOT next-stage start) [pool:2038,2355](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L2038)
- 4. `bpms.sync_fcl_stage_info.demand_end_date` — sync passthrough [asset:925](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L925)

```sql
demand_end_date = passthrough of business_1.demandexpirationdate ([pool:2038](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L2038))
```
🔎 **说明** 催告窗口结束日取服务商的催告到期日（demandexpirationdate），原样透传——不是下一阶段开始日。注意 demand_stage_days 不用此列，而是从 demand_start 一律数到当日（logic = curr_date，[pool:2039-2041](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L2039-2041)）。
▶ **示例（含完整算式）** 700082880000091：demand_start_date = 2025-12-29（透传自 `newrez.portnewrezfc.demandsentdate`）、demand_end_date = 2026-01-13（透传自 `demandexpirationdate`，只描绘催告窗口右端，**不参与天数计算**）。demand_stage_days **不取 demand_end_date**，按 curr_date 计算：
> `demand_stage_days = datediff(2025-12-29, curr_date 2026-06-09) + 1 = 162 + 1 = `**`163`**`（curr_date = ETL 运行日；与 prod 一致）`。

### 11. NOI 阶段开始日  (`bpms.sync_fcl_stage_info.noi_start_date`)

_NOI 桶未单独填充（由 DEMAND 覆盖）。_

> ⚠ null_in_build

**来源 / Source (L1)**
- Newrez: `port.fcl_stage_info.noi_start_date`  （仅 Newrez 提供此明细）

**流动顺序 / Flow:** ①fcl_stage_info → ②sync_fcl_stage_info
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `port.fcl_stage_info.noi_start_date` — NULL by design — NOI not populated in business_1 [pool:2043-2046](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L2043-2046)
- 2. `bpms.sync_fcl_stage_info.noi_start_date` — sync passthrough (NULL) [asset:925](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L925)

**说明 / Note:** NOI 阶段在 business_1 CTE 未填充（硬编码 NULL）；NOI 活动并入 DEMAND 窗口表示。prod 全量实测为 NULL。

### 12. NOI 阶段结束日(窗口)  (`bpms.sync_fcl_stage_info.noi_end_date`)

_NOI 阶段结束日（该阶段未填充，恒 NULL）。_

> ⚠ null_in_build

**来源 / Source (L1)**
- Newrez: `newrez.portnewrezfc`  （仅 Newrez 提供此明细）

**流动顺序 / Flow:** ①portnewrezfc → ②basic_data_loan_fcl → ③fcl_stage_info → ④sync_fcl_stage_info
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `newrez.portnewrezfc` — —
- 2. `port.basic_data_loan_fcl` · (stage end) — source 源
- 3. `port.fcl_stage_info.noi_end_date` — NULL by design [pool:2043-2046](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L2043-2046)
- 4. `bpms.sync_fcl_stage_info.noi_end_date` — sync passthrough [asset:925](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L925)

**说明 / Note:** 硬编码 NULL（见 noi_start_date）。prod 全量实测为 NULL。

### 13. NOI 阶段已历天数  (`bpms.sync_fcl_stage_info.noi_stage_days`)

_NOI 桶未单独填充（由 DEMAND 覆盖）。_

> ⚠ null_in_build

**来源 / Source (L1)**
- Newrez: `port.fcl_stage_info.noi_stage_days`  （仅 Newrez 提供此明细）

**流动顺序 / Flow:** ①fcl_stage_info → ②sync_fcl_stage_info
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `port.fcl_stage_info.noi_stage_days` — NULL by design [pool:2046](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L2046)
- 2. `bpms.sync_fcl_stage_info.noi_stage_days` — sync passthrough (NULL) [asset:925](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L925)

**说明 / Note:** 硬编码 NULL——不计算 NOI 窗口。prod 全量实测为 NULL。

### 14. 转介 阶段开始日  (`bpms.sync_fcl_stage_info.referral_start_date`)

_阶段开始日期。_

> ℹ️ **透传**自 `newrez.portnewrezfc.fcreferraldate`（转介日 = REFERRAL 阶段左端）。完整规则见 [doc 31 §2](31_fcl_stage_window_rules.md#2-stage_start_date-来源总表)。

**来源 / Source (L1)**
- Newrez: `newrez.portnewrezfc.fcreferraldate`
- Carrington: `carrington.portcarrington.fcl_referral_date`
- Capecodfive: `capecodfive.portcapecodfive_monthly_collections.foreclosure_date_refrd_atty`

**流动顺序 / Flow:** ①basic_data_loan_fcl → ②fcl_stage_info → ③sync_fcl_stage_info
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `port.basic_data_loan_fcl.referral_start_date` — source 源
- 2. `port.fcl_stage_info.referral_start_date` — passthrough of source referral_start_date [pool:2048](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L2048)
- 3. `bpms.sync_fcl_stage_info.referral_start_date` — sync passthrough [asset:925](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L925)

```sql
referral_start_date = passthrough of business_1.referral_start_date (no transform)
```
🔎 **说明** 直接透传来源里程碑日期 `referral_start_date`，无转换；贷款未进入该阶段则为 NULL。
▶ **示例** 700082880000091：referral_start_date 2026-01-20 ⇒ 2026-01-20。

### 15. 转介 阶段结束日(窗口)  (`bpms.sync_fcl_stage_info.referral_end_date`)

_转介窗口结束（= 下一阶段「首次法律」开始日；未到则 NULL）。_

> ℹ️ **派生**（= 下一阶段 `first_legal_start_date`），**非** Newrez 单列透传；首次法律未到则 NULL。完整规则见 [doc 31 §3](31_fcl_stage_window_rules.md#3-stage_end_date-派生规则总表)。

**来源 / Source (L1)**
- Newrez: `newrez.portnewrezfc`  （仅 Newrez 提供此明细）

**流动顺序 / Flow:** ①portnewrezfc → ②basic_data_loan_fcl → ③fcl_stage_info → ④sync_fcl_stage_info
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `newrez.portnewrezfc` — —
- 2. `port.basic_data_loan_fcl` · (stage end) — source 源
- 3. `port.fcl_stage_info.referral_end_date` — = next stage start (first_legal_start_date (legal_start_date)); NULL if not reached [pool:2049,2365](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L2049)
- 4. `bpms.sync_fcl_stage_info.referral_end_date` — sync passthrough [asset:925](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L925)

```sql
referral_end_date = first_legal_start_date (legal_start_date) (the next stage's start); NULL if the next stage has not started
```
🔎 **说明** 转介窗口在下一阶段（首次法律）开始时结束：referral_end_date = first_legal_start_date。若首次法律尚未开始，则此列为 NULL——此时 referral_stage_days 改为数到当日（logic_referral_end_date = coalesce(end, curr_date)，[pool:2050-2052](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L2050-2052)）。
▶ **示例** ① 下一阶段已到 — 700082880000091：first_legal_start=2026-03-12 ⇒ referral_end_date=2026-03-12，referral_stage_days=52（datediff(2026-01-20,2026-03-12)+1）。② 未到 — 700082700000033（仍在 REFERRAL）：referral_end_date=NULL，referral_stage_days=119（从 2026-02-11 数到当日）。

### 16. 首次法律 阶段开始日  (`bpms.sync_fcl_stage_info.first_legal_start_date`)

_阶段开始日期。_

> ℹ️ **透传**自 `newrez.portnewrezfc.firstlegaldate`（首次法律行动日 = FIRST_LEGAL 阶段左端）。完整规则见 [doc 31 §2](31_fcl_stage_window_rules.md#2-stage_start_date-来源总表)。

**来源 / Source (L1)**
- Newrez: `newrez.portnewrezfc.firstlegaldate`
- Carrington: —
- Capecodfive: `capecodfive.portcapecodfive_monthly_collections.foreclosure_first_legal_date`

**流动顺序 / Flow:** ①basic_data_loan_fcl → ②fcl_stage_info → ③sync_fcl_stage_info
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `port.basic_data_loan_fcl.legal_start_date` — source 源
- 2. `port.fcl_stage_info.first_legal_start_date` — passthrough of source legal_start_date [pool:2058](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L2058)
- 3. `bpms.sync_fcl_stage_info.first_legal_start_date` — sync passthrough [asset:925](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L925)

```sql
first_legal_start_date = passthrough of business_1.legal_start_date (no transform)
```
🔎 **说明** 直接透传来源里程碑日期 `legal_start_date`，无转换；贷款未进入该阶段则为 NULL。
▶ **示例** 700082880000091：legal_start_date 2026-03-12 ⇒ first_legal_start_date = 2026-03-12。

### 17. 首次法律 阶段结束日(窗口)  (`bpms.sync_fcl_stage_info.first_legal_end_date`)

_首次法律窗口结束（= 下一阶段「送达」开始日；未到则 NULL）。_

> ℹ️ **派生**（= 下一阶段 `service_start_date`），**非** Newrez 单列透传；送达未到则 NULL。完整规则见 [doc 31 §3](31_fcl_stage_window_rules.md#3-stage_end_date-派生规则总表)。

**来源 / Source (L1)**
- Newrez: `newrez.portnewrezfc`  （仅 Newrez 提供此明细）

**流动顺序 / Flow:** ①portnewrezfc → ②basic_data_loan_fcl → ③fcl_stage_info → ④sync_fcl_stage_info
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `newrez.portnewrezfc` — —
- 2. `port.basic_data_loan_fcl` · (stage end) — source 源
- 3. `port.fcl_stage_info.first_legal_end_date` — = next stage start (service_start_date); NULL if not reached [pool:2059,2370](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L2059)
- 4. `bpms.sync_fcl_stage_info.first_legal_end_date` — sync passthrough [asset:925](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L925)

```sql
first_legal_end_date = service_start_date (the next stage's start); NULL if the next stage has not started
```
🔎 **说明** 首次法律窗口在下一阶段（送达）开始时结束：first_legal_end_date = service_start_date；若送达尚未开始则为 NULL（此时 first_legal_stage_days 数到当日，[pool:2060-2062](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L2060-2062)）。
▶ **示例（含完整算式）**
> ① 下一阶段已开始（end 已填） — 700082880000091：first_legal_start_date = 2026-03-12（透传自 `newrez.firstlegaldate`）、service_start_date = 2026-05-13 ⇒ first_legal_end_date = 2026-05-13；first_legal_stage_days = datediff(2026-03-12, 2026-05-13) + 1 = 62 + 1 = **63**（与 prod 一致）。
> ② 仍在 FIRST_LEGAL（送达未到，end 取 curr_date） — first_legal_end_date = NULL；first_legal_stage_days = datediff(first_legal_start_date, curr_date 2026-06-09) + 1（同 referral 700082700000033 的「数到当日」模式）。

### 18. 首次法律日(首见追踪)  (`bpms.sync_fcl_stage_info.first_legal_date_history`)

_首次法律日的 ETL 首见追踪。_

**来源 / Source (L1)**
- Newrez: `newrez.portnewrezfc.firstlegaldate`  （仅 Newrez 提供此明细）

**流动顺序 / Flow:** ①portnewrezfc → ②basic_data_loan_fcl → ③fcl_stage_info → ④sync_fcl_stage_info
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `newrez.portnewrezfc.firstlegaldate` — servicer raw 原始
- 2. `port.basic_data_loan_fcl.legal_start_date` — source 源
- 3. `port.fcl_stage_info.first_legal_date_history` — first-seen tracking (join L); NULL across prod [pool:2374](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L2374)
- 4. `bpms.sync_fcl_stage_info.first_legal_date_history` — sync passthrough [asset:925](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L925)

**说明 / Note:** ETL「首见」追踪列，来自 L.first_legal_date_history 关联；该来源未填充，故 prod 当前全量为 NULL。

### 19. 送达 阶段开始日  (`bpms.sync_fcl_stage_info.service_start_date`)

_阶段开始日期。_

> ℹ️ **透传**自 `newrez.portnewrezfc.servicecompletedate`。⚠️ **命名反直觉**：`servicecompletedate` 字面像「送达**完成**日」，但 FCL stage 模型里 SERVICE 阶段指的是「送达完成后、判决可得前的等待窗口」——所以这个日期是 SERVICE 阶段的**起点**，**不是 end**。完整规则见 [doc 31 §2 + §6](31_fcl_stage_window_rules.md#6-容易混淆的-5-点)。

**来源 / Source (L1)**
- Newrez: `newrez.portnewrezfc.servicecompletedate`
- Carrington: —
- Capecodfive: `capecodfive.portcapecodfive_monthly_collections.foreclosure_service_date`

**流动顺序 / Flow:** ①basic_data_loan_fcl → ②fcl_stage_info → ③sync_fcl_stage_info
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `port.basic_data_loan_fcl.service_start_date` — source 源
- 2. `port.fcl_stage_info.service_start_date` — passthrough of source service_start_date [pool:2068](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L2068)
- 3. `bpms.sync_fcl_stage_info.service_start_date` — sync passthrough [asset:925](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L925)

```sql
service_start_date = passthrough of business_1.service_start_date (no transform)
```
🔎 **说明** 直接透传来源里程碑日期 `service_start_date`，无转换；贷款未进入该阶段则为 NULL。
▶ **示例** 700082880000091：service_start_date 2026-05-13 ⇒ 2026-05-13。

### 20. 送达 阶段结束日(窗口)  (`bpms.sync_fcl_stage_info.service_end_date`)

_送达窗口结束（= 下一阶段「可判决日」；未到则 NULL）。_

> ℹ️ **派生**（= 下一阶段 `judgment_available_date`），**非** Newrez 单列透传；判决可得日未到则 NULL。完整规则见 [doc 31 §3](31_fcl_stage_window_rules.md#3-stage_end_date-派生规则总表)。

**来源 / Source (L1)**
- Newrez: `newrez.portnewrezfc`  （仅 Newrez 提供此明细）

**流动顺序 / Flow:** ①portnewrezfc → ②basic_data_loan_fcl → ③fcl_stage_info → ④sync_fcl_stage_info
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `newrez.portnewrezfc` — —
- 2. `port.basic_data_loan_fcl` · (stage end) — source 源
- 3. `port.fcl_stage_info.service_end_date` — = next stage start (judgement availability (judgment_available_date)); NULL if not reached [pool:2069,2376](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L2069)
- 4. `bpms.sync_fcl_stage_info.service_end_date` — sync passthrough [asset:925](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L925)

```sql
service_end_date = judgement availability (judgment_available_date) (the next stage's start); NULL if the next stage has not started
```
🔎 **说明** 送达窗口在下一阶段（可判决日）开始时结束：service_end_date = judgment_available_date；若未到则为 NULL（此时 service_stage_days 数到当日，[pool:2070-2072](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L2070-2072)）。
▶ **示例（含完整算式）**
> ① 下一阶段已开始（end 已填） — 7727000357：service_start_date = 2025-08-14（透传自 `newrez.servicecompletedate`）、service_end_date = 2026-01-26（= 下一阶段 `judgment_available_date`） ⇒ service_stage_days = datediff(2025-08-14, 2026-01-26) + 1 = 165 + 1 = **166**（与 prod 一致）。
> ② 仍在 SERVICE（判决日未到，end 取 curr_date） — 700082880000091（当前 stage=SERVICE）：service_start_date = 2026-05-13（透传自 `newrez.servicecompletedate`）、service_end_date = NULL ⇒ service_stage_days = datediff(2026-05-13, curr_date 2026-06-09) + 1 = 27 + 1 = **28**（curr_date = ETL 运行日；与 prod 一致）。**用户的疑问澄清：例 ② 中的「2026-05-13」就是本贷款的 `service_start_date`（即 newrez 源里的 `servicecompletedate`），不是 raw 文件外另外灌入。**

### 21. 公告 阶段开始日  (`bpms.sync_fcl_stage_info.publication_start_date`)

_Publication 对这些 servicer 未填充。_

> ⚠ null_in_build

**来源 / Source (L1)**
- Newrez: `port.fcl_stage_info.publication_start_date`  （仅 Newrez 提供此明细）

**流动顺序 / Flow:** ①fcl_stage_info → ②sync_fcl_stage_info
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `port.fcl_stage_info.publication_start_date` — NULL by design — publication not populated [pool:2078-2081](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L2078-2081)
- 2. `bpms.sync_fcl_stage_info.publication_start_date` — sync passthrough (NULL) [asset:925](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L925)

**说明 / Note:** 公告阶段在 business_1 未填充（硬编码 NULL）。prod 全量实测为 NULL。

### 22. 公告 阶段结束日(窗口)  (`bpms.sync_fcl_stage_info.publication_end_date`)

_公告阶段结束日（该阶段未填充，恒 NULL）。_

> ⚠ null_in_build

**来源 / Source (L1)**
- Newrez: `newrez.portnewrezfc`  （仅 Newrez 提供此明细）

**流动顺序 / Flow:** ①portnewrezfc → ②basic_data_loan_fcl → ③fcl_stage_info → ④sync_fcl_stage_info
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `newrez.portnewrezfc` — —
- 2. `port.basic_data_loan_fcl` · (stage end) — source 源
- 3. `port.fcl_stage_info.publication_end_date` — NULL by design [pool:2078-2081](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L2078-2081)
- 4. `bpms.sync_fcl_stage_info.publication_end_date` — sync passthrough [asset:925](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L925)

**说明 / Note:** 硬编码 NULL（见 publication_start_date）。prod 全量实测为 NULL。

### 23. 公告 阶段已历天数  (`bpms.sync_fcl_stage_info.publication_stage_days`)

_Publication 对这些 servicer 未填充。_

> ⚠ null_in_build

**来源 / Source (L1)**
- Newrez: `port.fcl_stage_info.publication_stage_days`  （仅 Newrez 提供此明细）

**流动顺序 / Flow:** ①fcl_stage_info → ②sync_fcl_stage_info
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `port.fcl_stage_info.publication_stage_days` — NULL by design [pool:2081](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L2081)
- 2. `bpms.sync_fcl_stage_info.publication_stage_days` — sync passthrough (NULL) [asset:925](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L925)

**说明 / Note:** 硬编码 NULL——不计算公告窗口。prod 全量实测为 NULL。

### 24. 判决 阶段开始日  (`bpms.sync_fcl_stage_info.judgement_start_date`)

_阶段开始日期。_

**来源 / Source (L1)**
- Newrez: `newrez.portnewrezfc.fcjudgmenthearingscheduled`
- Carrington: —
- Capecodfive: —

**流动顺序 / Flow:** ①basic_data_loan_fcl → ②fcl_stage_info → ③sync_fcl_stage_info
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `port.basic_data_loan_fcl.fcjudgment_hearing_scheduled` — source 源
- 2. `port.fcl_stage_info.judgement_start_date` — passthrough of source fcjudgment_start_date [pool:2084,2386](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L2084)
- 3. `bpms.sync_fcl_stage_info.judgement_start_date` — sync passthrough [asset:925](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L925)

```sql
judgement_start_date = passthrough of business_1.fcjudgment_start_date (no transform)
```
🔎 **说明** 直接透传来源里程碑日期 `fcjudgment_start_date`，无转换；贷款未进入该阶段则为 NULL。
▶ **示例** 7727001179：fcjudgment_start_date 2025-11-29 ⇒ judgement_start_date = 2025-11-29。

### 25. 判决 阶段结束日(窗口)  (`bpms.sync_fcl_stage_info.judgement_end_date`)

_判决阶段结束日（恒 NULL；判决桶用倒计天数 to_judgement_days）。_

**来源 / Source (L1)**
- Newrez: `newrez.portnewrezfc`  （仅 Newrez 提供此明细）

**流动顺序 / Flow:** ①portnewrezfc → ②basic_data_loan_fcl → ③fcl_stage_info → ④sync_fcl_stage_info
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `newrez.portnewrezfc` — —
- 2. `port.basic_data_loan_fcl` · (stage end) — source 源
- 3. `port.fcl_stage_info.judgement_end_date` — NULL (bucket uses to_judgement_days) [pool:2387](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L2387)
- 4. `bpms.sync_fcl_stage_info.judgement_end_date` — sync passthrough [asset:925](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L925)

**说明 / Note:** 投影中硬编码 NULL。判决桶用 judgement_start_date + to_judgement_days 倒计天数表示，不设窗口结束日。prod 全量实测为 NULL。

### 26. 拍卖 阶段开始日  (`bpms.sync_fcl_stage_info.sale_start_date`)

_阶段开始日期。_

**来源 / Source (L1)**
- Newrez: `newrez.portnewrezfc.fcscheduledsaledate`
- Carrington: `carrington.portcarrington.fcl_scheduled_sale_date`
- Capecodfive: `capecodfive.portcapecodfive_monthly_collections.foreclosure_date_sale_scheduled`

**流动顺序 / Flow:** ①basic_data_loan_fcl → ②fcl_stage_info → ③sync_fcl_stage_info
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `port.basic_data_loan_fcl.fcscheduled_sale_date` — source 源
- 2. `port.fcl_stage_info.sale_start_date` — passthrough of source sale_start_date [pool:2090,2391](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L2090)
- 3. `bpms.sync_fcl_stage_info.sale_start_date` — sync passthrough [asset:925](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L925)

```sql
sale_start_date = passthrough of business_1.sale_start_date (no transform)
```
🔎 **说明** 直接透传来源里程碑日期 `sale_start_date`，无转换；贷款未进入该阶段则为 NULL。
▶ **示例** 7727001179：sale_start_date 2026-06-23 ⇒ sale_start_date = 2026-06-23。

### 27. 拍卖 阶段结束日(窗口)  (`bpms.sync_fcl_stage_info.sale_end_date`)

_拍卖阶段结束日（恒 NULL；拍卖桶用倒计天数 to_sale_days）。_

**来源 / Source (L1)**
- Newrez: `newrez.portnewrezfc`  （仅 Newrez 提供此明细）

**流动顺序 / Flow:** ①portnewrezfc → ②basic_data_loan_fcl → ③fcl_stage_info → ④sync_fcl_stage_info
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `newrez.portnewrezfc` — —
- 2. `port.basic_data_loan_fcl` · (stage end) — source 源
- 3. `port.fcl_stage_info.sale_end_date` — NULL (bucket uses to_sale_days) [pool:2392](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L2392)
- 4. `bpms.sync_fcl_stage_info.sale_end_date` — sync passthrough [asset:925](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L925)

**说明 / Note:** 投影中硬编码 NULL。拍卖桶用 sale_start_date + to_sale_days 倒计天数表示。prod 全量实测为 NULL。


## 阶段天数

### 28. 催告/Demand 阶段已历天数  (`bpms.sync_fcl_stage_info.demand_stage_days`)

_阶段内含端点已历天数。_

**来源 / Source (L1)**
- Newrez: `newrez.portnewrezfc`  （仅 Newrez 提供此明细）

**流动顺序 / Flow:** ①portnewrezfc → ②basic_data_loan_fcl → ③fcl_stage_info → ④sync_fcl_stage_info
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `newrez.portnewrezfc` — —
- 2. `port.basic_data_loan_fcl` · (stage dates) — source 源
- 3. `port.fcl_stage_info.demand_stage_days` — datediff+1 (inclusive) 见 sql [pool:2040-2076](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L2040-2076)
- 4. `bpms.sync_fcl_stage_info.demand_stage_days` — sync passthrough [asset:925](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L925)

```sql
demand_stage_days = datediff(day, demand_start_date, curr_date) + 1
-- demand 阶段特殊：不取 demand_end_date 作为窗口结尾，一律数到 curr_date
```
🔎 **说明** demand 阶段特殊——**总是数到当日（curr_date）**，不取 demand_end_date（即 demandexpirationdate）作为窗口结尾 [pool:2039-2041]。公式：`demand_stage_days = datediff(demand_start_date, curr_date) + 1`。
▶ **示例（含完整算式）** 700082880000091：demand_start_date = 2025-12-29（透传自 `newrez.demandsentdate`）、curr_date = 2026-06-09（ETL 运行日）
> ⇒ demand_stage_days = datediff(2025-12-29, 2026-06-09) + 1 = 162 + 1 = **163**（与 prod 一致）。
> 注：本贷款的 demand_end_date = 2026-01-13 在天数计算中**未使用**——仅作文档窗口右端。

### 29. 催告/Demand 阶段内 LM 天数  (`bpms.sync_fcl_stage_info.demand_in_lm_days`)

_阶段内与开启 LM 周期重叠天数。_

**来源 / Source (L1)**
- Newrez: `newrez.portnewrezfc`  （仅 Newrez 提供此明细）

**流动顺序 / Flow:** ①portnewrezfc → ②basic_data_loan_fcl → ③fcl_stage_info → ④sync_fcl_stage_info
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `newrez.portnewrezfc` — —
- 2. `port.basic_data_loan_fcl` · (LM cycle) — source 源
- 3. `port.fcl_stage_info.demand_in_lm_days` — interval overlap (LM) 见 sql [pool:2246-2330](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L2246-2330)
- 4. `bpms.sync_fcl_stage_info.demand_in_lm_days` — sync passthrough [asset:925](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L925)

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
- 3. `port.fcl_stage_info.demand_on_hold_days` — interval overlap (Hold) 见 sql [pool:2215-2297](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L2215-2297)
- 4. `bpms.sync_fcl_stage_info.demand_on_hold_days` — sync passthrough [asset:925](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L925)

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
- 3. `port.fcl_stage_info.noi_in_lm_days` — interval overlap (LM) 见 sql [pool:2246-2330](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L2246-2330)
- 4. `bpms.sync_fcl_stage_info.noi_in_lm_days` — sync passthrough [asset:925](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L925)

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
- 3. `port.fcl_stage_info.noi_on_hold_days` — interval overlap (Hold) 见 sql [pool:2215-2297](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L2215-2297)
- 4. `bpms.sync_fcl_stage_info.noi_on_hold_days` — sync passthrough [asset:925](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L925)

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
- 3. `port.fcl_stage_info.referral_stage_days` — datediff+1 (inclusive) 见 sql [pool:2040-2076](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L2040-2076)
- 4. `bpms.sync_fcl_stage_info.referral_stage_days` — sync passthrough [asset:925](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L925)

```sql
referral_stage_days = datediff(day, referral_start_date, COALESCE(first_legal_start_date, curr_date)) + 1
-- end = 下一阶段(首次法律)开始日；若未开始则取 curr_date
```
🔎 **说明** referral 阶段端点：**end = COALESCE(下一阶段 first_legal_start_date, curr_date)**——首次法律已开始则用其开始日为右端；否则数到当日 [pool:2050-2052]。公式：`referral_stage_days = datediff(referral_start_date, COALESCE(first_legal_start_date, curr_date)) + 1`。
▶ **示例（含完整算式）**
> ① 下一阶段已开始 — 7727004408：referral_start_date = 2024-03-08（透传自 `newrez.fcreferraldate`）、first_legal_start_date = 2025-07-28
> ⇒ referral_stage_days = datediff(2024-03-08, 2025-07-28) + 1 = 507 + 1 = **508**（与 prod 一致）。
>
> ② 仍在 REFERRAL（首次法律未到） — 700082700000033：referral_start_date = 2026-02-11、first_legal_start_date = NULL ⇒ end = curr_date = 2026-06-09
> ⇒ referral_stage_days = datediff(2026-02-11, 2026-06-09) + 1 = 118 + 1 = **119**（与 prod 一致）。

### 34. 转介 阶段内 LM 天数  (`bpms.sync_fcl_stage_info.referral_in_lm_days`)

_阶段内与开启 LM 周期重叠天数。_

**来源 / Source (L1)**
- Newrez: `newrez.portnewrezfc`  （仅 Newrez 提供此明细）

**流动顺序 / Flow:** ①portnewrezfc → ②basic_data_loan_fcl → ③fcl_stage_info → ④sync_fcl_stage_info
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `newrez.portnewrezfc` — —
- 2. `port.basic_data_loan_fcl` · (LM cycle) — source 源
- 3. `port.fcl_stage_info.referral_in_lm_days` — interval overlap (LM) 见 sql [pool:2246-2330](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L2246-2330)
- 4. `bpms.sync_fcl_stage_info.referral_in_lm_days` — sync passthrough [asset:925](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L925)

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
- 3. `port.fcl_stage_info.referral_on_hold_days` — interval overlap (Hold) 见 sql [pool:2215-2297](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L2215-2297)
- 4. `bpms.sync_fcl_stage_info.referral_on_hold_days` — sync passthrough [asset:925](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L925)

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
- 3. `port.fcl_stage_info.first_legal_stage_days` — datediff+1 (inclusive) 见 sql [pool:2040-2076](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L2040-2076)
- 4. `bpms.sync_fcl_stage_info.first_legal_stage_days` — sync passthrough [asset:925](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L925)

```sql
first_legal_stage_days = datediff(day, first_legal_start_date, COALESCE(service_start_date, curr_date)) + 1
-- end = 下一阶段(送达)开始日；若未开始则取 curr_date
```
🔎 **说明** first_legal 阶段端点：**end = COALESCE(下一阶段 service_start_date, curr_date)** [pool:2060-2062]。公式：`first_legal_stage_days = datediff(first_legal_start_date, COALESCE(service_start_date, curr_date)) + 1`。
▶ **示例（含完整算式）**
> ① 下一阶段已开始 — 7727004408：first_legal_start_date = 2025-07-28（透传自 `newrez.firstlegaldate`）、service_start_date = 2026-02-16
> ⇒ first_legal_stage_days = datediff(2025-07-28, 2026-02-16) + 1 = 203 + 1 = **204**（与 prod 一致）。
>
> ② 另一例 — 700082880000091：first_legal_start_date = 2026-03-12、service_start_date = 2026-05-13
> ⇒ first_legal_stage_days = datediff(2026-03-12, 2026-05-13) + 1 = 62 + 1 = **63**（与 prod 一致）。

### 37. 首次法律 阶段内 LM 天数  (`bpms.sync_fcl_stage_info.first_legal_in_lm_days`)

_阶段内与开启 LM 周期重叠天数。_

**来源 / Source (L1)**
- Newrez: `newrez.portnewrezfc`  （仅 Newrez 提供此明细）

**流动顺序 / Flow:** ①portnewrezfc → ②basic_data_loan_fcl → ③fcl_stage_info → ④sync_fcl_stage_info
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `newrez.portnewrezfc` — —
- 2. `port.basic_data_loan_fcl` · (LM cycle) — source 源
- 3. `port.fcl_stage_info.first_legal_in_lm_days` — interval overlap (LM) 见 sql [pool:2246-2330](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L2246-2330)
- 4. `bpms.sync_fcl_stage_info.first_legal_in_lm_days` — sync passthrough [asset:925](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L925)

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
- 3. `port.fcl_stage_info.first_legal_on_hold_days` — interval overlap (Hold) 见 sql [pool:2215-2297](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L2215-2297)
- 4. `bpms.sync_fcl_stage_info.first_legal_on_hold_days` — sync passthrough [asset:925](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L925)

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
- 3. `port.fcl_stage_info.service_stage_days` — datediff+1 (inclusive) 见 sql [pool:2040-2076](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L2040-2076)
- 4. `bpms.sync_fcl_stage_info.service_stage_days` — sync passthrough [asset:925](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L925)

```sql
service_stage_days = datediff(day, service_start_date, COALESCE(judgment_available_date, curr_date)) + 1
-- end = 下一阶段(判决可得日)；若未到则取 curr_date
```
🔎 **说明** service 阶段端点：**end = COALESCE(下一阶段 judgment_available_date, curr_date)** [pool:2070-2072]。公式：`service_stage_days = datediff(service_start_date, COALESCE(judgment_available_date, curr_date)) + 1`。
▶ **示例（含完整算式）**
> ① 下一阶段已开始 — 7727000357：service_start_date = 2025-08-14（透传自 `newrez.servicecompletedate`）、judgment_available_date = 2026-01-26
> ⇒ service_stage_days = datediff(2025-08-14, 2026-01-26) + 1 = 165 + 1 = **166**（与 prod 一致）。
>
> ② 仍在 SERVICE（判决日未到） — 700082880000091（当前 stage=SERVICE）：service_start_date = 2026-05-13、judgment_available_date = NULL ⇒ end = curr_date = 2026-06-09
> ⇒ service_stage_days = datediff(2026-05-13, 2026-06-09) + 1 = 27 + 1 = **28**（curr_date = ETL 运行日；与 prod 一致）。

### 40. 送达 阶段内 LM 天数  (`bpms.sync_fcl_stage_info.service_in_lm_days`)

_阶段内与开启 LM 周期重叠天数。_

**来源 / Source (L1)**
- Newrez: `newrez.portnewrezfc`  （仅 Newrez 提供此明细）

**流动顺序 / Flow:** ①portnewrezfc → ②basic_data_loan_fcl → ③fcl_stage_info → ④sync_fcl_stage_info
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `newrez.portnewrezfc` — —
- 2. `port.basic_data_loan_fcl` · (LM cycle) — source 源
- 3. `port.fcl_stage_info.service_in_lm_days` — interval overlap (LM) 见 sql [pool:2246-2330](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L2246-2330)
- 4. `bpms.sync_fcl_stage_info.service_in_lm_days` — sync passthrough [asset:925](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L925)

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
- 3. `port.fcl_stage_info.service_on_hold_days` — interval overlap (Hold) 见 sql [pool:2215-2297](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L2215-2297)
- 4. `bpms.sync_fcl_stage_info.service_on_hold_days` — sync passthrough [asset:925](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L925)

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
- 3. `port.fcl_stage_info.publication_in_lm_days` — interval overlap (LM) 见 sql [pool:2246-2330](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L2246-2330)
- 4. `bpms.sync_fcl_stage_info.publication_in_lm_days` — sync passthrough [asset:925](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L925)

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
- 3. `port.fcl_stage_info.publication_on_hold_days` — interval overlap (Hold) 见 sql [pool:2215-2297](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L2215-2297)
- 4. `bpms.sync_fcl_stage_info.publication_on_hold_days` — sync passthrough [asset:925](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L925)

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
- 3. `port.fcl_stage_info.to_judgement_days` — countdown to judgement: future⇒datediff(curr_date, date) (no +1), past⇒0, none⇒NULL [pool:2085-2087,2388](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L2085-2087)
- 4. `bpms.sync_fcl_stage_info.to_judgement_days` — sync passthrough [asset:925](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L925)

```sql
case when fcjudgment_start_date is null then null when fcjudgment_start_date >= curr_date then datediff(day, curr_date, fcjudgment_start_date) else 0 end
```
🔎 **说明** 从当日（curr_date，纽约时区）到排定判决日的倒计天数——不加 1。三分支：未来日 ⇒ datediff(curr_date, 判决日)；过去日 ⇒ 0（下限封顶）；无日期 ⇒ NULL。
▶ **示例** ① 未来 — 7727004408：判决日 2026-08-21 ⇒ to_judgement_days = 73（datediff(2026-06-09,2026-08-21)）。② 过去 — 7727001179：判决日 2025-11-29（已过）⇒ 0。③ 无日期 ⇒ NULL。

### 45. 判决 阶段内 LM 天数  (`bpms.sync_fcl_stage_info.judgement_in_lm_days`)

_阶段内与开启 LM 周期重叠天数。_

**来源 / Source (L1)**
- Newrez: `newrez.portnewrezfc`  （仅 Newrez 提供此明细）

**流动顺序 / Flow:** ①portnewrezfc → ②basic_data_loan_fcl → ③fcl_stage_info → ④sync_fcl_stage_info
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `newrez.portnewrezfc` — —
- 2. `port.basic_data_loan_fcl` · (LM cycle) — source 源
- 3. `port.fcl_stage_info.judgement_in_lm_days` — interval overlap (LM) 见 sql [pool:2246-2330](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L2246-2330)
- 4. `bpms.sync_fcl_stage_info.judgement_in_lm_days` — sync passthrough [asset:925](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L925)

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
- 3. `port.fcl_stage_info.judgement_on_hold_days` — interval overlap (Hold) 见 sql [pool:2215-2297](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L2215-2297)
- 4. `bpms.sync_fcl_stage_info.judgement_on_hold_days` — sync passthrough [asset:925](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L925)

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
- 3. `port.fcl_stage_info.to_sale_days` — countdown to sale: future⇒datediff(curr_date, date) (no +1), past⇒0, none⇒NULL [pool:2091-2093,2393](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L2091-2093)
- 4. `bpms.sync_fcl_stage_info.to_sale_days` — sync passthrough [asset:925](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L925)

```sql
case when sale_start_date is null then null when sale_start_date >= curr_date then datediff(day, curr_date, sale_start_date) else 0 end
```
🔎 **说明** 从当日（curr_date，纽约时区）到排定拍卖日的倒计天数——不加 1。三分支：未来日 ⇒ datediff(curr_date, 拍卖日)；过去日 ⇒ 0；无日期 ⇒ NULL。
▶ **示例** ① 未来 — 7727001179：拍卖日 2026-06-23 ⇒ to_sale_days = 14（datediff(2026-06-09,2026-06-23)，不加 1）。② 过去 — 拍卖日已过 ⇒ 0。③ 无日期 ⇒ NULL。

### 48. 拍卖 阶段内 LM 天数  (`bpms.sync_fcl_stage_info.sale_in_lm_days`)

_阶段内与开启 LM 周期重叠天数。_

**来源 / Source (L1)**
- Newrez: `newrez.portnewrezfc`  （仅 Newrez 提供此明细）

**流动顺序 / Flow:** ①portnewrezfc → ②basic_data_loan_fcl → ③fcl_stage_info → ④sync_fcl_stage_info
**血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)**
- 1. `newrez.portnewrezfc` — —
- 2. `port.basic_data_loan_fcl` · (LM cycle) — source 源
- 3. `port.fcl_stage_info.sale_in_lm_days` — interval overlap (LM) 见 sql [pool:2246-2330](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L2246-2330)
- 4. `bpms.sync_fcl_stage_info.sale_in_lm_days` — sync passthrough [asset:925](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L925)

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
- 3. `port.fcl_stage_info.sale_on_hold_days` — interval overlap (Hold) 见 sql [pool:2215-2297](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L2215-2297)
- 4. `bpms.sync_fcl_stage_info.sale_on_hold_days` — sync passthrough [asset:925](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L925)

```sql
on_hold = datediff(greatest(stage_start, hold_start), least(stage_end, coalesce(hold_end,curr_date))) + 1; only open holds (fchold1..3 of basic_data_loan_fcl); pivoted per stage
```
🔎 **说明** 阶段窗口与「进行中」Hold（basic_data_loan_fcl 的 fchold1..3）的重叠天数：datediff(greatest(stage_start, hold_start), least(stage_end, coalesce(hold_end, 今天)))+1；按阶段后取 max()。
▶ **示例** 7727000569：Service 阶段 ∩ 开启 Hold ⇒ service_on_hold_days = 87（prod）。


## 系统 / 审计列

### 50. 系统 / 审计列

_应用/ETL 管理列（非 servicer 来源）。_

**列 / Columns:** `create_time, update_time, create_user, create_dept, update_user, status, is_deleted, tenant_id`

**说明 / Note:** 列：create_time, update_time, create_user, create_dept, update_user, status, is_deleted, tenant_id。tenant_id ← GET_LOAN_TENANT_ID(portfunding ⋈ basic_data_trust_funding，[asset:932-936](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L932-936))；create_*/update_* 由 BPS 应用写；is_deleted 视图恒 0；status 应用标志。非 servicer 数据。


> 本文档共 50 个字段。
