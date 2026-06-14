# 32 · 全 Pipeline 逐字段 Mapping + 生产数据举例（doc 32 导读）

> 本文是 **导读**。逐字段内容、规则、生产实测举例都在配套工作簿
> [`docs/32_fcl_pipeline_field_mapping.xlsx`](../32_fcl_pipeline_field_mapping.xlsx)。
> 本 MD 只讲「为什么、怎么读、范围」，不复制字段内容（单一真源是 JSON，见下）。

## 文档信息

| 项目 | 内容 |
|------|------|
| **文档目的** | **Why**：把整条 FCL pipeline 的数据处理「演」出来——每个字段从 servicer 原始列，经每一层（L1→L5），到 BPS sync 表，逐字段写清**每跳转换规则**，并用**生产实测数据**举例。**What problem**：doc 19 是「按表/按贷款的 raw dump」、doc 26–31 是叙述式逐字段血缘；本文提供一份**可筛选、可对账、带色卡与导航**的 Excel，把「字段 × 逐层规则 × 生产实测」三者合一。**Scope**：Phase 1 pilot **只覆盖主链 `bpms.sync_loan_foreclosure`**（含主链中间表）；其余 4 链与全部 ~23 表见 Phase 2。**System fit**：Excel 为可对账视图，叙述仍指回 doc 25–31；与 doc 02/13/14 的字段口径一致。 |
| **目标读者** | 数据工程师 · 业务分析 · 对账/校验人员 · servicer onboarding · 未来 AI 会话 |

**修订历史：**

