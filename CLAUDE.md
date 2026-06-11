# ForeclosureRule2 — Project Rules

## Session Workflow (Mandatory)

### 1. Prompt Log
Append every user instruction to `prompt.md` in the project root using this format:

```
## [YYYY-MM-DD HH:MM UTC] <one-line summary>
> <verbatim user prompt>
```

Do this at the start of processing each user message, before any other work.

### 2. Decision Log
Whenever making a key technical or architectural decision, append to the `## Decisions` section of `prompt.md`:

```
### Decision: <title> [YYYY-MM-DD]
- **Context**: why this decision was needed
- **Options considered**: A, B, C
- **Choice**: chosen option
- **Reason**: rationale
```

### 3. Milestone Wrap-up (after each completed phase)
After declaring a milestone/phase complete:
1. Run `/simplify` to clean up changed code (remove redundancy, unify style)
2. Run all available tests and report a pass/fail summary
3. Log the milestone completion in `prompt.md` under `## Milestones`

## Standard Document Header Rule (Mandatory for all generated documents)

Every document created in this project must begin with a standardized header block before any content.

### Required Header Sections

#### 1. Document Purpose
Explain:
- **Why** this document exists
- **What problem** it solves or knowledge gap it fills
- **Scope** — what is and is not covered
- **System fit** — how it relates to the broader project

#### 2. Target Audience
Identify primary and secondary readers, e.g.:
developers · data engineers · business analysts · validators ·
operations teams · onboarding engineers · reviewers · architects ·
future AI sessions

#### 3. Revision History
| Date | Author | Version | Changes | Related |
|------|--------|---------|---------|---------|
| YYYY-MM-DD | AI Agent | v1 | Initial draft | — |

### Optional Header Sections (include when applicable)

| Section | When to include |
|---------|----------------|
| Dependencies | document relies on other docs, systems, or data |
| Assumptions | facts taken as true without verification |
| Blockers / Open Questions | unresolved issues affecting completeness |
| Related Documents | companion docs, upstream/downstream references |
| Glossary | domain terms, abbreviations, status codes |
| System Boundaries | explicit in-scope vs. out-of-scope boundaries |
| Known Limitations | gaps, approximations, areas needing validation |

### Why this rule exists
Headers help readers immediately understand:
- **Why** to read the document
- **Whether** it is relevant to them
- **How mature / accurate** it is (via version + change log)
- **How it evolved** over time

---

## Code-First ETL / Data Lineage Analysis Rule (Mandatory)

When analyzing any ETL pipeline, data flow, table write mechanism, or data lineage:

1. **Read source code before concluding**: inspect relevant config files, utility functions, SQL templates, flow/task code, and write/sync helpers before making an architectural conclusion. MCP/database queries can verify the current data state, but they cannot by themselves prove why data looks that way or how a table is written.

2. **Do not infer architecture from symptoms alone**: never conclude that a table is independently maintained, incorrectly wired, or written by a separate mechanism only from NULL timestamps, row count differences, or field value mismatches. These symptoms may be caused by ETL delay, environment differences, snapshot timing, filters, SQL design, or data quality issues.

3. **If code and MCP data conflict, code has priority for design intent**: MCP/database results show a point-in-time state snapshot. Source code shows intended processing logic and write paths. Treat MCP findings as validation evidence or anomaly evidence, then reconcile them against code before documenting conclusions.

### PrefectFlow 本地代码路径（Code-First 取证用）

**本地 PrefectFlow 仓库路径**：`C:\Users\jli\MyData\Copilot\PrefectFlow`

需要 Code-First 取证 `pool:XXX`（`basic_data_pool_config.py`）/ `asset:XXX`（`asset_managment_config.py`）等代码引用时，**直接用 Read 工具读本地文件**，不要尝试 WebFetch 内网 GitLab（gitlab.bridgerinvestment.com 需要登录认证，WebFetch 必败）。

关键文件路径：
- `flow/basic_data/basic_data_config/basic_data_pool_config.py` —— Redshift SQL 模板（GEN_FCL_DETAIL / GEN_FCL_STAGE / CREATE_BASIC_FCL 等，~2400+ 行）
- `flow/bps/bps_config/asset_managment_config.py` —— BPS 同步 SQL（UPDATE_FORECLOSURE / GEN_FORECLOSURE_* / GET_FCL_STAGE_DATA 等）
- `flow/basic_data/portmonth/gen_portmonth_v4.py`、`gen_portmonth_mysql.py` —— portmonthbase 双写
- `flow/basic_data/portmonth/daily_data_loan_common_config.py` —— L2 统一日表
- `flow/portfolio_daily/portdaily_config.py` —— L2 portdaily_v2 派生

