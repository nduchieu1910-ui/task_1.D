"""Kiem tra bo chan doan tren do thi THAT cua nhom (data/concepts_v0.csv + canh REQUIRES).

Test tu bo qua neu repo chua co data/concepts_v0.csv.
"""

from pathlib import Path

import networkx as nx
import pytest

from diagnosis import (build_graph, diagnose, format_report, load_concepts,
                       load_graph_from_files, load_requires_from_init_db)

ROOT = Path(__file__).resolve().parents[1]
CONCEPTS = ROOT / "data/concepts_v0.csv"
EDGES_CSV = ROOT / "data/edges_v0.csv"
INIT_DB = ROOT / "scripts/init_db.py"

pytestmark = pytest.mark.skipif(not CONCEPTS.exists(), reason="chua co data/concepts_v0.csv")


@pytest.fixture(scope="module")
def real():
    edges = EDGES_CSV if EDGES_CSV.exists() else INIT_DB
    G, concepts = load_graph_from_files(CONCEPTS, edges)
    Q = {f"{c}_q{k}": {c: 1.0} for c in G.nodes for k in (1, 2)}
    return G, concepts, Q


def answers(G, weak):
    return {f"{c}_q{k}": (0.0 if c in weak else 1.0) for c in G.nodes for k in (1, 2)}


# ----------------------------- cau truc do thi -----------------------------


def test_graph_is_dag_with_all_concepts(real):
    G, concepts, _ = real
    assert G.number_of_nodes() == len(concepts) == 70
    assert nx.is_directed_acyclic_graph(G)


def test_edge_direction_follows_requires_convention(real):
    G, _, _ = real
    # init_db: ("C03_10", "C03_09") = duyet DSLK REQUIRES DSLK don
    # -> bo chan doan: C03_09 la tien quyet cua C03_10
    assert G.has_edge("C03_09", "C03_10")
    assert not G.has_edge("C03_10", "C03_09")
    assert [n for n in G if G.in_degree(n) == 0] == ["C01_01"]


def test_csv_and_init_db_give_same_edges():
    if not (EDGES_CSV.exists() and INIT_DB.exists()):
        pytest.skip("can ca data/edges_v0.csv va scripts/init_db.py")
    from diagnosis import load_requires_csv

    assert set(load_requires_csv(EDGES_CSV)) == set(load_requires_from_init_db(INIT_DB))


def test_build_graph_rejects_unknown_id_and_cycle():
    ids = ["A", "B"]
    with pytest.raises(ValueError, match="khong co trong danh sach"):
        build_graph(ids, [("A", "Z")])
    with pytest.raises(ValueError, match="chu trinh"):
        build_graph(ids, [("A", "B"), ("B", "A")])


def test_load_concepts_rejects_duplicate(tmp_path):
    p = tmp_path / "c.csv"
    p.write_text("concept_id,name_vi\nC01_01,a\nC01_01,b\n", encoding="utf-8")
    with pytest.raises(ValueError, match="trung"):
        load_concepts(p)


# ----------------------------- 5 ca tren do thi that -----------------------------


def closure(G, *roots):
    out = set(roots)
    for r in roots:
        out |= nx.descendants(G, r)
    return out


@pytest.mark.parametrize("roots", [
    pytest.param(["C01_09"], id="hong-de-quy-keo-cay-sap-xep-do-thi"),
    pytest.param(["C03_09"], id="hong-DSLK-don"),
    pytest.param(["C04_07"], id="hong-dinh-nghia-BST"),
    pytest.param(["C06_08"], id="chi-hong-nut-la-so-sanh-sap-xep"),
    pytest.param(["C04_07", "C07_05"], id="hai-goc-doc-lap-BST-va-ham-bam"),
])
@pytest.mark.parametrize("mode", ["direct", "ancestors"])
def test_root_recovered_when_root_and_all_descendants_are_weak(real, roots, mode):
    G, _, Q = real
    weak = closure(G, *roots)
    res = diagnose(answers(G, weak), Q, G, mode=mode)
    assert res["weak"] == weak
    assert set(res["roots"]) == set(roots)
    for r in roots:
        assert set(res["evidence"][r]["explains"]) <= weak


def test_root_with_more_explained_concepts_is_ranked_first(real):
    G, _, Q = real
    # C04_07 (BST) giai thich 7 khai niem, C07_05 (ham bam) chi 1
    res = diagnose(answers(G, closure(G, "C04_07", "C07_05")), Q, G)
    assert res["roots"] == ["C04_07", "C07_05"]


def test_report_prints_vietnamese_names_and_paths(real):
    G, concepts, Q = real
    res = diagnose(answers(G, closure(G, "C03_09")), Q, G)
    text = format_report(res, concepts)
    assert "C03_09 Danh sách liên kết đơn" in text
    assert "C03_09 -> " in text
