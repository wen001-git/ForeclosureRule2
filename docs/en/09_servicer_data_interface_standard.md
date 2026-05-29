# 09 — Servicer Data Interface Standard

---

## Document Information

| Field | Content |
|-------|---------|
| **Purpose** | Define the field specifications, data dictionary, and delivery format that each servicer must follow when submitting loan data to the new system. Serves as the authoritative basis for issuing formal field-completion requests to servicers. |
| **Problem solved** | The current system lacks a unified standard for servicer data ingestion: field names differ across servicers, enumeration values are inconsistent, and critical status fields are missing — making FCL / LM / BK status derivation unreliable. |
| **Scope** | 8 active servicers — SLS / Newrez / Carrington / Selene / MRC / Arvest / CapeCodFive / FCI |
| **System** | New system interface design layer (pre-specification for PrefectFlow rewrite) |

**Target audience:** Data product managers · Business analysts · New system ETL architects · Servicer onboarding engineers · Compliance reviewers

**Dependencies:**
- `08_servicer_fcl_field_mapping.md` — Per-servicer current-state analysis (empirical basis for this document)
- `07_fcl_lineage_and_rules.md` — Existing ETL implementation details (new system design reference)
- `01_source_data.md` — Raw table structure (field source index)

**Revision history:**

| Date | Author | Version | Changes |
|------|--------|---------|---------|
| 2026-05-25 | AI Agent (Claude Sonnet 4.6) | v2 | Added rationale note to Group E explaining why `bankruptcy_flag` is independent of MBA `Bankruptcy` enum (mutually exclusive values cannot express FCL+BK coexistence) |
| 2026-05-25 | AI Agent (Claude Sonnet 4.6) | v1 | Initial version, based on doc 08 DB-verified data |

---

## 1. Purpose and Scope

This document defines the **servicer data ingestion standard** for the new system — the target state.

| Document | Perspective | Role |
|----------|-------------|------|
| **doc 08** (current state) | "What servicers provide today" | Gap analysis, issue identification |
| **doc 09** (this standard) | "What the new system requires" | Interface design, formal request basis |

### Priority Definitions

| Priority | Meaning | System behavior |
|----------|---------|----------------|
| **P0 Required** | Missing this field means the system cannot correctly process the loan | Reject ingestion or flag as data quality error |
| **P1 Recommended** | Missing this field degrades key business analysis (FCL timeline, LM type indistinguishable) | Accept but flag insufficient data completeness |
| **P2 Optional** | Providing this field enables more granular analysis | Use if present, ignore if absent |

---

## 2. Four-Dimensional Status Model (Core Design Principles)

### 2.1 Four Independent Loan Status Dimensions

US mortgage loan status consists of four **fully orthogonal** dimensions that cannot substitute for one another:

```
Dimension A — Delinquency (severity of missed payments)
              Current → DQ30 → DQ60 → DQ90 → DQ120P

Dimension B — FCL (Foreclosure)      Has legal action been initiated?
              N (not in foreclosure) / Y (foreclosure proceedings active)

Dimension C — LM (Loss Mitigation)   Is there an active remediation plan?
              N (no LM) / Y (forbearance / modification / repayment plan / etc.)

Dimension D — BK (Bankruptcy)        Has the borrower filed for bankruptcy?
              N (no bankruptcy) / Y (automatic stay in effect)
```

**A single loan can simultaneously occupy multiple dimensions:**

| Example | Delinquency | FCL | LM | BK | Business meaning |
|---------|-------------|-----|----|----|-----------------|
| Typical foreclosure | `D120P` | `Y` | `N` | `N` | Severely delinquent; legal proceedings initiated |
| FCL with negotiation | `FCL` | `Y` | `Y` | `N` | In foreclosure while simultaneously negotiating forbearance |
| Bankruptcy protection | `D90` | `Y` | `N` | `Y` | Automatic stay has temporarily halted foreclosure |
| Normal performing loan | `Current` | `N` | `N` | `N` | On-time payments; no special status |

### 2.2 Key Principles

1. **FCL is a legal status, not a delinquency degree** — `FCL` can never be inferred from `days360`. It requires an explicit servicer-provided flag. (120 days past due ≠ foreclosure; FCL requires a formal legal action trigger.)

