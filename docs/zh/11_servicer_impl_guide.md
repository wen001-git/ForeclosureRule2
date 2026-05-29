# doc 11 — Servicer 现有数据 → 新系统 FCL 实施映射指南

---

## 文档目的

- **为什么存在**：新系统已定义 Servicer 数据接口标准（doc 09），但 Servicer 短期内无法按新格式提供数据。本文档基于 Servicer **现有数据**，给出新系统在过渡期的 FCL 实施方案——每个 Servicer 用什么字段、写什么逻辑、能实现哪些目标字段。
- **解决的问题**：doc 08 是分析文档（说明现状和差距），doc 09 是目标规范（说明应该做什么）。两者之间缺少一份**开发者可直接编码的实施参考**，本文档填补这个空白。
- **覆盖范围**：
  - 目标字段：`foreclosure_flag` / `delinquency_status` / `lm_flag` / `hold_flag` / `hold_reason` / `bankruptcy_flag` / `foreclosure_stage` / `referral_date` / `sale_date_scheduled` / `sale_date_actual`
  - 8 个 Servicer：SLS / Newrez / Carrington / Selene / MRC / Arvest / CapeCodFive / FCI
- **不覆盖**：字段的完整业务定义（见 doc 10 Glossary）；目标接口标准（见 doc 09）；现状分析详情（见 doc 08）
- **时效性**：本文档是**过渡期文档**。随 Servicer 按 doc 09 标准补充字段，对应章节应逐步更新或移除。

## 目标读者

主要读者：新系统 ETL 开发者 · 数据工程师  
次要读者：系统架构师 · 项目经理（了解现阶段可实现程度）

## 修订历史

| 日期 | 作者 | 版本 | 变更内容 | 关联文档 |
|------|------|------|---------|---------|
| 2026-05-25 | AI Agent (Claude Sonnet 4.6) | v1 | 初始版本，基于 doc 08 DB 实测数据（2026-05-25）；含 Newrez portnewrezfc 多次 Hold 处理方案 | doc 08 / doc 09 |

## 依赖文档

| 文档 | 关系 |
|------|------|
| `docs/zh/08_servicer_fcl_field_mapping.md` | 现状分析来源，本文档所有字段信息和规则均基于此 |
| `docs/zh/09_servicer_data_interface_standard.md` | 目标接口标准，本文档的目标字段命名与此对齐 |
| `docs/zh/10_glossary.md` | 术语定义参考 |

## 已知限制

- 本文档的字段取值范围和行数来源于 DB 实测（2026-05-25），随时间变化可能需要更新
- Selene / MRC / FCI 的 Step 3 逻辑尚未实现，本文档给出的是**应该实现的逻辑**，不代表当前系统已有

---

## Section 1: 当前可实现程度总览

> **图例**：✅ 可完整实现 | 🟡 可部分实现（有字段，逻辑需调整） | ⚠️ 有字段但数据质量问题 | ❌ 无法实现（无字段）

| Servicer | 频率 | foreclosure_flag | delinquency_status | lm_flag | hold_flag | bankruptcy_flag | 综合评级 |
|---------|------|-----------------|-------------------|---------|-----------|----------------|---------|
| **SLS** | 日 | 🟡 文本推导，无独立标志 | ✅ MBA 文本直接映射 | ❌ 无字段 | ❌ 无字段 | 🟡 文本推导 | 🟡 中等 |
| **Newrez** | 日 | 🟡→✅ 主表文本 + portnewrezfc 可升级 | ✅ MBA 文本 + 复合值 | ✅ activelmflag | 🟡 portnewrezfc 有但需逻辑推导 | 🟡 文本推导 | 🟡→✅ 升级空间大 |
| **Carrington** | 日 | ✅ 双字段（文本+独立标志） | ✅ loan_status 映射 | ✅ lm_flag | ❌ 无字段 | 🟡 文本推导 | ✅ 最完整 |
| **Selene** | 日 | 🟡 有字段，Step 3 待写 | ❌ 非标准 loan_status | 🟡 有 lm_setup_date，Step 3 待写 | ❌ 无字段 | ❌ 无字段 | ⚠️ 需写 Step 3 |
| **MRC** | 日 | ❌ fc_flag 从未激活 | ❌ min_status 全空 | 🟡 有专项表，无顶层标志 | ❌ 无字段 | ❌ 无字段 | ❌ 需确认 MRC |
| **Arvest** | 月 | ❌ 无字段 | ❌ 无逾期状态字段 | ❌ 无字段 | ❌ 无字段 | ❌ 无字段 | ❌ 需请求 Servicer |
| **CapeCodFive** | 月 | ❌ 无字段 | ⚠️ 数字 DPD（可转换，无 FCL） | ❌ 无字段 | ❌ 无字段 | ❌ 无字段 | ⚠️→❌ 仅 DPD 可用 |
| **FCI** | 日(API) | 🟡 有字段，Step 3 待写 | 🟡 有字段，Step 3 待写 | ❌ 无字段 | ❌ 无字段 | 🟡 `status='Bankruptcy'` | 🟡 需写 ETL |

