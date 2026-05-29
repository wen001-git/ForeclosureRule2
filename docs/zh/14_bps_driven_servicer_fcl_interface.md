# doc 14 — BPS 驱动的 Servicer FCL 数据接口规范

---

## 文档目的

- **为什么存在**：Doc 09（行业标准视角）从 CFPB/MBA 规范出发，定义了 Servicer 应当提供哪些抽象字段。本文档从另一方向出发——以 BPS Asset Management Foreclosure 五大功能面板的**实际显示需求**为终点，逆向还原每个面板所需的 Servicer 源字段，形成 BPS 落地层的具体数据接口规范。
- **解决的问题**：当团队需要向新 Servicer 提出"你必须提供哪些数据"时，需要一份以 BPS 展示为依据、可直接作为正式字段补全请求依据的文件，而非仅凭行业规范。
- **范围**：覆盖 BPS Foreclosure 五大面板所需的全部 Servicer 字段（约 92 个）；含 doc 09 四维状态基础标志层（12 个）+ BPS 展示明细层（68 个）+ Newrez 已提供高价值增强字段层（12 个）；以 Newrez 为合规基准；不涉及 ETL 中间层代码细节（见 doc 12）。
- **系统关系**：本文是 doc 09 的 BPS 落地实施版本。Doc 09 = 行业准入标准（29 个抽象字段）；本文 = BPS 系统上线标准（约 92 个具体字段，含基础标志层、面板明细层、Newrez 增强层与合规现状）。

## 目标读者

主要读者：**数据治理团队 · 新 Servicer 对接工程师 · BPS 系统运营人员**  
次要读者：数据质量工程师 · 合规分析师 · 未来 AI Session

## 修订历史

| 日期 | 作者 | 版本 | 变更说明 | 关联文档 |
|------|------|------|---------|---------|
| 2026-05-27 | AI Agent (Claude Sonnet 4.6) | v1 | 初稿：7个Section + 附录A；以BPS五大面板为终点逆向定义约67个Servicer字段规范；Newrez合规现状基于doc 13 MCP实测（2026-05） | doc 09, doc 13 |
| 2026-05-28 | AI Agent (Claude Sonnet 4.6) | v2 | 新增附录B：ETL中间表 `port.basic_data_loan_fcl` 全字段用途分类（✅ BPS已使用 vs 🔮 ETL归一化/未进BPS）；涵盖约37个业务字段；4个预留字段（`fcjudgment_end_date`/`titleordereddate`/`jr_sr_lien_flag`/`activejnrlienfcflag`）标注未来用途与设计意图 | doc 12 v5, doc 13 v21 |
| 2026-05-28 | AI Agent (Codex) | v3 | 增加接口标准审核状态：确认 doc 14 可作为后续逐 Servicer 缺口分析的目标标准；明确字段级审核准入、冻结范围、仍需业务确认的问题 | doc 13 v21, doc 15 |
| 2026-05-28 | AI Agent (Claude Sonnet 4.6) | v4 | 全部 7 张字段规范表（Section 2.1–2.5、3.1、4.1）新增第 2 列「业务含义/计算逻辑（如有）」：覆盖全部 67 个字段的业务语义、派生公式和 Newrez 特殊说明；Section 2 格式说明同步更新 | doc 13 |
| 2026-05-28 | AI Agent (Claude Sonnet 4.6) | v5 | Section 2.3 新增 `noi_date` 字段（NOI 正式止赎意向通知与 Demand Sent Date 催款函概念分离）；更新 `demand_sent_date` 的 BPS 映射说明与业务含义；Section 5.1/5.2 字段计数同步更新（68 个，❌ 7 个 Newrez 未提供） | — |
| 2026-05-28 | AI Agent (Claude Sonnet 4.6) | v6 | 新增 Section 2.0「四维状态基础标志字段」（12 个字段：delinquency_status/next_payment_due_date/days_past_due/foreclosure_flag/lm_flag/lm_type/lm_start_date/lm_end_date/hold_flag/hold_reason/reo_flag/reo_acquisition_date）；补充 delinquency_status MBA 允许值表；文档范围更新至约 80 个字段；Section 5.1 合规矩阵新增基础状态字段行；Section 1.4 对比表更新 | doc 09 |
| 2026-05-28 | AI Agent (Claude Sonnet 4.6) | v7 | MCP 实测发现 Newrez 已提供但系统未利用的高价值字段（查询 portnewrezfc 62列 + portnewrezgeneral 100+列）；新增 Section 2.6「贷款属性与风险增强字段」（9个：investor_loan_id/lien_position/interest_paid_through_date/in_auction_flag/borrower_deceased_flag/reason_for_default/hold_1/2/3_comment）；Section 2.4 补充 hold_1/2/3_modified_date（P2）；记录零填充字段（SR Lien/SCRA/FEMA 等）为未来扩展；文档范围更新至约 92 个字段 | MCP 实测 2026-05 |

## 依赖文档

| 文档 | 说明 |
|------|------|
| doc 09 | 行业标准视角字段规范（CFPB/MBA 29个字段），P0/P1/P2优先级定义与本文一致 |
| doc 13 | Newrez 字段反向映射实测（MCP 验证，2026-05）；Newrez 各字段填充率、数据质量问题（Q1–Q11）均来自该文档 |
| doc 12 | ETL 管道与中间表细节（本文不展开） |
| `basic_data_pool_config.py` | ETL 字段映射源码（Redshift 中间表 → BPS MySQL） |

## 已知限制

- Newrez 填充率数据基于 MCP 实测（2026-05-24，约 13,321 笔活跃 FCL 贷款），可能随时间变化
- BK 面板中 `bkstatus`/`bkstage` 数字编码的解码行为尚未完全确认（见 Q7 in doc 13）
- 其他 Servicer 的合规现状需另行实测；本文以 Newrez 为合规基准示例

## 相关文档

| 文档 | 说明 |
|------|------|
| doc 08 | Newrez 字段映射状态（整体视角） |
| doc 09 | 行业标准字段规范（本文的"上游标准"） |
| doc 10 | ForeclosureRule2 全局术语表 |
| doc 13 | Newrez BPS 展示字段反向映射（本文数据来源） |

---

## 审核状态（v3）

**结论**：本文档可以作为后续逐 Servicer 缺口分析的目标接口标准，但不是最终对外合同版本。它当前适合作为内部数据产品、数据治理、ETL 和 BPS 运营之间的统一评审基线。

### 已冻结的判断口径

| 项目 | v3 审核结论 |
|---|---|
| 字段范围 | 以 BPS Foreclosure 五大面板和两个聚合视图为终点，覆盖 FCL 主表、Hold、LM、BK、Stage/Timeline 的字段需求 |
| 优先级口径 | P0=入库前提；P1=核心展示/运营判断；P2=增强分析或合规补充 |
| Newrez 基准 | Newrez 作为第一个 benchmark Servicer；字段填充率和 Q1-Q12 问题沿用 doc 13 的 MCP 实测 |
| ETL 中间层 | 中间层字段不作为对 Servicer 的直接请求名称，但用于解释当前系统能否接收、归一化、同步到 BPS |
| 后续文档使用方式 | 每个 Servicer 独立文档必须逐项对照本文 Section 2-4 和附录 A，输出 `已提供 / 部分提供 / 未提供 / 内部可推导 / 内部 ETL 缺口` |

### 字段准入检查规则

后续新增或调整字段时，必须同时满足以下检查，才能进入本文档的正式字段清单：

| 检查项 | 要求 |
|---|---|
| BPS 需求来源 | 能指向 doc 13 的 BPS 面板、BPS sync 表、或 BPS 聚合视图字段 |
| 业务含义 | 能用业务语言说明该字段解决什么运营/合规问题 |
| 数据来源 | 至少能明确当前 Newrez benchmark 的来源字段、派生规则或缺失原因 |
| 系统链路 | 能说明该字段是否已进入 PrefectFlow ETL、中间表、BPS sync 表 |
| 缺失影响 | 能说明缺失后是拒绝入库、面板空白、计算不准，还是仅影响增强分析 |

### 仍需业务/工程确认的问题

| 问题 | 当前处理方式 | 后续动作 |
|---|---|---|
| BK 面板 `bkstatus` / `bkstage` 是否应在 BPS 侧解码为文本 | 保留为已知限制；不阻塞 doc 14 作为接口标准 | 在 Newrez BK 专项核对时确认解码表来源 |
| `noi_start_date` 与 `demand_start_date` 的 BPS 展示差异 | doc 14 按 doc 13 结论记录：Newrez `demandsentdate` 进入 `demand_start_date`，不是 Time Line Tab 的 `NOI Date 1` | 与 BPS 前端/产品确认是否需要调整显示名称 |
| `actual_judgement_hearing_set_days` 的最终计算来源 | 暂按 doc 13 Q12 记录为来源不明；`fcjudgment_end_date` 作为未来 ETL 化候选 | 后续代码审查或 BPS 应用层确认 |
| P2 字段是否必须向全部 Servicer 请求 | 默认不作为入库阻断；用于正式字段补全请求时按 Servicer 业务价值排序 | 在逐 Servicer 文档中分别给出建议 |

---

## Section 1：总体架构与设计原则

### 1.1 BPS 五大面板字段需求分布

