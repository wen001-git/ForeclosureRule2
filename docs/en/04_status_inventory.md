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

> **📅 Data date (unified statement)**: all counts are from **prod** (`redshift_prod`/`mysql_prod`), never dev. Per-table as-of differs: `port.portmonthbase` (delinq) = **2025-08-01** (frozen there in prod); `port.fcl_stage_info` (stages, §6) = **2026-06-07**. §6 stage counts are split into two methods (latest snapshot / cumulative), each with as-of and SQL.

**Revision history:**

| Date | Author | Version | Changes |
|------|--------|---------|---------|
| 2026-05-21 | AI Agent (Claude Sonnet 4.6) | v1 | Initial version, code reverse-engineering + DB evidence |
| 2026-06-10 | AI Agent (Claude Opus 4.8) | v2 | §6 stage counts corrected to **two methods** (6.1 latest snapshot as-of 2026-06-07, 41 rows; 6.2 cumulative 302 snapshots, 9,587 rows) with method note + SQL; fixed the old undated "8,733" (prod-verified) |

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
| `C` | `C` | Current |
| `D30` | `1` | 30 days past due |
| `D60` | `2` | 60 days past due |
| `D90` | `3` | 90 days past due |
| `D120P` | `4` (also `5`–`9`) | 120+ days past due |

> **DB-verified correction (`port.basic_data_monthly_loan_clean_data_delinq`, fctrdt=2026-07-01)**: Current is encoded as **`C`** (not the old doc's `0`); `5`–`9` also map to `D120P`. Trust the live data.

**Example history string (real, loan `7727000088`):** `paymthistfull = "RFFFFFFFFFFFF4321CC1C11CCCCCC11CCCCCCCC1C"` (left=newest, right=oldest). Reading it: leftmost `R` = currently REO ← 12×`F` = the prior 12 months in foreclosure ← `4321` = earlier delinquency escalation (D120P→D90→D60→D30) ← mostly `C` on the right = earliest, performing. In time order (right→left): Current → escalating delinquency → FCL → now REO.

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

> **Counting method**: `port.fcl_stage_info` is stored as daily `fctrdt` snapshots (one row per in-FCL loan per day). Both methods are listed below — use **6.1 latest snapshot** for "loans currently in the FCL pipeline", **6.2 cumulative** for "historical data volume". Do not mix them.

### 6.1 Single latest snapshot (loans currently in the FCL pipeline)

- **Method**: single latest snapshot `fctrdt = MAX(fctrdt)`. **As-of 2026-06-07**, **41 rows** (all `group=FCL`).
- **SQL**:

```sql
SELECT stage, COUNT(*) AS n FROM port.fcl_stage_info
WHERE fctrdt=(SELECT MAX(fctrdt) FROM port.fcl_stage_info)
GROUP BY stage ORDER BY n DESC;
```

| Stage Code | Records | Business Meaning |
|------------|---------|-----------------|
| `REFERRAL` | 20 | Attorney referral |
| `SALE` | 8 | Foreclosure sale |
| `FIRST_LEGAL` | 7 | First legal action filed |
| `SERVICE` | 4 | Legal document service |
| `JUDGEMENT` | 2 | Judgment phase |
| `DEMAND` | 0 | Demand letter / Notice of Intent issued |

Stage groups (latest snapshot): `FCL` 41 · `D120P` 0 · `D90` 0 · `REO` 0.

### 6.2 Cumulative across all fctrdt (historical data volume · loan-day)

- **Method**: cumulative across all `fctrdt` (no date filter; one row per loan per snapshot day = loan-day), **not** the current count. **Coverage 2025-06-04 .. 2026-06-07, 302 daily snapshots, 9,587 rows**.
- **SQL**:

```sql
SELECT stage, COUNT(*) AS n FROM port.fcl_stage_info GROUP BY stage ORDER BY n DESC;
SELECT "group" AS grp, COUNT(*) AS n FROM port.fcl_stage_info GROUP BY "group" ORDER BY n DESC;
```

| Stage Code | Records (cumulative) | Business Meaning |
|------------|---------|-----------------|
| `REFERRAL` | 3,766 | Attorney referral |
| `SALE` | 2,124 | Foreclosure sale |
| `SERVICE` | 1,551 | Legal document service |
| `FIRST_LEGAL` | 941 | First legal action filed |
| `JUDGEMENT` | 744 | Judgment phase |
| `DEMAND` | 461 | Demand letter / Notice of Intent issued |

Stage groups (cumulative): `FCL` 9,114 · `D120P` 424 · `D90` 39 · `REO` 10.

> ⚠️ Correction: the prior "8,733 total records" and per-stage figures (DEMAND 448 / REFERRAL 3,341 / …) were a **cumulative** snapshot at an earlier data date, unlabeled as to method/date — easily misread as "current in-FCL loan count". Now split into the two methods above with as-of dates and SQL (prod-verified 2026-06-07).

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
