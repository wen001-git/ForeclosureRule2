# doc 19 — 5 个样例贷款 · FCL 全表全字段原始转储（Markdown 版）

> 本文件由 `scripts/build_fcl_sample_raw_dump_md.py` 自动生成，是 `docs/19_fcl_sample_loan_raw_dump.xlsx` 的 Markdown 对应版（内容一致）。

## 文档说明

- **文档目的**：把 5 个样例贷款在 BPS foreclosure 相关【所有表的全部字段】逐一列出，便于读者完整观察业务与数据的对应关系。doc 16 仅含各面板用到的部分字段，本表是其原始数据底座。
- **目标读者**：数据工程师 · 业务分析师 · 验证人员 · 接入工程师 · 未来 AI 会话
- **取数口径**：Newrez 源表 `dataasof=MAX`(每贷款)；`sync_fcl_stage_info` `fctrdt=MAX`；sync 基础表当前态；视图取每贷款 `fctrdt` 最新一行。日期统一 `YYYY-MM-DD`；空值显示 `—`。
- **排版**：1 行/贷款的表 → 转置（字段为行 × 5 贷款列）；多行/贷款的表（hold/lm/bk）→ 平铺（记录为行 × 全字段列）。

### 修订历史

| 日期 | 作者 | 版本 | 变更 | 关联 |
|---|---|---|---|---|
| 2026-06-03 | AI Agent (Claude Opus 4.8) | v1 | 初稿：12 节，与 doc 19 xlsx 一一对应；所有取值 DB 实测 | doc 16 · doc 19 xlsx |

## 一、表清单 / 索引

### Newrez 源数据表（5）

| 表 | 用途 | 列数 | 本dump命中 |
|---|---|---|---|
| newrez.portnewrezfc | FCL 主源表（时间线/状态/Hold槽/金额/律师） | 63 | 5/5 贷款 |
| newrez.portnewrezbk | 破产源表 | 60 | 5/5 贷款 |
| newrez.portnewrezlm | 损失缓解(LM)源表 | 56 | 5/5 贷款 |
| newrez.portnewrezgeneral | 通用源表（legalstatus / delinquency_status_mba 等） | 125 | 5/5 贷款 |
| newrez.portnewrezprop | 房产源表（propertystate 等） | 32 | 5/5 贷款 |

### BPS 直接对接表（5 基础表 + 1 视图）

| 表 / 视图 | 用途 | 列数 | 本dump行 |
|---|---|---|---|
| bpms_dev.sync_loan_foreclosure | Summary/Timeline/target 主表 | 72 | 4/5 贷款 |
| bpms_dev.sync_fcl_stage_info | 聚合 Stage/Timeline 表 | 57 | 4/5 贷款 |
| bpms_dev.sync_loan_foreclosure_hold | Hold 全历史（每次变更一行） | 15 | 16 行 |
| bpms_dev.sync_loan_foreclosure_loss_mitigation | LM 周期历史 | 22 | 20 行 |
| bpms_dev.sync_loan_foreclosure_bankruptcy | 破产记录 | 22 | 3 行 |
| bpms_dev.biz_data_view_loan_details_foreclosure（视图） | 详情页视图（actual/var 天数；取每贷款最新 fctrdt 一行） | 104 | 5/5 贷款 |

### 不纳入本转储的表（中间层 / dev 不存在）

| 表 | 原因 |
|---|---|
| newrez.portnewrezdatadic | 数值码解码字典；dev newrez 无此表，解码在 Redshift 完成 |
| port.basic_data_loan_foreclosure* | Redshift→MySQL 间的中间表，非源表也非 BPS 直接展示表 |
| port.portfunding | 融资池过滤表（JOIN 条件），非业务字段来源 |

### 样例贷款（5）

| # | loanid —— 选取理由 |
|---|---|
| Loan 1 | 7727000088 —— Judicial(FL)·JUDGEMENT·Hold×7·LM×9 |
| Loan 2 | 7727000672 —— Non-Judicial(MI)·REFERRAL |
| Loan 3 | 7727004200 —— Judicial(IL)·SALE |
| Loan 4 | 7727000065 —— BK + Hold×4 + 完结REO |
| Loan 5 | 7727000010 —— Chapter 13 Active BK（未入 FCL 管道） |

---

## portnewrezfc — newrez.portnewrezfc

> FCL 主源表（时间线/状态/Hold槽/金额/律师）。全 **63** 字段 · 取数口径：dataasof=MAX(每贷款) · 命中 5/5 贷款（无行的贷款列显示 `—`）。