| BPS 面板 | 页面类型 | Servicer 来源表 | 主要字段组 |
|---|---|---|---|
| FCL Milestone 时间线 | 贷款详情页 | `portnewrezfc` | `timeline_*`（19个日期字段） |
| FCL Summary 摘要 | 贷款详情页 | `portnewrezfc` | `summary_*`（16个状态字段） |
| Hold 记录历史 | 贷款详情页 | `portnewrezfc` | Hold 槽位 3×4 字段 |
| Loss Mitigation Cycle | 贷款详情页 | `portnewrezlm` | LM 周期字段（10列） |
| Bankruptcy | 贷款详情页 | `portnewrezbk` | BK 字段（10+列） |
| Aggregate Stage Tab | 聚合概览页 | `portnewrezfc` | Stage 分组 + 天数统计 |
| Aggregate Time Line Tab | 聚合概览页 | `portnewrezfc` | 7个里程碑日期列（1–7） |

### 1.2 优先级定义

与 doc 09 保持一致：

| 优先级 | 含义 | 缺失后果 |
|--------|------|---------|
| **P0** | 系统入库前提条件 | 缺失则拒绝入库，BPS 无法处理该贷款 |
| **P1** | 核心面板显示字段 | 缺失则对应 BPS 面板数据异常或显示空白（降级可用） |
| **P2** | 增强型分析字段 | 可选；存在时启用对应分析功能；缺失不影响主流程 |

### 1.3 三张 Newrez 来源表与 BPS 面板的对应关系

```
Newrez 来源表                   → BPS 面板
portnewrezfc (FCL主表)          → FCL Summary / Timeline / Stage Tab /
                                   Time Line Tab / Hold 面板 / Bid Approval
portnewrezlm (LM表)             → Loss Mitigation Cycle 面板
portnewrezbk (BK表)             → Bankruptcy 面板
```

> **注**：`portnewrezfc` 是核心表，承担了 BPS 绝大多数面板的数据来源。LM 和 BK 各自独立，每张表对应一个专属面板。

### 1.4 本文与 doc 09 的差异

| 维度 | Doc 09（行业标准） | 本文（BPS 落地标准） |
|------|------------------|-------------------|
| 视角 | CFPB/MBA 行业规范出发 | BPS 五大面板显示需求出发 |
| 字段数量 | 29 个抽象字段，分 7 组 | 约 92 个具体字段（12 个基础状态标志 + 68 个 BPS 展示明细 + 12 个 Newrez 增强字段），含 Newrez 原始字段名 |
| 优先级 | P0/P1/P2（本文沿用） | 同左 |
| BPS 面板映射 | 无 | 每个字段明确标注喂入哪个 BPS 面板 |
| Newrez 现状 | 无 | 每个字段标注 Newrez 填充率 / 合规状态 |
| 用途 | 行业准入标准参考 | 向 Servicer 发出正式字段补全请求的依据 |

---

## Section 2：FCL 主数据字段规范（来源：`portnewrezfc`）

> **字段规范表格格式说明**：
>
> | 标准接口字段名 | Newrez 原始字段 | 类型 | 优先级 | 格式要求 | 喂入的 BPS 面板/功能 | Newrez 现状 |
>
> **Newrez 现状列取值**：`✅ 已提供（fill%）` / `⚠️ 部分提供（fill%）` / `❌ 未提供（0%）` / `N/A 推导字段`

### 2.0 四维状态基础标志字段（衔接 doc 09 行业标准）

> **本节定位**：来自 doc 09 Group B/D/E/F/G 的高层抽象字段，是 Servicer 数据接口的**行业标准最小集**。后续 Section 2.1–4.1 是 BPS 系统展示所需的补充明细字段。向新 Servicer 提出字段补全请求时，**必须先满足本节 P0 字段**，再谈后续明细字段。  
> **与 Section 2.1–4.1 的关系**：本节字段是"维度标志层"（告诉系统这笔贷款处于哪个状态维度）；后续各节是"明细层"（具体时间线、周期记录、金额等）。两层互补，不重复。

| 标准接口字段名 | Newrez 原始字段 | 类型 | 优先级 | 允许值/格式 | BPS 系统功能 | Newrez 现状 |
|---|---|---|---|---|---|---|
| `delinquency_status` | `delinquency_status_mba` | VARCHAR ENUM | **P0** | MBA 标准文本枚举（见下方允许值表） | ETL 入库筛选；FCL/LM/BK 状态识别基础；`sync_fcl_stage_info` D120P 次筛选触发；禁止使用数字字符串（`'29.0'`）| ✅ `delinquency_status_mba` 已提供（含 12K+ FCL 行） |
| `next_payment_due_date` | `nextduedate`（来源表：`portnewrezpmt`） | DATE | **P0** | YYYY-MM-DD | days360 兜底计算基准；ETL 以 `days360(nextduedate, dataasof)` 推导 DPD | ✅ `portnewrezpmt.nextduedate` 已提供，活跃 FCL 填充率 **100%**（MCP 实测）|
| `days_past_due` | *(无；ETL 推导)* | INTEGER | P1 | 0–999 正整数 | 与 `delinquency_status` 交叉校验；ETL 以 `days360(nextduedate, dataasof)` 计算；Newrez 有 `portnewrezgeneral.mbadelinquency`（**月数**，非天数，整型）可辅助参考 | N/A 推导字段（Newrez 无原生 DPD 天数字段；`mbadelinquency` = 月数，不可直接用作 DPD 天数）|
| `foreclosure_flag` | `fcl_flag` | CHAR(1) | **P0** | `Y` / `N` | FCL 活跃状态明确标志；对应 BPS `active_fcl_flag`（0/1 Newrez 专用）；`Y` = 止赎法律程序已正式启动 | 🟡 `portnewrezfc.fcl_flag` 存在但 ETL 当前置为 null（内部 ETL 问题，见 doc 09 Section 5.2；应作为首要修复项） |
| `lm_flag` | `activelmflag` | CHAR(1) | **P0** | `Y` / `N` | LM 活跃顶层标志；ETL 决定贷款是否进入 LM 处理通道；对应 BPS LM Cycle 面板的来源判断 | 🟡 部分提供（有标志，无 type/日期） |
| `lm_type` | *(无对应字段)* | VARCHAR ENUM | P1 | `Forbearance`/`Modification`/`RepaymentPlan`/`TrialPlan`/`ShortSale`/`DeedInLieu` | LM 处置类型标准化；对应 `lm_deal` 字段的行业标准版本 | ❌ 未提供（Newrez 以 `lmdeal` 数字编码代替，非标准枚举） |
| `lm_start_date` | `dealstartdate` | DATE | P1 | YYYY-MM-DD | LM 方案开始日；对应 Section 3.1 `lm_cycle_open_date` | 🟡 周期层面有 `dealstartdate`（LM 周期开始日） |
| `lm_end_date` | `lmremovaldate` | DATE | P1 | YYYY-MM-DD | LM 方案到期日；对应 Section 3.1 `lm_cycle_close_date` | 🟡 周期层面有 `lmremovaldate` |
| `hold_flag` | *(无顶层字段)* | CHAR(1) | P1 | `Y` / `N` | FCL 是否处于暂停（Hold）状态的顶层标志；对应 Section 2.4 槽位字段 | ❌ 无独立顶层 flag（`fchold1startdate` 可推导，但非正式 flag） |
| `hold_reason` | `fchold1description` | VARCHAR ENUM | P1 | `BK`/`LM`/`HUD`/`Covid`/`Other` | Hold 原因标准化枚举；Section 2.4 `hold_1_description` 是其自由文本版本 | ❌ Newrez 提供自由文本（如"Court Delay"），无标准枚举 |
| `reo_flag` | *(无对应字段)* | CHAR(1) | **P0** | `Y` / `N` | 止赎完成、房产已归贷款方所有的明确标志 | ❌ 未提供 |
| `reo_acquisition_date` | *(无对应字段)* | DATE | P1 | YYYY-MM-DD | REO 房产正式转让至贷款方的日期 | ❌ 未提供 |

**业务含义/计算逻辑**

| 标准接口字段名 | 业务含义/计算逻辑 |
|---|---|
| `delinquency_status` | MBA 标准逾期状态文本枚举；四维模型中"维度 A"的核心字段；Servicer 必须使用枚举文本（不得用数字 DPD）；FCL 状态识别（`Foreclosure` 枚举值）、BK 状态识别（`Bankruptcy` 枚举值）、REO 识别均依赖此字段 |
| `next_payment_due_date` | 下一应付款日；来源：`newrez.portnewrezpmt.nextduedate`（DATE，活跃 FCL 100% 填充）；ETL 用 `days360(nextduedate, dataasof)` 计算 DPD 天数；是 `delinquency_status` 缺失时的 DPD 兜底推导来源 |
| `days_past_due` | 数字型逾期天数；Newrez **无原生 DPD 天数字段**——ETL 以 `days360(nextduedate, dataasof)` 计算；`portnewrezgeneral.mbadelinquency` 为**月数**（整型，如 13 = 13个月逾期），不可直接作为 DPD 天数使用；与 `delinquency_status` 交叉校验，发现格式错误时用于替代推导 |
| `foreclosure_flag` | FCL 法律程序是否已正式启动的明确 Y/N 标志；**绝不能从 `days_past_due` 推算**（逾期 120 天 ≠ 止赎，FCL 需要 Servicer 显式提供）；对应 BPS `active_fcl_flag`（0=N / 1=Y）|
| `lm_flag` | LM 方案是否当前活跃的顶层 Y/N 标志；决定 ETL 是否读取 LM 明细字段；独立于 FCL 维度（可与 FCL 并存） |
| `lm_type` | LM 方案类型标准枚举；影响系统处理逻辑（Forbearance = 临时性，Modification = 永久性）；Newrez 以 `lmdeal` 数字编码提供，需 ETL 解码映射 |
| `lm_start_date` | LM 方案开始日期（顶层汇总）；Newrez 在 LM 周期表（`portnewrezlm`）中以 `dealstartdate` 提供 |
| `lm_end_date` | LM 方案到期日期（顶层汇总）；Newrez 在 LM 周期表中以 `lmremovaldate` 提供；到期是否续签是核心决策点 |
| `hold_flag` | FCL 是否处于暂停（Hold）状态的顶层标志；Newrez 通过 `fchold1startdate IS NOT NULL` 可推导，但非正式 flag；需向 Servicer 明确要求独立标志 |
| `hold_reason` | Hold 原因标准化枚举（`BK`/`LM`/`HUD`/`Covid`/`Other`）；Newrez 提供自由文本（如"Loss Mitigation Workout"），无标准化 |
| `reo_flag` | 止赎完成后房产归贷款方所有的明确标志；Newrez 目前未提供独立 REO flag，需通过 `fcresults` 或 `delinquency_status='REO'` 推导 |
| `reo_acquisition_date` | REO 房产转让至贷款方的日期；影响 REO 持有时间计算；Newrez 未提供 |

