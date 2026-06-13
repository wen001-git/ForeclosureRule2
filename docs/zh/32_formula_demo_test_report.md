# doc 32 ·「🧮 公式演示」列 + 逐层举例列 —— 测试验证报告

## 文档信息

### 1. 文档目的
- **Why**：doc 32 在 5 张非 src 逐表 sheet（⑨⑩⑪⑱⑳）新增了 (a) 25 笔样本贷款「逐层真值举例列」与 (b)「🧮 公式演示」列（活 Excel 公式 + 高亮相关字段）。本报告对这两项改动做**一次全面测试验证**并留档。
- **What problem**：确认新功能正确（公式引用对、结果应等于实测值、显示码已处理、高亮正确、布局/冻结/分组无误）、不回归（② src 与既有页不变）、且**幂等可重跑**。
- **Scope**：覆盖 doc 32 工作簿 `docs/32_fcl_pipeline_field_mapping.xlsx` 及其真源 `outputs/fcl_layer_examples.json`、`outputs/fcl_formula_demos.json`、生成器 `outputs/build_fcl_pipeline_mapping_xlsx.txt`。**不含** Phase 2（stage/hold/lm/bk 四链）。
- **System fit**：doc 32 是 FCL pipeline 的可对账 Excel 视图；本次新增「用真公式演示转换逻辑」。

### 2. 目标读者
数据工程师 · 业务分析 · 对账/校验人员 · 未来 AI 会话 · reviewer

### 3. 修订历史
| 日期 | 作者 | 版本 | 变更 | 相关 |
|------|------|------|------|------|
| 2026-06-12 | AI Agent (Claude Opus 4.8) | v1 | 初版：🧮 公式演示列 + 举例列 全面测试验证（TC1–TC9） | doc 32 v4；`fcl_formula_demos.json` |
| 2026-06-12 | AI Agent (Claude Opus 4.8) | v2 | 追加 首见 min(dataasof) 方案3 活公式（⑪⑱ 表底 + D 页，MINIFS）测试 TC10–TC11；TC8 幂等改为全 16 sheet | `fcl_minihist_demos.json` |
| 2026-06-13 | AI Agent (Claude Opus 4.8) | v3 | **真·Excel 引擎(pywin32/COM)复算验证**：发现并修复 2 缺陷（MINIFS 在本机 Excel 不支持→#NAME?；规则文本"= fcbidamount"被当公式）；MINIFS→MIN+IF助列；②src 补 25 笔源头数据。全 16 sheet CalculateFull **0 错误** | TC12–TC14 |
| 2026-06-13 | AI Agent (Claude Opus 4.8) | v4 | **全字段 🧮 公式覆盖**：用 lineage hops + 同名直传，把 5 非 src 表**每个字段**的 🧮 列填为「引用上游层活公式」(直传/改名 `='上游'!cell`)；336 字段 → **247 活公式 + 89 诚实注**（注=NULL投影/SLA常量/variance/bid_approval/decode/系统列/Hold多行/视图实时算，非单格可表达）。真 Excel 0 错误 | TC15 |
| 2026-06-13 | AI Agent (Claude Opus 4.8) | v5 | 🧮 列改为**每 servicer 一列**（🧮·Newrez 7727003984 + 🧮·Carrington 7727000806），各列内部统一该笔→列自洽、并排展示 servicer 差异；Carr 计算列加 null-guard、修复 actual_* 引用全历史 set_date(含 2 行提示)致 DATEVALUE #VALUE。336×2=672 格→476 公式+196 注，真 Excel 0 错误 | TC16 |

