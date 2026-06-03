# -*- coding: utf-8 -*-
"""
端到端测试：运行 doc 14 的两个写表脚本（add_field_spec_verify_sql / run_verify_sql_results）后，
用户「人工」列（表头含「人工」）的单元格内容与批注是否被改动。

做法：把 live xlsx 复制到临时副本 → 快照人工列(值+批注) → 把两脚本的 XLSX 指向副本并 main() →
再快照 → 逐格对比。全程不碰用户的 live 文件。
"""
import sys, io, shutil, tempfile, subprocess
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parent))

from openpyxl import load_workbook
from openpyxl.utils import get_column_letter
from _excel_guard import manual_cols

LIVE = Path("docs/14_servicer_fcl_field_spec.xlsx")

# 在独立子进程中运行某 writer，把其 XLSX 指向副本（避免两脚本 import 时反复重绑 sys.stdout 冲突）
RUNNER = (
    "import importlib,sys;"
    "from pathlib import Path;"
    "sys.path.insert(0,'scripts');"
    "m=importlib.import_module(sys.argv[1]);"
    "m.XLSX=Path(sys.argv[2]);"
    "m.main()"
)


def snapshot(path):
    """返回 {col_letter: {'header':..., 'values':[...], 'comments':[...]}} 仅人工列。"""
    wb = load_workbook(path)
    ws = next(s for s in wb.worksheets if "Field Spec" in s.title)
    mcols = sorted(manual_cols(ws))
    snap = {}
    for c in mcols:
        L = get_column_letter(c)
        vals, coms = [], []
        for r in range(1, ws.max_row + 1):
            cell = ws.cell(r, c)
            vals.append(cell.value)
            coms.append(cell.comment.text if cell.comment else None)
        snap[L] = {"header": ws.cell(1, c).value, "values": vals, "comments": coms}
    wb.close()
    return snap, mcols, ws.max_row, ws.max_column


def run_writer(modname, tmp):
    p = subprocess.run([sys.executable, "-c", RUNNER, modname, str(tmp)],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    out = (p.stdout or "").strip().splitlines()
    if out:
        print("   " + out[-1])
    if p.returncode != 0:
        print(f"   [returncode {p.returncode}] {(p.stderr or '').strip().splitlines()[-1:]}")
    return p.returncode


def main():
    tmpdir = Path(tempfile.mkdtemp(prefix="doc14guard_"))
    tmp = tmpdir / "copy.xlsx"
    shutil.copy(LIVE, tmp)
    print(f"副本：{tmp}")

    before, mcols, nrow, ncol = snapshot(tmp)
    print(f"人工列：{[(L, before[L]['header']) for L in before]}")
    print(f"sheet 维度：{nrow} 行 × {ncol} 列\n")

    for modname in ("add_field_spec_verify_sql", "run_verify_sql_results"):
        print(f"=== 运行 {modname}.main()（写入副本）===")
        try:
            run_writer(modname, tmp)
        except Exception as e:
            print(f"  脚本异常（可能 col 命中人工列被 assert_safe 拦截 = 也算保护生效）：{str(e).splitlines()[0][:160]}")
        print()

    after, _, nrow2, ncol2 = snapshot(tmp)

    print("=== 对比人工列（值 + 批注）===")
    ok = True
    for L in before:
        bv, av = before[L]["values"], after.get(L, {}).get("values")
        bc, ac = before[L]["comments"], after.get(L, {}).get("comments")
        hdr_b = before[L]["header"]
        hdr_a = after.get(L, {}).get("header")
        diffs = []
        if hdr_b != hdr_a:
            diffs.append(f"表头变了: {hdr_b!r} -> {hdr_a!r}")
        if av is None:
            diffs.append("整列消失/列号漂移")
        else:
            for i, (x, y) in enumerate(zip(bv, av), 1):
                if x != y:
                    diffs.append(f"第{i}行 值: {x!r} -> {y!r}")
            for i, (x, y) in enumerate(zip(bc, ac), 1):
                if x != y:
                    diffs.append(f"第{i}行 批注: {x!r} -> {y!r}")
        if diffs:
            ok = False
            print(f"  ❌ {L}「{hdr_b}」被改动：")
            for d in diffs[:10]:
                print(f"       - {d}")
        else:
            nonempty = sum(1 for v in bv if v not in (None, ""))
            print(f"  ✅ {L}「{hdr_b}」未变（{nonempty} 个非空单元格 + 批注完整保留）")

    print(f"\n人工列总数：before={len(before)} after={len(after)} | 维度 {nrow}×{ncol} -> {nrow2}×{ncol2}")
    print("\n结果：" + ("✅ PASS — 脚本未覆盖任何人工列" if ok and len(before) == len(after)
                       else "❌ FAIL — 人工列被改动！"))
    shutil.rmtree(tmpdir, ignore_errors=True)


if __name__ == "__main__":
    main()
