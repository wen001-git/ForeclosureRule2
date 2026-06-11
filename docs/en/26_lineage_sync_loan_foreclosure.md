# Doc 26 · Main (milestones / summary / status) — `bpms.sync_loan_foreclosure` field lineage

> <!-- RULEGLOSS_PTR -->📖 **Rule terms**: plain-language + formula for the technical phrases in the `rule` column — see [doc 25 · transform-rule glossary (appendix)](25_fcl_lineage_overview.md).

> **Auto-generated** — to change, edit `outputs/fcl_lineage_source.json` and re-run `python - < scripts/gen_fcl_lineage.py`; do not hand-edit this file.


## Document Purpose

Per-field lineage for BPS table `bpms.sync_loan_foreclosure`: from the Servicer raw column, through every intermediate table, to the final BPS column, with each hop's transform rule and code reference.

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


`newrez.portnewrezfc` → `tempfc.temp_basic_data_fcl` → `port.basic_data_loan_fcl` → `port.basic_data_loan_foreclosure` → `bpms.sync_loan_foreclosure` → `bpms.biz_data_view_loan_details_foreclosure`

| # | layer | db | table | role |
|---|---|---|---|---|
| 1 | L0/L1 | MySQL+Redshift | `newrez.portnewrezfc` | Servicer raw |
| 2 | L4·temp | Redshift | `tempfc.temp_basic_data_fcl` | 3-servicer rename-UNION of L1 raw / 三家 servicer 改名 UNION (CREATE_BASIC_FCL, [pool:1531-1654](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L1531-1654)) |
| 3 | L4 | Redshift | `port.basic_data_loan_fcl` | canonical FCL fact |
| 4 | L4 | Redshift→MySQL | `port.basic_data_loan_foreclosure` | timeline+summary build (GEN_FCL_DETAIL) |
| 5 | L5 | MySQL bpms | `bpms.sync_loan_foreclosure` | BPS app table (UPDATE_FORECLOSURE upsert) |
| 6 | L5 | MySQL bpms | `bpms.biz_data_view_loan_details_foreclosure` | display view (Actual/Var days) |

> The `#` column is a sequence number, not the layer number. The FCL fact `port.basic_data_loan_fcl` is built DIRECTLY from the L1 servicer raw tables (UNIONed in `tempfc.temp_basic_data_fcl`; CREATE_BASIC_FCL [pool:1531-1654](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L1531-1654)), so the L2 unified-daily (`port.basic_data_daily_loan_common`) and L3 clean (`basic_data_daily_loan_common_clean` / `basic_data_loan_delinq_clean`) layers are NOT part of this branch by design — they carry the common + delinquency fields and re-enter only via the `group` dimension (doc 27, `basic_data_fcl_related`) and the monthly `portmonth` path. See doc 02 for the full L0–L5 pipeline.

> code: `pool` = [PrefectFlow/flow/basic_data/basic_data_config/basic_data_pool_config.py](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py) · `asset` = [PrefectFlow/flow/bps/bps_config/asset_managment_config.py](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py) · `view` = bpms.biz_data_view_loan_details_foreclosure (SHOW CREATE VIEW)


## Identity / key columns

### 1. id (PK)  (`bpms.sync_loan_foreclosure.id`)

_Auto surrogate primary key._

**Source (L1)**
- Newrez: `bpms.sync_loan_foreclosure.id`  (Newrez-only detail)

