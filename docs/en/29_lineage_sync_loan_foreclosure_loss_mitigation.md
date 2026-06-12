# Doc 29 · Loss Mitigation (code→text decode) — `bpms.sync_loan_foreclosure_loss_mitigation` field lineage

> <!-- RULEGLOSS_PTR -->📖 **Rule terms**: plain-language + formula for the technical phrases in the `rule` column — see [doc 25 · transform-rule glossary (appendix)](25_fcl_lineage_overview.md).
> <!-- CODEGLOSS_PTR -->🔧 **code legend**: `pool`=ETL build/SQL code `basic_data_pool_config.py` · `asset`=BPS sync SQL `asset_managment_config.py` · `view`=BPS view definition; the number after the colon = **line number** in that file (links are clickable).

> **Data source** — the source of truth is `outputs/fcl_lineage_source.json` (per-field lineage); these per-field docs are currently hand-maintained (the old generator `scripts/gen_fcl_lineage.py` has been retired/removed).


## Document Purpose

Per-field lineage for BPS table `bpms.sync_loan_foreclosure_loss_mitigation`: from the Servicer raw column, through every intermediate table, to the final BPS column, with each hop's transform rule and code reference.

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


`newrez.portnewrezlm` → `port.basic_data_loan_foreclosure_loss_mitigation` → `bpms.sync_loan_foreclosure_loss_mitigation`

| # | layer | db | table | role |
|---|---|---|---|---|
| 1 | L0/L1 | MySQL+Redshift | `newrez.portnewrezlm` | Servicer raw (coded) |
| 2 | L4 | Redshift | `port.basic_data_loan_foreclosure_loss_mitigation` | datadic decode (COALESCE(desc, code)); dedup latest per loan+cycle |
| 3 | L5 | MySQL bpms | `bpms.sync_loan_foreclosure_loss_mitigation` | BPS app table (GEN_FORECLOSURE_LM pass-through) |

> The `#` column is a sequence number, not the layer number. The FCL fact `port.basic_data_loan_fcl` is built DIRECTLY from the L1 servicer raw tables (UNIONed in `tempfc.temp_basic_data_fcl`; CREATE_BASIC_FCL [pool:1531-1654](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L1531-1654)), so the L2 unified-daily (`port.basic_data_daily_loan_common`) and L3 clean (`basic_data_daily_loan_common_clean` / `basic_data_loan_delinq_clean`) layers are NOT part of this branch by design — they carry the common + delinquency fields and re-enter only via the `group` dimension (doc 27, `basic_data_fcl_related`) and the monthly `portmonth` path. See doc 02 for the full L0–L5 pipeline.

> code: `pool` = [PrefectFlow/flow/basic_data/basic_data_config/basic_data_pool_config.py](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py) · `asset` = [PrefectFlow/flow/bps/bps_config/asset_managment_config.py](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py) · `view` = bpms.biz_data_view_loan_details_foreclosure (SHOW CREATE VIEW)

> Datadic decode pattern (LM deal/program/status/decision/denial/borrower, BK status): COALESCE((SELECT description FROM newrez.portnewrezdatadic WHERE field_name='<X>' AND code=CONCAT(raw,'.0')), raw) — raw codes stored as '5.0'; falls back to the raw code if no dictionary row.


## Identity / key columns

> Newrez-only detail (Carrington/others are not built in this table).

### 1. id (PK)  (`bpms.sync_loan_foreclosure_loss_mitigation.id`)

_Auto surrogate primary key._

**Source (L1)**
- Newrez: `bpms.sync_loan_foreclosure_loss_mitigation.id`  (Newrez-only detail)

