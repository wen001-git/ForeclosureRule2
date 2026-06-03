"""
Split the "典型取值" column into "取值范围" + "典型取值" for tables 18 and 19
in foreclosure_data_dictionary.md.

All ranges are MCP MySQL verified (2026-06-01).

Run: python scripts/split_typical_values_18_19.py
"""

import sys, io, re
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

DOC = Path("docs/foreclosure_data_dictionary.md")

# ── Field mappings: {field_name: (取值范围, 典型取值)} ─────────────────────────

T18 = {
    "id":                              ("1~1,556,688",                                               "1"),
    "loanid":                          ("纯数字字符串",                                              "7727000088"),
    "dataasof":                        ("YYYY-MM-DD",                                                "2026-05-27"),
    "shellpointloanid":                ("格式 NR-YYYY-NNNNNN",                                       "NR-2024-001234"),
    "fcsetupdate":                     ("2024-02-07~2026-05-26",                                     "2024-01-10"),
    "fcreferraldate":                  ("2024-02-07~2026-05-26",                                     "2024-01-20"),
    "smsdaysinfc":                     ("1~606天",                                                   "128"),
    "daysinfc":                        ("1~814天",                                                   "215"),
    "demandsentdate":                  ("2021-10-18~2026-04-20",                                     "2024-02-01"),
    "demandexpirationdate":            ("2018-03-02~2026-06-22",                                     "2024-03-02"),
    "fcstage":                         ("自由文本（Newrez系统内部）",                                  "Service Complete"),
    "lastfcstepcompleted":             ("自由文本",                                                   "First Legal"),
    "lastfcstepcompleteddate":         ("2019-10-14~2026-05-27",                                     "2024-02-15"),
    "fchold1description":              ("Loss Mitigation Workout · Awaiting Funds to Post · Service Delay · Court Delay · Hearing Set · Bankruptcy Filed 等15+种", "Loss Mitigation Workout"),
    "fchold1startdate":                ("2019-11-20~2026-05-27",                                     "2024-01-05"),
    "fchold1enddate":                  ("2019-11-26~2026-05-28（空=仍持续）",                         "2024-03-15"),
    "fchold2description":              ("同 fchold1description（69.8%填充）",                         "Loss Mitigation Workout"),
    "fchold2startdate":                ("2019-11-20~2026-05-27",                                     "2022-11-08"),
    "fchold2enddate":                  ("2019-11-26~2026-05-28（空=仍持续）",                         "2022-11-25"),
    "fcjudgmenthearingscheduled":      ("2020-01-22~2026-08-21",                                     "2026-01-18"),
    "fcjudgmententered":               ("2025-01-10~2026-04-09",                                     "2026-01-07"),
    "fcscheduledsaledate":             ("2025-04-17~2026-08-06",                                     "2024-05-15"),
    "fcsalehelddate":                  ("2025-05-27~2026-05-22",                                     "2024-05-15"),
    "fcsaleamount":                    ("$90,001~$400,000",                                          "170000.00"),
    "fcresults":                       ("REO · 3rd Party（活跃FCL为空）",                             "REO"),
    "firstlegaldate":                  ("2018-10-29~2026-05-27",                                     "2024-02-01"),
    "servicecompletedate":             ("2018-12-10~2026-02-15",                                     "2024-03-10"),
    "titleordereddate":                ("YYYY-MM-DD",                                                "2023-12-20"),
    "titlecleardate":                  ("2025-03-24~2026-04-26（Newrez少量提供）",                    "2024-01-15"),
    "titlereceiveddate":               ("2025-03-24~2026-04-26（Newrez少量提供）",                    "2024-01-25"),
    "fcremovaldesc":                   ("自由文本",                                                   "Foreclosure Complete"),
    "fcremovaldate":                   ("2019-11-27~2026-05-28",                                     "2024-06-01"),
    "fccontestedflag":                 ("0 / 1",                                                     "0"),
    "judicial":                        ("0（Non-Judicial）/ 1（Judicial）",                           "1"),
    "fcfirm":                          ("自由文本（律师事务所名称）",                                  "Kelley Kronenberg, P.A."),
    "jr_sr_lien_flag":                 ("0 / 1",                                                     "0"),
    "fcbidamount":                     ("$90,000~$543,305.96",                                       "160000.00"),
    "activefcflag":                    ("0（已完结）/ 1（进行中）",                                    "1"),
    "fchold1projectedenddate":         ("YYYY-MM-DD",                                                "2024-03-20"),
    "fchold1comment":                  ("自由文本",                                                   "Awaiting Bankruptcy Resolution"),
    "fchold2projectedenddate":         ("YYYY-MM-DD",                                                "2023-01-07"),
    "fchold2comment":                  ("自由文本",                                                   "Awaiting Court Scheduling"),
    "holdmodified":                    ("2019-11-26~2026-05-28",                                     "2024-02-20"),
    "holdmodified2":                   ("2019-11-26~2026-05-28",                                     "2022-11-25"),
    "create_time":                     ("2024-04-09~2026-05-31（datetime）",                          "2023-12-14 08:30:00"),
    "update_time":                     ("2024-04-09~2026-05-31（datetime）",                          "2026-05-27 10:15:00"),
    "dtdeedrecorded":                  ("2025-10-28~2026-05-21",                                     "2024-06-01"),
    "fcapprbidprice":                  ("$90,000~$536,008.42",                                       "162000.00"),
    "fcl3rdpartyproceedsreceiveddate": ("2026-03-04~2026-05-26",                                     "2026-03-04"),
    "investorloanid":                  ("格式 INV-YYYYMMDD-NNN",                                     "INV-20240110-088"),
    "fchold3description":              ("同 fchold1description（52.6%填充）",                         "Service Delay"),
    "fchold3startdate":                ("2019-10-24~2026-05-25",                                     "格式 YYYY-MM-DD"),
    "fchold3enddate":                  ("YYYY-MM-DD（空=仍持续）",                                    "格式 YYYY-MM-DD"),
    "fchold3projectedenddate":         ("YYYY-MM-DD",                                                "格式 YYYY-MM-DD"),
    "fchold3comment":                  ("自由文本",                                                   "同 fchold1comment 格式"),
    "holdmodified3":                   ("YYYY-MM-DD",                                                "格式 YYYY-MM-DD"),
    "activejnrlienfcflag":             ("0 / 1",                                                     "0"),
    "currentmilestone":                ("Closed · First Legal · Judgment Entered · Sale Held · Sold · Service Complete · Sale Scheduled", "First Legal"),
    "srlienmonitorflag":               ("0 / 1",                                                     "0"),
    "srliensalescheduleddate":         ("实测始终为 NULL",                                            "—"),
    "srliensalehelddate":              ("实测始终为 NULL",                                            "—"),
    "srliensaleresult":                ("实测始终为 NULL",                                            "—"),
    "srliensaledate":                  ("YYYY-MM-DD",                                                "2024-06-15"),
}