| 字段 | 7727000088 | 7727000672 | 7727004200 | 7727000065 | 7727000010 |
|---|---|---|---|---|---|
| id | 1825466 | 1825025 | 1826610 | 1825487 | 1825480 |
| loanid | 7727000088 | 7727000672 | 7727004200 | 7727000065 | 7727000010 |
| dataasof | 2026-06-01 | 2026-06-01 | 2026-06-01 | 2026-06-01 | 2026-06-01 |
| shellpointloanid | 1031718838 | 1032761570 | 0688132141 | 1031718621 | 1031718692 |
| fcsetupdate | 2025-05-23 | 2026-03-09 | 2025-06-27 | 2025-02-03 | — |
| fcreferraldate | 2025-05-23 | 2026-03-09 | 2025-06-27 | 2025-02-03 | — |
| smsdaysinfc | 368 | 79 | 294 | 254 | — |
| daysinfc | 368 | 79 | 294 | 254 | — |
| demandsentdate | 2025-02-18 | 2025-11-17 | 2025-05-20 | 2024-08-12 | 2026-04-10 |
| demandexpirationdate | 2025-03-25 | 2025-12-22 | 2025-06-24 | 2024-09-18 | 2026-05-15 |
| fcstage | Post Sale Review (SCRA and PACER Check) | Pre-Sale Review 1 (SCRA and PACER Check) | Pre-Sale Review 1 (SCRA and PACER Check) | Post Sale Review (SCRA and PACER Check) | — |
| lastfcstepcompleted | Post Sale Review (SCRA and PACER Check) | First Publication | Sale Scheduled For | Post Sale Review (SCRA and PACER Check) | — |
| lastfcstepcompleteddate | 2026-05-26 | 2026-03-25 | 2026-05-19 | 2025-10-15 | — |
| fchold1description | Court Delay | Delinquency Review | Delinquency Review | Court Delay | — |
| fchold1startdate | 2026-04-09 | 2026-05-12 | 2026-04-17 | 2025-08-26 | — |
| fchold1enddate | 2026-04-26 | 2026-05-27 | 2026-04-17 | 2025-08-28 | — |
| fchold2description | Hearing Set | Loss Mitigation Workout | Hearing Set | Court Delay | — |
| fchold2startdate | 2026-03-16 | 2026-03-25 | 2026-01-29 | 2025-07-02 | — |
| fchold2enddate | 2026-04-07 | 2026-05-27 | 2026-02-13 | 2025-07-14 | — |
| fcjudgmenthearingscheduled | 2026-03-27 | — | 2026-04-13 | 2025-10-15 | — |
| fcjudgmententered | 2026-04-08 | — | 2026-02-13 | 2025-08-25 | — |
| fcscheduledsaledate | — | — | 2026-05-19 | — | — |
| fcsalehelddate | 2026-05-22 | — | — | 2025-10-14 | — |
| fcsaleamount | 200100.0000000000000000 | — | — | 357200.0000000000000000 | — |
| fcresults | REO | — | — | REO | — |
| firstlegaldate | 2025-06-13 | 2026-03-25 | 2025-07-21 | 2025-03-27 | — |
| servicecompletedate | 2025-07-18 | — | 2025-12-24 | 2025-05-03 | — |
| titleordereddate | — | — | — | 2025-11-13 | — |
| titlecleardate | — | — | — | — | — |
| titlereceiveddate | — | — | — | 2025-12-02 | — |
| fcremovaldesc | Process Complete | Loss Mitigation | Paid in Full | Process Complete | — |
| fcremovaldate | 2026-05-26 | 2026-05-27 | 2026-04-17 | 2025-10-15 | — |
| fccontestedflag | 0 | 0 | 0 | 0 | 0 |
| judicial | 1 | 0 | 1 | 1 | — |
| fcfirm | Kelley Kronenberg, P.A. | Orlans Law Group PLLC | Johnson, Blumberg & Associates, LLC | RAS (Primary) | — |
| jr_sr_lien_flag | 1 | 1 | 1 | 1 | — |
| fcbidamount | 301500.0000000000000000 | — | — | 390832.5000000000000000 | — |
| activefcflag | 0 | 0 | 0 | 0 | 0 |
| fchold1projectedenddate | 2026-04-29 | 2026-07-11 | 2026-06-16 | 2025-09-15 | — |
| fchold1comment | Delay Reason: Pending Ruling on Judgment, Hold Start Date: 2026-04-09, Date of Delay: 2026-04-06, Anticipated Resolution ETA: 2026-04-29, Additional Detail On Delay: We are pending judge's execution of the  proposed Order | Delinquency Review | Delinquency Review | Delay Reason: Pending Judges Decision/Ruling, Hold Start Date: 2025-08-26, Date of Delay: 2025-08-13, Anticipated Resolution ETA: 2025-09-15, Additional Detail On Delay: The Final Judgment was granted at NJT held 8/25/2025. At this time firm is pending the executed final Judgment with sale date scheduled to be docketed with the court a requirement to complete the Judgment entered.  | — |
| fchold2projectedenddate | 2026-04-06 | 2026-06-01 | 2026-02-13 | 2025-07-22 | — |
| fchold2comment | Hearing scheduled for 04/06/2026, Additional Detail: Plaintiff's Motion for Summary Judgment scheduled for 4.6.26. Please end court delay hold. Thanks | BRP Complete:  Complete Ack Sent:  RPP Approved: 03/24/2026 RPP Payments Due: 6 Last RPP Payment Made: 05/12/2026 Next Payment Due: 06/01/2026 | RID: 861849328; Judgment hearing scheduled for 2/13/26 | Delay Reason: Pending Judges Decision/Ruling, Hold Start Date: 2025-07-02, Date of Delay: 2025-07-01, Anticipated Resolution ETA: 2025-07-22, Additional Detail On Delay: Pending court's ruling on the Plaintiff's motion for clerk's default.  | — |
| holdmodified | 2026-04-27 | 2026-05-27 | 2026-04-17 | 2025-08-29 | — |
| holdmodified2 | 2026-04-07 | 2026-05-27 | 2026-02-13 | 2025-07-15 | — |
| create_time | 2026-06-02 | 2026-06-02 | 2026-06-02 | 2026-06-02 | 2026-06-02 |
| update_time | 2026-06-02 | 2026-06-02 | 2026-06-02 | 2026-06-02 | 2026-06-02 |
| dtdeedrecorded | — | — | — | 2025-10-28 | — |
| fcapprbidprice | 301500.0000000000000000 | — | — | 390832.5000000000000000 | — |
| fcl3rdpartyproceedsreceiveddate | — | — | — | — | — |
| investorloanid | 7727000088 | 7727000672 | 7727004200 | 7727000065 | 7727000010 |
| fchold3description | Court Delay | — | Service Delay | Bankruptcy Filed | — |
| fchold3startdate | 2026-01-16 | — | 2025-12-30 | 2025-05-06 | — |
| fchold3enddate | 2026-03-16 | — | 2026-01-23 | 2025-06-27 | — |
| fchold3projectedenddate | 2026-03-17 | — | 2026-01-23 | 2025-07-07 | — |
| fchold3comment | Delay Reason: Pending Hearing Date for Judgment, Hold Start Date: 2026-01-16, Date of Delay: 2026-01-19, Anticipated Resolution ETA: 2026-03-17, Additional Detail On Delay: We have reached out to the JA for dates in April and is pending a response. The JA had advised there were only limited dates. Pending response to proceed., Actions Taken by the Firm: Called the court, Most Recent Follow-Up Date: 02/20/2026, Additional Info:  We have reached out to the JA for dates in April and is pending a response. The JA had advised there were only limited dates. Pending response to proceed. | — | Due to title identifying the incorrect HOA, the new correct HOA had to be served.  The HOA was served 12/24/25 and the time period for the correct HOA to file their Answer does not expire until 1-23-2026.  See Step 9.  We cannot proceed to judgment until after 1-23-2026.   | CaseNumber: 2500228 Chapter: 7 Filed Date: 04/30/2025 POC Bar Date:  Post-Petition Due Date:  MFR Referral Date: 05/15/2025 MFR Filed Date: 06/10/2025 MFR Granted Date:  Dismissal Date: | — |
| holdmodified3 | 2026-03-17 | — | 2026-01-23 | 2025-06-27 | — |
| activejnrlienfcflag | 0 | 0 | 0 | 0 | 0 |
| currentmilestone | Sold | Closed | Closed | Sold | — |
| srlienmonitorflag | — | — | — | — | — |
| srliensalescheduleddate | — | — | — | — | — |
| srliensalehelddate | — | — | — | — | — |
| srliensaleresult | — | — | — | — | — |
| srliensaledate | — | — | — | — | — |

---

## portnewrezbk — newrez.portnewrezbk

> 破产源表。全 **60** 字段 · 取数口径：dataasof=MAX(每贷款) · 命中 5/5 贷款（无行的贷款列显示 `—`）。

| 字段 | 7727000088 | 7727000672 | 7727004200 | 7727000065 | 7727000010 |
|---|---|---|---|---|---|
| id | 1833486 | 1833045 | 1834630 | 1833507 | 1833500 |
| loanid | 7727000088 | 7727000672 | 7727004200 | 7727000065 | 7727000010 |
| dataasof | 2026-06-01 | 2026-06-01 | 2026-06-01 | 2026-06-01 | 2026-06-01 |
| shellpointloanid | 1031718838 | 1032761570 | 0688132141 | 1031718621 | 1031718692 |
| bkfileddate | — | — | — | 2025-04-30 | 2024-02-06 |
| bkstatus | — | — | — | 2 | 1 |
| bkremovalcode | — | — | — | 1 | — |
| bkremovaldate | — | — | — | 2025-07-29 | — |
| bkchapter | — | — | — | 7 | 13 |
| bkcasenumber | — | — | — | 2500228 | 2310152 |
| bkpostpetitionduedate | — | — | — | — | 2026-05-01 |
| prepetitionduedate | 2025-01-01 | 2026-02-01 | 2024-12-01 | 2024-03-01 | 2026-04-01 |
| pocfileddate | — | — | — | — | 2023-09-30 |
| dischargeddate | — | — | — | 2025-07-29 | — |
| dismisseddate | — | — | — | — | — |
| mfrfileddate | — | — | — | 2025-06-10 | — |
| mfrhearingdate | — | — | — | 2025-06-24 | — |
| mfrgranteddate | — | — | — | 2025-06-25 | — |
| trusteeassetflag | — | — | — | 0 | 0 |
| trusteeassetdate | — | — | — | 2025-06-01 | — |
| planconfirmationdate | — | — | — | — | 2024-07-11 |
| bkstage | — | — | — | 8 | 4 |
| bkfirm | — | — | — | — | Aldridge Pite, LLP |
| reaffirmationdate | — | — | — | — | — |
| trusteeabandonmentdate | — | — | — | — | — |
| pocreferreddate | — | — | — | — | — |
| pocbardate | — | — | — | — | 2024-04-16 |
| mfrreferred | — | — | — | 2025-05-15 | 2025-11-10 |
| mfrhearingresults | — | — | — | 3 | 0 |
| cramdowndatereferred | — | — | — | — | — |
| cramdownobjectionfileddate | — | — | — | — | — |
| cramdownresultdate | — | — | — | — | — |
| cramdownhearingresults | — | — | — | 0 | 0 |
| adversarialactionfileddate | — | — | — | — | — |
| adversarialhearingdate | — | — | — | — | — |
| adversarialresultdate | — | — | — | — | — |
| adversarialresults | — | — | — | 0 | 0 |
| cramdownflag | — | — | — | 0 | 0 |
| bankruptcypaymenttype | — | — | — | — | 1 |
| debtorintention | — | — | — | — | 1 |
| jointfilerflag | — | — | — | — | 0 |
| activebkflag | 0 | 0 | 0 | 0 | 1 |
| apocfileddate | — | — | — | — | — |
| apocreferraldate | — | — | — | — | — |
| reasonforapoc | — | — | — | — | — |
| attorney | — | — | — | — | — |
| create_time | 2026-06-02 | 2026-06-02 | 2026-06-02 | 2026-06-02 | 2026-06-02 |
| update_time | 2026-06-02 | 2026-06-02 | 2026-06-02 | 2026-06-02 | 2026-06-02 |
| bkrepayplanpaymentcount | — | — | — | — | 60 |
| bksourceoffundscode | — | — | — | — | — |
| bkpoccourtreceiveddate | — | — | — | — | — |
| bkrcurrentstatusdate | — | — | — | — | 2026-05-26 |
| bkborrowerintent | — | — | — | — | 1 |
| bkpostpetitionpaymentcurrent | — | — | — | — | 2192.0000000000000000 |
| bkcramdownpercent | — | — | — | — | — |
| bkpostsuspensebalance | — | — | — | — | — |
| bkpresuspensebalance | — | — | — | — | — |
| investorloanid | 7727000088 | 7727000672 | 7727004200 | 7727000065 | 7727000010 |
| bkfilingstate | — | — | — | WV | FL |
| bkfilingregion | — | — | — | Northern District of WV (Martinsburg) | Northern District of Florida, Gainesville Division                     |

