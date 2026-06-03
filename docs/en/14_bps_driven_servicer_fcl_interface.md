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
| 2026-06-02 | AI Agent (Claude Sonnet 4.6) | v17 | Source-table corrections (information_schema verified): ① `delinquency_status` source annotated as `portnewrezgeneral` (not portnewrezfc); ② `foreclosure_flag` removed the false "`portnewrezfc.fcl_flag` exists" claim — Newrez has no such column; FCL active status is actually `activefcflag`; ③ `state` source corrected to `portnewrezprop.propertystate` (portnewrezfc has no state column); also fixed 14_servicer_fcl_field_spec.xlsx Field Spec col4/verify-SQL (incl. lm_flag→portnewrezlm, lien_position→portnewrezgeneral.lienposition); zh/en synced | DB verified 2026-06-02 |
| 2026-06-02 | AI Agent (Claude Sonnet 4.6) | v18 | Section 2.0 added a `days360(nextduedate, dataasof)` calculation footnote (30/360 day-count formula, argument order, DPD meaning, C/D30/D60/D90/D120P bucketing, source `PrefectFlow/flow/remit_validation/utils.py:14-21`); Excel synced with a cell comment + a days360 glossary entry; zh/en synced | source-verified in PrefectFlow |
| 2026-06-02 | AI Agent (Claude Sonnet 4.6) | v19 | Section 4.1 — the 3 `⚠️ Code behavior under investigation` BK fields resolved via DB verification: ① `bk_status` is decoded to text by BPS (1→Active·2→Discharged·3→Dismissed·4→Closed·5→ReliefGranted); ② `bk_legal_status` actually comes from `portnewrezgeneral.legalstatus` text (FCBU/BK13/BK7…), `bkstage` was a misattribution; ③ `mfr_hearing_results` — BPS mfr_status empty in dev (0/64). Disproves the earlier "BK integer codes not decoded / BPS stores numbers" assumption; Excel + doc 13 Q7/Section 6 + data dictionary corrected too | DB-verified 2026-06-02 |
| 2026-06-02 | AI Agent (Claude Sonnet 4.6) | v20 | Corrected `lm_flag` Newrez status: DB shows `activelmflag` 100% filled at latest snapshot (5052/5052, 0:5018·1:34, no nulls) — the prior "🟡 Partially provided (no type/dates)" was wrong (flag is fully provided → ✅; type/dates are separate fields lm_type/lm_start_date/lm_end_date). Synced to Excel + MD; added a "doc 14 MD⇄Excel sync" rule to project CLAUDE.md. (zh counterpart = zh v21) | DB-verified 2026-06-02 |
| 2026-06-02 | AI Agent (Claude Opus 4.8) | v18 | Added "📖 Regulatory terms" footnote after the Section 3 LM business-meaning table: explains CFPB / Reg X / RESPA / 12 CFR 1024.40 (SPOC) / 1024.41 / Imminent Default; full entries also added to doc 10 "Category H — Regulatory/Compliance Terms"; zh/en synced | doc 10 v3 |

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

| Standard Interface Field | Newrez Raw Field | Type | Priority | Allowed Values / Format | BPS System Function | Newrez Status |
|---|---|---|---|---|---|---|
| `delinquency_status` | `delinquency_status_mba` (from `portnewrezgeneral`) | VARCHAR ENUM | **P0** | MBA standard text enum (see allowed values table below) | ETL entry filter; foundation for FCL/LM/BK status identification; `sync_fcl_stage_info` D120P secondary filter trigger; numeric strings (`'29.0'`) are prohibited | ✅ `portnewrezgeneral.delinquency_status_mba` provided (12K+ FCL rows) |
| `next_payment_due_date` | `nextduedate` (from `portnewrezpmt`) | DATE | **P0** | YYYY-MM-DD | Fallback basis for days360 calculation; ETL derives DPD via `days360(nextduedate, dataasof)` | ✅ `portnewrezpmt.nextduedate` provided; **100% fill rate** for active FCL loans (MCP-verified) |
| `days_past_due` | *(none; ETL-derived)* | INTEGER | P1 | 0–999 positive integer | Cross-validates `delinquency_status`; ETL calculates via `days360(nextduedate, dataasof)`; Newrez has `portnewrezgeneral.mbadelinquency` (**months** past due, not days, integer) for reference | N/A Derived field (Newrez has no native DPD days field; `mbadelinquency` = months past due, cannot be used directly as DPD days) |
| `foreclosure_flag` | *(no `fcl_flag` in Newrez; see `activefcflag`)* | CHAR(1) | **P0** | `Y` / `N` | Explicit FCL active status flag; corresponds to BPS `active_fcl_flag` (0/1 Newrez-specific); `Y` = foreclosure legal proceedings formally initiated | ❌ Newrez has **no standalone `fcl_flag` column** (DB-verified; no portnewrez* table contains it); FCL active status is expressed by `portnewrezfc.activefcflag` (see `active_fcl_flag`) or derived from `delinquency_status='Foreclosure'` |
| `lm_flag` | `activelmflag` | CHAR(1) | **P0** | `Y` / `N` | Top-level LM active flag; ETL uses this to route loans into LM processing; basis for BPS LM Cycle panel data sourcing | ✅ Provided (`activelmflag`, 100% filled at latest snapshot: 0/1, no nulls; observed 0:5018·1:34). Expressed as 0/1 (map to Y/N); cycle-table-level flag — LM type/dates are separate fields (`lm_type` / `lm_start_date` / `lm_end_date`) |
| `lm_type` | *(no field)* | VARCHAR ENUM | P1 | Newrez `lmdeal`-decoded deal (8): `Evaluation` / `Modification` / `Forbearance` / `Payment Plan` / `Deferment` / `Short Sale` / `DIL` / `Payoff` (= `lm_deal`; Trial Period Plan is a program-level value under Modification, not a deal) | Standardized LM type; same concept as `lm_deal` (Newrez `lmdeal`-decoded) | ❌ Newrez provides no standard `lm_type` text; supplied as `lmdeal` int code, ETL-decoded to the 8 deals above (see `lm_deal`) |
| `lm_start_date` | `dealstartdate` | DATE | P1 | YYYY-MM-DD | LM program start date; corresponds to Section 3.1 `lm_cycle_open_date` | 🟡 Cycle-level `dealstartdate` available |
| `lm_end_date` | `lmremovaldate` | DATE | P1 | YYYY-MM-DD | LM program expiration date; corresponds to Section 3.1 `lm_cycle_close_date` | 🟡 Cycle-level `lmremovaldate` available |
| `hold_flag` | *(no top-level field)* | CHAR(1) | P1 | `Y` / `N` | Top-level flag for whether FCL is in Hold (paused) status; corresponds to the Section 2.4 slot fields | ❌ No independent top-level flag (`fchold1startdate IS NOT NULL` can be derived, but not a formal flag) |
| `hold_reason` | `fchold1description` | VARCHAR ENUM | P1 | `BK`/`LM`/`HUD`/`Covid`/`Other` | Standardized hold reason enum; Section 2.4 `hold_1_description` is its free-text version | ❌ Newrez provides free text (e.g., "Court Delay"), no standard enum |
| `reo_flag` | *(no field)* | CHAR(1) | **P0** | `Y` / `N` | Explicit flag that foreclosure is complete and property now owned by lender | ❌ Not provided |
| `reo_acquisition_date` | *(no field)* | DATE | P1 | YYYY-MM-DD | Date property was formally transferred to lender as REO | ❌ Not provided |

