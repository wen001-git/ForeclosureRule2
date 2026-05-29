# Prompt & Decision Log — ForeclosureRule2

---

## [2026-05-28 UTC] Install claude-mem tool — bun install workaround
> Bash(npx claude-mem install 2>&1) — failed due to tree-sitter-cli post-install script under Bun on Windows; attempting workaround with bun install --ignore-scripts

---

## [2026-05-28 UTC] Doc 14 v7 — 新增 Section 2.6 Newrez 已提供高价值未利用字段（MCP 实测验证）
> 那还有没有 newrez提供了，但是我们没有利用到的字段？这些字段有业务分析作用吗？我们需要定义到标准接口表吗？请查询数据库回答，要有依据

## [2026-05-28 UTC] Doc 14 v6 — 新增 Section 2.0 四维状态基础字段（delinquency_status 等 12 个 doc 09 缺口字段）
> Could you please review Doc 14 to check if any fields are still missing... noticed Doc 14 lacks delinquency_status... Does Newrez provide these? Should we incorporate these industry-standard fields?

## [2026-05-28 UTC] Doc 14 v5 — Section 2.3 新增 noi_date 字段（NOI 与 Demand 概念分离）
> OK，现在更新 doc 14 加入这个字段（noi_date，正式止赎意向通知日，与 demand_sent_date 分开）

## [2026-05-28 UTC] Doc 16 — BPS Foreclosure 面板速查（新建，含截图）
> 新建一个"面板速查页"，并把截图放到文档中

## [2026-05-28 UTC] Doc 14 v4 — 全部字段规范表新增第 2 列「业务含义/计算逻辑（如有）」
> 对于 doc 14，请对于每个字段都加上一列：业务含义/计算逻辑（如有），加到第2列

## [2026-05-28 UTC] Doc 13 v23 — 5 张 BPS FCL 表源数据筛选条件（ETL 代码验证）
> I just restart claude code, this is last information: ... 13_newrez_fcl_bps_display_mapping.md 文档中，是否有 servicer源数据的筛选条件呢？比如说【Section 4：Hold 面板 — 全历史记录模型】的数据是查询 bpms_dev.sync_loan_foreclosure_hold 表，但是这个表bpms_dev.sync_loan_foreclosure_hold 的数据对应的 servicer源数据是什么，源数据是通过什么筛选条件得出 bpms_dev.sync_loan_foreclosure_hold 的？请查询代码验证。或者 你列出 BPS MySQL 的与foreclosure相关的表是通过什么筛选逻辑从 servicer的源数据中生成的？你的建议呢？（扩展为全部5张BPS FCL表）

## [2026-05-28 UTC] Doc 13 v22 — Q3 activefcflag NULL-safe 处理技术详解
> Could you write your explanation down in a document? Which document would be the best place to put it?

### ✅ Doc 13 v22 完成 [2026-05-28]
- zh + en 两文件同步更新
- Section 8 Q 表后新增「Q3 技术详解 / Q3 Technical Detail」子节
- 内容：① NULL 取值原因（Newrez 历史漏填）；② 为何视为"进行中"（完结有多重证据：fcremovaldate + fcremovaldesc）；③ 风险不对称性说明；④ 正确 SQL 写法（OR NULL / COALESCE，并说明 `<=>` 为何不适用）；⑤ 影响范围表（受影响数据 / 当前状态 / 修复建议 / 跨文档参考）
- 选择放在 doc 13 Section 8 的原因：Q3 已有索引条目 + Section 8 是"数据质量问题"专区，工程师调试时第一时间查阅

## [2026-05-28 UTC] 两张 FCL 表字段级对比 + doc 02/12 更正
> pls conduct（对 84 条重叠 loanid 做字段级对比，并在 doc 02/12 中更正 bpms_dev.sync_loan_foreclosure 非 ETL 产物的发现）

## [2026-05-28 UTC] 调查 bpms_dev.sync_loan_foreclosure 与 port.basic_data_loan_foreclosure 的数据流关系
> so bpms_dev.sync_loan_foreclosure is base on port.basic_data_loan_foreclosure? 数据处理流程是什么样的？

## [2026-05-28 UTC] Doc 02 v2 — MCP-verified Layer 5 corrections + basic_data_pool_config.py + bpms_dev.sync_loan_foreclosure
> pls tell me why this doc 02_etl_pipeline , the section 1. 总体架构：五层管道, do not include this file [C:\Users\jli\MyData\Copilot\PrefectFlow\flow\basic_data\basic_data_config\basic_data_pool_config.py], is it because this file is not in the pipeline? and why the layer 5 does not inlude bpms_dev.sync_loan_foreclosure,you can use MCP to check the Newrez data(source data) and the out put data (mysql DB)
> yes,pls conduct ,and check what did you miss in the previously job without MCP help

### Decision: Doc 02 Layer 5 correction approach [2026-05-28]
- **Context**: Layer 5 in doc 02 showed Redshift `port.sync_*` tables, but MCP queries showed those don't exist in Redshift (only `port.sync_to_bps_status` audit log). MCP revealed Layer 5 is entirely MySQL with two schemas.
- **Options considered**: A) Minimal fix (just add missing table), B) Full MCP-verified rewrite of Layer 5 with correct schema separation
- **Choice**: B — full correction with MySQL `port` vs `bpms_dev` schema separation
- **Reason**: The original error was fundamental (wrong database platform); partial fix would leave readers confused about the actual architecture

## Milestones

### ✅ Doc 02 v2 完成 [2026-05-28]
- zh + en 两文件同步更新
- 5项修正：Layer 5 平台（Redshift→MySQL）、新增 `bpms_dev.sync_loan_foreclosure`、`5-FORECLOSURE` 目标更正为 MySQL `port.basic_data_loan_foreclosure`、Layer 4 补充 `basic_data_pool_config.py`、Layer 5 新增 `bpms_dev.biz_data_view_loan_details_foreclosure`
- 修订历史 v2 已追加

## [2026-05-28 UTC] Research project state
> pls research this project

## [2026-05-28 UTC] foreclosure_data_dictionary.md v4 — 新增表17 bpms_dev.sync_loan_foreclosure（72列，MCP验证）
> can you add bpms_dev.sync_loan_foreclosure to this doc C:\Users\jli\MyData\Copilot\ForeclosureRule2\docs\foreclosure_data_dictionary.md
> pls use mcp to check the fields

### ✅ foreclosure_data_dictionary.md v4 完成 [2026-05-28]
- 新增表17：`bpms_dev.sync_loan_foreclosure`（72列，MCP 2026-05-28 实测）
- 7个字段分组：标识符(6列) / timeline_*(19列) / target_*_days(15列) / variance_*(4列) / bid_approval_*(4列) / summary_*(16列) / 管理字段(8列)
- 关键标注：① `target_*_days` 为硬编码 MySQL DEFAULT（静态SLA，非动态计算）；② `actual_*_days` 不在本表（位于 `sync_fcl_stage_info`）；③ `bid_approval_loan_resolution_holods` 列名拼写错误已记录
- 修订历史 v4 已追加；文档页脚更新至 v4

## [2026-05-28 UTC] Doc 13 v21 + Doc 12 v5 + Doc 14 v2 — ETL 中间层未使用字段文档化 + Doc 14 新增「ETL 已归一化/未进 BPS」字段清单
> 好的，赞同你的建议，doc12和doc 13都记录。而且 basic_data_pool_config.py 中处理了servicer源数据跟我方数据的映射关系的规则，虽然bps系统还没有使用，但是否也应该规划到 14_bps_driven_servicer_fcl_interface.md 中呢？不过请标识出来哪些是BPS系统需要，哪些是为未来我们跟踪贷款状态需要的数据

## Milestones

### ✅ Doc 13 v21 完成 [2026-05-28]
- zh + en 两文件 Section 8 追加 Q12
- Q12 记录：`port.basic_data_loan_fcl.fcjudgment_end_date` 存储于 ETL 中间表但未被下游 BPS ETL 消费；架构缺口说明 + 设计意图（跨 Servicer 标准化 + `actual_judgement_hearing_set_days` 预留）
- 修订历史 v21 已追加

### ✅ Doc 12 v5 完成 [2026-05-28]
- zh + en 两文件新增 Section 15
- 记录 4 个 ETL 中间表预留字段：`fcjudgment_end_date` / `titleordereddate` / `jr_sr_lien_flag` / `activejnrlienfcflag`
- 每字段含：Newrez/Capecodfive 原始字段、类型、设计意图、当前状态（🔮）
- 修订历史 v5 已追加

### ✅ Doc 14 v2 完成 [2026-05-28]
- zh + en 两文件新增附录 B
- 附录 B：`port.basic_data_loan_fcl` 全约 37 个业务字段的用途分类（✅ BPS已使用 vs 🔮 ETL预留/未进BPS）
- 4 个 🔮 字段标注未来用途；Hold 槽位标记 ✅；含 Servicer须知说明框
- 修订历史 v2 已追加

---

## [2026-05-27 UTC] Doc 14 v1 + Doc 13 v20 patch — BPS 驱动的 Servicer FCL 数据接口规范 + Judgement 字段映射更正
> 请帮我整理一下，如果按照BPS系统对Foreclosure 显示信息的要求，我们的对Servicer的标准数据接口应该要怎么设计？（附：ETL 代码验证发现 doc 13 中 judgement 字段映射错误，一并修正）

---

