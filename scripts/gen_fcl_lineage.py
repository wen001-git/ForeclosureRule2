# -*- coding: utf-8 -*-
"""
Generate the foreclosure field-level data-lineage docs (hub 25 + per-table 26-30, zh+en)
from the single source of truth outputs/fcl_lineage_source.json.

Run via stdin (endpoint-security rule — do NOT execute a .py directly from the user dir):
    python - < scripts/gen_fcl_lineage.py
Working dir must be the project root.
"""
import json, io, os

ROOT = os.getcwd()
SRC = os.path.join(ROOT, "outputs", "fcl_lineage_source.json")
DOCS = os.path.join(ROOT, "docs")
DATE = "2026-06-09"

with io.open(SRC, encoding="utf-8") as f:
    D = json.load(f)

# ---- doc routing: (number, slug, branch-key or 'hub') ----
DOC_MAP = [
    ("25", "fcl_lineage_overview", "hub"),
    ("26", "lineage_sync_loan_foreclosure", "main"),
    ("27", "lineage_sync_fcl_stage_info", "stage"),
    ("28", "lineage_sync_loan_foreclosure_hold", "hold"),
    ("29", "lineage_sync_loan_foreclosure_loss_mitigation", "lm"),
    ("30", "lineage_sync_loan_foreclosure_bankruptcy", "bk"),
]
FAMILY_TITLE = {
    "milestone": {"en": "Timeline milestones", "zh": "时间线里程碑"},
    "summary": {"en": "Summary / status", "zh": "汇总 / 状态"},
    "stage_dim": {"en": "Dimensions (group / judicial / state)", "zh": "维度（group / judicial / state）"},
    "stage_date": {"en": "Stage start dates", "zh": "阶段开始日期"},
    "stage_days": {"en": "Stage day counts", "zh": "阶段天数"},
    "hold": {"en": "Hold spans", "zh": "Hold 时段"},
    "lm": {"en": "Loss-Mitigation cycle", "zh": "损失缓释周期"},
    "bk": {"en": "Bankruptcy filing", "zh": "破产记录"},
    "identity": {"en": "Identity / key columns", "zh": "标识 / 主键列"},
    "target": {"en": "Target days (config; view defaults)", "zh": "目标天数（配置；视图默认）"},
    "variance": {"en": "Variance columns", "zh": "Variance 列"},
    "bid": {"en": "Bid approval columns", "zh": "Bid Approval 列"},
    "system": {"en": "System / audit columns", "zh": "系统 / 审计列"},
    "view": {"en": "View-computed columns", "zh": "视图计算列"},
    "other": {"en": "Other columns", "zh": "其他列"},
}


def L(v, lang):
    if isinstance(v, dict):
        return v.get(lang, v.get("en", ""))
    return v if v is not None else ""


def esc(s):
    return str(s).replace("|", "\\|").replace("\n", " ")


def short_tbl(t):
    # display the table without schema prefix noise but keep db.schema.table readable
    return t


def header(lang, num, title, purpose, audience, related):
    t = "文档目的" if lang == "zh" else "Document Purpose"
    a = "目标读者" if lang == "zh" else "Target Audience"
    r = "修订历史" if lang == "zh" else "Revision History"
    rel = "相关文档" if lang == "zh" else "Related Documents"
    cols = ("日期 | 作者 | 版本 | 变更 | 关联" if lang == "zh"
            else "Date | Author | Version | Changes | Related")
    revs = D["meta"].get("revisions") or [{"date": DATE, "ver": "v1",
            "zh": "初稿（由 fcl_lineage_source.json 生成）", "en": "Initial draft (generated from fcl_lineage_source.json)"}]
    rev_rows = "\n".join("| %s | AI Agent | %s | %s | doc 02 · doc 13 · doc 14 |"
                         % (rv["date"], rv["ver"], esc(rv["zh"] if lang == "zh" else rv["en"]))
                         for rv in revs)
    out = []
    out.append("# Doc %s · %s\n" % (num, title))
    out.append("> %s\n" % ("**自动生成** —— 改动请编辑 `outputs/fcl_lineage_source.json` 后重跑 `python - < scripts/gen_fcl_lineage.py`，勿手改本文件。" if lang == "zh"
               else "**Auto-generated** — to change, edit `outputs/fcl_lineage_source.json` and re-run `python - < scripts/gen_fcl_lineage.py`; do not hand-edit this file."))
    out.append("\n## %s\n\n%s\n" % (t, purpose))
    out.append("## %s\n\n%s\n" % (a, audience))
    out.append("## %s\n\n| %s |\n|---|---|---|---|---|\n%s\n" % (r, cols, rev_rows))
    out.append("## %s\n\n%s\n" % (rel, related))
    out.append("\n---\n")
    return "\n".join(out)


