# 08 — Servicer Raw Field → Foreclosure Status Mapping Rules

---

## Document Information

| Field | Content |
|-------|---------|
| **Purpose** | From a business rules perspective, document which raw fields in each servicer's data files are used to determine Foreclosure status, the mapping logic, business meaning, and legal context. Removes the ETL middle layer — focuses directly on "what field the servicer provides" → "how we derive FCL status." |
| **Problem solved** | The current system's FCL determination logic is scattered across multiple ETL config files with no unified business rule specification. This document is the current-state baseline (Layer 1) with gap analysis (Layer 2), providing the foundation for requesting missing fields from servicers. |
| **Scope** | 8 servicers — FCL status mapping current state + gap analysis |
| **System** | PrefectFlow ETL pipeline — MySQL Layer 1 raw data |

**Target audience:** Data product managers · Business analysts · Compliance reviewers · Engineers onboarding new servicers

**Dependencies:** `07_fcl_lineage_and_rules.md` (ETL implementation details), `01_source_data.md` (raw table structure)

**Revision history:**

| Date | Author | Version | Changes |
|------|--------|---------|---------|
| 2026-05-25 | AI Agent (Claude Sonnet 4.6) | v6 | Merged two overlapping minimum field set sections into a single dual-perspective table (system requirements × servicer requests); added explanation for why `bankruptcy_flag` is independent of the MBA `Bankruptcy` enum value |
| 2026-05-25 | AI Agent (Claude Sonnet 4.6) | v5 | Added MBA full raw value range table, FCL-Hold explanation, and recommended minimum field set to background section |
| 2026-05-25 | AI Agent (Claude Sonnet 4.6) | v4 | Added LM gap rows to each servicer's gap analysis section; added LM rows to gap summary table |
| 2026-05-25 | AI Agent (Claude Sonnet 4.6) | v3 | Added LM vs MBA standard relationship explanation; added LM field requirements section (6 types + minimum field set + per-servicer coverage) |
| 2026-05-25 | AI Agent (Claude Sonnet 4.6) | v2 | All field values DB-verified via Redshift; corrected CapeCodFive/FCI ratings; fixed SLS/Newrez value examples |
| 2026-05-25 | AI Agent (Claude Sonnet 4.6) | v1 | Initial version, reverse-engineered from PrefectFlow source code |

---

## Background: Business Meaning of FCL Status in US Mortgage

### FCL Status Codes (MBA Standard)

| Code | Business Meaning | Trigger Condition |
|------|----------------|-------------------|
| `C` | Current | DPD < 30 days |
| `D30` | 30–59 Days Past Due | DPD 30–59 days |
| `D60` | 60–89 Days Past Due | DPD 60–89 days |
| `D90` | 90–119 Days Past Due | DPD 90–119 days |
| `D120P` | 120+ Days Past Due | DPD ≥ 120 days |
| `FCL` | **Foreclosure (in foreclosure proceedings)** | Servicer has referred loan to legal process (judicial or non-judicial foreclosure) |
| `REO` | Real Estate Owned (bank-held property) | Foreclosure complete; property acquired by lender |
| `P` | Paid in Full | Loan paid off (normal payoff, short sale, REO disposition) |

### MBA Standard Delinquency: Full Raw Value Range (Servicer Transmission Layer)

> **Two levels to distinguish**: The table above shows **system internal codes** (C/D30/D60/D90/D120P/FCL/REO/P) — the output of ETL Step 3. The table below shows the **raw text values servicers transmit to us**, which must be mapped to internal codes by the ETL.

Using Newrez as the representative example, showing actual values observed in production (DB-verified 2026-05-25):

| Servicer raw value | Meaning | Present in Newrez data | Maps to internal code |
|-------------------|---------|----------------------|----------------------|
| `Current` | 0–29 DPD, performing | ✅ | → `C` |
| `1-29 DPD` | 1–29 days past due (Newrez sub-classification) | ✅ | → `C` |
| `30-59 DPD` | 30–59 days past due | ✅ | → `D30` |
| `60-89 DPD` | 60–89 days past due | ✅ | → `D60` |
| `90-119 DPD` | 90–119 days past due | ✅ | → `D90` |
| `120-149 DPD` | 120–149 days past due | ✅ | → `D120P` |
| `150-179 DPD` | 150–179 days past due | ✅ | → `D120P` |
| `180+ DPD` | 180+ days past due | ✅ | → `D120P` |
| `Foreclosure` | In foreclosure proceedings | ✅ | → `FCL` |
| `Foreclosure / Non-Perf BK` | Foreclosure + non-performing bankruptcy (Newrez extension) | ✅ | → `FCL` (+ `bankruptcy='Y'`) |
| `Foreclosure / Perf BK` | Foreclosure + performing bankruptcy (Newrez extension) | ✅ | → `FCL` (+ `bankruptcy='Y'`) |
| `Performing Bankruptcy` | Performing bankruptcy (still making payments) | ✅ | → `D90`/`D120P` + `bankruptcy='Y'` |
| `Non-Performing Bankruptcy` | Non-performing bankruptcy | ✅ | → `D120P` + `bankruptcy='Y'` |
| `REO` | Real estate owned by lender | ✅ | → `REO` |
| `REO Sale` | REO has been sold (disposition complete) | ✅ | → `P` |
| `Full Payoff` / `Paid in Full` | Fully paid off | ✅ | → `P` |
| `3rd Party Sale` | Third-party auction sale | ✅ | → `P` |
| `Service Release` | Loan servicing rights transferred (loan leaves this servicer) | ✅ | → Special handling |

