# doc 15 — Newrez Servicer FCL 字段缺口分析

---

## 文档目的

- **为什么存在**：Newrez 是当前 BPS Foreclosure 字段反向映射的 benchmark Servicer，也是 doc 14 目标接口标准的主要数据来源。本文将 Newrez 从原始数据、PrefectFlow 血缘、BPS 展示到字段缺口的链条单独固化，作为后续其他 Servicer 文档的样例。
- **解决的问题**：把 Newrez “已经能支持什么、哪里只是部分支持、哪些字段应向 Servicer 请求、哪些属于内部 ETL/BPS 问题”分开，避免把 Servicer 缺字段和公司内部链路缺口混在一起。
- **范围**：覆盖 Newrez FCL 主表、Hold、LM、BK、Stage/Timeline 聚合字段；不重新展开 doc 13 的所有 SQL，只引用其已验证结论。
- **系统关系**：本文是 doc 14 的第一个逐 Servicer 落地对照文档，也是后续 Carrington/SLS/Selene/MRC 等文档的模板样例。

## 目标读者

数据产品经理 · 数据治理团队 · Newrez 对接负责人 · ETL 开发者 · BPS 运营人员 · 未来 AI Session

## 修订历史

| 日期 | 作者 | 版本 | 变更说明 | 关联文档 |
|------|------|------|---------|---------|
| 2026-05-28 | AI Agent (Codex) | v1 | 初始版本；基于 doc 13 v21、doc 14 v3、PrefectFlow 代码路径建立 Newrez 缺口清单 | doc 13, doc 14 |
| 2026-05-28 | AI Agent (Codex) | v2 | 增加数据库验证计划，明确后续用 MCP 刷新 Newrez 字段填充率、枚举分布和端到端样本校验 | doc 98 |

## 依赖文档

| 文档 | 用途 |
|------|------|
| doc 01 | Newrez 原始表结构和字段来源 |
| doc 07 | Newrez 当前 FCL 血缘与判断规则 |
| doc 08 | Newrez 原始字段到 FCL 状态的现状映射 |
| doc 12 | BPS sync 流程和目标表 |
| doc 13 | BPS 展示字段反向映射和 MCP 实测 |
| doc 14 | BPS 驱动的目标接口标准 |
| doc 98 | 数据库验证与 MCP 使用规范 |

## 已知限制

- 本文沿用 doc 13 在 2026-05 的 MCP 实测填充率；活跃贷款数量和填充率会随每日快照变化。
- 本文 v1 未直接连接数据库重新测量；正式向 Newrez 发送字段请求前，应按 Section 7 的 SQL 计划刷新数值。
- BK 面板部分解码逻辑仍需工程确认，特别是 `bkstatus` / `bkstage` 是否应转为业务文本。

---

## 1. Newrez 概况

| 项目 | 内容 |
|------|------|
| Servicer | Newrez / Shellpoint |
| 数据频率 | 日报为主 |
| 当前原始来源 | PrefectFlow 配置中按 Newrez Foreclosure、Bankruptcy、LossMitigation 文件入库 |
| FCL 主表 | `newrez.portnewrezfc` |
| LM 表 | `newrez.portnewrezlm` |
| BK 表 | `newrez.portnewrezbk` |
| BPS 主要目标表 | `bpms_dev.sync_loan_foreclosure`, `sync_loan_foreclosure_hold`, `sync_loan_foreclosure_loss_mitigation`, `sync_loan_foreclosure_bankruptcy`, `sync_fcl_stage_info` |
| 当前系统评级 | ✅ 可作为 benchmark；但存在 P1/P2 字段缺口和若干 BPS/ETL 口径问题 |

## 2. 当前数据血缘链条

```
Newrez 日报/专项文件
  -> newrez.portnewrezfc / portnewrezlm / portnewrezbk
  -> PrefectFlow basic_data_pool_config.py
  -> port.basic_data_loan_fcl / port.basic_data_loan_foreclosure / fcl_stage_info
  -> sync_asset_management.py
  -> bpms_dev.sync_* Foreclosure 表
  -> BPS Foreclosure 详情页和聚合页
```

