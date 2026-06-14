# doc 34 — Phase 2（stage/hold/lm/bk 四链）+ 知识图谱 综合测试报告

## 文档目的（Document Purpose）
- **为什么存在**：本会话交付了两项大改动——(1) doc 32 Excel 新增 Phase 2 四条 FCL 业务链（阶段/暂停/损失缓释/破产）的逐表 sheet；(2) `outputs/fcl_pipeline.html` 升级为「FCL 知识图谱」（第 6 视图）。本文记录对这两项的**全面测试**与证据，供验收与回归。
- **解决的问题 / 填补的空白**：此前 doc 32 仅覆盖主链（sync_loan_foreclosure）；其余 FCL 业务族表（stage/hold/lm/bk）无逐表详情。HTML 此前只有数据血缘视图，缺业务/分析维度。本文证明两项改动已落地、数据真实、公式可算、图谱连通。
- **范围**：仅本会话两项交付的测试。**不**覆盖主链既有 sheet 的历史测试（见 doc 32 测试报告 TC1–TC17）。
- **系统定位**：doc 32（逐字段 mapping + 举例 Excel）与 `fcl_pipeline.html`（交互浏览器）的验收记录；上游真源为 `fcl_table_meta` / `fcl_lineage_source` / `fcl_field_meanings` / `fcl_logic_coverage` + 业务概念抽取。

## 目标读者（Target Audience）
主要：验收者 / validators、数据工程师、未来 AI 会话；次要：业务分析师、onboarding 工程师、reviewers。

## 修订历史（Revision History）
| 日期 | 作者 | 版本 | 变更 | 相关 |
|------|------|------|------|------|
| 2026-06-13 | AI Agent (Claude Opus 4.8) | v1 | 初稿：Phase 2 四链 + 知识图谱综合测试 | doc 32；fcl_pipeline.html |

## 依赖（Dependencies）
- 数据真源（只读 DB 实测）：`outputs/fcl_layer_examples_phase2.json`（8 表举例）、`fcl_knowledge_graph.json`（图谱）、`fcl_kg_{business,analysis,panels}.json`（概念抽取）。
- 生成器：`outputs/build_fcl_pipeline_mapping_xlsx.txt`（Excel）、`outputs/build_fcl_knowledge_graph.txt`（图谱）、`scripts/inject_kg.txt`（注入）。
- 测试工具：openpyxl（内容哈希/读回）、真 Excel 引擎 pywin32 COM（`CalculateFull` + `SpecialCells(xlErrors)`）、Node v22（`node --check` + DOM-stub 运行时）。

## 已知限制（Known Limitations）
- **多行历史表（hold/lm/bk）举例列**取该笔「代表性最新行」（hold=最新段、lm=最新周期、bk=最新申请）；完整历史在 BPS 面板/长表，本 sheet 不展开多行。已在 sheet 注与本文注明。
- **stage 表 19/25 样本贷款有行**（活跃 FCL 过滤）；其余样本贷款 stage 列为 ∅NULL（属实，非缺陷）。bk 仅 6/25 有记录。
- 知识图谱的浏览器**视觉**呈现未在本环境用真浏览器截图确认；已用 Node 运行时（DOM stub）实跑 `renderKG` 验证产出 SVG 无异常（见 §2）。建议验收者开 HTML 目视确认。

---

## 一、Phase 2：stage / hold / lm / bk 四链逐表 sheet

### TC-P2.1 取数（DB 只读 + schema-verify）
子 agent 经 `redshift_prod`（port.\*）/ `mysql_prod`（bpms.\*）拉 **8 张表 × 25 样本贷款**的代表性行，写入 `fcl_layer_examples_phase2.json`。`information_schema` 核验：**8 表 FM 列全部存在、0 缺失**；key 列均为 `loanid`。覆盖：stage 19 贷款 / hold 25 / lm 22 / bk 6。**rs 与 sync 代表行逐字节一致**（sync 为忠实副本，仅少 port-only 管理列 dataasof/servicer/improgram）。编码：真 NULL→`∅NULL`、空串→`∅空串`、日期→YYYY-MM-DD。

### TC-P2.2 8 张 sheet 生成
生成器 `B_TABLES` 新增 8 项 → doc 32 由 17 增至 **25 sheet**：⑬ `mid·fcl_stage_info`(48 字段) / ⑲ `bps·sync_fcl_stage_info`(57) / ⑮ `mid·fcl_hold`(17) / ㉑ `bps·sync_fcl_hold`(15) / ⑯ `mid·fcl_lm`(16) / ㉒ `bps·sync_fcl_lm`(22) / ⑰ `mid·fcl_bankruptcy`(15) / ㉓ `bps·sync_fcl_bankruptcy`(22)。每表均含用户要求的四项：**字段 + 业务含义 + 计算逻辑/mapping rule（取自 lineage hops）+ 来源/类型 + 逐层举例列（25 列）+ 🧮 每 servicer 公式列（Newrez/Carrington 各一）**。