> **`delinquency_status` 允许值（MBA 标准，来自 doc 09 Group B）**：
>
> | 允许值 | 内部映射码 | 说明 |
> |---|---|---|
> | `Current` | `C` | 0–29 DPD，正常还款 |
> | `1-29 DPD` | `C` | 细分版本（Newrez 等使用） |
> | `30-59 DPD` | `D30` | — |
> | `60-89 DPD` | `D60` | — |
> | `90-119 DPD` | `D90` | — |
> | `120-149 DPD` | `D120P` | — |
> | `150-179 DPD` | `D120P` | — |
> | `180+ DPD` | `D120P` | — |
> | `Foreclosure` | `FCL` | FCL 法律程序已启动 |
> | `REO` | `REO` | 止赎完成，房产归贷款方 |
> | `Bankruptcy` / `Performing Bankruptcy` / `Non-Performing Bankruptcy` | 按 DPD + `bankruptcy_flag='Y'` | 破产须同时通过 `bankruptcy_flag`/`active_bk_flag` 传递 |
> | `PaidOff` / `Full Payoff` / `Paid in Full` | `P` | 已还清 |
> | `REO Sale` / `3rd Party Sale` | `P` | 处置完成 |
> | `Service Release` | 特殊处理 | 贷款服务权转让 |
>
> ⚠️ **禁止格式**：`'29.0'`、`'30.0'`、`'90.0'` 等数字字符串（CapeCodFive 当前违反此规范，导致 FCL 永远无法被识别）

---

### 2.1 贷款识别与入库筛选字段（P0 — 必须字段）

这些字段是 BPS 入库的**前提条件**；任何一项缺失将导致整条贷款记录无法进入 BPS 系统。

| 标准接口字段名 | Newrez 原始字段 | 类型 | 优先级 | 格式要求 | 喂入的 BPS 面板/功能 | Newrez 现状 |
|---|---|---|---|---|---|---|
| `loan_id` | `loanid` | VARCHAR | **P0** | 纯数字字符串，全系统主键 | 所有面板；BPS 全局 JOIN Key | ✅ 100% |
| `servicer_loan_id` | `shellpointloanid` | VARCHAR | **P0** | Servicer 内部编号 | FCL Summary `summary_servicer_number` | ✅ 100% |
| `data_as_of_date` | `dataasof` | DATE | **P0** | YYYY-MM-DD | 快照日期；天数计算基准（SMS/Days in FCL 实时修正） | ✅ 100% |
| `state` | `state` | CHAR(2) | **P0** | US state code（大写） | Stage 分组；目标天数配置依据 | ✅ 100% |
| `judicial_flag` | `judicial` | TINYINT | **P0** | 1=司法州 / 0=非司法州 | FCL Summary Judicial/Non-Judicial；Stage 分流判断 | ✅ 100% |
| `active_fcl_flag` | `activefcflag` | TINYINT | **P0** | 0=已完结 / 1=进行中（NULL 视为 1） | BPS 入库条件之一；历史 NULL 需 NULL-safe 处理（见 doc 13 Q3） | ✅ 100%（含历史NULL） |
| `fcl_referral_date` | `fcreferraldate` | DATE | **P0** | YYYY-MM-DD | **BPS 入库核心前提**；`timeline_referred_to_foreclosure_date`；Timeline 起点 | ✅ 100% |

**业务含义/计算逻辑**

| 标准接口字段名 | 业务含义/计算逻辑 |
|---|---|
| `loan_id` | 贷款在全系统的唯一数字标识符；贯穿所有 BPS 面板和表的全局 JOIN Key |
| `servicer_loan_id` | Servicer 内部编号；与 loan_id 是不同维度的标识，用于双方系统双向核对 |
| `data_as_of_date` | 本批次数据的截止快照日期（通常滞后当天 1–2 天）；BPS 实时修正公式：`smsdaysinfc + DATEDIFF(今日NY, dataasof)` |
| `state` | 房产所在州代码（大写两位）；决定适用的止赎法律程序（Judicial/Non-Judicial）和 BPS 各阶段目标天数配置 |
| `judicial_flag` | 是否走司法程序（需法院判决才能拍卖）；影响 Stage 分流逻辑（JUDGEMENT 阶段仅 Judicial 州适用）和时间线字段含义 |
| `active_fcl_flag` | 止赎是否仍在进行中；0=已结案，1=进行中，历史 NULL 保守视为进行中（见 doc 13 Q3 技术详解） |
| `fcl_referral_date` | 贷款方将止赎案件正式移交律师事务所的日期；**BPS 入库核心条件**（非空才收录）；时间线的法律起点 |

### 2.2 FCL 状态字段（P1 — FCL Summary 面板核心）

| 标准接口字段名 | Newrez 原始字段 | 类型 | 优先级 | 格式要求 | 喂入的 BPS 面板/功能 | Newrez 现状 |
|---|---|---|---|---|---|---|
| `fcl_stage` | `fcstage` | VARCHAR | P1 | 文本（Newrez 系统内部阶段描述） | FCL Summary `summary_current_step`（次优先；`currentmilestone` 为空时使用） | ✅ 99.5% |
| `current_milestone` | `currentmilestone` | VARCHAR | P1 | BPS 里程碑标签文本 | FCL Summary `summary_current_step`（**最优先**） | ⚠️ 62.7%（填充率偏低） |
| `last_step_completed` | `lastfcstepcompleted` | VARCHAR | P1 | 文本 | FCL Summary `summary_last_step_completed` | ✅ 99.5% |
| `last_step_completed_date` | `lastfcstepcompleteddate` | DATE | P1 | YYYY-MM-DD | FCL Summary `summary_last_step_completed_date` | ✅ 99.5% |
| `fcl_results` | `fcresults` | VARCHAR | P1 | 文本；典型值：`3rd Party`/`REO` | FCL Summary（完结贷款）；`timeline_third_party_sold_date_date` 触发逻辑 | ⚠️ 2.1%（仅完结贷款有值） |
| `attorney_firm` | `fcfirm` | VARCHAR | P1 | 文本 | FCL Summary `summary_foreclosure_attorney` / `summary_firm` | ✅ 100% |
| `contested_flag` | `fccontestedflag` | TINYINT | P1 | 0/1 | FCL Summary `summary_contested_litigation` | ✅ 100% |
| `sms_days_in_fcl` | `smsdaysinfc` | INTEGER | P1 | 正整数（Servicer 视角天数，以 dataasof 为基准） | FCL Summary `summary_sms_days_in_fcl`（BPS 实时加补 dataasof 滞后天数） | ✅ 100% |
| `days_in_fcl` | `daysinfc` | INTEGER | P1 | 正整数（投资者视角天数） | FCL Summary `summary_days_in_fcl`（同上，BPS 实时修正） | ✅ 100% |

**业务含义/计算逻辑**

| 标准接口字段名 | 业务含义/计算逻辑 |
|---|---|
| `fcl_stage` | Newrez 系统内部当前工作步骤文本描述（如"Pre-Sale Review"）；`summary_current_step` 次优先展示字段（`currentmilestone` 为空时使用） |
| `current_milestone` | BPS 里程碑标签（由 BPS 内部流程或运营写入）；`summary_current_step` **最优先**展示字段 |
| `last_step_completed` | 最近一次已完成的止赎处理步骤文本（如"Motion for Judgment Sent to Court"）；供运营追踪进度 |
| `last_step_completed_date` | 上述步骤的完成日期 |
| `fcl_results` | FCL 最终处置结果（仅完结贷款有值）；典型值：`3rd Party`（第三方购买）/ `REO`（银行取回）；`fcresults='3rd Party'` 时触发 `timeline_third_party_sold_date_date` 逻辑 |
| `attorney_firm` | 负责处理本止赎案件的律师事务所全称 |
| `contested_flag` | 是否存在争议诉讼（借款人提出法律抗辩）；1=有争议 / 0=无争议 |
| `sms_days_in_fcl` | Servicer（SMS/Newrez）视角的 FCL 在途天数（以 dataasof 为基准）；BPS 实时修正：`smsdaysinfc + DATEDIFF(今日NY, dataasof)` |
| `days_in_fcl` | 投资者视角的 FCL 在途天数；计算口径与 sms_days_in_fcl 有所不同；BPS 同样实时修正：`daysinfc + DATEDIFF(今日NY, dataasof)` |

