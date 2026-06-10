# doc 22 — BPS Foreclosure "Time Line / Stage" Aggregate Page: Data Sourcing Rules

---

## Document Information

| Field | Content |
|-------|---------|
| **Purpose** | The BPS Asset Management → Portfolio → **Foreclosure** aggregate page (`/#/portfolio/agg-summary`) has two tabs — **Stage** and **Time Line** — plus a top **Overview** summary. This doc answers a set of confusions about the Time Line tab: it shows one row per loan yet lists *many* loans (so it is not "one loan's timeline"); how does it relate to the Stage tab; which table feeds it and what does the query look like; and — **"the sync tables hold a loan's *current* state, so where do the historical milestone dates in the timeline come from?"** |
| **Problem solved** | Pins down the single source table, the column-level mapping, the current-state-vs-history semantics, and gives runnable representative SQL plus a sample-loan walk-through. |
| **Scope** | ✅ The Foreclosure module of the agg-summary page (Stage tab / Time Line tab / Overview): source table, column map, query rules, history semantics. ❌ Not the BPS loan-**detail** Foreclosure panel (that is `sync_loan_foreclosure`, see doc 13/16); ❌ not BPS front-end rendering internals. |
| **System** | Source system `C:\Users\jli\MyData\Copilot\PrefectFlow` (Prefect 2.x ETL). This doc reverse-documents its L4→L5 foreclosure-stage path. |

**Target audience:** Primary — operations/asset-management analysts · BPS validators · data engineers. Secondary — onboarding engineers · future AI sessions.

**Revision history:**

| Date | Author | Version | Changes | Related |
|------|--------|---------|---------|---------|
| 2026-06-07 | AI Agent (Claude Opus 4.8) | v1 | Initial draft: Time Line/Stage sourced from `sync_fcl_stage_info` — sourcing rules, column map, current-vs-history, representative SQL, sample walk (code-read + prod `bpms` verified) | doc 02/12/13/16/21 |

**Related documents:**

| Doc | Note |
|-----|------|
| doc 02 | ETL 5-layer pipeline, as-of evolution (§8 current vs historical) |
| doc 12 | `sync_asset_management.py` sync orchestration, SYNC_TABLE_MAP |
| doc 13/16 | BPS panel field reverse mapping / quickref |
| doc 25–30 | FCL field-level lineage (per-table; stage system, days calculations) |
| doc 10 | Glossary (FCL/REO/LM/BK/delinq/fctrdt …) |

> Glossary: FCL=Foreclosure · REO=Real Estate Owned · LM=Loss Mitigation · BK=Bankruptcy · `fctrdt`=reporting/run cut-off date (snapshot date) · Servicer=loan servicer · BPS=downstream business system.

---

## §1 One-paragraph answer

> **The Time Line tab and the Stage tab read from the same table, `bpms.sync_fcl_stage_info`, filtered to the latest snapshot (`MAX(fctrdt)`), one row per loan.** What you see is not "one loan's timeline" but "the milestone dates of every foreclosure loan in the portfolio." A single loan's progression is encoded **horizontally as date columns** (NOI/Referral/First Legal/Service/Judgement/Sale), not as multiple rows. Stage tab and Time Line tab are **different columns of the same row**: Time Line shows each stage's `*_start_date`; Stage shows each stage's `*_stage_days / *_in_lm_days / *_on_hold_days` plus the current `stage`.

---

## §2 Source table & lineage