文档中保留 `gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a3/...#LXXX-XXX` 链接给读者点击（钉到提交 32a750a3，本地与该提交逐字节一致），AI 自己取证用本地 Read。

### Why this rule exists
2026-06-11：在 doc 33 §2.5.1 取证 `timeline_sale_date_set_date` 的 min(dataasof) 算法时，尝试 WebFetch GitLab 内网失败，本应直接读本地 PrefectFlow 仓库（用户存在 `C:\Users\jli\MyData\Copilot\PrefectFlow`），但因为没有这条规则导致绕弯。

---

## Schema-Verify Rule for Generated DB Artifacts (Mandatory)

When generating any artifact that references database `table.column` names — verification SQL, queries, field-mapping tables, data-lineage cells, `源表`/source-path columns — every column-table pair MUST be validated against the live schema before the artifact is considered done.

1. **Never trust a document/spreadsheet's stated source path as ground truth.** A field's `Newrez原始字段`, `来源表`, or `完整路径` value in an existing doc/Excel may be wrong. The database (`information_schema.columns`) is the only authority for where a column actually lives. If you build a new artifact (e.g. SQL) from a doc's source-path field, you inherit its errors.

2. **Validate ALL pairs, not a sample.** When generating N similar artifacts (e.g. 92 SQLs), spot-checking 2–3 is insufficient — the broken ones hide in the unchecked majority. One `information_schema` query covers every table+column at once:
   ```sql
   SELECT table_name, column_name FROM information_schema.columns
   WHERE table_schema='<schema>' AND table_name IN (...);
   ```
   Cross-check every referenced `table.column` against that result; flag any that don't exist.

3. **Cross-reference prior findings in the same session.** If you already discovered the true location of a column earlier (e.g. `delinquency_status_mba` is in `portnewrezgeneral`, not `portnewrezfc`), apply that knowledge — do not silently re-introduce the wrong path from a stale source.

4. **A generated SQL is not "verified" until it executes.** Run representative queries of each *type/source-table* (not just any 2), or validate the full column set programmatically. "It looks runnable" ≠ verified.

5. **血缘 hop 列必须 DB 核验；派生/无源必须显式占位、不得伪装成真列。** 适用于 `outputs/fcl_lineage_source.json` 及任何派生 artifact（`outputs/fcl_pipeline.html` 内嵌 GLIN、doc 25-31 血缘表）：
   - **每个 `hop.t.c`（真实列）必须是 `information_schema` 实测存在的列**。新增/修改血缘后，跑 `python - < scripts/verify_lineage_columns.txt` 生成 `outputs/_chk_rs.sql`（port.\* → `redshift_prod`）与 `outputs/_chk_mysql.sql`（newrez.\*+bpms.\* → `mysql_prod`）两份 NOT-IN 检查，经对应 MCP 执行，**两边都须返回 0 行**才算通过；任何返回的 `(tbl, c)` 即「血缘写了一个该表不存在的列」，必须修真源 JSON。
   - **某跳无独立源列（派生 / 计算 / 该表不提供该列）时，必须用明确占位**（`(derived)` / `(stage end)` / `(none)` / `—`），且 HTML/doc **渲染为「派生 / 无独立列」样式**（`db.schema.table` + 灰显占位标签），**绝不可拼成 `table.占位` 让它看起来像一个真字段**。
   - 改完真源 JSON 后必须重跑 `scripts/inject_glin.txt` 刷新 HTML 内嵌 GLIN，并同步对应 doc 25-31 单元格——三处（JSON / HTML / doc）保持一致。

### Why this rule exists
On 2026-06-02, 5 fields in `14_servicer_fcl_field_spec.xlsx` had wrong source tables in the `Newrez原始字段` column (e.g. `delinquency_status_mba` listed under `portnewrezfc` but actually in `portnewrezgeneral`; `state` under `portnewrezfc` but actually `portnewrezprop.propertystate`; `fcl_flag` which exists in no table). The generated verification SQL inherited all 5 errors because it was built from the unverified col4 path and only 2 of 92 SQLs were spot-checked — both happened to be correct. The true locations had already been discovered earlier in the same session but were not applied. A single `information_schema` cross-check of all 92 pairs would have caught every error up front.

