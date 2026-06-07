# 02 — ETL 管道分析：数据流与表谱系

> **命名说明（2024-07-05）：** 本文源表前缀现为 `portnewrez*`（此前为 `portshellpoint*`，Shellpoint 时期）；DB 实测 `newrez` schema 仅 `portnewrez*`，现役以此为准，改名史详见 doc 01。

---

## 文档信息

| 项目 | 内容 |
|------|------|
| **文档目的** | 完整描述 PrefectFlow 系统中止赎相关数据从原始摄入到下游报告的五层 ETL 管道，包括每层的关键表、转换逻辑触发点、以及 **MySQL + Redshift 双写策略**（§7，2026-06-06 code+MCP 更正）。 |
| **解决的问题** | 管道在 **L1–L4 双写 MySQL 与 Redshift**、L5 同步进 BPS（MySQL），逻辑分散在多个配置文件中，本文档提供统一的全景视图。 |
| **覆盖范围** | Layer 0（原始数据）→ Layer 4（BPS 同步输出），止赎相关表的完整谱系 |
| **系统归属** | `PrefectFlow/flow/servicer_data/`、`flow/basic_data/`、`flow/servicer_business/`、`flow/bps/` |

**目标读者：** 数据工程师 · 系统重写架构师 · 调试/运营工程师 · 架构师

**依赖文档：** `01_source_data.md`（了解各层数据来源）

**相关文档：** `03_fcl_status_logic.md`（Layer 3 的逻辑细节）、`06_diagrams.md`（图表版）

**修订历史：**

| 日期 | 作者 | 版本 | 变更内容 |
|------|------|------|---------|
| 2026-06-07 | AI Agent (Claude Opus 4.8) | v5 | 新增 **§8.1 as-of date 演变 + 为何 BPS `sync_*` 无 as-of、只有 `update_time`**（code + MCP 实证：DELETE+APPEND 覆盖刷新 `df_db_util.py:691,693`、两步 `UPDATE_FORECLOSURE`、`datediff` 实时校正吸收 as-of `asset_managment_config.py:597-598`；真实数据示例 loan 7727000088：368+2=370）；新增 **§9 各表取数验证 SQL（最新数据日期）**（as-of 列 information_schema 全量核验；同款 SQL 注入 fcl_pipeline.html 各节点抽屉）；§8.1 订正写入机制（主表 `bpms.sync_loan_foreclosure` 经 `UPDATE_FORECLOSURE` 的 `ON DUPLICATE KEY UPDATE` 写入，UPDATE 列表排除 create/update_time → NULL） | PrefectFlow 源码 + mysql_prod/redshift_prod 实测 |
| 2026-06-06 | AI Agent (Claude Opus 4.8) | v4 | **更正为 MySQL+Redshift 双写架构**（原"一层一平台"有误）：§1 图 + §2/§3/§4/§5 各层补"落库 DB+file:line"，**§7 重写为双写证据表** + §7.1 今天其它更正（两支线/days360/fcl_flag 非归一/Carrington 整列缺失/delinq_clean 生成代码不在仓库）；交叉链接 doc 20 §B.6 / doc 21 | PrefectFlow 源码 + mysql_prod/redshift 实测 |
| 2026-06-05 | AI Agent (Claude Opus 4.8) | v3 | 表名改正 `portshellpoint*`→`portnewrez*`（DB 实测 newrez 现役表，2024-07-05 改名）+ 加命名说明（DB 实测；doc 01） |
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
│  Layer 1 — 服务商 Staging（MySQL + Redshift 双写）           │
│  newrez.portnewrezfc/bk/lm/general                      │
│  sls.portfcldaily/portbkdaily/portlmdaily/portassetdaily     │
│  carrington.portcarrington                                   │
│  mrc.portmrcforeclosure | fci.* | selene.*                  │
└─────────────────┬───────────────────────────────────────────┘
                  │  portdaily_config.py（UNION ALL + 标准化）
                  ▼
┌─────────────────────────────────────────────────────────────┐
│  Layer 2 — 统一 Daily 层（Redshift + MySQL 双写）            │
│  port.portdaily_v2                                          │
│  port.basic_data_daily_loan_common                          │
└─────────────────┬───────────────────────────────────────────┘
                  │  daily_data_loan_common_clean_config.py
                  ▼
