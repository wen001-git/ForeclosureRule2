# doc 31 — FCL 阶段窗口规则速查（start / end / days / in_lm / on_hold）

> <!-- RULEGLOSS_PTR -->📖 **术语解释**：本文 `rule` 列的技术语句 → 易懂中文 + 数学公式，见 [doc 25 · 逐跳转换规则速查（附录）](25_fcl_lineage_overview.md)。
> <!-- CODEGLOSS_PTR -->🔧 **code 列图例**：`pool`=ETL 建表/SQL 代码 `basic_data_pool_config.py` · `asset`=BPS 同步 SQL `asset_managment_config.py` · `view`=BPS 视图定义；冒号后数字=该文件**行号**（链接可点）。

## 文档目的（Document Purpose）

- **为什么存在**：`bpms.sync_fcl_stage_info` 每个 FCL 阶段（DEMAND / NOI / REFERRAL / FIRST_LEGAL / SERVICE / PUBLICATION / JUDGEMENT / SALE）有 5 类时间列——`<X>_start_date / <X>_end_date / <X>_stage_days / <X>_in_lm_days / <X>_on_hold_days`——它们的取值规则**散落在 doc 27 的 25+ 个 §**（§9-§13/§14-§23/§28-§41），且**命名反直觉**（如 `servicecompletedate` 实际喂 SERVICE 阶段的 start，不是 end），新人/审核人很难快速建立全局认知。
- **解决什么问题**：用一篇集中速查文档把 8 个 stage × 5 类列的规则一表读完，配真实数据工作例，把容易踩的坑显式标出。
- **范围（Scope）**：
  - **包含**：8 个 stage × `start_date / end_date / stage_days` 的规则与来源；`in_lm_days / on_hold_days` 的完整 SQL 语义（取自 PrefectFlow pool:2215-2330）。
  - **不包含**：每个字段的逐跳 lineage（去 doc 27 看）；BPS 视图字段（去 doc 26）；BPS UI 字段映射（去 doc 13/16）。
- **系统位置**：FCL 字段血缘 hub（doc 25）的「阶段/天数」分支的**规则速查入口**；doc 27 的**横向汇总视图**。

## 目标读者

数据工程师 · 业务分析师 · 验证人员 · 接入工程师 · 新成员 · 未来 AI 会话

## 修订历史

| 日期 | 作者 | 版本 | 变更 | 关联 |
|------|------|------|------|------|
| 2026-06-10 | AI Agent (Claude Opus 4.7 1M) | v1 | 初稿——整合 stage start/end/stage_days/in_lm/on_hold 规则；含 pool:2038-2076 / pool:2215-2330 Code-First 实证；4 真实 loan 工作例 | doc 27 §9-§41 · pool:2038-2076 · pool:2215-2330 |

## 依赖（Dependencies）

- `port.fcl_stage_info`（Redshift，FCL stage 计算的中间产物）由 `basic_data_pool_config.py` pool:2037-2440 构建，MySQL 副本经 L5 同步到 `bpms.sync_fcl_stage_info`。
- `port.basic_data_loan_fcl`（FCL 事实表）提供 stage 触发日期。
- `port.basic_data_loan_foreclosure_loss_mitigation` 提供 LM 周期（cycle_opened_date / cycle_closed_date）。
- `tempfc.current_fcl_hold_temp`（运行时临时表）提供 Hold 区间（hold_start_dt / hold_end_dt / hold_stage）。
- `tempfc.current_date_new_york.curr_date` 提供 ETL 运行日（NY 时区）。
- `tempfc.current_fcl_business_2_temp` 提供长格式的 `(loanid, stage, stage_start_dt, stage_end_dt)`，是 in_lm/on_hold 计算的左表。**注**：该表的 stage_end_dt = `logic_<stage>_end_date`（≠ `business_1.<X>_end_date`；DEMAND=curr_date，其余=下一阶段 start 或 curr_date，pool:2028-2105；§8 OQ1 已关闭）。

## 已知局限（Known Limitations）

