# doc 13 — Newrez FCL Field Reverse Mapping: BPS Display Fields → Newrez Raw Data

---

## Document Purpose

- **Why this document exists**: Docs 08/09/11 were written from an industry-standard perspective, defining what a Servicer *should* provide. This document flips the perspective — starting from what BPS Asset Management's Foreclosure screen *actually displays*, and tracing each displayed field back to the exact Newrez raw table, column, and calculation rule.
- **Problem solved**: When a FCL field on the BPS screen shows an unexpected value, operations and data teams need to immediately know where that value comes from. This document provides a direct Newrez raw field → BPS display field mapping without needing to read ETL code.
- **Scope**: Newrez only (largest servicer, 13,321 active FCL loans); FCL-related fields only. **Not covered**: intermediate ETL code, Redshift staging tables, sync pipeline details (see doc 12).
- **System fit**: This document is the results-oriented companion to doc 08 (field mapping status) and the business-meaning annotation to doc 12 (ETL pipeline).

## Target Audience

Primary: Operations analysts · Data quality engineers · BPS system acceptance testers  
Secondary: New ETL developers · FCL data governance team · Future AI sessions

## Revision History

| Date | Author | Version | Changes | Related |
|------|--------|---------|---------|---------|
| 2026-06-04 | AI Agent (Claude Opus 4.8) | v36 | **Section 8: added Q13/Q14 (doc 19 field-validation findings)**. Q13 `summary_current_step` documented `COALESCE(currentmilestone, fcstage)` vs measured BPS=`fcstage` (currentmilestone non-empty yet unused, 4/4 hit loans) — documented order reversed, or overwrite-snapshot load timing; **pending ETL-code verification (basic_data_pool_config.py, outside this repo)** (conflicts with Q4 — added conflict pointers at Q4 + §3.7). Q14: 8 BPS main-table fields unpopulated (src has values / BPS empty: timeline_notice_of_intent(_end)/approved_for_referral/referred_to_attorney/foreclosure_completed, summary_servicer_number/completed_foreclosure/foreclosure_attorney; same-source summary_firm IS filled = partial fill). Synced with doc 16 ① FCL Summary note + doc 19 main sheet annotation | doc 19 measured 2026-06-04 · doc 16 · doc 14 v34 |
| 2026-06-04 | AI Agent (Claude Opus 4.8) | v35 | **Corrected §3.7 `summary_foreclosure_status` mapping rule** (code + DB verified): the old `activefcflag=1 → use fcstage; =0 → fcresults or fcremovaldesc` was **wrong**. Actual logic (basic_data_pool_config.py:273 GEN_FCL_DETAIL): `activefcflag=1` → fixed text `'Active Foreclosure'`; `activefcflag=0` and `fcremovaldesc` non-empty → `'Closed Foreclosure:'+fcremovaldesc`; else NULL. `fcstage` actually populates `summary_current_step`; `fcresults` is unused. Also updated: business meaning, §3 header note, two appendix source notes (flagged as stale dev sample), and expanded Type/Current Step/Completed Foreclosure arrow shorthand into full "if…then…". DB: Active 43/Closed 50/NULL 1 all match; 4 stale rows noted. Synced with doc 16/14 | basic_data_pool_config.py:273 · doc 14 v33 · doc 16 v3 |
| 2026-06-03 | AI Agent (Claude Opus 4.8) | v34 | §3.7 footnote: added the start-date basis for `summary_sms_days_in_fcl` vs `summary_days_in_fcl` (code + DB verified): days ← `fcreferraldate` (datediff+1, :1628) = investor/full; sms ← Newrez native `smsdaysinfc` (svc_days_infc, :280/:1545) counted from `fcsetupdate` = servicer/SMS basis → sms≤days (only 2 of 91 differ); both get BPS +DATEDIFF real-time adjustment (:597-598). Synced with doc 14 v31 | basic_data_pool_config.py · doc 14 v31 |
| 2026-06-03 | AI Agent (Claude Opus 4.8) | v33 | §5 numeric-decode mechanism traced (code + DB verified): lmdeal/lmprogram/lmstatus/lmdecision/borrowerintention/denialreason decode source = **Redshift dict table `newrez.portnewrezdatadic`** (not in dev MySQL); decode JOINs at `basic_data_pool_config.py:835-840` (BK at :367), not hardcoded; LMDeal dict = 13 codes, 8 observed; noted that a cross-table join `lmdeal=1→Evaluation` is a snapshot-timing artifact | basic_data_pool_config.py:835-840; Redshift portnewrezdatadic; data dictionary |
| 2026-06-03 | AI Agent (Claude Opus 4.8) | v32 | [Readability] Unified middle-dot `·` separators in value/enum lists to `\|` (consistent with doc 14): currentmilestone / fchold descriptions / stage output fields / bk decode / Q7 (13 spots). Kept `·` in "X stage · sub-meaning" structural labels, audience line, env labels, cross-references, and revision history | doc 14 v24 |
| 2026-06-03 | AI Agent (Claude Opus 4.8) | v31 | [Terminology fix] `activefcflag=0` was wrongly called "completed" in several places; it actually means **not currently in active foreclosure** — DB-verified (referred-to-FCL & activefcflag=0): Reinstated 26 / Loss Mitigation 16 / Paid in Full 11 (stopped, not completed) vs REO·3rd·DiL 10 (truly completed); BPS labels all "Closed Foreclosure" ≠ Completed. Fixed Section 1 entry table, Section 3.7 summary_completed_foreclosure, Section 7 population framing, Section 8 Q3, activefcflag definition; synced to doc 16/doc 14 | DB-verified 2026-06-03 |
| 2026-06-02 | AI Agent (Claude Opus 4.8) | v30b | [ETL code + DB verified] Section 6 Bankruptcy mapping corrected: `status_date`←`bkfileddate` (not bkrcurrentstatusdate); `lien_status`/`mfr_status`/`claim_status`/`mfr_filed_date` hardcoded NULL in extract; `bankruptcy_status`=COALESCE(datadic decode, bkstatus) | basic_data_pool_config.py:349-363 |
| 2026-06-01 | AI Agent (Claude Sonnet 4.6) | v29 | Section 2: added value-range/sample-value content to all three subtables — 2.1: new standalone supplementary table '2.1-B Value Range / Examples' (42 fields, date ranges and enum values from live MCP Redshift queries); 2.2 and 2.3: new 4th column 'Value Range / Examples'; zh+en versions updated | — |
| 2026-05-26 | AI Agent (Claude Sonnet 4.6) | v1 | Initial version — complete BPS FCL display field reverse mapping; validated via MCP | doc 08, doc 12 |
| 2026-05-26 | AI Agent (Claude Sonnet 4.6) | v2 | UI screenshot re-verification: ①corrected main BPS table name (sync_loan_foreclosure); ②corrected view column count (104); ③rewrote Hold section (full history model); ④added LM Cycle, Bankruptcy, and Aggregate View panel mappings; ⑤corrected LM field encoding description (BPS stores decoded text, not numeric codes); ⑥updated appendix with multi-panel validation for loan 7727000088 | doc 08, doc 12 |
| 2026-05-26 | AI Agent (Claude Sonnet 4.6) | v3 | Section 3.1–3.7 table structure overhaul: ①added new first column "BPS UI Label" (Panel > Field display text, derived from BPS UI + MCP COLUMN_COMMENT); ②merged "Source Table" into "Newrez Raw Field" as full-path single column (`newrez.schema.table.field`); ③added new last column "Business Meaning" (derived from MCP COLUMN_COMMENT + existing notes); ④BPS full field path documented via per-subsection header note; ⑤Section 3.4 converted from text block to structured table | MCP COLUMN_COMMENT |
| 2026-05-26 | AI Agent (Claude Sonnet 4.6) | v4 | Added "Glossary" section (12-term quick reference: NOI/Demand Letter distinction, Target/Actual/Var Days framework, dataasof, SMS/Shellpoint, MFR, POC, 3rd Party Sale, etc.), positioned between Screenshots and Section 1; full definitions also added to doc 10 v2 | doc 10 v2 |
| 2026-05-26 | AI Agent (Claude Sonnet 4.6) | v5 | Table width optimization (Plan A): extracted `newrez.portnewrezfc.` prefix from cell values to per-section header notes; cells now show field name only. Section 3.5 retains short table name prefix (`portnewrezbk.` / `portnewrezfc.`) to disambiguate mixed-source fields. Updated column headers and section header notes throughout Section 3. | — |
| 2026-05-27 | AI Agent (Claude Sonnet 4.6) | v6 | MCP fill rate verification: measured all `—` fields against 13,360 active FCL loans. Key findings: `titlereceiveddate`/`titlecleardate`=0% (Newrez does not report these), `servicecompletedate`=28.9%, `fcjudgmententered`=7.9%; Section 3.7 updated with live rates (`shellpointloanid`/`fcfirm`=100%, `lastfcstepcompleted`=99.5%, `fcsaleamount`=4.7%⚠️); Section 8 added Q8/Q9 (title fields always null + sale amount anomaly). | — |
| 2026-05-27 | AI Agent (Claude Sonnet 4.6) | v7 | Column reorder: moved "Business Meaning" to 2nd column in all Section 3.x tables (3.1–3.7) for beginner-friendly readability — business context first, technical fields after. | — |
| 2026-05-27 | AI Agent (Claude Sonnet 4.6) | v8 | Disambiguate two ambiguities: ①Added "Mapping Rule" column semantics note at Section 3 header (data flow direction Newrez→BPS vs. document lookup direction BPS→Newrez); ②Section 3.4 header note now clarifies formula operands (actual_*/target_*) are both from bpms_dev.sync_loan_foreclosure (no Newrez data involved). | — |
| 2026-05-27 | AI Agent (Claude Sonnet 4.6) | v9 | Added Appendix B: Data Verification SQL (SQL-1 through SQL-7), covering all MCP-query-derived data in this document — field fill rates (SQL-1), fcresults distribution (SQL-2), Q9 anomaly verification (SQL-3), specific loan raw fields (SQL-4), Hold history (SQL-5), LM history (SQL-6), Bankruptcy check (SQL-7); Section 2.1 / 3.1 / Appendix A each have a new SQL reference note. | — |
| 2026-05-27 | AI Agent (Claude Sonnet 4.6) | v10 | Clarify third mapping rule ambiguity: added 4th bullet to Section 3 opening note, explicitly stating that field names in mapping rule expressions (e.g. `activefcflag`, `judicial`) belong to the Newrez source table specified in each section's header — no BPS fields are involved in mapping rule expressions. | — |
| 2026-05-27 | AI Agent (Claude Sonnet 4.6) | v11 | Full Appendix B SQL coverage: ①Added SQL-8 (queries `bpms_dev.sync_loan_foreclosure` for all three field groups: target_*/actual_*/var_*, covering Sections 3.2/3.3/3.4); ②Added "Verification SQL" header notes to Sections 3.2–3.7, Section 4, Section 5, and Section 8 pointing to relevant SQL queries in Appendix B. | — |
| 2026-05-27 | AI Agent (Claude Sonnet 4.6) | v12 | Added data range documentation to all pages: Section 7 (Aggregation Overview) — entry filter, loan count (~13,321), and source table header note; Sections 4/5/6 — "single-loan view" data range notes; Appendix B — SQL-9 (`sync_fcl_stage_info` stage distribution query to reproduce aggregation overview totals). | — |
| 2026-05-27 | AI Agent (Claude Sonnet 4.6) | v13 | Section 7: added "Stage Classification Logic" subsection — waterfall priority table (7 levels), per-stage classification conditions (Newrez `portnewrezfc` fields), key notes, and screenshot data consistency verification; Appendix B: added SQL-10 (JOIN `portnewrezfc` to verify stage field conditions). | — |
| 2026-05-27 | AI Agent (Claude Sonnet 4.6) | v14 | Section 5: added two new subsections — ① "LM Field Values and Business Meaning" (four tables covering Deal / Program / Status / Final Disposition); ② "Why Does LM Have Multiple Cycles?" (4 root causes + loanid=7727000088 9-round timeline analysis); Appendix B: added SQL-11 (full LM field value distribution query). | — |
| 2026-05-27 | AI Agent (Claude Sonnet 4.6) | v15 | Section 7 "Stage Classification Logic" table: added fourth column "BPS Output Fields (`sync_fcl_stage_info`)" making the Newrez condition → BPS stored field mapping explicit; added key notes (ETL output field + BPS page display = BPS stored data); SQL-10 expanded to SELECT stage-specific BPS date/days output fields alongside Newrez source conditions, enabling complete cross-pipeline verification. | — |
| 2026-05-27 | AI Agent (Claude Sonnet 4.6) | v16 | MCP live execution revealed three SQL-10 bugs: ① collation mismatch between schemas (utf8mb4_general_ci vs utf8mb4_0900_ai_ci) causes [1267] error; ② both tables are daily snapshot tables (fctrdt/dataasof), loanid-only JOIN produces Cartesian product; ③ missing current-snapshot filter. All three fixed and verified (26 rows, no duplicates). Corrected `stage` column values in classification table to actual DB codes (all-caps: SALE/JUDGEMENT/SERVICE/FIRST_LEGAL/REFERRAL/DEMAND/PUBLICATION); added stage code → BPS display name mapping table; added key notes (snapshot table guidance + collation/Cartesian product handling). | — |
| 2026-05-27 | AI Agent (Claude Sonnet 4.6) | v17 | Section 5: added "UI Column Reference" subsection after the BPS table structure mapping — covers all 10 UI columns (Deal / Program / Status / Cycle Opened Date / Cycle Closed Date / Final Disposition / Denial Reason / Borrower Intentions / Imminent Default / Single Point of Contact) with business role, workflow context, and Newrez-specific notes (CFPB Reg X citations for Imminent Default and Single Point of Contact). | — |
| 2026-05-27 | AI Agent (Claude Sonnet 4.6) | v18 | Glossary: added "Upcoming FC Sales" entry — BPS stage code `SALE`; trigger condition `fcscheduledsaledate IS NOT NULL`; priority 1 (highest); applies to both Judicial states (post-judgment) and Non-Judicial states (post-service/publication); linked to BPS output fields `sale_start_date` / `to_sale_days`. | — |
| 2026-05-27 | AI Agent (Claude Sonnet 4.6) | v19 | Section 7 expanded to dual-tab coverage (Stage Tab + Time Line Tab): ①section title updated; ②added "Time Line Tab" subsection with 12-column field mapping table (MCP JOIN-verified), Group field meanings (FCL/REO/D120P), NOI Date vs. Demand Date distinction, Judgement Date ~11-day discrepancy, and 3-loan sample data; ③Appendix B: added SQL-12 (reproduces Time Line Tab view with demand_start_date comparison column); ④Section 8: added Q10 (judgement_start_date ~11-day gap) and Q11 (noi_start_date always NULL / demand_start_date not mapped to NOI Date column). | — |
| 2026-05-27 | AI Agent (Claude Sonnet 4.6) | v20 | Critical mapping correction (ETL code + MCP data double-confirmed): ①Time Line Tab mapping table — Judgement Date 6 source field changed from `fcjudgmententered` to `fcjudgmenthearingscheduled`; ②Note 4 — rewritten: the ~11-day gap is NOT an ETL processing delay but reflects two fields with completely different business meanings (`fcjudgmenthearingscheduled` = hearing scheduled date / future planned event; `fcjudgmententered` = court formally entered judgment / completed legal fact); ETL code cited: `fc.fcjudgment_hearing_scheduled AS timeline_judgement_date`; ③Q10 — rewritten with same correction; ④SQL-12 comment updated. | ETL `basic_data_pool_config.py` |
| 2026-05-28 | AI Agent (Claude Sonnet 4.6) | v21 | Section 8: added Q12 — `port.basic_data_loan_fcl.fcjudgment_end_date` is stored in the Redshift ETL intermediate table but not consumed by any downstream BPS ETL; documents the architecture gap and design intent (cross-servicer standardized naming + reserved for future `actual_judgement_hearing_set_days` calculation). | doc 12 Section 15 |
| 2026-05-28 | AI Agent (Claude Sonnet 4.6) | v22 | Section 8: added "Q3 Technical Detail" subsection after the Q table — full explanation of `activefcflag` NULL-safe handling: root cause, correct SQL patterns (OR NULL / COALESCE), business logic (closed FCL has explicit multi-field evidence; NULL conservatively treated as in-progress), and impact scope. | doc 08 · doc 14 Section 2.1 |
| 2026-05-28 | AI Agent (Claude Sonnet 4.6) | v23 | Added source-data filter conditions (ETL code verified) for all 5 BPS FCL tables: Section 3.1 — ETL code reference for main FCL table filter; Section 4 (Hold) — two-layer filter conditions + GROUP BY dedup + independence from main FCL table; Section 5 (LM) — `dealstartdate IS NOT NULL` + dedup logic + numeric decode note; Section 6 (BK) — `LENGTH(TRIM(bkstatus)) > 0` + dedup + additional JOIN; Section 7 (Aggregation) — corrected entry filter to `activefcflag=1 AND fcremovaldate IS NULL` + added D90/D120P secondary filter. | ETL code: asset_managment_config.py · basic_data_pool_config.py |
| 2026-05-29 | LiJiawen | v24 | Standardized BPS UI screenshots: added official Figure 13-x titles for all manually inserted screenshots, used relative paths, and synchronized the Chinese screenshot set into the English document at matching sections. | docs/zh/13 |
| 2026-05-29 | LiJiawen | v25 | Renamed the 9 doc 13 screenshot files to business-meaningful English slug filenames and updated both Chinese and English image references. | docs/zh/13 |
| 2026-06-02 | AI Agent (Claude Sonnet 4.6) | v30 | Section 5 LM field values overhauled (MCP SQL-D1/D2/D3 CTE JOIN verified): ① Deal table added `Deferment` (lmdeal=11) and `Payoff` (lmdeal=9), corrected `Repayment Plan` → `Payment Plan` (lmdeal=4), added Newrez code column; ② Program table expanded from 5 to 20 rows (Bridger mod, VA series, FHA series, Deferment, etc.); ③ Status table expanded from 6 to 20 rows; ④ Two BPS-table description fixes: `lmstatus=112` "Awaiting MI Approval"→"Workout Denial", `lmdecision=6` "LMS Opened in Error"→"Referral to FC"; ⑤ UI Column Reference Deal description synced. Synced from zh v30. | SQL-D1/D2/D3 CTE JOIN |
| 2026-06-02 | AI Agent (Claude Sonnet 4.6) | v31 | Appendix B verification SQL: added snapshot-date filters (fixes snapshot-table count inflation). SQL-1/2/3 (query `newrez.portnewrezfc`, a daily-snapshot table: 891 snapshot days × ~7.6K loans) gained `AND dataasof=(SELECT MAX(dataasof)...)`; SQL-9 (queries `bpms_dev.sync_fcl_stage_info`, daily snapshot) gained `fctrdt=(SELECT MAX(fctrdt)...)` on both main query and denominator. Unchanged: SQL-5/6/7/8/11/13 (bpms event/cycle tables, not daily snapshots, ~1-4 rows/loan); SQL-10/12 (already filtered). Data-dictionary verification SQL (SQL-D1~D6) already uses latest-snapshot CTE — no change. | DB verified 2026-06-02 |

## Dependencies