┌─────────────────────────────────────────────────────────────┐
│  Layer 3 — Clean Daily 层（Redshift + MySQL 双写）           │
│  port.basic_data_daily_loan_common_clean                    │
│  port.port_daily_clean                                      │
│  port.basic_data_loan_delinq_clean  ← 新增精细逾期表        │
└─────────────────┬───────────────────────────────────────────┘
                  │  gen_portmonth_config.py（月度聚合 + 业务规则）
                  │  basic_data_pool_config.py（FCL 业务表构建）
                  ▼
┌─────────────────────────────────────────────────────────────┐
│  Layer 4 — 月度业务层（月度双写; FCL业务族 RS建→L5同步）     │
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

> ⚠️ **双写架构更正（2026-06-06，code+MCP 实证）**：上图各层**不是"一层一平台"**——**L1–L4 同时写入 MySQL 与 Redshift 两套库**（同名表各一份）：plain 配置→Redshift、`mysql_` 前缀配置→MySQL，由各自 flow 分别构建。只有 **L4 的 FCL 业务族**（`basic_data_loan_foreclosure`/`fcl_stage_info`/`_hold`/`_loss_mitigation`/`_bankruptcy`）是 **Redshift 单建、再由 L5 同步进 MySQL**。逐层代码证据见 **§7**；落库证据表另见 [doc 20 §B.6](20_end_to_end_walkthrough.md)，字段级血缘见 [doc 21](21_fcl_field_lineage.md)。

---

## 2. Layer 0 → Layer 1：原始数据摄入

**触发方式：** Prefect 调度 Flow，每日自动执行  
**代码位置：** 各服务商摄入 Flow `flow/basic_data/load_daily_data_flow/load_daily_<servicer>_flow.py`  
**数据格式：** CSV / TXT / XLSX → 原始表（按 `dataasof` 分区存储）  
**落库：MySQL + Redshift 双写**（code 实证）——每家有两条 flow：`update_<svc>_daily_to_mysql(save_to_new=True)`→MySQL、`_to_redshift(save_to_new=False)`→Redshift（`load_daily_shellpoint_flow.py:9-47`）；分流 `servicer_task.py:158-163`；写库 `daily_task.py:923-942`(MySQL)/`960-983`(RS)。MCP 实测 `newrez.portnewrezfc` 两库都在。

**摄入路径：**
| 服务商 | S3 路径 | MySQL Schema | 核心止赎表 |
|--------|---------|-------------|-----------|
| Newrez/Shellpoint | `s3://brigaws/shellpoint_new/` | `newrez` | `portnewrezfc`, `portnewrezbk`, `portnewrezlm` |
| SLS | `s3://brigaws/sls_new/` | `sls` | `portfcldaily`, `portbkdaily`, `portlmdaily`, `portassetdaily` |
| Carrington | `s3://brigaws/carrington_new/` | `carrington` | `portcarrington` |
| MRC | `s3://brigaws/mrc_new/` | `mrc` | `portmrcforeclosure` |
| FCI | `s3://brigaws/fci_new/` | `fci` | 按分类文件表 |
| Selene | `s3://brigaws/selene_new/` | `selene` | 按分类文件表 |

---

## 3. Layer 1 → Layer 2：统一 Daily 层

**代码文件：** `flow/servicer_data/sericer_data_config/portdaily_config.py`（60KB）  
**落库：Redshift + MySQL 双写**——plain `daily_data_loan_common_config.py:5,97`→Redshift `port.basic_data_daily_loan_common`；`mysql_daily_data_loan_common_config.py:5,94`→MySQL 同名表；两条 flow `gen_daily_data_loan_common_flow.py:17-48(RS)/52-84(MySQL)`。

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
**落库：Redshift + MySQL 双写**——plain config→Redshift `port.basic_data_daily_loan_common_clean`；`mysql_daily_data_loan_common_clean_config.py`→MySQL 同名；两条 flow `gen_daily_data_loan_common_clean_flow.py:78-139(RS)/186-243(MySQL)`。