**Business Meaning / Calculation Logic**

| Standard Interface Field | Business Meaning / Calculation Logic |
|---|---|
| `delinquency_status` | MBA standard delinquency status text enum; the core "Dimension A" field in the 4-dimension model; Servicers must use enum text (numeric DPD values forbidden); FCL status identification (`Foreclosure` enum), BK identification (`Bankruptcy` enum), and REO identification all depend on this field |
| `next_payment_due_date` | Next payment due date; source: `newrez.portnewrezpmt.nextduedate` (DATE, 100% fill rate for active FCL loans); ETL calculates DPD via `days360(nextduedate, dataasof)`; primary fallback source when `delinquency_status` is missing or malformed |
| `days_past_due` | Numeric days past due; Newrez has **no native DPD days field** — ETL calculates via `days360(nextduedate, dataasof)`; `portnewrezgeneral.mbadelinquency` stores **months** past due (integer, e.g., 13 = 13 months delinquent), which cannot be used directly as DPD days; cross-validates `delinquency_status` and serves as substitute when format errors occur |
| `foreclosure_flag` | Explicit Y/N flag whether FCL legal proceedings have formally commenced; **must never be derived from `days_past_due`** (120+ DPD ≠ foreclosure; FCL requires an explicit flag from Servicer); corresponds to BPS `active_fcl_flag` (0=N / 1=Y) |
| `lm_flag` | Top-level Y/N flag whether LM program is currently active; determines whether ETL reads LM detail fields; independent of FCL dimension (can coexist with FCL) |
| `lm_type` | Standard LM type enum; affects system processing logic (Forbearance = temporary, Modification = permanent); Newrez supplies via `lmdeal` numeric code requiring ETL decode mapping |
| `lm_start_date` | LM program start date (top-level summary); Newrez provides via LM cycle table (`portnewrezlm`) as `dealstartdate` |
| `lm_end_date` | LM program expiration date (top-level summary); Newrez provides via LM cycle table as `lmremovaldate`; whether it's renewed at expiry is a critical decision point |
| `hold_flag` | Top-level flag whether FCL is paused (Hold); derivable from Newrez `fchold1startdate IS NOT NULL`, but not a formal flag; Servicers should be explicitly asked for a dedicated flag |
| `hold_reason` | Standardized hold reason enum (`BK`/`LM`/`HUD`/`Covid`/`Other`); Newrez provides free text (e.g., "Loss Mitigation Workout"), not standardized |
| `reo_flag` | Explicit flag that foreclosure is complete and property is lender-owned; Newrez currently lacks a dedicated REO flag; must be derived from `fcresults` or `delinquency_status='REO'` |
| `reo_acquisition_date` | Date property was transferred to lender as REO; affects REO holding period calculation; Newrez does not provide |

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
> - **Source**: `PrefectFlow/flow/remit_validation/utils.py:14-21` (Python definition); SQL usage in `basic_data_pool_config.py`. Full glossary entry in **doc 10**.

---

### 2.1 Loan Identification and Entry Filter Fields (P0 — Required)

These fields are **prerequisites for BPS entry**; absence of any one will cause the entire loan record to be rejected.