### 2.3 FCL 时间线字段（P0/P1/P2 — Timeline 面板 + Aggregate Time Line Tab）

> **注**：本节字段对应两个 BPS 展示位置：
> 1. **贷款详情页 FCL Milestone 时间线**：`timeline_*` 字段（19个）
> 2. **聚合概览页 Time Line Tab**：`{stage}_start_date` 字段（7列，见 Section 7）

| 标准接口字段名 | Newrez 原始字段 | 类型 | 优先级 | BPS 面板/字段 | Newrez 现状 |
|---|---|---|---|---|---|
| `noi_date` | *(无；Newrez 以 `demandsentdate` 混用)* | DATE | P1 | Milestone NOI Date；`timeline_notice_of_intent_date`；Time Line Tab `noi_start_date` | ❌ Newrez 不单独提供（当前 BPS 以 `demandsentdate` 替代写入，属过渡处理；见下方注） |
| `demand_sent_date` | `demandsentdate` | DATE | P1 | Stage DEMAND 分组触发；`demand_start_date`（聚合页）；若 Servicer 不提供独立 `noi_date`，BPS 以本字段替代写入 `timeline_notice_of_intent_date` | ✅ 85.9%（14.1%空缺，见 doc 13 Q5） |
| `demand_expiration_date` | `demandexpirationdate` | DATE | P1 | `timeline_notice_of_intent_end_date`；`actual_notice_of_intent_days` 计算 | ✅ 85.7% |
| `fcl_setup_date` | `fcsetupdate` | DATE | P1 | `timeline_approved_for_referral_date`；Newrez 通常与 `fcreferraldate` 相同日期 | ✅ 100% |
| `first_legal_date` | `firstlegaldate` | DATE | P1 | Milestone First Legal；`timeline_first_legal_date`；Stage FIRST_LEGAL 触发 | ⚠️ 57.6% |
| `service_complete_date` | `servicecompletedate` | DATE | P1 | Milestone Service；`timeline_service_date`；Stage SERVICE 触发 | ⚠️ 28.9% |
| `publication_date` | *(无对应字段)* | DATE | P2 | Milestone Publication；`timeline_publication_date`；Stage PUBLICATION 触发 | ❌ 0%（Newrez 不提供，见 doc 13 Q1） |
| `title_received_date` | `titlereceiveddate` | DATE | P2 | `timeline_title_report_received_date` | ❌ 0%（Newrez 不提供，见 doc 13 Q8） |
| `title_clear_date` | `titlecleardate` | DATE | P2 | `timeline_preliminary_title_cleared_date` / `timeline_final_title_cleared_date` | ❌ 0%（Newrez 不提供，见 doc 13 Q8） |
| `judgement_hearing_scheduled` | `fcjudgmenthearingscheduled` | DATE | P1 | Milestone Judgement Date；**`timeline_judgement_date` / `judgement_start_date`**；Stage JUDGEMENT 触发（优先级2） | ✅ 11.9%（仅司法州） |
| `judgement_entered_date` | `fcjudgmententered` | DATE | P1 | ETL 中间表 `fcjudgment_end_date`；用于 `actual_judgement_hearing_set_days` 计算（`fcjudgmententered` − `fcjudgmenthearingscheduled`）；**非 BPS Time Line Tab 直接展示字段** | ✅ 7.9%（仅司法州） |
| `scheduled_sale_date` | `fcscheduledsaledate` | DATE | P1 | Milestone Sale；`timeline_sale_date_projected_date`；`sale_start_date`；**Stage SALE 触发（最高优先级1）** | ✅ 18.2% |
| `sale_held_date` | `fcsalehelddate` | DATE | P1 | `timeline_sale_date_held_date`；3rd Party Sale 逻辑触发 | ✅ 2.1%（完结贷款） |
| `deed_recorded_date` | `dtdeedrecorded` | DATE | P2 | `timeline_foreclosure_completed_date`（优先；COALESCE第一选项） | ✅ ~0%（完结贷款） |
| `fcl_removal_date` | `fcremovaldate` | DATE | P1 | `timeline_foreclosure_completed_date`（兜底；COALESCE第二选项） | ✅ ~2.0%（完结贷款） |
| `third_party_proceeds_date` | `fcl3rdpartyproceedsreceiveddate` | DATE | P2 | `timeline_third_party_proceeds_received_date` | ✅ ~0%（极少数完结贷款） |

**业务含义/计算逻辑**

| 标准接口字段名 | 业务含义/计算逻辑 |
|---|---|
| `noi_date` | 州法律要求发出的**正式止赎意向通知**：Judicial 州 = 法院程序前法定通知（通常 30–45 天）；Non-Judicial 州 = Notice of Default 或等效通知。与 `demand_sent_date`（催款函）概念不同——NOI 是法律层面的止赎启动声明，部分 Servicer 两者分开提供日期；Newrez 以 `demandsentdate` 混用，BPS 当前以其替代写入 `timeline_notice_of_intent_date` |
| `demand_sent_date` | 止赎前的**催款函/违约通知**（要求借款人还清欠款），可早于 NOI 也可与其合并为同一文件；触发 BPS DEMAND Stage 分组（`demand_start_date`）；Newrez 将此字段同时用作 NOI 日期（过渡处理，非标准接口设计） |
| `demand_expiration_date` | NOI/催款函到期日（到期后若未还款则可推进止赎）；计算：`actual_notice_of_intent_days = demandexpirationdate − demandsentdate` |
| `fcl_setup_date` | FCL 内部建档日（BPS 系统开案日）；Newrez 中通常与 `fcreferraldate` 为同一日期 |
| `first_legal_date` | 首次向法院提起止赎诉讼（Filing）的日期；Non-Judicial 州通常为空（无需诉诸法院）；触发 FIRST_LEGAL Stage |
| `service_complete_date` | 法律文书（传票/通知）送达借款人完成的日期；触发 SERVICE Stage |
| `publication_date` | 止赎公告在报纸/官方渠道发布的日期（Non-Judicial 州必须环节）；Newrez 不提供此字段 |
| `title_received_date` | 律师事务所收到产权调查报告的日期；Newrez 不提供此字段 |
| `title_clear_date` | 产权调查完成、确认无未知留置权的日期；分别对应初步清查和最终清查两个阶段；Newrez 不提供 |
| `judgement_hearing_scheduled` | 法院止赎判决听证会/出售确认听证会的**排定日期**（未来计划事件）；Judicial 州专用；触发 JUDGEMENT Stage（优先级 2） |
| `judgement_entered_date` | 法院**正式录入判决**的日期（已完成的法律事实）；计算：`actual_judgement_hearing_set_days = fcjudgmententered − fcjudgmenthearingscheduled`；非 Time Line Tab 直接展示字段（见 doc 13 Q10/Q12） |
| `scheduled_sale_date` | 止赎拍卖的排定日期；一旦非空即触发**最高优先级 SALE Stage**；随进程动态更新 |
| `sale_held_date` | 止赎拍卖实际举行日期；与 `fcresults` 组合判断是否为第三方购买 |
| `deed_recorded_date` | 产权过户登记日（法律意义上止赎完结）；`timeline_foreclosure_completed_date` 的 `COALESCE` 第一选项 |
| `fcl_removal_date` | FCL 流程撤销或结案日（借款人还款/LM 成功/其他原因）；`COALESCE(dtdeedrecorded, fcremovaldate)` 第二兜底选项 |
| `third_party_proceeds_date` | 第三方买家拍卖款到账日 |

> **Judgement 相关字段特别说明**（基于 ETL 代码 + MCP 数据双重验证）：
>
> | Newrez 字段 | ETL 中间表命名 | 业务含义 | BPS 去向 |
> |---|---|---|---|
> | `fcjudgmenthearingscheduled` | `fcjudgment_hearing_scheduled` | 止赎听证会/出售确认听证会的**排定日期**（未来计划事件）；BPS Stage JUDGEMENT 分类触发条件 | `judgement_start_date`（聚合页）、`timeline_judgement_date`（详情页） |
> | `fcjudgmententered` | `fcjudgment_end_date` | 法院**正式录入判决的日期**（已完成的法律事实）；两字段差约 11 天，非 ETL 延迟——两字段度量完全不同时间点 | ETL 中间表；用于 `actual_judgement_hearing_set_days` 计算 |
>
> ETL 代码确认：`fc.fcjudgment_hearing_scheduled AS timeline_judgement_date`（`basic_data_pool_config.py`）

### 2.4 Hold 槽位字段（P1 — Hold 面板历史记录）

Newrez 最多提供 3 个槽位，每槽 4 字段。BPS 每日追加变更行，积累完整 Hold 历史。

