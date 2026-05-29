# 03 — FCL Status Generation Logic: Complete White-Box Analysis

---

## Document Information

| Field | Content |
|-------|---------|
| **Purpose** | Layer-by-layer detailed analysis of how the system generates standardized foreclosure status from raw servicer data. This is the core document in the entire documentation suite, covering all SQL CASE-WHEN logic, Python transformations, override rules, and manual correction mechanisms. |
| **Problem solved** | FCL status generation logic is distributed across 5+ config files spanning 5 processing layers. This document consolidates them into a fully traceable rule tree. |
| **Scope** | Layer 1 (raw status) → Layer 5 (BPS sync); full status generation pipeline for foreclosure, delinquency, REO, bankruptcy, and loss mitigation |
| **System** | `portdaily_config.py`, `gen_portmonth_config.py`, `daily_data_loan_common_clean_config.py` |

**Target audience:** Data engineers · System rewrite architects · Business analysts · Validators/reconciliation engineers · Onboarding engineers

**Dependencies:** `01_source_data.md` (field origins), `02_etl_pipeline.md` (pipeline structure)

**Known limitations:**
- The specific override trigger conditions for VASP are not explicitly defined in code; inferred from DB evidence
- Classification criteria for `port.basic_data_loan_delinq_clean.delinq_source` not fully extracted from code

**Revision history:**

| Date | Author | Version | Changes |
|------|--------|---------|---------|
| 2026-05-21 | AI Agent (Claude Sonnet 4.6) | v1 | Initial version, code reverse-engineering + Redshift DB dual verification |

---

## 1. Logic Overview: Five-Layer Rule Stack

FCL status passes through 5 processing layers, each potentially overriding the previous:

```
┌─────────────────────────────────────────────────────────────┐
│  Layer 1 — Raw Servicer Status                              │
│  Each servicer's own fields (delinquency_status_mba/status) │
│  ❌ Heterogeneous — not comparable across servicers         │
└──────────────────────┬──────────────────────────────────────┘
                       │  CASE-WHEN mapping (portdaily_config.py)
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  Layer 2 — Normalized delinq Code                           │
│  C / D30 / D60 / D90 / D120P / FCL / REO / P               │
│  ✅ Cross-servicer comparable; based on days360 + priority  │
└──────────────────────┬──────────────────────────────────────┘
                       │  GEN_PREVDELINQ (gen_portmonth_config.py)
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  Layer 3 — prevdelinq + Payment History String              │
│  Confirmed delinquency (D), payment history (paymthistfull) │
│  ✅ Adds temporal context; identifies re-entry after FCL    │
└──────────────────────┬──────────────────────────────────────┘
                       │  port.basic_data_loan_fix manual override
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  Layer 4 — Manual Override Corrections                      │
│  port.basic_data_loan_fix (highest priority; 49 delinq overrides)│
│  ✅ Corrects data errors; outweighs all automated logic     │
└──────────────────────┬──────────────────────────────────────┘
                       │  FCL detail table generation
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  Layer 5 — FCL Detail Table System (7 tables)               │
│  port.basic_data_loan_foreclosure / fcl / hold / bk / lm / related│
│  ✅ Granular FCL stages, hold reasons, BK/LM merged views   │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Layer 1 → Layer 2: Core CASE-WHEN Normalization Logic

**Code files:** `portdaily_config.py` (Newrez and daily clean layer), `gen_portmonth_config.py` (Carrington, Interim monthly supplement)

### 2.1 Core Transformation Rules (All Servicers)

```sql
-- Standard delinq generation (priority: highest to lowest)
CASE
  -- Priority 1: Paid in full / completed payoff
  WHEN svcdelinq IN ('Full Payoff', 'Paid in Full', 'Completed Payoff',
                     'Completed Short Sale', 'Service Release')
    THEN 'P'

  -- Priority 2: REO (bank-acquired property)
  WHEN svcdelinq = 'REO'
    THEN 'REO'

  -- Priority 3: Foreclosure status
  WHEN svcdelinq = 'Foreclosure'
    THEN 'FCL'
  WHEN svcdelinq IN ('Foreclosure / Perf BK', 'Foreclosure / Non-Perf BK')
    THEN 'FCL'   -- bankruptcy field separately set to 'Y'

  -- Carrington special encoding (status field, not text)
  WHEN status = 'F'          THEN 'FCL'
  WHEN status IN ('R','REO') THEN 'REO'
  WHEN status = 'P'          THEN 'P'

  -- Zero-balance override (Arvest/Capecodfive)
  WHEN balance = 0           THEN 'P'

  -- Fallback: calculate DPD via days360
  ELSE
    CASE
      WHEN days360(nextduedate, fctrdt) < 30  THEN 'C'
      WHEN days360(nextduedate, fctrdt) < 60  THEN 'D30'
      WHEN days360(nextduedate, fctrdt) < 90  THEN 'D60'
      WHEN days360(nextduedate, fctrdt) < 120 THEN 'D90'
      ELSE 'D120P'
    END
