# ForeclosureRule2

[English Version](README.md)

ForeclosureRule2 是一个以文档为核心的逆向分析项目，用来梳理生产环境中的房贷止赎 ETL 系统。这个仓库本身不运行 ETL，而是通过代码优先分析与数据库验证，说明止赎相关数据如何从各 Servicer 原始文件进入 PrefectFlow，再同步到 BPS 报表表。

## 仓库包含什么

- `docs/en/` 与 `docs/zh/` 下的英文、中文分析文档
- `PROJECT_INDEX.md` 中的项目级快速导览
- `outputs/` 下的生成结果、图表和交互式 HTML 浏览器
- `scripts/` 下用于生成或整理文档产物的辅助脚本
- `docs/` 下的配套表格、样例与说明材料

## 最佳入口

- `PROJECT_INDEX.md`：工程师和 AI Agent 的最快全局导览
- `docs/en/00_index.md`：英文文档总索引与阅读顺序
- `docs/zh/00_index.md`：中文文档总索引与阅读顺序
- `docs/zh/20_end_to_end_walkthrough.md`：最推荐的端到端总览入口
- `outputs/fcl_pipeline.html`：交互式 FCL 管道浏览器

## 仓库范围

这个仓库重点覆盖：

- Servicer 原始止赎相关数据
- 从原始接入到 BPS sync 的 5 层 ETL 管道
- delinquency、foreclosure、bankruptcy、loss mitigation 的状态逻辑
- Redshift、MySQL 与下游同步表之间的字段血缘
- Servicer 接口标准与接入分析

这个仓库不包含：

- 被分析的 PrefectFlow 生产 ETL 源码本体
- 生产环境凭据
- BPS 下游应用内部实现逻辑

## 文档结构

- `docs/en/`：英文分析文档
- `docs/zh/`：中文分析文档，以及部分仅中文维护的工作文档
- `docs/archive/`：已归档的历史文档
- `outputs/`：生成图表、JSON 快照和审阅产物

## 推荐阅读路径

- 全局理解：`docs/zh/20_end_to_end_walkthrough.md` -> `docs/zh/02_etl_pipeline.md` -> `docs/zh/18_loss_mitigation_business_primer.md`
- 字段血缘：`docs/zh/25_fcl_lineage_overview.md` -> `docs/zh/26_lineage_sync_loan_foreclosure.md` 到 `docs/zh/30_lineage_sync_loan_foreclosure_bankruptcy.md`
- Servicer 接入：`docs/zh/09_servicer_data_interface_standard.md` -> `docs/zh/14_bps_driven_servicer_fcl_interface.md`
- 验证与对账：`docs/zh/03_fcl_status_logic.md` -> `docs/zh/04_status_inventory.md` -> `docs/zh/31_fcl_stage_window_rules.md`

## 维护说明

- 顶层规则与工作约束见 `CLAUDE.md` 和 `AGENTS.md`。
- 本地连接配置和机器相关文件不要提交。
- 这是一个中英文并行维护的项目；新增导航类文档时，建议同步维护中英文入口。
