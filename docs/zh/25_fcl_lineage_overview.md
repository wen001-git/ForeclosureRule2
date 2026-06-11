# Doc 25 · 止赎字段血缘 · 总览（hub）

> **自动生成** —— 改动请编辑真源 `outputs/fcl_lineage_source.json`，然后依次重跑：①`python - < scripts/verify_lineage_columns.txt`（生成列核验 SQL，经 `redshift_prod`/`mysql_prod` 跑须 0 行）②`python - < scripts/build_rule_glossary.txt`（刷新规则词典 + 本文附录）③`python - < scripts/inject_glin.txt`（刷新 `outputs/fcl_pipeline.html` 内嵌血缘）。勿手改本文件。（旧生成器 `scripts/gen_fcl_lineage.py` 已废弃删除。）


## 文档目的

止赎核心字段从 Servicer 原始列到 BPS sync 表的**字段级**数据血缘总入口：规范跳链骨架 + 全字段主索引 + 指向各 BPS 表明细文档（doc 26–30）的链接。规则 Code-First 取自 PrefectFlow；列名已对 prod（redshift_prod / mysql_prod）核验。补充 doc 02（表级管道）。取代 doc 21。

## 目标读者

数据工程师 · 分析师 · 校验人员 · 业务分析 · 未来 AI 会话

## 修订历史

| 日期 | 作者 | 版本 | 变更 | 关联 |
|---|---|---|---|---|
| 2026-06-09 | AI Agent | v1 | 初稿：doc 25–30 由 fcl_lineage_source.json 生成（per-field 血缘 + 跳链 + 取数 SQL） | doc 02 · doc 13 · doc 14 |
| 2026-06-09 | AI Agent | v2 | Servicer 分列（Newrez/Carrington/Capecodfive 来源分开） | doc 02 · doc 13 · doc 14 |
| 2026-06-09 | AI Agent | v3 | 非平凡 SQL 加说明 + 计算示例 | doc 02 · doc 13 · doc 14 |
| 2026-06-09 | AI Agent | v4 | 改为每字段竖排卡片，规则写全不省略 | doc 02 · doc 13 · doc 14 |
| 2026-06-09 | AI Agent | v5 | 跳链补 tempfc 行 + 说明 L2/L3 为何不在本分支；字段标题加序号 | doc 02 · doc 13 · doc 14 |
| 2026-06-09 | AI Agent | v6 | 覆盖 BPS sync 表全部列（系统/审计列分组、视图计算列）；每跳加流动顺序 | doc 02 · doc 13 · doc 14 |
| 2026-06-09 | AI Agent | v7 | 为所有字段补中文名/业务含义（DDL 注释 Code-First 提取）；新增修订历史维护 | doc 02 · doc 13 · doc 14 |
| 2026-06-09 | AI Agent | v8 | 为 stage 计算字段补完整逻辑说明+举例（多分支多例）；按 SQL 投影 Code-First 校正 end_date/countdown 跳规则（demand_end=催告到期、referral/first_legal/service_end=下一阶段开始、judgement/sale/noi/publication=NULL）；修正 to_judgement/to_sale 错误示例 | doc 02 · doc 13 · doc 14 |
| 2026-06-09 | AI Agent | v9 | 代码引用 [pool:]/[asset:] 做成可点击 GitLab 链接（fork jli/prefectflow，钉到提交 32a750a3，行号精确稳定）；code legend 文件路径亦可点击；view 视图保留纯文字 | doc 02 · doc 13 · doc 14 |
| 2026-06-10 | AI Agent | v10 | hub 新增「FCL 事实中枢 vs BPS 投影」说明：basic_data_loan_fcl=事实中枢/全历史，**直接派生 foreclosure + fcl_stage_info 两张**；_hold/_bankruptcy/_loss_mitigation/fcl_related 各自从原始 servicer 表并行构建（非 fcl 子表） | doc 02 · doc 13 · doc 14 |

## 相关文档

doc 02（ETL 管道）· doc 13（BPS 视图字段映射）· doc 14（Servicer FCL 字段规范）· doc 26–30（各 sync 表字段血缘）· ~~doc 21~~（已弃用）


---

## 怎么读这套血缘

> 🧬 **表关系入口**：先看 [doc 33 — FCL 表实体关系图](33_fcl_table_erd.md)（PK / 粒度键 / 1:N / N:N 一图看 22 张表布局），再回本文逐字段看跳链。
> 📐 **阶段窗口规则速查**：见 [doc 31](31_fcl_stage_window_rules.md)（start/end/stage_days/in_lm/on_hold 公式 + 4 真实 loan 工作例）。

每个 **BPS sync 表**一篇明细文档（doc 26–30）。每篇里 **一行 = 一个字段**，列 = 该字段在链路上每一张表的列名，最后一列给出**每一跳的转换规则 + 代码出处**（`pool`/`asset`/`view`，见下）。非平凡转换（CASE/解码/unpivot/天数）附真实 SQL。

> code: `pool` = [PrefectFlow/flow/basic_data/basic_data_config/basic_data_pool_config.py](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py) · `asset` = [PrefectFlow/flow/bps/bps_config/asset_managment_config.py](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py) · `view` = bpms.biz_data_view_loan_details_foreclosure (SHOW CREATE VIEW)

> L4 事实表 port.basic_data_loan_fcl 由 3 家 servicer UNION——Newrez(newrez.portnewrezfc)、Carrington(carrington.portcarrington)、Capecodfive。下表 raw 列为 Newrez 来源；Carrington/Capecodfive 差异见各字段 carrington 备注。SLS/MRC 等不上报 FCL 明细（仅逾期推断）。

> **📅 数据日期**：均取自 **prod**（`redshift_prod`/`mysql_prod`），无 dev。样例快照 BPS stage `fctrdt=2026-06-06`、Newrez raw `dataasof=2026-06-07`；FCL 主表/阶段口径最新快照 as-of 2026-06-07。各表 as-of 见 doc 02 头部「数据日期」统一声明。


## 规范跳链骨架（4 条分支）

### 主线（里程碑 / 汇总 / 状态）

**规范跳链 / canonical hop chain**


