"""Sinh du lieu mau cho giao dien va de thu ham doc CSV.

    python scripts/make_demo_data.py

Tao:
  data/samples/Q_demo.csv          Q-matrix GIA: moi khai niem 2 cau <id>_q1, <id>_q2
  data/samples/responses_demo.csv  bai lam GIA cua 4 sinh vien (dang dai)
Q that la san pham cua C (data/Q_v1.csv, nhiem vu 2.3).
"""

import csv
import sys
from pathlib import Path

import networkx as nx

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from diagnosis.io import load_graph_from_files  # noqa: E402

SCENARIOS = {
    "SV_A_hong_de_quy": ["C01_09"],
    "SV_B_hong_DSLK_va_BST": ["C03_09", "C04_07"],
    "SV_C_chi_sai_Dijkstra": ["C05_08"],
    "SV_D_vung_het": [],
}


def main() -> None:
    G, _ = load_graph_from_files(ROOT / "data/concepts_v0.csv", ROOT / "data/edges_v0.csv")
    out = ROOT / "data/samples"
    out.mkdir(parents=True, exist_ok=True)
    with open(out / "Q_demo.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["item_id", "concept_id", "weight"])
        for c in G.nodes:
            for k in (1, 2):
                w.writerow([f"{c}_q{k}", c, 1])
    with open(out / "responses_demo.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["student_id", "item_id", "score"])
        for sid, roots in SCENARIOS.items():
            weak = set()
            for r in roots:
                weak |= {r} | nx.descendants(G, r)
            for c in G.nodes:
                for k in (1, 2):
                    w.writerow([sid, f"{c}_q{k}", 0 if c in weak else 1])
    print(f"Da ghi {out / 'Q_demo.csv'} va {out / 'responses_demo.csv'}")


if __name__ == "__main__":
    main()
