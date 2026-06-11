# ForeclosureRule2 — Foreclosure Analysis Documentation (English)

---

## Document Information

| Field | Content |
|-------|---------|
| **Purpose** | Navigation index for all English-language analysis documents in the ForeclosureRule2 project. Provides content summaries, use cases, and recommended reading order. |
| **Problem solved** | Foreclosure handling logic is scattered across 500+ files in PrefectFlow — this library makes it comprehensible as a whole. |
| **Scope** | Source data → ETL pipeline → status generation logic → status inventory → attribute mapping → diagrams |
| **System** | `C:\Users\jli\MyData\Copilot\PrefectFlow` (Prefect 2.x mortgage loan servicing ETL system) |

**Target audience:** Data engineers · Business analysts · System rewrite architects · Onboarding engineers · Validators/reconciliation engineers · Future AI sessions

**Revision history:**

| Date | Author | Version | Changes |
|------|--------|---------|---------|
| 2026-05-21 | AI Agent (Claude Sonnet 4.6) | v1 | Initial version, complete reverse-engineering analysis |

---

## Document Inventory

| # | File | Core Content | Use Case |
|---|------|-------------|----------|
| 00 | `00_index.md` | This index | Navigation |
| **20** | **`20_end_to_end_walkthrough.md`** | **🌟 [Recommended first read] End-to-end walkthrough + narration**: connects the foreclosure data journey across all five layers (source Servicer files → BPS), and explains **from a business angle WHY the data is processed this way** (§A.6, e.g. why one FCL has many Holds); two layers (business-view panorama + narration + Q&A / per-layer deep-dive walkthrough + code-location map + sample-loan walk) | Walking colleagues through the whole pipeline + business rationale; fast big-picture orientation; entry point to all other docs |
| ~~21~~ | ⛔ **ARCHIVED** (no link) · `docs/archive/en/21_fcl_field_lineage.DEPRECATED.md` | **Archived 2026-06-11**: moved to `docs/archive/en/`; AI coding tools — DO NOT READ; ERD migrated to doc 33, field lineage migrated to doc 25-30, business rationale see doc 20 §A.6. | Retired; history only |
| **25** | **`25_fcl_lineage_overview.md`** | **🔬 [Field-lineage hub]** Overview of the field-level lineage from Servicer raw column → BPS sync tables: 4 canonical hop-chain skeletons + master field index + known gaps + end-to-end worked trace (loan 7727004408, MCP-verified) + links to 26–30. Rules Code-First from PrefectFlow (file:line); columns schema-verified against prod. Generated from `outputs/fcl_lineage_source.json` via `scripts/gen_fcl_lineage.py` | Entry point for field-level lineage walkthrough/reconciliation; supersedes doc 21 |
| **26** | **`26_lineage_sync_loan_foreclosure.md`** | `bpms.sync_loan_foreclosure` per-field lineage: milestones (`timeline_*`) + summary/status (`summary_*`), one row/field with per-hop column+rule+code, ending at the display view (Actual/Var) | Main-table field reconciliation |
| **27** | **`27_lineage_sync_fcl_stage_info.md`** | `bpms.sync_fcl_stage_info` per-field lineage: stage start dates / stage-days / to_*_days / in_lm / on_hold + group (delq_status: mba+days360) / judicial (state fallback) / state | Aggregate-page field reconciliation |
| **28** | **`28_lineage_sync_loan_foreclosure_hold.md`** | `bpms.sync_loan_foreclosure_hold` per-field lineage: fchold1..4 wide slots → long-table unpivot | Hold panel reconciliation |
| **29** | **`29_lineage_sync_loan_foreclosure_loss_mitigation.md`** | `bpms.sync_loan_foreclosure_loss_mitigation` per-field lineage: LM cycle + datadic code→text decode | LM panel reconciliation |
| **30** | **`30_lineage_sync_loan_foreclosure_bankruptcy.md`** | `bpms.sync_loan_foreclosure_bankruptcy` per-field lineage: BK filing + status decode | BK panel reconciliation |
| **31** | **`31_fcl_stage_window_rules.md`** | **🧮 FCL Stage Window Rules Cheat-sheet**: 8 stages × 5 column types (`start_date / end_date / stage_days / in_lm_days / on_hold_days`) in one read — start passthrough sources, end derivation, stage_days formula, in_lm/on_hold SQL semantics (Code-First from pool:2215-2330), 4 real-loan worked examples, counter-intuitive callouts (`servicecompletedate` → SERVICE start, not end) | Troubleshoot stage days / in_lm / on_hold; new-hire mental model for stage windows; horizontal summary of doc 27 |
| **33** | **`33_fcl_table_erd.md`** | **🧬 FCL Table ERD**: ~22 FCL-related tables (L1 sources 5 + Newrez payments 1 + L4 Redshift 8 + portmonth 1 + L5 BPS sync 6 + view 1) with PK / grain key / 1:N / N:N (interval overlap) relationships — 1 master diagram + 5 sub-diagrams (FCL main / portmonth anchor / Hold / LM / BK) + PK cheat-sheet + 6 common JOIN templates + cardinality rationale + Code-First refs. **Correction**: the view connects only to sync_loan_foreclosure + sync_portmonth (NOT 5 tables), MCP-verified | Troubleshoot table relationships ("why does a loan have multiple Holds?"), new-hire mental model for the table layout, join template lookup for reconciliation |
| 01 | `01_source_data.md` | Raw servicer table schemas, FCL-relevant field inventory | Data lineage, field definition lookup |
| 02 | `02_etl_pipeline.md` | Full ETL pipeline: 5-layer data flow, table lineage, Redshift vs MySQL split | Pipeline understanding, debugging, rewrite planning |
| 03 | `03_fcl_status_logic.md` | Complete foreclosure status generation logic (SQL/Python/mapping tables/override rules) | Status calculation, rewrite reference |
| 04 | `04_status_inventory.md` | Enumeration of all FCL-related status codes: meaning, source, business usage | Status lookup, reconciliation, validation |
| 05 | `05_loan_attribute_mapping.md` | Loan attribute ↔ foreclosure status mapping relationships | Impact analysis, rule validation |
| 06 | `06_diagrams.md` | All diagrams (dataflow, state machine, lineage, rule layers, dependencies) | Architecture review, documentation presentation |
| 07 | `07_fcl_lineage_and_rules.md` | Per-servicer FCL data lineage and judgment rules (SLS/Newrez/Carrington/Selene/MRC/Arvest/CapeCodFive/FCI/Rocket/SPS) | Servicer FCL implementation analysis, gap identification, improvement planning |
| 08 | `08_servicer_fcl_field_mapping.md` | Servicer raw field → FCL status mapping rules (business perspective, ETL-layer removed) + gap analysis + field completion priority | Business rule refactoring, requesting missing fields from servicers, compliance review |
| 09 | `09_servicer_data_interface_standard.md` | New system Servicer data interface standard: 7-group field catalog (P0/P1/P2) + per-servicer compliance matrix + action item summary + delivery format spec | System rewrite pre-specification, formal servicer field requests, new ETL interface design |
| 10 | `10_glossary.md` | Comprehensive glossary: 7 categories, 50+ entries covering core business statuses / delinquency codes / FCL process / LM types / bankruptcy / ETL architecture / system abbreviations | New member onboarding, quick term lookup when reading any project document |
| 11 | `11_servicer_impl_guide.md` | **Transitional implementation guide**: mapping logic for 8 servicers' existing data → new system standard fields (CASE WHEN pseudocode + implementability matrix + implementation roadmap); includes Newrez portnewrezfc multi-hold handling | New system ETL developer coding reference; transitional implementation plan while servicers adopt the new data format |
| 12 | `12_sync_asset_management.md` | **Code investigation**: full analysis of `sync_asset_management.py` — 2-phase ETL orchestration (10-step Redshift staging build + 13-choice BPS sync), all DB tables read/written, function reference, environment/tenant parameters, status tracking, and 1 identified dead-code issue in `get_sync_df()` | ETL developer reference; debugging daily BPS sync; new system rewrite of this flow |
| 13 | `13_newrez_fcl_bps_display_mapping.md` | **BPS UI field reverse mapping** (Newrez, v2): traces each of BPS Foreclosure's 5 display panels back to Newrez raw data sources (newrez.portnewrezfc/bk/lm) and calculation rules; covers the 104-column view (timeline/target/actual/var/variance/bid_approval/summary) plus Hold full history, LM Cycle, and Bankruptcy panels, plus aggregate view Days in Stage/LM/Hold via sync_fcl_stage_info | BPS data debugging; Newrez field mapping reference; template for onboarding new servicers |
| **22** | **`22_bps_fcl_timeline_sourcing.md`** | **BPS agg-summary Foreclosure page sourcing**: how the **Time Line** and **Stage** tabs (and Overview) of `/#/portfolio/agg-summary` are sourced — both from `bpms.sync_fcl_stage_info` (← `port.fcl_stage_info`, `GEN_FCL_STAGE`); full UI-column ⇄ table-column map, Time Line vs Stage vs Overview, the "current-state vs history" explanation (table retains `fctrdt` snapshots; page shows `MAX(fctrdt)`), representative SQL, and a verified sample-loan walk (7727000088) | Answering "which table/SQL feeds the Time Line page?"; BPS agg-page debugging; understanding why one loan = one row of date columns |
| **23** | **`23_bk_discharge_to_payoff_analysis.md`** | **BK discharge → payoff (P) duration analysis (DB-verified)**: answers "how long from bankruptcy discharge to final payoff" — prod shows only 11 measurable loans, median 186 months (≈15.5 yrs), and it is **NOT a process duration** (discharge mostly 2008–2014, payoff 2023–2026, unrelated), empirically confirming Ch.7/11 discharge ≠ payoff and lien survival; includes definitions, per-loan detail, limitations and verification SQL | Answering the BK→P duration question; correcting the "discharge quickly leads to payoff" intuition; BK reconciliation/definition reference |
| **24** | **`24_bk_to_current_vs_foreclosure.md`** | **BK→Current vs BK→Foreclosure core difference**: the dividing line at the BK node = whether the mortgage default is cured (≠ whether it is discharged); Ch.13 cure reinstates→C, while dismissal/MFR/Ch.7 (lien survives)→FCL; includes comparison table, triggers, § 1322/1328/362/727/524 basis + authoritative sources, and the system pass-through note | Clearing up the "BK success = back to Current" misconception; business/legal explanation of the two BK edges; training & reconciliation reference |