| Resource | Description |
|----------|-------------|
| `newrez.portnewrezfc` | Newrez FCL master data (MCP-verified, 57 columns) |
| `newrez.portnewrezbk` | Newrez bankruptcy data (MCP-verified, 60 columns) |
| `newrez.portnewrezlm` | Newrez loss mitigation data (MCP-verified, 56 columns) |
| `bpms_dev.sync_loan_foreclosure` | BPS FCL master table (MCP-verified, 86 columns) |
| `bpms_dev.sync_loan_foreclosure_hold` | BPS hold history table (MCP-verified, 15 columns) |
| `bpms_dev.sync_loan_foreclosure_loss_mitigation` | BPS LM cycle table (MCP-verified, 22 columns) |
| `bpms_dev.sync_loan_foreclosure_bankruptcy` | BPS bankruptcy table (MCP-verified, 22 columns) |
| `bpms_dev.sync_fcl_stage_info` | BPS stage tracking table (MCP-verified, 57 columns) |
| `bpms_dev.biz_data_view_loan_details_foreclosure` | BPS display view (MCP-verified, **104 columns**) |
| doc 12 | ETL pipeline and intermediate table details |

## Known Limitations

- `timeline_publication_date` has no corresponding field in Newrez source tables; typically null in BPS
- ~14.1% of active FCL loans have no `demandsentdate` (no NOI record)
- `imminent_default` and `single_point_of_contact` in the LM sync table are NULL for all Newrez loans — Newrez does not provide these fields
- ~~`lien_status` and `claim_status` in the Bankruptcy panel: source Newrez fields require further confirmation~~ **(Resolved 2026-06-02)**: `lien_status` / `claim_status` / `mfr_status` / `mfr_filed_date` are **hardcoded `NULL`** in the ETL extract (basic_data_pool_config.py:349-363) — not mapped from any Newrez field. See Section 6.

---

## BPS UI Reference Screenshots

**Figure 13-1 — Loan Foreclosure Detail Page (Loan ID: 7727000088)**

Panels: Foreclosure Milestone timeline, Hold, Foreclosure Summary, Loss Mitigation Cycle, Bankruptcy.

![BPS Loan Foreclosure Detail Page](../zh/image/bps-loan-foreclosure-detail-loan-7727000088.png)

**Figure 13-2 — Foreclosure Aggregate Overview: Stage Tab (/agg-summary)**

Panels: Overview summary table, stage-grouped loan lists with Days in Stage / Days in LM / Days on Hold columns.

![BPS Foreclosure Aggregate Overview](../zh/image/bps-foreclosure-aggregate-stage-tab-summary.png)

**Figure 13-3 — Foreclosure Aggregate Overview: Time Line Tab (/agg-summary)**

Displays the loan-level timeline columns: NOI Date, Referral Date, First Legal Date, Service Date, Publication Date, Judgement Date, and Sale Date.

![BPS Foreclosure Aggregate Overview Time Line Tab](../zh/image/bps-foreclosure-aggregate-time-line-tab.png)

---

## Glossary

> Quick-reference for terms specific to this document. Full definitions for project-wide terms (FCL, REO, LM, BK, Judicial/Non-Judicial, First Legal, Sale, etc.) are in **[doc 10 — ForeclosureRule2 Comprehensive Glossary](../zh/10_glossary.md)**.

| Term | Full Name | Definition |
|---|---|---|
| **NOI** | Notice of Intent | Pre-FCL legal notice from lender to borrower (Judicial states). Demands the borrower cure the default (typically within 30 days) or foreclosure will begin. See Demand Letter below. |
| **Demand Letter** | Demand Letter / Demand Notice | Alternative name for NOI (common in Non-Judicial states). Newrez names its field `demandsentdate`, so this document uses "NOI / Demand" as a unified label. Maps to BPS field `timeline_notice_of_intent_date`. |
| **Referral Date** | FCL Referral Date | The date the lender formally transfers the case to a foreclosure attorney (Newrez: `fcreferraldate`). This is BPS's entry filter (non-null required) and the FCL timeline calculation anchor. |
| **FCL Hold** | Foreclosure Hold | An operational pause in an otherwise active FCL. Common causes: Automatic Stay (bankruptcy), LM negotiation in progress, court delay. BPS records full hold history in the Hold panel (Section 4). |
| **Target Days** | Target Days | System-configured compliance benchmark days per FCL stage (constants set by state / judicial type; not from Newrez). BPS field prefix: `target_*`. See Section 3.2. |
| **Actual Days** | Actual Days | Days elapsed in each FCL stage, calculated as DATEDIFF between two timeline endpoint dates. BPS field prefix: `actual_*`. See Section 3.3. |
| **Var Days** | Variance Days | `Actual Days − Target Days`. Positive = behind target; Negative = ahead of schedule; Zero = on target. BPS field prefix: `var_*`. See Section 3.4. |
| **dataasof** | Data As Of | The Newrez data snapshot date (typically 1–2 days behind today). BPS adds `DATEDIFF(today, dataasof)` when displaying FCL days to compensate for this lag and reflect the true current-day count. |
| **SMS / Shellpoint** | Shellpoint Mortgage Servicing | Newrez's legacy operational sub-brand name. The `smsdaysinfc` field ("SMS-reported FCL days") uses this abbreviation; corresponds to servicer-reported perspective vs. investor-basis `daysinfc`. |
| **MFR** | Motion for Relief (from Automatic Stay) | Lender's formal motion to bankruptcy court requesting the Automatic Stay be lifted so FCL can resume. Affects BPS Bankruptcy panel fields `mfr_filed_date` and `mfr_status` (Section 6). |
| **POC** | Proof of Claim | A creditor's formal filing in bankruptcy court establishing the debt amount owed. Affects BPS Bankruptcy panel field `proof_of_claim_date` (Section 6). |
| **3rd Party Sale** | Third-Party Sale | Auction outcome where an external buyer wins the bid — property transfers to a third party (not the lender). Contrast with REO (no bidder; lender takes possession). Determined via Newrez `fcresults` field; affects `timeline_third_party_sold_date_date` logic (Section 3.1). |
| **Upcoming FC Sales** | Upcoming Foreclosure Sale (BPS stage: `SALE`) | Highest-priority BPS stage (priority 1). Trigger: Newrez `fcscheduledsaledate IS NOT NULL` — a foreclosure auction date has been officially scheduled. Once triggered, the loan enters this stage regardless of state type: Judicial states (scheduled after judgment) or Non-Judicial states (scheduled after service/publication). BPS output fields: `sale_start_date` (auction date), `to_sale_days` (days remaining to auction). DB storage code: `SALE` (see Section 7 stage code mapping table). |

---

## Section 1: Mapping Architecture Overview

This document focuses on the direct connections between Newrez raw data and BPS display fields; the intermediate Redshift processing layer is abstracted away (see doc 12):

```
Newrez Raw Data (MySQL newrez schema)
├── portnewrezfc   ← FCL master (timeline, stage, hold slots, bid amounts)
├── portnewrezbk   ← Bankruptcy data (60 columns)
└── portnewrezlm   ← Loss mitigation data (56 columns)
          │
          │  ╔═══════════════════════════════════════════╗
          │  ║  Intermediate Layer (omitted — see doc 12) ║
          │  ║  Redshift staging tables → BPS MySQL       ║
          │  ╚═══════════════════════════════════════════╝
          │
          ▼
BPS MySQL (bpms_dev schema) — 5 core tables
├── sync_loan_foreclosure (86 cols)          → Milestone, Summary, Bid Approval panels
├── sync_loan_foreclosure_hold (15 cols)     → Hold panel (full historical records)
├── sync_loan_foreclosure_loss_mitigation (22 cols) → Loss Mitigation Cycle panel
├── sync_loan_foreclosure_bankruptcy (22 cols)      → Bankruptcy panel
└── sync_fcl_stage_info (57 cols)            → Aggregate view Days in Stage/LM/Hold
          │
          ▼
biz_data_view_loan_details_foreclosure (104-column VIEW)
(covers sync_loan_foreclosure fields only; Hold/LM/BK panels queried separately)
```

**BPS display field groups** (corresponding to Section 3.x below):

| Group | Field Prefix | Count | Meaning | BPS Source Table |
|-------|-------------|-------|---------|-----------------|
| 1 | `timeline_*` | 19 | FCL milestone dates | sync_loan_foreclosure |
| 2 | `target_*` | 16 | Per-stage target days (config constants) | sync_loan_foreclosure |
| 3 | `actual_*` | 16 | Per-stage actual days (calculated) | sync_loan_foreclosure |
| 4 | `var_*` | 16 | Per-stage variance days (calculated) | sync_loan_foreclosure |
| 5 | `variance_*` | 4 | Bankruptcy/hold variance indicators | sync_loan_foreclosure |
| 6 | `bid_approval_*` | 4 | Bid approval information | sync_loan_foreclosure |
| 7 | `summary_*` | 16 | FCL summary status | sync_loan_foreclosure |
| — | Hold panel | 3 cols/row | Historical hold records | sync_loan_foreclosure_hold |
| — | LM Cycle panel | 10 cols/row | LM cycle history | sync_loan_foreclosure_loss_mitigation |
| — | Bankruptcy panel | 10 cols/row | Bankruptcy records | sync_loan_foreclosure_bankruptcy |
| — | Aggregate view | 4 cols/row | Stage day statistics | sync_fcl_stage_info |

### Source Data Filter Conditions — All 5 BPS FCL Tables

> **ETL code source**: `flow/basic_data/basic_data_config/basic_data_pool_config.py` (Newrez→Redshift extraction layer) + `flow/bps/bps_config/asset_managment_config.py` (Redshift→MySQL sync layer)

| BPS Table | Newrez Source Table | Extraction Filter | Sync Filter | Dedup Logic | Includes inactive loans (activefcflag=0)? |
|---|---|---|---|---|---|
| `sync_loan_foreclosure` | `portnewrezfc` | None (full load into Redshift) | `fcreferraldate IS NOT NULL` + JOIN portfunding | None | ✅ Yes (activefcflag=0: not in active foreclosure — completed OR withdrawn/reinstated/paid) |
| `sync_loan_foreclosure_hold` | `portnewrezfc` | `fchold1startdate IS NOT NULL` | Any slot: description/dates non-empty + JOIN portfunding | GROUP BY (loanid, description, start_date) | ✅ Yes |
| `sync_loan_foreclosure_loss_mitigation` | `portnewrezlm` | `dealstartdate IS NOT NULL` | None (full pass-through) + JOIN portfunding | ROW_NUMBER PARTITION BY (loanid, dealstartdate) | ✅ Yes |
| `sync_loan_foreclosure_bankruptcy` | `portnewrezbk` | `LENGTH(TRIM(bkstatus)) > 0` | None (full pass-through) + JOIN portfunding | ROW_NUMBER PARTITION BY (loanid, bkfileddate) | ✅ Yes |
| `sync_fcl_stage_info` | `basic_data_loan_fcl` (multi-servicer) | Primary: `activefcflag=1 AND fcremovaldate IS NULL`; Secondary: D90/D120P + demandsentdate non-null | None (full pass-through) + JOIN portfunding | Multi-layer CTE calculation | ❌ Active FCL only |

> **Key distinction**: `sync_fcl_stage_info` is the **only table that excludes inactive loans (activefcflag=0)** — the Aggregation Overview page reflects only loans currently in active foreclosure, making its population different from the other four tables (which include activefcflag=0 inactive/historical loans). Loan counts across these tables should not be directly compared. Note: `activefcflag=0` means **not currently in active foreclosure** (includes both completed and withdrawn/reinstated/paid), not necessarily "completed".  
> **All five tables** require `JOIN port.portfunding ON loanid` to confirm the loan is in the funding pool.

---

## Section 2: Newrez FCL Source Tables Reference

### 2.1 newrez.portnewrezfc (FCL Master Table)

> Scale: **13,321 active FCL loans** (activefcflag=1, dataasof 2026-05-24)  
> **Verification SQL**: Fill rates in this table are produced by Appendix B — SQL-1 (copy and run directly in MySQL)  
> **Value Examples**: See **2.1-B Value Range / Examples** below (field ranges and enum values from live MCP queries)

| Raw Field | Type | Business Meaning | Active FCL Fill Rate |
|-----------|------|-----------------|---------------------|
| `fcsetupdate` | date | FCL setup date (internal system open date) | 100% |
| `fcreferraldate` | date | Referral to attorney date | 100% |
| `demandsentdate` | date | Demand letter sent date (NOI issued) | 85.9% |
| `demandexpirationdate` | date | Demand expiration date (NOI end) | 85.7% |
| `firstlegaldate` | date | First legal action date | 57.6% |
| `servicecompletedate` | date | Legal service completion date | — |
| `titlereceiveddate` | date | Title report received date | — |
| `titlecleardate` | date | Title clearance date | — |
| `fcjudgmenthearingscheduled` | date | Judgment hearing scheduled date (Judicial states) | 11.9% |
| `fcjudgmententered` | date | Judgment entered date | — |
| `fcscheduledsaledate` | date | Scheduled/projected sale date | 18.2% |
| `fcsalehelddate` | date | Actual sale held date | 2.1% |
| `fcremovaldate` | date | FCL removal/completion date | — |
| `dtdeedrecorded` | date | Deed recorded date | — |
| `fcl3rdpartyproceedsreceiveddate` | date | Third-party sale proceeds received date | — |
| `fcstage` | varchar | Current FCL workflow stage (Newrez system text) | — |
| `currentmilestone` | varchar | Current BPS milestone label | 62.7% |
| `lastfcstepcompleted` | varchar | Most recent completed step description | — |
| `lastfcstepcompleteddate` | date | Most recent completed step date | — |
| `fcresults` | varchar | Final FCL disposition result (completed loans) | — |
| `fcremovaldesc` | varchar | FCL removal reason description | — |
| `activefcflag` | int | Whether in active foreclosure (1=in active FCL / 0=not in active FCL: completed or withdrawn/reinstated/paid) | 100% |
| `fccontestedflag` | int | Contested litigation flag (1=yes / 0=no) | 100% |
| `judicial` | int | Judicial foreclosure (1=judicial / 0=non-judicial) | 100% |
| `fcfirm` | varchar | Foreclosure attorney firm name | — |
| `fcbidamount` | decimal | Servicer-reported bid amount | 9.0% |
| `fcapprbidprice` | decimal | Approved bid price | 8.9% |
| `fcsaleamount` | decimal | Actual sale amount | — |
| `smsdaysinfc` | int | Servicer-reported days in FCL (as of dataasof) | 100% |
| `daysinfc` | int | Investor-basis days in FCL (as of dataasof) | 100% |
| `fchold1description` | varchar | Hold slot 1 current reason description | 89.6% |
| `fchold1startdate` | date | Hold 1 start date | — |
| `fchold1enddate` | date | Hold 1 end date (null = still active) | — |
| `fchold1projectedenddate` | date | Hold 1 projected end date | — |
| `fchold2description` | varchar | Hold slot 2 current reason description | 69.8% |
| `fchold2startdate` | date | Hold 2 start date | — |
| `fchold2enddate` | date | Hold 2 end date | — |
| `fchold2projectedenddate` | date | Hold 2 projected end date | — |
| `fchold3description` | varchar | Hold slot 3 current reason description | 52.6% |
| `fchold3startdate` | date | Hold 3 start date | — |
| `fchold3enddate` | date | Hold 3 end date | — |
| `fchold3projectedenddate` | date | Hold 3 projected end date | — |

> ⚠️ **Hold slot note**: The 3 hold slots in `portnewrezfc` (fchold1/2/3) reflect **Newrez's current snapshot** of active/recent holds. BPS appends each change as a new row in `sync_loan_foreclosure_hold` on each daily sync, accumulating full hold history (see Section 4).


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
| `currentmilestone` | varchar | `'Closed'` \| `'First Legal'` \| `'Judgment Entered'` \| `'Sale Held'` \| `'Sold'` \| `'Service Complete'` \| `'Sale Scheduled'` (62.7% fill) |
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
| `fchold1description` | varchar | `'Loss Mitigation Workout'` \| `'Awaiting Funds to Post'` \| `'Service Delay'` \| `'Court Delay'` \| `'Hearing Set'` \| `'Client Document Execution'` \| `'Original Note'` \| `'Delinquency Review'` \| `'Bankruptcy Filed'` \| `'Moratorium'` \| `'Awaiting Escrow Analysis'` \| `'Title Resolution'` (89.6% fill) |
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

### 2.2 newrez.portnewrezbk (Bankruptcy Table, 60 columns)

Key fields shown in the BPS Bankruptcy panel:

| Raw Field | Type | Business Meaning | Value Range / Examples |
|---|---|---|---|
| `activebkflag` | int | Currently in bankruptcy protection (1=yes / 0=no) | `1` (active BK) / `0` (terminated) |
| `bkchapter` | int | Bankruptcy chapter (7 / 11 / 13 etc.) | `7` (liquidation) / `11` (reorganization) / `13` (individual repayment plan) |
| `bkfileddate` | date | Bankruptcy filing date | `2008-06-16` to `2026-04-27` |
| `bkstatus` | int | Bankruptcy status (numeric code) | `1`–`5` (Newrez internal codes; **BPS decodes to text** Active/Discharged/Dismissed/Closed/ReliefGranted — see Section 6 / Q7) |
| `bkstage` | int | Bankruptcy legal stage (numeric code) | `0`–`22` (common: `8`/`21`/`1`/`4`). Note: BPS `legal_status` actually comes from `portnewrezgeneral.legalstatus` text, **not from this field** (see Section 6 / Q7) |
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
| `debtorintention` | int | Debtor intention (numeric code) | `1` (most common) / `2` / `0` |

### 2.3 newrez.portnewrezlm (Loss Mitigation Table, 56 columns)

Key fields shown in the BPS Loss Mitigation Cycle panel:

| Raw Field | Type | Business Meaning | Value Range / Examples |
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
| `daysinstatus` | int | Days in current status | `0` to `991` days |

> **Important**: Newrez `portnewrezlm` stores numeric codes (`lmdeal`, `lmprogram`, etc. are all int). The ETL **decodes these to business text** when writing to BPS's `sync_loan_foreclosure_loss_mitigation` (e.g., `lmdeal=7` → `"DIL"`, `lmprogram=10` → `"Deed-in-Lieu"`).

---

## Section 3: Complete BPS Display Field Mapping

> **"Newrez Field → BPS Field" column**: This column records the specific ETL rule used to transform each Newrez raw field value into the corresponding BPS stored value. Common rule values:
> - `Direct`: ETL copies the Newrez field value into BPS unchanged
> - `COALESCE(A, B)`: Uses the first non-null value of A or B
> - `When fcresults='xxx' use...`: Conditional assignment based on another field's value
> - `if …, then = …; otherwise …`: full conditional assignment (arrow shorthand avoided). ⚠️ Note the output may be a **fixed literal constant** (e.g. `'Active Foreclosure'`), not the value of the condition field — e.g. `summary_foreclosure_status` uses `activefcflag` as a test but stores a constant, not `activefcflag`'s value; `fcstage` is not written to this field either (it goes to `summary_current_step`).
> - **Condition field note**: All field names appearing in rule expressions (e.g. `activefcflag`, `judicial`, `currentmilestone`) belong to the Newrez source table specified in that section's header (typically `newrez.portnewrezfc`). The ETL evaluates these conditions entirely on the Newrez side — **no BPS fields are referenced in mapping rule expressions**.

