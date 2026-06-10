# 23 — BK Discharge → Payoff（P）历时分析（DB 实测）

---

## 文档目的

- **为什么存在**：回答一个常见业务问题——「一笔贷款从破产 discharge 到最终 payoff（状态机里的 P — Loan ends）一般要多久？」并把基于生产库的实测结论、口径与验证 SQL 固化下来，供后续复用与复核。
- **解决的问题**：状态机图（`fcl_pipeline.html` / doc 17 §4 / doc 07 §2.4）画出了 `BK → discharge → … → P` 这条边，但**没有给出时长**，且容易让人误以为「discharge 会较快导向 payoff」。本文用 prod 数据校正这一直觉。
- **范围**：仅覆盖「BK 了结日期 → payoff 日期」这一对事件的时长测算、口径与局限；不覆盖 BK 业务本身的法律解释（见 doc 17 §5.4 / doc 07 §2.5）、也不覆盖完整 FCL 时间线（见 doc 25–30）。
- **系统关系**：本文是 doc 17 / doc 07「BK 状态转换」内容的**数据实证补充**，所有结论来自 `redshift_prod`（prod Redshift）只读查询。

## 目标读者

主要读者：业务分析师 · 数据产品经理 · 验证/对账工程师  
次要读者：数据工程师 · 风险/资产管理 · 未来 AI Session

## 修订历史

| 日期 | 作者 | 版本 | 变更说明 | 关联文档 |
|------|------|------|---------|---------|
| 2026-06-08 | AI Agent (Claude Opus 4.8) | v1 | 初版：BK discharge → payoff 历时 DB 实测（prod Redshift）、口径、逐笔明细、解读与局限、验证 SQL | doc 17 · doc 07 · doc 21 |

## 依赖文档

| 文档 | 用途 |
|------|------|
| `17_foreclosure_business_primer.md` §5.4 | BK 业务含义与各转换法律依据（§ 362/§ 727/§ 1322/§ 1328/§ 524） |
| `07_fcl_lineage_and_rules.md` §2.5 | 同上（en/zh 版本） |
| `21_fcl_field_lineage.md` | FCL/BK 字段血缘 |

## 已知限制

> ⚠️ **本文结论的样本极小、且「历时」为重建值而非记录值**，详见 §6、§7。**不可据此做统计推断或对外口径**，仅作数据现状说明。

---

## 1. 问题

> 一笔贷款从 **BK discharge** 到 **P（Loan ends / paid off）** 一般历时多久？

## 2. 结论（TL;DR）

**生产数据无法给出一个有意义的「BK discharge → P 历时」——这两个事件在数据中本质上是相隔约 15 年、彼此不相关的两件事。**

- 能同时取到「BK 了结日期」与「payoff 日期」的贷款（宽口径）共 **11 笔**：间隔 **135–199 个月（约 11–16.6 年）**，中位数 **186 个月（≈15.5 年）**，平均 172.7 个月。
- 仅取 `bankruptcy_status='Discharged'` 的严格口径：**4 笔**，间隔 186–193 个月（≈15.5–16 年）。
- 这些数字**不是流程耗时**，而是「**很久以前的历史破产 discharge**（2008–2014）」与「**近期、独立原因的 payoff**（2023–2026）」之间的时间跨度。

这恰好**用数据印证了法律事实**：**Ch.7 / Ch.11 discharge ≠ 还清**——它只免除个人债务责任，抵押权（lien）存续，贷款照常存续十余年，之后才因再融资/出售/到期等独立原因 payoff（见 doc 17 §5.4 / doc 07 §2.5 的 § 727 / § 524(a)(2) 依据）。换言之，`BK discharge → P` 在法律上成立，但**在数据中不存在一个特征性时长**。

## 3. 数据来源与字段（已 schema 校验）

