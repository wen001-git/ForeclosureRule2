# 05 — 贷款属性 ↔ FCL 状态映射关系

---

## 文档信息

| 项目 | 内容 |
|------|------|
| **文档目的** | 系统性梳理所有影响 FCL/逾期状态生成的贷款属性字段，说明每个字段的决定权重、所在处理层、来源服务商，以及如何组合生成最终状态。 |
| **解决的问题** | 状态生成依赖多个字段的组合判断，单独看某个字段无法理解完整逻辑。本文档将字段的"输入角色"可视化，便于调试和重写。 |
| **覆盖范围** | 主要决定因素（直接生成 `delinq`）、辅助状态属性（填充 FCL 详情表）、手工覆盖字段 |
| **系统归属** | `portdaily_config.py`, `gen_portmonth_config.py`, `portmonth_config.py` |

**目标读者：** 数据工程师 · 系统重写架构师 · 验证/对账工程师 · 业务分析师

**依赖文档：** `01_source_data.md`（字段定义）、`03_fcl_status_logic.md`（生成逻辑）、`04_status_inventory.md`（状态代码）

**修订历史：**

| 日期 | 作者 | 版本 | 变更内容 |
|------|------|------|---------|
| 2026-05-21 | AI Agent (Claude Sonnet 4.6) | v1 | 初始版本，代码逆向 + DB 实证 |

---

## 1. 主要决定因素：直接影响 `delinq` 生成

### 1.1 优先级排序（从高到低）

```
优先级 1 ── 手工覆盖（最终修正）
  └── basic_data_loan_fix.delinq（有效期 start_date ≤ fctrdt < end_date）

优先级 2 ── 全额还清关键词（立即退出止赎流程）
  └── svcdelinq IN ('Full Payoff','Paid in Full','Completed Payoff',
                    'Completed Short Sale','Service Release')
  └── balance = 0（仅 Arvest/Capecodfive）

优先级 3 ── REO 状态
  └── svcdelinq = 'REO'
  └── status IN ('R','REO')  [Carrington]

优先级 4 ── 止赎状态
  └── svcdelinq = 'Foreclosure'
  └── svcdelinq IN ('Foreclosure / Perf BK','Foreclosure / Non-Perf BK')
  └── status = 'F'  [Carrington]

优先级 5 ── days360 逾期天数计算（兜底）
  └── days360(nextduedate, fctrdt) 分桶 → C/D30/D60/D90/D120P
```

### 1.2 主要决定字段详细说明

| 字段 | 类型 | 所在层 | 服务商 | 作用 |
|------|------|--------|--------|------|
| `port.basic_data_loan_fix.delinq` | VARCHAR | Layer 4（覆盖） | 所有（手工） | 最高优先级：直接覆盖所有自动生成的 delinq |
| `svcdelinq` | VARCHAR | Layer 1→2 | Newrez、Interim | 服务商原始逾期描述，含"Foreclosure"/"REO"/"Full Payoff"等 |
| `delinquency_status_mba` | VARCHAR | Layer 1→2 | Newrez（MySQL） | Newrez 特有 MBA 标准逾期描述（17种原始值） |
| `delq_status_mba` | VARCHAR | Layer 1→2 | SLS | SLS 的 MBA 逾期代码（已接近标准格式） |
| `status` | VARCHAR | Layer 1→2 | Carrington | Carrington 单字符状态：F/R/REO/P/其他 |
| `nextduedate` | DATE | Layer 2 | 所有 | 下次还款到期日：与 `fctrdt` 组合计算逾期天数 |
| `fctrdt` | DATE | Layer 2 | 所有 | 报表截止日（当月数据的次月1日）：days360计算基准 |
| `balance` | DECIMAL | Layer 2 | Arvest/Capecodfive | 贷款余额：余额=0 时强制设为 `P` |
| `prevdelinq` | VARCHAR | Layer 3 | 所有 | 上月状态：影响 `D`（确认逾期）的生成 |

---

## 2. 辅助属性：填充 FCL 详情表

这些字段不直接决定 `delinq`，但通过填充 7 张 FCL 详情表提供补充状态信息。

### 2.1 止赎详情属性