2. **MBA standard unified** — `delinquency_status` must use MBA standard enumeration text; numeric DPD strings (e.g. `'29.0'`) are not acceptable.

3. **Dual-file model** — Main daily/monthly report (current status snapshot) + FCL specialty report (detailed timeline), both submitted in parallel.

4. **Four dimensions transmitted independently** — Each dimension has its own dedicated fields. Multiple statuses must not be compressed into a single text field (e.g. `'Foreclosure / Perf BK'` forces fragile text parsing).

---

## 3. Standard Field Catalog

> **Format note**: Field names below are recommended standard names. Servicers' actual field names may differ, but value domains must conform to this specification. Mapping configurations are applied at system ingestion time.

### Group A — Loan and Report Identification

| Standard field name | Type | Priority | Allowed values / format | Notes |
|--------------------|------|----------|------------------------|-------|
| `servicer_loan_id` | VARCHAR(50) | **P0** | Any string, no spaces | Servicer-side unique loan number; JOINed with system `loan_id` |
| `deal_id` | VARCHAR(50) | **P0** | Any string | Portfolio / Deal identifier |
| `report_date` | DATE | **P0** | `YYYY-MM-DD` | Data as-of date |

---

### Group B — Delinquency Status (MBA Standard)

| Standard field name | Type | Priority | Allowed values | Notes |
|--------------------|------|----------|---------------|-------|
| `delinquency_status` | VARCHAR ENUM | **P0** | See allowed values table below | MBA standard delinquency status text — **numeric DPD strings are not permitted** (see ⚠️ note) |
| `next_payment_due_date` | DATE | **P0** | `YYYY-MM-DD` | Next payment due date; used for days360 fallback calculation |
| `days_past_due` | INTEGER | P1 | 0–999 | Numeric DPD; cross-validated against `delinquency_status` |

**`delinquency_status` allowed values (all accepted by the system; mapped to internal codes):**

| Allowed value | Maps to internal code | Notes |
|--------------|----------------------|-------|
| `Current` | `C` | 0–29 DPD, performing |
| `1-29 DPD` | `C` | Granular sub-classification (used by Newrez etc.) |
| `30-59 DPD` | `D30` | |
| `60-89 DPD` | `D60` | |
| `90-119 DPD` | `D90` | |
| `120-149 DPD` | `D120P` | |
| `150-179 DPD` | `D120P` | |
| `180+ DPD` | `D120P` | |
| `Foreclosure` | `FCL` | |
| `REO` | `REO` | |
| `PaidOff` / `Full Payoff` / `Paid in Full` | `P` | |
| `Bankruptcy` / `Performing Bankruptcy` / `Non-Performing Bankruptcy` | DPD-based + `bankruptcy='Y'` | Bankruptcy must also be transmitted via `bankruptcy_flag` |
| `REO Sale` / `3rd Party Sale` | `P` | Disposition complete |
| `Service Release` | Special handling | Loan servicing rights transferred |

> ⚠️ **Prohibited value format**: `'29.0'`, `'30.0'`, `'90.0'` and similar numeric strings (current CapeCodFive issue — causes FCL to be permanently undetectable).

---

### Group C — FCL Foreclosure Status

| Standard field name | Type | Priority | Allowed values | Notes |
|--------------------|------|----------|---------------|-------|
| `foreclosure_flag` | CHAR(1) | **P0** | `Y` / `N` | Whether loan is in active foreclosure proceedings (legal action formally initiated) |
| `foreclosure_type` | VARCHAR ENUM | P1 | `Judicial` / `NonJudicial` | Impacts timeline expectations (judicial: 12–36 months; non-judicial: 2–6 months) |
| `foreclosure_stage` | VARCHAR ENUM | P1 | `Referral` / `FirstLegal` / `Service` / `Judgment` / `Sale` | Current stage within FCL proceedings |
| `foreclosure_start_date` | DATE | P1 | `YYYY-MM-DD` | Earliest FCL initiation date (typically attorney referral date) |
| `referral_date` | DATE | P1 | `YYYY-MM-DD` | Date referred to attorney / legal entity |
| `sale_date_scheduled` | DATE | P2 | `YYYY-MM-DD` | Scheduled auction date |
| `sale_date_actual` | DATE | P2 | `YYYY-MM-DD` | Actual auction date (populated after FCL completion) |
| `fcl_exit_type` | VARCHAR ENUM | P2 | `3rdPartySale` / `REO` / `Reinstatement` / `ShortSale` / `DeedInLieu` | How foreclosure ended |