---

## portnewrezlm — newrez.portnewrezlm

> 损失缓解(LM)源表。全 **56** 字段 · 取数口径：dataasof=MAX(每贷款) · 命中 5/5 贷款（无行的贷款列显示 `—`）。

| 字段 | 7727000088 | 7727000672 | 7727004200 | 7727000065 | 7727000010 |
|---|---|---|---|---|---|
| id | 1822162 | 1821721 | 1823306 | 1822183 | 1822176 |
| loanid | 7727000088 | 7727000672 | 7727004200 | 7727000065 | 7727000010 |
| dataasof | 2026-06-01 | 2026-06-01 | 2026-06-01 | 2026-06-01 | 2026-06-01 |
| shellpointloanid | 1031718838 | 1032761570 | 0688132141 | 1031718621 | 1031718692 |
| hardshiptype | 11 | 11 | 20 | 11 | 12 |
| borrowerintention | — | — | — | — | — |
| lmdeal | 7 | 4 | 1 | 2 | 1 |
| dealstartdate | 2026-02-17 | 2026-02-25 | 2026-01-06 | 2025-07-01 | 2026-04-16 |
| daysindeal | 66 | 96 | 27 | 0 | 12 |
| lmstatus | 112 | 25 | 5 | 166 | 112 |
| statusstartdate | 2026-04-22 | 2026-03-24 | 2026-01-14 | 2024-11-26 | 2026-04-23 |
| daysinstatus | 2 | 69 | 19 | 217 | 5 |
| lmprogram | 10 | 29 | 496 | 21 | 498 |
| lmdecision | 6 | 99 | 10 | 11 | 6 |
| lmremovaldate | 2026-04-24 | — | 2026-02-02 | 2025-07-01 | 2026-04-28 |
| denialreason | 40 | — | — | — | 124 |
| forbearanceagreementdate | — | — | 2025-02-01 | — | — |
| forbearancedatecompleted | — | — | 2025-05-01 | — | — |
| forbearancebeginningduedate | — | — | 2025-02-01 | — | — |
| forbearanceendingduedate | — | — | 2025-04-30 | — | — |
| forbearancenumberofmonths | — | — | 3 | — | — |
| forbearancestatus | — | — | 4 | — | — |
| forbearancetype | — | — | 61 | — | — |
| trialagreementdate | — | — | — | — | — |
| trialdatecompleted | — | — | — | — | — |
| trialbeginningduedate | — | — | — | — | — |
| trialendingduedate | — | — | — | — | — |
| trialnumberofmonths | — | — | — | — | — |
| trialstatus | — | — | — | — | — |
| repaymentagreementdate | — | 2026-03-24 | — | — | — |
| repaymentstartdate | — | 2026-05-01 | — | — | — |
| repaymentenddate | — | 2026-10-31 | — | — | — |
| repaymenttype | — | 4 | — | — | — |
| repaymentstatus | — | 1 | — | — | — |
| repaymentplandownpmt | — | 9000.0000000000000000 | — | — | — |
| repaymentplandownpmtdate | — | 2026-04-24 | — | — | — |
| pradate1 | — | — | — | — | — |
| praamount1 | — | — | — | — | — |
| pradate2 | — | — | — | — | — |
| praamount2 | — | — | — | — | — |
| pradate3 | — | — | — | — | — |
| praamount3 | — | — | — | — | — |
| activelmflag | 0 | 1 | 0 | 0 | 0 |
| create_time | 2026-06-02 | 2026-06-02 | 2026-06-02 | 2026-06-02 | 2026-06-02 |
| update_time | 2026-06-02 | 2026-06-02 | 2026-06-02 | 2026-06-02 | 2026-06-02 |
| lossmitmodtermsmodifiedtermextensionmonths | — | — | — | — | — |
| deferment_flag | — | — | — | — | — |
| deferment_amount | — | — | — | — | — |
| number_pi_payments_deferred | — | — | — | — | — |
| shortsalenetproceedsamount | — | — | — | — | — |
| shortsalecontractofferamount | — | — | — | — | — |
| appealperiodexpirationdate | — | — | — | — | 2026-05-11 |
| lossmitmodpreviouslydeferredcapitalizedamount | — | — | — | — | — |
| deferment_date | — | — | — | — | — |
| denialletterdate | 2026-04-23 | 2025-08-12 | — | — | 2026-04-27 |
| investorloanid | 7727000088 | 7727000672 | 7727004200 | 7727000065 | 7727000010 |

---

## portnewrezgeneral — newrez.portnewrezgeneral

> 通用源表（legalstatus / delinquency_status_mba 等）。全 **125** 字段 · 取数口径：dataasof=MAX(每贷款) · 命中 5/5 贷款（无行的贷款列显示 `—`）。

