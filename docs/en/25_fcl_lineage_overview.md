# Doc 25 · Foreclosure field lineage · overview (hub)

> **Auto-generated** — to change, edit `outputs/fcl_lineage_source.json` and re-run `python - < scripts/gen_fcl_lineage.py`; do not hand-edit this file.


## Document Purpose

Hub for the **field-level** data lineage of core foreclosure fields, Servicer raw → BPS sync tables: the canonical hop-chain skeletons, a master field index, and links to the per-BPS-table detail docs (26–30). Rules are Code-First from PrefectFlow; columns schema-verified against prod (redshift_prod / mysql_prod). Complements doc 02 (table-level). Supersedes doc 21.

## Target Audience

data engineers · analysts · validators · business analysts · future AI sessions

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

## Related Documents

doc 02 (ETL pipeline) · doc 13 (BPS view field mapping) · doc 14 (Servicer FCL field spec) · doc 26–30 (per-table lineage) · ~~doc 21~~ (superseded)


---

## How to read this lineage

One detail doc per **BPS sync table** (doc 26–30). In each, **one row = one field**; columns are the field's column name at every table along its chain; the last column gives the **per-hop transform rule + code reference** (`pool`/`asset`/`view`, see below). Non-trivial transforms (CASE / decode / unpivot / day-math) include the real SQL.

> code: `pool` = PrefectFlow/flow/basic_data/basic_data_config/basic_data_pool_config.py · `asset` = PrefectFlow/flow/bps/bps_config/asset_managment_config.py · `view` = bpms.biz_data_view_loan_details_foreclosure (SHOW CREATE VIEW)

> The L4 fact (port.basic_data_loan_fcl) UNIONs 3 servicers — Newrez (newrez.portnewrezfc), Carrington (carrington.portcarrington), Capecodfive (capecodfive.portcapecodfive_monthly_collections). The 'raw' column shown is the Newrez source; Carrington/Capecodfive differences are in the per-field carrington note. SLS/MRC/etc. report no FCL detail (delinquency inference only).

> BPS stage snapshot fctrdt=2026-06-06; Newrez raw dataasof=2026-06-07


## Canonical hop-chain skeletons (4 branches)

### Main (milestones / summary / status)

**Canonical hop chain**


`newrez.portnewrezfc` → `tempfc.temp_basic_data_fcl` → `port.basic_data_loan_fcl` → `port.basic_data_loan_foreclosure` → `bpms.sync_loan_foreclosure` → `bpms.biz_data_view_loan_details_foreclosure`

| # | layer | db | table | role |
|---|---|---|---|---|
| 1 | L0/L1 | MySQL+Redshift | `newrez.portnewrezfc` | Servicer raw |
| 2 | L4·temp | Redshift | `tempfc.temp_basic_data_fcl` | 3-servicer rename-UNION of L1 raw / 三家 servicer 改名 UNION (CREATE_BASIC_FCL, pool:1531-1654) |
| 3 | L4 | Redshift | `port.basic_data_loan_fcl` | canonical FCL fact |
| 4 | L4 | Redshift→MySQL | `port.basic_data_loan_foreclosure` | timeline+summary build (GEN_FCL_DETAIL) |
| 5 | L5 | MySQL bpms | `bpms.sync_loan_foreclosure` | BPS app table (UPDATE_FORECLOSURE upsert) |
| 6 | L5 | MySQL bpms | `bpms.biz_data_view_loan_details_foreclosure` | display view (Actual/Var days) |

### Stage / days

**Canonical hop chain**


`newrez.portnewrezfc` → `tempfc.temp_basic_data_fcl` → `port.basic_data_loan_fcl` → `port.fcl_stage_info` → `bpms.sync_fcl_stage_info`

| # | layer | db | table | role |
|---|---|---|---|---|
| 1 | L0/L1 | MySQL+Redshift | `newrez.portnewrezfc` | Servicer raw |
| 2 | L4·temp | Redshift | `tempfc.temp_basic_data_fcl` | 3-servicer rename-UNION of L1 raw / 三家 servicer 改名 UNION (CREATE_BASIC_FCL, pool:1531-1654) |
| 3 | L4 | Redshift | `port.basic_data_loan_fcl` | canonical FCL fact |
| 4 | L4 | Redshift | `port.fcl_stage_info` | stage classification + day-math (GEN_FCL_STAGE); group/state from port.basic_data_fcl_related |
| 5 | L5 | MySQL bpms | `bpms.sync_fcl_stage_info` | BPS app table (12-FCL_STAGE sync, keeps fctrdt history) |