| 日期 | 作者 | 版本 | 变更 | 相关 |
|------|------|------|------|------|
| 2026-06-10 | AI Agent (Claude Opus 4.8) | v1 | Phase 1 pilot：主链 sync_loan_foreclosure 逐字段 mapping + 20 笔生产举例 + 多 as-of 改期演示 + BPS 截图三方对账 | doc 25/26, 02, 13, 14；skill `excel-pipeline-lineage` |
| 2026-06-12 | AI Agent (Claude Opus 4.7) | v2 | §关键口径 +bullet 6「投影列」(SQL π / pool:253-305 + CC5 7727004824 跨表对照) +bullet 7「bpms 主表」(=sync_loan_foreclosure + sibling 4 表 + 视图层 + CC5 0 笔进入原因 asset:605)；Sheet C 描述补 footnote 链向 bullet 7 | doc 33 §2 / §2.5.1 |
| 2026-06-12 | AI Agent (Claude Opus 4.8) | v3 | 5 张非 src 逐表 sheet（⑨⑩⑪⑱⑳）右侧新增 **25 笔样本贷款「逐层真值举例列」**（1 列 1 贷款，序同 C 页；冻结前 4 列、举例列可折叠）；全历史字段（拍卖/判决听证首见 set_date）采用**方案B**：格内当前值下附多天提示。真源 `outputs/fcl_layer_examples.json`（prod 只读、schema-verify 通过） | skill `excel-pipeline-lineage`；D 页改期演示 |
| 2026-06-13 | AI Agent (Claude Opus 4.8) | v6 | 🧮 公式列改为**每 servicer 一列**（🧮·Newrez 7727003984 + 🧮·Carrington 7727000806），各列内部统一引用该 servicer 那笔→列自洽、并排展示 servicer 差异（daysinfc：Newrez 461 直传 vs Carrington 477 datediff，真 Excel 实算确认）；Carr 计算列加 null-guard、⑨ Carr 直传标「源未纳入」。336×2=672 格→476 公式+196 注。真 Excel 0 错误 | 测试报告 v5 |
| 2026-06-13 | AI Agent (Claude Opus 4.8) | v7 | **澄清 daysinfc 规则 + 非copy计算规则在「计算逻辑」cell内附本笔真值工作示例**。daysinfc 旧写「rename (Newrez) / computed (others)」既错(Newrez 是 copy 非 rename)又含糊；真源 `fcl_lineage_source.json` 改为「Newrez 直传同名列；Carr/CC5 = FCL活跃 ? datediff(referral,快照日)+1 : NULL」（code pool:1546/1587/1628，已核代码）→ 重跑 inject_glin 刷 HTML + doc 26 zh/en 同步。生成器新增 `eg_worked()`：用 demo loan 真值给 servicer/daysinfc/activefcflag/fcstage/summary_foreclosure_status/summary_type/⑱ days 重算/⑳ actual_* 生成「｜ 例 …」工作示例（纯 copy 不举例）。审计 0 个真计算字段缺示例；真 Excel 0 错误；内容级幂等 | doc 26；pool:1546/1587/1628 |
| 2026-06-13 | AI Agent (Claude Opus 4.8) | v8 | **⑨ Carrington 派生字段从文字注 → 活 Excel 公式**。此前 ⑨ `activefcflag` 的 🧮·Carrington 列是文字注（输入 `fcl_flag` 在 `carrington.portcarrington`，本工作簿未建该 sheet，无格可引用）。现 ⑨ 表底新增「Carr 源输入演示」块（DB 实测 8 列：fcl_flag/fcl_sub_status/fcl_referral_date/carrington_ln/sale 日期/fcl_attorney_name/snap，loan 7727000806），Carr 派生字段引用该块出**活公式**：`activefcflag=IF(块!fcl_flag="Active",1,"∅NULL")`、`fcstage/svc_loanid/referral/fcfirm/dataasof`=直接引用；⑩ Carr activefcflag/fcstage 直传引用 ⑨ 格；仅该 UNION 分支恒 NULL 字段标「Carr 分支=NULL 常量」。真 Excel 实算 ⑨ activefcflag=1/svc_loanid=3000077131/referral=2025-02-19/daysinfc=477、0 错误；公式 476→487。真源 `outputs/fcl_carr_source_demo.json`（DB 只读） | pool:1574-1611；测试报告 TC16 |
| 2026-06-13 | AI Agent (Claude Opus 4.8) | v9 | **新增 ②c src·portcarrington 独立 src 表（Carrington L1 源），替代 v8 的 ⑨ 表底 demo 块**。代码核实 CREATE_BASIC_FCL UNION 三 servicer 源（newrez.portnewrezfc / **carrington.portcarrington** / capecodfive.portcapecodfive_monthly_collections，pool:1572/1613/1654），此前只渲染 Newrez ②。新 ②c sheet 与 ② 对称（25 样本列：5 Carr 实测、20 Newrez=∅NULL），只渲染 pipeline 实际消费的 9 列（portcarrington 共 199 列）；⑨ 的 Carr 派生字段公式改为引用 ②c 该笔格（真上游），`activefcflag=IF('②c…'!fcl_flag="Active",1,∅NULL)` 等；删 ⑨ demo 块。fcl_table_meta 加 ②c（doc 32 临时号，全局 23→24 重编号留 doc 19/25 同步）。5 Carr loan 值 DB 只读实测、9 列 information_schema 全核存在；真 Excel 17 sheet 0 错误、值不变、幂等。真源 `fcl_field_meanings.json`+`fcl_layer_examples.json`+`fcl_table_meta.json` | pool:1572-1654；测试报告 TC17 |
| 2026-06-13 | AI Agent (Claude Opus 4.8) | v10 | **Phase 2：新增 stage/hold/lm/bk 四链逐表 sheet（17→25 sheet）**。⑬⑲(阶段)/⑮㉑(暂停)/⑯㉒(损失缓释)/⑰㉓(破产) 各表均含 字段+业务含义+计算逻辑(lineage)+来源/类型+逐层举例列(25)+每 servicer 🧮 公式列。举例数据 DB 只读实测(子agent 写 `fcl_layer_examples_phase2.json`，8 表 schema-verify 0 缺失；多行表 hold/lm/bk 取代表性最新行)；BPS 侧公式=活引用 Redshift 上游(IMM_UP 扩四链)。公式 487→677、真 Excel 25 sheet 0 错误、幂等。同期 `fcl_pipeline.html` 升级为知识图谱(第6视图,386节点/963边/1连通)。综合测试见 doc 34 | doc 34；asset:925/829 |
| 2026-06-14 | AI Agent (Claude Opus 4.8) | v11 | **逐表 sheet 改按【圈号升序】排列**（原按业务链分组；用户反馈按编号更好找）；**Phase 3 新增 ③④㉔（25→28 sheet）**：③src·portnewrezbk、④src·portnewrezlm（bk/lm 的 L1 raw 源，同 ② 只有 字段+举例，DB 实测、多行取代表性最新行）+ ㉔dic·portnewrezdatadic（解码字典 sheet：BKStatus/BKStage/LMDeal/LMDecision/LegalStatus/MBADelinquency 等 12 类 140 行 code→文本）。**Schema-Verify 纠错**：解码字典长表实测仅在 redshift_prod（mysql 的 newrezdatadic 是另一张宽表、无 LM/BK），已订正 ㉔ 表元。真 Excel 28 sheet 0 错误、幂等。仍无 sheet：⑤⑥⑦⑧⑫⑭ | pool:367/835-840；redshift_prod.newrez.portnewrezdatadic |
| 2026-06-14 | AI Agent (Claude Opus 4.8) | v12 | **Phase 4 新增 ⑤⑥⑫（28→31 sheet）**：⑤src·portnewrezgeneral(125字段)、⑥src·portnewrezprop(32字段)（L1 源，is_src=字段+举例，DB 实测、各 20/25 loan 有行）+ ⑫mid·fcl_related(14字段，⑬ group 的 r 源)：字段+计算逻辑(新增 field_rule 14条,pool:1697-1770)+25 举例+每 servicer 公式。⑫ Newrez 派生字段活引用上游——`propertystate`→⑥、`isloanlitigated/deactreason/reasonfordefault/inauctionflag`→⑤、`bk_flag`→③.activebkflag、`servicer`=常量、`delq_status`=CASE(注)；Carr 分支源列(litigation_type/property_state…)未纳入 ②c→注。真 Excel 31 sheet 0 错误、幂等。仍无 sheet：⑦⑧⑭ | pool:1697-1770；doc 34 |
| 2026-06-13 | AI Agent (Claude Opus 4.8) | v5 | **全字段 🧮 覆盖**：用 lineage hops + 同名直传，把 5 非 src 表**每个字段**的 🧮 填为「引用上游层活公式」(直传/改名 `='上游'!cell`→整条 pipeline 成可联动活链)；336 字段→247 活公式+89 诚实注。② 补 25 笔源头数据。真·Excel(COM) 复算 0 错误 | `fcl_lineage_source.json` hops；测试报告 v4 |
| 2026-06-12 | AI Agent (Claude Opus 4.8) | v4 | 5 张非 src sheet「来源/类型」后新增 **「🧮 公式演示」列**：精选 9 条可单格表达的逻辑写**活 Excel 公式**（CASE 止赎状态/类型、Carr daysinfc datediff、days 实时重算、actual_X TO_DAYS 差、改名直传），显示码在公式内当空处理(VALUE/DATEVALUE)，跨层逻辑用跨 sheet 引用；**高亮**该笔 demo loan 的输入(浅蓝)/输出(浅橙)/公式(浅绿)格 + 公式格批注。冻结改前 5 列。另：全历史「首见 min(dataasof)」(set_date)用**方案3**——⑪⑱ 表底加 3 行抽样块 + 矩阵 set_date 行 🧮=实时 `MINIFS`、D 页自包含块。真源 `outputs/fcl_formula_demos.json` + `outputs/fcl_minihist_demos.json` | doc 33 §2.5；pool:273/279/300/1628、asset:597 |