> **Note**: `Foreclosure / Non-Perf BK` and `Foreclosure / Perf BK` are Newrez-specific composite values that compress FCL and BK status into a single field. The doc 09 interface standard requires these two dimensions to be transmitted through **separate fields** (`foreclosure_flag` + `bankruptcy_flag`) to avoid fragile text parsing.

### FCL-Hold: Not an MBA Standard Status

MBA standard does **not** include `FCL-Hold` as a category.

**FCL-Hold** (foreclosure hold) is a servicer-internal operational status indicating that foreclosure proceedings have been initiated but are temporarily suspended. Common reasons:
- Borrower has applied for Loss Mitigation (loan modification / forbearance)
- Bankruptcy automatic stay (Automatic Stay)
- COVID special forbearance period
- Court order to suspend

Under the MBA framework, even when a Hold is active, the loan is still **reported as `Foreclosure`** — because MBA reflects legal status (foreclosure proceedings have been initiated), not operational progress. Therefore, relying solely on the MBA status field makes it impossible to know whether foreclosure is on hold. A separate `fcl_hold_flag` / `hold_reason` field is needed.

### Legal Definition of Foreclosure

**Foreclosure** is the legal process by which a lender, following a borrower default (typically 90–120+ days delinquent), pursues court-ordered or contractual forced sale of the collateral property to recover the outstanding loan balance.

- **Judicial Foreclosure**: Requires court approval. Typical states: New York, New Jersey, Florida (process: 6 months – 2 years)
- **Non-Judicial Foreclosure (Power of Sale)**: No court required; follows contractual terms for direct auction. Typical states: California, Texas (process: 3–6 months)

**At the system level**, when a servicer marks a loan as FCL in their data file, it typically indicates the loan has entered one of these stages: DEMAND → REFERRAL (attorney referral) → FIRST LEGAL (first legal action) → SERVICE (document service) → JUDGEMENT → SALE (auction)

### LM (Loss Mitigation) Status and Its Relationship to MBA Delinquency Status

**LM is not part of the MBA standard delinquency status.** `delinquency_status_mba` reflects only "how overdue is the loan" — it does not reflect "what remediation is being attempted." LM information must be conveyed through a separate field.

The two dimensions are **completely orthogonal** — think of them as two independent axes:

```
MBA delinquency_status_mba (delinquency status) = horizontal axis: how severe is the default?
LM status (loss mitigation status)              = vertical axis: what remediation is in progress?

A single loan can simultaneously be:
  delinq = 'D90' AND lm_flag = 'Y'  (90 days past due + loan modification in progress)
  delinq = 'FCL' AND lm_flag = 'Y'  (in foreclosure + forbearance being negotiated)
  delinq = 'C'   AND lm_flag = 'N'  (current, no mitigation needed)
```

**LM does not produce an independent delinq status code.** In the system, `lm_flag = 'Y'` is only an auxiliary flag; `delinq` is still calculated from days360 or servicer-provided status text. LM success → borrower resumes payments → `delinq` naturally returns to `C`. LM failure → loan remains delinquent → `delinq` continues to accumulate toward FCL.

---

## Per-Servicer Mapping

### ETL Layer Reference (required context for reading this document)

This document frequently uses the terms "Step 3" and "Layer 1/L2". Meanings:

```
Layer 1 / MySQL L1
  Servicer raw tables (e.g. sls.portassetdaily, carrington.portcarrington)
  → Field names match servicer file exactly; no renaming
        ↓ ETL Step 1: field renaming + JOIN
Layer 2 / L2
  Redshift port.basic_data_daily_loan_common
  → All servicers merged into unified field names (svcdelinq, fcl_flag, etc.); values not yet transformed
        ↓ ETL Step 3: FCL/REO/P/D30... determination logic
Layer 3 (Clean)
  Redshift port.basic_data_daily_loan_common_clean
  → Final standardized delinq status codes produced ('FCL', 'REO', 'D30', etc.)
        ↓
Layer 4 (Monthly analytics)
  port.portmonthbase / port.portmonth
```

> **"Not connected to Step 3"** = This servicer's data is in L2 ✅, but `daily_data_loan_common_clean_config.py` contains **no SQL block** for this servicer ❌. The `delinq` field is never populated, so FCL status does not exist in any downstream report.

---

### Overall Quality Summary

> **Field note**: All fields below are **MySQL Layer 1 raw fields** (loaded directly from servicer files without renaming). Format: `schema.table.field`.

| Servicer | Frequency | Delinquency Status Field | Independent FCL Flag | Bankruptcy Field | LM Field | FCL Coverage |
|---------|-----------|-------------------------|---------------------|-----------------|----------|-------------|
| SLS | Daily | ✅ `sls.portassetdaily.delq_status_mba` | ❌ None | ✅ text-derived | ❌ None | 🟡 Medium (text match only) |
| Newrez | Daily | ✅ `newrez.portnewrezgeneral.delinquency_status_mba` | ❌ captured but null | ✅ text-derived | ✅ `newrez.portnewrezlm.activelmflag` | 🟡 Medium (text match only) |
| Carrington | Daily | ✅ `carrington.portcarrington.loan_status` | ✅ `carrington.portcarrington.fcl_flag` | ✅ text-derived | ✅ `carrington.portcarrington.lm_flag` | ✅ Best (dual-field check) |
| Selene | Daily | ✅ `selene.portselenemain.loan_status` | ✅ `selene.portselenemain.foreclosure_status_code` (captured, unused) | — | ✅ `selene.portselenemain.lm_setup_date` | ❌ Not connected to Step 3 |
| MRC | Daily | ✅ `mrc.portmrcloan.min_status` | ✅ `mrc.portmrcforeclosure.fc_flag` (captured, unused) | — | — | ❌ Not connected to Step 3 |
| Arvest | Monthly | ❌ No delinquency status field | ❌ None | ✅ bid-derived | ❌ None | ❌ days360 only (FCL can never be produced) |
| CapeCodFive | Monthly | ⚠️ `capecodfive.portcapecodfive_monthly_servicing.mba_delinquency_status` (values are numeric DPD, not text status) | ❌ None | — | — | ❌ FCL can never be produced (value format mismatch) |
| FCI | Daily (API) | ✅ `fci.portfciloanportfolio.status` (captured, unused — 2,408 FCL rows ignored) | — | — | — | ❌ Not implemented at all |