## [2026-05-27 UTC] Doc 13 v19 — Section 7 新增 Time Line Tab 完整字段映射
> [Image #12] BPS系统的Asset Management - agg summary - foreclosure页面中，还有一个Time Line tab页面，请帮我分析一下这个页面上的各个字段与mysql数据库的BPS的表和newrez数据源的数据的映射关系，就像你之前做的分析

---

## [2026-05-27 UTC] Doc 13 v18 — 术语说明新增「Upcoming FC Sales」词条
> what is [Upcoming FC Sales] mean? pls add it to the teams list

---

## [2026-05-27 UTC] Doc 13 v17 — Section 5 BPS 表结构新增「UI 列业务含义」说明
> [Image #11] in the Section 5：Loss Mitigation Cycle 面板 - BPS 表结构, what do the UI 列 mean?

---

## [2026-05-27 UTC] Doc 13 v16 — SQL-10 三项 Bug 修复 + stage 存储值更正 + 每日快照表说明
> ok, pls conduct

---

## [2026-05-27 UTC] Doc 13 v15 — Section 7 阶段划分表补充 BPS 输出字段列 + SQL-10 展示完整管道
> ok, pls conduct as you thought

---

## [2026-05-27 UTC] Doc 13 v14 — Section 5 新增 LM 字段取值含义 + 多轮次原因解析
> [Image #3] on the [Section 5：Loss Mitigation Cycle 面板] section, what do deal & Program & status & Final Disposition mean? the range of values for this fields are? What is the business significance of each value? and why LM have so many Cycles?

---

## [2026-05-27 UTC] Doc 13 — 所有表格「映射规则」列更名为「Newrez字段 → BPS展示字段」
> [Image #2] 13#文档，表格的标题请直接表达具体意思（直接写成 Newrez字段 -> BPS展示字段）

---

## [2026-05-27 UTC] Doc 13 v13 patch — Section 3.1 入库筛选条件补充完整字段路径（db.schema.table.field）
> [Image #2] 筛选条件的字段，请以 db.schema.table.field 的格式展示

---

## [2026-05-27 UTC] Doc 13 v13 — Section 7 新增「阶段划分判断逻辑」（Stage Classification Logic）
> [Image #1] on the BPS Foreclosure Summary page, How are these loans categorized into the various stages? What is the underlying classification logic? Which fields are relevant? Have you documented this information?

## Milestones

### Doc 14 v1 完成 [2026-05-27]
- 新建 `docs/zh/14_bps_driven_servicer_fcl_interface.md` + `docs/en/14_bps_driven_servicer_fcl_interface.md`
- **文档定位**：以 BPS 五大面板实际显示需求为终点，逆向定义 Servicer 数据接口规范（doc 09 行业标准的 BPS 落地实施版）
- **结构**：7 个 Section + 附录 A
  - Section 1：总体架构（五大面板字段分布 + P0/P1/P2 优先级 + 三张来源表对应关系 + 与 doc 09 差异说明）
  - Section 2：FCL 主数据字段规范（5个子节，来源 `portnewrezfc`）：2.1识别/入库（7字段，全P0）/ 2.2 FCL状态（9字段）/ 2.3 FCL时间线（15字段；含 Judgement 字段双表说明）/ 2.4 Hold槽位（12字段）/ 2.5 Bid/Sale（3字段）
  - Section 3：LM 字段规范（来源 `portnewrezlm`）：10字段；强调解码映射表交付要求
  - Section 4：BK 字段规范（来源 `portnewrezbk`）：11字段
  - Section 5：合规矩阵（67字段；Newrez ~78%；6字段未提供清单；3个部分提供字段关注点）
  - Section 6：交付格式规范（频率/文件格式/日期标准/NULL处理/数据模型/解码要求/Hold特殊说明）
  - Section 7：字段补全请求优先级汇总（P0/P1/P2 三档）
  - 附录 A：BPS 面板 → Servicer 字段逆向快查索引（7个面板，含 Time Line Tab NOI Date 1 特别注意）
- **关键设计决策**：字段规范表格含 7 列（标准字段名/Newrez原始字段/类型/优先级/格式/BPS面板/Newrez现状）；Section 2.3 Judgement 字段已使用 v20 更正后的正确映射（`fcjudgmenthearingscheduled` → `judgement_start_date`）

### Doc 13 v20 patch 完成 [2026-05-27]
- zh + en 双语同步更正 Judgement 字段映射错误（ETL 代码 + MCP 数据双重确认）：
  - **Time Line Tab 映射表**：Judgement Date 6 → `judgement_start_date`，Newrez 源从 `fcjudgmententered` 更正为 `fcjudgmenthearingscheduled`
  - **Note 4**（zh: 关键要点注4 / en: Key Notes Note 4）：全文改写。明确 `fcjudgmenthearingscheduled`（听证会排期日，未来计划事件）≠ `fcjudgmententered`（法院正式录入判决日，已完成法律事实）；约 11 天差异非 ETL 处理延迟，而是两字段度量完全不同时间点；ETL 代码引用：`fc.fcjudgment_hearing_scheduled AS timeline_judgement_date`（`basic_data_pool_config.py`）
  - **Q10**（Section 8 数据质量问题表）：同上改写，同时标注 `[v20 corrected]`
  - **SQL-12 注释**：删除"~11-day gap vs fcjudgmententered"，改为正确字段名说明
  - zh + en revision history 各新增 v20 行

### Doc 13 v19 完成 [2026-05-27]
- Section 7 扩展为双视图（Stage Tab + Time Line Tab），zh + en 双语同步：
  - 标题更新：「各阶段天数统计」→「聚合概览页（Stage Tab + Time Line Tab）」
  - 新增开篇说明：两 Tab 共用同一数据源 sync_fcl_stage_info
  - 新增「Time Line Tab」子节（zh + en）：
    - 12 列字段映射表（Loan ID / Group / Servicer / States / Judicial / NOI Date 1 / Referral Date 2 / First Legal Date 3 / Service Date 4 / Publication Date 5 / Judgement Date 6 / Sale Date 7）
    - MCP JOIN 实测验证（referral/first_legal/service/sale 字段精确匹配）
    - 3 笔样本贷款数据（与 Image #12 截图比对）
    - 4 条关键注释：Group 含义（FCL/REO/D120P）/ NOI vs Demand 区别 / Publication 恒NULL / Judgement ~11天差异
  - 附录 B 新增 SQL-12（复现 Time Line Tab 视图，含 demand_start_date 对比列）
  - zh + en 修订历史各新增 v19 行

### Doc 13 v18 完成 [2026-05-27]
- zh `术语说明` + en `Glossary` 均新增「Upcoming FC Sales」词条
- 说明要点：BPS 阶段代码 `SALE`；触发条件 `fcscheduledsaledate IS NOT NULL`；优先级 1（7 级中最高）；同时覆盖 Judicial 州（判决后排期）和 Non-Judicial 州（Service/Publication 后排期）；BPS 输出字段：`sale_start_date`/`to_sale_days`；交叉引用 Section 7 stage 代码映射表
- zh + en 修订历史各新增 v18 行

### Doc 13 v17 完成 [2026-05-27]
- Section 5 BPS 表结构映射表后、「关键特性」前新增子节（zh + en 双语）：
  - zh：「UI 列业务含义」— 10 列说明表（UI 列 / 业务角色 / 补充说明）
  - en：「UI Column Reference」— 同上英文版
  - 涵盖：Deal（策略方向）/ Program（具体方案）/ Status（当前工作状态）/ Cycle Opened Date（周期开始日）/ Cycle Closed Date（周期结束日，NULL=进行中）/ Final Disposition（最终处置结论，FCL 决定因素）/ Denial/Reason（拒绝原因）/ Borrower Intentions（借款人意向，Newrez 通常为空）/ Imminent Default（CFPB Reg X 触发，Newrez 恒 NULL）/ Single Point of Contact（CFPB Reg X 12 CFR 1024.40，Newrez 恒 NULL）

### Doc 13 v16 完成 [2026-05-27]
- MCP 实测发现并修复 SQL-10 三项 Bug（zh + en 双语同步）：
  - Bug ①：两库 collation 不一致（bpms_dev=utf8mb4_general_ci，newrez=utf8mb4_0900_ai_ci），JOIN 触发 SQL Error [1267]；修复：加 `COLLATE utf8mb4_general_ci`
  - Bug ②：两表均为每日快照表（`fctrdt`/`dataasof`），仅 loanid JOIN → 682×55 笛卡尔积；修复：加 `AND p.dataasof = s.fctrdt`
  - Bug ③：未筛当前快照日；修复：加 `fctrdt = MAX(fctrdt)`
  - 修复后实测：26 行，无重复，与 BPS 页面完全一致
- Section 7「阶段划分判断逻辑」表：`stage` 列值更正为 DB 实际存储代码（全大写：SALE/JUDGEMENT/SERVICE/FIRST_LEGAL/REFERRAL/DEMAND/PUBLICATION）
- 新增「stage 代码 → BPS 页面显示名映射」子表（7 行）
- 关键要点新增：①`stage` 全大写代码说明；②`sync_fcl_stage_info` 每日快照表说明（含 collation/笛卡尔积处理指引）
- SQL-10 头注释更新：明确三项修复细节 + MCP 实测验证状态

### Doc 13 v15 完成 [2026-05-27]
- Section 7「阶段划分判断逻辑」/「Stage Classification Logic」（zh + en 双语）：
  - 补充说明段落：ETL 将分类结果写入 `sync_fcl_stage_info.stage`；BPS 页面直接读取存储字段，无额外转换
  - 分类表新增第四列「BPS 输出字段（`sync_fcl_stage_info`）」，每一阶段均明确列出：`{stage}_start_date` · `to_{stage}_days` · `{stage}_in_lm_days` · `{stage}_on_hold_days`
  - 关键要点新增两条：①ETL 写入字段说明；②BPS 页面显示 = BPS 存储数据
  - SQL-10 扩展：新增 BPS 输出字段（5 个阶段的 start_date + stage/to_days）在 Newrez 条件字段之前，实现跨管道完整验证

### Doc 13 v14 完成 [2026-05-27]
- Section 5（LM Cycle 面板）新增两个子节（zh + en 双语）：
  - 「LM 字段取值与业务含义」/ "LM Field Values and Business Meaning"：
    - Deal 枚举表（6值：Evaluation / Modification / Forbearance / Repayment Plan / Short Sale / DIL）
    - Program 枚举表（5值含 Bridger mod / 496.0 业务含义）
    - Status 枚举表（6值：Pending Financials / Workout Denial / Document Follow-up / DIL Title Ordered / Negotiate DIL liens / Awaiting MI Approval）
    - Final Disposition 枚举表（7值含对 FCL 进程影响分析）
  - 「为什么 LM 会有多轮次？」/ "Why Does LM Have Multiple Cycles?"：
    - 四大原因：监管强制要求（CFPB Reg X）/ 方案升级序列 / 方案变更 / 操作性错误
    - loanid=7727000088 完整 9 轮时间线分析表
- 附录 B 新增 SQL-11（LM 字段取值分布查询）
- zh/en 两文件 revision history 均更新至 v14

### Doc 13 v13 完成 [2026-05-27]
- Section 7（聚合概览页）新增子节「阶段划分判断逻辑」/「Stage Classification Logic」
  - 7级瀑布式优先级判断表（Upcoming FC Sales → Referral → NOI）
  - 各阶段判断条件（Newrez `portnewrezfc` 字段名）
  - 关键要点：所有字段来自 `newrez.portnewrezfc`；`fcscheduledsaledate` 最高优先级；Publication/NOI组 Newrez 恒为 0
  - 截图数据一致性验证（26笔 Newrez 贷款分布）
- 附录 B 新增 SQL-10（JOIN `sync_fcl_stage_info` + `portnewrezfc`，按优先级展示关键判断字段）
- zh + en 两文件 revision history v13 已添加

---

## [2026-05-27 UTC] Doc 13 v12 — 数据范围说明全覆盖（Section 4/5/6 单贷款视图 + Section 7 全量视图 + SQL-9）
> #13 document, on the section Section 7：聚合概览页 — 各阶段天数统计, this section should describe the data range of this page, right? Have you written the data range for each page into the document?

## Milestones

### Doc 13 v12 完成 [2026-05-27]
- Section 7（聚合概览页）新增 3 行头注：入库条件（`fcreferraldate IS NOT NULL` + `activefcflag=1`）、当前约 13,321 笔、来源表 `sync_fcl_stage_info`、SQL-9 验证引用
- Section 4（Hold）新增「单贷款视图」数据范围说明
- Section 5（LM）新增「单贷款视图」数据范围说明
- Section 6（BK）新增「单贷款视图」数据范围说明 + SQL-7 验证引用
- 附录 B 新增 SQL-9（`sync_fcl_stage_info` 按 `stage` 分组汇总）
- zh + en 两文件 revision history v12 已添加

---

## [2026-05-26 UTC] Doc 07 v2 — BPS FCL 7阶段管道解析 + 新增 Section 2.4.6（含 Mermaid 图）
> 这是我们公司BPS系统中 FCL标准流程：NOI,Referral,First Legal,Service,Publication,upcoming Judgement, Upcoming FC Sales，请帮我解释一下每个阶段的意思？你在 07_fcl_lineage_and_rules.md 中写了 2.4 美国贷款生命周期状态图，我觉得内容很好，让我了解了美国贷款状态扭转，现在，请审核一下我公司的FCL的流程，是否合理？为什么我司使用 upcoming Judgement、 Upcoming FC Sales，而不用 Judgement、FC Sales.
> （后续补充）如果把我公司的 FCL标准流程加入到这个 美国贷款生命周期状态图，是否合理？请另外画一张包含这个 FCL标准流程 的美国贷款生命周期状态图，在已有的【2.4 美国贷款生命周期状态图】基础上，不删除原来的内容，这个文档结构该如何编排？

## [2026-05-26 23:21 UTC] 更新 doc 12，补充 5 张 BPS MySQL 表
> 帮我更新一下 doc 12，把这5张 BPS 表也加进去

## [2026-05-26 UTC] Doc 13 Section 3 新增 BPS 界面标签列和业务含义列
> in the 13# document, on the [BPS 展示字段] section，里展示的是字段的在数据库中的字段名，我还想要增加1列放在第一列，就是在BPS系统界面上展示的文字是什么（是哪个功能模块哪个字段）？第二列才是对应的Mysql数据库的schema.table.field，而且还增加一列说明BPS展示的这个字段的业务含义

## [2026-05-26 UTC] Doc 10 v2 + Doc 13 v4 — Add Glossary section with NOI/Demand and other missing terms
> [Image: doc 13 screenshot showing "NOI / Demand 信函发出日"] What does "NOI / Demand" mean? How about adding a section to the document specifically for defining key terms? What do you think?

## [2026-05-26 UTC] (session resumed) Continue doc 13 v3 — complete Sections 3.2–3.7 in zh and en
> (Session resumed from previous context window. Completed the remaining 6 subsections rewrite for doc 13 v3.)

## [2026-05-26 UTC] Doc 13 v5 — 方案 A 表格宽度优化（session resumed）
> 如果有些表格的字段不是来源与同一个 schema.table 呢？你如何表达？

## [2026-05-26 UTC] Doc 13 Section 3.1 实测填充率 "——" 含义澄清
> why on the section of [Section 3：BPS 展示字段完整映射表], have some 【实测填充率】 were filled by ——, is that because you did not research? or it is 0%?

## [2026-05-27 UTC] Doc 13 v6 — MCP 实测填充率补全
> 执行 MCP 查询，把所有 —— 换成真实数字，然后把 doc 13 更新到 v6

## [2026-05-27 UTC] Doc 13 v7 — 「业务含义」列移至第 2 列
> 请把文档中的[业务含义]挪到第2列，因为我是美国贷款业务的初学者，还不能清楚理解每个字段的业务含义

## [2026-05-27 UTC] Doc 13 v8 — 澄清「映射规则」方向 + Section 3.4 公式字段来源
> section 3 中的 映射规则，是 Newrez 字段 到 BPS 展示字段 的映射规则吗？还是 BPS 展示字段 到 BPS 界面标签 的映射规则？3.4 各阶段差异天数（var_*）中，计算公式 的字段的 schema.table 是？

## [2026-05-27 UTC] Doc 13 v11 — 附录 B SQL 全面覆盖（新增 SQL-8 + 各 Section 引用说明）
> Section 3.4 的 var_* 是否有对应 SQL 在附录 B？如果有，请在对应 Section 加注释。（答：当前无 → 新增 SQL-8；同时补全所有 Section 的 SQL 引用说明）

## [2026-05-27 UTC] Doc 13 v10 — 澄清映射规则中条件字段的 schema.table
> （截图：Section 3.7 summary_foreclosure_status 行的映射规则列，红框标注 `activefcflag=1 → 取 fcstage`）这是哪个表的字段？

## [2026-05-27 UTC] Doc 13 v9 — 新增附录 B：数据验证 SQL
> 请把文档中你通过查询数据库得出的信息，比如 【实测样本验证】等，附上你所使用的验证数据的SQL，以方便我自己去数据库里面查询。not only [实测样本验证] should supplemented related SQL, but also the information that out put from you have searched the DB, if the SQL is too much, so you can list the Key business related SQL, make sure I can copy it to run in mysql DB to learn and verify the data

## Milestones

### Doc 07 v2 — BPS FCL 运营阶段管道（Section 2.4.6）[2026-05-26]
- Both `docs/zh/07_fcl_lineage_and_rules.md` and `docs/en/07_fcl_lineage_and_rules.md` updated to v2
- New **Section 2.4.6** inserted after existing 2.4.5 (Judicial vs Non-Judicial), before Section 2.5
- Existing Sections 2.4.1–2.4.5 (and all of 2.5) left completely unchanged
- New section content (zh + en mirrors):
  - **Stage Flowchart**: Mermaid `flowchart LR` — 7 BPS stages, branch at Service (Non-Judicial→Publication; Judicial→Upcoming Judgement), amber styling on "Upcoming" stages, green P / red REO terminals
  - **Stage table**: 7 rows × 6 columns (# / BPS Stage / Monitoring Mode / Applicable / Key Fields / Description)
  - **"Upcoming" naming rationale**: 4 points including field evidence (`to_judgement_days`, `to_sale_days` as countdown fields)
  - **Design rationale**: 4 points (coverage, Publication necessity, no completed-tail group, operations-first naming)
  - **Comparison table**: 2.4.4 theoretical model (7 stages) vs BPS pipeline (7 stages) side-by-side
- Revision history v2 row added to both zh and en files

### Doc 10 v2 + Doc 13 v4 — Glossary Additions [2026-05-26]
- **Doc 10 zh + en** (both updated, 318→375 lines each): Added 9 missing terms across 3 categories:
  - **Category C / 分类 C**: NOI/Demand Letter (full definition with Judicial vs Non-Judicial distinction and Newrez field name origin), 3rd Party Sale, Target/Actual/Var Days framework (table format)
  - **Category E / 分类 E**: MFR (full definition, promoted from one-liner in Category G), POC (full definition, new)
  - **Category G / 分类 G**: dataasof, SMS/Shellpoint (2 new rows); NOI and MFR one-liners updated to cross-reference full entries
- **Doc 13 zh + en** (v4): Added `## 术语说明` / `## Glossary` section (12-term quick-reference table) between Screenshots block and Section 1; revision history v4 row added to both

### Doc 13 v3 — Section 3.1–3.7 Table Structure Overhaul [2026-05-26]
- Both `docs/zh/13_newrez_fcl_bps_display_mapping.md` and `docs/en/13_newrez_fcl_bps_display_mapping.md` updated to v3
- All 7 subsections (3.1–3.7) now have:
  - **New first column** "BPS 界面标签" / "BPS UI Label": `[Panel] > [Field Label]` format
  - **Per-section header note** specifying BPS MySQL full path (`bpms_dev.sync_loan_foreclosure.{field}`)
  - **Newrez Raw Field** column now shows full `newrez.schema.table.field` path (来源表 merged in)
  - **New last column** "业务含义" / "Business Meaning" (derived from MCP COLUMN_COMMENT + existing notes)
- Section 3.4 converted from code-block text to structured 4-column table (BPS UI Label + BPS Field + Formula + Business Meaning)
- Section 3.2 preserved its existing Business Meaning column; gained only the new first column
- Revision history v3 row added to both zh and en files

### Doc 12 v4 — BPS MySQL FCL Tables Added [2026-05-26]
- Both `docs/zh/12_sync_asset_management.md` (741→872 lines) and `docs/en/12_sync_asset_management.md` (736→867 lines) updated to v4
- New Section 14 added: complete BPS MySQL FCL table structures (bpms_dev, MCP-verified)
  - `bpms_dev.sync_loan_foreclosure`: 72 cols fully documented (first time); all 15 target_*_days with actual field names + defaults confirmed via MCP; 8 admin cols include previously-unknown `update_user` (pos 68)
  - Other 4 tables (hold/lm/bk/stage): column count delta vs Section 13 explained (9 extra = id + 8 admin)
- Section 12 MySQL Write Tables: supplementary note added about `bpms_dev.sync_loan_foreclosure` not being in SYNC_TABLE_MAP
- Section 13 summary: annotation added clarifying ETL field counts vs actual table column counts
- Revision history: v4 row added to both files

### Doc 13 v5 — 方案 A：表格宽度优化 [2026-05-26]
- Both `docs/zh/13_newrez_fcl_bps_display_mapping.md` and `docs/en/13_newrez_fcl_bps_display_mapping.md` updated to v5
- **方案 A implemented**:
  - Sections 3.1, 3.3, 3.6, 3.7: `newrez.portnewrezfc.` prefix extracted from all field cells to per-section header note; cells now show short field name only
  - Section 3.3 column header fixed (was broken by global replace): now reads `计算公式（端点字段来自 portnewrezfc）` / `Calculation (field endpoints from portnewrezfc)`
  - Section 3.5 (mixed sources): retains short table name prefix in cells (`portnewrezbk.activebkflag`, `portnewrezfc.fchold1projectedenddate`) to disambiguate two different source tables; header note explains mixed-source rationale
  - Column header "Newrez 原始字段（完整路径）" / "Newrez Raw Field (Full Path)" → "Newrez 字段" / "Newrez Field" throughout Sections 3.1, 3.5, 3.6, 3.7
  - Revision history v5 row added to both files
- **Mixed-source pattern decision**: For tables drawing fields from >1 schema.table, retain the `table.` short prefix in cells; document the mixed sources explicitly in the section header note

### Doc 13 v11 — 附录 B SQL 全面覆盖 [2026-05-27]
- **问题1（Section 3.4）**：var_* 差异天数字段在附录 B 中当前无对应 SQL → 新增 SQL-8
- **问题2（全局）**：所有有 SQL 关联的 Section 都应加引用注释 → 补全 9 处缺失的头注
- **新增 SQL-8**（两文件）：查询 `bpms_dev.sync_loan_foreclosure`，同时输出 target_*/actual_*/var_* 三组字段；来源表为 BPS 主 FCL 表，不涉及 Newrez
- **补全「验证 SQL」引用**：Section 3.2（SQL-8）、3.3（SQL-8+SQL-4）、3.4（SQL-8）、3.5（SQL-4）、3.6（SQL-1+SQL-4）、3.7（SQL-1+SQL-4）、Section 4（SQL-5）、Section 5（SQL-6）、Section 8（SQL-1+SQL-3）
- 文件行数：zh 935→997 行，en 912→968 行
- revision history v11 行添加至两个文件

### Doc 13 v10 — 澄清映射规则条件字段来源 [2026-05-27]
- 触发：用户截图 Section 3.7 `summary_foreclosure_status` 行，红框标注映射规则列中的 `activefcflag=1 → 取 fcstage`，问"这是哪个表的字段？"
- **答案**：`activefcflag`、`fcstage`、`fcresults`、`fcremovaldesc` 全部来自 `newrez.portnewrezfc`（Newrez 侧条件判断）
- **修改**（zh + en）：Section 3 开头注释块新增第 4 条要点，明确「映射规则表达式中出现的所有字段名属于该小节 Newrez 来源表，不涉及任何 BPS 字段」
- revision history v10 行添加至两个文件

### Doc 13 v9 — 新增附录 B：数据验证 SQL [2026-05-27]
- 涉及文件：`docs/zh/13_newrez_fcl_bps_display_mapping.md`（682→935 行）、`docs/en/13_newrez_fcl_bps_display_mapping.md`（659→912 行）
- **新增附录 B**（zh + en 双语），包含 SQL-1 至 SQL-7 共 7 条可在 MySQL 直接运行的只读 SQL
  - **B.1 全量统计类**：SQL-1（字段填充率总览，覆盖 Section 2.1 / 3.1 / 3.7 / Q8）、SQL-2（fcresults 分布，覆盖 266笔 3rd Party 注释）、SQL-3（Q9 异常验证：fcsaleamount > fcsalehelddate）
  - **B.2 样本贷款类**：SQL-4（指定贷款 Newrez 原始字段，覆盖附录 A.A + A.B）、SQL-5（Hold 历史，覆盖 Section 4 + A.B Hold 面板）、SQL-6（LM 历史，覆盖 Section 5 + A.B LM 面板）、SQL-7（破产核查，覆盖 A.B Bankruptcy 面板）
- **新增 SQL 引用说明**：Section 2.1 头注（指向 SQL-1）、Section 3.1 头注第 4 行（指向 SQL-1 / SQL-2）、附录 A 入口（指向 SQL-4 至 SQL-7）
- 附录 A 标题由"附录：两笔贷款…"重命名为"附录 A：两笔贷款…"（en 同步为"Appendix A"）
- revision history v9 行添加至两个文件

### Doc 13 v8 — 澄清两处歧义 [2026-05-27]
- 问题解答：
  - **映射规则方向**：Newrez 原始字段 → BPS 展示字段（ETL 数据流向）；文档标题"BPS→Newrez"是读者查询方向，两者相反但不矛盾
  - **Section 3.4 公式操作数**：`actual_*_days` 和 `target_*_days` 均来自 `bpms_dev.sync_loan_foreclosure`，与 var_* 同表，全程不涉及 Newrez
- 文档修改（zh + en）：
  - Section 3 开头新增「映射规则」列语义注释块（5行，含数据流向说明和与文档标题方向的关系）
  - Section 3.4 头注由 2 行扩展为 3 行，第三行说明公式操作数 schema.table
  - revision history v8 行添加至两个文件

### Doc 13 v7 — 「业务含义」列移至第 2 列 [2026-05-27]
- 涉及文件：`docs/zh/13_newrez_fcl_bps_display_mapping.md`（zh 上轮已完成）、`docs/en/13_newrez_fcl_bps_display_mapping.md`（本轮完成 3.3–3.7）
- **变更内容**：Section 3.1–3.7（7 个小节全部）将「业务含义 / Business Meaning」从最后一列调至第 2 列
- **原因**：用户是美国贷款业务初学者，需优先理解业务语义，再看技术字段名和映射规则
- 修订历史 v7 行同步添加至 zh + en 两个文件

### Doc 13 v6 — MCP 实测填充率补全 [2026-05-27]
- MCP 查询对象：`newrez.portnewrezfc` WHERE `activefcflag=1`（13,360 笔活跃 FCL）
- **Section 3.1**：全部 8 个 `—` 替换为实测值：
  - `titlereceiveddate` / `titlecleardate` = **0.0%** ⚠️（Newrez 不提供产权日期，同 Publication Date）
  - `servicecompletedate` = **28.9%**
  - `fcjudgmententered` = **7.9%**
  - COALESCE(dtdeedrecorded, fcremovaldate) = **2.0%**（dtdeedrecorded=0%）
  - `fcresults='3rd Party'` = **2.0%**（266 笔）
  - `fcl3rdpartyproceedsreceiveddate` = **0.0%**
- **Section 3.7**：业务含义列补入实测值（100% for fcfirm/shellpointloanid；99.5% for lastfcstepcompleted；4.7% for fcsaleamount⚠️）
- **Section 8**：新增 Q8（产权字段 0%，Newrez 不报告）、Q9（fcsaleamount 4.7% > fcsalehelddate 2.1%，疑数据时序问题）
- 修订历史 v6 行添加至 zh + en 两个文件

---

## [2026-05-26 UTC] Trace FCL fields written to BPS tables in sync_asset_management.py
> 请重点关注 prefectflow\flow\bps\sync_asset_management.py 中有关foreclosure的代码，我想知道有关foreclosure的字段都写入了哪个表？提供给BPS系统

---

## [2026-05-26 UTC] Investigate and document sync_asset_management.py
> C:\Users\jli\MyData\Copilot\PrefectFlow\flow\bps\sync_asset_management.py  pls investigate this code and document your findings.

---

## [2026-05-26 UTC] Research this project
> pls research this project

---

## [2026-05-25 UTC] 新建 doc 11 — Servicer 现有数据 → 新系统 FCL 实施映射指南
> 我要重构 prefect 项目，我正在做一个新的系统，刚才我们已经定了针对 servicer 的有关 forclosure 的标准接口字段：09_servicer_data_interface_standard.md，我会在新的系统中设计这些字段，但是目前 servicer 还不能马上按这个标准接口提供数据，所以我需要使用现有的 servicer 数据来实现新系统的有关 foreclosure 的状态，目前 08_servicer_fcl_field_mapping.md 有这些内容吗？（附：Newrez portnewrezfc 多次 hold 字段分析）

### Decision: 新建 doc 11 作为过渡实施指南 [2026-05-25]
- **Context**: doc 08 有足够的分析材料（字段清单 + FCL 判断规则），但不是开发者可直接使用的实施规范；doc 09 是目标接口标准，尚未得到 Servicer 支持
- **Options considered**: A) 在 doc 08 中新增实施章节；B) 新建 doc 11；C) 直接让开发者读 doc 08
- **Choice**: B — 新建 doc 11，定位为 doc 08（现状）和 doc 09（目标）之间的桥接实施文档
- **Reason**: doc 08 是分析文档，混入实施规范会破坏其定位；开发者需要一个可直接编码的参考，包含 CASE WHEN 逻辑和 Newrez portnewrezfc 的利用方案
- **Newrez 多次 Hold 决策**: doc 09 Group F 保持单一活跃 Hold 设计；portnewrezfc 的 fchold1/2/3 历史记录在 doc 11 Newrez 章节中专项处理（取最新未结束的 hold 作为当前活跃 hold）

---

## [2026-05-25 UTC] 新建 doc 10 — 综合术语清单（Glossary）
> 这个项目有术语清单吗？

---

## [2026-05-25 UTC] doc 08 — 合并两个重叠的"最小字段集"section
> in the 08_servicer_fcl_field_mapping.md doc, the section [向 Servicer 请求字段的推荐最小集] is different from this section [理想 FCL 判断所需的最小字段集], I think they are talking about the same thing, am I mistake? (annotation: 这两个section 描述向servicer要求的字段不太一样，有什么区别？请研究一下) — 方案：合并为一张双视角表格，删除 Background 区域的旧 Section 2，在 Gap Summary 区域保留合并后的单一表格

### Decision: 合并两个最小字段集 section 为双视角对照表 [2026-05-25]
- **Context**: doc 08 存在两个重叠 section（行 86 和行 576），分别从系统视角和 Servicer 请求视角列举最小字段集，内容部分重叠但各有遗漏，令读者困惑
- **Options considered**: A) 保留两个，加交叉引用说明区别；B) 合并为一张双视角表格；C) 删除较弱的一个
- **Choice**: B — 合并为一张双视角表格，增加"系统需要"和"需请求 Servicer"两列
- **Reason**: 合并表可同时解释 `next_payment_due_date`（系统需要但 Servicer 已提供）和 `fcl_hold_flag`（两者都需要）的差异，比两张分开的表更清晰；同时解答了用户关于 `bankruptcy_flag` 为何独立于 MBA `Bankruptcy` 枚举的疑问（MBA 枚举互斥，无法表达 FCL+BK 并存状态）

---

## [2026-05-25 UTC] doc 08/09 — 补录 MBA 完整取值范围、FCL-Hold 说明、推荐字段集
> 这个你之前回答过我的问题，没有加到文档中吗？MBA 标准逾期状态完整取值范围 [full table + FCL-Hold explanation + recommended field set]

---

## [2026-05-25 UTC] 新建 09 — Servicer 数据接口标准规范（系统重构前置文档）
> 因为我要重构这个prefect系统，要做一个新的系统，所以，我更加关注如何利用现有的servicer提供的daily和monthly数据，推出贷款 foreclosure 的相关状态，然后制定出标准的servicer需要提供的数据的接口表、数据字典，然后要求servicer按照这个标准来补充缺少的字段。

---

## [2026-05-25 UTC] 08 文档 — 缺口汇总章节"Layer 2"和"Step 3"补充说明
> in the 08_servicer_fcl_field_mapping.md, on the [缺口汇总与优先级] section, what is Layer 2 and step 3 mean, pls add explanation

---

## [2026-05-25 UTC] 08 文档 — LM 覆盖表中"进入 L2"列补充说明
> in the 08_servicer_fcl_field_mapping.md, on the [各 Servicer LM 数据现状与缺口] section, what is the [L2] mean? pls add explanation

---

## [2026-05-25 UTC] 08 文档 en 版 — 补全各 Servicer 缺口分析中的 LM 字段需求行（续上一会话）
> (Session auto-resumed) Continue adding LM gap rows to each servicer's gap analysis in docs/en/08_servicer_fcl_field_mapping.md — Newrez, Carrington, Selene, MRC, Arvest, CapeCodFive, FCI + gap summary table

---

## [2026-05-25 UTC] 08 文档 v2 — DB 查询确认所有"待确认"字段取值，修正 CapeCodFive/FCI 评级
> (Session continued) pls continue — DB 查询 MySQL L1 和 Redshift L2 实际字段取值，更新 08_servicer_fcl_field_mapping.md zh+en 两个版本

---

## [2026-05-25 UTC] 生成 08_servicer_fcl_field_mapping.md — Servicer 原始字段到 FCL 状态映射规则文档
> 作为业务型数据产品经理，我想写一个文档，分别描述各个servicer的原始文件的字段到foreclosure状态的映射关系，去掉中间的数据流...

---

## [2026-05-25 UTC] 07_fcl_lineage_and_rules.md — 为 SQL 表别名 p/s/c 补充来源说明
> in this doc:07_fcl_lineage_and_rules.md, what is p mean in this section [3.2.4 FCL 判断规则（Step 3）]

---

## [2026-05-25 UTC] 将 port.portmonth 和 port.portmonthbase 加入 foreclosure_data_dictionary.md
> pls add port.portmonth and port.portmonthbase to foreclosure_data_dictionary.md, I want to research all the fields in this two tables, pls research the real data via [Redshift credentials]

---

## [2026-05-25 UTC] 将 port.basic_data_loan_fcl 和 port.basic_data_loan_foreclosure 加入 foreclosure_data_dictionary.md
> pls add port.basic_data_loan_fcl and port.basic_data_loan_foreclosure to foreclosure_data_dictionary.md, I want to research all the fields in this two tables

---

## [2026-05-25 UTC] 新增 Section 1.2：basic_data_loan_fcl vs basic_data_loan_foreclosure 详解
> 你的这个发现，跟之前你写的内容是否有冲突？请检查一下，如果有冲突，再去研究一下代码：重要发现：只有 3 个 Servicer 有 FCL 详情数据 ... 其余 7 个 Servicer（SLS、Selene、MRC、FCI、Rocket、Arvest、SPS）不在 basic_data_loan_fcl 中，因此也不在 basic_data_loan_foreclosure 中。

---

## [2026-05-24 UTC] 写 FCL 数据血缘与判断规则文档（per-Servicer）
> 我想知道有关foreclosure状态从最初的来源数据到最终得出foreclosure状态的整个数据血缘过程，按servicer分析现状和判断规则，并调研 PrefectFlow 源码

---

## [2026-05-24 UTC] 调研 PrefectFlow 源码分析 basic_data_loan_foreclosure vs basic_data_loan_fcl 的区别
> 请调研分析 C:\Users\jli\MyData\Copilot\PrefectFlow 这个代码才给出结论，不要只看文档

---

## [2026-05-24 UTC] Add schema prefixes to all table names in docs
> [Image #1] 文档中的表，请写明schema，比如port.basic_data_loan_fcl

---

## [2026-05-23 UTC] Research project history and outputs
> pls research this project, and what preiously this project have done? anf output?

---

## [2026-05-20 00:00 UTC] 初始化项目并设置会话规则
> 我们来初始化这个项目，pls refine this prompt: 请记录我的每个prompt, 记录到prompt.md中，请记录我的每次决策，请在每次完成阶段性任务后，自动进行一次代码整理和全面测试，请把这个规则添加到project rule和user level rule中

---

## [2026-05-20 00:10 UTC] Add Standard Document Header governance rule to project and user rules
> Please add the following documentation governance rule into both: Project Level Rules, User Level Rules. Standard Document Header Rule: Every generated document must include a standardized document header section at the beginning. Required sections: Document Purpose (why, problem, scope, fit), Target Audience, Revision History/Change Log. Optional: dependencies, assumptions, blockers, related documents, glossary, system boundaries, open questions, known limitations.

---

## [2026-05-21 UTC] Enhance 01_source_data.md with DB/schema labels, table descriptions, and per-field statistics
> source.md这个文档中，列出的表是来源于哪个数据库？哪个Schema?对于每个表，请说明该表的描述，对于表的每个字段，请增加这几列：字段取值范围、字段计算逻辑，如有，请用 SQL / 数学公式 / 集合论方式表达、字段值举例、字段值的统计信息、是否foreclosure用到的字段，如果一个表格显示太宽了，可以分成两个表格展示，好浏览一些

---

## [2026-05-21 UTC] Complete English v2 of 01_source_data.md (session continuation)
> (Session resumed from context limit — continuing to update docs/en/01_source_data.md with all v2 enhancements applied to the Chinese version)

---

## [2026-05-23 UTC] 生成 PrefectFlow Foreclosure 核心表/字段说明文档
> 我是一名数据产品经理，我刚开始熟悉美国贷款业务，我要给C:\Users\jli\MyData\Copilot\PrefectFlow 项目中，涉及到与foreclosure相关的主要的表、字段做说明文档，对于每个表 都要说明表的作用和业务意图，表的上游数据，表的下游数据；对于每个表里面的每个字段都要以表格形式列出：字段名、字段业务含义、字段的来源数据、字段的计算逻辑、备注。请生成一套与 Mortgage Loan Foreclosure 相关的核心表/字段说明文档，用于：reverse engineering / onboarding / validator/debug / 数据治理 / 未来系统重构。格式：Markdown 为主，存放于 ForeclosureRule2/docs/。

---

## Decisions

### Decision: Prompt & decision logging format [2026-05-20]
- **Context**: User wants a persistent log of all prompts and key decisions across sessions
- **Options considered**: (A) Separate files for prompts vs decisions, (B) Single `prompt.md` with sections, (C) Database/structured log
- **Choice**: B — single `prompt.md` with `## Decisions` and `## Milestones` sections
- **Reason**: Minimal overhead, human-readable, easy to grep; one file per project keeps it simple

### Decision: Rule placement — project CLAUDE.md + user ~/.claude/CLAUDE.md [2026-05-20]
- **Context**: Rules need to apply both to this project and potentially other projects
- **Options considered**: (A) Project CLAUDE.md only, (B) User settings.json hooks, (C) Both project and user CLAUDE.md
- **Choice**: C — project CLAUDE.md for project-specific context, user CLAUDE.md for global enforcement
- **Reason**: Project file can carry domain context; user file ensures the workflow applies everywhere without repeating it per project

---

## Milestones

### Milestone: Full ForeclosureRule2 documentation suite completed [2026-05-21]

**Deliverables (14 files, zh+en pairs):**

| File | Status |
|------|--------|
| `docs/zh/00_index.md` | ✅ Created |
| `docs/en/00_index.md` | ✅ Created |
| `docs/zh/01_source_data.md` | ✅ Created |
| `docs/en/01_source_data.md` | ✅ Created |
| `docs/zh/02_etl_pipeline.md` | ✅ Created |
| `docs/en/02_etl_pipeline.md` | ✅ Created |
| `docs/zh/03_fcl_status_logic.md` | ✅ Created |
| `docs/en/03_fcl_status_logic.md` | ✅ Created |
| `docs/zh/04_status_inventory.md` | ✅ Created |
| `docs/en/04_status_inventory.md` | ✅ Created |
| `docs/zh/05_loan_attribute_mapping.md` | ✅ Created |
| `docs/en/05_loan_attribute_mapping.md` | ✅ Created |
| `docs/zh/06_diagrams.md` | ✅ Created (6 Mermaid diagrams) |
| `docs/en/06_diagrams.md` | ✅ Created (6 Mermaid diagrams) |

**Key findings documented:**
- 5-layer delinq generation rule stack (manual fix → payoff keywords → REO → FCL → days360)
- 12 standard delinq codes (C/D30/D60/D90/D120P/FCL/REO/P/D/VASP/REPUR/NULL)
- 6 FCL stages tracked in fcl_stage_info (DEMAND→REFERRAL→FIRST_LEGAL→SERVICE→JUDGEMENT→SALE)
- 30 distinct FCL hold types (DB-verified)
- 49 delinq overrides in basic_data_loan_fix (DB-verified)
- SLS→Newrez servicer switch on 2024-07-05

**Data verification:** All counts and distributions cross-validated against Redshift dev (redshift_dev).

---

## Milestones

### Milestone: 08_servicer_fcl_field_mapping.md v2 完成 [2026-05-25]

**DB 实测验证（MySQL L1 + Redshift L2 双重查询）：**

| 发现 | 影响 |
|------|------|
| CapeCodFive `mba_delinquency_status` 值为数字 DPD（`'29.0'`/`'30.0'`），非文本状态码 | CapeCodFive 评级从 🟡 降为 ❌，FCL 永远无法产生 |
| FCI 正确字段名为 `status`（非 `loanStatus`），有 2,371 行 'Foreclosure' + 37 行 'Pre Foreclosure' | FCI 有大量 FCL 数据被完全忽略 |
| Selene `loan_status` 无 'Foreclosure' 值（使用非标准描述），`foreclosure_status_code='A'`(41行) 是唯一可靠信号 | Selene 无需新字段即可修复：Step 3 加 `WHEN fcl_flag='A' THEN 'FCL'` |
| MRC `min_status` 始终为空字符串（12,740行），`fc_flag` 仅有 `'N'`（18行，从未激活） | MRC 无可用字段，需向 Servicer 确认 |
| SLS 实际取值 `'DQ 30'`/`'DQ 60'`/`'DQ 90'`（不是 `'30-59'`/`'60-89'`） | 文档修正，ETL 逻辑使用 'Foreclosure' 文本，不影响功能 |
| Newrez 有 `'1-29 DPD'`、`'Performing Bankruptcy'`、`'REO Sale'`、`'3rd Party Sale'` 等之前未记录的值 | 文档补全 |

**验证方式**：Python psycopg2 直连 Redshift + MySQL L1 外部 schema 查询（2026-05-25）

---

### Milestone: foreclosure_data_dictionary.md v3 完成 [2026-05-25]

**新增两张表（基于 Redshift 2026-05-25 实测 + PrefectFlow 源码双重验证）：**

| 新增 | 状态 |
|------|------|
| 表 15：`port.portmonthbase`（120列，按7组分类） | ✅ 已完成 |
| 表 16：`port.portmonth`（141列，★标注23个portmonthbase独有的新增字段） | ✅ 已完成 |
| Section 2 架构图 Layer 3 新增两张表 | ✅ 已完成 |

**关键数据发现（DB实测）：**
- `portmonthbase`：78,913行，2023-02 ~ 2025-08；FCL=279行（0.35%）
- `portmonth`：129,023行，2023-02 ~ 2026-06；FCL=580行（0.45%）；delinq='FCL'时主要svcdelinq='Foreclosure'(495行)
- portmonth 比 portmonthbase 多 23列（prevdelinq/paymthist/ots_delinq/hpa/cltv/losssev/nsf/mainissue/risktier/trust等），少2列（lm_flag→inlossmit, reasonfordefault→defaultreason）
- Servicer分布：Arvest最大（portmonth 44.7%），Newrez第二（32.5%）
- `remit_status` 全量='cash'；`trust` 全量有值；`hpa`/`cltv` 99.98%有值；`losssev` 仅21行非空

**验证方式**：Redshift实时查询 + `portmonth_config_v2.py`（GEN_PORTMONTHBASE） + `gen_portmonth_config.py`（GEN_PORTMONTH_DATA）源码分析

---

### Milestone: foreclosure_data_dictionary.md v2 完成 [2026-05-25]

**新增两张表（基于源码 + Redshift 2026-05-25 实测双重验证）：**

| 新增 | 状态 |
|------|------|
| 表 13：`port.basic_data_loan_fcl`（61列，按7组分类） | ✅ 已完成 |
| 表 14：`port.basic_data_loan_foreclosure`（62列，含INSERT填充状态标注） | ✅ 已完成 |
| Section 2 架构图 Layer 3 新增两张表 | ✅ 已完成 |

**关键数据发现（DB实测修正了之前文档的错误）：**
- `fcstage` 在 Newrez 中是内部流程描述（'Pre-Sale Review 1'等），非标准化代码；多数为空字符串
- `summary_foreclosure_status` 真实取值：Active Foreclosure(44行) + Closed Foreclosure:*(58行) + NULL(6048行)
- `target_*`（15列）和 `variance_*`（4列）DB实测全部NULL，非占位符估计
- `holdmodified*` 类型为 DATE（非 TIMESTAMP）；`svc_days_infc`/`daysinfc` 类型为 DOUBLE PRECISION（非 INT）

---

### Milestone: Section 1.2 added to 07_fcl_lineage_and_rules.md (v1.5) [2026-05-25]

**结论**：DB查询结果与源码分析结论完全一致，无冲突。

**新增内容（两个文档均已更新）：**
- 1.2.1 数据流 ASCII 图（源码行号标注）
- 1.2.2 两表结构对比（61列/1.8M行 vs 62列/6,150行，行数悬殊原因说明）
- 1.2.3 basic_data_loan_fcl 7组字段详解（基础标识/FCL状态/阶段时间线/耗时/金额/司法属性/Hold详情）
- 1.2.4 basic_data_loan_foreclosure 新增字段（INSERT填充32列，30列为NULL，逐一标注）
- 1.2.5 Servicer 覆盖限制（Redshift实测：Newrez 1,524,631行/Carrington 305,662行/CapeCodFive 5,793行；FCL Stage分布）

**验证方式**：PrefectFlow源码（Line 149-305 + Line 1530-1692）+ Redshift实时查询（2026-05-25）双重验证

---

### Milestone: FCL Data Lineage & Rules Document (07) completed [2026-05-24]

**Deliverables (4 files):**

| File | Status |
|------|--------|
| `docs/zh/07_fcl_lineage_and_rules.md` | ✅ Created |
| `docs/en/07_fcl_lineage_and_rules.md` | ✅ Created |
| `docs/zh/00_index.md` | ✅ Updated (07 entry + reading path added) |
| `docs/en/00_index.md` | ✅ Updated (07 entry + reading path added) |

**Key findings (source-code verified from PrefectFlow):**
- SLS, Newrez, Carrington: ✅ Full FCL determination in `daily_data_loan_common_clean_config.py`
- Arvest, CapeCodFive: 🟡 Text match only (`svcdelinq = 'Foreclosure'`), monthly path only
- Selene, MRC: 🟡 `fcl_flag` captured in Step 2 but **absent from Step 3** — FCL falls through to days360 (max D120P, never FCL)
- FCI, Rocket, SPS: ❌ No FCL logic implemented
- Universal priority stack: explicit text → fcl_flag → days360 → manual fix override
- Per-servicer recommended fix SQL documented based on actual available fields

---

### Milestone: Foreclosure Data Dictionary v1 [2026-05-23]
- **产出文件**: `C:\Users\jli\MyData\Copilot\ForeclosureRule2\docs\foreclosure_data_dictionary.md`
- **覆盖表数**: 12 张核心表（Layer 1 ~ Layer 3）
- **覆盖字段**: 每表 10-25 个 Foreclosure 相关字段，含置信度标注
- **Simplify**: 本次为文档生成任务，无代码变更，跳过 `/simplify`
- **测试**: 文档已与源码（SQL/Python）交叉核验，字段来源可追溯

---

### Milestone: docs/en/01_source_data.md v2 completed [2026-05-21]

**English v2 enhancements applied (matching zh v2):**
- Added DB connection info section (MySQL host, port, schema-per-servicer table)
- Added table naming change notice (`portshellpoint*` → `portnewrez*`)
- Per-servicer section headers with Database/Schema labels
- Each table: description, fully qualified name, total row count, key ID/date field info
- All field tables split into Part A (Field | Type | Meaning | Value Range | Calculation Logic | FCL Related) + Part B (Field | Example Values | Statistics)
- Corrected Carrington fields: removed non-existent `status`/`foreclosure_status_code`; documented real fields (`loan_status`, `fcl_flag`, `fcl_status`, `fcl_sub_status`, `fcl_referral_date`, etc.)
- Added `delinquency_status_mba` → `delinq` complete 18-value mapping table (Newrez)
- Added `delq_status_mba` → `delinq` 8-value mapping table (SLS)
- Added `loan_status` complete 16-value distribution table with mapped `delinq` (Carrington)
- Updated Known Limitations to 7 items
- v2 revision history entry added

## [2026-05-26 UTC] 询问MCP自动触发机制
> 你会自动使用MCP吗？在什么情况自动触发MCP?


## [2026-05-26 UTC] 演示MCP查询
> 演示一次 MCP 查询


## [2026-05-26 UTC] Update 12_sync_asset_management.md table names to schema.table format
> 12_sync_asset_management.md，pls display the table name use this format: schema.table, because there are many schemas in the dB


## Decisions

### Decision: MySQL schema prefix for BPS sync tables [2026-05-26]
- **Context**: User requested schema.table format for MySQL target tables in 12_sync_asset_management.md
- **Options considered**: A) `bpms`, B) `bps`, C) `{bps|bpms}` placeholder
- **Choice**: `bpms` for all sync_* tables; `port` for basic_data_loan_foreclosure
- **Reason**: Confirmed via MCP query (information_schema.TABLES): sync_* tables only exist in bpms_dev/bpms_test/bpms_uat on this server (no bps_* schemas). basic_data_loan_foreclosure confirmed to exist in MySQL `port` schema only.


