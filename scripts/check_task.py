"""Kiem tra tu dong tung yeu cau cua nhiem vu 1.6.

    python scripts/check_task.py
"""

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import networkx as nx  # noqa: E402

from diagnosis import M1Params, diagnose, find_roots  # noqa: E402

results = []


def check(label, ok, detail=""):
    results.append(ok)
    print(f"  [{'OK ' if ok else 'LOI'}] {label}" + (f"  ({detail})" if detail else ""))


G = nx.DiGraph([("A", "B"), ("B", "C"), ("X", "C")])
Q = {f"{c}{k}": {c: 1} for c in "ABCX" for k in (1, 2)}
resp = {"A1": 1, "A2": 1, "B1": 0, "B2": 0, "C1": 0, "C2": 0, "X1": 1, "X2": 1}

print("\nNhiem vu 1.6 - Bo chan doan baseline M1 va ham tim nut goc\n")

print("Buoc 1. Giao dien chung")
res = diagnose(resp, Q, G)
check("diagnose(responses, Q, G) tra ve mastery, weak, roots, evidence",
      {"mastery", "weak", "roots", "evidence"} <= set(res))
check("mastery la dict, weak la set, roots la list, evidence la dict",
      isinstance(res["mastery"], dict) and isinstance(res["weak"], set)
      and isinstance(res["roots"], list) and isinstance(res["evidence"], dict))
ev = res["evidence"].get("B", {})
check("evidence cua nut goc co cau sai lien quan", ev.get("wrong_items") == ["B1", "B2"], str(ev.get("wrong_items")))
check("evidence cua nut goc co duong di tren do thi", ev.get("paths", {}).get("C") == ["B", "C"], str(ev.get("paths")))

print("\nBuoc 2. M1: trung binh hau nghiem Beta-Binomial")
cases = {(2, 2): 0.75, (1, 2): 0.50, (0, 2): 0.25}
ok = all(abs(diagnose({"A1": float(k >= 1), "A2": float(k >= 2)}, Q, G)["mastery"]["A"] - v) < 1e-9
         for (k, n), v in cases.items())
check("mastery = (so cau dung + 1) / (so cau + 2): 2/2 -> 0.75, 1/2 -> 0.50, 0/2 -> 0.25", ok)
check("'yeu' khi duoi nguong", res["weak"] == {"B", "C"}, str(sorted(res["weak"])))

print("\nBuoc 3. Outer fringe")
check("nut goc = chua vung va moi tien quyet deu vung", res["roots"] == ["B"], str(res["roots"]))
check("khai niem yeu co tien quyet yeu thi khong la goc", "C" not in find_roots(G, {"B", "C"}))

print("\nBuoc 4. Unit test do thi do choi 10 nut, 5 ca dung tay")
out = subprocess.run([sys.executable, "-m", "pytest", "-q", "-k", "five_hand_built_cases",
                      str(ROOT / "tests/test_diagnosis.py")], capture_output=True, text=True, cwd=ROOT)
m = re.search(r"(\d+) passed", out.stdout)
passed = int(m.group(1)) if m else 0
check("5/5 ca kiem thu dung nut goc", passed == 5 and out.returncode == 0, f"{passed}/5")

print("\nKhong nen: nhung nguong 0.6 cung trong code")
r1 = diagnose({"A1": 1, "A2": 0}, Q, G, M1Params(threshold=0.6))["weak"]
r2 = diagnose({"A1": 1, "A2": 0}, Q, G, M1Params(threshold=0.4))["weak"]
check("nguong la tham so M1Params(threshold=...) va thay doi duoc ket qua", "A" in r1 and "A" not in r2)
import ast  # noqa: E402

hard = []
for p in (ROOT / "diagnosis").glob("*.py"):
    tree = ast.parse(p.read_text(encoding="utf-8"))
    allowed = set()
    for node in ast.walk(tree):  # cho phep duy nhat: threshold: float = 0.6 trong M1Params
        if isinstance(node, ast.AnnAssign) and getattr(node.target, "id", "") == "threshold":
            allowed.add(id(node.value))
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and node.value == 0.6 and id(node) not in allowed:
            hard.append(f"{p.name}:{node.lineno}")
check("hang so 0.6 chi o gia tri mac dinh cua M1Params (khong nhung trong logic)", not hard, ", ".join(hard))

print("\nSan pham")
check("thu muc diagnosis/", (ROOT / "diagnosis/__init__.py").exists())
check("tests/test_diagnosis.py", (ROOT / "tests/test_diagnosis.py").exists())

print(f"\nKet qua: {sum(results)}/{len(results)} yeu cau dat.")
sys.exit(0 if all(results) else 1)