### 3.1 FCL Timeline Dates (timeline_*)

> **Entry filter**: `bpms_dev.sync_loan_foreclosure.timeline_referred_to_foreclosure_date IS NOT NULL` (source field: `newrez.portnewrezfc.fcreferraldate` — only loans with an FCL referral date are included)  
> **ETL code source**: The filter is applied in `asset_managment_config.py` `GEN_FORECLOSURE` SQL (`WHERE a.timeline_referred_to_foreclosure_date IS NOT NULL`), combined with `JOIN port.portfunding ON loanid` (loan must exist in the funding pool). `newrez.portnewrezfc` is loaded in full into Redshift staging table `port.basic_data_loan_fcl` with no upstream WHERE; filtering happens at the Redshift→MySQL sync layer.  
> **BPS database path**: All fields below reside in `bpms_dev.sync_loan_foreclosure`; full path is `bpms_dev.sync_loan_foreclosure.{BPS Display Field}`  
> **Newrez source table**: All fields in the "Newrez Field" column below come from `newrez.portnewrezfc` (prefix omitted; full path format: `newrez.portnewrezfc.{field_name}`)  
> **Verification SQL**: "Fill Rate" column values come from Appendix B — SQL-1; `fcresults` distribution (the "266 loans 3rd Party" note) comes from SQL-2

**Figure 13-4 — Loan Foreclosure Detail Page: Foreclosure Milestone Timeline Panel**

![BPS Loan Foreclosure Milestone Timeline Panel](../zh/image/bps-loan-foreclosure-milestone-timeline-panel.png)

| BPS UI Label | Business Meaning | BPS Display Field | Newrez Field | Newrez Field → BPS Field | Fill Rate |
|---|---|---|---|---|---|
| Milestone > Notice of Intent Date | NOI / Demand letter sent date. ~14.1% of active FCL loans are null (Newrez has no NOI event recorded) | `timeline_notice_of_intent_date` | `demandsentdate` | Direct | 85.9% |
| Milestone > Notice of Intent End Date | NOI expiration date, typically sent date +30 days | `timeline_notice_of_intent_end_date` | `demandexpirationdate` | Direct | 85.7% |
| Milestone > Approved for Referral Date | Internal FCL approval / open date (BPS onboarding date); typically same day as attorney referral ⚠️ | `timeline_approved_for_referral_date` | `fcsetupdate` | Direct | 100% |
| Milestone > Referred to Attorney Date | Attorney referral date; `fcreferraldate` and `fcsetupdate` are typically the same date for Newrez ⚠️ | `timeline_referred_to_attorney_date` | `fcreferraldate` | Direct | 100% |
| Milestone > Referred to Foreclosure Date | **BPS entry filter field**: loan only included if non-null. Same raw Newrez field as attorney referral ⚠️ | `timeline_referred_to_foreclosure_date` | `fcreferraldate` | Direct | 100% |
| Milestone > Title Report Received Date | Date title report was received ⚠️ Newrez does not populate this field (null for all active FCL loans) | `timeline_title_report_received_date` | `titlereceiveddate` | Direct | 0.0% |
| Milestone > Preliminary Title Cleared Date | Preliminary title clearance completed ⚠️ Newrez does not populate this field; same raw field as final title clearance | `timeline_preliminary_title_cleared_date` | `titlecleardate` | Direct (preliminary clearance) | 0.0% |
| Milestone > First Legal Date | First legal action date (filing). May be null in non-judicial states (no court filing required) | `timeline_first_legal_date` | `firstlegaldate` | Direct | 57.6% |
| Milestone > Service Date | Legal service completion date | `timeline_service_date` | `servicecompletedate` | Direct | 28.9% |
| Milestone > Publication Date | ⚠️ Newrez does not report foreclosure publication date; field is typically null in BPS, related actual/var also null | `timeline_publication_date` | *(no corresponding Newrez field)* | Newrez does not report this; always null in BPS | 0% |
| Milestone > Judgement Hearing Set Date | Judgment hearing scheduled date. Judicial states only; null for non-judicial | `timeline_judgement_hearing_set_date` | `fcjudgmenthearingscheduled` | Direct | 11.9% |
| Milestone > Judgement Date | Judgment entered date. Judicial states only | `timeline_judgement_date` | `fcjudgmententered` | Direct | 7.9% |
| Milestone > Projected Sale Date | Latest projected / scheduled sale date (updates dynamically) | `timeline_sale_date_projected_date` | `fcscheduledsaledate` | Direct | 18.2% |
| Milestone > Sale Date Set | Confirmed scheduled sale date. Same raw field as Projected; BPS distinguishes via internal state logic ⚠️ | `timeline_sale_date_set_date` | `fcscheduledsaledate` | Direct | 18.2% |
| Milestone > Final Title Cleared Date | Final title clearance completed ⚠️ Newrez does not populate this field; same raw field as preliminary clearance | `timeline_final_title_cleared_date` | `titlecleardate` | Direct (final clearance) | 0.0% |
| Milestone > Sale Date Held | Actual sale held date. Most active FCL loans have not yet reached this milestone | `timeline_sale_date_held_date` | `fcsalehelddate` | Direct | 2.1% |
| Milestone > Foreclosure Completed Date | Final FCL completion marker. Deed recorded date takes priority; falls back to FCL removal / completion date (verified: `dtdeedrecorded`=0%, `fcremovaldate`=2.0%, COALESCE result=2.0%) | `timeline_foreclosure_completed_date` | `dtdeedrecorded` / `fcremovaldate` | `COALESCE(dtdeedrecorded, fcremovaldate)` | 2.0% |
| Milestone > FCL 3rd Party Sold Date | Third-party buyer closing date (266 active FCL loans have `fcresults='3rd Party'`). Must be combined with `fcresults` to confirm third-party purchase ⚠️ | `timeline_third_party_sold_date_date` | `fcsalehelddate` | Use `fcsalehelddate` when `fcresults='3rd Party'` | 2.0% |
| Milestone > FCL 3rd Party Proceeds Received Date | Date third-party sale proceeds were received (no active FCL loans have reached this stage) | `timeline_third_party_proceeds_received_date` | `fcl3rdpartyproceedsreceiveddate` | Direct | 0.0% |

> ⚠️ **Newrez-specific behavior**:
> - `fcsetupdate` and `fcreferraldate` are typically the same date (confirmed in live data), so `timeline_approved_for_referral_date` and `timeline_referred_to_attorney_date` will usually show identical values.
> - `timeline_sale_date_projected_date` and `timeline_sale_date_set_date` both derive from `fcscheduledsaledate`; the distinction is managed internally by BPS state logic.
> - `timeline_preliminary_title_cleared_date` and `timeline_final_title_cleared_date` both derive from `titlecleardate`; BPS records each at different pipeline stages.

---

### 3.2 Per-Stage Target Days (target_*)

> **Source: System configuration constants — not from Newrez data**  
> **BPS database path**: All fields below reside in `bpms_dev.sync_loan_foreclosure`; full path is `bpms_dev.sync_loan_foreclosure.{BPS Display Field}`  
> **Verification SQL**: Use Appendix B — SQL-8 to query stored target_* values for sample loans (outputs all three groups together for easy comparison)

These fields are pre-configured compliance targets set by state / judicial type / servicer. Newrez raw data is not used.

| BPS UI Label | Business Meaning | BPS Display Field | Source | Default Value |
|---|---|---|---|---|
| Target Days > Notice of Intent | Standard days from NOI issued to NOI expiration | `target_notice_of_intent_days` | System config | 30 days |
| Target Days > Notice of Intent Expiration | Standard days from NOI expiration to approval for referral | `target_notice_of_intent_expired_days` | System config | 90 days |
| Target Days > Approved for Referral | Standard days from approval to formal attorney referral | `target_approved_for_referral_days` | System config | 30 days |
| Target Days > Referred to Attorney | Standard days from attorney referral to FCL referral | `target_referred_to_attorney_days` | System config | 1 day |
| Target Days > Referred to Foreclosure | Standard days from FCL referral to first legal action | `target_referred_to_foreclosure_days` | System config | 1 day |
| Target Days > Title Report Received | Standard days from referral to title report received | `target_title_report_received_days` | System config | 30 days |
| Target Days > Preliminary Title Cleared | Standard days from title received to preliminary clearance | `target_preliminary_title_cleared_days` | System config | 30 days |
| Target Days > First Legal | Standard days from first legal action to service completion | `target_first_legal_days` | System config | 120 days |
| Target Days > Service | Standard days from service to judgment hearing | `target_service_days` | System config | 90 days |
| Target Days > Publication | Standard days for publication stage | `target_publication_days` | System config | 30 days |
| Target Days > Judgement Hearing Set | Standard days from judgment hearing to judgment entered (judicial) | `target_judgement_hearing_set_days` | System config | 120 days |
| Target Days > Judgement | Standard days from judgment to sale date set | `target_judgement_days` | System config | 30 days |
| Target Days > Sale Date Set | Standard days from sale set to sale held | `target_sale_date_set_days` | System config | 30 days |
| Target Days > Final Title Cleared | Standard days for final title clearance | `target_final_title_cleared_days` | System config | 5 days |
| Target Days > Sale Date Held | Standard days from sale held to FCL completion | `target_sale_date_held_days` | System config | 0 days |
| Target Days > Total | Total FCL target days (sum of all stage targets) | `target_total` | Calculated | = sum of above |

---

### 3.3 Per-Stage Actual Days (actual_*)

> **Source: Calculated from timeline_* dates — not direct Newrez fields**  
> **BPS database path**: All fields below reside in `bpms_dev.sync_loan_foreclosure`; full path is `bpms_dev.sync_loan_foreclosure.{BPS Display Field}`  
> **Endpoint field note**: Newrez endpoint field names in the "Calculation" column are from `newrez.portnewrezfc` (prefix omitted)  
> **Verification SQL**: Use Appendix B — SQL-8 to query stored actual_* results for sample loans (ETL has already computed and stored these; raw endpoint dates can be checked via SQL-4)

Formula: `actual_{stage}_days = DATEDIFF(stage_end_timeline_date, stage_start_timeline_date)` (null when either endpoint is null)

| BPS UI Label | Business Meaning | BPS Display Field | Calculation (field endpoints from portnewrezfc) |
|---|---|---|---|
| Actual Days > Notice of Intent | NOI validity period (issued to expiration) | `actual_notice_of_intent_days` | `demandexpirationdate` − `demandsentdate` |
| Actual Days > Notice of Intent Expiration | Waiting days from NOI expiration to approval for referral | `actual_notice_of_intent_expire_days` | `fcsetupdate` − `demandexpirationdate` |
| Actual Days > Approved for Referral | Days from FCL open to attorney referral (Newrez typically same date, result = 0) ⚠️ | `actual_approved_for_referral_days` | `fcreferraldate` − `fcsetupdate` |
| Actual Days > Referred to Attorney | Same field subtracted from itself; always 0 ⚠️ | `actual_referred_to_attorney_days` | `fcreferraldate` − `fcreferraldate` |
| Actual Days > Referred to Foreclosure | Days from referral to first legal action (filing) | `actual_referred_to_foreclosure_days` | `firstlegaldate` − `fcreferraldate` |
| Actual Days > Title Report Received | Days from referral to title report received | `actual_title_report_received_days` | `titlereceiveddate` − `fcreferraldate` |
| Actual Days > Preliminary Title Cleared | Days from title report received to preliminary clearance | `actual_preliminary_title_cleared_days` | `titlecleardate` − `titlereceiveddate` |
| Actual Days > First Legal | Days from first legal action to legal service completion | `actual_first_legal_days` | `servicecompletedate` − `firstlegaldate` |
| Actual Days > Service | Days from service completion to judgment hearing scheduled | `actual_service_days` | `fcjudgmenthearingscheduled` − `servicecompletedate` |
| Actual Days > Publication | Publication stage actual days (null for all Newrez loans) ⚠️ | `actual_publication_days` | Depends on `timeline_publication_date` (no Newrez source → always null) |
| Actual Days > Judgement Hearing Set | Days from judgment hearing to judgment entered (judicial states only) | `actual_judgement_hearing_set_days` | `fcjudgmententered` − `fcjudgmenthearingscheduled` |
| Actual Days > Judgement | Days from judgment entered to sale date set | `actual_judgement_days` | `fcscheduledsaledate` − `fcjudgmententered` |
| Actual Days > Sale Date Set | Days from sale date set to sale held | `actual_sale_date_set_days` | `fcsalehelddate` − `fcscheduledsaledate` |
| Actual Days > Final Title Cleared | Days from sale held to final title clearance completed | `actual_final_title_cleared_days` | `fcsalehelddate` − `titlecleardate` |
| Actual Days > Sale Date Held | Days from sale held to FCL completion | `actual_sale_date_held_days` | `fcremovaldate` − `fcsalehelddate` |
| Actual Days > Total | Total actual FCL days across all stages | `actual_total` | = sum of all actual_*_days |

---

### 3.4 Per-Stage Variance Days (var_*)

> **Pure calculation — no raw data source**  
> **BPS database path**: All fields below reside in `bpms_dev.sync_loan_foreclosure`; full path is `bpms_dev.sync_loan_foreclosure.{BPS Display Field}`  
> **Formula operand sources**: The `actual_*_days` fields (from Section 3.3) and `target_*_days` fields (from Section 3.2) referenced in the formulas both reside in the same table `bpms_dev.sync_loan_foreclosure`. All three field groups (target / actual / var) live in the same table; the calculation is entirely internal to BPS with **no Newrez raw data involved**.  
> **Verification SQL**: Appendix B — SQL-8 outputs all three field groups (target_*/actual_*/var_*) together, making it easy to compare and verify the calculation relationship

Formula: `var_{stage}_days = actual_{stage}_days − target_{stage}_days` (positive = behind target / negative = ahead of schedule / zero = exactly on target)

| BPS UI Label | Business Meaning | BPS Display Field | Calculation |
|---|---|---|---|
| Var Days > Notice of Intent | Variance days for NOI stage (actual vs. target) | `var_notice_of_intent_days` | `actual_notice_of_intent_days` − `target_notice_of_intent_days` |
| Var Days > Notice of Intent Expiration | Variance days for NOI expiration waiting stage | `var_notice_of_intent_expire_days` | `actual_notice_of_intent_expire_days` − `target_notice_of_intent_expired_days` |
| Var Days > Approved for Referral | Variance for approval-to-referral stage (actual typically 0, result typically 0 − 30 = −30) ⚠️ | `var_approved_for_referral_days` | `actual_approved_for_referral_days` − `target_approved_for_referral_days` |
| Var Days > Referred to Attorney | Variance for attorney referral stage (actual typically 0, result typically 0 − 1 = −1) ⚠️ | `var_referred_to_attorney_days` | `actual_referred_to_attorney_days` − `target_referred_to_attorney_days` |
| Var Days > Referred to Foreclosure | Variance from FCL referral to first legal action | `var_referred_to_foreclosure_days` | `actual_referred_to_foreclosure_days` − `target_referred_to_foreclosure_days` |
| Var Days > Title Report Received | Variance for title report received stage | `var_title_report_received_days` | `actual_title_report_received_days` − `target_title_report_received_days` |
| Var Days > Preliminary Title Cleared | Variance for preliminary title clearance stage | `var_preliminary_title_cleared_days` | `actual_preliminary_title_cleared_days` − `target_preliminary_title_cleared_days` |
| Var Days > First Legal | Variance for first legal action stage | `var_first_legal_days` | `actual_first_legal_days` − `target_first_legal_days` |
| Var Days > Service | Variance for service stage | `var_service_days` | `actual_service_days` − `target_service_days` |
| Var Days > Publication | Variance for publication stage (typically null since publication_date is null for Newrez) ⚠️ | `var_publication_days` | `actual_publication_days` − `target_publication_days` |
| Var Days > Judgement Hearing Set | Variance for judgment hearing stage (judicial states only) | `var_judgement_hearing_set_days` | `actual_judgement_hearing_set_days` − `target_judgement_hearing_set_days` |
| Var Days > Judgement | Variance from judgment to sale date set | `var_judgement_days` | `actual_judgement_days` − `target_judgement_days` |
| Var Days > Sale Date Set | Variance for sale date set stage | `var_sale_date_set_days` | `actual_sale_date_set_days` − `target_sale_date_set_days` |
| Var Days > Final Title Cleared | Variance for final title clearance stage | `var_final_title_cleared_days` | `actual_final_title_cleared_days` − `target_final_title_cleared_days` |
| Var Days > Sale Date Held | Variance from sale held to FCL completion | `var_sale_date_held_days` | `actual_sale_date_held_days` − `target_sale_date_held_days` |
| Var Days > Total | Total FCL variance days (positive = behind target overall) | `var_total` | `actual_total` − `target_total` |

---

### 3.5 Variance Indicators (variance_*)

> **BPS database path**: All fields below reside in `bpms_dev.sync_loan_foreclosure`; full path is `bpms_dev.sync_loan_foreclosure.{BPS Display Field}`  
> **Newrez source tables (mixed)**: Rows 1–3 come from `newrez.portnewrezbk`; Row 4 (Estimated Hold Days) comes from `newrez.portnewrezfc`. Table name prefix is retained in the field column to disambiguate sources.  
> **Verification SQL**: The `variance_estimated_hold_days` input fields (`fchold*projectedenddate`) can be queried via Appendix B — SQL-4 (from `newrez.portnewrezfc`); `portnewrezbk` fields are not currently covered in Appendix B

| BPS UI Label | Business Meaning | BPS Display Field | Newrez Field | Newrez Field → BPS Field |
|---|---|---|---|---|
| Variance > Active Bankruptcy | Flags whether the loan is currently under active bankruptcy protection | `variance_active_bankruptcy` | `portnewrezbk.activebkflag` | Direct (1 = currently in bankruptcy protection / 0 = no) |
| Variance > Completed Bankruptcy | Flags whether the loan has historically completed a bankruptcy proceeding | `variance_completed_bankruptcy` | `portnewrezbk.activebkflag`, `portnewrezbk.bkremovaldate` | `activebkflag = 0 AND bkremovaldate IS NOT NULL` → 1 (completed BK); else 0 |
| Variance > Bankruptcies | Total number of historical bankruptcy filings for this loan (all chapters) | `variance_bankruptcies` | `portnewrezbk.loanid` (row count) | `COUNT(*)` grouped by loanid |
| Variance > Estimated Hold Days | Estimated remaining hold days (based on Newrez projected end dates, not the hold history table) ⚠️ | `variance_estimated_hold_days` | `portnewrezfc.fchold1projectedenddate`, `portnewrezfc.fchold2projectedenddate`, `portnewrezfc.fchold3projectedenddate` | `MAX(non-null projected end dates) − current_date (New York time)` |

> **Note**: `variance_estimated_hold_days` is sourced from `newrez.portnewrezfc` projected end date fields — **not** from `sync_loan_foreclosure_hold` (which does not store projected end dates).

---

### 3.6 Bid Approval Fields (bid_approval_*)

