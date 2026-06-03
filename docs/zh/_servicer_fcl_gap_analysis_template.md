# Servicer FCL 字段缺口分析模板

---

## 文档目的

- **为什么存在**：为每个 Servicer 独立分析从原始日报/月报到 Foreclosure 状态、BPS 展示字段、字段缺口的完整链路提供统一模板。
- **解决的问题**：避免各 Servicer 文档结构不一致，导致字段缺口、内部 ETL 缺口、对外请求事项无法横向比较。
- **范围**：覆盖单个 Servicer 的原始文件/表、FCL 状态判断链路、BPS doc 14 字段对照、缺口分级、证据与行动项。
- **系统关系**：本文档模板服务于 ForeclosureRule2 文档体系；每个实际 Servicer 文档应引用 `14_bps_driven_servicer_fcl_interface.md` 作为目标标准。

## 目标读者

数据产品经理 · 数据治理团队 · Servicer 对接工程师 · ETL 开发者 · BPS 运营人员 · 未来 AI Session

## 修订历史

| 日期 | 作者 | 版本 | 变更说明 | 关联文档 |
|------|------|------|---------|---------|
| 2026-05-28 | LiJiawen | v1 | 初始模板，用于后续逐 Servicer 缺口文档 | doc 14 |
| 2026-05-28 | LiJiawen | v2 | 增加数据库验证计划章节，要求每个 Servicer 文档用 MCP/SQL 验证字段存在性、填充率、枚举值和样本 loan 血缘 | doc 98 |

## 依赖文档

| 文档 | 用途 |
|------|------|
| doc 01 | 原始表和字段来源索引 |
| doc 07 | 当前系统按 Servicer 的血缘与判断规则 |
| doc 08 | Servicer 原始字段到 FCL 状态的现状映射 |
| doc 13 | BPS 展示字段反向映射 benchmark |
| doc 14 | BPS 驱动的目标接口标准 |
| doc 98 | 数据库验证与 MCP 使用规范 |

---

## 1. Servicer 概况

| 项目 | 内容 |
|------|------|
| Servicer | `<Servicer Name>` |
| 数据频率 | 日报 / 月报 / 混合 |
| 当前原始来源 | S3 / SFTP / 共享盘 / Excel / CSV / 其他 |
| 当前 raw/staging 表 | `schema.table` |
| FCL 专项表 | `schema.table` / 无 |
| LM 专项表 | `schema.table` / 无 |
| BK 专项表 | `schema.table` / 无 |
| 当前系统评级 | ✅完整 / 🟡部分可用 / ❌不可用 |

## 2. 当前数据血缘链条

```
Servicer 原始文件
  -> MySQL raw/staging 表
  -> PrefectFlow 归一化配置
  -> Redshift 中间/分析表
  -> delinq / FCL 判断
  -> BPS sync 表
  -> BPS Foreclosure UI
```

| 层级 | 表/文件/代码 | 作用 | 证据 |
|------|-------------|------|------|
| 原始文件 | `<file pattern>` | Servicer 提供的源数据 | `<source>` |
| MySQL raw | `schema.table` | 原始字段入库 | doc 01 / DB |
| 归一化 | `PrefectFlow path` | 字段重命名、JOIN、类型转换 | 代码路径 |
| 状态判断 | `PrefectFlow path` | 生成 `delinq` / FCL 标识 | 代码路径 |
| BPS 同步 | `sync_*` | 写入 BPS 展示表 | doc 12 / doc 13 |

## 3. Foreclosure 状态判断逻辑

| 判断层级 | 字段/规则 | 当前实现 | 风险 |
|----------|----------|----------|------|
| 显式 FCL 标志 | `<field>` | `<rule>` | `<risk>` |
| 逾期状态文本 | `<field>` | `<mapping>` | `<risk>` |
| 日期兜底 | `nextduedate` / days360 | `<rule>` | 不能替代法律 FCL 状态 |
| 人工覆盖 | `basic_data_loan_fix` | `<rule>` | 需单独审计 |

