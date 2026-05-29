# 09 — Servicer 数据接口标准规范

---

## 文档信息

| 项目 | 内容 |
|------|------|
| **文档目的** | 定义新系统中，每个 Servicer 向系统提交贷款数据时必须遵守的字段规范、数据字典与交付格式，作为向 Servicer 发出正式字段补全请求的依据。 |
| **解决的问题** | 现有系统的 Servicer 数据接入缺乏统一标准：各 Servicer 字段名不同、枚举值不统一、关键状态字段缺失，导致 FCL / LM / BK 状态无法可靠推导。 |
| **覆盖范围** | 8 个在管 Servicer — SLS / Newrez / Carrington / Selene / MRC / Arvest / CapeCodFive / FCI |
| **系统归属** | 新系统接口设计层（PrefectFlow 重构前置规范） |

**目标读者：** 数据产品经理 · 业务分析师 · 新系统 ETL 架构师 · Servicer 对接工程师 · 合规审核

**依赖文档：**
- `08_servicer_fcl_field_mapping.md` — 各 Servicer 现状分析（本文档的数据依据）
- `07_fcl_lineage_and_rules.md` — 现有 ETL 实现细节（新系统设计参考）
- `01_source_data.md` — 原始表结构（字段来源索引）

**修订历史：**

| 日期 | 作者 | 版本 | 变更内容 |
|------|------|------|---------|
| 2026-05-25 | AI Agent (Claude Sonnet 4.6) | v2 | Group E 补充 `bankruptcy_flag` 独立设计原因说明（MBA 枚举互斥，无法表达 FCL+BK 并存） |
| 2026-05-25 | AI Agent (Claude Sonnet 4.6) | v1 | 初始版本，基于 doc 08 DB 实测数据逆向研究 |

---

## 1. 文档目的与适用范围

本文档是新系统的 **Servicer 数据接入标准**，定义"目标状态"。

| 文档 | 视角 | 作用 |
|------|------|------|
| **doc 08**（现状） | "Servicer 现在给什么" | 现状分析、缺口识别 |
| **doc 09**（规范）| "新系统要求 Servicer 给什么" | 接口设计、补全请求依据 |

### 优先级定义

| 优先级 | 含义 | 系统行为 |
|--------|------|---------|
| **P0 必须** | 缺少此字段，系统无法正确处理该贷款 | 拒绝接入或标记为数据质量异常 |
| **P1 建议** | 缺少此字段，关键业务分析降级（FCL 时间线、LM 类型无法区分） | 接受但标注数据完整度不足 |
| **P2 可选** | 提供此字段可支持更精细的分析 | 有则使用，无则忽略 |

---

## 2. 四维状态模型（核心设计原则）

### 2.1 贷款状态的四个正交维度

美国抵押贷款的状态由四个**完全独立**的维度组成，不可相互替代：

```
维度 A — Delinquency（逾期程度）= 欠款多严重？
          Current → DQ30 → DQ60 → DQ90 → DQ120P

维度 B — FCL（止赎状态）         = 法律程序是否已启动？
          N（未启动） / Y（止赎进行中）

维度 C — LM（损失缓解）          = 是否有主动补救方案？
          N（无 LM） / Y（宽限/修改/还款计划等）

维度 D — BK（破产）              = 借款人是否申请破产？
          N（未破产） / Y（破产自动中止令生效）
```

**同一笔贷款可以同时处于多个维度**：

| 示例 | Delinquency | FCL | LM | BK | 业务含义 |
|------|-------------|-----|----|----|---------|
| 典型止赎 | `D120P` | `Y` | `N` | `N` | 严重逾期已进入法律程序 |
| 止赎中谈判 | `FCL` | `Y` | `Y` | `N` | 进入止赎但同时在谈宽限 |
| 破产保护中 | `D90` | `Y` | `N` | `Y` | 破产自动中止令暂停止赎 |
| 正常贷款 | `Current` | `N` | `N` | `N` | 按时还款，无任何特殊状态 |

### 2.2 关键原则

1. **FCL 是法律状态，不是逾期程度** — `FCL` 绝不能从 `days360` 推算，必须由 Servicer 明确提供（逾期 120 天≠止赎，止赎需要法律程序启动的显式标志）

2. **MBA 标准统一** — `delinquency_status` 必须使用 MBA 标准枚举文本，不得使用数字 DPD 字符串（如 `'29.0'`）

