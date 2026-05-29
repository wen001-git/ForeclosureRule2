# 03 — 止赎状态生成逻辑：完整白盒分析

---

## 文档信息

| 项目 | 内容 |
|------|------|
| **文档目的** | 逐层详细解析系统如何从各服务商原始数据生成标准化止赎状态。本文档是整个文档库的核心，涵盖所有 SQL CASE-WHEN 逻辑、Python 转换、覆盖规则、手工修正机制。 |
| **解决的问题** | 止赎状态生成逻辑分布在 5+ 个配置文件中，跨越 5 个处理层次，本文档将其整合为可追溯的完整规则树。 |
| **覆盖范围** | Layer 1（原始状态）→ Layer 5（BPS 同步），止赎、逾期、REO、破产、损失缓解的状态生成全流程 |
| **系统归属** | `portdaily_config.py`, `gen_portmonth_config.py`, `daily_data_loan_common_clean_config.py` |

**目标读者：** 数据工程师 · 系统重写架构师 · 业务分析师 · 验证/对账工程师 · 新成员

**依赖文档：** `01_source_data.md`（字段来源）、`02_etl_pipeline.md`（管道结构）

**已知局限：**
- VASP 的具体覆盖触发条件未在代码中显式定义，基于 DB 实证推断
- `port.basic_data_loan_delinq_clean.delinq_source` 的分类标准未从代码中完全提取

**修订历史：**

| 日期 | 作者 | 版本 | 变更内容 |
|------|------|------|---------|
| 2026-05-21 | AI Agent (Claude Sonnet 4.6) | v1 | 初始版本，代码逆向 + Redshift DB 双重验证 |

---

## 1. 逻辑总览：五层规则栈

止赎状态经过以下 5 层处理，每层都可能覆盖上一层的结果：

```
┌─────────────────────────────────────────────────────────────┐
│  Layer 1 — 原始服务商状态                                    │
│  各服务商自己的字段（delinquency_status_mba / status 等）    │
│  ❌ 异构，不可直接跨服务商比较                               │
└──────────────────────┬──────────────────────────────────────┘
                       │  CASE-WHEN 映射（portdaily_config.py）
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  Layer 2 — 标准化 delinq 代码                               │
│  C / D30 / D60 / D90 / D120P / FCL / REO / P               │
│  ✅ 跨服务商可比，基于 days360 计算 + 状态优先级覆盖        │
└──────────────────────┬──────────────────────────────────────┘
                       │  GEN_PREVDELINQ（gen_portmonth_config.py）
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  Layer 3 — prevdelinq + 付款历史字符串                      │
│  确认逾期（D）、历史字符串（paymthistfull）                  │
│  ✅ 增加时序上下文，识别止赎后重入逾期的贷款                │
└──────────────────────┬──────────────────────────────────────┘
                       │  port.basic_data_loan_fix 手工覆盖
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  Layer 4 — 手工覆盖修正                                     │
│  basic_data_loan_fix（最高优先级，49条 delinq 覆盖）        │
│  ✅ 修正数据错误，权重高于所有自动逻辑                      │
└──────────────────────┬──────────────────────────────────────┘
                       │  FCL 详情表生成
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  Layer 5 — FCL 详情表体系（7张表）                          │
│  port.basic_data_loan_foreclosure / fcl / hold / bk / lm / related │
│  ✅ 精细化止赎阶段、暂停原因、合并 BK/LM 状态              │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Layer 1 → Layer 2：标准化 delinq 核心 CASE-WHEN 逻辑

**代码文件：** `portdaily_config.py`（Newrez 和 daily clean 层），`gen_portmonth_config.py`（Carrington、Interim 月度补充）

### 2.1 核心转换规则（所有服务商通用）

```sql
-- 标准 delinq 生成（优先级从高到低）
CASE
  -- 优先级 1：全额还清 / 完成还清
  WHEN svcdelinq IN ('Full Payoff', 'Paid in Full', 'Completed Payoff', 
                     'Completed Short Sale', 'Service Release')
    THEN 'P'

  -- 优先级 2：REO（银行接管房产）
  WHEN svcdelinq = 'REO'
    THEN 'REO'

  -- 优先级 3：止赎状态
  WHEN svcdelinq = 'Foreclosure'
    THEN 'FCL'
  WHEN svcdelinq IN ('Foreclosure / Perf BK', 'Foreclosure / Non-Perf BK')
    THEN 'FCL'   -- bankruptcy 字段另行设置为 'Y'

  -- Carrington 特殊编码（status 字段而非文字）
  WHEN status = 'F'          THEN 'FCL'
  WHEN status IN ('R','REO') THEN 'REO'
  WHEN status = 'P'          THEN 'P'

  -- 余额为零的特殊处理（Arvest/Capecodfive）
  WHEN balance = 0           THEN 'P'

  -- 余量：按 days360 计算逾期天数
  ELSE
    CASE
      WHEN days360(nextduedate, fctrdt) < 30  THEN 'C'
      WHEN days360(nextduedate, fctrdt) < 60  THEN 'D30'
      WHEN days360(nextduedate, fctrdt) < 90  THEN 'D60'
      WHEN days360(nextduedate, fctrdt) < 120 THEN 'D90'
      ELSE 'D120P'
    END