---

## Section 2: 实施路线图

### 阶段一：立即可做（无需 Servicer 配合，只需写/调整 ETL 逻辑）

| Servicer | 工作内容 | 预期收益 |
|---------|---------|---------|
| **Newrez** | 利用 `portnewrezfc` 表中的 `activefcflag`、`fcstage`、`fcreferraldate`、`fcscheduledsaledate`、hold1/2/3 字段 | 从"仅文本匹配"升级为"活跃 FCL 标志 + 流程阶段 + Hold 历史" |
| **Selene** | 在 Step 3 中新增 Selene 处理块：`WHEN fcl_flag='A' THEN 'FCL'`（无需新字段） | 激活 41 条已采集的 FCL 记录；`lm_setup_date` 可推导 `lm_flag` |
| **FCI** | 在 Step 3/ETL 中新增 FCI 处理逻辑：`WHEN status='Foreclosure' THEN 'FCL'` | 激活 2,408 条已在 MySQL 中但被忽略的 FCL 记录 |
| **CapeCodFive** | 将数字 DPD 字符串转换为分段逾期码 | 至少恢复 DPD 判断（FCL 仍需向 Servicer 请求）|

### 阶段二：需向 Servicer 请求字段

| Servicer | 需请求的字段 | 优先级 | 阻塞内容 |
|---------|------------|--------|---------|
| **Arvest** | `delinquency_status`（含 `'Foreclosure'`）或 `foreclosure_flag` + `lm_flag` + `lm_type` | P0 | FCL 永远无法产生 |
| **CapeCodFive** | 文本型 `delinquency_status` 或 `foreclosure_flag` + `lm_flag` + `lm_type` | P0 | FCL 永远无法产生 |
| **MRC** | 确认 `min_status` 为空原因 + 请求替代逾期状态字段或 `foreclosure_flag` | P0 | FCL 无法判断 |
| **SLS** | `lm_flag` + `lm_type`（可利用 `portfcldaily` 辅助 FCL 校验） | P1 | LM 状态无法判断 |
| **所有 Servicer** | `lm_type` + `lm_start_date` + `lm_end_date`（目前仅 Carrington/Newrez/Selene 有 lm_flag） | P1–P2 | LM 细分类型无法区分 |

---

## Section 3: 各 Servicer 实施配方

> **字段命名约定**：使用 doc 09 标准接口字段名作为目标字段名。源字段用 `` `schema.table.field` `` 格式标注。

---

### 3.1 SLS（日报，数据截至 2024-07-05 切换至 Newrez）

**来源表**：`sls.portassetdaily`（主日报）、`sls.portfcldaily`（FCL 专项，目前未用）

#### `delinquency_status`（目标字段）
```sql
-- 来源：sls.portassetdaily.delq_status_mba
CASE delq_status_mba
    WHEN 'Paid in Full'     THEN 'PaidOff'
    WHEN 'Service Release'  THEN 'PaidOff'   -- 服务权转让，贷款离开
    WHEN 'REO'              THEN 'REO'
    WHEN 'Foreclosure'      THEN 'Foreclosure'
    WHEN 'Bankruptcy'       THEN 'DQ120P'    -- 辅助：同时设 bankruptcy_flag='Y'
    WHEN 'DQ 30'            THEN 'DQ30'
    WHEN 'DQ 60'            THEN 'DQ60'
    WHEN 'DQ 90'            THEN 'DQ90'
    WHEN 'Current'          THEN 'Current'
    ELSE days360_fallback(nextduedate)       -- 兜底
END
```