3. **双文件模型** — 主日报（当前状态快照）+ FCL 专项报告（详细时间线），两者并行提交

4. **四维独立传递** — 四个维度各自有独立字段，不得将多个状态压缩进单一文本字段（如 `'Foreclosure / Perf BK'` 这种混合写法会给系统解析带来脆弱性）

---

## 3. 标准字段目录

> **格式说明**：字段名为建议标准名，Servicer 实际字段名可以不同，但值域必须符合本规范。系统接入时通过字段映射配置对齐。

### Group A — 贷款与报告标识

| 标准字段名 | 类型 | 优先级 | 允许值 / 格式 | 说明 |
|-----------|------|--------|-------------|------|
| `servicer_loan_id` | VARCHAR(50) | **P0** | 任意字符串，不含空格 | Servicer 侧唯一贷款编号，与我方系统 `loan_id` JOIN |
| `deal_id` | VARCHAR(50) | **P0** | 任意字符串 | 投资组合/Deal 编号 |
| `report_date` | DATE | **P0** | `YYYY-MM-DD` | 数据截止日（data as-of date） |

---

### Group B — 逾期状态（MBA 标准）

| 标准字段名 | 类型 | 优先级 | 允许值 | 说明 |
|-----------|------|--------|--------|------|
| `delinquency_status` | VARCHAR ENUM | **P0** | 见下方允许值表 | MBA 标准逾期状态文本，**不得使用数字 DPD**（见 ⚠️ 说明） |
| `next_payment_due_date` | DATE | **P0** | `YYYY-MM-DD` | 下一应付款日，用于 days360 兜底计算 |
| `days_past_due` | INTEGER | P1 | 0–999 | 数字型 DPD，与 `delinquency_status` 互相校验 |

**`delinquency_status` 允许值（系统均可接受，映射至内部码）：**

| 允许值 | 映射至系统内部码 | 说明 |
|--------|--------------|------|
| `Current` | `C` | 0–29 DPD，正常还款 |
| `1-29 DPD` | `C` | 细分版本（Newrez 等使用） |
| `30-59 DPD` | `D30` | |
| `60-89 DPD` | `D60` | |
| `90-119 DPD` | `D90` | |
| `120-149 DPD` | `D120P` | |
| `150-179 DPD` | `D120P` | |
| `180+ DPD` | `D120P` | |
| `Foreclosure` | `FCL` | |
| `REO` | `REO` | |
| `PaidOff` / `Full Payoff` / `Paid in Full` | `P` | |
| `Bankruptcy` / `Performing Bankruptcy` / `Non-Performing Bankruptcy` | 按 DPD 计算 + `bankruptcy='Y'` | 破产须同时通过 `bankruptcy_flag` 传递 |
| `REO Sale` / `3rd Party Sale` | `P` | 处置完成 |
| `Service Release` | 特殊处理 | 贷款服务权转让 |

> ⚠️ **禁止值格式**：`'29.0'`、`'30.0'`、`'90.0'` 等数字字符串（CapeCodFive 当前违反此规范，导致 FCL 永远无法被识别）。
>
> DPD : Days Past Due 逾期天数

---

### Group C — FCL 止赎状态

| 标准字段名 | 类型 | 优先级 | 允许值 | 说明 |
|-----------|------|--------|--------|------|
| `foreclosure_flag` | CHAR(1) | **P0** | `Y` / `N` | 是否处于活跃止赎程序（法律程序已正式启动） |
| `foreclosure_type` | VARCHAR ENUM | P1 | `Judicial` / `NonJudicial` | 司法止赎 vs 非司法止赎（影响时间线预期） |
| `foreclosure_stage` | VARCHAR ENUM | P1 | `Referral` / `FirstLegal` / `Service` / `Judgment` / `Sale` | 止赎程序当前所在阶段 |
| `foreclosure_start_date` | DATE | P1 | `YYYY-MM-DD` | FCL 程序最早启动日期（通常为律师转介日） |
| `referral_date` | DATE | P1 | `YYYY-MM-DD` | 移交律师/法律机构的日期 |
| `sale_date_scheduled` | DATE | P2 | `YYYY-MM-DD` | 计划拍卖日 |
| `sale_date_actual` | DATE | P2 | `YYYY-MM-DD` | 实际拍卖日（止赎完成后填入） |
| `fcl_exit_type` | VARCHAR ENUM | P2 | `3rdPartySale` / `REO` / `Reinstatement` / `ShortSale` / `DeedInLieu` | 止赎结束方式 |