| Standard Interface Field | Newrez Raw Field | Type | Priority | Format | BPS Panel / Function | Newrez Status |
|---|---|---|---|---|---|---|
| `loan_id` | `loanid` | VARCHAR | **P0** | Numeric string; global primary key | All panels; BPS global JOIN key | ✅ 100% |
| `servicer_loan_id` | `shellpointloanid` | VARCHAR | **P0** | Servicer internal number | FCL Summary `summary_servicer_number` | ✅ 100% |
| `data_as_of_date` | `dataasof` | DATE | **P0** | YYYY-MM-DD | Snapshot date; basis for real-time day recalculation (SMS/Days in FCL) | ✅ 100% |
| `state` | `propertystate` (from `portnewrezprop`) | CHAR(2) | **P0** | US state code (uppercase) | Stage grouping; target days configuration | ✅ 100% (`portnewrezprop.propertystate`, DB-verified) |
| `judicial_flag` | `judicial` | TINYINT | **P0** | 1=Judicial / 0=Non-Judicial | FCL Summary Judicial type; stage routing | ✅ 100% |
| `active_fcl_flag` | `activefcflag` | TINYINT | **P0** | 1=in active foreclosure / 0=not in active foreclosure (completed OR withdrawn/reinstated/paid; BPS "Closed Foreclosure"); NULL conservatively treated as 1 | BPS entry condition; historical NULLs require NULL-safe handling (see doc 13 Q3) | ✅ 100% (incl. historical NULLs) |
| `fcl_referral_date` | `fcreferraldate` | DATE | **P0** | YYYY-MM-DD | **BPS core entry prerequisite**; `timeline_referred_to_foreclosure_date`; FCL timeline anchor | ✅ 100% |

**Business Meaning / Calculation Logic**

| Standard Interface Field | Business Meaning / Calculation Logic |
|---|---|
| `loan_id` | Globally unique numeric loan identifier; serves as the JOIN key across all BPS panels and tables |
| `servicer_loan_id` | Servicer's internal loan number; a different dimension from loan_id; used for bidirectional cross-system reconciliation |
| `data_as_of_date` | Snapshot cutoff date for this data batch (typically 1–2 days behind real time); BPS real-time correction formula: `smsdaysinfc + DATEDIFF(today NY, dataasof)` |
| `state` | Two-letter uppercase state code where the property is located; determines applicable foreclosure law (Judicial/Non-Judicial) and BPS target day configurations per stage |
| `judicial_flag` | Whether the foreclosure requires a court judgment before auction; affects JUDGEMENT stage routing (Judicial states only) and timeline field meanings |
| `active_fcl_flag` | Whether the loan is in an active foreclosure process; 1=active, 0=not in active foreclosure (BPS "Closed Foreclosure" — includes completed AND withdrawn/reinstated/paid, **not necessarily "completed"**); historical NULLs conservatively treated as active (see doc 13 Q3 Technical Detail) |
| `fcl_referral_date` | Date the lender formally transferred the foreclosure case to an attorney firm; **BPS entry core condition** (must be non-null to be included); legal start of the FCL timeline |

### 2.2 FCL Status Fields (P1 — FCL Summary Panel Core)

| Standard Interface Field | Newrez Raw Field | Type | Priority | Format | BPS Panel / Function | Newrez Status |
|---|---|---|---|---|---|---|
| `fcl_stage` | `fcstage` | VARCHAR | P1 | Text (Newrez internal stage description) | FCL Summary `summary_current_step` (**fallback**; used when `currentmilestone` is null) | ✅ 99.5% |
| `current_milestone` | `currentmilestone` | VARCHAR | P1 | BPS milestone label text | FCL Summary `summary_current_step` (**highest priority**) | ⚠️ 62.7% (fill rate low) |
| `last_completed_step` | `lastfcstepcompleted` | VARCHAR | P1 | Text | FCL Summary `summary_last_step_completed` | ✅ 99.5% |
| `last_completed_step_date` | `lastfcstepcompleteddate` | DATE | P1 | YYYY-MM-DD | FCL Summary `summary_last_step_completed_date` | ✅ 99.5% |
| `fcl_results` | `fcresults` | VARCHAR | P1 | Text; typical values: `3rd Party` / `REO` | FCL Summary (completed loans); `timeline_third_party_sold_date_date` trigger logic | ⚠️ 2.1% (completed loans only) |
| `attorney_firm` | `fcfirm` | VARCHAR | P1 | Text | FCL Summary `summary_foreclosure_attorney` / `summary_firm` | ✅ 100% |
| `contested_flag` | `fccontestedflag` | TINYINT | P1 | 0/1 | FCL Summary `summary_contested_litigation` | ✅ 100% |
| `sms_days_in_fcl` | `smsdaysinfc` | INTEGER | P1 | Positive integer (Servicer-perspective days, as of dataasof) | FCL Summary `summary_sms_days_in_fcl` (BPS adds real-time lag correction) | ✅ 100% |
| `days_in_fcl` | `daysinfc` | INTEGER | P1 | Positive integer (investor-perspective days) | FCL Summary `summary_days_in_fcl` (same real-time correction) | ✅ 100% |

**Business Meaning / Calculation Logic**

| Standard Interface Field | Business Meaning / Calculation Logic |
|---|---|
| `fcl_stage` | Newrez's internal current workflow step text (e.g., "Pre-Sale Review"); `summary_current_step` **fallback** display field (used when `currentmilestone` is null) |
| `current_milestone` | BPS milestone label (written by BPS internal workflow or operations); `summary_current_step` **highest priority** display field |
| `last_completed_step` | Most recently completed foreclosure processing step text (e.g., "Motion for Judgment Sent to Court"); used by operations to track progress |
| `last_completed_step_date` | Completion date of the above step |
| `fcl_results` | Final FCL disposition result (populated only for completed loans); typical values: `3rd Party` (third-party purchase) / `REO` (lender-owned); `fcresults='3rd Party'` triggers the `timeline_third_party_sold_date_date` logic |
| `attorney_firm` | Full name of the law firm handling this foreclosure case |
| `contested_flag` | Whether contested litigation exists (borrower filed a legal objection); 1=contested / 0=not contested |
| `servicer_days_in_fcl` | Servicer-perspective days in FCL — counted from the servicer FCL setup date (`fcsetupdate`); Newrez/SMS=Shellpoint implements this as native `smsdaysinfc` (ETL alias `svc_days_infc`). BPS real-time correction: `smsdaysinfc + DATEDIFF(today NY, dataasof)`; ≤ days_in_fcl. (Standard field name is servicer-neutral; `smsdaysinfc`/`summary_sms_days_in_fcl` are the Newrez/BPS column names.) |
| `days_in_fcl` | Investor / full-timeline days in FCL — counted from the referral date (`fcreferraldate`); differs from servicer_days_in_fcl in start date (referral vs setup), so days_in_fcl ≥ servicer_days_in_fcl; BPS applies same real-time correction: `daysinfc + DATEDIFF(today NY, dataasof)` |