| 标准接口字段名 | Newrez 原始字段 | 类型 | 优先级 | BPS 面板/功能 | Newrez 现状 |
|---|---|---|---|---|---|
| `hold_1_description` | `fchold1description` | VARCHAR | P1 | Hold 面板 `description` | ✅ 89.6% |
| `hold_1_start_date` | `fchold1startdate` | DATE | P1 | Hold 面板 `description_start_date` | ✅（与 description 同步） |
| `hold_1_end_date` | `fchold1enddate` | DATE | P1 | Hold 面板 `description_end_date`（NULL=进行中） | ✅ |
| `hold_1_projected_end_date` | `fchold1projectedenddate` | DATE | P2 | `variance_estimated_hold_days` 计算（MAX(槽位1/2/3投影结束日) − today） | ✅ |
| `hold_2_description` | `fchold2description` | VARCHAR | P1 | 同上（槽位2） | ✅ 69.8% |
| `hold_2_start_date` | `fchold2startdate` | DATE | P1 | 同上 | ✅ |
| `hold_2_end_date` | `fchold2enddate` | DATE | P1 | 同上 | ✅ |
| `hold_2_projected_end_date` | `fchold2projectedenddate` | DATE | P2 | 同上 | ✅ |
| `hold_3_description` | `fchold3description` | VARCHAR | P1 | 同上（槽位3） | ✅ 52.6% |
| `hold_3_start_date` | `fchold3startdate` | DATE | P1 | 同上 | ✅ |
| `hold_3_end_date` | `fchold3enddate` | DATE | P1 | 同上 | ✅ |
| `hold_3_projected_end_date` | `fchold3projectedenddate` | DATE | P2 | 同上 | ✅ |
| `hold_1_modified_date` | `holdmodified` | DATE | P2 | Hold 槽位 1 最后修改日期；用于追踪 Hold 状态变化时间点 | ✅ 82.1% |
| `hold_2_modified_date` | `holdmodified2` | DATE | P2 | Hold 槽位 2 最后修改日期 | ✅ 82.1% |
| `hold_3_modified_date` | `holdmodified3` | DATE | P2 | Hold 槽位 3 最后修改日期 | ✅ 82.1% |

**业务含义/计算逻辑**

| 标准接口字段名 | 业务含义/计算逻辑 |
|---|---|
| `hold_1_description` | Hold 槽位 1 原因描述（如"Loss Mitigation Workout"/"Court Delay"）；自由文本；BPS Hold 面板 Description 列 |
| `hold_1_start_date` | Hold 1 开始日期；也是 BPS 提取层过滤条件（`fchold1startdate IS NOT NULL` 才入库） |
| `hold_1_end_date` | Hold 1 结束日期；NULL 表示该 Hold 仍在持续中 |
| `hold_1_projected_end_date` | Hold 1 预计结束日；计算：`variance_estimated_hold_days = MAX(槽1/2/3 projected) − 今日NY` |
| `hold_2_description` | Hold 槽位 2 原因描述（同一时期有多个并发 Hold 时使用） |
| `hold_2_start_date` | Hold 2 开始日期 |
| `hold_2_end_date` | Hold 2 结束日期；NULL 表示持续中 |
| `hold_2_projected_end_date` | Hold 2 预计结束日；同槽位 1 参与 MAX 计算 |
| `hold_3_description` | Hold 槽位 3 原因描述（第 3 个并发 Hold） |
| `hold_3_start_date` | Hold 3 开始日期 |
| `hold_3_end_date` | Hold 3 结束日期；NULL 表示持续中 |
| `hold_3_projected_end_date` | Hold 3 预计结束日；同槽位 1 参与 MAX 计算 |

> **架构说明**：Newrez 3个槽位是**当前快照**。BPS 每日 Sync 时检测变更并追加新行至 `sync_loan_foreclosure_hold`，积累完整 Hold 历史（如 loanid=7727000088 有 7 条历史记录，Newrez 当前槽位仅显示 1 个活跃 Hold）。

### 2.5 竞拍与成交字段（P1/P2 — Bid Approval 面板）

| 标准接口字段名 | Newrez 原始字段 | 类型 | 优先级 | BPS 面板/功能 | Newrez 现状 |
|---|---|---|---|---|---|
| `bid_amount` | `fcbidamount` | DECIMAL | P2 | Bid Approval `bid_approval_bid_amount`；FCL Summary `summary_foreclosure_bid_amount` | ✅ 9.0% |
| `approved_bid_price` | `fcapprbidprice` | DECIMAL | P2 | Bid Approval `bid_approval_bid_amount`（BPS 审批视角） | ✅ 8.9% |
| `sale_amount` | `fcsaleamount` | DECIMAL | P1 | FCL Summary `summary_foreclosure_sale_amount`；⚠️ 填充率(4.7%) > sale_held(2.1%)，疑有排序问题（见 doc 13 Q9） | ⚠️ 4.7% |

**业务含义/计算逻辑**

| 标准接口字段名 | 业务含义/计算逻辑 |
|---|---|
| `bid_amount` | Servicer 报告的止赎竞拍出价金额；拍卖临近才有值（活跃 FCL 约 9% 填充） |
| `approved_bid_price` | BPS 内部审批后的竞拍出价金额；经 BPS 竞拍审批流程确认；与 `fcbidamount` 可能存在差异 |
| `sale_amount` | 止赎拍卖实际成交金额；填充率(4.7%) > `fcsalehelddate`(2.1%)，疑为数据时序问题（金额先于拍卖日到达，见 doc 13 Q9） |

---

### 2.6 贷款属性与风险增强字段（P1/P2 — Newrez 已提供但系统未利用）

> **来源**：本节字段来自 `newrez.portnewrezfc` 和 `newrez.portnewrezgeneral`，经 MCP 实测（2026-05）确认 Newrez 已提供，但当前 ETL 和 BPS 系统未读取利用。  
> **BPS 展示**：本节字段当前无直接对应的 BPS 面板展示；纳入接口标准的目的是：(1) 为新系统 ETL 重构预留数据来源；(2) 为逐 Servicer 缺口分析提供参照基准。  
> **数据依据**：填充率基于 MCP 查询活跃 FCL 最新快照（39 笔样本）。

| 标准接口字段名 | Newrez 原始字段 | 来源表 | 类型 | 优先级 | 业务用途 | Newrez 现状 |
|---|---|---|---|---|---|---|
| `investor_loan_id` | `investorloanid` | `portnewrezfc` | VARCHAR | P1 | 投资者口径贷款编号；用于与投资者报告系统（如 Fannie Mae/Freddie Mac 报告）交叉核对；区别于系统 `loan_id` 和 Servicer `shellpointloanid` | ✅ **100%** |
| `lien_position` | `jr_sr_lien_flag`（portnewrezfc）/ `lienposition`（portnewrezgeneral） | `portnewrezfc` + `portnewrezgeneral` | INT | P1 | 留置权顺序（1=第一顺位/Senior；2=第二顺位/Junior）；**FCL 策略因此根本不同**——Junior Lien 止赎时 Senior Lien 优先受偿，须单独处理 | ✅ **100%**（双表均有）|
| `interest_paid_through_date` | `interestpaidthroughdate` | `portnewrezgeneral` | DATE | P1 | 借款人已付利息覆盖至的日期（即"paid-to date"）；计算真实逾期天数的直接依据，比 `nextduedate` 更精确，直接反映借款人实际还款行为 | ✅ **100%** |
| `in_auction_flag` | `inauctionflag` | `portnewrezgeneral` | INT | P1 | 贷款当前是否处于拍卖程序中（1=是）；低填充率但高信号强度——有值即意味着止赎即将完成，是 BPS 状态展示的关键补充 | ✅ 7.7%（有值即高价值） |
| `borrower_deceased_flag` | `borrowerdeceasedflag` | `portnewrezgeneral` | INT | P1 | 借款人是否已故（1=是）；影响止赎法律程序——须通知遗产代理人，部分州要求重新确认贷款所有权，止赎时间线受影响 | ✅ 5.1%（有值即高影响） |
| `reason_for_default` | `reasonfordefault` | `portnewrezgeneral` | VARCHAR | P2 | 贷款违约根本原因文本（如失业、收入减少、医疗支出、离婚等）；LM 方案适配与风险分类分析的重要依据 | ✅ 46.2% |
| `hold_1_comment` | `fchold1comment` | `portnewrezfc` | VARCHAR | P2 | Hold 槽位 1 备注/详细说明；补充 `hold_1_description` 字段，记录 Hold 的具体背景（如"BK case #2026-123"）| ✅ 82.1% |
| `hold_2_comment` | `fchold2comment` | `portnewrezfc` | VARCHAR | P2 | Hold 槽位 2 备注说明（同上） | ✅ 82.1% |
| `hold_3_comment` | `fchold3comment` | `portnewrezfc` | VARCHAR | P2 | Hold 槽位 3 备注说明（同上） | ✅ 82.1% |

**业务含义/计算逻辑**

| 标准接口字段名 | 业务含义/计算逻辑 |
|---|---|
| `investor_loan_id` | 投资者（如 Fannie Mae、Freddie Mac、私募基金）持有的贷款编号；与系统 `loan_id`（我方主键）和 `servicer_loan_id`（Newrez 内部号）均不同；用于投资者报告核对和转 Servicer 时的贷款追踪 |
| `lien_position` | 留置权位置：1=第一顺位（Senior Lien，优先受偿）；2=第二顺位（Junior Lien）。Junior Lien 止赎时需同时关注 Senior Lien 的 FCL 进度（`srlienmonitorflag` 等字段，当前 Newrez 样本无数据）；BPS 应区分两种止赎逻辑 |
| `interest_paid_through_date` | 借款人已还款覆盖至的日期；与 `report_date`（`dataasof`）之差即为实际逾期天数，比 `days360(nextduedate, dataasof)` 更直接；例：`interestpaidthroughdate=2025-10-01`、`dataasof=2026-05-24` → 逾期约 235 天 |
| `in_auction_flag` | 贷款是否正处于止赎拍卖流程中（即拍卖已排定或正在进行中）；高信号强度：7.7% 的活跃 FCL 有值，意味着约 7% 的贷款处于止赎最终阶段，需要高优先级处理 |
| `borrower_deceased_flag` | 借款人已故标记；已故借款人的止赎须通知遗产代理人或继承人，部分州有专项法律要求；影响 BPS 运营工作流和合规报告 |
| `reason_for_default` | 违约根本原因文本（Newrez 自由文本格式）；用于：(1) LM 方案选择（失业→Forbearance；收入永久降低→Modification）；(2) 批量风险分类；(3) 投资者报告 |
| `hold_1_comment` | Hold 槽位 1 的附加备注，补充 `hold_1_description` 的结构化描述；典型内容：破产案号、法院延期原因、LM 谈判细节 |
| `hold_2_comment` | Hold 槽位 2 备注（同上） |
| `hold_3_comment` | Hold 槽位 3 备注（同上） |

