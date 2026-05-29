# doc 11 — Servicer Current Data → New System FCL Implementation Guide

---

## Document Purpose

- **Why this document exists**: The new system has defined the Servicer data interface standard (doc 09), but servicers cannot immediately deliver data in that format. This document provides a new system FCL implementation plan based on **existing servicer data** — for each servicer, which fields to use, what logic to write, and which target fields can be populated.
- **Problem solved**: doc 08 is an analysis document (current state and gaps); doc 09 is a target specification (what should be). There is no **directly codeable developer implementation reference** between them — this document fills that gap.
- **Scope**:
  - Target fields: `foreclosure_flag` / `delinquency_status` / `lm_flag` / `hold_flag` / `hold_reason` / `bankruptcy_flag` / `foreclosure_stage` / `referral_date` / `sale_date_scheduled` / `sale_date_actual`
  - 8 servicers: SLS / Newrez / Carrington / Selene / MRC / Arvest / CapeCodFive / FCI
- **Not covered**: Full field business definitions (see doc 10 Glossary); target interface standard (see doc 09); current-state analysis details (see doc 08)
- **Lifespan**: This is a **transitional document**. As servicers adopt the doc 09 standard and provide new-format fields, the corresponding sections here should be updated or retired.

## Target Audience

Primary: New system ETL developers · Data engineers  
Secondary: System architects · Project managers (to understand current implementability)

## Revision History

| Date | Author | Version | Changes | Related |
|------|--------|---------|---------|---------|
| 2026-05-25 | AI Agent (Claude Sonnet 4.6) | v1 | Initial version, based on doc 08 DB-verified data (2026-05-25); includes Newrez portnewrezfc multi-hold handling | doc 08 / doc 09 |

## Dependencies

| Document | Relationship |
|----------|-------------|
| `docs/en/08_servicer_fcl_field_mapping.md` | Current-state analysis source — all field information and rules in this document are based on it |
| `docs/en/09_servicer_data_interface_standard.md` | Target interface standard — target field naming in this document aligns with it |
| `docs/en/10_glossary.md` | Term definition reference |

## Known Limitations

- Field value ranges and row counts are from DB verification (2026-05-25) and may need updating over time
- Step 3 logic for Selene / MRC / FCI has not yet been implemented; logic shown here describes **what should be implemented**, not current system behavior

---

## Section 1: Current Implementability Summary

> **Legend**: ✅ Fully implementable | 🟡 Partially implementable (field exists, logic needs adjustment) | ⚠️ Field exists but data quality issue | ❌ Not implementable (no field)

| Servicer | Freq | foreclosure_flag | delinquency_status | lm_flag | hold_flag | bankruptcy_flag | Overall |
|---------|------|-----------------|-------------------|---------|-----------|----------------|---------|
| **SLS** | Daily | 🟡 Text-derived, no independent flag | ✅ MBA text direct mapping | ❌ No field | ❌ No field | 🟡 Text-derived | 🟡 Moderate |
| **Newrez** | Daily | 🟡→✅ Main table text + portnewrezfc upgradeable | ✅ MBA text + compound values | ✅ activelmflag | 🟡 portnewrezfc has it, logic needed | 🟡 Text-derived | 🟡→✅ Large upgrade potential |
| **Carrington** | Daily | ✅ Dual field (text + independent flag) | ✅ loan_status mapping | ✅ lm_flag | ❌ No field | 🟡 Text-derived | ✅ Most complete |
| **Selene** | Daily | 🟡 Field exists, Step 3 pending | ❌ Non-standard loan_status | 🟡 lm_setup_date exists, Step 3 pending | ❌ No field | ❌ No field | ⚠️ Step 3 must be written |
| **MRC** | Daily | ❌ fc_flag never activated | ❌ min_status always empty | 🟡 Dedicated table exists, no top-level flag | ❌ No field | ❌ No field | ❌ Must confirm with MRC |
| **Arvest** | Monthly | ❌ No field | ❌ No delinquency status field | ❌ No field | ❌ No field | ❌ No field | ❌ Must request from Servicer |
| **CapeCodFive** | Monthly | ❌ No field | ⚠️ Numeric DPD (convertible, no FCL) | ❌ No field | ❌ No field | ❌ No field | ⚠️→❌ DPD only |
| **FCI** | Daily (API) | 🟡 Field exists, Step 3 pending | 🟡 Field exists, Step 3 pending | ❌ No field | ❌ No field | 🟡 `status='Bankruptcy'` | 🟡 ETL needs writing |

