"""Tim nut goc (outer fringe) va dau vet bang chung."""

from __future__ import annotations

from typing import Literal

import networkx as nx

PrereqMode = Literal["direct", "ancestors"]


def find_roots(
    G: nx.DiGraph,
    weak: set[str],
    mode: PrereqMode = "direct",
) -> set[str]:
    """Nut goc = khai niem chua vung ma moi tien quyet deu da vung.

    mode="direct":    chi xet tien quyet truc tiep (predecessors) - dung dinh nghia
                      outer fringe cua KST tren do thi da rut gon bac cau.
    mode="ancestors": xet moi to tien. Chat hon: neu co to tien nao yeu (ke ca khi
                      tien quyet truc tiep "vung" do nhieu), khai niem khong la goc.
    Khai niem chua quan sat duoc coi la "khong yeu" (khong co bang chung).
    """
    if mode == "direct":
        upstream = G.predecessors
    elif mode == "ancestors":
        upstream = lambda c: nx.ancestors(G, c)  # noqa: E731
    else:
        raise ValueError("mode phai la 'direct' hoac 'ancestors'")
    return {c for c in weak if not any(p in weak for p in upstream(c))}


def explained_by(G: nx.DiGraph, root: str, weak: set[str]) -> dict[str, list[str]]:
    """Cac khai niem yeu ma root giai thich duoc: dung duoc tu root qua duong di
    chi gom khai niem yeu. Tra ve {khai_niem: duong_di_ngan_nhat}."""
    H = G.subgraph(weak)
    paths = nx.single_source_shortest_path(H, root)
    paths.pop(root, None)
    return paths


def rank_roots(
    G: nx.DiGraph,
    roots: set[str],
    weak: set[str],
    mastery: dict[str, float],
) -> list[str]:
    """Uu tien goc giai thich duoc nhieu khai niem yeu nhat, roi den mastery thap nhat.
    Thu tu nay quyet dinh Hit@1, Recall@3, MRR o thi nghiem mo phong."""
    return sorted(
        roots,
        key=lambda r: (-len(explained_by(G, r, weak)), mastery[r], r),
    )