> **零填充字段（Newrez 当前样本未提供）**：以下字段在 Newrez 数据中当前填充率为 0%，暂不纳入正式字段表，作为未来扩展预留：
> - **Senior/Junior Lien 跟踪**：`srlienmonitorflag`、`srliensalescheduleddate`、`srliensalehelddate`（当 Newrez 为 Junior Lien 时，Senior Lien 的止赎进度至关重要）
> - **SCRA 军人保护**：`loanscraflag`、`loanscrastartdate`、`loanscraenddate`（SCRA 生效时止赎必须暂停；现役军人贷款须特殊处理）
> - **FEMA 灾区**：`femaarea`、`femaaffect`（灾区贷款受止赎暂停令保护）
> - **产权委托**：`titleordereddate`（产权报告委托日，早于 `titlereceiveddate`）

---

## Section 3：LM 数据字段规范（来源：`portnewrezlm`）

### 3.1 LM 周期字段（P1 — Loss Mitigation Cycle 面板）

每个 LM 周期独立一行（`lmdeal` + `dealstartdate` 唯一标识）。BPS 一对多存储，历史不覆盖。

| 标准接口字段名 | Newrez 原始字段 | 类型 | 优先级 | 格式/ETL 要求 | BPS 面板/功能 | Newrez 现状 |
|---|---|---|---|---|---|---|
| `lm_deal` | `lmdeal` | INT→VARCHAR | P1 | **必须附解码映射表**（int码 → 业务文本，如 `7`→`"DIL"`） | LM Cycle `deal` | ✅ 已提供 |
| `lm_program` | `lmprogram` | INT→VARCHAR | P1 | **必须附解码映射表** | LM Cycle `program` | ✅ 已提供 |
| `lm_status` | `lmstatus` | INT→VARCHAR | P1 | **必须附解码映射表** | LM Cycle `lmc_status` | ✅ 已提供 |
| `lm_cycle_open_date` | `dealstartdate` | DATE | P1 | YYYY-MM-DD；LM 周期开始日 | LM Cycle `cycle_opened_date` | ✅ 已提供 |
| `lm_cycle_close_date` | `lmremovaldate` | DATE | P1 | YYYY-MM-DD；NULL=进行中 | LM Cycle `cycle_closed_date` | ✅ 已提供 |
| `lm_final_disposition` | `lmdecision` | INT→VARCHAR | P1 | **必须附解码映射表** | LM Cycle `final_disposition` | ✅ 已提供 |
| `lm_denial_reason` | `denialreason` | INT→VARCHAR | P1 | **必须附解码映射表**；无拒绝时空字符串 | LM Cycle `denialreason` | ✅ 已提供 |
| `borrower_intentions` | `borrowerintention` | INT→VARCHAR | P2 | 解码映射表（若提供） | LM Cycle `borrower_intentions` | ❌ 0%（Newrez 不提供，见 doc 13 Q6） |
| `imminent_default` | *(无)* | VARCHAR | P2 | CFPB Reg X 触发条件 | LM Cycle `imminent_default` | ❌ 0%（Newrez 不提供，见 doc 13 Q6） |
| `single_point_of_contact` | *(无)* | VARCHAR | P2 | CFPB Reg X 12 CFR 1024.40 | LM Cycle `single_point_of_contact` | ❌ 0%（Newrez 不提供，见 doc 13 Q6） |

**业务含义/计算逻辑**

| 标准接口字段名 | 业务含义/计算逻辑 |
|---|---|
| `lm_deal` | LM 策略大类（整型编码）；ETL 解码为文本：Evaluation / Modification / Short Sale / DIL 等；反映本轮救济的整体方向 |
| `lm_program` | LM 具体执行方案（整型编码）；Deal 大类下的子方案；如 Bridger mod / 496.0 / Deed-in-Lieu |
| `lm_status` | 本 LM 周期当前工作进展状态（整型编码）；如 Pending Financials / Workout Denial / DIL Title Ordered |
| `lm_cycle_open_date` | 本轮 LM 周期开始日（Servicer 正式开立此次 workout 的日期）；与 `lm_deal` 共同构成周期唯一标识 |
| `lm_cycle_close_date` | 本轮 LM 周期结束日；NULL=仍在进行中；结合 open_date 可计算周期历时 |
| `lm_final_disposition` | LM 周期最终处置结论（整型编码）；决定 FCL 走向：`Referral to FC` / `Request Incomplete` → FCL 继续；`Approved` → FCL 暂停 |
| `lm_denial_reason` | LM 方案被拒时的具体原因（整型编码）；无拒绝时为空字符串 |
| `borrower_intentions` | 借款人明确声明的处置意向（整型编码）；如保留房产 / 短售 / 以房抵债；CFPB Reg X 相关；Newrez 不提供 |
| `imminent_default` | CFPB Reg X 要求的即将违约标识；标记尚未拖欠但面临可预见还款困难的借款人；触发 LM 提前介入评估义务；Newrez 不提供 |
| `single_point_of_contact` | CFPB Reg X 12 CFR 1024.40 要求的专属服务联系人姓名；处于 LM 流程的借款人须有唯一对接人；Newrez 不提供 |

### 3.2 ETL 解码要求（LM 字段特殊说明）

Newrez `portnewrezlm` 中的 `lmdeal`、`lmprogram`、`lmstatus`、`lmdecision`、`denialreason` 均以**数字编码**存储（int 类型）。BPS 的 `sync_loan_foreclosure_loss_mitigation` 表存储**解码后文本**，不存储数字码。

**Servicer 交付要求**：
1. 每次数据提交时，必须同步提供字段解码映射表（int 码 → 业务文本）
2. 若解码映射发生变更，需重新同步历史数据
3. BPS 不接受仅提交数字码的 LM 记录（无法在面板正确展示）

---

## Section 4：破产数据字段规范（来源：`portnewrezbk`）

### 4.1 BK 字段（P1/P2 — Bankruptcy 面板）

BK 数据与 FCL 数据独立，每条贷款的破产记录在 BPS 中以独立行存储（若无破产记录，Bankruptcy 面板显示"No Rows To Show"）。

| 标准接口字段名 | Newrez 原始字段 | 类型 | 优先级 | BPS 面板/功能 | Newrez 现状 |
|---|---|---|---|---|---|
| `active_bk_flag` | `activebkflag` | TINYINT | P1 | `variance_active_bankruptcy`（FCL Summary 破产状态指示） | ✅ 已提供 |
| `bk_status` | `bkstatus` | INT/VARCHAR | P1 | BK 面板 Status 列（编码解码行为待确认，见 doc 13 Q7） | ⚠️ 编码确认中 |
| `bk_legal_status` | `bkstage` | INT/VARCHAR | P1 | BK 面板 Legal Status 列（同上） | ⚠️ 编码确认中 |
| `bk_status_date` | `bkrcurrentstatusdate` | DATE | P1 | BK 面板 Status Date | ✅ 已提供 |
| `bk_chapter` | `bkchapter` | VARCHAR/INT | P1 | BK 面板 Chapter（7/11/13） | ✅ 已提供 |
| `bk_filed_date` | `bkfileddate` | DATE | P1 | BK 历史追溯；`bkfileddate` | ✅ 已提供 |
| `bk_removal_date` | `bkremovaldate` | DATE | P1 | `variance_completed_bankruptcy` 计算（activebkflag=0 AND bkremovaldate IS NOT NULL） | ✅ 已提供 |
| `mfr_filed_date` | `mfrfileddate` | DATE | P1 | BK 面板 MFR Filed Date | ✅ 已提供 |
| `mfr_hearing_results` | `mfrhearingresults` | INT | P1 | BK 面板 MFR Status（数字编码，见 Q7） | ⚠️ 编码确认中 |
| `proof_of_claim_date` | `pocfileddate` | DATE | P1 | BK 面板 Proof of Claim Date | ✅ 已提供 |
| `post_petition_due_date` | `bkpostpetitionduedate` | DATE | P1 | BK 面板 Post Petition Due Date | ✅ 已提供 |

**业务含义/计算逻辑**

