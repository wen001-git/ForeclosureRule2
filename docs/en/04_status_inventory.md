# 04 — Complete Status Code Inventory

---

## Document Information

| Field | Content |
|-------|---------|
| **Purpose** | Authoritative inventory of all foreclosure/delinquency/REO/bankruptcy/loss mitigation status codes in the system, including each code's meaning, source field, generation layer, business usage, and lifecycle stage. |
| **Problem solved** | Status codes are scattered across multiple config files and processing layers, with raw servicer codes and standard codes intermixed. This document consolidates all codes in one place. |
| **Scope** | Layer 1 (raw servicer codes) → Layer 4 (normalized codes and special statuses); covers all 12 standard delinq values and supplementary flags |
| **System** | See `03_fcl_status_logic.md` |

**Target audience:** Business analysts · Data validation/reconciliation engineers · Report developers · Onboarding engineers

**Dependencies:** `01_source_data.md` (source fields), `03_fcl_status_logic.md` (generation logic)

**Revision history:**

| Date | Author | Version | Changes |
|------|--------|---------|---------|
| 2026-05-21 | AI Agent (Claude Sonnet 4.6) | v1 | Initial version, code reverse-engineering + DB evidence |

---

## 1. Normalized `delinq` Code Reference

`delinq` is the primary status field in core tables like `port.portmonthbase`, representing each loan's monthly delinquency/foreclosure status.

| Code | Meaning | Generation Layer | Source / Generation Method | Business Usage | Lifecycle Stage | DB Evidence |
|------|---------|-----------------|---------------------------|----------------|-----------------|-------------|
| `C` | Current (< 30 DPD) | Layer 2 | `days360(nextduedate, fctrdt) < 30` | Performing loan monitoring | Performing | 72,796 rows (92.2%) |
| `D30` | 30–59 days past due | Layer 2 | `days360 ∈ [30,60)` | Early delinquency tracking | Early delinquency | 2,274 rows (2.9%) |
| `D60` | 60–89 days past due | Layer 2 | `days360 ∈ [60,90)` | Delinquency escalation monitoring | Delinquency | 480 rows (0.6%) |
| `D90` | 90–119 days past due | Layer 2 | `days360 ∈ [90,120)` | Loss mitigation trigger | Serious delinquency | 206 rows (0.3%) |
| `D120P` | 120+ days past due | Layer 2 | `days360 ≥ 120` | FCL referral candidate | Serious delinquency | 403 rows (0.5%) |
| `FCL` | In foreclosure | Layer 2 | `svcdelinq='Foreclosure'` or `status='F'` | FCL tracking, loss analysis | Foreclosure | 279 rows (0.4%) |
| `REO` | Real Estate Owned (bank-acquired) | Layer 2 | `svcdelinq='REO'` or `status IN ('R','REO')` | REO disposition tracking | Post-foreclosure | 12 rows (0.02%) |
| `P` | Paid in full / liquidated | Layer 2 | `svcdelinq IN ('Full Payoff','Paid in Full',...)` or `balance=0` | Portfolio reduction analysis | Liquidation | 2,288 rows (2.9%) |
| `D` | Confirmed delinquency (re-entry post-FCL) | Layer 3 | `prevdelinq IN ('D120P','FCL','REO')` and still delinquent | Serious default history tracking | Delinquency re-entry | 273 rows (clean table) |
| `VASP` | Vendee/Servicer Purchase | Layer 4 | Operational override (likely `port.basic_data_loan_fix`), Newrez only | Government-backed loan special disposition | Special disposition | 19 rows |
| `REPUR` | Repurchase | Layer 4 | Servicer-specific logic or manual tagging, Carrington only | Repurchased loan tracking | Special disposition | 1 row |
| `NULL` | Not populated | — | Data missing or in-process | Data quality monitoring | — | 155 rows (0.2%) |

---

## 2. Supplementary Flag Fields

These fields coexist with `delinq`, providing additional status dimensions.

| Field | Values | Meaning | Generation Method |
|-------|--------|---------|------------------|
| `fcl_flag` | `1`/`0` or raw text | Servicer active FCL indicator | Newrez: `activefcflag`; SLS: `fcl_active_flag`; Carrington: `foreclosure_status_code`; MRC: `fc_flag` |
| `lm_flag` | `'Y'`/`'N'` | Loss mitigation active | Newrez: `activelmflag='1'→Y`; Carrington: `lm_flag='Active'→Y`; SLS: inferred from `loss_mit_evaluation_status` |
| `bankruptcy` | `'Y'`/`'N'` | Bankruptcy status | Newrez: `delinquency_status_mba LIKE '%Bankruptcy%'`; SLS: `bk_active_flag` |
| `prevdelinq` | Same code set as `delinq` | Prior month status | LAG window function over `portmonthbase ORDER BY fctrdt` |

---

## 3. Payment History Character Encoding

`paymthistfull` is assembled by concatenating monthly `prevdelinqchar` values (most recent first).

| `delinq` Code | `prevdelinqchar` | Character Meaning |
|--------------|-----------------|------------------|
| `FCL` | `F` | Foreclosure |
| `REO` | `R` | REO |
| `P` | `P` | Paid off |
| `D` | `D` | Confirmed delinquent |
| `C` | `0` | Current |
| `D30` | `1` | 30 days past due |
| `D60` | `2` | 60 days past due |
| `D90` | `3` | 90 days past due |
| `D120P` | `4` | 120+ days past due |

