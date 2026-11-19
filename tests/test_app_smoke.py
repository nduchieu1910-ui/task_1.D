"""Chay thu app/d_app.py voi mot Streamlit gia (khong can cai Streamlit).

Muc dich: bat loi Python trong giao dien (sai ten bien, sai kieu du lieu...) truoc khi chay that.
Giao dien that van can kiem tra bang `streamlit run app/d_app.py`.
"""

import runpy
import sys
import types
from pathlib import Path

import pytest

APP = Path(__file__).resolve().parents[1] / "app" / "d_app.py"


class Stop(Exception):
    pass


class FakeSt(types.ModuleType):
    """Gia lap cac ham Streamlit ma app dung. `answers` = {nhan widget: gia tri chon}."""

    def __init__(self, answers):
        super().__init__("streamlit")
        self.answers = answers
        self.session_state = {}
        self.calls = []
        self.sidebar = self
        self.column_config = types.SimpleNamespace(NumberColumn=lambda *a, **k: None)

    # --- ngu canh with ---
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def _log(self, name, *a, **k):
        self.calls.append((name, a, k))

    # --- widget ---
    def radio(self, label, options, **k):
        return self.answers.get(label, options[0])

    def selectbox(self, label, options, index=0, **k):
        return self.answers.get(label, list(options)[index])

    def multiselect(self, label, options, **k):
        return self.answers.get(label, [])

    def slider(self, label, lo, hi, value, step=None, **k):
        return self.answers.get(label, value)

    def number_input(self, label, lo, hi, value, step=None, **k):
        return self.answers.get(label, value)

    def checkbox(self, label, value=False, **k):
        return self.answers.get(label, value)

    def text_input(self, label, value="", **k):
        return self.answers.get(label, value)

    def button(self, label, **k):
        return self.answers.get(label, False)

    def file_uploader(self, label, **k):
        return None

    def data_editor(self, data, **k):
        return self.answers.get("data_editor", data)

    def columns(self, spec):
        n = spec if isinstance(spec, int) else len(spec)
        return [self for _ in range(n)]

    def tabs(self, labels):
        return [self for _ in labels]

    def expander(self, *a, **k):
        return self

    def cache_data(self, *a, **k):
        if a and callable(a[0]):
            return a[0]
        return lambda f: f

    def stop(self):
        raise Stop()

    def __getattr__(self, name):  # title, caption, metric, graphviz_chart, error, ...
        return lambda *a, **k: self._log(name, *a, **k)


def run_app(answers):
    fake = FakeSt(answers)
    comp = types.ModuleType("streamlit.components")
    v1 = types.ModuleType("streamlit.components.v1")
    v1.html = lambda html, **k: fake._log("components_html", html, **k)
    comp.v1 = v1
    fake.components = comp
    names_ = ["streamlit", "streamlit.components", "streamlit.components.v1"]
    old = {n: sys.modules.get(n) for n in names_}
    sys.modules.update({"streamlit": fake, "streamlit.components": comp, "streamlit.components.v1": v1})
    try:
        runpy.run_path(str(APP), run_name="__main__")
    except Stop:
        pass
    finally:
        for n, m in old.items():
            if m is None:
                sys.modules.pop(n, None)
            else:
                sys.modules[n] = m
    return fake


def names(fake):
    return [c[0] for c in fake.calls]


def logged(fake, name):
    return [c for c in fake.calls if c[0] == name]


def test_preset_mode_draws_graph_and_finds_roots():
    fake = run_app({"Kịch bản": "SV B: hổng DSLK đơn (C03_09) và BST (C04_07)"})
    assert not logged(fake, "error"), logged(fake, "error")
    assert "components_html" in names(fake)  # mac dinh ve SVG
    metrics = {c[1][0]: c[1][1] for c in logged(fake, "metric")}
    assert metrics["Lỗ hổng gốc"] == 2
    html = logged(fake, "components_html")[0][1][0]
    assert "<svg" in html and ">C03_09<" in html and "#F7C1C1" in html  # nut goc to do
    assert 'stroke="#E24B4A"' in html  # dau vet bang chung cua goc dau tien


def test_graphviz_option_still_available():
    fake = run_app({"Kịch bản": "SV B: hổng DSLK đơn (C03_09) và BST (C04_07)", "Kiểu vẽ": "Graphviz"})
    dot = logged(fake, "graphviz_chart")[0][1][0]
    assert '"C03_09"' in dot and "#F7C1C1" in dot