---

### 3.1 SLS — 🟡 Medium (Text Match Only)

**Data Overview**

| Attribute | Value |
|-----------|-------|
| Frequency | Daily |
| Format | `.txt` (fixed format, multiple file types) |
| Key raw tables | `sls.portassetdaily` (main daily + delinquency status), `sls.portfcldaily` (FCL-specific file) |
| Active period | Before 2024-07-05 (switched to Newrez after) |

**FCL-Related Raw Fields** (all MySQL Layer 1 raw fields)

| Full field path (schema.table.field) | Business meaning | Value range / examples | FCL use |
|--------------------------------------|-----------------|----------------------|---------|
| `sls.portassetdaily.delq_status_mba` | MBA standard delinquency status | `'Current'`(158K), `'DQ 30'`(47K), `'Service Release'`(19K), `'Paid in Full'`(5K), `'DQ 60'`(5K), `'DQ 90'`(4K), `'Bankruptcy'`(1K), `'Foreclosure'`(546) | **Primary determination field** (DB-verified 2026-05-25) |
| `sls.portassetdaily.nextduedate` | Next payment due date | `DATE`, e.g. `2024-03-01` | days360 fallback calculation |
| `sls.portfcldaily.fcl_status` | FCL-specific status (separate file) | To be confirmed | **Not currently used for delinq determination** |
| `sls.portfcldaily.fcl_referral_date` | Date referred to legal process | `DATE` | Timeline field, not used for status |

**FCL Status Determination Rules (business logic, priority order)**

1. **Paid-Off (P)**: `delq_status_mba = 'Paid in Full'`
2. **REO**: `delq_status_mba = 'REO'`
3. **FCL**: `delq_status_mba = 'Foreclosure'`
4. **Fallback (days360)**: If none of the above, calculate `days360(nextduedate)` → C / D30 / D60 / D90 / D120P
5. **Bankruptcy (auxiliary flag)**: `delq_status_mba = 'Bankruptcy'` → `bankruptcy = 'Y'`

> **Business context**: SLS uses the MBA standard delinquency status code. `'Foreclosure'` indicates SLS has formally entered foreclosure proceedings for this loan. This field is actively maintained by SLS in their internal system.

**Gap Analysis**

| Gap | Risk | Notes |
|-----|------|-------|
| No independent FCL activation flag | 🟡 Medium | Entirely dependent on `delq_status_mba` text. If SLS delays updating the status, the system cannot independently detect FCL |
| `portfcldaily` data not used for FCL determination | 🟡 Medium | SLS provides a dedicated FCL file (`portfcldaily`) but the system doesn't use it to validate/supplement delinq |
| **LM: No LM fields at all** | 🟡 Medium | SLS data has no `lm_flag`, `lm_type`, or equivalent. Cannot determine whether a loan is in an active LM plan, or distinguish FCL+LM mixed state. **Request from SLS: `lm_flag` + `lm_type`** |

---

### 3.2 Newrez — 🟡 Medium (Text Match Only; fcl_flag is Null)

**Data Overview**

| Attribute | Value |
|-----------|-------|
| Frequency | Daily |
| Format | `.txt` / `.csv` (multiple file types: main + specialty reports) |
| Key raw tables | `newrez.portnewrezgeneral` (main daily), `newrez.portnewrezfc` (FCL specialty), `newrez.portnewrezlm` (LM specialty) |
| Active period | From 2024-07-05 (switched from SLS) |

**FCL-Related Raw Fields** (all MySQL Layer 1 raw fields)

| Full field path (schema.table.field) | Business meaning | Value range / examples | FCL use |
|--------------------------------------|-----------------|----------------------|---------|
| `newrez.portnewrezgeneral.delinquency_status_mba` | MBA standard delinquency status | `'Current'`(1.07M), `'1-29 DPD'`(251K), `'Full Payoff'`(147K), `'30-59 DPD'`(21K), `'Foreclosure'`(12K), `'60-89 DPD'`(8K), `'90-119 DPD'`(4K), `'Performing Bankruptcy'`(3K), `'Non-Performing Bankruptcy'`(2K), `'REO'`(700), `'Foreclosure / Non-Perf BK'`(500), `'Foreclosure / Perf BK'`(346), `'REO Sale'`(228), `'3rd Party Sale'`(132) | **Primary determination field** (DB-verified 2026-05-25) |
| `newrez.portnewrezgeneral.nextduedate` | Next payment due date | `DATE` | days360 fallback |
| `newrez.portnewrezfc.fcl_flag` | FCL activation flag (FCL specialty file) | Captured but system sets to `null` | **Captured but unused** |
| `newrez.portnewrezlm.activelmflag` | LM activation flag | `'1'` (active) / `'0'` (inactive) | → `lm_flag = 'Y'` |
| `newrez.portnewrezlm.forbearancestatus` | Forbearance status | `'Active'`, `'Completed'`, etc. | LM supplemental info |

**FCL Status Determination Rules (business logic, priority order)**