| 事件 | 表 | 字段 | 说明 |
|------|----|----|------|
| BK 了结日期（discharge 代理） | `port.basic_data_loan_foreclosure_bankruptcy` | `bankruptcy_status`, `status_date` | **无专门 discharge 日期字段**；以 `status_date`（当前 BK 法律状态对应日期）作代理。BK 表仅 74 行 / 69 笔、8 个 dataasof（2024-07~2026-06）、仅 FCL 业务族 servicer（Newrez/Carrington/CapeCodFive） |
| Payoff 日期（P） | `port.basic_data_loan_funding` | `paidoffdate` | 全组合 1,081 笔有 payoff 日期 |
| 关联键 | 两表 | `loanid` | — |

`bankruptcy_status` 取值分布（实测）：`Completed/Cancelled` 32、`Discharged` 17、`Active` 17、`Dismissed` 4、`ReliefGranted` 3、`Closed` 1。

## 4. 方法

1. 从 BK 表取「BK 已了结」的贷款及其 `status_date`：
   - **严格口径** = `bankruptcy_status='Discharged'`；
   - **宽口径** = `Discharged` + `Completed/Cancelled` + `Closed` + `Dismissed` + `ReliefGranted`。
2. 按 `loanid` 关联 `basic_data_loan_funding.paidoffdate`，仅保留 `paidoffdate IS NOT NULL` 且 `paidoffdate >= 了结日期`。
3. 历时 = `DATEDIFF(day, 了结日期, paidoffdate)`，换算月数 = `/30.44`。

## 5. 结果（prod 实测，2026-06-08）

### 5.1 汇总

| 口径 | 贷款数 | 最短(月) | 中位数(月) | 平均(月) | 最长(月) |
|------|-------|---------|-----------|---------|---------|
| 严格（`Discharged`） | 4 | 186.0 | ~191.4 | ~190.4 | 192.9 |
| 宽（任何 BK 了结状态） | 11 | 135.2 | 186.0 | 172.7 | 199.2 |

### 5.2 逐笔明细（11 笔）

| loanid | servicer | 章 | BK 状态 | BK 了结日期 | payoff 日期 | 历时(月) |
|--------|----------|----|--------|-----------|------------|---------|
| 7727004377 | Newrez | 7 | Discharged | 2009-06-01 | 2024-11-30 | 186.0 |
| 7727004650 | Newrez | 11 | Discharged | 2010-06-03 | 2026-03-31 | 189.9 |
| 7727004651 | Newrez | 11 | Discharged | 2010-06-03 | 2026-06-30 | 192.9 |
| 7727004649 | Newrez | 11 | Discharged | 2010-06-03 | 2026-06-30 | 192.9 |
| 7727004393 | Newrez | 7 | Closed | 2014-12-24 | 2026-03-31 | 135.2 |
| 7727000979 | Carrington | 13 | Completed/Cancelled | 2012-11-06 | 2024-03-31 | 136.8 |
| 7727000910 | Carrington | 7 | Completed/Cancelled | 2012-02-27 | 2024-08-31 | 150.1 |
| 7727000983 | Carrington | 13 | Completed/Cancelled | 2011-02-17 | 2024-10-31 | 164.4 |
| 7727000883 | Carrington | 7 | Completed/Cancelled | 2011-10-31 | 2025-08-31 | 166.0 |
| 7727000904 | Carrington | 7 | Completed/Cancelled | 2008-06-09 | 2023-12-31 | 186.7 |
| 7727000880 | Carrington | 13 | Completed/Cancelled | 2008-12-23 | 2025-07-31 | 199.2 |

## 6. 解读：为什么这不是真正的「历时」

- `status_date` 记录的是 servicer 报来的**历史法律状态日期**——上表显示这些破产 **2008–2014 年**就已 discharge/了结。
- `paidoffdate` 都在 **2023–2026 年**。
- 中间约 **15 年**，期间贷款一直在组合内正常存续。
- **discharge 并未「导致」payoff**：两者相隔十余年、互不相关。Ch.7/Ch.11 discharge 只免个人责任、lien 存续，贷款继续存在，多年后才因独立原因还清。
- **故 `BK discharge → P` 没有特征性时长**；状态机图上的该边表示「法律上可能的路径」，而非「一个可测的耗时」。