**核心变换：** 将原始 `delq_status` 映射为标准化 `delinq` 代码  
> 实测口径（见 doc 21 §5.4）：逐家一个 CASE，`Foreclosure*→FCL`/`REO→REO`/`Payoff*→P`，**其余一律 `days360(nextduedate, fctrdt)` 分档**（<30→C…≥120→D120P）。**`FCL` 是法律状态、不由天数推导**（`days360` 永不产 `FCL`，须 servicer 显式标注）。`delinq` 实测现存值 `C/D30/D60/D90/D120P/FCL/REO/P/VASP`（无 `REPUR`/独立 `D`）。

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

**落库（分两类，code 实证）：**
- **月度通用表 / `portmonthbase` = 双写**：`monthly_data_loan_common_config.py`(RS) + `mysql_monthly_data_loan_common_config.py`(MySQL)，flow `gen_monthly_data_loan_common_flow.py:24-30/78-84`；portmonthbase 由 `gen_portmonth_v4.py:45-46`(RS) + `gen_portmonth_mysql.py:42-43`(MySQL) 分别建。
- **FCL 业务族 = 仅 Redshift 构建**（`basic_data_pool_config.py`，目标 `{REDSHIFT_PORT}.`，无 `mysql_` 池配置）；其 **MySQL 副本由 Layer 5 同步**产生。MCP 实测 `port.basic_data_loan_foreclosure` 两库都在（RS 建 / MySQL 经 L5）。

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

## 7. MySQL ⇄ Redshift：双写架构（2026-06-06 code+MCP 实证，更正旧"一层一平台"说法）

> **更正**：早期本节认为"Layer 1=MySQL、Layer 2–4=Redshift、Layer 5=MySQL"（一层一平台）。读 PrefectFlow 源码 + MCP 实测后确认：**L1–L4 是 MySQL + Redshift 双写**（同名表在两套库各存一份），由 **plain 配置→Redshift、`mysql_` 前缀配置→MySQL** 两套 config/flow 分别构建；只有 **L4 的 FCL 业务族**是 Redshift 单建、再由 L5 同步进 MySQL。

**连接层判据**：`config/db_conn.py` 中 MySQL=`pymysql.connect`(:15-25)、Redshift=`redshift_connector.connect`(:26-34)；统一入口 `execute_sql(sql, DbTypeEnum.{MYSQL|REDSHIFT}.value, db)` 决定落哪库（`flow/__init__.py:19 REDSHIFT_PORT="port"`）。

| 层 | 落 MySQL? | 落 Redshift? | 代码证据（file:line） | MCP 实测 |
|---|---|---|---|---|
| **L1 原始落库** | ✅ | ✅ | 双 flow `load_daily_<svc>_flow.py:9-47`；分流 `servicer_task.py:158-163`；写库 `daily_task.py:923-942`(MySQL)/`960-983`(RS)；`MYSQL_DB_MAP servicer_config.py:374-387` | `newrez.portnewrezfc` 两库都在 |
| **L2 统一日表** | ✅ | ✅ | plain→RS `daily_data_loan_common_config.py:5,97`；`mysql_…:5,94`；flow `gen_daily_data_loan_common_flow.py:17-48(RS)/52-84(MySQL)` | `port.basic_data_daily_loan_common` 两库都在 |
| **L3 清洗日表** | ✅ | ✅ | `daily_data_loan_common_clean_config.py`(RS)/`mysql_…clean_config.py`(MySQL)；flow `gen_daily_data_loan_common_clean_flow.py:78-139/186-243` | `port.basic_data_daily_loan_common_clean` 两库都在 |
| **L4 月度通用 / portmonthbase** | ✅ | ✅ | `monthly_data_loan_common_config.py`(RS)/`mysql_monthly_…`(MySQL)；`gen_portmonth_v4.py:45-46`(RS)+`gen_portmonth_mysql.py:42-43`(MySQL) | RS 有 `portmonthbase`；MySQL 有 `basic_data_monthly_loan_common` |
| **L4 FCL 业务族**（foreclosure/stage/hold/lm/bk） | ⛔（由 L5 同步） | ✅（单建） | `basic_data_pool_config.py`（仅 `{REDSHIFT_PORT}.`，无 `mysql_` 池配置） | `port.basic_data_loan_foreclosure` 两库都在（MySQL 经 L5） |
| **L5 BPS 同步** | ✅（写） | ✅（读） | 读 RS `df_db_util.py:117-137`；写 MySQL `:665-699`/`:702-726`；`sync_asset_management.py` | `bpms.sync_*`、`port.basic_data_loan_foreclosure`(中转) |