> **BPS database path**: All fields below reside in `bpms_dev.sync_loan_foreclosure`; full path is `bpms_dev.sync_loan_foreclosure.{BPS Display Field}`  
> **Newrez source table**: All fields in the "Newrez Field" column below come from `newrez.portnewrezfc` (prefix omitted)  
> **Verification SQL**: `fcbidamount` fill rate comes from Appendix B — SQL-1; sample loan field values can be queried via SQL-4
> ⚠️ **Note**: the Newrez raw field `fcapprbidprice` (approved bid price) exists but is **NOT mapped to any Bid Approval display column** — the only populated column here, `bid_approval_bid_amount`, uses `fcbidamount` (see correction in the table below).

| BPS UI Label | Business Meaning | BPS Display Field | Newrez Field | Newrez Field → BPS Field |
|---|---|---|---|---|
| Bid Approval > Approval Status | Bid approval status (BPS-internal column; the FCL ETL never writes it) | `bid_approval_status` | *(no upstream)* | **No Newrez source** — column exists in the `basic_data_loan_foreclosure` DDL (`basic_data_pool_config.py:193`) but is **NOT in the INSERT column list**; intended to be set by a BPS-side bid-approval workflow. **DB-verified 2026-06-07: 0% filled** (0/6152 RS · 0/89 BPS) |
| Bid Approval > Sale Date | Scheduled auction date for the bid | `bid_approval_sale_date` | *(no upstream)* | ⚠️ **Corrected**: previously listed `fcscheduledsaledate` — that source feeds `timeline_sale_date_projected_date`, **not this column**. Not in the INSERT list; **DB-verified 0% filled** (0/6152 · 0/89) |
| Bid Approval > Bid Amount | Bid amount (the ONLY bid_approval_* column the ETL populates) | `bid_approval_bid_amount` | `fcbidamount` | ⚠️ **Corrected**: source is `fcbidamount` (`basic_data_pool_config.py:272`), **NOT `fcapprbidprice`**; same value as `summary_foreclosure_bid_amount`. DB-verified 16 rows filled (16/6152 · 16/89) |
| Bid Approval > Loan Resolution Holds | Holds blocking loan resolution (note: real column name misspelled "holods") ⚠️ | `bid_approval_loan_resolution_holods` | *(no upstream)* | ⚠️ **Corrected**: previously listed concatenated `fchold*description` — that data lives in the separate long table `sync_loan_foreclosure_hold`, not this column. Not in the INSERT list; **DB-verified 0% filled** (0/6152 · 0/89) |

---

### 3.7 FCL Summary Fields (summary_*)

> **BPS database path**: All fields below reside in `bpms_dev.sync_loan_foreclosure`; full path is `bpms_dev.sync_loan_foreclosure.{BPS Display Field}`  
> **Newrez source table**: All fields in the "Newrez Field" column below come from `newrez.portnewrezfc` (prefix omitted)  
> **Verification SQL**: Field fill rates come from Appendix B — SQL-1; sample loan field values (including `smsdaysinfc`/`dataasof`) come from SQL-4

**Figure 13-5 — Loan Foreclosure Detail Page: Foreclosure Summary Panel**

![BPS Loan Foreclosure Summary Panel](../zh/image/bps-loan-foreclosure-summary-panel.png)

| BPS UI Label | Business Meaning | BPS Display Field | Newrez Field | Newrez Field → BPS Field |
|---|---|---|---|---|
| Summary > Foreclosure Status | FCL status text: fixed text `Active Foreclosure` when active; `Closed Foreclosure:` + removal reason when inactive with a reason (`fcremovaldesc` 2.0%); otherwise empty | `summary_foreclosure_status` | `activefcflag`, `fcremovaldesc` | if `activefcflag=1`, then `summary_foreclosure_status` = fixed text `'Active Foreclosure'`; if `activefcflag=0` and `fcremovaldesc` is non-empty, then = `'Closed Foreclosure:'` + `fcremovaldesc`; otherwise = `NULL`.<br>(Note: `fcstage` is **not** used by this field — it populates `summary_current_step`; `fcresults` is not used either. Code `basic_data_pool_config.py:273` GEN_FCL_DETAIL) |
| Summary > Foreclosure Bid Amount | Servicer-reported bid amount (~9% fill rate in active FCL) | `summary_foreclosure_bid_amount` | `fcbidamount` | Direct |
| Summary > Foreclosure Sale Amount | Actual auction sale amount (active FCL fill rate: 4.7% — anomalously higher than sale-held rate of 2.1%; indicates data lag issue) ⚠️ | `summary_foreclosure_sale_amount` | `fcsaleamount` | Direct |
| Summary > Contested Litigation | Whether contested litigation exists (1=yes / 0=no) | `summary_contested_litigation` | `fccontestedflag` | Direct |
| Summary > Firm | Foreclosure law firm name (same source as Foreclosure Attorney, displayed twice in BPS UI) | `summary_firm` | `fcfirm` | Same as `summary_foreclosure_attorney` (both fields display the same source, slightly different UI placement) |
| Summary > Type | Foreclosure type as readable text (converts boolean judicial flag to label) | `summary_type` | `judicial` | if `judicial=1`, then `summary_type` = `'Judicial'`; if `judicial=0`, then = `'Non Judicial'`; if `judicial` is `NULL`/empty, then = `NULL` |
| Summary > SMS Days in FCL | Servicer (Newrez/SMS=Shellpoint) FCL days in-flight — counted from the servicer **setup date fcsetupdate**; adjusted to eliminate Newrez data cutoff lag | `summary_sms_days_in_fcl` | `smsdaysinfc`(svc_days_infc), `dataasof` | **Real-time recalculation**: `smsdaysinfc + DATEDIFF(today_NY, dataasof)`; basis = fcsetupdate, ≤ Days in FCL (see footnote) |
| Summary > Days in FCL | Investor/full-timeline FCL days in-flight — counted from the **referral date fcreferraldate**; adjusted to reflect actual days as of today | `summary_days_in_fcl` | `daysinfc`, `dataasof` | **Real-time recalculation**: `daysinfc + DATEDIFF(today_NY, dataasof)`; basis = fcreferraldate, ≥ SMS Days in FCL |
| Summary > Current Step | Current FCL processing step (BPS milestone label preferred; falls back to Newrez stage description) | `summary_current_step` | `currentmilestone` / `fcstage` | if `currentmilestone` is non-null, then `summary_current_step` = `currentmilestone`; otherwise = `fcstage` (this is where the Newrez stage text goes). ⚠️ **doc 19 measurement (2026-06-04): BPS actually uses `fcstage` even when currentmilestone is non-empty — value-order pending ETL-code verification, see §8 Q13** |
| Summary > Last Step Completed | Text description of the most recently completed FCL processing step (99.5% fill rate) | `summary_last_step_completed` | `lastfcstepcompleted` | Direct |
| Summary > Last Step Completed Date | Date the most recently completed step was finished (99.5% fill rate) | `summary_last_step_completed_date` | `lastfcstepcompleteddate` | Direct |
| Summary > Servicer Number | Newrez/Shellpoint internal loan number (distinct from investor loanid; 100% fill rate) | `summary_servicer_number` | `shellpointloanid` | Direct |
| Summary > Completed Foreclosure | Boolean flag for whether FCL is no longer active (⚠️ named "Completed" but really an "inactive" flag) | `summary_completed_foreclosure` | `activefcflag` | if `activefcflag=0`, then `summary_completed_foreclosure` = 1; if `activefcflag=1`, then = 0 (i.e. the inverse of `activefcflag`). ⚠️ `activefcflag=0` = **not in active foreclosure** (DB: Reinstated 26 / Loss Mitigation 16 / Paid in Full 11 / truly-completed REO \| 3rd \| DiL 10), **not all completed** |
| Summary > Servicer FC Bid Amount | Servicer-perspective FCL bid amount | `summary_srv_fc_bid_amount` | `fcbidamount` | Same as `summary_foreclosure_bid_amount` (both take `fcbidamount`). Note: the Newrez raw field `fcapprbidprice` (approved bid) exists but is **not mapped to any display column** |
| Summary > Judicial Foreclosure | Raw boolean for judicial type (1=Judicial / 0=Non-Judicial); the Type field above is its readable text version | `summary_judicial_foreclosure` | `judicial` | Direct |
| Summary > Foreclosure Attorney | Foreclosure law firm full name (same source as the Firm field above) | `summary_foreclosure_attorney` | `fcfirm` | Direct |

> ⚠️ **Real-time days recalculation — live example**:
> Sample loan (loanid=7727000672): `smsdaysinfc = 77`, `dataasof = 2026-05-24`, today = 2026-05-26.
> BPS displayed value = 77 + 2 = **79 days** — reflects actual days in FCL as of today, not as of Newrez data cutoff.
>
> **The core difference = different start date (code + DB verified, 2026-06-03)**:
> - `summary_days_in_fcl` ← `daysinfc`: ETL recomputes from the **referral date `fcreferraldate`** as `datediff(referral_start_date, snapshot)+1` (only when Active; `basic_data_pool_config.py:1628`) — **investor / full-timeline** basis.
> - `summary_sms_days_in_fcl` ← Newrez native `smsdaysinfc` (ETL alias `svc_days_infc` = servicer days in FC, passed through; `:280/:1545`), empirically counted from the **servicer FCL setup date `fcsetupdate`** — **current servicer (SMS = Shellpoint)** basis.
> - Since `fcsetupdate ≥ fcreferraldate`, **`servicer_days_in_fcl ≤ days_in_fcl`** (doc 14 standard field name; the BPS column is `summary_sms_days_in_fcl`); in the latest snapshot only 2 of 91 differ (e.g. 7727004408: days=816 / sms=586, a 230-day referral→setup gap). When referral=setup they are equal.
> - Both get the BPS real-time adjustment `+ DATEDIFF(today_NY, dataasof)` (`asset_managment_config.py:597-598`).

---

## Section 4: Hold Panel — Full Historical Record Model

> **Verification SQL**: Full Hold history for any loan: Appendix B — SQL-5 (queries `bpms_dev.sync_loan_foreclosure_hold`; replace loanid as needed)
> **Data Range**: The Hold panel is a **single-loan view** showing the complete Hold history for the selected loan across its entire FCL lifecycle (not a current-snapshot view). Data comes from `bpms_dev.sync_loan_foreclosure_hold`, where every Hold change is appended as a new row (non-destructive history). All Hold records for the loan are displayed (if no records exist, the panel shows "No Rows To Show").
>
> **Source Data Filter Conditions (ETL code verified)**:
> - **Layer 1 (Newrez→Redshift extraction, `basic_data_pool_config.py`)**: `WHERE fchold1startdate IS NOT NULL` — only loans where Hold slot 1 has a start date enter the Redshift staging table `port.basic_data_loan_foreclosure_hold`.
> - **Layer 2 (Redshift→MySQL sync, `asset_managment_config.py` `GEN_FORECLOSURE_HOLD`)**: All 3 Hold slots are unpivoted into separate rows; each slot's condition: `(description IS NOT NULL AND description != '') OR start_date IS NOT NULL OR end_date IS NOT NULL` (any one of the three suffices). Final `JOIN port.portfunding ON loanid` (loan must be in the funding pool). `GROUP BY loanid, svcloanid, description, description_start_date` deduplicates multiple daily snapshots of the same Hold event.
> - **Independent from the main FCL table**: The Hold table's extraction chain is fully independent — `fcreferraldate IS NOT NULL` is **not** required. A loan can appear in the Hold table even if it is absent from `sync_loan_foreclosure`.
> - **Write strategy**: DELETE (full clear by tenant_id) + INSERT (full reload).

**Figure 13-6 — Loan Foreclosure Detail Page: Hold Panel**

![BPS Loan Foreclosure Hold Panel](../zh/image/bps-loan-foreclosure-hold-panel.png)

### BPS Table Structure

**BPS storage table**: `bpms_dev.sync_loan_foreclosure_hold` (15 columns)

| BPS Field | Type | Meaning |
|---|---|---|
| `loanid` | bigint | Loan ID |
| `svcloanid` | varchar | Servicer internal loan number |
| `fctrdt` | date | Source data batch date |
| `description` | varchar(256) | Hold reason description (text) |
| `description_start_date` | date | Hold start date |
| `description_end_date` | date | Hold end date (NULL = still active) |

### Newrez Raw Fields → BPS Hold Table Mapping

| UI Column | BPS Field | Newrez Raw Field | Source Table |
|---|---|---|---|
| Description | `description` | `fchold1/2/3description` | portnewrezfc |
| Start Date | `description_start_date` | `fchold1/2/3startdate` | portnewrezfc |
| End Date | `description_end_date` | `fchold1/2/3enddate` | portnewrezfc |

### Key Architectural Note

The 3 hold slots in Newrez `portnewrezfc` (fchold1/2/3) represent a **current snapshot** of active/recent holds. On each daily BPS sync:
- If any hold's description, start, or end date has changed, a new row is appended
- If a hold has closed (enddate newly populated), a new row is appended

This means `sync_loan_foreclosure_hold` accumulates the **complete hold history** for each loan — far more rows than the 3 current slots.

**Live verification** (MCP query, loanid=7727000088):
This loan has 7 hold records in BPS spanning 2025-05-28 to present, while Newrez currently shows only 1 active hold slot:

| Description | Start Date | End Date |
|---|---|---|
| Original Note | 2025-05-28 | 2025-06-11 |
| Service Delay | 2025-07-15 | 2025-07-31 |
| Loss Mitigation Workout | 2025-07-31 | 2025-08-01 |
| Loss Mitigation Workout | 2025-08-13 | 2025-10-21 |
| Court Delay | 2025-10-21 | 2025-12-16 |
| Loss Mitigation Workout | 2026-02-20 | 2026-02-24 |
| Court Delay | 2026-01-16 | NULL (ongoing) |

### variance_estimated_hold_days — Special Note

This field is stored in `sync_loan_foreclosure` (main table) and calculated as:
```
MAX(fchold1projectedenddate, fchold2projectedenddate, fchold3projectedenddate) − current_date(New York time)
```
**Source: `portnewrezfc` projected end date fields** — NOT from `sync_loan_foreclosure_hold` (which does not store projected end dates).

---

## Section 5: Loss Mitigation Cycle Panel

> **Verification SQL**: Full LM Cycle history for any loan: Appendix B — SQL-6 (queries `bpms_dev.sync_loan_foreclosure_loss_mitigation`; replace loanid as needed)
> **Data Range**: The LM panel is a **single-loan view** showing the complete Loss Mitigation cycle history for the selected loan (one row per LM cycle). Data comes from `bpms_dev.sync_loan_foreclosure_loss_mitigation`, with each cycle uniquely identified by `deal` + `cycle_opened_date`. All LM cycles for the loan are displayed, including historically closed ones.
>
> **Source Data Filter Conditions (ETL code verified)**:
> - **Extraction layer (Newrez→Redshift, `basic_data_pool_config.py`)**: `newrez.portnewrezlm` filter: `WHERE dealstartdate IS NOT NULL` (LM cycle must have a start date). Deduplication: `ROW_NUMBER() OVER (PARTITION BY loanid, dealstartdate ORDER BY dataasof DESC) = 1` (one row per LM cycle, latest snapshot retained).
> - **Numeric decode**: 6 integer-coded fields (`lmdeal`, `lmprogram`, `lmstatus`, `lmdecision`, `denialreason`, `borrowerintention`) are decoded to business text via `LEFT JOIN newrez.portnewrezdatadic` in the Redshift extraction layer before writing to BPS (unlike the Hold panel which stores Newrez text descriptions directly).
>   - **Mapping data lives in a DB dictionary table; decode logic lives in code** (not hardcoded): dict table `newrez.portnewrezdatadic` (long format `field_name | code | description`, **Redshift-only** — not in dev MySQL); decode JOINs at `basic_data_pool_config.py:835-840` (`:835 LMDeal→deal`, `:836 LMProgram→program`, `:837 LMStatus→lmc_status`, `:838 LMDecision→final_disposition`, `:839 BorrowerIntention`, `:840 DenialReason`; BK at `:367 BKStatus`). `concat(code,'.0')` aligns with `lmdeal`'s decimal-string storage (e.g. `'7.0'`).
>   - **LMDeal dict defines 13 codes**: `1 Modification | 2 Evaluation | 3 Reinstatement | 4 Payment Plan | 5 Forbearance | 6 Short Sale | 7 DIL | 8 Loan Sale | 9 Payoff | 10 Settlement | 11 Deferment | 12 CFK | 13 Consent Judgement`; **only 8 observed in current data** (1/2/4/5/6/7/9/11). A cross-table join of "newrez latest-snapshot lmdeal × BPS deal" may show rare mismatches (e.g. `lmdeal=1`→`Evaluation`, 2 rows) — a snapshot-timing artifact (deal evolved Evaluation→Modification at the same `cycle_opened_date`), not a dict ambiguity; the dict is strictly 1:1.
> - **Sync layer (Redshift→MySQL, `asset_managment_config.py` `GEN_FORECLOSURE_LM`)**: No additional WHERE filter (full pass-through); `JOIN port.portfunding ON loanid` (loan must be in the funding pool).
> - **Multi-servicer**: Redshift staging table consolidates Newrez (`portnewrezlm`) + Carrington + Capecodfive LM data.

**Figure 13-7 — Loan Foreclosure Detail Page: Loss Mitigation Cycle Panel**

![BPS Loan Foreclosure Loss Mitigation Cycle Panel](../zh/image/bps-loan-foreclosure-loss-mitigation-cycle-panel.png)

### BPS Table Structure

**BPS storage table**: `bpms_dev.sync_loan_foreclosure_loss_mitigation` (22 columns)

| UI Column | BPS Field | Type | Newrez Raw Field | Source Table | Newrez Field → BPS Field |
|---|---|---|---|---|---|
| Deal | `deal` | varchar(256) | `lmdeal` (int) | portnewrezlm | ETL decodes numeric code to text (e.g. `7` → `"DIL"`) |
| Program | `program` | varchar(256) | `lmprogram` (int) | portnewrezlm | ETL decodes to text (e.g. `10` → `"Deed-in-Lieu"`) |
| Status | `lmc_status` | varchar(256) | `lmstatus` (int) | portnewrezlm | ETL decodes to text (e.g. `112` → `"Workout Denial"`, `166` → `"Pending Financials"`) |
| Cycle Opened Date | `cycle_opened_date` | date | `dealstartdate` | portnewrezlm | Direct (LM cycle start date) |
| Cycle Closed Date | `cycle_closed_date` | date | `lmremovaldate` | portnewrezlm | Direct (LM cycle end date; NULL = active) |
| Final Disposition | `final_disposition` | varchar(256) | `lmdecision` (int) | portnewrezlm | ETL decodes to text (e.g. `6` → `"Referral to FC"`, `11` → `"LMS Opened in Error"`, `99` → `"Pending"`) |
| Denial / Reason | `denialreason` | varchar(256) | `denialreason` (int) | portnewrezlm | ETL decodes to text; empty string if no denial |
| Borrower Intentions | `borrower_intentions` | varchar(256) | `borrowerintention` (int) | portnewrezlm | ETL decodes to text; typically empty for Newrez |
| Imminent Default | `imminent_default` | varchar(256) | *(no Newrez counterpart)* | — | NULL for all Newrez loans |
| Single Point of Contact | `single_point_of_contact` | varchar(256) | *(no Newrez counterpart)* | — | NULL for all Newrez loans |

### UI Column Reference