1. **Paid-Off (P)**: `delinquency_status_mba = 'Full Payoff'`
2. **REO**: `delinquency_status_mba = 'REO'`
3. **FCL**: `delinquency_status_mba IN ('Foreclosure', 'Foreclosure / Non-Perf BK', 'Foreclosure / Perf BK')`
4. **Fallback (days360)**: Calculate `days360(nextduedate)` → C / D30 / D60 / D90 / D120P
5. **Bankruptcy (auxiliary flag)**: `delinquency_status_mba LIKE '%Bankruptcy%'` → `bankruptcy = 'Y'`
6. **Special (VASP)**: Specific VASP deal loans hard-coded as `delinq = 'VASP'` (19 records)

> **Business context**: `'Foreclosure / Non-Perf BK'` = foreclosure with non-performing bankruptcy; `'Foreclosure / Perf BK'` = foreclosure with performing bankruptcy. Newrez conveys both FCL and bankruptcy status through a single field.

**Gap Analysis**

| Gap | Risk | Notes |
|-----|------|-------|
| `fcl_flag` captured but null | 🔴 High | Newrez provides `portnewrezfc` which should contain an independent FCL flag, but system sets it to null. Largest data utilization gap. |
| Bankruptcy status derived from main status field | 🟡 Medium | No independent bankruptcy flag; bankruptcy is embedded in the delinquency status text |
| VASP rule hard-coded | 🟡 Medium | Special-deal VASP classification is hard-coded in ETL, not driven by field logic |
| **LM: Has flag but missing type and dates** | 🟡 Medium | Has `activelmflag` (Y/N) and `forbearancestatus` (numeric codes), but no `lm_type` (cannot distinguish Forbearance vs Modification), no `lm_start_date` / `lm_end_date`. **Request from Newrez: `lm_type` + `lm_start_date` + `lm_end_date`** |

---

### 3.3 Carrington — ✅ Best Coverage (Dual-Field Check)

**Data Overview**

| Attribute | Value |
|-----------|-------|
| Frequency | Daily (main) + bi-weekly (delinquency specialty) |
| Format | `.xlsx` or `.csv` |
| Key raw tables | `carrington.portcarrington` (comprehensive daily report containing both delinquency status and FCL flag) |

**FCL-Related Raw Fields** (all MySQL Layer 1 raw fields, all from `carrington.portcarrington`)

| Full field path (schema.table.field) | Business meaning | Value range / examples | FCL use |
|--------------------------------------|-----------------|----------------------|---------|
| `carrington.portcarrington.loan_status` | Loan status | `'CUR'`(204K), `'0-29'`(61K), `'Completed Payoff'`(18K), `'30-59'`(9K), `'Loss Mitigation'`(5K), `'60-89'`(2K), `'Foreclosure'`(2K), `'Bankruptcy - Performing'`(2K), `'90-119'`, `'120+'`, `'REO'`, `'Foreclosure/Bankruptcy - Non-Performing'`, etc. | FCL text determination (DB-verified 2026-05-25) |
| `carrington.portcarrington.fcl_flag` | FCL activation flag (independent field) | `'Active'` (3,373 rows — FCL active) / `''` (303,007 rows — inactive) | **Independent FCL flag** ★ (DB-verified 2026-05-25) |
| `carrington.portcarrington.nextduedate` | Next payment due date | `DATE` | days360 fallback |
| `carrington.portcarrington.lm_flag` | LM activation flag | `'Active'` (active) | → `lm_flag = 'Y'` |
| `carrington.portcarrington.covid_forbearance_flag` | COVID forbearance flag | `'Y'` / `'N'` | Special forbearance period marker |

**FCL Status Determination Rules (business logic, priority order)**

1. **FCL**: `loan_status = 'Foreclosure'` **OR** `fcl_flag = 'Active'` (dual-field OR check)
2. **REO**: `loan_status IN ('R', 'REO')`
3. **Paid-Off (P)**: `loan_status IN ('Completed Payoff', 'Completed Short Sale', 'Completed REO Sale')`
4. **Fallback (days360)**: Calculate `days360(nextduedate)` → C / D30 / D60 / D90 / D120P
5. **Bankruptcy (auxiliary flag)**: `loan_status = 'Bankruptcy - Performing'` → `bankruptcy = 'Y'`

> **Design strength**: `fcl_flag = 'Active'` acts as a safety net — even if `loan_status` doesn't explicitly say `'Foreclosure'`, an active FCL flag still triggers FCL classification. This dual-field protection is missing for all other servicers.

**Gap Analysis**

| Gap | Risk | Notes |
|-----|------|-------|
| No independent bankruptcy flag | 🟡 Medium | Bankruptcy inferred from `loan_status` text only |
| Short Sale and REO Sale both map to P | 🟡 Low | Cannot distinguish liquidation type |
| **LM: Has flag but missing type and dates** | 🟡 Medium | Has `lm_flag` ('Active') and `covid_forbearance_flag`, but `loan_status = 'Loss Mitigation'` (5K rows) is not independently mapped, and no `lm_type` / `lm_start_date`. **Request from Carrington: `lm_type` + `lm_start_date` + `lm_end_date`** |

---

### 3.4 Selene — ❌ Fields Captured but Not Connected to FCL Determination

**Data Overview**

| Attribute | Value |
|-----------|-------|
| Frequency | Daily |
| Format | `.csv` (multiple report types: P181, P102, DailyExtract, etc.) |
| Key raw tables | `selene.portselenemain` (main daily), `selene.portselenedetails` |

**FCL-Related Raw Fields** (all MySQL Layer 1 raw fields, all from `selene.portselenemain`)

