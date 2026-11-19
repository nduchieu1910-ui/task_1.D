"""Do thi do choi 10 nut (CTDL&GT) dung chung cho cac test.

    array ----------> linked_list ---> stack_queue ---> graph_bfs
    pointer -------->      |                               ^
                           v                               |
    recursion -------> tree -----------------------------+
                           |
                           v
                          bst
    array -----> sorting <----- complexity
"""

import networkx as nx
import pytest

EDGES = [
    ("array", "linked_list"),
    ("pointer", "linked_list"),
    ("linked_list", "stack_queue"),
    ("array", "sorting"),
    ("complexity", "sorting"),
    ("recursion", "tree"),
    ("linked_list", "tree"),
    ("tree", "bst"),
    ("stack_queue", "graph_bfs"),
    ("tree", "graph_bfs"),
]
CONCEPTS = sorted({c for e in EDGES for c in e})
assert len(CONCEPTS) == 10


@pytest.fixture
def G():
    g = nx.DiGraph()
    g.add_nodes_from(CONCEPTS)
    g.add_edges_from(EDGES)
    return g


@pytest.fixture
def Q():
    """Moi khai niem 2 cau, moi cau gan dung 1 khai niem (trong so 1)."""
    return {f"{c}_{k}": {c: 1.0} for c in CONCEPTS for k in (1, 2)}


@pytest.fixture
def make_responses():
    """Khai niem trong `weak` sai ca 2 cau, con lai dung ca 2."""

    def _make(weak, skip=()):
        out = {}
        for c in CONCEPTS:
            if c in skip:
                continue
            s = 0.0 if c in weak else 1.0
            out[f"{c}_1"] = s
            out[f"{c}_2"] = s
        return out

    return _make