### TC-P2.3 每 servicer 活公式（passthrough → 真上游）
`IMM_UP` 扩展四链 BPS←Redshift 上游；fill 循环纳入 8 新 meta。实测 BPS 侧字段 🧮 公式为**活引用上游 Redshift sheet 该笔格**，例：
- ⑲ `group` = `='⑬ mid·fcl_stage_info'!G17`（upsert 直传 [asset:925]）
- ⑲ `state`/`judicial`/`referral_stage_days` 同理引用 ⑬。
- ㉓ `bankruptcy_status` = `='⑰ mid·fcl_bankruptcy'!…`、`legal_status` 引用 ⑰ [asset:829]。
Redshift 侧的解码/计算字段（其源 servicer raw 未渲染）走「计算逻辑」列文字说明（与主链 ⑪ 同口径）。

### TC-P2.4 真 Excel 引擎复算
pywin32 COM 打开副本 → `CalculateFull()` → 逐 sheet `SpecialCells(xlCellTypeFormulas, xlErrors)`：**全 25 sheet、677 活公式、0 公式错误**（含全部 Phase 2 新 passthrough 引用——0 个 #REF/#NAME/#VALUE）。

### TC-P2.5 幂等
连跑生成器两遍，全 25 sheet 内容级 MD5 一致（`d9505a5f…`）。

---

## 二、知识图谱（fcl_pipeline.html 第 6 视图「🧠 知识图谱」）

### TC-KG.1 图谱数据汇编
`build_fcl_knowledge_graph.txt` 由真源汇编 `fcl_knowledge_graph.json`：**386 节点 / 963 边 / 0 悬挂边**。三维齐备——管道（层 6 / 表 24 / 字段 154 / servicer 3 / LT 规则 30 / 机制 5）、Foreclosure 分析（状态 18 / 阶段 8 / 里程碑 9）、业务（概念 61 / 术语 23 / BPS 面板 10）+ 文档 35。业务/分析维度由 3 个抽取 agent 从 doc 17/18/10、03/04/05/31、16/13/14 提取（存 `fcl_kg_{business,analysis,panels}.json`）。

### TC-KG.2 连通性（三维真正连成一张网）
图遍历：**1 个连通分量、386/386 节点、0 孤立点**。跨维边 **498** 条（documented_in 345、business↔pipeline 138、modeled_by 6、corresponds 18、displayed_in 9…）。新增层序 spine（L0→L5）、doc:00 索引 hub、分析↔业务桥（milestone:referral↔concept:referral、status:fcl↔concept:foreclosure 等，语义准确）把原先的「分析孤岛 + 孤立文档」并入主图。

### TC-KG.3 HTML 集成 + JS 语法
新增 `v-kg` 按钮、`setView('kg')`、`renderKG` 自包含模块（维度泳道聚类布局 + 类型 chip 过滤 + 搜索 + 滚轮缩放/拖拽平移 + 点节点 ego 高亮 + 详情抽屉邻居可点）+ i18n（中英）。`scripts/inject_kg.txt` 注入 251KB（`</`→`<\/` 防止过早闭合 script）。`node --check` 整段脚本：**0 语法错误**；标记 `/*KG_START*//*KG_END*/` 各 1，内嵌 JSON 解析通过、0 悬挂。

### TC-KG.4 运行时实跑（Node + DOM stub）
以最小 DOM stub 在 Node 实跑：`renderKG()` 产出 `<svg>`、**232 个可见节点**（154 字段默认隐藏）、14 个过滤 chip；`kgSelect('concept:foreclosure')` 抽屉出邻居；`kgToggle('field')`/`kgSearch`/`kgReset`/中英切换 均无异常。

---

## 三、Phase 3：③④ L1 源 + ㉔ 解码字典（2026-06-14 追加）

### TC-P3.1 ③④ bk/lm L1 源 sheet
新增 **③ src·portnewrezbk**(60 字段)、**④ src·portnewrezlm**(56 字段)，按 ② 同款 is_src 排版（字段+业务含义+来源/类型+25 逐层举例列；L1 raw 无上游故无公式列）。举例数据子 agent 只读实测写 `fcl_layer_examples_phase3.json`：`information_schema` 核 ③④ 列 0 缺失；20/25 样本贷款有行（5 Carr 无 Newrez bk/lm 行→∅NULL）；多行表取代表性最新行（bk=最新 bkfileddate、lm=最新 dealstartdate）。实测 ③ `bkstatus`/`bkchapter` 等真值已入表（如 7727000065 Ch7、7727003984 Ch13）。

