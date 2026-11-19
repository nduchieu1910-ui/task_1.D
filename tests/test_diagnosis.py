import math

import networkx as nx
import pytest

from diagnosis import M1Params, diagnose, diagnose_batch, find_roots, graph_from_requires

# ---------------------------------------------------------------------------
# 5 ca dung tay co dap an nut goc (tieu chi "xong" cua nhiem vu 1.6)
# ---------------------------------------------------------------------------

CASES = [
    pytest.param(set(), [], id="ca1-khong-hong-gi"),
    pytest.param(
        {"pointer", "linked_list", "stack_queue", "tree", "bst", "graph_bfs"},
        ["pointer"],
        id="ca2-mot-goc-keo-ca-chuoi",
    ),
    pytest.param(
        {"recursion", "tree", "bst", "graph_bfs", "complexity", "sorting"},
        ["recursion", "complexity"],  # recursion giai thich 3 nut, complexity 1 nut
        id="ca3-hai-goc-doc-lap-xep-uu-tien",
    ),
    pytest.param({"bst"}, ["bst"], id="ca4-chi-hong-nut-la"),
    pytest.param(
        {"linked_list", "stack_queue", "tree", "bst", "graph_bfs"},
        ["linked_list"],  # tree yeu nhung recursion vung -> goc la linked_list
        id="ca5-goc-o-giua-do-thi",
    ),
]


@pytest.mark.parametrize("weak, expected_roots", CASES)
def test_five_hand_built_cases(G, Q, make_responses, weak, expected_roots):
    res = diagnose(make_responses(weak), Q, G)
    assert res["weak"] == weak
    assert res["roots"] == expected_roots


# ---------------------------------------------------------------------------
# Giao dien va dau vet bang chung
# ---------------------------------------------------------------------------


def test_output_keys_and_types(G, Q, make_responses):
    res = diagnose(make_responses({"bst"}), Q, G)
    assert {"mastery", "weak", "roots", "evidence"} <= set(res)
    assert set(res["mastery"]) == set(G.nodes)
    assert all(0.0 <= v <= 1.0 for v in res["mastery"].values())
    assert isinstance(res["weak"], set) and isinstance(res["roots"], list)


def test_evidence_contains_wrong_items_and_paths(G, Q, make_responses):
    weak = {"pointer", "linked_list", "stack_queue", "tree", "bst", "graph_bfs"}
    ev = diagnose(make_responses(weak), Q, G)["evidence"]["pointer"]
    assert ev["wrong_items"] == ["pointer_1", "pointer_2"]
    assert ev["explains"] == ["bst", "graph_bfs", "linked_list", "stack_queue", "tree"]
    assert ev["paths"]["bst"] == ["pointer", "linked_list", "tree", "bst"]
    assert ev["downstream_wrong_items"]["tree"] == ["tree_1", "tree_2"]


def test_mastery_is_beta_posterior_mean(G, Q, make_responses):
    res = diagnose(make_responses({"bst"}), Q, G)
    # prior Beta(1,1): 2 cau dung -> 3/4; 2 cau sai -> 1/4
    assert math.isclose(res["mastery"]["array"], 0.75)
    assert math.isclose(res["mastery"]["bst"], 0.25)
    assert res["details"]["bst"]["p_mastered"] < 0.2


# ---------------------------------------------------------------------------
# Cac loi de mac
# ---------------------------------------------------------------------------


def test_unobserved_concept_is_not_marked_weak(G, Q, make_responses):
    # Khong co cau nao cho complexity: prior mean 0.5 < 0.6 nhung KHONG duoc gan yeu
    res = diagnose(make_responses({"sorting"}, skip={"complexity"}), Q, G)
    assert "complexity" in res["unobserved"]
    assert "complexity" not in res["weak"]
    assert res["roots"] == ["sorting"]


def test_missing_answers_none_or_nan_are_skipped(G, Q, make_responses):
    r = make_responses({"bst"})
    r["array_1"] = None
    r["array_2"] = float("nan")
    res = diagnose(r, Q, G)
    assert "array" in res["unobserved"]