`newrez.portnewrezfc` → `tempfc.temp_basic_data_fcl` → `port.basic_data_loan_fcl` → `port.basic_data_loan_foreclosure` → `bpms.sync_loan_foreclosure` → `bpms.biz_data_view_loan_details_foreclosure`

| # | layer | db | 表 table | role |
|---|---|---|---|---|
| 1 | L0/L1 | MySQL+Redshift | `newrez.portnewrezfc` | Servicer raw |
| 2 | L4·temp | Redshift | `tempfc.temp_basic_data_fcl` | 3-servicer rename-UNION of L1 raw / 三家 servicer 改名 UNION (CREATE_BASIC_FCL, [pool:1531-1654](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L1531-1654)) |
| 3 | L4 | Redshift | `port.basic_data_loan_fcl` | canonical FCL fact |
| 4 | L4 | Redshift→MySQL | `port.basic_data_loan_foreclosure` | timeline+summary build (GEN_FCL_DETAIL) |
| 5 | L5 | MySQL bpms | `bpms.sync_loan_foreclosure` | BPS app table (UPDATE_FORECLOSURE upsert) |
| 6 | L5 | MySQL bpms | `bpms.biz_data_view_loan_details_foreclosure` | display view (Actual/Var days) |

### 阶段 / 天数

> 📐 **规则速查**：见 [doc 31 — FCL 阶段窗口规则](31_fcl_stage_window_rules.md)——一表读懂每个 stage 的 `start_date` 来源、`end_date` 派生规则、`stage_days` 公式、`in_lm_days`/`on_hold_days` SQL 语义 + 4 真实 loan 工作例 + 反直觉点（`servicecompletedate` → SERVICE start 不是 end）。

**规范跳链 / canonical hop chain**


`newrez.portnewrezfc` → `tempfc.temp_basic_data_fcl` → `port.basic_data_loan_fcl` → `port.fcl_stage_info` → `bpms.sync_fcl_stage_info`

| # | layer | db | 表 table | role |
|---|---|---|---|---|
| 1 | L0/L1 | MySQL+Redshift | `newrez.portnewrezfc` | Servicer raw |
| 2 | L4·temp | Redshift | `tempfc.temp_basic_data_fcl` | 3-servicer rename-UNION of L1 raw / 三家 servicer 改名 UNION (CREATE_BASIC_FCL, [pool:1531-1654](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L1531-1654)) |
| 3 | L4 | Redshift | `port.basic_data_loan_fcl` | canonical FCL fact |
| 4 | L4 | Redshift | `port.fcl_stage_info` | stage classification + day-math (GEN_FCL_STAGE); group/state from port.basic_data_fcl_related |
| 5 | L5 | MySQL bpms | `bpms.sync_fcl_stage_info` | BPS app table (12-FCL_STAGE sync, keeps fctrdt history) |

### Hold（宽表→长表 unpivot）

**规范跳链 / canonical hop chain**


`newrez.portnewrezfc (fchold1..4 slots)` → `port.basic_data_loan_foreclosure_hold` → `bpms.sync_loan_foreclosure_hold`

| # | layer | db | 表 table | role |
|---|---|---|---|---|
| 1 | L0/L1 | MySQL+Redshift | `newrez.portnewrezfc (fchold1..4 slots)` | Servicer raw |
| 2 | L4 | Redshift | `port.basic_data_loan_foreclosure_hold` | wide description1..3 (+ Carrington slot4); deduped roll-up of *_hold_detail |
| 3 | L5 | MySQL bpms | `bpms.sync_loan_foreclosure_hold` | long rows via UNION ALL unpivot (GEN_FORECLOSURE_HOLD) |

### 损失缓释（编码→文本解码）

**规范跳链 / canonical hop chain**


`newrez.portnewrezlm` → `port.basic_data_loan_foreclosure_loss_mitigation` → `bpms.sync_loan_foreclosure_loss_mitigation`

| # | layer | db | 表 table | role |
|---|---|---|---|---|
| 1 | L0/L1 | MySQL+Redshift | `newrez.portnewrezlm` | Servicer raw (coded) |
| 2 | L4 | Redshift | `port.basic_data_loan_foreclosure_loss_mitigation` | datadic decode (COALESCE(desc, code)); dedup latest per loan+cycle |
| 3 | L5 | MySQL bpms | `bpms.sync_loan_foreclosure_loss_mitigation` | BPS app table (GEN_FORECLOSURE_LM pass-through) |

### 破产（编码→文本解码）

**规范跳链 / canonical hop chain**


`newrez.portnewrezbk (+ portnewrezgeneral.legalstatus)` → `port.basic_data_loan_foreclosure_bankruptcy` → `bpms.sync_loan_foreclosure_bankruptcy`

| # | layer | db | 表 table | role |
|---|---|---|---|---|
| 1 | L0/L1 | MySQL+Redshift | `newrez.portnewrezbk (+ portnewrezgeneral.legalstatus)` | Servicer raw (coded) |
| 2 | L4 | Redshift | `port.basic_data_loan_foreclosure_bankruptcy` | datadic decode; dedup latest per loan+filing |
| 3 | L5 | MySQL bpms | `bpms.sync_loan_foreclosure_bankruptcy` | BPS app table (GEN_FORECLOSURE_BK pass-through) |

> `#` 列是序号，不是层号。FCL 事实表 `port.basic_data_loan_fcl` 直接由 L1 各 servicer 原始表构建（在 `tempfc.temp_basic_data_fcl` 中 UNION；CREATE_BASIC_FCL [pool:1531-1654](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L1531-1654)），因此 L2 统一日表（`port.basic_data_daily_loan_common`）与 L3 清洗层（`basic_data_daily_loan_common_clean` / `basic_data_loan_delinq_clean`）按设计不在本分支——它们承载通用+逾期字段，仅经 `group` 维度（doc 27，`basic_data_fcl_related`）与月度 `portmonth` 路径回流。完整 L0–L5 管道见 doc 02。

> datadic 解码模式（LM deal/program/status/decision/denial/borrower、BK status）：COALESCE((SELECT description FROM newrez.portnewrezdatadic WHERE field_name='<X>' AND code=CONCAT(raw,'.0')), raw)——原始码存为 '5.0' 形式；字典无匹配则回退原始码。