> **最低要求**：新系统只需 `foreclosure_flag = 'Y'` 即可正确标记 FCL 状态。其余 P1/P2 字段支持时间线分析和风险评估。

> **FCL-Hold 说明**：MBA 标准中没有 `FCL-Hold` 状态。即使止赎程序处于暂停（Hold）状态，MBA 仍然报告为 `Foreclosure`。如果需要区分"止赎已暂停"vs"止赎进行中"，必须依赖 Group F 的 `hold_flag` + `hold_reason` 字段，而不能从 `delinquency_status` 推断。

---

### Group D — LM 损失缓解状态

| 标准字段名 | 类型 | 优先级 | 允许值 | 说明 |
|-----------|------|--------|--------|------|
| `lm_flag` | CHAR(1) | **P0** | `Y` / `N` | 是否处于活跃 LM 方案 |
| `lm_type` | VARCHAR ENUM | P1 | `Forbearance` / `Modification` / `RepaymentPlan` / `TrialPlan` / `ShortSale` / `DeedInLieu` | LM 方案类型（区分临时性 vs 永久性方案） |
| `lm_start_date` | DATE | P1 | `YYYY-MM-DD` | LM 方案开始日期 |
| `lm_end_date` | DATE | P1 | `YYYY-MM-DD` | LM 方案到期日（**关键**：到期是否续签是核心决策点） |
| `lm_status` | VARCHAR ENUM | P2 | `Active` / `Trial` / `Completed` / `Denied` / `Expired` | LM 方案当前状态 |

**LM 六种类型说明：**

| LM 类型 | 业务含义 | 典型持续时间 | 结果 |
|--------|---------|------------|------|
| **Forbearance** | 暂停或减少还款，到期后补缴 | 3–12 个月 | 临时性，到期恢复或转 Modification |
| **Loan Modification** | 永久修改利率 / 期限 / 本金 | 永久 | 最彻底的 LM 方案 |
| **Repayment Plan** | 分期补缴历史欠款，与正常还款并行 | 3–6 个月 | 完成后清零历史欠款 |
| **Trial Period Plan** | 修改正式生效前的考察期 | 3 个月 | 通过试用期才转为 Permanent Modification |
| **Short Sale** | 低于贷款余额出售房产，免除剩余债务 | 数月 | 贷款终结，`delinq → P` |
| **Deed in Lieu** | 借款人主动将房产转让给贷款方 | 数月 | 贷款终结，免于止赎拍卖 |

---

### Group E — 破产状态

| 标准字段名 | 类型 | 优先级 | 允许值 | 说明 |
|-----------|------|--------|--------|------|
| `bankruptcy_flag` | CHAR(1) | P1 | `Y` / `N` | 独立破产标志（**当前所有 8 个 Servicer 均无此独立字段**，均通过逾期状态文本推导） |
| `bankruptcy_chapter` | INTEGER | P1 | `7` / `11` / `13` | 破产章节（影响自动中止令范围和时间线） |
| `bankruptcy_filing_date` | DATE | P1 | `YYYY-MM-DD` | 破产申请日期 |
| `bankruptcy_discharge_date` | DATE | P2 | `YYYY-MM-DD` | 破产解除/驳回日期 |

> **为什么需要独立字段，而不是依赖 MBA `Bankruptcy` 枚举？** MBA `delinquency_status` 是单选互斥字段——当贷款同时处于 FCL 和 BK 时，Servicer 只能填一个值（报 `Foreclosure` 则丢失 BK 信息，报 `Bankruptcy` 则丢失 FCL 信息）。独立的 `bankruptcy_flag` 才能与 `foreclosure_flag` 并存，捕获"FCL 因 BK 自动中止令暂停"这一常见混合状态。

> **Chapter 7 vs Chapter 13 的实际影响**：Chapter 7（清算型，3–6 个月）vs Chapter 13（重组型，3–5 年还款计划）。FCL 在 BK 期间受自动中止令保护，需单独处理。

---

### Group F — Hold 暂停状态

