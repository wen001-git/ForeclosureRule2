# doc 10 — ForeclosureRule2 Comprehensive Glossary

---

## Document Purpose

- **Why this document exists**: Business terms, ETL architecture vocabulary, MBA standard codes, and servicer-specific abbreviations are scattered across docs 01–09. This document provides a single lookup entry point.
- **Problem solved**: When any reader (new member, reviewer, or AI session) encounters an unfamiliar term in any project document, they can look it up here without searching through multiple documents.
- **Scope**: Core business statuses · Delinquency status codes · FCL process · LM types · Bankruptcy · ETL architecture · System abbreviations · Regulatory/Compliance — 8 categories, 55+ entries.
- **Not covered**: Field-level data dictionary (see `docs/foreclosure_data_dictionary.md`); servicer raw table schemas (see `docs/en/01_source_data.md`).
- **System**: ForeclosureRule2 project, PrefectFlow (Prefect 2.x mortgage loan servicing ETL system).

## Target Audience

Primary: New team members (any role) · Business analysts · Data engineers · Validators · Future AI sessions  
Secondary: Compliance reviewers · System rewrite architects · Servicer liaison personnel

## Revision History

| Date | Author | Version | Changes | Related |
|------|--------|---------|---------|---------|
| 2026-05-25 | AI Agent (Claude Sonnet 4.6) | v1 | Initial version — consolidated from docs 00–09 and foreclosure_data_dictionary.md | docs 00–09 |
| 2026-05-26 | AI Agent (Claude Sonnet 4.6) | v2 | Added 9 missing terms: NOI/Demand Letter (Category C), 3rd Party Sale (Category C), Target/Actual/Var Days framework (Category C), MFR full definition (Category E), POC (Category E), dataasof and SMS/Shellpoint (Category G); updated Category G NOI and MFR one-liners to cross-reference full entries | doc 13 v4 |
| 2026-06-02 | AI Agent (Claude Opus 4.8) | v3 | Added "Category H — Regulatory/Compliance Terms" (6 entries: CFPB, RESPA, Reg X, 12 CFR 1024.40/SPOC, 12 CFR 1024.41, Imminent Default); added CFPB/RESPA/SPOC cross-reference rows to Category G; updated scope to 8 categories | doc 14 |
| 2026-06-03 | AI Agent (Claude Opus 4.8) | v4 | Category C new term `dtdeedrecorded` (deed recorded date = title transfer / FCL legal completion, ~2–3 weeks after fcsalehelddate, mostly→REO; BPS primary source for timeline_foreclosure_completed_date, proxy for REO acquisition date); also expanded doc 14 reo_acquisition_date verify-SQL comment | doc 14 · doc 13 §3.1 |
| 2026-06-08 | AI Agent (Claude Opus 4.8) | v5 | Category C: added two consolidated terms **FCL Stages (6 stages / 8 buckets / 15 sub-stages)** and **FCL episode (one foreclosure experience)**; same source as doc 21 §0.3 terminology note | doc 21 §0.3/§3 · doc 13 · doc 17/18 |

## Dependencies

| Document | Relationship |
|----------|-------------|
| `docs/en/00_index.md` | Project navigation; contains 11-term quick reference glossary |
| `docs/en/08_servicer_fcl_field_mapping.md` | Detailed background on MBA standard, FCL process, LM types |
| `docs/en/09_servicer_data_interface_standard.md` | Field naming conventions, four-dimensional status model |
| `docs/foreclosure_data_dictionary.md` | Field-level data dictionary |

---

## Category A — Core Business Statuses

> These four dimensions are fully orthogonal — a single loan can simultaneously be in multiple states (e.g., FCL + BK + LM active at the same time).

---

**FCL** (Foreclosure)

The legal process by which a lender, following borrower default, uses the mortgage contract to pursue forced sale of the collateral property to recover the outstanding loan balance. FCL is a legal status, not a degree of delinquency — D120P (120+ days past due) does not equal FCL; FCL must be explicitly flagged by the servicer. System internal code: `FCL`.  
**Related**: Judicial Foreclosure / Non-Judicial Foreclosure (process types); REO (one possible outcome); fcl_flag (data field)