T19 = {
    "id":                                              ("1~1,556,688",                                               "1"),
    "loanid":                                          ("纯数字字符串",                                              "7727000088"),
    "dataasof":                                        ("YYYY-MM-DD",                                                "2026-05-27"),
    "shellpointloanid":                                ("格式 NR-YYYY-NNNNNN",                                       "NR-2024-001234"),
    "hardshiptype":                                    ("11 / 12 / 19 / 20 / 7 / 8 / 21 等（整数编码，10+种）",      "11"),
    "borrowerintention":                               ("1 / 2 / 3（整数编码）",                                     "2"),
    "lmdeal":                                          ("1 / 2 / 4 / 5 / 6 / 7 / 9 / 11（整数编码）",               "2"),
    "dealstartdate":                                   ("2020-08-17~2026-05-29",                                     "2024-01-15"),
    "daysindeal":                                      ("0~991天",                                                   "45"),
    "lmstatus":                                        ("166 / 112 / 5 / 20 / 140 / 113 等（整数编码，15+种）",       "166"),
    "statusstartdate":                                 ("2020-08-17~2026-05-29",                                     "2024-02-01"),
    "daysinstatus":                                    ("0~991天",                                                   "30"),
    "lmprogram":                                       ("21 / 73 / 496 / 12 / 29 等（整数编码，15+种）",              "21"),
    "lmdecision":                                      ("99 / 5 / 11 / 10 / 6 / 14 等（整数编码）",                  "99"),
    "lmremovaldate":                                   ("2020-09-22~2026-05-29（空=进行中）",                         "2024-03-15"),
    "denialreason":                                    ("109 / 76 / 4 / 6 / 21 等（整数编码，10+种）",               "109"),
    "forbearanceagreementdate":                        ("2020-04-01~2026-05-25",                                     "2024-01-20"),
    "forbearancedatecompleted":                        ("2020-10-15~2026-04-30",                                     "2024-04-20"),
    "forbearancebeginningduedate":                     ("YYYY-MM-DD",                                                "2024-01-01"),
    "forbearanceendingduedate":                        ("YYYY-MM-DD",                                                "2024-04-01"),
    "forbearancenumberofmonths":                       ("1~12个月（常见 3/6/12）",                                    "3"),
    "forbearancestatus":                               ("4 / 1 / 6（整数编码）",                                     "4"),
    "forbearancetype":                                 ("41 / 61 / 40（整数编码）",                                  "41"),
    "trialagreementdate":                              ("2024-04-01~2026-05-29",                                     "2024-02-01"),
    "trialdatecompleted":                              ("YYYY-MM-DD",                                                "2024-05-01"),
    "trialbeginningduedate":                           ("YYYY-MM-DD",                                                "2024-02-01"),
    "trialendingduedate":                              ("YYYY-MM-DD",                                                "2024-05-01"),
    "trialnumberofmonths":                             ("3（实测仅此1值）",                                           "3"),
    "trialstatus":                                     ("8 / 1 / 4 / 7（整数编码）",                                 "8"),
    "repaymentagreementdate":                          ("2023-04-20~2026-03-30",                                     "2024-05-05"),
    "repaymentstartdate":                              ("2023-04-20~2026-04-30",                                     "2024-05-15"),
    "repaymentenddate":                                ("2023-06-20~2027-01-30",                                     "2025-05-15"),
    "repaymenttype":                                   ("4（实测仅此1值）",                                           "4"),
    "repaymentstatus":                                 ("5 / 1 / 7 / 4 / 6 / 3（整数编码）",                        "5"),
    "repaymentplandownpmt":                            ("$0~$40,000",                                                "5000.00"),
    "repaymentplandownpmtdate":                        ("2023-12-04~2026-04-23",                                     "2024-05-15"),
    "pradate1":                                        ("实测始终为 NULL",                                            "—"),
    "praamount1":                                      ("实测始终为 0",                                              "0"),
    "pradate2":                                        ("实测始终为 NULL",                                            "—"),
    "praamount2":                                      ("实测始终为 NULL",                                            "—"),
    "pradate3":                                        ("实测始终为 NULL",                                            "—"),
    "praamount3":                                      ("实测始终为 NULL",                                            "—"),
    "activelmflag":                                    ("0（未在LM）/ 1（LM进行中）",                                 "1"),
    "create_time":                                     ("2024-04-09~2026-05-31（datetime）",                          "2023-12-14 08:30:00"),
    "update_time":                                     ("2024-04-09~2026-05-31（datetime）",                          "2026-05-27 10:15:00"),
    "lossmitmodtermsmodifiedtermextensionmonths":       ("0~181个月",                                                 "6"),
    "deferment_flag":                                  ("0 / 1",                                                     "1"),
    "deferment_amount":                                ("$1,319~$130,729.62",                                        "10000.00"),
    "number_pi_payments_deferred":                     ("1~14期",                                                    "3"),
    "shortsalenetproceedsamount":                      ("实测始终为 0",                                              "0"),
    "shortsalecontractofferamount":                    ("实测始终为 0",                                              "0"),
    "appealperiodexpirationdate":                      ("2024-09-17~2026-05-12",                                     "2024-04-15"),
    "lossmitmodpreviouslydeferredcapitalizedamount":   ("$0~$4,500",                                                 "8000.00"),
    "deferment_date":                                  ("2020-09-11~2026-05-14",                                     "2024-03-01"),
    "denialletterdate":                                ("2019-05-07~2026-05-27",                                     "2024-04-10"),
    "investorloanid":                                  ("格式 INV-YYYYMMDD-NNN",                                     "INV-20240115-088"),
}


