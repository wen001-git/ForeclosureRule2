# doc 10 — ForeclosureRule2 综合术语清单

---

## 文档目的

- **为什么存在**：项目各文档（doc 01–09）中散落着大量业务术语、ETL 架构词汇、MBA 标准编码和 Servicer 专用缩写，缺乏统一的查询入口。
- **解决的问题**：新成员、审查者或 AI 会话在阅读任何文档时遇到不熟悉的术语，可直接查本文档，无需翻阅多个文档。
- **覆盖范围**：核心业务状态 · 逾期状态编码 · FCL 流程 · LM 类型 · 破产相关 · ETL 架构 · 系统缩写 · 监管/合规，共 8 大分类，55+ 条目。
- **不覆盖**：字段级数据字典（见 `docs/foreclosure_data_dictionary.md`）；Servicer 原始表结构（见 `docs/zh/01_source_data.md`）。
- **系统归属**：ForeclosureRule2 项目，PrefectFlow（Prefect 2.x 抵押贷款服务 ETL 系统）。

## 目标读者

主要读者：新成员（任何角色）· 业务分析师 · 数据工程师 · 验证人员 · 未来 AI 会话  
次要读者：合规审查 · 系统重构架构师 · Servicer 对接人员

## 修订历史

| 日期 | 作者 | 版本 | 变更内容 | 关联文档 |
|------|------|------|---------|---------|
| 2026-05-25 | AI Agent (Claude Sonnet 4.6) | v1 | 初始版本，综合 doc 00–09 及 foreclosure_data_dictionary.md 的术语 | doc 00–09 |
| 2026-05-26 | AI Agent（Claude Sonnet 4.6） | v2 | 新增 9 条缺失术语：NOI/Demand Letter（分类 C）、3rd Party Sale（分类 C）、Target/Actual/Var Days 三层框架（分类 C）、MFR 完整定义（分类 E）、POC（分类 E）、dataasof 和 SMS/Shellpoint（分类 G）；原 MFR 一行缩写词条更新为指向分类 E 的完整定义 | doc 13 v4 |
| 2026-06-02 | AI Agent (Claude Opus 4.8) | v3 | 新增「分类 H — 监管/合规术语」6 条（CFPB、RESPA、Reg X、12 CFR 1024.40/SPOC、12 CFR 1024.41、Imminent Default）；分类 G 增 CFPB/RESPA/SPOC 交叉指引行；覆盖范围更新为 8 大分类 | doc 14 |
| 2026-06-03 | AI Agent (Claude Opus 4.8) | v4 | 分类 C 新增词条 `dtdeedrecorded`（止赎契据登记日=产权过户/止赎完成点，约在 fcsalehelddate 后 2-3 周、多数→REO；BPS 用作 timeline_foreclosure_completed_date 首选、近似 REO 取得日）；同步略扩 doc 14 reo_acquisition_date 验证SQL 注释 | doc 14 · doc 13 §3.1 |

## 依赖文档

| 文档 | 关系 |
|------|------|
| `docs/zh/00_index.md` | 项目导航，包含 11 条基础速查术语 |
| `docs/zh/08_servicer_fcl_field_mapping.md` | MBA 标准、FCL 流程、LM 类型的详细背景 |
| `docs/zh/09_servicer_data_interface_standard.md` | 字段命名规范、四维状态模型 |
| `docs/foreclosure_data_dictionary.md` | 字段级数据字典，字段语义说明 |

---

## 分类 A — 核心业务状态

> 这四个维度相互正交，同一笔贷款可同时处于多个状态（如 FCL + BK + LM 并存）。

---

**FCL**（Foreclosure，止赎）

贷款方因借款人违约，依据抵押合同，通过法律程序强制出售抵押房产以回收贷款余额的过程。FCL 是法律状态，不是逾期程度——D120P（逾期 120 天以上）不等于 FCL，FCL 必须由 Servicer 明确标记。系统内部码：`FCL`。  
**相关**：Judicial Foreclosure / Non-Judicial Foreclosure（流程类型）；REO（结果之一）；fcl_flag（数据字段）