### 引擎级验证（v3 更新）
> ✅ **已用真·Excel 引擎复算**：在本机安装 `pywin32`，用 **COM 驱动本机真实 Excel**（`C:\Program Files\Microsoft Office\Root\Office16\EXCEL.EXE`）对工作簿副本 `Application.CalculateFull()` 重算，再用 `SpecialCells(xlCellTypeFormulas, xlErrors)` 扫描——**全 16 sheet 0 个公式错误**，D!B60 首见 = `2026-05-22`。
> 此外仍有三重保证作补充：① 公式语法 well-formed；② 公式内每个单元格引用**程序化反查指向正确 (字段, demo loan) 且真值正确**；③ 每条 demo 的 **expect 由人工按真值算出**（独立 Python 复算 10/10 = 期望 = 实测）。
> ⚠️ 注：本验证用 Excel **Office16(2019/365 引擎)**；若在更老的 **Excel 2016** 打开，MINIFS 等新函数不支持——本次已**主动避开**（改用 MIN+IF），故旧版亦可。`summary_days_in_fcl` 含 `TODAY()` 会逐日增长（实时重算语义）。

---

## 测试环境
- 文件：`docs/32_fcl_pipeline_field_mapping.xlsx`（16 sheet，重生成无 traceback）。
- 工具：openpyxl（回读校验）；生成器经 `python - < outputs/build_fcl_pipeline_mapping_xlsx.txt`（stdin）运行。
- 数据来源：`fcl_layer_examples.json`（prod 只读拉取，Step 1 已过 information_schema schema-verify NOT-IN 0 行）；本次**未再查库**（DB 只读天然满足）。
- 验证日期：2026-06-12（`summary_days_in_fcl` 演示含 `TODAY()`，下述结果以此日为基准）。

## 测试结果总览
| # | 测试项 | 结果 |
|---|--------|------|
| TC1 | 布局：5 非 src 表 = 30 列、冻结 F15、col5 表头=🧮 公式演示 | ✅ PASS |
| TC2 | 回归：② src 仍 3 列、无公式/举例列 | ✅ PASS |
| TC3 | 9 条公式 demo：语法 well-formed（`=` 开头） | ✅ PASS 9/9 |
| TC4 | 公式单元格引用**指向正确 (字段, loan) 且真值正确**（含跨表引用） | ✅ PASS 9/9 |
| TC5 | 期望值 expect = 实测值（人工核） | ✅ PASS（见明细） |
| TC6 | 显示码处理：公式内 VALUE/DATEVALUE/空判，不改数据 | ✅ PASS |
| TC7 | 高亮：输入浅蓝(DDEBF7)/输出浅橙(FCE4D6)/公式浅绿(E2EFDA) + 公式格批注 | ✅ PASS 9/9 |
| TC8 | 幂等：连跑两遍，**全 16 sheet 16,296 格** 内容 MD5 一致 | ✅ PASS（`8b30fde0…`） |
| TC9 | 诚实性：不可复现的 COALESCE 演示已剔除、未伪造 | ✅ PASS |
| TC10 | 首见 min(dataasof) **方案3** 小块（⑪⑱ 表底 + D 页）：dataasof 存**真实日期**(可被 MIN 计算)、value 文本 | ✅ PASS |
| TC11 | ⑪⑱ 矩阵 set_date 行 🧮 = 实时 `MIN(助列C)`（助列 C=IF(value=当前值,dataasof,"")），首见 = **2026-05-22** = 实测 | ✅ PASS |
| TC12 | **真·Excel 引擎(pywin32/COM) CalculateFull 复算**：全 16 sheet **0 个公式错误**；D!B60 首见 = `2026-05-22` | ✅ PASS |
| TC13 | 缺陷修复回归：① MINIFS→#NAME?(本机 Excel 不支持) 已改 MIN+IF；② 规则文本"= fcbidamount"被当公式 已用 `_T()` 全角化 | ✅ FIXED |
| TC14 | ② src·portnewrezfc 补 25 笔源头实测值（key=loanid，as-of 2026-06-10）；fcreferraldate 7727003984=2025-03-07 = ⑩.referral_start_date | ✅ PASS |
| TC15 | **全字段 🧮 覆盖**：5 非 src 表 336 字段 → **247 活公式（直传/改名跨表引用 + 9 计算 demo）+ 89 诚实注**；真 Excel 0 错误、幂等 `463a343e` | ✅ PASS |
| TC16 | **每 servicer 一列**（🧮·Newrez + 🧮·Carrington）：336×2=672 格 → 476 公式+196 注；真 Excel 实算 **daysinfc Newrez=461(直传) / Carrington=477(datediff)**；0 公式错误、幂等 `e68c7365` | ✅ PASS |

