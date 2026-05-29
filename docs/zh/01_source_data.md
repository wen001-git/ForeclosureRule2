# 01 — 源数据分析：止赎相关原始数据

---

## 文档信息

| 项目 | 内容 |
|------|------|
| **文档目的** | 全面梳理 PrefectFlow 系统中各服务商的原始数据表结构，聚焦止赎（FCL）、破产（BK）、损失缓解（LM）相关字段，为 ETL 管道分析和状态生成逻辑提供数据来源依据。 |
| **解决的问题** | 各服务商数据格式和字段命名高度异构，本文档统一梳理，消除字段理解歧义。新增各字段的取值范围、计算逻辑、DB实证统计，直接可用于验证和系统重写。 |
| **覆盖范围** | Newrez/Shellpoint、SLS、Carrington、MRC、FCI、Selene 六个服务商的原始 MySQL staging 表 |
| **系统归属** | `PrefectFlow/statistics_script/` DDL 文件 + `PrefectFlow/flow/servicer_data/` 配置 |

**目标读者：** 数据工程师 · 验证/对账工程师 · 系统重写架构师 · 新成员

**依赖文档：** 无（本文档是所有其他文档的数据基础）

**已知局限：**
- MRC 表目前只有17条记录（全为当月数据），fc_status/fc_milestone 等字段均为 NULL
- SLS 数据截止 2024-08-07（SLS 于 2024-07-05 切换为 Newrez，此后不再更新）
- Carrington 原始文档中的 `status` / `foreclosure_status_code` 字段不存在；实际字段为 `loan_status` 和 `fcl_flag`

**修订历史：**

| 日期 | 作者 | 版本 | 变更内容 | 数据验证 |
|------|------|------|---------|---------|
| 2026-05-21 | AI Agent (Claude Sonnet 4.6) | v1 | 初始版本，基于代码逆向 + Redshift DB 实证 | 已通过 Redshift dev 验证 |
| 2026-05-21 | AI Agent (Claude Sonnet 4.6) | v2 | 新增：DB/Schema标注、表描述、字段取值范围/计算逻辑/值举例/统计信息/FCL相关 | MySQL prod 直接查询验证 |

---

## 数据库连接信息

所有表均在 **MySQL** 实例中（Azure 托管）：

| 属性 | 值 |
|------|---|
| **主机** | `bridg004-db-prod.mysql.database.azure.com` |
| **端口** | `3306` |
| **用户** | `brgdev` |
| **认证** | SSL 必需 |

| 服务商 | MySQL Schema | 主要表 |
|--------|-------------|--------|
| Newrez / Shellpoint | `newrez` | `portnewrezfc`, `portnewrezbk`, `portnewrezlm`, `portnewrezgeneral` |
| SLS | `sls` | `portassetdaily`, `portfcldaily`, `portbkdaily`, `portlmdaily` |
| Carrington | `carrington` | `portcarrington` |
| MRC | `mrc` | `portmrcforeclosure` |
| FCI | `fci` | 按文件类别分表 |
| Selene | `selene` | 按文件类别分表 |

> **命名变更说明：** 2024-07-05 前，Newrez 服务商对应的表前缀为 `portshellpoint*`（Shellpoint 时期）；切换后改为 `portnewrez*`。DDL 文件 `shellpoint_daily.sql` 为历史文件，现役表以 `portnewrez*` 为准。

---

## 1. 数据摄入架构概览

```
外部数据源（S3 / SMB / SFTP）
    │
    ├── s3://brigaws/shellpoint_new/      → newrez schema (MySQL)
    ├── s3://brigaws/sls_new/             → sls schema (MySQL)
    ├── s3://brigaws/carrington_new/      → carrington schema (MySQL)
    ├── s3://brigaws/mrc_new/             → mrc schema (MySQL)
    ├── s3://brigaws/fci_new/             → fci schema (MySQL)
    └── s3://brigaws/selene_new/          → selene schema (MySQL)
```

每个服务商数据以独立的 MySQL Schema 存储，**按日上传**，每次数据包含数据日期字段（字段名因服务商而异，见各表说明）。

---

## 2. Newrez / Shellpoint（`newrez` schema）

**数据库：** MySQL（`bridg004-db-prod`）  
**Schema：** `newrez`  
**数据文件格式：** `.csv`  
**表前缀：** `portnewrez*`（历史：`portshellpoint*`）  
**DDL 参考：** `statistics_script/shellpoint_daily.sql`（历史名称，现役表已改名）  
**数据时间范围：** 2023-12-14 ~ 2026-05-19（持续更新）

---

### 2.1 `portnewrezfc` — 止赎详情表（原 `portshellpointfc`）

**表描述：** 止赎流程全生命周期跟踪表。记录每笔贷款的止赎启动、各阶段里程碑日期（转介→首次法律行动→送达→判决→计划拍卖→实际拍卖）、暂停原因（最多4层）及止赎结果。每笔贷款每个数据日期一行。

**全限定名：** `newrez.portnewrezfc`｜**总行数：** 1,553,268

**Part A — 字段定义**

