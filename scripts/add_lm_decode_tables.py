"""
Two changes to foreclosure_data_dictionary.md (表19 section):

1. Update 取值范围 cells for enum-coded fields:
   - Small enums (borrowerintention, lmdeal): inline code=text mapping
   - Large enums (lmprogram, lmstatus, lmdecision, denialreason): reference note

2. Add "#### LM 编码字段解码参考" section after the 表19 field spec table,
   containing decode tables for all major enum-coded LM fields.

All decode data from BPS JOIN queries (2026-06-01).

Run: python scripts/add_lm_decode_tables.py
"""

import sys, io
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

DOC = Path("docs/foreclosure_data_dictionary.md")

# ── Inline cell patches (old → new) ──────────────────────────────────────────

CELL_PATCHES = [
    # borrowerintention: add BPS decode
    (
        "| `borrowerintention` | Borrower intention 编码 | Newrez 系统 | 直接上报 | int | 1 / 2 / 3（整数编码） | 2 |",
        "| `borrowerintention` | Borrower intention 编码 | Newrez 系统 | 直接上报 | int | `1`=Unknown / `2`=Retention / `3`=Disposition | `2` |",
        "borrowerintention inline decode"
    ),
    # lmdeal: add BPS decode inline (8 codes, manageable)
    (
        "| `lmdeal` | LM Deal 大类编码 | Newrez 系统 | 直接上报 | int | 1 / 2 / 4 / 5 / 6 / 7 / 9 / 11（整数编码） | 2 |",
        "| `lmdeal` | LM Deal 大类编码 | Newrez 系统 | 直接上报 | int | `1`=Modification · `2`=Evaluation · `4`=Payment Plan · `5`=Forbearance · `6`=Short Sale · `7`=DIL · `9`=Payoff · `11`=Deferment（见下方解码参考表） | `2` |",
        "lmdeal inline decode"
    ),
    # lmprogram: reference to decode table
    (
        "| `lmprogram` | LM Program 编码 | Newrez 系统 | 直接上报 | int | 21 / 73 / 496 / 12 / 29 等（整数编码，15+种） | 21 |",
        "| `lmprogram` | LM Program 编码 | Newrez 系统 | 直接上报 | int | 15+种编码（21=Evaluation · 73=Deferment · 10=Deed-in-Lieu · 8=Short Sale 等；**见下方解码参考表**） | `21` |",
        "lmprogram reference"
    ),
    # lmstatus: reference to decode table
    (
        "| `lmstatus` | LM 当前状态编码 | Newrez 系统 | 直接上报 | int | 166 / 112 / 5 / 20 / 140 / 113 等（整数编码，15+种） | 166 |",
        "| `lmstatus` | LM 当前状态编码 | Newrez 系统 | 直接上报 | int | 15+种编码（166=Pending Financials · 112=Workout Denial · 5=Document Follow-up 等；**见下方解码参考表**） | `166` |",
        "lmstatus reference"
    ),
    # lmdecision: reference to decode table
    (
        "| `lmdecision` | LM 最终决策编码 | Newrez 系统 | 直接上报 | int | 99 / 5 / 11 / 10 / 6 / 14 等（整数编码） | 99 |",
        "| `lmdecision` | LM 最终决策编码 | Newrez 系统 | 直接上报 | int | 12+种编码（99=Pending · 6=Referral to FC · 10=Request Incomplete · 11=LMS Opened in Error 等；**见下方解码参考表**） | `99` |",
        "lmdecision reference"
    ),
    # denialreason: reference to decode table
    (
        "| `denialreason` | LM 拒绝原因编码 | Newrez 系统 | 直接上报 | int | 109 / 76 / 4 / 6 / 21 等（整数编码，10+种） | 109 |",
        "| `denialreason` | LM 拒绝原因编码 | Newrez 系统 | 直接上报 | int | 18+种编码（109=Loan not due 3+ months · 4=Withdrawal · 6=Ineligible 等；**见下方解码参考表**） | `109` |",
        "denialreason reference"
    ),
]

