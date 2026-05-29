# 02 — ETL 管道分析：数据流与表谱系

---

## 文档信息

| 项目 | 内容 |
|------|------|
| **文档目的** | 完整描述 PrefectFlow 系统中止赎相关数据从原始摄入到下游报告的五层 ETL 管道，包括每层的关键表、转换逻辑触发点、以及 MySQL vs Redshift 的分层策略。 |
| **解决的问题** | 管道跨越 MySQL staging、Redshift analytics、BPS sync 三个平台，逻辑分散在多个配置文件中，本文档提供统一的全景视图。 |
| **覆盖范围** | Layer 0（原始数据）→ Layer 4（BPS 同步输出），止赎相关表的完整谱系 |
| **系统归属** | `PrefectFlow/flow/servicer_data/`、`flow/basic_data/`、`flow/servicer_business/`、`flow/bps/` |

**目标读者：** 数据工程师 · 系统重写架构师 · 调试/运营工程师 · 架构师

**依赖文档：** `01_source_data.md`（了解各层数据来源）

**相关文档：** `03_fcl_status_logic.md`（Layer 3 的逻辑细节）、`06_diagrams.md`（图表版）

**修订历史：**

| 日期 | 作者 | 版本 | 变更内容 |
|------|------|------|---------|
| 2026-05-21 | AI Agent (Claude Sonnet 4.6) | v1 | 初始版本，代码分析 + DB 实证 |
| 2026-05-28 | AI Agent (Claude Sonnet 4.6) | v2 | MCP 实证修正：(1) Layer 5 平台由 Redshift 更正为 MySQL（`port` + `bpms_dev` 两个 schema）；(2) 补充缺失的 `bpms_dev.sync_loan_foreclosure`（主 FCL BPS 表）；(3) `5-FORECLOSURE` 目标更正为 `port.basic_data_loan_foreclosure`（MySQL）；(4) Layer 3→4 补充 `basic_data_pool_config.py`；(5) 新增 `bpms_dev.biz_data_view_loan_details_foreclosure` |

---

## 1. 总体架构：五层管道