| 字段名 | 类型 | 含义 | 取值范围 | 计算逻辑 | FCL相关 |
|--------|------|------|---------|---------|--------|
| `loanid` | varchar(255) | 贷款 ID（Bridger 内部主键） | 非空字符串，10位数字为主 | 原始摄入（Bridger 分配） | ✅ 主要 |
| `dataasof` | date | 数据日期（每日快照） | 2023-12-14 ~ 2026-05-19 | 原始摄入 | — |
| `activefcflag` | int | **活跃止赎标志** | {0, 1}，0=Inactive，1=Active，无NULL | 原始摄入 → `portdaily_config.py` 映射为 `fcl_flag` | ✅ 主要 |
| `fcstage` | varchar(255) | **当前止赎阶段**描述 | 65种文字描述 + NULL | 原始摄入（服务商跟踪） → 流入 `port.fcl_stage_info.stage` | ✅ 主要 |
| `fcsetupdate` | date | 止赎启动日期 | 2018-08-15 ~ 2026-05-18，或 NULL | 原始摄入（服务商批准止赎时填写） | ✅ 主要 |
| `fcreferraldate` | date | 委托律师转介日期 | 2018-08-15 ~ 2026-05-18，或 NULL | 原始摄入 → 流入 `port.fcl_stage_info.referral_start_date` | ✅ 主要 |
| `firstlegaldate` | date | 首次法律行动日期 | 2018-10-29 ~ 2026-05-18，或 NULL | 原始摄入 → 流入 `port.fcl_stage_info.legal_start_date` | ✅ 主要 |
| `servicecompletedate` | date | 法律文书送达完成日期 | 2018-12-10 ~ 2026-02-16，或 NULL | 原始摄入 → 流入 `port.fcl_stage_info.service_start_date` | ✅ 主要 |
| `fcjudgmenthearingscheduled` | date | 判决听证预定日期 | 2020-01-22 ~ 2026-08-21，或 NULL | 原始摄入 → 流入 `port.fcl_stage_info.judgement_start_date` | ✅ 主要 |
| `fcjudgmententered` | date | 判决生效日期 | 2025-01-10 ~ 2026-04-09，或 NULL | 原始摄入 | ✅ 主要 |
| `fcscheduledsaledate` | date | 计划拍卖日期 | 2023-09-14 ~ 2026-07-14，或 NULL | 原始摄入 → 流入 `port.fcl_stage_info.sale_start_date` | ✅ 主要 |
| `fcsalehelddate` | date | 实际拍卖执行日期 | 2025-05-27 ~ 2026-05-15，或 NULL | 原始摄入 → 流入 `port.basic_data_loan_fcl` | ✅ 主要 |
| `fcsaleamount` | decimal(32,16) | 拍卖成交金额（美元） | $90,001 ~ $400,000，或 NULL | 原始摄入（拍卖结果） | ✅ 辅助 |
| `fcresults` | varchar(255) | 止赎结果描述 | {"3rd Party", "REO"}，或 NULL | 原始摄入 → 流入 `port.basic_data_loan_fcl.fcresults` | ✅ 主要 |
| `fchold1description` | varchar(255) | **止赎暂停原因1** | 38种文字描述，或 NULL | 原始摄入 → 流入 `port.basic_data_loan_foreclosure_hold` | ✅ 主要 |
| `fchold1startdate` | date | 暂停1开始日期 | 2019-11-21 ~ 2026-05-19，或 NULL | 原始摄入 | ✅ 主要 |
| `fchold1enddate` | date | 暂停1结束日期 | 2019-11-27 ~ 2026-05-14，或 NULL | 原始摄入 | ✅ 主要 |
| `fchold2description` | varchar(255) | **止赎暂停原因2** | 36种文字描述，或 NULL | 原始摄入 → 流入 `port.basic_data_loan_foreclosure_hold` | ✅ 主要 |
| `fchold2startdate` | date | 暂停2开始日期 | 2019-11-21 ~ 2026-05-19，或 NULL | 原始摄入 | ✅ 主要 |
| `fchold2enddate` | date | 暂停2结束日期 | 2019-11-27 ~ 2026-05-14，或 NULL | 原始摄入 | ✅ 主要 |
| `judicial` | int | 司法止赎类型标志 | {0, 1}，0=Non-Judicial，1=Judicial | 原始摄入 → 流入 `port.basic_data_loan_fcl.judicial` | ✅ 辅助 |
| `fcbidamount` | decimal(32,16) | 止赎出价金额（美元） | $90,000 ~ $543,306，或 NULL | 原始摄入（参与方报价） | ✅ 辅助 |
| `daysinfc` | int | 贷款在止赎流程中的天数 | 1 ~ 803，或 NULL | 原始摄入（服务商计算：`fcsetupdate → dataasof` 天数） | ✅ 主要 |
| `fcremovaldesc` | varchar(255) | 止赎撤销原因描述 | {"Reinstated","Loss Mitigation","Paid in Full","Process Complete","Deed in Lieu Cmplte","3rd Party"}，或 NULL | 原始摄入 → 映射为 `summary_foreclosure_status` | ✅ 主要 |
| `fcremovaldate` | date | 止赎撤销日期 | 2019-11-27 ~ 2026-05-18，或 NULL | 原始摄入 | ✅ 主要 |

**Part B — 字段统计**

| 字段名 | 值举例 | 统计信息 |
|--------|--------|---------|
| `loanid` | "0671496644", "9799754446" | 共1,553,268行 · NULL率0% · 7,370个唯一贷款 |
| `dataasof` | 2024-01-15, 2026-05-19 | 共1,553,268行 · NULL率0% · 880个不同日期（每日一批） |
| `activefcflag` | 0, 1 | 共1,553,268行 · NULL率0% · 0(1,539,831=99.1%), 1(13,437=0.9%) |
| `fcstage` | "Pre-Sale Review 1 (SCRA and PACER Check)", "Complaint Sent for Filing" | 共1,553,268行 · NULL率97.9% · 非NULL: 32,841行·65种·前5: Pre-Sale Review 1(3,840), Preliminary Title Clear(2,746), NOS Sent for Recording(2,663), Complaint Sent for Filing(2,589) |
| `fcsetupdate` | 2024-07-04, 2025-02-03 | 共1,553,268行 · NULL率97.9% · 非NULL: 32,968行·84个日期·最早2018-08-15·最新2026-05-18 |
| `fcreferraldate` | 2022-09-13, 2021-05-27 | 共1,553,268行 · NULL率97.9% · 非NULL: 32,968行·93个日期·范围2018-08-15~2026-05-18 |
| `firstlegaldate` | 2022-10-27, 2024-03-29 | 共1,553,268行 · NULL率98.9% · 非NULL: 16,466行·53个日期·范围2018-10-29~2026-05-18 |
| `servicecompletedate` | 2024-04-01, 2024-11-26 | 共1,553,268行 · NULL率99.6% · 非NULL: 6,787行·22个日期 |
| `fcjudgmenthearingscheduled` | 2025-09-16, 2025-10-15 | 共1,553,268行 · NULL率99.8% · 非NULL: 2,909行·24个日期·范围2020-01-22~2026-08-21 |
| `fcjudgmententered` | 2025-01-10, 2025-08-13 | 共1,553,268行 · NULL率99.9% · 非NULL: 1,833行·11个日期 |
| `fcscheduledsaledate` | 2025-06-05, 2025-05-16 | 共1,553,268行 · NULL率99.7% · 非NULL: 4,035行·52个日期·范围2023-09-14~2026-07-14 |
| `fcsalehelddate` | 2025-10-14, 2025-11-04 | 共1,553,268行 · NULL率99.9% · 非NULL: 895行·9个日期·范围2025-05-27~2026-05-15 |
| `fcsaleamount` | 274000, 357200, 400000 | 共1,553,268行 · NULL率99.9% · 非NULL: 1,251行·9种金额·$90,001~$400,000 |
| `fcresults` | "3rd Party", "REO" | 共1,553,268行 · NULL率99.9% · 2种结果 |
| `fchold1description` | "Loss Mitigation Workout", "Awaiting Funds to Post", "Service Delay" | 共1,553,268行 · NULL率98.1% · 38种描述·前5: Loss Mitigation Workout(9,147), Awaiting Funds to Post(7,141), Service Delay(2,010), Court Delay(1,467) |
| `fchold1startdate` | 2024-04-07, 2022-11-16 | 共1,553,268行 · NULL率98.1% · 非NULL: 29,941行·250个日期 |
| `fchold1enddate` | 2024-04-12, 2022-11-25 | 共1,553,268行 · NULL率98.6% · 非NULL: 22,080行·191个日期 |
| `fchold2description` | "Loss Mitigation Workout", "ACT(PA) Letter/Demand Letter/NOI Expiration" | 共1,553,268行 · NULL率98.5% · 36种描述 |
| `fchold2startdate` | 2024-02-23, 2022-11-08 | 共1,553,268行 · NULL率98.5% · 非NULL: 22,934行·205个日期 |
| `fchold2enddate` | 2023-06-05, 2022-11-25 | 共1,553,268行 · NULL率98.6% · 非NULL: 22,357行·196个日期 |
| `judicial` | 0, 1 | 共1,553,268行 · NULL率97.9% · 1(16,601=50.4%), 0(16,367=49.6%) — 司法/非司法各半 |
| `fcbidamount` | 154591.01, 231285.22, 271278.01 | 共1,553,268行 · NULL率99.8% · 非NULL: 2,545行·20种金额·$90,000~$543,306 |
| `daysinfc` | 63, 83, 36 | 共1,553,268行 · NULL率97.9% · 非NULL: 32,968行·803个不同值·范围1~803天 |
| `fcremovaldesc` | "Reinstated", "Loss Mitigation", "Paid in Full" | 共1,553,268行 · NULL率98.7% · 非NULL: 19,809行·6种描述 |
| `fcremovaldate` | 2024-04-11, 2022-11-25 | 共1,553,268行 · NULL率98.7% · 非NULL: 19,809行·73个日期·范围2019-11-27~2026-05-18 |