**Flow:** ①sync_loan_foreclosure_loss_mitigation
**Lineage (per hop: # column — rule [code])**
- 1. `bpms.sync_loan_foreclosure_loss_mitigation.id` — auto-increment PK (BPS app) [asset]

**Note:** Generated by the BPS app on insert; not from source.

### 2. Investor loan id  (`bpms.sync_loan_foreclosure_loss_mitigation.loanid`)

_Investor loan id / servicer loan id._

**Source (L1)**
- Newrez: `newrez.portnewrezfc.loanid`  (Newrez-only detail)

**Flow:** ①portnewrezfc → ②basic_data_loan_foreclosure_loss_mitigation → ③sync_loan_foreclosure_loss_mitigation
**Lineage (per hop: # column — rule [code])**
- 1. `newrez.portnewrezfc.loanid` — servicer raw
- 2. `port.basic_data_loan_foreclosure_loss_mitigation.loanid` — passthrough
- 3. `bpms.sync_loan_foreclosure_loss_mitigation.loanid` — sync passthrough [asset]

### 3. Servicer loan id  (`bpms.sync_loan_foreclosure_loss_mitigation.svcloanid`)

_Investor loan id / servicer loan id._

**Source (L1)**
- Newrez: `newrez.portnewrezfc.shellpointloanid`  (Newrez-only detail)

**Flow:** ①portnewrezfc → ②basic_data_loan_foreclosure_loss_mitigation → ③sync_loan_foreclosure_loss_mitigation
**Lineage (per hop: # column — rule [code])**
- 1. `newrez.portnewrezfc.shellpointloanid` — servicer raw
- 2. `port.basic_data_loan_foreclosure_loss_mitigation.svcloanid` — passthrough
- 3. `bpms.sync_loan_foreclosure_loss_mitigation.svcloanid` — sync passthrough [asset]

### 4. fctrdt  (`bpms.sync_loan_foreclosure_loss_mitigation.fctrdt`)

_Daily snapshot/report date (=dataasof)._

**Source (L1)**
- Newrez: `port.basic_data_loan_fcl.dataasof`  (Newrez-only detail)

**Flow:** ①basic_data_loan_fcl → ②sync_loan_foreclosure_loss_mitigation
**Lineage (per hop: # column — rule [code])**
- 1. `port.basic_data_loan_fcl.dataasof` — dataasof → fctrdt
- 2. `bpms.sync_loan_foreclosure_loss_mitigation.fctrdt` — sync passthrough [asset]


## Loss-Mitigation cycle

> Newrez-only detail (Carrington/others are not built in this table).

### 5. Deal  (`bpms.sync_loan_foreclosure_loss_mitigation.deal`)

_LM deal type (decoded)._

**Source (L1)**
- Newrez: `newrez.portnewrezlm` · lmdeal (code)  (Newrez-only detail)

**Flow:** ①portnewrezlm → ②basic_data_loan_foreclosure_loss_mitigation → ③sync_loan_foreclosure_loss_mitigation
**Lineage (per hop: # column — rule [code])**
- 1. `newrez.portnewrezlm` · lmdeal (code) — servicer raw 编码
- 2. `port.basic_data_loan_foreclosure_loss_mitigation.deal` — datadic decode 解码 见 sql [pool:821,835](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L821)
- 3. `bpms.sync_loan_foreclosure_loss_mitigation.deal` — GEN_FORECLOSURE_LM pass-through [asset:804](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L804)

```sql
COALESCE(datadic[field_name='LMDeal', code=lmdeal||'.0'].description, lmdeal)
```
🔎 **How it works:** Integer code → text via newrez.portnewrezdatadic (field_name='LMDeal'). Codes are stored as 'N.0', so the join key is concat(code,'.0'); COALESCE falls back to the raw code if no dictionary match.
▶ **Example:** 7727004408: lmdeal=2 ⇒ deal='Evaluation'.

### 6. Program  (`bpms.sync_loan_foreclosure_loss_mitigation.program`)

_LM program (decoded)._

**Source (L1)**
- Newrez: `newrez.portnewrezlm` · lmprogram (code)  (Newrez-only detail)

**Flow:** ①portnewrezlm → ②basic_data_loan_foreclosure_loss_mitigation → ③sync_loan_foreclosure_loss_mitigation
**Lineage (per hop: # column — rule [code])**
- 1. `newrez.portnewrezlm` · lmprogram (code) — servicer raw 编码
- 2. `port.basic_data_loan_foreclosure_loss_mitigation.program` — datadic decode 解码 [pool:822,836](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L822)
- 3. `bpms.sync_loan_foreclosure_loss_mitigation.program` — pass-through [asset:805](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L805)

```sql
COALESCE(datadic['LMProgram', lmprogram||'.0'], lmprogram)
```
🔎 **How it works:** Same datadic decode pattern, field_name='LMProgram' (join concat(code,'.0'); fallback to raw).
▶ **Example:** 7727004408: lmprogram=21 ⇒ program='Evaluation'.

### 7. Status  (`bpms.sync_loan_foreclosure_loss_mitigation.lmc_status`)

_LM cycle status (decoded)._

**Source (L1)**
- Newrez: `newrez.portnewrezlm` · lmstatus (code)  (Newrez-only detail)

**Flow:** ①portnewrezlm → ②basic_data_loan_foreclosure_loss_mitigation → ③sync_loan_foreclosure_loss_mitigation
**Lineage (per hop: # column — rule [code])**
- 1. `newrez.portnewrezlm` · lmstatus (code) — servicer raw 编码
- 2. `port.basic_data_loan_foreclosure_loss_mitigation.lmc_status` — datadic decode 解码 [pool:823,837](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L823)
- 3. `bpms.sync_loan_foreclosure_loss_mitigation.lmc_status` — pass-through [asset:806](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L806)

```sql
COALESCE(datadic['LMStatus', lmstatus||'.0'], lmstatus)
```
🔎 **How it works:** Same datadic decode pattern, field_name='LMStatus' (join concat(code,'.0'); fallback to raw).
▶ **Example:** 7727004408: lmstatus=166 ⇒ lmc_status='Pending Financials'.

### 8. Cycle Opened Date  (`bpms.sync_loan_foreclosure_loss_mitigation.cycle_opened_date`)

_LM cycle start._

**Source (L1)**
- Newrez: `newrez.portnewrezlm.dealstartdate`  (Newrez-only detail)

**Flow:** ①portnewrezlm → ②basic_data_loan_foreclosure_loss_mitigation → ③sync_loan_foreclosure_loss_mitigation
**Lineage (per hop: # column — rule [code])**
- 1. `newrez.portnewrezlm.dealstartdate` — servicer raw
- 2. `port.basic_data_loan_foreclosure_loss_mitigation.cycle_opened_date` — rename 改名 (dedup key) [pool:824](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L824)
- 3. `bpms.sync_loan_foreclosure_loss_mitigation.cycle_opened_date` — pass-through [asset:807](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L807)

### 9. Cycle Closed Date  (`bpms.sync_loan_foreclosure_loss_mitigation.cycle_closed_date`)

_LM cycle end (NULL = open)._

**Source (L1)**
- Newrez: `newrez.portnewrezlm.lmremovaldate`  (Newrez-only detail)

**Flow:** ①portnewrezlm → ②basic_data_loan_foreclosure_loss_mitigation → ③sync_loan_foreclosure_loss_mitigation
**Lineage (per hop: # column — rule [code])**
- 1. `newrez.portnewrezlm.lmremovaldate` — servicer raw
- 2. `port.basic_data_loan_foreclosure_loss_mitigation.cycle_closed_date` — rename 改名 [pool:825](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L825)
- 3. `bpms.sync_loan_foreclosure_loss_mitigation.cycle_closed_date` — pass-through [asset:808](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L808)

### 10. Final Disposition  (`bpms.sync_loan_foreclosure_loss_mitigation.final_disposition`)

_LM final decision (decoded)._

**Source (L1)**
- Newrez: `newrez.portnewrezlm` · lmdecision (code)  (Newrez-only detail)

**Flow:** ①portnewrezlm → ②basic_data_loan_foreclosure_loss_mitigation → ③sync_loan_foreclosure_loss_mitigation
**Lineage (per hop: # column — rule [code])**
- 1. `newrez.portnewrezlm` · lmdecision (code) — servicer raw 编码
- 2. `port.basic_data_loan_foreclosure_loss_mitigation.final_disposition` — datadic decode 解码 [pool:826,838](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L826)
- 3. `bpms.sync_loan_foreclosure_loss_mitigation.final_disposition` — pass-through [asset:809](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L809)

```sql
COALESCE(datadic['LMDecision', lmdecision||'.0'], lmdecision)
```
🔎 **How it works:** Same datadic decode pattern, field_name='LMDecision' (join concat(code,'.0'); fallback to raw).
▶ **Example:** 7727004408: lmdecision=99 ⇒ final_disposition='Pending'.

### 11. Denial / Reason  (`bpms.sync_loan_foreclosure_loss_mitigation.denialreason`)

_Denial reason (decoded)._

**Source (L1)**
- Newrez: `newrez.portnewrezlm` · denialreason (code)  (Newrez-only detail)

**Flow:** ①portnewrezlm → ②basic_data_loan_foreclosure_loss_mitigation → ③sync_loan_foreclosure_loss_mitigation
**Lineage (per hop: # column — rule [code])**
- 1. `newrez.portnewrezlm` · denialreason (code) — servicer raw 编码
- 2. `port.basic_data_loan_foreclosure_loss_mitigation.denialreason` — datadic decode 解码 [pool:828,840](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L828)
- 3. `bpms.sync_loan_foreclosure_loss_mitigation.denialreason` — pass-through [asset:810](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L810)

```sql
COALESCE(datadic['DenialReason', denialreason||'.0'], denialreason)
```
🔎 **How it works:** Same datadic decode pattern, field_name='DenialReason' (join concat(code,'.0'); fallback to raw).
▶ **Example:** 7727004408 (Short Sale cycle): denialreason=78 ⇒ 'Buyer walked (SS)'.

### 12. Borrower Intentions  (`bpms.sync_loan_foreclosure_loss_mitigation.borrower_intentions`)

_Borrower intention (decoded)._

**Source (L1)**
- Newrez: `newrez.portnewrezlm` · borrowerintention (code)  (Newrez-only detail)

**Flow:** ①portnewrezlm → ②basic_data_loan_foreclosure_loss_mitigation → ③sync_loan_foreclosure_loss_mitigation
**Lineage (per hop: # column — rule [code])**
- 1. `newrez.portnewrezlm` · borrowerintention (code) — servicer raw 编码
- 2. `port.basic_data_loan_foreclosure_loss_mitigation.borrower_intentions` — datadic decode 解码 [pool:829,839](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L829)
- 3. `bpms.sync_loan_foreclosure_loss_mitigation.borrower_intentions` — pass-through [asset:811](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L811)

**Note:** Raw col borrowerintention (singular) → out borrower_intentions (plural).

```sql
COALESCE(datadic['BorrowerIntention', borrowerintention||'.0'], borrowerintention)
```
🔎 **How it works:** Same datadic decode pattern, field_name='BorrowerIntention' (join concat(code,'.0'); fallback to raw). Note raw col is borrowerintention (singular) → output borrower_intentions (plural).
▶ **Example:** 7727004408 (Short Sale cycle): borrowerintention=3 ⇒ 'Disposition'.

### 13. Imminent default flag  (`bpms.sync_loan_foreclosure_loss_mitigation.imminent_default`)

_Imminent default flag._

> ⚠ newrez_null

**Source (L1)**
- Newrez: `newrez.portnewrezlm`  (Newrez-only detail)

**Flow:** ①portnewrezlm → ②basic_data_loan_foreclosure_loss_mitigation → ③sync_loan_foreclosure_loss_mitigation
**Lineage (per hop: # column — rule [code])**
- 1. `newrez.portnewrezlm` — 无源
- 2. `port.basic_data_loan_foreclosure_loss_mitigation.imminent_default` — null [pool:830](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L830)
- 3. `bpms.sync_loan_foreclosure_loss_mitigation.imminent_default` — pass-through [asset:812](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L812)

**Note:** Hardcoded NULL for Newrez.

### 14. Single point of contact  (`bpms.sync_loan_foreclosure_loss_mitigation.single_point_of_contact`)

_SPOC._

> ⚠ newrez_null

**Source (L1)**
- Newrez: `newrez.portnewrezlm`  (Newrez-only detail)

**Flow:** ①portnewrezlm → ②basic_data_loan_foreclosure_loss_mitigation → ③sync_loan_foreclosure_loss_mitigation
**Lineage (per hop: # column — rule [code])**
- 1. `newrez.portnewrezlm` — 无源
- 2. `port.basic_data_loan_foreclosure_loss_mitigation.single_point_of_contact` — null [pool:831](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L831)
- 3. `bpms.sync_loan_foreclosure_loss_mitigation.single_point_of_contact` — pass-through [asset:813](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L813)

**Note:** Hardcoded NULL for Newrez.


## System / audit columns

> Newrez-only detail (Carrington/others are not built in this table).

### 15. System / audit columns

_App/ETL-managed columns (not servicer-sourced)._

**Columns:** `create_user, create_dept, create_time, update_user, update_time, status, is_deleted, tenant_id`

**Note:** Columns: create_user, create_dept, create_time, update_user, update_time, status, is_deleted, tenant_id. tenant_id ← GET_LOAN_TENANT_ID(portfunding ⋈ basic_data_trust_funding, [asset:932-936](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L932-936)); create_*/update_* set by the BPS app; is_deleted constant 0 (view); status app flag. Not servicer data.


> This doc covers 15 fields.