| 字段 | 来源服务商 | 源表 | 目标表 | 用途 |
|------|----------|------|-------|------|
| `activefcflag` / `fcl_active_flag` / `fc_flag` | Newrez/SLS/MRC | 服务商 MySQL | `port.basic_data_loan_foreclosure` | 活跃止赎标志 |
| `fcstage` / `fcl_current_status_desc` | Newrez/SLS | `portshellpointfc`/`portfcldaily` | `port.basic_data_loan_fcl`, `port.fcl_stage_info` | 当前止赎阶段 |
| `fcsetupdate` | Newrez | `portshellpointfc` | `port.basic_data_loan_fcl` | 止赎启动日期 |
| `fcreferraldate` / `fcl_referred_to_attorney_date` | Newrez/SLS | 服务商 FC 表 | `port.fcl_stage_info.referral_start_date` | 律师转介日期 |
| `firstlegaldate` / `fcl_first_legal_action_date` | Newrez/SLS | 服务商 FC 表 | `port.fcl_stage_info.legal_start_date` | 首次法律行动日期 |
| `servicecompletedate` / `fcl_service_complete_date` | Newrez/SLS | 服务商 FC 表 | `port.fcl_stage_info.service_start_date` | 文书送达完成日期 |
| `fcjudgmenthearingscheduled` / `fcl_judgement_entered_date` | Newrez/SLS | 服务商 FC 表 | `port.fcl_stage_info.judgement_start_date` | 判决日期 |
| `fcscheduledsaledate` / `fcl_sale_scheduled_date` | Newrez/SLS | 服务商 FC 表 | `port.fcl_stage_info.sale_start_date` | 计划拍卖日期 |
| `fcsalehelddate` / `fcl_sale_held_date` | Newrez/SLS | 服务商 FC 表 | `port.basic_data_loan_fcl` | 实际拍卖日期 |
| `fcresults` | Newrez | `portshellpointfc` | `port.basic_data_loan_fcl` | 止赎结果描述 |
| `fcremovaldesc` / `fcremovaldate` | Newrez | `portshellpointfc` | `port.basic_data_loan_fcl` | 撤销原因及日期 |
| `judicial` | Newrez | `portshellpointfc` | `port.basic_data_loan_fcl` | 是否司法止赎 |
| `daysinfc` / `fcl_days` | Newrez/SLS | 服务商 FC 表 | `port.basic_data_loan_foreclosure` | 在止赎中的天数 |
| `fcbidamount` / `fcsaleamount` | Newrez/SLS | 服务商 FC 表 | `port.basic_data_loan_fcl` | 出价/成交金额 |

### 2.2 Hold（暂停）属性

| 字段 | 来源 | 目标表 | 用途 |
|------|------|-------|------|
| `fchold1description` / `fchold2description` / ... | Newrez `portshellpointfc` | `port.basic_data_loan_foreclosure_hold`, `port.basic_data_loan_fcl` | 止赎暂停原因（最多4个） |
| `fchold1startdate` / `fchold1enddate` | Newrez | 同上 | 暂停起止日期 |
| `fchold1projectedenddate` | Newrez | 同上 | 预计结束日期 |
| `fchold1comment` | Newrez | 同上 | 暂停说明备注 |

**DB实证：** 30种不同 Hold 描述，`Loss Mitigation Workout`（58条）、`Service Delay`（50条）最常见。

### 2.3 破产（BK）属性

| 字段 | 来源服务商 | 源表 | 目标表 | 用途 |
|------|----------|------|-------|------|
| `activebkflag` / `bk_active_flag` | Newrez/SLS | BK 表 | `port.basic_data_loan_foreclosure_bankruptcy` | 活跃破产标志 |
| `bkstatus` | Newrez | `portshellpointbk` | 同上 | 破产状态码 |
| `bkchapter` / `bk_chapter_code` | Newrez/SLS | BK 表 | 同上 | 破产章节（7/11/13） |
| `bkfileddate` / `bk_filed_date` | Newrez/SLS | BK 表 | 同上 | 破产申请日期 |
| `mfrfileddate` / `mfrhearingdate` | Newrez | `portshellpointbk` | 同上 | MFR（解除自动冻结令）日期 |
| `bkcasenumber` | Newrez | `portshellpointbk` | 同上 | 破产案件编号 |

`bankruptcy` 辅助标志（Y/N）的生成：
- Newrez: `delinquency_status_mba LIKE '%Bankruptcy%'` → `'Y'`
- SLS: `bk_active_flag='1'` → `'Y'`

### 2.4 损失缓解（LM）属性

| 字段 | 来源服务商 | 源表 | 目标表 | 用途 |
|------|----------|------|-------|------|
| `activelmflag` | Newrez | `portshellpointlm` | `port.basic_data_loan_foreclosure_loss_mitigation` | 活跃 LM 标志 |
| `lmstatus` | Newrez | `portshellpointlm` | 同上 | LM 状态码 |
| `lmdeal` / `lmprogram` | Newrez | `portshellpointlm` | 同上 | LM 方案类型 |
| `loss_mit_evaluation_status` | SLS | `portlmdaily` | 同上 | SLS LM 评估状态 |
| `loss_mit_workout_type_code_desc` | SLS | `portlmdaily` | 同上 | SLS 方案类型描述 |
| `lm_flag` | Carrington | `portcarrington` | 同上 | Carrington LM 标志（`'Active'`=Y） |

