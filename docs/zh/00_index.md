# ForeclosureRule2 — 止赎状态分析文档库（中文版）

---

## 文档信息

| 项目 | 内容 |
|------|------|
| **文档目的** | 本索引是 ForeclosureRule2 项目所有中文分析文档的导航入口。提供各文档的内容摘要、适用场景与阅读顺序建议。 |
| **解决的问题** | 解决 PrefectFlow 止赎处理逻辑分散在 500+ 个文件中、难以整体理解的问题。 |
| **覆盖范围** | 源数据 → ETL 管道 → 状态生成逻辑 → 状态枚举 → 属性映射 → 可视化图表 |
| **系统归属** | `C:\Users\jli\MyData\Copilot\PrefectFlow`（Prefect 2.x 抵押贷款服务 ETL 系统） |

**目标读者：** 数据工程师 · 业务分析师 · 系统重写架构师 · 新成员 · 验证/对账工程师 · 未来 AI 会话

**修订历史：**

| 日期 | 作者 | 版本 | 变更内容 |
|------|------|------|---------|
| 2026-05-21 | AI Agent (Claude Sonnet 4.6) | v1 | 初始版本，完整逆向工程分析 |
| 2026-06-08 | AI Agent (Claude Opus 4.8) | v2 | 用词正式化：doc 99 用例的汇报对象表述统一为「向管理层 / Reviewer 汇报」 |
| 2026-06-16 | AI Agent (Claude Opus 4.8) | v3 | 目录补齐：新增 doc 19（样例贷款原始转储）、doc 08-1（数据验证手册）行；新增交互件 `outputs/fcl_pipeline.html`（FCL Pipeline Explorer）条目；新增「测试报告」小节（doc 32 公式演示、doc 34 Phase2+KG）；「推荐阅读顺序」中已归档的 21 改为 25→26-30；更新 doc 32 描述（已扩展至 Phase 2-5 多业务链） |

---

## 文档目录

