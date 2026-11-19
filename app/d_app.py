"""Giao dien bo chan doan M1 (nhiem vu 1.6, D).

Chay tu thu muc goc:
    streamlit run app/d_app.py
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

import networkx as nx
import streamlit as st
import streamlit.components.v1 as components

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from diagnosis import (M1Params, diagnose, format_report, load_concepts,  # noqa: E402
                       load_graph_from_files, load_graph_from_neo4j, load_q_csv,
                       load_requires_csv, load_responses_csv, build_graph,
                       mastery_table, overall_verdict, result_to_json, to_dot, to_svg)
from diagnosis.viz import LEGEND  # noqa: E402

st.set_page_config(page_title="Chẩn đoán lỗ hổng kiến thức gốc", layout="wide")

PRESETS = {
    "SV A: hổng đệ quy (C01_09)": ["C01_09"],
    "SV B: hổng DSLK đơn (C03_09) và BST (C04_07)": ["C03_09", "C04_07"],
    "SV C: chỉ sai Dijkstra (C05_08)": ["C05_08"],
    "SV D: hổng mảng (C02_01)": ["C02_01"],
    "Vững tất cả": [],
}


def save_upload(uploaded) -> Path:
    tmp = Path(tempfile.mkdtemp()) / uploaded.name
    tmp.write_bytes(uploaded.getvalue())
    return tmp


@st.cache_data(show_spinner=False)
def graph_from_default_files():
    return load_graph_from_files(ROOT / "data/concepts_v0.csv", ROOT / "data/edges_v0.csv")


def demo_q(concept_ids, n=2):
    return {f"{c}_q{k}": {c: 1.0} for c in concept_ids for k in range(1, n + 1)}


# ============================== SIDEBAR: do thi + tham so ==============================
with st.sidebar:
    st.header("Đồ thị tiên quyết")
    src = st.radio("Nguồn", ["File trong data/", "Tải file lên", "Neo4j"],
                   help="Cạnh (a)-[:REQUIRES]->(b) nghĩa là học a cần b. Bộ chẩn đoán tự đảo chiều.")
    G = concepts = None
    try:
        if src == "File trong data/":
            G, concepts = graph_from_default_files()
        elif src == "Tải file lên":
            fc = st.file_uploader("concepts_v0.csv (cột concept_id, name_vi, …)", type="csv")
            fe = st.file_uploader("edges_v0.csv (cột src, dst)", type="csv")
            if fc and fe:
                concepts = load_concepts(save_upload(fc))
                G = build_graph(concepts, load_requires_csv(save_upload(fe)))
        else:
            uri = st.text_input("URI", "bolt://localhost:7687")
            user = st.text_input("User", "neo4j")
            pw = st.text_input("Mật khẩu", type="password")
            if st.button("Kết nối"):
                from neo4j import GraphDatabase

                with GraphDatabase.driver(uri, auth=(user, pw)) as drv:
                    G, concepts = load_graph_from_neo4j(drv)
                st.session_state["neo4j_graph"] = (G, concepts)
            if "neo4j_graph" in st.session_state:
                G, concepts = st.session_state["neo4j_graph"]
    except Exception as exc:  # hien loi than thien thay vi trang do
        st.error(f"Không nạp được đồ thị: {exc}")

    if G is not None:
        st.success(f"{G.number_of_nodes()} khái niệm, {G.number_of_edges()} cạnh tiên quyết")

    st.header("Tham số M1")
    threshold = st.slider("Ngưỡng vững", 0.30, 0.90, 0.60, 0.05,
                          help="Không nhúng cứng 0,6: sẽ chọn lại bằng ROC ở GĐ3.")
    a0 = st.number_input("Prior a₀ (phiếu đúng có sẵn)", 0.1, 10.0, 1.0, 0.5)
    b0 = st.number_input("Prior b₀ (phiếu sai có sẵn)", 0.1, 10.0, 1.0, 0.5)
    mode = st.radio("Tìm nút gốc", ["direct", "ancestors"],
                    help="direct: chỉ xét tiên quyết trực tiếp. ancestors: xét mọi tổ tiên.")
    normalize = st.checkbox("Chia đều trọng số câu nhiều khái niệm", value=False)

st.title("Chẩn đoán lỗ hổng kiến thức gốc — M1")
st.caption("Nhiệm vụ 1.6 · Beta-Binomial + outer fringe · diagnose(responses, Q, G) → {mastery, weak, roots, evidence}")

if G is None:
    st.info("Chọn nguồn đồ thị ở thanh bên trái.")
    st.stop()

ids = sorted(G.nodes)
names = {c: concepts.get(c, {}).get("name_vi", "") for c in ids}

# ============================== DAU VAO: bai lam ==============================
st.subheader("1. Bài làm của sinh viên")
how = st.radio("Cách nhập", ["Kịch bản mẫu", "Nhập tay theo khái niệm", "Tải file CSV"], horizontal=True)
responses: dict[str, float] = {}
Q: dict[str, dict[str, float]] = {}

if how == "Kịch bản mẫu":
    col1, col2 = st.columns([2, 3])
    with col1:
        preset = st.selectbox("Kịch bản", list(PRESETS))
    with col2:
        extra = st.multiselect("Thêm lỗ hổng gốc (khái niệm và mọi hậu duệ sẽ làm sai)", ids,
                               format_func=lambda c: f"{c} · {names[c]}")
    roots_in = [r for r in PRESETS[preset] if r in G] + list(extra)
    weak_in = set()
    for r in roots_in:
        weak_in |= {r} | nx.descendants(G, r)
    Q = demo_q(ids)
    responses = {i: (0.0 if next(iter(Q[i])) in weak_in else 1.0) for i in Q}
    st.caption(f"Q-matrix giả: mỗi khái niệm 2 câu. {len(weak_in)} khái niệm được cho làm sai cả 2 câu.")

elif how == "Nhập tay theo khái niệm":
    st.caption("Sửa cột số câu và số câu đúng. Số câu = 0 nghĩa là khái niệm không có trong đề (chưa quan sát).")
    if "manual" not in st.session_state or set(r["concept_id"] for r in st.session_state["manual"]) != set(ids):
        st.session_state["manual"] = [{"concept_id": c, "ten": names[c], "so_cau": 2, "so_dung": 2} for c in ids]
    table = st.data_editor(
        st.session_state["manual"], key="manual_editor", hide_index=True, use_container_width=True,
        disabled=["concept_id", "ten"],
        column_config={
            "so_cau": st.column_config.NumberColumn("Số câu", min_value=0, max_value=20, step=1),
            "so_dung": st.column_config.NumberColumn("Số câu đúng", min_value=0, max_value=20, step=1),
        },
    )
    rows = table.to_dict("records") if hasattr(table, "to_dict") else list(table)
    bad = [r["concept_id"] for r in rows if int(r["so_dung"] or 0) > int(r["so_cau"] or 0)]
    if bad:
        st.error(f"Số câu đúng lớn hơn số câu ở: {', '.join(bad)}. Sửa lại trước khi chẩn đoán.")
        st.stop()
    for r in rows:
        n, k = int(r["so_cau"] or 0), int(r["so_dung"] or 0)
        for j in range(1, n + 1):
            item = f"{r['concept_id']}_q{j}"
            Q[item] = {r["concept_id"]: 1.0}
            responses[item] = 1.0 if j <= k else 0.0

else:
    st.caption("Q-matrix: cột item_id, concept_id, weight. Bài làm: cột student_id, item_id, score "
               "(hoặc dạng rộng: student_id + mỗi câu một cột).")
    c1, c2 = st.columns(2)
    with c1:
        fq = st.file_uploader("Q-matrix (CSV)", type="csv")
    with c2:
        fr = st.file_uploader("Bài làm (CSV)", type="csv")
    use_sample = st.checkbox("Dùng file mẫu trong data/samples/", value=not (fq and fr))
    try:
        if use_sample:
            Q = load_q_csv(ROOT / "data/samples/Q_demo.csv")
            all_resp = load_responses_csv(ROOT / "data/samples/responses_demo.csv")
        elif fq and fr:
            Q = load_q_csv(save_upload(fq))
            all_resp = load_responses_csv(save_upload(fr))
        else:
            st.info("Tải lên cả hai file hoặc chọn dùng file mẫu.")
            st.stop()
    except Exception as exc:
        st.error(f"Không đọc được file: {exc}")
        st.stop()
    sid = st.selectbox("Sinh viên", sorted(all_resp))
    responses = all_resp[sid]

# ============================== CHAN DOAN ==============================
params = M1Params(threshold=threshold, prior_alpha=a0, prior_beta=b0, normalize_rows=normalize)
try:
    res = diagnose(responses, Q, G, params, mode=mode)
except Exception as exc:
    st.error(f"Chẩn đoán lỗi: {exc}")
    st.stop()

st.subheader("2. Kết luận")
v = overall_verdict(res, concepts)
(st.success if v["level"] == "ok" else st.warning)(f"**{v['title']}** {v['detail']}")
m = st.columns(4)
n_unobs = len(res["unobserved"])
m[0].metric("Vững", len(ids) - len(res["weak"]) - n_unobs)
m[1].metric("Chưa vững", len(res["weak"]))
m[2].metric("Lỗ hổng gốc", len(res["roots"]))
m[3].metric("Chưa có câu hỏi", n_unobs)

# ------------------------------ 3. DO THI ------------------------------
st.subheader("3. Đồ thị tiên quyết")
c1, c2 = st.columns([3, 2])
with c1:
    hl = st.selectbox("Tô đậm dấu vết của", ["(không)"] + res["roots"],
                      index=1 if res["roots"] else 0,
                      format_func=lambda c: c if c == "(không)" else f"{c} · {names.get(c, '')}")
with c2:
    only = st.checkbox("Chỉ hiện khái niệm liên quan", value=len(res["roots"]) > 0)
st.caption("Đỏ = lỗ hổng gốc · Vàng = chưa vững · Xanh = vững · Xám = chưa có câu hỏi. "
           "Mũi tên A → B: A là tiên quyết của B. Đường đỏ = dấu vết bằng chứng. Rê chuột lên ô để xem tên.")
style = st.radio("Kiểu vẽ", ["SVG (khuyên dùng)", "Graphviz"], horizontal=True,
                 help="Nếu một kiểu không hiện trên trình duyệt của bạn, đổi sang kiểu còn lại.")
hl_root = None if hl == "(không)" else hl
if style.startswith("SVG"):
    svg, h = to_svg(G, res, concepts, highlight_root=hl_root, only_relevant=only)
    components.html(f'<div style="overflow-x:auto">{svg}</div>', height=h + 30, scrolling=True)
    st.download_button("Tải hình đồ thị (SVG)", svg, file_name="do_thi_chan_doan.svg", mime="image/svg+xml")
else:
    st.graphviz_chart(to_dot(G, res, concepts, highlight_root=hl_root, only_relevant=only))

# ------------------------------ 4. CHI TIET ------------------------------
st.subheader("4. Chi tiết")
rows = mastery_table(res, concepts, a0=a0, b0=b0, threshold=threshold)
tab_calc, tab_roots, tab_dl = st.tabs(["Công thức và cách tính", "Lỗ hổng gốc và bằng chứng", "Tải kết quả"])

with tab_calc:
    st.markdown("**Bước 1. Đếm phiếu** (mỗi câu đúng thêm 1 phiếu α, mỗi câu sai thêm 1 phiếu β; "
                f"có sẵn a₀ = {a0:g} phiếu đúng và b₀ = {b0:g} phiếu sai):")
    st.latex(r"\alpha = a_0 + \text{số câu đúng} \qquad \beta = b_0 + \text{số câu sai}")
    st.markdown("**Bước 2. Mức thành thạo:**")
    st.latex(r"\text{mức thành thạo} = \frac{\alpha}{\alpha + \beta}")
    st.markdown(f"**Bước 3. Kết luận:** mức thành thạo ≥ {threshold:.2f} là **vững**, "
                f"nhỏ hơn là **chưa vững**. Khái niệm không có câu hỏi thì **chưa kết luận**.")
    st.markdown("**Bước 4. Nút gốc:** khái niệm chưa vững mà mọi tiên quyết đều vững "
                f"(chế độ `{mode}`).")
    show = st.radio("Hiện", ["Khái niệm chưa vững", "Tất cả"], horizontal=True)
    view = [r for r in rows if show == "Tất cả" or r["trang_thai"] in ("Lỗ hổng gốc", "Chưa vững")]
    cols = ["concept_id", "ten", "so_cau", "so_dung", "so_sai", "alpha", "beta", "cong_thuc", "ket_luan", "trang_thai"]
    st.dataframe([{k: r[k] for k in cols} for r in view] or [{"concept_id": "(không có)"}],
                 use_container_width=True, hide_index=True)

with tab_roots:
    if not res["roots"]:
        st.success("Không phát hiện lỗ hổng gốc.")
    for k, r in enumerate(res["roots"], 1):
        ev = res["evidence"][r]
        with st.expander(f"{k}. {r} · {names.get(r, '')} — mức thành thạo {ev['mastery']:.2f}", expanded=k == 1):
            st.markdown(f"**Câu làm sai:** {', '.join(ev['wrong_items']) or 'không'}")
            st.markdown(f"**Tiên quyết đã vững:** {', '.join(ev['prerequisites_mastered']) or 'không có (nút nguồn)'}")
            st.markdown(f"**Giải thích {len(ev['explains'])} khái niệm yếu khác:**")
            for c in ev["explains"]:
                st.markdown("- " + " → ".join(f"{x} {names.get(x, '')}" for x in ev["paths"][c]))

with tab_dl:
    st.download_button("Tải kết quả JSON", json.dumps(result_to_json(res), ensure_ascii=False, indent=2),
                       file_name="ket_qua_chan_doan.json", mime="application/json")
    import csv as _csv
    import io as _io

    buf = _io.StringIO()
    w = _csv.DictWriter(buf, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)
    st.download_button("Tải bảng khái niệm CSV", buf.getvalue().encode("utf-8-sig"),
                       file_name="bang_khai_niem.csv", mime="text/csv")
    report = v["title"] + "\n" + v["detail"] + "\n\n" + format_report(res, concepts)
    st.download_button("Tải báo cáo văn bản", report, file_name="bao_cao.txt", mime="text/plain")
    st.code(report, language=None)
