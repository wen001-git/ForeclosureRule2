
### 表 20：`newrez.portnewrezbk` — Newrez Bankruptcy 原始日报表

| 属性 | 值 |
|------|----|
| **表名** | `portnewrezbk` |
| **所属 Schema** | MySQL `newrez` |
| **数据层** | Raw / Servicer-specific（Newrez/Shellpoint 原始 BK 日报落地表） |
| **业务作用** | Newrez 破产全流程追踪表，含破产申请/章节/状态、MFR（解除中止动议）、POC（债权申报）、Cramdown、对抗性诉讼、受托人资产、还款计划确认及暂记款余额等子流程节点 |
| **业务意图** | 作为 Newrez BK 原始事实表，识别贷款是否处于破产保护（破产会暂停 FCL），并为 BPS Bankruptcy 面板提供章节/状态/MFR/POC 等业务上下文 |
| **上游来源** | Newrez/Shellpoint `Bankruptcy` / `AresOversight_Bankruptcy` 文件；映射见 `flow/basic_data/load_servicer_data_config/servicer_config.py` |
| **下游使用** | Redshift 中间表（`WHERE LENGTH(TRIM(bkstatus))>0`，按 `loanid+bkfileddate` 去重最新快照）→ `bpms_dev.sync_loan_foreclosure_bankruptcy`（表23，`bkstatus`/`bkstage` 经 `portnewrezdatadic` 解码）；`activebkflag` 驱动主表 `variance_active_bankruptcy`（表17）；见 doc 13 §2.2 / §6 |
| **Foreclosure 关系** | 间接但关键：活跃破产（`activebkflag=1`）触发 FCL Hold/暂停；破产 Dismiss/MFR Granted 后 FCL 通常恢复 |
| **主键 / 索引** | `id` 自增主键；业务 join key 通常为 `loanid + dataasof`；BK 去重常按 `loanid + bkfileddate` |
| **DB验证** | 2026-06-01 MySQL 实测：60列；全表 1,576,896 行；最新快照 `dataasof=2026-05-31` 共 5,052 行。取值范围/填充率取自最新快照（脚本 `scripts/extract_table_stats.py`） |

> ⚠️ `bkstatus`/`bkstage`/`bkremovalcode`/`mfrhearingresults` 等为 **Newrez 内部数值编码**，下游写入 BPS 时经 `newrez.portnewrezdatadic` 解码为文本（见表23 与 doc 13 Q7）。最新快照中仅 32 笔有破产记录（`activebkflag` 等填充约 1%），属正常（多数活跃贷款无破产）。

#### 字段说明（60列）

| 字段名 | 字段业务含义 | 来源数据 | 计算/推导逻辑 | 数据类型 | 取值范围 | 典型取值 | 上游字段 | 下游用途 | 备注 |
|--------|-----------|--------|-----------|----------|---------|---------|--------|--------|------|
| `id` | MySQL 自增主键 | Newrez 系统 | 直接上报 | bigint NOT NULL | 1824745 ~ 1829796 | 1824745 | — | 技术主键 | ✅；填充 5052/5052=100% |
| `loanid` | Bridger/投资人贷款 ID | Newrez 系统 | 直接上报 | varchar(255) | 文本，5052种（样例 0695996231 … 7727006148） | 0695996231 | — | 按 `loanid+dataasof` 关联其他 Newrez 表 | ✅；填充 5052/5052=100% |
| `dataasof` | 数据快照日期 | Newrez 系统 | 直接上报 | date NOT NULL | {2026-05-31} | 2026-05-31 | — | 每日报表日期 | ✅；填充 5052/5052=100% |
| `shellpointloanid` | Newrez/Shellpoint 服务商贷款号 | Newrez 系统 | 直接上报 | varchar(255) | 文本，5052种（样例 0578252925 … 9799754446） | 0578252925 | — | 下游 `svcloanid` | ✅；填充 5052/5052=100% |
| `bkfileddate` | 破产申请日 | Newrez 系统 | 直接上报 | date | {2010-06-03, 2025-04-30, 2024-02-09, 2017-01-18, 2024-01-13, 2008-06-16, 2009-06-01, 2014-12-24, 2026-02-26, 2024-02-01, 2023-11-20, 2022-08-25, 2025-04-18, 2024-03-25, 2026-03-27, 2024-02-06} 等29种 | 2010-06-03 | — | BK 时间线起点 | ✅；填充 32/5052=1% |
| `bkstatus` | 破产状态编码（Newrez 内部数值码） | Newrez 系统 | 直接上报 | int | {2, 1, 3, 5, 4}（5种） | 2 | — | 解码后→ `bankruptcy_status`（表23） | 🟡 数值码，需字典解码；填充 32/5052=1% |
| `bkremovalcode` | 破产终止原因编码（1=Dismissed/2=Discharged 等） | Newrez 系统 | 直接上报 | int | {1, 2, 4, 3}（4种） | 1 | — | 破产结案原因 | 🟡 数值码；填充 20/5052=0% |
| `bkremovaldate` | 破产程序终止日 | Newrez 系统 | 直接上报 | date | {2014-09-24, 2024-06-24, 2022-03-14, 2024-04-11, 2013-08-15, 2009-09-18, 2015-05-08, 2022-09-30, 2026-04-14, 2025-07-29, 2026-03-25, 2023-06-21, 2022-12-30, 2021-06-08, 2023-04-20, 2026-01-08} 等17种 | 2014-09-24 | — | → `variance_completed_bankruptcy` 判定 | ✅；填充 20/5052=0% |
| `bkchapter` | 破产章节（7=清算/11=重组/13=个人还款） | Newrez 系统 | 直接上报 | int | {13, 7, 11}（3种） | 13 | — | → `chapter`（表23） | ✅；填充 32/5052=1% |
| `bkcasenumber` | 破产案件编号 | Newrez 系统 | 直接上报 | varchar(255) | {1033613, 2500228, 2410065, 1701437, 2400439, 881575, 981704, 1482201, 2611401, 2430197, 2331915, 2213209, 2503460, 2421405, 2680351, 2310152} 等29种 | 1033613 | — | 案件追溯 | ✅；填充 32/5052=1% |
| `bkpostpetitionduedate` | 破产申请后贷款应付日 | Newrez 系统 | 直接上报 | date | {2026-05-01, 2026-02-01, 2026-04-01, 2022-04-01, 2024-02-01, 2026-05-06, 2026-07-01, 2022-09-01, 2025-05-01, 2024-04-01, 2023-11-01, 2023-04-01, 2025-12-01, 2025-09-01, 2018-09-01, 2021-04-01} 等18种 | 2026-05-01 | — | → `post_petition_due_date`（表23） | ✅；填充 22/5052=0% |
| `prepetitionduedate` | 破产申请前贷款应付日 | Newrez 系统 | 直接上报 | date | 2022-11-01 ~ 2026-09-01 | 2022-11-01 | — | Pre-petition 欠款基准 | ✅；填充 5052/5052=100% |
| `pocfileddate` | 债权申报（POC）提交日 | Newrez 系统 | 直接上报 | date | {2010-06-17, 2025-08-05, 2022-10-17, 2025-09-22, 2023-11-15, 2023-09-30, 2025-06-27, 2001-01-01, 2024-03-29, 2026-05-04, 2017-03-31, 2024-04-19} | 2010-06-17 | — | → `proof_of_claim_date`（表23） | ✅；填充 13/5052=0% |
| `dischargeddate` | 债务免责（Discharge）日 | Newrez 系统 | 直接上报 | date | {2014-09-24, 2026-01-08, 2021-06-08, 2022-12-30, 2023-06-21, 2025-07-29, 2024-06-24, 2015-04-17, 2009-09-18, 2013-08-15, 2024-04-08, 2022-03-14} | 2014-09-24 | — | BK 完结情形之一 | ✅；填充 15/5052=0% |
| `dismisseddate` | 破产驳回（Dismiss）日 | Newrez 系统 | 直接上报 | date | {2025-12-08, 2026-04-14, 2022-09-30} | 2025-12-08 | — | BK 完结情形之一；驳回后 FCL 可恢复 | ✅；填充 3/5052=0% |
| `mfrfileddate` | 解除自动中止动议（MFR）提交日 | Newrez 系统 | 直接上报 | date | {2025-11-04, 2025-11-21, 2026-04-29, 2026-02-04, 2025-06-10} | 2025-11-04 | — | → `mfr_filed_date`（表23） | ✅；填充 5/5052=0% |
| `mfrhearingdate` | MFR 听证日 | Newrez 系统 | 直接上报 | date | {2025-12-02, 2026-05-15, 2026-03-09, 2025-06-24} | 2025-12-02 | — | MFR 子流程 | ✅；填充 4/5052=0% |
| `mfrgranteddate` | MFR 批准日（批准后可推进 FCL） | Newrez 系统 | 直接上报 | date | {2025-12-05, 2026-03-11, 2025-06-25} | 2025-12-05 | — | MFR 子流程 | ✅；填充 3/5052=0% |
| `trusteeassetflag` | 受托人资产标志（1=有可分配资产） | Newrez 系统 | 直接上报 | int | {0, 1}（2种） | 0 | — | Ch7 资产案件标识 | ✅；填充 32/5052=1% |
| `trusteeassetdate` | 受托人资产认定日 | Newrez 系统 | 直接上报 | date | {2025-11-09, 2023-04-19, 2024-04-16, 2025-06-01, 2024-02-22} | 2025-11-09 | — | Ch7 子流程 | ✅；填充 5/5052=0% |
| `planconfirmationdate` | 还款计划确认日（Ch13 Plan Confirmed） | Newrez 系统 | 直接上报 | date | {2014-03-24, 2023-04-20, 2024-08-15, 2024-07-11, 2024-02-23, 2024-05-07, 2017-03-20, 2024-06-25} | 2014-03-24 | — | Ch13 子流程 | ✅；填充 11/5052=0% |
| `bkstage` | 破产阶段编码（Newrez 内部数值码） | Newrez 系统 | 直接上报 | int | {8, 0, 4, 10, 21, 7, 17}（7种） | 8 | — | 解码后→ `legal_status`（表23） | 🟡 数值码，需字典解码；填充 32/5052=1% |
| `bkfirm` | 破产律师事务所名称 | Newrez 系统 | 直接上报 | varchar(255) | {Padgett Law Group, Aldridge Pite, LLP, Bonial & Associates, P.C., McCalla Raymer Leibert Pierce, LLP, Hill Wallack} | Padgett Law Group | — | 律所信息 | ✅；填充 12/5052=0% |
| `reaffirmationdate` | 重申债务确认（Reaffirmation）日 | Newrez 系统 | 直接上报 | date | {2015-01-14} | 2015-01-14 | — | Ch7 重申子流程 | ✅；填充 1/5052=0% |
| `trusteeabandonmentdate` | 受托人放弃资产日 | Newrez 系统 | 直接上报 | date | 实测全为 NULL | — | — | Ch7 子流程 | ✅；填充 0/5052=0% |
| `pocreferreddate` | POC 转介日 | Newrez 系统 | 直接上报 | date | {2025-07-07, 2025-06-06, 2025-07-17, 2026-05-26, 2026-05-21, 2025-06-04, 2026-04-03, 2024-02-13} | 2025-07-07 | — | POC 子流程 | ✅；填充 8/5052=0% |
| `pocbardate` | POC 申报截止日（Bar Date） | Newrez 系统 | 直接上报 | date | {2010-10-21, 2024-04-16, 2024-04-19, 2017-05-24, 2026-05-07, 2024-04-11, 2024-01-29, 2025-06-27, 2026-06-05, 2024-05-28, 2023-07-24, 2026-06-10, 2024-01-02, 2025-09-22, 2022-10-27, 2025-08-05} | 2010-10-21 | — | POC 截止节点 | ✅；填充 19/5052=0% |
| `mfrreferred` | MFR 转介日 | Newrez 系统 | 直接上报 | date | {2025-10-21, 2025-10-24, 2026-04-08, 2026-01-07, 2025-11-10, 2025-05-15} | 2025-10-21 | — | MFR 子流程 | ✅；填充 6/5052=0% |
| `mfrhearingresults` | MFR 听证结果编码 | Newrez 系统 | 直接上报 | int | {0, 3, 4, 5}（4种） | 0 | — | 解码后→ `mfr_status`（表23） | 🟡 数值码；填充 32/5052=1% |
| `cramdowndatereferred` | Cramdown 转介日 | Newrez 系统 | 直接上报 | date | 实测全为 NULL | — | — | Cramdown 子流程 | ✅；填充 0/5052=0% |
| `cramdownobjectionfileddate` | Cramdown 异议提交日 | Newrez 系统 | 直接上报 | date | 实测全为 NULL | — | — | Cramdown 子流程 | ✅；填充 0/5052=0% |
| `cramdownresultdate` | Cramdown 结果日 | Newrez 系统 | 直接上报 | date | 实测全为 NULL | — | — | Cramdown 子流程 | ✅；填充 0/5052=0% |
| `cramdownhearingresults` | Cramdown 听证结果编码 | Newrez 系统 | 直接上报 | int | {0}（1种） | 0 | — | Cramdown 结果 | 🟡 数值码；填充 32/5052=1% |
| `adversarialactionfileddate` | 对抗性诉讼（Adversary）提交日 | Newrez 系统 | 直接上报 | date | 实测全为 NULL | — | — | Adversary 子流程 | ✅；填充 0/5052=0% |
| `adversarialhearingdate` | 对抗性诉讼听证日 | Newrez 系统 | 直接上报 | date | 实测全为 NULL | — | — | Adversary 子流程 | ✅；填充 0/5052=0% |
| `adversarialresultdate` | 对抗性诉讼结果日 | Newrez 系统 | 直接上报 | date | 实测全为 NULL | — | — | Adversary 子流程 | ✅；填充 0/5052=0% |
| `adversarialresults` | 对抗性诉讼结果编码 | Newrez 系统 | 直接上报 | int | {0}（1种） | 0 | — | Adversary 结果 | 🟡 数值码；填充 32/5052=1% |
| `cramdownflag` | Cramdown 标志（1=存在 cramdown） | Newrez 系统 | 直接上报 | int | {0}（1种） | 0 | — | 本金 cramdown 标识 | ✅；填充 32/5052=1% |
| `bankruptcypaymenttype` | 破产还款类型编码 | Newrez 系统 | 直接上报 | int | {1, 2, 0}（3种） | 1 | — | 还款类型细分 | 🟡 数值码；填充 12/5052=0% |
| `debtorintention` | 债务人意向编码（保留/放弃房产） | Newrez 系统 | 直接上报 | int | {1, 0}（2种） | 1 | — | 债务人意向 | 🟡 数值码；填充 12/5052=0% |
| `jointfilerflag` | 是否共同申请人（1=joint） | Newrez 系统 | 直接上报 | int | {0, 1}（2种） | 0 | — | 共同申请标识 | ✅；填充 12/5052=0% |
| `activebkflag` | 是否在破产保护中（1=是/0=否） | Newrez 系统 | 直接上报 | int | {0, 1}（2种） | 0 | — | → `variance_active_bankruptcy`；BK 活跃判定 | ✅；填充 5052/5052=100% |
| `apocfileddate` | 修订债权申报（APOC）提交日 | Newrez 系统 | 直接上报 | date | {2025-09-23, 2025-08-05} | 2025-09-23 | — | APOC 子流程 | ✅；填充 2/5052=0% |
| `apocreferraldate` | APOC 转介日 | Newrez 系统 | 直接上报 | date | {2025-09-23, 2025-08-29} | 2025-09-23 | — | APOC 子流程 | ✅；填充 2/5052=0% |
| `reasonforapoc` | APOC 原因（文本） | Newrez 系统 | 直接上报 | varchar(255) | {Error with Claim} | Error with Claim | — | APOC 原因说明 | ✅；填充 2/5052=0% |
| `attorney` | 受理律师/律所名称 | Newrez 系统 | 直接上报 | varchar(255) | {Aldridge Pite, LLP} | Aldridge Pite, LLP | — | 律师信息（APOC 相关） | ✅；填充 2/5052=0% |
| `create_time` | 记录创建时间 | Newrez 系统 | 直接上报 | datetime | {2026-06-01 21:37:44} | 2026-06-01 21:37:44 | — | MySQL 管理字段（实测=落库时间） | ✅；填充 5052/5052=100% |
| `update_time` | 记录更新时间 | Newrez 系统 | 直接上报 | datetime | {2026-06-01 21:37:44} | 2026-06-01 21:37:44 | — | MySQL 管理字段 | ✅；填充 5052/5052=100% |
| `bkrepayplanpaymentcount` | 破产还款计划期数 | Newrez 系统 | 直接上报 | int | {0, 60, 36}（3种） | 0 | — | Ch13 计划期数 | ✅；填充 12/5052=0% |
| `bksourceoffundscode` | 资金来源编码 | Newrez 系统 | 直接上报 | int | 实测全为 NULL | — | — | 还款资金来源 | 🟡 数值码；填充 0/5052=0% |
| `bkpoccourtreceiveddate` | POC 法院收到日 | Newrez 系统 | 直接上报 | date | {2025-09-22, 2026-05-04, 2024-04-19} | 2025-09-22 | — | POC 子流程 | ✅；填充 3/5052=0% |
| `bkrcurrentstatusdate` | 当前破产状态生效日期 | Newrez 系统 | 直接上报 | date | {2026-04-27, 2026-04-15, 2025-07-12, 2023-10-24, 2026-04-01, 2026-04-08, 2026-05-26, 2026-03-27, 2023-11-20, 2024-02-01, 2026-02-26, 2024-02-09} | 2026-04-27 | — | → `status_date`（表23） | ✅；填充 12/5052=0% |
| `bkborrowerintent` | 借款人破产意向编码 | Newrez 系统 | 直接上报 | int | {1, 0}（2种） | 1 | — | 借款人意向 | 🟡 数值码；填充 12/5052=0% |
| `bkpostpetitionpaymentcurrent` | 破产后应付款当前额 | Newrez 系统 | 直接上报 | decimal(32,16) | {0, 1805.15, 2437.01, 2192, 1232.3, 805.5, 4103.99, 1427.01}（8种） | $0 | — | Post-petition 还款监控 | ✅；填充 12/5052=0% |
| `bkcramdownpercent` | Cramdown 比例（本金削减%） | Newrez 系统 | 直接上报 | decimal(32,16) | 实测全为 NULL | — | — | Cramdown 金额计算 | ✅；填充 0/5052=0% |
| `bkpostsuspensebalance` | 破产后暂记款（suspense）余额 | Newrez 系统 | 直接上报 | decimal(32,16) | {0}（1种） | $0 | — | 暂记款监控 | ✅；填充 8/5052=0% |
| `bkpresuspensebalance` | 破产前暂记款余额 | Newrez 系统 | 直接上报 | decimal(32,16) | {0}（1种） | $0 | — | 暂记款监控 | ✅；填充 7/5052=0% |
| `investorloanid` | 投资人贷款号 | Newrez 系统 | 直接上报 | varchar(100) | 文本，5051种（样例 1000006548 … 958710） | 1000006548 | — | 投资人对账 ID | ✅；填充 5052/5052=100% |
| `bkfilingstate` | 破产申请州 | Newrez 系统 | 直接上报 | varchar(255) | {OH, IL, FL, CA, TX, AZ, RI, CO, TN, NE, WV, MN, GA, NV, MD, PA} | OH | — | 管辖州 | ✅；填充 32/5052=1% |
| `bkfilingregion` | 破产申请法院辖区（含 Division） | Newrez 系统 | 直接上报 | varchar(255) | {Southern District Of Ohio, Dayton, Central District of Illinois, Peoria Division, (None), Southern District of Ohio, Dayton Division   , Northern District of Illinois, Eastern Division, Eastern District of California, Sacramento Division, District of Rhode Island (Providence), Northern District Of Illinois, Chicago Division, Central District Of California, Riverside Division, Mian District Of Colorado, Denver Division, Main District of Arizona, Phoenix Division, District of Nebraska, Omaha Division                                , Northern District of WV (Martinsburg), Northern District of Florida, Gainesville Division                    , District Of Arizona, Phoenix Division, District of Minnesota, St. Paul Division} 等23种 | Southern District Of Ohio, Dayton | — | 联邦破产法院辖区 | ✅；填充 32/5052=1% |