**Flow:** ①sync_loan_foreclosure
**Lineage (per hop: # column — rule [code])**
- 1. `bpms.sync_loan_foreclosure.id` — auto-increment PK (BPS app) [asset]

**Note:** Generated by the BPS app on insert; not from source.

### 2. bid_id (deal id)  (`bpms.sync_loan_foreclosure.bid_id`)

_Bridger deal id._

**Source (L1)**
- Newrez: `port.portfunding.dealid`  (Newrez-only detail)

**Flow:** ①portfunding → ②sync_loan_foreclosure  (the view `biz_data_view_loan_details_foreclosure` does not expose this column, so the chain terminates at the sync table)
**Lineage (per hop: # column — rule [code])**
- 1. `port.portfunding.dealid` — join on loanid [asset:541,604](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L541)
- 2. `bpms.sync_loan_foreclosure.bid_id` — dealid → bid_id [asset:541](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L541)

### 3. funding_id  (`bpms.sync_loan_foreclosure.funding_id`)

_Bridger funding id._

**Source (L1)**
- Newrez: `port.portfunding.fundingid`  (Newrez-only detail)

**Flow:** ①portfunding → ②sync_loan_foreclosure  (the view `biz_data_view_loan_details_foreclosure` does not expose this column, so the chain terminates at the sync table)
**Lineage (per hop: # column — rule [code])**
- 1. `port.portfunding.fundingid` — join on loanid [asset:542,604](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L542)
- 2. `bpms.sync_loan_foreclosure.funding_id` — fundingid → funding_id [asset:542](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L542)

### 4. Investor loan id  (`bpms.sync_loan_foreclosure.loanid`)

_Investor loan id / servicer loan id._

**Source (L1)**
- Newrez: `newrez.portnewrezfc.loanid`  (Newrez-only detail)

**Flow:** ①portnewrezfc → ②basic_data_loan_fcl → ③basic_data_loan_foreclosure → ④sync_loan_foreclosure → ⑤biz_data_view_loan_details_foreclosure
**Lineage (per hop: # column — rule [code])**
- 1. `newrez.portnewrezfc.loanid` — servicer raw 原始
- 2. `port.basic_data_loan_fcl.loanid` — rename/passthrough 改名直传
- 3. `port.basic_data_loan_foreclosure.loanid` — passthrough 直传
- 4. `bpms.sync_loan_foreclosure.loanid` — GEN_FORECLOSURE join port.portfunding 直传 [asset:543](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L543)
- 5. `bpms.biz_data_view_loan_details_foreclosure.loanid` — passthrough [view]

### 5. Servicer loan id  (`bpms.sync_loan_foreclosure.svcloanid`)

_Investor loan id / servicer loan id._

**Source (L1)**
- Newrez: `newrez.portnewrezfc.shellpointloanid`  (Newrez-only detail)

**Flow:** ①portnewrezfc → ②basic_data_loan_fcl → ③basic_data_loan_foreclosure → ④sync_loan_foreclosure → ⑤biz_data_view_loan_details_foreclosure
**Lineage (per hop: # column — rule [code])**
- 1. `newrez.portnewrezfc.shellpointloanid` — servicer raw 原始
- 2. `port.basic_data_loan_fcl.svc_loanid` — rename/passthrough 改名直传
- 3. `port.basic_data_loan_foreclosure.svcloanid` — passthrough 直传
- 4. `bpms.sync_loan_foreclosure.svcloanid` — GEN_FORECLOSURE join port.portfunding 直传 [asset:543](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L543)
- 5. `bpms.biz_data_view_loan_details_foreclosure.svcloanid` — passthrough [view]

### 6. servicer  (`bpms.sync_loan_foreclosure.servicer`)

_Servicer name._

**Source (L1)**
- Newrez: `(per servicer)` · constant 'Newrez'/'Carrington'/'Capecodfive'  (Newrez-only detail)

**Flow:** ①(per → ②sync_loan_foreclosure
**Lineage (per hop: # column — rule [code])**
- 1. `(per servicer)` · constant 'Newrez'/'Carrington'/'Capecodfive' — constant per UNION branch [pool:1536/1577/1618](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L1536)
- 2. `bpms.sync_loan_foreclosure.servicer` — sync passthrough [asset]


## Timeline milestones

### 7. Notice of Intent Date  (`bpms.sync_loan_foreclosure.timeline_notice_of_intent_date`)

_NOI/Demand letter date._

> ⚠ newrez_null

**Source (L1)**
- Newrez: —
- Carrington: —
- Capecodfive: `capecodfive.portcapecodfive_monthly_collections.noi_date`

**Flow:** ①basic_data_loan_fcl → ②basic_data_loan_foreclosure → ③sync_loan_foreclosure → ④biz_data_view_loan_details_foreclosure
**Lineage (per hop: # column — rule [code])**
- 1. `port.basic_data_loan_fcl.noi_date` — null for Newrez（常量空） [pool:1542](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L1542)
- 2. `port.basic_data_loan_foreclosure.timeline_notice_of_intent_date` — direct copy 直传 [pool:258](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L258)
- 3. `bpms.sync_loan_foreclosure.timeline_notice_of_intent_date` — upsert pass-through 直传 [asset:703/753](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L703)
- 4. `bpms.biz_data_view_loan_details_foreclosure` · timeline_notice_of_intent_date (+actual/var) — view: actual=to_days(x)-to_days(nextduedate); var=actual-target [view]

**Note:** Newrez has no NOI source → NULL; only Capecodfive populates noi_date.

### 8. End date of notice of intent  (`bpms.sync_loan_foreclosure.timeline_notice_of_intent_end_date`)

_Reserved milestone; not populated by the FCL ETL._

> ⚠ null_in_build

**Source (L1)**
- Newrez: `port.basic_data_loan_foreclosure.timeline_notice_of_intent_end_date`  (Newrez-only detail)

**Flow:** ①basic_data_loan_foreclosure → ②sync_loan_foreclosure → ③biz_data_view_loan_details_foreclosure
**Lineage (per hop: # column — rule [code])**
- 1. `port.basic_data_loan_foreclosure.timeline_notice_of_intent_end_date` — not in GEN_FCL_DETAIL INSERT → NULL 未填充 [pool:148-305](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L148-305)
- 2. `bpms.sync_loan_foreclosure.timeline_notice_of_intent_end_date` — GEN_FORECLOSURE 直传（值=NULL） [asset:540-605](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L540-605)
- 3. `bpms.biz_data_view_loan_details_foreclosure.timeline_notice_of_intent_end_date` — passthrough [view]

### 9. Approval for referral  (`bpms.sync_loan_foreclosure.timeline_approved_for_referral_date`)

_Reserved milestone; not populated by the FCL ETL._

> ⚠ null_in_build

**Source (L1)**
- Newrez: `port.basic_data_loan_foreclosure.timeline_approved_for_referral_date`  (Newrez-only detail)

**Flow:** ①basic_data_loan_foreclosure → ②sync_loan_foreclosure → ③biz_data_view_loan_details_foreclosure
**Lineage (per hop: # column — rule [code])**
- 1. `port.basic_data_loan_foreclosure.timeline_approved_for_referral_date` — not in GEN_FCL_DETAIL INSERT → NULL 未填充 [pool:148-305](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L148-305)
- 2. `bpms.sync_loan_foreclosure.timeline_approved_for_referral_date` — GEN_FORECLOSURE 直传（值=NULL） [asset:540-605](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L540-605)
- 3. `bpms.biz_data_view_loan_details_foreclosure.timeline_approved_for_referral_date` — passthrough [view]

### 10. Date referred to attorney  (`bpms.sync_loan_foreclosure.timeline_referred_to_attorney_date`)

_Reserved milestone; not populated by the FCL ETL._

> ⚠ null_in_build

**Source (L1)**
- Newrez: `port.basic_data_loan_foreclosure.timeline_referred_to_attorney_date`  (Newrez-only detail)

**Flow:** ①basic_data_loan_foreclosure → ②sync_loan_foreclosure → ③biz_data_view_loan_details_foreclosure
**Lineage (per hop: # column — rule [code])**
- 1. `port.basic_data_loan_foreclosure.timeline_referred_to_attorney_date` — not in GEN_FCL_DETAIL INSERT → NULL 未填充 [pool:148-305](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L148-305)
- 2. `bpms.sync_loan_foreclosure.timeline_referred_to_attorney_date` — GEN_FORECLOSURE 直传（值=NULL） [asset:540-605](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L540-605)
- 3. `bpms.biz_data_view_loan_details_foreclosure.timeline_referred_to_attorney_date` — passthrough [view]

### 11. Referred to Foreclosure (Referral)  (`bpms.sync_loan_foreclosure.timeline_referred_to_foreclosure_date`)

_Formal FCL referral date; BPS ingestion filter (must be non-null)._

**Source (L1)**
- Newrez: `newrez.portnewrezfc.fcreferraldate`
- Carrington: `carrington.portcarrington.fcl_referral_date`
- Capecodfive: `capecodfive.portcapecodfive_monthly_collections.foreclosure_date_refrd_atty`

**Flow:** ①basic_data_loan_fcl → ②basic_data_loan_foreclosure → ③sync_loan_foreclosure → ④biz_data_view_loan_details_foreclosure
**Lineage (per hop: # column — rule [code])**
- 1. `port.basic_data_loan_fcl.referral_start_date` — rename 改名 [pool:1544](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L1544)
- 2. `port.basic_data_loan_foreclosure.timeline_referred_to_foreclosure_date` — direct copy 直传 [pool:259](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L259)
- 3. `bpms.sync_loan_foreclosure.timeline_referred_to_foreclosure_date` — upsert pass-through 直传 [asset:707/757](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L707)
- 4. `bpms.biz_data_view_loan_details_foreclosure` · timeline_referred_to_foreclosure_date (+actual/var) — view: actual=to_days(x)-to_days(nextduedate); var=actual-Σtarget [view]

### 12. Title Report Received  (`bpms.sync_loan_foreclosure.timeline_title_report_received_date`)

_Title report received date._

> ⚠ newrez_empty

**Source (L1)**
- Newrez: `newrez.portnewrezfc.titlereceiveddate`
- Carrington: —
- Capecodfive: —

**Flow:** ①basic_data_loan_fcl → ②basic_data_loan_foreclosure → ③sync_loan_foreclosure → ④biz_data_view_loan_details_foreclosure
**Lineage (per hop: # column — rule [code])**
- 1. `port.basic_data_loan_fcl.titlereceiveddate` — rename 改名 [pool:1540](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L1540)
- 2. `port.basic_data_loan_foreclosure.timeline_title_report_received_date` — direct copy 直传 [pool:260](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L260)
- 3. `bpms.sync_loan_foreclosure.timeline_title_report_received_date` — upsert pass-through [asset:758](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L758)
- 4. `bpms.biz_data_view_loan_details_foreclosure` · timeline_title_report_received_date (+actual/var) — view actual/var [view]

**Note:** Newrez does not populate titlereceiveddate (active FCL ~0%).

### 13. Preliminary Title Cleared  (`bpms.sync_loan_foreclosure.timeline_preliminary_title_cleared_date`)

_Preliminary title-clear date._

> ⚠ newrez_empty

**Source (L1)**
- Newrez: `newrez.portnewrezfc.titlecleardate`
- Carrington: —
- Capecodfive: —

**Flow:** ①basic_data_loan_fcl → ②basic_data_loan_foreclosure → ③sync_loan_foreclosure → ④biz_data_view_loan_details_foreclosure
**Lineage (per hop: # column — rule [code])**
- 1. `port.basic_data_loan_fcl.titlecleardate` — rename 改名 [pool:1541](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L1541)
- 2. `port.basic_data_loan_foreclosure.timeline_preliminary_title_cleared_date` — direct copy 直传 [pool:261](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L261)
- 3. `bpms.sync_loan_foreclosure.timeline_preliminary_title_cleared_date` — upsert pass-through [asset:759](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L759)
- 4. `bpms.biz_data_view_loan_details_foreclosure` · timeline_preliminary_title_cleared_date (+actual/var) — view actual/var [view]

**Note:** Shares titlecleardate with Final Title Cleared; Newrez not populated.

### 14. 1st Legal  (`bpms.sync_loan_foreclosure.timeline_first_legal_date`)

_First legal action (filing) date._

**Source (L1)**
- Newrez: `newrez.portnewrezfc.firstlegaldate`
- Carrington: —
- Capecodfive: `capecodfive.portcapecodfive_monthly_collections.foreclosure_first_legal_date`

**Flow:** ①basic_data_loan_fcl → ②basic_data_loan_foreclosure → ③sync_loan_foreclosure → ④biz_data_view_loan_details_foreclosure
**Lineage (per hop: # column — rule [code])**
- 1. `port.basic_data_loan_fcl.legal_start_date` — rename 改名 [pool:1549](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L1549)
- 2. `port.basic_data_loan_foreclosure.timeline_first_legal_date` — direct copy 直传 [pool:262](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L262)
- 3. `bpms.sync_loan_foreclosure.timeline_first_legal_date` — upsert pass-through [asset:760](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L760)
- 4. `bpms.biz_data_view_loan_details_foreclosure` · timeline_first_legal_date (+actual/var) — view actual/var [view]

**Note:** Non-Judicial states usually empty.

### 15. Service Complete  (`bpms.sync_loan_foreclosure.timeline_service_date`)

_Legal document service completion date._

**Source (L1)**
- Newrez: `newrez.portnewrezfc.servicecompletedate`
- Carrington: —
- Capecodfive: `capecodfive.portcapecodfive_monthly_collections.foreclosure_service_date`

**Flow:** ①basic_data_loan_fcl → ②basic_data_loan_foreclosure → ③sync_loan_foreclosure → ④biz_data_view_loan_details_foreclosure
**Lineage (per hop: # column — rule [code])**
- 1. `port.basic_data_loan_fcl.service_start_date` — rename 改名 [pool:1550](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L1550)
- 2. `port.basic_data_loan_foreclosure.timeline_service_date` — direct copy 直传 [pool:263](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L263)
- 3. `bpms.sync_loan_foreclosure.timeline_service_date` — upsert pass-through [asset:761](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L761)
- 4. `bpms.biz_data_view_loan_details_foreclosure` · timeline_service_date (+actual/var) — view actual/var [view]

### 16. Publication scheduled date  (`bpms.sync_loan_foreclosure.timeline_publication_date`)

_Reserved milestone; not populated by the FCL ETL._

> ⚠ null_in_build

**Source (L1)**
- Newrez: `port.basic_data_loan_foreclosure.timeline_publication_date`  (Newrez-only detail)

**Flow:** ①basic_data_loan_foreclosure → ②sync_loan_foreclosure → ③biz_data_view_loan_details_foreclosure
**Lineage (per hop: # column — rule [code])**
- 1. `port.basic_data_loan_foreclosure.timeline_publication_date` — not in GEN_FCL_DETAIL INSERT → NULL 未填充 [pool:148-305](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L148-305)
- 2. `bpms.sync_loan_foreclosure.timeline_publication_date` — GEN_FORECLOSURE 直传（值=NULL） [asset:540-605](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L540-605)
- 3. `bpms.biz_data_view_loan_details_foreclosure.timeline_publication_date` — passthrough [view]

### 17. Judgement Hearing Set  (`bpms.sync_loan_foreclosure.timeline_judgement_hearing_set_date`)

_Date the current scheduled-hearing value first appeared in a snapshot (ETL tracking). Judicial only._

**Source (L1)**
- Newrez: `newrez.portnewrezfc.fcjudgmenthearingscheduled`
- Carrington: —
- Capecodfive: —

**Flow:** ①basic_data_loan_fcl → ②basic_data_loan_foreclosure → ③sync_loan_foreclosure → ④biz_data_view_loan_details_foreclosure
**Lineage (per hop: # column — rule [code])**
- 1. `port.basic_data_loan_fcl.fcjudgment_hearing_scheduled` — rename 改名 [pool:1551](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L1551)
- 2. `port.basic_data_loan_foreclosure.timeline_judgement_hearing_set_date` — ETL tracking: min(dataasof) of current value 首见日 [pool:264,295](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L264)
- 3. `bpms.sync_loan_foreclosure.timeline_judgement_hearing_set_date` — upsert pass-through [asset:762](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L762)
- 4. `bpms.biz_data_view_loan_details_foreclosure` · timeline_judgement_hearing_set_date (+actual/var) — view actual/var [view]

```sql
ju.jd_set_date = min(dataasof) FROM port.basic_data_loan_fcl WHERE fcjudgment_hearing_scheduled IS NOT NULL GROUP BY loanid, fcjudgment_hearing_scheduled
```
🔎 **How it works:** Tracks WHEN the current scheduled-hearing value first appeared: group the loan's daily snapshots by (loanid, fcjudgment_hearing_scheduled) and take MIN(dataasof). So it is the date that hearing date was first set — not the hearing date itself.
▶ **Example:** Loan 7727004408: the hearing date 2026-08-21 first appears in the 2026-05-14 snapshot ⇒ timeline_judgement_hearing_set_date = 2026-05-14 (while Judgement = 2026-08-21).

### 18. Judgement  (`bpms.sync_loan_foreclosure.timeline_judgement_date`)

_Currently scheduled judgement-hearing date (current value). NOT fcjudgmententered._

**Source (L1)**
- Newrez: `newrez.portnewrezfc.fcjudgmenthearingscheduled`
- Carrington: —
- Capecodfive: —

**Flow:** ①basic_data_loan_fcl → ②basic_data_loan_foreclosure → ③sync_loan_foreclosure → ④biz_data_view_loan_details_foreclosure
**Lineage (per hop: # column — rule [code])**
- 1. `port.basic_data_loan_fcl.fcjudgment_hearing_scheduled` — rename 改名 [pool:1551](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L1551)
- 2. `port.basic_data_loan_foreclosure.timeline_judgement_date` — direct copy (current value) 直传 [pool:265](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L265)
- 3. `bpms.sync_loan_foreclosure.timeline_judgement_date` — upsert pass-through [asset:763](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L763)
- 4. `bpms.biz_data_view_loan_details_foreclosure` · timeline_judgement_date (+actual/var) — view actual/var [view]

**Note:** Same raw field as Hearing Set, but this is the current value (not first-seen).

### 19. Sale Date Projected  (`bpms.sync_loan_foreclosure.timeline_sale_date_projected_date`)

_Latest projected/scheduled auction date (dynamic)._

**Source (L1)**
- Newrez: `newrez.portnewrezfc.fcscheduledsaledate`
- Carrington: `carrington.portcarrington.fcl_scheduled_sale_date`
- Capecodfive: `capecodfive.portcapecodfive_monthly_collections.foreclosure_date_sale_scheduled`

**Flow:** ①basic_data_loan_fcl → ②basic_data_loan_foreclosure → ③sync_loan_foreclosure → ④biz_data_view_loan_details_foreclosure
**Lineage (per hop: # column — rule [code])**
- 1. `port.basic_data_loan_fcl.fcscheduled_sale_date` — rename 改名 [pool:1553](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L1553)
- 2. `port.basic_data_loan_foreclosure.timeline_sale_date_projected_date` — direct copy 直传 [pool:266](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L266)
- 3. `bpms.sync_loan_foreclosure.timeline_sale_date_projected_date` — upsert pass-through [asset:764](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L764)
- 4. `bpms.biz_data_view_loan_details_foreclosure.timeline_sale_date_projected_date` — passthrough (no actual/var) [view]

### 20. Sale Date Set  (`bpms.sync_loan_foreclosure.timeline_sale_date_set_date`)

_Date the current scheduled-sale value first appeared in a snapshot (ETL tracking)._

**Source (L1)**
- Newrez: `newrez.portnewrezfc.fcscheduledsaledate`
- Carrington: `carrington.portcarrington.fcl_scheduled_sale_date`
- Capecodfive: `capecodfive.portcapecodfive_monthly_collections.foreclosure_date_sale_scheduled`

**Flow:** ①basic_data_loan_fcl → ②basic_data_loan_foreclosure → ③sync_loan_foreclosure → ④biz_data_view_loan_details_foreclosure
**Lineage (per hop: # column — rule [code])**
- 1. `port.basic_data_loan_fcl.fcscheduled_sale_date` — rename 改名 [pool:1553](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L1553)
- 2. `port.basic_data_loan_foreclosure.timeline_sale_date_set_date` — ETL tracking: min(dataasof) of current value 首见日 [pool:267,300](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L267)
- 3. `bpms.sync_loan_foreclosure.timeline_sale_date_set_date` — upsert pass-through [asset:765](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L765)
- 4. `bpms.biz_data_view_loan_details_foreclosure` · timeline_sale_date_set_date (+actual/var) — view actual/var [view]

```sql
sa.sa_set_date = min(dataasof) FROM port.basic_data_loan_fcl WHERE fcscheduled_sale_date IS NOT NULL GROUP BY loanid, fcscheduled_sale_date
```
🔎 **How it works:** Same first-seen logic as Hearing Set, for the scheduled-sale date: MIN(dataasof) over (loanid, fcscheduled_sale_date). The date the current sale date was first scheduled.
▶ **Example:** e.g. if a loan's scheduled sale 2026-06-23 first appears on the 2026-03-10 snapshot ⇒ timeline_sale_date_set_date = 2026-03-10 (Sale Date Projected stays 2026-06-23).

### 21. Final Title Cleared  (`bpms.sync_loan_foreclosure.timeline_final_title_cleared_date`)

_Final title-clear date._

> ⚠ newrez_empty

**Source (L1)**
- Newrez: `newrez.portnewrezfc.titlecleardate`
- Carrington: —
- Capecodfive: —

**Flow:** ①basic_data_loan_fcl → ②basic_data_loan_foreclosure → ③sync_loan_foreclosure → ④biz_data_view_loan_details_foreclosure
**Lineage (per hop: # column — rule [code])**
- 1. `port.basic_data_loan_fcl.titlecleardate` — rename 改名 [pool:1541](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L1541)
- 2. `port.basic_data_loan_foreclosure.timeline_final_title_cleared_date` — direct copy 直传 [pool:268](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L268)
- 3. `bpms.sync_loan_foreclosure.timeline_final_title_cleared_date` — upsert pass-through [asset:766](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L766)
- 4. `bpms.biz_data_view_loan_details_foreclosure` · timeline_final_title_cleared_date (+actual/var) — view actual/var [view]

**Note:** Shares titlecleardate with Preliminary; Newrez not populated.

### 22. Sale Held  (`bpms.sync_loan_foreclosure.timeline_sale_date_held_date`)

_Actual auction-held date._

**Source (L1)**
- Newrez: `newrez.portnewrezfc.fcsalehelddate`
- Carrington: `carrington.portcarrington.fcl_sale_held_date`
- Capecodfive: `capecodfive.portcapecodfive_monthly_collections.foreclosure_sale_date`

**Flow:** ①basic_data_loan_fcl → ②basic_data_loan_foreclosure → ③sync_loan_foreclosure → ④biz_data_view_loan_details_foreclosure
**Lineage (per hop: # column — rule [code])**
- 1. `port.basic_data_loan_fcl.fcsale_held_date` — rename 改名 [pool:1554](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L1554)
- 2. `port.basic_data_loan_foreclosure.timeline_sale_date_held_date` — direct copy 直传 [pool:269](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L269)
- 3. `bpms.sync_loan_foreclosure.timeline_sale_date_held_date` — upsert pass-through [asset:767](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L767)
- 4. `bpms.biz_data_view_loan_details_foreclosure` · timeline_sale_date_held_date (+actual/var) — view actual/var [view]

### 23. Date foreclosure was completed  (`bpms.sync_loan_foreclosure.timeline_foreclosure_completed_date`)

_Reserved milestone; not populated by the FCL ETL._

> ⚠ null_in_build

**Source (L1)**
- Newrez: `port.basic_data_loan_foreclosure.timeline_foreclosure_completed_date`  (Newrez-only detail)

**Flow:** ①basic_data_loan_foreclosure → ②sync_loan_foreclosure → ③biz_data_view_loan_details_foreclosure
**Lineage (per hop: # column — rule [code])**
- 1. `port.basic_data_loan_foreclosure.timeline_foreclosure_completed_date` — not in GEN_FCL_DETAIL INSERT → NULL 未填充 [pool:148-305](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L148-305)
- 2. `bpms.sync_loan_foreclosure.timeline_foreclosure_completed_date` — GEN_FORECLOSURE 直传（值=NULL） [asset:540-605](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L540-605)
- 3. `bpms.biz_data_view_loan_details_foreclosure.timeline_foreclosure_completed_date` — passthrough [view]

### 24. 3rd Party Sold Date  (`bpms.sync_loan_foreclosure.timeline_third_party_sold_date_date`)

_Third-party buyer sold date._

> ⚠ null_in_build

**Source (L1)**
- Newrez: —
- Carrington: —
- Capecodfive: —

**Flow:** ①basic_data_loan_fcl → ②basic_data_loan_foreclosure → ③sync_loan_foreclosure → ④biz_data_view_loan_details_foreclosure
**Lineage (per hop: # column — rule [code])**
- 1. `port.basic_data_loan_fcl` — —
- 2. `port.basic_data_loan_foreclosure.timeline_third_party_sold_date_date` — null 常量空 [pool:270](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L270)
- 3. `bpms.sync_loan_foreclosure.timeline_third_party_sold_date_date` — upsert pass-through [asset:769](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L769)
- 4. `bpms.biz_data_view_loan_details_foreclosure.timeline_third_party_sold_date_date` — passthrough [view]

**Note:** Hardcoded NULL in GEN_FCL_DETAIL (not mapped from raw here).

### 25. 3rd Party Proceeds Received  (`bpms.sync_loan_foreclosure.timeline_third_party_proceeds_received_date`)

_Third-party auction proceeds received date._

> ⚠ newrez_empty

**Source (L1)**
- Newrez: `newrez.portnewrezfc.fcl3rdpartyproceedsreceiveddate`
- Carrington: —
- Capecodfive: —

**Flow:** ①basic_data_loan_fcl → ②basic_data_loan_foreclosure → ③sync_loan_foreclosure → ④biz_data_view_loan_details_foreclosure
**Lineage (per hop: # column — rule [code])**
- 1. `port.basic_data_loan_fcl.fcl3rdpartyproceedsreceiveddate` — rename 改名 [pool:1558](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L1558)
- 2. `port.basic_data_loan_foreclosure.timeline_third_party_proceeds_received_date` — direct copy 直传 [pool:271](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L271)
- 3. `bpms.sync_loan_foreclosure.timeline_third_party_proceeds_received_date` — upsert pass-through [asset:770](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L770)
- 4. `bpms.biz_data_view_loan_details_foreclosure.timeline_third_party_proceeds_received_date` — passthrough [view]


## Target days (config; view defaults)

### 26. Target for notice of intent  (`bpms.sync_loan_foreclosure.target_notice_of_intent_days`)

_Target days for the milestone (config constant)._

> ⚠ view_default

**Source (L1)**
- Newrez: `port.basic_data_loan_foreclosure.target_notice_of_intent_days`  (Newrez-only detail)

**Flow:** ①basic_data_loan_foreclosure → ②sync_loan_foreclosure → ③biz_data_view_loan_details_foreclosure
**Lineage (per hop: # column — rule [code])**
- 1. `port.basic_data_loan_foreclosure.target_notice_of_intent_days` — NULL (not populated) [pool:174-188](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L174-188)
- 2. `bpms.sync_loan_foreclosure.target_notice_of_intent_days` — GEN_FORECLOSURE: target_* commented out → NULL [asset:564-577](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L564-577)
- 3. `bpms.biz_data_view_loan_details_foreclosure.target_notice_of_intent_days` — ifnull(target_notice_of_intent_days, <default>) — view default constant [view]

**Note:** Stored NULL in sync; the view supplies the default target (e.g. first_legal 120, service 90, judgement 30).

### 27. Target for notice of intent expiration  (`bpms.sync_loan_foreclosure.target_notice_of_intent_expired_days`)

_Target days for the milestone (config constant)._

> ⚠ view_default

**Source (L1)**
- Newrez: `port.basic_data_loan_foreclosure.target_notice_of_intent_expired_days`  (Newrez-only detail)

**Flow:** ①basic_data_loan_foreclosure → ②sync_loan_foreclosure → ③biz_data_view_loan_details_foreclosure
**Lineage (per hop: # column — rule [code])**
- 1. `port.basic_data_loan_foreclosure.target_notice_of_intent_expired_days` — NULL (not populated) [pool:174-188](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L174-188)
- 2. `bpms.sync_loan_foreclosure.target_notice_of_intent_expired_days` — GEN_FORECLOSURE: target_* commented out → NULL [asset:564-577](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L564-577)
- 3. `bpms.biz_data_view_loan_details_foreclosure.target_notice_of_intent_expired_days` — ifnull(target_notice_of_intent_expired_days, <default>) — view default constant [view]

**Note:** Stored NULL in sync; the view supplies the default target (e.g. first_legal 120, service 90, judgement 30).

### 28. Target for approval for referral  (`bpms.sync_loan_foreclosure.target_approved_for_referral_days`)

_Target days for the milestone (config constant)._

> ⚠ view_default

**Source (L1)**
- Newrez: `port.basic_data_loan_foreclosure.target_approved_for_referral_days`  (Newrez-only detail)

**Flow:** ①basic_data_loan_foreclosure → ②sync_loan_foreclosure → ③biz_data_view_loan_details_foreclosure
**Lineage (per hop: # column — rule [code])**
- 1. `port.basic_data_loan_foreclosure.target_approved_for_referral_days` — NULL (not populated) [pool:174-188](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L174-188)
- 2. `bpms.sync_loan_foreclosure.target_approved_for_referral_days` — GEN_FORECLOSURE: target_* commented out → NULL [asset:564-577](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L564-577)
- 3. `bpms.biz_data_view_loan_details_foreclosure.target_approved_for_referral_days` — ifnull(target_approved_for_referral_days, <default>) — view default constant [view]

**Note:** Stored NULL in sync; the view supplies the default target (e.g. first_legal 120, service 90, judgement 30).

### 29. Target for referred to attorney  (`bpms.sync_loan_foreclosure.target_referred_to_attorney_days`)

_Target days for the milestone (config constant)._

> ⚠ view_default

**Source (L1)**
- Newrez: `port.basic_data_loan_foreclosure.target_referred_to_attorney_days`  (Newrez-only detail)

**Flow:** ①basic_data_loan_foreclosure → ②sync_loan_foreclosure → ③biz_data_view_loan_details_foreclosure
**Lineage (per hop: # column — rule [code])**
- 1. `port.basic_data_loan_foreclosure.target_referred_to_attorney_days` — NULL (not populated) [pool:174-188](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L174-188)
- 2. `bpms.sync_loan_foreclosure.target_referred_to_attorney_days` — GEN_FORECLOSURE: target_* commented out → NULL [asset:564-577](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L564-577)
- 3. `bpms.biz_data_view_loan_details_foreclosure.target_referred_to_attorney_days` — ifnull(target_referred_to_attorney_days, <default>) — view default constant [view]

**Note:** Stored NULL in sync; the view supplies the default target (e.g. first_legal 120, service 90, judgement 30).

### 30. Target for referred to foreclosure  (`bpms.sync_loan_foreclosure.target_referred_to_foreclosure_days`)

_Target days for the milestone (config constant)._

> ⚠ view_default

**Source (L1)**
- Newrez: `port.basic_data_loan_foreclosure.target_referred_to_foreclosure_days`  (Newrez-only detail)

**Flow:** ①basic_data_loan_foreclosure → ②sync_loan_foreclosure → ③biz_data_view_loan_details_foreclosure
**Lineage (per hop: # column — rule [code])**
- 1. `port.basic_data_loan_foreclosure.target_referred_to_foreclosure_days` — NULL (not populated) [pool:174-188](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L174-188)
- 2. `bpms.sync_loan_foreclosure.target_referred_to_foreclosure_days` — GEN_FORECLOSURE: target_* commented out → NULL [asset:564-577](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L564-577)
- 3. `bpms.biz_data_view_loan_details_foreclosure.target_referred_to_foreclosure_days` — ifnull(target_referred_to_foreclosure_days, <default>) — view default constant [view]

**Note:** Stored NULL in sync; the view supplies the default target (e.g. first_legal 120, service 90, judgement 30).

### 31. Target title report was received  (`bpms.sync_loan_foreclosure.target_title_report_received_days`)

_Target days for the milestone (config constant)._

> ⚠ view_default

**Source (L1)**
- Newrez: `port.basic_data_loan_foreclosure.target_title_report_received_days`  (Newrez-only detail)

**Flow:** ①basic_data_loan_foreclosure → ②sync_loan_foreclosure → ③biz_data_view_loan_details_foreclosure
**Lineage (per hop: # column — rule [code])**
- 1. `port.basic_data_loan_foreclosure.target_title_report_received_days` — NULL (not populated) [pool:174-188](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L174-188)
- 2. `bpms.sync_loan_foreclosure.target_title_report_received_days` — GEN_FORECLOSURE: target_* commented out → NULL [asset:564-577](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L564-577)
- 3. `bpms.biz_data_view_loan_details_foreclosure.target_title_report_received_days` — ifnull(target_title_report_received_days, <default>) — view default constant [view]

**Note:** Stored NULL in sync; the view supplies the default target (e.g. first_legal 120, service 90, judgement 30).

### 32. Target preliminary title was cleared  (`bpms.sync_loan_foreclosure.target_preliminary_title_cleared_days`)

_Target days for the milestone (config constant)._

> ⚠ view_default

**Source (L1)**
- Newrez: `port.basic_data_loan_foreclosure.target_preliminary_title_cleared_days`  (Newrez-only detail)

**Flow:** ①basic_data_loan_foreclosure → ②sync_loan_foreclosure → ③biz_data_view_loan_details_foreclosure
**Lineage (per hop: # column — rule [code])**
- 1. `port.basic_data_loan_foreclosure.target_preliminary_title_cleared_days` — NULL (not populated) [pool:174-188](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L174-188)
- 2. `bpms.sync_loan_foreclosure.target_preliminary_title_cleared_days` — GEN_FORECLOSURE: target_* commented out → NULL [asset:564-577](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L564-577)
- 3. `bpms.biz_data_view_loan_details_foreclosure.target_preliminary_title_cleared_days` — ifnull(target_preliminary_title_cleared_days, <default>) — view default constant [view]

**Note:** Stored NULL in sync; the view supplies the default target (e.g. first_legal 120, service 90, judgement 30).

### 33. Target of first legal action  (`bpms.sync_loan_foreclosure.target_first_legal_days`)

_Target days for the milestone (config constant)._

> ⚠ view_default

**Source (L1)**
- Newrez: `port.basic_data_loan_foreclosure.target_first_legal_days`  (Newrez-only detail)

**Flow:** ①basic_data_loan_foreclosure → ②sync_loan_foreclosure → ③biz_data_view_loan_details_foreclosure
**Lineage (per hop: # column — rule [code])**
- 1. `port.basic_data_loan_foreclosure.target_first_legal_days` — NULL (not populated) [pool:174-188](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L174-188)
- 2. `bpms.sync_loan_foreclosure.target_first_legal_days` — GEN_FORECLOSURE: target_* commented out → NULL [asset:564-577](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L564-577)
- 3. `bpms.biz_data_view_loan_details_foreclosure.target_first_legal_days` — ifnull(target_first_legal_days, <default>) — view default constant [view]

**Note:** Stored NULL in sync; the view supplies the default target (e.g. first_legal 120, service 90, judgement 30).

### 34. Target of service completion date  (`bpms.sync_loan_foreclosure.target_service_days`)

_Target days for the milestone (config constant)._

> ⚠ view_default

**Source (L1)**
- Newrez: `port.basic_data_loan_foreclosure.target_service_days`  (Newrez-only detail)

**Flow:** ①basic_data_loan_foreclosure → ②sync_loan_foreclosure → ③biz_data_view_loan_details_foreclosure
**Lineage (per hop: # column — rule [code])**
- 1. `port.basic_data_loan_foreclosure.target_service_days` — NULL (not populated) [pool:174-188](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L174-188)
- 2. `bpms.sync_loan_foreclosure.target_service_days` — GEN_FORECLOSURE: target_* commented out → NULL [asset:564-577](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L564-577)
- 3. `bpms.biz_data_view_loan_details_foreclosure.target_service_days` — ifnull(target_service_days, <default>) — view default constant [view]

**Note:** Stored NULL in sync; the view supplies the default target (e.g. first_legal 120, service 90, judgement 30).

### 35. Target of publication completion date  (`bpms.sync_loan_foreclosure.target_publication_days`)

_Target days for the milestone (config constant)._

> ⚠ view_default

**Source (L1)**
- Newrez: `port.basic_data_loan_foreclosure.target_publication_days`  (Newrez-only detail)

**Flow:** ①basic_data_loan_foreclosure → ②sync_loan_foreclosure → ③biz_data_view_loan_details_foreclosure
**Lineage (per hop: # column — rule [code])**
- 1. `port.basic_data_loan_foreclosure.target_publication_days` — NULL (not populated) [pool:174-188](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L174-188)
- 2. `bpms.sync_loan_foreclosure.target_publication_days` — GEN_FORECLOSURE: target_* commented out → NULL [asset:564-577](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L564-577)
- 3. `bpms.biz_data_view_loan_details_foreclosure.target_publication_days` — ifnull(target_publication_days, <default>) — view default constant [view]

**Note:** Stored NULL in sync; the view supplies the default target (e.g. first_legal 120, service 90, judgement 30).

### 36. Target of judgment hearing was set  (`bpms.sync_loan_foreclosure.target_judgement_hearing_set_days`)

_Target days for the milestone (config constant)._

> ⚠ view_default

**Source (L1)**
- Newrez: `port.basic_data_loan_foreclosure.target_judgement_hearing_set_days`  (Newrez-only detail)

**Flow:** ①basic_data_loan_foreclosure → ②sync_loan_foreclosure → ③biz_data_view_loan_details_foreclosure
**Lineage (per hop: # column — rule [code])**
- 1. `port.basic_data_loan_foreclosure.target_judgement_hearing_set_days` — NULL (not populated) [pool:174-188](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L174-188)
- 2. `bpms.sync_loan_foreclosure.target_judgement_hearing_set_days` — GEN_FORECLOSURE: target_* commented out → NULL [asset:564-577](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L564-577)
- 3. `bpms.biz_data_view_loan_details_foreclosure.target_judgement_hearing_set_days` — ifnull(target_judgement_hearing_set_days, <default>) — view default constant [view]

**Note:** Stored NULL in sync; the view supplies the default target (e.g. first_legal 120, service 90, judgement 30).

### 37. Target of judgment was issued  (`bpms.sync_loan_foreclosure.target_judgement_days`)

_Target days for the milestone (config constant)._

> ⚠ view_default

**Source (L1)**
- Newrez: `port.basic_data_loan_foreclosure.target_judgement_days`  (Newrez-only detail)

**Flow:** ①basic_data_loan_foreclosure → ②sync_loan_foreclosure → ③biz_data_view_loan_details_foreclosure
**Lineage (per hop: # column — rule [code])**
- 1. `port.basic_data_loan_foreclosure.target_judgement_days` — NULL (not populated) [pool:174-188](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L174-188)
- 2. `bpms.sync_loan_foreclosure.target_judgement_days` — GEN_FORECLOSURE: target_* commented out → NULL [asset:564-577](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L564-577)
- 3. `bpms.biz_data_view_loan_details_foreclosure.target_judgement_days` — ifnull(target_judgement_days, <default>) — view default constant [view]

**Note:** Stored NULL in sync; the view supplies the default target (e.g. first_legal 120, service 90, judgement 30).

### 38. Target of sale date set  (`bpms.sync_loan_foreclosure.target_sale_date_set_days`)

_Target days for the milestone (config constant)._

> ⚠ view_default

**Source (L1)**
- Newrez: `port.basic_data_loan_foreclosure.target_sale_date_set_days`  (Newrez-only detail)

**Flow:** ①basic_data_loan_foreclosure → ②sync_loan_foreclosure → ③biz_data_view_loan_details_foreclosure
**Lineage (per hop: # column — rule [code])**
- 1. `port.basic_data_loan_foreclosure.target_sale_date_set_days` — NULL (not populated) [pool:174-188](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L174-188)
- 2. `bpms.sync_loan_foreclosure.target_sale_date_set_days` — GEN_FORECLOSURE: target_* commented out → NULL [asset:564-577](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L564-577)
- 3. `bpms.biz_data_view_loan_details_foreclosure.target_sale_date_set_days` — ifnull(target_sale_date_set_days, <default>) — view default constant [view]

**Note:** Stored NULL in sync; the view supplies the default target (e.g. first_legal 120, service 90, judgement 30).

### 39. Target of final title was cleared  (`bpms.sync_loan_foreclosure.target_final_title_cleared_days`)

_Target days for the milestone (config constant)._

> ⚠ view_default

**Source (L1)**
- Newrez: `port.basic_data_loan_foreclosure.target_final_title_cleared_days`  (Newrez-only detail)

**Flow:** ①basic_data_loan_foreclosure → ②sync_loan_foreclosure → ③biz_data_view_loan_details_foreclosure
**Lineage (per hop: # column — rule [code])**
- 1. `port.basic_data_loan_foreclosure.target_final_title_cleared_days` — NULL (not populated) [pool:174-188](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L174-188)
- 2. `bpms.sync_loan_foreclosure.target_final_title_cleared_days` — GEN_FORECLOSURE: target_* commented out → NULL [asset:564-577](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L564-577)
- 3. `bpms.biz_data_view_loan_details_foreclosure.target_final_title_cleared_days` — ifnull(target_final_title_cleared_days, <default>) — view default constant [view]

**Note:** Stored NULL in sync; the view supplies the default target (e.g. first_legal 120, service 90, judgement 30).

### 40. Target of sale was held  (`bpms.sync_loan_foreclosure.target_sale_date_held_days`)

_Target days for the milestone (config constant)._

> ⚠ view_default

**Source (L1)**
- Newrez: `port.basic_data_loan_foreclosure.target_sale_date_held_days`  (Newrez-only detail)

**Flow:** ①basic_data_loan_foreclosure → ②sync_loan_foreclosure → ③biz_data_view_loan_details_foreclosure
**Lineage (per hop: # column — rule [code])**
- 1. `port.basic_data_loan_foreclosure.target_sale_date_held_days` — NULL (not populated) [pool:174-188](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L174-188)
- 2. `bpms.sync_loan_foreclosure.target_sale_date_held_days` — GEN_FORECLOSURE: target_* commented out → NULL [asset:564-577](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L564-577)
- 3. `bpms.biz_data_view_loan_details_foreclosure.target_sale_date_held_days` — ifnull(target_sale_date_held_days, <default>) — view default constant [view]

**Note:** Stored NULL in sync; the view supplies the default target (e.g. first_legal 120, service 90, judgement 30).


## Variance columns

### 41. Flag for active bankruptcy  (`bpms.sync_loan_foreclosure.variance_active_bankruptcy`)

_Defined in schema but not populated by the FCL ETL._

> ⚠ null_in_build

**Source (L1)**
- Newrez: `port.basic_data_loan_foreclosure.variance_active_bankruptcy`  (Newrez-only detail)

**Flow:** ①basic_data_loan_foreclosure → ②sync_loan_foreclosure → ③biz_data_view_loan_details_foreclosure
**Lineage (per hop: # column — rule [code])**
- 1. `port.basic_data_loan_foreclosure.variance_active_bankruptcy` — not in GEN_FCL_DETAIL INSERT → NULL 未填充 [pool:148-305](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L148-305)
- 2. `bpms.sync_loan_foreclosure.variance_active_bankruptcy` — GEN_FORECLOSURE 直传（值=NULL） [asset:540-605](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L540-605)
- 3. `bpms.biz_data_view_loan_details_foreclosure.variance_active_bankruptcy` — passthrough [view]

### 42. Flag for completed bankruptcy  (`bpms.sync_loan_foreclosure.variance_completed_bankruptcy`)

_Defined in schema but not populated by the FCL ETL._

> ⚠ null_in_build

**Source (L1)**
- Newrez: `port.basic_data_loan_foreclosure.variance_completed_bankruptcy`  (Newrez-only detail)

**Flow:** ①basic_data_loan_foreclosure → ②sync_loan_foreclosure → ③biz_data_view_loan_details_foreclosure
**Lineage (per hop: # column — rule [code])**
- 1. `port.basic_data_loan_foreclosure.variance_completed_bankruptcy` — not in GEN_FCL_DETAIL INSERT → NULL 未填充 [pool:148-305](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L148-305)
- 2. `bpms.sync_loan_foreclosure.variance_completed_bankruptcy` — GEN_FORECLOSURE 直传（值=NULL） [asset:540-605](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L540-605)
- 3. `bpms.biz_data_view_loan_details_foreclosure.variance_completed_bankruptcy` — passthrough [view]

### 43. Estimated hold days for the process  (`bpms.sync_loan_foreclosure.variance_estimated_hold_days`)

_Defined in schema but not populated by the FCL ETL._

> ⚠ null_in_build

**Source (L1)**
- Newrez: `port.basic_data_loan_foreclosure.variance_estimated_hold_days`  (Newrez-only detail)

**Flow:** ①basic_data_loan_foreclosure → ②sync_loan_foreclosure → ③biz_data_view_loan_details_foreclosure
**Lineage (per hop: # column — rule [code])**
- 1. `port.basic_data_loan_foreclosure.variance_estimated_hold_days` — not in GEN_FCL_DETAIL INSERT → NULL 未填充 [pool:148-305](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L148-305)
- 2. `bpms.sync_loan_foreclosure.variance_estimated_hold_days` — GEN_FORECLOSURE 直传（值=NULL） [asset:540-605](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L540-605)
- 3. `bpms.biz_data_view_loan_details_foreclosure.variance_estimated_hold_days` — passthrough [view]

### 44. Total number of bankruptcies  (`bpms.sync_loan_foreclosure.variance_bankruptcies`)

_Defined in schema but not populated by the FCL ETL._

> ⚠ null_in_build

**Source (L1)**
- Newrez: `port.basic_data_loan_foreclosure.variance_bankruptcies`  (Newrez-only detail)

**Flow:** ①basic_data_loan_foreclosure → ②sync_loan_foreclosure → ③biz_data_view_loan_details_foreclosure
**Lineage (per hop: # column — rule [code])**
- 1. `port.basic_data_loan_foreclosure.variance_bankruptcies` — not in GEN_FCL_DETAIL INSERT → NULL 未填充 [pool:148-305](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L148-305)
- 2. `bpms.sync_loan_foreclosure.variance_bankruptcies` — GEN_FORECLOSURE 直传（值=NULL） [asset:540-605](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L540-605)
- 3. `bpms.biz_data_view_loan_details_foreclosure.variance_bankruptcies` — passthrough [view]


## Bid approval columns

### 45. Approval Status  (`bpms.sync_loan_foreclosure.bid_approval_status`)

_Defined in schema but not populated by the FCL ETL._

> ⚠ null_in_build

**Source (L1)**
- Newrez: `port.basic_data_loan_foreclosure.bid_approval_status`  (Newrez-only detail)

**Flow:** ①basic_data_loan_foreclosure → ②sync_loan_foreclosure → ③biz_data_view_loan_details_foreclosure
**Lineage (per hop: # column — rule [code])**
- 1. `port.basic_data_loan_foreclosure.bid_approval_status` — not in GEN_FCL_DETAIL INSERT → NULL 未填充 [pool:148-305](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L148-305)
- 2. `bpms.sync_loan_foreclosure.bid_approval_status` — GEN_FORECLOSURE 直传（值=NULL） [asset:540-605](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L540-605)
- 3. `bpms.biz_data_view_loan_details_foreclosure.bid_approval_status` — passthrough [view]

### 46. Sale Date  (`bpms.sync_loan_foreclosure.bid_approval_sale_date`)

_Defined in schema but not populated by the FCL ETL._

> ⚠ null_in_build

**Source (L1)**
- Newrez: `port.basic_data_loan_foreclosure.bid_approval_sale_date`  (Newrez-only detail)

**Flow:** ①basic_data_loan_foreclosure → ②sync_loan_foreclosure → ③biz_data_view_loan_details_foreclosure
**Lineage (per hop: # column — rule [code])**
- 1. `port.basic_data_loan_foreclosure.bid_approval_sale_date` — not in GEN_FCL_DETAIL INSERT → NULL 未填充 [pool:148-305](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L148-305)
- 2. `bpms.sync_loan_foreclosure.bid_approval_sale_date` — GEN_FORECLOSURE 直传（值=NULL） [asset:540-605](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L540-605)
- 3. `bpms.biz_data_view_loan_details_foreclosure.bid_approval_sale_date` — passthrough [view]

### 47. Bid Amount  (`bpms.sync_loan_foreclosure.bid_approval_bid_amount`)

_Foreclosure bid amount (same raw as summary_foreclosure_bid_amount)._

**Source (L1)**
- Newrez: `newrez.portnewrezfc.fcbidamount`  (Newrez-only detail)

**Flow:** ①portnewrezfc → ②basic_data_loan_fcl → ③basic_data_loan_foreclosure → ④sync_loan_foreclosure → ⑤biz_data_view_loan_details_foreclosure
**Lineage (per hop: # column — rule [code])**
- 1. `newrez.portnewrezfc.fcbidamount` — servicer raw
- 2. `port.basic_data_loan_fcl.fcbidamount` — rename
- 3. `port.basic_data_loan_foreclosure.bid_approval_bid_amount` — = fcbidamount [pool:272](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L272)
- 4. `bpms.sync_loan_foreclosure.bid_approval_bid_amount` — passthrough [asset]
- 5. `bpms.biz_data_view_loan_details_foreclosure.bid_approval_bid_amount` — passthrough [view]

### 48. Loan Resolution Holds  (`bpms.sync_loan_foreclosure.bid_approval_loan_resolution_holods`)

_Defined in schema but not populated by the FCL ETL._

> ⚠ null_in_build

**Source (L1)**
- Newrez: `port.basic_data_loan_foreclosure.bid_approval_loan_resolution_holods`  (Newrez-only detail)

**Flow:** ①basic_data_loan_foreclosure → ②sync_loan_foreclosure → ③biz_data_view_loan_details_foreclosure
**Lineage (per hop: # column — rule [code])**
- 1. `port.basic_data_loan_foreclosure.bid_approval_loan_resolution_holods` — not in GEN_FCL_DETAIL INSERT → NULL 未填充 [pool:148-305](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L148-305)
- 2. `bpms.sync_loan_foreclosure.bid_approval_loan_resolution_holods` — GEN_FORECLOSURE 直传（值=NULL） [asset:540-605](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L540-605)
- 3. `bpms.biz_data_view_loan_details_foreclosure.bid_approval_loan_resolution_holods` — passthrough [view]


## Summary / status

### 49. Servicer number identifier  (`bpms.sync_loan_foreclosure.summary_servicer_number`)

_Defined in schema but not populated by the FCL ETL._

> ⚠ null_in_build

**Source (L1)**
- Newrez: `port.basic_data_loan_foreclosure.summary_servicer_number`  (Newrez-only detail)

**Flow:** ①basic_data_loan_foreclosure → ②sync_loan_foreclosure → ③biz_data_view_loan_details_foreclosure
**Lineage (per hop: # column — rule [code])**
- 1. `port.basic_data_loan_foreclosure.summary_servicer_number` — not in GEN_FCL_DETAIL INSERT → NULL 未填充 [pool:148-305](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L148-305)
- 2. `bpms.sync_loan_foreclosure.summary_servicer_number` — GEN_FORECLOSURE 直传（值=NULL） [asset:540-605](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L540-605)
- 3. `bpms.biz_data_view_loan_details_foreclosure.summary_servicer_number` — passthrough [view]

### 50. Foreclosure Status  (`bpms.sync_loan_foreclosure.summary_foreclosure_status`)

_Active vs Closed (+reason)._

**Source (L1)**
- Newrez: `newrez.portnewrezfc.activefcflag + fcremovaldesc`
- Carrington: `carrington.portcarrington.fcl_flag`
- Capecodfive: `capecodfive.portcapecodfive_monthly_collections.foreclosure_flag`

**Flow:** ①basic_data_loan_fcl → ②basic_data_loan_foreclosure → ③sync_loan_foreclosure → ④biz_data_view_loan_details_foreclosure
**Lineage (per hop: # column — rule [code])**
- 1. `port.basic_data_loan_fcl` · activefcflag, fcremovaldesc — activefcflag=cast(int); fcremovaldesc rename [pool:1538,1563](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L1538)
- 2. `port.basic_data_loan_foreclosure.summary_foreclosure_status` — CASE active/closed 见 sql [pool:273](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L273)
- 3. `bpms.sync_loan_foreclosure.summary_foreclosure_status` — upsert pass-through [asset:730/780](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L730)
- 4. `bpms.biz_data_view_loan_details_foreclosure.summary_foreclosure_status` — passthrough [view]

**Rule (full):** Inputs are built per servicer, then a shared CASE produces the text. **Newrez**: `activefcflag` (0/1) and `fcremovaldesc` taken directly. **Carrington**: no `activefcflag` column → `activefcflag = CASE WHEN fcl_flag='Active' THEN 1 ELSE NULL` ([pool:1579](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L1579)); `fcremovaldesc` is NULL. **Capecodfive**: `activefcflag = CASE WHEN foreclosure_flag='Active' THEN 1 ELSE NULL` ([pool:1620](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L1620)). **Shared rule**: `CASE WHEN activefcflag=1 THEN 'Active Foreclosure' WHEN activefcflag=0 AND fcremovaldesc<>'' THEN CONCAT('Closed Foreclosure:',fcremovaldesc) ELSE NULL` ([pool:273](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L273)).

```sql
CASE WHEN activefcflag=1 THEN 'Active Foreclosure' WHEN activefcflag=0 AND fcremovaldesc IS NOT NULL AND fcremovaldesc!='' THEN CONCAT('Closed Foreclosure:', fcremovaldesc) ELSE null END
```
🔎 **How it works:** activefcflag=1 ⇒ fixed text 'Active Foreclosure'. activefcflag=0 AND fcremovaldesc non-empty ⇒ 'Closed Foreclosure:'+fcremovaldesc (the exit reason). Otherwise NULL. (Note: the closed text uses fcremovaldesc, NOT fcstage.)
▶ **Example:** 7727004408: activefcflag=1 ⇒ 'Active Foreclosure'. A closed loan with activefcflag=0, fcremovaldesc='Paid in Full' ⇒ 'Closed Foreclosure:Paid in Full'.

### 51. Flag for completed foreclosure  (`bpms.sync_loan_foreclosure.summary_completed_foreclosure`)

_Defined in schema but not populated by the FCL ETL._

> ⚠ null_in_build

**Source (L1)**
- Newrez: `port.basic_data_loan_foreclosure.summary_completed_foreclosure`  (Newrez-only detail)

**Flow:** ①basic_data_loan_foreclosure → ②sync_loan_foreclosure → ③biz_data_view_loan_details_foreclosure
**Lineage (per hop: # column — rule [code])**
- 1. `port.basic_data_loan_foreclosure.summary_completed_foreclosure` — not in GEN_FCL_DETAIL INSERT → NULL 未填充 [pool:148-305](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L148-305)
- 2. `bpms.sync_loan_foreclosure.summary_completed_foreclosure` — GEN_FORECLOSURE 直传（值=NULL） [asset:540-605](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L540-605)
- 3. `bpms.biz_data_view_loan_details_foreclosure.summary_completed_foreclosure` — passthrough [view]

### 52. Foreclosure Bid Amount  (`bpms.sync_loan_foreclosure.summary_foreclosure_bid_amount`)

_FCL bid amount._

**Source (L1)**
- Newrez: `newrez.portnewrezfc.fcbidamount`
- Carrington: —
- Capecodfive: —

**Flow:** ①basic_data_loan_fcl → ②basic_data_loan_foreclosure → ③sync_loan_foreclosure → ④biz_data_view_loan_details_foreclosure
**Lineage (per hop: # column — rule [code])**
- 1. `port.basic_data_loan_fcl.fcbidamount` — rename 改名 [pool:1555](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L1555)
- 2. `port.basic_data_loan_foreclosure.summary_foreclosure_bid_amount` — direct copy 直传 [pool:274](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L274)
- 3. `bpms.sync_loan_foreclosure.summary_foreclosure_bid_amount` — upsert pass-through [asset:733/782](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L733)
- 4. `bpms.biz_data_view_loan_details_foreclosure.summary_foreclosure_bid_amount` — passthrough [view]

**Note:** Same raw fcbidamount also feeds bid_approval_bid_amount & summary_srv_fc_bid_amount.

### 53. Servicer foreclosure bid amount  (`bpms.sync_loan_foreclosure.summary_srv_fc_bid_amount`)

_Foreclosure bid amount (same raw as summary_foreclosure_bid_amount)._

**Source (L1)**
- Newrez: `newrez.portnewrezfc.fcbidamount`  (Newrez-only detail)

**Flow:** ①portnewrezfc → ②basic_data_loan_fcl → ③basic_data_loan_foreclosure → ④sync_loan_foreclosure → ⑤biz_data_view_loan_details_foreclosure
**Lineage (per hop: # column — rule [code])**
- 1. `newrez.portnewrezfc.fcbidamount` — servicer raw
- 2. `port.basic_data_loan_fcl.fcbidamount` — rename
- 3. `port.basic_data_loan_foreclosure.summary_srv_fc_bid_amount` — = fcbidamount [pool:275](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L275)
- 4. `bpms.sync_loan_foreclosure.summary_srv_fc_bid_amount` — passthrough [asset]
- 5. `bpms.biz_data_view_loan_details_foreclosure.summary_srv_fc_bid_amount` — passthrough [view]

### 54. Foreclosure Sale Amount  (`bpms.sync_loan_foreclosure.summary_foreclosure_sale_amount`)

_FCL sale amount._

**Source (L1)**
- Newrez: `newrez.portnewrezfc.fcsaleamount`
- Carrington: —
- Capecodfive: —

**Flow:** ①basic_data_loan_fcl → ②basic_data_loan_foreclosure → ③sync_loan_foreclosure → ④biz_data_view_loan_details_foreclosure
**Lineage (per hop: # column — rule [code])**
- 1. `port.basic_data_loan_fcl.fcsaleamount` — rename 改名 [pool:1557](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L1557)
- 2. `port.basic_data_loan_foreclosure.summary_foreclosure_sale_amount` — direct copy 直传 [pool:276](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L276)
- 3. `bpms.sync_loan_foreclosure.summary_foreclosure_sale_amount` — upsert pass-through [asset:734/784](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L734)
- 4. `bpms.biz_data_view_loan_details_foreclosure.summary_foreclosure_sale_amount` — passthrough [view]

### 55. Judicial Foreclosure (flag)  (`bpms.sync_loan_foreclosure.summary_judicial_foreclosure`)

_Numeric judicial flag._

**Source (L1)**
- Newrez: `newrez.portnewrezfc.judicial`
- Carrington: —
- Capecodfive: —

**Flow:** ①basic_data_loan_fcl → ②basic_data_loan_foreclosure → ③sync_loan_foreclosure → ④biz_data_view_loan_details_foreclosure
**Lineage (per hop: # column — rule [code])**
- 1. `port.basic_data_loan_fcl.judicial` — rename 改名 [pool:1565](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L1565)
- 2. `port.basic_data_loan_foreclosure.summary_judicial_foreclosure` — cast(empty→null else decimal) [pool:277](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L277)
- 3. `bpms.sync_loan_foreclosure.summary_judicial_foreclosure` — upsert pass-through [asset:735/785](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L735)
- 4. `bpms.biz_data_view_loan_details_foreclosure.summary_judicial_foreclosure` — passthrough [view]

### 56. Name of the foreclosure attorney  (`bpms.sync_loan_foreclosure.summary_foreclosure_attorney`)

_Defined in schema but not populated by the FCL ETL._

> ⚠ null_in_build

**Source (L1)**
- Newrez: `port.basic_data_loan_foreclosure.summary_foreclosure_attorney`  (Newrez-only detail)

**Flow:** ①basic_data_loan_foreclosure → ②sync_loan_foreclosure → ③biz_data_view_loan_details_foreclosure
**Lineage (per hop: # column — rule [code])**
- 1. `port.basic_data_loan_foreclosure.summary_foreclosure_attorney` — not in GEN_FCL_DETAIL INSERT → NULL 未填充 [pool:148-305](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L148-305)
- 2. `bpms.sync_loan_foreclosure.summary_foreclosure_attorney` — GEN_FORECLOSURE 直传（值=NULL） [asset:540-605](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L540-605)
- 3. `bpms.biz_data_view_loan_details_foreclosure.summary_foreclosure_attorney` — passthrough [view]

### 57. Contested / Litigation  (`bpms.sync_loan_foreclosure.summary_contested_litigation`)

_Contested litigation flag._

**Source (L1)**
- Newrez: `newrez.portnewrezfc.fccontestedflag`
- Carrington: —
- Capecodfive: —

**Flow:** ①basic_data_loan_fcl → ②basic_data_loan_foreclosure → ③sync_loan_foreclosure → ④biz_data_view_loan_details_foreclosure
**Lineage (per hop: # column — rule [code])**
- 1. `port.basic_data_loan_fcl.fccontestedflag` — rename 改名 [pool:1567](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L1567)
- 2. `port.basic_data_loan_foreclosure.summary_contested_litigation` — cast(empty→null else decimal) [pool:285](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L285)
- 3. `bpms.sync_loan_foreclosure.summary_contested_litigation` — upsert pass-through [asset:737/787](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L737)
- 4. `bpms.biz_data_view_loan_details_foreclosure.summary_contested_litigation` — passthrough [view]

### 58. Firm  (`bpms.sync_loan_foreclosure.summary_firm`)

_Foreclosure firm name._

**Source (L1)**
- Newrez: `newrez.portnewrezfc.fcfirm`
- Carrington: `carrington.portcarrington.fcl_attorney_name`
- Capecodfive: —

**Flow:** ①basic_data_loan_fcl → ②basic_data_loan_foreclosure → ③sync_loan_foreclosure → ④biz_data_view_loan_details_foreclosure
**Lineage (per hop: # column — rule [code])**
- 1. `port.basic_data_loan_fcl.fcfirm` — rename 改名 [pool:1566](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L1566)
- 2. `port.basic_data_loan_foreclosure.summary_firm` — direct copy 直传 [pool:278](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L278)
- 3. `bpms.sync_loan_foreclosure.summary_firm` — upsert pass-through [asset:738/789](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L738)
- 4. `bpms.biz_data_view_loan_details_foreclosure.summary_firm` — passthrough [view]

### 59. Type (Judicial / Non Judicial)  (`bpms.sync_loan_foreclosure.summary_type`)

_Judicial vs Non Judicial text._

**Source (L1)**
- Newrez: `newrez.portnewrezfc.judicial`
- Carrington: —
- Capecodfive: —

**Flow:** ①basic_data_loan_fcl → ②basic_data_loan_foreclosure → ③sync_loan_foreclosure → ④biz_data_view_loan_details_foreclosure
**Lineage (per hop: # column — rule [code])**
- 1. `port.basic_data_loan_fcl.judicial` — rename 改名 [pool:1565](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L1565)
- 2. `port.basic_data_loan_foreclosure.summary_type` — CASE 0→Non Judicial / 1→Judicial [pool:279](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L279)
- 3. `bpms.sync_loan_foreclosure.summary_type` — upsert pass-through [asset:739/790](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L739)
- 4. `bpms.biz_data_view_loan_details_foreclosure.summary_type` — passthrough [view]

```sql
CASE WHEN judicial IS NULL OR judicial='' THEN null WHEN cast(cast(judicial AS float) as int)=0 THEN 'Non Judicial' WHEN cast(cast(judicial AS float) as int)=1 THEN 'Judicial' ELSE null END
```
🔎 **How it works:** Normalize the judicial flag: NULL/blank ⇒ NULL; otherwise cast text→float→int, then 0 ⇒ 'Non Judicial', 1 ⇒ 'Judicial'.
▶ **Example:** judicial='1' ⇒ 'Judicial' (7727004408); '0' ⇒ 'Non Judicial'; '' ⇒ NULL.

### 60. SMS Days in Foreclosure  (`bpms.sync_loan_foreclosure.summary_sms_days_in_fcl`)

_Servicer-reported days in FCL (from servicer setup date)._

**Source (L1)**
- Newrez: `newrez.portnewrezfc.smsdaysinfc`
- Carrington: —
- Capecodfive: —

**Flow:** ①basic_data_loan_fcl → ②basic_data_loan_foreclosure → ③sync_loan_foreclosure → ④biz_data_view_loan_details_foreclosure
**Lineage (per hop: # column — rule [code])**
- 1. `port.basic_data_loan_fcl.svc_days_infc` — rename (smsdaysinfc→svc_days_infc) [pool:1545](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L1545)
- 2. `port.basic_data_loan_foreclosure.summary_sms_days_in_fcl` — direct copy 直传 [pool:280](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L280)
- 3. `bpms.sync_loan_foreclosure.summary_sms_days_in_fcl` — upsert pass-through [asset:740/791](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L740)
- 4. `bpms.biz_data_view_loan_details_foreclosure.summary_sms_days_in_fcl` — passthrough [view]

### 61. Days in Foreclosure  (`bpms.sync_loan_foreclosure.summary_days_in_fcl`)

_Days in FCL from referral (investor basis)._

**Source (L1)**
- Newrez: `newrez.portnewrezfc.daysinfc`
- Carrington: —
- Capecodfive: —

**Flow:** ①basic_data_loan_fcl → ②basic_data_loan_foreclosure → ③sync_loan_foreclosure → ④biz_data_view_loan_details_foreclosure
**Lineage (per hop: # column — rule [code])**
- 1. `port.basic_data_loan_fcl.daysinfc` — rename (Newrez) / computed (others) [pool:1546](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L1546)
- 2. `port.basic_data_loan_foreclosure.summary_days_in_fcl` — direct copy 直传 [pool:281](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L281)
- 3. `bpms.sync_loan_foreclosure.summary_days_in_fcl` — upsert pass-through [asset:741/792](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L741)
- 4. `bpms.biz_data_view_loan_details_foreclosure.summary_days_in_fcl` — passthrough [view]

**Rule (full):** **Newrez**: raw `daysinfc` passed through ([pool:1546](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L1546)). **Carrington / Capecodfive**: no raw `daysinfc` → computed `CASE WHEN <active> THEN datediff(day, referral_start_date, <snapshot>)+1 ELSE NULL` (Carrington uses snap_shot_date, [pool:1587](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L1587); Capecodfive uses dataasof, [pool:1628](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L1628)). Downstream the view shows the lag-corrected value; see the per-hop rule.

**Note:** Newrez = raw daysinfc passthrough; Carrington/Capecodfive computed.

### 62. Current Step  (`bpms.sync_loan_foreclosure.summary_current_step`)

_Current FCL stage text._

**Source (L1)**
- Newrez: `newrez.portnewrezfc.fcstage`
- Carrington: `carrington.portcarrington.fcl_sub_status`
- Capecodfive: —

**Flow:** ①basic_data_loan_fcl → ②basic_data_loan_foreclosure → ③sync_loan_foreclosure → ④biz_data_view_loan_details_foreclosure
**Lineage (per hop: # column — rule [code])**
- 1. `port.basic_data_loan_fcl.fcstage` — rename 改名 [pool:1560](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L1560)
- 2. `port.basic_data_loan_foreclosure.summary_current_step` — direct copy 直传 [pool:282](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L282)
- 3. `bpms.sync_loan_foreclosure.summary_current_step` — upsert pass-through [asset:742/793](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L742)
- 4. `bpms.biz_data_view_loan_details_foreclosure.summary_current_step` — passthrough [view]

### 63. Last Step Completed  (`bpms.sync_loan_foreclosure.summary_last_step_completed`)

_Last completed FCL step._

**Source (L1)**
- Newrez: `newrez.portnewrezfc.lastfcstepcompleted`
- Carrington: —
- Capecodfive: `capecodfive.portcapecodfive_monthly_collections.most_recent_foreclosure_stage`

**Flow:** ①basic_data_loan_fcl → ②basic_data_loan_foreclosure → ③sync_loan_foreclosure → ④biz_data_view_loan_details_foreclosure
**Lineage (per hop: # column — rule [code])**
- 1. `port.basic_data_loan_fcl.lastfcstepcompleted` — rename 改名 [pool:1561](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L1561)
- 2. `port.basic_data_loan_foreclosure.summary_last_step_completed` — direct copy 直传 [pool:283](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L283)
- 3. `bpms.sync_loan_foreclosure.summary_last_step_completed` — upsert pass-through [asset:743/794](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L743)
- 4. `bpms.biz_data_view_loan_details_foreclosure.summary_last_step_completed` — passthrough [view]

### 64. Last step completed date  (`bpms.sync_loan_foreclosure.summary_last_step_completed_date`)

_Date of last completed step._

**Source (L1)**
- Newrez: `newrez.portnewrezfc.lastfcstepcompleteddate`
- Carrington: —
- Capecodfive: —

**Flow:** ①basic_data_loan_fcl → ②basic_data_loan_foreclosure → ③sync_loan_foreclosure → ④biz_data_view_loan_details_foreclosure
**Lineage (per hop: # column — rule [code])**
- 1. `port.basic_data_loan_fcl.lastfcstepcompleteddate` — rename 改名 [pool:1562](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L1562)
- 2. `port.basic_data_loan_foreclosure.summary_last_step_completed_date` — direct copy 直传 [pool:284](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L284)
- 3. `bpms.sync_loan_foreclosure.summary_last_step_completed_date` — upsert pass-through [asset:744/795](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L744)
- 4. `bpms.biz_data_view_loan_details_foreclosure.summary_last_step_completed_date` — passthrough [view]


## System / audit columns

### 65. System / audit columns

_App/ETL-managed columns (not servicer-sourced)._

**Columns:** `create_user, create_dept, create_time, update_user, update_time, status, is_deleted, tenant_id`

**Note:** Columns: create_user, create_dept, create_time, update_user, update_time, status, is_deleted, tenant_id. tenant_id ← GET_LOAN_TENANT_ID(portfunding ⋈ basic_data_trust_funding, [asset:932-936](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L932-936)); create_*/update_* set by the BPS app; is_deleted constant 0 (view); status app flag. Not servicer data.


## View-computed columns

### 66. View-computed columns (Actual / Variance / Totals)

_The display view derives ~45 day-variance columns from the timeline dates + targets + nextduedate._

**Columns:** `actual_<stage>_days / var_<stage>_days / target_total / actual_total / var_total`

```sql
actual_<stage>_days = to_days(timeline_<stage>_date) - to_days(nextduedate);
var_<stage>_days   = actual_<stage>_days - (cumulative target days up to that stage);
target_total = Σ target_*; actual_total = Σ actual_*; var_total = Σ var_*
```
🔎 **How it works:** Per milestone the view computes actual days (from next-due date) and variance vs the cumulative target; plus row totals. Targets use ifnull(target_X, <default>).
▶ **Example:** e.g. actual_first_legal_days = to_days(timeline_first_legal_date) - to_days(nextduedate); var_first_legal_days = that - (Σ targets through first legal).


> This doc covers 66 fields.