---

### 2.2 `portnewrezbk` — 破产详情表（原 `portshellpointbk`）

**表描述：** 破产流程跟踪表，记录每笔贷款的破产申请日期、章节类型（7/11/13）、各关键事件日期（撤销/解除/驳回/MFR）及破产阶段。每笔贷款每个数据日期一行。

**全限定名：** `newrez.portnewrezbk`｜**总行数：** 1,553,268

**Part A — 字段定义**

| 字段名 | 类型 | 含义 | 取值范围 | 计算逻辑 | FCL相关 |
|--------|------|------|---------|---------|--------|
| `loanid` | varchar(255) | 贷款 ID | 同 portnewrezfc | 原始摄入 | ✅ 辅助 |
| `dataasof` | date | 数据日期 | 2023-12-14 ~ 2026-05-19 | 原始摄入 | — |
| `activebkflag` | int | **活跃破产标志** | {0, 1}，无NULL | 原始摄入 → `CASE WHEN delinquency_status_mba LIKE '%Bankruptcy%' THEN 'Y'` 用于生成 `bankruptcy` 辅助字段 | ✅ 辅助 |
| `bkstatus` | int | 破产状态码 | {1,2,3,4,5}（服务商编码）或 NULL | 原始摄入（服务商定义码值） | ✅ 辅助 |
| `bkchapter` | int | 破产章节 | {7, 11, 13} 或 NULL | 原始摄入 → 流入 `port.basic_data_loan_foreclosure_bankruptcy.chapter` | ✅ 辅助 |
| `bkfileddate` | date | 破产申请日期 | 2008-06-16 ~ 2026-04-27，或 NULL | 原始摄入 → 流入 `port.basic_data_loan_foreclosure_bankruptcy` | ✅ 辅助 |
| `bkremovaldate` | date | 破产撤销/结案日期 | 2009-09-18 ~ 2026-04-14，或 NULL | 原始摄入 | ✅ 辅助 |
| `dischargeddate` | date | 破产解除日期 | 2009-09-18 ~ 2026-01-08，或 NULL | 原始摄入 | ✅ 辅助 |
| `dismisseddate` | date | 破产驳回日期 | 2022-09-30 ~ 2026-04-14，或 NULL | 原始摄入 | ✅ 辅助 |
| `mfrfileddate` | date | 解除自动冻结申请日期 | 2025-06-10 ~ 2026-04-29，或 NULL | 原始摄入 → 流入 `port.basic_data_loan_foreclosure_bankruptcy.mfr_filed_date` | ✅ 辅助 |
| `mfrhearingdate` | date | 解除冻结听证日期 | 2025-06-24 ~ 2026-05-15，或 NULL | 原始摄入 | ✅ 辅助 |
| `bkcasenumber` | varchar(255) | 破产案件编号 | 法院分配的文字编号，或 NULL | 原始摄入 | — |

**Part B — 字段统计**

| 字段名 | 值举例 | 统计信息 |
|--------|--------|---------|
| `activebkflag` | 0, 1 | 共1,553,268行 · NULL率0% · 0(1,547,862=99.7%), 1(5,406=0.3%) |
| `bkstatus` | 1, 2, 3 | 共1,553,268行 · NULL率99.0% · 5种码值 · 2(8,033=52%), 1(5,353=34%), 3(882=6%) |
| `bkchapter` | 7, 11, 13 | 共1,553,268行 · NULL率99.0% · 3种 · 13(7,345=47%), 7(5,619=36%), 11(2,667=17%) |
| `bkfileddate` | 2010-06-03, 2024-02-09 | 共1,553,268行 · NULL率99.0% · 34个日期 · 范围2008-06-16~2026-04-27 |
| `bkremovaldate` | 2014-09-24, 2024-04-11 | 共1,553,268行 · NULL率99.4% · 23个日期 |
| `dischargeddate` | 2014-09-24, 2015-04-17 | 共1,553,268行 · NULL率99.4% · 13个日期 |
| `dismisseddate` | 2022-09-30, 2025-05-08 | 共1,553,268行 · NULL率99.9% · 5个日期 |
| `mfrfileddate` | 2025-06-10, 2025-11-04 | 共1,553,268行 · NULL率99.9% · 5个日期 |
| `mfrhearingdate` | 2025-06-24, 2025-12-02 | 共1,553,268行 · NULL率99.9% · 4个日期 |
| `bkcasenumber` | "1033613", "981704" | 共1,553,268行 · NULL率99.0% · 33个唯一案件号 |

---

### 2.3 `portnewrezlm` — 损失缓解详情表（原 `portshellpointlm`）

**表描述：** 损失缓解（LM）流程跟踪表。记录每笔贷款的LM活跃状态、方案类型（Deal/Program 均为整数编码）、以及三大LM子流程（Forbearance宽限、Trial试行还款、Repayment还款计划）的各自状态。每笔贷款每个数据日期一行。

**全限定名：** `newrez.portnewrezlm`｜**总行数：** 1,553,268

**Part A — 字段定义**

| 字段名 | 类型 | 含义 | 取值范围 | 计算逻辑 | FCL相关 |
|--------|------|------|---------|---------|--------|
| `loanid` | varchar(255) | 贷款 ID | 同前 | 原始摄入 | ✅ 辅助 |
| `dataasof` | date | 数据日期 | 2023-12-14 ~ 2026-05-19 | 原始摄入 | — |
| `activelmflag` | int | **活跃LM标志** | {0, 1}，无NULL | 原始摄入 → `CASE WHEN activelmflag='1' THEN 'Y' ELSE 'N'` 生成 `lm_flag` | ✅ 主要 |
| `lmstatus` | int | LM当前状态码 | 5 ~ 202（43种整数码）或 NULL | 原始摄入（服务商内部编码，需查码表） | ✅ 辅助 |
| `lmdeal` | int | LM方案大类代码 | 1 ~ 11（8种）或 NULL | 原始摄入 → 流入 `port.basic_data_loan_foreclosure_loss_mitigation.deal` | ✅ 辅助 |
| `lmprogram` | int | LM具体项目代码 | 8 ~ 531（35种）或 NULL | 原始摄入 → 流入 `port.basic_data_loan_foreclosure_loss_mitigation.program` | ✅ 辅助 |
| `forbearancestatus` | int | 宽限协议状态码 | {1, 4, 6} 或 NULL | 原始摄入（服务商内部编码） | ✅ 辅助 |
| `trialstatus` | int | 试行还款状态码 | {1, 4, 7, 8} 或 NULL | 原始摄入 | ✅ 辅助 |
| `repaymentstatus` | int | 还款计划状态码 | {1, 4, 5, 6, 7, ?} 或 NULL | 原始摄入 | ✅ 辅助 |

**Part B — 字段统计**