| 标准接口字段名 | 业务含义/计算逻辑 |
|---|---|
| `active_bk_flag` | 贷款当前是否处于活跃破产保护（Automatic Stay）中；1=进行中；Automatic Stay 期间止赎程序必须法律暂停 |
| `bk_status` | 破产案件当前状态（整型编码，解码表待确认）；反映破产程序进展节点 |
| `bk_legal_status` | 破产法律程序阶段（整型编码）；与 bk_status 为不同维度的分类 |
| `bk_status_date` | 当前破产状态生效日期 |
| `bk_chapter` | 破产申请所依据的破产法章节；常见：Chapter 7（清算）/ Chapter 13（偿还计划）/ Chapter 11（重组）；影响止赎恢复策略 |
| `bk_filed_date` | 破产申请向法院提交的日期；BPS 去重 KEY（同 loanid + bkfileddate 唯一确定一次破产申请） |
| `bk_removal_date` | 破产程序终止日；`variance_completed_bankruptcy` 计算：`activebkflag=0 AND bkremovaldate IS NOT NULL` |
| `mfr_filed_date` | Lender 向破产法院申请解除 Automatic Stay 的动议（MFR）提交日；MFR 获批后止赎可恢复推进 |
| `mfr_hearing_results` | MFR 听证会结果（整型编码，解码表待确认）；批准则止赎流程可恢复 |
| `proof_of_claim_date` | Lender 在破产程序中正式向法院登记债权金额（Proof of Claim）的提交日；破产程序合规要求 |
| `post_petition_due_date` | 破产申请后的贷款月供应付日；用于追踪 Automatic Stay 期间借款人是否持续还款 |

---

## Section 5：Servicer 合规现状矩阵

### 5.1 Newrez 当前合规状态汇总（基于 doc 13 MCP 实测，2026-05）

| 字段组 | Section | 总字段数 | ✅ 已提供 | ⚠️ 部分提供 | ❌ 未提供 | 合规率 |
|---|---|---|---|---|---|---|
| **四维状态基础标志** | **2.0** | **12** | **1** | **5** | **6** | **~8%** |
| 识别/入库字段 | 2.1 | 7 | 7 | 0 | 0 | **100%** |
| FCL 状态字段 | 2.2 | 9 | 7 | 2 | 0 | **88%** |
| FCL 时间线字段 | 2.3 | 16 | 9 | 2 | 4 | **~56%** |
| Hold 槽位字段 | 2.4 | 12 | 12 | 0 | 0 | **100%** |
| Bid/Sale 字段 | 2.5 | 3 | 2 | 1 | 0 | **83%** |
| 贷款属性增强字段 | 2.6 + 2.4补充 | 12 | 9 | 0 | 0 | **~75%** |
| LM 周期字段 | 3.1 | 10 | 7 | 0 | 3 | **70%** |
| BK 字段 | 4.1 | 11 | 8 | 3 | 0 | **91%** |
| **合计** | — | **92** | **62** | **13** | **13** | **~67%** |

### 5.2 Newrez 未提供字段清单（正式补全请求依据）

以下 6 个字段当前 Newrez **完全未提供**（0%），BPS 对应面板功能受影响：

| 字段名 | Newrez 未提供的原始字段 | 业务影响 | 优先级 | 受影响的 BPS 面板 |
|---|---|---|---|---|
| `noi_date` | *(无；Newrez 以 `demandsentdate` 混用)* | BPS `timeline_notice_of_intent_date` 及 Time Line Tab `noi_start_date` 当前以 `demandsentdate` 替代；正式 NOI 日期与催款函日期无法区分 | P1 | Milestone Notice of Intent Date；Time Line Tab NOI Date 1 |
| `publication_date` | *(无对应字段)* | BPS PUBLICATION 阶段始终为空；Stage 分类该层永远不触发 | P2 | Timeline Publication Date 5；Stage PUBLICATION 组 |
| `title_received_date` | `titlereceiveddate`（字段存在但全空） | 产权收到日始终为空 | P2 | Timeline `timeline_title_report_received_date` |
| `title_clear_date` | `titlecleardate`（字段存在但全空） | 产权清洁日始终为空（初步和最终两个字段均受影响） | P2 | Timeline preliminary/final title cleared |
| `borrower_intentions` | `borrowerintention`（字段存在但全空） | LM 面板借款人意向列始终为空 | P2 | LM Cycle Borrower Intentions |
| `imminent_default` | *(无对应字段)* | CFPB Reg X 紧迫违约指标始终为空 | P2 | LM Cycle Imminent Default |
| `single_point_of_contact` | *(无对应字段)* | CFPB Reg X 12 CFR 1024.40 单一联系人始终为空 | P2 | LM Cycle Single Point of Contact |

### 5.3 Newrez 部分提供字段关注点

以下字段 Newrez 已提供但存在质量问题，需关注：

| 字段 | 问题描述 | 填充率 | 优先级 |
|---|---|---|---|
| `currentmilestone` | 填充率仅 62.7%，BPS `summary_current_step` 需降级到 `fcstage` | 62.7% | P1 ⚠️ |
| `fcsaleamount` | 填充率(4.7%) > `fcsalehelddate`(2.1%)，疑有数据时序问题（金额先于 held date 到达） | 4.7% | P1 ⚠️ |
| `firstlegaldate` | 填充率 57.6%，部分非司法州贷款可能无此日期（合理） | 57.6% | P1 ⚠️ |
| `servicecompletedate` | 填充率 28.9%，仅完成 Service 阶段的贷款有值（合理） | 28.9% | P1 |

---

## Section 6：交付格式规范

### 6.1 基本交付规格

| 规格项 | 要求 | BPS 特有说明 |
|---|---|---|
| 交付频率 | **日报**（推荐）；月报仅适用于小型贷款组合 | 月报导致 FCL Stage 天数误差最大 30 天；日报可最小化数据延迟 |
| 文件格式 | CSV（UTF-8 无 BOM）或 Fixed-width TXT | 禁止 xlsx（Excel 文件）；避免 BOM 导致字段解析错误 |
| 日期格式 | **`YYYY-MM-DD`** 为唯一标准 | BPS 日期字段不容错处理非标格式（如 MM/DD/YYYY）；非标格式将导致字段解析失败 |
| NULL 值处理 | 空字符串 `''` 或 `NULL` 均可 | **禁止**：`N/A`、`NA`、`0001-01-01`（系统将误识别为有效值） |
| 文件命名 | `{servicer}_{report_type}_{YYYYMMDD}.csv` | 示例：`newrez_fcl_main_20260527.csv`、`newrez_lm_20260527.csv` |

### 6.2 数据模型结构

| 文件/批次 | 内容 | 每贷款行数 |
|---|---|---|
| FCL 主文件 | Section 2.1–2.3（识别/状态/时间线字段）+ 2.4（Hold 槽位）+ 2.5（Bid/Sale） | 1 行/贷款（快照） |
| LM 文件 | Section 3.1 LM 周期字段 | **多行/贷款**（每 LM 周期独立一行；历史不覆盖） |
| BK 文件 | Section 4.1 BK 字段 | 多行/贷款（每次破产独立记录） |
| **解码映射表**（必须） | LM 字段（deal/program/status/disposition）的 int→文本映射 | 独立文件 |

### 6.3 编码字段解码映射要求

**涉及字段**：`lmdeal`、`lmprogram`、`lmstatus`、`lmdecision`、`denialreason`（LM），以及 `bkstatus`、`bkstage`、`mfrhearingresults`（BK，待确认）

**要求**：
1. 首次提交时必须同时提交解码映射表
2. 每次解码映射变更需提前通知，BPS 侧需重新同步历史数据
3. 映射表格式示例：

```
field_name,code,text_label
lmdeal,7,DIL
lmdeal,1,Evaluation
lmprogram,10,Deed-in-Lieu
...
```

### 6.4 Hold 槽位交付特别说明

- Newrez 当前提供 3 个固定槽位（`fchold1/2/3`）；若单笔贷款超过 3 个活跃 Hold，需按时间顺序轮转（最早的 Hold 结束后新 Hold 才可进入槽位）
- BPS 侧每日追加变更行，槽位内容变化即生成新行（积累完整历史）
- Servicer 需提供每日完整快照（包含所有当前活跃 Hold），而非仅变更部分

---

## Section 7：字段补全请求优先级汇总

本节汇总向 Servicer 发出正式字段补全请求的优先级顺序。

### 7.1 P0 字段（缺失 = 拒绝入库，必须立即修复）

以下 7 个字段任何一个缺失，BPS 将无法处理该贷款：

| 字段 | Newrez 原始字段 | Newrez 现状 |
|---|---|---|
| `loan_id` | `loanid` | ✅ 100%（Newrez 合规） |
| `servicer_loan_id` | `shellpointloanid` | ✅ 100% |
| `data_as_of_date` | `dataasof` | ✅ 100% |
| `state` | `state` | ✅ 100% |
| `judicial_flag` | `judicial` | ✅ 100% |
| `active_fcl_flag` | `activefcflag` | ✅ 100%（历史 NULL 需 NULL-safe 处理） |
| `fcl_referral_date` | `fcreferraldate` | ✅ 100% |

> Newrez 当前所有 P0 字段均合规。**新 Servicer 接入时需优先验证这 7 个字段**。

### 7.2 P1 字段 — 当前 Newrez 存在问题（需关注）

| 字段 | 问题 | 优先级 |
|---|---|---|
| `currentmilestone` | 填充率 62.7%（偏低） | P1 ⚠️ 建议补全至 90%+ |
| `fcsaleamount` | 4.7% vs `fcsalehelddate` 2.1%（数据时序异常，见 Q9） | P1 ⚠️ 建议核查 |
| `firstlegaldate` | 57.6%（部分合理，但需区分"未到阶段"与"漏报"） | P1 |
| `servicecompletedate` | 28.9%（部分合理，仍在 Service 前阶段贷款为空） | P1 |

### 7.3 P2 字段 — Newrez 未提供（建议正式补全请求）