**依赖（单一真源 JSON，脚本只排版）：**
- `outputs/fcl_lineage_source.json` — 逐字段 hops + 每跳规则 + 代码出处（与 doc 26 同源）
- `outputs/fcl_table_meta.json` — 23 表业务含义/血缘元数据
- `outputs/fcl_field_meanings.json` — 逐表字段含义
- `outputs/fcl_pipeline_examples.json` — prod 只读拉取的 20 笔举例 + 改期历史 + BPS 截图锚点
- `outputs/fcl_layer_examples.json` — **逐层逐字段 25 笔样本真值**（5 张非 src 表的逐表 sheet 举例列真源；prod 只读，含全历史字段的多天提示）
- `outputs/fcl_formula_demos.json` — **🧮 公式演示规格**（精选可单格表达的转换逻辑 → 活 Excel 公式 + 高亮配色；脚本只排版）
- `outputs/fcl_minihist_demos.json` — **首见 min(dataasof) 活公式数据**（方案3 多值小块：⑪⑱ 表底 + D 页 MINIFS 演示）
- 生成器：`outputs/build_fcl_pipeline_mapping_xlsx.txt`（`python - < …txt` 运行，幂等可重跑）

---

## 怎么读这个工作簿

打开 xlsx，首张 **🧭 导航 Index** 点「➤ 打开」可跳到任意 sheet。

**仿 doc 19**：全局/导航页 + 分析视图（字母）+ 逐表页（圈号·层级标签 src/mid/bps）。