### 2.3 FCL Timeline Fields (P0/P1/P2 — Timeline Panel + Aggregate Time Line Tab)

> **Note**: Fields in this section are consumed by two BPS display locations:
> 1. **Loan detail page FCL Milestone timeline**: `timeline_*` fields (19 fields)
> 2. **Aggregate overview Time Line Tab**: `{stage}_start_date` fields (7 columns; see Section 7)

| Standard Interface Field | Newrez Raw Field | Type | Priority | BPS Panel / Field | Newrez Status |
|---|---|---|---|---|---|
| `noi_date` | *(none; Newrez conflates with `demandsentdate`)* | DATE | P1 | Milestone NOI Date; `timeline_notice_of_intent_date`; Time Line Tab `noi_start_date` | ❌ Newrez does not provide separately (BPS currently substitutes `demandsentdate` as interim measure; see note below) |
| `demand_sent_date` | `demandsentdate` | DATE | P1 | Stage DEMAND grouping trigger; `demand_start_date` (aggregate page); if Servicer does not provide a separate `noi_date`, BPS uses this field as a substitute for `timeline_notice_of_intent_date` | ✅ 85.9% (14.1% missing; see doc 13 Q5) |
| `demand_expiration_date` | `demandexpirationdate` | DATE | P1 | `timeline_notice_of_intent_end_date`; `actual_notice_of_intent_days` calculation | ✅ 85.7% |
| `fcl_setup_date` | `fcsetupdate` | DATE | P1 | `timeline_approved_for_referral_date`; Newrez typically same date as `fcreferraldate` | ✅ 100% |
| `first_legal_date` | `firstlegaldate` | DATE | P1 | Milestone First Legal; `timeline_first_legal_date`; Stage FIRST_LEGAL trigger | ⚠️ 57.6% |
| `service_complete_date` | `servicecompletedate` | DATE | P1 | Milestone Service; `timeline_service_date`; Stage SERVICE trigger | ⚠️ 28.9% |
| `publication_date` | *(no corresponding field)* | DATE | P2 | Milestone Publication; `timeline_publication_date`; Stage PUBLICATION trigger | ❌ 0% (Newrez does not provide; see doc 13 Q1) |
| `title_received_date` | `titlereceiveddate` | DATE | P2 | `timeline_title_report_received_date` | ❌ 0% (Newrez does not provide; see doc 13 Q8) |
| `title_clear_date` | `titlecleardate` | DATE | P2 | `timeline_preliminary_title_cleared_date` / `timeline_final_title_cleared_date` | ❌ 0% (Newrez does not provide; see doc 13 Q8) |
| `judgement_hearing_scheduled` | `fcjudgmenthearingscheduled` | DATE | P1 | Milestone Judgement Date; **`timeline_judgement_date` / `judgement_start_date`**; Stage JUDGEMENT trigger (priority 2) | ✅ 11.9% (Judicial states only) |
| `judgement_entered_date` | `fcjudgmententered` | DATE | P1 | ETL intermediate table `fcjudgment_end_date`; used for `actual_judgement_hearing_set_days` calculation (`fcjudgmententered` − `fcjudgmenthearingscheduled`); **NOT a direct BPS Time Line Tab display field** | ✅ 7.9% (Judicial states only) |
| `scheduled_sale_date` | `fcscheduledsaledate` | DATE | P1 | Milestone Sale; `timeline_sale_date_projected_date`; `sale_start_date`; **Stage SALE trigger (highest priority 1)** | ✅ 18.2% |
| `sale_held_date` | `fcsalehelddate` | DATE | P1 | `timeline_sale_date_held_date`; 3rd Party Sale logic trigger | ✅ 2.1% (completed loans) |
| `deed_recorded_date` | `dtdeedrecorded` | DATE | P2 | `timeline_foreclosure_completed_date` (priority; COALESCE first option) | ✅ ~0% (completed loans) |
| `fcl_removal_date` | `fcremovaldate` | DATE | P1 | `timeline_foreclosure_completed_date` (fallback; COALESCE second option) | ✅ ~2.0% (completed loans) |
| `third_party_proceeds_date` | `fcl3rdpartyproceedsreceiveddate` | DATE | P2 | `timeline_third_party_proceeds_received_date` | ✅ ~0% (very few completed loans) |

**Business Meaning / Calculation Logic**