END AS delinq
```

**Key rule analysis:**

| Rule | Priority | Notes |
|------|----------|-------|
| Paid-in-full keywords | Highest | Any servicer's "payoff" description maps to `P` |
| REO text | Second | Overrides all DPD calculations |
| FCL text | Second | Maps to `FCL` even if days360 < 30 |
| Carrington `status='F'` | Second | Carrington uses single-char codes instead of text |
| `balance=0` | Second | Catch-all for Arvest/Capecodfive historical data |
| `days360` calculation | Lowest | Only used when no higher-priority rule matches |

### 2.2 `days360` Function

```
days360(nextduedate, fctrdt)
= Days between nextduedate and fctrdt, calculated at 30 days/month
= Business standard for measuring "how many days past due" (differs from calendar days)
```

**DPD bucket boundaries:**
- `< 30` → Current (`C`)
- `30–59` → `D30` (inclusive of 30, exclusive of 60)
- `60–89` → `D60`
- `90–119` → `D90`
- `≥ 120` → `D120P`

### 2.3 Supplementary Flag Generation: fcl_flag / lm_flag / bankruptcy

These three fields are independent of `delinq` and do not participate in `delinq` calculation:

| Flag field | Generation rule |
|------------|----------------|
| `fcl_flag` | From servicer's active FCL indicator (see 2.4) |
| `lm_flag` | Newrez: `CASE WHEN activelmflag='1' THEN 'Y' ELSE 'N'` <br> Carrington: `CASE WHEN lm_flag='Active' THEN 'Y' ELSE 'N'` <br> SLS: inferred from `loss_mit_evaluation_status` |
| `bankruptcy` | Newrez: `CASE WHEN delinquency_status_mba LIKE '%Bankruptcy%' THEN 'Y' ELSE 'N'` <br> SLS: from `bk_active_flag` |

### 2.4 fcl_flag Source per Servicer

| Servicer | Source field | Values |
|----------|-------------|--------|
| Newrez | `activefcflag` | `1` (Active) / `0` (Inactive) |
| SLS | `fcl_active_flag` | `'1'` / `'0'` |
| Carrington | `foreclosure_status_code` | raw text code |
| MRC | `fc_flag` | raw value |
| Interim | no independent FCL flag | NULL |

---

## 3. Layer 2 → Layer 3: prevdelinq and Payment History Logic

**Code section:** `GEN_PREVDELINQ` constant in `gen_portmonth_config.py`

### 3.1 prevdelinq Calculation (LAG Window Function)

```sql
-- Step 1: Calculate prior month delinq
CREATE TABLE d.tmpportmonthprevdelinq AS
SELECT loanid, fctrdt,
       delinq,
       LAG(delinq) OVER (PARTITION BY loanid ORDER BY fctrdt) AS prevdelinq_svc,
       ...
FROM port.portmonthbase;

-- Step 2: Merge BID historical data (fills gaps in early data)
UPDATE portmonthbase SET prevdelinq =
  COALESCE(p1.prevdelinq_svc, b.delinqgroup_new)
FROM d.tmpportmonthprevdelinq p1
LEFT JOIN d.tmpbiddelinq b ON p1.loanid = b.loanid;
```

### 3.2 Payment History String Mapping

```sql
-- delinq → single character prevdelinqchar (for concatenating history string)
CASE
  WHEN delinq = 'FCL'   THEN 'F'
  WHEN delinq = 'REO'   THEN 'R'
  WHEN delinq = 'P'     THEN 'P'
  WHEN delinq = 'D'     THEN 'D'
  WHEN delinq = 'C'     THEN '0'
  WHEN delinq = 'D30'   THEN '1'
  WHEN delinq = 'D60'   THEN '2'
  WHEN delinq = 'D90'   THEN '3'
  WHEN delinq = 'D120P' THEN '4'
  ELSE delinq
END AS prevdelinqchar
```

Final `paymthistfull` (most-recent-first payment history string) is assembled via:
`LISTAGG(prevdelinqchar, '') WITHIN GROUP (ORDER BY fctrdt DESC)`

### 3.3 Confirmed Delinquency Rule (code = 'D')

```sql
-- Special rule: loans where prevdelinq was FCL/REO/D120P, and current month
-- is still delinquent (not C/P/REO/FCL), are marked as confirmed delinquent 'D'
UPDATE portmonthbase
SET delinq = 'D'
FROM (
  SELECT fctrdt, loanid
  FROM d.portmonthyilin1
  WHERE prevdelinq IN ('D120P', 'FCL', 'REO')
  AND delinq NOT IN ('C', 'P', 'REO', 'FCL')
) sub
WHERE portmonthbase.loanid = sub.loanid
  AND portmonthbase.fctrdt = sub.fctrdt;
