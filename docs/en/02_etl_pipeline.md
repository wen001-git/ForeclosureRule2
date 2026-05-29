# 02 — ETL Pipeline Analysis: Data Flow and Table Lineage

---

## Document Information

| Field | Content |
|-------|---------|
| **Purpose** | Complete description of the five-layer ETL pipeline for FCL-related data, from raw ingestion through downstream reporting, including key tables per layer, transformation trigger points, and MySQL vs. Redshift layering strategy. |
| **Problem solved** | The pipeline spans MySQL staging, Redshift analytics, and BPS sync across three platforms — logic is scattered across many config files. This document provides a unified panoramic view. |
| **Scope** | Layer 0 (raw data) → Layer 4 (BPS sync output); complete lineage of all FCL-related tables |
| **System** | `PrefectFlow/flow/servicer_data/`, `flow/basic_data/`, `flow/servicer_business/`, `flow/bps/` |

**Target audience:** Data engineers · System rewrite architects · Debug/operations engineers · Architects

**Dependencies:** `01_source_data.md` (understand data origins at each layer)

**Related documents:** `03_fcl_status_logic.md` (Layer 3 logic details), `06_diagrams.md` (diagram version)

**Revision history:**

| Date | Author | Version | Changes |
|------|--------|---------|---------|
| 2026-05-21 | AI Agent (Claude Sonnet 4.6) | v1 | Initial version, code analysis + DB evidence |
| 2026-05-28 | AI Agent (Claude Sonnet 4.6) | v2 | MCP-verified corrections: (1) Layer 5 platform corrected from Redshift to MySQL (`port` + `bpms_dev` schemas); (2) Added missing `bpms_dev.sync_loan_foreclosure` (primary FCL BPS table); (3) `5-FORECLOSURE` target corrected to `port.basic_data_loan_foreclosure` (MySQL); (4) Added `basic_data_pool_config.py` to Layer 3→4; (5) Added `bpms_dev.biz_data_view_loan_details_foreclosure` |

---

## 1. Overall Architecture: Five-Layer Pipeline

```
┌──────────────────────────────────────────────────────────────┐
│  Layer 0 — Raw Data Sources                                  │
│  S3 / SMB / SFTP → servicer files                           │
└─────────────────┬────────────────────────────────────────────┘
                  │  Prefect ingestion flows (daily schedule)
                  ▼
┌──────────────────────────────────────────────────────────────┐
│  Layer 1 — Servicer Staging (MySQL)                         │
│  newrez.portshellpointfc/bk/lm/general                      │
│  sls.portfcldaily/portbkdaily/portlmdaily/portassetdaily     │
│  carrington.portcarrington                                   │
│  mrc.portmrcforeclosure  |  fci.*  |  selene.*              │
└─────────────────┬────────────────────────────────────────────┘
                  │  portdaily_config.py (UNION ALL + normalize)
                  ▼
┌──────────────────────────────────────────────────────────────┐
│  Layer 2 — Unified Daily Layer (Redshift)                   │
│  port.portdaily_v2                                          │
│  port.basic_data_daily_loan_common                          │
└─────────────────┬────────────────────────────────────────────┘
                  │  daily_data_loan_common_clean_config.py
                  ▼
┌──────────────────────────────────────────────────────────────┐
│  Layer 3 — Clean Daily Layer (Redshift)                     │
│  port.basic_data_daily_loan_common_clean                    │
│  port.port_daily_clean                                      │
│  port.basic_data_loan_delinq_clean  ← refined delinq table │
└─────────────────┬────────────────────────────────────────────┘
                  │  gen_portmonth_config.py (monthly + biz rules)
                  │  basic_data_pool_config.py (FCL business tables)
                  ▼
┌──────────────────────────────────────────────────────────────┐
│  Layer 4 — Monthly Business Layer (Redshift)                │
│  port.portmonthbase             ← primary analytical table  │
│  port.basic_data_loan_foreclosure  ← FCL timeline          │
│  port.basic_data_loan_foreclosure_hold                      │
│  port.basic_data_loan_foreclosure_bankruptcy                │
│  port.basic_data_loan_foreclosure_loss_mitigation           │
│  port.basic_data_loan_fcl       ← FCL detail (w/ holds)   │
│  port.basic_data_fcl_related    ← FCL related attributes   │
│  port.fcl_stage_info            ← FCL stage tracking       │
│  port.basic_data_loan_reo       ← REO records              │
│  port.basic_data_monthly_loan_clean_data ← monthly clean   │
└─────────────────┬────────────────────────────────────────────┘
                  │  sync_to_bps_config.py (BPS sync)
                  ▼
┌──────────────────────────────────────────────────────────────┐
│  Layer 5 — BPS Sync Layer (MySQL, two schemas)              │
│                                                             │
│  [MySQL port schema — direct ETL sync targets]             │
│  port.basic_data_loan_foreclosure  ← FCL timeline (#5)    │
│  port.portmonth                    ← monthly base (#1)     │
│                                                             │
│  [MySQL bpms_dev schema — BPS application layer]           │
│  bpms_dev.sync_portmonth                                    │
│  bpms_dev.sync_loan_foreclosure    ← FCL primary BPS table │
│  bpms_dev.sync_loan_foreclosure_loss_mitigation             │
│  bpms_dev.sync_loan_foreclosure_bankruptcy                  │
│  bpms_dev.sync_loan_foreclosure_hold                        │
│  bpms_dev.sync_fcl_stage_info                               │
│  bpms_dev.biz_data_view_loan_details_foreclosure ← BPS view│
│                                                             │
│  [Redshift port — audit log only]                          │
│  port.sync_to_bps_status  ← sync run status per servicer  │
└──────────────────────────────────────────────────────────────┘
```