def test_threshold_is_a_parameter(G, Q):
    # 1 dung 1 sai -> mean 0.5: yeu voi nguong 0.6, vung voi nguong 0.4
    r = {"bst_1": 1.0, "bst_2": 0.0}
    assert diagnose(r, Q, G, M1Params(threshold=0.6))["weak"] == {"bst"}
    assert diagnose(r, Q, G, M1Params(threshold=0.4))["weak"] == set()


def test_direct_vs_ancestors_mode_with_noisy_middle(G, Q, make_responses):
    # recursion yeu, tree "vung" do nhieu, bst yeu
    weak = {"recursion", "bst"}
    r = make_responses(weak)
    direct = diagnose(r, Q, G, mode="direct")
    strict = diagnose(r, Q, G, mode="ancestors")
    assert set(direct["roots"]) == {"recursion", "bst"}
    assert strict["roots"] == ["recursion"]


def test_multi_concept_item_weights(G):
    Q = {"mix": {"tree": 1.0, "linked_list": 1.0}}
    raw = diagnose({"mix": 0.0}, Q, G)["details"]
    norm = diagnose({"mix": 0.0}, Q, G, M1Params(normalize_rows=True))["details"]
    assert math.isclose(raw["tree"]["beta"], 2.0)    # 1 + 1*1
    assert math.isclose(norm["tree"]["beta"], 1.5)   # 1 + 1*0.5


def test_partial_credit(G, Q):
    res = diagnose({"bst_1": 0.5, "bst_2": 0.5}, Q, G)
    assert math.isclose(res["mastery"]["bst"], 0.5)


def test_cycle_in_graph_is_rejected(G, Q, make_responses):
    G.add_edge("bst", "array")
    with pytest.raises(ValueError, match="chu trinh"):
        diagnose(make_responses(set()), Q, G)


def test_unknown_item_and_bad_score_are_rejected(G, Q):
    with pytest.raises(KeyError):
        diagnose({"khong_ton_tai": 1.0}, Q, G)
    with pytest.raises(ValueError):
        diagnose({"bst_1": 7}, Q, G)


def test_concept_in_Q_missing_from_graph(G):
    with pytest.raises(ValueError, match="khong co trong G"):
        diagnose({"x": 1.0}, {"x": {"heap": 1.0}}, G)


def test_find_roots_alone():
    g = nx.DiGraph([("A", "B"), ("B", "C")])
    assert find_roots(g, {"B", "C"}) == {"B"}
    assert find_roots(g, {"A", "C"}) == {"A", "C"}
    assert find_roots(g, {"A", "C"}, mode="ancestors") == {"A"}


def test_graph_from_neo4j_requires_is_reversed(Q, make_responses):
    # (tree)-[:REQUIRES]->(recursion): recursion la tien quyet cua tree
    G = graph_from_requires([("tree", "recursion"), ("bst", "tree")],
                            nodes=["recursion", "tree", "bst"])
    assert G.has_edge("recursion", "tree") and G.has_edge("tree", "bst")
    Q3 = {k: v for k, v in Q.items() if k.split("_")[0] in {"recursion", "tree", "bst"}}
    r = {k: 0.0 for k in Q3}
    assert diagnose(r, Q3, G)["roots"] == ["recursion"]


def test_batch_with_dataframe(G, Q, make_responses):
    pd = pytest.importorskip("pandas")
    df = pd.DataFrame(
        [make_responses({"bst"}), make_responses({"pointer", "linked_list"})],
        index=["S001", "S002"],
    )
    out = diagnose_batch(df, Q, G)
    assert out["S001"]["roots"] == ["bst"]
    assert out["S002"]["roots"] == ["pointer"]


def test_Q_as_dataframe(G, Q, make_responses):
    pd = pytest.importorskip("pandas")
    qdf = pd.DataFrame.from_dict(Q, orient="index").fillna(0.0)
    res = diagnose(make_responses({"bst"}), qdf, G)
    assert res["roots"] == ["bst"]