## FCL 事实中枢 vs BPS 投影（`basic_data_loan_fcl` vs `basic_data_loan_foreclosure`）

> 二者**不重复**，是父（事实中枢）子（BPS 投影）关系。**`basic_data_loan_fcl`＝FCL 事实/明细中枢**：三家 servicer 原始 FCL 表 UNION（经 `tempfc.temp_basic_data_fcl`，**直接由 L1 原始表构建、绕过 L2/L3**）+ 4 个 Hold 槽；保留每日快照全历史、含全部原始 FCL 字段（[pool:1658](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L1658)）。**它直接派生 `basic_data_loan_foreclosure` 与 `fcl_stage_info` 两张**：foreclosure 取数 [pool:287-304](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L287-304)，是 `bpms.sync_loan_foreclosure` 的直接上游、属 BPS 投影（只留每家最新快照 + 里程碑首次日 + 整形成 BPS 契约列 timeline_*/target_*/variance_*/bid_*/summary_*）。链：三家原始表 → temp_basic_data_fcl → basic_data_loan_fcl(事实中枢) → basic_data_loan_foreclosure(BPS投影) → sync → 视图。⚠️ 同属 FCL 业务族的 `_hold`、`_bankruptcy`(←portnewrezbk)、`_loss_mitigation`(←portnewrezlm)、`basic_data_fcl_related`(←portnewrezgeneral) **各自从原始 servicer 表并行构建、并非 fcl 的子表**；`basic_data_loan_reo` 在别处维护。命名提醒：更原始/全的反而叫 `_fcl`，按 BPS 塑形的叫 `_foreclosure`。


## 全字段主索引

