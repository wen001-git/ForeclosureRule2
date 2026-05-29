# 06 — 系统图表汇总

---

## 文档信息

| 项目 | 内容 |
|------|------|
| **文档目的** | 以 Mermaid 图表形式直观呈现整个止赎状态处理系统的架构、状态机、数据流向和表依赖关系。 |
| **解决的问题** | 文字描述难以直观展示状态转换路径和表间依赖，本文档通过六类图补充视觉化理解。 |
| **覆盖范围** | 高层数据流、FCL 状态转换（简）、FCL 状态机（详）、表血缘、规则层次、BPS 同步依赖 |
| **系统归属** | 全系统（PrefectFlow ETL pipeline） |

**目标读者：** 所有角色（可视化参考）

**依赖文档：** `02_etl_pipeline.md`（管道结构）、`03_fcl_status_logic.md`（状态逻辑）、`04_status_inventory.md`（状态代码）

**修订历史：**

| 日期 | 作者 | 版本 | 变更内容 |
|------|------|------|---------|
| 2026-05-21 | AI Agent (Claude Sonnet 4.6) | v1 | 初始版本，六类 Mermaid 图 |

---

## 图 1 — 高层数据流（Layer 0 → Layer 5）

```mermaid
flowchart TD
    subgraph L0["Layer 0 — 原始数据来源"]
        S3["S3 / SMB / SFTP\n服务商文件"]
    end

    subgraph L1["Layer 1 — 服务商暂存（MySQL）"]
        NR["newrez.*\nportshellpointfc/bk/lm/general"]
        SLS["sls.*\nportfcldaily/portbkdaily/portlmdaily"]
        CAR["carrington.portcarrington"]
        MRC["mrc.portmrcforeclosure"]
        FCI["fci.*"]
        SEL["selene.*"]
    end

    subgraph L2["Layer 2 — 统一日数据（Redshift）"]
        PDV2["port.portdaily_v2\nSLS+Newrez UNION"]
        BDLC["port.basic_data_daily_loan_common\n所有服务商统一 schema"]
    end

    subgraph L3["Layer 3 — 清洗日数据（Redshift）"]
        CLEAN["port.basic_data_daily_loan_common_clean"]
        PDC["port.port_daily_clean"]
        DELINQ["port.basic_data_loan_delinq_clean\ndelinq_source / ghost_reason"]
    end

    subgraph L4["Layer 4 — 月度业务层（Redshift）"]
        PMB["port.portmonthbase\n主分析表"]
        BLF["port.basic_data_loan_foreclosure\nFCL时间线"]
        BLFCL["port.basic_data_loan_fcl\nFCL明细+Hold"]
        BLFH["port.basic_data_loan_foreclosure_hold"]
        BLFBK["port.basic_data_loan_foreclosure_bankruptcy"]
        BLFLM["port.basic_data_loan_foreclosure_loss_mitigation"]
        BLFR["port.basic_data_fcl_related"]
        FSI["port.fcl_stage_info\n6阶段×5维度"]
        BLREO["port.basic_data_loan_reo"]
    end

    subgraph L5["Layer 5 — BPS 同步层"]
        SPM["port.sync_portmonth"]
        SFL["port.sync_loan_foreclosure_loss_mitigation"]
        SFB["port.sync_loan_foreclosure_bankruptcy"]
        SFH["port.sync_loan_foreclosure_hold"]
        SFS["port.sync_fcl_stage_info"]
    end

    S3 -->|Prefect 日调度| NR
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

## 图 2 — FCL 状态转换（简版）

```mermaid
stateDiagram-v2
    [*] --> C : 贷款正常
    C --> D30 : days360 ≥ 30
    D30 --> D60 : days360 ≥ 60
    D60 --> D90 : days360 ≥ 90
    D90 --> D120P : days360 ≥ 120
    D120P --> FCL : servicer FCL flag / svcdelinq=Foreclosure
    FCL --> REO : 拍卖完成/银行接管
    FCL --> P : 止赎中还清
    REO --> P : REO处置完成
    D30 --> C : 还款恢复
    D60 --> C : 还款恢复
    D90 --> C : 还款恢复
    D120P --> C : 还款恢复
    FCL --> D : 止赎后再次逾期 (prevdelinq=FCL)
    REO --> D : REO后再次逾期 (prevdelinq=REO)
    D120P --> D : 严重逾期后再次逾期 (prevdelinq=D120P)
    C --> VASP : 政府贷款特殊处置 (运营覆盖)
    C --> P : 全额还清
    D30 --> P : 提前还清
    note right of D
        确认逾期：之前为FCL/REO/D120P，且当月仍逾期
    end note
    note right of VASP
        Vendee/Servicer Purchase，仅 Newrez，19条
    end note
