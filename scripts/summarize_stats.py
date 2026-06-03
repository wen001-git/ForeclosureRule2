"""Summarize table_stats JSON into compact per-column 取值范围 lines (token-efficient)."""
import json

with open("outputs/table_stats_for_data_dictionary.json", encoding="utf-8") as f:
    data = json.load(f)


def fill(s, snap):
    nn = s["non_null"]
    pct = (nn / snap * 100) if snap else 0
    return f"{nn}/{snap}={pct:.0f}%"


def rng(s):
    t = s["type"]
    d = s["distinct"]
    if d == 0:
        return "实测全为 NULL"
    # low-card: list non-None top values
    if "top" in s:
        vals = [x["v"] for x in s["top"] if x["v"] != "None"]
        vals = vals[:20]
        if t.startswith(("int", "tinyint", "bigint", "decimal", "double", "float")):
            # numeric enum -> show min~max plus value set if small
            if d <= 12:
                return f"{{{', '.join(vals)}}}（{d}种）"
            return f"{s['min']} ~ {s['max']}（{d}种）"
        return f"{{{', '.join(vals)}}}" + ("" if d <= 20 else f" 等{d}种")
    # high-card
    if t.startswith("date") or t.startswith("datetime"):
        return f"{s['min']} ~ {s['max']}"
    if t.startswith(("int", "bigint", "decimal", "double", "float", "tinyint")):
        return f"{s['min']} ~ {s['max']}"
    # high-card text
    return f"文本，{d}种（样例 {s['min']} … {s['max']}）"


lines = []
for tk, td in data.items():
    lines.append(f"\n===== {tk}  rows={td['_total_rows']} snap={td['_snapshot_rows']} cols={td['_col_count']} =====")
    snap = td["_snapshot_rows"]
    for name, s in td["columns"].items():
        lines.append(f"[{s['pos']:>3}] {name} | {s['type']} | fill {fill(s, snap)} | 取值范围: {rng(s)}")

with open("outputs/stats_summary.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("wrote outputs/stats_summary.txt")