What each column on the BPS LM Cycle panel shows to the user and its role in the Loss Mitigation workflow:

| UI Column | Business Role | Notes |
|---|---|---|
| **Deal** | LM category (strategy direction) | Identifies the overall workout path: Evaluation → retention options (Modification / Forbearance / Payment Plan / Deferment) → exit options (Short Sale / DIL) → termination (Payoff). See "LM Field Values — Deal" below for value details. |
| **Program** | Specific workout plan | The investor program or proprietary plan ID within the Deal category (e.g., Bridger mod, 496.0, Deed-in-Lieu). More granular than Deal; directly determines the compliance and approval pathway. |
| **Status** | Current working status | Reflects the current progress milestone within this LM cycle (e.g., waiting for borrower documents, denied, negotiating junior liens). Updated in real time as the workout progresses. |
| **Cycle Opened Date** | Cycle start date | The date the servicer formally opened this workout attempt (maps to Newrez `dealstartdate`). |
| **Cycle Closed Date** | Cycle end date | The date this LM cycle was closed. **NULL = cycle still active.** Combined with Cycle Opened Date, gives the duration of the workout attempt. |
| **Final Disposition** | Concluding outcome | The summary conclusion when the cycle closes, directly determining whether FCL resumes: `Referral to FC` / `Request Incomplete` → FCL continues; `Approved` → FCL suspended; `Pending` → still in progress. |
| **Denial / Reason** | Denial reason | The specific reason the LM was denied (e.g., income below threshold, incomplete documentation). **Empty string (not NULL)** when no denial occurred. |
| **Borrower Intentions** | Borrower's stated preference | Records what the borrower says they want to do to resolve the delinquency (retain home, short sale, DIL, etc.). **Typically empty for Newrez loans** — Newrez does not provide `borrowerintention` data. |
| **Imminent Default** | Imminent default flag | CFPB Reg X requires servicers to evaluate LM options for borrowers facing "imminent default" (not yet delinquent but facing foreseeable hardship); this field flags that trigger condition. **Always NULL for Newrez loans** — Newrez does not report this data. |
| **Single Point of Contact** | Designated servicer contact | CFPB Reg X 12 CFR 1024.40 requires servicers to assign one dedicated employee as the primary contact for each borrower in loss mitigation; this field stores that contact's name or ID. **Always NULL for Newrez loans.** |

### Key Characteristics

- **Multi-row storage**: Each LM cycle (uniquely identified by `lmdeal` + `dealstartdate`) is stored as one row, recording the complete LM history for the loan.
- **Decoded text storage**: BPS stores business text labels, not Newrez raw numeric codes. (This differs from the hold table, where Newrez already provides text descriptions directly.)
- **Data volume**: loanid=7727000088 has 9 LM history records (2024-09 to 2026-02, MCP-verified).

**Live data (loanid=7727000088, MCP-verified)**:

| Deal | Program | Status | Cycle Opened | Cycle Closed | Final Disposition |
|---|---|---|---|---|---|
| Evaluation | Evaluation | Pending Financials | 2024-09-20 | 2024-10-21 | Request Incomplete |
| Modification | Bridger mod | Workout Denial | 2025-01-30 | 2025-03-11 | Referral to FC |
| Modification | Bridger mod | Workout Denial | 2025-03-17 | 2025-04-29 | Referral to FC |
| Modification | Bridger mod | Workout Denial | 2025-05-08 | 2025-06-14 | Referral to FC |
| Modification | 496.0 | Workout Denial | 2025-06-20 | 2025-10-20 | Referral to FC |
| Short Sale | Short Sale | Document Follow-up | 2025-10-20 | 2025-11-21 | Request Incomplete |
| DIL | Deed-in-Lieu | DIL Title Ordered | 2025-12-10 | 2026-01-27 | LMS Opened in Error |
| DIL | Deed-in-Lieu | Negotiate DIL liens | 2026-01-27 | 2026-02-17 | LMS Opened in Error |
| DIL | Deed-in-Lieu | Awaiting MI Approval | 2026-02-17 | NULL (active) | Pending |

### LM Field Values and Business Meaning

> The following enumerated values are produced by the Newrez ETL decode step (`lmdeal` / `lmprogram` / `lmstatus` / `lmdecision` integer codes → text). Full value distributions can be verified with Appendix B — SQL-11.

#### Deal (LM Category)

The `deal` field marks the direction of the current LM round, forming a natural escalation sequence from "retain the home" to "exit the home":

> MCP-verified (SQL-D1, latest-snapshot CTE JOIN) complete enumeration: `lmdeal` code → BPS `deal` text.

| `deal` Value | `lmdeal` Code | Business Meaning | Borrower Outcome | Typical Order |
|---|---|---|---|---|
| `Evaluation` | 2 | Initial assessment: collects borrower financials, determines applicable LM type; no specific plan committed yet | Undetermined | Step 1 |
| `Modification` | 1 | Loan modification: permanently changes rate / term / principal; borrower retains the property | Retain property | Step 2 |
| `Forbearance` | 5 | Temporary relief: suspends payments for 3–12 months (mandated during COVID by regulators) | Temporary relief | Step 2 (temporary) |
| `Payment Plan` | 4 | Repayment plan: repays arrears in installments without modifying loan terms | Retain property | Step 2 (light) |
| `Deferment` | 11 | Deferment: defers part of the arrears to the end of the loan as a lump sum; rate/term unchanged | Retain property | Step 2 (special) |
| `Short Sale` | 6 | Short sale: sells property for less than loan balance; lender provides written deficiency waiver | Sell property | Step 3 |
| `DIL` | 7 | Deed-in-Lieu: borrower voluntarily transfers title to lender; loan extinguished by agreement | Surrender property | Step 4 (final) |
| `Payoff` | 9 | Borrower pays off the loan in full (arrears + fees); FCL terminated | Pay off loan | Any time |

> ⚠️ **Correction from prior version**: `Repayment Plan` was outdated wording; MCP testing confirms the BPS-stored text is actually `Payment Plan` (lmdeal=4). Also added `Deferment` (lmdeal=11) and `Payoff` (lmdeal=9), two categories previously omitted.

#### Program (Specific Solution)

The `program` field identifies the specific workout plan within a `deal` category, decoded from Newrez `lmprogram` (int) via ETL:

> MCP-verified (SQL-D2, latest-snapshot CTE JOIN) complete enumeration, grouped by Deal category:

| `program` Value | `lmprogram` Code | Parent Deal | Business Meaning |
|---|---|---|---|
| `Evaluation` | 21 | Evaluation | Generic evaluation workflow (no specific plan) |
| `Deferment` | 73 | Deferment | Standard deferment plan |
| `Repayment Plan` | 29 | Payment Plan | Installment repayment plan |
| `Short-term Forbearance` | 12 | Forbearance | Short-term forbearance (typically 3–6 months) |
| `Disaster Forbearance` | 151 | Forbearance | Disaster-triggered forbearance |
| `Unemployment Forbearance` | 14 | Forbearance | Unemployment-triggered forbearance |
| `Short-term FB COVID` *(RETIRED 2023-11-01)* | 215 | Forbearance | COVID forbearance (retired) |
| `Bridger mod` | 419 | Modification | Proprietary Bridger / Newrez modification plan (non-GSE) |
| `SLS Standard Mod` | 240 | Modification | SLS standard modification plan |
| `Standard Proprietary Modification` | 273 | Modification | Generic proprietary modification |
| `FHA Recovery SAPC` | 348 | Modification | FHA payment recovery modification (SAPC) |
| `FHA Recovery Mod (40yr)` | 346 | Modification | FHA 40-year modification |
| `SLS Non-Standard Mod` | 358 | Modification | SLS non-standard modification |
| `VA Traditional` | 396 | Modification | VA traditional modification |
| `VA 30 Year Modification` | 364 | Modification | VA 30-year modification |
| `VA 40 Year Modification` | 365 | Modification | VA 40-year modification |
| `VASP No Trial` | 405 | Modification | VA VASP plan (no trial period) |
| `Short Sale` | 8 | Short Sale | Standard short sale workflow |
| `Deed-in-Lieu` | 10 | DIL | Standard deed-in-lieu workflow |
| `Payoff` | 25 | Payoff | Full payoff |

> Note: `program` values vary with investor guideline changes; the above are the valid plans observed in MCP testing. Codes `496` / `498` mapped inconsistently in testing — defer to the actual BPS record.

#### Status (Current Working Status)

`lmc_status` is decoded from Newrez `lmstatus` (int) and reflects the progress milestone within the LM cycle:

> MCP-verified (SQL-D3, latest-snapshot CTE JOIN) complete enumeration (`lmstatus` code → BPS `lmc_status` text):

| `lmc_status` Value | `lmstatus` Code | Business Meaning |
|---|---|---|
| `Pending Financials` | 166 | Waiting for borrower to submit financial documents (income verification, bank statements, etc.) |
| `Workout Denial` | 112 | Current LM round has been denied (borrower ineligible or unresponsive) |
| `Document Follow-up` | 5 | Partial documents received; following up to collect outstanding items |
| `Book mod` | 20 | Loan modification being formally booked (agreement signed, ETL writing to system) |
| `Monitor Forbearance` | 113 | Monitoring forbearance execution (whether borrower pauses payments as agreed) |
| `Deferment Agreement Ordered` | 140 | Deferment agreement ordered / signed |
| `Deferment Plan In Progress` | 139 | Deferment plan in progress |
| `Monitor for pmts/funds` | 25 | Monitoring whether borrower pays / funds arrive |
| `Follow up for 1st Trial Payment` | 13 | Following up on first trial-period payment (Trial Plan kickoff) |
| `Liquidation Referral` | 172 | Liquidation / disposition referral (plan failed, moved to liquidation) |
| `Not Assigned` | 116 | Unassigned handler / status |
| `Countered by Supervisor` | 45 | Supervisor countered / adjusted the plan (internal review step) |
| `Monitor for Mod Agreement` | 47 | Monitoring modification agreement execution |
| `DIL Title Ordered` | 126 | In the DIL process, a title search has been ordered (to confirm no other liens) |
| `Negotiate DIL liens` | 127 | Negotiating payoff terms with junior lienholders (second mortgage, HOA arrears, etc.) |
| `DIL Sent for Recording` | 135 | Deed-in-lieu documents submitted for title recording |
| `Awaiting investor approval` | 24 | Waiting for investor (e.g., Fannie Mae / VA) to approve the LM plan |
| `Awaiting MI Approval` | — | Waiting for the Mortgage Insurance (MI) company to approve (see loanid=7727000088 live record) |
| `Solicitation Offered` | 187 | Plan offer sent to borrower; awaiting response |
| `Submitted for Approval` | — | Submitted for approval; awaiting result |

#### Final Disposition (Outcome of the LM Round)

`final_disposition` is decoded from Newrez `lmdecision` (int) and records the conclusion when an LM cycle closes:

| `final_disposition` Value | Business Meaning | Impact on FCL |
|---|---|---|
| `Request Incomplete` | Borrower did not complete the application (missing docs / stopped responding / abandoned) | FCL proceeds |
| `Referral to FC` | LM definitively failed; case formally returned to foreclosure | FCL proceeds |
| `LMS Opened in Error` | LM record was created by operational mistake (not a real LM evaluation); should be disregarded | No impact (administrative error) |
| `Pending` | Cycle is still active; no final conclusion yet | FCL on hold |
| `Approved` | LM plan was approved for execution | FCL dismissed or suspended |
| `Denied` | LM plan was denied after full evaluation | FCL proceeds |
| `Withdrawn` | Borrower voluntarily withdrew the application | FCL proceeds |

---

### Why Does LM Have Multiple Cycles?

A single loan can accumulate multiple LM records (e.g., loanid=7727000088 has 9 rounds) for four primary reasons:

1. **Regulatory mandate**: CFPB Reg X (12 CFR 1024.41) requires servicers to evaluate all available LM options before advancing foreclosure. After each failed LM round, FCL briefly resumes, but a new round can be initiated as soon as the borrower again qualifies.
2. **Sequential deal escalation**: Borrowers typically start with retention-focused plans (Evaluation → Modification) and, upon failure, escalate to exit plans (Short Sale → DIL), each transition opening a new LM cycle.
3. **Program change**: Within the same deal category, a new investor guideline or compliance plan may trigger a fresh program attempt after the prior one is denied (e.g., Bridger mod → 496.0), generating multiple Modification cycles.
4. **Operational error**: System mistakes create an erroneously opened LM record, closed as `LMS Opened in Error`, requiring the correct cycle to be reopened.

#### loanid=7727000088 — Full Round Timeline (9 Rounds Explained)

| Round | Deal / Program | Outcome | Date Range | Root Cause |
|---|---|---|---|---|
| 1 | Evaluation / Evaluation | Request Incomplete | 2024-09-20 → 2024-10-21 | Regulatory initial assessment; borrower failed to submit documents → FCL continues |
| 2 | Modification / Bridger mod | Referral to FC | 2025-01-30 → 2025-03-11 | First attempt at modification; Workout Denial → formally referred back to FCL |
| 3 | Modification / Bridger mod | Referral to FC | 2025-03-17 → 2025-04-29 | 2nd attempt with same program; Workout Denial → Referral to FC |
| 4 | Modification / Bridger mod | Referral to FC | 2025-05-08 → 2025-06-14 | 3rd attempt with same program; Workout Denial → Referral to FC |
| 5 | Modification / 496.0 | Referral to FC | 2025-06-20 → 2025-10-20 | Switched to new investor plan (496.0); Workout Denial → Referral to FC |
| 6 | Short Sale / Short Sale | Request Incomplete | 2025-10-20 → 2025-11-21 | All modification plans failed; escalated to short sale; borrower did not complete application |
| 7 | DIL / Deed-in-Lieu | LMS Opened in Error | 2025-12-10 → 2026-01-27 | Short sale failed; escalated to DIL; record created in error and voided |
| 8 | DIL / Deed-in-Lieu | LMS Opened in Error | 2026-01-27 → 2026-02-17 | Second operational error; record voided again |
| 9 | DIL / Deed-in-Lieu | Pending (active) | 2026-02-17 → NULL | Formal DIL process underway; awaiting Mortgage Insurance (MI) company approval |

---

## Section 6: Bankruptcy Panel

> **Data Range**: The Bankruptcy panel is a **single-loan view** showing all bankruptcy records for the selected loan. Data comes from `bpms_dev.sync_loan_foreclosure_bankruptcy`. If the loan has no bankruptcy records, the panel displays "No Rows To Show" (confirmed by MCP query on loanid=7727000088). Bankruptcy records originate from Newrez `portnewrezbk`, independent of the main FCL table.
>
> **Source Data Filter Conditions (ETL code verified)**:
> - **Extraction layer (Newrez→Redshift, `basic_data_pool_config.py`)**: `newrez.portnewrezbk` filter: `WHERE LENGTH(TRIM(bkstatus)) > 0` (bankruptcy status code must be non-empty, excluding whitespace-only rows). Deduplication: `ROW_NUMBER() OVER (PARTITION BY loanid, bkfileddate ORDER BY dataasof DESC) = 1` (one row per bankruptcy filing, latest snapshot retained).
> - **Additional JOINs**: `LEFT JOIN newrez.portnewrezgeneral ON (loanid, dataasof)` to retrieve `legalstatus`; `LEFT JOIN newrez.portnewrezdatadic ON field_name='BKStatus'` to decode bankruptcy status.
> - **Sync layer (Redshift→MySQL, `asset_managment_config.py` `GEN_FORECLOSURE_BK`)**: No additional WHERE filter (full pass-through); `JOIN port.portfunding ON loanid` (loan must be in the funding pool).
> - **Multi-servicer**: Redshift staging table consolidates Newrez (`portnewrezbk`) + Carrington (`bk_flag` non-empty) + Capecodfive (`bankruptcy_flag != 'N'`) bankruptcy data.
> **Verification SQL**: See Appendix B — SQL-7 (confirms whether a loan has any bankruptcy records)

**Figure 13-8 — Loan Foreclosure Detail Page: Bankruptcy Panel**

![BPS Loan Foreclosure Bankruptcy Panel](../zh/image/bps-loan-foreclosure-bankruptcy-panel.png)

### BPS Table Structure

**BPS storage table**: `bpms_dev.sync_loan_foreclosure_bankruptcy` (22 columns)

| UI Column | BPS Field | Newrez Raw Field | Source Table | Newrez Field → BPS Field (ETL code-verified basic_data_pool_config.py:349-363) |
|---|---|---|---|---|
| Status | `bankruptcy_status` | `bkstatus` (int) + datadic | portnewrezbk | **`COALESCE(portnewrezdatadic[BKStatus].description, bkstatus)`** — decoded text, falls back to raw code if unmatched. Observed values: Completed/Cancelled \| Discharged \| Active \| Dismissed \| ReliefGranted \| Closed (occasional raw code e.g. `3.0`) |
| Legal Status | `legal_status` | `legalstatus` (text) | **portnewrezgeneral** | **Direct text** (DB-verified: FCBU/BK13/BK7/BK11/.../REO, 31/64 non-null); actual source is `portnewrezgeneral.legalstatus`, not a decode of `bkstage` |
| Status Date | `status_date` | **`bkfileddate`** | portnewrezbk | ⚠️ Direct from bankruptcy **filing date `bkfileddate`** (code-verified correction — NOT `bkrcurrentstatusdate`, which is mostly NULL in dev) |
| Chapter | `chapter` | `bkchapter` (int) | portnewrezbk | `CAST(bkchapter AS DECIMAL)` (7 / 11 / 13) |
| Lien Status | `lien_status` | *(none)* | — | ⚠️ **ETL hardcodes `NULL`** (`null as lien_status`); 0/64 populated |
| MFR Status | `mfr_status` | *(none)* | — | ⚠️ **ETL hardcodes `NULL`** (`null as mfr_status`, NOT `mfrhearingresults`); 0/64 |
| MFR Filed Date | `mfr_filed_date` | *(none)* | — | ⚠️ **Newrez path hardcodes `NULL`** (`null as mfr_filed_date`, NOT `mfrfileddate`); only 3/64 non-null (likely BPS-internal/historical) |
| Claim Status | `claim_status` | *(none)* | — | ⚠️ **ETL hardcodes `NULL`** (`null as claim_status`); 0/64 |
| Proof of Claim Date | `proof_of_claim_date` | `pocfileddate` | portnewrezbk | Direct (24/64 non-null) |
| Post Petition Due Date | `post_petition_due_date` | `bkpostpetitionduedate` | portnewrezbk | Direct (22/64 non-null; post-petition loan payment due date) |

### Notes