```

---

## 图 3 — FCL 状态机（详版，含辅助标志）

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
        FCL_Hold : FCL + Hold\n(30种 hold 类型)
        FCL_Stage : FCL 阶段跟踪\nDEMAND→REFERRAL→\nFIRST_LEGAL→SERVICE→\nJUDGEMENT→SALE
    }

    state Liquidated {
        P : Paid in Full (P)
        REO : REO (银行持有)
        REPUR : Repurchase (REPUR)\nCarrington only
    }

    state Special {
        VASP : VASP\nVendee/Servicer Purchase\nNewrez only
        D_conf : D (确认逾期)\nprevdelinq=FCL/REO/D120P
    }

    Performing --> Delinquent : days360 递增
    Delinquent --> Performing : 还款恢复
    Delinquent --> ForeclosureActive : FCL 触发
    ForeclosureActive --> Liquidated : 清算/还清/拍卖完成
    ForeclosureActive --> Delinquent : 撤销止赎
    Liquidated --> D_conf : 再次出现逾期
    Delinquent --> D_conf : prevdelinq=D120P\n且当月仍逾期
    Performing --> Special : 运营层覆盖
    Performing --> Liquidated : 全额还清

    state "Override Layer" as OL {
        Fix : basic_data_loan_fix\n49条 delinq 覆盖\n最高优先级
    }

    OL --> ForeclosureActive : 手工设为 FCL
    OL --> Performing : 手工设为 C
    OL --> Liquidated : 手工设为 P/REO
```

---

## 图 4 — 表血缘关系（主要 FCL 相关表）

```mermaid
graph LR
    subgraph MySQL["MySQL（服务商暂存）"]
        SPFC["portshellpointfc"]
        SPBK["portshellpointbk"]
        SPLM["portshellpointlm"]
        SPGEN["portshellpointgeneral"]
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

    subgraph RedshiftL5["Redshift L5（BPS）"]
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
    FIX -->|覆盖| PMB
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

## 图 5 — 规则层次（delinq 生成优先级）

```mermaid
flowchart TD
    INPUT["贷款记录\n(nextduedate, fctrdt, svcdelinq, balance, ...)"]

    INPUT --> CHECK_FIX{"basic_data_loan_fix\n有覆盖记录？"}
    CHECK_FIX -->|是| OUT_FIX["输出：fix.delinq\n(最高优先级)"]
    CHECK_FIX -->|否| CHECK_PAYOFF{"svcdelinq 含\n'Full Payoff'/'Paid in Full'\n'Completed Payoff'等？\n或 balance=0？"}

    CHECK_PAYOFF -->|是| OUT_P["输出：P"]
    CHECK_PAYOFF -->|否| CHECK_REO{"svcdelinq='REO'\n或 status IN ('R','REO')？"}

    CHECK_REO -->|是| OUT_REO["输出：REO"]
    CHECK_REO -->|否| CHECK_FCL{"svcdelinq='Foreclosure'\n或含 'BK' 的 Foreclosure？\n或 status='F'（Carrington）？"}

    CHECK_FCL -->|是| OUT_FCL["输出：FCL\n（BK 类同时设 bankruptcy=Y）"]
    CHECK_FCL -->|否| CALC_DAYS["计算 days360(nextduedate, fctrdt)"]

    CALC_DAYS --> CHECK_C{"< 30 天？"}
    CHECK_C -->|是| OUT_C["输出：C"]
    CHECK_C -->|否| CHECK_D30{"< 60 天？"}
    CHECK_D30 -->|是| OUT_D30["输出：D30"]
    CHECK_D30 -->|否| CHECK_D60{"< 90 天？"}
    CHECK_D60 -->|是| OUT_D60["输出：D60"]
    CHECK_D60 -->|否| CHECK_D90{"< 120 天？"}
    CHECK_D90 -->|是| OUT_D90["输出：D90"]
    CHECK_D90 -->|否| OUT_D120P["输出：D120P"]

    OUT_C --> PREVCHECK
    OUT_D30 --> PREVCHECK
    OUT_D60 --> PREVCHECK
    OUT_D90 --> PREVCHECK
    OUT_D120P --> PREVCHECK

    PREVCHECK{"prevdelinq IN\n('D120P','FCL','REO')\n且 delinq∉(C,P,REO,FCL)？"}
    PREVCHECK -->|是| OUT_D["覆盖：D（确认逾期）"]
    PREVCHECK -->|否| FINAL["最终 delinq 输出"]

    OUT_FIX --> FINAL
    OUT_P --> FINAL
    OUT_REO --> FINAL
    OUT_FCL --> FINAL
    OUT_D --> FINAL
```

---

## 图 6 — BPS 同步依赖关系

```mermaid
graph TD
    subgraph Source["Redshift Layer 4（数据源）"]
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

    subgraph Target["BPS 同步目标表（Layer 5）"]
        SPM["port.sync_portmonth"]
        SFL["port.sync_loan_foreclosure_loss_mitigation"]
        SFB["port.sync_loan_foreclosure_bankruptcy"]
        SFH["port.sync_loan_foreclosure_hold"]
        SFS["port.sync_fcl_stage_info"]
    end

    subgraph Monitor["执行监控"]
        STATUS["port.sync_to_bps_status\ngenerate_type / status / numofrows\nmax_generate_asofdate / excute_date"]
    end

    PMB --> K1 --> SPM
    BLF --> K5
    BLFLM --> K8 --> SFL
    BLFBK --> K9 --> SFB
    BLFH --> K10 --> SFH
    FSI --> K12 --> SFS

    K1 -->|执行结果| STATUS
    K5 -->|执行结果| STATUS
    K8 -->|执行结果| STATUS
    K9 -->|执行结果| STATUS
    K10 -->|执行结果| STATUS
    K12 -->|执行结果| STATUS
```

---

## 对应英文版

英文版：`docs/en/06_diagrams.md`