### Hold (wide→long unpivot)

**Canonical hop chain**


`newrez.portnewrezfc (fchold1..4 slots)` → `port.basic_data_loan_foreclosure_hold` → `bpms.sync_loan_foreclosure_hold`

| # | layer | db | table | role |
|---|---|---|---|---|
| 1 | L0/L1 | MySQL+Redshift | `newrez.portnewrezfc (fchold1..4 slots)` | Servicer raw |
| 2 | L4 | Redshift | `port.basic_data_loan_foreclosure_hold` | wide description1..3 (+ Carrington slot4); deduped roll-up of *_hold_detail |
| 3 | L5 | MySQL bpms | `bpms.sync_loan_foreclosure_hold` | long rows via UNION ALL unpivot (GEN_FORECLOSURE_HOLD) |

### Loss Mitigation (code→text decode)

**Canonical hop chain**


`newrez.portnewrezlm` → `port.basic_data_loan_foreclosure_loss_mitigation` → `bpms.sync_loan_foreclosure_loss_mitigation`

| # | layer | db | table | role |
|---|---|---|---|---|
| 1 | L0/L1 | MySQL+Redshift | `newrez.portnewrezlm` | Servicer raw (coded) |
| 2 | L4 | Redshift | `port.basic_data_loan_foreclosure_loss_mitigation` | datadic decode (COALESCE(desc, code)); dedup latest per loan+cycle |
| 3 | L5 | MySQL bpms | `bpms.sync_loan_foreclosure_loss_mitigation` | BPS app table (GEN_FORECLOSURE_LM pass-through) |

### Bankruptcy (code→text decode)

**Canonical hop chain**


`newrez.portnewrezbk (+ portnewrezgeneral.legalstatus)` → `port.basic_data_loan_foreclosure_bankruptcy` → `bpms.sync_loan_foreclosure_bankruptcy`

| # | layer | db | table | role |
|---|---|---|---|---|
| 1 | L0/L1 | MySQL+Redshift | `newrez.portnewrezbk (+ portnewrezgeneral.legalstatus)` | Servicer raw (coded) |
| 2 | L4 | Redshift | `port.basic_data_loan_foreclosure_bankruptcy` | datadic decode; dedup latest per loan+filing |
| 3 | L5 | MySQL bpms | `bpms.sync_loan_foreclosure_bankruptcy` | BPS app table (GEN_FORECLOSURE_BK pass-through) |

> The `#` column is a sequence number, not the layer number. The FCL fact `port.basic_data_loan_fcl` is built DIRECTLY from the L1 servicer raw tables (UNIONed in `tempfc.temp_basic_data_fcl`; CREATE_BASIC_FCL pool:1531-1654), so the L2 unified-daily (`port.basic_data_daily_loan_common`) and L3 clean (`…_clean` / `…_delinq_clean`) layers are NOT part of this branch by design — they carry the common + delinquency fields and re-enter only via the `group` dimension (doc 27, `basic_data_fcl_related`) and the monthly `portmonth` path. See doc 02 for the full L0–L5 pipeline.

> Datadic decode pattern (LM deal/program/status/decision/denial/borrower, BK status): COALESCE((SELECT description FROM newrez.portnewrezdatadic WHERE field_name='<X>' AND code=CONCAT(raw,'.0')), raw) — raw codes stored as '5.0'; falls back to the raw code if no dictionary row.


## Master field index

