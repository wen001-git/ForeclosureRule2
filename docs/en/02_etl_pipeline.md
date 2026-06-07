# 02 — ETL Pipeline Analysis: Data Flow and Table Lineage

> **Naming note (2024-07-05):** the source-table prefix is now `portnewrez*` (formerly `portshellpoint*`, the Shellpoint era); the live `newrez` schema only has `portnewrez*` — authoritative now; rename history in doc 01.

---

## Document Information

| Field | Content |
|-------|---------|
| **Purpose** | Complete description of the five-layer ETL pipeline for FCL-related data, from raw ingestion through downstream reporting, including key tables per layer, transformation trigger points, and the **MySQL + Redshift dual-write strategy** (§7, corrected 2026-06-06 via code+MCP). |
| **Problem solved** | The pipeline **dual-writes L1–L4 to MySQL and Redshift**, then syncs to BPS (MySQL) — logic is scattered across many config files. This document provides a unified panoramic view. |
| **Scope** | Layer 0 (raw data) → Layer 4 (BPS sync output); complete lineage of all FCL-related tables |
| **System** | `PrefectFlow/flow/servicer_data/`, `flow/basic_data/`, `flow/servicer_business/`, `flow/bps/` |

**Target audience:** Data engineers · System rewrite architects · Debug/operations engineers · Architects

**Dependencies:** `01_source_data.md` (understand data origins at each layer)

**Related documents:** `03_fcl_status_logic.md` (Layer 3 logic details), `06_diagrams.md` (diagram version)

**Revision history:**