- ~~§8 Open Question 1~~ **已于 2026-06-14 关闭**：`business_2.stage_end_dt` = `logic_<stage>_end_date`（DEMAND=curr_date，pool:2028-2105 取证），且 in_lm 归因 `rnk=1` 取最近 open cycle（pool:2235-2266）；loan 7727000131 demand_in_lm 已对账（18=datediff(2026-05-28,2026-06-14)+1）。详见 §5.3 / §8 OQ1。

---

## 1. 模型直观（10 秒读懂）

每个 stage 是一个**时间窗口** `[start_date, end_date]`：

- **start_date** = **透传**自 servicer 报的"该阶段触发事件日"列（一律单列直传，无转换）。
- **end_date** = 通常**派生**自下一阶段的 start_date（少数例外见 §3）；下一阶段未到则 NULL。
- **stage_days** = 该窗口长度，公式 `datediff(start, COALESCE(end, curr_date)) + 1`（含端点）。
- **in_lm_days** = 该窗口与「**正在 open** 的 LM 周期」的重叠天数（**只取一条最近 open**，详 §5）。
- **on_hold_days** = 该窗口与「**正在 open** 的 Hold」的重叠天数（同 §5 取一条）。

⚠️ 容易踩的坑：① `servicecompletedate` → SERVICE **start**（不是 end）；② `demand_end_date` 不参与 demand_stage_days；③ in_lm/on_hold **每 stage 只算一条 OPEN 周期**，不是求和。

---

## 2. stage_start_date 来源总表

| stage | start = 哪个 Newrez 列（透传） | port 中间名 | 反直觉 | Code-First |
|---|---|---|---|---|
| **DEMAND** | `newrez.portnewrezfc.demandsentdate` | `basic_data_loan_fcl.demandsentdate` | — | [pool:2037](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L2037) |
| NOI | — | — (null_in_build) | — | [pool:2043-2046](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L2043-2046) |
| **REFERRAL** | `newrez.portnewrezfc.fcreferraldate` | `basic_data_loan_fcl.referral_start_date` | — | [pool:2048](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L2048) |
| **FIRST_LEGAL** | `newrez.portnewrezfc.firstlegaldate` | `basic_data_loan_fcl.legal_start_date` | — | [pool:2058](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L2058) |
| **SERVICE** | `newrez.portnewrezfc.servicecompletedate` | `basic_data_loan_fcl.service_start_date` | **⚠️ 是** — 字面像"完成日"，实际是 SERVICE 阶段的**起点**（送达完成后、判决前的等待窗口的左端） | [pool:2068](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L2068) |
| PUBLICATION | — | — (null_in_build) | — | [pool:2078-2081](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L2078-2081) |
| JUDGEMENT | `newrez.portnewrezfc.fcjudgmenthearingscheduled` | `basic_data_loan_fcl.fcjudgment_start_date` | 注：BPS 列名 `judgement_start_date` 来自此源；不是 `fcjudgmententered` | (在最终 INSERT 中映射为 `judgement_start_date`) |
| SALE | `newrez.portnewrezfc.fcscheduledsaledate` | `basic_data_loan_fcl.sale_start_date` | — | (同上) |

**核心规律**：start_date = **触发该阶段的事件日**。SERVICE 命名反直觉是因为「送达完成」是该阶段的触发事件（送达完成后进入等待判决期）。

---

## 3. stage_end_date 派生规则总表

| stage | end_date 规则 | 是否单列透传 | 未到时取值 | Code-First |
|---|---|---|---|---|
| **DEMAND** | = `demandexpirationdate`（透传，仅作窗口右端展示） | **透传** | (透传值；可能为 NULL) | [pool:2038](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L2038) |
| NOI | — | (null_in_build) | NULL | pool:2043-2046 |
| **REFERRAL** | = 下一阶段 `first_legal_start_date` | **派生** | NULL | [pool:2049,2365](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L2049) |
| **FIRST_LEGAL** | = 下一阶段 `service_start_date` | **派生** | NULL | [pool:2059,2370](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L2059) |
| **SERVICE** | = 下一阶段 `judgment_available_date` | **派生** | NULL | [pool:2069,2376](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L2069) |
| PUBLICATION | — | (null_in_build) | NULL | pool:2078-2081 |
| JUDGEMENT | 硬编码 NULL（最终 INSERT `null as judgement_end_date`） | — | NULL | (final INSERT in pool:2330+) |
| SALE | 硬编码 NULL（最终 INSERT `null as sale_end_date`） | — | NULL | (final INSERT in pool:2330+) |