```
┌─────────────────────────────────────────────────────────────┐
│  Layer 0 — 原始数据源                                         │
│  S3 / SMB / SFTP → 各服务商文件                              │
└─────────────────┬───────────────────────────────────────────┘
                  │  Prefect 摄入 Flow（每日调度）
                  ▼
┌─────────────────────────────────────────────────────────────┐
│  Layer 1 — 服务商 Staging（MySQL）                           │
│  newrez.portshellpointfc/bk/lm/general                      │
│  sls.portfcldaily/portbkdaily/portlmdaily/portassetdaily     │
│  carrington.portcarrington                                   │
│  mrc.portmrcforeclosure | fci.* | selene.*                  │
└─────────────────┬───────────────────────────────────────────┘
                  │  portdaily_config.py（UNION ALL + 标准化）
                  ▼
┌─────────────────────────────────────────────────────────────┐
│  Layer 2 — 统一 Daily 层（Redshift）                         │
│  port.portdaily_v2                                          │
│  port.basic_data_daily_loan_common                          │
└─────────────────┬───────────────────────────────────────────┘
                  │  daily_data_loan_common_clean_config.py
                  ▼
┌─────────────────────────────────────────────────────────────┐
│  Layer 3 — Clean Daily 层（Redshift）                        │
│  port.basic_data_daily_loan_common_clean                    │
│  port.port_daily_clean                                      │
│  port.basic_data_loan_delinq_clean  ← 新增精细逾期表        │
└─────────────────┬───────────────────────────────────────────┘
                  │  gen_portmonth_config.py（月度聚合 + 业务规则）
                  │  basic_data_pool_config.py（FCL 业务表构建）
                  ▼
┌─────────────────────────────────────────────────────────────┐
│  Layer 4 — 月度业务层（Redshift）                            │
│  port.portmonthbase          ← 主分析表                     │
│  port.basic_data_loan_foreclosure   ← FCL 时间线           │
│  port.basic_data_loan_foreclosure_hold                      │
│  port.basic_data_loan_foreclosure_bankruptcy                │
│  port.basic_data_loan_foreclosure_loss_mitigation           │
│  port.basic_data_loan_fcl    ← FCL 详情（含 hold）         │
│  port.basic_data_fcl_related ← FCL 关联属性                │
│  port.fcl_stage_info         ← FCL 阶段跟踪                │
│  port.basic_data_loan_reo    ← REO 记录                    │
│  port.basic_data_monthly_loan_clean_data ← 月度 clean 数据 │
└─────────────────┬───────────────────────────────────────────┘
                  │  sync_to_bps_config.py（BPS 同步）
                  ▼
┌─────────────────────────────────────────────────────────────┐
│  Layer 5 — BPS 同步层（MySQL，两个 schema）                  │
│                                                             │
│  [MySQL port schema — ETL 直接同步目标]                     │
│  port.basic_data_loan_foreclosure  ← FCL 时间线（#5）      │
│  port.portmonth                    ← 月度基础数据（#1）     │
│                                                             │
│  [MySQL bpms_dev schema — BPS 应用层]                      │
│  bpms_dev.sync_portmonth                                    │
│  bpms_dev.sync_loan_foreclosure    ← FCL 主展示表          │
│  bpms_dev.sync_loan_foreclosure_loss_mitigation             │
│  bpms_dev.sync_loan_foreclosure_bankruptcy                  │
│  bpms_dev.sync_loan_foreclosure_hold                        │
│  bpms_dev.sync_fcl_stage_info                               │
│  bpms_dev.biz_data_view_loan_details_foreclosure ← BPS视图 │
│                                                             │
│  [Redshift port — 仅审计日志]                               │
│  port.sync_to_bps_status  ← 每次同步状态记录               │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Layer 0 → Layer 1：原始数据摄入

**触发方式：** Prefect 调度 Flow，每日自动执行  
**代码位置：** `flow/basic_data/load_monthly_raw_data.py`、各服务商摄入 Flow  
**数据格式：** CSV / TXT / XLSX → MySQL 表（按 `dataasof` 分区存储）

**摄入路径：**
| 服务商 | S3 路径 | MySQL Schema | 核心止赎表 |
|--------|---------|-------------|-----------|
| Newrez/Shellpoint | `s3://brigaws/shellpoint_new/` | `newrez` | `portshellpointfc`, `portshellpointbk`, `portshellpointlm` |
| SLS | `s3://brigaws/sls_new/` | `sls` | `portfcldaily`, `portbkdaily`, `portlmdaily`, `portassetdaily` |
| Carrington | `s3://brigaws/carrington_new/` | `carrington` | `portcarrington` |
| MRC | `s3://brigaws/mrc_new/` | `mrc` | `portmrcforeclosure` |
| FCI | `s3://brigaws/fci_new/` | `fci` | 按分类文件表 |
| Selene | `s3://brigaws/selene_new/` | `selene` | 按分类文件表 |

---

## 3. Layer 1 → Layer 2：统一 Daily 层

**代码文件：** `flow/servicer_data/sericer_data_config/portdaily_config.py`（60KB）

### 3.1 `port.portdaily_v2` 生成（关键：SLS/Newrez 切换处理）

```python
SLS_TO_NEWREZ_DATE = '2024-07-05'

GEN_PORTDAILY_v2 = '''
-- SLS 历史数据（2024-07-05 之前）
SELECT s.dataasofdate AS asofdate,
       s.account_number_investor AS loanid,
       'SLS' AS servicer,
       a.delq_status_mba AS delq_status,    ← SLS 已接近标准格式
       null AS fcl_flag,                    ← SLS 在此层不映射 fcl_flag
       null AS lm_flag,
       ...
FROM sls.portstandarddaily s, sls.portassetdaily a
WHERE s.dataasofdate < '2024-07-05'
UNION ALL
-- Newrez 数据（2024-07-05 之后）
SELECT p.dataasof AS asofdate,
       p.loanid,
       'Newrez' AS servicer,
       g.delinquency_status_mba AS delq_status,  ← Newrez 原始 MBA 状态
       null AS fcl_flag,
       CASE WHEN lm.activelmflag = '1' THEN 'Y' ELSE 'N' END AS lm_flag,
       ...
FROM newrez.portnewrezpmt p JOIN newrez.portnewrezgeneral g ...
'''
```