| Standard Interface Field | Business Meaning / Calculation Logic |
|---|---|
| `noi_date` | **Formal Notice of Intent to Foreclose** required by state law: Judicial states = mandatory pre-court notice (typically 30–45 days); Non-Judicial states = Notice of Default or equivalent. Conceptually distinct from `demand_sent_date` (payment demand letter) — some Servicers provide both dates separately; Newrez conflates the two using `demandsentdate`, which BPS currently substitutes into `timeline_notice_of_intent_date` as an interim measure |
| `demand_sent_date` | Pre-foreclosure **payment demand letter / default notice** requiring the borrower to cure arrears; may precede or coincide with the formal NOI; triggers BPS DEMAND Stage grouping (`demand_start_date`); Newrez uses this field for both purposes (interim handling, not the interface standard design) |
| `demand_expiration_date` | NOI / demand letter expiration date (foreclosure may proceed if unpaid after this date); calculation: `actual_notice_of_intent_days = demandexpirationdate − demandsentdate` |
| `fcl_setup_date` | FCL internal open date (BPS system case creation date); Newrez typically records the same date as `fcreferraldate` |
| `first_legal_date` | Date the foreclosure lawsuit was first filed with the court; typically null in Non-Judicial states (no court required); triggers FIRST_LEGAL Stage |
| `service_complete_date` | Date legal documents (summons/notice) were successfully served on the borrower; triggers SERVICE Stage |
| `publication_date` | Date the foreclosure notice was published in a newspaper / official channel (required step in Non-Judicial states); Newrez does not provide this field |
| `title_received_date` | Date the attorney firm received the title search report; Newrez does not provide this field |
| `title_clear_date` | Date the title search confirmed no unknown liens; applies to both preliminary and final title clearance stages; Newrez does not provide |
| `judgement_hearing_scheduled` | **Scheduled date** of the foreclosure judgment hearing / sale confirmation hearing (future planned event); Judicial states only; triggers JUDGEMENT Stage (priority 2) |
| `judgement_entered_date` | Date the court **formally entered** (recorded) the judgment (completed legal fact); calculation: `actual_judgement_hearing_set_days = fcjudgmententered − fcjudgmenthearingscheduled`; NOT a direct Time Line Tab display field (see doc 13 Q10/Q12) |
| `scheduled_sale_date` | Scheduled foreclosure auction date; any non-null value immediately triggers the **highest-priority SALE Stage**; updated dynamically as the process advances |
| `sale_held_date` | Date the foreclosure auction was actually held; combined with `fcresults` to determine whether it was a third-party purchase |
| `deed_recorded_date` | Date the deed was recorded (legal completion of foreclosure); first option in `COALESCE(dtdeedrecorded, fcremovaldate)` for `timeline_foreclosure_completed_date` |
| `fcl_removal_date` | Date the FCL process was cancelled or closed (borrower paid/LM succeeded/other reason); fallback second option in the COALESCE |
| `third_party_proceeds_date` | Date auction proceeds were received from the third-party buyer |

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

| Standard Interface Field | Newrez Raw Field | Type | Priority | BPS Panel / Function | Newrez Status |
|---|---|---|---|---|---|
| `hold_1_description` | `fchold1description` | VARCHAR | P1 | Hold panel `description` | ✅ 89.6% |
| `hold_1_start_date` | `fchold1startdate` | DATE | P1 | Hold panel `description_start_date` | ✅ (in sync with description) |
| `hold_1_end_date` | `fchold1enddate` | DATE | P1 | Hold panel `description_end_date` (NULL = still active) | ✅ |
| `hold_1_projected_end_date` | `fchold1projectedenddate` | DATE | P2 | `variance_estimated_hold_days` calculation (MAX(slot 1/2/3 projected end) − today) | ✅ |
| `hold_2_description` | `fchold2description` | VARCHAR | P1 | Same as slot 1 (slot 2) | ✅ 69.8% |
| `hold_2_start_date` | `fchold2startdate` | DATE | P1 | Same | ✅ |
| `hold_2_end_date` | `fchold2enddate` | DATE | P1 | Same | ✅ |
| `hold_2_projected_end_date` | `fchold2projectedenddate` | DATE | P2 | Same | ✅ |
| `hold_3_description` | `fchold3description` | VARCHAR | P1 | Same (slot 3) | ✅ 52.6% |
| `hold_3_start_date` | `fchold3startdate` | DATE | P1 | Same | ✅ |
| `hold_3_end_date` | `fchold3enddate` | DATE | P1 | Same | ✅ |
| `hold_3_projected_end_date` | `fchold3projectedenddate` | DATE | P2 | Same | ✅ |
| `hold_1_modified_date` | `holdmodified` | DATE | P2 | Hold slot 1 last modified date; tracks when this hold was last updated | ✅ 82.1% |
| `hold_2_modified_date` | `holdmodified2` | DATE | P2 | Hold slot 2 last modified date | ✅ 82.1% |
| `hold_3_modified_date` | `holdmodified3` | DATE | P2 | Hold slot 3 last modified date | ✅ 82.1% |

**Business Meaning / Calculation Logic**

| Standard Interface Field | Business Meaning / Calculation Logic |
|---|---|
| `hold_1_description` | Hold slot 1 reason text (e.g., "Loss Mitigation Workout" / "Court Delay"); free-form text; maps to BPS Hold panel Description column |
| `hold_1_start_date` | Hold 1 start date; also the BPS extraction filter condition (`fchold1startdate IS NOT NULL` required for ingestion) |
| `hold_1_end_date` | Hold 1 end date; NULL means this Hold is still active |
| `hold_1_projected_end_date` | Hold 1 projected end date; used in calculation: `variance_estimated_hold_days = MAX(slot1/2/3 projected) − today NY` |
| `hold_2_description` | Hold slot 2 reason text (used when multiple concurrent Holds exist in the same period) |
| `hold_2_start_date` | Hold 2 start date |
| `hold_2_end_date` | Hold 2 end date; NULL means still active |
| `hold_2_projected_end_date` | Hold 2 projected end date; participates in MAX calculation alongside slot 1 |
| `hold_3_description` | Hold slot 3 reason text (third concurrent Hold) |
| `hold_3_start_date` | Hold 3 start date |
| `hold_3_end_date` | Hold 3 end date; NULL means still active |
| `hold_3_projected_end_date` | Hold 3 projected end date; participates in MAX calculation alongside slots 1 and 2 |

