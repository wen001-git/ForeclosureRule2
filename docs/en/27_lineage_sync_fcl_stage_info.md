# Doc 27 · Stage / days — `bpms.sync_fcl_stage_info` field lineage

> <!-- RULEGLOSS_PTR -->📖 **Rule terms**: plain-language + formula for the technical phrases in the `rule` column — see [doc 25 · transform-rule glossary (appendix)](25_fcl_lineage_overview.md).
> <!-- CODEGLOSS_PTR -->🔧 **code legend**: `pool`=ETL build/SQL code `basic_data_pool_config.py` · `asset`=BPS sync SQL `asset_managment_config.py` · `view`=BPS view definition; the number after the colon = **line number** in that file (links are clickable).

> **Data source** — the source of truth is `outputs/fcl_lineage_source.json` (per-field lineage); these per-field docs are currently hand-maintained (the old generator `scripts/gen_fcl_lineage.py` has been retired/removed).


## Document Purpose

Per-field lineage for BPS table `bpms.sync_fcl_stage_info`: from the Servicer raw column, through every intermediate table, to the final BPS column, with each hop's transform rule and code reference.

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


`newrez.portnewrezfc` → `tempfc.temp_basic_data_fcl` → `port.basic_data_loan_fcl` → `port.fcl_stage_info` → `bpms.sync_fcl_stage_info`

| # | layer | db | table | role |
|---|---|---|---|---|
| 1 | L0/L1 | MySQL+Redshift | `newrez.portnewrezfc` | Servicer raw |
| 2 | L4·temp | Redshift | `tempfc.temp_basic_data_fcl` | 3-servicer rename-UNION of L1 raw / 三家 servicer 改名 UNION (CREATE_BASIC_FCL, [pool:1531-1654](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L1531-1654)) |
| 3 | L4 | Redshift | `port.basic_data_loan_fcl` | canonical FCL fact |
| 4 | L4 | Redshift | `port.fcl_stage_info` | stage classification + day-math (GEN_FCL_STAGE); group/state from port.basic_data_fcl_related |
| 5 | L5 | MySQL bpms | `bpms.sync_fcl_stage_info` | BPS app table (12-FCL_STAGE sync, keeps fctrdt history) |

> The `#` column is a sequence number, not the layer number. The FCL fact `port.basic_data_loan_fcl` is built DIRECTLY from the L1 servicer raw tables (UNIONed in `tempfc.temp_basic_data_fcl`; CREATE_BASIC_FCL [pool:1531-1654](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L1531-1654)), so the L2 unified-daily (`port.basic_data_daily_loan_common`) and L3 clean (`basic_data_daily_loan_common_clean` / `basic_data_loan_delinq_clean`) layers are NOT part of this branch by design — they carry the common + delinquency fields and re-enter only via the `group` dimension (doc 27, `basic_data_fcl_related`) and the monthly `portmonth` path. See doc 02 for the full L0–L5 pipeline.

> code: `pool` = [PrefectFlow/flow/basic_data/basic_data_config/basic_data_pool_config.py](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py) · `asset` = [PrefectFlow/flow/bps/bps_config/asset_managment_config.py](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py) · `view` = bpms.biz_data_view_loan_details_foreclosure (SHOW CREATE VIEW)


## Identity / key columns

### 1. id (PK)  (`bpms.sync_fcl_stage_info.id`)

_Auto surrogate primary key._

**Source (L1)**
- Newrez: `bpms.sync_fcl_stage_info.id`  (Newrez-only detail)

