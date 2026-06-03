"""
Add value-range / sample-value content to doc 13 Section 2 (zh + en).

Strategy:
  2.1 (portnewrezfc, 42 fields, already 4-col) → insert separate 2.1-B table after footnote
  2.2 (portnewrezbk, 17 fields, 3-col) → add 4th column inline
  2.3 (portnewrezlm, 12 fields, 3-col) → add 4th column inline

Data source: MCP Redshift queries (2026-06-01)

Run from project root: python scripts/add_section2_examples.py
"""

import sys, io
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ZH = Path("docs/zh/13_newrez_fcl_bps_display_mapping.md")
EN = Path("docs/en/13_newrez_fcl_bps_display_mapping.md")

# ── 2.1-B supplementary table (Chinese) ─────────────────────────────────────

TABLE_21B_ZH = """
#### 2.1-B 取值样例 / Value Examples

> 以下取值范围与枚举样例来自 MCP Redshift 实测（`newrez.portnewrezfc`，截至 2026-06-01）。日期格式均为 YYYY-MM-DD。

| 原始字段 | 类型 | 取值范围 / 取值样例 |
|---|---|---|
| `fcsetupdate` | date | `2024-02-07` ～ `2026-05-26` |
| `fcreferraldate` | date | `2024-02-07` ～ `2026-05-26`（通常与 `fcsetupdate` 相同） |
| `demandsentdate` | date | `2021-10-18` ～ `2026-04-20` |
| `demandexpirationdate` | date | 通常为 `demandsentdate + 30天` |
| `firstlegaldate` | date | 格式 YYYY-MM-DD；Non-Judicial 州多为空（活跃 FCL 57.6% 填充） |
| `servicecompletedate` | date | 格式 YYYY-MM-DD；活跃 FCL 28.9% 填充 |
| `titlereceiveddate` | date | Newrez 不提供，活跃 FCL 0% 填充 |
| `titlecleardate` | date | Newrez 不提供，活跃 FCL 0% 填充 |
| `fcjudgmenthearingscheduled` | date | 格式 YYYY-MM-DD；仅 Judicial 州（11.9% 填充） |
| `fcjudgmententered` | date | 格式 YYYY-MM-DD；仅 Judicial 州（法院录入日） |
| `fcscheduledsaledate` | date | `2025-04-17` ～ `2026-08-06`（18.2% 填充） |
| `fcsalehelddate` | date | `2025-05-27` ～ `2026-05-22`（2.1% 填充，仅完结贷款） |
| `fcremovaldate` | date | 格式 YYYY-MM-DD；FCL 完结时填充 |
| `dtdeedrecorded` | date | 格式 YYYY-MM-DD；活跃 FCL ~0% 填充 |
| `fcl3rdpartyproceedsreceiveddate` | date | 格式 YYYY-MM-DD；极少数完结贷款 |
| `fcstage` | varchar | Newrez 系统阶段文本，不标准化，填充率低 |
| `currentmilestone` | varchar | `'Closed'` · `'First Legal'` · `'Judgment Entered'` · `'Sale Held'` · `'Sold'` · `'Service Complete'` · `'Sale Scheduled'`（62.7% 填充） |
| `lastfcstepcompleted` | varchar | Newrez 系统自由文本，如 `'FC Referral'`、`'Sale Held'` |
| `lastfcstepcompleteddate` | date | 格式 YYYY-MM-DD |
| `fcresults` | varchar | `'REO'`（贷款方取得房产）/ `'3rd Party'`（第三方买家成交）/ 空（进行中 FCL） |
| `fcremovaldesc` | varchar | 自由文本，如 `'Foreclosure Completed'` |
| `activefcflag` | int | `1`（进行中）/ `0`（已完结） |
| `fccontestedflag` | int | `1`（有争议诉讼）/ `0`（无） |
| `judicial` | int | `1`（Judicial 州，如 NY/NJ/FL）/ `0`（Non-Judicial 州，如 CA/TX） |
| `fcfirm` | varchar | 律师事务所名称，自由文本 |
| `fcbidamount` | decimal | `$90,000` ～ `$543,305.96`（活跃 FCL，9.0% 填充） |
| `fcapprbidprice` | decimal | 与 `fcbidamount` 同量级（批准出价，8.9% 填充） |
| `fcsaleamount` | decimal | 格式 NNNNNN.NN；仅拍卖成交时有值 |
| `smsdaysinfc` | int | `1` ～ `606` 天（Shellpoint/SMS 口径） |
| `daysinfc` | int | `1` ～ `814` 天（投资者口径） |
| `fchold1description` | varchar | `'Loss Mitigation Workout'` · `'Awaiting Funds to Post'` · `'Service Delay'` · `'Court Delay'` · `'Hearing Set'` · `'Client Document Execution'` · `'Original Note'` · `'Delinquency Review'` · `'Bankruptcy Filed'` · `'Moratorium'` · `'Awaiting Escrow Analysis'` · `'Title Resolution'`（89.6% 填充） |
| `fchold1startdate` | date | 格式 YYYY-MM-DD |
| `fchold1enddate` | date | 格式 YYYY-MM-DD；空 = Hold 仍持续 |
| `fchold1projectedenddate` | date | 格式 YYYY-MM-DD |
| `fchold2description` | varchar | 同 `fchold1description` 枚举值（69.8% 填充） |
| `fchold2startdate` | date | 格式 YYYY-MM-DD |
| `fchold2enddate` | date | 格式 YYYY-MM-DD |
| `fchold2projectedenddate` | date | 格式 YYYY-MM-DD |
| `fchold3description` | varchar | 同 `fchold1description` 枚举值（52.6% 填充） |
| `fchold3startdate` | date | 格式 YYYY-MM-DD |
| `fchold3enddate` | date | 格式 YYYY-MM-DD |
| `fchold3projectedenddate` | date | 格式 YYYY-MM-DD |

"""