| 字段 | 7727000088 | 7727000672 | 7727004200 | 7727000065 | 7727000010 |
|---|---|---|---|---|---|
| id | 1825844 | 1825403 | 1826988 | 1825865 | 1825858 |
| loanid | 7727000088 | 7727000672 | 7727004200 | 7727000065 | 7727000010 |
| dataasof | 2026-06-01 | 2026-06-01 | 2026-06-01 | 2026-06-01 | 2026-06-01 |
| shellpointloanid | 1031718838 | 1032761570 | 0688132141 | 1031718621 | 1031718692 |
| investorid | BI2726 | BI2725 | BIRTT1 | TT1REO | BI2726 |
| investorloanid | 7727000088 | 7727000672 | 7727004200 | 7727000065 | 7727000010 |
| priorservicerloannumber | 9010021155 | 32288235 | 3260057082 | 9014327961 | 9014059868 |
| boarddate | 2024-07-04 | 2024-07-04 | 2024-02-07 | 2024-07-04 | 2024-07-04 |
| acquisitiondate | 2024-07-02 | 2024-07-02 | 2024-02-01 | 2024-07-02 | 2024-07-02 |
| acquisitionbalance | 318856.0900000000000000 | 421270.3900000000000000 | 455612.0600000000000000 | 470399.5100000000000000 | 271997.4700000000000000 |
| mbadelinquency | 14 | 6 | 15 | 14 | 9 |
| delinqstatatboarding | 3 | 4 | 3 | 6 | 10 |
| lienposition | 1 | 1 | 1 | 1 | 1 |
| loantype | 0 | 0 | 0 | 2 | 2 |
| loanpurpose | 1 | 1 | 1 | 3 | 3 |
| documentationtype | 0 | 0 | 0 | 0 | 0 |
| dateinactive | — | — | 2026-04-16 | — | — |
| currentinterestrate | 0.0662500000000000 | 0.0987500000000000 | 0.0275000000000000 | 0.0425000000000000 | 0.0362500000000000 |
| originalterm | 360 | 360 | 360 | 360 | 360 |
| originalnotedate | 2022-09-20 | 2022-09-15 | 2017-05-16 | 2022-05-24 | 2022-02-17 |
| originalmaturitydate | 2052-10-01 | 2052-10-01 | 2047-06-01 | 2052-06-01 | 2052-03-01 |
| originalamt | 324900.0000000000000000 | 425000.0000000000000000 | 532000.0000000000000000 | 484200.0000000000000000 | 282335.0000000000000000 |
| currentmaturitydate | 2052-10-01 | 2052-10-01 | 2047-06-01 | 2052-06-01 | 2052-03-01 |
| amortizationterm | 360 | 360 | 360 | 360 | 360 |
| remainingterm | 334 | 321 | 0 | 340 | 312 |
| otherliens | — | — | — | — | — |
| otherliensbalance | — | — | — | — | — |
| legalstatus | REO | — | FCBU | REO | BK13 |
| warningstatus | — | — | AttyCons | ICC-REO | — |
| isattorneyrepresented | 0 | 0 | 0 | 0 | 0 |
| issoldiersandsailors | 0 | 0 | 0 | 0 | 0 |
| isloanlitigated | 0 | 0 | 0 | 0 | 0 |
| isescrowed | 1 | 1 | 1 | 1 | 1 |
| femaarea | 0 | 0 | 0 | 0 | 0 |
| femaaffect | 0 | 0 | 0 | 0 | 0 |
| balloonflag | 0 | 0 | 0 | 0 | 0 |
| balloondate | — | — | — | — | — |
| prepaymentpenaltyflag | 0 | 0 | 0 | 0 | 0 |
| prepaymentpenaltyterm | 0 | 0 | 0 | 0 | 0 |
| prepaymentpenaltyfee | 0 | 0 | 0 | 0 | 0 |
| chargeoff | 0 | 0 | 0 | 0 | 0 |
| chargeoffdate | — | — | — | — | — |
| chargeoffamount | — | — | — | — | — |
| payoffrequested | 0 | 0 | 1 | 0 | 0 |
| payoffrequestdate | — | — | 2026-03-23 | — | — |
| mersid | 101229710000033408 | 100859730000132976 | — | 100661190012111072 | 100661190011370480 |
| servicefeepercent | 0E-16 | 0E-16 | 0E-16 | 0E-16 | 0E-16 |
| servicefeedollars | 0E-16 | 0E-16 | 0E-16 | 0E-16 | 0E-16 |
| interestmethod | 0 | 0 | 0 | 0 | 0 |
| negamflag | 0 | 0 | 0 | 0 | 0 |
| borrowerdeceasedflag | 0 | 0 | 0 | 0 | 0 |
| coborrowerdeceasedflag | 0 | — | — | — | — |
| priorservicer | Specialized Loan Servicing | Specialized Loan Servicing | Associated Bank | Specialized Loan Servicing | Specialized Loan Servicing |
| foreignnationalflag | 0 | 0 | 0 | 0 | 0 |
| min_status | 1 | 1 | — | 1 | 1 |
| origorgid | 1012297 | 1008597 |  | 1006611 | 1006611 |
| origorgname | Approved Mortgage Source, LLC | IMPAC Mortgage Corp. | — | Home Point Financial Corporation | — |
| servicerorgid | 1007544 | 1007544 |  | 1007544 | 1003225 |
| subservorgid |  |  |  |  |  |
| ppc1_id | — | — | — | — | — |
| investorname | TRESTLE TITLING TRUST-1 (TRUSTEE) | TRESTLE TITLING TRUST -1 | Trustee for Trestle Titling Trust-1 | Trestle Titling Trust-1 | TRESTLE TITLING TRUST-1 (TRUSTEE) |
| min_number | 1.012297100000334e17 | 1.0085973000013298e17 | — | 1.0066119001211107e17 | 1.0066119001137048e17 |
| registerstatus | Assigned For Default or BK | Assigned For Default or BK | — | Assigned For Default or BK | Inactive |
| deactreason | FC-BK | FC-BK | — | FC-BK | — |
| securitization | — | — | — | 	N | — |
| poolnumber | 0 | 0 | 0 | 0 | 0 |
| investororgid | 1012111 | 1012111 |  | 1012111 | 1012111 |
| is_hpml | 0 | 0 | 0 | 0 | 0 |
| investmentproperty | 0 | 0 | 0 | 0 | 0 |
| hasadditionalcollateral | 0 | 0 | 0 | 0 | 0 |
| creditorname | WILMINGTON SAVINGS FUND SOCIETY, FSB, not in its individual capacity, but solely as Trustee for Trestle Titling Trust-1 | TRESTLE TITLING TRUST -1 | WILMINGTON SAVINGS FUND SOCIETY, FSB, not in its individual capacity, but solely as Trustee for Trestle Titling Trust-1 | Trestle Titling Trust-1 | WILMINGTON SAVINGS FUND SOCIETY, FSB, not in its individual capacity, but solely as Trustee for Trestle Titling Trust-1 |
| vestingname | TRESTLE REO- 1 LLC | TRESTLE REO- 1 LLC | TRESTLE REO- 1 LLC | TRESTLE REO- 1 LLC | TRESTLE REO- 1 LLC |
| memberid | — | — | — | — | — |
| welcomeletter | — | — | 2024-02-12 | — | — |
| tilanotice | — | — | 2024-07-17 | — | — |
| debenturerate | 3.2500000000000000 | 3.2500000000000000 | 2.7500000000000000 | 1.8750000000000000 | 1.8750000000000000 |
| reasonfordefault | Reduction in Borrower's Income | — | — | Unable to Contact Borrower | — |
| custodianname | DC-WT | DC-WT | DC-WT | DC-WT | DC-WT |
| custodiancollateralid | 8001883579 | 3111022026 | 7727004200 | 7001810280 | 6001690164 |
| delinquency_status_mba | REO | 120-149 DPD | Full Payoff | REO | Performing Bankruptcy |
| create_time | 2026-06-02 | 2026-06-02 | 2026-06-02 | 2026-06-02 | 2026-06-02 |
| update_time | 2026-06-02 | 2026-06-02 | 2026-06-02 | 2026-06-02 | 2026-06-02 |
| eoy_1099c_cancelled_date_reported | — | — | — | — | — |
| loanscraflag | — | — | — | — | — |
| srlienstatuscode | — | — | — | — | — |
| srlienname | — | — | — | — | — |
| srlienduedate | — | — | — | — | — |
| srlienstatusdesc | — | — | — | — | — |
| prepaypenaltyenddate | — | — | — | — | — |
| loanscrapaymenteffectivedate | — | — | — | — | — |
| cdfi | 0 | 0 | 0 | 0 | 0 |
| investorchargeoff | 0 | 0 | 0 | 0 | 0 |
| eoy_1099c_flag | — | — | — | — | — |
| disasterdesignationdate | — | — | — | — | — |
| inauctionflag | 0 | 0 | 0 | 1 | 0 |
| fhavapmicasenumber | — | — | 1000201256 | 171762357107 | 171762373396 |
| loanscraenddate | — | — | — | — | — |
| borrowerprimarymilitarystatuscode | 0 | 0 | 0 | 0 | 0 |
| borrowerprimarymilitarystatuscodedesc | Not Maintained | Not Maintained | Not Maintained | Not Maintained | Not Maintained |
| dscr | 0 | 0 | 0 | 0 | 0 |
| loanscrastartdate | — | — | — | — | — |
| disastername | — | — | — | — | — |
| bridgeloan | 0 | 0 | 0 | 0 | 0 |
| secondhome | 0 | 0 | 0 | 0 | 0 |
| priorservicername | Specialized Loan Servicing | Specialized Loan Servicing | Associated Bank | Specialized Loan Servicing | Specialized Loan Servicing |
| disasterimpactcreateddate | — | — | — | — | — |
| investorchargeoffdate | — | — | — | — | — |
| disasterdeclarationnumber | — | — | — | — | — |
| lienseniorbalanceprincipalcurrent | — | — | — | — | — |
| loanscrainterestrate | — | — | — | — | — |
| loanscrapipayment | — | — | — | — | — |
| eoy_1099c_cancelled_amount_reported | — | — | — | — | — |
| otsdelinquency | REO | 120-149 DPD | Full Payoff | REO | Performing Bankruptcy |
| leadbilldays | — | — | — | — | — |
| guarantyfeepercent | 0E-16 | 0E-16 | 0E-16 | 0E-16 | 0E-16 |
| acquiredduedate | 2024-07-01 | 2024-05-01 | 2024-01-01 | 2024-03-01 | 2024-03-01 |
| interestpaidthroughdate | 2024-12-01 | 2026-01-01 | 2024-11-01 | 2024-02-01 | 2026-03-01 |
| srstatus | — | — | — | — | — |
| enoteflag | 0 | 0 | 0 | 0 | 0 |
| billingstatementdate | 2026-05-18 | 2026-05-18 | 2026-03-18 | 2025-07-21 | 2026-05-18 |
| vrmflag | 0 | 0 | 0 | 0 | 0 |
| pendinginvestoridtransfer | 0 | 0 | 0 | 0 | 0 |
| newinvestorid | — | — | — | — | — |
| amltype | 0 | 0 | 0 | 0 | 0 |
| successorservicer | — | — | — | — | — |

---

## portnewrezprop — newrez.portnewrezprop