- This panel only contains data for loans with a bankruptcy filing history. UI screenshot for loanid=7727000088 shows "No Rows To Show" — confirmed by MCP: no records in `sync_loan_foreclosure_bankruptcy` for this loan.
- **(Resolved 2026-06-02, ETL code + DB-verified)** Verified field-by-field against `basic_data_pool_config.py:349-363` (BK extract layer):
  - `bankruptcy_status` = `COALESCE(portnewrezdatadic[BKStatus].description, bkstatus)` — decode to text, fall back to raw code if unmatched (observed e.g. `3.0`); decoded values: Completed/Cancelled(31) | Discharged(15) | Active(13) | Dismissed(2) | ReliefGranted(1) | Closed(1). The earlier "1→Active…5→ReliefGranted" 5-value map was incomplete — corrected.
  - `legal_status` comes **directly from `newrez.portnewrezgeneral.legalstatus`** (FCBU/BK13/BK7…, 31/64 non-null), not a decode of `bkstage`.
  - ⚠️ `status_date` is actually **`bkfileddate` (filing date)**, NOT `bkrcurrentstatusdate` (code-verified correction; the latter is mostly NULL in dev).
  - ⚠️ `lien_status` / `mfr_status` / `claim_status` / `mfr_filed_date` are **hardcoded `NULL`** in the Newrez extract path (`null as ...`); DB shows lien/mfr/claim = 0/64, `mfr_filed_date` only 3/64 (those loanids likely BPS-internal/historical, not the current extract). This corrects the earlier "mfr_status ← mfrhearingresults / mfr_filed_date ← mfrfileddate / lien·claim TBD" statements.
  - Sync layer `GEN_FORECLOSURE_BK` (`asset_managment_config.py`) has no extra WHERE, `JOIN port.portfunding`. Verify via Appendix B — SQL-13.

---

## Section 7: Aggregate Overview (Stage Tab + Time Line Tab)

> The Aggregate Overview page contains two view tabs, both drawing from the same data source `bpms_dev.sync_fcl_stage_info`: the **Stage Tab** groups loans by current stage and shows elapsed day statistics; the **Time Line Tab** shows each loan's FCL milestone dates as a horizontal timeline (see the `### Time Line Tab` subsection at the end of this section).
> **Data Range**: This page displays all active FCL loans that meet the entry criteria; approximately **13,321 loans** (dataasof 2026-05-24, fuller dataset / production scope). Each loan is grouped into the corresponding BPS stage bucket (via the `stage` field), showing stage-day statistics in a single row.
> **⚠️ Count reconciliation (2026-06-02, this dev env)**: current dev `bpms_dev.sync_fcl_stage_info` at latest `fctrdt=2026-03-13` has only **26 rows** (all Newrez / group=FCL) — a different dataset/snapshot than the 13,321 above. Related source counts: `newrez.portnewrezfc` latest snapshot (2026-05-31) `activefcflag=1`=**36**, `activefcflag=0`=5016 (5052 total); main FCL table `bpms_dev.sync_loan_foreclosure` (`fcreferraldate` not null, includes activefcflag=0 inactive loans) =**98**. These three populations (active aggregate / truly-active source / main table incl. inactive) are not directly comparable. (activefcflag=0 = not in active foreclosure: completed or withdrawn/reinstated/paid.)
>
> **Source Data Filter Conditions (ETL code verified — differs from Section 3.1)**:
> - **Primary filter (in-progress FCL, `basic_data_pool_config.py` `GEN_FCL_STAGE` lines 1789–1791)**: `activefcflag = 1 AND fcremovaldate IS NULL AND (fcremovaldesc IS NULL OR fcremovaldesc = '')` — only loans actively in FCL and not yet removed. ⚠️ **Inactive loans (`activefcflag=0`: not in active foreclosure — completed or withdrawn/reinstated/paid) are excluded from this table**, unlike `sync_loan_foreclosure` (which includes activefcflag=0 inactive loans).
> - **Secondary filter (pre-FCL demand-letter loans, lines 1809–1818)**: `activefcflag != 1 AND demandsentdate IS NOT NULL AND referral_start_date IS NULL AND delinquency_status IN ('D90', 'D120P')` — 90-day+ delinquent loans with a Demand Letter but not yet referred to FCL are also included (shown under `DEMAND` stage).
> - **Sync layer (Redshift→MySQL, `asset_managment_config.py` `GET_FCL_STAGE_DATA` lines 925–929)**: `SELECT a.* FROM port.fcl_stage_info a JOIN port.portfunding p ON a.loanid = p.loanid` (no additional WHERE; full pass-through with funding pool join).
> - **Difference from Section 3.1**: Main FCL table entry condition is `fcreferraldate IS NOT NULL` (includes activefcflag=0 historical inactive loans); Aggregation Overview condition is `activefcflag=1 AND fcremovaldate IS NULL` (active in-progress only, stricter). The two populations differ — their loan counts should not be directly compared.
> **Source table**: `bpms_dev.sync_fcl_stage_info` (one row per active FCL loan, 57 columns)
> **Validation SQL**: Stage distribution across all loans: Appendix B — SQL-9 (grouped by `stage`; reproduces the loan count breakdown shown on the Aggregation Overview page)

**Figure 13-9 — Foreclosure Aggregate Overview: Stage Tab Grouped Detail**

![BPS Foreclosure Aggregate Overview Stage Tab Grouped Detail](../zh/image/bps-foreclosure-aggregate-stage-tab-grouped-detail.png)

### BPS Table Structure

**BPS storage table**: `bpms_dev.sync_fcl_stage_info` (57 columns)

The Foreclosure aggregate overview page (`/agg-summary` → Foreclosure tab) groups loans by current stage and shows per-loan:

| UI Column | BPS Field | Description |
|---|---|---|
| [Stage] Date (e.g., Referral Date) | `{stage}_start_date` | Stage start date |
| Days to Sale | `to_sale_days` | Days remaining until sale date (Upcoming FC Sales group) |
| Days to Judgement | `to_judgement_days` | Days remaining until judgment date (Upcoming Judgement group) |
| Days in Stage | `{stage}_stage_days` | Days elapsed in current stage (all other stage groups) |
| Days in LM | `{stage}_in_lm_days` | Days in LM status during this stage |
| Days on Hold | `{stage}_on_hold_days` | Days on hold during this stage |

### Stage Field Prefixes in sync_fcl_stage_info

| Stage (BPS Group Header) | Field Prefix | Date Fields | Day Count Fields |
|---|---|---|---|
| NOI/Demand Letter | `demand_` | `demand_start_date`, `demand_end_date` | `demand_stage_days`, `demand_in_lm_days`, `demand_on_hold_days` |
| NOI (Approved for Referral) | `noi_` | `noi_start_date`, `noi_end_date` | `noi_stage_days`, `noi_in_lm_days`, `noi_on_hold_days` |
| Referral | `referral_` | `referral_start_date`, `referral_end_date` | `referral_stage_days`, `referral_in_lm_days`, `referral_on_hold_days` |
| First Legal | `first_legal_` | `first_legal_start_date`, `first_legal_end_date` | `first_legal_stage_days`, `first_legal_in_lm_days`, `first_legal_on_hold_days` |
| Service | `service_` | `service_start_date`, `service_end_date` | `service_stage_days`, `service_in_lm_days`, `service_on_hold_days` |
| Publication | `publication_` | `publication_start_date`, `publication_end_date` | `publication_stage_days`, `publication_in_lm_days`, `publication_on_hold_days` |
| Upcoming Judgement | `judgement_` | `judgement_start_date`, `judgement_end_date` | `to_judgement_days`, `judgement_in_lm_days`, `judgement_on_hold_days` |
| Upcoming FC Sales | `sale_` | `sale_start_date`, `sale_end_date` | `to_sale_days`, `sale_in_lm_days`, `sale_on_hold_days` |

> **Note**: `sync_fcl_stage_info` also includes `stage` (current stage name), `group`, `servicer`, `state`, and `judicial` fields for aggregation and filtering. The `first_legal_date_history` field tracks first legal date change history.

### Newrez Data Source

Date fields in `sync_fcl_stage_info` come from the corresponding timeline fields in `portnewrezfc` (same as Section 3.1). Day count fields are computed by BPS during daily sync. The `*_in_lm_days` and `*_on_hold_days` counts are derived by combining `portnewrezlm.activelmflag`, hold status history, and elapsed time calculations.

### Stage Classification Logic

BPS uses a **waterfall priority rule** to assign each loan a `stage` value: forward-looking scheduled events ("Upcoming" stages) are checked first; if none apply, the most recently completed milestone determines the stage. The conditions are **mutually exclusive and fully cover** all active FCL loans. The ETL writes the classification result to `sync_fcl_stage_info.stage`; **the BPS Foreclosure Summary page reads directly from that table's stage-specific fields — no additional transformation** (BPS page display = BPS stored data).

| Priority | `stage` Stored Value (all-caps DB code) | Classification Condition (Newrez `portnewrezfc` fields) | BPS Output Fields (`sync_fcl_stage_info`) |
|----------|----------------------------------------|--------------------------------------------------------|------------------------------------------|
| 1 | `SALE` | `fcscheduledsaledate IS NOT NULL` | `sale_start_date` \| `to_sale_days` \| `sale_in_lm_days` \| `sale_on_hold_days` |
| 2 | `JUDGEMENT` | `fcjudgmenthearingscheduled IS NOT NULL` AND `fcscheduledsaledate IS NULL` | `judgement_start_date` \| `to_judgement_days` \| `judgement_in_lm_days` \| `judgement_on_hold_days` |
| 3 | `PUBLICATION` | `publication_date IS NOT NULL` (always 0 for Newrez loans — see Section 8 Q1) | `publication_start_date` \| `publication_stage_days` \| `publication_in_lm_days` \| `publication_on_hold_days` |
| 4 | `SERVICE` | `servicecompletedate IS NOT NULL` AND priorities 1–3 not triggered | `service_start_date` \| `service_stage_days` \| `service_in_lm_days` \| `service_on_hold_days` |
| 5 | `FIRST_LEGAL` | `firstlegaldate IS NOT NULL` AND `servicecompletedate IS NULL` | `first_legal_start_date` \| `first_legal_stage_days` \| `first_legal_in_lm_days` \| `first_legal_on_hold_days` |
| 6 | `REFERRAL` | `fcreferraldate IS NOT NULL` AND `firstlegaldate IS NULL` | `referral_start_date` \| `referral_stage_days` \| `referral_in_lm_days` \| `referral_on_hold_days` |
| 7 | `DEMAND` | `demandsentdate IS NOT NULL` AND `fcreferraldate IS NULL` (post-entry loans should not hit this; live rate = 0%) | `demand_start_date` \| `demand_stage_days` \| `demand_in_lm_days` \| `demand_on_hold_days` |

#### Stage Code → BPS Page Display Name Mapping

The `stage` field stores short all-caps codes; the BPS Foreclosure Summary page front-end maps them to display names (display-layer conversion only, no additional storage):

| `stage` DB Stored Value | BPS Foreclosure Summary Page Display Name |
|---|---|
| `SALE` | Upcoming FC Sales |
| `JUDGEMENT` | Upcoming Judgement |
| `PUBLICATION` | Publication |
| `SERVICE` | Service |
| `FIRST_LEGAL` | First Legal |
| `REFERRAL` | Referral |
| `DEMAND` | NOI/Demand Letter |

> When filtering in SQL, use the stored code — e.g., `WHERE stage = 'REFERRAL'` (not `'Referral'`).

> **Key points**:
> - All classification fields come from `newrez.portnewrezfc` (the same source table as Section 3.1)
> - `fcscheduledsaledate` carries the highest priority — a scheduled sale date immediately places the loan into `SALE`, regardless of judicial/non-judicial status
> - `SALE` covers both Judicial states (post-judgment → sale scheduled) and Non-Judicial states (post-service/publication → sale scheduled)
> - `PUBLICATION` is always 0 for Newrez loans — Newrez does not provide a `publication_date` field (see Section 8 Q1)
> - `DEMAND` is always 0 post-entry — the entry condition already requires `fcreferraldate IS NOT NULL`, so all ingested loans have advanced beyond level 7
> - **ETL output field**: The classification result is written to `sync_fcl_stage_info.stage`; the BPS page reads directly from that table's stage-specific fields — no additional transformation (**BPS page display = BPS stored data**)
> - **`stage` stores all-caps codes** (`SALE`/`JUDGEMENT`/`SERVICE`/`FIRST_LEGAL`/`REFERRAL`/`DEMAND`/`PUBLICATION`); the BPS page performs a display-layer name mapping; SQL filters must use the stored codes
> - **`sync_fcl_stage_info` is a daily snapshot table** (`fctrdt` = snapshot date, one row per loan per day): filter to current state with `fctrdt = MAX(fctrdt)`; when JOINing `portnewrezfc`, add both `COLLATE utf8mb4_general_ci` (collation mismatch) and `p.dataasof = s.fctrdt` (prevents Cartesian product)
> - **Validation SQL**: Appendix B — SQL-10 has all three fixes applied and is MCP-verified (26 rows, no duplicates for current Newrez snapshot)

### Time Line Tab

> **Data source**: Same as Stage Tab — `bpms_dev.sync_fcl_stage_info` (daily snapshot; filter to current state with `fctrdt = MAX(fctrdt)`). Current Newrez snapshot (2026-03-13): 26 loans, all `group = FCL`.
> **Validation SQL**: Appendix B — SQL-12

The Time Line Tab shows **one row per loan**, displaying each FCL milestone date as a horizontal timeline sequence (numbers 1–7 indicate FCL stage **chronological order**, not priority). Unlike the Stage Tab which shows elapsed day statistics, this view directly shows actual milestone dates, making it easy to trace a loan's full FCL progression history.

#### Field Mapping (MCP JOIN-Verified)

**BPS storage table**: `bpms_dev.sync_fcl_stage_info` (same table as Stage Tab)

| UI Column | # | BPS Field | Newrez Source Field (`portnewrezfc`) | Newrez Fill Rate / Notes |
|---|---|---|---|---|
| Loan ID | — | `loanid` | `loanid` | 100% |
| Group | — | `group` | Derived field (ETL-assigned) | FCL / REO / D120P (see Note 1) |
| Servicer | — | `servicer` | Static "Newrez" | — |
| States | — | `state` | `state` | 100% |
| Judicial | — | `judicial` | `judicial` | 100%; Y = Judicial state, N = Non-Judicial |
| NOI Date | 1 | `noi_start_date` | `demandsentdate`* | Always NULL for Newrez (see Note 2) ⚠️ |
| Referral Date | 2 | `referral_start_date` | `fcreferraldate` | 100% (FCL entry prerequisite) ✅ |
| First Legal Date | 3 | `first_legal_start_date` | `firstlegaldate` | ✅ |
| Service Date | 4 | `service_start_date` | `servicecompletedate` | 28.9% fill rate ✅ |
| Publication Date | 5 | `publication_start_date` | No corresponding field | Always NULL for Newrez (see Note 3) ⚠️ |
| Judgement Date | 6 | `judgement_start_date` | `fcjudgmenthearingscheduled` | Judicial states only; note the business-meaning difference from `fcjudgmententered` (see Note 4) ⚠️ |
| Sale Date | 7 | `sale_start_date` | `fcscheduledsaledate` | ✅ |

#### MCP Live Validation Sample (vs. Image #12 Screenshot)

| loanid | Group | Judicial | Referral Date 2 | First Legal Date 3 | Service Date 4 | Judgement Date 6 | Sale Date 7 |
|---|---|---|---|---|---|---|---|
| 7727000357 | FCL | Y (IL) | 2025-01-23 | 2025-06-11 | 2025-08-14 | 2026-01-18 | 2026-04-08 |
| 7727000088 | FCL | Y (FL) | 2025-05-23 | 2025-06-13 | 2025-07-18 | 2026-07-15 | NULL |
| 7727004200 | FCL | Y | 2025-06-27 | 2025-07-21 | 2025-12-24 | 2026-04-13 | 2026-05-19 |

#### Key Notes

> - **Note 1 — Group field**: `group` is an ETL-derived classification, not directly from Newrez raw data. Three values: `FCL` (Active Foreclosure — loan is actively in the FCL pipeline), `REO` (Real Estate Owned — lender took possession after no third-party bidder at auction), `D120P` (120+ Days Past Due — delinquent but not yet referred to FCL). Current snapshot (2026-03-13): all 26 Newrez loans are `FCL`.
> - **Note 2 — NOI Date 1 vs. Demand Date (important distinction)**:
>   - `noi_start_date` (data source for the "NOI Date 1" UI column): Always NULL for Newrez — Newrez does not populate the `noi_start_date` field, so this UI column is always blank for Newrez loans.
>   - `demand_start_date` (**not displayed in the Time Line Tab**): Newrez `demandsentdate` → BPS `demand_start_date`; 24/26 loans in the current snapshot have a value. This field is used only for Stage Tab day-count calculations and is not surfaced as "NOI Date" in the Time Line Tab.
> - **Note 3 — Publication Date 5**: `publication_start_date` is always NULL for Newrez loans — Newrez does not provide a `publication_date` field (see Section 8 Q1).
> - **Note 4 — Judgement Date: two different fields, two different time points** (v20 corrected): BPS `judgement_start_date` maps to **`fcjudgmenthearingscheduled`** (judgment hearing scheduled date — a *future planned event*), NOT to `fcjudgmententered` (date the court formally entered the judgment — a *completed legal fact*). These two fields have completely different business meanings:
>   - `fcjudgmenthearingscheduled`: The scheduled/set date of the upcoming judgment hearing or sale confirmation hearing. This is the date BPS uses for `judgement_start_date` / `timeline_judgement_date`. ETL code confirmed: `fc.fcjudgment_hearing_scheduled AS timeline_judgement_date` (`basic_data_pool_config.py`).
>   - `fcjudgmententered`: The date the court formally entered (recorded) the judgment — a completed legal fact. Stored in ETL intermediate table as `fcjudgment_end_date`; used for `actual_judgement_hearing_set_days` calculation, not directly shown in the Time Line Tab.
>   - MCP-verified (loan 7727000357): `fcjudgmenthearingscheduled` = 2026-01-18 **matches** BPS `judgement_start_date` = 2026-01-18 ✅; `fcjudgmententered` = 2026-01-07 (11 days earlier, a different date). The ~11-day gap is NOT a processing delay — it is the difference between the hearing scheduled date and the court entry date.
> - **Timeline numbers 1–7**: Numbers indicate FCL stage **chronological order** (Demand/NOI → Referral → First Legal → Service → Publication → Judgement → Sale) — not priority. Priority waterfall is in the Stage Tab section above.
> - **Stage Tab vs. Time Line Tab**: Stage Tab groups by current `stage` and shows elapsed day statistics per stage bucket; Time Line Tab shows one row per loan with all milestone dates horizontally — easy to trace the full FCL timeline for any loan.
> - **Validation SQL**: Appendix B — SQL-12 (reproduces the Time Line Tab view; includes `demand_start_date` as a comparison column)

---

## Section 8: Known Data Quality Issues (Newrez-Specific)

> **Verification SQL**: Q8 (title fields 0% fill rate) comes from Appendix B — SQL-1; Q9 (fcsaleamount anomaly) comes from SQL-3