---

**REO** (Real Estate Owned)

After foreclosure proceedings complete with no third-party buyer at auction, property ownership transfers from the borrower to the lender (bank/fund). REO is one terminal outcome of FCL. System internal code: `REO`.  
**Related**: FCL (preceding status); 3rd Party Sale (alternative FCL exit); reo_flag (data field)

---

**BK** (Bankruptcy)

A borrower's petition to a federal court for bankruptcy protection under U.S. bankruptcy law. Filing immediately triggers an **Automatic Stay**, legally halting all collection actions (including any in-progress FCL). Most common types: Chapter 7 (liquidation) and Chapter 13 (reorganization).  
**Note**: The MBA `delinquency_status` `Bankruptcy` enum value and `Foreclosure` are **mutually exclusive** in a single field, so an independent `bankruptcy_flag` is needed to capture the FCL+BK coexistence scenario.  
**Related**: Automatic Stay; FCL-Hold; Chapter 7 / 13; bankruptcy_flag (data field)

---

**LM** (Loss Mitigation)

The collective term for all workout arrangements a lender negotiates with a delinquent borrower to avoid the costs of foreclosure. Includes Forbearance, Loan Modification, Repayment Plan, and others. LM is an independent dimension — it can coexist with FCL (foreclosure already initiated while LM negotiations are ongoing).  
**Related**: FCL-Hold (LM can pause FCL); lm_flag / lm_type (data fields); Category D (six LM types)

---

**Delinquency**

The status of a borrower who has not made scheduled mortgage payments, classified by Days Past Due (DPD). The system uses 8 internal status codes (see Category B). Delinquency describes a factual payment condition; FCL describes a legal action — they are not the same thing.  
**Related**: DPD; MBA standard (raw values); days360 (fallback calculation method)

---

## Category B — Delinquency Status Codes

### System Internal Codes (ETL output layer)

| Internal Code | Meaning | DPD Range |
|--------------|---------|----------|
| `C` | Current (on-time payments) | DPD < 30 days |
| `D30` | 30–59 days delinquent | 30–59 days |
| `D60` | 60–89 days delinquent | 60–89 days |
| `D90` | 90–119 days delinquent | 90–119 days |
| `D120P` | 120+ days delinquent | ≥ 120 days |
| `FCL` | Foreclosure proceedings active | Servicer-flagged; NOT DPD-calculated |
| `REO` | Real Estate Owned (bank-held property) | Post-FCL completion |
| `P` | Paid in Full / Loan terminated | Payoff, Short Sale, REO disposition, etc. |

> Internal codes are produced by ETL Step 3 (`daily_data_loan_common_clean_config.py`) mapping servicer raw data to a normalized set. Stored in the L3 Clean layer and portmonthbase.

---

### MBA Standard Raw Values (Servicer transmission layer)

> The following are raw text values transmitted by servicers (representative: Newrez, DB-verified 2026-05-25), which Step 3 maps to internal codes.

| Servicer Raw Value | Meaning | Maps to Internal Code |
|-------------------|---------|----------------------|
| `Current` | 0–29 DPD, on-time payments | → `C` |
| `1-29 DPD` | 1–29 days delinquent (Newrez sub-classification) | → `C` |
| `30-59 DPD` | 30–59 days delinquent | → `D30` |
| `60-89 DPD` | 60–89 days delinquent | → `D60` |
| `90-119 DPD` | 90–119 days delinquent | → `D90` |
| `120-149 DPD` | 120–149 days delinquent | → `D120P` |
| `150-179 DPD` | 150–179 days delinquent | → `D120P` |
| `180+ DPD` | 180+ days delinquent | → `D120P` |
| `Foreclosure` | Foreclosure proceedings active | → `FCL` |
| `Foreclosure / Non-Perf BK` | FCL + non-performing bankruptcy (Newrez compound value) | → `FCL` (+ `bankruptcy='Y'`) |
| `Foreclosure / Perf BK` | FCL + performing bankruptcy (Newrez compound value) | → `FCL` (+ `bankruptcy='Y'`) |
| `Performing Bankruptcy` | Bankruptcy but still making payments | → `D90`/`D120P` (+ `bankruptcy='Y'`) |
| `Non-Performing Bankruptcy` | Bankruptcy, not making payments | → `D120P` (+ `bankruptcy='Y'`) |
| `REO` | Bank-held property | → `REO` |
| `REO Sale` | REO disposed (sold) | → `P` |
| `Full Payoff` / `Paid in Full` | Loan fully repaid | → `P` |
| `3rd Party Sale` | Third-party auction purchase (FCL auction success) | → `P` |
| `Service Release` | Loan servicing rights transferred | → Special handling |

