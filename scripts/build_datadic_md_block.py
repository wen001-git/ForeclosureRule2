# -*- coding: utf-8 -*-
"""
把 portnewrezdatadic（FCL 解码字典）作为「表 26」插入 docs/foreclosure_data_dictionary.md：
读取 outputs/fcl_sample_raw_dump_data.json 的 datadic（由 fetch_fcl_sample_raw_dump_data.py 经
redshift_prod 只读预取），生成解码表 —— 小字段全量、大字段去长尾（prod 最新快照出现的码）。
同时在「表19 LM 编码字段解码参考」加指向表26 的交叉引用、并补修订史 v13。

幂等：表26 包在 <!-- DATADIC26 START/END --> 标记内，重跑替换；交叉引用/版本行有则跳过。不连库。
Run: python scripts/build_datadic_md_block.py
"""
import sys, io, json
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent
DATA = json.loads((ROOT / "outputs" / "fcl_sample_raw_dump_data.json").read_text(encoding="utf-8"))
DD = DATA["datadic"]
MD = ROOT / "docs" / "foreclosure_data_dictionary.md"
START, END = "<!-- DATADIC26 START -->", "<!-- DATADIC26 END -->"


def codesort(codes):
    return sorted(codes, key=lambda c: (0, int(c)) if str(c).isdigit() else (1, str(c)))


def esc(s):
    return str(s).replace("|", "\\|") if s is not None else ""


def build_block():
    o = [START,
         "### 表 26：`newrez.portnewrezdatadic` — Redshift 解码字典", "",
         "> **角色**：Newrez 数值编码 → 文本 的字典（长表）。FCL ETL 在 Redshift 把 LM/BK 整数码 `LEFT JOIN` "
         "本表解码为文本后写入 BPS（`basic_data_pool_config.py:835-840` LM、`:367` BK；`concat(code,'.0')` 对齐源存法）。"
         "**dev MySQL 无此表**，仅 prod Redshift `newrez` schema 有。",
         ">",
         "> **结构（6 列）**：`package` \\| `module_name` \\| `appendix` \\| `field_name` \\| `code` \\| `description`。"
         "FCL 相关 `field_name`：LM 模块 LMDeal/LMProgram/LMStatus/LMDecision/DenialReason/BorrowerIntention；"
         "BK 模块 BKStatus/BKStage。",
         ">",
         "> **范围**：小字段（LMDeal/BorrowerIntention/BKStatus/BKStage）列**全量**；大字段（LMProgram/LMStatus/"
         "LMDecision/DenialReason）只列 **prod 最新快照实际出现的码**（去长尾；字典总码数见各表标题）。doc 19 "
         "`㉑ dict·portnewrezdatadic` 节只列 5 样例贷款用到的码。",
         ">",
         "> **查询 SQL（redshift_prod 只读）**：",
         "```sql",
         "SELECT field_name, code, description FROM newrez.portnewrezdatadic",
         "WHERE (module_name='LossMitigation' AND field_name IN",
         "       ('LMDeal','LMProgram','LMStatus','LMDecision','DenialReason','BorrowerIntention'))",
         "   OR (module_name='Bankruptcy' AND field_name IN ('BKStatus','BKStage'));",
         "```", ""]
    small = set(DD["small_fields"])
    for fn in DD["field_order"]:
        d = DD["dict"].get(fn, {})
        if fn in small:
            codes = codesort(d.keys())
            title = f"#### {fn} ← `{DD['field_src'][fn]}`（{DD['field_module'][fn]}；字典 {len(d)} 码，本表全量列出）"
        else:
            codes = codesort(DD["prod_present"][fn])
            title = (f"#### {fn} ← `{DD['field_src'][fn]}`（{DD['field_module'][fn]}；字典 {len(d)} 码 · "
                     f"prod 实际 {len(DD['prod_present'][fn])} 码，本表列 prod 出现的码）")
        o += [title, "", "| 编码 | 解码（description） |", "|---|---|"]
        for c in codes:
            o.append(f"| {esc(c)} | {esc(d.get(c, '（字典无此码）'))} |")
        o.append("")
    o.append(END)
    return "\n".join(o)


def main():
    lines = MD.read_text(encoding="utf-8").splitlines()
    text = "\n".join(lines)
    block = build_block()

    # 1) 插入/替换 表26（在「## 4. Foreclosure 状态机」之前）
    if START in text:
        i0 = next(i for i, l in enumerate(lines) if l.strip() == START)
        i1 = next(i for i, l in enumerate(lines) if l.strip() == END)
        lines = lines[:i0] + block.splitlines() + lines[i1 + 1:]
        action = "替换"
    else:
        anchor = next(i for i, l in enumerate(lines) if l.startswith("## 4. Foreclosure 状态机"))
        # 回退到该 heading 前的 '---' 分隔（若紧邻）
        ins = anchor
        if ins >= 2 and lines[ins - 1].strip() == "" and lines[ins - 2].strip() == "---":
            ins = ins - 2
        lines = lines[:ins] + block.splitlines() + ["", "---", ""] + lines[ins:]
        action = "插入"

    # 2) 「表19 LM 编码字段解码参考」交叉引用
    xref = "> **权威全量见 [表 26 `newrez.portnewrezdatadic`](#表-26newrezportnewrezdatadic--redshift-解码字典)**（本节为 BPS JOIN 观测子集）。"
    if "表 26 `newrez.portnewrezdatadic`" not in "\n".join(l for l in lines if l.startswith("> **权威全量")):
        for i, l in enumerate(lines):
            if l.startswith("#### 表19 LM 编码字段解码参考"):
                lines.insert(i + 1, xref)
                lines.insert(i + 1, "")
                break

    # 3) 修订史 v13（插在 |---| 分隔行之后，作为最新一行）
    if "| v13 |" not in text:
        for i, l in enumerate(lines):
            if l.startswith("|------|") or (l.startswith("|") and set(l.replace("|", "").strip()) <= set("- ")):
                if i > 17:  # 修订史表的分隔行（在 ## Revision History 之后）
                    row = ("| 2026-06-04 | AI Agent (Claude Opus 4.8) | v13 | 新增**表26 `newrez.portnewrezdatadic`**"
                           "（Redshift 解码字典）：结构+角色+解码表（小字段 LMDeal/BorrowerIntention/BKStatus/BKStage 全量；"
                           "大字段 LMProgram/LMStatus/LMDecision/DenialReason 去长尾=prod 最新快照出现的码）；"
                           "「表19 LM 解码参考」加表26交叉引用。数据经 redshift_prod 只读预取 | doc 19 v3 · redshift_prod |")
                    lines.insert(i + 1, row)
                    break

    MD.write_text("\n".join(lines) + ("\n" if not lines[-1] == "" else ""), encoding="utf-8")
    print(f"表26 {action}完成；字段 {len(DD['field_order'])} 个。")


if __name__ == "__main__":
    main()