| Sheet | 看什么 |
|---|---|
| **① 表清单 索引** | 首张索引，**分层分组**（分析视图 / 一 Newrez源 src / 二 Redshift中间层 mid / 三 BPS对接 bps / 四 字典 dic）+ 列数 + 「➤ 打开」跳转链 |
| **⓪ 表说明与全链路血缘** | 全 23 表总览：层级 / 业务含义 / pipeline 作用 / 上下游链路 / 粒度（仿 doc 19 ⓪） |
| **⓪b 全局Pipeline图** | L1→L5 网格图：各层表 + 主线/逾期支线/维度字典 + 图例（仿 doc 19 ⓪b） |
| **A 导读·色卡·样本** | 读法、as-of/多天说明、**转换类型色卡 + 一行定义**、样本贷款清单（Newrez 20 + Carrington 5，与 C 页一致） |
| **B 主表逐字段 Mapping** | 一字段一行：目标字段 → L1 servicer 源 → L4 fcl 族 → L4 foreclosure 投影(+代码) → L5 upsert/视图规则 → **转换类型**(色卡) → 代表样本。可筛选 |
| **C 生产数据矩阵（样本）** | 样本贷款 × 主表关键字段**最新快照实测值**（Newrez 20 + Carrington 5 广度 + CC5 说明，**非全量**——实际进 bpms 约 91 笔）。⚙️ "bpms" = **bpms 主表** = `bpms.sync_loan_foreclosure`，定义见 §关键口径 bullet 7 |
| **D 多as-of 改期演示** | `7727003984`（改期 12 次）+ `7727000367`（稳定值反例）的多天历史，演示 `set_date` vs `projected` |
| **E BPS 截图证据** | 嵌入 BPS UI 截图 + 代码⇄Redshift⇄BPS UI 三方对账 |
| **F 逻辑类型目录** | FCL 全部**字段级逻辑 LT01–LT30+SYS**（每类 历史依赖 + 示例字段 + 覆盖字段数 + 示例 loan + ✓体检）+ **管道级机制 M1–M5**（标演示位置）。体检：26 类直接覆盖 + 4 类(LT04/13/14/21)覆盖于上游 Redshift/视图/合并 + 0 真缺 → 30/30 已说明 |
| **G 字段级逻辑清单** | **字段驱动·穷尽**：5 张 BPS sync 表全部 **154 字段**，每字段标 **LT#** + 规则摘要 + 历史依赖（每字段必有 LT，无空行）。真源 `fcl_lineage_source.json` + `fcl_pipeline.html`。可按 LT 筛选/排序 |
| **② src·portnewrezfc … ⑳ bps·view_loan_details** | 主链每张表（含中间表）一个 sheet：业务含义/全链路血缘 + 全字段清单。tab 名带 **src·/mid·/bps·** 层级标签。**非 src 表（⑨⑩⑪⑱⑳）每字段在「业务含义」旁加「计算逻辑/mapping rule（上游→本字段）」列**，非直传附实测例（源 fcl_lineage_source 逐跳 + pool/asset 代码行 + doc 33）。按表看：改名/UNION 在 ⑨⑩、首见/CASE/datediff 在 ⑪、upsert 透传在 ⑱、actual/var 公式在 ⑳；src ② 无计算逻辑/公式列，但**已补 25 笔源头原始值举例列**（servicer 原始表 `newrez.portnewrezfc`，pipeline 起点；Carrington=∅NULL）。**非 src 表「来源/类型」列右侧再加 25 笔样本贷款「逐层真值举例列」**（1 列 1 贷款，序同 C 页；冻结前 4 列、举例列可一键折叠；同一贷款顺 ⑨→⑩→⑪→⑱→⑳ 下看即见值的改名/派生/坍缩）。全历史字段（拍卖/判决听证首见 set_date）格内附**方案B**多天提示（完整改期链见 D 页）；∅NULL=真实空、∅空串=空字符串。真源 `fcl_layer_examples.json`。**另在「来源/类型」后加两个「🧮 公式演示」列（每 servicer 一列：Newrez 7727003984 / Carrington 7727000806）**：每字段都有活公式(点击看)——直传/改名=引用上游层该笔格 `='上游'!cell`(改 ② 源头值会一路联动上来)、计算=真公式(显示码当空)、结果=该 servicer 该笔实测值;少数(NULL投影/SLA常量/系统列/decode/Hold多行/视图实时算)注明原因(绿=公式/灰=注)。例 daysinfc：Newrez=461 直传 vs Carrington=477 datediff（真 Excel 实算确认）。⚠️ Carr 源(非②)未纳入→⑨ Carr 直传标「未纳入」。真源 lineage hops + `fcl_formula_demos.json` |