TABLE_21B_EN = """
#### 2.1-B Value Range / Examples

> Value ranges and enumerated samples below are from MCP Redshift live queries (`newrez.portnewrezfc`, as of 2026-06-01). All date formats are YYYY-MM-DD.

| Raw Field | Type | Value Range / Sample Values |
|---|---|---|
| `fcsetupdate` | date | `2024-02-07` to `2026-05-26` |
| `fcreferraldate` | date | `2024-02-07` to `2026-05-26` (usually same as `fcsetupdate`) |
| `demandsentdate` | date | `2021-10-18` to `2026-04-20` |
| `demandexpirationdate` | date | Typically `demandsentdate + 30 days` |
| `firstlegaldate` | date | YYYY-MM-DD; blank for Non-Judicial states (57.6% fill in active FCL) |
| `servicecompletedate` | date | YYYY-MM-DD; 28.9% fill in active FCL |
| `titlereceiveddate` | date | Not provided by Newrez; 0% fill in active FCL |
| `titlecleardate` | date | Not provided by Newrez; 0% fill in active FCL |
| `fcjudgmenthearingscheduled` | date | YYYY-MM-DD; Judicial states only (11.9% fill) |
| `fcjudgmententered` | date | YYYY-MM-DD; Judicial states only (court entry date) |
| `fcscheduledsaledate` | date | `2025-04-17` to `2026-08-06` (18.2% fill) |
| `fcsalehelddate` | date | `2025-05-27` to `2026-05-22` (2.1% fill, completed loans only) |
| `fcremovaldate` | date | YYYY-MM-DD; populated when FCL completes |
| `dtdeedrecorded` | date | YYYY-MM-DD; ~0% fill in active FCL |
| `fcl3rdpartyproceedsreceiveddate` | date | YYYY-MM-DD; rare, completed loans only |
| `fcstage` | varchar | Newrez system stage text; non-standardized, low fill rate |
| `currentmilestone` | varchar | `'Closed'` · `'First Legal'` · `'Judgment Entered'` · `'Sale Held'` · `'Sold'` · `'Service Complete'` · `'Sale Scheduled'` (62.7% fill) |
| `lastfcstepcompleted` | varchar | Newrez free text, e.g. `'FC Referral'`, `'Sale Held'` |
| `lastfcstepcompleteddate` | date | YYYY-MM-DD |
| `fcresults` | varchar | `'REO'` (lender takes property) / `'3rd Party'` (third-party buyer) / blank (active FCL) |
| `fcremovaldesc` | varchar | Free text, e.g. `'Foreclosure Completed'` |
| `activefcflag` | int | `1` (in progress) / `0` (completed) |
| `fccontestedflag` | int | `1` (contested litigation) / `0` (none) |
| `judicial` | int | `1` (judicial state, e.g. NY/NJ/FL) / `0` (non-judicial, e.g. CA/TX) |
| `fcfirm` | varchar | Attorney firm name, free text |
| `fcbidamount` | decimal | `$90,000` to `$543,305.96` (active FCL, 9.0% fill) |
| `fcapprbidprice` | decimal | Similar range to `fcbidamount` (approved bid, 8.9% fill) |
| `fcsaleamount` | decimal | Format NNNNNN.NN; only when sale closed |
| `smsdaysinfc` | int | `1` to `606` days (Shellpoint/SMS basis) |
| `daysinfc` | int | `1` to `814` days (investor basis) |
| `fchold1description` | varchar | `'Loss Mitigation Workout'` · `'Awaiting Funds to Post'` · `'Service Delay'` · `'Court Delay'` · `'Hearing Set'` · `'Client Document Execution'` · `'Original Note'` · `'Delinquency Review'` · `'Bankruptcy Filed'` · `'Moratorium'` · `'Awaiting Escrow Analysis'` · `'Title Resolution'` (89.6% fill) |
| `fchold1startdate` | date | YYYY-MM-DD |
| `fchold1enddate` | date | YYYY-MM-DD; null = hold still active |
| `fchold1projectedenddate` | date | YYYY-MM-DD |
| `fchold2description` | varchar | Same enum values as `fchold1description` (69.8% fill) |
| `fchold2startdate` | date | YYYY-MM-DD |
| `fchold2enddate` | date | YYYY-MM-DD |
| `fchold2projectedenddate` | date | YYYY-MM-DD |
| `fchold3description` | varchar | Same enum values as `fchold1description` (52.6% fill) |
| `fchold3startdate` | date | YYYY-MM-DD |
| `fchold3enddate` | date | YYYY-MM-DD |
| `fchold3projectedenddate` | date | YYYY-MM-DD |

"""

