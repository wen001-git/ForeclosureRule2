# 23 — BK Discharge → Payoff (P) Duration Analysis (DB-verified)

---

## Document Information

| Field | Content |
|-------|---------|
| **Purpose** | Answer a common business question — "how long does a loan take to go from bankruptcy discharge to final payoff (the P — Loan ends state)?" — and lock down the prod-verified conclusion, definitions, and verification SQL for reuse and review. |
| **Problem solved** | The state machine (`fcl_pipeline.html` / doc 17 §4 / doc 07 §2.4) draws the `BK → discharge → … → P` edge but gives **no duration**, and can mislead readers into thinking discharge quickly leads to payoff. This note corrects that intuition with prod data. |
| **Scope** | Only the elapsed time between the "BK-ended date" and the "payoff date", its definitions and limitations; NOT the legal explanation of BK (see doc 17 §5.4 / doc 07 §2.5) nor the full FCL timeline (see doc 25–30). |
| **System fit** | A **data-evidence supplement** to the "BK state transitions" content in doc 17 / doc 07; all conclusions come from read-only queries against `redshift_prod` (prod Redshift). |

**Target audience:** business analysts · data product managers · validation/reconciliation engineers · data engineers · risk / asset management · future AI sessions

**Revision history:**

| Date | Author | Version | Changes | Related |
|------|--------|---------|---------|---------|
| 2026-06-08 | AI Agent (Claude Opus 4.8) | v1 | Initial version: BK discharge → payoff duration DB-verified (prod Redshift), definitions, per-loan detail, interpretation & limitations, verification SQL | doc 17 · doc 07 · doc 21 |

## Dependencies

| Document | Use |
|----------|-----|
| `17_foreclosure_business_primer.md` §5.4 (zh) | BK business meaning + per-transition legal basis (§ 362/§ 727/§ 1322/§ 1328/§ 524) |
| `07_fcl_lineage_and_rules.md` §2.5 | Same (en/zh) |
| `21_fcl_field_lineage.md` | FCL/BK field lineage |

## Known Limitations

> ⚠️ **The sample is tiny and the "duration" is reconstructed, not recorded** (see §6, §7). **Do not use for statistical inference or external reporting** — this is a description of the current data state only.

---

## 1. Question

> How long does a loan typically take to go from **BK discharge** to **P (Loan ends / paid off)**?

## 2. Conclusion (TL;DR)

**Production data cannot yield a meaningful "BK discharge → P duration" — in the data these are two essentially unrelated events about 15 years apart.**

- Loans for which both a "BK-ended date" and a "payoff date" exist (broad scope): **11 loans**, gap **135–199 months (~11–16.6 years)**, median **186 months (≈15.5 years)**, average 172.7 months.
- Strict scope `bankruptcy_status='Discharged'` only: **4 loans**, gap 186–193 months (≈15.5–16 years).
- These numbers are **not a process duration** — they are the span between a **long-ago historical BK discharge** (2008–2014) and a **recent, independently-caused payoff** (2023–2026).

This **empirically confirms the legal fact**: **Ch.7 / Ch.11 discharge ≠ payoff** — it only releases personal liability; the mortgage lien survives, the loan keeps existing for over a decade, and only later pays off for independent reasons (refinance / sale / maturity) — see the § 727 / § 524(a)(2) basis in doc 17 §5.4 / doc 07 §2.5. In other words, `BK discharge → P` is legally possible, but **there is no characteristic duration in the data**.

## 3. Data Sources & Fields (schema-verified)

| Event | Table | Columns | Note |
|-------|-------|---------|------|
| BK-ended date (discharge proxy) | `port.basic_data_loan_foreclosure_bankruptcy` | `bankruptcy_status`, `status_date` | **No dedicated discharge-date column**; `status_date` (the date of the current BK legal status) is used as a proxy. BK table is only 74 rows / 69 loans across 8 dataasof (2024-07~2026-06), FCL-family servicers only (Newrez/Carrington/CapeCodFive). |
| Payoff date (P) | `port.basic_data_loan_funding` | `paidoffdate` | 1,081 loans portfolio-wide have a payoff date. |
| Join key | both tables | `loanid` | — |

`bankruptcy_status` value distribution (measured): `Completed/Cancelled` 32, `Discharged` 17, `Active` 17, `Dismissed` 4, `ReliefGranted` 3, `Closed` 1.

## 4. Method

1. From the BK table, take "BK-ended" loans and their `status_date`:
   - **Strict scope** = `bankruptcy_status='Discharged'`;
   - **Broad scope** = `Discharged` + `Completed/Cancelled` + `Closed` + `Dismissed` + `ReliefGranted`.
2. Join to `basic_data_loan_funding.paidoffdate` on `loanid`, keep only `paidoffdate IS NOT NULL` and `paidoffdate >= bk_end_date`.
3. Duration = `DATEDIFF(day, bk_end_date, paidoffdate)`; months = `/30.44`.

## 5. Results (prod, 2026-06-08)

### 5.1 Summary

| Scope | Loans | Min (mo) | Median (mo) | Avg (mo) | Max (mo) |
|-------|-------|----------|-------------|----------|----------|
| Strict (`Discharged`) | 4 | 186.0 | ~191.4 | ~190.4 | 192.9 |
| Broad (any BK-ended status) | 11 | 135.2 | 186.0 | 172.7 | 199.2 |

### 5.2 Per-loan detail (11 loans)