---

## Section 2: Implementation Roadmap

### Phase 1: Immediately actionable (no servicer cooperation needed — ETL logic only)

| Servicer | Work Required | Expected Benefit |
|---------|--------------|-----------------|
| **Newrez** | Use `portnewrezfc` fields: `activefcflag`, `fcstage`, `fcreferraldate`, `fcscheduledsaledate`, hold1/2/3 fields | Upgrade from "text-match only" to "active FCL flag + process stage + hold history" |
| **Selene** | Add Selene block to Step 3: `WHEN fcl_flag='A' THEN 'FCL'` (no new fields needed) | Activate 41 already-collected FCL records; `lm_setup_date` enables `lm_flag` |
| **FCI** | Add FCI processing logic to Step 3/ETL: `WHEN status='Foreclosure' THEN 'FCL'` | Activate 2,408 FCL records currently in MySQL but ignored |
| **CapeCodFive** | Convert numeric DPD strings to banded delinquency codes | At minimum restore DPD determination (FCL still requires servicer request) |

### Phase 2: Requires servicer field requests

| Servicer | Fields to Request | Priority | What's Blocked |
|---------|------------------|---------|---------------|
| **Arvest** | `delinquency_status` (including `'Foreclosure'`) or `foreclosure_flag` + `lm_flag` + `lm_type` | P0 | FCL can never be produced |
| **CapeCodFive** | Text-based `delinquency_status` or `foreclosure_flag` + `lm_flag` + `lm_type` | P0 | FCL can never be produced |
| **MRC** | Investigate why `min_status` is empty + request alternative delinquency field or `foreclosure_flag` | P0 | FCL determination impossible |
| **SLS** | `lm_flag` + `lm_type` (can use `portfcldaily` for FCL cross-validation) | P1 | LM status unavailable |
| **All servicers** | `lm_type` + `lm_start_date` + `lm_end_date` (only Carrington/Newrez/Selene have lm_flag) | P1–P2 | LM sub-type classification unavailable |

---

## Section 3: Per-Servicer Implementation Recipes

> **Field naming convention**: Target field names use doc 09 standard interface names. Source fields are annotated as `` `schema.table.field` ``.

---

### 3.1 SLS (Daily report, data through 2024-07-05 then transferred to Newrez)

**Source tables**: `sls.portassetdaily` (main daily report), `sls.portfcldaily` (FCL dedicated, currently unused)

#### `delinquency_status` (target field)
```sql
-- Source: sls.portassetdaily.delq_status_mba
CASE delq_status_mba
    WHEN 'Paid in Full'     THEN 'PaidOff'
    WHEN 'Service Release'  THEN 'PaidOff'   -- servicing rights transfer
    WHEN 'REO'              THEN 'REO'
    WHEN 'Foreclosure'      THEN 'Foreclosure'
    WHEN 'Bankruptcy'       THEN 'DQ120P'    -- also set bankruptcy_flag='Y'
    WHEN 'DQ 30'            THEN 'DQ30'
    WHEN 'DQ 60'            THEN 'DQ60'
    WHEN 'DQ 90'            THEN 'DQ90'
    WHEN 'Current'          THEN 'Current'
    ELSE days360_fallback(nextduedate)       -- fallback
END
```

#### `foreclosure_flag` (target field)
```sql
-- ⚠️ No independent FCL flag — text-derived only (delayed status risk)
CASE WHEN delq_status_mba = 'Foreclosure' THEN 'Y' ELSE 'N' END
```
> **Known issue**: SLS provides `portfcldaily` (FCL dedicated file) but the system does not use it. Recommended P1 action: use `portfcldaily.fcl_status` as a cross-validation source.