```

**DB verification:** 273 records with `delinq='D'` in `port.basic_data_monthly_loan_clean_data` confirm this rule is active.

---

## 4. Layer 3 → Layer 4: Manual Override (Highest Priority)

**Table:** `port.basic_data_loan_fix`  
**DB verification:** 13 fields can be overridden; `delinq` has the most overrides (49 records)

```sql
-- Override logic
UPDATE port.portmonthbase a
SET delinq          = COALESCE(b.delinq, a.delinq),
    balance         = COALESCE(b.balance, a.balance),
    invbal          = COALESCE(b.invbal, a.invbal),
    escrowbal       = COALESCE(b.escrowbal, a.escrowbal),
    ...
FROM port.basic_data_loan_fix_clean b
WHERE a.loanid = b.loanid
  AND b.table_name = 'portmonthbase'
  AND a.fctrdt >= b.start_date
  AND a.fctrdt < b.end_date;
```

**`port.basic_data_loan_fix` overridable fields (DB-verified):**

| Field | Override record count |
|-------|-----------------------|
| `delinq` | 49 |
| `bpo` | 8 |
| `bpodate` | 8 |
| `balance` | 3 |
| `invbal` | 3 |
| `escrowbal` / `escrowadv` / `corpadvrec` / `corpadvnonrec` / `corpadvtotal` | 1 each |
| `deferredprin` / `deferredint` | 1 each |
| `agency` | 1 |

---

## 5. Layer 4: FCL Detail Table System (7 Tables)

These 7 tables do not modify `port.portmonthbase.delinq` — they provide supplementary FCL processing detail.

### 5.1 `port.basic_data_loan_fcl` — Core FCL Detail (61 columns)

Key field groups:

**Base flags:**
- `activefcflag`: Active foreclosure (0/1)
- `judicial`: Judicial foreclosure type
- `jr_sr_lien_flag`: Junior/senior lien flag

**Milestone dates (full pipeline):**
`fcsetupdate` → `referral_start_date` → `legal_start_date` → `service_start_date` → `fcjudgment_hearing_scheduled` → `fcjudgment_end_date` → `fcscheduled_sale_date` → `fcsale_held_date`

**Amount fields:**
- `fcbidamount`: FCL bid amount
- `fcapprbidprice`: Approved bid price
- `fcsaleamount`: Auction sale amount

**Outcome fields:**
- `fcresults`: Foreclosure result (e.g., 3rd Party Sale / Deed Acquired, etc.)
- `fcstage`: Current stage
- `fcremovaldesc` / `fcremovaldate`: Removal reason and date

**Hold information (4 levels, each with 5 fields):**
```
fchold1description / fchold1startdate / fchold1enddate / fchold1projectedenddate / fchold1comment
fchold2description / fchold2startdate / fchold2enddate / fchold2projectedenddate / fchold2comment
fchold3description / fchold3startdate / fchold3enddate / fchold3projectedenddate / fchold3comment
fchold4description / fchold4startdate / fchold4enddate / fchold4projectedenddate / fchold4comment
```

### 5.2 `port.basic_data_loan_foreclosure_hold` — Structured Hold (17 columns)

**DB-verified: 30 hold reason types:**

| Hold Type | Records | Business Meaning |
|-----------|---------|-----------------|
| `Loss Mitigation Workout` | 58 | LM workout in progress |
| `Service Delay` | 50 | Service of process delayed |
| `Client Document Execution` | 34 | Client document execution in progress |
| `Awaiting Funds to Post` | 26 | Waiting for funds to be posted |
| `Court Delay` | 23 | Court scheduling delay |
| `ACT(PA) Letter/Demand Letter/NOI Expiration` | 17 | Demand letter / notice of intent expiration |
| `Hearing Set` | 15 | Hearing has been scheduled |
| `Original Note` | 14 | Original note issue |
| `Delinquency Review` | 13 | Delinquency under review |
| `Bankruptcy Filed` | 11 | Bankruptcy petition filed |
| `Mediation Hearing` | 12 | Mediation hearing |
| `Note Possession Confirmation` | 12 | Note possession confirmation |
| `Title Resolution` | 9 | Title issue resolution |
| `FEMA Hold` | 1 | FEMA disaster suspension |
| `Moratorium` | 1 | Government/legal moratorium |

### 5.3 `port.basic_data_loan_foreclosure_bankruptcy` — FCL+BK (15 columns)

| Field | Meaning |
|-------|---------|
| `bankruptcy_status` | Bankruptcy status |
| `legal_status` | Legal status |
| `chapter` | Bankruptcy chapter (7/11/13) |
| `lien_status` | Lien status |
| `mfr_status` | Motion for Relief from Stay status |
| `mfr_filed_date` | MFR filing date |
| `claim_status` | Proof of claim status |
| `proof_of_claim_date` | Proof of claim date |
| `post_petition_due_date` | Post-petition due date |

### 5.4 `port.basic_data_loan_foreclosure_loss_mitigation` — FCL+LM (16 columns)

| Field | Meaning |
|-------|---------|
| `deal` | LM deal type |
| `program` | LM specific program |
| `lmc_status` | LM status code |
| `cycle_opened_date` | LM cycle opened date |
| `cycle_closed_date` | LM cycle closed date |
| `final_disposition` | Final disposition determination |
| `denialreason` | Denial reason |
| `borrower_intentions` | Borrower intentions |
| `imminent_default` | Imminent default flag |

### 5.5 `port.basic_data_fcl_related` — FCL Related Attributes (14 columns)

| Field | Meaning |
|-------|---------|
| `delq_status` | Delinquency status (for join) |
| `isloanlitigated` | Whether loan is in litigation |
| `deactreason` | Account deactivation reason |
| `reasonfordefault` | Reason for default |
| `inauctionflag` | Whether loan is in auction (int) |
| `liquidationdate` | Liquidation date |
| `liquidationtype` | Liquidation type |
| `liquidationproceeds` | Liquidation proceeds |
| `bk_flag` | Bankruptcy flag |
| `propertystate` | Property state |

### 5.6 `port.fcl_stage_info` — Stage Tracking (48 columns)

See `02_etl_pipeline.md` Section 5.3 for full detail.

Six stages: `DEMAND` → `REFERRAL` → `FIRST_LEGAL` → `SERVICE` → `JUDGEMENT` → `SALE`

Per stage tracking: start/end dates, actual stage days, LM days (excluded from timeline), hold days (excluded from timeline).

---

## 6. Special Status Code Generation Mechanisms

### 6.1 VASP (Vendee/Servicer Purchase)

**DB evidence:** 19 records, all from Newrez; `svcdelinq` is `Current` (10), `180+ DPD` (8), `Foreclosure` (1)

**Inferred mechanism:** VASP is a special disposition status for government-backed loans (VA Vendee), applied at the operational or manual level — not auto-generated by CASE-WHEN. Likely written via `port.basic_data_loan_fix` or a proprietary configuration step.

### 6.2 REPUR (Repurchase)

**DB evidence:** 1 record, from Carrington; `svcdelinq='Loss Mitigation'`

**Inferred mechanism:** Loan was repurchased; applied via servicer-specific logic or manual tagging.

### 6.3 D (Confirmed Delinquency)

**DB evidence:** 273 records in `port.basic_data_monthly_loan_clean_data`

**Generation condition:** `prevdelinq IN ('D120P','FCL','REO')` AND current month is still delinquent (not C/P/REO/FCL) → marked as `D`, meaning "confirmed long-term serious delinquency"

---

## 7. Complete Rule Priority Summary

```
Highest Priority ────────────────────────────────── Lowest Priority

[Manual Override]  [Special Keywords]  [FCL/REO/P]  [days360 Calc]
  delinq_fix        'Full Payoff'       'Foreclosure'  < 30  → C
   (49 records)     'Paid in Full'      'REO'          30-59 → D30
                    balance=0           status='F'     60-89 → D60
                    (Arvest)            status='R'     90-119→ D90
                                                       ≥120  → D120P

                         ↓ Additive (does not override delinq)
                    [Supplementary Flag Layer]
                    fcl_flag + lm_flag + bankruptcy

                         ↓ Temporal context
                    [prevdelinq Layer]
                    D (confirmed delinquency) / VASP / REPUR
```

---

## 8. Status Generation Execution Monitoring

**Table:** `port.sync_to_bps_status`

After each FCL-related table generation, the system automatically records:

| Field | Meaning |
|-------|---------|
| `generate_type` | Operation name (e.g., GEN_FCL_DETAIL, CREATE_BASIC_DATA_FCL_HOLD) |
| `status` | `success` / `failure` |
| `servicer` | Servicer name |
| `max_generate_asofdate` | Maximum data date processed |
| `numofrows` | Number of rows processed |
| `excute_date` | Execution date |

---

## Chinese Version

`docs/zh/03_fcl_status_logic.md`
