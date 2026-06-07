# 06 — System Diagrams

> **Naming note (2024-07-05):** the source-table prefix is now `portnewrez*` (formerly `portshellpoint*`, the Shellpoint era); the live `newrez` schema only has `portnewrez*` — authoritative now; rename history in doc 01.

---

## Document Information

| Field | Content |
|-------|---------|
| **Purpose** | Visual representation of the entire FCL status processing system's architecture, state machine, data flow, and table dependency relationships using Mermaid diagrams. |
| **Problem solved** | Textual descriptions cannot intuitively show status transition paths and inter-table dependencies. This document supplements the text docs with six visual diagram types. |
| **Scope** | High-level data flow, FCL state transition (simple), FCL state machine (detailed), table lineage, rule layers, BPS sync dependencies |
| **System** | Full system (PrefectFlow ETL pipeline) |

**Target audience:** All roles (visual reference)

**Dependencies:** `02_etl_pipeline.md` (pipeline structure), `03_fcl_status_logic.md` (status logic), `04_status_inventory.md` (status codes)

**Revision history:**

| Date | Author | Version | Changes |
|------|--------|---------|---------|
| 2026-06-05 | AI Agent (Claude Opus 4.8) | v2 | Renamed `portshellpoint*`→`portnewrez*` (DB-verified live newrez tables; renamed 2024-07-05) + naming note (DB-verified; doc 01) |
| 2026-05-21 | AI Agent (Claude Sonnet 4.6) | v1 | Initial version, six Mermaid diagram types |

---

## Diagram 1 — High-Level Data Flow (Layer 0 → Layer 5)

```mermaid
flowchart TD
    subgraph L0["Layer 0 — Raw Data Sources"]
        S3["S3 / SMB / SFTP\nServicer files"]
    end

    subgraph L1["Layer 1 — Servicer Staging (MySQL)"]
        NR["newrez.*\nportnewrezfc/bk/lm/general"]
        SLS["sls.*\nportfcldaily/portbkdaily/portlmdaily"]
        CAR["carrington.portcarrington"]
        MRC["mrc.portmrcforeclosure"]
        FCI["fci.*"]
        SEL["selene.*"]
    end

    subgraph L2["Layer 2 — Unified Daily (Redshift)"]
        PDV2["port.portdaily_v2\nSLS+Newrez UNION"]
        BDLC["port.basic_data_daily_loan_common\nAll servicers, unified schema"]
    end

    subgraph L3["Layer 3 — Clean Daily (Redshift)"]
        CLEAN["port.basic_data_daily_loan_common_clean"]
        PDC["port.port_daily_clean"]
        DELINQ["port.basic_data_loan_delinq_clean\ndelinq_source / ghost_reason"]
    end

    subgraph L4["Layer 4 — Monthly Business (Redshift)"]
        PMB["port.portmonthbase\nPrimary analytical table"]
        BLF["port.basic_data_loan_foreclosure\nFCL timeline"]
        BLFCL["port.basic_data_loan_fcl\nFCL detail + Hold"]
        BLFH["port.basic_data_loan_foreclosure_hold"]
        BLFBK["port.basic_data_loan_foreclosure_bankruptcy"]
        BLFLM["port.basic_data_loan_foreclosure_loss_mitigation"]
        BLFR["port.basic_data_fcl_related"]
        FSI["port.fcl_stage_info\n6 stages × 5 dimensions"]
        BLREO["port.basic_data_loan_reo"]
    end

    subgraph L5["Layer 5 — BPS Sync Layer"]
        SPM["port.sync_portmonth"]
        SFL["port.sync_loan_foreclosure_loss_mitigation"]
        SFB["port.sync_loan_foreclosure_bankruptcy"]
        SFH["port.sync_loan_foreclosure_hold"]
        SFS["port.sync_fcl_stage_info"]
    end

    S3 -->|Prefect daily schedule| NR
    S3 --> SLS
    S3 --> CAR
    S3 --> MRC
    S3 --> FCI
    S3 --> SEL

    NR -->|portdaily_config.py| PDV2
    SLS --> PDV2
    NR -->|daily_data_loan_common_config.py| BDLC
    SLS --> BDLC
    CAR --> BDLC
    MRC --> BDLC
    FCI --> BDLC
    SEL --> BDLC

    PDV2 -->|daily_data_loan_common_clean_config.py| CLEAN
    BDLC --> CLEAN
    CLEAN --> PDC
    CLEAN --> DELINQ

    PDC -->|gen_portmonth_config.py| PMB
    PMB --> BLF
    PMB --> BLFCL
    PMB --> BLFH
    PMB --> BLFBK
    PMB --> BLFLM
    PMB --> BLFR
    PMB --> FSI
    PMB --> BLREO

    PMB -->|sync_to_bps_config.py| SPM
    BLFLM --> SFL
    BLFBK --> SFB
    BLFH --> SFH
    FSI --> SFS
```

