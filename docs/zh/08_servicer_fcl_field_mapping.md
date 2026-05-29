# 08 — Servicer 原始字段 → Foreclosure 状态映射规则

---

## 文档信息

| 项目 | 内容 |
|------|------|
| **文档目的** | 以业务规则视角，描述各 Servicer 原始数据文件中与 Foreclosure 状态判断相关的字段、映射逻辑、业务含义。去掉 ETL 中间层，直接从"Servicer 给了我什么字段"到"我们如何得出 FCL 状态"。 |
| **解决的问题** | 现有系统 FCL 判断逻辑分散在多个 ETL 配置文件中，缺乏统一的业务规则规范。本文档是重构前的现状基线（Layer 1），并标注缺口（Layer 2），为后续向 Servicer 补全字段提供依据。 |
| **覆盖范围** | 8 个 Servicer 的 FCL 状态映射现状 + 缺口分析 |
| **系统归属** | PrefectFlow ETL pipeline — MySQL Layer 1 原始数据层 |

**目标读者：** 数据产品经理 · 业务分析师 · 合规审核 · 未来接入新 Servicer 的工程师

**依赖文档：** `07_fcl_lineage_and_rules.md`（ETL 实现细节）、`01_source_data.md`（原始表结构）

**修订历史：**

| 日期 | 作者 | 版本 | 变更内容 |
|------|------|------|---------|
| 2026-05-25 | AI Agent (Claude Sonnet 4.6) | v6 | 合并两个重叠的最小字段集 section 为双视角对照表（系统需求 × Servicer 请求）；补充 `bankruptcy_flag` 独立于 MBA 枚举的原因说明 |
| 2026-05-25 | AI Agent (Claude Sonnet 4.6) | v5 | 背景章节补充 MBA 完整原始取值范围表、FCL-Hold 说明、推荐最小字段集 |
| 2026-05-25 | AI Agent (Claude Sonnet 4.6) | v4 | 各 Servicer 缺口分析表中新增 LM 字段需求行；缺口汇总表新增 P1/P2 LM 行 |
| 2026-05-25 | AI Agent (Claude Sonnet 4.6) | v3 | 新增 LM 与 MBA 标准关系说明；新增 LM 字段需求规范章节（6种类型 + 字段最小集 + 各Servicer覆盖） |
| 2026-05-25 | AI Agent (Claude Sonnet 4.6) | v2 | 全字段取值经 Redshift DB 实测验证；修正 CapeCodFive/FCI 评级；修正 SLS/Newrez 值示例 |
| 2026-05-25 | AI Agent (Claude Sonnet 4.6) | v1 | 初始版本，基于 PrefectFlow 源码逆向研究 |

---

## 背景：美国抵押贷款 FCL 状态的业务含义

### FCL 状态体系（MBA 标准）

| 状态码 | 业务含义 | 触发条件（业务层面） |
|--------|---------|------------------|
| `C` | Current（正常还款） | DPD < 30 天 |
| `D30` | 30–59 天逾期 | DPD 30–59 天 |
| `D60` | 60–89 天逾期 | DPD 60–89 天 |
| `D90` | 90–119 天逾期 | DPD 90–119 天 |
| `D120P` | 120+ 天逾期 | DPD ≥ 120 天 |
| `FCL` | **Foreclosure（止赎程序中）** | Servicer 已将贷款移交法律程序（司法/非司法止赎） |
| `REO` | Real Estate Owned（银行持有房产） | 止赎完成，房产归银行所有 |
| `P` | Paid in Full（全额还清） | 贷款偿清（正常还清、短售、REO 处置） |

### MBA 标准逾期状态原始取值范围（Servicer 传输层）

> **两个层次的区别**：上表是**系统内部码**（C/D30/D60/D90/D120P/FCL/REO/P），是 ETL Step 3 的输出。下表是 **Servicer 传输给我们的原始文本值**，需要经过映射才能变成系统内部码。

下表以 Newrez 为代表，展示真实出现的 MBA 标准原始值（DB 实测 2026-05-25）：

| Servicer 原始传输值 | 含义 | 是否在 Newrez 数据中出现 | 映射到系统内部码 |
|--------------------|------|----------------------|--------------|
| `Current` | 0–29 DPD，正常还款 | ✅ | → `C` |
| `1-29 DPD` | 1–29 天逾期（Newrez 细分） | ✅ | → `C` |
| `30-59 DPD` | 30–59 天逾期 | ✅ | → `D30` |
| `60-89 DPD` | 60–89 天逾期 | ✅ | → `D60` |
| `90-119 DPD` | 90–119 天逾期 | ✅ | → `D90` |
| `120-149 DPD` | 120–149 天逾期 | ✅ | → `D120P` |
| `150-179 DPD` | 150–179 天逾期 | ✅ | → `D120P` |
| `180+ DPD` | 180 天以上逾期 | ✅ | → `D120P` |
| `Foreclosure` | 止赎程序中 | ✅ | → `FCL` |
| `Foreclosure / Non-Perf BK` | 止赎 + 非履约破产（Newrez 扩展值） | ✅ | → `FCL`（同时 `bankruptcy='Y'`） |
| `Foreclosure / Perf BK` | 止赎 + 履约破产（Newrez 扩展值） | ✅ | → `FCL`（同时 `bankruptcy='Y'`） |
| `Performing Bankruptcy` | 履约破产（仍在还款） | ✅ | → `D90`/`D120P` + `bankruptcy='Y'` |
| `Non-Performing Bankruptcy` | 非履约破产 | ✅ | → `D120P` + `bankruptcy='Y'` |
| `REO` | 银行持有房产 | ✅ | → `REO` |
| `REO Sale` | REO 已出售（处置完成） | ✅ | → `P` |
| `Full Payoff` / `Paid in Full` | 全额还清 | ✅ | → `P` |
| `3rd Party Sale` | 第三方拍卖出售 | ✅ | → `P` |
| `Service Release` | 贷款服务权转让（贷款离开此 Servicer） | ✅ | → 特殊处理 |

> **注意**：`Foreclosure / Non-Perf BK`、`Foreclosure / Perf BK` 是 Newrez 自定义的复合值，将 FCL 和 BK 状态压缩在单一字段中传递。doc 09 的接口标准要求这两个状态通过**独立字段**（`foreclosure_flag` + `bankruptcy_flag`）分开传递，避免系统解析脆弱性。