**核心规律**：除 DEMAND（透传 demandexpirationdate 作展示）外，其余 end_date 都是**下一阶段 start 的派生**。JUDGEMENT/SALE 末端阶段在 sync 表里 end_date 硬编码 NULL。

---

## 4. stage_days 公式 + 工作例

### 公式

```sql
-- 通用（REFERRAL/FIRST_LEGAL/SERVICE）：
<X>_stage_days = datediff(day,
                          <X>_start_date,
                          COALESCE(<X>_end_date, curr_date)) + 1

-- DEMAND 特殊：
demand_stage_days = datediff(day, demand_start_date, curr_date) + 1
                    -- 不取 demand_end_date 作右端
```

含端点（+1）。`curr_date` = `tempfc.current_date_new_york.curr_date`（ETL 运行日，2026-06-10 测为 2026-06-09）。

### 工作例（Code-First MCP 实测，2026-06-10）

**Loan 7727000357**（Judicial · 已 SERVICE 结束，JUDGEMENT 阶段）

| stage | start | end | stage_days | 算式 |
|---|---|---|---|---|
| DEMAND | 2024-11-20 | 2024-12-25（透传，不用） | 567 | datediff(2024-11-20, 2026-06-09)+1 = 566+1 = **567** |
| REFERRAL | 2025-01-23 | 2025-06-11 | 140 | datediff(2025-01-23, 2025-06-11)+1 = 139+1 = **140** |
| FIRST_LEGAL | 2025-06-11 | 2025-08-14 | 65 | datediff(2025-06-11, 2025-08-14)+1 = 64+1 = **65** |
| SERVICE | 2025-08-14 | 2026-01-26 | 166 | datediff(2025-08-14, 2026-01-26)+1 = 165+1 = **166** |

**Loan 700082880000091**（当前 stage = SERVICE）

| stage | start | end | stage_days | 算式 |
|---|---|---|---|---|
| DEMAND | 2025-12-29 | 2026-01-13（不用） | 163 | datediff(2025-12-29, 2026-06-09)+1 = 162+1 = **163** |
| REFERRAL | 2026-01-20 | 2026-03-12 | 52 | datediff(2026-01-20, 2026-03-12)+1 = 51+1 = **52** |
| FIRST_LEGAL | 2026-03-12 | 2026-05-13 | 63 | datediff(2026-03-12, 2026-05-13)+1 = 62+1 = **63** |
| **SERVICE** | **2026-05-13**（=`servicecompletedate`，看清这是 start 不是 end）| **NULL**（判决未到）| **28** | datediff(2026-05-13, curr_date 2026-06-09)+1 = 27+1 = **28** |

**Loan 7727004408**（多 stage 闭合）

| stage | start | end | stage_days | 算式 |
|---|---|---|---|---|
| REFERRAL | 2024-03-08 | 2025-07-28 | 508 | datediff(2024-03-08, 2025-07-28)+1 = 507+1 = **508** |
| FIRST_LEGAL | 2025-07-28 | 2026-02-16 | 204 | datediff(2025-07-28, 2026-02-16)+1 = 203+1 = **204** |
| SERVICE | 2026-02-16 | 2026-05-14 | 88 | datediff(2026-02-16, 2026-05-14)+1 = 87+1 = **88** |

**Loan 700082700000033**（仍在 REFERRAL）

| stage | start | end | stage_days | 算式 |
|---|---|---|---|---|
| DEMAND | 2025-12-01 | 2026-01-05（不用） | 191 | datediff(2025-12-01, 2026-06-09)+1 = 190+1 = **191** |
| **REFERRAL** | 2026-02-11 | **NULL**（首次法律未到） | **119** | datediff(2026-02-11, curr_date 2026-06-09)+1 = 118+1 = **119** |

---

## 5. in_lm_days / on_hold_days 详细规则（Code-First from pool:2215-2330）