> **Note**: `CapeCodFive` currently transmits numeric DPD values (`'29.0'`, `'30.0'`) instead of MBA text enums, causing all status mapping to fail. This is a P0 issue. See doc 08.

---

## Category C — FCL Process Terms

**Judicial Foreclosure**

A foreclosure proceeding that requires court approval. Typical states: New York, New Jersey, Florida. Timeline: 6 months–2 years. Court involvement provides broader borrower recourse options but significantly extends the foreclosure timeline.

---

**Non-Judicial Foreclosure** (Power of Sale)

A foreclosure proceeding that does not require court involvement. The lender proceeds directly to auction per the "power of sale" clause in the mortgage contract. Typical states: California, Texas. Timeline: 3–6 months. Faster and more common across the U.S.

---

**Referral**

The first stage of the FCL process: the lender formally transfers the case to a foreclosure attorney, authorizing initiation of legal proceedings. `referral_date` marks the start of the FCL timeline.

---

**NOI / Demand Letter** (Notice of Intent / Demand Letter)

A formal written legal notice sent from the lender to the borrower **before** foreclosure officially begins, demanding that the borrower cure the default (typically within 30 days) or face initiation of the foreclosure process. NOI is a **pre-FCL** prerequisite in many states — it does not mean FCL has started.

- **Judicial states** (New York, New Jersey, Florida, etc.): typically called **Notice of Intent (NOI)** or **Notice of Default (NOD)**
- **Non-Judicial states** (California, Texas, etc.): typically called a **Demand Letter**

Newrez names its field `demandsentdate` ("Demand sent date"), reflecting the Non-Judicial terminology. BPS doc 13 uses **"NOI / Demand"** as a unified label to avoid state-specific naming confusion.  
**Related BPS fields**: `timeline_notice_of_intent_date` (sent date, sourced from `demandsentdate`), `timeline_notice_of_intent_end_date` (expiration, from `demandexpirationdate`). See doc 13 Section 3.1.  
**Related**: FCL; Referral; First Legal

---

**First Legal**

The first formal legal step taken by the foreclosure attorney on behalf of the lender (e.g., filing a complaint or recording a Notice of Default). Marks the point when the foreclosure enters the public record.

---

**Service** (Document Service)

The formal delivery of legal documents (summons, complaint) to the borrower. A required step in judicial foreclosure; the borrower has a set period after service to respond or contest.

---

**Judgment**

The court's favorable ruling for the lender, authorizing the property sale to proceed. In judicial foreclosure states, Judgment is the final legal hurdle before auction.

---

**Sale**

The final disposition stage of the FCL process: the property is sold at public auction. Outcomes:
- Third-party buyer present → `3rd Party Sale` (maps to `P`)
- No third-party buyer → property goes to lender → `REO`

---

**FCL Stages (the 6 stages)**

The ordered legal milestones one foreclosure case advances through. Standard **6-stage** order:
`DEMAND` → `REFERRAL`(to attorney) → `FIRST_LEGAL` → `SERVICE` → `JUDGEMENT`(court ruling) → `SALE`(auction).
The `fcl_stage_info` table uses these to place each loan at its **current stage** and compute time per stage (deducting non-actionable LM/Hold overlap days).