**注意点：**
- `port.portdaily_v2` 的 `fcl_flag` 对 SLS 和 Newrez **均为 null**，fcl_flag 在下层补充
- Carrington 的 `fcl_flag` 从 `foreclosure_status_code` 直接映射

### 3.2 `port.basic_data_daily_loan_common` 生成

**代码文件：** `flow/basic_data/transfer_daily_data_config/daily_data_loan_common_config.py`（47KB）

所有服务商（含 Carrington、MRC、FCI、Selene）的日度数据在此层 UNION 到统一 schema：

```sql
CREATE TABLE port.basic_data_daily_loan_common (
  ...
  delq_status VARCHAR(255),   ← 各服务商原始逾期描述
  fcl_flag    VARCHAR(50),    ← 各服务商止赎标志
  lm_flag     VARCHAR(1),     ← Y/N
  bankruptcy  VARCHAR(10),    ← Y/N
  ...
)
```

**各服务商 fcl_flag 映射：**
| 服务商 | 来源字段 | fcl_flag 值 |
|--------|---------|------------|
| Newrez | `activefcflag` | `1`/`0` |
| SLS | `fcl_active_flag` | `'1'`/`'0'` |
| Carrington | `foreclosure_status_code` | 原值传入 |
| MRC | `fc_flag` | 原值传入 |

---

## 4. Layer 2 → Layer 3：Clean Daily 层

**代码文件：** `flow/basic_data/transfer_daily_data_config/daily_data_loan_common_clean_config.py`（72KB）

**核心变换：** 将原始 `delq_status` 映射为标准化 `delinq` 代码

关键产出：
- `port.basic_data_daily_loan_common_clean`：标准化后的日度全量数据
- `port.port_daily_clean`：包含 `delinq`、`fcl_flag`、`lm_flag`、`bankruptcy` 等标准字段
- `port.basic_data_loan_delinq_clean`：精细逾期状态表（含 `delinq_source`、`ghost_reason`、`is_ghost_payoff`）

**`port.basic_data_loan_delinq_clean` 关键字段（DB实证）：**

| 字段 | 含义 |
|------|------|
| `delinq` | 标准化逾期状态（C/D30/.../FCL/REO/P/VASP/REPUR/D） |
| `ots_delinq` | OTS（贷储局）逾期分类 |
| `prevdelinq` | 上月逾期状态（LAG 计算） |
| `ots_prevdelinq` | OTS 上月逾期 |
| `delinq_source` | 逾期状态数据来源标识 |
| `is_ghost_payoff` | 是否为虚假还清（布尔值） |
| `ghost_reason` | 虚假还清原因 |
| `paymthist` | 付款历史字符串 |

---

## 5. Layer 3 → Layer 4：月度业务层（核心）

**代码文件：**
- `flow/servicer_business/sericer_business_data_config/gen_portmonth_config.py`（90KB）— `portmonthbase` 主分析表
- `flow/servicer_business/sericer_business_data_config/gen_portmonth_config_v4.py`（77KB）— 月度更新版
- `flow/basic_data/basic_data_config/basic_data_pool_config.py`（2,400+行）— **所有 FCL 业务表**（`basic_data_loan_foreclosure`、`basic_data_loan_fcl`、`fcl_stage_info` 等 7 张表）及 `GEN_FCL_STAGE` 阶段计算

### 5.1 `port.portmonthbase` 生成

`port.portmonthbase` 是系统的**主分析表**，月度快照，包含每个贷款每月的完整状态。

**数据来源 JOIN：**
```sql
CREATE TABLE port.portmonthbase AS
SELECT a.*,
       b.principalreceived, b.interestreceived, ...  -- 来自 basic_data_monthly_loan_remit_clean
FROM port.basic_data_daily_loan_common_clean a
LEFT JOIN port.basic_data_monthly_loan_remit_clean b ON a.fctrdt=b.fctrdt AND a.loanid=b.loanid
```