| 文档编号 | 文件名 | 核心内容 | 适用场景 |
|---------|--------|---------|---------|
| 00 | `00_index.md` | 本索引 | 导航入口 |
| **🧭 交互件** | **`outputs/fcl_pipeline.html`**（FCL Pipeline Explorer，单文件可双击打开） | **7 视图交互浏览器**：BPS 字段血缘 · 管道(Layer 0→5) · 数据流动(可切 Newrez/Carrington/Capecodfive 源) · 血缘图谱(逐字段跨库血缘，可切详细/经典) · 状态码 · 业务科普 · 🧠知识图谱。数据由 `fcl_lineage_source.json`/`fcl_table_meta.json`/`fcl_knowledge_graph.json` 内嵌驱动（运行时自包含、无需联网/JSON） | 交互式讲解与对账；新成员快速建立全局认知；点表/字段看结构·血缘·验证 SQL |
| **20** | **`20_end_to_end_walkthrough.md`** | **🌟【推荐第一篇】数据流总览 + 讲解稿**：把 foreclosure 数据从来源 Servicer 文件 → BPS 系统的五层全过程串成一条线，并**从业务角度解释「数据为什么这样处理」**（§A.6，如一个 FCL 为何多条 Hold）；两层（业务视角全景+讲解脚本+Q&A／按层深入 walkthrough+代码定位地图+样本 loan 走查） | 向同事讲解全流程+业务理由；新成员快速建立全局认知；其它文档总入口 |
| ~~21~~ | ⛔ **已归档**（无超链接） · `docs/archive/zh/21_fcl_field_lineage.DEPRECATED.md` | **2026-06-11 归档**：迁至 `docs/archive/zh/`；AI 编码工具请勿读；ER 部分迁入 doc 33，字段血缘迁入 doc 25-30，业务理由见 doc 20 §A.6。 | 不再使用；仅历史保留 |
| **25** | **`25_fcl_lineage_overview.md`** | **🔬【字段血缘总入口/hub】** 止赎核心字段 Servicer 原始列 → BPS sync 表的字段级血缘总览：4 条规范跳链骨架 + 全字段主索引 + 已知缺口 + 端到端样例（loan 7727004408，MCP 实测）+ 指向 26–30 的链接。规则 Code-First 取自 PrefectFlow（含 file:line），列名逐列对 prod 核验。由 `outputs/fcl_lineage_source.json` 驱动（手工维护；旧生成器 `gen_fcl_lineage.py` 已删，附录词典/HTML 内嵌经 `scripts/build_rule_glossary.txt`+`inject_glin.txt` 刷新） | 字段级血缘讲解/对账总入口；取代 doc 21 |
| **26** | **`26_lineage_sync_loan_foreclosure.md`** | `bpms.sync_loan_foreclosure` 逐字段血缘：里程碑(`timeline_*`)+汇总/状态(`summary_*`)，一字段一行、每跳列名+规则+代码，终于展示视图(Actual/Var) | 主表字段对账 |
| **27** | **`27_lineage_sync_fcl_stage_info.md`** | `bpms.sync_fcl_stage_info` 逐字段血缘：阶段开始日/天数/to_*_days/in_lm/on_hold + group(delq_status: mba+days360)/judicial(州级回退)/state | 聚合页字段对账 |
| **28** | **`28_lineage_sync_loan_foreclosure_hold.md`** | `bpms.sync_loan_foreclosure_hold` 逐字段血缘：fchold1..4 宽列 → 长表 unpivot | Hold 面板对账 |
| **29** | **`29_lineage_sync_loan_foreclosure_loss_mitigation.md`** | `bpms.sync_loan_foreclosure_loss_mitigation` 逐字段血缘：LM 周期 + datadic 编码→文本解码 | LM 面板对账 |
| **30** | **`30_lineage_sync_loan_foreclosure_bankruptcy.md`** | `bpms.sync_loan_foreclosure_bankruptcy` 逐字段血缘：BK 记录 + 状态解码 | BK 面板对账 |
| **31** | **`31_fcl_stage_window_rules.md`** | **🧮 FCL 阶段窗口规则速查**：8 个 stage × 5 类列（`start_date / end_date / stage_days / in_lm_days / on_hold_days`）一表读懂——start 透传源、end 派生规则、stage_days 公式、in_lm/on_hold SQL 语义（Code-First from pool:2215-2330）、4 真实 loan 工作例、反直觉点澄清（`servicecompletedate` → SERVICE start 不是 end） | 排查 stage 天数 / in_lm / on_hold；新人理解 stage 窗口模型；横向汇总 doc 27 散落规则 |
| **32** | **`32_fcl_pipeline_field_mapping.md`** + **`docs/32_fcl_pipeline_field_mapping.xlsx`** | **🟦 全 pipeline 逐字段 mapping 工作簿**：每字段 × 每层转换规则 + 25 笔生产实测「逐层真值举例」+ 多 as-of（改期/首见）演示 + BPS 截图三方对账 + 🧮公式演示列（活 Excel 公式）；交互式（导航索引/超链接/自动筛选/转换类型色卡）。覆盖主链 `sync_loan_foreclosure` 及 Phase 2-5 四条业务链（stage/hold/lm/bk）逐表 sheet。JSON 驱动、skill `excel-pipeline-lineage` 生成（`docs/32_…xlsx` 为本地重生成件，git 忽略；真源在 JSON+生成器） | 逐字段对账、看整条管道每层怎么变、生产举例 |
| **33** | **`33_fcl_table_erd.md`** | **🧬 FCL 表实体关系图（ERD）**：~22 张 FCL 相关表（L1 源 5 + Newrez 还款 1 + L4 Redshift 8 + portmonth 1 + L5 BPS sync 6 + 视图 1）的 PK / 粒度键 / 1:N / N:N（区间相交）关系——1 张总图 + 5 张分支图（FCL 主线/portmonth 锚点/Hold/LM/BK）+ PK 速查表 + 常见 JOIN 速查（6 类）+ 粒度业务原因 + Code-First 引用。**校正**：视图实际只接 sync_loan_foreclosure + sync_portmonth 两张（不是 5 张），MCP 实证 | 排查表关系（"为什么一笔 loan 多 Hold"）、新人理解表布局、对账时 join 模板速查 |
| 01 | `01_source_data.md` | 各服务商原始数据表结构、止赎相关字段清单 | 数据溯源、字段定义查询 |
| 02 | `02_etl_pipeline.md` | 完整 ETL 管道：5层数据流、表谱系、Redshift vs MySQL 分层 | 管道理解、调试、重写规划 |
| 03 | `03_fcl_status_logic.md` | 止赎状态生成的完整逻辑（SQL/Python/映射表/覆盖规则） | 状态计算原理、重写参考 |
| 04 | `04_status_inventory.md` | 系统内所有止赎相关状态码的枚举、含义、来源、业务用途 | 状态查询、对账、验证 |
| 05 | `05_loan_attribute_mapping.md` | 贷款属性 ↔ 止赎状态的映射关系 | 影响因素分析、规则验证 |
| 06 | `06_diagrams.md` | 全部可视化图表（数据流、状态机、谱系、规则层次、依赖关系） | 技术评审、架构理解、文档演示 |
| 07 | `07_fcl_lineage_and_rules.md` | 按服务商的完整 FCL 数据血缘与判断规则（SLS/Newrez/Carrington/Selene/MRC/Arvest/CapeCodFive/FCI/Rocket/SPS） | 各服务商 FCL 实现现状分析、差距识别、改进规划 |
| 08 | `08_servicer_fcl_field_mapping.md` | 各服务商原始字段 → FCL 状态映射规则（业务视角，去掉 ETL 中间层）+ 缺口分析 + 字段补全优先级 | 业务规则重梳理、向 Servicer 请求补全字段、合规审核 |
| 08-1 | `08-1Data validation Manual.md` | **数据验证手册**：逐字段列出 Newrez 源列 → 中间层的映射并附 DB 实测/截图佐证（如 `delinquency_status_mba → delq_status`、`activelmflag → lm_flag`） | 字段映射的人工验证留痕；对账时核对单字段映射是否落地 |
| 09 | `09_servicer_data_interface_standard.md` | 新系统 Servicer 数据接口标准：7 组标准字段目录（P0/P1/P2）+ 各 Servicer 合规矩阵 + 行动项汇总 + 交付格式规范 | 系统重构前置规范、向 Servicer 正式发出字段补全请求、新 ETL 接口设计 |
| 10 | `10_glossary.md` | 综合术语清单：7 大分类 50+ 条目，覆盖核心业务状态 / 逾期状态编码 / FCL 流程 / LM 类型 / 破产相关 / ETL 架构 / 系统缩写 | 新成员入门、阅读任何文档时查询不熟悉的术语 |
| 11 | `11_servicer_impl_guide.md` | **过渡期实施指南**：8 个 Servicer 现有数据 → 新系统标准字段的映射逻辑（CASE WHEN 伪代码 + 可实现程度矩阵 + 实施路线图）；含 Newrez portnewrezfc 多次 Hold 处理方案 | 新系统 ETL 开发者编码参考；在 Servicer 提供新格式数据前的过渡期实施方案 |
| 12 | `12_sync_asset_management.md` | **代码调研文档**：`sync_asset_management.py` 全面分析——两阶段 ETL 编排（10 步 Redshift 中间层构建 + 13 类 BPS 同步），所有读/写 DB 表、函数说明、环境/租户参数、状态追踪机制，以及 `get_sync_df()` 中发现的 1 个死代码问题 | ETL 开发者参考；调试每日 BPS 同步；新系统重写该 Flow 时的设计参考 |
| 13 | `13_newrez_fcl_bps_display_mapping.md` | **BPS 界面字段逆向映射**（Newrez 专项，v2）：以 BPS Foreclosure 界面 5 个面板为终点，逆向追溯每个展示字段的 Newrez 原始数据来源（newrez.portnewrezfc/bk/lm）与计算规则；涵盖 timeline/target/actual/var/variance/bid_approval/summary 共 104 个视图字段，以及 Hold 全历史、LM Cycle、Bankruptcy 三个独立面板，以及聚合视图 Days in Stage/LM/Hold 的来源（sync_fcl_stage_info） | BPS 数据排查；Newrez 字段映射参考；新 Servicer 接入时的字段对应模板 |
| 14 | `14_bps_driven_servicer_fcl_interface.md` | **BPS 驱动的 Servicer FCL 数据接口规范**：以 doc 13 的 BPS 五大面板和聚合视图为终点，定义约 67 个 Servicer 字段、P0/P1/P2 优先级、交付格式、字段补全请求顺序；v3 已增加审核状态和字段准入检查规则 | doc 14 审核；作为后续逐 Servicer 缺口分析的目标标准；向 Servicer 发出字段补全请求的依据 |
| 15 | `15_newrez_servicer_fcl_gap_analysis.md` | **Newrez Servicer FCL 字段缺口分析**：第一个逐 Servicer 文档样例；将 Newrez 原始表、PrefectFlow 血缘、BPS 展示字段、doc 14 目标字段和缺口行动项连成完整链路 | Newrez 字段补全讨论；验证 doc 14 是否可落地；后续 Servicer 文档模板样例 |
| 16 | `16_bps_panel_quickref.md` | **BPS Foreclosure 面板速查**：6 个面板（Foreclosure Summary / Timeline / Hold / LM / BK / 聚合概览）的 UI 截图 + 紧凑字段映射表（UI 标签 → Newrez 源字段 → Mapping Rule）+ 快速排查路径；doc 13 的速查入口 | BPS 界面数据排查；新成员快速上手；运营/数据联调时对照 BPS 截图定位源字段 |
| 17 | `17_foreclosure_business_primer.md` | **美国贷款 Foreclosure 业务入门**：从 doc 7 第 2 章独立提取的分享版，介绍 FCL 判断依据、常见字段、贷款生命周期、FCL 内部阶段、司法/非司法差异、Foreclosure 与 Bankruptcy 关系 | 给业务/运营/新同事分享；无需阅读完整 ETL 血缘即可理解 Foreclosure 基础概念 |
| 18 | `18_loss_mitigation_business_primer.md` | **Loss Mitigation（LM）业务入门与方案说明**：解释 LM 的业务含义、六类常见方案、BPS/Newrez Deal/Program/Status/Final Disposition 字段，以及 LM 与 FCL 的关系 | 快速理解 LM 各方案；BPS LM Cycle 面板排查；向 Servicer 讨论 LM 字段前置学习 |
| 19 | `19_fcl_sample_loan_raw_dump.md` + `docs/19_fcl_sample_loan_raw_dump.xlsx` | **5 个样例贷款 · FCL 全链路全表全字段原始转储**：一节一张表，逐字段列出 Newrez 源 → Redshift 中间层 → BPS 的「业务 ↔ 数据」对应（每张表附全链路血缘块 + file:line）；全 prod 实测。doc 16 的原始数据底座 | 端到端样例对账；看一笔贷款在每张表的真实取值；新成员理解全链路 |
| **22** | **`22_bps_fcl_timeline_sourcing.md`** | **BPS agg-summary 止赎页取数规则**：`/#/portfolio/agg-summary` 的 **Time Line** 与 **Stage** tab（及 Overview）均取自 `bpms.sync_fcl_stage_info`（← `port.fcl_stage_info`，`GEN_FCL_STAGE`）；含 UI 列 ⇄ 表列完整映射、三视图关系、「当前态 vs 历史态」解答（表保留 `fctrdt` 多快照，页面取 `MAX(fctrdt)`）、代表性 SQL、样本走查(7727000088 实测吻合) | 回答「Time Line 页取自哪张表/SQL 怎么写」；BPS 聚合页排查；理解为何一笔贷款=一行日期列 |
| **23** | **`23_bk_discharge_to_payoff_analysis.md`** | **BK discharge → payoff（P）历时分析（DB 实测）**：回答「破产 discharge 到最终 payoff 多久」——prod 实测仅 11 笔可测、中位 186 月（≈15.5 年），且**非流程耗时**（discharge 多在 2008–2014、payoff 在 2023–2026，二者不相关），实证 Ch.7/11 discharge≠还清、lien 存续；含口径、逐笔明细、局限与验证 SQL | 回答 BK→P 时长问题；纠正「discharge 很快导向 payoff」直觉；BK 相关对账/口径参考 |
| **24** | **`24_bk_to_current_vs_foreclosure.md`** | **BK→Current 与 BK→Foreclosure 核心差异**：BK 节点两条出边的分水岭 = 房贷违约是否被 cure（≠ 是否 discharge）；Ch.13 补缴 reinstate→C，dismissal/MFR/Ch.7（lien 存续）→FCL；含对比表、触发条件、§ 1322/1328/362/727/524 依据与权威来源、系统透传说明 | 厘清「破产成功=回 Current」误解；BK 两条转换边的业务/法律解释；培训与对账参考 |
| 98 | `98_database_verification_strategy.md` | **数据库验证与 MCP 使用规范**：规定后续研究默认用 MCP 只读验证 MySQL/Redshift，记录查询目的、SQL、快照日期、结果摘要，并保护连接信息 | 字段映射查库验证；逐 Servicer 文档 SQL 附录；Reviewer 复现 |
| 99 | `99_servicer_fcl_gap_summary_and_action_plan.md` | **Servicer FCL 缺口汇总与行动计划**：汇总 doc 14 审核结论、后续逐 Servicer 文档顺序、行动项分类、验收标准 | 项目管理；向管理层 / Reviewer 汇报；后续工作路线图 |
| 模板 | `_servicer_fcl_gap_analysis_template.md` | 单个 Servicer FCL 缺口分析模板：固定文档头、血缘链条、doc 14 字段对照、缺口分级、证据与 Open Questions 结构 | 生成 Carrington/SLS/Selene/MRC/Arvest/CapeCodFive/FCI 等后续文档 |