- The physical table also carries `NOI` (between Demand and Referral) and `PUBLICATION` (between Service and Judgement) buckets — usually NULL for Newrez — so only the 6 main stages are typically listed (**8 buckets total**).
- The BPS compliance target/actual/var view further splits stages into **15 sub-stages** (see doc 13 §3).

**Related**: Referral; NOI / Demand Letter; Service; Judgment; Sale; FCL episode; doc 21 §3

---

**FCL episode**

One continuous foreclosure experience for a loan: from entering foreclosure to exiting it (cured via Reinstatement / loss-mitigation / Paid, or completed via auction → REO).

- After a cure a loan can **re-enter** foreclosure = a **new episode**; multi-attempt cases are keyed by `(loanid, deal_start)`.
- Typically **loan : FCL episode = 1:1** — at most one active foreclosure at a time; across the loan's life there may be several (sequential).
- Its relationship to BK is **N:N**: one bankruptcy **automatic stay** freezes the **entire foreclosure** (across all stages, not one stage), and within one episode the borrower may file BK **multiple times**.

**Related**: FCL; BK / Bankruptcy; MFR; FCL Stages; doc 21 §0.3; doc 17 §1/§5; doc 18 §5

---

**3rd Party Sale**

An auction outcome where an external buyer successfully bids on the property — the property transfers to a third party (neither the original borrower nor the lender). This is a "successful" FCL exit. System internal code maps to `P` (Paid); the loan is closed.  
Contrasts with **REO** (no bidder; lender takes possession). Newrez records the final outcome in the `fcresults` field; BPS uses this to determine whether to populate `timeline_third_party_sold_date_date` and `timeline_third_party_proceeds_received_date` (see doc 13 Section 3.1).  
**Related**: REO; Sale; fcresults (Newrez field)

---

**dtdeedrecorded** (Deed Recorded Date)

A Newrez `portnewrezfc` date field: the date the post-sale property-transfer deed (Trustee's / Sheriff's Deed) is **officially recorded** in the county land records — i.e., the **legal completion point** of foreclosure, when title transfers (usually to the lender → **REO**, occasionally to a third-party buyer).  
It occurs ~**2–3 weeks after** `fcsalehelddate` (sale held date) in observed samples, with `fcresults=REO / fcremovaldesc=Process Complete`. BPS uses it as the **primary source** for `timeline_foreclosure_completed_date = COALESCE(dtdeedrecorded, fcremovaldate)`; since Newrez has no dedicated "REO acquisition date" field, doc 14 uses `dtdeedrecorded` as a **proxy** for `reo_acquisition_date`. Fill rate is very low (~0%; few loans reach title transfer).  
**Related**: Sale Held (`fcsalehelddate`); `fcremovaldate` (FCL removal/closure date); REO; `timeline_foreclosure_completed_date` (BPS)

---

**Target Days / Actual Days / Var Days**

BPS's three-layer framework for measuring FCL per-stage compliance performance (see doc 13 Sections 3.2–3.4):

| Dimension | BPS Field Prefix | Data Source | Meaning |
|-----------|-----------------|-------------|---------|
| **Target Days** | `target_*` | System configuration constants (by state / judicial type) | Compliance benchmark days per stage; independent of Newrez |
| **Actual Days** | `actual_*` | DATEDIFF between two timeline endpoint dates | Actual days elapsed in each stage |
| **Var Days** (Variance) | `var_*` | `actual_* − target_*` | Positive = behind target; Negative = ahead; Zero = on target |

15 FCL stages each have a corresponding target/actual/var field set, plus `*_total` (end-to-end sum).  
**Related**: doc 13 Sections 3.2/3.3/3.4; `bpms_dev.sync_loan_foreclosure` (BPS MySQL storage table)

---

## Category D — LM Types (Six)

**Forbearance**

A temporary suspension or reduction of the borrower's monthly payment obligation, with the deferred amount repaid later (typically in installments added to regular payments). Typical duration: 3–12 months. Heavily used during COVID-19. A temporary arrangement; upon expiration converts to Modification or resumes normal payments.

---

**Loan Modification**

Permanent modification of loan terms (interest rate, repayment term, principal balance) to bring the monthly payment to an affordable level. The most comprehensive LM solution. Once executed, the loan returns to performing status.