**为什么双写（观察推断）**：Redshift 跑重分析 SQL（UNION ALL、窗口函数、days360）；MySQL 供 **BPS / 应用低延迟直查**。二者表名相同、各存一份。
> 落库证据表同源见 [doc 20 §B.6](20_end_to_end_walkthrough.md)；字段级血缘 + 业务理由见 [doc 21](21_fcl_field_lineage.md)。

**Layer 5 要点（保留）**：`sync_*` 数据表只在 MySQL（prod=`bpms`，dev=`bpms_dev`；及 `port` 中转）。Redshift 的 `port.sync_to_bps_status` 仅为同步执行审计日志，不是数据表。

### 7.1 今天补充的其它更正（code + MCP，与 doc 20/21 一致）

1. **两条支线**：止赎里程碑/状态走 **FCL 业务族支线**（直取 `portnewrezfc`/`portcarrington` → `basic_data_loan_fcl` → `basic_data_loan_foreclosure`/`fcl_stage_info`）；`delinq` 走**逾期支线**（`portnewrezgeneral.delinquency_status_mba` → `basic_data_daily_loan_common` → `_clean`）。两者在 `fcl_stage_info`（`group=delq_status`）汇合。
2. **L2 `fcl_flag` 非跨家归一**：该列在统一日表是**直传**（Newrez/SLS 恒 NULL），FCL 口径实际在 **L3 `delinq` CASE** 判定；真正跨家归一 `activefcflag` 的是 FCL 业务族支线（`basic_data_pool_config.py`），不在统一日表。
3. **`FCL` 是法律状态、不由天数推导**：`days360` 永不产 `FCL`（详见 §4 注与 doc 21 §5.4/§6）。
4. **Carrington 整列缺失（prod 实测）**：`timeline_first_legal_date`、`timeline_judgement_date`、`summary_judicial_foreclosure` 对 Carrington **全 NULL**（`portcarrington` 无对应源列）；跨 Servicer 差异见 doc 21 §6/§7。
5. **`basic_data_loan_delinq_clean`（含 `is_ghost_payoff/ghost_reason/delinq_source`）**：prod 实测列存在且有数据，但**生成代码在 PrefectFlow 版本库 grep 全仓 0 命中**（可能由另一 repo/手工流程维护）——被问到时如实说明，不臆断（doc 21 §9#7）。

---

## 8. 关键数据日期字段说明

| 字段 | 含义 | 示例 |
|------|------|------|
| `asofdate` / `dataasofdate` | 原始数据日期 | 2025-01-15 |
| `fctrdt` | 报告截止日（月末次日） | 2025-02-01（代表1月数据） |
| `uploaddate` | 上传到系统的日期 | 2025-01-16 |
| `create_time` / `update_time` | 记录创建/更新时间（审计） | — |

### 8.1 as-of date 的演变 + 为何 BPS `sync_*` 无 as-of、只有 `update_time`（code + MCP 实证）

**as-of（数据日期）在各层的演变：**

| 层 | as-of 列 | 含义 | 粒度 |
|---|---|---|---|
| L1 源 `newrez.portnewrez*` | `dataasof` | 每日快照日（原始表按此分区） | loanid+dataasof（1 行/贷款/天） |
| L2 `basic_data_daily_loan_common` | `asofdate` | 统一后的每日日期 | loanid+asofdate |
| L3 `basic_data_daily_loan_common_clean` | `fctrdt` | 报告截止日 | loanid+fctrdt |
| L4 `basic_data_loan_fcl` / `_foreclosure` | 取 `MAX(dataasof)` | 只保留每贷款最新快照 | 1 行/贷款（最新） |
| L4 `fcl_stage_info` | `fctrdt` | 月度阶段快照 | loanid+fctrdt |
| **L5 主表 `bpms.sync_loan_foreclosure`** | **无** | 当前态，只有审计列 | 1 行/贷款 |
| L5 `bpms.sync_fcl_stage_info` | **`fctrdt`（保留）** | 保留 as-of 历史 | loanid+fctrdt（多行/贷款） |

