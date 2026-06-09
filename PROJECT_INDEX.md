# PROJECT_INDEX — ForeclosureRule2 (AI Agent Quick-Start)

> **Read this file first.** It is the single-read orientation map for any AI coding tool working on this
> project. It exists so an agent can understand *what this repo is, where the real source system lives,
> which databases exist, which rules are mandatory, and which doc answers which question* — without
> crawling 20+ documents. Jump from here to the specific doc/table/rule you need.

---

## Document Information

| Field | Content |
|-------|---------|
| **Purpose** | Compact, AI-facing index of the ForeclosureRule2 documentation project. Lets an agent orient in one read and jump to the right doc/table/rule, minimizing token spend. |
| **Problem solved** | The detailed docs live in `docs/en/` & `docs/zh/` (20+ files each) plus `CLAUDE.md`/`AGENTS.md`. A fresh agent otherwise re-crawls everything to learn the basics. |
| **Scope** | This repo only (documentation *about* the PrefectFlow ETL system). Does **not** restate full doc content — it points to it. |
| **System fit** | Top-level entry point; complements the human-facing reading-order index at `docs/en/00_index.md`. |

**Target audience:** AI coding agents (primary) · onboarding engineers · data engineers · architects · validators.

**Revision history:**

| Date | Author | Version | Changes | Related |
|------|--------|---------|---------|---------|
| 2026-06-08 | AI Agent | v1 | Initial AI-facing project index | `docs/en/00_index.md`, `CLAUDE.md` |

---

## 1. What this project is

ForeclosureRule2 is a **reverse-engineering documentation suite** for a production mortgage-foreclosure
ETL system. It **documents** how foreclosure (FCL) data flows from servicer files into the downstream
**BPS** (Business Planning System) — it does **not** execute ETL itself. Every claim is code-read from the
source system and database-verified against production (MCP). The goal is to make 500+ scattered
processing rules comprehensible as a whole, to support validation/reconciliation, servicer onboarding,
and an eventual system rewrite.

## 2. Documented source system

The actual code being analyzed lives **outside this repo**, at:

```
C:\Users\jli\MyData\Copilot\PrefectFlow      (Prefect 2.x mortgage-loan servicing ETL)
```

This repo = *docs about that system*. When a doc cites `file:line`, it refers to PrefectFlow source.

## 3. Architecture cheat-sheet (facts reused constantly)

- **5-layer pipeline (L0→L5):**
  - **L0** raw servicer files (S3/SFTP) → **L1** per-servicer staging (`newrez.portnewrez{fc,bk,lm,general}`, `sls.*`, `carrington.*`, `mrc.*`, …)
  - **L2** unified daily (`port.basic_data_daily_loan_common`) → **L3** clean daily (`..._clean`, delinq mapping)
  - **L4** monthly FCL business family (Redshift-built): `port.basic_data_loan_foreclosure`, `basic_data_loan_fcl`, `fcl_stage_info`, `*_hold`, `*_loss_mitigation`, `*_bankruptcy`, `basic_data_fcl_related`, `basic_data_loan_reo`
  - **L5** BPS sync (MySQL `bpms.*`): primary table **`bpms.sync_loan_foreclosure`**, plus `sync_fcl_stage_info`, `sync_loan_foreclosure_{hold,loss_mitigation,bankruptcy}`
- **Dual-write:** L1–L4 write to both MySQL and Redshift. The L4 FCL family is **Redshift-only**, then copied to MySQL by a **two-step L5 sync** (`sync_to_mysql` clear+append → `update_to_mysql` `INSERT…ON DUPLICATE KEY UPDATE`). This is why `bpms.sync_loan_foreclosure.create_time/update_time` are NULL by design.
- **4 orthogonal status dimensions** (one loan can be all at once): **delinquency** (C/D30/D60/D90/D120P) · **FCL** · **LM** (loss mitigation) · **BK** (bankruptcy).
- **Core FCL rule:** FCL is produced **only** by a servicer-reported `delinquency_status='Foreclosure'`. The `days360(next_due, report_date)` DPD fallback **can never** yield FCL (max D120P). FCL is a legal-process status, orthogonal to delinquency.
- **FCL is a 6-stage legal process:** Demand → Referral (timeline start) → First Legal → Service → Judgement → Sale. Judicial states (NY/NJ/FL) 12mo–3yr; non-judicial (CA/TX) 2–6mo.
- **Servicer coverage:** **3 full** (Newrez, Carrington, CapeCodFive — have L4 FCL detail tables) vs **7 inference-only** (SLS, Selene, MRC, FCI, Rocket, Arvest, SPS — FCL inferred from delinq bucket, no timeline/stage).
- **Key date columns:** `dataasof` (L1 servicer snapshot) → `asofdate` (L2) → `fctrdt` (L3/L4 report cutoff = first day of following month). `sync_fcl_stage_info` retains `fctrdt` history; `sync_loan_foreclosure` overwrites to current-state only.