> **Minimum requirement**: The new system only needs `foreclosure_flag = 'Y'` to correctly label FCL status. P1/P2 fields support timeline analysis and risk forecasting.

> **FCL-Hold note**: MBA standard does not include an `FCL-Hold` status. Even when foreclosure proceedings are on hold, MBA still reports the loan as `Foreclosure`. To distinguish "foreclosure paused" from "foreclosure actively progressing," you must rely on Group F's `hold_flag` + `hold_reason` fields — it cannot be inferred from `delinquency_status`.

---

### Group D — LM Loss Mitigation Status

| Standard field name | Type | Priority | Allowed values | Notes |
|--------------------|------|----------|---------------|-------|
| `lm_flag` | CHAR(1) | **P0** | `Y` / `N` | Whether loan is in an active LM plan |
| `lm_type` | VARCHAR ENUM | P1 | `Forbearance` / `Modification` / `RepaymentPlan` / `TrialPlan` / `ShortSale` / `DeedInLieu` | LM plan type (distinguishes temporary vs permanent solutions) |
| `lm_start_date` | DATE | P1 | `YYYY-MM-DD` | LM plan start date |
| `lm_end_date` | DATE | P1 | `YYYY-MM-DD` | LM plan expiration date (**critical**: renewal decision is a key business trigger) |
| `lm_status` | VARCHAR ENUM | P2 | `Active` / `Trial` / `Completed` / `Denied` / `Expired` | Current LM plan status |

**Six LM Types:**

| LM Type | Business meaning | Typical duration | Outcome |
|---------|----------------|-----------------|---------|
| **Forbearance** | Temporarily suspend or reduce payments; arrears repaid later | 3–12 months | Temporary; may convert to Modification |
| **Loan Modification** | Permanently change interest rate / term / principal | Permanent | Most comprehensive LM solution |
| **Repayment Plan** | Pay off arrears in installments alongside regular payments | 3–6 months | Runs parallel to regular payment schedule |
| **Trial Period Plan** | Probationary period before permanent modification takes effect | 3 months | Pass trial → Permanent Modification |
| **Short Sale** | Sell property below loan balance; remaining balance forgiven | Months | Loan closes; `delinq → P` |
| **Deed in Lieu** | Borrower voluntarily transfers property to lender | Months | Loan closes; avoids foreclosure auction |

---

### Group E — Bankruptcy Status

| Standard field name | Type | Priority | Allowed values | Notes |
|--------------------|------|----------|---------------|-------|
| `bankruptcy_flag` | CHAR(1) | P1 | `Y` / `N` | Independent bankruptcy flag (**currently all 8 servicers lack this as a standalone field**; all infer it from delinquency status text) |
| `bankruptcy_chapter` | INTEGER | P1 | `7` / `11` / `13` | Bankruptcy chapter (affects automatic stay scope and timeline) |
| `bankruptcy_filing_date` | DATE | P1 | `YYYY-MM-DD` | Bankruptcy petition filing date |
| `bankruptcy_discharge_date` | DATE | P2 | `YYYY-MM-DD` | Bankruptcy discharge / dismissal date |

> **Why is an independent field needed, rather than relying on the MBA `Bankruptcy` enum value?** MBA `delinquency_status` is a single-select, mutually exclusive field — when a loan is simultaneously in FCL and BK, the servicer can only report one value (reporting `Foreclosure` loses the BK information; reporting `Bankruptcy` loses the FCL information). An independent `bankruptcy_flag` can coexist with `foreclosure_flag`, capturing the common mixed-status scenario: "FCL proceedings paused due to BK automatic stay."

> **Chapter 7 vs Chapter 13**: Chapter 7 (liquidation, 3–6 months) vs Chapter 13 (reorganization, 3–5 year repayment plan). FCL proceedings are protected by automatic stay during bankruptcy and must be handled separately.