| Endpoint (BPS / MySQL) | Intermediate (Redshift) | Generating code |
|---|---|---|
| `bpms.sync_fcl_stage_info` | `port.fcl_stage_info` | Sync: `SYNC_TABLE_MAP['12-FCL_STAGE']` ([`flow/bps/bps_config/sync_to_bps_config.py:13`](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/sync_to_bps_config.py#L13)); build: `GEN_FCL_STAGE` ([`flow/basic_data/basic_data_config/basic_data_pool_config.py:2344-2440`](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L2344-2440)) |

- **`group`** (C/D30/D60/D90/D120P/FCL/REO/P) is computed by `CREATE_FCL_RELATE_ATTR` ([`basic_data_pool_config.py:1695-1771`](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L1695-1771)) from `newrez.portnewrezgeneral.delinquency_status_mba`, `carrington.portcarrington.loan_status`, etc.; FCL/REO/Full Payoff decided directly, the rest bucketed by `days360(nextduedate, dataasof)`.
- **`judicial`** (Y/N): takes source `fc.judicial` (1→Y, 0→N), else falls back to `port.basic_data_judicial_config` (joined on property state).
- Stage dates come from `tempfc.current_fcl_business_1_temp` and sibling temp tables, finally inserted into `port.fcl_stage_info` by `GEN_FCL_STAGE` (it does `delete ... where fctrdt = today` then `insert`, see [`basic_data_pool_config.py:2341-2344`](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L2341-2344)).

```
L1 newrez.portnewrezfc / portnewrezgeneral …   (source: daily snapshots)
        │  GEN_FCL_DETAIL / CREATE_FCL_RELATE_ATTR
        ▼
L4 port.basic_data_fcl_related (delq_status, state) + tempfc.current_fcl_business_1_temp (stage dates/days)
        │  GEN_FCL_STAGE  (basic_data_pool_config.py:2344)
        ▼
L4 port.fcl_stage_info   (one row = loanid + fctrdt)
        │  sync (12-FCL_STAGE)   sync_asset_management.py → sync_to_mysql
        ▼
L5 bpms.sync_fcl_stage_info  ←  agg-summary Stage / Time Line read from here
```

---

## §3 Column map (Time Line UI column ⇄ table column, verified)

| UI column | `sync_fcl_stage_info` column | Stage | Note |
|---|---|---|---|
| Loan ID / Group / Servicer / States / Judicial | `loanid` / `group` / `servicer` / `state` / `judicial` | — | Identity & classification |
| NOI Date 1 | `noi_start_date` | NOI | Always NULL for Newrez (no source field) |
| Referral Date 2 | `referral_start_date` | Referral | source `fcreferraldate`, BPS-entry prerequisite |
| First Legal Date 3 | `first_legal_start_date` | First Legal | source `firstlegaldate` |
| Service Date 4 | `service_start_date` | Service | source `servicecompletedate` |
| (Publication 5) | `publication_start_date` | Publication | Always NULL for Newrez |
| Judgement Date 6 | `judgement_start_date` | Judgement | source `fcjudgmenthearingscheduled` (hearing *scheduled* date, not court-entry date) |
| Sale Date 7 | `sale_start_date` | Sale | source `fcscheduledsaledate` |

> `sync_fcl_stage_info` has 57 columns total: besides the stage dates above, each stage also carries `*_end_date / *_stage_days / *_in_lm_days / *_on_hold_days` (for the Stage tab), plus `first_legal_date_history` (text), `stage` (current active stage), `fctrdt` (snapshot date), and audit columns.

---

## §4 Time Line vs Stage vs Overview — three views of one table

| View | Columns used | Meaning |
|---|---|---|
| **Time Line tab** | each stage's `*_start_date` | the milestone-date sequence of each loan, laid out horizontally |
| **Stage tab** | each stage's `*_stage_days` / `*_in_lm_days` / `*_on_hold_days` + `stage` | which stage the loan currently sits in, and time spent per stage (with LM/Hold carve-outs) |
| **Overview summary** | aggregate counts over `servicer` / `group` / `judicial` | per-servicer Loan Count, FC, D120P, Judicial/Non-Judicial counts |

- **Days in Stage** ≈ `datediff(stage_start, stage_end or today) + 1`; `*_in_lm_days` / `*_on_hold_days` are day carve-outs while the loan was in LM / Hold during that stage (see doc 27 stage system).
- These are **not three tables** — they are different projections/aggregations of `sync_fcl_stage_info` (latest snapshot).

---

## §5 The key confusion: "sync tables hold current state — so where is the history?"

Two layers:

1. **Milestones are columns, not rows.** A single loan's progression from demand → sale is encoded as multiple **event-date columns** on one row (`referral_start_date`, `first_legal_start_date`, …). Once a stage date is written it **persists unchanged** — that *is* the loan's timeline; no history rows are needed to render the full progression.

2. **`sync_fcl_stage_info` actually does retain historical snapshots.** Unusually, it **keeps the `fctrdt` column** (snapshot date), so each loan has many rows (one per run day). Verified on prod `bpms`:

   | Metric | Value |
   |---|---|
   | Total rows | **8,368** |
   | Distinct loanid | **66** |
   | Distinct `fctrdt` | **300** (2025-06-03 → 2026-06-04, ~daily) |
   | Rows per loan | mostly **300** rows/loan |

   This contrasts with the main table `bpms.sync_loan_foreclosure`, which is **DELETE+APPEND overwrite-refreshed** to **1 row per loan (current state only)** (see `util/df_db_util.py` `sync_to_mysql`: `delete from {table}` then `to_sql(append)`; the FCL main table additionally upserts via `UPDATE_FORECLOSURE`'s `ON DUPLICATE KEY UPDATE`).

3. **The agg-summary page shows only the latest snapshot.** The page filters `sync_fcl_stage_info` to `fctrdt = MAX(fctrdt)`, giving "one row per loan." So Time Line shows many loans, one row each — the *latest* milestones of all foreclosure loans, not the multi-row history of a single loan. The historical snapshots exist in the table but the page does not expand them by default.

---

## §6 Representative SQL (page-equivalent queries)

```sql
-- Time Line tab: latest snapshot, one row per loan
SELECT loanid, `group`, servicer, state, judicial,
       noi_start_date, referral_start_date, first_legal_start_date,
       service_start_date, publication_start_date,
       judgement_start_date, sale_start_date
FROM bpms.sync_fcl_stage_info
WHERE fctrdt = (SELECT MAX(fctrdt) FROM bpms.sync_fcl_stage_info)
  AND is_deleted = 0
ORDER BY referral_start_date;     -- the UI "↑" arrows sort by that date column

-- Stage tab: same latest snapshot, day columns
SELECT loanid, `group`, servicer, stage,
       demand_stage_days, referral_stage_days, first_legal_stage_days,
       service_stage_days, to_judgement_days, to_sale_days
FROM bpms.sync_fcl_stage_info
WHERE fctrdt = (SELECT MAX(fctrdt) FROM bpms.sync_fcl_stage_info) AND is_deleted = 0;

-- Overview summary: counts by Servicer × group / judicial
SELECT servicer, `group`, judicial, COUNT(*) AS loans
FROM bpms.sync_fcl_stage_info
WHERE fctrdt = (SELECT MAX(fctrdt) FROM bpms.sync_fcl_stage_info) AND is_deleted = 0
GROUP BY servicer, `group`, judicial;
```

> To see a single loan's **historical evolution** (rather than the aggregate page's latest state), drop the `MAX(fctrdt)` filter and `ORDER BY fctrdt` — the table retains daily snapshots.

---

## §7 Sample walk-through: loan `7727000088` (prod `bpms`, verified)

Latest snapshot (`fctrdt = 2026-05-24`):

| Column | Value (DB, UTC) | BPS display (US-Eastern) |
|---|---|---|
| group / servicer / state / judicial | REO / Newrez / FL / Y | same |
| noi_start_date | NULL | (blank) |
| referral_start_date | 2025-05-22T16:00Z | **2025-05-23** |
| first_legal_start_date | 2025-06-12T16:00Z | **2025-06-13** |
| service_start_date | 2025-07-17T16:00Z | **2025-07-18** |
| judgement_start_date | 2026-03-26T16:00Z | 2026-03-27 |
| sale_start_date | NULL | (blank) |
| stage | JUDGEMENT | JUDGEMENT |

**Exact match to the screenshot** (Referral 2025-05-23 / First Legal 2025-06-13 / Service 2025-07-18).

> ⚠️ **Time zone**: date columns are stored as US-Eastern midnight in UTC (`T16:00Z`), so the UTC value read via MCP/DB displays as the **next day** in the BPS UI. Convert to US-Eastern before comparing.

> ⚠️ **Environment difference**: the DB figures here are from **prod `bpms`**; the screenshot is from **UAT** (`uat-bips`). The prod latest snapshot is Newrez 21 + Carrington 6 = 27 loans, slightly different from the screenshot (Newrez 26 + Carrington 5) — an environment data difference. The **loan-level milestones (7727000088) match column-for-column**, confirming the sourcing rule.