def chain_md(branch, lang):
    ch = D["branches"][branch]["chain"]
    parts = []
    for h in ch:
        parts.append("`%s`" % h["table"])
    arrow = " → ".join(parts)
    lines = ["**%s**\n" % ("规范跳链 / canonical hop chain" if lang == "zh" else "Canonical hop chain"), "", arrow, ""]
    lines.append("| # | layer | db | %s | role |" % ("表 table" if lang == "zh" else "table"))
    lines.append("|---|---|---|---|---|")
    for i, h in enumerate(ch, 1):
        lines.append("| %d | %s | %s | `%s` | %s |" % (i, h["layer"], h["db"], h["table"], esc(h["role"])))
    lines.append("")
    return "\n".join(lines)


def _codecell(c):
    import re
    if c and re.match(r'^[a-z][a-z0-9_]*\.[a-z0-9_.]+$', c):
        return "`%s`" % esc(c)
    return esc(c) if c else ""


def servicer_source_table(fields, lang):
    """Per-servicer L1 source columns: Field | Newrez | Carrington | Capecodfive."""
    cap = ("> 各 servicer 来源（newrez.* / carrington.portcarrington / capecodfive.portcapecodfive_monthly_collections）；`—` 表示该 servicer 不提供。"
           if lang == "zh" else
           "> Source per servicer (newrez.* / carrington.portcarrington / capecodfive.portcapecodfive_monthly_collections); `—` = not provided by that servicer.")
    hdr = [("字段 Field" if lang == "zh" else "Field"), "Newrez", "Carrington", "Capecodfive"]
    out = [cap, "", "| " + " | ".join(hdr) + " |", "|" + "---|" * len(hdr)]
    for fld in fields:
        s = fld.get("servicers", {})
        row = ["**%s**" % esc(L(fld["label"], lang)), _codecell(s.get("Newrez", "—")),
               _codecell(s.get("Carrington", "—")), _codecell(s.get("Capecodfive", "—"))]
        out.append("| " + " | ".join(row) + " |")
    return "\n".join(out) + "\n"