#### `foreclosure_flag`（目标字段）
```sql
-- ⚠️ 无独立 FCL 标志，仅文本推导（延报风险）
CASE WHEN delq_status_mba = 'Foreclosure' THEN 'Y' ELSE 'N' END
```
> **已知问题**：SLS 提供 `portfcldaily`（FCL 专项文件）但系统未利用。建议 P1 阶段用 `portfcldaily.fcl_status` 作为辅助校验。

#### `bankruptcy_flag`（目标字段）
```sql
CASE WHEN delq_status_mba = 'Bankruptcy' THEN 'Y' ELSE 'N' END
```

#### 无法实现的字段（需向 SLS 请求）
- `lm_flag` ❌ — SLS 数据中无任何 LM 字段
- `hold_flag` ❌ — 无字段
- `foreclosure_stage` ❌ — `portfcldaily` 中可能有，待确认

---

### 3.2 Newrez（日报，2024-07-05 起接替 SLS）

**来源表**：`newrez.portnewrezgeneral`（主日报）、`newrez.portnewrezfc`（FCL 专项 ⭐）、`newrez.portnewrezlm`（LM 专项）

> **⭐ 重要**：Newrez 是所有 Servicer 中 FCL 数据最丰富的。`portnewrezfc` 提供了 doc 09 Group C/F 要求的大多数字段，但**当前系统几乎未使用**。以下实施方案基于充分利用 `portnewrezfc`。

#### `delinquency_status`（目标字段）
```sql
-- 来源：newrez.portnewrezgeneral.delinquency_status_mba
CASE
    WHEN delinquency_status_mba IN ('Full Payoff', 'Paid in Full',
         '3rd Party Sale', 'REO Sale', 'Service Release') THEN 'PaidOff'
    WHEN delinquency_status_mba = 'REO'                   THEN 'REO'
    WHEN delinquency_status_mba IN ('Foreclosure',
         'Foreclosure / Non-Perf BK',
         'Foreclosure / Perf BK')                         THEN 'Foreclosure'
    WHEN delinquency_status_mba LIKE '%Bankruptcy%'        THEN 'DQ120P'
         -- 同时设 bankruptcy_flag='Y'
    WHEN delinquency_status_mba = '1-29 DPD'              THEN 'Current'
    WHEN delinquency_status_mba = '30-59 DPD'             THEN 'DQ30'
    WHEN delinquency_status_mba = '60-89 DPD'             THEN 'DQ60'
    WHEN delinquency_status_mba = '90-119 DPD'            THEN 'DQ90'
    WHEN delinquency_status_mba IN ('120-149 DPD', '150-179 DPD', '180+ DPD') THEN 'DQ120P'
    WHEN delinquency_status_mba = 'Current'               THEN 'Current'
    ELSE days360_fallback(nextduedate)
END
```

#### `foreclosure_flag`（目标字段）
```sql
-- 方案A（当前可用，文本推导）：
CASE WHEN delinquency_status_mba IN (
    'Foreclosure', 'Foreclosure / Non-Perf BK', 'Foreclosure / Perf BK'
) THEN 'Y' ELSE 'N' END

-- 方案B（推荐，利用 portnewrezfc — 无需 Servicer 提供新字段）：
-- JOIN newrez.portnewrezfc ON loanid = loanid AND dataasof = dataasof
CASE WHEN portnewrezfc.activefcflag = 1 THEN 'Y' ELSE 'N' END
```

#### `foreclosure_stage`（目标字段，来自 portnewrezfc）
```sql
-- 来源：newrez.portnewrezfc.fcstage / lastfcstepcompleted
-- 映射（原始值待实测确认，建议先查询 DISTINCT fcstage）：
CASE fcstage
    WHEN 'Referral'     THEN 'Referral'
    WHEN 'First Legal'  THEN 'FirstLegal'
    WHEN 'Service'      THEN 'Service'
    WHEN 'Judgment'     THEN 'Judgment'
    WHEN 'Sale'         THEN 'Sale'
    ELSE fcstage   -- 保留原始值，待后续标准化
END
```

#### `referral_date` / `sale_date_scheduled` / `sale_date_actual`（来自 portnewrezfc）
```sql
portnewrezfc.fcreferraldate         → referral_date
portnewrezfc.fcscheduledsaledate    → sale_date_scheduled
portnewrezfc.fcsalehelddate         → sale_date_actual
portnewrezfc.fcsetupdate            → foreclosure_start_date
portnewrezfc.fcresults              → fcl_exit_type（映射待定）
```

