# ForeclosureRule2 — Project Rules

## Session Workflow (Mandatory)

### 1. Prompt Log
Append every user instruction to `prompt.md` in the project root using this format:

```
## [YYYY-MM-DD HH:MM UTC] <one-line summary>
> <verbatim user prompt>
```

Do this at the start of processing each user message, before any other work.

### 2. Decision Log
Whenever making a key technical or architectural decision, append to the `## Decisions` section of `prompt.md`:

```
### Decision: <title> [YYYY-MM-DD]
- **Context**: why this decision was needed
- **Options considered**: A, B, C
- **Choice**: chosen option
- **Reason**: rationale
```

### 3. Milestone Wrap-up (after each completed phase)
After declaring a milestone/phase complete:
1. Run `/simplify` to clean up changed code (remove redundancy, unify style)
2. Run all available tests and report a pass/fail summary
3. Log the milestone completion in `prompt.md` under `## Milestones`

## Standard Document Header Rule (Mandatory for all generated documents)

Every document created in this project must begin with a standardized header block before any content.

### Required Header Sections

#### 1. Document Purpose
Explain:
- **Why** this document exists
- **What problem** it solves or knowledge gap it fills
- **Scope** — what is and is not covered
- **System fit** — how it relates to the broader project

#### 2. Target Audience
Identify primary and secondary readers, e.g.:
developers · data engineers · business analysts · validators ·
operations teams · onboarding engineers · reviewers · architects ·
future AI sessions

#### 3. Revision History
| Date | Author | Version | Changes | Related |
|------|--------|---------|---------|---------|
| YYYY-MM-DD | AI Agent | v1 | Initial draft | — |

### Optional Header Sections (include when applicable)

| Section | When to include |
|---------|----------------|
| Dependencies | document relies on other docs, systems, or data |
| Assumptions | facts taken as true without verification |
| Blockers / Open Questions | unresolved issues affecting completeness |
| Related Documents | companion docs, upstream/downstream references |
| Glossary | domain terms, abbreviations, status codes |
| System Boundaries | explicit in-scope vs. out-of-scope boundaries |
| Known Limitations | gaps, approximations, areas needing validation |

### Why this rule exists
Headers help readers immediately understand:
- **Why** to read the document
- **Whether** it is relevant to them
- **How mature / accurate** it is (via version + change log)
- **How it evolved** over time

---

## Code-First ETL / Data Lineage Analysis Rule (Mandatory)

When analyzing any ETL pipeline, data flow, table write mechanism, or data lineage:

1. **Read source code before concluding**: inspect relevant config files, utility functions, SQL templates, flow/task code, and write/sync helpers before making an architectural conclusion. MCP/database queries can verify the current data state, but they cannot by themselves prove why data looks that way or how a table is written.

2. **Do not infer architecture from symptoms alone**: never conclude that a table is independently maintained, incorrectly wired, or written by a separate mechanism only from NULL timestamps, row count differences, or field value mismatches. These symptoms may be caused by ETL delay, environment differences, snapshot timing, filters, SQL design, or data quality issues.

3. **If code and MCP data conflict, code has priority for design intent**: MCP/database results show a point-in-time state snapshot. Source code shows intended processing logic and write paths. Treat MCP findings as validation evidence or anomaly evidence, then reconcile them against code before documenting conclusions.

---

## Project Context
- Domain: Foreclosure rule processing / compliance automation
- Working directory: `C:\Users\jli\MyData\Copilot\ForeclosureRule2`