## 7. 数据局限

1. **无专门 discharge 日期字段**，以 `status_date` 代理。
2. **BK 表为当前态快照、覆盖极小**：74 行 / 69 笔，仅 FCL 业务族 servicer；非事件流水。
3. **样本量太小**：discharged 仅 17 笔，其中只有 4 笔有 payoff（宽口径 11 笔）——无统计意义。
4. **系统透传 servicer 状态、不记录状态转换**（见 doc 07 §2.5 / `03_fcl_status_logic.md` §2.1）；本结果由两表 join 重建，非记录的转换事件。
5. 全程 `redshift_prod` **只读**，未做任何写操作。

## 8. 验证 SQL（redshift_prod）

### 8.1 逐笔明细

```sql
WITH bk AS (
  SELECT loanid, servicer, chapter, bankruptcy_status,
         MIN(status_date) AS bk_end_date          -- discharge 日期代理（无专门 discharge 字段）
  FROM port.basic_data_loan_foreclosure_bankruptcy
  WHERE bankruptcy_status IN ('Discharged','Completed/Cancelled','Closed','Dismissed','ReliefGranted')
    AND status_date IS NOT NULL
  GROUP BY loanid, servicer, chapter, bankruptcy_status
)
SELECT bk.loanid, bk.servicer, bk.chapter, bk.bankruptcy_status,
       bk.bk_end_date, f.paidoffdate,
       DATEDIFF(day, bk.bk_end_date, f.paidoffdate)                 AS days_to_payoff,
       ROUND(DATEDIFF(day, bk.bk_end_date, f.paidoffdate)/30.44, 1) AS months_to_payoff
FROM bk
JOIN port.basic_data_loan_funding f ON f.loanid = bk.loanid       -- payoff 日期来源
WHERE f.paidoffdate IS NOT NULL
ORDER BY (bk.bankruptcy_status='Discharged') DESC, days_to_payoff;
```

### 8.2 汇总统计

```sql
WITH bk AS (
  SELECT loanid, bankruptcy_status, MIN(status_date) AS bk_end_date
  FROM port.basic_data_loan_foreclosure_bankruptcy
  WHERE bankruptcy_status IN ('Discharged','Completed/Cancelled','Closed','Dismissed','ReliefGranted')
    AND status_date IS NOT NULL
  GROUP BY loanid, bankruptcy_status
),
d AS (
  SELECT bk.loanid, DATEDIFF(day, bk.bk_end_date, f.paidoffdate)/30.44 AS months_to_payoff
  FROM bk JOIN port.basic_data_loan_funding f ON f.loanid = bk.loanid
  WHERE f.paidoffdate IS NOT NULL AND f.paidoffdate >= bk.bk_end_date
)
SELECT COUNT(*) loans,
       ROUND(MIN(months_to_payoff),1) min_m,
       ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY months_to_payoff),1) median_m,
       ROUND(AVG(months_to_payoff),1) avg_m,
       ROUND(MAX(months_to_payoff),1) max_m
FROM d;   -- → 11 笔, min 135.2, median 186.0, avg 172.7, max 199.2（月）
```

> 注：`MEDIAN(x)` 在本只读角色下会报 `transaction is read-only`，改用 `PERCENTILE_CONT(0.5) WITHIN GROUP (...)` 即可。

## 9. 相关文档

- BK 法律依据（§ 362/§ 727/§ 1322/§ 1328/§ 524）：doc 17 §5.4、doc 07 §2.5
- 状态机与转换：doc 17 §4、doc 07 §2.4、`outputs/fcl_pipeline.html`
- FCL/BK 字段血缘：doc 21