#### `hold_flag` / `hold_reason` / `hold_start_date`（来自 portnewrezfc，多次 Hold 处理）

> **背景**：Newrez 在 `portnewrezfc` 中提供最多 3 次 Hold 历史记录（`fchold1` / `fchold2` / `fchold3`）。新系统标准接口需要"当前活跃 Hold"，取法如下：

```sql
-- 取当前活跃 Hold（优先 hold3 → hold2 → hold1，取第一个 enddate 为空的）
CASE
    WHEN fchold3startdate IS NOT NULL AND fchold3enddate IS NULL
        THEN 1  -- hold3 活跃
    WHEN fchold2startdate IS NOT NULL AND fchold2enddate IS NULL
        THEN 2  -- hold2 活跃
    WHEN fchold1startdate IS NOT NULL AND fchold1enddate IS NULL
        THEN 1  -- hold1 活跃
    ELSE NULL   -- 无活跃 hold
END AS active_hold_num

-- 对应映射：
hold_flag       = CASE WHEN active_hold_num IS NOT NULL THEN 'Y' ELSE 'N' END
hold_reason     = CASE active_hold_num
                      WHEN 3 THEN fchold3description
                      WHEN 2 THEN fchold2description
                      WHEN 1 THEN fchold1description
                  END
hold_start_date = CASE active_hold_num
                      WHEN 3 THEN fchold3startdate
                      WHEN 2 THEN fchold2startdate
                      WHEN 1 THEN fchold1startdate
                  END
```

> **Hold 历史记录**（非标准接口，可选存储以供分析）：`fchold1description/startdate/enddate` × 3 次，覆盖 FCL 暂停的完整历史轨迹。

#### `lm_flag`（来自 portnewrezlm）
```sql
-- 来源：newrez.portnewrezlm.activelmflag
CASE WHEN activelmflag = '1' THEN 'Y' ELSE 'N' END
```

#### `bankruptcy_flag`
```sql
CASE WHEN delinquency_status_mba LIKE '%Bankruptcy%' THEN 'Y' ELSE 'N' END
```

#### 无法实现的字段（需向 Newrez 请求）
- `lm_type` ❌ — `forbearancestatus` 字段存在但为数字码，无法区分 Forbearance vs Modification
- `lm_start_date` / `lm_end_date` ❌ — 无

---

### 3.3 Carrington（日报，最完整的 Servicer）

**来源表**：`carrington.portcarrington`（综合日报，同时含逾期状态和 FCL 标志）

#### `delinquency_status`（目标字段）
```sql
-- 来源：carrington.portcarrington.loan_status
CASE
    WHEN loan_status IN ('Completed Payoff', 'Completed Short Sale',
         'Completed REO Sale')                THEN 'PaidOff'
    WHEN loan_status IN ('R', 'REO')          THEN 'REO'
    WHEN loan_status = 'Foreclosure'
         OR fcl_flag = 'Active'               THEN 'Foreclosure'
    WHEN loan_status LIKE '%Bankruptcy%'       THEN 'DQ120P'
         -- 同时设 bankruptcy_flag='Y'
    WHEN loan_status IN ('CUR', 'Current',
         '0-29')                              THEN 'Current'
    WHEN loan_status = '30-59'                THEN 'DQ30'
    WHEN loan_status = '60-89'                THEN 'DQ60'
    WHEN loan_status = '90-119'               THEN 'DQ90'
    WHEN loan_status = '120+'                 THEN 'DQ120P'
    ELSE days360_fallback(nextduedate)
END
```

#### `foreclosure_flag`（目标字段）
```sql
-- ✅ 双字段 OR 校验（最安全的实现方式，其他 Servicer 的参照模板）
CASE WHEN loan_status = 'Foreclosure' OR fcl_flag = 'Active'
     THEN 'Y' ELSE 'N' END
```

#### `lm_flag`（目标字段）
```sql
-- 来源：carrington.portcarrington.lm_flag 和 loan_status
CASE WHEN lm_flag = 'Active' OR loan_status = 'Loss Mitigation'
     THEN 'Y' ELSE 'N' END
```

#### `bankruptcy_flag`
```sql
CASE WHEN loan_status LIKE '%Bankruptcy%' THEN 'Y' ELSE 'N' END
```