| 层级 | 位置 | 作用 | 当前结论 |
|------|------|------|----------|
| 原始入库配置 | `flow/basic_data/load_servicer_data_config/servicer_config.py` | Newrez FCL/BK/LM 文件映射到 `newrez.portnewrezfc/bk/lm` | 已有独立 FCL、BK、LM 专项来源 |
| FCL 中间层 | `flow/basic_data/basic_data_config/basic_data_pool_config.py` | 将 `portnewrezfc` 字段归一化到 `port.basic_data_loan_fcl` | `fcjudgmenthearingscheduled`、`fcscheduledsaledate` 等核心字段已接入 |
| BPS 主表映射 | `basic_data_pool_config.py` + `asset_managment_config.py` | 生成 `timeline_*`, `summary_*`, `bid_approval_*` 等字段 | BPS 主表和详情页字段大部分可覆盖 |
| BPS Stage | `basic_data_pool_config.py` + `sync_asset_management.py` | 使用最新 `newrez.portnewrezfc.dataasof` 计算 FCL Stage | Stage 逻辑以 Newrez 当前快照为基准 |
| BPS 同步 | `flow/bps/bps_config/sync_to_bps_config.py` | 将 Foreclosure、LM、BK、Hold、Stage 写入 BPS sync 表 | 5 类 Foreclosure sync 表均已配置 |

## 3. Foreclosure 状态判断逻辑

| 判断层级 | Newrez 字段/规则 | 当前实现 | 风险 |
|----------|------------------|----------|------|
| BPS 入库前提 | `fcreferraldate IS NOT NULL` 且 `activefcflag` 表示活跃 | doc 13/doc 14 已确认；BPS 以已转介 FCL 贷款为核心范围 | 历史 `activefcflag` NULL 需 NULL-safe 处理 |
| FCL 主状态 | `delinquency_status_mba` / Newrez MBA 文本值含 `Foreclosure` 扩展值 | doc 08 已记录映射到内部 `FCL` | 复合值同时包含 BK，需要独立 BK 字段避免语义丢失 |
| 当前阶段 | `currentmilestone` 优先，`fcstage` 兜底 | BPS Summary 当前步骤以 `currentmilestone` 为优先 | `currentmilestone` 填充率偏低，且与 `fcstage` 可能不一致 |
| Stage 聚合 | `fcscheduledsaledate`, `fcjudgmenthearingscheduled`, `servicecompletedate`, `firstlegaldate`, `fcreferraldate`, `demandsentdate` | BPS 使用瀑布式优先级写入 `sync_fcl_stage_info.stage` | Publication 对 Newrez 恒空，NOI/Demand 展示口径需特别说明 |
| Hold | `fchold1/2/3*` 槽位 | BPS 每日追加变更，形成 Hold 历史 | Newrez 只给快照槽位，不是完整历史文件 |
| LM/BK | `portnewrezlm`, `portnewrezbk` | BPS 独立面板读取独立 sync 表 | LM 已解码为文本；BK 解码行为仍需确认 |

## 4. doc 14 目标字段对照

| doc 14 字段组 | 关键字段 | Newrez 状态 | 当前来源 | 缺口性质 | 优先级 |
|---|---|---|---|---|---|
| P0 入库字段 | `loan_id`, `servicer_loan_id`, `data_as_of_date`, `state`, `judicial_flag`, `active_fcl_flag`, `fcl_referral_date` | 已提供 | `portnewrezfc.loanid/shellpointloanid/dataasof/state/judicial/activefcflag/fcreferraldate` | 无；仅需 NULL-safe 处理历史 `activefcflag` | P0 |
| FCL Summary | `current_milestone`, `last_step_completed`, `attorney_firm`, `days_in_fcl`, `sale_amount` | 部分提供 | `currentmilestone`, `lastfcstepcompleted`, `fcfirm`, `daysinfc`, `fcsaleamount` | `currentmilestone` 填充率偏低；`fcsaleamount` 与 `fcsalehelddate` 时序异常 | P1 |
| Timeline | Demand/Referral/First Legal/Service/Judgement/Sale/Completed | 部分提供 | `demandsentdate`, `fcreferraldate`, `firstlegaldate`, `servicecompletedate`, `fcjudgmenthearingscheduled`, `fcscheduledsaledate`, `fcremovaldate/dtdeedrecorded` | `publication_date`, `titlereceiveddate`, `titlecleardate` 基本未提供 | P1/P2 |
| Hold | 3 个 Hold 槽位 | 已提供但为快照槽位 | `fchold1/2/3description/start/end/projectedenddate` | 若要求完整历史，需依赖 BPS 内部追加机制，不是 Servicer 源文件直接提供 | P1/P2 |
| LM | Deal/Program/Status/Cycle/Disposition/Denial | 部分提供 | `portnewrezlm.lmdeal/lmprogram/lmstatus/dealstartdate/lmremovaldate/lmdecision/denialreason` | `borrowerintention`, `imminent_default`, `single_point_of_contact` 未提供 | P1/P2 |
| BK | Chapter/Status/MFR/POC/Post-petition due | 部分提供 | `portnewrezbk` | `lien_status`, `claim_status` 来源待确认；BK 数字码解码待确认 | P1 |
| Aggregate Stage/Timeline | `stage`, `{stage}_start_date`, days metrics | 内部可推导 | `portnewrezfc` + `sync_fcl_stage_info` | `NOI Date 1` 使用 `noi_start_date`，但 Newrez Demand 日期进入 `demand_start_date`，需产品确认显示口径 | P1 |

