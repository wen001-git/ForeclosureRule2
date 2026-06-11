# doc 14 — BPS-Driven Servicer FCL Data Interface Standard

---

## Document Purpose

- **Why this document exists**: Doc 09 (industry-standard perspective) starts from CFPB/MBA norms and defines the abstract fields a Servicer *should* provide. This document approaches the problem from the opposite direction — starting from the *actual display requirements* of BPS Asset Management's five Foreclosure panels, and reverse-engineering each panel's required Servicer source fields to produce BPS's concrete data interface specification.
- **Problem solved**: When the team needs to tell a new Servicer "you must provide these specific fields," a document grounded in BPS display reality — not just industry norms — is needed as the formal basis for field completion requests.
- **Scope**: All Servicer fields required by BPS's five Foreclosure panels (~92 fields total: 12 four-dimension state foundation fields + 68 BPS display detail fields + 12 Newrez enhancement fields); Newrez is used as the compliance benchmark. ETL intermediate-layer code details are out of scope (see doc 12).
- **System fit**: This document is the BPS-system implementation version of doc 09. Doc 09 = industry access standard (29 abstract fields); this document = BPS onboarding standard (~92 concrete fields, including foundation state flag layer, BPS display detail layer, Newrez enhancement layer, and compliance status).

## Target Audience

Primary: **Data governance team · New Servicer onboarding engineers · BPS system operations**  
Secondary: Data quality engineers · Compliance analysts · Future AI sessions

## Revision History