#### `bankruptcy_flag` (target field)
```sql
CASE WHEN delq_status_mba = 'Bankruptcy' THEN 'Y' ELSE 'N' END
```

#### Fields not achievable (must request from SLS)
- `lm_flag` ❌ — no LM fields in SLS data at all
- `hold_flag` ❌ — no field
- `foreclosure_stage` ❌ — may exist in `portfcldaily`, to be confirmed

---

### 3.2 Newrez (Daily report, from 2024-07-05 replacing SLS)

**Source tables**: `newrez.portnewrezgeneral` (main daily), `newrez.portnewrezfc` (FCL dedicated ⭐), `newrez.portnewrezlm` (LM dedicated)

> **⭐ Important**: Newrez has the richest FCL data among all servicers. `portnewrezfc` provides most of the fields doc 09 Group C/F requires, but the **current system barely uses it**. The implementation plan below fully leverages `portnewrezfc`.

#### `delinquency_status` (target field)
```sql
-- Source: newrez.portnewrezgeneral.delinquency_status_mba
CASE
    WHEN delinquency_status_mba IN ('Full Payoff', 'Paid in Full',
         '3rd Party Sale', 'REO Sale', 'Service Release') THEN 'PaidOff'
    WHEN delinquency_status_mba = 'REO'                   THEN 'REO'
    WHEN delinquency_status_mba IN ('Foreclosure',
         'Foreclosure / Non-Perf BK',
         'Foreclosure / Perf BK')                         THEN 'Foreclosure'
    WHEN delinquency_status_mba LIKE '%Bankruptcy%'        THEN 'DQ120P'
         -- also set bankruptcy_flag='Y'
    WHEN delinquency_status_mba = '1-29 DPD'              THEN 'Current'
    WHEN delinquency_status_mba = '30-59 DPD'             THEN 'DQ30'
    WHEN delinquency_status_mba = '60-89 DPD'             THEN 'DQ60'
    WHEN delinquency_status_mba = '90-119 DPD'            THEN 'DQ90'
    WHEN delinquency_status_mba IN
         ('120-149 DPD', '150-179 DPD', '180+ DPD')       THEN 'DQ120P'
    WHEN delinquency_status_mba = 'Current'               THEN 'Current'
    ELSE days360_fallback(nextduedate)
END
```

#### `foreclosure_flag` (target field)
```sql
-- Option A (currently usable, text-derived):
CASE WHEN delinquency_status_mba IN (
    'Foreclosure', 'Foreclosure / Non-Perf BK', 'Foreclosure / Perf BK'
) THEN 'Y' ELSE 'N' END

-- Option B (recommended — uses portnewrezfc, no new fields needed from Servicer):
-- JOIN newrez.portnewrezfc ON loanid = loanid AND dataasof = dataasof
CASE WHEN portnewrezfc.activefcflag = 1 THEN 'Y' ELSE 'N' END
```

#### `foreclosure_stage` (target field, from portnewrezfc)
```sql
-- Source: newrez.portnewrezfc.fcstage / lastfcstepcompleted
-- Mapping (raw values to be confirmed via DISTINCT query on fcstage):
CASE fcstage
    WHEN 'Referral'     THEN 'Referral'
    WHEN 'First Legal'  THEN 'FirstLegal'
    WHEN 'Service'      THEN 'Service'
    WHEN 'Judgment'     THEN 'Judgment'
    WHEN 'Sale'         THEN 'Sale'
    ELSE fcstage   -- preserve raw value pending standardization
END
```

#### `referral_date` / `sale_date_scheduled` / `sale_date_actual` (from portnewrezfc)
```sql
portnewrezfc.fcreferraldate         → referral_date
portnewrezfc.fcscheduledsaledate    → sale_date_scheduled
portnewrezfc.fcsalehelddate         → sale_date_actual
portnewrezfc.fcsetupdate            → foreclosure_start_date
portnewrezfc.fcresults              → fcl_exit_type (mapping TBD)
```

#### `hold_flag` / `hold_reason` / `hold_start_date` (from portnewrezfc — multi-hold handling)