**止赎相关字段（DB实证，11个 distinct delinq 值）：**
| 字段 | 含义 | DB 总记录数 |
|------|------|------------|
| `delinq` | 标准化逾期状态 | 78,913 行 |
| `svcdelinq` | 服务商原始描述 | 44 个不同值 |
| `fctrdt` | 报告月份截止日 | 月度快照 |
| `lm_flag` | LM 标志 | — |

**portmonthbase 中 delinq 分布（DB实证）：**
| delinq | 记录数 | 占比 |
|--------|--------|------|
| `C` | 72,796 | 92.2% |
| `P` | 2,288 | 2.9% |
| `D30` | 2,274 | 2.9% |
| `D60` | 480 | 0.6% |
| `D120P` | 403 | 0.5% |
| `FCL` | 279 | 0.4% |
| `D90` | 206 | 0.3% |
| `NULL` | 155 | 0.2% |
| `VASP` | 19 | 0.02% |
| `REO` | 12 | 0.02% |
| `REPUR` | 1 | 0.001% |

### 5.2 FCL 相关 Layer 4 表

| 表名 | 记录数(近似) | 核心内容 |
|------|------------|---------|
| `port.basic_data_loan_foreclosure` | ~6K | FCL 完整时间线（23个里程碑日期 + 目标天数 + 方差 + 7种关闭原因） |
| `port.basic_data_loan_fcl` | — | FCL 详情 + 4个 Hold 描述（含预计结束日期、备注） |
| `port.basic_data_loan_foreclosure_hold` | — | 结构化 Hold（4级，含描述+起止日期） |
| `port.basic_data_loan_foreclosure_bankruptcy` | — | FCL+BK 联合视图（BK 状态、章节、MFR、债权申请） |
| `port.basic_data_loan_foreclosure_loss_mitigation` | — | FCL+LM 联合视图（16字段：方案、周期、最终处置） |
| `port.basic_data_fcl_related` | — | FCL 关联属性（诉讼标志、清算类型、BK 标志、违约原因） |
| `port.fcl_stage_info` | ~8,733 | FCL 阶段跟踪（6阶段 × 5维度：起止日期、阶段天数、LM天数、暂停天数） |
| `port.basic_data_loan_reo` | — | REO 简单记录（loanid + start_date + end_date） |

### 5.3 `port.fcl_stage_info` 阶段体系（DB实证）

**6个已确认阶段（按进程顺序）：**

| 阶段（stage） | 含义 | 记录数 |
|-------------|------|--------|
| `DEMAND` | 催款/意向通知 | 448 |
| `REFERRAL` | 转交律师 | 3,341 |
| `FIRST_LEGAL` | 首次法律行动 | 800 |
| `SERVICE` | 法律文件送达 | 1,486 |
| `JUDGEMENT` | 判决阶段 | 700 |
| `SALE` | 拍卖阶段 | 1,958 |

**阶段所属组（`group` 字段）：**
| group | 含义 | 记录数 |
|-------|------|--------|
| `FCL` | 已进入止赎的贷款 | 8,277 |
| `D120P` | 严重逾期（尚未正式 FCL 但已进入阶段跟踪） | 411 |
| `D90` | 90天逾期进入跟踪 | 39 |
| `REO` | 已进入 REO | 6 |

**每个阶段跟踪的5个维度：**
- `*_start_date` / `*_end_date`：阶段起止日期
- `*_stage_days`：阶段实际天数
- `*_in_lm_days`：阶段中处于 LM 状态的天数（扣除）
- `*_on_hold_days`：阶段中处于 Hold 状态的天数（扣除）

### 5.4 `port.basic_data_loan_foreclosure` 7种关闭原因（DB实证）