| Field | Servicer raw col | BPS sync table | final BPS col + detail doc |
|---|---|---|---|
| id (PK) | `id` | `sync_loan_foreclosure` | `id` (→ doc 26) |
| bid_id (deal id) | `dealid` | `sync_loan_foreclosure` | `bid_id` (→ doc 26) |
| funding_id | `fundingid` | `sync_loan_foreclosure` | `funding_id` (→ doc 26) |
| Investor loan id | `loanid` | `sync_loan_foreclosure` | `loanid` (→ doc 26) |
| Servicer loan id | `shellpointloanid` | `sync_loan_foreclosure` | `svcloanid` (→ doc 26) |
| servicer | `constant 'Newrez'/'Carrington'/'Capecodfive'` | `sync_loan_foreclosure` | `servicer` (→ doc 26) |
| Notice of Intent Date | `—` | `sync_loan_foreclosure` | `timeline_notice_of_intent_date` (→ doc 26) |
| End date of notice of intent | `timeline_notice_of_intent_end_date` | `sync_loan_foreclosure` | `timeline_notice_of_intent_end_date` (→ doc 26) |
| Approval for referral | `timeline_approved_for_referral_date` | `sync_loan_foreclosure` | `timeline_approved_for_referral_date` (→ doc 26) |
| Date referred to attorney | `timeline_referred_to_attorney_date` | `sync_loan_foreclosure` | `timeline_referred_to_attorney_date` (→ doc 26) |
| Referred to Foreclosure (Referral) | `fcreferraldate` | `sync_loan_foreclosure` | `timeline_referred_to_foreclosure_date` (→ doc 26) |
| Title Report Received | `titlereceiveddate` | `sync_loan_foreclosure` | `timeline_title_report_received_date` (→ doc 26) |
| Preliminary Title Cleared | `titlecleardate` | `sync_loan_foreclosure` | `timeline_preliminary_title_cleared_date` (→ doc 26) |
| 1st Legal | `firstlegaldate` | `sync_loan_foreclosure` | `timeline_first_legal_date` (→ doc 26) |
| Service Complete | `servicecompletedate` | `sync_loan_foreclosure` | `timeline_service_date` (→ doc 26) |
| Publication scheduled date | `timeline_publication_date` | `sync_loan_foreclosure` | `timeline_publication_date` (→ doc 26) |
| Judgement Hearing Set | `fcjudgmenthearingscheduled` | `sync_loan_foreclosure` | `timeline_judgement_hearing_set_date` (→ doc 26) |
| Judgement | `fcjudgmenthearingscheduled` | `sync_loan_foreclosure` | `timeline_judgement_date` (→ doc 26) |
| Sale Date Projected | `fcscheduledsaledate` | `sync_loan_foreclosure` | `timeline_sale_date_projected_date` (→ doc 26) |
| Sale Date Set | `fcscheduledsaledate` | `sync_loan_foreclosure` | `timeline_sale_date_set_date` (→ doc 26) |
| Final Title Cleared | `titlecleardate` | `sync_loan_foreclosure` | `timeline_final_title_cleared_date` (→ doc 26) |
| Sale Held | `fcsalehelddate` | `sync_loan_foreclosure` | `timeline_sale_date_held_date` (→ doc 26) |
| Date foreclosure was completed | `timeline_foreclosure_completed_date` | `sync_loan_foreclosure` | `timeline_foreclosure_completed_date` (→ doc 26) |
| 3rd Party Sold Date | `—` | `sync_loan_foreclosure` | `timeline_third_party_sold_date_date` (→ doc 26) |
| 3rd Party Proceeds Received | `fcl3rdpartyproceedsreceiveddate` | `sync_loan_foreclosure` | `timeline_third_party_proceeds_received_date` (→ doc 26) |
| Target for notice of intent | `target_notice_of_intent_days` | `sync_loan_foreclosure` | `target_notice_of_intent_days` (→ doc 26) |
| Target for notice of intent expiration | `target_notice_of_intent_expired_days` | `sync_loan_foreclosure` | `target_notice_of_intent_expired_days` (→ doc 26) |
| Target for approval for referral | `target_approved_for_referral_days` | `sync_loan_foreclosure` | `target_approved_for_referral_days` (→ doc 26) |
| Target for referred to attorney | `target_referred_to_attorney_days` | `sync_loan_foreclosure` | `target_referred_to_attorney_days` (→ doc 26) |
| Target for referred to foreclosure | `target_referred_to_foreclosure_days` | `sync_loan_foreclosure` | `target_referred_to_foreclosure_days` (→ doc 26) |
| Target title report was received | `target_title_report_received_days` | `sync_loan_foreclosure` | `target_title_report_received_days` (→ doc 26) |
| Target preliminary title was cleared | `target_preliminary_title_cleared_days` | `sync_loan_foreclosure` | `target_preliminary_title_cleared_days` (→ doc 26) |
| Target of first legal action | `target_first_legal_days` | `sync_loan_foreclosure` | `target_first_legal_days` (→ doc 26) |
| Target of service completion date | `target_service_days` | `sync_loan_foreclosure` | `target_service_days` (→ doc 26) |
| Target of publication completion date | `target_publication_days` | `sync_loan_foreclosure` | `target_publication_days` (→ doc 26) |
| Target of judgment hearing was set | `target_judgement_hearing_set_days` | `sync_loan_foreclosure` | `target_judgement_hearing_set_days` (→ doc 26) |
| Target of judgment was issued | `target_judgement_days` | `sync_loan_foreclosure` | `target_judgement_days` (→ doc 26) |
| Target of sale date set | `target_sale_date_set_days` | `sync_loan_foreclosure` | `target_sale_date_set_days` (→ doc 26) |
| Target of final title was cleared | `target_final_title_cleared_days` | `sync_loan_foreclosure` | `target_final_title_cleared_days` (→ doc 26) |
| Target of sale was held | `target_sale_date_held_days` | `sync_loan_foreclosure` | `target_sale_date_held_days` (→ doc 26) |
| Flag for active bankruptcy | `variance_active_bankruptcy` | `sync_loan_foreclosure` | `variance_active_bankruptcy` (→ doc 26) |
| Flag for completed bankruptcy | `variance_completed_bankruptcy` | `sync_loan_foreclosure` | `variance_completed_bankruptcy` (→ doc 26) |
| Estimated hold days for the process | `variance_estimated_hold_days` | `sync_loan_foreclosure` | `variance_estimated_hold_days` (→ doc 26) |
| Total number of bankruptcies | `variance_bankruptcies` | `sync_loan_foreclosure` | `variance_bankruptcies` (→ doc 26) |
| Approval Status | `bid_approval_status` | `sync_loan_foreclosure` | `bid_approval_status` (→ doc 26) |
| Sale Date | `bid_approval_sale_date` | `sync_loan_foreclosure` | `bid_approval_sale_date` (→ doc 26) |
| Bid Amount | `fcbidamount` | `sync_loan_foreclosure` | `bid_approval_bid_amount` (→ doc 26) |
| Loan Resolution Holds | `bid_approval_loan_resolution_holods` | `sync_loan_foreclosure` | `bid_approval_loan_resolution_holods` (→ doc 26) |
| Servicer number identifier | `summary_servicer_number` | `sync_loan_foreclosure` | `summary_servicer_number` (→ doc 26) |
| Foreclosure Status | `activefcflag + fcremovaldesc` | `sync_loan_foreclosure` | `summary_foreclosure_status` (→ doc 26) |
| Flag for completed foreclosure | `summary_completed_foreclosure` | `sync_loan_foreclosure` | `summary_completed_foreclosure` (→ doc 26) |
| Foreclosure Bid Amount | `fcbidamount` | `sync_loan_foreclosure` | `summary_foreclosure_bid_amount` (→ doc 26) |
| Servicer foreclosure bid amount | `fcbidamount` | `sync_loan_foreclosure` | `summary_srv_fc_bid_amount` (→ doc 26) |
| Foreclosure Sale Amount | `fcsaleamount` | `sync_loan_foreclosure` | `summary_foreclosure_sale_amount` (→ doc 26) |
| Judicial Foreclosure (flag) | `judicial` | `sync_loan_foreclosure` | `summary_judicial_foreclosure` (→ doc 26) |
| Name of the foreclosure attorney | `summary_foreclosure_attorney` | `sync_loan_foreclosure` | `summary_foreclosure_attorney` (→ doc 26) |
| Contested / Litigation | `fccontestedflag` | `sync_loan_foreclosure` | `summary_contested_litigation` (→ doc 26) |
| Firm | `fcfirm` | `sync_loan_foreclosure` | `summary_firm` (→ doc 26) |
| Type (Judicial / Non Judicial) | `judicial` | `sync_loan_foreclosure` | `summary_type` (→ doc 26) |
| SMS Days in Foreclosure | `smsdaysinfc` | `sync_loan_foreclosure` | `summary_sms_days_in_fcl` (→ doc 26) |
| Days in Foreclosure | `daysinfc` | `sync_loan_foreclosure` | `summary_days_in_fcl` (→ doc 26) |
| Current Step | `fcstage` | `sync_loan_foreclosure` | `summary_current_step` (→ doc 26) |
| Last Step Completed | `lastfcstepcompleted` | `sync_loan_foreclosure` | `summary_last_step_completed` (→ doc 26) |
| Last step completed date | `lastfcstepcompleteddate` | `sync_loan_foreclosure` | `summary_last_step_completed_date` (→ doc 26) |
| System / audit columns | `create_user, create_dept, create_time, update_user, update_time, status, is_deleted, tenant_id` | `sync_loan_foreclosure` | `create_user, create_dept, create_time, update_user, update_time, status, is_deleted, tenant_id` (→ doc 26) |
| id (PK) | `id` | `sync_fcl_stage_info` | `id` (→ doc 27) |
| stage (current bucket) | `(stage dates)` | `sync_fcl_stage_info` | `stage` (→ doc 27) |
| fctrdt | `dataasof` | `sync_fcl_stage_info` | `fctrdt` (→ doc 27) |
| Investor loan id | `loanid` | `sync_fcl_stage_info` | `loanid` (→ doc 27) |
| Group (FCL/D120P/D90/REO/P…) | `delinquency_status_mba (+ portnewrezpmt.nextduedate)` | `sync_fcl_stage_info` | `group` (→ doc 27) |
| servicer | `constant 'Newrez'/'Carrington'/'Capecodfive'` | `sync_fcl_stage_info` | `servicer` (→ doc 27) |
| State | `propertystate` | `sync_fcl_stage_info` | `state` (→ doc 27) |
| Judicial (Y/N) | `judicial (+ propertystate)` | `sync_fcl_stage_info` | `judicial` (→ doc 27) |
| Demand start date | `demandsentdate` | `sync_fcl_stage_info` | `demand_start_date` (→ doc 27) |
| Demand window end | `—` | `sync_fcl_stage_info` | `demand_end_date` (→ doc 27) |
| Demand days in stage | `—` | `sync_fcl_stage_info` | `demand_stage_days` (→ doc 27) |
| Demand days in LM | `—` | `sync_fcl_stage_info` | `demand_in_lm_days` (→ doc 27) |
| Demand days on hold | `—` | `sync_fcl_stage_info` | `demand_on_hold_days` (→ doc 27) |
| NOI start date | `noi_start_date` | `sync_fcl_stage_info` | `noi_start_date` (→ doc 27) |
| NOI window end | `—` | `sync_fcl_stage_info` | `noi_end_date` (→ doc 27) |
| NOI days in stage | `noi_stage_days` | `sync_fcl_stage_info` | `noi_stage_days` (→ doc 27) |
| NOI days in LM | `—` | `sync_fcl_stage_info` | `noi_in_lm_days` (→ doc 27) |
| NOI days on hold | `—` | `sync_fcl_stage_info` | `noi_on_hold_days` (→ doc 27) |
| Referral start date | `fcreferraldate` | `sync_fcl_stage_info` | `referral_start_date` (→ doc 27) |
| Referral window end | `—` | `sync_fcl_stage_info` | `referral_end_date` (→ doc 27) |
| Referral days in stage | `—` | `sync_fcl_stage_info` | `referral_stage_days` (→ doc 27) |
| Referral days in LM | `—` | `sync_fcl_stage_info` | `referral_in_lm_days` (→ doc 27) |
| Referral days on hold | `—` | `sync_fcl_stage_info` | `referral_on_hold_days` (→ doc 27) |
| First Legal start date | `firstlegaldate` | `sync_fcl_stage_info` | `first_legal_start_date` (→ doc 27) |
| First Legal window end | `—` | `sync_fcl_stage_info` | `first_legal_end_date` (→ doc 27) |
| First Legal days in stage | `—` | `sync_fcl_stage_info` | `first_legal_stage_days` (→ doc 27) |
| First Legal days in LM | `—` | `sync_fcl_stage_info` | `first_legal_in_lm_days` (→ doc 27) |
| First Legal days on hold | `—` | `sync_fcl_stage_info` | `first_legal_on_hold_days` (→ doc 27) |
| First-legal first-seen date | `firstlegaldate` | `sync_fcl_stage_info` | `first_legal_date_history` (→ doc 27) |
| Service start date | `servicecompletedate` | `sync_fcl_stage_info` | `service_start_date` (→ doc 27) |
| Service window end | `—` | `sync_fcl_stage_info` | `service_end_date` (→ doc 27) |
| Service days in stage | `—` | `sync_fcl_stage_info` | `service_stage_days` (→ doc 27) |
| Service days in LM | `—` | `sync_fcl_stage_info` | `service_in_lm_days` (→ doc 27) |
| Service days on hold | `—` | `sync_fcl_stage_info` | `service_on_hold_days` (→ doc 27) |
| Publication start date | `publication_start_date` | `sync_fcl_stage_info` | `publication_start_date` (→ doc 27) |
| Publication window end | `—` | `sync_fcl_stage_info` | `publication_end_date` (→ doc 27) |
| Publication days in stage | `publication_stage_days` | `sync_fcl_stage_info` | `publication_stage_days` (→ doc 27) |
| Publication days in LM | `—` | `sync_fcl_stage_info` | `publication_in_lm_days` (→ doc 27) |
| Publication days on hold | `—` | `sync_fcl_stage_info` | `publication_on_hold_days` (→ doc 27) |
| Judgement start date | `fcjudgmenthearingscheduled` | `sync_fcl_stage_info` | `judgement_start_date` (→ doc 27) |
| Judgement window end | `—` | `sync_fcl_stage_info` | `judgement_end_date` (→ doc 27) |
| Days to judgement | `fcjudgmenthearingscheduled` | `sync_fcl_stage_info` | `to_judgement_days` (→ doc 27) |
| Judgement days in LM | `—` | `sync_fcl_stage_info` | `judgement_in_lm_days` (→ doc 27) |
| Judgement days on hold | `—` | `sync_fcl_stage_info` | `judgement_on_hold_days` (→ doc 27) |
| Sale start date | `fcscheduledsaledate` | `sync_fcl_stage_info` | `sale_start_date` (→ doc 27) |
| Sale window end | `—` | `sync_fcl_stage_info` | `sale_end_date` (→ doc 27) |
| Days to sale | `fcscheduledsaledate` | `sync_fcl_stage_info` | `to_sale_days` (→ doc 27) |
| Sale days in LM | `—` | `sync_fcl_stage_info` | `sale_in_lm_days` (→ doc 27) |
| Sale days on hold | `—` | `sync_fcl_stage_info` | `sale_on_hold_days` (→ doc 27) |
| System / audit columns | `create_time, update_time, create_user, create_dept, update_user, status, is_deleted, tenant_id` | `sync_fcl_stage_info` | `create_time, update_time, create_user, create_dept, update_user, status, is_deleted, tenant_id` (→ doc 27) |
| id (PK) | `id` | `sync_loan_foreclosure_hold` | `id` (→ doc 28) |
| Investor loan id | `loanid` | `sync_loan_foreclosure_hold` | `loanid` (→ doc 28) |
| Servicer loan id | `shellpointloanid` | `sync_loan_foreclosure_hold` | `svcloanid` (→ doc 28) |
| fctrdt | `dataasof` | `sync_loan_foreclosure_hold` | `fctrdt` (→ doc 28) |
| Hold description | `fchold1..3 description` | `sync_loan_foreclosure_hold` | `description` (→ doc 28) |
| Hold start date | `fchold1..3 startdate` | `sync_loan_foreclosure_hold` | `description_start_date` (→ doc 28) |
| Hold end date | `fchold1..3 enddate` | `sync_loan_foreclosure_hold` | `description_end_date` (→ doc 28) |
| System / audit columns | `create_user, create_dept, create_time, update_user, update_time, status, is_deleted, tenant_id` | `sync_loan_foreclosure_hold` | `create_user, create_dept, create_time, update_user, update_time, status, is_deleted, tenant_id` (→ doc 28) |
| id (PK) | `id` | `sync_loan_foreclosure_loss_mitigation` | `id` (→ doc 29) |
| Investor loan id | `loanid` | `sync_loan_foreclosure_loss_mitigation` | `loanid` (→ doc 29) |
| Servicer loan id | `shellpointloanid` | `sync_loan_foreclosure_loss_mitigation` | `svcloanid` (→ doc 29) |
| fctrdt | `dataasof` | `sync_loan_foreclosure_loss_mitigation` | `fctrdt` (→ doc 29) |
| Deal | `lmdeal (code)` | `sync_loan_foreclosure_loss_mitigation` | `deal` (→ doc 29) |
| Program | `lmprogram (code)` | `sync_loan_foreclosure_loss_mitigation` | `program` (→ doc 29) |
| Status | `lmstatus (code)` | `sync_loan_foreclosure_loss_mitigation` | `lmc_status` (→ doc 29) |
| Cycle Opened Date | `dealstartdate` | `sync_loan_foreclosure_loss_mitigation` | `cycle_opened_date` (→ doc 29) |
| Cycle Closed Date | `lmremovaldate` | `sync_loan_foreclosure_loss_mitigation` | `cycle_closed_date` (→ doc 29) |
| Final Disposition | `lmdecision (code)` | `sync_loan_foreclosure_loss_mitigation` | `final_disposition` (→ doc 29) |
| Denial / Reason | `denialreason (code)` | `sync_loan_foreclosure_loss_mitigation` | `denialreason` (→ doc 29) |
| Borrower Intentions | `borrowerintention (code)` | `sync_loan_foreclosure_loss_mitigation` | `borrower_intentions` (→ doc 29) |
| Imminent default flag | `—` | `sync_loan_foreclosure_loss_mitigation` | `imminent_default` (→ doc 29) |
| Single point of contact | `—` | `sync_loan_foreclosure_loss_mitigation` | `single_point_of_contact` (→ doc 29) |
| System / audit columns | `create_user, create_dept, create_time, update_user, update_time, status, is_deleted, tenant_id` | `sync_loan_foreclosure_loss_mitigation` | `create_user, create_dept, create_time, update_user, update_time, status, is_deleted, tenant_id` (→ doc 29) |
| id (PK) | `id` | `sync_loan_foreclosure_bankruptcy` | `id` (→ doc 30) |
| Investor loan id | `loanid` | `sync_loan_foreclosure_bankruptcy` | `loanid` (→ doc 30) |
| Servicer loan id | `shellpointloanid` | `sync_loan_foreclosure_bankruptcy` | `svcloanid` (→ doc 30) |
| fctrdt | `dataasof` | `sync_loan_foreclosure_bankruptcy` | `fctrdt` (→ doc 30) |
| Bankruptcy Status | `bkstatus (code)` | `sync_loan_foreclosure_bankruptcy` | `bankruptcy_status` (→ doc 30) |
| Legal Status | `legalstatus` | `sync_loan_foreclosure_bankruptcy` | `legal_status` (→ doc 30) |
| Status Date | `bkfileddate` | `sync_loan_foreclosure_bankruptcy` | `status_date` (→ doc 30) |
| Chapter | `bkchapter` | `sync_loan_foreclosure_bankruptcy` | `chapter` (→ doc 30) |
| Lien status | `(none for Newrez)` | `sync_loan_foreclosure_bankruptcy` | `lien_status` (→ doc 30) |
| MFR status | `(none for Newrez)` | `sync_loan_foreclosure_bankruptcy` | `mfr_status` (→ doc 30) |
| MFR filed date | `(none for Newrez)` | `sync_loan_foreclosure_bankruptcy` | `mfr_filed_date` (→ doc 30) |
| Claim status | `(none for Newrez)` | `sync_loan_foreclosure_bankruptcy` | `claim_status` (→ doc 30) |
| Proof of Claim Date | `pocfileddate` | `sync_loan_foreclosure_bankruptcy` | `proof_of_claim_date` (→ doc 30) |
| Post-petition due date | `bkpostpetitionduedate` | `sync_loan_foreclosure_bankruptcy` | `post_petition_due_date` (→ doc 30) |
| System / audit columns | `create_user, create_dept, create_time, update_user, update_time, status, is_deleted, tenant_id` | `sync_loan_foreclosure_bankruptcy` | `create_user, create_dept, create_time, update_user, update_time, status, is_deleted, tenant_id` (→ doc 30) |
| View-computed columns (Actual / Variance / Totals) | `actual_<stage>_days / var_<stage>_days / target_total / actual_total / var_total` | `sync_loan_foreclosure` | `actual_<stage>_days / var_<stage>_days / target_total / actual_total / var_total` (→ doc 26) |