---

**REO**（Real Estate Owned，银行持有房产）

止赎程序完成后，房产无人出价购买，房产所有权从借款人转至贷款方（银行/基金）持有。是 FCL 的终点结果之一。系统内部码：`REO`。  
**相关**：FCL（前置状态）；3rd Party Sale（另一种 FCL 结束方式）；reo_flag（数据字段）

---

**BK**（Bankruptcy，破产）

借款人依据美国破产法向法院申请破产保护。申请后立即触发**自动中止令（Automatic Stay）**，强制暂停所有催收行动（包括正在进行的 FCL）。最常见类型：Chapter 7（清算型）和 Chapter 13（重组型）。  
**注意**：MBA `delinquency_status` 中的 `Bankruptcy` 枚举值与 `Foreclosure` **互斥**，因此需要独立 `bankruptcy_flag` 字段来捕获 FCL+BK 并存状态。  
**相关**：Automatic Stay；FCL-Hold；Chapter 7 / 13；bankruptcy_flag（数据字段）

---

**LM**（Loss Mitigation，损失缓解）

贷款方为避免止赎损失、与逾期借款人协商的各类缓解方案的总称。包括宽限（Forbearance）、贷款修改（Modification）、还款计划（Repayment Plan）等。LM 是独立维度，可与 FCL 并存（FCL 已启动但同时在谈 LM）。  
**相关**：FCL-Hold（LM 导致 FCL 暂停）；lm_flag / lm_type（数据字段）；分类 D（LM 六种类型）

---

**Delinquency**（逾期状态）

借款人未按时还款的状态，按逾期天数（Days Past Due, DPD）分级。系统使用 8 个内部状态码（见分类 B）。逾期是事实描述，FCL 是法律状态，两者不等同。  
**相关**：DPD；MBA 标准（原始取值）；days360（兜底计算方法）

---

## 分类 B — 逾期状态编码

### 系统内部状态码（ETL 输出层）

| 内部码 | 含义 | DPD 范围 |
|--------|------|---------|
| `C` | Current（正常还款） | DPD < 30 天 |
| `D30` | 30–59 天逾期 | 30–59 天 |
| `D60` | 60–89 天逾期 | 60–89 天 |
| `D90` | 90–119 天逾期 | 90–119 天 |
| `D120P` | 120 天以上逾期 | ≥ 120 天 |
| `FCL` | Foreclosure（止赎程序中） | 由 Servicer 标记，非 DPD 计算 |
| `REO` | Real Estate Owned（银行持有房产） | FCL 完成后 |
| `P` | Paid in Full（全额还清/贷款终止） | 还清、Short Sale、REO 处置等 |

> 系统内部码由 ETL Step 3（`daily_data_loan_common_clean_config.py`）从 Servicer 原始数据映射而来，存储于 L3 Clean 层及 portmonthbase。

---

### MBA 标准原始取值范围（Servicer 传输层）

> 以下为 Servicer 向系统传输的原始文本值（以 Newrez 为代表，DB 实测 2026-05-25），经 Step 3 映射为系统内部码。