# ── Section 2.2 replacement tables ───────────────────────────────────────────

OLD_22_ZH = """| 原始字段 | 类型 | 业务含义 |
|---|---|---|
| `activebkflag` | int | 是否在破产保护中（1=是 / 0=否） |
| `bkchapter` | int | 破产章节（7 / 11 / 13 等） |
| `bkfileddate` | date | 破产申请日 |
| `bkstatus` | int | 破产状态（数值编码） |
| `bkstage` | int | 破产阶段（数值编码） |
| `bkrcurrentstatusdate` | date | 当前状态生效日期 |
| `bkremovaldate` | date | 破产程序终止日 |
| `bkremovalcode` | int | 破产终止原因（数值编码） |
| `mfrfileddate` | date | 解除留置动议（MFR）提交日 |
| `mfrhearingdate` | date | MFR 听证日 |
| `mfrgranteddate` | date | MFR 批准日 |
| `mfrhearingresults` | int | MFR 听证结果（数值编码） |
| `pocfileddate` | date | 债权申报（POC）提交日 |
| `bkpostpetitionduedate` | date | 破产申请后贷款应付日 |
| `bkcasenumber` | varchar | 破产案件编号 |
| `bkfirm` | varchar | 破产律师事务所名称 |
| `debtorintention` | int | 债务人意向（数值编码） |"""