---

**Repayment Plan**

The borrower resumes normal monthly payments while simultaneously repaying past-due arrears in installments. Typically runs 3–6 months in parallel with normal payment schedule. Suitable for borrowers whose short-term hardship has been resolved.

---

**Trial Period Plan**

A probationary period (typically 3 months) before a permanent Modification takes effect. The borrower must make 3 on-time payments at the proposed new terms. Pass → Permanent Modification; Fail → LM application denied.

---

**Short Sale**

The lender agrees to accept a sale price below the outstanding loan balance and waives the deficiency. The loan closes after the short sale completes, mapping to `P`. Considered a "controlled foreclosure alternative."

---

**Deed in Lieu** (Deed in Lieu of Foreclosure)

The borrower voluntarily transfers property ownership to the lender in exchange for full release from the mortgage obligation. Achieves the same end result as foreclosure (lender obtains the property) but avoids a public auction, reducing costs and reputational harm for both parties. Maps to `P`.

---

## Category E — Bankruptcy-Related Terms

**Automatic Stay**

A federal legal protection that takes effect **immediately upon a bankruptcy filing**, automatically halting all collection actions, including: phone collection, legal proceedings, and foreclosure processes (creating FCL Hold). No separate court order is required — filing for bankruptcy activates it instantly.  
**FCL impact**: Any in-progress FCL enters Hold status until the bankruptcy proceeding concludes or the court lifts the stay (via MFR).

---

**Chapter 7** (Liquidation Bankruptcy)

Under Chapter 7 of the U.S. Bankruptcy Code, a court-appointed trustee liquidates the debtor's non-exempt assets to repay creditors; remaining unsecured debts are discharged. Typical duration: 3–6 months — the fastest bankruptcy type.  
**FCL impact**: Chapter 7 generally cannot save the home; foreclosure typically resumes after BK proceedings close (though the Automatic Stay provides temporary protection during the case).

---

**Chapter 13** (Reorganization Bankruptcy)

Under Chapter 13 of the U.S. Bankruptcy Code, the debtor proposes a 3–5 year repayment plan to gradually pay down debts (including mortgage arrears) while retaining the property. Primary option for borrowers who want to use bankruptcy to save their home.  
**FCL impact**: Chapter 13 can "cure" mortgage arrears; FCL remains paused throughout the plan's execution period.

---

**FCL-Hold** (Foreclosure Hold / Pause)

An operational state where foreclosure proceedings have been legally initiated (FCL flag = Y) but are operationally paused.  
**Common causes**: Automatic Stay (BK) / Borrower LM application / HUD special requirements / COVID forbearance / Court order.  
**MBA framework behavior**: MBA `delinquency_status` has no Hold classification — the loan still reports as `Foreclosure`. A separate `fcl_hold_flag` + `hold_reason` field is therefore required to represent Hold status.  
**Related**: Automatic Stay; LM; hold_flag / hold_reason (data fields)

---

**MFR** (Motion for Relief from Automatic Stay)

A formal motion filed by the lender (creditor) in bankruptcy court, requesting that the court lift the Automatic Stay so that foreclosure collection actions can resume. If granted, the FCL process can proceed out of Hold status.  
**Typical scenario**: After a Chapter 7 bankruptcy filing, the lender believes the borrower has no intent to retain the property or the repayment plan is infeasible, and files MFR to accelerate resumption of foreclosure.  
**Related BPS fields**: `mfr_filed_date` (date MFR was filed), `mfr_status` (MFR hearing outcome). See doc 13 Section 6.  
**Related**: Automatic Stay; FCL-Hold; BK; Chapter 7 / 13

---

**POC** (Proof of Claim)

A formal written document filed by a creditor (lender) in bankruptcy court to officially assert the amount of the debt owed, including principal, interest, late fees, and other charges. Filing a POC is a required step to protect the lender's creditor rights in a bankruptcy proceeding.  
**Deadline**: Chapter 7 — typically within 70 days of the creditor notice; Chapter 13 — before plan confirmation.  
**Consequence of non-filing**: If a POC is not timely filed, the creditor's claim may be excluded from the bankruptcy estate distribution.  
**Related BPS fields**: `proof_of_claim_date` (date POC was filed). See doc 13 Section 6.  
**Related**: BK; Automatic Stay; Chapter 7 / 13; MFR