| 字段名 | 值举例 | 统计信息 |
|--------|--------|---------|
| `activelmflag` | 0, 1 | 共1,553,268行 · NULL率0% · 0(1,531,996=98.6%), 1(21,272=1.4%) |
| `lmstatus` | 166, 112, 5, 20 | 共1,553,268行 · NULL率93.3% · 43种码 · 166(39,483=38%), 112(16,398=16%), 5(11,604=11%) |
| `lmdeal` | 2, 1, 11, 5 | 共1,553,268行 · NULL率93.3% · 8种 · 2(37,445=36%), 1(30,962=30%), 11(13,461=13%) |
| `lmprogram` | 21, 73, 12, 29 | 共1,553,268行 · NULL率93.3% · 35种 · 21(37,412=36%), 73(13,461=13%) |
| `forbearancestatus` | 4, 1, 6 | 共1,553,268行 · NULL率99.2% · 3种 · 4(10,193=83%), 1(2,067=17%), 6(2) |
| `trialstatus` | 8, 1, 4 | 共1,553,268行 · NULL率99.4% · 4种 · 8(7,110=71%), 1(2,239=22%), 4(675=7%) |
| `repaymentstatus` | 5, 1, 7 | 共1,553,268行 · NULL率99.4% · 6种 · 5(4,401=48%), 1(2,043=22%), 7(1,876=20%) |

---

### 2.4 `portnewrezgeneral` — 贷款通用信息表（原 `portshellpointgeneral`）

**表描述：** 贷款通用状态快照，最关键字段是 `delinquency_status_mba`（MBA标准逾期描述）—— 该字段是 ETL 生成标准化 `delinq` 代码的主要输入。该字段并非原始文件字段，而是在数据摄入代码中额外补充填写的（DDL注释："这个字段在excel文档中没有呢，代码中自己补充进去的"）。

**全限定名：** `newrez.portnewrezgeneral`｜**总行数：** 1,553,258

**Part A — 字段定义**

| 字段名 | 类型 | 含义 | 取值范围 | 计算逻辑 | FCL相关 |
|--------|------|------|---------|---------|--------|
| `loanid` | varchar(255) | 贷款 ID | 同前 | 原始摄入 | ✅ 主要 |
| `dataasof` | date | 数据日期 | 2023-12-14 ~ 2026-05-19 | 原始摄入 | — |
| `delinquency_status_mba` | varchar(50) | **MBA标准逾期状态描述**（核心字段） | 18种文字描述，无NULL | 原始摄入（Newrez提供） → `portdaily_config.py` CASE-WHEN 映射为 `delinq`（C/D30/.../FCL/REO/P） | ✅ 主要 |
| `mbadelinquency` | int | MBA逾期数字桶编码 | 1 ~ 19（18种），无NULL | 原始摄入（与 `delinquency_status_mba` 一一对应）| ✅ 辅助 |
| `legalstatus` | varchar(255) | 法律状态代码 | {"FCBU","BK13","BK7","BK7DCH",...} 14种 + NULL | 原始摄入 → 流入 `port.basic_data_loan_fcl.legalstatus` | ✅ 辅助 |
| `reasonfordefault` | varchar(255) | 违约原因描述 | 29种文字描述，或 NULL | 原始摄入 → 流入 `port.basic_data_fcl_related.reasonfordefault` | ✅ 辅助 |

**Part B — 字段统计**

| 字段名 | 值举例 | 统计信息 |
|--------|--------|---------|
| `delinquency_status_mba` | "Current", "1-29 DPD", "Full Payoff", "Foreclosure" | 共1,553,258行 · NULL率0% · 18种 · Current(1,085,990=69.9%), 1-29 DPD(256,528=16.5%), Full Payoff(149,690=9.6%), 30-59 DPD(21,616=1.4%), Foreclosure(12,573=0.8%) |
| `mbadelinquency` | 1, 2, 15, 3, 13 | 共1,553,258行 · NULL率0% · 18种数字 · 1(1,085,990=69.9%), 2(256,528=16.5%), 15(149,690=9.6%) |
| `legalstatus` | "FCBU", "BK13", "BK7", "REOSLD" | 共1,553,258行 · NULL率98.1% · 14种 · FCBU(13,679=53%), BK13(4,312=16%), BK7(1,769=7%) |
| `reasonfordefault` | "Curtailment of Income", "Business Failure" | 共1,553,258行 · NULL率97.8% · 29种描述 |

**`delinquency_status_mba` → `delinq` 完整映射表（18种原始值）：**

| 原始值 | 标准 `delinq` | 备注 |
|-------|--------------|------|
| `Current` | `C`（或 `VASP`*） | VASP 为特殊覆盖，19条 |
| `1-29 DPD` | `D30` | days360 < 30 时也可能为C，此处服务商已判断 |
| `30-59 DPD` | `D30` | |
| `60-89 DPD` | `D60` | |
| `90-119 DPD` | `D90` | |
| `120-149 DPD` | `D120P` | |
| `180+ DPD` | `D120P` | |
| `Foreclosure` | `FCL` | activefcflag=1 |
| `Foreclosure / Perf BK` | `FCL` | bankruptcy='Y' |
| `Foreclosure / Non-Perf BK` | `FCL` | bankruptcy='Y' |
| `REO` | `REO` | |
| `Full Payoff` | `P` | |
| `Paid in Full` | `P` | |
| `Completed Short Sale` | `P` | |
| `Service Release` | `P` | |
| `Loss Mitigation` | days360计算 | lm_flag='Y' |
| `Performing Bankruptcy` | days360计算 | bankruptcy='Y' |
| `Non-Performing Bankruptcy` | days360计算 | bankruptcy='Y' |

---

## 3. SLS（`sls` schema）

**数据库：** MySQL（`bridg004-db-prod`）  
**Schema：** `sls`  
**数据文件格式：** `.txt`  
**服务商有效期：** ≤ 2024-07-05（此后切换为 Newrez）  
**DDL 参考：** `statistics_script/sls_daily.sql`  
**数据时间范围：** 2023-02-22 ~ 2024-08-07

> **注意：** SLS 是 Shellpoint/Newrez 之前的主要服务商。2024-07-05 后停止更新，历史数据保留。SLS 各分表的贷款ID字段为 `account_number`，日期字段名因表而异（`dataasofdate` 或 `data_as_of_date`）。

---

### 3.1 `portassetdaily` — 资产日报摘要表

**表描述：** 贷款组合日报总览表，包含 MBA 逾期状态（接近标准格式）、FCL/BK/REO/宽限活跃标志。是 SLS 数据中最重要的状态来源表，等同于 Newrez 的 `portnewrezgeneral`。

**全限定名：** `sls.portassetdaily`｜**总行数：** 240,608  
**贷款ID字段：** `account_number_investor`（varchar）  
**日期字段：** `dataasofdate`（date，2023-02-22 ~ 2024-08-07）  
**唯一贷款数：** 790

**Part A — 字段定义**