> **Architecture note**: Newrez's 3 hold slots represent the **current snapshot** of active/recent holds. On each daily BPS sync, if any hold field changes, a new row is appended to `sync_loan_foreclosure_hold`, accumulating the complete Hold history (e.g., loanid=7727000088 has 7 historical records while Newrez currently shows only 1 active slot).

### 2.5 Bid and Sale Fields (P1/P2 — Bid Approval Panel)

| Standard Interface Field | Newrez Raw Field | Type | Priority | BPS Panel / Function | Newrez Status |
|---|---|---|---|---|---|
| `bid_amount` | `fcbidamount` | DECIMAL | P2 | Bid Approval `bid_approval_bid_amount`; FCL Summary `summary_foreclosure_bid_amount` | ✅ 9.0% |
| `approved_bid_price` | `fcapprbidprice` | DECIMAL | P2 | Bid Approval `bid_approval_bid_amount` (BPS approval perspective) | ✅ 8.9% |
| `sale_amount` | `fcsaleamount` | DECIMAL | P1 | FCL Summary `summary_foreclosure_sale_amount`; ⚠️ fill rate (4.7%) > sale_held (2.1%), possible sequencing issue (see doc 13 Q9) | ⚠️ 4.7% |

**Business Meaning / Calculation Logic**

| Standard Interface Field | Business Meaning / Calculation Logic |
|---|---|
| `bid_amount` | Servicer-reported foreclosure bid amount; only populated when auction is imminent (~9% fill rate in active FCL) |
| `approved_bid_price` | BPS-approved bid amount after internal bid approval workflow; may differ from `fcbidamount` |
| `sale_amount` | Actual foreclosure auction sale amount; fill rate (4.7%) exceeds `fcsalehelddate` (2.1%), suggesting a data sequencing issue (see doc 13 Q9) |

---

### 2.6 Loan Attribute and Risk Enhancement Fields (P1/P2 — Newrez-Provided but Not Yet Utilized)

> **Source**: Fields in this section come from `newrez.portnewrezfc` and `newrez.portnewrezgeneral`. MCP live measurements (2026-05) confirm Newrez provides these fields, but the current ETL and BPS system does not read or utilize them.  
> **BPS display**: These fields currently have no direct BPS panel mapping. Their inclusion in the interface standard serves two purposes: (1) reserve data sources for new-system ETL redesign; (2) provide a reference baseline for per-Servicer gap analysis.  
> **Data basis**: Fill rates from MCP query on active FCL latest snapshot (39-loan sample).

| Standard Interface Field | Newrez Raw Field | Source Table | Type | Priority | Business Use | Newrez Status |
|---|---|---|---|---|---|---|
| `investor_loan_id` | `investorloanid` | `portnewrezfc` | VARCHAR | P1 | Investor-perspective loan ID; used for cross-referencing with investor reporting systems (e.g., Fannie Mae/Freddie Mac); distinct from system `loan_id` and Servicer `shellpointloanid` | ✅ **100%** |
| `lien_position` | `jr_sr_lien_flag` (portnewrezfc) / `lienposition` (portnewrezgeneral) | `portnewrezfc` + `portnewrezgeneral` | INT | P1 | Lien priority (1=first/Senior; 2=second/Junior); **FCL strategy differs fundamentally** — Junior Lien foreclosure must account for Senior Lien priority claim | ✅ **100%** (both tables) |
| `interest_paid_through_date` | `interestpaidthroughdate` | `portnewrezgeneral` | DATE | P1 | Date through which borrower has paid interest ("paid-to date"); most direct basis for calculating true delinquency days, more precise than `nextduedate` | ✅ **100%** |
| `in_auction_flag` | `inauctionflag` | `portnewrezgeneral` | INT | P1 | Whether the loan is currently in auction proceedings (1=yes); low fill rate but high signal strength — any value means foreclosure is near completion | ✅ 7.7% (high value when populated) |
| `borrower_deceased_flag` | `borrowerdeceasedflag` | `portnewrezgeneral` | INT | P1 | Whether the borrower has died (1=yes); affects foreclosure legal process — estate representative must be notified; some states require re-establishing loan ownership before proceeding | ✅ 5.1% (high impact when populated) |
| `reason_for_default` | `reasonfordefault` | `portnewrezgeneral` | VARCHAR | P2 | Root cause of default (e.g., unemployment, income reduction, medical expense, divorce); key input for LM program selection and risk classification | ✅ 46.2% |
| `hold_1_comment` | `fchold1comment` | `portnewrezfc` | VARCHAR | P2 | Hold slot 1 detailed notes; supplements `hold_1_description` with specific context (e.g., "BK case #2026-123", "Awaiting LM decision") | ✅ 82.1% |
| `hold_2_comment` | `fchold2comment` | `portnewrezfc` | VARCHAR | P2 | Hold slot 2 notes (same as above) | ✅ 82.1% |
| `hold_3_comment` | `fchold3comment` | `portnewrezfc` | VARCHAR | P2 | Hold slot 3 notes (same as above) | ✅ 82.1% |

**Business Meaning / Calculation Logic**

