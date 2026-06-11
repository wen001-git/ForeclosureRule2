# Doc 28 · Hold (wide→long unpivot) — `bpms.sync_loan_foreclosure_hold` field lineage

> <!-- RULEGLOSS_PTR -->📖 **Rule terms**: plain-language + formula for the technical phrases in the `rule` column — see [doc 25 · transform-rule glossary (appendix)](25_fcl_lineage_overview.md).

> **Auto-generated** — to change, edit `outputs/fcl_lineage_source.json` and re-run `python - < scripts/gen_fcl_lineage.py`; do not hand-edit this file.


## Document Purpose

Per-field lineage for BPS table `bpms.sync_loan_foreclosure_hold`: from the Servicer raw column, through every intermediate table, to the final BPS column, with each hop's transform rule and code reference.

## Target Audience

data engineers · analysts · validators · future AI sessions

## Revision History

| Date | Author | Version | Changes | Related |
|---|---|---|---|---|
| 2026-06-09 | AI Agent | v1 | Initial: doc 25–30 generated from fcl_lineage_source.json (per-field lineage + hop chain + fetch SQL) | doc 02 · doc 13 · doc 14 |
| 2026-06-09 | AI Agent | v2 | Per-servicer source columns (Newrez/Carrington/Capecodfive separated) | doc 02 · doc 13 · doc 14 |
| 2026-06-09 | AI Agent | v3 | Non-trivial SQL annotated with explanation + worked example | doc 02 · doc 13 · doc 14 |
| 2026-06-09 | AI Agent | v4 | Switched to per-field vertical cards; rules written in full | doc 02 · doc 13 · doc 14 |
| 2026-06-09 | AI Agent | v5 | Added tempfc hop + L2/L3-absent note to the chain; numbered field cards | doc 02 · doc 13 · doc 14 |
| 2026-06-09 | AI Agent | v6 | Cover every BPS sync-table column (system/audit grouped, view-computed); numbered data-flow order | doc 02 · doc 13 · doc 14 |
| 2026-06-09 | AI Agent | v7 | Added Chinese name/business meaning to every field (Code-First from DDL comments); started maintaining the revision history | doc 02 · doc 13 · doc 14 |
| 2026-06-09 | AI Agent | v8 | Added full logic notes + worked examples (multi-branch) to stage computed fields; Code-First-corrected the end_date/countdown hop rules from the SQL projection; fixed the wrong to_judgement/to_sale examples | doc 02 · doc 13 · doc 14 |
| 2026-06-09 | AI Agent | v9 | Made [pool:]/[asset:] code citations clickable GitLab links (fork jli/prefectflow pinned to commit 32a750a3; exact stable line numbers); legend file paths clickable too; view stays plain text | doc 02 · doc 13 · doc 14 |
| 2026-06-10 | AI Agent | v10 | Hub: added FCL-fact-hub vs BPS-projection note: basic_data_loan_fcl = fact hub/full history, **directly feeds foreclosure + fcl_stage_info**; _hold/_bankruptcy/_loss_mitigation/fcl_related are built in parallel from raw servicer tables (not children of fcl) | doc 02 · doc 13 · doc 14 |

## Related Documents

doc 02 (ETL pipeline, table-level) · doc 13/14 (field mappings) · doc 25 (lineage hub) · PrefectFlow source (per-hop code refs)


---

**Canonical hop chain**


`newrez.portnewrezfc (fchold1..4 slots)` → `port.basic_data_loan_foreclosure_hold` → `bpms.sync_loan_foreclosure_hold`

| # | layer | db | table | role |
|---|---|---|---|---|
| 1 | L0/L1 | MySQL+Redshift | `newrez.portnewrezfc (fchold1..4 slots)` | Servicer raw |
| 2 | L4 | Redshift | `port.basic_data_loan_foreclosure_hold` | wide description1..3 (+ Carrington slot4); deduped roll-up of *_hold_detail |
| 3 | L5 | MySQL bpms | `bpms.sync_loan_foreclosure_hold` | long rows via UNION ALL unpivot (GEN_FORECLOSURE_HOLD) |

> The `#` column is a sequence number, not the layer number. The FCL fact `port.basic_data_loan_fcl` is built DIRECTLY from the L1 servicer raw tables (UNIONed in `tempfc.temp_basic_data_fcl`; CREATE_BASIC_FCL [pool:1531-1654](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L1531-1654)), so the L2 unified-daily (`port.basic_data_daily_loan_common`) and L3 clean (`basic_data_daily_loan_common_clean` / `basic_data_loan_delinq_clean`) layers are NOT part of this branch by design — they carry the common + delinquency fields and re-enter only via the `group` dimension (doc 27, `basic_data_fcl_related`) and the monthly `portmonth` path. See doc 02 for the full L0–L5 pipeline.

> code: `pool` = [PrefectFlow/flow/basic_data/basic_data_config/basic_data_pool_config.py](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py) · `asset` = [PrefectFlow/flow/bps/bps_config/asset_managment_config.py](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py) · `view` = bpms.biz_data_view_loan_details_foreclosure (SHOW CREATE VIEW)


## Identity / key columns

### 1. id (PK)  (`bpms.sync_loan_foreclosure_hold.id`)

_Auto surrogate primary key._

**Source (L1)**
- Newrez: `bpms.sync_loan_foreclosure_hold.id`  (Newrez-only detail)