> **Context**: Newrez provides up to 3 historical hold records in `portnewrezfc` (`fchold1` / `fchold2` / `fchold3`). The new system standard interface needs "current active hold." Derivation logic:

```sql
-- Identify current active hold (priority: hold3 → hold2 → hold1, take first with null enddate)
CASE
    WHEN fchold3startdate IS NOT NULL AND fchold3enddate IS NULL
        THEN 3   -- hold3 is active
    WHEN fchold2startdate IS NOT NULL AND fchold2enddate IS NULL
        THEN 2   -- hold2 is active
    WHEN fchold1startdate IS NOT NULL AND fchold1enddate IS NULL
        THEN 1   -- hold1 is active
    ELSE NULL    -- no active hold
END AS active_hold_num

-- Corresponding field mappings:
hold_flag       = CASE WHEN active_hold_num IS NOT NULL THEN 'Y' ELSE 'N' END
hold_reason     = CASE active_hold_num
                      WHEN 3 THEN fchold3description
                      WHEN 2 THEN fchold2description
                      WHEN 1 THEN fchold1description
                  END
hold_start_date = CASE active_hold_num
                      WHEN 3 THEN fchold3startdate
                      WHEN 2 THEN fchold2startdate
                      WHEN 1 THEN fchold1startdate
                  END
```

> **Hold history** (non-standard interface, optional for analytics): `fchold1/2/3 description/startdate/enddate` provides the complete FCL pause history across up to 3 events.

#### `lm_flag` (from portnewrezlm)
```sql
-- Source: newrez.portnewrezlm.activelmflag
CASE WHEN activelmflag = '1' THEN 'Y' ELSE 'N' END
```

#### `bankruptcy_flag`
```sql
CASE WHEN delinquency_status_mba LIKE '%Bankruptcy%' THEN 'Y' ELSE 'N' END
```

#### Fields not achievable (must request from Newrez)
- `lm_type` ❌ — `forbearancestatus` exists but is a numeric code; cannot distinguish Forbearance vs Modification
- `lm_start_date` / `lm_end_date` ❌ — no field

---

### 3.3 Carrington (Daily report — most complete servicer)

**Source table**: `carrington.portcarrington` (comprehensive daily report containing both delinquency status and FCL flag)

#### `delinquency_status` (target field)
```sql
-- Source: carrington.portcarrington.loan_status
CASE
    WHEN loan_status IN ('Completed Payoff', 'Completed Short Sale',
         'Completed REO Sale')                THEN 'PaidOff'
    WHEN loan_status IN ('R', 'REO')          THEN 'REO'
    WHEN loan_status = 'Foreclosure'
         OR fcl_flag = 'Active'               THEN 'Foreclosure'
    WHEN loan_status LIKE '%Bankruptcy%'       THEN 'DQ120P'
         -- also set bankruptcy_flag='Y'
    WHEN loan_status IN ('CUR', 'Current',
         '0-29')                              THEN 'Current'
    WHEN loan_status = '30-59'                THEN 'DQ30'
    WHEN loan_status = '60-89'                THEN 'DQ60'
    WHEN loan_status = '90-119'               THEN 'DQ90'
    WHEN loan_status = '120+'                 THEN 'DQ120P'
    ELSE days360_fallback(nextduedate)
END
```

#### `foreclosure_flag` (target field)
```sql
-- ✅ Dual-field OR check — the reference pattern for other servicers
CASE WHEN loan_status = 'Foreclosure' OR fcl_flag = 'Active'
     THEN 'Y' ELSE 'N' END
```

#### `lm_flag` (target field)
```sql
-- Source: carrington.portcarrington.lm_flag and loan_status
CASE WHEN lm_flag = 'Active' OR loan_status = 'Loss Mitigation'
     THEN 'Y' ELSE 'N' END
```

#### `bankruptcy_flag`
```sql
CASE WHEN loan_status LIKE '%Bankruptcy%' THEN 'Y' ELSE 'N' END
```

#### Fields not achievable (must request from Carrington)
- `hold_flag` ❌ — no field
- `lm_type` ❌ — cannot distinguish Forbearance vs Modification (`lm_flag` is only 'Active'/'Inactive')
- `lm_start_date` / `lm_end_date` ❌ — no field