> 房产源表（propertystate 等）。全 **32** 字段 · 取数口径：dataasof=MAX(每贷款) · 命中 5/5 贷款（无行的贷款列显示 `—`）。

| 字段 | 7727000088 | 7727000672 | 7727004200 | 7727000065 | 7727000010 |
|---|---|---|---|---|---|
| id | 1813224 | 1812783 | 1814368 | 1813245 | 1813238 |
| loanid | 7727000088 | 7727000672 | 7727004200 | 7727000065 | 7727000010 |
| dataasof | 2026-06-01 | 2026-06-01 | 2026-06-01 | 2026-06-01 | 2026-06-01 |
| shellpointloanid | 1031718838 | 1032761570 | 0688132141 | 1031718621 | 1031718692 |
| propertyaddressline1 | 21 LK CHARLES LN | W 3120 SCHLOSSER RD | 13977 W EMMA LN | 2331 SW FREEMAN ST | 19801 OLD BELLAMY RD |
| propertyaddressline2 | — | — | — | — | — |
| propertycity | PALM COAST | MORAN | METTAWA | PORT SAINT LUCIE | ALACHUA |
| propertystate | FL | MI | IL | FL | FL |
| propertyzip | 32137 | 49760 | 60045 | 34953 | 32615 |
| propertycounty | FLAGLER | MACKINAC | LAKE | ST. LUCIE | ALACHUA |
| propertytype | 20 | 20 | 39 | 20 | 20 |
| currentoccupancy | 2 | 0 | 0 | 2 | 0 |
| currentoccupancydate | 2026-05-26 | — | — | 2026-05-23 | 2026-01-28 |
| mostrecentvalue | 335000.0000000000000000 | 350000.0000000000000000 | 855000.0000000000000000 | 455900.0000000000000000 | 320750.0000000000000000 |
| mostrecentvaluedate | 2026-03-30 | 2026-04-29 | 2026-03-05 | 2026-03-30 | 2022-12-06 |
| valuationmethod | 4 | 4 | 2 | 2 | 2 |
| bpoprovider | — | — | 10 | — | — |
| originalpropertyvalue | 343000.0000000000000000 | 508000.0000000000000000 | 563000.0000000000000000 | 538000.0000000000000000 | 325000.0000000000000000 |
| originalpropertyvaluedate | 2022-08-01 | 2022-05-01 | — | 2022-05-01 | 2022-02-01 |
| vacancyflag | 1 | 0 | 0 | 1 | 0 |
| originalltv | 0.9472000000000000 | 0.8366000000000000 | 0.9449000000000000 | 0.9000000000000000 | 0.8687000000000000 |
| currentltv | 0.9459000000000000 | 1.1890000000000000 | 0E-16 | 1.0318000000000000 | 0.8103000000000000 |
| numberofunits | 1 | 1 | 1 | 1 | 1 |
| mostrecentbpovalue | 260000.0000000000000000 | 539900.0000000000000000 | 855000.0000000000000000 | 455900.0000000000000000 | 320750.0000000000000000 |
| mostrecentbpovaluedate | 2026-03-18 | 2026-04-25 | 2026-03-05 | 2026-03-30 | 2022-12-06 |
| taxservice | First American Tax Service | First American Tax Service | First American Tax Service | First American Tax Service | First American Tax Service |
| datesenttotaxoutsource | 2024-07-11 | 2024-07-23 | 2024-02-14 | 2024-07-11 | 2024-07-11 |
| create_time | 2026-06-02 | 2026-06-02 | 2026-06-02 | 2026-06-02 | 2026-06-02 |
| update_time | 2026-06-02 | 2026-06-02 | 2026-06-02 | 2026-06-02 | 2026-06-02 |
| originaloccupancy | Primary Residence | Primary Residence | Primary Residence | Primary Residence | Primary Residence |
| investorloanid | 7727000088 | 7727000672 | 7727004200 | 7727000065 | 7727000010 |
| countycode | 35 | 97 | 97 | 111 | 1 |

---

## sync_loan_foreclosure — bpms_dev.sync_loan_foreclosure

> Summary/Timeline/target 主表。全 **72** 字段 · 取数口径：当前态(1行/贷款) · 命中 4/5 贷款（无行的贷款列显示 `—`）。

| 字段 | 7727000088 | 7727000672 | 7727004200 | 7727000065 | 7727000010 |
|---|---|---|---|---|---|
| id | 199 | 275 | 198 | 82 | — |
| bid_id | HMP002 | IMPAC001 | BOA002 | HMP002 | — |
| funding_id | HMP002 | IMPAC001 | BOA002 | HMP002 | — |
| loanid | 7727000088 | 7727000672 | 7727004200 | 7727000065 | — |
| svcloanid | 1031718838 | 1032761570 | 0688132141 | 1031718621 | — |
| servicer | Newrez | Newrez | Newrez | Newrez | — |
| timeline_notice_of_intent_date | — | — | — | — | — |
| timeline_notice_of_intent_end_date | — | — | — | — | — |
| timeline_approved_for_referral_date | — | — | — | — | — |
| timeline_referred_to_attorney_date | — | — | — | — | — |
| timeline_referred_to_foreclosure_date | 2025-05-23 | 2026-03-09 | 2025-06-27 | 2025-02-03 | — |
| timeline_title_report_received_date | — | — | — | 2025-12-02 | — |
| timeline_preliminary_title_cleared_date | — | — | — | — | — |
| timeline_first_legal_date | 2025-06-13 | — | 2025-07-21 | 2025-03-27 | — |
| timeline_service_date | 2025-07-18 | — | 2025-12-24 | 2025-05-03 | — |
| timeline_publication_date | — | — | — | — | — |
| timeline_judgement_hearing_set_date | 2026-03-06 | — | 2026-02-13 | 2025-07-15 | — |
| timeline_judgement_date | 2026-07-15 | — | 2026-04-13 | 2025-10-15 | — |
| timeline_sale_date_projected_date | — | — | 2026-05-19 | — | — |
| timeline_sale_date_set_date | — | — | 2026-02-19 | — | — |
| timeline_final_title_cleared_date | — | — | — | — | — |
| timeline_sale_date_held_date | — | — | — | 2025-10-14 | — |
| timeline_foreclosure_completed_date | — | — | — | — | — |
| timeline_third_party_sold_date_date | — | — | — | — | — |
| timeline_third_party_proceeds_received_date | — | — | — | — | — |
| target_notice_of_intent_days | 30 | 30 | 30 | 30 | — |
| target_notice_of_intent_expired_days | 90 | 90 | 90 | 90 | — |
| target_approved_for_referral_days | 30 | 30 | 30 | 30 | — |
| target_referred_to_attorney_days | 1 | 1 | 1 | 1 | — |
| target_referred_to_foreclosure_days | 1 | 1 | 1 | 1 | — |
| target_title_report_received_days | 30 | 30 | 30 | 30 | — |
| target_preliminary_title_cleared_days | 30 | 30 | 30 | 30 | — |
| target_first_legal_days | 120 | 120 | 120 | 120 | — |
| target_service_days | 90 | 90 | 90 | 90 | — |
| target_publication_days | 30 | 30 | 30 | 30 | — |
| target_judgement_hearing_set_days | 120 | 120 | 120 | 120 | — |
| target_judgement_days | 30 | 30 | 30 | 30 | — |
| target_sale_date_set_days | 30 | 30 | 30 | 30 | — |
| target_final_title_cleared_days | 5 | 5 | 5 | 5 | — |
| target_sale_date_held_days | 0 | 0 | 0 | 0 | — |
| variance_active_bankruptcy | — | — | — | — | — |
| variance_completed_bankruptcy | — | — | — | — | — |
| variance_estimated_hold_days | — | — | — | — | — |
| variance_bankruptcies | — | — | — | — | — |
| bid_approval_status | — | — | — | — | — |
| bid_approval_sale_date | — | — | — | — | — |
| bid_approval_bid_amount | — | — | — | 390832.4999999999967232 | — |
| bid_approval_loan_resolution_holods | — | — | — | — | — |
| summary_servicer_number | — | — | — | — | — |
| summary_foreclosure_status | Active Foreclosure | Active Foreclosure | Active Foreclosure | Closed Foreclosure:Process Complete | — |
| summary_completed_foreclosure | — | — | — | — | — |
| summary_foreclosure_bid_amount | — | — | — | 390832.4999999999967232 | — |
| summary_srv_fc_bid_amount | — | — | — | 390832.4999999999967232 | — |
| summary_foreclosure_sale_amount | — | — | — | 357200.0000000000000000 | — |
| summary_judicial_foreclosure | 1 | 0 | 1 | 1 | — |
| summary_foreclosure_attorney | — | — | — | — | — |
| summary_contested_litigation | 0 | 0 | 0 | 0 | — |
| summary_firm | Kelley Kronenberg, P.A. | Orlans Law Group PLLC | Johnson, Blumberg & Associates, LLC | RAS (Primary) | — |
| summary_type | Judicial | Non Judicial | Judicial | Judicial | — |
| summary_sms_days_in_fcl | 298 | 8 | 263 | 257 | — |
| summary_days_in_fcl | 298 | 8 | 263 | 257 | — |
| summary_current_step | Judgment Entered | Title Report Received | Pre-Sale Review 1 (SCRA and PACER Check) | Post Sale Review (SCRA and PACER Check) | — |
| summary_last_step_completed | Motion for Judgment Sent to Court | File Received By Attorney | Are We Proceeding with a Consent Judgment  | Post Sale Review (SCRA and PACER Check) | — |
| summary_last_step_completed_date | 2025-12-17 | 2026-03-09 | 2026-02-17 | 2025-10-15 | — |
| create_user | — | — | — | — | — |
| create_dept | — | — | — | — | — |
| create_time | — | — | — | — | — |
| update_user | — | — | — | — | — |
| update_time | — | — | — | — | — |
| status | 0 | 0 | 0 | 0 | — |
| is_deleted | 0 | 0 | 0 | 0 | — |
| tenant_id | 000000 | 000000 | 000000 | 000000 | — |