---

## Diagram 2 — FCL State Transition (Simple)

```mermaid
stateDiagram-v2
    [*] --> C : Loan originated
    C --> D30 : days360 ≥ 30
    D30 --> D60 : days360 ≥ 60
    D60 --> D90 : days360 ≥ 90
    D90 --> D120P : days360 ≥ 120
    D120P --> FCL : Servicer FCL flag / svcdelinq=Foreclosure
    FCL --> REO : Auction complete / bank acquires
    FCL --> P : Paid off while in FCL
    REO --> P : REO disposition complete
    D30 --> C : Payment cured
    D60 --> C : Payment cured
    D90 --> C : Payment cured
    D120P --> C : Payment cured
    FCL --> D : Re-entry into delinquency (prevdelinq=FCL)
    REO --> D : Re-entry after REO (prevdelinq=REO)
    D120P --> D : Re-entry after serious delinq (prevdelinq=D120P)
    C --> VASP : Government loan special disposition (operational override)
    C --> P : Paid in full
    D30 --> P : Early payoff
    note right of D
        Confirmed delinquency: previous was FCL/REO/D120P, current month still delinquent
    end note
    note right of VASP
        Vendee/Servicer Purchase, Newrez only, 19 records
    end note
```

---

## Diagram 3 — FCL State Machine (Detailed, with Supplementary Flags)

```mermaid
stateDiagram-v2
    [*] --> Performing

    state Performing {
        C : Current (C)\ndays360 < 30
    }

    state Delinquent {
        D30 : 30–59 DPD
        D60 : 60–89 DPD
        D90 : 90–119 DPD
        D120P : 120+ DPD
    }

    state ForeclosureActive {
        FCL_only : FCL\n(no BK, no LM)
        FCL_BK : FCL + Bankruptcy\nbankruptcy=Y
        FCL_LM : FCL + Loss Mitigation\nlm_flag=Y
        FCL_Hold : FCL + Hold\n(30 hold types)
        FCL_Stage : FCL Stage Tracking\nDEMAND→REFERRAL→\nFIRST_LEGAL→SERVICE→\nJUDGEMENT→SALE
    }

    state Liquidated {
        P : Paid in Full (P)
        REO : REO (bank-held)
        REPUR : Repurchase (REPUR)\nCarrington only
    }

    state Special {
        VASP : VASP\nVendee/Servicer Purchase\nNewrez only
        D_conf : D (Confirmed Delinquency)\nprevdelinq=FCL/REO/D120P
    }

    Performing --> Delinquent : days360 increases
    Delinquent --> Performing : Payment cured
    Delinquent --> ForeclosureActive : FCL triggered
    ForeclosureActive --> Liquidated : Liquidation/payoff/auction complete
    ForeclosureActive --> Delinquent : FCL removed
    Liquidated --> D_conf : Delinquency re-entry
    Delinquent --> D_conf : prevdelinq=D120P\nand current still delinquent
    Performing --> Special : Operational layer override
    Performing --> Liquidated : Paid in full

    state "Override Layer" as OL {
        Fix : basic_data_loan_fix\n49 delinq overrides\nHighest priority
    }

    OL --> ForeclosureActive : Manual set to FCL
    OL --> Performing : Manual set to C
    OL --> Liquidated : Manual set to P/REO
```

