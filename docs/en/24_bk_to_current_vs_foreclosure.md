# 24 — BK → Current vs. BK → Foreclosure: The Core Difference

---

## Document Information

| Field | Content |
|-------|---------|
| **Purpose** | The state machine (`fcl_pipeline.html` / doc 17 §4 / doc 07 §2.4) draws two edges out of the **BK — Bankruptcy** node — one to **C (Current)** and one to **FCL (Foreclosure)**. This note explains the core difference between those two edges, what triggers each, and the legal basis — as a standalone, shareable topic. |
| **Problem solved** | Readers often assume "BK succeeds → Current, BK fails → foreclosure". The real dividing line is **whether the mortgage default (arrears) gets cured** — which is NOT the same as whether the bankruptcy is "discharged" (a Ch.7 discharge usually leads to foreclosure). |
| **Scope** | Only the difference, triggers, and legal basis of the BK node's two out-edges; NOT the full bankruptcy primer (see doc 17 §5.4 / doc 07 §2.5) nor BK→payoff duration (see doc 23). |
| **System fit** | A topic expansion of the "BK state-transition legal basis" in doc 17 §5.4 / doc 07 §2.5; all statutory basis comes from Title 11 (Cornell LII) and U.S. Courts Bankruptcy Basics. |

**Target audience:** business analysts · data product managers · operations · new joiners · ETL developers · validation/reconciliation engineers · risk / asset management · future AI sessions

**Revision history:**

| Date | Author | Version | Changes | Related |
|------|--------|---------|---------|---------|
| 2026-06-08 | AI Agent (Claude Opus 4.8) | v1 | Initial version: BK→Current vs BK→Foreclosure core difference, triggers, comparison table, legal basis & authoritative sources, system pass-through note | doc 17 · doc 07 · doc 23 |

## Known Limitations

- This is business/legal background, not a substitute for legal advice or compliance determination.
- State-level foreclosure/bankruptcy procedures vary; this note describes the federal Bankruptcy Code (Title 11) in general terms.

---

## 1. Question

In the state machine, **BK** has two out-edges — `BK → C` and `BK → FCL`. What is the **core difference**?

## 2. The core difference, in one sentence

**It comes down to whether the bankruptcy actually "cured" the mortgage default:**
- **BK → Current**: the bankruptcy (Chapter 13) **cured the past-due mortgage and reinstated the loan** → home kept, delinq returns to `C`. The **cure / success** path.
- **BK → Foreclosure**: the bankruptcy ended with the mortgage default **still unresolved**, and the automatic stay was removed → the lender **resumes foreclosure**. The **not-cured / stay-lifted** path.

> Key: the dividing line is **whether the mortgage arrears were cured**, **not** whether the bankruptcy was "discharged". A Ch.7 discharge only releases personal liability; the lien survives, so it usually leads to foreclosure.

## 3. The two edges in detail

### 3.1 BK → Current ("Ch.13 done")

- The borrower files **Chapter 13** (reorganization / repayment plan) and, over **3–5 years**, **cures the past-due mortgage (arrears)** while keeping current payments.
- On completing all plan payments, a discharge is granted, the mortgage is reinstated → delinq returns to `C`, home kept.
- Legal mechanism:
  - **§ 1322(b)(5)**: the plan may "cure any default within a reasonable time and maintain payments".
  - **§ 1328(a)**: discharge "after completion … of all payments under the plan".
- U.S. Courts: *"The individual may then **bring the past-due payments current** over a reasonable period of time."*

### 3.2 BK → Foreclosure ("BK lifted/discharged → resume")

The bankruptcy ends with the mortgage default **unresolved**; the automatic stay (§ 362) no longer protects the borrower, and foreclosure resumes. Three triggers:

| Trigger | Mechanism | Statute |
|---------|-----------|---------|
| **Dismissal / plan failure** | Ch.13 plan not performed (payments stopped), case dismissed, stay terminates | § 362(c) |
| **Relief from stay (MFR) granted** | Lender files a Motion for Relief; once granted, foreclosure may continue | § 362(d) |
| **Ch.7 discharge** | Ch.7 releases only **personal liability**; the **lien survives**; arrears not cured → home can still be foreclosed | § 727 + § 524(a)(2) |