def field_matrix(fields, branch, lang, hop_start=0):
    """One row per field; columns = chain tables from hop_start onward + rule/code.
    hop_start=0 -> full chain incl. raw; hop_start=1 -> pipeline only (fact->BPS), raw shown separately."""
    ch = D["branches"][branch]["chain"]
    nhop = len(ch)
    # header
    hdr = ["%s" % ("字段 Field" if lang == "zh" else "Field")]
    for h in ch[hop_start:]:
        hdr.append(h["table"].split(".")[-1])
    hdr.append("规则·代码 / rule·code" if lang == "zh" else "rule · code")
    out = ["| " + " | ".join(hdr) + " |"]
    out.append("|" + "---|" * len(hdr))
    sql_blocks = []
    for fld in fields:
        row = ["**%s**" % esc(L(fld["label"], lang))]
        hops = fld["hops"]
        for i in range(hop_start, nhop):
            c = hops[i]["c"] if i < len(hops) else ""
            row.append("`%s`" % esc(c) if c and c not in ("(none)", "(n/a)", "—") else esc(c))
        # rule+code cell: per-hop rules joined (only the displayed hops)
        rules = []
        for h in hops[hop_start:]:
            code = (" [%s]" % h["code"]) if h.get("code") else ""
            if h["rule"] and h["rule"] not in ("—",):
                rules.append("%s%s" % (esc(h["rule"]), code))
        cell = " · ".join(rules)
        if fld.get("status") and fld["status"] != "ok":
            cell = "⚠ %s · %s" % (fld["status"], cell)
        row.append(cell)
        out.append("| " + " | ".join(row) + " |")
        if fld.get("sql"):
            sql_blocks.append(fld)
    md = "\n".join(out) + "\n"
    # notes + sql blocks after the table
    notes = []
    for fld in fields:
        if fld.get("note"):
            notes.append("- **%s** — %s" % (esc(L(fld["label"], lang)), esc(L(fld["note"], lang))))
    if notes:
        md += "\n" + "\n".join(notes) + "\n"
    if sql_blocks:
        md += "\n**%s**\n\n" % ("非平凡转换 SQL（含说明与示例）/ non-trivial transform SQL (with explanation & example)" if lang == "zh" else "Non-trivial transform SQL (with explanation & example)")
        for fld in sql_blocks:
            md += "*%s*\n\n```sql\n%s\n```\n" % (esc(L(fld["label"], lang)), fld["sql"])
            if fld.get("sql_note"):
                md += "\n🔎 **%s** %s\n" % ("说明" if lang == "zh" else "How it works:", esc(L(fld["sql_note"], lang)))
            if fld.get("sql_eg"):
                md += "\n▶ **%s** %s\n" % ("示例" if lang == "zh" else "Example:", esc(L(fld["sql_eg"], lang)))
            md += "\n"
    return md


SCH = {"Newrez": "newrez", "Carrington": "carrington", "Capecodfive": "capecodfive"}
CIRC = "①②③④⑤⑥⑦⑧⑨⑩"


def _hopcell(h):
    t = h["t"]
    c = h.get("c", "")
    if c in ("(none)", "(n/a)", "—", ""):
        return "`%s`" % t
    if t.startswith("(") or " " in c or "/" in c or "," in c:
        return "`%s` · %s" % (t, esc(c))
    return "`%s.%s`" % (t, esc(c))


def _sqlblock(out, fld, lang):
    out.append("")
    out.append("```sql\n%s\n```" % fld["sql"])
    if fld.get("sql_note"):
        out.append("🔎 **%s** %s" % ("说明" if lang == "zh" else "How it works:", esc(L(fld["sql_note"], lang))))
    if fld.get("sql_eg"):
        out.append("▶ **%s** %s" % ("示例" if lang == "zh" else "Example:", esc(L(fld["sql_eg"], lang))))


