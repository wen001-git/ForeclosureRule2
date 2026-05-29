# 04 — 状态码完整清单

---

## 文档信息

| 项目 | 内容 |
|------|------|
| **文档目的** | 系统内所有止赎/逾期/REO/破产/损失缓解状态码的权威清单，包含每个代码的含义、来源字段、生成层次、业务用途和生命周期阶段。 |
| **解决的问题** | 状态码散布在多个配置文件和多个处理层，且原始服务商代码与标准代码混用，本文档一次性整合所有代码。 |
| **覆盖范围** | Layer 1（服务商原始代码）→ Layer 4（标准化代码及特殊状态）；涵盖所有12种标准 delinq 值及辅助标志 |
| **系统归属** | 见 `03_fcl_status_logic.md` |

**目标读者：** 业务分析师 · 数据验证/对账工程师 · 报表开发者 · 新成员

**依赖文档：** `01_source_data.md`（原始字段）、`03_fcl_status_logic.md`（生成逻辑）

**修订历史：**

| 日期 | 作者 | 版本 | 变更内容 |
|------|------|------|---------|
| 2026-05-21 | AI Agent (Claude Sonnet 4.6) | v1 | 初始版本，代码逆向 + DB 实证 |

---

## 1. 标准化 `delinq` 代码全览

`delinq` 是 `port.portmonthbase` 等核心表的主状态字段，代表贷款当月的逾期/止赎状态。

| 代码 | 含义 | 生成层次 | 来源/生成方式 | 业务用途 | 生命周期阶段 | DB实证 |
|------|------|---------|------------|---------|------------|-------|
| `C` | 当前状态（< 30天逾期） | Layer 2 | `days360(nextduedate, fctrdt) < 30` | 正常贷款监控 | 正常履约 | 72,796条 (92.2%) |
| `D30` | 30-59天逾期 | Layer 2 | `days360 ∈ [30,60)` | 早期逾期跟踪 | 早期逾期 | 2,274条 (2.9%) |
| `D60` | 60-89天逾期 | Layer 2 | `days360 ∈ [60,90)` | 逾期升级监控 | 逾期 | 480条 (0.6%) |
| `D90` | 90-119天逾期 | Layer 2 | `days360 ∈ [90,120)` | 损失缓解触发 | 严重逾期 | 206条 (0.3%) |
| `D120P` | 120天以上逾期 | Layer 2 | `days360 ≥ 120` | FCL转介候选 | 严重逾期 | 403条 (0.5%) |
| `FCL` | 止赎进行中 | Layer 2 | `svcdelinq='Foreclosure'` 或 `status='F'` | FCL跟踪、损失分析 | 止赎 | 279条 (0.4%) |
| `REO` | 银行接管房产 | Layer 2 | `svcdelinq='REO'` 或 `status IN ('R','REO')` | REO处置跟踪 | 止赎后 | 12条 (0.02%) |
| `P` | 全额还清/清算 | Layer 2 | `svcdelinq IN ('Full Payoff','Paid in Full',...)` 或 `balance=0` | 贷款减少分析 | 清算 | 2,288条 (2.9%) |
| `D` | 确认逾期（止赎后重入） | Layer 3 | `prevdelinq IN ('D120P','FCL','REO')` 且仍逾期 | 严重违约历史追踪 | 再入逾期 | 273条（clean表） |
| `VASP` | Vendee/Servicer Purchase | Layer 4 | 运营覆盖（疑似 `port.basic_data_loan_fix`），仅 Newrez | 政府担保贷款特殊处置 | 特殊处置 | 19条 |
| `REPUR` | 贷款回购 | Layer 4 | 服务商特定逻辑或人工标记，仅 Carrington | 回购贷款跟踪 | 特殊处置 | 1条 |
| `NULL` | 未填充 | — | 数据缺失或处理中 | 数据质量监控 | — | 155条 (0.2%) |

---

## 2. 辅助标志字段

这些字段与 `delinq` 并列存在，提供额外的状态维度。

| 字段 | 取值 | 含义 | 生成方式 |
|------|------|------|---------|
| `fcl_flag` | `1`/`0` 或原始文字 | 服务商活跃止赎标志 | Newrez: `activefcflag`; SLS: `fcl_active_flag`; Carrington: `foreclosure_status_code`; MRC: `fc_flag` |
| `lm_flag` | `'Y'`/`'N'` | 损失缓解活跃 | Newrez: `activelmflag='1'→Y`; Carrington: `lm_flag='Active'→Y`; SLS: 从 `loss_mit_evaluation_status` 推断 |
| `bankruptcy` | `'Y'`/`'N'` | 破产状态 | Newrez: `delinquency_status_mba LIKE '%Bankruptcy%'`; SLS: `bk_active_flag` |
| `prevdelinq` | 同 `delinq` 代码集合 | 上月状态 | LAG 窗口函数 over `portmonthbase ORDER BY fctrdt` |

---

## 3. 付款历史字符编码

`paymthistfull` 字符串由每月 `prevdelinqchar` 拼接而成（最新月在前）。

| `delinq` 代码 | `prevdelinqchar` | 字符含义 |
|--------------|-----------------|---------|
| `FCL` | `F` | Foreclosure |
| `REO` | `R` | REO |
| `P` | `P` | Paid off |
| `D` | `D` | Confirmed delinquent |
| `C` | `0` | Current |
| `D30` | `1` | 30 days past due |
| `D60` | `2` | 60 days past due |
| `D90` | `3` | 90 days past due |
| `D120P` | `4` | 120+ days past due |