## TC1–TC2 布局与回归（实测）
- ⑨⑩⑪⑱⑳：`max_column=30`（4 基础列 + 🧮 公式列 + 25 举例列）、`freeze_panes=F15`（钉前 5 列）、举例列 6..30 `outline_level=1` 可折叠。
- ② src·portnewrezfc：`max_column=3`（字段/业务含义/来源类型），无公式/举例列，符合「L1 raw 不演示」。

## TC3–TC7 九条公式 demo 明细（全部 PASS）
> 列含义：输出格=该 demo loan 在输出字段行的实测值（应=公式结果）；引用真值=公式所引上游格的实测内容。

| 表 | 输出字段 | demo loan | 公式（活） | 引用真值（实测） | 期望=实测 |
|---|---|---|---|---|---|
| ⑨ temp | daysinfc | 7727000806(Carr) | `=DATEDIF(DATEVALUE(referral),DATEVALUE(dataasof),"d")+1` | referral=2025-02-19, dataasof=2026-06-10 | **477** ✅ |
| ⑩ fcl | daysinfc | 7727000806(Carr) | 同上（同表引用） | referral=2025-02-19, dataasof=2026-06-10 | **477** ✅ |
| ⑪ forecl | summary_type | 7727003984 | `=IF(IFERROR(VALUE(judicial),-1)=1,"Judicial","Non Judicial")` | summary_judicial_foreclosure=`0` | **Non Judicial** ✅ |
| ⑱ sync | summary_type | 7727004408 | 同上（同表引用） | summary_judicial_foreclosure=`1` | **Judicial** ✅ |
| ⑱ sync | summary_foreclosure_status | 7727000367 | `=IF(VALUE(⑩.activefcflag)=1,"Active…",IF(AND(=0,desc 非空),"Closed Foreclosure:"&⑩.fcremovaldesc,""))` | ⑩.activefcflag=`0`, ⑩.fcremovaldesc=`Loss Mitigation`（跨表 `'⑩…'!G19`） | **Closed Foreclosure:Loss Mitigation** ✅ |
| ⑪ forecl | summary_foreclosure_status | 7727003984 | 同上（跨表→⑩） | ⑩.activefcflag=`1`, ⑩.fcremovaldesc=`∅空串`（跨表 `'⑩…'!F19`） | **Active Foreclosure** ✅ |
| ⑱ sync | summary_days_in_fcl | 7727004408 | `=IFERROR(VALUE(⑪.days),0)+(TODAY()-DATEVALUE(⑪.dataasof))` | ⑪.summary_days_in_fcl=`825`, ⑪.dataasof=2026-06-10（跨表→⑪） | **827**（@2026-06-12；TODAY() 后逐日+1）✅ |
| ⑪ forecl | timeline_referred_to_foreclosure_date | 7727003984 | `='⑩…'!referral_start_date`（改名直传） | ⑩.referral_start_date=2025-03-07 | **2025-03-07** ✅ |
| ⑳ view | actual_first_legal_days | 7727000065 | `=DATEVALUE(timeline_first_legal)-DATEVALUE(nextduedate)` | timeline_first_legal=2025-03-27, nextduedate=2024-03-01 | **391** ✅ |

- **TC4 引用正确性**：程序化反查每个引用单元格 → 其所在行字段名 + 列贷款号 == 期望的 (输入字段, demo loan)，9/9 命中（跨表引用 `'⑩ mid·basic_data_loan_fcl'!G19` 等亦正确解析）。
- **TC6 显示码**：`activefcflag` 文本 `0/1` 经 `VALUE()`；日期文本经 `DATEVALUE()`；`fcremovaldesc` 空判 `NOT(OR(=∅NULL,=∅空串,=""))`。**数据未改**，∅NULL/∅空串 显式标记保留。
- **TC7 高亮**：9/9 公式格=浅绿、输出格=浅橙、各输入格=浅蓝（跨表 demo 的输入高亮正确落在上游 ⑩/⑪ 表的同 demo-loan 列）；9/9 公式格带批注（demo loan + 逻辑 + 期望 + 输入位置）。