### FCL-Hold：不是 MBA 标准状态

MBA 标准中**没有** `FCL-Hold` 这个分类。

**FCL-Hold**（止赎暂停）是 Servicer 内部的操作状态，指止赎程序已启动但暂时中止，常见原因：
- 借款人申请 Loss Mitigation（贷款修改/宽限）
- 破产自动中止令（Automatic Stay）
- COVID 特殊宽限期
- 法院指令暂停

在 MBA 框架下，即使有 Hold，贷款仍然**报告为 `Foreclosure`**，因为 MBA 反映的是法律状态（已进入止赎程序），而非操作进度。因此，如果只依赖 MBA 状态字段，无法知道止赎是否处于暂停——需要额外的 `fcl_hold_flag` / `hold_reason` 字段。

### Foreclosure 的法律定义

**Foreclosure** 是指当借款人违约（通常为连续逾期 90–120 天后）时，贷款方依据抵押合同，通过法律程序强制出售抵押房产以回收贷款余额的过程。

- **司法止赎（Judicial Foreclosure）**：需经法院批准，典型州：纽约、新泽西、佛罗里达（流程 6 个月–2 年）
- **非司法止赎（Non-Judicial / Power of Sale）**：无需法院，按合同约定直接拍卖，典型州：加利福尼亚、德克萨斯（流程 3–6 个月）

**系统层面**：当 Servicer 在数据文件中将贷款标记为 FCL 状态时，通常意味着该贷款已进入以下流程中的某个阶段：DEMAND → REFERRAL（移交律师）→ FIRST LEGAL（首次法律行动）→ SERVICE（文件送达）→ JUDGEMENT（判决）→ SALE（拍卖）

### LM（损失缓解）状态与 MBA 逾期状态的关系

**LM 不属于 MBA 标准逾期状态。** `delinquency_status_mba` 只反映"贷款逾期多久"，不反映"是否有补救方案"。LM 信息需要单独字段传递。

两者的关系是**完全正交**的——可以理解为两个独立坐标轴：

```
MBA delinquency_status_mba（逾期状态） = 横轴：欠款多严重？
LM status（损失缓解状态）             = 纵轴：正在做什么补救？

同一笔贷款可以同时是：
  delinq = 'D90' AND lm_flag = 'Y'  （90天逾期 + 正在做贷款修改）
  delinq = 'FCL' AND lm_flag = 'Y'  （已进入止赎 + 同时在谈宽限）
  delinq = 'C'   AND lm_flag = 'N'  （正常还款，无LM）
```

**LM 不产生独立 delinq 状态码。** 在系统中，`lm_flag = 'Y'` 只是附加标志，`delinq` 仍然按照逾期天数（days360）或 Servicer 提供的状态文本计算。LM 成功 → 借款人恢复还款 → `delinq` 自然变回 `C`；LM 失败 → 贷款继续滞留 → `delinq` 继续累积直至 FCL。

---

## 各 Servicer 映射现状

### ETL 层次说明（读懂本文档所需背景）

本文档多处使用"Step 3"和"Layer 1/L2"术语，含义如下：

```
Layer 1 / MySQL L1
  各 Servicer 原始表（如 sls.portassetdaily、carrington.portcarrington）
  → 字段名与 Servicer 原始文件一致，未经重命名
        ↓ ETL Step 1：字段重命名 + JOIN
Layer 2 / L2
  Redshift port.basic_data_daily_loan_common
  → 所有 Servicer 合并为统一字段名（svcdelinq、fcl_flag 等），但字段值未转换
        ↓ ETL Step 3：FCL/REO/P/D30... 判断逻辑
Layer 3（Clean）
  Redshift port.basic_data_daily_loan_common_clean
  → 生成最终标准 delinq 状态码（'FCL'、'REO'、'D30' 等）
        ↓
Layer 4（月度分析）
  port.portmonthbase / port.portmonth
```

> **"未接入 Step 3"** = 该 Servicer 的数据已进入 L2 ✅，但 `daily_data_loan_common_clean_config.py` 中**不存在**对应的 SQL 处理块 ❌，导致 `delinq` 字段永远为空，FCL 状态在所有下游报表中均不存在。

---

### 整体评级一览

> **字段说明**：下表所有字段均为 **MySQL Layer 1 原始字段**（Servicer 文件直接入库，字段名未经重命名），格式为 `schema.table.field`。

| Servicer | 数据频率 | 有逾期状态文本字段 | 有独立 FCL 标志字段 | 有破产字段 | 有 LM 字段 | FCL 判断完整度 |
|---------|---------|--------------|----------------|---------|----------|-------------|
| SLS | 日报 | ✅ `sls.portassetdaily.delq_status_mba` | ❌ 无 | ✅ 文本推导 | ❌ 无 | 🟡 中等（仅文本匹配） |
| Newrez | 日报 | ✅ `newrez.portnewrezgeneral.delinquency_status_mba` | ❌ 采集但为 null | ✅ 文本推导 | ✅ `newrez.portnewrezlm.activelmflag` | 🟡 中等（仅文本匹配） |
| Carrington | 日报 | ✅ `carrington.portcarrington.loan_status` | ✅ `carrington.portcarrington.fcl_flag` | ✅ 文本推导 | ✅ `carrington.portcarrington.lm_flag` | ✅ 最完整（双字段校验） |
| Selene | 日报 | ✅ `selene.portselenemain.loan_status` | ✅ `selene.portselenemain.foreclosure_status_code`（采集未使用） | — | ✅ `selene.portselenemain.lm_setup_date` | ❌ 未接入 Step 3 |
| MRC | 日报 | ✅ `mrc.portmrcloan.min_status` | ✅ `mrc.portmrcforeclosure.fc_flag`（采集未使用） | — | — | ❌ 未接入 Step 3 |
| Arvest | 月报 | ❌ 无逾期状态字段 | ❌ 无 | ✅ bid 表推导 | ❌ 无 | ❌ 仅 days360（FCL 永远无法产生） |
| CapeCodFive | 月报 | ⚠️ `capecodfive.portcapecodfive_monthly_servicing.mba_delinquency_status`（值为数字 DPD，非文本状态） | ❌ 无 | — | — | ❌ FCL 永远无法产生（值格式不匹配） |
| FCI | 日报（API） | ✅ `fci.portfciloanportfolio.status`（采集未使用，有 2,408 行 FCL 数据） | — | — | — | ❌ 完全未实现 |