### 5.1 核心 SQL 结构（简化伪 SQL）

```sql
-- Step 1: per-row (loanid, stage, single open cycle) detail
SELECT *,
  rank() OVER (PARTITION BY loanid, stage ORDER BY lm_stage) AS rnk
FROM (
  SELECT b2.loanid, b2.stage, b2.stage_start_dt, b2.stage_end_dt,
         l.cycle_opened_date,
         COALESCE(l.cycle_closed_date, curr_date) AS lm_end_dt,
         l.lm_stage,
         GREATEST(b2.stage_start_dt, l.cycle_opened_date) AS in_lm_start_dt,
         LEAST  (b2.stage_end_dt,   COALESCE(l.cycle_closed_date, curr_date)) AS in_lm_end_dt,
         DATEDIFF(day, in_lm_start_dt, in_lm_end_dt) + 1 AS in_lm_days
  FROM tempfc.current_fcl_business_2_temp b2
  LEFT JOIN (
    SELECT *,
      ROW_NUMBER() OVER (PARTITION BY loanid ORDER BY cycle_opened_date DESC) AS lm_stage
    FROM port.basic_data_loan_foreclosure_loss_mitigation   -- ⚠️ 不带 fctrdt 过滤（全历史）
  ) l
    ON b2.loanid = l.loanid
   AND b2.stage_start_dt <= l.cycle_opened_date
   AND b2.stage_end_dt   >= l.cycle_opened_date   -- cycle 必须 open 在 stage 窗口内
  WHERE l.cycle_closed_date IS NULL                -- 只取 OPEN
) t
WHERE rnk = 1;     -- 每 (loanid, stage) 只保留 lm_stage 最小（=cycle_opened 最新）那一条

-- Step 2: pivot to wide form per loanid
SELECT loanid,
  MAX(CASE WHEN stage='DEMAND'      THEN in_lm_days END) AS demand_in_lm_days,
  MAX(CASE WHEN stage='REFERRAL'    THEN in_lm_days END) AS referral_in_lm_days,
  ...
FROM step1
GROUP BY loanid;
```

Hold 逻辑完全镜像，**唯一差异**：

| 差异点 | LM | Hold |
|---|---|---|
| 输入表 | `port.basic_data_loan_foreclosure_loss_mitigation`（**不带 fctrdt 过滤**——全历史 cycle 行都参与） | `tempfc.current_fcl_hold_temp`（**带 `b2.fctrdt = dataasof`** 过滤——只用同 fctrdt 快照的 hold 行） |
| OPEN 过滤 | `cycle_closed_date IS NULL` | `hold_end_dt IS NULL` |
| 排序键 | `lm_stage = ROW_NUMBER OVER (PARTITION BY loanid ORDER BY cycle_opened_date DESC)`——rnk=1 选 **cycle_opened 最近**的 | `hold_stage`（外部表预生成，含义类似优先级） |

### 5.2 关键规则（要点）

1. **OPEN-only**：只考虑当前未关闭的 LM 周期 / Hold（`*_closed_date IS NULL`）。
2. **cycle 必须 open 在 stage 窗口内**：约束 `stage_start ≤ cycle_opened ≤ stage_end`——cycle 必须**在该 stage 期间被打开**才计入。在 stage 之前打开、延续进 stage 的 cycle **不计**。
3. **每 (loanid, stage) 只算一条**：`rank() OVER (PARTITION BY loanid, stage ORDER BY lm_stage) WHERE rnk=1`——LM 选 cycle_opened 最近的、Hold 选 hold_stage 最小的。**不是 SUM、不是 MAX(days)**，是**取一条记录**。
4. **聚合的 max() 是防御性**：第二步 `MAX(<X>_in_lm_days) GROUP BY loanid` 因为每 (loan, stage) 已唯一一行，max() 实际等同于 "the value for that stage"。
5. **end_date 替代**：`in_lm_end_dt = LEAST(stage_end, COALESCE(cycle_closed_date, curr_date))`——OPEN cycle 用 curr_date 截止；stage 已结束则用 stage_end。
6. **curr_date 来源**：`tempfc.current_date_new_york.curr_date`（ETL 运行日，NY 时区；2026-06-10 实测 = 2026-06-09）——**不是 fctrdt**。
7. **LM vs Hold 历史范围**：LM 拉全历史，可能覆盖远早于当前 fctrdt 的 cycle；Hold 仅同 fctrdt 快照。这造成两者在历史 loan 上行为有差异。