---

## sync_fcl_stage_info — bpms_dev.sync_fcl_stage_info

> 聚合 Stage/Timeline 表。全 **57** 字段 · 取数口径：fctrdt=MAX(每贷款) · 命中 4/5 贷款（无行的贷款列显示 `—`）。

| 字段 | 7727000088 | 7727000672 | 7727004200 | 7727000065 | 7727000010 |
|---|---|---|---|---|---|
| id | 303008 | 303012 | 303143 | 305599 | — |
| stage | JUDGEMENT | REFERRAL | SALE | JUDGEMENT | — |
| fctrdt | 2026-03-13 | 2026-03-13 | 2026-03-13 | 2025-10-14 | — |
| loanid | 7727000088 | 7727000672 | 7727004200 | 7727000065 | — |
| group | FCL | FCL | FCL | REO | — |
| servicer | Newrez | Newrez | Newrez | Newrez | — |
| state | FL | MI | IL | FL | — |
| judicial | Y | N | Y | Y | — |
| demand_start_date | 2025-02-18 | 2025-11-17 | 2025-05-20 | 2024-08-12 | — |
| demand_end_date | 2025-03-25 | 2025-12-22 | 2025-06-24 | 2024-09-18 | — |
| demand_stage_days | 391 | 119 | 300 | 431 | — |
| demand_in_lm_days | 27 | 19 | 164 | — | — |
| demand_on_hold_days | 59 | — | — | — | — |
| noi_start_date | — | — | — | — | — |
| noi_end_date | — | — | — | — | — |
| noi_stage_days | — | — | — | — | — |
| noi_in_lm_days | — | — | — | — | — |
| noi_on_hold_days | — | — | — | — | — |
| referral_start_date | 2025-05-23 | 2026-03-09 | 2025-06-27 | 2025-02-03 | — |
| referral_end_date | 2025-06-13 | — | 2025-07-21 | 2025-03-27 | — |
| referral_stage_days | 22 | 7 | 25 | 53 | — |
| referral_in_lm_days | — | — | — | — | — |
| referral_on_hold_days | — | — | — | — | — |
| first_legal_start_date | 2025-06-13 | — | 2025-07-21 | 2025-03-27 | — |
| first_legal_end_date | 2025-07-18 | — | 2025-12-24 | 2025-05-03 | — |
| first_legal_stage_days | 36 | — | 157 | 38 | — |
| first_legal_in_lm_days | — | — | 83 | — | — |
| first_legal_on_hold_days | — | — | — | — | — |
| first_legal_date_history | — | — | — | — | — |
| service_start_date | 2025-07-18 | — | 2025-12-24 | 2025-05-03 | — |
| service_end_date | 2026-03-06 | — | 2026-02-13 | 2025-07-15 | — |
| service_stage_days | 232 | — | 52 | 74 | — |
| service_in_lm_days | 18 | — | — | — | — |
| service_on_hold_days | 50 | — | — | — | — |
| publication_start_date | — | — | — | — | — |
| publication_end_date | — | — | — | — | — |
| publication_stage_days | — | — | — | — | — |
| publication_in_lm_days | — | — | — | — | — |
| publication_on_hold_days | — | — | — | — | — |
| judgement_start_date | 2026-07-15 | — | 2026-04-13 | 2025-10-15 | — |
| judgement_end_date | — | — | — | — | — |
| to_judgement_days | 122 | — | 29 | 0 | — |
| judgement_in_lm_days | — | — | — | — | — |
| judgement_on_hold_days | — | — | — | — | — |
| sale_start_date | — | — | 2026-05-19 | — | — |
| sale_end_date | — | — | — | — | — |
| to_sale_days | — | — | 65 | — | — |
| sale_in_lm_days | — | — | — | — | — |
| sale_on_hold_days | — | — | — | — | — |
| create_time | 2026-03-16 | 2026-03-16 | 2026-03-16 | 2026-03-16 | — |
| update_time | 2026-03-16 | 2026-03-16 | 2026-03-16 | 2026-03-16 | — |
| create_user | — | — | — | — | — |
| create_dept | — | — | — | — | — |
| update_user | — | — | — | — | — |
| status | 0 | 0 | 0 | 0 | — |
| is_deleted | 0 | 0 | 0 | 0 | — |
| tenant_id | 000000 | 000000 | 000000 | 000000 | — |

---

## view_loan_details — bpms_dev.biz_data_view_loan_details_foreclosure

> 详情页视图（actual/var 天数；取每贷款最新 fctrdt 一行）。全 **104** 字段 · 取数口径：每贷款 fctrdt 最新一行 · 命中 5/5 贷款（无行的贷款列显示 `—`）。