| Servicer 原始传输值 | 含义 | 映射到系统内部码 |
|--------------------|------|--------------|
| `Current` | 0–29 DPD，正常还款 | → `C` |
| `1-29 DPD` | 1–29 天逾期（Newrez 细分） | → `C` |
| `30-59 DPD` | 30–59 天逾期 | → `D30` |
| `60-89 DPD` | 60–89 天逾期 | → `D60` |
| `90-119 DPD` | 90–119 天逾期 | → `D90` |
| `120-149 DPD` | 120–149 天逾期 | → `D120P` |
| `150-179 DPD` | 150–179 天逾期 | → `D120P` |
| `180+ DPD` | 180 天以上逾期 | → `D120P` |
| `Foreclosure` | 止赎程序中 | → `FCL` |
| `Foreclosure / Non-Perf BK` | 止赎 + 非履约破产（Newrez 复合值） | → `FCL`（同时 `bankruptcy='Y'`） |
| `Foreclosure / Perf BK` | 止赎 + 履约破产（Newrez 复合值） | → `FCL`（同时 `bankruptcy='Y'`） |
| `Performing Bankruptcy` | 履约破产（仍在还款） | → `D90`/`D120P`（同时 `bankruptcy='Y'`） |
| `Non-Performing Bankruptcy` | 非履约破产 | → `D120P`（同时 `bankruptcy='Y'`） |
| `REO` | 银行持有房产 | → `REO` |
| `REO Sale` | REO 已出售（处置完成） | → `P` |
| `Full Payoff` / `Paid in Full` | 全额还清 | → `P` |
| `3rd Party Sale` | 第三方拍卖出售（FCL 拍卖成功） | → `P` |
| `Service Release` | 贷款服务权转让 | → 特殊处理 |

> **注意**：`CapeCodFive` 当前传输数字 DPD（`'29.0'`、`'30.0'`），不是 MBA 文本枚举，导致系统映射失败。这是 P0 问题。见 doc 08。

---

## 分类 C — FCL 流程术语

**Judicial Foreclosure**（司法止赎）

需经法院批准的止赎程序。典型州：纽约、新泽西、佛罗里达。流程周期 6 个月–2 年。法院参与提高了借款人的救济渠道，但也延长了止赎时间线。

---

**Non-Judicial Foreclosure**（非司法止赎 / Power of Sale）

无需法院，贷款方依据合同中的"授权出售条款"直接启动拍卖。典型州：加利福尼亚、德克萨斯。流程周期 3–6 个月。速度更快，是美国多数州的主要形式。

---

**Referral**（移交律师）

止赎程序的第一个阶段：贷款方将案件正式移交止赎律师，授权其启动法律程序。`referral_date` 是 FCL 时间线的起点。

---

**NOI / Demand Letter**（止赎意向通知函）

止赎正式启动**之前**，贷款方向借款人发出的法律通知函，要求其在规定期限内（通常 30 天）还清欠款或安排还款，否则将启动止赎程序。NOI 是 FCL 的前置步骤，**不等于** FCL 已经启动。

- **Judicial 州**（纽约、新泽西、佛罗里达等）：通常称为 **Notice of Intent**（NOI）或 **Notice of Default**（NOD）
- **Non-Judicial 州**（加利福尼亚、德克萨斯等）：通常称为 **Demand Letter**

Newrez 系统以 `demandsentdate`（"Demand 发出日"）命名此字段，因此在 BPS doc 13 中以"NOI / Demand"统称两者，避免与州法差异混淆。  
**相关 BPS 字段**：`timeline_notice_of_intent_date`（发出日，来自 `demandsentdate`）、`timeline_notice_of_intent_end_date`（到期日，来自 `demandexpirationdate`）。见 doc 13 Section 3.1。  
**相关**：FCL；Referral；First Legal

---

**First Legal**（首次法律行动）

止赎律师代表贷款方采取的第一个正式法律步骤（如递交诉状或录制 Notice of Default）。标志着法律程序正式进入公开记录。

---

**Service**（文件送达）

法律文件（传票、诉状）正式送达借款人的阶段。司法止赎中为必要环节，借款人收到文件后有一定期限提出抗辩。

---

**Judgment**（判决）

法院对贷款方有利的裁决，允许其继续进行拍卖。在司法止赎州，Judgment 是拍卖前的最后法律关卡。

---

**Sale**（拍卖）

FCL 流程的最终处置阶段：房产被公开拍卖。结果：
- 有第三方出价 → `3rd Party Sale`（映射到 `P`）
- 无第三方出价 → 房产归贷款方 → `REO`

---

**3rd Party Sale**（第三方拍卖成交）