NEW_22_ZH = """| 原始字段 | 类型 | 业务含义 | 取值样例/范围 |
|---|---|---|---|
| `activebkflag` | int | 是否在破产保护中（1=是 / 0=否） | `1`（破产中）/ `0`（已终止） |
| `bkchapter` | int | 破产章节（7 / 11 / 13 等） | `7`（清算）/ `11`（重组）/ `13`（个人还款计划） |
| `bkfileddate` | date | 破产申请日 | `2008-06-16` ～ `2026-04-27` |
| `bkstatus` | int | 破产状态（数值编码） | `1`～`5`（Newrez 内部码；ETL 未解码，详见 SQL-13） |
| `bkstage` | int | 破产阶段（数值编码） | `0`～`22`（常见：`8`/`21`/`1`/`4`；详见 SQL-13） |
| `bkrcurrentstatusdate` | date | 当前状态生效日期 | 格式 YYYY-MM-DD |
| `bkremovaldate` | date | 破产程序终止日 | `2009-09-18` ～ `2026-04-14` |
| `bkremovalcode` | int | 破产终止原因（数值编码） | `1`（Dismissed）/ `2`（Discharged）/ `3` / `4` |
| `mfrfileddate` | date | 解除留置动议（MFR）提交日 | `2025-06-10` ～ `2026-04-29` |
| `mfrhearingdate` | date | MFR 听证日 | 格式 YYYY-MM-DD |
| `mfrgranteddate` | date | MFR 批准日 | 格式 YYYY-MM-DD |
| `mfrhearingresults` | int | MFR 听证结果（数值编码） | `0`（无结果/待定）/ `3` / `4` / `5` / `6` |
| `pocfileddate` | date | 债权申报（POC）提交日 | `2001-01-01` ～ `2026-05-04` |
| `bkpostpetitionduedate` | date | 破产申请后贷款应付日 | 格式 YYYY-MM-DD |
| `bkcasenumber` | varchar | 破产案件编号 | 如 `'1:23-bk-12345'`（格式随法院） |
| `bkfirm` | varchar | 破产律师事务所名称 | 自由文本，如 `'Robertson Anschutz...'` |
| `debtorintention` | int | 债务人意向（数值编码） | `1`（最常见）/ `2` / `0` |"""

OLD_22_EN = """| Raw Field | Type | Business Meaning |
|-----------|------|-----------------|
| `activebkflag` | int | Currently in bankruptcy protection (1=yes / 0=no) |
| `bkchapter` | int | Bankruptcy chapter (7 / 11 / 13 etc.) |
| `bkfileddate` | date | Bankruptcy filing date |
| `bkstatus` | int | Bankruptcy status (numeric code) |
| `bkstage` | int | Bankruptcy legal stage (numeric code) |
| `bkrcurrentstatusdate` | date | Current status effective date |
| `bkremovaldate` | date | Bankruptcy termination date |
| `bkremovalcode` | int | Bankruptcy removal reason (numeric code) |
| `mfrfileddate` | date | Motion for Relief (MFR) filed date |
| `mfrhearingdate` | date | MFR hearing date |
| `mfrgranteddate` | date | MFR granted date |
| `mfrhearingresults` | int | MFR hearing result (numeric code) |
| `pocfileddate` | date | Proof of Claim (POC) filed date |
| `bkpostpetitionduedate` | date | Post-petition loan payment due date |
| `bkcasenumber` | varchar | Bankruptcy case number |
| `bkfirm` | varchar | Bankruptcy attorney firm name |
| `debtorintention` | int | Debtor intention (numeric code) |"""

NEW_22_EN = """| Raw Field | Type | Business Meaning | Value Range / Examples |
|---|---|---|---|
| `activebkflag` | int | Currently in bankruptcy protection (1=yes / 0=no) | `1` (active BK) / `0` (terminated) |
| `bkchapter` | int | Bankruptcy chapter (7 / 11 / 13 etc.) | `7` (liquidation) / `11` (reorganization) / `13` (individual repayment plan) |
| `bkfileddate` | date | Bankruptcy filing date | `2008-06-16` to `2026-04-27` |
| `bkstatus` | int | Bankruptcy status (numeric code) | `1`–`5` (Newrez internal codes; not decoded by ETL — see SQL-13) |
| `bkstage` | int | Bankruptcy legal stage (numeric code) | `0`–`22` (common: `8`/`21`/`1`/`4` — see SQL-13) |
| `bkrcurrentstatusdate` | date | Current status effective date | YYYY-MM-DD format |
| `bkremovaldate` | date | Bankruptcy termination date | `2009-09-18` to `2026-04-14` |
| `bkremovalcode` | int | Bankruptcy removal reason (numeric code) | `1` (Dismissed) / `2` (Discharged) / `3` / `4` |
| `mfrfileddate` | date | Motion for Relief (MFR) filed date | `2025-06-10` to `2026-04-29` |
| `mfrhearingdate` | date | MFR hearing date | YYYY-MM-DD format |
| `mfrgranteddate` | date | MFR granted date | YYYY-MM-DD format |
| `mfrhearingresults` | int | MFR hearing result (numeric code) | `0` (no result/pending) / `3` / `4` / `5` / `6` |
| `pocfileddate` | date | Proof of Claim (POC) filed date | `2001-01-01` to `2026-05-04` |
| `bkpostpetitionduedate` | date | Post-petition loan payment due date | YYYY-MM-DD format |
| `bkcasenumber` | varchar | Bankruptcy case number | e.g. `'1:23-bk-12345'` (format varies by court) |
| `bkfirm` | varchar | Bankruptcy attorney firm name | Free text, e.g. `'Robertson Anschutz...'` |
| `debtorintention` | int | Debtor intention (numeric code) | `1` (most common) / `2` / `0` |"""