## Known gaps / null fields

| Field | status | note |
|---|---|---|
| Notice of Intent Date | `newrez_null` | Newrez has no NOI source → NULL; only Capecodfive populates noi_date. |
| End date of notice of intent | `null_in_build` |  |
| Approval for referral | `null_in_build` |  |
| Date referred to attorney | `null_in_build` |  |
| Title Report Received | `newrez_empty` | Newrez does not populate titlereceiveddate (active FCL ~0%). |
| Preliminary Title Cleared | `newrez_empty` | Shares titlecleardate with Final Title Cleared; Newrez not populated. |
| Publication scheduled date | `null_in_build` |  |
| Final Title Cleared | `newrez_empty` | Shares titlecleardate with Preliminary; Newrez not populated. |
| Date foreclosure was completed | `null_in_build` |  |
| 3rd Party Sold Date | `null_in_build` | Hardcoded NULL in GEN_FCL_DETAIL (not mapped from raw here). |
| 3rd Party Proceeds Received | `newrez_empty` |  |
| Target for notice of intent | `view_default` | Stored NULL in sync; the view supplies the default target (e.g. first_legal 120, service 90, judgement 30). |
| Target for notice of intent expiration | `view_default` | Stored NULL in sync; the view supplies the default target (e.g. first_legal 120, service 90, judgement 30). |
| Target for approval for referral | `view_default` | Stored NULL in sync; the view supplies the default target (e.g. first_legal 120, service 90, judgement 30). |
| Target for referred to attorney | `view_default` | Stored NULL in sync; the view supplies the default target (e.g. first_legal 120, service 90, judgement 30). |
| Target for referred to foreclosure | `view_default` | Stored NULL in sync; the view supplies the default target (e.g. first_legal 120, service 90, judgement 30). |
| Target title report was received | `view_default` | Stored NULL in sync; the view supplies the default target (e.g. first_legal 120, service 90, judgement 30). |
| Target preliminary title was cleared | `view_default` | Stored NULL in sync; the view supplies the default target (e.g. first_legal 120, service 90, judgement 30). |
| Target of first legal action | `view_default` | Stored NULL in sync; the view supplies the default target (e.g. first_legal 120, service 90, judgement 30). |
| Target of service completion date | `view_default` | Stored NULL in sync; the view supplies the default target (e.g. first_legal 120, service 90, judgement 30). |
| Target of publication completion date | `view_default` | Stored NULL in sync; the view supplies the default target (e.g. first_legal 120, service 90, judgement 30). |
| Target of judgment hearing was set | `view_default` | Stored NULL in sync; the view supplies the default target (e.g. first_legal 120, service 90, judgement 30). |
| Target of judgment was issued | `view_default` | Stored NULL in sync; the view supplies the default target (e.g. first_legal 120, service 90, judgement 30). |
| Target of sale date set | `view_default` | Stored NULL in sync; the view supplies the default target (e.g. first_legal 120, service 90, judgement 30). |
| Target of final title was cleared | `view_default` | Stored NULL in sync; the view supplies the default target (e.g. first_legal 120, service 90, judgement 30). |
| Target of sale was held | `view_default` | Stored NULL in sync; the view supplies the default target (e.g. first_legal 120, service 90, judgement 30). |
| Flag for active bankruptcy | `null_in_build` |  |
| Flag for completed bankruptcy | `null_in_build` |  |
| Estimated hold days for the process | `null_in_build` |  |
| Total number of bankruptcies | `null_in_build` |  |
| Approval Status | `null_in_build` |  |
| Sale Date | `null_in_build` |  |
| Loan Resolution Holds | `null_in_build` |  |
| Servicer number identifier | `null_in_build` |  |
| Flag for completed foreclosure | `null_in_build` |  |
| Name of the foreclosure attorney | `null_in_build` |  |
| NOI start date | `null_in_build` |  |
| NOI window end | `null_in_build` |  |
| NOI days in stage | `null_in_build` |  |
| Publication start date | `null_in_build` |  |
| Publication window end | `null_in_build` |  |
| Publication days in stage | `null_in_build` |  |
| Imminent default flag | `newrez_null` | Hardcoded NULL for Newrez. |
| Single point of contact | `newrez_null` | Hardcoded NULL for Newrez. |
| Lien status | `newrez_null` |  |
| MFR status | `newrez_null` |  |
| MFR filed date | `newrez_null` |  |
| Claim status | `newrez_null` |  |