| 字段 Field | Servicer 原始列 | BPS sync 表 | 最终 BPS 列 + 明细文档 |
|---|---|---|---|
| id 主键 | `id` | `sync_loan_foreclosure` | `id` (→ doc 26) |
| bid_id 交易ID | `dealid` | `sync_loan_foreclosure` | `bid_id` (→ doc 26) |
| funding_id 资金ID | `fundingid` | `sync_loan_foreclosure` | `funding_id` (→ doc 26) |
| 投资人贷款 ID | `loanid` | `sync_loan_foreclosure` | `loanid` (→ doc 26) |
| 服务商贷款 ID | `shellpointloanid` | `sync_loan_foreclosure` | `svcloanid` (→ doc 26) |
| servicer 服务商 | `constant 'Newrez'/'Carrington'/'Capecodfive'` | `sync_loan_foreclosure` | `servicer` (→ doc 26) |
| Notice of Intent 通知意向日 | `—` | `sync_loan_foreclosure` | `timeline_notice_of_intent_date` (→ doc 26) |
| 通知意向结束日期 | `timeline_notice_of_intent_end_date` | `sync_loan_foreclosure` | `timeline_notice_of_intent_end_date` (→ doc 26) |
| 批准转交日期 | `timeline_approved_for_referral_date` | `sync_loan_foreclosure` | `timeline_approved_for_referral_date` (→ doc 26) |
| 转交律师日期 | `timeline_referred_to_attorney_date` | `sync_loan_foreclosure` | `timeline_referred_to_attorney_date` (→ doc 26) |
| Referred to Foreclosure 转介止赎 | `fcreferraldate` | `sync_loan_foreclosure` | `timeline_referred_to_foreclosure_date` (→ doc 26) |
| Title Report Received 收到产权报告 | `titlereceiveddate` | `sync_loan_foreclosure` | `timeline_title_report_received_date` (→ doc 26) |
| Preliminary Title Cleared 初步产权清查 | `titlecleardate` | `sync_loan_foreclosure` | `timeline_preliminary_title_cleared_date` (→ doc 26) |
| 1st Legal 首次法律行动 | `firstlegaldate` | `sync_loan_foreclosure` | `timeline_first_legal_date` (→ doc 26) |
| Service Complete 送达完成 | `servicecompletedate` | `sync_loan_foreclosure` | `timeline_service_date` (→ doc 26) |
| 止赎公告计划发布日期 | `timeline_publication_date` | `sync_loan_foreclosure` | `timeline_publication_date` (→ doc 26) |
| Judgement Hearing Set 听证排定(首见) | `fcjudgmenthearingscheduled` | `sync_loan_foreclosure` | `timeline_judgement_hearing_set_date` (→ doc 26) |
| Judgement 判决(当前排定听证日) | `fcjudgmenthearingscheduled` | `sync_loan_foreclosure` | `timeline_judgement_date` (→ doc 26) |
| Sale Date Projected 预计拍卖日 | `fcscheduledsaledate` | `sync_loan_foreclosure` | `timeline_sale_date_projected_date` (→ doc 26) |
| Sale Date Set 拍卖排定(首见) | `fcscheduledsaledate` | `sync_loan_foreclosure` | `timeline_sale_date_set_date` (→ doc 26) |
| Final Title Cleared 最终产权清查 | `titlecleardate` | `sync_loan_foreclosure` | `timeline_final_title_cleared_date` (→ doc 26) |
| Sale Held 实际拍卖 | `fcsalehelddate` | `sync_loan_foreclosure` | `timeline_sale_date_held_date` (→ doc 26) |
| 止赎完成日期 | `timeline_foreclosure_completed_date` | `sync_loan_foreclosure` | `timeline_foreclosure_completed_date` (→ doc 26) |
| 第三方成交日 | `—` | `sync_loan_foreclosure` | `timeline_third_party_sold_date_date` (→ doc 26) |
| 第三方拍卖款到账日 | `fcl3rdpartyproceedsreceiveddate` | `sync_loan_foreclosure` | `timeline_third_party_proceeds_received_date` (→ doc 26) |
| 通知意向目标天数，默认值：30 | `target_notice_of_intent_days` | `sync_loan_foreclosure` | `target_notice_of_intent_days` (→ doc 26) |
| 通知意向过期目标天数，默认值：90 | `target_notice_of_intent_expired_days` | `sync_loan_foreclosure` | `target_notice_of_intent_expired_days` (→ doc 26) |
| 批准转交目标天数，默认值：30 | `target_approved_for_referral_days` | `sync_loan_foreclosure` | `target_approved_for_referral_days` (→ doc 26) |
| 转交律师目标天数，默认值：1 | `target_referred_to_attorney_days` | `sync_loan_foreclosure` | `target_referred_to_attorney_days` (→ doc 26) |
| 转交止赎目标天数，默认值：1 | `target_referred_to_foreclosure_days` | `sync_loan_foreclosure` | `target_referred_to_foreclosure_days` (→ doc 26) |
| 收到产权报告目标天数，默认值：30 | `target_title_report_received_days` | `sync_loan_foreclosure` | `target_title_report_received_days` (→ doc 26) |
| 初步产权清理完成目标天数，默认值：30 | `target_preliminary_title_cleared_days` | `sync_loan_foreclosure` | `target_preliminary_title_cleared_days` (→ doc 26) |
| 初次法律行动目标天数，默认值：120 | `target_first_legal_days` | `sync_loan_foreclosure` | `target_first_legal_days` (→ doc 26) |
| 服务完成目标天数，默认值：90 | `target_service_days` | `sync_loan_foreclosure` | `target_service_days` (→ doc 26) |
| publication目标天数，默认值：30 | `target_publication_days` | `sync_loan_foreclosure` | `target_publication_days` (→ doc 26) |
| 判决听证会设置目标天数，默认值：120 | `target_judgement_hearing_set_days` | `sync_loan_foreclosure` | `target_judgement_hearing_set_days` (→ doc 26) |
| 判决发布目标天数，默认值：30 | `target_judgement_days` | `sync_loan_foreclosure` | `target_judgement_days` (→ doc 26) |
| 实际设定出售目标天数，默认值：30 | `target_sale_date_set_days` | `sync_loan_foreclosure` | `target_sale_date_set_days` (→ doc 26) |
| 最终产权清理完成目标天数，默认值：5 | `target_final_title_cleared_days` | `sync_loan_foreclosure` | `target_final_title_cleared_days` (→ doc 26) |
| 实际出售目标天数，默认值：0 | `target_sale_date_held_days` | `sync_loan_foreclosure` | `target_sale_date_held_days` (→ doc 26) |
| 当前破产标志，1 表示是，0 表示否 | `variance_active_bankruptcy` | `sync_loan_foreclosure` | `variance_active_bankruptcy` (→ doc 26) |
| 完成破产标志，1 表示是，0 表示否 | `variance_completed_bankruptcy` | `sync_loan_foreclosure` | `variance_completed_bankruptcy` (→ doc 26) |
| 预计持有天数 | `variance_estimated_hold_days` | `sync_loan_foreclosure` | `variance_estimated_hold_days` (→ doc 26) |
| 破产总数 | `variance_bankruptcies` | `sync_loan_foreclosure` | `variance_bankruptcies` (→ doc 26) |
| 审批状态 | `bid_approval_status` | `sync_loan_foreclosure` | `bid_approval_status` (→ doc 26) |
| 销售日期 | `bid_approval_sale_date` | `sync_loan_foreclosure` | `bid_approval_sale_date` (→ doc 26) |
| 投标金额 | `fcbidamount` | `sync_loan_foreclosure` | `bid_approval_bid_amount` (→ doc 26) |
| 贷款决议阻滞说明 | `bid_approval_loan_resolution_holods` | `sync_loan_foreclosure` | `bid_approval_loan_resolution_holods` (→ doc 26) |
| 服务商编号标识 | `summary_servicer_number` | `sync_loan_foreclosure` | `summary_servicer_number` (→ doc 26) |
| Foreclosure Status 止赎状态 | `activefcflag + fcremovaldesc` | `sync_loan_foreclosure` | `summary_foreclosure_status` (→ doc 26) |
| 完成止赎标志 | `summary_completed_foreclosure` | `sync_loan_foreclosure` | `summary_completed_foreclosure` (→ doc 26) |
| 止赎竞价金额 | `fcbidamount` | `sync_loan_foreclosure` | `summary_foreclosure_bid_amount` (→ doc 26) |
| 服务商止赎竞价金额 | `fcbidamount` | `sync_loan_foreclosure` | `summary_srv_fc_bid_amount` (→ doc 26) |
| 止赎成交金额 | `fcsaleamount` | `sync_loan_foreclosure` | `summary_foreclosure_sale_amount` (→ doc 26) |
| Judicial Foreclosure 司法标志 | `judicial` | `sync_loan_foreclosure` | `summary_judicial_foreclosure` (→ doc 26) |
| 止赎律师姓名 | `summary_foreclosure_attorney` | `sync_loan_foreclosure` | `summary_foreclosure_attorney` (→ doc 26) |
| Contested / Litigation 争议诉讼 | `fccontestedflag` | `sync_loan_foreclosure` | `summary_contested_litigation` (→ doc 26) |
| Firm 律所 | `fcfirm` | `sync_loan_foreclosure` | `summary_firm` (→ doc 26) |
| Type 司法/非司法 | `judicial` | `sync_loan_foreclosure` | `summary_type` (→ doc 26) |
| SMS Days in FCL (servicer 口径) | `smsdaysinfc` | `sync_loan_foreclosure` | `summary_sms_days_in_fcl` (→ doc 26) |
| Days in FCL (投资人口径) | `daysinfc` | `sync_loan_foreclosure` | `summary_days_in_fcl` (→ doc 26) |
| Current Step 当前阶段 | `fcstage` | `sync_loan_foreclosure` | `summary_current_step` (→ doc 26) |
| Last Step Completed 最近完成步骤 | `lastfcstepcompleted` | `sync_loan_foreclosure` | `summary_last_step_completed` (→ doc 26) |
| 最近完成步骤日期 | `lastfcstepcompleteddate` | `sync_loan_foreclosure` | `summary_last_step_completed_date` (→ doc 26) |
| 系统 / 审计列 | `create_user, create_dept, create_time, update_user, update_time, status, is_deleted, tenant_id` | `sync_loan_foreclosure` | `create_user, create_dept, create_time, update_user, update_time, status, is_deleted, tenant_id` (→ doc 26) |
| id 主键 | `id` | `sync_fcl_stage_info` | `id` (→ doc 27) |
| stage 当前阶段分类 | `(stage dates)` | `sync_fcl_stage_info` | `stage` (→ doc 27) |
| fctrdt 报告快照日 | `dataasof` | `sync_fcl_stage_info` | `fctrdt` (→ doc 27) |
| 投资人贷款 ID | `loanid` | `sync_fcl_stage_info` | `loanid` (→ doc 27) |
| Group 分组（FCL/D120P/D90/REO/P） | `delinquency_status_mba (+ portnewrezpmt.nextduedate)` | `sync_fcl_stage_info` | `group` (→ doc 27) |
| servicer 服务商 | `constant 'Newrez'/'Carrington'/'Capecodfive'` | `sync_fcl_stage_info` | `servicer` (→ doc 27) |
| State 州 | `propertystate` | `sync_fcl_stage_info` | `state` (→ doc 27) |
| Judicial 司法(Y/N) | `judicial (+ propertystate)` | `sync_fcl_stage_info` | `judicial` (→ doc 27) |
| 催告/Demand 阶段开始日 | `demandsentdate` | `sync_fcl_stage_info` | `demand_start_date` (→ doc 27) |
| 催告/Demand 阶段结束日(窗口) | `—` | `sync_fcl_stage_info` | `demand_end_date` (→ doc 27) |
| 催告/Demand 阶段已历天数 | `—` | `sync_fcl_stage_info` | `demand_stage_days` (→ doc 27) |
| 催告/Demand 阶段内 LM 天数 | `—` | `sync_fcl_stage_info` | `demand_in_lm_days` (→ doc 27) |
| 催告/Demand 阶段内 Hold 天数 | `—` | `sync_fcl_stage_info` | `demand_on_hold_days` (→ doc 27) |
| NOI 阶段开始日 | `noi_start_date` | `sync_fcl_stage_info` | `noi_start_date` (→ doc 27) |
| NOI 阶段结束日(窗口) | `—` | `sync_fcl_stage_info` | `noi_end_date` (→ doc 27) |
| NOI 阶段已历天数 | `noi_stage_days` | `sync_fcl_stage_info` | `noi_stage_days` (→ doc 27) |
| NOI 阶段内 LM 天数 | `—` | `sync_fcl_stage_info` | `noi_in_lm_days` (→ doc 27) |
| NOI 阶段内 Hold 天数 | `—` | `sync_fcl_stage_info` | `noi_on_hold_days` (→ doc 27) |
| 转介 阶段开始日 | `fcreferraldate` | `sync_fcl_stage_info` | `referral_start_date` (→ doc 27) |
| 转介 阶段结束日(窗口) | `—` | `sync_fcl_stage_info` | `referral_end_date` (→ doc 27) |
| 转介 阶段已历天数 | `—` | `sync_fcl_stage_info` | `referral_stage_days` (→ doc 27) |
| 转介 阶段内 LM 天数 | `—` | `sync_fcl_stage_info` | `referral_in_lm_days` (→ doc 27) |
| 转介 阶段内 Hold 天数 | `—` | `sync_fcl_stage_info` | `referral_on_hold_days` (→ doc 27) |
| 首次法律 阶段开始日 | `firstlegaldate` | `sync_fcl_stage_info` | `first_legal_start_date` (→ doc 27) |
| 首次法律 阶段结束日(窗口) | `—` | `sync_fcl_stage_info` | `first_legal_end_date` (→ doc 27) |
| 首次法律 阶段已历天数 | `—` | `sync_fcl_stage_info` | `first_legal_stage_days` (→ doc 27) |
| 首次法律 阶段内 LM 天数 | `—` | `sync_fcl_stage_info` | `first_legal_in_lm_days` (→ doc 27) |
| 首次法律 阶段内 Hold 天数 | `—` | `sync_fcl_stage_info` | `first_legal_on_hold_days` (→ doc 27) |
| 首次法律日(首见追踪) | `firstlegaldate` | `sync_fcl_stage_info` | `first_legal_date_history` (→ doc 27) |
| 送达 阶段开始日 | `servicecompletedate` | `sync_fcl_stage_info` | `service_start_date` (→ doc 27) |
| 送达 阶段结束日(窗口) | `—` | `sync_fcl_stage_info` | `service_end_date` (→ doc 27) |
| 送达 阶段已历天数 | `—` | `sync_fcl_stage_info` | `service_stage_days` (→ doc 27) |
| 送达 阶段内 LM 天数 | `—` | `sync_fcl_stage_info` | `service_in_lm_days` (→ doc 27) |
| 送达 阶段内 Hold 天数 | `—` | `sync_fcl_stage_info` | `service_on_hold_days` (→ doc 27) |
| 公告 阶段开始日 | `publication_start_date` | `sync_fcl_stage_info` | `publication_start_date` (→ doc 27) |
| 公告 阶段结束日(窗口) | `—` | `sync_fcl_stage_info` | `publication_end_date` (→ doc 27) |
| 公告 阶段已历天数 | `publication_stage_days` | `sync_fcl_stage_info` | `publication_stage_days` (→ doc 27) |
| 公告 阶段内 LM 天数 | `—` | `sync_fcl_stage_info` | `publication_in_lm_days` (→ doc 27) |
| 公告 阶段内 Hold 天数 | `—` | `sync_fcl_stage_info` | `publication_on_hold_days` (→ doc 27) |
| 判决 阶段开始日 | `fcjudgmenthearingscheduled` | `sync_fcl_stage_info` | `judgement_start_date` (→ doc 27) |
| 判决 阶段结束日(窗口) | `—` | `sync_fcl_stage_info` | `judgement_end_date` (→ doc 27) |
| 距判决倒计天数 | `fcjudgmenthearingscheduled` | `sync_fcl_stage_info` | `to_judgement_days` (→ doc 27) |
| 判决 阶段内 LM 天数 | `—` | `sync_fcl_stage_info` | `judgement_in_lm_days` (→ doc 27) |
| 判决 阶段内 Hold 天数 | `—` | `sync_fcl_stage_info` | `judgement_on_hold_days` (→ doc 27) |
| 拍卖 阶段开始日 | `fcscheduledsaledate` | `sync_fcl_stage_info` | `sale_start_date` (→ doc 27) |
| 拍卖 阶段结束日(窗口) | `—` | `sync_fcl_stage_info` | `sale_end_date` (→ doc 27) |
| 距拍卖倒计天数 | `fcscheduledsaledate` | `sync_fcl_stage_info` | `to_sale_days` (→ doc 27) |
| 拍卖 阶段内 LM 天数 | `—` | `sync_fcl_stage_info` | `sale_in_lm_days` (→ doc 27) |
| 拍卖 阶段内 Hold 天数 | `—` | `sync_fcl_stage_info` | `sale_on_hold_days` (→ doc 27) |
| 系统 / 审计列 | `create_time, update_time, create_user, create_dept, update_user, status, is_deleted, tenant_id` | `sync_fcl_stage_info` | `create_time, update_time, create_user, create_dept, update_user, status, is_deleted, tenant_id` (→ doc 27) |
| id 主键 | `id` | `sync_loan_foreclosure_hold` | `id` (→ doc 28) |
| 投资人贷款 ID | `loanid` | `sync_loan_foreclosure_hold` | `loanid` (→ doc 28) |
| 服务商贷款 ID | `shellpointloanid` | `sync_loan_foreclosure_hold` | `svcloanid` (→ doc 28) |
| fctrdt 报告快照日 | `dataasof` | `sync_loan_foreclosure_hold` | `fctrdt` (→ doc 28) |
| Hold 描述（暂停原因） | `fchold1..3 description` | `sync_loan_foreclosure_hold` | `description` (→ doc 28) |
| Hold 开始日 | `fchold1..3 startdate` | `sync_loan_foreclosure_hold` | `description_start_date` (→ doc 28) |
| Hold 结束日 | `fchold1..3 enddate` | `sync_loan_foreclosure_hold` | `description_end_date` (→ doc 28) |
| 系统 / 审计列 | `create_user, create_dept, create_time, update_user, update_time, status, is_deleted, tenant_id` | `sync_loan_foreclosure_hold` | `create_user, create_dept, create_time, update_user, update_time, status, is_deleted, tenant_id` (→ doc 28) |
| id 主键 | `id` | `sync_loan_foreclosure_loss_mitigation` | `id` (→ doc 29) |
| 投资人贷款 ID | `loanid` | `sync_loan_foreclosure_loss_mitigation` | `loanid` (→ doc 29) |
| 服务商贷款 ID | `shellpointloanid` | `sync_loan_foreclosure_loss_mitigation` | `svcloanid` (→ doc 29) |
| fctrdt 报告快照日 | `dataasof` | `sync_loan_foreclosure_loss_mitigation` | `fctrdt` (→ doc 29) |
| Deal 交易类型 | `lmdeal (code)` | `sync_loan_foreclosure_loss_mitigation` | `deal` (→ doc 29) |
| Program 方案 | `lmprogram (code)` | `sync_loan_foreclosure_loss_mitigation` | `program` (→ doc 29) |
| Status 状态 | `lmstatus (code)` | `sync_loan_foreclosure_loss_mitigation` | `lmc_status` (→ doc 29) |
| Cycle Opened Date 周期开启日 | `dealstartdate` | `sync_loan_foreclosure_loss_mitigation` | `cycle_opened_date` (→ doc 29) |
| Cycle Closed Date 周期关闭日 | `lmremovaldate` | `sync_loan_foreclosure_loss_mitigation` | `cycle_closed_date` (→ doc 29) |
| Final Disposition 最终处置 | `lmdecision (code)` | `sync_loan_foreclosure_loss_mitigation` | `final_disposition` (→ doc 29) |
| Denial / Reason 拒绝原因 | `denialreason (code)` | `sync_loan_foreclosure_loss_mitigation` | `denialreason` (→ doc 29) |
| Borrower Intentions 借款人意向 | `borrowerintention (code)` | `sync_loan_foreclosure_loss_mitigation` | `borrower_intentions` (→ doc 29) |
| 即将违约标志 | `—` | `sync_loan_foreclosure_loss_mitigation` | `imminent_default` (→ doc 29) |
| 单一联系人(SPOC) | `—` | `sync_loan_foreclosure_loss_mitigation` | `single_point_of_contact` (→ doc 29) |
| 系统 / 审计列 | `create_user, create_dept, create_time, update_user, update_time, status, is_deleted, tenant_id` | `sync_loan_foreclosure_loss_mitigation` | `create_user, create_dept, create_time, update_user, update_time, status, is_deleted, tenant_id` (→ doc 29) |
| id 主键 | `id` | `sync_loan_foreclosure_bankruptcy` | `id` (→ doc 30) |
| 投资人贷款 ID | `loanid` | `sync_loan_foreclosure_bankruptcy` | `loanid` (→ doc 30) |
| 服务商贷款 ID | `shellpointloanid` | `sync_loan_foreclosure_bankruptcy` | `svcloanid` (→ doc 30) |
| fctrdt 报告快照日 | `dataasof` | `sync_loan_foreclosure_bankruptcy` | `fctrdt` (→ doc 30) |
| Bankruptcy Status 破产状态 | `bkstatus (code)` | `sync_loan_foreclosure_bankruptcy` | `bankruptcy_status` (→ doc 30) |
| Legal Status 法律状态 | `legalstatus` | `sync_loan_foreclosure_bankruptcy` | `legal_status` (→ doc 30) |
| Status Date 状态日(申请日) | `bkfileddate` | `sync_loan_foreclosure_bankruptcy` | `status_date` (→ doc 30) |
| Chapter 章节 | `bkchapter` | `sync_loan_foreclosure_bankruptcy` | `chapter` (→ doc 30) |
| 留置状态 | `(none for Newrez)` | `sync_loan_foreclosure_bankruptcy` | `lien_status` (→ doc 30) |
| 解除自动中止(MFR)状态 | `(none for Newrez)` | `sync_loan_foreclosure_bankruptcy` | `mfr_status` (→ doc 30) |
| MFR 申请日 | `(none for Newrez)` | `sync_loan_foreclosure_bankruptcy` | `mfr_filed_date` (→ doc 30) |
| 债权状态 | `(none for Newrez)` | `sync_loan_foreclosure_bankruptcy` | `claim_status` (→ doc 30) |
| Proof of Claim Date 债权申报日 | `pocfileddate` | `sync_loan_foreclosure_bankruptcy` | `proof_of_claim_date` (→ doc 30) |
| 破产后应付日 | `bkpostpetitionduedate` | `sync_loan_foreclosure_bankruptcy` | `post_petition_due_date` (→ doc 30) |
| 系统 / 审计列 | `create_user, create_dept, create_time, update_user, update_time, status, is_deleted, tenant_id` | `sync_loan_foreclosure_bankruptcy` | `create_user, create_dept, create_time, update_user, update_time, status, is_deleted, tenant_id` (→ doc 30) |
| 视图计算列（Actual / Variance / 合计） | `actual_<stage>_days / var_<stage>_days / target_total / actual_total / var_total` | `sync_loan_foreclosure` | `actual_<stage>_days / var_<stage>_days / target_total / actual_total / var_total` (→ doc 26) |