## 5. Newrez 缺口与行动项

### 5.1 向 Newrez 请求或确认

| 请求项 | 原因 | 优先级 | 验收标准 |
|--------|------|--------|----------|
| 补充或提高 `currentmilestone` 填充率 | BPS Summary 当前步骤优先读取该字段 | P1 | 活跃 FCL 贷款填充率提升至业务认可阈值，且与 `fcstage` 差异可解释 |
| 确认 `fcsaleamount` 与 `fcsalehelddate` 更新时序 | 当前金额填充率高于 sale held 日期，可能造成成交信息误读 | P1 | Newrez 给出字段更新规则；BPS 使用金额时同步校验 sale held 日期 |
| 提供 `publication_date` | Publication stage 和 timeline 字段恒空 | P2 | 新增字段或确认 Newrez 不适用 Publication 阶段 |
| 提供 title 相关日期 | `titlereceiveddate` / `titlecleardate` 当前基本为空 | P2 | Title received/clear 字段可用于 Timeline |
| 提供 LM `borrowerintention` 或替代字段 | BPS LM 面板 Borrower Intentions 为空 | P2 | 字段有稳定枚举和解码说明 |
| 提供 `imminent_default`、`single_point_of_contact` | CFPB Reg X 相关字段缺失 | P2 | 字段或明确“不提供/不适用”说明 |

### 5.2 内部 ETL/BPS 需确认

| 行动项 | 原因 | Owner | 优先级 |
|--------|------|-------|--------|
| 确认 `activefcflag IS NULL` 的处理是否在所有链路一致 | doc 13 Q3 记录历史 NULL 需视为活跃 | ETL/BPS | P0 |
| 确认 BK 数字码解码表 | LM 已解码为文本，BK 可能仍存数字码 | ETL/BPS | P1 |
| 确认 Time Line Tab `NOI Date 1` 是否应展示 Demand 日期 | Newrez `demandsentdate` 进入 `demand_start_date`，但 `noi_start_date` 恒空 | BPS 产品 | P1 |
| 确认 `actual_judgement_hearing_set_days` 来源 | `fcjudgment_end_date` 已进中间表但未明确进入下游 BPS 计算 | ETL/BPS | P1 |

## 6. 对外字段请求摘要

建议向 Newrez 发出的正式请求可分两批：

| 批次 | 字段 | 说明 |
|------|------|------|
| 第一批 P1 质量确认 | `currentmilestone`, `fcsaleamount`, `fcsalehelddate` | 不一定要求新增字段，但需要 Newrez 解释更新规则、提高填充率或提供可用替代口径 |
| 第二批 P2 完整性补充 | `publication_date`, `titlereceiveddate`, `titlecleardate`, `borrowerintention`, `imminent_default`, `single_point_of_contact` | 不阻断 BPS 当前使用，但会提升 Timeline、LM、合规分析完整性 |

## 7. 数据库验证计划

> 默认使用 MCP 只读查询。本文当前沿用 doc 13 的 2026-05 MCP 结果；如用于正式字段请求，应重新运行本节 SQL 并记录查询日期、快照日期、行数和结论。

### 7.1 验证矩阵