# ── Section 2.3 replacement tables ───────────────────────────────────────────

OLD_23_ZH = """| 原始字段 | 类型 | 业务含义 |
|---|---|---|
| `activelmflag` | int | 是否在 LM 方案中（1=是 / 0=否） |
| `lmdeal` | int | LM 交易类型（数值编码，ETL 解码为文本） |
| `lmprogram` | int | LM 方案名称（数值编码，ETL 解码为文本） |
| `lmstatus` | int | LM 当前状态（数值编码，ETL 解码为文本） |
| `dealstartdate` | date | LM 周期开始日 |
| `lmremovaldate` | date | LM 周期结束日 |
| `lmdecision` | int | LM 审批结论（数值编码，ETL 解码为文本） |
| `denialreason` | int | 拒绝原因（数值编码，ETL 解码为文本） |
| `borrowerintention` | int | 借款人意向（数值编码，ETL 解码为文本） |
| `hardshiptype` | int | 困境类型（数值编码） |
| `daysindeal` | int | 在当前 LM 交易中的天数 |
| `daysinstatus` | int | 在当前状态中的天数 |"""

NEW_23_ZH = """| 原始字段 | 类型 | 业务含义 | 取值样例/范围 |
|---|---|---|---|
| `activelmflag` | int | 是否在 LM 方案中（1=是 / 0=否） | `1`（LM 进行中）/ `0`（未在 LM 或已结束） |
| `lmdeal` | int | LM 交易类型（数值编码，ETL 解码为文本） | 实测值：`1`/`2`/`4`/`5`/`6`/`7`/`9`/`11`；解码→ `Evaluation`/`Modification`/`Forbearance`/`Short Sale`/`DIL` 等（详见 Section 5） |
| `lmprogram` | int | LM 方案名称（数值编码，ETL 解码为文本） | 实测 15+ 种（`10`→Deed-in-Lieu、`21`→Evaluation、`73`/`396`/`496` 等）；解码见 Section 5 |
| `lmstatus` | int | LM 当前状态（数值编码，ETL 解码为文本） | 实测 15+ 种（`5`/`20`/`112`/`113`/`166` 等）；解码→ `Pending Financials`/`Workout Denial` 等（见 Section 5） |
| `dealstartdate` | date | LM 周期开始日 | `2020-08-17` ～ `2026-05-29` |
| `lmremovaldate` | date | LM 周期结束日 | `2020-09-22` ～ `2026-05-29`；空 = 周期仍进行中 |
| `lmdecision` | int | LM 审批结论（数值编码，ETL 解码为文本） | 实测值：`1`/`4`/`5`/`6`/`7`/`10`/`11`/`14`/`17`/`99`；解码→ `Approved`/`Denied`/`Referral to FC`/`Pending` 等（见 Section 5） |
| `denialreason` | int | 拒绝原因（数值编码，ETL 解码为文本） | 实测 10+ 种（`4`/`6`/`76`/`109` 等）；无拒绝时为空 |
| `borrowerintention` | int | 借款人意向（数值编码，ETL 解码为文本） | `1`/`2`/`3`；Newrez 贷款通常为空 |
| `hardshiptype` | int | 困境类型（数值编码） | 实测 10+ 种（`7`/`8`/`11`/`12`/`19`/`20`/`21`/`33`/`35` 等） |
| `daysindeal` | int | 在当前 LM 交易中的天数 | `0` ～ `991` 天 |
| `daysinstatus` | int | 在当前状态中的天数 | `0` ～ `991` 天 |"""