---

### 表 21：`bpms_dev.sync_loan_foreclosure_hold` — BPS Hold 历史记录表

| 属性 | 值 |
|------|----|
| **表名** | `sync_loan_foreclosure_hold` |
| **所属 Schema** | MySQL `bpms_dev`（BPS 应用数据库） |
| **数据层** | Layer 5 — BPS Application Layer |
| **业务作用** | 贷款 FCL 生命周期内的**完整 Hold 历史**（每次 Hold 变更追加一行），驱动 BPS Loan Foreclosure 详情页 Hold 面板 |
| **业务意图** | Newrez `portnewrezfc` 仅保留 3 个当前 Hold 槽位（fchold1/2/3）；BPS 每日同步将每次变更落为新行，从而累积完整 Hold 历史（单贷款可远多于 3 行） |
| **上游来源** | Redshift `port.basic_data_loan_foreclosure_hold`（源 `portnewrezfc`，`WHERE fchold1startdate IS NOT NULL`，3 槽 UNPIVOT，按 `loanid,description,start_date` 去重）→ `JOIN port.portfunding`；DELETE+INSERT 全量重写（见 doc 13 §4） |
| **下游使用** | BPS Hold 面板（Description/Start/End）；入库链路与主 FCL 表独立（不要求 `fcreferraldate IS NOT NULL`） |
| **Foreclosure 关系** | 直接：Hold（BK/LM/Court Delay 等）暂停 FCL 计时，是 SLA 方差分析的事件来源 |
| **主键 / 索引** | `id` 自增主键；业务键 `loanid + description + description_start_date` |
| **DB验证** | 2026-06-01 实测：15列；338 行（85 个 distinct svcloanid）；`description` 40 种文本（如 `Loss Mitigation Workout` / `Court Delay`）；脚本 `scripts/extract_table_stats.py` |

> 说明：本表**不存储 Hold 预计结束日**；主表 `sync_loan_foreclosure.variance_estimated_hold_days` 的 projected 来源是 `portnewrezfc` 的 `fchold*projectedenddate`（见表17 与 doc 13 §4.4）。

#### 字段说明（15列）

| 字段名 | 字段业务含义 | 来源数据 | 计算/推导逻辑 | 数据类型 | 取值范围 | 典型取值 | 上游字段 | 下游用途 | 备注 |
|--------|-----------|--------|-----------|----------|---------|---------|--------|--------|------|
| `id` | 自增主键 | BPS ETL | AUTO_INCREMENT | bigint NOT NULL | 10842 ~ 11540 | 10842 | — | 技术主键 | ✅；填充 338/338=100% |
| `loanid` | 系统贷款 ID | BPS ETL | 直接写入 | bigint | 7727000012 ~ 700082870000041 | 7727000012 | `port.basic_data_loan_fcl.loanid` | 贷款 join key | ✅；填充 338/338=100% |
| `svcloanid` | Servicer 内部贷款号 | BPS ETL | 直接写入 | varchar(64) | 文本，85种（样例 0578252925 … 7000329258） | 0578252925 | — | Servicer 对账 | ✅；填充 338/338=100% |
| `fctrdt` | 数据来源批次日期 | BPS ETL | 直接写入 | date | 2023-12-17 ~ 2026-03-13 | 2023-12-17 | — | 快照批次追踪 | ✅；填充 338/338=100% |
| `description` | Hold 原因描述（文本） | BPS ETL | 源 fchold1/2/3description（UNPIVOT） | varchar(256) | 文本，40种（样例 ACT(PA) Letter/Demand Letter/NOI Expiration … Veterans Affairs Servicing Purchase (VASP)） | ACT(PA) Letter/Demand Letter/NOI Expiration | `newrez.portnewrezfc.fchold*description` | BPS Hold 面板 Description 列 | ✅；填充 297/338=88% |
| `description_start_date` | Hold 开始日 | BPS ETL | 源 fchold1/2/3startdate | date | 2019-10-24 ~ 2026-03-13 | 2019-10-24 | `newrez.portnewrezfc.fchold*startdate` | Hold 面板 Start Date | ✅；填充 338/338=100% |
| `description_end_date` | Hold 结束日（NULL=仍持续） | BPS ETL | 源 fchold1/2/3enddate | date | 2019-11-15 ~ 2026-03-12 | 2019-11-15 | `newrez.portnewrezfc.fchold*enddate` | Hold 面板 End Date | ✅；填充 316/338=93% |
| `create_user` | 记录创建用户 | BPS 应用层 | 直接写入 | bigint | 实测全为 NULL | — | — | 审计追踪 | dev 未回填；填充 0/338=0% |
| `create_dept` | 记录创建部门 | BPS 应用层 | 直接写入 | bigint | 实测全为 NULL | — | — | 审计追踪 | dev 未回填；填充 0/338=0% |
| `create_time` | 记录创建时间 | BPS 应用层 | 直接写入 | datetime | 实测全为 NULL | — | — | 审计追踪 | dev 未回填；填充 0/338=0% |
| `update_user` | 最后更新用户 | BPS 应用层 | 直接写入 | bigint | 实测全为 NULL | — | — | 审计追踪 | dev 未回填；填充 0/338=0% |
| `update_time` | 最后更新时间 | BPS 应用层 | 直接写入 | datetime | 实测全为 NULL | — | — | 审计追踪 | dev 未回填；填充 0/338=0% |
| `status` | 记录状态（0=正常） | BPS 应用层 | DEFAULT 0 | int NOT NULL | {0}（1种） | 0 | — | 软停用标志 | ✅；填充 338/338=100% |
| `is_deleted` | 是否软删除（0=未删） | BPS 应用层 | DEFAULT 0 | int NOT NULL | {0}（1种） | 0 | — | 软删除标志 | ✅；填充 338/338=100% |
| `tenant_id` | 租户 ID | BPS 应用层 | 直接写入 | varchar(12) NOT NULL | {000000, 984018} | 000000 | — | 多租户支持 | ✅；填充 338/338=100% |

---

### 表 22：`bpms_dev.sync_loan_foreclosure_loss_mitigation` — BPS Loss Mitigation 周期表