| Issue # | Description | Affected BPS Fields | Current Status |
|---|---|---|---|
| Q1 | `timeline_publication_date` — no corresponding field in `portnewrezfc` | `timeline_publication_date`, `actual_publication_days` | Field is null in BPS for Newrez loans; related actual/var fields also null |
| Q2 | `fcsetupdate` and `fcreferraldate` are typically the same date, making `actual_approved_for_referral_days` and `actual_referred_to_attorney_days` near-zero | `actual_approved_for_referral_days`, `actual_referred_to_attorney_days` | Expected behavior — Newrez completes approval and referral simultaneously |
| Q3 | `activefcflag` historically had NULL values (documented as P0 issue in doc 08) | `summary_completed_foreclosure` | Requires NULL-safe handling: treat `activefcflag IS NULL` as in-progress |
| Q4 | `currentmilestone` and `fcstage` track different things: `fcstage` is Newrez's current workflow step; `currentmilestone` is the BPS milestone label (sometimes set ahead of time) | `summary_current_step` | When they differ, `currentmilestone` takes priority, which may appear inconsistent. ⚠️ **doc 19 field measurement (2026-06-04) conflicts with this — BPS actually uses `fcstage`; pending ETL-code verification, see Q13** |
| Q5 | `demandsentdate` is null for ~14.1% of active FCL loans | `timeline_notice_of_intent_date`, `actual_notice_of_intent_days` | Loans without NOI data can still be in FCL (entry condition uses `fcreferraldate`, not `demandsentdate`) |
| Q6 | `imminent_default` and `single_point_of_contact` in LM sync table are NULL for all Newrez loans | LM Cycle panel — these two columns | Newrez does not provide these fields; always null for Newrez loans |
| Q7 | Are BK panel `bankruptcy_status` / `legal_status` decoded text? | Bankruptcy panel Status and Legal Status columns | ✅ **Resolved (2026-06-02, DB-verified)**: `bankruptcy_status` = ETL decode of `bkstatus` (int 1–5) to text (1→Active \| 2→Discharged \| 3→Dismissed \| 4→Closed \| 5→ReliefGranted); `legal_status` comes directly from `newrez.portnewrezgeneral.legalstatus` (text FCBU/BK13/BK7…), not a decode of `bkstage`. Both are text, not numeric codes |
| Q8 | `titlereceiveddate` and `titlecleardate` have **0.0% fill rate** for active FCL loans (MCP-verified) — Newrez does not populate title-related date fields | `timeline_title_report_received_date`, `timeline_preliminary_title_cleared_date`, `timeline_final_title_cleared_date`; and related `actual_*`, `var_*` fields | All three BPS title milestone fields will **always be null** for Newrez loans. Same nature as Q1 (Publication) — Newrez simply does not report these dates |
| Q9 | `fcsaleamount` has **4.7% fill rate** for active FCL loans — higher than sale-held rate (`fcsalehelddate` = 2.1%). ~2.6% of active loans have a sale amount recorded without a corresponding sale held date | `summary_foreclosure_sale_amount` | Likely a Newrez field update sequencing issue (amount arrives before held date). When using `fcsaleamount`, always verify `fcsalehelddate` is non-null ⚠️ |
| Q10 | **[v20 corrected]** `sync_fcl_stage_info.judgement_start_date` maps to **`fcjudgmenthearingscheduled`** (hearing scheduled date), NOT `fcjudgmententered` (court entry date). These two fields measure different time points. MCP-verified (loan 7727000357): `fcjudgmenthearingscheduled` = 2026-01-18 **matches** BPS `judgement_start_date` = 2026-01-18 ✅; `fcjudgmententered` = 2026-01-07. The ~11-day gap is NOT a processing lag — `fcjudgmenthearingscheduled` is the scheduled hearing date (future planned event); `fcjudgmententered` is when the court formally recorded the judgment (completed legal fact). ETL code: `fc.fcjudgment_hearing_scheduled AS timeline_judgement_date` (`basic_data_pool_config.py`) | Time Line Tab "Judgement Date 6" column; `sync_fcl_stage_info.judgement_start_date` | Root cause confirmed: two fields with different business meanings. When verifying Judgement Date 6, use `fcjudgmenthearingscheduled`; use `fcjudgmententered` only for actual hearing-set → judgment-entered days calculation ⚠️ |
| Q11 | Time Line Tab "NOI Date 1" column (`noi_start_date`) is **always NULL for Newrez** loans; Newrez `demandsentdate` is stored in `demand_start_date` (24/26 populated) but this field does NOT map to the Time Line Tab's NOI Date column | Time Line Tab "NOI Date 1" column; `sync_fcl_stage_info.noi_start_date` | `noi_start_date` is always null for Newrez. To look up the Demand Letter date, query `demand_start_date` (the source for Stage Tab day-count calculations) — do not rely on the Time Line Tab's NOI Date column for Newrez loans ⚠️ |
| Q12 | `port.basic_data_loan_fcl.fcjudgment_end_date` (sourced from Newrez `fcjudgmententered` / Capecodfive `foreclosure_judgement_date`) is stored in the Redshift ETL intermediate table but **is never referenced by any downstream ETL query** and does not flow into any BPS MySQL field. The ETL origin of `bpms_dev.sync_loan_foreclosure.actual_judgement_hearing_set_days` (judgment stage elapsed days) is unclear — likely computed at the BPS application layer | `timeline_judgement_date` (connected to `fcjudgment_hearing_scheduled` ✅); `actual_judgement_hearing_set_days` (ETL source unknown); all `var_*/target_*` judgment day-count fields | `fcjudgment_end_date` is a **design-reserved field**: its name follows the intermediate table's start/end naming convention (`fcjudgment_hearing_scheduled` = stage start, `fcjudgment_end_date` = stage end); cross-servicer normalized (Capecodfive's `foreclosure_judgement_date` maps to the same column); currently has no impact on BPS display; reserved as a future data source for `actual_judgement_hearing_set_days` ETL (= `fcjudgment_end_date` − `fcjudgment_hearing_scheduled`). See doc 12 Section 15 |
| Q13 | **[Field-measured discrepancy · pending verification]** `summary_current_step` documented rule is `COALESCE(currentmilestone, fcstage)` (currentmilestone first, see Q4), but **doc 19 field measurement (2026-06-04; 4 of 5 sample loans are in the FCL table) shows BPS actual = `fcstage`** while src `currentmilestone` is non-empty — e.g. `7727000088` src `currentmilestone='Sold'` vs BPS `summary_current_step='Post Sale Review (SCRA and PACER Check)'` (= `fcstage`); `7727000672` `'Closed'` vs `'Pre-Sale Review 1…'`. Two possibilities: ① the documented order is reversed and BPS actually uses `fcstage`; ② BPS is **overwrite-refreshed** and at load time `currentmilestone` was still empty (snapshot timing). **ETL source `basic_data_pool_config.py` is not in this repo — pending verification** (conflicts with Q4; ETL code is authoritative) | `summary_current_step`; corrects/confirms Q4 | ⚠️ **pending ETL-code verification**; evidence in doc 19 main sheet 取数公式 (red cells) + doc 16 ① FCL Summary note |
| Q14 | **[Field-measured · confirmed phenomenon]** Several BPS main-table `sync_loan_foreclosure` fields are **unpopulated** (Newrez src has values but the BPS column is empty); doc 19 (2026-06-04) — all 4 hit loans empty: `timeline_notice_of_intent_date` / `timeline_notice_of_intent_end_date` / `timeline_approved_for_referral_date` / `timeline_referred_to_attorney_date` / `timeline_foreclosure_completed_date` / `summary_servicer_number` / `summary_completed_foreclosure` / `summary_foreclosure_attorney`. Consistent with prod col-S measurements (these columns largely empty/all-NULL). ⚠️ Note: **same-source** fields `summary_firm` (=`fcfirm`) and `timeline_referred_to_foreclosure_date` (=`fcreferraldate`) **are** populated → BPS-ETL **partial fill** (not a Newrez source gap, unlike Q1/Q8) | the 8 BPS fields above | phenomenon confirmed; **why unfilled** pending ETL-code verification. `summary_completed_foreclosure` all-NULL also see §3.7 / doc 14 v34; evidence in doc 19 + doc 16 note |

### Q3 Technical Detail: `activefcflag` NULL-safe Handling

#### Background

`portnewrezfc.activefcflag` is a **P0-priority field** for BPS entry. Expected values:

| Value | Meaning |
|-------|---------|
| `1` | In active foreclosure (Active Foreclosure) |
| `0` | Not currently in active foreclosure (Closed / Removed: includes completed AND withdrawn/reinstated/paid) |
| `NULL` | ⚠️ Historical legacy issue (see below) |

**Problem**: Newrez historical data contains loans where `activefcflag IS NULL`, yet these loans were still actively in the FCL process — **not closed**. Newrez simply failed to populate `1` for those historical records, leaving the field blank.

#### Why NULL should be treated as "in-progress" rather than "closed"

In BPS's data architecture, FCL **closure** has explicit, multi-field evidence:

- `fcremovaldate` is populated → explicit exit date
- `fcremovaldesc` is populated → explicit exit reason (e.g., `'Borrower Reinstated'`, `'Loss Mitigation'`, `'Paid in Full'`, `'Process Complete'`)

> Note: `activefcflag=0` means **not currently in active foreclosure**; the exit reason is most often **reinstated / loss-mitigation / paid (stopped, NOT completed)**, and only a minority are REO/3rd Party/DiL (truly completed). So `activefcflag=0` ≠ "completed".

Therefore: **if a loan has exited active foreclosure, there is unambiguous exit evidence — it is not identified solely by `activefcflag = 0`.**

Conversely, if `activefcflag IS NULL` and `fcremovaldate` is also null, the conservative interpretation is "still in FCL."

> **Asymmetric risk**: **Missing an active FCL loan** (incorrectly treating it as closed) is a worse outcome than **tracking an already-closed loan** (incorrectly treating it as active) — the former creates a BPS display gap; the latter at most shows one extra historical row.

#### Correct ETL / query pattern

```sql
-- ❌ Unsafe — drops all loans where activefcflag IS NULL
WHERE activefcflag = 1

-- ✅ Option 1: explicit OR NULL (recommended — clearest intent)
WHERE activefcflag = 1 OR activefcflag IS NULL

-- ✅ Option 2: COALESCE substitution (works well inside complex expressions)
WHERE COALESCE(activefcflag, 1) = 1
```

> **Note**: MySQL's `<=>` operator (NULL-safe equal) makes two NULLs equal (`NULL <=> NULL` = TRUE), but `activefcflag <=> 1` still excludes NULLs (`NULL <=> 1` = FALSE). Therefore `<=>` **does not apply here**.

#### Impact scope

| Dimension | Detail |
|-----------|--------|
| **Affected data** | Newrez historical FCL records (see doc 08 P0 issue log for counts) |
| **Current new data** | Newrez now populates `activefcflag = 1` correctly; no new NULLs being introduced |
| **Primary affected BPS field** | `summary_completed_foreclosure` (entry condition uses this field to distinguish in-progress vs. closed) |
| **Recommended fix** | Use `COALESCE(activefcflag, 1) = 1` in all ETL entry filters; validate fill rate for this field when onboarding any new Servicer |
| **Cross-references** | doc 08 P0 issue log · doc 14 Section 2.1 P0 field table · doc 14 Appendix B |

---

## Appendix A: Multi-Panel End-to-End Validation

> All data below was obtained via MCP live database queries (direct MySQL access). To reproduce, see Appendix B — SQL-4 for Newrez raw fields; SQL-5 for Hold history; SQL-6 for LM history; SQL-7 for Bankruptcy check.

### A. loanid=7727000672 (Non-Judicial, in progress, Referral stage)

| BPS Display Field | Calculated Value | Source |
|---|---|---|
| `timeline_notice_of_intent_date` | 2025-11-17 | `demandsentdate` |
| `timeline_notice_of_intent_end_date` | 2025-12-22 | `demandexpirationdate` |
| `timeline_approved_for_referral_date` | 2026-03-09 | `fcsetupdate` |
| `timeline_referred_to_foreclosure_date` | 2026-03-09 | `fcreferraldate` |
| `timeline_first_legal_date` | 2026-03-25 | `firstlegaldate` |
| `timeline_sale_date_projected_date` | 2026-08-06 | `fcscheduledsaledate` |
| `summary_judicial_foreclosure` | 0 (Non-Judicial) | `judicial` |
| `summary_firm` | Orlans Law Group PLLC | `fcfirm` |
| `summary_foreclosure_status` | Pre-Sale Review 1 (SCRA and PACER Check) | ⚠️ The screenshot shows the `fcstage` text (old ETL behavior / stale sample). **Current rule**: `activefcflag=1` → fixed text `'Active Foreclosure'`; this `fcstage` text now goes to `summary_current_step` (see §3.7) |
| `summary_last_step_completed` | First Publication | `lastfcstepcompleted` |
| `summary_last_step_completed_date` | 2026-03-25 | `lastfcstepcompleteddate` |
| `summary_sms_days_in_fcl` | **79 days** | `smsdaysinfc(77) + DATEDIFF(2026-05-26, 2026-05-24)` |
| `actual_notice_of_intent_days` | 35 days | 2025-12-22 − 2025-11-17 |
| `actual_referred_to_foreclosure_days` | 16 days | 2026-03-25 − 2026-03-09 |
| Hold panel | No records | `sync_loan_foreclosure_hold` — no rows for this loan |
| `variance_estimated_hold_days` | Check `portnewrezfc.fchold*projectedenddate` | — |

### B. loanid=7727000088 (Judicial, multi-panel validation)

> Note: UI screenshot was taken while loan was in Judgment Entered stage. MCP latest data (2026-05-24) shows the loan has since sold (REO, 2026-05-22, $200,100). Values below reflect the screenshot time point.

**Foreclosure Summary panel**:

| BPS Display Field | UI Value | Newrez Source |
|---|---|---|
| Foreclosure status | Active Foreclosure | `activefcflag=1` → fixed text `'Active Foreclosure'` (not `fcstage`; `fcstage` now goes to `summary_current_step`) |
| Foreclosure bid amount | (empty) | `fcbidamount` (not yet populated) |
| Foreclosure sale amount | (empty) | `fcsaleamount` (sale not yet complete) |
| Contested / Litigation | 0 | `fccontestedflag` |
| Firm | Kelley Kronenberg, P.A. | `fcfirm` |
| Type | Judicial | `judicial=1` |
| SMS Days in Foreclosure | 298 | `smsdaysinfc + DATEDIFF(screenshot_date, dataasof)` |
| Days in Foreclosure | 298 | `daysinfc + DATEDIFF(screenshot_date, dataasof)` |
| Current Step | Judgment Entered | `currentmilestone` or `fcstage` |
| Last Step Completed | Motion for Judgment Sent to Court | `lastfcstepcompleted` |
| Last Step Completed Date | 2025-12-17 | `lastfcstepcompleteddate` |

**Hold panel** (MCP-verified, sync_loan_foreclosure_hold, 7 records):

| Description | Start Date | End Date | Newrez Source |
|---|---|---|---|
| Original Note | 2025-05-28 | 2025-06-11 | fchold*description/startdate/enddate |
| Service Delay | 2025-07-15 | 2025-07-31 | same |
| Loss Mitigation Workout | 2025-07-31 | 2025-08-01 | same |
| Loss Mitigation Workout | 2025-08-13 | 2025-10-21 | same |
| Court Delay | 2025-10-21 | 2025-12-16 | same |
| Loss Mitigation Workout | 2026-02-20 | 2026-02-24 | same |
| Court Delay | 2026-01-16 | NULL (ongoing) | same |

**Loss Mitigation Cycle panel** (MCP-verified, 9 records — see Section 5 for full data).

**Bankruptcy panel**: No Rows To Show — confirmed by MCP: no records in `sync_loan_foreclosure_bankruptcy` for this loan.

---

## Appendix B: Data Verification SQL

> This appendix contains 7 SQL queries that can be run directly in MySQL, covering all numeric values, distributions, and sample data in this document that were derived from MCP database queries.
> Connection: Both `newrez` and `bpms_dev` schemas reside on the same MySQL instance (dev environment). All queries below are read-only.

### B.1 Aggregate Statistics

Use these to reproduce all **percentage values and distributions** in the document and understand the overall FCL data landscape.

---

#### SQL-1 — Active FCL Field Fill Rate Survey

> **Document coverage**: Section 2.1 Fill Rate column, Section 3.1 Measured Fill Rate column, Section 3.7 summary field business meanings, Section 8 Q8  
> **Source table**: `newrez.portnewrezfc` (`activefcflag=1`, approximately 13,321 active FCL loans)

```sql
-- ============================================================
-- SQL-1: Active FCL field fill rate survey
-- Source table: newrez.portnewrezfc
-- Produces: Section 2.1 fill rate column / Section 3.1 measured fill rate
--           Section 3.7 summary field fill rates / Section 8 Q8
-- ============================================================
SELECT
  COUNT(*) AS total_active_fcl,

  -- ── Timeline dates (corresponding to Section 3.1 timeline_* fields) ──
  ROUND(SUM(demandsentdate             IS NOT NULL)/COUNT(*)*100,1) AS demandsentdate_pct,
  ROUND(SUM(demandexpirationdate       IS NOT NULL)/COUNT(*)*100,1) AS demandexpirationdate_pct,
  ROUND(SUM(fcsetupdate                IS NOT NULL)/COUNT(*)*100,1) AS fcsetupdate_pct,
  ROUND(SUM(fcreferraldate             IS NOT NULL)/COUNT(*)*100,1) AS fcreferraldate_pct,
  ROUND(SUM(firstlegaldate             IS NOT NULL)/COUNT(*)*100,1) AS firstlegaldate_pct,
  ROUND(SUM(servicecompletedate        IS NOT NULL)/COUNT(*)*100,1) AS servicecompletedate_pct,
  ROUND(SUM(titlereceiveddate          IS NOT NULL)/COUNT(*)*100,1) AS titlereceiveddate_pct,       -- Q8: expected 0%
  ROUND(SUM(titlecleardate             IS NOT NULL)/COUNT(*)*100,1) AS titlecleardate_pct,          -- Q8: expected 0%
  ROUND(SUM(fcjudgmenthearingscheduled IS NOT NULL)/COUNT(*)*100,1) AS fcjudgmenthearingscheduled_pct,
  ROUND(SUM(fcjudgmententered          IS NOT NULL)/COUNT(*)*100,1) AS fcjudgmententered_pct,
  ROUND(SUM(fcscheduledsaledate        IS NOT NULL)/COUNT(*)*100,1) AS fcscheduledsaledate_pct,
  ROUND(SUM(fcsalehelddate             IS NOT NULL)/COUNT(*)*100,1) AS fcsalehelddate_pct,
  ROUND(SUM(dtdeedrecorded             IS NOT NULL)/COUNT(*)*100,1) AS dtdeedrecorded_pct,
  ROUND(SUM(fcremovaldate              IS NOT NULL)/COUNT(*)*100,1) AS fcremovaldate_pct,
  ROUND(SUM(COALESCE(dtdeedrecorded, fcremovaldate) IS NOT NULL)/COUNT(*)*100,1) AS fcl_completed_coalesce_pct,
  ROUND(SUM(fcl3rdpartyproceedsreceiveddate IS NOT NULL)/COUNT(*)*100,1) AS thirdparty_proceeds_pct,

  -- ── Status text fields ────────────────────────────────────────
  ROUND(SUM(fcstage       IS NOT NULL AND fcstage       != '')/COUNT(*)*100,1) AS fcstage_pct,
  ROUND(SUM(currentmilestone IS NOT NULL AND currentmilestone != '')/COUNT(*)*100,1) AS currentmilestone_pct,
  ROUND(SUM(fcresults     IS NOT NULL AND fcresults     != '')/COUNT(*)*100,1) AS fcresults_pct,
  ROUND(SUM(fcremovaldesc IS NOT NULL AND fcremovaldesc != '')/COUNT(*)*100,1) AS fcremovaldesc_pct,
  ROUND(SUM(lastfcstepcompleted     IS NOT NULL AND lastfcstepcompleted     != '')/COUNT(*)*100,1) AS lastfcstepcompleted_pct,
  ROUND(SUM(lastfcstepcompleteddate IS NOT NULL)/COUNT(*)*100,1) AS lastfcstepcompleteddate_pct,

  -- ── Bid / amount fields (Section 3.6 / 3.7) ──────────────────
  ROUND(SUM(fcbidamount    IS NOT NULL)/COUNT(*)*100,1) AS fcbidamount_pct,
  ROUND(SUM(fcapprbidprice IS NOT NULL)/COUNT(*)*100,1) AS fcapprbidprice_pct,
  ROUND(SUM(fcsaleamount   IS NOT NULL)/COUNT(*)*100,1) AS fcsaleamount_pct,   -- Q9: expected higher than fcsalehelddate

  -- ── Identifier / attorney fields (Section 3.7) ───────────────
  ROUND(SUM(shellpointloanid IS NOT NULL AND shellpointloanid != '')/COUNT(*)*100,1) AS shellpointloanid_pct,
  ROUND(SUM(fcfirm           IS NOT NULL AND fcfirm           != '')/COUNT(*)*100,1) AS fcfirm_pct,

  -- ── Hold slots (Section 3.5 / Section 4) ─────────────────────
  ROUND(SUM(fchold1description IS NOT NULL)/COUNT(*)*100,1) AS fchold1description_pct,
  ROUND(SUM(fchold2description IS NOT NULL)/COUNT(*)*100,1) AS fchold2description_pct,
  ROUND(SUM(fchold3description IS NOT NULL)/COUNT(*)*100,1) AS fchold3description_pct

FROM newrez.portnewrezfc
WHERE activefcflag = 1
  AND dataasof = (SELECT MAX(dataasof) FROM newrez.portnewrezfc);
```

