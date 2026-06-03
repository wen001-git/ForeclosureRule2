# -*- coding: utf-8 -*-
"""
把 doc 13 / 数据字典 中【值/枚举列表】的中点 `·` 分隔符统一为 `|`（与 doc 14 一致）。

仅改指定行（值/枚举列表）；不动：读者行、修订历史、跨文档引用、环境标注(MySQL · bpms_dev)、
结构标签「X 阶段 · 子含义」。表格行用 ` \| `（转义，markdown 渲染为 |）；散文行用 ` | `。
幂等：再次运行不会重复转换（` · ` 已没了）。

Run: python scripts/fix_value_separator_md.py
"""
import sys, io
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# 仅这些行的 · 是值/枚举列表分隔符（行号取自 2026-06-03 grep）
TARGETS = {
    "docs/zh/13_newrez_fcl_bps_display_mapping.md":
        [260, 274, 528, 820, 835, 901, 902, 903, 904, 905, 906, 907, 996],
    "docs/en/13_newrez_fcl_bps_display_mapping.md":
        [259, 273, 527, 819, 834, 900, 901, 902, 903, 904, 905, 906, 998],
    "docs/foreclosure_data_dictionary.md":
        [1210, 1283, 1294, 1327, 1375, 1378, 1381, 1382, 1384, 1806],
}


def convert(line):
    table = line.lstrip().startswith("|")
    sep = " \\| " if table else " | "
    return line.replace(" · ", sep).replace("·", sep)


def main():
    for rel, lines in TARGETS.items():
        p = Path(rel)
        txt = p.read_text(encoding="utf-8").splitlines(keepends=True)
        changed = 0
        for ln in lines:
            i = ln - 1
            if i < 0 or i >= len(txt):
                print(f"  [warn] {rel}:{ln} 越界"); continue
            old = txt[i]
            if "·" not in old:
                print(f"  [skip] {rel}:{ln} 无 ·（可能已转换）"); continue
            txt[i] = convert(old)
            changed += 1
        p.write_text("".join(txt), encoding="utf-8")
        print(f"{rel}: 转换 {changed}/{len(lines)} 行")


if __name__ == "__main__":
    main()