## 已知缺口 / 空值字段

| 字段 | status | 说明 |
|---|---|---|
| Notice of Intent 通知意向日 | `newrez_null` | Newrez 无 NOI 源 → 恒空；仅 Capecodfive 填充。 |
| 通知意向结束日期 | `null_in_build` |  |
| 批准转交日期 | `null_in_build` |  |
| 转交律师日期 | `null_in_build` |  |
| Title Report Received 收到产权报告 | `newrez_empty` | Newrez 实测不填充（活跃 FCL ~0%）。 |
| Preliminary Title Cleared 初步产权清查 | `newrez_empty` | 与 Final Title Cleared 共用 titlecleardate；Newrez 不填充。 |
| 止赎公告计划发布日期 | `null_in_build` |  |
| Final Title Cleared 最终产权清查 | `newrez_empty` | 与 Preliminary 共用 titlecleardate；Newrez 不填充。 |
| 止赎完成日期 | `null_in_build` |  |
| 第三方成交日 | `null_in_build` | GEN_FCL_DETAIL 中硬编码 NULL（此处未从 raw 映射）。 |
| 第三方拍卖款到账日 | `newrez_empty` |  |
| 通知意向目标天数，默认值：30 | `view_default` | sync 中存 NULL；视图给默认 target（如 first_legal 120、service 90、judgement 30）。 |
| 通知意向过期目标天数，默认值：90 | `view_default` | sync 中存 NULL；视图给默认 target（如 first_legal 120、service 90、judgement 30）。 |
| 批准转交目标天数，默认值：30 | `view_default` | sync 中存 NULL；视图给默认 target（如 first_legal 120、service 90、judgement 30）。 |
| 转交律师目标天数，默认值：1 | `view_default` | sync 中存 NULL；视图给默认 target（如 first_legal 120、service 90、judgement 30）。 |
| 转交止赎目标天数，默认值：1 | `view_default` | sync 中存 NULL；视图给默认 target（如 first_legal 120、service 90、judgement 30）。 |
| 收到产权报告目标天数，默认值：30 | `view_default` | sync 中存 NULL；视图给默认 target（如 first_legal 120、service 90、judgement 30）。 |
| 初步产权清理完成目标天数，默认值：30 | `view_default` | sync 中存 NULL；视图给默认 target（如 first_legal 120、service 90、judgement 30）。 |
| 初次法律行动目标天数，默认值：120 | `view_default` | sync 中存 NULL；视图给默认 target（如 first_legal 120、service 90、judgement 30）。 |
| 服务完成目标天数，默认值：90 | `view_default` | sync 中存 NULL；视图给默认 target（如 first_legal 120、service 90、judgement 30）。 |
| publication目标天数，默认值：30 | `view_default` | sync 中存 NULL；视图给默认 target（如 first_legal 120、service 90、judgement 30）。 |
| 判决听证会设置目标天数，默认值：120 | `view_default` | sync 中存 NULL；视图给默认 target（如 first_legal 120、service 90、judgement 30）。 |
| 判决发布目标天数，默认值：30 | `view_default` | sync 中存 NULL；视图给默认 target（如 first_legal 120、service 90、judgement 30）。 |
| 实际设定出售目标天数，默认值：30 | `view_default` | sync 中存 NULL；视图给默认 target（如 first_legal 120、service 90、judgement 30）。 |
| 最终产权清理完成目标天数，默认值：5 | `view_default` | sync 中存 NULL；视图给默认 target（如 first_legal 120、service 90、judgement 30）。 |
| 实际出售目标天数，默认值：0 | `view_default` | sync 中存 NULL；视图给默认 target（如 first_legal 120、service 90、judgement 30）。 |
| 当前破产标志，1 表示是，0 表示否 | `null_in_build` |  |
| 完成破产标志，1 表示是，0 表示否 | `null_in_build` |  |
| 预计持有天数 | `null_in_build` |  |
| 破产总数 | `null_in_build` |  |
| 审批状态 | `null_in_build` |  |
| 销售日期 | `null_in_build` |  |
| 贷款决议阻滞说明 | `null_in_build` |  |
| 服务商编号标识 | `null_in_build` |  |
| 完成止赎标志 | `null_in_build` |  |
| 止赎律师姓名 | `null_in_build` |  |
| NOI 阶段开始日 | `null_in_build` | NOI 阶段在 business_1 CTE 未填充（硬编码 NULL）；NOI 活动并入 DEMAND 窗口表示。prod 全量实测为 NULL。 |
| NOI 阶段结束日(窗口) | `null_in_build` | 硬编码 NULL（见 noi_start_date）。prod 全量实测为 NULL。 |
| NOI 阶段已历天数 | `null_in_build` | 硬编码 NULL——不计算 NOI 窗口。prod 全量实测为 NULL。 |
| 公告 阶段开始日 | `null_in_build` | 公告阶段在 business_1 未填充（硬编码 NULL）。prod 全量实测为 NULL。 |
| 公告 阶段结束日(窗口) | `null_in_build` | 硬编码 NULL（见 publication_start_date）。prod 全量实测为 NULL。 |
| 公告 阶段已历天数 | `null_in_build` | 硬编码 NULL——不计算公告窗口。prod 全量实测为 NULL。 |
| 即将违约标志 | `newrez_null` | Newrez 硬编码 NULL。 |
| 单一联系人(SPOC) | `newrez_null` | Newrez 硬编码 NULL。 |
| 留置状态 | `newrez_null` |  |
| 解除自动中止(MFR)状态 | `newrez_null` |  |
| MFR 申请日 | `newrez_null` |  |
| 债权状态 | `newrez_null` |  |

