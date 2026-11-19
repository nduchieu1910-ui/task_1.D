"""Xuat INITIAL_REQUIRES_EDGES trong scripts/init_db.py (cua B) ra data/edges_v0.csv.

Chay lai moi khi B sua danh sach canh:
    python scripts/export_edges.py                       # mac dinh: ../scripts/init_db.py trong repo nhom
    python scripts/export_edges.py duong/dan/init_db.py
"""

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from diagnosis.io import build_graph, load_concepts, load_requires_from_init_db  # noqa: E402


def main() -> None:
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "scripts/init_db.py"
    if not src.exists():
        sys.exit(f"Khong thay {src}. Truyen duong dan: python scripts/export_edges.py <init_db.py>")
    pairs = load_requires_from_init_db(src)
    concepts = load_concepts(ROOT / "data/concepts_v0.csv")
    G = build_graph(concepts, pairs)  # bao loi ngay neu sai id hoac co chu trinh
    out = ROOT / "data/edges_v0.csv"
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["src", "dst", "relation", "status"])
        for a, b in pairs:
            w.writerow([a, b, "REQUIRES", "draft"])
    print(f"Da ghi {len(pairs)} canh vao {out} (do thi {G.number_of_nodes()} nut, khong chu trinh)")


if __name__ == "__main__":
    main()