---

### 3.4 Selene (Daily report — Step 3 pending)

**Source table**: `selene.portselenemain` (main daily report)

> ⚠️ **Current state**: No Selene Step 3 processing block in ETL at all. The following is **what should be implemented**.

#### `foreclosure_flag` (target field)
```sql
-- Source: selene.portselenemain.foreclosure_status_code
-- DB verified: 'A' = Active FCL (41 rows); 'R' = Released/Resolved (100 rows); '' = no FCL
CASE WHEN foreclosure_status_code = 'A' THEN 'Y' ELSE 'N' END
```

#### `delinquency_status` (target field)
```sql
-- ⚠️ loan_status has no 'Foreclosure' value; foreclosure_status_code must override first
CASE
    WHEN foreclosure_status_code = 'A'     THEN 'Foreclosure'
    WHEN loan_status = 'Liquidated'        THEN 'PaidOff'
    -- Other loan_status values (No Contact / In Contact / Lost Contact)
    -- cannot be mapped to delinquency bands
    -- Only reliable delinquency fallback is days360
    ELSE days360_fallback(nextduedate)
END
```

#### `lm_flag` (target field)
```sql
-- Source: selene.portselenemain.lm_setup_date
CASE WHEN lm_setup_date IS NOT NULL THEN 'Y' ELSE 'N' END
```

#### Fields not achievable (must request from Selene)
- `lm_type` ❌ — no field
- `lm_end_date` ❌ — no field (critical: cannot know if LM has expired)
- `hold_flag` ❌ — no field
- `bankruptcy_flag` ❌ — no field

---

### 3.5 MRC (Daily report — field anomalies, MRC confirmation required)

**Source tables**: `mrc.portmrcloan` (main daily), `mrc.portmrcforeclosure` (FCL dedicated, only 18 rows)

> ❌ **Current state**: Both key fields are non-functional — `min_status` is always an empty string; `fc_flag` has never been 'Y'. Step 3 also does not exist. No FCL determination is possible.

#### Required investigations (must complete before implementation)

| Question | Investigation Approach |
|---------|----------------------|
| Why is `portmrcloan.min_status` always empty? | Contact MRC; check `portmrcforeclosure` other fields (`fc_status`, `fc_milestone`) as alternatives |
| Why is `portmrcforeclosure.fc_flag` never activated? | `referral_hold_reason` field shows FCL text — confirm what triggers `fc_flag='Y'` |
| Is there an alternative delinquency status field? | Query full `portmrcloan` column list for any other DPD or status field |

#### Currently achievable (fallback only)
```sql
-- Fully degrades to days360 (no reliable status field available)
days360_fallback(nextduedate)
```

#### `lm_flag` (partially achievable)
```sql
-- Source: mrc.portmrcforbearance.status (dedicated table, no top-level flag)
-- Requires JOIN to portmrcforbearance
CASE WHEN portmrcforbearance.status IN ('Active', ...) THEN 'Y' ELSE 'N' END
```

---

### 3.6 Arvest (Monthly report — no delinquency status field)

**Source table**: `arvest.portarvestremitmonthlystatement` (monthly loan statement)

> ❌ **Critical limitation**: Arvest monthly reports contain no delinquency status field whatsoever. FCL can never be produced; all FCL loans are misclassified as D120P.

#### Currently achievable (DPD fallback only)
```sql
-- Fully degrades to days360
-- Source: arvest.portarvestremitmonthlystatement.nextduedate
days360_fallback(nextduedate)
```

#### Field request list for Arvest (P0 priority)
- `delinquency_status` (including `'Foreclosure'` / `'REO'`) **or** `foreclosure_flag` (`Y/N`)
- `lm_flag` + `lm_type` (request in same batch)

---

### 3.7 CapeCodFive (Monthly report — value format mismatch)

**Source table**: `capecodfive.portcapecodfive_monthly_servicing` (monthly servicing report)

> ⚠️ **Key finding**: Field name is `mba_delinquency_status`, but actual values are numeric DPD strings (`'29.0'`, `'60.0'`) rather than text status codes. All FCL text matching permanently fails.

