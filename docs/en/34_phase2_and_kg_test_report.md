# doc 34 — Phase 2 (stage/hold/lm/bk chains) + Knowledge Graph — Comprehensive Test Report

## Document Purpose
- **Why it exists**: this session shipped two large changes — (1) doc 32 Excel gained Phase 2 per-table sheets for the four FCL business chains (stage / hold / loss-mitigation / bankruptcy); (2) `outputs/fcl_pipeline.html` gained a 6th view, the **FCL Knowledge Graph**. This file records the **comprehensive test** + evidence for both, for acceptance and regression.
- **Gap it fills**: doc 32 previously covered only the main chain (sync_loan_foreclosure); the other FCL-family tables had no detail sheet. The HTML had only data-lineage views (no business/analysis dimension). This report proves both changes landed, with real data, computable formulas, and a connected graph.
- **Scope**: only this session's two deliverables. Does **not** cover the main chain's historical tests (see doc 32 test report TC1–TC17).
- **System fit**: acceptance record for doc 32 (per-field mapping + worked-example Excel) and `fcl_pipeline.html` (interactive explorer). Upstream truth: `fcl_table_meta` / `fcl_lineage_source` / `fcl_field_meanings` / `fcl_logic_coverage` + business-concept extraction.

## Target Audience
Primary: validators, data engineers, future AI sessions. Secondary: business analysts, onboarding engineers, reviewers.

## Revision History
| Date | Author | Version | Changes | Related |
|------|--------|---------|---------|---------|
| 2026-06-13 | AI Agent (Claude Opus 4.8) | v1 | Initial: Phase 2 four chains + Knowledge Graph comprehensive test (EN mirror of docs/zh/34) | doc 32; fcl_pipeline.html |

## Dependencies
- Read-only DB-measured data sources: `outputs/fcl_layer_examples_phase2.json` (8 tables), `fcl_knowledge_graph.json` (graph), `fcl_kg_{business,analysis,panels}.json` (concept extraction).
- Generators: `build_fcl_pipeline_mapping_xlsx.txt` (Excel), `build_fcl_knowledge_graph.txt` (graph), `scripts/inject_kg.txt` (inject).
- Test tools: openpyxl (content hash / readback), real Excel engine via pywin32 COM (`CalculateFull` + `SpecialCells(xlErrors)`), Node v22 (`node --check` + DOM-stub runtime).

## Known Limitations
- **Multi-row history tables (hold/lm/bk)**: the worked-example column shows the loan's representative latest row (hold = latest segment, lm = latest cycle, bk = latest filing); full history lives in the BPS panels / long tables and is not expanded per-row in the sheet. Noted in the sheet note and here.
- **Stage table: 19/25 sample loans have a row** (active-FCL filter); the rest are ∅NULL (factual, not a defect). BK has records for only 6/25.
- The browser **visual** of the knowledge graph was not screenshot-confirmed in this environment; it was runtime-validated with a Node DOM stub (`renderKG` produces SVG without error). Reviewers should open the HTML to confirm visually.

---

## 1 · Phase 2: stage / hold / lm / bk per-table sheets

### TC-P2.1 Data pull (read-only DB + schema-verify)
A sub-agent pulled the representative row for **8 tables × 25 sample loans** via `redshift_prod` (port.\*) / `mysql_prod` (bpms.\*) into `fcl_layer_examples_phase2.json`. `information_schema` check: **all FM-listed columns exist, 0 missing**; key column = `loanid`. Coverage: stage 19 loans / hold 25 / lm 22 / bk 6. **rs and sync representative rows are byte-identical** (sync is a faithful copy, minus port-only admin cols dataasof/servicer/improgram). Encoding: real NULL→`∅NULL`, empty→`∅空串`, dates→YYYY-MM-DD.

### TC-P2.2 8 sheets generated
`B_TABLES` gained 8 entries → doc 32 grew 17 → **25 sheets**: ⑬ `mid·fcl_stage_info`(48) / ⑲ `bps·sync_fcl_stage_info`(57) / ⑮ `mid·fcl_hold`(17) / ㉑ `bps·sync_fcl_hold`(15) / ⑯ `mid·fcl_lm`(16) / ㉒ `bps·sync_fcl_lm`(22) / ⑰ `mid·fcl_bankruptcy`(15) / ㉓ `bps·sync_fcl_bankruptcy`(22). Each has all four requested aspects: **fields + business meaning + calc logic / mapping rule (from lineage hops) + source/type + per-layer worked-example columns (25) + per-servicer 🧮 formula columns (Newrez / Carrington)**.