| 属性 | 值 |
|------|----|
| **表名** | `sync_loan_foreclosure_loss_mitigation` |
| **所属 Schema** | MySQL `bpms_dev` |
| **数据层** | Layer 5 — BPS Application Layer |
| **业务作用** | 贷款完整 Loss Mitigation 周期历史（每个 LM 周期一行），驱动 BPS LM Cycle 面板 |
| **业务意图** | 追踪每轮 workout（Evaluation→Modification/Forbearance/Short Sale/DIL）的开/关、方案与最终处置；LM 失败通常转回 FCL，成功则暂停/终止 FCL |
| **上游来源** | Redshift（源 `newrez.portnewrezlm`，`WHERE dealstartdate IS NOT NULL`，按 `loanid,dealstartdate` 去重；6 个整型编码经 `portnewrezdatadic` 解码）→ `JOIN port.portfunding`；合并 Newrez+Carrington+Capecodfive（见 doc 13 §5） |
| **下游使用** | BPS LM Cycle 面板（Deal/Program/Status/Cycle Dates/Final Disposition 等 10 列）；编码↔文本解码对照见表19「LM 编码解码参考」 |
| **Foreclosure 关系** | 直接：LM 周期影响 FCL Hold/恢复；`final_disposition` 决定 FCL 是否继续 |
| **主键 / 索引** | `id` 自增主键；业务键 `loanid + deal + cycle_opened_date` |
| **DB验证** | 2026-06-01 实测：22列；544 行（250 个 distinct svcloanid）；`deal`/`program`/`lmc_status`/`final_disposition` 填充约 87%；脚本 `scripts/extract_table_stats.py` |

> ⚠️ 本表存储**解码后业务文本**（与 Hold 表直接存文本不同；编码解码在 Redshift 层完成）。实测部分值仍为未解码数字（如 `deal='2.0'`、`lmc_status='166.0'`），属 ETL 字典缺失项，应以表19 解码参考为准。

#### 字段说明（22列）

| 字段名 | 字段业务含义 | 来源数据 | 计算/推导逻辑 | 数据类型 | 取值范围 | 典型取值 | 上游字段 | 下游用途 | 备注 |
|--------|-----------|--------|-----------|----------|---------|---------|--------|--------|------|
| `id` | 自增主键 | BPS ETL | AUTO_INCREMENT | bigint NOT NULL | 25061 ~ 26155 | 25061 | — | 技术主键 | ✅；填充 544/544=100% |
| `loanid` | 系统贷款 ID | BPS ETL | 直接写入 | bigint | 7727000010 ~ 700082890000291 | 7727000010 | `newrez.portnewrezlm.loanid` | 贷款 join key | ✅；填充 544/544=100% |
| `svcloanid` | Servicer 内部贷款号 | BPS ETL | 直接写入 | varchar(64) | 文本，250种（样例 0578252925 … 7000359729） | 0578252925 | — | Servicer 对账 | ✅；填充 544/544=100% |
| `fctrdt` | 数据来源批次日期 | BPS ETL | 直接写入 | date | 2023-11-15 ~ 2026-03-13 | 2023-11-15 | — | 快照批次追踪 | ✅；填充 544/544=100% |
| `deal` | LM 大类（解码文本） | BPS ETL | lmdeal(int) 经 portnewrezdatadic 解码 | varchar(256) | {Modification, Evaluation, Forbearance, Deferment, Payment Plan, 2.0, DIL, Short Sale, 4.0, 1.0, Payoff} | Modification | `newrez.portnewrezlm.lmdeal` | LM Cycle 面板 Deal 列 | ✅ 解码存储（如 7→DIL）；填充 475/544=87% |
| `program` | LM 具体方案（解码文本） | BPS ETL | lmprogram(int) 解码 | varchar(256) | {Evaluation, Deferment, 496.0, Short-term Forbearance, Bridger mod, Repayment Plan, VA Traditional, SLS Standard Mod, FHA Recovery SAPC, 498.0, 21.0, Deed-in-Lieu, Standard Proprietary Modification, Short Sale, VASP No Trial, Unemployment Forbearance} 等30种 | Evaluation | `newrez.portnewrezlm.lmprogram` | LM Cycle 面板 Program 列 | ✅ 解码存储（如 10→Deed-in-Lieu）；填充 475/544=87% |
| `lmc_status` | LM 当前状态（解码文本） | BPS ETL | lmstatus(int) 解码 | varchar(256) | {Workout Denial, Pending Financials , Document Follow-up, Monitor Forbearance, Book mod, Deferment Agreement Ordered, 166.0, Deferment Plan In Progress, Monitor for pmts/funds, Liquidation Referral, Follow up for 1st Trial Payment, Solicitation Offered, 5.0, Monitor for Mod Agreement, Follow up for 2nd Trial Payment, 112.0} 等26种 | Workout Denial | `newrez.portnewrezlm.lmstatus` | LM Cycle 面板 Status 列 | ✅ 解码（如 166→Pending Financials）；填充 475/544=87% |
| `cycle_opened_date` | LM 周期开始日 | BPS ETL | 直接映射 dealstartdate | date | 2020-08-17 ~ 2026-03-12 | 2020-08-17 | `newrez.portnewrezlm.dealstartdate` | LM 周期唯一键之一 | ✅；填充 543/544=100% |
| `cycle_closed_date` | LM 周期结束日（NULL=进行中） | BPS ETL | 直接映射 lmremovaldate | date | 2020-09-22 ~ 2026-03-12 | 2020-09-22 | `newrez.portnewrezlm.lmremovaldate` | 周期历时计算 | ✅；填充 489/544=90% |
| `final_disposition` | 最终处置结论（解码文本） | BPS ETL | lmdecision(int) 解码 | varchar(256) | {Referral to FC, Request Incomplete/Failed to Provide Information, Pending, LMS Opened in Error, Reinstated/Current, Deferment Completed, Forbearance Complete, Modification Complete, Not Eligible for Loss Mitigation, Full Pay Off, 10.0, 11.0, 99.0, FC Sale Held, 5.0, 6.0} 等18种 | Referral to FC | `newrez.portnewrezlm.lmdecision` | 决定 FCL 是否恢复（如 Referral to FC） | ✅ 解码存储；填充 475/544=87% |
| `denialreason` | 拒绝原因（解码文本，无则空串） | BPS ETL | denialreason(int) 解码 | varchar(256) | {, Loan not due for 3 or more monthly payments, Request Incomplete/Failed to Provide Documentation, HAMP Sunset, Withdrawal of Request/Non-Acceptance, Unable to achieve target payment, Hardship not resolved, Investor Not Participating, Failed Plan, Loan not 90+ DPD , Post-Mod P&I Payment > Current P&I Payment, Trial Plan Default, HDTI out of range, Request Withdrawn, Default Not Imminent, Ineligible Borrower: Not a Natural Person} 等28种 |  | `newrez.portnewrezlm.denialreason` | LM 拒绝原因 | ✅ 无拒绝=空字符串；填充 475/544=87% |
| `borrower_intentions` | 借款人意向（解码文本） | BPS ETL | borrowerintention(int) 解码 | varchar(256) | {, Retention, Disposition, Unknown} |  | `newrez.portnewrezlm.borrowerintention` | 借款人意向 | ✅ Newrez 多为空；填充 475/544=87% |
| `imminent_default` | 即将违约标识（CFPB Reg X） | BPS ETL | Newrez 无对应字段 | varchar(256) | 实测全为 NULL | — | — | LM Cycle 面板列 | ✅ Newrez 恒 NULL（doc 13 Q6）；填充 0/544=0% |
| `single_point_of_contact` | 专属联系人（CFPB 12 CFR 1024.40） | BPS ETL | Newrez 无对应字段 | varchar(256) | 实测全为 NULL | — | — | LM Cycle 面板列 | ✅ Newrez 恒 NULL（doc 13 Q6）；填充 0/544=0% |
| `create_user` | 记录创建用户 | BPS 应用层 | 直接写入 | bigint | 实测全为 NULL | — | — | 审计追踪 | dev 未回填；填充 0/544=0% |
| `create_dept` | 记录创建部门 | BPS 应用层 | 直接写入 | bigint | 实测全为 NULL | — | — | 审计追踪 | dev 未回填；填充 0/544=0% |
| `create_time` | 记录创建时间 | BPS 应用层 | 直接写入 | datetime | 实测全为 NULL | — | — | 审计追踪 | dev 未回填；填充 0/544=0% |
| `update_user` | 最后更新用户 | BPS 应用层 | 直接写入 | bigint | 实测全为 NULL | — | — | 审计追踪 | dev 未回填；填充 0/544=0% |
| `update_time` | 最后更新时间 | BPS 应用层 | 直接写入 | datetime | 实测全为 NULL | — | — | 审计追踪 | dev 未回填；填充 0/544=0% |
| `status` | 记录状态（0=正常） | BPS 应用层 | DEFAULT 0 | int NOT NULL | {0}（1种） | 0 | — | 软停用标志 | ✅；填充 544/544=100% |
| `is_deleted` | 是否软删除（0=未删） | BPS 应用层 | DEFAULT 0 | int NOT NULL | {0}（1种） | 0 | — | 软删除标志 | ✅；填充 544/544=100% |
| `tenant_id` | 租户 ID | BPS 应用层 | 直接写入 | varchar(12) NOT NULL | {000000, 984018} | 000000 | — | 多租户支持 | ✅；填充 544/544=100% |

---

### 表 23：`bpms_dev.sync_loan_foreclosure_bankruptcy` — BPS Bankruptcy 记录表

| 属性 | 值 |
|------|----|
| **表名** | `sync_loan_foreclosure_bankruptcy` |
| **所属 Schema** | MySQL `bpms_dev` |
| **数据层** | Layer 5 — BPS Application Layer |
| **业务作用** | 贷款破产申请记录，驱动 BPS Bankruptcy 面板（仅有破产记录的贷款才有行） |
| **业务意图** | 向资产经理展示破产章节/状态/MFR/POC 等关键节点；破产保护期间 FCL 暂停 |
| **上游来源** | Redshift（源 `newrez.portnewrezbk`，`WHERE LENGTH(TRIM(bkstatus))>0`，按 `loanid,bkfileddate` 去重；`LEFT JOIN portnewrezgeneral` 取 legalstatus、`portnewrezdatadic` 解码 bkstatus）→ `JOIN port.portfunding`；合并 Newrez+Carrington+Capecodfive（见 doc 13 §6） |
| **下游使用** | BPS Bankruptcy 面板（Status/Legal Status/Chapter/MFR/POC 等 10 列） |
| **Foreclosure 关系** | 直接：上游 `activebkflag`/`bkremovaldate` 还驱动主表 `variance_active_bankruptcy`/`variance_completed_bankruptcy`（表17） |
| **主键 / 索引** | `id` 自增主键；业务键 `loanid + bkfileddate` |
| **DB验证** | 2026-06-01 实测：22列；64 行（59 个 distinct svcloanid）；`bankruptcy_status`/`chapter` 100% 填充，`legal_status` 48%；脚本 `scripts/extract_table_stats.py` |

> ⚠️ `bankruptcy_status`/`legal_status` 实测多为已解码文本（Active/Discharged/Dismissed、BK13/BK7/REO 等），但仍混有少量未解码数字（如 `3.0`），属字典缺失项（doc 13 Q7）。`lien_status`/`mfr_status`/`claim_status` dev 全为 NULL，源字段待确认。

#### 字段说明（22列）