| 标准字段名 | 类型 | 优先级 | 允许值 | 说明 |
|-----------|------|--------|--------|------|
| `hold_flag` | CHAR(1) | P1 | `Y` / `N` | FCL 程序是否处于暂停状态（BK/LM/HUD 等原因） |
| `hold_reason` | VARCHAR ENUM | P1 | `BK` / `LM` / `HUD` / `Covid` / `Other` | 暂停原因 |
| `hold_start_date` | DATE | P2 | `YYYY-MM-DD` | 暂停开始日期 |
| `hold_end_date` | DATE | P2 | `YYYY-MM-DD` | 暂停预计结束日期 |

---

### Group G — REO 银行持有房产

| 标准字段名 | 类型 | 优先级 | 允许值 | 说明 |
|-----------|------|--------|--------|------|
| `reo_flag` | CHAR(1) | **P0** | `Y` / `N` | 止赎完成，房产已归贷款方所有 |
| `reo_acquisition_date` | DATE | P1 | `YYYY-MM-DD` | 房产转让至贷款方的日期 |

---

## 4. 各 Servicer 合规矩阵

> 数据来源：`08_servicer_fcl_field_mapping.md`（DB 实测 2026-05-25）。✅ = 已提供且可用；🟡 = 部分提供或有问题；❌ = 完全缺失；⚠️ = 有字段但值格式错误。

| Servicer | 频率 | A: 标识 | B: 逾期状态 | C: FCL flag | D: LM | E: BK | F: Hold | G: REO |
|---------|------|---------|-----------|------------|-------|-------|---------|--------|
| **SLS** | 日 | ✅ | ✅ `delq_status_mba`（有 546 行 Foreclosure） | 🟡 无独立 flag；`portfcldaily.fcl_status` 未接入 | ❌ 无任何 LM 字段 | 🟡 文本推导（无独立 flag） | ❌ | ❌ |
| **Newrez** | 日 | ✅ | ✅ `delinquency_status_mba`（有 12K 行 Foreclosure） | 🟡 `portnewrezfc.fcl_flag` 已采集但值为 null | 🟡 有 `lm_flag`，无 type / 日期 | 🟡 文本推导（无独立 flag） | ❌ | ❌ |
| **Carrington** | 日 | ✅ | ✅ `loan_status`（2K Foreclosure rows）+ `fcl_flag` 双字段 | ✅ **全系统唯一实现独立 `fcl_flag`** | 🟡 有 `lm_flag`，无 type / 日期 | 🟡 文本推导（无独立 flag） | ❌ | ❌ |
| **Selene** | 日 | ✅ | 🟡 `loan_status` 无 Foreclosure 值（非标准术语） | 🟡 `foreclosure_status_code='A'`(41行) 已在 L2，但 Step 3 缺失 | 🟡 `lm_setup_date` 已采集，Step 3 缺失 | ❌ | ❌ | ❌ |
| **MRC** | 日 | ✅ | ❌ `min_status` 始终为空字符串（12,740 行全空） | ❌ `fc_flag` 从未为 'Y'（18 行全为 'N'） | 🟡 仅有 `portmrcforbearance` 专项表，无顶层 `lm_flag` | ❌ | ❌ | ❌ |
| **Arvest** | **月** | ✅ | ❌ **月报无任何逾期状态字段**（根本缺失） | ❌ 无 | ❌ 无 | 🟡 bid 表可推导 | ❌ | ❌ |
| **CapeCodFive** | **月** | ✅ | ⚠️ `mba_delinquency_status` = 数字 DPD 字符串（`'29.0'`）**不可用** | ❌ 无 | ❌ 无 | ❌ | ❌ | ❌ |
| **FCI** | 日(API) | ✅ | ✅ `status` 已采集（2,408 行 FCL rows），但**完全未接入 ETL** | ❌ 未接入 | ❌ 无 | ❌ | ❌ | ❌ |

---

## 5. 各 Servicer 缺口与行动项

### 5.1 SLS

**当前已满足**：Group A（标识）✅、Group B（`delq_status_mba` 含 `'Foreclosure'`）✅

**缺失（按优先级）**：
- P0: 无独立 `foreclosure_flag`（`portfcldaily.fcl_status` 存在但系统未读取）
- P1: 无 `lm_flag`、`lm_type`（完全缺失）
- P1: 无独立 `bankruptcy_flag`

**建议请求摘要**：向 SLS 请求在主日报中新增 `foreclosure_flag` (`Y`/`N`)，并在 LM 专项报告中提供 `lm_flag` + `lm_type`。同时建议启用现有 `portfcldaily` 文件的 `fcl_status` 字段，接入系统作为 FCL 二次校验。

---

### 5.2 Newrez

