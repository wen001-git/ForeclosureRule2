# -*- coding: utf-8 -*-
"""
生成 docs/zh/19_fcl_sample_loan_raw_dump.md —— docs/19_fcl_sample_loan_raw_dump.xlsx 的 Markdown 对应版。

复用 scripts/build_fcl_sample_raw_dump_xlsx.py 的取数与配置（LOANS / TRANSPOSE / FLAT / fmt /
cols_of / one_row / all_rows），把同样的 5 个样例贷款全表全字段内容输出为 markdown：
封面/表清单 + 8 个转置表（字段为行 × 5 贷款列）+ 3 个平铺表（记录为行 × 全字段列）。

只读 DB。Run: python scripts/build_fcl_sample_raw_dump_md.py
"""
import sys, io
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parent))

import pymysql
import build_fcl_sample_raw_dump_xlsx as X

OUT = X.ROOT / "docs" / "zh" / "19_fcl_sample_loan_raw_dump.md"


def esc(v):
    """markdown 表格单元格转义：| -> \\| ，换行 -> <br>。v 应已过 X.fmt。"""
    s = X.fmt(v) if not isinstance(v, str) else v
    return s.replace("|", "\\|").replace("\r", " ").replace("\n", "<br>")


def md_table(headers, rows):
    out = ["| " + " | ".join(esc(h) for h in headers) + " |",
           "|" + "|".join(["---"] * len(headers)) + "|"]
    for r in rows:
        out.append("| " + " | ".join(esc(c) for c in r) + " |")
    return out