---

### Group F — Hold / Pause Status

| Standard field name | Type | Priority | Allowed values | Notes |
|--------------------|------|----------|---------------|-------|
| `hold_flag` | CHAR(1) | P1 | `Y` / `N` | Whether FCL proceedings are currently on hold (BK / LM / HUD / etc.) |
| `hold_reason` | VARCHAR ENUM | P1 | `BK` / `LM` / `HUD` / `Covid` / `Other` | Reason for the hold |
| `hold_start_date` | DATE | P2 | `YYYY-MM-DD` | Hold start date |
| `hold_end_date` | DATE | P2 | `YYYY-MM-DD` | Hold projected end date |

---

### Group G — REO (Real Estate Owned)

| Standard field name | Type | Priority | Allowed values | Notes |
|--------------------|------|----------|---------------|-------|
| `reo_flag` | CHAR(1) | **P0** | `Y` / `N` | Foreclosure complete; property acquired by lender |
| `reo_acquisition_date` | DATE | P1 | `YYYY-MM-DD` | Date property transferred to lender |

---

## 4. Per-Servicer Compliance Matrix

> Source: `08_servicer_fcl_field_mapping.md` (DB-verified 2026-05-25). ✅ = provided and usable; 🟡 = partially provided or has issues; ❌ = completely absent; ⚠️ = field exists but value format is wrong.

| Servicer | Freq | A: ID | B: Delinq | C: FCL flag | D: LM | E: BK | F: Hold | G: REO |
|---------|------|-------|-----------|------------|-------|-------|---------|--------|
| **SLS** | Daily | ✅ | ✅ `delq_status_mba` (546 Foreclosure rows) | 🟡 No independent flag; `portfcldaily.fcl_status` not connected | ❌ No LM fields at all | 🟡 Text-derived (no independent flag) | ❌ | ❌ |
| **Newrez** | Daily | ✅ | ✅ `delinquency_status_mba` (12K Foreclosure rows) | 🟡 `portnewrezfc.fcl_flag` captured but null | 🟡 Has `lm_flag`; missing type / dates | 🟡 Text-derived (no independent flag) | ❌ | ❌ |
| **Carrington** | Daily | ✅ | ✅ `loan_status` (2K Foreclosure) + `fcl_flag` dual-field | ✅ **Only servicer with independent `fcl_flag`** | 🟡 Has `lm_flag`; missing type / dates | 🟡 Text-derived (no independent flag) | ❌ | ❌ |
| **Selene** | Daily | ✅ | 🟡 `loan_status` has no Foreclosure value (non-standard terminology) | 🟡 `foreclosure_status_code='A'` (41 rows) in L2 but Step 3 absent | 🟡 `lm_setup_date` captured; Step 3 absent | ❌ | ❌ | ❌ |
| **MRC** | Daily | ✅ | ❌ `min_status` always empty string (12,740 rows all empty) | ❌ `fc_flag` never 'Y' (18 rows all 'N') | 🟡 Only `portmrcforbearance` table; no top-level `lm_flag` | ❌ | ❌ | ❌ |
| **Arvest** | **Monthly** | ✅ | ❌ **Monthly report has no delinquency status field at all** | ❌ None | ❌ None | 🟡 Derived from bid table | ❌ | ❌ |
| **CapeCodFive** | **Monthly** | ✅ | ⚠️ `mba_delinquency_status` = numeric DPD strings (`'29.0'`) — **unusable** | ❌ None | ❌ None | ❌ | ❌ | ❌ |
| **FCI** | Daily (API) | ✅ | ✅ `status` captured (2,408 FCL rows); **never connected to ETL** | ❌ Not connected | ❌ None | ❌ | ❌ | ❌ |

---

## 5. Per-Servicer Gaps and Action Items

### 5.1 SLS

**Currently satisfied**: Group A (identification) ✅, Group B (`delq_status_mba` includes `'Foreclosure'`) ✅

**Missing (by priority)**:
- P0: No independent `foreclosure_flag` (`portfcldaily.fcl_status` exists but system never reads it)
- P1: No `lm_flag`, `lm_type` (completely absent)
- P1: No independent `bankruptcy_flag`