### 5.3 工作例

**Loan 7727000131 · LM cycles**（Code-First 全历史，cycle_closed_date IS NULL 的 3 条）

| lm_stage（按 cycle_opened DESC）| cycle_opened_date | cycle_closed_date |
|---|---|---|
| 1 | 2026-05-28 | NULL（当前 open） |
| 4 | 2025-10-20 | NULL（历史 open，已不在 latest snapshot） |
| 5 | 2025-09-15 | NULL（历史 open，已不在 latest snapshot） |

注：lm_stage 2/3/6 是 closed cycle，被 OPEN 过滤掉。

**对 DEMAND stage 应用规则**（demand window：start=`demand_start_date`=2025-08-15；**end=`logic_demand_sent_end_date`=`curr_date`**——DEMAND 窗口端恒取 curr_date，**不取** `demand_end_date`=demandexpirationdate=2025-09-19，pool:2039/2028-2105 实测）：

- 窗口 = [2025-08-15, **curr_date 2026-06-14**]（最新快照 fctrdt 2026-06-12；curr_date 由 demand_stage_days=304=datediff(2025-08-15,curr)+1 反解得 2026-06-14）。
- 过滤"cycle 在 stage 窗口内 open"：三条 OPEN cycle（2026-05-28 / 2025-10-20 / 2025-09-15）**全部** ∈ [2025-08-15, 2026-06-14]。
- 多条命中 → `rnk=1` 取 **cycle_opened 最近** 的一条 = **2026-05-28**（lm_stage=1），**不是** 最早的 2025-09-15。
- 算式：`datediff(greatest(2025-08-15, 2026-05-28), least(curr_date 2026-06-14, curr_date)) + 1 = datediff(2026-05-28, 2026-06-14) + 1 = 17 + 1 = 18`。
- **prod 实测 demand_in_lm_days = 18 ✓ 完全对账**（doc 早期版本在 2026-06-08 快照记为 14：同机制，该快照 curr_date≈2026-06-10 → datediff(2026-05-28,2026-06-10)+1=14，亦对账）。

> **本例曾是 §8 OQ1（已于 2026-06-14 关闭）**：早期手算 5 天用了两个错误前提——① 误把 demand 窗口端当成 `demand_end_date`（实为 curr_date）；② 误取最早的 open cycle 2025-09-15（实为 rnk=1 取最近的 2026-05-28）。两处均经 Code-First 取证 `current_fcl_business_2_temp`/in_lm 归因（pool:2028-2105 / 2235-2266）订正，无残留未解。

---

## 6. 容易混淆的 5 点

1. **`servicecompletedate` → SERVICE 阶段的 start，不是 end**。字面像"送达完成"，但 FCL stage 模型里 SERVICE 阶段定义为"送达完成后、判决可得前的等待窗口"，所以送达完成日是该窗口的左端。
2. **`demand_end_date` 不参与 `demand_stage_days` 计算**。demand 是唯一一个 stage_days 公式特殊的——一律用 curr_date 作右端，不论 demand_end_date 是否填充。
3. **end_date = NULL 时，stage_days 用 curr_date 数**——COALESCE 行为，不是 NULL 传播为 NULL。
4. **`curr_date` ≠ `fctrdt`**。`curr_date` 来自 `tempfc.current_date_new_york.curr_date`，是 ETL **运行**当天（NY 时区，2026-06-10 实测 2026-06-09）；`fctrdt` 是数据**报告日**（一天前，2026-06-08）。stage_days/in_lm/on_hold 都用 curr_date。
5. **in_lm/on_hold 每 stage 只算一条 OPEN 周期/Hold 的重叠**——不是把所有 OPEN cycles 求和，也不是 MAX 多条的 days。代码用 `rank() ... rnk=1` 强制取一条（LM 是 cycle_opened 最近的，Hold 是 hold_stage 最小的）。**且 cycle 必须 OPEN 在 stage 窗口内**（不是窗口与 cycle 时间区间相交即可计入）。