#### `delinquency_status` (DPD numeric conversion approach)
```sql
-- Source: capecodfive.portcapecodfive_monthly_servicing.mba_delinquency_status
-- Convert numeric DPD string to banded delinquency code (restores DPD, not FCL/REO)
CASE
    WHEN TRY_CAST(mba_delinquency_status AS FLOAT) < 30   THEN 'Current'
    WHEN TRY_CAST(mba_delinquency_status AS FLOAT) < 60   THEN 'DQ30'
    WHEN TRY_CAST(mba_delinquency_status AS FLOAT) < 90   THEN 'DQ60'
    WHEN TRY_CAST(mba_delinquency_status AS FLOAT) < 120  THEN 'DQ90'
    WHEN TRY_CAST(mba_delinquency_status AS FLOAT) >= 120 THEN 'DQ120P'
    ELSE days360_fallback(next_payment_due_date)
END
-- ⚠️ Note: this conversion cannot produce 'Foreclosure' or 'REO' values
```

#### Field request list for CapeCodFive (P0 priority)
- `delinquency_status` (text-based, including `'Foreclosure'` / `'REO'`) **or** `foreclosure_flag` (`Y/N`)
- `lm_flag` + `lm_type` (request in same batch)

---

### 3.8 FCI (Daily API report — ETL pending)

**Source table**: `fci.portfciloanportfolio` (collected via GraphQL API)

> ⚠️ **Current state**: 2,408 FCL records are in MySQL but completely absent from ETL processing. No Step 3 exists.

#### `delinquency_status` + `foreclosure_flag` (target fields — pending implementation)
```sql
-- Source: fci.portfciloanportfolio.status
-- ⚠️ Note: column name is 'status' (lowercase), NOT 'loanStatus'
CASE status
    WHEN 'Paid off'        THEN 'PaidOff'
    WHEN 'Transfer out'    THEN 'PaidOff'
    WHEN 'Closed'          THEN 'PaidOff'
    WHEN 'REO'             THEN 'REO'
    WHEN 'Foreclosure'     THEN 'Foreclosure'
    WHEN 'Pre Foreclosure' THEN 'Foreclosure'  -- confirm business meaning
    WHEN 'Delinquency'     THEN days360_fallback(...)
    WHEN 'Performing'      THEN 'Current'
    WHEN 'Bankruptcy'      THEN 'DQ120P'       -- also set bankruptcy_flag='Y'
    ELSE days360_fallback(...)
END

-- foreclosure_flag:
CASE WHEN status IN ('Foreclosure', 'Pre Foreclosure') THEN 'Y' ELSE 'N' END
```

#### `bankruptcy_flag`
```sql
CASE WHEN status = 'Bankruptcy' THEN 'Y' ELSE 'N' END
```

#### Fields not achievable (must request from FCI)
- `lm_flag` ❌ — no LM fields in FCI data
- `hold_flag` ❌ — no field

---

## Section 4: Reference — Newrez `portnewrezfc` Available Fields

The following fields directly correspond to doc 09 Group C/F target fields and can be used in ETL immediately (no new fields needed from Newrez):

| doc 09 Target Field | Source Field (`newrez.portnewrezfc.*`) |
|--------------------|---------------------------------------|
| `foreclosure_flag` | `activefcflag` (1=Y, 0=N) |
| `foreclosure_stage` | `fcstage` / `lastfcstepcompleted` |
| `foreclosure_start_date` | `fcsetupdate` |
| `referral_date` | `fcreferraldate` |
| `sale_date_scheduled` | `fcscheduledsaledate` |
| `sale_date_actual` | `fcsalehelddate` |
| `fcl_exit_type` | `fcresults` |
| `hold_flag` (current) | Derived from hold1/2/3 (see Section 3.2) |
| `hold_reason` (current) | Derived from fchold1/2/3description (see Section 3.2) |
| `hold_start_date` | Derived from fchold1/2/3startdate (see Section 3.2) |

> These fields are **already provided by Newrez**. The system only needs to write ETL logic to read and map them — no Servicer field requests required.