| Full field path (schema.table.field) | Business meaning | Value range / examples | FCL use |
|--------------------------------------|-----------------|----------------------|---------|
| `selene.portselenemain.loan_status` | Loan status | `'Current'`(115K), `'Liquidated'`(1K), `'No Contact'`(922), `'In Contact'`(429), `'Lost Contact'`(201), `'Prequal'`(3) — ⚠️ **No `'Foreclosure'` value; Selene uses non-standard status terminology** | Written to L2 but not used for FCL determination (DB-verified 2026-05-25) |
| `selene.portselenemain.foreclosure_status_code` | FCL status code (independent field) | `''`(118K — no FCL), `'A'`(41 rows = **Active Foreclosure**), `'R'`(100 rows = **Released/Resolved**) — this is the only reliable FCL signal for Selene | **Mapped to L2 `fcl_flag`, but no Selene Step 3 logic exists** (DB-verified 2026-05-25) |
| `selene.portselenemain.lm_setup_date` | LM setup date | `DATE` (non-null → LM active) | → `lm_flag = 'Y'` |
| `selene.portselenemain.nextduedate` | Next payment due date | `DATE` | Could be used for days360 |

**FCL Status Determination Rules**

> ⚠️ **Current state: Completely absent.** No `GEN_BASIC_DATA_DAILY_LOAN_COMMON_CLEAN_SELENE` variable exists in the ETL.
>
> Selene daily data enters L2 (`basic_data_daily_loan_common`) ✅ but is **never processed into a standardized `delinq` status** (Step 3 ❌).
>
> Result: Selene loan delinq statuses in `portmonthbase` come from a monthly path covering only some deals — not a systematic implementation.

**Gap Analysis**

| Gap | Risk | Notes |
|-----|------|-------|
| Step 3 completely absent | 🔴 Critical | All Selene loans have no FCL status from the daily path |
| `foreclosure_status_code` not used | 🔴 Critical | `'A'`(41 rows) = Active FCL, already captured in L2 `fcl_flag` — Step 3 simply doesn't read it |
| `loan_status` has no `'Foreclosure'` value | 🔴 Critical | Selene uses `'No Contact'`/`'In Contact'`/`'Lost Contact'` — non-standard terminology; text-match for FCL will never succeed |
| **LM: Field exists but Step 3 absent** | 🟡 Medium | `lm_setup_date` is captured (non-null = LM active), but no Selene Step 3 logic exists so `lm_flag` cannot be passed to downstream. No `lm_type` or dates. **After fixing Step 3, request from Selene: `lm_type` + `lm_end_date`** |

**Recommended fix** (no new fields needed from Selene):
- Add Selene logic to Step 3: `WHEN fcl_flag = 'A' THEN 'FCL'` — `foreclosure_status_code='A'` is already captured in L2

---

### 3.5 MRC — ❌ Fields Captured but Not Connected to FCL Determination

**Data Overview**

| Attribute | Value |
|-----------|-------|
| Frequency | Daily |
| Format | `.txt` (fixed format, 18 report types) |
| Key raw tables | `mrc.portmrcloan` (main daily), `mrc.portmrcforeclosure` (FCL specialty table) |

**FCL-Related Raw Fields** (MySQL Layer 1 raw fields from two separate tables)

| Full field path (schema.table.field) | Business meaning | Value range / examples | FCL use |
|--------------------------------------|-----------------|----------------------|---------|
| `mrc.portmrcloan.min_status` | Loan minimum delinquency status | ⚠️ **Always empty string `''` (all 12,740 rows)** — field is completely unusable; no delinquency data at all | Written to L2 `delq_status`, but value is empty — cannot be used for FCL determination (DB-verified 2026-05-25) |
| `mrc.portmrcforeclosure.fc_flag` | FCL activation flag (dedicated FCL table, only 18 rows) | ⚠️ **Only `'N'` (18 rows) — `'Y'` never appears** — even when a loan is in FCL proceedings (`referral_hold_reason` has FCL text), this field remains `'N'` | **Mapped to L2 `fcl_flag`, but no MRC Step 3 logic exists** (DB-verified 2026-05-25) |
| `mrc.portmrcloan.dataasof` | Data as-of date | `DATE` | JOIN key |

**FCL Status Determination Rules**

> ⚠️ **Current state: Completely absent.** Same as Selene — no MRC Step 3 processing exists in the ETL.
>
> MRC provides both: (1) `min_status` delinquency status in the main daily report, and (2) `fc_flag` in a dedicated FCL table. Both are captured but neither contributes to `delinq` output.

**Gap Analysis**

| Gap | Risk | Notes |
|-----|------|-------|
| Step 3 completely absent | 🔴 Critical | All MRC loans have no FCL status from the daily path |
| `min_status` always empty | 🔴 Critical | DB-verified: all 12,740 rows are empty string. Field is completely unusable. Root cause unknown (MRC system issue? field not enabled?) |
| `fc_flag` never activated | 🔴 Critical | DB-verified: `portmrcforeclosure` has only 18 rows, all `'N'`. A loan's `referral_hold_reason` shows FCL text (e.g. "HOLD 99 OPEN DEMAND AGING") but `fc_flag` is never set to `'Y'` |
| **LM: Only dedicated forbearance table; no overall LM flag** | 🟡 Medium | MRC has `portmrcforbearance` dedicated table (`status` field), but no top-level `lm_flag`, and no `lm_type` or date fields. **Request from MRC: top-level `lm_flag` + `lm_type` + `lm_start_date`** |

**Recommended field clarification request**

Needs to be confirmed with MRC:
- Why is `portmrcloan.min_status` always empty? Is there an alternative delinquency status field?
- Under what condition would `fc_flag = 'Y'`? Has MRC ever set this field to active?
- Alternative: can `portmrcforeclosure.fc_status` or `fc_milestone` be used to derive FCL status?

