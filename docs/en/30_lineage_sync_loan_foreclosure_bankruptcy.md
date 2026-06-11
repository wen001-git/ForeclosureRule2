# Doc 30 · Bankruptcy (code→text decode) — `bpms.sync_loan_foreclosure_bankruptcy` field lineage

> <!-- RULEGLOSS_PTR -->📖 **Rule terms**: plain-language + formula for the technical phrases in the `rule` column — see [doc 25 · transform-rule glossary (appendix)](25_fcl_lineage_overview.md).

> **Auto-generated** — to change, edit `outputs/fcl_lineage_source.json` and re-run `python - < scripts/gen_fcl_lineage.py`; do not hand-edit this file.


## Document Purpose

Per-field lineage for BPS table `bpms.sync_loan_foreclosure_bankruptcy`: from the Servicer raw column, through every intermediate table, to the final BPS column, with each hop's transform rule and code reference.

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


`newrez.portnewrezbk (+ portnewrezgeneral.legalstatus)` → `port.basic_data_loan_foreclosure_bankruptcy` → `bpms.sync_loan_foreclosure_bankruptcy`

| # | layer | db | table | role |
|---|---|---|---|---|
| 1 | L0/L1 | MySQL+Redshift | `newrez.portnewrezbk (+ portnewrezgeneral.legalstatus)` | Servicer raw (coded) |
| 2 | L4 | Redshift | `port.basic_data_loan_foreclosure_bankruptcy` | datadic decode; dedup latest per loan+filing |
| 3 | L5 | MySQL bpms | `bpms.sync_loan_foreclosure_bankruptcy` | BPS app table (GEN_FORECLOSURE_BK pass-through) |

> The `#` column is a sequence number, not the layer number. The FCL fact `port.basic_data_loan_fcl` is built DIRECTLY from the L1 servicer raw tables (UNIONed in `tempfc.temp_basic_data_fcl`; CREATE_BASIC_FCL [pool:1531-1654](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L1531-1654)), so the L2 unified-daily (`port.basic_data_daily_loan_common`) and L3 clean (`basic_data_daily_loan_common_clean` / `basic_data_loan_delinq_clean`) layers are NOT part of this branch by design — they carry the common + delinquency fields and re-enter only via the `group` dimension (doc 27, `basic_data_fcl_related`) and the monthly `portmonth` path. See doc 02 for the full L0–L5 pipeline.

> code: `pool` = [PrefectFlow/flow/basic_data/basic_data_config/basic_data_pool_config.py](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py) · `asset` = [PrefectFlow/flow/bps/bps_config/asset_managment_config.py](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py) · `view` = bpms.biz_data_view_loan_details_foreclosure (SHOW CREATE VIEW)

> Datadic decode pattern (LM deal/program/status/decision/denial/borrower, BK status): COALESCE((SELECT description FROM newrez.portnewrezdatadic WHERE field_name='<X>' AND code=CONCAT(raw,'.0')), raw) — raw codes stored as '5.0'; falls back to the raw code if no dictionary row.


## Identity / key columns

> Newrez-only detail (Carrington/others are not built in this table).

### 1. id (PK)  (`bpms.sync_loan_foreclosure_bankruptcy.id`)

_Auto surrogate primary key._

**Source (L1)**
- Newrez: `bpms.sync_loan_foreclosure_bankruptcy.id`  (Newrez-only detail)