### 测试报告（验收/回归留档，不占主目录编号）

| 文件 | 内容 |
|------|------|
| `32_formula_demo_test_report.md` | doc 32 「🧮 公式演示列 + 逐层举例列」的全面测试验证（公式引用、结果=实测值、显示码、高亮、幂等；不含 Phase 2） |
| `34_phase2_and_kg_test_report.md` | doc 32 Phase 2（stage/hold/lm/bk 四链逐表 sheet）+ `fcl_pipeline.html` 知识图谱视图的综合测试与证据 |

> 注：上述两份均为**测试报告**；正式 doc 32 指 `32_fcl_pipeline_field_mapping.md`（`32_formula_demo_test_report.md` 与其同号但属测试报告，非正式 doc 32）。

---

## 推荐阅读顺序

```
全貌入门（推荐）：20 → 02 → 17/18（也可直接打开交互件 outputs/fcl_pipeline.html）
字段级血缘讲解：25 → 26-30 → 13 → 19（总入口→逐表→BPS界面→样例对账）
初次了解系统：  00 → 02 → 03 → 04
业务背景入门：  17 → 10 → 07
LM 业务入门：   18 → 10 → 13 → 15
数据溯源分析：  01 → 07 → 02 → 05
系统重写准备：  03 → 07 → 05 → 06 → 02 → 09
验证/对账场景：  04 → 03 → 05
服务商差距分析：08 → 07 → 03 → 09
业务规则重构：  08 → 03 → 07 → 09
新系统接口设计：09 → 08 → 07
新系统 ETL 实施：09 → 11 → 08
BPS 驱动字段标准：13 → 14 → 15 → 99
数据库验证规范：98 → 13 附录B → 15 Section 7
逐 Servicer 缺口分析：14 → 98 → 模板 → 15 → 16/17/18...
仅看图：        06
```