| Date | Author | Version | Changes |
|------|--------|---------|---------|
| 2026-06-07 | AI Agent (Claude Opus 4.8) | v5 | Added **§8.1 how the as-of date evolves + why BPS `sync_*` has no as-of, only `update_time`** (code + MCP-proven: DELETE+APPEND overwrite refresh `df_db_util.py:691,693`, two-step `UPDATE_FORECLOSURE`, `datediff` real-time correction absorbing the as-of `asset_managment_config.py:597-598`; real-data example loan 7727000088: 368+2=370); added **§9 per-table data-inspection SQL (latest data-date)** (as-of column verified across all tables via information_schema; same SQL injected into every node drawer of fcl_pipeline.html); §8.1 corrected the write mechanism (main `bpms.sync_loan_foreclosure` written via `UPDATE_FORECLOSURE`'s `ON DUPLICATE KEY UPDATE`, whose UPDATE list excludes create/update_time → NULL) | PrefectFlow source + mysql_prod/redshift_prod |
| 2026-06-06 | AI Agent (Claude Opus 4.8) | v4 | **Corrected to MySQL+Redshift dual-write architecture** (the old "one platform per layer" was wrong): §1 diagram + §2/§3/§4/§5 per-layer "storage DB + file:line"; **§7 rewritten as the dual-write evidence table** + §7.1 other corrections (two branches / days360 / fcl_flag not normalized / Carrington whole-column gaps / delinq_clean producing code not in repo); cross-links doc 20 §B.6 / doc 21 | PrefectFlow source + mysql_prod/redshift |
| 2026-06-05 | AI Agent (Claude Opus 4.8) | v3 | Renamed `portshellpoint*`→`portnewrez*` (DB-verified live newrez tables; renamed 2024-07-05) + naming note (DB-verified; doc 01) |
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
│  Layer 1 — Servicer Staging (MySQL + Redshift dual-write)   │
│  newrez.portnewrezfc/bk/lm/general                      │
│  sls.portfcldaily/portbkdaily/portlmdaily/portassetdaily     │
│  carrington.portcarrington                                   │
│  mrc.portmrcforeclosure  |  fci.*  |  selene.*              │
└─────────────────┬────────────────────────────────────────────┘
                  │  portdaily_config.py (UNION ALL + normalize)
                  ▼
┌──────────────────────────────────────────────────────────────┐
│  Layer 2 — Unified Daily Layer (Redshift + MySQL dual-write)│
│  port.portdaily_v2                                          │
│  port.basic_data_daily_loan_common                          │
└─────────────────┬────────────────────────────────────────────┘
                  │  daily_data_loan_common_clean_config.py
                  ▼
┌──────────────────────────────────────────────────────────────┐
│  Layer 3 — Clean Daily Layer (Redshift + MySQL dual-write)  │
│  port.basic_data_daily_loan_common_clean                    │
│  port.port_daily_clean                                      │
│  port.basic_data_loan_delinq_clean  ← refined delinq table │
└─────────────────┬────────────────────────────────────────────┘
                  │  gen_portmonth_config.py (monthly + biz rules)
                  │  basic_data_pool_config.py (FCL business tables)
                  ▼
┌──────────────────────────────────────────────────────────────┐
│  Layer 4 — Monthly Business (monthly dual-write; FCL fam RS→L5)│
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

> ⚠️ **Dual-write correction (2026-06-06, code+MCP-proven)**: the layers above are **NOT "one platform per layer"** — **L1–L4 write to BOTH MySQL and Redshift** (same table names, one copy in each): plain configs→Redshift, `mysql_`-prefixed configs→MySQL, built by their own flows. Only the **L4 FCL business family** (`basic_data_loan_foreclosure`/`fcl_stage_info`/`_hold`/`_loss_mitigation`/`_bankruptcy`) is **Redshift-built only, then synced to MySQL by L5**. Per-layer code evidence in **§7**; storage evidence table also in [doc 20 §B.6](20_end_to_end_walkthrough.md); field-level lineage in [doc 21](21_fcl_field_lineage.md).

---

## 2. Layer 0 → Layer 1: Raw Data Ingestion

**Trigger:** Prefect scheduled flow, runs daily  
**Code:** per-servicer ingestion flows `flow/basic_data/load_daily_data_flow/load_daily_<servicer>_flow.py`  
**Format:** CSV / TXT / XLSX → raw tables (stored by `dataasof` date)  
**Storage: MySQL + Redshift dual-write** (code-proven) — each servicer has two flows: `update_<svc>_daily_to_mysql(save_to_new=True)`→MySQL and `_to_redshift(save_to_new=False)`→Redshift (`load_daily_shellpoint_flow.py:9-47`); branch at `servicer_task.py:158-163`; writes in `daily_task.py:923-942`(MySQL)/`960-983`(RS). MCP-verified `newrez.portnewrezfc` exists in both.

| Servicer | S3 Path | MySQL Schema | Key FCL Tables |
|----------|---------|-------------|----------------|
| Newrez/Shellpoint | `s3://brigaws/shellpoint_new/` | `newrez` | `portnewrezfc`, `portnewrezbk`, `portnewrezlm` |
| SLS | `s3://brigaws/sls_new/` | `sls` | `portfcldaily`, `portbkdaily`, `portlmdaily`, `portassetdaily` |
| Carrington | `s3://brigaws/carrington_new/` | `carrington` | `portcarrington` |
| MRC | `s3://brigaws/mrc_new/` | `mrc` | `portmrcforeclosure` |
| FCI | `s3://brigaws/fci_new/` | `fci` | per-category file tables |
| Selene | `s3://brigaws/selene_new/` | `selene` | per-category file tables |

---

## 3. Layer 1 → Layer 2: Unified Daily Layer

**Code:** `flow/servicer_data/sericer_data_config/portdaily_config.py` (60KB)  
**Storage: Redshift + MySQL dual-write** — plain `daily_data_loan_common_config.py:5,97`→Redshift `port.basic_data_daily_loan_common`; `mysql_daily_data_loan_common_config.py:5,94`→MySQL same table; two flows `gen_daily_data_loan_common_flow.py:17-48(RS)/52-84(MySQL)`.

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
**Storage: Redshift + MySQL dual-write** — plain config→Redshift `port.basic_data_daily_loan_common_clean`; `mysql_daily_data_loan_common_clean_config.py`→MySQL same name; two flows `gen_daily_data_loan_common_clean_flow.py:78-139(RS)/186-243(MySQL)`.

**Core transformation:** Maps raw `delq_status` to standardized `delinq` codes  
> Verified rule (doc 21 §5.4): one CASE per servicer — `Foreclosure*→FCL` / `REO→REO` / `Payoff*→P`, **everything else bucketed by `days360(nextduedate, fctrdt)`** (<30→C…≥120→D120P). **`FCL` is a legal status, NOT derived from days** (`days360` never outputs `FCL`; it must be explicitly flagged by the servicer). DB-observed `delinq` values: `C/D30/D60/D90/D120P/FCL/REO/P/VASP` (no `REPUR`/standalone `D`).

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

**Storage (two cases, code-proven):**
- **Monthly common / `portmonthbase` = dual-write**: `monthly_data_loan_common_config.py`(RS) + `mysql_monthly_data_loan_common_config.py`(MySQL), flow `gen_monthly_data_loan_common_flow.py:24-30/78-84`; portmonthbase via `gen_portmonth_v4.py:45-46`(RS) + `gen_portmonth_mysql.py:42-43`(MySQL).
- **FCL business family = built in Redshift only** (`basic_data_pool_config.py`, target `{REDSHIFT_PORT}.`, no `mysql_` pool config); its **MySQL copy is produced by the Layer 5 sync**. MCP-verified `port.basic_data_loan_foreclosure` in both (RS-built / MySQL via L5).

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

## 7. MySQL ⇄ Redshift: dual-write architecture (2026-06-06 code+MCP-proven, corrects the old "one platform per layer")

> **Correction**: this section previously stated "Layer 1=MySQL, Layers 2–4=Redshift, Layer 5=MySQL" (one platform per layer). Reading PrefectFlow source + MCP testing confirmed: **L1–L4 dual-write to MySQL + Redshift** (same table names, one copy in each), built by **plain configs→Redshift and `mysql_`-prefixed configs→MySQL** (separate config/flows); only the **L4 FCL business family** is Redshift-built then synced to MySQL by L5.

**How to tell the engine**: `config/db_conn.py` — MySQL=`pymysql.connect` (:15-25), Redshift=`redshift_connector.connect` (:26-34); the single entry `execute_sql(sql, DbTypeEnum.{MYSQL|REDSHIFT}.value, db)` picks the DB (`flow/__init__.py:19 REDSHIFT_PORT="port"`).

| Layer | MySQL? | Redshift? | Code evidence (file:line) | MCP check |
|---|---|---|---|---|
| **L1 raw land** | ✅ | ✅ | two flows `load_daily_<svc>_flow.py:9-47`; branch `servicer_task.py:158-163`; writes `daily_task.py:923-942`(MySQL)/`960-983`(RS); `MYSQL_DB_MAP servicer_config.py:374-387` | `newrez.portnewrezfc` in both |
| **L2 unified daily** | ✅ | ✅ | plain→RS `daily_data_loan_common_config.py:5,97`; `mysql_…:5,94`; flow `gen_daily_data_loan_common_flow.py:17-48(RS)/52-84(MySQL)` | `port.basic_data_daily_loan_common` in both |
| **L3 clean daily** | ✅ | ✅ | `daily_data_loan_common_clean_config.py`(RS)/`mysql_…clean_config.py`(MySQL); flow `gen_daily_data_loan_common_clean_flow.py:78-139/186-243` | `port.basic_data_daily_loan_common_clean` in both |
| **L4 monthly common / portmonthbase** | ✅ | ✅ | `monthly_data_loan_common_config.py`(RS)/`mysql_monthly_…`(MySQL); `gen_portmonth_v4.py:45-46`(RS)+`gen_portmonth_mysql.py:42-43`(MySQL) | RS has `portmonthbase`; MySQL has `basic_data_monthly_loan_common` |
| **L4 FCL business family** (foreclosure/stage/hold/lm/bk) | ⛔ (via L5 sync) | ✅ (built) | `basic_data_pool_config.py` (target `{REDSHIFT_PORT}.`, no `mysql_` pool config) | `port.basic_data_loan_foreclosure` in both (MySQL via L5) |
| **L5 BPS sync** | ✅ (write) | ✅ (read) | reads RS `df_db_util.py:117-137`; writes MySQL `:665-699`/`:702-726`; `sync_asset_management.py` | `bpms.sync_*`, `port.basic_data_loan_foreclosure` (transit) |

**Why dual-write (inferred)**: Redshift runs heavy analytical SQL (UNION ALL, window functions, days360); MySQL serves **low-latency BPS/app reads**. Same table names, one copy in each.
> Same storage-evidence table in [doc 20 §B.6](20_end_to_end_walkthrough.md); field-level lineage + business rationale in [doc 21](21_fcl_field_lineage.md).

**Layer 5 note (retained)**: `sync_*` data tables exist only in MySQL (prod=`bpms`, dev=`bpms_dev`; plus the `port` transit table). The Redshift `port.sync_to_bps_status` is only a sync execution audit log, not a data table.

### 7.1 Other corrections from today (code + MCP, consistent with doc 20/21)

1. **Two branches**: foreclosure milestones/status take the **FCL business-family branch** (read `portnewrezfc`/`portcarrington` directly → `basic_data_loan_fcl` → `basic_data_loan_foreclosure`/`fcl_stage_info`); `delinq` takes the **delinquency branch** (`portnewrezgeneral.delinquency_status_mba` → `basic_data_daily_loan_common` → `_clean`). They meet at `fcl_stage_info` (`group=delq_status`).
2. **L2 `fcl_flag` not cross-servicer normalized**: it is **pass-through** in the unified daily table (NULL for Newrez/SLS); the FCL determination actually happens in the **L3 `delinq` CASE**; cross-servicer `activefcflag` unification lives on the FCL business-family branch (`basic_data_pool_config.py`), not the unified daily table.
3. **`FCL` is a legal status, not derived from days** (`days360` never outputs `FCL`; see §4 note and doc 21 §5.4/§6).
4. **Carrington whole-column gaps (prod-tested)**: `timeline_first_legal_date`, `timeline_judgement_date`, `summary_judicial_foreclosure` are **all NULL for Carrington** (`portcarrington` has no source columns); cross-servicer differences in doc 21 §6/§7.
5. **`basic_data_loan_delinq_clean` (with `is_ghost_payoff/ghost_reason/delinq_source`)**: prod-tested the columns exist and hold data, but its **producing code has 0 hits in a full PrefectFlow grep** (likely another repo/manual process) — state this honestly when asked; don't assume (doc 21 §9#7).

---

## 8. Key Date Fields Reference

| Field | Meaning | Example |
|-------|---------|---------|
| `asofdate` / `dataasofdate` | Original data date | 2025-01-15 |
| `fctrdt` | Report cutoff date (first of the following month) | 2025-02-01 (represents Jan data) |
| `uploaddate` | Date uploaded to system | 2025-01-16 |
| `create_time` / `update_time` | Record creation/update time (audit) | — |

### 8.1 How the as-of date evolves + why the BPS `sync_*` tables have no as-of, only `update_time` (code + MCP-proven)

**As-of (data date) across the layers:**

| Layer | as-of column | Meaning | Grain |
|---|---|---|---|
| L1 source `newrez.portnewrez*` | `dataasof` | daily snapshot date (raw tables partitioned by it) | loanid+dataasof (1 row/loan/day) |
| L2 `basic_data_daily_loan_common` | `asofdate` | unified daily date | loanid+asofdate |
| L3 `basic_data_daily_loan_common_clean` | `fctrdt` | report cutoff date | loanid+fctrdt |
| L4 `basic_data_loan_fcl` / `_foreclosure` | takes `MAX(dataasof)` | keeps only each loan's latest snapshot | 1 row/loan (latest) |
| L4 `fcl_stage_info` | `fctrdt` | monthly stage snapshot | loanid+fctrdt |
| **L5 main `bpms.sync_loan_foreclosure`** | **none** | current-state, audit cols only | 1 row/loan |
| L5 `bpms.sync_fcl_stage_info` | **`fctrdt` (kept)** | retains as-of history | loanid+fctrdt (many rows/loan) |

**MCP-verified columns (mysql_prod):**
- `bpms.sync_loan_foreclosure`: business `timeline_*_date` cols + audit `create_time`/`update_time`/`update_user`; **no `asofdate`/`fctrdt`/`dataasof`**. `create_time`/`update_time` default NULL, written by the ETL (not MySQL-managed, **may be NULL**).
- `bpms.sync_fcl_stage_info`: **has `fctrdt`** + stage dates + `create_time`(CURRENT_TIMESTAMP)/`update_time`(on update, MySQL-managed).

**Write mechanism (PrefectFlow code) — two kinds:**
- ① **Most `sync_*` tables**: written by `sync_to_mysql` as a **whole-table `DELETE` + `to_sql(append)` (overwrite refresh)** into bpms (`df_db_util.py:691,693`).
- ② **The main table `bpms.sync_loan_foreclosure` is special (two-step)**: `sync_to_mysql` first clears + appends the **port staging** table `port.basic_data_loan_foreclosure` (MySQL, `:675-676,691-693`), then `update_to_mysql` runs `UPDATE_FORECLOSURE`: `INSERT…SELECT…ON DUPLICATE KEY UPDATE` into bpms (`:698,716`; SQL in `asset_managment_config.py`). That upsert's UPDATE list **excludes `create_time`/`update_time`** → so they stay NULL (doc 12 §14.0).
- `flow/bps/bps_config/asset_managment_config.py:535-608` `GEN_FORECLOSURE`: output **omits `dataasof`**; the days fields = stored value `+ datediff(day, a.dataasof, tempfc.current_date_new_york)` (`:597-598`; `current_date_new_york` = run day / NY today, `:536-538`); filter `timeline_referred_to_foreclosure_date IS NOT NULL` (`:605`).

**Why the main table has no as-of, only `update_time`:**
1. **It's a current-state table**: only the latest snapshot per loan is taken, then the whole table is overwrite-refreshed — one row always means "latest", so an as-of column is redundant.
2. **As-of history lives upstream** (L1 `dataasof` daily snapshots can reproduce any day); BPS only needs the current state.
3. **`create_time`/`update_time` are audit columns** (when the row was synced), not a data date.
4. **The days fields are recomputed to the run day**: `datediff(dataasof → run day)` absorbs the as-of gap into `summary_days_in_fcl`, so the table means "as of run time" — a frozen as-of column would mislead.
5. **Exception**: the stage table `sync_fcl_stage_info` keeps many rows by `fctrdt` (the as-of carrier); only the main table collapses to 1 row.

**Real-data example (MCP-verified, loan `7727000088`, doc 19 Loan 1):**

| Location | Field | Verified value |
|---|---|---|
| Redshift `port.basic_data_loan_foreclosure` (source) | `dataasof` | **2026-06-04** |
| same | `summary_days_in_fcl` (stored, as of dataasof) | **368** |
| `bpms.sync_loan_foreclosure` (output main) | `summary_days_in_fcl` | **370** |
| same | `dataasof` / `asofdate` / `fctrdt` | **column absent** |
| same | `create_time` / `update_time` | **NULL** |
| `bpms.sync_fcl_stage_info` | `fctrdt` (multiple rows, history kept) | 2026-05-24, 2026-05-23 … |
| same | `update_time` (= BPS run day) | 2026-06-06 00:52:45 |

Check: `368 + datediff('2026-06-04' → run day '2026-06-06') = 368 + 2 = 370` = the main table's value. **Those 2 days are the as-of**, absorbed into the days field by `datediff` — which is why the output stores no separate as-of column. Re-derive (read-only):

```sql
-- source (Redshift redshift_prod)
SELECT dataasof, summary_days_in_fcl FROM port.basic_data_loan_foreclosure WHERE loanid='7727000088';
-- output main (MySQL mysql_prod.bpms)
SELECT summary_days_in_fcl, create_time, update_time FROM bpms.sync_loan_foreclosure WHERE loanid='7727000088';
-- stage table keeps fctrdt history
SELECT loanid, fctrdt, update_time FROM bpms.sync_fcl_stage_info WHERE loanid='7727000088' ORDER BY fctrdt DESC;
```

---

## 9. Per-table data-inspection SQL (latest data-date)

> Copy-paste to look at a table's data in the DB. The as-of column was verified for every table via `information_schema`. Connections: **L1=`mysql_prod`**, **L2–L4=`redshift_prod`**, **L5=`mysql_prod.bpms`**. Tables with no data-date column are anchored by `loanid`/`update_time` (noted). Adjust `LIMIT 50` as needed.

### L1 sources (mysql_prod)
| Table | Latest data-date SQL |
|---|---|
| `newrez.portnewrezfc` (`bk/lm/general/prop` same, all `dataasof`) | `SELECT * FROM newrez.portnewrezfc WHERE dataasof=(SELECT MAX(dataasof) FROM newrez.portnewrezfc) LIMIT 50;` |
| `sls.portassetdaily` (history; `portfcldaily/bk/lm` use `uploaddate`) | `SELECT * FROM sls.portassetdaily WHERE dataasofdate=(SELECT MAX(dataasofdate) FROM sls.portassetdaily) LIMIT 50;` |
| `carrington.portcarrington` (**no data-date column**) | `SELECT * FROM carrington.portcarrington ORDER BY update_time DESC LIMIT 50;` |
| `mrc.portmrcforeclosure` | `SELECT * FROM mrc.portmrcforeclosure WHERE dataasof=(SELECT MAX(dataasof) FROM mrc.portmrcforeclosure) LIMIT 50;` |
| `newrez.portnewrezdatadic` (dictionary, no date) | `SELECT * FROM newrez.portnewrezdatadic LIMIT 100;` |

### L2–L3 delinquency branch (redshift_prod)
| Table | Latest data-date SQL |
|---|---|
| `port.portdaily_v2` | `SELECT * FROM port.portdaily_v2 WHERE asofdate=(SELECT MAX(asofdate) FROM port.portdaily_v2) LIMIT 50;` |
| `port.basic_data_daily_loan_common` | `SELECT * FROM port.basic_data_daily_loan_common WHERE asofdate=(SELECT MAX(asofdate) FROM port.basic_data_daily_loan_common) LIMIT 50;` |
| `port.basic_data_daily_loan_common_clean` | `SELECT * FROM port.basic_data_daily_loan_common_clean WHERE fctrdt=(SELECT MAX(fctrdt) FROM port.basic_data_daily_loan_common_clean) LIMIT 50;` |
| `port.port_daily_clean` | `SELECT * FROM port.port_daily_clean WHERE fctrdt=(SELECT MAX(fctrdt) FROM port.port_daily_clean) LIMIT 50;` |
| `port.basic_data_loan_delinq_clean` | `SELECT * FROM port.basic_data_loan_delinq_clean WHERE fctrdt=(SELECT MAX(fctrdt) FROM port.basic_data_loan_delinq_clean) LIMIT 50;` |

### L4 monthly / FCL business family (redshift_prod)
| Table | Latest data-date SQL |
|---|---|
| `port.portmonthbase` | `SELECT * FROM port.portmonthbase WHERE fctrdt=(SELECT MAX(fctrdt) FROM port.portmonthbase) LIMIT 50;` |
| `tempfc.temp_basic_data_fcl` | `SELECT * FROM tempfc.temp_basic_data_fcl WHERE dataasof=(SELECT MAX(dataasof) FROM tempfc.temp_basic_data_fcl) LIMIT 50;` |
| `port.basic_data_loan_fcl` | `SELECT * FROM port.basic_data_loan_fcl WHERE dataasof=(SELECT MAX(dataasof) FROM port.basic_data_loan_fcl) LIMIT 50;` |
| `port.basic_data_loan_foreclosure` | `SELECT * FROM port.basic_data_loan_foreclosure WHERE dataasof=(SELECT MAX(dataasof) FROM port.basic_data_loan_foreclosure) LIMIT 50;` |
| `port.basic_data_fcl_related` | `SELECT * FROM port.basic_data_fcl_related WHERE dataasof=(SELECT MAX(dataasof) FROM port.basic_data_fcl_related) LIMIT 50;` |
| `port.fcl_stage_info` | `SELECT * FROM port.fcl_stage_info WHERE fctrdt=(SELECT MAX(fctrdt) FROM port.fcl_stage_info) LIMIT 50;` |
| `port.basic_data_loan_foreclosure_hold` (many rows/loan) | `SELECT * FROM port.basic_data_loan_foreclosure_hold WHERE dataasof=(SELECT MAX(dataasof) FROM port.basic_data_loan_foreclosure_hold) LIMIT 50;` |
| `port.basic_data_loan_foreclosure_loss_mitigation` | `SELECT * FROM port.basic_data_loan_foreclosure_loss_mitigation WHERE dataasof=(SELECT MAX(dataasof) FROM port.basic_data_loan_foreclosure_loss_mitigation) LIMIT 50;` |
| `port.basic_data_loan_foreclosure_bankruptcy` | `SELECT * FROM port.basic_data_loan_foreclosure_bankruptcy WHERE dataasof=(SELECT MAX(dataasof) FROM port.basic_data_loan_foreclosure_bankruptcy) LIMIT 50;` |
| `port.portfunding` (**no data-date column**, dimension) | `SELECT * FROM port.portfunding WHERE loanid='7727000088';` |
| `port.basic_data_loan_reo` (**no data-date column**) | `SELECT * FROM port.basic_data_loan_reo WHERE loanid='7727000088';` |

### L5 BPS sync (mysql_prod.bpms)
| Table | Latest data-date SQL |
|---|---|
| `bpms.sync_loan_foreclosure` (**no data-date column**, current-state 1 row/loan) | `SELECT * FROM bpms.sync_loan_foreclosure WHERE loanid='7727000088';` |
| `bpms.sync_fcl_stage_info` | `SELECT * FROM bpms.sync_fcl_stage_info WHERE fctrdt=(SELECT MAX(fctrdt) FROM bpms.sync_fcl_stage_info) LIMIT 50;` |
| `bpms.sync_loan_foreclosure_hold` | `SELECT * FROM bpms.sync_loan_foreclosure_hold WHERE fctrdt=(SELECT MAX(fctrdt) FROM bpms.sync_loan_foreclosure_hold) LIMIT 50;` |
| `bpms.sync_loan_foreclosure_loss_mitigation` | `SELECT * FROM bpms.sync_loan_foreclosure_loss_mitigation WHERE fctrdt=(SELECT MAX(fctrdt) FROM bpms.sync_loan_foreclosure_loss_mitigation) LIMIT 50;` |
| `bpms.sync_loan_foreclosure_bankruptcy` | `SELECT * FROM bpms.sync_loan_foreclosure_bankruptcy WHERE fctrdt=(SELECT MAX(fctrdt) FROM bpms.sync_loan_foreclosure_bankruptcy) LIMIT 50;` |
| `bpms.biz_data_view_loan_details_foreclosure` (view) | `SELECT * FROM bpms.biz_data_view_loan_details_foreclosure WHERE fctrdt=(SELECT MAX(fctrdt) FROM bpms.biz_data_view_loan_details_foreclosure) LIMIT 50;` |
| `port.basic_data_loan_foreclosure` (MySQL staging, **no data-date column**) | `SELECT * FROM port.basic_data_loan_foreclosure WHERE loanid='7727000088';` |

> The same SQL is injected into every node drawer of the Pipeline view in `outputs/fcl_pipeline.html` (click a node).

---

## Chinese Version

`docs/zh/02_etl_pipeline.md`