---

## Category F — ETL Architecture Terms

**L1** (Raw Data Layer / MySQL Staging)

ETL pipeline layer 1: MySQL staging tables where servicer raw files are loaded before any normalization. Data comes directly from servicers. Table naming pattern: `port{servicer}loan` (e.g., `portslsloan`, `portnewrezloan`).  
**Characteristics**: Inconsistent column names across servicers, non-standardized values, separate tables per servicer.

---

**L2** (Normalized Layer / Redshift Unified Schema)

ETL pipeline layer 2: Redshift intermediate tables with a unified schema after normalization. Core tables: `port.basic_data_daily_loan_common` (daily) / `port.basic_data_monthly_loan_common` (monthly).  
**Characteristics**: Each servicer's fields are mapped to common column names, but status determination logic (e.g., FCL) has not yet been applied.

---

**L3** (Clean Layer / Post–Status Determination)

ETL pipeline layer 3: Data after Step 3 processing, where `delinq` status codes have been determined and data quality has been validated.  
**Related**: Step 3; daily_data_loan_common_clean_config.py

---

**L4** (Monthly Aggregation Layer)

ETL pipeline layer 4: Month-granularity aggregation tables. Core tables: `portmonthbase` (primary monthly table) / `portmonth` (extended with monthly derived fields). Used for BPS reporting and downstream analytics.

---

**Step 3**

The core Python ETL script responsible for status determination: `daily_data_loan_common_clean_config.py`. Role: reads L2 data and maps each servicer's raw fields to system internal status codes (`delinq` = C/D30/…/FCL/REO/P) per servicer-specific rules.  
**When Step 3 is absent**: If a servicer has no corresponding SQL logic block in Step 3, the `delinq` field will always be null (classic cases: Selene, FCI).  
**Related**: L2 → L3 transformation node

---

**portmonthbase**

The primary Redshift monthly analytical table (L4 layer), containing a month-end status snapshot for each loan. The core data source for BPS reporting and monthly reconciliation. Approximately 120 columns, including system logic fields.  
**Related**: portmonth (adds 23 derived fields on top of portmonthbase)

---

**basic_data_loan_fix**

A manual override correction table storing human-reviewed status corrections for specific loans. Has the **highest priority** in the ETL pipeline, overriding all automated calculations.  
**Purpose**: Corrects edge-case errors caused by servicer data quality issues or system logic limitations.

---

**days360**

A day-count function that calculates the difference between two dates using the 360-day year convention (30 days per month). Used for the industry-standard DPD calculation: `DPD = days360(next_payment_due_date, report_date)`.  
**Importance**: When a servicer does not provide `delinquency_status` (e.g., Arvest monthly reports), `next_payment_due_date` + days360 is the only fallback method for DPD calculation.

---

**fctrdt** (FCT Report Date)

The report cutoff date, typically the first day of the following month after month-end (e.g., March month-end → April 1). The primary time dimension key for portmonthbase and monthly report analysis. Format: `YYYY-MM-DD`.

---

## Category G — System Abbreviations / Terminology