---

### 3.6 Arvest — ❌ No Delinquency Status Field; FCL Can Never Be Produced

**Data Overview**

| Attribute | Value |
|-----------|-------|
| Frequency | **Monthly only** (no daily data) |
| Format | `.xlsx` (multiple Excel files merged) |
| Key raw tables | `arvest.portarvestremitmonthlystatement` (monthly loan statement), `arvest.portarvestremit` (monthly remittance) |

**FCL-Related Raw Fields** (MySQL Layer 1 raw fields)

| Full field path (schema.table.field) | Business meaning | Value range / examples | FCL use |
|--------------------------------------|-----------------|----------------------|---------|
| `arvest.portarvestremitmonthlystatement.nextduedate` | Next payment due date | `DATE` | **Only usable field** — days360 fallback |
| `arvest.portarvestremitmonthlystatement.due_date` | Due date | `DATE` | Reference |
| ~~Delinquency status field~~ | **Does not exist** | — | Arvest monthly report has no delinquency status field |

**FCL Status Determination Rules**

> ⚠️ **Critical limitation: Arvest's monthly report contains no delinquency status field (`loan_status`, `delinquency_status`, etc.). The system can only use `days360(nextduedate)` to calculate days past due.**

1. **FCL / REO / Paid-Off**: Logic exists in code (`svcdelinq = 'Foreclosure'` etc.), but `svcdelinq` is **always null** in the Arvest path
2. **Effective rule**: Degrades entirely to days360 fallback:
   - `days360 < 30` → C
   - `days360 < 60` → D30
   - `days360 < 90` → D60
   - `days360 < 120` → D90
   - else → D120P
3. **Result**: Arvest loans in foreclosure are misclassified as `D120P`. `delinq = 'FCL'` **can never be produced** in the Arvest path.

**Gap Analysis**

| Gap | Risk | Notes |
|-----|------|-------|
| No delinquency status field in Arvest monthly report | 🔴 Critical | Monthly report fundamentally lacks `loan_status` or equivalent |
| FCL status can never be produced | 🔴 Critical | All Arvest FCL loans are mislabeled as D120P |
| Monthly-only data | 🟡 Medium | T+1 month data lag — FCL changes not reflected promptly |
| **LM: No LM fields at all** | 🟡 Medium | Arvest monthly report has no `lm_flag` or any LM-related fields. Cannot determine whether a loan is in an active LM plan. **Request from Arvest: `lm_flag` + `lm_type` (request alongside delinquency status fields)** |

**Recommended field request (high priority)**

Request from Arvest — either of the following would resolve the core issue:
- `loan_status` or `delinquency_status` containing `'Foreclosure'`, `'REO'`, etc.
- `foreclosure_flag`: binary FCL activation flag (`'Y'`/`'N'` or `1`/`0`)

---

### 3.7 CapeCodFive — ❌ FCL Can Never Be Produced (Value Format Mismatch)

**Data Overview**

| Attribute | Value |
|-----------|-------|
| Frequency | **Monthly only** (no daily data) |
| Format | `.xlsx` (custom format) |
| Key raw tables | `capecodfive.portcapecodfive_monthly_servicing` (monthly servicing report with MBA standard delinquency status) |

**FCL-Related Raw Fields** (MySQL Layer 1 raw fields)

| Full field path (schema.table.field) | Business meaning | Value range / examples | FCL use |
|--------------------------------------|-----------------|----------------------|---------|
| `capecodfive.portcapecodfive_monthly_servicing.mba_delinquency_status` | MBA standard delinquency status field name, but **actual values are numeric DPD strings** | `''`(6,459), `'29.0'`(11), `'30.0'`(7), `'27.0'`(7), `'26.0'`(5), `'60.0'`(2), `'90.0'`(1), etc. — ⚠️ **No `'Foreclosure'` text value ever appears** | DB-verified: ETL checks `svcdelinq = 'Foreclosure'` but values are numeric, text match never succeeds (DB-verified 2026-05-25) |
| `capecodfive.portcapecodfive_monthly_servicing.next_payment_due_date` | Next payment due date (monthly servicing) | `DATE` | days360 fallback |
| `capecodfive.portcapecodfive_remit_report.next_due` | Next payment due date (remit report, preferred) | `DATE` | days360 fallback |

**FCL Status Determination Rules (actual execution)**

> ⚠️ **Critical finding: ETL code checks `svcdelinq = 'Foreclosure'` but `mba_delinquency_status` actual values are numeric DPD strings (e.g. `'29.0'`, `'30.0'`). They will never equal text `'Foreclosure'`.**
>
> Identical to Arvest: **FCL status can never be produced in the CapeCodFive path.** All FCL loans are misclassified as D120P.

1. ~~**FCL**: `svcdelinq = 'Foreclosure'`~~ → never matches (values are numeric strings)
2. ~~**REO**: `svcdelinq IN ('R', 'REO')`~~ → never matches
3. ~~**Paid-Off (P)**: `svcdelinq = 'Completed Payoff'`~~ → never matches
4. **No data**: `nextduedate IS NULL` → `delinq = NULL`
5. **Only effective rule (days360 fallback)**: Degrades to pure date calculation → C / D30 / D60 / D90 / D120P

**Gap Analysis**

| Gap | Risk | Notes |
|-----|------|-------|
| `mba_delinquency_status` value format mismatch | 🔴 Critical | Field name suggests MBA categorical status, but actual values are numeric DPD (e.g. `'29.0'`). Text match logic will permanently fail |
| FCL status can never be produced | 🔴 Critical | Same issue as Arvest — all CapeCodFive FCL loans are mislabeled as D120P |
| No independent FCL flag | 🔴 Critical | No fallback mechanism |
| Monthly-only data | 🟡 Medium | T+1 month data lag |
| **LM: No LM fields at all** | 🟡 Medium | CapeCodFive monthly report has no `lm_flag` or any LM-related fields. **Request from CapeCodFive: `lm_flag` + `lm_type` (request alongside delinquency status fields)** |