> Also: the L3 producer of `port.basic_data_loan_delinq_clean` is not in the PrefectFlow repo (referenced by name only); SLS/MRC and other servicers report no FCL detail.


## End-to-end worked trace (MCP-verified)

Two milestone fields traced end-to-end for one real loan; the value is identical at every hop (MCP-verified against redshift_prod and mysql_prod).

**Referred to Foreclosure** — loan `7727004408`

| hop | table.column | value |
|---|---|---|
| L1 raw | `newrez.portnewrezfc.fcreferraldate` | `2024-03-08` |
| L4 fact | `port.basic_data_loan_fcl.referral_start_date` | `2024-03-08` |
| L4 | `port.basic_data_loan_foreclosure.timeline_referred_to_foreclosure_date` | `2024-03-08` |
| L5 BPS | `bpms.sync_loan_foreclosure.timeline_referred_to_foreclosure_date` | `2024-03-08` |

**Judgement (scheduled hearing date)** — loan `7727004408`

| hop | table.column | value |
|---|---|---|
| L1 raw | `newrez.portnewrezfc.fcjudgmenthearingscheduled` | `2026-08-21` |
| L4 fact | `port.basic_data_loan_fcl.fcjudgment_hearing_scheduled` | `2026-08-21` |
| L4 | `port.basic_data_loan_foreclosure.timeline_judgement_date` | `2026-08-21` |
| L5 BPS | `bpms.sync_loan_foreclosure.timeline_judgement_date` | `2026-08-21` |


## Per-table detail docs

- **doc 26** — `bpms.sync_loan_foreclosure` (Main (milestones / summary / status))
- **doc 27** — `bpms.sync_fcl_stage_info` (Stage / days)
- **doc 28** — `bpms.sync_loan_foreclosure_hold` (Hold (wide→long unpivot))
- **doc 29** — `bpms.sync_loan_foreclosure_loss_mitigation` (Loss Mitigation (code→text decode))
- **doc 30** — `bpms.sync_loan_foreclosure_bankruptcy` (Bankruptcy (code→text decode))