On 2026-06-11, the FCL lineage (`fcl_lineage_source.json`, behind doc 25-31 + the pipeline HTML graph) carried three lineage-column errors that a full `information_schema` NOT-IN sweep caught at once: (1) `demand_end_date` had its real source column `demandexpirationdate` (DB-verified to exist in BOTH `newrez.portnewrezfc` and `port.basic_data_loan_fcl`) replaced by placeholders `—` / `(stage end)`, so the lineage graph rendered a fake/empty column and falsely implied "newrez has no demand-end source"; (2)+(3) `bid_id` and `funding_id` had a final hop into `bpms.biz_data_view_loan_details_foreclosure` claiming columns `bid_id` / `funding_id`, but the view exposes neither (only `id`/`loanid`/`svcloanid`/`tenant_id`) — these IDs live only in `bpms.sync_loan_foreclosure`, so the chain had to terminate one hop earlier. All three were invisible to spot-checking but fell out of one generated NOT-IN check run against `mysql_prod` + `redshift_prod` (389 simple-column pairs across 19 tables → 0 rows after fix).

---

## 修复传播规则：改一处必须同步依赖链上下游 (Mandatory)

发现并修复任何文档 / artifact 的一处错误（事实、字段、来源表、血缘、结论、数值、命名等）时，**不得只改命中的那一处**——必须把修复传播到它在依赖链上的**上游（它所依赖/派生自的来源）与下游（依赖/派生/引用它的所有副本）**，使整条链在同一次改动内保持一致、无矛盾、无残留旧值。

### 必做步骤
1. **先定位真源（single source of truth），从根修起。** 若错误出现在派生件（HTML / MD / Excel / SQL）而真源另有其物（如 `outputs/fcl_lineage_source.json`、DB schema、某 config），**先改真源**，再向下游重生成/同步——绝不只 patch 派生件留真源带病。
2. **画出该文档的依赖图，逐个落实：**
   - **上游**：本文结论来自哪里？来源若也错，连同上游一并修（否则下次重生成又退回旧值）。
   - **下游**：哪些文件由本文派生或引用本文？全部同步。本项目已知主链：
     - 血缘：`outputs/fcl_lineage_source.json` → `scripts/inject_glin.txt` 刷新 `outputs/fcl_pipeline.html` 内嵌 GLIN → doc 25-31（zh+en）。三处必须一致。
     - 字段规范：`docs/14_servicer_fcl_field_spec.xlsx`（DB 实测真源）⇄ `docs/zh|en/14_*.md` 字段卡片（见「doc 14 MD ⇄ Excel 同步规则」）。
     - 文档头部「自动生成…重跑 X」语句必须指向**现行**脚本/链路（旧生成器删除后要改掉，否则误导）。
   - 跨语言镜像（`docs/zh/**` ⇄ `docs/en/**`）视为彼此的下游，必须同步。
3. **改完用 grep 全仓搜「旧的错误值 / 旧字段名 / 旧来源表 / 旧结论关键词」确认 0 残留**——任何残留即一处未传播到的下游副本。
4. **若依赖链由脚本生成，** 改真源后重跑对应生成脚本（而非手改派生件），并按各自规则做后置校验（如血缘的 `verify_lineage_columns.txt` 列核验须 0 行）。
5. **传播范围不确定时**，宁可多搜一轮（grep 关键词 + 列出引用本文的文件）也不要漏改；漏改下游会留下「一处对、一处旧」的自相矛盾。

### Why this rule exists
2026-06-11：修 `demand_end_date` / `bid_id` / `funding_id` 三处血缘错误时，真源 `fcl_lineage_source.json` 改完、HTML 内嵌 GLIN 经 `inject_glin.txt` 重生成后，**doc 26（zh+en）仍残留**指向 `biz_data_view_loan_details_foreclosure.bid_id/funding_id` 的错误视图跳——若不向下游传播并 grep 复查，下游文档会与真源/HTML 自相矛盾。更早（2026-06-02、历史多次）也反复出现「只改了 Excel/MD 其一、另一处留旧结论」「文档头部仍写已删除的 `gen_fcl_lineage.py`」等漏传播问题。本规则把「改一处 = 改整条依赖链」固化为强制动作。

---

## Excel 人工列 / 批注保护规则 (Mandatory)

适用于本项目所有 Excel（尤其 `docs/14_servicer_fcl_field_spec.xlsx`）。

1. **任何列，只要表头（第 1 行）包含「人工」二字，即为用户所有**——脚本与 AI **绝不写入、覆盖、删除或移动**该列及其单元格内容/批注。
2. 用户**手动添加的单元格批注（comment）**同样受保护，不得删除或覆盖。
3. 生成 / 更新 Excel 列时，**必须按表头名称定位目标列**（用 skill `excel-pipeline-lineage` 工具箱的 `col_by_header`，见下），**不得硬编码列号**——否则用户插入列会导致列号漂移、误写到别的列。
4. 写入任一列前，先用工具箱的 `assert_safe(ws, col)` / `sheet_has_manual(ws)` 校验；命中人工列则中止/跳过。
   > 工具箱在 `.claude/skills/excel-pipeline-lineage/references/toolkit.txt`，经 `exec(open(...,encoding='utf-8').read())` 加载（**勿 import**）。注：旧引用的 `scripts/_excel_guard.py` 实际不存在，守卫逻辑现统一在该 toolkit。