**Recommended field request (high priority)**

Request from CapeCodFive either:
- `loan_status` or `delinquency_status` with text values like `'Foreclosure'`, `'REO'`
- `foreclosure_flag`: binary FCL activation flag (`'Y'`/`'N'`)

---

### 3.8 FCI — ❌ Not Implemented At All

**Data Overview**

| Attribute | Value |
|-----------|-------|
| Frequency | Daily (via GraphQL API) |
| Format | GraphQL API (60+ report types) |
| Key raw tables | `fci.portfciloanportfolio` (main loan portfolio), `fci.portfciwebforeclosure` (FCL specialty) |

**FCL-Related Raw Fields** (MySQL Layer 1 raw fields, loaded via GraphQL API)

| Full field path (schema.table.field) | Business meaning | Value range / examples | FCL use |
|--------------------------------------|-----------------|----------------------|---------|
| `fci.portfciloanportfolio.status` | Loan status (⚠️ note: column is `status`, NOT `loanStatus`) | `'Paid off'`(65K), `'Performing'`(31K), `'Transfer out'`(14K), **`'Foreclosure'`(2,371)**, **`'REO'`(2,040)**, `'Delinquency'`(1,570), `'Closed'`(721), `'Bankruptcy'`(112), **`'Pre Foreclosure'`(37)** | **Captured in MySQL but never used for delinq determination** (DB-verified 2026-05-25) |
| `fci.portfciloanpaystring.currentDQStatus` | Current delinquency status | Needs further investigation | Captured, unused |

**FCL Status Determination Rules**

> ❌ **Not implemented.** FCI data is collected via GraphQL API and loaded into MySQL, but no ETL logic exists to transform it into a standard `delinq` status. FCI loans have no FCL determination in any analysis table (portmonthbase / portmonth).

**Gap Analysis**

| Gap | Risk | Notes |
|-----|------|-------|
| Completely absent from ETL delinq pipeline | 🔴 Critical | All FCI loans have no FCL status in the system. DB-verified: FCI has **2,408 FCL rows** (`'Foreclosure'`+`'Pre Foreclosure'`) being completely ignored |
| Field name documentation error | 🟡 Medium | Original doc said `loanStatus`; DB-verified correct column name is `status` (lowercase, no camelCase) |
| `currentDQStatus` values not confirmed | 🟡 Medium | Needs further query of `fci.portfciloanpaystring` |
| **LM: No LM fields at all** | 🟡 Medium | FCI data has no `lm_flag` or any LM-related fields. **After implementing ETL, request from FCI: `lm_flag` + `lm_type`** |

---

## Gap Summary and Priority

### Layer 2 — Full Gap Landscape

> **Term quick reference** (full definitions in the "ETL Layer Reference" box at the top of this document)
> - **Layer 2 / L2**: Redshift `port.basic_data_daily_loan_common` — the unified staging table where ETL Step 1 merges all servicers' raw MySQL data with standardized field names. "Layer 2 — Full Gap Landscape" means all gaps below are identified at the L2 level.
> - **Step 3**: The FCL/REO/P/D30... status determination logic in `daily_data_loan_common_clean_config.py`. It reads `svcdelinq` / `fcl_flag` fields from L2 and writes the final standardized `delinq` status code to L3 (`basic_data_daily_loan_common_clean`). "Step 3 absent" = no SQL block exists for this servicer in that file → `delinq` is always null → FCL status never appears in any downstream report.

| Priority | Servicer | Gap Type | Required Field / Action |
|----------|---------|---------|------------------------|
| P0 (Immediate) | Selene | Step 3 absent, but `foreclosure_status_code='A'`(41 rows) already in L2 | **No new fields needed**: add `WHEN fcl_flag='A' THEN 'FCL'` to Step 3 |
| P0 (Immediate) | MRC | Step 3 absent; `min_status` always empty; `fc_flag` never activated | Confirm alternative field with MRC (`fc_status`/`fc_milestone`); or request delinquency status field |
| P0 (Immediate) | Arvest | No delinquency status field at all | Request `loan_status` or `foreclosure_flag` from Arvest |
| P0 (Immediate) | CapeCodFive | `mba_delinquency_status` is numeric DPD — FCL text match permanently fails | Request text-based delinquency status or FCL flag from CapeCodFive |
| P0 (Immediate) | FCI | Not implemented; 2,408 FCL rows ignored | Build ETL logic (`status='Foreclosure'`) |
| P1 (Near-term) | Newrez | `fcl_flag` captured but null | Investigate `portnewrezfc` for actual FCL flag field |
| P1 (Near-term) | SLS | No FCL flag; `portfcldaily` unused | Use `portfcldaily` data as validation/supplement |
| P1 (Near-term) | SLS / Arvest / CapeCodFive / FCI / MRC | No `lm_flag`; cannot determine LM status | Request `lm_flag` + `lm_type` from each servicer |
| P2 (Mid-term) | Newrez / Carrington / Selene | Have LM flag; missing `lm_type` and dates | Request `lm_type` + `lm_start_date` + `lm_end_date` |
| P2 (Mid-term) | All servicers | No unified independent bankruptcy field | Request independent bankruptcy flag per servicer |

### Minimum Field Set for FCL Determination: System Requirements vs. Servicer Requests