拍卖中有外部买家出价成功，房产归第三方（既非原借款人、也非贷款方）所有，是 FCL 的"成功出售"结果。贷款系统内部码映射为 `P`（Paid），贷款关闭。  
与 **REO**（无人出价，贷款方取得房产并进入持有期）相对。Newrez 通过 `fcresults` 字段记录最终处置结果；BPS 据此判断是否填充 `timeline_third_party_sold_date_date` 和 `timeline_third_party_proceeds_received_date` 字段（见 doc 13 Section 3.1）。  
**相关**：REO；Sale；fcresults（Newrez 字段）

---

**dtdeedrecorded**（止赎契据登记日 / Deed Recorded Date）

Newrez `portnewrezfc` 日期字段：成交后产权转让契据（Trustee's / Sheriff's Deed）在县/郡土地登记处**正式登记的日期**，即止赎法律流程的**完成点**——产权在这一天正式过户（多数转给贷款方成为 **REO**，少数转给第三方买家）。  
时序上在 `fcsalehelddate`（拍卖举行日）之后约 **2–3 周**（实测样例），对应贷款 `fcresults=REO / fcremovaldesc=Process Complete`。BPS 用它作 `timeline_foreclosure_completed_date = COALESCE(dtdeedrecorded, fcremovaldate)` 的**首选来源**；Newrez 无独立「REO 取得日」字段，故 doc 14 用 `dtdeedrecorded` **近似** `reo_acquisition_date`（REO 持有期计算）。实测填充率极低（~0%，走到产权过户的贷款很少）。  
**相关**：Sale Held（`fcsalehelddate`）；`fcremovaldate`（FCL 撤销/完结日）；REO；`timeline_foreclosure_completed_date`（BPS）

---

**Target Days / Actual Days / Var Days**（目标天数 / 实际天数 / 差异天数）

BPS 系统衡量 FCL 各阶段合规表现的三层天数框架（见 doc 13 Section 3.2–3.4）：

| 维度 | BPS 字段前缀 | 数据来源 | 含义 |
|------|------------|---------|------|
| **Target Days** 目标天数 | `target_*` | 系统配置常量（按州 / 司法类型预设） | 各阶段的合规基准天数；与 Newrez 无关 |
| **Actual Days** 实际天数 | `actual_*` | 两端 timeline 日期相减（`DATEDIFF`） | 各阶段实际经历的天数 |
| **Var Days** 差异天数 | `var_*` | `actual_* − target_*` | 正数 = 超期落后；负数 = 提前；0 = 达标 |

共 15 个 FCL 阶段各有一组 target/actual/var 字段，另加 `*_total`（全程汇总）。  
**相关**：doc 13 Section 3.2/3.3/3.4；`bpms_dev.sync_loan_foreclosure`（BPS MySQL 存储表）

---

## 分类 D — LM 类型（六种）

**Forbearance**（宽限协议）

暂停或减少借款人的月供义务，到期后补缴欠款（通常分期摊回）。典型时长 3–12 个月。COVID 期间大量使用。属于临时性安排，到期后可转为 Modification 或恢复正常还款。

---

**Loan Modification**（贷款修改）

永久性修改贷款条款（利率、还款期限、本金余额等），使借款人的月供降至可负担水平。是最根本的 LM 解决方案，处理后贷款恢复正常还款状态。

---

**Repayment Plan**（还款计划）

借款人在恢复正常月供的同时，额外分期补缴之前的欠款。通常持续 3–6 个月，与正常还款并行。适合短期困难已解决的借款人。

---

**Trial Period Plan**（试行期计划）

永久性 Modification 生效前的试用期（通常 3 个月）。借款人需按拟议的新条款完成 3 次按时还款，才能进入正式 Modification。试行期通过 → Permanent Modification；试行期失败 → LM 申请被拒。

---

**Short Sale**（短售）

贷款方允许借款人以低于贷款余额的价格出售房产，贷款方同意免除差额。贷款在 Short Sale 完成后关闭，系统内部码映射为 `P`。属于"受控止赎替代方案"。