def parse_row_field(line):
    """Extract the field name from a markdown table row (first cell, strip backticks)."""
    m = re.match(r"\|\s*`([^`]+)`", line)
    if m:
        return m.group(1).strip()
    return None


def split_row(line, mapping):
    """Replace the 典型取值 cell (6th cell, index 5) with two cells."""
    cells = line.split("|")
    # cells[0] = '' (before first |), cells[1..N] = content, cells[-1] = '' (after last |)
    if len(cells) < 10:
        return line, False  # not a full data row
    field = parse_row_field(line)
    if field not in mapping:
        return line, False
    val_range, val_typical = mapping[field]
    # Insert new cell at position 6 (after 数据类型 at position 5, replacing 典型取值 at 6)
    # Current: [0='', 1=字段名, 2=业务含义, 3=来源数据, 4=计算逻辑, 5=数据类型, 6=典型取值, 7=上游, 8=下游, 9=备注, 10='']
    cells.insert(6, f" {val_range} ")
    cells[7] = f" {val_typical} "  # replace old 典型取值 with new 典型取值
    return "|".join(cells), True


def process_table_section(lines, start_idx, mapping):
    """Find the header/separator/data rows of the field spec table and transform them."""
    i = start_idx
    n = len(lines)
    changed = 0
    in_table = False

    while i < n:
        line = lines[i].rstrip("\n")

        # Detect the 9-column field spec table header
        if ("字段名" in line and "典型取值" in line and "上游字段" in line
                and "| 取值范围 |" not in line):
            # Replace header: insert 取值范围 before 典型取值
            lines[i] = line.replace("| 典型取值 |", "| 取值范围 | 典型取值 |") + "\n"
            in_table = True
            i += 1
            # Fix the separator row (next line)
            if i < n and lines[i].startswith("|---"):
                sep = lines[i].rstrip("\n")
                # Count current separators and add one more
                lines[i] = sep.replace("|------|--------|------|", "|------|--------|------|------|", 1) + "\n"
            i += 1
            continue

        if in_table:
            line = lines[i].rstrip("\n")
            # Stop at blank line or next section header
            if not line.startswith("|"):
                in_table = False
                break
            new_line, did_change = split_row(line, mapping)
            if did_change:
                lines[i] = new_line + "\n"
                changed += 1
            else:
                # Row not in mapping — field not found; keep as-is but insert empty range cell
                cells = line.split("|")
                if len(cells) >= 10:
                    cells.insert(6, " — ")
                    lines[i] = "|".join(cells) + "\n"

        i += 1

    return changed