**Flow:** ①sync_fcl_stage_info
**Lineage (per hop: # column — rule [code])**
- 1. `bpms.sync_fcl_stage_info.id` — auto-increment PK (BPS app) [asset]

**Note:** Generated by the BPS app on insert; not from source.

### 2. fctrdt  (`bpms.sync_fcl_stage_info.fctrdt`)

_Daily snapshot/report date (=dataasof)._

**Source (L1)**
- Newrez: `port.basic_data_loan_fcl.dataasof`  (Newrez-only detail)

**Flow:** ①basic_data_loan_fcl → ②sync_fcl_stage_info
**Lineage (per hop: # column — rule [code])**
- 1. `port.basic_data_loan_fcl.dataasof` — dataasof → fctrdt
- 2. `bpms.sync_fcl_stage_info.fctrdt` — sync passthrough [asset]

### 3. Investor loan id  (`bpms.sync_fcl_stage_info.loanid`)

_Investor loan id / servicer loan id._

**Source (L1)**
- Newrez: `newrez.portnewrezfc.loanid`  (Newrez-only detail)

**Flow:** ①portnewrezfc → ②fcl_stage_info → ③sync_fcl_stage_info
**Lineage (per hop: # column — rule [code])**
- 1. `newrez.portnewrezfc.loanid` — servicer raw
- 2. `port.fcl_stage_info.loanid` — passthrough
- 3. `bpms.sync_fcl_stage_info.loanid` — sync passthrough [asset]

### 4. servicer  (`bpms.sync_fcl_stage_info.servicer`)

_Servicer name._

**Source (L1)**
- Newrez: `(per servicer)` · constant 'Newrez'/'Carrington'/'Capecodfive'  (Newrez-only detail)

**Flow:** ①(per → ②sync_fcl_stage_info
**Lineage (per hop: # column — rule [code])**
- 1. `(per servicer)` · constant 'Newrez'/'Carrington'/'Capecodfive' — constant per UNION branch [pool:1536/1577/1618](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L1536)
- 2. `bpms.sync_fcl_stage_info.servicer` — sync passthrough [asset]


## Dimensions (group / judicial / state)

### 5. stage (current bucket)  (`bpms.sync_fcl_stage_info.stage`)

_The loan's current stage classification (waterfall outcome)._

**Source (L1)**
- Newrez: `port.basic_data_loan_fcl` · (stage dates)  (Newrez-only detail)

**Flow:** ①basic_data_loan_fcl → ②fcl_stage_info → ③sync_fcl_stage_info
**Lineage (per hop: # column — rule [code])**
- 1. `port.basic_data_loan_fcl` · (stage dates) — waterfall by first non-null date
- 2. `port.fcl_stage_info.stage` — CASE waterfall: SALE→JUDGEMENT→PUBLICATION→SERVICE→FIRST_LEGAL→REFERRAL→DEMAND [pool:2095-2102](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L2095-2102)
- 3. `bpms.sync_fcl_stage_info.stage` — sync passthrough [asset:925](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L925)

**Note:** Values: SALE / JUDGEMENT / PUBLICATION / SERVICE / FIRST_LEGAL / REFERRAL / DEMAND (7; prod snapshot currently REFERRAL/SALE/FIRST_LEGAL/SERVICE/JUDGEMENT).

```sql
CASE: sale_start⇒SALE; elif fcjudgment_start⇒JUDGEMENT; elif publication_start⇒PUBLICATION; elif service_start⇒SERVICE; elif legal_start⇒FIRST_LEGAL; elif referral_start⇒REFERRAL; elif demand_sent_start⇒DEMAND; else NULL
```
🔎 **How it works:** The current stage is the FURTHEST milestone the loan has reached: a 7-way CASE checked in priority order SALE → JUDGEMENT → PUBLICATION → SERVICE → FIRST_LEGAL → REFERRAL → DEMAND — the first stage whose start date is non-null wins.
▶ **Example:** ① 7727001179: sale_start set ⇒ stage = SALE. ② 7727000357: no sale but fcjudgment_start set ⇒ JUDGEMENT. ③ 700082880000091: only up to service_start ⇒ SERVICE. ④ 700082700000033: only referral_start ⇒ REFERRAL.

### 6. Group (FCL/D120P/D90/REO/P)  (`bpms.sync_fcl_stage_info.group`)

_Delinquency/legal group used to bucket the loan._

**Source (L1)**
- Newrez: `newrez.portnewrezgeneral.delinquency_status_mba`
- Carrington: `carrington.portcarrington.loan_status / fcl_flag`
- Capecodfive: —

**Flow:** ①basic_data_fcl_related → ②fcl_stage_info → ③sync_fcl_stage_info
**Lineage (per hop: # column — rule [code])**
- 1. `port.basic_data_fcl_related.delq_status` — CASE mba then days360 fallback 见 sql [pool:1702-1711](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L1702-1711)
- 2. `port.fcl_stage_info.group` — = r.delq_status (join loanid+dataasof) [pool:2348,2400](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L2348)
- 3. `bpms.sync_fcl_stage_info.group` — 12-FCL_STAGE sync pass-through [asset:925](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L925)

**Rule (full):** `fcl_stage_info.group = basic_data_fcl_related.delq_status`. **Newrez** ([pool:1702-1711](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L1702-1711)): if `delinquency_status_mba='Full Payoff'`→P, `'REO'`→REO, any `'Foreclosure*'`→FCL; otherwise bucket by `days360(portnewrezpmt.nextduedate, dataasof)`: `<30`→C, `<60`→D30, `<90`→D60, `<120`→D90, else→D120P. **Carrington** ([pool:1749-1758](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L1749-1758)): if `loan_status='Foreclosure' OR fcl_flag='Active'`→FCL, `loan_status IN ('R','REO')`→REO, `IN ('Completed Payoff','Completed Short Sale')`→P; otherwise the same `days360` buckets on `date_payment_due`. **Capecodfive** is not in `basic_data_fcl_related` → group is `—`.

```sql
group = port.basic_data_fcl_related.delq_status; CASE delinquency_status_mba: 'Full Payoff'→P, 'REO'→REO, Foreclosure*→FCL, ELSE days360(nextduedate,dataasof): <30→C,<60→D30,<90→D60,<120→D90,else→D120P
```
🔎 **How it works:** delq_status (carried into fcl_stage_info.group): if delinquency_status_mba is 'Full Payoff'→P, 'REO'→REO, any 'Foreclosure*'→FCL; otherwise bucket by days360(nextduedate, dataasof): <30→C, <60→D30, <90→D60, <120→D90, else→D120P.
▶ **Example:** 7727004408: delinquency_status_mba='Foreclosure' ⇒ FCL. (Delinquency path, illustrative: nextduedate ~100 days before dataasof ⇒ days360≈100 ⇒ D90.)

### 7. State  (`bpms.sync_fcl_stage_info.state`)

_Property state._

**Source (L1)**
- Newrez: `newrez.portnewrezprop.propertystate`
- Carrington: `carrington.portcarrington.property_state`
- Capecodfive: —

**Flow:** ①basic_data_fcl_related → ②fcl_stage_info → ③sync_fcl_stage_info
**Lineage (per hop: # column — rule [code])**
- 1. `port.basic_data_fcl_related.propertystate` — direct 直传 [pool:1721](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L1721)
- 2. `port.fcl_stage_info.state` — = property state (r.propertystate), joined in [pool:2401](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L2401)
- 3. `bpms.sync_fcl_stage_info.state` — sync pass-through [asset:925](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L925)

**Note:** The property's US state, joined from the FCL relation attributes (r.propertystate). Direct value, no transform.

### 8. Judicial (Y/N)  (`bpms.sync_fcl_stage_info.judicial`)

_Judicial flag with state fallback._

**Source (L1)**
- Newrez: `newrez.portnewrezfc.judicial`
- Carrington: —
- Capecodfive: —

**Flow:** ①basic_data_loan_fcl → ②fcl_stage_info → ③sync_fcl_stage_info
**Lineage (per hop: # column — rule [code])**
- 1. `port.basic_data_loan_fcl.judicial` — normalize cast(int) [pool:2034](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L2034)
- 2. `port.fcl_stage_info.judicial` — Y/N else state-config fallback 见 sql [pool:2351-2353,2432](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L2351-2353)
- 3. `bpms.sync_fcl_stage_info.judicial` — sync pass-through [asset:925](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L925)

**Rule (full):** `fcl_stage_info.judicial = CASE judicial=1→'Y', 0→'N'`. **Newrez** supplies the loan-level `judicial` flag ([pool:1565](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L1565)). **Carrington / Capecodfive** have `judicial=NULL` in the fact ([pool:1606](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L1606) / 1647) → **state fallback**: join `basic_data_judicial_config` on the property state and use its judicial value ([pool:2351-2353,](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L2351-2353) join [pool:2432](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L2432)).

```sql
CASE judicial=1→'Y', 0→'N', ELSE config_judicial (port.basic_data_judicial_config keyed by propertystate)
```
🔎 **How it works:** From the normalized loan-level judicial: 1→'Y', 0→'N'. If NULL/blank, fall back to the state-level judicial config (basic_data_judicial_config keyed by property state).
▶ **Example:** judicial=1 ⇒ 'Y'. A loan with no flag in a judicial state (e.g. FL) ⇒ config 'Y'; in a non-judicial state (e.g. TX) ⇒ 'N'.


## Stage start dates

### 9. Demand start date  (`bpms.sync_fcl_stage_info.demand_start_date`)

_Stage start date._

> ℹ️ **Passthrough** of `newrez.portnewrezfc.demandsentdate` (demand-letter sent date = DEMAND stage left edge). Full rules: see [doc 31 §2](31_fcl_stage_window_rules.md#2-stage_start_date-sources).

**Source (L1)**
- Newrez: `newrez.portnewrezfc.demandsentdate`
- Carrington: —
- Capecodfive: —

**Flow:** ①basic_data_loan_fcl → ②fcl_stage_info → ③sync_fcl_stage_info
**Lineage (per hop: # column — rule [code])**
- 1. `port.basic_data_loan_fcl.demandsentdate` — source 源
- 2. `port.fcl_stage_info.demand_start_date` — passthrough of source demandsentdate [pool:2037](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L2037)
- 3. `bpms.sync_fcl_stage_info.demand_start_date` — sync passthrough [asset:925](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L925)

```sql
demand_start_date = passthrough of business_1.demandsentdate (no transform)
```
🔎 **How it works:** Direct passthrough of the source milestone date `demandsentdate`; no transform. NULL if the loan never reached this stage.
▶ **Example:** 700082880000091: demandsentdate 2025-12-29 ⇒ demand_start_date = 2025-12-29.

### 10. Demand window end  (`bpms.sync_fcl_stage_info.demand_end_date`)

_Demand window end (= demand-expiration date demandexpirationdate)._

> ℹ️ **Passthrough** of `newrez.portnewrezfc.demandexpirationdate` (window right edge for display). ⚠️ **NOT used in demand_stage_days computation** — demand always counts to curr_date. Full rules: see [doc 31 §3 + §5](31_fcl_stage_window_rules.md#3-stage_end_date-derivation).

**Source (L1)**
- Newrez: `newrez.portnewrezfc`  (Newrez-only detail)

**Flow:** ①portnewrezfc → ②basic_data_loan_fcl → ③fcl_stage_info → ④sync_fcl_stage_info
**Lineage (per hop: # column — rule [code])**
- 1. `newrez.portnewrezfc.demandexpirationdate` — servicer raw (column exists, DB-verified)
- 2. `port.basic_data_loan_fcl.demandexpirationdate` — passthrough (column exists, DB-verified)
- 3. `port.fcl_stage_info.demand_end_date` — = source demandexpirationdate (passthrough; NOT next-stage start) [pool:2038,2355](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L2038)
- 4. `bpms.sync_fcl_stage_info.demand_end_date` — sync passthrough [asset:925](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L925)

```sql
demand_end_date = passthrough of business_1.demandexpirationdate ([pool:2038](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L2038))
```
🔎 **How it works:** The demand window's end is the servicer's demand-expiration date (demandexpirationdate), passed through unchanged — it is NOT the next stage's start. Note: demand_stage_days does not use this column; it always counts from demand_start to the current date (logic = curr_date, [pool:2039-2041](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L2039-2041)).
▶ **Example (with full math)** 700082880000091: demand_start_date = 2025-12-29 (passthrough of `newrez.portnewrezfc.demandsentdate`), demand_end_date = 2026-01-13 (passthrough of `demandexpirationdate`; **right edge of the window only — not used in day-count math**). demand_stage_days ignores demand_end_date and counts to curr_date:
> `demand_stage_days = datediff(2025-12-29, curr_date 2026-06-09) + 1 = 162 + 1 = `**`163`**` (curr_date = ETL run date; matches prod)`.

### 11. NOI start date  (`bpms.sync_fcl_stage_info.noi_start_date`)

_NOI bucket not populated separately (covered by DEMAND)._

> ⚠ null_in_build

**Source (L1)**
- Newrez: `port.fcl_stage_info.noi_start_date`  (Newrez-only detail)

**Flow:** ①fcl_stage_info → ②sync_fcl_stage_info
**Lineage (per hop: # column — rule [code])**
- 1. `port.fcl_stage_info.noi_start_date` — NULL by design — NOI not populated in business_1 [pool:2043-2046](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L2043-2046)
- 2. `bpms.sync_fcl_stage_info.noi_start_date` — sync passthrough (NULL) [asset:925](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L925)

**Note:** The NOI stage is not populated in the business_1 CTE (hardcoded NULL); NOI activity is represented inside the DEMAND window. Verified NULL across all prod rows.

### 12. NOI window end  (`bpms.sync_fcl_stage_info.noi_end_date`)

_NOI window end (stage not populated; always NULL)._

> ⚠ null_in_build

**Source (L1)**
- Newrez: `newrez.portnewrezfc`  (Newrez-only detail)

**Flow:** ①portnewrezfc → ②basic_data_loan_fcl → ③fcl_stage_info → ④sync_fcl_stage_info
**Lineage (per hop: # column — rule [code])**
- 1. `newrez.portnewrezfc` — —
- 2. `port.basic_data_loan_fcl` · (stage end) — source 源
- 3. `port.fcl_stage_info.noi_end_date` — NULL by design [pool:2043-2046](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L2043-2046)
- 4. `bpms.sync_fcl_stage_info.noi_end_date` — sync passthrough [asset:925](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L925)

**Note:** Hardcoded NULL (see noi_start_date). Verified NULL across all prod rows.

### 13. NOI days in stage  (`bpms.sync_fcl_stage_info.noi_stage_days`)

_NOI bucket not populated separately (covered by DEMAND)._

> ⚠ null_in_build

**Source (L1)**
- Newrez: `port.fcl_stage_info.noi_stage_days`  (Newrez-only detail)

**Flow:** ①fcl_stage_info → ②sync_fcl_stage_info
**Lineage (per hop: # column — rule [code])**
- 1. `port.fcl_stage_info.noi_stage_days` — NULL by design [pool:2046](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L2046)
- 2. `bpms.sync_fcl_stage_info.noi_stage_days` — sync passthrough (NULL) [asset:925](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L925)

**Note:** Hardcoded NULL — no NOI window is computed. Verified NULL across all prod rows.

### 14. Referral start date  (`bpms.sync_fcl_stage_info.referral_start_date`)

_Stage start date._

> ℹ️ **Passthrough** of `newrez.portnewrezfc.fcreferraldate` (referral date = REFERRAL stage left edge). Full rules: see [doc 31 §2](31_fcl_stage_window_rules.md#2-stage_start_date-sources).

**Source (L1)**
- Newrez: `newrez.portnewrezfc.fcreferraldate`
- Carrington: `carrington.portcarrington.fcl_referral_date`
- Capecodfive: `capecodfive.portcapecodfive_monthly_collections.foreclosure_date_refrd_atty`

**Flow:** ①basic_data_loan_fcl → ②fcl_stage_info → ③sync_fcl_stage_info
**Lineage (per hop: # column — rule [code])**
- 1. `port.basic_data_loan_fcl.referral_start_date` — source 源
- 2. `port.fcl_stage_info.referral_start_date` — passthrough of source referral_start_date [pool:2048](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L2048)
- 3. `bpms.sync_fcl_stage_info.referral_start_date` — sync passthrough [asset:925](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L925)

```sql
referral_start_date = passthrough of business_1.referral_start_date (no transform)
```
🔎 **How it works:** Direct passthrough of the source milestone date `referral_start_date`; no transform. NULL if the loan never reached this stage.
▶ **Example:** 700082880000091: referral_start_date 2026-01-20 ⇒ 2026-01-20.

### 15. Referral window end  (`bpms.sync_fcl_stage_info.referral_end_date`)

_Referral window end (= next stage 'first legal' start; NULL if not reached)._

> ℹ️ **Derived** (= next stage `first_legal_start_date`), **NOT** a Newrez single-column passthrough; NULL if first-legal not started. Full rules: see [doc 31 §3](31_fcl_stage_window_rules.md#3-stage_end_date-derivation).

**Source (L1)**
- Newrez: `newrez.portnewrezfc`  (Newrez-only detail)

**Flow:** ①portnewrezfc → ②basic_data_loan_fcl → ③fcl_stage_info → ④sync_fcl_stage_info
**Lineage (per hop: # column — rule [code])**
- 1. `newrez.portnewrezfc` — —
- 2. `port.basic_data_loan_fcl` · (stage end) — source 源
- 3. `port.fcl_stage_info.referral_end_date` — = next stage start (first_legal_start_date (legal_start_date)); NULL if not reached [pool:2049,2365](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L2049)
- 4. `bpms.sync_fcl_stage_info.referral_end_date` — sync passthrough [asset:925](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L925)

```sql
referral_end_date = first_legal_start_date (legal_start_date) (the next stage's start); NULL if the next stage has not started
```
🔎 **How it works:** The referral window ends when the next stage (first legal) starts: referral_end_date = first_legal_start_date. If first legal hasn't started, this column is NULL — and referral_stage_days then counts to the current date instead (logic_referral_end_date = coalesce(end, curr_date), [pool:2050-2052](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L2050-2052)).
▶ **Example:** ① next reached — 700082880000091: first_legal_start=2026-03-12 ⇒ referral_end_date=2026-03-12, referral_stage_days=52 (datediff(2026-01-20,2026-03-12)+1). ② not reached — 700082700000033 (in REFERRAL): referral_end_date=NULL, referral_stage_days=119 (counts 2026-02-11→today).

### 16. First Legal start date  (`bpms.sync_fcl_stage_info.first_legal_start_date`)

_Stage start date._

> ℹ️ **Passthrough** of `newrez.portnewrezfc.firstlegaldate` (first legal action date = FIRST_LEGAL stage left edge). Full rules: see [doc 31 §2](31_fcl_stage_window_rules.md#2-stage_start_date-sources).

**Source (L1)**
- Newrez: `newrez.portnewrezfc.firstlegaldate`
- Carrington: —
- Capecodfive: `capecodfive.portcapecodfive_monthly_collections.foreclosure_first_legal_date`

**Flow:** ①basic_data_loan_fcl → ②fcl_stage_info → ③sync_fcl_stage_info
**Lineage (per hop: # column — rule [code])**
- 1. `port.basic_data_loan_fcl.legal_start_date` — source 源
- 2. `port.fcl_stage_info.first_legal_start_date` — passthrough of source legal_start_date [pool:2058](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L2058)
- 3. `bpms.sync_fcl_stage_info.first_legal_start_date` — sync passthrough [asset:925](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L925)

```sql
first_legal_start_date = passthrough of business_1.legal_start_date (no transform)
```
🔎 **How it works:** Direct passthrough of the source milestone date `legal_start_date`; no transform. NULL if the loan never reached this stage.
▶ **Example:** 700082880000091: legal_start_date 2026-03-12 ⇒ first_legal_start_date = 2026-03-12.

### 17. First Legal window end  (`bpms.sync_fcl_stage_info.first_legal_end_date`)

_First-legal window end (= next stage 'service' start; NULL if not reached)._

> ℹ️ **Derived** (= next stage `service_start_date`), **NOT** a Newrez single-column passthrough; NULL if service not started. Full rules: see [doc 31 §3](31_fcl_stage_window_rules.md#3-stage_end_date-derivation).

**Source (L1)**
- Newrez: `newrez.portnewrezfc`  (Newrez-only detail)

**Flow:** ①portnewrezfc → ②basic_data_loan_fcl → ③fcl_stage_info → ④sync_fcl_stage_info
**Lineage (per hop: # column — rule [code])**
- 1. `newrez.portnewrezfc` — —
- 2. `port.basic_data_loan_fcl` · (stage end) — source 源
- 3. `port.fcl_stage_info.first_legal_end_date` — = next stage start (service_start_date); NULL if not reached [pool:2059,2370](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L2059)
- 4. `bpms.sync_fcl_stage_info.first_legal_end_date` — sync passthrough [asset:925](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L925)

```sql
first_legal_end_date = service_start_date (the next stage's start); NULL if the next stage has not started
```
🔎 **How it works:** The first-legal window ends when the next stage (service) starts: first_legal_end_date = service_start_date; NULL if service hasn't started (first_legal_stage_days then counts to the current date, [pool:2060-2062](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L2060-2062)).
▶ **Example (with full math)**
> ① Next stage reached (end filled) — 700082880000091: first_legal_start_date = 2026-03-12 (passthrough of `newrez.firstlegaldate`), service_start_date = 2026-05-13 ⇒ first_legal_end_date = 2026-05-13; first_legal_stage_days = datediff(2026-03-12, 2026-05-13) + 1 = 62 + 1 = **63** (matches prod).
> ② Still in FIRST_LEGAL (service not yet started, end = curr_date) — first_legal_end_date = NULL; first_legal_stage_days = datediff(first_legal_start_date, curr_date 2026-06-09) + 1 (same "count to today" pattern as referral 700082700000033).

### 18. First-legal first-seen date  (`bpms.sync_fcl_stage_info.first_legal_date_history`)

_ETL first-seen tracking of the first-legal date._

**Source (L1)**
- Newrez: `newrez.portnewrezfc.firstlegaldate`  (Newrez-only detail)

**Flow:** ①portnewrezfc → ②basic_data_loan_fcl → ③fcl_stage_info → ④sync_fcl_stage_info
**Lineage (per hop: # column — rule [code])**
- 1. `newrez.portnewrezfc.firstlegaldate` — servicer raw 原始
- 2. `port.basic_data_loan_fcl.legal_start_date` — source 源
- 3. `port.fcl_stage_info.first_legal_date_history` — first-seen tracking (join L); NULL across prod [pool:2374](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L2374)
- 4. `bpms.sync_fcl_stage_info.first_legal_date_history` — sync passthrough [asset:925](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L925)

**Note:** An ETL first-seen tracking column joined from L.first_legal_date_history; the source is not populated, so it is NULL across all current prod rows.

### 19. Service start date  (`bpms.sync_fcl_stage_info.service_start_date`)

_Stage start date._

> ℹ️ **Passthrough** of `newrez.portnewrezfc.servicecompletedate`. ⚠️ **Counter-intuitive name**: `servicecompletedate` literally reads like "service **completed** date", but in the FCL stage model the SERVICE stage is "the waiting window after service is completed and before judgement is available" — so this date is the SERVICE stage's **start**, NOT end. Full rules: see [doc 31 §2 + §6](31_fcl_stage_window_rules.md#6-common-pitfalls).

**Source (L1)**
- Newrez: `newrez.portnewrezfc.servicecompletedate`
- Carrington: —
- Capecodfive: `capecodfive.portcapecodfive_monthly_collections.foreclosure_service_date`

**Flow:** ①basic_data_loan_fcl → ②fcl_stage_info → ③sync_fcl_stage_info
**Lineage (per hop: # column — rule [code])**
- 1. `port.basic_data_loan_fcl.service_start_date` — source 源
- 2. `port.fcl_stage_info.service_start_date` — passthrough of source service_start_date [pool:2068](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L2068)
- 3. `bpms.sync_fcl_stage_info.service_start_date` — sync passthrough [asset:925](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L925)

```sql
service_start_date = passthrough of business_1.service_start_date (no transform)
```
🔎 **How it works:** Direct passthrough of the source milestone date `service_start_date`; no transform. NULL if the loan never reached this stage.
▶ **Example:** 700082880000091: service_start_date 2026-05-13 ⇒ 2026-05-13.

### 20. Service window end  (`bpms.sync_fcl_stage_info.service_end_date`)

_Service window end (= next stage 'judgement availability'; NULL if not reached)._

> ℹ️ **Derived** (= next stage `judgment_available_date`), **NOT** a Newrez single-column passthrough; NULL if judgement not reached. Full rules: see [doc 31 §3](31_fcl_stage_window_rules.md#3-stage_end_date-derivation).

**Source (L1)**
- Newrez: `newrez.portnewrezfc`  (Newrez-only detail)

**Flow:** ①portnewrezfc → ②basic_data_loan_fcl → ③fcl_stage_info → ④sync_fcl_stage_info
**Lineage (per hop: # column — rule [code])**
- 1. `newrez.portnewrezfc` — —
- 2. `port.basic_data_loan_fcl` · (stage end) — source 源
- 3. `port.fcl_stage_info.service_end_date` — = next stage start (judgement availability (judgment_available_date)); NULL if not reached [pool:2069,2376](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L2069)
- 4. `bpms.sync_fcl_stage_info.service_end_date` — sync passthrough [asset:925](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L925)

```sql
service_end_date = judgement availability (judgment_available_date) (the next stage's start); NULL if the next stage has not started
```
🔎 **How it works:** The service window ends when the next stage (judgement availability) starts: service_end_date = judgment_available_date; NULL if not reached (service_stage_days then counts to the current date, [pool:2070-2072](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L2070-2072)).
▶ **Example (with full math)**
> ① Next stage reached (end filled) — 7727000357: service_start_date = 2025-08-14 (passthrough of `newrez.servicecompletedate`), service_end_date = 2026-01-26 (= next stage `judgment_available_date`) ⇒ service_stage_days = datediff(2025-08-14, 2026-01-26) + 1 = 165 + 1 = **166** (matches prod).
> ② Still in SERVICE (judgement not yet reached, end = curr_date) — 700082880000091 (current stage = SERVICE): service_start_date = 2026-05-13 (passthrough of `newrez.servicecompletedate`), service_end_date = NULL ⇒ service_stage_days = datediff(2026-05-13, curr_date 2026-06-09) + 1 = 27 + 1 = **28** (curr_date = ETL run date; matches prod). **Clarification: the "2026-05-13" in case ② is this loan's `service_start_date` (i.e. the `servicecompletedate` from the newrez source) — not a separate raw-file value.**

### 21. Publication start date  (`bpms.sync_fcl_stage_info.publication_start_date`)

_Publication not populated for these servicers._

> ⚠ null_in_build

**Source (L1)**
- Newrez: `port.fcl_stage_info.publication_start_date`  (Newrez-only detail)

**Flow:** ①fcl_stage_info → ②sync_fcl_stage_info
**Lineage (per hop: # column — rule [code])**
- 1. `port.fcl_stage_info.publication_start_date` — NULL by design — publication not populated [pool:2078-2081](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L2078-2081)
- 2. `bpms.sync_fcl_stage_info.publication_start_date` — sync passthrough (NULL) [asset:925](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L925)

**Note:** The publication stage is not populated in business_1 (hardcoded NULL). Verified NULL across all prod rows.

### 22. Publication window end  (`bpms.sync_fcl_stage_info.publication_end_date`)

_Publication window end (stage not populated; always NULL)._

> ⚠ null_in_build

**Source (L1)**
- Newrez: `newrez.portnewrezfc`  (Newrez-only detail)

**Flow:** ①portnewrezfc → ②basic_data_loan_fcl → ③fcl_stage_info → ④sync_fcl_stage_info
**Lineage (per hop: # column — rule [code])**
- 1. `newrez.portnewrezfc` — —
- 2. `port.basic_data_loan_fcl` · (stage end) — source 源
- 3. `port.fcl_stage_info.publication_end_date` — NULL by design [pool:2078-2081](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L2078-2081)
- 4. `bpms.sync_fcl_stage_info.publication_end_date` — sync passthrough [asset:925](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L925)

**Note:** Hardcoded NULL (see publication_start_date). Verified NULL across all prod rows.

### 23. Publication days in stage  (`bpms.sync_fcl_stage_info.publication_stage_days`)

_Publication not populated for these servicers._

> ⚠ null_in_build

**Source (L1)**
- Newrez: `port.fcl_stage_info.publication_stage_days`  (Newrez-only detail)

**Flow:** ①fcl_stage_info → ②sync_fcl_stage_info
**Lineage (per hop: # column — rule [code])**
- 1. `port.fcl_stage_info.publication_stage_days` — NULL by design [pool:2081](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L2081)
- 2. `bpms.sync_fcl_stage_info.publication_stage_days` — sync passthrough (NULL) [asset:925](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L925)

**Note:** Hardcoded NULL — no publication window is computed. Verified NULL across all prod rows.

### 24. Judgement start date  (`bpms.sync_fcl_stage_info.judgement_start_date`)

_Stage start date._

**Source (L1)**
- Newrez: `newrez.portnewrezfc.fcjudgmenthearingscheduled`
- Carrington: —
- Capecodfive: —

**Flow:** ①basic_data_loan_fcl → ②fcl_stage_info → ③sync_fcl_stage_info
**Lineage (per hop: # column — rule [code])**
- 1. `port.basic_data_loan_fcl.fcjudgment_hearing_scheduled` — source 源
- 2. `port.fcl_stage_info.judgement_start_date` — passthrough of source fcjudgment_start_date [pool:2084,2386](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L2084)
- 3. `bpms.sync_fcl_stage_info.judgement_start_date` — sync passthrough [asset:925](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L925)

```sql
judgement_start_date = passthrough of business_1.fcjudgment_start_date (no transform)
```
🔎 **How it works:** Direct passthrough of the source milestone date `fcjudgment_start_date`; no transform. NULL if the loan never reached this stage.
▶ **Example:** 7727001179: fcjudgment_start_date 2025-11-29 ⇒ judgement_start_date = 2025-11-29.

### 25. Judgement window end  (`bpms.sync_fcl_stage_info.judgement_end_date`)

_Judgement window end (always NULL; bucket uses to_judgement_days)._

**Source (L1)**
- Newrez: `newrez.portnewrezfc`  (Newrez-only detail)

**Flow:** ①portnewrezfc → ②basic_data_loan_fcl → ③fcl_stage_info → ④sync_fcl_stage_info
**Lineage (per hop: # column — rule [code])**
- 1. `newrez.portnewrezfc` — —
- 2. `port.basic_data_loan_fcl` · (stage end) — source 源
- 3. `port.fcl_stage_info.judgement_end_date` — NULL (bucket uses to_judgement_days) [pool:2387](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L2387)
- 4. `bpms.sync_fcl_stage_info.judgement_end_date` — sync passthrough [asset:925](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L925)

**Note:** Hardcoded NULL in the projection. The judgement bucket tracks judgement_start_date + the to_judgement_days countdown, not a window end. Verified NULL across all prod rows.

### 26. Sale start date  (`bpms.sync_fcl_stage_info.sale_start_date`)

_Stage start date._

**Source (L1)**
- Newrez: `newrez.portnewrezfc.fcscheduledsaledate`
- Carrington: `carrington.portcarrington.fcl_scheduled_sale_date`
- Capecodfive: `capecodfive.portcapecodfive_monthly_collections.foreclosure_date_sale_scheduled`

**Flow:** ①basic_data_loan_fcl → ②fcl_stage_info → ③sync_fcl_stage_info
**Lineage (per hop: # column — rule [code])**
- 1. `port.basic_data_loan_fcl.fcscheduled_sale_date` — source 源
- 2. `port.fcl_stage_info.sale_start_date` — passthrough of source sale_start_date [pool:2090,2391](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L2090)
- 3. `bpms.sync_fcl_stage_info.sale_start_date` — sync passthrough [asset:925](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L925)

```sql
sale_start_date = passthrough of business_1.sale_start_date (no transform)
```
🔎 **How it works:** Direct passthrough of the source milestone date `sale_start_date`; no transform. NULL if the loan never reached this stage.
▶ **Example:** 7727001179: sale_start_date 2026-06-23 ⇒ sale_start_date = 2026-06-23.

### 27. Sale window end  (`bpms.sync_fcl_stage_info.sale_end_date`)

_Sale window end (always NULL; bucket uses to_sale_days)._

**Source (L1)**
- Newrez: `newrez.portnewrezfc`  (Newrez-only detail)

**Flow:** ①portnewrezfc → ②basic_data_loan_fcl → ③fcl_stage_info → ④sync_fcl_stage_info
**Lineage (per hop: # column — rule [code])**
- 1. `newrez.portnewrezfc` — —
- 2. `port.basic_data_loan_fcl` · (stage end) — source 源
- 3. `port.fcl_stage_info.sale_end_date` — NULL (bucket uses to_sale_days) [pool:2392](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L2392)
- 4. `bpms.sync_fcl_stage_info.sale_end_date` — sync passthrough [asset:925](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L925)

**Note:** Hardcoded NULL in the projection. The sale bucket uses sale_start_date + the to_sale_days countdown. Verified NULL across all prod rows.


## Stage day counts

### 28. Demand days in stage  (`bpms.sync_fcl_stage_info.demand_stage_days`)

_Inclusive days elapsed in the stage._

**Source (L1)**
- Newrez: `newrez.portnewrezfc`  (Newrez-only detail)

**Flow:** ①portnewrezfc → ②basic_data_loan_fcl → ③fcl_stage_info → ④sync_fcl_stage_info
**Lineage (per hop: # column — rule [code])**
- 1. `newrez.portnewrezfc` — —
- 2. `port.basic_data_loan_fcl` · (stage dates) — source 源
- 3. `port.fcl_stage_info.demand_stage_days` — datediff+1 (inclusive) 见 sql [pool:2040-2076](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L2040-2076)
- 4. `bpms.sync_fcl_stage_info.demand_stage_days` — sync passthrough [asset:925](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L925)

```sql
demand_stage_days = datediff(day, demand_start_date, curr_date) + 1
-- demand stage is special: ignores demand_end_date, always counts to curr_date
```
🔎 **How it works:** Demand is special — it **always counts to today (curr_date)** and does NOT use demand_end_date (= demandexpirationdate) as the right edge [pool:2039-2041]. Formula: `demand_stage_days = datediff(demand_start_date, curr_date) + 1`.
▶ **Example (with full math)** 700082880000091: demand_start_date = 2025-12-29 (passthrough of `newrez.demandsentdate`), curr_date = 2026-06-09 (ETL run date)
> ⇒ demand_stage_days = datediff(2025-12-29, 2026-06-09) + 1 = 162 + 1 = **163** (matches prod).
> Note: this loan's demand_end_date = 2026-01-13 is **NOT used** in the day-count — it is only the documented window's right edge.

### 29. Demand days in LM  (`bpms.sync_fcl_stage_info.demand_in_lm_days`)

_Days in the stage overlapping an open LM cycle._

**Source (L1)**
- Newrez: `newrez.portnewrezfc`  (Newrez-only detail)

**Flow:** ①portnewrezfc → ②basic_data_loan_fcl → ③fcl_stage_info → ④sync_fcl_stage_info
**Lineage (per hop: # column — rule [code])**
- 1. `newrez.portnewrezfc` — —
- 2. `port.basic_data_loan_fcl` · (LM cycle) — source 源
- 3. `port.fcl_stage_info.demand_in_lm_days` — interval overlap (LM) 见 sql [pool:2246-2330](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L2246-2330)
- 4. `bpms.sync_fcl_stage_info.demand_in_lm_days` — sync passthrough [asset:925](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L925)

```sql
in_lm = datediff(greatest(stage_start, cycle_opened_date), least(stage_end, coalesce(cycle_closed_date,curr_date))) + 1; only open cycles; pivoted per stage with max()
```
🔎 **How it works:** Days of the stage window overlapping an OPEN loss-mitigation cycle: datediff(greatest(stage_start, cycle_opened), least(stage_end, coalesce(cycle_closed, today)))+1; only open cycles; computed per stage then max().
▶ **Example:** 7727000569: the Service stage overlaps an open LM cycle ⇒ service_in_lm_days = 185 (prod).

### 30. Demand days on hold  (`bpms.sync_fcl_stage_info.demand_on_hold_days`)

_Days in the stage overlapping an open hold._

**Source (L1)**
- Newrez: `newrez.portnewrezfc`  (Newrez-only detail)

**Flow:** ①portnewrezfc → ②basic_data_loan_fcl → ③fcl_stage_info → ④sync_fcl_stage_info
**Lineage (per hop: # column — rule [code])**
- 1. `newrez.portnewrezfc` — —
- 2. `port.basic_data_loan_fcl.fchold1..3` — source 源
- 3. `port.fcl_stage_info.demand_on_hold_days` — interval overlap (Hold) 见 sql [pool:2215-2297](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L2215-2297)
- 4. `bpms.sync_fcl_stage_info.demand_on_hold_days` — sync passthrough [asset:925](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L925)

```sql
on_hold = datediff(greatest(stage_start, hold_start), least(stage_end, coalesce(hold_end,curr_date))) + 1; only open holds (fchold1..3 of basic_data_loan_fcl); pivoted per stage
```
🔎 **How it works:** Days of the stage window overlapping an OPEN hold (fchold1..3 of basic_data_loan_fcl): datediff(greatest(stage_start, hold_start), least(stage_end, coalesce(hold_end, today)))+1; per stage then max().
▶ **Example:** 7727000569: the Service stage ∩ an open hold ⇒ service_on_hold_days = 87 (prod).

### 31. NOI days in LM  (`bpms.sync_fcl_stage_info.noi_in_lm_days`)

_Days in the stage overlapping an open LM cycle._

**Source (L1)**
- Newrez: `newrez.portnewrezfc`  (Newrez-only detail)

**Flow:** ①portnewrezfc → ②basic_data_loan_fcl → ③fcl_stage_info → ④sync_fcl_stage_info
**Lineage (per hop: # column — rule [code])**
- 1. `newrez.portnewrezfc` — —
- 2. `port.basic_data_loan_fcl` · (LM cycle) — source 源
- 3. `port.fcl_stage_info.noi_in_lm_days` — interval overlap (LM) 见 sql [pool:2246-2330](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L2246-2330)
- 4. `bpms.sync_fcl_stage_info.noi_in_lm_days` — sync passthrough [asset:925](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L925)

```sql
in_lm = datediff(greatest(stage_start, cycle_opened_date), least(stage_end, coalesce(cycle_closed_date,curr_date))) + 1; only open cycles; pivoted per stage with max()
```
🔎 **How it works:** Days of the stage window overlapping an OPEN loss-mitigation cycle: datediff(greatest(stage_start, cycle_opened), least(stage_end, coalesce(cycle_closed, today)))+1; only open cycles; computed per stage then max().
▶ **Example:** 7727000569: the Service stage overlaps an open LM cycle ⇒ service_in_lm_days = 185 (prod).

### 32. NOI days on hold  (`bpms.sync_fcl_stage_info.noi_on_hold_days`)

_Days in the stage overlapping an open hold._

**Source (L1)**
- Newrez: `newrez.portnewrezfc`  (Newrez-only detail)

**Flow:** ①portnewrezfc → ②basic_data_loan_fcl → ③fcl_stage_info → ④sync_fcl_stage_info
**Lineage (per hop: # column — rule [code])**
- 1. `newrez.portnewrezfc` — —
- 2. `port.basic_data_loan_fcl.fchold1..3` — source 源
- 3. `port.fcl_stage_info.noi_on_hold_days` — interval overlap (Hold) 见 sql [pool:2215-2297](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L2215-2297)
- 4. `bpms.sync_fcl_stage_info.noi_on_hold_days` — sync passthrough [asset:925](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L925)

```sql
on_hold = datediff(greatest(stage_start, hold_start), least(stage_end, coalesce(hold_end,curr_date))) + 1; only open holds (fchold1..3 of basic_data_loan_fcl); pivoted per stage
```
🔎 **How it works:** Days of the stage window overlapping an OPEN hold (fchold1..3 of basic_data_loan_fcl): datediff(greatest(stage_start, hold_start), least(stage_end, coalesce(hold_end, today)))+1; per stage then max().
▶ **Example:** 7727000569: the Service stage ∩ an open hold ⇒ service_on_hold_days = 87 (prod).

### 33. Referral days in stage  (`bpms.sync_fcl_stage_info.referral_stage_days`)

_Inclusive days elapsed in the stage._

**Source (L1)**
- Newrez: `newrez.portnewrezfc`  (Newrez-only detail)

**Flow:** ①portnewrezfc → ②basic_data_loan_fcl → ③fcl_stage_info → ④sync_fcl_stage_info
**Lineage (per hop: # column — rule [code])**
- 1. `newrez.portnewrezfc` — —
- 2. `port.basic_data_loan_fcl` · (stage dates) — source 源
- 3. `port.fcl_stage_info.referral_stage_days` — datediff+1 (inclusive) 见 sql [pool:2040-2076](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L2040-2076)
- 4. `bpms.sync_fcl_stage_info.referral_stage_days` — sync passthrough [asset:925](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L925)

```sql
referral_stage_days = datediff(day, referral_start_date, COALESCE(first_legal_start_date, curr_date)) + 1
-- end = next stage (first_legal) start; if not started, use curr_date
```
🔎 **How it works:** Referral's right edge: **end = COALESCE(first_legal_start_date, curr_date)** — once first-legal has started, use that date as the right edge; otherwise count to today [pool:2050-2052]. Formula: `referral_stage_days = datediff(referral_start_date, COALESCE(first_legal_start_date, curr_date)) + 1`.
▶ **Example (with full math)**
> ① Next stage reached — 7727004408: referral_start_date = 2024-03-08 (passthrough of `newrez.fcreferraldate`), first_legal_start_date = 2025-07-28
> ⇒ referral_stage_days = datediff(2024-03-08, 2025-07-28) + 1 = 507 + 1 = **508** (matches prod).
>
> ② Still in REFERRAL (first_legal not started) — 700082700000033: referral_start_date = 2026-02-11, first_legal_start_date = NULL ⇒ end = curr_date = 2026-06-09
> ⇒ referral_stage_days = datediff(2026-02-11, 2026-06-09) + 1 = 118 + 1 = **119** (matches prod).

### 34. Referral days in LM  (`bpms.sync_fcl_stage_info.referral_in_lm_days`)

_Days in the stage overlapping an open LM cycle._

**Source (L1)**
- Newrez: `newrez.portnewrezfc`  (Newrez-only detail)

**Flow:** ①portnewrezfc → ②basic_data_loan_fcl → ③fcl_stage_info → ④sync_fcl_stage_info
**Lineage (per hop: # column — rule [code])**
- 1. `newrez.portnewrezfc` — —
- 2. `port.basic_data_loan_fcl` · (LM cycle) — source 源
- 3. `port.fcl_stage_info.referral_in_lm_days` — interval overlap (LM) 见 sql [pool:2246-2330](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L2246-2330)
- 4. `bpms.sync_fcl_stage_info.referral_in_lm_days` — sync passthrough [asset:925](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L925)

```sql
in_lm = datediff(greatest(stage_start, cycle_opened_date), least(stage_end, coalesce(cycle_closed_date,curr_date))) + 1; only open cycles; pivoted per stage with max()
```
🔎 **How it works:** Days of the stage window overlapping an OPEN loss-mitigation cycle: datediff(greatest(stage_start, cycle_opened), least(stage_end, coalesce(cycle_closed, today)))+1; only open cycles; computed per stage then max().
▶ **Example:** 7727000569: the Service stage overlaps an open LM cycle ⇒ service_in_lm_days = 185 (prod).

### 35. Referral days on hold  (`bpms.sync_fcl_stage_info.referral_on_hold_days`)

_Days in the stage overlapping an open hold._

**Source (L1)**
- Newrez: `newrez.portnewrezfc`  (Newrez-only detail)

**Flow:** ①portnewrezfc → ②basic_data_loan_fcl → ③fcl_stage_info → ④sync_fcl_stage_info
**Lineage (per hop: # column — rule [code])**
- 1. `newrez.portnewrezfc` — —
- 2. `port.basic_data_loan_fcl.fchold1..3` — source 源
- 3. `port.fcl_stage_info.referral_on_hold_days` — interval overlap (Hold) 见 sql [pool:2215-2297](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L2215-2297)
- 4. `bpms.sync_fcl_stage_info.referral_on_hold_days` — sync passthrough [asset:925](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L925)

```sql
on_hold = datediff(greatest(stage_start, hold_start), least(stage_end, coalesce(hold_end,curr_date))) + 1; only open holds (fchold1..3 of basic_data_loan_fcl); pivoted per stage
```
🔎 **How it works:** Days of the stage window overlapping an OPEN hold (fchold1..3 of basic_data_loan_fcl): datediff(greatest(stage_start, hold_start), least(stage_end, coalesce(hold_end, today)))+1; per stage then max().
▶ **Example:** 7727000569: the Service stage ∩ an open hold ⇒ service_on_hold_days = 87 (prod).

### 36. First Legal days in stage  (`bpms.sync_fcl_stage_info.first_legal_stage_days`)

_Inclusive days elapsed in the stage._

**Source (L1)**
- Newrez: `newrez.portnewrezfc`  (Newrez-only detail)

**Flow:** ①portnewrezfc → ②basic_data_loan_fcl → ③fcl_stage_info → ④sync_fcl_stage_info
**Lineage (per hop: # column — rule [code])**
- 1. `newrez.portnewrezfc` — —
- 2. `port.basic_data_loan_fcl` · (stage dates) — source 源
- 3. `port.fcl_stage_info.first_legal_stage_days` — datediff+1 (inclusive) 见 sql [pool:2040-2076](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L2040-2076)
- 4. `bpms.sync_fcl_stage_info.first_legal_stage_days` — sync passthrough [asset:925](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L925)

```sql
first_legal_stage_days = datediff(day, first_legal_start_date, COALESCE(service_start_date, curr_date)) + 1
-- end = next stage (service) start; if not started, use curr_date
```
🔎 **How it works:** First-legal's right edge: **end = COALESCE(service_start_date, curr_date)** [pool:2060-2062]. Formula: `first_legal_stage_days = datediff(first_legal_start_date, COALESCE(service_start_date, curr_date)) + 1`.
▶ **Example (with full math)**
> ① Next stage reached — 7727004408: first_legal_start_date = 2025-07-28 (passthrough of `newrez.firstlegaldate`), service_start_date = 2026-02-16
> ⇒ first_legal_stage_days = datediff(2025-07-28, 2026-02-16) + 1 = 203 + 1 = **204** (matches prod).
>
> ② Another — 700082880000091: first_legal_start_date = 2026-03-12, service_start_date = 2026-05-13
> ⇒ first_legal_stage_days = datediff(2026-03-12, 2026-05-13) + 1 = 62 + 1 = **63** (matches prod).

### 37. First Legal days in LM  (`bpms.sync_fcl_stage_info.first_legal_in_lm_days`)

_Days in the stage overlapping an open LM cycle._

**Source (L1)**
- Newrez: `newrez.portnewrezfc`  (Newrez-only detail)

**Flow:** ①portnewrezfc → ②basic_data_loan_fcl → ③fcl_stage_info → ④sync_fcl_stage_info
**Lineage (per hop: # column — rule [code])**
- 1. `newrez.portnewrezfc` — —
- 2. `port.basic_data_loan_fcl` · (LM cycle) — source 源
- 3. `port.fcl_stage_info.first_legal_in_lm_days` — interval overlap (LM) 见 sql [pool:2246-2330](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L2246-2330)
- 4. `bpms.sync_fcl_stage_info.first_legal_in_lm_days` — sync passthrough [asset:925](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L925)

```sql
in_lm = datediff(greatest(stage_start, cycle_opened_date), least(stage_end, coalesce(cycle_closed_date,curr_date))) + 1; only open cycles; pivoted per stage with max()
```
🔎 **How it works:** Days of the stage window overlapping an OPEN loss-mitigation cycle: datediff(greatest(stage_start, cycle_opened), least(stage_end, coalesce(cycle_closed, today)))+1; only open cycles; computed per stage then max().
▶ **Example:** 7727000569: the Service stage overlaps an open LM cycle ⇒ service_in_lm_days = 185 (prod).

### 38. First Legal days on hold  (`bpms.sync_fcl_stage_info.first_legal_on_hold_days`)

_Days in the stage overlapping an open hold._

**Source (L1)**
- Newrez: `newrez.portnewrezfc`  (Newrez-only detail)

**Flow:** ①portnewrezfc → ②basic_data_loan_fcl → ③fcl_stage_info → ④sync_fcl_stage_info
**Lineage (per hop: # column — rule [code])**
- 1. `newrez.portnewrezfc` — —
- 2. `port.basic_data_loan_fcl.fchold1..3` — source 源
- 3. `port.fcl_stage_info.first_legal_on_hold_days` — interval overlap (Hold) 见 sql [pool:2215-2297](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L2215-2297)
- 4. `bpms.sync_fcl_stage_info.first_legal_on_hold_days` — sync passthrough [asset:925](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L925)

```sql
on_hold = datediff(greatest(stage_start, hold_start), least(stage_end, coalesce(hold_end,curr_date))) + 1; only open holds (fchold1..3 of basic_data_loan_fcl); pivoted per stage
```
🔎 **How it works:** Days of the stage window overlapping an OPEN hold (fchold1..3 of basic_data_loan_fcl): datediff(greatest(stage_start, hold_start), least(stage_end, coalesce(hold_end, today)))+1; per stage then max().
▶ **Example:** 7727000569: the Service stage ∩ an open hold ⇒ service_on_hold_days = 87 (prod).

### 39. Service days in stage  (`bpms.sync_fcl_stage_info.service_stage_days`)

_Inclusive days elapsed in the stage._

**Source (L1)**
- Newrez: `newrez.portnewrezfc`  (Newrez-only detail)

**Flow:** ①portnewrezfc → ②basic_data_loan_fcl → ③fcl_stage_info → ④sync_fcl_stage_info
**Lineage (per hop: # column — rule [code])**
- 1. `newrez.portnewrezfc` — —
- 2. `port.basic_data_loan_fcl` · (stage dates) — source 源
- 3. `port.fcl_stage_info.service_stage_days` — datediff+1 (inclusive) 见 sql [pool:2040-2076](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L2040-2076)
- 4. `bpms.sync_fcl_stage_info.service_stage_days` — sync passthrough [asset:925](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L925)

```sql
service_stage_days = datediff(day, service_start_date, COALESCE(judgment_available_date, curr_date)) + 1
-- end = judgment_available_date; if not reached, use curr_date
```
🔎 **How it works:** Service's right edge: **end = COALESCE(judgment_available_date, curr_date)** [pool:2070-2072]. Formula: `service_stage_days = datediff(service_start_date, COALESCE(judgment_available_date, curr_date)) + 1`.
▶ **Example (with full math)**
> ① Next stage reached — 7727000357: service_start_date = 2025-08-14 (passthrough of `newrez.servicecompletedate`), judgment_available_date = 2026-01-26
> ⇒ service_stage_days = datediff(2025-08-14, 2026-01-26) + 1 = 165 + 1 = **166** (matches prod).
>
> ② Still in SERVICE (judgement not reached) — 700082880000091 (current stage = SERVICE): service_start_date = 2026-05-13, judgment_available_date = NULL ⇒ end = curr_date = 2026-06-09
> ⇒ service_stage_days = datediff(2026-05-13, 2026-06-09) + 1 = 27 + 1 = **28** (curr_date = ETL run date; matches prod).

### 40. Service days in LM  (`bpms.sync_fcl_stage_info.service_in_lm_days`)

_Days in the stage overlapping an open LM cycle._

**Source (L1)**
- Newrez: `newrez.portnewrezfc`  (Newrez-only detail)

**Flow:** ①portnewrezfc → ②basic_data_loan_fcl → ③fcl_stage_info → ④sync_fcl_stage_info
**Lineage (per hop: # column — rule [code])**
- 1. `newrez.portnewrezfc` — —
- 2. `port.basic_data_loan_fcl` · (LM cycle) — source 源
- 3. `port.fcl_stage_info.service_in_lm_days` — interval overlap (LM) 见 sql [pool:2246-2330](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L2246-2330)
- 4. `bpms.sync_fcl_stage_info.service_in_lm_days` — sync passthrough [asset:925](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L925)

```sql
in_lm = datediff(greatest(stage_start, cycle_opened_date), least(stage_end, coalesce(cycle_closed_date,curr_date))) + 1; only open cycles; pivoted per stage with max()
```
🔎 **How it works:** Days of the stage window overlapping an OPEN loss-mitigation cycle: datediff(greatest(stage_start, cycle_opened), least(stage_end, coalesce(cycle_closed, today)))+1; only open cycles; computed per stage then max().
▶ **Example:** 7727000569: the Service stage overlaps an open LM cycle ⇒ service_in_lm_days = 185 (prod).

### 41. Service days on hold  (`bpms.sync_fcl_stage_info.service_on_hold_days`)

_Days in the stage overlapping an open hold._

**Source (L1)**
- Newrez: `newrez.portnewrezfc`  (Newrez-only detail)

**Flow:** ①portnewrezfc → ②basic_data_loan_fcl → ③fcl_stage_info → ④sync_fcl_stage_info
**Lineage (per hop: # column — rule [code])**
- 1. `newrez.portnewrezfc` — —
- 2. `port.basic_data_loan_fcl.fchold1..3` — source 源
- 3. `port.fcl_stage_info.service_on_hold_days` — interval overlap (Hold) 见 sql [pool:2215-2297](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L2215-2297)
- 4. `bpms.sync_fcl_stage_info.service_on_hold_days` — sync passthrough [asset:925](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L925)

```sql
on_hold = datediff(greatest(stage_start, hold_start), least(stage_end, coalesce(hold_end,curr_date))) + 1; only open holds (fchold1..3 of basic_data_loan_fcl); pivoted per stage
```
🔎 **How it works:** Days of the stage window overlapping an OPEN hold (fchold1..3 of basic_data_loan_fcl): datediff(greatest(stage_start, hold_start), least(stage_end, coalesce(hold_end, today)))+1; per stage then max().
▶ **Example:** 7727000569: the Service stage ∩ an open hold ⇒ service_on_hold_days = 87 (prod).

### 42. Publication days in LM  (`bpms.sync_fcl_stage_info.publication_in_lm_days`)

_Days in the stage overlapping an open LM cycle._

**Source (L1)**
- Newrez: `newrez.portnewrezfc`  (Newrez-only detail)

**Flow:** ①portnewrezfc → ②basic_data_loan_fcl → ③fcl_stage_info → ④sync_fcl_stage_info
**Lineage (per hop: # column — rule [code])**
- 1. `newrez.portnewrezfc` — —
- 2. `port.basic_data_loan_fcl` · (LM cycle) — source 源
- 3. `port.fcl_stage_info.publication_in_lm_days` — interval overlap (LM) 见 sql [pool:2246-2330](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L2246-2330)
- 4. `bpms.sync_fcl_stage_info.publication_in_lm_days` — sync passthrough [asset:925](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L925)

```sql
in_lm = datediff(greatest(stage_start, cycle_opened_date), least(stage_end, coalesce(cycle_closed_date,curr_date))) + 1; only open cycles; pivoted per stage with max()
```
🔎 **How it works:** Days of the stage window overlapping an OPEN loss-mitigation cycle: datediff(greatest(stage_start, cycle_opened), least(stage_end, coalesce(cycle_closed, today)))+1; only open cycles; computed per stage then max().
▶ **Example:** 7727000569: the Service stage overlaps an open LM cycle ⇒ service_in_lm_days = 185 (prod).

### 43. Publication days on hold  (`bpms.sync_fcl_stage_info.publication_on_hold_days`)

_Days in the stage overlapping an open hold._

**Source (L1)**
- Newrez: `newrez.portnewrezfc`  (Newrez-only detail)

**Flow:** ①portnewrezfc → ②basic_data_loan_fcl → ③fcl_stage_info → ④sync_fcl_stage_info
**Lineage (per hop: # column — rule [code])**
- 1. `newrez.portnewrezfc` — —
- 2. `port.basic_data_loan_fcl.fchold1..3` — source 源
- 3. `port.fcl_stage_info.publication_on_hold_days` — interval overlap (Hold) 见 sql [pool:2215-2297](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L2215-2297)
- 4. `bpms.sync_fcl_stage_info.publication_on_hold_days` — sync passthrough [asset:925](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L925)

```sql
on_hold = datediff(greatest(stage_start, hold_start), least(stage_end, coalesce(hold_end,curr_date))) + 1; only open holds (fchold1..3 of basic_data_loan_fcl); pivoted per stage
```
🔎 **How it works:** Days of the stage window overlapping an OPEN hold (fchold1..3 of basic_data_loan_fcl): datediff(greatest(stage_start, hold_start), least(stage_end, coalesce(hold_end, today)))+1; per stage then max().
▶ **Example:** 7727000569: the Service stage ∩ an open hold ⇒ service_on_hold_days = 87 (prod).

### 44. Days to judgement  (`bpms.sync_fcl_stage_info.to_judgement_days`)

_Forward countdown to the scheduled judgement/sale._

**Source (L1)**
- Newrez: `newrez.portnewrezfc.fcjudgmenthearingscheduled`  (Newrez-only detail)

**Flow:** ①portnewrezfc → ②basic_data_loan_fcl → ③fcl_stage_info → ④sync_fcl_stage_info
**Lineage (per hop: # column — rule [code])**
- 1. `newrez.portnewrezfc.fcjudgmenthearingscheduled` — servicer raw 原始
- 2. `port.basic_data_loan_fcl.fcjudgment_hearing_scheduled` — source 源
- 3. `port.fcl_stage_info.to_judgement_days` — countdown to judgement: future⇒datediff(curr_date, date) (no +1), past⇒0, none⇒NULL [pool:2085-2087,2388](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L2085-2087)
- 4. `bpms.sync_fcl_stage_info.to_judgement_days` — sync passthrough [asset:925](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L925)

```sql
case when fcjudgment_start_date is null then null when fcjudgment_start_date >= curr_date then datediff(day, curr_date, fcjudgment_start_date) else 0 end
```
🔎 **How it works:** Forward countdown of days from the current date (curr_date, NY) to the scheduled judgement date — NO +1. Three branches: future date ⇒ datediff(curr_date, judgement_date); past date ⇒ 0 (floored); no date ⇒ NULL.
▶ **Example:** ① future — 7727004408: judgement 2026-08-21 ⇒ to_judgement_days = 73 (datediff(2026-06-09,2026-08-21)). ② past — 7727001179: judgement 2025-11-29 (already passed) ⇒ 0. ③ no date ⇒ NULL.

### 45. Judgement days in LM  (`bpms.sync_fcl_stage_info.judgement_in_lm_days`)

_Days in the stage overlapping an open LM cycle._

**Source (L1)**
- Newrez: `newrez.portnewrezfc`  (Newrez-only detail)

**Flow:** ①portnewrezfc → ②basic_data_loan_fcl → ③fcl_stage_info → ④sync_fcl_stage_info
**Lineage (per hop: # column — rule [code])**
- 1. `newrez.portnewrezfc` — —
- 2. `port.basic_data_loan_fcl` · (LM cycle) — source 源
- 3. `port.fcl_stage_info.judgement_in_lm_days` — interval overlap (LM) 见 sql [pool:2246-2330](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L2246-2330)
- 4. `bpms.sync_fcl_stage_info.judgement_in_lm_days` — sync passthrough [asset:925](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L925)

```sql
in_lm = datediff(greatest(stage_start, cycle_opened_date), least(stage_end, coalesce(cycle_closed_date,curr_date))) + 1; only open cycles; pivoted per stage with max()
```
🔎 **How it works:** Days of the stage window overlapping an OPEN loss-mitigation cycle: datediff(greatest(stage_start, cycle_opened), least(stage_end, coalesce(cycle_closed, today)))+1; only open cycles; computed per stage then max().
▶ **Example:** 7727000569: the Service stage overlaps an open LM cycle ⇒ service_in_lm_days = 185 (prod).

### 46. Judgement days on hold  (`bpms.sync_fcl_stage_info.judgement_on_hold_days`)

_Days in the stage overlapping an open hold._

**Source (L1)**
- Newrez: `newrez.portnewrezfc`  (Newrez-only detail)

**Flow:** ①portnewrezfc → ②basic_data_loan_fcl → ③fcl_stage_info → ④sync_fcl_stage_info
**Lineage (per hop: # column — rule [code])**
- 1. `newrez.portnewrezfc` — —
- 2. `port.basic_data_loan_fcl.fchold1..3` — source 源
- 3. `port.fcl_stage_info.judgement_on_hold_days` — interval overlap (Hold) 见 sql [pool:2215-2297](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L2215-2297)
- 4. `bpms.sync_fcl_stage_info.judgement_on_hold_days` — sync passthrough [asset:925](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L925)

```sql
on_hold = datediff(greatest(stage_start, hold_start), least(stage_end, coalesce(hold_end,curr_date))) + 1; only open holds (fchold1..3 of basic_data_loan_fcl); pivoted per stage
```
🔎 **How it works:** Days of the stage window overlapping an OPEN hold (fchold1..3 of basic_data_loan_fcl): datediff(greatest(stage_start, hold_start), least(stage_end, coalesce(hold_end, today)))+1; per stage then max().
▶ **Example:** 7727000569: the Service stage ∩ an open hold ⇒ service_on_hold_days = 87 (prod).

### 47. Days to sale  (`bpms.sync_fcl_stage_info.to_sale_days`)

_Forward countdown to the scheduled judgement/sale._

**Source (L1)**
- Newrez: `newrez.portnewrezfc.fcscheduledsaledate`  (Newrez-only detail)

**Flow:** ①portnewrezfc → ②basic_data_loan_fcl → ③fcl_stage_info → ④sync_fcl_stage_info
**Lineage (per hop: # column — rule [code])**
- 1. `newrez.portnewrezfc.fcscheduledsaledate` — servicer raw 原始
- 2. `port.basic_data_loan_fcl.fcscheduled_sale_date` — source 源
- 3. `port.fcl_stage_info.to_sale_days` — countdown to sale: future⇒datediff(curr_date, date) (no +1), past⇒0, none⇒NULL [pool:2091-2093,2393](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L2091-2093)
- 4. `bpms.sync_fcl_stage_info.to_sale_days` — sync passthrough [asset:925](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L925)

```sql
case when sale_start_date is null then null when sale_start_date >= curr_date then datediff(day, curr_date, sale_start_date) else 0 end
```
🔎 **How it works:** Forward countdown of days from the current date (curr_date, NY) to the scheduled sale date — NO +1. Three branches: future date ⇒ datediff(curr_date, sale_date); past date ⇒ 0; no date ⇒ NULL.
▶ **Example:** ① future — 7727001179: sale 2026-06-23 ⇒ to_sale_days = 14 (datediff(2026-06-09,2026-06-23), no +1). ② past — a sale date already passed ⇒ 0. ③ no date ⇒ NULL.

### 48. Sale days in LM  (`bpms.sync_fcl_stage_info.sale_in_lm_days`)

_Days in the stage overlapping an open LM cycle._

**Source (L1)**
- Newrez: `newrez.portnewrezfc`  (Newrez-only detail)

**Flow:** ①portnewrezfc → ②basic_data_loan_fcl → ③fcl_stage_info → ④sync_fcl_stage_info
**Lineage (per hop: # column — rule [code])**
- 1. `newrez.portnewrezfc` — —
- 2. `port.basic_data_loan_fcl` · (LM cycle) — source 源
- 3. `port.fcl_stage_info.sale_in_lm_days` — interval overlap (LM) 见 sql [pool:2246-2330](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L2246-2330)
- 4. `bpms.sync_fcl_stage_info.sale_in_lm_days` — sync passthrough [asset:925](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L925)

```sql
in_lm = datediff(greatest(stage_start, cycle_opened_date), least(stage_end, coalesce(cycle_closed_date,curr_date))) + 1; only open cycles; pivoted per stage with max()
```
🔎 **How it works:** Days of the stage window overlapping an OPEN loss-mitigation cycle: datediff(greatest(stage_start, cycle_opened), least(stage_end, coalesce(cycle_closed, today)))+1; only open cycles; computed per stage then max().
▶ **Example:** 7727000569: the Service stage overlaps an open LM cycle ⇒ service_in_lm_days = 185 (prod).

### 49. Sale days on hold  (`bpms.sync_fcl_stage_info.sale_on_hold_days`)

_Days in the stage overlapping an open hold._

**Source (L1)**
- Newrez: `newrez.portnewrezfc`  (Newrez-only detail)

**Flow:** ①portnewrezfc → ②basic_data_loan_fcl → ③fcl_stage_info → ④sync_fcl_stage_info
**Lineage (per hop: # column — rule [code])**
- 1. `newrez.portnewrezfc` — —
- 2. `port.basic_data_loan_fcl.fchold1..3` — source 源
- 3. `port.fcl_stage_info.sale_on_hold_days` — interval overlap (Hold) 见 sql [pool:2215-2297](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L2215-2297)
- 4. `bpms.sync_fcl_stage_info.sale_on_hold_days` — sync passthrough [asset:925](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L925)

```sql
on_hold = datediff(greatest(stage_start, hold_start), least(stage_end, coalesce(hold_end,curr_date))) + 1; only open holds (fchold1..3 of basic_data_loan_fcl); pivoted per stage
```
🔎 **How it works:** Days of the stage window overlapping an OPEN hold (fchold1..3 of basic_data_loan_fcl): datediff(greatest(stage_start, hold_start), least(stage_end, coalesce(hold_end, today)))+1; per stage then max().
▶ **Example:** 7727000569: the Service stage ∩ an open hold ⇒ service_on_hold_days = 87 (prod).


## System / audit columns

### 50. System / audit columns

_App/ETL-managed columns (not servicer-sourced)._

**Columns:** `create_time, update_time, create_user, create_dept, update_user, status, is_deleted, tenant_id`

**Note:** Columns: create_time, update_time, create_user, create_dept, update_user, status, is_deleted, tenant_id. tenant_id ← GET_LOAN_TENANT_ID(portfunding ⋈ basic_data_trust_funding, [asset:932-936](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L932-936)); create_*/update_* set by the BPS app; is_deleted constant 0 (view); status app flag. Not servicer data.


> This doc covers 50 fields.