## [2026-05-26 UTC] 逆向推导 BPS FCL 展示字段的来源逻辑（Newrez 为例）
> 之前我是以我调研到的美国贷款的业内通用的 Foreclosure 数据字段 输出了 08/09/11 文档，今天Boss要求要以我们公司的BPS系统所展示的Foreclosure信息为结果导向，倒推我司目前是如何利用Servicer提供的数据进行怎样的逻辑计算、Mapping rules的，得出BPS Asset Management系统所需的servicer提供的贷款的Foreclosure的字段（请不要输出中间的代码数据流的处理信息，只重点关注从Service原始数据字段直接到 BPS Asset Management系统 界面展示的字段的逻辑计算规则），先以数据比较规则的servicer Newrez为例



## [2026-05-26 UTC] UI截图核对BPS FCL字段映射（doc 13 v2）
> 这是BPS系统有关foreclosure的界面，请再核对一下里面用到的字段 跟 mysql数据库中schama.table.field的逻辑对应关系，以及 mysql数据库中schama.table.field的逻辑对应关系 跟 servicer newrez 的原始数据schema.table.field 的对应关系

### Decision: Doc 13 v2 scope [2026-05-26]
- **Context**: User provided actual BPS UI screenshots revealing 3 missed panels and several errors in v1
- **Options considered**: A) Targeted edits B) Full document rewrite
- **Choice**: Full rewrite (Write tool) — too many structural changes (new sections, renumbering, corrections)
- **Reason**: v1 missed Hold history model, LM Cycle panel, Bankruptcy panel, Aggregate view; main table name wrong; view column count wrong; LM encoding description wrong