def field_card(fld, branch, lang, idx=None):
    """Vertical per-field card: heading + source(per servicer) + numbered per-hop lineage + rule + SQL."""
    hops = fld["hops"]
    fam = fld.get("family")
    sync = next((h for h in hops if h["t"].startswith("bpms.")), hops[-1])
    prefix = ("%d. " % idx) if idx is not None else ""
    # grouped (system/audit) and view-computed cards: no servicer/lineage scaffolding
    if fam in ("system", "view"):
        out = ["### %s%s" % (prefix, esc(L(fld["label"], lang))), ""]
        if fld.get("biz"):
            out += ["_%s_" % esc(L(fld["biz"], lang)), ""]
        out.append("**%s** `%s`" % ("列 / Columns:" if lang == "zh" else "Columns:", esc(sync.get("c", ""))))
        if fld.get("note"):
            out += ["", "**%s** %s" % ("说明 / Note:" if lang == "zh" else "Note:", esc(L(fld["note"], lang)))]
        if fld.get("sql"):
            _sqlblock(out, fld, lang)
        out.append("")
        return "\n".join(out)
    tbl = sync["t"].split(".", 1)[1] if "." in sync["t"] else sync["t"]
    out = ["### %s%s  (`bpms.%s.%s`)" % (prefix, esc(L(fld["label"], lang)), tbl, esc(sync["c"])), ""]
    if fld.get("biz"):
        out += ["_%s_" % esc(L(fld["biz"], lang)), ""]
    if fld.get("status") and fld["status"] != "ok":
        out += ["> ⚠ %s" % fld["status"], ""]
    # Source per servicer
    out.append("**%s**" % ("来源 / Source (L1)" if lang == "zh" else "Source (L1)"))
    sv = fld.get("servicers")
    if sv:
        for srv in ["Newrez", "Carrington", "Capecodfive"]:
            v = sv.get(srv, "—")
            out.append("- %s: %s" % (srv, "—" if v == "—" else "`%s.%s`" % (SCH[srv], v)))
    else:
        out.append("- Newrez: %s  %s" % (_hopcell(hops[0]), "（仅 Newrez 提供此明细）" if lang == "zh" else "(Newrez-only detail)"))
    out.append("")
    # numbered per-hop lineage + a one-line flow order
    start = 1 if sv else 0
    chain = hops[start:]
    flow = " → ".join("%s%s" % (CIRC[i] if i < len(CIRC) else str(i + 1), h["t"].split(".")[-1].split(" ")[0]) for i, h in enumerate(chain))
    out.append("**%s** %s" % ("流动顺序 / Flow:" if lang == "zh" else "Flow:", flow))
    out.append("**%s**" % ("血缘（逐跳：序号 列 — 规则 [代码]）/ Lineage (per hop)" if lang == "zh" else "Lineage (per hop: # column — rule [code])"))
    for i, h in enumerate(chain, 1):
        rule = esc(h["rule"]) if h.get("rule") and h["rule"] != "—" else "—"
        code = (" [%s]" % h["code"]) if h.get("code") else ""
        out.append("- %d. %s — %s%s" % (i, _hopcell(h), rule, code))
    if fld.get("servicer_rule"):
        out += ["", "**%s** %s" % ("规则（完整）/ Rule (full):" if lang == "zh" else "Rule (full):", esc(L(fld["servicer_rule"], lang)))]
    if fld.get("note"):
        out += ["", "**%s** %s" % ("说明 / Note:" if lang == "zh" else "Note:", esc(L(fld["note"], lang)))]
    if fld.get("sql"):
        _sqlblock(out, fld, lang)
    out.append("")
    return "\n".join(out)


def gen_per_table(num, slug, branch, lang):
    b = D["branches"][branch]
    bps = b["bps_table"]
    title = "%s — %s" % (L(b["title"], lang), "`bpms.%s` 字段血缘" % bps if lang == "zh" else "`bpms.%s` field lineage" % bps)
    purpose = (("逐字段追踪 BPS 表 `bpms.%s` 的每个字段：从 Servicer 原始列，经每一张中间表，到最终 BPS 列，并给出每一跳的转换规则与代码出处。" % bps) if lang == "zh"
               else ("Per-field lineage for BPS table `bpms.%s`: from the Servicer raw column, through every intermediate table, to the final BPS column, with each hop's transform rule and code reference." % bps))
    audience = ("数据工程师 · 分析师 · 校验人员 · 未来 AI 会话" if lang == "zh" else "data engineers · analysts · validators · future AI sessions")
    related = ("doc 02（ETL 管道，表级）· doc 13/14（字段映射）· doc 25（血缘总览）· 源码 PrefectFlow（见各跳 code）" if lang == "zh"
               else "doc 02 (ETL pipeline, table-level) · doc 13/14 (field mappings) · doc 25 (lineage hub) · PrefectFlow source (per-hop code refs)")
    out = [header(lang, num, title, purpose, audience, related)]
    out.append(chain_md(branch, lang))
    if D["meta"].get("chain_note"):
        out.append("> %s\n" % esc(L(D["meta"]["chain_note"], lang)))
    # code legend line
    cl = D["meta"]["code_legend"]
    out.append("> code: `pool` = %s · `asset` = %s · `view` = %s\n" % (cl["pool"], cl["asset"], cl["view"]))
    if branch in ("lm", "bk"):
        out.append("> %s\n" % esc(L(D["decode_note"], lang)))
    # families present in this branch
    fields = [f for f in D["fields"] if f["bps_table"] == bps]
    fams = []
    for f in fields:
        if f["family"] not in fams:
            fams.append(f["family"])
    cardno = 0
    total = len(fields)
    for fam in fams:
        ff = [f for f in fields if f["family"] == fam]
        out.append("\n## %s\n" % L(FAMILY_TITLE.get(fam, {"en": fam, "zh": fam}), lang))
        if branch in ("lm", "bk"):
            out.append("> %s\n" % ("仅 Newrez 提供该明细（Carrington 等不在此表构建）。" if lang == "zh" else "Newrez-only detail (Carrington/others are not built in this table)."))
        for fld in ff:
            cardno += 1
            out.append(field_card(fld, branch, lang, cardno))
    out.append("\n> %s\n" % (("本文档共 %d 个字段。" % total) if lang == "zh" else "This doc covers %d fields." % total))
    return "\n".join(out)