| 验证类型 | MCP/数据库 | 目标表 | 目标字段/规则 | SQL 引用 | 预期结论 |
|----------|------------|--------|---------------|----------|----------|
| Schema 验证 | MySQL | `newrez.portnewrezfc` | FCL 主字段、timeline、hold、bid/sale 字段 | SQL-15-1 | 字段存在性与 doc 14 对照 |
| Fill rate 验证 | MySQL | `newrez.portnewrezfc` | P0/P1/P2 FCL 字段填充率 | SQL-15-2 | 刷新 `currentmilestone`、title、publication、sale 字段状态 |
| LM 验证 | MySQL | `newrez.portnewrezlm` | LM code 字段、cycle dates、borrower intention | SQL-15-3 | 确认 LM 字段覆盖与缺口 |
| BK 验证 | MySQL | `newrez.portnewrezbk` + BPS BK sync 表 | BK 字段与解码状态 | SQL-15-4 | 确认 BK 数字码和面板字段来源 |
| End-to-end 样本 | MySQL + Redshift | `newrez.portnewrezfc` -> `port.basic_data_loan_fcl` -> `bpms_dev.sync_fcl_stage_info` | 2-5 笔 loan 的阶段字段 | SQL-15-5 | 验证原始字段到 BPS Stage/Timeline 的一致性 |

### 7.2 SQL-15-1 — Newrez FCL 主表字段存在性

```sql
SELECT table_schema, table_name, column_name, data_type, column_comment
FROM information_schema.columns
WHERE table_schema = 'newrez'
  AND table_name = 'portnewrezfc'
  AND column_name IN (
    'loanid', 'shellpointloanid', 'dataasof', 'state', 'judicial',
    'activefcflag', 'fcreferraldate', 'currentmilestone', 'fcstage',
    'demandsentdate', 'firstlegaldate', 'servicecompletedate',
    'fcjudgmenthearingscheduled', 'fcjudgmententered',
    'fcscheduledsaledate', 'fcsalehelddate', 'fcsaleamount',
    'titlereceiveddate', 'titlecleardate',
    'fchold1description', 'fchold1startdate', 'fchold1enddate',
    'fchold2description', 'fchold2startdate', 'fchold2enddate',
    'fchold3description', 'fchold3startdate', 'fchold3enddate'
  )
ORDER BY ordinal_position;
```

### 7.3 SQL-15-2 — 活跃 FCL 字段填充率刷新

```sql
SELECT
  COUNT(*) AS active_fcl_rows,
  ROUND(SUM(loanid IS NOT NULL) / COUNT(*) * 100, 1) AS loanid_pct,
  ROUND(SUM(dataasof IS NOT NULL) / COUNT(*) * 100, 1) AS dataasof_pct,
  ROUND(SUM(activefcflag IS NOT NULL) / COUNT(*) * 100, 1) AS activefcflag_pct,
  ROUND(SUM(fcreferraldate IS NOT NULL) / COUNT(*) * 100, 1) AS fcreferraldate_pct,
  ROUND(SUM(currentmilestone IS NOT NULL) / COUNT(*) * 100, 1) AS currentmilestone_pct,
  ROUND(SUM(fcstage IS NOT NULL) / COUNT(*) * 100, 1) AS fcstage_pct,
  ROUND(SUM(demandsentdate IS NOT NULL) / COUNT(*) * 100, 1) AS demandsentdate_pct,
  ROUND(SUM(firstlegaldate IS NOT NULL) / COUNT(*) * 100, 1) AS firstlegaldate_pct,
  ROUND(SUM(servicecompletedate IS NOT NULL) / COUNT(*) * 100, 1) AS servicecompletedate_pct,
  ROUND(SUM(fcjudgmenthearingscheduled IS NOT NULL) / COUNT(*) * 100, 1) AS fcjudgmenthearingscheduled_pct,
  ROUND(SUM(fcscheduledsaledate IS NOT NULL) / COUNT(*) * 100, 1) AS fcscheduledsaledate_pct,
  ROUND(SUM(fcsalehelddate IS NOT NULL) / COUNT(*) * 100, 1) AS fcsalehelddate_pct,
  ROUND(SUM(fcsaleamount IS NOT NULL) / COUNT(*) * 100, 1) AS fcsaleamount_pct,
  ROUND(SUM(titlereceiveddate IS NOT NULL) / COUNT(*) * 100, 1) AS titlereceiveddate_pct,
  ROUND(SUM(titlecleardate IS NOT NULL) / COUNT(*) * 100, 1) AS titlecleardate_pct
FROM newrez.portnewrezfc
WHERE dataasof = (SELECT MAX(dataasof) FROM newrez.portnewrezfc)
  AND fcreferraldate IS NOT NULL
  AND COALESCE(activefcflag, 1) = 1;
```

### 7.4 SQL-15-3 — LM 字段覆盖与枚举