| 字段 | 7727000088 | 7727000672 | 7727004200 | 7727000065 | 7727000010 |
|---|---|---|---|---|---|
| id | 199 | 275 | 198 | 82 | — |
| loanid | 7727000088 | 7727000672 | 7727004200 | 7727000065 | 7727000010 |
| svcloanid | 1031718838 | 1032761570 | 0688132141 | 1031718621 | 1031718692 |
| fctrdt | 2026-03-01 | 2026-03-01 | 2026-03-01 | 2026-03-01 | 2026-03-01 |
| nextduedate | 2025-01-01 | 2025-11-01 | 2024-12-01 | 2024-03-01 | 2025-10-01 |
| timeline_notice_of_intent_date | — | — | — | — | — |
| timeline_notice_of_intent_end_date | — | — | — | — | — |
| timeline_approved_for_referral_date | — | — | — | — | — |
| timeline_referred_to_attorney_date | — | — | — | — | — |
| timeline_referred_to_foreclosure_date | 2025-05-23 | 2026-03-09 | 2025-06-27 | 2025-02-03 | — |
| timeline_title_report_received_date | — | — | — | 2025-12-02 | — |
| timeline_preliminary_title_cleared_date | — | — | — | — | — |
| timeline_first_legal_date | 2025-06-13 | — | 2025-07-21 | 2025-03-27 | — |
| timeline_service_date | 2025-07-18 | — | 2025-12-24 | 2025-05-03 | — |
| timeline_publication_date | — | — | — | — | — |
| timeline_judgement_hearing_set_date | 2026-03-06 | — | 2026-02-13 | 2025-07-15 | — |
| timeline_judgement_date | 2026-07-15 | — | 2026-04-13 | 2025-10-15 | — |
| timeline_sale_date_projected_date | — | — | 2026-05-19 | — | — |
| timeline_sale_date_set_date | — | — | 2026-02-19 | — | — |
| timeline_final_title_cleared_date | — | — | — | — | — |
| timeline_sale_date_held_date | — | — | — | 2025-10-14 | — |
| timeline_foreclosure_completed_date | — | — | — | — | — |
| timeline_third_party_sold_date_date | — | — | — | — | — |
| timeline_third_party_proceeds_received_date | — | — | — | — | — |
| target_notice_of_intent_days | 30 | 30 | 30 | 30 | 30 |
| target_notice_of_intent_expired_days | 90 | 90 | 90 | 90 | 90 |
| target_approved_for_referral_days | 30 | 30 | 30 | 30 | 30 |
| target_referred_to_attorney_days | 1 | 1 | 1 | 1 | 1 |
| target_referred_to_foreclosure_days | 1 | 1 | 1 | 1 | 1 |
| target_title_report_received_days | 30 | 30 | 30 | 30 | 30 |
| target_preliminary_title_cleared_days | 30 | 30 | 30 | 30 | 30 |
| target_first_legal_days | 120 | 120 | 120 | 120 | 120 |
| target_service_days | 90 | 90 | 90 | 90 | 90 |
| target_publication_days | 30 | 30 | 30 | 30 | 30 |
| target_judgement_hearing_set_days | 120 | 120 | 120 | 120 | 120 |
| target_judgement_days | 30 | 30 | 30 | 30 | 30 |
| target_sale_date_set_days | 30 | 30 | 30 | 30 | 30 |
| target_final_title_cleared_days | 5 | 5 | 5 | 5 | 5 |
| target_sale_date_held_days | 0 | 0 | 0 | 0 | 0 |
| actual_notice_of_intent_days | — | — | — | — | — |
| actual_notice_of_intent_expire_days | — | — | — | — | — |
| actual_approved_for_referral_days | — | — | — | — | — |
| actual_referred_to_attorney_days | — | — | — | — | — |
| actual_referred_to_foreclosure_days | 142 | 128 | 208 | 339 | — |
| actual_title_report_received_days | — | — | — | 641 | — |
| actual_preliminary_title_cleared_days | — | — | — | — | — |
| actual_first_legal_days | 163 | — | 232 | 391 | — |
| actual_service_days | 198 | — | 388 | 428 | — |
| actual_publication_days | — | — | — | — | — |
| actual_judgement_hearing_set_days | 429 | — | 439 | 501 | — |
| actual_judgement_days | 560 | — | 498 | 593 | — |
| actual_sale_date_set_days | — | — | 445 | — | — |
| actual_final_title_cleared_days | — | — | — | — | — |
| actual_sale_date_held_days | — | — | — | 592 | — |
| variance_active_bankruptcy | — | — | — | — | — |
| variance_completed_bankruptcy | — | — | — | — | — |
| variance_estimated_hold_days | — | — | — | — | — |
| variance_bankruptcies | — | — | — | — | — |
| bid_approval_status | — | — | — | — | — |
| bid_approval_sale_date | — | — | — | — | — |
| bid_approval_bid_amount | — | — | — | 390832.4999999999967232 | — |
| bid_approval_loan_resolution_holods | — | — | — | — | — |
| summary_servicer_number | — | — | — | — | — |
| summary_foreclosure_status | Active Foreclosure | Active Foreclosure | Active Foreclosure | Closed Foreclosure:Process Complete | — |
| summary_completed_foreclosure | — | — | — | — | — |
| summary_foreclosure_bid_amount | — | — | — | 390832.4999999999967232 | — |
| summary_srv_fc_bid_amount | — | — | — | 390832.4999999999967232 | — |
| summary_foreclosure_sale_amount | — | — | — | 357200.0000000000000000 | — |
| summary_judicial_foreclosure | 1 | 0 | 1 | 1 | — |
| summary_foreclosure_attorney | — | — | — | — | — |
| summary_contested_litigation | 0 | 0 | 0 | 0 | — |
| summary_firm | Kelley Kronenberg, P.A. | Orlans Law Group PLLC | Johnson, Blumberg & Associates, LLC | RAS (Primary) | — |
| summary_type | Judicial | Non Judicial | Judicial | Judicial | — |
| summary_sms_days_in_fcl | 298 | 8 | 263 | 257 | — |
| summary_days_in_fcl | 298 | 8 | 263 | 257 | — |
| summary_current_step | Judgment Entered | Title Report Received | Pre-Sale Review 1 (SCRA and PACER Check) | Post Sale Review (SCRA and PACER Check) | — |
| summary_last_step_completed | Motion for Judgment Sent to Court | File Received By Attorney | Are We Proceeding with a Consent Judgment  | Post Sale Review (SCRA and PACER Check) | — |
| summary_last_step_completed_date | 2025-12-17 | 2026-03-09 | 2026-02-17 | 2025-10-15 | — |
| create_user | — | — | — | — | — |
| create_dept | — | — | — | — | — |
| create_time | — | — | — | — | — |
| update_user | — | — | — | — | — |
| update_time | — | — | — | — | — |
| status | 0 | 0 | 0 | 0 | — |
| is_deleted | 0 | 0 | 0 | 0 | 0 |
| tenant_id | 000000 | 000000 | 000000 | 000000 | — |
| var_notice_of_intent_days | — | — | — | — | — |
| var_notice_of_intent_expire_days | — | — | — | — | — |
| var_approved_for_referral_days | — | — | — | — | — |
| var_referred_to_attorney_days | — | — | — | — | — |
| var_referred_to_foreclosure_days | -10 | -24 | 56 | 187 | — |
| var_title_report_received_days | — | — | — | 459 | — |
| var_preliminary_title_cleared_days | — | — | — | — | — |
| var_first_legal_days | -169 | — | -100 | 59 | — |
| var_service_days | -224 | — | -34 | 6 | — |
| var_publication_days | — | — | — | — | — |
| var_judgement_hearing_set_days | -143 | — | -133 | -71 | — |
| var_judgement_days | -42 | — | -104 | -9 | — |
| var_sale_date_set_days | — | — | -187 | — | — |
| var_final_title_cleared_days | — | — | — | — | — |
| var_sale_date_held_days | — | — | — | -45 | — |
| var_total | — | — | — | — | — |
| target_total | 637 | 637 | 637 | 637 | 637 |
| actual_total | — | — | — | — | — |

---

## hold — bpms_dev.sync_loan_foreclosure_hold

> Hold 全历史（每次变更一行）。全 **15** 字段 · 当前态(多行/贷款) · 共 **16** 行 · 各贷款行数：{'7727000065': 4, '7727000088': 7, '7727004200': 5}。

| id | loanid | svcloanid | fctrdt | description | description_start_date | description_end_date | create_user | create_dept | create_time | update_user | update_time | status | is_deleted | tenant_id |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 11444 | 7727000065 | 1031718621 | 2025-05-05 | Original Note | 2025-02-06 | 2025-03-10 | — | — | — | — | — | 0 | 0 | 000000 |
| 11385 | 7727000065 | 1031718621 | 2025-07-02 | Bankruptcy Filed | 2025-05-06 | 2025-06-27 | — | — | — | — | — | 0 | 0 | 000000 |
| 11376 | 7727000065 | 1031718621 | 2025-08-26 | Court Delay | 2025-07-02 | 2025-07-14 | — | — | — | — | — | 0 | 0 | 000000 |
| 11355 | 7727000065 | 1031718621 | 2026-03-13 | Court Delay | 2025-08-26 | 2025-08-28 | — | — | — | — | — | 0 | 0 | 000000 |
| 11390 | 7727000088 | 1031718838 | 2025-07-15 | Original Note | 2025-05-28 | 2025-06-11 | — | — | — | — | — | 0 | 0 | 000000 |
| 11371 | 7727000088 | 1031718838 | 2025-07-30 | Service Delay | 2025-07-15 | 2025-07-31 | — | — | — | — | — | 0 | 0 | 000000 |
| 11370 | 7727000088 | 1031718838 | 2025-08-12 | Loss Mitigation Workout | 2025-07-31 | 2025-08-01 | — | — | — | — | — | 0 | 0 | 000000 |
| 11321 | 7727000088 | 1031718838 | 2025-10-21 | Loss Mitigation Workout | 2025-08-13 | 2025-10-21 | — | — | — | — | — | 0 | 0 | 000000 |
| 11291 | 7727000088 | 1031718838 | 2026-01-18 | Court Delay | 2025-10-21 | 2025-12-16 | — | — | — | — | — | 0 | 0 | 000000 |
| 11230 | 7727000088 | 1031718838 | 2026-02-23 | Court Delay | 2026-01-16 | — | — | — | — | — | — | 0 | 0 | 000000 |
| 11241 | 7727000088 | 1031718838 | 2026-02-23 | Loss Mitigation Workout | 2026-02-20 | 2026-02-24 | — | — | — | — | — | 0 | 0 | 000000 |
| 11380 | 7727004200 | 0688132141 | 2025-09-03 | Client Document Execution | 2025-07-08 | 2025-07-09 | — | — | — | — | — | 0 | 0 | 000000 |
| 11304 | 7727004200 | 0688132141 | 2025-11-20 | Court Delay | 2025-09-03 | 2025-11-20 | — | — | — | — | — | 0 | 0 | 000000 |
| 11296 | 7727004200 | 0688132141 | 2025-12-30 | Hearing Set | 2025-11-21 | 2025-12-11 | — | — | — | — | — | 0 | 0 | 000000 |
| 11263 | 7727004200 | 0688132141 | 2026-01-28 | Service Delay | 2025-12-30 | 2026-01-23 | — | — | — | — | — | 0 | 0 | 000000 |
| 11245 | 7727004200 | 0688132141 | 2026-03-13 | Hearing Set | 2026-01-29 | 2026-02-13 | — | — | — | — | — | 0 | 0 | 000000 |