> 此外：L3 中间表 `port.basic_data_loan_delinq_clean` 的生产代码不在 PrefectFlow 仓库内（仅按名引用）；SLS/MRC 等 servicer 不上报 FCL 明细。


## 端到端样例（MCP 实测）

用一个真实贷款把两个里程碑字段端到端追踪；每一跳取值一致（已对 redshift_prod 与 mysql_prod 用 MCP 实测）。

**转介止赎 Referral** — loan `7727004408`

| hop | table.column | value |
|---|---|---|
| L1 raw | `newrez.portnewrezfc.fcreferraldate` | `2024-03-08` |
| L4 fact | `port.basic_data_loan_fcl.referral_start_date` | `2024-03-08` |
| L4 | `port.basic_data_loan_foreclosure.timeline_referred_to_foreclosure_date` | `2024-03-08` |
| L5 BPS | `bpms.sync_loan_foreclosure.timeline_referred_to_foreclosure_date` | `2024-03-08` |

**判决（排定听证日）** — loan `7727004408`

| hop | table.column | value |
|---|---|---|
| L1 raw | `newrez.portnewrezfc.fcjudgmenthearingscheduled` | `2026-08-21` |
| L4 fact | `port.basic_data_loan_fcl.fcjudgment_hearing_scheduled` | `2026-08-21` |
| L4 | `port.basic_data_loan_foreclosure.timeline_judgement_date` | `2026-08-21` |
| L5 BPS | `bpms.sync_loan_foreclosure.timeline_judgement_date` | `2026-08-21` |