END AS delinq
```

**关键规则解析：**

| 规则 | 优先级 | 说明 |
|------|--------|------|
| 全额还清类关键词 | 最高 | 任何服务商的"还清"描述均映射为 `P` |
| REO 文字 | 次高 | 覆盖所有逾期天数计算 |
| FCL 文字 | 次高 | 即使 days360 < 30，也输出 `FCL` |
| Carrington `status='F'` | 次高 | Carrington 用单字符代替文字描述 |
| `balance=0` | 次高 | 兜底处理 Arvest/Capecodfive 历史数据 |
| `days360` 计算 | 最低 | 仅在所有优先级未匹配时使用 |

### 2.2 `days360` 函数说明

```
days360(nextduedate, fctrdt)
= 按每月30天计算 nextduedate 到 fctrdt 的天数差
= 衡量贷款"逾期多少天"的业务标准（与日历天数不同）
```

**逾期桶分界：**
- `< 30` → Current（`C`）
- `30-59` → `D30`（含30，不含60）
- `60-89` → `D60`
- `90-119` → `D90`
- `≥ 120` → `D120P`

### 2.3 fcl_flag / lm_flag / bankruptcy 辅助字段生成

这三个辅助字段与 `delinq` 相互独立，不参与 `delinq` 的计算：

| 辅助字段 | 生成规则 |
|---------|---------|
| `fcl_flag` | 来自服务商 FCL 活跃标志（见 2.4） |
| `lm_flag` | Newrez: `CASE WHEN activelmflag='1' THEN 'Y' ELSE 'N'` <br> Carrington: `CASE WHEN lm_flag='Active' THEN 'Y' ELSE 'N'` <br> SLS: 通过 `loss_mit_evaluation_status` 推断 |
| `bankruptcy` | Newrez: `CASE WHEN delinquency_status_mba LIKE '%Bankruptcy%' THEN 'Y' ELSE 'N'` <br> SLS: 来自 `bk_active_flag` |

### 2.4 fcl_flag 各服务商来源

| 服务商 | 原始字段 | 取值 |
|--------|---------|------|
| Newrez | `activefcflag` | `1`（Active）/ `0`（Inactive）|
| SLS | `fcl_active_flag` | `'1'`/`'0'` |
| Carrington | `foreclosure_status_code` | 原始文字代码 |
| MRC | `fc_flag` | 原始值 |
| Interim | 无独立 FCL 标志 | NULL |

---

## 3. Layer 2 → Layer 3：prevdelinq 与付款历史逻辑

**代码段：** `gen_portmonth_config.py` 中的 `GEN_PREVDELINQ` 常量

### 3.1 prevdelinq 计算（LAG 窗口函数）

```sql
-- Step 1: 计算上月 delinq
CREATE TABLE d.tmpportmonthprevdelinq AS
SELECT loanid, fctrdt,
       delinq,
       LAG(delinq) OVER (PARTITION BY loanid ORDER BY fctrdt) AS prevdelinq_svc,
       ...
FROM port.portmonthbase;

-- Step 2: 合并 BID 历史数据（弥补早期数据缺失）
UPDATE portmonthbase SET prevdelinq =
  COALESCE(p1.prevdelinq_svc, b.delinqgroup_new)
FROM d.tmpportmonthprevdelinq p1
LEFT JOIN d.tmpbiddelinq b ON p1.loanid = b.loanid;
```

### 3.2 付款历史字符串映射

```sql
-- delinq → 单字符 prevdelinqchar（用于拼接历史字符串）
CASE
  WHEN delinq = 'FCL'   THEN 'F'
  WHEN delinq = 'REO'   THEN 'R'
  WHEN delinq = 'P'     THEN 'P'
  WHEN delinq = 'D'     THEN 'D'
  WHEN delinq = 'C'     THEN '0'
  WHEN delinq = 'D30'   THEN '1'
  WHEN delinq = 'D60'   THEN '2'
  WHEN delinq = 'D90'   THEN '3'
  WHEN delinq = 'D120P' THEN '4'
  ELSE delinq
