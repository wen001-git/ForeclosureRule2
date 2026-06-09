# 24 — BK → Current 与 BK → Foreclosure 的核心差异

---

## 文档目的

- **为什么存在**：状态机图（`fcl_pipeline.html` / doc 17 §4 / doc 07 §2.4）从 **BK — Bankruptcy** 节点引出两条出边——一条到 **C（Current）**、一条到 **FCL（Foreclosure）**。本文把"这两条边的核心差异是什么、各自由什么触发、法律依据是什么"讲透，作为可独立分享的专题。
- **解决的问题**：读者常误以为"破产成功就回 Current、破产失败就止赎"；真正的分水岭是**这笔房贷的违约（arrears）有没有被 cure**，与破产是否"discharge"并不等价（Ch.7 discharge 反而通常走止赎）。
- **范围**：仅覆盖 BK 节点这两条出边的差异、触发条件与法律依据；不覆盖完整破产业务（见 doc 17 §5.4 / doc 07 §2.5）、不覆盖 BK→payoff 时长（见 doc 23）。
- **系统关系**：doc 17 §5.4 / doc 07 §2.5「BK 状态转换法律依据」的专题展开版；所有法条依据来自 Title 11（Cornell LII）与 U.S. Courts Bankruptcy Basics 官方文本。

## 目标读者

主要读者：业务分析师 · 数据产品经理 · 运营 · 新同事  
次要读者：ETL 开发者 · 验证/对账工程师 · 风险/资产管理 · 未来 AI Session

## 修订历史

| 日期 | 作者 | 版本 | 变更说明 | 关联文档 |
|------|------|------|---------|---------|
| 2026-06-08 | AI Agent (Claude Opus 4.8) | v1 | 初版：BK→Current vs BK→Foreclosure 核心差异、触发条件、对比表、法律依据与权威来源、系统透传说明 | doc 17 · doc 07 · doc 23 |

## 已知限制

- 本文为业务/法律背景材料，不替代法律意见或合规判定。
- 各州具体止赎/破产程序细节不同；本文按联邦破产法（Title 11）通则说明。

---

## 1. 问题

状态机里 **BK** 有两条出边——`BK → C` 与 `BK → FCL`，二者的**核心差异**是什么？

## 2. 一句话核心差异

**看破产有没有"治好"这笔房贷的违约：**
- **BK → Current**：破产程序（Chapter 13）**把拖欠的房贷补缴干净、贷款恢复正常** → 房子保住、delinq 回到 `C`。**治愈/成功**路径。
- **BK → Foreclosure**：破产程序结束时房贷违约**仍未解决**，自动中止令（Automatic Stay）被解除 → 贷款方**恢复止赎**。**未治愈/中止令失效**路径。

> 关键：分水岭是**房贷欠款是否被 cure**，**不是**"破产是否 discharge"。Ch.7 discharge 只免除个人债务责任、抵押权（lien）存续，反而通常走止赎。

## 3. 两条边详解

### 3.1 BK → Current（图中 "Ch.13 done"）

- 借款人走 **Chapter 13**（重组 / 还款计划），在 **3–5 年**内**补缴拖欠的房贷欠款（arrears）**，同时维持当期月供。
- 计划全部还清后获得 discharge，房贷恢复正常（reinstate）→ delinq 回 `C`，房子保住。
- 法律机制：
  - **§ 1322(b)(5)**：计划可"在合理期限内 cure 违约、并维持还款"。
  - **§ 1328(a)**：在"完成计划全部还款后"给予 discharge。
- U.S. Courts 原话：*"The individual may then **bring the past-due payments current** over a reasonable period of time."*

### 3.2 BK → Foreclosure（图中 "BK lifted/discharged → resume"）

破产结束但房贷违约**未被解决**，自动中止令（§ 362）不再保护借款人，止赎恢复。三种触发方式：

| 触发 | 机制 | 法条 |
|------|------|------|
| **驳回 / 计划失败** | Ch.13 计划未履行（停缴），案件 dismissed，中止令终止 | § 362(c) |
| **MFR 获准** | 贷款方申请"解除中止令"（Motion for Relief），法院批准后即可继续止赎 | § 362(d) |
| **Ch.7 discharge** | Ch.7 只免除**个人债务责任**，**抵押权（lien）存续**；欠款未补，房子照样可被止赎 | § 727 + § 524(a)(2) |

