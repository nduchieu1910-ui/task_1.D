"""Chuan hoa Q-matrix va do thi tien quyet ve dang dung chung."""

from __future__ import annotations

from typing import Mapping

import networkx as nx

QDict = dict[str, dict[str, float]]  # item -> {concept: weight > 0}


def to_qdict(Q: object) -> QDict:
    """Nhan pandas.DataFrame (hang = cau, cot = khai niem) hoac dict long nhau."""
    if hasattr(Q, "iterrows"):  # pandas.DataFrame, khong bat buoc import pandas
        rows = {str(i): {str(c): float(v) for c, v in r.items() if v and v == v}
                for i, r in Q.iterrows()}
    elif isinstance(Q, Mapping):
        rows = {str(i): {str(c): float(w) for c, w in r.items() if w}
                for i, r in Q.items()}
    else:
        raise TypeError("Q phai la pandas.DataFrame hoac dict {item: {concept: weight}}")
    for item, row in rows.items():
        if not row:
            raise ValueError(f"Cau {item!r} khong gan khai niem nao trong Q-matrix")
        if any(w < 0 for w in row.values()):
            raise ValueError(f"Cau {item!r} co trong so am")
    return rows


def graph_from_requires(pairs, nodes=()) -> nx.DiGraph:
    """Tao G tu cac cap (A, B) nghia la (:Concept {id:A})-[:REQUIRES]->(:Concept {id:B}),
    tuc B la tien quyet cua A. Bo chan doan dung chieu nguoc lai: canh B -> A.

    pairs: iterable cac cap (A, B), vi du doc tu Cypher
        MATCH (a:Concept)-[:REQUIRES]->(b:Concept) RETURN a.id, b.id
    nodes: danh sach moi khai niem (de giu ca khai niem chua co canh).
    """
    G = nx.DiGraph()
    G.add_nodes_from(nodes)
    for a, b in pairs:
        G.add_edge(b, a)
    return G


def check_graph(G: nx.DiGraph, Q: QDict) -> None:
    """Canh A -> B nghia la A la tien quyet cua B. Do thi phai la DAG."""
    if not isinstance(G, nx.DiGraph):
        raise TypeError("G phai la networkx.DiGraph (canh: tien quyet -> phu thuoc)")
    if not nx.is_directed_acyclic_graph(G):
        cycle = nx.find_cycle(G)
        raise ValueError(f"Do thi tien quyet co chu trinh: {cycle}")
    missing = {c for row in Q.values() for c in row} - set(G.nodes)
    if missing:
        raise ValueError(f"Khai niem co trong Q nhung khong co trong G: {sorted(missing)}")
