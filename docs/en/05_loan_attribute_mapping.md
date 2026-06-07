# 05 — Loan Attribute ↔ FCL Status Mapping

> **Naming note (2024-07-05):** the source-table prefix is now `portnewrez*` (formerly `portshellpoint*`, the Shellpoint era); the live `newrez` schema only has `portnewrez*` — authoritative now; rename history in doc 01.

---

## Document Information

| Field | Content |
|-------|---------|
| **Purpose** | Systematic mapping of all loan attribute fields that influence FCL/delinquency status generation, explaining each field's decision weight, processing layer, source servicer, and how combinations produce final status values. |
| **Problem solved** | Status generation depends on multi-field combinations; looking at any single field in isolation does not reveal the complete logic. This document visualizes each field's "input role" for debugging and rewrite purposes. |
| **Scope** | Primary determinants (directly generate `delinq`), supplementary status attributes (populate FCL detail tables), manual override fields |
| **System** | `portdaily_config.py`, `gen_portmonth_config.py`, `portmonth_config.py` |

**Target audience:** Data engineers · System rewrite architects · Validation/reconciliation engineers · Business analysts

**Dependencies:** `01_source_data.md` (field definitions), `03_fcl_status_logic.md` (generation logic), `04_status_inventory.md` (status codes)

**Revision history:**

| Date | Author | Version | Changes |
|------|--------|---------|---------|
| 2026-06-05 | AI Agent (Claude Opus 4.8) | v2 | Renamed `portshellpoint*`→`portnewrez*` (DB-verified live newrez tables; renamed 2024-07-05) + naming note (DB-verified; doc 01) |
| 2026-05-21 | AI Agent (Claude Sonnet 4.6) | v1 | Initial version, code reverse-engineering + DB evidence |

---

## 1. Primary Determinants: Fields That Directly Influence `delinq` Generation

### 1.1 Priority Order (Highest to Lowest)

```
Priority 1 ── Manual override (final correction)
  └── basic_data_loan_fix.delinq (active when start_date ≤ fctrdt < end_date)

Priority 2 ── Paid-in-full keywords (immediate exit from FCL pipeline)
  └── svcdelinq IN ('Full Payoff','Paid in Full','Completed Payoff',
                    'Completed Short Sale','Service Release')
  └── balance = 0 (Arvest/Capecodfive only)

Priority 3 ── REO status
  └── svcdelinq = 'REO'
  └── status IN ('R','REO')  [Carrington]

Priority 4 ── Foreclosure status
  └── svcdelinq = 'Foreclosure'
  └── svcdelinq IN ('Foreclosure / Perf BK','Foreclosure / Non-Perf BK')
  └── status = 'F'  [Carrington]

Priority 5 ── days360 DPD calculation (fallback)
  └── days360(nextduedate, fctrdt) bucketing → C/D30/D60/D90/D120P
```

### 1.2 Primary Determinant Fields — Detail

| Field | Type | Layer | Servicer | Role |
|-------|------|-------|----------|------|
| `port.basic_data_loan_fix.delinq` | VARCHAR | Layer 4 (override) | All (manual) | Highest priority: directly overrides all auto-generated delinq |
| `svcdelinq` | VARCHAR | Layer 1→2 | Newrez, Interim | Raw servicer delinquency description; contains "Foreclosure"/"REO"/"Full Payoff" etc. |
| `delinquency_status_mba` | VARCHAR | Layer 1→2 | Newrez (MySQL) | Newrez-specific MBA standard delinquency description (17 raw values) |
| `delq_status_mba` | VARCHAR | Layer 1→2 | SLS | SLS MBA delinquency code (already near-standard) |
| `status` | VARCHAR | Layer 1→2 | Carrington | Carrington single-char status: F/R/REO/P/other |
| `nextduedate` | DATE | Layer 2 | All | Next payment due date: combined with `fctrdt` to calculate DPD |
| `fctrdt` | DATE | Layer 2 | All | Report cutoff date (first of following month): baseline for days360 calculation |
| `balance` | DECIMAL | Layer 2 | Arvest/Capecodfive | Loan balance: balance=0 forces `P` |
| `prevdelinq` | VARCHAR | Layer 3 | All | Prior month status: triggers generation of `D` (confirmed delinquency) |

---

## 2. Supplementary Attributes: Populating FCL Detail Tables

These fields do not directly determine `delinq`, but provide supplementary status information through the 7 FCL detail tables.

### 2.1 Foreclosure Detail Attributes