## 各 BPS 表明细文档

- **doc 26** — `bpms.sync_loan_foreclosure` (主线（里程碑 / 汇总 / 状态）)
- **doc 27** — `bpms.sync_fcl_stage_info` (阶段 / 天数)
- **doc 28** — `bpms.sync_loan_foreclosure_hold` (Hold（宽表→长表 unpivot）)
- **doc 29** — `bpms.sync_loan_foreclosure_loss_mitigation` (损失缓释（编码→文本解码）)
- **doc 30** — `bpms.sync_loan_foreclosure_bankruptcy` (破产（编码→文本解码）)

---

<!-- RULE_GLOSSARY START -->
## 附录：逐跳转换规则速查（技术语句 → 易懂解释 + 公式）

> 血缘表里 `rule` 列的技术语句，对应的易懂解释与数学公式如下（HTML 血缘图谱抽屉里每条规则下方也会显示）。

| 技术语句（rule） | 易懂解释 | 数学公式 |
|---|---|---|
| `decode / datadic` | 编码翻译：上游存的是数字/代码，ETL 查字典表(datadic)翻成业务文字。例：lmstatus=112 → "Workout Denial"。 | — |
| `interval overlap (lm / in_lm` | 与 LM（损失缓解）区间的重叠天数——从该阶段耗时里扣除这些天。 | 重叠天数 = min(阶段结束, LM结束) − max(阶段开始, LM开始) + 1 |
| `interval overlap (hold / on_hold` | 与 Hold（止赎暂停）区间的重叠天数——从该阶段耗时里扣除这些天。 | 重叠天数 = min(阶段结束, Hold结束) − max(阶段开始, Hold开始) + 1 |
| `view: actual / view actual` | 界面视图实时计算（不落库）：实际天数 = 里程碑日 − 应还款日；偏差 = 实际 − 累计目标天数。 | actual = 里程碑日 − 应还款日(nextduedate)；var = actual − Σtarget |
| `unpivot / wide→long` | 宽表转长表：原来一行里的 Hold1/2/3/4 等多列，拆成多行（一行一个 Hold）。 | — |
| `datediff+1 / +1 (inclusive)` | 阶段已历天数（含首尾两天）。 | 天数 = 结束日 − 开始日 + 1 |
| `countdown / 倒计` | 距目标日的倒计天数（已过则 0，无日期则空）。 | 天数 = 目标日 − 当日 |
| `min(dataasof / first-seen` | 首见日：取该值在历史每日快照中第一次出现的日期。 | 日期 = MIN(dataasof) WHERE 该值非空 |
| `dataasof → fctrdt / dataasof->fctrdt` | 数据日期改名：上游每日快照日 dataasof 改名为 fctrdt（含义不变）。 | — |
| `case when / case ` | 分情况取值：按条件 / CASE 规则得到——具体逻辑见本字段「规则说明」与 SQL（各字段不同）。 | — |
| `coalesce` | 取首个非空：从多个候选列里取第一个有值的。 | — |
| `auto-increment / 自增` | 自增主键：由 BPS 应用自动生成的行号，无业务来源。 | — |
| `bps app / etl managed` | 系统/审计列：由 BPS 应用或 ETL 维护（创建/更新时间等），非 servicer 上报数据。 | — |
| `null / 未填充` | 恒空：ETL 未写入该列（设计上留空 / 被注释掉），故值为 NULL。 | — |
| `rename / 改名` | 仅改列名：值不变，只是换了字段名。 | 下游 = 上游（改名） |
| `servicer raw / 原始` | 服务商原始列：数据最初来自 servicer 上报的这一列。 | — |
| `passthrough / pass-through` | 原样透传：上游列的值直接搬到下游，不做任何改动。 | 下游 = 上游 |
<!-- RULE_GLOSSARY END -->