> **关于圈号 ②⑨⑩⑪⑱⑳**：是「全 FCL pipeline 23 表的**全局编号**」（与 doc 19/25、`fcl_table_meta.json` 一致）。② src·portnewrezfc、⑨ mid·temp、⑩ mid·fcl、⑪ mid·foreclosure、⑱ bps·sync主表、⑳ bps·视图。缺号（③④…⑬⑲…）是本 pilot 尚未纳入的表，**Phase 2 补齐，不是排序错误**（① 表清单索引里这些表已列出、标「Phase 2 待补」）。分析视图用字母 A–E，与表号区分。

**转换类型** 一行定义（A 总览页色卡同款）：直传＝值与列名都不变的纯透传；**改名**＝值不变但中途列名改过；**首见日**＝取 `min(dataasof)`（当前值首次出现日，需多天历史）；天数重算＝存储天数+datediff(dataasof→运行日)；decode解码＝字典译码；CASE派生＝条件分支/拼接；常量NULL＝硬编码常量/空；其他＝主键/审计/视图列。

> **字段全限定记法 `db.schema.table.field`**（Sheet D / E 起用）：Redshift = `dev.<schema>.<表>.<列>`（catalog 名为 `dev`，实为 prod 集群，如 `dev.port.basic_data_loan_fcl.fcscheduled_sale_date`）；MySQL/BPS 无独立 schema 层，记为 `bpms.<表>.<列>`（如 `bpms.sync_loan_foreclosure.timeline_sale_date_set_date`）。

## 关键口径（已核代码 + prod 实证）

1. **`bpms.sync_loan_foreclosure.timeline_sale_date_projected_date`（projected）= 当前(最新 as-of)值**；**`bpms.sync_loan_foreclosure.timeline_sale_date_set_date`（set_date）= 该当前值首次出现的 `dataasof`**（`min(dataasof WHERE 值=当前值)`，`basic_data_pool_config.py:300-303`；按天追踪上游 `dev.port.basic_data_loan_fcl.fcscheduled_sale_date`）。改期链只有多天历史可见（见 Sheet D）。
2. **多天数据的意义**：仅 `*_set_date`/`judgement_hearing_set`/`*_days`（首见、天数重算）需多天；直传/decode 字段多天恒等，取最新快照即可。`basic_data_loan_fcl` 保留全部每日快照（943 个 dataasof）；`basic_data_loan_foreclosure`=MAX(dataasof) 每贷款最新；sync 主表当前态无 as-of。
3. **`summary_current_step` = `fcstage` 直传**（`pool:282`；`currentmilestone` ETL 未使用）——与本仓库 doc 13/14 v 最新更正一致。
4. **`bpms.sync_loan_foreclosure.summary_servicer_number`**：Newrez 样本实测全 NULL（prod 已知异常，doc 14 v34）。
5. **「取最新」橙色边两套规则**（见 D 页 7727003984 三日期对照 + F 矩阵注）：首见追踪 `min(dataasof)`（`bpms.sync_loan_foreclosure.timeline_sale_date_set_date` / `…timeline_judgement_hearing_set_date`，需全历史）vs 纯取最新直传（`bpms.sync_loan_foreclosure.timeline_sale_date_projected_date`、`bpms.sync_loan_foreclosure.summary_last_step_completed_date`=pool:284 直传 `dev.port.basic_data_loan_fcl.lastfcstepcompleteddate`，改期不更新、≠首见）。详见 **doc 33 §2.5.1**。