def main():
    conn = pymysql.connect(host=X.HOST, port=X.PORT, user=X.USER, password=X.PASSWORD,
                           autocommit=True, connect_timeout=20, read_timeout=180)
    cur = conn.cursor()
    L = X.LOAN_IDS
    out = []

    # ── 标准文档头 ──
    out += [
        "# doc 19 — 5 个样例贷款 · FCL 全表全字段原始转储（Markdown 版）",
        "",
        "> 本文件由 `scripts/build_fcl_sample_raw_dump_md.py` 自动生成，是 "
        "`docs/19_fcl_sample_loan_raw_dump.xlsx` 的 Markdown 对应版（内容一致）。",
        "",
        "## 文档说明",
        "",
        "- **文档目的**：把 5 个样例贷款在 BPS foreclosure 相关【所有表的全部字段】逐一列出，"
        "便于读者完整观察业务与数据的对应关系。doc 16 仅含各面板用到的部分字段，本表是其原始数据底座。",
        "- **目标读者**：数据工程师 · 业务分析师 · 验证人员 · 接入工程师 · 未来 AI 会话",
        "- **取数口径**：Newrez 源表 `dataasof=MAX`(每贷款)；`sync_fcl_stage_info` `fctrdt=MAX`；"
        "sync 基础表当前态；视图取每贷款 `fctrdt` 最新一行。日期统一 `YYYY-MM-DD`；空值显示 `—`。",
        "- **排版**：1 行/贷款的表 → 转置（字段为行 × 5 贷款列）；多行/贷款的表（hold/lm/bk）→ "
        "平铺（记录为行 × 全字段列）。",
        "",
        "### 修订历史",
        "",
        "| 日期 | 作者 | 版本 | 变更 | 关联 |",
        "|---|---|---|---|---|",
        f"| {X.RUN_DATE} | AI Agent (Claude Opus 4.8) | v1 | 初稿：12 节，与 doc 19 xlsx 一一对应；"
        "所有取值 DB 实测 | doc 16 · doc 19 xlsx |",
        "",
    ]

    # ── 预取所有数据 + 列数 ──
    tdata = {}   # table -> {loan: row_dict}
    tcols = {}   # table -> [col...]
    for title, sch, tab, kind, desc in X.TRANSPOSE:
        tcols[tab] = X.cols_of(cur, sch, tab)
        tdata[tab] = {lid: X.one_row(cur, sch, tab, lid, kind) for lid in L}
    fdata = {}   # table -> (cols, rows)
    for title, tab, sortcol, desc in X.FLAT:
        fdata[tab] = X.all_rows(cur, tab, sortcol)

    # ── 表清单 / 索引 ──
    out += ["## 一、表清单 / 索引", "",
            "### Newrez 源数据表（5）", ""]
    rows = []
    for title, sch, tab, kind, desc in X.TRANSPOSE[:5]:
        present = sum(1 for d in tdata[tab].values() if d)
        rows.append([f"{sch}.{tab}", desc, str(len(tcols[tab])), f"{present}/5 贷款"])
    out += md_table(["表", "用途", "列数", "本dump命中"], rows)
    out += ["", "### BPS 直接对接表（5 基础表 + 1 视图）", ""]
    rows = []
    bps_t = [X.TRANSPOSE[5], X.TRANSPOSE[6]]
    for title, sch, tab, kind, desc in bps_t:
        present = sum(1 for d in tdata[tab].values() if d)
        rows.append([f"{sch}.{tab}", desc, str(len(tcols[tab])), f"{present}/5 贷款"])
    for title, tab, sortcol, desc in X.FLAT:
        cols, recs = fdata[tab]
        rows.append([f"bpms_dev.{tab}", desc, str(len(cols)), f"{len(recs)} 行"])
    vt = X.TRANSPOSE[7]
    present = sum(1 for d in tdata[vt[2]].values() if d)
    rows.append([f"bpms_dev.{vt[2]}（视图）", vt[4], str(len(tcols[vt[2]])), f"{present}/5 贷款"])
    out += md_table(["表 / 视图", "用途", "列数", "本dump行"], rows)
    out += ["", "### 不纳入本转储的表（中间层 / dev 不存在）", ""]
    out += md_table(["表", "原因"], [
        ["newrez.portnewrezdatadic", "数值码解码字典；dev newrez 无此表，解码在 Redshift 完成"],
        ["port.basic_data_loan_foreclosure*", "Redshift→MySQL 间的中间表，非源表也非 BPS 直接展示表"],
        ["port.portfunding", "融资池过滤表（JOIN 条件），非业务字段来源"],
    ])
    out += ["", "### 样例贷款（5）", ""]
    out += md_table(["#", "loanid —— 选取理由"],
                    [[f"Loan {i}", f"{lid} —— {desc}"] for i, (lid, desc) in enumerate(X.LOANS, 1)])
    out += [""]

    # ── 转置组：字段为行 × 5 贷款列 ──
    SNAP = {"newrez": "dataasof=MAX(每贷款)", "stage": "fctrdt=MAX(每贷款)",
            "view": "每贷款 fctrdt 最新一行", "current": "当前态(1行/贷款)"}
    for title, sch, tab, kind, desc in X.TRANSPOSE:
        cols = tcols[tab]
        rows_d = tdata[tab]
        present = sum(1 for d in rows_d.values() if d)
        out += ["---", "", f"## {title.split(chr(183))[-1].strip()} — {sch}.{tab}", "",
                f"> {desc}。全 **{len(cols)}** 字段 · 取数口径：{SNAP[kind]} · 命中 {present}/5 贷款"
                "（无行的贷款列显示 `—`）。", ""]
        body = []
        for col in cols:
            body.append([col] + [(rows_d[lid].get(col) if rows_d[lid] else "—") for lid in L])
        out += md_table(["字段"] + L, body)
        out += [""]

    # ── 平铺组：记录为行 × 全字段列 ──
    for title, tab, sortcol, desc in X.FLAT:
        cols, recs = fdata[tab]
        per = {}
        for d in recs:
            per[str(d["loanid"])] = per.get(str(d["loanid"]), 0) + 1
        out += ["---", "", f"## {title.split(chr(183))[-1].strip()} — bpms_dev.{tab}", "",
                f"> {desc}。全 **{len(cols)}** 字段 · 当前态(多行/贷款) · 共 **{len(recs)}** 行 · "
                f"各贷款行数：{per}。", ""]
        body = [[d.get(c) for c in cols] for d in recs]
        out += md_table(cols, body)
        out += [""]

    cur.close()
    conn.close()
    OUT.write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"已保存：{OUT}")
    print(f"行数：{len(out)}")


if __name__ == "__main__":
    main()