## 4. Repository layout

| Path | Contents |
|------|----------|
| `docs/en/` | 20 English analysis docs (numbered, see §5). |
| `docs/zh/` | 27 Chinese docs — mirror of en (same numbering) **plus** zh-only docs 15/17/19/98/99 + validation manual + gap template. en/zh kept in parity. |
| `scripts/` | Python generators for the docs/Excel/SQL artifacts. **Run inline** (heredoc / `python -c`) — see rule in §7. |
| `outputs/` | Generated HTML diagrams (`fcl_pipeline.html`, `fcl_flow_playground.html`, `fcl_state_diagram_options.html`) + stats JSON. |
| `tools/` | JS tooling (`build_doc14_review_workbook.mjs`). |
| `docs/*.xlsx`, `docs/*.csv` | Field-spec Excel (e.g. `14_servicer_fcl_field_spec.xlsx`) + verification CSVs. |
| `.mcp.json` | DB MCP connections (gitignored; credentials live here only). |
| `CLAUDE.md` / `AGENTS.md` | Mandatory project rules (see §7). |
| `prompt.md` | Prompt + decision + milestone log (append per workflow rule). |

## 5. Document map (`#` → file → read when…)

Numbering is shared across `docs/en/` and `docs/zh/`.

| # | File | Read this when you need… |
|---|------|--------------------------|
| 00 | `00_index.md` | Human reading-order navigation (verbose). |
| 01 | `01_source_data.md` | Raw servicer table schemas / FCL field inventory. |
| 02 | `02_etl_pipeline.md` | **The 5-layer pipeline** — table lineage, dual-write, write mechanisms. (Authoritative pipeline doc.) |
| 03 | `03_fcl_status_logic.md` | Full FCL status generation logic (SQL/Python/mappings/overrides). |
| 04 | `04_status_inventory.md` | Every status code (delinq/FCL/REO/BK/special) + source + usage. |
| 05 | `05_loan_attribute_mapping.md` | Which loan attributes drive FCL/delinquency status. |
| 06 | `06_diagrams.md` | Mermaid diagrams (dataflow / state machine / lineage / dependencies). |
| 07 | `07_fcl_lineage_and_rules.md` | Per-servicer FCL lineage + judgment rules + gap analysis. |
| 08 | `08_servicer_fcl_field_mapping.md` | Servicer raw field → FCL status mapping (business view) + gaps. |
| 09 | `09_servicer_data_interface_standard.md` | New-system servicer interface standard (7 field groups, P0/P1/P2, compliance matrix). |
| 10 | `10_glossary.md` | **Domain glossary** (50+ terms: FCL/LM/BK/MBA/days360/fctrdt/BPS…). |
| 11 | `11_servicer_impl_guide.md` | Transitional ETL mapping (8 servicers' data → standard fields, pseudocode). |
| 12 | `12_sync_asset_management.md` | Code investigation of `sync_asset_management.py` (2-phase orchestration). |
| 13 | `13_newrez_fcl_bps_display_mapping.md` | BPS UI field → Newrez raw source reverse mapping (5 panels). |
| 14 | `14_bps_driven_servicer_fcl_interface.md` | **Servicer onboarding spec** — ~92 fields from 5 BPS panels, P0/P1/P2, Newrez compliance. Paired with `docs/14_servicer_fcl_field_spec.xlsx`. |
| 16 | `16_bps_panel_quickref.md` | Quick lookup tables for BPS panels + Newrez source fields. |
| 18 | `18_loss_mitigation_business_primer.md` | LM business meaning, solution types, LM↔FCL relationship. |
| 20 | `20_end_to_end_walkthrough.md` | 🌟 **Best first read** — end-to-end journey + business rationale + sample loan. |
| 21 | `21_fcl_field_lineage.md` | 🔬 **Field-by-field L0→L5 lineage** (~30 core fields, transform rules w/ code location, MCP-verified). |
| 22 | `22_bps_fcl_timeline_sourcing.md` | Which table/SQL feeds the BPS agg-summary Foreclosure Time Line/Stage tabs (`sync_fcl_stage_info`). |

**zh-only docs:** `15_newrez_servicer_fcl_gap_analysis`, `17_foreclosure_business_primer` (FCL process fundamentals), `19_fcl_sample_loan_raw_dump` (5-loan raw dump across layers), `98_database_verification_strategy`, `99_servicer_fcl_gap_summary_and_action_plan`, `08-1Data validation Manual`.

## 6. Database connections (names/roles only — NO credentials here)

**All databases are READ-ONLY. Never write (no INSERT/UPDATE/DELETE/DDL). Verify against prod.**

| MCP name | Role |
|----------|------|
| `mysql_prod` | Prod MySQL, database **`bpms`** — BPS sync tables (`sync_loan_foreclosure`, …). Use for BPS direct-value verification. |
| `redshift_prod` | Prod Redshift cluster (database literally named `dev`, but it is the **prod** cluster). L1–L4 analytics + FCL family build. |
| `mysql_dev` / `mysql_bpms_dev` | Dev/test (`bpms_dev` schema). **Stale** (data lags); reference only — use prod for same-date comparisons. |

Credentials live solely in gitignored `.mcp.json`; never write them into any tracked file.

## 7. Mandatory rules digest (full text in `CLAUDE.md`)

1. **DB read-only, always** — every DB/env/connection. No writes ever without explicit user consent.
2. **Code-First ETL analysis** — read PrefectFlow source before concluding *how/why* a table is written. MCP shows state, not intent. If code & data conflict, code wins for design intent.
3. **Schema-Verify** — validate **every** `table.column` against `information_schema.columns` before trusting it. Don't trust a doc's/Excel's stated source path; validate all pairs, not a sample. SQL isn't "verified" until it executes.
4. **Excel 人工-column protection** — any column whose header contains 「人工」 and any user-added cell comment is user-owned; scripts/AI must never write/overwrite/delete/move it. Locate columns by header name, not column number.
5. **doc 14 MD⇄Excel sync** — field-level changes must update both `docs/14_servicer_fcl_field_spec.xlsx` (single source of truth) and the MD; re-run the sync generator, never edit only one.
6. **Session workflow** — append each user prompt to `prompt.md` *before* work; log key decisions under `## Decisions`; log milestones; run `/simplify` + tests at milestone wrap-up.
7. **Python execution** — endpoint security blocks reading `.py` files under `C:\Users\jli\...`. Run logic **inline** (`python -c "…"` or `python - < script.txt` via stdin). Never `python some_file.py` from the user dir.
8. **Standard Document Header** — every new doc starts with Purpose / Target Audience / Revision History.

## 8. Task-oriented entry points

| Goal | Path |
|------|------|
| Big-picture orientation | `20` → `02` → `17`/`18` |
| Field-by-field lineage / reconciliation | `21` → `13` → `19` |
| Servicer onboarding / new interface | `09` → `14` → `08` |
| Status logic & inventory | `03` → `04` → `05` |
| Pipeline debugging / rewrite | `02` → `12` → `07` |
| Term lookup | `10` |

## 9. Known inconsistency (heads-up)

Git status shows several generator scripts staged for deletion (`scripts/_excel_guard.py`,
`sync_fieldspec_excel_to_md.py`, `build_*.py`, `run_verify_sql_results.py`,
`add_field_spec_verify_sql.py`) while `CLAUDE.md` still references some as mandatory tooling
(e.g. the doc-14 MD⇄Excel sync rule). If you need that tooling, confirm its current presence in
`scripts/` first rather than assuming the rule's named script still exists. (Reconciling this is not
yet done.)