## 4. doc 14 目标字段对照

状态取值：

- `已提供`：Servicer 已提供且当前系统可使用。
- `部分提供`：字段存在但填充率、枚举、含义或时效性有问题。
- `未提供`：Servicer 当前没有对应字段。
- `内部可推导`：Servicer 不直接提供，但系统能可靠计算。
- `内部 ETL 缺口`：Servicer 已提供或可推导，但当前 PrefectFlow/BPS 链路未接入。

| doc 14 字段组 | 关键字段 | 当前状态 | 当前来源 | 缺口性质 | 优先级 |
|---|---|---|---|---|---|
| P0 入库字段 | `loan_id`, `data_as_of_date`, `state`, `fcl_referral_date` | `<status>` | `<source>` | `<gap>` | P0 |
| FCL Summary | `current_milestone`, `days_in_fcl`, `attorney_firm` | `<status>` | `<source>` | `<gap>` | P1 |
| Timeline | `demand_sent_date`, `first_legal_date`, `service_complete_date`, `sale_date` | `<status>` | `<source>` | `<gap>` | P1/P2 |
| Hold | `hold_description/start/end` | `<status>` | `<source>` | `<gap>` | P1/P2 |
| LM | `lm_deal`, `lm_status`, `cycle dates` | `<status>` | `<source>` | `<gap>` | P1/P2 |
| BK | `bk_chapter`, `bk_status`, `mfr`, `poc` | `<status>` | `<source>` | `<gap>` | P1 |

## 5. 缺口与行动项

| 类型 | 行动项 | Owner | 优先级 | 验收标准 |
|------|--------|-------|--------|----------|
| 向 Servicer 请求 | `<field request>` | 数据产品/数据治理 | P0/P1/P2 | Servicer 文件新增或修正字段 |
| 内部 ETL 修复 | `<internal fix>` | ETL 开发 | P0/P1/P2 | 字段进入目标表且可回归验证 |
| BPS 产品确认 | `<question>` | BPS 产品/运营 | P1/P2 | 确认展示含义和字段命名 |

## 6. 数据库验证计划

> 默认使用 MCP 只读查询验证。若沿用历史查询结果，必须说明来源文档、查询日期和快照日期。

| 验证类型 | MCP/数据库 | 目标表 | 目标字段/规则 | SQL 引用 | 结论 |
|----------|------------|--------|---------------|----------|------|
| Schema 验证 | MySQL / Redshift | `<schema.table>` | `<fields>` | `<SQL-x>` | `<conclusion>` |
| Fill rate 验证 | MySQL / Redshift | `<schema.table>` | `<fields>` | `<SQL-x>` | `<conclusion>` |
| Enum 验证 | MySQL / Redshift | `<schema.table>` | `<status field>` | `<SQL-x>` | `<conclusion>` |
| 样本 loan 验证 | MySQL + Redshift | `<source -> target>` | `<loanid list>` | `<SQL-x>` | `<conclusion>` |
| 缺口验证 | MySQL / Redshift / 代码 | `<schema.table or path>` | `<gap>` | `<SQL-x or code path>` | `<conclusion>` |

### 推荐 SQL 模板

```sql
-- Purpose: verify <business conclusion>
-- Source: <schema.table>
-- Snapshot: <dataasof/fctrdt condition>
SELECT ...
```

## 7. 验证证据

| 证据类型 | 位置 | 覆盖结论 |
|----------|------|----------|
| PrefectFlow 代码 | `<path>` | `<conclusion>` |
| DB/MCP 查询 | `<sql reference>` | `<conclusion>` |
| BPS 截图/doc 13 | `<section>` | `<conclusion>` |
| 样本贷款 | `<loanid>` | `<conclusion>` |

## 8. Open Questions

| 问题 | 为什么重要 | 建议确认对象 |
|------|------------|--------------|
| `<question>` | `<impact>` | `<owner>` |