## TC8 幂等
连续重生成两遍，对 6 张表（②⑨⑩⑪⑱⑳）全部单元格内容取 MD5：两遍均 `919c6b53c0d06c7119041d7f7fcf5947`（12,408 格），**完全一致** → 幂等可重跑。

## TC9 诚实性 / 已剔除
- **COALESCE(dtdeedrecorded, fcremovaldate) → timeline_foreclosure_completed_date**：实测 loan 7727000065 输出为 `∅NULL`，而输入非空（dtdeed=2025-10-28），规则与输出不符 → **不收录该 demo**，避免「公式算出值 ≠ 实测值」的假演示。该字段真实规则待 Phase/Code-First 复核（疑有附加条件）。
- 不可单格表达的逻辑（set_date 首见 min(dataasof)=全历史、decode 需字典、LISTAGG）**未做公式**，留在「计算逻辑」列 / 方案B 多天提示 / D 页。

## TC10–TC11 首见 min(dataasof) 活公式（方案3）明细
**背景**：set_date 这类「全历史取最小」字段，矩阵里是「单格(值+多天提示文本)」，无法被公式取 min。故新增**方案3 多值小块**（3 行抽样 `(dataasof, 拍卖排定日)`，dataasof 存**真实日期**），让 `MINIFS` 能算。
- **放置（3 处，实测）**：⑪ 表底(r78–82)、⑱ 表底(r88–92)、D 页(r55–60)。每块：标题 + 表头 + 3 数据行；输入格高亮浅蓝。
- **⑪/⑱ 矩阵 set_date 行 🧮(col5)** = `=MINIFS(A80:A82,B80:B82,"2026-06-30")`（⑱ 为 `A90:A92,B90:B92`），日期格式 `yyyy-mm-dd`，浅绿、带批注指向底部块。
- **D 页** block 自包含，含结果行 `=MINIFS(A57:A59,B57:B59,"2026-06-30")`。
- **真值核**：3 行中仅 `2026-06-30` 那行匹配，其 dataasof=`2026-05-22` → MINIFS 取最早匹配 = **2026-05-22** = 实测 set_date ✓。
- **数据类型核**：dataasof 单元格实测为 `datetime`（非文本）→ MIN 可计算；value 为文本，与文本 criteria `"2026-06-30"` 匹配。

## TC12–TC14 真·Excel 引擎验证 + 缺陷修复 + ② 源头数据（v3）
**TC12 真引擎复算**：`pywin32` COM 打开副本 → `CalculateFull()` → `SpecialCells(xlCellTypeFormulas, xlErrors)` 逐 sheet 扫描。结果：**16/16 sheet 无公式错误**；`D!B60`(首见 MIN) 实算 = `2026-05-22`。

**TC13 缺陷修复（均由真引擎/用户发现）**：
- **MINIFS #NAME?**：本机 Excel 为 Office16，但 `MINIFS`/`MAXIFS` 仅 Excel 2019/365 起支持——首见公式 `=MINIFS(...)` 报 `#NAME?`（用户截图 D!B60）。**改用全版本兼容的 `MIN` + 助列 `IF`**：助列 C=`IF(value=当前值, dataasof, "")`，首见=`MIN(C)`。⑪⑱ 矩阵 set_date 行 + D 页均已改；复算 = 2026-05-22 ✓。
- **规则文本被当公式**：⑪ 计算逻辑列 `= fcbidamount [pool:272]`（C59/C65）以 `=` 开头被 Excel 解析为公式→`#NAME?`。**新增 `_T()`**：文本单元格首字符 `=` → 全角 `＝`（显示几乎一致、确为文本）；真公式单元格不经此函数。复算后 0 错误 ✓。