| Field | Source Servicer | Source Table | Target Table | Usage |
|-------|----------------|-------------|-------------|-------|
| `activefcflag` / `fcl_active_flag` / `fc_flag` | Newrez/SLS/MRC | Servicer MySQL | `port.basic_data_loan_foreclosure` | Active FCL flag |
| `fcstage` / `fcl_current_status_desc` | Newrez/SLS | `portnewrezfc`/`portfcldaily` | `port.basic_data_loan_fcl`, `port.fcl_stage_info` | Current FCL stage |
| `fcsetupdate` | Newrez | `portnewrezfc` | `port.basic_data_loan_fcl` | FCL setup date |
| `fcreferraldate` / `fcl_referred_to_attorney_date` | Newrez/SLS | Servicer FC table | `port.fcl_stage_info.referral_start_date` | Attorney referral date |
| `firstlegaldate` / `fcl_first_legal_action_date` | Newrez/SLS | Servicer FC table | `port.fcl_stage_info.legal_start_date` | First legal action date |
| `servicecompletedate` / `fcl_service_complete_date` | Newrez/SLS | Servicer FC table | `port.fcl_stage_info.service_start_date` | Service completion date |
| `fcjudgmenthearingscheduled` / `fcl_judgement_entered_date` | Newrez/SLS | Servicer FC table | `port.fcl_stage_info.judgement_start_date` | Judgment date |
| `fcscheduledsaledate` / `fcl_sale_scheduled_date` | Newrez/SLS | Servicer FC table | `port.fcl_stage_info.sale_start_date` | Scheduled sale date |
| `fcsalehelddate` / `fcl_sale_held_date` | Newrez/SLS | Servicer FC table | `port.basic_data_loan_fcl` | Actual sale date |
| `fcresults` | Newrez | `portnewrezfc` | `port.basic_data_loan_fcl` | Foreclosure outcome description |
| `fcremovaldesc` / `fcremovaldate` | Newrez | `portnewrezfc` | `port.basic_data_loan_fcl` | Removal reason and date |
| `judicial` | Newrez | `portnewrezfc` | `port.basic_data_loan_fcl` | Judicial foreclosure flag |
| `daysinfc` / `fcl_days` | Newrez/SLS | Servicer FC table | `port.basic_data_loan_foreclosure` | Days in foreclosure |
| `fcbidamount` / `fcsaleamount` | Newrez/SLS | Servicer FC table | `port.basic_data_loan_fcl` | Bid/sale amounts |

### 2.2 Hold Attributes

| Field | Source | Target Table | Usage |
|-------|--------|-------------|-------|
| `fchold1description` / `fchold2description` / ... | Newrez `portnewrezfc` | `port.basic_data_loan_foreclosure_hold`, `port.basic_data_loan_fcl` | FCL hold reasons (up to 4 levels) |
| `fchold1startdate` / `fchold1enddate` | Newrez | Same | Hold start/end dates |
| `fchold1projectedenddate` | Newrez | Same | Projected end date |
| `fchold1comment` | Newrez | Same | Hold notes/comments |

**DB evidence:** 30 distinct hold descriptions; `Loss Mitigation Workout` (58 records) and `Service Delay` (50 records) are most common.

### 2.3 Bankruptcy (BK) Attributes

| Field | Source Servicer | Source Table | Target Table | Usage |
|-------|----------------|-------------|-------------|-------|
| `activebkflag` / `bk_active_flag` | Newrez/SLS | BK table | `port.basic_data_loan_foreclosure_bankruptcy` | Active BK flag |
| `bkstatus` | Newrez | `portnewrezbk` | Same | Bankruptcy status code |
| `bkchapter` / `bk_chapter_code` | Newrez/SLS | BK table | Same | Bankruptcy chapter (7/11/13) |
| `bkfileddate` / `bk_filed_date` | Newrez/SLS | BK table | Same | BK filing date |
| `mfrfileddate` / `mfrhearingdate` | Newrez | `portnewrezbk` | Same | MFR (Motion for Relief) dates |
| `bkcasenumber` | Newrez | `portnewrezbk` | Same | Bankruptcy case number |

`bankruptcy` flag (Y/N) generation:
- Newrez: `delinquency_status_mba LIKE '%Bankruptcy%'` → `'Y'`
- SLS: `bk_active_flag='1'` → `'Y'`

### 2.4 Loss Mitigation (LM) Attributes

