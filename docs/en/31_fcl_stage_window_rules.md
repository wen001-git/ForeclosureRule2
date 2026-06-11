# doc 31 — FCL Stage Window Rules Cheat-sheet (start / end / days / in_lm / on_hold)

> <!-- RULEGLOSS_PTR -->📖 **Rule terms**: plain-language + formula for the technical phrases in the `rule` column — see [doc 25 · transform-rule glossary (appendix)](25_fcl_lineage_overview.md).

## Document Purpose

- **Why it exists**: `bpms.sync_fcl_stage_info` has 5 time-related columns per FCL stage (DEMAND / NOI / REFERRAL / FIRST_LEGAL / SERVICE / PUBLICATION / JUDGEMENT / SALE) — `<X>_start_date / <X>_end_date / <X>_stage_days / <X>_in_lm_days / <X>_on_hold_days`. Their rules are **scattered across 25+ sections of doc 27** (§9–§13 / §14–§23 / §28–§41), and the **column naming is counter-intuitive** (e.g. `servicecompletedate` actually feeds the SERVICE stage's **start**, not its end). New readers struggle to form a global picture.
- **What it solves**: a single cheat-sheet that lays out the rules for 8 stages × 5 column types in one read, with real-data worked examples and explicit pitfalls.
- **Scope**:
  - **In**: For each of 8 stages — `start_date` source, `end_date` derivation, `stage_days` formula; complete SQL semantics for `in_lm_days / on_hold_days` (Code-First from PrefectFlow pool:2215-2330).
  - **Out**: per-field hop-by-hop lineage (see doc 27); BPS view fields (doc 26); BPS UI mapping (doc 13/16).
- **System fit**: the **rules cheat-sheet entry-point** for the "stage / days" branch of the FCL lineage hub (doc 25); the **horizontal summary view** of doc 27.

## Target Audience

data engineers · business analysts · validators · onboarding engineers · new team members · future AI sessions

## Revision History

| Date | Author | Version | Changes | Related |
|------|--------|---------|---------|---------|
| 2026-06-10 | AI Agent (Claude Opus 4.7 1M) | v1 | Initial draft consolidating stage start/end/stage_days/in_lm/on_hold rules; Code-First from pool:2038-2076 + pool:2215-2330; 4 real-loan worked examples | doc 27 §9-§41 · pool:2038-2076 · pool:2215-2330 |

## Dependencies

- `port.fcl_stage_info` (Redshift) — built by `basic_data_pool_config.py` pool:2037-2440; MySQL copy synced to `bpms.sync_fcl_stage_info` via L5.
- `port.basic_data_loan_fcl` (FCL fact table) provides stage-trigger dates.
- `port.basic_data_loan_foreclosure_loss_mitigation` provides LM cycles (cycle_opened_date / cycle_closed_date).
- `tempfc.current_fcl_hold_temp` (runtime temp table) provides Hold intervals (hold_start_dt / hold_end_dt / hold_stage).
- `tempfc.current_date_new_york.curr_date` provides the ETL run date (NY timezone).
- `tempfc.current_fcl_business_2_temp` provides long-form `(loanid, stage, stage_start_dt, stage_end_dt)` — the left table for in_lm/on_hold. **Note**: this table's `stage_end_dt` for some stages may differ from `business_1.<X>_end_date` (see §8 Open Question).

## Known Limitations

- §8 Open Question 1 unresolved: the construction code of `business_2.stage_end_dt` (≈pool:2100-2200) was not retrieved when publishing this doc. Once obtained, we can fully reconcile 7727000131 demand_in_lm_days=14 vs hand-computed 5.

---

## 1. Conceptual Model (10-second read)

Every stage is a **time window** `[start_date, end_date]`:

- **start_date** = **passthrough** of the servicer-reported "trigger event date" column for that stage (always a single-column direct copy, no transform).
- **end_date** = usually **derived** from the next stage's start_date (a few exceptions in §3); NULL if the next stage hasn't started.
- **stage_days** = length of that window, formula `datediff(start, COALESCE(end, curr_date)) + 1` (inclusive).
- **in_lm_days** = the window's overlap with an **OPEN** LM cycle (**only one most-recent open cycle**, see §5).
- **on_hold_days** = the window's overlap with an **OPEN** hold (same single-row rule).

⚠️ Common pitfalls: ① `servicecompletedate` → SERVICE **start** (not end); ② `demand_end_date` does NOT participate in demand_stage_days; ③ in_lm/on_hold count **only one OPEN cycle per stage**, not a sum.

---

## 2. stage_start_date Sources

| stage | start = which Newrez column (passthrough) | port intermediate name | counter-intuitive | Code-First |
|---|---|---|---|---|
| **DEMAND** | `newrez.portnewrezfc.demandsentdate` | `basic_data_loan_fcl.demandsentdate` | — | [pool:2037](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L2037) |
| NOI | — | — (null_in_build) | — | [pool:2043-2046](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L2043-2046) |
| **REFERRAL** | `newrez.portnewrezfc.fcreferraldate` | `basic_data_loan_fcl.referral_start_date` | — | [pool:2048](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L2048) |
| **FIRST_LEGAL** | `newrez.portnewrezfc.firstlegaldate` | `basic_data_loan_fcl.legal_start_date` | — | [pool:2058](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L2058) |
| **SERVICE** | `newrez.portnewrezfc.servicecompletedate` | `basic_data_loan_fcl.service_start_date` | **⚠️ YES** — name reads like "completed", but in the FCL stage model it's the **start** of the SERVICE stage (the waiting window after service is completed and before judgement is available). | [pool:2068](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L2068) |
| PUBLICATION | — | — (null_in_build) | — | [pool:2078-2081](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L2078-2081) |
| JUDGEMENT | `newrez.portnewrezfc.fcjudgmenthearingscheduled` | `basic_data_loan_fcl.fcjudgment_start_date` | Note: BPS column `judgement_start_date` comes from THIS source, NOT `fcjudgmententered` | (final INSERT remap to `judgement_start_date`) |
| SALE | `newrez.portnewrezfc.fcscheduledsaledate` | `basic_data_loan_fcl.sale_start_date` | — | (same as above) |

**Pattern**: start_date = the **event date that triggers** that stage. SERVICE's name is counter-intuitive because "service completion" is precisely the triggering event for the SERVICE waiting stage.

---

## 3. stage_end_date Derivation

| stage | end_date rule | passthrough or derived | when not reached | Code-First |
|---|---|---|---|---|
| **DEMAND** | = `demandexpirationdate` (passthrough, for display only) | **passthrough** | (passthrough value; may be NULL) | [pool:2038](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L2038) |
| NOI | — | (null_in_build) | NULL | pool:2043-2046 |
| **REFERRAL** | = next stage `first_legal_start_date` | **derived** | NULL | [pool:2049,2365](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L2049) |
| **FIRST_LEGAL** | = next stage `service_start_date` | **derived** | NULL | [pool:2059,2370](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L2059) |
| **SERVICE** | = next stage `judgment_available_date` | **derived** | NULL | [pool:2069,2376](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L2069) |
| PUBLICATION | — | (null_in_build) | NULL | pool:2078-2081 |
| JUDGEMENT | hard-coded NULL (final INSERT: `null as judgement_end_date`) | — | NULL | (final INSERT pool:2330+) |
| SALE | hard-coded NULL (final INSERT: `null as sale_end_date`) | — | NULL | (final INSERT pool:2330+) |

**Pattern**: except DEMAND (passthrough of demandexpirationdate for display), all end_dates are **derived from the next stage's start**. JUDGEMENT/SALE (terminal stages) have hard-coded NULL end_dates in the sync table.

---

## 4. stage_days Formula + Worked Examples

### Formula

```sql
-- General (REFERRAL/FIRST_LEGAL/SERVICE):
<X>_stage_days = datediff(day,
                          <X>_start_date,
                          COALESCE(<X>_end_date, curr_date)) + 1

-- DEMAND special:
demand_stage_days = datediff(day, demand_start_date, curr_date) + 1
                    -- does NOT use demand_end_date as the right edge
```

Inclusive (+1). `curr_date` = `tempfc.current_date_new_york.curr_date` (ETL run date; 2026-06-10 measured = 2026-06-09).

### Worked Examples (Code-First, MCP-verified 2026-06-10)

**Loan 7727000357** (Judicial · SERVICE ended, in JUDGEMENT)

| stage | start | end | stage_days | math |
|---|---|---|---|---|
| DEMAND | 2024-11-20 | 2024-12-25 (not used) | 567 | datediff(2024-11-20, 2026-06-09)+1 = 566+1 = **567** |
| REFERRAL | 2025-01-23 | 2025-06-11 | 140 | datediff(2025-01-23, 2025-06-11)+1 = 139+1 = **140** |
| FIRST_LEGAL | 2025-06-11 | 2025-08-14 | 65 | datediff(2025-06-11, 2025-08-14)+1 = 64+1 = **65** |
| SERVICE | 2025-08-14 | 2026-01-26 | 166 | datediff(2025-08-14, 2026-01-26)+1 = 165+1 = **166** |

**Loan 700082880000091** (current stage = SERVICE)

| stage | start | end | stage_days | math |
|---|---|---|---|---|
| DEMAND | 2025-12-29 | 2026-01-13 (not used) | 163 | datediff(2025-12-29, 2026-06-09)+1 = 162+1 = **163** |
| REFERRAL | 2026-01-20 | 2026-03-12 | 52 | datediff(2026-01-20, 2026-03-12)+1 = 51+1 = **52** |
| FIRST_LEGAL | 2026-03-12 | 2026-05-13 | 63 | datediff(2026-03-12, 2026-05-13)+1 = 62+1 = **63** |
| **SERVICE** | **2026-05-13** (= `servicecompletedate` — note this is **start**, not end) | **NULL** (judgement not reached) | **28** | datediff(2026-05-13, curr_date 2026-06-09)+1 = 27+1 = **28** |

**Loan 7727004408** (multiple stages closed)

| stage | start | end | stage_days | math |
|---|---|---|---|---|
| REFERRAL | 2024-03-08 | 2025-07-28 | 508 | datediff(2024-03-08, 2025-07-28)+1 = 507+1 = **508** |
| FIRST_LEGAL | 2025-07-28 | 2026-02-16 | 204 | datediff(2025-07-28, 2026-02-16)+1 = 203+1 = **204** |
| SERVICE | 2026-02-16 | 2026-05-14 | 88 | datediff(2026-02-16, 2026-05-14)+1 = 87+1 = **88** |

**Loan 700082700000033** (still in REFERRAL)

| stage | start | end | stage_days | math |
|---|---|---|---|---|
| DEMAND | 2025-12-01 | 2026-01-05 (not used) | 191 | datediff(2025-12-01, 2026-06-09)+1 = 190+1 = **191** |
| **REFERRAL** | 2026-02-11 | **NULL** (first-legal not reached) | **119** | datediff(2026-02-11, curr_date 2026-06-09)+1 = 118+1 = **119** |

---

## 5. in_lm_days / on_hold_days — Code-First Rules (pool:2215-2330)

### 5.1 Core SQL Structure (simplified pseudo-SQL)

```sql
-- Step 1: per-row (loanid, stage, single open cycle) detail
SELECT *,
  rank() OVER (PARTITION BY loanid, stage ORDER BY lm_stage) AS rnk
FROM (
  SELECT b2.loanid, b2.stage, b2.stage_start_dt, b2.stage_end_dt,
         l.cycle_opened_date,
         COALESCE(l.cycle_closed_date, curr_date) AS lm_end_dt,
         l.lm_stage,
         GREATEST(b2.stage_start_dt, l.cycle_opened_date) AS in_lm_start_dt,
         LEAST  (b2.stage_end_dt,   COALESCE(l.cycle_closed_date, curr_date)) AS in_lm_end_dt,
         DATEDIFF(day, in_lm_start_dt, in_lm_end_dt) + 1 AS in_lm_days
  FROM tempfc.current_fcl_business_2_temp b2
  LEFT JOIN (
    SELECT *,
      ROW_NUMBER() OVER (PARTITION BY loanid ORDER BY cycle_opened_date DESC) AS lm_stage
    FROM port.basic_data_loan_foreclosure_loss_mitigation   -- ⚠️ NO fctrdt filter (full history)
  ) l
    ON b2.loanid = l.loanid
   AND b2.stage_start_dt <= l.cycle_opened_date
   AND b2.stage_end_dt   >= l.cycle_opened_date   -- cycle must OPEN within stage window
  WHERE l.cycle_closed_date IS NULL                -- OPEN only
) t
WHERE rnk = 1;     -- per (loanid, stage), keep only the row with smallest lm_stage (= most recent cycle_opened)

-- Step 2: pivot to wide form per loanid
SELECT loanid,
  MAX(CASE WHEN stage='DEMAND'      THEN in_lm_days END) AS demand_in_lm_days,
  MAX(CASE WHEN stage='REFERRAL'    THEN in_lm_days END) AS referral_in_lm_days,
  ...
FROM step1
GROUP BY loanid;
```

Hold logic mirrors LM with **one difference**:

| Difference | LM | Hold |
|---|---|---|
| Input table | `port.basic_data_loan_foreclosure_loss_mitigation` (**NO fctrdt filter** — all historical cycle rows participate) | `tempfc.current_fcl_hold_temp` (**WITH `b2.fctrdt = dataasof`** — only same-fctrdt snapshot hold rows) |
| OPEN filter | `cycle_closed_date IS NULL` | `hold_end_dt IS NULL` |
| Order key | `lm_stage = ROW_NUMBER OVER (PARTITION BY loanid ORDER BY cycle_opened_date DESC)` — rnk=1 picks the **most recent open** | `hold_stage` (pre-generated in the temp table; priority-like) |

### 5.2 Key Rules

1. **OPEN-only**: only currently un-closed LM cycles / Holds (`*_closed_date IS NULL`).
2. **Cycle must OPEN within stage window**: constraint `stage_start ≤ cycle_opened ≤ stage_end` — the cycle must be **opened during** that stage. A cycle opened before the stage but continuing into it does **NOT** count.
3. **One row per (loanid, stage)**: `rank() OVER (PARTITION BY loanid, stage ORDER BY lm_stage) WHERE rnk=1` — LM picks the most-recent `cycle_opened`, Hold picks the smallest `hold_stage`. **Not SUM, not MAX(days)** — it picks **one record**.
4. **The outer max() is defensive**: Step-2 `MAX(<X>_in_lm_days) GROUP BY loanid` — since (loan, stage) is already unique after rnk=1, max() just passes through the single value.
5. **End substitution**: `in_lm_end_dt = LEAST(stage_end, COALESCE(cycle_closed_date, curr_date))` — OPEN cycle uses curr_date as cap; stage-already-ended uses stage_end.
6. **curr_date source**: `tempfc.current_date_new_york.curr_date` (ETL run date, NY tz; 2026-06-10 measured = 2026-06-09) — **NOT fctrdt**.
7. **LM vs Hold history scope**: LM pulls full history (may include cycles long before the current fctrdt); Hold uses only the same-fctrdt snapshot. This causes behavioral divergence on loans with long history.

### 5.3 Worked Example

**Loan 7727000131 · LM cycles** (Code-First full history, the 3 rows with cycle_closed_date IS NULL)

| lm_stage (by cycle_opened DESC) | cycle_opened_date | cycle_closed_date |
|---|---|---|
| 1 | 2026-05-28 | NULL (currently open) |
| 4 | 2025-10-20 | NULL (historically open, no longer in latest snapshot) |
| 5 | 2025-09-15 | NULL (historically open, no longer in latest snapshot) |

Note: lm_stage 2/3/6 are closed cycles filtered out by OPEN.

**Apply rules to DEMAND stage** (demand window per `bpms.sync_fcl_stage_info`: start=2025-08-15, end=2025-09-19):

- Filter "cycle opens within stage": 2025-09-15 ✓ in [2025-08-15, 2025-09-19]; others ✗.
- 1 OPEN cycle qualifies → rnk=1 = lm_stage=5 (2025-09-15).
- Compute: `datediff(greatest(2025-08-15, 2025-09-15), least(2025-09-19, curr_date 2026-06-09)) + 1 = datediff(2025-09-15, 2025-09-19) + 1 = 4 + 1 = 5`.
- **But prod measures demand_in_lm_days = 14**.

**9-day gap — see §8 Open Question 1**: the gap points to `tempfc.current_fcl_business_2_temp.stage_end_dt` for DEMAND ≠ `fcl_stage_info.demand_end_date` (=2025-09-19); back-solving gives 2025-09-28 to produce 14 days, but 2025-09-28 doesn't match any known milestone. Need to retrieve the construction code for `business_2_temp` (≈pool:2100-2200).

---

## 6. Common Pitfalls (5)

1. **`servicecompletedate` → SERVICE stage's START, not end**. The name reads like "service completed", but the FCL stage model defines SERVICE as "the waiting window after service is completed and before judgement is available" — so this date is the window's left edge.
2. **`demand_end_date` does NOT participate in `demand_stage_days` computation**. DEMAND is the only stage with a special stage_days formula: it always counts to curr_date, regardless of whether demand_end_date is populated.
3. **When end_date = NULL, stage_days counts to curr_date** — COALESCE behavior, NOT NULL propagation.
4. **`curr_date` ≠ `fctrdt`**. `curr_date` comes from `tempfc.current_date_new_york.curr_date`, the ETL **run** date (NY tz; 2026-06-10 measured 2026-06-09); `fctrdt` is the data **report** date (one day earlier, 2026-06-08). stage_days / in_lm / on_hold all use curr_date.
5. **in_lm/on_hold count ONE OPEN cycle per stage** — not a sum across all OPEN cycles, not a MAX over per-cycle days. The code uses `rank() ... rnk=1` to force selection of a single row (LM: most-recent cycle_opened; Hold: smallest hold_stage). **And the cycle must OPEN within the stage window** (mere interval overlap does NOT qualify).

---

## 7. Code-First References

| Topic | Code location |
|---|---|
| stage_start_date passthrough | [pool:2037-2068](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L2037-2068) |
| stage_end_date derivation | [pool:2049,2059,2069,2076](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L2049) |
| stage_days formula (incl. demand special) | [pool:2038-2076](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L2038-2076) |
| in_lm_days SQL (complete) | [pool:2246-2330](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L2246-2330) |
| on_hold_days SQL (complete) | [pool:2215-2297](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L2215-2297) |
| Final INSERT into `port.fcl_stage_info` | pool:2330+ (same file, right after in_lm pivot) |
| Sync to `bpms.sync_fcl_stage_info` | [asset:925](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/bps/bps_config/asset_managment_config.py#L925) |

---

## 8. Open Questions

### OQ1 — Actual value of `business_2_temp.stage_end_dt` for DEMAND etc. (affects in_lm/on_hold)

**Symptom**: `bpms.sync_fcl_stage_info.demand_in_lm_days` measures 14 for loan 7727000131 (fctrdt 2026-06-08), but using `business_1.demand_sent_end_date` (= demandexpirationdate = 2025-09-19) and only cycle 2025-09-15 hits, the hand-computed value is 5. Gap = 9 days.

**Hypothesis**: `tempfc.current_fcl_business_2_temp.stage_end_dt` for DEMAND ≠ `business_1.demand_sent_end_date`. Could be `demandexpirationdate + N` (back-solved N=9 → 2025-09-28), or some servicer-specific / state-level configured / fcsetupdate-derived value.

**How to resolve**: get `basic_data_pool_config.py` ≈ pool:2100-2200 (the `current_fcl_business_2_temp` construction block) and verify.

**Impact**: §5 worked example shows the gap unresolved. Other stages (referral/first_legal/service) in_lm/on_hold rely on the same business_2 stage_end_dt and may have similar offsets.

### OQ2 — Exact definition of `hold_stage` (affects Hold rnk=1 selection)

The `tempfc.current_fcl_hold_temp.hold_stage` column is pre-generated externally; the snippet we received (pool:2215-2330) only references it in ORDER BY without showing the generator. Needs separate retrieval (likely in the hold_temp construction block).

---

## 9. Related Documents

- **[doc 27 — `bpms.sync_fcl_stage_info` per-field lineage](27_lineage_sync_fcl_stage_info.md)**: complete hop-by-hop chain for each field (Newrez → Redshift → BPS sync), with per-field examples.
- **[doc 25 — FCL field lineage overview](25_fcl_lineage_overview.md)**: field-lineage hub; enter each sync table from here.
- **[doc 13 — Newrez FCL BPS display mapping](13_newrez_fcl_bps_display_mapping.md)**: BPS UI fields → Newrez source (incl. Days in Stage/LM/Hold UI provenance).
- **[doc 14 — BPS-driven Servicer FCL data interface](14_bps_driven_servicer_fcl_interface.md)**: servicer field spec (incl. canonical definitions of stage-trigger fields).
- **[doc 22 — BPS agg-summary FCL page sourcing](22_bps_fcl_timeline_sourcing.md)**: how the agg-summary Time Line/Stage tab is sourced from `sync_fcl_stage_info`.