| Term | Full Form | Meaning |
|------|-----------|---------|
| **UPB** | Unpaid Principal Balance | The outstanding principal amount remaining on a loan — the primary measure of loan size. |
| **DPD** | Days Past Due | The number of days a payment is overdue, calculated using days360 from `next_payment_due_date` to the report date. |
| **MBA** | Mortgage Bankers Association | U.S. industry association that sets the standard delinquency classification system used in this project (text enum values for `delinquency_status`). |
| **NOI** | Notice of Intent / Notice of Default | Formal pre-FCL written notice from lender to borrower demanding cure of default. See Category C "NOI / Demand Letter" for full definition. |
| **MFR** | Motion for Relief (from Automatic Stay) | Lender's court motion to lift the Automatic Stay and resume FCL. See Category E "MFR" for full definition. |
| **BPS** | Business Planning System | PrefectFlow's downstream reporting consumer system. Monthly analytical results are ultimately synced to BPS. |
| **Servicer** | Mortgage Loan Servicer | Institution managing day-to-day loan administration on behalf of the loan owner (e.g., a fund) — collecting payments, tracking delinquency, executing foreclosure. This project covers 8 servicers: SLS / Newrez / Carrington / Selene / MRC / Arvest / CapeCodFive / FCI. |
| **Deal ID** | Portfolio / Deal Identifier | Business identifier grouping multiple loans into a single investment portfolio. One servicer may service multiple deals. |
| **svcdelinq** | Servicer Delinquency | Raw delinquency status text as transmitted by the servicer, stored in L2, before normalization. Distinct from the system's standardized `delinq` internal code. |
| **dataasof** | Data As Of | The snapshot date of data synchronized from a servicer (e.g., Newrez), typically 1–2 days behind today. BPS adds `DATEDIFF(today, dataasof)` when displaying FCL days-in-flight to compensate for this lag and reflect the true current-day count. |
| **SMS** | Shellpoint Mortgage Servicing | The operational sub-brand name of Newrez (Newrez LLC rebranded from Shellpoint, but some legacy field names retain the abbreviation). The BPS field `smsdaysinfc` ("SMS-reported FCL days") uses this abbreviation, corresponding to the servicer-reported perspective vs. the investor-basis `daysinfc`. |
| **CFPB** | Consumer Financial Protection Bureau | U.S. federal consumer-finance regulator; its mortgage-servicing rules (Reg X) are the regulatory basis for this project's LM/FCL compliance fields. See Category H. |
| **RESPA** | Real Estate Settlement Procedures Act | The parent statute that Reg X implements. See Category H. |
| **SPOC** | Single Point of Contact | The single designated servicer contact for a delinquent borrower, required by CFPB Reg X 12 CFR 1024.40; maps to field `single_point_of_contact`. See Category H. |

---

## Category H — Regulatory / Compliance Terms

**CFPB** (Consumer Financial Protection Bureau)

U.S. federal regulatory agency established by the Dodd-Frank Act (2010), responsible for writing and enforcing consumer-finance protection rules (including mortgages). The loss-mitigation / foreclosure compliance requirements on servicers (e.g., Newrez) in this project derive from CFPB rules.

---

**RESPA** (Real Estate Settlement Procedures Act)

U.S. federal law governing real-estate settlement and mortgage-servicing conduct. CFPB implements RESPA's mortgage-servicing provisions through **Reg X**.

---

**Reg X** (Regulation X — 12 CFR Part 1024)

The implementing regulation for RESPA, codified at Title 12, Part 1024 of the Code of Federal Regulations. Its mortgage-servicing provisions (1024.30–1024.41, effective 2014) define servicer obligations toward delinquent borrowers and loss mitigation (LM) — the regulatory source for this project's LM/FCL compliance fields.

---

**12 CFR 1024.40 / SPOC** (Continuity of Contact / Single Point of Contact)

Reg X 1024.40 requires the servicer to assign a delinquent borrower a **Single Point of Contact (SPOC)**, so the borrower is not repeatedly handed off among agents during the LM process. Maps to the BPS field `single_point_of_contact` (Newrez does not provide it; always NULL — see doc 13 Q6 / doc 14).

---

**12 CFR 1024.41** (Loss Mitigation Procedures)

Reg X 1024.41 prescribes the procedures and timelines for evaluating a borrower's LM options before advancing foreclosure (complete-application review period, appeal rights, etc.). It is the compliance backdrop for the LM Cycle fields.

---

**Imminent Default**

A state where a borrower is **not yet delinquent** but faces foreseeable repayment hardship. Reg X / investor guidelines require the servicer to evaluate such borrowers for LM proactively, rather than waiting for actual default. Maps to the BPS field `imminent_default` (Newrez does not provide it; always NULL — see doc 13 Q6 / doc 14).