6. **📐 概念：什么是「投影列」？** —— 「投影」(Projection，关系代数 **π** 操作) 即 SQL `SELECT` 列表所选取的列；派生表从源表 `SELECT` 哪些列、改成什么名、是否做计算，那个完整列单就是该派生表的「**投影列**」。具体到 `dev.port.basic_data_loan_foreclosure`：该表由 `GEN_FCL_DETAIL` SQL（`basic_data_pool_config.py:253-305`）从 `dev.port.basic_data_loan_fcl` 投影而来，`SELECT` 列表里约 30 个列即「投影列」，例如：

   - `fc.noi_date AS timeline_notice_of_intent_date` —— 源列 `noi_date` 投影到新列名
   - `fc.legal_start_date AS timeline_first_legal_date` —— 改名投影
   - `fc.fcscheduled_sale_date AS timeline_sale_date_projected_date` —— 改名投影
   - `case when fc.activefcflag=1 then 'Active Foreclosure' ... AS summary_foreclosure_status` —— CASE 计算后投影
   - `ju.jd_set_date AS timeline_judgement_hearing_set_date`、`sa.sa_set_date AS timeline_sale_date_set_date` —— 来自子查询的派生投影（详 doc 33 §2.5.1）

   **Capecodfive Loan `7727004824` 跨表对照（prod MCP 2026-06-12 实测；4825/4827 同）**：

   | 阶段 / 字段 | 源列（`dev.port.basic_data_loan_fcl`） | 投影后（`dev.port.basic_data_loan_foreclosure`） |
   |---|---|---|
   | servicer 标识 | `servicer = "Capecodfive"` | （投影不含 servicer，此处仅作行存在性证据） |
   | NOI | `noi_date = NULL` | `timeline_notice_of_intent_date = NULL` |
   | Referral | `referral_start_date = NULL` | `timeline_referred_to_foreclosure_date = NULL` |
   | First Legal | `legal_start_date = NULL` | `timeline_first_legal_date = NULL` |
   | Service | `service_start_date = NULL` | `timeline_service_date = NULL` |
   | Sale Projected | `fcscheduled_sale_date = NULL` | `timeline_sale_date_projected_date = NULL` |
   | Sale Held | `fcsale_held_date = NULL` | `timeline_sale_date_held_date = NULL` |
   | Summary status | （CASE 输入字段全 NULL） | `summary_foreclosure_status = NULL` |

   **解读**：投影列 ≠ 来源原始列——`basic_data_loan_foreclosure.timeline_notice_of_intent_date` 是通过 `GEN_FCL_DETAIL` 投影出的**新列**（改名自 `basic_data_loan_fcl.noi_date`）；Capecodfive 这 3 笔样本源列即为 NULL，投影下来仍为 NULL，这就是「投影列实测全 NULL」的含义。详跨表彩色血缘见 **doc 33 §2.5.1**。

7. **📐 概念：什么是「bpms 主表」？** —— 「**bpms 主表**」= **`bpms.sync_loan_foreclosure`**（BPS MySQL 应用层的 FCL 主同步表），是本工作簿 Sheet C 默认的 lineage 终点；它与 BPS 库内 4 张 sibling sync 表 + 1 张视图区分如下：

   | 角色 | 表名 | 说明 |
   |---|---|---|
   | **bpms 主表（本工作簿默认终点）** | `bpms.sync_loan_foreclosure` | 1 行/loan · 含 `timeline_*` / `summary_*` / `target_*` / `bid_approval_*` 等所有主体字段。Sheet C「实际进 bpms 约 91 笔」即此表 |
   | sibling 1（Hold 长表） | `bpms.sync_loan_foreclosure_hold` | 1 loan 多 Hold；详 doc 28 |
   | sibling 2（LM 周期） | `bpms.sync_loan_foreclosure_loss_mitigation` | 1 loan 多 cycle；详 doc 29 |
   | sibling 3（BK 申请） | `bpms.sync_loan_foreclosure_bankruptcy` | 1 loan 多次申请；详 doc 30 |
   | sibling 4（阶段表） | `bpms.sync_fcl_stage_info` | 1 loan/fctrdt（保留多月快照）；详 doc 27/31 |
   | sibling 5（月度账务） | `bpms.sync_portmonth` | 视图日期差锚点；非 FCL 主线 |
   | 视图层 | `bpms.biz_data_view_loan_details_foreclosure` | 由 `sync_loan_foreclosure` LEFT JOIN `sync_portmonth`（详 doc 33 §2 + §3.1） |

   **为什么 Capecodfive「0 笔进 bpms 主表」？** —— `GEN_FORECLOSURE` 同步（`asset_managment_config.py:605`）有 2 个过滤条件：① `timeline_referred_to_foreclosure_date IS NOT NULL`；② `JOIN dev.port.portfunding`（已融资在投组）。CC5 的 382 笔在 fcl 投影列已全 NULL（见 bullet 6 跨表对照），`referral_date` 全空 → 第一个过滤条件即排除，0 笔进入 bpms 主表。主图见 **doc 33 §2**。

## 范围与分期
- **本期（Phase 1）**：主链 `sync_loan_foreclosure`（66 个已录字段 / 表 72 列）+ 主链中间表逐表 sheet。
- **后续（Phase 2）**：其余 4 链（`sync_fcl_stage_info` 接 doc 27/31、`_hold`、`_loss_mitigation`、`_bankruptcy`）+ 剩余中间表，补齐全部 ~23 表。