**Flow:** ①sync_loan_foreclosure_bankruptcy
**Lineage (per hop: # column — rule [code])**
- 1. `bpms.sync_loan_foreclosure_bankruptcy.id` — auto-increment PK (BPS app) [asset]

**Note:** Generated by the BPS app on insert; not from source.

### 2. Investor loan id  (`bpms.sync_loan_foreclosure_bankruptcy.loanid`)

_Investor loan id / servicer loan id._

**Source (L1)**
- Newrez: `newrez.portnewrezfc.loanid`  (Newrez-only detail)

**Flow:** ①portnewrezfc → ②basic_data_loan_foreclosure_bankruptcy → ③sync_loan_foreclosure_bankruptcy
**Lineage (per hop: # column — rule [code])**
- 1. `newrez.portnewrezfc.loanid` — servicer raw
- 2. `port.basic_data_loan_foreclosure_bankruptcy.loanid` — passthrough
- 3. `bpms.sync_loan_foreclosure_bankruptcy.loanid` — sync passthrough [asset]

### 3. Servicer loan id  (`bpms.sync_loan_foreclosure_bankruptcy.svcloanid`)

_Investor loan id / servicer loan id._

**Source (L1)**
- Newrez: `newrez.portnewrezfc.shellpointloanid`  (Newrez-only detail)

**Flow:** ①portnewrezfc → ②basic_data_loan_foreclosure_bankruptcy → ③sync_loan_foreclosure_bankruptcy
**Lineage (per hop: # column — rule [code])**
- 1. `newrez.portnewrezfc.shellpointloanid` — servicer raw
- 2. `port.basic_data_loan_foreclosure_bankruptcy.svcloanid` — passthrough
- 3. `bpms.sync_loan_foreclosure_bankruptcy.svcloanid` — sync passthrough [asset]

### 4. fctrdt  (`bpms.sync_loan_foreclosure_bankruptcy.fctrdt`)

_Daily snapshot/report date (=dataasof)._

**Source (L1)**
- Newrez: `port.basic_data_loan_fcl.dataasof`  (Newrez-only detail)

**Flow:** ①basic_data_loan_fcl → ②sync_loan_foreclosure_bankruptcy
**Lineage (per hop: # column — rule [code])**
- 1. `port.basic_data_loan_fcl.dataasof` — dataasof → fctrdt
- 2. `bpms.sync_loan_foreclosure_bankruptcy.fctrdt` — sync passthrough [asset]


## Bankruptcy filing

> Newrez-only detail (Carrington/others are not built in this table).

### 5. Bankruptcy Status  (`bpms.sync_loan_foreclosure_bankruptcy.bankruptcy_status`)

_BK status (decoded: 1→Active,2→Discharged,3→Dismissed,4→Closed,5→ReliefGranted)._

**Source (L1)**
- Newrez: `newrez.portnewrezbk` · bkstatus (code)  (Newrez-only detail)

**Flow:** ①portnewrezbk → ②basic_data_loan_foreclosure_bankruptcy → ③sync_loan_foreclosure_bankruptcy
**Lineage (per hop: # column — rule [code])**
- 1. `newrez.portnewrezbk` · bkstatus (code) — servicer raw 编码
- 2. `port.basic_data_loan_foreclosure_bankruptcy.bankruptcy_status` — datadic decode 解码 [pool:354,367](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L354)
- 3. `bpms.sync_loan_foreclosure_bankruptcy.bankruptcy_status` — GEN_FORECLOSURE_BK pass-through [asset:828](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L828)

```sql
COALESCE(datadic[field_name='BKStatus', code=bkstatus||'.0'].description, bkstatus)
```
🔎 **How it works:** Integer code → text via datadic (field_name='BKStatus'; join concat(code,'.0'); fallback to raw). Decode map: 1→Active, 2→Discharged, 3→Dismissed, 4→Closed, 5→ReliefGranted.
▶ **Example:** Loan 7727000010: bkstatus=1 ⇒ bankruptcy_status='Active'.

### 6. Legal Status  (`bpms.sync_loan_foreclosure_bankruptcy.legal_status`)

_Legal status (BK13/BK7)._

**Source (L1)**
- Newrez: `newrez.portnewrezgeneral.legalstatus`  (Newrez-only detail)

**Flow:** ①portnewrezgeneral → ②basic_data_loan_foreclosure_bankruptcy → ③sync_loan_foreclosure_bankruptcy
**Lineage (per hop: # column — rule [code])**
- 1. `newrez.portnewrezgeneral.legalstatus` — servicer raw
- 2. `port.basic_data_loan_foreclosure_bankruptcy.legal_status` — direct 直传 (join) [pool:355,365](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L355)
- 3. `bpms.sync_loan_foreclosure_bankruptcy.legal_status` — pass-through [asset:829](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L829)

**Note:** Sourced from portnewrezgeneral.legalstatus (not portnewrezbk), joined loanid+dataasof.

### 7. Status Date  (`bpms.sync_loan_foreclosure_bankruptcy.status_date`)

_BK filing date._

**Source (L1)**
- Newrez: `newrez.portnewrezbk.bkfileddate`  (Newrez-only detail)

**Flow:** ①portnewrezbk → ②basic_data_loan_foreclosure_bankruptcy → ③sync_loan_foreclosure_bankruptcy
**Lineage (per hop: # column — rule [code])**
- 1. `newrez.portnewrezbk.bkfileddate` — servicer raw
- 2. `port.basic_data_loan_foreclosure_bankruptcy.status_date` — rename (dedup key) [pool:356](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L356)
- 3. `bpms.sync_loan_foreclosure_bankruptcy.status_date` — pass-through [asset:830](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L830)

**Note:** status_date maps from bkfileddate (filing date), not a current-status date.

### 8. Chapter  (`bpms.sync_loan_foreclosure_bankruptcy.chapter`)

_BK chapter (7/11/13)._

**Source (L1)**
- Newrez: `newrez.portnewrezbk.bkchapter`  (Newrez-only detail)

**Flow:** ①portnewrezbk → ②basic_data_loan_foreclosure_bankruptcy → ③sync_loan_foreclosure_bankruptcy
**Lineage (per hop: # column — rule [code])**
- 1. `newrez.portnewrezbk.bkchapter` — servicer raw
- 2. `port.basic_data_loan_foreclosure_bankruptcy.chapter` — cast(decimal) 数值化 [pool:357](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L357)
- 3. `bpms.sync_loan_foreclosure_bankruptcy.chapter` — pass-through [asset:831](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L831)

### 9. Lien status  (`bpms.sync_loan_foreclosure_bankruptcy.lien_status`)

_Newrez: not populated (NULL). MFR fields are Carrington-only._

> ⚠ newrez_null

**Source (L1)**
- Newrez: `newrez.portnewrezbk` · (none for Newrez)  (Newrez-only detail)

**Flow:** ①portnewrezbk → ②basic_data_loan_foreclosure_bankruptcy → ③sync_loan_foreclosure_bankruptcy
**Lineage (per hop: # column — rule [code])**
- 1. `newrez.portnewrezbk` · (none for Newrez) — —
- 2. `port.basic_data_loan_foreclosure_bankruptcy.lien_status` — null (Newrez) 常量空 [pool:358-361](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L358-361)
- 3. `bpms.sync_loan_foreclosure_bankruptcy.lien_status` — GEN_FORECLOSURE_BK passthrough [asset:832-835](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L832-835)

### 10. MFR status  (`bpms.sync_loan_foreclosure_bankruptcy.mfr_status`)

_Newrez: not populated (NULL). MFR fields are Carrington-only._

> ⚠ newrez_null

**Source (L1)**
- Newrez: `newrez.portnewrezbk` · (none for Newrez)  (Newrez-only detail)

**Flow:** ①portnewrezbk → ②basic_data_loan_foreclosure_bankruptcy → ③sync_loan_foreclosure_bankruptcy
**Lineage (per hop: # column — rule [code])**
- 1. `newrez.portnewrezbk` · (none for Newrez) — —
- 2. `port.basic_data_loan_foreclosure_bankruptcy.mfr_status` — null (Newrez) 常量空 [pool:358-361](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L358-361)
- 3. `bpms.sync_loan_foreclosure_bankruptcy.mfr_status` — GEN_FORECLOSURE_BK passthrough [asset:832-835](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L832-835)

### 11. MFR filed date  (`bpms.sync_loan_foreclosure_bankruptcy.mfr_filed_date`)

_Newrez: not populated (NULL). MFR fields are Carrington-only._

> ⚠ newrez_null

**Source (L1)**
- Newrez: `newrez.portnewrezbk` · (none for Newrez)  (Newrez-only detail)

**Flow:** ①portnewrezbk → ②basic_data_loan_foreclosure_bankruptcy → ③sync_loan_foreclosure_bankruptcy
**Lineage (per hop: # column — rule [code])**
- 1. `newrez.portnewrezbk` · (none for Newrez) — —
- 2. `port.basic_data_loan_foreclosure_bankruptcy.mfr_filed_date` — null (Newrez) 常量空 [pool:358-361](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L358-361)
- 3. `bpms.sync_loan_foreclosure_bankruptcy.mfr_filed_date` — GEN_FORECLOSURE_BK passthrough [asset:832-835](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L832-835)

### 12. Claim status  (`bpms.sync_loan_foreclosure_bankruptcy.claim_status`)

_Newrez: not populated (NULL). MFR fields are Carrington-only._

> ⚠ newrez_null

**Source (L1)**
- Newrez: `newrez.portnewrezbk` · (none for Newrez)  (Newrez-only detail)

**Flow:** ①portnewrezbk → ②basic_data_loan_foreclosure_bankruptcy → ③sync_loan_foreclosure_bankruptcy
**Lineage (per hop: # column — rule [code])**
- 1. `newrez.portnewrezbk` · (none for Newrez) — —
- 2. `port.basic_data_loan_foreclosure_bankruptcy.claim_status` — null (Newrez) 常量空 [pool:358-361](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L358-361)
- 3. `bpms.sync_loan_foreclosure_bankruptcy.claim_status` — GEN_FORECLOSURE_BK passthrough [asset:832-835](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L832-835)

### 13. Proof of Claim Date  (`bpms.sync_loan_foreclosure_bankruptcy.proof_of_claim_date`)

_Proof-of-claim filed date._

**Source (L1)**
- Newrez: `newrez.portnewrezbk.pocfileddate`  (Newrez-only detail)

**Flow:** ①portnewrezbk → ②basic_data_loan_foreclosure_bankruptcy → ③sync_loan_foreclosure_bankruptcy
**Lineage (per hop: # column — rule [code])**
- 1. `newrez.portnewrezbk.pocfileddate` — servicer raw
- 2. `port.basic_data_loan_foreclosure_bankruptcy.proof_of_claim_date` — rename 改名 [pool:362](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L362)
- 3. `bpms.sync_loan_foreclosure_bankruptcy.proof_of_claim_date` — pass-through [asset:836](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L836)

### 14. Post-petition due date  (`bpms.sync_loan_foreclosure_bankruptcy.post_petition_due_date`)

_Post-petition payment due date._

**Source (L1)**
- Newrez: `newrez.portnewrezbk.bkpostpetitionduedate`  (Newrez-only detail)

**Flow:** ①portnewrezbk → ②basic_data_loan_foreclosure_bankruptcy → ③sync_loan_foreclosure_bankruptcy
**Lineage (per hop: # column — rule [code])**
- 1. `newrez.portnewrezbk.bkpostpetitionduedate` — servicer raw
- 2. `port.basic_data_loan_foreclosure_bankruptcy.post_petition_due_date` — rename 改名 [pool:363](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L363)
- 3. `bpms.sync_loan_foreclosure_bankruptcy.post_petition_due_date` — pass-through [asset:837](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L837)


## System / audit columns

> Newrez-only detail (Carrington/others are not built in this table).

### 15. System / audit columns

_App/ETL-managed columns (not servicer-sourced)._

**Columns:** `create_user, create_dept, create_time, update_user, update_time, status, is_deleted, tenant_id`

**Note:** Columns: create_user, create_dept, create_time, update_user, update_time, status, is_deleted, tenant_id. tenant_id ← GET_LOAN_TENANT_ID(portfunding ⋈ basic_data_trust_funding, [asset:932-936](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L932-936)); create_*/update_* set by the BPS app; is_deleted constant 0 (view); status app flag. Not servicer data.


> This doc covers 15 fields.