| loanid | servicer | Chapter | BK status | BK-ended date | payoff date | Duration (mo) |
|--------|----------|---------|-----------|---------------|-------------|---------------|
| 7727004377 | Newrez | 7 | Discharged | 2009-06-01 | 2024-11-30 | 186.0 |
| 7727004650 | Newrez | 11 | Discharged | 2010-06-03 | 2026-03-31 | 189.9 |
| 7727004651 | Newrez | 11 | Discharged | 2010-06-03 | 2026-06-30 | 192.9 |
| 7727004649 | Newrez | 11 | Discharged | 2010-06-03 | 2026-06-30 | 192.9 |
| 7727004393 | Newrez | 7 | Closed | 2014-12-24 | 2026-03-31 | 135.2 |
| 7727000979 | Carrington | 13 | Completed/Cancelled | 2012-11-06 | 2024-03-31 | 136.8 |
| 7727000910 | Carrington | 7 | Completed/Cancelled | 2012-02-27 | 2024-08-31 | 150.1 |
| 7727000983 | Carrington | 13 | Completed/Cancelled | 2011-02-17 | 2024-10-31 | 164.4 |
| 7727000883 | Carrington | 7 | Completed/Cancelled | 2011-10-31 | 2025-08-31 | 166.0 |
| 7727000904 | Carrington | 7 | Completed/Cancelled | 2008-06-09 | 2023-12-31 | 186.7 |
| 7727000880 | Carrington | 13 | Completed/Cancelled | 2008-12-23 | 2025-07-31 | 199.2 |

## 6. Interpretation: why this is not a real "duration"

- `status_date` records the servicer-reported **historical legal status date** — the table above shows these bankruptcies were discharged/ended back in **2008–2014**.
- `paidoffdate` values are all in **2023–2026**.
- The ~**15-year** gap is a period during which the loan simply stayed in the portfolio, performing normally.
- **Discharge did not "cause" the payoff**: the two are over a decade apart and unrelated. Ch.7/Ch.11 discharge only releases personal liability; the lien survives, the loan persists, and it pays off years later for independent reasons.
- **So `BK discharge → P` has no characteristic duration**; the state-machine edge represents a "legally possible path", not a measurable elapsed time.

## 7. Data Limitations

1. **No dedicated discharge-date column**; `status_date` used as a proxy.
2. **BK table is a current-state snapshot with tiny coverage**: 74 rows / 69 loans, FCL-family servicers only; not an event log.
3. **Sample too small**: only 17 discharged loans, of which only 4 have a payoff (broad scope 11) — not statistically meaningful.
4. **The system passes through servicer status and does not record state transitions** (see doc 07 §2.5 / `03_fcl_status_logic.md` §2.1); this result is reconstructed by joining two tables, not a recorded transition event.
5. All queries are `redshift_prod` **read-only**; no writes performed.

## 8. Verification SQL (redshift_prod)

### 8.1 Per-loan detail

```sql
WITH bk AS (
  SELECT loanid, servicer, chapter, bankruptcy_status,
         MIN(status_date) AS bk_end_date          -- discharge-date proxy (no dedicated discharge column)
  FROM port.basic_data_loan_foreclosure_bankruptcy
  WHERE bankruptcy_status IN ('Discharged','Completed/Cancelled','Closed','Dismissed','ReliefGranted')
    AND status_date IS NOT NULL
  GROUP BY loanid, servicer, chapter, bankruptcy_status
)
SELECT bk.loanid, bk.servicer, bk.chapter, bk.bankruptcy_status,
       bk.bk_end_date, f.paidoffdate,
       DATEDIFF(day, bk.bk_end_date, f.paidoffdate)                 AS days_to_payoff,
       ROUND(DATEDIFF(day, bk.bk_end_date, f.paidoffdate)/30.44, 1) AS months_to_payoff
FROM bk
JOIN port.basic_data_loan_funding f ON f.loanid = bk.loanid       -- payoff date source
WHERE f.paidoffdate IS NOT NULL
ORDER BY (bk.bankruptcy_status='Discharged') DESC, days_to_payoff;
```

### 8.2 Summary statistics

```sql
WITH bk AS (
  SELECT loanid, bankruptcy_status, MIN(status_date) AS bk_end_date
  FROM port.basic_data_loan_foreclosure_bankruptcy
  WHERE bankruptcy_status IN ('Discharged','Completed/Cancelled','Closed','Dismissed','ReliefGranted')
    AND status_date IS NOT NULL
  GROUP BY loanid, bankruptcy_status
),
d AS (
  SELECT bk.loanid, DATEDIFF(day, bk.bk_end_date, f.paidoffdate)/30.44 AS months_to_payoff
  FROM bk JOIN port.basic_data_loan_funding f ON f.loanid = bk.loanid
  WHERE f.paidoffdate IS NOT NULL AND f.paidoffdate >= bk.bk_end_date
)
SELECT COUNT(*) loans,
       ROUND(MIN(months_to_payoff),1) min_m,
       ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY months_to_payoff),1) median_m,
       ROUND(AVG(months_to_payoff),1) avg_m,
       ROUND(MAX(months_to_payoff),1) max_m
FROM d;   -- → 11 loans, min 135.2, median 186.0, avg 172.7, max 199.2 (months)
```

> Note: `MEDIAN(x)` raises `transaction is read-only` under this read-only role; use `PERCENTILE_CONT(0.5) WITHIN GROUP (...)` instead.

## 9. Related Documents

- BK legal basis (§ 362/§ 727/§ 1322/§ 1328/§ 524): doc 17 §5.4, doc 07 §2.5
- State machine & transitions: doc 17 §4, doc 07 §2.4, `outputs/fcl_pipeline.html`
- FCL/BK field lineage: doc 21
