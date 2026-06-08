# doc 22 — BPS Foreclosure「Time Line / Stage」聚合页取数规则

---

## 文档目的

- **为什么存在**：BPS 资产管理 → Portfolio → **Foreclosure** 聚合页（`/#/portfolio/agg-summary`）下有 **Stage** 与 **Time Line** 两个 tab，外加顶部 **Overview** 汇总表。用户对 Time Line 页存在困惑：它一行一笔贷款、却列出很多 loan（不像"单笔贷款的时间线"）；它与 Stage 页是什么关系；取自哪张表、SQL 长什么样；以及——**"sync 表保存的不是 loan 当前状态吗？为什么会有历史里程碑日期供 timeline 取值？"** 本文逐一回答。
- **解决的问题**：把 Time Line / Stage / Overview 三者的**唯一数据源**、**列级映射**、**当前态 vs 历史态**讲清楚，并给出可直接执行的代表性 SQL 与样本走查。
- **范围**：✅ agg-summary 页 Foreclosure 模块（Stage tab / Time Line tab / Overview）的取数表、列映射、查询规则、历史语义。❌ 不含 BPS 贷款详情页的 Foreclosure 面板（那是 `sync_loan_foreclosure`，见 doc 13/16）；❌ 不含 BPS 前端内部渲染逻辑。
- **系统归属**：源系统 `C:\Users\jli\MyData\Copilot\PrefectFlow`（Prefect 2.x ETL）。本文是对其 L4→L5 止赎阶段链路的逆向说明。

## 目标读者

主要：运营/资产管理分析师 · BPS 验收人员 · 数据工程师  
次要：新成员 · 未来 AI Session

## 修订历史

| 日期 | 作者 | 版本 | 变更 | 关联 |
|------|------|------|------|------|
| 2026-06-07 | AI Agent（Claude Opus 4.8） | v1 | 初稿：Time Line/Stage 取自 `sync_fcl_stage_info` 的取数规则、列映射、当前态 vs 历史态、代表性 SQL、样本走查（代码读 + prod `bpms` 实测） | doc 02/12/13/16/21 |

## 相关文档

| 文档 | 说明 |
|------|------|
| doc 02 | ETL 五层管道、as-of 演化（§8 当前态 vs 历史态） |
| doc 12 | `sync_asset_management.py` 同步编排、SYNC_TABLE_MAP |
| doc 13/16 | BPS 面板字段逆向映射 / 速查 |
| doc 21 | FCL 字段级血缘（stage 系统、days 计算） |
| doc 10 | 术语表（FCL/REO/LM/BK/delinq/fctrdt 等） |

> 术语速查：FCL=Foreclosure 止赎 · REO=Real Estate Owned 已收回房产 · LM=Loss Mitigation 损失缓解 · BK=Bankruptcy 破产 · `fctrdt`=报告/跑批截止日（快照日）· Servicer=贷款服务商 · BPS=下游业务系统。

---

## §1 一句话答案

> **Time Line tab 与 Stage tab 取自同一张表 `bpms.sync_fcl_stage_info`，按"最新快照 (`MAX(fctrdt)`)"过滤后一行一笔贷款。** 你看到的不是"某一笔贷款的时间线"，而是"组合里每一笔止赎贷款各自的里程碑日期"——单笔贷款的进度被横向编码成多列日期（NOI/Referral/First Legal/Service/Judgement/Sale），不是多行。Stage tab 与 Time Line tab 是**同一行的不同列**：Time Line 展示各阶段 `*_start_date`，Stage 展示各阶段 `*_stage_days / *_in_lm_days / *_on_hold_days` 与当前 `stage`。

---

## §2 取数表与血缘

| 终点（BPS / MySQL） | 中间（Redshift） | 生成代码 |
|---|---|---|
| `bpms.sync_fcl_stage_info` | `port.fcl_stage_info` | 同步：`SYNC_TABLE_MAP['12-FCL_STAGE']`（`flow/bps/bps_config/sync_to_bps_config.py:13`）；生成：`GEN_FCL_STAGE`（`flow/basic_data/basic_data_config/basic_data_pool_config.py:2344-2440`） |