OLD_23_EN = """| Raw Field | Type | Business Meaning |
|-----------|------|-----------------|
| `activelmflag` | int | Currently in LM program (1=yes / 0=no) |
| `lmdeal` | int | LM deal type (numeric code, ETL-decoded to text) |
| `lmprogram` | int | LM program name (numeric code, ETL-decoded to text) |
| `lmstatus` | int | LM current status (numeric code, ETL-decoded to text) |
| `dealstartdate` | date | LM cycle start date |
| `lmremovaldate` | date | LM cycle end date |
| `lmdecision` | int | LM decision outcome (numeric code, ETL-decoded to text) |
| `denialreason` | int | Denial reason (numeric code, ETL-decoded to text) |
| `borrowerintention` | int | Borrower intention (numeric code, ETL-decoded to text) |
| `hardshiptype` | int | Hardship type (numeric code) |
| `daysindeal` | int | Days in current LM deal |
| `daysinstatus` | int | Days in current status |"""

NEW_23_EN = """| Raw Field | Type | Business Meaning | Value Range / Examples |
|---|---|---|---|
| `activelmflag` | int | Currently in LM program (1=yes / 0=no) | `1` (LM active) / `0` (not in LM or ended) |
| `lmdeal` | int | LM deal type (numeric code, ETL-decoded to text) | Observed: `1`/`2`/`4`/`5`/`6`/`7`/`9`/`11`; decoded → `Evaluation`/`Modification`/`Forbearance`/`Short Sale`/`DIL` etc. (see Section 5) |
| `lmprogram` | int | LM program name (numeric code, ETL-decoded to text) | 15+ codes observed (`10`→Deed-in-Lieu, `21`→Evaluation, `73`/`396`/`496` etc.); see Section 5 for decode |
| `lmstatus` | int | LM current status (numeric code, ETL-decoded to text) | 15+ codes observed (`5`/`20`/`112`/`113`/`166` etc.); decoded → `Pending Financials`/`Workout Denial` etc. (see Section 5) |
| `dealstartdate` | date | LM cycle start date | `2020-08-17` to `2026-05-29` |
| `lmremovaldate` | date | LM cycle end date | `2020-09-22` to `2026-05-29`; null = cycle still open |
| `lmdecision` | int | LM decision outcome (numeric code, ETL-decoded to text) | Observed: `1`/`4`/`5`/`6`/`7`/`10`/`11`/`14`/`17`/`99`; decoded → `Approved`/`Denied`/`Referral to FC`/`Pending` etc. (see Section 5) |
| `denialreason` | int | Denial reason (numeric code, ETL-decoded to text) | 10+ codes observed (`4`/`6`/`76`/`109` etc.); blank when no denial |
| `borrowerintention` | int | Borrower intention (numeric code, ETL-decoded to text) | `1`/`2`/`3`; typically null for Newrez loans |
| `hardshiptype` | int | Hardship type (numeric code) | 10+ codes observed (`7`/`8`/`11`/`12`/`19`/`20`/`21`/`33`/`35` etc.) |
| `daysindeal` | int | Days in current LM deal | `0` to `991` days |
| `daysinstatus` | int | Days in current status | `0` to `991` days |"""

# ── Revision history entries ──────────────────────────────────────────────────

REV_ZH_OLD = "| 2026-05-26 | AI Agent（Claude Sonnet 4.6） | v1 |"
REV_ZH_NEW = (
    "| 2026-06-01 | AI Agent（Claude Sonnet 4.6） | v29 | "
    "Section 2 全三个子表新增取值样例：2.1 新增独立附属表「2.1-B 取值样例」"
    "（42 字段，含日期范围、枚举值，数据来自 MCP Redshift 实测）；"
    "2.2 和 2.3 各增第 4 列「取值样例/范围」；中英文版本同步更新 | — |\n"
    "| 2026-05-26 | AI Agent（Claude Sonnet 4.6） | v1 |"
)