| 字段名 | 字段业务含义 | 来源数据 | 计算/推导逻辑 | 数据类型 | 取值范围 | 典型取值 | 上游字段 | 下游用途 | 备注 |
|--------|-----------|--------|-----------|----------|---------|---------|--------|--------|------|
| `id` | 自增主键 | BPS ETL | AUTO_INCREMENT | bigint NOT NULL | 2611 ~ 2739 | 2611 | — | 技术主键 | ✅；填充 64/64=100% |
| `loanid` | 系统贷款 ID | BPS ETL | 直接写入 | bigint | 7727000010 ~ 700082700000050 | 7727000010 | `newrez.portnewrezbk.loanid` | 贷款 join key | ✅；填充 64/64=100% |
| `svcloanid` | Servicer 内部贷款号 | BPS ETL | 直接写入 | varchar(64) | 文本，59种（样例 0578707313 … 7000357268） | 0578707313 | — | Servicer 对账 | ✅；填充 64/64=100% |
| `fctrdt` | 数据来源批次日期 | BPS ETL | 直接写入 | date | {2026-03-10, 2026-03-13, 2026-01-17, 2024-07-24, 2024-09-29, 2025-07-14, 2024-09-05, 2024-11-18, 2026-03-01} | 2026-03-10 | — | 快照批次追踪 | ✅；填充 64/64=100% |
| `bankruptcy_status` | 破产状态（解码文本） | BPS ETL | bkstatus(int) 经 portnewrezdatadic 解码 | varchar(256) | {Completed/Cancelled, Discharged, Active, Dismissed, 3.0, ReliefGranted, Closed} | Completed/Cancelled | `newrez.portnewrezbk.bkstatus` | BK 面板 Status 列 | ✅ 解码存储；填充 64/64=100% |
| `legal_status` | 法律程序状态（解码文本） | BPS ETL | bkstage(int) 解码 | varchar(256) | {BK13, , FCBU, BK11, BK11DCH, BK7, BK7DCH, REO, BKD13LM, BKD7LM, BK13DCH, FCSold} | BK13 | `newrez.portnewrezbk.bkstage` | BK 面板 Legal Status 列 | ✅ 解码（如 BK13/FCBU/REO）；填充 31/64=48% |
| `status_date` | 当前状态生效日期 | BPS ETL | 直接映射 bkrcurrentstatusdate | date | 2003-11-14 ~ 2026-02-26 | 2003-11-14 | `newrez.portnewrezbk.bkrcurrentstatusdate` | BK 面板 Status Date | ✅；填充 62/64=97% |
| `chapter` | 破产章节（7/11/13） | BPS ETL | 直接映射 bkchapter | varchar(256) | {13, 7, 11} | 13 | `newrez.portnewrezbk.bkchapter` | BK 面板 Chapter | ✅；填充 64/64=100% |
| `lien_status` | 留置权状态 | BPS ETL | 源待确认 | varchar(256) | 实测全为 NULL | — | `newrez.portnewrezbk.*` | BK 面板 Lien Status | 🟡 来源待确认；dev 全 NULL；填充 0/64=0% |
| `mfr_status` | MFR 状态（解码文本） | BPS ETL | mfrhearingresults(int) 解码 | varchar(256) | 实测全为 NULL | — | `newrez.portnewrezbk.mfrhearingresults` | BK 面板 MFR Status | 🟡 dev 全 NULL；填充 0/64=0% |
| `mfr_filed_date` | MFR 提交日 | BPS ETL | 直接映射 mfrfileddate | date | {2022-03-18, 2020-10-19, 2026-03-04} | 2022-03-18 | `newrez.portnewrezbk.mfrfileddate` | BK 面板 MFR Filed Date | ✅；填充 3/64=5% |
| `claim_status` | 债权状态 | BPS ETL | 源待确认 | varchar(256) | 实测全为 NULL | — | `newrez.portnewrezbk.*` | BK 面板 Claim Status | 🟡 来源待确认；dev 全 NULL；填充 0/64=0% |
| `proof_of_claim_date` | 债权申报（POC）日 | BPS ETL | 直接映射 pocfileddate | date | {2023-09-30, 2010-06-17, 2001-01-01, 2025-08-05, 2024-03-29, 2025-12-16, 2022-10-17, 2017-03-31, 2024-04-19, 2026-01-26, 2018-04-12, 2016-04-26, 2013-06-13, 2020-02-13, 2024-12-17, 2016-02-15} 等22种 | 2023-09-30 | `newrez.portnewrezbk.pocfileddate` | BK 面板 Proof of Claim Date | ✅；填充 24/64=38% |
| `post_petition_due_date` | 破产申请后应付日 | BPS ETL | 直接映射 bkpostpetitionduedate | date | {2026-01-01, 2026-02-01, 2025-06-01, 2026-04-01, 2026-03-06, 2024-02-01, 2026-03-01, 2021-04-01, 2025-11-01, 2025-02-01, 2022-04-01, 2018-09-01, 2025-09-01, 2025-10-01, 2025-05-01, 2022-09-01} 等20种 | 2026-01-01 | `newrez.portnewrezbk.bkpostpetitionduedate` | BK 面板 Post Petition Due Date | ✅；填充 22/64=34% |
| `create_user` | 记录创建用户 | BPS 应用层 | 直接写入 | bigint | 实测全为 NULL | — | — | 审计追踪 | dev 未回填；填充 0/64=0% |
| `create_dept` | 记录创建部门 | BPS 应用层 | 直接写入 | bigint | 实测全为 NULL | — | — | 审计追踪 | dev 未回填；填充 0/64=0% |
| `create_time` | 记录创建时间 | BPS 应用层 | 直接写入 | datetime | 实测全为 NULL | — | — | 审计追踪 | dev 未回填；填充 0/64=0% |
| `update_user` | 最后更新用户 | BPS 应用层 | 直接写入 | bigint | 实测全为 NULL | — | — | 审计追踪 | dev 未回填；填充 0/64=0% |
| `update_time` | 最后更新时间 | BPS 应用层 | 直接写入 | datetime | 实测全为 NULL | — | — | 审计追踪 | dev 未回填；填充 0/64=0% |
| `status` | 记录状态（0=正常） | BPS 应用层 | DEFAULT 0 | int NOT NULL | {0}（1种） | 0 | — | 软停用标志 | ✅；填充 64/64=100% |
| `is_deleted` | 是否软删除（0=未删） | BPS 应用层 | DEFAULT 0 | int NOT NULL | {0}（1种） | 0 | — | 软删除标志 | ✅；填充 64/64=100% |
| `tenant_id` | 租户 ID | BPS 应用层 | 直接写入 | varchar(12) NOT NULL | {000000, 984018} | 000000 | — | 多租户支持 | ✅；填充 64/64=100% |

---

### 表 24：`bpms_dev.sync_fcl_stage_info` — BPS FCL 阶段统计表

| 属性 | 值 |
|------|----|
| **表名** | `sync_fcl_stage_info` |
| **所属 Schema** | MySQL `bpms_dev` |
| **数据层** | Layer 5 — BPS Application Layer（聚合概览页数据源） |
| **业务作用** | 驱动 BPS Foreclosure 聚合概览页（Stage Tab + Time Line Tab）：按当前阶段分组的 Days in Stage / Days in LM / Days on Hold 统计，及各里程碑日期时间线 |
| **业务意图** | 为资产经理提供组合级 FCL 进度与停滞监控；含主表 `sync_loan_foreclosure` 所缺的实际历时天数（`*_stage_days` 等） |
| **上游来源** | Redshift `port.fcl_stage_info`（`GEN_FCL_STAGE`：主筛选 `activefcflag=1 AND fcremovaldate IS NULL`；次筛选 Demand 且 D90/D120P）→ `JOIN port.portfunding`（见 doc 13 §7） |
| **下游使用** | BPS 聚合概览页 Stage Tab（阶段天数）与 Time Line Tab（里程碑日期）；`stage` 代码经前端映射为显示名 |
| **Foreclosure 关系** | 核心：**唯一排除完结贷款**的 FCL 表（仅活跃 FCL），与主表 `sync_loan_foreclosure`（含完结）人口不同，数量不应直接比较 |
| **主键 / 索引** | `id` 自增主键；业务键 `loanid + fctrdt`（每日快照） |
| **DB验证** | 2026-06-01 实测：57列；5,825 行（56 个 distinct loanid × 多快照日）；`stage` 6 种代码；脚本 `scripts/extract_table_stats.py` |

> 阶段字段按前缀分组（`demand_`/`noi_`/`referral_`/`first_legal_`/`service_`/`publication_`/`judgement_`/`sale_`），各组含 `*_start_date`/`*_end_date`/`*_stage_days`/`*_in_lm_days`/`*_on_hold_days`；Upcoming 组用 `to_judgement_days`/`to_sale_days` 替代 stage_days。`noi_*`/`publication_*` 对 Newrez 恒 NULL（见 doc 13 §7）。

#### 字段说明（57列）