---

### 3.1 SLS — 🟡 中等（仅文本匹配）

**数据概览**

| 属性 | 值 |
|------|-----|
| 数据频率 | 日报 |
| 文件格式 | `.txt`（固定格式，多文件类型） |
| 关键原始表 | `sls.portassetdaily`（主日报 + 逾期状态）、`sls.portfcldaily`（FCL 专项） |
| 数据周期覆盖 | 2024-07-05 前（之后切换至 Newrez） |

**FCL 相关原始字段**（均为 MySQL Layer 1 原始字段）

| 完整字段路径（schema.table.field） | 业务含义 | 取值范围/示例 | FCL 用途 |
|----------------------------------|---------|------------|---------|
| `sls.portassetdaily.delq_status_mba` | MBA 标准逾期状态 | `'Current'`(158K)、`'DQ 30'`(47K)、`'Service Release'`(19K)、`'Paid in Full'`(5K)、`'DQ 60'`(5K)、`'DQ 90'`(4K)、`'Bankruptcy'`(1K)、`'Foreclosure'`(546) | **主要判断字段**（DB实测 2026-05-25） |
| `sls.portassetdaily.nextduedate` | 下一个应付款日期 | `DATE`，如 `2024-03-01` | days360 兜底计算 |
| `sls.portfcldaily.fcl_status` | FCL 专项状态（独立文件） | 待补充 | **目前未使用于 delinq 判断** |
| `sls.portfcldaily.fcl_referral_date` | 移交法律程序日期 | `DATE` | 时间线，未用于状态判断 |

**FCL 状态判断规则（业务逻辑，优先级由高到低）**

1. **Paid-Off（P）**：`delq_status_mba = 'Paid in Full'`
2. **REO**：`delq_status_mba = 'REO'`
3. **FCL**：`delq_status_mba = 'Foreclosure'`
4. **兜底（days360）**：以上均不符合时，计算 `days360(nextduedate)` → C / D30 / D60 / D90 / D120P
5. **破产（辅助标志）**：`delq_status_mba = 'Bankruptcy'` → `bankruptcy = 'Y'`

> **业务含义**：SLS 使用 MBA 标准逾期状态码，`'Foreclosure'` 表示 SLS 已将该贷款正式进入止赎程序。此字段由 SLS 在其内部系统中主动更新。

**缺口分析**

| 缺口 | 风险等级 | 说明 |
|------|---------|------|
| 无独立 FCL 激活标志字段 | 🟡 中等 | 完全依赖 `delq_status_mba` 文本。若 SLS 延迟更新状态，系统无法独立检测到 FCL |
| `portfcldaily` 数据采集未用于 FCL 判断 | 🟡 中等 | SLS 提供了专门的 FCL 文件（`portfcldaily`），但系统未利用其中数据来辅助/校验 `delinq` |
| **LM：无任何 LM 字段** | 🟡 中等 | SLS 数据中无 `lm_flag`、`lm_type` 等字段，无法判断贷款是否处于 LM 计划中，也无法区分 FCL+LM 混合状态。**需向 SLS 请求：`lm_flag` + `lm_type`** |

---

### 3.2 Newrez — 🟡 中等（仅文本匹配，fcl_flag 为空）

**数据概览**

| 属性 | 值 |
|------|-----|
| 数据频率 | 日报 |
| 文件格式 | `.txt` / `.csv`（多类型文件，分主报+专项） |
| 关键原始表 | `newrez.portnewrezgeneral`（主日报）、`newrez.portnewrezfc`（FCL 专项）、`newrez.portnewrezlm`（LM 专项） |
| 数据周期覆盖 | 2024-07-05 起（由 SLS 切换而来） |

**FCL 相关原始字段**（均为 MySQL Layer 1 原始字段）

| 完整字段路径（schema.table.field） | 业务含义 | 取值范围/示例 | FCL 用途 |
|----------------------------------|---------|------------|---------|
| `newrez.portnewrezgeneral.delinquency_status_mba` | MBA 标准逾期状态 | `'Current'`(1.07M)、`'1-29 DPD'`(251K)、`'Full Payoff'`(147K)、`'30-59 DPD'`(21K)、`'Foreclosure'`(12K)、`'60-89 DPD'`(8K)、`'Performing Bankruptcy'`(3K)、`'90-119 DPD'`(4K)、`'Non-Performing Bankruptcy'`(2K)、`'REO'`(700)、`'Foreclosure / Non-Perf BK'`(500)、`'Foreclosure / Perf BK'`(346)、`'REO Sale'`(228)、`'3rd Party Sale'`(132) | **主要判断字段**（DB实测 2026-05-25） |
| `newrez.portnewrezgeneral.nextduedate` | 下一应付款日期 | `DATE` | days360 兜底计算 |
| `newrez.portnewrezfc.fcl_flag` | FCL 激活标志（FCL 专项文件） | 采集中但系统赋值为 `null` | **采集但未使用** |
| `newrez.portnewrezlm.activelmflag` | LM 激活标志 | `'1'`（激活）/ `'0'`（未激活） | → `lm_flag = 'Y'` |
| `newrez.portnewrezlm.forbearancestatus` | 宽限状态 | `'Active'`、`'Completed'` 等 | LM 辅助信息 |

**FCL 状态判断规则（业务逻辑，优先级由高到低）**

1. **Paid-Off（P）**：`delinquency_status_mba = 'Full Payoff'`
2. **REO**：`delinquency_status_mba = 'REO'`
3. **FCL**：`delinquency_status_mba IN ('Foreclosure', 'Foreclosure / Non-Perf BK', 'Foreclosure / Perf BK')`
4. **兜底（days360）**：计算 `days360(nextduedate)` → C / D30 / D60 / D90 / D120P
5. **破产（辅助标志）**：`delinquency_status_mba LIKE '%Bankruptcy%'` → `bankruptcy = 'Y'`
6. **特殊（VASP）**：特定 VASP Deal 的贷款强制标为 `delinq = 'VASP'`（19 条）

