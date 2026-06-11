# 32 · 全 Pipeline 逐字段 Mapping + 生产数据举例（doc 32 导读）

> 本文是 **导读**。逐字段内容、规则、生产实测举例都在配套工作簿
> [`docs/32_fcl_pipeline_field_mapping.xlsx`](../32_fcl_pipeline_field_mapping.xlsx)。
> 本 MD 只讲「为什么、怎么读、范围」，不复制字段内容（单一真源是 JSON，见下）。

## 文档信息

| 项目 | 内容 |
|------|------|
| **文档目的** | **Why**：把整条 FCL pipeline 的数据处理「演」出来——每个字段从 servicer 原始列，经每一层（L1→L5），到 BPS sync 表，逐字段写清**每跳转换规则**，并用**生产实测数据**举例。**What problem**：doc 19 是「按表/按贷款的 raw dump」、doc 26–31 是叙述式逐字段血缘；本文提供一份**可筛选、可对账、带色卡与导航**的 Excel，把「字段 × 逐层规则 × 生产实测」三者合一。**Scope**：Phase 1 pilot **只覆盖主链 `bpms.sync_loan_foreclosure`**（含主链中间表）；其余 4 链与全部 ~23 表见 Phase 2。**System fit**：Excel 为可对账视图，叙述仍指回 doc 25–31；与 doc 02/13/14 的字段口径一致。 |
| **目标读者** | 数据工程师 · 业务分析 · 对账/校验人员 · servicer onboarding · 未来 AI 会话 |

**修订历史：**

| 日期 | 作者 | 版本 | 变更 | 相关 |
|------|------|------|------|------|
| 2026-06-10 | AI Agent (Claude Opus 4.8) | v1 | Phase 1 pilot：主链 sync_loan_foreclosure 逐字段 mapping + 20 笔生产举例 + 多 as-of 改期演示 + BPS 截图三方对账 | doc 25/26, 02, 13, 14；skill `excel-pipeline-lineage` |

**依赖（单一真源 JSON，脚本只排版）：**
- `outputs/fcl_lineage_source.json` — 逐字段 hops + 每跳规则 + 代码出处（与 doc 26 同源）
- `outputs/fcl_table_meta.json` — 23 表业务含义/血缘元数据
- `outputs/fcl_field_meanings.json` — 逐表字段含义
- `outputs/fcl_pipeline_examples.json` — prod 只读拉取的 20 笔举例 + 改期历史 + BPS 截图锚点
- 生成器：`outputs/build_fcl_pipeline_mapping_xlsx.txt`（`python - < …txt` 运行，幂等可重跑）

---

## 怎么读这个工作簿

打开 xlsx，首张 **🧭 导航 Index** 点「➤ 打开」可跳到任意 sheet。

**仿 doc 19**：全局/导航页 + 分析视图（字母）+ 逐表页（圈号·层级标签 src/mid/bps）。

| Sheet | 看什么 |
|---|---|
| **① 表清单 索引** | 首张索引，**分层分组**（分析视图 / 一 Newrez源 src / 二 Redshift中间层 mid / 三 BPS对接 bps / 四 字典 dic）+ 列数 + 「➤ 打开」跳转链 |
| **⓪ 表说明与全链路血缘** | 全 23 表总览：层级 / 业务含义 / pipeline 作用 / 上下游链路 / 粒度（仿 doc 19 ⓪） |
| **⓪b 全局Pipeline图** | L1→L5 网格图：各层表 + 主线/逾期支线/维度字典 + 图例（仿 doc 19 ⓪b） |
| **A 导读·色卡·样本** | 读法、as-of/多天说明、**转换类型色卡 + 一行定义**、20 笔样本清单 |
| **B 主表逐字段 Mapping** | 一字段一行：目标字段 → L1 servicer 源 → L4 fcl 族 → L4 foreclosure 投影(+代码) → L5 upsert/视图规则 → **转换类型**(色卡) → 代表样本。可筛选 |
| **C 生产数据矩阵 20 笔** | 20 笔贷款 × 主表关键字段**最新快照实测值** |
| **D 多as-of 改期演示** | `7727003984`（改期 12 次）+ `7727000367`（稳定值反例）的多天历史，演示 `set_date` vs `projected` |
| **E BPS 截图证据** | 嵌入 BPS UI 截图 + 代码⇄Redshift⇄BPS UI 三方对账 |
| **F 逻辑覆盖矩阵** | PrefectFlow FCL **16 条处理逻辑**，每条 ≥1 示例 loan + 转换类型 + **历史依赖**（最新/去重/全历史）+ **演示层**（端到端 bpms / Redshift 层）。可筛选 |
| **② src·portnewrezfc … ⑳ bps·view_loan_details** | 主链每张表（含中间表）一个 sheet：业务含义/全链路血缘 + 全字段清单。tab 名带 **src·/mid·/bps·** 层级标签 |