| 字段名 | 字段业务含义 | 来源数据 | 计算/推导逻辑 | 数据类型 | 取值范围 | 典型取值 | 上游字段 | 下游用途 | 备注 |
|--------|-----------|--------|-----------|----------|---------|---------|--------|--------|------|
| `id` | 自增主键 | BPS ETL（GEN_FCL_STAGE） | 直接写入 | bigint NOT NULL | 299808 ~ 305632 | 299808 | — | 技术主键 | ✅；填充 5825/5825=100% |
| `stage` | 当前 FCL 阶段代码（全大写） | BPS ETL（GEN_FCL_STAGE） | ETL 计算/派生 | varchar(100) | {REFERRAL, SALE, SERVICE, FIRST_LEGAL, JUDGEMENT, DEMAND} | REFERRAL | — | BPS 聚合页分组键；瀑布优先级判定 | ✅ {SALE,JUDGEMENT,SERVICE,FIRST_LEGAL,REFERRAL,DEMAND}；填充 5825/5825=100% |
| `fctrdt` | 数据快照日（每贷款每天一行） | BPS ETL（GEN_FCL_STAGE） | 直接写入 | date | 2025-06-04 ~ 2026-03-13 | 2025-06-04 | — | 查询当前态需 `fctrdt=MAX(fctrdt)` | ✅；填充 5825/5825=100% |
| `loanid` | 系统贷款 ID | BPS ETL（GEN_FCL_STAGE） | 直接写入 | varchar(100) | 文本，56种（样例 7727000065 … 7727005351） | 7727000065 | — | 贷款 join key | ✅；填充 5825/5825=100% |
| `group` | 派生分类（FCL/REO/D120P/D90） | BPS ETL（GEN_FCL_STAGE） | ETL 计算/派生 | varchar(100) | {FCL, D120P, D90, REO} | FCL | — | 聚合页分组/过滤 | ✅ ETL 写入派生字段；填充 5825/5825=100% |
| `servicer` | Servicer 名称 | BPS ETL（GEN_FCL_STAGE） | 直接写入 | varchar(100) | {Newrez, Carrington} | Newrez | — | 聚合页过滤 | ✅；填充 5825/5825=100% |
| `state` | 物业所在州 | BPS ETL（GEN_FCL_STAGE） | 直接写入 | varchar(100) | {FL, IL, NY, CA, AZ, IN, CO, PA, TX, WA, OR, NC, MT, MD, MA, RI} 等22种 | FL | `newrez.portnewrezfc.*`（经 `port.basic_data_loan_fcl`） | 聚合页过滤 | ✅；填充 5825/5825=100% |
| `judicial` | 是否司法州（Y/N） | BPS ETL（GEN_FCL_STAGE） | 直接写入 | varchar(1) | {Y, N} | Y | `newrez.portnewrezfc.*`（经 `port.basic_data_loan_fcl`） | 司法/非司法流程区分 | ✅；填充 5825/5825=100% |
| `demand_start_date` | NOI/Demand Letter 阶段 · 阶段开始日 | BPS ETL（GEN_FCL_STAGE） | 源 timeline 日期（经 basic_data_loan_fcl） | date | 2021-10-18 ~ 2026-02-04 | 2021-10-18 | `newrez.portnewrezfc` timeline | 聚合页 NOI/Demand Letter 组 | ✅；填充 4858/5825=83% |
| `demand_end_date` | NOI/Demand Letter 阶段 · 阶段结束日 | BPS ETL（GEN_FCL_STAGE） | 源 timeline 日期（经 basic_data_loan_fcl） | date | 2021-11-22 ~ 2026-03-11 | 2021-11-22 | `newrez.portnewrezfc` timeline | 聚合页 NOI/Demand Letter 组 | ✅；填充 4858/5825=83% |
| `demand_stage_days` | NOI/Demand Letter 阶段 · 在该阶段已历天数 | BPS ETL（GEN_FCL_STAGE） | BPS 结合 LM/Hold 状态计算 | int | 3 ~ 1452 | 3 | `portnewrezlm.activelmflag` / Hold 状态 | 聚合页 NOI/Demand Letter 组 | ✅；填充 4858/5825=83% |
| `demand_in_lm_days` | NOI/Demand Letter 阶段 · 该阶段内处于 LM 的天数 | BPS ETL（GEN_FCL_STAGE） | BPS 结合 LM/Hold 状态计算 | int | 3 ~ 283 | 3 | `portnewrezlm.activelmflag` / Hold 状态 | 聚合页 NOI/Demand Letter 组 | ✅；填充 2573/5825=44% |
| `demand_on_hold_days` | NOI/Demand Letter 阶段 · 该阶段内处于 Hold 的天数 | BPS ETL（GEN_FCL_STAGE） | BPS 结合 LM/Hold 状态计算 | int | 1 ~ 250 | 1 | `portnewrezlm.activelmflag` / Hold 状态 | 聚合页 NOI/Demand Letter 组 | ✅；填充 2672/5825=46% |
| `noi_start_date` | NOI(Approved for Referral) 阶段 · 阶段开始日 | BPS ETL（GEN_FCL_STAGE） | 源 timeline 日期（经 basic_data_loan_fcl） | date | 实测全为 NULL | — | `newrez.portnewrezfc` timeline | 聚合页 NOI(Approved for Referral) 组 | ✅；填充 0/5825=0% |
| `noi_end_date` | NOI(Approved for Referral) 阶段 · 阶段结束日 | BPS ETL（GEN_FCL_STAGE） | 源 timeline 日期（经 basic_data_loan_fcl） | date | 实测全为 NULL | — | `newrez.portnewrezfc` timeline | 聚合页 NOI(Approved for Referral) 组 | ✅；填充 0/5825=0% |
| `noi_stage_days` | NOI(Approved for Referral) 阶段 · 在该阶段已历天数 | BPS ETL（GEN_FCL_STAGE） | BPS 结合 LM/Hold 状态计算 | int | 实测全为 NULL | — | `portnewrezlm.activelmflag` / Hold 状态 | 聚合页 NOI(Approved for Referral) 组 | ✅；填充 0/5825=0% |
| `noi_in_lm_days` | NOI(Approved for Referral) 阶段 · 该阶段内处于 LM 的天数 | BPS ETL（GEN_FCL_STAGE） | BPS 结合 LM/Hold 状态计算 | int | 实测全为 NULL | — | `portnewrezlm.activelmflag` / Hold 状态 | 聚合页 NOI(Approved for Referral) 组 | ✅；填充 0/5825=0% |
| `noi_on_hold_days` | NOI(Approved for Referral) 阶段 · 该阶段内处于 Hold 的天数 | BPS ETL（GEN_FCL_STAGE） | BPS 结合 LM/Hold 状态计算 | int | 实测全为 NULL | — | `portnewrezlm.activelmflag` / Hold 状态 | 聚合页 NOI(Approved for Referral) 组 | ✅；填充 0/5825=0% |
| `referral_start_date` | Referral 阶段 · 阶段开始日 | BPS ETL（GEN_FCL_STAGE） | 源 timeline 日期（经 basic_data_loan_fcl） | date | 2024-01-11 ~ 2026-03-10 | 2024-01-11 | `newrez.portnewrezfc` timeline | 聚合页 Referral 组 | ✅；填充 5501/5825=94% |
| `referral_end_date` | Referral 阶段 · 阶段结束日 | BPS ETL（GEN_FCL_STAGE） | 源 timeline 日期（经 basic_data_loan_fcl） | date | {2025-02-12, 2025-04-03, 2025-04-15, 2025-05-19, 2025-01-16, 2025-06-13, 2025-06-11, 2025-07-23, 2025-07-21, 2025-07-28, 2025-08-13, 2025-08-07, 2024-10-29, 2025-03-31, 2025-10-14, 2025-03-27} 等30种 | 2025-02-12 | `newrez.portnewrezfc` timeline | 聚合页 Referral 组 | ✅；填充 3436/5825=59% |
| `referral_stage_days` | Referral 阶段 · 在该阶段已历天数 | BPS ETL（GEN_FCL_STAGE） | BPS 结合 LM/Hold 状态计算 | int | 3 ~ 762 | 3 | `portnewrezlm.activelmflag` / Hold 状态 | 聚合页 Referral 组 | ✅；填充 5501/5825=94% |
| `referral_in_lm_days` | Referral 阶段 · 该阶段内处于 LM 的天数 | BPS ETL（GEN_FCL_STAGE） | BPS 结合 LM/Hold 状态计算 | int | 3 ~ 132 | 3 | `portnewrezlm.activelmflag` / Hold 状态 | 聚合页 Referral 组 | ✅；填充 816/5825=14% |
| `referral_on_hold_days` | Referral 阶段 · 该阶段内处于 Hold 的天数 | BPS ETL（GEN_FCL_STAGE） | BPS 结合 LM/Hold 状态计算 | int | 2 ~ 227 | 2 | `portnewrezlm.activelmflag` / Hold 状态 | 聚合页 Referral 组 | ✅；填充 1300/5825=22% |
| `first_legal_start_date` | First Legal 阶段 · 阶段开始日 | BPS ETL（GEN_FCL_STAGE） | 源 timeline 日期（经 basic_data_loan_fcl） | date | {2025-02-12, 2025-04-03, 2025-04-15, 2025-05-19, 2025-01-16, 2025-06-13, 2025-06-11, 2025-07-23, 2025-07-21, 2025-07-28, 2025-08-13, 2025-08-07, 2024-10-29, 2025-03-31, 2025-10-14, 2025-03-27} 等30种 | 2025-02-12 | `newrez.portnewrezfc` timeline | 聚合页 First Legal 组 | ✅；填充 3436/5825=59% |
| `first_legal_end_date` | First Legal 阶段 · 阶段结束日 | BPS ETL（GEN_FCL_STAGE） | 源 timeline 日期（经 basic_data_loan_fcl） | date | {2025-03-04, 2025-04-24, 2025-06-02, 2025-07-18, 2025-08-14, 2025-08-25, 2025-05-28, 2025-09-02, 2025-05-23, 2025-12-08, 2025-05-03, 2025-12-24, 2025-09-21, 2026-01-13, 2025-12-29, 2025-07-27} 等17种 | 2025-03-04 | `newrez.portnewrezfc` timeline | 聚合页 First Legal 组 | ✅；填充 1993/5825=34% |
| `first_legal_stage_days` | First Legal 阶段 · 在该阶段已历天数 | BPS ETL（GEN_FCL_STAGE） | BPS 结合 LM/Hold 状态计算 | int | 3 ~ 424 | 3 | `portnewrezlm.activelmflag` / Hold 状态 | 聚合页 First Legal 组 | ✅；填充 3436/5825=59% |
| `first_legal_in_lm_days` | First Legal 阶段 · 该阶段内处于 LM 的天数 | BPS ETL（GEN_FCL_STAGE） | BPS 结合 LM/Hold 状态计算 | int | 1 ~ 283 | 1 | `portnewrezlm.activelmflag` / Hold 状态 | 聚合页 First Legal 组 | ✅；填充 828/5825=14% |
| `first_legal_on_hold_days` | First Legal 阶段 · 该阶段内处于 Hold 的天数 | BPS ETL（GEN_FCL_STAGE） | BPS 结合 LM/Hold 状态计算 | int | 3 ~ 250 | 3 | `portnewrezlm.activelmflag` / Hold 状态 | 聚合页 First Legal 组 | ✅；填充 853/5825=15% |
| `first_legal_date_history` | 首次法律行动日变更历史 | BPS ETL（GEN_FCL_STAGE） | ETL 计算/派生 | text | 实测全为 NULL | — | — | First Legal 改期追溯 | 🟡 dev 全 NULL；填充 0/5825=0% |
| `service_start_date` | Service 阶段 · 阶段开始日 | BPS ETL（GEN_FCL_STAGE） | 源 timeline 日期（经 basic_data_loan_fcl） | date | {2025-03-04, 2025-04-24, 2025-06-02, 2025-07-18, 2025-08-14, 2025-08-25, 2025-05-28, 2025-09-02, 2025-05-23, 2025-12-08, 2025-05-03, 2025-12-24, 2025-09-21, 2026-01-13, 2025-12-29, 2025-07-27} 等17种 | 2025-03-04 | `newrez.portnewrezfc` timeline | 聚合页 Service 组 | ✅；填充 1993/5825=34% |
| `service_end_date` | Service 阶段 · 阶段结束日 | BPS ETL（GEN_FCL_STAGE） | 源 timeline 日期（经 basic_data_loan_fcl） | date | {2025-11-17, 2025-07-03, 2025-12-17, 2025-10-27, 2025-06-11, 2025-10-29, 2026-01-26, 2025-08-08, 2025-12-08, 2025-07-15, 2025-07-14, 2025-07-21, 2025-08-06, 2026-02-13, 2025-11-04, 2025-09-12} 等22种 | 2025-11-17 | `newrez.portnewrezfc` timeline | 聚合页 Service 组 | ✅；填充 839/5825=14% |
| `service_stage_days` | Service 阶段 · 在该阶段已历天数 | BPS ETL（GEN_FCL_STAGE） | BPS 结合 LM/Hold 状态计算 | int | 4 ~ 377 | 4 | `portnewrezlm.activelmflag` / Hold 状态 | 聚合页 Service 组 | ✅；填充 1993/5825=34% |
| `service_in_lm_days` | Service 阶段 · 该阶段内处于 LM 的天数 | BPS ETL（GEN_FCL_STAGE） | BPS 结合 LM/Hold 状态计算 | int | 3 ~ 102 | 3 | `portnewrezlm.activelmflag` / Hold 状态 | 聚合页 Service 组 | ✅；填充 832/5825=14% |
| `service_on_hold_days` | Service 阶段 · 该阶段内处于 Hold 的天数 | BPS ETL（GEN_FCL_STAGE） | BPS 结合 LM/Hold 状态计算 | int | 1 ~ 145 | 1 | `portnewrezlm.activelmflag` / Hold 状态 | 聚合页 Service 组 | ✅；填充 834/5825=14% |
| `publication_start_date` | Publication 阶段 · 阶段开始日 | BPS ETL（GEN_FCL_STAGE） | 源 timeline 日期（经 basic_data_loan_fcl） | date | 实测全为 NULL | — | `newrez.portnewrezfc` timeline | 聚合页 Publication 组 | ✅；填充 0/5825=0% |
| `publication_end_date` | Publication 阶段 · 阶段结束日 | BPS ETL（GEN_FCL_STAGE） | 源 timeline 日期（经 basic_data_loan_fcl） | date | 实测全为 NULL | — | `newrez.portnewrezfc` timeline | 聚合页 Publication 组 | ✅；填充 0/5825=0% |
| `publication_stage_days` | Publication 阶段 · 在该阶段已历天数 | BPS ETL（GEN_FCL_STAGE） | BPS 结合 LM/Hold 状态计算 | int | 实测全为 NULL | — | `portnewrezlm.activelmflag` / Hold 状态 | 聚合页 Publication 组 | ✅；填充 0/5825=0% |
| `publication_in_lm_days` | Publication 阶段 · 该阶段内处于 LM 的天数 | BPS ETL（GEN_FCL_STAGE） | BPS 结合 LM/Hold 状态计算 | int | 实测全为 NULL | — | `portnewrezlm.activelmflag` / Hold 状态 | 聚合页 Publication 组 | ✅；填充 0/5825=0% |
| `publication_on_hold_days` | Publication 阶段 · 该阶段内处于 Hold 的天数 | BPS ETL（GEN_FCL_STAGE） | BPS 结合 LM/Hold 状态计算 | int | 实测全为 NULL | — | `portnewrezlm.activelmflag` / Hold 状态 | 聚合页 Publication 组 | ✅；填充 0/5825=0% |
| `judgement_start_date` | Upcoming Judgement 阶段 · 阶段开始日 | BPS ETL（GEN_FCL_STAGE） | 源 timeline 日期（经 basic_data_loan_fcl） | date | {2025-11-29, 2025-09-16, 2026-03-27, 2026-02-04, 2025-09-23, 2026-04-08, 2026-01-18, 2026-01-17, 2026-03-23, 2025-10-15, 2025-10-27, 2025-12-03, 2025-11-14, 2026-04-13, 2026-02-21, 2025-08-07} 等22种 | 2025-11-29 | `newrez.portnewrezfc` timeline | 聚合页 Upcoming Judgement 组 | ✅；填充 839/5825=14% |
| `judgement_end_date` | Upcoming Judgement 阶段 · 阶段结束日 | BPS ETL（GEN_FCL_STAGE） | 源 timeline 日期（经 basic_data_loan_fcl） | date | 实测全为 NULL | — | `newrez.portnewrezfc` timeline | 聚合页 Upcoming Judgement 组 | ✅；填充 0/5825=0% |
| `to_judgement_days` | 距判决日剩余天数 | BPS ETL（GEN_FCL_STAGE） | BPS 计算 | int | 0 ~ 151 | 0 | — | Upcoming Judgement 组 Days to Judgement | ✅；填充 839/5825=14% |
| `judgement_in_lm_days` | Upcoming Judgement 阶段 · 该阶段内处于 LM 的天数 | BPS ETL（GEN_FCL_STAGE） | BPS 结合 LM/Hold 状态计算 | int | 3 ~ 23（21种） | 9 | `portnewrezlm.activelmflag` / Hold 状态 | 聚合页 Upcoming Judgement 组 | ✅；填充 57/5825=1% |
| `judgement_on_hold_days` | Upcoming Judgement 阶段 · 该阶段内处于 Hold 的天数 | BPS ETL（GEN_FCL_STAGE） | BPS 结合 LM/Hold 状态计算 | int | 3 ~ 51 | 3 | `portnewrezlm.activelmflag` / Hold 状态 | 聚合页 Upcoming Judgement 组 | ✅；填充 274/5825=5% |
| `sale_start_date` | Upcoming FC Sales 阶段 · 阶段开始日 | BPS ETL（GEN_FCL_STAGE） | 源 timeline 日期（经 basic_data_loan_fcl） | date | {2025-12-29, 2025-12-30, 2026-03-31, 2025-12-17, 2025-08-15, 2026-01-16, 2026-04-08, 2026-05-15, 2025-08-26, 2026-03-03, 2026-04-07, 2025-10-28, 2026-02-04, 2025-10-14, 2026-03-11, 2026-02-27} 等30种 | 2025-12-29 | `newrez.portnewrezfc` timeline | 聚合页 Upcoming FC Sales 组 | ✅；填充 1197/5825=21% |
| `sale_end_date` | Upcoming FC Sales 阶段 · 阶段结束日 | BPS ETL（GEN_FCL_STAGE） | 源 timeline 日期（经 basic_data_loan_fcl） | date | 实测全为 NULL | — | `newrez.portnewrezfc` timeline | 聚合页 Upcoming FC Sales 组 | ✅；填充 0/5825=0% |
| `to_sale_days` | 距拍卖日剩余天数 | BPS ETL（GEN_FCL_STAGE） | BPS 计算 | int | 0 ~ 129 | 0 | — | Upcoming FC Sales 组 Days to Sale | ✅；填充 1197/5825=21% |
| `sale_in_lm_days` | Upcoming FC Sales 阶段 · 该阶段内处于 LM 的天数 | BPS ETL（GEN_FCL_STAGE） | BPS 结合 LM/Hold 状态计算 | int | 3 ~ 88 | 3 | `portnewrezlm.activelmflag` / Hold 状态 | 聚合页 Upcoming FC Sales 组 | ✅；填充 213/5825=4% |
| `sale_on_hold_days` | Upcoming FC Sales 阶段 · 该阶段内处于 Hold 的天数 | BPS ETL（GEN_FCL_STAGE） | BPS 结合 LM/Hold 状态计算 | int | 3 ~ 109 | 3 | `portnewrezlm.activelmflag` / Hold 状态 | 聚合页 Upcoming FC Sales 组 | ✅；填充 216/5825=4% |
| `create_time` | 记录创建时间 | BPS ETL（GEN_FCL_STAGE） | ETL 计算/派生 | datetime | {2026-03-16 06:54:17} | 2026-03-16 06:54:17 | — | 管理字段 | ✅ 实测=同步批次时间；填充 5825/5825=100% |
| `update_time` | 记录更新时间 | BPS ETL（GEN_FCL_STAGE） | ETL 计算/派生 | datetime | {2026-03-16 06:54:17} | 2026-03-16 06:54:17 | — | 管理字段 | ✅；填充 5825/5825=100% |
| `create_user` | 记录创建用户 | BPS ETL（GEN_FCL_STAGE） | ETL 计算/派生 | bigint | 实测全为 NULL | — | — | 审计追踪 | dev 未回填；填充 0/5825=0% |
| `create_dept` | 记录创建部门 | BPS ETL（GEN_FCL_STAGE） | ETL 计算/派生 | bigint | 实测全为 NULL | — | — | 审计追踪 | dev 未回填；填充 0/5825=0% |
| `update_user` | 最后更新用户 | BPS ETL（GEN_FCL_STAGE） | ETL 计算/派生 | bigint | 实测全为 NULL | — | — | 审计追踪 | dev 未回填；填充 0/5825=0% |
| `status` | 记录状态（0=正常） | BPS ETL（GEN_FCL_STAGE） | ETL 计算/派生 | int NOT NULL | {0}（1种） | 0 | — | 软停用标志 | ✅；填充 5825/5825=100% |
| `is_deleted` | 是否软删除（0=未删） | BPS ETL（GEN_FCL_STAGE） | ETL 计算/派生 | int NOT NULL | {0}（1种） | 0 | — | 软删除标志 | ✅；填充 5825/5825=100% |
| `tenant_id` | 租户 ID | BPS ETL（GEN_FCL_STAGE） | ETL 计算/派生 | varchar(12) NOT NULL | {000000} | 000000 | — | 多租户支持 | ✅；填充 5825/5825=100% |