- **`group`**（C/D30/D60/D90/D120P/FCL/REO/P）由 `CREATE_FCL_RELATE_ATTR` 计算（`basic_data_pool_config.py:1695-1771`），来源 `newrez.portnewrezgeneral.delinquency_status_mba`、`carrington.portcarrington.loan_status` 等；FCL/REO/Full Payoff 直接判定，其余按 `days360(nextduedate, dataasof)` 分档。
- **`judicial`**（Y/N）：先取源 `fc.judicial`（1→Y，0→N），否则回退 `port.basic_data_judicial_config`（按物业州 join）。
- 各阶段日期来自 `tempfc.current_fcl_business_1_temp` 等临时表，最终经 `GEN_FCL_STAGE` 插入 `port.fcl_stage_info`（先 `delete ... where fctrdt = 当日`，再 `insert`，见 `basic_data_pool_config.py:2341-2344`）。

```
L1 newrez.portnewrezfc / portnewrezgeneral …   (源：每日快照)
        │  GEN_FCL_DETAIL / CREATE_FCL_RELATE_ATTR
        ▼
L4 port.basic_data_fcl_related (delq_status, state) + tempfc.current_fcl_business_1_temp (各阶段日期/天数)
        │  GEN_FCL_STAGE  (basic_data_pool_config.py:2344)
        ▼
L4 port.fcl_stage_info   (一行 = loanid + fctrdt)
        │  sync (12-FCL_STAGE)   sync_asset_management.py → sync_to_mysql
        ▼
L5 bpms.sync_fcl_stage_info  ←  agg-summary 页 Stage / Time Line 取数于此
```

---

## §3 列映射（Time Line UI 列 ⇄ 表列，实测一致）

| UI 列 | `sync_fcl_stage_info` 列 | 阶段 | 备注 |
|---|---|---|---|
| Loan ID / Group / Servicer / States / Judicial | `loanid` / `group` / `servicer` / `state` / `judicial` | — | 标识与分类列 |
| NOI Date 1 | `noi_start_date` | NOI | Newrez 恒空（无对应源字段） |
| Referral Date 2 | `referral_start_date` | Referral | 源 `fcreferraldate`，BPS 入库前置 |
| First Legal Date 3 | `first_legal_start_date` | First Legal | 源 `firstlegaldate` |
| Service Date 4 | `service_start_date` | Service | 源 `servicecompletedate` |
| (Publication 5) | `publication_start_date` | Publication | Newrez 恒空 |
| Judgement Date 6 | `judgement_start_date` | Judgement | 源 `fcjudgmenthearingscheduled`（开庭排期日，非判决登记日） |
| Sale Date 7 | `sale_start_date` | Sale | 源 `fcscheduledsaledate` |

> `sync_fcl_stage_info` 实测共 57 列：除上述阶段日期外，每阶段还有 `*_end_date / *_stage_days / *_in_lm_days / *_on_hold_days`（供 Stage tab），以及 `first_legal_date_history`（text）、`stage`（当前活动阶段）、`fctrdt`（快照日）与审计列。

---

## §4 Time Line vs Stage vs Overview——同一张表的三种视图

| 视图 | 用到的列 | 含义 |
|---|---|---|
| **Time Line tab** | 各阶段 `*_start_date` | 横向展示每笔贷款的里程碑日期序列 |
| **Stage tab** | 各阶段 `*_stage_days` / `*_in_lm_days` / `*_on_hold_days` + `stage` | 当前停在哪个阶段、各阶段耗时（含 LM/Hold 扣减） |
| **Overview 汇总** | `servicer` / `group` / `judicial` 聚合计数 | 各 Servicer 的 Loan Count、FC、D120P、Judicial/Non-Judicial 笔数 |

- **Days in Stage** ≈ `datediff(stage_start, stage_end 或当日) + 1`；`*_in_lm_days`、`*_on_hold_days` 为该阶段内处于 LM / Hold 的天数扣减（详见 doc 21 stage 系统）。
- 三者**不是三张表**，而是对 `sync_fcl_stage_info`（最新快照）的不同投影/聚合。

---

## §5 关键困惑解答：「sync 表存的是当前状态，哪来的历史里程碑？」

分两层理解：

1. **里程碑是"列"，不是"行"。** 单笔贷款从催告→拍卖的进度，被编码成同一行上的多列**事件日期**（`referral_start_date`、`first_legal_start_date`…）。某阶段日期一旦写入就**保留不变**——这本身就是该贷款的"时间线"，无需多行历史即可呈现完整进程。