# ── Decode reference tables (inserted after 表19 field spec table) ─────────────

DECODE_SECTION = """
---

#### 表19 LM 编码字段解码参考（BPS JOIN 实测，2026-06-01）

> 以下解码来自 `newrez.portnewrezlm JOIN bpms_dev.sync_loan_foreclosure_loss_mitigation`，以最高频率映射为准（ETL 可能因版本差异产生少量多对多）。

##### lmdeal — LM 交易大类

| 编码 | 解码（BPS deal字段） | 业务含义 |
|---|---|---|
| `1` | Modification | 贷款修改（永久变更利率/期限/本金） |
| `2` | Evaluation | 初始评估阶段 |
| `4` | Payment Plan | 还款计划 |
| `5` | Forbearance | 宽限期（临时暂停还款） |
| `6` | Short Sale | 短售（低于贷款余额出售） |
| `7` | DIL | Deed-in-Lieu（以房抵债） |
| `9` | Payoff | 全额还清 |
| `11` | Deferment | 递延（延期偿还部分本金） |

##### lmprogram — LM 具体方案

| 编码 | 解码（BPS program字段） | 所属大类 |
|---|---|---|
| `21` | Evaluation | Evaluation |
| `73` | Deferment | Deferment |
| `29` | Repayment Plan | Payment Plan |
| `12` | Short-term Forbearance | Forbearance |
| `396` | VA Traditional | Forbearance/Modification |
| `419` | Bridger mod | Modification |
| `240` | SLS Standard Mod | Modification |
| `348` | FHA Recovery SAPC | Modification |
| `8` | Short Sale | Short Sale |
| `10` | Deed-in-Lieu | DIL |
| `14` | Unemployment Forbearance | Forbearance |
| `25` | Payoff | Payoff |
| `151` | Disaster Forbearance | Forbearance |
| `215` | Short-term FB COVID *(RETIRED 2023-11-01)* | Forbearance |
| `273` | Standard Proprietary Modification | Modification |
| `364` | VA 30 Year Modification | Modification |
| `365` | VA 40 Year Modification | Modification |
| `405` | VASP No Trial | Modification |
| `496` | *(多用途过渡码，具体含义随投资人指南变化)* | — |
| `498` | *(同上)* | — |

##### lmstatus — LM 当前工作状态

| 编码 | 解码（BPS lmc_status字段） | 阶段描述 |
|---|---|---|
| `166` | Pending Financials | 等待借款人提交财务材料 |
| `112` | Workout Denial | 本轮 LM 已被拒绝 |
| `5` | Document Follow-up | 跟进补充缺失材料 |
| `20` | Book mod | 贷款修改正式记账中 |
| `113` | Monitor Forbearance | 监控宽限期执行情况 |
| `140` | Deferment Agreement Ordered | 递延协议已下单/签署 |
| `139` | Deferment Plan In Progress | 递延计划进行中 |
| `25` | Monitor for pmts/funds | 监控借款人是否正常还款 |
| `13` | Follow up for 1st Trial Payment | 跟进首期试验期还款 |
| `172` | Liquidation Referral | 清算/处置转介 |
| `116` | Not Assigned | 未分配状态 |
| `45` | Countered by Supervisor | 主管已反驳/调整方案 |
| `135` | DIL Sent for Recording | 以房抵债文件已提交登记 |
| `47` | Book mod | 记账中（另一变体） |
| `48` | Workout Denial | 拒绝（另一代码） |
| `24` | Workout Denial | 拒绝（另一代码） |
| `185` / `186` | Book mod | 记账中（变体代码） |

##### lmdecision — LM 最终处置结论

| 编码 | 解码（BPS final_disposition字段） | 对 FCL 的影响 |
|---|---|---|
| `99` | Pending（进行中） | FCL 暂停 |
| `1` | Modification Complete | FCL 撤销/暂停 |
| `3` | DIL Complete | FCL 完成（DIL方式） |
| `4` | Forbearance Complete | 宽限完成，FCL 继续评估 |
| `5` | Reinstated/Current | 借款人已复原还款，FCL 撤销 |
| `6` | Referral to FC | LM 失败，正式转回 FCL |
| `7` | Not Eligible for Loss Mitigation | 不符合 LM 资格 |
| `10` | Request Incomplete/Failed to Provide Information | 申请不完整，FCL 继续 |
| `11` | LMS Opened in Error | 系统错误开立，忽略 |
| `14` | Deferment Completed | 递延完成 |
| `17` | Full Pay Off | 全额还清 |
| `18` | FC Sale Held | 拍卖已执行 |

##### denialreason — LM 拒绝原因

| 编码 | 解码（BPS denialreason字段） |
|---|---|
| `109` | Loan not due for 3 or more monthly payments |
| `76` | HAMP Sunset |
| `4` | Withdrawal of Request/Non-Acceptance |
| `6` | Ineligible Borrower |
| `75` | Declined Mod Review in favor of SS/DIL |
| `21` | Request Incomplete/Failed to Provide Documentation |
| `118` | Loan not 90+ DPD |
| `34` | Ineligible Borrower: Not a Natural Person |
| `30` | Failed Plan |
| `124` | Hardship not resolved |
| `86` | Request Withdrawn |
| `50` | Request Withdrawn Before Offer |
| `108` | Unable to achieve target payment |
| `2` | Trial Plan Default |
| `9` | Investor Not Participating |
| `32` | HDTI out of range |
| `78` | Buyer walked (SS) |
| `11` | Default Not Imminent |

"""

# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    text = DOC.read_text(encoding="utf-8")

    # 1. Apply cell patches
    ok = 0
    for old, new, label in CELL_PATCHES:
        if old in text:
            text = text.replace(old, new, 1)
            print(f"  OK: {label}")
            ok += 1
        else:
            print(f"  WARNING not found: {label}")

    # 2. Insert decode tables after 表19 field spec table
    # Anchor: the --- line that follows the 表19 field spec table
    anchor = "---\n\n## 4. Foreclosure 状态机"
    if anchor in text:
        text = text.replace(anchor, DECODE_SECTION + "\n---\n\n## 4. Foreclosure 状态机", 1)
        print("  OK: decode reference tables inserted")
        ok += 1
    else:
        # Try alternate anchor
        anchor2 = "## 4. Foreclosure"
        if anchor2 in text:
            idx = text.index(anchor2)
            text = text[:idx] + DECODE_SECTION + "\n" + text[idx:]
            print("  OK: decode reference tables inserted (alt anchor)")
            ok += 1
        else:
            print("  WARNING: could not find insertion anchor for decode tables")

    # 3. Revision history
    rev_old = "| 2026-06-01 | AI Agent (Claude Sonnet 4.6) | v7 |"
    rev_new = (
        "| 2026-06-01 | AI Agent (Claude Sonnet 4.6) | v8 | "
        "表19 LM 编码字段补全：① borrowerintention、lmdeal 取值范围列内联 BPS 解码文本；"
        "② lmprogram/lmstatus/lmdecision/denialreason 取值范围列增加解码参考说明；"
        "③ 新增「表19 LM 编码字段解码参考」章节（5 张解码表，共约 60 条 code→text 映射，"
        "来自 bpms_dev JOIN newrez 实测） | BPS JOIN 2026-06-01 |\n"
        + rev_old
    )
    if rev_old in text:
        text = text.replace(rev_old, rev_new, 1)
        print("  OK: revision history")
        ok += 1

    DOC.write_text(text, encoding="utf-8")
    print(f"\nSaved {DOC} — {ok} patches applied.")


if __name__ == "__main__":
    main()