---

### 表 25：`bpms_dev.biz_data_view_loan_details_foreclosure` — BPS FCL 详情展示视图

| 属性 | 值 |
|------|----|
| **表名** | `biz_data_view_loan_details_foreclosure`（**VIEW，非物理表**） |
| **所属 Schema** | MySQL `bpms_dev` |
| **数据层** | Layer 5 — BPS Application Layer（展示视图，最终展示口径） |
| **业务作用** | BPS Loan Foreclosure 详情页最终数据视图：在主表 `sync_loan_foreclosure` 基础上，按 `nextduedate` 实时计算各阶段 `actual_*_days`、`var_*_days` 偏差及 total 汇总 |
| **业务意图** | 将「目标 vs 实际 vs 偏差」三类天数指标在查询层一次性算出，避免落库；resolved actual/var 字段（如 `actual_judgement_hearing_set_days`）仅存在于本视图 |
| **视图定义** | `sync_portmonth`(monthly) `LEFT JOIN sync_loan_foreclosure`(loan_fcl) ON `loanid+tenant_id`，再 LEFT JOIN 各 loanid 的 `MAX(fctrdt)` 子查询（取最新月度快照）。`actual_*_days = TO_DAYS(timeline_x) − TO_DAYS(nextduedate)`；`var_*_days = actual − 累计 target`（MCP `SHOW CREATE VIEW` 实测） |
| **下游使用** | BPS 详情页 Milestone Timeline / Target / Actual / Variance 面板（含 doc 14 SQL-C3 验证的 `actual_judgement_hearing_set_days`） |
| **Foreclosure 关系** | 核心展示层：FCL 时间线 + SLA 合规（actual vs target）一站式视图 |
| **主键 / 索引** | 视图无主键；按 `loanid + fctrdt` 唯一 |
| **DB验证** | 2026-06-01 实测：104列；122,550 行（基于 `sync_portmonth` 全量月度贷款，含非 FCL，故 timeline/summary 等填充率低）；脚本 `scripts/extract_table_stats.py` |

> 列结构（104）：标识与锚点 5 + `timeline_*` 19 + `target_*_days` 15 + `actual_*_days` 15 + `variance_*` 4 + `bid_approval_*` 4 + `summary_*` 16 + 管理字段 8 + `var_*_days` 15 + 汇总 3（`var_total`/`target_total`/`actual_total`）。`target_*` 在视图中为 `bigint`（基表为 `int`）。填充率低因视图人口为全部月度贷款（122,550 行），非仅活跃 FCL。

#### 字段说明（104列）