> **业务含义**：`'Foreclosure / Non-Perf BK'` 表示止赎中同时有非履约破产；`'Foreclosure / Perf BK'` 表示止赎中同时有履约破产。Newrez 通过这个字段同时传递了 FCL 和 破产 两个状态。



```
SELECT
    p.dataasof,
    p.delinquency_status_mba,
    COUNT(*) AS cnt
FROM newrez.portnewrezgeneral p
WHERE p.dataasof = (
    SELECT MAX(dataasof)
    FROM newrez.portnewrezgeneral
)
GROUP BY
    p.dataasof,
    p.delinquency_status_mba
ORDER BY cnt DESC;

dataasof   delinquency_status_mba  cnt
2026-05-23	Current	4115
2026-05-23	Full Payoff	665
2026-05-23	1-29 DPD	157
2026-05-23	Foreclosure	33
2026-05-23	30-59 DPD	27
2026-05-23	60-89 DPD	14
2026-05-23	90-119 DPD	8
2026-05-23	REO	6
2026-05-23	Service Release	4
2026-05-23	Performing Bankruptcy	4
2026-05-23	Non-Performing Bankruptcy	3
2026-05-23	Foreclosure / Perf BK	3
2026-05-23	3rd Party Sale	2
2026-05-23	180+ DPD	2
2026-05-23	Foreclosure / Non-Perf BK	2
2026-05-23	REO Sale	1
2026-05-23	150-179 DPD	1

```



**缺口分析**

| 缺口 | 风险等级 | 说明 |
|------|---------|------|
| `fcl_flag` 采集但为 null | 🔴 高 | Newrez 提供了 `portnewrezfc` 表，其中应有独立 FCL 标志字段，但系统将其置为 null，未用于判断。这是最大的数据利用缺口 |
| 破产状态仅通过主状态字段推导 | 🟡 中等 | 没有独立破产字段（如 `bankruptcy_flag`），破产信息嵌入在逾期状态文本中，不够精细 |
| VASP 规则硬编码 | 🟡 中等 | 特定 deal 的 VASP 判断是代码中硬编码的，不在字段映射规则内 |
| **LM：有标志但缺少类型和日期** | 🟡 中等 | 已有 `activelmflag`（Y/N）和 `forbearancestatus`（数字码），但无 `lm_type`（无法区分 Forbearance vs Modification）、无 `lm_start_date` / `lm_end_date`。**需向 Newrez 请求：`lm_type` + `lm_start_date` + `lm_end_date`** |

---

### 3.3 Carrington — ✅ 最完整（双字段校验）

**数据概览**

| 属性 | 值 |
|------|-----|
| 数据频率 | 日报（主报）+ 双周（逾期专报） |
| 文件格式 | `.xlsx` 或 `.csv` |
| 关键原始表 | `carrington.portcarrington`（综合日报，同时含逾期状态和 FCL 标志） |

**FCL 相关原始字段**（均为 MySQL Layer 1 原始字段，同一张表 `carrington.portcarrington`）

| 完整字段路径（schema.table.field） | 业务含义 | 取值范围/示例 | FCL 用途 |
|----------------------------------|---------|------------|---------|
| `carrington.portcarrington.loan_status` | 贷款状态 | `'CUR'`(204K)、`'0-29'`(61K)、`'Completed Payoff'`(18K)、`'30-59'`(9K)、`'Loss Mitigation'`(5K)、`'60-89'`(2K)、`'Foreclosure'`(2K)、`'Bankruptcy - Performing'`(2K)、`'90-119'`、`'120+'`、`'REO'`、`'Foreclosure/Bankruptcy - Non-Performing'`等 | FCL 文本判断（DB实测 2026-05-25） |
| `carrington.portcarrington.fcl_flag` | FCL 激活标志（独立字段） | `'Active'`（3,373行，止赎激活）/ `''`（303,007行，未激活） | **FCL 独立标志** ★（DB实测 2026-05-25） |
| `carrington.portcarrington.nextduedate` | 下一应付款日期 | `DATE` | days360 兜底 |
| `carrington.portcarrington.lm_flag` | LM 激活标志 | `'Active'`（激活） | → `lm_flag = 'Y'` |
| `carrington.portcarrington.covid_forbearance_flag` | COVID 宽限标志 | `'Y'` / `'N'` | 特殊宽限期标注 |

**FCL 状态判断规则（业务逻辑，优先级由高到低）**

1. **FCL**：`loan_status = 'Foreclosure'` **或** `fcl_flag = 'Active'`（双字段 OR 校验）
2. **REO**：`loan_status IN ('R', 'REO')`
3. **Paid-Off（P）**：`loan_status IN ('Completed Payoff', 'Completed Short Sale', 'Completed REO Sale')`
4. **兜底（days360）**：计算 `days360(nextduedate)` → C / D30 / D60 / D90 / D120P
5. **破产（辅助标志）**：`loan_status = 'Bankruptcy - Performing'` → `bankruptcy = 'Y'`

> **设计优势**：`fcl_flag = 'Active'` 作为安全网——即使 `loan_status` 未明确标注 `'Foreclosure'`，只要 FCL 标志激活就触发 FCL 状态。这是其他所有 Servicer 都缺失的双重保障机制。

**缺口分析**

| 缺口 | 风险等级 | 说明 |
|------|---------|------|
| 无独立的破产激活字段 | 🟡 中等 | 破产仅通过 `loan_status` 文本推导，无独立破产标志 |
| Short Sale / REO Sale 均归入 P | 🟡 低 | 短售和正常还清都标为 P，无法区分清算方式 |
| **LM：有标志但缺少类型和日期** | 🟡 中等 | 已有 `lm_flag`（'Active'）和 `covid_forbearance_flag`，但 `loan_status = 'Loss Mitigation'`（5K 行）未独立映射，且无 `lm_type` / `lm_start_date`。**需向 Carrington 请求：`lm_type` + `lm_start_date` + `lm_end_date`** |

---

### 3.4 Selene — ❌ 字段采集但未接入 FCL 判断

**数据概览**

| 属性 | 值 |
|------|-----|
| 数据频率 | 日报 |
| 文件格式 | `.csv`（多种报告类型：P181、P102、DailyExtract 等） |
| 关键原始表 | `selene.portselenemain`（主日报）、`selene.portselenedetails` |