---

## 2. Layer 0 → Layer 1: Raw Data Ingestion

**Trigger:** Prefect scheduled flow, runs daily  
**Code:** `flow/basic_data/load_monthly_raw_data.py`, per-servicer ingestion flows  
**Format:** CSV / TXT / XLSX → MySQL tables (stored by `dataasof` date)

| Servicer | S3 Path | MySQL Schema | Key FCL Tables |
|----------|---------|-------------|----------------|
| Newrez/Shellpoint | `s3://brigaws/shellpoint_new/` | `newrez` | `portshellpointfc`, `portshellpointbk`, `portshellpointlm` |
| SLS | `s3://brigaws/sls_new/` | `sls` | `portfcldaily`, `portbkdaily`, `portlmdaily`, `portassetdaily` |
| Carrington | `s3://brigaws/carrington_new/` | `carrington` | `portcarrington` |
| MRC | `s3://brigaws/mrc_new/` | `mrc` | `portmrcforeclosure` |
| FCI | `s3://brigaws/fci_new/` | `fci` | per-category file tables |
| Selene | `s3://brigaws/selene_new/` | `selene` | per-category file tables |

---

## 3. Layer 1 → Layer 2: Unified Daily Layer

**Code:** `flow/servicer_data/sericer_data_config/portdaily_config.py` (60KB)

### 3.1 `port.portdaily_v2` Generation (SLS/Newrez Switch Handling)

```python
SLS_TO_NEWREZ_DATE = '2024-07-05'

GEN_PORTDAILY_v2 = '''
-- SLS historical data (before 2024-07-05)
SELECT s.dataasofdate AS asofdate,
       s.account_number_investor AS loanid,
       'SLS' AS servicer,
       a.delq_status_mba AS delq_status,    ← SLS already near-standard
       null AS fcl_flag,                    ← fcl_flag not mapped here for SLS
       null AS lm_flag,
       ...
FROM sls.portstandarddaily s, sls.portassetdaily a
WHERE s.dataasofdate < '2024-07-05'
UNION ALL
-- Newrez data (2024-07-05 onwards)
SELECT p.dataasof AS asofdate,
       p.loanid,
       'Newrez' AS servicer,
       g.delinquency_status_mba AS delq_status,  ← Newrez raw MBA status
       null AS fcl_flag,
       CASE WHEN lm.activelmflag = '1' THEN 'Y' ELSE 'N' END AS lm_flag,
       ...
FROM newrez.portnewrezpmt p JOIN newrez.portnewrezgeneral g ...
'''
```

**Key note:** `fcl_flag` is `null` for both SLS and Newrez in `port.portdaily_v2`. It is populated in the lower layers.  
Carrington's `fcl_flag` is mapped directly from `foreclosure_status_code`.

### 3.2 `port.basic_data_daily_loan_common` Generation

**Code:** `flow/basic_data/transfer_daily_data_config/daily_data_loan_common_config.py` (47KB)

All servicers (including Carrington, MRC, FCI, Selene) are UNIONed into a unified schema at this layer:

```sql
CREATE TABLE port.basic_data_daily_loan_common (
  ...
  delq_status VARCHAR(255),   ← servicer raw delinquency description
  fcl_flag    VARCHAR(50),    ← servicer FCL flag
  lm_flag     VARCHAR(1),     ← Y/N
  bankruptcy  VARCHAR(10),    ← Y/N
  ...
)
```

**`fcl_flag` mapping per servicer:**
| Servicer | Source Field | fcl_flag Value |
|----------|-------------|----------------|
| Newrez | `activefcflag` | `1`/`0` |
| SLS | `fcl_active_flag` | `'1'`/`'0'` |
| Carrington | `foreclosure_status_code` | raw value |
| MRC | `fc_flag` | raw value |

---

## 4. Layer 2 → Layer 3: Clean Daily Layer