- U.S. Courts: *"Creditors have the right to ask the bankruptcy court to **lift the stay** … If the stay is lifted, the creditor may then proceed … **completing its foreclosure action**."*

## 4. Comparison table

| Dimension | BK → Current | BK → Foreclosure |
|-----------|--------------|------------------|
| Mortgage default cured? | **Yes** (arrears fully repaid) | **No** (default remains) |
| Typical chapter | **Chapter 13** (reorganization, keep home) | **Chapter 7** (liquidation, lose home) or **dismissed Ch.13** |
| Exit mechanism | Plan completed → discharge, loan reinstated | Stay removed: dismissal / MFR / lien survives after Ch.7 |
| Fate of the automatic stay | Ends after serving its purpose | **Terminated / lifted early**, foreclosure resumes |
| Home outcome | Kept | Heading to auction (→ FCL → REO / 3rd-party sale) |
| Statutory basis | § 1322(b)(5) cure + § 1328(a) discharge | § 362(c) termination / § 362(d) MFR / § 727 + § 524(a)(2) |

## 5. Chapter view: Ch.7 vs Ch.13

- **Chapter 13 (reorganization)** = designed to **keep the home**: cure arrears + maintain payments → usually **→ Current**.
- **Chapter 7 (liquidation)** = discharges personal debt but **does not remove the lien**: arrears not cured, lien survives → usually **→ Foreclosure**.
- **Caveat**: Ch.7 ≠ always foreclosure — if the borrower reaffirms and keeps paying, it can return to Current; but in this system these are **already severely delinquent + already-in-FCL** loans, so the typical Ch.7 path is "personal liability released, lien survives → foreclosure resumes". That's why the diagram routes Ch.13 to C and discharge/lifted to FCL.

## 6. The automatic-stay layer

- Filing bankruptcy → **§ 362(a)** automatic stay immediately freezes foreclosure (FCL → FCL-Hold; see doc 17 §5.4 "automatic stay ≠ permanent ban on sale").
- **Two exits** decide which edge is taken:
  - **Exit via cure** (Ch.13 completed) → stay served its purpose, loan reinstated → **Current**.
  - **Exit via the stay being removed** (dismissal / § 362(d) MFR / lien surviving Ch.7) → **Foreclosure**.

## 7. Relationship to this system (important)

These edges are **legally** valid, but this ETL does **not compute** them — it just passes through the servicer-reported `delinquency_status_mba` each month:

- delinq becomes `C` only when the servicer re-reports `Current` (e.g., after Ch.13 completion);
- it goes to FCL only when the servicer reports `Foreclosure` again.

The system **reflects** outcomes, it does not **derive** them (see `03_fcl_status_logic.md` §2.1 lines 77–114; `Foreclosure / Perf·Non-Perf BK` is mapped to `FCL` by `CREATE_FCL_RELATE_ATTR`).

## 8. Authoritative sources

- [Chapter 13 — Bankruptcy Basics (U.S. Courts)](https://www.uscourts.gov/court-programs/bankruptcy/bankruptcy-basics/chapter-13-bankruptcy-basics)
- [Chapter 7 — Bankruptcy Basics (U.S. Courts)](https://www.uscourts.gov/court-programs/bankruptcy/bankruptcy-basics/chapter-7-bankruptcy-basics)
- [11 U.S.C. § 1322 (cure + maintain)](https://www.law.cornell.edu/uscode/text/11/1322)
- [11 U.S.C. § 1328 (discharge on plan completion)](https://www.law.cornell.edu/uscode/text/11/1328)
- [11 U.S.C. § 362 (automatic stay / relief from stay)](https://www.law.cornell.edu/uscode/text/11/362)
- [11 U.S.C. § 727 (Ch.7 discharge)](https://www.law.cornell.edu/uscode/text/11/727)
- [11 U.S.C. § 524 (effect of discharge — personal liability only)](https://www.law.cornell.edu/uscode/text/11/524)

## 9. Related Documents

- BK business & legal basis: doc 17 §5.4, doc 07 §2.5
- State machine & transitions: doc 17 §4, doc 07 §2.4, `outputs/fcl_pipeline.html`
- BK discharge → payoff duration (DB-verified): doc 23