REV_EN_OLD = "| 2026-05-26 | AI Agent (Claude Sonnet 4.6) | v1 |"
REV_EN_NEW = (
    "| 2026-06-01 | AI Agent (Claude Sonnet 4.6) | v29 | "
    "Section 2: added value-range/sample-value content to all three subtables — "
    "2.1: new standalone supplementary table '2.1-B Value Range / Examples' (42 fields, "
    "date ranges and enum values from live MCP Redshift queries); "
    "2.2 and 2.3: new 4th column 'Value Range / Examples'; zh+en versions updated | — |\n"
    "| 2026-05-26 | AI Agent (Claude Sonnet 4.6) | v1 |"
)

# ── Section 2.1 insertion anchor ─────────────────────────────────────────────

ZH_21_ANCHOR_OLD = "### 2.2 newrez.portnewrezbk（破产数据，60列）"
ZH_21_ANCHOR_NEW = TABLE_21B_ZH + "### 2.2 newrez.portnewrezbk（破产数据，60列）"

EN_21_ANCHOR_OLD = "### 2.2 newrez.portnewrezbk (Bankruptcy Table, 60 columns)"
EN_21_ANCHOR_NEW = TABLE_21B_EN + "### 2.2 newrez.portnewrezbk (Bankruptcy Table, 60 columns)"

# ── Section 2.1 header note ───────────────────────────────────────────────────

ZH_21_NOTE_OLD = (
    "> 数据规模：活跃 FCL（activefcflag=1）共 **13,321 笔**（dataasof 截至 2026-05-24）  \n"
    "> **验证 SQL**：本表填充率来自 附录 B — SQL-1（可直接复制到 MySQL 运行）"
)
ZH_21_NOTE_NEW = (
    "> 数据规模：活跃 FCL（activefcflag=1）共 **13,321 笔**（dataasof 截至 2026-05-24）  \n"
    "> **验证 SQL**：本表填充率来自 附录 B — SQL-1（可直接复制到 MySQL 运行）  \n"
    "> **取值样例**：见下方 **2.1-B 取值样例**（含字段取值范围与枚举值，来自 MCP 实测）"
)

EN_21_NOTE_OLD = (
    "> Scale: **13,321 active FCL loans** (activefcflag=1, dataasof 2026-05-24)  \n"
    "> **Verification SQL**: Fill rates in this table are produced by Appendix B — SQL-1 (copy and run directly in MySQL)"
)
EN_21_NOTE_NEW = (
    "> Scale: **13,321 active FCL loans** (activefcflag=1, dataasof 2026-05-24)  \n"
    "> **Verification SQL**: Fill rates in this table are produced by Appendix B — SQL-1 (copy and run directly in MySQL)  \n"
    "> **Value Examples**: See **2.1-B Value Range / Examples** below (field ranges and enum values from live MCP queries)"
)

# ── Apply all patches ─────────────────────────────────────────────────────────

def patch(path, patches):
    text = path.read_text(encoding="utf-8")
    for old, new, label in patches:
        if old not in text:
            print(f"  WARNING: '{label}' not found in {path.name}")
            continue
        text = text.replace(old, new, 1)
        print(f"  OK: {label}")
    path.write_text(text, encoding="utf-8")


def main():
    print(f"=== Patching {ZH.name} ===")
    patch(ZH, [
        (REV_ZH_OLD,       REV_ZH_NEW,       "revision history entry"),
        (ZH_21_NOTE_OLD,   ZH_21_NOTE_NEW,   "Section 2.1 header note"),
        (ZH_21_ANCHOR_OLD, ZH_21_ANCHOR_NEW, "2.1-B table insertion"),
        (OLD_22_ZH,        NEW_22_ZH,         "Section 2.2 4th column"),
        (OLD_23_ZH,        NEW_23_ZH,         "Section 2.3 4th column"),
    ])

    print(f"\n=== Patching {EN.name} ===")
    patch(EN, [
        (REV_EN_OLD,       REV_EN_NEW,       "revision history entry"),
        (EN_21_NOTE_OLD,   EN_21_NOTE_NEW,   "Section 2.1 header note"),
        (EN_21_ANCHOR_OLD, EN_21_ANCHOR_NEW, "2.1-B table insertion"),
        (OLD_22_EN,        NEW_22_EN,         "Section 2.2 4th column"),
        (OLD_23_EN,        NEW_23_EN,         "Section 2.3 4th column"),
    ])

    print("\nDone.")


if __name__ == "__main__":
    main()