| 字段名 | 类型 | 含义 | 取值范围 | 计算逻辑 | FCL相关 |
|--------|------|------|---------|---------|--------|
| `account_number_investor` | varchar(32) | 贷款ID（SLS内部） | 790个唯一值，无NULL | 原始摄入，通过 `port.portidmap` 映射为 `loanid` | ✅ 主要 |
| `dataasofdate` | date | 数据日期 | 2023-02-22 ~ 2024-08-07 | 原始摄入 | — |
| `delq_status_mba` | varchar(50) | **MBA逾期状态**（主要状态字段） | 8种文字描述，无NULL | 原始摄入，已接近标准格式 → 轻映射为 `delinq` | ✅ 主要 |
| `mba_delq_status_paystring` | varchar(255) | MBA付款历史字符串（24个月） | 最长24位，字符集包含C/D/数字 | 原始摄入（每月一个字符拼接） → 参考生成 `paymthistfull` | ✅ 辅助 |
| `fcl_active_flag` | varchar(1) | **活跃止赎标志** | {"N", "Y"}，无NULL | 原始摄入 → 映射为 `fcl_flag` | ✅ 主要 |
| `fc_hold_flag` | varchar(4) | 止赎暂停标志 | {"N   ", "Y   "}（含尾随空格），无NULL | 原始摄入（注意尾随空格需trim） | ✅ 辅助 |
| `bk_active_flag` | varchar(1) | 活跃破产标志 | {"Y", "N", ""}，NULL率0.65% | 原始摄入 → 参考生成 `bankruptcy` | ✅ 辅助 |
| `bk_chapter_code` | varchar | 破产章节代码 | {"07", "13", "11", ""}，NULL率0.65% | 原始摄入 | ✅ 辅助 |
| `reo_start_date` | date | REO开始日期 | 全部为NULL（240,608行均为NULL） | 原始摄入（当前数据集无REO记录） | — |
| `forbearance_flag` | varchar | 宽限标志 | {"N", "Y"}，无NULL | 原始摄入 → 参考生成 `lm_flag` | ✅ 辅助 |
| `modification_type` | varchar | 贷款修改类型 | {"", "NON-HAMP"}，NULL率0.64% | 原始摄入 | ✅ 辅助 |

**Part B — 字段统计**

| 字段名 | 值举例 | 统计信息 |
|--------|--------|---------|
| `delq_status_mba` | "Current", "DQ 30", "Service Release" | 共240,608行 · NULL率0% · 8种 · Current(158,272=65.8%), DQ 30(46,575=19.4%), Service Release(19,377=8.1%), Paid in Full(5,497=2.3%), DQ 60(4,800=2.0%) |
| `mba_delq_status_paystring` | "CCCCCCCC", "777777..." | 共240,608行 · NULL率0% · 1,082种唯一字符串 |
| `fcl_active_flag` | "N", "Y" | 共240,608行 · NULL率0% · N(240,072=99.8%), Y(536=0.2%) |
| `fc_hold_flag` | "N   ", "Y   " | 共240,608行 · NULL率0% · N(240,467=99.9%), Y(141=0.1%) — 注意尾随空格 |
| `bk_active_flag` | "Y", "N", "" | 共240,608行 · NULL率0.65% · ""(237,717=98.8%), Y(1,051=0.4%), N(274=0.1%) |
| `bk_chapter_code` | "07", "13", "11" | 共240,608行 · NULL率0.65% · ""(237,717), 07(843=0.35%), 13(268), 11(205) |
| `reo_start_date` | — | 共240,608行 · **NULL率100%** — 当前数据集无REO记录 |
| `forbearance_flag` | "N", "Y" | 共240,608行 · NULL率0% · N(239,875=99.7%), Y(733=0.3%) |
| `modification_type` | "", "NON-HAMP" | 共240,608行 · NULL率0.64% · ""(234,627=97.7%), NON-HAMP(4,441=1.8%) |

**`delq_status_mba` → `delinq` SLS映射（8种原始值）：**

| 原始值 | 标准 `delinq` |
|-------|--------------|
| `Current` | `C` |
| `DQ 30` | `D30` |
| `DQ 60` | `D60` |
| `DQ 90` | `D90` |
| `DQ 120+` | `D120P` |
| `Foreclosure` / `FCL` | `FCL` |
| `REO` | `REO` |
| `Paid in Full` / `Service Release` | `P` |
| `Bankruptcy` | days360计算 + bankruptcy='Y' |

---

### 3.2 `portfcldaily` — 止赎日报详情表

**表描述：** SLS 止赎流程跟踪表，记录每笔在止赎中的贷款的关键里程碑日期、止赎类型（JUD=司法/POS=非司法）和天数统计。行数较少（2,056行），因为只包含有止赎记录的贷款。

**全限定名：** `sls.portfcldaily`｜**总行数：** 2,056  
**贷款ID字段：** `account_number`（int，9个唯一值）  
**日期字段：** `data_as_of_date`（date，2023-03-29 ~ 2024-08-07，356个不同日期）  
**唯一贷款数：** 9

**Part A — 字段定义**

| 字段名 | 类型 | 含义 | 取值范围 | 计算逻辑 | FCL相关 |
|--------|------|------|---------|---------|--------|
| `fcl_active_flag` | varchar(255) | **活跃止赎标志** | {"Y", "N"}，无NULL | 原始摄入 → 映射为 `fcl_flag` | ✅ 主要 |
| `fcl_approval_date` | date | 止赎批准日期 | 2022-06-09 ~ 2024-04-18，无NULL | 原始摄入 | ✅ 主要 |
| `fcl_referred_to_attorney_date` | date | 委托律师日期 | 2022-06-09 ~ 2024-04-18，无NULL | 原始摄入 → 流入 `port.fcl_stage_info.referral_start_date` | ✅ 主要 |
| `fcl_first_legal_action_date` | date | 首次法律行动日期 | 2023-04-25 ~ 2024-03-29，或 NULL | 原始摄入 → 流入 `port.fcl_stage_info.legal_start_date` | ✅ 主要 |
| `fcl_service_complete_date` | date | 送达完成日期 | 全部NULL（当前数据集） | 原始摄入（尚无记录） | ✅ 主要 |
| `fcl_judgement_entered_date` | date | 判决生效日期 | 全部NULL（当前数据集） | 原始摄入（尚无记录） | ✅ 主要 |
| `fcl_sale_scheduled_date` | date | 计划拍卖日期 | 2023-07-27 ~ 2023-09-14，或 NULL | 原始摄入 → 流入 `port.fcl_stage_info.sale_start_date` | ✅ 主要 |
| `fcl_sale_held_date` | date | 实际拍卖日期 | 全部NULL（当前数据集） | 原始摄入（尚无记录） | ✅ 主要 |
| `fcl_days` | int | 在止赎中的天数 | 0 ~ 790，无NULL | 原始摄入（服务商计算） | ✅ 主要 |
| `fcl_days_variance_to_fnma` | int | 实际天数 vs Fannie Mae基准的偏差 | 全部NULL（当前数据集） | 原始摄入（尚无记录） | ✅ 辅助 |
| `fcl_current_status_desc` | text | 止赎当前阶段描述 | {"CLOSED", "REFFERED TO ATTORNEY", "SALE SCHEDULED"}，无NULL | 原始摄入（注：原始数据中拼写错误"REFFERED"） | ✅ 主要 |
| `fcl_type_code` | varchar(255) | 止赎类型代码 | {"POS"(非司法), "JUD"(司法)}，无NULL | 原始摄入 → 流入 `port.basic_data_loan_fcl.judicial` | ✅ 辅助 |
| `fcl_sale_amount` | decimal(32,16) | 拍卖成交金额 | 全部为0（当前无已成交记录） | 原始摄入 | ✅ 辅助 |
| `fcl_bid_amount` | decimal(32,16) | 止赎出价金额 | 全部为0（当前无记录） | 原始摄入 | ✅ 辅助 |