---

**Deed in Lieu**（代替止赎房产移交）

借款人主动将房产所有权移交给贷款方，换取贷款全额免除。效果与止赎相同（贷款方取得房产），但避免了公开拍卖程序，对双方损失更小。贷款关闭后映射为 `P`。

---

## 分类 E — 破产相关

**Automatic Stay**（自动中止令）

借款人申请破产后**立即自动生效**的联邦法律保护，强制暂停所有催收行动，包括：电话催收、法庭诉讼、止赎程序（FCL Hold）。无需法院单独命令，申请破产即触发。  
**影响**：正在进行的 FCL 进入 Hold 状态，直至破产程序结束或法院解除自动中止令。

---

**Chapter 7**（清算型破产）

美国破产法第 7 章。借款人无力偿债，法院任命破产受托人清算非豁免资产还债，剩余无担保债务全部免除。典型周期 3–6 个月，是流程最短的破产类型。  
**对 FCL 的影响**：Chapter 7 通常不能挽救房屋，止赎最终会恢复推进（但在 BK 期间受 Automatic Stay 保护）。

---

**Chapter 13**（重组型破产）

美国破产法第 13 章。借款人提出 3–5 年的还款计划，逐步偿还欠款（含逾期房款），同时保留房产所有权。是希望通过破产保住房屋的借款人的主要选择。  
**对 FCL 的影响**：Chapter 13 可以"固化"逾期欠款并允许借款人追赶还款，FCL 在计划执行期间持续暂停。

---

**FCL-Hold**（止赎暂停）

止赎程序已法律启动（FCL flag = Y）但操作上暂时中止的状态。  
**常见原因**：Automatic Stay（BK）/ 借款人申请 LM / HUD 特殊要求 / COVID 宽限 / 法院指令。  
**MBA 框架中的处理**：MBA `delinquency_status` 无 Hold 分类，贷款仍报告为 `Foreclosure`。因此必须用独立的 `fcl_hold_flag` + `hold_reason` 字段来表达 Hold 状态。  
**相关**：Automatic Stay；LM；hold_flag / hold_reason（数据字段）

---

**MFR**（Motion for Relief from Automatic Stay，解除自动中止令申请）

贷款方（债权人）在破产程序中向破产法院正式申请解除 Automatic Stay，以恢复对借款人的催收和止赎行动。法院批准后，FCL 程序即可从 Hold 状态恢复推进。  
**典型场景**：Chapter 7 破产申请后，贷款方认为借款人无意保留房产或破产计划不可行，遂申请 MFR 以尽快恢复止赎。  
**相关 BPS 字段**：`mfr_filed_date`（MFR 提交日）、`mfr_status`（MFR 听证结果）（见 doc 13 Section 6）  
**相关**：Automatic Stay；FCL-Hold；BK；Chapter 7 / 13

---

**POC**（Proof of Claim，债权申报书）

债权人（贷款方）在破产程序中向破产法院正式登记债权金额的书面文件，说明借款人欠款总额（含本金、利息、滞纳金、费用等）。POC 是在破产程序中保护债权的必要步骤。  
**时限**：Chapter 7 通常须在债权人通知后 70 天内提交；Chapter 13 须在方案确认前提交。  
**影响**：未及时提交 POC 可能导致债权在破产程序中被忽略，贷款方无法参与资产分配。  
**相关 BPS 字段**：`proof_of_claim_date`（POC 提交日）（见 doc 13 Section 6）  
**相关**：BK；Automatic Stay；Chapter 7 / 13；MFR

---

## 分类 F — ETL 架构术语

**L1**（原始数据层 / MySQL Staging）

ETL 管道第一层：Servicer 原始文件入库后的 MySQL staging 表。数据直接来自 Servicer，未经归一化处理。表名格式：`port{servicer}loan`（如 `portslsloan`、`portnewrezloan`）。  
**数据特点**：字段命名各异、取值不统一、按 Servicer 分表存储。