| Standard Interface Field | Business Meaning / Calculation Logic |
|---|---|
| `investor_loan_id` | Investor (e.g., Fannie Mae, Freddie Mac, private fund) loan number; different from system `loan_id` (our primary key) and `servicer_loan_id` (Newrez internal ID); used for investor reporting reconciliation and loan tracking across Servicer transfers |
| `lien_position` | Lien position: 1=first lien (Senior, priority claim); 2=second lien (Junior). Junior Lien foreclosure requires monitoring Senior Lien FCL progress (SR lien tracking fields currently at 0% fill in Newrez sample); BPS should differentiate the two foreclosure workflows |
| `interest_paid_through_date` | Date through which borrower payments have been credited; difference from `report_date` (`dataasof`) is the true delinquency days; e.g., `interestpaidthroughdate=2025-10-01`, `dataasof=2026-05-24` → ~235 days delinquent; more direct than `days360(nextduedate, dataasof)` |
| `in_auction_flag` | Whether loan is currently in the foreclosure auction process (scheduled or in progress); 7.7% of active FCL loans are flagged, indicating ~7% are at the final foreclosure stage requiring priority handling |
| `borrower_deceased_flag` | Deceased borrower flag; deceased-borrower foreclosure requires notifying estate representative or heirs; some states have specific legal requirements; affects BPS operational workflow and compliance reporting |
| `reason_for_default` | Default root cause free text (Newrez format); used for: (1) LM program selection (unemployment → Forbearance; permanent income reduction → Modification); (2) batch risk classification; (3) investor reporting |
| `hold_1_comment` | Hold slot 1 supplemental notes, adding context to the structured `hold_1_description`; typical content: bankruptcy case numbers, court continuance reasons, LM negotiation status |
| `hold_2_comment` | Hold slot 2 notes (same as above) |
| `hold_3_comment` | Hold slot 3 notes (same as above) |

> **Zero-fill fields (Newrez currently does not provide — reserved as future extensions)**:
> - **Senior/Junior Lien tracking**: `srlienmonitorflag`, `srliensalescheduleddate`, `srliensalehelddate` (when Newrez loan is Junior Lien, Senior Lien FCL progress is critical)
> - **SCRA military protections**: `loanscraflag`, `loanscrastartdate`, `loanscraenddate` (SCRA-protected loans must halt foreclosure; active-duty military loans require special handling)
> - **FEMA disaster areas**: `femaarea`, `femaaffect` (loans in declared disaster areas are subject to foreclosure moratoriums)
> - **Title ordering**: `titleordereddate` (date title search was commissioned, precedes `titlereceiveddate`; Newrez currently does not provide)

---

## Section 3: LM Data Field Specification (Source: `portnewrezlm`)

### 3.1 LM Cycle Fields (P1 — Loss Mitigation Cycle Panel)

Each LM cycle is stored as one row (uniquely identified by `lmdeal` + `dealstartdate`). BPS stores one-to-many; history is never overwritten.

| Standard Interface Field | Newrez Raw Field | Type | Priority | Format / ETL Requirement | BPS Panel / Function | Newrez Status |
|---|---|---|---|---|---|---|
| `lm_deal` | `lmdeal` | INT→VARCHAR | P1 | **Decode mapping table required** (int code → text, e.g., `7`→`"DIL"`) | LM Cycle `deal` | ✅ Provided |
| `lm_program` | `lmprogram` | INT→VARCHAR | P1 | **Decode mapping table required** | LM Cycle `program` | ✅ Provided |
| `lm_status` | `lmstatus` | INT→VARCHAR | P1 | **Decode mapping table required** | LM Cycle `lmc_status` | ✅ Provided |
| `lm_cycle_open_date` | `dealstartdate` | DATE | P1 | YYYY-MM-DD; LM cycle start date | LM Cycle `cycle_opened_date` | ✅ Provided |
| `lm_cycle_close_date` | `lmremovaldate` | DATE | P1 | YYYY-MM-DD; NULL = still active | LM Cycle `cycle_closed_date` | ✅ Provided |
| `lm_final_disposition` | `lmdecision` | INT→VARCHAR | P1 | **Decode mapping table required** | LM Cycle `final_disposition` | ✅ Provided |
| `lm_denial_reason` | `denialreason` | INT→VARCHAR | P1 | **Decode mapping table required**; empty string when no denial | LM Cycle `denialreason` | ✅ Provided |
| `borrower_intentions` | `borrowerintention` | INT→VARCHAR | P2 | Decode mapping table (if provided) | LM Cycle `borrower_intentions` | ❌ 0% (Newrez does not provide; see doc 13 Q6) |
| `imminent_default` | *(no field)* | VARCHAR | P2 | CFPB Reg X trigger condition | LM Cycle `imminent_default` | ❌ 0% (Newrez does not provide; see doc 13 Q6) |
| `single_point_of_contact` | *(no field)* | VARCHAR | P2 | CFPB Reg X 12 CFR 1024.40 | LM Cycle `single_point_of_contact` | ❌ 0% (Newrez does not provide; see doc 13 Q6) |

**Business Meaning / Calculation Logic**

| Standard Interface Field | Business Meaning / Calculation Logic |
|---|---|
| `lm_deal` | LM strategy category (integer-coded); ETL decodes to text: Evaluation / Modification / Short Sale / DIL etc.; reflects the overall direction of this loss mitigation attempt |
| `lm_program` | Specific LM execution program (integer-coded); sub-program within the Deal category; e.g., Bridger mod / 496.0 / Deed-in-Lieu |
| `lm_status` | Current workflow progress status for this LM cycle (integer-coded); e.g., Pending Financials / Workout Denial / DIL Title Ordered |
| `lm_cycle_open_date` | Start date of this LM cycle (date Servicer formally opened this workout attempt); forms part of the cycle's unique identifier together with `lm_deal` |
| `lm_cycle_close_date` | End date of this LM cycle; NULL = still in progress; combined with open_date to calculate cycle duration |
| `lm_final_disposition` | Final disposition of this LM cycle (integer-coded); determines FCL trajectory: `Referral to FC` / `Request Incomplete` → FCL continues; `Approved` → FCL paused |
| `lm_denial_reason` | Specific reason for LM denial (integer-coded); empty string when there is no denial |
| `borrower_intentions` | Borrower's stated intended resolution (integer-coded); e.g., retain property / short sale / deed-in-lieu; CFPB Reg X related; Newrez does not provide |
| `imminent_default` | CFPB Reg X required flag for imminent default; marks borrowers not yet delinquent but facing foreseeable repayment hardship; triggers early LM assessment obligation; Newrez does not provide |
| `single_point_of_contact` | CFPB Reg X 12 CFR 1024.40 required dedicated servicer contact name; borrowers in LM must have a single designated point of contact; Newrez does not provide |

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