END AS prevdelinqchar
```

最终通过 `LISTAGG(prevdelinqchar, '') WITHIN GROUP (ORDER BY fctrdt DESC)` 生成 `paymthistfull`（最新在前的付款历史字符串）。

### 3.3 确认逾期规则（code = 'D'）

```sql
-- 特殊规则：前月为 FCL/REO/D120P 的贷款，本月如再次出现逾期，标记为确认逾期 'D'
UPDATE portmonthbase
SET delinq = 'D'
FROM (
  SELECT fctrdt, loanid
  FROM d.portmonthyilin1
  WHERE prevdelinq IN ('D120P', 'FCL', 'REO')
  AND delinq NOT IN ('C', 'P', 'REO', 'FCL')
) sub
WHERE portmonthbase.loanid = sub.loanid
  AND portmonthbase.fctrdt = sub.fctrdt;
```

**DB 验证：** `port.basic_data_monthly_loan_clean_data` 中有 273 条 `delinq='D'` 记录，证实此规则有效运行。

---

## 4. Layer 3 → Layer 4：手工覆盖（最高优先级）

**表：** `port.basic_data_loan_fix`  
**DB 验证：** 共有 13 个字段可被覆盖，其中 `delinq` 覆盖最多（49 条记录）

```sql
-- 覆盖逻辑
UPDATE port.portmonthbase a
SET delinq          = COALESCE(b.delinq, a.delinq),
    balance         = COALESCE(b.balance, a.balance),
    invbal          = COALESCE(b.invbal, a.invbal),
    escrowbal       = COALESCE(b.escrowbal, a.escrowbal),
    ...
FROM port.basic_data_loan_fix_clean b
WHERE a.loanid = b.loanid
  AND b.table_name = 'portmonthbase'
  AND a.fctrdt >= b.start_date
  AND a.fctrdt < b.end_date;