#### 无法实现的字段（需向 Carrington 请求）
- `hold_flag` ❌ — 无字段
- `lm_type` ❌ — 无法区分 Forbearance vs Modification（`lm_flag` 只是 'Active'/'Inactive'）
- `lm_start_date` / `lm_end_date` ❌ — 无

---

### 3.4 Selene（日报，Step 3 待写）

**来源表**：`selene.portselenemain`（主日报）

> ⚠️ **当前状态**：ETL 中完全没有 Selene 的 Step 3 处理逻辑。以下是**应该实现的逻辑**。

#### `foreclosure_flag`（目标字段）
```sql
-- 来源：selene.portselenemain.foreclosure_status_code
-- DB 实测：'A' = Active FCL（41行）；'R' = Released（100行）；'' = 无 FCL
CASE WHEN foreclosure_status_code = 'A' THEN 'Y' ELSE 'N' END
```

#### `delinquency_status`（目标字段）
```sql
-- ⚠️ loan_status 无 'Foreclosure' 值，必须先用 foreclosure_status_code 覆盖
CASE
    WHEN foreclosure_status_code = 'A'     THEN 'Foreclosure'
    WHEN loan_status = 'Liquidated'        THEN 'PaidOff'
    -- loan_status 其他值（No Contact/In Contact/Lost Contact）无法映射到逾期级别
    -- 唯一可靠的逾期判断是 days360 兜底
    ELSE days360_fallback(nextduedate)
END
```

#### `lm_flag`（目标字段）
```sql
-- 来源：selene.portselenemain.lm_setup_date
CASE WHEN lm_setup_date IS NOT NULL THEN 'Y' ELSE 'N' END
```

#### 无法实现的字段（需向 Selene 请求）
- `lm_type` ❌ — 无
- `lm_end_date` ❌ — 无（关键：无法知道 LM 是否已到期）
- `hold_flag` ❌ — 无
- `bankruptcy_flag` ❌ — 无

---

### 3.5 MRC（日报，字段异常，待 MRC 确认）

**来源表**：`mrc.portmrcloan`（主日报）、`mrc.portmrcforeclosure`（FCL 专项，共 18 行）

> ❌ **当前状态**：两个关键字段均无效——`min_status` 始终为空字符串，`fc_flag` 从未为 'Y'。Step 3 也不存在。无法实现任何 FCL 判断。

#### 调查行动（实施前必须先确认）

| 问题 | 调查方式 |
|------|---------|
| `portmrcloan.min_status` 为何始终为空？ | 联系 MRC 确认；查询 `portmrcforeclosure` 其他字段（`fc_status`、`fc_milestone`）是否可替代 |
| `portmrcforeclosure.fc_flag` 为何从未激活？ | `referral_hold_reason` 字段已有止赎描述，确认 `fc_flag='Y'` 的触发条件 |
| 是否有替代逾期状态字段？ | 查询 `portmrcloan` 全字段清单，确认有无其他 DPD 或 status 字段 |

#### 当前可实现（仅作兜底）
```sql
-- 完全退化为 days360（无任何可靠状态字段）
days360_fallback(nextduedate)
```

#### `lm_flag`（部分可实现）
```sql
-- 来源：mrc.portmrcforbearance.status（专项表，无顶层标志）
-- 需通过 JOIN portmrcforbearance 才能判断
CASE WHEN portmrcforbearance.status IN ('Active', ...) THEN 'Y' ELSE 'N' END
```

---

### 3.6 Arvest（月报，无逾期状态字段）

**来源表**：`arvest.portarvestremitmonthlystatement`（月度贷款报表）

> ❌ **严重限制**：Arvest 月报中根本没有逾期状态字段。FCL 永远无法产生，所有 FCL 贷款均被误分类为 D120P。

#### 当前可实现（仅 DPD 兜底）
```sql
-- 完全退化为 days360
-- 来源：arvest.portarvestremitmonthlystatement.nextduedate
days360_fallback(nextduedate)
```

#### 向 Arvest 请求的字段清单（高优先级）
- `delinquency_status`（含 `'Foreclosure'` / `'REO'` 等）**或** `foreclosure_flag`（`Y/N`）
- `lm_flag` + `lm_type`（同批请求）

---

### 3.7 CapeCodFive（月报，值格式不匹配）

**来源表**：`capecodfive.portcapecodfive_monthly_servicing`（月度服务报告）