**TC14 ② src·portnewrezfc 补源头数据**：此前 ② 只有「字段/业务含义/来源类型」3 列、无实例值，导致读者看不到 pipeline 起点。现补 **25 笔 × 63 字段** 的 servicer 原始表 `dev.newrez.portnewrezfc` 最新快照真值（key=`loanid`，as-of 2026-06-10）。校验：`fcreferraldate(7727003984)=2025-03-07` 恰 = ⑩.`referral_start_date`（证改名链起点）；`id/create_time/update_time` 该表无→∅NULL；Carrington 5 笔不在此 Newrez 表→∅NULL（其 raw 源为另一张表）。schema-verify：63 字段中 60 为真列、3 系统列占位。

## 已知限制
1. **无 Excel 引擎**：公式数值结果未在本环境真算（见「关键限制」三重保证）；建议用户开表确认。
2. **`summary_days_in_fcl` 含 TODAY()**：演示结果随打开日逐日增长（与「实时重算」语义一致），与冻结的实测快照(827@06-12)会随时间出现差异——属预期，图例/批注已注明。
3. **跨表引用脆性**：依赖 sheet 名恒定 + 举例列在 5 表统一为 6..30；由生成器后置 pass 用注册表实算地址，避免硬编码。
4. 公式仅覆盖**精选 9 条**代表性逻辑（非全字段）；其余字段「🧮」列留空（美观），逻辑仍在「计算逻辑」列描述。

## TC15 daysinfc 规则澄清 + 非copy规则「计算逻辑」cell 内附工作示例（v7）
**背景**：用户指出 ⑩ `daysinfc` 规则「rename (Newrez) / computed (others)」既错（Newrez 是 copy 非 rename）又含糊（computed 无公式/示例），并要求**所有非 copy 计算规则**在「计算逻辑」cell 内补举例说明。

**TC15.1 规则澄清（已核代码）**：读 `basic_data_pool_config.py`——Newrez(pool:1546)=`daysinfc,`（直传同名列）、Carrington(pool:1587)=`CASE fcl_flag='Active' THEN datediff(referral_start_date, snap_shot_date)+1`、Capecodfive(pool:1628)=`CASE foreclosure_flag='Active' THEN datediff(referral_start_date, dataasof)+1`。真源 `fcl_lineage_source.json` hop rule 改为「Newrez 直传同名列 daysinfc(servicer 自报,不重算)；Carr/CC5 = FCL活跃 ? datediff(referral_start_date,快照日)+1 : NULL」，code→`pool:1546(NZ直传),1587(Carr),1628(CC5)`。重跑 `inject_glin.txt` 刷新 HTML；doc 26 zh/en 逐跳行同步。grep 旧文「rename (Newrez) / computed (others)」全仓 **0 残留**。

**TC15.2 非copy 工作示例**：生成器新增 `eg_worked(meta,field)`，用 demo loan（NZ 7727003984 / CA 7727000806）**真值**在规则后接「｜ 例 …」。覆盖：`servicer`（UNION 分支常量）、`daysinfc`（NZ 直传 461 vs CA datediff 2025-02-19→2026-06-10+1=477）、`activefcflag`（cast vs CASE）、`fcstage`（NZ 直传 vs CA fcl_sub_status）、`summary_foreclosure_status`/`summary_type`（仅 ⑪ 计算层 CASE）、`summary_days_in_fcl`（⑱ 实时重算 461→463）、`actual_*_days`（⑳ TO_DAYS 差）。纯直传/改名=copy 不举例（其 rule 已标「（自 X）」）。

**TC15.3 覆盖审计**：脚本扫 ⑨⑩⑪⑱⑳ 全字段——含计算关键词(CASE/datediff/COALESCE/TO_DAYS/Σ/decode/unpivot/days360/首见/CONCAT/重算)但无示例的字段 = **0**。真 Excel COM 全 16 sheet **0 公式错误**（示例为文本，不影响公式列）；内容级幂等（hash 两跑一致）。

## TC16 ⑨ Carrington 派生字段：文字注 → 活 Excel 公式（v8）
**背景**：用户指出 ⑨ `activefcflag` 的 🧮·Carrington 列是文字注而非公式，且「文字表达已在【计算逻辑】列有了」。**根因**：`activefcflag = CASE fcl_flag='Active' THEN 1 ELSE NULL`（Carrington 分支 pool:1579）的输入 `fcl_flag` 位于 `carrington.portcarrington`——本工作簿未建该 sheet（② 仅 Newrez），公式没有可引用的输入格，故只能写文字注。