def test_extra_root_and_ancestors_mode():
    fake = run_app({"Kịch bản": "Vững tất cả", "Thêm lỗ hổng gốc (khái niệm và mọi hậu duệ sẽ làm sai)": ["C05_08"],
                    "Tìm nút gốc": "ancestors"})
    metrics = {c[1][0]: c[1][1] for c in logged(fake, "metric")}
    assert metrics["Lỗ hổng gốc"] == 1 and metrics["Chưa vững"] == 1


def test_manual_mode_with_unobserved_concept():
    from diagnosis import load_graph_from_files

    root = APP.parents[1]
    G, c = load_graph_from_files(root / "data/concepts_v0.csv", root / "data/edges_v0.csv")
    rows = [{"concept_id": k, "ten": "", "so_cau": 2, "so_dung": 2} for k in sorted(G.nodes)]
    for r in rows:
        if r["concept_id"] == "C03_09":
            r["so_dung"] = 0
        if r["concept_id"] == "C01_02":
            r["so_cau"] = r["so_dung"] = 0  # khong co trong de
    fake = run_app({"Cách nhập": "Nhập tay theo khái niệm", "data_editor": rows})
    assert not logged(fake, "error")
    metrics = {c[1][0]: c[1][1] for c in logged(fake, "metric")}
    assert metrics["Chưa có câu hỏi"] == 1
    assert metrics["Lỗ hổng gốc"] == 1


def test_manual_mode_rejects_more_correct_than_items():
    fake = run_app({"Cách nhập": "Nhập tay theo khái niệm",
                    "data_editor": [{"concept_id": "C01_01", "ten": "", "so_cau": 1, "so_dung": 3}]})
    assert logged(fake, "error")
    assert "components_html" not in names(fake) and "graphviz_chart" not in names(fake)


def test_csv_mode_with_sample_files():
    fake = run_app({"Cách nhập": "Tải file CSV", "Sinh viên": "SV_A_hong_de_quy"})
    assert not logged(fake, "error"), logged(fake, "error")
    metrics = {c[1][0]: c[1][1] for c in logged(fake, "metric")}
    assert metrics["Lỗ hổng gốc"] == 1
    downloads = [c[1][0] for c in logged(fake, "download_button")]
    assert downloads == ["Tải hình đồ thị (SVG)", "Tải kết quả JSON", "Tải bảng khái niệm CSV",
                         "Tải báo cáo văn bản"]


def test_threshold_slider_changes_result():
    rows_half = None  # 1/2 dung -> mastery 0.5
    from diagnosis import load_graph_from_files

    root = APP.parents[1]
    G, _ = load_graph_from_files(root / "data/concepts_v0.csv", root / "data/edges_v0.csv")
    rows_half = [{"concept_id": k, "ten": "", "so_cau": 2, "so_dung": 1 if k == "C05_08" else 2}
                 for k in sorted(G.nodes)]
    strict = run_app({"Cách nhập": "Nhập tay theo khái niệm", "data_editor": rows_half, "Ngưỡng vững": 0.6})
    loose = run_app({"Cách nhập": "Nhập tay theo khái niệm", "data_editor": rows_half, "Ngưỡng vững": 0.45})
    get = lambda f: {c[1][0]: c[1][1] for c in logged(f, "metric")}["Chưa vững"]  # noqa: E731
    assert get(strict) == 1 and get(loose) == 0


def test_verdict_banner_and_formula_table():
    fake = run_app({"Kịch bản": "SV C: chỉ sai Dijkstra (C05_08)", "Hiện": "Khái niệm chưa vững"})
    banner = logged(fake, "warning")[0][1][0]
    assert "CHƯA VỮNG 1/70" in banner and "C05_08" in banner
    assert len(logged(fake, "latex")) == 2
    table = [c for c in logged(fake, "dataframe")][0][1][0]
    assert table[0]["concept_id"] == "C05_08"
    assert table[0]["cong_thuc"] == "(1+0) / (1+3) = 0.25"
    assert table[0]["ket_luan"] == "0.25 < 0.60 → chưa vững"


def test_all_mastered_shows_success_banner():
    fake = run_app({"Kịch bản": "Vững tất cả"})
    assert any("VỮNG tất cả 70" in c[1][0] for c in logged(fake, "success"))
