# doc 99 — Servicer FCL 缺口汇总与行动计划

---

## 文档目的

- **为什么存在**：把 ForeclosureRule2 已完成的现状研究、BPS 需求反推、doc 14 接口标准和逐 Servicer 缺口分析整合成后续执行路线。
- **解决的问题**：管理层和项目成员需要快速知道接下来先审什么、先写哪个 Servicer、哪些问题要向 Servicer 请求、哪些属于内部 ETL/BPS 修复。
- **范围**：覆盖后续文档产出顺序、统一判断口径、行动项分类和验收标准；不替代单个 Servicer 的详细字段分析。
- **系统关系**：本文是 ForeclosureRule2 的工作总控文档，依赖 doc 14 作为目标字段标准，依赖 doc 15 作为第一个逐 Servicer 样例。

## 目标读者

数据产品经理 · 管理层 / Reviewer · 数据治理团队 · ETL 开发者 · BPS 运营人员 · 未来 AI Session

## 修订历史

| 日期 | 作者 | 版本 | 变更说明 | 关联文档 |
|------|------|------|---------|---------|
| 2026-05-28 | LiJiawen | v1 | 初始行动计划；落地后续 doc 14 审核和逐 Servicer 缺口分析路线 | doc 14, doc 15 |
| 2026-06-08 | AI Agent (Claude Opus 4.8) | v2 | 用词正式化：目标读者表述统一为「管理层 / Reviewer」 | — |

## 依赖文档

| 文档 | 用途 |
|------|------|
| doc 07 | 当前系统按 Servicer 的血缘和判断规则 |
| doc 08 | Servicer 原始字段到 FCL 状态映射现状 |
| doc 13 | BPS 展示字段反向映射 benchmark |
| doc 14 | BPS 驱动的目标接口标准 |
| doc 15 | Newrez 缺口分析样例 |
| doc 98 | 数据库验证与 MCP 使用规范 |

---

## 1. 当前结论

| 结论 | 说明 |
|------|------|
| doc 14 可以作为后续目标标准 | v3 已增加审核状态和字段准入检查规则 |
| Newrez 应作为第一个 benchmark Servicer | doc 13 已完成 BPS 展示反向映射，doc 15 已形成逐 Servicer 样例 |
| 数据库验证默认使用 MCP | doc 98 已规定只读查询、SQL 留痕、快照日期记录和敏感信息处理 |
| 后续工作应区分两类缺口 | 一类是向 Servicer 请求字段；另一类是公司内部 ETL/BPS 链路未接入或展示口径不清 |
| 管理层材料应从逐字段文档抽取 | 不应直接让 reviewer 阅读所有代码级细节；需要总表和行动项 |

## 2. 后续产出顺序

| 顺序 | 文档 | 目标 | 状态 |
|------|------|------|------|
| 1 | `14_bps_driven_servicer_fcl_interface.md` | 冻结 BPS 驱动的目标字段标准 | 已完成 v3 审核状态 |
| 2 | `_servicer_fcl_gap_analysis_template.md` | 统一后续 Servicer 文档结构 | 已完成 v1 |
| 3 | `15_newrez_servicer_fcl_gap_analysis.md` | benchmark Servicer 样例 | 已完成 v1 |
| 3.5 | `98_database_verification_strategy.md` | 统一 MCP/SQL 只读验证规范 | 已完成 v1 |
| 4 | `16_carrington_servicer_fcl_gap_analysis.md` | 最完整 FCL flag Servicer 对照 | 待执行 |
| 5 | `17_sls_servicer_fcl_gap_analysis.md` | 历史 SLS 与 Newrez 切换链路 | 待执行 |
| 6 | `18_selene_servicer_fcl_gap_analysis.md` | 字段已采集但 ETL 未接入案例 | 待执行 |
| 7 | `19_mrc_servicer_fcl_gap_analysis.md` | 原始状态字段为空/不可用案例 | 待执行 |
| 8 | `20_arvest_servicer_fcl_gap_analysis.md` | 月报且缺少 FCL 状态字段案例 | 待执行 |
| 9 | `21_capecodfive_servicer_fcl_gap_analysis.md` | 字段格式错误导致 FCL 无法识别案例 | 待执行 |
| 10 | `22_fci_servicer_fcl_gap_analysis.md` | 低覆盖/未实现案例 | 待确认是否仍在范围内 |

## 3. 统一行动项分类

| 分类 | 判断标准 | 示例 |
|------|----------|------|
| 向 Servicer 请求 | 原始文件没有字段、字段填充率不足、枚举不符合标准、或字段含义需要 Servicer 解释 | Newrez `publication_date`、CapeCodFive MBA 文本枚举 |
| 内部 ETL 修复 | Servicer 已给字段，但 PrefectFlow 未接入、未映射到 `delinq`、或未同步到 BPS | Selene `foreclosure_status_code='A'` 未接入 Step 3 |
| BPS 产品确认 | 数据存在但 UI 字段名、显示口径、是否应展示仍不清楚 | Newrez Demand Date 是否展示为 NOI Date |
| 数据质量监控 | 字段已接入，但存在填充率、时序、异常值问题，需要持续监控 | Newrez `fcsaleamount` 早于 `fcsalehelddate` |
| 数据库验证 | 使用 MCP 只读查询确认字段存在性、填充率、枚举分布、样本 loan 血缘 | doc 98 标准 SQL、doc 15 Section 7 |

## 4. 每个 Servicer 文档验收标准

| 检查项 | 通过标准 |
|--------|----------|
| 标准文档头 | 包含目的、目标读者、修订历史、依赖、限制 |
| 血缘链条 | 能从原始表追到 PrefectFlow、Redshift/BPS sync、BPS UI |
| 状态判断 | 明确 FCL 是由显式字段、逾期文本、日期兜底还是人工覆盖产生 |
| doc 14 对照 | 至少覆盖 P0、FCL Summary、Timeline、Hold、LM、BK、Stage/Timeline 七组 |
| 缺口分类 | 明确区分 Servicer 请求、内部 ETL 修复、BPS 产品确认 |
| 证据 | 至少引用 doc 08/13/14 或 PrefectFlow 代码路径；关键结论应可复现 |
| SQL 留痕 | DB 实测结论必须附查询目的、SQL、快照日期、结果摘要 |

## 5. 下一步建议

1. 先让 reviewer 审 doc 14 v3 的字段范围、优先级定义和 Open Questions。
2. 用 doc 98 作为查库验证标准，所有后续“DB 实测”结论都附可复制 SQL。
3. 用 doc 15 Newrez 样例确认单个 Servicer 文档的粒度是否合适。
4. 按 Carrington → SLS → Selene/MRC → Arvest/CapeCodFive → FCI 的顺序继续产出。
5. 完成 3 个 Servicer 后，抽取第一版管理层矩阵：`Servicer × P0/P1/P2 gap × owner × action`。