**Part B — 字段统计**

| 字段名 | 值举例 | 统计信息 |
|--------|--------|---------|
| `fcl_active_flag` | "Y", "N" | 共2,056行 · NULL率0% · N(1,520=73.9%), Y(536=26.1%) |
| `fcl_approval_date` | 2022-06-09, 2023-05-12 | 共2,056行 · NULL率0% · 9个日期 |
| `fcl_referred_to_attorney_date` | 2022-06-09, 2023-05-02 | 共2,056行 · NULL率0% · 9个日期 |
| `fcl_first_legal_action_date` | 2023-04-25, 2023-12-06 | 共2,056行 · NULL率73.6% · 3个日期 |
| `fcl_service_complete_date` | — | 共2,056行 · **NULL率100%** |
| `fcl_judgement_entered_date` | — | 共2,056行 · **NULL率100%** |
| `fcl_sale_scheduled_date` | 2023-09-14, 2023-07-27 | 共2,056行 · NULL率85.8% · 2个日期 |
| `fcl_sale_held_date` | — | 共2,056行 · **NULL率100%** |
| `fcl_days` | 76, 83, 70, 69 | 共2,056行 · NULL率0% · 701个不同值 · 范围0~790天 |
| `fcl_days_variance_to_fnma` | — | 共2,056行 · **NULL率100%** |
| `fcl_current_status_desc` | "REFFERED TO ATTORNEY", "CLOSED" | 共2,056行 · NULL率0% · 3种描述（含原始拼写错误） |
| `fcl_type_code` | "POS", "JUD" | 共2,056行 · NULL率0% · POS(1,507=73.3%), JUD(549=26.7%) |
| `fcl_sale_amount` | 0 | 共2,056行 · NULL率0% · **全部为0**（无已成交记录） |
| `fcl_bid_amount` | 0 | 共2,056行 · NULL率0% · **全部为0** |

---

### 3.3 `portbkdaily` — 破产日报表

**表描述：** SLS 破产流程跟踪表，记录有效破产记录的基本信息。行数少（1,616行），只包含有破产记录的贷款。

**全限定名：** `sls.portbkdaily`｜**总行数：** 1,616  
**贷款ID字段：** `account_number`（int，7个唯一值）  
**日期字段：** `data_as_of_date`（date，2023-03-15 ~ 2024-08-07，365个不同日期）

**Part A — 字段定义**

| 字段名 | 类型 | 含义 | 取值范围 | 计算逻辑 | FCL相关 |
|--------|------|------|---------|---------|--------|
| `bk_active_flag` | varchar | **活跃破产标志** | {"Y", "N"}，无NULL | 原始摄入 → 参考生成 `bankruptcy` 辅助标志 | ✅ 辅助 |
| `bk_chapter_code` | varchar(255) | 破产章节代码 | {"07", "13", "11"}，无NULL | 原始摄入 → 流入 `port.basic_data_loan_foreclosure_bankruptcy.chapter` | ✅ 辅助 |
| `bk_filed_date` | date | 破产申请日期 | 2021-03-07 ~ 2024-03-25，无NULL | 原始摄入 | ✅ 辅助 |
| `bk_discharged_flag` | varchar | 破产解除标志 | {"Y", "N"}，无NULL | 原始摄入 | ✅ 辅助 |
| `fcl_days_in_bankruptcy` | varchar(255) | 止赎流程中在破产状态的天数 | 空字符串（92.6%）或数字字符串，无NULL | 原始摄入（空字符串=尚未计算）| ✅ 辅助 |
| `bk_cramdown_flag` | varchar | 强制偿债计划标志 | {"N"}（100%），无NULL | 原始摄入 | — |

**Part B — 字段统计**

| 字段名 | 值举例 | 统计信息 |
|--------|--------|---------|
| `bk_active_flag` | "Y", "N" | 共1,616行 · NULL率0% · Y(1,060=65.6%), N(556=34.4%) |
| `bk_chapter_code` | "07", "13", "11" | 共1,616行 · NULL率0% · 07(963=59.6%), 13(447=27.7%), 11(206=12.7%) |
| `bk_filed_date` | 2023-08-23, 2023-03-13 | 共1,616行 · NULL率0% · 7个日期 · 范围2021-03-07~2024-03-25 |
| `bk_discharged_flag` | "N", "Y" | 共1,616行 · NULL率0% · N(1,197=74.1%), Y(419=25.9%) |
| `fcl_days_in_bankruptcy` | "", "336", "337" | 共1,616行 · NULL率0% · 121种值 · ""(1,496=92.6%) 其余为天数 |
| `bk_cramdown_flag` | "N" | 共1,616行 · NULL率0% · **全部为"N"** |

---

### 3.4 `portlmdaily` — 损失缓解日报表

**表描述：** SLS 损失缓解流程跟踪表（最大SLS分表，原始有179个字段）。本文档仅记录止赎相关的关键LM字段。

**全限定名：** `sls.portlmdaily`｜**总行数：** 21,283  
**贷款ID字段：** `account_number`（bigint，34个唯一值）  
**日期字段：** `data_as_of_date`（datetime，2023-04-01 ~ 2024-08-07）

**Part A — 字段定义**

| 字段名 | 类型 | 含义 | 取值范围 | 计算逻辑 | FCL相关 |
|--------|------|------|---------|---------|--------|
| `loss_mit_evaluation_status` | varchar(255) | **LM评估状态**（主要状态字段） | 25种状态描述，无NULL | 原始摄入 → 参考生成 `lm_flag`（Pending类→Y，Resolved类→N） | ✅ 主要 |
| `loss_mit_workout_type_code_desc` | text | LM方案类型描述 | 9种描述（含空字符串），无NULL | 原始摄入 → 流入 `port.basic_data_loan_foreclosure_loss_mitigation` | ✅ 辅助 |
| `loss_mit_mod_effective_date` | datetime | 贷款修改生效日期 | 2023-10-01 ~ 2024-06-01，或 NULL | 原始摄入 → 流入 `port.basic_data_loan_foreclosure_loss_mitigation` | ✅ 辅助 |
| `loss_mit_mod_terms_modified_interest_rate_percent` | decimal(32,16) | 修改后利率（%） | 2.63% ~ 8.25%，或 NULL | 原始摄入（LM谈判结果） | ✅ 辅助 |
| `workout_completed_date` | datetime | LM方案完成日期 | 2024-04-26 ~ 2024-06-07，或 NULL | 原始摄入 | ✅ 辅助 |

**Part B — 字段统计**

| 字段名 | 值举例 | 统计信息 |
|--------|--------|---------|
| `loss_mit_evaluation_status` | "Resolved-Withdrawn", "Resolved-Complied", "Pending-Compliance" | 共21,283行 · NULL率0% · 25种 · Resolved-Withdrawn(6,705=31.5%), Resolved-Complied(3,871=18.2%), Resolved-BorrowerDisengaged(3,346=15.7%), Resolved-DidNotComply(2,586=12.2%), Pending-Compliance(1,375=6.5%) |
| `loss_mit_workout_type_code_desc` | "Trial Period Plan", "Modification" | 共21,283行 · NULL率0% · 9种（含空字符串） |
| `loss_mit_mod_effective_date` | 2024-02-01, 2024-04-01 | 共21,283行 · NULL率65.6% · 9个日期 · 范围2023-10-01~2024-06-01 |
| `loss_mit_mod_terms_modified_interest_rate_percent` | 7.13%, 4.00%, 8.25% | 共21,283行 · NULL率59.9% · 16种利率 · 范围2.63%~8.25% |
| `workout_completed_date` | 2024-04-26, 2024-06-07 | 共21,283行 · NULL率96.4% · 3个日期 |