`lm_flag` 辅助标志（Y/N）的生成：
- Newrez: `activelmflag='1'` → `'Y'`
- Carrington: `lm_flag='Active'` → `'Y'`
- SLS: 从 `loss_mit_evaluation_status` 推断

### 2.5 REO 和清算属性

| 字段 | 来源 | 目标表 | 用途 |
|------|------|-------|------|
| `reo_start_date` | SLS `portassetdaily` | `port.basic_data_loan_reo` | REO 开始日期 |
| `liquidationdate` / `liquidationtype` | Newrez/其他 | `port.basic_data_fcl_related` | 清算日期/类型 |
| `liquidationproceeds` | Newrez/其他 | `port.basic_data_fcl_related` | 清算所得 |
| `inauctionflag` | Newrez | `port.basic_data_fcl_related` | 是否在拍卖中 |

---

## 3. 字段组合决策矩阵

下表展示字段组合如何最终决定贷款状态：

| 场景 | 关键字段 | 最终 delinq | 最终辅助标志 |
|------|---------|------------|------------|
| 正常贷款 | `days360 < 30` | `C` | fcl_flag=0, lm_flag=N, bankruptcy=N |
| 轻度逾期 | `30 ≤ days360 < 60` | `D30` | fcl_flag=0 |
| 止赎中 | `svcdelinq='Foreclosure'` | `FCL` | fcl_flag=1 |
| 止赎+损失缓解 | `svcdelinq='Foreclosure'`, `activelmflag='1'` | `FCL` | fcl_flag=1, lm_flag=Y |
| 止赎+破产 | `svcdelinq='Foreclosure / Perf BK'` | `FCL` | fcl_flag=1, bankruptcy=Y |
| REO | `svcdelinq='REO'` 或 `status='R'` | `REO` | — |
| 全额还清 | `svcdelinq='Full Payoff'` | `P` | — |
| 余额清零 | `balance=0`（Arvest） | `P` | — |
| 确认逾期（重入） | `prevdelinq IN (FCL,REO,D120P)` + 仍逾期 | `D` | — |
| VASP（政府贷款） | 运营覆盖（Newrez） | `VASP` | — |
| 手工修正 | `port.basic_data_loan_fix` 有记录 | 覆盖任何自动值 | 覆盖范围最广 |

---

## 4. 字段权重总结图

```
贷款属性字段
    │
    ├── 必选（缺失则 delinq=NULL）
    │     ├── nextduedate    ← days360 基础
    │     └── fctrdt         ← days360 基础
    │
    ├── 状态决定（最高优先级）
    │     ├── svcdelinq / delinquency_status_mba / delq_status_mba / status
    │     │     └── 覆盖 days360 计算结果
    │     └── balance = 0   ← Arvest/Capecodfive 特例
    │
    ├── 手工覆盖（绝对最高优先级）
    │     └── basic_data_loan_fix.delinq
    │
    ├── 辅助标志（独立于 delinq，并列生成）
    │     ├── activefcflag / fcl_active_flag → fcl_flag
    │     ├── activelmflag / lm_flag         → lm_flag
    │     └── bk_active_flag / mbadelinq     → bankruptcy
    │
    └── 时序上下文（Layer 3 附加）
          └── prevdelinq（LAG）
                └── 触发 D（确认逾期）逻辑
```

---

## 5. 字段缺失/异常的处理

| 场景 | 字段 | 处理方式 | 结果 |
|------|------|---------|------|
| `nextduedate` 为 NULL | 不可计算 days360 | CASE-WHEN 其他分支兜底 | 可能为 NULL 或默认值 |
| `svcdelinq` 未匹配任何关键词 | 进入 ELSE 分支 | 用 days360 计算 | C/D30/D60/D90/D120P |
| SLS 历史数据（2024-07-05前） | portdaily_v2 的 UNION ALL 左侧 | 直接使用 SLS 字段 | 已接近标准格式 |
| Newrez 历史数据（2024-07-05后） | portdaily_v2 的 UNION ALL 右侧 | Newrez 字段映射 | 需要 CASE-WHEN 映射 |
| 服务商切换过渡期 | `SLS_TO_NEWREZ_DATE='2024-07-05'` | time-range UNION ALL | 两侧各取各的 |

---

## 对应英文版

英文版：`docs/en/05_loan_attribute_mapping.md`