> **关于圈号 ②⑨⑩⑪⑱⑳**：是「全 FCL pipeline 23 表的**全局编号**」（与 doc 19/25、`fcl_table_meta.json` 一致）。② src·portnewrezfc、⑨ mid·temp、⑩ mid·fcl、⑪ mid·foreclosure、⑱ bps·sync主表、⑳ bps·视图。缺号（③④…⑬⑲…）是本 pilot 尚未纳入的表，**Phase 2 补齐，不是排序错误**（① 表清单索引里这些表已列出、标「Phase 2 待补」）。分析视图用字母 A–E，与表号区分。

**转换类型** 一行定义（A 总览页色卡同款）：直传＝值与列名都不变的纯透传；**改名**＝值不变但中途列名改过；**首见日**＝取 `min(dataasof)`（当前值首次出现日，需多天历史）；天数重算＝存储天数+datediff(dataasof→运行日)；decode解码＝字典译码；CASE派生＝条件分支/拼接；常量NULL＝硬编码常量/空；其他＝主键/审计/视图列。

## 关键口径（已核代码 + prod 实证）

1. **`projected` = 当前(最新 as-of)值**；**`set_date` = 该当前值首次出现的 `dataasof`**（`min(dataasof WHERE 值=当前值)`，`basic_data_pool_config.py:300-303`）。改期链只有多天历史可见（见 Sheet ③）。
2. **多天数据的意义**：仅 `*_set_date`/`judgement_hearing_set`/`*_days`（首见、天数重算）需多天；直传/decode 字段多天恒等，取最新快照即可。`basic_data_loan_fcl` 保留全部每日快照（943 个 dataasof）；`basic_data_loan_foreclosure`=MAX(dataasof) 每贷款最新；sync 主表当前态无 as-of。
3. **`summary_current_step` = `fcstage` 直传**（`pool:282`；`currentmilestone` ETL 未使用）——与本仓库 doc 13/14 v 最新更正一致。
4. **`summary_servicer_number`**：20 笔实测全 NULL（prod 已知异常，doc 14 v34）。
5. **「取最新」橙色边两套规则**（见 D 页 7727003984 三日期对照 + F 矩阵注）：首见追踪 `min(dataasof)`（`sale_date_set_date`/`judgement_hearing_set_date`，需全历史）vs 纯取最新直传（`sale_date_projected_date`、`summary_last_step_completed_date`=pool:284 直传 `lastfcstepcompleteddate`，改期不更新、≠首见）。详见 **doc 33 §2.5.1**。

## 范围与分期
- **本期（Phase 1）**：主链 `sync_loan_foreclosure`（66 个已录字段 / 表 72 列）+ 主链中间表逐表 sheet。
- **后续（Phase 2）**：其余 4 链（`sync_fcl_stage_info` 接 doc 27/31、`_hold`、`_loss_mitigation`、`_bankruptcy`）+ 剩余中间表，补齐全部 ~23 表。