5. 重新生成某 sheet（delete + recreate）前，须确认该 sheet 不含人工列 / 批注；若含，改为**就地更新**而非重建。

### Why this rule exists
用户多次手动为 Field Spec 增补注释 / 列，之后被脚本删除。根因：生成脚本按**固定列号**（col9–14）写入；一旦用户插入列，列号漂移，重跑即覆盖用户内容。本规则要求「按表头定位 + 人工列只读」，从机制上杜绝。

---

## 生成 Excel：优先用 skill `excel-pipeline-lineage`

任何 pipeline / 数据血缘 / 字段 mapping 的 Excel（doc 14/16/19/21 等）优先走该 skill：`.claude/skills/excel-pipeline-lineage/`（SKILL.md + `references/toolkit.txt` 配色/人工守卫/幂等块/总览 + `archetypes.md` 三骨架 + `data_model.md` JSON 真源 schema）。

- 黄金参考生成器：`outputs/enrich_doc19_table_meta.txt`（doc 19，`python - < outputs/enrich_doc19_table_meta.txt` 运行；doc 19 为 zh-only）；字段血缘矩阵：`scripts/build_fcl_field_lineage_xlsx.py`。
- 内容放数据源 JSON（如 `outputs/fcl_table_meta.json`），脚本只排版；幂等可重跑（START/END 标记删旧重插、总览删后重建）。

---

## doc 14 MD ⇄ Excel 同步规则 (Mandatory)

doc 14 有两份载体：`docs/14_servicer_fcl_field_spec.xlsx`（📋 字段规范 Field Spec sheet，DB 实测的**单一真源**）与 `docs/zh|en/14_bps_driven_servicer_fcl_interface.md`。**任何字段级改动必须两者同步、逻辑保持一致**：

1. 字段属性（标准接口取值范围 / 典型取值 / Newrez 现状 / 验证SQL / 验证结果等）以 **Excel Field Spec 为准**。
2. 改了 Excel 后，**必须同步更新 zh MD 的字段卡片（Section 2.0–4.1）**保持一致——**不得只改其一**。
   > ⚠️ 原同步生成器 `scripts/sync_fieldspec_excel_to_md.py` **已不在仓库**（2026-06-10 审计确认缺失）。重建前：手工保持 Excel⇄zh MD 一致，或按 skill `excel-pipeline-lineage`（archetype C 字段 mapping 模式）重做生成器。
3. en MD 已卡片化（per-field 英文卡片，结构同 zh）。**en 业务散文（业务含义/格式/BPS面板/Newrez状态）在 en MD 卡片中手工维护**（其唯一来源——不在 Excel）；验证 SQL/结果/典型值/Newrez→BPS 规则来自 Excel。
   > ⚠️ 原 en 卡片生成器 `scripts/sync_fieldspec_en_cards.py` **已不在仓库**（2026-06-10 审计确认缺失）。改 Excel 后需**手工**刷新 en 卡片里 Excel 来源单元格（验证 SQL/结果/规则），或重建该生成器；en 业务散文一律手改卡片。
4. 任何结论性判断（某字段是否已提供 / 编码是否解码 / 来源表是哪张等）**必须先 DB 实测（information_schema + 数据查询），再同时落到 Excel 与 MD**，避免一处对、一处旧。

### Why this rule exists
2026-06-02 多次出现「只改了 Excel/MD 其一，另一处留旧结论」导致前后矛盾（如 foreclosure_flag、lm_flag 的 Newrez 现状）。本规则确保两份载体始终一致，且以 DB 实测为唯一真相来源。

---

## 数据库只读（强制）+ 验证用 prod 库 (Mandatory)

1. **所有数据库一律只读**——不分 dev / prod / redshift / mysql、不分任何环境、不分任何连接（MCP 或脚本）：**只允许 SELECT / 读取，禁止任何写操作**（INSERT / UPDATE / DELETE / REPLACE / TRUNCATE / DROP / ALTER / CREATE 及一切 DDL/DML 写）。绝不修改数据、绝不删除数据。