---

## 7. Code-First 引用

| 主题 | 代码位置 |
|---|---|
| stage_start_date 透传 | [pool:2037-2068](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L2037-2068) |
| stage_end_date 派生 | [pool:2049,2059,2069,2076](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L2049) |
| stage_days 公式（含 demand 特殊） | [pool:2038-2076](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L2038-2076) |
| in_lm_days SQL（完整） | [pool:2246-2330](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L2246-2330) |
| on_hold_days SQL（完整） | [pool:2215-2297](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L2215-2297) |
| 最终 INSERT 到 `port.fcl_stage_info` | pool:2330+（同文件，紧跟 in_lm pivot） |
| sync to `bpms.sync_fcl_stage_info` | [asset:925](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L925) |

---

## 8. Open Questions / 待确证

### ~~OQ1~~ — ✅ 已关闭（2026-06-14）：`business_2_temp.stage_end_dt` 的真实取值

**结论**：`tempfc.current_fcl_business_2_temp.stage_end_dt` = 各 stage 的 **`logic_<stage>_end_date`**（pool:2028-2105 实测），**不是** `<stage>_end_date`：
- **DEMAND** → `curr_date`（pool:2039；恒取运行日，不取 demandexpirationdate）。
- referral/first_legal/service → 下一阶段 start（无则 `curr_date`）。
- judgement/sale → `least(下一里程碑, curr_date)`。
- **noi / publication → NULL**（无 logic 窗口端 → 这两阶段不计 in_lm/on_hold）。

**原"差 9 天"的两处错因**（早期 §5 工作例）：① 误用 `demand_end_date`(2025-09-19) 作窗口端（实为 curr_date）；② 误取最早 open cycle 2025-09-15（实为 in_lm 归因 `rnk=1` 取 **cycle_opened 最近** 的一条，pool:2235-2266 `ROW_NUMBER ... ORDER BY cycle_opened_date DESC`）。订正后 loan 7727000131：窗口[2025-08-15, curr 2026-06-14] ∩ 最近 open cycle 2026-05-28 → `datediff(2026-05-28,2026-06-14)+1 = 18` = prod 实测 ✓。

**取证**：本会话 Code-First 读 `basic_data_pool_config.py` pool:2028-2105（business_1/2 窗口端）+ pool:2204-2266（in_lm/on_hold 归因）+ pool:1779-1781（curr_date 参数）。同机制已在 doc 32 ⑬ 的 `*_in_lm_days`/`*_on_hold_days` 公式列「数据代入·分步运算」工作示例中对 2 笔 demo loan 32/32 对账。

### OQ2 — `hold_stage` 的具体定义（影响 Hold rnk=1 的选取）

代码 `tempfc.current_fcl_hold_temp.hold_stage` 是外部预生成列；我们看到的代码（pool:2215-2330）只引用它做 ORDER BY，没看到生成逻辑。需另行取证（可能在 hold_temp 构造段）。

---

## 9. 相关文档

- **[doc 27 — `bpms.sync_fcl_stage_info` 逐字段血缘](27_lineage_sync_fcl_stage_info.md)**：每个字段的完整跳链（Newrez → Redshift → BPS sync），含各字段示例。
- **[doc 25 — FCL 字段血缘总览](25_fcl_lineage_overview.md)**：字段血缘 hub，从这里进入各 sync 表。
- **[doc 13 — Newrez FCL BPS 展示映射](13_newrez_fcl_bps_display_mapping.md)**：BPS UI 字段 → Newrez 源（含 Days in Stage/LM/Hold 的 UI 来源）。
- **[doc 14 — BPS 驱动的 Servicer FCL 数据接口](14_bps_driven_servicer_fcl_interface.md)**：servicer 字段规范（含各 stage 触发字段的标准定义）。
- **[doc 22 — BPS agg-summary 止赎页取数](22_bps_fcl_timeline_sourcing.md)**：agg-summary 页 Time Line/Stage tab 如何取自 `sync_fcl_stage_info`。