---

## loss_mitigation — bpms_dev.sync_loan_foreclosure_loss_mitigation

> LM 周期历史。全 **22** 字段 · 当前态(多行/贷款) · 共 **20** 行 · 各贷款行数：{'7727000010': 1, '7727000065': 2, '7727000088': 9, '7727000672': 2, '7727004200': 6}。

| id | loanid | svcloanid | fctrdt | deal | program | lmc_status | cycle_opened_date | cycle_closed_date | final_disposition | denialreason | borrower_intentions | imminent_default | single_point_of_contact | create_user | create_dept | create_time | update_user | update_time | status | is_deleted | tenant_id |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 25629 | 7727000010 | 1031718692 | 2026-03-13 | Evaluation | Evaluation | Pending Financials  | 2024-11-26 | 2024-12-23 | Request Incomplete/Failed to Provide Information |  |  | — | — | — | — | — | — | — | 0 | 0 | 000000 |
| 25635 | 7727000065 | 1031718621 | 2025-06-30 | Evaluation | Evaluation | Pending Financials  | 2024-11-26 | 2024-12-23 | Request Incomplete/Failed to Provide Information |  |  | — | — | — | — | — | — | — | 0 | 0 | 000000 |
| 25636 | 7727000065 | 1031718621 | 2026-03-13 | Evaluation | Evaluation | Pending Financials  | 2025-07-01 | 2025-07-01 | LMS Opened in Error |  |  | — | — | — | — | — | — | — | 0 | 0 | 000000 |
| 25643 | 7727000088 | 1031718838 | 2025-01-29 | Evaluation | Evaluation | Pending Financials  | 2024-09-20 | 2024-10-21 | Request Incomplete/Failed to Provide Information |  |  | — | — | — | — | — | — | — | 0 | 0 | 000000 |
| 25644 | 7727000088 | 1031718838 | 2025-03-16 | Modification | Bridger mod | Workout Denial | 2025-01-30 | 2025-03-11 | Referral to FC |  |  | — | — | — | — | — | — | — | 0 | 0 | 000000 |
| 25645 | 7727000088 | 1031718838 | 2025-05-07 | Modification | Bridger mod | Workout Denial | 2025-03-17 | 2025-04-29 | Referral to FC | Request Incomplete/Failed to Provide Documentation |  | — | — | — | — | — | — | — | 0 | 0 | 000000 |
| 25646 | 7727000088 | 1031718838 | 2025-06-19 | Modification | Bridger mod | Workout Denial | 2025-05-08 | 2025-06-14 | Referral to FC | Request Incomplete/Failed to Provide Documentation |  | — | — | — | — | — | — | — | 0 | 0 | 000000 |
| 25647 | 7727000088 | 1031718838 | 2025-10-20 | Modification | 496.0 | Workout Denial | 2025-06-20 | 2025-10-20 | Referral to FC |  |  | — | — | — | — | — | — | — | 0 | 0 | 000000 |
| 25648 | 7727000088 | 1031718838 | 2025-12-09 | Short Sale | Short Sale | Document Follow-up | 2025-10-20 | 2025-11-21 | Request Incomplete/Failed to Provide Information |  |  | — | — | — | — | — | — | — | 0 | 0 | 000000 |
| 25649 | 7727000088 | 1031718838 | 2026-01-27 | DIL | Deed-in-Lieu | DIL Title Ordered | 2025-12-10 | 2026-01-27 | LMS Opened in Error |  |  | — | — | — | — | — | — | — | 0 | 0 | 000000 |
| 25650 | 7727000088 | 1031718838 | 2026-02-17 | DIL | Deed-in-Lieu | Negotiate DIL liens | 2026-01-27 | 2026-02-17 | LMS Opened in Error |  |  | — | — | — | — | — | — | — | 0 | 0 | 000000 |
| 25651 | 7727000088 | 1031718838 | 2026-03-13 | DIL | Deed-in-Lieu | Awaiting MI Approval | 2026-02-17 | — | Pending |  |  | — | — | — | — | — | — | — | 0 | 0 | 000000 |
| 25841 | 7727000672 | 1032761570 | 2026-02-24 | Payment Plan | Repayment Plan | Workout Denial | 2025-04-11 | 2025-08-14 | Referral to FC | Trial Plan Default | Retention | — | — | — | — | — | — | — | 0 | 0 | 000000 |
| 25842 | 7727000672 | 1032761570 | 2026-03-13 | Payment Plan | Repayment Plan | Submitted for Approval | 2026-02-25 | — | Pending |  |  | — | — | — | — | — | — | — | 0 | 0 | 000000 |
| 26101 | 7727004200 | 0688132141 | 2025-05-06 | Forbearance | Unemployment Forbearance | Monitor Forbearance | 2025-01-24 | 2025-05-02 | Forbearance Complete |  |  | — | — | — | — | — | — | — | 0 | 0 | 000000 |
| 26102 | 7727004200 | 0688132141 | 2025-07-26 | Evaluation | Evaluation | Document Follow-up | 2025-05-07 | 2025-05-30 | LMS Opened in Error |  |  | — | — | — | — | — | — | — | 0 | 0 | 000000 |
| 26103 | 7727004200 | 0688132141 | 2025-10-02 | Modification | 496.0 | Workout Denial | 2025-07-27 | 2025-09-19 | Referral to FC |  |  | — | — | — | — | — | — | — | 0 | 0 | 000000 |
| 26104 | 7727004200 | 0688132141 | 2025-11-16 | Modification | 496.0 | Workout Denial | 2025-10-03 | — | Pending |  |  | — | — | — | — | — | — | — | 0 | 0 | 000000 |
| 26105 | 7727004200 | 0688132141 | 2026-01-05 | Modification | 496.0 | Workout Denial | 2025-11-17 | 2026-01-02 | Referral to FC |  |  | — | — | — | — | — | — | — | 0 | 0 | 000000 |
| 26106 | 7727004200 | 0688132141 | 2026-03-13 | Modification | 496.0 | Document Follow-up | 2026-01-06 | 2026-02-02 | Request Incomplete/Failed to Provide Information |  |  | — | — | — | — | — | — | — | 0 | 0 | 000000 |

---

## bankruptcy — bpms_dev.sync_loan_foreclosure_bankruptcy

> 破产记录。全 **22** 字段 · 当前态(多行/贷款) · 共 **3** 行 · 各贷款行数：{'7727000010': 2, '7727000065': 1}。

| id | loanid | svcloanid | fctrdt | bankruptcy_status | legal_status | status_date | chapter | lien_status | mfr_status | mfr_filed_date | claim_status | proof_of_claim_date | post_petition_due_date | create_user | create_dept | create_time | update_user | update_time | status | is_deleted | tenant_id |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2677 | 7727000010 | 1031718692 | 2024-07-24 | Active | BK13 | 2023-08-23 | 13 | — | — | — | — | 2023-09-30 | 2023-09-01 | — | — | — | — | — | 0 | 0 | 000000 |
| 2678 | 7727000010 | 1031718692 | 2026-03-13 | Active | BK13 | 2024-02-06 | 13 | — | — | — | — | 2023-09-30 | 2026-01-01 | — | — | — | — | — | 0 | 0 | 000000 |
| 2679 | 7727000065 | 1031718621 | 2026-03-13 | Discharged | REO | 2025-04-30 | 7 | — | — | — | — | — | — | — | — | — | — | — | 0 | 0 | 000000 |