---

## 4. Carrington（`carrington` schema）

**数据库：** MySQL（`bridg004-db-prod`）  
**Schema：** `carrington`  
**数据文件格式：** `.xlsx` 或 `.csv`  
**数据时间范围：** 2023-11-05 ~ 2026-05-19  

> **注意：** 原始文档描述的 `status` 和 `foreclosure_status_code` 字段**不存在**于当前数据库。实际FCL状态字段为 `loan_status`（文字描述）和 `fcl_flag`（"Active"）。Carrington 采用**单表设计**，所有 FCL/BK/LM/资产信息整合在一张表中。

---

### 4.1 `portcarrington` — Carrington 综合数据表

**表描述：** Carrington 服务商综合贷款状态快照表（单表设计）。将 FCL、BK、LM、资产基本信息整合在一张宽表中（约200个字段）。FCL状态通过 `loan_status` + `fcl_flag` + `fcl_status` 三字段联合描述。

**全限定名：** `carrington.portcarrington`｜**总行数：** 299,071  
**贷款ID字段：** `loanid`（varchar(100)，719个唯一值）  
**日期字段：** `snap_shot_date`（date，2023-11-05 ~ 2026-05-19，892个不同日期）

**Part A — 字段定义（止赎相关字段）**

| 字段名 | 类型 | 含义 | 取值范围 | 计算逻辑 | FCL相关 |
|--------|------|------|---------|---------|--------|
| `loanid` | varchar(100) | 贷款ID（Bridger） | 719个唯一值，无NULL | 原始摄入 | ✅ 主要 |
| `snap_shot_date` | date | 数据日期（快照日期） | 2023-11-05 ~ 2026-05-19 | 原始摄入 | — |
| `loan_status` | varchar(255) | **贷款综合状态**（含FCL/REO/LM等） | 16种文字描述，无NULL | 原始摄入 → `portdaily_config.py` CASE-WHEN 映射为 `delinq`（如 "Foreclosure"→FCL，"REO"→REO，"Completed Payoff"→P） | ✅ 主要 |
| `fcl_flag` | varchar(50) | **活跃止赎标志** | {"Active"} 或 NULL | 原始摄入 → 映射为 `fcl_flag='Y'` | ✅ 主要 |
| `fcl_status` | varchar(50) | 止赎阶段状态 | 7种文字描述（"1. First Legal Pending"等）或 NULL | 原始摄入 → 流入 `port.basic_data_loan_fcl` | ✅ 主要 |
| `fcl_sub_status` | varchar(50) | 止赎子状态 | 18种描述（如"Title Summary","Pending First Legal"等）或 NULL | 原始摄入 | ✅ 辅助 |
| `fcl_referral_date` | date | 止赎转介律师日期 | 2023-09-22 ~ 2026-03-17，或 NULL | 原始摄入 | ✅ 主要 |
| `fcl_scheduled_sale_date` | date | 计划拍卖日期 | 2023-12-05 ~ 2026-01-16，或 NULL | 原始摄入 | ✅ 主要 |
| `fcl_sale_held_date` | date | 实际拍卖日期 | 2025-01-23 ~ 2026-01-16，或 NULL | 原始摄入 | ✅ 主要 |
| `fcl_active_hold` | varchar(50) | 是否有活跃暂停 | {"Yes", "No"} 或 NULL | 原始摄入 | ✅ 辅助 |
| `fcl_latest_hold_reason` | varchar(255) | 最新暂停原因 | 7种描述（"BK Hold","Special Handling Loan Alert"等）或 NULL | 原始摄入 | ✅ 辅助 |
| `lm_flag` | varchar(50) | 损失缓解标志 | {"Active", "Completed/Cancelled"} 或 NULL | 原始摄入 → `CASE WHEN lm_flag='Active' THEN 'Y' ELSE 'N'` | ✅ 主要 |
| `bk_flag` | varchar(50) | 破产标志 | {"Active", "Completed/Cancelled"} 或 NULL | 原始摄入 → 生成 `bankruptcy` | ✅ 辅助 |
| `bk_chapter` | decimal(32,16) | 破产章节 | {7.0, 13.0} 或 NULL | 原始摄入 | ✅ 辅助 |
| `covid_forbearance_flag` | varchar(255) | COVID宽限标志 | {"N"} 或 NULL | 原始摄入（遗留字段，大部分为NULL） | — |

**Part B — 字段统计**

| 字段名 | 值举例 | 统计信息 |
|--------|--------|---------|
| `loan_status` | "CUR", "0-29", "Foreclosure", "Bankruptcy - Performing" | 共299,071行 · NULL率0% · 16种 · CUR(199,288=66.6%), 0-29(59,622=19.9%), Completed Payoff(17,176=5.7%), 30-59(8,862=3.0%), Loss Mitigation(4,699=1.6%), Foreclosure(2,077=0.7%), REO(286=0.1%) |
| `fcl_flag` | "Active" | 共299,071行 · NULL率98.9% · 非NULL: 3,314行 · 全为"Active" |
| `fcl_status` | "1. First Legal Pending", "2. First Legal Filed" | 共299,071行 · NULL率98.8% · 7种 · "1. First Legal Pending"(1,651=44%), "2. First Legal Filed"(1,150=31%), "3. Judgement Entered..."(398=11%), "5. Sales Held"(305=8%) |
| `fcl_sub_status` | "Title Summary", "Pending First Legal", "Judgment Entered" | 共299,071行 · NULL率98.8% · 18种 |
| `fcl_referral_date` | 2024-01-15, 2023-09-22 | 共299,071行 · NULL率98.8% · 22个日期 |
| `fcl_scheduled_sale_date` | 2025-06-30, 2026-01-16 | 共299,071行 · NULL率99.8% · 6个日期 |
| `fcl_sale_held_date` | 2025-01-23, 2026-01-16 | 共299,071行 · NULL率99.8% · 2个日期 |
| `fcl_active_hold` | "Yes", "No" | 共299,071行 · NULL率98.8% · Yes(1,983=53%), No(1,724=47%) |
| `fcl_latest_hold_reason` | "BK Hold", "Special Handling Loan Alert" | 共299,071行 · NULL率99.9% · 7种描述 |
| `lm_flag` | "Active", "Completed/Cancelled" | 共299,071行 · NULL率72.8% · Completed/Cancelled(76,654=94.2%), Active(4,702=5.8%) |
| `bk_flag` | "Active", "Completed/Cancelled" | 共299,071行 · NULL率91.3% · Completed/Cancelled(23,952=91.8%), Active(2,139=8.2%) |
| `bk_chapter` | 7.0, 13.0 | 共299,071行 · NULL率91.3% · 13.0(15,658=60%), 7.0(10,433=40%) |
| `covid_forbearance_flag` | "N" | 共299,071行 · NULL率96.4% · 非NULL: 10,704行 · 全为"N" |

**`loan_status` 完整取值分布（全16种）：**

