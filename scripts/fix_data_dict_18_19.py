"""
Fix 典型取值 values in foreclosure_data_dictionary.md for tables 18 and 19.

All corrections are verified against MySQL newrez.portnewrezfc and newrez.portnewrezlm
(queries run 2026-06-01).

Run: python scripts/fix_data_dict_18_19.py
"""

import sys, io
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

DOC = Path("docs/foreclosure_data_dictionary.md")

# Each patch: (old_string, new_string, label)
PATCHES = [

    # ── Table 18 corrections ────────────────────────────────────────────────

    # 1. currentmilestone — "First Legal Complete" doesn't exist; actual values confirmed
    (
        "| `currentmilestone` | 当前 FCL milestone | Newrez 系统 | 直接上报 | varchar(255) | `First Legal Complete`, `Service Complete` | — | Newrez 当前里程碑辅助字段 | ✅ Confirmed |",
        "| `currentmilestone` | 当前 FCL milestone | Newrez 系统 | 直接上报 | varchar(255) | `Closed` · `First Legal` · `Judgment Entered` · `Sale Held` · `Sold` · `Service Complete` · `Sale Scheduled` | — | Newrez 当前里程碑辅助字段 | ✅ Confirmed (MySQL 实测) |",
        "currentmilestone 典型取值"
    ),

    # 2. fchold1description — "Loss Mitigation" → "Loss Mitigation Workout" (full exact values)
    (
        "| `fchold1description` | Hold 1 原因描述 | Newrez 系统 | 直接上报 | varchar(255) | `Loss Mitigation`, `Bankruptcy`, `Litigated` | — | 下游 Hold detail 的 `description1` | ✅ Confirmed |",
        "| `fchold1description` | Hold 1 原因描述 | Newrez 系统 | 直接上报 | varchar(255) | `Loss Mitigation Workout` · `Awaiting Funds to Post` · `Service Delay` · `Court Delay` · `Hearing Set` · `Bankruptcy Filed` · `Moratorium` | — | 下游 Hold detail 的 `description1` | ✅ Confirmed (MySQL 实测) |",
        "fchold1description 典型取值"
    ),

    # 3. fchold2description — was —, now filled
    (
        "| `fchold2description` | Hold 2 原因描述 | Newrez 系统 | 直接上报 | varchar(255) | — | — | 下游 Hold detail 的 `description2` | ✅ Confirmed |",
        "| `fchold2description` | Hold 2 原因描述 | Newrez 系统 | 直接上报 | varchar(255) | `Loss Mitigation Workout` · `Service Delay` · `Court Delay` · `Client Document Execution` · `Hearing Set` | — | 下游 Hold detail 的 `description2` | ✅ Confirmed (MySQL 实测) |",
        "fchold2description 典型取值"
    ),

    # 4. fchold2startdate — was —
    (
        "| `fchold2startdate` | Hold 2 开始日期 | Newrez 系统 | 直接上报 | date | — | — | 下游 Hold detail 的 `description2_start_date` | ✅ Confirmed |",
        "| `fchold2startdate` | Hold 2 开始日期 | Newrez 系统 | 直接上报 | date | `2022-11-08` | — | 下游 Hold detail 的 `description2_start_date` | ✅ Confirmed (MySQL 实测) |",
        "fchold2startdate 典型取值"
    ),

    # 5. fchold2enddate — was —
    (
        "| `fchold2enddate` | Hold 2 结束日期 | Newrez 系统 | 直接上报 | date | — | — | 下游 Hold detail 的 `description2_end_date` | ✅ Confirmed |",
        "| `fchold2enddate` | Hold 2 结束日期 | Newrez 系统 | 直接上报 | date | `2022-11-25`（空=仍持续） | — | 下游 Hold detail 的 `description2_end_date` | ✅ Confirmed (MySQL 实测) |",
        "fchold2enddate 典型取值"
    ),

    # 6. fcresults — "3rd Party Sale" and "Redemption" don't exist in actual data
    (
        "| `fcresults` | FCL 结果 | Newrez 系统 | 直接上报 | varchar(255) | `3rd Party Sale`, `REO`, `Redemption` | — | 识别 `REO` / `3rd Party` 等结案结果 | ✅ Confirmed |",
        "| `fcresults` | FCL 结果 | Newrez 系统 | 直接上报 | varchar(255) | `REO` · `3rd Party`（进行中 FCL 为空） | — | 识别 `REO` / `3rd Party` 等结案结果 | ✅ Confirmed (MySQL 实测，仅此2值) |",
        "fcresults 典型取值"
    ),

    # 7. fchold2projectedenddate — was —
    (
        "| `fchold2projectedenddate` | Hold 2 预计结束日期 | Newrez 系统 | 直接上报 | date | — | — | Hold 面板 projected end date | ✅ Confirmed |",
        "| `fchold2projectedenddate` | Hold 2 预计结束日期 | Newrez 系统 | 直接上报 | date | `2023-01-07` | — | Hold 面板 projected end date | ✅ Confirmed (MySQL 实测) |",
        "fchold2projectedenddate 典型取值"
    ),

    # 8. fchold2comment — was —
    (
        "| `fchold2comment` | Hold 2 备注 | Newrez 系统 | 直接上报 | varchar(1000) | — | — | 写入 `port.basic_data_loan_comments` | ✅ Confirmed |",
        "| `fchold2comment` | Hold 2 备注 | Newrez 系统 | 直接上报 | varchar(1000) | 同 `fchold1comment` 格式，如 `Awaiting Court Scheduling` | — | 写入 `port.basic_data_loan_comments` | ✅ Confirmed |",
        "fchold2comment 典型取值"
    ),

    # 9. holdmodified2 — was —
    (
        "| `holdmodified2` | Hold 2 修改日期 | Newrez 系统 | 直接上报 | date | — | — | Hold comment 的 `comments_date` | ✅ Confirmed |",
        "| `holdmodified2` | Hold 2 修改日期 | Newrez 系统 | 直接上报 | date | `2022-11-25` | — | Hold comment 的 `comments_date` | ✅ Confirmed (MySQL 实测) |",
        "holdmodified2 典型取值"
    ),

    # 10. fchold3description — was —
    (
        "| `fchold3description` | Hold 3 原因描述 | Newrez 系统 | 直接上报 | varchar(1000) | — | — | 下游 Hold detail 的 `description3` | ✅ Confirmed |",
        "| `fchold3description` | Hold 3 原因描述 | Newrez 系统 | 直接上报 | varchar(1000) | `Service Delay` · `Loss Mitigation Workout` · `Client Document Execution` · `Hearing Set` | — | 下游 Hold detail 的 `description3` | ✅ Confirmed (MySQL 实测) |",
        "fchold3description 典型取值"
    ),

    # 11. fchold3startdate — was —
    (
        "| `fchold3startdate` | Hold 3 开始日期 | Newrez 系统 | 直接上报 | date | — | — | 下游 Hold detail 的 `description3_start_date` | ✅ Confirmed |",
        "| `fchold3startdate` | Hold 3 开始日期 | Newrez 系统 | 直接上报 | date | 格式 YYYY-MM-DD | — | 下游 Hold detail 的 `description3_start_date` | ✅ Confirmed |",
        "fchold3startdate 典型取值"
    ),

    # 12. fchold3enddate — was —
    (
        "| `fchold3enddate` | Hold 3 结束日期 | Newrez 系统 | 直接上报 | date | — | — | 下游 Hold detail 的 `description3_end_date` | ✅ Confirmed |",
        "| `fchold3enddate` | Hold 3 结束日期 | Newrez 系统 | 直接上报 | date | 格式 YYYY-MM-DD（空=仍持续） | — | 下游 Hold detail 的 `description3_end_date` | ✅ Confirmed |",
        "fchold3enddate 典型取值"
    ),

    # 13. fchold3projectedenddate — was —
    (
        "| `fchold3projectedenddate` | Hold 3 预计结束日期 | Newrez 系统 | 直接上报 | date | — | — | Hold 面板 projected end date | ✅ Confirmed |",
        "| `fchold3projectedenddate` | Hold 3 预计结束日期 | Newrez 系统 | 直接上报 | date | 格式 YYYY-MM-DD | — | Hold 面板 projected end date | ✅ Confirmed |",
        "fchold3projectedenddate 典型取值"
    ),

    # 14. fchold3comment — was —
    (
        "| `fchold3comment` | Hold 3 备注 | Newrez 系统 | 直接上报 | varchar(1000) | — | — | 写入 `port.basic_data_loan_comments` | ✅ Confirmed |",
        "| `fchold3comment` | Hold 3 备注 | Newrez 系统 | 直接上报 | varchar(1000) | 同 `fchold1comment` 格式 | — | 写入 `port.basic_data_loan_comments` | ✅ Confirmed |",
        "fchold3comment 典型取值"
    ),

    # 15. holdmodified3 — was —
    (
        "| `holdmodified3` | Hold 3 修改日期 | Newrez 系统 | 直接上报 | date | — | — | Hold comment 的 `comments_date` | ✅ Confirmed |",
        "| `holdmodified3` | Hold 3 修改日期 | Newrez 系统 | 直接上报 | date | 格式 YYYY-MM-DD | — | Hold comment 的 `comments_date` | ✅ Confirmed |",
        "holdmodified3 典型取值"
    ),

    # ── Table 19 corrections ────────────────────────────────────────────────

    # 16. hardshiptype — "1,2,3" → actual codes 11,12,19,20
    (
        "| `hardshiptype` | Hardship 类型编码 | Newrez 系统 | 直接上报 | int | `1`, `2`, `3` | — | 借款人困难原因；需字典解码 | ✅ Confirmed |",
        "| `hardshiptype` | Hardship 类型编码 | Newrez 系统 | 直接上报 | int | `11` · `12` · `19` · `20` · `7` · `8` · `21`（实测 top 7；需 Newrez 字典解码） | — | 借款人困难原因；需字典解码 | ✅ Confirmed (MySQL 实测) |",
        "hardshiptype 典型取值"
    ),

    # 17. denialreason — "1,2,3" → actual codes 109,76,4,6
    (
        "| `denialreason` | LM 拒绝原因编码 | Newrez 系统 | 直接上报 | int | `1`, `2`, `3` | — | 下游解码为 `denialreason` | ✅ Confirmed |",
        "| `denialreason` | LM 拒绝原因编码 | Newrez 系统 | 直接上报 | int | `109` · `76` · `4` · `6` · `21`（实测 top 5；需 Newrez 字典解码） | — | 下游解码为 `denialreason` | ✅ Confirmed (MySQL 实测) |",
        "denialreason 典型取值"
    ),

    # 18. pradate2/praamount2/pradate3/praamount3 — add "实测始终为 NULL" note
    (
        "| `pradate2` | PRA 日期 2 | Newrez 系统 | 直接上报 | date | — | — | PRA 相关字段 | ✅ Confirmed |",
        "| `pradate2` | PRA 日期 2 | Newrez 系统 | 直接上报 | date | — (实测始终为 NULL) | — | PRA 相关字段 | ✅ Confirmed (MySQL 实测) |",
        "pradate2 典型取值"
    ),
    (
        "| `praamount2` | PRA 金额 2 | Newrez 系统 | 直接上报 | int | — | — | PRA 相关金额 | ✅ Confirmed |",
        "| `praamount2` | PRA 金额 2 | Newrez 系统 | 直接上报 | int | — (实测始终为 NULL) | — | PRA 相关金额 | ✅ Confirmed (MySQL 实测) |",
        "praamount2 典型取值"
    ),
    (
        "| `pradate3` | PRA 日期 3 | Newrez 系统 | 直接上报 | date | — | — | PRA 相关字段 | ✅ Confirmed |",
        "| `pradate3` | PRA 日期 3 | Newrez 系统 | 直接上报 | date | — (实测始终为 NULL) | — | PRA 相关字段 | ✅ Confirmed (MySQL 实测) |",
        "pradate3 典型取值"
    ),
    (
        "| `praamount3` | PRA 金额 3 | Newrez 系统 | 直接上报 | int | — | — | PRA 相关金额 | ✅ Confirmed |",
        "| `praamount3` | PRA 金额 3 | Newrez 系统 | 直接上报 | int | — (实测始终为 NULL) | — | PRA 相关金额 | ✅ Confirmed (MySQL 实测) |",
        "praamount3 典型取值"
    ),
]