```sql
SELECT
  'lmdeal' AS field_name, lmdeal AS field_value, COUNT(*) AS cnt
FROM newrez.portnewrezlm
WHERE dataasof = (SELECT MAX(dataasof) FROM newrez.portnewrezlm)
GROUP BY lmdeal
UNION ALL
SELECT 'lmprogram', lmprogram, COUNT(*)
FROM newrez.portnewrezlm
WHERE dataasof = (SELECT MAX(dataasof) FROM newrez.portnewrezlm)
GROUP BY lmprogram
UNION ALL
SELECT 'lmstatus', lmstatus, COUNT(*)
FROM newrez.portnewrezlm
WHERE dataasof = (SELECT MAX(dataasof) FROM newrez.portnewrezlm)
GROUP BY lmstatus
ORDER BY field_name, cnt DESC;
```

### 7.5 SQL-15-4 — BK 字段与 BPS BK 同步表核对

```sql
SELECT
  bk.bkstatus,
  bk.bkstage,
  COUNT(*) AS raw_rows,
  SUM(bps.loanid IS NOT NULL) AS rows_in_bps_bk
FROM newrez.portnewrezbk bk
LEFT JOIN bpms_dev.sync_loan_foreclosure_bankruptcy bps
  ON bps.loanid COLLATE utf8mb4_general_ci = bk.loanid COLLATE utf8mb4_general_ci
WHERE bk.dataasof = (SELECT MAX(dataasof) FROM newrez.portnewrezbk)
GROUP BY bk.bkstatus, bk.bkstage
ORDER BY raw_rows DESC;
```

### 7.6 SQL-15-5 — BPS Stage 与 Newrez 来源字段样本核对

```sql
SELECT
  s.loanid,
  s.stage,
  s.referral_start_date,
  s.first_legal_start_date,
  s.service_start_date,
  s.judgement_start_date,
  s.sale_start_date,
  fc.fcreferraldate,
  fc.firstlegaldate,
  fc.servicecompletedate,
  fc.fcjudgmenthearingscheduled,
  fc.fcscheduledsaledate
FROM bpms_dev.sync_fcl_stage_info s
JOIN newrez.portnewrezfc fc
  ON s.loanid COLLATE utf8mb4_general_ci = fc.loanid COLLATE utf8mb4_general_ci
WHERE s.servicer = 'Newrez'
  AND s.fctrdt = (SELECT MAX(fctrdt) FROM bpms_dev.sync_fcl_stage_info WHERE servicer = 'Newrez')
  AND fc.dataasof = (SELECT MAX(dataasof) FROM newrez.portnewrezfc)
ORDER BY s.stage, s.loanid
LIMIT 25;
```

## 8. 验证证据

| 证据类型 | 位置 | 覆盖结论 |
|----------|------|----------|
| PrefectFlow 源码 | `flow/basic_data/load_servicer_data_config/servicer_config.py` | Newrez FCL/BK/LM 原始表入库配置存在 |
| PrefectFlow 源码 | `flow/basic_data/basic_data_config/basic_data_pool_config.py` | Newrez FCL 字段归一化、timeline、stage 字段映射存在 |
| PrefectFlow 源码 | `flow/bps/sync_asset_management.py` | FCL Stage 计算使用 `newrez.portnewrezfc` 最大 `dataasof` |
| PrefectFlow 源码 | `flow/bps/bps_config/sync_to_bps_config.py` | Foreclosure/LM/BK/Hold/Stage sync 表配置存在 |
| 文档证据 | doc 13 Section 8 Q1-Q12 | Newrez 主要数据质量问题和已知映射问题 |
| 文档证据 | doc 14 Section 2-4 / 附录 A | 目标字段和 BPS 面板对照标准 |
| 数据库验证计划 | 本文 Section 7 | 后续刷新 Newrez 字段覆盖率、枚举分布、BK 解码和 BPS Stage 样本链路 |

## 9. Open Questions

| 问题 | 为什么重要 | 建议确认对象 |
|------|------------|--------------|
| Newrez 是否能稳定提供 Publication 相关字段？ | 决定 BPS Publication 阶段是否长期为空 | Newrez / BPS 产品 |
| BK 面板 `lien_status`、`claim_status` 来源字段是什么？ | 当前 doc 13 标注待确认，影响 BK 面板字段请求 | ETL/BPS |
| Demand Letter 是否应在 BPS Time Line Tab 显示为 NOI Date？ | 当前 Newrez Demand 日期未进入 `noi_start_date`，可能导致 UI 看起来缺数据 | BPS 产品 |
| `currentmilestone` 与 `fcstage` 冲突时是否永远以 `currentmilestone` 为准？ | 影响 Summary 当前步骤解释 | BPS 运营 / ETL |
