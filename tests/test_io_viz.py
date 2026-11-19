"""Test ham doc CSV (Q-matrix, bai lam) va ham ve do thi."""

from pathlib import Path

import pytest

from diagnosis import (diagnose, overall_verdict, load_graph_from_files, load_q_csv, load_responses_csv,
                       mastery_table, node_status, result_to_json, to_dot, to_svg)

ROOT = Path(__file__).resolve().parents[1]


def test_load_q_csv_multi_concept_and_default_weight(tmp_path):
    p = tmp_path / "q.csv"
    p.write_text("item_id,concept_id,weight\nq1,C03_09,1\nq1,C03_10,0.5\nq2,C04_07,\n", encoding="utf-8")
    Q = load_q_csv(p)
    assert Q == {"q1": {"C03_09": 1.0, "C03_10": 0.5}, "q2": {"C04_07": 1.0}}


def test_load_q_csv_requires_columns(tmp_path):
    p = tmp_path / "q.csv"
    p.write_text("cau,khai_niem\nq1,C01_01\n", encoding="utf-8")
    with pytest.raises(ValueError, match="item_id"):
        load_q_csv(p)


def test_load_responses_long_and_wide(tmp_path):
    long = tmp_path / "long.csv"
    long.write_text("student_id,item_id,score\nS1,q1,1\nS1,q2,0\nS2,q1,0.5\n", encoding="utf-8")
    wide = tmp_path / "wide.csv"
    wide.write_text("student_id,q1,q2\nS1,1,0\nS2,0.5,\n", encoding="utf-8")
    expect = {"S1": {"q1": 1.0, "q2": 0.0}, "S2": {"q1": 0.5}}
    assert load_responses_csv(long) == expect
    assert load_responses_csv(wide) == expect


def test_sample_files_reproduce_scenarios():
    G, _ = load_graph_from_files(ROOT / "data/concepts_v0.csv", ROOT / "data/edges_v0.csv")
    Q = load_q_csv(ROOT / "data/samples/Q_demo.csv")
    R = load_responses_csv(ROOT / "data/samples/responses_demo.csv")
    got = {s: diagnose(r, Q, G)["roots"] for s, r in R.items()}
    assert got == {"SV_A_hong_de_quy": ["C01_09"], "SV_B_hong_DSLK_va_BST": ["C03_09", "C04_07"],
                   "SV_C_chi_sai_Dijkstra": ["C05_08"], "SV_D_vung_het": []}


@pytest.fixture
def toy_result(G, Q, make_responses):
    weak = {"pointer", "linked_list", "stack_queue", "tree", "bst", "graph_bfs"}
    return diagnose(make_responses(weak, skip={"complexity"}), Q, G)


def test_node_status(toy_result):
    s = node_status(toy_result)
    assert s["pointer"] == "root" and s["tree"] == "weak"
    assert s["array"] == "ok" and s["complexity"] == "unobserved"


def test_to_dot_highlights_evidence_path(G, toy_result):
    dot = to_dot(G, toy_result, highlight_root="pointer")
    assert dot.startswith("digraph G {") and dot.rstrip().endswith("}")
    assert '"pointer" -> "linked_list" [color="#E24B4A"' in dot
    assert '"array" -> "sorting";' in dot  # canh khong thuoc bang chung: mau xam mac dinh


def test_to_dot_only_relevant_hides_unrelated(G, toy_result):
    dot = to_dot(G, toy_result, only_relevant=True)
    assert '"sorting"' not in dot
    assert '"pointer"' in dot and '"bst"' in dot


def test_mastery_table_and_json(toy_result):
    rows = mastery_table(toy_result)
    assert rows[0]["trang_thai"] == "Lỗ hổng gốc"
    unobs = [r for r in rows if r["concept_id"] == "complexity"][0]
    assert unobs["muc_thanh_thao"] is None
    js = result_to_json(toy_result)
    assert js["roots"] == ["pointer"] and isinstance(js["weak"], list)


def test_mastery_table_shows_each_calculation_step(toy_result):
    rows = {r["concept_id"]: r for r in mastery_table(toy_result, threshold=0.6)}
    assert rows["array"]["cong_thuc"] == "(1+2) / (3+1) = 0.75"
    assert rows["array"]["ket_luan"] == "0.75 ≥ 0.60 → vững"
    assert rows["pointer"]["alpha"] == "1" and rows["pointer"]["beta"] == "3"
    assert rows["complexity"]["ket_luan"] == "chưa kết luận"


def test_overall_verdict(toy_result, G, Q, make_responses):
    v = overall_verdict(toy_result)
    assert v["level"] == "weak" and "pointer" in v["detail"]
    ok = overall_verdict(diagnose(make_responses(set()), Q, G))
    assert ok["level"] == "ok" and "VỮNG" in ok["title"]


def test_to_svg_is_valid_xml_with_colors_and_evidence(G, toy_result):
    import xml.etree.ElementTree as ET

    svg, h = to_svg(G, toy_result, highlight_root="pointer", chapter_of=lambda c: c[0].upper())
    ET.fromstring(svg)  # SVG hop le
    assert h > 0 and svg.count("<rect") == G.number_of_nodes()
    assert "#F7C1C1" in svg and "#E5E3DC" in svg  # goc do, chua quan sat xam
    assert svg.count('stroke="#E24B4A"') == 5  # 5 canh tren duong bang chung cua pointer


def test_to_svg_on_real_graph_only_relevant():
    G, c = load_graph_from_files(ROOT / "data/concepts_v0.csv", ROOT / "data/edges_v0.csv")
    Q = load_q_csv(ROOT / "data/samples/Q_demo.csv")
    R = load_responses_csv(ROOT / "data/samples/responses_demo.csv")
    res = diagnose(R["SV_A_hong_de_quy"], Q, G)
    full, _ = to_svg(G, res, c)
    small, _ = to_svg(G, res, c, highlight_root="C01_09", only_relevant=True)
    assert full.count("<rect") == 70
    assert small.count("<rect") == 21  # 20 khai niem yeu + 1 tien quyet cua goc (C01_04)
    assert "Giải thuật đệ quy" in small  # ten trong tooltip