**FCL 相关原始字段**（均为 MySQL Layer 1 原始字段，同一张表 `selene.portselenemain`）

| 完整字段路径（schema.table.field） | 业务含义 | 取值范围/示例 | FCL 用途 |
|----------------------------------|---------|------------|---------|
| `selene.portselenemain.loan_status` | 贷款状态 | `'Current'`(115K)、`'Liquidated'`(1K)、`'No Contact'`(922)、`'In Contact'`(429)、`'Lost Contact'`(201)、`'Prequal'`(3) — ⚠️ **无 'Foreclosure' 值，Selene 使用非标准状态描述** | 进入 L2，但未用于 FCL 判断（DB实测 2026-05-25） |
| `selene.portselenemain.foreclosure_status_code` | FCL 状态码（独立字段） | `''`(118K，无 FCL)、`'A'`(41行 = **Active Foreclosure**)、`'R'`(100行 = **Released/Resolved**) — 这是 Selene 唯一可靠的 FCL 信号 | **采集至 L2 `fcl_flag`，但 Step 3 不存在 Selene 处理逻辑**（DB实测 2026-05-25） |
| `selene.portselenemain.lm_setup_date` | LM 设置日期 | `DATE`（有值 → LM 激活） | → `lm_flag = 'Y'` |
| `selene.portselenemain.nextduedate` | 下一应付款日期 | `DATE` | 理论上可用于 days360 |

**FCL 状态判断规则**

> ⚠️ **当前状态：完全缺失。** ETL 中不存在 `GEN_BASIC_DATA_DAILY_LOAN_COMMON_CLEAN_SELENE` 处理变量。
>
> Selene 的日报数据进入了 L2（`basic_data_daily_loan_common`）✅，但**从未被处理成标准化的 `delinq` 状态**（Step 3 ❌）。
>
> 实际结果：Selene 贷款在 `portmonthbase` 中的 `delinq` 来源于月报路径的部分 deal 覆盖，不是系统性实现。

**缺口分析**

| 缺口 | 风险等级 | 说明 |
|------|---------|------|
| Step 3 完全缺失 | 🔴 严重 | 所有 Selene 贷款的 FCL 状态无法通过日报路径产生 |
| `foreclosure_status_code` 未被使用 | 🔴 严重 | `'A'`(41行) 表示 Active FCL，已采集至 L2 `fcl_flag`，但 Step 3 完全未读取 |
| `loan_status` 无 'Foreclosure' 值 | 🔴 严重 | Selene 使用 `'No Contact'`/`'In Contact'`/`'Lost Contact'` 等非标准描述，无法用文本匹配检测 FCL |

| **LM：字段有但 Step 3 缺失** | 🟡 中等 | `lm_setup_date` 已采集（非空=LM激活），但 Step 3 不存在 Selene 处理逻辑，`lm_flag` 无法传递至下游。无 `lm_type` / 日期。**修 Step 3 后，需向 Selene 请求：`lm_type` + `lm_end_date`** |

**推荐实现方案**（无需向 Selene 请求新字段）：
- 在 Step 3 中加入 Selene 处理逻辑：`WHEN fcl_flag = 'A' THEN 'FCL'`（利用现有 `foreclosure_status_code = 'A'` 字段）

---

### 3.5 MRC — ❌ 字段采集但未接入 FCL 判断

**数据概览**

| 属性 | 值 |
|------|-----|
| 数据频率 | 日报 |
| 文件格式 | `.txt`（固定格式，18 种报告类型） |
| 关键原始表 | `mrc.portmrcloan`（主日报）、`mrc.portmrcforeclosure`（FCL 专项表） |

**FCL 相关原始字段**（MySQL Layer 1 原始字段，来自两张不同表）

| 完整字段路径（schema.table.field） | 业务含义 | 取值范围/示例 | FCL 用途 |
|----------------------------------|---------|------------|---------|
| `mrc.portmrcloan.min_status` | 贷款最低逾期状态 | ⚠️ **始终为空字符串 `''`（12,740行全部为空）** — 字段完全无效，无任何逾期状态数据 | 进入 L2 `delq_status`，但值为空，无法用于 FCL 判断（DB实测 2026-05-25） |
| `mrc.portmrcforeclosure.fc_flag` | FCL 激活标志（独立 FCL 专项表，共 18 行） | ⚠️ **仅有 `'N'`（18行），从未出现 `'Y'`** — 即使贷款处于止赎流程（`referral_hold_reason` 有 FCL 文本），该字段始终为 `'N'` | **采集至 L2 `fcl_flag`，但 Step 3 不存在 MRC 处理逻辑**（DB实测 2026-05-25） |
| `mrc.portmrcloan.dataasof` | 数据截止日期 | `DATE` | JOIN 键 |

**FCL 状态判断规则**

> ⚠️ **当前状态：完全缺失。** 与 Selene 相同，ETL 中不存在 MRC 的 Step 3 处理逻辑。
>
> MRC 同时提供了：(1) 主日报中的 `min_status` 逾期状态，(2) 专项 FCL 表中的 `fc_flag` 激活标志——两个非常有价值的字段，但均未被系统用于 `delinq` 输出。

**缺口分析**

| 缺口 | 风险等级 | 说明 |
|------|---------|------|
| Step 3 完全缺失 | 🔴 严重 | 所有 MRC 贷款的 FCL 状态无法通过日报路径产生 |
| `min_status` 始终为空 | 🔴 严重 | DB实测：全部 12,740 行均为空字符串，该字段完全不可用。根本原因未知（MRC 系统问题？字段未启用？） |
| `fc_flag` 从未激活 | 🔴 严重 | DB实测：`portmrcforeclosure` 仅 18 行，全为 `'N'`，从未出现 `'Y'`。FCL 专项表有 `referral_hold_reason` 字段（值如 "HOLD 99 OPEN DEMAND AGING"）说明有止赎贷款，但 `fc_flag` 从未被置为激活 |

**推荐补全字段请求**

| **LM：仅有宽限专项表，无整体 LM 标志** | 🟡 中等 | MRC 有 `portmrcforbearance` 专项表（`status` 字段），但无顶层 `lm_flag`，且无 `lm_type`、日期字段。**需向 MRC 请求：顶层 `lm_flag` + `lm_type` + `lm_start_date`** |