Each servicer should provide at minimum the following fields for reliable FCL determination. The table marks which fields the ETL algorithm requires (system perspective) versus which need to be explicitly requested from servicers (interface perspective):

| Field | Type | System Needs | Request from Servicer | Priority | Notes |
|-------|------|-------------|----------------------|----------|-------|
| `delinquency_status_mba` | VARCHAR ENUM | ✓ | ✓ | P0 | MBA text enum — primary determination signal (FCL / REO / DPD bands / Payoff) |
| `fcl_flag` | `'Y'`/`'N'` | ✓ | ✓ | P0 | Independent FCL activation flag (safety net — prevents misclassification when status text is delayed); only Carrington currently provides this |
| `next_payment_due_date` | DATE | ✓ | — All servicers already provide | — | days360 fallback calculation; existing field, no additional request needed |
| `fcl_hold_flag` | `'Y'`/`'N'` | ✓ | ✓ | P1 | Whether FCL proceedings are on hold (MBA reports Foreclosure even when hold is active) |
| `fcl_hold_reason` | VARCHAR ENUM | ✓ | ✓ | P1 | Hold reason (`LM` / `BK` / `HUD` / `Covid` / `Other`) |
| `bankruptcy_flag` | `'Y'`/`'N'` | ✓ | ✓ (none currently) | P1 | Independent bankruptcy flag. MBA `Bankruptcy` and `Foreclosure` enum values are **mutually exclusive** — a single field cannot express FCL+BK coexistence; an independent flag is required to capture the "FCL on hold due to BK" mixed-status scenario |

> **Reference model**: Currently only **Carrington** provides both `loan_status` (MBA-approximate) + `fcl_flag` (independent activation flag) — the closest implementation to this ideal model. Use Carrington as the reference template when specifying data requirements to other servicers.

---

---

## LM (Loss Mitigation) Field Requirements

### Six LM Types

| LM Type | Business Meaning | Typical Duration | Outcome |
|---------|----------------|-----------------|---------|
| **Forbearance** | Temporarily suspend or reduce payments; arrears repaid later | 3–12 months | Temporary; may convert to Modification |
| **Loan Modification** | Permanently change interest rate / term / principal | Permanent | Most comprehensive LM solution |
| **Repayment Plan** | Pay off arrears in installments alongside regular payments | 3–6 months | Runs parallel to regular payment schedule |
| **Trial Period Plan** | Probationary period before permanent modification takes effect | 3 months | Pass trial → Permanent Modification |
| **Short Sale** | Sell property below loan balance; remaining balance forgiven | Months | Loan closes; delinq → P |
| **Deed in Lieu** | Borrower voluntarily transfers property to lender | Months | Loan closes; avoids foreclosure auction |

### Minimum LM Field Set to Request from Servicers

| Field name (suggested) | Type | Priority | Notes |
|----------------------|------|----------|-------|
| `lm_flag` | `'Y'`/`'N'` | **P0 Required** | Whether loan is in active LM — the most fundamental signal |
| `lm_type` | enum text | **P1 Recommended** | `Forbearance` / `Modification` / `RepaymentPlan` / `TrialPlan` / `ShortSale` / `DeedInLieu` |
| `lm_start_date` | DATE | **P1 Recommended** | Date LM plan began |
| `lm_end_date` | DATE | **P1 Recommended** | Forbearance / plan expiration date (renewal decision is critical) |
| `lm_status` | enum text | **P2 Optional** | `Active` / `Trial` / `Completed` / `Denied` / `Expired` |

> **Practical recommendation**: Prioritize `lm_flag` + `lm_type`. These two fields together cover 90% of business decision needs.

### Per-Servicer LM Data Coverage and Gaps

> **"In L2" column explained**: L2 = Redshift `port.basic_data_daily_loan_common`, the unified staging table where all servicer data is merged by ETL Step 1 with standardized field names (e.g. `lm_flag`, `svcdelinq`). "In L2" shows whether the servicer's raw LM field has been mapped by ETL Step 1 into `lm_flag = 'Y'/'N'` in L2. ✅ = written to L2; ❌ NULL = `lm_flag` is null in L2, meaning LM information is lost at the L2 stage and unavailable to all downstream tables.

| Servicer | Current LM fields | In L2 | Coverage | Action |
|---------|------------------|-------|---------|--------|
| **Newrez** | `activelmflag`('1'/'0') + `forbearancestatus` (numeric codes) | ✅ `lm_flag='Y'/'N'` | 🟡 Flag present; no type or dates | Request `lm_type` + `lm_start_date` |
| **Carrington** | `lm_flag`('Active'/other) + `covid_forbearance_flag` | ✅ `lm_flag='Y'/'N'` | 🟡 Flag present; no type or dates | Request `lm_type` + `lm_start_date` |
| **Selene** | `lm_setup_date` (non-null = active) | ✅ `lm_flag='Y'/'N'` (Step 3 absent) | 🟡 Flag present; no type | Fix Step 3 first; then request `lm_type` |
| **MRC** | `portmrcforbearance.status` (dedicated forbearance table) | ✅ `forbearance` field only; no `lm_flag` | 🟡 Forbearance present; no overall LM flag | Request top-level `lm_flag` + `lm_type` |
| **SLS** | None | ❌ NULL | ❌ | Request `lm_flag` + `lm_type` |
| **Arvest** | None | ❌ NULL | ❌ | Request `lm_flag` in monthly report |
| **CapeCodFive** | None | ❌ NULL | ❌ | Request `lm_flag` in monthly report |
| **FCI** | None | ❌ NULL | ❌ | Implement ETL first; then request `lm_flag` |

---

## Chinese Version

`docs/zh/08_servicer_fcl_field_mapping.md`