**Code:** `flow/basic_data/transfer_daily_data_config/daily_data_loan_common_clean_config.py` (72KB)

**Core transformation:** Maps raw `delq_status` to standardized `delinq` codes

Key outputs:
- `port.basic_data_daily_loan_common_clean` — standardized daily full data
- `port.port_daily_clean` — includes `delinq`, `fcl_flag`, `lm_flag`, `bankruptcy` standard fields
- `port.basic_data_loan_delinq_clean` — refined delinquency table (with `delinq_source`, `ghost_reason`, `is_ghost_payoff`)

**`port.basic_data_loan_delinq_clean` key fields (DB-verified):**

| Field | Meaning |
|-------|---------|
| `delinq` | Normalized delinquency status (C/D30/.../FCL/REO/P/VASP/REPUR/D) |
| `ots_delinq` | OTS (Office of Thrift Supervision) delinquency classification |
| `prevdelinq` | Previous month delinquency (LAG calculation) |
| `ots_prevdelinq` | OTS previous month delinquency |
| `delinq_source` | Data source identifier for delinquency status |
| `is_ghost_payoff` | Boolean: whether this is a phantom payoff |
| `ghost_reason` | Reason for phantom payoff classification |
| `paymthist` | Payment history string |

---

## 5. Layer 3 → Layer 4: Monthly Business Layer (Core)

**Code files:**
- `flow/servicer_business/sericer_business_data_config/gen_portmonth_config.py` (90KB) — `portmonthbase` primary analytical table
- `flow/servicer_business/sericer_business_data_config/gen_portmonth_config_v4.py` (77KB) — monthly update variant
- `flow/basic_data/basic_data_config/basic_data_pool_config.py` (2,400+ lines) — **all FCL business tables** (`basic_data_loan_foreclosure`, `basic_data_loan_fcl`, `fcl_stage_info`, and 4 others) plus the `GEN_FCL_STAGE` stage calculation block

### 5.1 `port.portmonthbase` Generation

`port.portmonthbase` is the **primary analytical table** — monthly snapshots with complete loan state per month.

**Source JOIN:**
```sql
CREATE TABLE port.portmonthbase AS
SELECT a.*,
       b.principalreceived, b.interestreceived, ...  -- from basic_data_monthly_loan_remit_clean
FROM port.basic_data_daily_loan_common_clean a
LEFT JOIN port.basic_data_monthly_loan_remit_clean b ON a.fctrdt=b.fctrdt AND a.loanid=b.loanid
```

**`delinq` distribution in portmonthbase (DB-verified, 78,913 total rows):**

| delinq | Count | % |
|--------|-------|---|
| `C` | 72,796 | 92.2% |
| `P` | 2,288 | 2.9% |
| `D30` | 2,274 | 2.9% |
| `D60` | 480 | 0.6% |
| `D120P` | 403 | 0.5% |
| `FCL` | 279 | 0.4% |
| `D90` | 206 | 0.3% |
| `NULL` | 155 | 0.2% |
| `VASP` | 19 | 0.02% |
| `REO` | 12 | 0.02% |
| `REPUR` | 1 | 0.001% |

### 5.2 FCL-Related Layer 4 Tables

| Table | Approx. Rows | Core Content |
|-------|-------------|-------------|
| `port.basic_data_loan_foreclosure` | ~6K | Full FCL timeline (23 milestone dates + target days + variance + 7 closure reasons) |
| `port.basic_data_loan_fcl` | — | FCL detail + 4 hold descriptions (with projected end dates, comments) |
| `port.basic_data_loan_foreclosure_hold` | — | Structured holds (4 levels, description + start/end dates) |
| `port.basic_data_loan_foreclosure_bankruptcy` | — | FCL+BK combined view (BK status, chapter, MFR, claim) |
| `port.basic_data_loan_foreclosure_loss_mitigation` | — | FCL+LM combined view (16 fields: program, cycle, final disposition) |
| `port.basic_data_fcl_related` | — | FCL related attributes (litigation flag, liquidation type, BK flag, default reason) |
| `port.fcl_stage_info` | ~8,733 | FCL stage tracking (6 stages × 5 dimensions: dates, stage days, LM days, hold days) |
| `port.basic_data_loan_reo` | — | Simple REO record (loanid + start_date + end_date) |

### 5.3 `port.fcl_stage_info` Stage System (DB-verified)

**6 confirmed stages (in process order):**

| Stage | Meaning | Records |
|-------|---------|---------|
| `DEMAND` | Demand letter / Notice of Intent | 448 |
| `REFERRAL` | Attorney referral | 3,341 |
| `FIRST_LEGAL` | First legal action filed | 800 |
| `SERVICE` | Legal document service | 1,486 |
| `JUDGEMENT` | Judgment phase | 700 |
| `SALE` | Foreclosure sale | 1,958 |