| Field | Source Servicer | Source Table | Target Table | Usage |
|-------|----------------|-------------|-------------|-------|
| `activelmflag` | Newrez | `portnewrezlm` | `port.basic_data_loan_foreclosure_loss_mitigation` | Active LM flag |
| `lmstatus` | Newrez | `portnewrezlm` | Same | LM status code |
| `lmdeal` / `lmprogram` | Newrez | `portnewrezlm` | Same | LM deal/program type |
| `loss_mit_evaluation_status` | SLS | `portlmdaily` | Same | SLS LM evaluation status |
| `loss_mit_workout_type_code_desc` | SLS | `portlmdaily` | Same | SLS workout type description |
| `lm_flag` | Carrington | `portcarrington` | Same | Carrington LM flag (`'Active'`=Y) |

`lm_flag` supplementary flag (Y/N) generation:
- Newrez: `activelmflag='1'` → `'Y'`
- Carrington: `lm_flag='Active'` → `'Y'`
- SLS: inferred from `loss_mit_evaluation_status`

### 2.5 REO and Liquidation Attributes

| Field | Source | Target Table | Usage |
|-------|--------|-------------|-------|
| `reo_start_date` | SLS `portassetdaily` | `port.basic_data_loan_reo` | REO start date |
| `liquidationdate` / `liquidationtype` | Newrez/other | `port.basic_data_fcl_related` | Liquidation date/type |
| `liquidationproceeds` | Newrez/other | `port.basic_data_fcl_related` | Liquidation proceeds |
| `inauctionflag` | Newrez | `port.basic_data_fcl_related` | In-auction flag |

---

## 3. Field Combination Decision Matrix

This table shows how field combinations determine final loan status:

| Scenario | Key Fields | Final delinq | Final Supplementary Flags |
|----------|-----------|-------------|--------------------------|
| Performing loan | `days360 < 30` | `C` | fcl_flag=0, lm_flag=N, bankruptcy=N |
| Mild delinquency | `30 ≤ days360 < 60` | `D30` | fcl_flag=0 |
| In foreclosure | `svcdelinq='Foreclosure'` | `FCL` | fcl_flag=1 |
| FCL + loss mitigation | `svcdelinq='Foreclosure'`, `activelmflag='1'` | `FCL` | fcl_flag=1, lm_flag=Y |
| FCL + bankruptcy | `svcdelinq='Foreclosure / Perf BK'` | `FCL` | fcl_flag=1, bankruptcy=Y |
| REO | `svcdelinq='REO'` or `status='R'` | `REO` | — |
| Paid in full | `svcdelinq='Full Payoff'` | `P` | — |
| Zero balance | `balance=0` (Arvest) | `P` | — |
| Confirmed delinq (re-entry) | `prevdelinq IN (FCL,REO,D120P)` + still delinquent | `D` | — |
| VASP (gov. loan) | Operational override (Newrez) | `VASP` | — |
| Manual correction | Record exists in `port.basic_data_loan_fix` | Overrides any auto value | Broadest override scope |

---

## 4. Field Weight Summary Diagram

```
Loan Attribute Fields
    │
    ├── Required (delinq=NULL if missing)
    │     ├── nextduedate    ← days360 base input
    │     └── fctrdt         ← days360 base input
    │
    ├── Status determinants (highest auto priority)
    │     ├── svcdelinq / delinquency_status_mba / delq_status_mba / status
    │     │     └── Overrides days360 calculation result
    │     └── balance = 0   ← Arvest/Capecodfive special case
    │
    ├── Manual override (absolute highest priority)
    │     └── basic_data_loan_fix.delinq
    │
    ├── Supplementary flags (generated in parallel, independent of delinq)
    │     ├── activefcflag / fcl_active_flag → fcl_flag
    │     ├── activelmflag / lm_flag         → lm_flag
    │     └── bk_active_flag / mbadelinq     → bankruptcy
    │
    └── Temporal context (Layer 3 addition)
          └── prevdelinq (LAG)
                └── Triggers D (confirmed delinquency) logic
```

---

## 5. Handling Missing / Anomalous Fields

| Scenario | Field | Handling | Result |
|----------|-------|----------|--------|
| `nextduedate` is NULL | days360 not computable | Other CASE-WHEN branches catch it | Possibly NULL or default |
| `svcdelinq` matches no keyword | Falls through to ELSE branch | days360 calculation used | C/D30/D60/D90/D120P |
| SLS historical data (pre-2024-07-05) | Left side of `port.portdaily_v2` UNION ALL | SLS fields used directly | Already near-standard |
| Newrez data (post-2024-07-05) | Right side of `port.portdaily_v2` UNION ALL | Newrez field mapping applied | Requires CASE-WHEN mapping |
| Servicer switch transition period | `SLS_TO_NEWREZ_DATE='2024-07-05'` | Time-range UNION ALL | Each side uses its own fields |

---

## Chinese Version

`docs/zh/05_loan_attribute_mapping.md`
