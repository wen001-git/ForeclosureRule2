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

## 3 · Phase 3: ③④ L1 sources + ㉔ decode dictionary (added 2026-06-14)

### TC-P3.1 ③④ bk/lm L1 source sheets
Added **③ src·portnewrezbk** (60 fields) and **④ src·portnewrezlm** (56 fields), rendered like ② (is_src: fields + business meaning + source/type + 25 per-loan example columns; L1 raw has no upstream so no formula columns). A sub-agent pulled the data read-only into `fcl_layer_examples_phase3.json`: `information_schema` confirms 0 missing columns; 20/25 sample loans have rows (the 5 Carrington loans have no Newrez bk/lm row → ∅NULL); multi-row tables use the representative latest row (bk = latest bkfileddate, lm = latest dealstartdate). Real values verified in-sheet (e.g. 7727000065 Ch7, 7727003984 Ch13).

### TC-P3.2 ㉔ decode-dictionary sheet + Schema-Verify correction (Code-First)
Added **㉔ dic·portnewrezdatadic**, a custom decode-dictionary sheet (not per-loan; long format field_name/code/description): **12 categories, 140 rows** code→text (BKStatus/BKStage/BorrowerIntention/Judicial/LMDeal/LMDecision/LegalStatus/LiquidationType/MBADelinquency/ForbearanceStatus/RepaymentStatus/TrialStatus); large categories LMStatus(149)/LMProgram(388)/DenialReason(130)/ModType(387) flagged as not fully listed.
**Correction**: the ETL ([pool:367](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L367) BK / [pool:835-840](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L835-840) LM) `LEFT JOIN newrez.portnewrezdatadic WHERE field_name=...`. The sub-agent's mysql_prod check reported the table missing (only the wide `newrezdatadic`, no LM/BK); a Code-First recheck + direct `redshift_prod` query found the long table lives **only in Redshift** with all LM/BK categories — the correct dict was pulled from there and the ㉔ table-meta business_meaning corrected (was wrongly "8 columns").

### TC-P3.3 Ordering + recalc
Per-table sheets reordered to **ascending circled-number** (user feedback: easier to find by number): ② ②c ③ ④ ⑨ ⑩ ⑪ ⑬ ⑮ ⑯ ⑰ ⑱ ⑲ ⑳ ㉑ ㉒ ㉓ ㉔. 25 → **28 sheets**. Real Excel COM `CalculateFull`: **28 sheets, 0 formula errors** (③④ is_src have no formulas; ㉔ is plain text; main+Phase2 formulas unchanged); content-level idempotent. Still without a detail sheet: ⑤⑥⑦⑧⑫⑭.

## 4 · Phase 4: ⑤⑥ L1 sources + ⑫ basic_data_fcl_related (added 2026-06-14)

### TC-P4.1 ⑤⑥⑫ sheets
Added **⑤ src·portnewrezgeneral** (125 fields), **⑥ src·portnewrezprop** (32 fields) (is_src: fields + business meaning + source/type + 25 example columns) + **⑫ mid·fcl_related** (14 fields, non-src: also has the calc-logic column + per-servicer 🧮 formula columns). doc 32 grew 28 → **31 sheets**. Detail tabs remain ascending-by-number: ② ②c ③ ④ ⑤ ⑥ ⑨ ⑩ ⑪ ⑫ ⑬ ⑮ ⑯ ⑰ ⑱ ⑲ ⑳ ㉑ ㉒ ㉓ ㉔ (test T2 ascending = True, 21 detail sheets).

### TC-P4.2 Data pull + schema-verify
Sub-agent read-only pull → `fcl_layer_examples_phase4.json`: ⑤ general (mysql_prod, 125 cols, 20/25 loans), ⑥ prop (mysql_prod, 32 cols, 20/25), ⑫ fcl_related (redshift_prod, 14 cols, 25/25). `information_schema`: **0 missing columns** on all three. The 5 Carrington loans are absent from ⑤⑥ (Newrez tables) → omitted; ⑫ is cross-servicer so all 25 present. Verified ⑥ `propertystate` = CA/AZ/FL…; ⑫ `delq_status` observed values C/D30/D120P/FCL/P/REO.

### TC-P4.3 ⑫ calc logic + per-servicer live formulas
Added `field_rule` for ⑫'s 14 fields (Code-First from `CREATE_FCL_RELATE_ATTR` [pool:1697-1770](https://gitlab.bridgerinvestment.com/jli/prefectflow/-/blob/32a750a39c7eda989de991c47467979043e3d209/flow/basic_data/basic_data_config/basic_data_pool_config.py#L1697-1770)). ⑫ Newrez derived fields' 🧮 = **live upstream refs**: `propertystate`=`='⑥ src·portnewrezprop'!…`, `isloanlitigated/deactreason/reasonfordefault/inauctionflag`→⑤, `bk_flag`→`='③ src·portnewrezbk'!…` (activebkflag), `servicer`=constant, `delq_status`=CASE (note — the delinquency class, i.e. the `r` source of ⑬'s group). Carrington-branch source columns (litigation_type/property_state/bk_flag…) are not in ②c → honest note. Test T4: ⑫ has 8 cross-sheet formula refs, **0 dangling** (all point to existing ③⑤⑥ sheets).

### TC-P4.4 Recalc + idempotency
Real Excel COM `CalculateFull`: all **31 sheets, 0 formula errors** (incl. ⑫'s new passthrough refs to ⑤⑥③); formula count 677→**703**; content-level idempotent. Still without a detail sheet: ⑦⑧ (delinquency-branch L2/L3), ⑭ (portfunding dimension).

## Conclusion
**Phase 2, the Knowledge Graph, Phase 3, and Phase 4 all PASS.** doc 32 now has 25 sheets, 677 live formulas, real-Excel 0 errors, idempotent; each of the four chains carries fields / calc logic / per-layer examples / per-servicer formulas. The knowledge graph has 386 nodes, 963 edges, 1 connected component, 498 cross-dimension edges; the HTML 6th view has 0 JS syntax errors and passes runtime execution. All DB and code access was read-only; nothing committed.