**Stage group values (`group` field):**
| Group | Meaning | Records |
|-------|---------|---------|
| `FCL` | Loans formally in foreclosure | 8,277 |
| `D120P` | Seriously delinquent (120+ days) with stage tracking | 411 |
| `D90` | 90-day delinquent with stage tracking | 39 |
| `REO` | Already in REO | 6 |

**Five dimensions tracked per stage:**
- `*_start_date` / `*_end_date` — stage start and end dates
- `*_stage_days` — actual days in this stage
- `*_in_lm_days` — days within this stage spent in LM (excluded from timeline)
- `*_on_hold_days` — days within this stage spent on hold (excluded from timeline)

### 5.4 `port.basic_data_loan_foreclosure` — 7 Closure Reasons (DB-verified)

| `summary_foreclosure_status` | Meaning | Count |
|------------------------------|---------|-------|
| `Active Foreclosure` | FCL in progress | 43 |
| `Closed Foreclosure:Reinstated` | Closed (loan reinstated) | 25 |
| `Closed Foreclosure:Loss Mitigation` | Closed (entered LM) | 15 |
| `Closed Foreclosure:Paid in Full` | Closed (paid off) | 10 |
| `Closed Foreclosure:Process Complete` | Closed (auction/REO completed) | 7 |
| `Closed Foreclosure:Deed in Lieu Cmplte` | Closed (deed in lieu completed) | 1 |
| NULL | Not populated | 5,942 |

---

## 6. Layer 4 → Layer 5: BPS Sync Layer

**Code:** `flow/bps/bps_config/sync_to_bps_config.py`

**Sync table mapping (MCP-verified, 2026-05-28):**
| Sync Key | Redshift Source (Layer 4) | MySQL Target (Layer 5) | MCP Row Count |
|----------|--------------------------|----------------------|--------------|
| `1-PORTMONTH` | `port.portmonthbase` | `bpms_dev.sync_portmonth` | — |
| `5-FORECLOSURE` | `port.basic_data_loan_foreclosure` | `port.basic_data_loan_foreclosure` (MySQL) | 96 rows (Newrez) |
| `8-FORECLOSURE_LM` | `port.basic_data_loan_foreclosure_loss_mitigation` | `bpms_dev.sync_loan_foreclosure_loss_mitigation` | — |
| `9-FORECLOSURE_BK` | `port.basic_data_loan_foreclosure_bankruptcy` | `bpms_dev.sync_loan_foreclosure_bankruptcy` | — |
| `10-FORECLOSURE_HOLD` | `port.basic_data_loan_foreclosure_hold` | `bpms_dev.sync_loan_foreclosure_hold` | — |
| `12-FCL_STAGE` | `port.fcl_stage_info` | `bpms_dev.sync_fcl_stage_info` | — |

**Note:** `bpms_dev.sync_loan_foreclosure` is the **final destination** of the `5-FORECLOSURE` sync, written via two steps: `sync_to_mysql()` clears and appends Redshift data into MySQL `port.basic_data_loan_foreclosure` (staging), then `update_to_mysql()` executes `UPDATE_FORECLOSURE` (`INSERT INTO bpms_dev.sync_loan_foreclosure ... SELECT FROM port.basic_data_loan_foreclosure ... ON DUPLICATE KEY UPDATE`). The `create_time`/`update_time` NULL values are because the ON DUPLICATE KEY UPDATE clause excludes those columns — not because ETL is bypassed. Field divergence from the staging table reflects dev-environment ETL staleness. See doc 12 Section 14.0.

**Execution status logging:** Every sync (success/failure) writes to Redshift `port.sync_to_bps_status` (servicer, row count, max asofdate)

---

## 7. MySQL vs. Redshift Layering

| Layer | Platform | Rationale |
|-------|----------|-----------|
| Layer 1 (Staging) | MySQL | High-frequency writes, diverse formats, easy incremental append |
| Layers 2–4 (Analytics) | Redshift | Large-scale SQL, UNION ALL, window functions — Redshift excels |
| Layer 5 (BPS Sync) | MySQL (two schemas) | `port` schema receives direct ETL sync targets; `bpms_dev` schema is what the BPS application reads |

**Important:** Layer 5 is entirely MySQL. There are no `sync_*` data tables in Redshift. The Redshift `port.sync_to_bps_status` is only a sync execution audit log, not a data table.

---

## 8. Key Date Fields Reference

| Field | Meaning | Example |
|-------|---------|---------|
| `asofdate` / `dataasofdate` | Original data date | 2025-01-15 |
| `fctrdt` | Report cutoff date (first of the following month) | 2025-02-01 (represents Jan data) |
| `uploaddate` | Date uploaded to system | 2025-01-16 |
| `create_time` / `update_time` | Record creation/update time (audit) | — |

---

## Chinese Version

`docs/zh/02_etl_pipeline.md`