**示例历史字符串：** `"F4432100000"` = 12个月付款记录（左→新，右→旧），该贷款当前已从止赎（F）逐步恢复到当前状态（0）

---

## 4. 原始服务商代码映射

### 4.1 Newrez / Shellpoint（`delinquency_status_mba` 字段）

| 原始值 | 标准 `delinq` | 备注 |
|-------|--------------|------|
| `Current` | `C`（或 `VASP`*） | VASP 为特殊覆盖 |
| `1-29 DPD` / `30-59 DPD` | `D30` | |
| `60-89 DPD` / `60-89` | `D60` | |
| `90-119 DPD` / `DQ 90` | `D90` | |
| `120-149 DPD` / `180+ DPD` | `D120P` | |
| `Foreclosure` | `FCL` | |
| `Foreclosure / Perf BK` | `FCL` | `bankruptcy='Y'` |
| `Foreclosure / Non-Perf BK` | `FCL` | `bankruptcy='Y'` |
| `REO` | `REO` | |
| `Full Payoff` / `Paid in Full` | `P` | |
| `Completed Short Sale` | `P` | |
| `Service Release` | `P` | |
| `Loss Mitigation` | days360计算结果 | `lm_flag='Y'` |
| `Performing Bankruptcy` / `Bankruptcy - Performing` | days360计算结果 | `bankruptcy='Y'` |
| `Non-Performing Bankruptcy` | days360计算结果 | `bankruptcy='Y'` |

\* VASP（19条）：`delinquency_status_mba` 为 Current（10条）、180+ DPD（8条）、Foreclosure（1条），均被覆盖为 VASP

### 4.2 SLS（`delq_status_mba` 字段）

| 原始值 | 标准 `delinq` |
|-------|--------------|
| `C` | `C` |
| `D30` | `D30` |
| `D60` | `D60` |
| `D90` | `D90` |
| `D120+` | `D120P` |
| `FCL` | `FCL` |
| `REO` | `REO` |
| `P` | `P` |
| `REPUR` | `REPUR`（直接透传） |

SLS 原始代码已接近标准格式，转换最简单。

### 4.3 Carrington（`status` + `loan_status` 字段）

| `status` 值 | 标准 `delinq` |
|------------|--------------|
| `'F'` | `FCL` |
| `'R'` / `'REO'` | `REO` |
| `'P'` | `P` |
| 其他 | days360计算 |

### 4.4 Interim 服务商（`svcdelinq` 字段）

| 原始值 | 标准 `delinq` |
|-------|--------------|
| `'Foreclosure'` | `FCL` |
| `'R'` / `'REO'` | `REO` |
| `'Completed Payoff'` | `P` |
| `balance = 0`（Arvest/Capecodfive） | `P` |
| 其他 | days360计算 |

---

## 5. FCL 汇总状态码（`summary_foreclosure_status`）

**表：** `port.basic_data_loan_foreclosure`  
**DB实证（共43条活跃 + 58条关闭）：**

| 汇总状态 | 记录数 | 含义 |
|---------|--------|------|
| `Active Foreclosure` | 43 | 止赎进行中 |
| `Closed Foreclosure:Reinstated` | 25 | 关闭（贷款复贷） |
| `Closed Foreclosure:Loss Mitigation` | 15 | 关闭（进入损失缓解） |
| `Closed Foreclosure:Paid in Full` | 10 | 关闭（全额还清） |
| `Closed Foreclosure:Process Complete` | 7 | 关闭（拍卖/REO完成） |
| `Closed Foreclosure:Deed in Lieu Cmplte` | 1 | 关闭（以房代偿完成） |
| NULL | 5,942 | 未填充 |

---

## 6. FCL 阶段代码（`port.fcl_stage_info.stage` 字段）

**DB实证（共 8,733 条记录）：**

| 阶段代码 | 记录数 | 业务含义 |
|---------|--------|---------|
| `DEMAND` | 448 | 催款函/意向通知发出 |
| `REFERRAL` | 3,341 | 委托律师转介 |
| `FIRST_LEGAL` | 800 | 首次法律行动提交 |
| `SERVICE` | 1,486 | 法律文书送达 |
| `JUDGEMENT` | 700 | 判决阶段 |
| `SALE` | 1,958 | 止赎拍卖 |

**阶段分组（`group` 字段）：**

| 分组 | 记录数 | 含义 |
|------|--------|------|
| `FCL` | 8,277 | 正式进入止赎的贷款 |
| `D120P` | 411 | 120天以上逾期的阶段跟踪 |
| `D90` | 39 | 90天逾期的阶段跟踪 |
| `REO` | 6 | 已进入 REO 阶段 |

---

## 7. 状态码生命周期关系

```
正常履约
  C ──→ D30 ──→ D60 ──→ D90 ──→ D120P
                                   │
                                   ├──→ FCL ──→ SALE ──→ REO
                                   │              └──→ P（止赎完成/还清）
                                   │
                                   └──→ LM（lm_flag=Y）──→ 修改成功 → C
                                                        └──→ 失败 → FCL

FCL/REO 后重入逾期：
  FCL/REO ──→（本月仍逾期）──→ D（确认逾期）

特殊状态（运营层）：
  VASP（政府担保贷款特殊处置）
  REPUR（贷款回购）
```

---

## 对应英文版

英文版：`docs/en/04_status_inventory.md`