| `summary_foreclosure_status` | 含义 | 记录数 |
|------------------------------|------|--------|
| `Active Foreclosure` | 止赎进行中 | 43 |
| `Closed Foreclosure:Reinstated` | 关闭（已恢复还款） | 25 |
| `Closed Foreclosure:Loss Mitigation` | 关闭（进入损失缓解） | 15 |
| `Closed Foreclosure:Paid in Full` | 关闭（全额还清） | 10 |
| `Closed Foreclosure:Process Complete` | 关闭（流程完成，拍卖/REO） | 7 |
| `Closed Foreclosure:Deed in Lieu Cmplte` | 关闭（代物还款完成） | 1 |
| NULL | 未填写 | 5,942 |

---

## 6. Layer 4 → Layer 5：BPS 同步层

**代码文件：** `flow/bps/bps_config/sync_to_bps_config.py`

**同步表映射（MCP 实证，2026-05-28）：**
| 同步键 | Redshift 源表（Layer 4） | MySQL 目标表（Layer 5） | MCP 验证行数 |
|--------|------------------------|----------------------|------------|
| `1-PORTMONTH` | `port.portmonthbase` | `bpms_dev.sync_portmonth` | — |
| `5-FORECLOSURE` | `port.basic_data_loan_foreclosure` | `port.basic_data_loan_foreclosure`（MySQL） | 96 行（Newrez） |
| `8-FORECLOSURE_LM` | `port.basic_data_loan_foreclosure_loss_mitigation` | `bpms_dev.sync_loan_foreclosure_loss_mitigation` | — |
| `9-FORECLOSURE_BK` | `port.basic_data_loan_foreclosure_bankruptcy` | `bpms_dev.sync_loan_foreclosure_bankruptcy` | — |
| `10-FORECLOSURE_HOLD` | `port.basic_data_loan_foreclosure_hold` | `bpms_dev.sync_loan_foreclosure_hold` | — |
| `12-FCL_STAGE` | `port.fcl_stage_info` | `bpms_dev.sync_fcl_stage_info` | — |

**注意：** `bpms_dev.sync_loan_foreclosure` 是 `5-FORECLOSURE` 同步的**最终落地表**，经由两步写入：`sync_to_mysql()` 先将 Redshift 数据 clear+append 到 MySQL `port.basic_data_loan_foreclosure`（中转），随后 `update_to_mysql()` 执行 `UPDATE_FORECLOSURE`（`INSERT INTO bpms_dev.sync_loan_foreclosure ... SELECT FROM port.basic_data_loan_foreclosure ... ON DUPLICATE KEY UPDATE`）。`create_time`/`update_time` 全为 NULL 是因为 ON DUPLICATE KEY UPDATE 子句未包含这两列，非 ETL 绕过。数据字段与 `port` 中转表存在差异（dev 环境 ETL 未完整运行所致），见 doc 12 Section 14.0。

**执行状态日志：** 每次同步成功/失败都写入 Redshift `port.sync_to_bps_status`（含服务商、记录数、最大 asofdate）

---

## 7. MySQL vs Redshift 分层说明

| 层次 | 平台 | 原因 |
|------|------|------|
| Layer 1（Staging） | MySQL | 服务商数据多样、频率高，MySQL 易于增量写入 |
| Layer 2–4（Analytics） | Redshift | 大规模 SQL 计算、UNION ALL、窗口函数效率更高 |
| Layer 5（BPS Sync） | MySQL（两个 schema） | `port` schema 接收 ETL 直接同步目标；`bpms_dev` schema 是 BPS 应用层读取来源 |

**重要说明：** Layer 5 全部在 MySQL，Redshift 中无 `sync_*` 数据表。Redshift 的 `port.sync_to_bps_status` 仅为同步执行审计日志，不是数据表。

---

## 8. 关键数据日期字段说明

| 字段 | 含义 | 示例 |
|------|------|------|
| `asofdate` / `dataasofdate` | 原始数据日期 | 2025-01-15 |
| `fctrdt` | 报告截止日（月末次日） | 2025-02-01（代表1月数据） |
| `uploaddate` | 上传到系统的日期 | 2025-01-16 |
| `create_time` / `update_time` | 记录创建/更新时间（审计） | — |

---

## 对应英文版

英文版：`docs/en/02_etl_pipeline.md`