**Recommended request**: Ask SLS to add `foreclosure_flag` (`Y`/`N`) to the main daily report, and provide `lm_flag` + `lm_type` in an LM specialty report. Also recommend enabling the existing `portfcldaily` file's `fcl_status` field as a secondary FCL validation source.

---

### 5.2 Newrez

**Currently satisfied**: Group A ✅, Group B (12K FCL rows) ✅, Group D (`lm_flag` present) 🟡

**Missing (by priority)**:
- P0: `portnewrezfc.fcl_flag` captured but system sets to null (internal ETL issue — investigate `portnewrezfc` table structure)
- P1: `lm_type`, `lm_start_date`, `lm_end_date` (flag only, no details)
- P1: No independent `bankruptcy_flag`

**Recommended request**: First investigate why `portnewrezfc.fcl_flag` is null internally; enable it as dual-field FCL check once resolved. Request `lm_type` + `lm_start_date` + `lm_end_date` from Newrez.

---

### 5.3 Carrington

**Currently satisfied**: Group A ✅, Group B (dual-field: `loan_status` + `fcl_flag`) ✅, Group C (`fcl_flag` — best in system) ✅, Group D (`lm_flag` present) 🟡

**Missing (by priority)**:
- P1: `lm_type`, `lm_start_date`, `lm_end_date` (flag present, no details)
- P1: No independent `bankruptcy_flag` (inferred from `loan_status` text)
- P1: `loan_status = 'Loss Mitigation'` (5K rows) not independently mapped to `lm_flag`

**Recommended request**: Carrington is the current best-performing servicer. Primary asks: `lm_type` + `lm_start_date` + `lm_end_date`, and an independent `bankruptcy_flag`.

---

### 5.4 Selene

**Currently satisfied**: Group A ✅, Group C (`foreclosure_status_code='A'` captured) 🟡, Group D (`lm_setup_date` captured) 🟡

**Missing (by priority)**:
- P0: **ETL Step 3 completely absent** (no servicer request needed — internal fix: add `WHEN fcl_flag='A' THEN 'FCL'`)
- P0: `loan_status` has no `'Foreclosure'` value (Selene uses non-standard: `'No Contact'`/`'In Contact'`)
- P1: `lm_type`, `lm_end_date` (has `lm_setup_date`; missing type and expiry)

**Recommended request**: Fix ETL Step 3 first (no Selene action required). Then request Selene align `loan_status` values to MBA standard, and add `lm_type` + `lm_end_date`.

---

### 5.5 MRC

**Currently satisfied**: Group A ✅ (almost everything else absent)

**Missing (by priority)**:
- P0: `min_status` always empty (must confirm with MRC: why are all 12,740 rows empty? Is there an alternative delinquency field?)
- P0: `fc_flag` never `'Y'` (must confirm with MRC: what is the activation condition? Can `fc_status` / `fc_milestone` substitute?)
- P0: ETL Step 3 absent (internal fix, pending P0 field resolution)
- P1: No top-level `lm_flag` (only `portmrcforbearance` specialty table)
- P1: `lm_type`, `lm_start_date`

**Recommended request**: Schedule a working session with MRC to investigate field issues (`min_status` always empty; `fc_flag` activation conditions). Then request: (1) a usable delinquency status field, (2) an activatable `fc_flag` or alternative, (3) top-level `lm_flag` + `lm_type`.

---

### 5.6 Arvest

**Currently satisfied**: Group A ✅ (almost everything else absent)

**Missing (by priority)**:
- P0: **Monthly report has no delinquency status field** (fundamental absence — all FCL loans mislabeled as D120P)
- P0: No `foreclosure_flag`
- P1: No `lm_flag`, `lm_type`
- Additional concern: Monthly-only data (T+1 month FCL change delay; real-time accuracy poor)

**Recommended request (high priority)**: Ask Arvest to add to the monthly report, and explore whether a daily report is feasible:
1. `delinquency_status` (`Current`/`DQ30`/.../`Foreclosure`/`REO`/`PaidOff` text enumeration)
2. `foreclosure_flag` (`Y`/`N`)
3. `lm_flag` + `lm_type`

---

### 5.7 CapeCodFive

**Currently satisfied**: Group A ✅ (almost everything else absent)