> ⚠️ **关键发现**：字段名为 `mba_delinquency_status`，但实际值是数字 DPD 字符串（`'29.0'`、`'60.0'`），而非文本状态码。FCL 文本匹配永远失败。

#### `delinquency_status`（DPD 数字值的转换方案）
```sql
-- 来源：capecodfive.portcapecodfive_monthly_servicing.mba_delinquency_status
-- 将数字字符串转换为分段逾期码（只能恢复 DPD，无法恢复 FCL/REO）
CASE
    WHEN TRY_CAST(mba_delinquency_status AS FLOAT) < 30   THEN 'Current'
    WHEN TRY_CAST(mba_delinquency_status AS FLOAT) < 60   THEN 'DQ30'
    WHEN TRY_CAST(mba_delinquency_status AS FLOAT) < 90   THEN 'DQ60'
    WHEN TRY_CAST(mba_delinquency_status AS FLOAT) < 120  THEN 'DQ90'
    WHEN TRY_CAST(mba_delinquency_status AS FLOAT) >= 120 THEN 'DQ120P'
    ELSE days360_fallback(next_payment_due_date)
END
-- ⚠️ 注意：此转换无法产生 'Foreclosure' / 'REO' 值
```

#### 向 CapeCodFive 请求的字段清单（P0 优先级）
- `delinquency_status`（文本型，含 `'Foreclosure'` / `'REO'`）**或** `foreclosure_flag`（`Y/N`）
- `lm_flag` + `lm_type`（同批请求）

---

### 3.8 FCI（日报 API，ETL 待实现）

**来源表**：`fci.portfciloanportfolio`（通过 GraphQL API 采集）

> ⚠️ **当前状态**：2,408 条 FCL 数据已在 MySQL 中，但完全未接入 ETL 判断流程。Step 3 不存在。

#### `delinquency_status` + `foreclosure_flag`（目标字段，待实现）
```sql
-- 来源：fci.portfciloanportfolio.status
-- ⚠️ 注：字段名是 status（小写），非 loanStatus
CASE status
    WHEN 'Paid off'       THEN 'PaidOff'
    WHEN 'Transfer out'   THEN 'PaidOff'
    WHEN 'Closed'         THEN 'PaidOff'
    WHEN 'REO'            THEN 'REO'
    WHEN 'Foreclosure'    THEN 'Foreclosure'
    WHEN 'Pre Foreclosure' THEN 'Foreclosure'  -- 确认业务含义
    WHEN 'Delinquency'    THEN days360_fallback(...)
    WHEN 'Performing'     THEN 'Current'
    WHEN 'Bankruptcy'     THEN 'DQ120P'        -- 同时设 bankruptcy_flag='Y'
    ELSE days360_fallback(...)
END

-- foreclosure_flag：
CASE WHEN status IN ('Foreclosure', 'Pre Foreclosure') THEN 'Y' ELSE 'N' END
```

#### `bankruptcy_flag`
```sql
CASE WHEN status = 'Bankruptcy' THEN 'Y' ELSE 'N' END
```

#### 无法实现的字段（需向 FCI 请求）
- `lm_flag` ❌ — FCI 数据中无 LM 字段
- `hold_flag` ❌ — 无

---

## Section 4: 补充说明

### Newrez `portnewrezfc` 完整可用字段参考

以下字段直接对应 doc 09 Group C/F 的目标字段，可在 ETL 中直接使用（无需向 Newrez 请求新字段）：

| doc 09 目标字段 | 来源字段（`newrez.portnewrezfc.*`） |
|---------------|----------------------------------|
| `foreclosure_flag` | `activefcflag`（1=Y, 0=N） |
| `foreclosure_stage` | `fcstage` / `lastfcstepcompleted` |
| `foreclosure_start_date` | `fcsetupdate` |
| `referral_date` | `fcreferraldate` |
| `sale_date_scheduled` | `fcscheduledsaledate` |
| `sale_date_actual` | `fcsalehelddate` |
| `fcl_exit_type` | `fcresults` |
| `hold_flag`（当前） | 推导自 hold1/2/3（见 Section 3.2） |
| `hold_reason`（当前） | 推导自 fchold1/2/3description（见 Section 3.2） |
| `hold_start_date` | 推导自 fchold1/2/3startdate（见 Section 3.2） |

> 这些字段是 Newrez **当前已提供**的，系统只需写 ETL 逻辑来读取和映射，无需向 Newrez 请求新字段。