**Flow:** ①sync_loan_foreclosure_hold
**Lineage (per hop: # column — rule [code])**
- 1. `bpms.sync_loan_foreclosure_hold.id` — auto-increment PK (BPS app) [asset]

**Note:** Generated by the BPS app on insert; not from source.

### 2. Investor loan id  (`bpms.sync_loan_foreclosure_hold.loanid`)

_Investor loan id / servicer loan id._

**Source (L1)**
- Newrez: `newrez.portnewrezfc.loanid`  (Newrez-only detail)

**Flow:** ①portnewrezfc → ②basic_data_loan_foreclosure_hold → ③sync_loan_foreclosure_hold
**Lineage (per hop: # column — rule [code])**
- 1. `newrez.portnewrezfc.loanid` — servicer raw
- 2. `port.basic_data_loan_foreclosure_hold.loanid` — passthrough
- 3. `bpms.sync_loan_foreclosure_hold.loanid` — sync passthrough [asset]

### 3. Servicer loan id  (`bpms.sync_loan_foreclosure_hold.svcloanid`)

_Investor loan id / servicer loan id._

**Source (L1)**
- Newrez: `newrez.portnewrezfc.shellpointloanid`  (Newrez-only detail)

**Flow:** ①portnewrezfc → ②basic_data_loan_foreclosure_hold → ③sync_loan_foreclosure_hold
**Lineage (per hop: # column — rule [code])**
- 1. `newrez.portnewrezfc.shellpointloanid` — servicer raw
- 2. `port.basic_data_loan_foreclosure_hold.svcloanid` — passthrough
- 3. `bpms.sync_loan_foreclosure_hold.svcloanid` — sync passthrough [asset]

### 4. fctrdt  (`bpms.sync_loan_foreclosure_hold.fctrdt`)

_Daily snapshot/report date (=dataasof)._

**Source (L1)**
- Newrez: `port.basic_data_loan_fcl.dataasof`  (Newrez-only detail)

**Flow:** ①basic_data_loan_fcl → ②sync_loan_foreclosure_hold
**Lineage (per hop: # column — rule [code])**
- 1. `port.basic_data_loan_fcl.dataasof` — dataasof → fctrdt
- 2. `bpms.sync_loan_foreclosure_hold.fctrdt` — sync passthrough [asset]


## Hold spans

### 5. Hold description  (`bpms.sync_loan_foreclosure_hold.description`)

_Hold span description (Newrez wide slots → long rows)._

**Source (L1)**
- Newrez: `newrez.portnewrezfc.fchold1..3`
- Carrington: `carrington.portcarrington fchold4 slot`
- Capecodfive: —

**Flow:** ①basic_data_loan_foreclosure_hold → ②sync_loan_foreclosure_hold
**Lineage (per hop: # column — rule [code])**
- 1. `port.basic_data_loan_foreclosure_hold.description1..3` — slot assembly + dedup roll-up [pool:744-768](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L744-768)
- 2. `bpms.sync_loan_foreclosure_hold.description` — UNION ALL wide→long unpivot [asset:847-892](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L847-892)

```sql
WITH hold_unpivot AS (
  SELECT loanid, description1 AS description, description1_start_date AS s, description1_end_date AS e FROM ...hold WHERE description1<>''
  UNION ALL SELECT loanid, description2, description2_start_date, description2_end_date ...
  UNION ALL SELECT loanid, description3, description3_start_date, description3_end_date ...)
SELECT loanid, description, s AS description_start_date, MAX(e) AS description_end_date GROUP BY loanid, description, s
```
🔎 **How it works:** Newrez stores up to 3 hold slots wide; the sync UNION ALLs the non-empty slots into long rows, grouping by loanid+description+start_date and taking MAX(end_date).
▶ **Example:** 7727004408: fchold1=('Court Delay',2026-03-24,2026-04-10) & fchold2=('Mediation Hearing',2026-04-28,2026-05-14) ⇒ 2 separate rows.

### 6. Hold start date  (`bpms.sync_loan_foreclosure_hold.description_start_date`)

_Hold span description_start_date (Newrez wide slots → long rows)._

**Source (L1)**
- Newrez: `newrez.portnewrezfc.fchold1..3`
- Carrington: `carrington.portcarrington fchold4 slot`
- Capecodfive: —

**Flow:** ①basic_data_loan_foreclosure_hold → ②sync_loan_foreclosure_hold
**Lineage (per hop: # column — rule [code])**
- 1. `port.basic_data_loan_foreclosure_hold.description1..3_start_date` — slot assembly + dedup roll-up [pool:744-768](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L744-768)
- 2. `bpms.sync_loan_foreclosure_hold.description_start_date` — UNION ALL wide→long unpivot [asset:847-892](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L847-892)

### 7. Hold end date  (`bpms.sync_loan_foreclosure_hold.description_end_date`)

_Hold span description_end_date (Newrez wide slots → long rows)._

**Source (L1)**
- Newrez: `newrez.portnewrezfc.fchold1..3`
- Carrington: `carrington.portcarrington fchold4 slot`
- Capecodfive: —

**Flow:** ①basic_data_loan_foreclosure_hold → ②sync_loan_foreclosure_hold
**Lineage (per hop: # column — rule [code])**
- 1. `port.basic_data_loan_foreclosure_hold.description1..3_end_date` — slot assembly + dedup roll-up [pool:744-768](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L744-768)
- 2. `bpms.sync_loan_foreclosure_hold.description_end_date` — UNION ALL wide→long unpivot [asset:847-892](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L847-892)


## System / audit columns

### 8. System / audit columns

_App/ETL-managed columns (not servicer-sourced)._

**Columns:** `create_user, create_dept, create_time, update_user, update_time, status, is_deleted, tenant_id`

**Note:** Columns: create_user, create_dept, create_time, update_user, update_time, status, is_deleted, tenant_id. tenant_id ← GET_LOAN_TENANT_ID(portfunding ⋈ basic_data_trust_funding, [asset:932-936](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L932-936)); create_*/update_* set by the BPS app; is_deleted constant 0 (view); status app flag. Not servicer data.


> This doc covers 8 fields.