---

## 关键术语速查

| 术语 / 缩写 | 含义 |
|------------|------|
| FCL | Foreclosure，止赎 |
| REO | Real Estate Owned，抵押房产已被银行取回 |
| BK | Bankruptcy，破产 |
| LM | Loss Mitigation，损失缓解（如宽限、修改还款） |
| delinq | Delinquency，逾期状态码（C/D30/D60/D90/D120P/FCL/REO/P） |
| svcdelinq | 服务商原始逾期描述（未标准化） |
| days360 | 按 360 天/年计算两个日期之间的天数差 |
| fctrdt | 报告截止日（月末次日，即下月第一天） |
| portmonthbase | Redshift 中的月度主分析表 |
| basic_data_loan_fix | 人工覆盖修正表（最高优先级） |
| BPS | Business Planning System，业务规划系统（下游报告系统） |

> 完整术语定义（50+ 条目，含 FCL 流程 / LM 类型 / ETL 架构 / MBA 编码对照）见 [doc 10 综合术语清单](10_glossary.md)

---

## 系统边界说明

**包含：**
- PrefectFlow 代码库中所有与止赎状态生成相关的 Python、SQL 逻辑
- 涉及的 MySQL（staging）和 Redshift（分析层）表结构
- BPS 同步层（下游输出）

**不包含：**
- BPS 系统内部逻辑（属于下游系统）
- Polypath/IRR 计算（独立模块）
- 原始服务商文件的业务规则（属于上游系统）

---

## 对应英文版

英文同步版本：`docs/en/00_index.md`（章节编号、图表、术语完全对应）