2. **文档/字段验证以 prod 数据为准**：
   - `mysql_prod` —— MySQL **prod** 库（host `bridg004-db-prod...`，database **`bpms`**），BPS 系统表（`sync_loan_foreclosure` 等）所在；用于验证 BPS 直接取值。
   - `redshift_prod` —— Bridger 的 **prod** Redshift（host `brig-redshift...`，database 名为 `dev` 但实为 prod 集群）。（曾误命名为 `redshift_dev`，2026-06-04 更正为 `redshift_prod`。）
   - dev/test 库（`bridg004-db-test` / `bpms_dev`）数据滞后（如 BPS 表停在 2026-03-12，Newrez 源到 2026-06-01），**仅作滞后参考**；需要与 Newrez 源同一数据日期对比时，必须用 prod。

3. **DB 凭据只存放于 gitignored `.mcp.json`**，**不得写入任何 git 跟踪文件**（含本 CLAUDE.md、文档、脚本）——本规则按名称/角色引用各库，不含明文密码。

### Why this rule exists
2026-06-04：① 防止对任何库的误写/误删（数据安全）；② dev test 库与 Newrez 源数据日期不匹配，导致 mapping rule 无法同日验证，须改用 prod（mysql_prod=bpms、redshift_prod）。

---

## Python 执行限制（端点安全）— 用内联方式，勿执行用户目录下的 .py 文件 (Mandatory)

- **现象**：用任何本地解释器执行位于用户目录（`C:\Users\jli\...`）下的 `.py` 脚本文件都会 `[Errno 13] Permission denied`（端点安全禁止"读取用户目录下的 .py"，与解释器无关：`C:\miniconda` / `C:\Users\jli\AppData\Local\miniconda3` / WindowsApps 三者实测均如此）。
- **解决**：改用内联执行 —— `python -c "..."` 或 stdin heredoc `python - <<'EOF' … EOF`（代码经 stdin 传入、不读取 .py 文件），可正常运行，且 `openpyxl`/`json` 等库可用。脚本若要可复用，存为 `.txt` 再 `python - < script.txt`（仍走 stdin），或放到用户目录之外再 `python file.py`。
- **适用**：生成/更新 Excel·MD 等脚本逻辑一律以 heredoc / `-c` / `python - < file.txt` 内联执行；不要写成 `.py` 再 `python xxx.py`。
- **Bash cwd 陷阱**：Bash 工具默认工作目录是父目录 `C:\Users\jli\MyData\Copilot`，**不是**项目根 `ForeclosureRule2`；跑相对路径命令前先 `cd /c/Users/jli/MyData/Copilot/ForeclosureRule2`（或用绝对路径），否则相对路径会 FileNotFound。
- **控制台编码**：内联 python 打印中文 / 圈号（⓪②㉔等）前先 `sys.stdout.reconfigure(encoding='utf-8')`（或用 toolkit 的 `utf8_stdout()`），否则控制台 cp1252 触发 `UnicodeEncodeError`。

### Why this rule exists
2026-06-07：多次会话误判"python 不可用"而中断、或改让用户本地重跑；实测内联完全可用（openpyxl 3.1.5 在），仅"读取用户目录下 .py 文件"被端点安全拦截。

---

## Deprecated Docs — DO NOT READ (Mandatory for AI coding tools)

以下文档已**归档**，**AI 编码工具（Claude Code / Cursor / Copilot 等）请勿读取作为信息源**——内容多处已被新文档校正，继续参考会引入过时/错误信息：

- `docs/archive/**/*.DEPRECATED.md` —— 全部归档文档（迁离主 `docs/` 路径，文件名含 `DEPRECATED`）
- 当前归档清单：
  - `docs/archive/zh/21_fcl_field_lineage.DEPRECATED.md`（2026-06-11 归档；ER 部分迁入 doc 33、字段血缘迁入 doc 25-30、业务理由见 doc 20 §A.6、MCP 自查见 doc 98）
  - `docs/archive/en/21_fcl_field_lineage.DEPRECATED.md`（同上 en 镜像）

**例外**：如果用户**显式问到**这些归档文档的历史内容，可以读取并明确告知"该信息来自归档文档 `docs/archive/...`，已被 doc X 取代"。

### Why this rule exists
2026-06-11：doc 21 旧字段血缘被 doc 25-30 取代后，AI 工具仍可能从文件树扫到 `docs/zh/21_*.md` 并把过时信息（如 doc 02/19 中已校正的 sync_portmonth 上游、demand_end_date 与 stage_days 关系、view 是否经 5 张 sync 表汇入等）当成事实。物理迁至 `docs/archive/` 目录 + 文件名加 `DEPRECATED` + 本节硬指令三重防护。

---

## Project Context
- Domain: Foreclosure rule processing / compliance automation
- Working directory: `C:\Users\jli\MyData\Copilot\ForeclosureRule2`
