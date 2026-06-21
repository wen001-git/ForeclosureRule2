# ForeclosureRule2

[中文说明](README.zh-CN.md)

ForeclosureRule2 is a documentation-first reverse-engineering project for a production mortgage foreclosure ETL system. This repository does not run the ETL itself. It explains how foreclosure-related data moves from servicer files through PrefectFlow processing and into BPS reporting tables, with code-first analysis and database-backed verification captured in structured docs.

## What This Repo Contains

- English and Chinese analysis documents under `docs/en/` and `docs/zh/`
- Project-level orientation in `PROJECT_INDEX.md`
- Generated reference artifacts, diagrams, and HTML explorers under `outputs/`
- Helper scripts used to build or refine documentation artifacts under `scripts/`
- Supporting spreadsheets and source examples under `docs/`

## Best Starting Points

- `PROJECT_INDEX.md`: fastest high-level orientation for engineers and AI agents
- `docs/en/00_index.md`: English document map and reading order
- `docs/zh/00_index.md`: Chinese document map and reading order
- `docs/en/20_end_to_end_walkthrough.md`: recommended first read for the end-to-end story
- `outputs/fcl_pipeline.html`: interactive pipeline explorer

## Repository Scope

This repository documents:

- foreclosure source data from servicers
- the 5-layer ETL pipeline from raw intake to BPS sync
- status logic for delinquency, foreclosure, bankruptcy, and loss mitigation
- field lineage across Redshift, MySQL, and downstream sync tables
- onboarding and interface standards for servicers

This repository does not contain:

- the live PrefectFlow ETL codebase being analyzed
- production credentials
- downstream BPS internal application logic

## Documentation Structure

- `docs/en/`: English analysis set
- `docs/zh/`: Chinese analysis set, including several zh-only working documents
- `docs/archive/`: deprecated documents kept for history
- `outputs/`: generated diagrams, JSON snapshots, and review artifacts

## Suggested Reading Paths

- Big picture: `docs/en/20_end_to_end_walkthrough.md` -> `docs/en/02_etl_pipeline.md` -> `docs/en/18_loss_mitigation_business_primer.md`
- Field lineage: `docs/en/25_fcl_lineage_overview.md` -> `docs/en/26_lineage_sync_loan_foreclosure.md` to `docs/en/30_lineage_sync_loan_foreclosure_bankruptcy.md`
- Servicer onboarding: `docs/en/09_servicer_data_interface_standard.md` -> `docs/en/14_bps_driven_servicer_fcl_interface.md`
- Validation and reconciliation: `docs/en/03_fcl_status_logic.md` -> `docs/en/04_status_inventory.md` -> `docs/en/31_fcl_stage_window_rules.md`

## Working Notes

- Top-level rules and workflow constraints live in `CLAUDE.md` and `AGENTS.md`.
- Local connection settings and machine-specific files must stay untracked.
- The project is bilingual; when adding new navigation docs, keep English and Chinese entry points aligned.