需向 MRC 确认：
- `portmrcloan.min_status` 为何始终为空（是否另有逾期状态字段？）
- `portmrcforeclosure.fc_flag = 'Y'` 的激活条件（是否 MRC 系统从未更新此字段为 'Y'？）
- 替代方案：`portmrcforeclosure.fc_status` 或 `fc_milestone` 是否可以推导 FCL 状态

---

### 3.6 Arvest — ❌ 无逾期状态字段，FCL 永远无法产生

**数据概览**

| 属性 | 值 |
|------|-----|
| 数据频率 | **月报 only**（无日报） |
| 文件格式 | `.xlsx`（多个 Excel 文件合并） |
| 关键原始表 | `arvest.portarvestremitmonthlystatement`（月度贷款报表）、`arvest.portarvestremit`（月度还款数据） |

**FCL 相关原始字段**（MySQL Layer 1 原始字段）

| 完整字段路径（schema.table.field） | 业务含义 | 取值范围/示例 | FCL 用途 |
|----------------------------------|---------|------------|---------|
| `arvest.portarvestremitmonthlystatement.nextduedate` | 下一应付款日期 | `DATE` | **唯一可用字段**，用于 days360 兜底 |
| `arvest.portarvestremitmonthlystatement.due_date` | 到期日 | `DATE` | 辅助参考 |
| ~~逾期状态字段~~ | **不存在** | — | Arvest 月报中无逾期状态字段 |

**FCL 状态判断规则**

> ⚠️ **严重限制：Arvest 月报中没有任何逾期状态字段（如 `loan_status`、`delinquency_status` 等），系统只能依赖 `days360(nextduedate)` 计算逾期天数。**

1. **FCL / REO / Paid-Off**：代码中存在判断逻辑（`svcdelinq = 'Foreclosure'` 等），但 `svcdelinq` 字段在 Arvest 路径中**始终为 null**
2. **实际有效规则**：完全退化为 days360 兜底
   - `days360 < 30` → C
   - `days360 < 60` → D30
   - `days360 < 90` → D60
   - `days360 < 120` → D90
   - 其他 → D120P
3. **结果**：处于 Foreclosure 的 Arvest 贷款被错误分类为 `D120P`，`delinq = 'FCL'` 在 Arvest 路径中**永远无法产生**

**缺口分析**

| 缺口 | 风险等级 | 说明 |
|------|---------|------|
| 无逾期状态字段 | 🔴 严重 | Arvest 月报中根本没有 `loan_status` 或等效字段 |
| FCL 状态永远无法产生 | 🔴 严重 | 所有 Arvest FCL 贷款被误标为 D120P |
| 仅月报 | 🟡 中等 | T+1 月数据延迟，无法实时反映 FCL 进展 |

**推荐补全字段请求（高优先级）**

| **LM：无任何 LM 字段** | 🟡 中等 | Arvest 月报中无 `lm_flag` 或任何 LM 相关字段，无法判断贷款是否处于 LM。**需向 Arvest 请求：`lm_flag` + `lm_type`（与逾期状态字段一同请求）** |

需向 Arvest 请求以下字段之一（任一均可解决核心问题）：
- `loan_status` 或 `delinquency_status`：包含 `'Foreclosure'`、`'REO'` 等状态值
- `foreclosure_flag`：FCL 激活的二元标志（`'Y'`/`'N'` 或 `1`/`0`）
- `lm_flag` + `lm_type`：LM 状态字段

---

### 3.7 CapeCodFive — ❌ FCL 永远无法产生（值格式不匹配）

**数据概览**

| 属性 | 值 |
|------|-----|
| 数据频率 | **月报 only**（无日报） |
| 文件格式 | `.xlsx`（自定义格式） |
| 关键原始表 | `capecodfive.portcapecodfive_monthly_servicing`（月度服务报告，含 MBA 标准逾期状态） |

**FCL 相关原始字段**（MySQL Layer 1 原始字段）

| 完整字段路径（schema.table.field） | 业务含义 | 取值范围/示例 | FCL 用途 |
|----------------------------------|---------|------------|---------|
| `capecodfive.portcapecodfive_monthly_servicing.mba_delinquency_status` | MBA 标准逾期状态字段名，但 **实际值为数字型 DPD 字符串** | `''`(6,459行)、`'29.0'`(11)、`'30.0'`(7)、`'27.0'`(7)、`'26.0'`(5)、`'60.0'`(2)、`'90.0'`(1) 等 — ⚠️ **无任何 `'Foreclosure'` 文本值** | DB实测：ETL 检查 `svcdelinq = 'Foreclosure'`，但值为数字，永远不匹配（DB实测 2026-05-25） |
| `capecodfive.portcapecodfive_monthly_servicing.next_payment_due_date` | 下一应付款日期（月度服务报告） | `DATE` | days360 兜底 |
| `capecodfive.portcapecodfive_remit_report.next_due` | 下一应付款日期（还款报告，优先使用） | `DATE` | days360 兜底 |



**FCL 状态判断规则（实际执行结果）**

> ⚠️ **关键发现：ETL 代码检查 `svcdelinq = 'Foreclosure'` 但 `mba_delinquency_status` 的实际值是数字型 DPD 字符串（如 `'29.0'`, `'30.0'`），永远不会等于文本 `'Foreclosure'`。**
>
> 效果与 Arvest 相同：**FCL 状态在 CapeCodFive 路径下永远无法产生**，所有 FCL 贷款均被误分类为 D120P。

1. ~~**FCL**：`svcdelinq = 'Foreclosure'`~~ → 永远不匹配（值为数字字符串）
2. ~~**REO**：`svcdelinq IN ('R', 'REO')`~~ → 永远不匹配
3. ~~**Paid-Off（P）**：`svcdelinq = 'Completed Payoff'`~~ → 永远不匹配
4. **无数据**：`nextduedate IS NULL` → `delinq = NULL`
5. **实际唯一有效规则（days360 兜底）**：退化为纯日期计算 → C / D30 / D60 / D90 / D120P

**缺口分析**

| 缺口 | 风险等级 | 说明 |
|------|---------|------|
| `mba_delinquency_status` 值格式错误 | 🔴 严重 | 该字段名为"MBA标准逾期状态"，但实际值是数字型 DPD（如 `'29.0'`），非文本状态码。文本匹配逻辑永远失效 |
| FCL 状态永远无法产生 | 🔴 严重 | 与 Arvest 相同，所有 FCL 贷款被误标为 D120P |
| 无独立 FCL 标志字段 | 🔴 严重 | 无任何安全网 |
| 仅月报 | 🟡 中等 | T+1 月数据延迟 |