---

**L2**（归一化层 / Redshift 统一视图）

ETL 管道第二层：Redshift 中按统一 schema 归一化后的中间表。核心表：`port.basic_data_daily_loan_common`（日报）/ `port.basic_data_monthly_loan_common`（月报）。  
**数据特点**：各 Servicer 字段映射为统一列名，但部分判断逻辑（如 FCL 状态）尚未应用。

---

**L3**（Clean 层 / 状态判断后）

ETL 管道第三层：经 Step 3 处理后，`delinq` 状态码已确定，数据质量经过校验。  
**相关**：Step 3；daily_data_loan_common_clean_config.py

---

**L4**（月度聚合层）

ETL 管道第四层：以月为粒度的聚合分析表。核心表：`portmonthbase`（月度主表）/ `portmonth`（含月度新增衍生字段的扩展表）。用于 BPS 报告和下游分析。

---

**Step 3**

ETL 管道中负责状态判断的核心 Python 脚本：`daily_data_loan_common_clean_config.py`。作用：读取 L2 数据，按各 Servicer 的规则将原始字段映射为系统内部状态码（`delinq` = C/D30/.../FCL/REO/P）。  
**缺失的含义**：若某个 Servicer 在 Step 3 中没有对应的 SQL 逻辑块，则 `delinq` 字段始终为 null（典型案例：Selene、FCI）。  
**相关**：L2 → L3 的转换节点

---

**portmonthbase**

Redshift 月度主分析表（L4 层），汇总每笔贷款的月末状态快照。是 BPS 报告、月度对账的核心数据来源。约 120 列，含系统内部逻辑字段。  
**相关**：portmonth（在 portmonthbase 基础上新增 23 个衍生字段）

---

**basic_data_loan_fix**

人工覆盖修正表，存储经过人工审核确认的状态更正记录。在 ETL 管道中具有**最高优先级**，高于所有自动计算结果。  
**用途**：纠正 Servicer 数据错误或系统判断逻辑产生的特例偏差。

---

**days360**

按 360 天/年（每月 30 天）计算两个日期之间天数差的函数。用于贷款行业标准的 DPD 计算：`DPD = days360(next_payment_due_date, report_date)`。  
**重要性**：当 Servicer 未提供 `delinquency_status` 时（如 Arvest 月报），`next_payment_due_date` + days360 是唯一的 DPD 兜底计算方法。

---

**fctrdt**（FCT Report Date）

报告截止日，通常为月末次日（即下月第一天，如 3 月末 → 4 月 1 日）。是 portmonthbase 和月报分析的时间维度键。格式：`YYYY-MM-DD`。

---

## 分类 G — 系统缩写 / 数字名词

