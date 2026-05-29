# 01 — Source Data Analysis: Foreclosure-Related Raw Data

---

## Document Information

| Field | Content |
|-------|---------|
| **Purpose** | Comprehensive inventory of all servicer raw data tables in PrefectFlow, focused on FCL, BK, and LM fields, providing the source-of-truth basis for ETL pipeline and status generation analysis. |
| **Problem solved** | Each servicer uses different field names and formats for the same concepts — this document unifies them. Added in v2: per-field value range, calculation logic, example values, DB-verified statistics, and FCL relevance annotations. |
| **Scope** | Newrez/Shellpoint, SLS, Carrington, MRC, FCI, Selene — six servicers' MySQL staging schemas |
| **System** | `PrefectFlow/statistics_script/` DDL files + `PrefectFlow/flow/servicer_data/` configuration |

**Target audience:** Data engineers · Validators/reconciliation engineers · System rewrite architects · Onboarding engineers

**Dependencies:** None (this document is the data foundation for all others)

**Known Limitations:**
- MRC table currently has only 17 records (all current-month data); `fc_status`/`fc_milestone` and other fields are all NULL
- SLS data ends at 2024-08-07 (SLS was replaced by Newrez on 2024-07-05 and receives no further updates)
- Original documentation incorrectly listed `status` / `foreclosure_status_code` as Carrington fields — these do not exist; actual fields are `loan_status` and `fcl_flag`

**Revision history:**

| Date | Author | Version | Changes | Verification |
|------|--------|---------|---------|-------------|
| 2026-05-21 | AI Agent (Claude Sonnet 4.6) | v1 | Initial version, code reverse-engineering + Redshift DB evidence | Verified via Redshift dev |
| 2026-05-21 | AI Agent (Claude Sonnet 4.6) | v2 | Added: DB/Schema labels, table descriptions, per-field value range / calculation logic / example values / statistics / FCL relevance | Direct MySQL prod queries |

---

## Database Connection Information

All tables reside in a **MySQL** instance (Azure-managed):

| Property | Value |
|----------|-------|
| **Host** | `bridg004-db-prod.mysql.database.azure.com` |
| **Port** | `3306` |
| **User** | `brgdev` |
| **Auth** | SSL required |

| Servicer | MySQL Schema | Primary Tables |
|----------|-------------|----------------|
| Newrez / Shellpoint | `newrez` | `portnewrezfc`, `portnewrezbk`, `portnewrezlm`, `portnewrezgeneral` |
| SLS | `sls` | `portassetdaily`, `portfcldaily`, `portbkdaily`, `portlmdaily` |
| Carrington | `carrington` | `portcarrington` |
| MRC | `mrc` | `portmrcforeclosure` |
| FCI | `fci` | Per-category file tables |
| Selene | `selene` | Per-category file tables |

> **Naming change note:** Before 2024-07-05, the Newrez servicer tables used the prefix `portshellpoint*` (Shellpoint era). After the switch, the prefix became `portnewrez*`. DDL file `shellpoint_daily.sql` is a historical artifact; live tables use the `portnewrez*` prefix in the `newrez` schema.

---

## 1. Data Ingestion Architecture

```
External Sources (S3 / SMB / SFTP)
    │
    ├── s3://brigaws/shellpoint_new/      → newrez schema (MySQL)
    ├── s3://brigaws/sls_new/             → sls schema (MySQL)
    ├── s3://brigaws/carrington_new/      → carrington schema (MySQL)
    ├── s3://brigaws/mrc_new/             → mrc schema (MySQL)
    ├── s3://brigaws/fci_new/             → fci schema (MySQL)
    └── s3://brigaws/selene_new/          → selene schema (MySQL)
```

Each servicer's data is stored in an independent MySQL schema, **uploaded daily**. The date field name varies by servicer — see per-table notes.

---

## 2. Newrez / Shellpoint (`newrez` schema)

**Database:** MySQL (`bridg004-db-prod`)  
**Schema:** `newrez`  
**File format:** `.csv`  
**Table prefix:** `portnewrez*` (historical: `portshellpoint*`)  
**DDL reference:** `statistics_script/shellpoint_daily.sql` (historical name; live tables renamed)  
**Date range:** 2023-12-14 ~ 2026-05-19 (continuously updated)

---

### 2.1 `portnewrezfc` — Foreclosure Detail Table (formerly `portshellpointfc`)

**Description:** Full lifecycle foreclosure tracking table. Records each loan's FCL initiation, milestone dates (referral → first legal action → service → judgment → scheduled sale → held sale), hold reasons (up to 4 layers), and FCL outcome. One row per loan per data date.

**Fully qualified name:** `newrez.portnewrezfc` | **Total rows:** 1,553,268

**Part A — Field Definitions**