**推荐补全字段请求（高优先级）**

| **LM：无任何 LM 字段** | 🟡 中等 | CapeCodFive 月报中无 `lm_flag` 或任何 LM 相关字段。**需向 CapeCodFive 请求：`lm_flag` + `lm_type`（与逾期状态字段一同请求）** |

需向 CapeCodFive 请求以下字段之一：
- `loan_status` 或 `delinquency_status`：包含 `'Foreclosure'`、`'REO'` 等文本状态值
- `foreclosure_flag`：FCL 激活的二元标志（`'Y'`/`'N'`）
- `lm_flag` + `lm_type`：LM 状态字段

---

### 3.8 FCI — ❌ 完全未实现 FCL 判断

**数据概览**

| 属性 | 值 |
|------|-----|
| 数据频率 | 日报（通过 GraphQL API） |
| 文件格式 | GraphQL API（60+ 报告类型） |
| 关键原始表 | `fci.portfciloanportfolio`（主贷款组合）、`fci.portfciwebforeclosure`（FCL 专项） |

**FCL 相关原始字段**（MySQL Layer 1 原始字段，通过 GraphQL API 采集入库）

| 完整字段路径（schema.table.field） | 业务含义 | 取值范围/示例 | FCL 用途 |
|----------------------------------|---------|------------|---------|
| `fci.portfciloanportfolio.status` | 贷款状态（⚠️注：字段名为 `status`，非 `loanStatus`） | `'Paid off'`(65K)、`'Performing'`(31K)、`'Transfer out'`(14K)、**`'Foreclosure'`(2,371)**、**`'REO'`(2,040)**、`'Delinquency'`(1,570)、`'Bankruptcy'`(112)、`'Closed'`(721)、**`'Pre Foreclosure'`(37)** | **采集至 MySQL，但完全未接入 delinq 判断**（DB实测 2026-05-25） |
| `fci.portfciloanpaystring.currentDQStatus` | 当前逾期状态 | 需进一步查询 | 采集未使用 |

**FCL 状态判断规则**

> ❌ **完全未实现。** FCI 数据通过 GraphQL API 采集并存入 MySQL，但没有任何后续 ETL 逻辑将其转换为标准 `delinq` 状态。FCI 贷款在所有分析表（portmonthbase/portmonth）中均无 FCL 判断结果。

**缺口分析**

| 缺口 | 风险等级 | 说明 |
|------|---------|------|
| 完全未接入 ETL 判断流程 | 🔴 严重 | 所有 FCI 贷款的 FCL 状态在系统中不存在。DB实测：FCI 有 **2,408 行 FCL 数据**（`'Foreclosure'`+`'Pre Foreclosure'`），全部被忽略 |
| 字段名文档错误 | 🟡 中等 | 原文档写 `loanStatus`，DB实测正确列名为 `status`（小写，无驼峰命名）|
| `currentDQStatus` 取值未确认 | 🟡 中等 | 需进一步查询 `fci.portfciloanpaystring` |
| **LM：无任何 LM 字段** | 🟡 中等 | FCI 数据中无 `lm_flag` 或任何 LM 相关字段。**ETL 实现后，需向 FCI 请求：`lm_flag` + `lm_type`** |

---

## 缺口汇总与优先级

### Layer 2 — 缺口全景

> **术语速查（详细定义见文档顶部"ETL 层次说明"）**
> - **Layer 2 / L2**：Redshift `port.basic_data_daily_loan_common`，ETL Step 1 将所有 Servicer 原始 MySQL 数据合并、字段重命名后写入的统一暂存表。"Layer 2 — 缺口全景"表示以下缺口均在 L2 层面被识别到。
> - **Step 3**：`daily_data_loan_common_clean_config.py` 中的 FCL/REO/P/D30... 状态判断逻辑，读取 L2 中的 `svcdelinq` / `fcl_flag` 等字段，输出最终标准化的 `delinq` 状态码写入 L3（`basic_data_daily_loan_common_clean`）。"Step 3 缺失"= 该 Servicer 在此文件中没有对应的 SQL 处理块，`delinq` 永远为空。

| 优先级 | Servicer | 缺口类型 | 所需字段/行动 |
|--------|---------|---------|------------|
| P0（立即） | Selene | Step 3 缺失，但 `foreclosure_status_code='A'`(41行) 已在 L2 中 | **无需新字段**：直接在 Step 3 加 `WHEN fcl_flag='A' THEN 'FCL'` |
| P0（立即） | MRC | Step 3 缺失，`min_status` 为空，`fc_flag` 从未激活 | 向 MRC 确认替代字段（`fc_status`/`fc_milestone`），或请求逾期状态字段 |
| P0（立即） | Arvest | 无任何逾期状态字段 | 向 Arvest 请求 `loan_status` 或 `foreclosure_flag` |
| P0（立即） | CapeCodFive | `mba_delinquency_status` 为数字 DPD，FCL 文本匹配永远失败 | 向 CapeCodFive 请求文本型逾期状态字段或 FCL 标志 |
| P0（立即） | FCI | 完全未实现，2,408 行 FCL 数据被忽略 | 实现完整 ETL 判断逻辑（`status='Foreclosure'`） |
| P1（近期） | Newrez | `fcl_flag` 采集但为 null | 调研 `portnewrezfc` 表中的 FCL 标志字段 |
| P1（近期） | SLS | 无 FCL 标志，`portfcldaily` 未使用 | 利用 `portfcldaily` 数据作为校验 |
| P1（近期） | SLS / Arvest / CapeCodFive / FCI / MRC | 无 `lm_flag`，无法判断 LM 状态 | 各 Servicer 补充 `lm_flag` + `lm_type` |
| P2（中期） | Newrez / Carrington / Selene | 有 LM 标志，缺 `lm_type` 和日期 | 请求 `lm_type` + `lm_start_date` + `lm_end_date` |
| P2（中期） | 所有 Servicer | 无统一破产独立字段 | 各 Servicer 补充独立破产标志 |

