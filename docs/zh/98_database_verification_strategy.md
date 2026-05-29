# doc 98 — 数据库验证与 MCP 使用规范

---

## 文档目的

- **为什么存在**：ForeclosureRule2 的结论需要经常连接 MySQL 和 Redshift 验证字段、取值、填充率、样本 loan 血缘。本文规定后续研究如何使用 MCP 和 SQL 验证，避免只凭代码或历史文档推断。
- **解决的问题**：统一“什么时候查库、查哪个库、怎么记录 SQL、怎么保护连接信息”的工作方式，使每个 Servicer 缺口文档都可复现、可审计。
- **范围**：覆盖只读数据库验证流程、MCP 优先级、Python 直连 fallback、SQL 证据记录、敏感信息处理。不覆盖数据库写入、运维、权限申请。
- **系统关系**：本文是 ForeclosureRule2 的横向工作规范，服务于 doc 13、doc 14、doc 15 以及后续逐 Servicer 缺口分析文档。

## 目标读者

数据产品经理 · 数据治理团队 · ETL 开发者 · Reviewer · 未来 AI Session

## 修订历史

| 日期 | 作者 | 版本 | 变更说明 | 关联文档 |
|------|------|------|---------|---------|
| 2026-05-28 | AI Agent (Codex) | v1 | 初始版本；确立 MCP 优先、只读验证、SQL 附录和敏感信息处理规则 | doc 13, doc 14, doc 15 |

## 依赖

| 资源 | 用途 |
|------|------|
| `.mcp.json` | 本地 MCP server 配置；已包含 Redshift dev 和 MySQL dev 连接 |
| doc 13 附录 B | 已验证的 Newrez/BPS SQL 样例 |
| doc 15 | 第一个使用该规范的逐 Servicer 缺口文档 |

## 已知限制

- MCP 配置是本地私有开发配置，不应复制到对外文档或共享报告中。
- 本文只规定验证方法；实际行数、填充率、枚举分布会随数据库快照变化。
- 只允许只读验证。任何 `INSERT`、`UPDATE`、`DELETE`、DDL、同步任务触发都不属于本文范围。

---

## 1. 推荐连接方式

**默认使用 MCP 进行数据库验证。**

| 数据库 | MCP server | 主要用途 |
|--------|------------|----------|
| MySQL dev | `mysql_bpms_dev` | 验证 BPS 应用层表、Newrez 原始表、MySQL `port`/`bpms_dev` 表结构和样本数据 |
| Redshift dev | `redshift_dev` | 验证旧系统 ETL 分析层、中间层和 `port.*` 表 |

### 为什么优先 MCP

| 维度 | MCP | Python 直连脚本 |
|------|-----|----------------|
| 审计可读性 | 查询目的和 SQL 更容易直接沉淀到文档 | 容易把结果写入临时文件后丢失上下文 |
| 安全 | 复用本地配置，减少在脚本中硬编码密码 | 旧脚本已有硬编码连接信息，不适合继续扩散 |
| 适用场景 | 字段存在性、填充率、枚举、样本 loan、JOIN 校验 | 大批量导出、复杂统计、本地 JSON/CSV 产物 |

### Python 直连 fallback

仅在以下场景使用 Python 直连：

- MCP 无法完成批量统计或导出。
- 需要生成本地 JSON/CSV 证据文件。
- 需要运行复杂脚本化校验，多条 SQL 结果需要合并处理。

使用 Python fallback 时：

- 不新增硬编码密码脚本。
- 优先使用环境变量或本地私有配置。
- 输出文件必须标注数据源、查询日期、快照日期、SQL 摘要。

---

## 2. 每个结论的证据要求

后续文档中出现“DB 实测”“MCP 验证”“填充率”“字段不存在”“样本验证”等结论时，必须至少记录以下信息：

| 证据字段 | 要求 |
|----------|------|
| 查询目的 | 说明该 SQL 验证什么业务结论 |
| 数据库/Schema/Table | 写清 `schema.table`，跨库 JOIN 时写清两侧来源 |
| 快照条件 | 日报表必须说明 `dataasof` / `fctrdt` / `MAX(date)` 条件 |
| SQL | 只放 `SELECT` 或 metadata 查询 |
| 结果摘要 | 行数、填充率、主要枚举、是否匹配 |
| 限制 | 说明这是某个快照日的结果，不代表永久状态 |

