"""
Add snapshot-date filters to doc 13 Appendix B verification SQL (zh + en).

Only the daily-snapshot-table distribution/count queries are inflated and need a filter:
  - SQL-1, SQL-2, SQL-3  query newrez.portnewrezfc (daily snapshot) -> add dataasof = MAX
  - SQL-9                queries bpms_dev.sync_fcl_stage_info (daily snapshot) -> add fctrdt = MAX

NOT touched (verified non-snapshot): SQL-5/6/7/8/11/13 query bpms_dev event/cycle tables
(sync_loan_foreclosure[_hold/_loss_mitigation/_bankruptcy], ~1-4 rows/loan, no per-day dim);
SQL-10/12 already carry fctrdt = MAX; SQL-4 is a single-loan diagnostic.

SQL code lines are identical in zh and en, so the same replacements apply to both files.
Idempotent. Run: python scripts/add_dataasof_to_doc13_sql.py
"""

import sys, io
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

FILES = [
    Path("docs/zh/13_newrez_fcl_bps_display_mapping.md"),
    Path("docs/en/13_newrez_fcl_bps_display_mapping.md"),
]

FC_FILTER = "  AND dataasof = (SELECT MAX(dataasof) FROM newrez.portnewrezfc)"
STAGE_MAX = "(SELECT MAX(fctrdt) FROM bpms_dev.sync_fcl_stage_info)"

# (old, new, expected_min_count, label)
REPLACEMENTS = [
    # SQL-1 & SQL-3 (identical ending; both need the filter) -- replace_all
    (
        "FROM newrez.portnewrezfc\nWHERE activefcflag = 1;",
        f"FROM newrez.portnewrezfc\nWHERE activefcflag = 1\n{FC_FILTER};",
        "SQL-1/SQL-3 main (dataasof=MAX)",
        True,
    ),
    # SQL-2 denominator subquery
    (
        "(SELECT COUNT(*) FROM newrez.portnewrezfc WHERE activefcflag = 1), 1",
        "(SELECT COUNT(*) FROM newrez.portnewrezfc WHERE activefcflag = 1\n       AND dataasof = (SELECT MAX(dataasof) FROM newrez.portnewrezfc)), 1",
        "SQL-2 denominator (dataasof=MAX)",
        False,
    ),
    # SQL-2 main WHERE
    (
        "WHERE activefcflag = 1\n  AND fcresults IS NOT NULL",
        f"WHERE activefcflag = 1\n{FC_FILTER}\n  AND fcresults IS NOT NULL",
        "SQL-2 main (dataasof=MAX)",
        False,
    ),
    # SQL-9 denominator subquery
    (
        "(SELECT COUNT(*) FROM bpms_dev.sync_fcl_stage_info), 1",
        f"(SELECT COUNT(*) FROM bpms_dev.sync_fcl_stage_info\n     WHERE fctrdt = {STAGE_MAX}), 1",
        "SQL-9 denominator (fctrdt=MAX)",
        False,
    ),
    # SQL-9 main
    (
        "FROM bpms_dev.sync_fcl_stage_info\nGROUP BY stage",
        f"FROM bpms_dev.sync_fcl_stage_info\nWHERE fctrdt = {STAGE_MAX}\nGROUP BY stage",
        "SQL-9 main (fctrdt=MAX)",
        False,
    ),
]


def main():
    for path in FILES:
        text = path.read_text(encoding="utf-8")
        print(f"=== {path} ===")
        for old, new, label, is_all in REPLACEMENTS:
            if new in text and old not in text:
                print(f"  SKIP (already applied): {label}")
                continue
            cnt = text.count(old)
            if cnt == 0:
                print(f"  WARN not found: {label}")
                continue
            if is_all:
                text = text.replace(old, new)
                print(f"  OK x{cnt}: {label}")
            else:
                text = text.replace(old, new, 1)
                print(f"  OK: {label}")
        path.write_text(text, encoding="utf-8")
    print("\nDone.")


if __name__ == "__main__":
    main()