**当前已满足**：Group A ✅、Group B（含 12K FCL 行）✅、Group D（`lm_flag` 已有）🟡

**缺失（按优先级）**：
- P0: `portnewrezfc.fcl_flag` 采集但系统置为 null（内部 ETL 问题，需调研 `portnewrezfc` 表结构）
- P1: `lm_type`、`lm_start_date`、`lm_end_date`（只有标志，无明细）
- P1: 无独立 `bankruptcy_flag`

**建议请求摘要**：优先内部调研 `portnewrezfc` 中 `fcl_flag` 为何为 null；确认后启用该字段作为 FCL 双重校验。向 Newrez 请求 `lm_type` + `lm_start_date` + `lm_end_date`。

---

### 5.3 Carrington

**当前已满足**：Group A ✅、Group B（双字段：`loan_status` + `fcl_flag`）✅、Group C（`fcl_flag` = 全系统最佳）✅、Group D（`lm_flag` 已有）🟡

**缺失（按优先级）**：
- P1: `lm_type`、`lm_start_date`、`lm_end_date`（有标志，无明细）
- P1: 无独立 `bankruptcy_flag`（从 `loan_status` 文本推导）
- P1: `loan_status='Loss Mitigation'`（5K 行）未独立映射至 `lm_flag`

**建议请求摘要**：Carrington 是现状最佳 Servicer。主要需求是 `lm_type` + `lm_start_date` + `lm_end_date`，以及独立 `bankruptcy_flag`。

---

### 5.4 Selene

**当前已满足**：Group A ✅、Group C（`foreclosure_status_code='A'` 已采集）🟡、Group D（`lm_setup_date` 已采集）🟡

**缺失（按优先级）**：
- P0: **ETL Step 3 完全缺失**（无需向 Selene 请求新字段，内部修复即可）— 添加 `WHEN fcl_flag='A' THEN 'FCL'`
- P0: `loan_status` 不含 `'Foreclosure'`（Selene 使用非标准术语 `'No Contact'`/`'In Contact'`）
- P1: `lm_type`、`lm_end_date`（有 `lm_setup_date`，无类型和到期日）

**建议请求摘要**：优先修复 ETL Step 3（无需 Selene 配合）。同时请求 Selene 将 `loan_status` 枚举值对齐 MBA 标准，并补充 `lm_type` + `lm_end_date`。

---

### 5.5 MRC

**当前已满足**：Group A ✅（其余几乎全部缺失）

**缺失（按优先级）**：
- P0: `min_status` 始终为空（需向 MRC 确认：为何 12,740 行全为空？是否另有逾期状态字段？）
- P0: `fc_flag` 从未为 `'Y'`（需向 MRC 确认：激活条件是什么？`fc_status` / `fc_milestone` 是否可替代？）
- P0: ETL Step 3 缺失（内部修复，待 P0 字段问题解决后添加）
- P1: 无顶层 `lm_flag`（仅有 `portmrcforbearance` 专项表）
- P1: `lm_type`、`lm_start_date`

**建议请求摘要**：需先与 MRC 开会确认字段问题（`min_status` 为何为空，`fc_flag` 激活条件）。确认后向 MRC 请求：(1) 可用的逾期状态字段，(2) 可激活的 `fc_flag` 或替代字段，(3) 顶层 `lm_flag` + `lm_type`。

---

### 5.6 Arvest

**当前已满足**：Group A ✅（其余几乎全部缺失）

**缺失（按优先级）**：
- P0: **月报中无任何逾期状态字段**（根本性缺失，所有 FCL 贷款被误标为 D120P）
- P0: 无 `foreclosure_flag`
- P1: 无 `lm_flag`、`lm_type`
- 附加问题：仅提供月报（T+1 月数据延迟，FCL 实时性差）

**建议请求摘要**（高优先级）：向 Arvest 请求在月报中新增以下字段，并探讨能否升级为日报：
1. `delinquency_status`（`Current`/`DQ30`/.../`Foreclosure`/`REO`/`PaidOff` 枚举文本）
2. `foreclosure_flag`（`Y`/`N`）
3. `lm_flag` + `lm_type`

---

### 5.7 CapeCodFive

**当前已满足**：Group A ✅（其余几乎全部缺失）

