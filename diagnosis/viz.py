"""Ve ket qua chan doan thanh do thi Graphviz (chuoi DOT) cho giao dien.

Khong can cai Graphviz: st.graphviz_chart cua Streamlit tu ve chuoi DOT trong trinh duyet.
"""

from __future__ import annotations

from typing import Any

import networkx as nx

# (nen, vien, chu) - mau nhat de doc duoc chu
COLORS = {
    "root": ("#F7C1C1", "#A32D2D", "#501313"),
    "weak": ("#FAC775", "#854F0B", "#412402"),
    "ok": ("#C0DD97", "#3B6D11", "#173404"),
    "unobserved": ("#E5E3DC", "#888780", "#444441"),
}
LEGEND = {"root": "Lỗ hổng gốc", "weak": "Chưa vững", "ok": "Vững", "unobserved": "Chưa có câu hỏi"}


def node_status(res: dict[str, Any]) -> dict[str, str]:
    roots = set(res["roots"])
    unobs = set(res.get("unobserved", ()))
    out = {}
    for c in res["mastery"]:
        if c in unobs:
            out[c] = "unobserved"
        elif c in roots:
            out[c] = "root"
        elif c in res["weak"]:
            out[c] = "weak"
        else:
            out[c] = "ok"
    return out


def _esc(s: str) -> str:
    return s.replace("\\", "\\\\").replace('"', '\\"')


def to_dot(G: nx.DiGraph, res: dict[str, Any], concepts: dict | None = None,
           highlight_root: str | None = None, chapter_of=None,
           only_relevant: bool = False) -> str:
    """Chuoi DOT: moi chuong mot cum, nut to theo trang thai, duong bang chung to do.

    highlight_root: ve dam cac duong di bang chung cua nut goc nay.
    only_relevant:  chi ve khai niem chua vung, nut goc va tien quyet truc tiep cua nut goc.
    chapter_of:     ham concept_id -> nhan chuong (mac dinh lay 3 ky tu dau, vi du 'C03').
    """
    status = node_status(res)
    chapter_of = chapter_of or (lambda c: c.split("_")[0])

    nodes = set(G.nodes)
    if only_relevant:
        keep = set(res["weak"]) | set(res["roots"])
        for r in res["roots"]:
            keep |= set(G.predecessors(r))
        nodes = keep or nodes

    red_edges: set[tuple[str, str]] = set()
    if highlight_root and highlight_root in res.get("evidence", {}):
        for path in res["evidence"][highlight_root]["paths"].values():
            red_edges |= set(zip(path, path[1:]))

    lines = [
        "digraph G {",
        '  graph [rankdir=LR, fontname="Helvetica", fontsize=11, nodesep=0.15, ranksep=0.5];',
        '  node [shape=box, style="rounded,filled", fontname="Helvetica", fontsize=10, '
        'width=0.8, height=0.3, margin="0.05,0.02"];',
        '  edge [color="#B4B2A9", arrowsize=0.5];',
    ]
    clusters: dict[str, list[str]] = {}
    for c in sorted(nodes):
        clusters.setdefault(chapter_of(c), []).append(c)
    for i, (ch, members) in enumerate(sorted(clusters.items())):
        lines.append(f'  subgraph cluster_{i} {{ label="{_esc(ch)}"; color="#D3D1C7"; fontcolor="#5F5E5A";')
        for c in members:
            fill, border, font = COLORS[status[c]]
            name = concepts.get(c, {}).get("name_vi", "") if concepts else ""
            m = res["mastery"].get(c)
            tip = f"{c} {name}" + ("" if m is None or status[c] == "unobserved" else f" | {m:.2f}")
            pen = 2.5 if c == highlight_root else 1
            lines.append(f'    "{c}" [fillcolor="{fill}", color="{border}", fontcolor="{font}", '
                         f'penwidth={pen}, tooltip="{_esc(tip)}"];')
        lines.append("  }")
    for u, v in G.edges():
        if u in nodes and v in nodes:
            if (u, v) in red_edges:
                lines.append(f'  "{u}" -> "{v}" [color="#E24B4A", penwidth=2.2];')
            else:
                lines.append(f'  "{u}" -> "{v}";')
    lines.append("}")
    return "\n".join(lines)