推荐格式：

```sql
-- Purpose: verify <business conclusion>
-- Source: <schema.table>
-- Snapshot: <dataasof/fctrdt condition>
SELECT ...
```

---

## 3. 标准验证场景

### 3.1 字段是否存在

MySQL：

```sql
SELECT table_schema, table_name, column_name, data_type, column_comment
FROM information_schema.columns
WHERE table_schema = '<schema>'
  AND table_name = '<table>'
  AND column_name IN ('<field_1>', '<field_2>')
ORDER BY ordinal_position;
```

Redshift：

```sql
SELECT table_schema, table_name, column_name, data_type
FROM information_schema.columns
WHERE table_schema = '<schema>'
  AND table_name = '<table>'
  AND column_name IN ('<field_1>', '<field_2>')
ORDER BY ordinal_position;
```

### 3.2 字段填充率

```sql
SELECT
  COUNT(*) AS total_rows,
  SUM(<field> IS NOT NULL) AS non_null_rows,
  ROUND(SUM(<field> IS NOT NULL) / COUNT(*) * 100, 1) AS fill_pct
FROM <schema>.<table>
WHERE <snapshot/date/filter condition>;
```

### 3.3 枚举值分布

```sql
SELECT <field>, COUNT(*) AS cnt
FROM <schema>.<table>
WHERE <snapshot/date/filter condition>
GROUP BY <field>
ORDER BY cnt DESC;
```

### 3.4 单笔 loan 端到端追踪

```sql
SELECT *
FROM <source_schema>.<source_table>
WHERE loanid = '<loanid>'
  AND <snapshot/date/filter condition>;
```

然后分别查询：

1. Servicer 原始表。
2. Redshift 中间表。
3. BPS MySQL sync 表。
4. BPS view 或页面对应表。

### 3.5 跨库 JOIN 注意事项

MySQL `bpms_dev` 与 `newrez` JOIN 时，如果出现 collation 错误，应按 doc 13 的做法显式指定 COLLATE：

```sql
ON bps.loanid COLLATE utf8mb4_general_ci = src.loanid COLLATE utf8mb4_general_ci
```

同时必须过滤双方最新快照日，避免 daily snapshot 表仅按 `loanid` JOIN 产生笛卡尔积。

---

## 4. Servicer 文档固定 DB 验证章节

每个逐 Servicer 缺口文档必须包含“数据库验证计划”或“数据库验证证据”章节，至少覆盖：

| 验证类型 | 最低要求 |
|----------|----------|
| Schema 验证 | 核心 FCL/LM/BK 字段是否存在 |
| Fill rate 验证 | P0/P1 关键字段填充率 |
| Enum 验证 | 状态字段的取值分布 |
| Sample loan 验证 | 2-5 笔 loan 从原始表追到 BPS 表 |
| Gap 验证 | 对“未提供/部分提供/内部 ETL 缺口”给出 SQL 或代码证据 |

如果某个文档暂时沿用历史 MCP 结果而没有重新查库，必须在“已知限制”中说明：

> 本文沿用 `<doc>` 在 `<date>` 的 MCP 实测结果；如用于正式外部请求，需在发送前重新运行 SQL 刷新。

---

## 5. 敏感信息处理规则

- 不在业务文档中写数据库密码。
- 不在最终报告中复制 `.mcp.json` 全文。
- 不把连接字符串、账号密码放入 Markdown 附录。
- 可以写 MCP server 名称、schema/table 名称和只读 SQL。
- 如需对团队共享连接方式，应通过公司批准的密钥管理、MCP 配置模板或 IT 文档处理。

---

## 6. 后续执行默认规则

1. 先读代码和现有文档，形成假设。
2. 再用 MCP 只读查询验证字段和数据。
3. 把关键 SQL 写入对应文档附录或验证章节。
4. 把查询结论写成业务语言，而不是只贴查询结果。
5. 对时变结果标注查询日期和快照日期。