## Milestones

### Milestone: Doc 13 v2 — UI-Grounded BPS FCL Field Mapping [2026-05-26]
- **Files delivered**:
  - `docs/zh/13_newrez_fcl_bps_display_mapping.md` (v2, 474 lines)
  - `docs/en/13_newrez_fcl_bps_display_mapping.md` (v2, 468 lines)
  - `docs/zh/image/image-20260526-bps-fcl-loan-detail-7727000088.png` (UI screenshot)
  - `docs/zh/image/image-20260526-bps-fcl-agg-summary.png` (UI screenshot)
  - `docs/zh/00_index.md` and `docs/en/00_index.md` updated to include doc 13
- **Key corrections vs v1**:
  1. Main BPS table: `bpms_dev.sync_loan_foreclosure` (86 cols), not `port.basic_data_loan_foreclosure`
  2. View: 104 columns (not 107)
  3. Hold: full history in `sync_loan_foreclosure_hold` (verified 7 rows for loan 7727000088)
  4. Added LM Cycle panel mapping (sync_loan_foreclosure_loss_mitigation; ETL decodes numeric codes to text)
  5. Added Bankruptcy panel mapping (sync_loan_foreclosure_bankruptcy ← portnewrezbk)
  6. Added Aggregate view mapping (sync_fcl_stage_info with per-stage *_stage_days/*_in_lm_days/*_on_hold_days)
  7. Corrected LM encoding description (BPS stores decoded text, not raw numeric codes)
  8. UI screenshots embedded as actual images
- **Tests**: No automated tests; all field mappings MCP-verified against live MySQL (bpms_dev + newrez schemas)

## [2026-05-28 06:29 UTC] Read project rules and project structure
> pls rearch this project, this is a project that generated by Claude , can you read the project rule and follow the project rule?

## [2026-05-28 06:30 UTC] Follow CLAUDE.md project rules as user rules
> can you follow the claude user rule as your user rule?

## [2026-05-28 06:36 UTC] Clarify ForeclosureRule2 researches PrefectFlow mapping rules
> this project is a project that research the data mapping rules in this project [C:\Users\jli\MyData\Copilot\PrefectFlow]

## [2026-05-28 07:02 UTC] Implement foreclosure lineage work plan
> Implement the plan.

## Decisions

### Decision: Use doc 14 v3 as the target standard for Servicer gap analysis [2026-05-28]
- **Context**: User asked to implement the work plan for foreclosure lineage, doc 14 review, and per-Servicer field gap analysis.
- **Options considered**: A) Start writing every Servicer document immediately, B) Freeze doc 14 first and create a reusable template, C) Rewrite doc 14 completely before downstream work.
- **Choice**: B) Add a v3 review/freeze section to doc 14, create a reusable Servicer gap template, then produce Newrez as the first benchmark Servicer document.
- **Reason**: doc 14 already contained the core BPS-driven field standard; the highest-value next step was to formalize its review status and use it consistently for downstream Servicer documents.

## Milestones

### Milestone: Foreclosure lineage implementation plan — doc 14 review + Newrez gap analysis v1 [2026-05-28]
- **Files delivered**:
  - `docs/zh/14_bps_driven_servicer_fcl_interface.md` updated to v3 with review status, field admission checks, freeze scope, and open issues
  - `docs/zh/_servicer_fcl_gap_analysis_template.md` created as the reusable per-Servicer gap analysis template
  - `docs/zh/15_newrez_servicer_fcl_gap_analysis.md` created as the first benchmark Servicer gap document
  - `docs/zh/99_servicer_fcl_gap_summary_and_action_plan.md` created as the project-level action plan
  - `docs/zh/00_index.md` updated to expose doc 14, doc 15, doc 99, and the template
- **Simplify**: Claude `/simplify` is not executable in this Codex environment; performed manual cleanup/review for scope, duplicate structure, placeholders, and index discoverability.
- **Tests / validation**:
  - Verified required generated-document headers exist in doc 14, doc 15, doc 99, and the template
  - Verified new docs are referenced from `docs/zh/00_index.md`
  - Verified `15_newrez_servicer_fcl_gap_analysis.md` contains no template placeholders
  - No automated test suite exists for these Markdown-only documentation changes

## [2026-05-28 08:02 UTC] Implement MCP database verification strategy
> Implement the plan.

## Decisions

### Decision: Use MCP as the default database verification path [2026-05-28]
- **Context**: User provided MySQL and Redshift connection information and asked whether MCP should be established for database verification during the research process.
- **Options considered**: A) Use ad hoc Python direct connections, B) Use MCP as the default and keep Python as fallback, C) Avoid DB validation and rely on existing docs.
- **Choice**: B) Use MCP as the default read-only validation path, with Python fallback only for batch exports or complex local statistics.
- **Reason**: The project already has `.mcp.json` with MySQL and Redshift MCP servers configured; MCP gives better repeatability and reduces the need to spread credentials in scripts or documents.

## Milestones

### Milestone: MCP database verification standard v1 [2026-05-28]
- **Files delivered**:
  - `docs/zh/98_database_verification_strategy.md` created with MCP-first read-only validation rules, SQL evidence requirements, standard query patterns, fallback guidance, and sensitive information rules
  - `docs/zh/_servicer_fcl_gap_analysis_template.md` updated to v2 with a mandatory database verification plan section
  - `docs/zh/15_newrez_servicer_fcl_gap_analysis.md` updated to v2 with SQL-15-1 through SQL-15-5 for refreshing Newrez field existence, fill rates, LM/BK checks, and BPS Stage samples
  - `docs/zh/99_servicer_fcl_gap_summary_and_action_plan.md` updated to reference doc 98 as the validation standard
  - `docs/zh/00_index.md` updated to expose doc 98 and the new reading order
- **Simplify**: Claude `/simplify` is not executable in this Codex environment; performed manual cleanup/review for duplicate guidance, scope, and credential leakage.
- **Tests / validation**:
  - Verified no database passwords or connection strings were copied into the new/updated Markdown docs
  - Verified doc 98 has the required generated-document header sections
  - Verified doc 98 is referenced from `docs/zh/00_index.md`
  - Verified Newrez doc contains concrete SQL references and no template placeholders
  - No automated test suite exists for these Markdown-only documentation changes

## [2026-05-28 08:46 UTC] Add code-first ETL analysis rule to project and user rules
> pls add this rule to your project level rule and user level rule ,do you have this two rules file? 在分析任何 ETL 管道、数据流、表写入机制时：
>   ▎ 1. 必须先读源代码（config 文件、util 函数、SQL 模板），再做结论。MCP
>   ▎ 数据查询只能验证"当前状态"，不能证明"为什么"和"怎么写入的"。
>   ▎ 2. 禁止仅凭以下现象做架构推断：NULL timestamp、行数差异、字段值不匹配——这些可能是 ETL 延迟、环境差异、或 SQL
>   ▎ 设计，不代表独立机制。
>   ▎ 3. 当代码与 MCP 数据矛盾时，代码优先；MCP 显示的是某一时刻的状态快照，代码显示的是设计意图。

## Decisions

### Decision: Store code-first ETL rule in CLAUDE.md and global AGENTS.md [2026-05-28]
- **Context**: User asked to add a rule at both project level and user level for ETL/data-lineage analysis.
- **Options considered**: A) Project `CLAUDE.md` only, B) Global `C:\Users\jli\.codex\AGENTS.md` only, C) Both files.
- **Choice**: C) Add the rule to project-level `CLAUDE.md` and user-level `C:\Users\jli\.codex\AGENTS.md`.
- **Reason**: `CLAUDE.md` is the project rule file for ForeclosureRule2, while `C:\Users\jli\.codex\AGENTS.md` is the available user-level instruction file. `.codex\rules\default.rules` stores command permission rules, not behavior instructions.

## Milestones

### Milestone: Code-first ETL analysis rule added [2026-05-28]
- **Files delivered**:
  - `CLAUDE.md` updated with mandatory Code-First ETL / Data Lineage Analysis Rule
  - `C:\Users\jli\.codex\AGENTS.md` updated with the same user-level rule
- **Rule summary**:
  1. Read source code before making ETL/data-flow/table-write conclusions
  2. Do not infer architecture from symptoms alone, such as NULL timestamps, row count differences, or field mismatches
  3. If source code and MCP data conflict, use code as the priority source for design intent and MCP as point-in-time validation/anomaly evidence
- **Simplify**: Claude `/simplify` is not executable in this Codex environment; performed manual review for duplicate placement and wording consistency.
- **Tests / validation**:
  - Verified the rule exists in both `CLAUDE.md` and `C:\Users\jli\.codex\AGENTS.md`
  - Verified `.codex\rules\default.rules` was not changed because it is a command permission file, not a user behavior rule file

## [2026-05-29 01:46 UTC] Organize doc 13 manually added images and sync to English doc
> can you see dthe doc 13 [13_newrez_fcl_bps_display_mapping.md]  have some images? this were added by me, manaually, can you organize the images(add a official title ) and sync it to the corresponding EN doc? what is your recommendation?

## Decisions

### Decision: Standardize doc 13 screenshots as numbered Figure 13-x captions [2026-05-29]
- **Context**: User manually added BPS screenshots to the Chinese doc 13 and asked for organization plus English synchronization.
- **Options considered**: A) Only add alt text, B) Add official titles and leave images only in Chinese, C) Add numbered figure titles, use relative paths, and mirror the same figure set in English.
- **Choice**: C) Number all screenshots as Figure 13-1 through Figure 13-9 and synchronize them into the English document at corresponding sections.
- **Reason**: Numbered captions make the screenshots citable in later text and reviews; relative paths keep the docs portable; English sync keeps bilingual documentation aligned.

## Milestones

### Milestone: Doc 13 screenshot organization and English sync [2026-05-29]
- **Files delivered**:
  - `docs/zh/13_newrez_fcl_bps_display_mapping.md` updated to v24 with official Figure 13-x titles and relative image paths
  - `docs/en/13_newrez_fcl_bps_display_mapping.md` updated to v24 with matching English titles and the same 9 screenshot references
- **Key changes**:
  - Added official captions for full loan detail page, aggregate Stage Tab, aggregate Time Line Tab, Foreclosure Milestone, Foreclosure Summary, Hold, LM Cycle, Bankruptcy, and Stage grouped detail screenshots
  - Replaced absolute Windows image paths with relative paths in the Chinese doc
  - Added the Chinese-only manually inserted screenshots to the corresponding English sections
- **Simplify**: Claude `/simplify` is not executable in this Codex environment; performed manual cleanup for duplicate spacing, path consistency, and title alignment.
- **Tests / validation**:
  - Verified both Chinese and English doc 13 contain 9 image references
  - Verified every referenced image file exists
  - Verified no remaining absolute Windows image paths or backslash image paths in doc 13

## [2026-05-29 02:01 UTC] Rename doc 13 screenshot files with business-meaningful names
> 你可以修改一下文档中的图片的文件名的名称，让该图片的文件名是有业务含义的，可理解的

## Decisions

### Decision: Use business-meaningful English slug filenames for doc 13 screenshots [2026-05-29]
- **Context**: User requested renaming doc 13 image files so the filenames are understandable and business-meaningful.
- **Options considered**: A) Keep timestamp filenames and only rely on captions, B) Rename files with Chinese names, C) Rename files with concise English slug names.
- **Choice**: C) Rename the 9 doc 13 screenshots with concise English slug names matching their BPS panel/page meaning.
- **Reason**: English slug filenames are portable across tools, readable in both zh/en docs, and avoid encoding/path issues while preserving business meaning.

## Milestones

### Milestone: Doc 13 screenshot filenames renamed [2026-05-29]
- **Files renamed**:
  - `image-20260526-bps-fcl-loan-detail-7727000088.png` → `bps-loan-foreclosure-detail-loan-7727000088.png`
  - `image-20260526-bps-fcl-agg-summary.png` → `bps-foreclosure-aggregate-stage-tab-summary.png`
  - `image-20260527041231766.png` → `bps-foreclosure-aggregate-time-line-tab.png`
  - `image-20260527014246372.png` → `bps-loan-foreclosure-milestone-timeline-panel.png`
  - `foreclosure-summary.png` → `bps-loan-foreclosure-summary-panel.png`
  - `image-20260527013657760.png` → `bps-loan-foreclosure-hold-panel.png`
  - `image-20260527015824072.png` → `bps-loan-foreclosure-loss-mitigation-cycle-panel.png`
  - `image-20260527021837676.png` → `bps-loan-foreclosure-bankruptcy-panel.png`
  - `image-20260527031315386.png` → `bps-foreclosure-aggregate-stage-tab-grouped-detail.png`
- **Files updated**:
  - `docs/zh/13_newrez_fcl_bps_display_mapping.md` updated to v25 with new image paths
  - `docs/en/13_newrez_fcl_bps_display_mapping.md` updated to v25 with matching new image paths
- **Simplify**: Claude `/simplify` is not executable in this Codex environment; performed manual cleanup for filename consistency and cross-language references.
- **Tests / validation**:
  - Verified both zh/en doc 13 contain 9 image references
  - Verified all 18 zh/en image references resolve to existing files
  - Verified old timestamp-style filenames are no longer referenced by doc 13