| Date | Author | Version | Changes | Related |
|------|--------|---------|---------|---------|
| 2026-05-27 | AI Agent (Claude Sonnet 4.6) | v1 | Initial draft: 7 Sections + Appendix A; ~67 Servicer fields defined from BPS five-panel reverse mapping; Newrez compliance status based on doc 13 MCP live measurements (2026-05) | doc 09, doc 13 |
| 2026-05-28 | AI Agent (Claude Sonnet 4.6) | v2 | Added Appendix B: `port.basic_data_loan_fcl` ETL intermediate table field classification (✅ BPS active vs 🔮 ETL-normalized/not-in-BPS); covers ~37 business fields; 4 reserved fields annotated with future use intent | doc 12 v5, doc 13 v21 |
| 2026-05-28 | AI Agent (Claude Sonnet 4.6) | v4 | All 7 field specification tables (Sections 2.1–2.5, 3.1, 4.1) supplemented with standalone "Business Meaning / Calculation Logic" sub-tables covering all 67 fields; zh+en synchronized | doc 13 |
| 2026-05-28 | AI Agent (Claude Sonnet 4.6) | v5 | Section 2.3: added `noi_date` field (separating formal Notice of Intent from Demand Sent Date as distinct concepts); updated `demand_sent_date` BPS mapping and business meaning; Section 5.1/5.2 field counts updated (68 fields total, ❌ 7 not provided by Newrez) | — |
| 2026-05-28 | AI Agent (Claude Sonnet 4.6) | v6 | Added Section 2.0 "Four-Dimension State Foundation Fields" (12 fields: delinquency_status/next_payment_due_date/days_past_due/foreclosure_flag/lm_flag/lm_type/lm_start_date/lm_end_date/hold_flag/hold_reason/reo_flag/reo_acquisition_date); added delinquency_status MBA allowed values table; document scope updated to ~80 fields; Section 5.1 compliance matrix updated; Section 1.4 comparison table updated | doc 09 |
| 2026-05-28 | AI Agent (Claude Sonnet 4.6) | v7 | MCP live query of portnewrezfc (62 cols) + portnewrezgeneral (100+ cols) identified high-value fields Newrez provides but system does not utilize; added Section 2.6 "Loan Attribute and Risk Enhancement Fields" (9 fields: investor_loan_id/lien_position/interest_paid_through_date/in_auction_flag/borrower_deceased_flag/reason_for_default/hold_1/2/3_comment); Section 2.4 supplemented with hold_1/2/3_modified_date (P2); zero-fill fields (SR Lien/SCRA/FEMA etc.) documented as future extensions; document scope updated to ~92 fields | MCP live measurement 2026-05 |
| 2026-05-29 | LiJiawen | v13 | Renamed standard interface fields: `last_step_completed` → `last_completed_step`, `last_step_completed_date` → `last_completed_step_date` (eliminates naming ambiguity: `_completed` suffix could be misread as a boolean/status flag; BPS internal field `summary_last_step_completed` unchanged) | — |
| 2026-06-02 | AI Agent (Claude Sonnet 4.6) | v16 | `delinquency_status` allowed-values table completed with 3 DB-verified real values: `Foreclosure / Non-Perf BK`, `Foreclosure / Perf BK` (→FCL + bankruptcy='Y'), `Settlement` (special handling); footnote states all 19 values, consistent with doc 08 and DB verification; zh/en synced | doc 08 · DB verified 2026-06-01 |
| 2026-06-03 | AI Agent (Claude Opus 4.8) | v19 | Renamed standard interface field `sms_days_in_fcl` → **`servicer_days_in_fcl`** (removed single-servicer brand "SMS"=Shellpoint; a servicer-agnostic standard should not embed one servicer's brand; pairs with `days_in_fcl`, matches ETL alias svc_days_infc). Kept Newrez column `smsdaysinfc` / BPS column `summary_sms_days_in_fcl` / UI "SMS Days" unchanged. Updated Excel col C + meaning + col13 comment (synced to zh cards), en table, doc 13 §3.7 footnote, 3 generator-script keys | DB/code verified · doc 13 v34 |
| 2026-06-03 | AI Agent (Claude Opus 4.8) | v18 | Corrected `active_fcl_flag` value semantics: `activefcflag=0` previously labeled "completed"; it actually means **not currently in active foreclosure** (DB-verified: Reinstated 26 / Loss Mitigation 16 / Paid in Full 11 / truly-completed 10; BPS labels all "Closed Foreclosure" ≠ Completed). Updated Field Spec Excel value-range + meaning (synced to zh cards) and en horizontal table; synced with doc 13/16 | DB-verified 2026-06-03 |
| 2026-06-04 | AI Agent (Claude Opus 4.8) | v34 | Field Spec gained **two BPS-side verification columns** (symmetric to the Newrez side): `BPS验证SQL` (value queries against **prod bpms** sync_* tables) + `BPS验证结果` (prod read-only measurements, 63 fields populated / 29 N/A); the former `验证SQL`/`验证结果` columns were renamed `Newrez验证SQL`/`Newrez验证结果`. All bpms table.column pairs Schema-Verified against prod information_schema (63/63 pass). Results carry a dual-date as-of: business snapshot `fctrdt≤2026-06-01` (**aligned** with the Newrez source data date) + ETL load `2026-06-03` (from `sync_fcl_stage_info`, the only table whose update_time is populated; the main sync family's update_time is all-NULL = upsert excludes it). Prod anomalies found: `summary_completed_foreclosure`/`summary_servicer_number` all-NULL, 4 timeline columns 0-filled, a few un-decoded numeric codes in `program`/`denialreason`. zh cards synced (per-field BPS result row + BPS SQL block). en detailed per-field BPS measurements live in the Excel Field Spec (single source of truth); this en horizontal table is not card-ified. | mysql_prod read-only 2026-06-04 · data date 2026-06-01 |
| 2026-06-04 | AI Agent (Claude Opus 4.8) | v35 | Added standard interface field **`fcl_removal_description`** to Section 2.2 (FCL removal reason, source `portnewrezfc.fcremovaldesc`; right after `fcl_results`, P1) — fills the missing "why" companion to `fcl_removal_date` (the "when"). It is already consumed by BPS (`summary_foreclosure_status = 'Closed Foreclosure:' + fcremovaldesc`), so it's a real interface dependency. BPS has no standalone column → BPS verify SQL/result = N/A-with-note (same as `fcl_results`). DB-measured 2026-06-01 (enum, removed loans only): Reinstated:26 / Loss Mitigation:16 / Paid in Full:11 / Process Complete:9 / Deed in Lieu Cmplte:1 (~1.2% fill). Row inserted under a backup + per-field O/P/Q value+comment equality guard, with section-header merges unmerged/re-merged and `#` renumbered 1..93; zh cards + en table + both generator MAP/TYPE synced | DB-measured 2026-06-01 · mysql_dev |
| 2026-06-04 | AI Agent (Claude Opus 4.8) | v36 | Added a column **`Newrez → BPS 规则（doc 13/16）`** to the Field Spec (inserted before `Newrez状态`, right after `BPS面板/功能`): per-field "Newrez source value → BPS value" transform rule (direct copy / `judicial=1→'Judicial'` / `COALESCE(dtdeedrecorded,fcremovaldate)` / integer code decoded via `portnewrezdatadic` / 3-slot UNPIVOT / `COALESCE(datadic-decode, raw code)` / hard-coded NULL / N/A, etc.), all 93 fields; rules sourced from doc 13 and doc 16 (`build_bps_display_mapping_xlsx.py` mapA tables), aligned with the field→BPS-column `MAP` in `add_field_spec_bps_verify_sql.py`. New generator `add_field_spec_newrez_bps_rule.py` (idempotent; column-insert merge-safe — section headers A:J sit to the left; backup + per-(field,manual-header) O/P/Q value+comment equality guard with auto-restore); zh cards gain the rule row after `BPS 面板/功能`. **Full en horizontal-table column-ization deferred** (en is not card-ified; the rule's single source of truth is the Excel + zh cards) | doc 13 · doc 16 |
| 2026-06-04 | AI Agent (Claude Opus 4.8) | v37 | **Card-ified this en doc** (Sections 2.0–4.1) into per-field **English cards matching the zh layout**: vertical Attribute\|Value table (Newrez Raw Field · Data Type · Business Meaning · Format/Allowed Values · Typical Value · BPS Panel/Function · **Newrez → BPS Rule** · Newrez Status · Newrez/BPS Verify Result) + Newrez/BPS Verify SQL blocks, wrapped in `FS-CARDS` markers; all prose/sub-tables/footnotes preserved (allowed-values table, days360 note, Judgement mapping, 3.2 ETL-decode note, regulatory footnote). Also fixed the stale en field name `sms_days_in_fcl` → **`servicer_days_in_fcl`** (the v32/v19 rename had not reached the en spec row). New one-shot generator `sync_fieldspec_en_cards.py` (joins en English prose + Excel data + an authored English `RULE_EN` + a `ZH2EN` token map; aborts if already card-ified; CJK-clean). en business prose (meaning/format/BPS panel/status) stays hand-authored here (its source); verify SQL/results/rule come from the Excel | zh layout parity |
| 2026-06-04 | AI Agent (Claude Opus 4.8) | v38 | **BPS验证SQL SELECT now returns the data date** — first column `'2026-06-01' AS data_date`, so running the query self-documents the snapshot (matches the `数据日 2026-06-01` header). ⚠️ Found the BPS sync tables are **overwrite-refreshed** (`fctrdt`=latest ETL refresh date; the 2026-06-01 state was overwritten by the 06-02 refresh and is not reproducible — 198 of 569 rows now stamped 2026-06-02), so we do **not** filter by `fctrdt` (filtering yields a wrong subset, 141≠207); we use a literal reference date + full table (≈col S measurement). Changed `add_field_spec_bps_verify_sql.py` build_sql; col S unchanged (already date-labeled). Also made `sync_fieldspec_en_cards.py` **re-runnable** (on an already-card-ified doc it parses English prose from the cards + refreshes Excel-sourced data) and used it to refresh each en card's BPS Verify SQL block | prod read-only 2026-06-04 |
| 2026-06-02 | AI Agent (Claude Sonnet 4.6) | v17 | Source-table corrections (information_schema verified): ① `delinquency_status` source annotated as `portnewrezgeneral` (not portnewrezfc); ② `foreclosure_flag` removed the false "`portnewrezfc.fcl_flag` exists" claim — Newrez has no such column; FCL active status is actually `activefcflag`; ③ `state` source corrected to `portnewrezprop.propertystate` (portnewrezfc has no state column); also fixed 14_servicer_fcl_field_spec.xlsx Field Spec col4/verify-SQL (incl. lm_flag→portnewrezlm, lien_position→portnewrezgeneral.lienposition); zh/en synced | DB verified 2026-06-02 |
| 2026-06-02 | AI Agent (Claude Sonnet 4.6) | v18 | Section 2.0 added a `days360(nextduedate, dataasof)` calculation footnote (30/360 day-count formula, argument order, DPD meaning, C/D30/D60/D90/D120P bucketing, source [`PrefectFlow/flow/remit_validation/utils.py:14-21`](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/remit_validation/utils.py#L14-21)); Excel synced with a cell comment + a days360 glossary entry; zh/en synced | source-verified in PrefectFlow |
| 2026-06-02 | AI Agent (Claude Sonnet 4.6) | v19 | Section 4.1 — the 3 `⚠️ Code behavior under investigation` BK fields resolved via DB verification: ① `bk_status` is decoded to text by BPS (1→Active·2→Discharged·3→Dismissed·4→Closed·5→ReliefGranted); ② `bk_legal_status` actually comes from `portnewrezgeneral.legalstatus` text (FCBU/BK13/BK7…), `bkstage` was a misattribution; ③ `mfr_hearing_results` — BPS mfr_status empty in dev (0/64). Disproves the earlier "BK integer codes not decoded / BPS stores numbers" assumption; Excel + doc 13 Q7/Section 6 + data dictionary corrected too | DB-verified 2026-06-02 |
| 2026-06-02 | AI Agent (Claude Sonnet 4.6) | v20 | Corrected `lm_flag` Newrez status: DB shows `activelmflag` 100% filled at latest snapshot (5052/5052, 0:5018·1:34, no nulls) — the prior "🟡 Partially provided (no type/dates)" was wrong (flag is fully provided → ✅; type/dates are separate fields lm_type/lm_start_date/lm_end_date). Synced to Excel + MD; added a "doc 14 MD⇄Excel sync" rule to project CLAUDE.md. (zh counterpart = zh v21) | DB-verified 2026-06-02 |
| 2026-06-02 | AI Agent (Claude Opus 4.8) | v18 | Added "📖 Regulatory terms" footnote after the Section 3 LM business-meaning table: explains CFPB / Reg X / RESPA / 12 CFR 1024.40 (SPOC) / 1024.41 / Imminent Default; full entries also added to doc 10 "Category H — Regulatory/Compliance Terms"; zh/en synced | doc 10 v3 |
| 2026-06-04 | AI Agent (Claude Opus 4.8) | v21 | Corrected `active_fcl_flag` 格式/计算规则 (Field Spec Excel `格式/计算规则` column) — it still said "0=completed / 1=in progress", contradicting the v18/v20 meaning fix (0 ≠ completed). Rewritten as a full conditional (if activefcflag=1 then 1; if =0 then 0 = not in active foreclosure, BPS "Closed Foreclosure"; NULL→1); synced to zh card. Part of the doc 13/14/16 sweep that corrected the Foreclosure Status mapping rule (`activefcflag=1`→fixed text `'Active Foreclosure'`, not `fcstage`; `fcstage`→`summary_current_step`) per code ([basic_data_pool_config.py:273](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L273)) + DB | DB/code · doc 13 v35 · doc 16 v3 |

## Dependencies

| Resource | Description |
|----------|-------------|
| doc 09 | Industry-standard field spec (CFPB/MBA, 29 fields); P0/P1/P2 priority definitions are consistent with this document |
| doc 13 | Newrez field reverse mapping (MCP-verified, 2026-05); fill rates and data quality issues (Q1–Q11) are derived from this document |
| doc 12 | ETL pipeline and intermediate table details (not expanded in this document) |
| `basic_data_pool_config.py` | ETL field mapping source code (Redshift intermediate table → BPS MySQL) |

## Known Limitations

- Newrez fill rate data is based on MCP live measurements (2026-05-24, ~13,321 active FCL loans); may change over time
- BK panel `bkstatus`/`bkstage` numeric code decode behavior not fully confirmed (see doc 13 Q7)
- Compliance status for other Servicers requires separate measurement; this document uses Newrez as the reference benchmark

## Related Documents

| Document | Description |
|----------|-------------|
| doc 08 | Newrez field mapping status (overall view) |
| doc 09 | Industry-standard field specification (upstream standard for this document) |
| doc 10 | ForeclosureRule2 comprehensive glossary |
| doc 13 | Newrez BPS display field reverse mapping (source of this document's data) |

---

## Section 1: Overall Architecture and Design Principles

### 1.1 BPS Five-Panel Field Requirement Distribution

| BPS Panel | Page Type | Servicer Source Table | Primary Field Groups |
|---|---|---|---|
| FCL Milestone Timeline | Loan detail page | `portnewrezfc` | `timeline_*` (19 date fields) |
| FCL Summary | Loan detail page | `portnewrezfc` | `summary_*` (16 status fields) |
| Hold Records History | Loan detail page | `portnewrezfc` | Hold slots 3×4 fields |
| Loss Mitigation Cycle | Loan detail page | `portnewrezlm` | LM cycle fields (10 columns) |
| Bankruptcy | Loan detail page | `portnewrezbk` | BK fields (10+ columns) |
| Aggregate Stage Tab | Aggregate overview | `portnewrezfc` | Stage grouping + day statistics |
| Aggregate Time Line Tab | Aggregate overview | `portnewrezfc` | 7 milestone date columns (1–7) |

### 1.2 Priority Definitions

Consistent with doc 09:

| Priority | Meaning | Impact if Missing |
|----------|---------|------------------|
| **P0** | System entry prerequisite | Missing → entire loan record rejected from BPS |
| **P1** | Core panel display field | Missing → corresponding BPS panel shows anomalous data or blank (degraded-available) |
| **P2** | Enhanced analytics field | Optional; enables corresponding analysis when present; absence does not affect main workflow |

### 1.3 Three Newrez Source Tables and Their BPS Panel Mapping

```
Newrez Source Table                 → BPS Panel
portnewrezfc (FCL master)           → FCL Summary / Timeline / Stage Tab /
                                       Time Line Tab / Hold Panel / Bid Approval
portnewrezlm (LM table)             → Loss Mitigation Cycle panel
portnewrezbk (BK table)             → Bankruptcy panel
```

> **Note**: `portnewrezfc` is the core table, supplying the vast majority of BPS panels. LM and BK each map independently to their own dedicated panel.

### 1.4 This Document vs. Doc 09

| Dimension | Doc 09 (Industry Standard) | This Document (BPS Implementation Standard) |
|-----------|--------------------------|-------------------------------------------|
| Perspective | Derived from CFPB/MBA industry norms | Derived from BPS five-panel display requirements |
| Field count | 29 abstract fields in 7 groups | ~92 concrete fields (12 foundation state flags + 68 BPS display details + 12 Newrez enhancement fields) with Newrez raw field names |
| Priority | P0/P1/P2 (adopted by this document) | Same |
| BPS panel mapping | Not included | Every field explicitly tagged with the BPS panel it feeds |
| Newrez compliance status | Not included | Every field tagged with Newrez fill rate / compliance status |
| Use case | Industry access standard reference | Formal basis for Servicer field completion requests |

---

## Section 2: FCL Master Data Field Specification (Source: `portnewrezfc`)

> **Field specification table format**:
>
> | Standard Interface Field | Newrez Raw Field | Type | Priority | Format | BPS Panel / Function | Newrez Status |
>
> **Newrez Status column values**: `✅ Provided (fill%)` / `⚠️ Partially provided (fill%)` / `❌ Not provided (0%)` / `N/A Derived field`

### 2.0 Four-Dimension State Foundation Fields (Aligned with doc 09 Industry Standard)

> **Role of this section**: These are the high-level abstract fields from doc 09 Groups B/D/E/F/G — the **industry-standard minimum set** that every Servicer must provide. Sections 2.1–4.1 contain the BPS-specific detail fields needed for panel display. When issuing field completion requests to a new Servicer, **P0 fields in this section must be satisfied first**, before requesting panel detail fields.  
> **Relationship to Sections 2.1–4.1**: This section = "dimension flag layer" (tells the system which state dimension a loan is in); subsequent sections = "detail layer" (timelines, cycle records, amounts, etc.). The two layers are complementary, not overlapping.

<!-- FS-CARDS:2.0 START -->
##### `delinquency_status` · P0 · Four-Dimension State Foundation Fields

| Attribute | Value |
|---|---|
| Newrez Raw Field | `delinquency_status_mba` (from `portnewrezgeneral`) |
| Data Type | VARCHAR ENUM |
| Business Meaning | MBA standard delinquency status text enum; the core "Dimension A" field in the 4-dimension model; Servicers must use enum text (numeric DPD values forbidden); FCL status identification (`Foreclosure` enum), BK identification (`Bankruptcy` enum), and REO identification all depend on this field |
| Format / Allowed Values | MBA standard text enum (see allowed values table below) |
| Typical Value | Foreclosure |
| BPS Panel / Function | ETL entry filter; foundation for FCL/LM/BK status identification; `sync_fcl_stage_info` D120P secondary filter trigger; numeric strings (`'29.0'`) are prohibited |
| Newrez → BPS Rule | N/A — four-dimension status; not via BPS FCL sync tables |
| Newrez Status | ✅ `portnewrezgeneral.delinquency_status_mba` provided (12K+ FCL rows) |
| Newrez Verify Result | [data_date 2026-06-01] 1-29 DPD:2161 \| Current:2053 \| Full Payoff:678 \| 30-59 DPD:64 \| Foreclosure:30 \| 60-89 DPD:18 \| 90-119 DPD:10 \| 120-149 DPD:8 \| REO:5 \| Service Release:4 \| Performing Bankruptcy:4 \| Foreclosure / Non-Perf BK:3 \| 3rd Party Sale:3 \| Non-Performing Bankruptcy:3 \| Foreclosure / Perf BK:3 \| 180+ DPD:2 \| Settlement:1 \| REO Sale:1 \| 150-179 DPD:1 |
| BPS Verify Result | N/A — not mapped to a BPS FCL sync table (see Newrez → BPS Rule) |

Newrez Verify SQL:
```sql
-- Verify against mysql_dev, data date 2026-06-01
SELECT dataasof AS data_date, delinquency_status_mba AS val, COUNT(*) AS cnt
FROM   newrez.portnewrezgeneral
WHERE  dataasof = '2026-06-01'
  AND  delinquency_status_mba IS NOT NULL AND delinquency_status_mba != ''
GROUP  BY dataasof, delinquency_status_mba ORDER BY cnt DESC LIMIT 30;
```

##### `next_payment_due_date` · P0 · Four-Dimension State Foundation Fields

| Attribute | Value |
|---|---|
| Newrez Raw Field | `nextduedate` (from `portnewrezpmt`) |
| Data Type | DATE |
| Business Meaning | Next payment due date; source: `newrez.portnewrezpmt.nextduedate` (DATE, 100% fill rate for active FCL loans); ETL calculates DPD via `days360(nextduedate, dataasof)`; primary fallback source when `delinquency_status` is missing or malformed |
| Format / Allowed Values | YYYY-MM-DD |
| Typical Value | 2024-03-01 |
| BPS Panel / Function | Fallback basis for days360 calculation; ETL derives DPD via `days360(nextduedate, dataasof)` |
| Newrez → BPS Rule | N/A — not in BPS FCL sync tables |
| Newrez Status | ✅ `portnewrezpmt.nextduedate` provided; **100% fill rate** for active FCL loans (MCP-verified) |
| Newrez Verify Result | [data_date 2026-06-01] 2026-06-01 \| 2026-06-01 \| 2026-07-01 \| 2025-10-01 \| 2024-07-01 \| 2026-07-01 \| 2026-06-01 \| 2026-06-01 \| 2026-07-01 \| 2025-11-01 (10 rows) |
| BPS Verify Result | N/A — not mapped to a BPS FCL sync table (see Newrez → BPS Rule) |

Newrez Verify SQL:
```sql
-- Verify against mysql_dev, data date 2026-06-01
SELECT loanid, dataasof, nextduedate
FROM   newrez.portnewrezpmt
WHERE  dataasof = '2026-06-01'
  AND  nextduedate IS NOT NULL
LIMIT  10;
```

##### `days_past_due` · P1 · Four-Dimension State Foundation Fields

| Attribute | Value |
|---|---|
| Newrez Raw Field | *(none; ETL-derived)* |
| Data Type | INTEGER |
| Business Meaning | Numeric days past due; Newrez has **no native DPD days field** — ETL calculates via `days360(nextduedate, dataasof)`; `portnewrezgeneral.mbadelinquency` stores **months** past due (integer, e.g., 13 = 13 months delinquent), which cannot be used directly as DPD days; cross-validates `delinquency_status` and serves as substitute when format errors occur |
| Format / Allowed Values | 0–999 positive integer |
| Typical Value | 215 |
| BPS Panel / Function | Cross-validates `delinquency_status`; ETL calculates via `days360(nextduedate, dataasof)`; Newrez has `portnewrezgeneral.mbadelinquency` (**months** past due, not days, integer) for reference |
| Newrez → BPS Rule | N/A — ETL-derived days360(nextduedate,dataasof); not in BPS FCL sync tables |
| Newrez Status | N/A Derived field (Newrez has no native DPD days field; `mbadelinquency` = months past due, cannot be used directly as DPD days) |
| Newrez Verify Result | [data_date 2026-06-01] 2026-06-01 \| 2026-06-01 \| 2026-07-01 \| 2025-10-01 \| 2024-07-01 \| 2026-07-01 \| 2026-06-01 \| 2026-06-01 \| 2026-07-01 \| 2025-11-01 (10 rows) |
| BPS Verify Result | N/A — not mapped to a BPS FCL sync table (see Newrez → BPS Rule) |

Newrez Verify SQL:
```sql
-- Verify against mysql_dev, data date 2026-06-01
SELECT loanid, dataasof, nextduedate
FROM   newrez.portnewrezpmt
WHERE  dataasof = '2026-06-01'
  AND  nextduedate IS NOT NULL
LIMIT  10;
```

##### `foreclosure_flag` · P0 · Four-Dimension State Foundation Fields

| Attribute | Value |
|---|---|
| Newrez Raw Field | *(no `fcl_flag` in Newrez; see `activefcflag`)* |
| Data Type | CHAR(1) |
| Business Meaning | Explicit Y/N flag whether FCL legal proceedings have formally commenced; **must never be derived from `days_past_due`** (120+ DPD ≠ foreclosure; FCL requires an explicit flag from Servicer); corresponds to BPS `active_fcl_flag` (0=N / 1=Y) |
| Format / Allowed Values | `Y` / `N` |
| Typical Value | Y |
| BPS Panel / Function | Explicit FCL active status flag; corresponds to BPS `active_fcl_flag` (0/1 Newrez-specific); `Y` = foreclosure legal proceedings formally initiated |
| Newrez → BPS Rule | N/A — no fcl_flag; FCL activeness via active_fcl_flag→summary_completed_foreclosure |
| Newrez Status | ❌ Newrez has **no standalone `fcl_flag` column** (DB-verified; no portnewrez* table contains it); FCL active status is expressed by `portnewrezfc.activefcflag` (see `active_fcl_flag`) or derived from `delinquency_status='Foreclosure'` |
| Newrez Verify Result | [data_date 2026-06-01] 0:5016 \| 1:36 |
| BPS Verify Result | N/A — not mapped to a BPS FCL sync table (see Newrez → BPS Rule) |

Newrez Verify SQL:
```sql
-- Verify against mysql_dev, data date 2026-06-01
SELECT dataasof AS data_date, activefcflag, COUNT(*) AS cnt
FROM   newrez.portnewrezfc
WHERE  dataasof = '2026-06-01'
GROUP  BY dataasof, activefcflag ORDER BY cnt DESC;
```

##### `lm_flag` · P0 · Four-Dimension State Foundation Fields

| Attribute | Value |
|---|---|
| Newrez Raw Field | `activelmflag` |
| Data Type | CHAR(1) |
| Business Meaning | Top-level Y/N flag whether LM program is currently active; determines whether ETL reads LM detail fields; independent of FCL dimension (can coexist with FCL) |
| Format / Allowed Values | `Y` / `N` |
| Typical Value | Y |
| BPS Panel / Function | Top-level LM active flag; ETL uses this to route loans into LM processing; basis for BPS LM Cycle panel data sourcing |
| Newrez → BPS Rule | N/A — no standalone flag; LM existence = rows in the loss_mitigation table |
| Newrez Status | ✅ Provided (`activelmflag`, 100% filled at latest snapshot: 0/1, no nulls; observed 0:5018·1:34). Expressed as 0/1 (map to Y/N); cycle-table-level flag — LM type/dates are separate fields (`lm_type` / `lm_start_date` / `lm_end_date`) |
| Newrez Verify Result | [data_date 2026-06-01] 0:5019 \| 1:33 |
| BPS Verify Result | N/A — not mapped to a BPS FCL sync table (see Newrez → BPS Rule) |

Newrez Verify SQL:
```sql
-- Verify against mysql_dev, data date 2026-06-01
SELECT dataasof AS data_date, activelmflag, COUNT(*) AS cnt
FROM   newrez.portnewrezlm
WHERE  dataasof = '2026-06-01'
GROUP  BY dataasof, activelmflag ORDER BY cnt DESC;
```

##### `lm_type` · P1 · Four-Dimension State Foundation Fields

| Attribute | Value |
|---|---|
| Newrez Raw Field | *(no field)* |
| Data Type | VARCHAR ENUM |
| Business Meaning | Standard LM type enum; affects system processing logic (Forbearance = temporary, Modification = permanent); Newrez supplies via `lmdeal` numeric code requiring ETL decode mapping |
| Format / Allowed Values | Newrez `lmdeal`-decoded deal (8): `Evaluation` / `Modification` / `Forbearance` / `Payment Plan` / `Deferment` / `Short Sale` / `DIL` / `Payoff` (= `lm_deal`; Trial Period Plan is a program-level value under Modification, not a deal) |
| Typical Value | Modification |
| BPS Panel / Function | Standardized LM type; same concept as `lm_deal` (Newrez `lmdeal`-decoded) |
| Newrez → BPS Rule | Integer code lmdeal decoded to text via portnewrezdatadic (e.g. 7→DIL) → deal |
| Newrez Status | ❌ Newrez provides no standard `lm_type` text; supplied as `lmdeal` int code, ETL-decoded to the 8 deals above (see `lm_deal`) |
| Newrez Verify Result | 1 Modification:194 \| 1 Evaluation:2 \| 2 Evaluation:104 \| 4 Payment Plan:37 \| 5 Forbearance:51 \| 6 Short Sale:9 \| 7 DIL:10 \| 9 Payoff:1 \| 11 Deferment:50 |
| BPS Verify Result | [BPS prod \| data date fctrdt≤2026-06-01 \| ETL load 2026-06-03] Modification:207 \| Evaluation:115 \| ∅NULL:72 \| Forbearance:57 \| Deferment:56 \| Payment Plan:39 \| Short Sale:12 \| DIL:10 \| Payoff:1 |

Newrez Verify SQL:
```sql
-- Verify against mysql_dev, data date 2026-06-01
WITH latest_lm AS (
  SELECT loanid, dealstartdate, lmdeal,
         ROW_NUMBER() OVER (PARTITION BY loanid, dealstartdate ORDER BY dataasof DESC) AS rn
  FROM newrez.portnewrezlm WHERE lmdeal IS NOT NULL AND dataasof <= '2026-06-01'
)
SELECT l.lmdeal, b.deal, COUNT(*) AS cnt
FROM   latest_lm l
JOIN   bpms_dev.sync_loan_foreclosure_loss_mitigation b
  ON   l.loanid = b.loanid AND l.dealstartdate = b.cycle_opened_date
WHERE  l.rn = 1
  AND  b.deal IS NOT NULL AND b.deal != '' AND b.deal NOT REGEXP '^[0-9]'
GROUP  BY l.lmdeal, b.deal ORDER BY l.lmdeal, cnt DESC;
```

BPS Verify SQL (prod, read-only):
```sql
-- Verify against prod bpms (read-only)
SELECT '2026-06-01' AS data_date, `deal` AS val, COUNT(*) AS cnt
FROM   bpms.sync_loan_foreclosure_loss_mitigation
GROUP  BY `deal` ORDER BY cnt DESC;
```

##### `lm_start_date` · P1 · Four-Dimension State Foundation Fields

| Attribute | Value |
|---|---|
| Newrez Raw Field | `dealstartdate` |
| Data Type | DATE |
| Business Meaning | LM program start date (top-level summary); Newrez provides via LM cycle table (`portnewrezlm`) as `dealstartdate` |
| Format / Allowed Values | YYYY-MM-DD |
| Typical Value | 2024-01-15 |
| BPS Panel / Function | LM program start date; corresponds to Section 3.1 `lm_cycle_open_date` |
| Newrez → BPS Rule | Direct copy (dealstartdate → cycle_opened_date) |
| Newrez Status | 🟡 Cycle-level `dealstartdate` available |
| Newrez Verify Result | [data_date 2026-06-01] 2025-09-18 \| 2026-04-28 \| 2026-03-06 \| 2025-07-18 \| 2025-05-23 \| 2025-09-19 \| 2025-11-05 \| 2025-12-10 \| 2026-02-25 \| 2026-03-31 (10 rows) |
| BPS Verify Result | [BPS prod \| data date fctrdt≤2026-06-01 \| ETL load 2026-06-03] non-null 568/569 \| range 2020-08-17~2026-06-01 |

Newrez Verify SQL:
```sql
-- Verify against mysql_dev, data date 2026-06-01
SELECT loanid, dataasof, dealstartdate
FROM   newrez.portnewrezlm
WHERE  dataasof = '2026-06-01'
  AND  dealstartdate IS NOT NULL
LIMIT  10;
```

BPS Verify SQL (prod, read-only):
```sql
-- Verify against prod bpms (read-only)
SELECT '2026-06-01' AS data_date, COUNT(*) AS total, COUNT(`cycle_opened_date`) AS non_null,
       MIN(`cycle_opened_date`) AS min_dt, MAX(`cycle_opened_date`) AS max_dt
FROM   bpms.sync_loan_foreclosure_loss_mitigation;
```

##### `lm_end_date` · P1 · Four-Dimension State Foundation Fields

| Attribute | Value |
|---|---|
| Newrez Raw Field | `lmremovaldate` |
| Data Type | DATE |
| Business Meaning | LM program expiration date (top-level summary); Newrez provides via LM cycle table as `lmremovaldate`; whether it's renewed at expiry is a critical decision point |
| Format / Allowed Values | YYYY-MM-DD |
| Typical Value | 2024-06-30 |
| BPS Panel / Function | LM program expiration date; corresponds to Section 3.1 `lm_cycle_close_date` |
| Newrez → BPS Rule | Direct copy (lmremovaldate → cycle_closed_date; NULL=open) |
| Newrez Status | 🟡 Cycle-level `lmremovaldate` available |
| Newrez Verify Result | [data_date 2026-06-01] 2025-11-07 \| 2026-05-03 \| 2026-05-08 \| 2026-05-20 \| 2025-12-03 \| 2026-05-07 \| 2026-05-01 \| 2025-09-08 \| 2025-05-27 \| 2025-09-29 (10 rows) |
| BPS Verify Result | [BPS prod \| data date fctrdt≤2026-06-01 \| ETL load 2026-06-03] non-null 511/569 \| range 2020-09-22~2026-06-01 |

Newrez Verify SQL:
```sql
-- Verify against mysql_dev, data date 2026-06-01
SELECT loanid, dataasof, lmremovaldate
FROM   newrez.portnewrezlm
WHERE  dataasof = '2026-06-01'
  AND  lmremovaldate IS NOT NULL
LIMIT  10;
```

BPS Verify SQL (prod, read-only):
```sql
-- Verify against prod bpms (read-only)
SELECT '2026-06-01' AS data_date, COUNT(*) AS total, COUNT(`cycle_closed_date`) AS non_null,
       MIN(`cycle_closed_date`) AS min_dt, MAX(`cycle_closed_date`) AS max_dt
FROM   bpms.sync_loan_foreclosure_loss_mitigation;
```

##### `hold_flag` · P1 · Four-Dimension State Foundation Fields

| Attribute | Value |
|---|---|
| Newrez Raw Field | *(no top-level field)* |
| Data Type | CHAR(1) |
| Business Meaning | Top-level flag whether FCL is paused (Hold); derivable from Newrez `fchold1startdate IS NOT NULL`, but not a formal flag; Servicers should be explicitly asked for a dedicated flag |
| Format / Allowed Values | `Y` / `N` |
| Typical Value | Y |
| BPS Panel / Function | Top-level flag for whether FCL is in Hold (paused) status; corresponds to the Section 2.4 slot fields |
| Newrez → BPS Rule | N/A — no standalone flag; Hold existence = rows in the hold table |
| Newrez Status | ❌ No independent top-level flag (`fchold1startdate IS NOT NULL` can be derived, but not a formal flag) |
| Newrez Verify Result | [data_date 2026-06-01] hold_loans=89 |
| BPS Verify Result | N/A — not mapped to a BPS FCL sync table (see Newrez → BPS Rule) |

Newrez Verify SQL:
```sql
-- Verify against mysql_dev, data date 2026-06-01
SELECT '2026-06-01' AS data_date, COUNT(*) AS hold_loans
FROM   newrez.portnewrezfc
WHERE  dataasof = '2026-06-01'
  AND  fchold1startdate IS NOT NULL;
```

##### `hold_reason` · P1 · Four-Dimension State Foundation Fields

| Attribute | Value |
|---|---|
| Newrez Raw Field | `fchold1description` |
| Data Type | VARCHAR ENUM |
| Business Meaning | Standardized hold reason enum (`BK`/`LM`/`HUD`/`Covid`/`Other`); Newrez provides free text (e.g., "Loss Mitigation Workout"), not standardized |
| Format / Allowed Values | `BK`/`LM`/`HUD`/`Covid`/`Other` |
| Typical Value | BK |
| BPS Panel / Function | Standardized hold reason enum; Section 2.4 `hold_1_description` is its free-text version |
| Newrez → BPS Rule | 3 slots fchold1/2/3description UNPIVOT-merged → description |
| Newrez Status | ❌ Newrez provides free text (e.g., "Court Delay"), no standard enum |
| Newrez Verify Result | [data_date 2026-06-01] Loss Mitigation Workout:21 \| Awaiting Funds to Post:16 \| Delinquency Review:12 \| Bankruptcy Filed:6 \| Hearing Set:4 \| Court Delay:4 \| Client Document Execution:4 \| Service Delay:4 \| Note Possession Confirmation:3 \| Title Resolution:3 \| Original Note:2 \| Allonge of Note:1 \| Service By Publication:1 \| Guaranty Agreement:1 \| Demand Letter Review:1 \| Awaiting Escrow Analysis:1 \| Moratorium:1 \| Mediation Hearing:1 \| FC Payment Research/Dispute:1 \| ACT(PA) Letter/Demand Letter/NOI Expiration:1 \| Original Assignment:1 |
| BPS Verify Result | [BPS prod \| data date fctrdt≤2026-06-01 \| ETL load 2026-06-03] Loss Mitigation Workout:63 \| Service Delay:48 \| ∅NULL:44 \| Client Document Execution:29 \| Court Delay:23 \| Awaiting Funds to Post:20 \| ACT(PA) Letter/Demand Letter/NOI Expiration:18 \| Hearing Set:17 \| Mediation Hearing:13 \| Delinquency Review:11 \| Original Note:10 \| Title Resolution:9 \| Note Possession Confirmation:8 \| Bankruptcy Filed:8 \| Copy of Power of Attorney:7 \| Copy of Payment History:5 \| Original Assignment:5 \| Demand Letter Review:4 \| Service By Publication:4 \| Copy of Periodic Statement:4 \| Pending Prior Servicer Doc(s):2 \| Awaiting Escrow Analysis:2 \| Soldiers and Sailors Relief Act:2 \| Allonge of Note:2 \| FC Payment Research/Dispute:2 \| +15 values, 1 row each:15 |

Newrez Verify SQL:
```sql
-- Verify against mysql_dev, data date 2026-06-01
SELECT dataasof AS data_date, fchold1description AS val, COUNT(*) AS cnt
FROM   newrez.portnewrezfc
WHERE  dataasof = '2026-06-01'
  AND  fchold1description IS NOT NULL AND fchold1description != ''
GROUP  BY dataasof, fchold1description ORDER BY cnt DESC LIMIT 30;
```

BPS Verify SQL (prod, read-only):
```sql
-- Verify against prod bpms (read-only)
SELECT '2026-06-01' AS data_date, `description` AS val, COUNT(*) AS cnt
FROM   bpms.sync_loan_foreclosure_hold
GROUP  BY `description` ORDER BY cnt DESC;
```

##### `reo_flag` · P0 · Four-Dimension State Foundation Fields

| Attribute | Value |
|---|---|
| Newrez Raw Field | *(no field)* |
| Data Type | CHAR(1) |
| Business Meaning | Explicit flag that foreclosure is complete and property is lender-owned; Newrez currently lacks a dedicated REO flag; must be derived from `fcresults` or `delinquency_status='REO'` |
| Format / Allowed Values | `Y` / `N` |
| Typical Value | Y |
| BPS Panel / Function | Explicit flag that foreclosure is complete and property now owned by lender |
| Newrez → BPS Rule | N/A — no standalone REO flag (can be inferred from fcresults) |
| Newrez Status | ❌ Not provided |
| Newrez Verify Result | [data_date 2026-06-01] REO:6 |
| BPS Verify Result | N/A — not mapped to a BPS FCL sync table (see Newrez → BPS Rule) |

Newrez Verify SQL:
```sql
-- Verify against mysql_dev, data date 2026-06-01
SELECT dataasof AS data_date, fcresults, COUNT(*) AS cnt
FROM   newrez.portnewrezfc
WHERE  dataasof = '2026-06-01'
  AND  fcresults IN ('REO','REO Sale')
GROUP  BY dataasof, fcresults;
```

##### `reo_acquisition_date` · P1 · Four-Dimension State Foundation Fields

| Attribute | Value |
|---|---|
| Newrez Raw Field | *(no field)* |
| Data Type | DATE |
| Business Meaning | Date property was transferred to lender as REO; affects REO holding period calculation; Newrez does not provide |
| Format / Allowed Values | YYYY-MM-DD |
| Typical Value | 2024-05-01 |
| BPS Panel / Function | Date property was formally transferred to lender as REO |
| Newrez → BPS Rule | N/A — no standalone REO acquisition date (see dtdeedrecorded) |
| Newrez Status | ❌ Not provided |
| Newrez Verify Result | [data_date 2026-06-01] 2026-04-28 \| 2026-05-22 \| 2025-10-28 \| 2025-11-12 (4 rows) |
| BPS Verify Result | N/A — not mapped to a BPS FCL sync table (see Newrez → BPS Rule) |

Newrez Verify SQL:
```sql
-- Verify against mysql_dev, data date 2026-06-01
SELECT loanid, dataasof, dtdeedrecorded
FROM   newrez.portnewrezfc
WHERE  dataasof = '2026-06-01'
  AND  dtdeedrecorded IS NOT NULL
LIMIT  10;
```

<!-- FS-CARDS:2.0 END -->



> **`delinquency_status` Allowed Values (MBA Standard, from doc 09 Group B)**:
>
> | Allowed Value | Internal Code | Notes |
> |---|---|---|
> | `Current` | `C` | 0–29 DPD, paying on time |
> | `1-29 DPD` | `C` | Fine-grained variant (used by Newrez etc.) |
> | `30-59 DPD` | `D30` | — |
> | `60-89 DPD` | `D60` | — |
> | `90-119 DPD` | `D90` | — |
> | `120-149 DPD` | `D120P` | — |
> | `150-179 DPD` | `D120P` | — |
> | `180+ DPD` | `D120P` | — |
> | `Foreclosure` | `FCL` | FCL legal proceedings initiated |
> | `Foreclosure / Non-Perf BK` | `FCL` (+ `bankruptcy='Y'`) | Foreclosure + non-performing bankruptcy (Newrez extension; present in DB) |
> | `Foreclosure / Perf BK` | `FCL` (+ `bankruptcy='Y'`) | Foreclosure + performing bankruptcy (Newrez extension; present in DB) |
> | `REO` | `REO` | Foreclosure complete; property lender-owned |
> | `Bankruptcy` / `Performing Bankruptcy` / `Non-Performing Bankruptcy` | By DPD + `bankruptcy_flag='Y'` | Bankruptcy must also be transmitted via `bankruptcy_flag` / `active_bk_flag` |
> | `PaidOff` / `Full Payoff` / `Paid in Full` | `P` | Loan paid off |
> | `REO Sale` / `3rd Party Sale` | `P` | Disposition complete |
> | `Service Release` | Special handling | Loan servicing transferred (loan leaves this servicer) |
> | `Settlement` | Special handling | Settled/closed (very rare; present in DB) |
>
> ⚠️ **Prohibited formats**: `'29.0'`, `'30.0'`, `'90.0'` numeric strings (CapeCodFive currently violates this, causing FCL to never be identified)
>
> Note: This table lists all 19 MBA standard transmission values, fully consistent with doc 08 "MBA Standard Delinquency: Full Raw Value Range" and DB verification (`newrez.portnewrezgeneral.delinquency_status_mba`, 2026-06-01).

> **`days360(nextduedate, dataasof)` calculation note** (referenced by the `days_past_due` / `next_payment_due_date` rows):
>
> `days360` is the **30/360 day-count convention** — it counts days between two dates treating every month as 30 days and every year as 360 days:
>
> ```
> days360(start, end) = (end.yr − start.yr)×360 + (end.mo − start.mo)×30 + (end.day − start.day)
> ```
>
> - **Argument order**: `start = nextduedate` (next payment due date), `end = dataasof` (data snapshot date).
> - **Meaning**: days from the due date to the snapshot date = **DPD (days past due)**; positive when the loan is overdue.
> - **ETL bucketing** (produces the `delinquency_status` internal code): `<30 → C`, `<60 → D30`, `<90 → D60`, `<120 → D90`, `≥120 → D120P` (note: `days360` never yields `FCL` — foreclosure requires an explicit servicer flag).
> - **Example**: `nextduedate=2024-01-01`, `dataasof=2024-04-01` → `days360=90` → `D90`.
> - **Source**: [`PrefectFlow/flow/remit_validation/utils.py:14-21`](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/remit_validation/utils.py#L14-21) (Python definition); SQL usage in `basic_data_pool_config.py`. Full glossary entry in **doc 10**.

---

### 2.1 Loan Identification and Entry Filter Fields (P0 — Required)

These fields are **prerequisites for BPS entry**; absence of any one will cause the entire loan record to be rejected.

<!-- FS-CARDS:2.1 START -->
##### `loan_id` · P0 · Loan Identification and Entry Filter Fields

| Attribute | Value |
|---|---|
| Newrez Raw Field | `loanid` |
| Data Type | VARCHAR |
| Business Meaning | Globally unique numeric loan identifier; serves as the JOIN key across all BPS panels and tables |
| Format / Allowed Values | Numeric string; global primary key |
| Typical Value | 7727000088 |
| BPS Panel / Function | All panels; BPS global JOIN key |
| Newrez → BPS Rule | Direct copy (loanid) |
| Newrez Status | ✅ 100% |
| Newrez Verify Result | 700082700000027 \| 700082700000004 \| 700082700000014 \| 700082700000016 \| 700082700000003 \| 700082700000011 \| 700082880000126 \| 700082700000026 \| 700082700000005 \| 700082700000013 (10 rows) |
| BPS Verify Result | [BPS prod \| data date 2026-06-01(main table has no embedded as-of, same ETL cycle as Newrez source) \| ETL load 2026-06-03] sample (first 5): 7727000012 \| 7727000065 \| 7727000082 \| 7727000088 \| 7727000119 |

Newrez Verify SQL:
```sql
-- Verify against mysql_dev, data date 2026-06-01
SELECT loanid, dataasof
FROM   newrez.portnewrezfc
WHERE  dataasof = '2026-06-01'
  AND  loanid IS NOT NULL AND loanid != ''
LIMIT  10;
```

BPS Verify SQL (prod, read-only):
```sql
-- Verify against prod bpms (read-only)
SELECT '2026-06-01' AS data_date, `loanid`
FROM   bpms.sync_loan_foreclosure
WHERE  `loanid` IS NOT NULL AND `loanid` != ''
LIMIT  5;
```

##### `servicer_loan_id` · P0 · Loan Identification and Entry Filter Fields

| Attribute | Value |
|---|---|
| Newrez Raw Field | `shellpointloanid` |
| Data Type | VARCHAR |
| Business Meaning | Servicer's internal loan number; a different dimension from loan_id; used for bidirectional cross-system reconciliation |
| Format / Allowed Values | Servicer internal number |
| Typical Value | NR-2024-001234 |
| BPS Panel / Function | FCL Summary `summary_servicer_number` |
| Newrez → BPS Rule | Direct copy (shellpointloanid → summary_servicer_number) |
| Newrez Status | ✅ 100% |
| Newrez Verify Result | [data_date 2026-06-01] 9799754446 \| 9798424553 \| 9796670868 \| 9796285410 \| 9792903412 \| 9787544114 \| 9779201442 \| 9776836927 \| 9776762263 \| 9770660612 (10 rows) |
| BPS Verify Result | [BPS prod \| data date 2026-06-01(main table has no embedded as-of, same ETL cycle as Newrez source) \| ETL load 2026-06-03] all NULL (prod not populated) |

Newrez Verify SQL:
```sql
-- Verify against mysql_dev, data date 2026-06-01
SELECT loanid, dataasof, shellpointloanid
FROM   newrez.portnewrezfc
WHERE  dataasof = '2026-06-01'
  AND  shellpointloanid IS NOT NULL AND shellpointloanid != ''
LIMIT  10;
```

BPS Verify SQL (prod, read-only):
```sql
-- Verify against prod bpms (read-only)
SELECT '2026-06-01' AS data_date, `summary_servicer_number`
FROM   bpms.sync_loan_foreclosure
WHERE  `summary_servicer_number` IS NOT NULL AND `summary_servicer_number` != ''
LIMIT  5;
```

##### `data_as_of_date` · P0 · Loan Identification and Entry Filter Fields

| Attribute | Value |
|---|---|
| Newrez Raw Field | `dataasof` |
| Data Type | DATE |
| Business Meaning | Snapshot cutoff date for this data batch (typically 1–2 days behind real time); BPS real-time correction formula: `smsdaysinfc + DATEDIFF(today NY, dataasof)` |
| Format / Allowed Values | YYYY-MM-DD |
| Typical Value | 2026-05-27 |
| BPS Panel / Function | Snapshot date; basis for real-time day recalculation (SMS/Days in FCL) |
| Newrez → BPS Rule | N/A — main table has no dataasof column (overwrite snapshot) |
| Newrez Status | ✅ 100% |
| Newrez Verify Result | 700082700000027 \| 700082700000004 \| 700082700000014 \| 700082700000016 \| 700082700000003 \| 700082700000011 \| 700082880000126 \| 700082700000026 \| 700082700000005 \| 700082700000013 (10 rows) |
| BPS Verify Result | N/A — not mapped to a BPS FCL sync table (see Newrez → BPS Rule) |

Newrez Verify SQL:
```sql
-- Verify against mysql_dev, data date 2026-06-01
SELECT loanid, dataasof, dataasof
FROM   newrez.portnewrezfc
WHERE  dataasof = '2026-06-01'
  AND  dataasof IS NOT NULL
LIMIT  10;
```

##### `state` · P0 · Loan Identification and Entry Filter Fields

| Attribute | Value |
|---|---|
| Newrez Raw Field | `propertystate` (from `portnewrezprop`) |
| Data Type | CHAR(2) |
| Business Meaning | Two-letter uppercase state code where the property is located; determines applicable foreclosure law (Judicial/Non-Judicial) and BPS target day configurations per stage |
| Format / Allowed Values | US state code (uppercase) |
| Typical Value | FL |
| BPS Panel / Function | Stage grouping; target days configuration |
| Newrez → BPS Rule | Direct copy (propertystate → sync_fcl_stage_info.state) |
| Newrez Status | ✅ 100% (`portnewrezprop.propertystate`, DB-verified) |
| Newrez Verify Result | [data_date 2026-06-01] CA:794 \| FL:617 \| TX:395 \| IL:331 \| OH:257 \| NY:210 \| AZ:181 \| NJ:167 \| PA:167 \| GA:159 \| NC:158 \| MN:137 \| MI:107 \| CO:101 \| TN:99 \| VA:97 \| MD:86 \| MO:84 \| WA:79 \| MA:77 \| NV:75 \| OR:65 \| CT:65 \| SC:65 \| UT:53 \| IN:47 \| AL:46 \| RI:38 \| HI:29 \| AR:27 |
| BPS Verify Result | [BPS prod \| data date fctrdt=2026-06-01 \| ETL load 2026-06-03] FL:1510 \| NY:1225 \| IL:1075 \| CA:983 \| AZ:669 \| IN:332 \| TX:324 \| CO:296 \| PA:288 \| WA:262 \| OR:221 \| MT:179 \| MD:149 \| NC:123 \| OH:118 \| MN:78 \| MI:77 \| NJ:74 \| SC:70 \| MA:68 \| RI:55 \| TN:47 \| GA:40 \| +other states:0 |

Newrez Verify SQL:
```sql
-- Verify against mysql_dev, data date 2026-06-01
SELECT dataasof AS data_date, propertystate AS val, COUNT(*) AS cnt
FROM   newrez.portnewrezprop
WHERE  dataasof = '2026-06-01'
  AND  propertystate IS NOT NULL AND propertystate != ''
GROUP  BY dataasof, propertystate ORDER BY cnt DESC LIMIT 30;
```

BPS Verify SQL (prod, read-only):
```sql
-- Verify against prod bpms (read-only)
SELECT '2026-06-01' AS data_date, `state` AS val, COUNT(*) AS cnt
FROM   bpms.sync_fcl_stage_info
GROUP  BY `state` ORDER BY cnt DESC;
```

##### `judicial_flag` · P0 · Loan Identification and Entry Filter Fields

| Attribute | Value |
|---|---|
| Newrez Raw Field | `judicial` |
| Data Type | TINYINT |
| Business Meaning | Whether the foreclosure requires a court judgment before auction; affects JUDGEMENT stage routing (Judicial states only) and timeline field meanings |
| Format / Allowed Values | 1=Judicial / 0=Non-Judicial |
| Typical Value | 1 |
| BPS Panel / Function | FCL Summary Judicial type; stage routing |
| Newrez → BPS Rule | judicial=1→'Judicial', 0→'Non Judicial', NULL→NULL (summary_type); summary_judicial_foreclosure copies the boolean |
| Newrez Status | ✅ 100% |
| Newrez Verify Result | [data_date 2026-06-01] NULL:4953 \| 0:51 \| 1:48 |
| BPS Verify Result | [BPS prod \| data date 2026-06-01(main table has no embedded as-of, same ETL cycle as Newrez source) \| ETL load 2026-06-03] 0:43 \| 1:34 \| ∅NULL:12 |

Newrez Verify SQL:
```sql
-- Verify against mysql_dev, data date 2026-06-01
SELECT dataasof AS data_date, judicial, COUNT(*) AS cnt
FROM   newrez.portnewrezfc
WHERE  dataasof = '2026-06-01'
GROUP  BY dataasof, judicial ORDER BY cnt DESC;
```

BPS Verify SQL (prod, read-only):
```sql
-- Verify against prod bpms (read-only)
SELECT '2026-06-01' AS data_date, `summary_judicial_foreclosure` AS val, COUNT(*) AS cnt
FROM   bpms.sync_loan_foreclosure
GROUP  BY `summary_judicial_foreclosure` ORDER BY cnt DESC;
```

##### `active_fcl_flag` · P0 · Loan Identification and Entry Filter Fields

| Attribute | Value |
|---|---|
| Newrez Raw Field | `activefcflag` |
| Data Type | TINYINT |
| Business Meaning | Whether the loan is in an active foreclosure process; 1=active, 0=not in active foreclosure (BPS "Closed Foreclosure" — includes completed AND withdrawn/reinstated/paid, **not necessarily "completed"**); historical NULLs conservatively treated as active (see doc 13 Q3 Technical Detail) |
| Format / Allowed Values | 1=in active foreclosure / 0=not in active foreclosure (completed OR withdrawn/reinstated/paid; BPS "Closed Foreclosure"); NULL conservatively treated as 1 |
| Typical Value | 1 |
| BPS Panel / Function | BPS entry condition; historical NULLs require NULL-safe handling (see doc 13 Q3) |
| Newrez → BPS Rule | summary_completed_foreclosure = NOT(activefcflag) (0→1, 1→0); prod-measured all-NULL |
| Newrez Status | ✅ 100% (incl. historical NULLs) |
| Newrez Verify Result | [data_date 2026-06-01] 0:5016 \| 1:36 |
| BPS Verify Result | [BPS prod \| data date 2026-06-01(main table has no embedded as-of, same ETL cycle as Newrez source) \| ETL load 2026-06-03] ∅NULL:89 |

Newrez Verify SQL:
```sql
-- Verify against mysql_dev, data date 2026-06-01
SELECT dataasof AS data_date, activefcflag, COUNT(*) AS cnt
FROM   newrez.portnewrezfc
WHERE  dataasof = '2026-06-01'
GROUP  BY dataasof, activefcflag ORDER BY cnt DESC;
```

BPS Verify SQL (prod, read-only):
```sql
-- Verify against prod bpms (read-only)
SELECT '2026-06-01' AS data_date, `summary_completed_foreclosure` AS val, COUNT(*) AS cnt
FROM   bpms.sync_loan_foreclosure
GROUP  BY `summary_completed_foreclosure` ORDER BY cnt DESC;
```

##### `fcl_referral_date` · P0 · Loan Identification and Entry Filter Fields

| Attribute | Value |
|---|---|
| Newrez Raw Field | `fcreferraldate` |
| Data Type | DATE |
| Business Meaning | Date the lender formally transferred the foreclosure case to an attorney firm; **BPS entry core condition** (must be non-null to be included); legal start of the FCL timeline |
| Format / Allowed Values | YYYY-MM-DD |
| Typical Value | 2024-01-20 |
| BPS Panel / Function | **BPS core entry prerequisite**; `timeline_referred_to_foreclosure_date`; FCL timeline anchor |
| Newrez → BPS Rule | Direct copy (fcreferraldate → timeline_referred_to_foreclosure_date; entry filter field) |
| Newrez Status | ✅ 100% |
| Newrez Verify Result | [data_date 2026-06-01] 2025-02-18 \| 2025-10-09 \| 2026-05-26 \| 2026-03-05 \| 2026-01-28 \| 2026-03-16 \| 2026-01-29 \| 2026-05-22 \| 2026-05-26 \| 2026-01-20 (10 rows) |
| BPS Verify Result | [BPS prod \| data date 2026-06-01(main table has no embedded as-of, same ETL cycle as Newrez source) \| ETL load 2026-06-03] non-null 89/89 \| range 2018-08-15~2026-05-27 |

Newrez Verify SQL:
```sql
-- Verify against mysql_dev, data date 2026-06-01
SELECT loanid, dataasof, fcreferraldate
FROM   newrez.portnewrezfc
WHERE  dataasof = '2026-06-01'
  AND  fcreferraldate IS NOT NULL
LIMIT  10;
```

BPS Verify SQL (prod, read-only):
```sql
-- Verify against prod bpms (read-only)
SELECT '2026-06-01' AS data_date, COUNT(*) AS total, COUNT(`timeline_referred_to_foreclosure_date`) AS non_null,
       MIN(`timeline_referred_to_foreclosure_date`) AS min_dt, MAX(`timeline_referred_to_foreclosure_date`) AS max_dt
FROM   bpms.sync_loan_foreclosure;
```

<!-- FS-CARDS:2.1 END -->



### 2.2 FCL Status Fields (P1 — FCL Summary Panel Core)

<!-- FS-CARDS:2.2 START -->
##### `fcl_stage` · P1 · FCL Status Fields

| Attribute | Value |
|---|---|
| Newrez Raw Field | `fcstage` |
| Data Type | VARCHAR |
| Business Meaning | Newrez's internal current workflow step text (e.g., "Pre-Sale Review"); **the sole source of `summary_current_step` (direct passthrough)** |
| Format / Allowed Values | Text (Newrez internal stage description) |
| Typical Value | Service Complete |
| BPS Panel / Function | FCL Summary `summary_current_step` (**sole source, direct passthrough**); also stage-waterfall → sync_fcl_stage_info.stage |
| Newrez → BPS Rule | ① → `summary_current_step`: **direct passthrough of fcstage** (`basic_data_pool_config.py:282`; currentmilestone not involved); ② → `sync_fcl_stage_info.stage`: stage-waterfall determination (by milestone priority: REFERRAL/SALE/SERVICE/FIRST_LEGAL/JUDGEMENT/DEMAND) |
| Newrez Status | ✅ 99.5% |
| Newrez Verify Result | [data_date 2026-06-01] Pre-Sale Review 1 (SCRA and PACER Check):16 \| Service Complete:12 \| Post Sale Review (SCRA and PACER Check):9 \| Sale Scheduled For:9 \| Title Report Received:7 \| NOS Sent for Recording:6 \| Complaint Sent for Filing:5 \| Preliminary Title Clear:4 \| Presale Redemption Will Expire On:3 \| Pre-Sale Review 2 (SCRA and PACER Check):3 \| Order Of Reference Sent:3 \| Complaint Prepared and Sent for Filing:2 \| Service Sent:2 \| Judgment Hearing Scheduled For:2 \| NOD Prepared and Sent for Filing :2 \| NOD Mailed and Posted:1 \| First Publication:1 \| Order Of Reference Received:1 \| Acceleration Letter Sent:1 \| Hearing Complete:1 \| TSG Report Received:1 \| Dockets Prepared and Sent for Filing:1 \| Is Home Equity/Judicial Rail Needed :1 \| Return of Service Filed:1 \| Answer Period Will Expire On:1 \| Final Title Clear:1 \| Complaint Submitted for Service:1 \| Submitted for Service:1 \| Notice … |
| BPS Verify Result | [BPS prod \| data date fctrdt=2026-06-01 \| ETL load 2026-06-03] REFERRAL:2738 \| SALE:2068 \| SERVICE:1528 \| FIRST_LEGAL:775 \| JUDGEMENT:732 \| DEMAND:422 |

Newrez Verify SQL:
```sql
-- Verify against mysql_dev, data date 2026-06-01
SELECT dataasof AS data_date, fcstage AS val, COUNT(*) AS cnt
FROM   newrez.portnewrezfc
WHERE  dataasof = '2026-06-01'
  AND  fcstage IS NOT NULL AND fcstage != ''
GROUP  BY dataasof, fcstage ORDER BY cnt DESC LIMIT 30;
```

BPS Verify SQL (prod, read-only):
```sql
-- Verify against prod bpms (read-only)
SELECT '2026-06-01' AS data_date, `stage` AS val, COUNT(*) AS cnt
FROM   bpms.sync_fcl_stage_info
GROUP  BY `stage` ORDER BY cnt DESC;
```

##### `current_milestone` · P1 · FCL Status Fields

| Attribute | Value |
|---|---|
| Newrez Raw Field | `currentmilestone` |
| Data Type | VARCHAR |
| Business Meaning | Newrez raw milestone-label column; **not consumed by the current ETL** (`summary_current_step` actually takes `fcstage`, see rule) |
| Format / Allowed Values | BPS milestone label text |
| Typical Value | First Legal |
| BPS Panel / Function | (was assumed to feed `summary_current_step`; **field-measured: ETL does not use it** — see rule) |
| Newrez → BPS Rule | ⛔ **ETL does not read `currentmilestone`**: `summary_current_step` = `fcstage` direct passthrough (`basic_data_pool_config.py:282`; `currentmilestone` has 0 refs in the entire PrefectFlow repo; prod `summary_current_step` values are all fcstage free-text). Kept as a standard-interface candidate but **unused by the current pipeline** (corrected 2026-06-10; the earlier "currentmilestone-first" was wrong, see doc 13 §8 Q13) |
| Newrez Status | ⚠️ 62.7% (raw column exists but ETL does not consume it — **improving fill rate does not affect summary_current_step**) |
| Newrez Verify Result | [data_date 2026-06-01] Closed:54 \| First Legal:16 \| Sold:9 \| Sale Held:7 \| Service Complete:6 \| Judgment Entered:4 \| Sale Scheduled:3 |
| BPS Verify Result | [BPS prod \| data date 2026-06-01(main table has no embedded as-of, same ETL cycle as Newrez source) \| ETL load 2026-06-03] Pre-Sale Review 1 (SCRA and PACER Check):13 \| Post Sale Review (SCRA and PACER Check):9 \| NOS Sent for Recording:7 \| Sale Scheduled For:7 \| Service Complete:6 \| Preliminary Title Clear:5 \| ∅NULL:4 \| Complaint Sent for Filing:3 \| Order Of Reference Sent:3 \| Pre-Sale Review 2 (SCRA and PACER Check):3 \| First Legal Action Filed:2 \| Title Summary:2 \| Presale Redemption Will Expire On:2 \| Pending First Legal:2 \| Judgment Hearing Scheduled For:2 \| NOD Prepared and Sent for Filing :2 \| Title Report Received:2 \| Return of Service Filed:1 \| Acceleration Letter Sent:1 \| Is Home Equity/Judicial Rail Needed :1 \| Order Of Reference Received:1 \| Hearing Complete:1 \| TSG Report Received:1 \| Complaint Submitted for Service:1 \| Contested / Litigation Start:1 \| Sale Deed Recorded:1 \| Dockets Prepared and Sent for Filing:1 \| Answer Period … |

Newrez Verify SQL:
```sql
-- Verify against mysql_dev, data date 2026-06-01
SELECT dataasof AS data_date, currentmilestone AS val, COUNT(*) AS cnt
FROM   newrez.portnewrezfc
WHERE  dataasof = '2026-06-01'
  AND  currentmilestone IS NOT NULL AND currentmilestone != ''
GROUP  BY dataasof, currentmilestone ORDER BY cnt DESC LIMIT 30;
```

BPS Verify SQL (prod, read-only):
```sql
-- Verify against prod bpms (read-only)
SELECT '2026-06-01' AS data_date, `summary_current_step` AS val, COUNT(*) AS cnt
FROM   bpms.sync_loan_foreclosure
GROUP  BY `summary_current_step` ORDER BY cnt DESC;
```

##### `last_completed_step` · P1 · FCL Status Fields

| Attribute | Value |
|---|---|
| Newrez Raw Field | `lastfcstepcompleted` |
| Data Type | VARCHAR |
| Business Meaning | Most recently completed foreclosure processing step text (e.g., "Motion for Judgment Sent to Court"); used by operations to track progress |
| Format / Allowed Values | Text |
| Typical Value | FC Referral |
| BPS Panel / Function | FCL Summary `summary_last_step_completed` |
| Newrez → BPS Rule | Direct copy (lastfcstepcompleted → summary_last_step_completed) |
| Newrez Status | ✅ 99.5% |
| Newrez Verify Result | [data_date 2026-06-01] Preliminary Title Clear:21 \| Post Sale Review (SCRA and PACER Check):9 \| File Received By Attorney:8 \| Sale Scheduled For:6 \| Complaint Sent For Service:5 \| Title Report Received:4 \| Submitted for Service:4 \| Presale Redemption Will Expire On:3 \| NOS Recorded:3 \| Answer Period Will Expire On:3 \| Final Title Clear:3 \| NOS Posted:3 \| HUD First Action Expires:2 \| Review for Judicial Action:2 \| Motion for Judgment Sent to Court:2 \| NOS Sent for Recording:2 \| Complaint Submitted for Service:2 \| Firm Registers NOI With State:2 \| Service Complete:2 \| NOTS Recorded:1 \| Complaint Filed:1 \| File Referred To Attorney:1 \| First Publication of NOS:1 \| Order Authorizing Sale Received:1 \| Attorney Acknowledges:1 \| Praecipe Filed:1 \| Hearing Scheduled For:1 \| NOD Filed:1 \| Are We Proceeding with a Consent Judgment :1 \| Order Of Reference Sent:1 |
| BPS Verify Result | [BPS prod \| data date 2026-06-01(main table has no embedded as-of, same ETL cycle as Newrez source) \| ETL load 2026-06-03] Preliminary Title Clear:12 \| ∅NULL:12 \| Post Sale Review (SCRA and PACER Check):9 \| Title Report Received:5 \| Sale Scheduled For:5 \| NOS Recorded:3 \| File Received By Attorney:3 \| Submitted for Service:3 \| Final Title Clear:3 \| Answer Period Will Expire On:3 \| Presale Redemption Will Expire On:3 \| Motion for Judgment Sent to Court:2 \| NOS Sent for Recording:2 \| Review for Judicial Action:2 \| Service Complete:2 \| Complaint Sent For Service:2 \| HUD First Action Expires:2 \| NOTS Recorded:1 \| First Publication:1 \| Hearing Scheduled For:1 \| Order Of Reference Sent:1 \| NOD Filed:1 \| Praecipe Filed:1 \| Is Home Equity/Judicial Rail Needed :1 \| First Publication of NOS:1 \| Are We Proceeding with a Consent Judgment :1 \| Order Authorizing Sale Received:1 \| NOS Posted:1 \| Complaint Submitted for Service:1 \| Complaint Filed:1 \| Firm … |

Newrez Verify SQL:
```sql
-- Verify against mysql_dev, data date 2026-06-01
SELECT dataasof AS data_date, lastfcstepcompleted AS val, COUNT(*) AS cnt
FROM   newrez.portnewrezfc
WHERE  dataasof = '2026-06-01'
  AND  lastfcstepcompleted IS NOT NULL AND lastfcstepcompleted != ''
GROUP  BY dataasof, lastfcstepcompleted ORDER BY cnt DESC LIMIT 30;
```

BPS Verify SQL (prod, read-only):
```sql
-- Verify against prod bpms (read-only)
SELECT '2026-06-01' AS data_date, `summary_last_step_completed` AS val, COUNT(*) AS cnt
FROM   bpms.sync_loan_foreclosure
GROUP  BY `summary_last_step_completed` ORDER BY cnt DESC;
```

##### `last_completed_step_date` · P1 · FCL Status Fields

| Attribute | Value |
|---|---|
| Newrez Raw Field | `lastfcstepcompleteddate` |
| Data Type | DATE |
| Business Meaning | Completion date of the above step |
| Format / Allowed Values | YYYY-MM-DD |
| Typical Value | 2024-02-15 |
| BPS Panel / Function | FCL Summary `summary_last_step_completed_date` |
| Newrez → BPS Rule | Direct copy (lastfcstepcompleteddate → summary_last_step_completed_date) |
| Newrez Status | ✅ 99.5% |
| Newrez Verify Result | [data_date 2026-06-01] 2025-02-26 \| 2025-11-03 \| 2026-05-26 \| 2026-04-23 \| 2026-05-05 \| 2026-04-30 \| 2026-03-03 \| 2026-05-22 \| 2026-05-26 \| 2026-03-13 (10 rows) |
| BPS Verify Result | [BPS prod \| data date 2026-06-01(main table has no embedded as-of, same ETL cycle as Newrez source) \| ETL load 2026-06-03] non-null 77/89 \| range 2019-10-14~2026-05-26 |

Newrez Verify SQL:
```sql
-- Verify against mysql_dev, data date 2026-06-01
SELECT loanid, dataasof, lastfcstepcompleteddate
FROM   newrez.portnewrezfc
WHERE  dataasof = '2026-06-01'
  AND  lastfcstepcompleteddate IS NOT NULL
LIMIT  10;
```

BPS Verify SQL (prod, read-only):
```sql
-- Verify against prod bpms (read-only)
SELECT '2026-06-01' AS data_date, COUNT(*) AS total, COUNT(`summary_last_step_completed_date`) AS non_null,
       MIN(`summary_last_step_completed_date`) AS min_dt, MAX(`summary_last_step_completed_date`) AS max_dt
FROM   bpms.sync_loan_foreclosure;
```

##### `fcl_results` · P1 · FCL Status Fields

| Attribute | Value |
|---|---|
| Newrez Raw Field | `fcresults` |
| Data Type | VARCHAR |
| Business Meaning | Final FCL disposition result (populated only for completed loans); typical values: `3rd Party` (third-party purchase) / `REO` (lender-owned); `fcresults='3rd Party'` triggers the `timeline_third_party_sold_date_date` logic |
| Format / Allowed Values | Text; typical values: `3rd Party` / `REO` |
| Typical Value | REO |
| BPS Panel / Function | FCL Summary (completed loans); `timeline_third_party_sold_date_date` trigger logic |
| Newrez → BPS Rule | N/A — not stored standalone in BPS; only drives the fcresults='3rd Party' timeline_third_party_sold check |
| Newrez Status | ⚠️ 2.1% (completed loans only) |
| Newrez Verify Result | [data_date 2026-06-01] REO:6 \| 3rd Party:3 |
| BPS Verify Result | N/A — not mapped to a BPS FCL sync table (see Newrez → BPS Rule) |

Newrez Verify SQL:
```sql
-- Verify against mysql_dev, data date 2026-06-01
SELECT dataasof AS data_date, fcresults AS val, COUNT(*) AS cnt
FROM   newrez.portnewrezfc
WHERE  dataasof = '2026-06-01'
  AND  fcresults IS NOT NULL AND fcresults != ''
GROUP  BY dataasof, fcresults ORDER BY cnt DESC LIMIT 30;
```

##### `fcl_removal_description` · P1 · FCL Status Fields

| Attribute | Value |
|---|---|
| Newrez Raw Field | `fcremovaldesc` |
| Data Type | VARCHAR |
| Business Meaning | Reason the loan exited/closed foreclosure (populated only for removed loans): Reinstated / Loss Mitigation / Paid in Full / Process Complete / Deed in Lieu; drives the BPS Foreclosure Status `'Closed Foreclosure: <desc>'` suffix; pairs with `fcl_removal_date` |
| Format / Allowed Values | `Reinstated` / `Loss Mitigation` / `Paid in Full` / `Process Complete` / `Deed in Lieu Cmplte` (empty for active FCL) |
| Typical Value | Reinstated |
| BPS Panel / Function | FCL Summary `summary_foreclosure_status` (folded into `'Closed Foreclosure:'+desc`; no standalone BPS column) |
| Newrez → BPS Rule | N/A — not stored standalone in BPS (folded into Foreclosure Status; see Newrez → BPS Rule) |
| Newrez Status | ✅ ~1.2% (removed-FCL loans only; 63 non-null at 2026-06-01) |
| Newrez Verify Result | [data_date 2026-06-01] Reinstated:26 \| Loss Mitigation:16 \| Paid in Full:11 \| Process Complete:9 \| Deed in Lieu Cmplte:1 |
| BPS Verify Result | N/A — not mapped to a BPS FCL sync table (see Newrez → BPS Rule) |

Newrez Verify SQL:
```sql
-- Verify against mysql_dev, data date 2026-06-01
SELECT dataasof AS data_date, fcremovaldesc AS val, COUNT(*) AS cnt
FROM   newrez.portnewrezfc
WHERE  dataasof = '2026-06-01'
  AND  fcremovaldesc IS NOT NULL AND fcremovaldesc != ''
GROUP  BY dataasof, fcremovaldesc ORDER BY cnt DESC LIMIT 30;
```

##### `attorney_firm` · P1 · FCL Status Fields

| Attribute | Value |
|---|---|
| Newrez Raw Field | `fcfirm` |
| Data Type | VARCHAR |
| Business Meaning | Full name of the law firm handling this foreclosure case |
| Format / Allowed Values | Text |
| Typical Value | Kelley Kronenberg, P.A. |
| BPS Panel / Function | FCL Summary `summary_foreclosure_attorney` / `summary_firm` |
| Newrez → BPS Rule | Direct copy (fcfirm → summary_foreclosure_attorney / summary_firm) |
| Newrez Status | ✅ 100% |
| Newrez Verify Result | [data_date 2026-06-01] Korde & Associates, P.C. \| Stern & Eisenberg, PC \| Padgett Law Group \| Clunk, Hoose Co., LPA \| Friedman Vartolo LLP \| McCarthy & Holthus, LLP \| Friedman Vartolo LLP \| McCarthy & Holthus, LLP \| Foundation Legal Group, LLP \| Friedman Vartolo LLP (10 rows) |
| BPS Verify Result | [BPS prod \| data date 2026-06-01(main table has no embedded as-of, same ETL cycle as Newrez source) \| ETL load 2026-06-03] ∅NULL:85 \| Brock & Scott PLLC:1 \| McPhail Sanchez, LLC:1 \| Vylla Solutions, LLC:1 \| Lender Legal PLLC:1 |

Newrez Verify SQL:
```sql
-- Verify against mysql_dev, data date 2026-06-01
SELECT loanid, dataasof, fcfirm
FROM   newrez.portnewrezfc
WHERE  dataasof = '2026-06-01'
  AND  fcfirm IS NOT NULL AND fcfirm != ''
LIMIT  10;
```

BPS Verify SQL (prod, read-only):
```sql
-- Verify against prod bpms (read-only)
SELECT '2026-06-01' AS data_date, `summary_foreclosure_attorney` AS val, COUNT(*) AS cnt
FROM   bpms.sync_loan_foreclosure
GROUP  BY `summary_foreclosure_attorney` ORDER BY cnt DESC;
```

##### `contested_flag` · P1 · FCL Status Fields

| Attribute | Value |
|---|---|
| Newrez Raw Field | `fccontestedflag` |
| Data Type | TINYINT |
| Business Meaning | Whether contested litigation exists (borrower filed a legal objection); 1=contested / 0=not contested |
| Format / Allowed Values | 0/1 |
| Typical Value | 0 |
| BPS Panel / Function | FCL Summary `summary_contested_litigation` |
| Newrez → BPS Rule | Direct copy (fccontestedflag → summary_contested_litigation) |
| Newrez Status | ✅ 100% |
| Newrez Verify Result | [data_date 2026-06-01] 0:5051 \| 1:1 |
| BPS Verify Result | [BPS prod \| data date 2026-06-01(main table has no embedded as-of, same ETL cycle as Newrez source) \| ETL load 2026-06-03] 0:75 \| ∅NULL:13 \| 1:1 |

Newrez Verify SQL:
```sql
-- Verify against mysql_dev, data date 2026-06-01
SELECT dataasof AS data_date, fccontestedflag, COUNT(*) AS cnt
FROM   newrez.portnewrezfc
WHERE  dataasof = '2026-06-01'
GROUP  BY dataasof, fccontestedflag ORDER BY cnt DESC;
```

BPS Verify SQL (prod, read-only):
```sql
-- Verify against prod bpms (read-only)
SELECT '2026-06-01' AS data_date, `summary_contested_litigation` AS val, COUNT(*) AS cnt
FROM   bpms.sync_loan_foreclosure
GROUP  BY `summary_contested_litigation` ORDER BY cnt DESC;
```

##### `servicer_days_in_fcl` · P1 · FCL Status Fields

| Attribute | Value |
|---|---|
| Newrez Raw Field | `smsdaysinfc` |
| Data Type | INTEGER |
| Business Meaning | Servicer-perspective days in FCL — counted from the servicer FCL setup date (`fcsetupdate`); Newrez/SMS=Shellpoint implements this as native `smsdaysinfc` (ETL alias `svc_days_infc`). BPS real-time correction: `smsdaysinfc + DATEDIFF(today NY, dataasof)`; ≤ days_in_fcl. (Standard field name is servicer-neutral; `smsdaysinfc`/`summary_sms_days_in_fcl` are the Newrez/BPS column names.) |
| Format / Allowed Values | Positive integer (Servicer-perspective days, as of dataasof) |
| Typical Value | 128 |
| BPS Panel / Function | FCL Summary `summary_sms_days_in_fcl` (BPS adds real-time lag correction) |
| Newrez → BPS Rule | smsdaysinfc + DATEDIFF(today NY, dataasof) real-time recompute (counted from fcsetupdate) |
| Newrez Status | ✅ 100% |
| Newrez Verify Result | [data_date 2026-06-01] 10 \| 29 \| 7 \| 67 \| 99 \| 50 \| 40 \| 11 \| 7 \| 133 (10 rows) |
| BPS Verify Result | [BPS prod \| data date 2026-06-01(main table has no embedded as-of, same ETL cycle as Newrez source) \| ETL load 2026-06-03] non-null 69/89 \| range 9~610 \| avg 188.36 |

Newrez Verify SQL:
```sql
-- Verify against mysql_dev, data date 2026-06-01
SELECT loanid, dataasof, smsdaysinfc
FROM   newrez.portnewrezfc
WHERE  dataasof = '2026-06-01'
  AND  smsdaysinfc IS NOT NULL
LIMIT  10;
```

BPS Verify SQL (prod, read-only):
```sql
-- Verify against prod bpms (read-only)
SELECT '2026-06-01' AS data_date, COUNT(*) AS total, COUNT(`summary_sms_days_in_fcl`) AS non_null,
       MIN(`summary_sms_days_in_fcl`) AS min_v, MAX(`summary_sms_days_in_fcl`) AS max_v, ROUND(AVG(`summary_sms_days_in_fcl`),2) AS avg_v
FROM   bpms.sync_loan_foreclosure;
```

##### `days_in_fcl` · P1 · FCL Status Fields

| Attribute | Value |
|---|---|
| Newrez Raw Field | `daysinfc` |
| Data Type | INTEGER |
| Business Meaning | Investor / full-timeline days in FCL — counted from the referral date (`fcreferraldate`); differs from servicer_days_in_fcl in start date (referral vs setup), so days_in_fcl ≥ servicer_days_in_fcl; BPS applies same real-time correction: `daysinfc + DATEDIFF(today NY, dataasof)` |
| Format / Allowed Values | Positive integer (investor-perspective days) |
| Typical Value | 215 |
| BPS Panel / Function | FCL Summary `summary_days_in_fcl` (same real-time correction) |
| Newrez → BPS Rule | daysinfc + DATEDIFF(today NY, dataasof) real-time recompute (counted from fcreferraldate) |
| Newrez Status | ✅ 100% |
| Newrez Verify Result | [data_date 2026-06-01] 10 \| 29 \| 7 \| 67 \| 99 \| 50 \| 40 \| 11 \| 7 \| 133 (10 rows) |
| BPS Verify Result | [BPS prod \| data date 2026-06-01(main table has no embedded as-of, same ETL cycle as Newrez source) \| ETL load 2026-06-03] non-null 83/89 \| range 8~818 \| avg 185.06 |

Newrez Verify SQL:
```sql
-- Verify against mysql_dev, data date 2026-06-01
SELECT loanid, dataasof, daysinfc
FROM   newrez.portnewrezfc
WHERE  dataasof = '2026-06-01'
  AND  daysinfc IS NOT NULL
LIMIT  10;
```

BPS Verify SQL (prod, read-only):
```sql
-- Verify against prod bpms (read-only)
SELECT '2026-06-01' AS data_date, COUNT(*) AS total, COUNT(`summary_days_in_fcl`) AS non_null,
       MIN(`summary_days_in_fcl`) AS min_v, MAX(`summary_days_in_fcl`) AS max_v, ROUND(AVG(`summary_days_in_fcl`),2) AS avg_v
FROM   bpms.sync_loan_foreclosure;
```

<!-- FS-CARDS:2.2 END -->



### 2.3 FCL Timeline Fields (P0/P1/P2 — Timeline Panel + Aggregate Time Line Tab)

> **Note**: Fields in this section are consumed by two BPS display locations:
> 1. **Loan detail page FCL Milestone timeline**: `timeline_*` fields (19 fields)
> 2. **Aggregate overview Time Line Tab**: `{stage}_start_date` fields (7 columns; see Section 7)

<!-- FS-CARDS:2.3 START -->
##### `noi_date` · P1 · FCL Timeline Fields

| Attribute | Value |
|---|---|
| Newrez Raw Field | *(none; Newrez conflates with `demandsentdate`)* |
| Data Type | DATE |
| Business Meaning | **Formal Notice of Intent to Foreclose** required by state law: Judicial states = mandatory pre-court notice (typically 30–45 days); Non-Judicial states = Notice of Default or equivalent. Conceptually distinct from `demand_sent_date` (payment demand letter) — some Servicers provide both dates separately; Newrez conflates the two using `demandsentdate`, which BPS currently substitutes into `timeline_notice_of_intent_date` as an interim measure |
| Format / Allowed Values | YYYY-MM-DD |
| Typical Value | — |
| BPS Panel / Function | Milestone NOI Date; `timeline_notice_of_intent_date`; Time Line Tab `noi_start_date` |
| Newrez → BPS Rule | Direct copy (demandsentdate → timeline_notice_of_intent_date) |
| Newrez Status | ❌ Newrez does not provide separately (BPS currently substitutes `demandsentdate` as interim measure; see note below) |
| Newrez Verify Result | [data_date 2026-06-01] 2024-12-05 \| 2026-04-15 \| 2025-06-16 \| 2026-04-17 \| 2026-05-29 \| 2026-04-13 \| 2026-01-22 \| 2026-05-04 \| 2025-11-24 \| 2025-12-19 (10 rows) |
| BPS Verify Result | [BPS prod \| data date 2026-06-01(main table has no embedded as-of, same ETL cycle as Newrez source) \| ETL load 2026-06-03] non-null 5/89 \| range 2024-05-17~2025-04-22 |

Newrez Verify SQL:
```sql
-- Verify against mysql_dev, data date 2026-06-01
SELECT loanid, dataasof, demandsentdate
FROM   newrez.portnewrezfc
WHERE  dataasof = '2026-06-01'
  AND  demandsentdate IS NOT NULL
LIMIT  10;
```

BPS Verify SQL (prod, read-only):
```sql
-- Verify against prod bpms (read-only)
SELECT '2026-06-01' AS data_date, COUNT(*) AS total, COUNT(`timeline_notice_of_intent_date`) AS non_null,
       MIN(`timeline_notice_of_intent_date`) AS min_dt, MAX(`timeline_notice_of_intent_date`) AS max_dt
FROM   bpms.sync_loan_foreclosure;
```

##### `demand_sent_date` · P1 · FCL Timeline Fields

| Attribute | Value |
|---|---|
| Newrez Raw Field | `demandsentdate` |
| Data Type | DATE |
| Business Meaning | Pre-foreclosure **payment demand letter / default notice** requiring the borrower to cure arrears; may precede or coincide with the formal NOI; triggers BPS DEMAND Stage grouping (`demand_start_date`); Newrez uses this field for both purposes (interim handling, not the interface standard design) |
| Format / Allowed Values | YYYY-MM-DD |
| Typical Value | 2024-02-01 |
| BPS Panel / Function | Stage DEMAND grouping trigger; `demand_start_date` (aggregate page); if Servicer does not provide a separate `noi_date`, BPS uses this field as a substitute for `timeline_notice_of_intent_date` |
| Newrez → BPS Rule | Direct copy (demandsentdate → timeline_notice_of_intent_date; same as noi_date) |
| Newrez Status | ✅ 85.9% (14.1% missing; see doc 13 Q5) |
| Newrez Verify Result | [data_date 2026-06-01] 2024-12-05 \| 2026-04-15 \| 2025-06-16 \| 2026-04-17 \| 2026-05-29 \| 2026-04-13 \| 2026-01-22 \| 2026-05-04 \| 2025-11-24 \| 2025-12-19 (10 rows) |
| BPS Verify Result | [BPS prod \| data date 2026-06-01(main table has no embedded as-of, same ETL cycle as Newrez source) \| ETL load 2026-06-03] non-null 5/89 \| range 2024-05-17~2025-04-22 |

Newrez Verify SQL:
```sql
-- Verify against mysql_dev, data date 2026-06-01
SELECT loanid, dataasof, demandsentdate
FROM   newrez.portnewrezfc
WHERE  dataasof = '2026-06-01'
  AND  demandsentdate IS NOT NULL
LIMIT  10;
```

BPS Verify SQL (prod, read-only):
```sql
-- Verify against prod bpms (read-only)
SELECT '2026-06-01' AS data_date, COUNT(*) AS total, COUNT(`timeline_notice_of_intent_date`) AS non_null,
       MIN(`timeline_notice_of_intent_date`) AS min_dt, MAX(`timeline_notice_of_intent_date`) AS max_dt
FROM   bpms.sync_loan_foreclosure;
```

##### `demand_expiration_date` · P1 · FCL Timeline Fields

| Attribute | Value |
|---|---|
| Newrez Raw Field | `demandexpirationdate` |
| Data Type | DATE |
| Business Meaning | NOI / demand letter expiration date (foreclosure may proceed if unpaid after this date); calculation: `actual_notice_of_intent_days = demandexpirationdate − demandsentdate` |
| Format / Allowed Values | YYYY-MM-DD |
| Typical Value | 2024-03-02 |
| BPS Panel / Function | `timeline_notice_of_intent_end_date`; `actual_notice_of_intent_days` calculation |
| Newrez → BPS Rule | Direct copy (demandexpirationdate → timeline_notice_of_intent_end_date) |
| Newrez Status | ✅ 85.7% |
| Newrez Verify Result | [data_date 2026-06-01] 2025-02-08 \| 2026-05-20 \| 2025-12-19 \| 2026-05-17 \| 2026-06-13 \| 2026-04-28 \| 2026-02-21 \| 2026-05-20 \| 2025-12-19 \| 2026-01-18 (10 rows) |
| BPS Verify Result | [BPS prod \| data date 2026-06-01(main table has no embedded as-of, same ETL cycle as Newrez source) \| ETL load 2026-06-03] non-null 0/89 (prod all NULL) |

Newrez Verify SQL:
```sql
-- Verify against mysql_dev, data date 2026-06-01
SELECT loanid, dataasof, demandexpirationdate
FROM   newrez.portnewrezfc
WHERE  dataasof = '2026-06-01'
  AND  demandexpirationdate IS NOT NULL
LIMIT  10;
```

BPS Verify SQL (prod, read-only):
```sql
-- Verify against prod bpms (read-only)
SELECT '2026-06-01' AS data_date, COUNT(*) AS total, COUNT(`timeline_notice_of_intent_end_date`) AS non_null,
       MIN(`timeline_notice_of_intent_end_date`) AS min_dt, MAX(`timeline_notice_of_intent_end_date`) AS max_dt
FROM   bpms.sync_loan_foreclosure;
```

##### `fcl_setup_date` · P1 · FCL Timeline Fields

| Attribute | Value |
|---|---|
| Newrez Raw Field | `fcsetupdate` |
| Data Type | DATE |
| Business Meaning | FCL internal open date (BPS system case creation date); Newrez typically records the same date as `fcreferraldate` |
| Format / Allowed Values | YYYY-MM-DD |
| Typical Value | 2024-01-10 |
| BPS Panel / Function | `timeline_approved_for_referral_date`; Newrez typically same date as `fcreferraldate` |
| Newrez → BPS Rule | Direct copy (fcsetupdate → timeline_approved_for_referral_date) |
| Newrez Status | ✅ 100% |
| Newrez Verify Result | [data_date 2026-06-01] 2025-02-18 \| 2025-10-09 \| 2026-05-26 \| 2026-03-05 \| 2026-01-28 \| 2026-03-16 \| 2026-01-29 \| 2026-05-22 \| 2026-05-26 \| 2026-01-20 (10 rows) |
| BPS Verify Result | [BPS prod \| data date 2026-06-01(main table has no embedded as-of, same ETL cycle as Newrez source) \| ETL load 2026-06-03] non-null 0/89 (prod all NULL) |

Newrez Verify SQL:
```sql
-- Verify against mysql_dev, data date 2026-06-01
SELECT loanid, dataasof, fcsetupdate
FROM   newrez.portnewrezfc
WHERE  dataasof = '2026-06-01'
  AND  fcsetupdate IS NOT NULL
LIMIT  10;
```

BPS Verify SQL (prod, read-only):
```sql
-- Verify against prod bpms (read-only)
SELECT '2026-06-01' AS data_date, COUNT(*) AS total, COUNT(`timeline_approved_for_referral_date`) AS non_null,
       MIN(`timeline_approved_for_referral_date`) AS min_dt, MAX(`timeline_approved_for_referral_date`) AS max_dt
FROM   bpms.sync_loan_foreclosure;
```

##### `first_legal_date` · P1 · FCL Timeline Fields

| Attribute | Value |
|---|---|
| Newrez Raw Field | `firstlegaldate` |
| Data Type | DATE |
| Business Meaning | Date the foreclosure lawsuit was first filed with the court; typically null in Non-Judicial states (no court required); triggers FIRST_LEGAL Stage |
| Format / Allowed Values | YYYY-MM-DD |
| Typical Value | 2024-02-01 |
| BPS Panel / Function | Milestone First Legal; `timeline_first_legal_date`; Stage FIRST_LEGAL trigger |
| Newrez → BPS Rule | Direct copy (firstlegaldate → timeline_first_legal_date; often empty in non-judicial states) |
| Newrez Status | ⚠️ 57.6% |
| Newrez Verify Result | [data_date 2026-06-01] 2026-04-23 \| 2026-04-28 \| 2026-04-30 \| 2026-02-25 \| 2026-03-12 \| 2025-10-30 \| 2026-04-28 \| 2026-05-28 \| 2025-08-19 \| 2026-02-19 (10 rows) |
| BPS Verify Result | [BPS prod \| data date 2026-06-01(main table has no embedded as-of, same ETL cycle as Newrez source) \| ETL load 2026-06-03] non-null 47/89 \| range 2018-10-29~2026-05-21 |

Newrez Verify SQL:
```sql
-- Verify against mysql_dev, data date 2026-06-01
SELECT loanid, dataasof, firstlegaldate
FROM   newrez.portnewrezfc
WHERE  dataasof = '2026-06-01'
  AND  firstlegaldate IS NOT NULL
LIMIT  10;
```

BPS Verify SQL (prod, read-only):
```sql
-- Verify against prod bpms (read-only)
SELECT '2026-06-01' AS data_date, COUNT(*) AS total, COUNT(`timeline_first_legal_date`) AS non_null,
       MIN(`timeline_first_legal_date`) AS min_dt, MAX(`timeline_first_legal_date`) AS max_dt
FROM   bpms.sync_loan_foreclosure;
```

##### `service_complete_date` · P1 · FCL Timeline Fields

| Attribute | Value |
|---|---|
| Newrez Raw Field | `servicecompletedate` |
| Data Type | DATE |
| Business Meaning | Date legal documents (summons/notice) were successfully served on the borrower; triggers SERVICE Stage |
| Format / Allowed Values | YYYY-MM-DD |
| Typical Value | 2024-03-10 |
| BPS Panel / Function | Milestone Service; `timeline_service_date`; Stage SERVICE trigger |
| Newrez → BPS Rule | Direct copy (servicecompletedate → timeline_service_date) |
| Newrez Status | ⚠️ 28.9% |
| Newrez Verify Result | [data_date 2026-06-01] 2024-11-26 \| 2025-05-23 \| 2024-04-01 \| 2025-11-19 \| 2025-03-04 \| 2025-08-14 \| 2025-06-02 \| 2025-07-18 \| 2026-01-13 \| 2025-05-03 (10 rows) |
| BPS Verify Result | [BPS prod \| data date 2026-06-01(main table has no embedded as-of, same ETL cycle as Newrez source) \| ETL load 2026-06-03] non-null 19/89 \| range 2018-12-10~2026-02-16 |

Newrez Verify SQL:
```sql
-- Verify against mysql_dev, data date 2026-06-01
SELECT loanid, dataasof, servicecompletedate
FROM   newrez.portnewrezfc
WHERE  dataasof = '2026-06-01'
  AND  servicecompletedate IS NOT NULL
LIMIT  10;
```

BPS Verify SQL (prod, read-only):
```sql
-- Verify against prod bpms (read-only)
SELECT '2026-06-01' AS data_date, COUNT(*) AS total, COUNT(`timeline_service_date`) AS non_null,
       MIN(`timeline_service_date`) AS min_dt, MAX(`timeline_service_date`) AS max_dt
FROM   bpms.sync_loan_foreclosure;
```

##### `publication_date` · P2 · FCL Timeline Fields

| Attribute | Value |
|---|---|
| Newrez Raw Field | *(no corresponding field)* |
| Data Type | DATE |
| Business Meaning | Date the foreclosure notice was published in a newspaper / official channel (required step in Non-Judicial states); Newrez does not provide this field |
| Format / Allowed Values | YYYY-MM-DD |
| Typical Value | — |
| BPS Panel / Function | Milestone Publication; `timeline_publication_date`; Stage PUBLICATION trigger |
| Newrez → BPS Rule | Not provided by Newrez; timeline_publication_date always empty |
| Newrez Status | ❌ 0% (Newrez does not provide; see doc 13 Q1) |
| Newrez Verify Result | N/A (no verifiable source) |
| BPS Verify Result | [BPS prod \| data date 2026-06-01(main table has no embedded as-of, same ETL cycle as Newrez source) \| ETL load 2026-06-03] non-null 0/89 (prod all NULL) |

BPS Verify SQL (prod, read-only):
```sql
-- Verify against prod bpms (read-only)
SELECT '2026-06-01' AS data_date, COUNT(*) AS total, COUNT(`timeline_publication_date`) AS non_null,
       MIN(`timeline_publication_date`) AS min_dt, MAX(`timeline_publication_date`) AS max_dt
FROM   bpms.sync_loan_foreclosure;
```

##### `title_received_date` · P2 · FCL Timeline Fields

| Attribute | Value |
|---|---|
| Newrez Raw Field | `titlereceiveddate` |
| Data Type | DATE |
| Business Meaning | Date the attorney firm received the title search report; Newrez does not provide this field |
| Format / Allowed Values | YYYY-MM-DD |
| Typical Value | 2025-04-01 |
| BPS Panel / Function | `timeline_title_report_received_date` |
| Newrez → BPS Rule | Direct copy (titlereceiveddate → timeline_title_report_received_date; mostly empty in Newrez) |
| Newrez Status | ❌ 0% (Newrez does not provide; see doc 13 Q8) |
| Newrez Verify Result | [data_date 2026-06-01] 2026-04-26 \| 2025-12-02 \| 2025-03-24 \| 2025-12-02 (4 rows) |
| BPS Verify Result | [BPS prod \| data date 2026-06-01(main table has no embedded as-of, same ETL cycle as Newrez source) \| ETL load 2026-06-03] non-null 4/89 \| range 2025-03-24~2026-04-26 |

Newrez Verify SQL:
```sql
-- Verify against mysql_dev, data date 2026-06-01
SELECT loanid, dataasof, titlereceiveddate
FROM   newrez.portnewrezfc
WHERE  dataasof = '2026-06-01'
  AND  titlereceiveddate IS NOT NULL
LIMIT  10;
```

BPS Verify SQL (prod, read-only):
```sql
-- Verify against prod bpms (read-only)
SELECT '2026-06-01' AS data_date, COUNT(*) AS total, COUNT(`timeline_title_report_received_date`) AS non_null,
       MIN(`timeline_title_report_received_date`) AS min_dt, MAX(`timeline_title_report_received_date`) AS max_dt
FROM   bpms.sync_loan_foreclosure;
```

##### `title_clear_date` · P2 · FCL Timeline Fields

| Attribute | Value |
|---|---|
| Newrez Raw Field | `titlecleardate` |
| Data Type | DATE |
| Business Meaning | Date the title search confirmed no unknown liens; applies to both preliminary and final title clearance stages; Newrez does not provide |
| Format / Allowed Values | YYYY-MM-DD |
| Typical Value | 2025-04-15 |
| BPS Panel / Function | `timeline_preliminary_title_cleared_date` / `timeline_final_title_cleared_date` |
| Newrez → BPS Rule | Direct copy (titlecleardate → timeline_preliminary_title_cleared_date / final_title_cleared) |
| Newrez Status | ❌ 0% (Newrez does not provide; see doc 13 Q8) |
| Newrez Verify Result | [data_date 2026-06-01] 2026-04-26 \| 2025-03-24 \| 2026-02-02 (3 rows) |
| BPS Verify Result | [BPS prod \| data date 2026-06-01(main table has no embedded as-of, same ETL cycle as Newrez source) \| ETL load 2026-06-03] non-null 3/89 \| range 2025-03-24~2026-04-26 |

Newrez Verify SQL:
```sql
-- Verify against mysql_dev, data date 2026-06-01
SELECT loanid, dataasof, titlecleardate
FROM   newrez.portnewrezfc
WHERE  dataasof = '2026-06-01'
  AND  titlecleardate IS NOT NULL
LIMIT  10;
```

BPS Verify SQL (prod, read-only):
```sql
-- Verify against prod bpms (read-only)
SELECT '2026-06-01' AS data_date, COUNT(*) AS total, COUNT(`timeline_preliminary_title_cleared_date`) AS non_null,
       MIN(`timeline_preliminary_title_cleared_date`) AS min_dt, MAX(`timeline_preliminary_title_cleared_date`) AS max_dt
FROM   bpms.sync_loan_foreclosure;
```

##### `judgement_hearing_scheduled` · P1 · FCL Timeline Fields

| Attribute | Value |
|---|---|
| Newrez Raw Field | `fcjudgmenthearingscheduled` |
| Data Type | DATE |
| Business Meaning | **Scheduled date** of the foreclosure judgment hearing / sale confirmation hearing (future planned event); Judicial states only; triggers JUDGEMENT Stage (priority 2) |
| Format / Allowed Values | YYYY-MM-DD |
| Typical Value | 2026-01-18 |
| BPS Panel / Function | Milestone Judgement Date; **`timeline_judgement_date` / `judgement_start_date`**; Stage JUDGEMENT trigger (priority 2) |
| Newrez → BPS Rule | Direct copy (fcjudgmenthearingscheduled → timeline_judgement_hearing_set_date / timeline_judgement_date) |
| Newrez Status | ✅ 11.9% (Judicial states only) |
| Newrez Verify Result | [data_date 2026-06-01] 2025-11-14 \| 2026-01-18 \| 2026-03-27 \| 2025-10-15 \| 2026-02-04 \| 2026-08-21 \| 2025-09-16 \| 2026-04-13 \| 2025-11-29 \| 2020-01-22 (10 rows) |
| BPS Verify Result | [BPS prod \| data date 2026-06-01(main table has no embedded as-of, same ETL cycle as Newrez source) \| ETL load 2026-06-03] non-null 10/89 \| range 2023-12-14~2026-05-14 |

Newrez Verify SQL:
```sql
-- Verify against mysql_dev, data date 2026-06-01
SELECT loanid, dataasof, fcjudgmenthearingscheduled
FROM   newrez.portnewrezfc
WHERE  dataasof = '2026-06-01'
  AND  fcjudgmenthearingscheduled IS NOT NULL
LIMIT  10;
```

BPS Verify SQL (prod, read-only):
```sql
-- Verify against prod bpms (read-only)
SELECT '2026-06-01' AS data_date, COUNT(*) AS total, COUNT(`timeline_judgement_hearing_set_date`) AS non_null,
       MIN(`timeline_judgement_hearing_set_date`) AS min_dt, MAX(`timeline_judgement_hearing_set_date`) AS max_dt
FROM   bpms.sync_loan_foreclosure;
```

##### `judgement_entered_date` · P1 · FCL Timeline Fields

| Attribute | Value |
|---|---|
| Newrez Raw Field | `fcjudgmententered` |
| Data Type | DATE |
| Business Meaning | Date the court **formally entered** (recorded) the judgment (completed legal fact); calculation: `actual_judgement_hearing_set_days = fcjudgmententered − fcjudgmenthearingscheduled`; NOT a direct Time Line Tab display field (see doc 13 Q10/Q12) |
| Format / Allowed Values | YYYY-MM-DD |
| Typical Value | 2026-01-07 |
| BPS Panel / Function | ETL intermediate table `fcjudgment_end_date`; used for `actual_judgement_hearing_set_days` calculation (`fcjudgmententered` − `fcjudgmenthearingscheduled`); **NOT a direct BPS Time Line Tab display field** |
| Newrez → BPS Rule | N/A — BPS timeline_judgement_date actually takes fcjudgmenthearingscheduled, not fcjudgmententered |
| Newrez Status | ✅ 7.9% (Judicial states only) |
| Newrez Verify Result | [data_date 2026-06-01] 2025-01-10 \| 2025-10-20 \| 2026-01-07 \| 2026-04-08 \| 2025-08-25 \| 2025-12-29 \| 2026-02-04 \| 2025-08-13 \| 2026-02-13 \| 2026-03-20 (10 rows) |
| BPS Verify Result | N/A — not mapped to a BPS FCL sync table (see Newrez → BPS Rule) |

Newrez Verify SQL:
```sql
-- Verify against mysql_dev, data date 2026-06-01
SELECT loanid, dataasof, fcjudgmententered
FROM   newrez.portnewrezfc
WHERE  dataasof = '2026-06-01'
  AND  fcjudgmententered IS NOT NULL
LIMIT  10;
```

##### `scheduled_sale_date` · P1 · FCL Timeline Fields

| Attribute | Value |
|---|---|
| Newrez Raw Field | `fcscheduledsaledate` |
| Data Type | DATE |
| Business Meaning | Scheduled foreclosure auction date; any non-null value immediately triggers the **highest-priority SALE Stage**; updated dynamically as the process advances |
| Format / Allowed Values | YYYY-MM-DD |
| Typical Value | 2024-05-15 |
| BPS Panel / Function | Milestone Sale; `timeline_sale_date_projected_date`; `sale_start_date`; **Stage SALE trigger (highest priority 1)** |
| Newrez → BPS Rule | Direct copy (fcscheduledsaledate → timeline_sale_date_set_date / projected) |
| Newrez Status | ✅ 18.2% |
| Newrez Verify Result | [data_date 2026-06-01] 2026-06-02 \| 2025-09-09 \| 2025-05-16 \| 2025-08-26 \| 2026-06-26 \| 2025-06-05 \| 2026-07-08 \| 2026-06-10 \| 2026-06-30 \| 2026-07-09 (10 rows) |
| BPS Verify Result | [BPS prod \| data date 2026-06-01(main table has no embedded as-of, same ETL cycle as Newrez source) \| ETL load 2026-06-03] non-null 14/89 \| range 2025-01-23~2026-05-22 |

Newrez Verify SQL:
```sql
-- Verify against mysql_dev, data date 2026-06-01
SELECT loanid, dataasof, fcscheduledsaledate
FROM   newrez.portnewrezfc
WHERE  dataasof = '2026-06-01'
  AND  fcscheduledsaledate IS NOT NULL
LIMIT  10;
```

BPS Verify SQL (prod, read-only):
```sql
-- Verify against prod bpms (read-only)
SELECT '2026-06-01' AS data_date, COUNT(*) AS total, COUNT(`timeline_sale_date_set_date`) AS non_null,
       MIN(`timeline_sale_date_set_date`) AS min_dt, MAX(`timeline_sale_date_set_date`) AS max_dt
FROM   bpms.sync_loan_foreclosure;
```

##### `sale_held_date` · P1 · FCL Timeline Fields

| Attribute | Value |
|---|---|
| Newrez Raw Field | `fcsalehelddate` |
| Data Type | DATE |
| Business Meaning | Date the foreclosure auction was actually held; combined with `fcresults` to determine whether it was a third-party purchase |
| Format / Allowed Values | YYYY-MM-DD |
| Typical Value | 2024-05-15 |
| BPS Panel / Function | `timeline_sale_date_held_date`; 3rd Party Sale logic trigger |
| Newrez → BPS Rule | Direct copy (fcsalehelddate → timeline_sale_date_held_date) |
| Newrez Status | ✅ 2.1% (completed loans) |
| Newrez Verify Result | [data_date 2026-06-01] 2026-04-07 \| 2025-12-04 \| 2026-05-15 \| 2026-05-22 \| 2026-05-12 \| 2025-10-14 \| 2026-03-11 \| 2025-11-04 \| 2025-12-29 (9 rows) |
| BPS Verify Result | [BPS prod \| data date 2026-06-01(main table has no embedded as-of, same ETL cycle as Newrez source) \| ETL load 2026-06-03] non-null 11/89 \| range 2025-01-23~2026-05-22 |

Newrez Verify SQL:
```sql
-- Verify against mysql_dev, data date 2026-06-01
SELECT loanid, dataasof, fcsalehelddate
FROM   newrez.portnewrezfc
WHERE  dataasof = '2026-06-01'
  AND  fcsalehelddate IS NOT NULL
LIMIT  10;
```

BPS Verify SQL (prod, read-only):
```sql
-- Verify against prod bpms (read-only)
SELECT '2026-06-01' AS data_date, COUNT(*) AS total, COUNT(`timeline_sale_date_held_date`) AS non_null,
       MIN(`timeline_sale_date_held_date`) AS min_dt, MAX(`timeline_sale_date_held_date`) AS max_dt
FROM   bpms.sync_loan_foreclosure;
```

##### `deed_recorded_date` · P2 · FCL Timeline Fields

| Attribute | Value |
|---|---|
| Newrez Raw Field | `dtdeedrecorded` |
| Data Type | DATE |
| Business Meaning | Date the deed was recorded (legal completion of foreclosure); first option in `COALESCE(dtdeedrecorded, fcremovaldate)` for `timeline_foreclosure_completed_date` |
| Format / Allowed Values | YYYY-MM-DD |
| Typical Value | 2024-06-01 |
| BPS Panel / Function | `timeline_foreclosure_completed_date` (priority; COALESCE first option) |
| Newrez → BPS Rule | COALESCE(dtdeedrecorded, fcremovaldate) → timeline_foreclosure_completed_date |
| Newrez Status | ✅ ~0% (completed loans) |
| Newrez Verify Result | [data_date 2026-06-01] 2026-04-28 \| 2026-05-22 \| 2025-10-28 \| 2025-11-12 (4 rows) |
| BPS Verify Result | [BPS prod \| data date 2026-06-01(main table has no embedded as-of, same ETL cycle as Newrez source) \| ETL load 2026-06-03] non-null 0/89 (prod all NULL) |

Newrez Verify SQL:
```sql
-- Verify against mysql_dev, data date 2026-06-01
SELECT loanid, dataasof, dtdeedrecorded
FROM   newrez.portnewrezfc
WHERE  dataasof = '2026-06-01'
  AND  dtdeedrecorded IS NOT NULL
LIMIT  10;
```

BPS Verify SQL (prod, read-only):
```sql
-- Verify against prod bpms (read-only)
SELECT '2026-06-01' AS data_date, COUNT(*) AS total, COUNT(`timeline_foreclosure_completed_date`) AS non_null,
       MIN(`timeline_foreclosure_completed_date`) AS min_dt, MAX(`timeline_foreclosure_completed_date`) AS max_dt
FROM   bpms.sync_loan_foreclosure;
```

##### `fcl_removal_date` · P1 · FCL Timeline Fields

| Attribute | Value |
|---|---|
| Newrez Raw Field | `fcremovaldate` |
| Data Type | DATE |
| Business Meaning | Date the FCL process was cancelled or closed (borrower paid/LM succeeded/other reason); fallback second option in the COALESCE |
| Format / Allowed Values | YYYY-MM-DD |
| Typical Value | 2024-06-01 |
| BPS Panel / Function | `timeline_foreclosure_completed_date` (fallback; COALESCE second option) |
| Newrez → BPS Rule | COALESCE(dtdeedrecorded, fcremovaldate) → timeline_foreclosure_completed_date (same column as deed_recorded_date, fallback source) |
| Newrez Status | ✅ ~2.0% (completed loans) |
| Newrez Verify Result | [data_date 2026-06-01] 2025-02-28 \| 2025-11-07 \| 2026-05-11 \| 2026-05-07 \| 2026-05-05 \| 2026-03-10 \| 2025-11-11 \| 2026-03-27 \| 2025-08-29 \| 2026-04-08 (10 rows) |
| BPS Verify Result | [BPS prod \| data date 2026-06-01(main table has no embedded as-of, same ETL cycle as Newrez source) \| ETL load 2026-06-03] non-null 0/89 (prod all NULL) |

Newrez Verify SQL:
```sql
-- Verify against mysql_dev, data date 2026-06-01
SELECT loanid, dataasof, fcremovaldate
FROM   newrez.portnewrezfc
WHERE  dataasof = '2026-06-01'
  AND  fcremovaldate IS NOT NULL
LIMIT  10;
```

BPS Verify SQL (prod, read-only):
```sql
-- Verify against prod bpms (read-only)
SELECT '2026-06-01' AS data_date, COUNT(*) AS total, COUNT(`timeline_foreclosure_completed_date`) AS non_null,
       MIN(`timeline_foreclosure_completed_date`) AS min_dt, MAX(`timeline_foreclosure_completed_date`) AS max_dt
FROM   bpms.sync_loan_foreclosure;
```

##### `third_party_proceeds_date` · P2 · FCL Timeline Fields

| Attribute | Value |
|---|---|
| Newrez Raw Field | `fcl3rdpartyproceedsreceiveddate` |
| Data Type | DATE |
| Business Meaning | Date auction proceeds were received from the third-party buyer |
| Format / Allowed Values | YYYY-MM-DD |
| Typical Value | 2026-03-04 |
| BPS Panel / Function | `timeline_third_party_proceeds_received_date` |
| Newrez → BPS Rule | Direct copy (fcl3rdpartyproceedsreceiveddate → timeline_third_party_proceeds_received_date) |
| Newrez Status | ✅ ~0% (very few completed loans) |
| Newrez Verify Result | [data_date 2026-06-01] 2026-05-27 \| 2026-04-02 \| 2026-03-05 (3 rows) |
| BPS Verify Result | [BPS prod \| data date 2026-06-01(main table has no embedded as-of, same ETL cycle as Newrez source) \| ETL load 2026-06-03] non-null 3/89 \| range 2026-03-05~2026-05-27 |

Newrez Verify SQL:
```sql
-- Verify against mysql_dev, data date 2026-06-01
SELECT loanid, dataasof, fcl3rdpartyproceedsreceiveddate
FROM   newrez.portnewrezfc
WHERE  dataasof = '2026-06-01'
  AND  fcl3rdpartyproceedsreceiveddate IS NOT NULL
LIMIT  10;
```

BPS Verify SQL (prod, read-only):
```sql
-- Verify against prod bpms (read-only)
SELECT '2026-06-01' AS data_date, COUNT(*) AS total, COUNT(`timeline_third_party_proceeds_received_date`) AS non_null,
       MIN(`timeline_third_party_proceeds_received_date`) AS min_dt, MAX(`timeline_third_party_proceeds_received_date`) AS max_dt
FROM   bpms.sync_loan_foreclosure;
```

<!-- FS-CARDS:2.3 END -->



> **Judgement-related fields special note** (ETL code + MCP data double-confirmed):
>
> | Newrez Field | ETL Intermediate Name | Business Meaning | BPS Destination |
> |---|---|---|---|
> | `fcjudgmenthearingscheduled` | `fcjudgment_hearing_scheduled` | **Scheduled date** of the foreclosure judgment hearing / sale confirmation hearing (future planned event); BPS Stage JUDGEMENT classification trigger | `judgement_start_date` (aggregate page), `timeline_judgement_date` (detail page) |
> | `fcjudgmententered` | `fcjudgment_end_date` | Date the court **formally entered** (recorded) the judgment (completed legal fact); ~11-day gap from `fcjudgmenthearingscheduled` is NOT an ETL delay — they measure entirely different time points | ETL intermediate table; used for `actual_judgement_hearing_set_days` calculation |
>
> ETL code confirmed: `fc.fcjudgment_hearing_scheduled AS timeline_judgement_date` (`basic_data_pool_config.py`)

### 2.4 Hold Slot Fields (P1 — Hold Panel History Records)

Newrez provides up to 3 slots, each with 4 fields. BPS appends a new row on each change, accumulating full Hold history.

<!-- FS-CARDS:2.4 START -->
##### `hold_1_description` · P1 · Hold Slot Fields

| Attribute | Value |
|---|---|
| Newrez Raw Field | `fchold1description` |
| Data Type | VARCHAR |
| Business Meaning | Hold slot 1 reason text (e.g., "Loss Mitigation Workout" / "Court Delay"); free-form text; maps to BPS Hold panel Description column |
| Format / Allowed Values | Text |
| Typical Value | Loss Mitigation Workout |
| BPS Panel / Function | Hold panel `description` |
| Newrez → BPS Rule | 3 slots UNPIVOT-merged → description (one row appended per slot, full history) |
| Newrez Status | ✅ 89.6% |
| Newrez Verify Result | [data_date 2026-06-01] Loss Mitigation Workout:21 \| Awaiting Funds to Post:16 \| Delinquency Review:12 \| Bankruptcy Filed:6 \| Hearing Set:4 \| Court Delay:4 \| Client Document Execution:4 \| Service Delay:4 \| Note Possession Confirmation:3 \| Title Resolution:3 \| Original Note:2 \| Allonge of Note:1 \| Service By Publication:1 \| Guaranty Agreement:1 \| Demand Letter Review:1 \| Awaiting Escrow Analysis:1 \| Moratorium:1 \| Mediation Hearing:1 \| FC Payment Research/Dispute:1 \| ACT(PA) Letter/Demand Letter/NOI Expiration:1 \| Original Assignment:1 |
| BPS Verify Result | [BPS prod \| data date fctrdt≤2026-06-01 \| ETL load 2026-06-03] Loss Mitigation Workout:63 \| Service Delay:48 \| ∅NULL:44 \| Client Document Execution:29 \| Court Delay:23 \| Awaiting Funds to Post:20 \| ACT(PA) Letter/Demand Letter/NOI Expiration:18 \| Hearing Set:17 \| Mediation Hearing:13 \| Delinquency Review:11 \| Original Note:10 \| Title Resolution:9 \| Note Possession Confirmation:8 \| Bankruptcy Filed:8 \| Copy of Power of Attorney:7 \| Copy of Payment History:5 \| Original Assignment:5 \| Demand Letter Review:4 \| Service By Publication:4 \| Copy of Periodic Statement:4 \| Pending Prior Servicer Doc(s):2 \| Awaiting Escrow Analysis:2 \| Soldiers and Sailors Relief Act:2 \| Allonge of Note:2 \| FC Payment Research/Dispute:2 \| +15 values, 1 row each:15 |

Newrez Verify SQL:
```sql
-- Verify against mysql_dev, data date 2026-06-01
SELECT dataasof AS data_date, fchold1description AS val, COUNT(*) AS cnt
FROM   newrez.portnewrezfc
WHERE  dataasof = '2026-06-01'
  AND  fchold1description IS NOT NULL AND fchold1description != ''
GROUP  BY dataasof, fchold1description ORDER BY cnt DESC LIMIT 30;
```

BPS Verify SQL (prod, read-only):
```sql
-- Verify against prod bpms (read-only)
SELECT '2026-06-01' AS data_date, `description` AS val, COUNT(*) AS cnt
FROM   bpms.sync_loan_foreclosure_hold
GROUP  BY `description` ORDER BY cnt DESC;
```

##### `hold_1_start_date` · P1 · Hold Slot Fields

| Attribute | Value |
|---|---|
| Newrez Raw Field | `fchold1startdate` |
| Data Type | DATE |
| Business Meaning | Hold 1 start date; also the BPS extraction filter condition (`fchold1startdate IS NOT NULL` required for ingestion) |
| Format / Allowed Values | YYYY-MM-DD |
| Typical Value | 2024-01-05 |
| BPS Panel / Function | Hold panel `description_start_date` |
| Newrez → BPS Rule | Direct copy (fchold1startdate → description_start_date) |
| Newrez Status | ✅ (in sync with description) |
| Newrez Verify Result | [data_date 2026-06-01] 2025-11-06 \| 2026-05-28 \| 2026-05-09 \| 2026-05-06 \| 2026-05-02 \| 2026-03-04 \| 2026-03-13 \| 2026-04-29 \| 2025-11-01 \| 2026-05-28 (10 rows) |
| BPS Verify Result | [BPS prod \| data date fctrdt≤2026-06-01 \| ETL load 2026-06-03] non-null 375/375 \| range 2019-10-24~2026-06-01 |

Newrez Verify SQL:
```sql
-- Verify against mysql_dev, data date 2026-06-01
SELECT loanid, dataasof, fchold1startdate
FROM   newrez.portnewrezfc
WHERE  dataasof = '2026-06-01'
  AND  fchold1startdate IS NOT NULL
LIMIT  10;
```

BPS Verify SQL (prod, read-only):
```sql
-- Verify against prod bpms (read-only)
SELECT '2026-06-01' AS data_date, COUNT(*) AS total, COUNT(`description_start_date`) AS non_null,
       MIN(`description_start_date`) AS min_dt, MAX(`description_start_date`) AS max_dt
FROM   bpms.sync_loan_foreclosure_hold;
```

##### `hold_1_end_date` · P1 · Hold Slot Fields

| Attribute | Value |
|---|---|
| Newrez Raw Field | `fchold1enddate` |
| Data Type | DATE |
| Business Meaning | Hold 1 end date; NULL means this Hold is still active |
| Format / Allowed Values | YYYY-MM-DD |
| Typical Value | 2024-03-15 |
| BPS Panel / Function | Hold panel `description_end_date` (NULL = still active) |
| Newrez → BPS Rule | Direct copy (fchold1enddate → description_end_date; NULL=still active) |
| Newrez Status | ✅ |
| Newrez Verify Result | [data_date 2026-06-01] 2025-11-07 \| 2026-05-11 \| 2026-05-07 \| 2026-05-05 \| 2026-03-10 \| 2025-11-11 \| 2026-05-21 \| 2026-03-27 \| 2025-08-22 \| 2025-08-14 (10 rows) |
| BPS Verify Result | [BPS prod \| data date fctrdt≤2026-06-01 \| ETL load 2026-06-03] non-null 357/375 \| range 2019-11-15~2026-06-01 |

Newrez Verify SQL:
```sql
-- Verify against mysql_dev, data date 2026-06-01
SELECT loanid, dataasof, fchold1enddate
FROM   newrez.portnewrezfc
WHERE  dataasof = '2026-06-01'
  AND  fchold1enddate IS NOT NULL
LIMIT  10;
```

BPS Verify SQL (prod, read-only):
```sql
-- Verify against prod bpms (read-only)
SELECT '2026-06-01' AS data_date, COUNT(*) AS total, COUNT(`description_end_date`) AS non_null,
       MIN(`description_end_date`) AS min_dt, MAX(`description_end_date`) AS max_dt
FROM   bpms.sync_loan_foreclosure_hold;
```

##### `hold_1_projected_end_date` · P2 · Hold Slot Fields

| Attribute | Value |
|---|---|
| Newrez Raw Field | `fchold1projectedenddate` |
| Data Type | DATE |
| Business Meaning | Hold 1 projected end date; used in calculation: `variance_estimated_hold_days = MAX(slot1/2/3 projected) − today NY` |
| Format / Allowed Values | YYYY-MM-DD |
| Typical Value | 2024-03-20 |
| BPS Panel / Function | `variance_estimated_hold_days` calculation (MAX(slot 1/2/3 projected end) − today) |
| Newrez → BPS Rule | N/A — BPS hold table has no projected-end column |
| Newrez Status | ✅ |
| Newrez Verify Result | [data_date 2026-06-01] 2026-01-05 \| 2026-07-27 \| 2026-07-08 \| 2026-07-05 \| 2026-07-01 \| 2026-05-03 \| 2026-06-05 \| 2026-06-28 \| 2025-11-08 \| 2026-06-18 (10 rows) |
| BPS Verify Result | N/A — not mapped to a BPS FCL sync table (see Newrez → BPS Rule) |

Newrez Verify SQL:
```sql
-- Verify against mysql_dev, data date 2026-06-01
SELECT loanid, dataasof, fchold1projectedenddate
FROM   newrez.portnewrezfc
WHERE  dataasof = '2026-06-01'
  AND  fchold1projectedenddate IS NOT NULL
LIMIT  10;
```

##### `hold_2_description` · P1 · Hold Slot Fields

| Attribute | Value |
|---|---|
| Newrez Raw Field | `fchold2description` |
| Data Type | VARCHAR |
| Business Meaning | Hold slot 2 reason text (used when multiple concurrent Holds exist in the same period) |
| Format / Allowed Values | Text |
| Typical Value | Loss Mitigation Workout |
| BPS Panel / Function | Same as slot 1 (slot 2) |
| Newrez → BPS Rule | 3 slots UNPIVOT-merged → description (same as hold_1) |
| Newrez Status | ✅ 69.8% |
| Newrez Verify Result | [data_date 2026-06-01] Loss Mitigation Workout:16 \| Client Document Execution:9 \| Court Delay:8 \| ACT(PA) Letter/Demand Letter/NOI Expiration:7 \| Awaiting Funds to Post:6 \| Delinquency Review:5 \| Service Delay:4 \| Hearing Set:4 \| Bankruptcy Filed:3 \| Original Note:2 \| Title Resolution:2 \| Copy of Payment History:2 \| Note Possession Confirmation:1 \| Copy of Periodic Statement:1 \| Mediation Hearing:1 \| Allonge of Note:1 \| FC Escrow/Corp Breakdown Needed:1 \| HAF - Homeowner Assistance Fund:1 |
| BPS Verify Result | [BPS prod \| data date fctrdt≤2026-06-01 \| ETL load 2026-06-03] Loss Mitigation Workout:63 \| Service Delay:48 \| ∅NULL:44 \| Client Document Execution:29 \| Court Delay:23 \| Awaiting Funds to Post:20 \| ACT(PA) Letter/Demand Letter/NOI Expiration:18 \| Hearing Set:17 \| Mediation Hearing:13 \| Delinquency Review:11 \| Original Note:10 \| Title Resolution:9 \| Note Possession Confirmation:8 \| Bankruptcy Filed:8 \| Copy of Power of Attorney:7 \| Copy of Payment History:5 \| Original Assignment:5 \| Demand Letter Review:4 \| Service By Publication:4 \| Copy of Periodic Statement:4 \| Pending Prior Servicer Doc(s):2 \| Awaiting Escrow Analysis:2 \| Soldiers and Sailors Relief Act:2 \| Allonge of Note:2 \| FC Payment Research/Dispute:2 \| +15 values, 1 row each:15 |

Newrez Verify SQL:
```sql
-- Verify against mysql_dev, data date 2026-06-01
SELECT dataasof AS data_date, fchold2description AS val, COUNT(*) AS cnt
FROM   newrez.portnewrezfc
WHERE  dataasof = '2026-06-01'
  AND  fchold2description IS NOT NULL AND fchold2description != ''
GROUP  BY dataasof, fchold2description ORDER BY cnt DESC LIMIT 30;
```

BPS Verify SQL (prod, read-only):
```sql
-- Verify against prod bpms (read-only)
SELECT '2026-06-01' AS data_date, `description` AS val, COUNT(*) AS cnt
FROM   bpms.sync_loan_foreclosure_hold
GROUP  BY `description` ORDER BY cnt DESC;
```

##### `hold_2_start_date` · P1 · Hold Slot Fields

| Attribute | Value |
|---|---|
| Newrez Raw Field | `fchold2startdate` |
| Data Type | DATE |
| Business Meaning | Hold 2 start date |
| Format / Allowed Values | YYYY-MM-DD |
| Typical Value | 2024-01-05 |
| BPS Panel / Function | Same |
| Newrez → BPS Rule | Direct copy (fchold2startdate → description_start_date) |
| Newrez Status | ✅ |
| Newrez Verify Result | [data_date 2026-06-01] 2025-11-06 \| 2026-05-28 \| 2026-05-09 \| 2026-05-06 \| 2026-05-02 \| 2026-03-04 \| 2026-03-13 \| 2026-04-28 \| 2025-10-24 \| 2026-05-04 (10 rows) |
| BPS Verify Result | [BPS prod \| data date fctrdt≤2026-06-01 \| ETL load 2026-06-03] non-null 375/375 \| range 2019-10-24~2026-06-01 |

Newrez Verify SQL:
```sql
-- Verify against mysql_dev, data date 2026-06-01
SELECT loanid, dataasof, fchold2startdate
FROM   newrez.portnewrezfc
WHERE  dataasof = '2026-06-01'
  AND  fchold2startdate IS NOT NULL
LIMIT  10;
```

BPS Verify SQL (prod, read-only):
```sql
-- Verify against prod bpms (read-only)
SELECT '2026-06-01' AS data_date, COUNT(*) AS total, COUNT(`description_start_date`) AS non_null,
       MIN(`description_start_date`) AS min_dt, MAX(`description_start_date`) AS max_dt
FROM   bpms.sync_loan_foreclosure_hold;
```

##### `hold_2_end_date` · P1 · Hold Slot Fields

| Attribute | Value |
|---|---|
| Newrez Raw Field | `fchold2enddate` |
| Data Type | DATE |
| Business Meaning | Hold 2 end date; NULL means still active |
| Format / Allowed Values | YYYY-MM-DD |
| Typical Value | 2024-03-15 |
| BPS Panel / Function | Same |
| Newrez → BPS Rule | Direct copy (fchold2enddate → description_end_date) |
| Newrez Status | ✅ |
| Newrez Verify Result | [data_date 2026-06-01] 2025-11-07 \| 2026-05-11 \| 2026-05-07 \| 2026-05-05 \| 2026-03-10 \| 2026-05-08 \| 2026-04-29 \| 2025-10-30 \| 2026-05-05 \| 2026-05-21 (10 rows) |
| BPS Verify Result | [BPS prod \| data date fctrdt≤2026-06-01 \| ETL load 2026-06-03] non-null 357/375 \| range 2019-11-15~2026-06-01 |

Newrez Verify SQL:
```sql
-- Verify against mysql_dev, data date 2026-06-01
SELECT loanid, dataasof, fchold2enddate
FROM   newrez.portnewrezfc
WHERE  dataasof = '2026-06-01'
  AND  fchold2enddate IS NOT NULL
LIMIT  10;
```

BPS Verify SQL (prod, read-only):
```sql
-- Verify against prod bpms (read-only)
SELECT '2026-06-01' AS data_date, COUNT(*) AS total, COUNT(`description_end_date`) AS non_null,
       MIN(`description_end_date`) AS min_dt, MAX(`description_end_date`) AS max_dt
FROM   bpms.sync_loan_foreclosure_hold;
```

##### `hold_2_projected_end_date` · P2 · Hold Slot Fields

| Attribute | Value |
|---|---|
| Newrez Raw Field | `fchold2projectedenddate` |
| Data Type | DATE |
| Business Meaning | Hold 2 projected end date; participates in MAX calculation alongside slot 1 |
| Format / Allowed Values | YYYY-MM-DD |
| Typical Value | 2024-03-20 |
| BPS Panel / Function | Same |
| Newrez → BPS Rule | N/A — BPS hold table has no projected-end column |
| Newrez Status | ✅ |
| Newrez Verify Result | [data_date 2026-06-01] 2026-01-05 \| 2026-07-27 \| 2026-07-08 \| 2026-07-05 \| 2026-07-01 \| 2026-05-03 \| 2026-05-08 \| 2026-05-28 \| 2025-10-30 \| 2026-06-03 (10 rows) |
| BPS Verify Result | N/A — not mapped to a BPS FCL sync table (see Newrez → BPS Rule) |

Newrez Verify SQL:
```sql
-- Verify against mysql_dev, data date 2026-06-01
SELECT loanid, dataasof, fchold2projectedenddate
FROM   newrez.portnewrezfc
WHERE  dataasof = '2026-06-01'
  AND  fchold2projectedenddate IS NOT NULL
LIMIT  10;
```

##### `hold_3_description` · P1 · Hold Slot Fields

| Attribute | Value |
|---|---|
| Newrez Raw Field | `fchold3description` |
| Data Type | VARCHAR |
| Business Meaning | Hold slot 3 reason text (third concurrent Hold) |
| Format / Allowed Values | Text |
| Typical Value | Loss Mitigation Workout |
| BPS Panel / Function | Same (slot 3) |
| Newrez → BPS Rule | 3 slots UNPIVOT-merged → description (same as hold_1) |
| Newrez Status | ✅ 52.6% |
| Newrez Verify Result | [data_date 2026-06-01] Client Document Execution:8 \| Loss Mitigation Workout:6 \| Court Delay:5 \| Mediation Hearing:3 \| Original Note:3 \| Hearing Set:3 \| Service Delay:3 \| Allonge of Note:2 \| Note Possession Confirmation:2 \| Bankruptcy Filed:2 \| Title Resolution:2 \| ACT(PA) Letter/Demand Letter/NOI Expiration:2 \| Service By Publication:2 \| Copy of Payment History:1 \| Awaiting Escrow Analysis:1 \| Delinquency Review:1 \| Copy of Note:1 \| FC Payment Research/Dispute:1 \| MERS Assignment Needed:1 \| Guaranty Agreement:1 \| Awaiting Funds to Post:1 \| FEMA Hold:1 \| Copy of Power of Attorney:1 \| COVID Affected:1 \| Court Delay Mid Term (46 - 90 Days):1 |
| BPS Verify Result | [BPS prod \| data date fctrdt≤2026-06-01 \| ETL load 2026-06-03] Loss Mitigation Workout:63 \| Service Delay:48 \| ∅NULL:44 \| Client Document Execution:29 \| Court Delay:23 \| Awaiting Funds to Post:20 \| ACT(PA) Letter/Demand Letter/NOI Expiration:18 \| Hearing Set:17 \| Mediation Hearing:13 \| Delinquency Review:11 \| Original Note:10 \| Title Resolution:9 \| Note Possession Confirmation:8 \| Bankruptcy Filed:8 \| Copy of Power of Attorney:7 \| Copy of Payment History:5 \| Original Assignment:5 \| Demand Letter Review:4 \| Service By Publication:4 \| Copy of Periodic Statement:4 \| Pending Prior Servicer Doc(s):2 \| Awaiting Escrow Analysis:2 \| Soldiers and Sailors Relief Act:2 \| Allonge of Note:2 \| FC Payment Research/Dispute:2 \| +15 values, 1 row each:15 |

Newrez Verify SQL:
```sql
-- Verify against mysql_dev, data date 2026-06-01
SELECT dataasof AS data_date, fchold3description AS val, COUNT(*) AS cnt
FROM   newrez.portnewrezfc
WHERE  dataasof = '2026-06-01'
  AND  fchold3description IS NOT NULL AND fchold3description != ''
GROUP  BY dataasof, fchold3description ORDER BY cnt DESC LIMIT 30;
```

BPS Verify SQL (prod, read-only):
```sql
-- Verify against prod bpms (read-only)
SELECT '2026-06-01' AS data_date, `description` AS val, COUNT(*) AS cnt
FROM   bpms.sync_loan_foreclosure_hold
GROUP  BY `description` ORDER BY cnt DESC;
```

##### `hold_3_start_date` · P1 · Hold Slot Fields

| Attribute | Value |
|---|---|
| Newrez Raw Field | `fchold3startdate` |
| Data Type | DATE |
| Business Meaning | Hold 3 start date |
| Format / Allowed Values | YYYY-MM-DD |
| Typical Value | 2024-01-05 |
| BPS Panel / Function | Same |
| Newrez → BPS Rule | Direct copy (fchold3startdate → description_start_date) |
| Newrez Status | ✅ |
| Newrez Verify Result | [data_date 2026-06-01] 2026-05-26 \| 2026-04-24 \| 2026-02-03 \| 2026-04-27 \| 2026-02-20 \| 2026-01-21 \| 2026-04-27 \| 2025-10-06 \| 2026-03-27 \| 2026-02-18 (10 rows) |
| BPS Verify Result | [BPS prod \| data date fctrdt≤2026-06-01 \| ETL load 2026-06-03] non-null 375/375 \| range 2019-10-24~2026-06-01 |

Newrez Verify SQL:
```sql
-- Verify against mysql_dev, data date 2026-06-01
SELECT loanid, dataasof, fchold3startdate
FROM   newrez.portnewrezfc
WHERE  dataasof = '2026-06-01'
  AND  fchold3startdate IS NOT NULL
LIMIT  10;
```

BPS Verify SQL (prod, read-only):
```sql
-- Verify against prod bpms (read-only)
SELECT '2026-06-01' AS data_date, COUNT(*) AS total, COUNT(`description_start_date`) AS non_null,
       MIN(`description_start_date`) AS min_dt, MAX(`description_start_date`) AS max_dt
FROM   bpms.sync_loan_foreclosure_hold;
```

##### `hold_3_end_date` · P1 · Hold Slot Fields

| Attribute | Value |
|---|---|
| Newrez Raw Field | `fchold3enddate` |
| Data Type | DATE |
| Business Meaning | Hold 3 end date; NULL means still active |
| Format / Allowed Values | YYYY-MM-DD |
| Typical Value | 2024-03-15 |
| BPS Panel / Function | Same |
| Newrez → BPS Rule | Direct copy (fchold3enddate → description_end_date) |
| Newrez Status | ✅ |
| Newrez Verify Result | [data_date 2026-06-01] 2026-04-27 \| 2026-04-22 \| 2026-04-30 \| 2026-02-24 \| 2026-04-09 \| 2026-04-27 \| 2025-10-23 \| 2026-04-14 \| 2026-03-27 \| 2025-12-26 (10 rows) |
| BPS Verify Result | [BPS prod \| data date fctrdt≤2026-06-01 \| ETL load 2026-06-03] non-null 357/375 \| range 2019-11-15~2026-06-01 |

Newrez Verify SQL:
```sql
-- Verify against mysql_dev, data date 2026-06-01
SELECT loanid, dataasof, fchold3enddate
FROM   newrez.portnewrezfc
WHERE  dataasof = '2026-06-01'
  AND  fchold3enddate IS NOT NULL
LIMIT  10;
```

BPS Verify SQL (prod, read-only):
```sql
-- Verify against prod bpms (read-only)
SELECT '2026-06-01' AS data_date, COUNT(*) AS total, COUNT(`description_end_date`) AS non_null,
       MIN(`description_end_date`) AS min_dt, MAX(`description_end_date`) AS max_dt
FROM   bpms.sync_loan_foreclosure_hold;
```

##### `hold_3_projected_end_date` · P2 · Hold Slot Fields

| Attribute | Value |
|---|---|
| Newrez Raw Field | `fchold3projectedenddate` |
| Data Type | DATE |
| Business Meaning | Hold 3 projected end date; participates in MAX calculation alongside slots 1 and 2 |
| Format / Allowed Values | YYYY-MM-DD |
| Typical Value | 2024-03-20 |
| BPS Panel / Function | Same |
| Newrez → BPS Rule | N/A — BPS hold table has no projected-end column |
| Newrez Status | ✅ |
| Newrez Verify Result | [data_date 2026-06-01] 2026-07-26 \| 2026-05-01 \| 2026-05-16 \| 2026-04-30 \| 2026-04-13 \| 2026-04-13 \| 2026-05-27 \| 2025-10-31 \| 2026-05-26 \| 2026-04-19 (10 rows) |
| BPS Verify Result | N/A — not mapped to a BPS FCL sync table (see Newrez → BPS Rule) |

Newrez Verify SQL:
```sql
-- Verify against mysql_dev, data date 2026-06-01
SELECT loanid, dataasof, fchold3projectedenddate
FROM   newrez.portnewrezfc
WHERE  dataasof = '2026-06-01'
  AND  fchold3projectedenddate IS NOT NULL
LIMIT  10;
```

##### `hold_1_modified_date` · P2 · Hold Slot Fields

| Attribute | Value |
|---|---|
| Newrez Raw Field | `holdmodified` |
| Data Type | DATE |
| Business Meaning |  |
| Format / Allowed Values | YYYY-MM-DD |
| Typical Value | 2024-02-20 |
| BPS Panel / Function | Hold slot 1 last modified date; tracks when this hold was last updated |
| Newrez → BPS Rule | N/A — BPS hold table has no modified column |
| Newrez Status | ✅ 82.1% |
| Newrez Verify Result | [data_date 2026-06-01] 2025-11-07 \| 2026-05-28 \| 2026-05-11 \| 2026-05-07 \| 2026-05-05 \| 2026-03-10 \| 2026-05-12 \| 2026-04-29 \| 2025-11-11 \| 2026-05-29 (10 rows) |
| BPS Verify Result | N/A — not mapped to a BPS FCL sync table (see Newrez → BPS Rule) |

Newrez Verify SQL:
```sql
-- Verify against mysql_dev, data date 2026-06-01
SELECT loanid, dataasof, holdmodified
FROM   newrez.portnewrezfc
WHERE  dataasof = '2026-06-01'
  AND  holdmodified IS NOT NULL
LIMIT  10;
```

##### `hold_2_modified_date` · P2 · Hold Slot Fields

| Attribute | Value |
|---|---|
| Newrez Raw Field | `holdmodified2` |
| Data Type | DATE |
| Business Meaning |  |
| Format / Allowed Values | YYYY-MM-DD |
| Typical Value | 2024-02-20 |
| BPS Panel / Function | Hold slot 2 last modified date |
| Newrez → BPS Rule | N/A — BPS hold table has no modified column |
| Newrez Status | ✅ 82.1% |
| Newrez Verify Result | [data_date 2026-06-01] 2025-11-07 \| 2026-05-28 \| 2026-05-11 \| 2026-05-07 \| 2026-05-05 \| 2026-03-10 \| 2026-05-08 \| 2026-04-29 \| 2025-10-30 \| 2026-05-05 (10 rows) |
| BPS Verify Result | N/A — not mapped to a BPS FCL sync table (see Newrez → BPS Rule) |

Newrez Verify SQL:
```sql
-- Verify against mysql_dev, data date 2026-06-01
SELECT loanid, dataasof, holdmodified2
FROM   newrez.portnewrezfc
WHERE  dataasof = '2026-06-01'
  AND  holdmodified2 IS NOT NULL
LIMIT  10;
```

##### `hold_3_modified_date` · P2 · Hold Slot Fields

| Attribute | Value |
|---|---|
| Newrez Raw Field | `holdmodified3` |
| Data Type | DATE |
| Business Meaning |  |
| Format / Allowed Values | YYYY-MM-DD |
| Typical Value | 2024-02-20 |
| BPS Panel / Function | Hold slot 3 last modified date |
| Newrez → BPS Rule | N/A — BPS hold table has no modified column |
| Newrez Status | ✅ 82.1% |
| Newrez Verify Result | [data_date 2026-06-01] 2026-05-27 \| 2026-04-27 \| 2026-04-22 \| 2026-04-27 \| 2026-02-26 \| 2026-04-09 \| 2026-04-27 \| 2025-10-23 \| 2026-04-14 \| 2026-03-27 (10 rows) |
| BPS Verify Result | N/A — not mapped to a BPS FCL sync table (see Newrez → BPS Rule) |

Newrez Verify SQL:
```sql
-- Verify against mysql_dev, data date 2026-06-01
SELECT loanid, dataasof, holdmodified3
FROM   newrez.portnewrezfc
WHERE  dataasof = '2026-06-01'
  AND  holdmodified3 IS NOT NULL
LIMIT  10;
```

<!-- FS-CARDS:2.4 END -->



> **Architecture note**: Newrez's 3 hold slots represent the **current snapshot** of active/recent holds. On each daily BPS sync, if any hold field changes, a new row is appended to `sync_loan_foreclosure_hold`, accumulating the complete Hold history (e.g., loanid=7727000088 has 7 historical records while Newrez currently shows only 1 active slot).

### 2.5 Bid and Sale Fields (P1/P2 — Bid Approval Panel)

<!-- FS-CARDS:2.5 START -->
##### `bid_amount` · P2 · Bid and Sale Fields

| Attribute | Value |
|---|---|
| Newrez Raw Field | `fcbidamount` |
| Data Type | DECIMAL |
| Business Meaning | Servicer-reported foreclosure bid amount; only populated when auction is imminent (~9% fill rate in active FCL) |
| Format / Allowed Values | Positive number (USD) |
| Typical Value | 160000.00 |
| BPS Panel / Function | Bid Approval `bid_approval_bid_amount`; FCL Summary `summary_foreclosure_bid_amount` |
| Newrez → BPS Rule | Direct copy (fcbidamount → summary_foreclosure_bid_amount / summary_srv_fc_bid_amount) |
| Newrez Status | ✅ 9.0% |
| Newrez Verify Result | [data_date 2026-06-01] 288000.0000000000000000 \| 154591.0100000000000000 \| 136392.4400000000000000 \| 164738.0000000000000000 \| 250540.4900000000000000 \| 355000.0000000000000000 \| 301500.0000000000000000 \| 260555.0000000000000000 \| 390832.5000000000000000 \| 125366.7300000000000000 (10 rows) |
| BPS Verify Result | [BPS prod \| data date 2026-06-01(main table has no embedded as-of, same ETL cycle as Newrez source) \| ETL load 2026-06-03] non-null 16/89 \| range 90000~543305.96 \| avg 265705.54 |

Newrez Verify SQL:
```sql
-- Verify against mysql_dev, data date 2026-06-01
SELECT loanid, dataasof, fcbidamount
FROM   newrez.portnewrezfc
WHERE  dataasof = '2026-06-01'
  AND  fcbidamount IS NOT NULL
LIMIT  10;
```

BPS Verify SQL (prod, read-only):
```sql
-- Verify against prod bpms (read-only)
SELECT '2026-06-01' AS data_date, COUNT(*) AS total, COUNT(`summary_foreclosure_bid_amount`) AS non_null,
       MIN(`summary_foreclosure_bid_amount`) AS min_v, MAX(`summary_foreclosure_bid_amount`) AS max_v, ROUND(AVG(`summary_foreclosure_bid_amount`),2) AS avg_v
FROM   bpms.sync_loan_foreclosure;
```

##### `approved_bid_price` · P2 · Bid and Sale Fields

| Attribute | Value |
|---|---|
| Newrez Raw Field | `fcapprbidprice` |
| Data Type | DECIMAL |
| Business Meaning | BPS-approved bid amount after internal bid approval workflow; may differ from `fcbidamount` |
| Format / Allowed Values | Positive number (USD) |
| Typical Value | 162000.00 |
| BPS Panel / Function | Bid Approval `bid_approval_bid_amount` (BPS approval perspective) |
| Newrez → BPS Rule | Direct copy (fcapprbidprice → bid_approval_bid_amount; Bid Approval panel) |
| Newrez Status | ✅ 8.9% |
| Newrez Verify Result | [data_date 2026-06-01] 288000.0000000000000000 \| 136392.4400000000000000 \| 164738.0000000000000000 \| 250540.4900000000000000 \| 355000.0000000000000000 \| 301500.0000000000000000 \| 260555.0000000000000000 \| 390832.5000000000000000 \| 123294.5700000000000000 \| 230805.9400000000000000 (10 rows) |
| BPS Verify Result | [BPS prod \| data date 2026-06-01(main table has no embedded as-of, same ETL cycle as Newrez source) \| ETL load 2026-06-03] non-null 16/89 \| range 90000~543305.96 \| avg 265705.54 |

Newrez Verify SQL:
```sql
-- Verify against mysql_dev, data date 2026-06-01
SELECT loanid, dataasof, fcapprbidprice
FROM   newrez.portnewrezfc
WHERE  dataasof = '2026-06-01'
  AND  fcapprbidprice IS NOT NULL
LIMIT  10;
```

BPS Verify SQL (prod, read-only):
```sql
-- Verify against prod bpms (read-only)
SELECT '2026-06-01' AS data_date, COUNT(*) AS total, COUNT(`bid_approval_bid_amount`) AS non_null,
       MIN(`bid_approval_bid_amount`) AS min_v, MAX(`bid_approval_bid_amount`) AS max_v, ROUND(AVG(`bid_approval_bid_amount`),2) AS avg_v
FROM   bpms.sync_loan_foreclosure;
```

##### `sale_amount` · P1 · Bid and Sale Fields

| Attribute | Value |
|---|---|
| Newrez Raw Field | `fcsaleamount` |
| Data Type | DECIMAL |
| Business Meaning | Actual foreclosure auction sale amount; fill rate (4.7%) exceeds `fcsalehelddate` (2.1%), suggesting a data sequencing issue (see doc 13 Q9) |
| Format / Allowed Values | Positive number (USD) |
| Typical Value | 170000.00 |
| BPS Panel / Function | FCL Summary `summary_foreclosure_sale_amount`; ⚠️ fill rate (4.7%) > sale_held (2.1%), possible sequencing issue (see doc 13 Q9) |
| Newrez → BPS Rule | Direct copy (fcsaleamount → summary_foreclosure_sale_amount) |
| Newrez Status | ⚠️ 4.7% |
| Newrez Verify Result | [data_date 2026-06-01] 288000.0000000000000000 \| 165900.0000000000000000 \| 164738.0000000000000000 \| 200100.0000000000000000 \| 260555.0000000000000000 \| 357200.0000000000000000 \| 203122.0000000000000000 \| 274000.0000000000000000 \| 400000.0000000000000000 \| 90001.0000000000000000 (10 rows) |
| BPS Verify Result | [BPS prod \| data date 2026-06-01(main table has no embedded as-of, same ETL cycle as Newrez source) \| ETL load 2026-06-03] non-null 10/89 \| range 90001~400000 \| avg 240361.60 |

Newrez Verify SQL:
```sql
-- Verify against mysql_dev, data date 2026-06-01
SELECT loanid, dataasof, fcsaleamount
FROM   newrez.portnewrezfc
WHERE  dataasof = '2026-06-01'
  AND  fcsaleamount IS NOT NULL
LIMIT  10;
```

BPS Verify SQL (prod, read-only):
```sql
-- Verify against prod bpms (read-only)
SELECT '2026-06-01' AS data_date, COUNT(*) AS total, COUNT(`summary_foreclosure_sale_amount`) AS non_null,
       MIN(`summary_foreclosure_sale_amount`) AS min_v, MAX(`summary_foreclosure_sale_amount`) AS max_v, ROUND(AVG(`summary_foreclosure_sale_amount`),2) AS avg_v
FROM   bpms.sync_loan_foreclosure;
```

<!-- FS-CARDS:2.5 END -->



---

### 2.6 Loan Attribute and Risk Enhancement Fields (P1/P2 — Newrez-Provided but Not Yet Utilized)

> **Source**: Fields in this section come from `newrez.portnewrezfc` and `newrez.portnewrezgeneral`. MCP live measurements (2026-05) confirm Newrez provides these fields, but the current ETL and BPS system does not read or utilize them.  
> **BPS display**: These fields currently have no direct BPS panel mapping. Their inclusion in the interface standard serves two purposes: (1) reserve data sources for new-system ETL redesign; (2) provide a reference baseline for per-Servicer gap analysis.  
> **Data basis**: Fill rates from MCP query on active FCL latest snapshot (39-loan sample).

<!-- FS-CARDS:2.6 START -->
##### `investor_loan_id` · P1 · Loan Attribute and Risk Enhancement Fields

| Attribute | Value |
|---|---|
| Newrez Raw Field | `investorloanid` |
| Data Type | VARCHAR |
| Business Meaning | Investor (e.g., Fannie Mae, Freddie Mac, private fund) loan number; different from system `loan_id` (our primary key) and `servicer_loan_id` (Newrez internal ID); used for investor reporting reconciliation and loan tracking across Servicer transfers |
| Format / Allowed Values | Text |
| Typical Value | INV-20240110-088 |
| BPS Panel / Function |  |
| Newrez → BPS Rule | N/A — provided by Newrez but not yet used by the system (not in BPS sync tables) |
| Newrez Status | ✅ **100%** |
| Newrez Verify Result | [data_date 2026-06-01] 5087355 \| 5084227 \| 5085432 \| 5085637 \| 5084093 \| 5085003 \| 8195317 \| 5086934 \| 5084351 \| 5085356 (10 rows) |
| BPS Verify Result | N/A — not mapped to a BPS FCL sync table (see Newrez → BPS Rule) |

Newrez Verify SQL:
```sql
-- Verify against mysql_dev, data date 2026-06-01
SELECT loanid, dataasof, investorloanid
FROM   newrez.portnewrezfc
WHERE  dataasof = '2026-06-01'
  AND  investorloanid IS NOT NULL AND investorloanid != ''
LIMIT  10;
```

##### `lien_position` · P1 · Loan Attribute and Risk Enhancement Fields

| Attribute | Value |
|---|---|
| Newrez Raw Field | `jr_sr_lien_flag` (portnewrezfc) / `lienposition` (portnewrezgeneral) |
| Data Type | INT |
| Business Meaning | Lien position: 1=first lien (Senior, priority claim); 2=second lien (Junior). Junior Lien foreclosure requires monitoring Senior Lien FCL progress (SR lien tracking fields currently at 0% fill in Newrez sample); BPS should differentiate the two foreclosure workflows |
| Format / Allowed Values | Positive integer |
| Typical Value | 1 |
| BPS Panel / Function |  |
| Newrez → BPS Rule | N/A — provided by Newrez but not yet used by the system (not in BPS sync tables) |
| Newrez Status | ✅ **100%** (both tables) |
| Newrez Verify Result | [data_date 2026-06-01] 1:5025 \| 2:27 |
| BPS Verify Result | N/A — not mapped to a BPS FCL sync table (see Newrez → BPS Rule) |

Newrez Verify SQL:
```sql
-- Verify against mysql_dev, data date 2026-06-01
SELECT dataasof AS data_date, lienposition AS val, COUNT(*) AS cnt
FROM   newrez.portnewrezgeneral
WHERE  dataasof = '2026-06-01'
  AND  lienposition IS NOT NULL AND lienposition != ''
GROUP  BY dataasof, lienposition ORDER BY cnt DESC LIMIT 30;
```

##### `interest_paid_through_date` · P1 · Loan Attribute and Risk Enhancement Fields

| Attribute | Value |
|---|---|
| Newrez Raw Field | `interestpaidthroughdate` |
| Data Type | DATE |
| Business Meaning | Date through which borrower payments have been credited; difference from `report_date` (`dataasof`) is the true delinquency days; e.g., `interestpaidthroughdate=2025-10-01`, `dataasof=2026-05-24` → ~235 days delinquent; more direct than `days360(nextduedate, dataasof)` |
| Format / Allowed Values | YYYY-MM-DD |
| Typical Value | 2024-01-31 |
| BPS Panel / Function |  |
| Newrez → BPS Rule | N/A — provided by Newrez but not yet used by the system (not in BPS sync tables) |
| Newrez Status | ✅ **100%** |
| Newrez Verify Result | [data_date 2026-06-01] 2026-05-01 \| 2026-05-01 \| 2026-06-01 \| 2025-09-01 \| 2024-06-01 \| 2026-06-01 \| 2026-05-01 \| 2026-05-01 \| 2026-06-01 \| 2025-10-01 (10 rows) |
| BPS Verify Result | N/A — not mapped to a BPS FCL sync table (see Newrez → BPS Rule) |

Newrez Verify SQL:
```sql
-- Verify against mysql_dev, data date 2026-06-01
SELECT loanid, dataasof, interestpaidthroughdate
FROM   newrez.portnewrezgeneral
WHERE  dataasof = '2026-06-01'
  AND  interestpaidthroughdate IS NOT NULL
LIMIT  10;
```

##### `in_auction_flag` · P1 · Loan Attribute and Risk Enhancement Fields

| Attribute | Value |
|---|---|
| Newrez Raw Field | `inauctionflag` |
| Data Type | INT |
| Business Meaning | Whether loan is currently in the foreclosure auction process (scheduled or in progress); 7.7% of active FCL loans are flagged, indicating ~7% are at the final foreclosure stage requiring priority handling |
| Format / Allowed Values | Positive integer |
| Typical Value | 0 |
| BPS Panel / Function |  |
| Newrez → BPS Rule | N/A — provided by Newrez but not yet used by the system (not in BPS sync tables) |
| Newrez Status | ✅ 7.7% (high value when populated) |
| Newrez Verify Result | [data_date 2026-06-01] 0:5045 \| 1:7 |
| BPS Verify Result | N/A — not mapped to a BPS FCL sync table (see Newrez → BPS Rule) |

Newrez Verify SQL:
```sql
-- Verify against mysql_dev, data date 2026-06-01
SELECT dataasof AS data_date, inauctionflag, COUNT(*) AS cnt
FROM   newrez.portnewrezgeneral
WHERE  dataasof = '2026-06-01'
GROUP  BY dataasof, inauctionflag ORDER BY cnt DESC;
```

##### `borrower_deceased_flag` · P1 · Loan Attribute and Risk Enhancement Fields

| Attribute | Value |
|---|---|
| Newrez Raw Field | `borrowerdeceasedflag` |
| Data Type | INT |
| Business Meaning | Deceased borrower flag; deceased-borrower foreclosure requires notifying estate representative or heirs; some states have specific legal requirements; affects BPS operational workflow and compliance reporting |
| Format / Allowed Values | Positive integer |
| Typical Value | 0 |
| BPS Panel / Function |  |
| Newrez → BPS Rule | N/A — provided by Newrez but not yet used by the system (not in BPS sync tables) |
| Newrez Status | ✅ 5.1% (high impact when populated) |
| Newrez Verify Result | [data_date 2026-06-01] 0:5036 \| 1:16 |
| BPS Verify Result | N/A — not mapped to a BPS FCL sync table (see Newrez → BPS Rule) |

Newrez Verify SQL:
```sql
-- Verify against mysql_dev, data date 2026-06-01
SELECT dataasof AS data_date, borrowerdeceasedflag, COUNT(*) AS cnt
FROM   newrez.portnewrezgeneral
WHERE  dataasof = '2026-06-01'
GROUP  BY dataasof, borrowerdeceasedflag ORDER BY cnt DESC;
```

##### `reason_for_default` · P2 · Loan Attribute and Risk Enhancement Fields

| Attribute | Value |
|---|---|
| Newrez Raw Field | `reasonfordefault` |
| Data Type | VARCHAR |
| Business Meaning | Default root cause free text (Newrez format); used for: (1) LM program selection (unemployment → Forbearance; permanent income reduction → Modification); (2) batch risk classification; (3) investor reporting |
| Format / Allowed Values | Text |
| Typical Value | Unable to Contact Borrower |
| BPS Panel / Function |  |
| Newrez → BPS Rule | N/A — provided by Newrez but not yet used by the system (not in BPS sync tables) |
| Newrez Status | ✅ 46.2% |
| Newrez Verify Result | [data_date 2026-06-01] Unable to Contact Borrower:39 \| Reduction in Borrower's Income:9 \| Within Grace Period:8 \| Other/No applicable codes:6 \| Servicing Problems:3 \| Excessive Obligations:3 \| Death of Primary Borrower:3 \| Payment Dispute:2 \| Unemployment:2 \| Customer Pay Period:2 \| Illness of Borrower's Family Member:2 \| Tenant Not Paying:1 \| Overlooked:1 \| Illness of Primary Borrower:1 \| Inability to Rent Property:1 |
| BPS Verify Result | N/A — not mapped to a BPS FCL sync table (see Newrez → BPS Rule) |

Newrez Verify SQL:
```sql
-- Verify against mysql_dev, data date 2026-06-01
SELECT dataasof AS data_date, reasonfordefault AS val, COUNT(*) AS cnt
FROM   newrez.portnewrezgeneral
WHERE  dataasof = '2026-06-01'
  AND  reasonfordefault IS NOT NULL AND reasonfordefault != ''
GROUP  BY dataasof, reasonfordefault ORDER BY cnt DESC LIMIT 30;
```

##### `hold_1_comment` · P2 · Loan Attribute and Risk Enhancement Fields

| Attribute | Value |
|---|---|
| Newrez Raw Field | `fchold1comment` |
| Data Type | VARCHAR |
| Business Meaning | Hold slot 1 supplemental notes, adding context to the structured `hold_1_description`; typical content: bankruptcy case numbers, court continuance reasons, LM negotiation status |
| Format / Allowed Values | Text |
| Typical Value | Awaiting Bankruptcy Resolution |
| BPS Panel / Function |  |
| Newrez → BPS Rule | N/A — provided by Newrez but not yet used by the system (not in BPS sync tables) |
| Newrez Status | ✅ 82.1% |
| Newrez Verify Result | [data_date 2026-06-01] Funds received that could reinstate or payoff the loan: Unapplied balance: 0.00 Due Date: 12/01/2025 \| Delinquency Review \| Funds received that could reinstate or payoff the loan: Unapplied balance: 0.00 Due Date: 06/01/2026 \| Delinquency Review \| Delinquency Review \| Delinquency Review \| Praecipe to reinstate complaint received. Same will be sent to the sheriff to be included with service to effectuate completion. ETA for service completion is 3-4 weeks. Our firm last followed up for the needed affidavits on 5/8/26. Next update 6/5/26. \| Chapter 7 filed 04/27/2026. Case 2611770. \| Funds received that could reinstate or payoff the loan: Unapplied balance: 0.00 Due Date: 11/01/2025 \| Service still being attempted for The Unknown Tenant in Possession, all others have been served as of 5/28. Next follow up 6/11 eta for completion 6/18 (10 rows) |
| BPS Verify Result | N/A — not mapped to a BPS FCL sync table (see Newrez → BPS Rule) |

Newrez Verify SQL:
```sql
-- Verify against mysql_dev, data date 2026-06-01
SELECT loanid, dataasof, fchold1comment
FROM   newrez.portnewrezfc
WHERE  dataasof = '2026-06-01'
  AND  fchold1comment IS NOT NULL AND fchold1comment != ''
LIMIT  10;
```

##### `hold_2_comment` · P2 · Loan Attribute and Risk Enhancement Fields

| Attribute | Value |
|---|---|
| Newrez Raw Field | `fchold2comment` |
| Data Type | VARCHAR |
| Business Meaning | Hold slot 2 notes (same as above) |
| Format / Allowed Values | Text |
| Typical Value | Awaiting Court Scheduling |
| BPS Panel / Function |  |
| Newrez → BPS Rule | N/A — provided by Newrez but not yet used by the system (not in BPS sync tables) |
| Newrez Status | ✅ 82.1% |
| Newrez Verify Result | [data_date 2026-06-01] Delinquency Review \| Funds received that could reinstate or payoff the loan: Unapplied balance: 0.00 Due Date: 07/01/2026 \| Delinquency Review \| Funds received that could reinstate or payoff the loan: Unapplied balance: 0.00 Due Date: 06/01/2026 \| Funds received that could reinstate or payoff the loan: Unapplied balance: 0.00 Due Date: 06/01/2026 \| Funds received that could reinstate or payoff the loan: Unapplied balance: 0.00 Due Date: 04/08/2026 \| Service was initiated 3/13/26. We are currently pending the return of the affidavits of service. This process may take upwards of 45-60 days. Firm last followed up regarding same on 4/10/26. ETA for completion is 3-4 weeks. Next update 5/8/26. \| Pending signature required document to proceed with foreclosure action. \| Notice of Sale sent for filing 10/24/2025. ETA for first legal filing is 10/30/2025. Follo … |
| BPS Verify Result | N/A — not mapped to a BPS FCL sync table (see Newrez → BPS Rule) |

Newrez Verify SQL:
```sql
-- Verify against mysql_dev, data date 2026-06-01
SELECT loanid, dataasof, fchold2comment
FROM   newrez.portnewrezfc
WHERE  dataasof = '2026-06-01'
  AND  fchold2comment IS NOT NULL AND fchold2comment != ''
LIMIT  10;
```

##### `hold_3_comment` · P2 · Loan Attribute and Risk Enhancement Fields

| Attribute | Value |
|---|---|
| Newrez Raw Field | `fchold3comment` |
| Data Type | VARCHAR |
| Business Meaning | Hold slot 3 notes (same as above) |
| Format / Allowed Values | Text |
| Typical Value | — |
| BPS Panel / Function |  |
| Newrez → BPS Rule | N/A — provided by Newrez but not yet used by the system (not in BPS sync tables) |
| Newrez Status | ✅ 82.1% |
| Newrez Verify Result | [data_date 2026-06-01] Our firm is pending receipt of the original note to proceed with the foreclosure, once received we will be able to prepare complaint for verification. \| Delay Reason: Pending Recording, Hold Start Date: 2026-04-24, Date of Delay: 2026-04-23, Anticipated Resolution ETA: 2026-05-01 \| unable to proceed until allonge is received. RID: 862116504 \| Notice of Sale sent for filing on 4/27/2026. ETA for completion of NOS posted milestone is 4/30/2026. \| Pending signature required document to proceed with foreclosure action. \| Unable to proceed, pending Guaranty Agreement-RID: 861370088 \| Pending signature required document to proceed with foreclosure action. \| Pending receipt Note Allonge requested \| AOM Needed from Mortgage Electronic Registration Systems, Inc., as nominee for A&D Mortgage LLC, Its Successors and Assigns To: Alic Archwest Mortgage Trust, To Proceed to Fi … |
| BPS Verify Result | N/A — not mapped to a BPS FCL sync table (see Newrez → BPS Rule) |

Newrez Verify SQL:
```sql
-- Verify against mysql_dev, data date 2026-06-01
SELECT loanid, dataasof, fchold3comment
FROM   newrez.portnewrezfc
WHERE  dataasof = '2026-06-01'
  AND  fchold3comment IS NOT NULL AND fchold3comment != ''
LIMIT  10;
```

<!-- FS-CARDS:2.6 END -->



> **Zero-fill fields (Newrez currently does not provide — reserved as future extensions)**:
> - **Senior/Junior Lien tracking**: `srlienmonitorflag`, `srliensalescheduleddate`, `srliensalehelddate` (when Newrez loan is Junior Lien, Senior Lien FCL progress is critical)
> - **SCRA military protections**: `loanscraflag`, `loanscrastartdate`, `loanscraenddate` (SCRA-protected loans must halt foreclosure; active-duty military loans require special handling)
> - **FEMA disaster areas**: `femaarea`, `femaaffect` (loans in declared disaster areas are subject to foreclosure moratoriums)
> - **Title ordering**: `titleordereddate` (date title search was commissioned, precedes `titlereceiveddate`; Newrez currently does not provide)

---

## Section 3: LM Data Field Specification (Source: `portnewrezlm`)

### 3.1 LM Cycle Fields (P1 — Loss Mitigation Cycle Panel)

Each LM cycle is stored as one row (uniquely identified by `lmdeal` + `dealstartdate`). BPS stores one-to-many; history is never overwritten.

<!-- FS-CARDS:3.1 START -->
##### `lm_deal` · P1 · LM Cycle Fields

| Attribute | Value |
|---|---|
| Newrez Raw Field | `lmdeal` |
| Data Type | INT→VARCHAR |
| Business Meaning | LM strategy category (integer-coded); ETL decodes to text: Evaluation / Modification / Short Sale / DIL etc.; reflects the overall direction of this loss mitigation attempt |
| Format / Allowed Values | **Decode mapping table required** (int code → text, e.g., `7`→`"DIL"`) |
| Typical Value | Modification |
| BPS Panel / Function | LM Cycle `deal` |
| Newrez → BPS Rule | Integer code lmdeal decoded to text via portnewrezdatadic (e.g. 7→DIL) → deal |
| Newrez Status | ✅ Provided |
| Newrez Verify Result | 1 Modification:194 \| 1 Evaluation:2 \| 2 Evaluation:104 \| 4 Payment Plan:37 \| 5 Forbearance:51 \| 6 Short Sale:9 \| 7 DIL:10 \| 9 Payoff:1 \| 11 Deferment:50 |
| BPS Verify Result | [BPS prod \| data date fctrdt≤2026-06-01 \| ETL load 2026-06-03] Modification:207 \| Evaluation:115 \| ∅NULL:72 \| Forbearance:57 \| Deferment:56 \| Payment Plan:39 \| Short Sale:12 \| DIL:10 \| Payoff:1 |

Newrez Verify SQL:
```sql
-- Verify against mysql_dev, data date 2026-06-01
WITH latest_lm AS (
  SELECT loanid, dealstartdate, lmdeal,
         ROW_NUMBER() OVER (PARTITION BY loanid, dealstartdate ORDER BY dataasof DESC) AS rn
  FROM newrez.portnewrezlm WHERE lmdeal IS NOT NULL AND dataasof <= '2026-06-01'
)
SELECT l.lmdeal, b.deal, COUNT(*) AS cnt
FROM   latest_lm l
JOIN   bpms_dev.sync_loan_foreclosure_loss_mitigation b
  ON   l.loanid = b.loanid AND l.dealstartdate = b.cycle_opened_date
WHERE  l.rn = 1
  AND  b.deal IS NOT NULL AND b.deal != '' AND b.deal NOT REGEXP '^[0-9]'
GROUP  BY l.lmdeal, b.deal ORDER BY l.lmdeal, cnt DESC;
```

BPS Verify SQL (prod, read-only):
```sql
-- Verify against prod bpms (read-only)
SELECT '2026-06-01' AS data_date, `deal` AS val, COUNT(*) AS cnt
FROM   bpms.sync_loan_foreclosure_loss_mitigation
GROUP  BY `deal` ORDER BY cnt DESC;
```

##### `lm_program` · P1 · LM Cycle Fields

| Attribute | Value |
|---|---|
| Newrez Raw Field | `lmprogram` |
| Data Type | INT→VARCHAR |
| Business Meaning | Specific LM execution program (integer-coded); sub-program within the Deal category; e.g., Bridger mod / 496.0 / Deed-in-Lieu |
| Format / Allowed Values | **Decode mapping table required** |
| Typical Value | Bridger mod |
| BPS Panel / Function | LM Cycle `program` |
| Newrez → BPS Rule | Integer code lmprogram decoded to text via portnewrezdatadic (e.g. 10→Deed-in-Lieu) → program |
| Newrez Status | ✅ Provided |
| Newrez Verify Result | 8 Short Sale:9 \| 10 Deed-in-Lieu:10 \| 12 Short-term Forbearance:41 \| 14 Unemployment Forbearance:6 \| 21 Evaluation:103 \| 25 Payoff:1 \| 29 Repayment Plan:37 \| 73 Deferment:50 \| 151 Disaster Forbearance:2 \| 215 Short-term FB COVID (RETIRED 2023-11-01):2 \| 240 SLS Standard Mod:26 \| 273 Standard Proprietary Modification:9 \| 346 FHA Recovery Mod (40yr):1 \| 348 FHA Recovery SAPC:16 \| 358 SLS Non-Standard Mod:1 \| 364 VA 30 Year Modification:2 \| 365 VA 40 Year Modification:2 \| 396 VA Traditional:30 \| 405 VASP No Trial:7 \| 419 Bridger mod:38 \| 496 Evaluation:2 |
| BPS Verify Result | [BPS prod \| data date fctrdt≤2026-06-01 \| ETL load 2026-06-03] Evaluation:114 \| ∅NULL:72 \| Deferment:56 \| 496.0:55 \| Short-term Forbearance:47 \| Repayment Plan:39 \| Bridger mod:38 \| VA Traditional:30 \| SLS Standard Mod:26 \| FHA Recovery SAPC:16 \| 498.0:14 \| Short Sale:12 \| Deed-in-Lieu:10 \| Standard Proprietary Modification:9 \| VASP No Trial:7 \| Unemployment Forbearance:6 \| 499.0:4 \| VA 40 Year Modification:2 \| VA 30 Year Modification:2 \| Disaster Forbearance:2 \| Short-term FB COVID (RETIRED 2023-11-01):2 \| +7 values, 1 row each(incl. 531.0/527.0/500.0 etc.undecoded code):7 |

Newrez Verify SQL:
```sql
-- Verify against mysql_dev, data date 2026-06-01
WITH latest_lm AS (
  SELECT loanid, dealstartdate, lmprogram,
         ROW_NUMBER() OVER (PARTITION BY loanid, dealstartdate ORDER BY dataasof DESC) AS rn
  FROM newrez.portnewrezlm WHERE lmprogram IS NOT NULL AND dataasof <= '2026-06-01'
)
SELECT l.lmprogram, b.program, COUNT(*) AS cnt
FROM   latest_lm l
JOIN   bpms_dev.sync_loan_foreclosure_loss_mitigation b
  ON   l.loanid = b.loanid AND l.dealstartdate = b.cycle_opened_date
WHERE  l.rn = 1
  AND  b.program IS NOT NULL AND b.program != '' AND b.program NOT REGEXP '^[0-9]'
GROUP  BY l.lmprogram, b.program ORDER BY l.lmprogram, cnt DESC;
```

BPS Verify SQL (prod, read-only):
```sql
-- Verify against prod bpms (read-only)
SELECT '2026-06-01' AS data_date, `program` AS val, COUNT(*) AS cnt
FROM   bpms.sync_loan_foreclosure_loss_mitigation
GROUP  BY `program` ORDER BY cnt DESC;
```

##### `lm_status` · P1 · LM Cycle Fields

| Attribute | Value |
|---|---|
| Newrez Raw Field | `lmstatus` |
| Data Type | INT→VARCHAR |
| Business Meaning | Current workflow progress status for this LM cycle (integer-coded); e.g., Pending Financials / Workout Denial / DIL Title Ordered |
| Format / Allowed Values | **Decode mapping table required** |
| Typical Value | Pending Financials |
| BPS Panel / Function | LM Cycle `lmc_status` |
| Newrez → BPS Rule | Integer code lmstatus decoded to text via portnewrezdatadic (e.g. 112→Workout Denial) → lmc_status |
| Newrez Status | ✅ Provided |
| Newrez Verify Result | 5 Document Follow-up:72 \| 13 Follow up for 1st Trial Payment:4 \| 13 Pending Financials :1 \| 20 Book mod:24 \| 20 Follow up for 2nd Trial Payment:2 \| 20 Follow up for 1st Trial Payment:1 \| 20 Monitor for Mod Agreement – Final Trial Payment Due:1 \| 24 Awaiting investor approval:1 \| 25 Monitor for pmts/funds:9 \| 25 Submitted for Approval:1 \| 45 Countered by Supervisor:2 \| 47 Monitor for Mod Agreement:3 \| 112 Workout Denial:144 \| 112 Document Follow-up:1 \| 112 Awaiting MI Approval:1 \| 112 Monitor for pmts/funds:1 \| 112 Pending Financials :1 \| 113 Monitor Forbearance:27 \| 116 Not Assigned:1 \| 126 DIL Title Ordered:1 \| 127 Negotiate DIL liens:1 \| 135 DIL Sent for Recording:1 \| 139 Deferment Plan In Progress:11 \| 140 Deferment Agreement Ordered:21 \| 166 Pending Financials :113 \| 172 Liquidation Referral:7 \| 186 Follow up for 1st Trial Payment:1 \| 186 Monitor for Mod Agreement – Final Trial Payme … |
| BPS Verify Result | [BPS prod \| data date fctrdt≤2026-06-01 \| ETL load 2026-06-03] Workout Denial:160 \| Pending Financials :127 \| Document Follow-up:74 \| ∅NULL:72 \| Monitor Forbearance:31 \| Book mod:28 \| Deferment Agreement Ordered:23 \| Deferment Plan In Progress:13 \| Monitor for pmts/funds:10 \| Liquidation Referral:8 \| Follow up for 1st Trial Payment:5 \| Solicitation Offered:4 \| Monitor for Mod Agreement:3 \| +9 values, <=2 rows each:14 |

Newrez Verify SQL:
```sql
-- Verify against mysql_dev, data date 2026-06-01
WITH latest_lm AS (
  SELECT loanid, dealstartdate, lmstatus,
         ROW_NUMBER() OVER (PARTITION BY loanid, dealstartdate ORDER BY dataasof DESC) AS rn
  FROM newrez.portnewrezlm WHERE lmstatus IS NOT NULL AND dataasof <= '2026-06-01'
)
SELECT l.lmstatus, b.lmc_status, COUNT(*) AS cnt
FROM   latest_lm l
JOIN   bpms_dev.sync_loan_foreclosure_loss_mitigation b
  ON   l.loanid = b.loanid AND l.dealstartdate = b.cycle_opened_date
WHERE  l.rn = 1
  AND  b.lmc_status IS NOT NULL AND b.lmc_status != '' AND b.lmc_status NOT REGEXP '^[0-9]'
GROUP  BY l.lmstatus, b.lmc_status ORDER BY l.lmstatus, cnt DESC;
```

BPS Verify SQL (prod, read-only):
```sql
-- Verify against prod bpms (read-only)
SELECT '2026-06-01' AS data_date, `lmc_status` AS val, COUNT(*) AS cnt
FROM   bpms.sync_loan_foreclosure_loss_mitigation
GROUP  BY `lmc_status` ORDER BY cnt DESC;
```

##### `lm_cycle_open_date` · P1 · LM Cycle Fields

| Attribute | Value |
|---|---|
| Newrez Raw Field | `dealstartdate` |
| Data Type | DATE |
| Business Meaning | Start date of this LM cycle (date Servicer formally opened this workout attempt); forms part of the cycle's unique identifier together with `lm_deal` |
| Format / Allowed Values | YYYY-MM-DD; LM cycle start date |
| Typical Value | 2024-01-15 |
| BPS Panel / Function | LM Cycle `cycle_opened_date` |
| Newrez → BPS Rule | Direct copy (dealstartdate → cycle_opened_date) |
| Newrez Status | ✅ Provided |
| Newrez Verify Result | [data_date 2026-06-01] 2025-09-18 \| 2026-04-28 \| 2026-03-06 \| 2025-07-18 \| 2025-05-23 \| 2025-09-19 \| 2025-11-05 \| 2025-12-10 \| 2026-02-25 \| 2026-03-31 (10 rows) |
| BPS Verify Result | [BPS prod \| data date fctrdt≤2026-06-01 \| ETL load 2026-06-03] non-null 568/569 \| range 2020-08-17~2026-06-01 |

Newrez Verify SQL:
```sql
-- Verify against mysql_dev, data date 2026-06-01
SELECT loanid, dataasof, dealstartdate
FROM   newrez.portnewrezlm
WHERE  dataasof = '2026-06-01'
  AND  dealstartdate IS NOT NULL
LIMIT  10;
```

BPS Verify SQL (prod, read-only):
```sql
-- Verify against prod bpms (read-only)
SELECT '2026-06-01' AS data_date, COUNT(*) AS total, COUNT(`cycle_opened_date`) AS non_null,
       MIN(`cycle_opened_date`) AS min_dt, MAX(`cycle_opened_date`) AS max_dt
FROM   bpms.sync_loan_foreclosure_loss_mitigation;
```

##### `lm_cycle_close_date` · P1 · LM Cycle Fields

| Attribute | Value |
|---|---|
| Newrez Raw Field | `lmremovaldate` |
| Data Type | DATE |
| Business Meaning | End date of this LM cycle; NULL = still in progress; combined with open_date to calculate cycle duration |
| Format / Allowed Values | YYYY-MM-DD; NULL = still active |
| Typical Value | 2024-03-15 |
| BPS Panel / Function | LM Cycle `cycle_closed_date` |
| Newrez → BPS Rule | Direct copy (lmremovaldate → cycle_closed_date; NULL=open) |
| Newrez Status | ✅ Provided |
| Newrez Verify Result | [data_date 2026-06-01] 2025-11-07 \| 2026-05-03 \| 2026-05-08 \| 2026-05-20 \| 2025-12-03 \| 2026-05-07 \| 2026-05-01 \| 2025-09-08 \| 2025-05-27 \| 2025-09-29 (10 rows) |
| BPS Verify Result | [BPS prod \| data date fctrdt≤2026-06-01 \| ETL load 2026-06-03] non-null 511/569 \| range 2020-09-22~2026-06-01 |

Newrez Verify SQL:
```sql
-- Verify against mysql_dev, data date 2026-06-01
SELECT loanid, dataasof, lmremovaldate
FROM   newrez.portnewrezlm
WHERE  dataasof = '2026-06-01'
  AND  lmremovaldate IS NOT NULL
LIMIT  10;
```

BPS Verify SQL (prod, read-only):
```sql
-- Verify against prod bpms (read-only)
SELECT '2026-06-01' AS data_date, COUNT(*) AS total, COUNT(`cycle_closed_date`) AS non_null,
       MIN(`cycle_closed_date`) AS min_dt, MAX(`cycle_closed_date`) AS max_dt
FROM   bpms.sync_loan_foreclosure_loss_mitigation;
```

##### `lm_final_disposition` · P1 · LM Cycle Fields

| Attribute | Value |
|---|---|
| Newrez Raw Field | `lmdecision` |
| Data Type | INT→VARCHAR |
| Business Meaning | Final disposition of this LM cycle (integer-coded); determines FCL trajectory: `Referral to FC` / `Request Incomplete` → FCL continues; `Approved` → FCL paused |
| Format / Allowed Values | **Decode mapping table required** |
| Typical Value | Referral to FC |
| BPS Panel / Function | LM Cycle `final_disposition` |
| Newrez → BPS Rule | Integer code lmdecision decoded to text via portnewrezdatadic (e.g. 6→Referral to FC) → final_disposition |
| Newrez Status | ✅ Provided |
| Newrez Verify Result | 1 Modification Complete:15 \| 1 Pending:2 \| 3 DIL Complete:1 \| 4 Forbearance Complete:16 \| 4 Pending:2 \| 5 Reinstated/Current:32 \| 5 Pending:2 \| 5 Request Incomplete/Failed to Provide Information:1 \| 6 Referral to FC:110 \| 6 Pending:4 \| 7 Not Eligible for Loss Mitigation:7 \| 10 Request Incomplete/Failed to Provide Information:94 \| 10 Pending:4 \| 11 LMS Opened in Error:52 \| 14 Deferment Completed:30 \| 17 Full Pay Off:7 \| 18 FC Sale Held:2 \| 99 Pending:77 |
| BPS Verify Result | [BPS prod \| data date fctrdt≤2026-06-01 \| ETL load 2026-06-03] Referral to FC:123 \| Request Incomplete/Failed to Provide Information:102 \| Pending:97 \| ∅NULL:72 \| LMS Opened in Error:53 \| Reinstated/Current:36 \| Deferment Completed:33 \| Forbearance Complete:19 \| Modification Complete:17 \| Not Eligible for Loss Mitigation:7 \| Full Pay Off:7 \| FC Sale Held:2 \| DIL Complete:1 |

Newrez Verify SQL:
```sql
-- Verify against mysql_dev, data date 2026-06-01
WITH latest_lm AS (
  SELECT loanid, dealstartdate, lmdecision,
         ROW_NUMBER() OVER (PARTITION BY loanid, dealstartdate ORDER BY dataasof DESC) AS rn
  FROM newrez.portnewrezlm WHERE lmdecision IS NOT NULL AND dataasof <= '2026-06-01'
)
SELECT l.lmdecision, b.final_disposition, COUNT(*) AS cnt
FROM   latest_lm l
JOIN   bpms_dev.sync_loan_foreclosure_loss_mitigation b
  ON   l.loanid = b.loanid AND l.dealstartdate = b.cycle_opened_date
WHERE  l.rn = 1
  AND  b.final_disposition IS NOT NULL AND b.final_disposition != '' AND b.final_disposition NOT REGEXP '^[0-9]'
GROUP  BY l.lmdecision, b.final_disposition ORDER BY l.lmdecision, cnt DESC;
```

BPS Verify SQL (prod, read-only):
```sql
-- Verify against prod bpms (read-only)
SELECT '2026-06-01' AS data_date, `final_disposition` AS val, COUNT(*) AS cnt
FROM   bpms.sync_loan_foreclosure_loss_mitigation
GROUP  BY `final_disposition` ORDER BY cnt DESC;
```

##### `lm_denial_reason` · P1 · LM Cycle Fields

| Attribute | Value |
|---|---|
| Newrez Raw Field | `denialreason` |
| Data Type | INT→VARCHAR |
| Business Meaning | Specific reason for LM denial (integer-coded); empty string when there is no denial |
| Format / Allowed Values | **Decode mapping table required**; empty string when no denial |
| Typical Value | Withdrawal of Request/Non-Acceptance |
| BPS Panel / Function | LM Cycle `denialreason` |
| Newrez → BPS Rule | Integer code denialreason decoded to text via portnewrezdatadic (empty when no denial) |
| Newrez Status | ✅ Provided |
| Newrez Verify Result | 2 Trial Plan Default:3 \| 4 Withdrawal of Request/Non-Acceptance:12 \| 6 Ineligible Borrower:1 \| 9 Investor Not Participating:5 \| 11 Default Not Imminent:1 \| 20 Title Exceptions:1 \| 21 Request Incomplete/Failed to Provide Documentation:22 \| 30 Failed Plan:5 \| 32 HDTI out of range:2 \| 34 Ineligible Borrower: Not a Natural Person:1 \| 50 Request Withdrawn Before Offer:1 \| 53 Prev Denial – No Chg in Circumstance:1 \| 59 Pre-Mod HDTI < 31%:1 \| 75 Declined Mod Review in favor of SS/DIL:1 \| 76 HAMP Sunset:15 \| 78 Buyer walked (SS):1 \| 86 Request Withdrawn:2 \| 95 Loan not eligible for deferment:1 \| 101 Required Payment Returned / Not Received:1 \| 108 Unable to achieve target payment:9 \| 109 Loan not due for 3 or more monthly payments:25 \| 115 Post-Mod P&I Payment > Current P&I Payment:4 \| 118 Loan not 90+ DPD :5 \| 122 DTI out of range for Deferment:1 \| 124 Hardship not resolved:6 |
| BPS Verify Result | [BPS prod \| data date fctrdt≤2026-06-01 \| ETL load 2026-06-03] (empty string):351 \| ∅NULL:72 \| Request Incomplete/Failed to Provide Documentation:28 \| Loan not due for 3 or more monthly payments:25 \| HAMP Sunset:16 \| Withdrawal of Request/Non-Acceptance:15 \| Unable to achieve target payment:9 \| Hardship not resolved:7 \| Investor Not Participating:6 \| Failed Plan:5 \| Loan not 90+ DPD :5 \| Post-Mod P&I Payment > Current P&I Payment:4 \| Trial Plan Default:4 \| HDTI out of range:3 \| 145.0(undecoded code):1 \| +18 values, 1 row each:18 |

Newrez Verify SQL:
```sql
-- Verify against mysql_dev, data date 2026-06-01
WITH latest_lm AS (
  SELECT loanid, dealstartdate, denialreason,
         ROW_NUMBER() OVER (PARTITION BY loanid, dealstartdate ORDER BY dataasof DESC) AS rn
  FROM newrez.portnewrezlm WHERE denialreason IS NOT NULL AND dataasof <= '2026-06-01'
)
SELECT l.denialreason, b.denialreason, COUNT(*) AS cnt
FROM   latest_lm l
JOIN   bpms_dev.sync_loan_foreclosure_loss_mitigation b
  ON   l.loanid = b.loanid AND l.dealstartdate = b.cycle_opened_date
WHERE  l.rn = 1 AND l.denialreason != 0
  AND  b.denialreason IS NOT NULL AND b.denialreason != '' AND b.denialreason NOT REGEXP '^[0-9]'
GROUP  BY l.denialreason, b.denialreason ORDER BY l.denialreason, cnt DESC;
```

BPS Verify SQL (prod, read-only):
```sql
-- Verify against prod bpms (read-only)
SELECT '2026-06-01' AS data_date, `denialreason` AS val, COUNT(*) AS cnt
FROM   bpms.sync_loan_foreclosure_loss_mitigation
GROUP  BY `denialreason` ORDER BY cnt DESC;
```

##### `borrower_intentions` · P2 · LM Cycle Fields

| Attribute | Value |
|---|---|
| Newrez Raw Field | `borrowerintention` |
| Data Type | INT→VARCHAR |
| Business Meaning | Borrower's stated intended resolution (integer-coded); e.g., retain property / short sale / deed-in-lieu; CFPB Reg X related; Newrez does not provide |
| Format / Allowed Values | Decode mapping table (if provided) |
| Typical Value | Retention |
| BPS Panel / Function | LM Cycle `borrower_intentions` |
| Newrez → BPS Rule | Integer code borrowerintention decoded to text via portnewrezdatadic (usually empty in Newrez) |
| Newrez Status | ❌ 0% (Newrez does not provide; see doc 13 Q6) |
| Newrez Verify Result | 1 Unknown:1 \| 2 Retention:47 \| 3 Disposition:4 |
| BPS Verify Result | [BPS prod \| data date fctrdt≤2026-06-01 \| ETL load 2026-06-03] (empty string):442 \| ∅NULL:72 \| Retention:49 \| Disposition:5 \| Unknown:1 |

Newrez Verify SQL:
```sql
-- Verify against mysql_dev, data date 2026-06-01
WITH latest_lm AS (
  SELECT loanid, dealstartdate, borrowerintention,
         ROW_NUMBER() OVER (PARTITION BY loanid, dealstartdate ORDER BY dataasof DESC) AS rn
  FROM newrez.portnewrezlm WHERE borrowerintention IS NOT NULL AND dataasof <= '2026-06-01'
)
SELECT l.borrowerintention, b.borrower_intentions, COUNT(*) AS cnt
FROM   latest_lm l
JOIN   bpms_dev.sync_loan_foreclosure_loss_mitigation b
  ON   l.loanid = b.loanid AND l.dealstartdate = b.cycle_opened_date
WHERE  l.rn = 1 AND l.borrowerintention != 0
  AND  b.borrower_intentions IS NOT NULL AND b.borrower_intentions != '' AND b.borrower_intentions NOT REGEXP '^[0-9]'
GROUP  BY l.borrowerintention, b.borrower_intentions ORDER BY l.borrowerintention, cnt DESC;
```

BPS Verify SQL (prod, read-only):
```sql
-- Verify against prod bpms (read-only)
SELECT '2026-06-01' AS data_date, `borrower_intentions` AS val, COUNT(*) AS cnt
FROM   bpms.sync_loan_foreclosure_loss_mitigation
GROUP  BY `borrower_intentions` ORDER BY cnt DESC;
```

##### `imminent_default` · P2 · LM Cycle Fields

| Attribute | Value |
|---|---|
| Newrez Raw Field | *(no field)* |
| Data Type | VARCHAR |
| Business Meaning | CFPB Reg X required flag for imminent default; marks borrowers not yet delinquent but facing foreseeable repayment hardship; triggers early LM assessment obligation; Newrez does not provide |
| Format / Allowed Values | CFPB Reg X trigger condition |
| Typical Value | — |
| BPS Panel / Function | LM Cycle `imminent_default` |
| Newrez → BPS Rule | N/A — always NULL for Newrez (BPS column exists but the Newrez path does not populate it) |
| Newrez Status | ❌ 0% (Newrez does not provide; see doc 13 Q6) |
| Newrez Verify Result | N/A (no verifiable source) |
| BPS Verify Result | [BPS prod \| data date fctrdt≤2026-06-01 \| ETL load 2026-06-03] ∅NULL:569 |

BPS Verify SQL (prod, read-only):
```sql
-- Verify against prod bpms (read-only)
SELECT '2026-06-01' AS data_date, `imminent_default` AS val, COUNT(*) AS cnt
FROM   bpms.sync_loan_foreclosure_loss_mitigation
GROUP  BY `imminent_default` ORDER BY cnt DESC;
```

##### `single_point_of_contact` · P2 · LM Cycle Fields

| Attribute | Value |
|---|---|
| Newrez Raw Field | *(no field)* |
| Data Type | VARCHAR |
| Business Meaning | CFPB Reg X 12 CFR 1024.40 required dedicated servicer contact name; borrowers in LM must have a single designated point of contact; Newrez does not provide |
| Format / Allowed Values | CFPB Reg X 12 CFR 1024.40 |
| Typical Value | — |
| BPS Panel / Function | LM Cycle `single_point_of_contact` |
| Newrez → BPS Rule | N/A — always NULL for Newrez (BPS column exists but the Newrez path does not populate it) |
| Newrez Status | ❌ 0% (Newrez does not provide; see doc 13 Q6) |
| Newrez Verify Result | N/A (no verifiable source) |
| BPS Verify Result | [BPS prod \| data date fctrdt≤2026-06-01 \| ETL load 2026-06-03] ∅NULL:569 |

BPS Verify SQL (prod, read-only):
```sql
-- Verify against prod bpms (read-only)
SELECT '2026-06-01' AS data_date, `single_point_of_contact` AS val, COUNT(*) AS cnt
FROM   bpms.sync_loan_foreclosure_loss_mitigation
GROUP  BY `single_point_of_contact` ORDER BY cnt DESC;
```

<!-- FS-CARDS:3.1 END -->



> 📖 **Regulatory terms**: **CFPB** = Consumer Financial Protection Bureau, the U.S. federal consumer-finance regulator. **Reg X** (Regulation X) is its rule implementing **RESPA** (Real Estate Settlement Procedures Act), codified at **12 CFR Part 1024**; within it, **1024.40** requires assigning a Single Point of Contact (**SPOC**, maps to `single_point_of_contact`) to a delinquent borrower, and **1024.41** prescribes the loss-mitigation evaluation procedures before foreclosure. **Imminent Default** denotes a borrower not yet delinquent but facing foreseeable hardship who must be evaluated for LM proactively (maps to `imminent_default`). For full entries, see doc 10 "Category H — Regulatory/Compliance Terms".

### 3.2 ETL Decode Requirement (LM Fields Special Note)

Newrez `portnewrezlm` stores `lmdeal`, `lmprogram`, `lmstatus`, `lmdecision`, and `denialreason` as **numeric codes** (int type). BPS's `sync_loan_foreclosure_loss_mitigation` stores **decoded text**, not numeric codes.

**Servicer delivery requirements**:
1. Each data submission must be accompanied by a field decode mapping table (int code → business text)
2. Any changes to the decode mapping must be communicated in advance; BPS will need to resync historical data
3. BPS will not accept LM records submitted as numeric codes only (they cannot be displayed correctly in the panel)

---

## Section 4: Bankruptcy Data Field Specification (Source: `portnewrezbk`)

### 4.1 BK Fields (P1/P2 — Bankruptcy Panel)

BK data is independent from FCL data; each bankruptcy record for a loan is stored as a separate row in BPS. If a loan has no bankruptcy records, the Bankruptcy panel shows "No Rows To Show."

<!-- FS-CARDS:4.1 START -->
##### `active_bk_flag` · P1 · BK Fields

| Attribute | Value |
|---|---|
| Newrez Raw Field | `activebkflag` |
| Data Type | TINYINT |
| Business Meaning | Whether the loan is currently under active bankruptcy protection (Automatic Stay); 1=active; foreclosure must legally halt during Automatic Stay |
| Format / Allowed Values | 0 / 1 |
| Typical Value | 1 |
| BPS Panel / Function | `variance_active_bankruptcy` (FCL Summary active bankruptcy indicator) |
| Newrez → BPS Rule | N/A — BK table has no active flag; bankruptcy existence = rows present |
| Newrez Status | ✅ Provided |
| Newrez Verify Result | [data_date 2026-06-01] 0:5039 \| 1:13 |
| BPS Verify Result | N/A — not mapped to a BPS FCL sync table (see Newrez → BPS Rule) |

Newrez Verify SQL:
```sql
-- Verify against mysql_dev, data date 2026-06-01
SELECT dataasof AS data_date, activebkflag, COUNT(*) AS cnt
FROM   newrez.portnewrezbk
WHERE  dataasof = '2026-06-01'
GROUP  BY dataasof, activebkflag ORDER BY cnt DESC;
```

##### `bk_status` · P1 · BK Fields

| Attribute | Value |
|---|---|
| Newrez Raw Field | `bkstatus` (int) |
| Data Type | INT→VARCHAR |
| Business Meaning | Current bankruptcy case status. Newrez raw `bkstatus` is an integer code (1–5); **BPS decodes it to text** (observed dominant map: 1→Active·2→Discharged·3→Dismissed·4→Closed·5→ReliefGranted); reflects the current node in bankruptcy proceedings |
| Format / Allowed Values | Positive integer |
| Typical Value | 2 |
| BPS Panel / Function | BK panel Status column (BPS decodes to text; DB-verified) |
| Newrez → BPS Rule | COALESCE(portnewrezdatadic[BKStatus] decoded text, raw bkstatus code) (Active/Discharged/Dismissed/Closed/ReliefGranted) |
| Newrez Status | ✅ Confirmed: BPS decodes to text (Active/Discharged/Dismissed/Closed/ReliefGranted; bkstatus 1→Active·2→Discharged·3→Dismissed·4→Closed·5→ReliefGranted, DB-verified) |
| Newrez Verify Result | [data_date 2026-06-01] 2:14 \| 1:13 \| 3:3 \| 5:2 \| 4:1 |
| BPS Verify Result | [BPS prod \| data date fctrdt≤2026-06-01 \| ETL load 2026-06-03] Completed/Cancelled:32 \| Active:16 \| Discharged:15 \| Dismissed:3 \| ReliefGranted:2 \| Closed:1 |

Newrez Verify SQL:
```sql
-- Verify against mysql_dev, data date 2026-06-01
SELECT dataasof AS data_date, bkstatus AS code, COUNT(*) AS cnt
FROM   newrez.portnewrezbk
WHERE  dataasof = '2026-06-01'
  AND  bkstatus IS NOT NULL AND bkstatus != ''
GROUP  BY dataasof, bkstatus ORDER BY cnt DESC;
```

BPS Verify SQL (prod, read-only):
```sql
-- Verify against prod bpms (read-only)
SELECT '2026-06-01' AS data_date, `bankruptcy_status` AS val, COUNT(*) AS cnt
FROM   bpms.sync_loan_foreclosure_bankruptcy
GROUP  BY `bankruptcy_status` ORDER BY cnt DESC;
```

##### `bk_legal_status` · P1 · BK Fields

| Attribute | Value |
|---|---|
| Newrez Raw Field | `legalstatus` (from `portnewrezgeneral`, text; doc's `bkstage` was a misattribution) |
| Data Type | VARCHAR |
| Business Meaning | Bankruptcy legal-proceeding stage. BPS `legal_status` **actually comes from `newrez.portnewrezgeneral.legalstatus`** (text, e.g. FCBU/BK13/BK7/BK11/...), NOT a decode of `bkstage` (DB-verified); a different classification dimension from bk_status |
| Format / Allowed Values | Text |
| Typical Value | 8 |
| BPS Panel / Function | BK panel Legal Status column (from portnewrezgeneral.legalstatus text) |
| Newrez → BPS Rule | Direct text copy (portnewrezgeneral.legalstatus → legal_status, e.g. FCBU/BK13/BK7) |
| Newrez Status | ✅ Confirmed: BPS `legal_status` comes from `portnewrezgeneral.legalstatus` text (FCBU/BK13/BK7/BK11/BK7DCH/BK11DCH/BKD7LM/BKD13LM/FCSold/REO, etc.), **not** a decode of `bkstage` (DB-verified) |
| Newrez Verify Result | [data_date 2026-06-01] 8:14 \| 4:5 \| 10:3 \| 21:2 \| 7:2 \| 17:1 |
| BPS Verify Result | [BPS prod \| data date fctrdt≤2026-06-01 \| ETL load 2026-06-03] ∅NULL:35 \| BK13:12 \| BK11DCH:3 \| BK11:3 \| FCBU:3 \| BK7:3 \| BK7DCH:2 \| (empty string):2 \| REO:2 \| BKD13LM:1 \| BKD7LM:1 \| BK13DCH:1 \| FCSold:1 |

Newrez Verify SQL:
```sql
-- Verify against mysql_dev, data date 2026-06-01
SELECT dataasof AS data_date, bkstage AS code, COUNT(*) AS cnt
FROM   newrez.portnewrezbk
WHERE  dataasof = '2026-06-01'
  AND  bkstage IS NOT NULL AND bkstage != ''
GROUP  BY dataasof, bkstage ORDER BY cnt DESC;
```

BPS Verify SQL (prod, read-only):
```sql
-- Verify against prod bpms (read-only)
SELECT '2026-06-01' AS data_date, `legal_status` AS val, COUNT(*) AS cnt
FROM   bpms.sync_loan_foreclosure_bankruptcy
GROUP  BY `legal_status` ORDER BY cnt DESC;
```

##### `bk_status_date` · P1 · BK Fields

| Attribute | Value |
|---|---|
| Newrez Raw Field | `bkrcurrentstatusdate` |
| Data Type | DATE |
| Business Meaning | Effective date of the current bankruptcy status |
| Format / Allowed Values | YYYY-MM-DD |
| Typical Value | 2024-01-15 |
| BPS Panel / Function | BK panel Status Date |
| Newrez → BPS Rule | Direct copy (bkfileddate → status_date; code-verified = BK filing date, not bkrcurrentstatusdate) |
| Newrez Status | ✅ Provided |
| Newrez Verify Result | [data_date 2026-06-01] 2026-04-27 \| 2026-04-15 \| 2025-07-12 \| 2023-10-24 \| 2026-04-01 \| 2026-04-08 \| 2026-05-26 \| 2026-03-27 \| 2023-11-20 \| 2024-02-01 (10 rows) |
| BPS Verify Result | [BPS prod \| data date fctrdt≤2026-06-01 \| ETL load 2026-06-03] non-null 67/69 \| range 2003-11-14~2026-05-29 |

Newrez Verify SQL:
```sql
-- Verify against mysql_dev, data date 2026-06-01
SELECT loanid, dataasof, bkrcurrentstatusdate
FROM   newrez.portnewrezbk
WHERE  dataasof = '2026-06-01'
  AND  bkrcurrentstatusdate IS NOT NULL
LIMIT  10;
```

BPS Verify SQL (prod, read-only):
```sql
-- Verify against prod bpms (read-only)
SELECT '2026-06-01' AS data_date, COUNT(*) AS total, COUNT(`status_date`) AS non_null,
       MIN(`status_date`) AS min_dt, MAX(`status_date`) AS max_dt
FROM   bpms.sync_loan_foreclosure_bankruptcy;
```

##### `bk_chapter` · P1 · BK Fields

| Attribute | Value |
|---|---|
| Newrez Raw Field | `bkchapter` |
| Data Type | VARCHAR/INT |
| Business Meaning | Bankruptcy chapter filed under; common: Chapter 7 (liquidation) / Chapter 13 (repayment plan) / Chapter 11 (reorganization); affects foreclosure resumption strategy |
| Format / Allowed Values | Positive integer |
| Typical Value | 7 |
| BPS Panel / Function | BK panel Chapter (7/11/13) |
| Newrez → BPS Rule | CAST to DECIMAL (7/11/13 → chapter) |
| Newrez Status | ✅ Provided |
| Newrez Verify Result | [data_date 2026-06-01] 13:15 \| 7:12 \| 11:6 |
| BPS Verify Result | [BPS prod \| data date fctrdt≤2026-06-01 \| ETL load 2026-06-03] 13:38 \| 7:25 \| 11:6 |

Newrez Verify SQL:
```sql
-- Verify against mysql_dev, data date 2026-06-01
SELECT dataasof AS data_date, bkchapter AS code, COUNT(*) AS cnt
FROM   newrez.portnewrezbk
WHERE  dataasof = '2026-06-01'
  AND  bkchapter IS NOT NULL AND bkchapter != ''
GROUP  BY dataasof, bkchapter ORDER BY cnt DESC;
```

BPS Verify SQL (prod, read-only):
```sql
-- Verify against prod bpms (read-only)
SELECT '2026-06-01' AS data_date, `chapter` AS val, COUNT(*) AS cnt
FROM   bpms.sync_loan_foreclosure_bankruptcy
GROUP  BY `chapter` ORDER BY cnt DESC;
```

##### `bk_filed_date` · P1 · BK Fields

| Attribute | Value |
|---|---|
| Newrez Raw Field | `bkfileddate` |
| Data Type | DATE |
| Business Meaning | Date the bankruptcy petition was filed with the court; BPS deduplication key (loanid + bkfileddate uniquely identifies one bankruptcy filing) |
| Format / Allowed Values | YYYY-MM-DD |
| Typical Value | 2023-01-15 |
| BPS Panel / Function | BK history tracing |
| Newrez → BPS Rule | Direct copy (bkfileddate → status_date; same as bk_status_date) |
| Newrez Status | ✅ Provided |
| Newrez Verify Result | [data_date 2026-06-01] 2026-04-27 \| 2025-12-29 \| 2025-04-02 \| 2025-05-27 \| 2022-08-18 \| 2021-03-07 \| 2018-08-29 \| 2025-07-12 \| 2023-10-24 \| 2026-04-01 (10 rows) |
| BPS Verify Result | [BPS prod \| data date fctrdt≤2026-06-01 \| ETL load 2026-06-03] non-null 67/69 \| range 2003-11-14~2026-05-29 |

Newrez Verify SQL:
```sql
-- Verify against mysql_dev, data date 2026-06-01
SELECT loanid, dataasof, bkfileddate
FROM   newrez.portnewrezbk
WHERE  dataasof = '2026-06-01'
  AND  bkfileddate IS NOT NULL
LIMIT  10;
```

BPS Verify SQL (prod, read-only):
```sql
-- Verify against prod bpms (read-only)
SELECT '2026-06-01' AS data_date, COUNT(*) AS total, COUNT(`status_date`) AS non_null,
       MIN(`status_date`) AS min_dt, MAX(`status_date`) AS max_dt
FROM   bpms.sync_loan_foreclosure_bankruptcy;
```

##### `bk_removal_date` · P1 · BK Fields

| Attribute | Value |
|---|---|
| Newrez Raw Field | `bkremovaldate` |
| Data Type | DATE |
| Business Meaning | Date the bankruptcy proceeding was terminated; `variance_completed_bankruptcy` logic: `activebkflag=0 AND bkremovaldate IS NOT NULL` |
| Format / Allowed Values | YYYY-MM-DD |
| Typical Value | 2024-06-01 |
| BPS Panel / Function | `variance_completed_bankruptcy` calculation (activebkflag=0 AND bkremovaldate IS NOT NULL) |
| Newrez → BPS Rule | N/A — BPS bankruptcy table has no removal column |
| Newrez Status | ✅ Provided |
| Newrez Verify Result | [data_date 2026-06-01] 2025-12-08 \| 2026-01-08 \| 2023-04-20 \| 2021-06-08 \| 2022-12-30 \| 2023-06-21 \| 2026-03-25 \| 2025-07-29 \| 2024-06-24 \| 2026-04-14 (10 rows) |
| BPS Verify Result | N/A — not mapped to a BPS FCL sync table (see Newrez → BPS Rule) |

Newrez Verify SQL:
```sql
-- Verify against mysql_dev, data date 2026-06-01
SELECT loanid, dataasof, bkremovaldate
FROM   newrez.portnewrezbk
WHERE  dataasof = '2026-06-01'
  AND  bkremovaldate IS NOT NULL
LIMIT  10;
```

##### `mfr_filed_date` · P1 · BK Fields

| Attribute | Value |
|---|---|
| Newrez Raw Field | `mfrfileddate` |
| Data Type | DATE |
| Business Meaning | Date the lender filed a Motion for Relief (MFR) from the Automatic Stay with the bankruptcy court; foreclosure can resume if MFR is granted |
| Format / Allowed Values | YYYY-MM-DD |
| Typical Value | 2025-08-01 |
| BPS Panel / Function | BK panel MFR Filed Date |
| Newrez → BPS Rule | BPS mfr_filed_date column exists but the Newrez extraction path hard-codes NULL (not from mfrfileddate) |
| Newrez Status | ✅ Provided |
| Newrez Verify Result | [data_date 2026-06-01] 2025-11-04 \| 2025-11-21 \| 2026-04-29 \| 2026-02-04 \| 2025-06-10 (5 rows) |
| BPS Verify Result | [BPS prod \| data date fctrdt≤2026-06-01 \| ETL load 2026-06-03] non-null 4/69 \| range 2020-10-19~2026-04-10 |

Newrez Verify SQL:
```sql
-- Verify against mysql_dev, data date 2026-06-01
SELECT loanid, dataasof, mfrfileddate
FROM   newrez.portnewrezbk
WHERE  dataasof = '2026-06-01'
  AND  mfrfileddate IS NOT NULL
LIMIT  10;
```

BPS Verify SQL (prod, read-only):
```sql
-- Verify against prod bpms (read-only)
SELECT '2026-06-01' AS data_date, COUNT(*) AS total, COUNT(`mfr_filed_date`) AS non_null,
       MIN(`mfr_filed_date`) AS min_dt, MAX(`mfr_filed_date`) AS max_dt
FROM   bpms.sync_loan_foreclosure_bankruptcy;
```

##### `mfr_hearing_results` · P1 · BK Fields

| Attribute | Value |
|---|---|
| Newrez Raw Field | `mfrhearingresults` |
| Data Type | INT |
| Business Meaning | MFR hearing outcome. Newrez raw `mfrhearingresults` is an integer code (0/3/4/5/6 observed); BPS `mfr_status` is empty in dev (0/64) — whether/how it flows downstream is TBD; if granted, foreclosure proceedings may resume |
| Format / Allowed Values | Positive integer |
| Typical Value | 0 |
| BPS Panel / Function | BK panel MFR Status |
| Newrez → BPS Rule | N/A — BPS mfr_status is hard-coded NULL (not from mfrhearingresults) |
| Newrez Status | ⚠️ Newrez provides a raw numeric code (0/3/4/5/6 observed); BPS `mfr_status` column is empty in dev (0/64) — downstream population/decode TBD |
| Newrez Verify Result | [data_date 2026-06-01] 3:3 \| 4:1 \| 5:1 |
| BPS Verify Result | N/A — not mapped to a BPS FCL sync table (see Newrez → BPS Rule) |

Newrez Verify SQL:
```sql
-- Verify against mysql_dev, data date 2026-06-01
SELECT dataasof AS data_date, mfrhearingresults AS code, COUNT(*) AS cnt
FROM   newrez.portnewrezbk
WHERE  dataasof = '2026-06-01'
  AND  mfrhearingresults IS NOT NULL AND mfrhearingresults != ''
GROUP  BY dataasof, mfrhearingresults ORDER BY cnt DESC;
```

##### `proof_of_claim_date` · P1 · BK Fields

| Attribute | Value |
|---|---|
| Newrez Raw Field | `pocfileddate` |
| Data Type | DATE |
| Business Meaning | Date the lender formally registered its debt claim amount (Proof of Claim) with the bankruptcy court; required for bankruptcy compliance |
| Format / Allowed Values | YYYY-MM-DD |
| Typical Value | 2023-03-01 |
| BPS Panel / Function | BK panel Proof of Claim Date |
| Newrez → BPS Rule | Direct copy (pocfileddate → proof_of_claim_date) |
| Newrez Status | ✅ Provided |
| Newrez Verify Result | [data_date 2026-06-01] 2025-08-05 \| 2022-10-17 \| 2025-09-22 \| 2023-11-15 \| 2023-09-30 \| 2025-06-27 \| 2001-01-01 \| 2010-06-17 \| 2010-06-17 \| 2024-03-29 (10 rows) |
| BPS Verify Result | [BPS prod \| data date fctrdt≤2026-06-01 \| ETL load 2026-06-03] non-null 24/69 \| range 2001-01-01~2026-05-04 |

Newrez Verify SQL:
```sql
-- Verify against mysql_dev, data date 2026-06-01
SELECT loanid, dataasof, pocfileddate
FROM   newrez.portnewrezbk
WHERE  dataasof = '2026-06-01'
  AND  pocfileddate IS NOT NULL
LIMIT  10;
```

BPS Verify SQL (prod, read-only):
```sql
-- Verify against prod bpms (read-only)
SELECT '2026-06-01' AS data_date, COUNT(*) AS total, COUNT(`proof_of_claim_date`) AS non_null,
       MIN(`proof_of_claim_date`) AS min_dt, MAX(`proof_of_claim_date`) AS max_dt
FROM   bpms.sync_loan_foreclosure_bankruptcy;
```

##### `post_petition_due_date` · P1 · BK Fields

| Attribute | Value |
|---|---|
| Newrez Raw Field | `bkpostpetitionduedate` |
| Data Type | DATE |
| Business Meaning | Monthly loan payment due date after the bankruptcy petition was filed; used to track whether the borrower continued making payments during Automatic Stay |
| Format / Allowed Values | YYYY-MM-DD |
| Typical Value | 2024-01-01 |
| BPS Panel / Function | BK panel Post Petition Due Date |
| Newrez → BPS Rule | Direct copy (bkpostpetitionduedate → post_petition_due_date) |
| Newrez Status | ✅ Provided |
| Newrez Verify Result | [data_date 2026-06-01] 2026-02-01 \| 2025-11-01 \| 2025-02-01 \| 2021-04-01 \| 2018-09-01 \| 2025-09-01 \| 2025-12-01 \| 2026-05-01 \| 2023-04-01 \| 2026-04-01 (10 rows) |
| BPS Verify Result | [BPS prod \| data date fctrdt≤2026-06-01 \| ETL load 2026-06-03] non-null 25/69 \| range 2018-09-01~2026-07-01 |

Newrez Verify SQL:
```sql
-- Verify against mysql_dev, data date 2026-06-01
SELECT loanid, dataasof, bkpostpetitionduedate
FROM   newrez.portnewrezbk
WHERE  dataasof = '2026-06-01'
  AND  bkpostpetitionduedate IS NOT NULL
LIMIT  10;
```

BPS Verify SQL (prod, read-only):
```sql
-- Verify against prod bpms (read-only)
SELECT '2026-06-01' AS data_date, COUNT(*) AS total, COUNT(`post_petition_due_date`) AS non_null,
       MIN(`post_petition_due_date`) AS min_dt, MAX(`post_petition_due_date`) AS max_dt
FROM   bpms.sync_loan_foreclosure_bankruptcy;
```

<!-- FS-CARDS:4.1 END -->



---

## Section 5: Servicer Compliance Status Matrix

### 5.1 Newrez Current Compliance Summary (MCP Live Measurements, 2026-05)

| Field Group | Section | Total Fields | ✅ Provided | ⚠️ Partial | ❌ Not Provided | Compliance Rate |
|---|---|---|---|---|---|---|
| **Four-Dimension State Foundation** | **2.0** | **12** | **1** | **5** | **6** | **~8%** |
| Identification / Entry | 2.1 | 7 | 7 | 0 | 0 | **100%** |
| FCL Status | 2.2 | 9 | 7 | 2 | 0 | **88%** |
| FCL Timeline | 2.3 | 16 | 9 | 2 | 4 | **~56%** |
| Hold Slots | 2.4 | 12 | 12 | 0 | 0 | **100%** |
| Bid / Sale | 2.5 | 3 | 2 | 1 | 0 | **83%** |
| Loan Attribute Enhancement | 2.6 + 2.4 supplement | 12 | 9 | 0 | 0 | **~75%** |
| LM Cycle | 3.1 | 10 | 7 | 0 | 3 | **70%** |
| Bankruptcy | 4.1 | 11 | 8 | 3 | 0 | **91%** |
| **Total** | — | **92** | **62** | **13** | **13** | **~67%** |

### 5.2 Newrez Fields Not Provided (Formal Completion Request Basis)

The following 6 fields are **completely absent from Newrez** (0%); the corresponding BPS panel functions are affected:

| Field | Newrez Raw Field (missing/empty) | Business Impact | Priority | Affected BPS Panel |
|---|---|---|---|---|
| `noi_date` | *(none; Newrez conflates with `demandsentdate`)* | BPS `timeline_notice_of_intent_date` and Time Line Tab `noi_start_date` currently use `demandsentdate` as substitute; formal NOI date and demand letter date cannot be distinguished | P1 | Milestone Notice of Intent Date; Time Line Tab NOI Date 1 |
| `publication_date` | *(no corresponding field)* | BPS PUBLICATION stage always blank; Stage classification layer never triggers | P2 | Timeline Publication Date 5; Stage PUBLICATION group |
| `title_received_date` | `titlereceiveddate` (field exists but always empty) | Title received date always blank | P2 | Timeline `timeline_title_report_received_date` |
| `title_clear_date` | `titlecleardate` (field exists but always empty) | Title clearance date always blank (both preliminary and final affected) | P2 | Timeline preliminary/final title cleared |
| `borrower_intentions` | `borrowerintention` (field exists but always empty) | LM panel Borrower Intentions column always blank | P2 | LM Cycle Borrower Intentions |
| `imminent_default` | *(no corresponding field)* | CFPB Reg X imminent default indicator always blank | P2 | LM Cycle Imminent Default |
| `single_point_of_contact` | *(no corresponding field)* | CFPB Reg X 12 CFR 1024.40 single point of contact always blank | P2 | LM Cycle Single Point of Contact |

### 5.3 Newrez Partially-Provided Fields — Watch Items

Fields Newrez provides but with quality concerns:

| Field | Issue | Fill Rate | Priority |
|---|---|---|---|
| `currentmilestone` | **ETL does not consume this column**: `summary_current_step` always takes `fcstage` direct (pool:282; currentmilestone has 0 refs in repo). The 62.7% fill rate is irrelevant to BPS | 62.7% | — (downgraded: not a BPS source) |
| `fcsaleamount` | Fill rate (4.7%) > `fcsalehelddate` (2.1%); possible field sequencing issue (amount arrives before held date) | 4.7% | P1 ⚠️ |
| `firstlegaldate` | 57.6%; some Non-Judicial state loans may legitimately have no First Legal date | 57.6% | P1 ⚠️ |
| `servicecompletedate` | 28.9%; only loans that have passed the Service stage will have this (partially expected) | 28.9% | P1 |

---

## Section 6: Delivery Format Specification

### 6.1 Basic Delivery Specifications

| Specification | Requirement | BPS-Specific Note |
|---|---|---|
| Frequency | **Daily** (recommended); monthly only for small loan portfolios | Monthly delivery causes FCL Stage day count errors of up to 30 days; daily minimizes data lag |
| File format | CSV (UTF-8 without BOM) or Fixed-width TXT | Prohibit xlsx; avoid BOM which causes field parse errors |
| Date format | **`YYYY-MM-DD`** is the only accepted standard | BPS date fields do not tolerate non-standard formats (e.g., MM/DD/YYYY); non-standard formats cause field parse failures |
| NULL handling | Empty string `''` or `NULL` both acceptable | **Prohibited**: `N/A`, `NA`, `0001-01-01` (system will misidentify as valid values) |
| File naming | `{servicer}_{report_type}_{YYYYMMDD}.csv` | Examples: `newrez_fcl_main_20260527.csv`, `newrez_lm_20260527.csv` |

### 6.2 Data Model Structure

| File / Batch | Contents | Rows Per Loan |
|---|---|---|
| FCL main file | Sections 2.1–2.3 (identification/status/timeline) + 2.4 (Hold slots) + 2.5 (Bid/Sale) | 1 row/loan (snapshot) |
| LM file | Section 3.1 LM cycle fields | **Multiple rows/loan** (one row per LM cycle; history not overwritten) |
| BK file | Section 4.1 BK fields | Multiple rows/loan (one record per bankruptcy) |
| **Decode mapping table** (required) | LM fields (deal/program/status/disposition) int→text mapping | Separate file |

### 6.3 Encoded Field Decode Mapping Requirements

**Affected fields**: `lmdeal`, `lmprogram`, `lmstatus`, `lmdecision`, `denialreason` (LM); and `bkstatus`, `bkstage`, `mfrhearingresults` (BK, TBD)

**Requirements**:
1. Decode mapping table must be submitted with the first data delivery
2. Any changes to the decode mapping must be pre-notified; BPS will resync historical data
3. BPS does not accept LM records submitted as numeric codes only

Mapping table format example:
```
field_name,code,text_label
lmdeal,7,DIL
lmdeal,1,Evaluation
lmprogram,10,Deed-in-Lieu
...
```

### 6.4 Hold Slot Delivery Notes

- Newrez currently provides 3 fixed hold slots (`fchold1/2/3`); if a loan has more than 3 active holds, slots must be rotated in chronological order (earliest hold must end before a new hold can enter the slot)
- BPS appends a new row on each hold field change, accumulating the complete history
- Servicers must provide a complete daily snapshot (including all currently active holds), not just delta/changes

---

## Section 7: Field Completion Request Priority Summary

This section summarizes the priority order for formally requesting Servicer field completion.

### 7.1 P0 Fields (Missing = Rejected from BPS — Must Fix Immediately)

Any of the following 7 fields missing will prevent the loan from being processed by BPS:

| Field | Newrez Raw Field | Newrez Status |
|---|---|---|
| `loan_id` | `loanid` | ✅ 100% (Newrez compliant) |
| `servicer_loan_id` | `shellpointloanid` | ✅ 100% |
| `data_as_of_date` | `dataasof` | ✅ 100% |
| `state` | `state` | ✅ 100% |
| `judicial_flag` | `judicial` | ✅ 100% |
| `active_fcl_flag` | `activefcflag` | ✅ 100% (historical NULLs require NULL-safe handling) |
| `fcl_referral_date` | `fcreferraldate` | ✅ 100% |

> Newrez is currently compliant on all P0 fields. **When onboarding a new Servicer, validate these 7 fields first.**

### 7.2 P1 Fields — Current Newrez Issues (Action Recommended)

| Field | Issue | Priority |
|---|---|---|
| `currentmilestone` | Not consumed by ETL (summary_current_step takes fcstage direct); improving fill rate has no BPS effect | — (not a BPS source) |
| `fcsaleamount` | 4.7% vs `fcsalehelddate` 2.1% (sequencing anomaly; see Q9) | P1 ⚠️ Investigate |
| `firstlegaldate` | 57.6% (partially expected; distinguish "not yet reached" from "not reported") | P1 |
| `servicecompletedate` | 28.9% (partially expected for early-stage loans) | P1 |

### 7.3 P2 Fields — Newrez Not Providing (Formal Completion Request Recommended)

| Field | Affected BPS Function | Reason to Request |
|---|---|---|
| `publication_date` | BPS PUBLICATION stage always blank | Complete timeline; Stage classification completeness |
| `titlereceiveddate` | Title received date always blank | Timeline completeness |
| `titlecleardate` | Title clearance date always blank | Timeline completeness |
| `borrowerintention` | LM borrower intentions column always blank | LM panel completeness |
| `imminent_default` | CFPB Reg X indicator blank | Compliance metric completeness |
| `single_point_of_contact` | CFPB Reg X 12 CFR 1024.40 indicator blank | Compliance metric completeness |

---

## Appendix A: BPS Panel → Servicer Fields Reverse Lookup Index

> Use case: Quickly look up "which Servicer fields are required" starting from "what BPS displays." Useful for BPS panel troubleshooting and field-by-field verification when onboarding a new Servicer.

| BPS Panel | UI Key Column / Function | Required Servicer Fields | Priority |
|---|---|---|---|
| **FCL Milestone Timeline** | NOI Date | `demandsentdate` | P1 |
| | Referral Date | `fcreferraldate` | P0 |
| | First Legal Date | `firstlegaldate` | P1 |
| | Service Date | `servicecompletedate` | P1 |
| | Publication Date | *(Newrez does not provide)* | P2 ❌ |
| | Judgement Date | `fcjudgmenthearingscheduled` | P1 |
| | Sale Date | `fcscheduledsaledate` | P1 |
| | Foreclosure Completed | `dtdeedrecorded` / `fcremovaldate` | P1/P2 |
| **FCL Summary Panel** | Current Step | `fcstage` (direct passthrough; `currentmilestone` not used by ETL) | P1 |
| | Attorney | `fcfirm` | P1 |
| | SMS Days / Days in FCL | `smsdaysinfc` + `dataasof` / `daysinfc` + `dataasof` | P1 |
| | Sale Amount | `fcsaleamount` | P1 |
| **Hold Panel** | Description / Start / End | `fchold{1/2/3}description` / `startdate` / `enddate` | P1 |
| | Estimated Hold Days | `fchold{1/2/3}projectedenddate` | P2 |
| **LM Cycle Panel** | Deal / Program / Status | `lmdeal`+decode / `lmprogram`+decode / `lmstatus`+decode | P1 |
| | Cycle Opened/Closed | `dealstartdate` / `lmremovaldate` | P1 |
| | Final Disposition | `lmdecision`+decode | P1 |
| | Borrower Intentions | `borrowerintention`+decode | P2 ❌ (Newrez not providing) |
| | Imminent Default | *(Newrez does not provide)* | P2 ❌ |
| **Bankruptcy Panel** | Chapter / Status / MFR | `bkchapter` / `bkstatus` / `mfrhearingresults` | P1 |
| | MFR Filed / POC Date | `mfrfileddate` / `pocfileddate` | P1 |
| | Post Petition Due Date | `bkpostpetitionduedate` | P1 |
| **Aggregate Stage Tab** | Stage grouping | `fcreferraldate`+`firstlegaldate`+`servicecompletedate`+`fcjudgmenthearingscheduled`+`fcscheduledsaledate` | P0/P1 |
| | Days in Stage | ETL-computed from above dates (BPS side) | N/A |
| **Aggregate Time Line Tab** | NOI Date 1 | `demandsentdate` (→ `demand_start_date`; NOT `noi_start_date`) ⚠️ | P1 |
| | Referral Date 2 | `fcreferraldate` → `referral_start_date` | P0 |
| | First Legal Date 3 | `firstlegaldate` → `first_legal_start_date` | P1 |
| | Service Date 4 | `servicecompletedate` → `service_start_date` | P1 |
| | Publication Date 5 | *(Newrez does not provide)* → `publication_start_date` always NULL | P2 ❌ |
| | Judgement Date 6 | `fcjudgmenthearingscheduled` → `judgement_start_date` | P1 |
| | Sale Date 7 | `fcscheduledsaledate` → `sale_start_date` | P1 |

> **Time Line Tab NOI Date 1 — Important**: Newrez `demandsentdate` maps to BPS `demand_start_date`, NOT to `noi_start_date`; therefore the Time Line Tab's "NOI Date 1" column is **always blank for Newrez loans**. To look up the Demand Letter date for a Newrez loan, query `demand_start_date` (the field used for Stage Tab day-count calculations) — do not rely on the Time Line Tab's NOI Date column for Newrez.

---

## Appendix B: ETL Intermediate Table Field Classification — BPS Active vs Future Tracking Reserved

> **Data source**: `port.basic_data_loan_fcl` (Redshift ETL intermediate table, cross-servicer UNION, ~37 business fields + Hold slots)  
> **Source code**: `basic_data_pool_config.py` (FCL UNION query, lines 1490–1600)  
> **Legend**:
> - ✅ **BPS Active**: Field flows to BPS MySQL (`bpms.basic_data_loan_foreclosure` or `bpms.sync_*` tables) and drives BPS UI display
> - 🔮 **ETL Reserved / Not in BPS**: Field is normalized and stored in the intermediate table but not consumed by any downstream BPS ETL; available for future loan state tracking analytics

| Intermediate Table Field | Legend | Corresponding BPS Field (if active) / Future Use (if reserved) |
|---|---|---|
| `dataasof` | ✅ | `fctrdt` (data-as-of date, all BPS FCL tables) |
| `loanid` | ✅ | `loanid` (primary key in all BPS FCL tables) |
| `servicer` | ✅ | Servicer identifier |
| `svc_loanid` | ✅ | `svcloanid` |
| `activefcflag` | ✅ | Basis for `summary_foreclosure_status` derivation |
| `titleordereddate` | 🔮 | Future: title tracking chain completeness analysis (chain starting point) |
| `titlereceiveddate` | ✅ | `timeline_title_report_received_date` |
| `titlecleardate` | ✅ | `timeline_preliminary_title_cleared_date` / `timeline_final_title_cleared_date` |
| `noi_date` | ✅ | `timeline_notice_of_intent_date` |
| `fcsetupdate` | ✅ | `timeline_approved_for_referral_date` |
| `referral_start_date` | ✅ | `timeline_referred_to_foreclosure_date` |
| `svc_days_infc` | ✅ | `summary_sms_days_in_fcl` (real-time recalculation) |
| `daysinfc` | ✅ | `summary_days_in_fcl` (real-time recalculation) |
| `demandsentdate` | ✅ | `timeline_notice_of_intent_date` + `demand_start_date` |
| `demandexpirationdate` | ✅ | `timeline_notice_of_intent_end_date` |
| `legal_start_date` | ✅ | `timeline_first_legal_date` |
| `service_start_date` | ✅ | `timeline_service_date` |
| `fcjudgment_hearing_scheduled` | ✅ | `timeline_judgement_date` / `judgement_start_date` (Stage Tab) |
| `fcjudgment_end_date` | 🔮 | Future: `actual_judgement_hearing_set_days` = `fcjudgment_end_date` − `fcjudgment_hearing_scheduled` (see doc 13 Q12) |
| `fcscheduled_sale_date` | ✅ | `timeline_sale_date_projected_date` / `sale_start_date` |
| `fcsale_held_date` | ✅ | `timeline_sale_date_held_date` |
| `fcbidamount` | ✅ | `bid_approval_bid_amount` |
| `fcapprbidprice` | ✅ | `bid_approval_bid_amount` (combined display) |
| `fcsaleamount` | ✅ | `summary_foreclosure_sale_amount` |
| `fcl3rdpartyproceedsreceiveddate` | ✅ | `timeline_third_party_proceeds_received_date` |
| `fcresults` | ✅ | Basis for `summary_completed_foreclosure` derivation |
| `fcstage` | ✅ | `summary_current_step` (secondary priority) |
| `lastfcstepcompleted` | ✅ | `summary_last_step_completed` |
| `lastfcstepcompleteddate` | ✅ | `summary_last_step_completed_date` |
| `fcremovaldesc` | ✅ | Basis for `summary_foreclosure_status` derivation |
| `fcremovaldate` | ✅ | `timeline_foreclosure_completed_date` |
| `judicial` | ✅ | `summary_judicial_foreclosure` / `summary_type` |
| `fcfirm` | ✅ | `summary_foreclosure_attorney` / `summary_firm` |
| `fccontestedflag` | ✅ | `summary_contested_litigation` |
| `jr_sr_lien_flag` | 🔮 | Future: lien risk analysis (junior lien complexity assessment) |
| `dtdeedrecorded` | ✅ | `timeline_foreclosure_completed_date` (preferred source) |
| `activejnrlienfcflag` | 🔮 | Future: active junior lien FCL status tracking |
| **Hold slots (via JOIN)**: `hold_{n}_description` / `start_date` / `end_date` / `projected_end_date` | ✅ | `bpms.sync_loan_foreclosure_hold` (full Hold history table) |

> **Servicer Note**:
> - **✅ Fields**: Must provide — missing fields cause BPS panel display errors (P0/P1) or disable analytics functions (P2). See Sections 2–4 for specific priorities.
> - **🔮 Fields**: Optional — no current impact on BPS display. If provided, our ETL can normalize and store them immediately, laying the data foundation for future loan state tracking features.

---

*Document end — doc 14 v2 (2026-05-28)*