| 术语 | 全称 | 含义 |
|------|------|------|
| **UPB** | Unpaid Principal Balance | 未偿还本金余额。贷款当前还剩多少本金未还，是衡量贷款规模的基础指标。 |
| **DPD** | Days Past Due | 逾期天数。从 `next_payment_due_date` 到报告日之间的 days360 差值。 |
| **MBA** | Mortgage Bankers Association | 美国抵押贷款银行家协会。行业标准的制定组织，本项目中特指 MBA 逾期状态分类标准（文本枚举取值规范）。 |
| **NOI** | Notice of Intent / Notice of Default | 贷款方向借款人发出的正式违约通知，通常是启动 FCL 前的必要步骤。详见分类 C「NOI / Demand Letter」完整词条。 |
| **MFR** | Motion for Relief (from Automatic Stay) | 贷款方向破产法院申请解除自动中止令的动议。详见分类 E「MFR」完整词条。 |
| **BPS** | Business Planning System | 业务规划系统，PrefectFlow 的下游报告消费系统。月度分析结果最终同步至 BPS。 |
| **Servicer** | Mortgage Loan Servicer（贷款服务商） | 代表贷款所有方（如基金）负责日常贷款管理的机构，包括收取还款、跟踪逾期状态、执行止赎程序等。本项目涉及 8 个 Servicer：SLS / Newrez / Carrington / Selene / MRC / Arvest / CapeCodFive / FCI。 |
| **Deal ID** | Portfolio / Deal Identifier（投资组合编号） | 将多笔贷款归为同一投资组合的业务标识符。同一 Servicer 可能服务多个 Deal。 |
| **svcdelinq** | Servicer Delinquency（服务商原始逾期描述） | L2 层中存储 Servicer 原始传输的逾期状态文本，未经标准化。与系统内部 `delinq` 码相区分。 |
| **dataasof** | Data As Of（数据截止日） | Servicer（如 Newrez）向系统同步数据时的快照日期，通常滞后当天 1–2 天。BPS 在展示"今日 FCL 天数"时，通过 `DATEDIFF(今日, dataasof)` 补偿延迟，以反映真实的当日天数。 |
| **SMS** | Shellpoint Mortgage Servicing | Newrez 的运营子品牌全称（Newrez LLC 已更名，但部分历史字段仍使用旧品牌缩写）。`smsdaysinfc`（"SMS 报告的 FCL 天数"）中的"SMS"即来源于此，与投资者口径的 `daysinfc` 相对应。 |
| **CFPB** | Consumer Financial Protection Bureau（消费者金融保护局） | 美国联邦消费金融监管机构；其按揭服务规则（Reg X）是本项目 LM/FCL 合规字段的法规依据。详见分类 H。 |
| **RESPA** | Real Estate Settlement Procedures Act（房地产结算程序法） | Reg X 所实现的母法。详见分类 H。 |
| **SPOC** | Single Point of Contact（专属联系人） | CFPB Reg X 12 CFR 1024.40 要求为违约借款人指派的唯一服务对接人，对应字段 `single_point_of_contact`。详见分类 H。 |

---

## 分类 H — 监管 / 合规术语（Regulatory / Compliance）

**CFPB**（消费者金融保护局，Consumer Financial Protection Bureau）

美国联邦监管机构，依据 Dodd-Frank Act（2010）设立，负责制定并执行消费金融（含按揭贷款）的保护规则。本项目中 servicer（如 Newrez）的损失缓解 / 止赎合规要求即来自 CFPB 规则。

---

**RESPA**（房地产结算程序法，Real Estate Settlement Procedures Act）

美国联邦法律，规范房地产结算与按揭服务行为。CFPB 通过 **Reg X** 实施 RESPA 的按揭服务条款。

---

**Reg X**（法规 X，Regulation X — 12 CFR Part 1024）

RESPA 的实施细则，编于《美国联邦法规》第 12 编第 1024 部分。其按揭服务条款（1024.30–1024.41，2014 年生效）规定 servicer 对违约借款人和损失缓解（LM）的处理义务，是本项目 LM/FCL 合规字段的法规来源。

---

**12 CFR 1024.40 / SPOC**（持续联系 / 专属联系人，Continuity of Contact / Single Point of Contact）

Reg X 1024.40 要求 servicer 为违约借款人指派一名**专属联系人（SPOC）**，避免借款人在 LM 流程中被不同客服反复转接。对应 BPS 字段 `single_point_of_contact`（Newrez 不提供、恒 NULL，见 doc 13 Q6 / doc 14）。

---

**12 CFR 1024.41**（损失缓解程序，Loss Mitigation Procedures）

Reg X 1024.41 规定 servicer 在推进止赎前评估借款人 LM 选项的程序与时限（完整申请审查期、上诉权等）。是 LM Cycle 各字段的合规背景。

---

**Imminent Default**（即将违约）

指借款人**尚未实际拖欠**、但面临可预见还款困难的状态。Reg X / 投资人指南要求 servicer 对这类借款人也提前进行 LM 评估，而非等到真正违约。对应 BPS 字段 `imminent_default`（Newrez 不提供、恒 NULL，见 doc 13 Q6 / doc 14）。