def _xml(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def to_svg(G: nx.DiGraph, res: dict[str, Any], concepts: dict | None = None,
           highlight_root: str | None = None, chapter_of=None,
           only_relevant: bool = False) -> tuple[str, int]:
    """Ve do thi thanh SVG thuan (khong can Graphviz). Tra ve (svg, chieu_cao_px).

    Moi chuong mot cot, khai niem xep tu tren xuong theo ma. Mui ten A -> B: A la tien quyet cua B.
    """
    status = node_status(res)
    chapter_of = chapter_of or (lambda c: c.split("_")[0])
    nodes = set(G.nodes)
    if only_relevant:
        keep = set(res["weak"]) | set(res["roots"])
        for r in res["roots"]:
            keep |= set(G.predecessors(r))
        nodes = keep or nodes

    red: set[tuple[str, str]] = set()
    if highlight_root and highlight_root in res.get("evidence", {}):
        for path in res["evidence"][highlight_root]["paths"].values():
            red |= set(zip(path, path[1:]))

    cols: dict[str, list[str]] = {}
    for c in sorted(nodes):
        cols.setdefault(chapter_of(c), []).append(c)
    W, H, CW, RH, TOP, LEFT = 96, 26, 128, 36, 34, 10
    pos = {}
    for i, (ch, members) in enumerate(sorted(cols.items())):
        for j, c in enumerate(members):
            pos[c] = (LEFT + i * CW, TOP + j * RH)
    width = LEFT * 2 + max(1, len(cols)) * CW
    height = TOP + max((len(m) for m in cols.values()), default=1) * RH + 10

    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
           f'viewBox="0 0 {width} {height}" font-family="Segoe UI, Helvetica, Arial, sans-serif">',
           '<defs>'
           '<marker id="ag" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto">'
           '<path d="M0,0 L10,5 L0,10 z" fill="#B4B2A9"/></marker>'
           '<marker id="ar" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto">'
           '<path d="M0,0 L10,5 L0,10 z" fill="#E24B4A"/></marker></defs>']
    for i, ch in enumerate(sorted(cols)):
        out.append(f'<text x="{LEFT + i * CW + W / 2}" y="18" text-anchor="middle" font-size="13" '
                   f'fill="#5F5E5A">{_xml(ch)}</text>')

    def anchor(a, b):
        (x1, y1), (x2, y2) = pos[a], pos[b]
        if x1 == x2:  # cung chuong: noi canh phai -> canh phai, cong ra ngoai
            sx, sy, ex, ey = x1 + W, y1 + H / 2, x2 + W, y2 + H / 2
            bend = x1 + W + 14 + abs(y2 - y1) * 0.08
            return f"M{sx},{sy} C{bend},{sy} {bend},{ey} {ex},{ey}"
        sx, sy = (x1 + W, y1 + H / 2) if x2 > x1 else (x1, y1 + H / 2)
        ex, ey = (x2, y2 + H / 2) if x2 > x1 else (x2 + W, y2 + H / 2)
        mx = (sx + ex) / 2
        return f"M{sx},{sy} C{mx},{sy} {mx},{ey} {ex},{ey}"

    edges = [(u, v) for u, v in G.edges() if u in pos and v in pos]
    for u, v in sorted(edges, key=lambda e: e in red):  # canh do ve sau cung, nam tren
        if (u, v) in red:
            out.append(f'<path d="{anchor(u, v)}" fill="none" stroke="#E24B4A" stroke-width="2.2" '
                       f'marker-end="url(#ar)"/>')
        else:
            out.append(f'<path d="{anchor(u, v)}" fill="none" stroke="#B4B2A9" stroke-width="1" '
                       f'opacity="0.7" marker-end="url(#ag)"/>')
    for c, (x, y) in pos.items():
        fill, border, font = COLORS[status[c]]
        name = concepts.get(c, {}).get("name_vi", "") if concepts else ""
        m = res["mastery"].get(c)
        tip = f"{c} {name}" + ("" if status[c] == "unobserved" or m is None
                               else f" | mức thành thạo {m:.2f}") + f" | {LEGEND[status[c]]}"
        sw = 3 if c == highlight_root else 1
        out.append(f'<g><title>{_xml(tip)}</title>'
                   f'<rect x="{x}" y="{y}" width="{W}" height="{H}" rx="5" fill="{fill}" '
                   f'stroke="{border}" stroke-width="{sw}"/>'
                   f'<text x="{x + W / 2}" y="{y + 17}" text-anchor="middle" font-size="12" '
                   f'fill="{font}">{_xml(c)}</text></g>')
    out.append("</svg>")
    return "".join(out), height


def _num(x: float) -> str:
    return f"{x:g}" if abs(x - round(x)) > 1e-9 else str(int(round(x)))


def mastery_table(res: dict[str, Any], concepts: dict | None = None,
                  a0: float = 1.0, b0: float = 1.0, threshold: float | None = None) -> list[dict]:
    """Bang ket qua tung khai niem, kem tung buoc tinh M1 (dung cho bang va tai CSV).

    so_dung, so_sai la tong trong so (bang so cau neu moi cau trong so 1).
    """
    status = node_status(res)
    rows = []
    for c, m in res["mastery"].items():
        d = res.get("details", {}).get(c, {})
        alpha, beta = d.get("alpha", a0), d.get("beta", b0)
        n_dung, n_sai = alpha - a0, beta - b0
        unobs = status[c] == "unobserved"
        row = {
            "concept_id": c,
            "ten": concepts.get(c, {}).get("name_vi", "") if concepts else "",
            "so_cau": d.get("n_items", 0),
            "so_dung": _num(n_dung),
            "so_sai": _num(n_sai),
            "alpha": _num(alpha),
            "beta": _num(beta),
            "cong_thuc": "không có câu hỏi" if unobs else
                         f"({_num(a0)}+{_num(n_dung)}) / ({_num(alpha)}+{_num(beta)}) = {m:.2f}",
            "muc_thanh_thao": None if unobs else round(m, 3),
            "p_vung": None if unobs else round(d.get("p_mastered", 0.0), 3),
            "trang_thai": LEGEND[status[c]],
        }
        if threshold is not None:
            row["ket_luan"] = ("chưa kết luận" if unobs else
                               f"{m:.2f} {'≥' if m >= threshold else '<'} {threshold:.2f} → "
                               f"{'vững' if m >= threshold else 'chưa vững'}")
        rows.append(row)
    order = {"Lỗ hổng gốc": 0, "Chưa vững": 1, "Vững": 2, "Chưa có câu hỏi": 3}
    rows.sort(key=lambda r: (order[r["trang_thai"]], r["concept_id"]))
    return rows


def result_to_json(res: dict[str, Any]) -> dict:
    """Ket qua chan doan dang JSON (set -> list) de luu file."""
    return {
        "mastery": res["mastery"],
        "weak": sorted(res["weak"]),
        "roots": list(res["roots"]),
        "evidence": res["evidence"],
        "unobserved": sorted(res.get("unobserved", ())),
    }