**Example history string:** `"F4432100000"` = 12-month payment record (left=newest, right=oldest); this loan progressed from FCL (F) back to current (0).

---

## 4. Raw Servicer Code Mapping

### 4.1 Newrez / Shellpoint (`delinquency_status_mba` field)

| Raw Value | Standard `delinq` | Notes |
|-----------|------------------|-------|
| `Current` | `C` (or `VASP`*) | VASP is a special override |
| `1-29 DPD` / `30-59 DPD` | `D30` | |
| `60-89 DPD` / `60-89` | `D60` | |
| `90-119 DPD` / `DQ 90` | `D90` | |
| `120-149 DPD` / `180+ DPD` | `D120P` | |
| `Foreclosure` | `FCL` | |
| `Foreclosure / Perf BK` | `FCL` | `bankruptcy='Y'` |
| `Foreclosure / Non-Perf BK` | `FCL` | `bankruptcy='Y'` |
| `REO` | `REO` | |
| `Full Payoff` / `Paid in Full` | `P` | |
| `Completed Short Sale` | `P` | |
| `Service Release` | `P` | |
| `Loss Mitigation` | days360 result | `lm_flag='Y'` |
| `Performing Bankruptcy` / `Bankruptcy - Performing` | days360 result | `bankruptcy='Y'` |
| `Non-Performing Bankruptcy` | days360 result | `bankruptcy='Y'` |

\* VASP (19 records): `delinquency_status_mba` is Current (10), 180+ DPD (8), Foreclosure (1) — all overridden to VASP

### 4.2 SLS (`delq_status_mba` field)

| Raw Value | Standard `delinq` |
|-----------|------------------|
| `C` | `C` |
| `D30` | `D30` |
| `D60` | `D60` |
| `D90` | `D90` |
| `D120+` | `D120P` |
| `FCL` | `FCL` |
| `REO` | `REO` |
| `P` | `P` |
| `REPUR` | `REPUR` (passed through) |

SLS raw codes are already close to standard format — simplest transformation of all servicers.

### 4.3 Carrington (`status` + `loan_status` fields)

| `status` Value | Standard `delinq` |
|---------------|------------------|
| `'F'` | `FCL` |
| `'R'` / `'REO'` | `REO` |
| `'P'` | `P` |
| Other | days360 calculation |

### 4.4 Interim Servicers (`svcdelinq` field)

| Raw Value | Standard `delinq` |
|-----------|------------------|
| `'Foreclosure'` | `FCL` |
| `'R'` / `'REO'` | `REO` |
| `'Completed Payoff'` | `P` |
| `balance = 0` (Arvest/Capecodfive) | `P` |
| Other | days360 calculation |

---

## 5. FCL Summary Status Codes (`summary_foreclosure_status`)

**Table:** `port.basic_data_loan_foreclosure`  
**DB evidence (43 active + 58 closed):**

| Summary Status | Records | Meaning |
|----------------|---------|---------|
| `Active Foreclosure` | 43 | FCL in progress |
| `Closed Foreclosure:Reinstated` | 25 | Closed (loan reinstated) |
| `Closed Foreclosure:Loss Mitigation` | 15 | Closed (entered loss mitigation) |
| `Closed Foreclosure:Paid in Full` | 10 | Closed (paid off) |
| `Closed Foreclosure:Process Complete` | 7 | Closed (auction/REO completed) |
| `Closed Foreclosure:Deed in Lieu Cmplte` | 1 | Closed (deed in lieu completed) |
| NULL | 5,942 | Not populated |

---

## 6. FCL Stage Codes (`port.fcl_stage_info.stage` field)

**DB evidence (8,733 total records):**

| Stage Code | Records | Business Meaning |
|------------|---------|-----------------|
| `DEMAND` | 448 | Demand letter / Notice of Intent issued |
| `REFERRAL` | 3,341 | Attorney referral |
| `FIRST_LEGAL` | 800 | First legal action filed |
| `SERVICE` | 1,486 | Legal document service |
| `JUDGEMENT` | 700 | Judgment phase |
| `SALE` | 1,958 | Foreclosure sale |

**Stage group values (`group` field):**

| Group | Records | Meaning |
|-------|---------|---------|
| `FCL` | 8,277 | Loans formally in foreclosure |
| `D120P` | 411 | 120+ DPD loans with stage tracking |
| `D90` | 39 | 90-day delinquent loans with stage tracking |
| `REO` | 6 | Loans already in REO |

---

## 7. Status Code Lifecycle Relationships

```
Performing
  C ──→ D30 ──→ D60 ──→ D90 ──→ D120P
                                   │
                                   ├──→ FCL ──→ SALE ──→ REO
                                   │              └──→ P (sale complete / paid off)
                                   │
                                   └──→ LM (lm_flag=Y) ──→ Modification success → C
                                                        └──→ Failed → FCL

Re-entry after FCL/REO:
  FCL/REO ──→ (current month still delinquent) ──→ D (confirmed delinquency)

Special statuses (operational layer):
  VASP (government-backed loan special disposition)
  REPUR (loan repurchase)
```

---

## Chinese Version

`docs/zh/04_status_inventory.md`
