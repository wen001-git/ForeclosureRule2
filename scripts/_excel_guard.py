"""
Shared guard for protecting user-owned「人工」columns in project Excel files.

Per the project CLAUDE.md "Excel 人工列 / 批注保护规则":
- Any column whose row-1 header contains 「人工」 is user-owned: scripts must never
  write/overwrite/delete it.
- Generated columns must be located BY HEADER NAME (not a hardcoded index), so a
  user-inserted column can't cause index drift and clobbering.

Usage:
    from _excel_guard import col_by_header, next_free_col, assert_safe, manual_cols
    col = col_by_header(ws, "验证SQL") or next_free_col(ws)
    assert_safe(ws, col)
    ws.cell(r, col, value)
"""

MANUAL_MARK = "人工"


def manual_cols(ws) -> set:
    """Set of 1-based column indices whose row-1 header contains 「人工」."""
    out = set()
    for c in range(1, ws.max_column + 1):
        v = ws.cell(1, c).value
        if isinstance(v, str) and MANUAL_MARK in v:
            out.add(c)
    return out


def is_manual(ws, col: int) -> bool:
    v = ws.cell(1, col).value
    return isinstance(v, str) and MANUAL_MARK in v


def col_by_header(ws, name_substring: str):
    """First non-manual column whose row-1 header CONTAINS name_substring; else None.
    Substring match tolerates suffixes like '验证结果（实测 2026-06-02）'."""
    for c in range(1, ws.max_column + 1):
        v = ws.cell(1, c).value
        if isinstance(v, str) and name_substring in v and MANUAL_MARK not in v:
            return c
    return None


def next_free_col(ws) -> int:
    """First column index after the current last used column (append target)."""
    return ws.max_column + 1


def assert_safe(ws, col: int):
    """Raise if `col` is a user-owned 人工 column — scripts must not write it."""
    if is_manual(ws, col):
        hdr = ws.cell(1, col).value
        raise RuntimeError(
            f"REFUSED to write column {col} — its header {hdr!r} contains 「人工」 "
            f"(user-owned, protected by CLAUDE.md rule). Locate the generated column by header instead."
        )