### TC-P2.3 Per-servicer live formulas (passthrough → real upstream)
`IMM_UP` extended with the four chains' BPS←Redshift upstreams; the fill loop includes the 8 new metas. BPS-side fields show **live formulas referencing the upstream Redshift sheet's cell**, e.g. ⑲ `group` = `='⑬ mid·fcl_stage_info'!G17` (upsert pass-through [asset:925]); ㉓ `bankruptcy_status`/`legal_status` reference ⑰ [asset:829]. Redshift-side decode/derive fields (whose servicer raw is not rendered) use the calc-logic column note (same convention as main chain ⑪).

### TC-P2.4 Real Excel recalc
pywin32 COM opens a copy → `CalculateFull()` → per-sheet `SpecialCells(xlCellTypeFormulas, xlErrors)`: **all 25 sheets, 677 live formulas, 0 formula errors** (incl. every Phase-2 passthrough — 0 #REF/#NAME/#VALUE).

### TC-P2.5 Idempotency
Two generator runs → identical content-level MD5 across all 25 sheets.

---

## 2 · Knowledge Graph (fcl_pipeline.html 6th view "🧠 Knowledge Graph")

### TC-KG.1 Graph assembly
`build_fcl_knowledge_graph.txt` assembles `fcl_knowledge_graph.json` from the truth sources: **386 nodes / 963 edges / 0 dangling**. Three dimensions present — pipeline (layers 6 / tables 24 / fields 154 / servicers 3 / LT rules 30 / mechanisms 5), foreclosure analysis (status 18 / stages 8 / milestones 9), business (concepts 61 / terms 23 / BPS panels 10) + docs 35. Business/analysis dimensions extracted by 3 sub-agents from docs 17/18/10, 03/04/05/31, 16/13/14 (stored in `fcl_kg_{business,analysis,panels}.json`).

### TC-KG.2 Connectivity (three dimensions truly wired into one web)
Graph traversal: **1 connected component, 386/386 nodes, 0 isolated**. **498 cross-dimension edges** (documented_in 345, business↔pipeline 138, modeled_by 6, corresponds 18, displayed_in 9…). A layer spine (L0→L5), a doc:00 index hub, and analysis↔business bridges (milestone:referral↔concept:referral, status:fcl↔concept:foreclosure, etc. — semantically exact) fold the former analysis island + isolated docs into the main graph.

### TC-KG.3 HTML integration + JS syntax
Added `v-kg` button, `setView('kg')`, a self-contained `renderKG` module (dimension-lane clustered layout + node-type filter chips + search + wheel-zoom / drag-pan + click-node ego highlight + detail drawer with clickable neighbors) + i18n (EN/中文). `scripts/inject_kg.txt` injects 251 KB (`</`→`<\/` to guard against premature `</script>`). `node --check` on the whole script: **0 syntax errors**; markers `/*KG_START*//*KG_END*/` each appear once; embedded JSON parses, 0 dangling.

### TC-KG.4 Runtime execution (Node + DOM stub)
With a minimal DOM stub in Node: `renderKG()` emits `<svg>`, **232 visible nodes** (154 fields hidden by default), 14 filter chips; `kgSelect('concept:foreclosure')` populates the drawer with neighbors; `kgToggle('field')` / `kgSearch` / `kgReset` / EN↔中文 toggle all run without error.

---

## Conclusion
**Both Phase 2 and the Knowledge Graph PASS.** doc 32 now has 25 sheets, 677 live formulas, real-Excel 0 errors, idempotent; each of the four chains carries fields / calc logic / per-layer examples / per-servicer formulas. The knowledge graph has 386 nodes, 963 edges, 1 connected component, 498 cross-dimension edges; the HTML 6th view has 0 JS syntax errors and passes runtime execution. All DB and code access was read-only; nothing committed.