- U.S. Courts 原话：*"Creditors have the right to ask the bankruptcy court to **lift the stay** … If the stay is lifted, the creditor may then proceed … **completing its foreclosure action**."*

## 4. 对比表

| 维度 | BK → Current | BK → Foreclosure |
|------|--------------|------------------|
| 房贷违约是否被治愈 | **是**（arrears 补缴完成） | **否**（违约仍在） |
| 典型章节 | **Chapter 13**（重组，可保房） | **Chapter 7**（清算，留不住房）或 **Ch.13 失败被驳回** |
| 退出机制 | 计划完成 → discharge、贷款 reinstate | 中止令被解除：dismissal / MFR / Ch.7 后 lien 存续 |
| 自动中止令命运 | 完成使命后正常结束 | **提前被解除 / 终止**，止赎恢复 |
| 房子结局 | 保住 | 走向拍卖（→ FCL → REO / 第三方拍卖） |
| 法条依据 | § 1322(b)(5) cure + § 1328(a) discharge | § 362(c) 终止 / § 362(d) MFR / § 727 + § 524(a)(2) |

## 5. 章节视角：Ch.7 vs Ch.13

- **Chapter 13（重组）** = 设计目标就是**保房**：补缴欠款 + 维持月供 → 通常 **→ Current**。
- **Chapter 7（清算）** = 免除个人债务、但**不消除抵押权**：欠款没治、lien 存续 → 通常 **→ Foreclosure**。
- **易错点**：Ch.7 ≠ 一定止赎——若借款人 reaffirm（重申债务）并继续正常还月供，也可能回 Current；但本系统中这些都是**已严重逾期 + 已进 FCL** 的贷款，Ch.7 典型走向就是「个人责任免除、lien 存续 → 止赎恢复」。这也是图里把 Ch.13 画到 C、把 discharge/lifted 画到 FCL 的原因。

## 6. 自动中止令（Automatic Stay）这一层的机制

- 借款人申请破产 → **§ 362(a)** 自动中止令立即冻结止赎（FCL → FCL-Hold，详见 doc 17 §5.4「自动中止令 ≠ 永久禁止拍卖」）。
- **两种退出**决定走向哪条边：
  - **靠 cure 退出**（Ch.13 完成补缴）→ 中止令完成使命、贷款 reinstate → **Current**。
  - **靠中止令被解除退出**（dismissal / § 362(d) MFR / Ch.7 后 lien 存续）→ **Foreclosure**。

## 7. 与本系统的关系（重要）

这两条边在**法律上**成立，但本 ETL **不会自己计算**它们——系统只是逐月**透传 servicer 上报的 `delinquency_status_mba`**：

- 当借款人因 Ch.13 完成而被 servicer 重新报成 `Current` 时，delinq 才变 `C`；
- 当 servicer 把状态报回 `Foreclosure` 时才走 FCL。

系统**反映**结果、不**推导**结果（见 `03_fcl_status_logic.md` §2.1 第 77–114 行；`Foreclosure / Perf·Non-Perf BK` 由 `CREATE_FCL_RELATE_ATTR` 映射为 `FCL`）。

## 8. 权威来源

- [Chapter 13 — Bankruptcy Basics (U.S. Courts)](https://www.uscourts.gov/court-programs/bankruptcy/bankruptcy-basics/chapter-13-bankruptcy-basics)
- [Chapter 7 — Bankruptcy Basics (U.S. Courts)](https://www.uscourts.gov/court-programs/bankruptcy/bankruptcy-basics/chapter-7-bankruptcy-basics)
- [11 U.S.C. § 1322 (cure + maintain)](https://www.law.cornell.edu/uscode/text/11/1322)
- [11 U.S.C. § 1328 (discharge on plan completion)](https://www.law.cornell.edu/uscode/text/11/1328)
- [11 U.S.C. § 362 (automatic stay / relief from stay)](https://www.law.cornell.edu/uscode/text/11/362)
- [11 U.S.C. § 727 (Ch.7 discharge)](https://www.law.cornell.edu/uscode/text/11/727)
- [11 U.S.C. § 524 (effect of discharge — personal liability only)](https://www.law.cornell.edu/uscode/text/11/524)

## 9. 相关文档

- BK 业务与法律依据：doc 17 §5.4、doc 07 §2.5
- 状态机与转换：doc 17 §4、doc 07 §2.4、`outputs/fcl_pipeline.html`
- BK discharge → payoff 时长（DB 实测）：doc 23