**MCP 实测列（mysql_prod）：**
- `bpms.sync_loan_foreclosure`：只有业务里程碑 `timeline_*_date` + 审计 `create_time`/`update_time`/`update_user`；**无 `asofdate`/`fctrdt`/`dataasof`**。`create_time`/`update_time` 默认 NULL、由 ETL 写（非 MySQL 自动，**值可能为 NULL**）。
- `bpms.sync_fcl_stage_info`：**有 `fctrdt`** + 各阶段日期 + `create_time`(CURRENT_TIMESTAMP)/`update_time`(on update，MySQL 自动维护)。

**写入机制（PrefectFlow code）——分两类：**
- ① **多数 `sync_*` 表**：由 `sync_to_mysql` **整表 `DELETE` + `to_sql(append)` 覆盖刷新**写入 bpms（`df_db_util.py:691,693`）。
- ② **主表 `bpms.sync_loan_foreclosure` 特殊（两步）**：先 `sync_to_mysql` 清空+追加 **port 中转**表 `port.basic_data_loan_foreclosure`（MySQL，`:675-676,691-693`），再由 `update_to_mysql` 跑 `UPDATE_FORECLOSURE`：`INSERT…SELECT…ON DUPLICATE KEY UPDATE` 写入 bpms（`:698,716`；SQL 在 `asset_managment_config.py`）。该 upsert 的 UPDATE 列表**不含 `create_time`/`update_time`** → 故二者保持 NULL（doc 12 §14.0）。
- `flow/bps/bps_config/asset_managment_config.py:535-608` `GEN_FORECLOSURE`：输出列**不含 `dataasof`**；天数 = 存储值 `+ datediff(day, a.dataasof, tempfc.current_date_new_york)`（`:597-598`；`current_date_new_york` = 运行日/纽约今天，`:536-538`）；过滤 `timeline_referred_to_foreclosure_date IS NOT NULL`（`:605`）。

**为何主表无 as-of、只有 `update_time`：**
1. **sync 主表是「当前态」表**：只取每贷款最新快照、再整表覆盖刷新，一行永远代表最新，单存 as-of 列冗余。
2. **as-of 历史留在上游**（L1 `dataasof` 每日快照可复现任意一天）；BPS 只需当前态。
3. **`create_time`/`update_time` 是审计列**（行何时被同步写），不是数据日期。
4. **主表天数实时重算到「运行日」**：`datediff(dataasof → 运行日)` 把 as-of 的差吸收进 `summary_days_in_fcl`，故表语义是「截至运行此刻」，单存一个冻结 as-of 反而误导。
5. **例外**：阶段表 `sync_fcl_stage_info` 按 `fctrdt` 保留多行历史（as-of 载体），只有主表坍缩成 1 行。

**真实数据示例（MCP 实测，loan `7727000088`，doc 19 Loan 1）：**

| 位置 | 字段 | 实测值 |
|---|---|---|
| Redshift `port.basic_data_loan_foreclosure`（源） | `dataasof` | **2026-06-04** |
| 同上 | `summary_days_in_fcl`（存储，截至 dataasof） | **368** |
| `bpms.sync_loan_foreclosure`（输出主表） | `summary_days_in_fcl` | **370** |
| 同上 | `dataasof` / `asofdate` / `fctrdt` | **无此列** |
| 同上 | `create_time` / `update_time` | **NULL** |
| `bpms.sync_fcl_stage_info` | `fctrdt`（多行，保留历史） | 2026-05-24、2026-05-23 … |
| 同上 | `update_time`（= BPS 运行日） | 2026-06-06 00:52:45 |

验证：`368 + datediff('2026-06-04' → 运行日 '2026-06-06') = 368 + 2 = 370` = 主表实测值。**那 2 天就是 as-of**，被 `datediff` 吸收进天数 → 故输出不再单存 as-of 列。复算 SQL（只读）：