def find_table_start(lines, marker):
    for i, l in enumerate(lines):
        if marker in l:
            return i
    return -1


def main():
    text_lines = DOC.read_text(encoding="utf-8").splitlines(keepends=True)

    # Add revision history entry
    rev_old = "| 2026-05-29 | AI Agent (Codex) | v5 |"
    rev_new = (
        "| 2026-06-01 | AI Agent (Claude Sonnet 4.6) | v7 | "
        "表18/表19「典型取值」列拆分为「取值范围」+「典型取值」两列（9列→10列）；"
        "取值范围来自 MCP MySQL 实测（min/max、枚举集、格式约束）；"
        "典型取值保留单一代表性示例 | MySQL newrez 实测 2026-06-01 |\n"
        + rev_old
    )

    full_text = "".join(text_lines)
    if rev_old in full_text:
        full_text = full_text.replace(rev_old, rev_new, 1)
        text_lines = full_text.splitlines(keepends=True)
        print("OK: revision history")

    # Process 表18
    idx18 = find_table_start(text_lines, "### 表 18：`newrez.portnewrezfc`")
    if idx18 >= 0:
        c = process_table_section(text_lines, idx18, T18)
        print(f"OK: 表18 — {c} rows split")
    else:
        print("WARNING: 表18 not found")

    # Process 表19
    idx19 = find_table_start(text_lines, "### 表 19：`newrez.portnewrezlm`")
    if idx19 >= 0:
        c = process_table_section(text_lines, idx19, T19)
        print(f"OK: 表19 — {c} rows split")
    else:
        print("WARNING: 表19 not found")

    DOC.write_text("".join(text_lines), encoding="utf-8")
    print(f"Saved: {DOC}")


if __name__ == "__main__":
    main()