| 字段名 | 字段业务含义 | 来源数据 | 计算/推导逻辑 | 数据类型 | 取值范围 | 典型取值 | 上游字段 | 下游用途 | 备注 |
|--------|-----------|--------|-----------|----------|---------|---------|--------|--------|------|
| `id` | FCL 记录 ID（来自 loan_fcl） | 视图计算 | `loan_fcl.id` | bigint | 1 ~ 279 | 1 | 表17 `id` | 贷款 FCL 关联 | ✅；填充 2359/122550=2% |
| `loanid` | 系统贷款 ID | 视图计算 | `monthly.loanid` | bigint | 7727000002 ~ 700083320000172 | 7727000002 | `sync_portmonth.loanid` | 视图主键 | ✅；填充 122550/122550=100% |
| `svcloanid` | Servicer 内部贷款号 | 视图计算 | `monthly.svcloanid` | varchar(32) | 文本，9426种（样例 001324995 … HB0075942） | 001324995 | `sync_portmonth` | 对账 | ✅；填充 122550/122550=100% |
| `fctrdt` | 数据快照日（月度） | 视图计算 | `monthly.fctrdt` | date | 2023-02-01 ~ 2026-03-01 | 2023-02-01 | `sync_portmonth` | 时间维度 | ✅；填充 122550/122550=100% |
| `nextduedate` | 下次应还款日（DPD/历时计算锚点） | 视图计算 | `monthly.nextduedate` | date | 2021-09-01 ~ 2027-07-01 | 2021-09-01 | `sync_portmonth` | actual_*_days 计算基准 | ✅ 100%；填充 122037/122550=100% |
| `timeline_notice_of_intent_date` | FCL 里程碑日期（同表17 `timeline_notice_of_intent_date`） | 视图计算 | 取自 `loan_fcl.timeline_notice_of_intent_date` | date | {2025-04-22, 2024-05-17, 2024-10-18, 2025-02-22, 2025-01-22} | 2025-04-22 | 表17 `timeline_notice_of_intent_date` | Milestone Timeline 展示 | ✅；填充 145/122550=0% |
| `timeline_notice_of_intent_end_date` | FCL 里程碑日期（同表17 `timeline_notice_of_intent_end_date`） | 视图计算 | 取自 `loan_fcl.timeline_notice_of_intent_end_date` | date | 实测全为 NULL | — | 表17 `timeline_notice_of_intent_end_date` | Milestone Timeline 展示 | ✅；填充 0/122550=0% |
| `timeline_approved_for_referral_date` | FCL 里程碑日期（同表17 `timeline_approved_for_referral_date`） | 视图计算 | 取自 `loan_fcl.timeline_approved_for_referral_date` | date | 实测全为 NULL | — | 表17 `timeline_approved_for_referral_date` | Milestone Timeline 展示 | ✅；填充 0/122550=0% |
| `timeline_referred_to_attorney_date` | FCL 里程碑日期（同表17 `timeline_referred_to_attorney_date`） | 视图计算 | 取自 `loan_fcl.timeline_referred_to_attorney_date` | date | 实测全为 NULL | — | 表17 `timeline_referred_to_attorney_date` | Milestone Timeline 展示 | ✅；填充 0/122550=0% |
| `timeline_referred_to_foreclosure_date` | FCL 里程碑日期（同表17 `timeline_referred_to_foreclosure_date`） | 视图计算 | 取自 `loan_fcl.timeline_referred_to_foreclosure_date` | date | 2018-08-15 ~ 2026-03-10 | 2018-08-15 | 表17 `timeline_referred_to_foreclosure_date` | Milestone Timeline 展示 | ✅；填充 2359/122550=2% |
| `timeline_title_report_received_date` | FCL 里程碑日期（同表17 `timeline_title_report_received_date`） | 视图计算 | 取自 `loan_fcl.timeline_title_report_received_date` | date | {2025-12-02, 2025-03-24} | 2025-12-02 | 表17 `timeline_title_report_received_date` | Milestone Timeline 展示 | ✅；填充 96/122550=0% |
| `timeline_preliminary_title_cleared_date` | FCL 里程碑日期（同表17 `timeline_preliminary_title_cleared_date`） | 视图计算 | 取自 `loan_fcl.timeline_preliminary_title_cleared_date` | date | {2025-03-24, 2026-02-02} | 2025-03-24 | 表17 `timeline_preliminary_title_cleared_date` | Milestone Timeline 展示 | ✅；填充 59/122550=0% |
| `timeline_first_legal_date` | FCL 里程碑日期（同表17 `timeline_first_legal_date`） | 视图计算 | 取自 `loan_fcl.timeline_first_legal_date` | date | 2018-10-29 ~ 2026-02-25 | 2018-10-29 | 表17 `timeline_first_legal_date` | Milestone Timeline 展示 | ✅；填充 1127/122550=1% |
| `timeline_service_date` | FCL 里程碑日期（同表17 `timeline_service_date`） | 视图计算 | 取自 `loan_fcl.timeline_service_date` | date | {2025-06-02, 2025-09-02, 2025-05-03, 2026-01-13, 2025-07-18, 2025-08-14, 2024-04-01, 2025-11-19, 2025-03-04, 2025-05-23, 2024-11-26, 2025-12-08, 2025-04-24, 2018-12-10, 2025-05-28, 2025-12-29} 等19种 | 2025-06-02 | 表17 `timeline_service_date` | Milestone Timeline 展示 | ✅；填充 559/122550=0% |
| `timeline_publication_date` | FCL 里程碑日期（同表17 `timeline_publication_date`） | 视图计算 | 取自 `loan_fcl.timeline_publication_date` | date | 实测全为 NULL | — | 表17 `timeline_publication_date` | Milestone Timeline 展示 | ✅；填充 0/122550=0% |
| `timeline_judgement_hearing_set_date` | FCL 里程碑日期（同表17 `timeline_judgement_hearing_set_date`） | 视图计算 | 取自 `loan_fcl.timeline_judgement_hearing_set_date` | date | {2025-10-27, 2025-07-15, 2026-03-06, 2026-01-26, 2025-08-06, 2025-11-17, 2023-12-14, 2025-07-03, 2026-02-13} | 2025-10-27 | 表17 `timeline_judgement_hearing_set_date` | Milestone Timeline 展示 | ✅；填充 272/122550=0% |
| `timeline_judgement_date` | FCL 里程碑日期（同表17 `timeline_judgement_date`） | 视图计算 | 取自 `loan_fcl.timeline_judgement_date` | date | {2026-02-04, 2025-10-15, 2026-07-15, 2026-01-18, 2025-11-14, 2025-11-29, 2020-01-22, 2025-09-16, 2026-04-13} | 2026-02-04 | 表17 `timeline_judgement_date` | Milestone Timeline 展示 | ✅；填充 272/122550=0% |
| `timeline_sale_date_projected_date` | FCL 里程碑日期（同表17 `timeline_sale_date_projected_date`） | 视图计算 | 取自 `loan_fcl.timeline_sale_date_projected_date` | date | {2026-04-07, 2026-04-08, 2026-03-31, 2026-04-02, 2025-06-05, 2026-06-26, 2026-05-15, 2025-08-26, 2026-01-16, 2025-01-23, 2025-05-16, 2025-11-04, 2026-03-27, 2026-05-19, 2025-09-09} | 2026-04-07 | 表17 `timeline_sale_date_projected_date` | Milestone Timeline 展示 | ✅；填充 521/122550=0% |
| `timeline_sale_date_set_date` | FCL 里程碑日期（同表17 `timeline_sale_date_set_date`） | 视图计算 | 取自 `loan_fcl.timeline_sale_date_set_date` | date | {2026-02-25, 2026-02-22, 2025-12-23, 2026-01-23, 2025-03-07, 2026-02-15, 2026-01-08, 2025-07-18, 2025-01-23, 2025-11-26, 2025-04-10, 2025-09-25, 2026-02-11, 2026-02-27, 2026-03-12, 2026-02-19} 等17种 | 2026-02-25 | 表17 `timeline_sale_date_set_date` | Milestone Timeline 展示 | ✅；填充 521/122550=0% |
| `timeline_final_title_cleared_date` | FCL 里程碑日期（同表17 `timeline_final_title_cleared_date`） | 视图计算 | 取自 `loan_fcl.timeline_final_title_cleared_date` | date | {2025-03-24, 2026-02-02} | 2025-03-24 | 表17 `timeline_final_title_cleared_date` | Milestone Timeline 展示 | ✅；填充 59/122550=0% |
| `timeline_sale_date_held_date` | FCL 里程碑日期（同表17 `timeline_sale_date_held_date`） | 视图计算 | 取自 `loan_fcl.timeline_sale_date_held_date` | date | {2026-03-11, 2025-10-14, 2026-01-16, 2025-01-23, 2025-12-04, 2025-12-29, 2025-11-04} | 2026-03-11 | 表17 `timeline_sale_date_held_date` | Milestone Timeline 展示 | ✅；填充 204/122550=0% |
| `timeline_foreclosure_completed_date` | FCL 里程碑日期（同表17 `timeline_foreclosure_completed_date`） | 视图计算 | 取自 `loan_fcl.timeline_foreclosure_completed_date` | date | 实测全为 NULL | — | 表17 `timeline_foreclosure_completed_date` | Milestone Timeline 展示 | ✅；填充 0/122550=0% |
| `timeline_third_party_sold_date_date` | FCL 里程碑日期（同表17 `timeline_third_party_sold_date_date`） | 视图计算 | 取自 `loan_fcl.timeline_third_party_sold_date_date` | date | 实测全为 NULL | — | 表17 `timeline_third_party_sold_date_date` | Milestone Timeline 展示 | ✅；填充 0/122550=0% |
| `timeline_third_party_proceeds_received_date` | FCL 里程碑日期（同表17 `timeline_third_party_proceeds_received_date`） | 视图计算 | 取自 `loan_fcl.timeline_third_party_proceeds_received_date` | date | {2026-03-05} | 2026-03-05 | 表17 `timeline_third_party_proceeds_received_date` | Milestone Timeline 展示 | ✅；填充 21/122550=0% |
| `target_notice_of_intent_days` | SLA 目标天数（同表17 `target_notice_of_intent_days`） | 视图计算 | `IFNULL(loan_fcl.target_notice_of_intent_days, 默认值)` | bigint NOT NULL | {30}（1种） | 30 | 表17 `target_notice_of_intent_days` | Target 基准 | ✅ 含 IFNULL 默认；填充 122550/122550=100% |
| `target_notice_of_intent_expired_days` | SLA 目标天数（同表17 `target_notice_of_intent_expired_days`） | 视图计算 | `IFNULL(loan_fcl.target_notice_of_intent_expired_days, 默认值)` | bigint NOT NULL | {90}（1种） | 90 | 表17 `target_notice_of_intent_expired_days` | Target 基准 | ✅ 含 IFNULL 默认；填充 122550/122550=100% |
| `target_approved_for_referral_days` | SLA 目标天数（同表17 `target_approved_for_referral_days`） | 视图计算 | `IFNULL(loan_fcl.target_approved_for_referral_days, 默认值)` | bigint NOT NULL | {30}（1种） | 30 | 表17 `target_approved_for_referral_days` | Target 基准 | ✅ 含 IFNULL 默认；填充 122550/122550=100% |
| `target_referred_to_attorney_days` | SLA 目标天数（同表17 `target_referred_to_attorney_days`） | 视图计算 | `IFNULL(loan_fcl.target_referred_to_attorney_days, 默认值)` | bigint NOT NULL | {1}（1种） | 1 | 表17 `target_referred_to_attorney_days` | Target 基准 | ✅ 含 IFNULL 默认；填充 122550/122550=100% |
| `target_referred_to_foreclosure_days` | SLA 目标天数（同表17 `target_referred_to_foreclosure_days`） | 视图计算 | `IFNULL(loan_fcl.target_referred_to_foreclosure_days, 默认值)` | bigint NOT NULL | {1}（1种） | 1 | 表17 `target_referred_to_foreclosure_days` | Target 基准 | ✅ 含 IFNULL 默认；填充 122550/122550=100% |
| `target_title_report_received_days` | SLA 目标天数（同表17 `target_title_report_received_days`） | 视图计算 | `IFNULL(loan_fcl.target_title_report_received_days, 默认值)` | bigint NOT NULL | {30}（1种） | 30 | 表17 `target_title_report_received_days` | Target 基准 | ✅ 含 IFNULL 默认；填充 122550/122550=100% |
| `target_preliminary_title_cleared_days` | SLA 目标天数（同表17 `target_preliminary_title_cleared_days`） | 视图计算 | `IFNULL(loan_fcl.target_preliminary_title_cleared_days, 默认值)` | bigint NOT NULL | {30}（1种） | 30 | 表17 `target_preliminary_title_cleared_days` | Target 基准 | ✅ 含 IFNULL 默认；填充 122550/122550=100% |
| `target_first_legal_days` | SLA 目标天数（同表17 `target_first_legal_days`） | 视图计算 | `IFNULL(loan_fcl.target_first_legal_days, 默认值)` | bigint NOT NULL | {120}（1种） | 120 | 表17 `target_first_legal_days` | Target 基准 | ✅ 含 IFNULL 默认；填充 122550/122550=100% |
| `target_service_days` | SLA 目标天数（同表17 `target_service_days`） | 视图计算 | `IFNULL(loan_fcl.target_service_days, 默认值)` | bigint NOT NULL | {90}（1种） | 90 | 表17 `target_service_days` | Target 基准 | ✅ 含 IFNULL 默认；填充 122550/122550=100% |
| `target_publication_days` | SLA 目标天数（同表17 `target_publication_days`） | 视图计算 | `IFNULL(loan_fcl.target_publication_days, 默认值)` | bigint NOT NULL | {30}（1种） | 30 | 表17 `target_publication_days` | Target 基准 | ✅ 含 IFNULL 默认；填充 122550/122550=100% |
| `target_judgement_hearing_set_days` | SLA 目标天数（同表17 `target_judgement_hearing_set_days`） | 视图计算 | `IFNULL(loan_fcl.target_judgement_hearing_set_days, 默认值)` | bigint NOT NULL | {120}（1种） | 120 | 表17 `target_judgement_hearing_set_days` | Target 基准 | ✅ 含 IFNULL 默认；填充 122550/122550=100% |
| `target_judgement_days` | SLA 目标天数（同表17 `target_judgement_days`） | 视图计算 | `IFNULL(loan_fcl.target_judgement_days, 默认值)` | bigint NOT NULL | {30}（1种） | 30 | 表17 `target_judgement_days` | Target 基准 | ✅ 含 IFNULL 默认；填充 122550/122550=100% |
| `target_sale_date_set_days` | SLA 目标天数（同表17 `target_sale_date_set_days`） | 视图计算 | `IFNULL(loan_fcl.target_sale_date_set_days, 默认值)` | bigint NOT NULL | {30}（1种） | 30 | 表17 `target_sale_date_set_days` | Target 基准 | ✅ 含 IFNULL 默认；填充 122550/122550=100% |
| `target_final_title_cleared_days` | SLA 目标天数（同表17 `target_final_title_cleared_days`） | 视图计算 | `IFNULL(loan_fcl.target_final_title_cleared_days, 默认值)` | bigint NOT NULL | {5}（1种） | 5 | 表17 `target_final_title_cleared_days` | Target 基准 | ✅ 含 IFNULL 默认；填充 122550/122550=100% |
| `target_sale_date_held_days` | SLA 目标天数（同表17 `target_sale_date_held_days`） | 视图计算 | `IFNULL(loan_fcl.target_sale_date_held_days, 默认值)` | bigint NOT NULL | {0}（1种） | 0 | 表17 `target_sale_date_held_days` | Target 基准 | ✅ 含 IFNULL 默认；填充 122550/122550=100% |
| `actual_notice_of_intent_days` | 实际历时天数（notice_of_intent） | 视图计算 | `TO_DAYS(timeline_notice_of_intent_date) − TO_DAYS(nextduedate)` | int | -594 ~ 811 | -594 | 本视图 timeline + nextduedate | Actual Days 展示 | ✅ 视图实时计算；填充 145/122550=0% |
| `actual_notice_of_intent_expire_days` | 实际历时天数（notice_of_intent_expire） | 视图计算 | `TO_DAYS(timeline_notice_of_intent_expire_date) − TO_DAYS(nextduedate)` | int | 实测全为 NULL | — | 本视图 timeline + nextduedate | Actual Days 展示 | ✅ 视图实时计算；填充 0/122550=0% |
| `actual_approved_for_referral_days` | 实际历时天数（approved_for_referral） | 视图计算 | `TO_DAYS(timeline_approved_for_referral_date) − TO_DAYS(nextduedate)` | int | 实测全为 NULL | — | 本视图 timeline + nextduedate | Actual Days 展示 | ✅ 视图实时计算；填充 0/122550=0% |
| `actual_referred_to_attorney_days` | 实际历时天数（referred_to_attorney） | 视图计算 | `TO_DAYS(timeline_referred_to_attorney_date) − TO_DAYS(nextduedate)` | int | 实测全为 NULL | — | 本视图 timeline + nextduedate | Actual Days 展示 | ✅ 视图实时计算；填充 0/122550=0% |
| `actual_referred_to_foreclosure_days` | 实际历时天数（referred_to_foreclosure） | 视图计算 | `TO_DAYS(timeline_referred_to_foreclosure_date) − TO_DAYS(nextduedate)` | int | -2147 ~ 1274 | -2147 | 本视图 timeline + nextduedate | Actual Days 展示 | ✅ 视图实时计算；填充 2346/122550=2% |
| `actual_title_report_received_days` | 实际历时天数（title_report_received） | 视图计算 | `TO_DAYS(timeline_title_report_received_date) − TO_DAYS(nextduedate)` | int | 215 ~ 1035 | 215 | 本视图 timeline + nextduedate | Actual Days 展示 | ✅ 视图实时计算；填充 95/122550=0% |
| `actual_preliminary_title_cleared_days` | 实际历时天数（preliminary_title_cleared） | 视图计算 | `TO_DAYS(timeline_preliminary_title_cleared_date) − TO_DAYS(nextduedate)` | int | 277 ~ 754（25种） | 357 | 本视图 timeline + nextduedate | Actual Days 展示 | ✅ 视图实时计算；填充 58/122550=0% |
| `actual_first_legal_days` | 实际历时天数（first_legal） | 视图计算 | `TO_DAYS(timeline_first_legal_date) − TO_DAYS(nextduedate)` | int | -2072 ~ 1100 | -2072 | 本视图 timeline + nextduedate | Actual Days 展示 | ✅ 视图实时计算；填充 1121/122550=1% |
| `actual_service_days` | 实际历时天数（service） | 视图计算 | `TO_DAYS(timeline_service_date) − TO_DAYS(nextduedate)` | int | -2030 ~ 1108 | -2030 | 本视图 timeline + nextduedate | Actual Days 展示 | ✅ 视图实时计算；填充 557/122550=0% |
| `actual_publication_days` | 实际历时天数（publication） | 视图计算 | `TO_DAYS(timeline_publication_date) − TO_DAYS(nextduedate)` | int | 实测全为 NULL | — | 本视图 timeline + nextduedate | Actual Days 展示 | ✅ 视图实时计算；填充 0/122550=0% |
| `actual_judgement_hearing_set_days` | 实际历时天数（judgement_hearing_set） | 视图计算 | `TO_DAYS(timeline_judgement_hearing_set_date) − TO_DAYS(nextduedate)` | int | -200 ~ 1129 | -200 | 本视图 timeline + nextduedate | Actual Days 展示 | ✅ 视图实时计算；填充 271/122550=0% |
| `actual_judgement_days` | 实际历时天数（judgement） | 视图计算 | `TO_DAYS(timeline_judgement_date) − TO_DAYS(nextduedate)` | int | -1622 ~ 1260 | -1622 | 本视图 timeline + nextduedate | Actual Days 展示 | ✅ 视图实时计算；填充 271/122550=0% |
| `actual_sale_date_set_days` | 实际历时天数（sale_date_set） | 视图计算 | `TO_DAYS(timeline_sale_date_set_date) − TO_DAYS(nextduedate)` | int | -359 ~ 1148 | -359 | 本视图 timeline + nextduedate | Actual Days 展示 | ✅ 视图实时计算；填充 517/122550=0% |
| `actual_final_title_cleared_days` | 实际历时天数（final_title_cleared） | 视图计算 | `TO_DAYS(timeline_final_title_cleared_date) − TO_DAYS(nextduedate)` | int | 277 ~ 754（25种） | 357 | 本视图 timeline + nextduedate | Actual Days 展示 | ✅ 视图实时计算；填充 58/122550=0% |
| `actual_sale_date_held_days` | 实际历时天数（sale_date_held） | 视图计算 | `TO_DAYS(timeline_sale_date_held_date) − TO_DAYS(nextduedate)` | int | 187 ~ 1075 | 187 | 本视图 timeline + nextduedate | Actual Days 展示 | ✅ 视图实时计算；填充 203/122550=0% |
| `variance_active_bankruptcy` | 同表17 `variance_active_bankruptcy` | 视图计算 | `loan_fcl.variance_active_bankruptcy` | int | 实测全为 NULL | — | 表17 `variance_active_bankruptcy` | BK 方差 | ✅；填充 0/122550=0% |
| `variance_completed_bankruptcy` | 同表17 `variance_completed_bankruptcy` | 视图计算 | `loan_fcl.variance_completed_bankruptcy` | int | 实测全为 NULL | — | 表17 `variance_completed_bankruptcy` | BK 方差 | ✅；填充 0/122550=0% |
| `variance_estimated_hold_days` | 同表17 `variance_estimated_hold_days` | 视图计算 | `loan_fcl.variance_estimated_hold_days` | int | 实测全为 NULL | — | 表17 `variance_estimated_hold_days` | BK 方差 | ✅；填充 0/122550=0% |
| `variance_bankruptcies` | 同表17 `variance_bankruptcies` | 视图计算 | `loan_fcl.variance_bankruptcies` | int | 实测全为 NULL | — | 表17 `variance_bankruptcies` | BK 方差 | ✅；填充 0/122550=0% |
| `bid_approval_status` | 同表17 `bid_approval_status` | 视图计算 | `loan_fcl.bid_approval_status` | varchar(128) | 实测全为 NULL | — | 表17 `bid_approval_status` | Bid Approval 展示 | ✅；填充 0/122550=0% |
| `bid_approval_sale_date` | 同表17 `bid_approval_sale_date` | 视图计算 | `loan_fcl.bid_approval_sale_date` | date | 实测全为 NULL | — | 表17 `bid_approval_sale_date` | Bid Approval 展示 | ✅；填充 0/122550=0% |
| `bid_approval_bid_amount` | 同表17 `bid_approval_bid_amount` | 视图计算 | `loan_fcl.bid_approval_bid_amount` | decimal(32,16) | {$125,366.73, $390,832.50, $231,285.22, $136,392.44, $154,591.01, $543,305.96, $271,278.01, $90,000, $428,971.78}（9种） | $125,366.73 | 表17 `bid_approval_bid_amount` | Bid Approval 展示 | ✅；填充 254/122550=0% |
| `bid_approval_loan_resolution_holods` | 同表17 `bid_approval_loan_resolution_holods` | 视图计算 | `loan_fcl.bid_approval_loan_resolution_holods` | text | 实测全为 NULL | — | 表17 `bid_approval_loan_resolution_holods` | Bid Approval 展示 | ✅；填充 0/122550=0% |
| `summary_servicer_number` | 同表17 `summary_servicer_number` | 视图计算 | `loan_fcl.summary_servicer_number` | varchar(64) | 实测全为 NULL | — | 表17 `summary_servicer_number` | Summary 展示 | ✅；填充 0/122550=0% |
| `summary_foreclosure_status` | 同表17 `summary_foreclosure_status` | 视图计算 | `loan_fcl.summary_foreclosure_status` | varchar(64) | {Active Foreclosure, Closed Foreclosure:Loss Mitigation, Closed Foreclosure:Reinstated, Closed Foreclosure:Paid in Full, Closed Foreclosure:Process Complete, 1. First Legal Pending, Closed Foreclosure:Deed in Lieu Cmplte, 2. First Legal Filed, 5. Sales Held} | Active Foreclosure | 表17 `summary_foreclosure_status` | Summary 展示 | ✅；填充 2330/122550=2% |
| `summary_completed_foreclosure` | 同表17 `summary_completed_foreclosure` | 视图计算 | `loan_fcl.summary_completed_foreclosure` | int | 实测全为 NULL | — | 表17 `summary_completed_foreclosure` | Summary 展示 | ✅；填充 0/122550=0% |
| `summary_foreclosure_bid_amount` | 同表17 `summary_foreclosure_bid_amount` | 视图计算 | `loan_fcl.summary_foreclosure_bid_amount` | decimal(32,16) | {$125,366.73, $390,832.50, $231,285.22, $136,392.44, $154,591.01, $543,305.96, $271,278.01, $90,000, $428,971.78}（9种） | $125,366.73 | 表17 `summary_foreclosure_bid_amount` | Summary 展示 | ✅；填充 254/122550=0% |
| `summary_srv_fc_bid_amount` | 同表17 `summary_srv_fc_bid_amount` | 视图计算 | `loan_fcl.summary_srv_fc_bid_amount` | decimal(32,16) | {$125,366.73, $390,832.50, $231,285.22, $136,392.44, $154,591.01, $543,305.96, $271,278.01, $90,000, $428,971.78}（9种） | $125,366.73 | 表17 `summary_srv_fc_bid_amount` | Summary 展示 | ✅；填充 254/122550=0% |
| `summary_foreclosure_sale_amount` | 同表17 `summary_foreclosure_sale_amount` | 视图计算 | `loan_fcl.summary_foreclosure_sale_amount` | decimal(32,16) | {$203,122.00, $357,200, $274,000, $165,900, $90,001.00, $400,000}（6种） | $203,122.00 | 表17 `summary_foreclosure_sale_amount` | Summary 展示 | ✅；填充 182/122550=0% |
| `summary_judicial_foreclosure` | 同表17 `summary_judicial_foreclosure` | 视图计算 | `loan_fcl.summary_judicial_foreclosure` | int | {0, 1}（2种） | 0 | 表17 `summary_judicial_foreclosure` | Summary 展示 | ✅；填充 2069/122550=2% |
| `summary_foreclosure_attorney` | 同表17 `summary_foreclosure_attorney` | 视图计算 | `loan_fcl.summary_foreclosure_attorney` | varchar(256) | {Lender Legal PLLC, McPhail Sanchez, LLC, Brock & Scott PLLC, Vylla Solutions, LLC} | Lender Legal PLLC | 表17 `summary_foreclosure_attorney` | Summary 展示 | ✅；填充 116/122550=0% |
| `summary_contested_litigation` | 同表17 `summary_contested_litigation` | 视图计算 | `loan_fcl.summary_contested_litigation` | int | {0, 1}（2种） | 0 | 表17 `summary_contested_litigation` | Summary 展示 | ✅；填充 2040/122550=2% |
| `summary_firm` | 同表17 `summary_firm` | 视图计算 | `loan_fcl.summary_firm` | varchar(256) | 文本，45种（样例 Albertelli Law … ZBS Law, LLP） | Albertelli Law | 表17 `summary_firm` | Summary 展示 | ✅；填充 2243/122550=2% |
| `summary_type` | 同表17 `summary_type` | 视图计算 | `loan_fcl.summary_type` | varchar(128) | {Non Judicial, Judicial} | Non Judicial | 表17 `summary_type` | Summary 展示 | ✅；填充 2069/122550=2% |
| `summary_sms_days_in_fcl` | 同表17 `summary_sms_days_in_fcl` | 视图计算 | `loan_fcl.summary_sms_days_in_fcl` | int | 7 ~ 531 | 7 | 表17 `summary_sms_days_in_fcl` | Summary 展示 | ✅；填充 1797/122550=1% |
| `summary_days_in_fcl` | 同表17 `summary_days_in_fcl` | 视图计算 | `loan_fcl.summary_days_in_fcl` | int | 7 ~ 739 | 7 | 表17 `summary_days_in_fcl` | Summary 展示 | ✅；填充 2214/122550=2% |
| `summary_current_step` | 同表17 `summary_current_step` | 视图计算 | `loan_fcl.summary_current_step` | varchar(128) | 文本，37种（样例 Acceleration Letter Sent … TSG Report Received） | Acceleration Letter Sent | 表17 `summary_current_step` | Summary 展示 | ✅；填充 2243/122550=2% |
| `summary_last_step_completed` | 同表17 `summary_last_step_completed` | 视图计算 | `loan_fcl.summary_last_step_completed` | varchar(256) | 文本，32种（样例 Answer Period Will Expire On … TSG Report Received） | Answer Period Will Expire On | 表17 `summary_last_step_completed` | Summary 展示 | ✅；填充 2069/122550=2% |
| `summary_last_step_completed_date` | 同表17 `summary_last_step_completed_date` | 视图计算 | `loan_fcl.summary_last_step_completed_date` | date | 2019-10-14 ~ 2026-03-12 | 2019-10-14 | 表17 `summary_last_step_completed_date` | Summary 展示 | ✅；填充 2069/122550=2% |
| `create_user` | 管理字段（同表17 `create_user`） | 视图计算 | `loan_fcl.create_user` | bigint | 实测全为 NULL | — | 表17 `create_user` | 审计/多租户 | ✅；填充 0/122550=0% |
| `create_dept` | 管理字段（同表17 `create_dept`） | 视图计算 | `loan_fcl.create_dept` | bigint | 实测全为 NULL | — | 表17 `create_dept` | 审计/多租户 | ✅；填充 0/122550=0% |
| `create_time` | 管理字段（同表17 `create_time`） | 视图计算 | `loan_fcl.create_time` | datetime | 实测全为 NULL | — | 表17 `create_time` | 审计/多租户 | ✅；填充 0/122550=0% |
| `update_user` | 管理字段（同表17 `update_user`） | 视图计算 | `loan_fcl.update_user` | bigint | 实测全为 NULL | — | 表17 `update_user` | 审计/多租户 | ✅；填充 0/122550=0% |
| `update_time` | 管理字段（同表17 `update_time`） | 视图计算 | `loan_fcl.update_time` | datetime | 实测全为 NULL | — | 表17 `update_time` | 审计/多租户 | ✅；填充 0/122550=0% |
| `status` | 管理字段（同表17 `status`） | 视图计算 | `loan_fcl.status` | int | {0}（1种） | 0 | 表17 `status` | 审计/多租户 | ✅；填充 2359/122550=2% |
| `is_deleted` | 是否软删除 | 视图计算 | 视图恒置 0 | int NOT NULL | {0}（1种） | 0 | — | 软删除标志 | ✅ 视图硬编码 0；填充 122550/122550=100% |
| `tenant_id` | 管理字段（同表17 `tenant_id`） | 视图计算 | `loan_fcl.tenant_id` | varchar(12) | {000000, 984018} | 000000 | 表17 `tenant_id` | 审计/多租户 | ✅；填充 2359/122550=2% |
| `var_notice_of_intent_days` | SLA 偏差天数（notice_of_intent；正=超期） | 视图计算 | `actual − 累计 target` | bigint | -624 ~ 781 | -624 | 本视图 actual_* − target_* | Variance 展示 | ✅ 视图实时计算；填充 145/122550=0% |
| `var_notice_of_intent_expire_days` | SLA 偏差天数（notice_of_intent_expire；正=超期） | 视图计算 | `actual − 累计 target` | bigint | 实测全为 NULL | — | 本视图 actual_* − target_* | Variance 展示 | ✅ 视图实时计算；填充 0/122550=0% |
| `var_approved_for_referral_days` | SLA 偏差天数（approved_for_referral；正=超期） | 视图计算 | `actual − 累计 target` | bigint | 实测全为 NULL | — | 本视图 actual_* − target_* | Variance 展示 | ✅ 视图实时计算；填充 0/122550=0% |
| `var_referred_to_attorney_days` | SLA 偏差天数（referred_to_attorney；正=超期） | 视图计算 | `actual − 累计 target` | bigint | 实测全为 NULL | — | 本视图 actual_* − target_* | Variance 展示 | ✅ 视图实时计算；填充 0/122550=0% |
| `var_referred_to_foreclosure_days` | SLA 偏差天数（referred_to_foreclosure；正=超期） | 视图计算 | `actual − 累计 target` | bigint | -2299 ~ 1122 | -2299 | 本视图 actual_* − target_* | Variance 展示 | ✅ 视图实时计算；填充 2346/122550=2% |
| `var_title_report_received_days` | SLA 偏差天数（title_report_received；正=超期） | 视图计算 | `actual − 累计 target` | bigint | 33 ~ 853 | 33 | 本视图 actual_* − target_* | Variance 展示 | ✅ 视图实时计算；填充 95/122550=0% |
| `var_preliminary_title_cleared_days` | SLA 偏差天数（preliminary_title_cleared；正=超期） | 视图计算 | `actual − 累计 target` | bigint | 65 ~ 542（25种） | 145 | 本视图 actual_* − target_* | Variance 展示 | ✅ 视图实时计算；填充 58/122550=0% |
| `var_first_legal_days` | SLA 偏差天数（first_legal；正=超期） | 视图计算 | `actual − 累计 target` | bigint | -2404 ~ 768 | -2404 | 本视图 actual_* − target_* | Variance 展示 | ✅ 视图实时计算；填充 1121/122550=1% |
| `var_service_days` | SLA 偏差天数（service；正=超期） | 视图计算 | `actual − 累计 target` | bigint | -2452 ~ 686 | -2452 | 本视图 actual_* − target_* | Variance 展示 | ✅ 视图实时计算；填充 557/122550=0% |
| `var_publication_days` | SLA 偏差天数（publication；正=超期） | 视图计算 | `actual − 累计 target` | bigint | 实测全为 NULL | — | 本视图 actual_* − target_* | Variance 展示 | ✅ 视图实时计算；填充 0/122550=0% |
| `var_judgement_hearing_set_days` | SLA 偏差天数（judgement_hearing_set；正=超期） | 视图计算 | `actual − 累计 target` | bigint | -772 ~ 557 | -772 | 本视图 actual_* − target_* | Variance 展示 | ✅ 视图实时计算；填充 271/122550=0% |
| `var_judgement_days` | SLA 偏差天数（judgement；正=超期） | 视图计算 | `actual − 累计 target` | bigint | -2224 ~ 658 | -2224 | 本视图 actual_* − target_* | Variance 展示 | ✅ 视图实时计算；填充 271/122550=0% |
| `var_sale_date_set_days` | SLA 偏差天数（sale_date_set；正=超期） | 视图计算 | `actual − 累计 target` | bigint | -991 ~ 516 | -991 | 本视图 actual_* − target_* | Variance 展示 | ✅ 视图实时计算；填充 517/122550=0% |
| `var_final_title_cleared_days` | SLA 偏差天数（final_title_cleared；正=超期） | 视图计算 | `actual − 累计 target` | bigint | -360 ~ 117（25种） | -280 | 本视图 actual_* − target_* | Variance 展示 | ✅ 视图实时计算；填充 58/122550=0% |
| `var_sale_date_held_days` | SLA 偏差天数（sale_date_held；正=超期） | 视图计算 | `actual − 累计 target` | bigint | -450 ~ 438 | -450 | 本视图 actual_* − target_* | Variance 展示 | ✅ 视图实时计算；填充 203/122550=0% |
| `var_total` | 总偏差合计 | 视图计算 | Σ(actual_* − target_*) | bigint | 实测全为 NULL | — | 本视图 var_* | 总 SLA 偏差 | ✅ 任一分项 NULL 则为 NULL；填充 0/122550=0% |
| `target_total` | 目标天数合计 | 视图计算 | Σ(target_*_days) | bigint NOT NULL | {637}（1种） | 637 | 本视图 target_* | 总目标=637 | ✅；填充 122550/122550=100% |
| `actual_total` | 实际历时合计 | 视图计算 | Σ(actual_*_days) | bigint | 实测全为 NULL | — | 本视图 actual_* | 总历时 | ✅ 任一分项 NULL 则为 NULL；填充 0/122550=0% |