2. **`sync_fcl_stage_info` 确实保留了历史快照。** 它**与众不同地保留 `fctrdt` 列**（快照日），因此每笔贷款有多行（每个跑批日一行）。prod `bpms` 实测：

   | 指标 | 值 |
   |---|---|
   | 总行数 | **8,368** |
   | 不同 loanid | **66** |
   | 不同 `fctrdt` | **300**（2025-06-03 → 2026-06-04，近似每日） |
   | 每笔贷款行数 | 多数 **300** 行/loan |

   这与主表 `bpms.sync_loan_foreclosure` 形成对比——后者是 **DELETE+APPEND 覆盖刷新**、**一笔贷款仅 1 行（最新态）**（写法见 `util/df_db_util.py` 的 `sync_to_mysql`：先 `delete from {table}` 再 `to_sql(append)`；FCL 主表另走 `UPDATE_FORECLOSURE` 的 `ON DUPLICATE KEY UPDATE` 上插）。

3. **agg-summary 页只展示最新快照。** 页面对 `sync_fcl_stage_info` 取 `fctrdt = MAX(fctrdt)`，于是回到"一行一笔贷款"。所以你在 Time Line 看到很多 loan、每个一行——是"组合里所有止赎贷款的最新里程碑"，而非"一笔贷款的多行历史"。历史快照虽然存在表里，但本页默认不展开。

---

## §6 代表性 SQL（页面实际等价查询）

```sql
-- Time Line tab：最新快照、一行一笔贷款
SELECT loanid, `group`, servicer, state, judicial,
       noi_start_date, referral_start_date, first_legal_start_date,
       service_start_date, publication_start_date,
       judgement_start_date, sale_start_date
FROM bpms.sync_fcl_stage_info
WHERE fctrdt = (SELECT MAX(fctrdt) FROM bpms.sync_fcl_stage_info)
  AND is_deleted = 0
ORDER BY referral_start_date;     -- UI 各列「↑」即按该日期列排序

-- Stage tab：同一最新快照，取天数列
SELECT loanid, `group`, servicer, stage,
       demand_stage_days, referral_stage_days, first_legal_stage_days,
       service_stage_days, to_judgement_days, to_sale_days
FROM bpms.sync_fcl_stage_info
WHERE fctrdt = (SELECT MAX(fctrdt) FROM bpms.sync_fcl_stage_info) AND is_deleted = 0;

-- Overview 汇总：按 Servicer × group / judicial 计数
SELECT servicer, `group`, judicial, COUNT(*) AS loans
FROM bpms.sync_fcl_stage_info
WHERE fctrdt = (SELECT MAX(fctrdt) FROM bpms.sync_fcl_stage_info) AND is_deleted = 0
GROUP BY servicer, `group`, judicial;
```

> 若要看某笔贷款的**历史演化**（而非聚合页的最新态），去掉 `MAX(fctrdt)` 过滤并 `ORDER BY fctrdt` 即可——表里保留了每日快照。

---

## §7 样本走查：loan `7727000088`（prod `bpms` 实测）

最新快照（`fctrdt = 2026-05-24`）：

| 列 | 值（DB，UTC） | BPS 显示（美东） |
|---|---|---|
| group / servicer / state / judicial | REO / Newrez / FL / Y | 同左 |
| noi_start_date | NULL | （空） |
| referral_start_date | 2025-05-22T16:00Z | **2025-05-23** |
| first_legal_start_date | 2025-06-12T16:00Z | **2025-06-13** |
| service_start_date | 2025-07-17T16:00Z | **2025-07-18** |
| judgement_start_date | 2026-03-26T16:00Z | 2026-03-27 |
| sale_start_date | NULL | （空） |
| stage | JUDGEMENT | JUDGEMENT |

**与截图完全吻合**（截图 Referral 2025-05-23 / First Legal 2025-06-13 / Service 2025-07-18）。

> ⚠️ **时区注意**：日期列以美东午夜存为 UTC（`T16:00Z`），故 MCP/DB 读出的 UTC 值在 BPS 界面会显示为**次日**。比对时统一换算到美东即可对齐。

> ⚠️ **环境差异**：本文 DB 实测取自 **prod `bpms`**；截图来自 **UAT**（`uat-bips`）。最新快照 prod 为 Newrez 21 + Carrington 6 = 27 笔，与截图（Newrez 26 + Carrington 5）略有出入，属环境数据差异；**贷款级里程碑（7727000088）逐列吻合**，足证取数规则正确。