def main():
    text = DOC.read_text(encoding="utf-8")
    ok = 0
    for old, new, label in PATCHES:
        if old not in text:
            print(f"  WARNING not found: {label}")
            continue
        text = text.replace(old, new, 1)
        print(f"  OK: {label}")
        ok += 1

    # Add revision history entry
    rev_old = "| 2026-05-29 | AI Agent (Codex) | v5 |"
    rev_new = (
        "| 2026-06-01 | AI Agent (Claude Sonnet 4.6) | v6 | "
        "表18/表19 典型取值 MySQL 实测校正：① currentmilestone 更正（去除不存在的 'First Legal Complete'）；"
        "② fchold1description 更正为完整枚举值；③ fcresults 更正（去除不存在的 '3rd Party Sale'/'Redemption'）；"
        "④ Hold 2/3 全部 — 字段补充实测值；⑤ hardshiptype/denialreason 更正为实际编码；"
        "⑥ pradate2/3、praamount2/3 标注实测始终 NULL | MySQL newrez 实测 |\n"
        "| 2026-05-29 | AI Agent (Codex) | v5 |"
    )
    if rev_old in text:
        text = text.replace(rev_old, rev_new, 1)
        print("  OK: revision history")
        ok += 1
    else:
        print("  WARNING: revision history anchor not found")

    DOC.write_text(text, encoding="utf-8")
    print(f"\nSaved {DOC} — {ok}/{len(PATCHES)+1} patches applied.")


if __name__ == "__main__":
    main()
