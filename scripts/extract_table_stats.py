"""
extract_table_stats.py — 取值范围/类型 实测提取器（for foreclosure_data_dictionary.md 表17/20-25）

连接 .mcp.json 所用的同一台 TEST 库（bridg004-db-test / bpms_dev，可跨 schema 查 newrez），
对每张目标表自动发现全部列，计算每列：非空数/空数/填充率/distinct/MIN/MAX；
低基数列(distinct<=LOW_CARD)额外取 Top 值计数。

性能：每表用「单次组合聚合」一遍扫描算完 COUNT/COUNT(DISTINCT)/MIN/MAX（视图只物化一次），
再仅对低基数列各跑一条 GROUP BY。输出 JSON 到 outputs/table_stats_for_data_dictionary.json。

与 MCP 查询同库同源，仅为批量化、可复现的 DB 验证手段（项目 db_stats_mysql.py 同款做法）。只读。
"""
import json
import os
import pymysql

# DB 凭据从环境变量读取（勿硬编码）：必填 FCL_DB_PASSWORD；host/port/user 有默认值，可用同名环境变量覆盖
HOST = os.environ.get("FCL_DB_HOST", "bridg004-db-test.mysql.database.azure.com")
PORT = int(os.environ.get("FCL_DB_PORT", "3306"))
USER = os.environ.get("FCL_DB_USER", "brgdev")
PASSWORD = os.environ.get("FCL_DB_PASSWORD")

LOW_CARD = 30  # distinct <= 此值的列额外取 Top 值分布

# (schema, table, snapshot_filter)  snapshot_filter 用于大表只在最新快照取分布
TARGETS = [
    ("bpms_dev", "sync_loan_foreclosure", None),
    ("newrez", "portnewrezbk", "dataasof = (SELECT MAX(dataasof) FROM `newrez`.`portnewrezbk`)"),
    ("bpms_dev", "sync_loan_foreclosure_hold", None),
    ("bpms_dev", "sync_loan_foreclosure_loss_mitigation", None),
    ("bpms_dev", "sync_loan_foreclosure_bankruptcy", None),
    ("bpms_dev", "sync_fcl_stage_info", None),
    ("bpms_dev", "biz_data_view_loan_details_foreclosure", None),
]


def get_columns(cur, schema, table):
    cur.execute(
        "SELECT ordinal_position, column_name, column_type, is_nullable, column_default "
        "FROM information_schema.columns WHERE table_schema=%s AND table_name=%s "
        "ORDER BY ordinal_position",
        (schema, table),
    )
    return [
        {"pos": r[0], "name": r[1], "type": r[2], "nullable": r[3], "default": r[4]}
        for r in cur.fetchall()
    ]


def combined_stats(cur, schema, table, cols, snap):
    """One pass: per column COUNT, COUNT(DISTINCT), MIN, MAX."""
    where = f" WHERE {snap}" if snap else ""
    parts = []
    for c in cols:
        n = c["name"]
        parts.append(f"COUNT(`{n}`)")
        parts.append(f"COUNT(DISTINCT `{n}`)")
        parts.append(f"MIN(`{n}`)")
        parts.append(f"MAX(`{n}`)")
    cur.execute(f"SELECT {', '.join(parts)} FROM `{schema}`.`{table}`{where}")
    row = cur.fetchone()
    res = {}
    for i, c in enumerate(cols):
        base = i * 4
        res[c["name"]] = {
            "non_null": row[base],
            "distinct": row[base + 1],
            "min": str(row[base + 2]),
            "max": str(row[base + 3]),
        }
    return res


def top_values(cur, schema, table, col, snap):
    where = f" WHERE {snap}" if snap else ""
    cur.execute(
        f"SELECT `{col}`, COUNT(*) c FROM `{schema}`.`{table}`{where} "
        f"GROUP BY `{col}` ORDER BY c DESC LIMIT {LOW_CARD}"
    )
    return [{"v": str(r[0]), "c": r[1]} for r in cur.fetchall()]


def main():
    conn = pymysql.connect(
        host=HOST, port=PORT, user=USER, password=PASSWORD,
        connect_timeout=20, charset="utf8mb4", ssl={"ssl": True},
    )
    cur = conn.cursor()
    out = {}
    for schema, table, snap in TARGETS:
        key = f"{schema}.{table}"
        print(f"--- {key} (snap={'latest' if snap else 'all'}) ---", flush=True)
        cur.execute(f"SELECT COUNT(*) FROM `{schema}`.`{table}`")
        total = cur.fetchone()[0]
        where = f" WHERE {snap}" if snap else ""
        cur.execute(f"SELECT COUNT(*) FROM `{schema}`.`{table}`{where}")
        snap_rows = cur.fetchone()[0]
        cols = get_columns(cur, schema, table)
        print(f"    rows={total} snap_rows={snap_rows} cols={len(cols)} -> combined pass", flush=True)
        stats = combined_stats(cur, schema, table, cols, snap)
        # top values only for low-card columns
        for c in cols:
            s = stats[c["name"]]
            s.update(type=c["type"], nullable=c["nullable"], default=c["default"], pos=c["pos"])
            s["null"] = snap_rows - s["non_null"]
            d = s["distinct"]
            if d is not None and 0 < d <= LOW_CARD:
                s["top"] = top_values(cur, schema, table, c["name"], snap)
        data = {"_total_rows": total, "_snapshot_rows": snap_rows,
                "_snapshot_filter": snap, "_col_count": len(cols), "columns": stats}
        out[key] = data
        print(f"    done {key}", flush=True)

    cur.close()
    conn.close()
    os.makedirs("outputs", exist_ok=True)
    path = "outputs/table_stats_for_data_dictionary.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2, default=str)
    print(f"\nDone -> {path}", flush=True)


if __name__ == "__main__":
    main()
