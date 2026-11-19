"""Demo bo chan doan M1 tren do thi THAT cua nhom (70 khai niem CTDL&GT).

    python scripts/demo_diagnosis.py

CHU Y: Q-matrix o day la Q GIA (moi khai niem 2 cau "<id>_q1", "<id>_q2") vi
Q-matrix that la san pham cua C (nhiem vu 2.3). Khi co data/Q_v1.csv thi thay.
"""

import sys
from pathlib import Path

import networkx as nx

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from diagnosis import diagnose, format_report, load_graph_from_files  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]


def demo_Q(concept_ids):
    return {f"{c}_q{k}": {c: 1.0} for c in concept_ids for k in (1, 2)}


def responses_for(weak, concept_ids):
    """SV gia: khai niem trong `weak` sai ca 2 cau, con lai dung ca 2."""
    return {f"{c}_q{k}": (0.0 if c in weak else 1.0) for c in concept_ids for k in (1, 2)}


def main() -> None:
    edges = ROOT / "data/edges_v0.csv"
    if not edges.exists():
        edges = ROOT / "scripts/init_db.py"
    G, concepts = load_graph_from_files(ROOT / "data/concepts_v0.csv", edges)
    ids = list(G.nodes)
    print(f"Đồ thị: {G.number_of_nodes()} khái niệm, {G.number_of_edges()} cạnh tiên quyết\n")
    Q = demo_Q(ids)

    scenarios = {
        "SV A - hổng đệ quy (C01_09)": {"C01_09"} | nx.descendants(G, "C01_09"),
        "SV B - hổng DSLK đơn (C03_09) và BST (C04_07)":
            {"C03_09", "C04_07"} | nx.descendants(G, "C03_09") | nx.descendants(G, "C04_07"),
        "SV C - chỉ sai bài toán đường đi ngắn nhất (C05_08)": {"C05_08"},
    }
    for title, weak in scenarios.items():
        print("=" * 70)
        print(title)
        print("=" * 70)
        res = diagnose(responses_for(weak, ids), Q, G)
        print(format_report(res, concepts, max_paths=3))
        print()


if __name__ == "__main__":
    main()