---

## Recommended Reading Order

```
Big picture (recommended):       20 → 02 → 17/18
Field-level lineage walkthrough: 21 → 13 → 19 (field-by-field + transform rules + reconciliation)
First-time system orientation:  00 → 02 → 03 → 04
Data lineage analysis:          01 → 07 → 02 → 05
System rewrite preparation:     03 → 07 → 05 → 06 → 02 → 09
Validation / reconciliation:    04 → 03 → 05
Servicer gap analysis:          08 → 07 → 03 → 09
Business rule refactoring:      08 → 03 → 07 → 09
New system interface design:    09 → 08 → 07
New system ETL implementation:  09 → 11 → 08
Diagrams only:                  06
```

---

## Quick Glossary

| Term / Abbrev. | Meaning |
|----------------|---------|
| FCL | Foreclosure |
| REO | Real Estate Owned (bank-acquired property post-foreclosure) |
| BK | Bankruptcy |
| LM | Loss Mitigation (e.g., forbearance, loan modification) |
| delinq | Delinquency status code (C / D30 / D60 / D90 / D120P / FCL / REO / P) |
| svcdelinq | Servicer's raw delinquency description (un-normalized) |
| days360 | Day count between two dates using 360-day year convention |
| fctrdt | Report cutoff date (first day of the following month) |
| portmonthbase | Primary monthly analytical table in Redshift |
| basic_data_loan_fix | Manual override correction table (highest priority) |
| BPS | Business Planning System (downstream reporting system) |
| MBA | Mortgage Bankers Association — standard delinquency classification |

> For full definitions (50+ entries, including FCL process stages / LM types / ETL architecture / MBA code mapping), see [doc 10 Comprehensive Glossary](10_glossary.md)

---

## System Boundaries

**In scope:**
- All Python and SQL foreclosure status generation logic in the PrefectFlow codebase
- MySQL (staging) and Redshift (analytics) table schemas involved in FCL processing
- BPS sync layer (downstream output tables)

**Out of scope:**
- Internal BPS system logic (downstream system)
- Polypath / IRR calculation modules (independent modules)
- Servicer business rules upstream of file delivery

---

## Chinese Version

Synchronized Chinese version: `docs/zh/00_index.md` (identical section numbering, diagrams, and terminology)