**缺失（按优先级）**：
- P0: **`mba_delinquency_status` 值格式错误**（字段名为 MBA 标准，但实际值是数字 DPD `'29.0'`）— FCL 文本匹配永远失败
- P0: 无独立 `foreclosure_flag`（无任何安全网）
- P1: 无 `lm_flag`、`lm_type`
- 附加问题：仅提供月报（T+1 月数据延迟）

**建议请求摘要**（高优先级）：向 CapeCodFive 请求修正 `mba_delinquency_status` 字段格式（改为 MBA 标准文本枚举），并新增 `foreclosure_flag` + `lm_flag` + `lm_type`。

---

### 5.8 FCI

**当前已满足**：Group A ✅、Group B（`status` 已有 2,408 行 FCL 数据，但未接入 ETL）🟡

**缺失（按优先级）**：
- P0: **ETL 完全未实现**（2,408 行 FCL 数据在 MySQL 中被完全忽略）— 内部修复
- P0: FCL 数据从未流入下游（`portmonthbase`/`portmonth`）
- P1: 无 `lm_flag`、`lm_type`

**建议请求摘要**：优先实现 ETL（`status='Foreclosure'` 映射逻辑，无需 FCI 配合）。ETL 完成后，向 FCI 请求 `lm_flag` + `lm_type`。

---

## 6. 数据交付格式规范

| 规范项 | 要求 | 说明 |
|--------|------|------|
| **频率** | 日报（推荐）/ 月报（小组合可接受） | 月报有 T+1 月 FCL 变化延迟，不推荐 |
| **格式** | CSV（推荐，UTF-8）/ 固定宽度 TXT | 不使用 xlsx（解析脆弱、格式不稳定） |
| **日期格式** | `YYYY-MM-DD` | 拒绝 `MM/DD/YYYY`、`YYYYMMDD`、Excel 日期序列号 |
| **NULL 处理** | 空字符串 `''` 或显式 `NULL` | 不使用 `N/A`、`NA`、`None`、`-`、`0001-01-01` |
| **枚举值** | 必须使用 Section 3 定义的标准枚举 | 不接受自定义文本（如 `'Foreclosure / Perf BK'` 需拆分传递） |
| **文件命名** | `{servicer}_{report_type}_{YYYYMMDD}.csv` | 例：`newrez_main_20260525.csv` |
| **双文件模型** | 主日报 + FCL 专项报告 | FCL 专项报告包含止赎时间线字段（Group C 的 P1/P2 字段） |
| **字段顺序** | 按 Group A → B → C → D → E → F → G 顺序 | 便于系统自动校验 |

---

## 7. 向 Servicer 请求字段的优先级汇总

### 立即请求（P0 缺口，影响 FCL 状态准确性）

| Servicer | 请求内容 | 紧迫原因 |
|---------|---------|---------|
| **Arvest** | `delinquency_status`（文本型）或 `foreclosure_flag` | 所有 FCL 贷款被误标为 D120P |
| **CapeCodFive** | 将 `mba_delinquency_status` 改为文本枚举，或新增 `foreclosure_flag` | 字段格式错误导致 FCL 永远无法识别 |
| **MRC** | 确认 `min_status` 为何为空；确认 `fc_flag` 激活条件 | 两个 FCL 字段均无效，贷款状态完全缺失 |
| **SLS** | 接入 `portfcldaily.fcl_status` 作为校验来源 | 单字段匹配存在延报风险 |
| **FCI** | （内部修复 ETL，无需 FCI 配合） | 2,408 行 FCL 数据被完全忽略 |
| **Selene** | （内部修复 ETL Step 3，无需 Selene 配合） | 所有日报 FCL 状态丢失 |

### 近期请求（P1 缺口，影响 LM/BK 分析质量）

| Servicer | 请求内容 |
|---------|---------|
| **SLS** | `lm_flag` + `lm_type` |
| **Arvest** | `lm_flag` + `lm_type`（与逾期状态字段同批请求） |
| **CapeCodFive** | `lm_flag` + `lm_type`（与逾期状态字段同批请求） |
| **MRC** | `lm_flag` + `lm_type` + `lm_start_date` |
| **Newrez** | `lm_type` + `lm_start_date` + `lm_end_date` |
| **Carrington** | `lm_type` + `lm_start_date` + `lm_end_date` |
| **Selene** | `lm_type` + `lm_end_date` |
| **所有 Servicer** | 独立 `bankruptcy_flag` + `bankruptcy_chapter` |

---

## 对应英文版

英文版：`docs/en/09_servicer_data_interface_standard.md`