def gen_hub(num, lang):
    title = ("止赎字段血缘 · 总览（hub）" if lang == "zh" else "Foreclosure field lineage · overview (hub)")
    purpose = (("止赎核心字段从 Servicer 原始列到 BPS sync 表的**字段级**数据血缘总入口：规范跳链骨架 + 全字段主索引 + 指向各 BPS 表明细文档（doc 26–30）的链接。规则 Code-First 取自 PrefectFlow；列名已对 prod（redshift_prod / mysql_prod）核验。补充 doc 02（表级管道）。取代 doc 21。" ) if lang == "zh"
               else ("Hub for the **field-level** data lineage of core foreclosure fields, Servicer raw → BPS sync tables: the canonical hop-chain skeletons, a master field index, and links to the per-BPS-table detail docs (26–30). Rules are Code-First from PrefectFlow; columns schema-verified against prod (redshift_prod / mysql_prod). Complements doc 02 (table-level). Supersedes doc 21."))
    audience = ("数据工程师 · 分析师 · 校验人员 · 业务分析 · 未来 AI 会话" if lang == "zh" else "data engineers · analysts · validators · business analysts · future AI sessions")
    related = ("doc 02（ETL 管道）· doc 13（BPS 视图字段映射）· doc 14（Servicer FCL 字段规范）· doc 26–30（各 sync 表字段血缘）· ~~doc 21~~（已弃用）" if lang == "zh"
               else "doc 02 (ETL pipeline) · doc 13 (BPS view field mapping) · doc 14 (Servicer FCL field spec) · doc 26–30 (per-table lineage) · ~~doc 21~~ (superseded)")
    out = [header(lang, num, title, purpose, audience, related)]
    # how to read
    out.append("## %s\n" % ("怎么读这套血缘" if lang == "zh" else "How to read this lineage"))
    out.append(("每个 **BPS sync 表**一篇明细文档（doc 26–30）。每篇里 **一行 = 一个字段**，列 = 该字段在链路上每一张表的列名，最后一列给出**每一跳的转换规则 + 代码出处**（`pool`/`asset`/`view`，见下）。非平凡转换（CASE/解码/unpivot/天数）附真实 SQL。\n" ) if lang == "zh"
               else ("One detail doc per **BPS sync table** (doc 26–30). In each, **one row = one field**; columns are the field's column name at every table along its chain; the last column gives the **per-hop transform rule + code reference** (`pool`/`asset`/`view`, see below). Non-trivial transforms (CASE / decode / unpivot / day-math) include the real SQL.\n"))
    cl = D["meta"]["code_legend"]
    out.append("> code: `pool` = %s · `asset` = %s · `view` = %s\n" % (cl["pool"], cl["asset"], cl["view"]))
    out.append("> %s\n" % esc(L(D["meta"]["servicer_note"], lang)))
    out.append("> %s\n" % esc(D["meta"]["snapshot"]))
    # skeletons
    out.append("\n## %s\n" % ("规范跳链骨架（4 条分支）" if lang == "zh" else "Canonical hop-chain skeletons (4 branches)"))
    for bk in ["main", "stage", "hold", "lm", "bk"]:
        out.append("### %s\n" % L(D["branches"][bk]["title"], lang))
        out.append(chain_md(bk, lang))
    if D["meta"].get("chain_note"):
        out.append("> %s\n" % esc(L(D["meta"]["chain_note"], lang)))
    out.append("> %s\n" % esc(L(D["decode_note"], lang)))
    # master index
    out.append("\n## %s\n" % ("全字段主索引" if lang == "zh" else "Master field index"))
    out.append("| %s | %s | %s | %s |" % (
        ("字段 Field" if lang == "zh" else "Field"),
        ("Servicer 原始列" if lang == "zh" else "Servicer raw col"),
        ("BPS sync 表" if lang == "zh" else "BPS sync table"),
        ("最终 BPS 列 + 明细文档" if lang == "zh" else "final BPS col + detail doc")))
    out.append("|---|---|---|---|")
    doc_of = {b: n for n, s, b in DOC_MAP}
    for f in D["fields"]:
        raw = f["hops"][0]["c"]
        rawt = f["hops"][0]["t"]
        final = f["hops"][-1]["c"] if f["branch"] != "main" else (f["hops"][-2]["c"] if len(f["hops"]) >= 2 else f["hops"][-1]["c"])
        # use the sync (L5) hop = second-to-last for main (last is view), last for others
        sync_hop = None
        for h in f["hops"]:
            if h["t"].startswith("bpms.sync"):
                sync_hop = h
        finalc = sync_hop["c"] if sync_hop else final
        docn = doc_of.get(f["branch"], "")
        out.append("| %s | `%s` | `%s` | `%s` (→ doc %s) |" % (
            esc(L(f["label"], lang)),
            esc(raw) if raw not in ("(none)", "(n/a)") else "—",
            f["bps_table"],
            esc(finalc), docn))
    out.append("")
    # gaps
    gaps = [f for f in D["fields"] if f.get("status") and f["status"] != "ok"]
    out.append("\n## %s\n" % ("已知缺口 / 空值字段" if lang == "zh" else "Known gaps / null fields"))
    if gaps:
        out.append("| %s | %s | %s |" % (("字段" if lang == "zh" else "Field"), "status", ("说明" if lang == "zh" else "note")))
        out.append("|---|---|---|")
        for f in gaps:
            out.append("| %s | `%s` | %s |" % (esc(L(f["label"], lang)), f["status"], esc(L(f.get("note", ""), lang))))
    out.append("\n> %s\n" % (("此外：L3 中间表 `port.basic_data_loan_delinq_clean` 的生产代码不在 PrefectFlow 仓库内（仅按名引用）；SLS/MRC 等 servicer 不上报 FCL 明细。" ) if lang == "zh"
               else "Also: the L3 producer of `port.basic_data_loan_delinq_clean` is not in the PrefectFlow repo (referenced by name only); SLS/MRC and other servicers report no FCL detail."))
    # worked trace (optional)
    wt = D.get("meta", {}).get("worked_trace")
    if wt:
        out.append("\n## %s\n" % ("端到端样例（MCP 实测）" if lang == "zh" else "End-to-end worked trace (MCP-verified)"))
        out.append(L(wt.get("intro", ""), lang) + "\n")
        for tr in wt.get("fields", []):
            out.append("**%s** — loan `%s`\n" % (esc(L(tr["label"], lang)), wt.get("loanid", "")))
            out.append("| hop | table.column | value |")
            out.append("|---|---|---|")
            for st in tr["steps"]:
                out.append("| %s | `%s` | `%s` |" % (esc(st.get("hop", "")), esc(st["tc"]), esc(st["val"])))
            out.append("")
    # links
    out.append("\n## %s\n" % ("各 BPS 表明细文档" if lang == "zh" else "Per-table detail docs"))
    for n, s, b in DOC_MAP:
        if b == "hub":
            continue
        out.append("- **doc %s** — `bpms.%s` (%s)" % (n, D["branches"][b]["bps_table"], L(D["branches"][b]["title"], lang)))
    return "\n".join(out)


written = []
for num, slug, branch in DOC_MAP:
    for lang in ("zh", "en"):
        if branch == "hub":
            body = gen_hub(num, lang)
        else:
            body = gen_per_table(num, slug, branch, lang)
        path = os.path.join(DOCS, lang, "%s_%s.md" % (num, slug))
        with io.open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(body.rstrip() + "\n")
        written.append(path)

print("generated %d files:" % len(written))
for p in written:
    print(" ", os.path.relpath(p, ROOT).replace("\\", "/"))