```sql
-- 源（Redshift redshift_prod）
SELECT dataasof, summary_days_in_fcl FROM port.basic_data_loan_foreclosure WHERE loanid='7727000088';
-- 输出主表（MySQL mysql_prod.bpms）
SELECT summary_days_in_fcl, create_time, update_time FROM bpms.sync_loan_foreclosure WHERE loanid='7727000088';
-- 阶段表保留 fctrdt 历史
SELECT loanid, fctrdt, update_time FROM bpms.sync_fcl_stage_info WHERE loanid='7727000088' ORDER BY fctrdt DESC;
```

---

## 9. 各表取数验证 SQL（最新数据日期）

> 想在库里看某表数据时直接复制运行。as-of 列已用 `information_schema` 全量实测核验。验证库：**L1=`mysql_prod`**、**L2–L4=`redshift_prod`**、**L5=`mysql_prod.bpms`**。无数据日期列者按 `loanid`/`update_time` 取（已注明）。`LIMIT 50` 可自行调整。

### L1 源（mysql_prod）
| 表 | 最新数据日期取数 SQL |
|---|---|
| `newrez.portnewrezfc`（`bk/lm/general/prop` 换表名同理，均 `dataasof`） | `SELECT * FROM newrez.portnewrezfc WHERE dataasof=(SELECT MAX(dataasof) FROM newrez.portnewrezfc) LIMIT 50;` |
| `sls.portassetdaily`（历史；`portfcldaily/bk/lm` 用 `uploaddate`） | `SELECT * FROM sls.portassetdaily WHERE dataasofdate=(SELECT MAX(dataasofdate) FROM sls.portassetdaily) LIMIT 50;` |
| `carrington.portcarrington`（**无数据日期列**） | `SELECT * FROM carrington.portcarrington ORDER BY update_time DESC LIMIT 50;` |
| `mrc.portmrcforeclosure` | `SELECT * FROM mrc.portmrcforeclosure WHERE dataasof=(SELECT MAX(dataasof) FROM mrc.portmrcforeclosure) LIMIT 50;` |
| `newrez.portnewrezdatadic`（字典，无日期） | `SELECT * FROM newrez.portnewrezdatadic LIMIT 100;` |

### L2–L3 逾期支线（redshift_prod）
| 表 | 最新数据日期取数 SQL |
|---|---|
| `port.portdaily_v2` | `SELECT * FROM port.portdaily_v2 WHERE asofdate=(SELECT MAX(asofdate) FROM port.portdaily_v2) LIMIT 50;` |
| `port.basic_data_daily_loan_common` | `SELECT * FROM port.basic_data_daily_loan_common WHERE asofdate=(SELECT MAX(asofdate) FROM port.basic_data_daily_loan_common) LIMIT 50;` |
| `port.basic_data_daily_loan_common_clean` | `SELECT * FROM port.basic_data_daily_loan_common_clean WHERE fctrdt=(SELECT MAX(fctrdt) FROM port.basic_data_daily_loan_common_clean) LIMIT 50;` |
| `port.port_daily_clean` | `SELECT * FROM port.port_daily_clean WHERE fctrdt=(SELECT MAX(fctrdt) FROM port.port_daily_clean) LIMIT 50;` |
| `port.basic_data_loan_delinq_clean` | `SELECT * FROM port.basic_data_loan_delinq_clean WHERE fctrdt=(SELECT MAX(fctrdt) FROM port.basic_data_loan_delinq_clean) LIMIT 50;` |

