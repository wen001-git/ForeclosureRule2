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

### Why this rule exists
On 2026-06-02, 5 fields in `14_servicer_fcl_field_spec.xlsx` had wrong source tables in the `Newrez原始字段` column (e.g. `delinquency_status_mba` listed under `portnewrezfc` but actually in `portnewrezgeneral`; `state` under `portnewrezfc` but actually `portnewrezprop.propertystate`; `fcl_flag` which exists in no table). The generated verification SQL inherited all 5 errors because it was built from the unverified col4 path and only 2 of 92 SQLs were spot-checked — both happened to be correct. The true locations had already been discovered earlier in the same session but were not applied. A single `information_schema` cross-check of all 92 pairs would have caught every error up front.

---

## Excel 人工列 / 批注保护规则 (Mandatory)

适用于本项目所有 Excel（尤其 `docs/14_servicer_fcl_field_spec.xlsx`）。

1. **任何列，只要表头（第 1 行）包含「人工」二字，即为用户所有**——脚本与 AI **绝不写入、覆盖、删除或移动**该列及其单元格内容/批注。
2. 用户**手动添加的单元格批注（comment）**同样受保护，不得删除或覆盖。
3. 生成 / 更新 Excel 列时，**必须按表头名称定位目标列**（用 `scripts/_excel_guard.py` 的 `col_by_header`），**不得硬编码列号**——否则用户插入列会导致列号漂移、误写到别的列。
4. 写入任一列前，先用 `scripts/_excel_guard.py` 的 `assert_safe(ws, col)` 校验；命中人工列则中止报错。
5. 重新生成某 sheet（delete + recreate）前，须确认该 sheet 不含人工列 / 批注；若含，改为**就地更新**而非重建。

### Why this rule exists
用户多次手动为 Field Spec 增补注释 / 列，之后被脚本删除。根因：生成脚本按**固定列号**（col9–14）写入；一旦用户插入列，列号漂移，重跑即覆盖用户内容。本规则要求「按表头定位 + 人工列只读」，从机制上杜绝。

---

## doc 14 MD ⇄ Excel 同步规则 (Mandatory)

doc 14 有两份载体：`docs/14_servicer_fcl_field_spec.xlsx`（📋 字段规范 Field Spec sheet，DB 实测的**单一真源**）与 `docs/zh|en/14_bps_driven_servicer_fcl_interface.md`。**任何字段级改动必须两者同步、逻辑保持一致**：

1. 字段属性（标准接口取值范围 / 典型取值 / Newrez 现状 / 验证SQL / 验证结果等）以 **Excel Field Spec 为准**。
2. 改了 Excel 后，**必须运行 `scripts/sync_fieldspec_excel_to_md.py`** 重新生成 zh MD 的字段卡片（Section 2.0–4.1）保持一致——**不得只改其一**。
3. en MD 已卡片化（`scripts/sync_fieldspec_en_cards.py` 生成 per-field 英文卡片，结构同 zh，2026-06-04 v37）。**en 业务散文（业务含义/格式/BPS面板/Newrez状态）在 en MD 卡片中手工维护**（其唯一来源——不在 Excel）；验证 SQL/结果/典型值/Newrez→BPS规则来自 Excel。该生成器**可重跑**（v38）：已卡片化时从卡片解析英文散文、再用 Excel 刷新 SQL/结果/规则；未卡片化时从旧横表解析。故改 Excel 后**重跑 `sync_fieldspec_en_cards.py` 即可刷新 en 的 Excel 来源单元格**；en 业务散文若要改则手改卡片。
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

### Why this rule exists
2026-06-07：多次会话误判"python 不可用"而中断、或改让用户本地重跑；实测内联完全可用（openpyxl 3.1.5 在），仅"读取用户目录下 .py 文件"被端点安全拦截。

---

## Project Context
- Domain: Foreclosure rule processing / compliance automation
- Working directory: `C:\Users\jli\MyData\Copilot\ForeclosureRule2`