### TC-P3.2 ㉔ 解码字典 sheet + Schema-Verify 纠错（Code-First）
新增 **㉔ dic·portnewrezdatadic** 自定义解码字典 sheet（非 per-loan，长表 field_name/code/description）：**12 类 140 行** code→文本（BKStatus/BKStage/BorrowerIntention/Judicial/LMDeal/LMDecision/LegalStatus/LiquidationType/MBADelinquency/ForbearanceStatus/RepaymentStatus/TrialStatus）；大类 LMStatus(149)/LMProgram(388)/DenialReason(130)/ModType(387) 注明不全列。
**重大纠错**：代码 [pool:367](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L367)（BK）/ [pool:835-840](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L835-840)（LM）`LEFT JOIN newrez.portnewrezdatadic WHERE field_name=...` 解码。子 agent 初查 mysql_prod 报"该表不存在、只有宽表 newrezdatadic（无 LM/BK）"；经 Code-First 复核 + 直接查 `redshift_prod`，该长表【**仅在 Redshift**】且含全部 LM/BK 类——遂据 Redshift 实测拉正确字典并订正 ㉔ 表元 business_meaning（原误写"8 列"）。

### TC-P3.3 排序 + 复算
逐表 sheet 改为【圈号升序】（用户反馈"按编号好找"）：② ②c ③ ④ ⑨ ⑩ ⑪ ⑬ ⑮ ⑯ ⑰ ⑱ ⑲ ⑳ ㉑ ㉒ ㉓ ㉔。25→**28 sheet**。真 Excel COM `CalculateFull`：**28 sheet 0 公式错误**（③④ is_src 无公式、㉔ 纯文本、主链+Phase2 公式不变）；内容级幂等。仍无逐表 sheet：⑤⑥⑦⑧⑫⑭。

## 四、Phase 4：⑤⑥ L1 源 + ⑫ basic_data_fcl_related（2026-06-14 追加）

### TC-P4.1 ⑤⑥⑫ sheet 生成
新增 **⑤ src·portnewrezgeneral**(125 字段)、**⑥ src·portnewrezprop**(32 字段)（is_src：字段+业务含义+来源/类型+25 举例列）+ **⑫ mid·fcl_related**(14 字段，非 src：另有 计算逻辑列 + 每 servicer 🧮 公式列)。doc 32 由 28 增至 **31 sheet**。逐表 tab 仍【圈号升序】：② ②c ③ ④ ⑤ ⑥ ⑨ ⑩ ⑪ ⑫ ⑬ ⑮ ⑯ ⑰ ⑱ ⑲ ⑳ ㉑ ㉒ ㉓ ㉔（实测 T2 升序 True，21 张逐表页）。

### TC-P4.2 取数 + schema-verify
子 agent 只读实测写 `fcl_layer_examples_phase4.json`：⑤ general(mysql_prod，125 列、20/25 loan)、⑥ prop(mysql_prod，32 列、20/25)、⑫ fcl_related(redshift_prod，14 列、25/25)。`information_schema` 核三表列 **0 缺失**。5 笔 Carrington 不在 ⑤⑥（Newrez 表）→省略；⑫ 跨 servicer 故 25 笔齐。实测 ⑥ `propertystate` = CA/AZ/FL…；⑫ `delq_status` 实测取值 C/D30/D120P/FCL/P/REO。

### TC-P4.3 ⑫ 计算逻辑 + 每 servicer 活公式
为 ⑫ 14 字段新增 `field_rule`（Code-First 自 `CREATE_FCL_RELATE_ATTR` [pool:1697-1770](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L1697-1770)），计算逻辑列逐字段说明来源。⑫ Newrez 派生字段 🧮=**活引用上游**：`propertystate`=`='⑥ src·portnewrezprop'!…`、`isloanlitigated/deactreason/reasonfordefault/inauctionflag`→⑤、`bk_flag`→`='③ src·portnewrezbk'!…`(activebkflag)、`servicer`=常量、`delq_status`=CASE(注，逾期分类，即 ⑬ group 的 r 源)。Carrington 分支源列(litigation_type/property_state/bk_flag…)未纳入 ②c → 诚实注。实测 T4：⑫ 跨表公式 8 处、**0 悬挂**（均指向已存在的 ③⑤⑥ sheet）。

### TC-P4.4 复算 + 幂等
真 Excel COM `CalculateFull`：全 **31 sheet 0 公式错误**（含 ⑫ 新 passthrough 引用 ⑤⑥③）；🧮 计数 677→**703**；内容级幂等（hash 两跑一致）。仍无逐表 sheet：⑦⑧（逾期支线 L2/L3）、⑭（portfunding 维度）。

## 结论
**Phase 2 / 知识图谱 / Phase 3 / Phase 4 四项均通过（PASS）。** doc 32 现 25 sheet、677 活公式、真 Excel 0 错误、幂等；四链每表均具备 字段/计算逻辑/逐层举例/每 servicer 公式。知识图谱 386 节点 963 边、1 连通分量、跨维 498 边，HTML 第 6 视图 JS 0 语法错误、运行时实跑通过。全程 DB 与代码只读，未提交。

> 英文镜像（docs/en/34）：本测试报告当前为 zh；如需 en 版可后续补（业务散文性质，按 doc 同步规则）。