| Field | Type | Meaning | Value Range | Calculation Logic | FCL Related |
|-------|------|---------|-------------|-------------------|-------------|
| `loanid` | varchar(255) | Loan ID (Bridger internal key) | Non-null string, primarily 10-digit numbers | Raw ingest (Bridger-assigned) | ✅ Primary |
| `dataasof` | date | Data date (daily snapshot) | 2023-12-14 ~ 2026-05-19 | Raw ingest | — |
| `activefcflag` | int | **Active foreclosure flag** | {0, 1}, 0=Inactive, 1=Active, no NULLs | Raw ingest → mapped to `fcl_flag` in `portdaily_config.py` | ✅ Primary |
| `fcstage` | varchar(255) | **Current FCL stage** description | 65 text descriptions + NULL | Raw ingest (servicer-tracked) → flows into `port.fcl_stage_info.stage` | ✅ Primary |
| `fcsetupdate` | date | FCL setup/initiation date | 2018-08-15 ~ 2026-05-18, or NULL | Raw ingest (written when servicer approves FCL) | ✅ Primary |
| `fcreferraldate` | date | Attorney referral date | 2018-08-15 ~ 2026-05-18, or NULL | Raw ingest → flows into `port.fcl_stage_info.referral_start_date` | ✅ Primary |
| `firstlegaldate` | date | First legal action date | 2018-10-29 ~ 2026-05-18, or NULL | Raw ingest → flows into `port.fcl_stage_info.legal_start_date` | ✅ Primary |
| `servicecompletedate` | date | Service of process completion date | 2018-12-10 ~ 2026-02-16, or NULL | Raw ingest → flows into `port.fcl_stage_info.service_start_date` | ✅ Primary |
| `fcjudgmenthearingscheduled` | date | Judgment hearing scheduled date | 2020-01-22 ~ 2026-08-21, or NULL | Raw ingest → flows into `port.fcl_stage_info.judgement_start_date` | ✅ Primary |
| `fcjudgmententered` | date | Judgment entered date | 2025-01-10 ~ 2026-04-09, or NULL | Raw ingest | ✅ Primary |
| `fcscheduledsaledate` | date | Scheduled foreclosure sale date | 2023-09-14 ~ 2026-07-14, or NULL | Raw ingest → flows into `port.fcl_stage_info.sale_start_date` | ✅ Primary |
| `fcsalehelddate` | date | Actual foreclosure sale date | 2025-05-27 ~ 2026-05-15, or NULL | Raw ingest → flows into `port.basic_data_loan_fcl` | ✅ Primary |
| `fcsaleamount` | decimal(32,16) | Sale proceeds (USD) | $90,001 ~ $400,000, or NULL | Raw ingest (auction result) | ✅ Secondary |
| `fcresults` | varchar(255) | Foreclosure outcome description | {"3rd Party", "REO"}, or NULL | Raw ingest → flows into `port.basic_data_loan_fcl.fcresults` | ✅ Primary |
| `fchold1description` | varchar(255) | **FCL hold reason 1** | 38 text descriptions, or NULL | Raw ingest → flows into `port.basic_data_loan_foreclosure_hold` | ✅ Primary |
| `fchold1startdate` | date | Hold 1 start date | 2019-11-21 ~ 2026-05-19, or NULL | Raw ingest | ✅ Primary |
| `fchold1enddate` | date | Hold 1 end date | 2019-11-27 ~ 2026-05-14, or NULL | Raw ingest | ✅ Primary |
| `fchold2description` | varchar(255) | **FCL hold reason 2** | 36 text descriptions, or NULL | Raw ingest → flows into `port.basic_data_loan_foreclosure_hold` | ✅ Primary |
| `fchold2startdate` | date | Hold 2 start date | 2019-11-21 ~ 2026-05-19, or NULL | Raw ingest | ✅ Primary |
| `fchold2enddate` | date | Hold 2 end date | 2019-11-27 ~ 2026-05-14, or NULL | Raw ingest | ✅ Primary |
| `judicial` | int | Judicial foreclosure flag | {0, 1}, 0=Non-Judicial, 1=Judicial | Raw ingest → flows into `port.basic_data_loan_fcl.judicial` | ✅ Secondary |
| `fcbidamount` | decimal(32,16) | FCL bid amount (USD) | $90,000 ~ $543,306, or NULL | Raw ingest (bidder's offer) | ✅ Secondary |
| `daysinfc` | int | Days in foreclosure process | 1 ~ 803, or NULL | Raw ingest (servicer-calculated: `fcsetupdate → dataasof` delta) | ✅ Primary |
| `fcremovaldesc` | varchar(255) | FCL removal reason description | {"Reinstated","Loss Mitigation","Paid in Full","Process Complete","Deed in Lieu Cmplte","3rd Party"}, or NULL | Raw ingest → mapped to `summary_foreclosure_status` | ✅ Primary |
| `fcremovaldate` | date | Foreclosure removal date | 2019-11-27 ~ 2026-05-18, or NULL | Raw ingest | ✅ Primary |

**Part B — Field Statistics**

| Field | Example Values | Statistics |
|-------|----------------|------------|
| `loanid` | "0671496644", "9799754446" | 1,553,268 rows · NULL rate 0% · 7,370 unique loans |
| `dataasof` | 2024-01-15, 2026-05-19 | 1,553,268 rows · NULL rate 0% · 880 distinct dates (one batch per day) |
| `activefcflag` | 0, 1 | 1,553,268 rows · NULL rate 0% · 0(1,539,831=99.1%), 1(13,437=0.9%) |
| `fcstage` | "Pre-Sale Review 1 (SCRA and PACER Check)", "Complaint Sent for Filing" | 1,553,268 rows · NULL rate 97.9% · non-NULL: 32,841 rows · 65 values · top 5: Pre-Sale Review 1(3,840), Preliminary Title Clear(2,746), NOS Sent for Recording(2,663), Complaint Sent for Filing(2,589) |
| `fcsetupdate` | 2024-07-04, 2025-02-03 | 1,553,268 rows · NULL rate 97.9% · non-NULL: 32,968 rows · 84 dates · range 2018-08-15~2026-05-18 |
| `fcreferraldate` | 2022-09-13, 2021-05-27 | 1,553,268 rows · NULL rate 97.9% · non-NULL: 32,968 rows · 93 dates · range 2018-08-15~2026-05-18 |
| `firstlegaldate` | 2022-10-27, 2024-03-29 | 1,553,268 rows · NULL rate 98.9% · non-NULL: 16,466 rows · 53 dates · range 2018-10-29~2026-05-18 |
| `servicecompletedate` | 2024-04-01, 2024-11-26 | 1,553,268 rows · NULL rate 99.6% · non-NULL: 6,787 rows · 22 dates |
| `fcjudgmenthearingscheduled` | 2025-09-16, 2025-10-15 | 1,553,268 rows · NULL rate 99.8% · non-NULL: 2,909 rows · 24 dates · range 2020-01-22~2026-08-21 |
| `fcjudgmententered` | 2025-01-10, 2025-08-13 | 1,553,268 rows · NULL rate 99.9% · non-NULL: 1,833 rows · 11 dates |
| `fcscheduledsaledate` | 2025-06-05, 2025-05-16 | 1,553,268 rows · NULL rate 99.7% · non-NULL: 4,035 rows · 52 dates · range 2023-09-14~2026-07-14 |
| `fcsalehelddate` | 2025-10-14, 2025-11-04 | 1,553,268 rows · NULL rate 99.9% · non-NULL: 895 rows · 9 dates · range 2025-05-27~2026-05-15 |
| `fcsaleamount` | 274000, 357200, 400000 | 1,553,268 rows · NULL rate 99.9% · non-NULL: 1,251 rows · 9 distinct amounts · $90,001~$400,000 |
| `fcresults` | "3rd Party", "REO" | 1,553,268 rows · NULL rate 99.9% · 2 outcomes |
| `fchold1description` | "Loss Mitigation Workout", "Awaiting Funds to Post", "Service Delay" | 1,553,268 rows · NULL rate 98.1% · 38 descriptions · top 5: Loss Mitigation Workout(9,147), Awaiting Funds to Post(7,141), Service Delay(2,010), Court Delay(1,467) |
| `fchold1startdate` | 2024-04-07, 2022-11-16 | 1,553,268 rows · NULL rate 98.1% · non-NULL: 29,941 rows · 250 dates |
| `fchold1enddate` | 2024-04-12, 2022-11-25 | 1,553,268 rows · NULL rate 98.6% · non-NULL: 22,080 rows · 191 dates |
| `fchold2description` | "Loss Mitigation Workout", "ACT(PA) Letter/Demand Letter/NOI Expiration" | 1,553,268 rows · NULL rate 98.5% · 36 descriptions |
| `fchold2startdate` | 2024-02-23, 2022-11-08 | 1,553,268 rows · NULL rate 98.5% · non-NULL: 22,934 rows · 205 dates |
| `fchold2enddate` | 2023-06-05, 2022-11-25 | 1,553,268 rows · NULL rate 98.6% · non-NULL: 22,357 rows · 196 dates |
| `judicial` | 0, 1 | 1,553,268 rows · NULL rate 97.9% · 1(16,601=50.4%), 0(16,367=49.6%) — judicial and non-judicial roughly equal |
| `fcbidamount` | 154591.01, 231285.22, 271278.01 | 1,553,268 rows · NULL rate 99.8% · non-NULL: 2,545 rows · 20 distinct amounts · $90,000~$543,306 |
| `daysinfc` | 63, 83, 36 | 1,553,268 rows · NULL rate 97.9% · non-NULL: 32,968 rows · 803 distinct values · range 1~803 days |
| `fcremovaldesc` | "Reinstated", "Loss Mitigation", "Paid in Full" | 1,553,268 rows · NULL rate 98.7% · non-NULL: 19,809 rows · 6 descriptions |
| `fcremovaldate` | 2024-04-11, 2022-11-25 | 1,553,268 rows · NULL rate 98.7% · non-NULL: 19,809 rows · 73 dates · range 2019-11-27~2026-05-18 |

---

### 2.2 `portnewrezbk` — Bankruptcy Detail Table (formerly `portshellpointbk`)

**Description:** Bankruptcy process tracking table. Records each loan's bankruptcy filing date, chapter type (7/11/13), key event dates (removal/discharge/dismissal/MFR), and current BK stage. One row per loan per data date.

**Fully qualified name:** `newrez.portnewrezbk` | **Total rows:** 1,553,268

**Part A — Field Definitions**

| Field | Type | Meaning | Value Range | Calculation Logic | FCL Related |
|-------|------|---------|-------------|-------------------|-------------|
| `loanid` | varchar(255) | Loan ID | Same as portnewrezfc | Raw ingest | ✅ Secondary |
| `dataasof` | date | Data date | 2023-12-14 ~ 2026-05-19 | Raw ingest | — |
| `activebkflag` | int | **Active bankruptcy flag** | {0, 1}, no NULLs | Raw ingest → `CASE WHEN delinquency_status_mba LIKE '%Bankruptcy%' THEN 'Y'` generates `bankruptcy` auxiliary field | ✅ Secondary |
| `bkstatus` | int | Bankruptcy status code | {1,2,3,4,5} (servicer-coded) or NULL | Raw ingest (servicer-defined codes) | ✅ Secondary |
| `bkchapter` | int | Bankruptcy chapter | {7, 11, 13} or NULL | Raw ingest → flows into `port.basic_data_loan_foreclosure_bankruptcy.chapter` | ✅ Secondary |
| `bkfileddate` | date | Bankruptcy filing date | 2008-06-16 ~ 2026-04-27, or NULL | Raw ingest → flows into `port.basic_data_loan_foreclosure_bankruptcy` | ✅ Secondary |
| `bkremovaldate` | date | Bankruptcy removal/closing date | 2009-09-18 ~ 2026-04-14, or NULL | Raw ingest | ✅ Secondary |
| `dischargeddate` | date | Bankruptcy discharge date | 2009-09-18 ~ 2026-01-08, or NULL | Raw ingest | ✅ Secondary |
| `dismisseddate` | date | Bankruptcy dismissal date | 2022-09-30 ~ 2026-04-14, or NULL | Raw ingest | ✅ Secondary |
| `mfrfileddate` | date | Motion for Relief from Stay filed date | 2025-06-10 ~ 2026-04-29, or NULL | Raw ingest → flows into `port.basic_data_loan_foreclosure_bankruptcy.mfr_filed_date` | ✅ Secondary |
| `mfrhearingdate` | date | MFR hearing date | 2025-06-24 ~ 2026-05-15, or NULL | Raw ingest | ✅ Secondary |
| `bkcasenumber` | varchar(255) | Bankruptcy case number | Court-assigned text, or NULL | Raw ingest | — |

**Part B — Field Statistics**

| Field | Example Values | Statistics |
|-------|----------------|------------|
| `activebkflag` | 0, 1 | 1,553,268 rows · NULL rate 0% · 0(1,547,862=99.7%), 1(5,406=0.3%) |
| `bkstatus` | 1, 2, 3 | 1,553,268 rows · NULL rate 99.0% · 5 codes · 2(8,033=52%), 1(5,353=34%), 3(882=6%) |
| `bkchapter` | 7, 11, 13 | 1,553,268 rows · NULL rate 99.0% · 3 values · 13(7,345=47%), 7(5,619=36%), 11(2,667=17%) |
| `bkfileddate` | 2010-06-03, 2024-02-09 | 1,553,268 rows · NULL rate 99.0% · 34 dates · range 2008-06-16~2026-04-27 |
| `bkremovaldate` | 2014-09-24, 2024-04-11 | 1,553,268 rows · NULL rate 99.4% · 23 dates |
| `dischargeddate` | 2014-09-24, 2015-04-17 | 1,553,268 rows · NULL rate 99.4% · 13 dates |
| `dismisseddate` | 2022-09-30, 2025-05-08 | 1,553,268 rows · NULL rate 99.9% · 5 dates |
| `mfrfileddate` | 2025-06-10, 2025-11-04 | 1,553,268 rows · NULL rate 99.9% · 5 dates |
| `mfrhearingdate` | 2025-06-24, 2025-12-02 | 1,553,268 rows · NULL rate 99.9% · 4 dates |
| `bkcasenumber` | "1033613", "981704" | 1,553,268 rows · NULL rate 99.0% · 33 unique case numbers |

---

### 2.3 `portnewrezlm` — Loss Mitigation Table (formerly `portshellpointlm`)

**Description:** Loss mitigation (LM) process tracking table. Records each loan's LM active status, deal/program type (both integer-coded), and the status of three LM sub-processes (Forbearance, Trial payment plan, Repayment plan). One row per loan per data date.

**Fully qualified name:** `newrez.portnewrezlm` | **Total rows:** 1,553,268

**Part A — Field Definitions**

| Field | Type | Meaning | Value Range | Calculation Logic | FCL Related |
|-------|------|---------|-------------|-------------------|-------------|
| `loanid` | varchar(255) | Loan ID | Same as above | Raw ingest | ✅ Secondary |
| `dataasof` | date | Data date | 2023-12-14 ~ 2026-05-19 | Raw ingest | — |
| `activelmflag` | int | **Active LM flag** | {0, 1}, no NULLs | Raw ingest → `CASE WHEN activelmflag='1' THEN 'Y' ELSE 'N'` generates `lm_flag` | ✅ Primary |
| `lmstatus` | int | Current LM status code | 5 ~ 202 (43 integer codes) or NULL | Raw ingest (servicer internal codes; requires lookup table) | ✅ Secondary |
| `lmdeal` | int | LM deal type code | 1 ~ 11 (8 values) or NULL | Raw ingest → flows into `port.basic_data_loan_foreclosure_loss_mitigation.deal` | ✅ Secondary |
| `lmprogram` | int | Specific LM program code | 8 ~ 531 (35 values) or NULL | Raw ingest → flows into `port.basic_data_loan_foreclosure_loss_mitigation.program` | ✅ Secondary |
| `forbearancestatus` | int | Forbearance agreement status code | {1, 4, 6} or NULL | Raw ingest (servicer internal codes) | ✅ Secondary |
| `trialstatus` | int | Trial payment plan status code | {1, 4, 7, 8} or NULL | Raw ingest | ✅ Secondary |
| `repaymentstatus` | int | Repayment plan status code | {1, 4, 5, 6, 7} or NULL | Raw ingest | ✅ Secondary |

**Part B — Field Statistics**

| Field | Example Values | Statistics |
|-------|----------------|------------|
| `activelmflag` | 0, 1 | 1,553,268 rows · NULL rate 0% · 0(1,531,996=98.6%), 1(21,272=1.4%) |
| `lmstatus` | 166, 112, 5, 20 | 1,553,268 rows · NULL rate 93.3% · 43 codes · 166(39,483=38%), 112(16,398=16%), 5(11,604=11%) |
| `lmdeal` | 2, 1, 11, 5 | 1,553,268 rows · NULL rate 93.3% · 8 values · 2(37,445=36%), 1(30,962=30%), 11(13,461=13%) |
| `lmprogram` | 21, 73, 12, 29 | 1,553,268 rows · NULL rate 93.3% · 35 values · 21(37,412=36%), 73(13,461=13%) |
| `forbearancestatus` | 4, 1, 6 | 1,553,268 rows · NULL rate 99.2% · 3 values · 4(10,193=83%), 1(2,067=17%), 6(2) |
| `trialstatus` | 8, 1, 4 | 1,553,268 rows · NULL rate 99.4% · 4 values · 8(7,110=71%), 1(2,239=22%), 4(675=7%) |
| `repaymentstatus` | 5, 1, 7 | 1,553,268 rows · NULL rate 99.4% · 6 values · 5(4,401=48%), 1(2,043=22%), 7(1,876=20%) |

---

### 2.4 `portnewrezgeneral` — General Loan Information (formerly `portshellpointgeneral`)

**Description:** General loan status snapshot. The most critical field is `delinquency_status_mba` (MBA-standard delinquency description) — this field is the primary input for ETL-generated normalized `delinq` codes. Note: this field is **not** present in the raw Excel file; it is populated programmatically during ingest (DDL comment: "这个字段在excel文档中没有呢，代码中自己补充进去的" — "this field is not in the Excel file; it is filled in by code").

**Fully qualified name:** `newrez.portnewrezgeneral` | **Total rows:** 1,553,258

**Part A — Field Definitions**

| Field | Type | Meaning | Value Range | Calculation Logic | FCL Related |
|-------|------|---------|-------------|-------------------|-------------|
| `loanid` | varchar(255) | Loan ID | Same as above | Raw ingest | ✅ Primary |
| `dataasof` | date | Data date | 2023-12-14 ~ 2026-05-19 | Raw ingest | — |
| `delinquency_status_mba` | varchar(50) | **MBA-standard delinquency status** (core field) | 18 text values, no NULLs | Raw ingest (Newrez-provided) → `portdaily_config.py` CASE-WHEN maps to `delinq` (C/D30/.../FCL/REO/P) | ✅ Primary |
| `mbadelinquency` | int | MBA delinquency numeric bucket code | 1 ~ 19 (18 values), no NULLs | Raw ingest (one-to-one with `delinquency_status_mba`) | ✅ Secondary |
| `legalstatus` | varchar(255) | Legal status code | {"FCBU","BK13","BK7","BK7DCH",...} 14 values + NULL | Raw ingest → flows into `port.basic_data_loan_fcl.legalstatus` | ✅ Secondary |
| `reasonfordefault` | varchar(255) | Reason for default | 29 text descriptions, or NULL | Raw ingest → flows into `port.basic_data_fcl_related.reasonfordefault` | ✅ Secondary |

**Part B — Field Statistics**

| Field | Example Values | Statistics |
|-------|----------------|------------|
| `delinquency_status_mba` | "Current", "1-29 DPD", "Full Payoff", "Foreclosure" | 1,553,258 rows · NULL rate 0% · 18 values · Current(1,085,990=69.9%), 1-29 DPD(256,528=16.5%), Full Payoff(149,690=9.6%), 30-59 DPD(21,616=1.4%), Foreclosure(12,573=0.8%) |
| `mbadelinquency` | 1, 2, 15, 3, 13 | 1,553,258 rows · NULL rate 0% · 18 numeric values · 1(1,085,990=69.9%), 2(256,528=16.5%), 15(149,690=9.6%) |
| `legalstatus` | "FCBU", "BK13", "BK7", "REOSLD" | 1,553,258 rows · NULL rate 98.1% · 14 values · FCBU(13,679=53%), BK13(4,312=16%), BK7(1,769=7%) |
| `reasonfordefault` | "Curtailment of Income", "Business Failure" | 1,553,258 rows · NULL rate 97.8% · 29 descriptions |

**`delinquency_status_mba` → `delinq` complete mapping (18 raw values):**

| Raw Value | Standard `delinq` | Notes |
|-----------|-------------------|-------|
| `Current` | `C` (or `VASP`*) | VASP is a special override — 19 records |
| `1-29 DPD` | `D30` | Servicer has already computed DPD bucket |
| `30-59 DPD` | `D30` | |
| `60-89 DPD` | `D60` | |
| `90-119 DPD` | `D90` | |
| `120-149 DPD` | `D120P` | |
| `180+ DPD` | `D120P` | |
| `Foreclosure` | `FCL` | `activefcflag=1` |
| `Foreclosure / Perf BK` | `FCL` | `bankruptcy='Y'` |
| `Foreclosure / Non-Perf BK` | `FCL` | `bankruptcy='Y'` |
| `REO` | `REO` | |
| `Full Payoff` | `P` | |
| `Paid in Full` | `P` | |
| `Completed Short Sale` | `P` | |
| `Service Release` | `P` | |
| `Loss Mitigation` | days360-based | `lm_flag='Y'` |
| `Performing Bankruptcy` | days360-based | `bankruptcy='Y'` |
| `Non-Performing Bankruptcy` | days360-based | `bankruptcy='Y'` |

> \* `VASP` (Vendee/Servicer Purchase): Special government-backed loan status, Newrez only. `delinquency_status_mba='Current'` but overridden to `VASP` (DB evidence: 10 Current + 8 180+DPD + 1 Foreclosure → VASP).

---

## 3. SLS (`sls` schema)

**Database:** MySQL (`bridg004-db-prod`)  
**Schema:** `sls`  
**File format:** `.txt`  
**Active period:** ≤ 2024-07-05 (replaced by Newrez thereafter)  
**DDL reference:** `statistics_script/sls_daily.sql`  
**Date range:** 2023-02-22 ~ 2024-08-07

> **Note:** SLS was the primary servicer before Shellpoint/Newrez. Data ends at 2024-08-07 (no further updates after the 2024-07-05 switch). SLS sub-tables use `account_number` as the loan ID field; the date field name varies by table (`dataasofdate` or `data_as_of_date`).

---

### 3.1 `portassetdaily` — Asset Summary Table

**Description:** Daily loan portfolio overview including MBA delinquency status (near-normalized format), FCL/BK/REO/forbearance active flags. The most important status source table in SLS data — equivalent to Newrez's `portnewrezgeneral`.

**Fully qualified name:** `sls.portassetdaily` | **Total rows:** 240,608  
**Loan ID field:** `account_number_investor` (varchar) | **Date field:** `dataasofdate` (date, 2023-02-22 ~ 2024-08-07)  
**Unique loans:** 790

**Part A — Field Definitions**

| Field | Type | Meaning | Value Range | Calculation Logic | FCL Related |
|-------|------|---------|-------------|-------------------|-------------|
| `account_number_investor` | varchar(32) | Loan ID (SLS internal) | 790 unique values, no NULLs | Raw ingest; mapped to `loanid` via `port.portidmap` | ✅ Primary |
| `dataasofdate` | date | Data date | 2023-02-22 ~ 2024-08-07 | Raw ingest | — |
| `delq_status_mba` | varchar(50) | **MBA delinquency status** (primary status field) | 8 text values, no NULLs | Raw ingest, already near-normalized → light mapping to `delinq` | ✅ Primary |
| `mba_delq_status_paystring` | varchar(255) | MBA payment history string (24 months) | Up to 24 chars; character set includes C/D/digits | Raw ingest (one char per month, concatenated) → referenced in generating `paymthistfull` | ✅ Secondary |
| `fcl_active_flag` | varchar(1) | **Active FCL flag** | {"N", "Y"}, no NULLs | Raw ingest → mapped to `fcl_flag` | ✅ Primary |
| `fc_hold_flag` | varchar(4) | FCL hold flag | {"N   ", "Y   "} (with trailing spaces), no NULLs | Raw ingest (note: trailing spaces require TRIM) | ✅ Secondary |
| `bk_active_flag` | varchar(1) | Active BK flag | {"Y", "N", ""}, NULL rate 0.65% | Raw ingest → referenced in generating `bankruptcy` | ✅ Secondary |
| `bk_chapter_code` | varchar | BK chapter code | {"07", "13", "11", ""}, NULL rate 0.65% | Raw ingest | ✅ Secondary |
| `reo_start_date` | date | REO start date | All NULL (240,608 rows) | Raw ingest (no REO records in current dataset) | — |
| `forbearance_flag` | varchar | Forbearance flag | {"N", "Y"}, no NULLs | Raw ingest → referenced in generating `lm_flag` | ✅ Secondary |
| `modification_type` | varchar | Loan modification type | {"", "NON-HAMP"}, NULL rate 0.64% | Raw ingest | ✅ Secondary |

**Part B — Field Statistics**

| Field | Example Values | Statistics |
|-------|----------------|------------|
| `delq_status_mba` | "Current", "DQ 30", "Service Release" | 240,608 rows · NULL rate 0% · 8 values · Current(158,272=65.8%), DQ 30(46,575=19.4%), Service Release(19,377=8.1%), Paid in Full(5,497=2.3%), DQ 60(4,800=2.0%) |
| `mba_delq_status_paystring` | "CCCCCCCC", "777777..." | 240,608 rows · NULL rate 0% · 1,082 unique strings |
| `fcl_active_flag` | "N", "Y" | 240,608 rows · NULL rate 0% · N(240,072=99.8%), Y(536=0.2%) |
| `fc_hold_flag` | "N   ", "Y   " | 240,608 rows · NULL rate 0% · N(240,467=99.9%), Y(141=0.1%) — note trailing spaces |
| `bk_active_flag` | "Y", "N", "" | 240,608 rows · NULL rate 0.65% · ""(237,717=98.8%), Y(1,051=0.4%), N(274=0.1%) |
| `bk_chapter_code` | "07", "13", "11" | 240,608 rows · NULL rate 0.65% · ""(237,717), 07(843=0.35%), 13(268), 11(205) |
| `reo_start_date` | — | 240,608 rows · **NULL rate 100%** — no REO records in current dataset |
| `forbearance_flag` | "N", "Y" | 240,608 rows · NULL rate 0% · N(239,875=99.7%), Y(733=0.3%) |
| `modification_type` | "", "NON-HAMP" | 240,608 rows · NULL rate 0.64% · ""(234,627=97.7%), NON-HAMP(4,441=1.8%) |

**`delq_status_mba` → `delinq` SLS mapping (8 raw values):**

| Raw Value | Standard `delinq` |
|-----------|-------------------|
| `Current` | `C` |
| `DQ 30` | `D30` |
| `DQ 60` | `D60` |
| `DQ 90` | `D90` |
| `DQ 120+` | `D120P` |
| `Foreclosure` / `FCL` | `FCL` |
| `REO` | `REO` |
| `Paid in Full` / `Service Release` | `P` |
| `Bankruptcy` | days360-based + `bankruptcy='Y'` |

---

### 3.2 `portfcldaily` — Foreclosure Detail Table

**Description:** SLS foreclosure process tracking table. Records key milestone dates, FCL type (JUD=Judicial / POS=Non-Judicial), and day-count metrics for loans in foreclosure. Row count is small (2,056 rows) because only loans with active FCL records are included.

**Fully qualified name:** `sls.portfcldaily` | **Total rows:** 2,056  
**Loan ID field:** `account_number` (int, 9 unique values) | **Date field:** `data_as_of_date` (date, 2023-03-29 ~ 2024-08-07, 356 distinct dates)  
**Unique loans:** 9

**Part A — Field Definitions**

| Field | Type | Meaning | Value Range | Calculation Logic | FCL Related |
|-------|------|---------|-------------|-------------------|-------------|
| `fcl_active_flag` | varchar(255) | **Active FCL flag** | {"Y", "N"}, no NULLs | Raw ingest → mapped to `fcl_flag` | ✅ Primary |
| `fcl_approval_date` | date | FCL approval date | 2022-06-09 ~ 2024-04-18, no NULLs | Raw ingest | ✅ Primary |
| `fcl_referred_to_attorney_date` | date | Attorney referral date | 2022-06-09 ~ 2024-04-18, no NULLs | Raw ingest → flows into `port.fcl_stage_info.referral_start_date` | ✅ Primary |
| `fcl_first_legal_action_date` | date | First legal action date | 2023-04-25 ~ 2024-03-29, or NULL | Raw ingest → flows into `port.fcl_stage_info.legal_start_date` | ✅ Primary |
| `fcl_service_complete_date` | date | Service of process completion date | All NULL (current dataset) | Raw ingest (no records yet) | ✅ Primary |
| `fcl_judgement_entered_date` | date | Judgment entered date | All NULL (current dataset) | Raw ingest (no records yet) | ✅ Primary |
| `fcl_sale_scheduled_date` | date | Scheduled sale date | 2023-07-27 ~ 2023-09-14, or NULL | Raw ingest → flows into `port.fcl_stage_info.sale_start_date` | ✅ Primary |
| `fcl_sale_held_date` | date | Actual sale date | All NULL (current dataset) | Raw ingest (no records yet) | ✅ Primary |
| `fcl_days` | int | Days in foreclosure | 0 ~ 790, no NULLs | Raw ingest (servicer-calculated) | ✅ Primary |
| `fcl_days_variance_to_fnma` | int | Actual days vs. Fannie Mae benchmark variance | All NULL (current dataset) | Raw ingest (no records yet) | ✅ Secondary |
| `fcl_current_status_desc` | text | Current FCL stage description | {"CLOSED", "REFFERED TO ATTORNEY", "SALE SCHEDULED"}, no NULLs | Raw ingest (note: original data has typo "REFFERED") | ✅ Primary |
| `fcl_type_code` | varchar(255) | FCL type code | {"POS" (Non-Judicial), "JUD" (Judicial)}, no NULLs | Raw ingest → flows into `port.basic_data_loan_fcl.judicial` | ✅ Secondary |
| `fcl_sale_amount` | decimal(32,16) | Sale proceeds | All 0 (no completed sales yet) | Raw ingest | ✅ Secondary |
| `fcl_bid_amount` | decimal(32,16) | Bid amount | All 0 (no records yet) | Raw ingest | ✅ Secondary |

**Part B — Field Statistics**

| Field | Example Values | Statistics |
|-------|----------------|------------|
| `fcl_active_flag` | "Y", "N" | 2,056 rows · NULL rate 0% · N(1,520=73.9%), Y(536=26.1%) |
| `fcl_approval_date` | 2022-06-09, 2023-05-12 | 2,056 rows · NULL rate 0% · 9 dates |
| `fcl_referred_to_attorney_date` | 2022-06-09, 2023-05-02 | 2,056 rows · NULL rate 0% · 9 dates |
| `fcl_first_legal_action_date` | 2023-04-25, 2023-12-06 | 2,056 rows · NULL rate 73.6% · 3 dates |
| `fcl_service_complete_date` | — | 2,056 rows · **NULL rate 100%** |
| `fcl_judgement_entered_date` | — | 2,056 rows · **NULL rate 100%** |
| `fcl_sale_scheduled_date` | 2023-09-14, 2023-07-27 | 2,056 rows · NULL rate 85.8% · 2 dates |
| `fcl_sale_held_date` | — | 2,056 rows · **NULL rate 100%** |
| `fcl_days` | 76, 83, 70, 69 | 2,056 rows · NULL rate 0% · 701 distinct values · range 0~790 days |
| `fcl_days_variance_to_fnma` | — | 2,056 rows · **NULL rate 100%** |
| `fcl_current_status_desc` | "REFFERED TO ATTORNEY", "CLOSED" | 2,056 rows · NULL rate 0% · 3 descriptions (including original typo) |
| `fcl_type_code` | "POS", "JUD" | 2,056 rows · NULL rate 0% · POS(1,507=73.3%), JUD(549=26.7%) |
| `fcl_sale_amount` | 0 | 2,056 rows · NULL rate 0% · **all 0** (no completed sales) |
| `fcl_bid_amount` | 0 | 2,056 rows · NULL rate 0% · **all 0** |

---

### 3.3 `portbkdaily` — Bankruptcy Detail Table

**Description:** SLS bankruptcy process tracking table. Records basic information for loans with active bankruptcy records. Small row count (1,616 rows) — only loans with BK records are included.

**Fully qualified name:** `sls.portbkdaily` | **Total rows:** 1,616  
**Loan ID field:** `account_number` (int, 7 unique values) | **Date field:** `data_as_of_date` (date, 2023-03-15 ~ 2024-08-07, 365 distinct dates)

**Part A — Field Definitions**

| Field | Type | Meaning | Value Range | Calculation Logic | FCL Related |
|-------|------|---------|-------------|-------------------|-------------|
| `bk_active_flag` | varchar | **Active BK flag** | {"Y", "N"}, no NULLs | Raw ingest → referenced in generating `bankruptcy` auxiliary flag | ✅ Secondary |
| `bk_chapter_code` | varchar(255) | BK chapter code | {"07", "13", "11"}, no NULLs | Raw ingest → flows into `port.basic_data_loan_foreclosure_bankruptcy.chapter` | ✅ Secondary |
| `bk_filed_date` | date | Bankruptcy filing date | 2021-03-07 ~ 2024-03-25, no NULLs | Raw ingest | ✅ Secondary |
| `bk_discharged_flag` | varchar | Discharge flag | {"Y", "N"}, no NULLs | Raw ingest | ✅ Secondary |
| `fcl_days_in_bankruptcy` | varchar(255) | FCL days spent in bankruptcy state | Empty string (92.6%) or numeric string, no NULLs | Raw ingest (empty string = not yet calculated) | ✅ Secondary |
| `bk_cramdown_flag` | varchar | Cramdown flag | {"N"} (100%), no NULLs | Raw ingest | — |

**Part B — Field Statistics**

| Field | Example Values | Statistics |
|-------|----------------|------------|
| `bk_active_flag` | "Y", "N" | 1,616 rows · NULL rate 0% · Y(1,060=65.6%), N(556=34.4%) |
| `bk_chapter_code` | "07", "13", "11" | 1,616 rows · NULL rate 0% · 07(963=59.6%), 13(447=27.7%), 11(206=12.7%) |
| `bk_filed_date` | 2023-08-23, 2023-03-13 | 1,616 rows · NULL rate 0% · 7 dates · range 2021-03-07~2024-03-25 |
| `bk_discharged_flag` | "N", "Y" | 1,616 rows · NULL rate 0% · N(1,197=74.1%), Y(419=25.9%) |
| `fcl_days_in_bankruptcy` | "", "336", "337" | 1,616 rows · NULL rate 0% · 121 values · ""(1,496=92.6%), remainder are day counts |
| `bk_cramdown_flag` | "N" | 1,616 rows · NULL rate 0% · **all "N"** |

---

### 3.4 `portlmdaily` — Loss Mitigation Detail Table

**Description:** SLS loss mitigation process tracking table (the largest SLS sub-table with 179 fields in the raw schema). This document covers only the FCL-relevant key LM fields.

**Fully qualified name:** `sls.portlmdaily` | **Total rows:** 21,283  
**Loan ID field:** `account_number` (bigint, 34 unique values) | **Date field:** `data_as_of_date` (datetime, 2023-04-01 ~ 2024-08-07)

**Part A — Field Definitions**

| Field | Type | Meaning | Value Range | Calculation Logic | FCL Related |
|-------|------|---------|-------------|-------------------|-------------|
| `loss_mit_evaluation_status` | varchar(255) | **LM evaluation status** (primary status field) | 25 status descriptions, no NULLs | Raw ingest → generates `lm_flag` (Pending-type → Y, Resolved-type → N) | ✅ Primary |
| `loss_mit_workout_type_code_desc` | text | LM workout type description | 9 descriptions (including empty string), no NULLs | Raw ingest → flows into `port.basic_data_loan_foreclosure_loss_mitigation` | ✅ Secondary |
| `loss_mit_mod_effective_date` | datetime | Loan modification effective date | 2023-10-01 ~ 2024-06-01, or NULL | Raw ingest → flows into `port.basic_data_loan_foreclosure_loss_mitigation` | ✅ Secondary |
| `loss_mit_mod_terms_modified_interest_rate_percent` | decimal(32,16) | Modified interest rate (%) | 2.63% ~ 8.25%, or NULL | Raw ingest (LM negotiation result) | ✅ Secondary |
| `workout_completed_date` | datetime | LM workout completion date | 2024-04-26 ~ 2024-06-07, or NULL | Raw ingest | ✅ Secondary |

**Part B — Field Statistics**

| Field | Example Values | Statistics |
|-------|----------------|------------|
| `loss_mit_evaluation_status` | "Resolved-Withdrawn", "Resolved-Complied", "Pending-Compliance" | 21,283 rows · NULL rate 0% · 25 values · Resolved-Withdrawn(6,705=31.5%), Resolved-Complied(3,871=18.2%), Resolved-BorrowerDisengaged(3,346=15.7%), Resolved-DidNotComply(2,586=12.2%), Pending-Compliance(1,375=6.5%) |
| `loss_mit_workout_type_code_desc` | "Trial Period Plan", "Modification" | 21,283 rows · NULL rate 0% · 9 values (including empty string) |
| `loss_mit_mod_effective_date` | 2024-02-01, 2024-04-01 | 21,283 rows · NULL rate 65.6% · 9 dates · range 2023-10-01~2024-06-01 |
| `loss_mit_mod_terms_modified_interest_rate_percent` | 7.13%, 4.00%, 8.25% | 21,283 rows · NULL rate 59.9% · 16 rate values · range 2.63%~8.25% |
| `workout_completed_date` | 2024-04-26, 2024-06-07 | 21,283 rows · NULL rate 96.4% · 3 dates |

---

## 4. Carrington (`carrington` schema)

**Database:** MySQL (`bridg004-db-prod`)  
**Schema:** `carrington`  
**File format:** `.xlsx` or `.csv`  
**Date range:** 2023-11-05 ~ 2026-05-19

> **Important:** The original documentation incorrectly listed `status` and `foreclosure_status_code` as fields — **these do not exist** in the current database. The actual FCL status fields are `loan_status` (text description) and `fcl_flag` ("Active"). Carrington uses a **single-table design** — all FCL, BK, LM, and asset information is consolidated in one table (~200 fields).

---

### 4.1 `portcarrington` — Carrington Consolidated Table

**Description:** Carrington servicer consolidated loan status snapshot (single-table design). Combines FCL, BK, LM, and basic asset information in one wide table (~200 fields). FCL status is expressed via the three-field combination: `loan_status` + `fcl_flag` + `fcl_status`.

**Fully qualified name:** `carrington.portcarrington` | **Total rows:** 299,071  
**Loan ID field:** `loanid` (varchar(100), 719 unique values) | **Date field:** `snap_shot_date` (date, 2023-11-05 ~ 2026-05-19, 892 distinct dates)

**Part A — Field Definitions (FCL-relevant fields)**

| Field | Type | Meaning | Value Range | Calculation Logic | FCL Related |
|-------|------|---------|-------------|-------------------|-------------|
| `loanid` | varchar(100) | Loan ID (Bridger) | 719 unique values, no NULLs | Raw ingest | ✅ Primary |
| `snap_shot_date` | date | Data date (snapshot date) | 2023-11-05 ~ 2026-05-19 | Raw ingest | — |
| `loan_status` | varchar(255) | **Comprehensive loan status** (includes FCL/REO/LM etc.) | 16 text values, no NULLs | Raw ingest → `portdaily_config.py` CASE-WHEN maps to `delinq` (e.g. "Foreclosure"→FCL, "REO"→REO, "Completed Payoff"→P) | ✅ Primary |
| `fcl_flag` | varchar(50) | **Active foreclosure flag** | {"Active"} or NULL | Raw ingest → mapped to `fcl_flag='Y'` | ✅ Primary |
| `fcl_status` | varchar(50) | FCL stage status | 7 text values ("1. First Legal Pending" etc.) or NULL | Raw ingest → flows into `port.basic_data_loan_fcl` | ✅ Primary |
| `fcl_sub_status` | varchar(50) | FCL sub-status | 18 descriptions ("Title Summary","Pending First Legal" etc.) or NULL | Raw ingest | ✅ Secondary |
| `fcl_referral_date` | date | FCL attorney referral date | 2023-09-22 ~ 2026-03-17, or NULL | Raw ingest | ✅ Primary |
| `fcl_scheduled_sale_date` | date | Scheduled sale date | 2023-12-05 ~ 2026-01-16, or NULL | Raw ingest | ✅ Primary |
| `fcl_sale_held_date` | date | Actual sale date | 2025-01-23 ~ 2026-01-16, or NULL | Raw ingest | ✅ Primary |
| `fcl_active_hold` | varchar(50) | Active hold indicator | {"Yes", "No"} or NULL | Raw ingest | ✅ Secondary |
| `fcl_latest_hold_reason` | varchar(255) | Latest hold reason | 7 descriptions ("BK Hold","Special Handling Loan Alert" etc.) or NULL | Raw ingest | ✅ Secondary |
| `lm_flag` | varchar(50) | Loss mitigation flag | {"Active", "Completed/Cancelled"} or NULL | Raw ingest → `CASE WHEN lm_flag='Active' THEN 'Y' ELSE 'N'` | ✅ Primary |
| `bk_flag` | varchar(50) | Bankruptcy flag | {"Active", "Completed/Cancelled"} or NULL | Raw ingest → generates `bankruptcy` | ✅ Secondary |
| `bk_chapter` | decimal(32,16) | BK chapter | {7.0, 13.0} or NULL | Raw ingest | ✅ Secondary |
| `covid_forbearance_flag` | varchar(255) | COVID forbearance flag | {"N"} or NULL | Raw ingest (legacy field, mostly NULL) | — |

**Part B — Field Statistics**

| Field | Example Values | Statistics |
|-------|----------------|------------|
| `loan_status` | "CUR", "0-29", "Foreclosure", "Bankruptcy - Performing" | 299,071 rows · NULL rate 0% · 16 values · CUR(199,288=66.6%), 0-29(59,622=19.9%), Completed Payoff(17,176=5.7%), 30-59(8,862=3.0%), Loss Mitigation(4,699=1.6%), Foreclosure(2,077=0.7%), REO(286=0.1%) |
| `fcl_flag` | "Active" | 299,071 rows · NULL rate 98.9% · non-NULL: 3,314 rows · all "Active" |
| `fcl_status` | "1. First Legal Pending", "2. First Legal Filed" | 299,071 rows · NULL rate 98.8% · 7 values · "1. First Legal Pending"(1,651=44%), "2. First Legal Filed"(1,150=31%), "3. Judgement Entered..."(398=11%), "5. Sales Held"(305=8%) |
| `fcl_sub_status` | "Title Summary", "Pending First Legal", "Judgment Entered" | 299,071 rows · NULL rate 98.8% · 18 values |
| `fcl_referral_date` | 2024-01-15, 2023-09-22 | 299,071 rows · NULL rate 98.8% · 22 dates |
| `fcl_scheduled_sale_date` | 2025-06-30, 2026-01-16 | 299,071 rows · NULL rate 99.8% · 6 dates |
| `fcl_sale_held_date` | 2025-01-23, 2026-01-16 | 299,071 rows · NULL rate 99.8% · 2 dates |
| `fcl_active_hold` | "Yes", "No" | 299,071 rows · NULL rate 98.8% · Yes(1,983=53%), No(1,724=47%) |
| `fcl_latest_hold_reason` | "BK Hold", "Special Handling Loan Alert" | 299,071 rows · NULL rate 99.9% · 7 descriptions |
| `lm_flag` | "Active", "Completed/Cancelled" | 299,071 rows · NULL rate 72.8% · Completed/Cancelled(76,654=94.2%), Active(4,702=5.8%) |
| `bk_flag` | "Active", "Completed/Cancelled" | 299,071 rows · NULL rate 91.3% · Completed/Cancelled(23,952=91.8%), Active(2,139=8.2%) |
| `bk_chapter` | 7.0, 13.0 | 299,071 rows · NULL rate 91.3% · 13.0(15,658=60%), 7.0(10,433=40%) |
| `covid_forbearance_flag` | "N" | 299,071 rows · NULL rate 96.4% · non-NULL: 10,704 rows · all "N" |

**`loan_status` complete value distribution (all 16 values):**

| loan_status Value | Row Count | % | Mapped `delinq` |
|-------------------|-----------|---|-----------------|
| `CUR` | 199,288 | 66.6% | `C` |
| `0-29` | 59,622 | 19.9% | `D30` |
| `Completed Payoff` | 17,176 | 5.7% | `P` |
| `30-59` | 8,862 | 3.0% | `D60` |
| `Loss Mitigation` | 4,699 | 1.6% | days360-based + lm_flag=Y |
| `60-89` | 2,335 | 0.8% | `D60` |
| `Foreclosure` | 2,077 | 0.7% | `FCL` |
| `Bankruptcy - Performing` | 1,966 | 0.7% | days360-based + bankruptcy=Y |
| `Completed Short Sale` | 1,237 | 0.4% | `P` |
| `90-119` | 642 | 0.2% | `D90` |
| `120+` | 422 | 0.1% | `D120P` |
| `REO` | 286 | 0.1% | `REO` |
| `Completed REO Sale` | 267 | 0.1% | `REO` |
| `Bankruptcy - Non-Performing` | 129 | 0.04% | days360-based + bankruptcy=Y |
| `Foreclosure/Bankruptcy - Non-Performing` | 44 | 0.01% | `FCL` + bankruptcy=Y |
| `3rd Party Sale` | 19 | 0.006% | `P` |

---

## 5. MRC (`mrc` schema)

**Database:** MySQL (`bridg004-db-prod`)  
**Schema:** `mrc`  
**File format:** `.txt`  
**Date range:** 2026-04-03 ~ 2026-04-29 (minimal current-month data only)

---

### 5.1 `portmrcforeclosure` — MRC Foreclosure Table

**Description:** MRC servicer foreclosure process tracking table. Schema is comprehensive (47 fields) covering milestone dates and outcomes across FCL stages — but the current database has extremely few records (17 rows only) and most fields are NULL.

**Fully qualified name:** `mrc.portmrcforeclosure` | **Total rows:** 17  
**Loan ID field:** `loanid` (varchar(24), 1 unique value) | **Date field:** `dataasof` (date, 2026-04-03 ~ 2026-04-29, 17 distinct dates)

**Part A — Field Definitions (core fields)**

| Field | Type | Meaning | Value Range | Calculation Logic | FCL Related |
|-------|------|---------|-------------|-------------------|-------------|
| `loanid` | varchar(24) | Loan ID (Bridger) | 1 unique value (700084240000002), no NULLs | Raw ingest | ✅ Primary |
| `dataasof` | date | Data date | 2026-04-03 ~ 2026-04-29 | Raw ingest | — |
| `fc_flag` | char(1) | **Active FCL flag** | {"N"} or NULL | Raw ingest → mapped to `fcl_flag` | ✅ Primary |
| `fc_status` | varchar(255) | FCL status | All NULL (current dataset) | Raw ingest | ✅ Primary |
| `fc_milestone` | varchar(255) | FCL milestone | All NULL (current dataset) | Raw ingest | ✅ Primary |
| `referral_date` | date | Attorney referral date | All NULL (current dataset) | Raw ingest | ✅ Primary |

**Part B — Field Statistics**

| Field | Example Values | Statistics |
|-------|----------------|------------|
| `fc_flag` | "N" | 17 rows · NULL rate 0% · **all "N"** (no active FCL currently) |
| `fc_status` | — | 17 rows · **NULL rate 100%** |
| `fc_milestone` | — | 17 rows · **NULL rate 100%** |

MRC also maintains a full 17-category file/table system: ARM, BANKRUPTCY, CLAIMS_PIPELINE, FORECLOSURE, LOAN, MOD_COMPLETE, REO, SHORT_SALE, etc.

---

## 6. FCI / Selene (`fci` / `selene` schema)

**Database:** MySQL (`bridg004-db-prod`)  
**Schema:** `fci` (FCI) and `selene` (Selene)  
**File formats:** FCI=`.xlsx`, Selene=`.csv`  
**Field definitions:** No standalone DDL files; fields inferred from SQL in `portmonth_config.py`

FCI and Selene FCL fields are extracted via per-servicer SQL directly in `portmonth_config.py` — field names and formats vary by servicer and are mapped to the standard `delinq` at the ETL layer.

---

## 7. Cross-Servicer Field Comparison

| Standard Field | Newrez | SLS | Carrington | MRC |
|---------------|--------|-----|------------|-----|
| **Loan ID field** | `loanid` (varchar) | `account_number_investor` (varchar) | `loanid` (varchar) | `loanid` (varchar) |
| **Data date field** | `dataasof` | `dataasofdate` / `data_as_of_date` | `snap_shot_date` | `dataasof` |
| **Raw delinq status** | `delinquency_status_mba` | `delq_status_mba` | `loan_status` | — |
| **Active FCL flag** | `activefcflag` (int 0/1) | `fcl_active_flag` (varchar Y/N) | `fcl_flag` (varchar "Active"/NULL) | `fc_flag` (char N) |
| **FCL stage** | `fcstage` (varchar) | `fcl_current_status_desc` (text) | `fcl_status` (varchar) | `fc_milestone` (varchar) |
| **Days in FCL** | `daysinfc` (int) | `fcl_days` (int) | — | — |
| **Hold reason** | `fchold1description` (varchar) | — | `fcl_active_hold` + `fcl_latest_hold_reason` | — |
| **Active BK flag** | `activebkflag` (int 0/1) | `bk_active_flag` (varchar Y/N) | `bk_flag` (varchar "Active"/NULL) | — |
| **BK chapter** | `bkchapter` (int 7/11/13) | `bk_chapter_code` (varchar "07"/"13"/"11") | `bk_chapter` (decimal 7.0/13.0) | — |
| **Active LM flag** | `activelmflag` (int 0/1) | `loss_mit_evaluation_status` (varchar) | `lm_flag` (varchar "Active"/NULL) | — |

---

## 8. Loan ID Mapping Table

**Table:** `port.portidmap` / `port.portloanidmap` (Redshift)

| Field | Meaning |
|-------|---------|
| `loanid` | Internal Bridger loan ID (primary key) |
| `sellerloanid` | Seller loan ID |
| `currentservicerloanidnew` | Current servicer loan ID |
| `slsloanid` | SLS-specific loan ID |
| `encompassloanidsold` | Encompass system loan ID |

Used for cross-servicer reconciliation and ID translation.

---

## 9. Known Limitations

| Limitation | Details |
|-----------|---------|
| No standalone DDL for FCI / Selene | Field definitions must be inferred from SQL in `portmonth_config.py` |
| SLS → Newrez switch on 2024-07-05 | Historical data has a transition point; time-range-aware queries must UNION both sides |
| SLS data ends at 2024-08-07 | No further SLS updates after the switch; Newrez takes over |
| Carrington single-table design | Cannot precisely distinguish BK/LM sub-states; only `loan_status` + `lm_flag` + `bk_flag` dimensions |
| VASP mapping logic not explicit in code | Appears to be an operational override (DB evidence: 19 VASP records, all from Newrez, `delinquency_status_mba` values are not uniform) |
| MRC data is minimal | Only 17 rows of current-month data; most fields (fc_status, fc_milestone, etc.) are NULL |
| Newrez tables renamed from `portshellpoint*` to `portnewrez*` | DDL file `shellpoint_daily.sql` uses historical names; live tables in `newrez` schema use `portnewrez*` prefix |

---

## Chinese Version

`docs/zh/01_source_data.md`