| Standard Interface Field | Newrez Raw Field | Type | Priority | BPS Panel / Function | Newrez Status |
|---|---|---|---|---|---|
| `active_bk_flag` | `activebkflag` | TINYINT | P1 | `variance_active_bankruptcy` (FCL Summary active bankruptcy indicator) | ✅ Provided |
| `bk_status` | `bkstatus` (int) | INT→VARCHAR | P1 | BK panel Status column (BPS decodes to text; DB-verified) | ✅ Confirmed: BPS decodes to text (Active/Discharged/Dismissed/Closed/ReliefGranted; bkstatus 1→Active·2→Discharged·3→Dismissed·4→Closed·5→ReliefGranted, DB-verified) |
| `bk_legal_status` | `legalstatus` (from `portnewrezgeneral`, text; doc's `bkstage` was a misattribution) | VARCHAR | P1 | BK panel Legal Status column (from portnewrezgeneral.legalstatus text) | ✅ Confirmed: BPS `legal_status` comes from `portnewrezgeneral.legalstatus` text (FCBU/BK13/BK7/BK11/BK7DCH/BK11DCH/BKD7LM/BKD13LM/FCSold/REO, etc.), **not** a decode of `bkstage` (DB-verified) |
| `bk_status_date` | `bkrcurrentstatusdate` | DATE | P1 | BK panel Status Date | ✅ Provided |
| `bk_chapter` | `bkchapter` | VARCHAR/INT | P1 | BK panel Chapter (7/11/13) | ✅ Provided |
| `bk_filed_date` | `bkfileddate` | DATE | P1 | BK history tracing | ✅ Provided |
| `bk_removal_date` | `bkremovaldate` | DATE | P1 | `variance_completed_bankruptcy` calculation (activebkflag=0 AND bkremovaldate IS NOT NULL) | ✅ Provided |
| `mfr_filed_date` | `mfrfileddate` | DATE | P1 | BK panel MFR Filed Date | ✅ Provided |
| `mfr_hearing_results` | `mfrhearingresults` | INT | P1 | BK panel MFR Status | ⚠️ Newrez provides a raw numeric code (0/3/4/5/6 observed); BPS `mfr_status` column is empty in dev (0/64) — downstream population/decode TBD |
| `proof_of_claim_date` | `pocfileddate` | DATE | P1 | BK panel Proof of Claim Date | ✅ Provided |
| `post_petition_due_date` | `bkpostpetitionduedate` | DATE | P1 | BK panel Post Petition Due Date | ✅ Provided |

**Business Meaning / Calculation Logic**

| Standard Interface Field | Business Meaning / Calculation Logic |
|---|---|
| `active_bk_flag` | Whether the loan is currently under active bankruptcy protection (Automatic Stay); 1=active; foreclosure must legally halt during Automatic Stay |
| `bk_status` | Current bankruptcy case status. Newrez raw `bkstatus` is an integer code (1–5); **BPS decodes it to text** (observed dominant map: 1→Active·2→Discharged·3→Dismissed·4→Closed·5→ReliefGranted); reflects the current node in bankruptcy proceedings |
| `bk_legal_status` | Bankruptcy legal-proceeding stage. BPS `legal_status` **actually comes from `newrez.portnewrezgeneral.legalstatus`** (text, e.g. FCBU/BK13/BK7/BK11/...), NOT a decode of `bkstage` (DB-verified); a different classification dimension from bk_status |
| `bk_status_date` | Effective date of the current bankruptcy status |
| `bk_chapter` | Bankruptcy chapter filed under; common: Chapter 7 (liquidation) / Chapter 13 (repayment plan) / Chapter 11 (reorganization); affects foreclosure resumption strategy |
| `bk_filed_date` | Date the bankruptcy petition was filed with the court; BPS deduplication key (loanid + bkfileddate uniquely identifies one bankruptcy filing) |
| `bk_removal_date` | Date the bankruptcy proceeding was terminated; `variance_completed_bankruptcy` logic: `activebkflag=0 AND bkremovaldate IS NOT NULL` |
| `mfr_filed_date` | Date the lender filed a Motion for Relief (MFR) from the Automatic Stay with the bankruptcy court; foreclosure can resume if MFR is granted |
| `mfr_hearing_results` | MFR hearing outcome. Newrez raw `mfrhearingresults` is an integer code (0/3/4/5/6 observed); BPS `mfr_status` is empty in dev (0/64) — whether/how it flows downstream is TBD; if granted, foreclosure proceedings may resume |
| `proof_of_claim_date` | Date the lender formally registered its debt claim amount (Proof of Claim) with the bankruptcy court; required for bankruptcy compliance |
| `post_petition_due_date` | Monthly loan payment due date after the bankruptcy petition was filed; used to track whether the borrower continued making payments during Automatic Stay |

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
| `currentmilestone` | Fill rate only 62.7%; BPS `summary_current_step` must fall back to `fcstage` | 62.7% | P1 ⚠️ |
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
| `currentmilestone` | Fill rate 62.7% (below acceptable) | P1 ⚠️ Recommend improvement to 90%+ |
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
| **FCL Summary Panel** | Current Step | `currentmilestone` (priority) / `fcstage` (fallback) | P1 |
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