### FCL 判断最小字段集：系统需求 × Servicer 请求对照

每个 Servicer 最少应提供以下字段，系统才能可靠判断 FCL 状态。下表同时标注了哪些字段是系统算法所需（ETL 视角）以及哪些需要向 Servicer 主动请求（接口视角）：

| 字段 | 类型 | 系统需要 | 需请求 Servicer | 优先级 | 说明 |
|------|------|---------|----------------|--------|------|
| `delinquency_status_mba` | VARCHAR ENUM | ✓ | ✓ | P0 | MBA 文本枚举主要判断依据（FCL/REO/DPD 分段/Payoff） |
| `fcl_flag` | `'Y'`/`'N'` | ✓ | ✓ | P0 | FCL 独立激活标志（安全网，防止状态延报）；当前仅 Carrington 实现 |
| `next_payment_due_date` | DATE | ✓ | — 所有 Servicer 已提供 | — | days360 兜底计算；现有字段，无需额外请求 |
| `fcl_hold_flag` | `'Y'`/`'N'` | ✓ | ✓ | P1 | FCL 是否处于暂停状态（MBA 报 Foreclosure 但实际 hold） |
| `fcl_hold_reason` | VARCHAR ENUM | ✓ | ✓ | P1 | 暂停原因（`LM` / `BK` / `HUD` / `Covid` / `Other`） |
| `bankruptcy_flag` | `'Y'`/`'N'` | ✓ | ✓（均无） | P1 | 独立破产标志。MBA `Bankruptcy` 与 `Foreclosure` 枚举**互斥**，无法表达 FCL+BK 并存状态；独立 flag 才能捕获"FCL 因 BK 暂停"的混合场景 |

> **参照模板**：目前只有 **Carrington** 同时提供了 `loan_status`（MBA 近似值）+ `fcl_flag`（独立激活标志），是最接近此理想模型的 Servicer，可作为向其他 Servicer 提出数据规范要求时的参照。

---

---

## LM（Loss Mitigation）字段需求规范

### LM 六种类型

| LM 类型 | 业务含义 | 典型持续时间 | 结果 |
|--------|---------|------------|------|
| **Forbearance**（宽限协议） | 暂停或减少还款，到期后补缴 | 3–12 个月 | 临时性，到期恢复或转 Modification |
| **Loan Modification**（贷款修改） | 永久修改利率 / 期限 / 本金 | 永久 | 最彻底的 LM 方案 |
| **Repayment Plan**（还款计划） | 分期补缴历史欠款 | 3–6 个月 | 与正常还款并行 |
| **Trial Period Plan**（试用期方案） | 修改正式生效前的考察期 | 3 个月 | 试用通过才转为 Permanent Modification |
| **Short Sale**（短售） | 低于贷款余额出售房产，免除剩余债务 | 数月 | 贷款终结，delinq → P |
| **Deed in Lieu**（代位放弃产权） | 借款人主动将房产转让给贷款方 | 数月 | 贷款终结，免于止赎拍卖 |

### 向 Servicer 请求 LM 数据的最小字段集

| 字段名（建议） | 类型 | 优先级 | 说明 |
|------------|------|--------|------|
| `lm_flag` | `'Y'`/`'N'` | **P0 必须** | 是否处于活跃 LM——最基础信号，所有 Servicer 均应提供 |
| `lm_type` | 枚举文本 | **P1 建议** | `Forbearance` / `Modification` / `RepaymentPlan` / `TrialPlan` / `ShortSale` / `DeedInLieu` |
| `lm_start_date` | DATE | **P1 建议** | LM 方案开始日期 |
| `lm_end_date` | DATE | **P1 建议** | 宽限 / 方案到期日（到期是否续签是关键决策点） |
| `lm_status` | 枚举文本 | **P2 可选** | `Active` / `Trial` / `Completed` / `Denied` / `Expired` |

> **实践建议**：优先要求 `lm_flag` + `lm_type`。`lm_flag` 决定是否在 LM，`lm_type` 决定是什么类型的 LM，两者组合即可覆盖 90% 的业务判断需求。

### 各 Servicer LM 数据现状与缺口

> **"进入 L2"列说明**：L2 = Redshift `port.basic_data_daily_loan_common`，是所有 Servicer 数据经 ETL Step 1 合并后的统一暂存表，字段名已标准化（如 `lm_flag`、`svcdelinq`）。"进入 L2" 表示该 Servicer 的 LM 原始字段是否已被 ETL Step 1 映射为 L2 中的 `lm_flag='Y'/'N'`。✅ 表示已写入；❌ NULL 表示 L2 中 `lm_flag` 为空，LM 信息在 L2 已丢失（下游无法使用）。

| Servicer | 当前 LM 字段 | 进入 L2 | 覆盖质量 | 行动项 |
|---------|------------|--------|---------|------|
| **Newrez** | `activelmflag`('1'/'0') + `forbearancestatus`（数字码） | ✅ `lm_flag='Y'/'N'` | 🟡 有标志，无类型和日期 | 请求 `lm_type` + `lm_start_date` |
| **Carrington** | `lm_flag`('Active'/其他) + `covid_forbearance_flag` | ✅ `lm_flag='Y'/'N'` | 🟡 有标志，无类型和日期 | 请求 `lm_type` + `lm_start_date` |
| **Selene** | `lm_setup_date`（非空=激活） | ✅ `lm_flag='Y'/'N'`（Step 3 缺失） | 🟡 有标志，无类型 | 先修 Step 3；再请求 `lm_type` |
| **MRC** | `portmrcforbearance.status`（宽限专项表） | ✅ `forbearance` 字段，但无 `lm_flag` | 🟡 有宽限，无整体 LM 标志 | 请求顶层 `lm_flag` + `lm_type` |
| **SLS** | 无 | ❌ NULL | ❌ | 请求 `lm_flag` + `lm_type` |
| **Arvest** | 无 | ❌ NULL | ❌ | 请求 `lm_flag`（月报中增加字段） |
| **CapeCodFive** | 无 | ❌ NULL | ❌ | 请求 `lm_flag`（月报中增加字段） |
| **FCI** | 无 | ❌ NULL | ❌ | 实现 ETL 后再请求 `lm_flag` |

---

## 对应英文版

英文版：`docs/en/08_servicer_fcl_field_mapping.md`