---

## Diagram 4 — Table Lineage (Key FCL-Related Tables)

```mermaid
graph LR
    subgraph MySQL["MySQL (Servicer Staging)"]
        SPFC["portnewrezfc"]
        SPBK["portnewrezbk"]
        SPLM["portnewrezlm"]
        SPGEN["portnewrezgeneral"]
        SLSFC["portfcldaily"]
        SLSBK["portbkdaily"]
        SLSLM["portlmdaily"]
        SLSA["portassetdaily"]
        CARPORT["portcarrington"]
        MRCFC["portmrcforeclosure"]
    end

    subgraph RedshiftL2["Redshift L2"]
        PDV2["port.portdaily_v2"]
        BDLC["port.basic_data_daily_loan_common"]
    end

    subgraph RedshiftL3["Redshift L3"]
        BDLCC["port.basic_data_daily_loan_common_clean"]
        PDC["port.port_daily_clean"]
        BDLD["port.basic_data_loan_delinq_clean"]
    end

    subgraph RedshiftL4["Redshift L4"]
        PMB["portmonthbase ★"]
        BLF["port.basic_data_loan_foreclosure"]
        BLFCL["port.basic_data_loan_fcl"]
        BLFH["port.basic_data_loan_foreclosure_hold"]
        BLFBK["port.basic_data_loan_foreclosure_bankruptcy"]
        BLFLM["port.basic_data_loan_foreclosure_loss_mitigation"]
        BLFR["port.basic_data_fcl_related"]
        FSI["port.fcl_stage_info"]
        BLREO["port.basic_data_loan_reo"]
        FIX["port.basic_data_loan_fix"]
    end

    subgraph RedshiftL5["Redshift L5 (BPS)"]
        SPM["port.sync_portmonth"]
        SFL["port.sync_loan_foreclosure_loss_mitigation"]
        SFB["port.sync_loan_foreclosure_bankruptcy"]
        SFH["port.sync_loan_foreclosure_hold"]
        SFS["port.sync_fcl_stage_info"]
    end

    SPFC --> BDLC
    SPBK --> BDLC
    SPLM --> BDLC
    SPGEN --> PDV2
    SLSFC --> BDLC
    SLSBK --> BDLC
    SLSLM --> BDLC
    SLSA --> PDV2
    CARPORT --> BDLC
    MRCFC --> BDLC

    PDV2 --> BDLCC
    BDLC --> BDLCC
    BDLCC --> PDC
    BDLCC --> BDLD

    PDC --> PMB
    FIX -->|override| PMB
    PMB --> BLF
    PMB --> BLFCL
    PMB --> BLFH
    PMB --> BLFBK
    PMB --> BLFLM
    PMB --> BLFR
    PMB --> FSI
    PMB --> BLREO

    PMB --> SPM
    BLFLM --> SFL
    BLFBK --> SFB
    BLFH --> SFH
    FSI --> SFS
```

---

## Diagram 5 — Rule Layer (delinq Generation Priority)