```

**`port.basic_data_loan_fix` 可覆盖字段（DB实证）：**

| 字段 | 覆盖记录数 |
|------|---------|
| `delinq` | 49 |
| `bpo` | 8 |
| `bpodate` | 8 |
| `balance` | 3 |
| `invbal` | 3 |
| `escrowbal` / `escrowadv` / `corpadvrec` / `corpadvnonrec` / `corpadvtotal` | 各1 |
| `deferredprin` / `deferredint` | 各1 |
| `agency` | 1 |

---

## 5. Layer 4：FCL 详情表体系（7张表）

这 7 张表不修改 `port.portmonthbase.delinq`，而是提供补充的止赎处理细节。

### 5.1 `port.basic_data_loan_fcl` — 核心止赎明细（61列）

关键字段组：

**基础标志：**
- `activefcflag`：活跃止赎（0/1）
- `judicial`：司法止赎类型
- `jr_sr_lien_flag`：高级/次级留置权标志

**里程碑日期（全流程）：**
`fcsetupdate` → `referral_start_date` → `legal_start_date` → `service_start_date` → `fcjudgment_hearing_scheduled` → `fcjudgment_end_date` → `fcscheduled_sale_date` → `fcsale_held_date`

**金额字段：**
- `fcbidamount`：止赎出价
- `fcapprbidprice`：批准出价金额
- `fcsaleamount`：拍卖成交金额

**结果字段：**
- `fcresults`：止赎结果（如 3rd Party Sale / Deed Acquired 等）
- `fcstage`：当前阶段
- `fcremovaldesc` / `fcremovaldate`：撤销原因和日期

**Hold 信息（4级，每级含4个字段）：**
```
fchold1description / fchold1startdate / fchold1enddate / fchold1projectedenddate / fchold1comment
fchold2description / fchold2startdate / fchold2enddate / fchold2projectedenddate / fchold2comment
fchold3description / fchold3startdate / fchold3enddate / fchold3projectedenddate / fchold3comment
fchold4description / fchold4startdate / fchold4enddate / fchold4projectedenddate / fchold4comment
```

### 5.2 `port.basic_data_loan_foreclosure_hold` — 结构化 Hold（17列）

**DB实证：30种 Hold 原因（描述类型）：**

| Hold 类型 | 记录数 | 业务含义 |
|----------|--------|---------|
| `Loss Mitigation Workout` | 58 | 损失缓解方案处理中 |
| `Service Delay` | 50 | 送达延迟 |
| `Client Document Execution` | 34 | 客户文件执行中 |
| `Awaiting Funds to Post` | 26 | 等待资金入账 |
| `Court Delay` | 23 | 法院延迟 |
| `ACT(PA) Letter/Demand Letter/NOI Expiration` | 17 | 催款/意向通知到期 |
| `Hearing Set` | 15 | 听证会已安排 |
| `Original Note` | 14 | 原始票据问题 |
| `Delinquency Review` | 13 | 逾期复查 |
| `Bankruptcy Filed` | 11 | 破产申请中 |
| `Mediation Hearing` | 12 | 调解听证 |
| `Note Possession Confirmation` | 12 | 票据持有确认 |
| `Title Resolution` | 9 | 产权问题处理 |
| `FEMA Hold` | 1 | FEMA 灾难暂停 |
| `Moratorium` | 1 | 暂停令（政府/法律） |

### 5.3 `port.basic_data_loan_foreclosure_bankruptcy` — FCL+BK（15列）

| 字段 | 含义 |
|------|------|
| `bankruptcy_status` | 破产状态 |
| `legal_status` | 法律状态 |
| `chapter` | 破产章节（7/11/13） |
| `lien_status` | 留置权状态 |
| `mfr_status` | 中止自动冻结状态 |
| `mfr_filed_date` | MFR 申请日期 |
| `claim_status` | 债权申请状态 |
| `proof_of_claim_date` | 债权证明日期 |
| `post_petition_due_date` | 申请后到期日 |

### 5.4 `port.basic_data_loan_foreclosure_loss_mitigation` — FCL+LM（16列）

| 字段 | 含义 |
|------|------|
| `deal` | LM 方案类型 |
| `program` | LM 具体项目 |
| `lmc_status` | LM 状态码 |
| `cycle_opened_date` | LM 周期开启日期 |
| `cycle_closed_date` | LM 周期关闭日期 |
| `final_disposition` | 最终处置结论 |
| `denialreason` | 拒绝原因 |
| `borrower_intentions` | 借款人意图 |
| `imminent_default` | 即将违约标志 |

### 5.5 `port.basic_data_fcl_related` — FCL 关联属性（14列）

| 字段 | 含义 |
|------|------|
| `delq_status` | 逾期状态（关联用） |
| `isloanlitigated` | 是否涉及诉讼 |
| `deactreason` | 账户停用原因 |
| `reasonfordefault` | 违约原因 |
| `inauctionflag` | 是否在拍卖中（int） |
| `liquidationdate` | 清算日期 |
| `liquidationtype` | 清算类型 |
| `liquidationproceeds` | 清算所得 |
| `bk_flag` | 破产标志 |
| `propertystate` | 房产所在州 |

### 5.6 `port.fcl_stage_info` — 阶段跟踪（48列）

详见 `02_etl_pipeline.md` 第 5.3 节。

6个阶段：`DEMAND` → `REFERRAL` → `FIRST_LEGAL` → `SERVICE` → `JUDGEMENT` → `SALE`

每个阶段跟踪：起止日期、实际天数、LM 天数（扣除）、Hold 天数（扣除）

---

## 6. 特殊状态码的生成机制

### 6.1 VASP（Vendee/Servicer Purchase）

**DB实证：** 19条记录，全部来自 Newrez，`svcdelinq` 为 `Current`（10条）、`180+ DPD`（8条）、`Foreclosure`（1条）

**推断机制：** VASP 是政府担保贷款的特殊处置状态（VA Vendee），由运营层或人工覆盖标记，非 CASE-WHEN 自动生成。疑似通过 `port.basic_data_loan_fix` 或专有配置写入。

### 6.2 REPUR（Repurchase）

**DB实证：** 1条记录，来自 Carrington，`svcdelinq='Loss Mitigation'`

**推断机制：** 贷款被回购，由服务商特定逻辑或人工标记。

### 6.3 D（确认逾期）

**DB实证：** 273条记录（`port.basic_data_monthly_loan_clean_data`）

**生成条件：** `prevdelinq IN ('D120P','FCL','REO')` 且本月仍在逾期中（非 C/P/REO/FCL）→ 标记为 `D`，表示"已确认为长期严重违约"

---

## 7. 完整规则优先级总结

```
最高优先级 ──────────────────────────────────── 最低优先级

[手工覆盖]    [特殊关键词]    [FCL/REO/P]    [days360计算]
 delinq_fix    'Full Payoff'   'Foreclosure'   < 30  → C
  (49条)       'Paid in Full'  'REO'           30-59 → D30
               balance=0       status='F'      60-89 → D60
               (Arvest)        status='R'      90-119→ D90
                                               ≥120  → D120P

                    ↓ 叠加（不覆盖 delinq）
               [辅助标志层]
               fcl_flag + lm_flag + bankruptcy

                    ↓ 时序上下文
               [prevdelinq层]
               D（确认逾期）/ VASP / REPUR
```

---

## 8. 状态生成执行状态监控

**表：** `port.sync_to_bps_status`

每次 FCL 相关表生成后，系统自动记录：

| 字段 | 含义 |
|------|------|
| `generate_type` | 操作名（如 GEN_FCL_DETAIL、CREATE_BASIC_DATA_FCL_HOLD） |
| `status` | `success` / `failure` |
| `servicer` | 服务商 |
| `max_generate_asofdate` | 最大数据日期 |
| `numofrows` | 处理记录数 |
| `excute_date` | 执行日期 |

---

## 对应英文版

英文版：`docs/en/03_fcl_status_logic.md`