### L4 月度 / FCL 业务族（redshift_prod）
| 表 | 最新数据日期取数 SQL |
|---|---|
| `port.portmonthbase` | `SELECT * FROM port.portmonthbase WHERE fctrdt=(SELECT MAX(fctrdt) FROM port.portmonthbase) LIMIT 50;` |
| `tempfc.temp_basic_data_fcl` | `SELECT * FROM tempfc.temp_basic_data_fcl WHERE dataasof=(SELECT MAX(dataasof) FROM tempfc.temp_basic_data_fcl) LIMIT 50;` |
| `port.basic_data_loan_fcl` | `SELECT * FROM port.basic_data_loan_fcl WHERE dataasof=(SELECT MAX(dataasof) FROM port.basic_data_loan_fcl) LIMIT 50;` |
| `port.basic_data_loan_foreclosure` | `SELECT * FROM port.basic_data_loan_foreclosure WHERE dataasof=(SELECT MAX(dataasof) FROM port.basic_data_loan_foreclosure) LIMIT 50;` |
| `port.basic_data_fcl_related` | `SELECT * FROM port.basic_data_fcl_related WHERE dataasof=(SELECT MAX(dataasof) FROM port.basic_data_fcl_related) LIMIT 50;` |
| `port.fcl_stage_info` | `SELECT * FROM port.fcl_stage_info WHERE fctrdt=(SELECT MAX(fctrdt) FROM port.fcl_stage_info) LIMIT 50;` |
| `port.basic_data_loan_foreclosure_hold`（一贷款多行） | `SELECT * FROM port.basic_data_loan_foreclosure_hold WHERE dataasof=(SELECT MAX(dataasof) FROM port.basic_data_loan_foreclosure_hold) LIMIT 50;` |
| `port.basic_data_loan_foreclosure_loss_mitigation` | `SELECT * FROM port.basic_data_loan_foreclosure_loss_mitigation WHERE dataasof=(SELECT MAX(dataasof) FROM port.basic_data_loan_foreclosure_loss_mitigation) LIMIT 50;` |
| `port.basic_data_loan_foreclosure_bankruptcy` | `SELECT * FROM port.basic_data_loan_foreclosure_bankruptcy WHERE dataasof=(SELECT MAX(dataasof) FROM port.basic_data_loan_foreclosure_bankruptcy) LIMIT 50;` |
| `port.portfunding`（**无数据日期列**，维度） | `SELECT * FROM port.portfunding WHERE loanid='7727000088';` |
| `port.basic_data_loan_reo`（**无数据日期列**） | `SELECT * FROM port.basic_data_loan_reo WHERE loanid='7727000088';` |

### L5 BPS 直接对接（mysql_prod.bpms）
| 表 | 最新数据日期取数 SQL |
|---|---|
| `bpms.sync_loan_foreclosure`（**无数据日期列**，当前态 1 行/贷款） | `SELECT * FROM bpms.sync_loan_foreclosure WHERE loanid='7727000088';` |
| `bpms.sync_fcl_stage_info` | `SELECT * FROM bpms.sync_fcl_stage_info WHERE fctrdt=(SELECT MAX(fctrdt) FROM bpms.sync_fcl_stage_info) LIMIT 50;` |
| `bpms.sync_loan_foreclosure_hold` | `SELECT * FROM bpms.sync_loan_foreclosure_hold WHERE fctrdt=(SELECT MAX(fctrdt) FROM bpms.sync_loan_foreclosure_hold) LIMIT 50;` |
| `bpms.sync_loan_foreclosure_loss_mitigation` | `SELECT * FROM bpms.sync_loan_foreclosure_loss_mitigation WHERE fctrdt=(SELECT MAX(fctrdt) FROM bpms.sync_loan_foreclosure_loss_mitigation) LIMIT 50;` |
| `bpms.sync_loan_foreclosure_bankruptcy` | `SELECT * FROM bpms.sync_loan_foreclosure_bankruptcy WHERE fctrdt=(SELECT MAX(fctrdt) FROM bpms.sync_loan_foreclosure_bankruptcy) LIMIT 50;` |
| `bpms.biz_data_view_loan_details_foreclosure`（视图） | `SELECT * FROM bpms.biz_data_view_loan_details_foreclosure WHERE fctrdt=(SELECT MAX(fctrdt) FROM bpms.biz_data_view_loan_details_foreclosure) LIMIT 50;` |
| `port.basic_data_loan_foreclosure`（MySQL 中转，**无数据日期列**） | `SELECT * FROM port.basic_data_loan_foreclosure WHERE loanid='7727000088';` |

> 同款 SQL 已注入 `outputs/fcl_pipeline.html` Pipeline 视图每个节点抽屉（点节点即见）。

---

## 对应英文版

英文版：`docs/en/02_etl_pipeline.md`