```mermaid
flowchart TD
    INPUT["Loan Record\n(nextduedate, fctrdt, svcdelinq, balance, ...)"]

    INPUT --> CHECK_FIX{"basic_data_loan_fix\nhas override record?"}
    CHECK_FIX -->|Yes| OUT_FIX["Output: fix.delinq\n(highest priority)"]
    CHECK_FIX -->|No| CHECK_PAYOFF{"svcdelinq contains\n'Full Payoff'/'Paid in Full'\n'Completed Payoff' etc?\nor balance=0?"}

    CHECK_PAYOFF -->|Yes| OUT_P["Output: P"]
    CHECK_PAYOFF -->|No| CHECK_REO{"svcdelinq='REO'\nor status IN ('R','REO')?"}

    CHECK_REO -->|Yes| OUT_REO["Output: REO"]
    CHECK_REO -->|No| CHECK_FCL{"svcdelinq='Foreclosure'\nor BK-variant Foreclosure?\nor status='F' (Carrington)?"}

    CHECK_FCL -->|Yes| OUT_FCL["Output: FCL\n(BK variant: also set bankruptcy=Y)"]
    CHECK_FCL -->|No| CALC_DAYS["Calculate days360(nextduedate, fctrdt)"]

    CALC_DAYS --> CHECK_C{"< 30 days?"}
    CHECK_C -->|Yes| OUT_C["Output: C"]
    CHECK_C -->|No| CHECK_D30{"< 60 days?"}
    CHECK_D30 -->|Yes| OUT_D30["Output: D30"]
    CHECK_D30 -->|No| CHECK_D60{"< 90 days?"}
    CHECK_D60 -->|Yes| OUT_D60["Output: D60"]
    CHECK_D60 -->|No| CHECK_D90{"< 120 days?"}
    CHECK_D90 -->|Yes| OUT_D90["Output: D90"]
    CHECK_D90 -->|No| OUT_D120P["Output: D120P"]

    OUT_C --> PREVCHECK
    OUT_D30 --> PREVCHECK
    OUT_D60 --> PREVCHECK
    OUT_D90 --> PREVCHECK
    OUT_D120P --> PREVCHECK

    PREVCHECK{"prevdelinq IN\n('D120P','FCL','REO')\nAND delinq NOT IN (C,P,REO,FCL)?"}
    PREVCHECK -->|Yes| OUT_D["Override: D (Confirmed Delinquency)"]
    PREVCHECK -->|No| FINAL["Final delinq output"]

    OUT_FIX --> FINAL
    OUT_P --> FINAL
    OUT_REO --> FINAL
    OUT_FCL --> FINAL
    OUT_D --> FINAL
```

---

## Diagram 6 — BPS Sync Dependency

```mermaid
graph TD
    subgraph Source["Redshift Layer 4 (Data Source)"]
        PMB["port.portmonthbase"]
        BLF["port.basic_data_loan_foreclosure"]
        BLFLM["port.basic_data_loan_foreclosure_loss_mitigation"]
        BLFBK["port.basic_data_loan_foreclosure_bankruptcy"]
        BLFH["port.basic_data_loan_foreclosure_hold"]
        FSI["port.fcl_stage_info"]
    end

    subgraph Config["sync_to_bps_config.py"]
        K1["1-PORTMONTH"]
        K5["5-FORECLOSURE"]
        K8["8-FORECLOSURE_LM"]
        K9["9-FORECLOSURE_BK"]
        K10["10-FORECLOSURE_HOLD"]
        K12["12-FCL_STAGE"]
    end

    subgraph Target["BPS Sync Target Tables (Layer 5)"]
        SPM["port.sync_portmonth"]
        SFL["port.sync_loan_foreclosure_loss_mitigation"]
        SFB["port.sync_loan_foreclosure_bankruptcy"]
        SFH["port.sync_loan_foreclosure_hold"]
        SFS["port.sync_fcl_stage_info"]
    end

    subgraph Monitor["Execution Monitoring"]
        STATUS["port.sync_to_bps_status\ngenerate_type / status / numofrows\nmax_generate_asofdate / excute_date"]
    end

    PMB --> K1 --> SPM
    BLF --> K5
    BLFLM --> K8 --> SFL
    BLFBK --> K9 --> SFB
    BLFH --> K10 --> SFH
    FSI --> K12 --> SFS

    K1 -->|execution result| STATUS
    K5 -->|execution result| STATUS
    K8 -->|execution result| STATUS
    K9 -->|execution result| STATUS
    K10 -->|execution result| STATUS
    K12 -->|execution result| STATUS
```

---

## Chinese Version

`docs/zh/06_diagrams.md`