**Missing (by priority)**:
- P0: **`mba_delinquency_status` value format wrong** (field name implies MBA standard, but actual values are numeric DPD `'29.0'`) — FCL text match permanently fails
- P0: No independent `foreclosure_flag` (no fallback mechanism)
- P1: No `lm_flag`, `lm_type`
- Additional concern: Monthly-only data (T+1 month delay)

**Recommended request (high priority)**: Ask CapeCodFive to fix `mba_delinquency_status` format (change to MBA standard text enumeration), and add `foreclosure_flag` + `lm_flag` + `lm_type`.

---

### 5.8 FCI

**Currently satisfied**: Group A ✅, Group B (`status` field has 2,408 FCL rows in MySQL, never connected to ETL) 🟡

**Missing (by priority)**:
- P0: **ETL completely absent** (2,408 FCL rows in MySQL are entirely ignored — internal fix)
- P0: FCL data never flows to downstream tables (`portmonthbase` / `portmonth`)
- P1: No `lm_flag`, `lm_type`

**Recommended request**: Fix ETL first (`status='Foreclosure'` mapping logic — no FCI action required). After ETL is live, request `lm_flag` + `lm_type` from FCI.

---

## 6. Data Delivery Format Specification

| Specification | Requirement | Notes |
|--------------|-------------|-------|
| **Frequency** | Daily (recommended) / Monthly (acceptable for small portfolios) | Monthly has T+1 month FCL change delay |
| **Format** | CSV (recommended, UTF-8) / Fixed-width TXT | Avoid xlsx (fragile parsing, format instability) |
| **Date format** | `YYYY-MM-DD` | Reject `MM/DD/YYYY`, `YYYYMMDD`, Excel date serial numbers |
| **NULL handling** | Empty string `''` or explicit `NULL` | Do not use `N/A`, `NA`, `None`, `-`, `0001-01-01` |
| **Enumeration values** | Must use standard enumerations from Section 3 | Do not use custom text (`'Foreclosure / Perf BK'` must be split into separate fields) |
| **File naming** | `{servicer}_{report_type}_{YYYYMMDD}.csv` | Example: `newrez_main_20260525.csv` |
| **Dual-file model** | Main report + FCL specialty report | FCL specialty contains Group C P1/P2 timeline fields |
| **Field order** | Group A → B → C → D → E → F → G | Enables automated schema validation |

---

## 7. Field Request Priority Summary

### Immediate Requests (P0 gaps — affecting FCL status accuracy)

| Servicer | Request content | Urgency reason |
|---------|----------------|----------------|
| **Arvest** | `delinquency_status` (text enum) or `foreclosure_flag` | All FCL loans mislabeled as D120P |
| **CapeCodFive** | Fix `mba_delinquency_status` to text enum, or add `foreclosure_flag` | Format error makes FCL permanently undetectable |
| **MRC** | Investigate why `min_status` is always empty; confirm `fc_flag` activation conditions | Both FCL fields are non-functional |
| **SLS** | Connect `portfcldaily.fcl_status` as a secondary validation source | Single-field dependency creates delay risk |
| **FCI** | (Internal ETL fix — no servicer action needed) | 2,408 FCL rows completely ignored |
| **Selene** | (Internal ETL Step 3 fix — no servicer action needed) | All daily FCL statuses lost |

### Near-Term Requests (P1 gaps — affecting LM/BK analysis quality)

| Servicer | Request content |
|---------|----------------|
| **SLS** | `lm_flag` + `lm_type` |
| **Arvest** | `lm_flag` + `lm_type` (bundle with delinquency status request) |
| **CapeCodFive** | `lm_flag` + `lm_type` (bundle with delinquency status request) |
| **MRC** | `lm_flag` + `lm_type` + `lm_start_date` |
| **Newrez** | `lm_type` + `lm_start_date` + `lm_end_date` |
| **Carrington** | `lm_type` + `lm_start_date` + `lm_end_date` |
| **Selene** | `lm_type` + `lm_end_date` |
| **All servicers** | Independent `bankruptcy_flag` + `bankruptcy_chapter` |

---

## Chinese Version

`docs/zh/09_servicer_data_interface_standard.md`