| loan_status 值 | 记录数 | % | 映射 delinq |
|---------------|--------|---|------------|
| `CUR` | 199,288 | 66.6% | `C` |
| `0-29` | 59,622 | 19.9% | `D30` |
| `Completed Payoff` | 17,176 | 5.7% | `P` |
| `30-59` | 8,862 | 3.0% | `D60` |
| `Loss Mitigation` | 4,699 | 1.6% | days360计算 + lm_flag=Y |
| `60-89` | 2,335 | 0.8% | `D60` |
| `Foreclosure` | 2,077 | 0.7% | `FCL` |
| `Bankruptcy - Performing` | 1,966 | 0.7% | days360计算 + bankruptcy=Y |
| `Completed Short Sale` | 1,237 | 0.4% | `P` |
| `90-119` | 642 | 0.2% | `D90` |
| `120+` | 422 | 0.1% | `D120P` |
| `REO` | 286 | 0.1% | `REO` |
| `Completed REO Sale` | 267 | 0.1% | `REO` |
| `Bankruptcy - Non-Performing` | 129 | 0.04% | days360计算 + bankruptcy=Y |
| `Foreclosure/Bankruptcy - Non-Performing` | 44 | 0.01% | `FCL` + bankruptcy=Y |
| `3rd Party Sale` | 19 | 0.006% | `P` |

---

## 5. MRC（`mrc` schema）

**数据库：** MySQL（`bridg004-db-prod`）  
**Schema：** `mrc`  
**数据文件格式：** `.txt`  
**数据时间范围：** 2026-04-03 ~ 2026-04-29（极少量当月数据）

---

### 5.1 `portmrcforeclosure` — MRC止赎记录表

**表描述：** MRC 服务商的止赎流程跟踪表，结构完整（47个字段），覆盖止赎各阶段里程碑日期和结果，但当前数据库中记录极少（仅17行）且大部分字段为NULL。

**全限定名：** `mrc.portmrcforeclosure`｜**总行数：** 17  
**贷款ID字段：** `loanid`（varchar(24)，1个唯一值）  
**日期字段：** `dataasof`（date，2026-04-03 ~ 2026-04-29，17个不同日期）

**Part A — 字段定义（核心字段）**

| 字段名 | 类型 | 含义 | 取值范围 | 计算逻辑 | FCL相关 |
|--------|------|------|---------|---------|--------|
| `loanid` | varchar(24) | 贷款ID（Bridger） | 1个唯一值（700084240000002），无NULL | 原始摄入 | ✅ 主要 |
| `dataasof` | date | 数据日期 | 2026-04-03 ~ 2026-04-29 | 原始摄入 | — |
| `fc_flag` | char(1) | **活跃止赎标志** | {"N"} 或 NULL | 原始摄入 → 映射为 `fcl_flag` | ✅ 主要 |
| `fc_status` | varchar(255) | 止赎状态 | 全部NULL（当前数据集） | 原始摄入 | ✅ 主要 |
| `fc_milestone` | varchar(255) | 止赎里程碑 | 全部NULL（当前数据集） | 原始摄入 | ✅ 主要 |
| `referral_date` | date | 委托律师日期 | 全部NULL（当前数据集） | 原始摄入 | ✅ 主要 |

**Part B — 字段统计**

| 字段名 | 值举例 | 统计信息 |
|--------|--------|---------|
| `fc_flag` | "N" | 共17行 · NULL率0% · **全部为"N"**（当前无活跃止赎） |
| `fc_status` | — | 共17行 · **NULL率100%** |
| `fc_milestone` | — | 共17行 · **NULL率100%** |

---

## 6. FCI / Selene（`fci` / `selene` schema）

**数据库：** MySQL（`bridg004-db-prod`）  
**Schema：** `fci`（FCI）和 `selene`（Selene）  
**数据文件格式：** FCI=`.xlsx`，Selene=`.csv`  
**字段定义：** 无独立 DDL 文件；字段从 `portmonth_config.py` 中的 SQL 推断  

FCI 和 Selene 的止赎字段通过 `portmonth_config.py` 中的 per-servicer SQL 直接提取，命名和格式因服务商而异，在 ETL 层统一映射到标准 `delinq`。

---

## 7. 跨服务商字段对照

| 标准字段 | Newrez | SLS | Carrington | MRC |
|---------|--------|-----|------------|-----|
| **贷款ID字段名** | `loanid` (varchar) | `account_number_investor` (varchar) | `loanid` (varchar) | `loanid` (varchar) |
| **数据日期字段名** | `dataasof` | `dataasofdate` / `data_as_of_date` | `snap_shot_date` | `dataasof` |
| **原始逾期状态** | `delinquency_status_mba` | `delq_status_mba` | `loan_status` | — |
| **活跃FCL标志** | `activefcflag` (int 0/1) | `fcl_active_flag` (varchar Y/N) | `fcl_flag` (varchar "Active"/NULL) | `fc_flag` (char N) |
| **FCL阶段** | `fcstage` (varchar) | `fcl_current_status_desc` (text) | `fcl_status` (varchar) | `fc_milestone` (varchar) |
| **在FCL中天数** | `daysinfc` (int) | `fcl_days` (int) | — | — |
| **Hold原因** | `fchold1description` (varchar) | — | `fcl_active_hold` + `fcl_latest_hold_reason` | — |
| **活跃BK标志** | `activebkflag` (int 0/1) | `bk_active_flag` (varchar Y/N) | `bk_flag` (varchar "Active"/NULL) | — |
| **BK章节** | `bkchapter` (int 7/11/13) | `bk_chapter_code` (varchar "07"/"13"/"11") | `bk_chapter` (decimal 7.0/13.0) | — |
| **活跃LM标志** | `activelmflag` (int 0/1) | `loss_mit_evaluation_status` (varchar) | `lm_flag` (varchar "Active"/NULL) | — |

---

## 8. 贷款 ID 映射表

**表：** `port.portidmap` / `port.portloanidmap`（Redshift）

| 字段 | 含义 |
|------|------|
| `loanid` | Bridger 内部贷款 ID（主键） |
| `sellerloanid` | 卖方贷款 ID |
| `currentservicerloanidnew` | 当前服务商贷款 ID |
| `slsloanid` | SLS 专用贷款 ID |
| `encompassloanidsold` | Encompass 系统贷款 ID |

---

## 9. 已知局限

| 局限 | 详情 |
|------|------|
| FCI / Selene 无独立 DDL | 字段定义只能从 `portmonth_config.py` 中的 SQL 推断 |
| SLS → Newrez 切换（2024-07-05） | 历史数据有切换点；时间范围感知查询必须 UNION 两侧数据 |
| SLS 数据截止 2024-08-07 | 此后 SLS 不再更新，Newrez 接管 |
| Carrington 单表设计 | 无法精确区分 BK/LM 子状态；仅 `loan_status` + `lm_flag` + `bk_flag` 三维度 |
| VASP 映射逻辑未在代码中显式定义 | 属于运营层覆盖（实证：19条 VASP 记录，全来自 Newrez，delinquency_status_mba 非一致）|
| MRC 数据极少 | 仅17行当月数据，大部分字段为NULL；止赎详情字段（fc_status等）均空 |
| Newrez 表名已从 portshellpoint* 改为 portnewrez* | DDL 文件 shellpoint_daily.sql 为历史名称；现役表在 `newrez` schema 中使用 `portnewrez*` 前缀 |

---

## 对应英文版

英文版：`docs/en/01_source_data.md`