| 字段 | 影响的 BPS 功能 | 向 Servicer 请求理由 |
|---|---|---|
| `publication_date` | BPS PUBLICATION 阶段始终空 | 完整时间线；Stage 分类完整性 |
| `titlereceiveddate` | 产权收到日始终空 | Timeline 完整性 |
| `titlecleardate` | 产权清洁日始终空 | Timeline 完整性 |
| `borrowerintention` | LM 借款人意向列始终空 | LM 面板完整性 |
| `imminent_default` | CFPB Reg X 指标空 | 合规指标完整性 |
| `single_point_of_contact` | CFPB Reg X 12 CFR 1024.40 指标空 | 合规指标完整性 |

---

## 附录 A：BPS 面板 → Servicer 字段逆向快查索引

> 用途：从"BPS 展示内容"快速查到"必须提供的 Servicer 字段"。适用于 BPS 面板排查、新 Servicer 对接时按面板逐一核查字段。

| BPS 面板 | UI 关键列/功能 | 必须的 Servicer 字段 | 优先级 |
|---|---|---|---|
| **FCL Milestone 时间线** | NOI Date | `demandsentdate` | P1 |
| | Referral Date | `fcreferraldate` | P0 |
| | First Legal Date | `firstlegaldate` | P1 |
| | Service Date | `servicecompletedate` | P1 |
| | Publication Date | *(Newrez 未提供)* | P2 ❌ |
| | Judgement Date | `fcjudgmenthearingscheduled` | P1 |
| | Sale Date | `fcscheduledsaledate` | P1 |
| | Foreclosure Completed | `dtdeedrecorded` / `fcremovaldate` | P1/P2 |
| **FCL Summary 面板** | Current Step | `currentmilestone`（优先）/ `fcstage`（兜底） | P1 |
| | Attorney | `fcfirm` | P1 |
| | SMS Days / Days in FCL | `smsdaysinfc` + `dataasof` / `daysinfc` + `dataasof` | P1 |
| | Sale Amount | `fcsaleamount` | P1 |
| **Hold 面板** | Description / Start / End | `fchold{1/2/3}description` / `startdate` / `enddate` | P1 |
| | Estimated Hold Days | `fchold{1/2/3}projectedenddate` | P2 |
| **LM Cycle 面板** | Deal / Program / Status | `lmdeal`+解码 / `lmprogram`+解码 / `lmstatus`+解码 | P1 |
| | Cycle Opened/Closed | `dealstartdate` / `lmremovaldate` | P1 |
| | Final Disposition | `lmdecision`+解码 | P1 |
| | Borrower Intentions | `borrowerintention`+解码 | P2 ❌（Newrez未提供） |
| | Imminent Default | *(Newrez 未提供)* | P2 ❌ |
| **Bankruptcy 面板** | Chapter / Status / MFR | `bkchapter` / `bkstatus` / `mfrhearingresults` | P1 |
| | MFR Filed / POC Date | `mfrfileddate` / `pocfileddate` | P1 |
| | Post Petition Due Date | `bkpostpetitionduedate` | P1 |
| **Aggregate Stage Tab** | Stage 分组 | `fcreferraldate`+`firstlegaldate`+`servicecompletedate`+`fcjudgmenthearingscheduled`+`fcscheduledsaledate` | P0/P1 |
| | Days in Stage | ETL 从上述日期计算（BPS 侧） | N/A |
| **Aggregate Time Line Tab** | NOI Date 1 | `demandsentdate`（→ `demand_start_date`，非 `noi_start_date`） ⚠️ | P1 |
| | Referral Date 2 | `fcreferraldate` → `referral_start_date` | P0 |
| | First Legal Date 3 | `firstlegaldate` → `first_legal_start_date` | P1 |
| | Service Date 4 | `servicecompletedate` → `service_start_date` | P1 |
| | Publication Date 5 | *(Newrez 未提供)* → `publication_start_date` 恒NULL | P2 ❌ |
| | Judgement Date 6 | `fcjudgmenthearingscheduled` → `judgement_start_date` | P1 |
| | Sale Date 7 | `fcscheduledsaledate` → `sale_start_date` | P1 |

> **Time Line Tab NOI Date 1 特别注意**：Newrez `demandsentdate` 映射到 BPS `demand_start_date`，不映射到 `noi_start_date`；因此 Time Line Tab 的"NOI Date 1"列对 Newrez 贷款**始终为空**。若需查询 Demand Letter 日期，应查 `demand_start_date`（Stage Tab 天数计算使用此字段）。

---

## 附录 B：ETL 中间表字段用途分类 — BPS已使用 vs 未来追踪预留

> **数据来源**：`port.basic_data_loan_fcl`（Redshift ETL 中间表，跨 Servicer UNION，约 37 个业务字段 + Hold 槽位）  
> **来源代码**：`basic_data_pool_config.py`（FCL UNION 查询，第 1490–1600 行）  
> **图例**：
> - ✅ **BPS已使用**：字段流向 BPS MySQL（`bpms.basic_data_loan_foreclosure` 或 `bpms.sync_*` 表），驱动 BPS UI 展示
> - 🔮 **ETL预留/未进BPS**：字段已归一化存储于中间表，当前未被任何下游 BPS ETL 消费；Servicer 提供后可用于未来贷款状态追踪分析

| 中间表字段 | 图例 | 对应 BPS 字段（已使用时）/ 未来用途（预留时） |
|---|---|---|
| `dataasof` | ✅ | `fctrdt`（数据截止日，所有 BPS FCL 表） |
| `loanid` | ✅ | `loanid`（全部 BPS FCL 表主键） |
| `servicer` | ✅ | Servicer 标识符 |
| `svc_loanid` | ✅ | `svcloanid` |
| `activefcflag` | ✅ | `summary_foreclosure_status` 推导依据 |
| `titleordereddate` | 🔮 | 未来：产权追踪链条完整性分析（链条起点） |
| `titlereceiveddate` | ✅ | `timeline_title_report_received_date` |
| `titlecleardate` | ✅ | `timeline_preliminary_title_cleared_date` / `timeline_final_title_cleared_date` |
| `noi_date` | ✅ | `timeline_notice_of_intent_date` |
| `fcsetupdate` | ✅ | `timeline_approved_for_referral_date` |
| `referral_start_date` | ✅ | `timeline_referred_to_foreclosure_date` |
| `svc_days_infc` | ✅ | `summary_sms_days_in_fcl`（实时重算） |
| `daysinfc` | ✅ | `summary_days_in_fcl`（实时重算） |
| `demandsentdate` | ✅ | `timeline_notice_of_intent_date` + `demand_start_date` |
| `demandexpirationdate` | ✅ | `timeline_notice_of_intent_end_date` |
| `legal_start_date` | ✅ | `timeline_first_legal_date` |
| `service_start_date` | ✅ | `timeline_service_date` |
| `fcjudgment_hearing_scheduled` | ✅ | `timeline_judgement_date` / `judgement_start_date`（Stage Tab） |
| `fcjudgment_end_date` | 🔮 | 未来：`actual_judgement_hearing_set_days` = `fcjudgment_end_date` − `fcjudgment_hearing_scheduled`（见 doc 13 Q12） |
| `fcscheduled_sale_date` | ✅ | `timeline_sale_date_projected_date` / `sale_start_date` |
| `fcsale_held_date` | ✅ | `timeline_sale_date_held_date` |
| `fcbidamount` | ✅ | `bid_approval_bid_amount` |
| `fcapprbidprice` | ✅ | `bid_approval_bid_amount`（合并展示） |
| `fcsaleamount` | ✅ | `summary_foreclosure_sale_amount` |
| `fcl3rdpartyproceedsreceiveddate` | ✅ | `timeline_third_party_proceeds_received_date` |
| `fcresults` | ✅ | `summary_completed_foreclosure` 推导依据 |
| `fcstage` | ✅ | `summary_current_step`（次优先） |
| `lastfcstepcompleted` | ✅ | `summary_last_step_completed` |
| `lastfcstepcompleteddate` | ✅ | `summary_last_step_completed_date` |
| `fcremovaldesc` | ✅ | `summary_foreclosure_status` 推导依据 |
| `fcremovaldate` | ✅ | `timeline_foreclosure_completed_date` |
| `judicial` | ✅ | `summary_judicial_foreclosure` / `summary_type` |
| `fcfirm` | ✅ | `summary_foreclosure_attorney` / `summary_firm` |
| `fccontestedflag` | ✅ | `summary_contested_litigation` |
| `jr_sr_lien_flag` | 🔮 | 未来：留置权风险分析（次级留置权复杂度评估） |
| `dtdeedrecorded` | ✅ | `timeline_foreclosure_completed_date`（优先） |
| `activejnrlienfcflag` | 🔮 | 未来：活跃次级留置权 FCL 状态追踪 |
| **Hold 槽位（JOIN）**：`hold_{n}_description` / `start_date` / `end_date` / `projected_end_date` | ✅ | `bpms.sync_loan_foreclosure_hold`（Hold 历史全量表） |

> **Servicer 须知**：
> - **✅ 字段**：必须提供——缺失会导致 BPS 对应面板数据异常（P0/P1 字段）或分析功能不可用（P2 字段）；具体优先级见 Section 2–4
> - **🔮 字段**：可选提供——当前不影响 BPS 展示；若提供，我方 ETL 已可直接归一化存储，为未来贷款状态追踪功能做好数据准备

---

*文档完 — doc 14 v3 (2026-05-28)*