**TC16.1 取数（DB 只读 + schema-verify）**：先 `information_schema.columns` 确认 `carrington.portcarrington` 含 `fcl_flag/fcl_sub_status/fcl_referral_date/carrington_ln/fcl_scheduled_sale_date/fcl_sale_held_date/fcl_attorney_name/snap_shot_date`；再查 loan 7727000806 最新快照（`redshift_prod`）：`fcl_flag=Active`、`fcl_sub_status=Contested / Litigation Start`、`fcl_referral_date=2025-02-19`、`carrington_ln=3000077131`、`fcl_attorney_name=Lender Legal PLLC`、两个 sale 日期=NULL。存入 `outputs/fcl_carr_source_demo.json`（脚本只排版）。

**TC16.2 实现**：⑨ 表底新增「Carr 源输入演示」块（8 行原始列，值格浅蓝=公式引用源）。Carr 派生字段（`CARR_DERIVE` 映射 pool:1574-1611）引用该块出**活公式**：`activefcflag=IF(块!fcl_flag="Active",1,"∅NULL")`、`fcstage/svc_loanid/fcsetupdate/referral_start_date/fcfirm/dataasof = 直接引用块格`；`daysinfc` 维持 datediff 活公式。⑩ 的 Carr `activefcflag/fcstage` 改为直传引用 ⑨ 格（去掉旧文字注短路）。仅该 UNION 分支**恒 NULL** 的字段（titleordereddate/noi_date 等）标「Carr 分支=NULL 常量（pool:1574-1611）」——比旧「源未纳入」更准确。

**TC16.3 真·Excel 引擎复算**：COM `CalculateFull` 后全 16 sheet **0 公式错误**；读回 ⑨ `activefcflag`Carr=**1**（CASE 实算）、`svc_loanid`=3000077131、`referral`=2025-02-19、`daysinfc`=477、⑩ `activefcflag`Carr=1（直传）。🧮 计数 476→**487 活公式**（+11）、注 196→185（−11）；内容级幂等（hash 两跑一致）。本次仅改 Excel + 新增 JSON，未触动 lineage/HTML/doc26。

## 结论（v5：每 servicer 一列）

**通过（PASS）**。🧮 公式列已改为**每 servicer 一列**（🧮·Newrez 7727003984 + 🧮·Carrington 7727000806），各列内部统一引用该 servicer 那笔 → 列自洽（结果=该 servicer 该笔实测）、并天然并排展示 servicer 差异（**daysinfc：Newrez 461 直传 vs Carrington 477 datediff**，经本机真 Excel `CalculateFull` 实算确认）。336×2=672 格 → 476 活公式 + 196 诚实注；Carr 计算列加 null-guard（缺值→∅NULL）、⑨ Carr 直传标「源未纳入」。**真 Excel 0 公式错误**、幂等 `e68c7365`。下方 v4 结论（单列全覆盖）为历史。

---
**（v4 历史结论）** 5 非 src 表 **每个字段的 🧮 列已填**：336 字段 → **247 活公式**（直传/改名 = 跨表引用上游层 `='上游'!cell`，把整条 pipeline 变成可联动的活链；+ 9 条计算 demo + 首见 min 方案3）+ **89 诚实注**（NULL 投影 / SLA target 常量 / variance / bid_approval / decode / 系统列 / Hold 多行 / 视图实时算——这些**无法用单格公式如实表达**，强行写公式即造假，故注明原因，规则列另有说明）。② 源头 25 笔已补。**真·Excel 引擎(pywin32 COM CalculateFull)复算：全 16 sheet 0 个公式错误**；修复 2 缺陷（MINIFS→MIN+IF；规则文本被当公式→`_T()`）。全 16 sheet 幂等（`463a343e`）。`summary_days_in_fcl` 含 TODAY() 会逐日增长属预期。