---

#### SQL-2 — fcresults Distribution (Auction Outcome Breakdown)

> **Document coverage**: Section 3.1 note "266 loans with fcresults='3rd Party'"  
> **Source table**: `newrez.portnewrezfc`

```sql
-- ============================================================
-- SQL-2: fcresults distribution
-- Source table: newrez.portnewrezfc
-- Produces: Section 3.1 "266 loans fcresults='3rd Party'" note
-- ============================================================
SELECT
  fcresults,
  COUNT(*)                                       AS loan_count,
  ROUND(COUNT(*) * 100.0 /
    (SELECT COUNT(*) FROM newrez.portnewrezfc WHERE activefcflag = 1
       AND dataasof = (SELECT MAX(dataasof) FROM newrez.portnewrezfc)), 1
  )                                              AS pct_of_active_fcl
FROM newrez.portnewrezfc
WHERE activefcflag = 1
  AND dataasof = (SELECT MAX(dataasof) FROM newrez.portnewrezfc)
  AND fcresults IS NOT NULL
  AND fcresults != ''
GROUP BY fcresults
ORDER BY loan_count DESC;
```

---

#### SQL-3 — Q9 Data Quality Anomaly Verification (fcsaleamount > fcsalehelddate)

> **Document coverage**: Section 8 Q9  
> **Source table**: `newrez.portnewrezfc`

```sql
-- ============================================================
-- SQL-3: Verify Q9 — fcsaleamount fill rate higher than fcsalehelddate
-- Source table: newrez.portnewrezfc
-- Produces: Section 8 Q9 analysis data
-- ============================================================
SELECT
  SUM(fcsaleamount IS NOT NULL)                                     AS has_sale_amount,
  SUM(fcsalehelddate IS NOT NULL)                                   AS has_held_date,
  -- Has amount but no held date: the anomaly core
  SUM(fcsaleamount IS NOT NULL AND fcsalehelddate IS NULL)          AS amount_without_held_date,
  -- Both present: normal completed sale
  SUM(fcsaleamount IS NOT NULL AND fcsalehelddate IS NOT NULL)      AS both_present,
  -- Further inspect fcresults
  SUM(fcsaleamount IS NOT NULL AND fcresults IS NOT NULL AND fcresults != '') AS amount_with_results
FROM newrez.portnewrezfc
WHERE activefcflag = 1
  AND dataasof = (SELECT MAX(dataasof) FROM newrez.portnewrezfc);
```

---

### B.2 Sample Loan Queries

Use these to verify **field mapping logic and end-to-end loan validation**. Replace `loanid` to query any loan.

---

#### SQL-4 — Query Specified Loan's Newrez Raw Fields

> **Document coverage**: Appendix A.A (loanid=7727000672), Appendix A.B Newrez-side fields (loanid=7727000088), Section 3.7 SMS Days live calculation verification  
> **Source table**: `newrez.portnewrezfc`  
> Change `WHERE loanid IN (...)` to query any loan

```sql
-- ============================================================
-- SQL-4: Query specified loan's Newrez FCL fields (replace loanid)
-- Source table: newrez.portnewrezfc
-- Produces: Appendix A.A (loanid=7727000672) / A.B Newrez-side fields
--           Section 3.7 SMS Days live recalculation verification
-- ── Replace loanid below with the loan you want to query ─────
-- ============================================================
SELECT
  loanid,
  -- Timeline dates
  demandsentdate, demandexpirationdate,
  fcsetupdate, fcreferraldate,
  firstlegaldate, servicecompletedate,
  fcjudgmenthearingscheduled, fcjudgmententered,
  fcscheduledsaledate, fcsalehelddate,
  dtdeedrecorded, fcremovaldate,
  -- Status / result
  fcstage, currentmilestone, activefcflag,
  fcresults, fcremovaldesc,
  lastfcstepcompleted, lastfcstepcompleteddate,
  -- Identifier / attorney
  shellpointloanid, fcfirm, judicial, fccontestedflag,
  -- Bid / amount
  fcbidamount, fcapprbidprice, fcsaleamount,
  -- FCL days (use with dataasof to verify live recalculation logic)
  smsdaysinfc, daysinfc, dataasof,
  -- Hold slots (current snapshot — 3 slots)
  fchold1description, fchold1startdate, fchold1enddate, fchold1projectedenddate,
  fchold2description, fchold2startdate, fchold2enddate, fchold2projectedenddate,
  fchold3description, fchold3startdate, fchold3enddate, fchold3projectedenddate
FROM newrez.portnewrezfc
WHERE loanid IN (7727000672, 7727000088);   -- add or replace loanid as needed
```

---

#### SQL-5 — BPS Hold History

> **Document coverage**: Section 4 Hold history architecture, Appendix A.B Hold panel (7 records)  
> **Source table**: `bpms_dev.sync_loan_foreclosure_hold`  
> Each Hold change appends a new row (no overwrite) — contrast with Newrez's 3 fixed Hold slots

```sql
-- ============================================================
-- SQL-5: BPS Hold full history (each change appends a new row)
-- Source table: bpms_dev.sync_loan_foreclosure_hold
-- Produces: Section 4 live verification / Appendix A.B Hold panel 7 records
-- ── Illustrates Newrez 3 Hold slots vs BPS full audit history ──
-- ============================================================
SELECT
  loanid,
  description,
  description_start_date,
  description_end_date       -- NULL means this Hold is still active
FROM bpms_dev.sync_loan_foreclosure_hold
WHERE loanid = 7727000088    -- replace with any loanid
ORDER BY description_start_date;
```

---

#### SQL-6 — BPS Loss Mitigation History

> **Document coverage**: Section 5 LM panel data, Appendix A.B LM panel (9 records)  
> **Source table**: `bpms_dev.sync_loan_foreclosure_loss_mitigation`  
> Newrez numeric codes (lmdeal, lmprogram, etc.) have been decoded to text by the ETL

```sql
-- ============================================================
-- SQL-6: BPS LM Cycle full history (one row per cycle)
-- Source table: bpms_dev.sync_loan_foreclosure_loss_mitigation
-- Produces: Section 5 live data / Appendix A.B LM panel 9 records
-- ── Newrez numeric codes (lmdeal, lmprogram) decoded to text by ETL ──
-- ============================================================
SELECT
  loanid,
  deal, program, lmc_status,
  cycle_opened_date,
  cycle_closed_date,         -- NULL means this LM cycle is still active
  final_disposition,
  denialreason
FROM bpms_dev.sync_loan_foreclosure_loss_mitigation
WHERE loanid = 7727000088    -- replace with any loanid
ORDER BY cycle_opened_date;
```

---

#### SQL-7 — Confirm No Bankruptcy Records

> **Document coverage**: Appendix A.B Bankruptcy panel "No Rows To Show"  
> **Source table**: `bpms_dev.sync_loan_foreclosure_bankruptcy`

```sql
-- ============================================================
-- SQL-7: Check whether a loan has any bankruptcy records
-- Source table: bpms_dev.sync_loan_foreclosure_bankruptcy
-- Produces: Appendix A.B Bankruptcy panel "No Rows To Show" confirmation
-- ============================================================
SELECT
  loanid,
  COUNT(*) AS bk_record_count
FROM bpms_dev.sync_loan_foreclosure_bankruptcy
WHERE loanid = 7727000088    -- replace with any loanid
GROUP BY loanid;
-- Expected: no rows (0 rows) = loan has no bankruptcy records
```

---

#### SQL-8 — BPS sync_loan_foreclosure target/actual/var Fields

> **Document coverage**: Section 3.2 (target_* target days), Section 3.3 (actual_* actual days), Section 3.4 (var_* variance days)  
> **Source table**: `bpms_dev.sync_loan_foreclosure` (BPS master FCL table — not a Newrez table)  
> All three field groups are BPS-internal; replace loanid to query any loan

```sql
-- ============================================================
-- SQL-8: BPS sync_loan_foreclosure — target / actual / var fields
-- Source table: bpms_dev.sync_loan_foreclosure
-- Produces: Section 3.2 target_* / Section 3.3 actual_* / Section 3.4 var_*
-- ── All BPS-internal fields; no Newrez raw data involved ─────
-- ── Replace loanid to query any loan ─────────────────────────
-- ============================================================
SELECT
  loanid,
  -- ── target_* days (Section 3.2 — system-configured per state/judicial) ─
  target_notice_of_intent_days, target_notice_of_intent_expired_days,
  target_approved_for_referral_days, target_referred_to_attorney_days,
  target_referred_to_foreclosure_days, target_first_legal_days,
  target_service_days, target_publication_days,
  target_judgement_days, target_sale_date_set_days, target_total,
  -- ── actual_* days (Section 3.3 — computed from Newrez date endpoints) ──
  actual_notice_of_intent_days, actual_notice_of_intent_expire_days,
  actual_approved_for_referral_days, actual_referred_to_attorney_days,
  actual_referred_to_foreclosure_days, actual_first_legal_days,
  actual_service_days, actual_publication_days,
  actual_judgement_days, actual_sale_date_set_days, actual_total,
  -- ── var_* days (Section 3.4 — actual minus target) ───────────
  -- positive = behind target; negative = ahead of schedule; zero = on target
  var_notice_of_intent_days, var_notice_of_intent_expire_days,
  var_approved_for_referral_days, var_referred_to_attorney_days,
  var_referred_to_foreclosure_days, var_first_legal_days,
  var_service_days, var_publication_days,
  var_judgement_days, var_sale_date_set_days, var_total
FROM bpms_dev.sync_loan_foreclosure
WHERE loanid IN (7727000672, 7727000088);   -- replace with any loanid
```

#### SQL-9 — sync_fcl_stage_info Stage Distribution (Section 7 Data Range Verification)

```sql
-- ============================================================
-- SQL-9: sync_fcl_stage_info stage distribution
-- Source table: bpms_dev.sync_fcl_stage_info
-- Produces: Section 7 loan count by BPS stage
--           (reproduces Aggregation Overview page totals)
-- ── One row per active FCL loan; grouped by stage ────────────
-- ── Total row count should match SQL-1 total_active_fcl (≈13,321) ──
-- ============================================================
SELECT
  stage                          AS bps_stage,
  COUNT(*)                       AS loan_count,
  ROUND(COUNT(*) * 100.0 /
    (SELECT COUNT(*) FROM bpms_dev.sync_fcl_stage_info
     WHERE fctrdt = (SELECT MAX(fctrdt) FROM bpms_dev.sync_fcl_stage_info)), 1
  )                              AS pct_of_total
FROM bpms_dev.sync_fcl_stage_info
WHERE fctrdt = (SELECT MAX(fctrdt) FROM bpms_dev.sync_fcl_stage_info)
GROUP BY stage
ORDER BY loan_count DESC;
-- Expected stage values: NOI/Demand Letter / NOI (Approved for Referral) / Referral /
--                        First Legal / Service / Publication /
--                        Upcoming Judgement / Upcoming FC Sales
```

#### SQL-10 — Stage Classification Condition Verification (Full Pipeline — Three Bug Fixes Applied, MCP-Verified)

```sql
-- ============================================================
-- SQL-10: Verify stage classification conditions (full pipeline — MCP-verified)
-- Source tables: bpms_dev.sync_fcl_stage_info + newrez.portnewrezfc
-- Produces: current-snapshot stage status for all Newrez loans with dual-side field comparison
-- ── Three bug fixes discovered via MCP live execution ──────────────────────────────
-- ①  COLLATE utf8mb4_general_ci: bpms_dev uses utf8mb4_general_ci, newrez uses
--     utf8mb4_0900_ai_ci — without COLLATE, MySQL raises SQL Error [1267]
-- ②  AND p.dataasof = s.fctrdt: both tables are daily snapshots; loanid-only JOIN
--     produces 682 × 55 = 37,510 rows per loan (Cartesian product)
-- ③  fctrdt = MAX(fctrdt): filter to current snapshot only (Newrez: 2026-03-13, 26 loans)
-- ============================================================
SELECT
  s.loanid,
  s.stage                    AS bps_stage,        -- DB stores all-caps code (SALE/JUDGEMENT/SERVICE etc.)
  s.fctrdt                   AS snapshot_date,     -- snapshot date (confirms data time point)
  s.servicer,
  s.state,
  s.judicial,
  -- ── BPS output fields (directly displayed on BPS page; read the column group matching the stage) ──
  s.sale_start_date,              -- SALE (Upcoming FC Sales): stage date
  s.to_sale_days,                 -- SALE: Days to Sale
  s.judgement_start_date,         -- JUDGEMENT (Upcoming Judgement): stage date
  s.to_judgement_days,            -- JUDGEMENT: Days to Judgement
  s.service_start_date,           -- SERVICE (Service): stage date
  s.service_stage_days,           -- SERVICE: Days in Stage
  s.first_legal_start_date,       -- FIRST_LEGAL (First Legal): stage date
  s.first_legal_stage_days,       -- FIRST_LEGAL: Days in Stage
  s.referral_start_date,          -- REFERRAL (Referral): stage date
  s.referral_stage_days,          -- REFERRAL: Days in Stage
  -- ── Newrez source fields (ETL classification conditions, highest to lowest priority) ──
  p.fcscheduledsaledate,          -- Priority 1: IS NOT NULL → SALE
  p.fcjudgmenthearingscheduled,   -- Priority 2: IS NOT NULL → JUDGEMENT
  p.servicecompletedate,          -- Priority 4: IS NOT NULL → SERVICE
  p.firstlegaldate,               -- Priority 5: IS NOT NULL → FIRST_LEGAL
  p.fcreferraldate,               -- Priority 6: IS NOT NULL → REFERRAL
  p.demandsentdate,               -- Priority 7: IS NOT NULL → DEMAND
  -- ── Supporting reference fields ────────────────────────────────────────────────────
  p.fcsalehelddate,               -- Non-null indicates sale has occurred
  p.fcjudgmententered             -- Judgment completion date
FROM bpms_dev.sync_fcl_stage_info s
JOIN newrez.portnewrezfc p
  ON s.loanid = p.loanid COLLATE utf8mb4_general_ci  -- ① collation fix
  AND p.dataasof = s.fctrdt                           -- ② date match to prevent Cartesian product
WHERE s.servicer = 'Newrez'                           -- replace with other servicer or remove filter
  AND s.fctrdt = (                                    -- ③ current snapshot only
      SELECT MAX(fctrdt)
      FROM bpms_dev.sync_fcl_stage_info
      WHERE servicer = 'Newrez'
  )
ORDER BY s.stage, s.loanid;
-- Expected patterns (MCP-verified: 26 rows, no duplicates):
-- SALE rows:        fcscheduledsaledate IS NOT NULL, sale_start_date = fcscheduledsaledate ✓
-- JUDGEMENT rows:   fcjudgmenthearingscheduled IS NOT NULL, fcscheduledsaledate IS NULL ✓
-- SERVICE rows:     servicecompletedate IS NOT NULL, service_start_date = servicecompletedate ✓
-- FIRST_LEGAL rows: firstlegaldate IS NOT NULL, servicecompletedate IS NULL ✓
-- REFERRAL rows:    fcreferraldate IS NOT NULL, firstlegaldate IS NULL ✓
```

#### SQL-11 — LM Field Value Distribution (Verify Section 5 Enumerated Values)

```sql
-- ============================================================
-- SQL-11: LM field value distribution (validate Section 5 enums)
-- Source table: bpms_dev.sync_loan_foreclosure_loss_mitigation
-- Output: actual deal / program / lmc_status / final_disposition
--         values with cycle counts — confirms ETL decode accuracy
-- ============================================================
SELECT
  deal,
  program,
  lmc_status,
  final_disposition,
  COUNT(*)  AS cycle_count
FROM bpms_dev.sync_loan_foreclosure_loss_mitigation
GROUP BY deal, program, lmc_status, final_disposition
ORDER BY deal, COUNT(*) DESC;
```

#### SQL-12 — Reproduce Time Line Tab View (Current Newrez Snapshot, with demand_start_date Comparison Column)

```sql
-- ============================================================
-- SQL-12: Reproduce Time Line Tab view (current Newrez snapshot)
-- Source table: bpms_dev.sync_fcl_stage_info
-- Output: all 12 UI columns + demand_start_date comparison column
--         (explains why "NOI Date 1" is always blank for Newrez:
--          noi_start_date is NULL; demandsentdate → demand_start_date
--          but demand_start_date is not shown in the NOI Date column)
-- ── MCP-verified: 26 rows, matches Image #12 screenshot ────
-- ============================================================
SELECT
  loanid,
  `group`,
  servicer,
  state,
  judicial,
  noi_start_date         AS `NOI Date 1`,               -- Always NULL for Newrez
  demand_start_date      AS `Demand Date (comparison)`,  -- Newrez demandsentdate → this field; 24/26 populated but NOT shown as NOI Date
  referral_start_date    AS `Referral Date 2`,
  first_legal_start_date AS `First Legal Date 3`,
  service_start_date     AS `Service Date 4`,
  publication_start_date AS `Publication Date 5`,        -- Always NULL for Newrez
  judgement_start_date   AS `Judgement Date 6`,          -- maps to fcjudgmenthearingscheduled (hearing scheduled date); fcjudgmententered is a different field
  sale_start_date        AS `Sale Date 7`
FROM bpms_dev.sync_fcl_stage_info
WHERE servicer = 'Newrez'
  AND fctrdt = (
      SELECT MAX(fctrdt)
      FROM bpms_dev.sync_fcl_stage_info
      WHERE servicer = 'Newrez'
  )
ORDER BY `group`, loanid;
```
